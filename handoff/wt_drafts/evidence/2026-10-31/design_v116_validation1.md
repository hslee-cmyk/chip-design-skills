# design v1.16.0 독립 검증 1 (2026-10-31)

- 대상: worktree `wt/design-v115` 브랜치 design/v115 `31b042cd..bc3b3572`(커밋 7개), 문서 40·41·42·design history
- 검증자: 작성자 아님(읽기 전용). 기준 = chip-design-skills CLAUDE.md A~F 33항목 + fpga CLAUDE.md '★graph 단일 정본' + 계획 v6.38.5(같은 worktree `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`)
- 방법: `git -C <W> diff -U0` 추가 줄 전수 읽기(546줄), 삭제 대상 이름 잔존 grep(40·41·42), 계획 원문 grep(U-124·DEC-64 (v2)·DEC-95 (3)·DEC-104 (3)(a)(b)·LA-1 Q8·DEC-11·LI-1), as-built는 사실 확인(재작성 범위·모듈 지도)으로만 인용, 진행 기록 `design_v116_progress.md`, 증거 `2026-10-30/gmid_multiroot.md` §2·§5.1
- 결론: **Major 2 · minor 9** -- design 승인 단계 진입 **불가**(Major 0 아님). 두 Major 모두 문언 수정으로 닫을 수 있다.

## 1. Major

### M1. R7 가드 필드 `GuardRow.ln_idu_set` -- 점 함수인 해 집합을 S0 한 점 값으로 저장해 층 0 후보에서 소비 (물리 정합·정의)
- 자리: 40:450(`device: start.guard` 행), 41:1796(R7 가드 필드 writer), 41:1408(E12), 41:1756(§6.7-4 (ii) "구간 = 고리 나머지 구간 ∩ R7 가드 필드 `device: start.guard` 해 집합"), 42:314(D-TB1c), J2(41:1445).
- 근거: 순방향 제약 행 g(ln IDu) ≤ 가드 경계의 해 집합은 그 소자의 (L, VDS, VSB) 점에서의 gm/ID(ln IDu) 곡선으로 정해진다(41:871 '그 점 (L, VDS, VSB)에서 … 순방향 조회'). writer는 출발 단계 블록(`start_intervals`) 하나이므로 `ln_idu_set`은 출발점의 (L, VDS, VSB)에서 잰 값이다. 그런데 소비자 R6 블록은 출발 스냅샷과 **층 0 후보 스냅샷에서 같은 블록으로** 불리고(41:1790), 층 0은 L 동치류 L 축 전부와 W4 VDS를 움직인다(41:514). 그러면 층 0 후보에서 B 밀도 재개방(41:903 (ii))·R7 (나) 선택이 다른 점의 해 집합을 쓴다 -- 그 후보의 실제 gm/ID 가드와 다르다(pfet 혹 띠에서는 구간 개수까지 달라질 수 있음, `gmid_multiroot.md` §2: L ≤ 0.2에서 진폭 최대 8.2 %). 옛 꼴 `GuardInterval(gm_id_lo, gm_id_hi)`는 경계를 gm/ID로 담아 점과 무관했다 -- v1.16.0 개정이 일반성을 줄였다(원칙 6).
- 계획 대조: 계획 DEC-104 (3)(b)·DEC-105 (5)(a)는 가드를 "ln IDu 축 위 순방향 제약 **행**"으로 적는다(행 = 경계 + 점에서 평가하는 함수). 해 집합을 필드 칸으로 저장하라는 문언은 없다 -- design 판단 J2가 더한 칸이다.
- 수정안(택1, 권고 (가)): (가) `GuardRow`에는 행(경계 `g_lo`·`g_hi`, `sources`)만 두고, 해 집합은 소비자(R6 블록)가 자기 평가 점 (L, VDS, VSB)에서 같은 순수 함수(41 §5.3.3 'gm/ID 부등식의 꼴' 해 집합 계산)로 낸다 -- 입력이 다른 호출이라 graph 규칙상 '순수 함수 정의 하나 공유'(40 §2.4 머리)이고 새 필드·사본 0. (나) `ln_idu_set`을 두려면 그 점((L, VDS, VSB))을 칸에 함께 적고, R6가 다른 점에서 읽을 때는 (가)의 함수로 다시 내도록 규칙을 적는다. 어느 쪽이든 J2 근거 열과 42 D-TB1c 확인 항목(층 0 후보 L ≠ 출발 L toy)을 같이 고친다.

