import io
import re
import zipfile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect

from accounts.models import User

from .. import storage as resume_storage
from ..models import Resume, Section


def safe_filename(value):
    return re.sub(r"[^\w\-. ]", "", str(value or "")).strip().replace(" ", "_")


def home(request):
    """Landing page: route the user to their role dashboard."""
    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login")
    if user.is_super_admin:
        return redirect("portal:super_admin_dashboard")
    if user.is_sub_admin:
        return redirect("portal:cr_dashboard")
    return redirect("portal:student_dashboard")


def _back(request, fallback):
    ref = request.META.get("HTTP_REFERER") or ""
    if ref.startswith("/") and not ref.startswith("//"):
        return ref
    return fallback


# ---------------------------------------------------------------------------
# Resume access rules
# ---------------------------------------------------------------------------
def can_view_resume(user, owner):
    """Everyone can see their own resume; CRs see their section; super admins see all."""
    if user.pk == owner.pk:
        return True
    if user.is_super_admin:
        return True
    if user.is_sub_admin and user.section_id and user.section_id == owner.section_id:
        return True
    if user.is_student_role and user.pk == owner.pk:
        return True
    return False


@login_required
def resume_view(request, user_id):
    owner = get_object_or_404(User, pk=user_id)
    if not can_view_resume(request.user, owner):
        raise PermissionDenied
    data = resume_storage.get_resume_bytes(owner)
    if data is None:
        raise Http404("No resume uploaded yet.")
    response = HttpResponse(data, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{safe_filename(owner.username)}.pdf"'
    return response


@login_required
def resume_download(request, user_id):
    owner = get_object_or_404(User, pk=user_id)
    if not can_view_resume(request.user, owner):
        raise PermissionDenied
    data = resume_storage.get_resume_bytes(owner)
    if data is None:
        raise Http404("No resume uploaded yet.")
    filename = f"{safe_filename(owner.username)}_{safe_filename(owner.first_name)}.pdf"
    response = HttpResponse(data, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def resume_delete(request, user_id):
    owner = get_object_or_404(User, pk=user_id)
    user = request.user
    # CRs are also students — they may delete (replace) their own resume too.
    allowed = user.is_super_admin or (
        user.pk == owner.pk and (user.is_student_role or user.is_sub_admin)
    )
    if not allowed:
        raise PermissionDenied
    if request.method == "POST":
        resume_storage.delete_resume(owner)
        Resume.objects.filter(user=owner).delete()
        messages.success(request, f"Resume of '{owner.username}' deleted.")
    return redirect(_back(request, "portal:home"))


@login_required
def section_resumes_zip(request, section_id):
    """ZIP download of all resumes in a section (super admin: any section, CR: own)."""
    section = get_object_or_404(Section, pk=section_id)
    user = request.user
    if not (user.is_super_admin or (user.is_sub_admin and user.section_id == section.id)):
        raise PermissionDenied

    # CRs are also students (special ones) — include their resumes in the ZIP.
    students = User.objects.filter(
        role__in=[User.Role.STUDENT, User.Role.SUB_ADMIN], section=section
    ).order_by("username")
    buffer = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for student in students:
            data = resume_storage.get_resume_bytes(student)
            if data is None:
                continue
            member = f"{safe_filename(student.username)}_{safe_filename(student.first_name)}.pdf"
            archive.writestr(member, data)
            count += 1

    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type="application/zip")
    zip_name = f"resumes_{safe_filename(section.branch.name)}_{safe_filename(section.name)}.zip"
    response["Content-Disposition"] = f'attachment; filename="{zip_name}"'
    if count:
        messages.success(request, f"ZIP created with {count} resume(s) from {section}.")
    else:
        messages.warning(request, "No resumes uploaded for this section yet.")
    return response
