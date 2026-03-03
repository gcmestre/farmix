from django.contrib import admin

from .models import Invoice, InvoiceLine, Quote, QuoteLine


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 1
    fields = ["description", "quantity", "unit", "unit_price", "iva_rate"]


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1
    fields = ["description", "quantity", "unit", "unit_price", "iva_rate"]


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["quote_number", "order", "client", "valid_until", "pharmacy", "created_at"]
    list_filter = ["pharmacy"]
    search_fields = ["quote_number", "client__name"]
    readonly_fields = ["quote_number"]
    inlines = [QuoteLineInline]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "order",
        "client",
        "status",
        "due_date",
        "pharmacy",
        "synced_at",
    ]
    list_filter = ["status", "pharmacy"]
    search_fields = ["invoice_number", "client__name", "external_id"]
    readonly_fields = ["invoice_number", "external_id", "synced_at"]
    inlines = [InvoiceLineInline]
