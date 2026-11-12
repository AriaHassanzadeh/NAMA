from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from market.models import Ad, Product, Shop
from .models import ProjectBrief, SavedAd, SavedProduct, SavedReport, SavedShop, ShopWatch, Workspace
from .serializers import ProjectBriefSerializer, SavedReportSerializer, ShopWatchInputSerializer, WorkspaceSerializer


def owned_workspace(request, workspace_id):
    return get_object_or_404(Workspace, pk=workspace_id, owner=request.user)


@method_decorator(never_cache, name="dispatch")
class WorkspaceListView(generics.ListCreateAPIView):
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        return Workspace.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@method_decorator(never_cache, name="dispatch")
class WorkspaceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkspaceSerializer
    lookup_url_kwarg = "workspace_id"
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Workspace.objects.filter(owner=self.request.user)


@method_decorator(never_cache, name="dispatch")
class ProjectBriefView(APIView):
    def get_brief(self, request, workspace_id):
        workspace = owned_workspace(request, workspace_id)
        return ProjectBrief.objects.get_or_create(workspace=workspace)[0]

    def get(self, request, workspace_id):
        return Response(ProjectBriefSerializer(self.get_brief(request, workspace_id)).data)

    def patch(self, request, workspace_id):
        serializer = ProjectBriefSerializer(self.get_brief(request, workspace_id), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@method_decorator(never_cache, name="dispatch")
class CompleteProjectBriefView(ProjectBriefView):
    http_method_names = ["post", "options"]

    def post(self, request, workspace_id):
        serializer = ProjectBriefSerializer(
            self.get_brief(request, workspace_id), data=request.data, partial=True, context={"complete": True},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(completed_at=timezone.now())
        return Response(serializer.data)


BOOKMARK_KINDS = {
    "ads": (SavedAd, Ad, "ad"),
    "products": (SavedProduct, Product, "product"),
    "shops": (SavedShop, Shop, "shop"),
}


def catalog_metadata(target):
    value = {
        "id": str(target.pk), "name": getattr(target, "name", getattr(target, "title", "")),
        "source_kind": target.source_kind,
    }
    if isinstance(target, Ad):
        value.update(title=target.title, product_id=str(target.product_id), shop_id=str(target.product.shop_id))
    elif isinstance(target, Product):
        value["shop_id"] = str(target.shop_id)
    elif isinstance(target, Shop):
        value["domain"] = target.domain
    return value


def bookmark_data(bookmark, field):
    target = getattr(bookmark, field)
    return {"id": str(bookmark.pk), "target_id": str(target.pk), "target": catalog_metadata(target), "created_at": bookmark.created_at}


@method_decorator(never_cache, name="dispatch")
class BookmarkBaseView(APIView):
    def configuration(self, kind):
        try:
            return BOOKMARK_KINDS[kind]
        except KeyError:
            raise NotFound() from None


class BookmarkListView(BookmarkBaseView):
    def get(self, request, workspace_id, kind):
        workspace = owned_workspace(request, workspace_id)
        model, _, field = self.configuration(kind)
        related = f"{field}__product" if field == "ad" else field
        records = model.objects.filter(workspace=workspace).select_related(related)
        return Response({"count": records.count(), "results": [bookmark_data(item, field) for item in records]})


class BookmarkDetailView(BookmarkBaseView):
    def put(self, request, workspace_id, kind, target_id):
        workspace = owned_workspace(request, workspace_id)
        model, target_model, field = self.configuration(kind)
        # Shared demo catalog records are the only catalog source exposed here.
        target = get_object_or_404(target_model, pk=target_id, source_kind="demo")
        record, created = model.objects.get_or_create(workspace=workspace, **{field: target})
        return Response(bookmark_data(record, field), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, workspace_id, kind, target_id):
        workspace = owned_workspace(request, workspace_id)
        model, _, field = self.configuration(kind)
        model.objects.filter(workspace=workspace, **{f"{field}_id": target_id}).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def watch_data(watch):
    return {
        "id": str(watch.pk), "shop_id": str(watch.shop_id), "shop": catalog_metadata(watch.shop),
        "enabled": watch.enabled, "created_at": watch.created_at, "updated_at": watch.updated_at,
    }


@method_decorator(never_cache, name="dispatch")
class ShopWatchListView(APIView):
    def get(self, request, workspace_id):
        workspace = owned_workspace(request, workspace_id)
        records = ShopWatch.objects.filter(workspace=workspace).select_related("shop")
        return Response({"count": records.count(), "results": [watch_data(item) for item in records]})


@method_decorator(never_cache, name="dispatch")
class ShopWatchView(APIView):
    def put(self, request, workspace_id, shop_id):
        workspace = owned_workspace(request, workspace_id)
        shop = get_object_or_404(Shop, pk=shop_id, source_kind="demo")
        serializer = ShopWatchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        watch, created = ShopWatch.objects.update_or_create(workspace=workspace, shop=shop, defaults=serializer.validated_data)
        return Response(watch_data(watch), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, workspace_id, shop_id):
        workspace = owned_workspace(request, workspace_id)
        ShopWatch.objects.filter(workspace=workspace, shop_id=shop_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(never_cache, name="dispatch")
class SavedReportListView(generics.ListCreateAPIView):
    serializer_class = SavedReportSerializer

    def get_queryset(self):
        return SavedReport.objects.filter(workspace=owned_workspace(self.request, self.kwargs["workspace_id"]))

    def perform_create(self, serializer):
        serializer.save(workspace=owned_workspace(self.request, self.kwargs["workspace_id"]))


@method_decorator(never_cache, name="dispatch")
class SavedReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavedReportSerializer
    lookup_url_kwarg = "report_id"
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return SavedReport.objects.filter(workspace=owned_workspace(self.request, self.kwargs["workspace_id"]))
