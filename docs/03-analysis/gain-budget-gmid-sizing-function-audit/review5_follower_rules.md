# 소스 팔로워 규칙 확장 검토 (계획 v5.9 대상)

- 검토 대상: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(이하 `plan`), library 신규 3회로
- 저장소 수정 없음. 측정 원자료(이 검토가 만든 것): `scratchpad/review5/probe_follower_structure.py` → `probe_follower_structure.result.md`
  (library 7회로 connectivity만 읽음: 순수 follower 후보, gate–source DC 사이클, 출력 포트 방향별 셀, LUT npz 축)
- 표기: **(J)** = 회로 해석이라 공동분석 대상(확정하지 않음). 논문 식은 test 쪽 독립 기준으로만 언급하고 엔진 상수로 제안하지 않는다.

## 0. 측정으로 확인한 사실 (규칙 제안의 근거)

| # | 사실 | 근거 |
|---|---|---|
| F1 | 순수 follower 후보(drain=레일, gate=신호 후보 넷)는 신규 3회로에만 있다: `two_stage_ota_sf` M8, `pushpull_follower_buffer` M1~M4, `sf_pushpull_output_opamp` M18/M19/M21/M22. 기존 4회로는 0 | probe result §각 회로 |
| F2 | gate–source 엣지만으로 닫힌 비자명 DC 사이클: 파일럿 5개(레일 경유 4개 = {M9a,M15,M11a,M11b}, {M16,M14b,M14a,M9b}, {M18a,M25,M20a,M20b}, {M26,M24b,M23a,M18b} / 레일 비경유 1개 = {M1a,M1b,M4a,M4b}, 노드 Vip·Vim 두 포트 경유), `pushpull_follower_buffer` 1개 {M1,M2,M3,M4}(노드 vin,A,vout,B), `sf_pushpull_output_opamp` 1개 {M18,M19,M21,M22}(Y,N17,vout,N20). folded·nmcnr·two_stage·two_stage_sf는 0 | probe result |
| F3 | DEC-15의 파일럿 적용 소자 M11a/M11b/M20a/M20b(plan:193)가 F2 레일 경유 사이클 멤버로 나온다 -- follower push-pull 루프와 같은 탐지 규칙에 걸린다(해석 동일성은 J3) | plan:193, probe |
| F4 | 출력 포트 방향별 셀: `two_stage_ota_sf` vout = M8(source, gate OUT 신호) + M9(drain, gate `bias` gate 전용 넷) → 한 방향만 신호 셀. `pushpull_follower_buffer`·`sf_pushpull_output_opamp` vout = 두 방향 모두 신호 셀(source 단자). 파일럿 Vop/Vom = 두 방향 모두 신호 CS(drain 단자) | probe result |
| F5 | 추가 equal_vgs 평행 엣지: `sf_pushpull_output_opamp` M17~M6(gate N5, source vdd), M20~M14(gate N13, source vss) -- 버퍼 전류원이 앞 블록 소자와 VGS 공유(K2 후보) | probe, sf json:40-45,82-87,124-129,145-150 |
| F6 | 유일한 사이징 LUT `assets/sky130_nfet_pfet_lut_sample.npz`: 축 L 12점, VGS·VDS 0~1.8 V 49점, **VS 0~0.8 V 5점**, 열 ID·GM·GDS·CGG·CGD·SID_1F(**CGS·CGB 없음**). LUT 생성 체크리스트는 CGS·CGB를 probe한다(`references/lut-generation-checklist.md:37`) | probe result §LUT |
| F7 | 버퍼 출력 DC 기준: 두 push-pull 회로 supplies vdd 1.8/vss 0/agnd 0.9, 버퍼 입력 DC = agnd(pushpull json:84-91). nmos 벌크 기본 = 가장 낮은 레일(DEC-61, plan:238) → vout≈agnd이면 출력 nmos vsb≈0.9 V, 출력 pmos(벌크 vdd) vsb≈0.9 V로 F6 VS 축 상한 0.8 V를 넘을 가능성이 크다(vout DC는 레벨 시프트 차이만큼 agnd와 다를 수 있어 "가능성") | F6, F7 |

## 1. 커버리지 표

열: 현 규칙이 계산하는 것 / 빠진 것 / 틀리거나 모호하게 판정하는 것.

