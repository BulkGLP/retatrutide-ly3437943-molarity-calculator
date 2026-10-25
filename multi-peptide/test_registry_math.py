import importlib.util
import unittest
from decimal import Decimal
from pathlib import Path

class RegistryMathTests(unittest.TestCase):
    def calculator(self):
        path = Path(__file__).with_name('registry_math.py')
        self.assertTrue(path.exists(), 'scientific calculator has not been implemented')
        spec = importlib.util.spec_from_file_location('registry_math', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.calculate

    def test_dimensionally_exact_reference(self):
        result = self.calculator()('10', '2', '1000')
        self.assertEqual(result, {'mass_concentration_mg_ml':'5.00000000', 'molarity_mM':'5.00000000', 'molarity_uM':'5000.00000000'})

    def test_retatrutide_independent_decimal_value(self):
        result = self.calculator()('10', '1', '4731.33')
        self.assertEqual(result['molarity_mM'], '2.11357060')
        self.assertEqual(result['molarity_uM'], '2113.57060277')

    def test_reject_nonpositive_missing_and_nonfinite(self):
        calc = self.calculator()
        for triple in [('10','0','1000'),('0','1','1000'),('10','1','-1'),('10','1',None),('10','1','NaN'),('Infinity','1','1000')]:
            with self.subTest(triple=triple), self.assertRaises(ValueError):
                calc(*triple)

    def test_scaling(self):
        calc=self.calculator()
        self.assertEqual(Decimal(calc('20','2','1000')['molarity_uM']), Decimal(calc('10','1','1000')['molarity_uM']))

if __name__ == '__main__':
    unittest.main()
