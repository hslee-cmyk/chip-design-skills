# K13v2 ⑥: 그 사이 결정 O-208~O-212 행의 K13 관련 키워드 실측(읽기 전용). 결과 o208_212_kw_out.txt
import os
ROOT = 'C:/Users/HSLEE/Documents/Todoc/fpga'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'o208_212_kw_out.txt')
open(OUT, 'w', encoding='utf-8').close()
ud = open(ROOT + '/wt/_drafts/user_decisions.md', 'rb').read().decode('utf-8', 'replace').split('\n')
KW = ('SF-1', 'DEC-79', 'MIM', 'pdk_decl', 'PDK', 'pdk_root', '면적', 'LUT 확장', 'LUT 생성', 'sky130_lut_sweep', 'layout', '레이아웃', 'LR8', 'K13', 'spec 칸', 'card')
for oid in ('O-208', 'O-209', 'O-210', 'O-211', 'O-212'):
    row = [l for l in ud if l.startswith('| %s |' % oid)]
    r = row[0] if row else ''
    hit = [k for k in KW if k in r]
    with open(OUT, 'a', encoding='utf-8') as f:
        f.write('%s\t행 있음=%s\t%s\n' % (oid, bool(row), ', '.join(hit) or '0'))
