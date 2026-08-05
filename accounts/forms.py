from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django import forms


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Roll number / username",
        help_text="Roll numbers are case-insensitive — type them in small or capital letters.",
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "e.g. 21CS1001",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        help_text="First-time password is your roll number in CAPITAL letters. After you change "
        "it, type it exactly as you set it.",
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-lg", "placeholder": "Your password"}
        ),
    )


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["new_password1"].help_text = (
            "Choose a strong password you can remember — you will use it "
            "every time you sign in."
        )
