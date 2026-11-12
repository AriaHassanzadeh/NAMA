import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from market.models import (
    Ad, AdFormat, AdMetrics, Category, Country, MediaAsset, Platform, Product,
    ProductMetrics, Shop, ShopMedia, ShopMetrics, SourceKind, Tag, ValueKind,
    validate_trend,
)


REFERENCE = "reference/demo/analyze/data.js"
CATEGORY_SLUGS = {
    "مد و پوشاک": "fashion",
    "خانه و آشپزخانه": "home-kitchen",
    "زیبایی و سلامت": "beauty-health",
    "سبک زندگی": "lifestyle",
}
COUNTRY_CODES = {
    "کانادا": "CA", "آمریکا": "US", "انگلستان": "GB", "فرانسه": "FR", "آلمان": "DE",
}
PLATFORMS = {"Meta": Platform.META, "TikTok": Platform.TIKTOK, "YouTube": Platform.YOUTUBE}
FORMATS = {"تصویر": AdFormat.IMAGE, "ویدیو": AdFormat.VIDEO}


def source_reference(collection, external_id):
    return f"{REFERENCE}#{collection}/{external_id}"


def decimal(value):
    return Decimal(str(value)) if value is not None else None


def ordinal_trend(values):
    points = [{"index": index, "value": value} for index, value in enumerate(values)]
    validate_trend(points)
    return points


class Command(BaseCommand):
    help = "Upsert only the explicitly illustrative reference demo; preserve other sources and record IDs."

    def handle(self, *args, **options):
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "reference_demo.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        try:
            with transaction.atomic():
                self.seed(data)
        except IntegrityError as exc:
            raise CommandError(
                "Demo seed conflicted with existing data; all changes rolled back. No records were deleted or reassigned."
            ) from exc
        self.stdout.write(self.style.SUCCESS(
            "Seeded demo only: 6 shops, 8 products, 10 ads, 9 media assets. Metrics are illustrative USD values; observation dates remain unknown."
        ))

    def seed(self, data):
        imported_at = timezone.now()

        def provenance(collection, external_id):
            return {
                "source_reference": source_reference(collection, external_id),
                "observed_on": None,
                "imported_at": imported_at,
            }

        def snapshot(model, relation, entity, collection, external_id, values):
            reference = source_reference(collection, external_id) + "/metrics"
            model.objects.update_or_create(
                **{relation: entity}, source_kind=SourceKind.DEMO, source_reference=reference,
                defaults={
                    "observed_on": None, "imported_at": imported_at,
                    "value_kind": ValueKind.ILLUSTRATIVE, "currency": "USD", **values,
                },
            )

        categories = {}
        for label in data["categories"]:
            category, _ = Category.objects.update_or_create(slug=CATEGORY_SLUGS[label], defaults={"label": label})
            categories[label] = category

        countries = {}
        for label in data["countries"]:
            flag = next(shop["flag"] for shop in data["shops"] if shop["country"] == label)
            country, _ = Country.objects.update_or_create(code=COUNTRY_CODES[label], defaults={"label": label, "flag": flag})
            countries[label] = country

        media_assets = {}
        for key, raw in data["media"].items():
            media, _ = MediaAsset.objects.update_or_create(key=key, defaults={
                "path": "/demo-assets/" + Path(raw["src"]).name,
                "source_width": raw.get("sw"), "source_height": raw.get("sh"),
                "crop_x": raw.get("x"), "crop_y": raw.get("y"),
                "crop_width": raw.get("w"), "crop_height": raw.get("h"),
                # A reference video-format ad still only has a thumbnail asset.
                "media_kind": AdFormat.IMAGE, "video_url": None,
            })
            media_assets[key] = media

        shops = {}
        for raw in data["shops"]:
            shop, _ = Shop.objects.update_or_create(
                source_kind=SourceKind.DEMO, external_id=raw["id"],
                defaults={
                    **provenance("shops", raw["id"]),
                    "name": raw["name"], "domain": raw["domain"], "initial": raw["initial"],
                    "color": raw["color"], "category": categories[raw["category"]],
                    "country": countries[raw["country"]], "created_on": date.fromisoformat(raw["created"]),
                },
            )
            shops[raw["id"]] = shop
            for position, media_key in enumerate(raw["media"]):
                ShopMedia.objects.update_or_create(shop=shop, position=position, defaults={"media": media_assets[media_key]})
            snapshot(ShopMetrics, "shop", shop, "shops", raw["id"], {
                "daily_revenue_estimate_amount": decimal(raw["revenue"]),
                "monthly_visits_count": raw["visits"], "growth_30d_percent": decimal(raw["growth"]),
                "active_ads_count": raw["active"], "total_ads_count": raw["total"],
                "reported_products_count": raw["products"], "trend": ordinal_trend(raw["trend"]),
            })

        products = {}
        for raw in data["products"]:
            product, _ = Product.objects.update_or_create(
                source_kind=SourceKind.DEMO, external_id=raw["id"],
                defaults={
                    **provenance("products", raw["id"]),
                    "shop": shops[raw["shop"]], "category": categories[raw["category"]],
                    "primary_media": media_assets[raw["media"]], "name": raw["name"],
                    "english_name": raw["english"], "description": raw["description"],
                    "published_on": date.fromisoformat(raw["published"]),
                },
            )
            products[raw["id"]] = product
            snapshot(ProductMetrics, "product", product, "products", raw["id"], {
                "price_amount": decimal(raw["price"]), "active_ads_count": raw["active"],
                "growth_percent": decimal(raw["growth"]),
            })

        for raw in data["ads"]:
            product = products[raw["product"]]
            if product.shop_id != shops[raw["shop"]].pk:
                raise CommandError("Reference product/shop relationships disagree; seed was rolled back.")
            ad, _ = Ad.objects.update_or_create(
                source_kind=SourceKind.DEMO, external_id=raw["id"],
                defaults={
                    **provenance("ads", raw["id"]), "product": product,
                    "category": categories[raw["category"]], "country": countries[raw["country"]],
                    "platform": PLATFORMS[raw["platform"]], "format": FORMATS[raw["format"]],
                    "primary_media": media_assets[raw["media"]], "title": raw["title"], "copy": raw["copy"],
                },
            )
            tags = [Tag.objects.update_or_create(slug=slugify(label, allow_unicode=True), defaults={"label": label})[0] for label in raw["tags"]]
            ad.tags.set(tags)
            snapshot(AdMetrics, "ad", ad, "ads", raw["id"], {
                "active_days": raw["active"], "reach_count": raw["reach"], "likes_count": raw["likes"],
                "spend_amount": decimal(raw["spend"]), "roas_ratio": decimal(raw["roas"]),
                "ctr_percent": decimal(raw["ctr"]), "variant_count": raw["variants"],
                "trend": ordinal_trend(raw["trend"]),
            })
