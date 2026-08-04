from .cr import (  # noqa: F401
    cr_dashboard,
    cr_delete_user,
    cr_reset_password,
    cr_resumes,
    cr_students,
    cr_students_csv,
    csv_template,
)
from .shared import (  # noqa: F401
    home,
    resume_delete,
    resume_download,
    resume_view,
    section_resumes_zip,
)
from .student import student_dashboard  # noqa: F401
from .super_admin import (  # noqa: F401
    delete_user,
    make_sub_admin,
    reset_password,
    super_admin_branch_delete,
    super_admin_branches,
    super_admin_dashboard,
    super_admin_resumes,
    super_admin_section_delete,
    super_admin_sections,
    super_admin_students,
    super_admin_students_add,
    super_admin_students_csv,
    super_admin_sub_admins,
)
