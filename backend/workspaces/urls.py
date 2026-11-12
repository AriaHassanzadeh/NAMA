from django.urls import path

from .views import (
    BookmarkDetailView, BookmarkListView, CompleteProjectBriefView, ProjectBriefView, SavedReportDetailView,
    SavedReportListView, ShopWatchListView, ShopWatchView, WorkspaceDetailView, WorkspaceListView,
)

urlpatterns = [
    path("workspaces/", WorkspaceListView.as_view(), name="workspace-list"),
    path("workspaces/<uuid:workspace_id>/", WorkspaceDetailView.as_view(), name="workspace-detail"),
    path("workspaces/<uuid:workspace_id>/brief/", ProjectBriefView.as_view(), name="project-brief"),
    path("workspaces/<uuid:workspace_id>/brief/complete/", CompleteProjectBriefView.as_view(), name="project-brief-complete"),
    path("workspaces/<uuid:workspace_id>/saved/<str:kind>/", BookmarkListView.as_view(), name="bookmark-list"),
    path("workspaces/<uuid:workspace_id>/saved/<str:kind>/<uuid:target_id>/", BookmarkDetailView.as_view(), name="bookmark-detail"),
    path("workspaces/<uuid:workspace_id>/watches/", ShopWatchListView.as_view(), name="shop-watch-list"),
    path("workspaces/<uuid:workspace_id>/shops/<uuid:shop_id>/watch/", ShopWatchView.as_view(), name="shop-watch"),
    path("workspaces/<uuid:workspace_id>/reports/", SavedReportListView.as_view(), name="saved-report-list"),
    path("workspaces/<uuid:workspace_id>/reports/<uuid:report_id>/", SavedReportDetailView.as_view(), name="saved-report-detail"),
]
