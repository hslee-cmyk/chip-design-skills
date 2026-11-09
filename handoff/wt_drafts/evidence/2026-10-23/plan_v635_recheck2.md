# 계획 v6.35 재검증 2 (plan/v635 `e73fa979`, 부모 `9ed1eafa`)

- 2026-10-23, 읽기 전용 검증 agent. 쓴 파일은 이 파일 하나다.
- 대상: `e73fa979`의 plan 전문(N3.8 'ICMR 좌표 -- 정의 자리 하나', 완료 조건 (8)(g), IT-2c 착수 조건 (vii), 후속 정정 표, Status).

## 점수: 94 / 100 -- 새 G·S 없음

## 1. 해소 확인

| 지적 | 판정 | 근거 |
|---|---|---|
| S-1(V_cm 정본 자리) | 해소 | N3.8 'V_cm의 정본 자리': `icm_config`(writer 하나)가 포트 끝과 같은 연립·같은 풀이에서 V_cm0와 아래·위 끝 V_cm을 `graph.icm_config` 칸으로 쓰고 `metrics_aux`가 READS한다. 새 graph 필드는 0, P2 정렬은 그대로이고, 소비자가 포트 창에서 다시 계산하지 않는다. (vii)과 후속 정정 표 design 행에 'V_cm 칸(소비자 `metrics_aux`)'이 들어갔다. 앞 판의 '대응을 정할 수 없으면 정의 불능' 갈래는 빠지고 '한 포트라도 창이 정의 불능이면 V_cm 칸·세 metric 정의 불능'만 남았다(fail-closed, 근거 있음). |
| N-a | 해소 | 착수 실측 (d)에 current_reuse gain 뷰 `{"pending":"MOD5"}`와 layer0 봉인점 없음이 들어갔다. |
| N-b | 해소 | 후속 정정 표 oracle 행 1639-1641 = 엔진 code `icm_inverting_port_*` 인용으로 고쳤다. |

## 2. 완료 조건 (8)(g) 판정 가능성

판정할 수 있다. '감도 음수 포트 toy에서 lo·hi를 짝지어 평균하면 red'는 실제 red 변형이다.

- 근거
  - 기본 뷰(e_cm = 0)에서 V_cm(아래 끝) = x_lo이다. 포트 전압은 x ± ε/2다.
  - 한 포트의 감도가 음수(dε/dx > 2, 곧 CM 쪽 전달이 DM 쪽보다 큰 꼴)면, P2 정렬 뒤 그 포트의 lo는 x_hi 끝 상태에서 온 값이다.
  - 이 lo를 다른 포트의 lo와 짝지어 평균하면 (x_lo + x_hi + (ε_lo − ε_hi)/2)/2 ≠ x_lo가 된다.
  - 손계산 끝 상태 평균과 갈리므로 짝지은 구현은 실패한다.
- 보완(N-1): red가 공허해지지 않도록 다음 두 전제 단언을 명시한다.
  - toy에서 한 포트 감도가 실제로 음수다.
  - 짝지은 평균과 끝 상태 평균의 차가 비교 허용치보다 크다.

나머지 단언도 판정할 수 있다.
- V_cm 끝 = 손계산 끝 상태 평균
- 양수 감도 toy에서 포트 lo끼리·hi끼리 평균과 일치
- `metrics_aux` READS에 `graph.icm_config`가 있음
- 기본 뷰 V_cm 끝 = x0 + Δ끝

AST 'metrics_aux에 포트 창에서 V_cm을 계산하는 식 0'은 대상(ICMR metric 함수 안에서 `node.dc_window_cfg` 칸의 lo·hi에 대한 산술)을 design이 이름으로 적어야 측정이 분명해진다(N-2).

## 3. 새 원칙 위반

없다.

- **graph 정본**: V_cm 칸의 writer는 `icm_config` 하나다. 포트 끝과 V_cm 끝은 같은 풀이에서 나온 다른 양(포트별 대 평균)이고 다른 자리에서 다시 계산하지 않으므로 둘째 생산자가 아니다. V_cm0는 `node.dc_v` READS에서 한 번 계산된다.
- **fail-closed**: 한 포트라도 정의 불능이면 V_cm과 세 metric이 정의 불능이다.
- **DC/AC·DEC-103·상수**: 변화 없다.
- **만들면 배선**: V_cm 칸 소비자는 `metrics_aux`의 세 metric이다.

## N (참고)

- **N-1** (8)(g) 감도 음수 포트 toy에 전제 단언 둘(음수 감도, 짝지은 평균과의 차 > 허용치)을 적는다.
- **N-2** (8)(g) AST 측정 대상(ICMR metric 함수, `node.dc_window_cfg` lo·hi 산술)을 design에서 이름으로 정한다.
