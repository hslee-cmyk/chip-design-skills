# sf_pushpull_output_opamp -- 동작 조건·정지 원인·ICMR 기능 기준 권고 (회로 분석가, 독립)

- 작성: 분석 agent, 2026-11-01. 저장소·계획·topology·spec·git 쓰기 0(엔진은 import 실행만, master HEAD `08048939`).
- 원자료: `sf_pushpull_output_opamp_files/`
  - `run_engine.py` → `engine_runs.jsonl`(엔진 단계 A·B·층 0, 케이스마다 append)
  - `spice_icmr.py` → `spice_icmr.jsonl`(손계산 설계점 + ICMR servo `.op` 훑기 + 점별 `.tf`), `summarize.py` → `summary.jsonl`
  - `spice_ac.py` → `spice_icmr.jsonl` 끝 행(`step: ac`)
  - case `base`는 R 조율식 결함(입력쌍 헤드룸 무시)으로 버린 실행이다. 판단에는 쓰지 않는다. 판단은 case `v2`만 쓴다.
- 원문: P.E. Allen, Lecture 26 'Buffered Op Amps', Page 26-6 'Source-Follower, Push-Pull Output Op Amp' Fig. 7.1-1
  - 로컬 PDF: `skills/analog-gmid-design/assets/library/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf` p.6(렌더 `pages/p06.png`)
  - 웹: https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf
- 원칙 8 용도 제한: 엔진 인용은 실행 결과(외부 사실)와 재작성 범위로만 쓴다.

## 1. 토폴로지 해석 (connectivity 표 + 원문 p.26-6만, analog-grammar 태그 미사용)

근거: `assets/library/sf_pushpull_output_opamp.topology.md`(topology_to_markdown.py 파생 표), 원문 p.6 그림을 net별로 대조했다. 22 MOS, 5 수동소자, IBias 1개.

| 부분 | 연결(net 기준) | 해석 | 확신도 |
|---|---|---|---|
| 입력단 | M1(g vin_p)·M2(g vin_n), source 공통 TAIL, 꼬리 M3(g NB), M4 diode(NB) + IBias | nmos 차동쌍, 단일 꼬리 전류원. IBias가 M4→M3 거울로 꼬리 전류를 정함 | 높음 |
| 좌측 부하 | vdd–M6–N56–M5–N5–R1a–N1(M1 drain). M6 g = N5, M5 g = N1 | pmos 자기 바이어스 저전압 캐스코드 diode. R1a 강하가 두 게이트 전위 차를 만든다 | 높음 |
| 좌측 출력 거울 | M9(g N5)·M10(g N1) → Y | M1 전류를 Y로 옮기는 캐스코드 거울(소스 쪽) | 높음 |
| 우측 부하 | vdd–M8–N78–M7–N7–R1b–N2(M2 drain). M8 g = N7, M7 g = N2. M11(g N7)·M12(g N2)가 복사 → N12 | M2 전류를 복사 | 높음 |
| nmos 거울 | N12–R1c–N13–M13–N1314–M14–vss. M13 g = N12, M14 g = N13. M15(g N12)·M16(g N13) → Y | M2 전류를 Y에서 빼는 캐스코드 거울(싱크 쪽) | 높음 |
| 1단 출력 | Y = M10 drain ∧ M15 drain, Cc(Y–agnd) | 대칭(전류 거울) OTA 꼴의 단일 고임피던스 노드. Cc는 Miller가 아니라 Y 접지 용량(지배극) | 높음 |
| 출력 버퍼 | M17(g N5)→N17 → M18 pmos follower(g Y, d vss) / M20(g N13)→N20 → M19 nmos follower(g Y, d vdd). N17 → M22 nmos(d vdd, s vout), N20 → M21 pmos(d vss, s vout) | 상보 source follower 두 단의 push-pull. 정지 전류는 VGS 고리로 정해진다: VSG18 + VGS19 = VGS22 + VSG21 | 높음 |
| 되먹임 | topology 안 DC 되먹임 소자 없음. spec feedback.elements = [](β = 1 루프로 PM 정의) | 개루프 증폭기 | 높음 |
| bulk | topology 미선언 → DEC-61·O-188 기본(nmos vss, pmos vdd) | 원문 그림 M18/M21 VDD, M19/M22 VSS 화살표와 같다 | 높음 |

