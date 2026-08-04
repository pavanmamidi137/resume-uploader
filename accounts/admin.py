from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "first_name", "role", "section", "must_change_password", "is_active")
    list_filter = ("role", "is_active", "section")
    search_fields = ("username", "first_name")
    fieldsets = UserAdmin.fieldsets + (
        ("Portal role", {"fields": ("role", "section", "must_change_password")}),
    )
