"""Assemble traceability and manuscript tables from verified local evidence."""
from pathlib import Path
import json,hashlib,re
import numpy as np
import pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1];T=O/'tables'
def md(df):return df.to_markdown(index=False,floatfmt='.9g')
v=json.loads((O/'analysis/verification.json').read_text());sources=json.loads((O/'analysis/source_manifest.json').read_text())
def write(name,s): (O/name).write_text(s,encoding='utf-8')
def csv(n):return pd.read_csv(T/n)
# Export the exact formal Markdown table content for typesetting.
for file,prefix in [('02_experimental_design_zh.md','design'),('03_results_discussion_zh.md','results')]:
    blocks=re.findall(r'(?m)(?:^\|.*\|\s*\n)+',(O/file).read_text(encoding='utf-8'))
    for i,b in enumerate(blocks,1):
        rows=[[x.strip() for x in line.strip().strip('|').split('|')] for line in b.strip().splitlines()]
        pd.DataFrame(rows[2:],columns=rows[0]).to_csv(T/f'{prefix}_table_{i}.csv',index=False,encoding='utf-8-sig')
# Actual K control distances, distinct from multistart spread in paired_objectives.
rows=[]
for r in csv('robust_paired_objectives.csv').itertuples():
    case=f'seed{r.seed}_B{r.B}_{r.cell}'
    old=csv('matched_controls_all_nodes.csv').query('seed==@r.seed and B==@r.B and cell==@r.cell')
    newpath=R/f'results/work_c2_robustness/k_refinement/run01/{case}/warm/fine/controls.json'
    new=np.array(json.loads(newpath.read_text()))
    arr=np.array([old.pivot(index='slot',columns='node',values=k).values for k in ['a','s','r']]); emb=np.repeat(arr,2,axis=1)
    rows.append(dict(seed=r.seed,B=r.B,cell=r.cell,D_u=float(np.max(abs(new[1:]-emb[1:]))),D_a=float(np.max(abs(new[0]-emb[0]))),source=str(newpath.relative_to(R))))
pd.DataFrame(rows).to_csv(T/'k_control_distances.csv',index=False)

inv='''# D2 证据与版本清单

日期：2026-11-11（Asia/Shanghai）。本轮仅分析既有结果，没有调用优化器或积分器。所有新增文件限于paper/work_d2；原始results、src、D1、冻结配置和审批日志保持原样。

## D1接口及审批

已读取D1的贡献、提纲、引言、模型、求解、R1变更、复现备注、验证JSON、交接及11月11日模型修订说明。贡献以01_research_contributions.md两项贡献为准，旧02_paper_outline.md、06_consistency_and_review.md和D1_handoff.md的三项贡献不继承。当前模型式(1)是容量、式(3)是状态、式(4)/(5)是目标；新式(17)–(20)接续。

本地paper/reviews/reports未定位到G-D1-R1最终验收文件。用户启动任务中说明其PASS，但不将这一说明改写为本地人工审批记录。现有D1_R1_verification.json仍记录WAITING_USER，05_game_solution_zh.md旧哈希因11月11日交叉引用修订已变；修订说明解释该版本差异。当前启动指令明确授权D2写作，未授权补填审批。

DECISIONS及APPROVAL_LOG已核：原G2于11月3日批准，新增Work C2的G1与G2于11月10日批准。C2交接中“待G2”等旧文字以更晚审批条目为准。本轮未改审批文件。

## 证据层及覆盖

|命名空间|覆盖|原始入口|本轮核验|论文用途|
|---|---|---|---|---|
|matched|36配置；9个四格组|results/matched_mechanism/run01|逐份model/config/fine控制、fine_evaluation目标/分解/轨迹/容量/精化；summary与6种机制表；A/B镜像重算|主要交互及机制|
|旧supplement C2|9个D格×8方法×2模式=144评价，另原图16评价|results/supplement_c2/run02/comparison|160份summary、controls、budgets、trajectories、refinement；重算140对和14组统计，与paired/statistics一致|强基线与协议边界|
|原图反例|seed33/business_cost/B0.6|results/equilibrium_audit/counterexample01|comparison.json精确值与四格cross_evaluation.csv|负结果，不并入9D格|
|Work C2 K精化|两组四格=8配置，32路径|results/work_c2_robustness/k_refinement/run01|tables全部CSV、8份case/baseline/embedding/cross原始JSON；热启动控制距离另算|局部质量、策略类限制|
|Work C2隔离复现|seed11/B1.2，K6四格|results/work_c2_robustness/cross_environment|environment/comparison；逐格模型、fine控制/目标；误差和质量表|同主机隔离依赖重求|
|有限策略表|n3/K2四张表|results/supplement_c2/run02/finite/summary.csv|读取既有汇总与审计；本轮未重新枚举收益矩阵|仅菜单内纯均衡边界|
|P3|原三场景27配置|handoffs/A_inventory.md及原图反例来源|读取盘点，不重新全量统计324评价|范围区分，不新增主结果|
|A/B/C1/C及审批|项目审计、修复及创新定位|handoffs/*.md，DECISIONS.md，reviews/*.md|实际源码与配置辅助核查|局部性质和主张上限|

## 指标、来源与复现命令

逐条主结果索引见tables/result_provenance.csv，含命名空间、case/seed/B/cell、方法、攻击模式、K/H、原始文件、公式及图表归属。完整实际读取文件及当时SHA256见analysis/source_manifest.json；历史清单逐项比对见tables/historical_hash_checks.csv。派生表是重新汇总，不是新实验或独立复现。

匹配目标使用fine_J_D(H48)，状态和保存分项使用H12；旧C2主目标使用fine_J_D(H192)，分项H48。禁止用较粗精度分项直接拼凑细精度总目标。保存轨迹的梯形面积不冒充RK4积分目标。

```powershell
python paper/work_d2/analysis/build_analysis.py
python paper/work_d2/analysis/plot_figures.py
python paper/work_d2/analysis/finish_package.py
```

这些脚本不导入src，不调用研究求解入口；输出均限于D2。历史正式实验命令存于原协议/metadata，本轮未执行。Python3.11.7，NumPy1.26.4，Pandas2.1.4；图形使用项目Matplotlib。PDF遮挡检查依赖单独放在analysis/_qa_packages，不加入研究分析的默认包路径。

## 异常处理

旧C2 run01确为FAILED（FileNotFoundError，22.9466秒），run02只有一次成功批次。历史scenario=separated字段是基础配置沿袭，四格命名以目录和模型为准。

Work C2 manifest包含审批日志的历史哈希，与当前追加G2后的文件不同；已逐字节证明当前文件前4290字节的SHA256精确匹配旧值，差异为后续G2批准追加。保留不匹配原记录及resolved_append标记，不改旧manifest，不归零或删除异常。其余历史清单记录均匹配。

'''
inv+=f"本轮源文件登记{v['source_files']}份，实质校验{v['checks']}项，失败{v['failed_checks']}项；历史清单比对{v['hash_checks']}条（清单有重叠，不是独立文件数）。详情见tables/verification_checks.csv与anomalies.csv。\n"
write('00_D2_evidence_inventory.md',inv)