- 이득 경로: vin → (gm1, Y의 캐스코드 출력저항) → Y → 출력 follower 두 단(이득 ≈ 1) → vout.
- 원문 p.6 수치: Rout ≈ 1/(gm21+gm22) ≤ 1000 Ω, Av(0) = 65 dB(IBias = 50 µA), GB = 60 MHz(CL = 1 pF), 'bias currents through M18 and M19 vary with the signal'.
- 원문은 ICMR를 정의하지도 재지도 않는다(p.6 전문; 같은 PDF에서 ICMR 수치는 p.24 Example 26-2 '+1 V to 2 V' 하나뿐인데, 다른 회로·공정의 예제다). 이 회로의 ICMR 기준은 원문에서 유도할 수 없다 → 사용자 선언 대상이다.

### 1.1 입력 공통모드가 움직일 때 먼저 무너지는 소자 (물리 유도)

- 아래 끝(V_cm↓)
  - TAIL = V_cm − VGS1. 먼저 꼬리 M3가 VDS3 < VDSAT3(triode)로 들어간다. 경계: V_cm,lo = VGS1(VSB = V_TAIL) + VDSAT3.
  - 차동 이득은 꼬리 임피던스에 1차로 무관하다(차동 모드에서 TAIL = 가상 접지). 꼬리 전류만 준다.
  - Y 이득 A1 = gm1·R_Y이고 R_Y(캐스코드) ∝ 1/I이다. 그래서 약·중반전에서 gm1 ∝ I이면 A1이 거의 일정하다.
  - **증분 DC 이득은 M3 triode 진입 뒤에도 한참 버틴다.** 꼬리 전류가 크게 줄고 거울 바닥 소자(M6·M8·M11, IR 강하 감소)도 triode에 들어간 다음에야 무너진다.
  - 버퍼 바이어스(M17·M20)는 가지 전류를 복사한다. 그래서 같이 줄어 속도(GBW)가 떨어진다. 이것은 DC 이득 기준이 보지 못하는 AC 양이다.
- 위 끝(V_cm↑)
  - N1 = vdd − VSG6 − I·R1a는 V_cm과 무관하게 고정이다.
  - V_cm이 오르면 TAIL이 오르고 M1·M2의 VDS가 준다. 경계: V_cm,hi = N1 + VGS1 − VDSAT1.
  - 넘으면 입력쌍이 triode가 되어 gm1과 R_Y가 같이 무너진다 → **증분 DC 이득이 급락한다.** 위 끝은 기능 기준이 실제로 묶는 쪽이다.
- 판정: 물리 결정자 = 아래 M3 VDSAT, 위 M1·M2 VDS(= N1 고정점). 아래 SPICE 실측(§3)과 일치한다 → **맞음**.

### 1.2 sky130 1.8 V에서의 물리 실현성 (LUT 실측, `sky130_nfet_pfet_lut_v2_r2.npz`)

- 출력단 VGS 고리: VGS22 + VSG21 = VSG18 + VGS19 ≤ vdd − VDSAT17 − VDSAT20.
- vout = agnd = 0.9 V에서 M21(pmos, body vdd, |VSB| = 0.9)의 문턱은 |VT| ≈ 1.17 V다(SPICE vth, L 0.5 µm). 그런데 N20 ≥ VDSAT20이어야 하므로 VSG21 ≤ vout − VDSAT20 ≈ 0.85 V다 → **M21은 항상 문턱 아래**다.
- 18 µA(Rout ≤ 1 kΩ에 필요한 정지 전류 어림)를 VSG 0.85 V로 흘리는 데 필요한 W·면적(LUT 보간, VDS 0.9):

| L | W | 게이트 면적 |
|---|---|---|
| 0.15 µm | 13.6 µm | 2 µm² |
| 0.5 µm | 34 mm | 16,900 µm² |
| 1 µm | 247 mm | 247,000 µm² |

