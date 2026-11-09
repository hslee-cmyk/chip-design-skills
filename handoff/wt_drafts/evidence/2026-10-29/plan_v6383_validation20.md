# 계획 v6.38.3 O-172 정정 커밋 독립 검증 20

- 대상: `wt/plan-v6383` `15a16679`(부모 `c8d96918` = O-170 승인 커밋). 변경 파일 2개: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(줄 11·291·304·388~391·636·1250·2223·2230·2415·2551·2557), `gain-budget-gmid-sizing.history.md`(줄 1514 추가).
- 검증자: 작성자·이전 검증자 아님. 읽기만 했다(`git -C` 읽기 명령만 썼고 reset·checkout·stash는 쓰지 않았다). 작성자 보고는 증거로 쓰지 않았다.
- 근거로 쓴 것: `git diff -U0` 문자 단위 비교, 결정 `wt/_drafts/user_decisions.md` O-171·O-172(1152·1153행), 점검 `wt/_drafts/evidence/2026-10-29/decision_physics_audit.md`와 `physics_audit/*.out.jsonl`, 엔진·topology·원문은 `wt/integ-it12` `d759838a`(읽기만), Crossref API(DOI 확인).

## 0. 결론

| 심각도 | 수 | 항목 |
|---|---|---|
| 높음 | 0 | -- |
| 중간 | 1 | V20-M1 DEC-92 (3) '한계'의 출처 오기(DOI가 다른 논문을 가리키고, 원문 [5]도 Monticelli가 아님) |
| 낮음 | 7 | V20-L1~L7 |

**판정: 병합 불가.** V20-M1 하나를 고치면 병합할 수 있다. 낮음 항목은 같은 커밋에서 함께 고치기를 권고한다.

## 1. 결함

### V20-M1 (중간) -- plan:291 class-AB 한계 문장의 출처 오기

현재 문언은 "Monticelli, IEEE JSSC 21(6), 1986, doi:10.1109/JSSC.1986.1052648, 원문 Xie·Chen [5]"이다.

- **DOI가 다른 논문이다.** Crossref `10.1109/JSSC.1986.1052648`의 실제 논문은 K.R. Lakshmikumar, R.A. Hadaway, M.A. Copeland, "Characterisation and modeling of mismatch in MOS transistors for precision analog design", JSSC 21(6) pp.1057-1066이다. Monticelli의 "A quad CMOS single-supply op amp with rail-to-rail output swing"(JSSC 21(6) pp.1026-1034)는 `10.1109/JSSC.1986.1052645`다(Crossref 조회).
- **원문 [5]도 Monticelli가 아니다.** Xie·Chen 원문의 [5]는 N. Sun, "OTAs with single ended outputs and output stage examples", 2019다(`assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/paper.md:535-536`). 원문이 class-AB 출력단 근거로 인용한 문헌은 [1] R. Hogervorst et al., JSSC 29(12) pp.1505-1513, 1994다(paper.md:61-62·519-522). 원문은 Monticelli를 인용하지 않는다.
- **원칙 위반**: 출처를 발명하지 말 것, 원문 근거에는 정확한 링크와 쪽 번호를 붙일 것, O-171(회로이론 판정 근거). 같은 오기가 점검 문서 A10 행에도 있다. 문서 그대로 옮기다 생긴 오류다.
- **수정안**: DOI를 `10.1109/JSSC.1986.1052645`로 고친다. '원문 Xie·Chen [5]'는 지운다. 대신 '원문 Xie·Chen §II.B p.3 Fig.3(Class AB 2단, 원문 인용 [1] Hogervorst 1994)'로 적는다. 로컬 PDF가 없으므로 '로컬 PDF 없음' 표기는 유지한다. 점검 문서 A10에도 정정 표지를 붙이도록 오케스트레이터에게 알린다.

물리 내용 자체는 맞다(§2 (a)).

### V20-L1 (낮음) -- plan:291 "Σgm이 최대 약 2배 과소"

