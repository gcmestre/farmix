from django.contrib.auth.models import User
from django.test import TestCase

from apps.core.models import AuditLog, Consent, Pharmacy, UserProfile
from apps.core.services import RGPDService


class RGPDServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="rgpd_user", password="test1234", first_name="Maria", last_name="Silva"
        )
        self.pharmacy = Pharmacy.objects.create(name="Test Pharmacy", slug="test-pharmacy")
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.VIEWER, pharmacy=self.pharmacy)

    def test_export_data(self):
        data = RGPDService.export_data(self.user)
        self.assertEqual(data["user"]["username"], "rgpd_user")
        self.assertIn("exported_at", data)
        # Check audit log was created
        self.assertTrue(AuditLog.objects.filter(action="export", model_name="User").exists())

    def test_manage_consent_grant(self):
        consent = RGPDService.manage_consent(
            user=self.user,
            purpose=Consent.Purpose.DATA_PROCESSING,
            legal_basis=Consent.LegalBasis.CONSENT,
            grant=True,
        )
        self.assertTrue(consent.is_active)

    def test_manage_consent_revoke(self):
        RGPDService.manage_consent(
            user=self.user,
            purpose=Consent.Purpose.MARKETING,
            legal_basis=Consent.LegalBasis.CONSENT,
            grant=True,
        )
        consent = RGPDService.manage_consent(
            user=self.user,
            purpose=Consent.Purpose.MARKETING,
            legal_basis=Consent.LegalBasis.CONSENT,
            grant=False,
        )
        self.assertFalse(consent.is_active)
