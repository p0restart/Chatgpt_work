"""Redraw manuscript Figures 2 and 4 from the D7 archive and a fixed replay."""

import csv
import hashlib
import json
from pathlib import Path
import sys

import matplotlib as mpl
import numpy as np

mpl.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PAPER = OUT.parent
ARCHIVE = PAPER / "work_d7" / "results" / "static"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PAPER / "audit_20261117" / "scripts"))

from audit_panel_alignment import require_matplotlib_panel_alignment
from src.core import Model, check_controls, simulate

BUDGETS = (0.6, 1.2, 1.8)
T = 10.0
K = 6
H = 48
ASSETS = ("API gateway", "Web application", "Order processing",
          "Authentication", "Core database", "Administration")
METRICS = ("API网关", "身份认证", "核心数据库", "全网价值加权")

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "DejaVu Sans"],
    "font.size": 8.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.65,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "path.simplify": False,
})


def load_case(budget):
    case = ARCHIVE / f"B{budget:.1f}"
    model_file = case / "model.json"
    control_file = case / "G_controls.json"
    values = json.loads(model_file.read_text(encoding="utf-8"))
    model = Model(**{k: np.array(v) if isinstance(v, list) else v
                     for k, v in values.items()})
    a, s, r = np.array(json.loads(control_file.read_text(encoding="utf-8")))
    assert model.B == budget and a.shape == (K, len(ASSETS))
    check_controls(model, a, s, r)
    return model, (a, s, r), (model_file, control_file)


def write_csv(name, header, rows):
    with (OUT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def export(fig, name):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig, json_out=OUT / f"{name}_alignment.json", strict=True)
    fig.savefig(OUT / f"{name}.png", dpi=600, facecolor="white")
    fig.savefig(OUT / f"{name}.pdf", facecolor="white")
    fig.savefig(OUT / f"{name}.svg", facecolor="white")
    plt.close(fig)


def draw_capacity(capacity):
    fig, axes = plt.subplots(1, 3, figsize=(17 / 2.54, 6.0 / 2.54), sharey=True)
    fig.subplots_adjust(left=0.105, right=0.98, bottom=0.23, top=0.73, wspace=0.23)
    slots = np.arange(1, K + 1)
    for i, (ax, (budget, isolation, recovery)) in enumerate(zip(axes, capacity)):
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#e3e3e3", linewidth=0.5)
        ax.bar(slots, isolation, color="#356B8C", width=0.67, label="源端隔离")
        ax.bar(slots, recovery, bottom=isolation, color="#D9AB62",
               width=0.67, label="本地恢复")
        ax.axhline(budget, color="#333333", linestyle="--", linewidth=1, label="容量上限")
        ax.set(title=f"({chr(97 + i)})  $B={budget:.1f}$", xticks=slots,
               ylim=(0, 2.0), yticks=[0, 0.6, 1.2, 1.8])
    axes[0].set_ylabel("归一化资源占用")
    fig.supxlabel("控制区间", x=0.542, y=0.045, fontsize=9)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.542, 0.98),
               ncol=3, frameon=False)
    export(fig, "fig2_resource_use")


def draw_states(t, display):
    fig, axes = plt.subplots(2, 2, figsize=(17 / 2.54, 11.2 / 2.54), sharex=True)
    fig.subplots_adjust(left=0.133, right=0.977, bottom=0.14, top=0.82,
                        wspace=0.29, hspace=0.43)
    styles = (("G 动态防御", "#2166AC", "-"),
              ("M 固定均值防御", "#AF5808", "--"),
              ("N 无防御", "#AD2B46", ":"))
    for i, ax in enumerate(axes.flat):
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#e3e3e3", linewidth=0.5)
        ax.axvline(5 * T / K, color="#777777", linewidth=0.8, zorder=1)
        for (label, color, style), values in zip(styles, display.values()):
            (line,) = ax.plot(t, values[:, i], color=color, linestyle=style,
                              label=label, linewidth=1.5)
            np.testing.assert_array_equal(line.get_xydata(), np.column_stack((t, values[:, i])))
        max_y = max(values[:, i].max() for values in display.values())
        ax.set(title=f"({chr(97 + i)})  {METRICS[i]}", xlim=(0, T),
               ylim=(0, max_y * 1.08), xticks=np.arange(0, T + 1, 2))
    fig.supxlabel("时间 $t$", x=0.555, y=0.036, fontsize=9)
    fig.supylabel("受损比例", x=0.029, y=0.48, fontsize=9)
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="upper center",
               bbox_to_anchor=(0.555, 0.97), ncol=3, frameon=False)
    export(fig, "fig4_state_trajectories")


