"""D7 manuscript figures, generated only from D7 frozen inputs and results."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch,FancyBboxPatch
BASE=Path(__file__).resolve().parents[1]
QA=BASE/'analysis/figure_qa'
sys.path.insert(0,str(QA))
from audit_panel_alignment import require_matplotlib_panel_alignment
OUT=BASE/'figures';OUT.mkdir(exist_ok=True);(OUT/'qa').mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
COL={'P':'#707070','G':'#0072B2','R':'#D55E00'};ST={'P':':','G':'-','R':'--'}
sources={}
def save(fig,name,paths,axes=None):
    if axes is not None:
        require_matplotlib_panel_alignment(fig,json_out=OUT/'qa'/f'{name}_alignment.json',overlay_svg=OUT/'qa'/f'{name}_alignment.svg',axes=list(np.array(axes).ravel()),strict=True)
    for ext in ['png','pdf','svg']:fig.savefig(OUT/f'{name}.{ext}',dpi=300,facecolor='white')
    sources[name]=[{'path':str(p.relative_to(BASE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    plt.close(fig)

# Single-canvas topology. Positions are diagram geometry, not measured locations.
f,a=plt.subplots(figsize=(7.1,3.6));f.subplots_adjust(left=.02,right=.98,bottom=.03,top=.97)
a.set(xlim=(-.9,5.4),ylim=(-1.25,2.25));a.axis('off')
pos={0:(0,1.5),1:(0,-.65),2:(2.2,-.65),3:(2.2,1.5),4:(4.55,-.65),5:(4.55,1.5)}
names=['v1  API gateway','v2  Web app','v3  Order service','v4  Authentication','v5  Core database','v6  Administration']
edges=pd.read_csv(BASE/'topology_edges.csv')
labelpos={(0,2):(.85,.2),(0,3):(1.1,1.65),(1,2):(1.1,-.49),(3,2):(2.43,.4),(3,4):(3.24,.2),(3,5):(3.38,1.65),(2,4):(3.4,-.49),(5,4):(4.8,.4)}
for row in edges.itertuples():
    j,i=int(row.source),int(row.target)
    start,end=np.array(pos[j]),np.array(pos[i]);vec=end-start
    boundary=min(.73/abs(vec[0]) if vec[0] else np.inf,.32/abs(vec[1]) if vec[1] else np.inf)
    a.add_patch(FancyArrowPatch(start+boundary*vec,end-boundary*vec,arrowstyle='-|>',mutation_scale=10,lw=1.15,color='#465563',shrinkA=0,shrinkB=0))
    x,y=labelpos[j,i];a.text(x,y,f'{row.beta:.2f}',ha='center',va='center',bbox=dict(facecolor='white',edgecolor='none',pad=.8))
for i,(x,y) in pos.items():
    a.add_patch(FancyBboxPatch((x-.68,y-.27),1.36,.54,boxstyle='round,pad=.015',facecolor='#E8F2F9' if i<2 else '#FFF0CE' if i==4 else '#EDF3EE',edgecolor='#586574',lw=1,zorder=4))
    a.text(x,y,names[i]+('\nq = 4' if i==4 else '\nq = 1'),ha='center',va='center',fontsize=8,zorder=5)
a.text(0,2.05,'Direct attack at v1 and v2 only',ha='left',fontsize=8)
a.text(2.3,-1.13,'s: limits outgoing propagation   |   r: increases local recovery',ha='center',fontsize=8)
save(f,'fig1_topology',[BASE/'topology_edges.csv',BASE/'topology_assets.csv'])

# Procedure schematic; external executed attacks never replaced by predicted attacks.
f,a=plt.subplots(figsize=(7.1,3.5));f.subplots_adjust(left=.015,right=.985,bottom=.02,top=.98);a.axis('off');a.set(xlim=(0,10),ylim=(0,5))
def box(x,y,w,h,text,fc='#EDF3F8'):
    a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.03',fc=fc,ec='#586574',lw=.8));a.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=8)
def arrow(p,q):a.add_patch(FancyArrowPatch(p,q,arrowstyle='-|>',mutation_scale=11,color='#465563',lw=1))
box(.2,3.35,2.3,1.05,'Current observed state\nKnown model parameters\nRemaining horizon')
box(3.25,3.35,3.2,1.05,'G: alternating local responses\nR: fixed-forecast optimization\nP: inherit original plan')
box(7.25,3.35,2.5,1.05,'Planned defense sequence\nKeep first interval only')
box(3.25,.75,3.2,1.05,'Actual state integration\nRecord actions, costs, resources')
box(7.25,.75,2.5,1.05,'Common executed attack\nE0: preset / E1: frozen',fc='#FFF1D9')
arrow((2.55,3.88),(3.18,3.88));arrow((6.5,3.88),(7.18,3.88))
arrow((8.5,3.3),(8.5,2.5));arrow((8.5,2.5),(4.85,2.5));arrow((4.85,2.5),(4.85,1.87))
arrow((7.18,1.27),(6.52,1.27));arrow((3.18,1.27),(1.35,1.27));arrow((1.35,1.27),(1.35,3.28))
a.text(4.85,2.76,'Executed defense',ha='center');a.text(1.5,2.2,'Next update',rotation=90,ha='center')
a.text(4.8,4.78,'Predicted attack belongs to planning; executed attack is held common',ha='center',fontsize=8)
save(f,'fig2_execution_flow',[BASE/'analysis/model_method.md',BASE/'analysis/run_rolling.py'])

p=BASE/'results/static/B1.2/G_decisions.csv';d=pd.read_csv(p)
f,axs=plt.subplots(1,2,figsize=(7.1,3.35));f.subplots_adjust(left=.13,right=.88,bottom=.19,top=.87,wspace=.32)
for ax,c,title in zip(axs,['s','r'],['(a) Source isolation s','(b) Local recovery r']):
    z=d.pivot(index='node',columns='slot',values=c).to_numpy();im=ax.imshow(z,vmin=0,vmax=1,cmap='Blues',aspect='auto',interpolation='nearest')
    ax.set(xticks=range(6),xticklabels=['0','1.67','3.33','5','6.67','8.33'],yticks=range(6),yticklabels=['v1 API','v2 Web','v3 Order','v4 Auth','v5 DB','v6 Admin'],xlabel='Interval start (model time)',title=title)
    for i in range(6):
        for k in range(6):ax.text(k,i,f'{z[i,k]:.2f}',ha='center',va='center',fontsize=7,color='white' if z[i,k]>.55 else '#152D40')
cax=f.add_axes([.91,.19,.018,.68]);f.colorbar(im,cax=cax,label='Normalized intensity')
save(f,'fig3_defense_actions',[p],axs)

paths=[BASE/f'results/static/B{b}/cross_evaluation.csv' for b in [.6,1.2,1.8]]
f,axs=plt.subplots(1,2,figsize=(7.1,3.1));f.subplots_adjust(left=.13,right=.97,bottom=.22,top=.85,wspace=.42)
for n,(ax,title) in enumerate(zip(axs,['(a) Common fixed attack a0','(b) Each policy\'s attack response'])):
    vals=[]
    for p in paths:
        df=pd.read_csv(p);g=df[(df.method=='G')&(df.attack==('a0' if n==0 else 'aG'))].iloc[0];v=df[(df.method=='F')&(df.attack==('a0' if n==0 else 'aBR_F'))].iloc[0];vals.append(v.J_D-g.J_D)
    ax.axhline(0,color='#777777',lw=.8);ax.plot([.6,1.2,1.8],np.array(vals)*1000,'o-',color=COL['G'],ms=5,lw=1)
    ax.set(title=title,xlabel='Defense capacity B',ylabel='1000 x loss difference (F - G)',xticks=[.6,1.2,1.8],ylim=(-.8,1.8))
    ax.grid(axis='y',alpha=.2)
save(f,'fig4_cross_evaluation',paths,axs)

folder=BASE/'results/rolling_event_B1.2';tp=folder/'trajectories.csv';cp=folder/'executed_controls.csv';tr=pd.read_csv(tp);co=pd.read_csv(cp)
f,axs=plt.subplots(2,2,figsize=(7.1,4.8));f.subplots_adjust(left=.13,right=.97,bottom=.12,top=.85,wspace=.4,hspace=.46)
diffs=[]
for j,E in enumerate(['E0','E1']):
    base=tr[(tr.evaluation==E)&(tr.method=='P')&(tr.H==48)]
    for method in ['P','G','R']:
        dd=tr[(tr.evaluation==E)&(tr.method==method)&(tr.H==48)]
        diff=1000*(dd.x4.to_numpy()-base.x4.to_numpy());diffs.extend(diff)
        axs[0,j].plot(dd.t,diff,color=COL[method],ls=ST[method],lw=1.3,label=method)
        dd=co[(co.evaluation==E)&(co.method==method)&(co.node==3)].sort_values('slot')
        axs[1,j].step(np.r_[dd.t_start,10],np.r_[dd.r,dd.r.iloc[-1]],where='post',color=COL[method],ls=ST[method],lw=1.3,label=method)
    for ax in axs[:,j]:
        ax.axvline(5,color='#333333',lw=.8,ls=':');ax.set(xlim=(0,10),xticks=[0,5,6.667,8.333,10],xticklabels=['0','5','6.67','8.33','10'],xlabel='Model time');ax.grid(alpha=.18)
    axs[0,j].set(title=f'({"ab"[j]}) {E}: database state difference',ylabel='1000 x [x5(method) - x5(P)]')
    axs[1,j].set(title=f'({"cd"[j]}) {E}: authentication recovery',ylabel='Executed r4',ylim=(0,.14))
pad=.08*(max(diffs)-min(diffs))
for ax in axs[0]:ax.set_ylim(min(diffs)-pad,max(diffs)+pad)
f.legend(*axs[0,0].get_legend_handles_labels(),loc='upper center',ncol=3,frameon=False,bbox_to_anchor=(.55,.98))
save(f,'fig5_rolling_execution',[tp,cp],axs)

# Supplement: actual, unshifted state values and resource use for the main offline case.
sp=BASE/'results/static/B1.2/G_states.csv';dp=BASE/'results/static/B1.2/G_decisions.csv';states=pd.read_csv(sp);dd=pd.read_csv(dp)
f,axs=plt.subplots(1,2,figsize=(7.1,3.2));f.subplots_adjust(left=.11,right=.97,bottom=.2,top=.85,wspace=.4)
for node,c in zip([0,3,4],['#0072B2','#D55E00','#009E73']):axs[0].plot(states.t,states[f'x{node}'],label=f'v{node+1}',color=c,lw=1.2)
axs[0].set(title='(a) Actual damaged fractions',xlabel='Model time',ylabel='Damaged fraction',xlim=(0,10),ylim=(0,.4));axs[0].legend(frameon=False)
res=dd.groupby('slot').first();axs[1].step(np.r_[res.t_start,10],np.r_[res.total_resource,res.total_resource.iloc[-1]],where='post',label='Used capacity',color=COL['G']);axs[1].axhline(1.2,color='#777777',ls='--',label='B = 1.2')
axs[1].set(title='(b) Total defense resource',xlabel='Model time',ylabel='Normalized resource',xlim=(0,10),ylim=(0,1.4));axs[1].legend(frameon=False)
save(f,'figS1_states_resources',[sp,dp],axs)
(OUT/'figure_sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated five figures with data provenance and panel alignment checks.')
