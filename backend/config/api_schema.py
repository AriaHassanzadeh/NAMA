"""Explicit contracts for the small session/workspace APIViews."""
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers

from accounts import api as auth
from demo.views import EntryOptionsView
from health.views import HealthView
from workspaces import views as workspace
from workspaces.serializers import ProjectBriefSerializer, ShopWatchInputSerializer


class CSRFTokenSerializer(serializers.Serializer):
    csrfToken = serializers.CharField()


class UserIdentitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    email = serializers.CharField(allow_blank=True)


class AuthDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class VerificationPendingSerializer(AuthDetailSerializer):
    delivery_mode = serializers.ChoiceField(choices=["local", "smtp"])


class SessionIdentitySerializer(serializers.Serializer):
    user = UserIdentitySerializer()


class SessionLoginResponseSerializer(SessionIdentitySerializer):
    csrfToken = serializers.CharField()


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.CharField()


class IdeaExampleSerializer(serializers.Serializer):
    id = serializers.CharField()
    text = serializers.CharField()
    icon = serializers.CharField()


class EntryOptionsResponseSerializer(serializers.Serializer):
    source_kind = serializers.CharField()
    label = serializers.CharField()
    idea_examples = IdeaExampleSerializer(many=True)


class BookmarkTargetSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    source_kind = serializers.CharField()
    title = serializers.CharField(required=False)
    domain = serializers.CharField(required=False)
    product_id = serializers.UUIDField(required=False)
    shop_id = serializers.UUIDField(required=False)


class BookmarkRecordSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    target_id = serializers.UUIDField()
    target = BookmarkTargetSerializer()
    created_at = serializers.DateTimeField()


class BookmarkListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    results = BookmarkRecordSerializer(many=True)


class ShopWatchRecordSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    shop_id = serializers.UUIDField()
    shop = BookmarkTargetSerializer()
    enabled = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class ShopWatchListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    results = ShopWatchRecordSerializer(many=True)


def document_csrf_header(result, generator, request, public):
    """Make required unsafe-request CSRF headers usable in Swagger/typed clients."""
    for operations in result["paths"].values():
        for method, operation in operations.items():
            if method not in {"post", "put", "patch", "delete"}:
                continue
            operation.setdefault("parameters", []).append({
                "name": "X-CSRFToken", "in": "header", "required": True,
                "schema": {"type": "string"},
                "description": "Use csrfToken from /auth/csrf/ with its cookie; login rotates it and returns the next token.",
            })
    return result


def configure_api_schema():
    auth.CSRFView.serializer_class = CSRFTokenSerializer
    auth.LoginView.serializer_class = auth.LoginSerializer
    auth.MeView.serializer_class = SessionIdentitySerializer
    auth.LogoutView.serializer_class = SessionIdentitySerializer
    extend_schema_view(post=extend_schema(request=auth.LoginSerializer, responses={200: SessionLoginResponseSerializer}, description="Fetch /auth/csrf/ first and send X-CSRFToken. Django rotates the session/CSRF token on login."))(auth.LoginView)
    extend_schema_view(post=extend_schema(request=None, responses={204: None}))(auth.LogoutView)
    auth.SignupView.serializer_class = auth.SignupSerializer
    auth.VerificationResendView.serializer_class = auth.VerificationResendSerializer
    auth.VerificationConfirmView.serializer_class = auth.VerificationConfirmSerializer
    extend_schema_view(post=extend_schema(request=auth.SignupSerializer, responses={202: VerificationPendingSerializer}, description="Email/password signup. Verification is required for new accounts; response does not disclose whether the address already exists."))(auth.SignupView)
    extend_schema_view(post=extend_schema(request=auth.VerificationResendSerializer, responses={202: VerificationPendingSerializer}, description="Generic response; a 60-second cooldown prevents repeated delivery. A newer email invalidates the older verification link."))(auth.VerificationResendView)
    extend_schema_view(post=extend_schema(request=auth.VerificationConfirmSerializer, responses={200: AuthDetailSerializer, 400: AuthDetailSerializer}, description="Explicit POST activates an unverified signup. Single-use token expires after 24 hours. Verification does not log the user in."))(auth.VerificationConfirmView)
    EntryOptionsView.serializer_class = EntryOptionsResponseSerializer
    HealthView.serializer_class = HealthResponseSerializer
    extend_schema_view(get=extend_schema(responses={200: HealthResponseSerializer, 503: HealthResponseSerializer}))(HealthView)
    workspace.ProjectBriefView.serializer_class = ProjectBriefSerializer
    workspace.CompleteProjectBriefView.serializer_class = ProjectBriefSerializer
    extend_schema_view(post=extend_schema(request=ProjectBriefSerializer, responses=ProjectBriefSerializer))(workspace.CompleteProjectBriefView)
    workspace.BookmarkListView.serializer_class = BookmarkListSerializer
    workspace.BookmarkDetailView.serializer_class = BookmarkRecordSerializer
    kind = OpenApiParameter("kind", str, OpenApiParameter.PATH, enum=["ads", "products", "shops"])
    extend_schema_view(get=extend_schema(parameters=[kind], responses=BookmarkListSerializer))(workspace.BookmarkListView)
    extend_schema_view(put=extend_schema(parameters=[kind], request=None, responses={200: BookmarkRecordSerializer, 201: BookmarkRecordSerializer}), delete=extend_schema(parameters=[kind], request=None, responses={204: None}))(workspace.BookmarkDetailView)
    workspace.ShopWatchListView.serializer_class = ShopWatchListSerializer
    workspace.ShopWatchView.serializer_class = ShopWatchInputSerializer
    extend_schema_view(put=extend_schema(request=ShopWatchInputSerializer, responses={200: ShopWatchRecordSerializer, 201: ShopWatchRecordSerializer}), delete=extend_schema(request=None, responses={204: None}))(workspace.ShopWatchView)
