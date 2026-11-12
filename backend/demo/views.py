from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


@method_decorator(never_cache, name="dispatch")
class EntryOptionsView(APIView):
    """Fictional starter ideas; this endpoint performs no market research."""

    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        return Response({
            "source_kind": "demo",
            "label": "داده‌های نمایشی؛ بدون اتصال به بازار واقعی",
            "idea_examples": [
                {
                    "id": "minimal-womenswear",
                    "text": "پوشاک مینیمال زنانه",
                    "icon": "shirt",
                },
                {
                    "id": "sportswear-shop",
                    "text": "فروشگاه لباس ورزشی",
                    "icon": "bolt",
                },
                {
                    "id": "casualwear-brand",
                    "text": "برند پوشاک روزمره",
                    "icon": "shirt",
                },
            ],
        })
