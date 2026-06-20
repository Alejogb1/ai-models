"""
Relabel 500 records with real L3/L4 names.
Uses keyword matching to pick the best L3 subcategory for each query.
"""
import json
import os
import re
from collections import defaultdict

PROJECT = r"C:\Users\ALEJOO\Documents\Gym IG Content Landing Page\ai-models"
LABELED_PATH = os.path.join(PROJECT, "labels", "output", "labeled_records.jsonl")
MAPPING_PATH = os.path.join(PROJECT, "labels", "taxonomy", "l3l4_mapping.json")
OUTPUT_PATH = os.path.join(PROJECT, "labels", "output", "labeled_records.jsonl")
QUERIES_PATH = os.path.join(PROJECT, "deepl-search", "experiments", "msmarco_sample.txt")

# Taxonomy structure
L1_NAMES = [
    "Arts & Entertainment",
    "Business & Finance",
    "Computers & Technology",
    "Education & Reference",
    "Food & Dining",
    "Health & Fitness",
    "Shopping & Commerce",
    "Travel & Local",
]

L2_NAMES = {
    0: ["Visual Arts", "Performing Arts", "Music", "Movies", "TV", "Literature", "Comics & Animation", "Celebrities"],
    1: ["Investing", "Banking", "Insurance", "Real Estate", "Accounting", "Small Business", "Careers & Jobs", "Economy"],
    2: ["Software", "Hardware", "Programming", "Networking", "Cybersecurity", "AI & Data", "Mobile", "Cloud & DevOps"],
    3: ["K-12", "Higher Education", "Online Learning", "Research", "Dictionaries & Thesauri", "How-To Guides", "Academic Subjects", "Test Prep"],
    4: ["Restaurants", "Recipes", "Cooking Tips", "Beverages", "Nutrition", "Cuisine Types", "Dining Out", "Food Science"],
    5: ["Exercise & Workouts", "Mental Health", "Medical Conditions", "Medications", "Alternative Medicine", "Nutrition & Diet", "Wellness", "Senior Health"],
    6: ["Clothing", "Electronics", "Home & Garden", "Beauty Products", "Sports Gear", "Books & Media", "Toys & Hobbies", "Groceries"],
    7: ["Destinations", "Hotels", "Flight Booking", "Public Transit", "Maps & Navigation", "Local Services", "Events", "Weather"],
}

# Build lookup: L1_name → L1_idx
L1_LOOKUP = {n: i for i, n in enumerate(L1_NAMES)}

# Build lookup: (L1_idx, L2_name) → L2_idx
L2_LOOKUP = {}
for l1_idx, names in L2_NAMES.items():
    for l2_idx, name in enumerate(names):
        L2_LOOKUP[(l1_idx, name)] = l2_idx


def normalize(text):
    """Normalize text for keyword matching."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text


def tokenize(text):
    return set(normalize(text).split())


def load_queries(path):
    """Load queries from msmarco_sample.txt."""
    queries = {}
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line:
                # MS MARCO format: id\ttext
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    queries[i] = parts[1]
                else:
                    queries[i] = line
    return queries


def pick_l3(query, l1_idx, l2_idx, mapping):
    """Pick the best L3 subcategory for this query based on keyword overlap."""
    prefix = f"A{l1_idx+1}.B{l2_idx+1}."
    query_tokens = tokenize(query)

    best_score = -1
    best_l3_id = None
    best_l3_name = None

    for l3_idx in range(8):
        l3_id = f"{prefix}C{l3_idx+1}"
        l3_name = mapping["l3_names"].get(l3_id, "")
        l3_tokens = tokenize(l3_name)

        # Score: count overlapping tokens
        overlap = len(query_tokens & l3_tokens)
        if overlap > best_score:
            best_score = overlap
            best_l3_id = l3_id
            best_l3_name = l3_name

    if best_l3_id is None:
        best_l3_id = f"{prefix}C1"
        best_l3_name = mapping["l3_names"].get(best_l3_id, "General")

    # Now pick L4 under this L3
    best_l4_id = None
    best_l4_name = None
    # Extract indices from ID: A{l1+1}.B{l2+1}.C{l3+1}
    parts = best_l3_id.split(".")
    picked_l1 = int(parts[0][1:]) - 1  # A1 → 0
    picked_l2 = int(parts[1][1:]) - 1  # B1 → 0
    picked_l3 = int(parts[2][1:]) - 1  # C1 → 0
    l3_global_idx = picked_l1 * 64 + picked_l2 * 8 + picked_l3
    n_l4 = 8 if l3_global_idx < 259 else 7

    for l4_idx in range(n_l4):
        l4_id = f"{best_l3_id}.D{l4_idx+1}"
        l4_name = mapping["l4_names"].get(l4_id, "")
        l4_tokens = tokenize(l4_name)
        overlap = len(query_tokens & l4_tokens)
        if overlap > 0 or best_l4_id is None:
            best_l4_id = l4_id
            best_l4_name = l4_name
            if overlap > 0:
                break

    return best_l3_name, best_l4_name


def main():
    print("Loading mapping...")
    with open(MAPPING_PATH, encoding="utf-8") as f:
        mapping = json.load(f)

    print("Loading queries...")
    queries = load_queries(QUERIES_PATH)
    print(f"  Loaded {len(queries)} queries")

    print("Relabeling records...")
    updated_count = 0
    needs_review_count = 0
    stats = defaultdict(int)

    with open(LABELED_PATH, encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in records:
            label = r["label"]  # [L1, L2, L3, L4]
            l1_name = label[0]
            l2_name = label[1]
            record_index = r["record_index"]
            query = queries.get(record_index, "")

            l1_idx = L1_LOOKUP.get(l1_name)
            l2_idx = L2_LOOKUP.get((l1_idx, l2_name)) if l1_idx is not None else None

            if l1_idx is not None and l2_idx is not None:
                l3_name, l4_name = pick_l3(query, l1_idx, l2_idx, mapping)
                r["label"] = [l1_name, l2_name, l3_name, l4_name]
                r["needs_human_review"] = False
                updated_count += 1
            else:
                r["label"] = [l1_name, l2_name, "needs_human_review", "needs_human_review"]
                r["needs_human_review"] = True
                needs_review_count += 1
                stats[(l1_name, l2_name)] += 1

            json.dump(r, f, ensure_ascii=False)
            f.write("\n")

    print(f"  Updated L3/L4: {updated_count}")
    if needs_review_count > 0:
        print(f"  Needs human review: {needs_review_count}")
        for key, cnt in sorted(stats.items()):
            print(f"    {key[0]} > {key[1]}: {cnt}")
    print("Done!")


if __name__ == "__main__":
    main()
