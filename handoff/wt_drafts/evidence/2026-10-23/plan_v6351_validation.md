# 계획 v6.35.1 검증 (plan/v6351 `fe5ad330`, base master `e6723f54`)

- 2026-10-23, 읽기 전용 검증 agent. 쓴 파일은 이 파일 하나다.
- 확인한 것
  - diff와 `fe5ad330`의 plan·history 전문
  - integ-it12 `1fa7b1e5`를 직접 열었다: `graph/s1v_fields.py`, `graph/views.py`, `graph/l_classes.py`, `metrics/achievability.py`, `metrics/CONTRACT.md`, `authoring/spec_constraints.py`, `graph/s1_values.py`
  - 13회로 sizing_spec

## 점수: 88 / 100

- 필수(G) 0, 권고(S) 1, 참고(N) 4.
- 정본 자리(S1v writer)와 선택 규칙 (i)~(vii), 13회로 결과, F 성분 포트, 레일 자름, (d) 영향 서술은 사실과 맞고 원칙에도 맞는다.
- 감점은 '같은 판정의 다른 자리'를 '다른 축'으로 처리한 근거 가운데 `achievability:348`에 대한 서술이 사실과 다른 점이다(S-1).

## 1. ICMR 전달 뷰 정본 자리 -- 맞다(graph 규칙 1·2·6)

- **as-built 확인**
  - `s1v_fields.py:251-256`: `judged` extras, `collect_views`, `gain_keys = _constrained_keys(model, judged, METRIC_GAIN_SS)`.
  - `:283-285`: `gain_views`는 `l_equivalence_classes`에만 넘어간다.
  - `:295`: 출력 다섯 필드에 gain 선택 결과가 없다. 계획 서술과 같다.
- **원칙**
  - writer 하나(θ 무관 base writer)이고 소비자는 `icm_config`·DE-1 (c)가 READS한다.
  - spec 로드 칸·`DcInputs`·extras로 다시 고르지 않는다.
  - 재사용은 graph reuse와 S3 graft다. 규칙 1·2·6에 맞는다.
- **'이미 계산하는 값'이라는 근거는 일부만 맞다.**
  - `_constrained_keys`(`:117-123`)는 mode `pending`을 거르고(`_VIEW_MODES`), 출처가 `VIEW_SOURCE_DECLARED`인 씨앗만 남긴다.
  - 규칙 (i)(결정 대기 뷰 감지)은 `gain_keys`만으로는 알 수 없다. 같은 writer 안에서 `judged`를 한 번 더 보는 지역 계산이 필요하다.
  - 입력(`judged` extras)은 이미 그 writer에 있으므로 새 입력이나 생산자는 없다. 문언만 다듬으면 된다(N-1).

## 2. 판정 입력·선택 규칙

- **(i) 결정 대기 뷰 → 정의 불능**: fail-closed로 맞다. as-built `_constrained_keys`는 pending을 걸러 '없음 → (iii) 기본 뷰'로 가므로 결정 안 된 MOD5를 가정하게 된다(fail-open).
- **S1v의 다른 소비자로 번지지 않는다.** 새 규칙은 새 값(ICMR 전달 뷰 선택 결과)에만 적용되고, `gain_keys`·`l_classes`·`("graph","views")` 값은 그대로다(계획 '선택 규칙 적용은 같은 writer 안 한 자리'). as-built `l_classes._main_path_starts`가 current_reuse에서 첫 전달 뷰로 대신하는 fail-open은 기존 동작으로 남는다(이 판 범위 밖, N-3).
- **13회로 결과**(spec 직접 grep, `human.constraints` metric `gain_ss_db`)
  - (ii) 9회로: ngcc·nmcnr·sf_pushpull·two_stage·cnr·erfc·r2r·rfc는 view 없음 + `user_spec`, two_stage_sf는 view 없음 + `reference`.
  - (iii) 3회로: common_gate·folded_cascode·pushpull_follower_buffer는 판정 gain 제약이 없다(common_gate·folded는 `pending_constraints`에 gain 하나씩, pushpull은 0). **gap 보고서의 '1회로'는 틀렸고 계획의 3회로가 맞다.**
  - (i) current_reuse: view `{"pending":"MOD5"}`, `user_spec`.
  - 로더 쪽 사실: view 없는 제약은 authoring `default_views`의 port 뷰(`_from_weights`, 출처 declared)가 되므로 `gain_keys`에 들어간다. (ii) 판정과 맞는다.

## 3. 다른 뷰 선택 자리 -- S-1

- `l_classes._main_path_starts`(`l_classes.py:49-52`): gain 뷰 중 첫째, 없으면 첫 전달 뷰다. L 동치류 주인을 정하는 할당 휴리스틱이므로 판정이 아니고, 여럿·없음을 대신 고르는 것이 이 용도에 필요하다. 축이 다르다는 주장은 성립한다.
- **`achievability.py:347-349`는 다르다.** gain 뷰 표지와 무관하게 `kind == "transfer"`인 첫 뷰를 고르고, `_gain_target(spec)`(`gain_ss_db >= G`)의 달성 가능성을 **판정**한다(GB4, 결과 `no_target` 등).
  - 질문이 'gain 제약의 전달 뷰에서 그 목표를 낼 수 있는가'이므로 DEC-23 판정 gain 뷰와 같은 양이다.
  - 계획의 근거 '분해·할당용 휴리스틱이고 판정이 아님'은 이 자리에 대해 사실이 아니다.
