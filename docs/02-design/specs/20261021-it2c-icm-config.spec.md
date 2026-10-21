---
id: 20261021-it2c-icm-config
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
approval: 20261021-it2-o67-scope
---
## 의도

- **절차(phase)**: 계획 DEC-86(285행)·N3.12 머리(669행)로 역할 분리 gate·spec card 흐름·merge_gate가 꺼졌다. 판정 = N6.3(매 변경 뒤 새 test 전체 실행, 작성자 ≠ test 작성자 WP-13, 약화 보고, 변경당 커밋 1) + 독립 측정·검증 agent이고 merge_gate가 아니다. 머리 블록은 형식 호환용이다(공통 문서 '절차 상태').

card IT-2c -- 측정 구성. 범위: design 41 4.7-3b 전부(41:729-742 -- `ss_nodal`·`icm_config`·`kvl_sensitivity`·세 자리 factor 이전·커널 상태 이어받기·S-3 선언 되먹임 DC 망·멈춤 S-OS1/S-OS2 fail-closed). 계획 N6.6 범위 1(측정 구성)·완료 조건 (8)(10)(12)(b)(c 일부), 사용자 결정 O-50 G4·O-53 A-1·A-2·O-58 S-1~S-3·O-59 (1)·O-61 P3·P5·O-63 (4)·O-64 (1)·O-67 (5). 앞 card = IT-2b(`saturation_window`·`region_rows`·`node.dc_output_structure`·`Window` 칸).

- 공통: card base·경로 접두·사용자 결정 원문·병합 관계·착수 조건·절차 상태·graph 단일 정본 계약 G1~G7 정의·정의 불능 code·판정 분해능·S-OS1/S-OS2·작성 전 실측 1~13·승인 기록 초안은 `docs/02-design/specs/20261021-it2-common.md`(옛 IT-2 단일 card 본문, 내용 불변)에 있다. 이 card는 그 가운데 아래 범위만 판정한다.
- 나눔 근거: 사용자 결정 O-69 (2)(2026-10-21) -- IT-2를 IT-2a(스냅샷 파생)·IT-2b(커널 창)·IT-2c(측정 구성)·IT-2d(다듬은 창·front) 넷으로, IT-1 code 위 같은 통합 브랜치, master 병합은 IT-1과 함께 한 번(O-19 (2)). 순서 IT-1 → IT-2a → IT-2b → IT-2c → IT-2d. 나눔은 판정 단위만 바꾸고 design·완료 조건은 그대로다.
- 이 card는 **동작 변경**(design 41 4.7-8). `E/` = `skills/analog-gmid-design/gmid_engine/`, `41:n` = design 41 v1.12.3 줄(master `468e6e73`); 현 base design 41 v1.12.4(master `0de6a34a`)에서는 735행 이상 +1 -- '(v1.12.4)' 표시 줄은 새 판 줄. 공통 문서 '동결 갱신' 참조.

## 관찰 가능한 계약

