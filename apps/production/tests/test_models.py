from django.contrib.auth.models import User
from django.test import TestCase

from apps.core.models import Pharmacy
from apps.inventory.models import RawMaterial, Supplier
from apps.orders.models import Client, Order
from apps.production.models import (
    BatchMaterialUsage,
    Formulation,
    FormulationIngredient,
    FormulationStep,
    Prescription,
    ProductionBatch,
    ProductionStepLog,
)


class FormulationModelTest(TestCase):
    def test_create_formulation(self):
        pharmacy = Pharmacy.objects.create(name="Form Pharmacy", slug="prod-model-form")
        f = Formulation.objects.create(
            code="F-001",
            name="Creme Hidratante",
            pharmaceutical_form="cream",
            shelf_life_days=180,
            pharmacy=pharmacy,
        )
        self.assertEqual(str(f), "F-001 - Creme Hidratante")
        self.assertIsNotNone(f.id)

    def test_soft_delete(self):
        pharmacy = Pharmacy.objects.create(name="Form Pharmacy SD", slug="prod-model-form-sd")
        f = Formulation.objects.create(
            code="F-002",
            name="Test",
            pharmaceutical_form="capsule",
            pharmacy=pharmacy,
        )
        f.soft_delete()
        self.assertEqual(Formulation.objects.count(), 0)
        self.assertEqual(Formulation.all_objects.count(), 1)


class FormulationIngredientTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Ingredient Pharmacy", slug="prod-model-ing")
        self.formulation = Formulation.objects.create(
            code="F-010",
            name="Test Formula",
            pharmaceutical_form="cream",
            pharmacy=self.pharmacy,
        )
        self.supplier = Supplier.objects.create(
            name="Lab Supplier",
            nif="111222333",
            pharmacy=self.pharmacy,
        )
        self.material = RawMaterial.objects.create(
            code="RM-001",
            name="Paracetamol",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )

    def test_create_ingredient(self):
        ing = FormulationIngredient.objects.create(
            formulation=self.formulation,
            raw_material=self.material,
            quantity=10.5,
            unit="g",
            is_active_ingredient=True,
            order_of_addition=1,
        )
        self.assertIn("Paracetamol", str(ing))
        self.assertTrue(ing.is_active_ingredient)

    def test_ingredients_ordered_by_addition(self):
        FormulationIngredient.objects.create(
            formulation=self.formulation,
            raw_material=self.material,
            quantity=5,
            unit="g",
            order_of_addition=2,
        )
        mat2 = RawMaterial.objects.create(
            code="RM-002",
            name="Excipient",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )
        FormulationIngredient.objects.create(
            formulation=self.formulation,
            raw_material=mat2,
            quantity=20,
            unit="g",
            order_of_addition=1,
        )
        ings = list(self.formulation.ingredients.all())
        self.assertEqual(ings[0].order_of_addition, 1)
        self.assertEqual(ings[1].order_of_addition, 2)


class FormulationStepTest(TestCase):
    def test_create_step(self):
        pharmacy = Pharmacy.objects.create(name="Step Pharmacy", slug="prod-model-step")
        f = Formulation.objects.create(
            code="F-020",
            name="Test",
            pharmaceutical_form="solution",
            pharmacy=pharmacy,
        )
        step = FormulationStep.objects.create(formulation=f, step_number=1, title="Weigh ingredients")
        self.assertEqual(str(step), "Step 1: Weigh ingredients")

    def test_steps_ordered_by_number(self):
        pharmacy = Pharmacy.objects.create(name="Step Pharmacy 2", slug="prod-model-step2")
        f = Formulation.objects.create(
            code="F-021",
            name="Test",
            pharmaceutical_form="cream",
            pharmacy=pharmacy,
        )
        FormulationStep.objects.create(formulation=f, step_number=3, title="Package")
        FormulationStep.objects.create(formulation=f, step_number=1, title="Weigh")
        FormulationStep.objects.create(formulation=f, step_number=2, title="Mix")
        steps = list(f.steps.all())
        self.assertEqual([s.step_number for s in steps], [1, 2, 3])


class PrescriptionModelTest(TestCase):
    def test_create_prescription(self):
        pharmacy = Pharmacy.objects.create(name="Rx Pharmacy", slug="prod-model-rx")
        client = Client.objects.create(name="Test Client", nif="999888777", pharmacy=pharmacy)
        order = Order.objects.create(client=client, pharmacy=pharmacy)
        rx = Prescription.objects.create(
            order=order,
            doctor_name="Dr. Silva",
            doctor_license="12345",
            patient_name="Joao Santos",
            patient_tax_number="123456789",
        )
        self.assertIn("Joao Santos", str(rx))

    def test_rgpd_meta_fields(self):
        self.assertIn("patient_name", Prescription.RGPDMeta.anonymizable_fields)
        self.assertIn("patient_tax_number", Prescription.RGPDMeta.anonymizable_fields)


class ProductionBatchModelTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Batch Pharmacy", slug="prod-model-batch")
        self.client_obj = Client.objects.create(
            name="Client",
            nif="111000222",
            pharmacy=self.pharmacy,
        )
        self.order = Order.objects.create(client=self.client_obj, pharmacy=self.pharmacy)
        self.formulation = Formulation.objects.create(
            code="F-100",
            name="Batch Test",
            pharmaceutical_form="cream",
            pharmacy=self.pharmacy,
        )

    def test_batch_number_auto_generated(self):
        batch = ProductionBatch.objects.create(
            order=self.order,
            formulation=self.formulation,
            quantity_produced=100,
            pharmacy=self.pharmacy,
        )
        self.assertTrue(batch.batch_number.startswith("BAT-"))
        self.assertIn("-0001", batch.batch_number)

    def test_sequential_batch_numbers(self):
        b1 = ProductionBatch.objects.create(
            order=self.order,
            formulation=self.formulation,
            pharmacy=self.pharmacy,
        )
        b2 = ProductionBatch.objects.create(
            order=self.order,
            formulation=self.formulation,
            pharmacy=self.pharmacy,
        )
        seq1 = int(b1.batch_number.split("-")[-1])
        seq2 = int(b2.batch_number.split("-")[-1])
        self.assertEqual(seq2, seq1 + 1)

    def test_fsm_transitions_happy_path(self):
        batch = ProductionBatch.objects.create(
            order=self.order,
            formulation=self.formulation,
            pharmacy=self.pharmacy,
        )
        self.assertEqual(batch.status, ProductionBatch.Status.PLANNED)

        batch.start()
        batch.save()
        self.assertEqual(batch.status, ProductionBatch.Status.IN_PROGRESS)

        batch.send_to_quality()
        batch.save()
        self.assertEqual(batch.status, ProductionBatch.Status.QUALITY_CHECK)

        batch.approve()
        batch.save()
        self.assertEqual(batch.status, ProductionBatch.Status.APPROVED)

        batch.complete()
        batch.save()
        self.assertEqual(batch.status, ProductionBatch.Status.COMPLETE)

    def test_fsm_reject_from_quality_check(self):
        batch = ProductionBatch.objects.create(
            order=self.order,
            formulation=self.formulation,
            pharmacy=self.pharmacy,
        )
        batch.start()
        batch.send_to_quality()
        batch.reject()
        batch.save()
        self.assertEqual(batch.status, ProductionBatch.Status.REJECTED)

    def test_invalid_transition_raises(self):
        from django_fsm import TransitionNotAllowed

        batch = ProductionBatch.objects.create(
            order=self.order,
            formulation=self.formulation,
            pharmacy=self.pharmacy,
        )
        with self.assertRaises(TransitionNotAllowed):
            batch.approve()  # Can't approve from "planned"


class ProductionStepLogTest(TestCase):
    def test_create_step_log(self):
        pharmacy = Pharmacy.objects.create(name="StepLog Pharmacy", slug="prod-model-steplog")
        client = Client.objects.create(name="C", nif="000111222", pharmacy=pharmacy)
        order = Order.objects.create(client=client, pharmacy=pharmacy)
        formulation = Formulation.objects.create(
            code="F-200",
            name="T",
            pharmaceutical_form="cream",
            pharmacy=pharmacy,
        )
        batch = ProductionBatch.objects.create(
            order=order,
            formulation=formulation,
            pharmacy=pharmacy,
        )
        step = FormulationStep.objects.create(formulation=formulation, step_number=1, title="Mix")
        user = User.objects.create_user(username="tech", password="test1234")

        log = ProductionStepLog.objects.create(batch=batch, step=step, performed_by=user, observations="All good")
        self.assertIn("Mix", str(log))


class BatchMaterialUsageTest(TestCase):
    def test_create_usage(self):
        pharmacy = Pharmacy.objects.create(name="Usage Pharmacy", slug="prod-model-usage")
        client = Client.objects.create(name="C", nif="333444555", pharmacy=pharmacy)
        order = Order.objects.create(client=client, pharmacy=pharmacy)
        formulation = Formulation.objects.create(
            code="F-300",
            name="T",
            pharmaceutical_form="cream",
            pharmacy=pharmacy,
        )
        batch = ProductionBatch.objects.create(
            order=order,
            formulation=formulation,
            pharmacy=pharmacy,
        )
        supplier = Supplier.objects.create(name="S", nif="666777888", pharmacy=pharmacy)
        material = RawMaterial.objects.create(
            code="RM-100",
            name="Zinc Oxide",
            default_unit="g",
            preferred_supplier=supplier,
            pharmacy=pharmacy,
        )
        from datetime import date

        from apps.inventory.models import Lot

        lot = Lot.objects.create(
            raw_material=material,
            lot_number="LOT-001",
            supplier=supplier,
            initial_quantity=1000,
            current_quantity=1000,
            received_date=date.today(),
            expiry_date=date(2027, 12, 31),
        )
        usage = BatchMaterialUsage.objects.create(batch=batch, lot=lot, quantity_used=50)
        self.assertIn("50", str(usage))
