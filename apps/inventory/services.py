from decimal import Decimal

from django.utils import timezone

from .models import Lot, ProhibitedSubstance, RawMaterial, StockMovement


class StockService:
    """Service for managing stock operations (FEFO-compliant)."""

    @staticmethod
    def receive_stock(lot, user=None):
        """Record stock receipt for a lot."""
        StockMovement.objects.create(
            lot=lot,
            movement_type=StockMovement.MovementType.RECEIPT,
            quantity=lot.initial_quantity,
            balance_after=lot.current_quantity,
            performed_by=user,
            notes=f"Initial receipt of lot {lot.lot_number}",
        )

    @staticmethod
    def use_for_production(raw_material, quantity, batch=None, user=None):
        """
        Consume stock using FEFO (First Expiry, First Out).
        Returns list of (lot, quantity_used) tuples.
        """
        remaining = Decimal(str(quantity))
        usage = []

        lots = Lot.objects.filter(
            raw_material=raw_material,
            is_exhausted=False,
            is_quarantined=False,
        ).order_by("expiry_date")

        for lot in lots:
            if remaining <= 0:
                break

            available = lot.current_quantity
            used = min(available, remaining)

            lot.current_quantity -= used
            if lot.current_quantity <= 0:
                lot.current_quantity = 0
                lot.is_exhausted = True
            lot.save()

            StockMovement.objects.create(
                lot=lot,
                movement_type=StockMovement.MovementType.PRODUCTION_USE,
                quantity=-used,
                balance_after=lot.current_quantity,
                reference_batch=batch,
                performed_by=user,
            )

            usage.append((lot, used))
            remaining -= used

        return usage

    @staticmethod
    def adjust_stock(lot, quantity, user=None, notes=""):
        """Manual stock adjustment (positive or negative)."""
        lot.current_quantity += Decimal(str(quantity))
        if lot.current_quantity <= 0:
            lot.current_quantity = 0
            lot.is_exhausted = True
        else:
            lot.is_exhausted = False
        lot.save()

        StockMovement.objects.create(
            lot=lot,
            movement_type=StockMovement.MovementType.ADJUSTMENT,
            quantity=quantity,
            balance_after=lot.current_quantity,
            performed_by=user,
            notes=notes,
        )

    @staticmethod
    def dispose_stock(lot, quantity, user=None, notes=""):
        """Record disposal of stock."""
        disposed = min(Decimal(str(quantity)), lot.current_quantity)
        lot.current_quantity -= disposed
        if lot.current_quantity <= 0:
            lot.current_quantity = 0
            lot.is_exhausted = True
        lot.save()

        StockMovement.objects.create(
            lot=lot,
            movement_type=StockMovement.MovementType.DISPOSAL,
            quantity=-disposed,
            balance_after=lot.current_quantity,
            performed_by=user,
            notes=notes,
        )


class AlertService:
    """Service for stock alerts."""

    @staticmethod
    def get_low_stock_materials(pharmacy=None):
        """Return materials below minimum stock level."""
        materials = RawMaterial.objects.filter(is_deleted=False)
        if pharmacy:
            materials = materials.filter(pharmacy=pharmacy)
        return [m for m in materials if m.is_low_stock]

    @staticmethod
    def get_expiring_lots(pharmacy=None, days=30):
        """Return lots expiring within the given number of days."""
        threshold = timezone.now().date() + timezone.timedelta(days=days)
        qs = (
            Lot.objects.filter(
                is_exhausted=False,
                is_quarantined=False,
                expiry_date__lte=threshold,
            )
            .select_related("raw_material", "supplier")
            .order_by("expiry_date")
        )
        if pharmacy:
            qs = qs.filter(raw_material__pharmacy=pharmacy)
        return qs

    @staticmethod
    def get_expired_lots(pharmacy=None):
        """Return lots that are expired but not exhausted."""
        today = timezone.now().date()
        qs = (
            Lot.objects.filter(
                is_exhausted=False,
                expiry_date__lt=today,
            )
            .select_related("raw_material", "supplier")
            .order_by("expiry_date")
        )
        if pharmacy:
            qs = qs.filter(raw_material__pharmacy=pharmacy)
        return qs


class ProhibitedSubstanceService:
    """Service for checking formulations against prohibited substances (Deliberação 1985/2015)."""

    @staticmethod
    def check_formulation(formulation):
        """
        Check if a formulation contains prohibited substances.
        Returns list of (raw_material, prohibited_substance_name) tuples.
        """
        prohibited = ProhibitedSubstance.objects.values_list("cas_number", "name")
        cas_map = {cas: name for cas, name in prohibited if cas}
        name_map = {name.lower(): name for _, name in prohibited}

        violations = []
        for ing in formulation.ingredients.select_related("raw_material"):
            rm = ing.raw_material
            if rm.cas_number and rm.cas_number in cas_map:
                violations.append((rm, cas_map[rm.cas_number]))
            elif rm.name.lower() in name_map:
                violations.append((rm, name_map[rm.name.lower()]))
        return violations
