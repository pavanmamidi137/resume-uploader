from django.contrib import admin

from .models import Branch, Resume, Section


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_at")
    search_fields = ("name", "code")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("branch", "name", "year", "student_count")
    list_filter = ("branch",)
    search_fields = ("branch__name", "name")


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("user", "original_filename", "size", "uploaded_at")
    search_fields = ("user__username", "original_filename")
