from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django_fsm import TransitionNotAllowed

from apps.core.models import Pharmacy
from apps.invoicing.models import (
    Invoice,
    Quote,
    QuoteLine,
    SipharmaProvider,
)
from apps.orders.models import Client, Order


class QuoteModelTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(
            name="Test Pharmacy",
            slug="inv-model-quote",
        )
        self.client_obj = Client.objects.create(
            name="Test Client",
            nif="111222333",
            pharmacy=self.pharmacy,
        )
        self.order = Order.objects.create(
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )

    def test_quote_number_auto_generated(self):
        q = Quote.objects.create(
            order=self.order,
            client=self.client_obj,
            valid_until=date.today() + timedelta(days=30),
            pharmacy=self.pharmacy,
        )
        self.assertTrue(q.quote_number.startswith("QUO-"))
        self.assertIn("-0001", q.quote_number)

    def test_sequential_quote_numbers(self):
        q1 = Quote.objects.create(
            order=self.order,
            client=self.client_obj,
            valid_until=date.today() + timedelta(days=30),
            pharmacy=self.pharmacy,
        )
        q2 = Quote.objects.create(
            order=self.order,
            client=self.client_obj,
            valid_until=date.today() + timedelta(days=30),
            pharmacy=self.pharmacy,
        )
        seq1 = int(q1.quote_number.split("-")[-1])
        seq2 = int(q2.quote_number.split("-")[-1])
        self.assertEqual(seq2, seq1 + 1)

    def test_quote_total(self):
        q = Quote.objects.create(
            order=self.order,
            client=self.client_obj,
            valid_until=date.today() + timedelta(days=30),
            pharmacy=self.pharmacy,
        )
        QuoteLine.objects.create(
            quote=q,
            description="Item 1",
            quantity=2,
            unit_price=Decimal("10.00"),
            iva_rate=Decimal("23.00"),
        )
        QuoteLine.objects.create(
            quote=q,
            description="Item 2",
            quantity=1,
            unit_price=Decimal("50.00"),
            iva_rate=Decimal("23.00"),
        )
        self.assertEqual(q.total, Decimal("70.00"))


class QuoteLineTest(TestCase):
    def test_total_calculation(self):
        pharmacy = Pharmacy.objects.create(
            name="Test Pharmacy",
            slug="inv-model-quoteline",
        )
        client = Client.objects.create(
            name="C",
            nif="444555666",
            pharmacy=pharmacy,
        )
        order = Order.objects.create(client=client, pharmacy=pharmacy)
        q = Quote.objects.create(
            order=order,
            client=client,
            valid_until=date.today() + timedelta(days=30),
            pharmacy=pharmacy,
        )
        line = QuoteLine.objects.create(
            quote=q,
            description="Test",
            quantity=3,
            unit_price=Decimal("15.00"),
            iva_rate=Decimal("23.00"),
        )
        self.assertEqual(line.total, Decimal("45.00"))
        expected_iva = Decimal("45.00") * Decimal("1.23")
        self.assertAlmostEqual(float(line.total_with_iva), float(expected_iva))


class InvoiceModelTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(
            name="Test Pharmacy",
            slug="inv-model-invoice",
        )
        self.client_obj = Client.objects.create(
            name="Test",
            nif="777888999",
            pharmacy=self.pharmacy,
        )
        self.order = Order.objects.create(
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )

    def test_invoice_number_auto_generated(self):
        inv = Invoice.objects.create(
            order=self.order,
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )
        self.assertTrue(inv.invoice_number.startswith("INV-"))

    def test_fsm_happy_path(self):
        inv = Invoice.objects.create(
            order=self.order,
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )
        self.assertEqual(inv.status, Invoice.Status.DRAFT)

        inv.send()
        inv.save()
        self.assertEqual(inv.status, Invoice.Status.SENT)

        inv.mark_paid()
        inv.save()
        self.assertEqual(inv.status, Invoice.Status.PAID)

    def test_fsm_overdue_then_paid(self):
        inv = Invoice.objects.create(
            order=self.order,
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )
        inv.send()
        inv.mark_overdue()
        inv.save()
        self.assertEqual(inv.status, Invoice.Status.OVERDUE)

        inv.mark_paid()
        inv.save()
        self.assertEqual(inv.status, Invoice.Status.PAID)

    def test_fsm_cancel_from_draft(self):
        inv = Invoice.objects.create(
            order=self.order,
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )
        inv.cancel()
        inv.save()
        self.assertEqual(inv.status, Invoice.Status.CANCELLED)

    def test_fsm_invalid_transition(self):
        inv = Invoice.objects.create(
            order=self.order,
            client=self.client_obj,
            pharmacy=self.pharmacy,
        )
        with self.assertRaises(TransitionNotAllowed):
            inv.mark_paid()  # Can't pay from draft


class SipharmaProviderTest(TestCase):
    def test_stub_create_invoice(self):
        pharmacy = Pharmacy.objects.create(
            name="Test Pharmacy",
            slug="inv-model-sipharma",
        )
        client = Client.objects.create(
            name="C",
            nif="000111222",
            pharmacy=pharmacy,
        )
        order = Order.objects.create(client=client, pharmacy=pharmacy)
        inv = Invoice.objects.create(
            order=order,
            client=client,
            pharmacy=pharmacy,
        )

        provider = SipharmaProvider()
        external_id = provider.create_invoice(inv)
        self.assertIn(inv.invoice_number, external_id)
