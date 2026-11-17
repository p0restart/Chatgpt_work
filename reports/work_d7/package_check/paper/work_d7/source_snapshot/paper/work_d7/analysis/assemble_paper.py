from pathlib import Path
import json, pandas as pd, numpy as np
BASE=Path(__file__).resolve().parents[1];D=BASE/'results/derived'
def md(df,digits=6):return df.to_markdown(index=False,floatfmt=f'.{digits}f')
actions=pd.read_csv(D/'all_asset_decisions.csv');cross=pd.read_csv(D/'cross_summary.csv');roll=pd.read_csv(D/'rolling_summary.csv');cost=pd.read_csv(D/'cost_components.csv');static=pd.read_csv(D/'static_summary.csv')
main=actions[(actions.case=='offline')&(actions.B==1.2)&(actions.method=='G')].copy()
main['区间']=main.apply(lambda r:f'[{r.t_start:.2f}, {r.t_end:.2f})',axis=1)
main['区间成本']=main[['security','business','isolation','recovery']].sum(axis=1)
short=main[main.code_index.isin([3,4])][['区间','paper_node','s','r','asset_resource','x_start','x_end','区间成本']].rename(columns={'paper_node':'资产','asset_resource':'资源','x_start':'起始状态','x_end':'结束状态'})
ct=cross.rename(columns={'protocol':'评价','J_D_G':'G损失','J_D_F':'F损失','F_minus_G':'F−G','percent':'相对差(%)'})
r=roll[roll.period=='full'].sort_values(['case','B','evaluation'],ascending=[False,True,True]).copy()
r['组别']=r.case.map({'event':'效率突变','control':'无扰动'})
r['ΔPG (%)']=r.apply(lambda x:f'{x.delta_P_to_G:.6f} ({x.percent_P_to_G:.5f})',axis=1)
r['ΔRG (%)']=r.apply(lambda x:f'{x.delta_R_to_G:.6f} ({x.percent_R_to_G:.5f})',axis=1)
rt=r[['组别','B','evaluation','J_D_P','J_D_G','J_D_R','ΔPG (%)','ΔRG (%)']].rename(columns={'evaluation':'攻击','J_D_P':'P损失','J_D_G':'G损失','J_D_R':'R损失'})
att=json.loads((BASE/'results/static/B1.2/cross_attacks.json').read_text())['aG']
attack_sentence=f'首区间v1/v2分别为{att[0][0]:.6f}/{att[0][1]:.6f}，末区间分别为{att[-1][0]:.6f}/{att[-1][1]:.6f}，末区间总攻击投入低于0.8的容量上限'
c=cost[(cost.case=='event')&(cost.B==1.2)&(cost.evaluation=='E0')&(cost.period=='full')].set_index('method')
sg=c.loc['P','security']-c.loc['G','security']
executed=actions[(actions.case=='event')&(actions.B==1.2)&(actions.evaluation=='E1')&(actions.method=='G')&(actions.code_index==3)&(actions.slot>=3)].sort_values('slot')
sentence='例如，E1下认证服务在三个更新区间实际执行的恢复强度依次为'+ '、'.join(f'{x:.6f}' for x in executed.r)+'，对应隔离强度依次为'+'、'.join(f'{x:.6f}' for x in executed.s)+'。'
exp=(BASE/'analysis/experiments_template.md').read_text(encoding='utf-8')
for k,v in {'ACTION_TABLE':md(short),'CROSS_TABLE':md(ct),'ROLLING_TABLE':md(rt),'ATTACK_SENTENCE':attack_sentence,'SECURITY_GAIN':f'{sg:.6f}','EXEC_ACTION_SENTENCE':sentence}.items():exp=exp.replace('{{'+k+'}}',v)
assert '{{' not in exp
parts=[(BASE/'analysis/intro.md').read_text(encoding='utf-8'),(BASE/'analysis/model_method.md').read_text(encoding='utf-8'),exp,(BASE/'analysis/references_formatted.md').read_text(encoding='utf-8')]
(BASE/'paper_v2_zh.md').write_text('\n\n'.join(parts),encoding='utf-8')
# Main table sources have exact numeric CSV counterparts, no manual retyping.
for name,df in [('table2_actions',short),('table3_cross',ct),('table4_rolling',rt)]:df.to_csv(D/f'{name}.csv',index=False,encoding='utf-8-sig')
protocol='''|方法/阶段|规划攻击假设|实际防御|评价/执行攻击|是否重求防御|
|---|---|---|---|---|
|离线G|双方交替局部响应|固定uDG|a0、aG、aBR,F分别评价|离线一次；评价时冻结|
|离线F|预设两入口各0.4|固定uFT|同上三条攻击|离线一次；评价时冻结|
|执行P|继承原G模型|原G尾段|每组共同E0/E1|不重新优化|
|执行G|已知参数、当前状态下的攻防计划|每次仅执行首区间|共同E0/E1；非内部预测攻击|5、20/3、25/3重求|
|执行R|上一已观测攻击在剩余时域保持|每次仅执行首区间|共同E0/E1|相同时刻仅优化防御|
|事件E1生成|固定P尾段|不改变P|在对应参数下最大化JA，随后冻结|仅攻击响应|
|无扰动组|主容量，αv1保持0.25|同样P/G/R|E0与事件组相同；E1按相同规则另算|同样更新规则|'''
metrics=json.loads((D/'metrics.json').read_text());ver=json.loads((BASE/'results/verification.json').read_text())
checks=pd.DataFrame([
['全分量有限差分梯度最大误差',pd.read_csv(BASE/'results/gate1/checks.csv').query("check.str.contains('gradient')",engine='python').value.max(),1e-6],
['最终归一化已发现改善',metrics['max_relative_improvement'],1e-7],['当前投影残差',metrics['max_incumbent_residual'],1e-4],['响应控制距离',metrics['max_response_distance'],1e-3],['三初始化控制差',metrics['max_path_spread'],1e-3],['逐时容量违反',metrics['max_capacity_violation'],1e-10],['数据库隔离',metrics['max_database_isolation'],1e-8],['独立固定控制轨迹/成本复算误差',ver['max_replay_error'],1e-6]],columns=['指标','最大值','阈值'])
checks.to_csv(D/'numerical_quality_summary.csv',index=False)
fullcost=cost[cost.period=='full'].copy();fullcost['评价']=fullcost.evaluation.fillna(fullcost.attack)
seedrows=[]
for p in sorted((BASE/'results').rglob('decision.json')):
    x=json.loads(p.read_text());seedrows.append(dict(path=str(p.relative_to(BASE)),seed=x.get('seed'),K=x.get('K'),T=x.get('T'),passed=x['passed']))
