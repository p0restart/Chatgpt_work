from pathlib import Path
import re,json,shutil,hashlib,zipfile
R=Path(__file__).resolve().parent
T=R/'latex'
scripts=T/'scripts';scripts.mkdir(exist_ok=True)
script=(R/'build_figures.py').read_text(encoding='utf-8')
script=script.replace('R=Path(__file__).resolve().parent\nDATA=R/\'latex/data\';OUT=R/\'latex/figures\'','R=Path(__file__).resolve().parents[1]\nDATA=R/\'data\';OUT=R/\'figures\'')
start=script.index('SKILL=')
end=script.index('FONT=',start)
helper='''def require_matplotlib_panel_alignment(fig,json_out,strict=True):
    """Check equal plot sizes and shared edges for each comparable grid row."""
    fig.canvas.draw()
    axes=[ax for ax in fig.axes if ax.get_subplotspec() is not None]
    rows={}
    for ax in axes:
        spec=ax.get_subplotspec()
        rows.setdefault((spec.rowspan.start,spec.rowspan.stop),[]).append(ax)
    checks=[]
    for group in rows.values():
        if len(group)<2: continue
        boxes=[ax.get_position() for ax in group]
        for prop,scale in [('width',fig.get_figwidth()*72),('height',fig.get_figheight()*72),('y0',fig.get_figheight()*72)]:
            spread=(max(getattr(b,prop) for b in boxes)-min(getattr(b,prop) for b in boxes))*scale
            checks.append({'quantity':prop,'spread_pt':spread})
            assert spread<=1.5
    Path(json_out).write_text(json.dumps({'passed':True,'checks':checks},indent=2))
'''
script=script[:start]+helper+script[end:]
(scripts/'rebuild_figures.py').write_text(script,encoding='utf-8')
readme='''English conference manuscript revised 20 November 2026

Files
  main.tex and IEEEtran.cls: revised editable LaTeX manuscript and retained class.
  main.pdf: compiled 8-page preview with author placeholders.
  Network_Defense_Revised.docx: synchronized editable Word manuscript, 7 pages in Word.
  figures/: vector PDF/SVG figures and 600-dpi PNG versions for Word.
  data/: frozen controls, saved states, original diagnostic records and environment.
  scripts/rebuild_figures.py: redraws the figures from the included saved data.

Compile
  Recommended with Times New Roman installed:
    xelatex -interaction=nonstopmode main.tex
    xelatex -interaction=nonstopmode main.tex
  Tectonic is also supported:
    tectonic main.tex
  pdfLaTeX uses Times-compatible newtx text and math fonts:
    pdflatex -interaction=nonstopmode main.tex
    pdflatex -interaction=nonstopmode main.tex
  Packages include newtxmath, cite, booktabs, tabularx, microtype and hyperref.
  No shell escape is needed.

Author information
  Replace the bracketed author, affiliation, location and email placeholders manually.
  The corresponding author is marked with an asterisk.
  After filling the author block, recompile and check pagination. The optional
  IEEEtriggeratref{19} balances the current final bibliography page; adjust or remove
  that line if the final author block changes reference pagination.

Rebuild figures
  Requires Python 3.11+, NumPy, Matplotlib, and Times New Roman installed.
    python scripts/rebuild_figures.py
  This redraws all four figures and checks comparable panel alignment.
  It does not re-optimize controls or rerun research experiments.
  The delivered figures additionally passed rendered-PDF text-size and collision
  checks, plus the complete manuscript was visually reviewed.

Remaining verification items
  1. Authors and affiliations are intentionally left for the author to complete.
  2. Reference [13] retains the supplied author list because its full official
     article metadata could not be recovered. Its journal name is corrected to
     Netinfo Security; no author or DOI was invented.
  3. Word retains native, editable Office equations. Its built-in mathematical
     glyphs still use Cambria Math. The older Word template requests Times New
     Roman/Symbol, while the checklist requires editable Office/MathType equations.
     Exact Word math-font compliance is therefore not claimed. If the organizer
     requires the older font restriction literally, confirmation or a MathType
     conversion is still needed. Equations were not flattened into pictures.

Reproducibility scope
  All 18 numbered model/equilibrium/action/deviation equations are unchanged.
  Model parameters, final controls, plotted trajectory samples and comparison
  values are unchanged. Additional diagnostic figures in the text are taken from
  existing archived runs. The package includes saved outputs for checking and
  redrawing; it is not a new standalone optimizer implementation.
'''
(T/'README_COMPILE.txt').write_text(readme,encoding='utf-8')
notes='''英文论文修订说明 2026年11月20日

交付：LaTeX编译PDF 8页；同步Word稿7页；作者信息按用户要求保留待手动填写。

已处理
1. 标题采用更自然的Resource-Constrained；统一累计综合防御损失的英文术语。
2. 修改摘要、局部表达及“时空可计算性”“投资收缩”等不自然用词；补API全称。
3. 明确共同攻击来自G对应的冻结攻击计划，比较结论限定主容量；保留期末M略优、部分资产曲线交叉等结果。
4. 从既有记录补入随机种子、历史运行版本、停止指标定义和实际数值诊断；未新建理论或实验结果。
5. 补全文献[1][7][9][10][16]作者；使用[6]官网英文题名；将[13]刊名改为Netinfo Security；给[21]补可访问来源页。
6. 四图重绘为Times New Roman，主体标签8pt；图2–4跨栏显示，提供PDF/SVG和600dpi PNG。保留全部6资产、8条边、72个防御控制分量及每方案289个状态采样点。
7. 修复源码原有Figure题注双句点、上标引用缺方括号及Index Terms与清单Keywords不一致的问题。
8. Word参数表和算法记号改为可编辑Office数学对象；统一下标、作者区字号、段间距，算法左对齐，消除表3数字拆行和跨栏图前的段尾异常拉伸。
9. 表2增加总计按未舍入值计算的说明。LaTeX末页分栏整理，避免参考文献条目跨页拆开。

验收依据
LaTeX成功编译，无未定义引用、未定义文献或Overfull提示。4图渲染字号与文字碰撞检查均通过，图2–4对应面板对齐检查通过；两版逐页视觉检查。18个编号公式与原LaTeX源码逐块一致；主要原始参数、控制及效果表数值保持不变。原始论文、原始压缩包和研究结果未覆盖。

仍保留的事项
作者信息：由用户手动补充。
文献[13]：完整官方作者表及正式英文题名仍未取得，保留原供稿内容，不猜填。
Word数学字体：保留原生可编辑公式，Word内部仍采用Cambria Math数学字形；旧Word样稿的Times New Roman/Symbol要求尚不能声明已完全满足。若严格执行这一限制，仍需组委会确认或MathType转换。未将公式改成图片。LaTeX采用Times正文和newtx数学排版。

填写作者后应再次检查分页。此包是已修订的可审阅稿，不表示已投稿或获得任何新增研究关卡批准。
'''
(T/'修订说明.txt').write_text(notes,encoding='utf-8')
shutil.copyfile(R/'Network_Defense_Revised.docx',T/'Network_Defense_Revised.docx')
shutil.copyfile(T/'main.pdf',R/'Network_Defense_Revised.pdf')
audit=json.loads((R/'qa/figure_audit_summary.json').read_text())
summary={n:{'text_size_passed':v['text_code']==0,'collision_passed':v['collision_code']==0} for n,v in audit.items()}
(T/'figure_checks.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
manifest={str(p.relative_to(T)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in T.rglob('*') if p.is_file() and p.suffix not in ['.log','.aux','.out'] and p.name!='sha256_manifest.json'}
(T/'sha256_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
archive=R/'Network_Defense_Revised_Source.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(T.rglob('*')):
  if p.is_file() and p.suffix not in ['.log','.aux','.out']:
   z.write(p,str(p.relative_to(T)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print('Packaged',archive.name,archive.stat().st_size,'bytes')
