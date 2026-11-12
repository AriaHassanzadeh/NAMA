import csv
import io
from collections import Counter
from decimal import Decimal
from urllib.parse import urlsplit, urlunsplit

from django.db.models import F, OuterRef, Prefetch, Q, Subquery, Window
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import RowNumber
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .api_serializers import AdSerializer, CategorySerializer, CountrySerializer, ProductSerializer, ShopSerializer, TrendPointSerializer
from .filters import AdFilterSerializer, CompareFilterSerializer, HomeFilterSerializer, OverviewFilterSerializer, ProductFilterSerializer, ShopFilterSerializer
from .models import Ad, AdMetrics, Category, Country, Product, ProductMetrics, Shop, ShopMedia, ShopMetrics

DEMO_LABEL = "داده‌های نمایشی؛ بدون اتصال به بازار واقعی"
PROVENANCE = {"source_kind": "demo", "label": DEMO_LABEL}


def metric_annotations(model, foreign_key, fields):
    latest = model.objects.filter(**{foreign_key: OuterRef("pk")}, source_kind="demo").order_by("-imported_at", "-pk")
    return {alias: Subquery(latest.values(field)[:1]) for alias, field in fields.items()}


def catalog_queryset(kind):
    preview_ads = Ad.objects.filter(source_kind="demo").select_related("primary_media").order_by("external_id", "pk")
    if kind == "ads":
        return Ad.objects.filter(source_kind="demo").select_related(
            "category", "country", "primary_media", "product__primary_media", "product__shop__category", "product__shop__country",
        ).prefetch_related("tags", Prefetch("metrics", AdMetrics.objects.filter(source_kind="demo"), to_attr="_snapshots")).annotate(
            **metric_annotations(AdMetrics, "ad_id", {"_reach": "reach_count", "_roas": "roas_ratio", "_active_days": "active_days"}),
        )
    if kind == "products":
        return Product.objects.filter(source_kind="demo").select_related(
            "category", "primary_media", "shop__category", "shop__country",
        ).prefetch_related(Prefetch("ads", preview_ads), Prefetch("metrics", ProductMetrics.objects.filter(source_kind="demo"), to_attr="_snapshots")).annotate(
            **metric_annotations(ProductMetrics, "product_id", {"_price": "price_amount", "_active_ads": "active_ads_count", "_growth": "growth_percent"}),
        )
    preview_products = Product.objects.filter(source_kind="demo").select_related("primary_media").prefetch_related(Prefetch("ads", preview_ads)).order_by("external_id", "pk")
    return Shop.objects.filter(source_kind="demo").select_related("category", "country").prefetch_related(
        Prefetch("gallery", ShopMedia.objects.select_related("media")), Prefetch("products", preview_products),
        Prefetch("metrics", ShopMetrics.objects.filter(source_kind="demo"), to_attr="_snapshots"),
    ).annotate(**metric_annotations(ShopMetrics, "shop_id", {"_revenue": "daily_revenue_estimate_amount", "_visits": "monthly_visits_count", "_growth": "growth_30d_percent", "_active_ads": "active_ads_count"}))


FILTERS = {"ads": AdFilterSerializer, "products": ProductFilterSerializer, "shops": ShopFilterSerializer}
SERIALIZERS = {"ads": AdSerializer, "products": ProductSerializer, "shops": ShopSerializer}


def order_expression(kind, ordering):
    columns = {
        "ads": {"reach": "_reach", "roas": "_roas", "active_days": "_active_days"},
        "products": {"growth": "_growth", "price": "_price", "active_ads": "_active_ads", "published_on": "published_on"},
        "shops": {"growth": "_growth", "revenue": "_revenue", "visits": "_visits", "active_ads": "_active_ads"},
    }
    value = F(columns[kind][ordering.lstrip("-")])
    return value.desc(nulls_last=True) if ordering.startswith("-") else value.asc(nulls_last=True)


