---
id: 20261021-it2b-kernel-window
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
approval: 20261021-it2-o67-scope
---

> **[상태 표지 2026-10-29] 완료 이력** -- IT-2b 판정 PASS(`integ/it12:.ai/verification/20261021-it2b-kernel-window.json`, code `431d2e7b`), master 미병합. 이 master 사본은 판정 전 동결본이다(판정본 = `integ/it12`: `Window` 칸 다섯, helper 이동 없음, (S4-나) 확정, 동작점 불일치 단언은 card EO-1). 이 card 산출 가운데 `node.dc_output_structure`(와 그 writer)는 현행 IT-2c가 지우고(계획 v6.38.4 N6.6 범위 6·N6.35 E-09, O-109 D4), 입력 창 측정 되풀이 경로(`k_max`·`unmeasured`/`unsettled`)는 card WB-1 범위 3a가 KVL 순서 창으로 다시 쓴다(N6.35 E-13) -- 재작성 범위 기록이며 보존 근거가 아니다(원칙 8). 본문은 기록이며 덧대지 않는다(O-169).

## 의도

- **절차(phase)**: 계획 DEC-86(285행)·N3.12 머리(669행)로 역할 분리 gate·spec card 흐름·merge_gate가 꺼졌다. 판정 = N6.3(매 변경 뒤 새 test 전체 실행, 작성자 ≠ test 작성자 WP-13, 약화 보고, 변경당 커밋 1) + 독립 측정·검증 agent이고 merge_gate가 아니다. 머리 블록은 형식 호환용이다(공통 문서 '절차 상태').

card IT-2b -- 커널 창. 범위: design 41 4.7-1a(출력 구조 분류 `node.dc_output_structure`), 4.7-2(`Window` 칸 셋·상태 어휘), 4.7-3 1~5(커널 창), 4.7-3a(창 경계 행 셋 `region_rows`, S4 갈래), 4.7-4 '공유하는 것'(helper `E/sizing/_helpers_dc_solve.py` 이동)·`saturation_window` 새 서명(4.7-3 2), 4.7-6 `fd_jacobian._steps`. 계획 N6.6 범위 1(커널 쪽)·완료 조건 (0)(7)(9)(12)(a 커널 쪽)·(b 상태). 앞 card = IT-2a. `_refine_ends` 삭제는 IT-2d(대체 함수와 같은 변경).

- 공통: card base·경로 접두·사용자 결정 원문·병합 관계·착수 조건·절차 상태·graph 단일 정본 계약 G1~G7 정의·정의 불능 code·판정 분해능·S-OS1/S-OS2·작성 전 실측 1~13·승인 기록 초안은 `docs/02-design/specs/20261021-it2-common.md`(옛 IT-2 단일 card 본문, 내용 불변)에 있다. 이 card는 그 가운데 아래 범위만 판정한다.
- 나눔 근거: 사용자 결정 O-69 (2)(2026-10-21) -- IT-2를 IT-2a(스냅샷 파생)·IT-2b(커널 창)·IT-2c(측정 구성)·IT-2d(다듬은 창·front) 넷으로, IT-1 code 위 같은 통합 브랜치, master 병합은 IT-1과 함께 한 번(O-19 (2)). 순서 IT-1 → IT-2a → IT-2b → IT-2c → IT-2d. 나눔은 판정 단위만 바꾸고 design·완료 조건은 그대로다.
- 이 card는 **동작 변경**(design 41 4.7-8). `E/` = `skills/analog-gmid-design/gmid_engine/`, `41:n` = design 41 v1.12.3 줄(master `468e6e73`); 현 base design 41 v1.12.4(master `0de6a34a`)에서는 735행 이상 +1 -- '(v1.12.4)' 표시 줄은 새 판 줄. 공통 문서 '동결 갱신' 참조.

## 관찰 가능한 계약

