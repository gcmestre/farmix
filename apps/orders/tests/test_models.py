from django.test import TestCase

from apps.core.models import Pharmacy
from apps.orders.models import Client, Order, OrderItem


class ClientModelTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Client Test Pharmacy", slug="orders-models-client")

    def test_create_client(self):
        client = Client.objects.create(
            name="Farmacia Central",
            nif="123456789",
            client_type=Client.ClientType.PHARMACY,
            pharmacy=self.pharmacy,
        )
        self.assertEqual(str(client), "Farmacia Central (123456789)")
        self.assertIsNotNone(client.id)

    def test_soft_delete(self):
        client = Client.objects.create(name="Test", nif="999999999", pharmacy=self.pharmacy)
        client.soft_delete()
        self.assertEqual(Client.objects.count(), 0)
        self.assertEqual(Client.all_objects.count(), 1)


class OrderModelTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Order Test Pharmacy", slug="orders-models-order")
        self.client_obj = Client.objects.create(name="Test Client", nif="111222333", pharmacy=self.pharmacy)

    def test_order_number_auto_generated(self):
        order = Order.objects.create(client=self.client_obj, pharmacy=self.pharmacy)
        self.assertTrue(order.order_number.startswith("ORD-"))
        self.assertIn("-0001", order.order_number)

    def test_sequential_order_numbers(self):
        o1 = Order.objects.create(client=self.client_obj, pharmacy=self.pharmacy)
        o2 = Order.objects.create(client=self.client_obj, pharmacy=self.pharmacy)
        seq1 = int(o1.order_number.split("-")[-1])
        seq2 = int(o2.order_number.split("-")[-1])
        self.assertEqual(seq2, seq1 + 1)

    def test_fsm_transitions(self):
        order = Order.objects.create(client=self.client_obj, pharmacy=self.pharmacy)
        self.assertEqual(order.status, Order.Status.NEW_REQUEST)

        order.send_for_quote()
        order.save()
        self.assertEqual(order.status, Order.Status.WAITING_FOR_QUOTE)

        order.quote_accepted()
        order.save()
        self.assertEqual(order.status, Order.Status.WAITING_FOR_RECIPE)

    def test_cancel_from_any_state(self):
        order = Order.objects.create(client=self.client_obj, pharmacy=self.pharmacy)
        order.cancel()
        order.save()
        self.assertEqual(order.status, Order.Status.CANCELLED)


class OrderItemTest(TestCase):
    def test_total_price(self):
        pharmacy = Pharmacy.objects.create(name="Item Test Pharmacy", slug="orders-models-item")
        client = Client.objects.create(name="Test", nif="444555666", pharmacy=pharmacy)
        order = Order.objects.create(client=client, pharmacy=pharmacy)
        item = OrderItem.objects.create(
            order=order,
            description="Creme manipulado",
            quantity=2,
            unit="un",
            unit_price=15.50,
        )
        self.assertEqual(item.total_price, 31.00)
