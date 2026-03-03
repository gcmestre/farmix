from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import Client, Complaint, Order, OrderItem


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["client_type", "name", "nif", "infarmed_code", "email", "phone", "notes"]


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["client", "source", "priority", "assigned_to", "prescription_file", "notes"]

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pharmacy:
            self.fields["client"].queryset = Client.objects.filter(pharmacy=pharmacy)
            self.fields["assigned_to"].queryset = User.objects.filter(userprofile__pharmacy=pharmacy)
        else:
            self.fields["client"].queryset = Client.objects.all()


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ["description", "quantity", "unit", "unit_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit_price"].required = False


class OrderStatusForm(forms.Form):
    action = forms.CharField(widget=forms.HiddenInput())
    comment = forms.CharField(
        label=_("Comment"),
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
    )


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = [
            "order",
            "batch",
            "complainant_name",
            "complaint_date",
            "description",
            "investigation",
            "corrective_action",
            "status",
        ]
        widgets = {
            "complaint_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "investigation": forms.Textarea(attrs={"rows": 3}),
            "corrective_action": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pharmacy:
            self.fields["order"].queryset = Order.objects.filter(pharmacy=pharmacy)
            from apps.production.models import ProductionBatch

            self.fields["batch"].queryset = ProductionBatch.objects.filter(pharmacy=pharmacy)
        self.fields["order"].required = False
        self.fields["batch"].required = False