write('04_claim_evidence_matrix.md','''# D2 主张—证据映射

以下表内源路径均相对项目根目录；D2派生表在tables。状态“允许”表示证据支持限定文字，不是人工批准。

|论文主张/位置|数值及证据|原始来源与派生表|范围|反例/边界|裁决|
|---|---|---|---|---|---|
|4.2匹配上游，保持下游总量|8边、下游总权重0.32，q交换不改变g|matched各model.json；matched_edges.csv|36配置|结构暴露匹配不强制状态匹配|允许|
|5.1价值位置效应受传播条件影响|9组I_J为0.018274—0.029192|fine_evaluation/summary.json:fine_J_D；matched_four_cells.csv|3种子×3容量|含攻击共同响应；无现实因果含义|允许|
|5.1 A/B对称|目标差≤7.32e-12，交换控制差≤7.75e-11|fine控制和目标；symmetry_recomputed.csv|9组|C/D不是镜像|允许|
|5.2低容量核心隔离近零|s2/s3≤7.65e-16|fine/controls.json；matched_controls_all_nodes.csv|B0.6的12格|不能写持续两动作切换|允许|
|5.2低容量前段恢复交互负向|r2为−.007356至−.006017，r3为−.006030至−.004761|控制重算；control_interactions_all_nodes.csv|同物理前四槽，3种子|末段seed22 r2转正|允许|
|5.2中容量异质性|seed11/22全域恢复交互近零正；seed33负|同上，robust_effects历史对照|B1.2|不推普适方向|允许|
|5.2高容量多数松弛|B1.8仅1/72槽绑定|fine控制及budgets；matched_budgets.csv|12格、K6|槽非独立样本，容量上限非消耗|允许|
|5.3强基线改善|响应评价Recovery .887—4.796%，Static .661—2.190%，Fixed .029—.286%|旧C2各summary:fine_J_D；baseline_pairs/statistics.csv|9D格，H192|小收益；不同攻击响应；不可相加|允许|
|5.3固定评价反向|Fixed比较−.094142至−.016590%，0/9正向|同上common_fixed_attack|相同9D格|不能隐藏或外推全36|允许|
|5.4原图反例|12.437518228196426 > 12.436854043461201|counterexample01/comparison.json与cross_evaluation.csv|原图seed33/business_cost/B0.6|同一固定攻击交叉比较中联合较低；不证明动作有害|允许|
|5.5两组K交互保持|.0182736907→.0182733189；.0291919616→.0291096181|K_refinement原始baseline/case，interactions.csv|仅两组8格|末段控制变化、跨类偏离存在|允许|
|5.5跨类偏离|D归一化.1223—.2141%，A .1731—.1767%|case.json:cross；robust_cross_class.csv|复制K6后固定对手，K12搜索|不同于K12重新求解残差；非全局上界|允许|
|5.5同主机隔离依赖复现|目标差≤1.96e-12，控制≤1.13e-11，状态≤4.08e-12|cross_environment/comparison.json及errors表|seed11/B1.2四格|相同Python/算法，非跨平台|允许|
|一般收益来源定理、严格Nash或首创新算法|无此证据|D1贡献裁决；B/C审计|不适用|局部条件不提供全局证书|禁止|

冻结研究主张未扩展；无新增外部文献引用或优先权声明。先例威胁沿用D1/Work C已有审查，本轮不宣称重新查新。完整八方法双方目标、安全/业务/行动成本分解、资源使用及全控制数据均保留，未以弱基线差距替代强基线结果。
''')

