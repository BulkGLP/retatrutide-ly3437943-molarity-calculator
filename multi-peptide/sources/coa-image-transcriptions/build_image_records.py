"""Normalize manually visually transcribed raster COA fields; never OCR/infer results."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
acquisition = json.loads((ROOT / 'inputs/coa-acquisition.json').read_text(encoding='utf-8-sig'))['records']
images = [r for r in acquisition if Path(r['source_file']).suffix.lower() in ('.png', '.jpg', '.jpeg')]
manual = json.loads((HERE / 'visual-transcriptions.json').read_text(encoding='utf-8'))
assert len(images) == len(manual) == 25
by_name = {r['file']: r for r in manual}
assert len(by_name) == 25
assert set(by_name) == {Path(r['source_file']).name for r in images}

def date_iso(value):
    if not value:
        return None
    for fmt in ('%m/%d/%Y', '%m/%d/%y'):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(value)

def evidence(source, literal, location, note=None):
    row = {'source_file': source, 'literal': literal, 'location': location, 'verification': 'Original raster file visually reviewed using tools.view_image.'}
    if note:
        row['note'] = note
    return row

output = []
for src in images:
    row = by_name[Path(src['source_file']).name]
    actual_hash = hashlib.sha256((ROOT / src['source_file']).read_bytes()).hexdigest()
    assert actual_hash == src['sha256'], src['source_file']
    pct_literal = None if row['purity'] is None else (f"{row['purity']:.3f}%" if row['purity'] in (99.762, 99.412, 99.641) else f"{row['purity']:.2f}%")
    chromate = row['report'] == '31112'
    january = row['file'].startswith('Bulk260113')
    report_label = 'report #' if chromate else 'Accession Number' if january else 'Accession #'
    content_label = 'Net Peptide Content' if january else 'Net Content'
    reported_label = row.get('reported_label', 'Reported Date' if january else 'Reported')
    received_label = 'Sample received' if chromate else 'Received Date' if january else 'Received'
    record = {
        'report_id': row['report'],
        'archive_report_id': src['archive_record']['reportId'],
        'product_slug': src['product_slug'],
        'product_label': row['product'],
        'nominal_label': re.search(r'(\d+(?:\.\d+)?)\s*(mg|mL)', row['product']).group(0) if re.search(r'(\d+(?:\.\d+)?)\s*(mg|mL)', row['product']) else None,
        'lot': row['lot'],
        'nominal_mass_mg': row.get('mass'),
        'nominal_volume_ml': row.get('volume'),
        'reported_hplc_purity_percent': row['purity'],
        'reported_content': row['content'],
        'reported_content_value': float(re.match(r'^([0-9.]+)', row['content']).group(1)) if row['content'] else None,
        'reported_content_unit': 'mg' if row['content'] and row['content'].endswith(' mg') else None,
        'received_date': date_iso(row['received']),
        'reported_date': date_iso(row['reported']),
        'reported_date_source_label': reported_label,
        'test_date': date_iso(row.get('test')),
        'purity_method': row.get('method'),
        'purity_method_detail': row.get('method_detail'),
        'formulation': None,
        'other_method': row.get('other_method'),
        'other_results': row.get('other_results', {}),
        'access_code': row.get('access_code'),
        'source_file': src['source_file'],
        'source_url': src['source_url'],
        'source_sha256': actual_hash,
        'source_sha256_verified': True,
        'verification_method': 'visual_review_of_original_raster',
        'review_method': 'visual_review_of_original_raster',
        'notes': row.get('notes', []),
    }
    if row['report'] != src['archive_record']['reportId']:
        record['notes'].append('The report_id follows the actual document; archive_report_id preserves the archive identifier for joins.')
    record['field_evidence'] = {
        'report_id': evidence(src['source_file'], f"{report_label}: {row['report']}", 'Report header; also footer where printed'),
        'product_slug': {'source_file': 'inputs/coa-acquisition.json', 'literal': src['product_slug'], 'verification': 'Archive source-to-product mapping; not claimed to be printed on COA.'},
        'product_label': evidence(src['source_file'], 'Product: ' + row['product'], 'Sample Summary/Product table'),
        'lot': evidence(src['source_file'], None if row['lot'] is None else 'Lot: ' + row['lot'], 'Report header/Product table', 'Not reported in source' if row['lot'] is None else None),
        'nominal_mass_mg': evidence(src['source_file'], 'Product: ' + row['product'] if row.get('mass') is not None else None, 'Sample Summary/Product table', 'Label mass only; not substituted with measured content' if row.get('mass') is not None else 'No nominal sample mass reported'),
        'nominal_volume_ml': evidence(src['source_file'], 'Product: ' + row['product'] if row.get('volume') is not None else None, 'Product table', 'Nominal label volume only' if row.get('volume') is not None else 'No nominal sample volume reported'),
        'reported_hplc_purity_percent': evidence(src['source_file'], None if pct_literal is None else 'Purity: ' + pct_literal, 'Sample Summary/Purity or Product/Purity table', 'No analytical purity value reported; no value inferred from labels or footer' if pct_literal is None else None),
        'reported_content': evidence(src['source_file'], None if row['content'] is None else content_label + ': ' + row['content'], 'Sample Summary or Product table', 'No measured net content reported; nominal sample label excluded' if row['content'] is None else None),
        'received_date': evidence(src['source_file'], received_label + ': ' + row['received'], 'Report header'),
        'reported_date': evidence(src['source_file'], reported_label + ': ' + row['reported'], 'Report footer' if chromate else 'Report header'),
        'test_date': evidence(src['source_file'], None if not row.get('test') else row.get('test_label', 'Test date') + ': ' + row['test'], 'Report header', 'No explicit test/analysis date; received/reported dates not substituted' if not row.get('test') else None),
        'purity_method': evidence(src['source_file'], row.get('method'), 'Analytical Results/Method band', 'No purity method asserted for an endotoxin-only or sterility-only result' if row.get('method') is None else 'Literal method preserved; no RP-HPLC designation inferred'),
    }
    lines = [f"Source: {src['source_file']}", f"SHA256: {actual_hash}", 'Verification: visual review of original source raster', f"{report_label}: {row['report']}", f"Product: {row['product']}", 'Lot: ' + str(row['lot']), f"{received_label}: {row['received']}", f"{reported_label}: {row['reported']}"]
    if row.get('test'):
        lines.append(row.get('test_label', 'Test date') + ': ' + row['test'])
    lines.extend(['Purity: ' + (pct_literal or '[not reported]'), content_label + ': ' + (row['content'] or '[not reported]'), 'Purity method: ' + (row.get('method') or '[not reported]')])
    if row.get('method_detail'):
        lines.append('Method: ' + row['method_detail'])
    if row.get('other_method'):
        lines.append('Other method: ' + row['other_method'])
    for key, val in row.get('other_results', {}).items():
        lines.append(key + ': ' + val)
    for note in record['notes']:
        lines.append('Review note: ' + note)
    transcript_path = HERE / (row['file'] + '.txt')
    transcript_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    record['transcription_file'] = transcript_path.relative_to(ROOT).as_posix()
    record['transcription_sha256'] = hashlib.sha256(transcript_path.read_bytes()).hexdigest()
    record['field_evidence']['nominal_label'] = evidence(src['source_file'], 'Product: ' + row['product'] if record['nominal_label'] is not None else None, 'Sample Summary/Product table', 'Nominal amount extracted only from printed product label')
    record['field_evidence']['formulation'] = evidence(src['source_file'], None, 'Whole report', 'No explicit formulation designation transcribed; do not infer mannitol-free or standard from report')
    for field, item in record['field_evidence'].items():
        item['evidence_file'] = 'inputs/coa-acquisition.json' if field == 'product_slug' else record['transcription_file']
        item['evidence_sha256'] = hashlib.sha256((ROOT / item['evidence_file']).read_bytes()).hexdigest()
        if item['literal'] is not None:
            assert item['literal'] in (ROOT / item['evidence_file']).read_text(encoding='utf-8-sig'), (row['file'], field, item['literal'])
    output.append(record)

result = {'schema': 'bulkglp-coa-image-transcriptions-v1', 'reviewed_at_utc': datetime.now(timezone.utc).isoformat(), 'record_count': len(output), 'source_hashes_verified': len(output), 'method': 'Independent visual review of all 25 original raster COAs; normalized fields anchored to literal per-field evidence. Archive metadata is mapping/context only.', 'limitations': ['No HPLC method was renamed RP-HPLC.', 'No reported/received date was inferred to be a test date.', 'Endotoxin-only and sterility-only reports carry null HPLC purity.', 'Reported content and nominal sample mass/volume are separate fields.', 'Source authenticity beyond downloaded-file integrity was not independently established by this transcription task.'], 'records': output}
dest = ROOT / 'inputs/coa-image-records.json'
dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'output': str(dest), 'records': len(output), 'hashes_verified': len(output), 'null_purity': sum(x['reported_hplc_purity_percent'] is None for x in output), 'explicit_test_date': [x['report_id'] for x in output if x['test_date']], 'archive_report_id_differences': [{'archive': x['archive_report_id'], 'actual': x['report_id']} for x in output if x['archive_report_id'] != x['report_id']]}, ensure_ascii=False))
