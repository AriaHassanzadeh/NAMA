import hashlib
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models.functions import Lower, Trim
from django.middleware.csrf import get_token
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from .models import User
from .verification import confirm_verification, send_verification

PENDING_DETAIL = "If this address can receive a verification email, instructions will be sent."
INVALID_LINK_DETAIL = "This verification link is invalid or has expired. Request a new email."


def pending_response():
    delivery_mode = "local" if settings.EMAIL_BACKEND == "django.core.mail.backends.filebased.EmailBackend" else "smtp"
    return Response({"detail": PENDING_DETAIL, "delivery_mode": delivery_mode}, status=status.HTTP_202_ACCEPTED)


def user_data(user):
    return {"id": user.pk, "username": user.get_username(), "email": user.email, "display_name": user.get_full_name() or user.email or user.get_username()}


def users_with_email(email):
    # Match the migrated uniqueness rule without rewriting preserved legacy rows.
    return User.objects.annotate(normalized_email=Lower(Trim("email"))).filter(normalized_email=email.strip().lower())


class AuthGlobalThrottle(SimpleRateThrottle):
    scope = "auth_global"
    rate = "300/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": "all"}


class LoginThrottle(SimpleRateThrottle):
    scope = "session_login"
    rate = "10/min"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.META.get("REMOTE_ADDR", "local")}


class IdentityThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        data = request.data if isinstance(request.data, dict) else {}
        identity = str(data.get("email") or data.get("username") or "").strip().lower()
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": digest}


class LoginIdentityThrottle(IdentityThrottle):
    scope = "login_identity"
    rate = "10/min"


class VerificationEmailThrottle(IdentityThrottle):
    scope = "verification_email"
    rate = "5/hour"


class VerificationIPThrottle(LoginThrottle):
    scope = "verification_ip"
    rate = "20/hour"


class ConfirmIPThrottle(LoginThrottle):
    scope = "verification_confirm_ip"
    rate = "30/hour"


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254, required=False)
    username = serializers.CharField(max_length=150, required=False)
    password = serializers.CharField(max_length=1024, trim_whitespace=False, write_only=True)

    def validate(self, attrs):
        if bool(attrs.get("email")) == bool(attrs.get("username")):
            raise serializers.ValidationError("Provide an email address or a username, together with your password.")
        return attrs


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)
    display_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        candidate = User(username=attrs["email"], email=attrs["email"], first_name=attrs.get("display_name", ""))
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": error.messages}) from error
        return attrs


class VerificationResendSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class VerificationConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200, trim_whitespace=False, write_only=True)


@method_decorator(never_cache, name="dispatch")
@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AuthGlobalThrottle, LoginThrottle, LoginIdentityThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "email" in data:
            candidate = users_with_email(data["email"]).first()
            if candidate is None:
                # Match Django's unknown-user password work without treating an
                # email as a legacy username that happens to contain an @ sign.
                make_password(data["password"])
                user = None
            else:
                user = authenticate(request=request._request, username=candidate.username, password=data["password"])
        else:
            user = authenticate(request=request._request, username=data["username"], password=data["password"])
        if user is None or (user.email_verification_required and user.email_verified_at is None):
            return Response({"detail": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)
        login(request._request, user)
        return Response({"user": user_data(user), "csrfToken": get_token(request)})


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class SignupView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer
    throttle_classes = [AuthGlobalThrottle, VerificationIPThrottle, VerificationEmailThrottle]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        password = make_password(data["password"])
        # Existing accounts receive the same response and are never changed or
        # sent another message by repeated signup requests.
        if not users_with_email(data["email"]).exists():
            try:
                with transaction.atomic():
                    user = User.objects.create(
                        username="u_" + uuid.uuid4().hex, email=data["email"],
                        first_name=data.get("display_name", ""), password=password,
                        is_active=False, email_verification_required=True,
                    )
            except IntegrityError:
                # A concurrent signup may have won the unique-email race.
                pass
            else:
                send_verification(user.pk)
        return pending_response()


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class VerificationResendView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = VerificationResendSerializer
    throttle_classes = [AuthGlobalThrottle, VerificationIPThrottle, VerificationEmailThrottle]

    def post(self, request):
        serializer = VerificationResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = users_with_email(serializer.validated_data["email"]).first()
        if user is not None:
            send_verification(user.pk)
        return pending_response()


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class VerificationConfirmView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = VerificationConfirmSerializer
    throttle_classes = [AuthGlobalThrottle, ConfirmIPThrottle]

    def post(self, request):
        serializer = VerificationConfirmSerializer(data=request.data)
        if not serializer.is_valid() or not confirm_verification(serializer.validated_data["token"]):
            return Response({"detail": INVALID_LINK_DETAIL}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Email verified. You can now sign in."})


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    def post(self, request):
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(never_cache, name="dispatch")
class MeView(APIView):
    def get(self, request):
        return Response({"user": user_data(request.user)})


urlpatterns = [
    path("csrf/", CSRFView.as_view(), name="auth-csrf"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("signup/", SignupView.as_view(), name="auth-signup"),
    path("verification/resend/", VerificationResendView.as_view(), name="auth-verification-resend"),
    path("verification/confirm/", VerificationConfirmView.as_view(), name="auth-verification-confirm"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
]
