from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import TestCase

from market.models import (
    Ad, AdMetrics, Category, Country, MediaAsset, Product, ProductMetrics,
    Shop, ShopMedia, ShopMetrics, SourceKind, Tag, ValueKind,
)


class SeedDemoTests(TestCase):
    def seed(self):
        call_command("seed_demo", stdout=StringIO())

    def test_repeat_seed_preserves_ids_and_relationships(self):
        self.seed()
        ids = {model.__name__: dict(model.objects.values_list("external_id", "pk")) for model in (Shop, Product, Ad)}
        snapshot_ids = {model.__name__: list(model.objects.order_by("pk").values_list("pk", flat=True)) for model in (ShopMetrics, ProductMetrics, AdMetrics)}
        self.seed()
        for model, count in ((Shop, 6), (Product, 8), (Ad, 10)):
            self.assertEqual(model.objects.count(), count)
            self.assertEqual(dict(model.objects.values_list("external_id", "pk")), ids[model.__name__])
            self.assertEqual(model.objects.filter(source_kind=SourceKind.DEMO, observed_on__isnull=True).count(), count)
        for model, count in ((ShopMetrics, 6), (ProductMetrics, 8), (AdMetrics, 10)):
            self.assertEqual(model.objects.count(), count)
            self.assertEqual(list(model.objects.order_by("pk").values_list("pk", flat=True)), snapshot_ids[model.__name__])
            self.assertEqual(model.objects.filter(source_kind=SourceKind.DEMO, value_kind=ValueKind.ILLUSTRATIVE, currency="USD", observed_on__isnull=True).count(), count)
        self.assertEqual(MediaAsset.objects.count(), 9)
        self.assertEqual(ShopMedia.objects.count(), 18)
        self.assertEqual(Category.objects.count(), 4)
        self.assertEqual(Country.objects.count(), 5)
        self.assertGreater(Tag.objects.count(), 0)
        ad = Ad.objects.get(source_kind=SourceKind.DEMO, external_id="a1")
        self.assertEqual(ad.product.external_id, "p5")
        self.assertEqual(ad.product.shop.external_id, "s5")
        self.assertEqual(ad.metrics.get().roas_ratio, Decimal("4.11"))
        self.assertEqual(ad.metrics.get().trend[0], {"index": 0, "value": 9})
        self.assertEqual(ad.primary_media.crop_x, 381)
        self.assertEqual(ad.primary_media.path, "/demo-assets/ads-reference.jpg")
        self.assertEqual(ad.primary_media.media_kind, "image")
        self.assertIsNone(ad.primary_media.video_url)
        self.assertEqual(set(ad.tags.values_list("label", flat=True)), {"نمایش کاربرد", "مسئله و راه‌حل"})

    def test_seed_preserves_manual_records_and_manual_snapshot(self):
        self.seed()
        category = Category.objects.get(pk="lifestyle")
        country = Country.objects.get(pk="CA")
        shop = Shop.objects.create(external_id="s1", name="Manual shop", domain=" MANUAL.EXAMPLE. ", category=category, country=country)
        product = Product.objects.create(external_id="p1", name="Manual product", shop=shop, category=category)
        ad = Ad.objects.create(external_id="a1", title="Manual ad", product=product, category=category, country=country, platform="meta", format="image")
        demo_ad = Ad.objects.get(source_kind=SourceKind.DEMO, external_id="a1")
        manual_metrics = AdMetrics.objects.create(ad=demo_ad, source_kind=SourceKind.MANUAL, source_reference=demo_ad.metrics.get().source_reference, reach_count=321)
        self.seed()
        for entity in (shop, product, ad):
            entity.refresh_from_db()
            self.assertEqual(entity.source_kind, SourceKind.MANUAL)
        self.assertEqual(shop.name, "Manual shop")
        self.assertEqual(shop.domain, "manual.example")
        self.assertEqual(product.name, "Manual product")
        self.assertEqual(ad.title, "Manual ad")
        manual_metrics.refresh_from_db()
        self.assertEqual(manual_metrics.reach_count, 321)
        self.assertEqual((Shop.objects.count(), Product.objects.count(), Ad.objects.count()), (7, 9, 11))

    def test_reported_metrics_remain_distinct_from_fixture_record_counts(self):
        self.seed()
        shop = Shop.objects.get(source_kind=SourceKind.DEMO, external_id="s3")
        self.assertEqual(shop.metrics.get().reported_products_count, 38)
        self.assertEqual(shop.products.count(), 2)
        self.assertEqual(shop.metrics.get().active_ads_count, 192)
        self.assertEqual(Ad.objects.filter(product__shop=shop).count(), 3)
        product = Product.objects.get(source_kind=SourceKind.DEMO, external_id="p1")
        self.assertEqual(product.metrics.get().active_ads_count, 20)
        self.assertEqual(product.ads.count(), 1)

    def test_domain_collision_rolls_back_without_overwriting_manual_shop(self):
        category = Category.objects.create(slug="manual", label="Manual")
        country = Country.objects.create(code="ZZ", label="Manual")
        manual = Shop.objects.create(external_id="private", name="Keep me", domain="nord.example", category=category, country=country)
        with self.assertRaises(CommandError):
            self.seed()
        manual.refresh_from_db()
        self.assertEqual(manual.name, "Keep me")
        self.assertEqual(Shop.objects.count(), 1)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(MediaAsset.objects.count(), 0)

    def test_database_rejects_invalid_ctr_but_accepts_negative_growth(self):
        self.seed()
        metrics = AdMetrics.objects.first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            AdMetrics.objects.filter(pk=metrics.pk).update(ctr_percent=Decimal("101"))
        shop_metrics = ShopMetrics.objects.first()
        ShopMetrics.objects.filter(pk=shop_metrics.pk).update(growth_30d_percent=Decimal("-12.5"))
        shop_metrics.refresh_from_db()
        self.assertEqual(shop_metrics.growth_30d_percent, Decimal("-12.50"))