- `dc_writer_plan` WRITES에 `("node", "dc_output_structure")`(값 `"high_impedance"`|`"kvl_fixed"`, 출력 포트 넷만), `DC_WRITES` `DC_WRITER_PLAN_WRITER` 행 등록(MF-3), sizing CONTRACT `:14`·소유표 새 행. 계산 = 41:721(IT-1 뒤 `_edges`, `_TIE` 없음, W3 목표 넷은 F′ 아님, `dc_resistor_cycle` 정지 먼저). θ 무관(S0).
- `dc_columns`가 `node.dc_window`를 모든 입력 포트 + W4 뿌리에 쓴다: 뿌리 = A6 되풀이(커널에서 `_refine_ends` 부르지 않음), 뿌리 아닌 포트 = 같은 `input_windows` 호출의 해·감도로 두 끝 전압 [min, max] ∩ 레일, 선언 포트 묶음 = 같은 x 이동량 Δ(묶음 = 선언 포트 전부 -- θ 프레임은 측정 구성 없음), F 성분 미선언 포트 = `Window(None, None, 0, input_status="f_component_undeclared")`, 고립 입력 포트 = 뿌리 절차, 측정 실패 = 뿌리 `unmeasured`(뿌리 아닌 포트 항목 없음), 동작점 불일치 = 성분 전체 `op_mismatch`·`status_detail`, `tol_v` = 그 해 `tolerance`, A6 b·c = `unsettled`(y 범위는 그대로 씀).
- `Circuit.region_rows` 5원소 행 (가) sat (나) triode, (S4-나): `kind` ⊆ {`"sat"`, `"triode"`}, 공용 전도 판정 함수·V_on 역함수 호출 0(41:708). 착수 때 EO-1이 병합돼 있으면 (S4-가)로 card 재동결.
- `saturation_window(unknown, roots, values, gradient, rows, *, slope=None) -> (dlo, dhi, slope) | None`: 이동량 창, `roots` 원소 = 넷 또는 쌍 `(행 넷, 고정 넷)`, `slope`를 주면 감도 연립 없이 끝만(반환 slope = 받은 값), 끝 식 = 행마다 `slack + sign·(s_a − s_b)·Δ ≥ 0` 교집합(`kind` 안 씀).
- `fd_jacobian._steps`는 writer relation `free_window`(W4 뿌리)만 y 스텝에 씀.
- 판정 단언: OS (a)~(k)(41:727), K1·K2(41:799-800), P (a)(b) 커널 쪽(41:808), D 창·`op_mismatch` 상태(41:809), L12 (a) 커널 쪽(41:813 앞부분), L12 (b) `dc_window` 상태.

graph 단일 정본 검사(이 card 범위): G1(`node.dc_output_structure` writer = `dc_writer_plan` 자리 하나·권한표 행 하나 -- OS (j); G_vgs 걷기·`_edges` 호출은 `writer_plan.py`에만; 창 끝 식은 `saturation_window`에만), G2(새 cache·사본 0), G3(출력 구조는 S0 필드 하나, `w3_target` 표지 없음 -- W3 여부는 `node.dc_writer`), G6(`node.dc_output_structure` 소비자는 IT-2c·IT-2d가 배선 -- 이 card 단독 시점에는 **출력 전용 상태**를 감사가 기록하고 IT-2c 병합본에서 소비자 ≥ 1 확인; `node.dc_window` 새 칸 셋의 소비자도 IT-2c(`icm_config` 상태 칸)·IT-2d(`metrics_aux`)), G7(`dc_writer_plan` θ 무관 `computes` 증분 0 -- OS (i)).

