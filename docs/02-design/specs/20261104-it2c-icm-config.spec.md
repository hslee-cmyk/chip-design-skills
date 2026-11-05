---
id: 20261104-it2c-icm-config
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
---
## 의도

ICMR을 봉인 뒤 측정 구성 블록 하나가 봉인점 KCL로 잰다. 창 필드는 `node.dc_window_cfg` 하나, 경계 행은 포화·`triode` 영역 행뿐, 판정 여유 0이다. 물리 결정자 = servo 측정 구성(입력을 함께 움직이고 출력을 봉인점에 묶은 W·바이어스 고정 KCL)과 소자 영역 경계 VDS = VDSAT.

원칙 1(분해능으로 물리 경계를 정하지 않음, 손계산 선형 끝 '추정', 최종 oracle), 3(DC 양), 4(섭동 = KCL), 7, 8, 10, 11, 12를 전 범위에 적용한다.

결정 덮개: O-58 S-1·S-2, O-59, O-107·O-108·O-109, O-111(R 결측), O-115·O-116·O-117·O-118(2번 제외), O-204, O-205 (3), O-211 조건(영역 행 창), O-215(**임시 -- 번복 가능**), O-225·O-226. design 41 v1.16.3 §4.7-W + A-27.

**IT-2a·IT-2b 재작성 몫이 이 card에 든다**(계획 P:1341): IT-2b 판정본의 +tol_VDsat 행, `dc_output_structure`, 커널 비뿌리 항목, 쌍 roots.

## 관찰 가능한 계약

interface card `20261104-it2c-icm-config.interface.md` 전체. O-211 조건 (1)~(3)의 자리:
- (1) 정의 동일성(엔진 식 = oracle servo 식): `Circuit`·연립을 oracle과 같은 정의로 둔다. 대조 실행은 OP-5(보류 다리).
- (2) `graph.ss_nodal` writer 선행: 이 card가 만든다.
- (3) 용량 전용 노드: 갈래 5 `icm_capacitive_only_node`.

## 재작성 범위(엔진 인용 = 지울·바꿀 자리, integ/it12 `b9351eac`)

| 자리 | 일 | 근거 |
|---|---|---|
| `E/sizing/block_columns.py:247-268` `region_rows` | `Circuit`으로 이동, tol 항 삭제. tol 조회 `:258`과 None 갈래 삭제 | W1·W6, U-101 (가′) |
| `E/sizing/block_columns.py` `writer_head`·`declared_inputs`·`input_windows`·`port_window`·F 성분 상태 `:805` | 커널 비뿌리 항목 삭제(D1), 공용 이동 | O-109 D1, O-118 3번 |
| `E/sizing/input_window.py:58` | `root` 하나, 쌍 roots·묶음 갈래 삭제 | N6.6 범위 1 끝, v6.34 N-5 |
| `E/sizing/writer_plan.py:25, :77, :122, :269`, `E/sizing/s2_values.py:114, :119, :150`, `E/sizing/CONTRACT.md:16, :204`, `E/_module_map.py:596` | `dc_output_structure`·`_output_structure`·`OUTPUT_*`·F 성분 상수 삭제 | E-09, O-109 D4 |
| `E/metrics/ss_metrics.py:71, :379-394`, `E/metrics/metrics_aux.py:52, :92-105` | 조립 사본·코드 사본 삭제, READS로 | v6.34.1 |
| `E/metrics/ss_evaluate.py:101-112` | 블록 호출 추가 | W5 호출 자리 |
| `E/metrics/stamp_*`, `records`, `_helpers_nodal.py:26` | `g_ops`, `bound` | O-107 |
| `E/graph/views.py:66-85`, `E/graph/s1v_fields.py`, `E/graph/view_analysis.py`, `s1v_values` | `default_port` | O-118 6번 |
| 세 조립 자리(`offset_analysis`·`offset_systematic`·`block_residual`) | `graph.ss_nodal` READS | O-59 (1) |
| `Circuit` 생성자 속성 | 읽기 전용 값으로 둔다(`types.MappingProxyType(dict(...))`·tuple). G-8 새 키 0. 40 §2.4.10 "그런 클래스는 구조로 고친다". 값·쓰임 불변. 쓰기가 필요한 `override`는 `block_columns._Circuit`에 남긴다. | I2, GL-1 래칫 |
| `assets/library/{current_reuse_telescopic_ota,nmcnr_amplifier}.structure.json` `rule_hash` | `views.py`·`view_analysis.py`·`s1v_fields.py`·`s1v_values.py`를 고치는 커밋 안에서 줄만 재기록. 사실·connectivity 변경 0 | 완료 (14), A-33·A-34 |

