# ICMR 측정 정의 재검토 -- follower 대 servo 대 declared_feedback (사용자 O-114)

- 작성: 2026-10-23, 분석 전용 agent. 결정하지 않고 근거와 선택지만 낸다.
- 저장소 파일(엔진 code·계획·design)은 고치지 않았다. git은 읽기만 했다.
- 작업 폴더: `wt/_scratch_icmr_def/`.
- 원자료 사본: `wt/_drafts/evidence/2026-10-23/icmr_definition_review/`
  - `scripts/`: `eng_seal.py`·`slice_wm.py`·`spice_follow_v2.py`(어제 v2 스크립트 사본에 구성 S·T 추가), `analyze_cfg.py`(새 분석), `ext.py`(PDF 발췌)
  - `analysis/`: 회로별 `*.cfg_analysis.json`, `table.txt`(전체 표), `slice_wm.json`, 교과서 발췌 텍스트
- 이름 정리. 지시문의 (A)(B)(C)를 그대로 쓴다. SPICE 실측 구성 이름은 따로 붙였다.

  | 실측 구성 | 뜻 | 지시문 선택지 |
  |---|---|---|
  | A | 순수 단위 이득 follower: V(in−) = V(out) | (A) |
  | L | 봉인점 유지 follower: V(in−) = V(out) − (V_out0 − V_inv0). 출력이 입력을 따라 움직이되 봉인점 차를 지닌다. 어제 v2의 '구성 B' | 해당 없음(아래 §3.3 -- **지금 엔진 design이 실제로 계산하는 것**) |
  | S | 이득 1 servo: L에 더해 반전 입력 기준도 Δ만큼 민다. 지금 oracle `oracle_swing.py` ICMR 구성과 같다 | (B) 근사 |
  | T | 고이득 servo(진단): V(in−) = x − (x0 − V_inv0) + G·(V(out) − V_out0), G = 1000. 출력을 V_out0에 거의 정확히 묶는다 | (B) 정의 그대로 |

---

## 0. 결론

1. **기록**: servo를 버린 근거는 물리 비교가 아니었다.
   - O-25 (2)의 문언 '출력 고정 안 함, Allen 관례'가 출발점이다.
   - O-50 G4 / X-DE5가 이것을 'Allen 관례 = 단위 이득 follower'로 해석해 확정했다.
   - 이유로 든 것은 둘이다. (i) Allen 측정 관례, (ii) '되먹임 없는 고이득 회로는 출력이 레일로 가서 출력이 정의되지 않는다'.
   - 그런데 (ii)는 순수 개루프에 대한 말이다. DC servo는 출력을 정의하므로 (ii)는 servo를 기각하는 근거가 아니다.
   - O-52 G4-D (c) '개루프 별도 정의' 기각도 servo 자체를 판정한 것이 아니다. **한 구조에만 둘째 정의를 두는 것**을 원칙 위반으로 기각했다.
2. **원문**: 손계산 정의는 (B)와 같은 양이다. 시뮬레이션 관례는 (A)다.
   - 손계산 정의는 입력단 포화 조건이고, 내부 노드와 출력은 동작점에 있다(Razavi 식 4.1, Lee 2007 식 9, Allen 정의 문언). 이것은 (B)와 같다.
   - 교과서·강의의 **시뮬레이션 측정 관례**는 (A) follower다(Allen 2014 측정 강의를 인용한 Matibag 그림 22, Berkeley EE140 숙제).
   - (A)는 '출력 스윙이 입력 범위를 덮을 때만 같은 값'이다. 이 단서는 Razavi(telescopic을 follower로 묶으면 범위가 VTH보다 좁음)와 포럼 지적에 나온다.
3. **실측(SPICE, 5회로)**: (A)와 (B)의 차는 회로 꼴에 따라 수 mV부터 0.7 V까지다.
   - folded_cascode: (A) 폭 0.885 V, (B) 1.588 V(아래 끝 0.48 V 차)
   - two_stage_ota_sf(SF 출력 버퍼): (A) [0.537, 0.868], (B) [0.532, 1.783]. (A)의 창은 봉인점 입력(1.193 V)을 포함하지도 않는다.
   - ngcc 아래 끝: 93 mV 차
   - two_stage 위 끝: 50 mV 차
4. **숨은 결함**: 지금 엔진 design(41 §4.7-3b)의 follower 감도는 (A)를 계산하지 않는다. 계산하는 것은 L이다.
   - 봉인점에서 u = V_out '증분'만 강제하기 때문이다.
   - L은 (A)와 최대 85 mV(folded), 93 mV(ngcc 아래) 다르다. two_stage_ota_sf에서는 두 창이 겹치지 않는다(L [1.030, 1.725] 대 A [0.537, 0.868]).
   - 계획 정의 '(A) 단위 이득 follower'와 엔진 계산 사이에 지금 gap이 있다.
5. **엔진 계산**: (B)는 봉인점이 곧 servo 동작점이다. 그래서 같은 블록·같은 `graph.ss_nodal` 인수분해·Schur 1칸에서 행 하나(δV_out = 0)만 바꾸면 된다.
   - SPICE T 대비 선형 끝 오차는 4회로에서 ≤ 45 mV다(곡률).
   - (A)를 정의대로 계산하려면 봉인점에서 (V_out0 − x0)만큼 떨어진 상태로 외삽해야 한다(two_stage_sf는 0.99 V). 이것은 DEC-103 선형 틀이 감당할 섭동 크기를 넘는다.
6. **권고: (B) 출력 동작점 고정(DC servo)**
   - ICMR은 증폭기 고유 성질이다. 정의: 두 입력을 묶어 CM을 훑고, 출력은 봉인점 동작점 값에 DC로 묶은 상태에서, 모든 소자가 선언 영역에 머무는 범위.
   - 차동 출력은 DM = 0을 묶고 CM은 CMFB가 정한다. 지금 O-67 차동 처리와 같은 꼴이라 단일·차동이 정의 하나로 합쳐진다.
   - (C) declared_feedback은 ICMR 정의에서 뺀다. 응용 구성 질문이라 다른 양이다.
   - follower 사용 범위가 필요한 소비자(슬루 계단 끝)는 별도로 다룬다.
   - **원래 취지와 다름**(O-25 (2)·O-50 G4 등을 되돌림, §7)이라 사용자 결정 대상이다.

