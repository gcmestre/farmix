import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from apps.core.decorators import role_required

from .filters import OrderFilter
from .forms import ClientForm, ComplaintForm, OrderForm, OrderItemForm, OrderStatusForm
from .models import Client, Complaint, Order
from .services import OrderWorkflowService


@login_required
def order_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Order.objects.select_related("client", "assigned_to")
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    f = OrderFilter(request.GET, queryset=qs)

    if request.htmx:
        return render(request, "orders/partials/_order_table.html", {"filter": f})

    return render(request, "orders/order_list.html", {"filter": f, "title": _("Orders")})


@login_required
def order_detail(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Order.objects.select_related("client", "assigned_to")
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    order = get_object_or_404(qs, pk=pk)
    items = order.items.all()
    order_total = sum(item.total_price for item in items)
    status_logs = order.status_logs.select_related("changed_by").all()
    available_transitions = []

    for t in order.get_available_status_transitions():
        for name, method in OrderWorkflowService.TRANSITION_MAP.items():
            if hasattr(method, "_django_fsm"):
                for key, ft in method._django_fsm.transitions.items():
                    if ft.target == t.target and order.status in (key if isinstance(key, (list, tuple)) else [key]):
                        available_transitions.append({"name": name, "label": t.target.replace("_", " ").title()})

    status_form = OrderStatusForm()

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "items": items,
            "order_total": order_total,
            "status_logs": status_logs,
            "available_transitions": available_transitions,
            "status_form": status_form,
            "title": f"Order {order.order_number}",
        },
    )


@login_required
@role_required("admin", "pharmacist", "front_desk")
def order_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = OrderForm(request.POST, request.FILES, pharmacy=pharmacy)
        if form.is_valid():
            order = form.save(commit=False)
            order.pharmacy = pharmacy
            order.created_by = request.user
            order.save()
            messages.success(request, _("Order created successfully."))
            return redirect("orders:order_detail", pk=order.pk)
    else:
        form = OrderForm(pharmacy=pharmacy)

    return render(request, "orders/order_form.html", {"form": form, "title": _("New Order")})


