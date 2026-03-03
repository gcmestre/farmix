from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils.translation import override as lang_override

from apps.core.models import Pharmacy
from apps.inventory.models import Lot, RawMaterial, StockMovement, Supplier


class SupplierModelTest(TestCase):
    def test_create_supplier(self):
        pharmacy = Pharmacy.objects.create(name="Supplier Test Pharmacy", slug="inv-model-supplier")
        s = Supplier.objects.create(name="Lab Supplier", nif="123456789", pharmacy=pharmacy)
        self.assertEqual(str(s), "Lab Supplier")

    def test_soft_delete(self):
        pharmacy = Pharmacy.objects.create(name="Soft Delete Pharmacy", slug="inv-model-supplier-del")
        s = Supplier.objects.create(name="Test", nif="111222333", pharmacy=pharmacy)
        s.soft_delete()
        self.assertEqual(Supplier.objects.count(), 0)
        self.assertEqual(Supplier.all_objects.count(), 1)


class RawMaterialModelTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Material Test Pharmacy", slug="inv-model-material")
        self.supplier = Supplier.objects.create(name="S", nif="999888777", pharmacy=self.pharmacy)

    def test_create_material(self):
        m = RawMaterial.objects.create(
            code="RM-001",
            name="Paracetamol",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )
        self.assertEqual(str(m), "RM-001 - Paracetamol")

    def test_current_stock_no_lots(self):
        m = RawMaterial.objects.create(
            code="RM-002",
            name="Empty",
            default_unit="g",
            minimum_stock=100,
            pharmacy=self.pharmacy,
        )
        self.assertEqual(m.current_stock, 0)
        self.assertTrue(m.is_low_stock)

    def test_current_stock_with_lots(self):
        m = RawMaterial.objects.create(
            code="RM-003",
            name="Stocked",
            default_unit="g",
            minimum_stock=50,
            pharmacy=self.pharmacy,
        )
        Lot.objects.create(
            raw_material=m,
            lot_number="L1",
            supplier=self.supplier,
            initial_quantity=100,
            current_quantity=80,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
        )
        Lot.objects.create(
            raw_material=m,
            lot_number="L2",
            supplier=self.supplier,
            initial_quantity=50,
            current_quantity=50,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
        )
        self.assertEqual(m.current_stock, Decimal("130"))
        self.assertFalse(m.is_low_stock)

    def test_current_stock_excludes_exhausted(self):
        m = RawMaterial.objects.create(
            code="RM-004",
            name="Partial",
            default_unit="g",
            pharmacy=self.pharmacy,
        )
        Lot.objects.create(
            raw_material=m,
            lot_number="L1",
            supplier=self.supplier,
            initial_quantity=100,
            current_quantity=0,
            is_exhausted=True,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
        )
        Lot.objects.create(
            raw_material=m,
            lot_number="L2",
            supplier=self.supplier,
            initial_quantity=50,
            current_quantity=50,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
        )
        self.assertEqual(m.current_stock, Decimal("50"))


class LotModelTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Lot Test Pharmacy", slug="inv-model-lot")
        self.supplier = Supplier.objects.create(name="S", nif="444555666", pharmacy=self.pharmacy)
        self.material = RawMaterial.objects.create(
            code="RM-010",
            name="Zinc Oxide",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )

    def test_create_lot(self):
        lot = Lot.objects.create(
            raw_material=self.material,
            lot_number="LOT-001",
            supplier=self.supplier,
            initial_quantity=1000,
            current_quantity=1000,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
        )
        self.assertIn("LOT-001", str(lot))

    def test_fefo_ordering(self):
        """Lots should be ordered by expiry_date (First Expiry First Out)."""
        Lot.objects.create(
            raw_material=self.material,
            lot_number="L-LATE",
            supplier=self.supplier,
            initial_quantity=100,
            current_quantity=100,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
        )
        Lot.objects.create(
            raw_material=self.material,
            lot_number="L-EARLY",
            supplier=self.supplier,
            initial_quantity=100,
            current_quantity=100,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
        )
        lots = list(self.material.lots.all())
        self.assertEqual(lots[0].lot_number, "L-EARLY")
        self.assertEqual(lots[1].lot_number, "L-LATE")


class StockMovementModelTest(TestCase):
    def test_create_movement(self):
        pharmacy = Pharmacy.objects.create(name="Movement Test Pharmacy", slug="inv-model-movement")
        supplier = Supplier.objects.create(name="S", nif="777888999", pharmacy=pharmacy)
        material = RawMaterial.objects.create(
            code="RM-020",
            name="Test",
            default_unit="g",
            pharmacy=pharmacy,
        )
        lot = Lot.objects.create(
            raw_material=material,
            lot_number="LOT-M01",
            supplier=supplier,
            initial_quantity=500,
            current_quantity=500,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=180),
        )
        mv = StockMovement.objects.create(
            lot=lot,
            movement_type=StockMovement.MovementType.RECEIPT,
            quantity=500,
            balance_after=500,
        )
        with lang_override("en"):
            self.assertIn("Receipt", str(mv))
