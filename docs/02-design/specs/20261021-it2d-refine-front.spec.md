---
id: 20261021-it2d-refine-front
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
approval: 20261021-it2-o67-scope
---
## 의도

- **절차(phase)**: 계획 DEC-86(285행)·N3.12 머리(669행)로 역할 분리 gate·spec card 흐름·merge_gate가 꺼졌다. 판정 = N6.3(매 변경 뒤 새 test 전체 실행, 작성자 ≠ test 작성자 WP-13, 약화 보고, 변경당 커밋 1) + 독립 측정·검증 agent이고 merge_gate가 아니다. 머리 블록은 형식 호환용이다(공통 문서 '절차 상태').

card IT-2d -- 다듬은 창·front. 범위: design 41 4.7-4 전부(`dc_window_refine`·끝 풀이 함수 하나·fail-closed 사유 셋·호출 자리 `refine_front_windows`·계수), 4.7-5 전부(`icm_window_metrics`·`IcmPort`·`IcmWindow`·`ls_swing` 새 서명·`metrics_aux` 합치기·`metrics_icm_front`·미수렴 front 처리·M7 경로·출력 전용 선언), 4.7-6 CONTRACT·소유표·모듈 지도. 계획 N6.6 범위 1(다듬은 창)·2·3, 완료 조건 (0)(1)(2)(3)(4)(7)(12)(a front·c·d). 앞 card = IT-2c. 이 card 판정 뒤 IT-1·IT-2 통합 병합 판정.

- 공통: card base·경로 접두·사용자 결정 원문·병합 관계·착수 조건·절차 상태·graph 단일 정본 계약 G1~G7 정의·정의 불능 code·판정 분해능·S-OS1/S-OS2·작성 전 실측 1~13·승인 기록 초안은 `docs/02-design/specs/20261021-it2-common.md`(옛 IT-2 단일 card 본문, 내용 불변)에 있다. 이 card는 그 가운데 아래 범위만 판정한다.
- 나눔 근거: 사용자 결정 O-69 (2)(2026-10-21) -- IT-2를 IT-2a(스냅샷 파생)·IT-2b(커널 창)·IT-2c(측정 구성)·IT-2d(다듬은 창·front) 넷으로, IT-1 code 위 같은 통합 브랜치, master 병합은 IT-1과 함께 한 번(O-19 (2)). 순서 IT-1 → IT-2a → IT-2b → IT-2c → IT-2d. 나눔은 판정 단위만 바꾸고 design·완료 조건은 그대로다.
- 이 card는 **동작 변경**(design 41 4.7-8). `E/` = `skills/analog-gmid-design/gmid_engine/`, `41:n` = design 41 v1.12.3 줄(master `468e6e73`); 현 base design 41 v1.12.4(master `0de6a34a`)에서는 735행 이상 +1 -- '(v1.12.4)' 표시 줄은 새 판 줄. 공통 문서 '동결 갱신' 참조.

## 관찰 가능한 계약