| # | 구조 사례 (회로: 소자) | 현 규칙이 계산 | 빠진 것 | 오판·모호 |
|---|---|---|---|---|
| C1 | 단일 NSF + 바이어스 sink (`two_stage_ota_sf`: M8 g=OUT s=vout d=vdd, M9 g=bias; json:60-73) | 셀 CD(plan:84,306), 버퍼 구간·극점 노드(plan:314), 국소 모델 이득 `gm/(gm+gmb+G)`(plan:89,444), gmb 유도(plan:445) | CS/CD 선택 기준 문장(plan:306은 "CS(출력 drain) 또는 CD(출력 source)"만). vout DC writer 티어 없음(W2 목록 plan:350에 CD source 없음) | 방향별 최대 전류 "조향 가능한 바이어스 전류원의 합"(plan:446, DEC-58 plan:233)이면 공급 방향(M8, 신호 셀)이 0 또는 미정으로 기록된다. 원문도 공급은 게이트 구동으로 정해지고 흡수만 IQ로 한정된다(L21:333,349) |
| C2 | PSF (`pushpull_follower_buffer` M3·M2, sf M18·M21) | C1과 같음, pmos vsb = abs(V(s)−V(b))(plan:238) | LUT 축 범위 밖 처리 규칙이 L에만 있다(LR3 plan:460) | 출력 pmos M2/M21 vsb가 VS 축 밖일 가능성(F6·F7) → 현재는 보간기 동작 미정(클램프/외삽) |
| C3 | 팔로워→팔로워 연쇄 (M3→A→M1, M4→B→M2; Y→M18→N17→M22) | 용어집: follower 사슬 묶음 = 버퍼 블록 하나, 중간 노드를 블록 노드 집합에(plan:90). 국소 모델이 곱을 단자 스탬프로 자동 계산(plan:444) | 묶음을 만드는 절차(어디서 시작·어디서 끝·다출력이면?) | 중간 노드 A는 M3 source + M5 drain(바이어스 전류 유입)이라 용어집 '입력 노드 구동 종류'(plan:85)의 전압 구동(follower 출력)과 전류 구동(drain 전류가 흘러드는 저임피던스 내부 노드)을 **동시에** 만족. 전류 구동으로 판정되면 M1(CD, 입력 A)은 규칙 5의 세 bullet(plan:312-314) 어디에도 안 맞는다 |
| C4 | 상보 push-pull 병렬 합류 + 정지전류 (vout: M1+M2, M22+M21) | 묶음 = 한 버퍼 블록(plan:90), `ID_source` 타입 `kvl_loop` 이름(plan:436), J12에 KVL 식 기재(plan:845) | `kvl_branch` 탐지 규칙·DOF 처리·W2 풀이 없음(S1 엣지 타입 이름만 plan:326). N3.7 입력 기준 규칙은 병렬 셀 입력이 "pass 셀·블록 내부 노드"로 이어질 때만 한 블록(plan:420) -- CD 경유 명시 없음. 바이어스로 제한되지 않는 출력단 전류·슬루는 J3·J12로 위임만(plan:439,446) | DEC-15(plan:193)는 파일럿 이름 목록, DEC-27(plan:205)은 VDS 하나를 포함한 루프의 **부등식**(`V_bat` 상한, 코드 sizing_recipe.py:1835-1883)이다. follower 루프(F2)는 VGS만의 **등식**이라 DEC-27 경로로는 표현 안 됨 |
| C5 | 레벨 시프트 (A = vin+VSG3, vout = A−VGS1 / vout = OUT−VGS8) | 봉인 항목 2 VGS 정합이 사후 검사(plan:389) | 헤드룸 창(W4)·다음 단 입력 DC와의 관계 규칙(J10은 "헤드룸에 영향"만 plan:843), 스윙 제약 슬롯(I-A6 plan:747) | CD source 노드가 W4 자유 노드로 들어가면 GB6 중층이 값을 배정하고 봉인 2가 거부하는 반복이 생긴다(티어 미정) |
| C6 | 바이어스 전류원 팔로워 (M5 g=VPB1, M6 g=VNB1, M9 g=bias) | gate 전용 넷 = 교류접지(plan:301), load(plan:308) → gds 스탬프 | 전류원 포화 하한(VDsat 유도 DF-25 plan:736)이 스윙 하한에 필요. 버퍼 바이어스 전류(I5/I6/I9)를 정하는 층: 버퍼 블록은 "할당하지 않는다"(plan:446)인데 내층 DP 결정 벡터는 블록 셀(plan:427) → 버퍼 셀 결정 층 공백 | -- |
| C7 | 신호가 실린 전류원 게이트 (M17 g=N5, M20 g=N13; 원문 "bias currents through M18 and M19 vary with the signal" L26:166) | K8 측면 주입 + MT3(plan:415,420), 7b 대조 test (i)(ii)(plan:815) | (i) 경계 조건의 "DC 고정" 값 출처 없음(plan:815). K2(F5 equal_vgs M17~M6, M20~M14) 결합 처리 | (a) 주 신호 분기를 **먼저** 판정(plan:420 "두 조건에 모두 해당하면 (a)"). M17 경로 N5→N17→M22→vout도 "출력노드까지 신호 셀 사슬로 이어져 합류"를 만족하고, (b)의 "순방향 신호 경로 셀이 아님"은 정의가 없다. 0-1 BFS(plan:310)로 보면 N17 거리는 Y 경유 2, M17 경유는 N5 거리+1인데 N5 거리가 수동소자 R1a 엣지 비용(규칙 4에 미정의)에 따라 1 또는 2라 동률(최단 DAG에 포함 → (a))이 될 수 있다. 즉 U-25·DoD 7b(ii)의 "정지하지 않는다"가 정의에 따라 뒤집힐 수 있다 |
| C8 | body effect (모든 follower 벌크 = 레일; two_stage_ota_sf M8 bulk gnd json:5) | vsb 유도(DEC-61), gmb = ∂ID/∂VSB(plan:445), 봉인 6(plan:393) | CD source 노드의 vsb 순환(vsb가 V(s)에 종속) 명시. 현 MNA gmb 미반영(plan:445, 7a) | VS 축 0.8 V(F6) 밖 vsb에 대한 거부 규칙 없음 |
| C9 | CL 직접 구동 (two_stage_ota_sf vout–gnd 3 pF, 두 push-pull vout–agnd 1 pF) | C_k,total에 선언 부하(plan:439), MNA gain에 부하 포함(plan:446) | follower 극·영점은 입력–출력 사이 용량(Cgs)으로 생긴다(L21:410-420 "C1 ≈ CGS1"). MNA가 cgs를 g–s 사이에 스탬프하려면 CGS 열이 필요한데 LUT에 없다(F6) | CGG를 접지 용량으로 스탬프하면 영점이 사라지고 앞 노드 부하가 과대 |
| C10 | 입력이 고임피던스 gain 노드 (OUT: M6/M7 drain·Cc; Y: M10/M15 drain·Cc) | 앞 블록 출력노드 + K5 다음 stage 입력 Cgg(plan:412), 국소 모델 경계 "다음 CS 게이트 용량 등"(plan:444) | CD 입력 어드미턴스(cgd + cgb + cgs·(1−A_buf)) 계산 규칙 | "다음 CS 게이트 용량"을 CD에 그대로 쓰면 앞 노드 극점을 낮게 추정(K5·`parasitic_pm_deg` 쪽으로 번짐) |
| C11 | 출력 임피던스 스펙 (세 회로 모두 `rout_ohm <= 1000`, sf json:279-283, pushpull json:97-102, two_stage_sf json:130-134) | 블록 테브난 임피던스 기록(plan:446) | 출력 임피던스 metric·제약 경로 | plan:446 "출력 임피던스에는 별도 임계값을 두지 않는다 -- 부하 효과는 gain 제약이 판정" → 부하가 CL뿐이면 DC gain에 Rout이 안 보여 U-25 `rout_ohm` 제약을 판정할 경로가 없다(**충돌**) |

