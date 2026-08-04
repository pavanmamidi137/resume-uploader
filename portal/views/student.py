from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render

from .. import storage as resume_storage
from ..decorators import role_required
from ..forms import ResumeUploadForm
from ..models import Resume

PDF_MAGIC = b"%PDF"


@role_required("STUDENT", "SUB_ADMIN")
def student_dashboard(request):
    user = request.user
    has_resume = hasattr(user, "resume")

    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = request.FILES["file"]
            head = uploaded.read(5)
            uploaded.seek(0)
            is_pdf = uploaded.name.lower().endswith(".pdf") and head.startswith(PDF_MAGIC)
            max_bytes = settings.MAX_RESUME_SIZE_MB * 1024 * 1024
            if not is_pdf:
                messages.error(request, "Only PDF files are allowed.")
            elif uploaded.size > max_bytes:
                messages.error(
                    request,
                    f"File is too large (maximum {settings.MAX_RESUME_SIZE_MB} MB).",
                )
            else:
                resume_storage.save_resume(user, uploaded)
                Resume.objects.update_or_create(
                    user=user,
                    defaults={"original_filename": uploaded.name, "size": uploaded.size},
                )
                messages.success(request, "Your resume was uploaded successfully.")
            return redirect("portal:student_dashboard")
    else:
        form = ResumeUploadForm()

    return render(
        request,
        "portal/student/dashboard.html",
        {
            "form": form,
            "has_resume": has_resume,
            "resume": getattr(user, "resume", None),
            "max_size_mb": settings.MAX_RESUME_SIZE_MB,
        },
    )
