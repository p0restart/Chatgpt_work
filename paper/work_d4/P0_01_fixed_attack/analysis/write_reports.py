"""Write a bounded R3-M1 response from completed, validated experiment artifacts."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[4]
P=ROOT/'paper/work_d4/P0_01_fixed_attack'
R=ROOT/'reports/work_d4'
RUN=ROOT/'results/work_d4/p0_1_fixed_attack/run01'

def span(values,fmt='.6f'):
    return f'{min(values):{fmt}} 至 {max(values):{fmt}}'

def main():
    summary=json.loads((R/'P0_01_summary.json').read_text(encoding='utf-8'))
    validation=json.loads((R/'P0_01_independent_validation.json').read_text(encoding='utf-8'))
    meta=json.loads((RUN/'metadata.json').read_text(encoding='utf-8'))
    if meta['status'] not in ('COMPLETED','NUMERICAL_GATE_FAILED','EXECUTION_FAILED'):
        raise RuntimeError('Do not generate final review submission during an active/time-paused run')
    df=pd.read_csv(P/'four_cell_comparison.csv')
    quality=pd.read_csv(P/'solver_quality.csv')
    components=pd.read_csv(P/'cost_interactions.csv')
    costs=pd.read_csv(P/'objective_components_H48.csv')
    control=pd.read_csv(P/'control_differences.csv')
    table='|种子|B|I_game|I_fixed|ΔI=game−fixed|I_fixed/I_game|质量|\n|---|---:|---:|---:|---:|---:|---|\n'
    for r in df.itertuples():
        if pd.isna(r.I_fixed):
            table+=f'|{r.seed}|{r.B:.1f}|—|—|—|—|{r.quality_status}|\n'
        else:
            table+=f'|{r.seed}|{r.B:.1f}|{r.I_game:.10f}|{r.I_fixed:.10f}|{r.delta_I:+.10f}|{r.fixed_over_game:.6f}|{r.quality_status}|\n'
    complete=summary['completed_cells']==36 and summary['passed_cells']==36 and validation['status']=='PASS'
    fixed_positive=int((df.I_fixed>4e-6).sum())
    fixed_negative=int((df.I_fixed < -4e-6).sum())
    valid=df[df.I_fixed.notna()]
    if complete and fixed_positive==9:
        verdict='全部九组的外生固定攻击局部防御候选仍有可分辨的正向价值—传播交互。因此，在本构造族和登记求解流程中，攻击者战略响应并不是出现交互的必要条件；动态传播与防御优化本身已经能够产生该现象。'
        position='建议收缩任何“战略攻防独有交互”或“微分博弈不可替代”的解释，将主要贡献定位为该构造族中价值位置效应对传播条件的依赖。微分博弈保留为战略环境对照和适用边界，而非交互存在的必要条件。新增证据增强了现象的对照完整性，同时收紧了其战略归因。'
    elif complete:
        verdict=f'九组固定攻击交互中正向{fixed_positive}组、负向{fixed_negative}组，其余在4e−6分辨率内。价值—传播交互对攻击生成环境的依赖须逐组解释，不能把原GAME结果视为所有攻击规则下的稳定规律。'
        position='建议按实际变号/近零范围收缩主张，保留动态防御与战略环境的条件性对照；不主张博弈必需或普遍优势。'
    else:
        verdict='部分格缺失或数值门槛未通过，不能用当前局部结果回答全九组问题。本阶段研究判断为INCONCLUSIVE/NEEDS_REVISION。'
        position='先处理公开列明的数值/缺失问题，不据不完整结果增强贡献；所有已得正负结果保留。'
    stats=(f'统一H=48主评价下，I_game为{span(valid.I_game)}，I_fixed为{span(valid.I_fixed)}，'
           f'ΔI为{span(valid.delta_I,"+.8f")}。I_fixed/I_game为{span(valid.fixed_over_game)}；'
           f'100ΔI/abs(I_game)为{span(valid.delta_over_abs_game_percent,"+.3f")}%（分母为原GAME交互绝对值，不是损失改善率）。') if len(valid) else '暂无完整配对组。'
    relative=(f'分别以同组C格防御损失为分母，GAME交互相对量级为{span(valid.GAME_I_over_C_percent,".3f")}%，'
              f'FIXED为{span(valid.FIXED_I_over_C_percent,".3f")}%。两个分母不同，不能当作同一方法的性能收益率。') if len(valid) else ''
    explanation=''
    for kind,title in [('s','隔离'),('r','恢复')]:
        values=control['delta_'+kind]
        explanation+=f'- {title}的FIXED−GAME逐分量差范围为{span(values,"+.6f")}，最大绝对差{abs(values).max():.6f}。\n'
    modecost=costs.pivot(index='case',columns='evaluation',values='J_D')
    fixed_cross=modecost['CROSS']-modecost['FIXED']
    explanation+=f'- 在相同外生攻击下，旧GAME防御到新FIXED防御的目标下降范围为{span(fixed_cross)}，正向{int((fixed_cross>0).sum())}/{len(fixed_cross)}。这只是该固定攻击问题的局部重新优化结果，不能跨GAME攻击环境解释为“博弈损失”。\n'
    comp_table='|损失分项交互|GAME范围|FIXED范围|\n|---|---:|---:|\n'
    for part,label in [('security','受损损失 q·x'),('business','隔离业务中断'),('isolation','隔离二次成本'),('recovery','恢复二次成本')]:
        g=components[(components.evaluation=='GAME')&(components.component==part)].interaction
        f=components[(components.evaluation=='FIXED')&(components.component==part)].interaction
        comp_table+=f'|{label}|{span(g,"+.8f")}|{span(f,"+.8f")}|\n'
    technical=f'''# P0-1 数值求解与验证报告

日期为2026-11-11（Asia/Shanghai）。运行状态{meta['status']}；阶段状态WAITING_USER_G_D4_P0_1_REVIEW。数值通过与用户审核是不同状态。

## 覆盖与来源

预登记36格，实际完成{summary['completed_cells']}格，通过{summary['passed_cells']}格，未运行{summary['not_run_cells']}格。所有FIXED为新求解，每格3个H12初值路径及其3个H48精化路径；GAME保留历史完整控制，主评价统一H48，另保留H96/H192整套复核。12起点加12稀疏通道粗审计、3起点细审计只检查防御。没有攻击最佳响应或攻击Nash诊断。

共{summary['optimizer_calls']}次SLSQP调用，失败{summary['failed_optimizer_calls']}次。全部原始退出码、初值、返回控制、迭代数及残差见optimizer_attempts.csv与原始trace/audit JSON。本轮未重随机种子、未挑选最优路径、未变宽门槛。

|指标|实测最大值|预登记门槛|
|---|---:|---:|
|归一化已发现防御改善|{summary['relative_improvement_max']:.6g}|1e−7|
|当前候选投影残差|{summary['current_residual_max']:.6g}|1e−4|
|响应计划距离|{summary['response_distance_max']:.6g}|1e−3|
|H12三初值控制差|{summary['initialization_difference_H12']:.6g}|1e−3|
|H48三初值控制差|{summary['initialization_difference_H48']:.6g}|1e−3|
|H12/H48主路径控制差|{summary['integration_control_difference']:.6g}|1e−3|
|控制违反|{summary['violation']:.6g}|1e−10|
|固定计划积分误差（目标/分项/全状态最大）|{summary['max_integration_error']:.6g}|1e−6|
|独立DOP853与H192最大差|{summary['independent_max_error']:.6g}|1e−6|
|GAME相对原C1 H48目标差|{summary['GAME_baseline_replay_error']:.6g}|1e−10|

独立表达的DOP853对GAME/FIXED/CROSS逐格核验，与主代码不共用dynamics/cost_rates函数，但同一执行者及同一机器，不宣称独立团队或独立优化实现。接口自检三个中心差分方向导数误差最高5.15e−9，均通过1e−5门槛。既有53项测试先行通过，源文件指纹随后保持相同，不将其计为本次研究实验。

## 复算审计

后处理重新从序列化控制重积分全部三种主评价，重算当前防御残差并从原始目标JSON独立计算四格差、C格归一化和交叉分解。验证状态{validation['status']}，{validation['check_count']}项检查；主计划重评价最大差{validation['maximum_primary_replay_error']:.6g}，交互表差{validation['maximum_interaction_table_error']:.6g}，成本交互合计差{validation['maximum_cost_interaction_identity_error']:.6g}。检查数不是独立实验数。

A/B交换对称性在两环境实测，GAME目标最大误差{summary.get('symmetry_max',{}).get('GAME',{}).get('objective_error',float('nan')):.6g}，FIXED为{summary.get('symmetry_max',{}).get('FIXED',{}).get('objective_error',float('nan')):.6g}；完整控制和状态交换差见symmetry_checks.csv。对称性只适用于A/B，不强加于C/D。

377个原稿/源码/历史输入文件在运行前后指纹保持不变，改变列表为{summary['protected_changes']}。全部时间段、30分钟组边界停止与恢复（如有）见metadata.json，不把暂停记为数值失败。

局部多初值和小残差不提供全局最优或Nash证明，实测积分差不提供全可行域严格误差界；GAME也保持其历史局部候选性质。非研究求解的后处理同步问题及处置单列于[P0-1执行记录](P0_01_execution_notes.md)，不把它混作优化失败，也不从记录中删除。

## 复现命令

从项目根目录，首次求解必须使用尚不存在的目录；以下求解命令会运行新优化，不要覆盖本次run01。

```powershell
python paper/work_d4/P0_01_fixed_attack/analysis/run_fixed.py --output results/work_d4/p0_1_fixed_attack/reproduction01
python paper/work_d4/P0_01_fixed_attack/analysis/analyze_fixed.py
python paper/work_d4/P0_01_fixed_attack/analysis/verify_fixed.py
python paper/work_d4/P0_01_fixed_attack/analysis/plot_fixed.py
```

当前分析与核验默认读取正式run01；若复跑至reproduction01，应先显式改其输入路径并保留新脚本快照，不把两次运行混为一批。Python、依赖版本、源码、指令、设计表及协议快照在run01/source_snapshot与metadata.json。
'''
    (R/'P0_01_solver_quality.md').write_text(technical,encoding='utf-8')
    response=f'''# P0-1 研究判断与R3-M1回应

日期为2026-11-11（Asia/Shanghai）。**WAITING_USER_G_D4_P0_1_REVIEW**。这是新增实验及回应草稿，不是D3正文修订，也不是外部审稿决定。

## 一页研究判断

{verdict}

{stats}

{relative}

{position}

## 全部九组配对

{table}

全部数值为同一H48目标；原四格值、等/不等出向效应、C格分母、原始控制指针及逐格质量状态见four_cell_comparison.csv，H96/H192独立成套复核见integration_interactions.csv。

## 配置解释及不利边界

{explanation}
{comp_table}

分项与控制共同变化可组织潜在解释，但未逐一识别唯一机制。CROSS附加评价将更换攻击输入与重新优化防御作代数分解，不能把ΔI或分解项称为纯战略响应因果效应。固定攻击也产生交互是对战略独有性的不利证据，不能被正向GAME结果掩盖。所有九组和36格未按效果筛选。

## 审稿问题与回应草稿

问题根据用户提供的指令转述，独立审稿报告本地缺失，未冒称逐字引用原报告。需要澄清现有价值—传播交互是否依赖攻击者的战略响应。

**回应草稿**

我们补充了与原36个匹配配置逐格对应的外生固定攻击对照。每槽固定入口0和1的攻击强度为0.4，其余为0，在保持原模型、成本、容量、时域及六槽联合防御可行集不变的条件下，分别从均分、零和随机初值重新优化防御计划。原GAME控制未被重新优化或替换，新旧目标统一以H48评价，并完成H96/H192积分复核、局部偏离与投影残差诊断和独立积分表达核对。

{verdict} {stats} 我们据此建议将贡献定位调整为价值位置与传播条件在该动态防御模型中的条件性交互，并用攻防博弈提供战略环境的对照，而不再将战略响应作为交互的独有来源。ΔI仅表示两种控制环境下的交互差异，因为防御计划也随攻击设定共同变化，不能直接作纯粹的攻击响应因果归因。全部九组原值、控制和数值质量已列入本阶段实验包。

**中文核对**

新增实验已实际执行，数值状态见质量报告；贡献措辞为建议，尚未写入D3，不能在正式回应中声称稿件已经修改。论文整合须等待用户对本阶段及后续阶段分别审核。P0-2/P0-3未执行。
'''
    (R/'P0_01_m1_response.md').write_text(response,encoding='utf-8')
    submission=f'''# G-D4-P0-1 审核提交

日期为2026-11-11（Asia/Shanghai）。**状态 WAITING_USER_G_D4_P0_1_REVIEW**。用户尚未批准本阶段结果。本报告的数值通过不自动转为人工批准。

## 结果与建议定位

{verdict}

{stats}

{position}

## 证据清单

- [正式协议](../paper/work_d4/P0_01_fixed_attack/protocol.md)、[36格设计表](../paper/work_d4/P0_01_fixed_attack/design_matrix.csv)、[用户启动指令快照](../paper/work_d4/P0_01_fixed_attack/instruction_source.md)。
- [原始运行目录](../results/work_d4/p0_1_fixed_attack/run01)、[元数据](../results/work_d4/p0_1_fixed_attack/run01/metadata.json)、[先导质量关卡](../results/work_d4/p0_1_fixed_attack/run01/pilot_gate.json)。
- [九组四格完整对比](../paper/work_d4/P0_01_fixed_attack/four_cell_comparison.csv)、[全部配置与损失](../paper/work_d4/P0_01_fixed_attack/controls_costs.csv)、[控制差](../paper/work_d4/P0_01_fixed_attack/control_differences.csv)、[完整状态差](../paper/work_d4/P0_01_fixed_attack/state_differences_H48.csv)、[分项交互](../paper/work_d4/P0_01_fixed_attack/cost_interactions.csv)。
- [交互对比图](../paper/work_d4/P0_01_fixed_attack/figure_interaction_comparison.png)、[低容量时序](../paper/work_d4/P0_01_fixed_attack/figure_temporal_seed11_B0.6.png)、[中容量时序](../paper/work_d4/P0_01_fixed_attack/figure_temporal_seed11_B1.2.png)、[高容量时序](../paper/work_d4/P0_01_fixed_attack/figure_temporal_seed11_B1.8.png)。同名PDF/SVG可检查。
- [求解质量](../reports/work_d4/P0_01_solver_quality.md)、[逐格质量](../paper/work_d4/P0_01_fixed_attack/solver_quality.csv)、[全部优化调用](../paper/work_d4/P0_01_fixed_attack/optimizer_attempts.csv)、[复算核验](../reports/work_d4/P0_01_independent_validation.json)、[研究判断及回应草稿](../reports/work_d4/P0_01_m1_response.md)。

## 登记协议符合性

36格完成{summary['completed_cells']}，数值通过{summary['passed_cells']}，未运行{summary['not_run_cells']}；SLSQP {summary['optimizer_calls']}次，失败{summary['failed_optimizer_calls']}。复算核验{validation['status']}，{validation['check_count']}项；历史输入保护改变列表{summary['protected_changes']}。全量九组已纳入，不根据符号筛选；GAME未替换、FIXED全部新优化、三组时序可查、交叉评价独立命名。独立审稿报告缺失已按指令登记，不影响按所给R3-M1问题执行。

## 未解决问题及人工决定

请审核是否接受该阶段证据及上述贡献定位。当前只完成P0-1，不证明拓扑/参数范围或全部九组K12稳定；P0-2/P0-3只有方案占位，须分别获得后续启动指示。D3原稿、模型与历史结果保持不变，APPROVAL_LOG既有批准条目未修改；不记录G-D4 APPROVED，不实际投稿。

本阶段提交后停止。
'''
    (ROOT/'reviews/G_D4_P0_1_submission.md').write_text(submission,encoding='utf-8')
    print('Wrote R3-M1 report, solver report and G-D4-P0-1 review submission; no manuscript changes.')

if __name__=='__main__':main()
