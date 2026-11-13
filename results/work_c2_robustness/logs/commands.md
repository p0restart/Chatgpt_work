# 本轮实际执行命令

工作目录为项目根目录。2026-11-07开始核查，隔离求解在北京时间2026-11-08运行。

1. `Get-FileHash src/core.py,src/game_solver.py -Algorithm SHA256`；`git status --short`；`git rev-parse HEAD`。
2. `python -m venv results/work_c2_robustness/cross_environment/venv`。
3. `python -m pytest -q -p no:cacheprovider`，日志 `tests_current.txt`。
4. 新环境解释器执行 `-m pip install --disable-pip-version-check --timeout 15 --retries 0 numpy==1.26.4 scipy==1.11.4 pandas==2.1.4 PyYAML==6.0.1 matplotlib==3.8.2 networkx==3.2.1 pytest==8.3.5`，第一次失败，日志 `environment_install.txt`。
5. 上述安装加入 `--index-url https://pypi.org/simple`，受限网络下失败，日志 `environment_install_pypi.txt`；允许联网后相同命令成功，日志 `environment_install_network.txt`。不是实验求解失败或重新挑选结果。
6. `python -m handoffs.C2_prepare`，日志 `prepare.txt`。该命令拒绝覆盖检查点；如复核请先阅读源码，使用不同新输出目录，不能直接覆盖本次证据。
7. 新环境解释器 `-m pip freeze` 保存 `cross_environment/requirements-installed.txt`；记录 sys.prefix/base_prefix/path、模块版本与实际加载路径，保存 `cross_environment/environment.json` 和 `pyvenv.cfg`。
8. 新环境解释器 `-m pytest -q -p no:cacheprovider`，日志 `tests_isolated.txt`。
9. 新环境解释器 `-m src.matched_mechanism --pilot-only --output results/work_c2_robustness/cross_environment/run01`，日志 `cross_environment_run01.txt`。重现时必须换尚不存在的新输出目录。
10. `python -m handoffs.C2_compare`，仅在run01实际完成后执行；原始完整输出保留，分析写入tables和cross_environment/comparison.json。

新环境解释器完整相对路径：`results/work_c2_robustness/cross_environment/venv/Scripts/python.exe`。虚拟环境目录不作为可移植成果；以固定依赖文件、安装日志、源码快照和全量清单重建。

K=12没有运行命令：WAITING_USER_G1_WORK_C2。不得把上述历史K=6重新积分标为新博弈求解。
