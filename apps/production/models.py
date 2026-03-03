from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from apps.core.fields import EncryptedCharField, EncryptedTextField
from apps.core.models import BaseModel
from apps.core.validators import FileValidator


class Formulation(BaseModel):
    """Compound medication formulation/recipe."""

    pharmacy = models.ForeignKey(
        "core.Pharmacy",
        on_delete=models.CASCADE,
        related_name="formulations",
        verbose_name=_("pharmacy"),
        null=True,
        blank=True,
    )
    code = models.CharField(_("code"), max_length=50)
    name = models.CharField(_("name"), max_length=255)
    pharmaceutical_form = models.CharField(
        _("pharmaceutical form"), max_length=100, help_text=_("e.g., cream, capsule, solution")
    )
    route_of_administration = models.CharField(
        _("route of administration"), max_length=100, blank=True, help_text=_("e.g., oral, topical, nasal")
    )
    dosage_instructions = models.TextField(_("dosage instructions"), blank=True)
    is_multi_stage = models.BooleanField(_("multi-stage"), default=False)
    shelf_life_days = models.PositiveIntegerField(_("shelf life (days)"), default=90)
    storage_conditions = models.CharField(_("storage conditions"), max_length=255, blank=True)
    base_quantity = models.DecimalField(
        _("base quantity"),
        max_digits=10,
        decimal_places=3,
        default=100,
        help_text=_("Base quantity the ingredient amounts refer to (e.g., 100 for 100g)"),
    )
    base_unit = models.CharField(
        _("base unit"),
        max_length=20,
        default="g",
        help_text=_("Unit of the base quantity (e.g., g, mL)"),
    )
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("formulation")
        verbose_name_plural = _("formulations")
        ordering = ["code"]
        unique_together = [("pharmacy", "code")]

    def __str__(self):
        return f"{self.code} - {self.name}"


class FormulationIngredient(BaseModel):
    """Ingredient in a formulation."""

    formulation = models.ForeignKey(
        Formulation, on_delete=models.CASCADE, related_name="ingredients", verbose_name=_("formulation")
    )
    raw_material = models.ForeignKey(
        "inventory.RawMaterial",
        on_delete=models.PROTECT,
        related_name="formulation_ingredients",
        verbose_name=_("raw material"),
    )
    quantity = models.DecimalField(_("quantity"), max_digits=10, decimal_places=4)
    unit = models.CharField(_("unit"), max_length=20, default="g")
    is_active_ingredient = models.BooleanField(_("active ingredient"), default=False)
    order_of_addition = models.PositiveIntegerField(_("order of addition"), default=0)

    class Meta:
        verbose_name = _("formulation ingredient")
        verbose_name_plural = _("formulation ingredients")
        ordering = ["order_of_addition"]

    def __str__(self):
        return f"{self.raw_material} ({self.quantity} {self.unit})"


class FormulationStep(BaseModel):
    """Step in a formulation procedure."""

    formulation = models.ForeignKey(
        Formulation, on_delete=models.CASCADE, related_name="steps", verbose_name=_("formulation")
    )
    step_number = models.PositiveIntegerField(_("step number"))
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    estimated_duration = models.DurationField(_("estimated duration"), null=True, blank=True)

    class Meta:
        verbose_name = _("formulation step")
        verbose_name_plural = _("formulation steps")
        ordering = ["step_number"]

    def __str__(self):
        return f"Step {self.step_number}: {self.title}"


class Prescription(BaseModel):
    """Prescription linked to an order — contains RGPD-sensitive data."""

    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="prescriptions", verbose_name=_("order")
    )
    doctor_name = models.CharField(_("doctor name"), max_length=255)
    doctor_license = models.CharField(_("doctor license"), max_length=50, blank=True)
    patient_name = EncryptedCharField(_("patient name"), max_length=500)
    patient_tax_number = EncryptedCharField(_("patient NIF"), max_length=500, blank=True)
    patient_address = EncryptedTextField(_("patient address"), blank=True)
    file = models.FileField(
        _("prescription file"),
        upload_to="prescriptions/rx/",
        blank=True,
        validators=[FileValidator()],
    )
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validated_prescriptions",
        verbose_name=_("validated by"),
    )

    class RGPDMeta:
        anonymizable_fields = ["patient_name", "patient_tax_number"]

    class Meta:
        verbose_name = _("prescription")
        verbose_name_plural = _("prescriptions")

    def __str__(self):
        return f"Rx for {self.patient_name} (Order: {self.order})"