## 2. 확장 규칙 제안 (일반형)

소자 이름은 예시로만 쓴다. 각 규칙은 DEC-59 분기 속성(`계산 규칙 있음 / 기록만`)을 함께 적는다.

### SF-1 셀 판정 기준 (N3.2-3 보강)
gate가 신호를 받는 소자의 출력 단자는 그 뷰의 교류접지 집합에 **속하지 않는** 채널 단자다.
- drain이 교류접지 → **CD**(출력 source). source가 교류접지 → **CS**(출력 drain).
- 둘 다 교류접지가 아니면: source 노드가 다른 신호 셀의 입력 단자나 출력 포트에 닿으면 CD·CS 이중 출력으로 `review_needed`(`기록만`), 닿지 않으면 CS(source는 degeneration, plan:306과 같음).
- 측정 기대: CD = F1의 9소자, 기존 4회로 CD 0(무동작).

### SF-2 입력 노드 구동 종류 = 신호 진입 단자 (용어집 plan:85 대체)
노드의 구동 종류는 **신호가 들어오는 단자**로 정한다. 신호 셀의 source 단자(CD 출력)로 들어오면 전압 구동, 신호 셀의 drain 단자(CS·CG 출력)로 들어오면 전류 구동. 바이어스 셀(gate 교류접지)의 drain·source는 신호 진입이 아니라 load다.
- 두 종류가 같이 들어오는 노드: drain 쪽 셀이 SF-4의 측면 주입이면 전압 구동, 아니면 `review_needed`(`기록만`).
- 기존 판정 보존: 캐스코드 source 노드(입력 셀 drain 전류 유입)는 그대로 전류 구동. C3의 A·B·N17·N20은 전압 구동.

### SF-3 follower 묶음 → 버퍼 블록 (용어집 plan:90, N3.2-6 절차화)
1. 전압 구동 넷 u(입력 포트 또는 이득 블록 출력노드)에서 CD·pass 셀의 입력→출력 엣지만 따라 도달하는 노드 집합 R(u)를 모은다.
2. R(u)에서 더 이상 CD·pass 입력으로 쓰이지 않는 노드가 **하나**면(합류 노드 v) 버퍼 블록 = {입력 u, 노드 집합 R(u), 출력노드 v}(`계산 규칙 있음`). 둘 이상이면 다출력 버퍼로 `기록만`.
3. 경로 중 CS·CG 셀을 만나면 묶음이 끝나고 그 셀은 규칙 5로 새 이득 블록을 시작한다.
4. 버퍼 블록과 앞 이득 블록이 공유하는 것은 경계 넷 u 하나뿐이다(J3의 "노드 집합 겹침 금지" 논리와 같다, plan:836).
5. N3.7 입력 기준 규칙(plan:420)의 "pass 셀·블록 내부 노드를 거쳐 닿는 넷"을 "pass 셀·**같은 묶음의 CD 셀**·블록 내부 노드"로 넓힌다.
- 측정 기대(J12에서 ratify): pushpull {u=vin; A,B,vout; v=vout}, sf {u=Y; N17,N20,vout; v=vout}, two_stage_ota_sf {u=OUT; vout; v=vout}.

### SF-4 측면 주입(K8) 구조 기준 -- (a)와의 모호성 제거 (N3.7 plan:420 (b) 대체)
신호 셀 c(CS)의 drain 노드 k가 다음을 모두 만족하면 측면 주입이다:
1. k가 어떤 블록의 출력노드가 아닌 내부 노드다.
2. k가 같은 블록의 순방향 CD 셀 source로 이미 **전압 구동**된다(SF-2).
3. c의 신호 입력 넷이 k가 속한 블록 밖의 노드다.

주 신호 분기 (a)는 합류 노드가 **전류 구동**(두 신호 셀 drain 전류가 합산)이거나 블록 출력노드일 때만이다. "순방향 신호 경로" 도달성·BFS 비용에 의존하지 않는다.
- 측정 기대: M17(k=N17, M18 source로 전압 구동)·M20(k=N20) → K8. 파일럿 CMFB 뷰의 M7→Vx는 Vx에 다른 전압 구동 진입이 없어(M1a/M1b gate 교류접지) K8이 아니다.
- **(J)** 원문 "bias currents ... vary with the signal"(L26:166)을 이 기준으로 읽는 것이 맞는지 J12에서 확정한다.

