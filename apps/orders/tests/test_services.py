from django.contrib.auth.models import User
from django.test import TestCase

from apps.core.models import AuditLog, Pharmacy, UserProfile
from apps.orders.models import Client, Order, OrderStatusLog
from apps.orders.services import OrderWorkflowService


class OrderWorkflowServiceTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Service Test Pharmacy", slug="orders-services")
        self.user = User.objects.create_user(username="pharmacist", password="test1234")
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.PHARMACIST, pharmacy=self.pharmacy)
        self.client_obj = Client.objects.create(name="Test Client", nif="111222333", pharmacy=self.pharmacy)
        self.order = Order.objects.create(client=self.client_obj, pharmacy=self.pharmacy)

    def test_transition_creates_log(self):
        OrderWorkflowService.transition(self.order, "send_for_quote", self.user, "Sending quote")
        self.assertEqual(self.order.status, Order.Status.WAITING_FOR_QUOTE)
        self.assertEqual(OrderStatusLog.objects.count(), 1)
        log = OrderStatusLog.objects.first()
        self.assertEqual(log.from_status, Order.Status.NEW_REQUEST)
        self.assertEqual(log.to_status, Order.Status.WAITING_FOR_QUOTE)

    def test_transition_creates_audit_log(self):
        OrderWorkflowService.transition(self.order, "send_for_quote", self.user)
        self.assertTrue(AuditLog.objects.filter(model_name="Order", action="update").exists())

    def test_invalid_transition_raises(self):
        with self.assertRaises(ValueError):
            OrderWorkflowService.transition(self.order, "nonexistent", self.user)

    def test_full_workflow(self):
        steps = [
            "send_for_quote",
            "quote_accepted",
            "recipe_received",
            "start_production",
            "production_complete",
            "mark_complete",
        ]
        for step in steps:
            OrderWorkflowService.transition(self.order, step, self.user)
        self.assertEqual(self.order.status, Order.Status.COMPLETE)
        self.assertEqual(OrderStatusLog.objects.count(), 6)
