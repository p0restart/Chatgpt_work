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
                     'axes.spines.top': False, 'axes.spines.right': False, 'legend.frameon': False})
ASSETS = ['API gateway', 'Web application', 'Order processing', 'Authentication', 'Core database', 'Administration']


def load(root, name):
    return pd.read_csv(root/f'B_{name}.csv', float_precision='round_trip')


def verify(cfg, runs, states, plans, match, metrics):
    checks = []

    def eq(label, actual, expected, tolerance=1e-12):
        np.testing.assert_allclose(actual, expected, atol=tolerance, rtol=0, err_msg=label)
        checks.append(label)

    model = cfg['model']
    states_columns = [f'x{asset}' for asset in range(1, 7)]
    for label, rows in runs.items():
        trace = states[label]
        boundary = trace[states_columns].to_numpy()[::cfg['H']]
        eq(f'{label} boundary start', rows.x_start, boundary[:-1].ravel())
        eq(f'{label} boundary end', rows.x_end, boundary[1:].ravel())
        eq(f'{label} weighted states', trace.weighted_damage, trace[states_columns].to_numpy() @ model['q']/sum(model['q']))
        eq(f'{label} computed resources', rows.resource,
           rows.s*np.tile(model['b_s'], cfg['K'])+rows.r*np.tile(model['b_r'], cfg['K']))
        total = rows.groupby('slot').resource.transform('sum')
        eq(f'{label} summed resources', rows.total_defense, total)
        eq(f'{label} share', rows.share, rows.resource/total.where(total != 0))
        eq(f'{label} peak capacity usage', metrics.loc[label, 'max_defense'], total.max())
        eq(f'{label} cost decomposition', metrics.loc[label, 'J_D'],
           metrics.loc[label, ['security', 'business', 'isolation', 'recovery', 'terminal_defense']].sum())
        eq(f'{label} cost of attack', metrics.loc[label, 'attacker_effort'], 1.)
        for key in states_columns + ['weighted_damage']:
            prefix = 'weighted' if key == 'weighted_damage' else key
            eq(f'{label} {key} terminal and peak', metrics.loc[label, [f'{prefix}_terminal', f'{prefix}_peak']].to_numpy(float),
               [trace[key].iloc[-1], trace[key].max()])
    eq('C1/C2 same full attack', runs['C1'].a, runs['C2'].a, 0)
    eq('C0/C1 same defense', runs['C0'][['s','r']], runs['C1'][['s','r']], 0)
    active = pd.concat([plans[(plans.label == label)&plans.slot.between(begin, end)]
                        for label, begin, end in (('D0',1,4), ('D1',5,8), ('D2',9,12))])
    eq('C2 equals executed plan slices', runs['C2'][['a','s','r']], active[['a','s','r']], 0)
    fields = ['a','s','r','resource','share','total_defense','x_start','x_end']
    for event, label_p, label_q in ((5,'M5_old','D1'), (9,'D2','M9_old')):
        segment = match[match.event_slot == event]
        for index, plan_label in (('P', label_p), ('Q', label_q)):
            selected = plans[plans.label == plan_label]
            eq(f'{event} {index} plan data', segment[[f'{index}_{key}' for key in fields]], selected[fields], 0)
            eq(f'{event} {index} zero total flag', segment[f'{index}_zero_total'], selected.zero_defense_total, 0)
        eq(f'{event} matched Q-P', segment[[f'delta_{key}' for key in fields]],
           segment[[f'Q_{key}' for key in fields]].to_numpy()-segment[[f'P_{key}' for key in fields]].to_numpy(), 0)
        eq(f'{event} matched C2 event state', segment[segment.slot == event].state_at_event,
           runs['C2'][runs['C2'].slot == event].x_start)
    difference = metrics.loc['C1','J_D']-metrics.loc['C2','J_D']
    eq('C1-C2 loss difference', metrics.loc['C2','loss_improvement_vs_C1'], difference)
    eq('relative improvement', metrics.loc['C2','relative_improvement_vs_C1'], difference/metrics.loc['C1','J_D'])
    return checks


def header(axis, letter, title):
    axis.text(0, 1.04, letter, transform=axis.transAxes, va='bottom', fontweight='bold')
    axis.text(.065, 1.04, title, transform=axis.transAxes, va='bottom')


def save(fig, axes, out, name, qa):
    if qa:
        sys.path.insert(0, str(qa))
        from audit_panel_alignment import require_matplotlib_panel_alignment

        require_matplotlib_panel_alignment(fig, axes=axes, json_out=out/f'{name}.alignment.json',
                                           require_panel_labels=True, strict=True)
    fig.savefig(out/f'{name}.pdf', metadata={'Title':name, 'CreationDate':None})
    fig.savefig(out/f'{name}.svg')
    fig.savefig(out/f'{name}.png', dpi=600)
    fig.savefig(out/f'{name}.tiff', dpi=600, pil_kwargs={'compression':'tiff_lzw'})
    plt.close(fig)


