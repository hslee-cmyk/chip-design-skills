# 정상상태 전류와 동적 전류 -- 셀 사이징에서 '두 θ점'이 필요한가 (문헌 조사·개념 정의)

- 작성: 방법론 조사 agent, 2026-10-25. 엔진·계획·design·spec은 고치지 않았다. 이 파일과 임시 파일(`wt/_scratch_steadydyn/`)만 썼다. git은 읽기만 했다(chip-design-skills HEAD `56dd1f8a`).
- 사용자 질문(원문, 2026-10-25): "지금 내가 요구한 개념정의는 steady state의 전류와 dynamic 전류가 섞인 개념인 것 같아. cell sizing측면에서는 이 두 전류를 모두 감당할 수 있어야 한다고 생각하는데, 그건 두가지 theta점 고정이 필요한 것이 아닌가 생각되는데 일반적으로는 어떻게 접근하는지 웹에서 조사해서 개념을 정의해보자."
- 앞선 근거(읽기만): `evidence/2026-10-25/load_drive_principle_audit.md`(아래 '감사'), `evidence/2026-10-24/min_current_from_load.md`, `classb_gmid_op_point.md`, `_drafts/user_decisions.md` O-26·O-122·O-123, 계획 `chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` DEC-65(264행)·DEC-70(269행)·DEC-71(270행)·DEC-103(302행)·U-115(2263행).
- 원자료(`wt/_scratch_steadydyn/`): `dl/*.pdf`(내려받은 원문), `h.txt`(Hershenson TCAD 2001 텍스트), `silveira.txt`, `boser.txt`, `L040.txt`(Allen ECE6412 L040, 감사가 내려받은 `_scratch_mincur/dl/L040.pdf`에서 추출), `rincon.txt`, `arxiv2309.txt`, `sbm.txt`, `allen_hits.txt`, `dec71.txt`.
- heldout은 쓰지 않았다. SPICE·엔진은 돌리지 않았다.

## 0. 결론

1. **문헌의 일반 접근은 '설계점 하나 + 극단 상태는 같은 W로 평가'다.** 두 번째 동작점을 독립 변수로 따로 사이징하는 문헌은 찾지 못했다.
   - gm/ID 원전(Silveira 1996)과 최적화 사이징(Hershenson·Boyd·Lee 2001)은 변수 하나의 바이어스점(소자별 전류·gm/ID, 또는 W·L·바이어스 전류)을 둔다. 슬루는 그 점의 전류식(SR = I/C)으로 바꾸고, 스윙은 출력 끝 전압에서 같은 변수로 포화 조건을 건다. Hershenson은 이 조건을 "for all possible values of the input common-mode voltage and the output voltage"로 쓴다(§IV-A, p.7, 식 (12)~(15)).
   - 동적 요구를 손계산 하한으로만 쓰고 정확 판정은 과도 시뮬레이션에 맡기는 절차도 강의 표준이다. Boser EE240B의 절차는 이렇다. 슬루 시간을 가정하고, 선형 정착으로 설계한 뒤, "verify with a full-scale input step"으로 검증하고 반복한다(OTA III 슬라이드 17).
2. **class-AB 출력 소자는 실무에서 W를 피크 전류 상태에서 정한다.** 정지전류는 바이어스 회로가 따로 정한다. 근거는 Allen L26 p.26-10(I1 = I2 = Ib·(W1/L1)/(W7/L7)), Rincon-Mora 2001(정지 140 µA, 최대 ±7 mA, CMFB가 정지점을 정함), Xie & Chen 2019 p.4, philipalcorn/gmid 예(출력 NMOS를 "about 14.6 mA peak"에서 gm/ID별로 W를 정함)다. **사용자 직관 '두 상태를 모두 감당해야 한다'는 맞다.**
3. **그러나 '두 θ점 고정'(독립 설계점 둘)은 필요하지 않다.**
   - 피크 상태는 같은 W를 공유한다. 그 단자 전압은 회로가 정한다. 구동단 DC 범위 끝이 V_GS,max를 정하고, 출력 범위 끝이 V_DS를 정한다. 그래서 피크 상태에 남는 자유도는 0이다.
   - 피크 상태는 정지 θ(I_q, ln IDu_q, L)의 함수다: I_peak,cap(θ) = (W/L)·IDu(V_GS,max, V_DS,end; L), W = I_q·L/IDu_q.
   - class-AB가 '두 점'처럼 보이는 까닭은 따로 있다. 정지전류와 W가 서로 독립인 두 자유도이고, 둘 다 이미 θ에 들어 있다.
   - 판정: **가설은 부분적으로 맞다.** 평가할 '상태'는 둘(정지 `.op`, 극단 `.dc`/`.tran`)이다. 설계점(θ)은 하나다.
