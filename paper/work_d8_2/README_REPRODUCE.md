# D8-2 读取与复现

从D8_2_experiment_report.md开始阅读。所要求的全部表格在本目录根；完整优化调用、路径、状态、预测与执行证据分别在results/K12和results/R_LAG。数值最大值及位置见results/numerical_quality_maxima.csv，作者侧独立固定控制积分审计见results/independent_fixed_control_audit.csv。结果不代表人工批准。

## 已实际执行的命令

在项目根目录依次执行：

```powershell
python paper/work_d8_2/analysis/run_d8_2.py register
python paper/work_d8_2/analysis/run_d8_2.py preflight
python -u paper/work_d8_2/analysis/run_d8_2.py A
python paper/work_d8_2/analysis/run_d8_2.py compare
python -u paper/work_d8_2/analysis/run_d8_2.py B
python paper/work_d8_2/analysis/audit_d8_2.py
python paper/work_d8_2/analysis/plot_d8_2.py
python paper/work_d8_2/analysis/check_figures.py
python paper/work_d8_2/analysis/build_report.py
```

首次A启动因输出父目录未创建在优化前失败，修复mkdir(parents=True)后公开说明并重复启动；没有数值结果被丢弃。后处理因补充来源、排名容差和图件检查而重复执行，不是重新优化。正式A/B优化各执行一次。来源清单对应登记时读取的原件，授权日志随后只追加本轮范围授权。

## 在独立新目录重优化

现有结果不可覆盖。下列示例设置输出目录后，重复上面的register至B及audit命令；若目录已存在则换一个新目录，不删除或覆盖旧结果。

```powershell
$env:D8_2_OUTPUT = Join-Path (Get-Location) 'paper/work_d8_2_reproduction01'
python paper/work_d8_2/analysis/run_d8_2.py register
python paper/work_d8_2/analysis/run_d8_2.py preflight
python -u paper/work_d8_2/analysis/run_d8_2.py A
python paper/work_d8_2/analysis/run_d8_2.py compare
python -u paper/work_d8_2/analysis/run_d8_2.py B
python paper/work_d8_2/analysis/audit_d8_2.py
Remove-Item Env:D8_2_OUTPUT
```

此处提供复现命令，不表示本轮已再次运行该重优化。可将本轮预注册与指令副本一并复制到新目录用于审计；必须保留D7原始数据相对路径。register在新目录保存本次实际来源哈希；审计工具验证当次来源不被修改。不同环境的SLSQP浮点路径可能有微小差异，应比较登记门槛、控制差、目标及符号，不能只逐字比较运行时间。

## 运行环境与依赖

本轮Python 3.11.7、NumPy 1.26.4、SciPy 1.11.4，本机Windows；完整版本在source_and_config_manifest.json。核心依赖沿用项目requirements.txt。科学数值计算没有换NumPy版本；PDF图件检查子进程单独引用项目已有的.figure-deps。

图件使用Python/Matplotlib；绘图和版式检查辅助程序已留存于sources/figure_qa_tools，代码使用这些随包副本。自动检查不替代目视检查，最终记录在figures/qa/visual_review.md。不需联网、外部模型或新文献访问。

## 文件完整性

SHA256SUMS列出所有交付有效文件及data_manifest.csv的SHA256；自身不可能包含自身哈希。__pycache__和临时文件不作交付，实际优化JSONL和所有状态/控制/模型文件均包含。报告中的源文件路径相对项目根，原始来源清单在source_and_config_manifest.json。打包仅本轮独立目录，不复制整个历史项目；复现仍需项目源码及D7原始结果。

最终交付检查：

```powershell
python paper/work_d8_2/analysis/finalize_delivery.py --verify-only
```

该命令只读校验已保存哈希、文件、数值状态及最终图件审计绑定，不调用优化器。
