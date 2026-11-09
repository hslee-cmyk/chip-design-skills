# current_reuse_telescopic_ota -- 동작 조건·정지 원인·ICMR 기능 기준 권고 (독립 회로 분석)

- 작성: 회로 분석 agent(독립), 2026-11-01. 기준 = master `08048939`. 저장소·계획·topology·spec·git 쓰기 0.
- 확인 사항: `assets/topology_to_markdown.py`를 실행하면 `assets/library/current_reuse_telescopic_ota.topology.md`를 다시 씁니다(도구 동작). 내용이 같아서 `git status` 변화는 0이었습니다.
- 스크립트·로그 위치: `current_reuse_telescopic_ota_files/`
  - `run_engine.py`: nmcnr agent 스크립트의 사본입니다. 바꾼 것은 OUT·회로·prefix뿐입니다.
  - 엔진 실행 기록: `engine_run_eb40.jsonl`, `engine_run_eb2000.jsonl`, `eb2000_summary.txt`, `eb2000_seq1175_nondevice_constraints.txt`
  - SPICE 실측 스크립트: `icmr_servo_sweep.py`
  - SPICE 실측 결과: `icmr_servo_sweep_s10.jsonl`, `icmr_servo_sweep_alldev_s5.jsonl`, `sweep_s10_table.txt`, `alldev_s5_summary.txt`
  - SPICE 대표점: `ref_cr_free_y0.85.cir`. 원본 `wt/_scratch_b81/out/spice/cr_free_y0.85.cir`과 sha256 `f69339b9…`가 같습니다. 이 점은 B81 분석에서 원문 노드 전압을 보존해 만든 sky130 θ이고, 엔진 front 점이 아닙니다.
- 원문 위치: `skills/analog-gmid-design/assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`(md: `paper.md`). 웹 링크는 찾지 못했습니다.

## (a) 토폴로지 해석

connectivity는 net 기준 표로 읽었습니다(`topology_to_markdown.py` 출력). 태그(device_roles 등)는 쓰지 않았습니다.

| 항목 | 해석 | 근거(net) | 확신도 |
|---|---|---|---|
| 1단 구조 | 완전차동 current-reuse telescopic 증폭기입니다. 한쪽 반회로 스택(7단)은 vdd → M6‖M7 → Vx → M1a(p 입력) → N1a2a → M2a(p 캐스코드) → **Vom1** ← M3a(n 캐스코드) ← N3a4a ← M4a(n 입력) ← Vy ← M5 → gnd 입니다 | Vip = M1a.g, M4a.g. Vom1 = M2a.d, M3a.d | 높음(원문 Fig.2 p.2와 같음) |
| 입력쌍 | p쌍 M1a/b와 n쌍 M4a/b가 같은 입력 gate를 공유하고 전류를 재사용합니다. Adm₁ ∝ (gm1 + gm4)·Rout | Vip·Vim가 두 쌍 gate 모두에 물림. 원문 p.2 '((gmn4+gmp1)ro)²' | 높음 |
| 꼬리 | p쪽은 M6(Vbias1 고정)와 M7(Vcmfb, CMFB 제어)이 병렬입니다. n쪽은 M5(Vbias4) 하나입니다 | Vx·Vy net | 높음 |
| 캐스코드 바이어스 | 꼬리 노드를 추종합니다. Vbias2 = Vx − VSG58 (M58 s=Vx, g=Vbias2, M57 diode). Vbias3 = Vy + VGS63 (M63 s=Vy, g=Vbias3, M64 diode). 그래서 입력소자 VDS는 일정하게 유지되고, 공통모드 이동은 캐스코드 VDS가 흡수합니다 | Vbias2·Vbias3·N58_57·N64_63 | 높음(원문 Fig.8 p.8 이미지와 대조) |
| 2단 | class-AB 공통소스입니다. M16(n, g=Vop1)·M15(p, g=Vg15)가 Vom을 구동하고, M26/M25가 Vop을 구동합니다. M9a/b·M18a/b는 floating battery이고, M11·M14·M20·M23 diode 사슬이 floating battery의 gate 바이어스를 만듭니다. Miller는 Cc–Rz(Vom–Vop1, Vop–Vom1)입니다 | Vg15·Vg25·N11b·N14a14b | 높음(원문 Fig.3 p.3) |
| CMFB | R1·R2로 평균한 Voc와 Voc_des(M39/M40 diode)를 M37a/b 차동쌍이 비교합니다. 결과 Vcmfb가 M7을 제어합니다(1단 p 꼬리 전류). | Voc·Voc_des·Vcmfb | 높음(원문 Fig.5 p.3) |
| 바이어스 | Iref → M18_bg(Vbias1) → M60·M66(Vbias4), M61 → M64/M63(Vbias3), M68 → M57/M58(Vbias2) | Vbias1~4 | 높음 |
| 되먹임 | 응용 되먹임은 Cf1/Cf2(출력→입력)이고 DC 경로가 없습니다. DC 동작점은 CMFB 루프 하나와 (ICMR 측정 시) servo가 닫습니다 | passive 표 | 높음 |

