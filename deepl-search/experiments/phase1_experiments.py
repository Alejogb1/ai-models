"""
Phase 1 Experiments: Premise Resolution (Zero-Cost)
====================================================
Runs 3 label-free experiments on the existing pipeline:

Exp 3: Taxonomy Granularity Sweep - does confidence degrade at finer granularity?
Exp 11: Spell Correction - what fraction of predictions change with misspellings?
Exp 12: Reject Option - what coverage at each confidence threshold?

Plus 3 experiments that need labels (run as simulations/proxies):

Exp 1: Session vs Single Query - self-consistency proxy
Exp 5: Paradigm Comparison - output characteristic comparison
Exp 6: F1 vs Cost-Weighted - simulation with synthetic errors

Each experiment ends with a clear decision per the premise-resolution framework.
"""

import json
import os
import sys
import time
import math
import random
from collections import Counter

import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from taxonomy import build_skeleton, get_all_leaves, get_nodes_at_level, count_leaves

BASE = os.path.join(os.path.dirname(__file__), '..', 'experiments')
N_QUERIES = 2000
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def load_queries(n=N_QUERIES):
    path = os.path.join(BASE, "msmarco_sample.txt")
    with open(path, "r", encoding="utf-8") as f:
        queries = [line.strip() for line in f.readlines()[:n]]
    return queries