### SF-5 버퍼 블록 속성 = 국소 모델 그대로, 경계 부하만 일반화 (N3.8 plan:444 보강)
- 이득(연쇄 곱, 상보 병렬 합)과 출력 테브난 임피던스는 블록 국소 모델의 단자별 gm·gmb·gds 스탬프가 자동으로 계산한다. **별도 분기 규칙을 두지 않는다**(plan:444와 일관). 전제는 두 가지다: gmb 스탬프(plan:445), 묶음 중간 노드 포함(SF-3).
- 경계 부하 일반화: "다음 블록 입력의 부하 어드미턴스(다음 CS 게이트 용량 등)"를 "**다음 블록 국소 모델에서 계산한 입력 넷 어드미턴스**"로 바꾼다. 게이트 용량은 cgd→drain 노드, cgs→source 노드, cgb→bulk 넷으로 스탬프하고, 입력 넷 전류/전압으로 앞 블록 경계 부하를 만든다. 저주파 gain에는 0이고 극점·K5·`parasitic_pm_deg`에만 들어간다.
- 필요 데이터: LUT CGS·CGB 열(F6 결손 → DF 신설, §5). 열이 생기기 전 대체 스탬프(CGG−CGD를 g–s에)는 근사로 기록하고, 해당 metric은 `verified_by`(SPICE, plan:452) 전까지 검증 대기로 표시한다.
- 검증: 강의 식(L26:76-78 연쇄, L21:519-523 병렬, L21:377 단일)은 **test 쪽 독립 기준으로만** 쓴다(엔진 코드에 넣지 않는다, 작성자≠검증자).

### SF-6 출력 임피던스 metric (plan:446 문장 수정, C11 충돌 해소)
- `output_impedance_ohm(port)` = 전체회로 MNA에서 모든 여기원을 교류접지로 두고 출력 포트에 단위 전류를 주입한 저주파 전압.
- 기본안 정의(원칙: 원문 식이 개루프 DC 양 `1/(gm21+gm22)`, L26:163): 개루프, DC.
- 제약은 spec에 선언(`rout_ohm`)이 있을 때만 판정하고, 엔진은 임계값을 만들지 않는다.
- 블록 테브난 값은 분해값이며, MNA 값과의 잔차를 기록한다(DEC-05와 대칭).

### SF-7 CD source 노드 = W2 순환 블록 (N3.4 plan:350 보강)
- 신호 CD 셀의 source 노드는 W2다: `V(s) = V(g) ∓ VGS(gm_id, L, vds=|V(d)−V(s)|, vsb=DEC-61(V(s)))`. vds·vsb가 V(s)에 종속하므로 순환 블록이며, 고정점 상한은 plan:399의 K_max를 따른다.
- 버퍼 블록 입력 넷의 DC는 앞 이득 블록 출력노드의 writer(W4 또는 W3)가 쓴다. 입력 포트면 spec의 입력 DC 선언이 쓴다(pushpull json:90).
- 두 CD 경로가 같은 합류 노드를 쓰는 경우(push-pull vout): 경로별 식이 둘이라 봉인 5 writer 유일(plan:392)에 걸린다. 따라서 합류 노드 전압과 SF-8 등식 하나를 **한 W2 블록**으로 함께 푼다(미지수 V(v) + 정지전류 쪽 종속 변수 하나, 등식 둘).

### SF-8 gate–source DC 사이클 = `kvl_branch` 일반 탐지 (DEC-15·DEC-27 통합)
**그래프 G_vgs**
- 노드 = 넷. 레일은 W0 전압을 가진 고정 노드 하나로 병합하고, 포트 넷은 병합하지 않는다.
- 엣지 = MOS마다 gate–source 무향 엣지 하나(gate 넷 = source 넷인 소자는 제외).
- 스패닝 트리의 비트리 엣지마다 기본 사이클 하나 → KVL `Σ±VGS = ΔV(고정 노드)`.

**분류**(모두 `계산 규칙 있음`)
- (v0) 같은 (gate 넷, source 넷) 평행 엣지 = `equal_vgs`(기존).
- (v1) 서로 다른 포트 넷을 둘 이상 지나는 사이클 = 포트 차 루프(ΔV = 포트 DC 차). 입력 DC가 같게 선언되면 새 결정 제약을 만들지 않고 대칭 매칭과 중복 여부만 대조한다. 예: 파일럿 {M1a,M1b,M4a,M4b}.
- (v2) 나머지 = `kvl_branch` **등식**. 레일을 지나면 ΔV = 레일 전압차, 아니면 0.
  - 멤버 중 drain 전류가 KCL·이상원·미러로 정해지지 않은 소자의 `ID_source` = `kvl_loop`(plan:436).
  - DOF: 등식 1개가 멤버 gm_id 하나를 종속시킨다(N3.7 DOF 등식 목록 plan:421에 추가).
  - 내층 DP: 사이클 멤버를 강결합 셀 그룹(plan:427)으로 두고, 그룹 스캔에서 등식을 만족하는 조합만 남긴다. 탐색 단위일 뿐 값을 같게 만드는 제약은 아니다.
  - 측정 기대: 파일럿 4, pushpull 1, sf 1, 나머지 0(F2).

**VDS를 한 번 포함한 사이클**(G_vgs에 drain–source 엣지를 정확히 1개 허용)
- 기존 `vds_match_vgs_of`·DEC-27 계열이다. 그 VDS 노드를 루프가 W1/W2로 쓰고, 포화 하한(VDsat, DF-25)이 VGS 합의 **부등식**(상한)이 된다(현 구현 sizing_recipe.py:1835-1883의 일반형, 선언 대신 connectivity에서 탐지).
- VDS 엣지 2개 이상은 스택 창(W4)이라 이 규칙 대상이 아니다.

