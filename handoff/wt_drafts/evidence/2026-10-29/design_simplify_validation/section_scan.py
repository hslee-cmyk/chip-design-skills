# design 40·41 절별 분량과 과잉 단서 낱말 수(독립 측정, design/v115 fc874bd6 작업 트리 읽기만)
# 결과: section_scan.out.md (절별 표), section_scan.out.jsonl
import re, json, sys
D = r'C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/'
FILES = {'40': D + 'gain-budget-gmid-sizing.40-engine.design.md',
         '41': D + 'gain-budget-gmid-sizing.41-gain-budget.design.md'}
CUES = {
    'precise': r'정확',
    'ngspice': r'ngspice',
    'spice_same': r'SPICE와 같',
    'measured': r'실측',
    'version': r'\(v1\.\d|판\(v1\.|v1\.\d+(\.\d+)?의 |v1\.\d+(\.\d+)? --',
    'history': r'경위',
    'verifN': r'검증 \d|검증 [A-Z]-?\d|재판정|재검증',
    'original': r'원래 취지',
    'asbuilt': r'as-built',
    'richardson': r'Richardson',
    'sweep': r'훑기',
    'pts': r'점 중',
    'uV': r'µV',
    'pct': r'\d %',
    'commit': r'`[0-9a-f]{8}`',
    'evid': r'wt/_drafts/evidence',
    'old': r'옛 ',
    'retract': r'철회|대체됨|정정',
}
res = []
for k, fn in FILES.items():
    txt = open(fn, encoding='utf-8').read()
    lines = txt.split('\n')
    # section boundaries: markdown headings
    secs = []
    cur = {'doc': k, 'start': 1, 'title': '(머리)'}
    for i, l in enumerate(lines, 1):
        if re.match(r'^#{1,4} ', l):
            cur['end'] = i - 1
            secs.append(cur)
            cur = {'doc': k, 'start': i, 'title': l.strip()[:80]}
    cur['end'] = len(lines)
    secs.append(cur)
    for s in secs:
        body = '\n'.join(lines[s['start'] - 1:s['end']])
        s['bytes'] = len(body.encode('utf-8'))
        s['lines'] = s['end'] - s['start'] + 1
        for c, pat in CUES.items():
            s[c] = len(re.findall(pat, body))
        res.append(s)
with open('section_scan.out.jsonl', 'w', encoding='utf-8') as f:
    for s in res:
        f.write(json.dumps(s, ensure_ascii=False) + '\n')
cols = list(CUES)
out = ['# 절별 분량·단서 수 (design/v115 fc874bd6)', '',
       '| 문서 | 줄 | 절 | KB | ' + ' | '.join(cols) + ' |',
       '|' + '---|' * (4 + len(cols))]
for s in res:
    out.append(f"| {s['doc']} | {s['start']}-{s['end']} | {s['title'].replace('|','/')} | {s['bytes']/1024:.1f} | " +
               ' | '.join(str(s[c]) for c in cols) + ' |')
tot = {}
for k in FILES:
    ss = [s for s in res if s['doc'] == k]
    tot[k] = {c: sum(s[c] for s in ss) for c in cols}
    tot[k]['KB'] = round(sum(s['bytes'] for s in ss) / 1024, 1)
    tot[k]['sections'] = len(ss)
out += ['', '## 합계', '```', json.dumps(tot, ensure_ascii=False, indent=1), '```']
open('section_scan.out.md', 'w', encoding='utf-8').write('\n'.join(out))
print(json.dumps(tot, ensure_ascii=False))