# ============================================================
# EXP 3: Taxonomy Granularity Sweep
# ============================================================
def experiment_3_granularity_sweep(clf, queries, out_dir):
    print("\n" + "="*60)
    print("EXP 3: Taxonomy Granularity Sweep")
    print("="*60)

    root = build_skeleton()
    l1_nodes = get_nodes_at_level(root, 1)
    l2_nodes = get_nodes_at_level(root, 2)
    l3_nodes = get_nodes_at_level(root, 3)
    leaves = get_all_leaves(root)

    leaf_to_l1 = {}
    leaf_to_l2 = {}
    leaf_to_l3 = {}

    for leaf in leaves:
        path_ids = leaf.path()
        leaf_to_l1[leaf.id] = path_ids[1] if len(path_ids) > 1 else None
        leaf_to_l2[leaf.id] = path_ids[2] if len(path_ids) > 2 else None
        leaf_to_l3[leaf.id] = path_ids[3] if len(path_ids) > 3 else None

    leaf_id_to_idx = {leaf.id: i for i, leaf in enumerate(leaves)}

    l1_centroids = {}
    for l1_node in l1_nodes:
        indices = [leaf_id_to_idx[leaf.id] for leaf in leaves
                   if leaf_to_l1.get(leaf.id) == l1_node.id]
        if indices:
            l1_centroids[l1_node.id] = clf.leaf_embeddings[indices].mean(axis=0)
            l1_centroids[l1_node.id] /= np.linalg.norm(l1_centroids[l1_node.id])

    l2_centroids = {}
    for l2_node in l2_nodes:
        indices = [leaf_id_to_idx[leaf.id] for leaf in leaves
                   if leaf_to_l2.get(leaf.id) == l2_node.id]
        if indices:
            l2_centroids[l2_node.id] = clf.leaf_embeddings[indices].mean(axis=0)
            l2_centroids[l2_node.id] /= np.linalg.norm(l2_centroids[l2_node.id])

    l3_centroids = {}
    for l3_node in l3_nodes:
        indices = [leaf_id_to_idx[leaf.id] for leaf in leaves
                   if leaf_to_l3.get(leaf.id) == l3_node.id]
        if indices:
            l3_centroids[l3_node.id] = clf.leaf_embeddings[indices].mean(axis=0)
            l3_centroids[l3_node.id] /= np.linalg.norm(l3_centroids[l3_node.id])

    print(f"Classifying {len(queries)} queries at 4 granularities...")
    batch_size = 100
    all_queries_embedded = []

    for i in range(0, len(queries), batch_size):
        batch = queries[i:i+batch_size]
        q_embs = clf.model.encode(batch, convert_to_numpy=True)
        q_embs = q_embs / np.linalg.norm(q_embs, axis=1, keepdims=True)
        all_queries_embedded.extend(q_embs)

    all_queries_embedded = np.array(all_queries_embedded)

    # L4
    l4_scores = all_queries_embedded @ clf.leaf_embeddings.T
    l4_max_conf = l4_scores.max(axis=1)
    l4_top1_idx = l4_scores.argmax(axis=1)
    l4_top1_ids = [leaves[idx].id for idx in l4_top1_idx]

    # L3
    l3_centroid_list = [l3_centroids[n.id] for n in l3_nodes]
    l3_centroid_array = np.array(l3_centroid_list)
    l3_centroid_array /= np.linalg.norm(l3_centroid_array, axis=1, keepdims=True)
    l3_scores = all_queries_embedded @ l3_centroid_array.T
    l3_max_conf = l3_scores.max(axis=1)

    # L2
    l2_centroid_list = [l2_centroids[n.id] for n in l2_nodes]
    l2_centroid_array = np.array(l2_centroid_list)
    l2_centroid_array /= np.linalg.norm(l2_centroid_array, axis=1, keepdims=True)
    l2_scores = all_queries_embedded @ l2_centroid_array.T
    l2_max_conf = l2_scores.max(axis=1)

    # L1
    l1_centroid_list = [l1_centroids[n.id] for n in l1_nodes]
    l1_centroid_array = np.array(l1_centroid_list)
    l1_centroid_array /= np.linalg.norm(l1_centroid_array, axis=1, keepdims=True)
    l1_scores = all_queries_embedded @ l1_centroid_array.T
    l1_max_conf = l1_scores.max(axis=1)

    # Self-consistency
    l1_from_l4 = [leaf_to_l1[lid] for lid in l4_top1_ids]
    l1_direct_indices = l1_scores.argmax(axis=1)
    l1_direct_ids = [l1_nodes[idx].id for idx in l1_direct_indices]

    consistent = sum(1 for a, b in zip(l1_from_l4, l1_direct_ids) if a == b)
    consistency_pct = 100.0 * consistent / len(queries)

    print(f"  L1 (8 classes):   mean max conf = {l1_max_conf.mean():.4f}")
    print(f"  L2 (64 classes):  mean max conf = {l2_max_conf.mean():.4f}")
    print(f"  L3 (512 classes): mean max conf = {l3_max_conf.mean():.4f}")
    print(f"  L4 (3843 classes):mean max conf = {l4_max_conf.mean():.4f}")
    print(f"  L1 self-consistency: {consistency_pct:.1f}%")

    l1_to_l2_drop = l1_max_conf.mean() - l2_max_conf.mean()
    l2_to_l3_drop = l2_max_conf.mean() - l3_max_conf.mean()
    l3_to_l4_drop = l3_max_conf.mean() - l4_max_conf.mean()
    total_drop = l1_max_conf.mean() - l4_max_conf.mean()

    print(f"  L1->L2 drop: {l1_to_l2_drop:.4f}")
    print(f"  L2->L3 drop: {l2_to_l3_drop:.4f}")
    print(f"  L3->L4 drop: {l3_to_l4_drop:.4f}")
    print(f"  Total L1->L4 drop: {total_drop:.4f}")

    print("\n  Confidence distribution:")
    for level_name, confs in [("L1", l1_max_conf), ("L2", l2_max_conf),
                              ("L3", l3_max_conf), ("L4", l4_max_conf)]:
        pct_above_05 = 100.0 * (confs > 0.5).mean()
        pct_above_07 = 100.0 * (confs > 0.7).mean()
        print(f"    {level_name}: >0.5: {pct_above_05:.1f}%, >0.7: {pct_above_07:.1f}%")

    # Effective usage
    l4_top1_counts = Counter(l4_top1_ids)
    l4_total_used = len(l4_top1_counts)
    l4_head = sum(1 for v in l4_top1_counts.values() if v >= len(queries) * 0.01)

    l3_top1_idx = l3_scores.argmax(axis=1)
    l3_top1_counts = Counter(l3_top1_idx)
    l3_total_used = len(l3_top1_counts)
    l3_head = sum(1 for v in l3_top1_counts.values() if v >= len(queries) * 0.01)

    l2_top1_idx = l2_scores.argmax(axis=1)
    l2_top1_counts = Counter(l2_top1_idx)
    l2_total_used = len(l2_top1_counts)

    l1_top1_idx = l1_scores.argmax(axis=1)
    l1_top1_counts = Counter(l1_top1_idx)
    l1_total_used = len(l1_top1_counts)

    print(f"\n  Effective usage (in {len(queries)} queries):")
    print(f"    L1: {l1_total_used}/8 used")
    print(f"    L2: {l2_total_used}/64 used")
    print(f"    L3: {l3_total_used}/{len(l3_nodes)} used, {l3_head} with >1% share")
    print(f"    L4: {l4_total_used}/{len(leaves)} used, {l4_head} with >1% share")

    print(f"\n  DECISION RULE:")
    if total_drop > 0.3:
        decision = "FALSIFIED: L1->L4 confidence drop > 0.3. Extra granularity adds noise. Target K=256-512."
    elif total_drop > 0.15:
        decision = "WEAKENED: L1->L4 confidence drop > 0.15 but < 0.3. Consider K=1024-1500."
    elif consistency_pct < 90:
        decision = f"WEAKENED: L1 self-consistency only {consistency_pct:.1f}%. L4 predictions inconsistent with L1."
    else:
        decision = "PREMISE HOLDS: Minimal confidence drop and high self-consistency. K=3843 is supported."

    print(f"  DECISION: {decision}")

    summary = {
        "n_queries": len(queries),
        "l1_mean_conf": float(round(l1_max_conf.mean(), 4)),
        "l2_mean_conf": float(round(l2_max_conf.mean(), 4)),
        "l3_mean_conf": float(round(l3_max_conf.mean(), 4)),
        "l4_mean_conf": float(round(l4_max_conf.mean(), 4)),
        "l1_to_l2_drop": float(round(l1_to_l2_drop, 4)),
        "l2_to_l3_drop": float(round(l2_to_l3_drop, 4)),
        "l3_to_l4_drop": float(round(l3_to_l4_drop, 4)),
        "total_drop": float(round(total_drop, 4)),
        "l1_self_consistency_pct": float(round(consistency_pct, 1)),
        "l1_above_07_pct": float(round(100.0 * (l1_max_conf > 0.7).mean(), 1)),
        "l4_above_07_pct": float(round(100.0 * (l4_max_conf > 0.7).mean(), 1)),
        "l3_effective_used": l3_total_used,
        "l4_effective_used": l4_total_used,
        "decision": decision,
    }

    path = os.path.join(out_dir, "exp3_granularity_sweep.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Results saved to {path}")
    return summary


