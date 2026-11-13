# Work D3 交接

日期：2026-11-11（Asia/Shanghai）。**G-D2已按用户明确授权登记APPROVED；D3通用稿工作完成，状态READY_FOR_AUTHOR_REVIEW / TEMPLATE_PENDING。** 这不表示具体会议套版、最终投稿PDF或实际投稿已完成，也不自动登记新的人工批准。

## 审阅入口

|交付|文件|
|---|---|
|压缩后的完整中文主文|[manuscript_zh.md](manuscript_zh.md)|
|中英文摘要与题名|[01_abstracts.md](01_abstracts.md)|
|结论|[02_conclusion_zh.md](02_conclusion_zh.md)|
|全量原值、配置解释与复现细节|[supplement_zh.md](supplement_zh.md)|
|统一引用库及访问范围|[references.bib](references.bib)、[citation_audit.md](citation_audit.md)|
|压缩规模及证据去向|[compression_audit.md](compression_audit.md)|
|投稿格式审查与尚待输入|[submission_format_audit.md](submission_format_audit.md)|
|主张对照与作者侧审查|[claim_evidence_map.md](claim_evidence_map.md)、[D3_review.md](D3_review.md)|
|轻量审阅包|[Work_D3_review_light.zip](review_package/Work_D3_review_light.zip)|

## 已完成范围

摘要364汉字、英文摘要218个空白分隔词，结论386汉字。对相同原有第1–5节，Unicode汉字数从12,260减为5,694，减少53.6%；新摘要与结论另计，不把汉字压缩率当页数承诺。

保留20组原公式、3主图、4主表。全量36目标、九组差值与精确参数移补充；固定评价反向结果、原图负反例、控制异质性与六槽跨类偏离留在主文。两项研究贡献保持不变，局部候选不升格为连续全局Nash。

85项文档及保存数据检查通过，原D1/D2源稿、源码、模型、图表与实验数据保持D3起始版本。五个D1历史哈希差异已解释为换行/表格格式，不假报逐字节一致。未运行新实验、优化、积分、研究测试或新独立审稿。

## 下一项依赖

需确定目标会议及官方模板，才能完成最终页数实测、引用样式适配、图表实际尺寸检查、作者/匿名字段、提交附件路径及最终PDF逐页验收。当前先交付可审阅中文通用稿，不假定任何出版社模板，不声称已可直接提交。

G-D2授权原文与版本边界见[正式批复登记](../../reviews/G_D2_decision.md)。既有D1/D2文件中的等待表述作为历史保留，最新状态以该记录及项目状态日志为准。

## 复核

项目根目录执行：

```powershell
python paper/work_d3/analysis/verify_d3.py
```

输出analysis/verification.json及compression_audit.md，只消费现有文字和保存数据。analysis/input_manifest.json保存输入指纹，analysis/delivery_manifest.json保存交付指纹；轻量包不含原始results大目录与依赖环境，不是独立实验重跑包。
