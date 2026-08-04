from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Create (or reset) the initial super admin plus demo data: "
        "branch, section, CR and students. Safe to re-run any time - "
        "it resets demo passwords and the forced-password-change flag."
    )

    def handle(self, *args, **options):
        from portal.models import Branch, Section

        # --- Super admin -------------------------------------------------
        username = self._env("DJANGO_SUPERUSER_USERNAME", "admin")
        password = self._env("DJANGO_SUPERUSER_PASSWORD", "admin123")
        email = self._env("DJANGO_SUPERUSER_EMAIL", "admin@example.com")

        admin, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": User.Role.SUPER_ADMIN,
                "must_change_password": False,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Super admin created: {username} / {password}"))
        admin.set_password(password)
        admin.email = email
        admin.role = User.Role.SUPER_ADMIN
        admin.is_staff = True
        admin.is_superuser = True
        admin.must_change_password = False
        admin.save()
        if not created:
            self.stdout.write(f"Super admin '{username}' password reset.")

        # --- Demo branch / section --------------------------------------
        branch, _ = Branch.objects.get_or_create(
            name="Computer Science", defaults={"code": "CSE"}
        )
        section, _ = Section.objects.get_or_create(
            branch=branch, name="A", defaults={"year": "2026"}
        )

        # --- Demo CR -----------------------------------------------------
        cr, created = User.objects.get_or_create(
            username="CR01",
            defaults={
                "role": User.Role.SUB_ADMIN,
                "first_name": "Demo Class Rep",
                "section": section,
                "must_change_password": True,
            },
        )
        cr.role = User.Role.SUB_ADMIN
        cr.first_name = "Demo Class Rep"
        cr.section = section
        cr.must_change_password = True
        cr.set_password("CR01")
        cr.save()
        if created:
            self.stdout.write(self.style.SUCCESS("CR created: CR01 / CR01 (CSE Sec A)"))
        else:
            self.stdout.write("CR 'CR01' password reset to CR01.")

        # --- Demo students ----------------------------------------------
        demo_students = [
            ("21CS1001", "Arjun Kumar"),
            ("21CS1002", "Priya Sharma"),
        ]
        for roll, name in demo_students:
            student, created = User.objects.get_or_create(
                username=roll,
                defaults={
                    "role": User.Role.STUDENT,
                    "first_name": name,
                    "section": section,
                    "must_change_password": True,
                },
            )
            student.role = User.Role.STUDENT
            student.first_name = name
            student.section = section
            student.must_change_password = True
            student.set_password(roll)
            student.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f"Student created: {roll} / {roll}"))
            else:
                self.stdout.write(f"Student '{roll}' password reset to '{roll}'.")

        self.stdout.write(self.style.SUCCESS("Demo data ready."))

    @staticmethod
    def _env(key, default):
        import os

        return os.environ.get(key, default)
