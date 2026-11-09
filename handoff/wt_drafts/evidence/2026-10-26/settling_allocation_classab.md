# 정착 배분(t_slew 10 ns / t_lln 30 ns)은 class-AB의 일반 spec인가 -- 문헌 조사 (O-138)

- 작성: 2026-10-26, 조사 agent(opus). 파일 수정 없음, 이 증거 파일만 씀.
- 질문(사용자 원문): "배분을 넣고, 이게 class-ab의 일반적인 spec인지 조사를 통해 확인해줘."
- 임시 파일: `wt/_scratch_settlealloc/` (내려받은 강의 PDF·텍스트 추출본)

## 0. 판정 (요약)

**일반 spec이 아니다. 저자가 고른 설계 배분(design budget)이다.**

1. 문헌에서 spec은 **전체 정착 시간 + 오차 띠**(+ static 오차)다. class-AB 논문도 같다. 슬루/선형 구간 나눔은 spec이 아니다. 해석 모형이거나 설계 절차의 **출발 가정**이다(§1).
2. 배분 비율에 표준값은 없다. 문헌마다 50 %, 1/3, 63 % 등으로 다르다. 그리고 모두 "가정하고 실측으로 고쳐 반복한다"는 단서가 붙는다(§1.3). 원리 있는 결정 규칙은 class-A 단일단의 "슬루 전류 = gm 전류" 전력 최적점 하나다. 이 규칙은 슬루 손계산이 필요하다. 그런데 엔진은 O-122에 따라 슬루를 다루지 않는다(§1.4).
3. class-AB라서 슬루가 짧다는 것은 정성 동기일 뿐이다. 10 ns라는 값의 근거는 없다. Xie·Chen 회로 자신의 판독 기울기를 보면 슬루가 상당했다. 2단 Miller 구조에서는 내부 Cc 슬루(I₁/Cc)가 남기 때문이다(§2).
4. **저자 as-built가 배분 유도값을 지키지 않았는데도 spec을 만족했다.** 배분이 요구한 루프 교차는 36.6 MHz였다. 실제 루프 UGF는 28.0 MHz였고, 정착은 37.885 ns ≤ 40 ns로 통과했다(§3.3). 그러므로 배분에서 유도한 GBW는 필요조건이 아니다. 하드 경계로 쓰면 맞는 설계를 거부한다.

---

## 1. 정착 시간을 슬루 + 선형으로 나누는 방식

### 1.1 저장소 원문

| 출처 | 쪽·식 | 인용 | 성격 |
|---|---|---|---|
| Xie & Chen 2019, `assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf` | p.3 §III.A 식 (1)(2) | "Assume ts = tslew + tlln ... The Class AB structure in the second stage can provide instantaneous current. Therefore, we allocate tslew and tlln to 10ns and 30ns respectively, to relax the bandwidth requirement and reduce the current consumption." / "tlln ⋅ωc = 6.9 (2) should be satisfied [8]" | **설계 배분**("Assume", "we allocate"). spec은 식 (1) εd ≤ 0.1 %, ts ≤ 40 ns와 Table I p.1이다 |
| 같은 원문 | 참고문헌 p.5 | [3]~[9]가 모두 "N. Sun, ... 2019" 강의 노트다. [8] "Step response". 감사의 글은 "Dr. Nan Sun"에게 한다 | 웹 출판처를 찾지 못했다(paper.md 머리 2026-10-14 기록). UT Austin 강의 과제 보고서로 **추론**한다. 일반 관례의 근거로는 무게가 약하다 |
| Leung 1999 (nmcnr), `assets/library/sources/nmcnr_amplifier__leung_1999/` | p.601 | "As the settling time (Ts) is composed of the slewing and quasi-linear period [6]" ([6] = Kamath, Meyer, Gray 1974) | **해석 분해**다. spec은 Table 1의 SR·settling time 측정값이다 |
| Hogervorst 1994 (class-AB 출력 r2r, heldout), `assets/heldout/sources/r2r_opamp__hogervorst_1994/` | 저널 p.1511~1512 | "The 1% large-signal settling time for the compact opamp with Miller compensation is 440 ns, for a capacative load of 10 pF and a step of 1 V." | **class-AB 출력 회로의 spec이 전체 정착 시간 하나**다. 배분은 없다 |
| Lee 2007 (ngcc) | p.24~25 | "unity gain bandwidth, phase margin, and settling time ... 10MHz, 59˚, and 120nsec" | 전체 정착 + GBW·PM을 따로 보고한다 |
| `references/gm-id-methodology.md` §10.3 (Seth & Murmann 계열) | 685행 | "Settling spec은 ... `|εd(t)| < 0.1% (t>2.5ns)` 같은 **직접적인 시간영역 조건**으로 검증" | spec = 시간영역 조건 |

