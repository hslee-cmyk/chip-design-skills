# 교과서 gm/ID 손계산 순서 기준 원칙·결정·계획 규칙 감사 + 통합 규칙 초안

- 작성: 감사 agent, 2026-10-26. 계획·design·엔진·spec은 고치지 않았다. 이 파일과 `wt/_scratch_handorder/`(원문 텍스트 추출·스크립트·결과)만 썼다.
- 사용자 지시(원문, 2026-10-26):
  1. "보정안보다 손계산 순서를 기준으로 원칙이 위배되는 부분을 수정해보자. 이 손계산 순서때문에 영향받는 원칙들이 뭐가 있는지 보고해"
  2. (범위 확대) "여기에 앞서정리한 동적전류, 정적전류, 최대전류 등의 개념을 적용하여 일관된 규칙들로 다듬어질 수 있는지 확인해"
  3. (기준) "기존 원칙이 맞지 않다면 그 원칙을 수정하는 것을 포함하여 가장 일관되고 합리적인 원칙을 도출해서 보고해"
- 대조 자료(읽기만, 줄 번호는 그 파일 기준)
  - 계획 v6.38 미승인안 `wt/plan-v638/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(DEC 행 줄 번호는 master v6.37과 같다 -- LA1C 머리 확인): N1.1 138행, DEC-58 255, DEC-64 263, DEC-65 264, DEC-67 266, DEC-70 269, DEC-71 270, DEC-73 272, DEC-92 291, DEC-95 294, DEC-100 299, DEC-103 302, U-112 2268, U-115 2271.
  - headroom-chain 계획 v0.7.9 `wt/plan-v638/docs/01-plan/features/headroom-chain.plan.md` N3.1(211~273행).
  - design 41(master 판) `wt/plan-v638/docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`: §5.3.3 915~933행(S 924·B 925·F 926), §5.3.4 935행, §6.1 1501행(7. 1512행), §6.2 1526행(icmr 1547행), §6.5 1601행, §6.7 1673행(원리 1675행).
  - 사용자 결정 `wt/_drafts/user_decisions.md`: L-11(229행), O-25·O-26(644·645행), O-29~O-33(648~653행), DEC-103(766행), O-115(800행), O-119(826행), O-120~O-123(837~858행), O-127(881행).
  - 앞선 증거: `2026-10-26/la1_design_covers_c1c2.md`(LA1C), `2026-10-26/theta_basis_principle_audit.md`(TBA), `2026-10-25/load_drive_principle_audit.md`(LDA), `2026-10-25/steady_vs_dynamic_current_sizing.md`(SVD).
  - 엔진 as-built `wt/integ-it12` `34585913`(읽기·실행만, 실행 전후 `git -C … status --short` 같음 -- `_scratch_handorder/out_git_before.txt`·`out_git_after.txt`).
- heldout은 쓰지 않았다.

---

## 0. 결론 (도출된 원칙 집합 요약)

1. **교과서 순서의 공통 골격**(§1, 원문 확인): spec → 보상·부하 C → **전류 하한**(대신호·부하 요구) → **신호 gm**(GBW·PM·rout) → S 소자 gm/ID·L → ID → **B 소자 = 헤드룸 고리의 나머지**(S가 정해진 뒤) → 종속 소자(미러 비·자기 바이어스 R = VDsat/I·바이어스 생성) → 이득·전력 검사 → SPICE.
   - 고리 안에서 **종속은 '전력에 중립인 쪽'**(B 밀도, 저항 값)이고, S(전류를 정하는 소자)는 종속이 되지 않는다. Allen L160 단계 6이 S1(단계 5)의 β1을 써서 S5(꼬리)를 정하는 것이 그 꼴이다.
2. **어긋나는 것**(§2 판정표 요약)
   - O-127 (ii): S가 섞인 고리에서 B를 고정하고 S 정의역을 자른다. **종속 방향이 교과서와 반대**다.
   - O-122: 교과서는 SR로 전류 하한을 정한다(Allen 단계 2, L190 단계 1, L26). 엔진은 0이고, oracle FAIL 뒤 처리도 미정의다(U-112).
   - L-11 '외층이 B를 다듬는다'와 DEC-73 (3) 수리: B 밀도의 writer가 셋이 된다(TBA W-1·W-2).
   - design 41 §6.2 헤드룸 예산: 고리 폭을 모든 소자에 고르게 나눈다. 실측으로는 하한이 **S(입력 소자)에만** 걸리고 꼬리 B에는 걸리지 않았다(§3.2).
   - O-26 (1)·DEC-65: 공급 능력을 동작점 전압의 총 전류로 잰다. 교과서(Allen L040)는 극단 상태의 순 전류다(LDA F1·F2).
   - N1.1 '결정 순서': 전류 하한 단계와 B 나머지 단계가 없다.
3. **맞는 것**: DEC-95 (3)(S는 독립 유지 -- 교과서와 같은 종속 방향), DEC-70(AC·대신호 → θ 제약), DEC-71 (4) (a)(b), O-29~O-31(정의·계산법 분리, 손계산 기본), DC/AC 분리, O-115·O-119(정의뿐이고 순서와 무관), DEC-103(설계점 = θ), §6.5 매크로(실측: gm6이 교과서 식과 1 % 안).
4. **통합 가능성**: 손계산 순서, 전류 개념(SVD·LDA), θ 기저(O-127·TBA)는 **하나의 규칙 집합으로 모인다**(§5). 핵심 장치는 셋이다.
   - (가) 요구 셋(소신호·정상상태·동적)을 spec 양으로 둔다. 능력은 θ 봉인점 필드 하나로 둔다.
   - (나) KVL 고리마다 종속 성분을 **구조 순위**(X > 값 미선언 저항 강하 > B 밀도 > W4 > F > S)로 하나 고른다. 그 값은 고리의 다른 구성원이 다 정해지는 가장 이른 단계에서 **한 블록이 파생**한다(writer 하나, B만 고리는 graph reuse로 1회).
   - (다) 극단 상태는 같은 W로 평가한다. 정확값은 oracle이 정한다.
5. **수정 대상 기존 원칙 11건**(§7). 그중 사용자 결정을 바꾸는 것은 O-127 (i)(ii), L-11, O-122, O-26 (1)/DEC-65, DEC-70 θ 정의, DEC-103 문언(계산법 보강)이다. 열린 결정 D1~D7·B1·W-1~W-5·U-115·U-new1은 승인 목록 하나(Q1~Q9, §8)로 대체할 수 있다. 'A1~A7'은 묶음으로 찾지 못했다(§10).

---

## 1. 교과서 손계산 순서 (원문 확인)

원문은 모두 로컬 사본에서 텍스트를 뽑아 읽었다(`_scratch_handorder/extract.py` → `txt/*.txt`, PyMuPDF). 저장소 `assets/library/sources/`에는 2단 OTA 설계 절차 원문이 없다. Allen Lecture 26(buffer 예제)만 있다. 그래서 원본 우선순위 규칙(README)의 `G:/내 드라이브/work/Todoc/` 사본을 썼다. **저장소 원문 보관소에 넣지는 않았다**(이 감사는 파일을 고치지 않는다 -- 넣을지는 오케스트레이터 판단).

### 1.1 출처 목록

| # | 출처 | 웹 | 로컬 PDF | 쪽 |
|---|---|---|---|---|
| T1 | P.E. Allen, ECE6412 Lecture 160 'MOSFET Op Amp Design'(1/30/04) | 저자 게시처(Georgia Tech pallen 사이트 ECE_6412 폴더, LDA §근거의 L040과 같은 경로 형식) -- **이 파일의 웹 주소는 확인하지 않음** | `G:/내 드라이브/work/Todoc/기술문서/설계문서/11_강의자료/(강의) Analog Integrated Circuit Design - Allen/L160-MOSOpAmpDesign(2UP).pdf` | Page 160-3~160-11, 160-12~13(nulling R) |
| T2 | Allen, ECE6412 Lecture 190 'Cascode Op Amps - I'(2/18/02) | 같음(미확인) | 같은 폴더 `L190-CascodeOpAmps-2UP.pdf` | Page 190-18(설계 표), 190-19~21(Example 3) |
| T3 | Allen, Lecture 26 'Buffered Op Amps'(6/25/14) | [aicdesign.org lecture26-140625.pdf](https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf) | `chip-design-skills/skills/analog-gmid-design/assets/library/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf` | Page 26-24~26-26(Example 26-2) |
| T4 | Allen, ECE6412 Lecture 300 'Buffered Op Amps'(3/21/02) | 미확인 | 같은 폴더 `L300-BufferedOpAmps-2UP.pdf` | Page 300-18~19(Example 7.1-2) |
| T5 | Allen, ECE6412 L040 'CE and CS Output Stages' | [pallen.ece.gatech.edu L040](https://pallen.ece.gatech.edu/Academic/ECE_6412/Spring_2004/L040-CS&CEOut(2UP).pdf) | `wt/_scratch_mincur/dl/L040.pdf`(LDA·SVD 인용 그대로, 이번에 다시 열지 않음) | p.040-3, p.040-5 |
| T6 | Silveira, Flandre, Jespers, 'A gm/ID based methodology …', IEEE JSSC 31(9), 1996 | [TAMU 사본](https://people.engr.tamu.edu/hoyos/courses/474/gm_ID_methodology_silveira_jssc_1996.pdf) | `G:/…/기술문서/Gm_over_Id/(Bible - original paper) A gm ID Based Methodology …__1996.pdf` | p.1315~1317 §III |
| T7 | Jespers & Murmann, *Systematic Design of Analog CMOS Circuits*, CUP 2017, 3장 | [doi:10.1017/9781108125840.003](https://doi.org/10.1017/9781108125840.003) | `G:/…/Gm_over_Id/(E-book) systematic design of analog CMOS circuits/3 basic-sizing-using-the-gmid-methodology.pdf` | 책 p.65~66(§3.1.2·§3.1.3) |
| T8 | 같은 책 6장 | [doi:10.1017/9781108125840.006](https://doi.org/10.1017/9781108125840.006) | 같은 폴더 `6 practical-circuit-examples-ii.pdf` | 책 p.255~257(Ex. 6.4·흐름), p.271~272(2단 흐름), p.284~285(§6.4.1·§6.4.2 간이 흐름) |

SVD §7-1은 T7·T8을 '원문 미열람'으로 적었다. 이번에 로컬 사본으로 열람했다.

### 1.2 Allen 2단 OTA (T1 Page 160-5~160-7) -- 단계마다 입력과 종속

원문 인용(Page 160-5): "1. From the desired phase margin, choose the minimum value for Cc … Cc > 0.22CL", "2. Determine the minimum value for the "tail current" (I5) from the largest of the two values. I5 = SR·Cc or I5 ≅ 10(VDD + |VSS|)/(2·Ts)", "3. Design for S3 from the maximum input voltage specification", "4. Verify that the pole of M3 … > 10 GB". Page 160-6: "5. Design for S1 (S2) to achieve the desired GB. gm1 = GB·Cc → S2 = gm2²/(K'2·I5)", "6. Design for S5 from the minimum input voltage. First calculate VDS5(sat) then find S5. VDS5(sat) = Vin(min) − VSS − √(I5/β1) − VT1(max) ≥ 100 mV", "7. Find S6 by letting the second pole (p2) be equal to 2.2 times GB and assuming that VSG4 = VSG6", "8. Calculate I6 … Check to make sure that S6 satisfies the Vout(max) requirement", "9. Design S7 to achieve the desired current ratios between I5 and I6. S7 = (I6/I5)S5". Page 160-7: "10. Check gain and power dissipation", "11. If the gain specification is not met, then the currents, I5 and I6, can be decreased or the W/L ratios … increased", "12. Simulate the circuit".

| 단계 | 입력(이미 정해진 것) | 종속으로 나오는 것 | 소자 종류(이 감사의 S/B/X) |
|---|---|---|---|
| 1 | PM spec, CL | Cc 하한 | 보상 수동소자 |
| 2 | SR spec(또는 정착 Ts), Cc | **I5 하한(= 최댓값)** | 꼬리 전류(θ 전류) |
| 3 | Vin(max) spec, I5, VT | S3(=S4) -- 최대 ICMR 고리의 나머지 | B(부하) |
| 4 | S3, I5 | 미러 극점 검사 | 검사 |
| 5 | GB spec, Cc, I5 | gm1 → S1 | **S** |
| 6 | Vin(min) spec, I5, **β1(단계 5)** | VDS5(sat) → S5 -- 최소 ICMR 고리의 나머지 | **B(꼬리), S가 섞인 고리** |
| 7 | PM(p2), CL, Cc, gm1, S4·gm4(VSG4 = VSG6) | gm6 → S6 | S(2단 입력) |
| 8 | gm6, S6 | I6, Vout(max) 검사 | θ 전류 |
| 9 | I6/I5, S5 | S7 | X(미러 비) |
| 10~12 | 전부 | 이득·전력 검사, 반복, SPICE | 검사 |

nulling 저항(Page 160-13): "Rz = (1/gm6)·(CL + Cc)/Cc" -- gm6이 정해진 뒤의 파생값이다. 단계 1의 0.22·CL은 RHP 영점 조건(gm6 ≥ 10·gm1)과 p2 = 2.2·GB에서 나온다. 영점 상쇄 R이 있으면 이 하한은 성립하지 않는다(§3.1 실측).

### 1.3 Allen folded cascode (T2 Page 190-18 표, Example 3 Page 190-19~20)

| 단계(원문) | 원문 식 | 입력 | 종속 | 종류 |
|---|---|---|---|---|
| 1 Slew Rate | "I3 = SR·CL" | SR, CL | 꼬리 전류 | θ 전류 |
| 2 Bias currents in output cascodes | "I4 = I5 = 1.2I3 to 1.5I3 -- Avoid zero current in cascodes" | I3 | 출력 가지 전류 | θ 전류(원문의 1.2~1.5는 경험 계수 -- **엔진에 옮기면 상수 발명**) |
| 3·4 Max/min output voltage | "VSD5(sat) = VSD7(sat) = 0.5[VDD − Vout(max)]", "VDS9(sat) = VDS11(sat) = 0.5(Vout(min) − \|VSS\|)" | 스윙 spec, I4·I5 | S4~S11 -- 스윙 고리 폭을 같게 나눔 | B·F(캐스코드 적층, S 없음) |
| 5 Self-bias cascode | "R1 = VSD14(sat)/I14 and R2 = VDS8(sat)/I6" | 3·4의 VDsat, 전류 | R | 값 미선언 저항(파생) |
| 6 GB | "S1 = S2 = gm1²/(KN'I3) = GB²CL²/(KN'I3)" | GB, CL, I3 | S1 | **S** |
| 7 Minimum input CM | "S3 = 2I3/[KN'(Vin(min) − VSS − √(I3/(KN'S1)) − VT1)²]" | Vin(min), I3, **S1(단계 6)** | S3(꼬리) | **B, S가 섞인 고리** |
| 8 Maximum input CM | "S4 = S5 = 2I4/[KP'(VDD − Vin(max) + VT1)²] -- S4 and S5 must meet or exceed the value in step 3" | Vin(max), I4 | S4·S5 하한 -- **여러 고리의 요구 중 최댓값** | B |
| 9·10 | 이득·전력 | -- | 검사 | -- |

- 순서가 2단과 다르게 보이는 것(스윙 고리 3·4가 GB 6보다 앞)은 그 고리에 S가 없기 때문이다. S가 섞인 고리(7)는 S(6) 뒤에 온다. **2단과 같은 규칙**이다.
- 자기 바이어스 R은 전류와 VDsat가 정해진 뒤 나온다. O-127 (iii) 'R = V_R/I_R 파생'과 같은 방향이다. 다만 교과서는 V_R도 B 밀도(VDsat)의 종속으로 둔다(§2 O-127 (iii) 행).

### 1.4 Allen buffer·출력단 (T3·T4·T5)

- T3 Page 26-25: "SR = 10V/µs and 100pF capacitor give I15 = 1mA", "To get Rout = 50Ω, if 1/gm15 is 25.8Ω, then design gm12 as … gm12 = 810µS" → 순서 = **동적 요구 → 출력 전류 → rout 요구 → follower gm → W**. 전류 거울 W는 비로 정한다("W14/L14 = (1000µA/125µA)160").
- T4 Page 300-18~19(Example 7.1-2): 같은 순서("SR = 10V/µs and 100pF capacitor give I11 = 1mA", "design gm9 as gm9 = 1/[(Rout − 1/gm10)(1+βF)]").
- T5 p.040-3·p.040-5(LDA·SVD 인용): "|I_OUT| > C_L·SR, |I_OUT| > v_OUT(peak)/R_L. The maximum current will be determined by both", "W1/L1 = 2(I_OUT⁻ + I_Q)/[K_N'(V_DD + |V_SS| − V_TN)²]" → 출력 소자 W는 **극단 상태(게이트를 레일까지 몬 순 전류)**에서 정한다. 정지전류 소자는 I_Q에서 정한다.

### 1.5 gm/ID 원전 (T6·T7·T8)

- T6 p.1316: "1) The drain current of each transistor is determined from the specified total current Itot and the choice of the current mirror factor B", "Choosing the values for gm/ID, ID is determined …", "The current mirror transistors are operated in strong inversion, with (gm/ID)3 equal to eight, to guarantee good matching and noise properties", "If the phase margin (PM) is not acceptable, the values of B, (gm/ID), or transistor lengths must be modified." → 전류(전력 예산) → 신호 소자 gm/ID(이득·fT 절충) → 부하 gm/ID는 **matching·잡음으로 고른 값**(헤드룸 고리가 아님) → L → W → PM 검사·반복. p.1315: "For large-signal related performance aspects such as signal swing, an ID–VG or gm/ID–VG relationship is required"(스윙은 같은 점으로 예측).
- T7 책 p.65(§3.1.2): "1. Determine gm (from design specifications). 2. Pick L … 3. Pick gm/ID: large gm/ID → low power, large signal swing (low VDsat); small gm/ID → high speed, small area. 4. Determine ID (from gm and gm/ID). 5. Determine W (from ID/W)."
- T8 책 p.255(Ex. 6.4): "If we split this voltage equally, then each transistor has a minimum VDS of 200 mV … restricts the gm/ID of the transistors to values larger than 10 S/A … we decide on gm/ID = 15 S/A for all transistors in the output branches." 같은 쪽: "The first step is to design the cascode stack (M2–M5) based on the circuit's output swing and low-frequency loop gain requirements. Next, we investigate the optimum inversion level for the input pair." 책 p.257: "3. Given a value for (gm/ID)1, we can now compute ID1. This fixes all currents and device widths in the circuit, since we have already chosen gm/ID values for the cascode stack."
- T8 책 p.271(2단): "The transconductance ratios between active loads and signal path devices (gm3/gm1 and gm4/gm2) … reducing these ratios comes with a loss in swing … A reasonable pick will suffice in practice." 흐름: "1. Calculate the required compensation capacitance … 2. Calculate the required gm1 … ωu1. 3. Calculate the required gm2 … ωp2." 책 p.284 §6.4.2: "1. Assume that the circuit will slew for some fraction of the settling time … 11. Calculate the slewing parameter X and the actual settling time. Adjust your slewing budget in step 1 and repeat all calculations, if needed." 책 p.285: "Evaluate the circuit in SPICE."

### 1.6 공통 골격 (회로 꼴과 무관하게)

| 순번 | 단계 | 입력 | 종속 | 교과서 근거 |
|---|---|---|---|---|
| H0 | 요구 정의 | spec | 소신호 요구(GBW·PM·이득·rout), 정상상태 요구(ICMR·스윙 범위 끝, R_L·I_L 부하 전류), 동적 요구(SR·정착 → C·dV/dt) | T1 Page 160-4 spec 목록, T5 p.040-3 |
| H1 | 보상·부하 C | PM, CL | Cc(하한 또는 최소값) | T1 단계 1, T8 p.271 흐름 1 |
| H2 | **전류 하한** | 동적 요구 × 노드 C, 정상상태 부하 전류 | 해당 가지의 최소 전류 | T1 단계 2 'largest of', T2 단계 1, T3·T4, T5, T8 §6.4.2 단계 1·11(반복) |
| H3 | 신호 gm | GBW·C, 비주극점(PM)·C, rout | gm1, gm_k, follower gm | T1 단계 5·7, T3, T7 단계 1 |
| H4 | S gm/ID·L → ID | gm, 이득 요구(L), 속도(fT) | ID = max(gm/(gm/ID), H2 하한), W | T7 단계 2~5, T6, T1 단계 5 |
| H5 | **B = 헤드룸 고리의 나머지** | 고리 폭(레일·범위 끝), 고리 안 S의 VGS/VDsat(H4), 전류 | B 밀도(VDsat). 여러 고리면 가장 엄한 것. 고리가 묶지 않으면 matching·잡음·gm 비로 고른 값 | T1 단계 3·6, T2 단계 3·4·7·8, T8 Ex. 6.4·p.271, T6(부하 gm/ID 8) |
| H6 | 종속 소자 | B 밀도, 전류 비 | 미러 W(비), 자기 바이어스 R = VDsat/I, 영점 R, 바이어스 생성 | T1 단계 9·Page 160-13, T2 단계 5, T3 W14 |
| H7 | 검사·반복 | 전부 | 이득·전력·스윙·PM 검사, 어긋나면 전류·gm/ID·L 조정 | T1 단계 10·11, T6, T8 단계 11·12 |
| H8 | 최종 | -- | SPICE | T1 단계 12, T8 단계 14 |

- **종속 방향의 일반형**: 한 KVL 고리에서 정해지는 순서는 '전류를 정하는 좌표(S·θ 전류) → 전력 중립 좌표(B 밀도) → 파생값(R, 미러 비)'이다. 전력 중립 좌표가 고리의 나머지를 받는다.
- **회로 꼴에 따른 차이는 순서 규칙이 아니라 고리 구성의 차이다.** folded cascode에서 스윙 고리가 GB보다 앞인 것은 그 고리에 S가 없기 때문이다(§1.3).
- **원문의 경험 계수**(Allen 1.2~1.5·I_Q 비, ≥100 mV, Silveira gm/ID = 8, JM gm/ID = 15·β = 0.75β_max·r_self = 0.4)는 손계산 관례다. 엔진 규칙에 옮기면 상수 발명이다. 아래 규칙은 이 수치를 쓰지 않는다.

---

## 2. 영향받는 원칙·결정 판정표

판정: **맞음** / **어긋남** / **부분** / **순서 무관**(정의만 하고 결정 순서를 제한하지 않음, O-29 (2)). '순서 제한' 칸은 그 원칙이 결정 순서를 제한하는지 적는다.

| # | 원칙·결정(자리) | 원문 요지(인용) | 순서 제한 | 손계산 순서 대비 | 판정 | 고칠 방향(문언 초안은 §7) |
|---|---|---|---|---|---|---|
| 1 | O-127 (i)(UD 881) | "B·종속(X) 소자만의 고리: 출발 단계가 B 밀도를 사슬 정합으로 맞춘다(B 밀도 writer = 출발 단계 하나, 층 0은 READS)" | 제한 | S 없는 고리를 먼저 맞추는 것은 H5와 같다(T2 단계 3·4). writer 하나 문언은 S 섞인 고리의 B를 막는다 | **부분** | §7 M1: writer를 '고리 종속 블록 하나'로 |
| 2 | O-127 (ii)(UD 881) | "층 0 결정 변수가 섞인 고리: 층 0 후보마다 판정, 좌표 하나면 그 축 정의역 자르기, 여럿이면 W4·V_R 재배분 뒤 거르기" | 제한 | 교과서는 S를 먼저 정하고 B가 나머지를 받는다(T1 단계 6, T2 단계 7). (ii)는 B를 고정하고 S를 자른다 → **종속 방향 반대**. 전력 최적점(S의 gm/ID)을 자를 수 있다 | **어긋남** | M2: 종속 = 구조 순위 최상위 구성원, B·R이면 층 0 후보마다 파생 |
| 3 | O-127 (iii) | "값 미선언 DC 경로 저항은 강하 V_R 이 결정 변수, R = V_R/I_R 파생" | 제한 | R = V/I 파생은 같다(T2 단계 5). 교과서의 V_R은 B 밀도(VDsat)의 종속이다. 결정 변수가 아니다 | **부분** | M2의 순위에서 V_R은 B보다 앞의 종속(고리 나머지를 먼저 받음) |
| 4 | O-127 (iv) | "그래도 위반이면 fail-closed" | 무관 | H7 검사와 같다 | **맞음** | 유지 |
| 5 | L-11(UD 229) | "필요 gm 정의된 신호 소자만 gm/ID 자유변수(ID = gm/(gm/ID)), 부하·미러·바이어스는 §6 구간·미러비·KCL 로 정하고 격자 곱에서 제외" + design 41 925행 "외층 SLSQP가 다듬는다" | 제한 | 앞 문장은 T7·T6와 같다(S만 gm에서). '§6 구간'으로만 B를 정하는 것은 H5(고리 나머지)를 빠뜨린다. '외층이 다듬는다'는 writer 셋(TBA W-2) | **부분** | M3: B는 어느 층에서도 독립 변수가 아님 |
| 6 | O-122(UD 849) | "슬루 판정과 탐색 모두 oracle `.tran`만 … 엔진은 슬루에 관여하지 않는다" | 제한 | 교과서는 SR → 전류 하한이 단계 2다(T1·T2·T3·T4, T8 단계 1·11은 반복) | **어긋남**(판정을 oracle에 두는 것은 맞음) | M4: 동적 요구는 출발 전류 하한('추정')과 oracle FAIL 되먹임으로만 |
| 7 | O-121·O-120(UD 837·842) | 슬루 엔진 판정·경계(O-122가 대체) | -- | 대체됨 | 판정 없음 | -- |
| 8 | O-115(UD 800) | "ICMR = 입력 포트를 함께 훑고 … 출력을 … 봉인점 동작점에 묶은 상태에서 전 소자가 선언 영역에 머무는 범위" | 무관(정의) | 교과서는 ICMR spec으로 B를 사이징한다(T1 단계 3·6). 정의(무엇을 재나)와 사이징 입력(범위 끝)은 서로 다른 일이다 | **순서 무관·맞음** | 유지. 사이징 쪽은 R4·R7(§5)에서 범위 끝을 고리 폭으로 씀 |
| 9 | O-119(UD 826) | 입력 범위 이름 분리(ICMR / 출력 스윙 / follower 사용 범위) | 무관 | 교과서 ICMR·Vout range와 같은 양 | **맞음** | 유지 |
| 10 | O-123·U-115(UD 858, PL 2271) | 방향별 최대 전류 손계산 규칙 보류 | 무관(계산법) | 교과서 T5: 극단 상태 순 전류(LUT로 일반화 가능) | **빠짐** | M5·R9(LUT 극단 조회 − 반대 가지) |
| 11 | O-26 (1)·DEC-65(UD 645, PL 264) | "노드 k를 동작점 전압에 고정하고 … 그 방향 전류" | 무관(정의) | T5는 범위 끝 상태의 순 전류(LDA F1·F2) | **어긋남**(정의) | M5 = LDA D6 (가) |
| 12 | O-29~O-31(UD 648~651) | 영역 = SPICE 해석 종류, 정의·계산법 분리, 손계산 기본·물리 정합, 층 배치 | 층 배치만 제한 | T1 단계 12·T8 단계 14(손계산 → SPICE)와 같다 | **맞음** | 유지 |
| 13 | DEC-103(UD 766, PL 302) | "설계점 결정 = θ 고정, 정해진 회로 섭동 = W·바이어스 고정 KCL 선형화" | 무관(틀) | 설계점 = θ는 T7과 같다. 극단 상태(T5 출력 W, class-AB 피크 19~658배 -- SVD §5)는 선형화 범위 밖 | **부분** | M6: 큰 편차는 같은 W의 소자 LUT 극단 조회 |
| 14 | DC/AC 분리(DEC-67, O-23) | DC 양은 DC 풀이, AC 양은 봉인 DC 점 소신호 | 무관 | 교과서도 헤드룸(DC) → gm(AC)을 같은 점에서 계산 | **맞음** | 유지 |
| 15 | O-125·O-126(UD 869·874) | LA-1 순서·완료 조건 | card 순서만 | 손계산 순서와 무관(엔진 단계 안의 규칙이 아니다) | **순서 무관** | 유지. LA-1 design이 R5·R6을 담아야 함 |
| 16 | 부하 구동 초안 L0′~L4′·D1~D7(LDA §3·§7.2) | 요구·능력 분리, 범위 끝 + 순 전류, 동적 몫 | 일부 | T5와 같다. D1 (다)(현행 O-122)만 H2와 다름 | **맞음**(D1 제외) | §8 Q3·Q4로 묶음 |
| 17 | 계획 N1.1(PL 138) | "결정 순서를 signal stage 유도 -> 보상 -> gain 할당(gm_id·L) ⇄ 노드전압 DC 해석 -> 전체회로 판정" | 제한 | H2(전류 하한)·H5(B 나머지)·H6(종속)이 없다. gain 할당이 L을 정하는 것은 T8(L from loop gain)과 같다 | **부분** | M7 |
| 18 | DEC-70(PL 269) | "AC·대신호 결과는 DC 값을 직접 덮어쓰지 않고 결정변수 θ … 의 **제약**으로만 되돌아간다" + θ 성분 "DC 전류 경로에 있는 값 미선언 저항 값" | 제한(되먹임 자리) | T1 단계 11·T6·T8 단계 11(반복 조정)은 같은 꼴이다. θ에 B ln IDu·R 값을 독립 성분으로 두는 것은 H5·H6(종속)과 다르다 | **부분** | M11: θ 독립 성분에서 고리 종속(B·V_R) 제외 |
| 19 | DEC-71 (3)(PL 270) | "블록 전류(KCL·선언 -- '슬루 하한'은 v6.37 O-122로 없음)" | 제한 | H2 전류 하한이 없다 | **부분** | M8 |
| 20 | DEC-71 (4) (a)(b)(PL 270) | "(a) 필요 gm에서 gm_id = gm / ID 역산 (b) 목표 이득에서 … L을 역산" | 제한 | T7 단계 1~4·T8(L from gain)과 같다 | **맞음** | 유지 |
| 21 | DEC-71 (4) (c)(PL 270) | "VDS 배분 = 전 소자를 포화 여유 하한(VDsat)으로 채운 뒤 남은 헤드룸을 … ∂(gm/gds)/∂VDS가 큰 소자부터 배분" | 제한 | B 밀도를 고정한 채 W4만 배분한다. 교과서는 B 밀도가 고리 나머지를 받는다(T1 단계 6). 남는 여유를 이득으로 주는 것은 교과서에 없는 확장(물리상 문제 없음) | **부분** | M8: 종속 파생(R5) 뒤 남은 여유만 (c) |
| 22 | DEC-73(PL 272) | 기본 경로 = 층 0 손계산 조립, 수리 `_repair` | 층 배치 | 층 0 손계산은 교과서 손계산과 같다. `_repair`가 B ln IDu를 바꾸면 B writer 둘째(TBA W-1) | **부분** | M9: 수리는 독립 좌표만 |
| 23 | DEC-95 (3)(PL 294) | "종속 gm_id 소자 선택 … ratified 선택 → diode → GB5가 gm을 요구하는 소자·뒤 stage 소자는 독립 유지 → 대칭 궤도 대표 → 이름" | 제한 | **S는 종속이 되지 않는다** -- 교과서 종속 방향과 같다 | **맞음** | R5 순위의 기존 근거로 일반화 |
| 24 | design 41 §6.1-7(1512행) | "gm/ID 선택: 구간 안의 최댓값" | 제한 | S 출발값으로는 T7('large gm/ID → low power')과 맞다. B에 쓰면 H5(나머지)·T6(부하 강반전)과 다르다 | **부분** | design(계획 뒤) |
| 25 | design 41 §6.2(1526~1556행) | 고리 폭을 "VDSAT_k ≤ V_part − Σ_{j≠k}(VDSAT_j,min + tol)"로 나누고 남는 여유는 같은 몫 | 제한 | T8 Ex. 6.4의 '같은 몫'과 닮았지만, S가 섞인 고리에서 교과서는 S 먼저 B 나머지다. 실측: 하한이 S에만 걸림(§3.2) | **어긋남** | design(계획 뒤): R5로 대체 |
| 26 | design 41 §6.5(1601행~) | 매크로: UGF = GBW, PM ≥ 목표, 전원 전류 최소 | 제한 | T1 단계 5·7과 같은 식을 함께 푼다. 실측 gm6이 교과서 식과 1 % 안(§3.1) | **맞음** | 유지 |
| 27 | design 41 §6.7 원리(1675행) | "노드 전압을 먼저 배분하고 gm/ID 를 역산하지 않는다" | 제한 | S에 대해서는 T7과 같다. B는 교과서가 노드 전압(고리 폭)에서 역산한다(T1 단계 3·6) | **부분** | 문언에 'S·F에 대해' 한정 추가(design) |
| 28 | headroom-chain R-1′ N3.1-3(HC 251~257행) | "위반 경로마다 조정 소자 하나를 DEC-95 (3) 순서로 고른다. diode는 조정 소자로 고르지 않는다" | 제한 | 조정 = 종속, DEC-95 (3) 순서 = S 독립 → 교과서 방향과 같다 | **맞음** | 유지(R5가 같은 순위를 씀) |
| 29 | headroom-chain N3.1-5(HC 257~263행) | "한 좌표만 들어가는 부등식: 탐색 상자를 그 좌표의 구간으로 정확히 자른다" | 제한 | 고리에 B가 없을 때(S·F만)만 교과서와 충돌하지 않는다 | **부분** | R5 (c)의 마지막 갈래로 한정 |
| 30 | headroom-chain X-1·N3.1-7(HC 272행) | "상위 DEC-64의 W4 처리는 그대로 두고, R-1′은 그 미지수를 소거한 출발 제약만 더한다" | 제한 | O-127이 이미 '구성'으로 개정 승인 | 판정 없음(O-127 승인 문언) | -- |
| 31 | HC-S `sat_threshold` | 포화 기준 정본 함수 하나 | 무관 | 교과서 VDS ≥ VDsat와 같은 기준 | **맞음** | 유지 |
| 32 | 출발 구간 design 41 §6.6 상태 | "as-built는 spec과 무관한 LUT 포락선 상자 중점" | -- | 교과서에는 상자 중점이 없다 | (TBA C-1~C-14) | R5·R12 |
| 33 | U-112(PL 2268) | 슬루 FAIL 뒤 처리 미정의 | -- | T8 단계 11('Adjust your slewing budget … repeat') = FAIL 되먹임이 교과서 절차 | **빠짐** | M4 (b) |

---

## 3. 실측

스크립트·결과: `wt/_scratch_handorder/scripts/two_stage_handorder.py` → `out/two_stage.json`, `scripts/rows_dump.py` → `out/rows.jsonl`(회로마다 append). 엔진 `integ-it12 34585913`. 컨텍스트 생성은 `_scratch_b80/scripts/probe.py`의 `context()`를 import했다(예산 40, 같은 설정).

### 3.1 two_stage_ota -- 교과서 손계산 대 엔진 출발 단계

spec(`two_stage_ota.sizing_spec.json`): gain ≥ 57 dB, GBW ≥ 7 MHz, PM ≥ 70°, CL = 3 pF(`measurement_load`), Cc·Rz = engine. SR·ICMR·스윙 선언 없음.

| 양 | 엔진(출발 매크로 `graph/start: macro`, 칸 0 봉인점) | 교과서 손계산(T1, 같은 Cc) | 교과서(T1 Cc = 0.22·CL = 0.66 pF) | 비고 |
|---|---|---|---|---|
| Cc | 0.384 pF | (엔진 값 사용) | 0.66 pF | 엔진은 Rz = 2.73 kΩ 영점 상쇄를 함께 둬서 RHP 영점 조건이 없다. T1의 0.22·CL은 영점 상쇄 없는 조건(Page 160-3)이라 적용 범위 밖. 물리 정합 |
| gm1 | 매크로 블록 2.06e-5 S, 봉인점 M1 2.21e-5 S | 2π·GBW·Cc = 1.69e-5 S | 2.90e-5 S | 엔진이 22 % 크다(노드 용량에 cgg 추정 포함 -- T8의 self-loading과 같은 물리) |
| gm6 | 3.67e-4 S | tan(PM)·gm1·CL/Cc = 3.63e-4 S | 3.63e-4 S | **1 % 안**. gm6 ∝ GBW·CL이라 Cc와 무관 |
| I5(꼬리) | 1.80 µA | 1.38 µA(엔진 gm/ID₁ = 24.5) | 2.37 µA | -- |
| I6 | 24.8 µA | 24.4 µA(gm/ID₆ = 14.8) | 24.4 µA | 총 전류 26.6 µA 대 26.8 µA(Cc 0.66) |
| SR = I5/Cc | 4.69 V/µs | -- | 3.59 V/µs | SR 선언이 없어 검사 없음. 교과서 단계 2가 비활성 |
| gm/ID: S M1·M2 / M6 | 22.9 / 14.8(구간 [18.9, 24.1] / [1.4, 18.9], t = 0.8) | -- | -- | T7 'large gm/ID → low power'와 같은 쪽 |
| gm/ID: B M3·M4(부하) | 14.4(구간 상한 15.3 = `offset_guard_6.4_2a`) | -- | -- | 부하 상한은 offset·잡음 가드 -- T8 gm 비 선택과 같은 물리 |
| gm/ID: B M5·M7(꼬리·싱크) | 22.6(구간 [16.9 `w_min_gm_id`, 24.3 `area`], t = 0.8) | 교과서: 고리 나머지(T1 단계 6) 또는 강반전(T6) | -- | **헤드룸 고리 하한 없음**(ICMR·스윙 선언 없음). 약반전 끝(VDsat 최소) 쪽을 고름 |
| L(모든 소자) | 0.15 µm(LUT 최솟값) | T8: 이득 요구로 L을 먼저 고름 | -- | 이득 L 하한 `gain_l_6.4_1`이 `u9_value_not_certified`로 비활성 |

- 판정:
  - **보상·신호 gm 단계(H1·H3)는 엔진과 교과서가 맞는다**(gm6 1 %). 매크로가 T1 단계 5·7을 함께 푸는 꼴이다.
  - **H2(전류 하한)**: 이 회로는 SR 선언이 없어 효과가 0이다.
  - **H4 L 선택**: 엔진 출발 단계에서 이득 L 하한이 비활성이라 L = LUT 최솟값이다. T8 순서(L을 이득에서 먼저)와 다르다. 이것은 원칙 충돌이 아니라 구현 공백이다(B80 front 0과 같은 계열, LA-1 범위).
  - **H5**: B 밀도는 고리 나머지가 아니라 구간 안 위치 t로 정해졌다.

### 3.2 library 9회로 -- 헤드룸 하한이 어느 소자에 걸리나

`rows.jsonl`의 `lo_src`(gm/ID 하한 출처). `lut_gm_id_range`·`lut_inverse_domain`은 뺐다.

| 회로 | ICMR·스윙 선언 | `headroom_*_6.2` 하한이 걸린 소자(역할) | 꼬리·부하 B의 하한 출처 |
|---|---|---|---|
| nmcnr_amplifier | icmr_v ≥ 0.5, swing ≥ 0.5 | M102·M103(input) | M101(tail_source): `w_min_gm_id`만, t = 0.4 |
| ngcc_3stage_ff | icmr_v ≥ 0.6 | M1·M2(input) | M0(tail_source): `w_min_gm_id`만 |
| sf_pushpull_output_opamp | icm_margin ≥ 0 | M1·M2(input) | M3(tail_source): `w_min_gm_id`만 |
| current_reuse_telescopic_ota | swing ≥ 2.4, icm_margin ≥ 0 | M15·M16·M25·M26(input, vgs·vdsat 둘 다) | 꼬리 M5·M6: `w_min_gm_id`만 |
| two_stage_ota·two_stage_ota_sf·folded_cascode·pushpull·common_gate | 없음 | 없음 | -- |

- **판정: 선언된 헤드룸 고리의 하한은 9회로 모두에서 S(입력) 소자에만 걸렸다. 꼬리 B에는 걸리지 않았다.** 교과서(T1 단계 6, T2 단계 7)는 S를 GB에서 정한 뒤 최소 ICMR로 꼬리 B를 정한다. design 41 §6.2의 '같은 몫' 분할은 그 방향을 담지 못한다.
- 출발 L: 9회로 모두 0.15 µm이다. 예외는 current_reuse M1a·M1b(2.5 µm)와 M4a·M4b(3.2 µm)뿐이다.
- 매크로 비활성 회로(GBW 선언 없음)의 출발 전류: folded_cascode M1 75 pA, pushpull 64~152 pA, common_gate 64~151 pA. 교과서라면 SR(T2 단계 1)이나 rout(T3, pushpull은 `rout_ss_ohm ≤ 1000` 선언)이 전류를 정한다. pushpull은 rout 요구가 있는데도 출발 단계에서 전류로 이어지지 않는다. design 41 E10(rout follower = S)은 층 0 문언에만 있다(LA1C §7 역할표). → R3(§5)의 '소신호 요구 → gm'을 출발 단계에도 걸어야 한다.

### 3.3 실측하지 않은 것

- R5(B가 고리 나머지를 받음)를 엔진 시제품으로 돌려 봉인·front를 재지 않았다. LA1C §7.2의 'W4 고정 −0.18 V → 재배분 +0.063 V'는 W4 축의 결과다. B 나머지 축은 미측정이다.
- B 밀도를 '나머지'(최소 면적)로 바꿨을 때의 면적·이득 변화는 미측정이다.

---

## 4. 손계산 순서 ↔ 엔진 단계 대응

| 교과서 | 엔진 단계 | 지금 | 통합 규칙(§5) |
|---|---|---|---|
| H0 요구 | S0(spec 읽기·구조) | 소신호 요구만 일부(매크로), 정상상태·동적 없음 | R1·R2 |
| H1 보상 C | 출발(§6.5 매크로) | 있음 | R3 |
| H2 전류 하한 | 출발(§6.5 전류) + 층 0 블록 전류(DEC-71 (3)) | 없음(O-122) | R8·R10 |
| H3 신호 gm | 출발(매크로) + 층 0 (a) | 있음. rout follower는 층 0만 | R3 |
| H4 S gm/ID·L → ID | 출발(구간·t) + 층 0 축 | 있음. 출발 이득 L 비활성 | R4 |
| H5 B 나머지 | 없음(§6.2 같은 몫, O-127 (i) 출발·(ii) S 자르기) | 어긋남 | R5·R6 |
| H6 종속 | 쓰기 계획(X), 조립(미러), 영점 R(DEC-92) | 부분. 자기 바이어스 R은 상자 중심(TBA C-2) | R5·R6 |
| H7 검사·반복 | 커널 봉인·제약, 층 0 회차, 외층 | 있음 | R11 |
| H8 SPICE | oracle(front 판정) | 있음. 슬루 FAIL 뒤 처리 없음 | R12 |

---

## 5. §통합 규칙 초안

### 5.0 근본원칙 우선순위 (충돌할 때 위가 이긴다)

| 순위 | 원칙 | 성격 | 근거 |
|---|---|---|---|
| P0 | **물리 정합**: KVL·KCL·영역(포화·전도)·정의 = oracle 정의(같은 SPICE 해석) | 깨면 결과 무의미 | O-30 사용자 원문 "물리적으로 말이 안 되는 … 아무 의미가 없잖아", O-29 (1) |
| P1 | **fail-closed·상수 발명 금지·회로 이름/태그 금지** | 결과 신뢰의 전제 | 사용자 메모리 규칙, WP-01·WP-03 |
| P2 | **정의 하나·writer 하나**(graph 단일 정본) | 일관성 | 프로젝트 CLAUDE.md graph 규칙 1~6 |
| P3 | **교과서 손계산 순서(종속 방향)** | 설계 타당성 | §1, 이번 사용자 지시 |
| P4 | **손계산 속도**(탐색 안에 끝 풀이·Newton 없음) | 엔진 목적 | O-30·O-108·O-109 C1 |
| P5 | **design 단순성** | 유지비 | -- |
| P6 | 기존 사용자 결정 문언 | P0~P5가 요구하면 수정안 + 승인 | 사용자 지시 3 |

- 충돌 예: P3(교과서: SR로 전류)와 P4·P0(엔진 슬루 추정 0.28~28배 부정확, O-122 근거)이 부딪힌다. → 정확해야 하는 판정은 P0에 따라 oracle에 두고, 교과서의 쓰임(전류 출발값)만 P3로 살린다(R10).
- 충돌 예: P2(writer 하나)와 P3(B가 S마다 나머지를 받음)가 부딪힌다. → 블록 하나를 여러 스냅샷에서 부르고 graph reuse로 묶는다. 둘 다 지킨다(R6).

### 5.1 규칙 목록

각 규칙: **정의 / 단계 / writer / SPICE 해석 / 근거**. 회로 이름·새 상수 없음.

**R1 요구는 spec 양이다(회로 무관).**
- 정의: 출력 포트 p·방향 d마다 요구는 셋이다.
  - (a) 소신호 요구: GBW·PM(비주극점)·이득·rout·잡음 → 필요 gm·gds·C.
  - (b) 정상상태 요구 R_ss,d(V): 선언 범위 끝 V에서 응용 망(DEC-100)이 끄는 DC 전류와 그 범위 끝 노드 전압(ICMR·스윙 끝).
  - (c) 동적 요구 R_dyn,d = C_node·SR_req: 속도 선언이 있을 때만 정의된다. C_node = 그 노드 용량(부하 + 보상).
- 단계: S0. writer: spec 해석 블록(기존 `constraint_classes`·spec 필드 -- 새 writer 없음, (c)는 정의만 하고 값은 R10에서 소비).
- SPICE: (a) `.ac`·`.noise`, (b) `.dc`, (c) `.tran`.
- 근거: T1 Page 160-4, T5 p.040-3, SVD §4 D-1, LDA L1′·L2′, O-29 (1).

**R2 능력은 θ 봉인점에서 낸 graph 필드다. 설계점은 하나다.**
- 정의: 설계점 = θ(정지점). 극단 상태는 같은 W·바이어스로 평가한다. 능력 필드는 셋이다.
  - (a) 소신호 필드: gm·gds·C(`ss`).
  - (b) 방향별 공급 능력 I_cap,d(V; θ): 출력 포트를 V에 고정하고 입력을 허용 범위 끝까지 몬 DC 해에서 포트로 내는 **순 전류**.
  - (c) DC 동작 범위(스윙·입력 창 끝).
- 단계: 커널 평가(봉인 뒤). writer: (a) 기존 ss 블록, (b)(c) DE-1 DC 동작 범위 블록 하나.
- SPICE: (a) `.op`+`.ac`, (b)(c) `.dc`.
- 근거: SVD §0-3·§5 (B), LDA L3′·D6 (가), T5 W1 식(극단 상태의 순 전류 = I_cap의 제곱 법칙 손계산), DEC-70.

**R3 소신호 요구 → 신호 gm(출발 단계와 층 0 모두).**
- 정의: 필요 gm은 전달 뷰 극점 망(매크로)의 UGF = GBW, PM ≥ 목표, 전원 전류 최소에서 정한다. rout 요구는 출력 follower의 필요 gm으로 정한다(design 41 E10). 출발 단계에도 같은 정의를 쓴다.
- 단계: 출발(§6.5) → 층 0 (a)가 READS. writer: 매크로 블록 하나(`graph/start: macro`).
- SPICE: `.ac`.
- 근거: T1 단계 5·7, T3 Page 26-25 rout → gm12, §3.1(gm6 1 %), §3.2(rout 요구 회로의 출발 전류 pA).

**R4 S 소자: gm/ID·L은 독립, ID = 필요 gm/(gm/ID).**
- 정의: S의 gm/ID는 [헤드룸·속도·가드 구간] 안의 독립 좌표다. L은 이득 요구에서 정한다(bin 안 역산, LR3). ID = max(gm_req/(gm/ID), R8 하한). R8 하한이 이기면 gm/ID 정의역 상한이 gm_req/I_min으로 잘린다(전류 하한을 gm/ID 상한으로 바꾼 같은 사실).
- 단계: 출발(구간·출발값) → 층 0(축). writer: 출발 구간 블록(구간), 층 0 블록(후보값).
- SPICE: `.op`.
- 근거: T7 단계 1~5, T6, L-11 앞 문장, DEC-71 (4)(a)(b), T8 §6.4(SR이 gm/ID를 제한 -- 식 (6.74) SR = 2·ID1/CC).

**R5 KVL 고리마다 종속 성분 하나 -- 구조 순위로 고른다.**
- 정의: R-1′ 제약 그래프의 고리(등식 고리와 포화 부등식 고리)마다 종속 성분은 구성원 중 아래 순위가 가장 앞인 하나다.
  1. X(쓰기 계획 종속, 등식 고리).
  2. 값 미선언 DC 경로 저항의 강하 V_R. R = V_R/I_R은 파생이다. I_R ≡ 0이면 DC θ가 아니다(TBA R-P3).
  3. B 소자 밀도(ln IDu). L 동치류 주인이 S·F이면 그 L은 B의 좌표로 세지 않는다(TBA R-P2).
  4. W4 자유 노드전압(y).
  5. F 소자 밀도.
  6. S 소자 밀도·θ 전류. 이 둘은 전류(전력)를 정하는 좌표라 마지막이다. 값이 선언된 저항에 흐르는 θ 전류도 여기 든다(U-new1).
- (a) 종속 성분은 고리의 다른 구성원이 다 정해지는 **가장 이른 단계**에서 파생한다.
- (b) 부등식 고리에서 종속의 값은 '고리 나머지'다. 범위가 선언된 고리는 범위 끝에서, 아니면 동작점에서 VDS ≥ VDsat + tol(`sat_threshold`)을 만족하는 값 가운데 R7의 선택 규칙을 따른다.
- (c) 고리 구성원이 S·F·θ 전류뿐이면(종속 후보 1~4 없음) 그 고리는 S·F 축의 정의역 제약이다. 좌표가 하나면 정의역을 자르고(HC N3.1-5), 여럿이면 층 0 후보를 거른다.
- (d) 한 성분이 여러 고리의 종속이면 가장 엄한 값(최댓값)을 쓴다. 그래도 남는 위반은 fail-closed(R11).
- 단계: S0에서 고리마다 종속 성분과 그 처리 단계를 한 번 정한다. 값은 R6에서 정한다. writer: R-1′ 제약 그래프 블록(HC-1)이 변 속성으로 쓴다(TBA §5 권고 (가) -- 분류 필드는 R13).
- SPICE: `.op`(포화 정의 = oracle `vds_ge_vdsat`).
- 근거: T1 단계 6(S5 ← β1), T2 단계 5·7·8, T8 Ex. 6.4·p.271, DEC-95 (3)(S 독립), HC N3.1-3(DEC-95 순서로 조정 소자), O-127 원칙 문장('종속 성분 제거 기저').

**R6 종속 성분 값의 writer는 블록 하나다(고리 종속 블록).**
- 정의: '고리 종속 블록' 하나가 R5의 종속 성분 값(B ln IDu, V_R, 해당 W4)을 쓴다.
  - 그 블록은 출발 단계 스냅샷과 층 0 후보 스냅샷에서 같은 블록으로 불린다.
  - 구성원이 모두 출발 단계에서 정해지는 고리(B·X·R만)는 입력 버전이 같아 graph reuse로 한 번만 계산된다.
  - S·F가 섞인 고리는 후보마다 다시 계산된다.
- 이 값은 θ의 독립 성분이 아니다. 외층·수리·Halton·상자 중심 경로도 이 값을 바꾸지 않는다. 그 경로들은 독립 성분만 움직이고, 종속 성분은 같은 블록이 다시 파생한다.
- 단계: 출발·층 0·외층(파생 호출). writer: 고리 종속 블록 하나(sizing 층, 쓰기 계획 다음).
- SPICE: -- (DC 파생).
- 근거: P2(writer 하나), 스냅샷 파생 규칙(CLAUDE.md graph 5), TBA W-1·W-2·W-3·W-5, LA1C §7.2(S가 움직이면 고리가 깨지고 재파생하면 회복).

**R7 B 밀도의 선택 규칙.**
- 정의: B 밀도는 다음 순서로 정한다.
  - (a) 고리 종속이면 R5 (b)의 나머지 구간 안에 있어야 한다.
  - (b) 그 구간과 matching·잡음·offset 가드(design 41 §6.4-2a·§7.5) 구간의 교집합 안에서 고른다. 범위가 선언된 고리는 **나머지 끝**(면적 최소 = 교과서 T1 단계 3·6, T2 단계 3·4·7)을 고른다. 범위가 선언되지 않은 고리는 지금 출발 선택점(구간 위치 t)을 유지한다.
  - (c) 교집합이 비면 fail-closed 충돌 기록이다.
- 단계: R6 블록 안. writer: R6과 같다.
- SPICE: `.op`.
- 근거: T1·T2(나머지), T6·T8(가드), 상수 0. 미선언 고리에서 나머지(면적 최소)로 바꿀지는 미측정이라 기본안에 넣지 않았다(Q6).

**R8 정상상태 요구 → 전류 하한과 범위 끝 고리.**
- 정의: 범위 끝 V에서 I_cap,d(V; θ) ≥ R_ss,d(V)는 θ 제약이다(DEC-70 자리).
  - 출발·층 0에서는 레일에 source가 붙은 공급 셀 전류 ≥ R_ss를 정확한 필요조건으로 블록 전류 하한에 건다(DEC-71 (3) '선언' 자리).
  - 범위 끝 헤드룸 고리는 R5와 **같은 R-1′ 고리**다. 평가점만 다르다. 동작점 대신 범위 끝 노드 전압과 그 상태의 소자 전류(I_β(V_end) ± 부하 전류)로 평가한다. 새 고리 집합을 만들지 않는다.
- 단계: S0(요구) / 출발·층 0(하한) / 커널(판정). writer: 요구 = spec, 능력 = DE-1 블록, 하한 = 출발 구간 블록.
- SPICE: `.dc`.
- 근거: T5 p.040-3, LDA L1′·L3′·L4′, SVD D-3.

**R9 극단 상태 평가 계산법(정의는 R2, 계산법은 둘).**
- 정의:
  - 작은 편차(헤드룸·포화 여유·창 끝)는 W·바이어스 고정 KCL 선형 감도 끝으로 계산한다(DE-1, DEC-103).
  - 큰 편차(방향별 피크 공급 능력)는 같은 W에서 그 소자의 LUT를 극단 단자 전압으로 조회한다. 극단 단자 전압은 V_GS = 구동단 DC 범위 끝(DE-1 READS), V_DS = 출력 범위 끝이다. 그 값에서 반대쪽 가지 전류를 뺀 순 전류를 쓴다.
  - 회로 전체 끝 풀이(Newton)는 두지 않는다. 구조 분류(class-A/AB)는 값 규칙을 가르지 않는다(DEC-65).
- 단계: 커널(봉인 뒤). writer: DE-1 블록 하나.
- SPICE: `.dc`(정확값 oracle).
- 근거: SVD §4 D-5·§5(class-AB 피크/정지 19~658배), T5 W1 식, O-109 C1, U-115 후보 (라)(이 감사의 신규 후보).

**R10 동적 요구는 판정하지 않고, 출발 전류값과 oracle 되먹임으로만 쓴다.**
- 정의:
  - (a) 출발 단계: 동적 요구가 선언된 노드의 공급 가지 전류 출발값 ≥ R_dyn('추정' 표기). 거부에는 쓰지 않는다.
  - (b) 판정은 oracle `.tran`(전 폭 계단, 20-80 % 기울기, O-121 B-2)뿐이다.
  - (c) oracle FAIL이면 그 점의 '측정 SR 대 요구 SR 비'를 근거로 R_dyn 노드 공급 가지의 θ 전류 하한을 올린다. 그 뒤 층 0 회차(L-3 넷째 반복 자리)를 다시 돈다. 상한 = K_max, 넘으면 fail-closed 기록.
  - (d) 사용자가 손계산한 피크 몫을 선언하면(`load_peak_amp` 재정의) R8 요구에 더한다.
- 단계: 출발((a)) / oracle((b)) / 층 0 회차((c)). writer: (a) 출발 구간 블록, (c) oracle 판정 기록 → θ 하한 필드(EO-1 판정 배선 생산자가 쓰는 판정 기록을 읽는다 -- 새 사본 없음).
- SPICE: `.tran`.
- 근거: T1 단계 2, T2 단계 1, T3·T4, T8 §6.4.2 단계 1·11, Boser 절차(SVD §1.1 'verify with a full-scale input step … Iterate'), O-122 근거(엔진 추정 0.28~28배 -- 그래서 판정에는 쓰지 않음), U-112.
- 주의:
  - (c)의 '비 = 전류 비'는 슬루가 전류에 비례하는 노드에서만 맞는 필요조건이다. 계단 크기에 비례하는 출력(class-AB, O-119 정정 2 주석)에서는 비가 맞지 않는다. 그래서 (c)는 '하한 올림 후보'이고 재판정은 다시 oracle이 한다(물리 정합: 판정은 언제나 oracle).
  - library SR 선언이 0이라 지금 효과는 0이다.

**R11 검사·반복 자리.**
- 정의: 커널 봉인(포화·KVL·KCL·VGS) → 제약(소신호·DC 범위) → 층 0 회차 → 외층(선택)의 순서다. 위반 후보는 margin과 함께 버린다. 다음 후보로 간다.
- 단계: 커널·층 0·외층. writer: 기존.
- SPICE: `.op`·`.ac`·`.dc`.
- 근거: T1 단계 10·11, DEC-70·DEC-73, O-127 (iv).

**R12 정확값은 oracle이 확정한다.**
- 정의: front 후보·최종점만 SPICE로 잰다. 엔진 값과의 차는 모델 오차(DEC-72)로 기록한다. 탐색 안에서는 무거운 계산을 하지 않는다.
- 단계: oracle(front 판정). writer: EO-1 생산자.
- SPICE: 정의 그대로.
- 근거: O-30·O-32·O-108, T1 단계 12, T8 단계 14.

**R13 S/B/F/X 분류는 S0 필드 하나다.**
- 정의:
  - S = 필요 gm이 R3으로 정의된 신호 소자(매크로 활성 input, rout follower).
  - F = 그 밖 신호 소자.
  - B = 부하·미러·바이어스·FF.
  - X = 쓰기 계획 종속.
  - 입력은 S1v `Block.roles`, `device.dc_coord`, spec(GBW·rout), L 동치류다. topology 태그는 쓰지 않는다.
- 단계: S0. writer: 분류 블록 하나(새 S0 필드 -- **계획에 정본 자리가 없다. 계획 개정 대상, S-7**).
- SPICE: --.
- 근거: TBA §5 (가), design 41 §5.3.3 표, L-11.

**R14 정의와 계산법 분리, DC/AC 분리(유지).**
- 정의: metric 규칙에는 정의(SPICE 해석 종류)만 둔다. 손계산은 계산법이고 정확도를 표기한다. DC 양은 DC 풀이로, AC 양은 봉인 DC 점의 소신호로 계산한다.
- 근거: O-29·O-31, DEC-67, O-23. 유지 근거: 교과서도 같은 점에서 DC(헤드룸) → AC(gm)를 계산한다(T1 단계 3~8).

### 5.2 단계 × writer 표 (같은 양은 writer 하나)

| 양 | 정의 | 단계 | writer | 읽는 곳 |
|---|---|---|---|---|
| 소신호 요구(GBW·PM·rout·이득) | R1 (a) | S0 | spec | 매크로, 층 0, 커널 |
| 정상상태 요구 R_ss,d(V) | R1 (b) | S0 | spec(값) + DE-1 정의식(응용 망 풀이는 R2 블록이 아니라 요구 쪽 -- design이 정함, 미결) | R8 |
| 동적 요구 R_dyn | R1 (c) | S0 | spec | R10 |
| 보상 C 출발값·필요 gm | R3 | 출발 | 매크로 블록 | 층 0 |
| S gm/ID·L 구간 | R4 | 출발 | 출발 구간 블록 | 층 0 |
| S gm/ID·L 후보값 | R4 | 층 0 | 층 0 블록 | 커널 |
| 고리 종속 판정(어느 성분이 종속, 처리 단계) | R5 | S0 | R-1′ 제약 그래프 블록 | R6 |
| 종속 성분 값(B ln IDu, V_R, 종속 W4) | R5·R6·R7 | 출발·층 0·외층(파생) | **고리 종속 블록 하나** | 커널 |
| S/B/F/X 분류 | R13 | S0 | 분류 블록(신설, 계획 자리 없음) | R5·R6·층 0 |
| 전류 하한(정상상태·동적 출발값) | R8·R10 (a) | 출발·층 0 | 출발 구간 블록 | 층 0 |
| 공급 능력 I_cap,d(V)·DC 동작 범위 | R2 (b)(c)·R9 | 커널 | DE-1 블록 | 제약 판정 |
| 슬루 판정 | R10 (b) | oracle | EO-1 판정 기록 | R10 (c) |

---

## 6. 세 가지 사이의 충돌과 일관 규칙안

| # | 충돌 | 일관 규칙안 | 대안 |
|---|---|---|---|
| K1 | 교과서는 SR로 I5를 정한다(T1 단계 2). O-122는 엔진이 슬루에 관여하지 않는다 | **R10**: 판정은 oracle만(O-122 유지), 동적 요구는 출발 전류값('추정')과 oracle FAIL 되먹임으로만 쓴다. D1 (나)(사용자 피크 선언)는 R10 (d)로 같이 둔다 | 표 K1 |
| K2 | 교과서는 S가 섞인 ICMR 고리에서 B 크기를 정한다. O-127 (ii)는 B를 고정하고 S를 자른다. L-11은 B를 §6 구간으로만 정한다 | **R5·R6·R7**: 종속 = 구조 순위(B가 S보다 앞), 층 0 후보마다 같은 블록이 파생 | 표 K2 |
| K3 | 정상상태 요구(범위 끝)와 손계산 헤드룸 고리가 같은 고리인가 | **같은 R-1′ 고리다. 평가점이 다르다**(R8). 범위 끝 노드 전압 + 그 상태의 소자 전류로 같은 변을 평가한다. 교과서 T1 단계 3·6은 범위 끝(Vin(max)·Vin(min))에서 고리를 평가한 것이다 | 고리 집합을 둘로 두는 안 -- ⚠ 원칙 경고: graph 규칙 1·3 — 같은 KVL 사실을 두 곳에서 생산 — CLAUDE.md, TBA §0-5 |
| K4 | 공급 능력 정의(범위 끝 + 순 전류)와 Allen L040 W1(극단 상태)은 같은 양인가 | **같은 양이다.** T5의 "W1/L1 = 2(I_OUT⁻ + I_Q)/[K'(VDD+\|VSS\|−VTN)²]"는 '게이트를 레일까지 몬 M1 전류 − I_Q ≥ I_OUT⁻'의 제곱 법칙 손계산이다. 이것이 R2 (b) I_cap의 계산법(R9 큰 편차 꼴)이다. 차이는 하나다: T5는 출력 끝에서도 M1 포화를 가정한다. R2 정의는 범위 끝에서 triode로 들어가면 그만큼 작게 잰다. 정의가 더 엄하고 손계산은 그 근사다 | -- |
| K5 | O-127 (i) 'B writer = 출발 단계 하나'와 DEC-73 (3) 수리·L-11 외층 | **R6**: 종속 값은 한 블록이 파생, 수리·외층은 독립 좌표만 | TBA W-1·W-2 대안 그대로 |
| K6 | O-127 (iii) 'V_R 결정 변수'와 교과서 'R = VDsat/I'(V_R은 B 밀도의 종속) | **R5 순위**: V_R이 B보다 앞의 종속이다. B만 남은 고리(자기 바이어스 캐스코드 바이어스)에서는 V_R이 고리 나머지를 받고, B 밀도는 R7 가드·출발값이 된다. 두 축을 다 자유로 두지 않는다(B81 R1a 1.5 % 얇은 영역 해소) | 교과서처럼 V_R을 B 밀도의 종속(V_R = VDsat)으로만 -- 자기 바이어스 R이 정확히 VDsat 강하인 회로에서만 맞고, 일반형(저항이 다른 강하를 맡는 회로)에서는 틀림 |
| K7 | DEC-103 'KCL 선형화'와 큰 편차(class-AB 피크) | **R9**: 같은 틀(W 고정), 계산법 둘(작은 편차 선형, 큰 편차 소자 LUT 극단 조회) | 선형만 -- ⚠ 원칙 경고: 물리 정합 — 19~658배 편차를 선형 감도로 외삽 — SVD §5 |
| K8 | 출발 단계 '구간 최댓값'(B 포함)과 교과서 '부하 강반전·나머지' | **R7**: B는 가드 교집합 + 선언 고리 나머지 끝, 미선언은 현행 유지 | 표 K2 (다) |

### 6.1 대안표 K1 -- 동적 요구(SR)

| 칸 | (가) R10: 판정 oracle + 출발 전류값 + FAIL 되먹임 (권고) | (나) 현행 O-122: 엔진 0, oracle 판정만 | (다) O-121 B-1 (나′) 부활: 엔진 출력 노드 전류 하한으로 거부 | (라) D1 (나)만: 사용자 피크 선언만 |
|---|---|---|---|---|
| 물리 정합 | 판정은 정의 그대로(oracle). 출발값은 필요조건 I ≥ C·SR(노드 C가 알려진 곳에서 정확) | 정의 그대로. FAIL 뒤 전류를 올릴 길이 없어 SR spec 회로는 front가 빌 수 있음(U-112 미정의) | 능력 추정이 상한이 아님(내부 β 1.19배·CLM 1.6~4.7배, O-122 근거) → 거짓 거부 위험 | 사용자 계산 정확도에 따름 |
| 손계산 일치 | T1 단계 2·T8 단계 11(반복)과 같음 | 다름(단계 2 없음) | 같음 | 부분 |
| design 단순성 | 중간(출발 하한 1줄 + FAIL 되먹임 자리 -- 넷째 반복 자리 재사용) | 높음 | 낮음(O-122가 지운 필드 부활) | 중간 |
| 실측 | library SR 선언 0 → 효과 0. heldout은 쓰지 않음 | 효과 0 | 60점 자른 점 0~12 %(O-121) | 0 |
| 원칙 | ⚠ 원칙 경고: O-122 — '엔진은 슬루에 관여하지 않는다'에 출발값·되먹임이 걸린다 — UD 849행. **원래 취지와 다름(사용자 승인 필요)**. 판정을 oracle에 두는 O-122의 근거(추정 부정확)는 지킨다 | ⚠ 원칙 경고: 교과서 손계산 순서(P3) — 전류 하한 단계가 없고 FAIL 뒤 처리가 없다 — T1 Page 160-5 단계 2, PL 2268 U-112 | ⚠ 원칙 경고: 물리 정합(P0) — 상한이 증명되지 않은 추정으로 거부 — O-122 근거, UD 849 | 정합 |

### 6.2 대안표 K2 -- S가 섞인 헤드룸 고리

| 칸 | (가) R5·R6: 종속 = 구조 순위, B가 층 0 후보마다 나머지를 받음(같은 블록) (권고) | (나) 현행 O-127 (ii): B 고정, S 정의역 자르기·W4 재배분 | (다) B를 층 0 격자 축으로(B도 탐색) |
|---|---|---|---|
| 물리 정합 | KVL·포화 정합. B 밀도는 전력에 중립이라 나머지를 받아도 전력 최적점이 바뀌지 않음 | 정합. 다만 S 정의역을 잘라 전력 최적 gm/ID를 잃을 수 있음(미측정) | 정합 |
| 손계산 일치 | T1 단계 6, T2 단계 7·8과 같음 | 반대 방향(B → S) | 다름(B를 최적화 축으로 두는 교과서 없음 -- T6·T8은 고정 선택) |
| design 단순성 | 중간(종속 블록 하나, 출발·층 0 공용, graph reuse) | 중간(정의역 자르기·거르기 두 갈래) | 낮음(Π 증가, L-11 '격자 곱 제외' 깨짐) |
| 실측 | W4 재배분은 LA1C §7.2에서 회복(+9 mV 이상). B 나머지 축은 미측정 | LA1C §7.4 nmcnr 봉인(정의역 자르기), two_stage W4 고정 −0.18 V | 미측정 |
| 원칙 | P2 지킴(writer 하나), DEC-95 (3)와 같은 방향. **원래 취지와 다름(사용자 승인 필요)**: O-127 (i) 'B writer = 출발 단계'·(ii) 문언 변경 | ⚠ 원칙 경고: 교과서 손계산 순서(P3) — 종속 방향 반대, DEC-95 (3)('GB5가 gm을 요구하는 소자 독립 유지')와 어긋남 — T1 Page 160-6 단계 6, PL 294 | ⚠ 원칙 경고: L-11 — B를 격자 곱에 넣음 — UD 229 / ⚠ 원칙 경고: 손계산 속도(P4) — 축 수 증가 |

---

## 7. 수정되는 기존 원칙 표

각 행: (a) 기존 문언·출처 / (b) 수정 문언 / (c) 근거 / (d) 승인 표시 / (e) 수정하지 않을 때의 대안과 ⚠.

### M1 O-127 (i) -- B 밀도 writer
- (a) UD 881행: "(i) B·종속(X) 소자만의 고리: 출발 단계가 B 밀도를 사슬 정합으로 맞춘다(B 밀도 writer = 출발 단계 하나, 층 0은 READS)".
- (b) "(i) 고리의 종속 성분(R5 순위: X > 값 미선언 저항 강하 > B 밀도 > W4 > F > S·θ 전류)은 고리 종속 블록 하나가 파생한다. 그 블록은 출발 단계와 층 0 후보 스냅샷에서 같은 블록으로 불린다. 구성원이 모두 출발 단계에서 정해지는 고리는 graph reuse로 한 번 계산된다. 수리·외층·상자 중심·Halton 경로는 종속 성분을 바꾸지 않는다."
- (c) 물리: B 밀도는 전류를 정하지 않으므로 고리 나머지를 받아도 전력 최적이 그대로다. 교과서: T1 단계 3·6, T2 단계 3·4·7·8. 실측: LA1C §7.3(sf B만 고리 출발 맞춤으로 봉인), §7.2(S가 움직이면 고리가 깨짐), TBA W-1·W-2(writer 셋).
- (d) **원래 취지와 다름(사용자 승인 필요)**: 'B writer = 출발 단계'를 'B writer = 고리 종속 블록(출발·층 0 공용)'으로.
- (e) 유지 시: ⚠ 원칙 경고: graph 단일 정본(P2) — 수리(DEC-73 (3))·외층(L-11)이 B를 바꾸면 writer 셋 — TBA W-1·W-2, PL 272, design 41 925행.

### M2 O-127 (ii)·(iii) -- S가 섞인 고리·V_R
- (a) UD 881행: "(ii) 층 0 결정 변수가 섞인 고리: 층 0 후보마다 판정, 좌표 하나면 그 축 정의역 자르기, 여럿이면 W4·V_R 재배분 뒤 거르기 (iii) 값 미선언 DC 경로 저항은 강하 V_R 이 결정 변수, R = V_R/I_R 파생".
- (b) "(ii) 층 0 결정 변수(S·F 밀도, L, θ 전류)가 섞인 고리는 층 0 후보마다 다시 파생한다. 종속 성분이 저항 강하·B 밀도·W4 중 하나면 그 값을 고리 나머지로 정한다(R7 가드와 교집합, 여러 고리면 최댓값). 종속 후보가 S·F·θ 전류뿐이면 그 축의 정의역 제약이다: 좌표 하나면 자르고, 여럿이면 거른다. (iii) 값 미선언 DC 경로 저항의 강하 V_R은 고리 종속 성분(순위 2)이고, R = V_R/I_R은 파생이다. 구조적으로 DC 전류가 0인 저항은 DC θ가 아니다. 값이 선언된 저항을 지나는 θ 전류는 종속이 되지 않는다(순위 6). 그 고리의 종속은 다른 구성원에서 고른다."
- (c) 교과서: T1 단계 6("VDS5(sat) = Vin(min) − VSS − √(I5/β1) − VT1"), T2 단계 5·7. 계획: DEC-95 (3)·HC N3.1-3(S 독립). 실측: §3.2(헤드룸 하한이 S에만 걸림), LA1C §7.2.
- (d) **원래 취지와 다름(사용자 승인 필요)**: S 정의역 자르기를 '종속 후보가 S·F뿐일 때'로 좁히고, V_R을 결정 변수에서 고리 종속으로 바꿈.
- (e) 유지 시: ⚠ 원칙 경고: 교과서 손계산 순서(P3) — B 고정·S 자르기는 종속 방향 반대, 전력 최적 gm/ID 손실 가능 — T1 Page 160-6, PL 294 DEC-95 (3).

### M3 L-11 -- B 정하는 법
- (a) UD 229행: "부하·미러·바이어스는 §6 구간·미러비·KCL 로 정하고 격자 곱에서 제외" + design 41 925행 "§6 출발값 … 을 쓰고, 외층 SLSQP가 다듬는다".
- (b) "부하·미러·바이어스(B)는 어느 층에서도 독립 변수가 아니다. 고리 종속이면 고리 나머지(R5·R6), 아니면 §6 가드 구간의 선택점·미러 비·KCL로 정하고 격자 곱에서 제외한다. 외층은 독립 성분만 움직이고 B는 같은 블록이 다시 파생한다."
- (c) T6·T7(S만 gm에서), T1·T2(B = 나머지), TBA W-2.
- (d) **원래 취지와 다름(사용자 승인 필요)**: '외층 SLSQP가 다듬는다' 삭제(외층 탐색 공간에서 B 축이 빠짐 -- front 영향 미측정).
- (e) 유지 시: ⚠ 원칙 경고: graph 단일 정본(P2) — 외층이 B의 셋째 writer — design 41 925행.

### M4 O-122 -- 슬루
- (a) UD 849행: "슬루 판정과 탐색 모두 oracle `.tran`(전 폭 계단, 20-80 % 기울기)만 쓴다. 엔진은 슬루에 관여하지 않는다."
- (b) "슬루 판정은 oracle `.tran`(전 폭 계단, 20-80 % 기울기)만 한다. 엔진은 슬루율을 추정하거나 그것으로 거부하지 않는다. 다만 (a) 동적 요구 R_dyn = C_node·SR_req를 출발 단계 공급 가지 전류의 출발 하한('추정')으로 쓰고, (b) oracle FAIL 점의 측정 SR 대 요구 SR 비로 그 가지 θ 전류 하한을 올려 층 0 회차를 다시 돈다(상한 K_max, 넘으면 fail-closed 기록, 재판정은 oracle)."
- (c) 교과서: T1 단계 2, T2 단계 1, T3·T4, T8 §6.4.2 단계 1·11. 물리: I ≥ C·dV/dt는 노드 C가 알려진 곳의 정확한 필요조건이다. 판정을 oracle에 두는 것은 O-122 근거(추정 0.28~28배) 그대로다. U-112(FAIL 뒤 처리 미정의)를 닫는다.
- (d) **원래 취지와 다름(사용자 승인 필요)**.
- (e) 유지 시: ⚠ 원칙 경고: 교과서 손계산 순서(P3) — 전류 하한 단계가 없고, SR 선언 회로에서 FAIL 뒤 전류를 올릴 경로가 없다 — T1 Page 160-5, PL 2268 U-112.

### M5 O-26 (1)·DEC-65 -- 공급 능력 정의
- (a) UD 645행·PL 264행: "노드 k를 동작점 전압에 고정하고 입력 … 을 허용 입력 범위(레일 범위) 끝까지 몬 DC 해에서 k로 드는 그 방향 전류".
- (b) "출력 포트 p를 선언 범위 끝 전압 V에 고정하고 입력을 허용 범위 끝까지 몬 DUT ⊕ 응용 망 DC 해에서, p를 V에 고정하는 원천이 내보내는(받는) 순 전류 I_cap,d(V). 계산법은 R9(작은 편차 KCL 선형, 큰 편차 같은 W의 소자 LUT 극단 조회 − 반대 가지)."
- (c) T5 p.040-3("Maximum sinking current = K'W/2L(…)² − I_Q"), LDA F1·F2·D6 (가), SVD §4.
- (d) **원래 취지와 다름(사용자 승인 필요)**(LDA D6과 같은 결정).
- (e) 유지 시: ⚠ 원칙 경고: 물리 정합(P0) — 요구(범위 끝)와 능력(동작점)을 다른 전압에서 비교하고 총 전류를 순 전류로 씀 — T5, LDA §0-2.

### M6 DEC-103 -- 계산법 보강
- (a) PL 302행: "이미 정해진 회로를 흔들 때의 반응(ICMR 창·감도·스윙·섭동)은 W·바이어스 전압을 고정한 KCL 선형화".
- (b) 같은 문장 뒤에 덧붙인다: "소자 전류가 동작점에서 크게 벗어나는 반응(방향별 피크 공급 능력)은 같은 W·바이어스에서 그 소자의 LUT를 극단 단자 전압으로 조회한다. 회로 전체 끝 풀이는 두지 않는다."
- (c) SVD §5(class-AB 피크/정지 19~658배), O-109 C1(끝 풀이 금지 유지).
- (d) **원래 취지와 다름(사용자 승인 필요)** -- 틀(W 고정)은 같고 계산법만 넓힌다(작음).
- (e) 유지 시: ⚠ 원칙 경고: 물리 정합(P0) — 큰 편차를 선형 감도로 외삽 — SVD §5.

### M7 계획 N1.1 결정 순서
- (a) PL 138행: "signal stage 유도 -> 보상 -> gain 할당(gm_id·L) ⇄ 노드전압 DC 해석 -> 전체회로 판정".
- (b) "요구 정의(소신호·정상상태·동적) -> signal stage 유도 -> 보상 -> 전류 하한 -> 신호 gm -> gain 할당(S gm_id·L) ⇄ 고리 종속 파생(B·저항 강하·W4) -> 전체회로 판정 -> oracle 확정".
- (c) §1.6 공통 골격.
- (d) 계획 문언 변경(목적 절) -- 승인 필요(취지는 같음).
- (e) 유지 시: ⚠ 원칙 경고: 교과서 손계산 순서(P3) — 전류 하한·B 나머지 단계 누락 — §2 17행.

### M8 DEC-71 (3)·(4)(c)
- (a) PL 270행: "블록 전류(KCL·선언 -- '슬루 하한'은 v6.37 O-122로 없음)", "(c) VDS 배분 = 전 소자를 포화 여유 하한(VDsat)으로 채운 뒤 남은 헤드룸을 … ∂(gm/gds)/∂VDS가 큰 소자부터 배분".
- (b) "블록 전류(KCL·선언·R8 정상상태 하한·R10 (a) 동적 출발 하한)". "(c) 후보마다 고리 종속 블록이 종속 성분(B 밀도·저항 강하·종속 W4)을 파생한 뒤, 남은 W4 여유를 ∂(gm/gds)/∂VDS가 큰 소자부터 배분".
- (c) T1 단계 6, LDA §7.1-7.
- (d) **원래 취지와 다름(사용자 승인 필요)**('슬루 하한 없음' 문언 개정은 M4에 종속).
- (e) 유지 시: ⚠ 원칙 경고: P3 — B 고정 VDS 배분은 나머지 규칙과 다름 — T1.

### M9 DEC-73 (3) 수리
- (a) PL 272행: "수리 = `_repair`만 … 실패 노드 writer 소자 하나의 ln IDu 한 축 이분법".
- (b) "수리 후보 좌표는 독립 성분(S·F 밀도, θ 전류, L)만이다. 종속 성분은 고리 종속 블록이 다시 파생한다. 실패 writer가 종속 성분뿐이면 탈락 기록."
- (c) TBA W-1 (가).
- (d) **원래 취지와 다름(사용자 승인 필요)**(O-36 (4)·O-37 범위 축소).
- (e) 유지 시: ⚠ 원칙 경고: P2 — 수리가 B writer 둘째 — PL 272.

### M10 design 41 §6.2·§6.1-7·§6.7 원리(계획 승인 뒤 design)
- (a) 41 1526~1556행(같은 몫 분할), 1512행 '구간 최댓값', 1675행 '노드 전압을 먼저 배분하고 gm/ID 를 역산하지 않는다'.
- (b) §6.2: 헤드룸 하한은 고리 종속이 아닌 S·F의 정의역 제약으로만 쓰고, 고리 종속 성분은 R5·R6로 정한다. §6.1-7: 'S·F 출발값은 구간 최댓값, B는 R7'. §6.7 원리: 'S·F에 대해' 한정.
- (c) §3.2 실측, T1.
- (d) design 정정(계획 우선 -- M1·M2·M3 승인 뒤).
- (e) 유지 시: ⚠ 원칙 경고: P3 — 헤드룸 하한이 S에만 걸림 — §3.2.

### M11 DEC-70 θ 정의
- (a) PL 269행: θ = "셀별 반전 좌표 ln IDu …, L 동치류 L, 결합변수 y …, W4 자유 노드전압, θ 전류 변수 …, DC 전류 경로에 있는 값 미선언 저항 값".
- (b) "θ의 독립 성분 = S·F 셀의 ln IDu, L 동치류 L, 결합변수 y 가운데 고리 종속이 아닌 것, θ 전류 변수. 고리 종속 성분(B ln IDu, 값 미선언 DC 경로 저항의 강하 V_R, 종속 W4)은 θ에 들지 않고 고리 종속 블록이 파생한다. 값 미선언 저항 값 R = V_R/I_R(파생)."
- (c) O-127 원칙 문장('θ 의 독립 성분은 … 종속 성분을 제거한 기저'), TBA W-4 (가), B81 R1a 1.5 % 얇은 영역.
- (d) **원래 취지와 다름(사용자 승인 필요)**: θ 스키마 변경(외층 SLSQP 변수 변경 -- 척도·front 영향 미측정).
- (e) 유지 시(층 0만 V_R, TBA W-4 (나)): ⚠ 원칙 경고: θ 기저(O-127) — 외층 θ에 R·I 두 독립 축이 한 부등식에 남음 — TBA W-4.

### 유지되는 원칙 (한 줄 근거)

| 원칙 | 유지 근거 |
|---|---|
| O-115 ICMR 정의(servo) | 정의(무엇을 재나)이고 사이징 순서와 무관. 사이징 쪽은 범위 끝을 R5·R8 고리 폭으로 쓴다 |
| O-119 입력 범위 이름 분리 | 교과서 ICMR·Vout range와 같은 양 |
| O-29~O-31 정의·계산법 분리, 손계산 기본·층 배치 | 교과서 손계산 → SPICE와 같음 |
| DC/AC 분리(DEC-67·O-23) | 교과서도 같은 점에서 DC → AC |
| DEC-70 '제약으로만 되돌아감' | T1 단계 11·T8 단계 11의 반복 조정과 같은 꼴(θ 정의 부분만 M11) |
| DEC-71 (4)(a)(b) 역산 우선 | T7 단계 1~4 그대로 |
| DEC-95 (3) 종속 선택 순서 | S 독립 = 교과서 종속 방향. R5 순위의 기존 근거 |
| HC R-1′(제약 그래프·Bellman–Ford·조정 소자 순서) | R5의 고리 정본 자리. 순서가 DEC-95 (3) |
| HC-S `sat_threshold` | 포화 정의 하나 = oracle `vds_ge_vdsat` |
| O-127 (iv) fail-closed | 교과서 검사 단계와 같음 |
| O-125·O-126 card 순서 | 엔진 규칙이 아니라 작업 순서. LA-1 design이 R5·R6을 담으면 됨 |
| §6.5 매크로 | 실측 gm6 1 %(§3.1) |

---

## 8. 사용자 승인 목록 (열린 결정 대체)

| Q | 결정 | 권고 | ⚠ | 대체하는 열린 결정 |
|---|---|---|---|---|
| Q1 | 원칙 우선순위 P0~P6(§5.0) 채택 | 채택 | -- | (신규) |
| Q2 | R5 종속 순위 + R6 고리 종속 블록 하나(M1·M2·M3·M9·M11) | 채택 | 원래 취지와 다름(O-127 (i)(ii)(iii), L-11, DEC-73 (3)·O-36 (4), DEC-70) | TBA W-1·W-2·W-3·W-5(종속은 언제나 블록이 파생 → 상자 중심은 독립 성분에만), W-4(V_R = 고리 종속 → θ 밖), U-new1(선언 R 경유 θ 전류 = 순위 6, 종속 아님) |
| Q3 | R10 동적 요구(M4) | (가) 출발 하한 + oracle FAIL 되먹임 | 원래 취지와 다름(O-122) | LDA D1 → (가)에 (나)를 함께(R10 (d)), D3 → (나)(`load_peak_amp` = 사용자 대신호 몫, 방향별), U-112 FAIL 뒤 처리 |
| Q4 | R2·R8·R9 공급 능력·정상상태 요구(M5·M6) | 채택 | 원래 취지와 다름(O-26 (1)·DEC-65, DEC-103 계산법) | LDA D6 → (가), U-115 → 후보 (라) 'R9: 같은 W 소자 LUT 극단 조회 − 반대 가지'(O-123 보류를 이 결정으로 닫을지 사용자 판단 -- DE-1 착수 조건 (iii)) |
| Q5 | 범위 위치·선언 정리 | LDA 권고 그대로 | -- | D2 → (가) 절대 범위 선언(미선언이면 R_ss 미측정, fail-closed), D4 → (가) `load_dc_amp` 삭제, D5 → (다) AP-1까지 fail-closed, D7 → (가) `constraints[]` `.tran` metric |
| Q6 | R7 B 선택: 선언 고리 = 나머지 끝, 미선언 = 현행 | 채택(미선언 고리를 나머지로 바꿀지는 실측 뒤) | -- | (신규) |
| Q7 | R13 S/B/F/X 분류 S0 필드 신설(계획 개정) | 채택 -- 계획 자리 없음(S-7). 계획 개정부터 | -- | TBA '분류 정본 자리 없음' |
| Q8 | R3 출발 단계에도 rout → follower gm(E10) | 채택 | -- | (신규, §3.2 pushpull 출발 전류 pA) |
| Q9 | M7 N1.1 결정 순서 문언 | 채택 | -- | -- |
| (유지) | B1 '계획을 따른다'(§6은 구간, 역산은 층 0) | 유지 -- R4와 같음 | -- | B1 닫힌 상태 유지 |

- **판정: D1~D7, B1, W-1~W-5, U-115, U-new1은 Q2~Q5·Q7로 모두 대체된다.** U-115는 Q4로 규칙 후보를 내지만, 사용자가 O-123에서 '나중에 다시 물어보라'고 보류했다. 그래서 Q4 안에서 따로 묻는다.
- **A1~A7**: 이 이름의 묶음을 증거 파일(LDA·SVD·TBA·LA1C)과 user_decisions에서 찾지 못했다(LDA의 결정은 D1~D7, 초안은 L0~L4). 2026-10-12 사용자 결정 'A1'(역산은 후보 수단, 격자 대체 안 함 -- DEC-71 (4))은 R4와 충돌 없이 유지된다. 나머지는 미확인(§10).

---

## 9. 원칙 점검 (이 감사의 권고 자체)

| 원칙 | 판정 | 근거 |
|---|---|---|
| graph 단일 정본 | 지킴: 종속 값 writer = 고리 종속 블록 하나(R6), 능력 = DE-1 하나, 요구 = spec. 새 cache·memo·sctx 슬롯·사본 0. 신설 필드는 분류(R13) 하나. 계획 자리가 없어 '계획 개정 대상'으로 멈춤(S-7) | §5.2 |
| 상수 발명 금지 | 지킴: 교과서 경험 계수(0.22·1.2~1.5·100 mV·gm/ID 8·15·0.75·0.4)를 규칙에 넣지 않음. R10 (c)의 비는 측정값 비 | §1.6 마지막 항 |
| fail-closed | 지킴: R5 (d), R7 (c), R10 (c) 상한, R8 범위 미선언 = 미측정 | §5.1 |
| 회로 이름·topology 태그 | 규칙 문언에 회로 이름 없음. 역할은 엔진 유도 필드(S1v roles·dc_coord)만. 회로 이름은 실측 인용에만 | §5 |
| heldout | 안 씀 | -- |
| 계획 우선 | design 정정(M10)은 계획 개정 승인 뒤로 둠 | §7 |
| DEC-103·DC/AC | 설계점 = θ, 극단 = 같은 W 평가. 동적은 ls oracle | R2·R9·R10 |
| 손계산 속도 | 탐색 안 끝 풀이 0. 종속 파생은 고리마다 1-D 나머지(LUT 역산) | R6 |
| 권고 실현 가능성 | §3 실측은 출발 단계·매크로까지. R5·R6 시제품 실측은 안 함 → '미측정' 표시 | §3.3 |

---

## 10. 미확인

1. T1·T2·T4 강의 노트의 웹 게시 주소(로컬 G: 사본만 확인). 저장소 원문 보관소(`assets/library/sources/`)에 넣지 않았다.
2. R5·R6(B가 층 0 후보마다 나머지를 받음)의 봉인·front 효과. 시제품을 만들지 않았다. LA1C §7.2는 W4 축만 쟀다.
3. R7을 미선언 고리에도 적용했을 때(B = 나머지, 면적 최소) 면적·이득·front 변화.
4. M3·M11(외층에서 B·R 축 제거, V_R 좌표)의 SLSQP 척도·front 영향.
5. R10 (c) 되먹임의 수렴(K_max 안에서 SR PASS 도달 여부). library SR 선언 0이라 실측 대상이 없다.
6. R3 출발 단계 E10 적용으로 pushpull류 출발 전류가 어떻게 바뀌는지(B80 E10 손계산 출발 front 1은 LA1C·B80 근거만 있다).
7. 출발 이득 L 하한 비활성(`u9_value_not_certified`)이 9회로 중 몇 회로인지. 이번에는 two_stage만 사유를 확인했다. 나머지 회로는 L = 0.15 µm만 확인했다.
8. 'A1~A7' 묶음의 출처.
9. 정상상태 요구 R_ss의 응용 망 DC 풀이를 어느 블록이 쓸지(R1 (b) writer -- spec 값 + 풀이 블록). design 결정 대상이다.
10. T6의 부하 gm/ID = 8(강반전) 선택이 엔진 가드(§6.4-2a·§7.5)의 상한과 같은 물리인지. 정성적으로만 비교했다(matching·잡음 = 가드).
