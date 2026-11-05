# 运行说明（G1已批准，P3/P4完成，等待G2）

G1批准：2026-10-26，路线A及五项范围；G2尚未批准。数值结果为合成K槽开环局部响应，不是连续反馈Nash证明。

```powershell
python -m pytest -q
python -m src.experiments --config configs/base.yaml --output results/p3/new_pilot --pilot
python -m src.experiments --config configs/base.yaml --output results/p3/new_main
python -m src.fair_evaluation --source results/p3/new_main --output results/p3/new_fair
python -m src.audit_p3 --root results/p3/new_fair
python -m src.summarize_p3 --root results/p3/new_fair
```

每次选择新输出目录。main保存原交替候选；fair保留每种方法的最终防御并补齐完整攻击响应，主公平比较使用fair。fair可在main完成后执行，也可读取已完成的配置；最多等待/执行30分钟，超时保留部分结果。audit_p3的pilot复现默认检查同级pilot01/pilot02，其他实验位置请相应配置目录。所有历史结果保留，不覆盖P2。

实际数据：results/p3/main01、fair01；最小复现：pilot01、pilot02。参数、边表、原始优化初末控制及退出码、逐槽预算、轨迹、12/24/48积分细化均在各配置子目录。数值环境沿用requirements-p2-observed.txt，pytest版本差异保留。图表QA依赖独立于数值实验环境。


审查入口：reviews/G2_submission.md；图表检查：reports/P3_figure_QA.md。实际主批次约1032秒，派生评价含等待约710秒，两过程部分重叠。

```powershell
python -m src.plot_p3 --root results/p3/fair01 --output figures/reproduced_p3 --qa-scripts C:/Users/Jin/.codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure/scripts
```

绘图需要上述QA脚本路径；数值实验不依赖该技能目录。PDF碰撞检查专用依赖在.figure-deps，不能将该目录加入正式数值运行环境。历史测试和数据文件仍完整保留。