def filtered_catalog(kind, parameters):
    validator = FILTERS[kind](data=parameters)
    validator.is_valid(raise_exception=True)
    data = validator.validated_data
    query = catalog_queryset(kind)
    if data.get("category"):
        query = query.filter(category_id=data["category"])
    if data.get("country"):
        query = query.filter(**{"shop__country_id" if kind == "products" else "country_id": data["country"]})
    if data.get("search"):
        paths = {"ads": ["title", "copy", "product__name", "product__english_name", "product__shop__name", "product__shop__domain"], "products": ["name", "english_name", "shop__name", "shop__domain"], "shops": ["name", "domain"]}[kind]
        condition = Q()
        for path in paths:
            condition |= Q(**{path + "__icontains": data["search"]})
        query = query.filter(condition)
    if kind == "ads":
        for field in ("platform", "format", "product"):
            if field in data:
                query = query.filter(**{field: data[field]})
        if "shop" in data:
            query = query.filter(product__shop_id=data["shop"])
        if "min_active_days" in data:
            query = query.filter(_active_days__gte=data["min_active_days"])
    elif kind == "products":
        if "shop" in data:
            query = query.filter(shop_id=data["shop"])
        if "max_price" in data:
            query = query.filter(_price__lte=data["max_price"])
        if "min_active_ads" in data:
            query = query.filter(_active_ads__gte=data["min_active_ads"])
    else:
        for parameter, column in [("min_daily_revenue", "_revenue"), ("min_growth", "_growth"), ("min_active_ads", "_active_ads")]:
            if parameter in data:
                query = query.filter(**{column + "__gte": data[parameter]})
    ordering = order_expression(kind, data["ordering"])
    if kind == "products" and data["one_per_shop"]:
        query = query.annotate(_shop_rank=Window(RowNumber(), partition_by=[F("shop_id")], order_by=[ordering, F("pk").asc()])).filter(_shop_rank=1)
    return query.order_by(ordering, "pk")


class DemoPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        def relative(link):
            if link is None:
                return None
            value = urlsplit(link)
            return urlunsplit(("", "", value.path, value.query, value.fragment))
        return Response({**PROVENANCE, "count": self.page.paginator.count, "next": relative(self.get_next_link()), "previous": relative(self.get_previous_link()), "results": data})

    def get_paginated_response_schema(self, schema):
        result = super().get_paginated_response_schema(schema)
        result["properties"].update(source_kind={"type": "string", "enum": ["demo"]}, label={"type": "string"})
        for key in ("next", "previous"):
            result["properties"][key]["format"] = "uri-reference"
        result["required"] = [*result.get("required", []), "source_kind", "label"]
        return result


@method_decorator(never_cache, name="dispatch")
class DemoReadView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ["get", "head", "options"]


@method_decorator(never_cache, name="dispatch")
class CatalogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = DemoPagination
    lookup_value_regex = "[0-9a-fA-F-]{36}"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        query = filtered_catalog(self.kind, self.request.query_params) if self.action == "list" else catalog_queryset(self.kind)
        if "shop_id" in self.kwargs:
            shop = get_object_or_404(Shop, pk=self.kwargs["shop_id"], source_kind="demo")
            query = query.filter(**{"product__shop": shop} if self.kind == "ads" else {"shop": shop})
        if "product_id" in self.kwargs:
            product = get_object_or_404(Product, pk=self.kwargs["product_id"], source_kind="demo")
            query = query.filter(product=product)
        return query


@extend_schema_view(list=extend_schema(parameters=[AdFilterSerializer]))
class AdViewSet(CatalogViewSet):
    kind = "ads"
    serializer_class = AdSerializer
    queryset = Ad.objects.none()

    @extend_schema(parameters=[CompareFilterSerializer], responses=AdSerializer(many=True))
    @action(detail=False, methods=["get"], pagination_class=None)
    def compare(self, request):
        validator = CompareFilterSerializer(data=request.query_params)
        validator.is_valid(raise_exception=True)
        identifiers = validator.validated_data["ids"]
        records = {item.pk: item for item in catalog_queryset("ads").filter(pk__in=identifiers)}
        if len(records) != len(identifiers):
            raise ValidationError({"ids": "One or more demo ads do not exist."})
        return Response(AdSerializer([records[key] for key in identifiers], many=True).data)


