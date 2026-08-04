from django.conf import settings
from django.db import models


class Branch(models.Model):
    """A department / branch, e.g. Computer Science."""

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.code or self.name


class Section(models.Model):
    """A class section within a branch, e.g. CSE - Sec A."""

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=50, help_text="Section letter, e.g. A")
    year = models.CharField(max_length=20, blank=True, default="", help_text="Optional, e.g. 2026")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["branch__name", "name", "year"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "name", "year"],
                name="uniq_branch_section_year",
            )
        ]

    def __str__(self):
        label = f"{self.branch} – Sec {self.name}"
        if self.year:
            label += f" ({self.year})"
        return label

    @property
    def display_name(self):
        return str(self)

    @property
    def student_count(self):
        return self.members.filter(role="STUDENT").count()


class Resume(models.Model):
    """One resume per student, uploaded to Supabase Storage (or local disk)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resume",
    )
    original_filename = models.CharField(max_length=255)
    size = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"Resume of {self.user.username}"

    @property
    def size_label(self):
        if self.size >= 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        return f"{self.size / 1024:.0f} KB"