# ============================================================
# EXP 11: Spell Correction Preprocessor
# ============================================================
def experiment_11_spell_correction(clf, queries, out_dir):
    print("\n" + "="*60)
    print("EXP 11: Spell Correction Preprocessor")
    print("="*60)

    try:
        import symspellpy
        HAS_SYMSPELL = True
    except ImportError:
        HAS_SYMSPELL = False
        print("  symspellpy not installed. Using edit-distance simulation.")

    def introduce_misspelling(word, p=0.3):
        if len(word) < 3 or random.random() > p:
            return word
        word = list(word)
        pos = random.randint(0, len(word) - 1)
        op = random.choice(['delete', 'insert', 'substitute', 'transpose'])

        if op == 'delete':
            word.pop(pos)
        elif op == 'insert' and len(word) < 15:
            c = random.choice('abcdefghijklmnopqrstuvwxyz')
            word.insert(pos, c)
        elif op == 'substitute':
            c = random.choice('abcdefghijklmnopqrstuvwxyz')
            word[pos] = c
        elif op == 'transpose' and pos < len(word) - 1:
            word[pos], word[pos+1] = word[pos+1], word[pos]

        return ''.join(word)

    def misspell_query(query, p=0.25):
        words = query.split()
        misspelled = [introduce_misspelling(w, p) for w in words]
        return ' '.join(misspelled)

    long_queries = [q for q in queries if len(q.split()) >= 2][:500]
    n = min(500, len(long_queries))
    long_queries = long_queries[:n]

    print(f"  Testing {n} queries with synthetic misspellings...")

    changed_no_correction = 0
    changed_with_correction = 0
    total_misspelled = 0

    for query in long_queries:
        result_orig = clf.classify(query, top_k=1, threshold=0.0)
        orig_id = result_orig.labels[0]['id'] if result_orig.labels else None

        for variant_idx in range(2):
            misspelled = misspell_query(query)
            if misspelled == query:
                continue
            total_misspelled += 1

            result_miss = clf.classify(misspelled, top_k=1, threshold=0.0)
            miss_id = result_miss.labels[0]['id'] if result_miss.labels else None

            if miss_id != orig_id:
                changed_no_correction += 1

    change_rate = 100.0 * changed_no_correction / total_misspelled if total_misspelled > 0 else 0

    print(f"  Total misspelled variants: {total_misspelled}")
    print(f"  Predictions changed by misspelling: {changed_no_correction} ({change_rate:.1f}%)")

    print(f"\n  DECISION RULE:")
    if change_rate >= 25:
        decision = f"FALSIFIED: {change_rate:.1f}% change rate from misspellings. Preprocessing more important than architecture."
    elif change_rate >= 15:
        decision = f"WEAKENED: {change_rate:.1f}% of misspelled queries change prediction. Spell correction preprocessor recommended."
    else:
        decision = f"PREMISE HOLDS: Only {change_rate:.1f}% of queries affected by misspellings. Raw text is sufficient."

    print(f"  DECISION: {decision}")

    summary = {
        "n_queries": n,
        "total_misspelled_variants": int(total_misspelled),
        "changed_by_misspelling": int(changed_no_correction),
        "change_rate_pct": float(round(change_rate, 1)),
        "has_symspell": HAS_SYMSPELL,
        "decision": decision,
    }

    path = os.path.join(out_dir, "exp11_spell_correction.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Results saved to {path}")
    return summary


