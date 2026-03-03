from django.contrib import admin

from .models import Lot, ProhibitedSubstance, RawMaterial, StockMovement, Supplier


class LotInline(admin.TabularInline):
    model = Lot
    extra = 0
    fields = [
        "lot_number",
        "supplier",
        "initial_quantity",
        "current_quantity",
        "received_date",
        "expiry_date",
        "is_quarantined",
        "is_exhausted",
    ]
    readonly_fields = ["current_quantity"]


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = [
        "movement_type",
        "quantity",
        "balance_after",
        "reference_batch",
        "performed_by",
        "timestamp",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "nif", "email", "phone", "is_active", "pharmacy"]
    list_filter = ["is_active", "pharmacy"]
    search_fields = ["name", "nif"]


@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "cas_number",
        "default_unit",
        "minimum_stock",
        "preferred_supplier",
        "is_controlled_substance",
        "pharmacy",
    ]
    list_filter = ["is_controlled_substance", "pharmacy"]
    search_fields = ["code", "name", "cas_number"]
    inlines = [LotInline]


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = [
        "lot_number",
        "raw_material",
        "supplier",
        "current_quantity",
        "received_date",
        "expiry_date",
        "is_quarantined",
        "is_exhausted",
    ]
    list_filter = ["is_quarantined", "is_exhausted"]
    search_fields = ["lot_number", "raw_material__name"]
    inlines = [StockMovementInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "lot",
        "movement_type",
        "quantity",
        "balance_after",
        "performed_by",
        "timestamp",
    ]
    list_filter = ["movement_type"]
    readonly_fields = [
        "lot",
        "movement_type",
        "quantity",
        "balance_after",
        "reference_batch",
        "performed_by",
        "notes",
        "timestamp",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProhibitedSubstance)
class ProhibitedSubstanceAdmin(admin.ModelAdmin):
    list_display = ["name", "cas_number", "regulation"]
    search_fields = ["name", "cas_number"]
