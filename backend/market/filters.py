from rest_framework import serializers


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "Unsupported parameter." for key in sorted(unknown)})
        return super().to_internal_value(data)


class CatalogFilterSerializer(StrictSerializer):
    search = serializers.CharField(max_length=200, required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=["fashion", "home-kitchen", "beauty-health", "lifestyle"], required=False)
    country = serializers.ChoiceField(choices=["CA", "US", "GB", "FR", "DE"], required=False)
    source_kind = serializers.ChoiceField(choices=["demo"], default="demo")
    page = serializers.IntegerField(min_value=1, max_value=1000000, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=12)


class AdFilterSerializer(CatalogFilterSerializer):
    platform = serializers.ChoiceField(choices=["meta", "tiktok", "youtube"], required=False)
    format = serializers.ChoiceField(choices=["image", "video"], required=False)
    min_active_days = serializers.IntegerField(min_value=0, max_value=36500, required=False)
    ordering = serializers.ChoiceField(choices=["-reach", "-roas", "-active_days", "active_days"], default="-reach")
    shop = serializers.UUIDField(required=False)
    product = serializers.UUIDField(required=False)


class ProductFilterSerializer(CatalogFilterSerializer):
    max_price = serializers.DecimalField(max_digits=16, decimal_places=2, min_value=0, required=False)
    min_active_ads = serializers.IntegerField(min_value=0, required=False)
    ordering = serializers.ChoiceField(choices=["-growth", "price", "-active_ads", "-published_on"], default="-published_on")
    one_per_shop = serializers.BooleanField(default=False)
    shop = serializers.UUIDField(required=False)


class ShopFilterSerializer(CatalogFilterSerializer):
    min_daily_revenue = serializers.DecimalField(max_digits=16, decimal_places=2, min_value=0, required=False)
    min_growth = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=-100, required=False)
    min_active_ads = serializers.IntegerField(min_value=0, required=False)
    ordering = serializers.ChoiceField(choices=["-growth", "-revenue", "-visits", "-active_ads"], default="-growth")


class OverviewFilterSerializer(StrictSerializer):
    focus = serializers.ChoiceField(choices=["ads", "products", "shops"], default="ads")
    period_days = serializers.ChoiceField(choices=[7, 30, 90], default=30)
    category = CatalogFilterSerializer().fields["category"]
    country = CatalogFilterSerializer().fields["country"]


class HomeFilterSerializer(OverviewFilterSerializer):
    selection_index = serializers.IntegerField(min_value=0, max_value=9, default=0)


class CompareFilterSerializer(StrictSerializer):
    ids = serializers.CharField(max_length=150)

    def validate_ids(self, value):
        from uuid import UUID
        parts = value.split(",")
        if not 2 <= len(parts) <= 3 or len(set(parts)) != len(parts):
            raise serializers.ValidationError("Choose two or three different ad IDs.")
        try:
            return [UUID(part) for part in parts]
        except ValueError:
            raise serializers.ValidationError("Each ID must be a UUID.") from None