# ============================================================
# EXP 12: Reject Option
# ============================================================
def experiment_12_reject_option(clf, queries, out_dir):
    print("\n" + "="*60)
    print("EXP 12: Reject Option Precision-Coverage Analysis")
    print("="*60)

    n = min(2000, len(queries))
    queries = queries[:n]

    results_list = []
    for query in queries:
        result = clf.classify(query, top_k=1, threshold=0.0)
        conf = result.labels[0]['score'] if result.labels else 0.0
        results_list.append({"query": query, "confidence": conf})

    confidences = np.array([r["confidence"] for r in results_list])

    thresholds = np.arange(0.0, 0.96, 0.05)
    curve = []

    for thresh in thresholds:
        accepted = confidences >= thresh
        n_accepted = int(accepted.sum())
        coverage = 100.0 * n_accepted / n
        mean_conf = confidences[accepted].mean() if n_accepted > 0 else 0

        curve.append({
            "threshold": float(round(thresh, 2)),
            "n_accepted": n_accepted,
            "coverage_pct": float(round(coverage, 1)),
            "mean_confidence": float(round(mean_conf, 4)),
        })

    print(f"  Confidence distribution over {n} queries:")
    print(f"    Mean: {confidences.mean():.4f}")
    print(f"    Median: {np.median(confidences):.4f}")
    print(f"    Std:  {confidences.std():.4f}")
    print(f"  Percentiles: 10={np.percentile(confidences, 10):.3f}, "
          f"25={np.percentile(confidences, 25):.3f}, "
          f"50={np.percentile(confidences, 50):.3f}, "
          f"75={np.percentile(confidences, 75):.3f}, "
          f"90={np.percentile(confidences, 90):.3f}")

    print(f"\n  Coverage at various thresholds:")
    for pt in curve:
        print(f"    tau={pt['threshold']:.2f}: coverage={pt['coverage_pct']:.1f}%")

    elbow_80 = None
    for pt in curve:
        if pt['coverage_pct'] >= 80:
            elbow_80 = pt
    elbow_90 = None
    for pt in curve:
        if pt['coverage_pct'] >= 90:
            elbow_90 = pt

    if elbow_90:
        print(f"  Threshold for 90% coverage: tau={elbow_90['threshold']:.2f} "
              f"(mean conf={elbow_90['mean_confidence']:.4f})")
    else:
        print("  Cannot reach 90% coverage")
    if elbow_80:
        print(f"  Threshold for 80% coverage: tau={elbow_80['threshold']:.2f} "
              f"(mean conf={elbow_80['mean_confidence']:.4f})")
    else:
        print("  Cannot reach 80% coverage")

    tau_mid = 0.5
    rejected = [r for r in results_list if r['confidence'] < tau_mid]
    low_conf_pct = 100.0 * len(rejected) / n

    print(f"\n  At tau=0.5: {len(rejected)} queries rejected ({low_conf_pct:.1f}%)")

    if elbow_90 and elbow_90['threshold'] >= 0.7:
        decision = "PREMISE HOLDS: 90% coverage at high threshold. Forced classification works well."
    elif elbow_80 and elbow_80['threshold'] >= 0.5:
        decision = "WEAKENED: 80% coverage at tau>=0.5. Reject option beneficial for remaining 20%."
    else:
        decision = "FALSIFIED: Cannot reach 80% coverage at reasonable threshold. Reject option essential."

    print(f"\n  DECISION: {decision}")

    summary = {
        "n_queries": n,
        "confidence_mean": float(round(float(confidences.mean()), 4)),
        "confidence_median": float(round(float(np.median(confidences)), 4)),
        "confidence_std": float(round(float(confidences.std()), 4)),
        "percentiles": {
            "p10": float(round(float(np.percentile(confidences, 10)), 4)),
            "p25": float(round(float(np.percentile(confidences, 25)), 4)),
            "p50": float(round(float(np.percentile(confidences, 50)), 4)),
            "p75": float(round(float(np.percentile(confidences, 75)), 4)),
            "p90": float(round(float(np.percentile(confidences, 90)), 4)),
        },
        "coverage_curve": curve,
        "low_confidence_at_05_pct": float(round(low_conf_pct, 1)),
        "elbow_90": elbow_90,
        "elbow_80": elbow_80,
        "decision": decision,
    }

    path = os.path.join(out_dir, "exp12_reject_option.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Results saved to {path}")
    return summary


