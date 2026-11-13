# D2 证据与版本清单

## 2026-11-11 最小修订版本追加

当前D1两份正文及重组说明与原D2 source_manifest登记哈希全部相同。式(1)–(20)逐项核对见D1_D2_equation_alignment.md；未发现旧版引用误用，无D1修订。D2只修改式(18)百分数显示约定及5.1交互相对量级说明，未修改任何数值CSV/图形。新增排版检查清单与轻量审查包；最新文件哈希见analysis/minimal_revision_version_manifest.json，旧源清单不覆盖。修订前正文/交接/清单快照在analysis/minimal_revision_before。G-D2人工审批仍待用户，不启动D3。

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

本轮源文件登记1356份，实质校验857项，失败0项；历史清单比对3310条（清单有重叠，不是独立文件数）。详情见tables/verification_checks.csv与anomalies.csv。
