"""Resume file storage.

When a real Supabase service-role key is configured in the .env file, resumes
are stored in the Supabase Storage bucket. Otherwise they are stored on the
local server under MEDIA_ROOT/resumes/... — so the app works out of the box.
"""
import os
import re

import requests
from django.conf import settings


def supabase_enabled():
    return getattr(settings, "SUPABASE_STORAGE_ENABLED", False)


def _bucket():
    return settings.SUPABASE_STORAGE_BUCKET


def _safe(part):
    cleaned = re.sub(r"[^\w.\- ]", "", str(part or "")).strip()
    return cleaned.replace(" ", "_") or "unknown"


def rel_path(user):
    """Storage path of a user's resume, e.g. CSE/Sec_A/21CS1001.pdf"""
    sec = user.section
    branch = sec.branch if sec else None
    return (
        f"{_safe(branch.name if branch else 'unknown')}/"
        f"{_safe(sec.name if sec else 'unknown')}/"
        f"{_safe(user.username)}.pdf"
    )


def _local_path(user):
    return os.path.join(settings.MEDIA_ROOT, "resumes", rel_path(user))


def _headers():
    return {"Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"}


def _storage_url(user):
    return f"{settings.SUPABASE_URL}/storage/v1/object/{_bucket()}/{rel_path(user)}"


def save_resume(user, file):
    """Persist the uploaded file and return its bytes."""
    data = file.read()
    if supabase_enabled():
        resp = requests.post(
            _storage_url(user),
            headers={**_headers(), "x-upsert": "true", "Content-Type": "application/pdf"},
            data=data,
            timeout=60,
        )
        resp.raise_for_status()
    else:
        path = _local_path(user)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
    return data


def get_resume_bytes(user):
    """Return resume bytes or None when no file exists."""
    if supabase_enabled():
        resp = requests.get(_storage_url(user), headers=_headers(), timeout=60)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.content
    path = _local_path(user)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def delete_resume(user):
    """Best-effort removal of a user's stored resume."""
    if supabase_enabled():
        try:
            requests.delete(_storage_url(user), headers=_headers(), timeout=30)
        except requests.RequestException:
            pass
    else:
        path = _local_path(user)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
