from io import StringIO
from uuid import uuid4

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from market.models import Ad, Product, Shop


class CatalogAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def test_public_catalog_contract_and_semantics(self):
        for kind, count in [("ads", 10), ("products", 8), ("shops", 6)]:
            with self.subTest(kind=kind):
                response = self.client.get(f"/api/v1/{kind}/")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["source_kind"], "demo")
                self.assertEqual(response.data["count"], count)
                self.assertEqual(len(response.data["results"]), count)
                self.assertIn("no-store", response["Cache-Control"])
                for record in response.data["results"]:
                    self.assertEqual(record["source_kind"], "demo")
                    self.assertIsNone(record["observed_on"])
                    self.assertEqual(record["latest_metrics"]["value_kind"], "illustrative")
                    self.assertEqual(record["latest_metrics"]["currency"], "USD")
        shop = Shop.objects.get(external_id="s5")
        data = self.client.get(f"/api/v1/shops/{shop.pk}/").data
        self.assertEqual(data["latest_metrics"]["active_ads_count"], 627)
        self.assertEqual(data["actual_products_count"], 1)
        self.assertEqual(data["actual_ads_count"], 2)
        ad = self.client.get("/api/v1/ads/?format=video").data["results"][0]
        self.assertEqual(ad["format"], "video")
        self.assertEqual(ad["primary_media"]["media_kind"], "image")
        self.assertIsNone(ad["primary_media"]["video_url"])

    def test_search_filters_order_and_pagination(self):
        response = self.client.get("/api/v1/ads/?platform=meta&format=video&country=DE&min_active_days=40&ordering=-reach&page_size=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["external_id"], "a4")
        self.assertIsNotNone(response.data["next"])
        self.assertTrue(response.data["next"].startswith("/api/v1/ads/"))
        self.assertEqual(self.client.get("/api/v1/ads/?search=nord.example").data["count"], 1)
        self.assertEqual(self.client.get("/api/v1/products/?max_price=50").data["count"], 4)
        self.assertEqual(self.client.get("/api/v1/shops/?min_growth=100").data["count"], 1)
        self.assertEqual(self.client.get("/api/v1/products/?search=no-such-product").data["count"], 0)
        self.assertEqual(self.client.get("/api/v1/ads/?page=1000").status_code, 404)

    def test_invalid_filters_and_readonly_writes(self):
        for query in ["format=exe", "ordering=spend;DROP", "page_size=101", "min_active_days=-1", "unknown=x", "country=ZZ"]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get("/api/v1/ads/?" + query).status_code, 400)
        self.assertEqual(self.client.post("/api/v1/ads/", {}, format="json").status_code, 405)

    def test_one_product_per_shop_is_chosen_after_sorting(self):
        ordered = self.client.get("/api/v1/products/?ordering=-growth").data["results"]
        expected, seen = [], set()
        for product in ordered:
            if product["shop"]["id"] not in seen:
                expected.append(product["id"])
                seen.add(product["shop"]["id"])
        response = self.client.get("/api/v1/products/?ordering=-growth&one_per_shop=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data["results"]], expected)
        self.assertEqual(response.data["count"], 6)

    def test_relationships_and_bounded_comparison(self):
        product = Product.objects.get(external_id="p5")
        related = self.client.get(f"/api/v1/products/{product.pk}/ads/")
        self.assertEqual(related.data["count"], 2)
        self.assertTrue(all(str(item["product"]["id"]) == str(product.pk) for item in related.data["results"]))
        ids = list(Ad.objects.order_by("external_id").values_list("id", flat=True)[:3])
        value = ",".join(str(key) for key in reversed(ids))
        response = self.client.get("/api/v1/ads/compare/?ids=" + value)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([str(item["id"]) for item in response.data], [str(key) for key in reversed(ids)])
        for value in [str(ids[0]), f"{ids[0]},{ids[0]}", f"{ids[0]},{uuid4()}", "bad,id"]:
            self.assertEqual(self.client.get("/api/v1/ads/compare/?ids=" + value).status_code, 400)

    def test_reports_use_real_seed_counts_and_honest_undated_series(self):
        response = self.client.get("/api/v1/reports/overview/?focus=ads&period_days=90")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["period_filter_applied"])
        self.assertEqual(response.data["available_record_counts"], {"ads": 10, "products": 8, "shops": 6})
        self.assertEqual(sum(item["count"] for item in response.data["platform_distribution"]), 10)
        self.assertEqual(len(response.data["trend_points"]), 12)
        self.assertTrue(all(set(point) == {"index", "value"} for point in response.data["trend_points"]))
        self.assertEqual(self.client.get("/api/v1/reports/overview/?period_days=2").status_code, 400)
        home = self.client.get("/api/v1/home/?selection_index=4")
        self.assertEqual(home.status_code, 200)
        self.assertEqual(len(home.data["featured_ads"]), 3)

    def test_related_serialization_has_bounded_query_count(self):
        for kind in ("ads", "products", "shops"):
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(f"/api/v1/{kind}/?page_size=100")
            self.assertEqual(response.status_code, 200)
            self.assertLessEqual(len(queries), 8, f"{kind} should prefetch its related data")

    def test_csv_contains_explicit_provenance_and_currency(self):
        response = self.client.get("/api/v1/ads/export/?platform=tiktok")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))
        self.assertIn(b'"source_kind"', response.content)
        self.assertIn(b'"USD"', response.content)
