# 계획 v6.35 독립 검증 (plan/v635 `6228d6af`, base master `0dd40d4a`)

- 2026-10-23, 읽기 전용 검증 agent. 쓴 파일은 이 파일 하나다.
- 확인한 것
  - diff와 `6228d6af`의 plan·history 전문
  - 사용자 결정: `_drafts/user_decisions.md` O-114·O-115
  - 근거 문서: `icmr_definition_review.md`와 그 원자료 `analysis/table.txt`, `*.cfg_analysis.json`
  - 엔진·oracle: integ-it12 `ee9bcf5b`(`git -C … show/grep`)
  - design 40·41, oracle design, IT-2 card(같은 커밋 `6228d6af`)

## 점수: 84 / 100

- 필수(G) 0, 권고(S) 3, 참고(N) 8.
- O-115가 빠짐없이, 다르지 않게 들어갔다. 살펴본 자리는 N3.8 602·603·615, N6.6 IT-2c 범위·완료 조건 (3)(5)(6)(8)(12)·착수 조건 (vii), N6.8, 후속 정정 표, N7.2다.
- 지운 대상은 엔진 code와 엔진 test에서 소비자가 0이다. 모두 아직 design에만 있다.
- 감점 사유
  - U-105의 근거('2차 크기 추정')가 실제로는 더 강한 사실(입력 둘인 회로에서는 상태가 같음)로 대체돼야 한다. 그 과정에서 ICMR 좌표와 `icmr_v` 정의가 엔진과 oracle에서 갈리는 점이 드러났다(S-1).
  - 전달 뷰를 고르는 규칙이 비어 있다(S-2).
  - O-83 R-N1을 덜어 낸 것이 원칙과 어긋난다(S-3).

## 1. O-115 반영

| 항목 | 판정 |
|---|---|
| ICMR = 입력 포트 함께 훑기(차동 입력 = 봉인점 차 유지)와 출력을 봉인점 `node.dc_v[out]`에 묶음, 차동 출력은 DM 고정·CM은 CMFB, 단일 입력은 회로 그대로 | 반영(N3.8 'ICMR 측정 구성 -- 정의 하나', '차동 출력 -- 정의 본문') |
| 엔진 = `graph.ss_nodal` + Schur 1칸 δs = 0 KCL 선형 끝('추정'), oracle = `.dc` servo | 반영('ICMR servo 감도 -- KCL', metric 표 615) |
| declared_feedback을 ICMR에서 뺌(DC 망·경로 판정·code·toy), Q-1 소멸 | 반영(삭제 목록 (8)(f), `tied_ports`·`inverting_port` 삭제) |
| 원래 취지와 다름 목록(O-25 (2)·O-50 G4/X-DE5·1720/1723·O-52·O-53 A-2·O-58 S-3·O-79~O-87·O-67 (1)·O-108·O-34 (2)/O-51) | 반영(N2.1 O-114·O-115 행, Status) |
| 권고 (i)(ii)(iii) → U-102·U-103·U-104 | 반영 |
| 범위 확대·축소 | 작성자가 더한 7건은 모두 '이 판이 더한 원래 취지와 다름(사용자 승인 대상)'으로 표시됐다(Status·H1). 표시 누락은 없다. |

## 2. 지운 것의 소비자

- **엔진·oracle code** (`ee9bcf5b` `git grep`, `gmid_engine`·`tools`)
  - `tied_ports`·`inverting_port`·`follower_beta1`·`_dc_feedback_reaches`·`feedback_cut_nets`·`icm_config_feedback*`·`icm_inverting_port*`·`icm_config_differential*`: 0건이다. IT-2c 미구현이라 design에만 있다.
  - `declared_feedback`: oracle test 함수 이름(`test_c14_undeclared_feedback_is_beta_1`, 슬루·β 쪽) 1건뿐이고 대상 밖이다.
- **design·card**: design 41:700·732~735·744·780·789·811, design 40:556, `specs/20261021-it2-common.md`(8), `it2c-icm-config.{interface,spec}`(3·4), `it2d-refine-front.{interface,spec}`(1·4).
  - (vii)이 design 41·40을 고치고 'IT-2c·IT-2d card 재동결'을 지시하므로 덮인다.
  - 다만 IT-2d card 두 파일이 `tied_ports`를 인용한다는 사실은 계획에 적혀 있지 않다(N-5).
  - design 41:789 `metrics_aux` 포트 거르기는 (vii)에서 'IT-2d design 몫'으로 지정됐다.