- `dc_window_refine`(새 블록, `E/sizing/window_refine.py` 진입점 `refine_input_windows`, writer `DC_WINDOW_REFINE_WRITER`) WRITES `("node", "dc_window_def_refined")` = `RefinedWindow(lo, hi, lo_end, hi_end, tol_v, criterion)`·`WindowEnd(x, v, reason)`, `criterion == "tol_judgement"`. READS = 41:758(`node.dc_window_cfg` 출발 창, `node.dc_window`·`node.dc_v` 없음). 쓰지 않는 포트 (a)~(d)(41:763). 끝 풀이 = 이 파일 비공개 함수 하나(`block_columns._refine_ends` 같은 변경에서 삭제), (i)(ii) 해 보관·(ii) 포화 확인, (iii)~(v) 사유, 대체값 0. 모듈 수준 `solve`·`k_max` import(주입 지점).
- `refine_front_windows(sctx, result) -> EvalResult`(새 `E/search/front_windows.py`): 봉인 통과 점에 `dc_window_refine` → `metrics_icm_front`, 반환은 parent·`sctx.cache`에 넣지 않음. 호출 = `slsqp_outer.accept`(`:153-156`, `state` 불변)·`find_front` `_point_record` 전(front·pending·unmeasured). 커널 평가·FD 열에서 부르지 않음. 끝 풀이 수 = perf `window_end_solves`(커널 계수·E_B·E_total 밖).
- `icm_window_metrics(ports, input_dc, config_undefined=()) -> IcmWindow`(새 `E/metrics/icm_window.py`): 41:779-786 규칙. `metrics_aux`가 `node.dc_window_cfg`·`graph.icm_config`·`node.dc_colour`로 **`graph.icm_config.tied_ports`를 뺀 입력 포트**(v1.12.4 gap G4, 41:780·789 v1.12.4 -- 묶인 포트가 없으면 입력 포트 전부)의 `IcmPort`를 만들어 부르고 `SwingIcmr`에 `dataclasses.replace`로 합침(형식 불변). `ls_swing(devices, rails, node_v, outputs, diff_outputs=False)` -- 입력 창 계산 삭제.
- `metrics_icm_front`(새 블록, `E/metrics/icm_front.py` 진입점 `icm_front`, writer `METRICS_ICM_FRONT_WRITER`, `SS_WRITES`) WRITES `("graph", "metrics_icm_front")`; 포트별 출처 = 다듬은 창 항목 있으면 그 칸, 없으면 `node.dc_window_cfg`; 출처는 `IcmWindow.sources` 참조. 포트 집합 = 커널과 같은 `tied_ports` 제외 집합(41:794 v1.12.4, G4 -- 이미 READS인 `graph.icm_config` 칸에서 거름, 새 칸·사본 없음). 구성 None → M7. 미수렴 front 처리(41:794).
- 판정 단언: L8 (a) 포트 집합 끝(41:811 v1.12.7 -- `tied_ports`의 반전 입력을 포함해 세 metric을 내면 red), L8 (b1)·(d) M7 metric 쪽(`icm_config_feedback_no_dc`·S-OS1 code(v1.12.7 새 code `icm_config_feedback_element_unsupported`도 같은 경로 -- 판 표시만 갱신, 재동결 O-85/O-86; 차동 출력 결합 code는 S-OS2 card 몫이라 뺌 -- 재동결 O-87)로 세 metric 정의 불능, 선언 `icm_margin_v` 제약 점 unmeasured -- L10 (h)와 같은 경로; 판 표시만 갱신·이 항목 추가 -- 재동결 O-81~O-83, 검증 N5), K3 (a)~(d), R1·R2, M1·M2(최종)·M3, W1, P (a)(b) 다듬은 창 쪽·(c)(d)(e), D metric code, L10 (h), L12 (a) front 쪽·(b) metric·(c)·(d).

graph 단일 정본 검사(이 card 범위 + 통합 최종): G1(`node.dc_window_def_refined` = `dc_window_refine`, `graph.metrics_icm_front` = `metrics_icm_front`; 끝 풀이 함수 하나; `saturation_window` 부르는 블록 셋 -- M2 최종; `window_refine.py`·`icm_front.py`에 G_vgs 걷기 0), G2(`front_cache` 0, `sctx.cache`에 다듬은 결과 0, `IcmWindow`에 `criterion`·`config` 칸 없음), G3(KVL·단일 입력 포트 다듬은 창 항목 0), G4(`IcmWindow.sources` 참조), G6(최종 표: 모든 IT-2 새 필드·칸 소비자 ≥ 1 또는 출력 전용 -- 출력 전용 = `graph.metrics_icm_front`, `RefinedWindow.criterion`, `IcmWindow.sources`, perf `window_end_solves`, `IcmWindow.model_error_ref`, `IcmConfig.transfer`), G7(K3 (c)·W1: 같은 θ 두 번째 graft, `computes` 증분 0).

