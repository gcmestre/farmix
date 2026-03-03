import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from apps.core.decorators import role_required

from .forms import (
    InvoiceForm,
    InvoiceLineForm,
    QuoteForm,
    QuoteLineForm,
    QuoteToInvoiceForm,
)
from .models import Invoice, InvoiceLine, Quote

# --- Quotes ---


@login_required
def quote_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    quotes = Quote.objects.select_related("order", "client").all()
    if pharmacy:
        quotes = quotes.filter(pharmacy=pharmacy)
    return render(
        request,
        "invoicing/quote_list.html",
        {
            "quotes": quotes,
            "title": _("Quotes"),
        },
    )


@login_required
def quote_detail(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Quote.objects.select_related("order", "client").all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    quote = get_object_or_404(qs, pk=pk)
    lines = quote.lines.all()
    return render(
        request,
        "invoicing/quote_detail.html",
        {
            "quote": quote,
            "lines": lines,
            "title": f"Quote {quote.quote_number}",
        },
    )


@login_required
@role_required("admin", "pharmacist")
def quote_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = QuoteForm(request.POST, pharmacy=pharmacy)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.created_by = request.user
            quote.pharmacy = pharmacy
            quote.save()
            messages.success(request, _("Quote created."))
            return redirect("invoicing:quote_detail", pk=quote.pk)
    else:
        form = QuoteForm(pharmacy=pharmacy)
    return render(
        request,
        "invoicing/quote_form.html",
        {
            "form": form,
            "title": _("New Quote"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def quote_add_line(request, quote_pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Quote.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    quote = get_object_or_404(qs, pk=quote_pk)
    if request.method == "POST":
        form = QuoteLineForm(request.POST)
        if form.is_valid():
            line = form.save(commit=False)
            line.quote = quote
            line.save()
            messages.success(request, _("Line added."))
            return redirect("invoicing:quote_detail", pk=quote.pk)
    else:
        form = QuoteLineForm()
    return render(
        request,
        "invoicing/quote_line_form.html",
        {
            "form": form,
            "quote": quote,
            "title": _("Add Line"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def quote_to_invoice(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Quote.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    quote = get_object_or_404(qs, pk=pk)
    if request.method == "POST":
        form = QuoteToInvoiceForm(request.POST)
        if form.is_valid():
            invoice = Invoice.objects.create(
                order=quote.order,
                client=quote.client,
                due_date=form.cleaned_data["due_date"],
                created_by=request.user,
                pharmacy=pharmacy,
            )
            for line in quote.lines.all():
                InvoiceLine.objects.create(
                    invoice=invoice,
                    description=line.description,
                    quantity=line.quantity,
                    unit=line.unit,
                    unit_price=line.unit_price,
                    iva_rate=line.iva_rate,
                )
            messages.success(request, _("Invoice created from quote."))
            return redirect("invoicing:invoice_detail", pk=invoice.pk)
    else:
        form = QuoteToInvoiceForm()
    return render(
        request,
        "invoicing/quote_to_invoice.html",
        {
            "form": form,
            "quote": quote,
            "title": _("Convert to Invoice"),
        },
    )


# --- Invoices ---


@login_required
def invoice_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    invoices = Invoice.objects.select_related("order", "client").all()
    if pharmacy:
        invoices = invoices.filter(pharmacy=pharmacy)
    status_filter = request.GET.get("status", "")
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    return render(
        request,
        "invoicing/invoice_list.html",
        {
            "invoices": invoices,
            "status_choices": Invoice.Status.choices,
            "current_status": status_filter,
            "title": _("Invoices"),
        },
    )


@login_required
def invoice_detail(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Invoice.objects.select_related("order", "client").all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    invoice = get_object_or_404(qs, pk=pk)
    lines = invoice.lines.all()
    return render(
        request,
        "invoicing/invoice_detail.html",
        {
            "invoice": invoice,
            "lines": lines,
            "title": f"Invoice {invoice.invoice_number}",
        },
    )


@login_required
@role_required("admin", "pharmacist")
def invoice_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = InvoiceForm(request.POST, pharmacy=pharmacy)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.pharmacy = pharmacy
            invoice.save()
            messages.success(request, _("Invoice created."))
            return redirect("invoicing:invoice_detail", pk=invoice.pk)
    else:
        form = InvoiceForm(pharmacy=pharmacy)
    return render(
        request,
        "invoicing/invoice_form.html",
        {
            "form": form,
            "title": _("New Invoice"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def invoice_add_line(request, invoice_pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Invoice.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    invoice = get_object_or_404(qs, pk=invoice_pk)
    if request.method == "POST":
        form = InvoiceLineForm(request.POST)
        if form.is_valid():
            line = form.save(commit=False)
            line.invoice = invoice
            line.save()
            messages.success(request, _("Line added."))
            return redirect("invoicing:invoice_detail", pk=invoice.pk)
    else:
        form = InvoiceLineForm()
    return render(
        request,
        "invoicing/invoice_line_form.html",
        {
            "form": form,
            "invoice": invoice,
            "title": _("Add Line"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def invoice_status_update(request, pk, action):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Invoice.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    invoice = get_object_or_404(qs, pk=pk)
    action_map = {
        "send": invoice.send,
        "mark_paid": invoice.mark_paid,
        "mark_overdue": invoice.mark_overdue,
        "cancel": invoice.cancel,
    }
    transition_fn = action_map.get(action)
    if transition_fn:
        transition_fn()
        invoice.save()
        messages.success(request, _("Invoice status updated."))
    else:
        messages.error(request, _("Invalid action."))
    return redirect("invoicing:invoice_detail", pk=invoice.pk)


@login_required
@role_required("admin", "pharmacist")
def invoice_export_csv(request):
    """Export invoices list as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="invoices.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "Invoice Number",
            "Client",
            "Order",
            "Status",
            "Due Date",
            "Total",
            "Total with IVA",
            "Created",
        ]
    )
    pharmacy = getattr(request, "pharmacy", None)
    invoices = Invoice.objects.select_related("order", "client").all()
    if pharmacy:
        invoices = invoices.filter(pharmacy=pharmacy)
    for inv in invoices:
        writer.writerow(
            [
                inv.invoice_number,
                inv.client.name,
                inv.order.order_number,
                inv.get_status_display(),
                inv.due_date or "",
                inv.total,
                inv.total_with_iva,
                inv.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )
    return response
