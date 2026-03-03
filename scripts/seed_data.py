"""
Seed development data for all apps.
Run with: python manage.py shell < scripts/seed_data.py
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User

from apps.core.models import UserProfile
from apps.inventory.models import Lot, RawMaterial, Supplier
from apps.inventory.services import StockService
from apps.orders.models import Client
from apps.production.models import (
    Formulation,
    FormulationIngredient,
    FormulationStep,
)

# --- Users ---
USERS = [
    {"email": "maria.silva@compoundmeds.local", "first_name": "Maria", "last_name": "Silva", "role": "pharmacist"},
    {"email": "joao.santos@compoundmeds.local", "first_name": "Joao", "last_name": "Santos", "role": "lab_technician"},
    {"email": "ana.costa@compoundmeds.local", "first_name": "Ana", "last_name": "Costa", "role": "front_desk"},
    {"email": "pedro.oliveira@compoundmeds.local", "first_name": "Pedro", "last_name": "Oliveira", "role": "viewer"},
]

for data in USERS:
    role = data.pop("role")
    email = data["email"]
    if not User.objects.filter(email=email).exists():
        user = User.objects.create_user(
            username=email,
            password="test1234",
            **data,
        )
        UserProfile.objects.create(user=user, role=role)
        print(f"Created user '{email}' with role '{role}'")
    else:
        print(f"User '{email}' already exists")

# --- Clients ---
CLIENTS = [
    {"name": "Farmacia Central", "nif": "501234567", "client_type": "pharmacy", "phone": "210000001"},
    {"name": "Farmacia do Rossio", "nif": "501234568", "client_type": "pharmacy", "phone": "210000002"},
    {"name": "Hospital S. Jose", "nif": "502345678", "client_type": "institution", "phone": "213000001"},
    {"name": "Manuel Ferreira", "nif": "123456789", "client_type": "individual", "phone": "910000001"},
]

for data in CLIENTS:
    obj, created = Client.objects.get_or_create(nif=data["nif"], defaults=data)
    print(f"{'Created' if created else 'Exists'} client '{obj.name}'")

# --- Suppliers ---
SUPPLIERS = [
    {"name": "ChemSupply Lda", "nif": "500100200", "email": "info@chemsupply.pt"},
    {"name": "PharmaRaw SA", "nif": "500100201", "email": "orders@pharmaraw.pt"},
    {"name": "BioIngredients", "nif": "500100202", "email": "sales@bioingredients.pt"},
]

suppliers = {}
for data in SUPPLIERS:
    obj, created = Supplier.objects.get_or_create(nif=data["nif"], defaults=data)
    suppliers[obj.nif] = obj
    print(f"{'Created' if created else 'Exists'} supplier '{obj.name}'")

# --- Raw Materials ---
MATERIALS = [
    {"code": "RM-001", "name": "Paracetamol", "default_unit": "g", "minimum_stock": 500, "supplier_nif": "500100200"},
    {
        "code": "RM-002",
        "name": "Lactose Monohydrate",
        "default_unit": "g",
        "minimum_stock": 1000,
        "supplier_nif": "500100200",
    },
    {"code": "RM-003", "name": "Ibuprofeno", "default_unit": "g", "minimum_stock": 300, "supplier_nif": "500100201"},
    {
        "code": "RM-004",
        "name": "Acido Salicilico",
        "default_unit": "g",
        "minimum_stock": 200,
        "supplier_nif": "500100201",
    },
    {"code": "RM-005", "name": "Vaselina", "default_unit": "g", "minimum_stock": 500, "supplier_nif": "500100202"},
    {"code": "RM-006", "name": "Glicerina", "default_unit": "mL", "minimum_stock": 1000, "supplier_nif": "500100202"},
    {
        "code": "RM-007",
        "name": "Agua Purificada",
        "default_unit": "mL",
        "minimum_stock": 5000,
        "supplier_nif": "500100200",
    },
]

materials = {}
for data in MATERIALS:
    supplier_nif = data.pop("supplier_nif")
    obj, created = RawMaterial.objects.get_or_create(
        code=data["code"],
        defaults={**data, "preferred_supplier": suppliers[supplier_nif]},
    )
    materials[obj.code] = obj
    print(f"{'Created' if created else 'Exists'} material '{obj.name}'")

# --- Lots ---
today = date.today()
LOTS = [
    {"material": "RM-001", "lot_number": "LOT-P001", "supplier_nif": "500100200", "qty": 2000, "days_exp": 365},
    {"material": "RM-002", "lot_number": "LOT-E001", "supplier_nif": "500100200", "qty": 5000, "days_exp": 365},
    {"material": "RM-003", "lot_number": "LOT-I001", "supplier_nif": "500100201", "qty": 1000, "days_exp": 300},
    {"material": "RM-004", "lot_number": "LOT-S001", "supplier_nif": "500100201", "qty": 500, "days_exp": 180},
    {"material": "RM-005", "lot_number": "LOT-V001", "supplier_nif": "500100202", "qty": 3000, "days_exp": 730},
    {"material": "RM-006", "lot_number": "LOT-G001", "supplier_nif": "500100202", "qty": 5000, "days_exp": 365},
    {"material": "RM-007", "lot_number": "LOT-A001", "supplier_nif": "500100200", "qty": 10000, "days_exp": 180},
]

for data in LOTS:
    if not Lot.objects.filter(lot_number=data["lot_number"]).exists():
        lot = Lot.objects.create(
            raw_material=materials[data["material"]],
            lot_number=data["lot_number"],
            supplier=suppliers[data["supplier_nif"]],
            initial_quantity=data["qty"],
            current_quantity=data["qty"],
            received_date=today - timedelta(days=15),
            expiry_date=today + timedelta(days=data["days_exp"]),
        )
        StockService.receive_stock(lot)
        print(f"Created lot '{lot.lot_number}'")
    else:
        print(f"Lot '{data['lot_number']}' already exists")

# --- Formulations ---
if not Formulation.objects.filter(code="FORM-001").exists():
    f1 = Formulation.objects.create(
        code="FORM-001",
        name="Paracetamol Capsules 500mg",
        pharmaceutical_form="capsule",
        shelf_life_days=180,
    )
    FormulationIngredient.objects.create(
        formulation=f1,
        raw_material=materials["RM-001"],
        quantity=Decimal("500"),
        unit="mg",
        is_active_ingredient=True,
        order_of_addition=1,
    )
    FormulationIngredient.objects.create(
        formulation=f1,
        raw_material=materials["RM-002"],
        quantity=Decimal("200"),
        unit="mg",
        is_active_ingredient=False,
        order_of_addition=2,
    )
    FormulationStep.objects.create(
        formulation=f1,
        step_number=1,
        title="Pesar ingredientes",
        description="Pesar paracetamol e lactose com precisao.",
    )
    FormulationStep.objects.create(
        formulation=f1,
        step_number=2,
        title="Misturar e encapsular",
        description="Misturar ingredientes e preencher capsulas.",
    )
    print("Created formulation 'FORM-001'")

if not Formulation.objects.filter(code="FORM-002").exists():
    f2 = Formulation.objects.create(
        code="FORM-002",
        name="Pomada de Acido Salicilico 5%",
        pharmaceutical_form="ointment",
        shelf_life_days=90,
        storage_conditions="Conservar abaixo de 25C",
    )
    FormulationIngredient.objects.create(
        formulation=f2,
        raw_material=materials["RM-004"],
        quantity=Decimal("5"),
        unit="g",
        is_active_ingredient=True,
        order_of_addition=1,
    )
    FormulationIngredient.objects.create(
        formulation=f2,
        raw_material=materials["RM-005"],
        quantity=Decimal("95"),
        unit="g",
        is_active_ingredient=False,
        order_of_addition=2,
    )
    FormulationStep.objects.create(
        formulation=f2,
        step_number=1,
        title="Pesar componentes",
        description="Pesar acido salicilico e vaselina.",
    )
    FormulationStep.objects.create(
        formulation=f2,
        step_number=2,
        title="Incorporar e homogeneizar",
        description="Incorporar acido salicilico na vaselina e homogeneizar.",
    )
    print("Created formulation 'FORM-002'")

print("\nSeed data complete.")