---

## 1. 기록 조사 -- 왜 지금 정의가 되었나

| 순서 | 결정 | 원문 위치 | 내용(인용 요지) | servo를 대하는 방식 |
|---|---|---|---|---|
| 1 | O-25 (2) (2026-10-19) | `wt/_drafts/user_decisions.md:644` | "ICMR = 차동 입력 0(또는 동작점 차)으로 두고 입력 공통모드를 DC로 훑을 때 **출력은 회로가 정하는 대로 따라가는 상태**에서 전 소자 포화 유지 범위(**출력 고정 안 함, Allen 관례**)". 동기는 옛 `ls_swing`(경로 합) 폐기다 | 문언이 '출력 고정 안 함'이라 servo(출력 고정)와 반대. 물리 비교는 없음 |
| 2 | X-DE2 | 계획 `gain-budget-gmid-sizing.plan.md:1650` | "ICMR 정의가 '출력을 고정하지 않고 회로가 정하는 대로 따름'(O-25 (2), Allen 관례)이 되어, 옛 `ls_swing` 입력 창 … 과 다른 양이다" | -- |
| 3 | O-50 G4 (2026-10-20) | `user_decisions.md:670` | "G4 ICMR 측정 구성 = spec 선언 되먹임 구성, 없으면 단위 이득 follower(β = 1, O-34 (2) 슬루와 같은 규칙) -- O-25 (2) … 의 해석 확정" | servo 대체를 결정 |
| 4 | X-DE5 (G4 근거) | 계획 `:1653` | "판정 근거: O-25 (2) 원문이 근거로 든 Allen 관례의 ICMR 측정 구성이 단위 이득 follower이고, **되먹임 없는 고이득 회로는 입력 차 0에서 출력이 레일까지 가 '회로가 정하는 출력'이 정의되지 않는다** … oracle은 servo로 출력을 고정한다(`oracle_swing.py:16-19`, 후속 정정 표)" | 기각 이유 (ii)는 **순수 개루프**에 대한 것. DC servo는 출력을 정의하므로 해당 안 됨 -- 이 판단은 servo와 follower를 비교하지 않았다 |
| 5 | oracle 후속 정정 | 계획 `:1720`, `:1723` | "ICMR 정의 O-25 하나로 맞추고 **servo 출력 고정 방식을 바꾼다**" / "G4: ICMR 훑기 구성 = 선언 되먹임 구성, 없으면 단위 이득 follower(**servo 출력 고정 대체**)" | oracle as-built = servo(아직 안 바뀜) |
| 6 | O-52 G4-D (2026-10-20) | `user_decisions.md:672`, history `:1375` | KVL 고정 출력(nmcnr RL)의 follower ICMR = O-43 D1 (a) 규칙. "(a) 정의 불능 (b) θ 성분 풀기 **(c) 개루프 별도 정의는 원칙 위반으로 기각**". history: "(c) 그 구조만 개루프로 재고 구성 표기를 달리함 -- 셋 다 원칙 위반으로 기각(기존 O-43 D1 (a) 규칙으로 정의되는데 정의 불능·새 풀이기·**별도 정의**를 만드는 것)" | 기각 사유 = '그 구조만 둘째 정의'. **모든 회로에 같은 servo 정의**는 판정 대상이 아니었다 |
| 7 | O-53 A-1·A-2 | `user_decisions.md:673` | 반전 입력 = DC 전달 부호 음수 포트. P3(입력 함께 훑기)는 측정 구성이 묶지 않은 포트에만 | follower 전제 |
| 8 | O-58 S-1~S-3 | `:678` | 측정 구성 창 = 봉인 뒤 블록 하나. 선언 되먹임 DC 망 = 선언 소자를 끊지 않은 봉인점 회로 | follower·선언 전제 |
| 9 | O-67 (1) | 계획 `:601`(문단 '차동 출력 회로의 측정 구성') | 차동 출력은 follower를 만들 수 없다. 선언 DC 되먹임이 없으면 **차동 모드만 닫는다**(원래 취지와 다름 승인) | 차동 출력에서는 이미 '출력 DM을 동작점 0에 묶음' -- servo와 같은 꼴 |
| 10 | O-79~O-87 | `user_decisions.md:700-708` | declared_feedback 정밀화: 용량만 선언 = 정의 불능, DC 되먹임 = 방향 의존 그래프 경로 판정, 두 출력 판정 갈림 = 정의 불능, 지원 밖 원소 = 정의 불능 | 13회로 해당 0개(O-79·O-82·O-83 문언 "해당 0개") |
| 11 | O-108·O-109·DEC-103 | `:766-772`, 계획 `:601`('단일 출력 follower 감도 -- KCL') | follower 감도 = 봉인점 DC 야코비안 + u = V_out Schur 1칸(KCL). 창 = 선형 감도 끝 하나 | 틀(KCL)은 servo에도 그대로 맞음(§5) |
| 12 | O-114 (2026-10-23) | `:796-798` | 재검토 지시. IT-2c test·code, Q-1(tied_ports) 보류 | -- |

**기록 결론**
- servo는 '문언(출력 고정 안 함) + 교과서 시뮬레이션 관례'로 대체되었다. 물리 비교, 실측, 엔진 틀 정합으로 진 적은 없다.
- O-52 (c) 기각은 '구조별 둘째 정의 금지'다. 모든 회로에 같은 servo 정의를 두는 것을 막지 않는다(추정이 아니라 history `:1375` 문언 그대로).

---

## 2. 원문 근거

