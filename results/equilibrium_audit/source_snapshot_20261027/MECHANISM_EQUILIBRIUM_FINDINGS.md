# 核心机制与均衡诊断结果（2026-10-27）

本轮回答用户“做过什么、具体验证什么”，并加强原范围内4个配置的求解诊断。不是G2批准，不是全局Nash证书。

## 一、纠正旧结果的解释
原81个交替任务中79仅更新一轮，另2个两轮；79个防御相对固定攻击解变化<1e-6。旧1%工程门槛允许过早停止，因此原27配置比较不支持充分双边适应或均衡机制叙述。原报告、成本和反例不覆盖，当前解释由本报告补充。

## 二、严格局部求解实际完成情况
4配置×3初始策略（旧候选/全零/随机）=12次求解，全部达到登记门槛：相对观测改善≤1e-7、当前策略投影残差≤1e-4、响应控制距离≤1e-3。实际3–10轮。迭代使用不阻尼更新，仅为诊断设置；模型/图/参数未改。

|已批准配置|三初值终点控制最大差|旧候选强化搜索的最大相对改善|新候选强化搜索的最大相对改善|
|---|---:|---:|---:|
|seed11/separated/B1.2|3.37e-5|4.35e-5|1.22e-10|
|seed22/separated/B1.2|2.50e-5|1.08e-3|2.04e-10|
|seed33/separated/B1.2|6.22e-5|1.33e-3|2.24e-10|
|seed33/business_cost/B0.6|2.24e-5|4.80e-5|5.13e-11|

表中为比例不是百分数。强化搜索：每方12起点（当前、零、10随机）加每通道集中投入初值；旧/新候选共304次局部优化，全部返回成功，最大违规1.03e-14。48子步重新响应的最大相对改善约2.24e-10；源文件见results/equilibrium_audit/run01各case_audit.json、new_strong_audit.json、fine_audit.json及summary.csv。

**支持的判断**：这4个配置存在多初始策略稳定、经过更强局部偏离搜索仍未被明显改进的K=6开环数值候选。旧停止精度确实需要加强。

**不支持的判断**：没有全域偏离上界，没有纯Nash存在/唯一证明，没有K精化或连续反馈结果。全部优化仍属于同类局部SLSQP搜索，多起点不变成全局证书；不能把1e-10当真实全局gap。其余23配置没有进行此次严格重算。

## 三、资源优先级不能由曲线大小替代
在新候选上计算每槽D目标梯度与边际安全收益，并检查高传播节点隔离和高价值节点恢复之间的可行微小容量转移。共38个方向检查，方向导数有限差分最大误差1.73e-5，小于登记1e-4。活动内部控制的每单位容量净边际收益最大差8.13e-5，符合局部驻点所要求的近似均衡边际收益，而非“投入更多者边际收益一定更高”。

边际表见各marginals.csv，资源转移见transfers.csv，逐槽汇总见slot_mechanism_audit.csv。所有核验均在既有策略附近，未改变图或参数。实际最后一槽并非所有案例隔离都为零；连续必要条件的末期零隔离区间不能直接映射为整个离散最后槽。

零终端损失和正隔离业务代价本身提供末期隔离衰减的替代解释，见RESEARCH_EXPLANATION.md。原“6/27优先级符号变化”只能叫控制水平交叉，不能据此宣布错位机制验证通过。

## 四、负增益反例的同精度检查
对seed33/business_cost/B0.6的Recovery-only同样加强求解并以48子步、12起点审计，最大相对观测改善1.33e-11。Joint目标12.4375182282，Recovery-only目标12.4368540435；联合仍高约0.00534046%。旧反例约0.010878%，加强求解后缩小但没有消失。

进一步交叉使用两套攻击与防御（均为严格局部候选），D成本如下：

|防御\攻击|Joint候选的攻击|Recovery-only候选的攻击|
|---|---:|---:|
|Joint防御|12.437518|12.434801|
|Recovery-only防御|12.439491|12.436854|

同一攻击下，Joint防御都更低；但各自攻击响应下，Joint的最终成本略高。以Recovery攻击为参照，Joint防御约减少0.002053成本，攻击改为Joint响应又增加约0.002717，净高约0.000664。由此可把这对候选的负差解释为攻击调整抵消直接防御收益；不是联合可行集比恢复可行集更小，也不是已经证明普适悖论。两套候选不是全局认证均衡。

数据：results/equilibrium_audit/counterexample01/comparison.json、cross_evaluation.csv、strong_fine_audit.json。另以Recovery防御作为Joint响应初值做了追加局部检查，原始退出记录保留。

## 五、核心机制仍缺的证据与下一步
目前对业务代价、容量绑定及攻击响应已有有界数值证据；但“价值—传播错位独立造成某种分配规律”仍受位置、入边和入口暴露混杂影响。加强局部求解不会自动消除这些混杂。

已准备G1-C1变更单及未执行配置：使用匹配的非入口节点2/3，匹配初始状态、入边和距离，保持总q和总传播权重，比较等/不等出强度×高价值位置的四格实验。此项新增传播图和配置，需用户明确批准后执行。见reviews/G1_C1_mechanism_identification.md。

## 复现命令
```powershell
python -m src.diagnose_equilibrium --output results/equilibrium_audit/new_run
python -m src.diagnose_counterexample --equilibrium-root results/equilibrium_audit/new_run --output results/equilibrium_audit/new_counterexample
python -m src.explain_counterexample --equilibrium-root results/equilibrium_audit/new_run --counterexample-root results/equilibrium_audit/new_counterexample
```
选择新目录复现，前两个脚本拒绝覆盖已有运行目录。原始命令与输出见logs/equilibrium_audit_run01.txt、equilibrium_counterexample01.txt、equilibrium_counterexample_cross.txt。

当前可作判断：数值候选可靠性显著加强；核心错位机制尚未完成识别；全局均衡仍未认证。三者分别报告，不合并成“研究已通过”。

汇总表可用 python -m src.summarize_equilibrium --root results/equilibrium_audit/run01 重建；verification.json保存机器可读诊断结论。
