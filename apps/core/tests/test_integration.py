"""End-to-end integration test: Order → Quote → Production → Inventory → Invoice."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from apps.core.models import Pharmacy, UserProfile
from apps.inventory.models import Lot, RawMaterial, StockMovement, Supplier
from apps.inventory.services import StockService
from apps.invoicing.models import Invoice, InvoiceLine, Quote, QuoteLine
from apps.orders.models import Client, Order, OrderItem
from apps.production.models import (
    BatchMaterialUsage,
    Formulation,
    FormulationIngredient,
    FormulationStep,
    ProductionBatch,
)


class EndToEndWorkflowTest(TestCase):
    """Full workflow: client order → quote → production → stock usage → invoice."""

    def setUp(self):
        # --- Pharmacy ---
        self.pharmacy = Pharmacy.objects.create(name="Integration Pharmacy", slug="integration-pharmacy")

        # --- Users ---
        self.pharmacist = User.objects.create_user(
            username="pharmacist",
            password="pass1234",
            first_name="Ana",
            last_name="Silva",
        )
        UserProfile.objects.create(
            user=self.pharmacist,
            role=UserProfile.Role.PHARMACIST,
            pharmacy=self.pharmacy,
        )
        self.tech = User.objects.create_user(
            username="tech",
            password="pass1234",
            first_name="Carlos",
            last_name="Santos",
        )
        UserProfile.objects.create(
            user=self.tech,
            role=UserProfile.Role.LAB_TECHNICIAN,
            pharmacy=self.pharmacy,
        )

        # --- Inventory setup ---
        self.supplier = Supplier.objects.create(
            name="ChemSupply Lda",
            nif="500100200",
            pharmacy=self.pharmacy,
        )
        self.paracetamol = RawMaterial.objects.create(
            code="RM-001",
            name="Paracetamol",
            default_unit="g",
            minimum_stock=500,
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )
        self.excipient = RawMaterial.objects.create(
            code="RM-002",
            name="Lactose Monohydrate",
            default_unit="g",
            minimum_stock=1000,
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )
        self.lot_para = Lot.objects.create(
            raw_material=self.paracetamol,
            lot_number="LOT-P001",
            supplier=self.supplier,
            initial_quantity=2000,
            current_quantity=2000,
            received_date=date.today() - timedelta(days=30),
            expiry_date=date.today() + timedelta(days=365),
        )
        self.lot_exc = Lot.objects.create(
            raw_material=self.excipient,
            lot_number="LOT-E001",
            supplier=self.supplier,
            initial_quantity=5000,
            current_quantity=5000,
            received_date=date.today() - timedelta(days=30),
            expiry_date=date.today() + timedelta(days=365),
        )
        # Record receipt movements
        StockService.receive_stock(self.lot_para, user=self.pharmacist)
        StockService.receive_stock(self.lot_exc, user=self.pharmacist)

        # --- Formulation ---
        self.formulation = Formulation.objects.create(
            code="FORM-001",
            name="Paracetamol Capsules 500mg",
            pharmaceutical_form="capsule",
            shelf_life_days=180,
            pharmacy=self.pharmacy,
        )
        FormulationIngredient.objects.create(
            formulation=self.formulation,
            raw_material=self.paracetamol,
            quantity=Decimal("500.0000"),
            unit="mg",
            is_active_ingredient=True,
            order_of_addition=1,
        )
        FormulationIngredient.objects.create(
            formulation=self.formulation,
            raw_material=self.excipient,
            quantity=Decimal("200.0000"),
            unit="mg",
            is_active_ingredient=False,
            order_of_addition=2,
        )
        FormulationStep.objects.create(
            formulation=self.formulation,
            step_number=1,
            title="Weigh ingredients",
            description="Weigh all ingredients.",
        )
        FormulationStep.objects.create(
            formulation=self.formulation,
            step_number=2,
            title="Mix and encapsulate",
            description="Mix ingredients and fill capsules.",
        )

        # --- Client ---
        self.client = Client.objects.create(
            client_type=Client.ClientType.PHARMACY,
            name="Farmacia Central",
            nif="501234567",
            email="central@example.com",
            phone="210000000",
            pharmacy=self.pharmacy,
        )

    def test_full_workflow(self):
        # 1. Create Order
        order = Order.objects.create(
            client=self.client,
            source=Order.Source.IN_PERSON,
            priority=Order.Priority.NORMAL,
            notes="60 capsules needed",
            pharmacy=self.pharmacy,
        )
        self.assertEqual(order.status, "new_request")
        self.assertTrue(order.order_number.startswith("ORD-"))

        OrderItem.objects.create(
            order=order,
            description="Paracetamol 500mg caps x60",
            formulation=self.formulation,
            quantity=60,
            unit="caps",
            unit_price=Decimal("0.50"),
        )

        # 2. Order workflow: new → waiting_for_quote
        order.send_for_quote()
        order.save()
        self.assertEqual(order.status, "waiting_for_quote")

        # 3. Create Quote
        quote = Quote.objects.create(
            order=order,
            client=self.client,
            valid_until=date.today() + timedelta(days=30),
            pharmacy=self.pharmacy,
        )
        self.assertTrue(quote.quote_number.startswith("QUO-"))

        QuoteLine.objects.create(
            quote=quote,
            description="Paracetamol 500mg capsules x60",
            quantity=60,
            unit="caps",
            unit_price=Decimal("0.50"),
            iva_rate=Decimal("6.00"),
        )
        self.assertEqual(quote.total, Decimal("30.000"))

        # 4. Order: quote accepted → waiting for recipe
        order.quote_accepted()
        order.save()
        self.assertEqual(order.status, "waiting_for_recipe")

        # 5. Recipe received → ready for production
        order.recipe_received()
        order.save()
        self.assertEqual(order.status, "ready_for_production")

        # 6. Start production → in_production
        order.start_production()
        order.save()
        self.assertEqual(order.status, "in_production")

        # 7. Create production batch
        batch = ProductionBatch.objects.create(
            order=order,
            formulation=self.formulation,
            produced_by=self.tech,
            quantity_produced=60,
            unit="caps",
            expiry_date=date.today() + timedelta(days=180),
        )
        self.assertTrue(batch.batch_number.startswith("BAT-"))
        self.assertEqual(batch.status, "planned")

        # 8. Use stock for production (FEFO)
        para_used = StockService.use_for_production(
            self.paracetamol,
            Decimal("30"),
            batch=batch,
            user=self.tech,
        )
        exc_used = StockService.use_for_production(
            self.excipient,
            Decimal("12"),
            batch=batch,
            user=self.tech,
        )
        self.assertEqual(len(para_used), 1)
        self.assertEqual(len(exc_used), 1)

        # Record traceability
        for lot, qty in para_used:
            BatchMaterialUsage.objects.create(
                batch=batch,
                lot=lot,
                quantity_used=qty,
            )
        for lot, qty in exc_used:
            BatchMaterialUsage.objects.create(
                batch=batch,
                lot=lot,
                quantity_used=qty,
            )

        # Verify stock decreased
        self.lot_para.refresh_from_db()
        self.assertEqual(self.lot_para.current_quantity, Decimal("1970"))
        self.lot_exc.refresh_from_db()
        self.assertEqual(self.lot_exc.current_quantity, Decimal("4988"))

        # Verify traceability records
        self.assertEqual(batch.material_usage.count(), 2)

        # 9. Production workflow: planned → in_progress → quality → approved → complete
        batch.start()
        batch.save()
        self.assertEqual(batch.status, "in_progress")

        batch.send_to_quality()
        batch.save()
        self.assertEqual(batch.status, "quality_check")

        batch.approve()
        batch.verified_by = self.pharmacist
        batch.save()
        self.assertEqual(batch.status, "approved")

        batch.complete()
        batch.save()
        self.assertEqual(batch.status, "complete")

        # 10. Order: production_complete → ready → complete
        order.production_complete()
        order.save()
        self.assertEqual(order.status, "ready")

        # 11. Create Invoice from Quote
        invoice = Invoice.objects.create(
            order=order,
            client=self.client,
            due_date=date.today() + timedelta(days=30),
            pharmacy=self.pharmacy,
        )
        self.assertTrue(invoice.invoice_number.startswith("INV-"))

        for line in quote.lines.all():
            InvoiceLine.objects.create(
                invoice=invoice,
                description=line.description,
                quantity=line.quantity,
                unit=line.unit,
                unit_price=line.unit_price,
                iva_rate=line.iva_rate,
            )
        self.assertEqual(invoice.total, Decimal("30.000"))

        # 12. Invoice workflow: draft → sent → paid
        invoice.send()
        invoice.save()
        self.assertEqual(invoice.status, "sent")

        invoice.mark_paid()
        invoice.save()
        self.assertEqual(invoice.status, "paid")

        # 13. Complete the order
        order.mark_complete()
        order.save()
        self.assertEqual(order.status, "complete")

        # --- Final assertions ---
        # Stock movements: 2 receipts + 2 production uses = 4
        self.assertEqual(StockMovement.objects.count(), 4)
        self.assertEqual(
            StockMovement.objects.filter(
                movement_type=StockMovement.MovementType.PRODUCTION_USE,
            ).count(),
            2,
        )

        # Full traceability chain
        usage = BatchMaterialUsage.objects.filter(batch=batch)
        self.assertEqual(usage.count(), 2)
        lots_used = set(usage.values_list("lot__lot_number", flat=True))
        self.assertEqual(lots_used, {"LOT-P001", "LOT-E001"})
