from django.contrib.auth import authenticate, login, logout
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


def user_data(user):
    return {"id": user.pk, "username": user.get_username(), "display_name": user.get_full_name() or user.get_username()}


class LoginThrottle(SimpleRateThrottle):
    scope = "session_login"
    rate = "10/min"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.META.get("REMOTE_ADDR", "local")}


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=1024, trim_whitespace=False, write_only=True)


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
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request=request._request, **serializer.validated_data)
        if user is None:
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST)
        login(request._request, user)
        return Response({"user": user_data(user), "csrfToken": get_token(request)})


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
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
]
