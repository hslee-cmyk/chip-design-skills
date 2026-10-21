---
id: 20261021-it2c-icm-config
phase: PHASE_TBD
evidence_type: red-green
gate_change: no
approval: 20261021-it2-o67-scope
---
## 의도

card IT-2c -- 측정 구성. 범위: design 41 4.7-3b 전부(41:729-742 -- `ss_nodal`·`icm_config`·`kvl_sensitivity`·세 자리 factor 이전·커널 상태 이어받기·S-3 선언 되먹임 DC 망·멈춤 S-OS1/S-OS2 fail-closed). 계획 N6.6 범위 1(측정 구성)·완료 조건 (8)(10)(12)(b)(c 일부), 사용자 결정 O-50 G4·O-53 A-1·A-2·O-58 S-1~S-3·O-59 (1)·O-61 P3·P5·O-63 (4)·O-64 (1)·O-67 (5). 앞 card = IT-2b(`saturation_window`·`region_rows`·`node.dc_output_structure`·`Window` 칸).

- 공통: card base·경로 접두·사용자 결정 원문·병합 관계·착수 조건·절차 상태·graph 단일 정본 계약 G1~G7 정의·정의 불능 code·판정 분해능·S-OS1/S-OS2·작성 전 실측 1~13·승인 기록 초안은 `docs/02-design/specs/20261021-it2-common.md`(옛 IT-2 단일 card 본문, 내용 불변)에 있다. 이 card는 그 가운데 아래 범위만 판정한다.
- 나눔 근거: 사용자 결정 O-69 (2)(2026-10-21) -- IT-2를 IT-2a(스냅샷 파생)·IT-2b(커널 창)·IT-2c(측정 구성)·IT-2d(다듬은 창·front) 넷으로, IT-1 code 위 같은 통합 브랜치, master 병합은 IT-1과 함께 한 번(O-19 (2)). 순서 IT-1 → IT-2a → IT-2b → IT-2c → IT-2d. 나눔은 판정 단위만 바꾸고 design·완료 조건은 그대로다.
- 이 card는 **동작 변경**(design 41 4.7-8). `E/` = `skills/analog-gmid-design/gmid_engine/`, `41:n` = design 41 v1.12.3 줄(master `468e6e73`).

## 관찰 가능한 계약

- `ss_nodal`(새 블록, `E/metrics/ss_nodal.py` 진입점 `ss_nodal_system`, writer `SS_NODAL_WRITER`) WRITES `("graph", "ss_nodal")` = `NodalSystem(nodes, fixed, g, factor)`, `__canonical__` = `(nodes, tuple(sorted(fixed)), g.shape, g.dtype.str, g.tobytes())`, 모든 ndarray `writeable=False`. `icm_config`(새 블록, `E/metrics/icm_config.py` 진입점 `icm_config_window`, writer `ICM_CONFIG_WRITER`) WRITES `("node", "dc_window_cfg")`·`("graph", "icm_config")`. 둘 다 `SS_WRITES` 등록, 호출 자리 = `ss_evaluate.py:101`(`ss_dev`) 바로 뒤 `ss_nodal` → `icm_config`, 조건 = `if aux_requests or views`.
- 계산 = 41:734 (1)~(5): 반전 입력 식별(선언 → 선언, 없으면 T_p, 분해능은 공통 문서 '판정 분해능' -- C-5), follower 행((2) `roots` 쌍), KVL 고정 연립((3) `kvl_sensitivity` + `slope`), `as_is_single_input`((5), 입력 하나면 (3)보다 먼저), 창 끝 = `saturation_window` 호출(끝 식 재구현 0), 포트 창 = [min, max] ∩ 레일, P3 묶음 = 선언 포트 − `tied_ports`. 커널 상태 이어받기 (가)~(라)(41:736). 선언 되먹임 망 = `ss.circuit` 그대로, 절단 해면 `icm_config_feedback_cut`.
- 세 자리(`offset_analysis.py:69`·`offset_systematic.py:46`·`block_residual.py:73`)의 `nodal_factor(conductance_matrix(ss.circuit, size), fixed)`를 `NodalSystem.factor` 읽기로, `metrics_aux` READS에 `("graph", "ss_nodal")`.
- **되먹임 선언 출처(C-3 해소, (b′) -- `wt/_drafts/evidence/2026-10-21/it2_prereq_c3_analysis.md` Q1)**: `icm_config` extras의 spec 되먹임 선언 = `ss_evaluate`가 이미 받는 키워드 `noise_decl`(`NoiseDecl`)의 `.feedback`. 그 값의 정본 = graph 필드 `graph/s1v: noise_input_cells`(writer `noise_decl` 하나, `E/search/noise_decl.py:33-43`), 운영 호출자 `E/search/kernel.py:136`이 그 필드를 읽어 넘긴다(design 41:731 'extras … spec 되먹임 선언' 범위 그대로 -- 새 필드·새 슬롯·사본 없음). 구현 주의 셋:
  1. `NoiseDecl.feedback`의 세 상태 tuple(소자 있음)·`()`(소자 없음 = β=1 선언)·`None`(결정 대기·거부·미전달)을 design 4.7-3b (1)과 사용자 결정 O-68 (2)(DC 성분 없는 되먹임·미선언의 측정 구성)의 갈래에 대조해 사상한다 -- **대조가 맞지 않으면 멈추고 보고**(C-3a).
  2. `ss_evaluate`·`icm_config` 안에서 `ctx.base.value("graph", S1V_KEY, "noise_input_cells")`를 직접 읽지 않는다(투영 밖 읽기 = 입력 버전 누락) -- 반드시 extras로.
  3. `ss_evaluate(noise_decl=None)` 기본값(test 전용 경로)을 '선언 없음 = 정상'으로 바꾸지 않는다 -- `None`은 결정 대기 갈래(design fail-closed 갈래)를 따른다.
