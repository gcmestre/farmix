from django import forms
from django.utils.translation import gettext_lazy as _

from apps.orders.models import Client, Order

from .models import Invoice, InvoiceLine, Quote, QuoteLine


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["order", "client", "valid_until", "notes"]
        widgets = {
            "valid_until": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pharmacy:
            self.fields["order"].queryset = Order.objects.filter(pharmacy=pharmacy)
            self.fields["client"].queryset = Client.objects.filter(pharmacy=pharmacy)


class QuoteLineForm(forms.ModelForm):
    class Meta:
        model = QuoteLine
        fields = ["description", "quantity", "unit", "unit_price", "iva_rate"]


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["order", "client", "due_date", "notes"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pharmacy:
            self.fields["order"].queryset = Order.objects.filter(pharmacy=pharmacy)
            self.fields["client"].queryset = Client.objects.filter(pharmacy=pharmacy)


class InvoiceLineForm(forms.ModelForm):
    class Meta:
        model = InvoiceLine
        fields = ["description", "quantity", "unit", "unit_price", "iva_rate"]


class QuoteToInvoiceForm(forms.Form):
    due_date = forms.DateField(
        label=_("Due Date"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
