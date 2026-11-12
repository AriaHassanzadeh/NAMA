from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView
from demo.views import EntryOptionsView
from health.views import HealthView
from .api_schema import configure_api_schema

configure_api_schema()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthView.as_view(), name="health"),
    path("api/v1/demo/entry-options/", EntryOptionsView.as_view(), name="entry-options"),
    path("api/v1/schema/", SpectacularJSONAPIView.as_view(), name="api-schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/v1/auth/", include("accounts.api")),
    path("api/v1/", include("workspaces.urls")),
    path("api/v1/", include("market.urls")),
]
