from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from apps.core.models import BaseModel
from apps.core.validators import FileValidator


class Client(BaseModel):
    """Client: pharmacy, institution, or individual."""

    class ClientType(models.TextChoices):
        PHARMACY = "pharmacy", _("Pharmacy")
        INSTITUTION = "institution", _("Institution")
        INDIVIDUAL = "individual", _("Individual")

    pharmacy = models.ForeignKey(
        "core.Pharmacy",
        on_delete=models.CASCADE,
        related_name="clients",
        verbose_name=_("pharmacy"),
        null=True,
        blank=True,
    )
    client_type = models.CharField(
        _("client type"), max_length=20, choices=ClientType.choices, default=ClientType.INDIVIDUAL
    )
    name = models.CharField(_("name"), max_length=255)
    nif = models.CharField(_("NIF"), max_length=20, help_text=_("Tax identification number"))
    infarmed_code = models.CharField(_("Infarmed code"), max_length=50, blank=True)
    email = models.EmailField(_("email"), blank=True)
    phone = models.CharField(_("phone"), max_length=20, blank=True)
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("client")
        verbose_name_plural = _("clients")
        ordering = ["name"]
        unique_together = [("pharmacy", "nif")]

    def __str__(self):
        return f"{self.name} ({self.nif})"


class Order(BaseModel):
    """Order with FSM status workflow."""

    class Status(models.TextChoices):
        NEW_REQUEST = "new_request", _("New Request")
        WAITING_FOR_QUOTE = "waiting_for_quote", _("Waiting for Quote")
        WAITING_FOR_RECIPE = "waiting_for_recipe", _("Waiting for Recipe")
        READY_FOR_PRODUCTION = "ready_for_production", _("Ready for Production")
        IN_PRODUCTION = "in_production", _("In Production")
        READY = "ready", _("Ready")
        COMPLETE = "complete", _("Complete")
        CANCELLED = "cancelled", _("Cancelled")
        ERROR = "error", _("Error")

    class Source(models.TextChoices):
        WHATSAPP = "whatsapp", _("WhatsApp")
        EMAIL = "email", _("Email")
        IN_PERSON = "in_person", _("In Person")
        PHONE = "phone", _("Phone")

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        NORMAL = "normal", _("Normal")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    pharmacy = models.ForeignKey(
        "core.Pharmacy",
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("pharmacy"),
        null=True,
        blank=True,
    )
    order_number = models.CharField(_("order number"), max_length=20, editable=False)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="orders", verbose_name=_("client"))
    source = models.CharField(_("source"), max_length=20, choices=Source.choices, default=Source.IN_PERSON)
    status = FSMField(_("status"), default=Status.NEW_REQUEST, choices=Status.choices, db_index=True)
    priority = models.CharField(_("priority"), max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders",
        verbose_name=_("assigned to"),
    )
    prescription_file = models.FileField(
        _("prescription file"),
        upload_to="prescriptions/",
        blank=True,
        validators=[FileValidator()],
    )
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ["-created_at"]
        unique_together = [("pharmacy", "order_number")]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number(self.pharmacy)
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number(pharmacy=None):
        from django.utils import timezone

        today = timezone.now()
        prefix = today.strftime("ORD-%Y%m-")
        qs = Order.all_objects.filter(order_number__startswith=prefix)
        if pharmacy:
            qs = qs.filter(pharmacy=pharmacy)
        last = qs.order_by("-order_number").first()
        if last:
            seq = int(last.order_number.split("-")[-1]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    # --- FSM Transitions ---
    @transition(field=status, source=Status.NEW_REQUEST, target=Status.WAITING_FOR_QUOTE)
    def send_for_quote(self):
        pass

    @transition(field=status, source=Status.WAITING_FOR_QUOTE, target=Status.WAITING_FOR_RECIPE)
    def quote_accepted(self):
        pass

    @transition(field=status, source=Status.WAITING_FOR_RECIPE, target=Status.READY_FOR_PRODUCTION)
    def recipe_received(self):
        pass

    @transition(field=status, source=Status.READY_FOR_PRODUCTION, target=Status.IN_PRODUCTION)
    def start_production(self):
        pass

    @transition(field=status, source=Status.IN_PRODUCTION, target=Status.READY)
    def production_complete(self):
        pass

    @transition(field=status, source=Status.READY, target=Status.COMPLETE)
    def mark_complete(self):
        pass

    @transition(
        field=status,
        source=[
            Status.NEW_REQUEST,
            Status.WAITING_FOR_QUOTE,
            Status.WAITING_FOR_RECIPE,
            Status.READY_FOR_PRODUCTION,
            Status.IN_PRODUCTION,
            Status.READY,
        ],
        target=Status.CANCELLED,
    )
    def cancel(self):
        pass

    @transition(
        field=status,
        source=[
            Status.NEW_REQUEST,
            Status.WAITING_FOR_QUOTE,
            Status.WAITING_FOR_RECIPE,
            Status.READY_FOR_PRODUCTION,
            Status.IN_PRODUCTION,
        ],
        target=Status.ERROR,
    )
    def mark_error(self):
        pass


class OrderItem(BaseModel):
    """Line item for an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("order"))
    description = models.CharField(_("description"), max_length=500)
    formulation = models.ForeignKey(
        "production.Formulation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name=_("formulation"),
    )
    quantity = models.DecimalField(_("quantity"), max_digits=10, decimal_places=3)
    unit = models.CharField(_("unit"), max_length=20, default="un")
    unit_price = models.DecimalField(_("unit price"), max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")

    def __str__(self):
        return f"{self.description} x{self.quantity}"

    @property
    def total_price(self):
        return self.quantity * self.unit_price


class OrderStatusLog(models.Model):
    """Immutable log of order status transitions."""

    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_logs", verbose_name=_("order"))
    from_status = models.CharField(_("from status"), max_length=30)
    to_status = models.CharField(_("to status"), max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name=_("changed by")
    )
    comment = models.TextField(_("comment"), blank=True)
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("order status log")
        verbose_name_plural = _("order status logs")
        ordering = ["-timestamp"]
        default_permissions = ("add", "view")

    def __str__(self):
        return f"{self.order} : {self.from_status} → {self.to_status}"


class Complaint(BaseModel):
    """Complaint record — regulatory compliance."""

    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        INVESTIGATING = "investigating", _("Investigating")
        RESOLVED = "resolved", _("Resolved")
        CLOSED = "closed", _("Closed")

    pharmacy = models.ForeignKey(
        "core.Pharmacy",
        on_delete=models.CASCADE,
        related_name="complaints",
        verbose_name=_("pharmacy"),
        null=True,
        blank=True,
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
        verbose_name=_("order"),
    )
    batch = models.ForeignKey(
        "production.ProductionBatch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
        verbose_name=_("batch"),
    )
    complainant_name = models.CharField(_("complainant name"), max_length=255)
    complaint_date = models.DateField(_("complaint date"))
    description = models.TextField(_("description"))
    investigation = models.TextField(_("investigation"), blank=True)
    corrective_action = models.TextField(_("corrective action"), blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_complaints",
        verbose_name=_("resolved by"),
    )
    resolved_at = models.DateTimeField(_("resolved at"), null=True, blank=True)

    class Meta:
        verbose_name = _("complaint")
        verbose_name_plural = _("complaints")
        ordering = ["-complaint_date"]

    def __str__(self):
        return f"Complaint {self.complaint_date} — {self.complainant_name}"