- 멈춤 S-OS1/S-OS2(O-67 (5)): `config` None, `undefined` = `icm_config_output_root_w3`/`icm_config_differential_output_structure` 하나, `node.dc_window_cfg` 항목 없음. O-67 (1)·O-68 (2)의 S-OS2 (나)는 계획·design 개정 뒤 후속 card(이 card 아님).
- 판정 단언: L8 (a)~(e)(41:810), L10 (a)~(g)(41:811), L12 (b) cfg 이어받기·(c) cfg 쪽, 커널 상태 이어받기 T-INH.

graph 단일 정본 검사(이 card 범위): G1(`graph.ss_nodal` = `ss_nodal`, `node.dc_window_cfg`·`graph.icm_config` = `icm_config` 자리 하나씩; 전회로 `conductance_matrix(ss.circuit` = `ss_nodal` 하나; `kvl_sensitivity` 정의·호출 하나; `icm_config.py`에 G_vgs 걷기·`_edges`·끝 식 0), G2(`IcmConfig`에 `output_structure`·`kvl` 칸 없음; 되먹임 출처는 extras 참조, `ctx.base` 직접 읽기 0), G3(KVL 고정·`as_is_single_input` 끝 = `node.dc_window_cfg` 한 칸), G6(`graph.ss_nodal` → `icm_config`·`metrics_aux`; `node.dc_window_cfg` → `metrics_aux`(IT-2d 배선 전에는 감사가 '소비자 대기' 기록)·`dc_window_refine`(IT-2d); `graph.icm_config` → IT-2d 소비자, `transfer` 칸 출력 전용; `node.dc_output_structure`·`node.dc_window` 상태 칸의 소비자 = 이 card의 `icm_config` -- IT-2b의 대기 기록 해소), G7(같은 입력 버전 `ss_nodal` `computes` 증분 0·WP-10 중복 인자 0).