- **oracle design**: `inverting_port_undetermined` 등 15곳. 후속 정정 표 1730행이 '반전 입력 식별을 슬루 전용으로'라고 적어 덮는다.
- **'반전 입력 식별·DC 되먹임 판정 정의는 슬루 전용, 엔진 구현 없음'**: 원칙에 맞는다.
  - `ls_constraints.py:36-47`은 슬루 행이 노드 전류·용량·분해능만 읽는다는 것을 직접 확인했다.
  - DE-1 (d) 엔진 슬루 전류는 `dc_current_basis` θ 전류 합이다.
  - 소비자는 oracle 슬루 벤치뿐이라 엔진에 만들면 배선 위반이다. 정의 한 자리를 oracle이 구현하므로 graph 정본도 문제없다.
  - 근거 인용은 보강이 필요하다(N-2).

## 3. 작성자가 새로 정한 7건

### U-105 보정 방향 e -- 물리는 맞다. 근거 문장과 좌표 정의를 고쳐야 한다(S-1)

- **물리**
  - 입력이 둘인 회로에서 servo 상태 집합은 '감지 s = s0'인 입력 2차원 공간의 곡선 하나다.
  - CM 방향과 평행하지 않은 e라면 어느 것이든 (x, ε)가 그 2차원 공간 전체를 덮는다. 따라서 **같은 곡선, 같은 끝 상태**가 나오고, 다른 것은 매개변수 x 하나뿐이다.
  - 선형화에서도 같다. 접선은 span{CM, e} = 입력 2차원 전체와 δs = 0의 교선이라 e와 무관하다.
  - 그러므로 포트 전압으로 재는 양(DV-18 `icm_margin_v`, 포트 창, 묶는 소자)은 e를 어떻게 골라도 **정확히 같다**.
  - 작성자의 '두 선택의 끝 차는 2차 크기'(추정)는 이 사실보다 약하다. 게다가 x 좌표로 재면 2차가 아니다.
- **x 좌표로 쟀을 때의 실제 크기**
  - 분석 원자료로 e의 CM 성분을 셈하면 끝 차는 ε/2 = (A_cm/A_dm)·Δ/2, 곧 Δ의 1차다.
  - 구성 S의 dV_out/dx는 two_stage 0.011, ngcc 0.015, folded −0.0007, two_stage_sf 0.009, nmcnr 0.44다(`*.cfg_analysis.json` `engine_lin_dVout_per_dx.S`).
  - nmcnr은 A_cm/A_dm ≈ 0.44 → 끝 차 ≈ 0.22·Δ다(위 끝 Δ ≈ 0.11 V → 약 24 mV, 추정).
  - 다른 회로는 ≤ 0.008·Δ다.
- **기본 뷰는 차동 입력에서 e = (+½, −½)다**(`authoring/spec_views.py` 머리말: p = +1/|D|, n = −1/|D|, v_cm = 0). 그래서 엔진 x는 실제 CM과 같다.
  - 반면 oracle as-built는 반전 입력 하나만 보정하고, 좌표 = 실제 입력 CM (V_inp + V_inn)/2다(`oracle_swing.py` 머리말, oracle design 1659 `icmr_coord`).
  - 계획의 `icmr_v`는 '포트 창 교집합의 폭'이다(N6.6 범위 2). servo에서는 두 포트가 함께 움직이므로 '포트 창 교집합 폭'과 'CM 좌표 폭'이 O(ε)만큼 다르다.
  - follower 때는 묶이지 않은 포트가 하나라 두 정의가 같았다. **엔진과 oracle `icmr_v`의 정의가 servo에서 갈린다.**
- **포트 role 의존**: e가 기본 뷰의 role 가중에서 나오므로 계획 문장 '포트 role 이름은 근거로 쓰지 않음'은 문자 그대로는 맞지 않는다. 그러나 결과는 role을 맞바꿔도(e → −e, 부호는 ε에 흡수) 같다. 그 불변성을 근거로 적으면 된다.
- **a_e = DEC-23 A_dc**: 같은 뷰라면 e의 정규화(가중 크기)가 같아야 같은 양이다. 생산자 하나(`graph.icm_config` 칸), DE-1 (c)가 READS → graph 규칙 1·3에 맞다. 정규화 조건을 적을 것(N-1). 실행 조건(N-4)도 적을 것.
- **단일·차동 출력**: 감지 V_op − V_on 하나, 미지수 ε 하나로 Schur 1×1이 된다. 맞다(CM은 CMFB가 정하고 행이 없음).

