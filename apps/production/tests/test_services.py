from decimal import Decimal

from django.test import TestCase

from apps.core.models import Pharmacy
from apps.inventory.models import RawMaterial, Supplier
from apps.production.models import Formulation, FormulationIngredient
from apps.production.services import BatchCalculatorService


class BatchCalculatorServiceTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Calculator Pharmacy", slug="prod-svc-calc")
        self.supplier = Supplier.objects.create(name="S", nif="111000222", pharmacy=self.pharmacy)

        self.formulation = Formulation.objects.create(
            code="F-CALC",
            name="Pomada Teste",
            pharmaceutical_form="Pomada",
            base_quantity=Decimal("100.000"),
            base_unit="g",
            pharmacy=self.pharmacy,
        )

        self.acid = RawMaterial.objects.create(
            code="RM-ACID",
            name="Ácido Salicílico",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )
        self.vaseline = RawMaterial.objects.create(
            code="RM-VAS",
            name="Vaselina Branca",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )

        FormulationIngredient.objects.create(
            formulation=self.formulation,
            raw_material=self.acid,
            quantity=Decimal("5.0000"),
            unit="g",
            is_active_ingredient=True,
            order_of_addition=1,
        )
        FormulationIngredient.objects.create(
            formulation=self.formulation,
            raw_material=self.vaseline,
            quantity=Decimal("95.0000"),
            unit="g",
            is_active_ingredient=False,
            order_of_addition=2,
        )

    def test_scale_factor_10x(self):
        """1000g from a 100g base = 10x scale factor."""
        result = BatchCalculatorService.calculate(self.formulation, Decimal("1000"))

        self.assertEqual(result["scale_factor"], Decimal("10.0000"))
        self.assertEqual(result["desired_quantity"], Decimal("1000"))
        self.assertEqual(result["base_quantity"], Decimal("100.000"))
        self.assertEqual(result["base_unit"], "g")

    def test_ingredients_scaled_correctly_10x(self):
        """Each ingredient should be multiplied by the scale factor."""
        result = BatchCalculatorService.calculate(self.formulation, Decimal("1000"))

        ingredients = result["ingredients"]
        self.assertEqual(len(ingredients), 2)

        acid_result = ingredients[0]
        self.assertEqual(acid_result["raw_material"], self.acid)
        self.assertEqual(acid_result["original_quantity"], Decimal("5.0000"))
        self.assertEqual(acid_result["calculated_quantity"], Decimal("50.0000"))
        self.assertEqual(acid_result["unit"], "g")
        self.assertTrue(acid_result["is_active"])

        vaseline_result = ingredients[1]
        self.assertEqual(vaseline_result["raw_material"], self.vaseline)
        self.assertEqual(vaseline_result["original_quantity"], Decimal("95.0000"))
        self.assertEqual(vaseline_result["calculated_quantity"], Decimal("950.0000"))
        self.assertFalse(vaseline_result["is_active"])

    def test_total_weight_matches_desired(self):
        """Total weight of scaled ingredients should equal desired quantity."""
        result = BatchCalculatorService.calculate(self.formulation, Decimal("1000"))
        self.assertEqual(result["total_weight"], Decimal("1000.0000"))

    def test_scale_factor_1x_same_as_base(self):
        """Requesting the base quantity returns original amounts."""
        result = BatchCalculatorService.calculate(self.formulation, Decimal("100"))

        self.assertEqual(result["scale_factor"], Decimal("1.0000"))
        self.assertEqual(result["ingredients"][0]["calculated_quantity"], Decimal("5.0000"))
        self.assertEqual(result["ingredients"][1]["calculated_quantity"], Decimal("95.0000"))

    def test_scale_down_half(self):
        """50g from a 100g base = 0.5x."""
        result = BatchCalculatorService.calculate(self.formulation, Decimal("50"))

        self.assertEqual(result["scale_factor"], Decimal("0.5000"))
        self.assertEqual(result["ingredients"][0]["calculated_quantity"], Decimal("2.5000"))
        self.assertEqual(result["ingredients"][1]["calculated_quantity"], Decimal("47.5000"))
        self.assertEqual(result["total_weight"], Decimal("50.0000"))

    def test_scale_up_fractional(self):
        """250g from a 100g base = 2.5x."""
        result = BatchCalculatorService.calculate(self.formulation, Decimal("250"))

        self.assertEqual(result["scale_factor"], Decimal("2.5000"))
        self.assertEqual(result["ingredients"][0]["calculated_quantity"], Decimal("12.5000"))
        self.assertEqual(result["ingredients"][1]["calculated_quantity"], Decimal("237.5000"))

    def test_very_small_quantity(self):
        """10g from a 100g base = 0.1x."""
        result = BatchCalculatorService.calculate(self.formulation, Decimal("10"))

        self.assertEqual(result["scale_factor"], Decimal("0.1000"))
        self.assertEqual(result["ingredients"][0]["calculated_quantity"], Decimal("0.5000"))
        self.assertEqual(result["ingredients"][1]["calculated_quantity"], Decimal("9.5000"))

    def test_very_large_quantity(self):
        """10kg (10000g) from a 100g base = 100x."""
        result = BatchCalculatorService.calculate(self.formulation, Decimal("10000"))

        self.assertEqual(result["scale_factor"], Decimal("100.0000"))
        self.assertEqual(result["ingredients"][0]["calculated_quantity"], Decimal("500.0000"))
        self.assertEqual(result["ingredients"][1]["calculated_quantity"], Decimal("9500.0000"))

    def test_string_quantity_converted(self):
        """Passing a string number should still work."""
        result = BatchCalculatorService.calculate(self.formulation, "500")

        self.assertEqual(result["scale_factor"], Decimal("5.0000"))
        self.assertEqual(result["ingredients"][0]["calculated_quantity"], Decimal("25.0000"))

    def test_desired_unit_matches_base_unit(self):
        """The desired_unit in the result should match the formulation's base_unit."""
        result = BatchCalculatorService.calculate(self.formulation, Decimal("1000"))
        self.assertEqual(result["desired_unit"], "g")

    def test_formulation_reference_in_result(self):
        """The result should contain a reference to the original formulation."""
        result = BatchCalculatorService.calculate(self.formulation, Decimal("1000"))
        self.assertEqual(result["formulation"], self.formulation)


