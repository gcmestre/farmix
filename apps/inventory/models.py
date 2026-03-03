from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.validators import FileValidator


class Supplier(BaseModel):
    """Raw material supplier."""

    pharmacy = models.ForeignKey(
        "core.Pharmacy",
        on_delete=models.CASCADE,
        related_name="suppliers",
        verbose_name=_("pharmacy"),
        null=True,
        blank=True,
    )
    name = models.CharField(_("name"), max_length=255)
    nif = models.CharField(_("NIF"), max_length=20)
    email = models.EmailField(_("email"), blank=True)
    phone = models.CharField(_("phone"), max_length=20, blank=True)
    address = models.TextField(_("address"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("supplier")
        verbose_name_plural = _("suppliers")
        ordering = ["name"]
        unique_together = [("pharmacy", "nif")]

    def __str__(self):
        return self.name


class RawMaterial(BaseModel):
    """Raw material / ingredient for compound medications."""

    pharmacy = models.ForeignKey(
        "core.Pharmacy",
        on_delete=models.CASCADE,
        related_name="materials",
        verbose_name=_("pharmacy"),
        null=True,
        blank=True,
    )
    code = models.CharField(_("code"), max_length=50)
    name = models.CharField(_("name"), max_length=255)
    cas_number = models.CharField(_("CAS number"), max_length=30, blank=True, help_text=_("Chemical Abstracts Service"))
    default_unit = models.CharField(_("default unit"), max_length=20, default="g")
    minimum_stock = models.DecimalField(_("minimum stock"), max_digits=10, decimal_places=3, default=0)
    reorder_point = models.DecimalField(_("reorder point"), max_digits=10, decimal_places=3, default=0)
    preferred_supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_materials",
        verbose_name=_("preferred supplier"),
    )
    is_controlled_substance = models.BooleanField(_("controlled substance"), default=False)
    pharmacopeia_reference = models.CharField(
        _("pharmacopeia reference"),
        max_length=100,
        blank=True,
        help_text=_("e.g., FP X, Ph.Eur., USP"),
    )
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("raw material")
        verbose_name_plural = _("raw materials")
        ordering = ["name"]
        unique_together = [("pharmacy", "code")]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def current_stock(self):
        """Sum of current_quantity across all non-exhausted, non-quarantined lots."""
        from django.db.models import Sum

        return (
            self.lots.filter(is_exhausted=False, is_quarantined=False).aggregate(total=Sum("current_quantity"))["total"]
            or 0
        )

    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock


class Lot(BaseModel):
    """Lot/batch of a raw material received from a supplier."""

    raw_material = models.ForeignKey(
        RawMaterial, on_delete=models.CASCADE, related_name="lots", verbose_name=_("raw material")
    )
    lot_number = models.CharField(_("lot number"), max_length=50)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="lots", verbose_name=_("supplier"))
    initial_quantity = models.DecimalField(_("initial quantity"), max_digits=10, decimal_places=3)
    current_quantity = models.DecimalField(_("current quantity"), max_digits=10, decimal_places=3)
    received_date = models.DateField(_("received date"))
    expiry_date = models.DateField(_("expiry date"))
    certificate_of_analysis = models.FileField(
        _("certificate of analysis"),
        upload_to="inventory/coa/",
        blank=True,
        validators=[FileValidator()],
    )
    cost_per_unit = models.DecimalField(
        _("cost per unit"),
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text=_("Cost per base unit (e.g., per gram, per mL)"),
    )
    is_quarantined = models.BooleanField(_("quarantined"), default=False)
    is_exhausted = models.BooleanField(_("exhausted"), default=False)

    class Meta:
        verbose_name = _("lot")
        verbose_name_plural = _("lots")
        ordering = ["expiry_date"]  # FEFO: First Expiry, First Out

    def __str__(self):
        return f"{self.raw_material.code} Lot#{self.lot_number}"


class StockMovement(models.Model):
    """Immutable stock movement ledger."""

    class MovementType(models.TextChoices):
        RECEIPT = "receipt", _("Receipt")
        PRODUCTION_USE = "production_use", _("Production Use")
        ADJUSTMENT = "adjustment", _("Adjustment")
        DISPOSAL = "disposal", _("Disposal")
        RETURN = "return", _("Return")

    id = models.AutoField(primary_key=True)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="movements", verbose_name=_("lot"))
    movement_type = models.CharField(_("type"), max_length=20, choices=MovementType.choices)
    quantity = models.DecimalField(_("quantity"), max_digits=10, decimal_places=3)
    balance_after = models.DecimalField(_("balance after"), max_digits=10, decimal_places=3)
    reference_batch = models.ForeignKey(
        "production.ProductionBatch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name=_("reference batch"),
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name=_("performed by")
    )
    notes = models.TextField(_("notes"), blank=True)
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("stock movement")
        verbose_name_plural = _("stock movements")
        ordering = ["-timestamp"]
        default_permissions = ("add", "view")

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} on {self.lot}"


class ProhibitedSubstance(BaseModel):
    """Prohibited substance per Deliberação 1985/2015."""

    name = models.CharField(_("name"), max_length=255, unique=True)
    cas_number = models.CharField(_("CAS number"), max_length=30, blank=True)
    regulation = models.CharField(_("regulation"), max_length=100, default="Deliberação 1985/2015")
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("prohibited substance")
        verbose_name_plural = _("prohibited substances")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.cas_number})" if self.cas_number else self.name