@login_required
@role_required("admin", "pharmacist", "front_desk")
def order_edit(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Order.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    order = get_object_or_404(qs, pk=pk)
    if request.method == "POST":
        form = OrderForm(request.POST, request.FILES, instance=order, pharmacy=pharmacy)
        if form.is_valid():
            order = form.save(commit=False)
            order.updated_by = request.user
            order.save()
            messages.success(request, _("Order updated successfully."))
            return redirect("orders:order_detail", pk=order.pk)
    else:
        form = OrderForm(instance=order, pharmacy=pharmacy)

    return render(request, "orders/order_form.html", {"form": form, "order": order, "title": _("Edit Order")})


@login_required
@role_required("admin", "pharmacist")
def order_status_update(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Order.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    order = get_object_or_404(qs, pk=pk)
    if request.method == "POST":
        form = OrderStatusForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            comment = form.cleaned_data.get("comment", "")
            try:
                OrderWorkflowService.transition(order, action, request.user, comment)
                messages.success(request, _("Order status updated."))
            except (ValueError, Exception) as e:
                messages.error(request, str(e))
    return redirect("orders:order_detail", pk=order.pk)


@login_required
@role_required("admin", "pharmacist", "front_desk")
def order_item_add(request, order_pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Order.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    order = get_object_or_404(qs, pk=order_pk)
    if request.method == "POST":
        form = OrderItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.order = order
            item.created_by = request.user
            item.save()
            if request.htmx:
                items = order.items.all()
                return render(request, "orders/partials/_order_items.html", {"items": items, "order": order})
            return redirect("orders:order_detail", pk=order.pk)
    else:
        form = OrderItemForm()

    return render(request, "orders/partials/_order_item_form.html", {"form": form, "order": order})


@login_required
def client_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    clients = Client.objects.all()
    if pharmacy:
        clients = clients.filter(pharmacy=pharmacy)
    search = request.GET.get("q", "")
    if search:
        clients = clients.filter(name__icontains=search) | clients.filter(nif__icontains=search)

    if request.htmx:
        return render(request, "orders/partials/_client_table.html", {"clients": clients})

    return render(request, "orders/client_list.html", {"clients": clients, "title": _("Clients")})


@login_required
def client_detail(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Client.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    client = get_object_or_404(qs, pk=pk)
    orders = client.orders.all()[:20]
    return render(
        request,
        "orders/client_detail.html",
        {
            "client": client,
            "orders": orders,
            "title": client.name,
        },
    )


@login_required
@role_required("admin", "pharmacist", "front_desk")
def client_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.pharmacy = pharmacy
            client.created_by = request.user
            client.save()
            messages.success(request, _("Client created successfully."))
            return redirect("orders:client_detail", pk=client.pk)
    else:
        form = ClientForm()

    return render(request, "orders/client_form.html", {"form": form, "title": _("New Client")})


@login_required
@role_required("admin", "pharmacist", "front_desk")
def client_edit(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Client.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    client = get_object_or_404(qs, pk=pk)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            client.updated_by = request.user
            client.save()
            messages.success(request, _("Client updated successfully."))
            return redirect("orders:client_detail", pk=client.pk)
    else:
        form = ClientForm(instance=client)

    return render(request, "orders/client_form.html", {"form": form, "client": client, "title": _("Edit Client")})


@login_required
def client_autocomplete(request):
    pharmacy = getattr(request, "pharmacy", None)
    q = request.GET.get("q", "")
    clients = Client.objects.none()
    if q:
        clients = Client.objects.filter(name__icontains=q)
        if pharmacy:
            clients = clients.filter(pharmacy=pharmacy)
        clients = clients[:10]
    results = [{"id": str(c.pk), "name": c.name, "nif": c.nif} for c in clients]
    return JsonResponse(results, safe=False)


@login_required
@role_required("admin", "pharmacist")
def order_export_csv(request):
    """Export orders list as CSV."""
    pharmacy = getattr(request, "pharmacy", None)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "Order Number",
            "Client",
            "Status",
            "Priority",
            "Source",
            "Assigned To",
            "Created",
        ]
    )
    orders = Order.objects.select_related("client", "assigned_to")
    if pharmacy:
        orders = orders.filter(pharmacy=pharmacy)
    for o in orders:
        writer.writerow(
            [
                o.order_number,
                o.client.name,
                o.get_status_display(),
                o.get_priority_display(),
                o.get_source_display(),
                o.assigned_to.get_full_name() if o.assigned_to else "",
                o.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )
    return response


@login_required
def complaint_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    complaints = Complaint.objects.select_related("order", "batch", "resolved_by").all()
    if pharmacy:
        complaints = complaints.filter(pharmacy=pharmacy)
    status_filter = request.GET.get("status", "")
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    return render(
        request,
        "orders/complaint_list.html",
        {
            "complaints": complaints,
            "status_choices": Complaint.Status.choices,
            "current_status": status_filter,
            "title": _("Complaints"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def complaint_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = ComplaintForm(request.POST, pharmacy=pharmacy)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.pharmacy = pharmacy
            complaint.created_by = request.user
            complaint.save()
            messages.success(request, _("Complaint recorded."))
            return redirect("orders:complaint_detail", pk=complaint.pk)
    else:
        form = ComplaintForm(pharmacy=pharmacy)
    return render(
        request,
        "orders/complaint_form.html",
        {
            "form": form,
            "title": _("New Complaint"),
        },
    )


@login_required
def complaint_detail(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Complaint.objects.select_related("order", "batch", "resolved_by")
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    complaint = get_object_or_404(qs, pk=pk)
    return render(
        request,
        "orders/complaint_detail.html",
        {
            "complaint": complaint,
            "title": _("Complaint Detail"),
        },
    )