**남겨 둠**(다른 card 몫 -- 고치지 않음): `dc_columns` 커널 입력 창 측정·`_interior_solution`·`_dyadic_ys`·`INPUT_STATUS_UNSETTLED` = WB-1 범위 3a. 봉인 7 +tol·`dc_seal_conduction`·`device.dc_off_current`·`dc_conduction_floor`·`linear_devices` = EO-1 §4.8. `search/cell_floor.py` = GC-7·EO-1. VDSAT READS = HC-S.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.metrics.icm_config` | `*` | 신규 모듈: 블록 `icm_config_window`, `kvl_sensitivity`, `_transfer_resolution` |
| `gmid_engine.metrics.ss_nodal` | `*` | 신규 모듈: 블록 `ss_nodal_system` |
| `gmid_engine.metrics.ss_circuit` | `ss_circuit_field` | 블록 |
| `gmid_engine.sizing._helpers_dc_solve` | `*` | 신규 모듈: `Circuit` |
| `gmid_engine.metrics.aux_types` | `NodalSystem`, `IcmConfig` | frozen dataclass |

## graph 단일 정본

(원칙 7, `fpga/CLAUDE.md` '★graph 단일 정본', 계획 N3.3 G0~G7·N6.3 '같은 입력 재계산 0')

* 새 필드: `graph.ss_circuit`(writer `ss_circuit`), `graph.ss_nodal`(`ss_nodal`), `node.dc_window_cfg`·`graph.icm_config`(`icm_config`). 권한표 행 넷. 다른 자리는 READS.
* 창 정의·판정은 같은 정의라 필드 하나(규칙 3, O-204 조건). `dc_window`와 축이 다르다: 측정 구성(θ 고정 대 W·바이어스 고정 KCL)과 판정 여유(순서 대 포화).
* V_cm 칸과 포트 끝은 정의가 다른 양(같은 끝 상태 평균 대 포트별 [min, max]).
* 재사용 = graph reuse와 S3 graft만. 봉인 뒤 층 블록이라 keep 밖, 같은 입력 버전이면 graft. 새 cache·memo·sctx 슬롯·값 사본 0.
* 래칫: 새 B 0이 원칙. `region_rows`의 봉인점 VDSAT 조회는 봉인 7과 같은 입력이고 해소 card = HC-S(W2 'HC-S부터'). 감사가 배정 기록을 남긴다.
* 정본 자리가 없으면 만들지 않고 멈추고 보고한다.

## 소비자

| 새·바뀐 필드·def | 엔진 소비자 또는 출력 전용 |
|---|---|
| `graph.ss_circuit` | `metrics_ss`, `metrics_aux`, `ss_nodal` |
| `graph.ss_nodal` | `icm_config`, `metrics_aux`(세 조립 자리) |
| `NodalSystem.g_bound` | `_transfer_resolution` |
| `node.dc_window_cfg` | IT-2d `metrics_aux._icm_ports`. 같은 통합 병합이라 master에 소비자 없는 상태 없음 |
| `graph.icm_config` | 같음 |
| `IcmConfig.pivot_a_e`·`pivot_resolution` | 출력 전용 -- 결과 JSON |
| `ViewS1v.default_port` | `icm_config` |
| `Circuit` | `dc_columns`, `icm_config` |

## 판정 유형 근거

동작 변경(O-34). 기준 = 원칙 2. E-0·정의 동일성. SPICE와 수치 일치는 기준이 아니다. e_m 없음. SPICE 다리 보류(A-5).

## oracle 종류와 출처

(a) 물리 불변식 toy와 소자 스탬프 손 조립 KCL + Schur 1칸. VDSAT는 LUT 원시 함수 직접(엔진 밖 데이터). (b) 조립 상쇄 toy는 정확 산술 참값 대조. 피검 `conductance_matrix`·`kvl_sensitivity`·`saturation_window`·`region_rows`를 기대값에 쓰지 않는다.

## 거부해야 할 입력

interface '갈래 순서' 1~5·7의 입력. 지원 밖 원소·bulk 미정. 어느 것도 빈 창·임의 끝으로 통과하지 않는다.

## library 회로 적용 여부

대상 = 13회로 전체(ICMR 판정 4회로, 나머지 기록). n/N·변화표·착수 실측 (a)(b)(d)(e)·`sf_pushpull` 재측정은 **유보**(O-225, N6.1 측정 게이트 '가'): 갈래 toy 유지, 판정 기록에 base sha와 '미완료(보류 다리)'. 용량 전용 노드 13회로 발동 0은 O-211 기록(agent 인용, 미재측정). held-out 0개라 A' 판정 정지.

## 무동작 판정 입력(무발동 값)

`graph.metrics_ss`·`graph.metrics_aux`의 `offset_*`·`block_residual` 값 비트 동일(세 자리 이전만). `graph.views` 값은 `default_port` 칸 추가로 지문이 13회로 모두 한 번 바뀌고 다른 칸 값 변화 0 기대(식별 칸 몫). 지문 변화는 동작 변경 칸.

## 재현할 수치

없음(회로 값 유보). `vdsat` 값은 LUT 출처.

## 결정 필요 항목

| 항목 | 물리 결정자 | 식·원문 | 실측 | 판정 |
|---|---|---|---|---|
| J1 행 꼴 = 5원소 유지 | 영역 행은 d–s 두 단자 | 일반 1차 행은 R0(gm·gds·gmb 항) 몫이었고 W2가 삭제 | 소비자 0(R0 삭제 뒤) | 맞음. 기본안 5원소. design 41 §4.7-3a 옛 줄·42 D-IT2 '행 꼴 일반 1차 행' 표지 대상 |
| J4 용량 전용 노드 code | DC 경로 없으면 전하 보존 극한, 정본 자리 없음(graph 규칙 6) | N3.8 조건 넷 (3), design 41 §4.7에 자리 없음 | 13회로 0(O-211 기록, 미재측정); `factor.floating`이 그 집합 | 조건부. 기본안 새 code `icm_capacitive_only_node`, 갈래 5. 계획 문언은 '기능 행'인데 O-211이 영역 행 창에도 건다고 함 |
| J5 cfg 띠 기록 칸 | 창 끝은 값 하나, 띠는 봉인점 판정 표지 | W1 '기록만', §4.8-3 `dc_seal_7` detail `indistinct` | -- | 맞음. 기본안 cfg 칸 0(소비자 0, 원칙 9). W5 띠 toy는 EO-1 §4.8로 |
| J6 `rule_hash` | -- | N6.6 완료 (14) | IT-1 범위 6도 같은 파일군(`scope_grep.txt`) | 결정됨(A-33·A-34): rule 파일을 고치는 커밋 안에서 줄만 재기록, T-RH, 감사가 diff·값 비교 근거 |

## 원래 취지와 다름

* O-206·O-211 기능 기준 필수 철회 -- O-215 임시, 재검토 항목 (9).
* 범위 확대: 조립 사본 정리 + `graph.ss_circuit` -- 계획 표지.
* 13회로 변화표·SPICE 다리·착수 실측 유보 -- A-5·A-7, 착수 실측 멈춤 조건이 LA-1 측정 시점으로 밀림.
* 봉인 7(+tol)과 창(여유 0)이 EO-1 병합 전까지 다른 경계를 쓴다. 봉인이 더 엄격해 fail-open 아님. 기간 표지.
* `off` 선언 행 toy 없음: `off` 칸 로더가 EO-1이라 대상 선언 0.

## 절차

(계획 DEC-86이 남긴 넷 그대로, 정본 = 계획 N6.3)

1. 코드 작성 주체와 test·기대값 작성 주체 분리(WP-13).
2. 깨진 test·기준 약화는 숨기지 않고 보고.
3. 변경당 커밋 1.
4. 매 변경 뒤 새 test 체계(`gmid_engine/tests/`) 전체 실행.

* **판정 기록**: `.ai/verification/20261104-it2c-icm-config.json`, 형식은 IT-1 card와 같다. 보류 표지 = V 칸 basis, 통과로 세지 않음(A-10).
* **test 이의**: `docs/02-design/disputes/20261104-it2c-icm-config.md`.

## 작성 전 실측

(2026-11-04, `scope_grep.txt`)

1. 사실 재측정: 위 표 줄 = `git cat-file -p integ/it12:...` 직접 읽기(`block_columns.py:247-268`, `ss_evaluate.py` 호출 순서, `metrics_aux.py:92, :160, :264`, `views.py:66-85`, `test_ss_types.py:102-105`, `test_s2_values.py:79`). 옛 card·계획 줄은 옮기지 않았다.
2. 엔진 인용 용도: 재작성 범위·소비자뿐.
3. 이름 충돌: `ss_nodal`·`icm_config_window`·`kvl_sensitivity`·`NodalSystem`·`default_port`·`g_bound`·`icm_capacitive_only_node`·`test_it2c_` 0 파일. `icm_config`·`IcmConfig` 1 파일(`test_writer_plan.py:688` 옛 부재 단언, 지울 OS test), `_helpers_dc_solve` 2 파일(`input_window.py:8` 문언, `test_block_columns.py:1383` 주석 -- 코드 정의 0). glob: 규칙 H(`structure_checks.py:979`)는 test↔원본 1:1, 새 test 파일 `test_icm_config.py`·`test_ss_nodal.py`·`test__helpers_dc_solve.py`가 새 원본과 짝.
4. 원칙 계약화: 여유 0을 T-L8a′로, 회로 이름 0을 role 맞바꿈 toy로.
5. 쓰기 경로: 코드 ≠ test ≠ 판정.
6. 계획서 소비자: `dc_window_def` 계획 13·graph-consumption 3·headroom-chain 3·40 2·41 9·42 1 -- 모두 W1 대체 표지 또는 삭제 문맥 확인은 표본, 전수는 병합 전 감사(HC·GC 문언은 그 card 몫). `_conduction_rows` 계획 3·41 7·42 1. `dc_output_structure` 계획 4·40 4·41 6·42 1.
7. 미배선: 소비자 표. cfg 소비자는 IT-2d 커밋이고 같은 통합 병합.
8. 기존 test: interface '고칠 기존 test'. 약화 없음 예상.
9. 승인 줄: 의도 절.
10. 범위 계약: diff 계약 없음.
11. test 이름: 접두 `test_it2c_`.
12. 같음 판정: `Window`·`IcmConfig` 칸 비교, ndarray는 `numpy` 비교, `Undefined` detail tuple.
13. red 모양: 신규 모듈 test의 `ImportError`는 신규 함수 조건으로 인정, 행동 red는 `ss_evaluate`·`dc_columns`·`build_s1v` 경유.
14. 상수·회로 이름: 새 수치 상수 0. 분해능은 float64 기계 상수 정의(O-107). 회로 이름 0.
