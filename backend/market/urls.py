from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .api import AdViewSet, CatalogExportView, FilterOptionsView, HomeView, ProductViewSet, ReportOverviewView, SavedReportRunView, ShopViewSet

router = SimpleRouter()
router.register("ads", AdViewSet, basename="ad")
router.register("products", ProductViewSet, basename="product")
router.register("shops", ShopViewSet, basename="shop")

urlpatterns = [
    path("filter-options/", FilterOptionsView.as_view(), name="filter-options"),
    path("home/", HomeView.as_view(), name="home-data"),
    path("reports/overview/", ReportOverviewView.as_view(), name="report-overview"),
    path("workspaces/<uuid:workspace_id>/reports/<uuid:report_id>/run/", SavedReportRunView.as_view(), name="saved-report-run"),
    path("<str:kind>/export/", CatalogExportView.as_view(), name="catalog-export"),
    path("products/<uuid:product_id>/ads/", AdViewSet.as_view({"get": "list"}), name="product-ads"),
    path("shops/<uuid:shop_id>/ads/", AdViewSet.as_view({"get": "list"}), name="shop-ads"),
    path("shops/<uuid:shop_id>/products/", ProductViewSet.as_view({"get": "list"}), name="shop-products"),
    path("", include(router.urls)),
]