### U-102 슬루 계단 끝 -- 타당하다

- ICMR에서 선언 되먹임을 빼고 슬루에 남기는 것은 모순이 아니다.
  - 슬루는 응용 구성의 과도 측정이다. 과도 되먹임 = 선언 구성(O-34 (2)·O-69 (1), 계획 603 OQ-11)이고, ICMR servo를 과도 되먹임으로 쓰지 않는다고 명시했다.
  - 측정 구성 축이 다른 양이라 graph 규칙 3에 맞다.
- 엔진이 계단 끝을 읽지 않는다는 점: `ls_constraints.py:36-47` 확인. 계획된 DE-1 (d) 엔진 계산(θ 기저 합)도 끝을 읽지 않는다.
- 다만 as-built `ls_fields`의 σ 셀 전류는 `ls_swing` gate 경로 합 `bounds`를 읽는다(`metrics/ls_fields.py:45-49`). ICMR 끝은 아니지만 '입력 쪽 범위'를 읽는 자리다. DE-1 (d)가 대체한다는 인용을 덧붙일 것(N-2).

### U-103 oracle servo -- 타당하다(새 상수 0). 실현 조건은 주의

- 조건 |s − s0| ≤ vntol + reltol·|V|를 정의 쪽에서 내리고, 어기면 fail-closed로 둔 것은 원칙에 맞다.
- 그러나 분석의 G = 1000 servo(T)조차 nmcnr에서는 출력이 1.658180~1.658589 V(±0.2 mV)다. reltol·|V| ≈ 0.17 mV를 넘어 정의 불능이 된다.
- 다른 회로는 ±13 µV 이내라 통과한다.
- oracle design은 이상 servo(nullor 꼴 또는 더 높은 이득)를 써야 한다(N-3).

### U-104 spec 출처 표기 -- 원문 확인으로 맞다

- ngcc `paper.md:1170-1202`는 식 (9) ICMR = V_DD − V_DSAT5 − V_TH(입력단 포화 손계산)이다. 같은 양이다.
- nmcnr `paper.md:254-255`는 "slew rate and settling time were measured in unity-gain configuration with a 0.5V step input"이다. ICMR 정의가 아니라 슬루 조건이므로 다른 양이다.
- spec record·citation 문구(`ngcc_3stage_ff.sizing_spec.json:99-108`, `nmcnr_amplifier.sizing_spec.json:117-126`)도 인용과 같다.
- 새 키 없이 record에 덧붙이는 방식도 맞다.

### RB-1 대상 소멸, R-N1 백로그, (10)(a) 삭제

- **RB-1**: 근거가 맞다. S-OS2 멈춤 갈래가 만들어지지 않아 등록표 자리가 없다(DEC-102 (6)).
- **(10)(a) 삭제**: 근거는 대체로 맞다(전제였던 S-3 DC 망 정의 불능 규칙이 없어짐). 다만 측정의 일부(절단 넷 함수가 `E/sizing`·`ss_nodal`에서 불리지 않음)는 ICMR과 무관한 일반 정합 가드였다(N-8).
- **R-N1 백로그**: S-3. 덜어 낸 근거는 'icm_config 호출 자리가 없어짐'인데, R-N1의 목적은 authoring `input_terminal_nets`와 `noise_plan._input_side`의 구현 둘을 하나로 만드는 것이었다. 이 목적은 ICMR과 무관하게 남는다.

## 4. 근본원칙

| 원칙 | 판정 |
|---|---|
| 물리 정합·가장 일반형 | 통과. 손계산 ICMR과 같은 양이고, 단일·차동이 같은 꼴이다. 다입력(> 2) 회로에서는 e 불변성이 깨지므로 S-1에서 규칙이 필요하다. |
| DC/AC | 통과(용량 개방 DC 야코비안) |
| DEC-103 | 통과. 봉인점 = servo 동작점이라 외삽이 0이다. 이번 개정으로 v6.34 design이 L 구성을 계산하던 gap도 해소된다. |
| 손계산 속도·SPICE 확정 | 통과(`nodal_solve` 2회 + 끝 식) |
| graph 단일 정본 | 통과(기준 `node.dc_v` READS, 감도 `graph.ss_nodal`, 창 `node.dc_window_cfg` 한 칸, a_e 생산자 하나). 단 S-3 부채가 존속한다. |
| fail-closed | 통과. 뷰 선택 규칙의 공백은 S-2. |
| 상수 발명 | 0 |
| 회로 이름 | 0. role 의존 문장은 S-1에서 정정한다. |
| 만들면 배선 | 통과(소비자 없는 칸·판정을 만들지 않음) |
| 계획 먼저 | 통과(착수 조건 (vii), U-105) |

