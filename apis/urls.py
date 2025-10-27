# jdgen/urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path("jdgen/", GenerateJDAPIView.as_view(), name="generate-jd"),
]
from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="JD Generation API",
        default_version="v1",
        description="API for generating professional Job Descriptions using DeepQuery inference engine.",
        terms_of_service="https://www.termsofservicegenerator.net/live.php?token=GnBU6OpZr7nuXZZH7Sc8Oh5ksAw0ipqX",
        contact=openapi.Contact(email="support@presear.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path('usage/', TotalUsageView.as_view(), name='total-usage'),
]
