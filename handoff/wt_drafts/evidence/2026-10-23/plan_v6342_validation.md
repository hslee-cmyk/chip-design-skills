# 계획 v6.34.2 검증 (plan/v6342 `50cf0a19`, 부모 master `5fae7366`)

- 작성 2026-10-23, 읽기 전용 검증 agent. 쓴 파일은 이 파일 하나다.
- 대상: `git -C wt/plan-v6342 diff 5fae7366 50cf0a19`와 `50cf0a19`의 plan 전문.
- 사용자 결정: `_drafts/user_decisions.md` O-111·O-112.
- 엔진: integ-it12 `09c3dce2`를 직접 열었다(HEAD 확인). 연 파일은 `metrics/registry.py`, `core/metric_signature.py`, `core/units.py`, `metrics/ss_evaluate.py`, `metrics/metrics_aux.py`, `metrics/ss_circuit.py`, `metrics/offset_*.py`, `authoring/dc_edges.py`다.

## 점수: 87 / 100

- 필수(G) 0, 권고(S) 2, 참고(N) 6.
- O-112의 relabel 범위, `offset_excess` = `dc`, `ff_gm_ratio` = `ss`, 영역 규칙 (i)(ii), 새 code 0은 빠짐없이, 다르지 않게 들어갔다.
- 사실 인용 다섯 가지는 코드와 모두 맞다.
- 감점은 두 곳이다.
  - 'DC 결측 여부'를 두 블록이 각자 판정한다(S-1, graph 규칙 1).
  - metric별 보고를 내는 규칙이 O-112 원문 '보고 항목은 결측 시 지금처럼 내지 않음'을 넘는다(S-2, 원래 취지와 다름 표시가 없다).

## 1. 사실 확인 (09c3dce2)

| 주장 | 결과 |
|---|---|
| `registry.py:39-65` 영역 값 | 맞다. `:56` `offset_in_sigma_mv`·`:57` `offset_excess`·`:58` `offset_sys_mv`·`:59` `mirror_ratio_sigma_pct`는 `ss`, `:60-62` `swing_out_v`·`icmr_v`·`icm_margin_v`는 `ls`, `:63` `ff_gm_ratio`는 `ss`, `:48-49` `supply_current_dc`·`power_dc_w`는 `dc`, `:50` `area_search_m2`는 `geom`이다. `required_input_cm_v`는 registry 행이 없다(`swing_icmr` 보고 칸, `metrics_aux.py:246-247`). |
| 영역 칸의 운영 소비자 0 | 맞다. 비test 엔진 소스에서 `.domain`을 읽는 metric 서명 자리는 `core/metric_signature.py:44-45` 어휘 검증뿐이다. 나머지 `.domain`은 `sctx.domain`·`CouplingVar.domain`처럼 다른 개념이다. 어휘는 `core/units.py:18` `DOMAINS = ("dc","ss","ls","geom")`이다. |
| `ss_evaluate.py:95-96` 요청 분할, `metrics_ss`에 DC metric 없음 | 맞다. `aux_requests` = 결과 형식 ∈ `AUX_TYPES`, `ss_requests` = view_kind 있음 ∧ aux 아님이다. view_kind 있는 비aux 행(`:39-46`·`:52-55`)은 모두 `ss`다. `dc` 두 행은 view_kind가 None이라 `metrics_ss`로 가지 않는다. |
| `metrics_aux.py:164-166` 결측이면 요청 전체 정의 불능, 보고 없이 조기 반환 | 맞다. `MetricBundle(…, (), (("missing_passives", …),), ())`로 보고 칸이 빈다. |
| `metrics_aux.py:224-239` 전달 뷰 보고 | 맞다. `for view in transfer_views` 안에서 FF 보고 캐시, `block_residual`, `nqs_ratio`, `ls_fields`(driving이 있을 때)가 나오고, `ls_fields`는 `c_slew_farad`를 내보낸다(`_ls_report`). metric별 보고는 `:240-251`의 `offset_contrib`·`swing_icmr`·`mirror_ratio`·`ff_gm_ratio`이고, 계산 캐시가 있을 때만 나온다. |
| `ss_circuit.py`는 값 없는 수동소자를 스탬프하지 않고 `missing`에 적는다 | 맞다(`:46-49` `continue`). 결측이 생기는 종류는 `LOOP_CUT_KINDS`(저항·커패시터)뿐이고, 다른 종류는 `_unsupported`다. |
| (13)(a) '같은 값'의 근거 | 성립한다. `offset_analysis`·`offset_systematic`은 `conductance_matrix`(용량 미포함)를, `mirror_ratio`는 gm/ID·σ만 쓴다. ICMR·스윙은 DC 창이다. 네 파일에 `capacitors`·`cgs` 같은 용량 칸 참조가 없다(grep 0). 커패시터 하나가 빠져도 `ss.circuit.mos`·`resistors`는 같다. |
| 술어 `is_dc_conducting_passive` | 아직 없다(head grep 0). design 41 v1.13.0이 IT-2c 몫으로 정했고, 기반 상수 `DC_CONDUCTING_PASSIVE_KINDS = ("resistor",)`(`authoring/dc_edges.py:11`)는 있다. 계획 문언 'IT-2c가 만든 술어'는 card 순서와 맞는다. |

