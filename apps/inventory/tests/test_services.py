from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.core.models import Pharmacy
from apps.inventory.models import Lot, ProhibitedSubstance, RawMaterial, StockMovement, Supplier
from apps.inventory.services import AlertService, ProhibitedSubstanceService, StockService
from apps.production.models import Formulation, FormulationIngredient


class StockServiceTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Stock Service Pharmacy", slug="inv-svc-stock")
        self.supplier = Supplier.objects.create(name="S", nif="111222333", pharmacy=self.pharmacy)
        self.material = RawMaterial.objects.create(
            code="RM-SVC",
            name="Test Material",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )

    def _create_lot(self, lot_number, qty, days_to_expiry=365):
        return Lot.objects.create(
            raw_material=self.material,
            lot_number=lot_number,
            supplier=self.supplier,
            initial_quantity=qty,
            current_quantity=qty,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=days_to_expiry),
        )

    def test_receive_stock(self):
        lot = self._create_lot("LOT-R01", 500)
        StockService.receive_stock(lot)
        self.assertEqual(StockMovement.objects.count(), 1)
        mv = StockMovement.objects.first()
        self.assertEqual(mv.movement_type, StockMovement.MovementType.RECEIPT)
        self.assertEqual(mv.quantity, Decimal("500"))

    def test_use_for_production_fefo(self):
        """Should consume from earliest-expiring lot first."""
        lot_early = self._create_lot("LOT-EARLY", 100, days_to_expiry=30)
        lot_late = self._create_lot("LOT-LATE", 200, days_to_expiry=365)

        usage = StockService.use_for_production(self.material, 150)

        self.assertEqual(len(usage), 2)
        self.assertEqual(usage[0][0], lot_early)
        self.assertEqual(usage[0][1], Decimal("100"))
        self.assertEqual(usage[1][0], lot_late)
        self.assertEqual(usage[1][1], Decimal("50"))

        lot_early.refresh_from_db()
        lot_late.refresh_from_db()
        self.assertTrue(lot_early.is_exhausted)
        self.assertEqual(lot_late.current_quantity, Decimal("150"))

    def test_use_for_production_single_lot(self):
        lot = self._create_lot("LOT-001", 500)
        usage = StockService.use_for_production(self.material, 200)

        self.assertEqual(len(usage), 1)
        lot.refresh_from_db()
        self.assertEqual(lot.current_quantity, Decimal("300"))
        self.assertFalse(lot.is_exhausted)

    def test_adjust_stock_positive(self):
        lot = self._create_lot("LOT-ADJ", 100)
        StockService.adjust_stock(lot, 50, notes="Found extra")

        lot.refresh_from_db()
        self.assertEqual(lot.current_quantity, Decimal("150"))
        mv = StockMovement.objects.filter(movement_type=StockMovement.MovementType.ADJUSTMENT).first()
        self.assertEqual(mv.quantity, Decimal("50"))

    def test_adjust_stock_negative_exhausts(self):
        lot = self._create_lot("LOT-NEG", 30)
        StockService.adjust_stock(lot, -50, notes="Correction")

        lot.refresh_from_db()
        self.assertEqual(lot.current_quantity, Decimal("0"))
        self.assertTrue(lot.is_exhausted)

    def test_dispose_stock(self):
        lot = self._create_lot("LOT-DISP", 200)
        StockService.dispose_stock(lot, 80, notes="Expired")

        lot.refresh_from_db()
        self.assertEqual(lot.current_quantity, Decimal("120"))
        mv = StockMovement.objects.filter(movement_type=StockMovement.MovementType.DISPOSAL).first()
        self.assertEqual(mv.quantity, Decimal("-80"))


class AlertServiceTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Alert Service Pharmacy", slug="inv-svc-alert")
        self.supplier = Supplier.objects.create(name="S", nif="999000111", pharmacy=self.pharmacy)

    def test_low_stock_materials(self):
        m = RawMaterial.objects.create(
            code="RM-LOW",
            name="Low Stock",
            default_unit="g",
            minimum_stock=100,
            pharmacy=self.pharmacy,
        )
        # No lots, so current_stock=0, which is <= minimum_stock=100
        low = AlertService.get_low_stock_materials()
        self.assertIn(m, low)

    def test_expiring_lots(self):
        m = RawMaterial.objects.create(
            code="RM-EXP",
            name="Expiring",
            default_unit="g",
            pharmacy=self.pharmacy,
        )
        Lot.objects.create(
            raw_material=m,
            lot_number="LOT-EXP",
            supplier=self.supplier,
            initial_quantity=100,
            current_quantity=100,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=10),
        )
        expiring = AlertService.get_expiring_lots(days=30)
        self.assertEqual(expiring.count(), 1)

    def test_expired_lots(self):
        m = RawMaterial.objects.create(
            code="RM-DEAD",
            name="Expired",
            default_unit="g",
            pharmacy=self.pharmacy,
        )
        Lot.objects.create(
            raw_material=m,
            lot_number="LOT-DEAD",
            supplier=self.supplier,
            initial_quantity=100,
            current_quantity=50,
            received_date=date.today() - timedelta(days=400),
            expiry_date=date.today() - timedelta(days=10),
        )
        expired = AlertService.get_expired_lots()
        self.assertEqual(expired.count(), 1)


class ProhibitedSubstanceServiceTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Prohibited Service Pharmacy", slug="inv-svc-prohibited")
        self.supplier = Supplier.objects.create(name="PS", nif="222333444", pharmacy=self.pharmacy)
        self.material = RawMaterial.objects.create(
            code="RM-PS",
            name="Phenylbutazone",
            cas_number="50-33-9",
            default_unit="g",
            pharmacy=self.pharmacy,
        )
        self.formulation = Formulation.objects.create(
            code="F-PS",
            name="Test Formula",
            pharmaceutical_form="cream",
            pharmacy=self.pharmacy,
        )
        FormulationIngredient.objects.create(
            formulation=self.formulation,
            raw_material=self.material,
            quantity=Decimal("5.0000"),
            unit="g",
        )

    def test_no_violation_without_prohibited(self):
        violations = ProhibitedSubstanceService.check_formulation(self.formulation)
        self.assertEqual(len(violations), 0)

    def test_violation_by_cas_number(self):
        ProhibitedSubstance.objects.create(
            name="Phenylbutazone",
            cas_number="50-33-9",
        )
        violations = ProhibitedSubstanceService.check_formulation(self.formulation)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0][0], self.material)

    def test_violation_by_name(self):
        # Material without CAS but name matches
        material2 = RawMaterial.objects.create(
            code="RM-PS2",
            name="Aminophenazone",
            default_unit="g",
            pharmacy=self.pharmacy,
        )
        FormulationIngredient.objects.create(
            formulation=self.formulation,
            raw_material=material2,
            quantity=Decimal("2.0000"),
            unit="g",
        )
        ProhibitedSubstance.objects.create(name="Aminophenazone")
        violations = ProhibitedSubstanceService.check_formulation(self.formulation)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0][0], material2)
