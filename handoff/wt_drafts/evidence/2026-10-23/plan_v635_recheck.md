# 계획 v6.35 재검증 (plan/v635 `9ed1eafa`, 부모 `6228d6af`)

- 2026-10-23, 읽기 전용 검증 agent. 쓴 파일은 이 파일 하나다.
- 확인한 것
  - `9ed1eafa`의 plan·history 전문
  - spec·topology 자산, oracle design(같은 커밋)
  - 엔진 integ-it12 `ee9bcf5b`(`Window` 칸, `spec_views.py`)

## 점수: 90 / 100 -- 새 G 0, 새 S 1

## 1. 앞 지적의 해소

| 지적 | 판정 |
|---|---|
| S-1 | 해소. N3.8에 'e 무관(입력 둘)' 유도, e 조건(CM과 평행 아님), role 불변성, 입력 셋 이상 = 정의 불능이 들어갔고, 좌표는 U-106으로 V_cm 하나가 됐다. |
| S-2 | 해소. 'ICMR 전달 뷰 = DEC-23 gain 뷰 하나', 없거나 (ac_excite, sense)가 다른 뷰가 둘 이상이면 정의 불능, 착수 실측 (d). |
| S-3 | 해소. R-N1을 번호 있는 card TN-1(N6.26)로 옮기고 N6.1 행을 더했다. |
| N-1 | 해소(a_e = A_dc 조건에 e 가중 정규화) |
| N-2 | 해소(`ls_fields.py:45-49` 인용) |
| N-3 | 해소(U-103 정확 고정 servo, nullor 꼴) |
| N-4 | 해소(실행 조건, offset이 같은 사유를 냄, DE-1 (c) READS) |
| N-5 | 해소(card 인용 20줄) |
| N-6 | 해소(짝 버전 v0.6.18·v0.3.11) |
| N-8 | 해소(정적 가드 → TN-1 (3)) |

## 2. U-106 (V_cm 좌표)

- **물리 정합**: 맞다. ICMR = 입력 공통모드 전압 범위이고, servo 끝 상태는 e와 무관(입력 둘)하므로 V_cm이 잘 정의된다. oracle as-built `icmr_coord`와 같은 정의가 된다.
- **지우는 것**: DV-18 포트별 margin, IT-Q2 (다), 포트 창 교집합 폭. 지워도 된다.
  - 같은 이름에 두 좌표를 두지 않는다(graph 규칙 3).
  - follower 때 두 정의가 같았던 근거(묶이지 않은 포트 하나)가 servo에서 사라진다.
  - '원래 취지와 다름(사용자 승인 대상)' 표시가 있다.
- **입력 하나인 회로 값 변화 0**: 맞다. V_cm = V_in이라 세 식이 옛 포트 식과 같다(icmr_v = 포트 창 폭, margin = min(V_p − lo, hi − V_p)).
- **IT-2d 충돌**: 없다. 다만 아래 S-1이 IT-2d `metrics_aux` 배선의 입력 자료 문제다.

## 3. 'ICMR 전달 뷰 = DEC-23 gain 뷰 하나'

- current_reuse의 view 선언 넷(`human/constraints[0,3,4,11]`)을 보면 gain 제약은 `gain_ss_db` 하나이고 그 view는 `{"pending": "MOD5"}`다. 나머지 셋은 `ratio_ss_db` 둘과 `parasitic_pm_ss_deg`다.
- 그래서 '둘 이상' 규칙은 발동하지 않는다. 그 회로의 ICMR은 결정 대기 뷰(기존 실행 전 정지 갈래)에 걸린다. layer0 봉인점도 없다.
- ngcc는 `gain_ss_db`가 둘(constraints·pending_constraints)이지만 둘 다 기본 뷰라 (excite, sense)가 같다.
- 결과적으로 규칙이 운영 회로를 정의 불능으로 만드는 사례는 지금 없다. 규칙 자체는 fail-closed로 받아들일 만하다.
- 착수 실측 (d)로 충분하다. pending 뷰 갈래를 (d) 기록에 함께 적기를 권한다(N-a).

## 4. card TN-1

- 범위 (1)~(4)와 완료 조건 (1) 동작 동일성(손으로 쓴 toy), (2) `git grep`, (3) AST 정적 가드와 red 변형은 판정할 수 있다. 변경 종류(순수 리팩터링), 순서(IT-1 + IT-2 master 병합 뒤), N6.1 행도 갖춰졌다.
- DEC-100 (2) 'DC는 저항이 작동'·(3) '해석에서 외부 소자를 빼지 않는다'는 DC 망 조립에서 루프 절단을 쓰지 않는다는 정적 가드의 근거로 맞다(DEC-100 원문 299행 확인).

