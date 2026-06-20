"""Evaluate Bi-Encoder vs B9 Baselines.

Compares three model variants on L2 retrieval:
1. Vanilla all-MiniLM-L6-v2 (baseline)
2. SimCSE pre-trained (from contrastive pre-training)
3. Bi-encoder trained on 500 labeled queries (Phase 6)

Usage:
    python scripts/evaluate_bi_encoder.py

Output: deepl-search/experiments/bi_encoder_eval_results.json
"""

import os
import json
import sys
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

sys.path.insert(0, os.path.dirname(__file__))
from train_bi_encoder import TransformerEncoder, L2_LIST, L1_L2_DESCRIPTIONS, L1_NAMES

LABELS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                           "labels", "output", "labeled_records.jsonl")
QUERIES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "experiments", "msmarco_sample.txt")
MODEL_PATHS = {
    "vanilla": "sentence-transformers/all-MiniLM-L6-v2",
    "simcse": os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "models", "simcse_query_encoder"),
    "bi_encoder_labeled": os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                       "models", "bi_encoder_labeled"),
}
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "experiments", "bi_encoder_eval_results.json")

all_l2_descs = [desc for _, _, desc in L2_LIST]
all_l2_names = [name for _, name, _ in L2_LIST]


def load_data():
    with open(QUERIES_PATH, 'r', encoding='utf-8') as f:
        queries_text = [line.strip() for line in f]
    records = []
    with open(LABELS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
    query_texts, l2_labels = [], []
    for r in records:
        idx = r["record_index"]
        if idx < len(queries_text):
            query_texts.append(queries_text[idx])
            l2_labels.append(r["label"][1])
    return query_texts, l2_labels


def evaluate_model(model, query_texts, l2_labels, device="cpu"):
    q_embeds = model.encode(query_texts, device=device)
    d_embeds = model.encode(all_l2_descs, device=device)
    q_embeds = q_embeds / np.linalg.norm(q_embeds, axis=1, keepdims=True)
    d_embeds = d_embeds / np.linalg.norm(d_embeds, axis=1, keepdims=True)
    sims = q_embeds @ d_embeds.T

    correct = 0
    confidences = []
    class_counts = {}
    per_l1_accuracy = {l1: {"correct": 0, "total": 0} for l1 in L1_NAMES}
    per_l1_confidence = {l1: [] for l1 in L1_NAMES}

    for i in range(len(query_texts)):
        sim = sims[i]
        top_idx = np.argmax(sim)
        predicted_l2 = all_l2_names[top_idx]
        confidence = float(sim[top_idx])
        confidences.append(confidence)
        class_counts[predicted_l2] = class_counts.get(predicted_l2, 0) + 1
        if predicted_l2 == l2_labels[i]:
            correct += 1

        # Per-L1 breakdown: find the L1 of the true label
        for l1_name in L1_NAMES:
            l2_names_in_l1 = [n for _, n, _ in L2_LIST if any(desc.startswith(n) for desc in L1_L2_DESCRIPTIONS[l1_name] if n == desc.split(":")[0].strip())]
            # Simpler: match by L2_LIST membership
            for ll1, ll2_name, _ in L2_LIST:
                if ll1 == l1_name and ll2_name == l2_labels[i]:
                    per_l1_accuracy[l1_name]["total"] += 1
                    if predicted_l2 == l2_labels[i]:
                        per_l1_accuracy[l1_name]["correct"] += 1
                    per_l1_confidence[l1_name].append(confidence)
                    break

    # Also compute L1 accuracy (is predicted L2 within the correct L1?)
    l1_correct = 0
    for i in range(len(query_texts)):
        true_l1 = None
        for l1_name in L1_NAMES:
            for ll1, ll2_name, _ in L2_LIST:
                if ll1 == l1_name and ll2_name == l2_labels[i]:
                    true_l1 = l1_name
                    break
            if true_l1:
                break
        pred_l1 = None
        for l1_name in L1_NAMES:
            for ll1, ll2_name, _ in L2_LIST:
                if ll1 == l1_name and ll2_name == all_l2_names[np.argmax(sims[i])]:
                    pred_l1 = l1_name
                    break
            if pred_l1:
                break
        if true_l1 and pred_l1 and true_l1 == pred_l1:
            l1_correct += 1

    bin_edges = [0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.0]
    bin_labels = ["0_0.05", "0.05_0.10", "0.10_0.15", "0.15_0.20", "0.20_0.30", "0.30_0.50", "0.50_1.00"]
    confidence_bins = {}
    for bl, start, end in zip(bin_labels, bin_edges[:-1], bin_edges[1:]):
        confidence_bins[bl] = sum(1 for c in confidences if start <= c < end)

    return {
        "l2_accuracy": correct / len(query_texts),
        "l1_accuracy": l1_correct / len(query_texts),
        "correct": correct,
        "total": len(query_texts),
        "mean_confidence": float(np.mean(confidences)),
        "std_confidence": float(np.std(confidences)),
        "max_confidence": float(np.max(confidences)),
        "min_confidence": float(np.min(confidences)),
        "effective_K": sum(1 for v in class_counts.values() if v / len(query_texts) > 0.01),
        "confidence_bins": confidence_bins,
        "per_l1_accuracy": {
            k: {"accuracy": v["correct"] / max(v["total"], 1), "total": v["total"]}
            for k, v in per_l1_accuracy.items()
        },
        "per_l1_mean_confidence": {
            k: float(np.mean(v)) if v else 0.0
            for k, v in per_l1_confidence.items()
        },
    }


def run():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    print("Loading data...")
    query_texts, l2_labels = load_data()
    print(f"Loaded {len(query_texts)} labeled queries")

    all_results = {}
    for variant, model_path in MODEL_PATHS.items():
        if not os.path.exists(model_path) and variant != "vanilla":
            print(f"\nSkipping {variant}: model not found at {model_path}")
            all_results[variant] = {"error": "model_not_found"}
            continue
        print(f"\n=== Evaluating {variant} ===")
        try:
            model = TransformerEncoder(model_path)
            model.to(device)
            model.eval()
        except Exception as e:
            print(f"  Error loading model: {e}")
            all_results[variant] = {"error": str(e)}
            continue

        results = evaluate_model(model, query_texts, l2_labels, device=device)
        print(f"  L2 Accuracy: {results['l2_accuracy']:.2%}")
        print(f"  L1 Accuracy: {results['l1_accuracy']:.2%}")
        print(f"  Mean conf: {results['mean_confidence']:.4f}")
        print(f"  Max conf: {results['max_confidence']:.4f}")
        print(f"  Effective K: {results['effective_K']}")
        all_results[variant] = results

    if len(all_results) >= 2:
        variants = [v for v in all_results if "error" not in all_results[v]]
        if len(variants) >= 2:
            print("\n=== Model Comparison ===")
            print(f"{'Variant':25s} {'L2 Acc':8s} {'L1 Acc':8s} {'Mean Conf':10s} {'Max Conf':10s} {'Eff K':6s}")
            print("-" * 70)
            for v in variants:
                r = all_results[v]
                print(f"{v:25s} {r['l2_accuracy']:.2%}    {r['l1_accuracy']:.2%}    {r['mean_confidence']:.4f}    {r['max_confidence']:.4f}    {r['effective_K']}")

            if "vanilla" in all_results and "bi_encoder_labeled" in all_results:
                v = all_results["vanilla"]
                b = all_results["bi_encoder_labeled"]
                print(f"\nDelta (bi_encoder - vanilla):")
                print(f"  L2 Acc: {b['l2_accuracy'] - v['l2_accuracy']:+.2%}")
                print(f"  L1 Acc: {b['l1_accuracy'] - v['l1_accuracy']:+.2%}")
                print(f"  Mean Conf: {b['mean_confidence'] - v['mean_confidence']:+.4f}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
