# G1 最小实验复现说明

工作目录：本项目根目录。Python3.11+；实测版本在requirements-p2-observed.txt。新环境安装尚未验证；当前机器实际验证了以下命令。

```powershell
python -m pytest -q
python -m src.smoke --config configs/base.yaml
python -m src.p2_validate --config configs/p2.yaml --output results/p2/reproduce_new
```

输出目录必须尚不存在，避免覆盖先前失败或结果。最后一条与已执行run01/02/03命令仅输出目录不同。已有审计结果选用run03。程序返回非零时仍保留已写出的起点日志，不应删除目录重跑同名结果。原始6节点烟雾测试仅为随包预设控制仿真，不是G1前开展正式6节点实验。

配置阈值在首次P2运行前写入configs/p2.yaml：3起点（原始、全0、seed11可行随机），SLSQP最大300迭代、ftol=1e-10，约束≤1e-10、投影残差≤1e-4、多起点目标差≤1e-5、差分误差≤1e-6、12子步及以上相对48子步目标误差≤1e-6。三起点只是诊断范围，无全局性。

|文件|内容|
|---|---|
|summary.csv|双方各自固定对手响应、目标分项、状态界及残差|
|controls.csv / trajectories.csv|所有槽控制及RK4时间点状态|
|slot_budgets.csv|每槽容量用量与余量|
|solver_trace.csv / *_raw_solver.json|所有起点退出状态、评价次数、耗时、残差与控制|
|*_refined_solver.json|24子步热启动响应复查|
|rk4_refinement.csv / gradient_check.csv|步长与梯度差分核验|
|config.yaml / model.json / edges.csv|完整参数、精确网络、种子|
|metadata.json|版本、运行时间、源文件哈希、诊断结果|

结果含两个不同的固定对手问题，不得将D行策略与A行策略拼接成“均衡”。运行本命令不会执行P3、模型冻结或自动审批。

## P3/P4复现
命令见README_RUN.md与reviews/G2_submission.md。实际main01耗时1031.87秒；fair01含等待耗时710.07秒，两过程部分重叠，不能相加为纯计算用时。pilot01/pilot02重新优化结果一致；所有324条保存策略重积分最大差9.77e-15。全批次未独立重新优化复跑。
