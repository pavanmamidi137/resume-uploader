# Resume Uploader

A Django + Bootstrap 5 resume management portal for colleges, backed by Supabase (Postgres + Storage).

## Roles

| Role | What they can do |
|------|------------------|
| **Super Admin** | Manage branches, class sections and CRs; add students (manual/CSV); promote students to CR; reset passwords; view/download all resumes (PDF or ZIP per section) |
| **Sub Admin (CR)** | Add students of their section (manual/CSV); view/download resumes of their section; reset student passwords; upload their own resume |
| **Student** | Upload/view/replace/delete their own resume — cannot see anyone else's |

## Tech stack

- Python 3.12, Django 6
- Bootstrap 5 (mobile-responsive drawer layout)
- Supabase Postgres (`DATABASE_URL`) + Supabase Storage (optional, falls back to local disk)
- Resume uploads limited to **1 MB** PDFs

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env (copy from .env.example and fill in your Supabase credentials)
cp .env.example .env

# 3. Migrate and seed demo data
python manage.py migrate
python manage.py seed_demo

# 4. Run
python manage.py runserver
```

Open http://127.0.0.1:8000

## Demo logins (after seed_demo)

| Role | Username | Password |
|------|----------|----------|
| Super Admin | `admin` | `admin123` |
| Sub Admin (CR) | `CR01` | `CR01` |
| Student | `21CS1001` | `21CS1001` |
| Student | `21CS1002` | `21CS1002` |

Students and CRs sign in with their roll number (roll number = username = initial password). Changing the password after login is optional.

## CSV upload format

```
roll_number,name
21CS1001,Student Name
21CS1002,Another Student
```

Roll numbers that already exist (students, CRs or admins) are automatically skipped — no duplicates.

## Deploy on Render

> ⚠️ **The most common failure**: the Start Command must reference the Django
> project package **`resume_portal`** (underscore) — NOT the repo name
> `resume-uploader` (hyphen). Gunicorn imports modules by Python name, and
> hyphens are invalid in module names:
>
> ```
> ModuleNotFoundError: No module named 'resume-uploader'
> ```

### Option A — Render Dashboard (recommended)

1. New → **Web Service** → connect the `resume-uploader` repo.
2. Set the **Build Command**:
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput
   ```
3. Set the **Start Command**:
   ```bash
   gunicorn resume_portal.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```
4. Add the environment variables below.

### Option B — Blueprint (`render.yaml`)

A `render.yaml` Blueprint with these commands is included in the repo.

### Environment variables (set on Render)

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | long random string (generate one, don't reuse the local one) |
| `DEBUG` | `0` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` (the `.onrender.com` hostname is added automatically) |
| `DATABASE_URL` | your Supabase Postgres connection string |
| `SUPABASE_URL` | `https://<project-ref>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | the **real** service-role key from Supabase → Project Settings → API |
| `SUPABASE_STORAGE_BUCKET` | `resumes` |

### Auto-deploy with GitHub Actions

A workflow (`.github/workflows/deploy.yml`) deploys to Render **on every push to `main`**:

1. **Django system check** runs first (`python manage.py check`) — if the code is
   broken, the deploy is blocked.
2. If it passes, GitHub POSTs to your **Render Deploy Hook**.

**One-time setup:**

1. Render dashboard → your service → **Settings → Deploy Hook → Create Hook**.
   Copy the URL (looks like `https://api.render.com/deploy/srv-xxxx?key=yyyy`).
2. GitHub repo → **Settings → Secrets and variables → Actions** → new secret
   named exactly `RENDER_DEPLOY_HOOK_URL` with that URL as the value.

> The hook URL is a secret capability (no auth required) — never commit it.
> The workflow has `workflow_dispatch`, so you can also trigger a deploy
> manually from the **Actions** tab.

Because deploys are hook-triggered, `render.yaml` sets `autoDeploy: false` to
avoid Render's native git-watch deploying in parallel.

### Production notes

- **Static files** are served by WhiteNoise (no CDN needed) — `collectstatic` runs in the build step.
- **Migrations** run automatically in the build step (or run them manually from the Render Shell).
- **Supabase Storage** is used only when `SUPABASE_SERVICE_ROLE_KEY` is a real key — with the placeholder it falls back to local disk (not persistent on Render). Create the `resumes` bucket in Supabase Storage if you haven't.
- HTTPS is enforced automatically when `DEBUG=0`; `CSRF_TRUSTED_ORIGINS` is populated from `RENDER_EXTERNAL_HOSTNAME`.