### M2. J7 `TieBreak(w4_root)` 유지 판단 -- 원칙 8이 배제한 근거 사용 + fail-closed 주장이 사실과 다름
- 자리: 41:639(§4.7-1 2), 41:1450(J7).
- 근거: (1) 유지 근거로 "IT-1 판정 PASS·문언 정정만이라 코드를 바꾸지 않고, 갈래는 새로 만드는 것이 아니며"를 든다 -- 원칙 8('지금 있다/승인됐다/바꾸는 비용'은 유지 근거가 아니다)이 명시적으로 배제한 근거다. (2) "색 유일성 불변식이 깨지면 기록으로 드러나는 fail-closed 자리(원칙 10)" -- as-built `TieBreak`은 기록만 하고 계속 진행한다(`E/sizing/s2_values.py:117` `TIE_ROOT = "w4_root"`, `writer_plan.py:21` "최소 색 후보가 둘 이상이면 `w4_root` 기록" -- 사실 확인 용도). 기록은 정지가 아니므로 fail-closed가 아니다. (3) "죽은 갈래라 test는 두지 않는다" -- 메모리 규칙(게이트는 '실제로 거부한다'를 test로 먼저 확인)과 어긋난다. (4) 대안 비교표가 없다(원칙 22).
- 수정안: 대안 셋 비교 후 결정 -- (a) 삭제(정의상 발동 0, 정의 하나), (b) 불변식 단언으로 교체(`dc_colour` 중복이면 `StructureUnresolvedError` 정지 + 주입 toy test -- 원칙 10을 실제로 만족), (c) 기록 유지. 권고 (b) 또는 (a); 계획 N6.5 범위 2가 이 판단을 design에 넘겼으므로 계획 개정은 불필요하다. card 귀속(IT-1 재판정 없이 TB-1 범위에 넣을지)도 함께 적는다.

## 2. minor

| # | 자리 | 지적 | 수정안 |
|---|---|---|---|
| m1 | 40:1377 (§3.10.6 '분류') | 삭제한 `floor_k`(40:1376 '옛 floor_k = max(b_k, ME_k)')를 다음 줄이 그대로 쓴다("m_k ≤ floor_k이면 활성"). 40:1378 '여유·바닥을 보고'도 `floor` 칸 삭제(40:1379)와 어긋남 -- 삭제 대상의 소비자 잔존 | `floor_k` → `b_k`, '바닥' → '분해능' |
| m2 | 41:2024 대 42:176 | 축소 격자 전수 대조 test 행이 '(slow, 9회로)'·'단계 A·B 정지 회로(current_reuse·ngcc·nmcnr)'로 남고, 42 D-P9는 'library 13'(O-181) -- 교차 참조 불일치. 40:2110(CMP-1 'v6.38 기준 9회로')도 같은 종류 | 41 §9 행을 'library 회로 전부(13 -- O-181)'로, CMP-1 괄호 갱신 |
| m3 | 41:516 (§4.2 고정 축) 대 41:1768 (§6.7-3) | §4.2는 B의 VGS를 `start.row`(ln IDu·L)에서 읽는다고 하나, §6.7-3·DEC-104 (3)(c)(O-151 DK1)는 `start.row`에 "B 선택값·B ln IDu 칸을 두지 않는다". 고리 밖 B(R7 (나))의 선택 ln IDu 정본 자리도 어느 절에도 없다 -- 기존 모순(v1.15.x)이나 이번 판이 516행을 고쳐 다시 단언했다 | B 값 출처를 `graph/start: loop_dep`(writer 역할 B)·`dc_coord` 등식(종속 B)·R7 (나) 선택값의 정본 자리로 적거나, 고리 밖 B 선택값 자리가 없으면 '정본 자리 없음 -- 계획부터'(graph 규칙 6)로 계획 개정 항목에 올린다 |
| m4 | 40:1112 (§3.7-4 (b)), J9(41:1452) | 고리 밖 ② '`GB5가 gm을 요구하는 소자`'를 R13 S 구조 술어로 읽은 것은 층 순서상 타당하나, 계획 DEC-95 (3)은 그 읽기를 `kvl_branch` ②에만 적었다 -- 계획 문언과 design 읽기가 다른 자리(원칙 17·24) | §5.12.8 '계획 개정 필요'에 P4로 추가(DEC-95 (3) 고리 밖 ②의 구조 술어 읽기) |
| m5 | 40:917 (`dependent_member` concept), 42:313 (D-TB1d) | 새 concept의 네 갈래(confirm 일치·confirm 불일치 정지 `structure_fact_mismatch`·override·orphan)의 확인 toy가 D-TB1d 확인 항목에 없다(이름 전단사 metamorphic만). library 사실 0건이라 실행 test로는 발동 0 -- '만들면 배선'·'게이트는 거부를 test로' | D-TB1d 확인에 concept 네 갈래 toy(정지 갈래는 red 먼저) 추가 |
| m6 | 40:449 (`theta_class` 행) | 층 확인이 패키지 순서(core < … < sizing)만 대조한다. 첫 소비자 `dc_writer_plan`이 같은 sizing 패키지 안에서 이 블록의 키를 import하므로 sizing 안 모듈 지도 층(`_module_map.py`, as-built `writer_plan.py` = sizing 둘째 층)도 `theta_class` < `writer_plan`이어야 한다 -- design에 미기재 | `E/_module_map.py` sizing 층 배정(예: `theta_class.py`를 `writer_plan.py`보다 아래 층)을 TB-1 범위 파일 목록과 함께 적는다 |
| m7 | design history H40-34(history 690행) | 커밋 목록이 여섯째까지이고 일곱째 `bc3b3572`(42 남은 O-186 문언)가 없다 | 일곱째 커밋 줄 추가 |
| m8 | 41:761 (IT-2 L11 (l-ⅰ) `graph.ss_circuit` 정준 순서) | 노드·소자 순서 '(`dc_colour`, 이름)'이 남음. `dc_colour`가 정점마다 유일(40 §2.4.8)이라 둘째 키는 정의상 공허이고 MNA 순서 치환은 해를 바꾸지 않아 결과를 정하지 않는다 -- O-189 위반 아님. 다만 같은 판에서 41:639·41:729를 '정준 위치'로 정정했으므로 문언 일관성 | 같은 '(구조 색, DEC-97 정준 위치) -- 둘째 키 공허' 문언 정정(동작 변화 0) |
| m9 | 41:1436 (§5.12.7 (d)) | '병합 순서 의존 소유 = N6.1 조건부 제작 함수(P6)'가 O-183으로 대체됐다는 표지가 없다(옛 승인 질문 기록 안이지만 현행 문언처럼 읽힘) | '(v1.16.0 -- O-183으로 대체, 병합 순서 규칙 표)' 표지 |

