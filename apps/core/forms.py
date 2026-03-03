from datetime import timedelta

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .models import Invitation, Pharmacy, UserProfile


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(label=_("First name"), max_length=150)
    last_name = forms.CharField(label=_("Last name"), max_length=150)
    email = forms.EmailField(label=_("Email"))

    class Meta:
        model = UserProfile
        fields = ["phone", "professional_license", "preferred_language"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        user = profile.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return profile


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(label=_("Email"), required=True)
    role = forms.ChoiceField(label=_("Role"), choices=UserProfile.Role.choices)
    phone = forms.CharField(label=_("Phone"), max_length=20, required=False)
    professional_license = forms.CharField(label=_("Professional license"), max_length=50, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._pharmacy = pharmacy

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def save(self, commit=True):
        self.instance.username = self.cleaned_data["email"]
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role": self.cleaned_data["role"],
                    "phone": self.cleaned_data.get("phone", ""),
                    "professional_license": self.cleaned_data.get("professional_license", ""),
                    "pharmacy": self._pharmacy,
                },
            )
        return user


class UserEditForm(forms.ModelForm):
    email = forms.EmailField(label=_("Email"), required=True)
    role = forms.ChoiceField(label=_("Role"), choices=UserProfile.Role.choices)
    phone = forms.CharField(label=_("Phone"), max_length=20, required=False)
    professional_license = forms.CharField(label=_("Professional license"), max_length=50, required=False)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "is_active")

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._pharmacy = pharmacy
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.userprofile
                self.fields["role"].initial = profile.role
                self.fields["phone"].initial = profile.phone
                self.fields["professional_license"].initial = profile.professional_license
            except UserProfile.DoesNotExist:
                pass

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def save(self, commit=True):
        self.instance.username = self.cleaned_data["email"]
        user = super().save(commit=commit)
        if commit:
            defaults = {
                "role": self.cleaned_data["role"],
                "phone": self.cleaned_data.get("phone", ""),
                "professional_license": self.cleaned_data.get("professional_license", ""),
            }
            if self._pharmacy:
                defaults["pharmacy"] = self._pharmacy
            UserProfile.objects.update_or_create(
                user=user,
                defaults=defaults,
            )
        return user


class PharmacyRegistrationForm(UserCreationForm):
    """Self-registration: creates a new Pharmacy + admin User."""

    pharmacy_name = forms.CharField(label=_("Pharmacy name"), max_length=255)
    pharmacy_email = forms.EmailField(label=_("Pharmacy email"))
    pharmacy_nif = forms.CharField(label=_("NIF"), max_length=20, required=False)
    first_name = forms.CharField(label=_("First name"), max_length=150)
    last_name = forms.CharField(label=_("Last name"), max_length=150)
    email = forms.EmailField(label=_("Email"))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def _generate_unique_slug(self, name):
        base_slug = slugify(name)[:90]
        slug = base_slug
        counter = 1
        while Pharmacy.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    @transaction.atomic
    def save(self, commit=True):
        self.instance.username = self.cleaned_data["email"]
        user = super().save(commit=commit)
        if commit:
            pharmacy = Pharmacy.objects.create(
                name=self.cleaned_data["pharmacy_name"],
                slug=self._generate_unique_slug(self.cleaned_data["pharmacy_name"]),
                email=self.cleaned_data["pharmacy_email"],
                nif=self.cleaned_data.get("pharmacy_nif", ""),
            )
            UserProfile.objects.create(
                user=user,
                pharmacy=pharmacy,
                role=UserProfile.Role.ADMIN,
            )
        return user


class InvitationForm(forms.ModelForm):
    """Admin form to invite a user to the pharmacy."""

    class Meta:
        model = Invitation
        fields = ["email", "role"]

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._pharmacy = pharmacy

    def clean_email(self):
        email = self.cleaned_data["email"]
        if self._pharmacy:
            if UserProfile.objects.filter(pharmacy=self._pharmacy, user__email__iexact=email).exists():
                raise forms.ValidationError(_("A user with this email already belongs to this pharmacy."))
            if Invitation.objects.filter(
                pharmacy=self._pharmacy, email__iexact=email, accepted_at__isnull=True
            ).exists():
                raise forms.ValidationError(_("An invitation for this email is already pending."))
        return email

    def save(self, commit=True):
        invitation = super().save(commit=False)
        invitation.pharmacy = self._pharmacy
        invitation.expires_at = timezone.now() + timedelta(days=7)
        if commit:
            invitation.save()
        return invitation


class InvitedUserRegistrationForm(UserCreationForm):
    """Registration form for users arriving via an invitation link."""

    first_name = forms.CharField(label=_("First name"), max_length=150)
    last_name = forms.CharField(label=_("Last name"), max_length=150)
    email = forms.EmailField(label=_("Email"), disabled=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, invitation=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._invitation = invitation
        if invitation:
            self.fields["email"].initial = invitation.email

    def clean_email(self):
        return self._invitation.email

    @transaction.atomic
    def save(self, commit=True):
        self.instance.username = self._invitation.email
        self.instance.email = self._invitation.email
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.create(
                user=user,
                pharmacy=self._invitation.pharmacy,
                role=self._invitation.role,
            )
            self._invitation.accepted_at = timezone.now()
            self._invitation.save(update_fields=["accepted_at", "updated_at"])
        return user