# ============================================================
# EXP 6: F1 vs Cost-Weighted F1 (Simulation)
# ============================================================
def experiment_6_cost_weighted(queries, out_dir):
    print("\n" + "="*60)
    print("EXP 6: F1 vs Cost-Weighted F1 (Simulation)")
    print("="*60)

    n = 1000
    n_classes = 100

    np.random.seed(RANDOM_SEED)
    l1_groups = np.repeat(range(8), [12, 13, 12, 13, 12, 13, 12, 13])[:n_classes]
    assert len(l1_groups) == n_classes

    def simulate_model(error_rate, cross_l1_pct, name):
        true_labels = np.random.randint(0, n_classes, n)
        predictions = true_labels.copy()

        error_mask = np.random.random(n) < error_rate
        n_errors = error_mask.sum()

        for idx in np.where(error_mask)[0]:
            true = true_labels[idx]
            if np.random.random() < cross_l1_pct:
                true_l1 = l1_groups[true]
                candidates = [c for c in range(n_classes) if l1_groups[c] != true_l1]
                predictions[idx] = np.random.choice(candidates)
            else:
                true_l1 = l1_groups[true]
                same_l1 = [c for c in range(n_classes) if l1_groups[c] == true_l1 and c != true]
                if same_l1:
                    predictions[idx] = np.random.choice(same_l1)

        correct = (predictions == true_labels).sum()
        tp = correct
        fp = n_errors
        fn = n_errors
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        total_cost = 0
        for t, p in zip(true_labels, predictions):
            if t == p:
                cost = 0.0
            elif l1_groups[t] != l1_groups[p]:
                cost = 1.0
            else:
                cost = 0.3
            total_cost += cost

        avg_cost = total_cost / n

        return {
            "name": name,
            "error_rate": error_rate,
            "cross_l1_pct": cross_l1_pct,
            "accuracy": float(round(correct / n, 4)),
            "f1": float(round(f1, 4)),
            "avg_cost": float(round(avg_cost, 4)),
            "cost_weighted_f1": float(round(f1 * (1 - avg_cost), 4)),
        }

    model_a = simulate_model(0.15, 0.30, "Model A: High F1, some cross-L1")
    model_b = simulate_model(0.20, 0.05, "Model B: Lower F1, all within-L1")
    model_c = simulate_model(0.18, 0.15, "Model C: Moderate F1, moderate cross-L1")

    models = [model_a, model_b, model_c]

    rank_by_f1 = sorted(models, key=lambda m: m["f1"], reverse=True)
    rank_by_cost = sorted(models, key=lambda m: m["cost_weighted_f1"], reverse=True)

    print(f"  {'Model':35s} {'Err':>5s} {'X-L1':>5s} {'Acc':>6s} {'F1':>6s} {'AvgCost':>8s} {'CW-F1':>6s}")
    print("  " + "-"*80)
    for m in models:
        print(f"  {m['name']:35s} {m['error_rate']:.2f} {m['cross_l1_pct']:.2f} "
              f"{m['accuracy']:.4f} {m['f1']:.4f} {m['avg_cost']:.4f} {m['cost_weighted_f1']:.4f}")

    print(f"\n  Rank by F1:           {[m['name'] for m in rank_by_f1]}")
    print(f"  Rank by CostWeighted: {[m['name'] for m in rank_by_cost]}")

    ranks_differ = [m['name'] for m in rank_by_f1] != [m['name'] for m in rank_by_cost]

    print(f"\n  DECISION RULE:")
    if ranks_differ:
        decision = "FALSIFIED: Ranking differs between F1 and cost-weighted F1. F1 is misleading. Adopt cost-weighted evaluation."
    else:
        decision = "PREMISE HOLDS: Same ranking by both metrics. F1 is sufficient proxy."

    print(f"  DECISION: {decision}")

    summary = {
        "n_samples": n,
        "n_classes": n_classes,
        "models": models,
        "rank_by_f1": [m['name'] for m in rank_by_f1],
        "rank_by_cost_weighted": [m['name'] for m in rank_by_cost],
        "ranks_differ": ranks_differ,
        "decision": decision,
    }

    path = os.path.join(out_dir, "exp6_cost_weighted_f1.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Results saved to {path}")
    return summary


