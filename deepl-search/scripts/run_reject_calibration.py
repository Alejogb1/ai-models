import json
import os
import numpy as np


def run():
    b9_path = os.environ.get(
        "B9_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "experiments", "b9_baseline_results.json")
    )
    output_path = os.environ.get(
        "OUTPUT_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "experiments", "reject_calibration_results.json")
    )

    print("Loading B9 results...")
    with open(b9_path) as f:
        b9 = json.load(f)

    all_results = {}

    for level in ["L1", "L2"]:
        print(f"\n=== {level} Reject Calibration ===")
        if level not in b9:
            print(f"  No {level} data")
            continue
        confs = np.array(b9[level].get("all_confidences", []))
        if len(confs) == 0:
            print(f"  No confidence data")
            continue

        thresholds = np.arange(0.0, 0.95, 0.025)
        results = []
        for tau in thresholds:
            n_above = int((confs >= tau).sum())
            coverage = n_above / len(confs)
            results.append({
                "threshold": round(float(tau), 3),
                "coverage": round(float(coverage), 4),
                "n_accepted": n_above,
                "n_rejected": len(confs) - n_above,
            })

        all_results[level] = {
            "curve": results,
            "n_classes": b9[level].get("n_classes", 0),
            "n_queries": len(confs),
            "overall_mean_confidence": round(float(confs.mean()), 4),
            "overall_std_confidence": round(float(confs.std()), 4),
        }

        for target in [0.95, 0.90, 0.80, 0.70, 0.50]:
            for r in reversed(results):
                if r["coverage"] >= target:
                    all_results[level][f"max_tau_for_{target:.0f}pct_coverage"] = {
                        "threshold": r["threshold"],
                        "coverage": r["coverage"],
                    }
                    break

        print(f"  Queries: {len(confs)}, mean conf: {confs.mean():.4f}")
        report_tau = all_results[level].get("max_tau_for_50pct_coverage", {})
        print(f"  Max tau at >=50% coverage: {report_tau.get('threshold', 'N/A')}")
        for r in [r for r in results if r["threshold"] in [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]]:
            print(f"    tau={r['threshold']:.2f}: coverage={r['coverage']:.1%}, accepted={r['n_accepted']}")

    if "L1" in b9 and "L2" in b9:
        print("\n=== Granularity Ladder ===")
        l1_confs = np.array(b9["L1"].get("all_confidences", []))
        l2_confs = np.array(b9["L2"].get("all_confidences", []))
        if len(l1_confs) > 0 and len(l2_confs) > 0:
            n = min(len(l1_confs), len(l2_confs))
            l1_a = l1_confs[:n]
            l2_a = l2_confs[:n]
            ladder = {}
            for tau in [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]:
                l2_acc = int((l2_a >= tau).sum())
                l1_fb = int(((l2_a < tau) & (l1_a >= tau)).sum())
                rej = int(((l2_a < tau) & (l1_a < tau)).sum())
                ladder[f"tau_{tau:.2f}"] = {
                    "l2_direct_pct": round(l2_acc / n * 100, 1),
                    "l1_fallback_pct": round(l1_fb / n * 100, 1),
                    "rejected_pct": round(rej / n * 100, 1),
                }
                print(f"  tau={tau:.2f}: L2={l2_acc/n*100:.1f}% L1={l1_fb/n*100:.1f}% reject={rej/n*100:.1f}%")
            all_results["granularity_ladder"] = ladder

    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    run()
