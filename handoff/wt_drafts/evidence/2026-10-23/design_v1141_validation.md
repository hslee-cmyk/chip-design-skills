# design v1.14.1 독립 검증 (2026-10-23)

- 대상: `wt/design-v1131` `8f755b05`(부모 `045b77f5`). numstat은 40 = 15/15, 41 = 30/30, 42 = 6/6이고 줄 수는 그대로다.
- 정본: 계획 v6.36(같은 worktree), 사용자 결정 O-117·O-118·O-119.
- 엔진: integ-it12 `3179cd78`.
- 읽기 전용으로 했고, git은 `git -C`만 썼다.

## 점수: 89 / 100

계획 v6.35.1·v6.36의 IT-2c 몫은 빠짐없이, 다르지 않게 들어갔다.
- 기본 포트 뷰를 S1v에 늘 두고 `default_port`로 식별하며, `icm_config`는 READS만 한다.
- 전도 행 R0, 일반 1차 행 꼴, F 성분 포트 함께 구동, 끝 상태 레일 자름이 들어갔다.
- 완료 조건 (7)(b)·L8 (h)·L12 (b)가 들어갔다.

지운 것의 엔진 소비자도 계획대로 IT-2c 변경 안에서 정리된다. 감점은 계획 문언 두 곳이 design과 어긋난 채 남은 것 때문이다(S-1, S-2). 계획을 먼저 고쳐야 한다.

## 1. 계획 반영 대조

| 계획 | design | 판정 |
|---|---|---|
| 기본 포트 뷰를 늘 하나 둠, 식별 방법은 design, `icm_config`는 READS, `SizingSpecDoc.icmr_view`·`DcInputs.icm_view`·extras 없음 | 41:731(`collect_views` = 선언 씨앗 + 기본 씨앗, `setdefault`; 식별 칸 `ViewSeed/ViewS1v.default_port`; extras 둘), 40:533 | 일치 |
| 정의 불능 = 입력 셋 이상 / 기본 뷰 없음 / 하나로 안 정해짐 / 피벗 판정 불능 / DC 결측 | 41:734 ①~⑥ | 일치(code 어휘는 3절) |
| 전도 행 R0: 측정 구성 창·정의 창에만, I0 + k·Δ = `dc_conduction_floor`, READS `ss_dev`, 하한 고정 = '추정' | 41:716(4.7-3a 6), 731 READS(`ss_dev`·`dc_op`·`dc_conduction_floor`) | 일치. k 부호를 손으로 확인했다(NMOS dID = gm dVg + gds dVd + gmb dVb − Σ dVs, PMOS는 σ = −1로 같은 꼴) |
| 행 형태 = 일반 1차 행 | 41:695·705·799 (`(terms, slack, kind)`, 넷 쌍 꼴은 줄임, `saturation_window` 서명 그대로) | 일치 |
| F 성분 포트 KCL 함께 구동, θ 쪽 정의 불능 판단 유지, `input_window_f_component_undeclared` 삭제 | 41:697·700·734 (4)(ii)(vii)·786 | 일치(2절 (2)) |
| 끝 상태 레일 자름 | 41:734 (4)(v) | 일치 |
| (7)(b) 정정(일반 toy, 대칭 toy, 전제 단언 둘) | 41:809 | 일치 |
| (8)(h) 전도 행 단언(nmcnr형 toy, 차단 끝이 먼저라는 전제, 과보수는 기록만) | 41:811 (h) | 일치. 이름 없는 toy이고 oracle은 손 조립이다 |
| (12)(b) library toy(`test_block_columns.py:1159` 꼴) | 41:814 (b) | 일치. heldout r2r 인용은 0이다 |

## 2. 작성자가 짚은 세 곳

### (1) S1v 지문 영향: design 쪽 사실이 맞다. 다만 고른 근거 하나가 틀렸다. → S-2

엔진 근거:
- `collect_views`(`graph/views.py:77-84`)는 지금 `_declared(spec) or _default(model)`이다.
- `_constrained_keys`(`s1v_fields.py:117-123`, 호출 `:122`)는 gain·pm 키를 **`source == VIEW_SOURCE_DECLARED`** 씨앗에서만 모은다.

그래서 기존 칸 `source`로는 기본 뷰를 식별할 수 없다. 기본 씨앗을 먼저 두고 `source`를 DEFAULT로 바꾸면, 같은 키로 합쳐진 선언 뷰가 gain·pm 키에서 빠진다. GB4 gain 뷰와 L 주인 규칙의 값이 바뀐다. 새 bool 칸으로 식별하고 선언 씨앗을 먼저 두는 design의 선택은 맞다.

지문 문장:
- 계획은 "12회로 변화 0"이라고 썼다. 이것은 뷰 추가 몫만 센 것이다.
- `ViewS1v`에 칸이 하나 늘면 `fp_of` dataclass 직렬화(칸 이름 포함)가 바뀐다. 그래서 13회로 모두 `graph.views` 값 지문이 한 번 바뀐다. design의 사실 문장이 맞다.
- 어차피 `views.py` 등의 바이트가 바뀌어 S1v 규칙 지문과 코드 해시도 바뀐다.

