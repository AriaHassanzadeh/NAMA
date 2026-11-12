import math
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower, Trim
from django.utils import timezone


class SourceKind(models.TextChoices):
    DEMO = "demo", "Demo"
    MANUAL = "manual", "Manual"
    CSV = "csv", "CSV"
    PROVIDER = "provider", "Provider"


class ValueKind(models.TextChoices):
    ILLUSTRATIVE = "illustrative", "Illustrative"
    OBSERVED = "observed", "Observed"
    ESTIMATED = "estimated", "Estimated"


class Platform(models.TextChoices):
    META = "meta", "Meta"
    TIKTOK = "tiktok", "TikTok"
    YOUTUBE = "youtube", "YouTube"


class AdFormat(models.TextChoices):
    IMAGE = "image", "Image"
    VIDEO = "video", "Video"


def validate_trend(value):
    """A reference chart is ordinal, not a dated market observation."""
    if not isinstance(value, list):
        raise ValidationError("Trend must be an ordinal list.")
    for index, point in enumerate(value):
        if not isinstance(point, dict) or set(point) != {"index", "value"}:
            raise ValidationError("Each trend point needs only index and value.")
        metric = point["value"]
        if (
            isinstance(point["index"], bool)
            or not isinstance(point["index"], int)
            or point["index"] != index
            or isinstance(metric, bool)
            or not isinstance(metric, (int, float))
            or not math.isfinite(metric)
            or metric < 0
        ):
            raise ValidationError("Trend indices must be consecutive; values must be finite and nonnegative.")


class Provenance(models.Model):
    source_kind = models.CharField(max_length=16, choices=SourceKind.choices, default=SourceKind.MANUAL)
    source_reference = models.CharField(max_length=500, blank=True, default="")
    observed_on = models.DateField(null=True, blank=True)
    imported_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class CatalogEntity(Provenance):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=100)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(fields=["source_kind", "external_id"], name="%(app_label)s_%(class)s_source_external_unique"),
        ]


class Category(models.Model):
    slug = models.SlugField(primary_key=True, max_length=80)
    label = models.CharField(max_length=120)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.label


class Country(models.Model):
    code = models.CharField(primary_key=True, max_length=2)
    label = models.CharField(max_length=120)
    flag = models.CharField(max_length=8, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.label


class MediaAsset(models.Model):
    key = models.SlugField(primary_key=True, max_length=80)
    path = models.CharField(max_length=500)
    source_width = models.PositiveIntegerField(null=True, blank=True)
    source_height = models.PositiveIntegerField(null=True, blank=True)
    crop_x = models.PositiveIntegerField(null=True, blank=True)
    crop_y = models.PositiveIntegerField(null=True, blank=True)
    crop_width = models.PositiveIntegerField(null=True, blank=True)
    crop_height = models.PositiveIntegerField(null=True, blank=True)
    media_kind = models.CharField(max_length=12, choices=AdFormat.choices, default=AdFormat.IMAGE)
    video_url = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        ordering = ["key"]


class Tag(models.Model):
    slug = models.SlugField(primary_key=True, max_length=100, allow_unicode=True)
    label = models.CharField(max_length=120)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.label


class Shop(CatalogEntity):
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=253, unique=True)
    initial = models.CharField(max_length=8, blank=True)
    color = models.CharField(max_length=7, default="#e7e7ec")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="shops")
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="shops")
    created_on = models.DateField(null=True, blank=True)

    class Meta(CatalogEntity.Meta):
        ordering = ["name", "pk"]
        constraints = CatalogEntity.Meta.constraints + [
            models.CheckConstraint(condition=models.Q(domain=Lower(Trim("domain"))) & ~models.Q(domain__endswith="."), name="market_shop_domain_normalized"),
        ]

    def save(self, *args, **kwargs):
        self.domain = self.domain.strip().lower().rstrip(".")
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ShopMedia(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="gallery")
    media = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, related_name="shop_placements")
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["shop", "position"], name="market_shop_media_position_unique"),
            models.UniqueConstraint(fields=["shop", "media"], name="market_shop_media_asset_unique"),
        ]