## 5. `inverting_port_undetermined` 개수

- oracle design(`9ed1eafa`)에서 **13줄 14회**다. 482, 1454(2회), 1534, 1607, 1639, 1640, 1641, 1659, 1743, 1751, 1824, 1874, 1945.
- 작성자의 셈이 맞다. 앞 검증의 '15곳'은 정정한다.
- 참고(N-b): 계획이 '`inverting_port_none`·`_ambiguous`·`_unresolved` 각 1회'라고 적은 것(1639-1641)은 실제로는 엔진 code `icm_inverting_port_*`를 인용한 비교표 줄이다. 이름 표기를 'icm_' 붙은 엔진 code 인용'으로 고치면 정확하다.

## 6. 새 발견

### S-1 V_cm 끝 상태 대응이 graph 필드에 없다 -- 정본 자리를 계획이 정해야 한다(S-7)

- **위치**: N3.8 'ICMR 좌표 -- 정의 자리 하나'의 '끝 상태 = `node.dc_window_cfg`(입력 포트마다)의 같은 끝 상태에서의 포트 전압들 -- 새 graph 필드 없이 `metrics_aux`가 그 창 칸에서 낸다(끝 상태 대응을 읽는 방법은 design; 대응을 정할 수 없거나 … 정의 불능)'
- **근거**
  - `node.dc_window_cfg` 값은 포트마다 `Window(lo, hi, constraints, input_status, tol_v)`다(`E/sizing/s2_values.py:360`, design 41:681·732). 어느 끝 상태에서 나온 값인지(x의 아래·위 끝)가 담기지 않는다.
  - 게다가 P2(O-49 '감도 음수 포트 = 두 끝 전압의 [min, max]')가 정렬하므로 대응이 구조적으로 사라진다.
  - V_cm(끝) = 같은 끝 상태의 포트 전압 평균은 이 칸만으로는 일반적으로 복원할 수 없다. 두 포트 감도가 모두 양수라고 가정하면 lo끼리·hi끼리 짝지을 수 있지만, 그 부호는 필드에 없어 `metrics_aux`가 확인할 수 없다(가정하면 fail-open, 늘 거부하면 거짓 정의 불능).
  - 즉 계산값(V_cm 끝)의 정본 자리가 정해지지 않은 채 design에 넘어갔다. CLAUDE.md 규칙 6('정본 자리가 없으면 멈추고 계획부터')에 해당한다.
- **수정 제안**: 계획이 하나를 고른다.
  - (가) 측정 구성 블록(`icm_config`, writer 하나)이 끝 상태별 V_cm(또는 x 끝과 ε 끝)을 기존 필드 `graph.icm_config` 칸으로 쓰고, `metrics_aux`가 READS한다. 새 graph 필드는 0이고 칸이 하나 는다.
  - (나) `node.dc_window_cfg` 항목을 끝 상태 순서로 저장한다(아래 끝 상태의 전압, 위 끝 상태의 전압). [min, max] 정렬(P2)은 소비자 쪽 metric 식에서 한다. P2 문언을 고쳐야 한다.
  - 기본안은 (가)다. 생산자가 V_cm을 바로 알고(기본 뷰는 e_cm = 0이라 V_cm = x0 + Δ끝), 대응 소실 문제가 생기지 않으며, P2를 건드리지 않는다.
  - 어느 쪽이든 '대응을 정할 수 없으면 정의 불능' 갈래는 필요 없어진다.
- **원칙 점검**: graph 규칙 1·6(정본 자리), fail-closed(거짓 정의 불능·fail-open 둘 다 피함), 계획 먼저 → 맞음

### N (참고)

- **N-a** IT-2c 착수 실측 (d)에 current_reuse `gain_ss_db` view = `{"pending": "MOD5"}`(결정 대기)라는 사실과 그때 ICMR 갈래를 기록한다.
- **N-b** 5절 code 이름 표기.

## 7. 새 원칙 위반

S-1 밖에는 없다. 점검한 항목은 graph 정본, fail-closed, DC/AC, DEC-103, 상수 0, 회로 이름 0, 만들면 배선, 계획 먼저다.
