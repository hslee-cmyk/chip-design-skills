"""계획 v6.38.7 둘째 커밋 뒤 엄격 잔재 grep (계획 6개 plan.md, 작업 트리).
키워드 = O-214·O-216·O-217·O-218로 낡은 문언. 분류:
  R 기록 표지 행('[정정됨'·'[배정 변경'·'[부분 철회'·'결정 기록]')
  S 후속 정정 표 '자리' 칸(design 낡은 문언을 적는 행)·낡은 card 표·Status 이전 판
  N 적중 ±100자에 옛|대체|옮김|삭제|해소|대상 소멸|O-21[4-8]가 있음
  C 나머지 -- 줄마다 읽어 판정(아래 VERDICT; 미판정은 '미판정'으로 남김)
출력: plan_v6387_grep.txt"""
import re, os, sys, io
W = r'C:\Users\HSLEE\Documents\Todoc\fpga\wt\plan-v6387\docs\01-plan\features'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plan_v6387_grep.txt')
FILES = ['gain-budget-gmid-sizing', 'graph-consumption', 'headroom-chain', 'offset-trim', 'oracle-portability', 'offset-strategy']
KW = [r"LA-1 범위 15 \(a\)", r"LA-1 범위 15\(가드", r"R7 가드[^|]{0,30}LA-1 범위 15", r"미룬 결정 \(8\)", r"미룬 결정 \(5\)", r"dc_role 선언 대기", r"선언 전 완료", r"DEC-71 \(4\)\(b\) (L )?역산 함수",
      r"L = LR3·L 칸", r"구현 = card LA-1 범위 15\.", r"gain_l_bounds[^|]{0,40}LA-1(?![a0-9])", r"LA-1a 범위 1\(옛 상위 LA-1a", r"역산 불가[^|]{0,20}격자 폴백"]
REC = re.compile(r"\[정정됨|\[배정 변경|\[부분 철회|결정 기록\]")
NEG = re.compile(r"옛|대체|옮김|삭제|해소|대상 소멸|O-21[4-8]")
VERDICT = {}
rows, cnt, cand = [], {}, []
for f in FILES:
    for i, l in enumerate(open(os.path.join(W, f + '.plan.md'), encoding='utf-8').read().split('\n'), 1):
        for k in KW:
            for m in re.finditer(k, l):
                win = l[max(0, m.start() - 100):m.end() + 100]
                if REC.search(l):
                    c = 'R'
                elif l.startswith('> **Status**') or re.search(r'\| (착수 전|완료 이력) \|', l) or l.startswith('| design'):
                    c = 'S'
                elif NEG.search(win):
                    c = 'N'
                else:
                    c = 'C'
                cnt[c] = cnt.get(c, 0) + 1
                ctx = l[max(0, m.start() - 120):m.end() + 120].strip()
                rows.append(f'{f}:{i}\t{k}\t{c}\t{ctx}')
                if c == 'C':
                    cand.append(f'{f}:{i}\t{k}\t{ctx}')
head = ['# v6.38.7 엄격 잔재 grep -- plan/v6387 둘째 커밋 작업 트리, 계획 6개', '# 합계: ' + ', '.join(f'{a} {b}' for a, b in sorted(cnt.items())) + f', 전체 {sum(cnt.values())}', '# 열: 파일:줄 / 키워드 / 분류 / 문맥']
open(OUT, 'w', encoding='utf-8').write('\n'.join(head + rows) + '\n')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print(head[1])
print('\n'.join(x[:360] for x in cand))
print('--- N')
print('\n'.join(x[:300] for x in rows if '\tN\t' in x))
