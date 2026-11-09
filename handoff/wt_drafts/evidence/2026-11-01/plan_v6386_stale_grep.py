"""계획 v6.38.6 열여섯째 커밋 뒤 옛 정의 키워드 grep (계획 5개 plan.md).

분류(줄 단위 + 적중 창 ±250자):
  상태 표지  -- 그 줄에 '[정정됨' 표지가 있다(결정 기록 행, 문언 불변)
  상태 사슬(이전 판 기록) -- Status 줄의 '이전 판' 사슬(판 기록)
  낡은 card 표 기술 -- N6.1 '낡은 card 표'(원칙 19)가 낡은 자리를 적은 칸
  정정 인용  -- 적중 창 안에 '옛·삭제·대체·철회·대상 소멸·지운다' 또는 사용자 결정 O-202~O-213 인용이 있다(새 정본 문언이 옛 것을 지운다·대체한다고 적는 자리)
  다른 뜻    -- 같은 낱말이 다른 개념(offset-trim '2단계 판정' = trim N·m 고정 단계, 옛 삭제 필드 `node.dc_window_def_refined`(O-109 C1))
  표지 없음  -- 위 셋이 아님(정본처럼 읽힐 수 있는 자리 -- 0이어야 함)
history 문서는 원문 보존 기록이라 대상 밖.
"""
import re, sys, io, os
W = r'C:\Users\HSLEE\Documents\Todoc\fpga\wt\plan-v6386\docs\01-plan\features'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plan_v6386_stale_grep.txt')
FILES = ['gain-budget-gmid-sizing', 'offset-trim', 'headroom-chain', 'graph-consumption', 'oracle-portability']
PATS = {
    'dc_conduction_floor': r'dc_conduction_floor',
    'dc_off_current': r'dc_off_current',
    '+tol_VDsat 판정 여유': r'\+\s?tol_VDsat|VDS − VDsat − tol_VDsat|VDsat − VDS − tol_VDsat|VDsat \+ tol_VDsat|VDSAT \+ tol',
    'ε = (gm/ID)·tol_V': r'ε = \(gm/ID\)·tol_V',
    'I_off ≤ / I_off >': r'I_off ≤|I_off >',
    'P-7 반전 수준 하한': r'반전 수준 하한',
    'g = s 꺼짐': r"g = s[^|]{0,80}꺼짐|꺼짐\(VGS = 0 고정\)",
    'SR 하한 floor': r'SR 하한[^|]{0,120}floor|하한 = 입력쌍 소수 가지 전류',
    'node.dc_window_def': r'dc_window_def(?!_refined)',
    'node.dc_window_def_refined': r'dc_window_def_refined',
    'stage2_judgment': r'stage2_judgment',
    '2단계 판정': r'2단계 판정|둘째 단계',
    'off 선언 대조': r"off`? 선언 (MOS|소자)가 (SPICE에서 )?전도|off 유지 경계",
    'off_current_A': r'off_current_A',
}
NEW = re.compile(r'O-20[2-9]|O-21[0-3]')
rows, cnt = [], {}
for f in FILES:
    lines = open(os.path.join(W, f + '.plan.md'), encoding='utf-8').read().split('\n')
    for i, l in enumerate(lines, 1):
        for k, p in PATS.items():
            for m in re.finditer(p, l):
                win = l[max(0, m.start() - 250):m.end() + 250]
                if '[정정됨' in l:
                    c = '상태 표지'
                elif l.startswith('> **Status**'):
                    c = '상태 사슬(이전 판 기록)'
                elif re.search(r'\| (착수 전|완료 이력) \|', l):
                    c = '낡은 card 표 기술'
                elif re.search(r'옛 |삭제|대체|철회|대상 소멸|지운다|바꿈|바꾼다', win):
                    c = '정정 인용'
                elif (f == 'offset-trim' and k == '2단계 판정') or k == 'node.dc_window_def_refined':
                    c = '다른 뜻'
                elif NEW.search(win):
                    c = '정정 인용'
                else:
                    c = '표지 없음'
                cnt[c] = cnt.get(c, 0) + 1
                ctx = l[max(0, m.start() - 120):m.end() + 120].replace('\t', ' ').strip()
                rows.append(f'{f}.plan.md:{i}\t{k}\t{c}\t{ctx}')
head = ['# 계획 v6.38.6 옛 정의 키워드 grep -- plan/v6386 `ef911010`(열여섯째 커밋) 작업 트리, plan.md 5개',
        '# 분류 기준은 이 스크립트 머리 docstring. 합계: ' + ', '.join(f'{k} {v}' for k, v in sorted(cnt.items())) + f', 전체 {sum(cnt.values())}',
        '# 열: 파일:줄 / 키워드 / 분류 / 문맥(±120자)']
open(OUT, 'w', encoding='utf-8').write('\n'.join(head + rows) + '\n')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print(head[1])
for r in rows:
    if '\t표지 없음\t' in r:
        print(r[:300])
