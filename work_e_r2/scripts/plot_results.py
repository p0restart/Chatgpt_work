"""Three single-panel scientific figures from the saved R2 data only."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import pandas as pd
SKILL=Path('C:/Users/Jin/.codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure')
sys.path.insert(0,str(SKILL/'scripts'))
from audit_panel_alignment import require_matplotlib_panel_alignment
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':8,'axes.labelsize':9,'axes.titlesize':10,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.8,'pdf.fonttype':42,'svg.fonttype':'none'})
FIG=OUT/'figures';FIG.mkdir(exist_ok=True)
BLUE='#246a9b';ORANGE='#bd6d24';DARK='#333e48'
def save(fig,name):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=str(FIG/f'{name}.alignment.json'),tolerance_pt=1.5,strict=True)
    fig.savefig(FIG/f'{name}.pdf')
    fig.savefig(FIG/f'{name}.svg')
    fig.savefig(FIG/f'{name}.png',dpi=600)
    plt.close(fig)
def main():
    d=pd.read_csv(OUT/'results/defender_bounds.csv');v=pd.read_csv(OUT/'results/objective_bounds.csv');v=v[v.object=='B'].set_index('player')
    base=read(OUT/'results/candidate_payoff_enclosure.json');threshold=float(F(base['B_D'][1])-F(1,100)*(1+F(base['B_D'][0])))
    fig,ax=plt.subplots(figsize=(7.2,4.4),layout='constrained')
    ax.fill_between(d.regions_created,d.lower_bound_B,d.upper_bound_B,color='#e6edf2',label='Unresolved optimal-value range')
    ax.plot(d.regions_created,d.lower_bound_B,color=BLUE,lw=1.7,label='Certified lower bound')
    ax.plot(d.regions_created,d.upper_bound_B,color=DARK,lw=1.5,label='Feasible-response upper bound')
    ax.axhline(threshold,color=ORANGE,ls='--',lw=1.2,label='Lower bound needed for 1% gap')
    ax.set(xlabel='Regions generated',ylabel='Defender best-response cost (B)',title='Defender global bounds remain separated at the pilot limit',xlim=(0,2050),ylim=(5.2,11.2))
    ax.legend(frameon=False,loc='upper left',bbox_to_anchor=(.02,.98),fontsize=7.5)
    save(fig,'fig1_defender_global_bounds')
    a=v.loc['A'];cert=read(OUT/'results/attacker_certificate.json')
    yl=[a.candidate_lower,a.best_known_response_lower];yh=[a.candidate_upper,a.best_known_response_upper];ym=[(l+h)/2 for l,h in zip(yl,yh)]
    fig,ax=plt.subplots(figsize=(7.2,4.4),layout='constrained')
    ax.errorbar([0,1],ym,yerr=[[m-l for m,l in zip(ym,yl)],[h-m for m,h in zip(ym,yh)]],fmt='o',color=BLUE,capsize=5,ms=6,lw=1.3,label='Certified payoff enclosure')
    ax.scatter([2],[a.global_BR_upper],marker='v',s=65,facecolors='none',edgecolors=ORANGE,linewidths=1.5,label='Global optimal-payoff upper bound')
    ax.set_xticks([0,1,2],['Fixed candidate','Best known response','Certified BR upper bound'])
    ax.set(xlim=(-.45,2.5),ylabel='Attacker payoff (B)',title='Attacker response and certified optimal-payoff envelope')
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.6f'))
    ax.set_ylim(min(yl)-5e-6,a.global_BR_upper+1.1e-5)
    ax.legend(frameon=False,loc='upper left',fontsize=7.5)
    save(fig,'fig2_attacker_response_certificate')
    ys=[v.loc[p].normalized_upper_percent for p in ('D','A')]
    assert all(y > 0 for y in ys)
    fig,ax=plt.subplots(figsize=(7.2,4.4),layout='constrained')
    ax.scatter([0,1],ys,c=[ORANGE,BLUE],s=55,zorder=3)
    ax.axhline(1,color=DARK,ls='--',lw=1.2,label='Pilot target (1%)')
    ax.axhline(.1,color='#8d969e',ls=':',lw=1.3,label='Secondary target (0.1%)')
    for x,y in enumerate(ys):ax.annotate(f'{y:.6g}%',(x,y),xytext=(0,10),textcoords='offset points',ha='center',fontsize=8)
    ax.set_xticks([0,1],['Defender','Attacker']);ax.set_yscale('log')
    ax.set(xlim=(-.5,1.5),ylim=(1e-4,100),ylabel='Certified normalized unilateral-gain upper bound (%)',title='Only the attacker meets the prescribed gap target')
    ax.legend(frameon=False,loc='upper right',fontsize=7.5)
    save(fig,'fig3_nash_gap_targets')
    dump(FIG/'figure_sources.json',dict(fig1='results/defender_bounds.csv: all saved rows',fig2='results/objective_bounds.csv: B, A',fig3='results/objective_bounds.csv: B, D/A',uncertainty='deterministic rigorous payoff enclosures, not statistical confidence intervals',backend='python',single_panel_count=3))
if __name__=='__main__':main()