pd.DataFrame(seedrows).to_csv(D/'decision_seed_manifest.csv',index=False)
sup=f'''# D7 补充材料

本文件与正文、results和source_snapshot一同交付。所有新数值均来自D7固定非对称拓扑；不依赖包外D3补充材料。尚待人工审阅。

## S1 评价协议与模型语义

{protocol}

网络与容量完全固定，见config_new_topology.yaml和topology_assets_edges.csv。β按来源行/接收列；x是实例组受损比例；s是来源隔离，r是本地恢复。模型时间、成本与控制强度均未现场标定。主结果是一个网络、三个容量和规定攻击条件的确定性案例。初始化路径不是独立实验样本。

## S2 主容量全量行动

下表给出离线G全部36个资产—时段决策。成本列为逐节点累计损失；独立DOP853计算节点受损面积并校核汇总成本。完整精度、各分项与其他方法/条件共1080行见[all_asset_decisions.csv](results/derived/all_asset_decisions.csv)。每行含a/s/r、节点容量、总容量、剩余容量、起止状态、四项成本和诊断文件来源。原始优化输出不被后处理覆盖；原简表solver_status只写see decision.json，统一导出表提供完整相对路径。

{md(main[['区间','paper_node','a','s','r','asset_resource','total_resource','x_start','x_end','区间成本']])}

![S1 主容量原状态和资源](figures/figS1_states_resources.png)

图S1：离线G、B=1.2的v1/v4/v5原始受损比例及逐时防御容量。状态纵轴从0开始；容量上限为1.2。每条曲线为一个确定性解，无统计误差条。事件组全部原状态保存在各组trajectories.csv，实际行动见executed_controls.csv，内部计划见planned_controls.csv，二者不可混用。

## S3 损失分项、攻击收益和执行面积

下表保留全部18项离线交叉评价及24项执行评价的全时域分解。每个执行组的事件前/后分项另见results/derived/cost_components.csv。由于g全为1，attacker_value等于未加防御价值权重的总受损面积Σ∫x_i dt；它与security=Σq_i∫x_i dt不同。终端权重均为0。JA=attacker_value−attacker_effort。

{md(fullcost[['case','B','method','评价','J_D','J_A','security','business','isolation','recovery','attacker_value','attacker_effort']])}

完整交叉表：每个results/static/B*/cross_evaluation.csv；完整实际/预测攻击：cross_attacks.json和各执行组attack_scenarios.csv、planned_controls.csv。G/F各自训练结果不能直接当作共同攻击下的优劣。

### 离线计算开销与资源

{md(static[['B','method','mean_resource','seconds','spread']])}

seconds包括三路径/多初值和H48最终诊断，额外H96检查单列在timing.csv中；原字段online_seconds在这里表示离线求解耗时。事件G/R各18次重规划的中位数为{metrics['G_event_replanning_seconds']['median']:.3f}/{metrics['R_event_replanning_seconds']['median']:.3f}秒。总任务时间与嵌套单方响应不得相加。运行时长受硬件及同时运行的本地程序影响，未开展重复时延基准。

## S4 数值可信度与边界

{checks.to_markdown(index=False,floatfmt='.4e')}

1544次登记SLSQP尝试全部正常退出；345条最终响应诊断、165条质量检查通过；Gate1有28项检查，独立复算有114项。强搜索用于F攻击响应与E1生成，包括12起点与入口稀疏初值。上述为已运行检查计数，不是全局最优证明。独立复算重新写出ODE和成本，用DOP853固定控制积分；它独立于RK4实现，但不是第二团队复核，也没有重新独立优化。

H48/96/192固定控制积分已比较状态、目标和分项；主策略在H48/H96上进行多起点单方检查。仅验证K=6；本轮未做新网络K12、参数敏感性或真实部署。历史旧网络精化中曾发现可进一步改善的配置，其负证据保留在原项目，不能用旧网络结果认证新拓扑。

## S5 初始化与失败处理

主seed为20261114+1000b，b按主容量1.2、0.6、1.8取0、1、2；F在此基础上+100，F攻击响应+200。滚动seed=20261114+1000b+100e+10j，e为E0/E1索引、j为更新索引；内部路径和复核种子偏移保留在原源码及每次optimizer_calls.jsonl。decision_seed_manifest.csv提供全部主任务种子。主路径预先固定，不按收益更换。SLSQP最大300步、ftol=10^-10；交替最多40次更新，含更新后的最终检查；无阻尼。任何数值质量失败停止依赖实验并保留日志。本次登记数值批次均通过，无删除的失败优化或替换参数试验。

绘图初版发现水平箭头尖被节点覆盖，以及状态差坐标范围过窄，已按真实全轨迹范围修正；未更改任何实验数值。图件检查与人工目视记录见figures/qa/README.md。

## S6 历史成果与审批隔离

历史ODE、成本、约束、RK4灵敏度、SLSQP及D5执行机制复用；原src和D5程序SHA检查一致。D7重新计算全部主策略与图表，未导入旧拓扑控制作为新网络结果。D4-P0-1、D5-P0和D5-run03仍待审；D7执行授权不是这些历史结果的批准，也不是D7结果的最终批准。旧36配置、镜像因素交互与旧K精化不进入D7主结论，既不混合样本，也不删除原负结果。

## S7 重现方法

见[REPRODUCE.md](REPRODUCE.md)。source_snapshot保存当次核心源码与执行程序；sources/runtime_manifest.json记录其SHA。可先在现有证据包运行固定控制独立复算，再在新建目录按登记顺序重新优化。禁止覆盖本包原始结果。原论文全文PDF不随交付包复制，文献核验访问层级与定位见reference_claim_map.md。
'''
(BASE/'supplement_zh.md').write_text(sup,encoding='utf-8')
print('Assembled complete five-chapter manuscript, four main tables and self-contained supplement.')