참고(지적 아님): 계획 문서 front matter `version: 6.38.4`(3행)인데 Status는 v6.38.5(11행) -- 계획 쪽 표기 불일치, design 판정과 무관(오케스트레이터 전달용).

## 3. 물리 판정표 (O-171)

| 항목 | 물리 결정자 | 식·근거 | 실측 | 판정 |
|---|---|---|---|---|
| θ 좌표 ln IDu·역산 키 하나(`vgs_for_current_density`) | VDS > 0에서 ID(VGS) 엄격 단조 | 41:471·40:116 | `gmid_multiroot.md` §2: nfet 비단조 0/8640, pfet gm/ID 비단조 72.5 %(ln ID 오목성 위반)이나 ID 자체는 단조 -- LUT 대 ngspice ≤ 1.1 % | 맞음 |
| gm/ID 순방향 조회·제약 행 해 집합(여러 구간) | gm/ID = d ln ID/dVGS, pfet 중간 반전 혹 | 41:871 | 위와 같음(진폭 중앙 0.88 %·최대 8.2 %) | 맞음 |
| 최소 폭 하한 ln IDu ≤ ln(ID·L/W_min) | W = ID·L/IDu | 41:1533 | 손유도 | 맞음 |
| 면적 조건 행 IDu ≤ I·L²/A_min(L, ln IDu) | W·L = I·L²/IDu ≥ A_min | 41:1624 | 손유도 | 맞음 |
| 헤드룸 위 끝 = 옛 gm/ID_lo, 속도 L 상한을 위 끝에서 | VDSAT·f_T가 반전 정도에 증가 | 41:1546·1638 | 손유도 | 맞음 |
| **GuardRow** (ln IDu 해 집합 칸) | 해 집합 = (L, VDS, VSB) 점 함수 | 41:871·1790·1756 | -- | **조건부(층 0에서 B의 L·VDS가 출발값과 같을 때만) -- M1** |
| **J1** S·F 출발 = S_d 아래 끝 | 아래 끝 = 집합 안 최소 전류 밀도(최소 VGS·VDSAT, 최대 W) | 계획 U-124 '위치 최대 = ln IDu 작은 쪽'(plan 303·2580), 41:1757 | nfet: 단조라 옛 'gm/ID 최댓값'과 같은 점. pfet: 혹(gm/ID 14~18, 아반전 평탄 25~30보다 낮음)이 아래 끝 근처에 걸릴 때만 gm/ID 최대점과 갈림 -- 차 ≤ 8.2 %(gm/ID)·VGS 수십 mV(§5.1: current_reuse +0.074~0.078 V, erfc +0.02~0.05 V). 출발값이라 판정 영향 없음(EP-7) | 조건부 맞음(원래 취지와 다름 후보 표지 적절 -- LA-1 변화표) |
| **J9** 고리 밖 ② = R13 S 구조 술어 | 쓰기 계획 S0 < GB5 gm 요구(S2) 층 순서 | 계획 DEC-95 (3)(kvl_branch ② 같은 읽기) | -- | 조건부 맞음(계획 문언 맞춤 필요 -- m4) |
| **J10** 어긋남 집계 base = 봉인 9 (i) 통과 후보 | 합격 θ에서 ID > 0 ⇒ θ 전도 집합 = 구조 전도 집합 | 40:1115, Q-S9(KCL 항등 0 전류 MOS는 양쪽 다 비전도) | -- | 맞음(조건: 봉인 9 (i) 예외 집합과 커널 창 '구조적 전도'의 정의 동일 -- M-6) |
| **J14** `trust_limits` 기준 = 분해능 | 잔차가 판정 분해능을 넘으면 분해값을 그 분해능으로 믿을 수 없음 | 40:1397, 41:445, DEC-74 판정 위치 불변 | -- | 맞음(기록만, 새 상수 0) |
| J4 사다리 floor = S_d 안 LUT VGS 칸 ln IDu 폭 최솟값 | 그 좌표의 LUT 격자 분해능 | 계획 V9 칸 폭 정의 | -- | 맞음 |
| J5 VGS_min·VDSAT_min = 정의역 최솟값 | ID(VGS) 단조 ⇒ 최소 ln IDu ↔ 최소 VGS | 41:1572·1583 | -- | 맞음 |
| 주파수 손계산 C 열(원칙 1) | f_T = gm/(2π·CGG), 극점 C_n = C 열 스탬프 | 41:927·1601 | -- | 맞음(as-built `cgs = cgg − cgd` 갈래 삭제 명시) |

