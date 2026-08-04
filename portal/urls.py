from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.home, name="home"),
    # Shared resume endpoints (permission checked inside the views)
    path("resume/<int:user_id>/view/", views.resume_view, name="resume_view"),
    path("resume/<int:user_id>/download/", views.resume_download, name="resume_download"),
    path("resume/<int:user_id>/delete/", views.resume_delete, name="resume_delete"),
    path("sections/<int:section_id>/zip/", views.section_resumes_zip, name="section_resumes_zip"),
    # ------------------------------------------------------------------
    # Super admin
    # ------------------------------------------------------------------
    path("superadmin/", views.super_admin_dashboard, name="super_admin_dashboard"),
    path("superadmin/branches/", views.super_admin_branches, name="super_admin_branches"),
    path("superadmin/branches/<int:pk>/delete/", views.super_admin_branch_delete, name="super_admin_branch_delete"),
    path("superadmin/sections/", views.super_admin_sections, name="super_admin_sections"),
    path("superadmin/sections/<int:pk>/delete/", views.super_admin_section_delete, name="super_admin_section_delete"),
    path("superadmin/sub-admins/", views.super_admin_sub_admins, name="super_admin_sub_admins"),
    path("superadmin/users/<int:user_id>/reset-password/", views.reset_password, name="super_admin_reset_password"),
    path("superadmin/users/<int:user_id>/delete/", views.delete_user, name="super_admin_delete_user"),
    path("superadmin/students/", views.super_admin_students, name="super_admin_students"),
    path("superadmin/students/add/", views.super_admin_students_add, name="super_admin_students_add"),
    path("superadmin/students/csv/", views.super_admin_students_csv, name="super_admin_students_csv"),
    path("superadmin/students/<int:user_id>/make-cr/", views.make_sub_admin, name="super_admin_make_cr"),
    path("superadmin/resumes/", views.super_admin_resumes, name="super_admin_resumes"),
    path("superadmin/resumes/all-zip/", views.all_resumes_zip, name="super_admin_all_resumes_zip"),
    # ------------------------------------------------------------------
    # CR (sub admin)
    # ------------------------------------------------------------------
    path("cr/", views.cr_dashboard, name="cr_dashboard"),
    path("cr/students/", views.cr_students, name="cr_students"),
    path("cr/students/csv/", views.cr_students_csv, name="cr_students_csv"),
    path("cr/students/template/", views.csv_template, name="csv_template"),
    path("cr/users/<int:user_id>/reset-password/", views.cr_reset_password, name="cr_reset_password"),
    path("cr/users/<int:user_id>/delete/", views.cr_delete_user, name="cr_delete_user"),
    path("cr/resumes/", views.cr_resumes, name="cr_resumes"),
    # ------------------------------------------------------------------
    # Student
    # ------------------------------------------------------------------
    path("student/", views.student_dashboard, name="student_dashboard"),
]
