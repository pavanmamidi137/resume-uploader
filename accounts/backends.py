from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveUsernameBackend(ModelBackend):
    """Authenticate users with case-insensitive usernames (roll numbers).

    Roll numbers are stored in CAPITAL letters (e.g. 21CS1001) and the default
    password is the roll number itself. This backend lets students/CRs type
    their roll number in small, capital or mixed letters — the username lookup
    is case-insensitive — while the password check stays exactly case-sensitive,
    so a user who changes their password to small or mixed-case letters still
    signs in with the password exactly as they set it.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        username = str(username).strip()
        try:
            user = UserModel._default_manager.get(
                **{f"{UserModel.USERNAME_FIELD}__iexact": username}
            )
        except (UserModel.DoesNotExist, UserModel.MultipleObjectsReturned):
            # Run a hash anyway so response time doesn't reveal whether a
            # username exists (same mitigation as Django's default backend).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
