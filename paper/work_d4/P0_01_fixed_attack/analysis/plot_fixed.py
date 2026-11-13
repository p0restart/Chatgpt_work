"""Plot all preregistered comparisons and the three fixed temporal examples."""
from pathlib import Path
import os
import sys
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'paper/work_d4/P0_01_fixed_attack'
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'analysis/mpl_config'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'paper/work_d4/P0_01_fixed_attack'
AUDITOR=Path('C:/Users/Jin/.codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure/scripts')
sys.path.insert(0,str(AUDITOR))
from audit_panel_alignment import require_matplotlib_panel_alignment

plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
    'font.size':7,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
    'legend.fontsize':7,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,
    'axes.spines.right':False,'axes.linewidth':.7,'lines.linewidth':1.2,'savefig.facecolor':'white'})
GAME='#315A7D';FIXED='#B76B35'
NODES=['#0072B2','#D55E00','#009E73','#CC79A7','#68737D','#56B4E9']

def save(fig,name):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=str(OUT/f'{name}.alignment.json'),
        overlay_svg=str(OUT/f'{name}.alignment.svg'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    fig.savefig(OUT/f'{name}.pdf')
    fig.savefig(OUT/f'{name}.svg')
    fig.savefig(OUT/f'{name}.png',dpi=300)
    plt.close(fig)

def compare():
    df=pd.read_csv(OUT/'four_cell_comparison.csv').sort_values(['seed','B'])
    if len(df)!=9 or df[['I_game','I_fixed','delta_I']].isna().any().any():
        raise RuntimeError('All nine groups must be present before the final comparison figure')
    fig,axes=plt.subplots(1,2,figsize=(7.2,4.0),sharey=True)
    fig.subplots_adjust(left=.15,right=.97,bottom=.16,top=.87,wspace=.38)
    y=np.arange(9)
    for yi,g,f in zip(y,df.I_game,df.I_fixed):
        axes[0].plot([g,f],[yi,yi],color='#A8ADB3',linewidth=1.1,zorder=1)
    axes[0].scatter(df.I_game,y,s=25,color=GAME,marker='o',label='GAME',zorder=3)
    axes[0].scatter(df.I_fixed,y,s=27,edgecolors=FIXED,facecolors='white',marker='s',linewidths=1.2,label='FIXED',zorder=4)
    axes[1].hlines(y,0,df.delta_I,color='#B7BEC5',linewidth=1.2)
    axes[1].scatter(df.delta_I,y,s=25,color='#5D6370',marker='D',zorder=3)
    labels=[f"{int(r.seed)} / {r.B:.1f}" for r in df.itertuples()]
    axes[0].set_yticks(y,labels);axes[0].set_ylabel('Seed / capacity B')
    axes[0].set_xlabel('Interaction I (defense-loss units)')
    axes[1].set_xlabel('Delta I = I_GAME - I_FIXED\n(defense-loss units)')
    for ax,letter in zip(axes,['a','b']):
        ax.axvline(0,color='#555B61',linewidth=.8,linestyle=':')
        ax.set_ylim(8.6,-.6)
        ax.grid(axis='x',color='#E8EBEE',linewidth=.5)
        ax.set_axisbelow(True)
        ax.text(-.15,1.04,letter,transform=ax.transAxes,fontsize=9,fontweight='bold')
        ax.ticklabel_format(axis='x',style='sci',scilimits=(-3,3),useMathText=False)
    vals=np.r_[0,df.I_game,df.I_fixed]
    pad=max(np.ptp(vals)*.09,1e-6)
    axes[0].set_xlim(min(0,float(vals.min()))-pad,max(0,float(vals.max()))+pad)
    vals=np.r_[0,df.delta_I];pad=max(np.ptp(vals)*.15,1e-6)
    axes[1].set_xlim(min(0,float(vals.min()))-pad,max(0,float(vals.max()))+pad)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.49,.99),ncol=2,frameon=False)
    save(fig,'figure_interaction_comparison')

def temporal():
    df=pd.read_csv(OUT/'all_controls.csv')
    time=np.arange(7)*10/6
    for B in (.6,1.2,1.8):
        fig,axes=plt.subplots(2,3,figsize=(7.2,4.7))
        fig.subplots_adjust(left=.08,right=.98,bottom=.12,top=.80,wspace=.35,hspace=.48)
        for ri,cell in enumerate(('C','D')):
            part=df[(df.seed==11)&(df.B==B)&(df.cell==cell)]
            for ci,kind in enumerate(('s','r')):
                ax=axes[ri,ci]
                for evaluation,style in [('GAME','-'),('FIXED','--')]:
                    for node,color in enumerate(NODES):
                        vals=part[(part.evaluation==evaluation)&(part.node==node)].sort_values('slot')[kind].to_numpy()
                        if len(vals)!=6:raise RuntimeError('Missing temporal controls')
                        ax.step(time,np.r_[vals,vals[-1]],where='post',color=color,linestyle=style,linewidth=1.)
                ax.set_ylabel(f'Cell {cell}: '+('isolation s' if kind=='s' else 'recovery r'))
                ax.set_ylim(bottom=-.01)
            ax=axes[ri,2]
            for e,color,style in [('GAME',GAME,'-'),('FIXED',FIXED,'--')]:
                use=part[part.evaluation==e].groupby('slot')[['s','r']].sum().sum(axis=1).to_numpy()/B
                ax.step(time,np.r_[use,use[-1]],where='post',color=color,linestyle=style,linewidth=1.4)
            ax.axhline(1,color='#777D84',linestyle=':',linewidth=.8)
            ax.set_ylim(-.03,1.08);ax.set_ylabel(f'Cell {cell}: capacity use / B')
        for i,ax in enumerate(axes.ravel()):
            ax.set_xlim(0,10);ax.set_xticks([0,5,10]);ax.set_xlabel('Model time')
            ax.text(-.23,1.06,chr(97+i),transform=ax.transAxes,fontweight='bold',fontsize=9)
        for ci in (0,1):
            ymax=max(axes[ri,ci].get_ylim()[1] for ri in (0,1))
            for ri in (0,1):axes[ri,ci].set_ylim(-.01,ymax)
        handles=[Line2D([0],[0],color=c,lw=1.5,label=f'Node {i}') for i,c in enumerate(NODES)]
        handles.extend([Line2D([0],[0],color='#333333',ls='-',label='GAME'),Line2D([0],[0],color='#333333',ls='--',label='FIXED')])
        fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.52,.98),ncol=4,frameon=False)
        fig.text(.50,.855,f'Seed 11, B = {B:.1f}',ha='center',fontsize=8)
        save(fig,f'figure_temporal_seed11_B{B}')

if __name__=='__main__':
    compare();temporal()
