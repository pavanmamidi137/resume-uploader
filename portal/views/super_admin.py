import io
import re
import zipfile

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User

from .. import storage as resume_storage
from ..csv_utils import parse_students_csv
from ..decorators import role_required
from ..forms import (
    BranchForm,
    SectionForm,
    SubAdminCreateForm,
    SuperAdminCsvUploadForm,
    SuperAdminStudentCreateForm,
)
from ..models import Branch, Resume, Section
from .shared import _back, safe_filename


def _student_queryset():
    return User.objects.filter(role=User.Role.STUDENT).select_related("section__branch")


@role_required("SUPER_ADMIN")
def super_admin_dashboard(request):
    student_total = User.objects.filter(role=User.Role.STUDENT).count()
    resume_total = Resume.objects.count()
    return render(
        request,
        "portal/superadmin/dashboard.html",
        {
            "branch_count": Branch.objects.count(),
            "section_count": Section.objects.count(),
            "cr_count": User.objects.filter(role=User.Role.SUB_ADMIN).count(),
            "student_count": student_total,
            "resume_count": resume_total,
            "pending_count": max(student_total - resume_total, 0),
        },
    )


# ---------------------------------------------------------------------------
# Branches
# ---------------------------------------------------------------------------
@role_required("SUPER_ADMIN")
def super_admin_branches(request):
    if request.method == "POST":
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Branch '{form.cleaned_data['name']}' added.")
            return redirect("portal:super_admin_branches")
    else:
        form = BranchForm()
    branches = Branch.objects.annotate(section_count=Count("sections")).order_by("name")
    return render(request, "portal/superadmin/branches.html", {"form": form, "branches": branches})


@role_required("SUPER_ADMIN")
def super_admin_branch_delete(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == "POST":
        if branch.sections.exists():
            messages.error(request, f"Cannot delete '{branch}' — delete its sections first.")
        else:
            branch.delete()
            messages.success(request, f"Branch '{branch}' deleted.")
    return redirect("portal:super_admin_branches")


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------
@role_required("SUPER_ADMIN")
def super_admin_sections(request):
    if request.method == "POST":
        form = SectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Section '{form.instance}' added.")
            return redirect("portal:super_admin_sections")
    else:
        form = SectionForm()
    sections = (
        Section.objects.select_related("branch")
        .annotate(member_count=Count("members"))
        .order_by("branch__name", "name")
    )
    return render(request, "portal/superadmin/sections.html", {"form": form, "sections": sections})


@role_required("SUPER_ADMIN")
def super_admin_section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)
    if request.method == "POST":
        members = section.members.count()
        if members:
            messages.error(
                request,
                f"Cannot delete '{section}' — {members} member(s) are still assigned.",
            )
        else:
            section.delete()
            messages.success(request, f"Section '{section}' deleted.")
    return redirect("portal:super_admin_sections")


# ---------------------------------------------------------------------------
# Sub admins (CRs)
# ---------------------------------------------------------------------------
@role_required("SUPER_ADMIN")
def super_admin_sub_admins(request):
    if request.method == "POST":
        form = SubAdminCreateForm(request.POST)
        if form.is_valid():
            roll = form.cleaned_data["roll_number"].strip().upper()
            name = form.cleaned_data["full_name"].strip()
            section = form.cleaned_data["section"]
            if User.objects.filter(username=roll).exists():
                messages.error(request, f"Username '{roll}' is already registered.")
            else:
                User.objects.create_user(
                    username=roll,
                    password=roll,
                    first_name=name,
                    role=User.Role.SUB_ADMIN,
                    section=section,
                    must_change_password=True,
                )
                messages.success(
                    request,
                    f"Sub admin (CR) '{roll}' created for {section} — initial password is the roll number.",
                )
            return redirect("portal:super_admin_sub_admins")
    else:
        form = SubAdminCreateForm()
    sub_admins = (
        User.objects.filter(role=User.Role.SUB_ADMIN)
        .select_related("section__branch")
        .order_by("username")
    )
    return render(
        request,
        "portal/superadmin/sub_admins.html",
        {"form": form, "sub_admins": sub_admins},
    )