4. **개념 정의안(§4):** 부하 쪽 **요구**는 셋으로 나눈다. 정상상태 요구(DC), 동적 요구(대신호·과도), 소신호 요구(gm)다. 회로 쪽 **능력**은 θ 봉인점에서 낸 필드 둘이다. 하나는 방향별 공급 능력 함수 I_cap,dir(V)(DC, DEC-65 정의를 범위 끝 V로 넓힌 것)이고, 다른 하나는 gm(θ)(ss)다. 정상상태와 동적 요구는 **같은 능력 함수 하나**와 비교한다. 준정적 근사로 슬루 중 노드 전류는 순간 전압에서의 DC 능력과 같기 때문이다. 정확값은 `.tran`이 확정한다.
5. **(A)(B)(C) 비교(§5) 권고:** **(B) 단일 θ + 극단 상태를 같은 W·바이어스로 평가해 θ 제약으로 되돌림**을 쓴다(DEC-70의 'DC 동작 범위 필드' 제약 자리).
   - 극단 상태 평가는 선형 KCL 감도(B-lin)로 할 곳과 소자 단위 비선형 LUT 평가(B-nl)로 할 곳을 나눈다. class-A 헤드룸은 B-lin, class-AB 피크 전류는 B-nl이다. class-AB 피크/정지 비는 실측 19~658배다. 이 크기는 선형화가 감당하는 '근사 오차'가 아니다.
   - (A)는 class-A의 레일 source β 쪽에서만 정확한 하한이다. 그 밖에는 출발값이다.
   - (C)는 W에 생산자가 둘이 된다(graph 규칙 1). 피크 상태를 설계점으로 다루므로 DEC-103과도 맞지 않는다. 그래서 기각한다. 예외는 바이어스 설정 자체가 다른 여러 동작 모드(가변 바이어스·모드 전환·PVT 코너)다. 이 경우에는 Hershenson §IX처럼 같은 W에 대해 조건마다 제약을 복제하는 꼴이 맞다.
6. **O-122와의 관계:** 교과서 관례(Allen·UT·arXiv·Hershenson)는 슬루를 바이어스 전류 하한으로 바꾼다(꼴 (A)). O-122는 엔진에서 이것을 지웠다. 이 차이는 사실로 적는다. 관례를 정의로 쓰지 않는다. 동적 요구는 지금 결정 그대로 둔다. 사용자가 손계산한 몫을 선언하거나(감사 D1 (나)), oracle `.tran`만 쓴다. O-122를 바꾸자는 권고는 하지 않는다.

## 1. 문헌 조사

### 1.1 gm/ID 원전·강의