- spec 면적 예산은 0.02 mm² = 20,000 µm²다.
- 결론: 이 회로는 **짧은 L bin(문턱 roll-off)에서만** 면적 예산 안에서 실현된다.
  - 엔진이 출력 pmos에 최소 L bin 쪽을 탐색하지 못하면 front가 빈다.
  - LUT L 축은 0.15 µm를 포함한다(`L` 배열 실측). spec에 L 제한이 없으므로 선언 문제는 아니다.

## 2. 엔진 정지 원인 (master HEAD 실측)

`engine_runs.jsonl`(HEAD `08048939765899c6435b01fca515c6afacffdf5a`, LUT manifest sha 경로 = `assets/lut_v2_location.json` resolve):

| E_B | 단계 A | 단계 B | 층 0 stop | 시험점 | 커널 | 실패 기록 |
|---|---|---|---|---|---|---|
| 40 | ok | ok | `start_lut_query_failed+probe_eval_budget` | 33 | 40 | SEAL_VIOLATION M10, tol_v_cell pmos VDS = −0.3294 V(축 [0, 1.8] 밖) |
| 2000 | ok | ok | 같음 | 1909 | 2000 | 같음 |

- 예산을 50배 늘려도 출발점이 0이다. 예산 문제가 아니다.
- 실패 값 M10 VDS −0.329 V는 B81 분석(`wt/_drafts/evidence/2026-10-26/b81_no_seal_root_cause.md` §1.1, 칸 1~6 M10 −0.038 ~ −0.329 V)과 같다 → 같은 기제가 master에도 남아 있다(agent 인용 + 실측 일치).
- 기제(B81 §1.1 실측 + §1.2 손계산 해석):
  - (a) 자기 바이어스 R·I를 독립 θ 성분으로 상자 중심에 둔다 → IR이 포화 창 [VSG5 − VSG6 + VDSAT6, VSG5 − VDSAT5] 밖에 놓인다.
  - (b) W4 자유 노드 N20의 창이 게이트 사슬 vdd–M17–N17–(M18 sg)–Y–(M19 gs)–N20–M20–vss를 보지 않는다 → Y가 N910 위로 올라가 M10이 역바이어스된다.
  - 'lut_query_failed'라는 이름은 원인(KVL 비정합 θ)을 가린다.
- 물리 가능 점은 있다.
  - B81: 손계산 672점 중 280점 봉인.
  - 이 문서 §3 설계점: SPICE에서 22 MOS 모두 포화, 최소 여유 +91 mV(M3).
- **분류**:
  - 엔진 결함(재작성 범위) = 층 0 출발 θ 구성. 근거는 O-127 θ 기저 원칙: '미선언 R은 V_R 결정' + 게이트 경유 KVL 고리의 종속 성분 제거. card LA-1(DEC-104·DEC-71 (4)).
  - spec 선언 문제: 아님(정지 원인 아님).
  - topology 연결 문제: 아님(§1 대조, 대기열 후보 0).

### 2.1 '동작'까지 필요한 조치 (순서)

1. (엔진, 재작성 범위) **층 0 출발 θ를 KVL 정합으로 구성(LA-1)**
   - R1a·R1b·R1c를 V_R(= I·R) 성분으로 θ화하고 R은 종속으로 둔다(O-127).
   - 게이트 경유 고리(VSG18 + VGS19 ≤ vdd − VDSAT17 − VDSAT20, VGS22 + VSG21 = VSG18 + VGS19)를 출발 단계 고리에 넣는다.
   - 출력 pmos의 L bin을 열린 축으로 둔다(§1.2 -- L ≥ 0.5 µm면 면적 예산 밖).
   - 이것 없이는 front = 0이 계속된다(E_B 2000 실측).
