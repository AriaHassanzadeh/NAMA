from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Ad, AdMetrics, Category, Country, MediaAsset, Product, ProductMetrics, Shop, ShopMedia, ShopMetrics, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["slug", "label"]


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["code", "label", "flag"]


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["slug", "label"]


class TrendPointSerializer(serializers.Serializer):
    index = serializers.IntegerField(min_value=0)
    value = serializers.FloatField()


class AdMetricsSerializer(serializers.ModelSerializer):
    trend = TrendPointSerializer(many=True, read_only=True)
    class Meta:
        model = AdMetrics
        fields = "__all__"


class ProductMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMetrics
        fields = "__all__"


class ShopMetricsSerializer(serializers.ModelSerializer):
    trend = TrendPointSerializer(many=True, read_only=True)
    class Meta:
        model = ShopMetrics
        fields = "__all__"


PROVENANCE = ["source_kind", "source_reference", "observed_on", "imported_at"]


def latest_snapshot(obj, serializer):
    snapshots = getattr(obj, "_snapshots", None)
    if snapshots is None:
        snapshots = list(obj.metrics.filter(source_kind="demo")[:1])
    return serializer(snapshots[0]).data if snapshots else None


class ShopSummarySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    country = CountrySerializer(read_only=True)
    class Meta:
        model = Shop
        fields = ["id", "external_id", "name", "domain", "initial", "color", "category", "country", "created_on", *PROVENANCE]


class ProductSummarySerializer(serializers.ModelSerializer):
    shop = ShopSummarySerializer(read_only=True)
    primary_media = MediaAssetSerializer(read_only=True)
    class Meta:
        model = Product
        fields = ["id", "external_id", "name", "english_name", "shop", "primary_media", *PROVENANCE]


class AdPreviewSerializer(serializers.ModelSerializer):
    primary_media = MediaAssetSerializer(read_only=True)
    class Meta:
        model = Ad
        fields = ["id", "title", "format", "primary_media", "source_kind"]


class ProductPreviewSerializer(serializers.ModelSerializer):
    primary_media = MediaAssetSerializer(read_only=True)
    class Meta:
        model = Product
        fields = ["id", "name", "primary_media", "source_kind"]


class AdSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(read_only=True)
    shop = ShopSummarySerializer(source="product.shop", read_only=True)
    primary_media = MediaAssetSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    country = CountrySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    latest_metrics = serializers.SerializerMethodField()
    class Meta:
        model = Ad
        fields = ["id", "external_id", "title", "copy", "product", "shop", "primary_media", "category", "country", "platform", "format", "tags", "latest_metrics", *PROVENANCE]

    @extend_schema_field(AdMetricsSerializer(allow_null=True))
    def get_latest_metrics(self, obj):
        return latest_snapshot(obj, AdMetricsSerializer)


class ProductSerializer(ProductSummarySerializer):
    category = CategorySerializer(read_only=True)
    latest_metrics = serializers.SerializerMethodField()
    related_ads = serializers.SerializerMethodField()
    actual_ads_count = serializers.SerializerMethodField()
    class Meta(ProductSummarySerializer.Meta):
        fields = [*ProductSummarySerializer.Meta.fields, "description", "published_on", "category", "latest_metrics", "related_ads", "actual_ads_count"]

    @extend_schema_field(ProductMetricsSerializer(allow_null=True))
    def get_latest_metrics(self, obj):
        return latest_snapshot(obj, ProductMetricsSerializer)

    @extend_schema_field(AdPreviewSerializer(many=True))
    def get_related_ads(self, obj):
        return AdPreviewSerializer(obj.ads.all()[:3], many=True).data

    def get_actual_ads_count(self, obj) -> int:
        return len(obj.ads.all())


class ShopMediaSerializer(serializers.ModelSerializer):
    media = MediaAssetSerializer(read_only=True)
    class Meta:
        model = ShopMedia
        fields = ["position", "media"]


class ShopSerializer(ShopSummarySerializer):
    latest_metrics = serializers.SerializerMethodField()
    gallery = ShopMediaSerializer(many=True, read_only=True)
    related_products = serializers.SerializerMethodField()
    related_ads = serializers.SerializerMethodField()
    actual_products_count = serializers.SerializerMethodField()
    actual_ads_count = serializers.SerializerMethodField()
    class Meta(ShopSummarySerializer.Meta):
        fields = [*ShopSummarySerializer.Meta.fields, "latest_metrics", "gallery", "related_products", "related_ads", "actual_products_count", "actual_ads_count"]

    @extend_schema_field(ShopMetricsSerializer(allow_null=True))
    def get_latest_metrics(self, obj):
        return latest_snapshot(obj, ShopMetricsSerializer)

    @extend_schema_field(ProductPreviewSerializer(many=True))
    def get_related_products(self, obj):
        return ProductPreviewSerializer(obj.products.all()[:3], many=True).data

    @extend_schema_field(AdPreviewSerializer(many=True))
    def get_related_ads(self, obj):
        ads = [ad for product in obj.products.all() for ad in product.ads.all()][:3]
        return AdPreviewSerializer(ads, many=True).data

    def get_actual_products_count(self, obj) -> int:
        return len(obj.products.all())

    def get_actual_ads_count(self, obj) -> int:
        return sum(len(product.ads.all()) for product in obj.products.all())