# ============================================================
# EXP 1: Session vs Single Query (Self-Consistency Proxy)
# ============================================================
def experiment_1_session_vs_query(clf, queries, out_dir):
    print("\n" + "="*60)
    print("EXP 1: Session vs Single Query (Proxy)")
    print("="*60)

    n = min(1000, len(queries))
    queries = queries[:n]

    single_queries = queries[::2]
    session_pairs = [(queries[i], queries[i+1])
                     for i in range(0, n-1, 2)]

    n_sessions = len(session_pairs)

    print(f"  Testing {len(single_queries)} single queries vs {n_sessions} session-pairs...")

    single_confs = []
    session_confs = []
    prediction_changes = 0

    for q_single, (q1, q2) in zip(single_queries[:n_sessions], session_pairs):
        result_single = clf.classify(q2, top_k=1, threshold=0.0)
        single_conf = result_single.labels[0]['score'] if result_single.labels else 0
        single_id = result_single.labels[0]['id'] if result_single.labels else None
        single_confs.append(single_conf)

        session_text = f"{q1} {q2}"
        result_session = clf.classify(session_text, top_k=1, threshold=0.0)
        session_conf = result_session.labels[0]['score'] if result_session.labels else 0
        session_id = result_session.labels[0]['id'] if result_session.labels else None
        session_confs.append(session_conf)

        if single_id and session_id and single_id != session_id:
            prediction_changes += 1

    single_mean = np.mean(single_confs)
    session_mean = np.mean(session_confs)
    change_rate = 100.0 * prediction_changes / n_sessions
    conf_gain = session_mean - single_mean

    print(f"  Single query mean confidence: {single_mean:.4f}")
    print(f"  Session (concat) mean confidence: {session_mean:.4f}")
    print(f"  Confidence gain from session: {conf_gain:.4f}")
    print(f"  Predictions changed by session: {prediction_changes}/{n_sessions} ({change_rate:.1f}%)")

    print(f"\n  DECISION RULE:")
    if change_rate > 20 and conf_gain > 0.03:
        decision = "WEAKENED: Session context changes predictions and increases confidence. Session-as-unit likely beneficial."
    elif change_rate > 30:
        decision = "FALSIFIED: Session context changes >30% of predictions. Query alone is insufficient."
    else:
        decision = "PREMISE HOLDS (tentative): Session context has minimal effect. Query-as-unit works."

    print(f"  DECISION: {decision}")

    summary = {
        "n_single": len(single_queries),
        "n_sessions": n_sessions,
        "single_mean_conf": float(round(float(single_mean), 4)),
        "session_mean_conf": float(round(float(session_mean), 4)),
        "conf_gain": float(round(float(conf_gain), 4)),
        "prediction_changes": int(prediction_changes),
        "change_rate_pct": float(round(change_rate, 1)),
        "decision": decision,
    }

    path = os.path.join(out_dir, "exp1_session_proxy.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Results saved to {path}")
    return summary