@extend_schema_view(list=extend_schema(parameters=[ProductFilterSerializer]))
class ProductViewSet(CatalogViewSet):
    kind = "products"
    serializer_class = ProductSerializer
    queryset = Product.objects.none()


@extend_schema_view(list=extend_schema(parameters=[ShopFilterSerializer]))
class ShopViewSet(CatalogViewSet):
    kind = "shops"
    serializer_class = ShopSerializer
    queryset = Shop.objects.none()


class FilterOptionsSerializer(serializers.Serializer):
    source_kind = serializers.CharField()
    label = serializers.CharField()
    categories = CategorySerializer(many=True)
    countries = CountrySerializer(many=True)
    platforms = serializers.ListField(child=serializers.CharField())
    formats = serializers.ListField(child=serializers.CharField())


class FilterOptionsView(DemoReadView):
    @extend_schema(responses=FilterOptionsSerializer)
    def get(self, request):
        return Response({**PROVENANCE, "categories": CategorySerializer(Category.objects.all(), many=True).data, "countries": CountrySerializer(Country.objects.all(), many=True).data, "platforms": ["meta", "tiktok", "youtube"], "formats": ["image", "video"]})


class CountsSerializer(serializers.Serializer):
    ads = serializers.IntegerField()
    products = serializers.IntegerField()
    shops = serializers.IntegerField()


class HomeResponseSerializer(serializers.Serializer):
    source_kind = serializers.CharField()
    label = serializers.CharField()
    selection_index = serializers.IntegerField()
    available_record_counts = CountsSerializer()
    featured_ads = AdSerializer(many=True)
    featured_products = ProductSerializer(many=True)
    featured_shops = ShopSerializer(many=True)


class HomeView(DemoReadView):
    @extend_schema(parameters=[HomeFilterSerializer], responses=HomeResponseSerializer)
    def get(self, request):
        validator = HomeFilterSerializer(data=request.query_params)
        validator.is_valid(raise_exception=True)
        params = validator.validated_data
        common = {key: params[key] for key in ("country", "category") if key in params}
        records = {kind: list(filtered_catalog(kind, common)) for kind in SERIALIZERS}
        featured = {}
        for kind, items in records.items():
            start = params["selection_index"] % len(items) if items else 0
            featured["featured_" + kind] = SERIALIZERS[kind]((items[start:] + items[:start])[:3], many=True).data
        return Response({**PROVENANCE, "selection_index": params["selection_index"], "available_record_counts": {key: len(value) for key, value in records.items()}, **featured})


class ReportMetricSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField(allow_null=True)
    unit = serializers.CharField()
    aggregation = serializers.CharField()
    value_kind = serializers.CharField()


class DistributionSerializer(serializers.Serializer):
    platform = serializers.CharField()
    count = serializers.IntegerField()


class ReportResponseSerializer(serializers.Serializer):
    source_kind = serializers.CharField()
    label = serializers.CharField()
    focus = serializers.CharField()
    period_days_requested = serializers.IntegerField()
    period_filter_applied = serializers.BooleanField()
    period_notice = serializers.CharField()
    available_record_counts = CountsSerializer()
    metrics = ReportMetricSerializer(many=True)
    platform_distribution = DistributionSerializer(many=True)
    distribution_basis = serializers.CharField()
    trend_basis = serializers.CharField()
    trend_points = TrendPointSerializer(many=True)


