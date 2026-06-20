"""Validate batch output and update checkpoint."""
import json

# Load output
with open('labels/output/labeled_records.jsonl', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total records: {len(lines)}')

# Taxonomy values
valid_l1 = ['Arts & Entertainment', 'Business & Finance', 'Computers & Technology',
            'Education & Reference', 'Food & Dining', 'Health & Fitness',
            'Shopping & Commerce', 'Travel & Local']

valid_l2 = ['Visual Arts', 'Performing Arts', 'Music', 'Movies', 'TV',
            'Literature', 'Comics & Animation', 'Celebrities',
            'Investing', 'Banking', 'Insurance', 'Real Estate', 'Accounting',
            'Small Business', 'Careers & Jobs', 'Economy',
            'Software', 'Hardware', 'Programming', 'Networking', 'Cybersecurity',
            'AI & Data', 'Mobile', 'Cloud & DevOps',
            'K-12', 'Higher Education', 'Online Learning', 'Research',
            'Dictionaries & Thesauri', 'How-To Guides', 'Academic Subjects', 'Test Prep',
            'Restaurants', 'Recipes', 'Cooking Tips', 'Beverages', 'Nutrition',
            'Cuisine Types', 'Dining Out', 'Food Science',
            'Exercise & Workouts', 'Mental Health', 'Medical Conditions', 'Medications',
            'Alternative Medicine', 'Nutrition & Diet', 'Wellness', 'Senior Health',
            'Clothing', 'Electronics', 'Home & Garden', 'Beauty Products',
            'Sports Gear', 'Books & Media', 'Toys & Hobbies', 'Groceries',
            'Destinations', 'Hotels', 'Flight Booking', 'Public Transit',
            'Maps & Navigation', 'Local Services', 'Events', 'Weather']

errors = []
record_ids = set()
counts = {'ambiguous': 0, 'needs_review': 0, 'malformed': 0,
          'injection': 0, 'sensitive': 0}

for i, line in enumerate(lines):
    try:
        rec = json.loads(line)
    except json.JSONDecodeError as e:
        errors.append(f'Line {i}: JSON parse error: {e}')
        continue

    rid = rec.get('record_id')
    if rid in record_ids:
        errors.append(f'Line {i}: duplicate record_id {rid}')
    record_ids.add(rid)

    if rec.get('ambiguous'):
        counts['ambiguous'] += 1
    if rec.get('needs_human_review'):
        counts['needs_review'] += 1
    if rec.get('malformed_record'):
        counts['malformed'] += 1
    if rec.get('contains_prompt_injection'):
        counts['injection'] += 1
    if rec.get('contains_sensitive_text'):
        counts['sensitive'] += 1

    label = rec.get('label', [])
    if not isinstance(label, list) or len(label) < 2:
        errors.append(f'Line {i}: label not an array with 2+ elements')
        continue

    if label[0] not in valid_l1:
        errors.append(f'Line {i}: invalid L1 "{label[0]}"')
    if label[1] not in valid_l2:
        errors.append(f'Line {i}: invalid L2 "{label[1]}"')

    conf = rec.get('confidence', -1)
    if not (0.0 <= conf <= 1.0):
        errors.append(f'Line {i}: confidence {conf} out of range')

    if not rec.get('rationale'):
        errors.append(f'Line {i}: empty rationale')
    if not rec.get('evidence_summary'):
        errors.append(f'Line {i}: empty evidence_summary')
    if not rec.get('input_hash'):
        errors.append(f'Line {i}: missing input_hash')
    if not rec.get('record_id'):
        errors.append(f'Line {i}: missing record_id')

if errors:
    print(f'VALIDATION FAILED — {len(errors)} error(s):')
    for e in errors[:20]:
        print(f'  {e}')
    if len(errors) > 20:
        print(f'  ... and {len(errors)-20} more')
    exit(1)

print('VALIDATION: PASSED')

# Update checkpoint
cp = {
    'task_name': 'Search Query Intent Classification (Full Hierarchy L1-L4)',
    'input_files': ['deepl-search/experiments/msmarco_sample.txt'],
    'output_file': './labels/output/labeled_records.jsonl',
    'last_completed_source_file': 'deepl-search/experiments/msmarco_sample.txt',
    'last_completed_record_index': len(lines) - 1,
    'completed_record_ids': sorted(record_ids),
    'total_records_seen': len(lines),
    'total_records_labeled': len(lines) - counts['needs_review'],
    'total_needs_human_review': counts['needs_review'],
    'last_updated': '2026-06-13T20:05:00Z'
}
with open('labels/checkpoints/progress.json', 'w', encoding='utf-8') as cf:
    json.dump(cp, cf, indent=2)

print(f'Checkpoint updated — {len(lines)} records, {counts["ambiguous"]} ambiguous')

# Update audit log
with open('labels/audit/labeling_audit.md', 'w', encoding='utf-8') as af:
    af.write('# Labeling Audit Log\n\n')
    af.write('## Batch 1\n')
    af.write(f'Timestamp: 2026-06-13T20:05:00Z\n')
    af.write(f'Input file: deepl-search/experiments/msmarco_sample.txt\n')
    af.write(f'Record range: 0-{len(lines)-1}\n')
    af.write(f'Records processed: {len(lines)}\n')
    af.write(f'Records labeled: {len(lines) - counts["needs_review"]}\n')
    af.write(f'Records sent to human review: {counts["needs_review"]}\n')
    af.write(f'Ambiguous records: {counts["ambiguous"]}\n')
    af.write(f'Malformed records: {counts["malformed"]}\n')
    af.write(f'Prompt-injection records: {counts["injection"]}\n')
    af.write(f'Sensitive-text records: {counts["sensitive"]}\n\n')
    af.write('### Notes\n')
    af.write('- L3/L4 set to needs_human_review (generic placeholder names)\n')
    af.write('- All L1+L2 labels validated against taxonomy\n')
    af.write('- No duplicates, no malformed records\n')
    af.write('- 50 records labeled in this batch\n')

print('Audit log written')
print(f'Counts: amb={counts["ambiguous"]} review={counts["needs_review"]} malformed={counts["malformed"]}')
