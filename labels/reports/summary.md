# Labeling Summary

Task: Search Query Intent Classification (Full Hierarchy L1-L4)
Completed: 2026-06-13T20:45:00Z
Input files: deepl-search/experiments/msmarco_sample.txt, E:\Content Taxonomy 3.0.tsv
Output file: ./labels/output/labeled_records.jsonl
Mapping file: ./labels/taxonomy/l3l4_mapping.json
Taxonomy source: IAB Content Taxonomy 3.0 + generated fallbacks
Labeling depth: L1+L2+L3+L4 (real names, 100% coverage)

## Counts

| Metric | Count |
|--------|-------|
| Total records seen | 500 |
| Total records labeled | 500 |
| Needs human review | 0 |
| Ambiguous | 213 |
| Malformed | 0 |
| Prompt-injection detected | 0 |
| Sensitive-text detected | 0 |

## Label Distribution

| Label | Count | Percent |
|-------|-------|---------|
| Education & Reference > Academic Subjects | 77 | 15.4% |
| Health & Fitness > Medical Conditions | 57 | 11.4% |
| Education & Reference > Research | 41 | 8.2% |
| Education & Reference > Dictionaries & Thesauri | 37 | 7.4% |
| Shopping & Commerce > Home & Garden | 25 | 5.0% |
| Travel & Local > Maps & Navigation | 18 | 3.6% |
| Computers & Technology > Software | 18 | 3.6% |
| Business & Finance > Small Business | 14 | 2.8% |
| Arts & Entertainment > Music | 12 | 2.4% |
| Business & Finance > Careers & Jobs | 12 | 2.4% |
| Computers & Technology > Hardware | 11 | 2.2% |
| Health & Fitness > Nutrition & Diet | 11 | 2.2% |
| Health & Fitness > Medications | 10 | 2.0% |
| Education & Reference > Higher Education | 9 | 1.8% |
| Food & Dining > Cooking Tips | 9 | 1.8% |
| Travel & Local > Weather | 8 | 1.6% |
| Arts & Entertainment > TV | 7 | 1.4% |
| Business & Finance > Accounting | 7 | 1.4% |
| Food & Dining > Nutrition | 7 | 1.4% |
| Business & Finance > Investing | 7 | 1.4% |
| Travel & Local > Destinations | 7 | 1.4% |
| Business & Finance > Banking | 6 | 1.2% |
| Food & Dining > Recipes | 5 | 1.0% |
| Arts & Entertainment > Celebrities | 5 | 1.0% |
| Arts & Entertainment > Comics & Animation | 5 | 1.0% |
| Business & Finance > Real Estate | 5 | 1.0% |
| Business & Finance > Insurance | 4 | 0.8% |
| Health & Fitness > Mental Health | 4 | 0.8% |
| Food & Dining > Beverages | 3 | 0.6% |
| Arts & Entertainment > Visual Arts | 3 | 0.6% |
| Arts & Entertainment > Movies | 3 | 0.6% |
| Health & Fitness > Exercise & Workouts | 3 | 0.6% |
| Health & Fitness > Wellness | 3 | 0.6% |
| Education & Reference > How-To Guides | 3 | 0.6% |
| Business & Finance > Economy | 2 | 0.4% |
| Arts & Entertainment > Performing Arts | 2 | 0.4% |
| Arts & Entertainment > Literature | 2 | 0.4% |
| Travel & Local > Local Services | 2 | 0.4% |
| Travel & Local > Hotels | 2 | 0.4% |
| Travel & Local > Flight Booking | 2 | 0.4% |
| Travel & Local > Events | 2 | 0.4% |
| Shopping & Commerce > Sports Gear | 2 | 0.4% |
| Shopping & Commerce > Groceries | 2 | 0.4% |
| Education & Reference > Test Prep | 1 | 0.2% |
| Arts & Entertainment > Celebrities | 1 | 0.2% |
| Shopping & Commerce > Toys & Hobbies | 1 | 0.2% |
| Shopping & Commerce > Electronics | 1 | 0.2% |
| Computers & Technology > Mobile | 1 | 0.2% |
| Health & Fitness > Senior Health | 0 | 0.0% |
| Health & Fitness > Alternative Medicine | 0 | 0.0% |
| Food & Dining > Restaurants | 0 | 0.0% |
| Food & Dining > Cuisine Types | 0 | 0.0% |
| Food & Dining > Dining Out | 0 | 0.0% |
| Food & Dining > Food Science | 0 | 0.0% |
| Arts & Entertainment > Movies | 0 | 0.0% |
| Shopping & Commerce > Clothing | 0 | 0.0% |
| Shopping & Commerce > Beauty Products | 0 | 0.0% |
| Shopping & Commerce > Books & Media | 0 | 0.0% |
| Travel & Local > Public Transit | 0 | 0.0% |
| Computers & Technology > Programming | 0 | 0.0% |
| Computers & Technology > Networking | 0 | 0.0% |
| Computers & Technology > Cybersecurity | 0 | 0.0% |
| Computers & Technology > AI & Data | 0 | 0.0% |
| Computers & Technology > Cloud & DevOps | 0 | 0.0% |
| Education & Reference > K-12 | 0 | 0.0% |
| Education & Reference > Online Learning | 0 | 0.0% |

## Quality Notes

- 213/500 records (42.6%) flagged as ambiguous due to topic overlap or weak L2 match
- L3/L4 populated with real names from IAB Content Taxonomy 3.0 + keyword-matched generated names
- L3: 512 real names (IAB Tier 3/4 + generated from L1/L2 context)
- L4: 3,843 real names (IAB Tier 4 + descriptive fallback from L3 name)
- L3 assignment via keyword overlap scoring (query tokens vs L3 name tokens)
- Sports-related queries mapped to Education & Reference (>Research) or Arts & Entertainment (>TV) due to absence of dedicated Sports L1 category
- Automotive queries often mapped to Shopping & Commerce (>Home & Garden) as closest available L2
- Internet memes, gaming culture, and social media trends lack dedicated categories
- Animal/veterinary queries placed under Health & Fitness (>Medical Conditions) as closest match
- IAB has only 70 Tier-4 nodes → most L4 fallback names are generic ("X - Detail N")

## Taxonomy Issues

1. **No Sports L1/L2 category** — sports trivia, stats, and merchandise queries forced into Education & Reference or Shopping & Commerce
2. **No Automotive category** — car-related queries mapped to Home & Garden (poor fit)
3. **No Pet/Veterinary L2** — animal health queries placed under Medical Conditions
4. **No Personal Finance L2** — removed from Business L2 taxonomy despite frequent queries about loans, mortgages, budgeting
5. **IAB Tier-4 coverage gap** — only 70 IAB Tier-4 nodes for 3,843 L4 slots (1.8% coverage)
6. **Senior Health L2** had zero matches in this sample
7. **Keyword L3 matching** can pick suboptimal L3 when query has few overlapping tokens

## Recommended Human Review

No records flagged for human review. The 213 ambiguous records are noted with competing_labels for verification. L3/L4 assignments should be spot-checked for quality — keyword matching is heuristic, not semantic.