- block_residual도 `metrics/CONTRACT.md:1093`이 '첫 전달 뷰(L 동치류 gain 뷰 규칙과 같음)'라고 적은 gain 분해 잔차 보고다. 대상 뷰는 gain 뷰다(보고라서 판정은 아님).
- **판정**
  - achievability는 같은 입력·같은 질문인데 규칙만 다른 기존 둘째 생산자다(as-built 부채, 이 판이 만든 것은 아님).
  - 계획이 이를 '다른 축'으로 등록하면 graph 규칙 3의 축 기록이 사실과 맞지 않게 된다.

## 4. 레일 자름 -- 맞다

- 끝 상태 단위(어느 포트든 레일 밖이면 범위 밖)는 물리(레일 밖 입력은 정의 밖, DEC-96 (2))와 (8)(g)(포트 끝과 V_cm 끝이 같은 끝 상태)에 맞는다.
- O-49 P2와 as-built의 포트별 '창 ∩ 레일' 대비 '원래 취지와 다름(사용자 승인 대상)' 표시가 있다.

## 5. F 성분 미선언 포트 -- 일관된다

N3.8 603(구동에서 빼고 봉인점에 고정, 세 metric 정의 불능, O-61 P4 (b) (가) 유지), N6.6 1521, (vii) 'F 성분 미선언 포트 구동 제외' 셋이 같은 규칙이다.

## 6. (7)(b) 정정

- '창 끝 = servo 손계산 끝'은 판정할 수 있다((8)(a) 손 조립 KCL oracle과 같은 방식).
- 'x 구동 몫의 포트 차 = 선언 차'는 graph 출력만으로는 관측할 수 없다. cfg 항목은 포트 끝만 담고 x 몫과 ε 몫을 나누지 않는다.
- 관측 방법을 정해야 한다(N-2).
  - 예 1: 입력 공통모드 전달이 0인 toy(ε = 0)에서 포트 끝 차 = 선언 차.
  - 예 2: design이 구동 벡터를 test 가능한 함수 출력으로 둔다.

## 7. (d) S1v 값 변경의 영향 -- 맞다

- `("graph","views")` READS 소비자는 비test 엔진 소스에서 `coupling_vars.py:170`, `metric_structure.py:30`, `achievability.py:334`, `start_intervals.py:238`, `noise_decl.py:33`, `iv_context.py:91` 여섯이다(grep 일치).
- `S1V_WRITES`는 `s1_values.py:213`에 있다.
- 기존 칸으로 둘 때와 새 필드로 둘 때의 지문 영향 서술(스냅샷 지문 한 번 변경, 값 변화 0)은 맞다.

## 8. 원칙

| 원칙 | 판정 |
|---|---|
| graph 단일 정본 | 통과. 새 값 writer 하나. 단 S-1의 기존 둘째 생산자 서술 문제가 있다. |
| fail-closed | 통과((i)(iv)(v)(vi)(vii), F 포트) |
| DC/AC·DEC-103·상수 0·회로 이름 0 | 통과 |
| 만들면 배선 | 통과(소비자 `icm_config`·DE-1 (c)) |
| 계획 먼저 | 통과 |

## 9. 발견 사항

### G: 0건

### S-1 `achievability:348`(와 block_residual)을 '다른 축'으로 처리한 근거가 사실과 다르다

- **위치**: N3.8 'ICMR 전달 뷰 -- 정본 자리·선택 규칙'의 '같은 판정의 다른 자리' 문장
- **근거**: 3절. achievability는 gain 목표를 판정하므로 DEC-23 판정 gain 뷰와 같은 양이다. as-built는 gain 표지를 보지 않고 첫 전달 뷰를 쓴다(`achievability.py:347-349`). block_residual도 gain 분해 대상이다(CONTRACT 1093).
- **수정 제안**
  - (가) 문장을 둘로 나눈다.
    - `l_classes` 주경로는 할당 휴리스틱이라 다른 축이다(기록).
    - achievability(판정)와 block_residual(gain 분해 보고)은 같은 양인 기존 둘째 생산자다. 백로그로 올리고, 해소할 때 S1v 정본 값을 READS하도록 바꾼다고 적는다(이 판 범위 밖, IT-2c는 손대지 않음).
  - (나) 새 값의 이름을 'ICMR 전달 뷰'보다 '판정 gain 전달 뷰(DEC-23)'로 정하면 다른 소비자가 읽을 개념과 맞는다(design 몫, N-4).
- **원칙 점검**: graph 규칙 1·3(축 기록은 사실이어야 함), 계획 먼저(부채 기록), 범위 최소(이 판에서 동작 변경 없음) → 맞음

### N (참고)

- **N-1** '그 writer가 이미 계산하는 값으로 고르므로'를 '그 writer의 기존 입력(`judged`)과 계산(`gain_keys`)에 결정 대기 뷰 검사 하나를 더해 고르므로'로 정확히 적는다. `_constrained_keys`는 pending을 거른다(`:119`).
- **N-2** (7)(b) 'x 구동 몫의 포트 차 = 선언 차'의 관측 방법을 정한다(6절).
- **N-3** `pending_constraints`의 gain(common_gate·folded·ngcc·nmcnr)은 view 칸이 없으므로 결정돼도 view 없이 오면 기본 포트 뷰가 된다. 그래서 (iii)·(ii)의 선택은 결정 뒤에도 바뀌지 않는다. 이 근거를 '판정 입력' 문장에 적으면 (i)(결정 대기 뷰 = 정의 불능)과의 비대칭이 설명된다. as-built `l_classes`의 current_reuse 첫 뷰 대신은 기존 fail-open이며 기록만 한다.
- **N-4** 새 값 이름(위 S-1 (나)).
