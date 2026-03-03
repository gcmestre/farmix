from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.decorators import role_required
from apps.inventory.services import ProhibitedSubstanceService

from .forms import (
    BatchCalculatorForm,
    BatchCostForm,
    EquipmentCalibrationForm,
    FormulationForm,
    FormulationIngredientForm,
    FormulationStepForm,
    ProductionBatchForm,
    QualityControlForm,
    StepCompletionForm,
)
from .models import BatchCost, EquipmentCalibration, Formulation, FormulationStep, ProductionBatch, QualityControl
from .services import BatchCalculatorService, BatchCostService


@login_required
def batch_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    batches = ProductionBatch.objects.select_related("order", "formulation", "produced_by").all()
    if pharmacy:
        batches = batches.filter(pharmacy=pharmacy)
    status_filter = request.GET.get("status", "")
    if status_filter:
        batches = batches.filter(status=status_filter)
    return render(
        request,
        "production/batch_list.html",
        {
            "batches": batches,
            "status_choices": ProductionBatch.Status.choices,
            "current_status": status_filter,
            "title": _("Production Batches"),
        },
    )


@login_required
def batch_detail(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = ProductionBatch.objects.select_related("order", "formulation", "produced_by", "verified_by")
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    batch = get_object_or_404(qs, pk=pk)
    step_logs = batch.step_logs.select_related("step", "performed_by").all()
    material_usage = batch.material_usage.select_related("lot__raw_material").all()
    formulation_steps = batch.formulation.steps.all()

    completed_step_ids = set(step_logs.values_list("step_id", flat=True))
    steps_with_status = []
    for step in formulation_steps:
        steps_with_status.append(
            {
                "step": step,
                "completed": step.pk in completed_step_ids,
                "log": next((sl for sl in step_logs if sl.step_id == step.pk), None),
            }
        )

    # QC record
    qc = getattr(batch, "quality_control", None)
    try:
        qc = batch.quality_control
    except QualityControl.DoesNotExist:
        qc = None

    # Cost record
    try:
        cost = batch.cost
    except BatchCost.DoesNotExist:
        cost = None

    # Prohibited substance check
    violations = ProhibitedSubstanceService.check_formulation(batch.formulation)

    return render(
        request,
        "production/batch_detail.html",
        {
            "batch": batch,
            "steps_with_status": steps_with_status,
            "material_usage": material_usage,
            "qc": qc,
            "cost": cost,
            "violations": violations,
            "title": f"Batch {batch.batch_number}",
        },
    )


@login_required
@role_required("admin", "pharmacist", "lab_technician")
def batch_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = ProductionBatchForm(request.POST, pharmacy=pharmacy)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.created_by = request.user
            batch.pharmacy = pharmacy
            batch.save()
            messages.success(request, _("Batch created successfully."))
            return redirect("production:batch_detail", pk=batch.pk)
    else:
        form = ProductionBatchForm(pharmacy=pharmacy)
    return render(request, "production/batch_form.html", {"form": form, "title": _("New Batch")})


@login_required
@role_required("admin", "pharmacist", "lab_technician")
def batch_step_complete(request, batch_pk, step_pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = ProductionBatch.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    batch = get_object_or_404(qs, pk=batch_pk)
    step = get_object_or_404(FormulationStep, pk=step_pk)

    if request.method == "POST":
        form = StepCompletionForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.batch = batch
            log.step = step
            log.performed_by = request.user
            log.started_at = timezone.now()
            log.completed_at = timezone.now()
            log.save()
            if batch.status == ProductionBatch.Status.PLANNED:
                batch.start()
                batch.save()
            messages.success(request, _("Step completed."))
            return redirect("production:batch_detail", pk=batch.pk)
    else:
        form = StepCompletionForm()
    return render(
        request,
        "production/partials/_step_complete_form.html",
        {
            "form": form,
            "batch": batch,
            "step": step,
        },
    )


@login_required
@role_required("admin", "pharmacist", "lab_technician")
def batch_status_update(request, pk, action):
    pharmacy = getattr(request, "pharmacy", None)
    qs = ProductionBatch.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    batch = get_object_or_404(qs, pk=pk)

    # Enforce pharmacist role for approval (Portaria 594/2004)
    if action == "approve":
        is_pharmacist = request.user.is_superuser
        if not is_pharmacist:
            try:
                is_pharmacist = request.user.userprofile.role in ("admin", "pharmacist")
            except Exception:
                is_pharmacist = False
        if not is_pharmacist:
            messages.error(request, _("Only a pharmacist can approve a batch."))
            return redirect("production:batch_detail", pk=batch.pk)

        # Require passing QC before approval
        try:
            qc = batch.quality_control
            if not qc.passed:
                messages.error(request, _("Quality control must pass before approval."))
                return redirect("production:batch_detail", pk=batch.pk)
        except QualityControl.DoesNotExist:
            messages.error(request, _("Quality control record is required before approval."))
            return redirect("production:batch_detail", pk=batch.pk)

        batch.verified_by = request.user

    action_map = {
        "start": batch.start,
        "send_to_quality": batch.send_to_quality,
        "approve": batch.approve,
        "reject": batch.reject,
        "complete": batch.complete,
    }
    transition_fn = action_map.get(action)
    if transition_fn:
        transition_fn()
        batch.save()
        messages.success(request, _("Batch status updated."))
    else:
        messages.error(request, _("Invalid action."))
    return redirect("production:batch_detail", pk=batch.pk)


@login_required
@role_required("admin", "pharmacist")
def batch_pdf(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = ProductionBatch.objects.select_related("order", "formulation", "produced_by", "verified_by")
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    batch = get_object_or_404(qs, pk=pk)
    step_logs = batch.step_logs.select_related("step", "performed_by").all()
    material_usage = batch.material_usage.select_related("lot__raw_material", "lot__supplier").all()

    # Prescription info
    prescription = batch.order.prescriptions.first()

    # QC record
    try:
        qc = batch.quality_control
    except QualityControl.DoesNotExist:
        qc = None

    # Cost record
    try:
        cost = batch.cost
    except BatchCost.DoesNotExist:
        cost = None

    ph = pharmacy or batch.pharmacy
    html = render_to_string(
        "production/pdf/batch_report.html",
        {
            "batch": batch,
            "step_logs": step_logs,
            "material_usage": material_usage,
            "prescription": prescription,
            "qc": qc,
            "cost": cost,
            "pharmacy_name": getattr(ph, "name", ""),
            "pharmacy_anf_number": getattr(ph, "anf_number", ""),
            "pharmacy_address": getattr(ph, "address", ""),
            "pharmacy_phone": getattr(ph, "phone", ""),
            "pharmacy_nif": getattr(ph, "nif", ""),
            "pharmacy_technical_director": getattr(ph, "technical_director", ""),
        },
    )
    try:
        from weasyprint import HTML

        pdf = HTML(string=html).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="ficha_{batch.batch_number}.pdf"'
        return response
    except Exception:
        return HttpResponse(html)


@login_required
def formulation_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    formulations = Formulation.objects.all()
    if pharmacy:
        formulations = formulations.filter(pharmacy=pharmacy)
    search = request.GET.get("q", "")
    if search:
        formulations = formulations.filter(name__icontains=search) | formulations.filter(code__icontains=search)
    return render(
        request,
        "production/formulation_list.html",
        {
            "formulations": formulations,
            "title": _("Formulations"),
        },
    )


@login_required
def formulation_detail(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Formulation.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    formulation = get_object_or_404(qs, pk=pk)
    ingredients = formulation.ingredients.select_related("raw_material").all()
    steps = formulation.steps.all()
    return render(
        request,
        "production/formulation_detail.html",
        {
            "formulation": formulation,
            "ingredients": ingredients,
            "steps": steps,
            "title": formulation.name,
        },
    )


@login_required
@role_required("admin", "pharmacist")
def formulation_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = FormulationForm(request.POST)
        if form.is_valid():
            formulation = form.save(commit=False)
            formulation.created_by = request.user
            formulation.pharmacy = pharmacy
            formulation.save()
            messages.success(request, _("Formulation created."))
            return redirect("production:formulation_detail", pk=formulation.pk)
    else:
        form = FormulationForm()
    return render(request, "production/formulation_form.html", {"form": form, "title": _("New Formulation")})


@login_required
@role_required("admin", "pharmacist")
def formulation_edit(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Formulation.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    formulation = get_object_or_404(qs, pk=pk)
    if request.method == "POST":
        form = FormulationForm(request.POST, instance=formulation)
        if form.is_valid():
            form.save()
            messages.success(request, _("Formulation updated."))
            return redirect("production:formulation_detail", pk=formulation.pk)
    else:
        form = FormulationForm(instance=formulation)
    return render(
        request,
        "production/formulation_form.html",
        {
            "form": form,
            "formulation": formulation,
            "title": _("Edit Formulation"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def formulation_add_ingredient(request, formulation_pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Formulation.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    formulation = get_object_or_404(qs, pk=formulation_pk)
    if request.method == "POST":
        form = FormulationIngredientForm(request.POST, pharmacy=pharmacy)
        if form.is_valid():
            ingredient = form.save(commit=False)
            ingredient.formulation = formulation
            ingredient.save()
            if request.htmx:
                ingredients = formulation.ingredients.select_related("raw_material").all()
                return render(
                    request,
                    "production/partials/_ingredients_table.html",
                    {
                        "ingredients": ingredients,
                        "formulation": formulation,
                    },
                )
            return redirect("production:formulation_detail", pk=formulation.pk)
    else:
        form = FormulationIngredientForm(pharmacy=pharmacy)
    return render(request, "production/partials/_ingredient_form.html", {"form": form, "formulation": formulation})


@login_required
@role_required("admin", "pharmacist")
def formulation_add_step(request, formulation_pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Formulation.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    formulation = get_object_or_404(qs, pk=formulation_pk)
    if request.method == "POST":
        form = FormulationStepForm(request.POST)
        if form.is_valid():
            step = form.save(commit=False)
            step.formulation = formulation
            step.save()
            if request.htmx:
                steps = formulation.steps.all()
                return render(
                    request,
                    "production/partials/_steps_list.html",
                    {
                        "steps": steps,
                        "formulation": formulation,
                    },
                )
            return redirect("production:formulation_detail", pk=formulation.pk)
    else:
        form = FormulationStepForm()
    return render(request, "production/partials/_step_form.html", {"form": form, "formulation": formulation})


@login_required
@role_required("admin", "pharmacist", "lab_technician")
def qc_create(request, batch_pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = ProductionBatch.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    batch = get_object_or_404(qs, pk=batch_pk)
    try:
        batch.quality_control  # noqa: B018
        return redirect("production:qc_detail", batch_pk=batch.pk)
    except QualityControl.DoesNotExist:
        pass

    if request.method == "POST":
        form = QualityControlForm(request.POST)
        if form.is_valid():
            qc = form.save(commit=False)
            qc.batch = batch
            qc.performed_by = request.user
            qc.save()
            messages.success(request, _("Quality control record saved."))
            return redirect("production:batch_detail", pk=batch.pk)
    else:
        form = QualityControlForm()
    return render(
        request,
        "production/qc_form.html",
        {
            "form": form,
            "batch": batch,
            "title": _("Quality Control"),
        },
    )


@login_required
def qc_detail(request, batch_pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = ProductionBatch.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    batch = get_object_or_404(qs, pk=batch_pk)
    try:
        qc = batch.quality_control
    except QualityControl.DoesNotExist:
        return redirect("production:qc_create", batch_pk=batch.pk)
    return render(
        request,
        "production/qc_detail.html",
        {
            "qc": qc,
            "batch": batch,
            "title": _("Quality Control Results"),
        },
    )


@login_required
@role_required("admin", "pharmacist")
def batch_label(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = ProductionBatch.objects.select_related("order", "formulation")
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    batch = get_object_or_404(qs, pk=pk)
    prescription = batch.order.prescriptions.first()
    storage = batch.storage_conditions or batch.formulation.storage_conditions
    # Active ingredients for Portaria 594/2004 label compliance
    ingredients = batch.formulation.ingredients.select_related("raw_material").filter(is_active_ingredient=True)

    ph = pharmacy or batch.pharmacy
    html = render_to_string(
        "production/pdf/batch_label.html",
        {
            "batch": batch,
            "prescription": prescription,
            "storage_conditions": storage,
            "ingredients": ingredients,
            "pharmacy_name": getattr(ph, "name", ""),
            "pharmacy_anf_number": getattr(ph, "anf_number", ""),
        },
    )

    # Mark label as generated
    batch.label_generated_at = timezone.now()
    batch.save(update_fields=["label_generated_at", "updated_at"])

    try:
        from weasyprint import HTML

        pdf = HTML(string=html).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="label_{batch.batch_number}.pdf"'
        return response
    except Exception:
        return HttpResponse(html)


@login_required
def batch_calculator(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = Formulation.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    formulation = get_object_or_404(qs, pk=pk)
    ingredients = formulation.ingredients.select_related("raw_material").all()

    result = None
    form = BatchCalculatorForm(request.GET if "desired_quantity" in request.GET else None)

    if form.is_valid():
        result = BatchCalculatorService.calculate(formulation, form.cleaned_data["desired_quantity"])

    if request.htmx and result:
        return render(
            request,
            "production/partials/_calculator_results.html",
            {
                "result": result,
                "formulation": formulation,
            },
        )

    return render(
        request,
        "production/batch_calculator.html",
        {
            "formulation": formulation,
            "ingredients": ingredients,
            "form": form,
            "result": result,
            "title": _("Batch Calculator — %(name)s") % {"name": formulation.name},
        },
    )


@login_required
@role_required("admin", "pharmacist")
def batch_cost(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = ProductionBatch.objects.all()
    if pharmacy:
        qs = qs.filter(pharmacy=pharmacy)
    batch = get_object_or_404(qs, pk=pk)

    if request.method == "POST":
        form = BatchCostForm(request.POST)
        if form.is_valid():
            BatchCostService.calculate(
                batch,
                packaging_cost=form.cleaned_data["packaging_cost"],
                preparation_fee=form.cleaned_data["preparation_fee"],
            )
            messages.success(request, _("Batch cost calculated."))
            return redirect("production:batch_detail", pk=batch.pk)
    else:
        try:
            existing_cost = batch.cost
            form = BatchCostForm(instance=existing_cost)
        except BatchCost.DoesNotExist:
            form = BatchCostForm()

    # Calculate raw material cost preview
    from decimal import Decimal

    raw_cost = Decimal("0")
    for usage in batch.material_usage.select_related("lot"):
        unit_cost = usage.lot.cost_per_unit or Decimal("0")
        raw_cost += usage.quantity_used * unit_cost

    return render(
        request,
        "production/batch_cost.html",
        {
            "form": form,
            "batch": batch,
            "raw_material_cost": raw_cost,
            "title": _("Batch Cost"),
        },
    )


@login_required
def calibration_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    calibrations = EquipmentCalibration.objects.select_related("performed_by").all()
    if pharmacy:
        calibrations = calibrations.filter(pharmacy=pharmacy)
    return render(
        request,
        "production/calibration_list.html",
        {
            "calibrations": calibrations,
            "title": _("Equipment Calibrations"),
        },
    )


@login_required
@role_required("admin", "pharmacist", "lab_technician")
def calibration_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    if request.method == "POST":
        form = EquipmentCalibrationForm(request.POST, request.FILES)
        if form.is_valid():
            calibration = form.save(commit=False)
            calibration.pharmacy = pharmacy
            calibration.performed_by = request.user
            calibration.created_by = request.user
            calibration.save()
            messages.success(request, _("Calibration record saved."))
            return redirect("production:calibration_list")
    else:
        form = EquipmentCalibrationForm()
    return render(
        request,
        "production/calibration_form.html",
        {
            "form": form,
            "title": _("New Calibration Record"),
        },
    )