# ============================================================
# EXP 5: Paradigm Comparison
# ============================================================
def experiment_5_paradigm_comparison(clf, queries, out_dir):
    print("\n" + "="*60)
    print("EXP 5: Paradigm Comparison (Output Characteristics)")
    print("="*60)

    n = min(500, len(queries))
    queries = queries[:n]

    results_list = []
    for query in queries:
        result = clf.classify(query, top_k=50, threshold=0.0)
        n_labels = len(result.labels)
        scores = [l['score'] for l in result.labels]
        max_conf = max(scores) if scores else 0

        results_list.append({
            "query": query,
            "n_labels_above_zero": n_labels,
            "max_conf": max_conf,
        })

    n_labels_list = [r['n_labels_above_zero'] for r in results_list]
    max_conf_list = [r['max_conf'] for r in results_list]

    avg_n_labels = np.mean(n_labels_list)
    pct_single_class = 100.0 * sum(1 for n in n_labels_list if n == 1) / n
    pct_wide = 100.0 * sum(1 for n in n_labels_list if n >= 10) / n

    print(f"  Classification behavior ({n} queries):")
    print(f"    Mean non-zero classes per query: {avg_n_labels:.1f}")
    print(f"    Single-class predictions: {pct_single_class:.1f}%")
    print(f"    10+ class predictions: {pct_wide:.1f}%")
    print(f"    Mean max confidence: {np.mean(max_conf_list):.4f}")

    print(f"\n  Retrieval behavior (coverage at threshold):")
    for thresh in [0.1, 0.2, 0.3, 0.4, 0.5]:
        n_with_any = sum(1 for m in max_conf_list if m >= thresh)
        coverage = 100.0 * n_with_any / n
        print(f"    tau={thresh:.1f}: {n_with_any}/{n} queries have any class above threshold ({coverage:.1f}%)")

    if avg_n_labels > 20:
        decision = "WEAKENED: Classifier distributes confidence across many classes. Retrieval/ranking may be more appropriate."
    elif pct_single_class > 80:
        decision = "PREMISE HOLDS: Most queries map to a single high-confidence class. Classification is appropriate."
    else:
        decision = "TENTATIVE: Mixed behavior. Paradigm choice depends on use case."

    print(f"\n  DECISION: {decision}")

    summary = {
        "n_queries": n,
        "mean_n_labels": float(round(float(avg_n_labels), 1)),
        "pct_single_class": float(round(pct_single_class, 1)),
        "pct_wide_10plus": float(round(pct_wide, 1)),
        "mean_max_conf": float(round(float(np.mean(max_conf_list)), 4)),
        "coverage_by_threshold": {
            f"tau_{int(t*100)}": float(round(100.0 * sum(1 for m in max_conf_list if m >= t) / n, 1))
            for t in [0.1, 0.2, 0.3, 0.4, 0.5]
        },
        "decision": decision,
    }

    path = os.path.join(out_dir, "exp5_paradigm_comparison.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Results saved to {path}")
    return summary


