import abc
from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from apps.core.models import BaseModel


class Quote(BaseModel):
    """Price quote for an order."""

    pharmacy = models.ForeignKey(
        "core.Pharmacy",
        on_delete=models.CASCADE,
        related_name="quotes",
        verbose_name=_("pharmacy"),
        null=True,
        blank=True,
    )
    quote_number = models.CharField(_("quote number"), max_length=20, editable=False)
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="quotes", verbose_name=_("order"))
    client = models.ForeignKey(
        "orders.Client", on_delete=models.PROTECT, related_name="quotes", verbose_name=_("client")
    )
    valid_until = models.DateField(_("valid until"))
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("quote")
        verbose_name_plural = _("quotes")
        ordering = ["-created_at"]
        unique_together = [("pharmacy", "quote_number")]

    def __str__(self):
        return f"Quote {self.quote_number}"

    def save(self, *args, **kwargs):
        if not self.quote_number:
            self.quote_number = self._generate_quote_number(self.pharmacy)
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_quote_number(pharmacy=None):
        from django.utils import timezone

        today = timezone.now()
        prefix = today.strftime("QUO-%Y%m-")
        qs = Quote.all_objects.filter(quote_number__startswith=prefix)
        if pharmacy:
            qs = qs.filter(pharmacy=pharmacy)
        last = qs.order_by("-quote_number").first()
        seq = int(last.quote_number.split("-")[-1]) + 1 if last else 1
        return f"{prefix}{seq:04d}"

    @property
    def total(self):
        return sum(line.total for line in self.lines.all())

    @property
    def total_with_iva(self):
        return sum(line.total_with_iva for line in self.lines.all())


class QuoteLine(BaseModel):
    """Line item in a quote."""

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="lines", verbose_name=_("quote"))
    description = models.CharField(_("description"), max_length=500)
    quantity = models.DecimalField(_("quantity"), max_digits=10, decimal_places=3)
    unit = models.CharField(_("unit"), max_length=20, default="un")
    unit_price = models.DecimalField(_("unit price"), max_digits=10, decimal_places=2)
    iva_rate = models.DecimalField(_("IVA rate"), max_digits=5, decimal_places=2, default=Decimal("23.00"))

    class Meta:
        verbose_name = _("quote line")
        verbose_name_plural = _("quote lines")

    def __str__(self):
        return f"{self.description} x{self.quantity}"

    @property
    def total(self):
        return self.quantity * self.unit_price

    @property
    def total_with_iva(self):
        return self.total * (1 + self.iva_rate / 100)


class Invoice(BaseModel):
    """Invoice with FSM status and provider integration."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SENT = "sent", _("Sent")
        PAID = "paid", _("Paid")
        OVERDUE = "overdue", _("Overdue")
        CANCELLED = "cancelled", _("Cancelled")

    pharmacy = models.ForeignKey(
        "core.Pharmacy",
        on_delete=models.CASCADE,
        related_name="invoices",
        verbose_name=_("pharmacy"),
        null=True,
        blank=True,
    )
    invoice_number = models.CharField(_("invoice number"), max_length=30, editable=False)
    external_id = models.CharField(_("external ID"), max_length=100, blank=True, help_text=_("Sipharma ID"))
    provider_name = models.CharField(_("provider"), max_length=50, default="sipharma")
    order = models.ForeignKey(
        "orders.Order", on_delete=models.PROTECT, related_name="invoices", verbose_name=_("order")
    )
    client = models.ForeignKey(
        "orders.Client", on_delete=models.PROTECT, related_name="invoices", verbose_name=_("client")
    )
    status = FSMField(_("status"), default=Status.DRAFT, choices=Status.choices, db_index=True)
    due_date = models.DateField(_("due date"), null=True, blank=True)
    synced_at = models.DateTimeField(_("synced at"), null=True, blank=True)
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("invoice")
        verbose_name_plural = _("invoices")
        ordering = ["-created_at"]
        unique_together = [("pharmacy", "invoice_number")]

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self._generate_invoice_number(self.pharmacy)
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_invoice_number(pharmacy=None):
        from django.utils import timezone

        today = timezone.now()
        prefix = today.strftime("INV-%Y%m-")
        qs = Invoice.all_objects.filter(invoice_number__startswith=prefix)
        if pharmacy:
            qs = qs.filter(pharmacy=pharmacy)
        last = qs.order_by("-invoice_number").first()
        seq = int(last.invoice_number.split("-")[-1]) + 1 if last else 1
        return f"{prefix}{seq:04d}"

    @property
    def total(self):
        return sum(line.total for line in self.lines.all())

    @property
    def total_with_iva(self):
        return sum(line.total_with_iva for line in self.lines.all())

    # --- FSM Transitions ---
    @transition(field=status, source=Status.DRAFT, target=Status.SENT)
    def send(self):
        pass

    @transition(field=status, source=[Status.SENT, Status.OVERDUE], target=Status.PAID)
    def mark_paid(self):
        pass

    @transition(field=status, source=Status.SENT, target=Status.OVERDUE)
    def mark_overdue(self):
        pass

    @transition(field=status, source=[Status.DRAFT, Status.SENT], target=Status.CANCELLED)
    def cancel(self):
        pass


class InvoiceLine(BaseModel):
    """Line item in an invoice."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines", verbose_name=_("invoice"))
    description = models.CharField(_("description"), max_length=500)
    quantity = models.DecimalField(_("quantity"), max_digits=10, decimal_places=3)
    unit = models.CharField(_("unit"), max_length=20, default="un")
    unit_price = models.DecimalField(_("unit price"), max_digits=10, decimal_places=2)
    iva_rate = models.DecimalField(_("IVA rate"), max_digits=5, decimal_places=2, default=Decimal("23.00"))

    class Meta:
        verbose_name = _("invoice line")
        verbose_name_plural = _("invoice lines")

    def __str__(self):
        return f"{self.description} x{self.quantity}"

    @property
    def total(self):
        return self.quantity * self.unit_price

    @property
    def total_with_iva(self):
        return self.total * (1 + self.iva_rate / 100)


class AbstractInvoiceProvider(abc.ABC):
    """Abstract interface for invoice providers (e.g., Sipharma)."""

    @abc.abstractmethod
    def create_invoice(self, invoice):
        """Create invoice in external system. Returns external_id."""

    @abc.abstractmethod
    def cancel_invoice(self, invoice):
        """Cancel invoice in external system."""

    @abc.abstractmethod
    def get_invoice_status(self, invoice):
        """Get current status from external system."""

    @abc.abstractmethod
    def get_invoice_pdf(self, invoice):
        """Download PDF from external system. Returns bytes."""


class SipharmaProvider(AbstractInvoiceProvider):
    """Stub implementation for Sipharma invoicing provider."""

    def create_invoice(self, invoice):
        # TODO: Implement with Sipharma API
        return f"SIPH-{invoice.invoice_number}"

    def cancel_invoice(self, invoice):
        # TODO: Implement with Sipharma API
        pass

    def get_invoice_status(self, invoice):
        # TODO: Implement with Sipharma API
        return invoice.status

    def get_invoice_pdf(self, invoice):
        # TODO: Implement with Sipharma API
        return b""
