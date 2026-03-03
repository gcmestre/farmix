from django.contrib import admin

from .models import (
    BatchCost,
    BatchMaterialUsage,
    Formulation,
    FormulationIngredient,
    FormulationStep,
    Prescription,
    ProductionBatch,
    ProductionStepLog,
    QualityControl,
)


class FormulationIngredientInline(admin.TabularInline):
    model = FormulationIngredient
    extra = 1


class FormulationStepInline(admin.TabularInline):
    model = FormulationStep
    extra = 1


@admin.register(Formulation)
class FormulationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "pharmaceutical_form", "shelf_life_days", "pharmacy")
    list_filter = ("pharmacy",)
    search_fields = ("code", "name")
    inlines = [FormulationIngredientInline, FormulationStepInline]


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("order", "doctor_name", "patient_name", "validated_by")
    search_fields = ("doctor_name", "patient_name")


class ProductionStepLogInline(admin.TabularInline):
    model = ProductionStepLog
    extra = 0


class BatchMaterialUsageInline(admin.TabularInline):
    model = BatchMaterialUsage
    extra = 0


@admin.register(ProductionBatch)
class ProductionBatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "order", "formulation", "status", "produced_by", "pharmacy", "created_at")
    list_filter = ("status", "pharmacy")
    search_fields = ("batch_number",)
    readonly_fields = ("batch_number",)
    inlines = [ProductionStepLogInline, BatchMaterialUsageInline]


@admin.register(QualityControl)
class QualityControlAdmin(admin.ModelAdmin):
    list_display = ("batch", "passed", "performed_by", "performed_at")
    list_filter = ("passed",)
    readonly_fields = ("weight_deviation_pct",)


@admin.register(BatchCost)
class BatchCostAdmin(admin.ModelAdmin):
    list_display = ("batch", "raw_material_cost", "packaging_cost", "preparation_fee", "total_cost")
    readonly_fields = ("total_cost",)
