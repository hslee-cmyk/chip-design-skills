# 단순화 검증 2 반영(bca180de 뒤) -- MJ-A 41 §4.7 옛 본문 재작성·m-E·추가 축소 → design 이력 H40-30~·H41-21~·H42-01~
W = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/"
T40 = open(W + "gain-budget-gmid-sizing.40-engine.design.md", encoding="utf-8").read()
T41 = open(W + "gain-budget-gmid-sizing.41-gain-budget.design.md", encoding="utf-8").read()
H = "design 이력 "


def seg(T, a, b, inc=False):
    i = T.index(a)
    j = T.index(b, i)
    return T[i:j + (len(b) if inc else 0)]


DIFF = "`(y, <role differential_input_p 포트 넷>)`"
JOBS = [
 dict(id="H41-21", file="41", title="§4.7-1 2 뿌리와 y 키(옛 문언 -- 4.7-V 1행으로 대체)", mode="lines", start="2. **뿌리와 y 키**:", end=None,
      new="2. **뿌리와 y 키**(4.7-V 1행 -- DEC-106): 입력 DC 미선언이면 선언된 차동 입력쌍(role `differential_input_p`·`_n`)의 두 포트를 한 점(입력 점)으로 묶고, 그 점이 F에 닿으면 v_cm은 KVL 종속, 아니면 W4 뿌리 하나·y 키 " + DIFF + "(결과 JSON 키 `y:<그 넷>`). 그 밖 W4 뿌리는 뿌리 규칙 그대로((구조 색, 이름) 최소, 같은 색 후보가 둘 이상이면 `TieBreak(w4_root)`; y 키 = 뿌리 넷). 한 성분 안 뿌리가 아닌 입력 포트는 트리 경로(MOS VGS)로 쓰인다. (옛 문언 = " + H + "H41-21.)"),
 dict(id="H41-22", file="41", title="§4.7-1 5 노드 풀이 블록 쪽(옛 문언 -- `_solve_input_window`·`_interior_solution`·'둘 이상이면 정지')", mode="lines", start="5. **노드 풀이 블록 쪽**(같은 card):", end=None,
      new="5. **노드 풀이 블록 쪽**(같은 card): `members` = 자기 자신(사슬 없음). 입력 점 뿌리의 θ 키 = " + DIFF + "(4.7-V 1행); W4 뿌리 창 = KVL 순서 창(4.7-3 1 -- 입력 창 측정·`_solve_input_window`·`_interior_solution` 없음, 4.7-V 2행). **G_vgs 밖 고립 입력 포트**(MOS gate·source에도 저항에도 닿지 않는 넷)는 W4 뿌리 y 키 = 넷으로 쓰이고, 차동 입력쌍이 아니면 다중 입력 규칙(4.7-V 1행 -- `input_cm_undefined` 탐색 전 정지)에 든다(세지 않으면 y가 둘인 회로가 정지 없이 지나감). `REL_TIE` 분기(writer 식·야코비안·path value) 삭제. `achievability`의 `tie:<넷>` 등식 삭제. (옛 문언 = " + H + "H41-22.)"),
 dict(id="H41-23", file="41", title="§4.7-1 test interface 단언 (a)의 y 키·(d) 옛 `input_port_multiple_roots` 단언", mode="sub",
      old=seg(T41, "입력 포트 W4 뿌리의 y 키 = 그 넷 이름,", "위치 = `E/tests/sizing/test_writer_plan.py`"),
      new="입력 점 W4 뿌리의 y 키 = " + DIFF + ", 기대 종속 목록(같은 DC 엣지로 생긴 종속 0, 포트 경로가 둘 이상인 v1 고리의 ΔV 소거 `cycle_vgs` 포함)은 toy 연결에서 손으로 유도한다 (b) 종속 수 = 같은 DC 엣지 없는 G_vgs(F 한 점)의 순환 수(손계산) (c) 입력 DC 선언 toy의 쓰기 계획 = 손계산 오라클(base에서도 green -- 무동작 성질) (d) 두 포트가 서로 다른 G_vgs 성분인 차동 입력쌍 toy → 정지 없이 입력 점 한 점(base는 포트마다 뿌리 -- red), 차동 쌍이 아닌 다중 입력 toy → `StructureUnresolvedError`, `detail[\"rule_branch\"] == \"input_cm_undefined\"`(base는 정지하지 않아 red -- 4.7-V 1행·40 §3.11-4). (옛 단언 = " + H + "H41-23.) "),
 dict(id="H41-24", file="41", title="§4.7-3a 3 판정 점의 끊긴 참조", mode="sub",
      old="4.7-3 1의 마지막 `override` 풀이 해 -- 그 해가 평가 스냅샷이 되어 봉인이 같은 점을 본다",
      new="노드 풀이 블록이 그 평가의 θ y로 푼 해(4.7-3 1; 계획 '노드 풀이 블록의 마지막 풀이 = 봉인이 보는 점') -- 그 해가 평가 스냅샷이 되어 봉인이 같은 점을 본다"),
 dict(id="H41-25", file="41", title="§4.7-7 L12 (a)·(e)·(f) 본문(커널 되풀이·`dc_window.tol_v` -- 4.7-V로 대상 소멸)", mode="sub",
      old=seg(T41, "(a) 커널 되풀이 `k_max` 소진 toy·tol 미정 toy(4.7-3 1 A6 b·c;", "(b) **F 성분 입력 DC 미선언 포트 library toy**"),
      new="(a) 대상 소멸(4.7-V 2행 -- 커널 되풀이·상태 칸 없음; 그 자리 toy = 'y 범위 = 순서 창' toy, §9) "),
 dict(id="H41-26", file="41", title="§4.7-7 L12 (e)·(f) 본문(커널 y 끝점·판정 tol 매 해 -- 대상 소멸)", mode="sub",
      old=seg(T41, "(e) **커널 y 끝점 기대**(사용자 결정 O-103, 4.7-8 (8)):", "기대 작성은 test 작성 주체 몫.", inc=True),
      new="(e)·(f) 대상 소멸(4.7-V 2행 -- A6 선형 끝·`node.dc_window.tol_v`·되풀이 판정 tol 없음; 순서 창 끝점의 봉인 7 거부는 40 §3.11-1·E-13 재상정 기준)."),
 dict(id="H41-27", file="41", title="§4.7-8 (8) 커널 W4 입력 뿌리 y 끝(대상 소멸)", mode="sub",
      old=seg(T41, "(8) **커널 W4 입력 뿌리 y 끝**", "(9) (대상 소멸"),
      new="(8) (대상 소멸 -- 4.7-V 2행: 커널 A6 선형 끝이 없음, 순서 창 끝점의 봉인 7 거부는 40 §3.11-1·E-13 재상정 기준; 옛 항목 = " + H + "H41-27) "),
 dict(id="H41-28", file="41", title="§4.7-8 (11) 커널 θ 프레임 창 미수렴 표시(대상 소멸)", mode="sub",
      old=seg(T41, "(11) **커널 θ 프레임 창 미수렴 표시**", "(12) **B77**"),
      new="(11) (대상 소멸 -- 커널 창 미수렴 상태 없음, 4.7-V 2행; 옛 항목 = " + H + "H41-28) "),
 dict(id="H41-29", file="41", title="§6.7-1a 옛 '개정' 항목(포트마다 W4 뿌리 후보·뿌리 둘 이상 정지)", mode="lines", start="- 개정(정본 = §4.7-1 1~5;", end=None,
      new="- 개정(정본 = §4.7-1 1~5·4.7-V 1행 -- DEC-106; 아래 v1.15.2 개정): 입력 DC 미선언이어도 '같은 DC' 엣지를 G_vgs에 넣지 않는다. (옛 '포트마다 W4 뿌리 후보·뿌리 둘 이상 정지' 문언 = " + H + "H41-29.)"),
 dict(id="H41-30", file="41", title="§9 §6.7-1a 쓰기 계획 행(옛 단언 + v1.15.2 대체 덧댐)", mode="lines", start="| §6.7-1a 쓰기 계획(card IT-1, §4.7-1) |", end=None,
      new="| §6.7-1a 쓰기 계획(card IT-1, §4.7-1) | (a) 입력 DC 미선언 차동 입력 toy, 입력 DC 선언 toy, 차동 쌍이 아닌 다중 입력 toy -- 기대 writer·종속 분류는 toy 연결에서 손으로 유도(손계산 오라클) | `tests/sizing/test_writer_plan.py` 안 새 test 함수(구조 규칙 H -- 계획 F-IT4·X-IT3, 함수 이름은 test 주체가 `git grep`으로 겹침 확인) | **red 먼저**(검증자가 격리 복제본 base에서 실패 기록): relation `input_tie` 0, 같은 DC 엣지로 생긴 종속 0 + 종속 수 = 같은 DC 엣지 없는 G_vgs 순환 수(포트 경로가 둘 이상인 v1 고리의 ΔV 소거 `cycle_vgs`는 기대값에 포함), 차동 입력쌍 = 입력 점 한 점·y 키 " + DIFF + "(두 포트가 다른 성분이어도 정지 없음), 선언 toy 쓰기 계획 = 오라클(base에서도 green), 차동 쌍이 아닌 다중 입력 = `unsupported_rule_branch`·`input_cm_undefined`(base는 정지하지 않음 -- red) |"),
 dict(id="H41-31", file="41", title="§4.7-0 as-built 사실 표(A1~A10, master 9401e98f)", mode="lines", start="**4.7-0 as-built 사실**", end="**4.7-1 card IT-1",
      new="**4.7-0 as-built 사실**(A1~A10, master `9401e98f` -- 재작성 범위 인용의 출처) = " + H + "H41-31(O-153: as-built는 규칙 근거가 아님; 본문의 'A1'·'A6 a'·'A10' 인용은 이 표를 가리킨다).\n"),
 dict(id="H41-32", file="41", title="§6.4-2 한계 기록(제안서 실측 한 슬라이스)", mode="lines", start="   - 한계 기록: 제안서 실측은 W 5 µm", end=None, new=""),
 dict(id="H41-33", file="41", title="§4.7-9 후속 정정 목록 복원 자리(H41-15 원문은 그대로 -- 미결 항목만 본문으로)", mode="lines",
      start="- 다른 계획·문서의 후속 정정 목록(helper 이동에 따른 경로·줄 번호 변경", end=None,
      new="- **다른 계획·문서의 후속 정정**(각 문서가 자기 개정에서 고친다 -- 미결, 원문 = " + H + "H41-15): helper 이동(4.7-4, IT-2c)으로 경로가 바뀐다 -- headroom-chain HC-S가 고칠 `block_columns.saturation_rows`(→ `_helpers_dc_solve.Circuit.region_rows`), 계획 N6.8 DE-1 F-DE5의 `E/sizing/block_columns.py` 인용(`_refine_ends`는 IT-2b에서 삭제 -- 끝 풀이 없음, O-109 C1), N6.6 F-I2-1·F-I2-4와 소비자 표의 `block_columns.py` 인용(IT-2 착수 때 재측정), 계획 DE-1 (c)(N6.8)의 '`offset_systematic.py` 같은 factor 재사용' 인용 → IT-2 뒤 `graph.ss_nodal` READS."),
 dict(id="H40-30", file="40", title="§11 ② search 상태·층 0 행의 선행 칸(완료 card 상태 기록)", mode="sub",
      old=seg(T40, "**XRUN-F1 card B**(위 행), ①(①-b 완료:", " | D-GR1·4·5·9·10·14, D-AP1 |"),
      new="선행 card 모두 병합됨(XRUN-F1 card B 138a6db3, ①-b eadb729, 실행 사이 재사용 제거 f23aec8, NFR-4 결정성, 결정 10 code_hash af10c9b) -- 선행 조건 원문 = " + H + "H40-30; U15 design(41 §5 v1.6) 승인"),
 dict(id="H40-31", file="40", title="머리 Planning Doc 판·as-built 기준(옛 메타)", mode="lines", start="> **Planning Doc**:", end="\n" if False else "진행 순서는 bkit PDCA다",
      new="> **Planning Doc**: [gain-budget-gmid-sizing.plan.md](../../01-plan/features/gain-budget-gmid-sizing.plan.md) v6.38.4\n> **as-built 기준**: 절마다 인용한 커밋(최근 = integ/it12 `b12792ab`); 옛 기준 master `004b7d2`·브랜치 목록 = " + H + "H40-31.\n"),
 dict(id="H40-32", file="40", title="§2.4.13 (1) 대상 행의 BLAS 적재 실측 괄호", mode="sub",
      old=seg(T40, "(실측 2026-10-15: numpy 2.4.6 `libscipy_openblas64_`", "Haswell')", inc=True),
      new="(실측 = " + H + "H40-32)"),
 dict(id="H42-01", file="42", title="머리 판 bullet v1.15.1·v1.15.0", mode="lines", start="> - **design v1.15.1 -- 계획 v6.38.2 맞춤", end="> - 한 행이 FR·NFR·DEC·설계 항목 하나다.",
      new="> - 옛 판 bullet(v1.15.1·v1.15.0) = " + H + "H42-01."),
 dict(id="H42-02", file="42", title="§4 판별 이력 v1.15.2 집계 정정 ~ v1.7", mode="lines", start="v1.15.2 집계 정정(2026-10-29", end="**후속 항목**",
      new="판별 이력(v1.15.2 집계 정정 ~ v1.7) = " + H + "H42-02.\n"),
 dict(id="H42-03", file="42", title="§4 판별 이력 v1.6 최종검증 ~ v1.4", mode="lines", start="v1.6 최종검증(2026-10-12)", end="센 방법:",
      new="판별 이력(v1.6 ~ v1.4) = " + H + "H42-03.\n"),
]