## 2. 원칙 점검

| 원칙 | 판정 | 비고 |
|---|---|---|
| graph 단일 정본: 분류 | 통과 | 영역은 서명 칸 하나, metric 이름 목록 사본 0. (13)(c)가 단언한다. |
| graph 단일 정본: 술어 | 통과 | 술어 정의는 하나(IT-2c)다. |
| graph 단일 정본: 판정값 | **주의(S-1)** | '결측에 DC 전도 소자가 있는가'라는 같은 판정값을 `ss_nodal`(IT-2c)과 `metrics_aux`(IT-2d)가 각자 계산한다. 술어가 하나여도 같은 값의 생산자가 둘이다(규칙 1). |
| fail-closed: 어휘 밖 영역 | 통과 | (ii)로 막는다. `MetricSignature`가 적재 때 어휘 밖을 이미 거부하므로 이중 방어다. |
| fail-closed: 저항 결측 | 통과 | 모든 metric이 정의 불능이다. |
| fail-closed: 전달 뷰 보고 | 통과 | 결측이 하나라도 있으면 내지 않는다. `ls_fields`(용량 사용)는 이 갈래 안이라 fail-open이 아니다. |
| fail-closed: metric별 보고 | S-2 | 3-(나) 참조 |
| DC/AC 분리·O-29 (1) | 통과 | 영역 = 정의 SPICE 해석 종류(`.op` MC·`.dc` → `dc`)다. `ff_gm_ratio`는 사용자 결정으로 `ss`다. 이 metric은 conductance만 쓰므로 용량만 결측일 때 정의 불능이 되는 것은 보수 쪽이고 fail-open이 아니다. |
| DEC-103 | 통과 | 계산 틀 변경이 없다. |
| 상수 발명·새 code·회로 이름 | 통과 | 기존 어휘 `passive_value_undeclared`만 쓰고, 이름 분기가 없다. |
| 계획 먼저 | 통과 | IT-2d design 전에 계획을 개정했다. card 경계 이동은 O-112로 승인됐고 '원래 취지와 다름(작음)'이 붙었다. |

## 3. 작성자가 따로 판단한 두 곳

- **(가) VB-1 세 자리(1913·1915·1919)의 담당 card 이름 맞춤**: O-112에서 바로 따라 나온다. 타당하다.
  - O-112가 relabel 담당을 DE-1에서 IT-2d로 옮겼으므로, VB-1이 'DE-1 소비자 표와 같은 자리'·'DE-1과 같은 변경이면 한 번만'·'DE-1보다 먼저 병합되면'으로 가리키던 대상도 IT-2d가 된다.
  - 규칙(`offset_sys_mv` 칸은 한 번만 바꾼다, 먼저 병합된 쪽이 바꾼다)은 그대로다.
  - IT-2d 문단 (1)에 'VB-1이 먼저 병합되면 다시 바꾸지 않는다'가 있어 양쪽 문언이 짝을 이룬다.
- **(나) metric별 보고를 '계산된 만큼' 내는 것**: 기술적으로는 fail-open이 아니다. 그러나 O-112 원문과 어긋난다(S-2).
  - fail-open이 아닌 이유
    - `offset_contrib`·`swing_icmr`·`mirror_ratio`는 DC metric 캐시에서만 나오고, 그 계산은 용량을 쓰지 않는다(1절).
    - `ff_gm_ratio` 보고는 그 metric(`ss`)이 정의 불능이면 캐시가 없어 나오지 않는다.
    - `ls_fields`처럼 용량이 필요한 보고는 전달 뷰 갈래라 막힌다.
  - 어긋나는 점
    - 원문은 "보고 항목은 결측 시 지금처럼 내지 않음"이다. 지금은 결측이면 **모든** 보고가 비고, metric별 보고도 나오지 않는다(`:166`).
    - 계획은 이것을 'registry 행이 없는 전달 뷰 보고'로 좁혔고, metric별 보고는 낸다. 또 (13)(a)는 `required_input_cm_v`(보고 칸)를 '정의되고 같음'으로 단언한다.
    - 이 축소에 '원래 취지와 다름' 표시나 결정 근거가 없다.

## 4. 완료 조건 (13) 판정 가능성