def build_report(focus, period_days, filters):
    common = {key: value for key, value in filters.items() if key in ("category", "country")}
    records = {kind: list(filtered_catalog(kind, {**common, **(filters if kind == focus else {})})) for kind in SERIALIZERS}
    snapshots = [item._snapshots[0] for item in records[focus] if item._snapshots]
    definitions = {
        "ads": [("reach_count", "count", "sum"), ("likes_count", "count", "sum"), ("spend_amount", "USD", "sum"), ("roas_ratio", "ratio", "mean"), ("ctr_percent", "percent", "mean")],
        "products": [("price_amount", "USD", "mean"), ("active_ads_count", "reported_count", "sum"), ("growth_percent", "percent", "mean")],
        "shops": [("daily_revenue_estimate_amount", "USD_per_day_estimate", "sum"), ("monthly_visits_count", "monthly_visits", "sum"), ("growth_30d_percent", "percent", "mean"), ("active_ads_count", "reported_count", "sum")],
    }
    metrics = []
    for field, unit, aggregation in definitions[focus]:
        values = [Decimal(str(getattr(snapshot, field))) for snapshot in snapshots if getattr(snapshot, field) is not None]
        amount = sum(values) / (len(values) if aggregation == "mean" else 1) if values else None
        metrics.append({"key": field, "value": str(amount.quantize(Decimal("0.01"))) if amount is not None else None, "unit": unit, "aggregation": aggregation, "value_kind": "illustrative"})
    trends = [getattr(snapshot, "trend", []) for snapshot in snapshots]
    points = []
    for index in range(max((len(trend) for trend in trends), default=0)):
        values = [trend[index]["value"] for trend in trends if index < len(trend)]
        points.append({"index": index, "value": round(sum(values) / len(values), 2)})
    distribution = Counter(item.platform for item in records["ads"])
    return {**PROVENANCE, "focus": focus, "period_days_requested": period_days, "period_filter_applied": False,
            "period_notice": "نمودارها شاخص نسبی و بدون تاریخ‌اند؛ بازهٔ زمانی روی این داده‌های نمایشی اعمال نشده است.",
            "available_record_counts": {key: len(value) for key, value in records.items()}, "metrics": metrics,
            "platform_distribution": [{"platform": key, "count": value} for key, value in sorted(distribution.items())],
            "distribution_basis": "demo_ad_record_count", "trend_basis": "mean_undated_relative_index", "trend_points": points}


class ReportOverviewView(DemoReadView):
    @extend_schema(parameters=[OverviewFilterSerializer], responses=ReportResponseSerializer)
    def get(self, request):
        validator = OverviewFilterSerializer(data=request.query_params)
        validator.is_valid(raise_exception=True)
        data = validator.validated_data
        return Response(build_report(data["focus"], data["period_days"], {key: data[key] for key in ("category", "country") if key in data}))


@method_decorator(never_cache, name="dispatch")
class SavedReportRunView(APIView):
    @extend_schema(responses=ReportResponseSerializer)
    def get(self, request, workspace_id, report_id):
        from workspaces.models import SavedReport
        record = get_object_or_404(SavedReport, pk=report_id, workspace_id=workspace_id, workspace__owner=request.user)
        return Response(build_report(record.report_type, record.period_days, record.filters))


class CatalogExportView(DemoReadView):
    @extend_schema(responses={(200, "text/csv"): str}, description="Demo-only CSV, with explicit USD/provenance columns; maximum 1000 records.")
    def get(self, request, kind):
        if kind not in SERIALIZERS:
            raise ValidationError({"kind": "Choose ads, products or shops."})
        records = filtered_catalog(kind, request.query_params)[:1000]
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(["id", "name", "source_kind", "value_kind", "currency", "metrics_json"])
        import json
        for item in records:
            name = getattr(item, "name", getattr(item, "title", ""))
            if name.startswith(("=", "+", "-", "@")):
                name = "'" + name
            snapshot = item._snapshots[0] if item._snapshots else None
            metric = SERIALIZERS[kind](item).data["latest_metrics"]
            writer.writerow([item.pk, name, "demo", snapshot.value_kind if snapshot else "", snapshot.currency if snapshot else "", json.dumps(metric, ensure_ascii=False, cls=DjangoJSONEncoder)])
        response = HttpResponse("\ufeff" + output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="nama-demo-{kind}.csv"'
        return response
