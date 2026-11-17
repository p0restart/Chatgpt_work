"""Add data-derived control directions without rerunning optimization."""
from pathlib import Path
import argparse
import pandas as pd

MARKER='<!--CONTROL_INTERPRETATION-->'
def describe(out):
    a=pd.read_csv(out/'attacker_best_responses.csv')
    d=pd.read_csv(out/'defender_best_responses.csv')
    lines=[MARKER,'','控制调整方向（由完整CSV计算）：','',
        '正向扰动下，攻击者在第1—3区间增加API网关攻击、减少Web攻击，第4—6区间方向反转；反向扰动的方向与之相反。变化已经出现在第1区间，因为这里求解的是预先知道完整防御计划的开环响应，不能解释为攻击者在线观测后才调整。','']
    means=[]
    for label,title in [('positive','正向'),('negative','反向')]:
        aa=a[(a.scenario==label)&(a.asset==1)&(a.slot==1)].iloc[0]
        dd=d[d.scenario==label]
        avg=dd.groupby('asset')[['delta_isolation','delta_recovery']].mean()
        ss=dd.loc[dd.delta_isolation.abs().idxmax()]
        rr=dd.loc[dd.delta_recovery.abs().idxmax()]
        lines.append(f'{title}：第1区间API攻击相对基准BR变化{aa.delta_from_baseline_BR:+.9f}。固定此攻击响应后，防御者相对原u_G的API平均隔离/恢复变化为{avg.loc[1,"delta_isolation"]:+.9f}/{avg.loc[1,"delta_recovery"]:+.9f}，Web为{avg.loc[2,"delta_isolation"]:+.9f}/{avg.loc[2,"delta_recovery"]:+.9f}。最大隔离变化在第{int(ss.slot)}区间{ss["name"]}，为{ss.delta_isolation:+.9f}；最大恢复变化在第{int(rr.slot)}区间{rr["name"]}，为{rr.delta_recovery:+.9f}。')
        lines.append('')
        for i,row in avg.iterrows():means.append(dict(scenario=label,asset=i,mean_delta_isolation=row.delta_isolation,mean_delta_recovery=row.delta_recovery))
    lines.extend(['这些方向和误差比较支持：在本次固定实例中，防御计划影响攻击数值响应，而改变后的攻击又影响防御隔离/恢复配置。双方目标改善幅度较小，不能据此主张有较大实际收益或普遍博弈优势。均值按六个等长区间计算，全部逐槽差异保留在CSV。',''])
    p=out/'results_and_limitations.md'
    existing=p.read_text(encoding='utf-8').split(MARKER)[0].rstrip()
    p.write_text(existing+'\n\n'+'\n'.join(lines),encoding='utf-8')
    pd.DataFrame(means).to_csv(out/'defense_mean_changes_by_asset.csv',index=False,encoding='utf-8-sig',float_format='%.17g')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='run01');args=ap.parse_args()
    p=Path(args.out);describe(p if p.is_absolute() else Path(__file__).resolve().parent/p)
