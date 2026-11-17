# 研究主张—证据映射

全部“通过”均指本次实现与数值检查，不是人工批准。复现入口见REPRODUCE.md。每个数据路径相对本目录；不依赖旧网络数值。

|主张/正文位置|具体证据|验证命令/来源|可以说明|不能说明|
|---|---|---|---|---|
|固定八边非对称网络，§4.1图1|config_new_topology.yaml；topology_assets_edges.csv；results/static/B1.2/model.json|run_d7.py preflight|输入遵从任务书|真实云漏洞或经验传播率|
|来源隔离与本地恢复一致，式(1)|results/gate1/checks.csv；src/core.py快照|run_d7.py preflight|方向、梯度、边界及结构诊断|实测安全措施效果|
|数据库隔离为数值零，§4.2|results/derived/all_asset_decisions.csv，code_index=4；metrics.json|summarize_results.py；verify_d7.py|本模型无出边正成本下的结构性质|数据库永远不需要其他隔离措施|
|逐时段行动可计算，图3表2|results/static/B1.2/G_controls.json；table2_actions.csv；全量1080行导出|assemble_paper.py；summarize_results.py|何时何处投入及成本/状态|可直接转为Pod命令|
|局部数值检查通过，§4.2|solver_audit.csv、optimizer_calls.jsonl、quality.csv；verification.json|verify_d7.py|1544次正常退出，345条响应诊断，114项独立复算|全局最优、连续Nash、独立团队认证|
|固定攻击F略优，表3图4a|results/static/B*/cross_evaluation.csv，attack=a0|run_d7.py cross；cross_summary.csv|三预算同攻击条件下G无优势|所有网络都无战略作用|
|各自响应下G小幅低损失，表3图4b|同表G/aG与F/aBR_F|cross_summary.csv|响应协议下0.00577%–0.01579%差异|纯防御因果增益或JD最坏攻击|
|攻击因防御改变，§4.3|B*/cross_attacks.json：max_attack_change|run_d7.py cross|最大分量变化0.002131–0.003163|显著/大幅战略收益|
|事件后G相对P改善，摘要/表4|rolling_event_B*/comparisons.csv，period=full|run_rolling.py；verify_d7.py|六个规定比较改善0.02884%–0.11623%|普遍优于任何继承计划|
|G与R排序依条件改变，§4.4|同表delta_R_to_G；表4|assemble_paper.py|E0 G略差，E1 G略好|博弈不可替代或普遍优越|
|无扰动收益不同，§4.4|rolling_control_B1.2/comparisons.csv|run_rolling.py --no-event|E0仅0.00003017；E1 G=P所报精度|E1组间纯α因果比较|
|行动与状态分时变化，图5|rolling_event_B1.2/trajectories.csv及executed_controls.csv|make_figures.py|短暂数据库正差、认证恢复先降后升相对P|全部资产所有时刻都改善|
|计算开销较高，§4.3/4.4|timing.csv item=replanning_total；derived/metrics.json|summarize_results.py|本次G/R中位14.38/3.18秒|在线实时部署或普适速度比|
|文献与贡献边界，§1–3|references.bib；reference_claim_map.md；literature_learning.md|原件/出版社/作者记录|已有直接先例，定位特定流程|首次开环非零和模型、通用新算法|
|人工审核仍待完成，稿首|01_decisions_and_provenance.md；审批记录快照|来源核验|授权实验和待审稿范围|D4/D5或D7已获结果批准|

图件逐一原始数据SHA在figures/figure_sources.json；主表由数据自动生成，精确值在results/derived/table2_actions.csv、table3_cross.csv、table4_rolling.csv。正文显示精度有限，检验使用未舍入CSV/JSON。图3两位小数的零不得作为精确零断言。
