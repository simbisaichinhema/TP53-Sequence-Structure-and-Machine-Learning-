"""Smoke tests for the multi-model benchmark upgrade.

Run from the repository root:
  python3 scripts/machine_learning/test_benchmark_smoke.py

Checks (no network, no retraining of the full benchmark):
  1. Baseline train.py artefacts still load and predict
  2. Every baseline model bundle in benchmark/models/ predicts
  3. Metrics helpers return expected keys / finite values
  4. Required result/figure files exist after a benchmark run
  5. Fair-protocol invariants (same features, seed, split size in config)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib  # noqa: E402
import pandas as pd  # noqa: E402

from metrics_utils import RATE_METRICS, binary_metrics  # noqa: E402
from model_registry import DEFAULT_BENCHMARK_MODELS, all_specs  # noqa: E402
from predict import predict_variant  # noqa: E402

FEAT_CSV = REPO / "data/processed/structural_features/tp53_features.csv"
RES = REPO / "results/machine_learning"
BENCH = RES / "benchmark"
FIG = REPO / "figures/machine_learning/benchmark"

failures: list[str] = []


def check(cond: bool, msg: str):
    if cond:
        print(f"  PASS  {msg}")
    else:
        print(f"  FAIL  {msg}")
        failures.append(msg)


def main() -> int:
    print("== 1. baseline model.joblib + predict ==")
    check((RES / "model.joblib").exists(), "default model.joblib exists")
    out = predict_variant(175, "R", "H")
    check(out["prediction"] == 1, "R175H predicted pathogenic via default")
    check(out["model"] == "random_forest", "default model is random_forest")

    print("== 2. benchmark artefacts ==")
    check((BENCH / "benchmark_results.csv").exists(),
          "benchmark_results.csv exists")
    check((BENCH / "benchmark_results.json").exists(),
          "benchmark_results.json exists")
    check((BENCH / "experiment_config.json").exists(),
          "experiment_config.json exists")
    check((BENCH / "benchmark_report.md").exists(),
          "benchmark_report.md exists")
    check((BENCH / "tuned_benchmark.json").exists(),
          "tuned_benchmark.json exists")
    check((RES / "position_aware" / "position_aware_results.json").exists(),
          "position_aware_results.json exists")

    cfg = json.loads((BENCH / "experiment_config.json").read_text())
    check(cfg["seed"] == 42, "experiment seed is 42")
    check(cfg["test_size"] == 0.2, "test_size is 0.2")
    check(cfg["n_splits"] == 5, "n_splits is 5")
    check(cfg["n_train"] == int(0.8 * cfg["n_samples"])
          or abs(cfg["n_train"] / cfg["n_samples"] - 0.8) < 0.02,
          f"train is ~80% (train={cfg['n_train']}, n={cfg['n_samples']})")
    check(cfg["n_train"] + cfg["n_test"] == cfg["n_samples"],
          "train+test == n_samples")
    check(cfg["test_set_used_for_selection"] is False,
          "test not used for selection")
    check(len(cfg["features"]) == 21, "21 features in config")

    payload = json.loads((BENCH / "benchmark_results.json").read_text())
    names = [r["name"] for r in payload["results"]]
    check(len(names) == 3, f"default benchmark has 3 models (got {names})")
    for required in DEFAULT_BENCHMARK_MODELS:
        check(required in names, f"default model present: {required}")
    # Extra registry models must not sneak into the default report
    extras = set(names) - set(DEFAULT_BENCHMARK_MODELS)
    check(not extras, f"no extra models in default report ({extras or 'none'})")

    print("== 3. metrics helpers ==")
    y_true = [0, 0, 1, 1, 1, 0]
    y_pred = [0, 1, 1, 1, 0, 0]
    y_prob = [0.1, 0.6, 0.9, 0.7, 0.4, 0.2]
    m = binary_metrics(y_true, y_pred, y_prob)
    for k in RATE_METRICS + ("tn", "fp", "fn", "tp"):
        check(k in m, f"metric key {k}")
    check(m["tn"] + m["fp"] + m["fn"] + m["tp"] == len(y_true),
          "confusion counts sum to n")
    check(0 <= m["mcc"] <= 1, "MCC in [0,1] for this example")

    print("== 4. per-model joblib predict ==")
    model_dir = BENCH / "models"
    check(model_dir.exists(), "models/ directory exists")
    for spec in all_specs():
        path = model_dir / f"{spec.name}.joblib"
        if not path.exists():
            if spec.optional:
                print(f"  SKIP  optional artefact missing: {spec.name}")
                continue
            check(False, f"artefact missing: {path.name}")
            continue
        bundle = joblib.load(path)
        check(set(bundle) >= {"pipeline", "features", "model_name", "seed"},
              f"bundle schema ok: {spec.name}")
        pred = predict_variant(248, "R", "Q", model_path=str(path))
        check(pred["prediction"] in (0, 1),
              f"predict works with {spec.name}")
        check(pred["model"] == spec.name,
              f"model_name field matches: {spec.name}")

    print("== 5. figures ==")
    for fname in (
        "accuracy_comparison.png", "f1_comparison.png",
        "roc_auc_comparison.png", "precision_recall_curves.png",
        "roc_curves.png", "confusion_matrices.png",
        "cv_performance_variability.png", "pr_auc_comparison.png",
    ):
        check((FIG / fname).exists() and (FIG / fname).stat().st_size > 1000,
              f"figure {fname}")

    print("== 6. feature matrix unchanged ==")
    df = pd.read_csv(FEAT_CSV)
    check(len(df) >= 500, f"feature matrix n>=500 (got {len(df)})")
    n_pos = int(df["label"].sum())
    n_neg = len(df) - n_pos
    check(n_pos > 100 and n_neg > 100,
          f"class balance P={n_pos} B={n_neg} both >100")
    check(df.duplicated(["pos", "ref", "alt"]).sum() == 0,
          "no duplicate (pos, ref, alt)")

    print()
    if failures:
        print(f"{len(failures)} FAILURE(S)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("All smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