## 5. 충돌

| 대상 | 판정 |
|---|---|
| IT-2d | 포트 집합 = 입력 포트 모두, 'β = 1 기본' 삭제로 문언이 맞는다. card 파일 재동결 목록은 N-5. |
| B77 | 영향 없다(영역 규칙·`metrics_aux` READS 그대로). |
| DE-1 | (a) 같은 블록에 기준만 더하고, (b) 스윙은 servo 행 없이 차동 훑기, (c) A_dc READS(N-1·N-4), (d) U-102. 충돌 없다. |
| IT-2e·N3.3 | 영향 없다. |
| oracle 계획 | 후속 정정 표 1721·1724·1730이 덮는다. ICMR 좌표·`icmr_v` 정의를 맞추는 일은 S-1. |
| 기존 승인분 | `graph.ss_circuit`, E 칸(`__canonical__` 포함), U-101 (가′), D1(W4 뿌리), D4(분류 필드 없음), 결측 영역 규칙은 문언이 유지됐다(602·1519·1531 확인). |

## 6. 발견 사항

### G: 0건

### S (승인 전 반영 권고)

- **S-1 ICMR 좌표·`icmr_v` 정의를 servo에 맞게 확정하고, U-105 근거를 정확한 사실로 바꾼다**
  - 위치: N3.8 'ICMR 측정 구성'(servo 보정·'포트 role 이름은 근거로 쓰지 않음'), N6.6 범위 2 `icmr_v` = '포트 창 교집합의 폭', N7.2 U-105('2차 크기 -- 추정'), 후속 정정 표 1730
  - 근거: 3절 U-105 분석.
    - 입력 둘인 회로에서 servo 끝 상태는 e(CM과 평행 아님)와 무관하다. 기본 뷰 e = (+½, −½)이고 `spec_views.py`로 확인했다.
    - 그러나 엔진 `icmr_v` = 포트 창 교집합 폭, oracle = CM 좌표 폭(`oracle_swing.py`, oracle design 1659 `icmr_coord`)이라 servo에서는 두 포트가 함께 움직여 O(ε)만큼 다르다.
    - x 좌표 기준 차는 Δ의 1차다(nmcnr 약 0.22·Δ).
  - 수정 제안
    - (가) U-105 근거를 "입력 둘인 회로에서 servo 끝 상태와 포트 전압 metric은 e 선택과 무관하다(CM과 평행하지 않은 e), e는 매개변수만 바꾼다"로 고친다. 다입력(> 2)은 미확인 표시와 함께 정의 불능 또는 별도 규칙으로 둔다.
    - (나) `icmr_v`의 좌표를 엔진·oracle 한 정의로 정한다(실제 입력 CM 폭 또는 포트 창 교집합 폭 가운데 하나). 정의 자리는 N3.8 하나이고 oracle 후속 정정 표가 인용한다.
    - (다) role 문장을 "기본 뷰 가중은 role에서 오지만 결과는 role을 맞바꿔도 같다(부호가 ε에 흡수됨)"로 고친다.
    - (라) a_e = A_dc 동일 조건에 'e 정규화가 같음'을 더한다(N-1과 같음).
  - 원칙 점검: 물리 정합, 오라클과 같은 구성·같은 정의 하나(O-50·O-53 취지), 정의 자리 하나, 근거+확인 → 맞음

- **S-2 ICMR 전달 뷰 선택 규칙의 공백**
  - 위치: N3.8 '출력 기준 = 그 전달 뷰(gain 제약 metric이 선언한 (ac_excite, sense))', 정의 불능 '전달 뷰가 없음'
  - 근거
    - 감지 s의 선택은 servo 상태를 바꾼다. 단일 출력 감지와 차동 감지는 다른 구속이다.
    - `current_reuse_telescopic_ota.sizing_spec.json`에는 view 선언이 여럿 있다(154·188·202·281행).
    - ngcc·nmcnr·sf_pushpull은 view 선언이 없어 기본 뷰(`spec_views.default_views`)에 기댄다. 기본 뷰가 `view_required`면 ICMR이 정의 불능이 된다. follower 때는 뷰가 필요 없었으므로 새 정의 불능 갈래다.
  - 수정 제안
    - 'ICMR 전달 뷰 = DEC-23 여기 방향을 정하는 그 gain 전달 뷰 하나'로 한 자리에서 정한다.
    - gain 전달 뷰가 둘 이상이고 (excite, sense)가 서로 다르면 정의 불능으로 두거나 선택 규칙을 둔다.
    - IT-2c 착수 실측에 'ICMR 제약 4회로(ngcc·nmcnr·current_reuse·sf_pushpull)의 뷰 유일성·기본 뷰 성립'을 더한다.
  - 원칙 점검: fail-closed, 정의 하나, 실측 먼저 → 맞음

