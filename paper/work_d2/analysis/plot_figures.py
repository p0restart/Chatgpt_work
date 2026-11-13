"""Plot saved D2 tables; no simulation or optimization."""
from pathlib import Path
import sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle

OUT=Path(__file__).resolve().parents[1]; TAB=OUT/'tables'; FIG=OUT/'figures'
SK=Path('C:/Users/Jin/.codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure/scripts')
sys.path.insert(0,str(SK))
from audit_panel_alignment import require_matplotlib_panel_alignment
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':8,'axes.titlesize':8,'axes.labelsize':8,'legend.fontsize':7,'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7})
def save(fig,name):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=FIG/(name+'.alignment.json'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    fig.savefig(FIG/(name+'.pdf'))
    fig.savefig(FIG/(name+'.svg'))
    fig.savefig(FIG/(name+'.png'),dpi=300)
    plt.close(fig)

edges=pd.read_csv(TAB/'matched_edges.csv')
fig,axes=plt.subplots(1,2,figsize=(7.2,3.0));fig.subplots_adjust(left=.035,right=.98,bottom=.16,top=.84,wspace=.22)
pos={0:(0,.65),1:(0,-.65),2:(1.35,.65),3:(1.35,-.65),4:(2.7,.65),5:(2.7,-.65)}
for ax,cell,title in zip(axes,['A','C'],['a  Equal outgoing weights','b  Unequal outgoing weights']):
    e=edges.query('seed==11 and B==0.6 and cell==@cell')
    for r in e.itertuples():
        u=np.array(pos[r.source]);v=np.array(pos[r.target]);d=(v-u)/np.linalg.norm(v-u)
        ax.add_patch(FancyArrowPatch(u+d*.14,v-d*.14,arrowstyle='-|>',mutation_scale=10,color='#626b73',linewidth=.9))
        # Labels on separated quarter-segments avoid crossings at layer midpoints.
        f=.32 if r.source in [0,2] else .68
        xy=u*(1-f)+v*f
        off=.16 if u[1]==v[1] else (.27 if r.source in [0,2] else -.27)
        lab=('u' if r.source==0 else 'v') if r.source<2 else f'{r.beta:.2f}'
        ax.text(xy[0],xy[1]+off,lab,ha='center',va='center',fontsize=8)
    for i,(x,y) in pos.items():
        ax.add_patch(Circle((x,y),.14,facecolor='#e3ebf0' if i in [2,3] else 'white',edgecolor='#243746',lw=1))
        ax.text(x,y,str(i),ha='center',va='center')
    ax.set_xlim(-.25,2.95);ax.set_ylim(-1.05,1.05);ax.set_title(title,pad=13);ax.axis('off')
fig.text(.5,.05,'A / C: q2 = 4, q3 = 1     |     B / D: q2 = 1, q3 = 4     |     Other q = 1',ha='center',fontsize=8)
save(fig,'fig01_matched_network')

p=pd.read_csv(TAB/'matched_four_cells.csv')
fig,axs=plt.subplots(2,3,figsize=(7.2,4.4));fig.subplots_adjust(left=.09,right=.98,bottom=.12,top=.91,wspace=.42,hspace=.43)
colors=['#486a89','#929ca6','#c08447','#397c72'];markers=['o','x','s','^']
for j,B in enumerate([.6,1.2,1.8]):
    g=p[p.B==B];ax=axs[0,j]
    for c,col,mk in zip('ABCD',colors,markers): ax.plot(g.seed,g['J_'+c],marker=mk,lw=.9,color=col,label=c,markersize=4)
    ax.set_ylim(0,13);ax.set_xticks([11,22,33]);ax.set_title(f'{chr(97+j)}  B = {B:g}');ax.set_ylabel('Defense loss' if j==0 else '')
    ax=axs[1,j];ax.axhline(0,color='.6',lw=.7);ax.plot(g.seed,g.interaction,'o-',color='#243746',lw=1,ms=4);ax.set_ylim(0,.035);ax.set_xticks([11,22,33]);ax.set_xlabel('Network seed');ax.set_ylabel('Four-cell interaction' if j==0 else '');ax.set_title(chr(100+j),loc='left')
fig.legend(*axs[0,0].get_legend_handles_labels(),loc='upper center',ncol=4,bbox_to_anchor=(.5,1.0),frameon=False)
save(fig,'fig02_losses_interactions')

ctl=pd.read_csv(TAB/'matched_controls_all_nodes.csv');bud=pd.read_csv(TAB/'matched_budgets.csv');st=pd.read_csv(TAB/'matched_states_H12.csv')
def controls_figure(groups,name,states=False):
    rows=4 if states else 3
    fig,axs=plt.subplots(rows,len(groups),squeeze=False,figsize=(7.2,6.0 if rows==3 else 7.6))
    fig.subplots_adjust(left=.09,right=.98,bottom=.08,top=.92,wspace=.38,hspace=.48)
    for col,(seed,B) in enumerate(groups):
        for cell,color in [('C','#426e9b'),('D','#b27036')]:
            g=ctl[(ctl.seed==seed)&(ctl.B==B)&(ctl.cell==cell)]
            for node,ls in [(2,'-'),(3,'--')]:
                z=g[g.node==node].sort_values('slot');t=np.r_[z.t_start,10]
                for row,kind in enumerate(['s','r']):axs[row,col].step(t,np.r_[z[kind],z[kind].iloc[-1]],where='post',color=color,ls=ls,lw=1.1,label=f'{cell}, node {node}')
                if states:
                    z=st[(st.seed==seed)&(st.B==B)&(st.cell==cell)&(st.node==node)].sort_values('t')
                    axs[3,col].plot(z.t,z.x,color=color,ls=ls,lw=1)
            z=bud[(bud.seed==seed)&(bud.B==B)&(bud.cell==cell)].sort_values('slot');axs[2,col].step(np.r_[z.t_start,10],np.r_[z.defense_use/B,z.defense_use.iloc[-1]/B],where='post',color=color,lw=1.1,ls='-' if cell=='C' else '--')
        axs[0,col].set_title(f'Seed {seed}, B = {B:g}')
        for row in range(rows):
            ax=axs[row,col];ax.set_xlim(0,10);ax.set_xticks([0,5,10]);ax.set_ylim([(0,.022),(0,.34),(0,1.08),(0,.25)][row]);ax.text(-.2 if len(groups)>1 else -.06,1.03,chr(97+row*len(groups)+col),transform=ax.transAxes,fontweight='bold',fontsize=8)
            if col==0:ax.set_ylabel(['Isolation intensity','Recovery intensity','Capacity used / B','Damaged fraction'][row])
            if row==rows-1:ax.set_xlabel('Time')
            if row==2:ax.axhline(1,color='.4',lw=.6,ls=':')
    fig.legend(*axs[0,0].get_legend_handles_labels(),loc='upper center',ncol=4,frameon=False,bbox_to_anchor=(.52,.995))
    save(fig,name)
controls_figure([(11,.6),(11,1.2),(11,1.8)],'fig03_temporal_allocation')
controls_figure([(33,1.2)],'figS01_seed33_state_allocation',True)

# Supplement: comparable state trajectories and full node allocation retain all channels.
al=pd.read_csv(TAB/'allocations_all_nodes.csv').query("window=='all' and kind!='a'")
save_data={'fig01':'matched_edges.csv','fig02':'matched_four_cells.csv','fig03':'matched_controls_all_nodes.csv; matched_budgets.csv','figS01':'matched_controls_all_nodes.csv; matched_budgets.csv; matched_states_H12.csv'}
(FIG/'source_data_map.json').write_text(json.dumps(save_data,indent=2),encoding='utf-8')
print('Exported 4 figures in PDF/SVG/PNG; alignment checks passed.')
