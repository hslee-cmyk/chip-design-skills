# O-58 계획 개정 2건 독립 검증 (2026-10-20)

검증자: 독립 agent(작성자 아님), 읽기 전용. 기준 master `2e707d5d`.
대상: gain-budget `plan/gb-v621` `bb545b92`(0b7c9994·bb545b92), oracle-portability `plan/oracle-v0611` `ade94756`.
행 번호는 각 head 판 기준(gb = `gain-budget-gmid-sizing.plan.md`, or = `oracle-portability.plan.md`).

## 판정: **수정 필요**

결정 반영 자체(8개 항목)는 모두 맞는 계획에 결정 뜻대로 들어갔다. S-1에는 '원래 취지와 다름, 승인 O-58' 표기가 있다(gb 318·565·1463·1476). 그러나 S-1·T-1 개정이 **같은 계획 안의 옛 문언을 다 따라 고치지 않았다**. N6.6 범위 1과 DE-1 (a)에 `node.dc_window` = '선언 제약 판정 창'이라는 옛 정의가 남아 있어, N3.8 새 창 필드 정의와 정면으로 어긋난다. Major 2건을 고치면 승인할 수 있다.

## 1. O-58 항목별 반영

| 항목 | 반영 자리 | 판정 |
|---|---|---|
| S-1 | gb N3.8 '엔진 쪽 계산 자리'·'창 필드'(565), N6.6 범위 1(1476)·완료 (10)(1484), O-16 행(1463), 결정표(318) | 반영됨, '원래 취지와 다름 승인 O-58' 표기 있음. 단 옛 문언이 남음(F1·F2) |
| S-2 | gb N3.8(565 'KVL 고정 출력 구조…정본 하나'), DE-1 (b)(1572) | 반영됨 |
| S-3 | gb N3.8 'DC 망'(565), N6.6 완료 (10)(a)(e) | 반영됨(용량 제외·저항 포함, 루프 절단 비적용은 착수 실측, 해당하면 정의 불능) |
| S-4 | gb N6.6 범위 1(1476), 완료 (9)(1484), N6.20(1890·1892) | 반영됨(O-56 (b) 확장, V_on 역함수 = 공용 전도 판정 함수 곁, 분해능 = tol_V 셀) |
| T-1 | gb N3.8(565 `triode` 경계 판정 여유), N3.6 표 7행(496), N6.6 범위 1(1476)·(9)(1484); or 416·421 | 정의는 반영됨. 동작 변경 분류와 맡는 card 표기가 없음(F4), 정본 함수 인용 없음(F5) |
| DV-10 | or G-19(583), OP-10(491), N3.9 슬루 행(432), 결정표(122) | 반영됨(record_id + 끝마다 점 식별자, 네 검사, 실행 순서 ICMR → 2단계 → 슬루) |
| DV-11 | gb DEC-23(223), N6.1 DE-1 행(1142), DE-1 (c)(1573); or N3.9 σ 행(434) | 반영됨(DEC-23이 먼저 정하고 oracle은 인용, 단일 입력 기준선 변화 = N4 0번 동작 변경). 완료 조건 없음(F6) |
| B-45 | or 결정표(122) '계획 변경 없음(design 층)' | 맞음(decision이 'design 수준'이라고 함) |

## 2. 작성자 해석 판정

**(a) 측정 구성 판정 창 새 필드: 별개의 양이 맞음(사본 아님).** head의 입력 창 필드는 넷이다.

| 필드 | 정의 | writer | 소비자 |
|---|---|---|---|
| `node.dc_window` | θ 프레임, +tol_VDsat, 측정 구성 없음, 선형 감도 | `dc_columns`(`block_columns.py:778`) | 탐색 `fd_jacobian.py:54-55`(W4 y 폭). 실측하니 엔진 안의 유일한 소비자 |
| 측정 구성 판정 창(새 필드, 이름은 design) | +tol_VDsat, 측정 구성 ICMR, 선형 감도 | 봉인 뒤 블록(IT-2) | 커널 ICMR 선언 제약. DE-1 전에는 커널 metric도 읽음 |
| `node.dc_window_def` | tol 없음, 측정 구성 ICMR, 선형 감도 | 봉인 뒤 블록(DE-1 (a)가 정의 기준을 더함) | metric 값(DE-1 뒤) |
| `node.dc_window_def_refined` | 끝 풀이로 다듬은 창, 기준 칸 '+tol'(IT-2) / '정의'(DE-1 뒤) | 수락 반복·front 블록 | front 판정·보고 |