정의 불능 code·S-OS1/S-OS2·판정 분해능 문언은 공통 문서 해당 절이 정본이다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.s2_values` | `RefinedWindow` | `RefinedWindow(lo, hi, lo_end, hi_end, tol_v, criterion)` |
| `gmid_engine.sizing.s2_values` | `WindowEnd` | `WindowEnd(x, v, reason)` |
| `gmid_engine.sizing.s2_values` | `DC_WINDOW_REFINE_WRITER` | 상수 `"dc_window_refine"` |
| `gmid_engine.sizing.s2_values` | `CRITERION_TOL_JUDGEMENT` | 상수 `"tol_judgement"` |
| `gmid_engine.sizing.s2_values` | `CRITERION_DEFINITION` | 상수 `"definition"` |
| `gmid_engine.sizing.s2_values` | `REASON_WINDOW_END_SOLVE_FAILED` | 상수 `"window_end_solve_failed"` |
| `gmid_engine.sizing.s2_values` | `REASON_WINDOW_END_K_MAX` | 상수 `"window_end_k_max_exhausted"` |
| `gmid_engine.sizing.s2_values` | `REASON_WINDOW_END_UNCONFIRMED` | 상수 `"window_end_saturation_unconfirmed"` |
| `gmid_engine.sizing.window_refine` | `*` | 신규 모듈: 블록 `refine_input_windows` |
| `gmid_engine.search.front_windows` | `*` | 신규 모듈: `def refine_front_windows(sctx, result) -> EvalResult` |
| `gmid_engine.metrics.icm_window` | `*` | 신규 모듈: `def icm_window_metrics(ports, input_dc, config_undefined=()) -> IcmWindow` |
| `gmid_engine.metrics.icm_front` | `*` | 신규 모듈: 블록 `icm_front`, 상수 `METRICS_ICM_FRONT_WRITER` |
| `gmid_engine.metrics.aux_types` | `IcmPort` | `IcmPort(net, v, lo, hi, tol_v, missing)` |
| `gmid_engine.metrics.aux_types` | `IcmWindow` | `IcmWindow(icmr_v, icm_margin_v, required_input_cm_v, window, v_icm, input_dc, icmr_resolution, margin_resolution, undefined, model_error_ref, sources)` |
| `gmid_engine.metrics.ls_swing` | `ls_swing` | `def ls_swing(devices, rails, node_v, outputs, diff_outputs=False) -> SwingIcmr` |
| `find_front 결과` | `perf `window_end_solves`` | 결과 칸 |

## 판정 유형 근거

red-green. 새 이름은 존재 부재 red(`ImportError`·`AttributeError` -- 00-common §8.1, '신규 시그니처' 표 대조), 행동 red는 시그니처 불변 진입점이 맡는다(새 키워드 직접 호출 `TypeError`는 red로 세지 않는다). 결정성 비트 동일은 감사의 equivalence 측정(같은 head 두 번).

## oracle 종류와 출처

(손) 이름 없는 toy 연결의 손계산(design 41 4.7-7), (식) design 식 그대로, (비교) 같은 스냅샷 필드로 부른 같은 순수 함수의 두 경로 같음, (독립) `RunCounters`·perf 증분·`git grep`. 피검 함수로 기대값을 만들지 않는다. SPICE 다리는 **보류**(card EO-1, 41:816).

## library 회로 적용 여부

적용(동작 변경). 감사가 9회로 변화표(원인 칸 = card 0 IT-0 기록 대비, 41:816 (1)~(7))·결정성·G-10 9회로 0을 잰다. 회로·소자·넷 이름 코드 0(EP-1).

## 거부해야 할 입력

- `RefinedWindow`는 `criterion` 없이 만들 수 없다(`TypeError`).
- 끝 풀이 실패·`k_max` 소진·(ii) 포화 미확인 끝 → 사유·`v` None, 대체값 0, 같은 성분 모든 입력 포트에 사유.
- test 주입은 `gmid_engine.sizing.window_refine.solve`·`.k_max`만(그 밖 내부 이름 금지).

## 무동작 판정 입력(무발동 값)

`SwingIcmr` 형식·결과 JSON 키·`swing_icmr` 보고 행 키·`RESOLUTION_FIELDS` 불변, run 레코드 키 불변(front 값 출처만 바뀜), `kernel_calls`·E_B 불변.

## 재현할 수치

design 41 예시(41:780): `icm_window_metrics((IcmPort("vin_n", 0.90, 0.35, 1.20, 1.2e-4, ()), IcmPort("vin_p", 0.90, 0.33, 1.18, 1.2e-4, ())), "pending")` → `icm_margin_v` = 0.28(vin_p), `icmr_v` = 0.83, `required_input_cm_v` = (0.90, 0.33, 1.18). 예시 리터럴 41:690.

## 결정 필요 항목

없음(U-1은 O-69 (2)로 결정). 착수 조건(공통 문서): IT-1 code 커밋, card 0 IT-0 기록. C-5는 해소됨(design 41 v1.12.4 735행 `_transfer_resolution`, 사용자 결정 O-72 (1)) -- IT-2c code 착수에는 대신 IT-2c 착수 실측 (a)~(c) 기록(공통 문서 'IT-2c 착수 실측')이 필요하다. 그 밖 design에 없는 판단은 멈추고 보고.

## code 작성자 멈춤 조건

- C-5 해소(IT-2c `_transfer_resolution` 비공개 함수 -- M7·`icm_inverting_port_unresolved` metric 경로는 IT-2c 출력을 읽을 뿐, 이 card는 분해능 함수를 만들지도 부르지도 않음).
- 미수렴 front 처리에서 `ss_constraint_rows`·`eps_sweep` 기존 규칙 밖 새 경로가 필요해 보이면 멈춤(41:794 '새 경로·새 칸·새 상태 없음').
- 층 0 front 후보 점 호출 자리는 LA-1 범위 12 -- 이 card는 진입점만(만들지 않음).
- 공통 멈춤: design에 없는 것을 정해야 하면 멈추고 보고(as-built 결정 금지), 정본 자리가 없으면 만들지 않는다(CLAUDE.md graph 단일 정본 규칙 6, 공통 문서 C-7). 범위 밖 하위 card의 일을 당겨오지 않는다.

## test 작성 주체 몫(code 주체는 고치지 않는다)

- `E/tests/sizing/test_s2_values.py`: `:70-75`(34 → 35, `dc_window_def_refined`), `:118-124`(`DC_TABLE`에 `("node", "dc_window_def_refined")` → `dc_window_refine`), `:127-128`(블록 WRITES = 표), `:97-106`(SS_TABLE에 `metrics_icm_front`) -- 표 확대.
- `ls_swing` 옛 서명 호출 test(착수 때 `git grep` 수 기록), `E/tests/metrics/test_aux_types.py:40` 그대로(새 타입 test 추가).
- 새 test: `tests/sizing/test_window_refine.py`, `tests/metrics/test_icm_window.py`, `tests/metrics/test_icm_front.py`, `tests/search/test_front_windows.py`.

## 작성 전 실측

공통 문서 '작성 전 실측' 1~13을 따른다. 이 card 사실(master `468e6e73`, 2026-10-21): `E/sizing/block_columns.py:663`(`_refine_ends`), `E/metrics/ls_swing.py:84`·`:107-118`, `E/metrics/metrics_aux.py:214·236·256-264`, `E/search/slsqp_outer.py:153-155`, `E/search/find_front.py:51·136-138`, 새 이름 엔진 0건. V3 규모(8): **미확인 (IT-1 code 뒤)** -- 착수 base(IT-1 code 뒤)에서 오케스트레이터가 `tools/gates/mutate_changed.py`로 채운 뒤 동결.
