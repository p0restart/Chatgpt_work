"""Plot complete deterministic D8-2 comparisons with the project's Python backend."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from paper.work_d8_2.analysis.run_d8_2 import BASE,STATIC,load_controls,sha
QA=ROOT/'paper/work_d8_2/sources/figure_qa_tools'
sys.path.insert(0,str(QA))
from audit_panel_alignment import require_matplotlib_panel_alignment
OUT=BASE/'figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
    'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
    'legend.fontsize':7,'pdf.fonttype':42,'svg.fonttype':'none',
    'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'legend.frameon':False})
COLORS={'s':'#3676A8','r':'#BF783E','G':'#3676A8','R':'#797979','R-LAG':'#AA6E40'}
sources={}

def save(fig,name,paths):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=str(OUT/f'{name}.alignment.json'),
        overlay_svg=str(OUT/f'{name}.alignment.svg'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    fig.savefig(OUT/f'{name}.pdf',facecolor='white')
    fig.savefig(OUT/f'{name}.svg',facecolor='white')
    fig.savefig(OUT/f'{name}.png',dpi=600,facecolor='white')
    plt.close(fig)
    sources[name]=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths]

def steps(ax,values,**kw):
    edges=np.linspace(0,10,len(values)+1);ax.stairs(values,edges,baseline=None,**kw)

def main():
    p6=STATIC/'G_controls.json';p12=BASE/'K12_G_controls.json';u6=load_controls(p6);u12=load_controls(p12)
    fig,axes=plt.subplots(2,3,figsize=(7.2,4.7),sharex=True,sharey=True)
    fig.subplots_adjust(left=.09,right=.98,bottom=.12,top=.85,wspace=.17,hspace=.40)
    for i,ax in enumerate(axes.flat):
        for kind,idx in [('s',1),('r',2)]:
            steps(ax,u6[idx][:,i],color=COLORS[kind],linestyle='--',linewidth=1.15,label=f'{kind}, K6')
            steps(ax,u12[idx][:,i],color=COLORS[kind],linewidth=1.4,label=f'{kind}, K12')
        ax.set_title(f'v{i+1}',pad=9);ax.text(-.12,1.10,chr(97+i),transform=ax.transAxes,fontweight='bold',fontsize=9)
        assert max(float(u6[1][:,i].max()),float(u6[2][:,i].max()),float(u12[1][:,i].max()),float(u12[2][:,i].max()))<.4
        ax.set_ylim(-.005,.4);ax.set_xlim(0,10);ax.set_xticks([0,5,10]);ax.grid(axis='y',alpha=.18)
        if i>=3:ax.set_xlabel('Model time')
        if i%3==0:ax.set_ylabel('Defense intensity')
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=4,bbox_to_anchor=(.54,.99))
    save(fig,'fig1_G_defense_controls',[p6,p12])

    fig,ax=plt.subplots(figsize=(7.2,2.7));fig.subplots_adjust(left=.10,right=.98,bottom=.20,top=.78)
    for i,c in [(0,'#3676A8'),(1,'#BF783E')]:
        steps(ax,u6[0][:,i],color=c,linestyle='--',label=f'v{i+1}, K6')
        steps(ax,u12[0][:,i],color=c,label=f'v{i+1}, K12')
    ax.set(xlabel='Model time',ylabel='Attack intensity',xlim=(0,10),ylim=(0,.55));ax.legend(ncol=4,loc='lower center',bbox_to_anchor=(.5,1.04))
    save(fig,'fig2_G_attack_controls',[p6,p12])

    source=BASE/'results/K12/asset_rankings.csv';df=pd.read_csv(source);df=df[df.kind=='resource']
    fig,ax=plt.subplots(figsize=(7.2,2.9));fig.subplots_adjust(left=.10,right=.98,bottom=.18,top=.78)
    x=np.arange(6);width=.18
    for j,(method,k,c) in enumerate([('G',6,'#A9C7DF'),('G',12,'#3676A8'),('F',6,'#E4C7AB'),('F',12,'#BF783E')]):
        data=df[(df.method==method)&(df.K==k)].sort_values('node')
        ax.bar(x+(j-1.5)*width,data['mean'],width,color=c,label=f'{method}, K{k}')
    ax.set_xticks(x,[f'v{i+1}' for i in x]);ax.set_ylabel('Time-mean resource intensity');ax.set_ylim(0,.52)
    ax.legend(ncol=4,loc='lower center',bbox_to_anchor=(.5,1.04))
    save(fig,'fig3_asset_mean_resource',[source])

    source=BASE/'results/R_LAG/four_method_objectives.csv';df=pd.read_csv(source);df=df[df.period=='post']
    categories=['security','business','isolation','recovery','J_D'];x=np.arange(len(categories))
    fig,ax=plt.subplots(figsize=(7.2,3.1));fig.subplots_adjust(left=.13,right=.98,bottom=.20,top=.80)
    for j,event in enumerate(('E0','E1')):
        f=df[df.evaluation==event].set_index('method');values=(f.loc['R-LAG',categories]-f.loc['G',categories]).astype(float).to_numpy()*1000
        ax.bar(x+(j-.5)*.32,values,.32,color=['#3676A8','#BF783E'][j],label=event)
    ax.axhline(0,color='#555555',linewidth=.7);ax.set_xticks(x,['Security','Business','Isolation','Recovery','Total JD'])
    ax.set_ylabel('(R-LAG − G) loss × 1000');ax.legend(ncol=2,loc='lower center',bbox_to_anchor=(.5,1.03))
    save(fig,'fig4_R_LAG_loss_decomposition',[source])

    source=BASE/'results/R_LAG/all_method_prediction_errors.csv';df=pd.read_csv(source);df=df[df.executed_first_interval]
    fig,axes=plt.subplots(1,2,figsize=(7.2,2.9),sharey=True)
    fig.subplots_adjust(left=.10,right=.98,bottom=.20,top=.80,wspace=.20)
    for j,(ax,event) in enumerate(zip(axes,('E0','E1'))):
        for method in ('G','R','R-LAG'):
            f=df[(df.evaluation==event)&(df.method==method)].sort_values('update')
            ax.plot([5,20/3,25/3],f.L1,color=COLORS[method],marker={'G':'o','R':'s','R-LAG':'D'}[method],markersize=3,label=method)
        ax.set_title(event,pad=9);ax.text(-.14,1.10,chr(97+j),transform=ax.transAxes,fontweight='bold',fontsize=9)
        ax.set_xlabel('Update time');ax.set_xticks([5,20/3,25/3],['5','20/3','25/3'])
        ax.set_ylim(-.005,max(.4,float(df.L1.max()))*1.1)
    axes[0].set_ylabel('First-interval attack L1 error')
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,ncol=3,loc='upper center',bbox_to_anchor=(.55,.99))
    save(fig,'fig5_prediction_errors',[source])
    (OUT/'figure_sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