- `ss_nodal`(새 블록, `E/metrics/ss_nodal.py` 진입점 `ss_nodal_system`, writer `SS_NODAL_WRITER`) WRITES `("graph", "ss_nodal")` = `NodalSystem(nodes, fixed, g, factor)`, `__canonical__` = `(nodes, tuple(sorted(fixed)), g.shape, g.dtype.str, g.tobytes())`, 모든 ndarray `writeable=False`. `icm_config`(새 블록, `E/metrics/icm_config.py` 진입점 `icm_config_window`, writer `ICM_CONFIG_WRITER`) WRITES `("node", "dc_window_cfg")`·`("graph", "icm_config")`. 둘 다 `SS_WRITES` 등록, 호출 자리 = `ss_evaluate.py:101`(`ss_dev`) 바로 뒤 `ss_nodal` → `icm_config`, 조건 = `if aux_requests or views`.
- 계산 = 41:734 (1)~(5): 반전 입력 식별(선언 → 선언, 없으면 T_p; 분해능 = `_transfer_resolution(system, volt, sense, injection=None) -> float | None` -- 이 파일 `E/metrics/icm_config.py` 안 비공개 함수 하나, 판정 |V_out| ≤ δV_out = |z_u|ᵀ|r|이면 `icm_inverting_port_unresolved`, 기록 `IcmConfig.transfer` resolution 칸(출력 전용); 정본 문언 design 41 v1.12.4 735행·공통 문서 '판정 분해능'), follower 행((2) `roots` 쌍), KVL 고정 연립((3) `kvl_sensitivity` + `slope`), `as_is_single_input`((5), 입력 하나면 (3)보다 먼저), 창 끝 = `saturation_window` 호출(끝 식 재구현 0), 포트 창 = [min, max] ∩ 레일, P3 묶음 = 선언 포트 − `tied_ports`. 커널 상태 이어받기 (가)~(라)(41:736). 선언 되먹임 망 = `ss.circuit` 그대로, 절단 해면 `icm_config_feedback_cut`.
- 세 자리(`offset_analysis.py:69`·`offset_systematic.py:46`·`block_residual.py:73`)의 `nodal_factor(conductance_matrix(ss.circuit, size), fixed)`를 `NodalSystem.factor` 읽기로, `metrics_aux` READS에 `("graph", "ss_nodal")`.
- **되먹임 선언 출처(C-3 해소, (b′) -- `wt/_drafts/evidence/2026-10-21/it2_prereq_c3_analysis.md` Q1)**: `icm_config` extras의 spec 되먹임 선언 = `ss_evaluate`가 이미 받는 키워드 `noise_decl`(`NoiseDecl`)의 `.feedback`. 그 값의 정본 = graph 필드 `graph/s1v: noise_input_cells`(writer `noise_decl` 하나, `E/search/noise_decl.py:33-43`), 운영 호출자 `E/search/kernel.py:136`이 그 필드를 읽어 넘긴다(design 41:731 'extras … spec 되먹임 선언' 범위 그대로 -- 새 필드·새 슬롯·사본 없음). 구현 주의 셋:
  1. `NoiseDecl.feedback`의 세 상태 tuple(소자 있음)·`()`(소자 없음 = β=1 선언)·`None`(결정 대기·거부·미전달)을 design 4.7-3b (1)과 사용자 결정 O-68 (2)(DC 성분 없는 되먹임·미선언의 측정 구성)의 갈래에 대조해 사상한다 -- **대조가 맞지 않으면 멈추고 보고**(C-3a).
  2. `ss_evaluate`·`icm_config` 안에서 `ctx.base.value("graph", S1V_KEY, "noise_input_cells")`를 직접 읽지 않는다(투영 밖 읽기 = 입력 버전 누락) -- 반드시 extras로.
  3. `ss_evaluate(noise_decl=None)` 기본값(test 전용 경로)을 '선언 없음 = 정상'으로 바꾸지 않는다 -- `None`은 결정 대기 갈래(design fail-closed 갈래)를 따른다.
