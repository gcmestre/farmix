from django.contrib.auth.models import User
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Pharmacy, UserProfile
from apps.orders.models import Client, Order


class OrderViewTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Order View Pharmacy", slug="orders-views-order")
        self.test_client = TestClient()
        self.user = User.objects.create_user(username="pharmacist", password="test1234")
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.PHARMACIST, pharmacy=self.pharmacy)
        self.test_client.login(username="pharmacist", password="test1234")
        self.client_obj = Client.objects.create(name="Farmacia Teste", nif="111222333", pharmacy=self.pharmacy)

    def test_order_list(self):
        response = self.test_client.get(reverse("orders:order_list"))
        self.assertEqual(response.status_code, 200)

    def test_order_create(self):
        response = self.test_client.post(
            reverse("orders:order_create"),
            {"client": str(self.client_obj.pk), "source": "in_person", "priority": "normal"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)

    def test_order_detail(self):
        order = Order.objects.create(client=self.client_obj, pharmacy=self.pharmacy)
        response = self.test_client.get(reverse("orders:order_detail", kwargs={"pk": order.pk}))
        self.assertEqual(response.status_code, 200)


class ClientViewTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Client View Pharmacy", slug="orders-views-client")
        self.test_client = TestClient()
        self.user = User.objects.create_user(username="frontdesk", password="test1234")
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.FRONT_DESK, pharmacy=self.pharmacy)
        self.test_client.login(username="frontdesk", password="test1234")

    def test_client_list(self):
        response = self.test_client.get(reverse("orders:client_list"))
        self.assertEqual(response.status_code, 200)

    def test_client_create(self):
        response = self.test_client.post(
            reverse("orders:client_create"),
            {
                "client_type": "pharmacy",
                "name": "Nova Farmacia",
                "nif": "987654321",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Client.objects.filter(nif="987654321").exists())