**통합 결론**
- 탐지 규칙 하나에 결과 종류 둘(등식 v2 / 부등식 VDS-1)이다. DEC-15의 이름 목록은 탐지 결과 대조로 바꾼다(DF-23 리터럴 제거와 정합).
- DEC-27 식은 VDS-1 사이클의 파일럿 사례로 남긴다. push-pull 정지전류(원문 L26:87-100)는 v2다.
- G_vgs는 DC 무향 관계 그래프라 S1v 방향 신호 그래프의 루프 분류 (0)~(4)(plan:304)와 별개다. kvl 사이클은 루프 뷰를 만들지 않는다고 명시한다.

### SF-9 body effect 연결과 LUT 커버리지 게이트
- 연결: SF-7 W2 순환 안에서 vsb(DEC-61) → VGS(LUT VS 축 보간) → 레벨 시프트이고, 같은 스냅샷의 gmb(∂ID/∂VSB, plan:445) → 국소 모델·MNA 이득이다. 레벨 시프트와 이득이 같은 vsb를 읽는지 버전 카운터로 확인한다(SC-b).
- **축 커버리지 게이트**: LR3(plan:460)의 외삽 금지를 L 외 축(VGS·VDS·VS)으로 넓힌다. 축 밖이면 클램프하지 않고 구조화 실패(`lut_axis_out_of_range{소자, 축, 값, 범위}`)로 처리한다.
  - 필요한 VS 축 상한은 상수로 두지 않고 `supplies`의 최고−최저 전위 차에서 유도해 LUT 생성 체크리스트 입력으로 둔다.
  - 현 표본 LUT는 VS ≤ 0.8 V(F6)라 두 push-pull 회로 출력단에서 실패할 가능성이 크다(F7).
- 벌크 선언 선택지: 기본 레일(현재 3회로 모두, json 주석) / source 연결(`bulk` = source 넷, vsb 0, 별도 well → LR8 행 분리 plan:465). connectivity라 사용자 결정이고(WP-07), 엔진은 선택지별 이득·레벨 시프트·면적 비교를 보고만 한다.

### SF-10 방향별 최대 전류 = 셀 종류로 구조 판정 (DEC-58·plan:439,446 보강)
노드 k·방향(충전/방전)마다, 그 방향으로 전류를 댈 수 있는 셀(채널 단자가 k에 붙고 반대 단자 경로가 해당 레일로 이어짐)을 분류한다.
- (β) 바이어스 셀(gate 교류접지·DC 고정): 기여 = 동작점 ID(포화 유지 범위 안).
- (σ) 신호 셀: 구동 제한이다. 기여 = W·L 고정에서 LUT ID(VGS_max). VGS_max는 gate 노드의 DC 스윙 한계(SF-11)와 k의 반대 방향 한계로 계산한다. 계산 불가면 "상한 미상".
- (κ) 측면 주입 셀(SF-4): "상한 미상"(과도 해석 없음).

구조 판정:
- 출력 포트 두 방향이 모두 σ면 push-pull, 한 방향만 σ면 class-A.
- class-AB 대 class-B는 SF-8 `kvl_loop` 해의 정지전류 > 0 여부로 정한다(동작점 값이지 구조 판정이 아님).
- 측정 기대(F4): two_stage_ota_sf vout = class-A(흡수 β = M9), 두 push-pull vout = push-pull. 기존 two_stage_ota OUT(M6 σ / M7 β)도 같은 규칙이다.

슬루 제약: `driving_spec` 슬루율이 선언되면 β 방향은 기존 식, σ 방향은 계산값으로 판정한다. "상한 미상"이 걸리면 `기록만`(DEC-59 정지). U-25에는 세 회로 모두 슬루 선언이 없어 현재 발동하지 않는다.

### SF-11 스윙 한계 metric (I-A6 슬롯, 제약은 선언 시만)
- 노드 k 방향별 DC 한계 = 레일에서 k까지 경로 합의 최소 여유. VDS 엣지는 포화 하한(DF-25 유도), VGS 엣지는 그 전류에서의 VGS(vsb 포함 W2)로 센다.
- follower 예시(원문 형태 L21:285-290): `V(out)max = V(g)max − VGS`, `V(out)min = 레일 + VDsat(sink)`. push-pull은 `V(A)max = 레일 − VDsat(전류원)` 뒤에 `V(out)max = V(A)max − VGS`로 연쇄한다.
- 한계에서의 전류: 부하 전류가 선언되면 그 값, 없으면 정지전류(동작점).
- U-25에는 스윙 선언이 없으므로 보고만 한다. 버퍼 입력 범위(ICMR)도 같은 경로 합으로 보고한다.

### SF-12 결정변수·DP 배치·전력
- 버퍼 셀 gm_id·L은 DEC-04대로 독립 결정변수다(S1 등식 제외).
- 버퍼 바이어스 셀 ID는 KCL·이상원·미러로 정해지지 않으면 결정변수다. 예: 단독 buffer의 M5/M6.
- sf opamp 내장 buffer의 M17/M20은 F5 equal_vgs로 앞 블록과 묶여 K2 결합변수 y가 된다.
- 정지전류 비(원문 "W/L ratios define I1 and I2 from I5 and I6", L26:100)는 gm/ID 흐름에서 **SF-8 등식이 만든 종속 관계**다. 독립 결정변수는 {바이어스 ID, kvl_loop 소자 ID, 등식이 종속시키지 않은 멤버 gm_id}다.
- DP 배치(plan:446 명확화): 버퍼 블록은 gain **목표를 받지 않지만** 내층 DP 단계로 결정한다. 블록 gain(음의 dB)을 누적 bin에 더하고, 비용은 전력으로 한다. 이득 블록이 0인 회로(`pushpull_follower_buffer`)는 DP 단계가 버퍼 블록뿐이고, gain 제약이 없으면 bin 없이 비용과 MT1 제약(`rout_ohm`)으로 탐색한다.
- 전력(U-10): 스택 중복 계상의 영향이 회로마다 다르다.
  - `pushpull_follower_buffer`: 전류 경로 셋(M5–M3, M4–M6, M1–M2)이 모두 2소자 직렬이라 배율이 균일해 최적점이 안 바뀐다.
  - `two_stage_ota_sf`: 입력 가지(M3/M1·M4/M2 + 공유 tail M5 → I5에 대해 소자 전류 합 3·I5)와 M6–M7·M8–M9(2배)가 불균일해 목적이 왜곡될 수 있다. U-10 비교표에 포함한다.