def main():
    capacity = []
    sources = []
    for budget in BUDGETS:
        model, (a, s, r), files = load_case(budget)
        sources.extend(files)
        capacity.append((budget, s @ model.b_s, r @ model.b_r))
    write_csv("fig2_capacity.csv",
              ["budget", "slot", "t_start", "t_end", "isolation", "recovery", "total"],
              ((b, k + 1, k * T / K, (k + 1) * T / K, c_s, c_r, c_s + c_r)
               for b, iso, rec in capacity for k, (c_s, c_r) in enumerate(zip(iso, rec))))

    model, (a, s, r), _ = load_case(1.2)
    archive_states = ARCHIVE / "B1.2" / "G_states.csv"
    sources.extend((archive_states, ROOT / "src" / "core.py"))
    archived = np.loadtxt(archive_states, delimiter=",", skiprows=1)
    t = archived[:, 0]
    np.testing.assert_array_equal(t, np.arange(K * H + 1) * (T / (K * H)))
    plans = {
        "G": (s, r),
        "M": (np.broadcast_to(s.mean(axis=0), s.shape), np.broadcast_to(r.mean(axis=0), r.shape)),
        "N": (np.zeros_like(s), np.zeros_like(r)),
    }
    write_csv("fig4_controls.csv",
              ["plan", "slot", "t_start", "t_end", "asset_id", "asset", "a", "s", "r"],
              ((name, k + 1, k * T / K, (k + 1) * T / K, f"v{i+1}", asset,
                a[k, i], sk[k, i], rk[k, i])
               for name, (sk, rk) in plans.items() for k in range(K)
               for i, asset in enumerate(ASSETS)))

    state_rows = []
    display = {}
    report = {
        "inputs_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sources},
        "RK4_substeps_per_slot": H,
        "points_per_plan": t.size,
        "published_table_3_columns": ["security", "business_and_action", "J_D", "X_q(T)"],
        "plans": {},
    }
    published = {
        "G": (8.176990, 1.149657, 9.326647, 0.157163),
        "M": (8.580319, 0.976515, 9.556834, 0.156868),
        "N": (10.945701, 0.0, 10.945701, 0.221271),
    }
    for name, (sk, rk) in plans.items():
        run = simulate(model, a, sk, rk, T, H)
        np.testing.assert_array_equal(run["times"], t)
        x = run["states"]
        refined = simulate(model, a, sk, rk, T, 4 * H)
        if name == "G":
            np.testing.assert_allclose(x, archived[:, 1:], rtol=0, atol=1e-13)
            report["G_archive_replay_max_abs_error"] = float(np.max(np.abs(x - archived[:, 1:])))
            x = archived[:, 1:]
        weighted = x @ model.q / model.q.sum()
        display[name] = np.column_stack((x[:, [0, 3, 4]], weighted))
        state_rows.extend((name, time, *state, weight) for time, state, weight in zip(t, x, weighted))
        p = run["parts"]
        computed = [p["security"], p["business"] + p["isolation"] + p["recovery"],
                    run["J_D"], weighted[-1]]
        np.testing.assert_array_equal(np.round(computed, 6), published[name])
        report["plans"][name] = {
            "state_source": "archive" if name == "G" else "fixed-control RK4 replay",
            "table_3_metrics": computed,
            "terminal_state_v1_to_v6": x[-1].tolist(),
            "terminal_plot_values": display[name][-1].tolist(),
            "H48_vs_H192_max_abs_state_error": float(np.max(np.abs(x - refined["states"][::4]))),
            "peak_gateway_time": float(t[np.argmax(x[:, 0])]),
        }
    write_csv("fig4_states.csv", ["plan", "t", *(f"x_v{i+1}" for i in range(len(ASSETS))), "X_q"],
              state_rows)

    cross = {}
    for metric, diff in zip(METRICS, (display["G"] - display["M"]).T):
        # The common initial state is excluded because it is not a rank reversal.
        indices = np.flatnonzero(diff[:-1] * diff[1:] < 0)
        cross[metric] = [
            {"bracket": [float(t[i]), float(t[i+1])],
             "G_minus_M": [float(diff[i]), float(diff[i+1])],
             "linear_estimate": float(t[i] - diff[i] * (t[i+1] - t[i]) / (diff[i+1] - diff[i]))}
            for i in indices
        ]
    report["G_M_sign_changes"] = cross
    np.testing.assert_array_equal(np.round(capacity[1][1] + capacity[1][2], 6),
                                  [0.843705, 1.2, 1.2, 1.2, 1.065570, 0.337751])
    (OUT / "verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    draw_capacity(capacity)
    draw_states(t, display)


if __name__ == "__main__":
    main()