### 1.2 웹 문헌

| 출처 | 위치 | 내용 | 성격 |
|---|---|---|---|
| B. Kamath, R. G. Meyer, P. R. Gray, "Relationship between frequency response and settling time of operational amplifiers," IEEE JSSC SC-9(6), pp.347-352, Dec. 1974, [doi:10.1109/JSSC.1974.1050527](https://doi.org/10.1109/JSSC.1974.1050527) | 원문 미열람(유료) | Boser 강의 OTA I 슬라이드 60~62가 이 논문의 doublet 정착 표기를 인용한다 | 정착 해석 모형. 배분 규칙은 아니다(원문 미확인) |
| B. Boser, EE240B "OTA III" (UC Berkeley, 2016), [PDF](https://www2-bsac.eecs.berkeley.edu/~boser/courses/240B/lectures/M10%20OTA%20III.pdf) | 슬라이드 15·16·17 | s.16 "ts = tslew + tlin ≈ (|V_xd,step| − V*)/(β·SR) − τ·ln(ε_d · c·V_id / V_od,lin)" / s.17 "Design Procedure with Slewing: 1. Start by assuming a slewing time, e.g. 50% of ts 2. Design and verify that linear settling completes within tlin (apply only small steps ...) 3. Now verify with a full-scale input step and check the actual ratio of tslew/tlin 4. Iterate until the design and verification match" | 배분은 **설계 절차의 출발 가정**이고 실측으로 반복해 고친다. 예시 값은 50 %다 |
| B. Boser, EE240B "OTA I: Step Response", [PDF](https://www2-bsac.eecs.berkeley.edu/~boser/courses/240B/lectures/M06%20OTA%20I.pdf) | s.32, s.43, s.49 | s.32 단극 동적 정착 표: 1 % → 4.6, **0.1 % → 6.9**, 0.01 % → 9.2 (ts/τ). s.43 "Settling Time versus f_p2/f_u, ε_d = 0.1 %" 곡선: f_p2/f_u ≈ 2.1 이상에서 ts·ω_u < 6.9이고, 최소 ≈ 3.5는 f_p2/f_u ≈ 3.4에서 나온다(그림 판독). s.49 "Settling time (single pole, no slewing)" 설계 예 | 6.9는 단극 선형 정착의 표준 상수다(ln 1000). 설계 예는 슬루 없음을 가정한다 |
| E. Ng, K. Oo, "A Fast-Settling, High Dynamic Range Fully Differential OTA," EE240 Class Project, Berkeley, 2002, [PDF](https://www.ocf.berkeley.edu/~eng/classes/240Project.pdf) | §III 3) | "r := 0.63, tslew := r·ts" ... "Iss := max(Iss, 2·ID1)" ... "We then assign 63% of dynamic accuracy to slewing to achieve maximum power efficiency" | **전력 최적 배분 규칙**의 실례다. 슬루가 요구하는 꼬리 전류와 선형 gm이 요구하는 전류(2·ID1)를 맞추는 점을 고른다. class-A 텔레스코픽 단일단이고 63 %를 슬루에 준다 |
| M. Miyahara, A. Matsuzawa, "A Performance Model for the Design of Pipelined ADCs with Consideration of Overdrive Voltage and Slewing," IEICE Trans. Fundamentals E91-A(2), pp.469-475, 2008, [PDF](https://www.ssc.p.isct.ac.jp/private/publications/2008/IEICE/E91-A_miyahara.pdf) | p.470 1장, §4 식 (19)~(22) | "the settling time reported in [2] assumed that the time of slewing is one third of the settling time without slewing." / 식 (22) "tset2 = tslew + ts ns" / "the error reported in [2] is about 10% in the 90 nm process and is about 30% in the 180 nm process" | 고정 비율(1/3)은 단순화다. 오차가 10~30 %라서 회로값(Veff, Vsig, β)에서 t_slew를 직접 유도하는 쪽으로 바꿨다 |
| M. Dei, F. Gagliardi, P. Bruschi, "Slew-Rate Enhancement Techniques for SC Fast-Settling Amplifiers: A Review," Chips 3(2):98-128, 2024, [doi:10.3390/chips3020005](https://doi.org/10.3390/chips3020005) | 본문 미열람(403) | 검색 요약: 실제 상황에서 SR 강화 방식을 고를 명확한 지침이 부족하다는 취지 | 표준 배분 규칙이 없다는 방증이다(본문 미확인) |

### 1.3 배분은 spec인가, 설계 선택인가

- **설계 선택이다.** spec 자리(Table I, 표 머리, 비교표)에 배분이 나오는 문헌은 찾지 못했다. Xie·Chen도 spec은 식 (1)이고, 배분은 "Assume … we allocate"다.
- 일반 비율 관례는 없다. 50 %(Boser 예시), 1/3(Matsuzawa 2007, Miyahara 2008 인용), 63 %(Ng·Oo 전력 최적), 25 %(Xie·Chen)로 흩어져 있다. 모두 반복 또는 회로값 유도로 대체되는 출발값이다.

### 1.4 원리 있는 결정 규칙

1. **물리 전이점(규칙이지 선택이 아님)**: 슬루는 선형 응답의 기울기가 SR을 넘는 동안만 일어난다. 끝나는 점은 차동 입력이 V*(선형 범위)로 줄어드는 때다(Boser s.15~16). 그래서 SR·V*·τ·계단이 정해지면 t_slew/t_lin 비율은 **결과로 정해진다.** 자유 변수는 SR과 ω_c(곧 전류·Cc)이고, 비율 자체는 자유 변수가 아니다.
2. **전력 최적(class-A 단일단)**: I_tail(슬루 요구) = 2·I_D1(gm 요구)이 되도록 고른다(Ng·Oo). 이 규칙이 성립하려면 SR과 gm이 같은 전류를 공유해야 한다. class-AB에서는 순간 슬루 전류가 정지전류에 묶이지 않는다. 그래서 같은 식이 성립하지 않는다. 성립 조건은 2단 Miller의 내부 Cc 슬루(I₁/Cc)뿐이다.
3. **2차 계의 최적 감쇠**: 같은 ω_c에서 f_p2/f_u ≈ 3.4 부근이 정착을 최소화한다(Boser s.43, ts·ω_c ≈ 3.5 대 단극 6.9). 이것은 PM 설계 규칙이지 시간 배분 규칙이 아니다.

## 2. class-AB에서 달라지는 점

| 출처 | 내용 |
|---|---|
| Xie & Chen p.2 §II.B | "by using the designed Class-AB output stage, instantaneous current will can be provided and therefore, less current is need for slew requirement." 근거는 정성뿐이고 10 ns라는 수치의 근거는 없다 |
| J. Kim, S. Song, J. Roh, "A High Slew-Rate Enhancement Class-AB OTA for SC Applications," IEEE Access 2020, [doi:10.1109/ACCESS.2020.3044608](https://doi.org/10.1109/ACCESS.2020.3044608) ([PDF](https://pdfs.semanticscholar.org/848c/68514b114886b1455296ce5391c7d093cd94.pdf)) | §I: "the transient response of the OTA circuit can be divided into deadtime, slewing, and settling ... The settling time ... is defined as the sum of the times required for each period." 비교표(Table)는 "0.1 Settling Time (µs)" 전체 값, SR, UGBW를 **따로** 보고한다. 배분은 없다 |
| Hogervorst 1994 (class-AB 출력) | spec·보고 = 1 % 대신호 정착 전체(440 / 275 ns) |
| Oregon State 특허 US 11,595,009 "Slewing mitigation apparatus for SC circuit", [Justia](https://patents.justia.com/patent/11595009) | 검색 요약: class-AB OTA는 정착 개선에 쓰일 수 있다는 배경 서술 |
| 2단 Miller 슬루(교과서 표준, Allen-Holberg 꼴 SR = min(I₅/Cc, I₆/(C_L+Cc))) | **원문 쪽 미확인.** class-AB 출력단은 둘째 항(출력 전류 한계)만 푼다. 첫째 항 I₁/Cc는 그대로 남는다 |

**Xie·Chen 회로 자체의 산술 점검(추론, 1차 근사)**

- 측정 루프 UGF 28.0 MHz(p.4 §IV.C)에서 ω_c = 1.76×10⁸ rad/s이고 τ = 5.68 ns다.
- 순수 선형 응답이라면 Vod 1.2 V 계단의 20-80 % 평균 기울기는 0.72 V / (τ·ln 4 = 7.9 ns) = **91 V/µs**다.
- 판독은 **42.5 / 42.9 V/µs**다(`library_sr_from_sources.md` §1.3). 구간별로는 20-50 % 47.5, 50-80 % 38.9로, 선형 예측 135 / 69보다 모두 낮다.
- → 원문 회로도 상당한 시간을 슬루한다. class-AB 출력이 있어도 슬루가 무시할 만하다는 근거는 원문에 없다. 원인은 내부 Cc 슬루로 추론한다. 차동 43 V/µs × Cc 0.5 pF이면 한쪽 약 11 µA다. 미확인이다.
- **"class-AB는 정착이 선형 구간에 지배된다"를 일반 원칙으로 적은 문헌은 찾지 못했다.** 찾은 것은 "class-AB가 슬루를 개선한다"는 정성 서술뿐이다.

## 3. 선형 정착 시간과 필요 대역폭

### 3.1 1차(단극)

- 공식: t_lin = τ·ln(1/ε), τ = 1/ω_c, ω_c = β·ω_GBW(루프 이득 교차 = 폐루프 −3 dB 대역)
  - 출처: Boser OTA I s.32·s.49 "τ = C_Ltot/(β·g_m)", Xie·Chen 식 (2)(3) "gm1 = ωc·Cc/β"
- ε = 0.1 %이면 ln 1000 = 6.908이다. 표준이다.
- 슬루 뒤 선형 구간은 전체 계단이 아니라 남은 V_od,lin에서 시작한다. 그래서 t_lin = τ·ln(V_od,lin / (ε·c·V_id))이고 6.9τ보다 짧다(Boser M10 s.15~16). Xie·Chen 식 (2)의 6.9는 이 점에서 **보수적**이다.
- 앞먹임 영점까지 넣으면 ln 안에 (1 − β·C_f/(C_f + C_L)) 인자가 붙는다(Boser OTA I s.37·s.49).

### 3.2 2차(PM 영향)

- 두 극 루프 T = ω_c / (s(1 + s/ω_p2))의 폐루프는 ζ = ½·√(ω_p2/ω_c)다. PM = atan(ω_p2/ω_c)다(Xie·Chen p.4 §III.B와 같은 근사, "Let PM be 70°, ωp2/ωc = 2.8").
- ε = 0.1 %에서 ts·ω_c는 다음과 같다(Boser OTA I s.43 그림 판독).
  - f_p2/f_u < 2이면 6.9보다 크다(덜 감쇠).
  - 약 2.1~10이면 6.9보다 작다.
  - 최소는 약 3.5이고 f_p2/f_u ≈ 3.4에서 나온다.
- 그래서 "t_lin·ω_c = 6.9"는 2차에서 필요조건이 아니다. PM에 따라 더 작은 ω_c로도 정착할 수 있다. doublet(극-영점 짝)이 있으면 느린 꼬리가 생긴다(Kamath 1974, Boser s.60~62).

### 3.3 current_reuse 수치 대조 (ε = 0.1 %, t_s = 40 ns, β = 0.48)

| 근거 | 루프 교차 f_c | 증폭기 GBW = f_c/β | 비고 |
|---|---|---|---|
| (가) 배분 t_lln 30 ns | 6.908/30 ns → **36.6 MHz** | 76.4 MHz | 원문 p.4 값과 같다 |
| (다) 배분 없음(t_slew = 0, 단극) | 6.908/40 ns → **27.5 MHz** | 57.3 MHz | 단극 모형 아래의 하한. 슬루가 끼면 더 느려지므로 단극에서는 필요조건이다 |
| 2차 최적 감쇠(이론 최소) | 3.5/40 ns → 약 13.9 MHz | 약 29 MHz | Boser s.43 판독. 실제 PM 제약 아래에서는 도달하기 어렵다 |
| **원문 as-built** | **28.0 MHz**(PM 60.557°) | 약 58 MHz(β 0.48 가정) | 정착 **37.885 ns 통과**. (가)의 36.6 MHz는 **못 지켰다** |

→ 저자 회로는 (가) 유도값 아래에서 spec을 만족했다. (다) 단극 하한(27.5 MHz)과는 거의 같다. 배분 유도 GBW를 경계로 쓰면 원문 회로 자신을 FAIL시킨다.

## 4. 엔진에서의 처리 -- 대안 비교

공통 전제:
- 정착 spec = `constraints[]` `.tran` `settle_s` ≤ 40 ns, ε 0.1 %, 실제 최종값 기준(O-132·O-134). 판정은 oracle이 한다.
- 매크로 활성(S 분류)에는 GBW 목표가 필요하다(`r5r6_prototype.md` §2.2 "gbw_target_hz가 선언되지 않아 매크로가 비활성").

| 안 | 물리 정합 | 손계산 일치 | design 단순성 | 실측(library) | 원칙 |
|---|---|---|---|---|---|
| (가) 사용자 지정 배분(10/30 ns)을 spec으로 → ω_c = 6.9/t_lln | 낮다. 배분은 SR·V*·τ로 정해지는 결과인데 이 안은 그것을 고정값으로 박는다. 2차 효과가 없다 | 원문 손계산(p.3~4)과 같다 | t_slew 10 ns는 소비자가 0이다(O-122로 엔진은 슬루를 다루지 않는다). t_lln만 쓰인다 | 원문 as-built 28 MHz < 36.6 MHz인데 통과 → 경계로 쓰면 오거부 | ⚠ 원칙 경고: 논문 값 그대로 인용 금지 — 배분은 spec이 아니라 저자의 설계 선택이고, 사용자 지정이어도 'spec'으로 두면 판정 원천이 둘(settle_s와 GBW 경계)이 된다 — Xie·Chen p.3 "Assume … we allocate", O-133 원천 하나 선례. ⚠ 원칙 경고: 만들면 배선 — t_slew 필드는 소비자 0 — O-122 |
| (가′) 같은 값을 **손계산 출발 목표**로만 둔다(판정·경계 아님, '사용자 지정 설계 배분' 표기) | 중간. 출발점일 뿐이고 판정은 oracle이 한다 | 원문과 같다 | 필드 하나(t_lln 또는 ω_c 목표)와 writer 하나 | 출발이 원문보다 빡빡하다(36.6 대 28 MHz). 전력이 과하게 잡힐 수 있다 | ⚠ 원칙 경고: 상수 발명 금지 — 30 ns는 회로에서 유도된 값이 아니다(사용자 지정이면 허용되나 근거는 저자 선택) — §1.3 |
| (나) 엔진 규칙으로 배분을 유도(전력 최적 등) | 높다(class-A 단일단). class-AB나 2단 Miller에서는 식이 달라진다 | 슬루 손계산이 필요하다 | 복잡하다. 셀 종류별 슬루 모형(O-122가 지운 것)이 필요하다 | 없다. 슬루 손계산 0.28~28배 오차(O-122 근거) | ⚠ 원칙 경고: O-122 — 엔진은 슬루에 관여하지 않는다 — `user_decisions.md` O-122. 문헌의 최적 배분 식은 class-A 전용(Ng·Oo)이고 class-AB 일반식은 찾지 못했다 |
| **(다) 정착 spec만. 엔진은 ω_c 하한을 '추정'으로 낸다(배분 0 → ω_c,est = ln(1/ε)/t_s, GBW_est = ω_c,est/β)** | 단극 모형에서는 필요조건이다(슬루는 정착을 늦추기만 한다). 2차에서는 근사다(추정 표기) | 표준 단극 공식(Boser s.32, Xie·Chen 식 (2)의 t_lln → t_s) | 가장 단순하다. 입력은 spec(t_s, ε)과 graph의 β뿐이다. 새 상수가 없다 | 27.5 MHz ≈ as-built 28.0 MHz. 원문 회로를 통과시킨다 | 상수 발명 없음. 판정은 oracle 그대로다(fail-closed 유지). 조건: GBW 추정을 spec `gbw_target_hz`에 사본으로 쓰지 않고 settle_s·β를 READS하는 **graph 필드 하나(writer 하나)**로 둔다(graph 단일 정본). O-122 Q3(동적 요구 판정) 재검토와 충돌하는지 확인이 필요하다: 이 값은 판정이 아니라 분류·출발 목표다 |
| (라) 사용자가 GBW를 직접 spec으로 | 사용자 값에 따라 다르다 | -- | 단순하다 | 원문에 GBW spec이 없다(Table I은 결과 28 MHz뿐) | ⚠ 원칙 경고: 원천 하나 — 정착 spec과 같은 물리 요구(동적 오차)의 둘째 원천이 된다 — O-133(gain 54 dB 삭제) 선례. ⚠ 논문 값 인용 금지 — 28 MHz는 결과값이다 |

**권고: (다).**
- 근거는 다음과 같다.
  - 새 상수가 없다(spec t_s·ε와 graph β만 쓴다).
  - 단극 모형에서 필요조건이다.
  - 원문 as-built와 정합한다(27.5 대 28.0 MHz).
  - 판정은 oracle settle_s 하나로 남는다.
- 사용자가 10/30 배분을 꼭 남기려 하면 (가′)로만 둔다(출발 목표, '사용자 지정 설계 배분', 판정 아님). (가) spec 형태는 권하지 않는다.
- 남는 결정:
  1. β 값 출처: 출발 전 β는 선언 용량에서 Cin을 무시한 0.5로 잡을지, 점마다 Cf/(Cf + Cs + Cgg)로 graph에서 읽을지 정해야 한다. 후자를 권한다(원문도 0.48로 보정).
  2. 2차 보정(Boser s.43 꼴)을 넣을지 정해야 한다. 넣으면 PM 의존이라 출발 목표가 낮아진다. 권고는 '안 넣음, 추정 표기'이고 oracle에 맡긴다.
  3. O-122 Q3와의 관계를 정해야 한다.

## 5. 결론

- "t_slew 10 ns / t_lln 30 ns"는 class-AB(또는 SC OTA)의 **일반 spec이 아니고 관례 비율도 아니다.**
  - Xie·Chen이 강의 과제 꼴 보고서(추론)에서 쓴 설계 배분이다.
- 근거:
  1. 문헌의 spec은 전체 정착 시간과 오차 띠다(Hogervorst 1994, Kim·Song·Roh 2020, Lee 2007, Xie·Chen 자신의 Table I).
  2. 슬루와 선형 정착 분해는 해석 모형이다(Kamath 1974, Leung p.601). 배분은 반복으로 고치는 출발 가정이다. 그 값은 50 %, 1/3, 63 %, 25 %로 흩어져 있다(Boser M10 s.17, Miyahara 2008, Ng·Oo 2002, Xie·Chen).
  3. class-AB에 맞춘 배분 규칙은 문헌에서 찾지 못했다.
  4. 원문 as-built가 배분 유도 대역(36.6 MHz)보다 낮은 28 MHz로 spec을 만족했다.
- 그래서 배분을 spec이나 경계로 넣지 않는다. 정착 spec에서 배분 없이 GBW 하한을 '추정'으로 유도하는 (다)를 권한다.

## 6. 미확인

1. N. Sun "Step response"(2019, Xie·Chen [8]) 원문을 찾지 못했다(웹 검색 2회). 식 (2)의 원래 맥락은 확인하지 못했다.
2. Kamath·Meyer·Gray 1974, Yang·Allstot 1990 "Considerations for fast settling operational amplifiers", Dei 외 2024 review는 본문을 열지 못했다(유료 또는 403). Kamath는 Boser 슬라이드의 2차 인용으로만 확인했다.
3. 교과서(Johns & Martin, Razavi, Gray-Meyer, Sansen, Allen-Holberg)의 슬루와 선형 정착 서술은 쪽 번호를 확인하지 못했다. §2의 2단 SR = min(I₅/Cc, I₆/(C_L + Cc))는 표준식으로 적었고 원문 대조는 하지 않았다.
4. Berkeley EE240B Lecture 10 "Settling Design"(Alon, sp18)은 로그인이 필요해 열지 못했다. 검색 요약에는 "slewing fraction을 가정하고 반복"과 2차 최적 K ≈ 3.3이 있었다. 본문은 미확인이다.
5. Boser s.43의 최소점(≈ 3.5 at ≈ 3.4)은 저해상도 그림 판독이다.
6. §2 산술 점검(선형 예측 91 V/µs 대 판독 43)은 단극 근사다. 2차 응답과 내부 Cc 슬루 전류(약 11 µA/쪽)는 추론이다.
7. Xie·Chen이 강의 과제 보고서라는 것은 참고문헌과 감사의 글에서 한 추론이다.
