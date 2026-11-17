# E0 模型清点

日期：2026-11-15（Asia/Shanghai）。对象为 D7 非对称主场景，D8.1 第三版及 D8.2 精化审计作交叉核对。新增工作限于 work_e；不修改论文、正式求解器、参数、审批或历史结果。

## 来源与有效性

有效冻结基础：DECISIONS.md、reviews/APPROVAL_LOG.md、02_MODEL_SPEC.md。D7 启动授权固定新图、q[4]=4、三预算；D8.2 仅授权 K12/消融，不自动批准其研究结论。E 本轮指令明确授权审计和小规模预实验，结果待人工验收。

实际输入：paper/work_d7/results/static/B1.2/model.json、G_controls.json；与 paper/work_d7/config_new_topology.yaml、analysis/run_d7.py:model 逐项核对。主审计 B=1.2，不将旧镜像图结果用于新图。三预算存在不代表本轮对其全部证明。

|对象|实现/核对材料|实际事实|
|---|---|---|
|动力学、收益、RK4|src/core.py:dynamics/cost_rates/simulate|源端隔离、增广状态积分、无裁剪|
|自由变量、梯度、SLSQP|src/game_solver.py:ResponseProblem/local_best_response|对离散RK4的精确一阶灵敏度；容量与箱约束|
|D7实际交替|src/matched_mechanism.py:strict_solve|不使用同名通用阻尼交替的不同停止规则|
|三完整初始路径/响应核验|paper/work_d5/analysis/run_replanning.py:Run.game/pair_audit|D7复用的编排；warm主路径固定|
|现稿|paper/work_d8_1/paper_v3_zh.md 第2、3章|式(1)–(5)与实现符号/向量顺序一致|
|既有审计|paper/work_d8_1/algorithm_audit.md；paper/work_d8_2/D8_2_numerical_audit.md|局部响应和固定轨迹积分证据，不是全局gap上界|
|既有理论|paper/work_t1/T1_proofs_zh.md P1–P4|重新检查状态适定、攻击凹性推导；不继承旧图的数值常数|

未发现上述状态方程、目标、约束或变量顺序的公式—代码冲突。连续正不变性与 RK4 检查不是同一断言；论文使用帽号区分数值目标，这一点正确。D7 图中数据库无出边，但其隔离分量仍实际参与优化；不能擅自删维。

## 参数及维度

n=6，入口代码索引0/1，T=10，K=6，H=48子步/槽，物理步长10/288。防御72维，攻击12维，联合84维。D8.2 K=12/H=24保持相同步长，对应144/24/168维；本轮主要研究K6。

八边（代码索引，来源→接收）：0→2 .08；0→3 .09；1→2 .10；3→2 .11；3→4 .07；3→5 .12；2→4 .10；5→4 .05。该图为有向无环图，但本报告不借此擅自线性化。

alpha=(.25,.25,0,0,0,0)，epsilon=1，delta=.1，gamma=.3，q=(1,1,1,1,4,1)，g=1，h=.05，c_s=c_r=c_a=1，omega=nu=0，所有容量权重=1；x0=(.1,0,0,0,0,0)，A=.8。B主审计1.2，D7另有.6/1.8。动态事件后alpha[0]=.5属于独立剩余时域问题，本轮不混入离线对象。

全部向量、版本、可行采样策略、随机种子和来源SHA256由 scripts/diagnostics.py 写入 run_config.json、source_manifest.json。运行后复查来源不变。