### Vom1의 물리 결정자, 그리고 입력 공통모드가 움직일 때 무엇이 먼저 무너지는가

**Vom1의 결정자.** Vom1 = VGS26입니다. 2단 n 소자가 정지 전류 I_q에서 갖는 VGS이고, 원문은 '약 0.5 V'라고 적었습니다(p.2). SPICE 대표점에서는 0.475 V이고 servo 구간 전체에서 고정입니다.

**창 경계의 닫힌 식(KVL, 손계산).**

- 위 끝(M3a 포화): `Vcm_max = Vom1 − VDSAT3a + VGS4a + VGS3a − VGS63`
- 아래 끝(M5 포화): `Vcm_min = VGS4a + VDSAT5`
- 창 폭: **`W ≈ Vom1 − VDSAT3a − VDSAT5 − VDS4a`**. 여기서 VDS4a = VGS63 − VGS3a이고, 추종 바이어스가 고정하는 값입니다(실측 82 mV).

**p쪽 여유.** p쪽(M2a)은 대표점에서 VDS − VDSAT = 0.91 V로 여유가 큽니다. 그래서 창은 n쪽이 정합니다. 이것은 원문 p.2 'unsymmetrical input common mode range … bottom devices (M3, M4 and M5) are pushed to linear region'과 맞습니다. 다만 이 연결에서 M5의 VDS(= Vy)는 Vcm과 함께 오릅니다. 위쪽에서 선형으로 가는 것은 M3a → M4a이고, M5는 아래쪽 끝을 정합니다. 원문 문장의 M5 포함은 이 연결에서는 아래 끝에만 해당합니다(확신도 중).

**SPICE 실측 순서.** servo로 Vod ≈ 0을 유지하고, 출력 CM은 회로 자체 CMFB가 잡은 상태입니다. 전 MOS(51개)를 보았습니다(`alldev_s5_summary.txt`, `sweep_s10_table.txt`).

| Vcm | 사건 | Adm |
|---|---|---|
| ≤ 0.555 V | M7(CMFB 꼬리) 전류 → 0(3.7e-13 A)이 되어 CMFB가 권한을 잃습니다. 출력 CM이 붕괴하고(Vop = Vom = 0) M16/M26이 비포화가 됩니다. **절벽** | 0.55 V에서 −31 dB |
| 0.5675 V | **M5가 VDS = VDSAT**입니다(첫 영역 이탈, 아래 끝). 약반전 꼬리라 VDS ~ 수 UT부터 전류가 줄고, VGS4a가 함께 내려가 끝이 손계산보다 낮게 갑니다 | 74.9 dB |
| 0.705 V | 이득 정점 | 76.16 dB |
| 0.90 V | 원문 동작점(출력 CM 0.9 V와 같은 입력 CM, Fig.10 중앙 이득 = Fig.11 0.9 V 값) | 74.30 dB |
| 0.922 V | 정점 −3 dB | 73.16 dB |
| 0.944 V | 0.9 V 기준 −3 dB | 71.30 dB |
| 0.970 V | **M3a/M3b가 VDS = VDSAT**입니다(위 끝 영역 이탈). 그 전부터 캐스코드 ro가 줄어 이득은 서서히 떨어집니다 | 67.7 dB |
| 1.05 V | M4a/b 비포화 | 52.4 dB |
| ≥ 1.17 V | M6·M7 비포화 → CMFB 상실 → 절벽 | 1.19 V에서 −123 dB |

