# jdgen/urls.py
from django.urls import path
from .views import GenerateJDAPIView

urlpatterns = [
    path("jdgen/", GenerateJDAPIView.as_view(), name="generate-jd"),
]
