import argparse
import json
import sys
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd

mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

mpl.rcParams.update({'font.family':'sans-serif', 'font.sans-serif':['Arial','DejaVu Sans'],
                     'font.size':9, 'pdf.fonttype':42, 'svg.fonttype':'none',
                     'axes.spines.top':False, 'axes.spines.right':False, 'legend.frameon':False})
ASSETS = ['API gateway','Web application','Order processing','Authentication','Core database','Administration']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--qa-scripts',type=Path)
    args = parser.parse_args()
    root = args.root
    match = pd.read_csv(root/'A_R1_matched_response.csv',float_precision='round_trip')
    results = pd.read_csv(root/'A_R1_results.csv',float_precision='round_trip')
    metrics = pd.read_csv(root/'A_R1_metrics.csv',float_precision='round_trip')
    checks = []

    def eq(label, lhs, rhs, tolerance=0):
        np.testing.assert_allclose(lhs,rhs,rtol=0,atol=tolerance,err_msg=label)
        checks.append(label)

    keys = ['s','r','resource']
    base = match[match.api_forecast == .20]
    middle = match[match.api_forecast == .30]
    for intensity, rows in match.groupby('api_forecast'):
        eq(f'{intensity}: shared initial states',rows.shared_x4,base.shared_x4)
        eq(f'{intensity}: matching slot and asset keys',rows[['slot','asset']],base[['slot','asset']])
        for baseline, suffix in ((base,'020'),(middle,'030')):
            eq(f'{intensity}: computed difference relative to {suffix}',
               rows[[f'delta_{key}_vs_{suffix}' for key in keys]],rows[keys].to_numpy()-baseline[keys].to_numpy())
    for scenario, intensity in (('S1',.30),('S2',.40)):
        actual = results[(results.scenario == scenario)&(results.label == 'C2')&results.slot.between(5,8)]
        forecast = match[(match.api_forecast == intensity)&match.slot.between(5,8)]
        eq(f'{scenario}: matched plan agrees with execution before slot 9',actual[keys],forecast[keys],1e-8)
        summary = metrics[metrics.scenario == scenario].set_index('label')
        gain = summary.loc['C1','J_D']-summary.loc['C2','J_D']
        eq(f'{scenario}: absolute improvement',summary.loc['C2','loss_improvement_vs_C1'],gain)
        eq(f'{scenario}: relative improvement',summary.loc['C2','relative_improvement_vs_C1'],gain/summary.loc['C1','J_D'])

    fig,axes = plt.subplots(1,3,sharey=True,figsize=(7.2,3.0))
    fig.subplots_adjust(left=.185,right=.975,bottom=.19,top=.78,wspace=.30)
    positions = np.arange(6)
    for axis, letter, field, title, unit in zip(axes,'abc',keys,('Isolation','Recovery','Resource use'),
                                               ('Change in intensity','Change in intensity','Change (resource units)')):
        axis.text(0,1.045,letter,transform=axis.transAxes,va='bottom',fontweight='bold')
        axis.text(.1,1.045,title,transform=axis.transAxes,va='bottom')
        axis.axvline(0,lw=.7,color='#6B7280')
        for intensity, color, offset in ((.30,'#007A80',-.18),(.40,'#355B99',.18)):
            frame = match[(match.slot == 5)&(match.api_forecast == intensity)].sort_values('asset')
            axis.barh(positions+offset,frame[f'delta_{field}_vs_020'],height=.31,color=color,
                      label=f'API intensity {intensity:.2f}')
        axis.xaxis.set_major_locator(MaxNLocator(3))
        axis.set_xlabel(unit)
    axes[0].set(yticks=positions,yticklabels=ASSETS,ylim=(5.55,-.55))
    handles,labels = axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',ncol=2,bbox_to_anchor=(.59,1))
    if args.qa_scripts:
        sys.path.insert(0,str(args.qa_scripts))
        from audit_panel_alignment import require_matplotlib_panel_alignment

        require_matplotlib_panel_alignment(fig,axes=axes,json_out=root/'A_R1_sensitivity.alignment.json',
                                           require_panel_labels=True,strict=True)
    fig.savefig(root/'A_R1_sensitivity.png',dpi=600)
    fig.savefig(root/'A_R1_sensitivity.pdf',metadata={'CreationDate':None})
    fig.savefig(root/'A_R1_sensitivity.svg')
    fig.savefig(root/'A_R1_sensitivity.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    plt.close(fig)
    (root/'A_R1_figure_data_checks.json').write_text(json.dumps({'passed':checks},indent=2)+'\n',encoding='utf-8')
    print(f'{len(checks)} figure-data checks passed')


if __name__ == '__main__':
    main()