정의 불능 code·S-OS1/S-OS2·판정 분해능 문언은 공통 문서 해당 절이 정본이다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.s2_values` | `Window` | `Window(lo, hi, constraints, input_status=None, tol_v=None, status_detail=())` |
| `gmid_engine.sizing.s2_values` | `OUTPUT_HIGH_IMPEDANCE` | 상수 `"high_impedance"` |
| `gmid_engine.sizing.s2_values` | `OUTPUT_KVL_FIXED` | 상수 `"kvl_fixed"` |
| `gmid_engine.sizing._helpers_dc_solve` | `*` | 신규 모듈: `Circuit`(as-built `block_columns._Circuit`, `region_rows(values)` 추가)·`solve`·`FAILURES` |
| `gmid_engine.sizing.input_window` | `saturation_window` | `def saturation_window(unknown, roots, values, gradient, rows, *, slope=None) -> tuple | None` |

## 판정 유형 근거

red-green. 새 이름은 존재 부재 red(`ImportError`·`AttributeError` -- 00-common §8.1, '신규 시그니처' 표 대조), 행동 red는 시그니처 불변 진입점이 맡는다(새 키워드 직접 호출 `TypeError`는 red로 세지 않는다). 결정성 비트 동일은 감사의 equivalence 측정(같은 head 두 번).

## oracle 종류와 출처

(손) 이름 없는 toy 연결의 손계산(design 41 4.7-7), (식) design 식 그대로, (비교) 같은 스냅샷 필드로 부른 같은 순수 함수의 두 경로 같음, (독립) `RunCounters`·perf 증분·`git grep`. 피검 함수로 기대값을 만들지 않는다. SPICE 다리는 **보류**(card EO-1, 41:816).

## library 회로 적용 여부

적용(동작 변경). 감사가 9회로 변화표(원인 칸 = card 0 IT-0 기록 대비, 41:816 (1)~(7))·결정성·G-10 9회로 0을 잰다. 회로·소자·넷 이름 코드 0(EP-1).

## 거부해야 할 입력

- `saturation_window`에 4원소 옛 행 꼴을 넣는 호출은 엔진에 0(새 꼴 5원소만).
- 다중 입력 뿌리 정지는 IT-1 몫(이 card는 그 정지를 전제로 뿌리 하나).

## 무동작 판정 입력(무발동 값)

θ 프레임 W4 y 범위(`node.dc_window` 뿌리 `lo`·`hi` -- as-built 식)와 `fd_jacobian` y 스텝 값은 입력 포트 항목 추가에도 9회로 비트 동일(감사).

## 재현할 수치

없음(toy 손계산은 test 주체 소유).

## 결정 필요 항목

없음(U-1은 O-69 (2)로 결정). 착수 조건(공통 문서): IT-1 code 커밋, card 0 IT-0 기록. C-5는 해소됨(design 41 v1.12.4 735행 `_transfer_resolution`, 사용자 결정 O-72 (1)) -- IT-2c code 착수에는 대신 IT-2c 착수 실측 (a)~(c) 기록(공통 문서 'IT-2c 착수 실측')이 필요하다. 그 밖 design에 없는 판단은 멈추고 보고.

## code 작성자 멈춤 조건

- 착수 때 S4 갈래 확인(U-2): master에 EO-1이 없으면 (S4-나), 있으면 멈추고 오케스트레이터가 card를 (S4-가)로 재동결.
- 4.7-1a 분류에서 계획에 없는 출력 갈래를 만나면 멈춤(S-OS1/S-OS2 fail-closed는 IT-2c).
- 공통 멈춤: design에 없는 것을 정해야 하면 멈추고 보고(as-built 결정 금지), 정본 자리가 없으면 만들지 않는다(CLAUDE.md graph 단일 정본 규칙 6, 공통 문서 C-7). 범위 밖 하위 card의 일을 당겨오지 않는다.

## test 작성 주체 몫(code 주체는 고치지 않는다)

- `E/tests/sizing/test_s2_values.py`: `:70-75` `test_dc_table_has_33_fields`(33 → 34, 이 card에서 `dc_output_structure` 한 행; IT-2d가 35로), `:118-124` `test_dc_writes_constant_matches_table`(`DC_TABLE`에 `("node", "dc_output_structure")` → `dc_writer_plan`), `:127-128` `test_block_name_and_writes_match_table`(블록 WRITES = 표), `:97-106` `test_s2_writers_is_s1_plus_dc_table_exactly`(DC_TABLE 확대분) -- 표 확대, 약화 아님.
- `E/tests/sizing/test_input_window.py`(옛 `saturation_window` 서명 호출).
- 새 test: `tests/sizing/test_output_structure.py`, `tests/sizing/test__helpers_dc_solve.py`, 커널 창은 기존 `dc_columns` test 파일.

## 작성 전 실측

공통 문서 '작성 전 실측' 1~13을 따른다. 이 card 사실(master `468e6e73`, 2026-10-21): `E/sizing/writer_plan.py:73`(WRITES 4필드), `E/sizing/s2_values.py:143·146·356`, `E/sizing/block_columns.py:143`(`_Circuit`)·`:225`·`:246`·`:560`·`:628`·`:691`, `E/sizing/input_window.py:26·48`, `E/search/fd_jacobian.py:54-55`, `E/authoring/spec_regions.py:16-17`(`REGIONS = (REGION_TRIODE,)` -- EO-1 미병합). V3 규모(8): **미확인 (IT-1 code 뒤)** -- 착수 base(IT-1 code 뒤)에서 오케스트레이터가 `tools/gates/mutate_changed.py`로 채운 뒤 동결.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20261021-it2b-kernel-window.spec.md`.