**손계산 대 실측.** 0.9 V 점의 실측 VGS로 위 끝을 계산하면 0.949 V이고 SPICE는 0.970 V입니다(차 21 mV, 체효과로 VGS3a 상승). 이 차는 엔진이 '추정'으로 표지하고 oracle이 확정하는 범위입니다(E-1).

**결론.**

- 아래쪽은 영역 행(M5)과 기능 붕괴(CMFB 상실)가 12 mV 안에서 함께 옵니다. 영역 행이 먼저 걸립니다.
- 위쪽은 **영역 행(0.970 V)보다 이득 저하가 먼저** 옵니다. 영역 행만 쓰면 8.4 dB 저하점까지 '창 안'이 됩니다. 기능 기준(O-206·O-211)이 실제로 판정을 바꾸는 쪽은 위쪽입니다.
- 원문 Fig.11(p.11, `images/p11_1.png`)과 같은 모양입니다: 아래쪽 절벽 ~0.545 V, 정점 0.814 V/78.66 dB, 완만한 하강, 1.17 V 절벽.

## (b) 엔진 정지 원인·분류·필요 조치

### 실측

엔진 소스 수정 0, library 경로 그대로, LUT는 `load_lut_set` 경로로 sha를 대조했습니다. 출력은 TEMP 고유 경로입니다.

**eval_budget 40**(시험 하네스 선언값, `engine_run_eb40.jsonl`)

- 단계 A·B ok
- `layer0_no_start`, stop = **`start_no_root_in_window+probe_eval_budget`**, kernel_calls 40, probes 27, front 0
- 실패 40/40은 모두 봉인 KVL 창이 빈 경우입니다:
  - M4a/Vy 33건: 창 [0, −0.0375]
  - M37b/Ncmfb_tail
  - M18a/Vg25
  - M18b/Vom1

**eval_budget 2000**, front 예산 600 s(`eb2000_summary.txt`)

- **Halton 927번째에서 출발점이 받아들여졌습니다.** `layer0_minimal`이 converged(t = 0.722, hard_ok true)이고, 봉인 124점입니다. B81(2026-10-26, integ-it12) 결과와 같은 시험점 번호입니다.
- 실패 1051건의 분포:
  - Ncmfb_tail(M37b) 244
  - N20b(M20b) 174
  - Vy(M4a) 173
  - N24b23a(M23a) 121
  - M63 LUT 조회 72
  - Vg25 65
  - Vom1 63
  - 기타
- 그래도 **front는 0**입니다. 원인은 다음과 같습니다.
  1. `unmeasured`: `gain_ss_db`·`ratio_ss_db`×2·`parasitic_pm_ss_deg` = `view_pending`(spec `{"pending":"MOD5"}`), `pm_ss_deg` = `dc_not_above_level`
  2. 봉인점에서도 `area_search_m2` 제약 c = −1.5e16(크게 위반), `pm_cm_ss_deg` c = −15.5(위반)
  3. `stops_wall_budget = 1`(709 s)
- `icm_margin_v`는 c = +0.394로 '만족'이 나옵니다. as-built는 영역 창으로 계산합니다. O-206 기준(기능 기준 미선언 = 정의 불능)은 아직 구현되어 있지 않습니다. 재작성 범위: IT-2c 재동결 착수 조건, 계획 P:1323.

### 분류