"순서로 식별하면 GB4 첫 뷰 값이 12회로에서도 바뀐다"(41:731)는 **코드상 성립하지 않는다**.
- GB4(`achievability.py:347-348`)는 `views`에서 첫 `kind == "transfer"` 뷰를 고른다.
- 계획 착수 실측 (d)의 grep 사실로는 12회로가 view 미선언이다. 그래서 전달 뷰는 합쳐진 기본 포트 뷰 하나뿐이다. 순서 식별이든 키 정렬이든 첫 전달 뷰가 같다.
- 순서 식별을 피할 진짜 근거는 다른 데 있다. 의미를 자리(위치)에 싣지 않고 칸에 싣는다는 graph 규칙 3의 취지와, 선언 전달 뷰가 생기는 회로에서 GB4 첫 뷰가 바뀐다는 점이다.

### (2) θ `f_component_undeclared` 상태 값·상수·code 삭제: 계획 원문과 맞다

계획 v6.36 N6.6 범위 1에 이렇게 적혀 있다.
- "θ 틀에서는 그 포트에 창이 없다 … as-built `block_columns.py:804` `f_component_undeclared` 항목은 IT-2c D1로 지워지는 것 그대로이고 θ 쪽 '정의 불능' 판단은 유지"
- "KCL 측정 구성 판정 창에는 F 성분 상태 항목이 없다 … `input_window_f_component_undeclared`도 생산자가 없어져 두지 않는다(만들면 배선)"

엔진의 생산자는 `block_columns.py:805` 하나다. 소비자는 `s2_values.py:119` 정의 하나다. design 41:697의 "θ 쪽 판단 유지 = D1로 항목 없음"은 계획 문언과 같은 뜻이다.

### (3) 전도 행을 `region_rows` 밖에 둔 것: 동작은 맞지만 계획 정오가 필요하다 → S-1

계획 완료 조건 (9)(S4-나)를 보면 v6.36 R0 문단과 충돌한다.
- (b) "경계 행 종류 집합 = {포화, `triode`}(design 행 `kind` 집합)"
- (c)(ii) "경계 행을 만드는 함수 … `device.dc_conduction_floor` 읽기 0"
- v6.36 R0 문단은 이 둘을 고치지 않았다. 그런데 측정 구성 판정 창의 경계 행에는 이제 `"conduction"` 행이 있고, 그 행은 `dc_conduction_floor`를 읽는다.

design은 (9)의 대상을 `region_rows`로 좁히고 R0를 `_conduction_rows`로 떼어 문언을 맞췄다. (9)의 취지(EO-1 공용 전도 판정 함수·`off` 행을 미리 베끼지 않음)는 R0가 봉인 9 정본 값을 READS로만 읽으므로 깨지지 않는다. 그래서 설계 동작은 맞다. 다만 "(9)의 대상 함수 = `region_rows`, 전도 행은 별도"는 계획 문언에 없는 해석이다. 계획에 사실 정정 한 줄을 먼저 넣어야 한다.

## 3. 지운 것의 소비자 (`3179cd78` grep, tests 포함)

| 이름 | 엔진 | 판정 |
|---|---|---|
| `icm_view_ambiguous`·`icm_excite_common_mode` | 0 | 구현된 적 없음 |
| `no_input_port` | `authoring/ports.py:71`(로드 규칙 -- 다른 자리), `metrics/ls_swing.py:88`(IT-2d가 입력 창 삭제) | `icm_config` 갈래 삭제와 무관하다. `icm_window_metrics` 갈래 삭제(41:786)는 ③ `view_required`가 먼저 걸려 도달 0이다. 맞음 |
| `INPUT_STATUS_F_COMPONENT_UNDECLARED` | 정의 `s2_values.py:119`, 생산 `block_columns.py:805`(D1로 삭제) | 맞음. tests `test_block_columns.py:1161-1168`·`test_s2_values.py:227-228`이 그 값을 단언·생성한다 → N-1 |
| `Circuit.writer_head` | `block_columns.py:239`(정의)·`:803`(F 갈래 호출, D1로 삭제) | 맞음 |
| extras 셋째 원소(`icmr_view`·`icm_view`) | 0(구현된 적 없음) | 맞음 |

`icm_excite_common_mode` 도달 0의 근거도 확인했다. `_default`(`views.py:64-73`)는 차동쌍일 때 가중 ±1/|D|를 준다(합 0이라 CM 방향 (1, 1)과 평행일 수 없다). 차동쌍이 아닌 2입력은 입력마다 뷰를 내므로 ④ `view_required`, 1입력은 `as_is_single_input`이다. 그래서 기본 뷰만 쓰는 한 도달 0이다. 계획 정의 불능 목록에는 'e ∥ CM'이 남아 있으므로 계획 쪽 정리가 필요하다(N-2).

## 4. 새로 만든 것