- 실효 Gm = gm16 + gm15·k이고, k = dv(Vg15)/dv(Vop1) ≈ gm9b/gm9a다.
- M15와 M16은 같은 정지 전류를 나눠 쓴다. 그래서 gm15/gm16 = (gm/ID)15/(gm/ID)16이고, 이 비는 θ가 정한다.
- 따라서 '최대 2배'라는 상한은 물리적으로 보장되지 않는다. 2배는 gm/ID가 같고 k ≈ 1일 때의 값일 뿐이다.
- 수정안: 'gm15 ≈ gm16·k ≈ 1이면 약 2배'.

### V20-L2 (낮음) -- plan:2551 nmcnr "창 위 끝 여유 약 0.1 V"

- 같은 문장에 인용한 실측값(IDu 1e-9 A/µm에서 위 끝 0.944 V)으로 보면, 측정 범위 안의 최대 여유는 0.944 − 0.9 = **0.044 V**다.
- 여유 0.1 V가 되려면 1 nA/µm보다 낮은 밀도가 필요한데, 그 밀도는 재지 않았다.
- 값의 출처는 `lut_checks.out.jsonl`의 `cr_window_density` 케이스다(current_reuse용 계산에서 꼬리 VSD 0.141 V와 VSG_p를 nmcnr에 같은 식으로 적용). 출처 표기가 'LUT 실측'뿐이다.
- O-172 사용자 기록도 같은 '0.1 V'를 쓴다. 점검 문서의 수치를 그대로 옮긴 것이다.
- 수정안: '여유 ≤ 약 0.04 V(1 nA/µm, `cr_window_density` 식 재사용)'로 고치고, 사용자 기록과 다른 점을 보고에 적는다.

### V20-L3 (낮음) -- plan:2551 current_reuse "창 중심 0.72~0.80 V"와 창 식

- **중심 범위가 좁게 적혔다.** LUT 실측 중심은 L 0.5 µm에서 0.714~0.734 V, L 1 µm에서 0.681~0.704 V다(`cr_window_density`). SPICE는 0.765~0.795 V다. 실측 범위는 0.68~0.80 V다. 다만 결론(중심 < 0.9 V)은 오히려 강해진다.
- **창 식이 상위집합이다.** '입력쌍 포화 창 = [V(꼬리 n) + VGS_n, V(꼬리 p) − VSG_p]'는 꼬리 조건만 반영한 창이다.
  - 입력 소자 M4a 자신의 VDS 조건이 빠졌다. M4a의 드레인 N3a4a는 캐스코드 M3a가 고정한다(topology).
  - 원문 p.3 §II.B도 "when the input common-mode voltage is high, the bottom devices (M3, M4 and M5) are pushed to linear region"이라고 적었다. 실제 창은 더 좁다.
- 수정안: '꼬리 조건 창(상위집합 -- 입력 소자 VDS 조건이 더 좁힘, 원문 p.3 §II.B)'으로 고치고, 중심을 '0.68~0.80 V'로 고친다. 결정(engine)은 그대로 성립한다.

### V20-L4 (낮음) -- plan:2551 "`icm_margin_v ≥ 0`이 판정"(engine 꼴)

- **정의는 된다.** N3.8 'ICMR 좌표'(plan:654)는 V_cm0 = 봉인점 입력 평균이다. 그러나 봉인 7(포화)이 이미 V_cm0를 창 안에 두므로 이 제약은 거의 항진이다(tol 차만 남는다).
- **as-built 처리는 '판정'과 다르다.**
  - `headroom_bound.py:20·170`: 입력 DC가 None이면 보고만 한다.
  - oracle `oracle_swing.py:251`과 `oracle_compare.py:207`: `input_dc_pending`이면 icm_margin을 내지 않는다.
  - `dc_inputs.py`는 `engine`과 `pending`을 똑같이 None으로 처리한다(plan:1582 (iv)에도 적힘).
