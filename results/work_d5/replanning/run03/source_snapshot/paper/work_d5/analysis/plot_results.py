"""D5 figures from saved executed controls and paired results only."""
import argparse
from pathlib import Path
import sys
import json
import subprocess
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

SKILL=Path('C:/Users/Jin/.codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure')
sys.path.insert(0,str(SKILL/'scripts'))
from audit_panel_alignment import require_matplotlib_panel_alignment

plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
    'font.size':8,'axes.labelsize':8,'axes.titlesize':9,'xtick.labelsize':7,'ytick.labelsize':7,
    'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False,
    'svg.fonttype':'none','pdf.fonttype':42,'axes.linewidth':.7})
COLORS={'P':'#6A7179','G':'#237A9D','R':'#AF623A'}
LINES={'P':'--','G':'-','R':':'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('run');args=ap.parse_args()
    out=Path(args.run);figdir=out/'figures';figdir.mkdir(exist_ok=True)
    c=pd.read_csv(out/'executed_controls.csv');tr=pd.read_csv(out/'trajectories.csv')
    paired=pd.read_csv(out/'comparisons.csv');allqa=[]
    def save(fig,name):
        fig.canvas.draw()
        require_matplotlib_panel_alignment(fig,json_out=figdir/f'{name}.alignment.json',
            tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
        fig.savefig(figdir/f'{name}.svg')
        fig.savefig(figdir/f'{name}.pdf')
        fig.savefig(figdir/f'{name}.png',dpi=600)
        for tool,extra in [('audit_pdf_text.py',['--min-pt','5','--json']),
                ('audit_figure_collisions.py',['--json-out',str(figdir/f'{name}.collision.json')])]:
            command=[sys.executable,str(SKILL/'scripts'/tool),str(figdir/f'{name}.pdf'),*extra]
            if tool=='audit_figure_collisions.py':
                # Reuse project-local PDF dependencies after the established environment.
                code="import sys,runpy;sys.path.append(sys.argv.pop(1));sys.argv.pop(0);runpy.run_path(sys.argv[0],run_name='__main__')"
                command=[sys.executable,'-c',code,str(Path('.figure-deps').resolve()),*command[1:]]
            p=subprocess.run(command,
                capture_output=True,text=True,encoding='utf-8',
                env={**os.environ,'PYTHONIOENCODING':'utf-8'})
            (figdir/f'{name}.{tool}.log').write_text(p.stdout+p.stderr,encoding='utf-8')
            allqa.append(dict(figure=name,audit=tool,exit_code=p.returncode))
        plt.close(fig)
    for e in ('E0','E1'):
        selected=c[(c.B==1.2)&(c.evaluation==e)]
        fig,axes=plt.subplots(2,3,figsize=(7.2,4.4),sharex=True,sharey=True)
        fig.subplots_adjust(left=.09,right=.88,bottom=.13,top=.86,hspace=.37,wspace=.25)
        vmax=max(selected.s.max(),selected.r.max())
        for col,method in enumerate(('P','G','R')):
            data=selected[selected.method==method]
            for row,kind in enumerate(('s','r')):
                ax=axes[row,col]
                z=data.pivot(index='node',columns='slot',values=kind).to_numpy()
                mesh=ax.pcolormesh(np.arange(7)*5/3,np.arange(7)-.5,z,cmap='Blues',
                    norm=Normalize(vmin=0,vmax=vmax),shading='flat',rasterized=False)
                ax.axvline(5,color='#333333',lw=1,ls='--')
                ax.set_yticks(range(6));ax.set_xticks([0,5,10]);ax.set_xlim(0,10)
                ax.set_title(f'{method}: '+('Isolation s' if row==0 else 'Recovery r'),pad=9)
                if col==0:ax.set_ylabel('Asset node')
                if row==1:ax.set_xlabel('Model time')
        cbax=fig.add_axes([.91,.22,.014,.5]);fig.colorbar(mesh,cax=cbax)
        cbax.tick_params(labelsize=7);cbax.set_title('Input',fontsize=7,pad=9)
        fig.suptitle(f'Executed resource allocation | B=1.2 | {e}',x=.5,y=.97,fontsize=10)
        # Colorbar is not a comparable scientific panel.
        fig.canvas.draw()
        require_matplotlib_panel_alignment(fig,json_out=figdir/f'resources_{e}.alignment.json',
            exclude_axes=[cbax],tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
        # Exclude the colorbar for the common export helper's automatic inference.
        cbax.set_in_layout(False)
        save(fig,f'resources_{e}')
        fig,axes=plt.subplots(2,3,figsize=(7.2,4.6),sharex=True)
        fig.subplots_adjust(left=.09,right=.98,bottom=.13,top=.81,hspace=.6,wspace=.43)
        for node,ax in enumerate(axes.flat):
            for method in ('P','G','R'):
                d=tr[(tr.B==1.2)&(tr.evaluation==e)&(tr.method==method)&(tr.H==192)]
                ax.plot(d.t,d[f'x{node}'],color=COLORS[method],ls=LINES[method],
                    lw=1.3 if method=='G' else 1.1,label=method)
            ax.axvline(5,color='#888888',ls='--',lw=.7,zorder=0)
            ax.set_title(f'Node {node}'+(' (high value)' if node==3 else ''),pad=8)
            ax.set_xlim(0,10);ax.set_xticks([0,5,10]);ax.set_ylim(bottom=0)
            if node%3==0:ax.set_ylabel('Damaged proportion')
            if node>=3:ax.set_xlabel('Model time')
        handles,labels=axes.flat[0].get_legend_handles_labels()
        fig.legend(handles,labels,ncol=3,frameon=False,loc='upper center',bbox_to_anchor=(.5,.92))
        fig.suptitle(f'Asset states under the same actual attack | B=1.2 | {e}',y=.99,fontsize=10)
        save(fig,f'states_{e}')
    fig,ax=plt.subplots(figsize=(7.2,3.4))
    fig.subplots_adjust(left=.13,right=.98,bottom=.23,top=.72)
    p=paired[paired.period=='full'].sort_values(['B','evaluation']);x=np.arange(len(p))
    ax.bar(x-.16,p.delta_P_to_G,width=.3,color='#237A9D',label='P minus G')
    ax.bar(x+.16,p.delta_R_to_G,width=.3,color='#AF623A',label='R minus G')
    ax.axhline(0,color='#555555',lw=.8)
    ax.set_xticks(x,[f'B={r.B}\n{r.evaluation}' for _,r in p.iterrows()])
    ax.set_ylabel('Absolute defense loss difference')
    fig.suptitle('Paired loss differences: positive values favor G',y=.98,fontsize=10)
    ax.legend(frameon=False,ncol=2,loc='upper center',bbox_to_anchor=(.5,1.25))
    save(fig,'paired_comparisons')
    fig,axes=plt.subplots(1,2,figsize=(7.2,2.9),sharey=True)
    fig.subplots_adjust(left=.1,right=.98,bottom=.19,top=.77,wspace=.3)
    for ax,e in zip(axes,('E0','E1')):
        for method in ('P','G','R'):
            d=c[(c.B==1.2)&(c.evaluation==e)&(c.method==method)].groupby('slot').resource_use.first()
            ax.stairs(d,np.arange(7)*5/3,color=COLORS[method],ls=LINES[method],label=method,lw=1.3)
        ax.axhline(1.2,color='#888888',ls='-.',lw=.8)
        ax.axvline(5,color='#888888',ls='--',lw=.7)
        ax.set_xticks([0,5,10]);ax.set_xlim(0,10);ax.set_ylim(0,1.3)
        ax.set_xlabel('Model time');ax.set_title(e,pad=9)
    axes[0].set_ylabel('Total resource use')
    h,l=axes[0].get_legend_handles_labels();fig.legend(h,l,ncol=3,frameon=False,
        loc='upper center',bbox_to_anchor=(.5,.98))
    save(fig,'resource_use')
    write=(figdir/'automated_qa.json')
    write.write_text(json.dumps(allqa,indent=2),encoding='utf-8')
    print(json.dumps(allqa))


if __name__=='__main__':main()
