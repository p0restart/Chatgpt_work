"""Render manuscript figures from saved runs. Run from any directory."""
import csv
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MATCHED = ROOT / "results/matched_mechanism/run01"
C2 = ROOT / "results/supplement_c2/run02"
OUT = ROOT / "manuscript/figures"
BUDGETS = ("0.6", "1.2", "1.8")
SEEDS = ("11", "22", "33")
COLORS = ("#0072B2", "#9E4C13", "#4F5963")

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "DejaVu Sans"],
    "mathtext.fontset": "dejavusans", "font.size": 8, "pdf.fonttype": 42,
    "svg.fonttype": "none", "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "axes.axisbelow": True,
})


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.svg")
    fig.savefig(OUT / f"{name}.png", dpi=600)
    plt.close(fig)


def topology():
    edges = rows(MATCHED / "seed11_B0.6_equal_high_at_node2/edges.csv")
    fig, ax = plt.subplots(figsize=(4.0, 1.85), layout="constrained")
    positions = {str(i): (i // 2, .78 if i % 2 == 0 else .22) for i in range(6)}
    for edge in edges:
        ax.annotate("", xy=positions[edge["target"]], xytext=positions[edge["source"]],
                    arrowprops=dict(arrowstyle="-|>", shrinkA=11, shrinkB=11,
                                    lw=.8, color="#637584", mutation_scale=9))
    for i, (x, y) in positions.items():
        ax.scatter(x, y, s=280, facecolor="#EEF4F7", edgecolor="#496577", zorder=3)
        ax.text(x, y, i, ha="center", va="center", zorder=4)
    for x, label in enumerate(("攻击入口", "匹配节点", "下游节点")):
        ax.text(x, 1.02, label, ha="center")
    ax.set(xlim=(-.34, 2.34), ylim=(.02, 1.18))
    ax.axis("off")
    save(fig, "fig01_matched_network")


def recovery_trajectory():
    fig, ax = plt.subplots(figsize=(4.55, 2.6), layout="constrained")
    for index, (spread, high) in enumerate((("equal", 2), ("equal", 3),
                                           ("unequal", 2), ("unequal", 3))):
        case = MATCHED / f"seed11_B0.6_{spread}_high_at_node{high}"
        control = sorted((row for row in rows(case / "fine_evaluation/controls.csv")
                          if row["node"] == "2"), key=lambda row: int(row["slot"]))
        ax.stairs([float(row["r"]) for row in control], np.linspace(0, 10, 7),
                  baseline=None, label=f"{'ABCD'[index]}组",
                  color=COLORS[index // 2], linestyle="-" if high == 2 else "--",
                  linewidth=1.35)
    ax.set(xlabel="模型时间", ylabel=r"节点 2 的恢复强度 $r_2$", xlim=(0, 10))
    ax.legend(ncol=2, loc="upper left")
    ax.grid(axis="y", color="#E5EAED", lw=.6)
    save(fig, "fig02_recovery_trajectory")


def interactions():
    source = rows(MATCHED / "paired_effects.csv")
    values = {(r["B"], r["window"], r["seed"], r["kind"], r["node"]):
              float(r["interaction"]) * 1000 for r in source if r["initialization"] == "fine"}
    channels = (("s", "2"), ("s", "3"), ("r", "2"), ("r", "3"))
    groups = [(budget, window) for budget in BUDGETS for window in ("first4", "last2")]
    data = np.array([[values[b, w, seed, kind, node] for b, w in groups for seed in SEEDS]
                     for kind, node in channels])
    extent = np.max(np.abs(data))
    fig, ax = plt.subplots(figsize=(7.15, 2.2), layout="constrained")
    chart = ax.imshow(data, cmap="RdBu_r", norm=TwoSlopeNorm(0, -extent, extent), aspect="auto")
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            if abs(value) > 1:
                ax.text(j, i, f"{value:+.1f}", ha="center", va="center", fontsize=6.5,
                        color="white" if abs(value) > extent * .68 else "#17222B")
    for boundary in range(3, 18, 3):
        ax.axvline(boundary - .5, color="white", lw=1.2)
    ax.set_yticks(range(4), [r"$s_2$", r"$s_3$", r"$r_2$", r"$r_3$"])
    ax.set_xticks(range(18), SEEDS * 6)
    ax.tick_params(length=0)
    axis = ax.secondary_xaxis("top")
    axis.set_xticks(range(1, 18, 3), [f"{b}｜{'前4槽' if w == 'first4' else '末2槽'}"
                                      for b, w in groups])
    axis.tick_params(length=0, pad=4)
    ax.set_xlabel("网络种子")
    fig.colorbar(chart, ax=ax, label=r"四格交互 $\Delta_y$（$10^{-3}$）", pad=.022)
    save(fig, "fig03_all_interactions")


def benefits():
    data = rows(C2 / "paired.csv")
    matched = [r for r in data if "unequal_high_at_node3" in r["case"]]
    methods = [
        ("Uniform", "均匀分配"), ("Value-only", "价值优先"), ("Spread-only", "传播优先"),
        ("Isolation-only", "动态仅隔离"), ("Recovery-only", "动态仅恢复"),
        ("Joint-static", "静态联合"), ("Fixed-trained", "固定攻击优化"),
    ]
    fig, ax = plt.subplots(figsize=(5.7, 3.05), layout="constrained")
    for y, (method, _) in enumerate(methods):
        for i, budget in enumerate(BUDGETS):
            vals = [float(r["reduction_percent"]) for r in matched
                    if r["evaluation"] == "adaptive_attack" and r["baseline"] == method
                    and float(r["B"]) == float(budget)]
            level = y + (i - 1) * .21
            ax.hlines(level, min(vals), max(vals), color=COLORS[i], linewidth=.85)
            ax.scatter(vals, [level] * len(vals), marker=("o", "s", "^")[i],
                       color=COLORS[i], s=13, zorder=3)
    ax.axvline(1, color="#747F86", linestyle="--", linewidth=.8)
    ax.set_yticks(range(len(methods)), [label for _, label in methods])
    ax.invert_yaxis()
    ax.set(xlabel="动态联合方案相对各基线的总防御损失降低率（%）", xlim=(-.35, 18.5))
    ax.grid(axis="x", color="#E5EAED", lw=.6)
    handles = [Line2D([], [], color=c, marker=m, linestyle="none", markersize=4, label=f"B = {b}")
               for c, m, b in zip(COLORS, ("o", "s", "^"), BUDGETS)]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5, 1.13), ncol=3)
    save(fig, "fig04_paired_baselines")


def evaluation_order():
    source = rows(C2 / "paired.csv")
    values = {(r["case"], r["evaluation"]): float(r["reduction_percent"])
              for r in source if r["baseline"] == "Fixed-trained"
              and "unequal_high_at_node3" in r["case"]}
    fig, ax = plt.subplots(figsize=(4.45, 2.65), layout="constrained")
    for budget, color in zip(BUDGETS, COLORS):
        for seed in SEEDS:
            case = f"seed{seed}_B{budget}_unequal_high_at_node3"
            ax.plot([0, 1], [values[case, "common_fixed_attack"], values[case, "adaptive_attack"]],
                    marker="o", color=color, alpha=.85, lw=.8, markersize=3)
    ax.axhline(0, color="#555F66", linestyle="--", lw=.8)
    ax.set_xticks([0, 1], ["公共固定攻击", "各自局部攻击响应"])
    ax.set(xlim=(-.22, 1.22), ylim=(-.12, .32), ylabel="相对固定攻击优化的损失降低率（%）")
    ax.grid(axis="y", color="#E5EAED", lw=.6)
    handles = [Line2D([], [], color=c, lw=1, label=f"B = {b}") for c, b in zip(COLORS, BUDGETS)]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5, 1.17), ncol=3)
    save(fig, "fig05_attack_evaluation")


def main():
    OUT.mkdir(exist_ok=True)
    topology()
    recovery_trajectory()
    interactions()
    benefits()
    evaluation_order()


if __name__ == "__main__":
    main()