- **spec 기록과도 어긋난다.** current_reuse spec의 `icm_margin_v` 기록은 "입력 DC(SP-2) 선언 시 활성"이다.
- 결과: 실제 보호 장치는 봉인 7과 DEC-106 (5)다. card CPG-1의 SPICE 판정에서는 current_reuse icm_margin이 빠질 수 있다.
- 수정안: 문언을 '보호 = 봉인 7(포화) + DEC-106 (5) 측정 구성 창; `icm_margin_v ≥ 0`은 engine 꼴에서 V_cm0 기준으로 정의되나 봉인 7과 겹침'으로 고친다. SF-1 data 커밋에 icm_margin 기록 문구 갱신과, 엔진·oracle의 engine 대 pending 처리 확인을 넣는다.

### V20-L5 (낮음) -- 낮음 항목 수 "4건"과 실제 나열 5개

- plan:11(Status), plan:390(N2.1 O-172), history:1514는 '낮음 4건'이라고 적고 다섯 항목을 나열한다: S 정의, U-134, R1 = R2, counted_rails, U2 folded.
- 점검 문서의 낮음 행도 A10·A11·A7·A18·A21 다섯 개다. 사용자 기록 O-172의 '4건'을 그대로 옮긴 것이다.
- 수정안: '낮음 5항목(사용자 기록 표기 4건)'.

### V20-L6 (낮음) -- plan:304 R1 = R2 확인 항목의 card 두 곳

- 확인 card가 'card LA-1 범위 15 toy(CMFB 평형) 또는 SF-1'로 두 곳이다.
- LA-1 범위 15 (f)와 완료 조건 10 (f)(plan:1926 부근), SF-1 범위 어디에도 이 항목이 없다. 이대로면 아무 card도 하지 않을 수 있다.
- 수정안: DEC-105 (7)의 구현이 card LA-1 범위 15이므로 LA-1 범위 15 (f)로 하나만 정하고, 완료 조건 10 (f)에 'R1·R2 묶음 확인'을 넣는다.

### V20-L7 (낮음) -- plan:2223 A18 "측정 부하로 흐르는 전류를 뺄지"

- DUT 전력은 Σ V_k·I_k − P_load다. 여기서 P_RL = (V_out − V_agnd)²/RL이다.
- 레일 전류에서 부하 전류를 빼고 V를 곱하면(예 VDD·(I_vdd − I_L)) 이 값과 일반적으로 같지 않다.
- '전류'라는 말이 정의 방향을 미리 정해 버린다.
- 수정안: '측정 부하 전력(또는 전류)을 뺄지'.

### 경미(결함 수에 넣지 않음)

- plan:391 N2.1 O-172 행의 '바꾼 자리' 열에 J-E(plan:2415)가 빠졌다.
- history:1514의 옛 문언 인용 «offset-strategy:380, 새 상수 없음) ¦»는 표 안이라 `|`를 `¦`로 바꿔 적었다. 그래서 부모 원문과 글자로 일치하지 않는다. 나머지 인용 11개는 부모 `c8d96918`에 모두 있고, 현재 판에서는 없어진 것을 확인했다(대상 아닌 'library 9회로…' 1개 제외).

## 2. 확인 결과(통과)

### (1) O-172 반영의 일관성

- current_reuse `input_dc` = engine은 다음 자리에서 모두 같다: U-128 상태·본문(2551), SF-1 착수 조건(1250), SF-1 data 커밋 값(2230), J-E 인용 행(2415), N2.1 O-170 표지(388), O-172 행(390), Status(11).
- 'current_reuse ... 0.9 V' 문언이 남은 곳은 표지가 붙은 N2.1 O-170 행(388)과 history 인용뿐이다(plan 전체 grep).
- 하위 계획 5개와 design 문서에는 current_reuse `input_dc` 값 인용이 0건이다.
- nmcnr agnd 조건부 사실은 2551에 있고, 2230·2415에는 '(조건부 -- U-128)' 표지가 있다.
- 낮음 (a)~(e)는 291·636 / 2557 / 304 / 2223 / 2551에 모두 반영됐다. DEC-106 적용 대상도 맞다: current_reuse ports `Vip`·`Vim`의 role이 `differential_input_p/n`이다(topology).

### (2) 물리·회로이론 점검(O-171)

