"""plan_v6386_stale_grep2.txt의 C(수작업 판정 대상) 줄마다 작성자 수작업 판정을 붙인다(판정 = 그 문장을 읽어 정함).
판정 갈래: 다른 뜻 / 현행 정본 문언(새 정의와 맞음) / 결정 기록 행 / 원칙 19 정정 표 자리 칸(낡은 자리를 적는 칸) / 출처 기록 / 정본처럼 읽히는 잔재(고칠 것)
결과: plan_v6386_stale_grep2_manual.txt (판정 없는 C가 있으면 '미판정'으로 남김 -- 0이어야 함)."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'plan_v6386_stale_grep2.txt'), encoding='utf-8').read().split('\n')
k = src.index('[C 목록]')
items = [l.split('\t') for l in src[k + 1:] if l.strip()]
GB = 'gain-budget-gmid-sizing'
V = {}
def put(f, lines, verdict):
    for n in lines:
        V[(f, n)] = verdict
put(GB, [300, 427, 428, 1287, 1288, 2169, 2255], "다른 뜻 -- O-73 '1단계 = DUT 외부 망 표지(SD-1), 2단계 = 응용 topology(AP-1)' 단계 번호")
put(GB, [728], "다른 뜻 -- 면적 '두 단계 정의'(탐색 축·판정 축, DEC-79)")
put(GB, [342], "결정 기록 행 -- O-114·O-115 결정 행의 경위 요약('v6.36 O-118 2번: … 전도 행 과보수 수용'은 그 결정의 당시 내용; 현행 = N3.8 '측정 구성 창 행 = 영역 행만', O-205 (3))")
put(GB, [417], "결정 기록 행 -- O-205 결정 행의 '원래 취지와 다름' 목록(옛 결정 이름 나열)")
put(GB, [648, 1408, 2620], "현행 정본 문언 -- 꺼짐 판정 = 선언 방향 채널 op ID ≤ 0(O-205·O-210 RR-2), KCL 항등 0 전류 MOS 예외 정의 자리")
put(GB, [660], "현행 정본 문언 -- N3.6 정본 (7) 삭제 필드·소비자 목록(지우는 대상 나열)")
put(GB, [729], "현행 정본 문언 -- `dc_window_def_refined`는 '두지 않는다' 목록, V_on = 차동 출력 V_op − V_on(다른 뜻)")
put(GB, [730], "현행 정본 문언 -- '같은 덱'으로 oracle 2단계 왕복이 없어진다(삭제 서술)")
put(GB, [1219], "결정 기록 -- N5.3 Q-S9 결정 행의 권고 (A′) 문언(꺼짐 판정 대상 = 현행과 같음)")
put(GB, [1711, 1717], "현행 정본 문언 -- IT-2 완료 조건의 '다듬은 창 … 정의 0'(삭제 확인 단언)")
put(GB, [1808], "다른 뜻 -- V_on = 차동 출력 V_op − V_on")
put(GB, [2039], "원칙 19 정정 표 자리 칸 -- oracle design 행(KCL 항등 0 MOS 제외 꺼짐 판정 = 현행)")
put(GB, [2042, 2043, 2044, 2045, 2046, 2048, 2049, 2051, 2053, 2054], "원칙 19 정정 표 자리 칸 -- design 후속 정정 표가 낡은 design 문언을 적는 칸(맞출 내용 칸이 현행 정본)")
put(GB, [2159], "현행 정본 문언 -- EO-1 범위 4 머리 '옛 범위 4(…) = history'(삭제 서술, 부정 낱말이 ±90자 밖)")
put(GB, [2163], "현행 정본 문언 -- EO-1 완료 포화 띠 toy(VDsat − tol_VDsat < VDS < VDsat → 거부 + '구별 불가' 기록 = O-204 정본 (2))")
put(GB, [2445], "현행 정본 문언 -- N6.35 E-19 행 test 칸(g = s 정지·꺼짐 분류 0 단언)")
put(GB, [2646], "현행 정본 문언 -- U-102 행 '슬루 벤치 같은 덱 `.dc`로 oracle 2단계 왕복 제거'(삭제 서술)")
put('graph-consumption', [233, 675], "다른 뜻 -- 부모 포인터를 '두 단계 이상' 따라가는 경로 재구성")
put('graph-consumption', [352], "현행 정본 문언 -- `off` 선언 소자는 '선언 영역 대조는 없다'(O-202)")
put('graph-consumption', [742], "현행 정본 문언 -- 정본 소유 표의 '소자 동작점 전도·꺼짐 판정 = EO-1 공용 전도 판정 함수'")
put('graph-consumption', [784], "현행 정본 문언 -- GC-7 `_peak_floor`(gm/ID 정점 마디 LUT memo 파생 함수 -- 전도 하한 아님), `current_box` I_off = θ 전류 상자 하한(다른 개념; design 41 §4.2 대조는 gain-budget 후속 정정 표 행)")
put('headroom-chain', [60], "출처 기록 -- v0.7.6 때 읽은 상위 계획의 필드 이름(판 인용); 현행 창 필드는 같은 문단 뒤쪽 '현행 창 필드는 상위 N3.8 창 필드' 문장(열일곱째 커밋 m5)")
put('oracle-portability', [429], "현행 정본 문언 -- '지금 오라클과 다른 점(OP-5가 고침)': as-built `off_current_A`·`sat_margin_V`를 지운다는 재작성 범위 서술")
put('oracle-portability', [689], "다른 뜻 -- oracle design §7.2 실행 전 검사 '2단계'(절차 단계 번호)")
put('oracle-portability', [717, 718], "다른 뜻 -- oracle design §21.2 '2단계 (a)(c)(e)'(절차 단계 번호, DR 행의 design 자리 인용)")
out, miss = [], 0
for it in items:
    f, n = it[0].rsplit(':', 1)
    n = int(n)
    v = V.get((f, n))
    if v is None:
        v = '미판정'
        miss += 1
    out.append(f'{f}:{n}\t{it[1]}\t{v}')
cnt = {}
for l in out:
    key = l.split('\t')[2].split(' -- ')[0]
    cnt[key] = cnt.get(key, 0) + 1
head = ['# 엄격 기준 잔재 grep C 목록 수작업 판정 -- 작성자(계획 v6.38.6 열일곱째 커밋), 판정 = 그 문장을 읽어 정함',
        '# 합계: ' + ', '.join(f'{a} {b}' for a, b in sorted(cnt.items())) + f'; 미판정 {miss}',
        "# '정본처럼 읽히는 잔재'는 열일곱째 커밋 안에서 고쳤다: headroom-chain M-H1c 행(VDS 대 VDsat + tol -> VDsat, grep 첫 실행 뒤 수정 -- 지금 목록에 없음)",
        "# N 갈래(부정 낱말 ±90자 인접)도 판정 키워드(2단계·둘째 단계·두 단계·stage2·confirmed_range·sweep_rezoom·PENDING·off_current_A·+tol·선언 영역 대조·꺼짐 판정·off 유지·dc_window_def·전도 여유·R0·전도 행) 적중을 계획 6개 전부 줄마다 읽었다(부정 낱말이 다른 절에 걸려 정본처럼 읽히는 문장을 놓치지 않으려고).",
        "#   그 재검토에서 정본처럼 읽혀 고친 곳: headroom-chain N0.1 '포화 불가 판정(R-3)' 정의의 'VDS ≥ VDsat + tol'·N3.1-3 '항 평가 동작점'의 '항(VDsat + tol …)', oracle-portability X-R4 'U-6 알림'의 'EO-1 2단계 배선'·OP-5 '온도 점 전도 판정' 절 이름 -- 나머지는 옛 문언을 지운다·대체한다·대상 소멸이라고 적는 자리 또는 결정 기록 행.",
        '# 열: 파일:줄 / 키워드 / 판정']
open(os.path.join(HERE, 'plan_v6386_stale_grep2_manual.txt'), 'w', encoding='utf-8').write('\n'.join(head + out) + '\n')
print(head[1])
