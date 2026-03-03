from decimal import Decimal, ROUND_HALF_UP

from .models import BatchCost


class BatchCostService:
    """Calculate batch cost per Portaria 769/2004 formula."""

    @staticmethod
    def calculate(batch, packaging_cost=Decimal("0"), preparation_fee=Decimal("0")):
        """
        Calculate batch cost breakdown.
        - Raw material cost: sum of (quantity_used * lot.cost_per_unit) for each usage
        - Packaging cost: provided externally
        - Preparation fee: provided externally
        """
        raw_cost = Decimal("0")
        for usage in batch.material_usage.select_related("lot"):
            unit_cost = usage.lot.cost_per_unit or Decimal("0")
            raw_cost += usage.quantity_used * unit_cost

        total = raw_cost + packaging_cost + preparation_fee

        cost, _ = BatchCost.objects.update_or_create(
            batch=batch,
            defaults={
                "raw_material_cost": raw_cost,
                "packaging_cost": packaging_cost,
                "preparation_fee": preparation_fee,
                "total_cost": total,
            },
        )
        return cost


class BatchCalculatorService:
    """Calculate ingredient quantities for a desired batch size."""

    @staticmethod
    def calculate(formulation, desired_quantity):
        """
        Scale ingredient quantities from the formulation's base to the desired quantity.

        Args:
            formulation: Formulation instance with ingredients
            desired_quantity: Decimal — desired total quantity in the formulation's base_unit

        Returns:
            dict with formulation info, scale factor, and scaled ingredient list
        """
        desired_quantity = Decimal(str(desired_quantity))
        base = formulation.base_quantity

        if base <= 0:
            base = Decimal("100")

        factor = desired_quantity / base
        precision = Decimal("0.0001")

        results = []
        for ing in formulation.ingredients.select_related("raw_material").all():
            calculated = (ing.quantity * factor).quantize(precision, rounding=ROUND_HALF_UP)
            results.append(
                {
                    "ingredient": ing,
                    "raw_material": ing.raw_material,
                    "original_quantity": ing.quantity,
                    "calculated_quantity": calculated,
                    "unit": ing.unit,
                    "is_active": ing.is_active_ingredient,
                }
            )

        return {
            "formulation": formulation,
            "base_quantity": base,
            "base_unit": formulation.base_unit,
            "desired_quantity": desired_quantity,
            "desired_unit": formulation.base_unit,
            "scale_factor": factor.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "ingredients": results,
            "total_weight": sum(r["calculated_quantity"] for r in results),
        }
