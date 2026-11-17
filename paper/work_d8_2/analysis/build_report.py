"""Build D8-2 Chinese report and evidence map from unrounded saved results."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from paper.work_d8_2.analysis.run_d8_2 import BASE,D7,STATIC,ROLL,load_controls,sha,csv

def read(name):return pd.read_csv(BASE/name)
def table(df,cols=None,digits=9):
    if cols is not None:df=df[cols]
    def fmt(v):
        if pd.isna(v):return '—'
        if isinstance(v,(float,np.floating)):return f'{v:.{digits}g}'
        return str(v).replace('|','/')
    lines=['| '+' | '.join(map(str,df.columns))+' |','|'+'|'.join(['---']*len(df.columns))+'|']
    lines+=['| '+' | '.join(fmt(v) for v in row)+' |' for row in df.itertuples(index=False,name=None)]
    return '\n'.join(lines)

def main():
    obj=read('K12_vs_K6_objective_comparison.csv');base=obj[((obj.K==6)&(obj.H==48))|((obj.K==12)&(obj.H==24))]
    dif=read('results/K12/objective_changes.csv');delta=dif[(dif.integration_level==0)&(dif.metric=='J_D')].copy();delta['change_percent']=100*delta.relative_change
    controls=read('K12_vs_K6_control_comparison.csv');controls=controls[controls.node==-1]
    cross=read('K12_cross_evaluation.csv');cross=cross[cross.H==24]
    crossdiff=read('results/K12/G_F_same_attack_differences.csv')
    ranks=read('results/K12/asset_rankings.csv');resources=ranks[ranks.kind=='resource'].pivot(index=['method','node'],columns='K',values='mean').reset_index()
    resources.columns=['method','node','K6_mean','K12_mean'];resources['change']=resources.K12_mean-resources.K6_mean
    four=read('results/R_LAG/four_method_objectives.csv');post=four[four.period=='post'].sort_values(['evaluation','J_D'])
    pairs=read('results/R_LAG/paired_comparisons.csv');pairs=pairs[pairs.period=='post']
    means=read('results/R_LAG/prediction_error_time_means.csv')
    quality=read('results/numerical_quality_maxima.csv');verification=json.loads((BASE/'results/verification.json').read_text())
    # Time comparison retains its historical/current provenance and excludes nested calls.
    oldtime=pd.read_csv(ROLL/'timing.csv');newtime=read('results/R_LAG/timing.csv')
    oldtime=oldtime[(oldtime.method.isin(['G','R']))&(oldtime['item']=='replanning_total')].copy();oldtime['source']='D7_saved'
    newtime=newtime[newtime['item']=='replanning_total'].copy();newtime['source']='D8_2_current'
    times=pd.concat([oldtime,newtime],ignore_index=True)
    csv(BASE/'results/R_LAG/replanning_time_comparison.csv',times.to_dict('records'))
    ts=times.groupby(['source','method']).seconds.agg(['count','median','min','max']).reset_index()
    action=read('results/R_LAG/action_changes.csv')
    aa=action.groupby(['evaluation','update','control'])[['replanning_change','temporal_change','minus_G']].agg(lambda x:float(abs(x).max())).reset_index()
    csv(BASE/'results/R_LAG/action_change_maxima.csv',aa.to_dict('records'))
    usage=[]
    for method in ('G','F'):
        for k in (6,12):
            u=load_controls(STATIC/f'{method}_controls.json' if k==6 else BASE/f'K12_{method}_controls.json')
            for slot in range(k):usage.append(dict(experiment='A',method=method,K=k,evaluation='own',slot=slot,
                defense=float((u[1][slot]+u[2][slot]).sum()),attack=float(u[0][slot].sum()),B=1.2,A=.8))
    for event in ('E0','E1'):
        u=load_controls(BASE/f'results/R_LAG/{event}_executed.json')
        for slot in range(6):usage.append(dict(experiment='B',method='R-LAG',K=6,evaluation=event,slot=slot,
            defense=float((u[1][slot]+u[2][slot]).sum()),attack=float(u[0][slot].sum()),B=1.2,A=.8))
    csv(BASE/'results/resource_usage.csv',usage)
    extrema=[]
    for p in [BASE/'results/K12/cross_states.csv',BASE/'results/R_LAG/E0_states.csv',BASE/'results/R_LAG/E1_states.csv']:
        frame=pd.read_csv(p)
        for bound in ('min','max'):
            a=frame[[f'x{i}' for i in range(6)]].to_numpy();flat=int(a.argmin() if bound=='min' else a.argmax());row,node=np.unravel_index(flat,a.shape)
            context={k:frame.iloc[row][k] for k in frame.columns if not k.startswith('x')}
            extrema.append(dict(source=p.relative_to(BASE).as_posix(),bound=bound,value=a[row,node],node=node,**context))
    csv(BASE/'results/state_extrema.csv',extrema)
    numcols=['check','value','threshold','experiment','evaluation','method','update','path','audit','player','H','count','all_passed']
    numcols=[c for c in numcols if c in quality]
    qa=BASE/'figures/qa/attempt03/summary.json'
    text=f'''# Work D8-2 补充仿真实验报告

日期：2026-11-15，Asia/Shanghai。状态：实验A/B计算完成，数值审计通过；本报告供人工审阅。只开展本轮授权实验及后处理，没有修改论文第三版。程序节点0–5对应论文v1–v6。

## Material Passport

- 类型：确定性仿真实验结果与作者侧数值审计。
- 数据：D7指定六资产八边合成网络，B=1.2；新增K12及两条R-LAG执行轨迹。
- 核验状态：数值检查PASS；不同积分算法复算固定控制，不是第二台机器重优化、外部审查或全局均衡认证。
- 原始输入：source_and_config_manifest.json中的182个文件及映射；D8-1派生表不作实验输入。

## 1. 直接回答五项验收问题

1. **K6的资产平均资源优先级保持，逐段动作不能称完全稳定。** G/F的时间平均总资源均保持 v1>v2>v3>v4>v5>v6。K12相邻两段平均映射回K6后，G的a/s/r最大差分别为0.0131623、0.00861277、0.00280266；子段内仍存在0.136390、0.0648215、0.105487的最大变化。总目标接近与动作分辨率的影响同时存在。
2. **G/F的比较方向在K12保持。** 同一a0下F损失略低，同一aG或aBR,F下G略低；没有统一支配关系。G自身响应协议的总损失降低约{-delta.loc[delta.method=='G','change_percent'].iloc[0]:.6f}%，F固定a0下约{-delta.loc[delta.method=='F','change_percent'].iloc[0]:.6f}%。G的攻击也随K改变，该行不是只改变防御的因果效果。
3. **每次更新攻击响应带来可观测但很小的执行差异。** E0下G的事件后损失比R-LAG高0.000297971（约0.004305%，分母为G）；E1下G比R-LAG低0.000325850（约0.004729%，分母为G）。差异高于积分误差，未证明具有实际云运维意义。
4. **方向在E0/E1不一致。** E0排序R<R-LAG<G<P，E1排序G<R-LAG<R<P，均以损失越低越好。
5. **新增证据支持指定网络中平均配置和比较方向对一次K精化保持，以及预测更新的条件性小幅差异。** 不支持博弈重规划普遍优越、预测误差独立因果贡献、连续控制收敛、全局Nash或真实部署有效。

## 2. 执行、参数与来源

原参数全量见source_and_config_manifest.json和D7原model.json。T10/B1.2/A0.8、入口v1/v2、q5=4、八条有向传播边、成本、容量系数、初始状态均不改变。当前核心、D5编排及D7脚本与D7实际source_snapshot哈希一致。182个登记来源在收尾复查；全部D7/D8-1来源未改。项目根DECISIONS.md与APPROVAL_LOG.md只追加本轮明确执行授权，前缀字节哈希另行核验，不冒充结果批准。

阶段记录位于checkpoints/gate0..4.json。Gate0来源登记通过；Gate1的K12及K3/2/1全分量梯度、目标、容量映射、嵌入等价和小规模响应检查通过；Gate2的K12正式求解/交叉完成，用时164.62 s；Gate3比较完成；Gate4六次R-LAG更新及执行完成，用时47.50 s。Gate5在图件和交付核验完成后由finalize.json登记。

首次启动A在创建结果目录时发生一次基础设施错误，尚未调用优化器，记录launch01_preoptimization_failure.json。修复独立适配器的父目录创建并公开说明后，按原登记设置启动，未丢弃任何数值结果、未改参数或更换初始化。早期图件自动检查曾未找到已有本地PDF检查依赖，且静态扫描未识别循环导出；保留首轮日志，补充依赖路径和显式导出后复核。这些不是实验数值失败或重优化。

正式优化尝试149次（K12 95次、R-LAG 54次），另有Gate1小规模6次，全部正常退出。交替过程早期偏离量允许较大，验收针对各路径最终候选及固定候选复核，不用全过程早期残差充当最终Nash诊断。所有起点、控制、退出码、实际种子及耗时保存在optimizer_calls.jsonl、optimizer_attempts.csv、trace.jsonl。

## 3. 实验A：控制精化

### 3.1 相同物理积分步长

K6/H48与K12/H24都为10/288；H再加倍两次分别形成10/576、10/1152。没有重新优化K6，只复算固定策略。复制K6每段两次嵌入K12，在相同物理步长下状态与目标差均为0。K12主解始终取Uniform，三路径最终控制差为0.000111374，未按收益选路径。

下表采用各方法自身训练/响应攻击：G为aG、F为a0。因此G/F两行之间不能直接当同攻击方法比较。K6与K12自身G攻击不同，双边目标的改变可能同时反映攻防策略变化。

{table(base,['method','K','H','J_D','J_A','security','business','isolation','recovery'])}

{table(delta,['method','K6','K12','difference','change_percent'])}

完整三层匹配积分结果见K12_vs_K6_objective_comparison.csv；分项绝对/相对变化见results/K12/objective_changes.csv。G安全损失降低0.0212593，但业务、隔离和恢复成本分别增加0.00172668、0.00418777、0.00605034。F的对手a0跨K相同，因此其损失变化可直接解释为此固定攻击下新增时间分辨率的数值改善，仍不是全局最优证明。

### 3.2 动作差异与资产优先级

node=-1表示全部六资产合并；Linf/RMSE比较的是K12两段均值减K6；within_parent比较同一原区间内第二子段减第一子段。攻击合并RMSE含四个非入口数值零，入口各自RMSE另保留在完整CSV，不能把合并RMSE当入口专属误差。

{table(controls,['method','control','Linf','RMSE','within_parent_Linf','within_parent_RMSE'])}

{table(resources)}

平均总资源顺位全部保持。隔离方面，G非零资产顺序v1>v3>v2>v4，F为v1>v2>v3>v4；v5/v6均为数值零（1e-8排序容差下并列，不把舍入噪声解释为排名反转）。恢复顺序两方法均为v1>v2>v3>v5>v4>v6。具体逐资产、逐区间变化与映射值在asset_rankings.csv、asset_means.csv、subinterval_changes.csv中。只有两个K值，不能据此宣称控制离散已收敛。

![G防御行动精化](figures/fig1_G_defense_controls.png)

图1：G六资产隔离s和恢复r的阶梯控制，K6虚线/K12实线，无平滑，全部六资产显示。相同颜色代表相同行动。全量数据为两组原始控制JSON。

![G攻击精化](figures/fig2_G_attack_controls.png)

图2：两个入口的G攻击强度也随精化调整，不把G目标差全部归于防御精化。

![平均资源配置](figures/fig3_asset_mean_resource.png)

图3：G/F在两个K值下的逐资产时间平均s+r；固定确定性实例，没有误差条或统计重复含义。

### 3.3 K12完整交叉评价

{table(cross,['method','attack','J_D','J_A','security','business','isolation','recovery'])}

{table(crossdiff,['K','attack','G','F','F_minus_G','percent_F_to_G'])}

同一列内才是同一攻击条件；跨K的aG/aBR,F分别重新生成，标签相同不表示数值相同。攻击最佳响应最大化JA，不能解释为对JD的最坏攻击。K12的G与F在各自响应协议下差异依然很小。完整H24/48/96成本分项、状态和每段容量见K12_cross_evaluation.csv、results/K12/cross_states.csv、cross_resource.csv。

## 4. 实验B：R-LAG

R-LAG首次使用离线G的攻击[3:6]，后两次严格使用同一E0/E1分支上一次G选定warm计划的攻击[1:]，分别为3、2、1段。所有六次输入来源哈希、切片、自身初态和自身防御暖启动都有记录，provenance_checks.csv逐项完全一致。实际攻击与D7 P/G/R逐分量完全相同，前三段防御也完全相同；只执行当前计划首段，不把整个预测计划视为执行结果。第一次状态为共同x(5)，之后来自R-LAG自身上一执行段终态。未重新求解D7的G/P/R或重新生成冻结攻击。

### 4.1 主要结果：[5,10]事件后累计损失

{table(post,['evaluation','method','security','business','isolation','recovery','J_D'])}

下表正值表示R-LAG优于比较方法，百分比分母为对应比较方法。

{table(pairs,['evaluation','comparator','comparator_minus_R_LAG','percent_comparator_to_R_LAG'])}

R-LAG相对P在两种条件下改善约0.062214%和0.160711%，但相对G的方向反转。对“重新求当前攻击响应”的增量，采用R-LAG−G：E0为−0.000297971，E1为+0.000325850。正值才表示G较好。它们是两条算法执行轨迹的差异，包含后续自身状态及防御暖启动的累积反馈，不是将状态逐次完全匹配后识别出的纯攻击更新因果效应。

![R-LAG相对G的分项损失](figures/fig4_R_LAG_loss_decomposition.png)

图4：R-LAG−G各分项及总JD，放大1000倍；正值为R-LAG成本较高。相反方向的分项抵消造成很小的净差异，不以安全损失单项代替综合损失。

### 4.2 攻击预测与防御变化

下表仅取每次更新实际执行的首区间，三个等长区间的时间平均。L1/Linf只对两个攻击入口计算。

{table(means)}

E0中R的预测最贴近实际，R-LAG居中，G最远；E1中G最贴近，R-LAG居中，R最远，方向与总损失排序一致。这是指定冻结攻击下的一致解释，不能推出真实攻击预测能力、误差与损失的单调定理或独立因果机制。所有剩余预测段误差另存R_LAG_prediction_errors.csv；不把这些尚未执行的段当作实际行动。

![预测误差](figures/fig5_prediction_errors.png)

图5：三次更新首区间的L1偏差，无平滑和统计推断。

各次防御行动最大改动如下：replanning_change是相对自身上一计划同一待执行段，temporal_change是相对上一实际执行段，minus_G是相对D7 G在同一绝对时段。三种口径不同。

{table(aa)}

逐资产变化见results/R_LAG/action_changes.csv，实际容量见R_LAG_E0/E1_controls.csv及results/resource_usage.csv，状态三精度轨迹见results/R_LAG/E0/E1_states.csv。全时域辅助结果保存在各objectives.csv中；共同历史完全相同，事件后和全时域绝对配对差一致，但百分比分母不同。

### 4.3 计算耗时

{table(ts)}

单位为实际墙钟秒。replanning_total包括本方法初始三起点与H48最终响应审计，H96额外审计单列；嵌套单方调用不重复累加。G/R是D7历史保存时间，R-LAG为本次时间，不是同时重测的性能基准。R-LAG表中仅包含新增防御优化成本，**仍依赖已有G历史攻击计划的生成成本**，不能据此说R-LAG可以独立替代G或更便宜地部署。模型时间未实测标定，也未模拟计算期间系统继续演化，不能宣称实时能力。

## 5. 数值质量与来源审计

下表报告各检查的最大值及出现位置。完整每条诊断见K12_numerical_quality.csv与R_LAG_numerical_quality.csv；原始退出码和完整控制见两个实验目录的日志。缺失位置表示该检查适用于整条执行轨迹；source_row保存在完整表，可追溯。

{table(quality,numcols)}

Gate1最大梯度误差4.17755e-9（K12防御向量分量22）；三路径最大差0.000111374；归一化已发现改善最大2.78705e-9、当前点投影残差最大7.40881e-5，均在K12 G Random路径最终候选；响应距离最大8.56517e-5也在该候选。原始迭代过程不等同于最终验收集合。小规模响应的6次尝试全部正常退出，独立保存在gate1_small_response_raw.json。状态范围原始极值与位置另存results/state_extrema.csv，容量逐段记录另存results/resource_usage.csv。

采用独立实现的增广ODE右端及DOP853，对本次6条K12交叉轨迹和2条R-LAG完整轨迹重新积分，状态/成本最大差{verification['independent_max_error']:.9g}，低于1e-6。该程序不调用优化器；这是同一执行者使用另一积分算法的数值审计，不是外部独立复现。结果见results/independent_fixed_control_audit.csv。全部{verification['quality_rows']}条展开数值检查通过，源码及原数据哈希保持。

上述工程检查不是未知全局Nash gap上界，不证明连续控制全局最优、均衡存在唯一或求解器全局收敛；K12只是新增的受限分段常值策略类。没有新参数扫描、其他预算重跑、真实云部署或新理论证明。新增图件均直接读取本次保存的控制、目标和比较表，来源哈希见figures/figure_sources.json。

## 6. 结果解释与交付边界

本轮关闭了“指定D7网络尚无K12控制精化”和“缺少历史博弈预测消融”两个有限证据缺口。平均资产配置与G/F同列比较方向保持，但子时段动作变化可见；当前G攻击更新在E1稍有收益、在E0稍有代价。证据不支持扩大为稳定博弈优势，论文若后续修订，应继续保留小收益、方向反转、合成参数及局部数值边界。

论文第三版、D7原始数据与D8-1文件均未修改。全部新增结果交用户进行下一轮审核；没有将本轮计算通过登记为G2或结果人工批准。复现方式见README_REPRODUCE.md，完整文件与SHA256见data_manifest.csv及SHA256SUMS。
'''
    (BASE/'D8_2_experiment_report.md').write_text(text,encoding='utf-8')
    claims='''# D8-2 主张—证据映射

2026-11-15。全部为指定六资产网络、B1.2的确定性仿真观察。不存在自动改稿或结果人工批准。

|主张|直接证据|可复核操作|支持范围/不能推出|
|---|---|---|---|
|平均总资源排序保持|results/K12/asset_rankings.csv；两组G/F原控制|对s+r按等长段取平均、按1e-8容差排序|两种K、指定模型；不是策略逐点稳定或全局收敛|
|K12映射回K6后控制差有限，但子段变化明显|K12_vs_K6_control_comparison.csv；subinterval_changes.csv|相邻两段均值减K6，逐段Linf/RMSE及内部差|必须同时报告平均与子段变化，不能只看目标|
|G/F同攻击列内方向保持|两K交叉矩阵；G_F_same_attack_differences.csv|同一K同一攻击的F−G|跨K的aG/aBR,F是不同数值轨迹，不是共同攻击|
|G自身JD降约0.099655%，F固定攻击JD降约0.152870%|K12_vs_K6_objective_comparison.csv；objective_changes.csv|匹配物理步长、(K12−K6)/abs(K6)|G双方控制均改变；局部策略候选，不证明全局最优|
|当前攻击更新增量在E0/E1方向相反且很小|R_LAG_E0/E1_objectives.csv；D7原objectives.csv；paired_comparisons.csv|H48、post、同一冻结实际攻击下R-LAG−G|包含后续自身状态差，非纯攻击预测因果效果；无普遍优势|
|R-LAG严格使用历史G攻击计划和自身状态|input_provenance.json；provenance_checks.csv；executed_first_interval.json|同分支源计划切片、暖启动与状态完全相等核对|预测机制消融，仍依赖G历史计算，不是独立普通基线|
|预测误差排序与损失方向一致|all_method_prediction_errors.csv；prediction_error_time_means.csv|每更新首段两入口L1/Linf的时间均值|描述性一致；非现实预测准确率或独立因果机制|
|数值诊断通过|K12/R_LAG_numerical_quality.csv；results/verification.json；各原始优化日志|按登记门槛检查、最大值及位置保留|受限策略空间的已发现偏离，不是全局Nash gap上界|
|固定轨迹积分一致|independent_fixed_control_audit.csv；积分精化检查|独立ODE右端+DOP853复算8条新轨迹|同作者数值审计，不是另一机器重优化或外部认证|
|原数据和核心保持|source_immutability_check.csv；source_and_config_manifest.json|182项来源SHA256及授权日志追加前缀|D7/D8-1原件不改；授权日志追加不等于结果批准|

复现命令见README_REPRODUCE.md；所有分析程序位于analysis/，未修改src/。
'''
    # Derive the displayed F percentage from saved data rather than a manual constant.
    fpercent=-float(delta.loc[delta.method=='F','change_percent'].iloc[0])
    claims=claims.replace('0.152870%',f'{fpercent:.6f}%')
    (BASE/'D8_2_claim_evidence_map.md').write_text(claims,encoding='utf-8')
    (BASE/'D8_2_remaining_issues.md').write_text('''# D8-2 剩余事项

2026-11-15。实验A/B的限定计算已完成；没有因未获预期优势而新增实验或筛选结果。

|事项|实际状态|对结论的影响|
|---|---|---|
|控制精化|K6/K12已对比，只有两个K|平均排序和方向保持，不能证明控制离散已收敛；子段动作差异必须保留|
|当前战略响应的增量|E0不利G、E1有利G，差仅约3e-4|不支持普遍优势；不能把G/P全部收益归于博弈|
|纯机制因果识别|R-LAG按自身执行状态滚动，历史预测来自G|合法消融，但含状态/暖启动反馈，不是每更新同状态的纯因素效应|
|R-LAG计算依赖|沿用已保存G历史预测|不能称独立可部署普通基线，耗时不含历史G生成成本|
|随机初始化和数值误差|预登记路径、起点和门槛通过|多起点不是全局偏离穷举；微小差异不等于实际重要性|
|全局均衡与真实云|本轮未证明/未实测|不扩大理论或部署主张|
|独立计算复现|同作者另一ODE积分器已复算；无第二台机器全流程重优化|不称外部认证或跨机器独立重优化|
|交付与审阅|结果供用户审核；第三版保持原样|WAITING_USER_D8_2_REVIEW；后续论文修改和结果采纳另由用户决定|

历史D4/D5待审及D7/D8-1人工审阅状态均未擅自更改。首次A启动的目录错误发生在优化前，记录保留；未发生数值失败后更换路径或调参通过。图件首次自动检查的依赖/扫描问题日志保留，最终检查与目视记录见figures/qa/。
''',encoding='utf-8')
    print('Report and evidence maps written',flush=True)
if __name__=='__main__':main()