## 4. graph 정본 판정표

| 변화 | writer 하나 | 정의 하나 | 새 사본 | 계획 근거 | 판정 |
|---|---|---|---|---|---|
| `device: theta_class` writer 이동(쓰기 계획 앞), X 칸 삭제 | `theta_class` 하나 | X = `dc_coord` 관계 둘째 칸 삭제(규칙 3 준수) | 0 | DEC-104 (3)(a)·O-187(plan 303) | 맞음 -- 단 sizing 안 모듈 층 미기재(m6) |
| `device: start.guard` = `GuardRow(g_lo, g_hi, ln_idu_set, sources)` | `start_intervals` 하나 | 경계와 해 집합은 다른 양 | 0 | DEC-104 (3)(b)·DEC-105 (5)(a) '순방향 제약 행' | **M1**(해 집합 칸은 계획 문언 밖 design 추가 + 점 의존) |
| `graph/start: loop_dep.b_ln_idu` 키 = writer 역할 B만 | R6 하나 | 종속 B ln IDu = 커널 고리 등식 단독 writer | 0 | O-187 'R6 값 대상 = writer 역할만' | 맞음 |
| `constraint_rows` + `measure_state`·`reason`, `EvalResult` 판정 칸 삭제 | search 제약 블록 하나(LA-1) | 미측정 = 같은 행의 칸(둘째 자리 없음), `state`(활성 여부)와 축 다름 기재 | 0 | 계획 LA-1 행 Q8 기본안(plan 1271 '행 안 상태 칸 unmeasured + 사유'), O-176 Ⅵ | 맞음 |
| `ly_point` 보존량 VGS(L2) | `ly_input`(as-built) → LI-1이 `dc_op` 직접 READS | 보존 칸 = VGS | 0(새 칸 없음, O-27 부채 유지·LI-1 해소) | O-186 (L2), LI-1 범위 (1)~(3)(plan 1834) | 맞음 |
| `structure.json` concept `dependent_member` | 사실 파일(선언 입력) → `writer_plan` READS | 고리 confirm / 고리 밖 override | 0 | DEC-64 (v2)(가)(나) 'ratified 선택 … 다르면 정지', DEC-95 (3) 'ratified 선택' 첫 키, N3 'J12 ratify → structure.json'(plan 96) | 근거 있음(정본 자리 신설 아님 -- 기존 ratify 저장소의 concept) -- 확인 toy 보강(m5) |
| `model_error` S0 필드·`model_error_ref`·`floor` 칸 삭제, 대조 기록 = oracle 판정 기록 record_id 참조 | -- | -- | 0(참조) | DEC-72 개정·O-178 | 맞음 -- 잔존 1건(m1 `floor_k`) |
| `current_symmetry` 'HC-1 한 길'(생산자 둘 기간) | HC-1 | -- | -- | 계획 검증 33 D-2 → HC-D·GC-D design 몫 표지 | 표지 적절(HC-1+GC-8 통합 병합이라 master 기간 0) |
| `vgs_for_gm_id`·gm/ID 축 곡선 삭제 | -- | gm/ID writer = `dc_op` 하나 | 0 | O-186 (A), M-TH1c | 맞음(잔존 언급은 모두 '옛·삭제' 표지 -- grep 전수) |

