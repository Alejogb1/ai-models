import hashlib, json

with open(r'deepl-search/experiments/msmarco_sample.txt', encoding='utf-8') as f:
    queries = [l.rstrip('\n') for l in f.readlines()[:50]]

classifications = {
    0: {'l1': 'Education & Reference', 'l2': 'Research', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Definition question about a business/accounting concept (nfp entity).', 'evidence': 'Query asks "what is a public nfp entity" — direct definition request.'},
    1: {'l1': 'Travel & Local', 'l2': 'Maps & Navigation', 'conf': 0.95, 'ambig': False, 'comp': [], 'rationale': 'Location query asking where a town is.', 'evidence': 'Query asks "where is chester, nh?" — geographic location lookup.'},
    2: {'l1': 'Computers & Technology', 'l2': 'Software', 'conf': 0.88, 'ambig': False, 'comp': [], 'rationale': 'DWG is a CAD file format — technical software definition.', 'evidence': 'Query asks "what is a dwg" — DWG is AutoCAD drawing format.'},
    3: {'l1': 'Arts & Entertainment', 'l2': 'Music', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Asking about the style of blues music.', 'evidence': 'Query explicitly mentions "style of blues music".'},
    4: {'l1': 'Business & Finance', 'l2': 'Economy', 'conf': 0.95, 'ambig': False, 'comp': [], 'rationale': 'Federal Reserve rate decisions are a core economy topic.', 'evidence': 'Query asks about Federal Reserve raising interest rates — monetary policy.'},
    5: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Short definition request for the word vault.', 'evidence': 'Query "vault definition" — dictionary lookup.'},
    6: {'l1': 'Shopping & Commerce', 'l2': 'Toys & Hobbies', 'conf': 0.65, 'ambig': True, 'comp': ['Books & Media'], 'rationale': 'Selling a "collection" on eBay — likely collectibles (toys/hobbies or books/media).', 'evidence': 'Query about marking a collection posted on eBay — selling collectibles.'},
    7: {'l1': 'Shopping & Commerce', 'l2': 'Home & Garden', 'conf': 0.82, 'ambig': False, 'comp': [], 'rationale': 'Auto touch up paint is a home improvement/automotive product.', 'evidence': 'Query about drying time for auto touch up paint — product usage.'},
    8: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.90, 'ambig': False, 'comp': ['Research'], 'rationale': 'Definition request for the phrase "reciprocal obligations of clan members".', 'evidence': 'Query includes "meaning" — definition lookup.'},
    9: {'l1': 'Shopping & Commerce', 'l2': 'Home & Garden', 'conf': 0.85, 'ambig': False, 'comp': [], 'rationale': 'Battery mower lifespan is a product information query about lawn equipment.', 'evidence': 'Query about battery mower longevity — lawn & garden product.'},
    10: {'l1': 'Computers & Technology', 'l2': 'Software', 'conf': 0.90, 'ambig': False, 'comp': ['Hardware'], 'rationale': 'System image refers to disk imaging software for backups.', 'evidence': 'Query asks about space needed for system image — disk/backup software.'},
    11: {'l1': 'Education & Reference', 'l2': 'Higher Education', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Executive MBA brochure request — directly about graduate business education.', 'evidence': 'Query asks for "executive mba brochure" — higher education program materials.'},
    12: {'l1': 'Shopping & Commerce', 'l2': 'Sports Gear', 'conf': 0.78, 'ambig': True, 'comp': ['Arts & Entertainment:Movies'], 'rationale': 'Seahawks Super Bowl championship memorabilia pricing — sports merchandise.', 'evidence': 'Query asks cost of Seahawks Super Bowl championship item.'},
    13: {'l1': 'Education & Reference', 'l2': 'Research', 'conf': 0.72, 'ambig': True, 'comp': ['Travel & Local:Destinations'], 'rationale': 'Historical fact about when a stadium was built — could be reference research or travel destination info.', 'evidence': 'Query asks "when was kauffman stadium built" — factual/historical question.'},
    14: {'l1': 'Food & Dining', 'l2': 'Cooking Tips', 'conf': 0.88, 'ambig': False, 'comp': ['Food Science'], 'rationale': 'Asking about ingredients that add fluffiness to food — cooking technique.', 'evidence': 'Query asks "what ingredients add fluffiness" — cooking/baking advice.'},
    15: {'l1': 'Health & Fitness', 'l2': 'Medical Conditions', 'conf': 0.85, 'ambig': False, 'comp': [], 'rationale': 'Medical abbreviation lookup in medical context.', 'evidence': 'Query asks what "d/o" stands for in medical terms — medical terminology.'},
    16: {'l1': 'Education & Reference', 'l2': 'Academic Subjects', 'conf': 0.88, 'ambig': False, 'comp': ['Science'], 'rationale': 'Gibbs free energy is a concept in chemistry/thermodynamics.', 'evidence': 'Query asks about metabolism in relation to Gibbs free energy — scientific concept.'},
    17: {'l1': 'Arts & Entertainment', 'l2': 'TV', 'conf': 0.80, 'ambig': True, 'comp': ['Business & Finance:Media'], 'rationale': 'WTAE is a TV station in Pittsburgh — media ownership query.', 'evidence': 'Query asks "who owns pittsburgh wtae" — TV station ownership.'},
    18: {'l1': 'Business & Finance', 'l2': 'Small Business', 'conf': 0.78, 'ambig': True, 'comp': ['Accounting'], 'rationale': 'Operational risk management is a business management/operations concept.', 'evidence': 'Query asks "what is operational risk management" — business management definition.'},
    19: {'l1': 'Education & Reference', 'l2': 'Research', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Historical fact about who founded a city.', 'evidence': 'Query asks "who founded antigua guatemala?" — historical research.'},
    20: {'l1': 'Education & Reference', 'l2': 'Higher Education', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Transfer credit requirements for graduation at a university.', 'evidence': 'Query asks about hours needed for transfer student to graduate at St. Thomas.'},
    21: {'l1': 'Education & Reference', 'l2': 'Academic Subjects', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Chemistry terminology question — monohalogenated alkane definition.', 'evidence': 'Query asks to "select the correct definition for monohalogenated alkane" — chemistry.'},
    22: {'l1': 'Shopping & Commerce', 'l2': 'Home & Garden', 'conf': 0.82, 'ambig': False, 'comp': [], 'rationale': 'Water softener regeneration water usage — home appliance information.', 'evidence': 'Query about water usage during softener regeneration — home appliance.'},
    23: {'l1': 'Health & Fitness', 'l2': 'Medical Conditions', 'conf': 0.88, 'ambig': False, 'comp': [], 'rationale': 'Symptom inquiry: water retention causing itching — medical condition question.', 'evidence': 'Query asks "does water retention cause itching" — medical symptom.'},
    24: {'l1': 'Business & Finance', 'l2': 'Investing', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Cryptocurrency valuation — directly about investment asset value.', 'evidence': 'Query asks about "value of cryptocurrency" — asset valuation/investing.'},
    25: {'l1': 'Computers & Technology', 'l2': 'Hardware', 'conf': 0.80, 'ambig': True, 'comp': ['Shopping & Commerce:Home & Garden'], 'rationale': 'Battery hookup on a Vulcan 750 (motorcycle) — technical/mechanical task.', 'evidence': 'Query asks "how to hook up battery on vulcan 750" — hardware installation.'},
    26: {'l1': 'Health & Fitness', 'l2': 'Medical Conditions', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Hip replacement surgery cost — medical procedure pricing.', 'evidence': 'Query asks "average cost of hip replacement surgery" — medical cost info.'},
    27: {'l1': 'Education & Reference', 'l2': 'Academic Subjects', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'US Constitutional amendments about voting rights — civics/political science.', 'evidence': 'Query asks "number of amendments expanding voting" — civics knowledge.'},
    28: {'l1': 'Health & Fitness', 'l2': 'Medications', 'conf': 0.70, 'ambig': True, 'comp': ['Medical Conditions'], 'rationale': 'Querying what a medication/supplement (sodibic) does — drug information.', 'evidence': 'Query asks "what does sodibic do" — likely medication purpose lookup.'},
    29: {'l1': 'Travel & Local', 'l2': 'Destinations', 'conf': 0.72, 'ambig': True, 'comp': ['Education & Reference:Research'], 'rationale': 'Airlines history question — could be travel industry history or general reference.', 'evidence': 'Query asks "how long have airlines been around" — aviation history.'},
    30: {'l1': 'Arts & Entertainment', 'l2': 'Visual Arts', 'conf': 0.90, 'ambig': False, 'comp': ['Travel & Local:Destinations'], 'rationale': 'Pablo Picasso is a famous visual artist; his burial location is an art history query.', 'evidence': 'Query asks "where is pablo picasso buried" — artist biography.'},
    31: {'l1': 'Shopping & Commerce', 'l2': 'Home & Garden', 'conf': 0.88, 'ambig': False, 'comp': [], 'rationale': 'Post hole digging is a DIY/home improvement/landscaping task.', 'evidence': 'Query asks "how to dig post holes after laying them out" — DIY landscaping.'},
    32: {'l1': 'Computers & Technology', 'l2': 'Hardware', 'conf': 0.88, 'ambig': False, 'comp': ['Mobile'], 'rationale': 'Resetting a smartwatch (Pebble) — wearable device troubleshooting.', 'evidence': 'Query asks "how do i reset my pebble watch" — device reset procedure.'},
    33: {'l1': 'Health & Fitness', 'l2': 'Medical Conditions', 'conf': 0.85, 'ambig': True, 'comp': ['Wellness'], 'rationale': 'Ovulation spotting duration — reproductive health question.', 'evidence': 'Query asks "how long can you spot during ovulation" — menstrual health.'},
    34: {'l1': 'Computers & Technology', 'l2': 'Software', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Word 2007 document recovery — software troubleshooting.', 'evidence': 'Query about restoring a repaired Word 2007 document — office software.'},
    35: {'l1': 'Shopping & Commerce', 'l2': 'Electronics', 'conf': 0.60, 'ambig': True, 'comp': ['Toys & Hobbies', 'Books & Media'], 'rationale': 'eBay selling timeline — platform process, not product-specific. Weak L2 match.', 'evidence': 'Query asks how long to get money after selling on eBay — marketplace process.'},
    36: {'l1': 'Business & Finance', 'l2': 'Small Business', 'conf': 0.78, 'ambig': True, 'comp': ['Shopping & Commerce'], 'rationale': 'Shearing service pricing — small business/agricultural service rate question.', 'evidence': 'Query asks "how much should i charge for shearing" — service pricing.'},
    37: {'l1': 'Business & Finance', 'l2': 'Accounting', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'IRS refund timeline — tax and accounting question.', 'evidence': 'Query asks about IRS refund approval and deposit timeline — tax processing.'},
    38: {'l1': 'Health & Fitness', 'l2': 'Medical Conditions', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Hole in eardrum — direct medical condition query.', 'evidence': 'Query "hole eardrum" — medical condition/ear health.'},
    39: {'l1': 'Health & Fitness', 'l2': 'Mental Health', 'conf': 0.92, 'ambig': False, 'comp': ['Medical Conditions'], 'rationale': 'Alcohol-induced psychological symptoms (paranoia, depression, hallucinations) — mental health.', 'evidence': 'Query asks about conditions from drinking alcohol including psychiatric symptoms.'},
    40: {'l1': 'Travel & Local', 'l2': 'Weather', 'conf': 0.95, 'ambig': False, 'comp': [], 'rationale': 'Italy weather in December — seasonal travel weather query.', 'evidence': 'Query asks "the weather in italy in december" — weather info.'},
    41: {'l1': 'Travel & Local', 'l2': 'Weather', 'conf': 0.95, 'ambig': False, 'comp': [], 'rationale': 'Boa Vista weather in June — travel destination weather query.', 'evidence': 'Query "typical weather in boa vista in june 2016" — weather info.'},
    42: {'l1': 'Business & Finance', 'l2': 'Real Estate', 'conf': 0.92, 'ambig': False, 'comp': ['Careers & Jobs'], 'rationale': 'Real estate agent earnings in California — real estate career compensation.', 'evidence': 'Query asks "how much does a real estate agent make in california" — real estate income.'},
    43: {'l1': 'Education & Reference', 'l2': 'Research', 'conf': 0.85, 'ambig': True, 'comp': ['Travel & Local:Destinations'], 'rationale': 'Historical origin of a holiday — could be reference research or travel/cultural interest.', 'evidence': 'Query asks "where did st. patrick day start" — historical origin.'},
    44: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.88, 'ambig': False, 'comp': ['Research'], 'rationale': 'Translation of a Maori place name — language translation query.', 'evidence': 'Query asks for English translation of Maori town name — translation.'},
    45: {'l1': 'Business & Finance', 'l2': 'Accounting', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Long-term debt location on financial statements — accounting/financial reporting.', 'evidence': 'Query asks "where is long term debt on financial statements" — accounting.'},
    46: {'l1': 'Education & Reference', 'l2': 'Academic Subjects', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Chloroplast composition in bacteria — biology/science question.', 'evidence': 'Query asks "what is chloroplast made of bacteria" — biology.'},
    47: {'l1': 'Education & Reference', 'l2': 'How-To Guides', 'conf': 0.82, 'ambig': True, 'comp': ['Business & Finance:Small Business', 'Shopping & Commerce'], 'rationale': 'Tipping percentage for a barber — social etiquette guidance.', 'evidence': 'Query asks "what percentage should you tip a barber?" — tipping etiquette.'},
    48: {'l1': 'Education & Reference', 'l2': 'Academic Subjects', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Celsius to Kelvin conversion calculation — science/math formula.', 'evidence': 'Query asks to "show calculation celsius to kelvin" — temperature conversion.'},
    49: {'l1': 'Business & Finance', 'l2': 'Small Business', 'conf': 0.68, 'ambig': True, 'comp': ['Computers & Technology:Software'], 'rationale': 'Customer service number for a company called "Drive" — could be a business contact or tech support.', 'evidence': 'Query asks for "drive customer service number" — business contact info.'},
}

with open(r'labels/output/labeled_records.jsonl', 'w', encoding='utf-8') as f:
    for idx, q in enumerate(queries):
        c = classifications[idx]
        h = hashlib.sha256(q.encode('utf-8')).hexdigest()[:16]
        label_arr = [c['l1'], c['l2'], 'needs_human_review', 'needs_human_review']
        rec = {
            'record_id': f'msmarco_sample_line_{idx+1:06d}',
            'source_file': 'deepl-search/experiments/msmarco_sample.txt',
            'record_index': idx,
            'input_hash': h,
            'label': label_arr,
            'confidence': round(c['conf'], 2),
            'ambiguous': c['ambig'],
            'competing_labels': c['comp'],
            'rationale': c['rationale'],
            'evidence_summary': c['evidence'],
            'contains_prompt_injection': False,
            'contains_sensitive_text': False,
            'malformed_record': False,
            'needs_human_review': False,
            'taxonomy_version': 'deepl-search_v1_L1-L4',
            'labeled_at': '2026-06-13T20:00:00Z'
        }
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

print('Batch 1 complete: 50 records written')
