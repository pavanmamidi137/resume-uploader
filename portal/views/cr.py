import re

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User

from .. import storage as resume_storage
from ..csv_utils import parse_students_csv
from ..decorators import role_required
from ..forms import CsvUploadForm, StudentCreateForm
from ..models import Resume
from .shared import _back


def _cr_students(user):
    return User.objects.filter(role=User.Role.STUDENT, section=user.section)


@role_required("SUB_ADMIN")
def cr_dashboard(request):
    user = request.user
    if not user.section_id:
        messages.error(request, "Your account is not linked to any section. Contact the super admin.")
    students = _cr_students(user)
    resume_count = Resume.objects.filter(user__section=user.section).count() if user.section_id else 0
    return render(
        request,
        "portal/cr/dashboard.html",
        {
            "section": user.section,
            "student_count": students.count(),
            "resume_count": resume_count,
            "pending_count": max(students.count() - resume_count, 0),
        },
    )


@role_required("SUB_ADMIN")
def cr_students(request):
    user = request.user
    section = user.section
    if not section:
        messages.error(request, "Your account is not linked to a section. Contact the super admin.")
        return redirect("portal:cr_dashboard")

    if request.method == "POST":
        form = StudentCreateForm(request.POST)
        if form.is_valid():
            roll = form.cleaned_data["roll_number"].strip().upper()
            name = form.cleaned_data["full_name"].strip()
            if User.objects.filter(username=roll).exists():
                messages.error(request, f"Roll number '{roll}' is already registered.")
            else:
                User.objects.create_user(
                    username=roll,
                    password=roll,
                    first_name=name,
                    role=User.Role.STUDENT,
                    section=section,
                    must_change_password=True,
                )
                messages.success(
                    request,
                    f"Student '{roll}' added — login with roll number {roll} / {roll}.",
                )
            return redirect("portal:cr_students")
    else:
        form = StudentCreateForm()

    search = request.GET.get("q", "").strip()
    students = (
        _cr_students(user)
        .annotate(has_resume=Count("resume"))
        .order_by("username")
    )
    if search:
        students = students.filter(
            Q(username__icontains=search) | Q(first_name__icontains=search)
        )
    return render(
        request,
        "portal/cr/students.html",
        {
            "form": form,
            "csv_form": CsvUploadForm(),
            "students": students,
            "section": section,
            "search": search,
        },
    )


@role_required("SUB_ADMIN")
def cr_students_csv(request):
    user = request.user
    if not user.section_id:
        messages.error(request, "Your account is not linked to a section.")
        return redirect("portal:cr_dashboard")

    if request.method == "POST" and request.FILES.get("csv_file"):
        try:
            rows = parse_students_csv(request.FILES["csv_file"].read())
        except Exception:
            rows = []
        if not rows:
            messages.error(
                request,
                "No valid rows found. Expected columns: roll_number,name",
            )
            return redirect("portal:cr_students")

        created = skipped = invalid = 0
        existing = set(
            User.objects.filter(username__in=[r for r, _ in rows]).values_list("username", flat=True)
        )
        seen = set()
        with transaction.atomic():
            for roll, name in rows:
                if not re.fullmatch(r"[\w.\-@]+", roll):
                    invalid += 1
                    continue
                if roll in seen:
                    skipped += 1
                    continue
                seen.add(roll)
                if roll in existing:
                    skipped += 1
                    continue
                User.objects.create_user(
                    username=roll,
                    password=roll,
                    first_name=name,
                    role=User.Role.STUDENT,
                    section=user.section,
                    must_change_password=True,
                )
                created += 1
        messages.success(
            request,
            f"CSV import complete: {created} created, "
            f"{skipped} skipped (already registered/duplicates), {invalid} invalid row(s).",
        )
    return redirect("portal:cr_students")


@role_required("SUB_ADMIN")
def csv_template(request):
    content = "roll_number,name\r\n21CS1001,Student Name\r\n21CS1002,Another Student\r\n"
    response = HttpResponse(content, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="students_upload_template.csv"'
    return response


@role_required("SUB_ADMIN")
def cr_resumes(request):
    user = request.user
    search = request.GET.get("q", "").strip()
    students = (
        _cr_students(user)
        .select_related("section__branch")
        .annotate(has_resume=Count("resume"))
        .order_by("username")
    )
    if search:
        students = students.filter(
            Q(username__icontains=search) | Q(first_name__icontains=search)
        )
    return render(
        request,
        "portal/cr/resumes.html",
        {"students": students, "section": user.section, "search": search},
    )


@role_required("SUB_ADMIN")
def cr_reset_password(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if not (request.user.section_id and target.section_id == request.user.section_id):
        raise PermissionDenied
    if request.method == "POST":
        target.set_password(target.username)
        target.must_change_password = True
        target.save(update_fields=["password", "must_change_password"])
        messages.success(request, f"Password of '{target.username}' reset to their roll number.")
    return redirect(_back(request, "portal:cr_students"))


@role_required("SUB_ADMIN")
def cr_delete_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if not (request.user.section_id and target.section_id == request.user.section_id):
        raise PermissionDenied
    if request.method == "POST":
        if hasattr(target, "resume"):
            resume_storage.delete_resume(target)
        target.delete()
        messages.success(request, f"Student '{target.username}' removed.")
    return redirect(_back(request, "portal:cr_students"))
