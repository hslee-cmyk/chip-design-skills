# K13v2 점검 파일용 실측(읽기 전용: git show/grep, 파일 읽기). 결과는 케이스마다 out.txt에 append.
import hashlib, re, subprocess, sys, os
ROOT = 'C:/Users/HSLEE/Documents/Todoc/fpga'
REPO = ROOT + '/chip-design-skills'
PLANW = ROOT + '/wt/plan-v6386'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out.txt')
open(OUT, 'w', encoding='utf-8').close()
def w(tag, s):
    with open(OUT, 'a', encoding='utf-8') as f:
        f.write('## ' + tag + '\n' + s.rstrip('\n') + '\n\n')
def git(repo, *a):
    return subprocess.run(['git', '-C', repo] + list(a), capture_output=True).stdout.decode('utf-8', 'replace')
# 1 후보 sha
cand = ROOT + '/wt/_drafts/evidence/2026-10-31/plan_v6386_decision_candidates.md'
w('1 candidate sha256', hashlib.sha256(open(cand, 'rb').read()).hexdigest())
# 2 계획 줄(a4d87f1a)
plan = git(PLANW, 'show', 'a4d87f1a:docs/01-plan/features/gain-budget-gmid-sizing.plan.md').split('\n')
w('2a plan line count a4d87f1a', str(len(plan)))
for n in (742, 1028, 1039, 1248, 1272, 2375):
    w('2b plan:%d' % n, plan[n-1][:600])
# 3 계획 grep
def hits(pat):
    return [(i+1, l[:200]) for i, l in enumerate(plan) if re.search(pat, l)]
for pat in (r'로더 확장', r'단위 캡 배열', r'slope 참조 꼴', r'PDK 루트', r'소자 kind 지도', r'gate pitch'):
    h = hits(pat)
    w('3 grep %s (%d)' % (pat, len(h)), '\n'.join('%d: %s' % x for x in h))
# 4 엔진 사실(master HEAD; 325ee241 대비 skills diff)
w('4a skills diff 325ee241..HEAD', git(REPO, 'diff', '--stat', '325ee241', 'HEAD', '--', 'skills') or '(빈 diff)')
P = 'skills/analog-gmid-design/'
def show(path):
    return git(REPO, 'show', 'HEAD:' + P + path).split('\n')
pd = show('gmid_engine/core/pdk_decl.py')
for a, b in ((8, 11), (46, 52), (526, 526), (607, 612)):
    w('4b pdk_decl.py:%d-%d' % (a, b), '\n'.join(pd[a-1:b]))
defs = [(i+1, l) for i, l in enumerate(pd) if l.startswith('def ')]
w('4c pdk_decl.py def 경계', '\n'.join('%d: %s' % x for x in defs))
dl = show('gmid_engine/lut/data_location.py')
w('4d data_location.py:80-84', '\n'.join(dl[79:84]))
pv = show('gmid_engine/lut/provenance.py')
w('4e provenance.py:62-66', '\n'.join(pv[61:66]))
for a in ('assets/sky130_pdk_decl.json', 'assets/sky130_lut_rule_decl.json', 'assets/lut_v2_location.json'):
    ls = show(a)
    w('4f %s pdk_root 줄' % a, '\n'.join('%d: %s' % (i+1, l) for i, l in enumerate(ls) if 'pdk_root' in l))
sw = show('assets/sky130_lut_sweep.py')
w('4g sky130_lut_sweep.py pdk_root 줄', '\n'.join('%d: %s' % (i+1, l.strip()[:160]) for i, l in enumerate(sw) if 'pdk_root' in l))
fl = git(REPO, 'grep', '-l', 'nfet_01v8', 'HEAD', '--', P + 'gmid_engine').split('\n')
fl = [x for x in fl if x]
t = [x for x in fl if '/tests/' in x]; nt = [x for x in fl if '/tests/' not in x]
w('4h nfet_01v8 gmid_engine 파일', 'tests %d, 그 밖 %d: %s' % (len(t), len(nt), ', '.join(nt)))
# 5 O-197 점검: K13 절 PDK 고유 토큰 위치
txt = open(cand, 'rb').read().decode('utf-8')
s = txt.index('## K13.'); e = txt.index('## 요약')
k13 = txt[s:e]
toks = r'sky130|capm\.|camimc|cpmimc|nfet_01v8|pfet_01v8|C:/pdk|0\.84|0\.14 ?µm'
lines = k13.split('\n')
res = []
for i, l in enumerate(lines):
    for m in re.finditer(toks, l):
        res.append('%d: %s ... [%s]' % (i, l[:60], m.group(0)))
w('5a K13 절 PDK 고유 토큰(절 안 줄 번호)', '\n'.join(res) or '0')
bi = k13.index('**바뀌는 결정·문언**')
chg = k13[bi:]
w('5b 바뀌는 결정·문언 안 PDK 고유 토큰 수', str(len(re.findall(toks, chg))))
# 6 원칙 1 문언 점검: 후보 K13 ③의 원칙 1 칸
m = re.search(r'\| ③ \|[^\n]*', k13)
w('6 후보 K13 ③ 원칙 1 부분', m.group(0)[:400] if m else '없음')
# 7 user_decisions O-202~O-207 의 키워드
ud = open(ROOT + '/wt/_drafts/user_decisions.md', 'rb').read().decode('utf-8', 'replace').split('\n')
for oid in ('O-202', 'O-203', 'O-204', 'O-205', 'O-206', 'O-207'):
    row = [l for l in ud if l.startswith('| %s |' % oid)]
    r = row[0] if row else ''
    kw = [k for k in ('SF-1', 'DEC-79', 'MIM', 'pdk_decl', 'PDK', '면적 제약', '면적', 'spec 칸', 'judged_by', 'card') if k in r]
    w('7 %s 키워드' % oid, ', '.join(kw) or '0')
