"""Analyze B8 LLM zero-shot baseline results.

Input: deepl-search/experiments/b8_baseline_results.json
Output: Confusion matrix, per-category accuracy, head/tail/mid breakdown

Usage:
    python scripts/analyze_b8_baseline.py
"""

import json
import os
from collections import Counter


L1_CATEGORIES = [
    "Arts & Entertainment", "Autos & Vehicles", "Business & Finance",
    "Education & Reference", "Health & Medical", "Home & Garden",
    "Shopping & E-commerce", "Sports & Recreation",
]


def analyze(b8_path: str, cross_path: str = None):
    with open(b8_path) as f:
        b8 = json.load(f)

    results = b8.get("results", [])
    print(f"Total results: {len(results)}")
    print(f"Errors: {len(b8.get('errors', []))}")
    print(f"Model: {b8.get('model', 'unknown')}")

    valid = [r for r in results if r.get("predicted_label") is not None]
    invalid = [r for r in results if r.get("predicted_label") is None]
    print(f"Valid predictions: {len(valid)}")
    print(f"Invalid (parse failures): {len(invalid)}")

    if invalid:
        print("\nSample parse failures (first 5):")
        for r in invalid[:5]:
            print(f"  '{r['query_text']}' -> raw: '{r.get('raw_response', '')}'")

    if len(valid) == 0:
        print("\nNo valid predictions to analyze")
        return

    pred_counts = Counter(r["predicted_label"] for r in valid)
    print(f"\n=== Prediction Distribution ===")
    for cat in sorted(pred_counts.keys(), key=lambda x: -pred_counts[x]):
        pct = pred_counts[cat] / len(valid) * 100
        print(f"  {cat}: {pred_counts[cat]} ({pct:.1f}%)")

    # Query length breakdown
    by_length = {"head": [], "mid": [], "tail": []}
    for r in results:
        length = len(r.get("query_text", ""))
        if length < 30:
            by_length["head"].append(r)
        elif length < 60:
            by_length["mid"].append(r)
        else:
            by_length["tail"].append(r)

    print(f"\n=== Length Stratification ===")
    for strata, items in by_length.items():
        print(f"  {strata}: {len(items)} queries")
        valid_s = [r for r in items if r.get("predicted_label")]
        if valid_s:
            top_cat = Counter(r["predicted_label"] for r in valid_s).most_common(1)[0]
            parse_rate = len(valid_s) / max(len(items), 1) * 100
            print(f"    Parse success: {parse_rate:.1f}%")
            print(f"    Top category: {top_cat[0]} ({top_cat[1]})")

    # Cross-model agreement (if available)
    if cross_path and os.path.exists(cross_path):
        print(f"\n=== Cross-Model Agreement ===")
        with open(cross_path) as f:
            cross = json.load(f)
        cross_results = {r["query_id"]: r for r in cross.get("results", [])}
        agreements = 0
        total = 0
        for r in valid:
            qid = r.get("query_id")
            other = cross_results.get(qid)
            if other and other.get("predicted_label"):
                total += 1
                if other["predicted_label"] == r["predicted_label"]:
                    agreements += 1
        if total > 0:
            print(f"  Agreement: {agreements}/{total} = {agreements/total*100:.1f}%")
        else:
            print(f"  No matching query IDs found for agreement analysis")

    # Summary
    print(f"\n=== Summary ===")
    print(f"  Total queries: {len(results)}")
    print(f"  Valid predictions: {len(valid)} ({len(valid)/max(len(results),1)*100:.1f}%)")
    print(f"  Unique categories used: {len(pred_counts)}/{len(L1_CATEGORIES)}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))

    primary = os.environ.get("B8_PATH",
        os.path.join(base_dir, "experiments", "b8_baseline_results.json"))
    cross = os.environ.get("B8_CROSS_PATH",
        os.path.join(base_dir, "experiments", "b8_cross_agreement_results.json"))

    if not os.path.exists(primary):
        print(f"Primary results not found at {primary}")
        print("Run scripts/run_b8_baseline.py first")
    else:
        analyze(primary, cross)