정의 불능 code·S-OS1/S-OS2·판정 분해능 문언은 공통 문서 해당 절이 정본이다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.metrics.ss_nodal` | `*` | 신규 모듈: 블록 `ss_nodal_system`, 상수 `SS_NODAL_WRITER` |
| `gmid_engine.metrics.icm_config` | `*` | 신규 모듈: 블록 `icm_config_window`, `def kvl_sensitivity(nodal, drive, closure)`, 상수 `ICM_CONFIG_WRITER` |
| `gmid_engine.metrics.aux_types` | `IcmConfig` | `IcmConfig(config, inverting_port, tied_ports, transfer, undefined)` |
| `gmid_engine.metrics.aux_types` | `NodalSystem` | `NodalSystem(nodes, fixed, g, factor)` |

## 판정 유형 근거

red-green. 새 이름은 존재 부재 red(`ImportError`·`AttributeError` -- 00-common §8.1, '신규 시그니처' 표 대조), 행동 red는 시그니처 불변 진입점이 맡는다(새 키워드 직접 호출 `TypeError`는 red로 세지 않는다). 결정성 비트 동일은 감사의 equivalence 측정(같은 head 두 번).

## oracle 종류와 출처

(손) 이름 없는 toy 연결의 손계산(design 41 4.7-7), (식) design 식 그대로, (비교) 같은 스냅샷 필드로 부른 같은 순수 함수의 두 경로 같음, (독립) `RunCounters`·perf 증분·`git grep`. 피검 함수로 기대값을 만들지 않는다. SPICE 다리는 **보류**(card EO-1, 41:816).

## library 회로 적용 여부

적용(동작 변경). 감사가 9회로 변화표(원인 칸 = card 0 IT-0 기록 대비, 41:816 (1)~(7))·결정성·G-10 9회로 0을 잰다. 회로·소자·넷 이름 코드 0(EP-1).

## 거부해야 할 입력

- `NodalSystem` 배열 제자리 쓰기 → `ValueError`(L10 (f) -- `writeable=False` 뺀 변형에서 FAIL을 먼저 확인).
- 선언 되먹임 소자를 절단한 봉인점 해 → `icm_config_feedback_cut`(definitional).
- S-OS1·S-OS2 갈래 → 창 값 없이 code 하나(값이 나오면 red).

## 무동작 판정 입력(무발동 값)

`offset_*`·`block_residual` metric 값은 factor 출처만 바뀌어 9회로 비트 동일(감사).

## 재현할 수치

없음(toy 손계산은 test 주체 소유).

## 결정 필요 항목

없음(U-1은 O-69 (2)로 결정). 착수 조건(공통 문서): IT-1 code 커밋, card 0 IT-0 기록, 그리고 C-5 해소(IT-2c). 그 밖 design에 없는 판단은 멈추고 보고.

## code 작성자 멈춤 조건

- C-1(41:737, :833): spec 루프 절단(`E/authoring/spec_elements.py:19-22`)이 쓰기 계획·봉인점 망에 적용됨 → 멈춤(사전 근거: `E/sizing`에 `input_terminal_nets` import 0 -- 감사가 다시 잼).
- C-2(41:740): library 9회로·toy에서 구동 쌍 넷 ⊄ ac 접지 ∪ 입력 넷 → 멈춤.
- **C-3 해소됨**(위 (b′), 오케스트레이터 분석 2026-10-21) -- 남은 멈춤 C-3a: `NoiseDecl.feedback` 세 상태와 design 4.7-3b (1)·O-68 (2) 갈래 대조 불일치.
- C-5: 판정 분해능 정의 함수(계획 gb v6.24 -- 엔진 δV_out = S-19 정본 분해능 `MetricResult.resolution`, O-68 (1))가 master/통합 base에 병합되고 design이 그 함수 이름·자리를 정하기 전에는 반전 입력 식별의 분해능 비교를 만들지 않고 멈춤.
- C-6: S-OS1·S-OS2는 fail-closed code만, 일반형·S-OS2 (나) 만들지 않음.
- 공통 멈춤: design에 없는 것을 정해야 하면 멈추고 보고(as-built 결정 금지), 정본 자리가 없으면 만들지 않는다(CLAUDE.md graph 단일 정본 규칙 6, 공통 문서 C-7). 범위 밖 하위 card의 일을 당겨오지 않는다.

## test 작성 주체 몫(code 주체는 고치지 않는다)

- `E/tests/sizing/test_s2_values.py:97-106` `test_s2_writers_is_s1_plus_dc_table_exactly`(SS_TABLE에 `ss_nodal`·`icm_config` 두 필드) -- 표 확대.
- 새 test: `tests/metrics/test_ss_nodal.py`, `tests/metrics/test_icm_config.py`.

## 작성 전 실측

공통 문서 '작성 전 실측' 1~13을 따른다. 이 card 사실(master `468e6e73`, 2026-10-21): `E/metrics/ss_evaluate.py:101·107`, `E/sizing/s2_values.py:173`(`SS_WRITES`), 세 factor 자리 `offset_analysis.py:69`·`offset_systematic.py:46`·`block_residual.py:73`, `E/search/kernel.py:136-138`·`E/search/noise_decl.py:33-43`·`E/search/search_context.py:184`(C-3 분석 F3~F6), `icm_config`·`ss_nodal` 엔진 0건. V3 규모(8)는 착수 base(IT-1 code 뒤)에서 오케스트레이터가 `tools/gates/mutate_changed.py`로 채운 뒤 동결.