- **`ViewSeed.default_port`·`ViewS1v.default_port`**
  - writer 하나: 생산 자리는 `collect_views`(호출자 `s1v_fields.py:122·254`)와 `analyze_view`(`view_analysis.py:217`, 칸 옮김)다. 둘 다 S1v 블록 `s1v_fields` 안이라 writer 하나다.
  - 루프 씨앗(`view_analysis.py:225`)은 기본값 False다.
  - `_constrained_keys`의 키 집합은 바뀌지 않는다. 선언이 먼저이고, 기본만 있는 키는 DEFAULT 출처라 원래대로 빠진다.
  - 적합.
- **정의 불능 code 어휘**
  - ① 기존 `passive_value_undeclared`
  - ② `icm_inputs_unsupported`(v1.14.0에서 수용)
  - ③④ 기존 `view_required`(고칠 자리가 포트 role·topology로 같다)
  - ⑥ `icm_servo_pivot_unresolved`
  - 새 code 순증은 0이다. 적합.
- **`sizing.__all__` 일곱 이름**(`Circuit`·`saturation_window`·`INPUT_STATUS_MEASURED`·`INPUT_STATUS_UNMEASURED`·writer 상수 셋): metrics가 쓰는 공개 이름만 있고 층 방향 4 ← 5가 맞다. 적합.

## 5. 원칙 점검

- graph 단일 정본: 적합. 뷰 정본 = S1v writer 하나. R0는 봉인 9·`ss_dev` READS이고 새 필드·cache가 없다.
- fail-closed: 적합.
- DC/AC 분리: 적합. 전도 행은 DC 양이다.
- DEC-103: 적합. KCL 섭동이다.
- 상수 0: 적합. `|rate| ≤ eps` 기존 건너뜀의 단위 차이는 사실로 기록돼 있다.
- 회로 이름 0: 적합. nmcnr형 toy는 이름 없는 toy다.
- 만들면 배선: 적합. 생산자·소비자가 0인 것을 지웠다.
- heldout 미사용: 적합. r2r 인용 0.
- 계획 먼저: S-1·S-2가 남았다.

## 6. 지적

### G
없음.

### S
- **S-1. 완료 조건 (9)(S4-나)(b)(c)를 계획에서 정정해야 한다.**
  - 위치: 계획 N6.6 완료 조건 (9), design 41:716·810.
  - 근거: 2절 (3). v6.36 R0가 측정 구성 창 경계 행에 `"conduction"`을 더했는데 (9)(b)·(c)(ii)의 문언은 그대로다. design이 대상 함수를 `region_rows`로 좁혀 문언을 피했다.
  - 수정안: 계획 (9)에 사실 정정 한 줄을 넣는다. "(b)(c)의 대상 = 선언 영역 행 함수(`region_rows`); 측정 구성 창의 전도 행 R0는 봉인 9 정본(`dc_conduction_floor`) READS라 대상 밖." 범위는 그대로다. 그 뒤 design 문언을 유지한다.
  - 원칙: 계획 먼저.
- **S-2. S1v 지문 문장과 식별 근거를 맞춰야 한다.**
  - 위치: 계획 N6.6 착수 실측 (d)의 '변화 0', design 41:731.
  - 근거: 2절 (1). 식별 칸 때문에 13회로 `graph.views` 지문이 한 번 바뀌는 것이 사실이다. 계획 문장은 뷰 추가 몫만 적었다. design이 순서 식별을 버린 근거("GB4 첫 뷰가 12회로에서 바뀜")는 12회로의 전달 뷰가 하나라서 성립하지 않는다.
  - 수정안: 계획 (d)에 "식별 칸으로 13회로 `graph.views` 지문이 한 번 바뀜(값 변화 0)"을 더한다. design 41:731의 근거는 다음으로 바꾼다.
    - `source`는 `_constrained_keys`가 선언 출처로 쓰는 칸이라 식별에 다시 쓸 수 없다.
    - 순서에 뜻을 실으면 선언 전달 뷰가 생기는 회로에서 GB4 첫 뷰가 바뀌고 의미가 위치에 숨는다(graph 규칙 3).
  - 원칙: 계획 먼저, 사실 정확성.

### N
- **N-1.** `INPUT_STATUS_F_COMPONENT_UNDECLARED` 삭제로 깨지는 기존 test(`test_block_columns.py:1161-1168`, `test_s2_values.py:227-228`)를 4.7-6 test 영향 목록(test 작성 주체 몫)에 더한다.
- **N-2.** 계획 N3.8 정의 불능 목록의 'e가 CM 방향과 평행'은 기본 포트 뷰만 쓰면 도달 0이다(3절). 계획 목록에도 '기본 뷰에서 도달 0'을 표시해 design 삭제와 맞춘다.
- **N-3.** `saturation_window`의 영 기울기 건너뜀(`|rate| ≤ eps`)이 전도 행(A/V)에도 걸린다는 기록은 좋다. 단위가 다른 문턱이라는 사실을 백로그(I-H3 곁)에 남겨 두는 것을 권한다.

## 미확인
- integ-it12 최신의 13회로 S1v 뷰 수 실측(엔진 실행 안 함). 2절 (1)의 '12회로 전달 뷰 하나'는 계획 grep 사실과 `collect_views` 코드를 근거로 한 판단이다.
- 계획 history H1 'v6.36' 본문.
