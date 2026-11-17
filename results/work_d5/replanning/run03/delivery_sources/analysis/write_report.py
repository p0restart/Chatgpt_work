"""Prepare D5 result tables and review package from verified saved outputs."""
import argparse
from pathlib import Path
import json
import hashlib
import shutil
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]


def table(frame):
    def fmt(x):
        if isinstance(x,(float,np.floating)):return f'{x:.9f}' if abs(x)<.01 else f'{x:.6f}'
        return str(x)
    return '\n'.join(['|'+'|'.join(map(str,frame.columns))+'|','|'+'|'.join(['---']*len(frame.columns))+'|']+
        ['|'+'|'.join(fmt(x) for x in row)+'|' for row in frame.itertuples(index=False,name=None)])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('run');args=ap.parse_args();out=Path(args.run)
    meta=json.loads((out/'metadata.json').read_text());valid=json.loads((out/'independent_validation.json').read_text())
    assert valid['passed'] and meta['status']=='COMPLETED_NUMERICAL_PASS'
    obj=pd.read_csv(out/'objectives.csv');obj=obj[obj.H==48]
    paired=pd.read_csv(out/'comparisons.csv');full=paired[paired.period=='full'].sort_values(['B','evaluation'])
    post=paired[paired.period=='post'].sort_values(['B','evaluation'])
    c=pd.read_csv(out/'executed_controls.csv');p=pd.read_csv(out/'planned_controls.csv')
    audit=pd.read_csv(out/'solver_audit.csv');quality=pd.read_csv(out/'quality.csv')
    timing=pd.read_csv(out/'timing.csv');attempts=pd.read_csv(out/'optimizer_attempts.csv')
    if 'phase' in timing:
        timing=timing[timing.phase!='independent_validation']
    timing=pd.concat([timing,pd.read_csv(out/'verification_timing.csv')],ignore_index=True)
    timing.to_csv(out/'timing.csv',index=False)
    nodes=pd.read_csv(out/'node_state_summary.csv')
    adjustments=[];forecasts=[]
    for (B,e),cg in c.groupby(['B','evaluation']):
        base=cg[cg.method=='P'].set_index(['slot','node'])
        for _,r in cg[(cg.method.isin(['G','R']))&(cg.slot>=3)].iterrows():
            ref=base.loc[(r.slot,r.node)]
            adjustments.append(dict(B=B,evaluation=e,method=r.method,slot=r.slot,node=r.node,
                s=r.s,r=r.r,s_P=ref.s,r_P=ref.r,delta_s=r.s-ref.s,delta_r=r.r-ref.r))
    pd.DataFrame(adjustments).to_csv(out/'resource_adjustments.csv',index=False)
    for (B,e,method,j),pg in p[(p.method.isin(['G','R']))&p.selected].groupby(['B','evaluation','method','update']):
        first=pg[pg.absolute_slot==3+j].sort_values('node')
        actual=c[(c.B==B)&(c.evaluation==e)&(c.method==method)&(c.slot==3+j)].sort_values('node')
        forecasts.append(dict(B=B,evaluation=e,method=method,update=j,
            a0_planned=first.a_plan.iloc[0],a1_planned=first.a_plan.iloc[1],
            a0_actual=actual.a_actual.iloc[0],a1_actual=actual.a_actual.iloc[1],
            first_slot_L1_error=float(np.sum(abs(first.a_plan.to_numpy()-actual.a_actual.to_numpy())))))
    f=pd.DataFrame(forecasts);f.to_csv(out/'attack_prediction_comparison.csv',index=False)
    online=timing[timing.item=='replanning_total']
    tstats=online.groupby('method').seconds.agg(['count','min','median','max','sum']).reset_index()
    tstats.to_csv(out/'timing_summary.csv',index=False)
    diagstats=pd.DataFrame([
        dict(metric='控制箱/容量最大违反',maximum=float(quality.loc[quality.check=='control_violation','value'].max()),threshold=1e-10),
        dict(metric='状态越界',maximum=float(quality.loc[quality.check=='state_domain','value'].max()),threshold=1e-10),
        dict(metric='状态拼接连续误差',maximum=float(quality.loc[quality.check=='continuity','value'].max()),threshold=1e-12),
        dict(metric='最终候选归一化已发现改善',maximum=float(audit.relative_improvement.max()),threshold=1e-7),
        dict(metric='最终候选当前投影残差',maximum=float(audit.incumbent_residual.max()),threshold=1e-4),
        dict(metric='最终候选响应控制距离',maximum=float(audit.response_distance.max()),threshold=1e-3),
        dict(metric='三起点/路径最大控制差',maximum=float(quality.loc[quality.check.str.contains('spread'),'value'].max()),threshold=1e-3),
        dict(metric='H48/96/192固定执行策略复核',maximum=float(quality.loc[quality.check=='reintegration','value'].max()),threshold=1e-6)])
    diagstats.to_csv(out/'quality_summary.csv',index=False)
    fullcols=['B','evaluation','J_D_P','J_D_G','J_D_R','delta_P_to_G','delta_R_to_G']
    decomp=obj[obj.period.isin(['post','full'])][['B','evaluation','method','period','security','business','isolation','recovery','J_D','J_A']].sort_values(['B','evaluation','period','method'])
    high=nodes[(nodes.node==3)&(nodes.period=='post')][['B','evaluation','method','state_area','weighted_security','end_state']].sort_values(['B','evaluation','method'])
    high.to_csv(out/'high_value_asset.csv',index=False)
    # Six-node first post-event actions; all controls remain in the complete execution table.
    event=c[(c.B==1.2)&(c.slot==3)][['evaluation','method','node','s','r','resource_use']]
    event.to_csv(out/'event_actions_B1.2.csv',index=False)
    signs=[]
    for e,g in full.groupby('evaluation'):
        signs.append(f"{e}下G相对R的绝对差范围为{g.delta_R_to_G.min():.9f}至{g.delta_R_to_G.max():.9f}。")
    resource=pd.DataFrame(adjustments)
    resource=resource[(resource.B==1.2)&(resource.method=='G')&(resource.slot==3)][
        ['evaluation','node','s_P','s','delta_s','r_P','r','delta_r']]
    predicted=f[(f.B==1.2)&(f['update']==0)]
    # Security vs objective reductions are deliberately evaluated separately.
    securityrows=[]
    for (B,e),g in obj[obj.period=='post'].groupby(['B','evaluation']):
        v=g.set_index('method')
        securityrows.append(dict(B=B,evaluation=e,security_P_minus_G=v.loc['P','security']-v.loc['G','security'],
            security_R_minus_G=v.loc['R','security']-v.loc['G','security'],
            business_P_minus_G=v.loc['P','business']-v.loc['G','business'],
            control_P_minus_G=(v.loc['P','isolation']+v.loc['P','recovery'])-(v.loc['G','isolation']+v.loc['G','recovery'])))
    security=pd.DataFrame(securityrows);security.to_csv(out/'loss_component_comparisons.csv',index=False)
    histories=[]
    for run in ('run01','run02'):
        q=out.parent/run/'metadata.json'
        if q.exists():
            old=json.loads(q.read_text());histories.append(dict(run=run,status=old['status'],error=old.get('error',''),seconds=old.get('seconds')))
    report=f'''# Work D5 动态防御重规划执行报告

日期：2026-11-13（Asia/Shanghai）。最终审阅状态：**WAITING_USER_D5_REVIEW**。数值运行状态：{meta['status']}。负责主体为本会话执行者，未使用平行代理或外部代跑。

## Material Passport

- 类型：确定性合成网络实验及作者侧复核；原始数据可用。
- 授权：用户完整D5指令；范围登记于审批/决策日志。仅实验实现、运行与审计；旧D4/P0待审事项未自动获批。
- 输出：本目录为最终数据入口；run01/run02失败及中间记录保留。没有修改D3正式合稿、原状态方程、拓扑或原始计划。
- 证据等级：指定六资产、三预算、两条公共攻击、有限槽局部候选；不是全局均衡或真实云实测。

## 1. 已完成计算与复用边界

完成3预算×2公共攻击×3防御方法，共18条完整执行轨迹；G和R各18次重规划，G每任务暖/零/随机三条完整交替路径，共54条路径。每预算生成一条E1公共攻击，另有中性E0。原有53测试通过；新增13项模型/接口检查通过，K'=3/2/1双方目标/离散梯度最大误差小于7e-10。当前四个核心模块与D4保存源码快照逐文件相同；旧历史计划的模型和控制直接读取，输入/源码SHA256已保存。

模型精确继承seed11的不等传播、高价值节点3配置，q=(1,1,1,4,1,1)，原八边。T=10，A=0.8，B∈{{0.6,1.2,1.8}}。t=5前alpha0=0.25，后为0.50；这是有效入口攻击效率变化，不是a0被强制翻倍。双方目标、预算和箱约束不变。每次以实际执行状态为初态，剩余时域5、10/3、5/3，对应3、2、1槽；仅执行首槽。采用原RK4、离散灵敏度、SLSQP和strict_solve，不开发新算法。

共同前缀完全一致；相同(B,E)三方法实际攻击逐分量一致。G预测攻击单独保存；R只使用上一槽攻击作持续预测，独立审计逐次确认没有未来实际攻击泄漏。E1先针对P的固定尾段求局部攻击响应，经3起点、12起点和两入口稀疏检查后冻结；未对G/R重生成实际攻击。

## 2. 防御损失与配对评价

以下为H48主评价，数值越低越好；差值正号表示G优于该参照。全时域和事件后差值一致，因为共同前缀相消。原始精度保留于CSV。

全时域：

{table(full[fullcols])}

事件后：

{table(post[fullcols])}

{' '.join(signs)}三预算/E0下G均劣于R，三预算/E1下G均优于R；这些是协议内小差异，不支持普遍优越性。G相对P的结果按上表完整保留，不能以数值通过代替性能提升。

受损、隔离业务和控制成本配对分解（事件后）：

{table(security)}

总目标和受损分项分别评价。B=0.6、E1下，G总损失低于R约0.000772885，但受损损失高约0.001868119；总目标优势来自业务和行动成本的权衡。B=1.8、E0下，G受损损失低于R约0.005454964，但总损失高约0.000577565，不能将两种指标混用。完整36行（18轨迹×事件后/全时域）双方目标及防御分解附于报告末表和objectives.csv；零终端权重保持原值。

## 3. 实际动作如何改变

所有逐资产逐槽实际a/s/r、全网用量及容量松弛见executed_controls.csv；G/R相对P的逐动作变化见resource_adjustments.csv。B1.2事件后第一槽G相对P的全部六节点配置如下；s/r为G实际执行，delta_s/delta_r为G减P。与原计划的配对差用于区分重新配置和原计划自身随时间的变化，不把事件前后跳变全部归因为alpha事件：

{table(resource)}

resources_E0/E1图将三方法完整六槽、六节点隔离和恢复分别展示，虚线为t=5；resource_use图显示全网用量与B=1.2容量线。每个方法都保留事件前控制，不以预测计划替代实际执行。

## 4. 状态与高价值资产

trajectories.csv包含18轨迹×H48/96/192全部状态采样；states_E0/E1图展示B1.2全部六资产的H192曲线。三方法曲线接近，不能通过截断纵轴夸大变化。全网累计加权受损损失为objectives中的security；高价值节点3的事件后受损面积、加权损失及终态如下（DOP853独立积分）：

{table(high)}

node_state_summary.csv保留全部节点、前/后/全时域面积和终态。状态是资产组受损比例，不是单台服务器受攻击概率。

## 5. 战略响应的实际作用与边界

G在各剩余时域中重新优化攻击计划并据此更新防御；R固定持续预测。两者使用相同观测、模型和更新时点，但预测规则和优化工作量不同。B1.2首次重规划的预测与实际输入为：

{table(predicted[['evaluation','method','a0_planned','a1_planned','a0_actual','a1_actual','first_slot_L1_error']])}

完整各次记录见attack_prediction_comparison.csv。E0下R在观测一槽后持续预测恰好正确；G仍为战略攻击候选配置资源，实际攻击与预测不相同。E1针对旧P生成，G的战略预测在此压力协议下获得小幅目标优势。这支持“方案收益依赖评价攻击轨迹”的判断，不把预测误差与收益的对应关系当作已识别因果机制，也不称E1是针对G/R的最坏攻击。

## 6. 数值质量与独立复核

记录{len(attempts)}次SLSQP起点优化，失败{int((~attempts.success).sum())}次；接受标志与成功退出分别保留。所有G路径、R/E1本方检查、三路径稳定性及H96固定候选局部偏离诊断通过。以下最大值仅来自最终候选/验收诊断，迭代中较大的改善和残差保留在trace.jsonl，不从历史记录删除。

{table(diagstats)}

独立复核{valid['checks']}项全部通过，逐项结果见independent_checks.csv。另用DOP853对实际拼接动作重积分，核对前/后/全时域双方目标、各成本分项和末态；模型右端与成本定义复用原函数，积分算法独立。核对重规划初态、只执行首槽、R只用历史攻击、统一攻击和前缀、配对算术、原文件保护以及中断前后的同参数策略一致性。源码/历史保护结果见protected_after.json。

这些检查证明本次有限槽局部候选达到登记门槛，不提供未知全局改善上界；多初值稳定不证明唯一性或纯开环Nash存在。拼接执行依赖观测历史，不是t=0开环均衡，也不是Markov反馈Nash。

## 7. 计算时间

G/R每次重规划的实际wall-clock汇总（秒）：

{table(tstats)}

全部36次更新时间在timing.csv的replanning_total，逐攻击/防御响应与每个起点耗时在response_optimization和optimizer_attempts.csv。在线G包括三初始化路径和H48停止检查；R包括三起点和H48检查。H96候选审计、E1生成分别列出；原运行的H48/96/192执行回放记录为合计时间，独立复核中另对每个H分开真实计时，写入saved_execution_replay_H48/H96/H192，不冒充原运行分项耗时。嵌套响应时间不能与任务总时间重复相加。

初始计划直接继承，历史离线wall-clock未能从既有记录独立分解，登记NA；没有把读取计划耗时冒充原始求解耗时。run03运行秒数不包含承接的B1.2历史计算，B1.2原始计时逐项继承run02，元数据明确标记来源；全部失败尝试和额外绘图/审计成本另留记录。

模型时间没有物理单位标定，执行采用理想即时切换，未模拟求解期间延迟；不能用wall-clock与5/3直接比较证明真实网络实时性。

## 8. 实际失败、修复与协议偏差

{table(pd.DataFrame(histories))}

run01仅预检结果JSON布尔编码失败；run02在B1.2完整通过后，B0.6的CSV保存中断。原件保留。修复仅涉及新增编排的记录格式和原子文件保存，不改变模型、种子、优化器或门槛。run03承接全部已通过B1.2数据和真实时间，未完成预算组按原输入重算，并检查中断前后已保存候选的一致性；不是换样本或择优重试。修订详细记录见paper/work_d5/revision_log.md。

与D4预案相比，新增H96固定候选局部响应诊断为明确记录的额外数值审计；没有重新规划H96控制器。目标/状态的正式精化仍固定已执行H48控制。旧D4提案输出目录改为用户D5目录，最终为run03。无数学或科学阈值偏差。

## 9. 可支持与不可支持的论文结论

可支持：在指定合成六资产网络和三预算下，观测当前状态后重新求解有限槽开环攻防候选、输出容量可行的逐节点隔离/恢复动作并执行下一槽的流程已经真实实现；18条轨迹在两条公共实际攻击下公平比较；相对静态继承计划的收益与G/R小差异以表中实际数值为限；可如实报告方法随攻击评价协议的优劣和计算开销。

不可支持：新求解算法创新、连续或全局Nash证明、反馈Nash、未知全局gap的上界、最坏攻击鲁棒性、真实云有效性、物理实时响应、跨拓扑/种子总体结论或G普遍胜过非博弈滚动优化。无无扰动对照，不能把重新规划与原计划的差异单独归因为alpha事件而非时域截短/再初始化。E0/E1不是随机独立重复，不报告总体显著性或置信区间。

## 10. 重现命令与文件入口

使用原Python3.11.7、NumPy1.26.4、SciPy1.11.4、Pandas2.1.4；硬件/线程和源码/模型SHA256见metadata.json。复现时必须选新的空输出目录，拒绝覆盖。

```powershell
python paper/work_d5/analysis/run_replanning.py --output results/work_d5/replanning/reproduce01
python paper/work_d5/analysis/verify_results.py results/work_d5/replanning/reproduce01
python paper/work_d5/analysis/plot_results.py results/work_d5/replanning/reproduce01
python paper/work_d5/analysis/write_report.py results/work_d5/replanning/reproduce01
```

本次实际续跑命令在metadata.json：--output results/work_d5/replanning/run03 --resume-from results/work_d5/replanning/run02。从头复现不需要承接失败目录；续跑原始计时无法以复现数值代替。

必交文件：experiment_protocol.md、executed_controls.csv、planned_controls.csv、trajectories.csv、objectives.csv、comparisons.csv、solver_audit.csv、timing.csv、figures/及本报告。附加optimizer_calls.jsonl、optimizer_attempts.csv、模型/每次初态/全部路径trace、独立复核、资源调整与预测比较、清单。source_snapshot保存数值执行时版本，delivery_sources另保存审计/绘图/报告源码，区分生成顺序。

最终提交reviews/G_D5_experiment_submission.md，等待用户实际结果审阅。没有进入D3修改或替用户批准D5结果。

## 附表：事件后与全时域完整成本分解

{table(decomp)}
'''
    (out/'D5_execution_report.md').write_text(report,encoding='utf-8')
    review=f'''# G-D5 实验结果审阅提交

日期：2026-11-13（Asia/Shanghai）。状态：**WAITING_USER_D5_REVIEW**。审核者：用户。尚未收到本轮结果批准。

## 提交材料与实际完成

- 完整报告：[D5_execution_report.md](../{out.as_posix()}/D5_execution_report.md)。
- 三预算、两公共攻击、三方法，共18完整轨迹；G/R各18次重规划；54条G初始化路径；{len(attempts)}次SLSQP起点优化全部成功。
- 数值登记门槛全部通过；{valid['checks']}项作者侧独立检查通过。原始控制、状态、损失分解、策略诊断、计算时间及失败原件完整保留。
- 计算中断修复仅影响保存方式；run01/run02保留，run03承接已通过B1.2并完成剩余两组；同参数重复候选核对通过。

## 可供审阅的主要数值

{table(full[fullcols])}

正号表示G较优；E0下G较R差，E1下G较R好，收益小且依赖评价轨迹。完整受损/业务/控制分解和高价值节点结果见报告，不能把总成本改善统称所有安全分项改善。

## 建议允许结论

在已测合成网络、预算、事件与控制类内，状态观测—剩余时域局部博弈重求—有限容量动作—下一次观测的运行流程可行；统一攻击评价能区分相对原计划的调整收益及相对非博弈滚动方法的正负边界。允许报告具体配置、绝对损失差、局部数值质量和实际计算开销。

## 必须保留的负面结果与证据缺口

G相对R在E0的全部三预算均为负；E1专门针对P且不是G/R最坏攻击；两轨迹非独立重复；没有无扰动对照、跨种子/拓扑扩展或计算延迟执行仿真。没有全局最优响应、纯开环Nash存在/唯一性、反馈Nash或真实云实时性证据。局部已发现改善不能当全局gap上界。

## 审核边界

本轮只提交D5结果及其可用表述，请用户审查后明确决定是否接受、哪些结论可进入后续稿。当前不修改D3，不自动批准旧D4/P0结果或论文定向材料。已有G1/G2授权范围不变，不伪造签字或第三方独立审稿。
'''
    reviewpath=ROOT/'reviews/G_D5_experiment_submission.md'
    reviewpath.write_text(review,encoding='utf-8')
    (out/'G_D5_experiment_submission.md').write_text(review.replace(
        '../'+out.as_posix()+'/D5_execution_report.md','D5_execution_report.md'),encoding='utf-8')
    source=out/'delivery_sources';source.mkdir(exist_ok=True)
    for pth in (ROOT/'paper/work_d5').rglob('*'):
        if pth.is_file() and '__pycache__' not in str(pth):
            target=source/pth.relative_to(ROOT/'paper/work_d5');target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(pth,target)
    print('Report and review submission generated from verified results.')


if __name__=='__main__':main()
