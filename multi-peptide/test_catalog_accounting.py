"""Meaningful regression tests for complete accounting without fake chemistry."""
import csv
import json
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent
EXCLUSIONS = {'lipotropic-c', 'shb', 'lipotropic-b', 'vitamin-b12', 'glow-blend', 'bpc-157-tb-500-blend', 'reconstitution-solution', 'klow-peptide'}
UNRESOLVED = {'foxo4-10mg', 'adamax', 'ahk-cu-10000mg'}

class AccountingTests(unittest.TestCase):
    def test_withheld_nomenclature_conflict_alone_prevents_scientific_completeness(self):
        from catalog_accounting import derive
        inventory=json.loads((BASE/'catalog-coa-inventory.json').read_text(encoding='utf-8-sig'))
        p=next(p for p in inventory['products'] if p['slug']=='thymalin-10mg')
        _,_,unresolved,summary=derive([p],[])
        self.assertEqual(len(unresolved), 1)
        self.assertTrue(summary['full_catalog_accounted_for'])
        self.assertFalse(summary['full_catalog_molarity_complete'])
        self.assertEqual(summary['conditional_identity_conflict_product_slugs'],['thymalin-10mg'])
    def test_every_catalog_product_accounted_exactly_once(self):
        path = BASE/'catalog_molarity_accounting.csv'
        self.assertTrue(path.is_file(), 'Missing exhaustive catalog accounting ledger')
        with path.open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
        catalog = json.loads((BASE/'inputs/catalog-products.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(len(rows), 44)
        self.assertEqual({r['product_slug'] for r in rows}, {p['slug'] for p in catalog['products']})
        self.assertEqual({r['product_slug'] for r in rows if r['accounting_status']=='stoichiometry_withheld_pending_sequence_specification'}, UNRESOLVED)

    def test_only_demonstrated_non_single_species_are_excluded(self):
        path = BASE/'catalog_non_single_species_exclusions.csv'
        self.assertTrue(path.is_file(), 'Missing scientific mixture/solution exclusion ledger')
        with path.open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 8)
        self.assertEqual({r['product_slug'] for r in rows}, EXCLUSIONS)
        for row in rows:
            self.assertTrue(row['scientific_reason'])
            self.assertEqual(row['molarity_computed'], 'False')
            self.assertTrue(row['canonical_url'].endswith('/product/'+row['product_slug']+'/'))

    def test_full_catalog_science_stays_incomplete_while_identity_gaps_remain(self):
        inventory = json.loads((BASE/'catalog-coa-inventory.json').read_text(encoding='utf-8-sig'))
        self.assertIn('catalog_accounting', inventory, 'Accounting must be explicit in inventory')
        accounting = inventory['catalog_accounting']
        self.assertTrue(accounting['full_catalog_accounted_for'])
        self.assertFalse(accounting['full_catalog_molarity_complete'])
        self.assertEqual(set(accounting['unresolved_identity_product_slugs']), UNRESOLVED)

if __name__ == '__main__':
    unittest.main()