class Product(CatalogEntity):
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    primary_media = models.ForeignKey(MediaAsset, on_delete=models.SET_NULL, related_name="products", null=True, blank=True)
    name = models.CharField(max_length=200)
    english_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    published_on = models.DateField(null=True, blank=True)

    class Meta(CatalogEntity.Meta):
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name


class Ad(CatalogEntity):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="ads")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="ads")
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="ads")
    platform = models.CharField(max_length=16, choices=Platform.choices)
    format = models.CharField(max_length=12, choices=AdFormat.choices)
    primary_media = models.ForeignKey(MediaAsset, on_delete=models.SET_NULL, related_name="ads", null=True, blank=True)
    title = models.CharField(max_length=250)
    copy = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, related_name="ads", blank=True)

    class Meta(CatalogEntity.Meta):
        ordering = ["title", "pk"]
        constraints = CatalogEntity.Meta.constraints + [
            models.CheckConstraint(condition=models.Q(platform__in=Platform.values), name="market_ad_platform_valid"),
            models.CheckConstraint(condition=models.Q(format__in=AdFormat.values), name="market_ad_format_valid"),
        ]

    def __str__(self):
        return self.title


class MetricSnapshot(Provenance):
    value_kind = models.CharField(max_length=16, choices=ValueKind.choices, default=ValueKind.OBSERVED)
    currency = models.CharField(max_length=3, default="USD")

    class Meta:
        abstract = True
        ordering = ["-imported_at", "-pk"]


class ShopMetrics(MetricSnapshot):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="metrics")
    daily_revenue_estimate_amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    monthly_visits_count = models.PositiveBigIntegerField(null=True, blank=True)
    growth_30d_percent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    active_ads_count = models.PositiveIntegerField(null=True, blank=True)
    total_ads_count = models.PositiveIntegerField(null=True, blank=True)
    reported_products_count = models.PositiveIntegerField(null=True, blank=True)
    trend = models.JSONField(default=list, blank=True, validators=[validate_trend])

    class Meta(MetricSnapshot.Meta):
        constraints = [
            models.UniqueConstraint(fields=["shop", "source_kind", "source_reference"], name="market_shop_metrics_source_unique"),
            models.CheckConstraint(condition=models.Q(daily_revenue_estimate_amount__gte=0), name="market_shop_revenue_nonnegative"),
            models.CheckConstraint(condition=models.Q(growth_30d_percent__gte=-100), name="market_shop_growth_minimum"),
        ]


class ProductMetrics(MetricSnapshot):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="metrics")
    price_amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    active_ads_count = models.PositiveIntegerField(null=True, blank=True)
    growth_percent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta(MetricSnapshot.Meta):
        constraints = [
            models.UniqueConstraint(fields=["product", "source_kind", "source_reference"], name="market_product_metrics_source_unique"),
            models.CheckConstraint(condition=models.Q(price_amount__gte=0), name="market_product_price_nonnegative"),
            models.CheckConstraint(condition=models.Q(growth_percent__gte=-100), name="market_product_growth_minimum"),
        ]


class AdMetrics(MetricSnapshot):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="metrics")
    active_days = models.PositiveIntegerField(null=True, blank=True)
    reach_count = models.PositiveBigIntegerField(null=True, blank=True)
    likes_count = models.PositiveBigIntegerField(null=True, blank=True)
    spend_amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    roas_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ctr_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    variant_count = models.PositiveIntegerField(null=True, blank=True)
    trend = models.JSONField(default=list, blank=True, validators=[validate_trend])

    class Meta(MetricSnapshot.Meta):
        constraints = [
            models.UniqueConstraint(fields=["ad", "source_kind", "source_reference"], name="market_ad_metrics_source_unique"),
            models.CheckConstraint(condition=models.Q(spend_amount__gte=0), name="market_ad_spend_nonnegative"),
            models.CheckConstraint(condition=models.Q(roas_ratio__gte=0), name="market_ad_roas_nonnegative"),
            models.CheckConstraint(condition=models.Q(ctr_percent__gte=0, ctr_percent__lte=100), name="market_ad_ctr_range"),
        ]
