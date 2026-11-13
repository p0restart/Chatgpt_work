"""Read-only research evidence checks plus D3 document QA and local reports."""
from pathlib import Path
import csv
import hashlib
import json
import re
import statistics
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'paper/work_d3'
HERE = OUT / 'analysis'

def read(p):
    return p.read_text(encoding='utf-8-sig')

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load_csv(name):
    with (ROOT / 'paper/work_d2/tables' / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

checks = []
def check(name, ok, detail=None):
    checks.append({'name': name, 'pass': bool(ok), 'detail': detail})

main = read(OUT / 'manuscript_zh.md')
supp = read(OUT / 'supplement_zh.md')
before = read(HERE / 'assembled_before.md')
expected = json.loads(read(HERE / 'input_manifest.json'))['files']
intentional = {'reviews/APPROVAL_LOG.md', 'DECISIONS.md', 'logs/STATUS.md'}
changed, same, permitted = [], 0, []
for name, sha in expected.items():
    p = ROOT / name
    if p.is_file() and digest(p) == sha:
        same += 1
    elif name in intentional:
        permitted.append(name)
    else:
        changed.append(name)
check('protected_input_bytes_unchanged_except_authorized_logs', not changed,
      {'matched': same, 'authorized_log_changes': permitted, 'unexpected': changed})

# The package bytes prove the old manifest; formatting-only drift is explicit.
historical = json.loads(read(ROOT / 'paper/work_d2/analysis/minimal_revision_version_manifest.json'))['files']
format_rows = []
with zipfile.ZipFile(ROOT / 'paper/work_d2/review_package/Work_D2_GD2_review_light.zip') as z:
    for name, sha in historical.items():
        if not name.startswith(('paper/work_d1/', 'paper/work_d2/')):
            continue
        p = ROOT / name
        if p.is_file() and digest(p) == sha:
            continue
        if name not in z.namelist():
            check('historical_drift_explained_' + name, False)
            continue
        old = z.read(name)
        a = old.decode('utf-8-sig').replace('\r\n', '\n')
        b = read(p)
        exact_text = a == b
        def canonical_markdown(text):
            lines = []
            for line in text.splitlines():
                compact = re.sub(r'\s+', '', line)
                if re.fullmatch(r'\|(?:[:-]+\|)+', compact):
                    compact = '|'.join('---' if part else '' for part in compact.split('|'))
                lines.append(compact)
            return ''.join(lines)
        whitespace_only = canonical_markdown(a) == canonical_markdown(b)
        row = {'file': name, 'package_hash_valid': hashlib.sha256(old).hexdigest() == sha,
               'text_equal_after_newlines': exact_text, 'whitespace_only': whitespace_only}
        format_rows.append(row)
        check('historical_drift_explained_' + name, row['package_hash_valid'] and whitespace_only, row)

def eqs(t):
    result = []
    for block in re.findall(r'\\\[.*?\\\]', t, re.S):
        m = re.search(r'\\tag\{(\d+)\}', block)
        if m:
            result.append((int(m.group(1)), block))
    return result

original = dict(eqs(before))
actual = eqs(main)
check('twenty_unique_equations_in_original_order', [n for n, _ in actual] == list(range(1, 21)))
for n, block in actual:
    check(f'equation_{n}_exact_text', original.get(n) == block)
check('no_unfilled_build_tokens', '@@' not in main and '@@' not in supp)
check('balanced_display_math', main.count(r'\[') == main.count(r'\]'))
check('balanced_inline_math', main.count(r'\(') == main.count(r'\)'))
check('six_main_sections', re.findall(r'^# ([1-6]) ', main, re.M) == list('123456'))
check('three_main_figures', re.findall(r'!\[图([1-3]) ', main) == list('123'))
check('four_main_tables', re.findall(r'^\*\*表([1-4]) ', main, re.M) == list('1234'))
check('supplement_figure_S1_present', 'figS01_seed33_state_allocation.png' in supp)

broken = []
local_count = 0
for p in OUT.glob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)', read(p)):
        if re.match(r'^(https?://|#|mailto:)', target):
            continue
        local_count += 1
        dest = target.split('#')[0].strip('<>')
        if not (p.parent / dest).exists():
            broken.append({'file': p.name, 'link': target})
check('all_local_artifact_links_resolve', not broken, {'count': local_count, 'broken': broken})

body, refs = main.split('## 参考文献', 1)
citations = [int(x) for x in re.findall(r'(?<!!)\[(\d+)\](?!\()', body)]
reference_numbers = [int(x) for x in re.findall(r'^\[(\d+)\] ', refs, re.M)]
check('five_references_without_orphans', sorted(set(citations)) == reference_numbers == list(range(1, 6)))
check('citation_first_use_order', list(dict.fromkeys(citations)) == list(range(1, 6)))
bib = read(OUT / 'references.bib')
keys = re.findall(r'^@\w+\{([^,]+),', bib, re.M)
check('five_unique_bibtex_keys', len(keys) == len(set(keys)) == 5, keys)
check('preprint_version_not_mixed_with_journal', 'version={2}' in bib and '107854' not in bib)
check('no_invented_author_placeholders', not re.search(r'作者姓名|单位名称|TODO|待填作者', main))