| # | 원인 | 분류 | 근거 |
|---|---|---|---|
| 1 | 층 0 출발점(상자 중심·사다리·Halton)이 KVL 비정합 θ를 만듭니다. 입력 gate 고리 Vip = VGS4a + VDS5, Voc_des = VSG40 ≥ VGS37b + VDS38, Vg25·N20b·N24b23a diode 사슬이 상자 중심 밀도에서 깨집니다. 봉인 가능 영역은 얇은 판입니다 | **엔진 결함(재작성 범위)**. LA-1 R6 블록(DEC-104·O-127 θ 기저 = KVL 종속 성분 제거)이 이 고리들을 종속으로 파생하면 상자 중심 종속값이 사라집니다. 출발 사다리·Halton 의존이 원인입니다 | 실측 eb40·eb2000. B81 §2 |
| 2 | 시험 예산 40이 원인을 가립니다(927번째에서 출발 성공) | 측정 조건(엔진 선언 아님). spec `front_budget_s` = PA-2 pending | eb2000 |
| 3 | gain·CMRR·PSRR·parasitic PM 뷰 `pending MOD5`, classab_centering metric `pending MOD5` | spec 선언 미완(엔진 design 몫: MOD5) | spec :151-162, :185-224 |
| 4 | `area_search_m2` 위반(봉인점 W가 과대) | 탐색 결과(층 0 점이 면적을 보지 않는 feasibility_only 점). 엔진 탐색 몫. #1이 고쳐진 뒤 다시 잽니다 | eb2000 seq 1175 |
| 5 | `pm_cm_ss_deg` 위반 | 사이징 결과(CMFB 루프). #1 뒤 다시 잽니다 | 같은 곳 |
| 6 | `icm_margin_v`의 ICMR 기능 기준 미선언 | spec 선언 필요(O-206). 미선언이면 이 제약은 정의 불능이 맞습니다. as-built는 아직 옛 정의(영역 창)로 값을 냅니다(재작성 범위 IT-2c) | spec :256-266, 계획 P:729 |
| 7 | `input_dc` = `{"pending":"SP-2"}` | spec data 미반영. U-128은 current_reuse = `engine`으로 닫혔고(O-170·O-172), data 커밋이 남아 있습니다 | spec :21-23, 계획 P:2311·P:2661 |
| 8 | `swing_out_v ≥ 2.4`가 남아 있습니다(metric은 O-154 Q3로 삭제됨) | spec 이관 필요. 출력 범위 절대 범위 Vod [−1.2, 1.2] V와 (b) 판정 꼴 칸(SF-1 범위 3) | spec :244-255, 계획 P:2299 |
| — | topology connectivity | **결함 없음**. 원문 Fig.1~5·Fig.8 이미지와 net이 맞습니다 | (a) |

### '동작'까지 필요한 조치(순서)

1. **엔진 #1**: LA-1(R6 블록·θ 기저 O-127)로 출발 θ의 고리 종속 성분을 KVL에서 파생합니다. 완료 판정 = 이 회로가 예산 40에서 출발점 ≥ 1. 계획이 이미 정한 재작성 범위라 새 결정은 없습니다.
2. **spec data**(SF-1·U-128):
   - `input_dc` = `engine`
   - `swing_out_v`를 출력 범위 선언(Vod ±1.2 V + (b) 칸)으로 옮김
   - `icm_margin_v`에 ICMR 기능 기준 칸 추가(아래 (c))
   - `intended_region`(CI-18)을 '예외 없음'으로 명시
3. **MOD5 뷰**: gain·ratio·parasitic PM 뷰를 정합니다. 없으면 ss 제약이 unmeasured로 남아 front가 열리지 않습니다.
4. 그 뒤 front 재측정: 면적·pm_cm 위반이 탐색으로 풀리는지 봅니다.
5. oracle: `.dc` servo 훑기 + 점별 `.tf`로 ICMR을 확정합니다(아래 실측과 같은 꼴).

## (c) ICMR 기능 기준 선언 권고

### 원문 정의(실측 판독)

- Table I(p.1)의 'Input common-mode range [576.5mV, 900.1mV]'는 Fig.11(p.11)의 두 표지 576.4665m·900.1689m과 같습니다.
- Fig.11 가로축은 'Vic (V)'입니다. 캡션 'DC gain versus output common-mode voltage'는 가로축과 맞지 않습니다. 이 그림은 ICMR 측정으로 판독합니다(확신도 높음).
- 수평선 H1 = 75.656 dB = 정점 M4(814.06 mV, 78.656 dB) − 3.000 dB입니다.
- 따라서 **원문 ICMR = 입력 CM 훑기의 DC 이득이 '정점 − 3 dB' 이상인 구간**입니다. 기준점은 정점이고 허용 저하는 3 dB입니다.
- 출력 스윙 Fig.10(p.10)도 중앙(=정점) 75.672 dB − 3 dB = 72.672 dB로 같은 꼴입니다(계획 P:729 (b)가 이미 인용).
- 측정 절 'IV.A DC Sweep'은 paper.md p.4에 있습니다. 계획 P:729는 'p.7'로 적었는데, 쪽 번호 재확인이 필요합니다(사소).
- 원문 동작점 Vic ≈ 0.9 V의 이득(75.66)은 H1과 거의 같습니다. **원문 설계는 위 끝 여유가 ≈ 0.1 mV**입니다.

