"""Exhaustive catalog accounting; exclusions are never computed molarities."""
import json
from collections import Counter

PENDING_WITHHELD = 'stoichiometry_withheld_pending_sequence_specification'
CONFLICT_WITHHELD = 'stoichiometry_withheld_catalog_coa_nomenclature_conflict'

SUPPLIER_REQUIREMENTS = {
    'ghk-cu': 'Active-lot signed specification: GHK ligand sequence/stereochemistry; ligand:copper ratio; charge/protonation; counterion and hydration state; quantitative net parent-complex mass per 100 mg labeled vial.',
    'ghk-cu-10000mg': 'Active-lot signed specification: GHK ligand sequence/stereochemistry; ligand:copper ratio; charge/protonation; counterion and hydration state; quantitative net parent-complex content of the 10 g powder.',
    'ahk-cu-10000mg': 'Active-lot signed specification: Ala-His-Lys stereochemistry; ligand:copper ratio; charge/protonation; hydrochloride or other counterion and hydration state; quantitative net parent-complex content of the 10 g powder.',
    'thymalin-10mg': 'Supplier must reconcile Thymalin catalog name with Thymulin report 2608100933; provide exact sequence/termini/stereochemistry and zinc state if a defined thymulin species, or the characterized composition and species count if a thymic extract/preparation.',
    'foxo4-10mg': 'Exact active-lot peptide sequence, D/L stereochemistry, terminal groups, cell-penetrating tag/linker, salt/hydration state and net parent-peptide mass. Confirm whether it is FOXO4-DRI, FOXO4-L or another FOXO4-derived construct.',
    'adamax': 'Exact active-lot peptide sequence/stereochemistry, N-acetyl group, structure and attachment site of adamantane, linker chemistry, terminal group, salt/hydration state and net parent-peptide mass; an unambiguous structure or validated registry identity.',
    'tb-500': 'Exact active-lot sequence, acetylation/terminal groups and stereochemistry; reconcile commercial TB-500 name and report 2605280346 Thymosin Beta-4 label; distinguish Ac-LKKTETQ fragment from full-length thymosin beta-4 and specify net parent-peptide mass.',
}

def derive(products, matrix):
    """Partition products, retaining identity gaps as gaps and nonpeptides separately."""
    matrix_counts = Counter(r['product_slug'] for r in matrix)
    ledger, exclusions, unresolved = [], [], []
    for p in products:
        c = p['chemical_reference']; slug = p['slug']
        common = dict(product_slug=slug, product_name=p['name'], canonical_url=p['canonical_url'],
            nominal_sizes=p['nominal_sizes'], offer_formats=[v['offer_format'] for v in p['variants']],
            reference_page='compounds/'+slug+'/index.html', molarity_computed=bool(matrix_counts[slug]),
            matrix_rows=matrix_counts[slug])
        state = c.get('identity_status')
        if state in ('unresolved_catalog_species', 'unresolved_catalog_coa_nomenclature_conflict'):
            status = CONFLICT_WITHHELD if state == 'unresolved_catalog_coa_nomenclature_conflict' else PENDING_WITHHELD
            reason = c['allowed_molarity_reason']
            unresolved.append(dict(common, original_flag_reason=reason, supplier_data_needed=SUPPLIER_REQUIREMENTS[slug],
                candidate_reference_count=len(c.get('candidate_references',[])),
                candidate_selection='No candidate selected; database identity does not establish catalog or lot identity.'))
        elif state in ('multi_component_formulation_no_single_molar_mass','formulation_specific_references_only'):
            status = 'non_single_species_exclusion'
            reason = c['allowed_molarity_reason']
            kind = 'multiple_formulation_product_listing' if state=='formulation_specific_references_only' else 'mixture_or_solution'
            exclusions.append(dict(common, exclusion_kind=kind, scientific_reason=reason,
                catalog_evidence_file='sources/catalog/'+slug+'.extracted.json', catalog_evidence_literal=p['description'],
                exclusion_scope='Product-level single molar mass/molarity only; no constituent concentration is inferred.'))
        elif c.get('allowed_molarity') and c.get('is_peptide') and matrix_counts[slug]:
            status = 'computed_peptide_reference'
            reason = c['allowed_molarity_reason']
        elif not c.get('is_peptide') and c.get('molar_mass_g_mol') and not c.get('allowed_molarity'):
            status = 'verified_non_peptide_reference_outside_matrix'
            reason = c['allowed_molarity_reason']
        else:
            status = 'unaccounted'
            reason = 'No valid accounting disposition established.'
        ledger.append(dict(common, accounting_status=status, reason=reason))
    counts = dict(Counter(r['accounting_status'] for r in ledger))
    complete_accounting = len(ledger)==len(products) and len({r['product_slug'] for r in ledger})==len(products) and not counts.get('unaccounted')
    conditional_conflicts=[r['product_slug'] for r in ledger if r['accounting_status']==CONFLICT_WITHHELD]
    summary = dict(full_catalog_accounted_for=bool(complete_accounting),
        full_catalog_molarity_complete=bool(complete_accounting and not unresolved and not conditional_conflicts),
        completeness_semantics='Full catalog accounting includes supported reference models, explicit non-single-species exclusions, nonpeptide references outside the peptide matrix, and explicit withheld stoichiometry dispositions. Publication readiness requires complete accounting and successful integrity/disclosure verification; it does not require invented masses or full mathematical completeness. Full catalog molarity remains false while sequence/specification gaps or the Thymalin catalog versus Thymulin/nonathymulin nomenclature conflict remain. This flag never represents measured lot concentrations.',
        products=len(products), disposition_counts=counts,
        unresolved_identity_product_slugs=[r['product_slug'] for r in ledger if r['accounting_status']==PENDING_WITHHELD],
        withheld_stoichiometry_product_slugs=[r['product_slug'] for r in unresolved],
        conditional_identity_conflict_product_slugs=conditional_conflicts,
        exclusions_are_computed_molarities=False,
        source_inventory_capture_date='2026-10-22', accounting_review_date='2026-10-25')
    return ledger, exclusions, unresolved, summary
