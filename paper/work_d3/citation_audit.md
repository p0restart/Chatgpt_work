# D3 引用统一与核查报告

日期：2026-11-11（Asia/Shanghai）。采用按正文首次出现顺序的数字引用，当前统一为[1]—[5]；这是通用工作稿约定，具体会议样式未指定。正文、文末条目与本目录references.bib一一对应；不从旧paper/references.bib直接全量继承，以免漏掉Preciado/Botteghi、混入未引用条目或误用期刊版本。

## 条目与实际证据范围

|号／BibTeX键|核对依据|本轮访问层级与限制|处置|
|---|---|---|---|
|[1] Preciado2014Protection|[作者预印本记录](https://arxiv.org/abs/1309.6270)、[公开全文PDF](https://arxiv.org/pdf/1309.6270)；D1/Work C已有期刊元数据与方法核查|本轮读公开全文的摘要/方法相关文本，支持有向异质网络、预防与纠正资源及几何规划；IEEE DOI重定向遇机器人验证，未重开出版社全文|保留期刊条目2014, 1(1):99–108及原DOI；公开稿作为方法访问依据，不把2013预印本首发年替换为期刊年|
|[2] PaarpornXu2024|[作者主页](https://sites.google.com/site/kpaarporn/research)；literature/fulltext_audit/R3_extracted.txt，PDF页1–2及模型相关段|作者主页确认作者、题名、期刊与年份；本地原文提取确认页码起点2421、DOI与两阶段预防/恢复资源竞赛，相关正文明确零和；NSF公开稿本轮超时，IEEE入口不可读|保留两位作者全名、2024,8:2421–2426；不宣称本轮在线全文已读|
|[3] Tian2025|[出版社DOI入口及检索可读文章页](https://doi.org/10.1016/j.comcom.2025.108148)；literature/fulltext_audit/R1_extracted.txt|本轮出版社检索结果含作者、卷237、文章号108148及章节预览；本地提取中开环定义、Hamiltonian方法段支持引言所述。DOI直接打开失败与搜索可读分别记录|保留2025期刊条目；不继承原文未经本项目证明的均衡/算法结论|
|[4] Botteghi2026v2|[作者v2记录](https://arxiv.org/abs/2601.16805v2)、[v2全文](https://arxiv.org/html/2601.16805v2)|本轮读v2全文相关段；记录明确v2为2026-10-05，并链接Economic Modelling期刊DOI，但未核期刊版全文或实际在线日期|明确引用arXiv v2；作者Martino S. Centonze统一为Centonze M S，BibTeX保留S.；不混用期刊卷号及预印本版本|
|[5] Chen2025|literature/fulltext_audit/R4_extracted.txt，封面及模型引言相关段；[作者摘要与元数据的PubMed记录](https://pubmed.ncbi.nlm.nih.gov/41416673/)|本轮读取保存的原文提取，核对作者、题名、Chaos35、文章号123136与DOI；AIP入口失败，PubMed本轮为仅摘要/元数据，不能称在线全文访问|补齐统一条目中的期号(12)；技术判断依已有本地原文方法提取，不借摘要扩展精确结论|

引言只简述上述先例与本研究问题的关系，未添加首创、优先权或“尚无研究”结论。核查范围不是系统查新；没有重开三篇历史原PDF，也没有重新逐字校对所有公式。本地提取来源链见[原文来源清单](../../literature/fulltext_audit/source_manifest.json)和[D1证据登记](../work_d1/00_evidence_register.md)。本轮没有做完整撤稿/更正状态专项检索，不能据此签发文献“全量无问题”结论。

## 一致性修订

1. 五项引用在全文仅维护一份文末表，按首次出现顺序排列；参考文献列表不保留“已核全文”这样的内部审阅注记，实际访问范围放本报告。
2. 作者姓氏与首字母、期刊名称、卷(期)、页码/文章号、DOI链接形式统一。Botteghi保留预印本版本和修订日期，不填未经核验的期刊上线日期。
3. 旧paper/references.bib及handoffs/C_bibliography.bib保留原样，本目录五条库是D3稿件的直接配套库；并不宣称替换整个项目所有文献库。
4. 作者名单与单位尚未提供，无法做作者自引比例、利益冲突或作者贡献核查；没有虚构相应声明。

可复核检查：`python paper/work_d3/analysis/verify_d3.py`。该检查只验证本文已纳入的五项编号/键与链接结构、来源指纹和数学/数值一致性，不替代全文阅读或会议专用引用样式验收。