### SF-13 버퍼 대조 test 경계 조건 (DoD 7b plan:815 보강)
- (i)의 "DC 고정" 값: 단독 회로 해의 VPB1·VNB1 DC(바이어스 셀 VGS)를 내장 버퍼 경계 N5·N13 DC로 둔다. 반대 방향 대조(내장 해의 N5·N13 DC를 단독 회로 W3 목표로)도 둔다.
- Y DC = agnd는 양쪽이 같다(pushpull json:90).
- (i)에서는 N5·N13 고정으로 K2(F5)가 끊겨 동일성 판정이 가능하다. (ii)에서는 K2 y와 K8 주입이 함께 남으므로 차이 보고에 두 결합을 분리해 적는다.

## 3. v5.9 규칙과의 충돌·정합 점검

| # | v5.9 위치 | 충돌/정합 | 처리 |
|---|---|---|---|
| X1 | N3.7 (a) 우선 판정 plan:420 vs K8 예시·U-25(plan:877)·DoD 7b(ii) | **충돌(정의 공백)**: "순방향 신호 경로" 미정의 + 수동소자 엣지 비용 미정의(plan:310)로 M17/M20이 (a)로 정지할 수 있음 | SF-4로 (b)를 구조 기준으로 바꾸고 (a)에 "합류 노드가 전류 구동이거나 블록 출력노드" 조건 추가. J12 |
| X2 | plan:446 "출력 임피던스에 별도 임계값 없음" vs U-25 `rout_ohm` | **충돌** | SF-6: 문장을 "엔진은 임계값을 만들지 않고 선언된 rout 제약만 판정"으로 수정, metric 신설 |
| X3 | DEC-58·plan:439,446 "조향 가능한 바이어스 전류원 합" | **오판**: 신호 셀 방향(two_stage_ota OUT의 M6, two_stage_ota_sf vout의 M8)을 0/미정으로 기록 | SF-10 β/σ/κ 분류로 교체, J3·J12 위임 문구를 "κ·상한 미상만" 으로 축소 |
| X4 | 규칙 5 bullet(plan:312-314) vs 용어집 plan:85 | **공백**: 바이어스 drain이 붙은 follower 출력 노드가 전류 구동으로 판정되면 CD가 규칙 5 밖 | SF-2 |
| X5 | DEC-15(plan:193) 이름 목록, DEC-27(plan:205) 이름 식 | 일반화 원칙(DEC-62, WP-05)과 긴장 | SF-8로 탐지 일반화, DEC-15·27은 사례로 격하 |
| X6 | N3.4 W2 목록(plan:350) | 공백: CD source 노드 티어 없음 | SF-7 |
| X7 | plan:444 경계 부하 "다음 CS 게이트 용량" + LUT 열 | 근사 오류(CD 부트스트랩) + 데이터 결손(F6) | SF-5, DF 신설 |
| X8 | DEC-57(plan:234) "기존 4개 회로는 follower가 없어 두 수가 같고" vs plan:318·J10(plan:843) folded M8 판정 미정 | 조건부 사실을 단정 | "folded M8이 J10에서 버퍼로 판정되지 않는 한"을 덧붙인다 |
| X9 | LR3(plan:460) L 축만 외삽 금지 | 공백(F6 VS 축) | SF-9 게이트 |
| X10 | plan:446 "버퍼 블록은 할당하지 않는다" vs plan:427 DP 결정 벡터 | 공백: 버퍼 셀 결정 층 없음 | SF-12 |
| -- | 루프 분류 (0)~(4) plan:304 | **충돌 없음**: G_vgs는 DC 무향 관계 그래프라 S1v 방향 신호 루프와 분리. follower 셀은 극성 비반전(plan:317) | SF-8에 "kvl 사이클은 루프 뷰를 만들지 않는다" 명시 |
| -- | 병렬 셀 입력 기준 규칙 plan:420 | 정합(CD 경유 추가로 확장, SF-3-5) | -- |
| -- | DEC-59 발동표 | 새 분기 추가 필요: `계산 규칙 있음` = CD 셀, 버퍼 묶음(단일 합류), SF-8 v0/v1/v2·VDS-1, SF-10 β/σ 분류, SF-4 K8 구조 기준 / `기록만` = CD·CS 이중 출력, 다출력 버퍼 묶음, 구동 종류 혼재(K8 아님), κ·상한 미상에서의 슬루 선언. 검증 발동 회로: v2·push-pull·버퍼 묶음 = 두 push-pull 회로 + 파일럿(v2), class-A follower = two_stage_ota_sf, K8 = sf opamp | -- |
| -- | J3(plan:836) | 정합: 버퍼 블록 경계 넷만 공유(SF-3-4)는 J3 근거와 같은 논리. 파일럿 v2 사이클 4개가 J3 정지전류 규칙의 탐지 결과가 되는지 J3에서 확인 | J3 대조표에 SF-8 결과 첨부 |
| -- | J10(plan:843) | 정합: 기본안(독립 버퍼 블록) 그대로. SF-3이 그 경계 절차 | -- |