2. (엔진, 재작성 범위) **ICMR 기능 행**
   - `graph.ss_nodal` writer(O-211 조건 (2), as-built 없음), DE-1 (e) 순수 함수, servo 측정 구성 식 = oracle 식(조건 (1)).
   - as-built `metrics/ls_swing.py`의 icm_margin_v(경로 합, 기능 기준 없음)는 O-206 뒤 fail-open 계산이 된다 → 삭제 범위.
   - 조건 (3) 용량 전용 노드: 이 회로의 모든 노드에 DC 경로가 있다(Cc·CL 모두 agnd 쪽, 0/23) → 정지 사유 없음.
3. (사용자 선언) §3 ICMR 기능 기준 칸 + §4 목록. 선언 전에는 icm_margin_v가 정의 불능이고, 판정 제약 전부가 verified_by가 되어야 하는 합격(O-205 (2))이 막힌다.
4. (사용자 선언) 탐색 예산.
   - PA-2 `front_budget_s`: 운영 E_B는 여기서 유도된다(`search/search_values.py:45-47` docstring).
   - PA-1 `objective.budgets`.
   - 미선언이면 harness 값 말고는 엔진 실행 근거가 없다.
5. (oracle) front 점 SPICE 확정: free 스펙 + 전 MOS 포화(spec spice_check), ICMR = `.dc` servo + 점별 `.tf`.

## 3. ICMR 기능 기준 -- 설계점 실측과 권고

### 3.1 측정 설계점 (손계산, 사용자 선언 아님 -- 측정용)

gm/ID 선택(LUT `GM/ID` 표):

| 소자 | gm/ID | L |
|---|---|---|
| 입력쌍 | ≈ 20 | 0.5 µm |
| 꼬리 | ≈ 13 | 1 µm |
| pmos 거울 | ≈ 14 | 1 µm |
| nmos 거울 | ≈ 18 | 1 µm(M20 헤드룸) |
| follower·출력 | 약반전 | 0.15 µm(§1.2) |

전류·소자값:
- IBias 50 µA(spec), M3:M4 = 1:1, 가지 23.4 µA.
- R은 '거울 여유 = R 아래 소자 여유' max-min으로 정했다: R1a = R1b = 12.89 kΩ, R1c = 20.77 kΩ(θ 상자 [1 kΩ, 1 MΩ] 안).
- Cc = gm1/(2π·60 MHz) = 1.235 pF(원문 GB = gm1/Cc 손계산 꼴, 상자 [0.1, 10] pF 안).
- 출력단 배율은 gm21 + gmb21 + gm22 + gmb22 ≥ 1 mS로 정했다(정지 전류 22.7 µA).

SPICE(ngspice-46 sky130 tt, `spice_icmr.jsonl` case v2):

| 항목 | 값 | spec |
|---|---|---|
| 포화 | 22/22, 최소 여유 +0.091 V(M3) | 전 MOS 포화 |
| 증분 DC 이득(.tf) | 80.0 dB | ≥ 65 dB ✓ |
| AC A0 | 80.0 dB | ✓ |
| Rout(10 kHz, 개루프) | 931 Ω | ≤ 1000 Ω ✓ |
| UGF | 24.6 MHz | ≥ 60 MHz ✗ |
| PM | 32.5° | ≥ 70° ✗ |
| 게이트 + Cc 면적 | ≈ 1.5e-9 m² | ≤ 2e-8 m² ✓ |

- GBW·PM 미달은 거울 경로(M7/M8 → M11/M12 → M13/M14 → M15/M16) 극과 Y 기생 때문으로 보인다(추정). 엔진 탐색의 몫이다.
- 이 점은 ICMR 측정 대상일 뿐 front 점이 아니다.

### 3.2 ICMR servo 훑기 실측

- 측정 구성: plan N3.8 'ICMR 측정 구성' 그대로다.
  - vin_p = x, vin_n = vout + (x − 0.9) 연결원 → 출력이 0.9 V에 묶인다.
  - 같은 x·같은 servo 입력 차로 개루프 `.tf v(vout) Vdif`를 잰다(증분 DC 이득).
  - x = 0.30 ~ 1.80 V, 10 mV 간격.
- 기준점 V_cm0 = 0.9 V(spec `human.input_dc` = agnd), A0 = 79.99 dB.

