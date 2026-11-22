import argparse
import json
import sys
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd

mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, MaxNLocator

mpl.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'],
                     'font.size': 9, 'pdf.fonttype': 42, 'svg.fonttype': 'none',
                     'axes.spines.right': False, 'axes.spines.top': False,
                     'axes.linewidth': .75, 'legend.frameon': False})
ASSETS = ('API gateway', 'Web application', 'Order processing', 'Authentication', 'Core database', 'Administration')


def load(root, name):
    return pd.read_csv(root / f'{name}.csv', float_precision='round_trip')


def verify_csv(root, cfg, slots, states, metrics):
    model, steps = cfg['model'], cfg['H']
    checks = []

    def equal(label, actual, expected, atol=1e-12):
        np.testing.assert_allclose(actual, expected, rtol=0, atol=atol, err_msg=label)
        checks.append(label)

    plans = load(root, 'A_plans')
    matched = load(root, 'A_matched_response')
    for label, group in slots.items():
        trace = states[label]
        boundary = trace.filter(regex='^x[1-6]$').to_numpy()[::steps]
        equal(f'{label}: start state from full trajectory', group.x_start, boundary[:-1].ravel())
        equal(f'{label}: end state from full trajectory', group.x_end, boundary[1:].ravel())
        equal(f'{label}: weighted trajectory', trace.weighted_damage,
              trace.filter(regex='^x[1-6]$').to_numpy() @ model['q']/sum(model['q']))
        equal(f'{label}: asset resource', group.resource,
              group.s*np.tile(model['b_s'], cfg['K'])+group.r*np.tile(model['b_r'], cfg['K']))
        calculated = group.groupby('slot').resource.transform('sum')
        equal(f'{label}: slot resource', group.total_defense, calculated)
        equal(f'{label}: reported peak resource', metrics.loc[label, 'max_defense'], calculated.max())
        equal(f'{label}: objective decomposition', metrics.loc[label, 'J_D'],
              metrics.loc[label, ['security', 'business', 'isolation', 'recovery', 'terminal_defense']].sum())
        for name, field in (('api', 'x1'), ('db', 'x5'), ('weighted', 'weighted_damage')):
            equal(f'{label}: {name} terminal and peak', metrics.loc[label, [f'{name}_terminal', f'{name}_peak']].to_numpy(dtype=float),
                  [trace[field].iloc[-1], trace[field].max()])
    equal('C1 and C2 use identical actual attacks', slots['C1'].a, slots['C2'].a, 0)
    equal('C0 and C1 use D0', slots['C1'][['s', 'r']], slots['C0'][['s', 'r']], 0)
    executed = pd.concat([plans[(plans.label == plan) & plans.slot.between(first, last)]
                          for plan, first, last in (('D0', 1, 4), ('D1', 5, 8), ('D2', 9, 12))])
    equal('C2 controls equal executed slices of D0/D1/D2', slots['C2'][['a', 's', 'r']], executed[['a', 's', 'r']], 0)
    for event, new, old in ((5, 'D1', 'M5_old'), (9, 'D2', 'M9_old')):
        match = matched[matched.event_slot == event]
        old_plan, new_plan = plans[plans.label == old], plans[plans.label == new]
        fields = ['a', 's', 'r', 'resource', 'total_defense', 'x_start', 'x_end']
        for prefix, plan in (('old', old_plan), ('new', new_plan)):
            equal(f'slot {event}: {prefix} matched export', match[[f'{prefix}_{name}' for name in fields]], plan[fields], 0)
        equal(f'slot {event}: matched differences', match[[f'delta_{name}' for name in fields]],
              new_plan[fields].to_numpy()-old_plan[fields].to_numpy())
        equal(f'slot {event}: event state from C2', match[match.slot == event].state_at_event,
              slots['C2'][slots['C2'].slot == event].x_start)
    equal('loss improvement', metrics.loc['C2', 'loss_improvement_vs_C1'], metrics.loc['C1', 'J_D']-metrics.loc['C2', 'J_D'])
    return checks