- `IcmConfig.tied_ports` = 구성이 출력에 묶은 입력 포트(41:780 v1.12.4, 예 follower의 반전 입력) -- 이 card가 writer, 소비 = IT-2d `metrics_aux`·`metrics_icm_front`의 margin 포트 거름(gap G4, 공통 문서 'margin 대상 포트').
- **착수 실측**(공통 문서 'IT-2c 착수 실측', design 41 v1.12.4 834행, O-71·O-72 (1)): (a) `current_reuse_telescopic_ota` 봉인점 T_p·δA_num (b) 진짜 A = 0 대칭 사례 (c) 오라클 vntol·reltol을 감사가 code 착수 전에 기록. 잴 수 없으면 '미측정 + 사유' 기록 + code 착수 전 사용자 보고, 대체 측정 없음.
- 멈춤 S-OS1/S-OS2(O-67 (5)): `config` None, `undefined` = `icm_config_output_root_w3`/`icm_config_differential_output_structure` 하나, `node.dc_window_cfg` 항목 없음. O-67 (1)·O-68 (2)의 S-OS2 (나)는 계획·design 개정 뒤 후속 card(이 card 아님).
- 단일 출력 + DC 되먹임 없는 선언 되먹임(41:734 (1) v1.12.6 -- 재동결 O-81~O-83; v1.12.5 O-79/O-80의 kind 판정을 경로 판정으로 대체): 판정 = `icm_config.py` 비공개 `_dc_feedback_reaches(view, cut_nets) -> bool | None` 하나(방향 의존 그래프 BFS -- `device.dc_nets` 원소 중 kind ≠ `current_source` 양방향, MOS gate→drain·gate→source 한 방향, 레일·절단 넷 아닌 입력 포트 경유 금지, O(N), cache 없음, 측정 구성 선택·T_p 전), READS 추가 `device.kind`·`device.pins`·`device.dc_nets`·`node.is_rail`·`node.port_direction`(writer `s1_structure`). False → `config` None, `undefined` = `icm_config_feedback_no_dc` 하나; None(지원 kind 밖 원소) → `icm_config_feedback_source_unsupported` 하나; 두 갈래 모두 `inverting_port` = 절단 넷 포트, `tied_ports` = (), `transfer` 빈 값, `node.dc_window_cfg` 항목 없음, S-OS1·`icm_config_feedback_cut`보다 먼저. 입력 하나면 `as_is_single_input` 먼저(O-80 R2), 빈 선언 `()`은 판정 안 함.
- **파일 범위 추가**(재동결 O-81~O-83, 계획 N6.6 IT-2c (iii)·O-83 R-N1): `E/authoring/_feedback_cuts.py` 절단 넷 순수 함수 `feedback_cut_nets(terminals, input_nets)`(`gmid_engine.authoring` export), 호출부 `E/authoring/spec_elements.py:104`·`E/authoring/spec_views.py:101`·`E/metrics/noise_plan.py:48`·`icm_config`가 직접 호출, `def input_terminal_nets`(`_feedback_cuts.py:11`)·`def _input_side`(`noise_plan.py:28`) 삭제(래퍼 없음), 함수 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` 행 둘(순수 함수·판정 개념 행), 동작 동일성 test(41:812 (i)).
- 판정 단언: L8 (a)~(e)(41:811(v1.12.6)), L10 (a)~(g)·(i)(41:812(v1.12.6)), L12 (b) cfg 이어받기·(c) cfg 쪽, 커널 상태 이어받기 T-INH.

graph 단일 정본 검사(이 card 범위): G1(`graph.ss_nodal` = `ss_nodal`, `node.dc_window_cfg`·`graph.icm_config` = `icm_config` 자리 하나씩; 전회로 `conductance_matrix(ss.circuit` = `ss_nodal` 하나; `kvl_sensitivity` 정의·호출 하나; `_transfer_resolution` 정의 하나·`icm_config.py` 비공개(분해능 식 재구현·사본 상수 0 -- `git grep`); `icm_config.py`에 G_vgs 걷기·`_edges`·끝 식 0), G2(`IcmConfig`에 `output_structure`·`kvl` 칸 없음; 되먹임 출처는 extras 참조, `ctx.base` 직접 읽기 0), G3(KVL 고정·`as_is_single_input` 끝 = `node.dc_window_cfg` 한 칸), G6(`graph.ss_nodal` → `icm_config`·`metrics_aux`; `node.dc_window_cfg` → `metrics_aux`(IT-2d 배선 전에는 감사가 '소비자 대기' 기록)·`dc_window_refine`(IT-2d); `graph.icm_config` → IT-2d 소비자, `transfer` 칸 출력 전용; `node.dc_output_structure`·`node.dc_window` 상태 칸의 소비자 = 이 card의 `icm_config` -- IT-2b의 대기 기록 해소), G7(같은 입력 버전 `ss_nodal` `computes` 증분 0·WP-10 중복 인자 0).

정의 불능 code·S-OS1/S-OS2·판정 분해능 문언은 공통 문서 해당 절이 정본이다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.metrics.ss_nodal` | `*` | 신규 모듈: 블록 `ss_nodal_system`, 상수 `SS_NODAL_WRITER` |
| `gmid_engine.metrics.icm_config` | `*` | 신규 모듈: 블록 `icm_config_window`, `def kvl_sensitivity(nodal, drive, closure)`, 상수 `ICM_CONFIG_WRITER` |
| `gmid_engine.metrics.aux_types` | `IcmConfig` | `IcmConfig(config, inverting_port, tied_ports, transfer, undefined)` |
| `gmid_engine.metrics.aux_types` | `NodalSystem` | `NodalSystem(nodes, fixed, g, factor)` |
| `gmid_engine.authoring` | `feedback_cut_nets` | `def feedback_cut_nets(terminals, input_nets) -> tuple[str, ...]`(재동결 O-81~O-83) |

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
- 단일 출력(입력 둘) + DC 되먹임 없는 선언 되먹임(용량만, Cf + Rb(in−–레일), R(in−–레일)만) → 창 값 없이 `icm_config_feedback_no_dc` 하나(값이 나오면 red; 재동결 O-79~O-83).
- 지원 kind 밖 원소가 있는 DUT의 선언 되먹임 판정 → `icm_config_feedback_source_unsupported`(운영 경로는 S1이 먼저 멈춤; 재동결 O-81~O-83).

## 무동작 판정 입력(무발동 값)

`offset_*`·`block_residual` metric 값은 factor 출처만 바뀌어 9회로 비트 동일(감사).

## 재현할 수치

없음(toy 손계산은 test 주체 소유).

## 결정 필요 항목

없음(U-1은 O-69 (2)로 결정). 착수 조건(공통 문서): IT-1 code 커밋, card 0 IT-0 기록. C-5는 해소됨(design 41 v1.12.4 735행 `_transfer_resolution`, 사용자 결정 O-72 (1)) -- IT-2c code 착수에는 대신 IT-2c 착수 실측 (a)~(c) 기록(공통 문서 'IT-2c 착수 실측')이 필요하다. 그 밖 design에 없는 판단은 멈추고 보고.

## code 작성자 멈춤 조건

- C-1(41:737, :833): spec 루프 절단(`E/authoring/spec_elements.py:19-22`)이 쓰기 계획·봉인점 망에 적용됨 → 멈춤(사전 근거: `E/sizing`에 `input_terminal_nets` import 0 -- 감사가 다시 잼).
- C-2(41:740): library 9회로·toy에서 구동 쌍 넷 ⊄ ac 접지 ∪ 입력 넷 → 멈춤.
- **C-3 해소됨**(위 (b′), 오케스트레이터 분석 2026-10-21) -- 남은 멈춤 C-3a: `NoiseDecl.feedback` 세 상태와 design 4.7-3b (1)·O-68 (2) 갈래 대조 불일치.
- C-5 **해소**(design 41 v1.12.4 735행 `_transfer_resolution`, 사용자 결정 O-72 (1); 옛 문언 O-68 (1) 'S-19 `MetricResult.resolution`'은 O-71이 대체). 남은 멈춤: 그 함수를 `icm_config.py` 밖·공개로 두어야 할 것처럼 보이면(구조 규칙 A, 이동은 DE-1 몫), 또는 착수 실측 결과가 계획 N3.8 정의와 어긋나면 멈추고 보고.
- C-6: S-OS1·S-OS2는 fail-closed code만, 일반형·S-OS2 (나) 만들지 않음.
- **S-FB1**(재동결 O-81~O-83, 41:812 (a) v1.12.6): 계획 완료 조건 (10)(a) 측정 꼴(IT-0 LC `E/metrics` 정적 grep 0·`run_kernel` 구간 동적 호출 0)과 (10)(f)(`icm_config`·`noise_plan`의 순수 함수 직접 호출)가 충돌 -- 계획 정정 전 code 착수 금지.
- 공통 멈춤: design에 없는 것을 정해야 하면 멈추고 보고(as-built 결정 금지), 정본 자리가 없으면 만들지 않는다(CLAUDE.md graph 단일 정본 규칙 6, 공통 문서 C-7). 범위 밖 하위 card의 일을 당겨오지 않는다.

## test 작성 주체 몫(code 주체는 고치지 않는다)

- `E/tests/sizing/test_s2_values.py:97-106` `test_s2_writers_is_s1_plus_dc_table_exactly`(SS_TABLE에 `ss_nodal`·`icm_config` 두 필드)·`:127-128` `test_block_name_and_writes_match_table`(블록 WRITES = 표 -- `ss_nodal`·`icm_config` 블록) -- 표 확대(design 41:719 v1.12.4 '같은 test에 걸리는 IT-2 새 writer 전부').
- 새 test: `tests/metrics/test_ss_nodal.py`, `tests/metrics/test_icm_config.py`.
- 기존 test 확장(재동결 O-81~O-83): `tests/authoring/test__feedback_cuts.py`에 `feedback_cut_nets` 0·1·2 갈래 직접 단언(기존 공개 경로 단언은 그대로), `tests/metrics/test_noise_plan.py`는 그대로 green.

## 작성 전 실측

공통 문서 '작성 전 실측' 1~13을 따른다. 이 card 사실(master `468e6e73`, 2026-10-21): `E/metrics/ss_evaluate.py:101·107`, `E/sizing/s2_values.py:173`(`SS_WRITES`), 세 factor 자리 `offset_analysis.py:69`·`offset_systematic.py:46`·`block_residual.py:73`, `E/search/kernel.py:136-138`·`E/search/noise_decl.py:33-43`·`E/search/search_context.py:184`(C-3 분석 F3~F6), `icm_config`·`ss_nodal` 엔진 0건. V3 규모(8): **미확인 (IT-1 code 뒤)** -- 착수 base(IT-1 code 뒤)에서 오케스트레이터가 `tools/gates/mutate_changed.py`로 채운 뒤 동결.