새 필드는 위 셋과 각각 한 가지 축(측정 구성, 판정 여유, 정밀도)이 다르다. 그래서 decision의 '같은 정의면 새 필드 없음' 조건에 걸리지 않고 O-16 (3)을 지킨다. 남은 점은 둘이다. (i) KVL 고정 출력 구조에서는 커널 창과 다듬은 창이 모두 같은 선형 감도 끝이다(565). IT-2 기간에는 새 필드와 `dc_window_def_refined`(+tol 기준)의 값이 같아진다. 이것은 정의가 같아서가 아니라 계산법이 우연히 일치하는 것이다. 정밀도 칸이 다르니 이름을 나눈 것은 그대로 맞다. 다만 design에서 값 복사가 아니라 같은 연립 결과를 한 번만 계산함을 밝혀야 한다(재계산 원칙). (ii) DE-1 뒤 새 필드의 소비자가 '선언 제약' 하나로 줄어든다는 문장이 N3.8 표에 없다. 지금은 '커널 metric'까지 소비자로 적혀 있어(565), DE-1 뒤의 metric 소비자 `dc_window_def`와 겹쳐 읽힌다. 1477의 'DE-1 전 한정'을 N3.8 표에도 붙이면 된다(Minor, F7).

**(b) T-1 여유는 +tol 판정 창과 봉인 7에만, 정의 창은 VDS < VDSAT: 원칙에 맞음.** O-33 (8)의 정의 대 판정 여유 분리와 같은 꼴이다. 포화 쪽 VDS − VDsat ≥ +tol의 거울이라 새 상수도 없다. 다만 tol_VDsat의 정본 함수(`sat_threshold`, HC-S)를 인용하지 않았다(F5). 훑기 점의 tol_VDsat를 어느 점 VDS에서 읽는지도 적혀 있지 않다. O-46 (2)는 훑기 점 값이 규칙이다(Minor, F5에 포함).

**(c) `node.dc_window_def` writer를 봉인 뒤 블록으로 옮긴 것: DE-1 범위 1 문언과 모순(Major, F2).** `dc_window_def`가 측정 구성 ICMR이라는 점(565 '같은 구성 하나')에서 S-1의 논리적 귀결이므로 옮긴 것 자체는 맞다. 그런데 DE-1 범위 1(1570)은 여전히 '**θ 고정 끝점 손계산 블록 하나**(정본)'가 `saturation_window`를 일반화해 모든 끝을 낸다고 적는다. 또 DE-1 (a)(1571)는 정의 창을 '평가 커널의 선형 감도 끝'으로, `node.dc_window`를 '커널 탐색과 **선언 제약 판정**이 읽는다'로 적는다. 결과적으로 끝점 블록 '하나'가 두 군데(θ 고정 블록, 봉인 뒤 블록)로 적혀 있다.

**(d) oracle tol_VDsat를 엔진 2단계가 적용(G5): gb와 뜻은 맞지만 gb 쪽 G5 문장에 tol_VDsat가 없음.** or 421은 'tol_VDsat는 tol_V와 같이 2단계(엔진 정본 LUT 함수)'라고 적는다. gb N3.8 'oracle 훑기 점의 계산 자리'(565, O-50 G5)는 I_off·tol_V만 열거한다. 정의 소유는 gb이므로 gb G5 문장에 tol_VDsat를 더해야 oracle 인용이 출처를 갖는다(Minor, F8).

**(e) DV-11 엔진 card = DE-1 (c): 원칙에 맞음.** DE-1 (c)가 같은 양 A_dc(계통 offset V_id*)를 만들므로 한 변경 한 자리다. N6.1 DE-1 행(1142)과 범위(1573)에 '오케스트레이터 기본안 -- 사용자 결정 아님' 표기가 있다. DEC-23(223)이 정의를 먼저 정하고 DE-1 순서(IT-1·IT-2 뒤)와도 충돌하지 않는다. 사실 확인: `offset_analysis.py:6-7`(A_dm으로 나눔)·`:76`(`gain_zero`, a_dm) 맞음. 단 완료 조건에 σ 전환의 red가 없다(F6).

**(f) T-1이 봉인 7을 엄격하게 함: 동작 변경 분류와 맡는 card 표기가 없음(Major와 Minor 사이, F4).** 엔진 현행은 triode 선언 소자를 봉인 7에서 빼기만 한다(`E/sizing/seal_saturation.py:56` `m not in linear_devices`). triode 대조 자체가 아직 구현되지 않았다. 따라서 master 엔진과 비교하면 O-53 B1 대조를 처음 넣는 card가 동작 변경을 일으키고, T-1은 그 card의 기준을 바꾼다(VDsat − tol < VDS < VDsat 구간이 새로 거부됨). head는 '옛 기준을 대체'라고만 적었다. N4 0번·N6.3 동작 변경 분류도, O-53 B1 봉인 7 대조를 맡는 card(N6.20 EO-1 1890·1892로 추정, 확신도 중간)의 범위·완료 조건 인용도 없다.

