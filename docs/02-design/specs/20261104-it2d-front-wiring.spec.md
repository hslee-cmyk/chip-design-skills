---
id: 20261104-it2d-front-wiring
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
---
## 의도

ICMR 세 metric을 `graph.icm_config` V_cm 칸에서 내고, 옛 입력 창 계산(`ls_swing`)을 지운다. 커널·front·보고가 같은 칸을 읽는다(O-109 C1). 용량만 결측인 점에서 DC metric을 정의한다(B77). 물리 결정자: 용량은 DC 망에 들지 않는다(DC/AC 분리, 원칙 3).

결정 덮개: O-109 C1, O-111·O-112·O-113, O-115·U-106, O-204 조건, O-215(**임시 -- 번복 가능**), O-225·O-226.

## 관찰 가능한 계약

interface card `20261104-it2d-front-wiring.interface.md` 전체.

## 재작성 범위(엔진 인용 = 지울·바꿀 자리, integ/it12 `b9351eac`)

| 자리 | 일 |
|---|---|
| `E/metrics/ls_swing.py:107-119`, 머리 문언 | 입력 창 계산·인자 삭제 |
| `E/metrics/metrics_aux.py:164-166` | 요청별 영역 분리 |
| `E/metrics/metrics_aux.py:264` | 새 서명 + `icm_window_metrics` |
| `E/metrics/aux_types.py:160-172` | `IcmPort`·`IcmWindow` |
| `E/metrics/registry.py` `_ROWS` | 영역 칸 |
| `E/metrics/pending_metrics.py:15-18`, `E/metrics/CONTRACT.md`(`:1238` 등) | 문언 |

계획 소비자 표의 `headroom_bound`는 대상 아님(다른 개념 -- 그대로).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.metrics.icm_window` | `*` | 신규 모듈: `def icm_window_metrics(config, ports, input_dc) -> IcmWindow` |
| `gmid_engine.metrics.aux_types` | `IcmPort`, `IcmWindow` | frozen dataclass |

## graph 단일 정본

(원칙 7, `fpga/CLAUDE.md` '★graph 단일 정본', 계획 N3.3 G0~G7·N6.3 '같은 입력 재계산 0')

* 새 graph 필드 0. `metrics_aux`는 `graph.icm_config`·`node.dc_window_cfg`·`graph.ss_nodal`·`graph.ss_circuit` READS.
* 영역 정본 = 서명 칸 하나, 분류 표·이름 목록 사본 0. DC 전도 결측 판정 = `ss_nodal` 하나.
* `IcmWindow`는 함수 반환이고 `SwingIcmr`로 합쳐진다(필드·사본 아님). 사본 칸 없음.
* front 전용 블록·다듬은 창 없음. 새 cache·memo·sctx 슬롯 0.
* 정본 자리가 없으면 만들지 않고 멈추고 보고한다.

## 소비자

| 새·바뀐 필드·def | 엔진 소비자 |
|---|---|
| `icm_window_metrics`, `IcmPort`, `IcmWindow` | `metrics_aux` |
| `MetricSignature.domain` | `metrics_aux` 결측 판정(첫 판정 소비자) |
| `node.dc_window_cfg`(IT-2c) | `_icm_ports` |
| `graph.icm_config`(IT-2c) | `metrics_aux` |

## 판정 유형 근거

동작 변경(O-34 (1)): 값 출처 변경, 용량만 결측 점의 DC metric 정의. 기준 = 원칙 2. 변화표 원인 칸은 B77과 `ls_swing` 삭제·cfg 배선을 나눈다(보류). SPICE 다리 보류.

## oracle 종류와 출처

(a) V_cm 손 값·구성으로 정해진 toy, 용량 값만 다른 대조 실행 비트 동일(용량이 DC 계산에 들지 않는 불변식). (d) 영역 표 = 사용자 결정 O-112.

## 거부해야 할 입력

저항 결측(모든 metric 정의 불능), 어휘 밖 영역(fail-closed), 측정 구성 None(세 metric 같은 code).

## library 회로 적용 여부

13회로 값·용량만 결측 봉인점 수는 **유보**(O-225). 판정 기록에 base sha와 보류 표지. held-out 0개라 A' 판정 정지.

## 무동작 판정 입력(무발동 값)

결측 없는 회로: `dc`·`ss` 판정 경로 값 불변. `swing_out_v` 값 불변.

## 재현할 수치

없음. 예시 수치는 interface의 합성 입력이고 설계값이 아니다.

## 결정 필요 항목

| 항목 | 물리 결정자 | 식·원문 | 실측 | 판정 |
|---|---|---|---|---|
| 없음 | -- | O-111~O-113·U-106 결정됨 | -- | -- |

## 원래 취지와 다름

* 영역 칸 relabel을 DE-1에서 옮김(승인 O-112), 보고 해석(O-113).
* 다듬은 창·front 블록 없음(승인 O-109 C1). 옛 card 범위 대부분 소멸.
* O-215 임시 판정. 알려진 한계: 공칭점 성능 spec은 창 끝을 보지 않는다(재검토 (9)).
* 변화표·SPICE 다리 유보(A-5·A-7).

## 절차

(계획 DEC-86이 남긴 넷 그대로, 정본 = 계획 N6.3)

1. 코드 작성 주체와 test·기대값 작성 주체 분리(WP-13).
2. 깨진 test·기준 약화는 숨기지 않고 보고.
3. 변경당 커밋 1.
4. 매 변경 뒤 새 test 체계(`gmid_engine/tests/`) 전체 실행.

* **판정 기록**: `.ai/verification/20261104-it2d-front-wiring.json`, 보류 표지 = V 칸 basis(A-10).
* **test 이의**: `docs/02-design/disputes/20261104-it2d-front-wiring.md`.

## 작성 전 실측

(2026-11-04)

1. 사실 재측정: `metrics_aux.py:160-166, :264`·`registry.py`·test 줄을 `git cat-file`·`git grep`으로 다시 쟀다. 계획 줄(`09c3dce2`)과 달라진 test 줄은 다시 잰 값으로 적었다(`test_pending_metrics.py`, `test_registry.py`).
2. 엔진 인용 용도: 재작성 범위뿐.
3. 이름 충돌: `IcmPort`·`IcmWindow`·`icm_window_metrics`·`test_it2d_` 0 파일(`scope_grep.txt`). 새 파일 `metrics/icm_window.py`·`tests/metrics/test_icm_window.py`는 규칙 H 짝. `tests/metrics/test_metrics_aux.py` 있음 여부는 test 주체가 확인(없으면 새로, `metrics_aux.py`와 짝).
4. 원칙 계약화: '분류 사본 0'을 T-B77c, '같은 칸'을 T-F로.
5. 쓰기 경로: 코드 ≠ test ≠ 판정.
6. 계획서 소비자: 지우는 이름은 `ls_swing` 인자뿐, design 41 §4.7-5에 새 서명. 옛 이름은 card 대체.
7. 미배선: 소비자 표.
8. 기존 test: interface 표. 약화 없음.
9. 승인 줄: 의도 절.
10. 범위 계약: diff 계약 없음.
11. test 이름: 접두 `test_it2d_`.
12. 같음 판정: dataclass 칸 비교, float 비교 허용은 손계산 산술(상수 비교는 정확값 예시).
13. red 모양: T-IW만 `ImportError`(신규 함수), 나머지 assertion.
14. 상수·회로 이름: 새 상수 0, 회로 이름 0.
