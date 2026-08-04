from django import forms

from .models import Branch, Section

TEXT = {"class": "form-control"}
SELECT = {"class": "form-select"}
FILE = {"class": "form-control", "accept": "application/pdf,.pdf"}


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ["name", "code"]
        widgets = {
            "name": forms.TextInput(
                attrs={**TEXT, "placeholder": "e.g. Computer Science"}
            ),
            "code": forms.TextInput(attrs={**TEXT, "placeholder": "e.g. CSE"}),
        }


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ["branch", "name", "year"]
        widgets = {
            "branch": forms.Select(attrs={**SELECT}),
            "name": forms.TextInput(attrs={**TEXT, "placeholder": "e.g. A"}),
            "year": forms.TextInput(attrs={**TEXT, "placeholder": "e.g. 2026"}),
        }


class SubAdminCreateForm(forms.Form):
    """Create a CR (sub admin) from a roll number."""

    roll_number = forms.CharField(
        label="CR roll number",
        max_length=50,
        widget=forms.TextInput(attrs={**TEXT, "placeholder": "e.g. 21CS001"}),
    )
    full_name = forms.CharField(
        label="Full name",
        max_length=150,
        widget=forms.TextInput(attrs={**TEXT, "placeholder": "e.g. Student Name"}),
    )
    section = forms.ModelChoiceField(
        label="Branch / Section",
        queryset=Section.objects.select_related("branch").all(),
        widget=forms.Select(attrs={**SELECT}),
    )


class StudentCreateForm(forms.Form):
    """Add a single student (used by CRs)."""

    roll_number = forms.CharField(
        label="Roll number",
        max_length=50,
        widget=forms.TextInput(attrs={**TEXT, "placeholder": "e.g. 21CS1001"}),
    )
    full_name = forms.CharField(
        label="Full name",
        max_length=150,
        widget=forms.TextInput(attrs={**TEXT, "placeholder": "e.g. Student Name"}),
    )


class SuperAdminStudentCreateForm(forms.Form):
    """Add a single student to a chosen section (used by super admin)."""

    roll_number = forms.CharField(
        label="Roll number",
        max_length=50,
        widget=forms.TextInput(attrs={**TEXT, "placeholder": "e.g. 21CS1001"}),
    )
    full_name = forms.CharField(
        label="Full name",
        max_length=150,
        widget=forms.TextInput(attrs={**TEXT, "placeholder": "e.g. Student Name"}),
    )
    section = forms.ModelChoiceField(
        label="Branch / Section",
        queryset=Section.objects.select_related("branch").all(),
        widget=forms.Select(attrs={**SELECT}),
    )


class CsvUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV file",
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": ".csv,text/csv"}
        ),
    )


class SuperAdminCsvUploadForm(forms.Form):
    """Bulk import into a chosen section (used by super admin)."""

    csv_file = forms.FileField(
        label="CSV file",
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": ".csv,text/csv"}
        ),
    )
    section = forms.ModelChoiceField(
        label="Import into section",
        queryset=Section.objects.select_related("branch").all(),
        widget=forms.Select(attrs={**SELECT}),
    )


class ResumeUploadForm(forms.Form):
    file = forms.FileField(
        label="Resume (PDF only)",
        widget=forms.ClearableFileInput(attrs={**FILE}),
    )
