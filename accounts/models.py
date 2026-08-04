from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with a role and an optional class section.

    Roles:
        SUPER_ADMIN — full control (branches, sections, CRs, everything)
        SUB_ADMIN   — class CR, manages the students of their section
        STUDENT     — regular student, can manage their own resume only
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        SUB_ADMIN = "SUB_ADMIN", "Sub Admin (CR)"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    section = models.ForeignKey(
        "portal.Section",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    must_change_password = models.BooleanField(
        default=True,
        help_text="Soft flag: suggests the user change their password (never blocks portal access).",
    )

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.SUPER_ADMIN
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    @property
    def is_super_admin(self):
        return self.is_superuser or self.role == self.Role.SUPER_ADMIN

    @property
    def is_sub_admin(self):
        return self.role == self.Role.SUB_ADMIN

    @property
    def is_student_role(self):
        return self.role == self.Role.STUDENT

    @property
    def role_label(self):
        return self.Role(self.role).label

    @property
    def section_label(self):
        if not self.section_id:
            return "—"
        return str(self.section)

    @property
    def initials(self):
        name = (self.first_name or self.username).strip()
        words = [w for w in name.split() if w]
        if not words:
            return "?"
        if len(words) == 1:
            return words[0][:2].upper()
        return (words[0][0] + words[-1][0]).upper()

    def __str__(self):
        return self.username
