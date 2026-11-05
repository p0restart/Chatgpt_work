"""Recalculate chapter 5 source tables without rerunning or changing experiments."""
import csv
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATCHED = ROOT / "results/matched_mechanism/run01"
C2 = ROOT / "results/supplement_c2/run02"
OUT = ROOT / "manuscript/sections/data"
SOURCES = {}


def read_csv(path):
    SOURCES[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_json(path):
    SOURCES[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(name, rows):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    paired = read_csv(C2 / "paired.csv")
    matched = [row for row in paired if "unequal_high_at_node3" in row["case"]]
    assert len({row["case"] for row in matched}) == 9
    assert len(matched) == 126
    summary = read_csv(C2 / "comparison/summary.csv")
    assert len(summary) == 160
    indexed = {(row["case"], row["evaluation"], row["method"]): row for row in summary}
    pair_errors = []
    for row in paired:
        joint = float(indexed[row["case"], row["evaluation"], "Joint-dynamic"]["fine_J_D"])
        baseline = float(indexed[row["case"], row["evaluation"], row["baseline"]]["fine_J_D"])
        reduction = 100 * (baseline - joint) / baseline
        pair_errors.extend((abs(joint - float(row["joint"])),
                            abs(baseline - float(row["baseline_cost"])),
                            abs(reduction - float(row["reduction_percent"]))))
    assert max(pair_errors) < 1e-10

    by_budget = []
    statistics_rows = []
    for evaluation in ("adaptive_attack", "common_fixed_attack"):
        for baseline in sorted({row["baseline"] for row in matched}):
            group = [row for row in matched if row["evaluation"] == evaluation
                     and row["baseline"] == baseline]
            values = [float(row["reduction_percent"]) for row in group]
            assert len(values) == 9
            statistics_rows.append(dict(evaluation=evaluation, baseline=baseline, count=9,
                min=min(values), median=statistics.median(values), max=max(values),
                positive_count=sum(value > 1e-8 for value in values),
                at_least_1pct=sum(value >= 1 for value in values)))
            for budget in (0.6, 1.2, 1.8):
                values = [float(row["reduction_percent"]) for row in group
                          if float(row["B"]) == budget]
                assert len(values) == 3
                by_budget.append(dict(evaluation=evaluation, B=budget, baseline=baseline,
                    count=3, min=min(values), median=statistics.median(values), max=max(values),
                    at_least_1pct=sum(value >= 1 for value in values)))
    saved = read_csv(C2 / "comparison_statistics.csv")
    errors = [abs(float(actual[key]) - float(expected[key]))
              for actual in statistics_rows
              for expected in saved
              if (actual["evaluation"], actual["baseline"]) ==
                 (expected["evaluation"], expected["baseline"])
              for key in ("count", "min", "median", "max", "positive_count", "at_least_1pct")]
    assert len(errors) == 14 * 6 and max(errors) < 1e-10
    write_csv("ch05_benefits_by_case.csv", matched)
    write_csv("ch05_benefits_by_budget.csv", by_budget)
    write_csv("ch05_benefits_overall.csv", statistics_rows)

    finite = []
    for budget in (0.6, 1.2):
        for step in (0.6, 0.3):
            row = read_json(C2 / f"finite/B{budget}/step{step}/audit.json")
            assert row["pairs"] == row["defense_plans"] * row["attack_plans"]
            assert row["pure_equilibria"] == 1 and not row["continuous_certificate"]
            finite.append(row)
    assert sum(row["pairs"] for row in finite) == 386397
    write_csv("ch05_finite_verification.csv", finite)

    mechanism = read_csv(MATCHED / "robust_effects.csv")
    capacities = read_csv(MATCHED / "capacity_summary.csv")
    low = [row for row in mechanism if float(row["B"]) == 0.6
           and row["window"] == "first4" and row["kind"] == "r"]
    assert len(low) == 6 and all(float(row["interaction"]) < -0.001 for row in low)
    capacity_ranges = []
    for budget in (0.6, 1.2, 1.8):
        for window in ("all", "first4", "last2"):
            group = [row for row in capacities if f"_B{budget}_" in row["case"]
                     and row["window"] == window]
            values = [int(row["binding_slots"]) for row in group]
            assert len(values) == 12
            capacity_ranges.append(dict(B=budget, window=window,
                                        minimum=min(values), maximum=max(values)))
    write_csv("ch05_capacity_binding.csv", capacity_ranges)
    components = []
    for budget in (0.6, 1.2, 1.8):
        group = [row for row in summary if "unequal_high_at_node3" in row["case"]
                 and row["evaluation"] == "adaptive_attack"
                 and row["method"] == "Joint-dynamic" and float(row["B"]) == budget]
        assert len(group) == 3
        components.append(dict(B=budget, **{key: statistics.mean(float(row[key]) for row in group)
            for key in ("security", "business", "isolation", "recovery",
                        "defense_use_mean", "binding_slots")}))
    write_csv("ch05_joint_components.csv", components)
    counterexample = [row for row in paired if row["case"] == "seed33_business_cost_B0.6"
                      and row["evaluation"] == "adaptive_attack"
                      and row["baseline"] == "Recovery-only"]
    assert len(counterexample) == 1 and float(counterexample[0]["reduction_percent"]) < 0
    ma = read_json(MATCHED / "audit.json")
    ca = read_json(C2 / "independent_audit.json")
    assert ma["cases"] == ma["numerical_pass_count"] == 36
    assert not ma["global_certificate"] and not ca["continuous_global_certificate"]
    result = dict(check_date="2026-11-03", scope="saved-data arithmetic and chapter source tables only",
        new_experiments_run=False, G2="PENDING", matched_mechanism_cases=36,
        matched_comparison_cases=9, comparison_evaluations=160,
        paired_reduction_rows_checked=len(paired), max_pair_recalculation_error=max(pair_errors),
        max_statistics_difference=max(errors), finite_table_count=4, finite_strategy_pairs=386397,
        low_budget_first4_recovery_interaction_range=[min(float(row["interaction"]) for row in low),
                                                     max(float(row["interaction"]) for row in low)],
        counterexample=counterexample[0], matched_audit=ma, C2_audit=ca, source_sha256=SOURCES)
    (OUT / "ch05_checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("matched_mechanism_cases", "matched_comparison_cases",
        "paired_reduction_rows_checked", "max_pair_recalculation_error", "max_statistics_difference",
        "finite_strategy_pairs", "low_budget_first4_recovery_interaction_range", "counterexample")},
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