## 4. 공동분석 항목 (J12에 추가)

- **J12-a** 버퍼 블록 경계 3건(SF-3 측정 기대값): pushpull {vin; A,B,vout}, sf {Y; N17,N20,vout}, two_stage_ota_sf {OUT; vout}. 앞 이득 블록 출력노드(OUT, Y)와의 경계.
- **J12-b** A·B·N17·N20의 구동 종류 = 전압 구동(SF-2)과 M5/M6(단독)·M17/M20(내장)의 load 귀속.
- **J12-c** SF-8 사이클 판독: 두 push-pull 루프의 멤버·부호(`VGS4+VSG3 = VGS1+VSG2` 형태, L26:89), 파일럿 레일 경유 4사이클이 J3의 정지전류 루프와 같은지(DEC-15 M11a/M11b/M20a/M20b 대조), 파일럿 포트 차 루프 {M1a,M1b,M4a,M4b}를 제약에서 뺄지(v1).
- **J12-d** M17/M20: SF-4 기준으로 K8인지 (a)인지. 원문 L26:166 "bias currents through M18 and M19 vary with the signal"의 해석.
- **J12-e** 출력 방향 분류(SF-10): two_stage_ota_sf vout = class-A(흡수 바이어스 제한), 두 push-pull vout = push-pull, 파일럿 Vop/Vom = push-pull CS(J3와 함께).
- **J12-f** `kvl_loop` 소자 목록(M1/M2, M21/M22)과 합류 노드 KCL `I_M1 = I_M2`(출력 DC 부하 전류 없음 전제)의 성립.
- **J12-g** two_stage_ota_sf: Cc가 O1–OUT(json:80-83)이라 follower M8은 Miller 루프 밖이고 vout이 별도 극점 노드인지(보상 GB5 입력).
- **J12-h**(범위 밖 관찰, 미검증) sf opamp M6(g=N5, d=N56)·M5(s=N56, d=N5) 복합 diode: 방향 신호 그래프에서 N5→N56(M6 g→d)→N5(M5 s→d, N56 전류 구동) 폐경로가 능동 셀 둘·수동소자 없음이다. 루프 분류 (2) 예시 문구 "능동 셀 하나와 저항"(plan:304)과 맞지 않아 (4)로 떨어질 수 있다. M7/M8·M13/M14도 같은 형태다. J11 대조표에서 확인 권고.

사용자 결정(U, 회로 해석 아님):
- **U-27** LUT 재생성: VS 축 상한 = `supplies` 전위 차에서 유도, CGS·CGB 열 추가(체크리스트 :37은 이미 probe). 기본안: 재생성 전에는 두 push-pull 회로의 사이징을 착수 조건 미충족으로 둔다.
- **U-28** follower 벌크 선언 변경 여부. 기본안: 도면대로 레일 유지(변경 없음), SF-9 비교 보고만.
- **U-29** 스윙·버퍼 입력 범위 제약 선언 여부(I-A6). 기본안: 보고만.

## 5. 계획서 반영안 (문장 초안)

**용어집**
- plan:84 셀 행 끝에 추가: "신호를 gate로 받는 소자의 출력 단자는 교류접지가 아닌 채널 단자다(drain 교류접지 = CD, source 교류접지 = CS, 둘 다 아니면 N3.2-3 SF-1)."
- plan:85 '입력 노드 구동 종류'를 교체: "노드에 신호가 들어오는 단자로 정한다: 신호 셀의 source 단자(CD 출력)로 들어오면 전압 구동, 신호 셀의 drain 단자로 들어오면 전류 구동. 바이어스 셀의 drain·source는 load다. 둘이 함께 들어오는 노드는 drain 쪽이 측면 주입(K8)이면 전압 구동, 아니면 `review_needed`."
- plan:90 버퍼 블록 괄호 안 끝에 추가: "묶음은 N3.2-6의 R(u) 절차로 만들고, 합류 노드가 둘 이상이면 `기록만`."
- 신설 행 "G_vgs": "MOS gate–source 무향 엣지와 레일 병합 고정 노드로 만든 DC 관계 그래프. 기본 사이클이 `equal_vgs`(평행) / 포트 차 루프 / `kvl_branch` 등식 / VDS 1개 포함 부등식으로 분류된다(DEC-64). 신호 루프 분류와 무관하다."

**DEC 신설**(plan:239 뒤)
- **DEC-63** "follower 묶음은 전압 구동 넷 u에서 CD·pass 엣지로 도달하는 노드 집합 R(u)이며, 합류 노드가 하나면 버퍼 블록 {u, R(u), v}다. 버퍼 블록 속성(이득·출력 임피던스)은 국소 모델이 단자 스탬프로 계산하고 별도 분기를 두지 않는다. 앞 블록 경계 부하는 다음 블록 국소 모델의 입력 넷 어드미턴스다(cgs는 source 노드에 스탬프). 버퍼 블록은 gain 목표를 받지 않지만 내층 DP 단계로 결정된다."
- **DEC-64** "`kvl_branch`는 G_vgs 기본 사이클에서 탐지한다. VGS만의 사이클(포트 차 루프 제외)은 등식이며 `kvl_loop` 정지전류와 gm_id 종속 1개를 만든다. VDS 엣지를 정확히 하나 포함한 사이클은 그 VDS 노드를 쓰고 포화 하한이 부등식이 된다(DEC-27은 이 형태의 사례). DEC-15의 이름 목록은 탐지 결과 대조로 대체한다."
- **DEC-65** "노드·방향별 최대 전류는 공급 셀 종류로 판정한다: 바이어스 셀 = 동작점 ID, 신호 셀 = LUT ID(VGS_max, 스윙 한계에서 계산), 측면 주입 셀 = 상한 미상. 출력 포트 두 방향이 모두 신호 셀이면 push-pull, 한 방향이면 class-A다. DEC-58의 '조향 가능한 바이어스 전류원 합'은 바이어스 셀 방향에만 적용한다."
- **DEC-66** "`output_impedance_ohm(port)` = 전체회로 MNA에서 여기원을 교류접지로 두고 출력 포트에 전류를 주입한 저주파 개루프 값. 선언된 `rout_ohm`만 판정한다."