- **(c) Voc 식 -- 맞음.** topology에서 R1은 Vom–Voc, R2는 Voc–Vop 사이에 있다. Voc에 닿는 MOS는 M37a gate뿐이므로 DC 전류가 0이다. 분압식은 Voc = (R2·Vom + R1·Vop)/(R1 + R2)이고, R1 = R2일 때만 중점이며, 그 밖에는 차동 신호가 CM 감지로 샌다. 모두 맞다. (참고: 출력 DC가 대칭이면 DC 평형점에서는 R1 ≠ R2여도 Voc가 출력 CM과 같다. 문언은 일반 (Vop, Vom)에 대한 서술이라 틀리지 않다.)
- **(d) 중간 rail 전력 -- 맞음(L7 문구 제외).** 'Tellegen에 따라 공급 전력 = Σ V_k·I_k(같은 기준)'은 맞다. agnd에 저항 부하가 걸린 회로는 nmcnr 하나(RL 25 kΩ)다. pushpull·sf_pushpull은 agnd에 CL·Cc만 걸려 DC 전류가 없다(topology `passive_elements`). 'library nmcnr 1'은 맞다. O-73 분리 인용도 맞다.
- **(a) class-AB 부유 전류원 -- 맞음(M1·L1 제외).** 연결을 확인했다: M15 gate = Vg15, M9a(pmos, s = Vg15, d = Vop1), M9b(nmos, s = Vop1, d = Vg15), M8(pmos, d = Vg15), M16 gate = Vop1. 반대쪽 M25·M26도 같은 꼴이다. Vg15 노드 KCL은 vg15·(gm9a + gds9a + gds9b + 1/ro8) = vop1·(gm9b + gds9a + gds9b)이고, 문언의 ≈ gm9b/gm9a와 같다. 출발 R = 1/gm16 > 1/Gm_eff이면 영점은 좌반면이다. 맞다.
- **sky130 수치는 점검 실측과 맞는다(L2·L3 제외).** pfet |Vth| 0.982~1.036 V(L 0.5~2 µm), nfet 0.55~0.63 V, nmcnr IDu 1e-9 → 0.944 V, 1e-8 → 0.833 V, gm/ID ≳ 25(1e-9에서 27.3), 원문 ICMR [576.5, 900.1] mV(paper.md:88), 0.18 µm(paper.md:33). nmcnr 입력 M102·M103은 pmos이고 꼬리 M101 source는 vdd다. 원문 p.3 §II.B의 'unsymmetrical input common mode range'도 engine 결정을 뒷받침한다.
- **U-134 -- 맞음.** `area.py:1-30`의 면적 = Σ W·L + 수동소자 값 × 단위 면적 + 머리 면적이다. sky130 decl `resistor_types` poly는 sheet·min_w·head를 갖는다. `area_search_m2` 선언은 9/9 spec이다. R = R_sheet·L/W이므로 면적은 R에 비례한다. 맞다.
- **U2 folded -- 맞음.** 경계는 |V_os| ≲ |ΔV_out|/A_dc이고 A_dc 하한 선언이 없으면 측정 불능이다. 이 조건부 문언은 물리에 맞다.

### (3) 형식

- `git diff -U0` 오적용 0: 모든 hunk가 의도한 문장에 삽입·치환됐다.
- 표 열 수: 바뀐 표 행(291·304·388~391·1250·2415·2551·2557, history 1514)이 모두 머리행과 같다(5·4 열). 새 문언의 `|`는 모두 `\|`로 이스케이프돼 있다.
- blob CR: plan 0, history 0.
- Status와 history: '승인됨(O-170), O-172 정정 검증 대기'와 '(정정 커밋 …)(승인 커밋 …)' 순서가 맞다. history H1 행은 승인 커밋 행 바로 뒤에 있다.

## 3. 권고 처리 순서

1. V20-M1을 고친다(DOI·원문 인용). 점검 문서 A10에 정정 표지를 붙인다.
2. 같은 커밋에서 L1~L7을 반영한다. L4는 SF-1 data 커밋 범위에 한 줄을 추가하는 것으로 처리한다.
3. 바뀐 곳만 다시 검증한다.