def save(fig, axes, out, name, qa_scripts):
    if qa_scripts:
        sys.path.insert(0, str(qa_scripts))
        from audit_panel_alignment import require_matplotlib_panel_alignment

        require_matplotlib_panel_alignment(fig, axes=axes, json_out=out/f'{name}.alignment.json',
                                           require_panel_labels=True, strict=True)
    fig.savefig(out/f'{name}.pdf', metadata={'Title': name, 'CreationDate': None})
    fig.savefig(out/f'{name}.svg')
    fig.savefig(out/f'{name}.png', dpi=600)
    fig.savefig(out/f'{name}.tiff', dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
    plt.close(fig)


def header(axis, letter, text):
    axis.text(0., 1.035, letter, transform=axis.transAxes, ha='left', va='bottom', fontweight='bold')
    axis.text(.075, 1.035, text, transform=axis.transAxes, ha='left', va='bottom')


def mark_events(axes, events):
    for axis in axes:
        for time in events:
            axis.axvline(time, color='#536278', lw=.75, dashes=(3, 3), alpha=.75)


def figures(root, cfg, slots, trajectories, metrics, qa_scripts):
    out = root / 'A_figures'
    out.mkdir(exist_ok=True)
    bounds = np.linspace(0, cfg['T'], cfg['K']+1)
    events = bounds[np.array(cfg['event_slots'])-1]
    active, unchanged = slots['C2'], slots['C1']
    resource = active.pivot(index='asset', columns='slot', values='resource').to_numpy()
    difference = resource-unchanged.pivot(index='asset', columns='slot', values='resource').to_numpy()
    active_api = active[active.asset == 1].a.to_numpy()
    np.testing.assert_array_equal(active_api, cfg['executed_api'])
    figure, axes = plt.subplots(3, 1, figsize=(7.2, 5.7), sharex=True,
                                gridspec_kw={'height_ratios': [1, 1.48, 1.48]})
    figure.subplots_adjust(left=.215, right=.835, top=.93, bottom=.095, hspace=.39)
    header(axes[0], 'a', 'External API gateway input (C1 and C2)')
    axes[0].stairs(active_api, bounds, baseline=None, color='#214B73', linewidth=2)
    axes[0].set(ylim=(.14, .46), yticks=[.20, .30, .40], ylabel='Attack intensity')
    axes[0].yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    absolute_limit = np.max(np.abs(difference))
    for axis, matrix, cmap, low, high, letter, title, scale in (
        (axes[1], resource, 'Blues', 0, resource.max(), 'b', 'Resource allocation with replanning (C2)', 'Resource units'),
        (axes[2], difference, 'RdBu_r', -absolute_limit, absolute_limit, 'c', 'Resource shift relative to unchanged plan (C2 − C1)', 'Resource units')):
        header(axis, letter, title)
        axis.spines['left'].set_visible(False)
        axis.spines['bottom'].set_visible(False)
        heatmap = axis.pcolormesh(bounds, np.arange(7), matrix, cmap=cmap, vmin=low, vmax=high,
                                  shading='flat', linewidth=.3, edgecolors='#f5f6f7')
        axis.set(yticks=np.arange(6)+.5, yticklabels=ASSETS, ylim=(6, 0))
        axis.tick_params(axis='y', length=0)
        position = axis.get_position()
        color_axis = figure.add_axes([.853, position.y0, .019, position.height])
        colorbar = figure.colorbar(heatmap, cax=color_axis, format=FormatStrFormatter('%.2f'))
        colorbar.locator = MaxNLocator(4, symmetric=(letter == 'c'))
        colorbar.update_ticks()
        colorbar.set_label(scale)
    mark_events(axes, events)
    axes[-1].set(xlim=(0, cfg['T']), xticks=np.arange(0, 11, 2), xlabel='Time (model units)')
    save(figure, axes, out, 'A1_attack_resource', qa_scripts)

    figure, axes = plt.subplots(3, 1, figsize=(7.2, 5.6), sharex=True)
    figure.subplots_adjust(left=.15, right=.96, top=.82, bottom=.095, hspace=.41)
    for axis, letter, key, title in zip(axes, 'abc', ('x1', 'x5', 'weighted_damage'),
                                       ('API gateway', 'Core database', 'Network weighted mean')):
        header(axis, letter, title)
        for label, color, linestyle, name in (('C2', '#006D77', '-', 'C2: replan'),
                                               ('C1', '#992F33', (0, (3.1, 2.4)), 'C1: unchanged plan')):
            trace = trajectories[label]
            axis.plot(trace.time, 100*trace[key], color=color, linestyle=linestyle, linewidth=1.65, label=name)
        axis.set_ylabel('Damage (%)')
        axis.yaxis.set_major_locator(MaxNLocator(4))
    mark_events(axes, events)
    axes[-1].set(xlim=(0, cfg['T']), xticks=np.arange(0, 11, 2), xlabel='Time (model units)')
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles[::-1], labels[::-1], loc='upper center', ncol=2, bbox_to_anchor=(.55, .974))
    save(figure, axes, out, 'A2_defense_outcomes', qa_scripts)

    first, second = metrics.loc['C1'], metrics.loc['C2']
    (out/'A2_loss_table.md').write_text(
        '# 图 A2 配套表：共同实际攻击下的防御损失\n\n'
        '| 方案 | 综合损失 | 相对 C1 的损失降低 | 相对改善 | 防御容量约束 |\n'
        '|---|---:|---:|---:|---|\n'
        f'| C1：原计划 | {first.J_D:.9f} | — | — | 满足（峰值 {first.max_defense:.6f}） |\n'
        f'| C2：重规划 | {second.J_D:.9f} | {second.loss_improvement_vs_C1:.9f} | '
        f'{second.relative_improvement_vs_C1:.6%} | 满足（峰值 {second.max_defense:.6f}） |\n\n'
        '来源：`A_metrics.csv`。损失为模型单位，相对改善以 C1 损失为分母。\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--qa-scripts', type=Path)
    args = parser.parse_args()
    root = args.root
    cfg = json.loads((root/'A_run_config.json').read_text(encoding='utf-8'))
    slots = {name: group for name, group in load(root, 'A_results').groupby('label')}
    traces = {name: group for name, group in load(root, 'A_state_trajectories').groupby('label')}
    metrics = load(root, 'A_metrics').set_index('label')
    checks = verify_csv(root, cfg, slots, traces, metrics)
    figures(root, cfg, slots, traces, metrics, args.qa_scripts)
    (root/'A_figure_data_checks.json').write_text(json.dumps({'passed': checks}, indent=2)+'\n', encoding='utf-8')
    print(f'{len(checks)} source-data checks passed; figures exported')


if __name__ == '__main__':
    main()
