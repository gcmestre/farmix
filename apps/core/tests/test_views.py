from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apps.core.models import Pharmacy, UserProfile


class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="test1234")
        self.pharmacy = Pharmacy.objects.create(name="Test Pharmacy", slug="test-pharmacy")
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.PHARMACIST, pharmacy=self.pharmacy)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_authenticated(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)


class ProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="profileuser", password="test1234", first_name="Test", last_name="User"
        )
        self.pharmacy = Pharmacy.objects.create(name="Test Pharmacy", slug="test-pharmacy")
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.VIEWER, pharmacy=self.pharmacy)
        self.client.login(username="profileuser", password="test1234")

    def test_profile_get(self):
        response = self.client.get(reverse("core:profile"))
        self.assertEqual(response.status_code, 200)

    def test_profile_update(self):
        response = self.client.post(
            reverse("core:profile"),
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "updated@test.com",
                "phone": "912345678",
                "professional_license": "",
                "preferred_language": "pt-pt",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")


class UserManagementViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username="admin_user", password="test1234")
        self.pharmacy = Pharmacy.objects.create(name="Test Pharmacy", slug="test-pharmacy")
        UserProfile.objects.create(user=self.admin, role=UserProfile.Role.ADMIN, pharmacy=self.pharmacy)
        self.client.login(username="admin_user", password="test1234")

    def test_user_list(self):
        response = self.client.get(reverse("core:user_list"))
        self.assertEqual(response.status_code, 200)

    def test_user_create(self):
        response = self.client.post(
            reverse("core:user_create"),
            {
                "first_name": "New",
                "last_name": "User",
                "email": "new@test.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
                "role": "viewer",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="new@test.com").exists())
        user = User.objects.get(email="new@test.com")
        self.assertEqual(user.username, "new@test.com")

    def test_user_list_denied_for_viewer(self):
        viewer = User.objects.create_user(username="viewer_user", password="test1234")
        UserProfile.objects.create(user=viewer, role=UserProfile.Role.VIEWER, pharmacy=self.pharmacy)
        self.client.login(username="viewer_user", password="test1234")
        response = self.client.get(reverse("core:user_list"))
        self.assertEqual(response.status_code, 403)

    def test_audit_log(self):
        response = self.client.get(reverse("core:audit_log"))
        self.assertEqual(response.status_code, 200)
