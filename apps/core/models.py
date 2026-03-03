import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class SoftDeleteManager(models.Manager):
    """Manager that filters out soft-deleted objects by default."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Manager that includes soft-deleted objects."""

    pass


class BaseModel(models.Model):
    """Abstract base model with UUID PK, timestamps, and soft delete."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        verbose_name=_("created by"),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
        verbose_name=_("updated by"),
    )
    is_deleted = models.BooleanField(_("deleted"), default=False, db_index=True)
    deleted_at = models.DateTimeField(_("deleted at"), null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self, user=None):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.updated_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "updated_by", "updated_at"])

    def restore(self, user=None):
        self.is_deleted = False
        self.deleted_at = None
        if user:
            self.updated_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "updated_by", "updated_at"])


class Pharmacy(BaseModel):
    """Pharmacy tenant — each pharmacy is an isolated tenant."""

    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)
    anf_number = models.CharField(_("ANF number"), max_length=50, blank=True)
    nif = models.CharField(_("NIF"), max_length=20, blank=True)
    address = models.TextField(_("address"), blank=True)
    phone = models.CharField(_("phone"), max_length=20, blank=True)
    email = models.EmailField(_("email"), blank=True)
    technical_director = models.CharField(_("technical director"), max_length=255, blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    # DPO — RGPD Data Protection Officer
    dpo_name = models.CharField(_("DPO name"), max_length=255, blank=True)
    dpo_email = models.EmailField(_("DPO email"), blank=True)
    dpo_phone = models.CharField(_("DPO phone"), max_length=20, blank=True)

    class Meta:
        verbose_name = _("pharmacy")
        verbose_name_plural = _("pharmacies")
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Extended user profile with role and professional info."""

    class Role(models.TextChoices):
        ADMIN = "admin", _("Administrator")
        PHARMACIST = "pharmacist", _("Pharmacist")
        LAB_TECHNICIAN = "lab_technician", _("Lab Technician")
        FRONT_DESK = "front_desk", _("Front Desk")
        VIEWER = "viewer", _("Viewer")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="userprofile",
    )
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
        verbose_name=_("pharmacy"),
    )
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
    )
    phone = models.CharField(_("phone"), max_length=20, blank=True)
    professional_license = models.CharField(
        _("professional license"),
        max_length=50,
        blank=True,
        help_text=_("Infarmed professional license number"),
    )
    license_verified = models.BooleanField(_("license verified"), default=False)
    license_expiry_date = models.DateField(_("license expiry date"), null=True, blank=True)
    preferred_language = models.CharField(
        _("preferred language"),
        max_length=5,
        choices=settings.LANGUAGES,
        default="pt-pt",
    )

    class Meta:
        verbose_name = _("user profile")
        verbose_name_plural = _("user profiles")

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_pharmacist(self):
        return self.role == self.Role.PHARMACIST

    @property
    def is_lab_technician(self):
        return self.role == self.Role.LAB_TECHNICIAN

    @property
    def can_manage_orders(self):
        return self.role in (self.Role.ADMIN, self.Role.PHARMACIST, self.Role.FRONT_DESK)

    @property
    def can_manage_production(self):
        return self.role in (self.Role.ADMIN, self.Role.PHARMACIST, self.Role.LAB_TECHNICIAN)

    @property
    def can_manage_invoicing(self):
        return self.role in (self.Role.ADMIN, self.Role.PHARMACIST)


class Invitation(BaseModel):
    """Invitation to join a pharmacy."""

    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name=_("pharmacy"),
    )
    email = models.EmailField(_("email"))
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=UserProfile.Role.choices,
        default=UserProfile.Role.VIEWER,
    )
    token = models.UUIDField(_("token"), default=uuid.uuid4, unique=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
        verbose_name=_("invited by"),
    )
    accepted_at = models.DateTimeField(_("accepted at"), null=True, blank=True)
    expires_at = models.DateTimeField(_("expires at"))

    class Meta:
        verbose_name = _("invitation")
        verbose_name_plural = _("invitations")
        unique_together = [("pharmacy", "email")]

    def __str__(self):
        return f"{self.email} -> {self.pharmacy.name}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_accepted(self):
        return self.accepted_at is not None

    @property
    def is_pending(self):
        return not self.is_accepted and not self.is_expired

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)


class Address(models.Model):
    """Generic address model attachable to any entity."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    street = models.CharField(_("street"), max_length=255)
    street_extra = models.CharField(_("street (line 2)"), max_length=255, blank=True)
    postal_code = models.CharField(_("postal code"), max_length=10)
    city = models.CharField(_("city"), max_length=100)
    district = models.CharField(_("district"), max_length=100, blank=True)
    country = models.CharField(_("country"), max_length=2, default="PT")

    class Meta:
        verbose_name = _("address")
        verbose_name_plural = _("addresses")

    def __str__(self):
        return f"{self.street}, {self.postal_code} {self.city}"


class AuditLog(models.Model):
    """Immutable audit log entry — RGPD compliance."""

    class Action(models.TextChoices):
        CREATE = "create", _("Create")
        UPDATE = "update", _("Update")
        DELETE = "delete", _("Delete")
        VIEW = "view", _("View")
        EXPORT = "export", _("Export")
        ANONYMIZE = "anonymize", _("Anonymize")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name=_("pharmacy"),
    )
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(_("action"), max_length=20, choices=Action.choices)
    model_name = models.CharField(_("model"), max_length=100, db_index=True)
    object_id = models.CharField(_("object ID"), max_length=255, blank=True)
    changes = models.JSONField(_("changes"), default=dict, blank=True)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)

    class Meta:
        verbose_name = _("audit log")
        verbose_name_plural = _("audit logs")
        ordering = ["-timestamp"]
        # Immutable: no update/delete permissions
        default_permissions = ("add", "view")

    def __str__(self):
        return f"{self.timestamp} | {self.action} | {self.model_name} | {self.user}"


class Consent(BaseModel):
    """RGPD consent tracking."""

    class Purpose(models.TextChoices):
        DATA_PROCESSING = "data_processing", _("Data Processing")
        MARKETING = "marketing", _("Marketing")
        THIRD_PARTY = "third_party", _("Third Party Sharing")
        RESEARCH = "research", _("Research")

    class LegalBasis(models.TextChoices):
        CONSENT = "consent", _("Consent")
        CONTRACT = "contract", _("Contract Performance")
        LEGAL_OBLIGATION = "legal_obligation", _("Legal Obligation")
        LEGITIMATE_INTEREST = "legitimate_interest", _("Legitimate Interest")

    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="consents",
        verbose_name=_("pharmacy"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consents",
    )
    purpose = models.CharField(_("purpose"), max_length=30, choices=Purpose.choices)
    legal_basis = models.CharField(_("legal basis"), max_length=30, choices=LegalBasis.choices)
    granted_at = models.DateTimeField(_("granted at"), null=True, blank=True)
    revoked_at = models.DateTimeField(_("revoked at"), null=True, blank=True)
    description = models.TextField(_("description"), blank=True)

    class Meta:
        verbose_name = _("consent")
        verbose_name_plural = _("consents")

    def __str__(self):
        status = "granted" if self.is_active else "revoked"
        return f"{self.user} - {self.get_purpose_display()} ({status})"

    @property
    def is_active(self):
        return self.granted_at is not None and self.revoked_at is None

    def grant(self):
        self.granted_at = timezone.now()
        self.revoked_at = None
        self.save(update_fields=["granted_at", "revoked_at", "updated_at"])

    def revoke(self):
        self.revoked_at = timezone.now()
        self.save(update_fields=["revoked_at", "updated_at"])
