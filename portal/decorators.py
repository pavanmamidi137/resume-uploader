from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Require login and one of the given roles (super admins always pass).

    Changing the password is optional and never blocks access to the portal.
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            if user.is_super_admin or user.role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied

        return wrapper

    return decorator