@role_required("SUPER_ADMIN")
def reset_password(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        if target.is_super_admin:
            messages.error(request, "You cannot reset a super admin's password here.")
        else:
            target.set_password(target.username)
            target.must_change_password = True
            target.save(update_fields=["password", "must_change_password"])
            messages.success(
                request,
                f"Password of '{target.username}' reset to their roll number.",
            )
    return redirect(_back(request, "portal:super_admin_dashboard"))


@role_required("SUPER_ADMIN")
def delete_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        if target.is_super_admin:
            messages.error(request, "You cannot delete a super admin.")
        else:
            if hasattr(target, "resume"):
                resume_storage.delete_resume(target)
            target.delete()
            messages.success(request, f"User '{target.username}' deleted.")
    return redirect(_back(request, "portal:super_admin_dashboard"))


# ---------------------------------------------------------------------------
# Students & resumes (super admin overview)
# ---------------------------------------------------------------------------
def _create_student(roll, name, section):
    """Create a student user (caller must ensure the roll number is free)."""
    return User.objects.create_user(
        username=roll,
        password=roll,
        first_name=name,
        role=User.Role.STUDENT,
        section=section,
        must_change_password=True,
    )


@role_required("SUPER_ADMIN")
def super_admin_students(request):
    branch_id = request.GET.get("branch") or ""
    section_id = request.GET.get("section") or ""
    search = request.GET.get("q", "").strip()
    students = _student_queryset().annotate(has_resume=Count("resume")).order_by(
        "section__branch__name", "username"
    )
    if section_id:
        students = students.filter(section_id=section_id)
    elif branch_id:
        students = students.filter(section__branch_id=branch_id)
    if search:
        students = students.filter(
            Q(username__icontains=search) | Q(first_name__icontains=search)
        )
    selected_section = (
        Section.objects.filter(pk=section_id).select_related("branch").first()
        if section_id
        else None
    )
    return render(
        request,
        "portal/superadmin/students.html",
        {
            "branches": Branch.objects.all(),
            "sections": Section.objects.select_related("branch").all(),
            "students": students,
            "selected_branch": branch_id,
            "selected_section_id": section_id,
            "selected_section": selected_section,
            "search": search,
            "add_form": SuperAdminStudentCreateForm(),
            "csv_form": SuperAdminCsvUploadForm(),
        },
    )


@role_required("SUPER_ADMIN")
def super_admin_students_add(request):
    """Add a single student to a chosen section (super admin)."""
    if request.method == "POST":
        form = SuperAdminStudentCreateForm(request.POST)
        if form.is_valid():
            roll = form.cleaned_data["roll_number"].strip().upper()
            name = form.cleaned_data["full_name"].strip()
            section = form.cleaned_data["section"]
            if User.objects.filter(username=roll).exists():
                messages.error(request, f"Roll number '{roll}' is already registered.")
            else:
                _create_student(roll, name, section)
                messages.success(
                    request,
                    f"Student '{roll}' added to {section} — login with roll number {roll} / {roll}.",
                )
        else:
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, f"{field}: {error}")
    return redirect("portal:super_admin_students")


@role_required("SUPER_ADMIN")
def super_admin_students_csv(request):
    """Bulk import students into a chosen section (super admin). Skips any roll
    number that already exists (including CRs and students of other sections)."""
    if request.method == "POST":
        form = SuperAdminCsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            section = form.cleaned_data["section"]
            try:
                rows = parse_students_csv(request.FILES["csv_file"].read())
            except Exception:
                rows = []
            if not rows:
                messages.error(
                    request,
                    "No valid rows found. Expected columns: roll_number,name",
                )
                return redirect("portal:super_admin_students")

            created = skipped = invalid = 0
            existing = set(
                User.objects.filter(username__in=[r for r, _ in rows]).values_list(
                    "username", flat=True
                )
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
                    _create_student(roll, name, section)
                    created += 1
            messages.success(
                request,
                f"CSV import into {section}: {created} created, "
                f"{skipped} skipped (already registered/duplicates), {invalid} invalid row(s).",
            )
        else:
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, f"{field}: {error}")
    return redirect("portal:super_admin_students")


@role_required("SUPER_ADMIN")
def make_sub_admin(request, user_id):
    """Promote a student of a section to sub admin (CR) of that same section."""
    target = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        if not target.is_student_role:
            messages.error(request, f"'{target.username}' is not a student account.")
        elif not target.section_id:
            messages.error(request, f"'{target.username}' has no section assigned.")
        else:
            target.role = User.Role.SUB_ADMIN
            target.must_change_password = True
            target.save(update_fields=["role", "must_change_password"])
            messages.success(
                request,
                f"'{target.username}' is now a sub admin (CR) of {target.section_label} — "
                f"login is unchanged (roll number / roll number).",
            )
    return redirect(_back(request, "portal:super_admin_students"))


@role_required("SUPER_ADMIN")
def all_resumes_zip(request):
    """ZIP of every uploaded resume, organised in Branch/Section folders."""
    students = (
        _student_queryset()
        .prefetch_related("section__branch")
        .order_by("section__branch__name", "section__name", "username")
    )
    buffer = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for student in students:
            data = resume_storage.get_resume_bytes(student)
            if data is None:
                continue
            sec = student.section
            if sec:
                folder = f"{safe_filename(sec.branch.name)}/Sec_{safe_filename(sec.name)}"
            else:
                folder = "Unassigned"
            member = f"{folder}/{safe_filename(student.username)}_{safe_filename(student.first_name)}.pdf"
            archive.writestr(member, data)
            count += 1
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="all_resumes.zip"'
    if count:
        messages.success(request, f"ZIP created with {count} resume(s) from all sections.")
    else:
        messages.warning(request, "No resumes uploaded yet.")
    return response


@role_required("SUPER_ADMIN")
def super_admin_resumes(request):
    branch_id = request.GET.get("branch") or ""
    section_id = request.GET.get("section") or ""
    search = request.GET.get("q", "").strip()
    students = _student_queryset().annotate(has_resume=Count("resume")).order_by(
        "section__branch__name", "username"
    )
    if section_id:
        students = students.filter(section_id=section_id)
    elif branch_id:
        students = students.filter(section__branch_id=branch_id)
    if search:
        students = students.filter(
            Q(username__icontains=search) | Q(first_name__icontains=search)
        )
    selected_section = (
        Section.objects.filter(pk=section_id).select_related("branch").first()
        if section_id
        else None
    )
    return render(
        request,
        "portal/superadmin/resumes.html",
        {
            "branches": Branch.objects.all(),
            "sections": Section.objects.select_related("branch").all(),
            "students": students,
            "selected_branch": branch_id,
            "selected_section_id": section_id,
            "selected_section": selected_section,
            "search": search,
            "uploaded": students.filter(has_resume__gt=0).count(),
        },
    )
