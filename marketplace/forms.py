# marketplace/forms.py
from django import forms
from django.forms import formset_factory
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.forms import SetPasswordForm


class StyledPasswordResetForm(PasswordResetForm):
    email=forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
        "class":"w-full border border-black border-2 rounded-md px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500",
        "placeholder":"Email",
    }))

class StyledSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full mb-4 p-3 border rounded-lg focus:ring focus:ring-purple-300",
                "placeholder": "Enter new password",
                "value":"",
            }
        )
    )
    new_password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full p-3 border rounded-lg focus:ring focus:ring-purple-300",
                "placeholder": "Confirm new password",
            }
        )
    )

class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "w-full border border-black border-2 rounded-md px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500",
            "placeholder": "Username",
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "w-full border border-black border-2 rounded-md px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500",
            "placeholder": "Password",
        })
    )

class StyledUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2","email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply Tailwind classes to each field
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                "class": "w-full border border-black border-2 rounded-md px-3 py-2 focus:outline-none",
                "placeholder": field.label  # optional: adds placeholder
            })
            field.label_suffix = ""  # remove ":" after label

PRODUCT_TYPE_CHOICES = [
    ("project", "Project Source Code"),
    ("apk", "Modified APK"),
    ("template", "Template"),
    ("plugin", "Plugin/Extension"),
]

class ProductForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "w-full border border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 5,
            "class": "w-full border border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
        })
    )
    category = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "w-full border border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-lg p-2"
        })
    )
    license = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "w-full border border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-lg p-2"
        })
    )
    license_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            "class": "w-full border border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-lg p-2"
        })
    )
    product_type = forms.ChoiceField(
        choices=PRODUCT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            "class": "w-full border border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-lg p-2"
        })
    )
    version = forms.CharField(
        max_length=50,
        initial="1.0.0",
        widget=forms.TextInput(attrs={
            "class": "w-full border border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-lg p-2"
        })
    )
    price = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False, initial=0,
        widget=forms.NumberInput(attrs={
            "class": "w-full border border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-lg p-2"
        })
    )
    is_free = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={
            "class": "h-4 w-4 text-blue-600 border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded"
        })
    )
    tags = forms.CharField(
        help_text="Comma-separated tags", required=False,
        widget=forms.TextInput(attrs={
            "class": "w-full border border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-lg p-2"
        })
    )
    thumbnail = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            "class": "w-full border border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-lg p-2"
        })
    )


class ProductFileForm(forms.Form):
    FILE_TYPE_CHOICES = [
        ("main", "Main File"),
        ("demo", "Demo File"),
        ("documentation", "Documentation"),
        ("screenshot", "Screenshot"),
    ]
    file_type = forms.ChoiceField(
        choices=FILE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            "class": "w-full border border-gray-300 rounded-lg p-2"
        })
    )
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            "class": "w-full border border-gray-300 rounded-lg p-2 mb-2"
        })
    )

ProductFileFormSet = formset_factory(ProductFileForm, extra=1, can_delete=True)

from django import forms

class DeveloperProfileForm(forms.Form):
    company_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control w-full px-2 py-2 border border-dark rounded-lg",
            "placeholder": "Enter your company name"
        })
    )

    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 4,
            "class": "form-control w-full px-2 py-2 border border-dark rounded-lg",
            "placeholder": "Write a short bio"
        })
    )

    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            "class": "form-control w-full px-2 py-2 border border-dark rounded-lg",
            "placeholder": "https://yourwebsite.com"
        })
    )

    avatar = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control w-100 px-2 py-2"
        })
    )

class ReviewForm(forms.Form):
    rating = forms.ChoiceField(choices=[(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)])
    comment = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

class ModerationForm(forms.Form):
    ACTION_CHOICES = [
        ("approved", "Approve"),
        ("rejected", "Reject"),
        ("suspended", "Suspend"),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect)
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, help_text="Optional reason")