def heatmap(fig, axis, matrix, cmap, low, high):
    mesh = axis.pcolormesh(np.arange(13)+.5, np.arange(7), matrix, cmap=cmap, vmin=low, vmax=high,
                           linewidth=.3, edgecolors='#f6f6f6')
    axis.set(ylim=(6,0), yticks=np.arange(6)+.5, yticklabels=ASSETS)
    axis.tick_params(axis='y', length=0)
    axis.spines['left'].set_visible(False)
    position = axis.get_position()
    color_axis = fig.add_axes([.867, position.y0, .018, position.height])
    scale = fig.colorbar(mesh, cax=color_axis, format=FormatStrFormatter('%.2f'))
    scale.locator = MaxNLocator(4, symmetric=low < 0)
    scale.update_ticks()
    scale.set_label('Resource units')


def render(out, cfg, runs, states, match, metrics, qa):
    out.mkdir(exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 5.35), gridspec_kw={'height_ratios':[1,1.42,1.42]})
    fig.subplots_adjust(left=.202, right=.846, top=.87, bottom=.12, hspace=.5)
    active = runs['C2']
    entries = active.pivot(index='slot', columns='asset', values='a').to_numpy()[:,:2]
    np.testing.assert_array_equal(entries, cfg['executed_entries'])
    header(axes[0], 'a', 'Observed attack allocation')
    for series, color, style, label in zip(entries.T, ('#214B73','#A54B21'), ('-',(0,(4,2))), ASSETS[:2]):
        axes[0].stairs(series, np.arange(13)+.5, baseline=None, color=color, linestyle=style, linewidth=1.75, label=label)
    axes[0].set(ylim=(.13,.47), yticks=[.2,.4], ylabel='Attack intensity')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=2, loc='upper center', bbox_to_anchor=(.53,.992))
    header(axes[1], 'b', 'Executed resource allocation by slot (C2)')
    resources = active.pivot(index='asset', columns='slot', values='resource').to_numpy()
    heatmap(fig, axes[1], resources, 'Blues', 0, resources.max())
    header(axes[2], 'c', 'Matched-state resource difference (Q − P)')
    delta = match.pivot(index='asset', columns=['event_slot','slot'], values='delta_resource').to_numpy()
    limit = abs(delta).max()
    heatmap(fig, axes[2], delta, 'RdBu_r', -limit, limit)
    for axis in axes[:2]:
        axis.set(xlim=(.5,12.5), xticks=np.arange(1,13))
        for change in (4.5,8.5):
            axis.axvline(change, color='#536278', lw=.75, dashes=(3,3))
    axes[0].tick_params(labelbottom=False)
    axes[2].axvline(8.5, color='#3D4854', lw=1.05)
    axes[2].set(xlim=(.5,12.5), xticks=np.arange(1,13),
                xticklabels=[*map(str,range(5,13)), *map(str,range(9,13))])
    for center, caption in ((.333,'State at slot 5 start'),(.833,'State at slot 9 start')):
        axes[2].text(center, -.245, caption, transform=axes[2].transAxes, ha='center', va='top')
    save(fig, axes, out, 'B1_spatial_response', qa)

    fig, axes = plt.subplots(2, 1, figsize=(7.2, 3.75), sharex=True)
    fig.subplots_adjust(left=.145, right=.96, top=.8, bottom=.15, hspace=.38)
    for axis, letter, field, title in zip(axes, 'ab', ('x5','weighted_damage'), ('Core database','Network weighted mean')):
        header(axis, letter, title)
        for label, color, style, caption in (('C2','#006D77','-','C2: replan'),('C1','#992F33',(0,(3,2)),'C1: unchanged plan')):
            axis.plot(states[label].time, 100*states[label][field], color=color, linestyle=style, lw=1.65, label=caption)
        for slot in cfg['event_slots']:
            axis.axvline((slot-1)*cfg['slot_width'], color='#536278', lw=.75, dashes=(3,3))
        axis.set_ylabel('Damage (%)')
        axis.yaxis.set_major_locator(MaxNLocator(4))
    axes[-1].set(xlim=(0,cfg['T']), xlabel='Time (model units)')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles[::-1], labels[::-1], ncol=2, loc='upper center', bbox_to_anchor=(.55,.99))
    save(fig, axes, out, 'B2_defense_outcomes', qa)
    lines = ['# 图 B2 配套表：共同实际攻击下的损失', '',
             '| 方案 | 综合损失 | 相对 C1 降低 | 相对改善 | 容量满足（峰值占用） |',
             '|---|---:|---:|---:|---|']
    for label in ('C1','C2'):
        row = metrics.loc[label]
        lines.append(f'| {label} | {row.J_D:.9f} | {row.loss_improvement_vs_C1:.9f} | '
                     f'{row.relative_improvement_vs_C1:.6%} | {"是" if row.capacity_ok else "否"}（{row.max_defense:.6f}） |')
    (out/'B2_loss_table.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--qa-scripts', type=Path)
    args = parser.parse_args()
    root = args.root
    cfg = json.loads((root/'B_run_config.json').read_text(encoding='utf-8'))
    results = {label: rows for label, rows in load(root,'results').groupby('label')}
    states = {label: rows for label, rows in load(root,'state_trajectories').groupby('label')}
    plans, match = load(root,'plans'), load(root,'spatial_response')
    metrics = load(root,'metrics').set_index('label')
    checks = verify(cfg, results, states, plans, match, metrics)
    render(root/'B_figures', cfg, results, states, match, metrics, args.qa_scripts)
    (root/'B_figure_data_checks.json').write_text(json.dumps({'passed':checks}, indent=2)+'\n', encoding='utf-8')
    print(f'{len(checks)} data checks passed')


if __name__ == '__main__':
    main()
