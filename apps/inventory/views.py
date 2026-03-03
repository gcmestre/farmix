import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from apps.core.decorators import role_required

from .forms import LotForm, ProhibitedSubstanceForm, RawMaterialForm, StockAdjustmentForm, SupplierForm
from .models import Lot, ProhibitedSubstance, RawMaterial, StockMovement, Supplier
from .services import AlertService, StockService


@login_required
def material_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    materials = RawMaterial.objects.select_related("preferred_supplier").all()
    if pharmacy:
        materials = materials.filter(pharmacy=pharmacy)
    search = request.GET.get("q", "")
    if search:
        materials = materials.filter(name__icontains=search) | materials.filter(code__icontains=search)
    return render(
        request,
        "inventory/material_list.html",
        {
            "materials": materials,
            "search": search,
            "title": _("Raw Materials"),
        },
    )


@login_required
def material_detail(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = RawMaterial.objects.select_related("preferred_supplier").all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    material = get_object_or_404(qs, pk=pk)
    lots = material.lots.select_related("supplier").filter(is_exhausted=False)
    movements = (
        StockMovement.objects.filter(lot__raw_material=material)
        .select_related("lot", "performed_by")
        .order_by("-timestamp")[:20]
    )
    return render(
        request,
        "inventory/material_detail.html",
        {
            "material": material,
            "lots": lots,
            "movements": movements,
            "title": material.name,
        },
    )


@login_required
@role_required("admin", "pharmacist")
def material_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = RawMaterialForm(request.POST, pharmacy=pharmacy)
        if form.is_valid():
            material = form.save(commit=False)
            material.created_by = request.user
            material.pharmacy = pharmacy
            material.save()
            messages.success(request, _("Material created."))
            return redirect("inventory:material_detail", pk=material.pk)
    else:
        form = RawMaterialForm(pharmacy=pharmacy)
    return render(
        request,
        "inventory/material_form.html",
        {
            "form": form,
            "title": _("New Material"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def material_edit(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = RawMaterial.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    material = get_object_or_404(qs, pk=pk)
    if request.method == "POST":
        form = RawMaterialForm(request.POST, instance=material, pharmacy=pharmacy)
        if form.is_valid():
            form.save()
            messages.success(request, _("Material updated."))
            return redirect("inventory:material_detail", pk=material.pk)
    else:
        form = RawMaterialForm(instance=material, pharmacy=pharmacy)
    return render(
        request,
        "inventory/material_form.html",
        {
            "form": form,
            "material": material,
            "title": _("Edit Material"),
        },
    )


@login_required
def lot_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    lots = Lot.objects.select_related("raw_material", "supplier").all()
    if pharmacy:
        lots = lots.filter(raw_material__pharmacy=pharmacy)
    status_filter = request.GET.get("status", "")
    if status_filter == "quarantined":
        lots = lots.filter(is_quarantined=True)
    elif status_filter == "exhausted":
        lots = lots.filter(is_exhausted=True)
    elif status_filter == "active":
        lots = lots.filter(is_exhausted=False, is_quarantined=False)
    return render(
        request,
        "inventory/lot_list.html",
        {
            "lots": lots,
            "current_status": status_filter,
            "title": _("Lots"),
        },
    )


@login_required
def lot_detail(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Lot.objects.select_related("raw_material", "supplier").all()
    if pharmacy:
        qs = qs.filter(raw_material__pharmacy=pharmacy)
    lot = get_object_or_404(qs, pk=pk)
    movements = lot.movements.select_related("performed_by").all()
    return render(
        request,
        "inventory/lot_detail.html",
        {
            "lot": lot,
            "movements": movements,
            "title": f"Lot {lot.lot_number}",
        },
    )


@login_required
@role_required("admin", "pharmacist", "lab_technician")
def lot_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = LotForm(request.POST, request.FILES, pharmacy=pharmacy)
        if form.is_valid():
            lot = form.save(commit=False)
            lot.created_by = request.user
            lot.save()
            StockService.receive_stock(lot, user=request.user)
            messages.success(request, _("Lot received."))
            return redirect("inventory:lot_detail", pk=lot.pk)
    else:
        form = LotForm(pharmacy=pharmacy)
    return render(
        request,
        "inventory/lot_form.html",
        {
            "form": form,
            "title": _("Receive Lot"),
        },
    )


@login_required
@role_required("admin", "pharmacist", "lab_technician")
def lot_adjust(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Lot.objects.all()
    if pharmacy:
        qs = qs.filter(raw_material__pharmacy=pharmacy)
    lot = get_object_or_404(qs, pk=pk)
    if request.method == "POST":
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            StockService.adjust_stock(
                lot,
                form.cleaned_data["quantity"],
                user=request.user,
                notes=form.cleaned_data.get("notes", ""),
            )
            messages.success(request, _("Stock adjusted."))
            return redirect("inventory:lot_detail", pk=lot.pk)
    else:
        form = StockAdjustmentForm()
    return render(
        request,
        "inventory/lot_adjust.html",
        {
            "form": form,
            "lot": lot,
            "title": _("Adjust Stock"),
        },
    )


@login_required
def supplier_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    suppliers = Supplier.objects.all()
    if pharmacy:
        suppliers = suppliers.filter(pharmacy=pharmacy)
    search = request.GET.get("q", "")
    if search:
        suppliers = suppliers.filter(name__icontains=search)
    return render(
        request,
        "inventory/supplier_list.html",
        {
            "suppliers": suppliers,
            "search": search,
            "title": _("Suppliers"),
        },
    )


@login_required
def supplier_detail(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Supplier.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    supplier = get_object_or_404(qs, pk=pk)
    lots = supplier.lots.select_related("raw_material").all()[:20]
    return render(
        request,
        "inventory/supplier_detail.html",
        {
            "supplier": supplier,
            "lots": lots,
            "title": supplier.name,
        },
    )


@login_required
@role_required("admin", "pharmacist")
def supplier_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.pharmacy = pharmacy
            supplier.save()
            messages.success(request, _("Supplier created."))
            return redirect("inventory:supplier_detail", pk=supplier.pk)
    else:
        form = SupplierForm()
    return render(
        request,
        "inventory/supplier_form.html",
        {
            "form": form,
            "title": _("New Supplier"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def supplier_edit(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Supplier.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    supplier = get_object_or_404(qs, pk=pk)
    if request.method == "POST":
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, _("Supplier updated."))
            return redirect("inventory:supplier_detail", pk=supplier.pk)
    else:
        form = SupplierForm(instance=supplier)
    return render(
        request,
        "inventory/supplier_form.html",
        {
            "form": form,
            "supplier": supplier,
            "title": _("Edit Supplier"),
        },
    )


@login_required
def alerts(request):
    pharmacy = getattr(request, "pharmacy", None)
    low_stock = AlertService.get_low_stock_materials(pharmacy=pharmacy)
    expiring = AlertService.get_expiring_lots(pharmacy=pharmacy, days=30)
    expired = AlertService.get_expired_lots(pharmacy=pharmacy)
    return render(
        request,
        "inventory/alerts.html",
        {
            "low_stock": low_stock,
            "expiring": expiring,
            "expired": expired,
            "title": _("Inventory Alerts"),
        },
    )


@login_required
def movements(request):
    pharmacy = getattr(request, "pharmacy", None)
    movement_list = StockMovement.objects.select_related("lot__raw_material", "performed_by", "reference_batch").all()
    if pharmacy:
        movement_list = movement_list.filter(lot__raw_material__pharmacy=pharmacy)
    movement_list = movement_list[:50]
    return render(
        request,
        "inventory/movements.html",
        {
            "movements": movement_list,
            "title": _("Stock Movements"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def inventory_export_csv(request):
    """Export raw materials inventory as CSV."""
    pharmacy = getattr(request, "pharmacy", None)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="inventory.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "Code",
            "Name",
            "Unit",
            "Current Stock",
            "Minimum Stock",
            "Reorder Point",
            "Preferred Supplier",
            "Is Controlled",
            "Low Stock",
        ]
    )
    materials = RawMaterial.objects.select_related("preferred_supplier").all()
    if pharmacy:
        materials = materials.filter(pharmacy=pharmacy)
    for m in materials:
        writer.writerow(
            [
                m.code,
                m.name,
                m.default_unit,
                m.current_stock,
                m.minimum_stock,
                m.reorder_point,
                m.preferred_supplier.name if m.preferred_supplier else "",
                "Yes" if m.is_controlled_substance else "No",
                "Yes" if m.is_low_stock else "No",
            ]
        )
    return response


@login_required
@role_required("admin", "pharmacist")
def prohibited_list(request):
    substances = ProhibitedSubstance.objects.all()
    return render(
        request,
        "inventory/prohibited_list.html",
        {
            "substances": substances,
            "title": _("Prohibited Substances"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def prohibited_create(request):
    if request.method == "POST":
        form = ProhibitedSubstanceForm(request.POST)
        if form.is_valid():
            substance = form.save(commit=False)
            substance.created_by = request.user
            substance.save()
            messages.success(request, _("Prohibited substance added."))
            return redirect("inventory:prohibited_list")
    else:
        form = ProhibitedSubstanceForm()
    return render(
        request,
        "inventory/prohibited_form.html",
        {
            "form": form,
            "title": _("Add Prohibited Substance"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def prohibited_edit(request, pk):
    substance = get_object_or_404(ProhibitedSubstance, pk=pk)
    if request.method == "POST":
        form = ProhibitedSubstanceForm(request.POST, instance=substance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Prohibited substance updated."))
            return redirect("inventory:prohibited_list")
    else:
        form = ProhibitedSubstanceForm(instance=substance)
    return render(
        request,
        "inventory/prohibited_form.html",
        {
            "form": form,
            "substance": substance,
            "title": _("Edit Prohibited Substance"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def prohibited_delete(request, pk):
    substance = get_object_or_404(ProhibitedSubstance, pk=pk)
    substance.soft_delete(user=request.user)
    messages.success(request, _("Prohibited substance removed."))
    return redirect("inventory:prohibited_list")


@login_required
@role_required("admin", "pharmacist")
def lot_release(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Lot.objects.all()
    if pharmacy:
        qs = qs.filter(raw_material__pharmacy=pharmacy)
    lot = get_object_or_404(qs, pk=pk)
    if not lot.is_quarantined:
        messages.info(request, _("This lot is not quarantined."))
        return redirect("inventory:lot_detail", pk=lot.pk)
    lot.is_quarantined = False
    lot.save(update_fields=["is_quarantined", "updated_at"])
    messages.success(request, _("Lot released from quarantine."))
    return redirect("inventory:lot_detail", pk=lot.pk)