| # | 출처 | 위치 | 내용 | (A)/(B) 중 어느 양 | 링크 / 로컬 |
|---|---|---|---|---|---|
| R1 | B. Razavi, *Design of Analog CMOS Integrated Circuits* (1st ed.) | §4.2 p.105-106, 식 (4.1), 그림 4.8 (PDF p.126-127) | V_in1 = V_in2 = V_in,CM으로 묶고 0→VDD로 훑음. 하한 V_GS1 + (V_GS3 − V_TH3). "Since Vout1 and Vout2 are relatively constant, … M1 and M2 enter the triode region if V_in,CM > V_out1 + V_TH = VDD − R_D·I_SS/2 + V_TH" | **(B)**: 출력 = 회로 동작점 값(개루프, 저항 부하라 동작점이 정해짐). follower 아님 | 로컬 `G:/내 드라이브/work/Todoc/기술문서/Gm_over_Id/Design of Analog CMOS Integrated Circuits (Behzad Razavi)marcado.pdf` (발췌 `analysis/razavi.txt`). 출판사 유료, 웹 공개본 링크 없음 |
| R2 | Razavi 같은 책 | §9.2.1 p.298-299, 그림 9.9 (PDF p.319-320) | telescopic의 입력·출력을 묶은 unity-gain: V_b − V_TH4 ≤ V_out ≤ V_b − V_GS4 + V_TH2, "this voltage range … always less than V_TH2". p.304: folded cascode는 "inputs and outputs can be shorted together and the choice of the input CM level is easier" | (A)는 출력 스윙과 섞인 '묶음 사용 범위'로 따로 다룸 -- ICMR(R1)과 다른 양 | 같은 파일 (`analysis/raz_tel.txt`) |
| R3 | Razavi 같은 책 | §9.7 p.325, 그림 9.47 (PDF p.346) | "consider the simple unity-gain buffer … in this case the voltage swings are limited by the input differential pair rather than the output cascode branch" | 응용(버퍼)에서 입력 범위가 제약이 되는 예. 정의가 아니라 응용 | 같은 파일 |
| R4 | J.-S. Lee et al., JSTS 7(1) 2007 | 저널 p.24 = PDF p.5, 식 (9) | "the ICMR of PMOS differential pair with NMOS active load is given by ICMR = V_DD − V_DSAT5 − V_TH − …" -- 입력단 소자 포화 조건 손계산 | **(B)**(입력단 조건, 출력 무관) | [doi:10.5573/JSTS.2007.7.1.020](https://doi.org/10.5573/JSTS.2007.7.1.020) · `skills/analog-gmid-design/assets/library/sources/ngcc_3stage_ff__lee_2007/paper.md:1165-1205` |
| R5 | E. Sánchez-Sinencio, LV tutorial (TAMU 2000) | p.45 표, p.47-48 | 입력 CM 요구 = 응용 구성에 따라 다름: inverting ≈ 0, non-inverting R1/(R1+R2)·Vsup, follower = rail-to-rail. VCMR = 레일에서 Vdsat + VGS(입력단만) | ICMR = 증폭기 성질(B), 요구치는 응용 구성이 정함 -- (C)는 '요구'의 질문 | [LV-Dallas-IEEE-Tutorial.PDF](https://people.engr.tamu.edu/s-sanchez/LV-Dallas-IEEE-Tutorial.PDF) · `assets/library/sources/current_reuse_telescopic_ota__sanchez_sinencio_2000/paper.md:2099-2240` |
| R6 | P. J. I. Matibag, UPC 석사논문 2024 | p.46 §5.7 그림 22, p.47 표 12 | "The range of input that the amplifier is working in the intended region (saturation) is defined by the ICMR. To measure this parameter, the circuit from figure 22 [= unity-gain follower] is used … when the input value deviates a 2% from the input, it is considered that the amplifier is not working". 그림 22 출처 [2] = "P.E. Allen, Measurement and Simulation of OPAMPS. Presentation. June 2014" | **(A)** 시뮬레이션 관례(정의 문장은 포화 = 증폭기 성질) | [upcommons](https://upcommons.upc.edu/bitstreams/a99028f7-5d7f-447a-b086-c1f4effcdb1b/download) · `assets/heldout/sources/rfc_ota__matibag_2024/pages/p46.png`, `paper.md:2238-2290`, 참고문헌 `:3658` |
| R7 | Penn ESE 568 (Khanna, 2018) lec5, Allen–Holberg 체계 강의 | slide 15 (PDF p.3) | "The input common-mode range is the range of common-mode voltages over which the **differential amplifier** continues to sense and amplify the difference signal with the same gain. Typically, the ICMR is defined by the common-mode voltage range over which all MOSFETs remain in the saturation region." | 증폭기 성질 정의 -- 출력 상태 명시 없음, '같은 이득으로 증폭을 계속' = 동작점 유지 쪽(B)에 가깝다(**추정**) | [lec5_6up.pdf](https://www.engineering.upenn.edu/~ese5680/fall2018/handouts/lec5_6up.pdf) · 사본 `wt/_scratch_icmr_def/dl/upenn_lec5.pdf`, 발췌 `analysis/upenn.txt` |
| R8 | Berkeley EE140/240A fa13 HW11 (검색 요약) | -- | unity-gain feedback에 넣고 입력을 훑어 dVout/dVin = 1/2가 되는 점을 범위로 | (A) 관례 | [hw11 pdf](https://inst.eecs.berkeley.edu/~ee140/fa13/homework/hw11.ee140-240a.f13.v2.pdf) -- **본문 직접 확인 안 함(검색 요약만, 미확인)** |
| R9 | EDAboard 'How to measure ICMR by Hspice' (포럼) | -- | unity-gain sweep 관례 + "the unit-feedback scheme … can only be available if the upper limit and lower limit of output range cover the limits of input range" | (A) 한계 지적 | [edaboard](https://edaboard.com/threads/how-to-measure-icmr-by-hspice.51279) -- 비권위 출처, 검색 요약만 |
| R10 | ADI MT-041 | p.1-2 | 입력 CM 범위와 출력 범위를 따로 정의(VCM(HI)/VCM(LO), VSAT(HI)/VSAT(LO)) | 입력·출력 범위 분리 = (B)와 같은 분리 | 로컬 `G:/내 드라이브/work/Todoc/기술문서/설계문서/12_Research Topics/EDACafe_Tutorials/Op Amp Input and Output Common-Mode and Differential Voltage Range.pdf` · [analog.com MT-041](https://www.analog.com/media/en/training-seminars/tutorials/MT-041.pdf)(링크 형식만 확인, 본문은 로컬로 확인) |
| R11 | Wulff CNR_OTA design note | `CNR_OTA.design.md:17-31` | "I've intentionally shifted the output common mode high in order for resistive feedback to give an input common mode that still keeps the tail current source … in saturation" | 응용 되먹임이 입력 CM을 정함 = (C)의 질문(응용 동작점), ICMR 정의 자체는 아님 | `assets/heldout/sources/cnr_ota__wulff_2024/CNR_OTA.design.md` |
| R12 | Allen–Holberg, *CMOS Analog Circuit Design* 2nd ed. | Ch.5·6 손계산 V_IC(max) = V_DD − V_SG3 + V_TN1, V_IC(min) = V_SS + V_DS5(sat) + V_GS1 | 입력단 포화 조건(거울 다이오드 쪽 동작점) = (B). 시뮬레이션은 unity-gain 구성(§6.6 측정 절) | **식·쪽 번호 미확인**(로컬 PDF·웹 본문 확보 실패; 식은 기억과 R7 강의의 Allen 체계 기준) |
| R13 | Johns–Martin, Gray–Meyer | -- | -- | **미확인**(로컬·웹 본문 확보 못 함) |

**판정: 손계산 정의는 어느 쪽과 같은 양인가**
- 손계산 식(R1·R4·R12)은 모두 '입력단과 꼬리 소자가 포화'다. 출력단·출력 노드는 회로 동작점 값을 쓴다(Razavi는 V_out = VDD − R_D·I_SS/2라고 명시).
- 그래서 **(B)와 같은 양**이다. 2단 회로에서 출력이 V_cm을 따라가며 출력단을 포화에서 밀어내는 효과는 손계산 식에 없다.
- (A)는 '증폭기를 follower로 쓸 때의 사용 범위'다. 시뮬레이션 관례(R6·R8)로 널리 쓰이지만 출력 스윙이 입력 범위를 덮을 때만 손계산 ICMR과 같다(R2·R9).

---

## 3. 물리 분석

### 3.1 두 구성의 차이는 출력 전압 하나다
- (A): V_out = V_cm(+오프셋). 출력단·캐스코드·출력 버퍼 소자의 포화 조건이 V_cm 함수로 창에 들어온다. 결과는 대략 ICMR(B) ∩ follower 출력 스윙이다.
  - 엄밀한 교집합은 아니다. 출력 전압이 gds·CMRR로 입력단 노드를 조금 옮긴다(two_stage 아래 끝 5 mV).
- (B): V_out = V_out0(봉인점). 출력 쪽 소자는 동작점에 머물고, 입력단과 그 부하·꼬리만 V_cm에 반응한다.
- 갈리는 회로 꼴(실측 §4):
  - **folded cascode**: (A)는 출력 캐스코드 바닥(M8)과 PMOS 쪽(M6)이 출력 스윙으로 창을 묶는다. (B)는 꼬리(M11)와 레일만 묶는다.
  - **출력 follower 버퍼(SF 출력, 2단+SF)**: 내부 노드 = V_out + V_GS,SF. (A)에서 출력이 V_cm을 따라가면 내부 노드가 V_cm + 0.7 V가 되어 일찍 포화를 잃는다.
  - **telescopic**: R2의 VTH 미만 범위(이 실측에는 없음 -- library의 telescopic은 차동 출력).
  - **다단 고스윙(two_stage, ngcc)**: 출력 스윙이 넓어 차가 작다(50 mV, 93 mV).
- 단일 출력 1단(5T): 출력 쪽 M2의 V_DS = V_GS1이라 항상 포화이고, 위 끝은 거울 쪽이 정한다. 두 구성이 같다(손 유도, 실측 없음 -- **추정**).

### 3.2 (B)의 기준 출력 전압 -- 상수를 발명하지 않는다
- 기준 = **봉인점 출력 노드 전압 `node.dc_v[out]`**. 이미 graph 필드이고 writer가 하나다.
  - W3 목표 출력이면 그 목표(예: 0.9 V)다.
  - 고임피던스 출력이면 봉인 풀이가 정한 값이다.
- oracle: `Vo,pred` = 같은 엔진 봉인점 예측(as-built `oracle_netlist.py:441-447`, `Vofs = vo − vin`). 새 상수가 없다.
- DEC-103 틀에서의 꼴:
  - 정해진 회로(W·바이어스 고정)를 흔드는 질문 → KCL 선형화.
  - 봉인점 DC 야코비안(`graph.ss_nodal`)에 '두 입력 = x0 + Δ(+ 한 입력에 미지 보정 ε), δV_out = 0' 행을 더한다.
  - 지금 follower 행(δu − δV_out = 0)과 같은 Schur 1칸이다. 바뀌는 것은 행의 꼴뿐이다.
  - 닫힌 꼴: 노드 감도 s_n = vx_n − vu_n·vx_out/vu_out (vx·vu = 두 입력 단위 구동 응답, 이미 `nodal_solve` 두 번으로 계산되는 양).
- **봉인점 = servo의 x0 동작점**이다(V_out = V_out0, 입력 차 = 봉인점 계통 오프셋). 선형화 중심이 정확히 맞는다.

### 3.3 지금 엔진 design이 계산하는 것은 L이다(새로 확인한 gap)
- 근거: design 41 v1.13.0 `:729-736`, 계획 `:601` '단일 출력 follower 감도 -- KCL'.
  - "반전 입력 노드 전압 u를 미지수로 두고 follower 닫음 u = V_out을 Schur 1칸으로 강제한 감도 … 창 끝 = 그 감도를 받은 `saturation_window` 끝"
  - 이 창은 봉인점 여유 + (follower 증분 감도)·Δ다.
- 그런데 봉인점은 V_inv0 ≠ V_out0이다(two_stage 1.156 대 0.900, two_stage_sf 1.194 대 0.206).
  - 그래서 이 창은 '출력이 입력을 따라 움직이되 봉인점 차를 유지하는' L 구성의 창이다. 정의 (A)(V_out = V_cm)가 아니다.
- 실측 L 대 A 차(§4 표):
  - folded 아래 −85 / 위 −81 mV
  - two_stage 위 +41 mV
  - ngcc 아래 −93 mV(L은 레일)
  - two_stage_sf는 **겹침 없음**
- (A)를 정의대로 계산하려면 둘째 우변(V_out0 − x0) 항이 필요하다(어제 v2 `it2c_spice_frame_v2.md` §2.3·`analyze_v2.py` `dv_kcl_A`). 이것은 봉인점 접선을 최대 0.99 V(two_stage_sf) 외삽하는 일이다.
  - v2는 "틀 판정은 B(=L)로 한다"라고만 적었다. 계획·design에는 이 gap이 기록되지 않았다.

### 3.4 차동 출력(CMFB)
- (A): follower를 만들 수 없다(출력 둘, 반전 입력 하나). 그래서 계획은 O-67로 '선언 DC 되먹임이 없으면 DM만 닫음'을 따로 두었다(원래 취지와 다름 승인).
- (B): 출력 DM = 동작점(0)으로 servo하고 CM은 회로의 CMFB가 정한다. 이것은 O-67의 '차동 모드만 닫는다'와 **같은 꼴**이다. 단일·차동이 정의 하나가 되고 구조별 갈래가 사라진다.
- oracle as-built도 차동 servo(`Efb_` 차동, `diff_feedback_gain`, `oracle_netlist.py:432-437`)라 같은 꼴이다.

### 3.5 (C) declared_feedback이 amp 설계 질문에 맞는가
- (C)는 '이 응용 되먹임 망에서 입력 CM이 어디까지 가도 되나'에 답한다. R5(응용별 요구 CM)와 R11(저항 되먹임이 입력 CM을 정함)이 이 질문이다.
- 이것은 응용 동작점 질문이다. 증폭기 설계 질문('이 증폭기의 입력 범위')과 측정 구성 축이 다른 양이다.
- graph 규칙 3: 정의가 다르면 다른 필드다. (C)를 ICMR 필드의 갈래로 두면 같은 이름에 두 정의가 섞인다.
- 13회로 실사용 0이다.
  - current_reuse_telescopic의 Cf1·Cf2는 용량만이라 DC 되먹임 '없음' → DM 닫힘 = (B)와 같은 결과.
  - 나머지는 `elements: []`(`*.sizing_spec.json` `human.feedback`).
- 기록상 슬루 과도 되먹임은 ICMR DC 망과 따로 정의된다(O-69 (1), 계획 `:602`). 그래서 (C)를 ICMR에서 빼도 슬루 쪽 선언 구성은 그대로다.

### 3.6 가정과 한계
- 판정 조건: VDS ≥ VDSAT + tol_seal(엔진 행 tol, 계획 판정 여유). tol = 0도 함께 계산했고 끝은 최대 26 mV(ngcc 위) 움직였다(`table.txt`·json `tol0`).
- 봉인점은 layer0 시작점 봉인이다(최적 설계점 아님). 회로별 절대값은 설계점마다 다르다. 구성 사이의 **차**가 이 분석의 대상이다.

---

## 4. 실측

### 4.1 방법
- 봉인점·기하는 어제 IT-2c v2와 같은 경로다.
  - `eng_seal.py`: 엔진 봉인점, `_scratch_it2c/src` 엔진.
  - `legacy_adapter.convert` → `oracle_netlist.write_netlists` free 본.
  - **finger 폭 = 엔진 LUT 정본 `slice_map[(kind, w_key)].w_m`, m = W/w_m 실수 배수**(B74 교훈, `w_key*1e-9` 안 씀). `slice_wm.json`: 5회로 모두 w_m = 5 µm.
- 구성 A·L·S·T. 비반전 입력 `Vdc_` 원을 x0에서 각 레일까지 0.5 mV 간격 `.dc`로 훑는다.
  - S는 `Vofs_`를 B 원 `c − (V(dcs) − x0)`로 바꾼다(oracle_swing ICMR과 같은 이득 1 servo).
  - T는 `Efb_`·`Vofs_`를 B 원 `x − (x0 − V_inv0) + 1000·(V(out) − V_out0)`로 바꾼다. 1000은 진단 도구 값이다: 출력 고정 오차 ≈ (CM 이득/1000)·Δ. 설계 상수가 아니다.
- 창 = x0에서 이어지는 '모든 엔진 sat 행 MOS 여유 ≥ 0' 구간(선형 보간). 엔진 선형 끝(KCL)은 `kcl_follower`의 vx·vu(= `graph.ss_nodal`과 같은 G)로 구성마다 같은 `lin_window`로 냈다.
  - A: v2 둘째 우변 식
  - L: 지금 design
  - S: δu = δV_out + Δ
  - T: δV_out = 0
- ngspice 오류 0. 모든 훑기가 끝까지 돌았다(`spice_run1~3.log`).
- sf_pushpull_output_opamp는 `layer0_start None`이라 봉인점이 없어 제외했다(`out/sf_pushpull_output_opamp.engine.json`).

### 4.2 결과 (입력 CM 절대 전압 V, tol_seal; 레일 = 0 / 1.8 V)

| 회로 (출력 꼴) | x0 / V_out0 | A 순수 follower | L (지금 엔진 design의 구성) | S servo 이득 1 (oracle as-built) | **T servo (B)** | A 대 T 차 (아래 / 위, mV) |
|---|---|---|---|---|---|---|
| two_stage_ota (2단, 고스윙) | 1.153 / 0.900 | [0.516, 1.663] w 1.148 (M5 / M2) | [0.511, 1.704] | [0.521, 1.713] | [0.521, 1.713] w 1.192 (M5 / M1) | −5 / **−50** |
| ngcc_3stage_ff (3단) | 0.538 / 0.900 | [0.093, 1.173] w 1.079 (M13 / M0) | [0.000, 1.182] | [0.000, 1.171] | [0.000, 1.171] w 1.170 (레일 / M0) | **+93** / +2 |
| folded_cascode (1단 캐스코드) | 1.046 / 1.132 | [0.695, 1.579] w **0.885** (M8 / M6) | [0.610, 1.498] | [0.212, 1.800] | [0.212, 1.800] w **1.588** (M11 / 레일) | **+483 / −220** |
| two_stage_ota_sf (2단 + SF 출력 버퍼) | 1.193 / 0.206 | **x0에서 포화 실패(M6)**. 포화 구간 [0.537, 0.868] w 0.331 | [1.030, 1.725] | [0.532, 1.784] | [0.532, 1.783] w **1.251** (M5 / M1) | +5 / **−915** (A 구간이 봉인점 입력을 포함 안 함) |
| nmcnr_amplifier (RL 부하 KVL 출력) | 0.300 / 1.658 | [0.077, 0.412] w 0.335 (M301 / M302) | [0.000, 0.341] | [0.000, 0.375] | [0.000, 0.409] w 0.409 (레일 / M302) | +77 / +3 |

- A 열의 출력 범위: two_stage [0.518, 1.642], folded [0.721, 1.570]. 출력이 V_cm을 따라가며 출력단 소자(M2·M8·M6·M13)가 묶는다.
- T 열의 출력: 모든 회로에서 V_out0 ± 0.5 mV(`vout_lo/hi`). S는 two_stage ±13, ngcc ±11 mV, nmcnr 1.598~1.745 V다. 이득 1 servo는 CMRR이 낮은 회로에서 출력을 다 묶지 못한다.
- S 대 T 끝 차: nmcnr 위 끝 35 mV, 나머지 ≤ 0.7 mV.
- nmcnr: 봉인점 입력 0.30 V(PMOS 입력, 레일 근처)·RL 출력이다. A에서 출력이 0.06~1.74 V로 흔들려 follower 추종 자체가 성립하지 않는다(DC 루프 이득 vu_out −133, CM 이득 큼).
  - spec `icmr_v ≥ 0.5`(`nmcnr_amplifier.sizing_spec.json:117-126`, '원문 단위 이득 0.5 V 계단')는 네 구성 모두에서 미달(0.33~0.41 V)이다.
  - 정의 비교 결론에는 쓰지 않는다(봉인점 의심, 별도 조사 몫).

### 4.3 엔진 선형 끝(KCL) 대 SPICE (mV, 엔진 − SPICE)

| 회로 | A (둘째 우변 외삽) | L (지금 design) | T (B, δV_out = 0) |
|---|---|---|---|
| two_stage_ota | +27.1 / −8.6 | +27.2 / −7.5 | +27.6 / −2.4 |
| ngcc_3stage_ff | −49.7 / −29.9 | −0.1(레일) / −37.1 | −0.1(레일) / −29.2 |
| folded_cascode | +5.2 / +1.8 | +8.5 / +0.4 | +45.0 / +0.4(레일) |
| two_stage_ota_sf | +31.0 / −14.1 (SPICE 구간 [0.537, 0.868] 기준) | +0.1 / −13.4 | +28.3 / −3.6 |
| nmcnr_amplifier | +18.9 / **+815** | 0 / +19.2 | 0 / **+818** (묶는 소자 M101 대 SPICE M302) |

- (B) 선형 끝은 nmcnr 밖 4회로에서 ≤ 45 mV다. 오차의 원천은 곡률이다. 같은 4회로에서 A(외삽) ≤ 50 mV, L ≤ 37 mV라 크기가 비슷하다.
- nmcnr는 A와 T에서 모두 800 mV대로 틀린다. 정의와 무관한 회로·봉인점 문제다(**추정**: 출력단 M302가 대신호로 크게 비선형).
- 묶는 소자는 4회로의 레일 아닌 끝에서 엔진 T와 SPICE T가 같다(folded 위 끝은 둘 다 레일).

---

## 5. 선택지별 영향

| 항목 | (A) follower (지금 계획) | (B) 출력 동작점 고정 servo | (C) declared_feedback |
|---|---|---|---|
| 정의가 답하는 질문 | follower로 쓸 때 입력 사용 범위(ICMR ∩ 출력 스윙) | 증폭기 입력단 고유 범위(손계산 식과 같은 양) | 특정 응용 망의 입력 범위 |
| 엔진 KCL 계산 | 정의대로 하려면 봉인점에서 (V_out0 − x0) 외삽(최대 0.99 V) 필요. 지금 design은 L을 계산 = **계획 정의와 gap** | 같은 블록 `icm_config`·같은 `graph.ss_nodal` 인수분해·Schur 1칸, 행만 δV_out = 0. 봉인점 = 동작점이라 외삽 0 | 선언 DC 망 + 경로 판정 + 여러 정의 불능 갈래(O-79~O-87) |
| 비용 | `nodal_solve` 2회(vx·vu) + 끝 식 -- gm/ID 손계산 수준 | 같음(새 풀이기·새 인수분해 0) | 같음 + 경로 그래프 탐색 |
| IT-2c `icm_config` 값 집합 | {declared_feedback, follower_beta1, as_is_single_input} | {servo(두 입력 묶음·출력 고정), as_is_single_input}, 차동 출력은 DM 고정(같은 servo 꼴) | (C)만 남기는 안은 13회로 0개라 해당 없음 |
| `tied_ports` (Q-1) | 출력에 묶인 반전 입력 | **두 입력 포트(함께 훑음)**, 출력에 묶인 포트 없음. P3(O-49·O-53 A-2) 갈래가 사라짐 | 선언이 정함 |
| 반전 입력 식별(O-53 A-1) | follower 닫음에 필수 | 엔진 선형 풀이에는 \|vu_out\| > 분해능만 필요하고 부호는 불필요(**추정**, 식 §3.2). oracle DC servo의 안정(음되먹임)에는 부호 필요. 슬루 follower(O-34)에도 필요하므로 판정 자체는 남음 | 선언이 정함 |
| 선언 되먹임 판정 기계 (`_dc_feedback_reaches`, `icm_config_feedback_*` code, S-3 DC 망) | 남음 | ICMR에서 소비자가 없어져 삭제 대상(**배선 원칙**: 만든 것은 쓰거나 지움) | 남음 |
| oracle | `oracle_swing.py` servo를 follower로 바꾸는 card 필요(계획 `:1720`·`:1723`) | **as-built servo 유지**. 이득 1 servo는 CMRR 낮은 회로에서 출력이 덜 묶임(nmcnr 35 mV) → 정확 고정(고이득·적분 servo) 여부 결정 필요. servo 포트가 role 이름 `input_n` 기반(`oracle_netlist.py:404`)인 점은 기존 결함(계획 '포트 role 이름 근거 금지'와 다름) | 선언 구성 넷리스트 |
| 13회로 판정 | ngcc `icmr_v ≥ 0.6`: A 1.079·T 1.170 둘 다 통과. nmcnr `≥ 0.5`: 둘 다 미달. icm_margin 회로(sf_pushpull, current_reuse)는 봉인점 없음·차동이라 이번 실측 밖 | 같음(판정 변화 0 -- 실측 두 제약 회로). 일반적으로 (B) ≥ (A)라 더 관대 | -- |
| spec 출처 정합 | nmcnr spec은 '원문 단위 이득 계단' 측정(A 관례), rfc 입력 DC는 Matibag follower ICMR(A) 중앙값 | ngcc spec은 손계산 식(9)(B 꼴). (B)로 바꾸면 nmcnr spec 값의 측정 정의가 엔진 정의와 다름 -- spec 출처 표기 재확인 필요 | -- |
| 슬루 계단 끝(O-28·O-51, 계획 `:602`) | 'ICMR 끝 = follower 계단 끝'이 같은 구성이라 정합 | **새 충돌**: (B) 끝까지 follower 계단을 밀면 출력이 따라가지 못하는 구간이 생김(folded 아래 끝 0.21 V 대 follower 0.69 V). 슬루 계단 끝을 'follower 사용 범위'로 따로 정해야 함(새 양이면 새 필드·소비자 확인 -- graph 규칙 3) | -- |
| card 범위 | IT-2c 그대로. 다만 L/A gap 해소(둘째 우변 외삽 도입 또는 정의를 L로 바꿈) 결정 필요 | IT-2c: follower 행 → δV_out = 0 행, config 집합 축소, DC 되먹임 판정 삭제(범위 축소). IT-2d·DE-1 (a) 정의 창은 같은 블록 재사용(기준만). DE-1 (b) 스윙은 변화 없음(이미 차동 훑기·follower 행 없음). oracle G4 card 취소 | -- |

### 5.1 원칙 점검표

| 원칙 | (A) follower | (B) servo | (C) declared |
|---|---|---|---|
| 물리 정합 최우선·가장 일반형 | 출력 스윙이 섞임. 차동 출력에 정의 안 됨(특례 O-67 필요). 지금 엔진은 L이라 물리 구성과 다름(실측) | 손계산 정의와 같은 양. 단일·차동이 같은 꼴(DM 고정)이라 일반형 | 응용 한정 -- 일반형 아님 |
| DC/AC 분리 | DC (위반 없음) | DC (위반 없음) | DC 망(위반 없음) |
| DEC-103 계산 틀 | 섭동 틀은 맞으나 정의대로면 큰 섭동(0.99 V) 외삽 -- 선형 틀 범위 밖 | 봉인점 = 동작점, 섭동 = Δ만. 틀에 정확히 맞음 | 맞음 |
| gm/ID 손계산 속도 | 같음 | 같음(행 하나 교체) | 경로 탐색 추가 |
| graph 단일 정본 | 문제 없음(정의·구현 gap은 별개) | 기준 V_out0 = `node.dc_v` READS(새 필드·사본 0). 'follower 사용 범위'가 필요하면 다른 정의 → 다른 필드(소비자 있을 때만) | ICMR 이름에 다른 정의를 섞음(규칙 3 위험) |
| fail-closed | 차동·선언 없음 등 갈래 다수 | 정의 불능 = 선형 풀이 특이, \|vu_out\| ≤ 분해능, 봉인점 없음. 갈래 감소 | 갈래 다수(용량만·경로 갈림·지원 밖 원소) |
| 상수 발명 금지 | 0 | 기준 = 봉인점 값. oracle 고이득 servo를 쓰면 이득 값은 도구 매개변수(판정 분해능으로 근거화 필요) | 0 |
| 회로 이름 code 금지 | 지킴 | 지킴. oracle servo의 role 이름 의존은 기존 결함으로 별도 | 지킴 |
| 계획 먼저 | 지금 계획 | 계획 N3.8 개정 → 검증 → 승인 → design 41 §4.7-3b | 지금 계획 |
| 논문 값 인용 금지 | -- | spec 값은 사용자 확정 값. 정의만 원문 근거 | -- |

---

## 6. 권고 -- (B) 출력 동작점 고정(DC servo) 하나

**정의(계획 N3.8 개정안 요지)**
- ICMR = 입력 포트를 같은 x로 함께 훑는다(차동 입력 = 봉인점 차 유지).
- 출력은 DC에서 봉인점 동작점 값에 묶는다.
  - 단일 출력: V_out = `node.dc_v[out]`
  - 차동 출력: DM = 봉인점 값, CM은 회로의 CMFB
- 이 상태에서 모든 MOS가 선언 영역에 머무는 범위다.
- 입력이 하나인 회로는 지금처럼 '회로 그대로'다.

**계산**
- 엔진: 봉인 뒤 `icm_config` 블록 안, `graph.ss_nodal` + Schur 1칸(δV_out = 0)의 KCL 선형 감도 끝('추정').
- oracle: `.dc` servo 훑기로 확정. as-built를 유지하되 출력 고정 정확도는 결정 사항이다.

**근거**
1. 손계산 ICMR(R1·R4·R12)과 같은 양이다. 출력 스윙은 이미 별도 metric(DE-1 (b))이 재므로 두 양이 분리된다(R10 ADI도 분리).
2. 실측에서 (A)와 (B)는 회로 꼴에 따라 0.7~0.9 V 다르다. 차이는 전부 출력 쪽 소자가 낸다(묶는 소자 M8·M6·M13·M2/SF 계열). 따라서 (A)는 입력 범위가 아니라 출력 스윙을 함께 잰다.
3. 엔진 틀(DEC-103·O-108 KCL)에 정확히 맞는다. 봉인점이 곧 servo 동작점이라 외삽이 없고, 새 풀이기·필드·cache가 없으며, 행 하나만 바꾼다.
   - 지금 design의 L(계획 정의와 다른 구성)이라는 gap도 함께 없어진다.
4. 차동 출력 특례(O-67)·선언 되먹임 판정 기계(O-79~O-87)·P3 갈래가 정의 하나로 합쳐지거나 사라진다. 가장 일반적인 형태다.
5. 사용자 질문의 실무 관행('amp 설계는 개루프, 되먹임은 응용')과 맞는다. 응용 되먹임(C)은 다른 양이라 ICMR 갈래에서 뺀다.

**착수 전 결정이 필요한 것(사용자 몫)**
- (i) 슬루 계단 끝(O-28·O-51): (B)로 바꾸면 follower 계단 끝이 ICMR 끝과 갈린다. 계단 끝을 무엇으로 할지 정해야 한다.
  - 후보: 오라클 follower 훑기로 잰 사용 범위를 슬루 전용으로 둔다(새 정의 = 새 필드, 소비자 = 슬루).
- (ii) oracle 출력 고정 정확도: 이득 1 servo(as-built)를 쓸지, 정확 고정(고이득) servo를 쓸지. nmcnr에서 35 mV 차가 난다.
- (iii) nmcnr spec 값(원문 follower 측정)과 (B) 정의의 정합 표기.

---

## 7. 원래 취지와 다름 -- (B)를 고르면 되돌리거나 바뀌는 결정

| 결정 | 지금 | (B) 뒤 |
|---|---|---|
| O-25 (2) | '출력은 회로가 정하는 대로 따름, **출력 고정 안 함**, Allen 관례' | 출력을 봉인점 동작점에 고정(문언 정반대) |
| O-50 G4 / X-DE5 | 측정 구성 = 선언 되먹임, 없으면 β = 1 follower. oracle servo 대체 | servo가 정의. oracle G4 'servo 대체' 취소 |
| 계획 `:1720`·`:1723` oracle 후속 정정 | servo 출력 고정 방식을 바꾼다 | 바꾸지 않음 |
| O-52 G4-D | KVL 고정 출력 follower = O-43 D1 (a) + follower 행 | 같은 연립 + δV_out = 0 행(기각된 (c) '구조별 개루프 정의'와는 다름 -- 모든 회로 같은 정의) |
| O-53 A-1·A-2 | 반전 입력 = follower 닫음 대상. P3 = 묶이지 않은 포트만 | 두 입력 함께 훑음(A-2 갈래 소멸). A-1은 슬루·oracle servo 부호용으로 남음 |
| O-58 S-3, O-79~O-87 | 선언 되먹임 DC 망·DC 되먹임 경로 판정·관련 정의 불능 code | ICMR에서 삭제(소비자 없음) |
| O-67 (1) | 차동 출력 = DM만 닫는 특례(원래 취지와 다름 승인) | 특례가 아니라 정의 본문 |
| O-108 | 단일 출력 follower 감도 = u = V_out Schur 1칸 | 같은 KCL·Schur 1칸, 행 = δV_out = 0 |
| O-34 (2)·O-51 | 슬루 계단 끝 = ICMR 끝(같은 follower 구성) | 계단 끝 정의 재결정 필요 |
| design 41 §4.7-3b, IT-2c card | config 집합·follower 행·DC 되먹임 판정 | 개정 |

(A)를 유지할 때도 별개로 '원래 취지와 다름'이 하나 남는다. 지금 엔진 design은 L을 계산한다. 계획 정의 (A)와 다르고 실측 차는 최대 93 mV이며, two_stage_sf에서는 창이 겹치지 않는다. 그래서 (A)를 유지하면 '둘째 우변 외삽 도입' 또는 '정의를 L로 바꿈' 결정이 따로 필요하다.

---

## 8. 미확인
- Allen–Holberg 교과서 본문: ICMR 손계산 식의 쪽 번호와 §6.6 측정 그림 번호. 로컬 PDF가 없고 웹 본문도 확보하지 못했다. R6이 인용한 Allen 2014 측정 강의 원본도 확보 못 했다.
- Johns–Martin, Gray–Meyer의 ICMR 정의.
- Berkeley EE140 HW11 본문(검색 요약만).
- 5T 단일단에서 (A)와 (B)가 같다는 것은 손 유도만 했다(실측 없음).
- (B)에서 엔진 선형 풀이가 반전 입력 부호를 쓰지 않아도 된다는 것: 식으로만 확인, code 확인 없음.
- sf_pushpull_output_opamp(봉인점 없음)·차동 출력 회로(current_reuse_telescopic, cnr_ota)·heldout(erfc, r2r, rfc)은 실측 밖이다.
- nmcnr 선형 끝 800 mV 오차의 원인.
- 봉인점은 layer0 시작점이다. 최적 설계점에서 차의 크기는 다를 수 있다(꼴은 같다고 **추정**).
