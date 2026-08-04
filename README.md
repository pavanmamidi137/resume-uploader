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