| 창 정의 | 아래 끝 | 위 끝 | 묶는 소자/양 | icm_margin_v |
|---|---|---|---|---|
| 영역 행만(VDS ≥ VDSAT 전 소자) | 0.79 | 1.04 | 아래 M3, 위 M1·M2 | 0.11 |
| 기능만: 상대 저하 ≤ 1 dB | 0.73 | 0.96 | 이득 | -- |
| 기능만: ≤ 3 dB | 0.69 | 1.00 | 이득 | -- |
| 기능만: ≤ 6 dB | 0.66 | 1.03 | 이득 | -- |
| 기능만: 절대 A ≥ gain_ss_db(65 dB) | 0.61 | 1.08 | 이득 | -- |
| **영역 ∧ 1 dB** | 0.79 | 0.96 | 아래 M3, 위 이득 | 0.06 |
| **영역 ∧ 3 dB** | 0.79 | 1.00 | 아래 M3, 위 이득 | 0.10 |
| **영역 ∧ A ≥ 65 dB** | 0.79 | 1.04 | 영역 행(기능 비구속) | 0.11 |

- 점 기록(발췌):

| x (V) | 증분 DC 이득 | 상태 |
|---|---|---|
| 0.70 | 77.7 dB | 꼬리 32 µA, M3 −58 mV |
| 0.60 | 63.9 dB | 꼬리 13 µA, M6·M8·M11도 triode |
| 1.00 | 77.6 dB | M1 여유 +39 mV |
| 1.05 | 71.3 dB | M1 −3 mV |
| 1.10 | 61.9 dB | |

- 물리 대조(§1.1 예측):
  - 아래 쪽: 이득 기준이 영역 행보다 느슨하다. M3 triode 뒤에도 0.7 V까지 1 dB 안이다. 아래 끝은 영역 행이 정한다.
  - 위 쪽: 이득이 M1 포화 경계 전에 이미 떨어진다(1.00 V에서 −2.4 dB, 여유 +39 mV). 상대 기준이 영역 행보다 엄하다.
  - 판정: **맞음**(예측과 부호·순서 일치).

### 3.3 ★ 먼저 보고: `icm_margin_v ≥ 0`은 현행 정의에서 판별력이 없다 (원래 취지와 다름 · 결정 간 모순 후보)

- 근거 정의
  - ICMR 측정 구성(O-115): 출력을 봉인점 동작점에 묶고 입력을 함께 훑는다.
  - 판정 꼴(O-211): 기준점 대비 허용 저하.
- x = V_cm0에서 servo 상태는 봉인점 그 자체다.
  - 영역 행: 봉인 = 전 소자 포화이므로 만족한다.
  - 기능 행: 기준점이 V_cm0이면 저하 0으로 만족한다. 절대 하한이면 gain_ss_db 제약과 같은 값이므로 만족한다.
  - 따라서 봉인된 모든 점에서 icm_margin_v ≥ 0이 **항등 참**이다.
- 실측: 위 표의 모든 창이 0.9를 품는다(margin 0.06 ~ 0.11).
- 출처 기록(spec :141-146)은 J-E(2026-10-08)다. 그때 ICMR 정의는 O-25 (2) '출력은 회로가 따라감'이었고 servo 이전이었다. O-115(servo)로 바뀌면서 이 제약은 '선언 입력 DC가 창 안'을 묻는 힘을 잃었다.
- 그래서 기능 기준을 무엇으로 선언하든 이 회로의 합격·front에는 영향이 0이다. 선언은 '정의 불능 → 정의됨'만 바꾼다.
- ⑩ 결정 간 모순 점검은 권고 작성자가 아닌 점검자의 전수 대조가 필요하다. 이 문서는 **후보 표지만** 한다(J-E ↔ O-115 ↔ O-206).

### 3.4 기능 기준 권고 (대칭 비교)

공통 전제:
- 기준점 = spec `human.input_dc`(agnd = 0.9 V)의 servo 점이다. 새 값 0, 원칙 3 DC 양.
- 같은 함수 DE-1 (e), oracle `.dc`/`.tf`.