- **(a) 판정할 수 있다.** 전제 단언(결측 ≠ ∅·DC 전도 소자 없음·결측 밖 정의 불능 사유 없음)이 공허함을 막는다. 보완점(N-1)이 둘 있다.
  - '같은 회로의 값과 같음'의 대조 실행을 '같은 θ·같은 봉인점, 커패시터 값만 선언'으로 정하고, 비교 기준(비트 동일 또는 허용치)을 적는다. 1절 근거대로라면 비트 동일을 기대할 수 있다.
  - `required_input_cm_v`는 보고 칸이라 S-2 결정에 따라 단언이 바뀐다.
- **(b) 판정할 수 있다.**
- **(c) 판정할 수 있다(조건부).** `metrics_aux`는 계산 분기를 이미 metric 이름으로 가른다(`:192-223` `if name in (...)`). 'metric 이름 비교 식 0'의 AST 대상을 결측 판정 함수(이름은 design)로 한정하지 않으면 기존 계산 분기 때문에 거짓 red가 난다(N-2).
  - registry 칸 단언은 줄 번호(`:56-62`)가 아니라 metric 이름으로 적어야 한다. VB-1이 먼저 병합되면 슬루 행 둘이 더해져 줄이 밀리고, `offset_sys_mv`는 base에서 이미 `dc`라 'base red'가 그 행에서는 성립하지 않는다(N-3).
- **(d) 판정할 수 있다.**

## 5. 충돌 점검

| 대상 | 판정 |
|---|---|
| IT-2c 범위·완료 조건 (10)(c)(ⅱ) | 충돌 없음. IT-2c는 `ss_nodal`·`icm_config`만 고치고 metric 결과를 단언하지 않는다(문언 유지). IT-1 + IT-2 master 병합이 한 번이라 잔존이 master에 나타나지 않는다는 서술도 맞다. |
| N3.3 | 충돌 없음. 영역은 registry 정적 서명이고 graph 필드가 아니다. 새 필드·cache 0. S-1 기본안도 기존 필드 `graph.ss_nodal`을 읽을 뿐이다. |
| `ls_swing` 삭제(IT-2d) | 충돌 없음. 같은 card 안이고 `swing_icmr` 보고 칸 출처만 바뀐다. 같은 card에서 두 변경이 겹치므로 design이 변화표를 원인별로 나눌 것(N-5). |
| DE-1 | 소비자 표(1630행)의 '영역 칸을 바꾸지 않는다'로 맞췄다. DE-Q3 결정 행(1659행)의 (가)안 '영역 칸만 dc로' 문구는 결정 기록이라 그대로 둬도 된다. DE-1이 그 뒤 계산법을 바꿔도 영역은 이미 `dc`라 영향이 없다. |
| VB-1 순서 | 양쪽 순서가 모두 처리돼 있다(1919행·IT-2d (1)). 줄 번호 문제는 N-3. |
| 영역 칸의 다른 소비자 | 엔진 안 0(1절). 다른 계획(oracle-portability 등)이나 test가 registry 영역 값을 단언하는지는 확인하지 않았다(N-6, 미확인). |

## 6. 발견 사항

### G: 0건

### S (승인 전 반영 권고)

- **S-1 'DC 결측 여부'의 생산자가 둘이다(graph 규칙 1)**
  - 위치: N3.8 'metric 결측 판정 -- 영역 규칙 하나' 중 '결측 소자가 저항인지 용량인지는 graph 열(소자 kind)을 READS로 읽어 가른다'. N6.6 'IT-2d -- B77' (2) '결측 소자 열은 `graph.ss_circuit`의 `SsCircuit.missing`과 graph 열(소자 kind)을 READS로 읽는다'.
  - 근거
    - IT-2c `ss_nodal`이 같은 술어로 '결측 ∩ DC 전도 ≠ ∅'를 판정하고, 그 결과를 `graph.ss_nodal`의 값(노달 계 / 정의 불능)으로 쓴다(N3.8 fail-closed).
    - IT-2d `metrics_aux`가 같은 입력으로 같은 판정을 다시 한다. 술어가 하나여도 같은 계산값을 두 자리에서 내는 것은 둘째 생산자다(CLAUDE.md 규칙 1).
    - `metrics_aux`는 이미 `graph.ss_nodal`을 READS로 읽는다. 기존 조립 자리 셋(`offset_analysis`·`offset_systematic`·`block_residual`)이 그 블록 안에서 `NodalSystem.factor`를 읽기 때문이다(N3.8 '엔진 쪽 계산 자리').
  - 수정 제안(기본안): 영역 `dc` metric의 결측 판정 입력을 '`graph.ss_nodal`이 노달 계인가(DC 전도 결측이면 정의 불능 값)'로 둔다.
    - `metrics_aux`는 `SsCircuit.missing ≠ ∅` 여부와 `graph.ss_nodal` 상태만 읽고 술어를 다시 부르지 않는다.
    - 술어 호출 자리 = `ss_nodal` 하나다.
    - 새 필드·칸·code는 0이다.
    - (13)(c)의 'DC 전도 술어 정의 1곳'에 '호출 1곳(`ss_nodal`)'을 더한다.
  - 원칙 점검: graph 규칙 1·4(참조 전달), fail-closed 유지, 새 필드 0 → 맞음
  - 대안: 같은 판정이 블록 안 지역 계산이라 허용된다고 보는 경우에는, 그 판단을 계획에 근거와 함께 적는다. 승인 예외 목록(N3.3·N3.5)에 없으므로 기본안이 원칙에 더 맞다.
