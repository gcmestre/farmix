from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Pharmacy, UserProfile
from apps.invoicing.models import Invoice, Quote, QuoteLine
from apps.orders.models import Client, Order


class QuoteViewTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(
            name="Test Pharmacy",
            slug="inv-views-quote",
        )
        self.test_client = TestClient()
        self.user = User.objects.create_user(
            username="pharmacist",
            password="test1234",
        )
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.PHARMACIST,
            pharmacy=self.pharmacy,
        )
        self.test_client.login(username="pharmacist", password="test1234")
        self.client_obj = Client.objects.create(
            name="Test",
            nif="111222333",
            pharmacy=self.pharmacy,
        )
        self.order = Order.objects.create(
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )

    def test_quote_list(self):
        response = self.test_client.get(reverse("invoicing:quote_list"))
        self.assertEqual(response.status_code, 200)

    def test_quote_create(self):
        response = self.test_client.post(
            reverse("invoicing:quote_create"),
            {
                "order": str(self.order.pk),
                "client": str(self.client_obj.pk),
                "valid_until": (date.today() + timedelta(days=30)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Quote.objects.count(), 1)

    def test_quote_detail(self):
        q = Quote.objects.create(
            order=self.order,
            client=self.client_obj,
            valid_until=date.today() + timedelta(days=30),
            pharmacy=self.pharmacy,
        )
        response = self.test_client.get(reverse("invoicing:quote_detail", kwargs={"pk": q.pk}))
        self.assertEqual(response.status_code, 200)

    def test_quote_add_line(self):
        q = Quote.objects.create(
            order=self.order,
            client=self.client_obj,
            valid_until=date.today() + timedelta(days=30),
            pharmacy=self.pharmacy,
        )
        response = self.test_client.post(
            reverse("invoicing:quote_add_line", kwargs={"quote_pk": q.pk}),
            {
                "description": "Test Line",
                "quantity": "2.000",
                "unit": "un",
                "unit_price": "25.00",
                "iva_rate": "23.00",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(q.lines.count(), 1)

    def test_quote_to_invoice(self):
        q = Quote.objects.create(
            order=self.order,
            client=self.client_obj,
            valid_until=date.today() + timedelta(days=30),
            pharmacy=self.pharmacy,
        )
        QuoteLine.objects.create(
            quote=q,
            description="Item 1",
            quantity=1,
            unit_price=Decimal("100.00"),
        )
        response = self.test_client.post(
            reverse("invoicing:quote_to_invoice", kwargs={"pk": q.pk}),
            {
                "due_date": (date.today() + timedelta(days=60)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.count(), 1)
        inv = Invoice.objects.first()
        self.assertEqual(inv.lines.count(), 1)


class InvoiceViewTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(
            name="Test Pharmacy",
            slug="inv-views-invoice",
        )
        self.test_client = TestClient()
        self.user = User.objects.create_user(
            username="admin_user",
            password="test1234",
        )
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.ADMIN,
            pharmacy=self.pharmacy,
        )
        self.test_client.login(username="admin_user", password="test1234")
        self.client_obj = Client.objects.create(
            name="Test",
            nif="444555666",
            pharmacy=self.pharmacy,
        )
        self.order = Order.objects.create(
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )

    def test_invoice_list(self):
        response = self.test_client.get(reverse("invoicing:invoice_list"))
        self.assertEqual(response.status_code, 200)

    def test_invoice_create(self):
        response = self.test_client.post(
            reverse("invoicing:invoice_create"),
            {
                "order": str(self.order.pk),
                "client": str(self.client_obj.pk),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.count(), 1)

    def test_invoice_detail(self):
        inv = Invoice.objects.create(
            order=self.order,
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )
        response = self.test_client.get(reverse("invoicing:invoice_detail", kwargs={"pk": inv.pk}))
        self.assertEqual(response.status_code, 200)

    def test_invoice_status_update(self):
        inv = Invoice.objects.create(
            order=self.order,
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )
        response = self.test_client.get(
            reverse(
                "invoicing:invoice_status_update",
                kwargs={
                    "pk": inv.pk,
                    "action": "send",
                },
            )
        )
        self.assertEqual(response.status_code, 302)
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.Status.SENT)

    def test_invoice_list_status_filter(self):
        Invoice.objects.create(
            order=self.order,
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )
        response = self.test_client.get(reverse("invoicing:invoice_list") + "?status=draft")
        self.assertEqual(response.status_code, 200)


class UnauthorizedInvoicingTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(
            name="Test Pharmacy",
            slug="inv-views-unauth",
        )
        self.test_client = TestClient()
        self.user = User.objects.create_user(
            username="viewer",
            password="test1234",
        )
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.VIEWER,
            pharmacy=self.pharmacy,
        )
        self.test_client.login(username="viewer", password="test1234")

    def test_viewer_cannot_create_quote(self):
        response = self.test_client.get(reverse("invoicing:quote_create"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_create_invoice(self):
        response = self.test_client.get(reverse("invoicing:invoice_create"))
        self.assertEqual(response.status_code, 403)
