from decimal import Decimal

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.inventory.models import RawMaterial
from apps.orders.models import Order

from .models import (
    BatchCost,
    EquipmentCalibration,
    Formulation,
    FormulationIngredient,
    FormulationStep,
    Prescription,
    ProductionBatch,
    ProductionStepLog,
    QualityControl,
)


class FormulationForm(forms.ModelForm):
    class Meta:
        model = Formulation
        fields = [
            "code",
            "name",
            "pharmaceutical_form",
            "route_of_administration",
            "dosage_instructions",
            "is_multi_stage",
            "shelf_life_days",
            "storage_conditions",
            "base_quantity",
            "base_unit",
            "notes",
        ]


class FormulationIngredientForm(forms.ModelForm):
    class Meta:
        model = FormulationIngredient
        fields = ["raw_material", "quantity", "unit", "is_active_ingredient", "order_of_addition"]

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pharmacy:
            self.fields["raw_material"].queryset = RawMaterial.objects.filter(pharmacy=pharmacy)


class FormulationStepForm(forms.ModelForm):
    class Meta:
        model = FormulationStep
        fields = ["step_number", "title", "description", "estimated_duration"]


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = [
            "doctor_name",
            "doctor_license",
            "patient_name",
            "patient_tax_number",
            "patient_address",
            "file",
        ]


class ProductionBatchForm(forms.ModelForm):
    class Meta:
        model = ProductionBatch
        fields = [
            "order",
            "formulation",
            "produced_by",
            "expiry_date",
            "quantity_produced",
            "unit",
            "storage_conditions",
            "special_precautions",
        ]

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pharmacy:
            self.fields["order"].queryset = Order.objects.filter(pharmacy=pharmacy)
            self.fields["formulation"].queryset = Formulation.objects.filter(pharmacy=pharmacy)


class StepCompletionForm(forms.ModelForm):
    class Meta:
        model = ProductionStepLog
        fields = ["observations", "parameters"]
        widgets = {
            "observations": forms.Textarea(attrs={"rows": 3}),
        }


class QualityControlForm(forms.ModelForm):
    class Meta:
        model = QualityControl
        fields = [
            "appearance",
            "odor",
            "texture",
            "ph_value",
            "expected_weight",
            "actual_weight",
            "passed",
            "observations",
        ]
        widgets = {
            "observations": forms.Textarea(attrs={"rows": 3}),
        }


class BatchCalculatorForm(forms.Form):
    desired_quantity = forms.DecimalField(
        label=_("Desired quantity"),
        min_value=Decimal("0.0001"),
        max_digits=10,
        decimal_places=3,
        widget=forms.NumberInput(attrs={"step": "0.001", "placeholder": "1000"}),
    )


class BatchCostForm(forms.ModelForm):
    class Meta:
        model = BatchCost
        fields = ["packaging_cost", "preparation_fee"]


class EquipmentCalibrationForm(forms.ModelForm):
    class Meta:
        model = EquipmentCalibration
        fields = [
            "equipment_name",
            "serial_number",
            "calibration_date",
            "next_calibration_date",
            "certificate_file",
            "observations",
        ]
        widgets = {
            "calibration_date": forms.DateInput(attrs={"type": "date"}),
            "next_calibration_date": forms.DateInput(attrs={"type": "date"}),
            "observations": forms.Textarea(attrs={"rows": 3}),
        }
