"""Release contract: accounted-for withheld identities may publish; broken evidence may not."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import verify_multi_peptide_registry as verifier

BASE = Path(__file__).resolve().parent
PENDING = {'foxo4-10mg', 'adamax', 'ahk-cu-10000mg'}
CONFLICT = 'thymalin-10mg'

class ReleaseGateTests(unittest.TestCase):
    def copy_release(self):
        temporary = tempfile.TemporaryDirectory(prefix='r3-release-gate-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'release'
        shutil.copytree(BASE, root, ignore=shutil.ignore_patterns('__pycache__'))
        return root

    def test_complete_accounting_can_publish_while_molarity_is_incomplete(self):
        result = verifier.verify(BASE, online=False)
        self.assertEqual(result['errors'], [])
        self.assertFalse(result['full_catalog_molarity_complete'])
        self.assertIs(result.get('publication_ready'), True)

    def test_machine_readable_result_keeps_three_conditional_reference_scopes(self):
        result = verifier.verify(BASE, online=False)
        self.assertEqual(result.get('conditional_reference_product_slugs'), ['ghk-cu', 'ghk-cu-10000mg', 'tb-500'])
        self.assertEqual(result.get('nomenclature_conflict_product_slugs'), ['thymalin-10mg'])

    def test_four_withheld_products_have_no_assigned_mass_or_matrix(self):
        inventory = json.loads((BASE/'catalog-coa-inventory.json').read_text(encoding='utf-8'))
        with (BASE/'catalog_molarity_accounting.csv').open(encoding='utf-8', newline='') as stream:
            dispositions = {r['product_slug']: r for r in csv.DictReader(stream)}
        with (BASE/'multi_peptide_molarity_matrix.csv').open(encoding='utf-8', newline='') as stream:
            matrix_slugs = {r['product_slug'] for r in csv.DictReader(stream)}
        for product in inventory['products']:
            slug = product['slug']
            if slug not in PENDING | {CONFLICT}:
                continue
            self.assertNotIn(slug, matrix_slugs)
            self.assertIsNone(product['chemical_reference']['molar_mass_g_mol'])
            self.assertFalse(product['chemical_reference']['allowed_molarity'])
            wanted = 'stoichiometry_withheld_catalog_coa_nomenclature_conflict' if slug == CONFLICT else 'stoichiometry_withheld_pending_sequence_specification'
            self.assertEqual(dispositions[slug]['accounting_status'], wanted)

    def test_missing_accounting_row_blocks_publication(self):
        root = self.copy_release()
        path = root/'catalog_molarity_accounting.csv'
        lines = path.read_text(encoding='utf-8').splitlines()
        path.write_text('\n'.join(lines[:-1])+'\n', encoding='utf-8')
        result = verifier.verify(root, online=False)
        self.assertTrue(result['errors'])
        self.assertIs(result.get('publication_ready'), False)

    def test_missing_disclosure_blocks_publication(self):
        root = self.copy_release()
        path = root/'site-preview/compounds/retatrutide/index.html'
        content = path.read_text(encoding='utf-8')
        path.write_text(content.replace('Chromatographic area purity is not net peptide content', 'Purity is content'), encoding='utf-8')
        result = verifier.verify(root, online=False)
        self.assertTrue(result['errors'])
        self.assertIs(result.get('publication_ready'), False)

    def test_sitemap_omission_blocks_publication(self):
        root = self.copy_release()
        (root/'site-preview/sitemap.xml').write_text('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>', encoding='utf-8')
        result = verifier.verify(root, online=False)
        self.assertTrue(result['errors'], 'Missing 44 crawlable reference URLs must be rejected')
        self.assertIs(result.get('publication_ready'), False)

if __name__ == '__main__':
    unittest.main()
