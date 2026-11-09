# 계획 v6.38.5 사용자 승인 상정 문서 (2026-10-29)

- 대상: worktree `wt/plan-v6385`, 브랜치 `plan/v6385`, 범위 `07964dfe..74e62d53`(커밋 16개: 첫째 `634310e0` ~ 열여섯째 `74e62d53`). 바뀐 파일은 GB plan(실제 수정 행 51개)과 GB history다. 열여섯째 커밋은 V11 반영이다(plan 10행 교체·행 삽입 0이라 `adb3686a`과 행 번호가 같음). 하위 계획 변경은 0이다.
- 작성: 승인 질문 문서 정리자(작성자·검증자 아님). 계획 수정 0. '실측' 칸은 아래 보고서의 측정을 인용한 것이다. 정리자가 직접 한 일은 셋뿐이다.
  - plan `07964dfe`↔`adb3686a`↔`74e62d53` 행 diff로 '원래 취지와 다름' 표지 자리를 뽑았다(스크립트는 scratchpad, 결과는 §2 (iii)·§3).
  - 원문 PDF 경로가 있는지 확인했다.
  - HCA `p8_exact_slice.out.json`의 회로별 점 수를 셌다(Q-W1 실측 칸).
- 약어
  - E = `wt/_drafts/evidence/2026-10-29/`
  - GB = `wt/plan-v6385/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(행 번호는 `74e62d53` 기준). H = 같은 자리 `.history.md`.
  - V1~V11 = E`plan_v6385_validation{1..11}.md`(V11 = `adb3686a` 검증). V12 = `74e62d53` 검증으로, 진행 중이라 인용하지 않았다.
  - ER = E`erfc_region.md`, FD = E`flow_derivation.md`, CB = E`classab_battery.md`, CR = E`cbox_rereview.md`, DI = E`plan_v6385_design_impact.md`(계획 열째 커밋 `6b0d70f6` 기준), HCA = E`handcalc_principle_audit.md`, UD = `wt/_drafts/user_decisions.md`
  - 원문
    - Wu 2025 = C. Wu 외, Sensors 25(8):2523, 2025, https://pmc.ncbi.nlm.nih.gov/articles/PMC12031453/ . 로컬 `chip-design-skills/skills/analog-gmid-design/assets/heldout/sources/erfc_ota__wu_2025/source.pdf`(텍스트 `paper.md`).
    - Xie 2019 = Xie & Chen, 'A 126µW Current-Reuse Telescopic OTA with Class-AB Output Stage'. 로컬 `chip-design-skills/skills/analog-gmid-design/assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`. 웹 링크는 찾지 못했다(CB 머리).
    - Razavi 1판 = B. Razavi, *Design of Analog CMOS Integrated Circuits*. 저장소 안에는 로컬 PDF가 없다. 저장소 밖 `G:/내 드라이브/work/Todoc/기술문서/Gm_over_Id/Design of Analog CMOS Integrated Circuits (Behzad Razavi)marcado.pdf`에 있다(존재 확인). 발췌 텍스트는 `wt/_drafts/evidence/2026-10-23/icmr_definition_review/analysis/razavi.txt`다.
  - 판정: 맞음 / 조건부 / 틀림 / 불확실. 확신도: 상 / 중상 / 중 / 중하.
- 손계산 원칙(O-173 E-0·E-1·E-2): gm/ID 손계산을 우선하고, 오차는 DEC-72 `model_error`로 기록하고, 최종 확정은 SPICE 오라클이 한다. 이 문서는 'SPICE 수치와 같다'를 근거나 판정으로 쓰지 않는다. SPICE·ngspice 값은 물리 결정자의 크기·경계·오차 기록으로만 인용한다.
- 사용자 결정 번호(O-173·O-174·'10번'·N13·U-35 등)는 사실 기록으로만 적고 근거로 쓰지 않는다.

---

## 0. 머리

### 0.1 이 판의 경위(5줄)

1. **시작 항목 셋**(첫째 커밋 `634310e0`).
   - (a) O-174: erfc M19~M21 영역 선언 대신 구조 규칙 하나를 둔다. 'DC 원소가 채널 하나뿐인 넷 → VDS = 0 묶음'이고, bulk = source일 때만 적용한다(ER). O-173 Q-4를 대체한다(사용자 결정됨).
   - (b) design 단순화 검증 2 MJ-B: WB-1 범위 3이 지울 상태를 커널 쪽으로 한정하고 cfg 이름은 남긴다 → **Q-CF1**.
   - (c) design v1.15.3 40 §3.7-A 2-5 멈춤: DEC-105 (2)에 '탐색 평가(θ 유도 W) 대 실현 평가(W′, front 점)'를 신설한다 → **Q-W1**.
2. **검증 1~10 흐름**: 모두 '승인 상정 불가'였고 Critical은 0이었다.
   - V1~V11 Major 수: 7 → 3 → 2 → 2 → 1 → 3 → 2 → 2 → 3 → 2 → 1. Minor 수: 9·5·5·6·6·6·5·8·8·5·5.
   - 매 커밋이 직전 검증을 반영했다.
   - 열다섯째 `adb3686a`은 V10을 반영했다. MJ10-1은 판별 입력을 기존 필드 `graph.dc_current_basis`로 정했고, MJ10-2는 결합 C 갈래를 card DR-1로 옮겼다(O-165 (a) 4축 비교).
   - 열여섯째 `74e62d53`은 V11을 반영했다.
     - MJ11-1: 적용 상자 writer = 기존 검색 정의역 S0 블록(`search_domain` 자리), 층 = `dc_current_basis`·`theta_schema` 뒤. 선언 상자(SF-1 범위 6 (e))와 적용 상자는 정의 축이 다른 두 필드로 나눴다. 사본 칸 `StartView.theta_bounds`를 지우고 소비자 목록을 바로잡았다.
     - m11-2: DR-1 완료 (10)에 결합 C toy를 넣었다.
     - m11-3·m11-4·m11-5: 인용을 고쳤고, `theta_bound_element` 교차 검사는 그 블록 안 거부로 남겼다.
   - 열여섯째 커밋의 독립 재확인이 V12(진행 중)다.
3. **사용자 질문으로 생긴 항목**
   - 'f_low를 이론적으로 정할 수 있나' → FD → f_low 전제를 철회하고 f_HP 상한(U1~U4)을 유도, 기하는 면적 최소 W_min·L_min(일곱째 커밋) → **Q-ZG1**.
   - 사용자 탐색안 'R 하한'·'R 상한/창' → (라)·(마)로 비교하고 비권고로 기록(아홉째·열째).
   - 'current_reuse 배터리 결정자 점검' → CB → **Q-CA1**(spec 제약 삭제)·**Q-KV1**(고리 종속 멤버, 여덟째~열한째).
   - θ 커패시터 상자 '10번' 재검토 → CR → **Q-CB1**(역할별 분리, 열셋째~열다섯째).
   - 보상 C 하한 → **Q-CB2**(열린 질문, V9 m9-7·V10 m10-3).
4. DI(design 영향 대조, 열째 커밋 기준)를 열두째 커밋 `a314f82f`에 반영했다.
   - design 멈춤 자리 인용을 '§3.7-A 2-5'로 고쳤다.
   - Q-W1 권고안 표지와 대안 채택 시 되돌릴 목록을 넣었다.
   - DR-1 착수 조건의 N3.4 W2 행을 넣었다.
   - erfc front가 비는 경우를 'fail-closed 기록'으로 분류했다.
5. **이 문서가 상정하는 것**: 결정 질문 6개(Q-W1·Q-CF1·Q-ZG1·Q-CA1·Q-KV1·Q-CB1)와 열린 질문 1개(Q-CB2). Q-W1은 지금 결정하지 않는다(착수 실측 뒤). 계획 v6.38.5 병합 승인은 **V12가 Major 0으로 끝난 뒤**에만 상정할 수 있다.

### 0.2 남은 열린 측정

| ID | 무엇 | 언제·누가 | 막는 대상 |
|---|---|---|---|
| V12 | `74e62d53`(V11 MJ11-1·m11-1~5 반영) 독립 재확인 | 독립 검증자(진행 중) | **계획 v6.38.5 승인 상정 전 필수** |
| Q-W1 착수 실측 | 두 측정 구성(선언 입력 고정 / servo)의 ΔV_out 대 출력 창, servo ΔV_id 대 성분 (3) 1차식, front 소속 변화 수. 점별 ID/gds·A_후단. 엔진은 고치지 않는 읽기 전용 스크립트(Q-P8 `p8_exact_slice` 선례) | card WB-1 착수 실측 | Q-W1 결정 → 일괄 반영·검증 → design |
| Q-T0·Q-T3 | tol_V 셀 구성 정정 시 9회로 봉인 거부 변화, tol_I 집계(최댓값 → 합) | card WB-1 착수 실측(이월, O-173) | Q-T0·Q-T3 결정 |
| Q-KV1 E-0·E-1 | (다) 다이오드 종속에서: 고리 닫힘, 종속 다이오드 W가 LUT 정의역 안, 모든 소자 포화. I_Q 손계산 대 oracle(E-1). 지금 실측은 배터리 종속(−0.014 %) 하나뿐이고, 출력 종속(as-built)·다이오드 종속((다))은 미측정 | card TB-1 design 전 | Q-KV1 확정((다) 착수 조건) |
| Q-KV1 P3 | 같은 예산에서 종속 멤버 선택별 front 비교 | card LA-1·ME-1 뒤 | 다시 열 계기에만 쓴다 |
| Q-CB1 하한 값 | 결합 C 하한 = oracle `.tran` SR sweep 경계. 격자 간격과 반복성(잡음 ±0.7 V/µs 대비 여유)을 함께 기록한다. 지금 값(1.0 FAIL / 1.5 pF PASS)은 sky130 대용 bench의 경향일 뿐이다 | card SF-1 `.tran` SR 항목(계단 크기) 정의 뒤 재측정 → data 커밋 + 사용자 승인 | 결합 C 상자 값(결정 자체는 막지 않음) |
| Q-CB2 | 보상 C 하한 고착이 결정을 바꾸는지(E-2) | card LA-1·ME-1 변화표 | Q-CB2 상정 |
| Q-ZG1 U4 | R_ds ≫ R_X 부하(MNA GBW) 거부 여부. 거부되면 사유를 기록하고 계획을 개정한다 | card DR-1 완료 (9) MNA toy | 없음(완료 조건) |
| erfc front 공백 | Q-CB1 승인 뒤에도 남는 원인: θ 의존 SR_∞·C_g,eff, 경계 여유 < 측정 잡음, 정류 표류. 이 위험은 남는다 | card DR-1 heldout 판정 기록 | 없음(fail-closed 기록, card 완료를 막지 않음) |

---

## 1. 질문별 표

칸: 무엇을 바꾸나 / 권고 / 대안·⚠ / 물리 결정자 / 회로이론 근거(식, 원문 쪽 + 로컬 PDF) / 실측(n/13 또는 n/9, 증거) / 판정·확신도 / 원래 취지와 다름 / 결정 시점 / design 반영 자리(DI 표) / card 순서 영향.

### Q-W1 -- 탐색 평가 대 실현 평가(GB 1161, DEC-105 (2) 304)

| 칸 | 내용 |
|---|---|
| 무엇을 바꾸나 | `DeviceOp.W`는 한 필드이고, 평가 입력 축은 둘이다. (i) 탐색 평가(SLSQP·층 0): W = θ 유도 I·L/IDu_s(조각 안 연속), 잔차 r은 기록만. (ii) 실현 평가(front 점): W′ = m·w_s, W′·바이어스 고정 KCL 비선형 재풀이, N3.6 봉인 전 항목(봉인 9 포함)을 재적용. 측정 구성 = DEC-23 V_id* 정의와 같은 servo다. 출력은 탐색 봉인점 `node.dc_v[out]` 기록 참조에 묶고, 입력 차는 미지수다. 피벗 판정은 IT-2 판정 기록을 참조하고, 실현 점 판정과 다르면 fail-closed다. 실현 평가를 거치지 않은 점은 front·선택·oracle 입력이 될 수 없다. 탈락 뒤 재필터한다. E-1·결과·oracle = 실현 값. DEC-23 성분 (3)을 성분 (1)에 흡수(식 삭제). 순서는 IT-1 + IT-2 → WB-1 → DE-1 |
| 권고 | 위 (i)(ii) + 순서 (ii). **지금은 결정하지 않는다.** 본문에는 'Q-W1 승인 시' 표지와 '권고안 문언' 표지·되돌릴 목록만 있다 |
| 대안·⚠ | (가) 매 평가 재풀이(O-173 C1 문언 그대로) ⚠ 조각 안 W′가 상수라 W·면적·용량 축 기울기가 0인 계단이 된다 → SLSQP 유한차분 기울기가 그 축에서 사라진다(추론, 선택 함수 미구현이라 실측 불능). (나) 매 평가 둘 다 풀기 ⚠ DC 풀이가 2배다. (다) 측정 구성 = 선언 입력 고정 ⚠ 출력이 ΔV_out ≈ r·V_A,eff·A_후단만큼 움직여 봉인 7이 깨지고, 닫힌 루프에서 정상인 점이 front에서 빠진다(E-1 결정 뒤집힘, 추정). (라) 성분 (3) 1차식 유지 ⚠ 같은 ΔW 효과를 두 자리가 낸다(graph 규칙 1), r 37 % 꼬리는 선형 범위 밖이다. 순서 (i) DE-1 → WB-1 ⚠ WB-1 → LA-0 → LA-1 사슬이 DE-1 선행 전체 뒤로 밀린다. 순서 (iii) 고정 해제 ⚠ 조건부 완료(O-165 (a))라 철회했다. **⚠ 원칙 경고**: 탐색 봉인점에 E-0 슬라이스 조건을 적용하지 않는 것은 E-0 범위 축소다. 실현 평가가 front의 유일한 실현 관문이 된다 |
| 물리 결정자 | (1) 탐색은 θ에 대해 조각 안 연속인 함수가 필요하다(유한차분 기울기). (2) 봉인·판정·oracle은 실현할 수 있는 소자(W′)를 봐야 한다(E-0). (3) 바이어스 고정 개루프 고이득 증폭기의 출력 DC는 전류 균형으로 정해져 감도가 크다. 그래서 측정 구성은 servo(출력 고정·입력 차 미지수)여야 실현 잔차가 입력 차로만 나타난다 |
| 회로이론 근거 | servo 정의 = 'the input level that forces the output voltage to go to zero'(Razavi 1판 §13.2 p.466 -- 로컬 PDF는 저장소 밖 G: 드라이브, 위 약어). 선언 입력 고정 시 ΔV_out ≈ (ΔI/I)·V_A,eff·A_후단(출력 노드 KCL, V_A,eff = ID/g_out). servo 시 ΔV_id ≈ ln(1 + r)/(gm/ID)(약반전 지수 꼴, 1차식 r/(gm/ID)). 탐색 조각 끊김 크기 = 인접 슬라이스 IDu 비(bin 양 끝 0.54~1.74배) |
| 실측 | 잔차 r: 65 소자-점, **5/9 회로**(folded_cascode 20·two_stage_ota_sf 15·nmcnr 15·two_stage_ota 10·pushpull 5), 중앙 1.07×10⁻⁴, p90 0.134, 최대 0.373(E`handcalc_principle_audit/p8_exact_slice.summary.json`·`.out.json`; 회로별 점 수는 정리자 집계). servo ΔV_id 식의 LUT 검산: nfet L 0.5·1 µm, r 0.01~0.37, ln(1+r) 꼴 오차 2~7 %(V5 `plan_v6385_validation5/wb1_toy.txt`). 다단 ΔV_out·front 소속 변화: **0/9(미측정, 추정)** -- WB-1 착수 실측 몫. 비용 13~261 ms/평가(F-LA10 인용, 실측 아님) |
| 판정·확신도 | **조건부 맞음**(조건: 착수 실측에서 servo 구성의 front 소속이 유지되고 선언 입력 고정 구성의 봉인 7 탈락이 실제로 나타나는가). 확신도 중(선형 감도 추정). V5~V10 모두 '상정 가능(결정은 실측 뒤)'으로 판정 |
| 원래 취지와 다름 | **예(후보)**: O-173 C1 재풀이 자리(DC 블록 매 평가 → 실현 평가), O-173 Q-P8 슬라이스 폭 적용 범위 = 실현 평가, E-0 범위, DEC-23 성분 (3) 흡수(O-46·O-118·O-119), X-LA11 근거 교체(순서는 유지), IT-2 '선후와 무관, 새 순서 규칙 0' 정정(IT-2 → WB-1 추가) |
| 결정 시점 | card WB-1 착수 실측 → Q-W1 결정 → 계획 일괄 반영·검증 → design |
| design 반영 자리(DI §2.1) | 권고 승인 시 다음이 바뀐다. 40:1142 §3.7-A 2-5(매 평가 재풀이 삭제 → 탐색 평가), 40 §3.7-A 새 '실현 평가' 절, 40:1131~1135(extras에 레이아웃 전 실현 기하), 40:1143·1148·1149·1150·1151·1159·1160·1183·1226·1300·2085·2196·2197, 41:737 (1)·780 (6)(피벗 판정 소비자 = 실현 servo, '출력 전용' 해제), 41:1427·1431·1435·2018·2019, 42:137·330·331, DE-1 design(성분 (3) 삭제·불일치 toy). 대안 (가)이면 40:1142 2-5를 유지하고 W′ 전 소비자를 바꾼다. 결정 전에 고칠 수 있는 자리: 계획 쪽 인용 정정은 열두째 커밋에서 끝났고, design 쪽은 없다 |
| card 순서 영향 | (ii)이면 WB-1 선행에 IT-1 + IT-2 통합 병합을 추가한다. 그러면 WB-1 → LA-0 → LA-1 사슬이 IT-1 + IT-2 뒤로 간다. DE-1은 WB-1 뒤 그대로다(근거 교체). (i)이면 WB-1이 DE-1 선행 전체(SF-1·IT-1·IT-2·HC-S·EO-1·VB-1·card B) 뒤로 간다. 대안 (다)는 IT-2 선행이 필요 없다 |

### Q-CF1 -- WB-1 범위 3 cfg 공유 이름(GB 1162)

| 칸 | 내용 |
|---|---|
| 무엇을 바꾸나 | WB-1 범위 3(E-13)이 지우는 상태를 **커널 쪽**으로 한정한다. 커널 상태 쓰기와 상수 `INPUT_STATUS_UNSETTLED`만 지운다. 측정 구성 창(`node.dc_window_cfg`, IT-2c `icm_config`)이 쓰는 이름 `INPUT_STATUS_MEASURED`·`INPUT_STATUS_UNMEASURED`·`Window.input_status`·`Window.tol_v`는 남긴다. grep 0 범위 = 커널 경로 |
| 권고 | 안 A |
| 대안·⚠ | B: cfg 전용 새 타입 ⚠ 새 타입이 생기고, IT-2c design 재개정 → IT-2c·IT-2d card 재동결 → IT-1 + IT-2 통합 병합 지연(Q-W1 (ii)이면 WB-1·LA-1까지 연쇄 지연) |
| 물리 결정자 | 해당 없음. 이름·필드 범위 결정이고 물리 양이 바뀌지 않는다. 규칙 근거는 graph 규칙 3이다. E-13 뒤 상태 생산자가 `icm_config` 하나라서 같은 이름이 두 뜻을 갖지 않는다 |
| 회로이론 근거 | 해당 없음(회로 식 대상 아님) |
| 실측 | 엔진 이름 사용처 전수(V1 §2.1, integ-it12 `41a1278b`): 네 상수와 `Window` 칸은 커널(`block_columns.py:755·761·780·789·796·799·805·810`)만 쓴다. cfg는 미구현이다. `sizing.__all__`에는 `Window`만 있다. 회로 값 변화: n/9 **해당 없음**(이름 범위 변경, 동작·값 변화 0) |
| 판정·확신도 | **맞음**, 상. V1~V10이 '상정 가능'을 유지했다 |
| 원래 취지와 다름 | 아니오 |
| 결정 시점 | card WB-1 범위 3a 착수 전(지금 결정 가능) |
| design 반영 자리(DI §2.2) | A이면 다음이 바뀐다. 40:1458(지울 목록 → `INPUT_STATUS_UNSETTLED` + 커널 쓰기), 40:2183·41:746(표지만 삭제), 41:630·658(같은 `Window` 타입, 커널은 상태 칸 None -- MJ-B 모순 해소), 40:461·1134·1456, 41:650·664·672, 42:342('칸 삭제' → '커널 쓰기 없음'), 41:2020·40 §3.11-1(grep 범위 = 커널 경로), 'IT-2c 예약(생산자 = cfg)' 표기. 결정과 무관하게 고칠 자리: 41:737 (2), 40:461 옛 꼴 |
| card 순서 영향 | A이면 무변경(3a가 IT-2c 앞이든 뒤든). B이면 IT-2c 재동결로 연쇄 지연 |

### Q-ZG1 -- DR-1 구조적 0 전류 MOS 기하 출처(GB 1163, N6.36 2348~2352)

| 칸 | 내용 |
|---|---|
| 무엇을 바꾸나 | O-174 VDS = 0 묶음 소자(erfc M19~M21)의 기하(W·L) 출처를 정한다. 넷째~여섯째 커밋에서 도입한 f_low 칸·f_low 존재 조건 제약 행·(δ) f_low 선택과 'SF-1 선행(f_low 선언 자리)'을 **철회**한다. 기하는 면적 최소 W_min·L_min(LUT 격자)으로 한다. 엔진 상한 행은 두지 않는다. f_HP·τ 기록 칸 하나를 둔다(출력 전용). 추가 선행·착수 실측은 없다 |
| 권고 | (나) f_HP 상한 유도 + 면적 최소 W_min·L_min. C 상자는 Q-CB1에 따른다. (i) fail-closed 기록은 함께 유지한다 |
| 대안·⚠ | (가) f_low 선언 ⚠ 근거 없이 R·C(면적)를 키운다. (다) 기록만 ⚠ 상한을 넘는 기하를 못 막는다. (라) R 하한 선언(사용자 탐색안, 예: R ≥ 100 GΩ) ⚠ R은 VSG에 지수 의존한다. 물리 결정자가 없으면 상수 발명이다. 큰 R은 정류 회복을 늦춘다 → **비권고**. (마) R 상한·창(사용자 질문) ⚠ 상한 ≥ R(W_min, L_min)이면 (나)와 같다. 미만이면 W로 최대 약 4.2배(3.6~4.5배)만 낮춘다. 결정자(회복 속도 하한)가 spec에 없어 상수 발명이다 → **비권고**. erfc front 공백 처리: (i) 수용 ⚠ front 공백 / (ii) 엔진 C_BAT 하한 ⚠ O-122 충돌 / (iii) 결합 C spec 선언 상자 = Q-CB1 (나) |
| 물리 결정자 | 부유 전지 경로의 목적은 대신호 슬루에서 M3B 포화를 유지하는 것이다. f_HP 아래에서도 OTA는 고정 바이어스로 증폭한다(DC 이득은 f_HP와 무관). 그래서 'f_HP ≪ 신호 대역 하한'은 틀렸다. f_HP **상한** = U1 대신호 처짐(τ = R_ds·(C_c + C_g) ≫ t_slew, oracle `.tran` 몫 -- O-122), U2 doublet(정착 제약이 선언됐을 때만), U3 PM, U4 R_ds ≫ R_X 부하(U3·U4는 R_ds·C_c MNA 스탬프). **하한**은 spec 양에서 나오지 않는다(시동 회복·정류는 spec 밖) → 면적 최소 |
| 회로이론 근거 | Wu 2025 p.3 §2.2(paper.md 184-186, 과도 응답 중 동작점 이동 방지), p.7 §3.1 Fig.5(333-352, 'lower low cut-off' = RC HPF 자신의 차단), p.7-8 §3.2(358-360, deep triode active resistor), p.9 Table 1(M19~21 3/1 µm, CBAT 값 없음), p.13-14(796-825, 600 mV p-p·19.32 V/µs). 로컬 PDF는 위 약어. 약반전 채널 I_D = I_0·e^{(V_SG−\|V_th\|)/(nV_T)}·(1 − e^{−V_SD/V_T}) → I = 0 ⇔ V_SD = 0(ER §2). doublet 꼬리 A_s = k·f_HP/((1+k)·β·f_u)는 FD §2에서 직접 유도했다(Kamath·Meyer·Gray 1974 JSSC -- **로컬 PDF 없음**) |
| 실측 | 구조 발동 **1/13**(erfc 넷 셋, library 9 + heldout 4 전수, V1 `plan_v6385_validation1/dr1_net_audit.txt`). AC 결합 게이트 + 고저항 꼴도 erfc 셋뿐이다(FD `flow_derivation/s5_corpus.txt`). DC 이득은 f_HP와 무관하고(73.059 dB), 결합 기여 k ≈ 1.6 %다(FD `s2_op_ac.txt`). SR은 고정 게이트 0.65/0.53, 결합 47/19 V/µs다(FD `s3_tran.txt`). W_min·L_min @ 1 pF일 때 f_HP 0.9 kHz(M19)·18.7 kHz(M21)로, 무해 경계(소신호 약 149 kHz, SR 약 100 kHz) 안이다. C 1.5 pF일 때 12.4 kHz·0.60 kHz로 재현했다(2/2, V9 `plan_v6385_validation9/fhp_check.txt`, `plan_v6385_v3/zg1_alt.txt`). R(W) 비단조(V8 `zg1_w_ratio.txt`: L 0.15에서 R(0.42)/R(7) 3.65~4.48). 정류 표류(C 1 pF 60주기 0.700 → 0.540 V 진행, 0.1 pF 0 -- FD `s6_pump.txt`) |
| 판정·확신도 | **조건부 맞음**(조건: O-122·U-112(닫힘) 유지). 확신도 중(f_low 철회는 중상, FD 결론 1. 상한 유도는 중, FD 결론 2). V10에서 '상정 가능' |
| 원래 취지와 다름 | **예**: f_low 칸·f_low 존재 조건 행·SF-1 선행 사유 철회(GB 1163·2348·2350·2352). 이 판 넷째~여섯째 커밋 전제의 철회다. (라)·(마) 비권고는 사용자 탐색안과 다른 권고다(표지는 대안 칸) |
| 결정 시점 | card DR-1 design 착수 전(추가 실측 없음 -- 지금 결정 가능) |
| design 반영 자리(DI §2.3) | design v1.15.3에는 DR-1 본문이 없다(grep 0). 그래서 **새 DR-1 design**에 다음을 쓴다: 기하 W_min·L_min, 소신호 스탬프(VDS = 0 점 gds·기준 폭 용량·gm = 0), C_c 정의. 40 §3.8 f_HP·τ 칸(writer 하나, 출력 전용). 40:1131·1132 L writer(`dc_lengths`)와 겹치는지 S-7로 확인한다(DI C5 -- V9는 '갈래로 두면 writer 하나 유지, θ 스키마에서 그 소자 L 키 제외는 design 몫'). 40 §3.7-A 2-1·5(선택 함수 밖 0 전류 소자 값). 40 §10.5(front 전부 `oracle_only_fail` 분류 -- 계획 2352가 'fail-closed 기록'으로 정함). 42에 새 D-DR1 행 |
| card 순서 영향 | (나): DR-1 선행 = IT-1 + IT-2 그대로이고, SF-1 선행은 철회한다. 단 Q-CB1 (나)·(α)·(Q)가 승인되면 SF-1 → DR-1이 다시 더해진다(사유가 다름: 결합 C 상자 갈래). (가)·(라)·(마)이면 SF-1 선행이 복원된다(spec 키). (ii)이면 O-122 재결정이 먼저다 |

### Q-CA1 -- 파일럿 spec 제약 `classab_centering_dev_v ≤ 0.15`(GB 1164)

| 칸 | 내용 |
|---|---|
| 무엇을 바꾸나 | current_reuse spec의 `user_spec` 제약 \|VGS16 − VSG15\| ≤ 0.15 V. metric이 아직 등록되지 않아(MOD5) 판정은 꺼져 있다. 등록되면 켜진다 |
| 권고 | (가) 삭제(spec data 커밋, 소비자 0 확인). 계획은 결정하지 않고 사용자 결정을 기다린다 |
| 대안·⚠ | (나) 출력 전용 metric ⚠ 소비자 0(만들고 안 씀). (다) 유지 ⚠ 상수 발명·물리 결정자 없음·정상점 거짓 거부 |
| 물리 결정자 | **없음**. 이 제약이 대신하려는 것(배터리 헤드룸·출력 소자 포화·1단 헤드룸)은 VDS-1·R-1′ 행이 일반형으로 이미 판정한다(CB 결정자 4·6). 옛 기록에는 이 제약이 V_bat < 0인 점을 통과시킨 전례가 있다(H 4191 인용, CB R-A) |
| 회로이론 근거 | 고리 KVL VSG11a + VSG11b = VSG15 + VSG9a, V_bat = vdd − VSG15 − VGS16 ≥ VDsat(M9a, M9b)(CB 결정자 4). 원문 동작점 \|0.475 − 0.487\| = 0.012 V(Xie 2019 p.7 Fig.7(b)), class-AB barely-on(p.2 §II.B). 로컬 PDF는 위 약어 |
| 실측 | 제약 보유 **1/13**(current_reuse spec, `git grep classab_centering` -- 엔진 레지스트리 미등록, `SPEC_CONTRACT.md:233`). sky130 대표점에서 모든 소자가 포화한 정상점이 \|0.624 − 0.876\| = 0.252 V로 거짓 거부된다(CB §3 R-A, `classab_battery/design_out.jsonl`·`rep_point.py`). 원문 180 nm 점은 0.012 V다 |
| 판정·확신도 | (가) 권고 **맞음**, 상(물리 결정자 없음·공정 의존 상수·정상점 거부를 실측). V6~V10에서 '상정 가능' |
| 원래 취지와 다름 | **예**(채택하면 U-35 `user_spec` 제약을 삭제한다) |
| 결정 시점 | card SF-1 spec data 커밋 전, 또는 그 metric을 등록하는 card 착수 전(지금 결정 가능) |
| design 반영 자리(DI §2.4) | (가)이면 design 변경 0이다(40:1867 §9.2 파일럿 spec 표에 이미 없음). SF-1 spec data 커밋 범위(40 §3.1-1·42 SF-1 행)에 '삭제 1건' 기록. (나)이면 40 §3.8-8 metric 어휘·레지스트리 행이 생긴다. (다)이면 등록 순간 판정이 켜진다 |
| card 순서 영향 | (가): SF-1 spec data 커밋 범위에 삭제 1건, 순서 무변경. (나)·(다): metric 등록 card가 생긴다(미정) |

### Q-KV1 -- `kvl_branch` 고리 종속 멤버 선택과 옛 OrderHints(GB 1165, DEC-95 294·DEC-104 303·TB-1 2209~2217)

| 칸 | 내용 |
|---|---|
| 무엇을 바꾸나 | θ 기저에서 고리마다 종속 멤버 하나를 고르는 규칙. 쓰기 계획의 종속 멤버가 곧 θ 기저 종속 멤버다(필드 `device.dc_coord` 하나, writer `dc_writer_plan` 하나). as-built는 출력 M15·M16·M25·M26이 종속이다. 옛 OrderHints는 구현돼 있지만 배선되지 않았다(`stage_b.py:152`) |
| 권고 | **(다)**: 고리에 R13 B 멤버가 있으면 B 멤버가 종속이다(B 안 순위 = diode → 대칭 궤도 대표 → 이름. ratified 선택은 B 안에서만 하고, 아니면 정지·기록). DEC-95 (3) ①·②는 B 멤버가 없는 고리에만 쓴다. R13 S/B/F는 쓰기 계획 **앞** S0 블록이 쓴다(입력 S1v `Block.roles`·spec·L 동치류, `dc_coord` READS 0). **+ (A)**: OrderHints 클래스와 Kruskal 키의 gm 요구·stage 단계를 지우고, 쓰기 계획 키를 R13 READS로 재작성한다. 배선 card = TB-1 |
| 대안·⚠ | (가) 규칙 변경 없음 + ② 입력만 S0 술어 ⚠ 배터리가 F이면 L-11('B는 어느 층에서도 독립 변수가 아니다')·R6과 모순이 남는다(고리 {M14a, M14b, M16, M9b}에서 다이오드 둘이 θ 독립 좌표가 됨). (나) ② → R13 S·F 독립 ⚠ 같은 모순 + R13 앞당김이 필요하다. (라) L-11 적용 범위 개정 ⚠ O-127·O-128 θ 기저 원칙을 바꾸고 얻는 것이 없다. OrderHints (B) 그대로 배선 ⚠ 'GB5 gm 요구'가 S2 양이라 S0 쓰기 계획에서 층 역전. (C) 미배선 유지 ⚠ 만들면 배선 위반 |
| 물리 결정자 | KVL이 닫히면 물리 해(dc_op)는 종속 멤버 선택과 무관하다. 선택은 θ 매개화(탐색 분포·독립 좌표 위 상자)와 종속 소자의 LUT 정의역(E-0)을 바꾼다. 그래서 판정 기준은 E-0·E-1 (a) 위반, 승인 규칙 두 개(L-11·R6 대 DEC-95 (3))의 모순, P3 탐색 품질이다 |
| 회로이론 근거 | translinear 고리 VSG11a + VSG11b = VSG15 + VSG9a, VGS14a + VGS14b = VGS16 + VGS9b(CB §0). 원문 Fig.7(b) 고리 수치 1.0675 = 1.0676, 1.062 = 1.062(Xie 2019 p.7). M9b는 CG 꼴이다(source = Vop1 입력, drain = Vg15 출력, 배터리 전달 H0 = (gm9b + gmb9b + gds)/(gm9a + gmb9a + gds)의 분자 -- CB 결정자 3). 로컬 PDF는 위 약어 |
| 실측 | 부유 상보쌍 **2/13**(current_reuse·r2r, `classab_battery/scan13.out.txt`). current_reuse `kvl_branch` 4고리(`s1_cycles.out.txt`). as-built 종속 = 출력(`writer_plan.out.txt`). 배터리 종속 θ 기저에서 I_Q −0.014 %, 고리 닫힘(`design_out.jsonl`). (다) 6고리 선택 재현: current_reuse 4/4 → M11a·M14a·M20a·M23a(V9 `plan_v6385_validation9/loop_pick.txt`). 버퍼 2고리는 J12-f ratify 대기라 생략했다. M9a S1v = pass·forward·main_path(V8 `s1v_m9a.txt`). OrderHints 참조 파일 9개(V10 엔진 grep). 순환 0·층 역전 0(엔진 실행 순서 `stage_a.py:238` → `kernel_context.py:85`, V9). **다이오드 종속 E-0·I_Q: 0/1 미측정** |
| 판정·확신도 | **조건부 맞음**(조건: TB-1 design 전 E-0(고리 닫힘·종속 다이오드 W가 LUT 정의역 안·모든 소자 포화)과 I_Q E-1 실측). 확신도: (가) 모순 성립 = 상(M9b F 상), (다) 동작 = 중(미측정). V10에서 '상정 가능(m10-2 문언 -- 반영됨)' |
| 원래 취지와 다름 | **예**: DEC-95 (3) ①·② 개정, TB-1 범위 1(R13 writer 위치)·card 성격 확장(필드만 → 쓰기 계획 배선, 동작 변경), DEC-104 (3)(a) '쓰기 계획 다음' → 앞, O-144 J3·O-146 K2·O-149 병합 규칙 재검토(첫 행동 소비자 = TB-1 자신) |
| 결정 시점 | card TB-1 design 착수 전, E-0·I_Q 실측 뒤. 다시 열 계기: TB-1 R13 분류에서 고리 종속 멤버 ∉ B, E-0·E-1 (a) 위반, P3 실측 |
| design 반영 자리(DI §2.5) | DI는 권고가 아직 (가)였던 열째 커밋 기준이라, 이 칸은 DI의 '(나)(다)' 행을 쓴다. 40:449 §2.4.8 `theta_class`, 41:874·1406 E11('쓰기 계획 다음 S0 블록' → '쓰기 계획 앞'), 41:898·1318, 40:2193 TB-1 행, 40:1107 §3.7 항목 4(순위 규칙 diode → 대칭 궤도 대표 → 이름), R13 X 칸 제거. 상태 칸 40:1122·42:134·267, 41:1703 '종속 = DEC-95 (3) 우선순위' |
| card 순서 영향 | TB-1 범위에 `writer_plan.py`·`kernel_context.py`·`sizing/__init__.py` 추가, 삭제 대상 `s2_values.py`·`sizing/CONTRACT.md:1001-1004`·test 5파일. 파일 겹침 card IT-1·DR-1(같은 통합 병합 금지, 나중 card가 rebase). 동작 변경 card라서 SPICE 다리 선행 EO-1. O-149 'HC-1·LA-1 가운데 먼저와 같은 통합 병합' 규칙의 전제가 사라진다 → 재검토. TB-1 design·HC-D design 재작성 |

### Q-CB1 -- θ 커패시터 상자 역할별 분리(GB 1166, DEC-105 (10)(a) 304·SF-1 범위 9 2195·DR-1 2352)

| 칸 | 내용 |
|---|---|
| 무엇을 바꾸나 | '10번' 공통 상자 [0.1 pF, 10 pF]를 역할별로 나눈다. 보상 C = 공통 상자 유지. 결합 C = 회로별 spec 선언 상자(`search.theta_bounds`), 하한 = oracle `.tran` SR sweep 실측 경계(여유 계수 없음, 격자·반복성 기록). 결합 C 판별 = 구조 규칙('C 한 끝 넷에 닿는 소자가 MOS 게이트와 구조적 0 전류 MOS(≥ 1)뿐'). 판별 입력 = 기존 필드 `graph.dc_current_basis`의 빈 항 MOS 행 READS(새 필드 0). 두 필드를 나눈다(정의 축이 다름, graph 규칙 3): '적용 상자'(원소별 탐색 상자 = 선언·공통 상자·결합 C 규칙을 합친 양)와 '선언 상자'(SF-1 범위 6 (e) spec 추출 필드, S1 앞). 적용 상자 writer = 기존 검색 정의역 S0 블록 하나(`search_domain` 자리 -- as-built `E/search/search_domain.py:76-80·106-112·124-135`, 재작성 범위로만 인용), 층 = `dc_current_basis`·`theta_schema` 뒤. 블록 본문 순서는 넷이다: 회로별 선언(선언 상자 READS) → 결합 C 선언 필수·미선언 정지(DR-1 갈래) → 그 밖 커패시터 공통 상자 → 출처 없는 θ 수동소자 정지. 로더는 구문 검사만 하고, `theta_bound_element` 교차 검사는 블록 안 거부로 남긴다(fail-closed). 소비자 재배선(적용 상자 = `domain.variables` READS): `iv_context.py:94`(사본 칸 `StartView.theta_bounds` `start_values.py:180` 삭제)·`iv_area.py:85`·`_helpers_area.py:24`·`macro_poles.py:133,141`·`achievability.py:126,248`. `search_context.py:164`는 소비자가 아니라 writer 입력이라 SF-1 범위 6 (e)가 지운다. 결합 C 갈래 card = DR-1(순서 SF-1 → DR-1, DR-1 완료 (10) toy) |
| 권고 | (나) 역할별 분리 + (α) 구조 판별·미선언 정지 + (Q) 결합 C 갈래를 card DR-1로 이관 |
| 대안·⚠ | (가) 현행 유지 ⚠ 면적이 C를 0.1 pF로 밀어 erfc 점이 모두 oracle SR FAIL → front 공백. (다) 공통 하한 상향 ⚠ 보상 C를 자르고 새 상수를 만든다. (라) 엔진 SR 행 ⚠ O-122 충돌, 정지 cgg가 1.45~2.9배 과소라 낙관 쪽. (마) front 공백 수용(= Q-ZG1 (i)). (바) O-144 재개(oracle FAIL 되먹임) ⚠ 큰 변경. (β) '선언 있으면 선언, 없으면 공통' ⚠ fail-open. writer 자리 대안 셋: 새 S0 블록 ⚠ `search_domain`의 `_passive_box`·미선언 정지가 같은 양의 둘째 생산자로 남는다(graph 규칙 1) / 범위 6 (e)의 S1 앞 블록 ⚠ `dc_current_basis` READS가 층 역전 / '결합 C만 S0 블록, 나머지는 로더' ⚠ 같은 양을 두 자리가 소자 집합으로 나눠 쓰고(graph 규칙 1), 로더는 결합 C를 판별할 수 없다. (P) SF-1 별도 커밋 + DR-1 같은 통합 병합 ⚠ 새 꼴 병합 규칙 +1, 표에서 놓치면 소비자 0 코드가 master에 들어간다. **⚠ 원칙 경고 둘**: (1) 보상 C에는 '관례를 정의로 쓰는' 상태가 남는다(→ Q-CB2). (2) 하한 1~1.5 pF는 반복 대신호 정류 표류 영역이다(oracle 반복 계단 FAIL 위험 기록). 승인돼도 front 공백 위험은 남는다(PASS 보장 아님) |
| 물리 결정자 | 결합 C 하한 = 결합비 α = C/(C + C_g,eff)(전하 분배)와 SR(대신호). 첫 주기 하한은 pseudo-R 처짐이 아니라 α가 정한다. 보상 C = PM·GBW(MNA가 판정) -- 다만 PM 목표가 있어도 하한에 붙는 경우가 있다(ngcc Cm2) |
| 회로이론 근거 | SR ≈ SR_∞·α₂, C_min = α_req/(1 − α_req)·C_g,eff(CR §3). Wu 2025 p.7 §3.1('CBAT does not need to be excessively large'), p.11-12 §3.5(SR = I_out/CL, 식 21~24 -- 전지 처짐 항 없음), p.13-14(600 mV p-p, 19.32 V/µs). 로컬 PDF는 위 약어 |
| 실측 | 13회로 θ 커패시터 전수 **13/13**: θ 커패시터 12(보상 9 + erfc 결합 3). 구조 판별에 맞는 것은 erfc 셋뿐이고 보상 9는 0이다(CR `cbox_rereview/c0_corpus.txt`, V9 재확인). SR 경계(erfc bench 1회로, O-122 정의 20-80 %): 세 C 같게 1.0 FAIL / 1.5 pF PASS, CBAT1만 0.1 FAIL / 0.2 pF PASS, 1.5 pF 상승 19.77 대 spec 19.32(잡음 ±0.7) -- `c5_sr2080.txt`. pseudo-R ↔ 이상 R 차 < 2 %(`c3_droop.txt`). SR_∞·α₂ 오차 −2~+7.5 %, 정지 cgg 1.45~2.9배 과소(`c4_fit.txt`). cnr 결합·감지 C 53.8 fF(PDK 최소도 0.1 pF 아님). 정류 표류 `flow_derivation/s6_pump.txt`. 상자를 쓰고 읽는 엔진 자리 전수(V11 §2(b), integ-it12 `b3336452` 읽기): writer는 `search_domain`(READS `dc_current_basis`·`theta_schema` `:89-90`)이다. 사본만 읽는 `iv_area.py:85`는 공통 상자 커패시터를 최소 면적 하한에서 빼서 정지 없이 틀린 값을 낸다(정적 판독, 실행 실측 아님). 빈 항 행 READS 일관성은 V11 §2(a)(`current_basis.py:130-141`) |
| 판정·확신도 | 물리 결정자 판정 **맞음**(중상). 권고 (나) **조건부 맞음**(조건: 하한 값은 oracle 실측 경계 + 사용자 승인. sky130 bench는 경향만), 확신도 중(CR 결론 5). V10·V11 '수정 후' → `74e62d53` 반영, V12 재확인 대기 |
| 원래 취지와 다름 | **예**: '10번'·N13 재질문, DEC-105 (10)(a) '값을 정하는 법칙이 없는 AC 설계 변수'(결합 C에 틀림), 상자 적용 자리 로더 → S0 블록(DEC-105 (10)·SF-1 범위 9), SF-1 → DR-1 순서(새 병합 순서 규칙 +1 -- **Status에만 표지, 본문 명시 표지 없음**, §3.4) |
| 결정 시점 | card SF-1 design(범위 9) 착수 전(지금 결정 가능). 하한 **값**은 SF-1 `.tran` SR 항목 정의 뒤 재측정 → data 커밋 + 사용자 승인 |
| design 반영 자리 | **DI 표 밖**이다(Q-CB1은 열셋째 커밋에서 생겼고 DI는 열째 기준). 정리자 추론으로 닿는 자리를 적는다: 40 §3.1-1·42:340 D-TBX(SF-1 범위 9 커패시터 상자 '10번', DI §1.2 Q-ZG1 표), 검색 정의역(`search_domain`) 블록을 다루는 design 절, 40 §2.4.8 필드 표(선언 상자·적용 상자 두 필드의 정의 축), SF-1 범위 6 (e) design(선언 상자 필드), 사본 칸 `StartView.theta_bounds` 삭제 자리, 40:1237 §3.8-3(엔진 슬루 칸 0 -- 그대로), 새 DR-1 design(결합 C 갈래·완료 (10) toy). 독립 대조는 하지 않았다 |
| card 순서 영향 | DR-1 선행에 SF-1 추가(+1, 소비자 소유 card = 첫 도달 card -- U-132 선례). SF-1 범위 9 확장: `search_domain` 자리 재작성, 소비자 재배선, 사본 칸 삭제, 완료 조건(적용 상자 writer 1곳·사본 칸 0·spec 직접 읽기 0 `git grep`·`iv_area` 공통 상자 하한 toy). DR-1 완료 (10) 결합 C toy 추가. Q-ZG1 (나)가 철회한 SF-1 선행이 다른 사유로 다시 생긴다 |

### Q-CB2 -- 보상 C(θ) 하한의 물리 결정자(GB 1167) -- 열린 질문 기록만

| 칸 | 내용 |
|---|---|
| 질문 | '10번' 하한 0.1 pF는 관례값이다. PM 목표가 없는 3회로 Cc와 PM 목표가 있는 ngcc Cm2가 모두 하한에 붙는다(STEP2 N7, CR §3). 후보 결정자: PDK 최소 MIM, 그 마디의 기생 용량 바닥(엔진 MNA가 이미 가짐) |
| 상태 | ⚠ 관례를 정의로 쓰는 상태가 남는다. **지금 결정하지 않는다** |
| 상정 조건 | 하한 고착이 결정을 바꾸는지 실측한다(card LA-1·ME-1 변화표, E-2) |
| 출처 | V9 m9-7, V10 m10-3, CR §1·§2.3 |

---

## 2. 보고 5묶음

### (i) bkit 단계표

| 대상 | Plan | Design | Do | Check | 상태 |
|---|---|---|---|---|---|
| 계획 v6.38.5(`07964dfe..74e62d53`, 커밋 16) | 작성 완료(열여섯째 = V11 반영) | -- | -- | V1~V11 완료(전부 Critical 0, Major 7·3·2·2·1·3·2·2·3·2·1), **V12 진행 중** | 승인 대기(상정 전 V12 Major 0 필요) |
| design v1.15.3(`wt/design-v115`) | -- | '계획 v6.38.5 대기' 표지 7곳(DI §1.1). Q-W1·Q-CF1·Q-ZG1·Q-KV1·Q-CB1 결정 뒤 개정 | -- | DI 대조(열째 커밋 기준) | 계획 승인·질문 결정 뒤 개정 → design-validator + design↔계획 gap |
| DR-1 design | -- | 없음(새로 작성) | -- | -- | Q-ZG1·Q-CB1 결정 뒤 착수 |
| 엔진 card(WB-1·TB-1·SF-1·DR-1 등) | -- | -- | 착수 없음 | -- | 계획 승인 대기. WB-1 착수 실측(Q-W1·Q-T0·Q-T3)은 결정용 읽기 전용 |
| erfc bulk 정정(O-174 대기열 #1) | -- | -- | 병합됨 `9caee65d` | -- | 완료 |

### (ii) 단계별 점검표 9항목

표시: 실측(경로) / agent 인용 / 해당 없음(근거). **'안 함' 칸 0.**

| # | 항목 | 상태 |
|---|---|---|
| ① | 회로·spec·엔진 선언 자리 직접 읽음 | 실측: V1 `dr1_net_audit.txt`(13회로 넷 전수), CR `c0_corpus.txt`(13회로 커패시터 전수), CB `scan13.out.txt`·`s1_cycles.out.txt`(topology `netlist` 직접 판독), ER `net_audit.txt`, V9 `topo_current_reuse_loops.txt`·`s1v_roles_current_reuse.txt`, V1 §2.1 엔진 이름 사용처(integ-it12). Q-CA1 spec 보유는 `git grep classab_centering`(정리자) |
| ② | graph 단일 정본(writer 하나·새 cache 0) | 실측: V11 §2(b)(상자 writer·소비자·사본 칸 엔진 전수 -- `search_domain.py`·`iv_context.py:94`·`start_values.py:180`·`iv_area.py:85`·`_helpers_area.py:24`), V10 §6(`theta_schema.py:66`, `current_basis.py:44`·`:130-133`, `spec_theta_bounds.py`, 소비자 4곳 grep), V9 §6(`block_lengths.py:17`, `block_widths.py:48`). 계획 문언상 새 필드·cache·사본 0(Q-CB1 판별 = 기존 `graph.dc_current_basis` READS, Q-KV1 R13 = 기존 계획 필드, Q-ZG1 f_HP·τ 칸 하나 writer 하나·출력 전용). DI §5 |
| ③ | 원칙 점검(물리 결정자·조건 n/13·n/9) | 실측: §1 각 표 '물리 결정자'·'실측' 칸(Q-W1 5/9, Q-ZG1 1/13, Q-CA1 1/13, Q-KV1 2/13, Q-CB1 13/13). V1~V10 각 '원칙 점검표'. Q-CF1은 n/9 해당 없음(이름 범위, 값 변화 0) |
| ④ | G-10·블록 안 재계산 | agent 인용: Q-W1 '실현 입력에 닿는 블록만 재계산, 나머지 graph reuse, FD 열 0'(V4 m4-4 → V5 해소, GB 304), DI §5 '블록 안 재계산' 행(G-10 계수 정의 = design 실현 평가 절). 실행 계측은 **해당 없음**: 이 판은 계획 문언 개정이고 엔진 코드 변경이 0이라 계측 대상 실행이 없다 |
| ⑤ | 소비자(만들면 배선) | 실측: V11 §2(b)(빠졌던 소비자 `iv_area.py:85` → 재배선 목록 정정, DR-1 완료 (10) toy = m11-2), OrderHints 미배선(`stage_b.py:152`) → (A) 삭제·재배선, 참조 9파일(V9·V10 grep). Q-CB1 결합 C 갈래 소비자 0 위험 → (Q) DR-1 이관(V10 MJ10-2). Q-ZG1 f_HP·τ 칸 = 출력 전용 선언. Q-CA1 (나) 소비자 0 ⚠. Q-CF1 3a 선병합 시 생산자 0 → 'IT-2c 예약' 표기(V1 m6) |
| ⑥ | 구조·파일 분할 | 실측(파일 범위): TB-1 OrderHints 삭제·재작성 9파일(V10 엔진 grep), DR-1·IT-1·TB-1 `writer_plan.py` 겹침(V9). 파일 분할(tests/structure A~I)은 **해당 없음**: 코드 변경 0, card 착수 때 점검 |
| ⑦ | 회로 이름 0 | 실측: V1 §1.1(DR-1 규칙 구조 조건만), V9 §2(c)(Q-CB1 구조 판별 13/13 일반, 회로 이름 0), V9 §6('이름' tie-break는 결정적 동률 처리로 허용), V5 §7(규칙 문언 0, 소자 이름은 실측 인용에만) |
| ⑧ | 실현 가능성(필드·단위·경로) | 실측: V11 §2(a)·(d)(빈 항 행이 필드에 실림 `current_basis.py:141`, 순환 0·fail-open 창 0), V10 §2(a)(`dead`는 지역 변수 → 기존 필드 `graph.dc_current_basis`로 정정, 층 순서 `kernel_context.py:81-91`), V9 §2(a)(R13 입력 S0 수준, 순환 0), V8 `s1v_grep.txt`·`layer_def.txt`(S1v가 쓰기 계획 앞), V1 §2.1(cfg 이름 사용처) |
| ⑨ | 물리·회로이론 검증 | 실측: ER(약반전 채널식·bulk 누설 VDS +0.246 V·bulk = source 0), FD(S2 이득·S3 SR·S4 doublet 식 검증·S6 정류), CR(c1~c5 α·SR 경계·처짐 분리·cgg), CB(고리 KVL·H0·I_Q), V5 `wb1_toy.txt`(ln(1+r) LUT 검산), V9 `fhp_check.txt`(f_HP 2/2). SPICE 값은 결정자 크기·경계 기록으로만 인용 |

### (iii) 원래 취지와 다름 전체 목록(본문 ↔ Status 1:1)

이 판(`07964dfe..74e62d53`)에서 새로 생긴 표지만 적는다. 이전 판 표지(DR-1 새 card O-173 BL-DR1 1231·2344, X-LA11 O-166 1942 등)는 그대로라 제외했다.

| # | 항목 | 바뀌는 결정·문언 | 본문 표지 행(GB) | Status(GB 11) | 이 문서 행 |
|---|---|---|---|---|---|
| 1 | O-174 | O-173 Q-4(erfc 영역 선언 + 규칙) → 구조 규칙 하나 | 2348 | 있음('O-174(O-173 Q-4 대체 -- 사용자 결정됨)') | 0.1 (1)(a) -- 결정됨, 질문 아님 |
| 2 | Q-W1 후보 | O-173 C1 재풀이 자리, Q-P8 적용 범위, E-0 범위 | 304, 1161, 1315 | 있음 | Q-W1 |
| 3 | Q-W1 후보 | DEC-23 성분 (3) 흡수(O-46·O-118·O-119) | 223, 1161 | 있음 | Q-W1 |
| 4 | Q-W1 후보 | X-LA11 근거 교체·IT-2 '선후와 무관' 정정(IT-2 → WB-1) | 1161, 1214, 1596 | 있음 | Q-W1 |
| 5 | Q-ZG1 | f_low 칸·존재 조건 행·SF-1 선행 철회 | 1163, 2348, 2350, 2352 | 있음(Q-ZG1 항목 괄호 'f_low 철회 -- 원래 취지와 다름'. 끝 요약 목록에는 없음) | Q-ZG1 |
| 6 | Q-CA1 | U-35 `user_spec` 제약 삭제(채택 시) | 1164 | 있음 | Q-CA1 |
| 7 | Q-KV1 (다) | DEC-95 (3) ①·② 개정 | 294, 1165 | 있음 | Q-KV1 |
| 8 | Q-KV1 (다) | TB-1 범위·card 성격 확장, DEC-104 (3)(a) 층 위치 | 1165, 2209 | 있음 | Q-KV1 |
| 9 | Q-KV1 (A) | O-144 J3·O-146 K2·O-149 병합 규칙 재검토 | 2209, 1165 | 있음('O-149 병합 규칙 재검토') | Q-KV1 |
| 10 | Q-CB1 | '10번'·N13 재질문, DEC-105 (10)(a) 문언 | 304, 1166, 2348 | 있음 | Q-CB1 |
| 11 | Q-CB1 | 상자 적용 자리 로더 → S0 블록(DEC-105 (10)·SF-1 범위 9) | 1166, 2195 | 있음 | Q-CB1 |
| 12 | Q-CB1 | SF-1 → DR-1 순서(새 병합 순서 규칙 +1) | **명시 표지 없음**: 1166 (Q)·1217·1231·2195·2352에 순서 문언은 있으나 '원래 취지와 다름' 표지가 그 순서를 가리키지 않는다(2195 표지 괄호 = DEC-105 (10)·적용 자리) | 있음('SF-1 → DR-1 순서') | Q-CB1 |
| 참고 | Q-KV1 대안 (라) | O-127·O-128 θ 기저 원칙 변경 | 1165(대안 칸 표지) | 없음(비권고 대안이라 해당 없음) | Q-KV1 대안 |
| 참고 | Q-ZG1 대안 (라)·(마) | 사용자 탐색안 비권고 | 1163 | 없음(표지 대상 아님 -- 결정 문언 변경 아님) | Q-ZG1 대안 |

### (iv) 권고 실측 출처 목록

- Q-W1: E`handcalc_principle_audit/p8_exact_slice.summary.json`·`.out.json`(r 65점·5/9), V5 `plan_v6385_validation5/wb1_toy.txt`(servo ΔV_id LUT 검산), V1 `p8_bin/wsweep3.out.jsonl`(조각 끊김 0.54~1.74배 -- GB 304 인용), V3 `servo.txt`(문언 대조), V4 m4-4(비용 유도값)
- Q-CF1: V1 §2.1(integ-it12 `41a1278b` 이름 사용처), `design_simplify_validation2.md` §5 (가)
- Q-ZG1: ER `erfc_region/net_audit.txt`·`results.txt`·`corner_table.txt`, FD `flow_derivation/s2_op_ac.txt`·`s3_tran.txt`·`s4_doublet_model.txt`·`s5_corpus.txt`·`s6_pump.txt`, `plan_v6385_v3/zg1_alt.txt`·`zg1_L.txt`, V1 `dr1_net_audit.txt`, V2 `zg1_wmin.txt`, V3 `zg1_w.txt`·`zg1_w_ngspice.txt`, V4 `zg1_grid.txt`·`zg1_total.txt`, V5 `zg1_delta.txt`, V8 `zg1_w_ratio.txt`, V9 `fhp_check.txt`
- Q-CA1: CB §3 R-A, `classab_battery/design_out.jsonl`·`rep_point.py`, `SPEC_CONTRACT.md:233`
- Q-KV1: CB `classab_battery/s1_cycles.out.txt`·`writer_plan.out.txt`·`design_out.jsonl`·`all_out.jsonl`·`scan13.out.txt`·`r2r_cycles.out.txt`, V8 `s1v_m9a.txt`·`orderhints_*.txt`·`layer_def.txt`, V9 `loop_pick.txt`·`writer_plan_grep.txt`·`s1v_roles_current_reuse.txt`·`topo_current_reuse_loops.txt`, V10 §2(b)
- Q-CB1: V11 §2(a)~(d)(엔진 상자 자리 전수), CR `cbox_rereview/c0_corpus.txt`·`c1_sweep.txt`·`c2_handcalc.txt`·`c3_droop.txt`·`c4_fit.txt`·`c5_sr2080.txt`, FD `s6_pump.txt`, V10 §2(a)(`current_basis.py:130-133`, `kernel_context.py:81-91`, 소비자 4곳)
- Q-CB2: CR §1·§3(STEP2 N7 하한 고착 사례), V9 m9-7
- design 영향: DI §1~§5

### (v) 권고 확인표

| 확인 | 결과 |
|---|---|
| 원칙 전수 자기 점검(graph 규칙 1~7·만들면 배선·상수 발명·회로 이름·DC/AC·O-153·O-169·O-165 (a)·fail-closed) | 각 권고의 대안·⚠ 칸에 반영했다. 새 상수를 제안하는 권고는 0이다((라)·(마) R 선언, (다) 공통 하한 상향은 상수 발명 ⚠로 비권고). 원칙 경고 ⚠ 셋: Q-W1 E-0 범위 축소, Q-CB1 보상 C 관례 잔존, Q-CB1 정류 표류 상충 |
| '승인 결정이므로'를 근거로 쓴 칸 | 0. '10번'·N13·U-35·O-149는 재질문·재검토 대상으로만 적었다 |
| SPICE 수치 일치를 판정 근거로 쓴 칸 | 0. SR 경계·f_HP·I_Q 오차는 결정자 크기·경계·오차 기록으로만 썼다 |
| 판정 '틀림' 권고 | 0. 대안 칸의 Q-KV1 (가)는 'F이면 모순'(틀림), Q-ZG1 'f_HP ≪ f_low'는 틀림으로 철회 |
| 판정 '불확실' | Q-CB2(열린 질문) |
| 판정 '조건부' | Q-W1(착수 실측), Q-ZG1(O-122·U-112 유지), Q-KV1(E-0·I_Q 실측), Q-CB1(하한 값 oracle 경계 + 승인) |
| 사이 결정·실측으로 갱신한 권고 | Q-ZG1: (라) W_min(V2) → (마)+(바)(V3) → (δ) 격자 선택(V4) → f_low 철회 후 (나)(FD, 일곱째 커밋) → (i) 기록 유지(V9). Q-KV1: 기본안 → (가)(V7) → (다)+(A)(V8·CB 손 판정). Q-CB1: 판별 입력 = '0 전류 집합 필드' → 기존 `graph.dc_current_basis`(V10), 결합 C 갈래 card (P) → (Q)(V10), 상자 writer 'S0 θ 상자 블록' → 기존 `search_domain` 자리 + 선언/적용 상자 분리(V11). Q-W1: 순서 고정 해제 → (ii)(V3·V4) |
| 문서 간 불일치(정리자 발견) | (1) CR 결론 4는 'θ 커패시터 15개'라고 적었지만 내역 합(library 9 + heldout 3)과 V9 재확인은 12다. 이 문서는 12를 쓴다. (2) Status의 'SF-1 → DR-1 순서' 원래 취지와 다름에 대응하는 본문 명시 표지가 없다(§2 (iii) #12). (3) DI는 열째 커밋 기준이라 Q-KV1 권고 (다)와 Q-CB1을 반영하지 않았다(§1 해당 칸에 표시) |
| 상정 전 남은 일 | V12(`74e62d53`) 독립 재확인 Major 0. (2)는 `74e62d53`에서도 그대로다(정리자 diff 확인). V12 또는 다음 커밋에서 처리할지 오케스트레이터가 판단한다 |

---

## 3. 1:1 대조표 -- Status 열린 결정·N5.3 행·'원래 취지와 다름' 표지 ↔ 이 문서

### 3.1 Status 열린 결정(GB 11) ↔ 이 문서

| Status 항목 | 이 문서 행 | 비고 |
|---|---|---|
| Q-W1(탐색 대 실현 평가, 원래 취지와 다름 후보 7항) | §1 Q-W1 | 1:1 |
| Q-CF1(안 A) | §1 Q-CF1 | 1:1 |
| Q-CA1(삭제 권고, 사용자 결정 대기) | §1 Q-CA1 | 1:1 |
| Q-CB1(역할별 분리, 적용 자리 S0 블록, SF-1 → DR-1) | §1 Q-CB1 | 1:1 |
| Q-CB2(열린 질문) | §1 Q-CB2 | 1:1(기록만) |
| Q-KV1((다) + (A), TB-1 design 전·E-0·I_Q 뒤) | §1 Q-KV1 | 1:1 |
| Q-ZG1((나) W_min·L_min, f_low 철회, (i) 유지) | §1 Q-ZG1 | 1:1 |
| Q-T0·Q-T3(WB-1 착수 실측 뒤) | §0.2 행 'Q-T0·Q-T3' | 이 판 질문 아님(이월, O-173 보류) |
| Q-C1(사용자 작성 몫) | 해당 없음 -- 이월, 사용자 connectivity 작성 대기(v6.38.4 상정 C11) | 이 판 변경 0 |
| Q-1(LOD 보류 -- 재개 조건) | 해당 없음 -- O-173 결정(보류) | 이 판 변경 0 |
| Q-2(머리 기하 ratify) | 해당 없음 -- O-173 결정(SF-1 범위 9 design에서 ratify) | 이 판 변경 0 |

### 3.2 N5.3 행(GB 1156~1167) ↔ 이 문서

| N5.3 행 | 이 문서 행 |
|---|---|
| 1156 Q-1 | §3.1(이월) |
| 1157 Q-2 | §3.1(이월) |
| 1158 Q-C1 | §3.1(이월) |
| 1159 Q-T0 | §0.2 |
| 1160 Q-T3 | §0.2 |
| 1161 Q-W1 | §1 Q-W1 |
| 1162 Q-CF1 | §1 Q-CF1 |
| 1163 Q-ZG1 | §1 Q-ZG1 |
| 1164 Q-CA1 | §1 Q-CA1 |
| 1165 Q-KV1 | §1 Q-KV1 |
| 1166 Q-CB1 | §1 Q-CB1 |
| 1167 Q-CB2 | §1 Q-CB2 |

N5.3 12행 ↔ 이 문서 12자리. 빠진 것 0.

### 3.3 Status '원래 취지와 다름' 요약 목록 ↔ 이 문서

| Status 표지 | §2 (iii) # | 이 문서 행 |
|---|---|---|
| O-174(O-173 Q-4 대체 -- 결정됨) | 1 | 0.1 (1)(a) |
| Q-W1 후보 | 2·3·4 | Q-W1 |
| Q-KV1 (다)(DEC-95 (3) ①·②·TB-1 범위·DEC-104 (3)(a)·O-149) | 7·8·9 | Q-KV1 |
| Q-CA1(U-35 `user_spec` 삭제) | 6 | Q-CA1 |
| Q-CB1('10번'·N13·DEC-105 (10)(a)·적용 자리 로더 → S0 블록·SF-1 → DR-1 순서) | 10·11·12 | Q-CB1 |
| (Q-ZG1 항목 괄호) f_low 철회 | 5 | Q-ZG1 |

### 3.4 본문 새 표지 ↔ Status(역방향)

정리자 행 diff 결과(`74e62d53`은 `adb3686a` 대비 표지 수 변화 0), 변경 행 51개에서 새 '원래 취지와 다름' 표지가 들어간 자리는 GB 11·223·294·304(2)·1161(2)·1163·1164·1165(3)·1166(2)·1214·1315·1596·2195·2209·2348(3)·2350·2352다. 모두 §2 (iii) #1~12 또는 '참고' 행에 귀속된다. Status에 없는 본문 표지는 Q-KV1 대안 (라) 하나이고, 비권고 대안이라 해당 없음이다.

### 3.5 대조 결과

- Status 열린 결정 12항 ↔ 이 문서: 빠진 것 0(질문 6 + 열린 질문 1 = §1, 이월 5 = §0.2·§3.1).
- N5.3 12행 ↔ 이 문서: 빠진 것 0.
- '원래 취지와 다름': Status → 본문 방향으로 **1건이 부분 대응**이다. Q-CB1 'SF-1 → DR-1 순서'는 Status에만 표지가 있고, 본문(1166 (Q)·1217·1231·2195·2352)에는 순서 문언만 있다. 본문 → Status 방향은 빠진 것 0이다.
- 권고: 1166 (Q) 또는 2352 '새 병합 순서 규칙 하나'에 '**원래 취지와 다름**(새 병합 순서 규칙 -- O-165 (a))'을 붙여 1:1을 닫는다(문언 1곳, 실측 불요). V12 결과와 함께 오케스트레이터가 판단한다.