| 안 | 허용 저하 정의 | 새 상수 | 물리 뜻 | 원문 맥락 | 엔진 계산 꼴 | 실측 창(영역 ∧ 기능) | ⚠ |
|---|---|---|---|---|---|---|---|
| **(가) 절대 하한 = gain spec** | 창 안 모든 점 A(x) ≥ `value_from_constraint: gain_ss_db`. 판정 꼴 (b)로 쓰면 허용 저하 = A(V_cm0) − 65 dB | 0 | '창 안에서 선언 DC 이득 사양을 계속 만족' -- 데이터시트의 'ICMR 전역에서 사양 보증'과 같은 뜻 | 원문 p.6 Av(0) = 65 dB가 이 회로의 유일한 이득 기준 | 같은 함수, 문턱만 constraint 참조 | [0.79, 1.04], 기능 비구속 | 허용 저하가 기준점 이득 여유에 따라 변한다(설계마다 다른 dB) |
| (나) 상대 저하 X dB | A(V_cm0) − A(x) ≤ X, X 사용자 선언 | X 1개 | 기준점 대비 모양 유지 | 원문에 없음. 3 dB는 current_reuse(Xie·Chen 2019 Fig. 10 p.10)의 **다른 회로·출력 범위** 정의라 이 회로 적용은 추론 | 같음 | X = 1: [0.79, 0.96] · X = 3: [0.79, 1.00] · X = 6: [0.79, 1.03] | 원칙 11·13: X를 원문 근거 없이 정하면 상수 발명. 사용자 지정이어야 한다 |
| (다) 기능 기준 없이 영역 행만 | -- | 0 | 과대 통과 | -- | -- | [0.79, 1.04] | O-206에서 기각(fail-open). 비교용 |

- 권고: **(가)**. 근거는 다음과 같다.
  1. 새 상수가 0이다(원칙 11).
  2. 원문이 이 회로에 준 유일한 기능 기준(Av(0) = 65 dB, p.26-6)과 같은 양이다.
  3. 실측에서 물리적으로 말이 되는 창이다. 영역 행과 같은 [0.79, 1.04]이고, 위 끝은 M1 포화 경계에서 이득이 72 dB(> 65)다.
- 판정: **조건부**. 조건 두 가지:
  - O-211의 '기준점 대비 허용 저하' 꼴에 '허용 저하 = A_ref − constraint 값' 참조 형식이 들어갈 수 있는지는 design(SF-1 칸 형식) 확인이 필요하다.
  - §3.3 때문에 이 회로에서는 어느 안이든 판정 영향이 0이다.
- (나)를 고르면 X는 사용자 지정값이어야 한다(근거 없는 3 dB 기본값 금지).

## 4. 이 회로 판정에 필요한 사용자 선언 목록

| # | 칸 | 현재 | 필요 이유 | 권고 기본안(원칙 유도) |
|---|---|---|---|---|
| 1 | icm_margin_v 기능 기준(O-206·O-211, SF-1 칸) | 없음 → 정의 불능 | 판정 제약 전부 verified_by가 합격 조건(O-205 (2)) | §3.4 (가) |
| 2 | icm_margin_v 값 0의 존폐(§3.3) | `>= 0`(J-E) | servo 정의에서 항등 참 | 셋 중 사용자 결정 ⚠: (i) 유지 + 보고 전용 표지 (ii) 제약 삭제 (iii) 값 m > 0 선언 -- 원문에 근거가 없고, β = 1 사용이면 입력 CM = 출력이므로 출력 범위 선언(현재 미선언)에서 유도 가능 |
| 3 | `intended_region`(CI-18) | pending | O-202 `off`·`judged_by`는 off 소자가 있을 때만 | 전 소자 포화(off·triode 선언 0) -- 정상 동작에서 꺼지는 소자 없음. M18·M19 전류는 신호에 따라 변하지만 정지점에서는 전도(원문 p.6 문장, SPICE 23 µA). 따라서 `judged_by` 불필요 |
| 4 | `objective.budgets`(PA-1) | pending | front 목적·예산 | 사용자 결정(원문 전력값 없음) |
| 5 | `search.front_budget_s`(PA-2) | pending | 운영 E_B 유도 | 사용자 결정(현재는 harness 값만) |
| 6 | `spice_check.front_points_rule`(AC-3) | pending | oracle 확정 점 | 기본안 endpoints_and_budget_point(spec :293 주석) |
| 7 | `node_voltage_targets_v`(CI-15) | pending | 필수 아님 | 선언 없음 유지(출력 DC는 β = 1 사용, W4 자유 노드) |

