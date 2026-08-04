from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LoginForm, StyledPasswordChangeForm


def role_home(user):
    """URL name of the dashboard for a given user."""
    if user.is_super_admin:
        return "portal:super_admin_dashboard"
    if user.is_sub_admin:
        return "portal:cr_dashboard"
    return "portal:student_dashboard"


def login_view(request):
    if request.user.is_authenticated:
        return redirect(role_home(request.user))

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            if user.must_change_password and not user.is_super_admin:
                # Optional: changing the password is suggested but not enforced.
                messages.info(
                    request,
                    f"Welcome back, {user.first_name or user.username}! You are using a temporary "
                    "password - you can change it anytime from the 'Change password' option "
                    "in the sidebar.",
                )
            else:
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(role_home(user))
    else:
        form = LoginForm(request)

    return render(request, "accounts/login.html", {"form": form})


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = StyledPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            if user.must_change_password:
                user.must_change_password = False
                user.save(update_fields=["must_change_password"])
            messages.success(request, "Password changed successfully.")
            return redirect(role_home(user))
    else:
        form = StyledPasswordChangeForm(request.user)

    return render(request, "accounts/change_password.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("accounts:login")