- **S-2 metric별 보고를 내는 규칙이 O-112 원문을 넘는다(원래 취지와 다름 미표시)**
  - 위치: N3.8 'metric 결측 판정' 중 '결측이 하나라도 있으면 registry 행이 없는 보고 항목(전달 뷰 보고)은 내지 않는다', N6.6 'IT-2d -- B77' (2) '보고 항목'·'metric별 보고 … 계산된 만큼', 완료 조건 (13)(a) `required_input_cm_v`
  - 근거: O-112 원문 "보고 항목은 결측 시 지금처럼 내지 않음". 지금 동작(`metrics_aux.py:166`)은 모든 보고를 비운다. 계획은 보고를 전달 뷰 보고와 metric별 보고로 나누는 작성자 해석을 표시 없이 넣었다.
  - 수정 제안: 둘 중 하나.
    - (가) 원문대로 결측이면 보고 전부를 내지 않는다. (13)(a)에서 `required_input_cm_v` 단언을 빼고 '보고 없음'으로 바꾼다. 결정 원문과 fail-closed에 가장 가깝다.
    - (나) 작성자 해석을 유지한다면 '원래 취지와 다름(작음): metric별 보고는 그 metric이 정의되면 낸다 -- 근거 = 그 보고는 같은 DC 계산 캐시에서만 나오고 용량을 쓰지 않음(`metrics_aux.py:240-251`)'으로 표시하고 사용자 확인을 받는다.
  - 기본안은 (가)다. 사용자 결정 원문이 우선이고, (나)의 이득(결측 점의 보고 정보)은 판정에 쓰이지 않는다.
  - 원칙 점검: 원래 취지와 다른 판단 보고, 결정 원문 우선, fail-closed → 맞음

### N (참고)

- **N-1** (13)(a)의 대조 실행을 '같은 θ·같은 봉인점에서 커패시터 값만 선언'으로, 비교를 '비트 동일'(근거 1절)로 적는다. → 맞음(판정 가능성)
- **N-2** (13)(c) AST 측정 대상을 'design이 정한 결측 판정 함수'로 한정한다. `metrics_aux`의 기존 계산 분기(`:192-223` metric 이름 분기)는 대상 밖이다. → 맞음(거짓 red 방지)
- **N-3** (13)(c)와 IT-2d (1)의 registry 칸 단언을 줄 번호가 아니라 metric 이름별로 적는다. VB-1이 먼저 병합되면 `offset_sys_mv` 행은 'base red' 대상에서 뺀다(1919행 규칙과 같은 갈래). → 맞음
- **N-4** `ff_gm_ratio`는 conductance만 써서 용량만 결측이어도 계산할 수 있지만, 사용자 결정 O-112(`ss` 유지)로 정의 불능이다. 보수 쪽이라 fail-open은 아니다. 변화표의 '용량만 결측 점' 칸에 이 사실을 적어 두면 결과를 해석하기 쉽다. 결정 변경을 권하는 것은 아니다. → 맞음(사실 기록)
- **N-5** IT-2d 변화표에서 B77(정의 불능 → 정의됨)과 `ls_swing` 삭제·cfg 배선(값 출처 변경)을 원인 칸으로 따로 적는다(O-34 동작 변경, 같은 card 두 원인). → 맞음
- **N-6** 미확인: 다른 계획·test가 registry 영역 값을 단언하는지. 예를 들어 `tests/metrics/test_registry*`, oracle-portability가 영역을 인용하는 자리다. IT-2d 착수 때 grep해 test 갱신 주체(test 작성자)를 정한다. → 맞음

## 7. 미확인

1. 운영 13회로에서 용량만 결측인 봉인점의 수(계획도 '착수 때 잰다').
2. 다른 계획 문서·test의 registry 영역 값 인용(N-6).
3. design 41 v1.13.0에 IT-2d B77 몫으로 고칠 자리 전수 목록(계획 다음 단계).
