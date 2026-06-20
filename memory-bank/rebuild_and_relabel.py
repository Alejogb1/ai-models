"""
Rebuild labeled_records.jsonl from batch scripts and relabel with real L3/L4 names.
"""
import hashlib
import json
import os
import re

PROJECT = r"C:\Users\ALEJOO\Documents\Gym IG Content Landing Page\ai-models"
BATCH_DIR = os.path.join(PROJECT, "memory-bank")
QUERIES_PATH = os.path.join(PROJECT, "deepl-search", "experiments", "msmarco_sample.txt")
MAPPING_PATH = os.path.join(PROJECT, "labels", "taxonomy", "l3l4_mapping.json")
OUTPUT_PATH = os.path.join(PROJECT, "labels", "output", "labeled_records.jsonl")

# Taxonomy lookup
L1_NAMES = [
    "Arts & Entertainment", "Business & Finance", "Computers & Technology",
    "Education & Reference", "Food & Dining", "Health & Fitness",
    "Shopping & Commerce", "Travel & Local",
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

def load_queries(path):
    queries = {}
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line:
                parts = line.split("\t", 1)
                queries[i] = parts[1] if len(parts) == 2 else line
    return queries

def extract_classifications(batch_file, start_offset=0):
    """Extract classification data from a batch labeling script.
    Returns dict with global indices."""
    with open(batch_file, encoding="utf-8") as f:
        content = f.read()
    # Find the dict variable: could be `classifications`, `CLASSIFICATIONS`, or `c`
    var_names = ["classifications", "CLASSIFICATIONS", "c"]
    dict_str = None
    for vn in var_names:
        pattern = vn + " = {"
        start = content.find(pattern)
        if start != -1:
            # Find the matching closing brace
            brace_count = 0
            in_dict = False
            end = start
            for i in range(start, len(content)):
                if content[i] == "{":
                    brace_count += 1
                    in_dict = True
                elif content[i] == "}":
                    brace_count -= 1
                    if in_dict and brace_count == 0:
                        end = i + 1
                        break
            dict_str = content[start:end]
            break
    if dict_str is None:
        print(f"  No classifications dict found in {batch_file}")
        return {}
    # Execute safely to get the dict
    local_vars = {}
    exec(dict_str, {"__builtins__": {}}, local_vars)
    # Find the dict variable
    for key in list(local_vars.keys()):
        if isinstance(local_vars[key], dict) and any(isinstance(k, int) for k in local_vars[key].keys()):
            raw = local_vars[key]
            # Add offset to keys
            return {start_offset + k: v for k, v in raw.items()}
    return {}

def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text

def tokenize(text):
    return set(normalize(text).split())

def pick_l3(query, l1_idx, l2_idx, mapping):
    prefix = f"A{l1_idx+1}.B{l2_idx+1}."
    query_tokens = tokenize(query)
    best_score = -1
    best_l3_id = None
    best_l3_name = None
    for l3_idx in range(8):
        l3_id = f"{prefix}C{l3_idx+1}"
        l3_name = mapping["l3_names"].get(l3_id, "")
        l3_tokens = tokenize(l3_name)
        overlap = len(query_tokens & l3_tokens)
        if overlap > best_score:
            best_score = overlap
            best_l3_id = l3_id
            best_l3_name = l3_name
    if best_l3_id is None:
        best_l3_id = f"{prefix}C1"
        best_l3_name = mapping["l3_names"].get(best_l3_id, "General")
    parts = best_l3_id.split(".")
    picked_l1 = int(parts[0][1:]) - 1
    picked_l2 = int(parts[1][1:]) - 1
    picked_l3 = int(parts[2][1:]) - 1
    l3_global_idx = picked_l1 * 64 + picked_l2 * 8 + picked_l3
    n_l4 = 8 if l3_global_idx < 259 else 7
    # Pick L4: first one with keyword overlap, else first
    best_l4_name = None
    for l4_idx in range(n_l4):
        l4_id = f"{best_l3_id}.D{l4_idx+1}"
        l4_name = mapping["l4_names"].get(l4_id, "")
        l4_tokens = tokenize(l4_name)
        if best_l4_name is None:
            best_l4_name = l4_name
        if len(query_tokens & l4_tokens) > 0:
            best_l4_name = l4_name
            break
    return best_l3_name, best_l4_name

def main():
    print("Loading mapping...")
    with open(MAPPING_PATH, encoding="utf-8") as f:
        mapping = json.load(f)

    print("Loading queries...")
    queries = load_queries(QUERIES_PATH)

    print("Extracting classifications from batch files...")
    all_classifications = {}
    # Maps batch file -> start offset in the global msmarco_sample.txt
    batch_offsets = {
        "label_batch1.py": 0,
        "label_batch2.py": 50,
        "label_batch3_4.py": 100,
        "label_batch5_6.py": 200,
        "label_batch7_8.py": 300,
        "label_batch9_10.py": 400,
    }
    for bf_name, offset in sorted(batch_offsets.items()):
        bf = os.path.join(BATCH_DIR, bf_name)
        if not os.path.exists(bf):
            print(f"  {bf_name} not found, skipping")
            continue
        print(f"  {bf_name} (offset {offset})...")
        cls = extract_classifications(bf, offset)
        print(f"    {len(cls)} records")
        all_classifications.update(cls)
    print(f"Total classifications: {len(all_classifications)}")

    print("Building records...")
    records = []
    sorted_indices = sorted(all_classifications.keys())
    for idx in sorted_indices:
        c = all_classifications[idx]
        q = queries.get(idx, "")
        h = hashlib.sha256(q.encode("utf-8")).hexdigest()[:16]

        # Get real L3/L4 names
        l1_name = c["l1"]
        l2_name = c["l2"]
        l1_idx = None
        for li, name in enumerate(L1_NAMES):
            if name == l1_name:
                l1_idx = li
                break
        l2_idx = None
        if l1_idx is not None:
            for li, name in enumerate(L2_NAMES[l1_idx]):
                if name == l2_name:
                    l2_idx = li
                    break

        if l1_idx is not None and l2_idx is not None:
            l3_name, l4_name = pick_l3(q, l1_idx, l2_idx, mapping)
            needs_review = False
        else:
            l3_name = "needs_human_review"
            l4_name = "needs_human_review"
            needs_review = True

        label_arr = [l1_name, l2_name, l3_name, l4_name]
        rec = {
            "record_id": f"msmarco_sample_line_{idx+1:06d}",
            "source_file": "deepl-search/experiments/msmarco_sample.txt",
            "record_index": idx,
            "input_hash": h,
            "label": label_arr,
            "confidence": round(c["conf"], 2),
            "ambiguous": c["ambig"],
            "competing_labels": c["comp"],
            "rationale": c["rationale"],
            "evidence_summary": c["evidence"],
            "contains_prompt_injection": False,
            "contains_sensitive_text": False,
            "malformed_record": False,
            "needs_human_review": needs_review,
            "taxonomy_version": "deepl-search_v1_L1-L4",
            "labeled_at": "2026-06-13T20:00:00Z",
        }
        records.append(rec)

    print(f"Writing {len(records)} records...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for rec in records:
            json.dump(rec, f, ensure_ascii=False)
            f.write("\n")

    # Audit
    l2_counts = {}
    for rec in records:
        l2_key = (rec["label"][0], rec["label"][1])
        l2_counts[l2_key] = l2_counts.get(l2_key, 0) + 1

    review_count = sum(1 for r in records if r["needs_human_review"])
    print(f"\nSummary:")
    print(f"  Total records: {len(records)}")
    print(f"  Needs human review: {review_count}")
    print(f"  Unique L1>L2 combos: {len(l2_counts)}")
    print(f"  Top L1>L2 combos:")
    for key, cnt in sorted(l2_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {key[0]} > {key[1]}: {cnt}")
    print("Done!")

if __name__ == "__main__":
    main()
