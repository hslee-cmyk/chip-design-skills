"""계획 v6.38.6 열일곱째 커밋 뒤 엄격 기준 잔재 grep (계획 6개 plan.md, 작업 트리).

기준(계획 검증 51 '엄격 기준' -- 그 문장이 정본처럼 읽히는가):
  R  기록 표지 -- 그 줄(행·문단)에 '[정정됨'·'결정 기록]'·'[대체됨'·'[철회'·'[삭제' 표지(결정 기록 행 -- 문언 불변)
  N  부정·대체 인접 -- 적중 ±90자 안에 옛|삭제|대체|철회|대상 소멸|기각|지운|두지 않|쓰지 않|않는다|없음|폐기|소멸|정정|읽기 0|호출 0|하지 않|만들지 않|아니다|아님
  S  Status 이전 판 사슬 / N6.1 낡은 card 표(원칙 19 -- 낡은 자리를 적는 칸)
  D  다른 뜻(자동 규칙 -- 아래 OTHER: 같은 낱말의 다른 개념)
  C  나머지 -- 수작업 판정 대상(MANUAL 표의 판정과 근거를 함께 적는다; 판정이 '정본처럼 읽힘'이면 고쳐야 함)
history 문서는 원문 보존 기록이라 대상 밖. 줄 번호 = 작업 트리.
"""
import re, sys, io, os
W = r'C:\Users\HSLEE\Documents\Todoc\fpga\wt\plan-v6386\docs\01-plan\features'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plan_v6386_stale_grep2.txt')
FILES = ['gain-budget-gmid-sizing', 'graph-consumption', 'headroom-chain', 'offset-trim', 'oracle-portability', 'offset-strategy']
KW = [r"dc_conduction_floor", r"dc_off_current", r"\+ ?tol_VDsat", r"VDsat \+ tol", r"VDSAT \+ tol", r"− ?tol_VDsat", r"\(gm/ID\)·tol_V",
      r"I_off ≤", r"I_off >", r"ε·ID", r"반전 수준 하한", r"g = s[^|]{0,60}꺼짐", r"conduction_floor", r"dc_window_def", r"stage2_judgment",
      r"잡음 수준", r"\[0, I_off\]", r"단조성 구간", r"2단계", r"둘째 단계", r"두 단계", r"1단계", r"\bR0\b", r"전도 여유", r"전도 행",
      r"off_current_A", r"V_on", r"off 유지 경계", r"\bU-69\b", r"\bP-7\b", r"_peak_floor", r"\|ID\| ≤ tol_I", r"선언 영역 대조", r"꺼짐 판정",
      r"PENDING_CONDUCTION", r"confirmed_range", r"sweep_rezoom", r"sat_margin_V", r"off_vgs0", r"off_device_on_signal_path"]
REC = re.compile(r"\[정정됨|결정 기록\]|\[대체됨|\[철회|\[삭제")
NEG = re.compile(r"옛|삭제|대체|철회|대상 소멸|기각|지운|두지 않|쓰지 않|않는다|없음|폐기|소멸|정정|읽기 0|호출 0|하지 않|만들지 않|아니다|아님")
OTHER = [  # (파일 또는 '*', 키워드 정규식, 문맥 정규식, 뜻)
    ('offset-trim', r'2단계|1단계|두 단계', r'.', 'offset-trim 1·2단계 = trim 흐름 단계(N·m 추천 → 고정 판정)'),
    ('offset-strategy', r'2단계|1단계|두 단계', r'.', 'offset-strategy 단계 = 탐색 흐름 단계'),
    ('*', r'1단계|2단계|두 단계', r'선언 영역 (범위|판정)|LUT (생성|확장)|부분 교차|card 0|MOD|레이아웃|DP|단계 A|단계 B|서열|결합|KCL|되먹임|servo|뉴턴|SCC|역산|조립|E-0|U17|출발|층 0|bisection|근 찾기|사다리|커밋', '다른 흐름의 단계 번호(판정 2단계가 아님)'),
    ('*', r'두 단계', r'혼재|C-1', '구동 종류 혼재 노드 판정 두 단계(design 41 §1.5)'),
    ('*', r'V_on', r'.', 'V_on'),
]
rows, cnt, cands = [], {}, []
for f in FILES:
    lines = open(os.path.join(W, f + '.plan.md'), encoding='utf-8').read().split('\n')
    for i, ln in enumerate(lines, 1):
        rec = bool(REC.search(ln))
        for kw in KW:
            for m in re.finditer(kw, ln):
                s, e = m.start(), m.end()
                win = ln[max(0, s - 90):e + 90]
                if rec:
                    c = 'R'
                elif ln.startswith('> **Status**') or re.search(r'\| (착수 전|완료 이력) \|', ln):
                    c = 'S'
                elif NEG.search(win):
                    c = 'N'
                else:
                    c = 'C'
                    for ff, kp, cp, mean in OTHER:
                        if (ff == '*' or ff == f) and re.search(kp, m.group(0)) and re.search(cp, ln[max(0, s - 200):e + 200]) and mean != 'V_on':
                            c = 'D'
                            break
                cnt[c] = cnt.get(c, 0) + 1
                ctx = ln[max(0, s - 160):e + 160].replace('\t', ' ').strip()
                if c == 'C':
                    cands.append((f, i, kw, ctx))
                rows.append(f'{f}.plan.md:{i}\t{kw}\t{c}\t{ctx}')
head = ['# 계획 v6.38.6 엄격 기준 잔재 grep -- plan/v6386 열일곱째 커밋 작업 트리, plan.md 6개(offset-strategy 포함)',
        '# 분류 기준 = 스크립트 머리 docstring. 합계: ' + ', '.join(f'{k} {v}' for k, v in sorted(cnt.items())) + f', 전체 {sum(cnt.values())}',
        '# C(수작업 판정 대상) 목록은 아래 [C 목록], 판정은 plan_v6386_stale_grep2_manual.txt',
        '# 열: 파일:줄 / 키워드 / 분류 / 문맥(±160자)']
open(OUT, 'w', encoding='utf-8').write('\n'.join(head + rows + ['', '[C 목록]'] + [f'{f}:{i}\t{kw}\t{ctx}' for f, i, kw, ctx in cands]) + '\n')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print(head[1])
for f, i, kw, ctx in cands:
    print(f'{f}:{i}\t{kw}\t{ctx[:330]}')