## 3. 결함 표

| # | 심각도 | 자리(head) | 내용 | 최소 수정 |
|---|---|---|---|---|
| F1 | **Major** | gb 1476(N6.6 범위 1 '필드' 문단: "커널 선형 창 = `node.dc_window`(… +tol 판정 창)", "커널 탐색·판정 창 `node.dc_window`(+tol -- 커널 탐색·선언 제약 판정)") | S-1 뒤 `node.dc_window`는 θ 프레임 탐색 창뿐인데, 같은 문단에 선언 제약 판정 창이라는 옛 정의가 남아 N3.8(565)·같은 문단 뒤쪽 '읽는 쪽'과 모순 | 두 구절을 "θ 프레임 탐색 창 `node.dc_window`(+tol, 측정 구성 없음 -- 커널 탐색)"와 "측정 구성 판정 창(+tol -- 커널 ICMR 선언 제약)"으로 바꾼다 |
| F2 | **Major** | gb 1570(DE-1 범위 1 머리 'θ 고정 끝점 손계산 블록 하나'), 1571((i) '평가 커널의 선형 감도 끝', (ii) "`node.dc_window` … 커널 탐색과 선언 제약 판정이 읽는다") | N3.8은 `dc_window_def` writer를 봉인 뒤 블록으로 두고 'DE-1 (a)가 그 블록에 정의 기준을 더함'이라 적는데, DE-1은 손대지 않아 끝점 블록 '하나'가 둘로 적힘. (ii)는 F1과 같은 옛 정의 | 1570에 "ICMR(측정 구성) 끝은 IT-2 봉인 뒤 블록이 쓰고, 이 card는 그 블록에 정의 기준을 더한다. 경계 행 선형 감도 계산은 같은 함수 하나(사본 없음)" 한 문장을 넣는다. 1571 (ii)를 F1과 같이 바꾸고, 측정 구성 판정 창을 (ii′)로 더한다 |
| F3 | Minor | gb 565 '창 필드' 새 필드 소비자 '커널 ICMR 선언 제약 판정·커널 metric' | DE-1 뒤에는 metric이 `dc_window_def`로 옮겨지는데(1476 '읽는 쪽') N3.8 표에는 기간 한정이 없음 | '커널 metric(DE-1 전 한정 -- N6.6 범위 2)'으로 고친다 |
| F4 | Major/Minor | gb 496(N3.6 표 7행), N6.20(1890·1892 부근) | T-1이 계획상 봉인 7 triode 거부를 엄격하게 하는데 동작 변경 분류(N4 0번·N6.3)와 맡는 card가 적혀 있지 않음. 엔진 현행 `seal_saturation.py:56`은 triode를 빼기만 함 | 7행 끝에 "봉인 7 triode 대조를 넣는 card(N6.x)의 동작 변경(N4 0번·N6.3) -- 기준 = T-1"을 적고, 그 card 완료 조건에 경계 toy(VDsat − tol < VDS < VDsat → 거부) red를 더한다 |
| F5 | Minor | gb 565 `triode` 경계 판정 여유 "tol_VDsat = 같은 VDSAT 열 leave-one-out 셀값" | 정본 함수(`sat_threshold`, HC-S, O-33 (8))를 인용하지 않아 triode 쪽 여유의 두 번째 진입점이 생길 수 있음. 훑기 점의 tol_VDsat를 어느 VDS에서 읽는지(그 점, O-46 (2)) 미기재 | "tol_VDsat = `sat_threshold` 정본(HC-S)의 같은 값, 훑기 점에서는 그 점 VDS(O-46 (2))"로 바꾼다 |
| F6 | Minor | gb 1573(DE-1 (c) σ 입력 환산) | 범위에만 있고 DE-1 완료 조건에 차동 비트 동일·단일 입력 '값 없음 → 값' red가 없음(만들면 배선·검증) | DE-1 완료 조건 3에 σ 두 red를 더한다 |
| F7 | Minor | gb 565(KVL 고정 출력 구조, 커널 창과 다듬은 창이 같은 선형 감도 끝) | IT-2 기간에는 새 필드와 `dc_window_def_refined`(+tol)의 값이 같은데, 계산을 한 번만 한다는 규칙이 없음 | "같은 연립 결과를 두 필드가 공유(재계산 0)" 한 구절을 더한다 |
| F8 | Minor | gb 565 'oracle 훑기 점의 계산 자리'(O-50 G5) 대 or 421 | or은 tol_VDsat도 2단계가 쓴다고 인용하는데 정의 소유자 gb의 G5 열거에는 I_off·tol_V만 있음 | gb G5 문장의 열거에 tol_VDsat(T-1)를 더한다 |
| F9 | Info | or 18·122 | gb 인용을 절 이름으로 하고 해시는 병합 뒤 맞춘다고 명시함 | 병합 뒤 해시 맞춤 커밋 필요(O-57과 같은 절차) |

