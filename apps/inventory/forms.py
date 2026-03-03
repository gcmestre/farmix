from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Lot, ProhibitedSubstance, RawMaterial, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "nif", "email", "phone", "address", "is_active", "notes"]


class RawMaterialForm(forms.ModelForm):
    class Meta:
        model = RawMaterial
        fields = [
            "code",
            "name",
            "cas_number",
            "default_unit",
            "minimum_stock",
            "reorder_point",
            "preferred_supplier",
            "is_controlled_substance",
            "pharmacopeia_reference",
            "notes",
        ]

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pharmacy:
            self.fields["preferred_supplier"].queryset = Supplier.objects.filter(pharmacy=pharmacy)


class LotForm(forms.ModelForm):
    class Meta:
        model = Lot
        fields = [
            "raw_material",
            "lot_number",
            "supplier",
            "initial_quantity",
            "current_quantity",
            "received_date",
            "expiry_date",
            "certificate_of_analysis",
            "cost_per_unit",
            "is_quarantined",
        ]
        widgets = {
            "received_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pharmacy:
            self.fields["raw_material"].queryset = RawMaterial.objects.filter(pharmacy=pharmacy)
            self.fields["supplier"].queryset = Supplier.objects.filter(pharmacy=pharmacy)


class StockAdjustmentForm(forms.Form):
    quantity = forms.DecimalField(
        label=_("Quantity"),
        max_digits=10,
        decimal_places=3,
        help_text=_("Positive to add, negative to subtract."),
    )
    notes = forms.CharField(
        label=_("Notes"),
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
    )


class ProhibitedSubstanceForm(forms.ModelForm):
    class Meta:
        model = ProhibitedSubstance
        fields = ["name", "cas_number", "regulation", "notes"]
