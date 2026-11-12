from django.contrib import admin

from .models import (
    Ad, AdMetrics, Category, Country, MediaAsset, Product, ProductMetrics,
    Shop, ShopMedia, ShopMetrics, Tag,
)


@admin.register(Shop, Product, Ad)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ("__str__", "external_id", "source_kind", "observed_on", "imported_at")
    list_filter = ("source_kind",)
    readonly_fields = ("id",)


admin.site.register([Category, Country, MediaAsset, Tag, ShopMedia, ShopMetrics, ProductMetrics, AdMetrics])