- 선언 불필요: bulk(기본 레일 = 원문 그림), 입력 DC(agnd 확정), 공급(확정), L 제한(없음이 맞음 -- §1.2 짧은 L 필요).

## 5. topology 정정 대기열 후보

없음. 22 MOS·5 수동·IBias 연결이 p.26-6 그림과 net별로 일치한다. 자동 플래그 vin_n·vin_p 'gate만 참조'는 외부 입력 핀이라 정상이다.

## 6. 보고 묶음 (원칙 26)

### 6.1 bkit 단계표

| 계획 | design | 검증 | 승인 | test | code | 구현 gap | 감사 |
|---|---|---|---|---|---|---|---|
| 해당 없음(분석 보고, 코드·계획 변경 0) | 해당 없음 | 해당 없음 | 해당 없음 | 해당 없음 | 해당 없음 | 해당 없음 | 해당 없음 |

### 6.2 단계별 점검표

- 코드 변경이 없어 graph 정본·G-10·블록 안 재계산·소비자·구조·회로 이름·fail-closed·상수 발명·DC/AC·계획 먼저는 모두 **해당 없음(코드 변경 0)**이다.
- 권고 자체의 원칙 점검:
  - 상수 발명 0: (가) 안. (나) X는 사용자 몫으로 표지.
  - DC/AC 분리: 기능 기준 = 증분 DC 이득.
  - 작성자 ≠ 검증자: 이 권고는 독립 검증 전이다.
  - 일반성: 이 회로 1/1만 실측. (가) 꼴은 회로 이름 무관.

### 6.3 원래 취지와 다름

- J-E(2026-10-08) `icm_margin_v >= 0`: O-115 servo 정의 뒤 항등 참(§3.3).
- 권고 (가)는 O-211 '선언 허용 저하' 문언을 constraint 참조 값으로 채운다. 칸 형식은 design 확인 필요.

### 6.4 권고 실측 출처

- 직접 실측:
  - `engine_runs.jsonl`(층 0 정지)
  - `spice_icmr.jsonl`·`summary.jsonl`(설계점·ICMR 창)
  - LUT 보간(§1.2, 명령은 이 문서 작성 세션 -- 수치는 §1.2 표)
- agent 인용: B81 `wt/_drafts/evidence/2026-10-26/b81_no_seal_root_cause.md` §1.1·§3(KVL 비정합 기제, 280/672 봉인). M10 VDS −0.329 V가 일치해 실측으로 뒷받침된다.

### 6.5 권고 확인표 ((가) 기능 기준)

| 항목 | 내용 | 구분 |
|---|---|---|
| ① 지적 사실 직접 재확인 | spec :95·:141 직접 읽음 | 실측 |
| ② 계획 grep | N3.8 'ICMR 기능 기준'·'출력 범위 판정 꼴'·'ICMR 측정 구성' 읽음 | 실측 |
| ③ 원칙 전수 | 1(물리 정합, SPICE식 아님)·3·11·13·14·16 | -- |
| ④ 대안표 | §3.4 | -- |
| ⑤ 실현 가능성 | SPICE 창 | 실측 |
| ⑥ 열린 결정 상호작용 | SF-1 칸 형식, §3.3 | -- |
| ⑦ 원래 취지 | §6.3 | -- |
| ⑧ 원문 | p.26-6, PDF 경로 위 | -- |
| ⑨ 물리 | §1.1 예측 대 §3.2 실측 | 맞음 |
| ⑩ 결정 간 모순 점검 | **안 함** -- 점검자 ≠ 작성자 필요. 후보만 §3.3 | 안 함 |