class BatchCalculatorServiceEdgeCasesTest(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Edge Pharmacy", slug="prod-svc-edge")
        self.supplier = Supplier.objects.create(name="S", nif="333444555", pharmacy=self.pharmacy)

    def test_zero_base_quantity_defaults_to_100(self):
        """If base_quantity is 0, should default to 100."""
        formulation = Formulation.objects.create(
            code="F-ZERO",
            name="Zero Base",
            pharmaceutical_form="cream",
            base_quantity=Decimal("0"),
            base_unit="g",
            pharmacy=self.pharmacy,
        )
        material = RawMaterial.objects.create(
            code="RM-Z",
            name="Ingredient",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )
        FormulationIngredient.objects.create(
            formulation=formulation,
            raw_material=material,
            quantity=Decimal("10.0000"),
            unit="g",
            order_of_addition=1,
        )

        result = BatchCalculatorService.calculate(formulation, Decimal("200"))
        self.assertEqual(result["base_quantity"], Decimal("100"))
        self.assertEqual(result["scale_factor"], Decimal("2.0000"))
        self.assertEqual(result["ingredients"][0]["calculated_quantity"], Decimal("20.0000"))

    def test_formulation_with_no_ingredients(self):
        """A formulation with no ingredients should return empty list."""
        formulation = Formulation.objects.create(
            code="F-EMPTY",
            name="Empty",
            pharmaceutical_form="cream",
            base_quantity=Decimal("100"),
            base_unit="g",
            pharmacy=self.pharmacy,
        )

        result = BatchCalculatorService.calculate(formulation, Decimal("1000"))
        self.assertEqual(len(result["ingredients"]), 0)
        self.assertEqual(result["total_weight"], 0)

    def test_ml_base_unit(self):
        """Formulations with mL base unit should work correctly."""
        formulation = Formulation.objects.create(
            code="F-ML",
            name="Solução",
            pharmaceutical_form="Solução oral",
            base_quantity=Decimal("100.000"),
            base_unit="mL",
            pharmacy=self.pharmacy,
        )
        material = RawMaterial.objects.create(
            code="RM-ML",
            name="Propranolol",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )
        water = RawMaterial.objects.create(
            code="RM-W",
            name="Água Purificada",
            default_unit="mL",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )
        FormulationIngredient.objects.create(
            formulation=formulation,
            raw_material=material,
            quantity=Decimal("0.1000"),
            unit="g",
            is_active_ingredient=True,
            order_of_addition=1,
        )
        FormulationIngredient.objects.create(
            formulation=formulation,
            raw_material=water,
            quantity=Decimal("99.9000"),
            unit="mL",
            is_active_ingredient=False,
            order_of_addition=2,
        )

        result = BatchCalculatorService.calculate(formulation, Decimal("500"))
        self.assertEqual(result["base_unit"], "mL")
        self.assertEqual(result["desired_unit"], "mL")
        self.assertEqual(result["scale_factor"], Decimal("5.0000"))
        self.assertEqual(result["ingredients"][0]["calculated_quantity"], Decimal("0.5000"))
        self.assertEqual(result["ingredients"][1]["calculated_quantity"], Decimal("499.5000"))

    def test_rounding_precision(self):
        """Quantities should be rounded to 4 decimal places."""
        formulation = Formulation.objects.create(
            code="F-ROUND",
            name="Rounding Test",
            pharmaceutical_form="cream",
            base_quantity=Decimal("100.000"),
            base_unit="g",
            pharmacy=self.pharmacy,
        )
        material = RawMaterial.objects.create(
            code="RM-R",
            name="Active",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )
        FormulationIngredient.objects.create(
            formulation=formulation,
            raw_material=material,
            quantity=Decimal("3.3333"),
            unit="g",
            order_of_addition=1,
        )

        result = BatchCalculatorService.calculate(formulation, Decimal("300"))
        # 3.3333 * 3 = 9.9999
        self.assertEqual(result["ingredients"][0]["calculated_quantity"], Decimal("9.9999"))

    def test_rounding_with_repeating_factor(self):
        """Test with a factor that produces repeating decimals."""
        formulation = Formulation.objects.create(
            code="F-REP",
            name="Repeating Test",
            pharmaceutical_form="cream",
            base_quantity=Decimal("100.000"),
            base_unit="g",
            pharmacy=self.pharmacy,
        )
        material = RawMaterial.objects.create(
            code="RM-REP",
            name="Active",
            default_unit="g",
            preferred_supplier=self.supplier,
            pharmacy=self.pharmacy,
        )
        FormulationIngredient.objects.create(
            formulation=formulation,
            raw_material=material,
            quantity=Decimal("7.0000"),
            unit="g",
            order_of_addition=1,
        )

        # 7 * (333/100) = 7 * 3.33 = 23.31
        result = BatchCalculatorService.calculate(formulation, Decimal("333"))
        self.assertEqual(result["ingredients"][0]["calculated_quantity"], Decimal("23.3100"))

    def test_fixture_fgp001_1kg(self):
        """Integration test: load FGP-001 from fixtures, calculate for 1kg."""
        try:
            formulation = Formulation.objects.get(code="FGP-001")
        except Formulation.DoesNotExist:
            self.skipTest("FGP-001 fixture not loaded")

        result = BatchCalculatorService.calculate(formulation, Decimal("1000"))

        self.assertEqual(result["scale_factor"], Decimal("10.0000"))
        self.assertEqual(len(result["ingredients"]), 2)

        # Ácido Salicílico: 5g * 10 = 50g
        acid = next(i for i in result["ingredients"] if i["is_active"])
        self.assertEqual(acid["calculated_quantity"], Decimal("50.0000"))

        # Vaselina: 95g * 10 = 950g
        vaseline = next(i for i in result["ingredients"] if not i["is_active"])
        self.assertEqual(vaseline["calculated_quantity"], Decimal("950.0000"))

        self.assertEqual(result["total_weight"], Decimal("1000.0000"))