class ProductionBatch(BaseModel):
    """Production batch tracking with FSM status."""

    class Status(models.TextChoices):
        PLANNED = "planned", _("Planned")
        IN_PROGRESS = "in_progress", _("In Progress")
        QUALITY_CHECK = "quality_check", _("Quality Check")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")
        COMPLETE = "complete", _("Complete")

    pharmacy = models.ForeignKey(
        "core.Pharmacy",
        on_delete=models.CASCADE,
        related_name="batches",
        verbose_name=_("pharmacy"),
        null=True,
        blank=True,
    )
    batch_number = models.CharField(_("batch number"), max_length=30, editable=False)
    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="batches", verbose_name=_("order"))
    formulation = models.ForeignKey(
        Formulation, on_delete=models.PROTECT, related_name="batches", verbose_name=_("formulation")
    )
    status = FSMField(_("status"), default=Status.PLANNED, choices=Status.choices, db_index=True)
    produced_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="produced_batches",
        verbose_name=_("produced by"),
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_batches",
        verbose_name=_("verified by"),
    )
    expiry_date = models.DateField(_("expiry date"), null=True, blank=True)
    production_parameters = models.JSONField(_("production parameters"), default=dict, blank=True)
    quantity_produced = models.DecimalField(_("quantity produced"), max_digits=10, decimal_places=3, default=0)
    unit = models.CharField(_("unit"), max_length=20, default="un")
    storage_conditions = models.CharField(
        _("storage conditions"),
        max_length=255,
        blank=True,
        help_text=_("Batch-level override; falls back to formulation"),
    )
    special_precautions = models.TextField(_("special precautions"), blank=True)
    label_generated_at = models.DateTimeField(_("label generated at"), null=True, blank=True)

    class Meta:
        verbose_name = _("production batch")
        verbose_name_plural = _("production batches")
        ordering = ["-created_at"]
        unique_together = [("pharmacy", "batch_number")]

    def __str__(self):
        return f"Batch {self.batch_number}"

    def save(self, *args, **kwargs):
        if not self.batch_number:
            self.batch_number = self._generate_batch_number(self.pharmacy)
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_batch_number(pharmacy=None):
        from django.utils import timezone

        today = timezone.now()
        prefix = today.strftime("BAT-%Y%m-")
        qs = ProductionBatch.all_objects.filter(batch_number__startswith=prefix)
        if pharmacy:
            qs = qs.filter(pharmacy=pharmacy)
        last = qs.order_by("-batch_number").first()
        if last:
            seq = int(last.batch_number.split("-")[-1]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    # --- FSM Transitions ---
    @transition(field=status, source=Status.PLANNED, target=Status.IN_PROGRESS)
    def start(self):
        pass

    @transition(field=status, source=Status.IN_PROGRESS, target=Status.QUALITY_CHECK)
    def send_to_quality(self):
        pass

    @transition(field=status, source=Status.QUALITY_CHECK, target=Status.APPROVED)
    def approve(self):
        pass

    @transition(field=status, source=Status.QUALITY_CHECK, target=Status.REJECTED)
    def reject(self):
        pass

    @transition(field=status, source=Status.APPROVED, target=Status.COMPLETE)
    def complete(self):
        pass


class ProductionStepLog(BaseModel):
    """Log of completed production steps for a batch."""

    batch = models.ForeignKey(
        ProductionBatch, on_delete=models.CASCADE, related_name="step_logs", verbose_name=_("batch")
    )
    step = models.ForeignKey(
        FormulationStep, on_delete=models.PROTECT, related_name="production_logs", verbose_name=_("step")
    )
    started_at = models.DateTimeField(_("started at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_steps",
        verbose_name=_("performed by"),
    )
    observations = models.TextField(_("observations"), blank=True)
    parameters = models.JSONField(_("parameters"), default=dict, blank=True)

    class Meta:
        verbose_name = _("production step log")
        verbose_name_plural = _("production step logs")
        ordering = ["step__step_number"]

    def __str__(self):
        return f"{self.batch} - {self.step}"


class BatchMaterialUsage(BaseModel):
    """Material usage tracking per batch — full traceability."""

    batch = models.ForeignKey(
        ProductionBatch, on_delete=models.CASCADE, related_name="material_usage", verbose_name=_("batch")
    )
    lot = models.ForeignKey(
        "inventory.Lot", on_delete=models.PROTECT, related_name="batch_usage", verbose_name=_("lot")
    )
    quantity_used = models.DecimalField(_("quantity used"), max_digits=10, decimal_places=4)

    class Meta:
        verbose_name = _("batch material usage")
        verbose_name_plural = _("batch material usage")

    def __str__(self):
        return f"{self.batch} used {self.quantity_used} from {self.lot}"


class QualityControl(BaseModel):
    """Quality control record for a production batch (Portaria 594/2004)."""

    batch = models.OneToOneField(
        ProductionBatch, on_delete=models.CASCADE, related_name="quality_control", verbose_name=_("batch")
    )
    # Organoleptic checks
    appearance = models.CharField(_("appearance"), max_length=255)
    odor = models.CharField(_("odor"), max_length=255, blank=True)
    texture = models.CharField(_("texture"), max_length=255, blank=True)
    # pH measurement
    ph_value = models.DecimalField(_("pH value"), max_digits=5, decimal_places=2, null=True, blank=True)
    # Weight / volume verification
    expected_weight = models.DecimalField(
        _("expected weight/volume"), max_digits=10, decimal_places=3, null=True, blank=True
    )
    actual_weight = models.DecimalField(
        _("actual weight/volume"), max_digits=10, decimal_places=3, null=True, blank=True
    )
    weight_deviation_pct = models.DecimalField(
        _("weight deviation (%)"), max_digits=5, decimal_places=2, null=True, blank=True
    )
    passed = models.BooleanField(_("passed"), default=False)
    observations = models.TextField(_("observations"), blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="qc_performed",
        verbose_name=_("performed by"),
    )
    performed_at = models.DateTimeField(_("performed at"), auto_now_add=True)

    class Meta:
        verbose_name = _("quality control")
        verbose_name_plural = _("quality controls")

    def __str__(self):
        status = _("Passed") if self.passed else _("Failed")
        return f"QC {self.batch.batch_number} - {status}"

    def save(self, *args, **kwargs):
        if self.expected_weight and self.actual_weight and self.expected_weight > 0:
            deviation = abs(self.actual_weight - self.expected_weight) / self.expected_weight * 100
            self.weight_deviation_pct = round(deviation, 2)
        super().save(*args, **kwargs)


class BatchCost(BaseModel):
    """Cost breakdown for a production batch (Portaria 769/2004)."""

    batch = models.OneToOneField(
        ProductionBatch, on_delete=models.CASCADE, related_name="cost", verbose_name=_("batch")
    )
    raw_material_cost = models.DecimalField(_("raw material cost"), max_digits=10, decimal_places=2, default=0)
    packaging_cost = models.DecimalField(_("packaging cost"), max_digits=10, decimal_places=2, default=0)
    preparation_fee = models.DecimalField(_("preparation fee"), max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(_("total cost"), max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("batch cost")
        verbose_name_plural = _("batch costs")

    def __str__(self):
        return f"Cost {self.batch.batch_number}: €{self.total_cost}"

    def save(self, *args, **kwargs):
        self.total_cost = self.raw_material_cost + self.packaging_cost + self.preparation_fee
        super().save(*args, **kwargs)


class EquipmentCalibration(BaseModel):
    """Equipment calibration record — regulatory compliance."""

    pharmacy = models.ForeignKey(
        "core.Pharmacy",
        on_delete=models.CASCADE,
        related_name="calibrations",
        verbose_name=_("pharmacy"),
        null=True,
        blank=True,
    )
    equipment_name = models.CharField(_("equipment name"), max_length=255)
    serial_number = models.CharField(_("serial number"), max_length=100, blank=True)
    calibration_date = models.DateField(_("calibration date"))
    next_calibration_date = models.DateField(_("next calibration date"))
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="calibrations_performed",
        verbose_name=_("performed by"),
    )
    certificate_file = models.FileField(
        _("certificate file"),
        upload_to="calibrations/",
        blank=True,
        validators=[FileValidator()],
    )
    observations = models.TextField(_("observations"), blank=True)

    class Meta:
        verbose_name = _("equipment calibration")
        verbose_name_plural = _("equipment calibrations")
        ordering = ["-calibration_date"]

    def __str__(self):
        return f"{self.equipment_name} — {self.calibration_date}"
