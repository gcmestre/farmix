import hashlib

from django.utils import timezone

from .models import AuditLog, Consent


class RGPDService:
    """Service for RGPD compliance: anonymization, data export, consent management."""

    ANONYMIZED_PLACEHOLDER = "[ANONYMIZED]"

    @classmethod
    def anonymize_data(cls, instance, user=None):
        """Anonymize PII fields marked in the model's RGPDMeta class."""
        rgpd_meta = getattr(instance, "RGPDMeta", None)
        if not rgpd_meta:
            return

        anonymizable_fields = getattr(rgpd_meta, "anonymizable_fields", [])
        changes = {}

        for field_name in anonymizable_fields:
            old_value = getattr(instance, field_name, None)
            if old_value and old_value != cls.ANONYMIZED_PLACEHOLDER:
                hashed = hashlib.sha256(str(old_value).encode()).hexdigest()[:12]
                setattr(instance, field_name, f"{cls.ANONYMIZED_PLACEHOLDER}-{hashed}")
                changes[field_name] = {"old": str(old_value), "new": cls.ANONYMIZED_PLACEHOLDER}

        if changes:
            instance.save()
            AuditLog.objects.create(
                user=user,
                action=AuditLog.Action.ANONYMIZE,
                model_name=instance.__class__.__name__,
                object_id=str(instance.pk),
                changes=changes,
            )

    @classmethod
    def export_data(cls, user, requesting_user=None):
        """Export all data related to a user for RGPD data portability (JSON)."""
        data = {
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_joined": user.date_joined.isoformat(),
            },
            "exported_at": timezone.now().isoformat(),
        }

        # Profile
        try:
            profile = user.userprofile
            data["profile"] = {
                "role": profile.role,
                "phone": profile.phone,
                "professional_license": profile.professional_license,
                "preferred_language": profile.preferred_language,
            }
        except Exception:
            pass

        # Consents
        data["consents"] = list(
            user.consents.values("purpose", "legal_basis", "granted_at", "revoked_at", "description")
        )

        AuditLog.objects.create(
            user=requesting_user or user,
            action=AuditLog.Action.EXPORT,
            model_name="User",
            object_id=str(user.pk),
            changes={"export_type": "full_data_export"},
        )

        return data

    @classmethod
    def manage_consent(cls, user, purpose, legal_basis, grant=True, description=""):
        """Grant or revoke consent for a specific purpose."""
        consent, created = Consent.objects.get_or_create(
            user=user,
            purpose=purpose,
            defaults={
                "legal_basis": legal_basis,
                "description": description,
            },
        )

        if grant:
            consent.grant()
        else:
            consent.revoke()

        return consent
