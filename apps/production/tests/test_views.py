from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Pharmacy, UserProfile
from apps.inventory.models import RawMaterial, Supplier
from apps.orders.models import Client, Order
from apps.production.models import (
    Formulation,
    FormulationStep,
    ProductionBatch,
    QualityControl,
)


class FormulationViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="Form View Pharmacy", slug="prod-views-form")
        self.user = User.objects.create_user(username="pharmacist", password="test1234")
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.PHARMACIST,
            pharmacy=self.pharmacy,
        )
        self.test_client.login(username="pharmacist", password="test1234")

    def test_formulation_list(self):
        response = self.test_client.get(reverse("production:formulation_list"))
        self.assertEqual(response.status_code, 200)

    def test_formulation_create(self):
        response = self.test_client.post(
            reverse("production:formulation_create"),
            {
                "code": "F-TEST-001",
                "name": "Test Cream",
                "pharmaceutical_form": "cream",
                "shelf_life_days": 90,
                "is_multi_stage": False,
                "base_quantity": "100.000",
                "base_unit": "g",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Formulation.objects.filter(code="F-TEST-001").exists())

    def test_formulation_detail(self):
        f = Formulation.objects.create(
            code="F-V01",
            name="View Test",
            pharmaceutical_form="cream",
            pharmacy=self.pharmacy,
        )
        response = self.test_client.get(reverse("production:formulation_detail", kwargs={"pk": f.pk}))
        self.assertEqual(response.status_code, 200)

    def test_formulation_edit(self):
        f = Formulation.objects.create(
            code="F-V02",
            name="Edit Test",
            pharmaceutical_form="cream",
            shelf_life_days=90,
            pharmacy=self.pharmacy,
        )
        response = self.test_client.post(
            reverse("production:formulation_edit", kwargs={"pk": f.pk}),
            {
                "code": "F-V02",
                "name": "Updated Name",
                "pharmaceutical_form": "cream",
                "shelf_life_days": 120,
                "is_multi_stage": False,
                "base_quantity": "100.000",
                "base_unit": "g",
            },
        )
        self.assertEqual(response.status_code, 302)
        f.refresh_from_db()
        self.assertEqual(f.name, "Updated Name")

    def test_formulation_add_ingredient(self):
        f = Formulation.objects.create(
            code="F-V03",
            name="Ing Test",
            pharmaceutical_form="cream",
            pharmacy=self.pharmacy,
        )
        supplier = Supplier.objects.create(
            name="S",
            nif="111222333",
            pharmacy=self.pharmacy,
        )
        material = RawMaterial.objects.create(
            code="RM-V01",
            name="Test Mat",
            default_unit="g",
            preferred_supplier=supplier,
            pharmacy=self.pharmacy,
        )
        response = self.test_client.post(
            reverse("production:formulation_add_ingredient", kwargs={"formulation_pk": f.pk}),
            {
                "raw_material": str(material.pk),
                "quantity": "10.0000",
                "unit": "g",
                "is_active_ingredient": True,
                "order_of_addition": 1,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(f.ingredients.count(), 1)


class BatchViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="Batch View Pharmacy", slug="prod-views-batch")
        self.user = User.objects.create_user(username="labtech", password="test1234")
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.LAB_TECHNICIAN,
            pharmacy=self.pharmacy,
        )
        self.test_client.login(username="labtech", password="test1234")
        self.client_obj = Client.objects.create(
            name="Farmacia",
            nif="999888777",
            pharmacy=self.pharmacy,
        )
        self.order = Order.objects.create(client=self.client_obj, pharmacy=self.pharmacy)
        self.formulation = Formulation.objects.create(
            code="F-BAT",
            name="Batch Test",
            pharmaceutical_form="cream",
            pharmacy=self.pharmacy,
        )

    def test_batch_list(self):
        response = self.test_client.get(reverse("production:batch_list"))
        self.assertEqual(response.status_code, 200)

    def test_batch_create(self):
        response = self.test_client.post(
            reverse("production:batch_create"),
            {
                "order": str(self.order.pk),
                "formulation": str(self.formulation.pk),
                "produced_by": str(self.user.pk),
                "quantity_produced": "100.000",
                "unit": "un",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProductionBatch.objects.count(), 1)

    def test_batch_detail(self):
        batch = ProductionBatch.objects.create(
            order=self.order,
            formulation=self.formulation,
            pharmacy=self.pharmacy,
        )
        response = self.test_client.get(reverse("production:batch_detail", kwargs={"pk": batch.pk}))
        self.assertEqual(response.status_code, 200)

    def test_batch_status_update(self):
        batch = ProductionBatch.objects.create(
            order=self.order,
            formulation=self.formulation,
            pharmacy=self.pharmacy,
        )
        response = self.test_client.get(
            reverse("production:batch_status_update", kwargs={"pk": batch.pk, "action": "start"})
        )
        self.assertEqual(response.status_code, 302)
        batch.refresh_from_db()
        self.assertEqual(batch.status, ProductionBatch.Status.IN_PROGRESS)

    def test_batch_step_complete(self):
        batch = ProductionBatch.objects.create(
            order=self.order,
            formulation=self.formulation,
            pharmacy=self.pharmacy,
        )
        step = FormulationStep.objects.create(formulation=self.formulation, step_number=1, title="Mix")
        response = self.test_client.post(
            reverse("production:batch_step_complete", kwargs={"batch_pk": batch.pk, "step_pk": step.pk}),
            {"observations": "Done", "parameters": "{}"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(batch.step_logs.count(), 1)

    def test_batch_list_status_filter(self):
        ProductionBatch.objects.create(
            order=self.order,
            formulation=self.formulation,
            pharmacy=self.pharmacy,
        )
        response = self.test_client.get(reverse("production:batch_list") + "?status=planned")
        self.assertEqual(response.status_code, 200)


class BatchPDFViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="PDF View Pharmacy", slug="prod-views-pdf")
        self.user = User.objects.create_user(username="pharmacist2", password="test1234")
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.PHARMACIST,
            pharmacy=self.pharmacy,
        )
        self.test_client.login(username="pharmacist2", password="test1234")
        client_obj = Client.objects.create(name="C", nif="444555666", pharmacy=self.pharmacy)
        order = Order.objects.create(client=client_obj, pharmacy=self.pharmacy)
        formulation = Formulation.objects.create(
            code="F-PDF",
            name="PDF Test",
            pharmaceutical_form="cream",
            pharmacy=self.pharmacy,
        )
        self.batch = ProductionBatch.objects.create(
            order=order,
            formulation=formulation,
            pharmacy=self.pharmacy,
        )

    def test_batch_pdf_returns_html_fallback(self):
        """PDF generation may fail without WeasyPrint system deps; should fallback to HTML."""
        response = self.test_client.get(reverse("production:batch_pdf", kwargs={"pk": self.batch.pk}))
        self.assertEqual(response.status_code, 200)


class UnauthorizedViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="Unauth View Pharmacy", slug="prod-views-unauth")
        self.user = User.objects.create_user(username="viewer", password="test1234")
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.VIEWER,
            pharmacy=self.pharmacy,
        )
        self.test_client.login(username="viewer", password="test1234")

    def test_viewer_cannot_create_formulation(self):
        response = self.test_client.get(reverse("production:formulation_create"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_create_batch(self):
        response = self.test_client.get(reverse("production:batch_create"))
        self.assertEqual(response.status_code, 403)


class QualityControlViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="QC View Pharmacy", slug="prod-views-qc")
        self.pharmacist = User.objects.create_user(username="qc_pharmacist", password="test1234")
        UserProfile.objects.create(
            user=self.pharmacist,
            role=UserProfile.Role.PHARMACIST,
            pharmacy=self.pharmacy,
        )
        self.test_client.login(username="qc_pharmacist", password="test1234")
        client_obj = Client.objects.create(name="QC Client", nif="777888999", pharmacy=self.pharmacy)
        order = Order.objects.create(client=client_obj, pharmacy=self.pharmacy)
        formulation = Formulation.objects.create(
            code="F-QC",
            name="QC Test",
            pharmaceutical_form="cream",
            pharmacy=self.pharmacy,
        )
        self.batch = ProductionBatch.objects.create(
            order=order,
            formulation=formulation,
            pharmacy=self.pharmacy,
        )

    def test_qc_create(self):
        response = self.test_client.post(
            reverse("production:qc_create", kwargs={"batch_pk": self.batch.pk}),
            {
                "appearance": "White cream, homogeneous",
                "odor": "Neutral",
                "texture": "Smooth",
                "ph_value": "5.50",
                "expected_weight": "100.000",
                "actual_weight": "98.500",
                "passed": True,
                "observations": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        qc = QualityControl.objects.get(batch=self.batch)
        self.assertTrue(qc.passed)
        self.assertEqual(qc.appearance, "White cream, homogeneous")
        # Auto-calculated deviation: |100-98.5|/100 * 100 = 1.5%
        self.assertEqual(qc.weight_deviation_pct, Decimal("1.50"))

    def test_qc_detail(self):
        QualityControl.objects.create(
            batch=self.batch,
            appearance="OK",
            passed=True,
            performed_by=self.pharmacist,
        )
        response = self.test_client.get(reverse("production:qc_detail", kwargs={"batch_pk": self.batch.pk}))
        self.assertEqual(response.status_code, 200)

    def test_qc_redirect_if_exists(self):
        QualityControl.objects.create(
            batch=self.batch,
            appearance="OK",
            passed=True,
            performed_by=self.pharmacist,
        )
        response = self.test_client.get(reverse("production:qc_create", kwargs={"batch_pk": self.batch.pk}))
        self.assertEqual(response.status_code, 302)  # Redirects to detail


class BatchApprovalEnforcementTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Approval View Pharmacy", slug="prod-views-approval")
        self.pharmacist_user = User.objects.create_user(username="approver", password="test1234")
        UserProfile.objects.create(
            user=self.pharmacist_user,
            role=UserProfile.Role.PHARMACIST,
            pharmacy=self.pharmacy,
        )
        self.labtech_user = User.objects.create_user(username="labtech2", password="test1234")
        UserProfile.objects.create(
            user=self.labtech_user,
            role=UserProfile.Role.LAB_TECHNICIAN,
            pharmacy=self.pharmacy,
        )
        client_obj = Client.objects.create(
            name="Approval Client",
            nif="111222334",
            pharmacy=self.pharmacy,
        )
        order = Order.objects.create(client=client_obj, pharmacy=self.pharmacy)
        formulation = Formulation.objects.create(
            code="F-APP",
            name="Approval Test",
            pharmaceutical_form="capsule",
            pharmacy=self.pharmacy,
        )
        self.batch = ProductionBatch.objects.create(
            order=order,
            formulation=formulation,
            pharmacy=self.pharmacy,
        )
        # Move to quality_check state
        self.batch.start()
        self.batch.send_to_quality()
        self.batch.save()

    def test_approve_requires_pharmacist(self):
        """Lab technician should NOT be able to approve."""
        # Create passing QC
        QualityControl.objects.create(
            batch=self.batch,
            appearance="OK",
            passed=True,
            performed_by=self.labtech_user,
        )
        test_client = TestClient()
        test_client.login(username="labtech2", password="test1234")
        response = test_client.get(
            reverse("production:batch_status_update", kwargs={"pk": self.batch.pk, "action": "approve"})
        )
        self.assertEqual(response.status_code, 302)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, ProductionBatch.Status.QUALITY_CHECK)  # Not approved

    def test_approve_requires_qc_passed(self):
        """Pharmacist should NOT approve without passing QC."""
        test_client = TestClient()
        test_client.login(username="approver", password="test1234")
        response = test_client.get(
            reverse("production:batch_status_update", kwargs={"pk": self.batch.pk, "action": "approve"})
        )
        self.assertEqual(response.status_code, 302)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, ProductionBatch.Status.QUALITY_CHECK)  # Still not approved

    def test_approve_with_pharmacist_and_qc(self):
        """Pharmacist WITH passing QC should approve successfully."""
        QualityControl.objects.create(
            batch=self.batch,
            appearance="OK",
            passed=True,
            performed_by=self.pharmacist_user,
        )
        test_client = TestClient()
        test_client.login(username="approver", password="test1234")
        response = test_client.get(
            reverse("production:batch_status_update", kwargs={"pk": self.batch.pk, "action": "approve"})
        )
        self.assertEqual(response.status_code, 302)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, ProductionBatch.Status.APPROVED)
        self.assertEqual(self.batch.verified_by, self.pharmacist_user)


class BatchLabelViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="Label View Pharmacy", slug="prod-views-label")
        self.user = User.objects.create_user(username="label_pharmacist", password="test1234")
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.PHARMACIST,
            pharmacy=self.pharmacy,
        )
        self.test_client.login(username="label_pharmacist", password="test1234")
        client_obj = Client.objects.create(
            name="Label Client",
            nif="555666777",
            pharmacy=self.pharmacy,
        )
        order = Order.objects.create(client=client_obj, pharmacy=self.pharmacy)
        formulation = Formulation.objects.create(
            code="F-LBL",
            name="Label Test",
            pharmaceutical_form="cream",
            route_of_administration="topical",
            pharmacy=self.pharmacy,
        )
        self.batch = ProductionBatch.objects.create(
            order=order,
            formulation=formulation,
            pharmacy=self.pharmacy,
        )

    def test_batch_label_returns_html_and_sets_timestamp(self):
        self.assertIsNone(self.batch.label_generated_at)
        response = self.test_client.get(reverse("production:batch_label", kwargs={"pk": self.batch.pk}))
        self.assertEqual(response.status_code, 200)
        self.batch.refresh_from_db()
        self.assertIsNotNone(self.batch.label_generated_at)
