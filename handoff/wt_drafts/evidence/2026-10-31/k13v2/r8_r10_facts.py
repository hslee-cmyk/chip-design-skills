# K13v2: R8 엔진 소비 자리·R10 경로 정의 실측(master HEAD, git show 읽기 전용). 재작성 범위 사실(원칙 8 용도 (2)).
import json, os, re, subprocess
REPO = 'C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills'
P = 'skills/analog-gmid-design/'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'r8_r10_out.txt')
open(OUT, 'w', encoding='utf-8').close()
def w(tag, s):
    with open(OUT, 'a', encoding='utf-8') as f:
        f.write('## ' + tag + '\n' + s.rstrip('\n') + '\n\n')
def show(path):
    return subprocess.run(['git', '-C', REPO, 'show', 'HEAD:' + P + path], capture_output=True).stdout.decode('utf-8', 'replace')
def git(*a):
    return subprocess.run(['git', '-C', REPO] + list(a), capture_output=True).stdout.decode('utf-8', 'replace')
# R8: 행 폭 = 소자별 L 합 -- 행 안 L 혼재를 PDK 규칙 확인 없이 받음
rows = show('gmid_engine/layout/rows.py').split('\n')
w('R8 layout/rows.py:95-96', '\n'.join(rows[94:96]))
ps = show('gmid_engine/layout/pattern_select.py').split('\n')
w('R8 layout/pattern_select.py:137', ps[136])
hit = git('grep', '-n', '-i', r'pitch_rule\|l_dependent\|gate_pitch\|L 혼재', 'HEAD', '--', P + 'gmid_engine/layout', P + 'gmid_engine/core', ':!*CONTRACT.md', ':!*/tests/*')
w('R8 layout·core 코드의 L 의존 간격·고정 pitch 규칙 읽기', hit or '0건')
conv = git('grep', '-l', '-E', r'from (gmid_engine|\.\.)\.?layout', 'HEAD', '--', P + 'gmid_engine/convergence')
w('R8 layout을 부르는 convergence 파일 수', str(len([x for x in conv.split('\n') if x])))
# R10: 경로 기준 정의
d = json.loads(show('assets/sky130_pdk_decl.json'))
heads = sorted({s['path'].split('/')[0] for s in d['sources'].values() if isinstance(s, dict) and 'path' in s})
w('R10 PDK 선언 pdk_root 와 sources 경로 첫 마디', 'pdk_root=%s; 첫 마디=%s' % (d['pdk_root'], ', '.join(heads)))
r = json.loads(show('assets/sky130_lut_rule_decl.json'))
w('R10 LUT 생성 규칙 선언 pdk_root', r['pdk_root'])
l = json.loads(show('assets/lut_v2_location.json'))
w('R10 LUT 위치 선언 pdk_root', json.dumps(l['pdk_root'], ensure_ascii=False))
pv = show('gmid_engine/lut/provenance.py').split('\n')
w('R10 provenance.py:64·69', pv[63] + '\n' + pv[68])
sw = show('assets/sky130_lut_sweep.py').split('\n')
w('R10 LUT 생성기 PDK_ROOT 정의', '\n'.join('%d: %s' % (i + 1, x) for i, x in enumerate(sw) if re.match(r'\s*PDK_ROOT\s*=', x)))
