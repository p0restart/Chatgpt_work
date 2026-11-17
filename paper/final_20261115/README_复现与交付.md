# 最终合稿交付与复现

本目录交付《基于非零和微分博弈的有限资源网络防御决策方法》中文五章合稿。正文为Markdown、含原生可编辑公式的Word及Word实际导出的PDF。主文四幅图、附录四幅图，全部提供PNG/PDF/SVG。没有新增策略优化或修改原实验参数。

阅读顺序：`论文终稿_中文.pdf` → `最终验收报告.md` → `01_数学与实验审计报告.md`。逐章Markdown在`chapters/`，第三章允许的全部变动见`chapter3_changes.diff`和`chapter3_mechanical_changes.json`。

## 数值复现

使用Python 3.11和requirements中的科学计算包。在独立复制或解压的本目录中执行：

```powershell
python reproduce.py
python assemble.py
python audit.py
```

第一条从`raw_d7/`中的冻结源码、模型及完整控制重新积分，复算18个静态防御—公共攻击组合、24条滚动执行轨迹，输出状态长表、成本、530项检查及图件。它不会调用策略优化器。第二条从交接章节和复算表合稿；第三条独立从原始CSV/JSON校验论文表格、引用、公式号和第三章变化。原始优化轨迹、退出码、多初值、种子与预算记录保留在`raw_d7/results/`。

主图数据为`results/gf_state_common_aG.csv`，固定攻击复核为`gf_state_common_a0.csv`；每个场景每方案1153点，字段含`scenario,plan,time,x1,…,x6,xq`及累计成本。状态由完整控制重新积分得到，没有从损失反推。原始控制、模型及来源校验码见`raw_manifest.json`。

绘图使用Python/Matplotlib。当前Windows主机采用Microsoft YaHei显示中文；其他主机需提供兼容中文字体。PNG为400 dpi，PDF/SVG为矢量。图内xq的数学定义见正文式（10）。DOP853内部步长自适应；192是每区间等距输出间隔数。RK4 H=48/96/192则表示实际积分子步数。

## 图形审计

多面板对齐报告已保存在`figures/qa/`。以下为逐PDF检查示例，其余图依次替换文件名：

```powershell
python raw_d7/analysis/figure_qa/audit_figure_collisions.py figures/fig4_3_GF_state_common_aG.pdf --json-out figures/qa/recheck.collision.json
python raw_d7/analysis/figure_qa/audit_pdf_text.py figures/fig4_3_GF_state_common_aG.pdf --json
```

8幅最终图的碰撞与字形尺寸审计均通过；最低有效字号7 pt。拓扑图来自D7原图，已在包内冻结，不依赖原项目外部路径。其节点色块内文字属于有意包含关系，无警告性遮挡。

## Word与PDF

Word公式采用原生OMML，计231处数学对象。`export_docx.py`使用配套latex2mathml及本机Office的MML2OMML转换表；`render_word.ps1`在后台用本机Word导出PDF。`render_pdf_qa.py`将实际PDF转为页面图以复核。导出依赖Windows/Office，不冒称跨平台排版已验证；数值复算不依赖Office。

```powershell
python export_docx.py
./render_word.ps1
python render_pdf_qa.py
```

若使用项目中已有PyMuPDF目录，可给最后一条增加`--pymupdf-path <目录>`。自动渲染器因本机缺少LibreOffice失败后，已改用Microsoft Word成功导出并检查16页。未安装LibreOffice不影响本次已交付PDF；后续改稿需再次执行真实渲染核验。

## 验收边界

交付包不附第三方论文全文或其完整文本提取。审稿时读取的原件仍在原研究项目中保留；文献审计提供出版链接、访问层级和原始来源清单。冻结审稿意见中的相应历史证据路径属于当时的审阅材料，不是数值复算依赖。

已完成内容合稿、固定控制复算、图表和同一机器隔离目录复现。3份报告来自彼此隔离的模拟审稿上下文，没有外部专家身份或录用保证。具体会议、页数上限、作者信息和投稿模板尚未提供，当前为单栏审阅版；本交付不表示已经投稿或获得新的G2结果审批。