- **S-3 O-83 R-N1(절단 넷 순수 함수로 구현 둘 → 하나)을 백로그로 돌린 것**
  - 위치: N6.6 IT-2c 착수 조건 (vii) 끝, N3.8 '선언 되먹임의 DC 되먹임 판정' 절단 넷 문장, Status (5)
  - 근거
    - R-N1의 목적은 authoring `_feedback_cuts.input_terminal_nets`와 `metrics/noise_plan._input_side`의 같은 규칙 두 구현을 하나로 만드는 것이다(graph 규칙 1). `icm_config` 호출이 사라져도 이 중복은 그대로다.
    - 사용자가 승인한 범위를 표시와 함께 덜어 냈다. 원칙상 기본안은 유지가 맞다.
  - 수정 제안
    - R-N1을 IT-2c에 남기거나, 번호 있는 작은 card로 순서를 잡는다(엔진 소비자 = authoring 둘·`noise_plan`).
    - 덜어 내려면 '원칙(규칙 1)과 충돌'을 명시해 사용자 결정에 올린다.
  - 원칙 점검: graph 규칙 1, 권고는 원칙과 일치, 원래 취지와 다름 보고 → 맞음

### N (참고)

- **N-1** a_e = A_dc 동일 조건에 'e 가중 정규화 같음(기본 뷰 ±½ 또는 선언 가중)'을 적는다.
- **N-2** U-102·N3.8 '엔진 쪽 칸 없음' 근거에 as-built `ls_fields.py:45-49`(σ 셀이 `ls_swing` gate `bounds`를 읽음 -- ICMR 끝 아님, DE-1 (d)가 대체)를 함께 인용한다.
- **N-3** U-103: 분석 T(G = 1000)에서도 nmcnr 출력 고정 오차 약 ±0.2 mV > reltol·|V| ≈ 0.17 mV라 정의 불능이 된다(`nmcnr_amplifier.cfg_analysis.json` T `vout_lo/hi`). oracle design이 이상 servo(nullor/고이득)와 수렴을 함께 정하도록 U-103 행에 적는다.
- **N-4** a_e를 `graph.icm_config` 칸에서 DE-1 (c) A_dc가 READS할 때, offset metric이 필요한 평가에서 `icm_config`가 늘 도는지(실행 조건 = `metrics_aux`와 같음) 명시한다. 돌지 않는 평가가 있으면 A_dc 정의 불능이 된다.
- **N-5** IT-2 card 재동결 목록에 `specs/20261021-it2-common.md`·`it2c-icm-config.{interface,spec}.md`·`it2d-refine-front.{interface,spec}.md`의 `tied_ports`·`inverting_port` 인용(합계 20곳)을 명시한다.
- **N-6** oracle design의 `inverting_port_undetermined` 계열(15곳)은 슬루 전용으로 남는다. 그 정정은 oracle 계획 개정 몫이라고 후속 정정 표 1730에 짝 버전을 적는다.
- **N-7** 13회로의 입력 포트 수(> 2인 회로 유무)는 미확인이다. S-1 (가)의 다입력 규칙이 필요한지 착수 실측으로 확인한다.
- **N-8** 지운 (10)(a) 가운데 정적 측정 (i)('절단 넷 함수 참조가 `E/sizing`·DC 망 조립 자리에 0')은 ICMR과 무관한 DC 정합 가드였다. 비용이 작으니 R-N1(S-3)과 함께 남길지 검토한다(선택).

## 7. 미확인

1. 다입력(> 2) 회로 유무와 그때의 servo 정의.
2. ICMR 제약 4회로의 기본 전달 뷰 성립 여부(S-2).
3. nmcnr에서 e 대 반전 입력 보정의 x 좌표 끝 차(추정 약 24 mV, 실측 아님).
4. design 41 4.7-5 `IcmPort`·front 쪽 `tied_ports` 소비 전수(IT-2d design 몫).
