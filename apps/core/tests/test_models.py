from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.translation import override as lang_override

from apps.core.models import AuditLog, Consent, Pharmacy, UserProfile


class UserProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="test1234")
        self.pharmacy = Pharmacy.objects.create(name="Test Pharmacy", slug="test-pharmacy")
        self.profile = UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.PHARMACIST,
            pharmacy=self.pharmacy,
        )

    def test_str(self):
        self.user.first_name = "Test"
        self.user.last_name = "User"
        self.user.save()
        with lang_override("en"):
            self.assertIn("Pharmacist", str(self.profile))

    def test_role_properties(self):
        self.assertTrue(self.profile.is_pharmacist)
        self.assertFalse(self.profile.is_admin)
        self.assertTrue(self.profile.can_manage_orders)
        self.assertTrue(self.profile.can_manage_production)
        self.assertTrue(self.profile.can_manage_invoicing)

    def test_admin_role(self):
        self.profile.role = UserProfile.Role.ADMIN
        self.profile.save()
        self.assertTrue(self.profile.is_admin)

    def test_lab_tech_permissions(self):
        self.profile.role = UserProfile.Role.LAB_TECHNICIAN
        self.profile.save()
        self.assertTrue(self.profile.can_manage_production)
        self.assertFalse(self.profile.can_manage_orders)
        self.assertFalse(self.profile.can_manage_invoicing)


class AuditLogTest(TestCase):
    def test_create_log(self):
        user = User.objects.create_user(username="auditor", password="test1234")
        pharmacy = Pharmacy.objects.create(name="Audit Pharmacy", slug="audit-pharmacy")
        log = AuditLog.objects.create(
            user=user,
            pharmacy=pharmacy,
            action=AuditLog.Action.CREATE,
            model_name="TestModel",
            object_id="123",
            changes={"field": "value"},
        )
        self.assertEqual(log.action, "create")
        self.assertEqual(log.model_name, "TestModel")

    def test_log_is_immutable_in_meta(self):
        self.assertEqual(AuditLog._meta.default_permissions, ("add", "view"))


class ConsentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="consent_user", password="test1234")
        self.pharmacy = Pharmacy.objects.create(name="Consent Pharmacy", slug="consent-pharmacy")
        self.consent = Consent.objects.create(
            user=self.user,
            pharmacy=self.pharmacy,
            purpose=Consent.Purpose.DATA_PROCESSING,
            legal_basis=Consent.LegalBasis.CONSENT,
        )

    def test_grant_consent(self):
        self.consent.grant()
        self.consent.refresh_from_db()
        self.assertTrue(self.consent.is_active)
        self.assertIsNotNone(self.consent.granted_at)

    def test_revoke_consent(self):
        self.consent.grant()
        self.consent.revoke()
        self.consent.refresh_from_db()
        self.assertFalse(self.consent.is_active)
        self.assertIsNotNone(self.consent.revoked_at)
