# P0-1 数值求解与验证报告

日期为2026-11-11（Asia/Shanghai）。运行状态COMPLETED；阶段状态WAITING_USER_G_D4_P0_1_REVIEW。数值通过与用户审核是不同状态。

## 覆盖与来源

预登记36格，实际完成36格，通过36格，未运行0格。所有FIXED为新求解，每格3个H12初值路径及其3个H48精化路径；GAME保留历史完整控制，主评价统一H48，另保留H96/H192整套复核。12起点加12稀疏通道粗审计、3起点细审计只检查防御。没有攻击最佳响应或攻击Nash诊断。

共1296次SLSQP调用，失败0次。全部原始退出码、初值、返回控制、迭代数及残差见optimizer_attempts.csv与原始trace/audit JSON。本轮未重随机种子、未挑选最优路径、未变宽门槛。

|指标|实测最大值|预登记门槛|
|---|---:|---:|
|归一化已发现防御改善|8.77585e-12|1e−7|
|当前候选投影残差|9.24126e-06|1e−4|
|响应计划距离|4.88647e-06|1e−3|
|H12三初值控制差|5.96357e-06|1e−3|
|H48三初值控制差|5.96357e-06|1e−3|
|H12/H48主路径控制差|0|1e−3|
|控制违反|9.76996e-15|1e−10|
|固定计划积分误差（目标/分项/全状态最大）|9.48971e-09|1e−6|
|独立DOP853与H192最大差|1.8492e-12|1e−6|
|GAME相对原C1 H48目标差|0|1e−10|

独立表达的DOP853对GAME/FIXED/CROSS逐格核验，与主代码不共用dynamics/cost_rates函数，但同一执行者及同一机器，不宣称独立团队或独立优化实现。接口自检三个中心差分方向导数误差最高5.15e−9，均通过1e−5门槛。既有53项测试先行通过，源文件指纹随后保持相同，不将其计为本次研究实验。

## 复算审计

后处理重新从序列化控制重积分全部三种主评价，重算当前防御残差并从原始目标JSON独立计算四格差、C格归一化和交叉分解。验证状态PASS，1673项检查；主计划重评价最大差0，交互表差0，成本交互合计差3.16414e-15。检查数不是独立实验数。

A/B交换对称性在两环境实测，GAME目标最大误差7.32037e-12，FIXED为8.88178e-15；完整控制和状态交换差见symmetry_checks.csv。对称性只适用于A/B，不强加于C/D。

377个原稿/源码/历史输入文件在运行前后指纹保持不变，改变列表为[]。全部时间段、30分钟组边界停止与恢复（如有）见metadata.json，不把暂停记为数值失败。

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
