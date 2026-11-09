"""계획 v6.38.6 스물두째 커밋(사용자 결정 O-215 -- 임시) 뒤 ICMR 기능 기준 옛 정의 엄격 잔재 grep (계획 6개 plan.md, 작업 트리).

키워드: ICMR 기능 기준을 필수·절대 항·'미선언 = 정의 불능'·'기능 기준 판정 결과가 없으면 정의 불능'·O-206 대가 '선언까지 ICMR 판정 정지'·
        '기준점·허용 저하가 선언될 때까지'·'점별 기능 기준 … 정의 조건'·'4/13 … 정의 불능' 등으로 쓰는 문언.
분류(줄 단위):
  R  기록 표지 -- '[정정됨'·'[부분 철회'·'결정 기록]' 표지 행(결정 기록, 문언 불변)
  S  Status 이전 판 사슬 / 낡은 card 표(원칙 19 -- 낡은 자리를 적는 칸) / LA-1 후속 정정 표 '자리' 칸
  N  같은 줄 ±120자에 O-215 또는 '대상 소멸'·'삭제'·'옛 '·'철회'가 있음(새 정본 문언이 옛 것을 지운다고 적는 자리)
  C  나머지 -- 정본처럼 읽히는 잔재 후보(수작업 판정; 0이어야 함)
출력: plan_v6386_o215_grep.txt
"""
import re, os
W = r'C:\Users\HSLEE\Documents\Todoc\fpga\wt\plan-v6386\docs\01-plan\features'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plan_v6386_o215_grep.txt')
FILES = ['gain-budget-gmid-sizing', 'oracle-portability', 'headroom-chain', 'graph-consumption', 'offset-trim', 'offset-strategy']
KW = [r"기능 기준[^|]{0,40}필수", r"필수[^|]{0,20}기능 기준", r"절대 항", r"미선언[^|]{0,6}= ?정의 불능", r"미선언 판정 제약[^|]{0,20}정의 불능",
      r"기능 기준 판정 결과[^|]{0,30}없으면 정의 불능", r"선언까지 ICMR 판정 정지", r"기준점·허용 저하가 선언될 때까지", r"점별 기능 기준[^|]{0,40}정의 조건",
      r"4/13[^|]{0,60}정의 불능", r"기능 기준 없이 영역 행 창만", r"DE-1 전[^|]{0,30}ICMR 판정 제약[^|]{0,20}정의 불능", r"K-1 충돌"]
REC = re.compile(r"\[정정됨|\[부분 철회|결정 기록\]|\[대체됨|\[철회")
NEG = re.compile(r"O-215|대상 소멸|삭제|옛 |철회|해소")
rows, cnt = [], {}
for f in FILES:
    lines = open(os.path.join(W, f + '.plan.md'), encoding='utf-8').read().split('\n')
    for i, l in enumerate(lines, 1):
        for k in KW:
            for m in re.finditer(k, l):
                win = l[max(0, m.start() - 120):m.end() + 120]
                if REC.search(l):
                    c = 'R'
                elif l.startswith('> **Status**') or re.search(r'\| (착수 전|완료 이력) \|', l) or (l.startswith('| design') or l.startswith('| oracle-portability design')):
                    c = 'S'
                elif NEG.search(win):
                    c = 'N'
                else:
                    c = 'C'
                cnt[c] = cnt.get(c, 0) + 1
                rows.append(f'{f}.plan.md:{i}\t{k}\t{c}\t{l[max(0, m.start() - 140):m.end() + 140].strip()}')
head = ['# O-215 엄격 잔재 grep -- plan/v6386 스물두째 커밋 작업 트리(계획 6개)',
        '# 분류 기준 = 스크립트 머리. 합계: ' + ', '.join(f'{a} {b}' for a, b in sorted(cnt.items())) + f', 전체 {sum(cnt.values())}',
        '# C(정본처럼 읽히는 후보)는 아래 목록을 줄마다 읽어 판정한다 -- 판정은 이 파일 끝 [C 판정]',
        '# 열: 파일:줄 / 키워드 / 분류 / 문맥']
open(OUT, 'w', encoding='utf-8').write('\n'.join(head + rows) + '\n')
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print(head[1])
for r in rows:
    if '\tC\t' in r:
        print(r[:420])
