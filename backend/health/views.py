from django.db import DatabaseError, connection
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


@method_decorator(never_cache, name="dispatch")
class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                if cursor.fetchone() != (1,):
                    raise DatabaseError("Unexpected readiness result")
        except DatabaseError:
            # Never expose connection details or exception text.
            return Response({"status": "unavailable", "database": "unavailable"}, status=503)
        return Response({"status": "ok", "database": "ok"})
