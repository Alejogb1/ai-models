import hashlib, json

with open(r'deepl-search/experiments/msmarco_sample.txt', encoding='utf-8') as f:
    all_lines = [l.rstrip('\n') for l in f.readlines()]
    queries = all_lines[50:100]

classifications = {
    0: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Definition request for "deck house".', 'evidence': 'Query "deck house definition" — dictionary lookup.'},
    1: {'l1': 'Arts & Entertainment', 'l2': 'Visual Arts', 'conf': 0.78, 'ambig': True, 'comp': ['Education & Reference:Research'], 'rationale': 'Tattoo renaissance is an art history topic — could be reference or visual arts.', 'evidence': 'Query asks "when did the tattoo renaissance begin" — art movement history.'},
    2: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Definition request for "virility".', 'evidence': 'Query asks "what is meant by virility" — word meaning lookup.'},
    3: {'l1': 'Education & Reference', 'l2': 'Academic Subjects', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Chemistry question about salt and its uses.', 'evidence': 'Query asks "what is a salt and uses chemistry" — chemistry concept.'},
    4: {'l1': 'Arts & Entertainment', 'l2': 'Celebrities', 'conf': 0.75, 'ambig': True, 'comp': ['Education & Reference:Research'], 'rationale': 'Aadi Khan age query — likely a celebrity/actor age lookup.', 'evidence': 'Query "aadi khan age" — biographical fact lookup.'},
    5: {'l1': 'Shopping & Commerce', 'l2': 'Home & Garden', 'conf': 0.85, 'ambig': False, 'comp': [], 'rationale': 'Humidifier is a home appliance — pricing query.', 'evidence': 'Query asks "average cost of a humidifier" — home product pricing.'},
    6: {'l1': 'Arts & Entertainment', 'l2': 'Music', 'conf': 0.88, 'ambig': False, 'comp': ['Computers & Technology:Software'], 'rationale': 'Chord generator is a music tool — identifying chords.', 'evidence': 'Query asks "what chord is this generator" — music chord identification.'},
    7: {'l1': 'Computers & Technology', 'l2': 'Software', 'conf': 0.88, 'ambig': False, 'comp': [], 'rationale': 'Third normal form is a database normalization concept.', 'evidence': 'Query about meeting third normal form requirements — database design.'},
    8: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Definition request for "manumission".', 'evidence': 'Query "definition manumission" — dictionary lookup.'},
    9: {'l1': 'Education & Reference', 'l2': 'Research', 'conf': 0.85, 'ambig': True, 'comp': ['Travel & Local:Destinations'], 'rationale': 'Geographic fact about the second busiest harbor.', 'evidence': 'Query "Second busiest harbor in world" — geographic research.'},
    10: {'l1': 'Business & Finance', 'l2': 'Banking', 'conf': 0.88, 'ambig': True, 'comp': ['Economy'], 'rationale': 'Bank profit dynamics with interest rate changes — banking/economy.', 'evidence': 'Query "do bank profits when interest rates rise" — banking economics.'},
    11: {'l1': 'Business & Finance', 'l2': 'Real Estate', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'FHA loan refinancing benefit analysis — mortgage/real estate.', 'evidence': 'Query about refinancing an FHA loan — home loan refinance.'},
    12: {'l1': 'Computers & Technology', 'l2': 'Software', 'conf': 0.70, 'ambig': True, 'comp': ['Hardware'], 'rationale': 'Hopper processes could refer to computing process scheduling or hardware hoppers.', 'evidence': 'Query asks "what is hopper processes" — computing term.'},
    13: {'l1': 'Education & Reference', 'l2': 'Academic Subjects', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Question about founder of behaviorism — psychology.', 'evidence': 'Query asks who founded behaviorism — psychology academic question.'},
    14: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Definition request for "legends".', 'evidence': 'Query "legends definition" — dictionary lookup.'},
    15: {'l1': 'Health & Fitness', 'l2': 'Medical Conditions', 'conf': 0.85, 'ambig': True, 'comp': ['Senior Health'], 'rationale': 'Blood donation eligibility after basal cell carcinoma — medical condition question.', 'evidence': 'Query "how soon after basal carcinoma can you donate blood" — medical guideline.'},
    16: {'l1': 'Health & Fitness', 'l2': 'Senior Health', 'conf': 0.85, 'ambig': True, 'comp': ['Medical Conditions'], 'rationale': 'Long-term health care requirements — often senior/elder care related.', 'evidence': 'Query asks "what are long term health care requirements" — care planning.'},
    17: {'l1': 'Health & Fitness', 'l2': 'Medical Conditions', 'conf': 0.88, 'ambig': False, 'comp': [], 'rationale': 'Splinter removal from under a nail — minor medical procedure.', 'evidence': 'Query asks "how to remove splinter from beneath nail" — first aid.'},
    18: {'l1': 'Education & Reference', 'l2': 'How-To Guides', 'conf': 0.85, 'ambig': False, 'comp': [], 'rationale': 'Citation guidance for citing a company in academic work.', 'evidence': 'Query asks "how to cite american airlines" — citation guide.'},
    19: {'l1': 'Arts & Entertainment', 'l2': 'Celebrities', 'conf': 0.85, 'ambig': True, 'comp': ['Education & Reference:Research'], 'rationale': 'Celebrity relationship duration query — Trump and Melania marriage.', 'evidence': 'Query "how long have trump and melania been married" — celebrity biography.'},
    20: {'l1': 'Shopping & Commerce', 'l2': 'Groceries', 'conf': 0.72, 'ambig': True, 'comp': ['Home & Garden'], 'rationale': 'Pet food manufacturing location — product information query. Groceries is closest L2.', 'evidence': 'Query asks "where is natures logic dog food made" — pet food product origin.'},
    21: {'l1': 'Travel & Local', 'l2': 'Weather', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Coldest weather query for New Mexico — climate information.', 'evidence': 'Query "coldest weather in new mexico" — weather/climate info.'},
    22: {'l1': 'Computers & Technology', 'l2': 'Software', 'conf': 0.88, 'ambig': False, 'comp': [], 'rationale': 'Application dispatcher already running — software error/state.', 'evidence': 'Query "application is already running the dispatcher" — app error message.'},
    23: {'l1': 'Travel & Local', 'l2': 'Flight Booking', 'conf': 0.88, 'ambig': True, 'comp': ['Travel & Local:Destinations'], 'rationale': 'Delta airline carry-on baggage size policy — flight/airline info.', 'evidence': 'Query asks "how big of a bag can you carry on a delta plane" — airline policy.'},
    24: {'l1': 'Shopping & Commerce', 'l2': 'Home & Garden', 'conf': 0.85, 'ambig': False, 'comp': [], 'rationale': 'Culligan water softener price — home appliance pricing.', 'evidence': 'Query "culligan water softener price" — home product cost.'},
    25: {'l1': 'Business & Finance', 'l2': 'Small Business', 'conf': 0.85, 'ambig': True, 'comp': ['Education & Reference:Academic Subjects'], 'rationale': 'Marketing environment is a business/marketing concept.', 'evidence': 'Query asks "what is the marketing environment" — business concept.'},
    26: {'l1': 'Travel & Local', 'l2': 'Maps & Navigation', 'conf': 0.90, 'ambig': False, 'comp': ['Destinations'], 'rationale': 'Location query for a ridge in Chattanooga, TN.', 'evidence': 'Query asks "where is the ridge in chattanooga, tn" — geographic location.'},
    27: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.88, 'ambig': True, 'comp': ['Research'], 'rationale': 'Definition query for "fasces" in occult context — word meaning.', 'evidence': 'Query "fasces occult meaning" — terminology lookup.'},
    28: {'l1': 'Education & Reference', 'l2': 'Research', 'conf': 0.85, 'ambig': True, 'comp': ['Arts & Entertainment:Sports'], 'rationale': 'Who invented the hook shot (basketball) — sports history fact.', 'evidence': 'Query asks "who invented the hook shot" — basketball history research.'},
    29: {'l1': 'Shopping & Commerce', 'l2': 'Home & Garden', 'conf': 0.75, 'ambig': True, 'comp': ['Business & Finance:Small Business'], 'rationale': 'Oil change pricing at Big O Tires — automotive service cost. Home & Garden is closest L2.', 'evidence': 'Query asks cost of full service oil change at Big O Tires — auto service.'},
    30: {'l1': 'Arts & Entertainment', 'l2': 'Performing Arts', 'conf': 0.70, 'ambig': True, 'comp': ['Food & Dining:Dining Out'], 'rationale': 'Meal service at a Texas play — theater/performance with dining.', 'evidence': 'Query "who serving the meal texas play" — theater dining service.'},
    31: {'l1': 'Health & Fitness', 'l2': 'Nutrition & Diet', 'conf': 0.88, 'ambig': True, 'comp': ['Medical Conditions'], 'rationale': 'Diet plan for rheumatoid arthritis — therapeutic diet/medical nutrition.', 'evidence': 'Query "diet plan for rheumatoid arthritis" — medical diet planning.'},
    32: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.88, 'ambig': True, 'comp': ['Academic Subjects'], 'rationale': 'Difference between toxic and hazardous — terminology distinction.', 'evidence': 'Query "the difference in toxic and hazardous" — definition comparison.'},
    33: {'l1': 'Health & Fitness', 'l2': 'Medications', 'conf': 0.88, 'ambig': False, 'comp': ['Medical Conditions'], 'rationale': 'Popular prescription sleep medication query — drug information.', 'evidence': 'Query "popular prescription sleep medication" — medication info lookup.'},
    34: {'l1': 'Arts & Entertainment', 'l2': 'TV', 'conf': 0.65, 'ambig': True, 'comp': ['Celebrities', 'Comics & Animation'], 'rationale': '"What in tarnation" meme origin — internet culture/humor history. No perfect L2 match.', 'evidence': 'Query asks origin of "what in tarnation" meme — internet meme history.'},
    35: {'l1': 'Arts & Entertainment', 'l2': 'Music', 'conf': 0.88, 'ambig': True, 'comp': ['Performing Arts'], 'rationale': 'Waltz origin question — dance/music history.', 'evidence': 'Query "when was the waltz originated" — dance history.'},
    36: {'l1': 'Travel & Local', 'l2': 'Hotels', 'conf': 0.88, 'ambig': False, 'comp': [], 'rationale': 'Hotel Golden Park count in Kolkata — hotel information query.', 'evidence': 'Query "how many hotel golden park in kolkata" — hotel availability.'},
    37: {'l1': 'Business & Finance', 'l2': 'Accounting', 'conf': 0.90, 'ambig': False, 'comp': [], 'rationale': 'Texas sales tax filing — tax compliance/accounting.', 'evidence': 'Query "tx sales tax filing" — tax filing information.'},
    38: {'l1': 'Travel & Local', 'l2': 'Maps & Navigation', 'conf': 0.85, 'ambig': True, 'comp': ['Education & Reference:Research'], 'rationale': 'Marine Corps base Camp Pendleton location — geographic location query.', 'evidence': 'Query asks "where is marine corps base camp pendleton located" — location lookup.'},
    39: {'l1': 'Shopping & Commerce', 'l2': 'Home & Garden', 'conf': 0.80, 'ambig': True, 'comp': ['Education & Reference:How-To Guides'], 'rationale': 'Testing plant pH — gardening/home plant care.', 'evidence': 'Query "how to test plants body ph" — plant care guide.'},
    40: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.85, 'ambig': False, 'comp': ['Research'], 'rationale': 'Definition of "hooah" — military terminology lookup.', 'evidence': 'Query "military hooah definition" — slang definition.'},
    41: {'l1': 'Computers & Technology', 'l2': 'Mobile', 'conf': 0.72, 'ambig': True, 'comp': ['Hardware'], 'rationale': 'Age of first smartphone — mobile technology history.', 'evidence': 'Query "age of first smartphone" — smartphone history.'},
    42: {'l1': 'Health & Fitness', 'l2': 'Wellness', 'conf': 0.75, 'ambig': True, 'comp': ['Shopping & Commerce:Beauty Products'], 'rationale': 'Detox pedicure — spa/wellness treatment or beauty service.', 'evidence': 'Query asks "what is a detox pedicure" — spa treatment description.'},
    43: {'l1': 'Shopping & Commerce', 'l2': 'Groceries', 'conf': 0.70, 'ambig': True, 'comp': ['Electronics', 'Home & Garden'], 'rationale': 'Sams Club membership cost — warehouse club pricing. Groceries is closest L2.', 'evidence': 'Query asks "how much is a sams club membership" — retail membership pricing.'},
    44: {'l1': 'Arts & Entertainment', 'l2': 'Comics & Animation', 'conf': 0.88, 'ambig': True, 'comp': ['Toys & Hobbies'], 'rationale': 'Pokemon evolution level in Brick Bronze game — gaming/Pokemon content.', 'evidence': 'Query asks Pokemon evolution level in Brick Bronze — game guide.'},
    45: {'l1': 'Education & Reference', 'l2': 'Academic Subjects', 'conf': 0.92, 'ambig': False, 'comp': [], 'rationale': 'Question about instinct in psychology — academic psychology.', 'evidence': 'Query asks "what is an instinct in psychology" — psychology concept.'},
    46: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.88, 'ambig': True, 'comp': ['Academic Subjects'], 'rationale': 'Meaning of "type" in Persian — translation/definition.', 'evidence': 'Query asks meaning of type in Persian — language translation.'},
    47: {'l1': 'Education & Reference', 'l2': 'Dictionaries & Thesauri', 'conf': 0.90, 'ambig': True, 'comp': ['Health & Fitness:Medical Conditions'], 'rationale': 'Putamen definition — brain anatomy term definition.', 'evidence': 'Query "putamen definition" — anatomical term lookup.'},
    48: {'l1': 'Travel & Local', 'l2': 'Maps & Navigation', 'conf': 0.88, 'ambig': False, 'comp': [], 'rationale': 'County location query for Acton, Montana.', 'evidence': 'Query asks "what county is acton mt in" — geographic location lookup.'},
    49: {'l1': 'Shopping & Commerce', 'l2': 'Home & Garden', 'conf': 0.88, 'ambig': False, 'comp': [], 'rationale': 'Kitchen backsplash cost — home improvement pricing.', 'evidence': 'Query "how much for backsplash" — home renovation cost.'},
}

with open(r'labels/output/labeled_records.jsonl', 'a', encoding='utf-8') as f:
    for idx, q in enumerate(queries):
        c = classifications[idx]
        h = hashlib.sha256(q.encode('utf-8')).hexdigest()[:16]
        label_arr = [c['l1'], c['l2'], 'needs_human_review', 'needs_human_review']
        rec = {
            'record_id': f'msmarco_sample_line_{51+idx:06d}',
            'source_file': 'deepl-search/experiments/msmarco_sample.txt',
            'record_index': 50 + idx,
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
            'labeled_at': '2026-06-13T20:10:00Z'
        }
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

print('Batch 2 complete: 50 records appended')
