from django.contrib import admin

from web.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "owner", "core_version", "created_at", "finished_at")
    list_filter = ("status",)
    search_fields = ("name",)
    readonly_fields = ("result", "error", "core_version", "created_at", "finished_at")
