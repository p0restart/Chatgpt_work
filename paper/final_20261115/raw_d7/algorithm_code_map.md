# 算法—代码—输出映射

映射对象为paper_v2_zh.md式(1)–(8)、算法1/2及本次实际执行源码。核心源码未修改；可移交副本保存在source_snapshot。以下行号指该快照，文件SHA见sources/runtime_manifest.json。

|论文步骤|实际模块/起始行|保存的证据或说明|
|---|---|---|
|式(1)来源隔离、入口攻击、本地恢复|source_snapshot/src/core.py:86 dynamics|β.T乘来源向量；与preflight全分量梯度及独立ODE复算一致|
|式(2)非零和目标与分项|core.py:93 cost_rates；:130 simulate|security/business/isolation/recovery/attacker_value/attacker_effort；终端项另加|
|式(3)箱约束、逐时容量|core.py:70 check_controls；game_solver.py:22 ResponseProblem|每时段拼接s再r，攻击仅取entry；C为时段块对角矩阵|
|RK4与离散灵敏度|game_solver.py:64 value_gradient|对RK4映射求控制灵敏度，非连续伴随边值求解|
|投影残差|game_solver.py:116 projected_residual|在箱与单时段加权容量集合上投影；报告当前点残差|
|算法1 LocalResponse|game_solver.py:135 local_best_response|SLSQP；300步；ftol=1e-10；当前/零/随机初值；可行不劣接受；全部退出状态另查|
|同一完整对双方响应与式(6)|game_solver.py:181 observed_gaps|先固定同一u/a分别调用响应；保留signed及截断到非负的发现改善|
|交替顺序与停止|matched_mechanism.py:42 strict_solve|m=0..40检查；不通过先更新防御，再在新防御下另求攻击；没有阻尼|
|三初始化路径与固定主路径|source_snapshot/paper/work_d5/analysis/run_replanning.py:158 Run.game|warm/zero/random；离线warm为Uniform；selected_path固定warm；spread与所有退出状态作为质量条件|
|H48/H96多起点复核|run_replanning.py:132 one_audit；:150 pair_audit|同一完整策略对分别检查；solver_audit.csv，H96不改变实际执行计划|
|F与R的固定对手优化|run_replanning.py:194 unilateral|三起点及H96复核；强搜索仅攻击生成strong=True，另加12起点及入口稀疏初值|
|D7固定场景构造|analysis/run_d7.py:model|显式八条边、q索引4、入口0/1；未调用旧拓扑生成器|
|离线G/F与交叉评价|analysis/run_d7.py:static/cross|每预算模型、36行行动、三种攻击×两防御的6项交叉表|
|算法2事件与公共历史|analysis/run_rolling.py:9 run_budget|从D7新离线G加载；前三区间共同；仅alpha[0]变化|
|算法2攻击生成|run_rolling.py:run_budget；D5 unilateral|E0均分；E1固定P尾段防御生成并冻结；不是攻击者最大化JD|
|算法2每步剩余问题|run_rolling.py:run_budget|各方法各自当前状态；剩余K=3/2/1；G用Run.game，R用Run.unilateral|
|R攻击预测|run_rolling.py:run_budget|上一区间观测攻击，首次用共同历史第三段；预测保存planned_controls|
|只执行首时段与累计|run_rolling.py:run_budget；D5 execute:265|实际攻击独立；H48/96/192再积分；每组common_attack_and_prefix质量检查|
|逐资产完整行动与成本|analysis/summarize_results.py:action_rows|1080行；每节点受损面积用DOP853后处理；30组汇总成本独立核对|
|独立复算|analysis/verify_d7.py:replay|不调用core.dynamics/cost_rates/RK4，独立写ODE；仅固定控制复算，不独立重新优化|
|图表数据|analysis/make_figures.py；analysis/assemble_paper.py|源表SHA见figures/figure_sources.json；主表精确CSV见results/derived/table*.csv|

## 与D6编辑草案的实质修正

1. 明确同一完整策略对的双边偏离检查，随后才更新防御并另算攻击；不是“旧攻击+新防御”混合检查。
2. 不把交替顺序解释成Stackelberg时序；不把SLSQP写成已完成全局argmin。
3. 明确最大40次更新但包含m=40更新后的检查；正文没有使用通用alternating_responses的另一套停止设置。
4. 多初值当前/零/随机与三条完整博弈路径分层表述；主路径固定，而非按最终收益挑选。
5. 正常退出与可行不劣接受是不同检查；最终要求登记优化调用均成功。
6. PMP/KKT仅用于边际解释。不存在“先解连续伴随系统，再将其控制直接用于本次仿真”的隐藏步骤。

## 复用适配边界

sources/D5_D7_execution_adapter.diff保留D5到D7执行适配的机械差异。变化仅涉及新模型/控制来源、事件α、预登记种子和输出目录；执行机制保留。run_d7.py在首次优化前增加跨预算CSV加载，避免日志被覆盖。原始运行脚本与源码完整快照随包保留，未修改历史D5文件。