**N3.2**
- plan:306 셀 우선순위 첫 문장 뒤: SF-1 문장.
- plan:314 bullet 끝: "CD 사슬과 상보 CD 합류는 DEC-63의 묶음 절차로 한 버퍼 블록이 된다. 버퍼 블록 입력 넷은 앞 이득 블록 출력노드와 공유하는 유일한 넷이다."
- plan:304 (2)~(4) 뒤: "G_vgs 사이클(DEC-64)은 DC 관계이며 루프 뷰를 만들지 않는다."
- plan:310 규칙 4: "수동소자 엣지 비용은 ○(6a design 확정)" -- 미정의 해소 요구만 적는다(값은 design).
- plan:318 (iv) 뒤: "(v) G_vgs 사이클 분류와 출력 포트 방향 분류(DEC-64·65) -- 기존 4개 회로의 `kvl_branch`는 파일럿에만 나와야 한다(측정: 레일 경유 4, 포트 차 1)."

**N3.4** plan:350 W2 행 끝: ", 신호 CD 셀의 source 노드(`V(s) = V(g) ∓ VGS(…, vsb(V(s)))`, 합류 노드는 `kvl_branch` 등식과 한 블록)".

**N3.6** 봉인 항목 신설 7: "`kvl_branch` 등식 잔차 ≤ tol_V."

**N3.7**
- plan:415 K8 행: 정의를 SF-4 세 조건으로 교체.
- plan:420 (a) 괄호에 "합류 노드가 전류 구동이거나 블록 출력노드" 추가. 입력 기준 규칙에 "같은 묶음의 CD 셀" 추가.
- plan:421 DOF 등식 목록에 "`kvl_branch` 등식" 추가.
- plan:427 강결합 셀 그룹에 "`kvl_branch` 사이클 멤버" 추가.
- plan:439 끝 문장을 "측면 주입 셀·상한 미상 방향만 J3·J12 결론을 따른다"로 축소.

**N3.8**
- plan:444 경계 부하 문구: SF-5.
- plan:446: "출력 임피던스에는 별도 임계값을 두지 않는다 --" 이하를 DEC-66 문장으로 교체. "버퍼 블록은 … 할당하지 않는다"를 "gain 목표를 받지 않고 DP 단계로 결정한다(DEC-63)"로 교체.
- 신설 bullet "스윙·입력 범위": SF-11(선언 시 제약, 아니면 보고).

**N3.9** LR3(plan:460) 끝: "L 밖 축(VGS·VDS·VS)도 외삽하지 않는다. 축 밖은 `lut_axis_out_of_range` 구조화 실패다. 필요한 VS 축 상한은 `supplies` 전위 차에서 유도한다."

**DEC 수정**
- DEC-57(plan:234): "기존 4개 회로는 follower가 없어" → "기존 4개 회로는 순수 follower가 없어(folded M8은 J10 판정 전까지 미정)".
- DEC-58(plan:233) 끝: "(방향별 최대 전류 판정은 DEC-65)".
- DEC-15·27 상태 열: "사례, 일반 탐지는 DEC-64".

**DF 신설**(plan:737 뒤)
- **DF-27** "LUT 표본 VS 축 0~0.8 V(5점)가 push-pull 출력 follower vsb(agnd 출력 기준 약 0.9 V)를 덮지 못할 수 있고, 축 밖 입력의 처리 규칙이 없다 | `sky130_nfet_pfet_lut_sample.npz`, `GmIdLUT` 보간부 | 4(red: VS 축 밖 픽스처) | LR3, DEC-61, U-27".
- **DF-28** "LUT에 CGS·CGB 열이 없어(CGG·CGD만) CD 입력 용량 부트스트랩과 follower 영점을 스탬프할 수 없다. 생성 체크리스트(:37)는 두 열을 probe한다 | LUT npz, MNA 스탬프부 | 7a(열 추가 전 근사 표시) | DEC-63, U-27".

**J12**(plan:845) 끝에 J12-a~h 문장을 추가한다. U-06 소비 Phase는 7b 정지전류(J12-c,f)·6a 구조(J12-a,b,d,e,g,h)로 나눈다.

**U 신설** U-27·U-28·U-29(§4 문장).

**DoD**
- 6a(plan:811) 끝: "CD 셀·버퍼 묶음·G_vgs 사이클 분류·출력 방향 분류가 library 7회로에서 ratified 대조표와 일치, 기존 4개 회로에서 CD 0·버퍼 묶음 0·`kvl_branch`는 파일럿만".
- 6b(plan:812): "CD source 노드 W2 고정점 수렴 픽스처, `kvl_branch` 등식 봉인 위반 픽스처 거부".
- 7a(plan:814): "버퍼 블록 국소 모델 이득·출력 임피던스가 test 쪽 독립 폐형식(gmb 포함)과 일치, `output_impedance_ohm` `verified_by`, LUT 축 밖 픽스처 거부".
- 7b(plan:815) 버퍼 대조 test (i)에 SF-13 DC 출처 문장, (ii)에 "K2(N5·N13 equal_vgs)와 K8 주입을 분리 보고" 추가.
