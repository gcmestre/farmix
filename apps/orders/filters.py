import django_filters
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Order

_input_css = "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"


class OrderFilter(django_filters.FilterSet):
    order_number = django_filters.CharFilter(
        lookup_expr="icontains",
        label=_("Order #"),
        widget=forms.TextInput(attrs={"class": _input_css, "placeholder": _("Order #")}),
    )
    client__name = django_filters.CharFilter(
        lookup_expr="icontains",
        label=_("Client"),
        widget=forms.TextInput(attrs={"class": _input_css, "placeholder": _("Client")}),
    )
    status = django_filters.ChoiceFilter(
        choices=Order.Status.choices,
        label=_("Status"),
        empty_label=_("All"),
        widget=forms.Select(attrs={"class": _input_css}),
    )
    priority = django_filters.ChoiceFilter(
        choices=Order.Priority.choices,
        label=_("Priority"),
        empty_label=_("All"),
        widget=forms.Select(attrs={"class": _input_css}),
    )

    class Meta:
        model = Order
        fields = ["order_number", "client__name", "status", "priority"]