삭제 대상 잔존 grep(40·41·42): `model_error` 20·`e_m` 8 이상·`모델 오차` 25·`vgs_for_gm_id` 9·`OrderHints|order_hints` 7·`ft_curve` 등 7·`"X"` 1·`조건부 제작` 5·`먼저 병합되는` 5·`ME-1` 6·`l_owner_name_order` 5·`gm_id_out_of_interval` 2 -- 전부 '옛·삭제·재작성 범위·사용자 결정 원문 인용' 표지 줄. 표지 없는 현행 소비자 = `floor_k`(m1) 하나, 낡은 표지 = 41:1436(m9).

## 5. 원칙 점검

| 원칙 | 결과 |
|---|---|
| 1 C 열 | 맞음(41:927, 41:1601, 40:1964) |
| 2 e_m 폐지·oracle 닫기 | 맞음(40:1964·1376, 41:829·1965) -- `floor_k` 잔존 m1 |
| 3 DC/AC 분리 | 위반 없음(저항 C_par 소신호만 40:880) |
| 6 가장 일반적 꼴 | 출발 구간 tuple(J3) 맞음 / GuardRow 해 집합 고정점(M1) |
| 8 as-built 근거 아님 | **J7 위반(M2)** |
| 9 만들면 배선 | `theta_class` 첫 소비자 같은 card 배선 맞음, `dependent_member` 배선 맞음(확인 toy m5) |
| 10 fail-closed | J7 '기록 = fail-closed' 주장 틀림(M2) |
| 11 상수 발명 | 새 상수 0 확인(J4·J10·사다리·PM_FLOOR = atan(1) 유도 기존) |
| 12 회로 이름 | 규칙에 회로 이름 없음(실측 기록 줄 제외) |
| 17·24 계획 먼저·취지 다름 | §5.12.8 P1~P3 적절, P4 추가 필요(m4), J1·J14 표지 적절 |
| 25 이력 분리 | H40-33·H41-34·H42-04·H40-34 이동 적절, 커밋 목록 누락(m7) |

## 6. 범위 밖 항목 판정(작성자가 남긴 셋)

| 항목 | 이름이 결과를 정하나 | 판정 |
|---|---|---|
| `ss_circuit` 노드·소자 정렬 (dc_colour, 이름) | 아니다 -- `dc_colour` 정점마다 유일이라 둘째 키 공허, MNA 순서 치환은 해 불변 | O-189 위반 아님 -- 문언 일관성 m8 |
| `structure.json` 루프 id 이름 회전(40:919) | 아니다 -- 사용자 사실을 대응시키는 식별 표현(이름 사상과 사실 파일이 함께 바뀜), 선택·순서를 정하지 않음 | O-189 위반 아님 |
| DOF 표본 규칙(40:1776 R3 `dof_rank_sample_count` 대 41 §4.5·B1/B2 '같은 표본' 대 41:573 증거 규칙 n·⌈n/2⌉) | 아니다 -- 이름 무관 | 이번 판 범위 밖 유지 가능. 작성자 진행 기록에 '불일치' 자리가 적혀 있지 않아 구체 판정 불가 -- 자리 명시 요청 |

## 7. 머리·판

- 40·41·42 `version: 1.16.0`·`plan_version: 6.38.5` 일치, Status 세 문서 같은 판·base `31b042cd` 표기 일치.
- 42 §4 집계: FR·NFR 15 + DEC 85 + 설계 항목 223 = 323, 열 합 일치; 기계 계수(§3 상태 열) 대비 증분 = MISS +8·PART −1(새 7행 + D-GB7c) -- 서술과 일치.

## 8. 격리 확인

- 실행: `git -C <W> log/diff/show/status/rev-parse`, 파일 읽기·grep만. reset·checkout·stash·push 0.
- 종료 시 `git -C wt/design-v115 rev-parse HEAD` = `bc3b357260ffec92e27aae1be6c714232bba5c3a`, `status --short` 0줄, 브랜치 design/v115.
- 쓴 파일: 이 파일 하나(+ 세션 scratchpad 임시 파일).
