from django.contrib import admin
from django.urls import include, path

from api.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),  # /api/docs — Swagger UI, /api/openapi.json — схема
    path("", include("web.urls")),
]