### 대안(대칭 비교)

SPICE 실측은 대표점 기준이고, 창 = 영역 행(전 MOS VDS ≥ VDSAT, O-204·O-205 R0) ∧ 기능 기준입니다.

| 안 | 기준점 | 허용 저하 | 창 (SPICE 실측) | 0.9 V 입력 시 icm_margin | 물리 정합 | 계획 꼴(O-211)과의 관계 | 엔진 계산 꼴 | 상수 |
|---|---|---|---|---|---|---|---|---|
| **(가) 권고** | 봉인점(선언/엔진 입력 DC의 servo 상태) | 3 dB(사용자 선언, 근거 = 원문 정의 Fig.11 p.11 + 이 회로 출력 범위 (b) 3 dB와 같은 규약) | [0.5675 (M5 영역), 0.9438 (기능)] | **0.0438 V** | 맞음. 동작점 대비 기능 유지 범위이고, 위쪽의 점진 저하(M3a ro 붕괴)를 잡습니다 | **같음**(기준점 대비 허용 저하, 구간 [봉인점, 영역 끝] 첫 교차) | DE-1 (e) 함수 + 단측 근 찾기(K_max) | 3 dB = 사용자 선언 1칸 |
| (가′) | 창 안 이득 정점(원문 그대로) | 3 dB | [0.5675, 0.9222] | 0.0222 V | 맞음. 원문 측정과 같은 정의 | ⚠ 다름. 정점 찾기(1차원 최대화)가 더해지고 근 찾기 구간 출발이 봉인점이 아닙니다 → 계획 개정 필요 | 함수 + 최대화 + 양측 근 찾기 | 3 dB |
| (나) | 없음(절대 하한) | 하한 = `value_from_constraint: gain_ss_db`(54 dB) | [0.5675, 0.970]. 기능 기준이 **안 걸리고** 영역 행(M3a)이 정합니다. 0.97 V 이득 67.7 dB > 54 | 0.070 V | 조건부. 요구 사양(이득)에 직결되고 새 상수 0입니다. 다만 이 설계에서는 무력하고(영역 행이 먼저), spec 54 dB는 옛 실측 −3 dB 유래 값(spec :159)입니다 | ⚠ 꼴이 다름(상대 저하가 아니라 절대 하한) → **원래 취지와 다름**(O-211 '기준점 대비 허용 저하') | 같은 근 찾기, 문턱 상수 | 0(참조) |
| (다) 기각 | 봉인점 | static settling ≤ 0.1%에서 유도: βA ≥ 1/ε → A ≥ 66.4 dB(β ≈ 0.48) | — | — | 물리 근거는 강합니다 | 그 spec이 선언되어 있지 않아(settle은 AP-1 대기) 유도 출처가 없습니다 → 상수 발명 | — | 기각 |

### 판정

- (가)는 **조건부 맞음**입니다.
  - 조건 1: 3 dB는 원문 '정의' 근거일 뿐이고 값 확정은 사용자 선언입니다(원칙 13).
  - 조건 2: 기준점 = 봉인점은 자기 참조입니다. 입력 DC를 `engine` 변수로 두면, 이득이 이미 떨어진 점을 봉인점으로 고른 설계도 그 점 대비 3 dB로 판정됩니다. 다만 그 점의 절대 이득은 `gain_ss_db` 제약이 따로 막습니다. 이 결합이 받아들일 만한지는 사용자가 봅니다.
- (가′)는 원문과 가장 같지만 계획 꼴을 바꿉니다.
- (나)는 새 상수 0이지만 꼴 변경(원래 취지와 다름)이고, 이 회로에서는 판별력이 0입니다.

### 실측 대조(원문 0.18 µm 대 sky130 대표점)