cells = load_csv('matched_four_cells.csv')
errs = []
interactions = []
percent = []
for r in cells:
    calc = (float(r['J_D'])-float(r['J_C']))-(float(r['J_B'])-float(r['J_A']))
    errs.append(abs(calc-float(r['interaction'])))
    interactions.append(calc)
    percent.append(100*calc/float(r['J_C']))
check('nine_interactions_recomputed_from_36_objectives', len(cells) == 9 and max(errs) < 1e-12 and min(interactions) > 0,
      {'max_arithmetic_difference': max(errs), 'interaction_range': [min(interactions), max(interactions)],
       'C_normalized_percent_range': [min(percent), max(percent)]})
check('main_abstract_interaction_range_rounding', f'{min(interactions):.6f}' in main and f'{max(interactions):.6f}' in main)
check('main_abstract_normalized_range_rounding', f'{min(percent):.3f}%—{max(percent):.3f}%' in main)

pairs = [r for r in load_csv('baseline_pairs.csv') if r['namespace'] == 'matched_D']
stats_rows = load_csv('baseline_statistics.csv')
stats = []
for e in ['adaptive_attack', 'common_fixed_attack']:
    for m in ['Recovery-only', 'Joint-static', 'Fixed-trained']:
        rr = [r for r in pairs if r['evaluation'] == e and r['baseline'] == m]
        vals = [100*(float(r['baseline_cost'])-float(r['joint']))/float(r['baseline_cost']) for r in rr]
        errors = [abs(v-float(r['reduction_percent'])) for v, r in zip(vals, rr)]
        calculated = [min(vals), statistics.median(vals), max(vals)]
        stored = next(r for r in stats_rows if r['evaluation'] == e and r['baseline'] == m)
        check('baseline_' + e + '_' + m,
              len(vals) == 9 and max(errors) < 1e-10 and all(abs(a-float(stored[k])) < 1e-10 for a,k in zip(calculated,['min','median','max'])),
              {'range_median': calculated, 'positive': sum(v>0 for v in vals), 'count': len(vals)})
        stats.append({'evaluation': e, 'method': m, 'min': min(vals), 'median': statistics.median(vals), 'max': max(vals)})
        # Compare every visible six-decimal table entry without relying on source prose.
        for value in calculated:
            shown = f'{value:.6f}'.replace('-', '−')
            check('table3_number_' + e + '_' + m + '_' + shown, shown in main, shown)

counter = json.loads(read(ROOT / 'results/equilibrium_audit/counterexample01/comparison.json'))
counter_pct = 100*(counter['recovery_J_D']-counter['joint_J_D'])/counter['recovery_J_D']
check('original_negative_case_preserved', counter_pct < 0 and abs(counter_pct-counter['joint_reduction_pct']) < 1e-12
      and '−0.005340456%' in main and repr(counter['joint_J_D']) in main and repr(counter['recovery_J_D']) in main,
      {'recomputed_percent': counter_pct})
robust = load_csv('robust_interactions.csv')
for r in robust:
    check('two_group_refinement_' + r['seed'], float(r['I6']) > 0 and float(r['I12']) > 0 and
          f"{float(r['I6']):.10f}→{float(r['I12']):.10f}" in main)
cross = load_csv('robust_cross_class.csv')
for player in ['D', 'A']:
    vals = [100*float(r['relative']) for r in cross if r['player'] == player]
    check('cross_class_deviation_' + player, len(vals) == 8 and min(vals) > 0,
          {'percent_min': min(vals), 'percent_max': max(vals)})

main_required = ['公共固定攻击', '九项均不占优', '原网络', '−0.005340456%', '跨类偏离',
                 '0.063305—0.064929', '0.082446—0.084091', '同Windows主机', 'run01失败',
                 '局部', '不证明连续开环Nash', '60/72、40/72、1/72']
for phrase in main_required:
    check('conclusion_changing_evidence_' + phrase, phrase in main)

def cjk(t):
    return len(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff]', t))

def sections(t):
    return {m.group(1):m.group(0) for m in re.finditer(r'^# ([1-6]) .*?(?=^# [1-6] |^## 参考文献|\Z)', t, re.M|re.S)}

old_sections, new_sections = sections(before), sections(main)
counts = []
for n in '12345':
    a,b = cjk(old_sections[n]), cjk(new_sections[n])
    counts.append({'section': n, 'before': a, 'after': b, 'reduction_percent':100*(a-b)/a})
