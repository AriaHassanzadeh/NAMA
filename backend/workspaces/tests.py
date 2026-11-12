import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from market.models import Ad, Category, Country, Product, Shop
from .models import ProjectBrief, SavedAd, SavedProduct, SavedReport, SavedShop, ShopWatch, Workspace


class WorkspaceAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="workspace-owner", password="test-password")
        cls.other = get_user_model().objects.create_user(username="workspace-other", password="test-password")
        cls.workspace = Workspace.objects.create(owner=cls.owner, name="Original project name")
        cls.foreign = Workspace.objects.create(owner=cls.other, name="Private other workspace")
        category = Category.objects.create(slug="lifestyle", label="Test category")
        country = Country.objects.create(code="CA", label="Test country", flag="")
        cls.shop = Shop.objects.create(name="Test shop", domain="test.example", category=category, country=country, external_id="workspace-test-shop", source_kind="demo")
        cls.product = Product.objects.create(name="Test product", shop=cls.shop, category=category, external_id="workspace-test-product", source_kind="demo")
        cls.ad = Ad.objects.create(title="Test ad", product=cls.product, category=category, country=country, platform="meta", format="image", external_id="workspace-test-ad", source_kind="demo")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        self.base = f"/api/v1/workspaces/{self.workspace.pk}"
        self.foreign_base = f"/api/v1/workspaces/{self.foreign.pk}"

    def test_list_and_create_are_owned_without_client_assignable_owner(self):
        response = self.client.get("/api/v1/workspaces/")
        self.assertEqual(response.status_code, 200)
        records = response.json().get("results", []) if isinstance(response.json(), dict) else response.json()
        self.assertEqual([item["id"] for item in records], [str(self.workspace.pk)])
        response = self.client.post("/api/v1/workspaces/", {"name": "New workspace", "owner": self.other.pk}, format="json")
        self.assertEqual(response.status_code, 201)
        created = Workspace.objects.get(pk=response.json()["id"])
        self.assertEqual(created.owner_id, self.owner.pk)
        self.assertTrue(ProjectBrief.objects.filter(workspace=created).exists())

    def test_foreign_workspace_nested_routes_do_not_leak(self):
        for suffix in ("/", "/brief/", "/saved/ads/", "/watches/", "/reports/"):
            with self.subTest(suffix=suffix):
                response = self.client.get(self.foreign_base + suffix)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("Private other workspace", response.content.decode())
        response = self.client.patch(self.foreign_base + "/", {"name": "Changed"}, format="json")
        self.assertEqual(response.status_code, 404)
        response = self.client.put(self.foreign_base + f"/saved/ads/{self.ad.pk}/", {}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_draft_round_trip_and_completion_preserve_workspace_name(self):
        response = self.client.patch(self.base + "/brief/", {"idea": "  Demo fashion shop  ", "name": "Do not rename workspace"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["idea"], "Demo fashion shop")
        self.assertIsNone(response.json()["completed_at"])
        response = self.client.post(self.base + "/brief/complete/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("goal", response.json())
        response = self.client.patch(self.base + "/brief/", {"audience": "consumer", "goal": "market"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["idea"], "Demo fashion shop")
        response = self.client.post(self.base + "/brief/complete/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()["completed_at"])
        self.workspace.refresh_from_db()
        self.assertEqual(self.workspace.name, "Original project name")
        response = self.client.patch(self.base + "/brief/", {"idea": "A revised demo shop"}, format="json")
        self.assertIsNone(response.json()["completed_at"])

    def test_brief_completion_validates_trimmed_values_and_choices(self):
        response = self.client.post(self.base + "/brief/complete/", {"idea": "    x   ", "customer_description": "  ", "goal": "market"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("idea", response.json())
        response = self.client.patch(self.base + "/brief/", {"audience": "unknown"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_bookmarks_are_idempotent_and_reference_catalog_ids(self):
        for kind, target, model in (("ads", self.ad, SavedAd), ("products", self.product, SavedProduct), ("shops", self.shop, SavedShop)):
            with self.subTest(kind=kind):
                url = self.base + f"/saved/{kind}/{target.pk}/"
                first = self.client.put(url, {}, format="json")
                repeat = self.client.put(url, {}, format="json")
                self.assertEqual((first.status_code, repeat.status_code), (201, 200))
                self.assertEqual(first.json()["id"], repeat.json()["id"])
                self.assertEqual(repeat.json()["target_id"], str(target.pk))
                self.assertEqual(repeat.json()["target"]["id"], str(target.pk))
                self.assertEqual(model.objects.filter(workspace=self.workspace).count(), 1)
                listing = self.client.get(self.base + f"/saved/{kind}/").json()
                self.assertEqual(listing["count"], 1)
                self.assertEqual(self.client.delete(url).status_code, 204)
                self.assertEqual(self.client.delete(url).status_code, 204)

    def test_bookmark_invalid_kind_target_and_method_are_safe(self):
        self.assertEqual(self.client.get(self.base + "/saved/unknown/").status_code, 404)
        self.assertEqual(self.client.put(self.base + f"/saved/ads/{uuid.uuid4()}/", {}, format="json").status_code, 404)
        self.assertEqual(self.client.put(self.base + "/saved/ads/", {}, format="json").status_code, 405)
        self.assertEqual(self.client.get(self.base + f"/saved/ads/{self.ad.pk}/").status_code, 405)

    def test_watches_are_stored_preferences_and_can_be_disabled(self):
        url = self.base + f"/shops/{self.shop.pk}/watch/"
        self.assertEqual(self.client.put(url, {}, format="json").status_code, 201)
        response = self.client.put(url, {"enabled": False}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["enabled"])
        self.assertEqual(ShopWatch.objects.filter(workspace=self.workspace).count(), 1)
        self.assertEqual(self.client.get(self.base + "/watches/").json()["count"], 1)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_report_definitions_validate_and_are_private(self):
        payload = {"name": "Demo report", "report_type": "products", "period_days": 30, "filters": {"category": "lifestyle", "search": "shirt"}}
        response = self.client.post(self.base + "/reports/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        report_id = response.json()["id"]
        self.assertEqual(self.client.patch(self.base + f"/reports/{report_id}/", {"filters": {"category": "invalid-category"}}, format="json").status_code, 400)
        self.assertEqual(self.client.get(self.base + f"/reports/{report_id}/run/").status_code, 200)
        self.assertEqual(self.client.patch(self.base + f"/reports/{report_id}/", {"filters": {"sql": "SELECT secret"}}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(self.base + f"/reports/{report_id}/", {"period_days": 365}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(self.base + f"/reports/{report_id}/", {"filters": {"search": ["array"]}}, format="json").status_code, 400)
        foreign_report = SavedReport.objects.create(workspace=self.foreign, name="Private report", report_type="ads")
        self.assertEqual(self.client.get(self.base + f"/reports/{foreign_report.pk}/").status_code, 404)
        self.assertEqual(self.client.get(self.foreign_base + f"/reports/{foreign_report.pk}/").status_code, 404)
        self.assertEqual(self.client.get(self.foreign_base + f"/reports/{foreign_report.pk}/run/").status_code, 404)
        self.assertEqual(self.client.delete(self.base + f"/reports/{report_id}/").status_code, 204)

    def test_anonymous_cannot_access_or_mutate_private_routes(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/v1/workspaces/").status_code, 403)
        self.assertEqual(self.client.post("/api/v1/workspaces/", {"name": "Attempt"}, format="json").status_code, 403)
        self.assertEqual(self.client.put(self.base + f"/saved/ads/{self.ad.pk}/", {}, format="json").status_code, 403)

    def test_authenticated_mutation_requires_real_session_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.patch(self.base + "/brief/", {"idea": "CSRF attempt"}, format="json").status_code, 403)
        token = client.get("/api/v1/auth/csrf/").json()["csrfToken"]
        self.assertEqual(client.patch(self.base + "/brief/", {"idea": "Allowed draft"}, format="json", HTTP_X_CSRFTOKEN=token).status_code, 200)
