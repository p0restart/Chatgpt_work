"""G2 review figures from actual saved data only."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--qa-scripts',required=True)
    args=parser.parse_args()
    sys.path.insert(0,args.qa_scripts)
    from audit_panel_alignment import require_matplotlib_panel_alignment
    root=Path(args.root); out=Path(args.output); out.mkdir(parents=True,exist_ok=False)
    df=pd.read_csv(root/'summary.csv')
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':9,'pdf.fonttype':42,
                         'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,
                         'legend.frameon':False})
    palette={'aligned':'#446C9E','separated':'#D07842','business_cost':'#648369'}
    def new():
        return plt.subplots(figsize=(180/25.4,120/25.4),layout='constrained')
    def save(fig,name,data):
        data.to_csv(out/f'{name}.csv',index=False)
        fig.canvas.draw()
        require_matplotlib_panel_alignment(fig,json_out=str(out/f'{name}.alignment.json'),strict=True)
        fig.savefig(out/f'{name}.pdf')
        fig.savefig(out/f'{name}.svg')
        fig.savefig(out/f'{name}.png',dpi=300)
        plt.close(fig)
    paired=df.pivot(index=['seed','scenario','B','evaluation'],columns='method',values='J_D').reset_index()
    paired['reduction_pct']=100*(paired['Recovery-only']-paired['Joint-dynamic'])/paired['Recovery-only']
    points=paired.pivot(index=['seed','scenario','B'],columns='evaluation',values='reduction_pct').reset_index()
    fig,ax=new()
    for scenario,g in points.groupby('scenario'):
        ax.scatter(g.fixed_attack,g.adaptive_attack,label=scenario,color=palette[scenario],s=35,alpha=.8)
    ax.axhline(0,color='.65',lw=.7); ax.axvline(0,color='.65',lw=.7)
    ax.set(xlabel='Cost reduction vs recovery-only: fixed attack (%)',
           ylabel='Cost reduction vs recovery-only: adaptive attack (%)')
    ax.legend(loc='upper left',bbox_to_anchor=(0,1.15),ncol=3)
    save(fig,'paired_ablation',points)
    subset=df[(df.method=='Joint-dynamic') & (df.evaluation=='adaptive_attack')]
    agg=subset.groupby(['scenario','B']).binding_slots.agg(['mean','std']).reset_index()
    fig,ax=new()
    for j,(scenario,g) in enumerate(agg.groupby('scenario')):
        ax.errorbar(g.B+(j-1)*.025,g['mean'],yerr=g['std'],marker='o',capsize=3,
                    color=palette[scenario],label=scenario,lw=1)
    ax.set(xlabel='Defense capacity B',ylabel='Binding control slots (mean ± SD; 3 seeds)',
           xticks=[.6,1.2,1.8],yticks=list(range(7)),ylim=(-.4,6.5))
    ax.legend(loc='upper left',bbox_to_anchor=(0,1.15),ncol=3)
    save(fig,'capacity',agg)
    records=[]
    for seed in (11,22,33):
        for b in (.6,1.2,1.8):
            values={}
            for scenario in ('separated','business_cost'):
                case=root/f'seed{seed}_{scenario}_B{b}'
                model=json.loads((case/'model.json').read_text())
                high=int(np.argmax(np.array(model['beta']).sum(axis=1)))
                controls=pd.read_csv(case/'Joint-dynamic_adaptive_attack'/'controls.csv')
                values[scenario]=controls[controls.node==high].s.mean()
            records.append(dict(seed=seed,B=b,**values,change=values['business_cost']-values['separated']))
    business=pd.DataFrame(records)
    fig,ax=new()
    for j,(seed,g) in enumerate(business.groupby('seed')):
        ax.scatter(g.B+(j-1)*.025,g.change,label=f'Seed {seed}',marker=['o','s','^'][j],s=45)
    ax.axhline(0,color='.65',lw=.7)
    ax.set(xlabel='Defense capacity B',ylabel='Mean isolation change at high-spread node (C − B)',xticks=[.6,1.2,1.8])
    ax.legend(loc='upper left',bbox_to_anchor=(0,1.15),ncol=3)
    save(fig,'business',business)
    gaps=df[df.relative_D.notna()].copy()
    (out/'gap_scope.json').write_text(json.dumps(dict(before=len(df),after=len(gaps),
        reason='Only optimized-method adaptive pairs have bilateral deviation audits; all such pairs retained.')))
    gaps['max_relative_gap']=gaps[['relative_D','relative_A']].max(axis=1)
    gaps=gaps.sort_values('max_relative_gap').reset_index(drop=True)
    gaps['ordered_case']=np.arange(1,len(gaps)+1)
    fig,ax=new()
    for method,g in gaps.groupby('method'):
        ax.scatter(g.ordered_case,100*g.max_relative_gap,s=20,label=method)
    ax.axhline(1,color='.5',ls='--',lw=1)
    ax.set(xlabel='Ordered configuration / optimized method',ylabel='Maximum relative observed improvement (%)',
           ylim=(0,max(1.12,110*gaps.max_relative_gap.max())))
    ax.legend(loc='upper left',bbox_to_anchor=(0,1.15),ncol=3)
    save(fig,'gaps',gaps)


if __name__=='__main__':
    main()
