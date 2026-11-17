from pathlib import Path
import sys, json, shutil, os
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parents[1]/'qa/mpl_cache')
sys.path.append(r'C:\Users\Jin\AppData\Local\Temp\codex_audit_20261117_deps')
import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,r'C:\Users\Jin\.codex\plugins\cache\nature-skills\nature-skills\0.1.0\skills\nature-figure\scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment

BASE=Path(__file__).resolve().parents[1]; OUT=BASE/'figures'
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Microsoft YaHei','DejaVu Sans'],
 'font.size':8.5,'axes.titlesize':9,'axes.labelsize':8.5,'xtick.labelsize':8,'ytick.labelsize':8,
 'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
 'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,
 'axes.linewidth':.7,'savefig.facecolor':'white'})

def save(fig,name):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=BASE/'qa'/f'{name}_alignment.json',strict=True)
    for suffix in ('png','pdf','svg'):
        fig.savefig(OUT/f'{name}.{suffix}',dpi=450)
    plt.close(fig)

df=pd.read_csv(BASE/'data/capacity_by_slot.csv')
df['B']=df.B.round(1)
fig,axs=plt.subplots(1,3,figsize=(17/2.54,6.5/2.54),sharey=True)
fig.subplots_adjust(left=.083,right=.99,bottom=.23,top=.79,wspace=.20)
for j,(ax,B) in enumerate(zip(axs,[.6,1.2,1.8])):
    d=df[(df.B==B)&(df.plan=='G')].sort_values('slot')
    ax.bar(d.slot,d.isolation,color='#356B8C',width=.68,label='源端隔离',linewidth=0)
    ax.bar(d.slot,d.recovery,bottom=d.isolation,color='#D9AB62',width=.68,label='本地恢复',linewidth=0)
    ax.axhline(B,color='#343434',ls=(0,(4,3)),lw=1,label='容量上限')
    ax.set_title(f'({chr(97+j)})  B = {B:.1f}',pad=7)
    ax.set_xticks(range(1,7));ax.set_ylim(0,2);ax.set_yticks([0,.6,1.2,1.8])
    ax.set_xlabel('控制区间 k');ax.grid(axis='y',color='#E6E6E6',lw=.45);ax.set_axisbelow(True)
axs[0].set_ylabel('资源占用（归一化）')
handles,labels=axs[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.53,1.01),ncol=3,frameon=False)
save(fig,'capacity_three_budgets')

df=pd.read_csv(BASE/'data/complete_controls.csv');df['B']=df.B.round(1);g=df[df.plan=='G']
assert len(g)==108
fig,axs=plt.subplots(2,3,figsize=(17/2.54,10.8/2.54),sharex=True,sharey=True)
fig.subplots_adjust(left=.10,right=.89,bottom=.13,top=.91,wspace=.19,hspace=.33)
for row,key in enumerate(['s','r']):
    for col,B in enumerate([.6,1.2,1.8]):
        ax=axs[row,col]
        matrix=g[g.B==B].pivot(index='asset',columns='slot',values=key).sort_index().to_numpy()
        assert matrix.shape==(6,6) and np.nanmax(matrix)<.5
        im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=.5,aspect='auto',interpolation='nearest')
        ax.set_title(f'({chr(97+row*3+col)})  B = {B:.1f} · '+('隔离' if row==0 else '恢复'),pad=7)
        ax.set_xticks(range(6),[str(k) for k in range(1,7)])
        ax.set_yticks(range(6),[f'v{i}' for i in range(1,7)])
        ax.set_xticks(np.arange(-.5,6,.5)[::2],minor=True)
        ax.set_yticks(np.arange(-.5,6,.5)[::2],minor=True)
        ax.grid(which='minor',color='white',linewidth=.6);ax.tick_params(which='minor',length=0)
        if row==1:ax.set_xlabel('控制区间 k')
        if col==0:ax.set_ylabel('资产')
cax=fig.add_axes([.925,.23,.022,.56]);cax.set_label('colorbar')
cbar=fig.colorbar(im,cax=cax);cax.set_title('强度',fontsize=8,pad=8);cbar.set_ticks([0,.1,.2,.3,.4,.5])
save(fig,'actions_three_budgets')
shutil.copyfile(BASE/'input/rId31.png',OUT/'topology.png')
print('Figures generated from 108 G control rows and 18 G capacity rows.')
