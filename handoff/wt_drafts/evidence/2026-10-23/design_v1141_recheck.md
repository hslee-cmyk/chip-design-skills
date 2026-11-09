# design v1.14.1 둘째 커밋 재검증 (2026-10-23)

- 대상: `wt/design-v1131` `8e665504`(부모 `8f755b05`). numstat: 40 4/4, 41 6/6, 42 0. 줄 수는 바뀌지 않았다.
- 계획 대조본: `wt/plan-v637` `4506f6dd` N6.6 완료 조건 (9)(S4-나).
- 읽기 전용으로 진행했고 git은 `git -C`만 썼다.

## 결과: 새 G·S 없음, 점수 97 / 100

## 1. 지적별 해소 여부

| 지적 | 반영 위치 | 판정 |
|---|---|---|
| 검증 S-2(식별 근거) | 41:731 | 해소. 옛 근거 'GB4 첫 뷰가 바뀜'은 틀렸다고 명시했다(`achievability.py:348`). 새 근거는 둘이다: `source`는 `_constrained_keys`가 쓰는 칸이라 다시 쓸 수 없고, 순서에 뜻을 실으면 graph 규칙 3에 어긋난다 |
| 검증 N-1(영향 test) | 41:797 | 해소. `test_block_columns.py:1161-1168`, `test_s2_values.py:227-228`을 test 작성 주체 몫으로 적었다 |
| gap S-1(design 쪽) | 41:716 '(9)과의 관계', 41:811 L8 (h) AST 단언 둘 | 해소. 2절 참조 |
| gap N-4 | 40:2092 | 해소. `writer_head`를 helper 목록에서 뺐다 |
| gap N-5 | 40:1266·1268 | 해소. 'DE-1 (c)에서 (나′)·기본 포트 뷰로 개정' 표지를 달았고, 값은 고치지 않았다 |
| gap N-6 | 41:734 ③ | 해소. '`collect_views`는 씨앗이 0일 때만 `view_required`'(`views.py:83-85`)로 사실을 바로잡았다. 판정 결과는 같다 |

## 2. 계획 v6.37 정오와의 대조

계획 (9)(S4-나) 문언:
- (b)의 {포화, `triode`}는 `region_rows`의 것이고, 측정 구성 창 전체의 행 종류는 {포화, `triode`, 전도}다.
- (c)(ii)는 `_conduction_rows`를 뺀다. 이 함수는 READS로 읽기만 허용한다.
- (c)(i)(iii)은 `_conduction_rows`에도 건다.

design 대조 결과:
- 41:716은 위 셋을 같은 뜻으로 인용한다.
- 41:811 L8 (h)는 다음을 단언한다:
  - `_conduction_rows`와 그것이 부르는 IT-2 모듈 함수에 (i) VGS = 0인 `op_point` 호출 0, (iii) EO-1 import 0
  - (ii) `dc_conduction_floor`는 READS 읽기만
  - kind 집합: `_conduction_rows` = {conduction}, `region_rows` = {sat, triode}
- 41:810 D (b)도 같다. **일치.**

## 3. 새 원칙 위반

없음. 새 필드·cache·code·상수가 없고, 바뀐 것은 문언·근거·영향 목록·표지뿐이다.