## 4. 사실 확인 (master 2e707d5d, file:line)

확인 결과 모두 맞음: `_helpers_nodal.py:26-28`(conductance_matrix, 용량 제외·저항 포함), `spec_elements.py:19-22`(루프 절단), `spec_regions.py:16-17`(`triode` 하나), `fd_jacobian.py:54-55`(`dc_window` → W4 y 폭), `offset_analysis.py:6-7`·`:69`·`:76`, `offset_systematic.py:46`, `block_residual.py:73`(세 군데 모두 `nodal_factor(conductance_matrix(ss.circuit, size), fixed)`), `metrics_aux.py:105`(`ss_circuit`), `kernel_run.py:83-99`(`dc_columns` → `dc_widths`가 봉인 전), `block_columns.py:230-231`(선언 소자 건너뜀)·`:251`(unknown)·`:778`(dc_window 쓰기). 확인하지 않은 것: `offset_systematic.py`·`aux_types.py`·`pending_metrics.py`의 A_dm 사용 자리 줄 번호(파일 이름만 적혀 있음).

## 5. 원칙 점검

- 새 상수: 없음(tol_VDsat·tol_V·ε 모두 기존 LUT·정의 인용). F5는 정본 인용 문제이고 상수 문제는 아니다.
- fail-closed: S-3 절단 해 = 정의 불능, DV-10 네 검사 불일치 = 거부, DV-11 A = 0·`.tf` 실패 = `unavailable`. 충족.
- 만들면 배선: 새 필드 소비자 = 커널 ICMR 제약(≥ 1). `node.dc_window` 소비자 = `fd_jacobian`. DV-10 지목 생산 = OP-10 엔진 커밋. 충족. σ 전환 red 누락은 F6.
- 계획 = 규칙만: 경위는 gb history v6.21(+3행)·or history v0.6.11에 있다. 본문에 '(2026-10-20 실측, 착수 때 재측정)' 같은 측정 조건 문구가 남아 있지만 이것은 기존 관행과 같다.
- DC/AC 분리: ICMR·DC 망·A_dc 모두 DC 극한·DC 야코비안으로 정의. 충족.
- 구조 독립: 반전 입력 식별은 부호 기반(role 이름 금지 유지). 충족.

## 6. 다른 계획 후속 정정 행 (master 기준)

| 계획 | 자리 | 정정 |
|---|---|---|
| headroom-chain | plan 331, 584(`node.dc_window` = '탐색·판정 창(+tol)', '동작 보존 대상') | 'θ 프레임 탐색 창'으로 이름을 정정하고, 측정 구성 판정 창도 `sat_threshold`(+tol) 소비자임을 HC-S 소비자 목록에 더한다. 59(필드 목록)에 새 필드 칸을 더한다 |
| headroom-chain | HC-S `sat_threshold` 정본 범위 | T-1 triode 반대쪽 여유(VDsat − VDS − tol_VDsat)가 같은 정본 함수를 쓰도록 소비자로 더한다(F5와 짝) |
| offset-trim | plan 755('A_dm 환산 자리 → A_dc(DEC-23·N3.8) 인용') | 이미 맞음. gb 병합 뒤 인용 해시와 DEC-23 'DV-11' 문언 출처만 맞춘다 |
| graph-consumption | 새 필드(측정 구성 판정 창) | 새 graph 필드라 소비자 ≥ 1(커널 ICMR 제약)을 graph 소비 표에 등록한다. 표에 해당 행이 있는지는 확인하지 못함 |
| oracle-portability | 422('훑기 중 이탈' 범위 조건) | gb F5 정정(훑기 점 tol_VDsat) 뒤 인용 해시를 맞춘다 |

## 7. 확인하지 못한 것

- gb 1480 소비자 표의 metric 쪽 자리(`ls_swing.py` 등)가 S-1 뒤 어느 필드를 읽는지는 대조하지 못했다(엔진 안 `"dc_window"` 소비자는 `fd_jacobian` 하나뿐임만 확인).
- 봉인 7 triode 대조를 맡는 card가 N6.20 EO-1인지는 행 번호(1890·1892) 존재만 확인했다(본문 정독 안 함).
- graph-consumption·offset 계획 전문 정독, design 40/41·oracle design 본문 대조, history 항목 문언 정독.
- or G-19 네 검사와 기존 G-19 다른 행(126·127·131·402·406·654·689·690)의 정합은 diff 행만 보았다.
