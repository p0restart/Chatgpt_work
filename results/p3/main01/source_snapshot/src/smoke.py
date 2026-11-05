"""Minimal demonstrator: simulate predetermined feasible controls, NOT optimized controls."""
import argparse
import json
from pathlib import Path
import numpy as np
import yaml
from .core import synthetic_model_from_config, simulate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    m = synthetic_model_from_config(cfg)
    K = int(cfg["K"])
    a = np.zeros((K, m.n))
    entries = np.flatnonzero(m.entry)
    # Feasible when costs are heterogeneous and only a few entry nodes exist.
    each = min(0.2, m.A / max(len(entries) * max(m.d_a[entries]), 1e-12))
    a[:, entries] = each
    s = np.zeros((K, m.n))
    r = np.zeros((K, m.n))
    out = simulate(m, a, s, r, float(cfg["T"]), int(cfg["rk4_substeps_per_slot"]))
    print(json.dumps({"label": "SMOKE_TEST_ONLY_NOT_OPTIMIZED", "n": m.n, "K": K,
                      "J_D": out["J_D"], "J_A": out["J_A"],
                      "end_state": out["states"][-1].tolist()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