# ============================================================
# MAIN
# ============================================================
def main():
    print("="*60)
    print("PHASE 1: Premise Resolution Experiments")
    print("="*60)

    out_dir = BASE
    queries = load_queries(N_QUERIES)
    print(f"Loaded {len(queries)} queries from MS MARCO sample")

    # Initialize model and leaf embeddings (batched to avoid OOM)
    print("Loading embedding model...")
    start = time.time()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"  Model loaded in {time.time()-start:.1f}s")

    root = build_skeleton()
    leaves = get_all_leaves(root)
    leaf_texts = [" > ".join(l.path_names()) for l in leaves]

    print(f"  Encoding {len(leaves)} leaf descriptions in batches of 256...")
    leaf_embeddings_list = []
    for i in range(0, len(leaf_texts), 256):
        batch = leaf_texts[i:i+256]
        emb = model.encode(batch, convert_to_numpy=True)
        leaf_embeddings_list.append(emb)
    leaf_embeddings = np.vstack(leaf_embeddings_list)
    leaf_embeddings = leaf_embeddings / np.linalg.norm(leaf_embeddings, axis=1, keepdims=True)
    print(f"  Leaf embeddings: {leaf_embeddings.shape}, time: {time.time()-start:.1f}s")

    class SimpleClassifier:
        pass
    clf = SimpleClassifier()
    clf.model = model
    clf.leaves = leaves
    clf.leaf_embeddings = leaf_embeddings

    def simple_classify(self, query, top_k=10, threshold=0.0):
        q_emb = self.model.encode([query], convert_to_numpy=True)
        q_emb = q_emb / np.linalg.norm(q_emb)
        scores = self.leaf_embeddings @ q_emb.T
        scores = scores.flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        labels = []
        for i in top_indices:
            if scores[i] >= threshold:
                leaf = self.leaves[i]
                labels.append({
                    "id": leaf.id,
                    "name": leaf.name,
                    "level": leaf.level,
                    "score": float(round(scores[i], 4)),
                    "path": leaf.path(),
                    "path_names": leaf.path_names(),
                })
        class Result:
            pass
        r = Result()
        r.query = query
        r.labels = labels
        r.method = 'embedding'
        r.latency_ms = 0.0
        return r
    import types
    clf.classify = types.MethodType(simple_classify, clf)

    print(f"  Classifier ready, {len(clf.leaves)} leaves, dim={clf.leaf_embeddings.shape[1]}")

    # Run experiments
    exp3_result = experiment_3_granularity_sweep(clf, queries, out_dir)
    exp11_result = experiment_11_spell_correction(clf, queries, out_dir)
    exp12_result = experiment_12_reject_option(clf, queries, out_dir)
    exp6_result = experiment_6_cost_weighted(queries, out_dir)
    exp1_result = experiment_1_session_vs_query(clf, queries, out_dir)
    exp5_result = experiment_5_paradigm_comparison(clf, queries, out_dir)

    # Summary
    print("\n" + "="*60)
    print("PHASE 1 SUMMARY")
    print("="*60)
    decisions = {
        "Exp 3 (Granularity)": exp3_result["decision"],
        "Exp 6 (Cost-Weighted)": exp6_result["decision"],
        "Exp 11 (Spell Correction)": exp11_result["decision"],
        "Exp 12 (Reject Option)": exp12_result["decision"],
        "Exp 1 (Session - proxy)": exp1_result["decision"],
        "Exp 5 (Paradigm - proxy)": exp5_result["decision"],
    }
    for name, decision in decisions.items():
        print(f"  {name:25s}: {decision}")

    print("\n  ARCHITECTURAL IMPLICATIONS:")
    for name, decision in decisions.items():
        status = "[OK]" if "HOLDS" in decision else "[~]" if "WEAKENED" in decision else "[X]"
        print(f"  {status} {name}: {decision}")

    all_results = {
        "exp3": exp3_result,
        "exp6": exp6_result,
        "exp11": exp11_result,
        "exp12": exp12_result,
        "exp1": exp1_result,
        "exp5": exp5_result,
        "summary": decisions,
    }
    path = os.path.join(out_dir, "phase1_all_results.json")
    with open(path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nAll results saved to {path}")


if __name__ == "__main__":
    main()