| 출처 | 설계점 | 대신호 요구의 처리 | 인용(쪽) |
|---|---|---|---|
| Silveira·Flandre·Jespers, IEEE JSSC 31(9), 1996 -- [PDF(TAMU 사본)](https://people.engr.tamu.edu/hoyos/courses/474/gm_ID_methodology_silveira_jssc_1996.pdf), 로컬 `wt/_scratch_steadydyn/dl/silveira.pdf` | 총 전류 I_tot = 2 µA를 먼저 정하고, 소자별 gm/ID를 고른 뒤 W/L을 정한다(점 하나) | SR은 그 점의 전류식(식 (5), B·I_D1/C_L 꼴)으로 **평가**한다. 스윙은 같은 소자의 I_D–V_G 관계로 **예측**한다(따로 사이징하지 않는다) | p.1315 §III: "For large-signal related performance aspects such as signal swing, an I_D–V_G or g_m/I_D–V_G relationship"; p.1316: "is required. This extension of the methodology was applied to predict the output swing." / "The B factor multiplies f_T and SR" |
| Boser, UC Berkeley EE240B "OTA III -- Slewing" -- [PDF](https://www2-bsac.eecs.berkeley.edu/~boser/courses/240B/lectures/M10%20OTA%20III.pdf), 로컬 `dl/boser_m10.pdf` | 선형 정착으로 설계한 점 하나 | 슬루는 가정한 비율로 두고 전 폭 계단 과도 시뮬레이션으로 검증·반복한다 | 슬라이드 17 "Design Procedure with Slewing": "1. Start by assuming a slewing time, e.g. 50% of ts 2. Design and verify that linear settling completes … (apply only small steps …) 3. Now verify with a full-scale input step … 4. Iterate" |
| Hoyos, TAMU ECEN474 Lecture 7(Murmann 노트 기반) -- [PDF](https://people.engr.tamu.edu/hoyos/courses/474/lecture7.pdf) | 표 기반 gm/ID 설계점 하나 | "Setting ID for VO=1.5V for large output swing range" -- 스윙은 동작점 위치로 맞춘다 | 텍스트 184~185행(`hoyos7.txt`) |
| arXiv 2309.04863(65 nm gm/ID 2단 OTA) -- [PDF](https://arxiv.org/pdf/2309.04863) | 점 하나 | SR → 전류: "SR = 2·I_D1/C_c = I_D5/C_c … From the given slew rate specification the value of currents … can be easily calculated" | §E, 식 (4) |
| UT Austin 2단 op-amp 절차(Thomsen) -- [DOC](https://users.ece.utexas.edu/~athomsen/twostage.doc) | 점 하나 | "Calculate I5min, I7min from slew rate", "If von6 violates the min output swing, adjust W/L6 up" -- 스윙은 같은 점의 V_ov로 검사·보정 | 문서 단계 5·7·9(번호 없음, 순서로 셈) |
| Jespers & Murmann, *Systematic Design of Analog CMOS Circuits*(CUP 2017) -- [Cambridge 3장](https://www.cambridge.org/core/books/systematic-design-of-analog-cmos-circuits/basic-sizing-using-the-gmid-methodology/185BE8CB4F04AD9FFC08CDE06D3EA8A9) | -- | **원문 미열람**(유료). 목차: 3장 기본 사이징(pp.21–61), 4장 잡음·왜곡·부정합, 5·6장 회로 예. 슬루를 다루는 쪽은 확인하지 못했다 | §7 미확인 |

### 1.2 교재·제조사

| 출처 | 내용 | 인용(쪽) |
|---|---|---|
| Allen, ECE6412 L040 "CE and CS Output Stages" -- [PDF](https://pallen.ece.gatech.edu/Academic/ECE_6412/Spring_2004/L040-CS&CEOut(2UP).pdf), 로컬 `wt/_scratch_mincur/dl/L040.pdf` | 요구 둘(C·SR, Vpk/R_L)을 한 '최대 전류'로 묶는다. **W는 극단 상태에서 정한다.** 흡수 소자 M1은 게이트를 레일까지 몬 상태에서 피크와 I_Q를 함께 나르도록 크기를 잡는다. 전류원 M2는 I_Q에서 정한다 | p.040-3: "Maximum sinking current is, I_OUT⁻ = K'₁W₁/2L₁·(V_DD − V_SS − V_T1)² − I_Q", "The maximum current will be determined by both …"; p.040-5 Example 5.5-1: "W1/L1 = 2(I_OUT⁻ + I_Q)/[K_N'(V_DD + \|V_SS\| − V_TN)²]" |
| Allen, Lecture 26 "Buffered Op Amps" -- [PDF](https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf), 로컬 `skills/analog-gmid-design/assets/library/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf` | class-AB: 정지전류는 바이어스 소자와의 W 비가 정한다(출력 W와 독립 자유도). Example 26-2: SR·C_L로 출력 전류 1 mA를 정한 뒤, 그 고정 회로로 R_L 끝 스윙을 **평가**한다 | Page 26-10(PDF p.10, `paper.md` 469·477행): "the common-source, push-pull is ideal if the quiescent current can be controlled", "I1 = I2 = Ib·(W1/L1)/(W7/L7)"; Page 26-25(PDF p.25): "SR = 10V/µs and 100pF capacitor give I15 = 1mA"; Page 26-26(PDF p.26, `paper.md` 1366행 부근): "The signal swing across the 500 load resistor will be restricted to ±0.5V due to the 1000µA output current limit." |
| ADI MT-045 -- [PDF](https://wcm-cce.cldnet.analog.com/media/cn/training-seminars/tutorials/MT-045_cn.pdf) | 전 전력 대역 SR = 2πf·Vp(속도 선언의 다른 꼴) | 감사 §2.3 인용 그대로 |
| Razavi, Johns-Martin, Sansen *Analog Design Essentials* | **원문 미열람.** 2단 op-amp 예제의 SR = I_tail/C_c 꼴은 위 Allen·UT·arXiv와 같은 관례로 알려져 있다. 쪽 번호는 확인하지 않았다 | §7 미확인 |

### 1.3 최적화 기반 사이징

| 출처 | 변수 | 슬루·스윙·극단 상태 | 인용(쪽) |
|---|---|---|---|
| Hershenson·Boyd·Lee, "Optimal Design of a CMOS Op-Amp via Geometric Programming", IEEE TCAD 20(1), 2001 -- [PDF](https://www-leland.stanford.edu/~boyd/papers/pdf/opamp_tcad.pdf), 로컬 `wt/_scratch_steadydyn/hershenson_tcad.pdf` | W·L·C_c·기준 전류. 바이어스 전류 I1·I5·I7은 그 단항식이다(점 하나) | **스윙**: 출력 최소·최대 전압에서 같은 변수로 포화 부등식을 건다(극단 상태 = 같은 설계의 평가). **슬루**: 바이어스 전류에 대한 두 posynomial 부등식(식 (37)). 수식 기호는 PDF 이미지라 텍스트로 뽑지 못했다. 교과서형 SR = min(2I1/C_c, I7/(C_c + C_L))로 읽히며 확인이 필요하다 | §IV-A p.7: "we assume that the output voltage is allowed to swing between a minimum value and a maximum value (which takes into account large signal swings in the output). The bias conditions are that each transistor should remain in saturation for all possible values of the input common-mode voltage and the output voltage", 식 (12)~(15), "Transistor … The most stringent condition occurs when the output voltage is at its minimum value"; §VI-A p.10 식 (37) |
| 같은 논문 §IX "Design for Process Robustness" p.14–15 | 같은 설계변수 | **여러 조건**: 조건마다 제약을 복제하고 변수는 공유한다 -- 꼴 (C)가 맞는 경우의 원형 | "list a set of possible parameters, and to replicate the design constraints for all possible parameter values" |
| Severo & Girardi, SForum 2010 -- [PDF](https://sbmicro.org.br/sforum-eventos/sforum2010/31.pdf) | 소자별 gm/ID·전류(GA 탐색) | SR 등 spec을 같은 설계 벡터에서 SPICE로 평가 | Abstract·§2: "transistors are free variables …", "Circuit specifications are evaluated using an external electrical simulator" |
| circuitgenome 분석 사이징 흐름 -- [문서](https://circuitgenome.readthedocs.io/en/stable/theory/sizing_flow.html) | KCL로 바이어스 전류를 먼저 고정하고 W·L만 고른다 | "SR sets the C_c ceiling", 스윙은 사이징 뒤 margin 보고 | 페이지 본문 |
| philipalcorn/gmid -- [GitHub](https://github.com/philipalcorn/gmid) | 소자 단위 LUT 사이징 | class-AB 출력 NMOS를 **피크 전류(약 14.6 mA)에서** gm/ID 10·7·5로 W를 정한다(W 13,469 / 785 / 529 µm) | README 예 |
| Chen TCAD 2022(gm/ID+BO), BAG, Chen 2024 class-AB | **찾지 못함/미열람** | 시뮬레이션 기반 최적화는 일반적으로 설계 벡터 하나를 여러 testbench(`.op/.ac/.tran`)로 평가한다(위 Severo와 같은 꼴). 원문 확인은 하지 않았다 | §7 |

### 1.4 class-AB 출력단

| 출처 | 정지전류를 정하는 것 | 피크(W)를 정하는 것 | 인용 |
|---|---|---|---|
| Allen L26 p.26-10 | 바이어스 소자 W 비(Ib·(W1/L1)/(W7/L7)) | 큰 C 부하 구동 능력("ability to sink and source a large current") | 위 표 |
| Rincon-Mora & Stair, IEEE TCAS-II 2001 -- [PDF](https://rincon-mora.gatech.edu/publicat/jrnls/tcasii01_ab_amp.pdf) | CMFB 루프 "controls the quiescent biasing conditions of the power transistors", "steady-state driver quiescent current is thus determined by the current flowing through RCMR" | 출력 소자 = ±7 mA 구동 | 초록 "maximum output current of ±7 mA with only 140 µA of quiescent current", §II·§III(PDF p.3·p.5) |
| Xie & Chen 2019, 로컬 `assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/paper.md` p.4(436~447행)·p.2(271~279행) | 안정도(gm2): "The limitation of reducing the current further more is the stability requirement" | **W를 '사이징 점'(gm/ID 17, 176 µA → W 25/65 µm)에서 정하고, 같은 W를 정지 22 µA("barely-on")로 운전** -- 문헌 속 '두 점' 실례 | "the drain current is decided to be 176µA … the channel width … set to 25µm and 65µm … The final output stage current is around 22µA while satisfying the stability requirement" |
| 앞선 실측 `classb_gmid_op_point.md` §0-3, `min_current_from_load.md` §3.3 | pushpull θ 전류를 올린 점: 정지 48 µA(엔진 = SPICE) | 최대 0.92 mA(source)·1.8 mA(sink) = 정지의 19~38배. library 배율 J_max/J_q 19~658배 | 같은 파일 |

Xie & Chen의 '176 µA 사이징 점'은 W를 고르는 손계산 수단이다. 독립 동작점이 아니다. W가 정해지면 자유도는 (W, I_q) 둘뿐이다. 이 둘은 θ의 (I_q, ln IDu_q)와 일대일이다(W = I_q·L/IDu_q). 그 논문은 gm2 = 3 mS를 176 µA 점에서 냈다. 그런데 안정도 판정은 정지 22 µA 점에서 해야 물리적으로 맞다. 원문은 "satisfying the stability requirement"라고만 적었고, 22 µA 점의 gm 값은 없다(확인 불가).

### 1.5 스윙 끝 포화 검사 (조사 4)

- 일반 절차는 같은 설계변수로 극단 상태를 평가하는 것이다. 극단에서 따로 사이징하지 않는다. Hershenson §IV-A(식 (12)~(15)), UT 절차 단계 7(V_ov6가 최소 출력 스윙을 어기면 같은 소자의 W/L을 키우고 gm을 다시 계산), Silveira p.1316(스윙 '예측'), Allen Example 26-2(고정 회로로 ±0.5 V 제한 평가)가 모두 이 꼴이다.
- 손계산 근사는 하나다. 극단에서도 소자 전류를 정지전류로 두고 V_DSsat(I_q)로 검사한다. 이것은 class-A 출력의 β 쪽이고 부하가 순수 C일 때(DC에서 출력 전류 0) CLM 범위 안에서 정확하다. R·전류원 부하가 있거나 σ 쪽이면 극단 전류 = I_β(V_end) ± I_load(V_end)라서 근사다.
- 계획과의 대응: 감사 F1(공급 능력을 동작점 전압이 아니라 범위 끝 전압에서 잴 것)과 같은 물리다.

## 2. 용어 정의표

| 용어 | 정의 | 영역(DEC-67) | 정의하는 SPICE 해석 | 엔진 자리(현행) |
|---|---|---|---|---|
| 정지전류(quiescent, I_Q) | 신호 0(입력 = 공칭 동작점)에서 가지 전류 | DC | `.op` | θ 전류 변수의 봉인점 값 |
| 정상상태 전류(steady-state, DC) | 입력·출력이 정지점이 **아닌** 어떤 일정 상태에서 충분한 시간 뒤의 가지·포트 전류(예: 출력을 범위 끝 V로 몬 상태에서 R_L·I_L이 끄는 전류). 정지전류는 그 특수형이다 | DC | `.dc`(입력 훑기, 또는 출력 포트를 V에 고정) | DE-1 DC 동작 범위 필드(선형 감도 끝) |
| 방향별 공급 능력 I_cap,dir(V) | 출력 포트를 V에 고정하고 입력을 허용 범위 끝까지 몬 DC 해에서, 포트를 고정하는 원천이 내보내는(받는) 순 전류. O-26 (1)·DEC-65 정의를 'V = 범위 끝'·'순 전류'로 넓힌 것(감사 F1·F2 -- 사용자 결정 D6 대기) | DC | `.dc` | DEC-65 '엔진 계산 미결(U-115)' |
| 대신호 전류(large-signal) | 소신호 선형 근사가 맞지 않는 진폭에서의 전류. DC 범위 끝(정적)과 과도(동적)를 모두 포함하는 상위 말이다. 엔진에서는 이 말을 쓸 때 정적인지 동적인지를 반드시 붙인다 | DC 또는 ls | `.dc`(정적) / `.tran`(동적) | -- |
| 동적 전류(dynamic, transient) | 시간에 따라 바뀌는 전류. 용량 성분 i_C = C·dv/dt를 포함한다 | ls | `.tran` | 엔진 칸 0(O-122) |
| 슬루 전류(slewing) | 대신호 계단에서 한 노드를 충·방전하는 전류가 상한에 묶인 상태의 전류(꼬리 전류가 한쪽으로 다 넘어감, 출력단이 최대 구동). 준정적 근사로는 그 순간 전압에서의 I_cap,dir(V)과 같다 | ls(근사 시 DC 능력과 비교) | `.tran`(전 폭 계단, 20-80 % 기울기 -- O-122) | oracle만 |
| 피크 전류(peak) | `.tran`에서 \|i(t)\|의 최댓값(요구 쪽: 부하가 요구하는 피크, 능력 쪽: 회로가 낼 수 있는 피크) | ls(정의), DC(준정적 상한) | `.tran`(정의), `.dc` 극단(준정적 상한) | `load_peak_amp`(감사 D3 재정의 대기) |
| 소신호 요구 | 전류가 아니라 gm·gds 요구(gm ≥ 2π·GBW·C 등). gm/ID 선택을 거쳐서만 전류가 된다 | ss | `.ac`·`.noise`(`.op` 위) | DEC-70 gm_req(C) 제약, 매크로 |

## 3. 사용자 가설 판정

- 가설: "두 전류를 모두 감당하려면 두 θ점 고정이 필요하다."
- 판정: **부분적으로 맞다.**
  - 맞는 부분
    - 두 **상태**를 모두 검사해야 한다. 정지 상태는 `.op`에서 ss 요구(GBW·PM·rout·안정도)를 본다. 극단 상태는 `.dc`/`.tran`에서 범위 끝 정상상태 요구와 동적 요구를 본다.
    - class-AB에서는 정지전류와 출력 W가 서로 다른 요구(정지 = ss·교차 왜곡, W = 피크)로 정해진다. 실무에서 W를 '피크 상태'에서 계산하는 것도 사실이다(Allen L040 Ex.5.5-1, philipalcorn/gmid, Xie & Chen).
  - 틀린 부분: 두 번째 **설계점**은 필요 없다. 피크 상태는 W를 공유하고, 단자 전압은 회로가 정한다. 그래서 피크 상태의 θ(ln IDu_peak = ln(I_peak·L/W))는 정지 θ와 회로 DC 범위 끝의 함수다. 독립 변수가 아니다. 이것을 독립 θ로 두면 W에 생산자가 둘이 된다. 정지점은 W = I_q·L/IDu_q를 내고, 피크점은 W = I_pk·L/IDu_pk를 낸다. 둘을 맞추는 등식이 하나 더 생기므로 결국 같은 자유도가 남는다(§5 (C)).
  - 수학적으로 같은 표현: 꼴 (C)는 피크 상태 변수에 'W 공유 + 극단 단자 전압 = 회로 DC 범위 끝'이라는 등식 제약을 붙인 것이다. 이 등식을 소거하면 꼴 (B)의 θ 제약 g(θ) = I_cap,dir(V_end; θ) − 요구 ≥ 0이 된다.
- 진짜로 '여러 설계 조건'이 필요한 경우는 바이어스 설정 자체가 다른 동작 모드다. 가변 바이어스, 모드별 전류 설정, PVT 코너가 그렇다. 이때는 Hershenson §IX처럼 W는 공유하고 조건마다 전류·제약을 복제한다. library에 그런 회로가 있는지는 확인하지 않았다(§7).

## 4. 개념 정의안 (부하 구동의 요구·능력 분리)

- **D-1 요구(spec 양, 회로 무관)**: 출력 포트 p·방향 d마다 셋.
  - 정상상태 요구 R_ss,d(V) [DC, `.dc`]: 출력을 범위 끝 V에 고정했을 때 응용 망(DEC-100)이 끄는 전류. 감사 L1′ 그대로다.
  - 동적 요구 R_dyn,d [ls, `.tran`]: C_tot·(dV/dt)_req. 속도 선언이 있을 때만 정의된다. O-122 아래에서는 엔진이 유도하지 않는다. 사용자 손계산 선언 몫(감사 D3) 또는 oracle 판정만 쓴다.
  - 소신호 요구 [ss, `.ac`]: gm·rout 등. 전류 요구가 아니다.
- **D-2 능력(θ 봉인점에서 계산한 graph 필드, writer 하나)**:
  - 방향별 공급 능력 I_cap,d(V; θ) [DC]. 하나의 함수로 정상상태 요구와 동적 요구를 함께 받는다.
  - gm(θ) 등 ss 필드.
- **D-3 조건**:
  - DC: 범위 두 끝 V에서 I_cap,d(V) ≥ R_ss,d(V).
  - 동적(손계산·준정적): I_cap,d(V) ≥ R_ss,d(V) + R_dyn,d. 이 합 규칙은 램프 계단에서 정확한 필요조건이고 사인파에서는 보수적이다(min_current_from_load §1.3).
  - 정확 판정은 `.tran`(oracle).
- **D-4 설계점 하나**: 설계점은 θ(정지점)다. 극단 상태는 같은 W·바이어스의 평가이고 θ 제약으로만 되돌아간다(DEC-70). class-AB에서 W와 I_q가 따로 정해지는 것은 θ의 두 성분(I_q, ln IDu_q)이 두 요구(피크·ss)에 각각 묶이는 것이다.
- **D-5 손계산 계산법(정의와 계산법을 나눔)**:
  - 헤드룸·포화 여유(작은 편차): DE-1 선형 KCL 감도 끝(DEC-103 그대로).
  - 피크 전류(큰 편차, class-AB·σ 방향): 같은 W에서 소자 LUT를 극단 단자 전압(V_GS = 구동단 DC 범위 끝, V_DS = 출력 범위 끝)으로 조회한 값에서 반대쪽 가지 전류를 뺀 순 전류. Allen L040 p.040-3의 K'W/2L(V_DD − V_SS − V_T)² − I_Q를 LUT로 일반화한 꼴이다.
  - 이것은 U-115 규칙 후보로 **관찰**만 적는다. 결정은 O-123 보류 그대로다.

## 5. (A)(B)(C) 비교

| 칸 | (A) 단일 설계점 + 요구를 정지전류 하한으로 변환 | (B) 단일 θ + 극단 상태를 같은 W·바이어스로 평가 → 요구 대비 판정을 θ 제약으로 | (C) 정지 θ와 피크 θ를 동시에 사이징(W 공유 제약) |
|---|---|---|---|
| 물리 정합 | class-A 레일 source β 쪽: I_β(V_end) ≈ I_q(CLM 범위)라 I_q ≥ 요구가 정확한 필요조건(β가 끝에서 포화를 잃지 않을 때). 꼬리 전류 SR = I_tail/C_c: 슬루 노드가 C_c 노드이고 꼬리가 다 넘어갈 때 정확, 기생·출력단 한계가 있으면 근사. **class-AB·σ 쪽은 틀림**: 피크 ≫ 정지(19~658배)라 I_q에 하한이 없다(min_current_from_load §0-1(마)) | 정의(O-26 (1) 확장)와 같은 물리. B-lin은 작은 편차(헤드룸)에 맞다. 큰 편차(피크)에는 B-nl(소자 LUT 극단 조회)이 필요하다 | 같은 물리를 담을 수 있으나, 피크 상태를 자유 변수로 두면 단자 전압이 회로 DC 범위 끝과 어긋나는 비물리 해가 생긴다. 막으려면 등식을 더 넣어야 하고, 그러면 (B)와 같아진다 |
| 교과서·문헌 일치 | 2단 op-amp 교재 관례(Allen·UT·arXiv·Hershenson 식 (37)) | Hershenson §IV-A 스윙 제약, UT 단계 7, Silveira 스윙 예측, Allen Ex.26-2 평가, Allen L040 Ex.5.5-1(극단에서 W 크기) | class-AB 실무의 'W를 피크에서' 표기(Xie & Chen, philipalcorn)가 겉보기로 닮았다. 다만 그 문헌들도 독립 변수 둘이 아니라 'W를 피크 상태 식으로 계산'한다. 진짜 다중 조건은 Hershenson §IX(코너) |
| 손계산 속도 | 가장 빠름(한 줄) | 빠름(B-lin = 봉인점 야코비안 재사용, B-nl = 소자당 LUT 조회 1회) | 느림(피크 상태 변수·등식이 소자마다 더해져 θ 차원이 늘고, 사실상 끝 풀이) |
| design 단순성 | 높음. 단 적용 조건(β·레일 source·class-A)을 갈래로 두어야 한다 | 중간: 능력 필드 하나(DEC-65)와 계산법 둘(lin/nl) | 낮음 |
| 원칙 | ⚠ 원칙 경고: DEC-65(구조 분류를 값 판정에 쓰지 않음) — (A)는 class-A/AB·β/σ 분류로 적용 여부를 갈라야 정확해진다 — 계획 264행, 감사 F3. ⚠ 원칙 경고: O-122 — SR → 전류 하한 변환은 엔진 슬루 경계와 같은 장치다 — user_decisions 849행, DEC-71 (3) "'슬루 하한'은 v6.37 O-122로 없음". 정상상태 요구 몫만 쓰면 둘 다 해당 없음 | DEC-103 정합(설계 = θ, 극단 = 정해진 회로의 섭동). DEC-70 정합(DC 동작 범위 필드 = θ 제약). DC/AC 분리 정합(능력 = DC 필드, 동적 = ls oracle). graph: 능력 필드 writer 하나. ⚠ 원칙 경고: O-109 C1(끝 풀이 Newton 금지) — B-nl이 회로 전체 끝 풀이가 되면 위반한다. 소자 단위 LUT 닫힌 꼴(구동단 범위 끝을 DE-1에서 READS)일 때만 정합 — 계획 DEC-70 문언 "끝 풀이(Newton)는 어느 층에도 두지 않는다" | ⚠ 원칙 경고: graph 단일 정본 규칙 1 — W(또는 피크 상태 IDu)에 생산자 둘 — 프로젝트 CLAUDE.md §graph 1·3. ⚠ 원칙 경고: DEC-103 — 피크 상태는 '정해진 회로를 흔드는 반응'인데 설계점으로 다룬다 — 계획 302행. ⚠ 원칙 경고: gm/ID 손계산 속도 원칙 — θ 차원 증가 |
| **권고** | 출발값·필요조건(레일 source β 쪽 정상상태 요구)으로만 | **채택**: 판정·제약의 정본 꼴 | 기각(다중 바이어스 모드·코너가 생길 때만 Hershenson §IX 꼴로 다시 검토) |

## 6. 계획 규칙과의 관계

| 규칙 | 닿는 곳 | 비고 |
|---|---|---|
| DEC-65(264행) | 능력 함수 I_cap,d(V)의 정의 자리다. 정상상태 요구와 비교하려면 '동작점 전압 → 범위 끝 V', '그 방향 전류 → 순 전류'로 넓혀야 한다(감사 F1·F2·D6과 같은 결론). 구조 분류는 보고만 한다 | 동적 요구도 준정적으로 같은 함수와 비교된다 -- 새 필드가 필요 없다 |
| DEC-70(269행) | (B)의 되먹임 자리다. 문언은 "DC 동작 범위 필드(방향 최대 전류, 스윙·입력 창 끝)"를 θ 제약 판정 입력으로 이미 적었다. 슬루는 θ 제약이 아니다(O-122) -- 그대로 둔다 | -- |
| DEC-71 (3)(270행) | 블록 전류 입력 'KCL·선언'에 정상상태 요구(레일 source β 쪽 필요조건)가 들어갈 자리가 있다(감사 §7.1-7). '슬루 하한' 없음은 그대로다 | -- |
| DEC-71 (4)(270행) | 역산 갈래 (a) '필요 gm → gm/ID'와 나란히 '필요 피크 전류 → W 하한 → 주어진 I_q에서 IDu_q 상한(= gm/ID_q 하한 쪽)'을 역산하는 갈래가 class-AB에 해당한다. θ 하나 안의 정의역 자르기이고 두 번째 θ가 아니다 | 미결 -- 사용자 결정(계획 개정 대상, 이 조사는 고치지 않음) |
| DEC-103(302행) | 설계점 = θ(정지), 극단 상태 = W·바이어스 고정 평가. 이 조사의 결론과 같다. 덧붙일 점: '틀만 맞으면 근사 오차 감수'의 '근사'가 선형화라면, class-AB 피크(19~658배)는 근사 범위 밖이다 → 같은 틀(W 고정) 안에서 비선형 소자 LUT 평가가 필요하다 | 원래 취지와 다름 아님(틀은 같고 계산법만 나눔). 계산법 선택은 사용자 결정 |
| U-115(2263행)·O-123 | 능력 함수의 엔진 손계산 규칙이다. 이 조사는 후보 꼴 하나(§4 D-5: 같은 W, 극단 단자 전압 LUT 조회 − 반대 가지)를 관찰로 더한다. 기존 후보 (나) `dc_current_basis` θ 전류 합은 동작점 전압·총 전류라 F1·F2가 남는다(감사 §1 28행) | O-123 보류 그대로 -- 결정하지 않았다 |
| O-122 | 동적 요구는 엔진이 유도하지 않는다. 교과서 관례(A)와의 차이는 사실로만 둔다. Boser 절차(설계 → 전 폭 계단 검증 → 반복)는 O-122 + 'oracle 슬루 FAIL 뒤 처리'(O-122 확인 사항)와 같은 모양이다 | FAIL 뒤 처리 정의 여부는 확인하지 않았다(§7) |

## 7. 미확인

1. Jespers & Murmann 2017, Murmann EE214/EE315 노트, Razavi, Johns-Martin, Sansen: 원문을 열람하지 못했다. 슬루·스윙 처리의 쪽 번호가 없다. 위 결론은 Silveira·Hershenson·Allen·Boser·UT 원문으로만 세웠다.
2. Hershenson 식 (37)의 정확한 기호: PDF 수식이 이미지라 텍스트로 뽑지 못했다. 바이어스 전류에 대한 두 부등식이라는 것까지만 확인했다.
3. Chen TCAD 2022, BAG, Chen 2024 class-AB gm/ID 논문: 찾지 못했다.
4. Xie & Chen의 정지 22 µA 점 gm(안정도 실제 판정값): 원문에 없다.
5. library에 바이어스 모드가 여럿인 회로(꼴 (C)가 맞는 경우)가 있는지 조사하지 않았다.
6. 준정적 근사(슬루 중 노드 전류 = 순간 전압의 DC 능력)의 오차는 측정하지 않았다. 내부 노드 C_c 슬루, 다단 경로 지연, 기생 C가 있으면 어긋난다. 정확값은 oracle `.tran`이다.
7. O-122 '확인 사항'(oracle 슬루 FAIL 뒤 처리가 계획에 정의됐는지)은 확인하지 않았다.

## 8. 원칙 점검 (이 조사의 권고)

| 원칙 | 판정 | 근거 |
|---|---|---|
| graph 단일 정본 | 지킴: 능력 = DEC-65 필드 하나(writer 하나), 요구 = spec READS. (C) 기각 이유가 규칙 1. 새 cache·사본 권고 0 | §4·§5 |
| DEC-103 | 지킴: 설계 = θ, 극단 = 고정 회로 평가. 계산법(lin/nl) 구분은 '틀' 안의 선택 | §5 (B) |
| DC/AC 분리 | 지킴: 정상상태 = DC `.dc`, 동적 = ls `.tran`, 소신호 = ss | §2 |
| O-122 | 지킴: 동적 요구를 엔진이 유도하는 권고 없음 | §0-6 |
| 상수 발명 금지 | 지킴: 수치는 원문·앞선 실측 인용뿐 | §1 |
| 회로 이름 | 지킴: 규칙은 구조(레일 source·포트·방향)로 | §4 |
| 관례를 정의로 쓰지 않음 | 지킴: 교과서 (A)는 '관례'로 표기, 정의는 O-26 (1) 확장 | §5 |
| 원래 취지와 다름 | 해당 없음(새 결정 권고 없음). 관찰: DEC-103 '근사 오차 감수'가 큰 편차에는 성립하지 않음 -- 사용자 판단 대상 | §6 |
