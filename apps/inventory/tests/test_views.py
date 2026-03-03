from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Pharmacy, UserProfile
from apps.inventory.models import Lot, ProhibitedSubstance, RawMaterial, Supplier


class MaterialViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="Material View Pharmacy", slug="inv-views-material")
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
        self.supplier = Supplier.objects.create(name="S", nif="111222333", pharmacy=self.pharmacy)

    def test_material_list(self):
        response = self.test_client.get(reverse("inventory:material_list"))
        self.assertEqual(response.status_code, 200)

    def test_material_create(self):
        response = self.test_client.post(
            reverse("inventory:material_create"),
            {
                "code": "RM-NEW",
                "name": "New Material",
                "default_unit": "g",
                "minimum_stock": "0.000",
                "reorder_point": "0.000",
                "is_controlled_substance": False,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(RawMaterial.objects.filter(code="RM-NEW").exists())

    def test_material_detail(self):
        m = RawMaterial.objects.create(
            code="RM-VW",
            name="View Test",
            default_unit="g",
            pharmacy=self.pharmacy,
        )
        response = self.test_client.get(reverse("inventory:material_detail", kwargs={"pk": m.pk}))
        self.assertEqual(response.status_code, 200)

    def test_material_edit(self):
        m = RawMaterial.objects.create(
            code="RM-ED",
            name="Edit Test",
            default_unit="g",
            minimum_stock=0,
            reorder_point=0,
            pharmacy=self.pharmacy,
        )
        response = self.test_client.post(
            reverse("inventory:material_edit", kwargs={"pk": m.pk}),
            {
                "code": "RM-ED",
                "name": "Updated",
                "default_unit": "g",
                "minimum_stock": "10.000",
                "reorder_point": "5.000",
                "is_controlled_substance": False,
            },
        )
        self.assertEqual(response.status_code, 302)
        m.refresh_from_db()
        self.assertEqual(m.name, "Updated")


class LotViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="Lot View Pharmacy", slug="inv-views-lot")
        self.user = User.objects.create_user(
            username="labtech",
            password="test1234",
        )
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.LAB_TECHNICIAN,
            pharmacy=self.pharmacy,
        )
        self.test_client.login(username="labtech", password="test1234")
        self.supplier = Supplier.objects.create(name="S", nif="444555666", pharmacy=self.pharmacy)
        self.material = RawMaterial.objects.create(
            code="RM-LOT",
            name="Lot Material",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )

    def test_lot_list(self):
        response = self.test_client.get(reverse("inventory:lot_list"))
        self.assertEqual(response.status_code, 200)

    def test_lot_create(self):
        response = self.test_client.post(
            reverse("inventory:lot_create"),
            {
                "raw_material": str(self.material.pk),
                "lot_number": "LOT-NEW",
                "supplier": str(self.supplier.pk),
                "initial_quantity": "500.000",
                "current_quantity": "500.000",
                "received_date": date.today().isoformat(),
                "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
                "is_quarantined": False,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Lot.objects.filter(lot_number="LOT-NEW").exists())

    def test_lot_detail(self):
        lot = Lot.objects.create(
            raw_material=self.material,
            lot_number="LOT-VW",
            supplier=self.supplier,
            initial_quantity=100,
            current_quantity=100,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=180),
        )
        response = self.test_client.get(reverse("inventory:lot_detail", kwargs={"pk": lot.pk}))
        self.assertEqual(response.status_code, 200)


class SupplierViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="Supplier View Pharmacy", slug="inv-views-supplier")
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

    def test_supplier_list(self):
        response = self.test_client.get(reverse("inventory:supplier_list"))
        self.assertEqual(response.status_code, 200)

    def test_supplier_create(self):
        response = self.test_client.post(
            reverse("inventory:supplier_create"),
            {
                "name": "New Supplier",
                "nif": "987654321",
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Supplier.objects.filter(nif="987654321").exists())

    def test_supplier_detail(self):
        s = Supplier.objects.create(name="View Supplier", nif="111000222", pharmacy=self.pharmacy)
        response = self.test_client.get(reverse("inventory:supplier_detail", kwargs={"pk": s.pk}))
        self.assertEqual(response.status_code, 200)


class AlertsViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="Alerts View Pharmacy", slug="inv-views-alerts")
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

    def test_alerts_page(self):
        response = self.test_client.get(reverse("inventory:alerts"))
        self.assertEqual(response.status_code, 200)

    def test_movements_page(self):
        response = self.test_client.get(reverse("inventory:movements"))
        self.assertEqual(response.status_code, 200)

    def test_viewer_cannot_create_material(self):
        response = self.test_client.get(reverse("inventory:material_create"))
        self.assertEqual(response.status_code, 403)


class ProhibitedSubstanceViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="Prohibited View Pharmacy", slug="inv-views-prohibited")
        self.user = User.objects.create_user(username="ps_pharmacist", password="test1234")
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.PHARMACIST, pharmacy=self.pharmacy)
        self.test_client.login(username="ps_pharmacist", password="test1234")

    def test_prohibited_list(self):
        response = self.test_client.get(reverse("inventory:prohibited_list"))
        self.assertEqual(response.status_code, 200)

    def test_prohibited_create(self):
        response = self.test_client.post(
            reverse("inventory:prohibited_create"),
            {
                "name": "Phenylbutazone",
                "cas_number": "50-33-9",
                "regulation": "Deliberação 1985/2015",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProhibitedSubstance.objects.filter(name="Phenylbutazone").exists())

    def test_prohibited_edit(self):
        ps = ProhibitedSubstance.objects.create(name="Test Sub", cas_number="123-45-6")
        response = self.test_client.post(
            reverse("inventory:prohibited_edit", kwargs={"pk": ps.pk}),
            {
                "name": "Updated Sub",
                "cas_number": "123-45-6",
                "regulation": "Deliberação 1985/2015",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        ps.refresh_from_db()
        self.assertEqual(ps.name, "Updated Sub")

    def test_prohibited_delete(self):
        ps = ProhibitedSubstance.objects.create(name="Del Sub", cas_number="111-22-3")
        response = self.test_client.get(reverse("inventory:prohibited_delete", kwargs={"pk": ps.pk}))
        self.assertEqual(response.status_code, 302)
        ps.refresh_from_db()
        self.assertTrue(ps.is_deleted)


class LotReleaseViewTest(TestCase):
    def setUp(self):
        self.test_client = TestClient()
        self.pharmacy = Pharmacy.objects.create(name="Lot Release View Pharmacy", slug="inv-views-release")
        self.user = User.objects.create_user(username="release_pharmacist", password="test1234")
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.PHARMACIST, pharmacy=self.pharmacy)
        self.test_client.login(username="release_pharmacist", password="test1234")
        supplier = Supplier.objects.create(name="Rel Supplier", nif="444555667", pharmacy=self.pharmacy)
        material = RawMaterial.objects.create(
            code="RM-REL",
            name="Release Mat",
            default_unit="g",
            pharmacy=self.pharmacy,
        )
        self.lot = Lot.objects.create(
            raw_material=material,
            lot_number="LOT-REL-01",
            supplier=supplier,
            initial_quantity=100,
            current_quantity=100,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            is_quarantined=True,
        )

    def test_lot_release_from_quarantine(self):
        self.assertTrue(self.lot.is_quarantined)
        response = self.test_client.get(reverse("inventory:lot_release", kwargs={"pk": self.lot.pk}))
        self.assertEqual(response.status_code, 302)
        self.lot.refresh_from_db()
        self.assertFalse(self.lot.is_quarantined)

    def test_lot_release_non_quarantined(self):
        self.lot.is_quarantined = False
        self.lot.save()
        response = self.test_client.get(reverse("inventory:lot_release", kwargs={"pk": self.lot.pk}))
        self.assertEqual(response.status_code, 302)  # Redirects with info message