write('05_figure_table_manifest.md','''# 图表与源数据清单

绘图脚本analysis/plot_figures.py；统计脚本analysis/build_analysis.py；表格导出analysis/finish_package.py。所有图均为Matplotlib从原始保存数据的D2派生表绘制，无生成图像或手填数值。正式输出为PDF/SVG/PNG；图内英文标签，中文标题及解释在正文。人工科学审阅：待G-D2，未代填。

|显示项|面板/筛选|原始输入|处理与单位|输出|
|---|---|---|---|---|
|Fig.1|equal/unequal两个图，取seed11 B0.6 A/C；价值交换为A/C高2、B/D高3|matched对应model.json|按beta非零项画8边；入口u/v与参数表对应；q取实际模型|figures/fig01_matched_network.{pdf,svg,png}；tables/matched_edges.csv|
|Fig.2|a–c三个B的36原值；d–f全部9组交互|36份fine_evaluation/summary.json:fine_J_D|H48，I=(D−C)−(B−A)，归一化目标单位；零基线|figures/fig02_losses_interactions.*；tables/matched_four_cells.csv|
|Fig.3|a–c隔离、d–f恢复、g–i总容量；seed11三B，C/D|fine/controls.json及各model|s/r原始强度、总用量/B，时间0–10、槽宽5/3；仅例图筛选，其他记录不删|figures/fig03_temporal_allocation.*；matched_controls_all_nodes.csv、matched_budgets.csv|
|Fig.S1|seed33/B1.2 C/D，隔离、恢复、容量、状态|上述控制及fine_evaluation/trajectories.csv|四格中C/D示例；状态H12，x为受损比例|figures/figS01_seed33_state_allocation.*；matched_states_H12.csv|
|Table1|模型和实验参数|冻结base/design及36份model|真实数值、来源、合成标记|第4节；tables/design_table_1.csv|
|Table2|八方法|src/experiments.py、supplement_c2.py及历史源码快照|训练方式、时间/动作自由度、实际容量规则|第4节；tables/design_table_2.csv|
|Fig2原值表|全部9组|同Fig2|原值6位，差值另保留完整精度|第5节；tables/results_table_1.csv|
|Table3|3强基线×2模式，9D格|旧C2逐评价summary.json:fine_J_D|H192，100×(基线−联合)/基线；范围/中位数，零负结果保留|第5节；tables/results_table_2.csv；baseline_pairs.csv、baseline_all_objectives.csv|
|Table4|反例、两组K、跨类、复现|counterexample比较JSON；Work C2 case/baseline/comparison|各证据层独立标注；不合并样本量|第5节；tables/results_table_3.csv；robust_*.csv、environment_*.csv|

## 数据与视觉检查

统计核验见analysis/verification.json。图形每次修改后重跑对齐、PDF字号和遮挡检查；结果见每图alignment.json、collision.json及analysis/figure_qa_log.txt。人工审阅尚未完成，执行者目视检查另记06_D2_review.md。

图形无误差条：这些点是同一合成构造族的确定性配置，不是现实网络抽样。主文以范围和逐配置配对表达变化，不添加置信区间或显著性星号。Fig2保留零轴；相近原值难以目视区分时用原值表和交互面板补足，不裁剪原值轴夸大优势。Fig3隔离与恢复用不同纵轴，图注明示；近零线保留。

统计表中的成本分解遵循自身保存精度，未冒充H192分解；全部六节点控制和容量保留。K控制距离使用逐槽复制和真实时间对齐，另见tables/k_control_distances.csv；paired_objectives中的stable_distance为多初值差，不作K差使用。
''')
print('Package notes and manuscript CSV tables written; K control differences:')
print(pd.DataFrame(rows).drop(columns='source').to_string(index=False))
