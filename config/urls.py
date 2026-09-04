"""Корневая маршрутизация проекта."""
from django.contrib import admin
from django.urls import include, path

from web.api import api as web_api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", web_api.urls),
    path("", include("web.urls")),
]