old_total = sum(x['before'] for x in counts)
new_total = sum(x['after'] for x in counts)
check('main_sections_1_to_5_compressed', new_total < old_total,
      {'before_cjk':old_total,'after_cjk':new_total,'reduction_percent':100*(old_total-new_total)/old_total})
abstract = body.split('## 摘要\n\n')[1].split('\n\n**关键词')[0]
abstract_en = read(OUT / '01_abstracts.md').split('## Abstract\n\n')[1].split('\n\n**Keywords')[0]
count_table = '\n'.join(f"|{x['section']}|{x['before']}|{x['after']}|{x['reduction_percent']:.1f}%|" for x in counts)
compression = f'''# D3 篇幅压缩与证据分配

口径：Unicode汉字数，含小节标题、表注及表格中文，排除文末参考文献；英文、数字与公式字符不计为汉字。对照为D3启动时D1第1–3节与D2第4–5节的直接拼接，保存于analysis/assembled_before.md。这个口径只衡量中文叙述规模，不是会议页数或英文词数。

|节|合稿前汉字数|D3汉字数|减少比例|
|---|---:|---:|---:|
{count_table}
|第1–5节合计|{old_total}|{new_total}|{100*(old_total-new_total)/old_total:.1f}%|

新增中文摘要{cjk(abstract)}汉字，结论{cjk(new_sections['6'])}汉字；英文摘要{len(abstract_en.split())}个空白分隔词（含数字及连字符词，非会议计数规则）。新增内容不混入上表既有五节压缩比例。主文式(1)–(20)全部保留原公式，3主图、4主表；正文缩短不能等同已达某个页数限制。

## 证据分配与重复处理

|内容及功能|主文保留|补充/来源去向|
|---|---|---|
|核心发现：价值位置×传播条件|九组交互方向、绝对范围、相对C格损失量级，图2原值尺度和交互|补充S1保留36目标及九组原值/差值表、全部精确上游边权|
|必要支撑：行动作用与计算对象|双方策略、动力学/目标、式1–20、局部求解和诊断性质|补充S3保留完整算法1、随机种子、历史流程差异与重现命令|
|异质性与机制限制|低容量近零隔离、前/末段反向、中容量种子差异、高容量松弛、图3|补充S2保留逐节点投入、末态、成本分解，图S1补充中容量例|
|协议内收益及改变结论的负证据|表3六行；Fixed-trained小正收益/固定评价全反向；原图负反例及交叉攻击数值|完整八方法原始目标与140配对仍在D2源表；不改历史数值|
|稳健性与适用范围|仅两组K比较、控制大分量变化、嵌入六槽的偏离、同主机复现、历史失败|补充S4保留完整精化、残差、路径、绑定比例及有限菜单范围|
|归档与工程来源|正文使用补充S1–S4指针|补充S5及D2源索引保留全量文件定位和旧审查；D1/D2原稿保持原样|

主文删减的主要是参数/符号重复解释、实现防护细节、全量原值表和重复的局部性质说明；没有删去会改变结论的负结果。摘要概括问题与关键边界，结论回答研究问题，不再逐图复述。主文仍保留20组公式以优先确保本轮数学接口稳定；实际会议很短时可能需要进一步迁移辅助推导，而不是缩小字号凑页数。

## 版本差异说明

D2最小修订清单中的5个D1文件与D3起始字节不同，压缩包内历史版本的哈希仍与清单匹配。其中贡献、引言、模型、求解4文件仅换行不同，提纲另有Markdown表格空格及分隔线长度变化。按换行、空白和表格分隔线规范化后5文件全部一致；无文字、数字、公式或结论变化。详见analysis/version_comparison.json、analysis/version_differences.diff和analysis/verification.json。D3记录实际起始哈希，不把上述差异误称为历史清单逐字节一致，也不回写D1源稿。
'''
(OUT / 'compression_audit.md').write_text(compression, encoding='utf-8')

report = {'date':'2026-11-11','timezone':'Asia/Shanghai',
          'scope':'document consistency and saved-data arithmetic; no solver, integration, tests or figure regeneration',
          'check_count':len(checks),'failures':[x for x in checks if not x['pass']],
          'checks':checks,'historical_formatting_differences':format_rows,
          'counts':{'sections_1_to_5_before_cjk':old_total,'sections_1_to_5_after_cjk':new_total,
                    'reduction_percent':100*(old_total-new_total)/old_total,
                    'abstract_cjk':cjk(abstract),'conclusion_cjk':cjk(new_sections['6']),
                    'english_abstract_space_words':len(abstract_en.split())}}
(HERE / 'version_comparison.json').write_text(json.dumps(format_rows,ensure_ascii=False,indent=2),encoding='utf-8')
(HERE / 'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(checks),'failed':report['failures'],'counts':report['counts']},ensure_ascii=False))
raise SystemExit(1 if report['failures'] else 0)