| 항목 | 원문 | sky130 대표점 |
|---|---|---|
| 정점 −3 dB 창 | [0.5765, 0.9002] | [0.5599, 0.9222](기능만). 영역 ∧ 기능이면 [0.5675, 0.9222] |
| 정점 위치 | 0.814 V | 0.705 V |
| 위 끝 지배 | n 캐스코드 | n 캐스코드(같음) |
| 아래 끝 | CMFB 절벽 | M5 영역 → CMFB 절벽(12 mV 뒤) |

## (d) 사용자 선언 필요 목록

1. `icm_margin_v` ICMR 기능 기준 칸(O-206·O-211). 권고 (가): 기준점 = 봉인점, 허용 저하 3 dB. 칸 이름·형식은 SF-1 design이 정합니다.
2. `input_dc`: U-128로 `engine`이 확정됐습니다. spec data 커밋만 남았습니다(사용자 승인 불필요, card 몫). 대안 = 0.9 V 고정(원문 동작점 = 출력 CM 0.9 V, p.1)이지만 논문 값 인용이라 비권고입니다.
3. 출력 범위 선언: `swing_out_v ≥ 2.4`를 절대 범위 Vod [−1.2, 1.2] V + (b) 판정 꼴 칸(기준점 Vod = 0, 허용 저하 3 dB, O-157 S2 추론 근거)으로 옮깁니다.
4. `intended_region`(CI-18): '예외 없음(전 MOS 포화 기본)'을 명시합니다.
   - M11a·M11b('sub-threshold', p.2)와 M15·M16·M25·M26('barely-on')은 약반전 포화이고, O-205 P5로 전도입니다.
   - `off` 선언 대상이 0이므로 `judged_by`(O-202 (4))도 필요 없습니다.
   - M40(gate = drain = gnd)은 diode 연결 전도 소자입니다.
5. MOD5 뷰(gain·CMRR·PSRR·parasitic PM)와 classab_centering metric 이름: design 몫이고, front가 열리는 데 필요합니다.
6. `front_budget_s`(PA-2): 예산 40에서는 출발 불가가 드러나지 않습니다. #1을 고친 뒤 다시 잽니다.
7. (선택) 출력 CM 목표(CI-15 `node_voltage_targets`): 대칭 스윙 = vdd/2 유도가 가능합니다. 다만 출력 범위 (b) 선언이 같은 효과를 내므로 따로 선언하지 않는 안을 권고합니다(둘째 생산자 방지).

## (e) 대기열 후보(topology connectivity)

- **없음.** net 표, 원문 Fig.1~5(p.2·p.3), Fig.8(p.8) 이미지 대조 결과가 일치합니다.

## (f) 근거 경로

- spec `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.sizing_spec.json`
  - :21-23 input_dc
  - :151-162 gain 54·MOD5
  - :212-224 classab pending
  - :244-255 swing_out_v
  - :256-266 icm_margin_v
  - :319-324 CI-15·CI-18
- 결정 `wt/_drafts/user_decisions.md`
  - :1186 O-205
  - :1187 O-206
  - :1192 O-211
  - :1183 O-202
  - :1184 O-203
  - :1185 O-204
- 계획 `wt/plan-v6386/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`
  - :729 'ICMR 기능 기준'·'출력 범위 판정 꼴 (b)'·'ICMR 측정 구성'
  - :653-661 N3.6
  - :1323 IT-2c
  - :1329 DE-1
  - :1333 SF-1
  - :2299 출력 범위 선언
  - :2311·:2661 U-128
- 원문 `…/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`
  - p.1 Table I
  - p.2 current-reuse 이득식·Vom1 ≈ 0.5 V·비대칭 ICMR
  - p.3 Fig.3~5
  - p.4 DC Sweep 절
  - p.6 Fig.6(b) 동작점(`images/p06_2.png`)
  - p.8 Fig.8 바이어스(`images/p08_2.png`)
  - p.10 Fig.10(`images/p10_1.png`)
  - p.11 Fig.11(`images/p11_1.png`)
- 선행 분석 `wt/_drafts/evidence/2026-10-26/b81_no_seal_root_cause.md` §2. 이번에 master HEAD로 다시 실행했고, 출발 성공 시험점 927이 같았습니다.
