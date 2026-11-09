# B81 -- sf_pushpull_output_opamp·current_reuse_telescopic_ota 봉인점 0 원인 실측

- 작성: 분석 agent, 2026-10-26. 엔진·계획·design·spec·저장소는 고치지 않았다.
- 엔진: `wt/integ-it12/skills/analog-gmid-design/gmid_engine` (integ/it12 HEAD `34585913`). import 실행과 메모리 monkeypatch만 썼다. 실행 전후 `git -C wt/integ-it12 status --short`는 같다(`_scratch_b81/git_status_before.txt` = `git_status_after.txt`, 둘 다 빈 출력).
- 원자료: `wt/_scratch_b81/`
  - 스크립트 `scripts/`: `ctx.py`(컨텍스트·계측), `l0diag.py`, `l0summary.py`, `l0trace.py`, `l0_toltrans.py`, `hp_sf.py`·`hp_sf2.py`·`hp_sf3.py`·`hp_sf_width.py`(sf 손계산 점), `hp_cr.py`(current_reuse 원문 점), `spice_sf.py`·`spice_cr.py`. `eng_seal.py`·`probe.py`·`anchor.py`는 classb 사본이고 출력 경로만 바꿨다.
  - 결과 `out/`: 케이스마다 append한 `*.jsonl`, SPICE 넷리스트 `out/spice/*.cir`, 원문 쪽 그림 `out/xie_p6~9.png`·`out/xie_img_p7_*.png`·`out/allen_p6.png`.
- heldout은 쓰지 않았다.
- 평가 예산: 앞선 측정(classb, IT-0 기준선, IT-2c Q-D)은 모두 `eval_budget = 40`(test fixture 선언, `tests/integration/test_layer0_boundary_rows.py:55-57`, IT-0 `perf.eval_budget_source = declared`)이었다. 여기서는 40·400·2000·6000을 쟀다.

## 0. 결론

| 회로 | 원인(실측) | 물리 가능 점 | 분류 |
|---|---|---|---|
| sf_pushpull | 층 0의 출발점(상자 중심·출발 사다리 7칸)과 Halton 시험점이 **KVL 비정합 θ**를 만든다. 보고 사유 `lut_query_failed`(tol_v_cell VDS 축)는 LUT 범위·조회 키 문제가 아니다. 역바이어스된 소자(VDS < 0)를 조회한 결과다. 예산 6000(시험점 5735)에서도 출발점 0이다 | **있다.** 손계산 설계점 672점 중 280점이 봉인됐다. SPICE 단위 되먹임 `.op`와 노드 ±1 mV로 맞는다 | 엔진 출발·탐색 문제(모델·정의 문제 아님) |
| current_reuse | 같은 꼴의 KVL 비정합이 출발점에서 생긴다(`Ncmfb_tail` 등). **예산 40이 원인을 덮었다.** 예산 2000이면 Halton 시험점 927번째(커널 1112회)에서 출발점이 받아들여지고 max-min이 수렴한다(t = 0.72, 경성 제약 모두 ≥ 0) | **있다.** 원문(Xie·Chen 2019 Fig.6~9) 노드 전압을 보존한 θ가 y 21점 중 20점에서 봉인됐다. SPICE `.op`(출력 고정)와 노드 ±1 mV, 전류 ±2.3 %로 맞는다 | 엔진 출발·탐색 문제 + 측정 예산 |

- 공통 기제(실측): 봉인 가능 영역이 θ 상자 안에서 아주 얇다. 원인은 독립인 θ 성분 여럿이 한 KVL 부등식에 묶이는 것이다. 예는 자기 바이어스 캐스코드의 R·I, 게이트를 거치는 VGS 사슬, W4 자유 노드 y다. sf_pushpull 봉인점 하나 주변에서 축 하나씩 훑으면 R1a 전류 축의 봉인 몫은 상자의 1.5 %, y 축은 16 %, M9 밀도 축은 8 %다(§3.3).
- gain view `{"pending":"MOD5"}`는 관여하지 않는다. B34(stick_diagram 폴백)도 관여하지 않는다(§2.4).
- 귀속: card **LA-1**(층 0 손계산 조립, DEC-71 (4) VDS 배분·기둥 KVL)이 고칠 대상이다. 다만 아래 두 꼴은 DEC-71 '기둥'(채널·저항 엣지만) 정의 밖이다. LA-1 design이 이 둘을 덮는지는 **미확인**이다.
  - 게이트를 거치는 KVL 고리(sf의 M18·M19 VGS 사슬)
  - 자기 바이어스 저항 R·I
- IT-2c 영향: Q-D·S1·S5·S7의 '미측정 + 사유'에서 사유 문언을 고쳐야 한다. current_reuse는 예산만 올리면 지금 잴 수 있다(§5).

## 1. sf_pushpull `start_lut_query_failed`

### 1.1 어느 조회가 실패하나 (실측, `out/l0diag_sf_pushpull_output_opamp.jsonl`)

- 실패 자리: `_Circuit.tolerance`(`sizing/block_columns.py:559-571`)가 `tol_v_cell`(`sizing/_helpers_lut.py:49-54`)을 부른다. 이 호출은 다변수 SCC `[N5, N1, N910]`의 Gauss-Seidel 반복마다 돈다(`block_columns.py:613-619`, `sizing/fixed_point.py:33` `tol = tolerance(current)`).
- 조회: pmos `tol_v` 표, 축 VDS, 값 −0.011 V(사다리 칸 0, 소자 M9)와 −0.038 ~ −0.329 V(칸 1~6과 층 0 보고, 소자 M10). LUT VDS 축은 [0, 1.8]이다.
- 판정:
  - LUT 범위 밖이다. 다만 VDS가 음수라 '범위가 좁다'는 뜻이 아니다. 소자가 역바이어스라는 뜻이다.
  - 조회 키(kind·w_key·L)는 맞다. L = 1.5e-7은 칸 [1.5e-7, 1.8e-7] 안이다.
  - 즉 θ가 KVL 비정합이다.
- 실패 점 노드 전압(사다리 칸 0, 엔진 풀이 중 마지막 값):

| 노드 | V | writer(쓰기 계획) | 비고 |
|---|---|---|---|
| vin_p, vin_n | 0.900 | input_dc | |
| N20 | 0.900 | W4 free_window, y = 0.5 | 창 = [0, 1.8](순서 창, `block_columns.py:208-218`) |
| Y | 1.785 | M19 vgs_gate(known N20) | Y = N20 + VGS19 |
| N5 | 1.157 | M9 vgs_gate(known vdd) | VSG9 = 0.643 |
| N1 | 1.149 | R1a 강하(known N5) | I·R = 2.53 µA × 3.16 kΩ = 8 mV |
| N910 | 1.811 | M10 vgs_source(known N1) | **vdd 위** |

- 소자 단자:

| 소자 | 종류 | VDS(크기) | 상태 |
|---|---|---|---|
| M9 | pmos | vdd − N910 = −0.011 | 역바이어스 → `tol_v_cell` VDS 축 실패 |
| M10 | pmos | N910 − Y = 0.026 | 포화 불가 |
| M19 | nmos | vdd − N20 = 0.9, VSB = 0.9 | VGS19 = 0.885 |

- 칸 1~6에서는 Y = 1.91 ~ 2.43 V로 레일 위로 올라간다(같은 파일).
- 원인 두 겹(실측 + 손계산 해석):
  - (a) 자기 바이어스 캐스코드 M9·M10의 조건 R1a·I(R1a) ≥ VSG10 − VSG9 + VDsat9를 어긴다. 중심점 θ는 R과 I를 각자 상자 기하 중심에 둔다. 그래서 IR = 8 mV이고, M10 밀도(ln IDu −13.7)가 M9(−16.7)보다 커서 VSG10 > VSG9이다.
  - (b) W4 뿌리 N20의 창은 N20에 채널이 닿는 소자(M19 source, M20 drain)만 본다(`kvl_window` `:208-218`). 게이트로 이어지는 하류 사슬 Y = N20 + VGS19, N17 = Y + VSG18 ≤ vdd − VDsat17은 창에 들어가지 않는다. 그래서 y = 0.5(N20 = 0.9)이면 Y가 pmos 캐스코드 위(N910)를 넘는다.
- 같은 θ에서 tolerance만 관대하게 하는 변형(`l0_toltrans.py`, VDS 축 밖 소자를 건너뜀)도 실패한다. 결과는 예산 400에서 `start_tol_v_undefined`, 건너뛴 조회 256회다. 따라서 tolerance의 과도 중단이 원인은 아니다. 다만 사유 이름이 원인(역바이어스·KVL)을 가리지 않고 'LUT 조회 실패'로 나오는 것은 보고 문제다(추정: 분류만 바뀌고 판정은 같다).

### 1.2 상자 균등·IBias 앵커도 같은 원인인가

- 층 0 Halton 400점 분포(`out/l0trace_sf_pushpull_output_opamp_400.jsonl`):

| 건수 | 실패 |
|---|---|
| 193 | N910 `no_root_in_window` |
| 121 | M10 `tol_v_cell` VDS |
| 14 | M9 `tol_v_cell` VDS |
| 42 | TAIL `no_root_in_window` |
| 19 | M19 `vgs_of_coordinate` |
| 11 | M9 `vgs_of_coordinate` |

  M9·M10·N910(pmos 캐스코드와 Y 기둥)이 328/400 = 82 %다.
- classb 상자 균등 400점과 앵커 1500점(`_scratch_classb/out/*.box/anchor.jsonl` 재집계 `scripts/tally.py`)도 같은 소자·노드가 1위다. 상자 86+56+13, 앵커 307+240+42가 M10·N910·M9 계열이다. 나머지는 M9·M19 `vgs_of_coordinate`(밀도가 LUT 곡선 밖), TAIL·NB이고, 모두 KVL·밀도 비정합이다.
- 판정: 같은 원인이다. 상자 균등은 밀도 축(ln IDu 하한 −57)과 R·I 축이 넓어서 실패가 더 흩어질 뿐이다.

### 1.3 예산을 올리면? (실측)

| 예산 | 시험점 | 결과 |
|---|---|---|
| 40 | 33 | 실패 |
| 400 | 379 | 실패 |
| 2000 | 1909 | 실패 |
| 6000 | 5735 | 실패(`out/l0sum_sf_pushpull_output_opamp.jsonl`, 151 s) |

**예산 문제가 아니다.**

## 2. current_reuse `start_no_root_in_window`

### 2.1 어느 뿌리·창인가 (실측, `out/l0diag_current_reuse_telescopic_ota.jsonl`)

- 실패 노드는 W4 뿌리가 아니다. 1변수 자기참조 노드 `Ncmfb_tail`(M37b vgs_source, known Voc_des)이고, `solve_self`(`block_columns.py:362-434`)에서 실패한다. 이 회로의 W4 뿌리는 `Vip`(입력, y = 0.5) 하나다.
- 창과 잔차:
  - 창 = [0, 0.248](하한은 레일, 상한은 M38 VDS 축)
  - h(lo) = +0.112(사다리 칸 0 재현에서는 +0.131), h(hi) = +∞(밀도 목표가 분지 위)
  - 부호가 같아 근이 없다(`:431`)
- 원인: Voc_des = VSG40(M40 pmos, gate = drain = gnd)이다. 밀도 −23.6(약반전)이면 0.447 V다. M37b 밀도 −16.2이면 VGS37b > Voc_des이고, 그래서 Ncmfb_tail < 0이다. 원문은 Voc_des = 0.9 V(Fig.9 (c)(d), M65·M76 VSG 0.9 V)이고 Ncmfb_tail = 0.365다.
- 사다리 칸 1~6의 실패 노드는 차례로 Vg25(M18a), Vg25, Vy(M4a: Vy = 0.9 − VGS4a < 0), Vy, Vom1(M18b)이다. 모두 KVL 사슬 비정합이다(같은 파일).
- Halton 400점 분포(`out/l0trace_current_reuse_telescopic_ota_400.jsonl`):

| 건수 | 실패 노드(소자) |
|---|---|
| 96 | Ncmfb_tail(M37b) |
| 93 | Vy(M4a) |
| 47 | N24b23a(M23a) |
| 42 | N20b(M20b) |
| 34 | Vg25(M18a) |
| 33 | Vom1(M18b) |
| 21 | M63 tol VDS |
| 12 | M4a tol VDS |

### 2.2 후보 가르기

| 후보 | 실험 | 판정 |
|---|---|---|
| 창 정의 오류 | 원문 전압 보존 θ(§3.2)는 같은 창 계산으로 봉인됐다(20/21). y = 0.0만 봉인 7(M4a·M5 VDS) 실패 | 창 식 자체는 틀리지 않았다. 다만 창이 하류 게이트 사슬을 보지 않아 출발점이 비정합 영역에 떨어진다(sf §1.1 (b)와 같은 꼴) |
| KVL 기둥 자체 불성립(헤드룸 부족) | 원문 점이 sky130 1.8 V에서 봉인됨. 원문 W/L 밀도를 그대로 옮긴 V-A는 21/21 실패(Vy `no_root`, M5 VDS < 0). sky130 pmos |VT|가 0.18 µm 공정보다 커서다 | 헤드룸은 있다. 단 밀도를 sky130에 맞게 다시 잡아야 하고, 입력 pmos는 gm/ID 15.5, 꼬리·캐스코드 nmos는 gm/ID 25 근처다 |
| current-reuse 두 블록의 가지 전류 공유(결합) 처리 | 원뿔 `M3a = −M19 + M1a + M17`, `M5 = M61 − M19 − M10 + M1a + M1b + M17 + M8`(classb schema)에 원문 전류를 넣으면 원문 KCL과 맞는다(5.522·12.317 µA). 봉인됨 | 결함 아님 |
| 정의역 상자 | 원문 점의 밀도는 모두 상자 안이다(`out/hp_cr.jsonl` translation `box`). R1·R2 원문 500 kΩ는 상자 상한 1e5 Ω 밖이지만 DC 전류가 0(`zeros: current R1`)이라 봉인에 무관하다 | 결함 아님(R 상자는 AC 값에만 관여, 미확인) |
| CMFB·R1·R2 평균 노드 | Voc·Vom·Vop(R 강하, 전류 0) 정상, SPICE 일치(§3.2) | 결함 아님 |
| **예산** | 예산 400 실패(시험점 340). **예산 2000 성공**: 시험점 927번째, 커널 1112회, 526 s, max-min 수렴(`out/l0sum_current_reuse_telescopic_ota.jsonl`) | **예산 40이 직접 원인**. 밑의 원인은 출발점 비정합으로 sf와 같다 |

### 2.3 gain view `pending: MOD5`

관여하지 않는다.
- DC 봉인 경로(`gmid_engine/sizing/*`)에 view를 읽는 코드가 0이다(`grep -l view sizing/*.py` → `theta_schema.py` 주석 한 줄뿐).
- 원문 점이 MOD5가 미결인 채로 봉인됐다.
- 층 0도 예산 2000에서 수렴했다.

### 2.4 B34(stick_diagram 폴백)

관여하지 않는다. current_reuse 단계 A·B와 탐색 컨텍스트 생성 뒤 `sys.modules`에 `stick`·`grammar`·`idioms`·`sizing_recipe` 모듈이 0개다(실측). B34는 legacy 경로 문제다.

## 3. 물리적으로 가능한 점

### 3.1 sf_pushpull (원문에 W/L 없음 -- Allen p.26-6은 IBias 50 µA·Rout ≤ 1 kΩ·Av 65 dB·GB 60 MHz만 줌)

원문 값 IBias = 50 µA에 손계산 규칙을 더해 θ를 만들었다(`scripts/hp_sf*.py`).
- 가지 25 µA, 출력 follower 50 µA, 출력 100 µA
- 자기 바이어스 R = (VGS_casc − VGS_mir + 2/(gm/ID)_mir + 0.1 V)/I
- L = 0.5 µm
- 격자: gm/ID와 y

| 단계 | 봉인 | 실패 |
|---|---|---|
| hp_sf(모든 소자 중반전) | 0/57 | y ≤ 0.35: N17 근 없음(N17 = Y + VSG18 > 1.8). y ≥ 0.4: N910 |
| hp_sf2(follower 약반전) | 0/270 | 꼬리 M3 포화, M17·M20 VDS |
| hp_sf3(거울·꼬리·follower 격자) | **280/672** | N17 216, M17·M20 VDS 176 |

- 봉인점 예(idx 49): gm/ID 거울 12·입력 15·꼬리 12·follower 25·M22 22, y = 0.23. Y = 0.947, N17 = 1.632, N20 = 0.414, vout 0.895.
- SPICE(ngspice-46 sky130 tt, 단위 되먹임 vin_n = vout, vin_p = 0.9, `out/spice_sf.jsonl`, `out/spice/sf_49.cir`):
  - 노드: 엔진 대 SPICE 차 ≤ 1.3 mV(Y 0.947/0.946, vout 0.895/0.900)
  - 전류: M1~M20 차 ≤ 0.05 %
  - 출력 M21·M22: SPICE 125 µA / 85.8 µA, 엔진 100 µA다. vout 5 mV 차가 약반전(gm/ID 23~33)에서 지수로 커진 것으로 보인다(추정). 두 소자 전류가 서로 다른 것(KCL)은 **미확인**이다.
- 판정: 봉인된다 → 엔진 탐색·출발 문제다.

### 3.2 current_reuse (원문 Xie·Chen 2019, 로컬 `assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf` p.6 Fig.6, p.7 Fig.7, p.8 Fig.8, p.9 Fig.9 치수·DC 동작점, 웹 출처 없음)

- 소자 대응(연결로 판정): M1a/b = 원문 M0/M7, M2a/b = M2/M6, M3a/b = M1/M4, M4a/b = M3/M5, M5 = M9, M6 = M8, M7 = M43, M17 = M87, M18a = M83, M18b = M82, M19 = M85, M25 = M77, M26 = M86, M20a/b = M81/M80, M22 = M88, M23a/M24b = M79/M78, M39/M40 = M65/M76.
- 원문 전류(5.723·5.522·12.32·7.878·5.103·1.196·0.339·0.857·1.397·20.45·2.199·2.502·0.350·0.384·0.260·1.534·1.396·1.273 µA)는 엔진 원뿔과 KCL이 맞는다.
- V-B(전압 보존: θ 전류 = 원문 ID, θ ln IDu = sky130 LUT에서 원문 단자 전압을 내는 밀도): **봉인 20/21**(y = 0.05~1.0). y = 0.85에서 Vip = 0.905다.
- V-A(원문 ln(ID·L/W) 그대로): 0/21. pmos |VT| 차로 Vy < 0이다.
- SPICE(`out/spice_cr.jsonl`, y = 0.85, Vip = Vim = 0.905, Iref 1.2 µA):
  - free `.op`: 바이어스·1단 노드 차 ≤ 1 mV, 소자 46/52 전류 차 ≤ 1 %. 차동 출력은 개루프라 갈라진다(Vom 0.344, Vop 1.452). 되먹임 Cf가 DC를 닫지 않는 개루프 OTA의 예상 동작이다.
  - Vom1·Vop1·Vom·Vop 고정 `.op`: 모든 노드 차 ≤ 1 mV, 전류 차 ≤ 2.3 %. 고정 전원 전류는 14~32 nA(1단 출력)·0.40 µA(출력, 가지 20 µA의 2 %)다.
- 판정: 원문 동작점이 엔진에서 봉인된다 → 엔진 탐색·출발 문제다.

### 3.3 봉인 영역의 두께 (sf_pushpull 봉인점 idx 49 주변 한 축 훑기, 축마다 201점, `out/hp_sf_width.jsonl`)

| 축 | 상자 | 봉인 구간 | 몫 |
|---|---|---|---|
| current R1a·R1b (ln A) | [−59.0, 5.0] | [−11.01, −10.37] | 1.5 % |
| current R1c | 같음 | [−11.01, −9.73] | 2.5 % |
| resistance R1a·R1b (ln Ω) | [4.6, 11.5] | [8.85, 9.79] | 14 % |
| y N20 | [0, 1] | [0.08, 0.24] | 16 % |
| ln_idu M9 | [−57.5, −10.4] | [−17.45, −13.92] | 8 % |
| ln_idu M11·M16·M19·M1·M18 | | | 10·18·18·20·22 % |
| 전류 M9·M17·M19·M21, Cc | | | 100 %(밀도 고정이면 전류는 W만 바꾼다) |

- 26축 몫의 곱은 6.7e-17이다. 축이 독립이라고 보면 무작위 시험 하나가 맞을 확률의 어림이다(**추정**: 실제 부피는 축 상관 때문에 더 크다).
- 이것으로 5735 Halton 시험점이 0인 것이 설명된다(추정).
- current_reuse는 927번째에서 맞았으므로 더 두껍다.

## 4. 일반성 (구조 조건)

- library 7회로를 예산 40으로 층 0 실행했다(`out/l0sum_lib.txt`).
  - pushpull_follower_buffer, two_stage_ota, two_stage_ota_sf, folded_cascode, common_gate_amplifier, ngcc_3stage_ff: 중심점에서 받아들여짐(시험점 0)
  - nmcnr: Halton 23번째
  - 실패는 B81 둘뿐이다.
- 실패 회로의 공통 구조 조건(연결로만 판정, 회로 이름 무관):
  - (C1) 레일 사이 KVL 경로가 **게이트–소스 강하 둘 이상**을 지난다. 경로는 W4 자유 노드나 1변수 자기참조 노드를 거친다. 그리고 그 합 + 양끝 전류원 VDsat이 공급 전압에 가깝다.
    - sf: vdd–M17–N17–(M18 sg)–Y–(M19 gs)–N20–M20–vss
    - current_reuse: Voc_des(M40 VSG)–M37b VGS–Ncmfb_tail–M38, class-AB Vg25–M18a/M18b–Vom1
  - (C2) **자기 바이어스 저항**: 한 가지 전류가 흐르는 저항의 강하가 두 게이트 전위 차(캐스코드 바이어스)를 정한다. R과 I가 독립인 ln 상자 성분이라 R·I 창이 상자의 1~2 %다(sf R1a·R1b·R1c).
  - (C3) pmos 입력쌍·pmos 캐스코드가 입력 CM 고정점에서 vdd까지 헤드룸을 나눈다. sky130 pmos |VT| ≈ 1 V라 약반전 쪽 밀도만 맞는다(current_reuse M1a gm/ID 15.5 at VSG 0.64 V).
- 통과한 회로의 VGS 사슬은 짧다(1단). pushpull의 VGS4 + VSG3 = VGS1 + VSG2 고리는 있지만 중심점이 통과했다. 그래서 위 조건은 '잠재 실패 조건'이고 충분조건은 아니다(추정).
- heldout은 재지 않았다.
- 잠재성: 위 조건을 가진 새 회로는 같은 꼴로 실패할 수 있다(추정, 근거 = 축 몫 측정 §3.3).

## 5. 기존 card 귀속과 IT-2c

- 계획 기록 grep:
  - 계획(v6.37)에 'B81' 0건이다.
  - `_drafts/user_decisions.md:871`(O-125, LA-1 완료 조건 'B81 회로는 제외하고 따로 보고'), `:879`(셈 정정)에 있다.
  - backlog 161행이 있다.
  - IT-0 기준선(`20261021-it0-baseline/cases.jsonl` m_i3)은 두 회로 모두 `n_starts 0`, `kernel_calls 40`, `eval_budget 40 declared`를 기록했다. 원인은 기록하지 않았다.
  - `.ai/context.md`(chip-design-skills·integ-it12)에 B81 관련 0건이다.
- 귀속 판정:
  - **LA-1**(N6.14, DEC-71 (4) 역산 우선 → VDS 배분(기둥 KVL, `sat_threshold` = HC-S 정본) → W 파생): 출발점을 KVL 정합으로 만드는 자리다. 계획 F-LA1(1765행)이 as-built 최소형(`layer0_center.py:1-8`)을 이미 gap으로 적었다. B81은 그 gap의 실례다.
  - **gap(계획 문언 확인 필요)**: DEC-71 '기둥'은 MOS 채널·저항 엣지만 쓴다(270행, 게이트는 엣지가 아님). 그래서 (C1) 게이트 경유 VGS 고리는 '공유 VGS(K2)·적층 헤드룸 → 쓰기 계획 θ 고정 풀이로 맞춤'(1782행)에 맡겨진다. 그 풀이가 이번에 실패한 바로 그 기계다. (C2) R·I도 VDS 배분 문언에 명시가 없다. LA-1 design(41 §5)이 둘을 덮는지는 **미확인**이다.
  - 계획 백로그 'W4 창에 VDSAT 하한'(1537행, 감사 S3)은 (b) y 쪽만 일부 덮는다. 하류 게이트 사슬은 덮지 않는다.
  - 평가 예산: 운영 E_B는 `front_budget_s`(PA-2 미결)에서 유도된다(`search/kernel.py:160-163`). 엔진에 SearchSettings 생성처는 0이다(test·harness만). 40은 test fixture 값이다.
  - DE-1·HC-S·IT-2c: 고칠 대상이 아니다. HC-S는 `sat_threshold` 정본으로 LA-1의 입력이다.
- **IT-2c 영향**(Q-D, S1·S5·S7; 브리핑의 'C2'는 이 착수 실측 조건으로 읽었다 -- 해석 미확인):
  - S1·S5 current_reuse: 사유 '층 0 시작점 없음'은 **예산 40 조건에서만 참**이다. 측정 harness 예산을 ≥ 1112(실측 커널 수)로 두면 층 0 출발점(봉인점)이 생긴다. 그러면 a_e·δA_num·servo 연립을 잴 수 있다(526 s). '미측정 + 사유'를 유지하려면 사유를 'E_B = 40 fixture에서 층 0 출발점 없음(B81, 예산 2000이면 있음)'으로 고쳐야 한다.
  - S7 sf_pushpull: 엔진 층 0으로는 예산 6000까지 출발점이 없다. 엔진만으로는 미측정 유지가 맞다. 손계산 봉인점(280점, SPICE 일치)이 있어 진단 입력으로 잴 수는 있다. 다만 엔진이 낸 점이 아니라서 **원래 취지와 다를 수 있다** -- 오케스트레이터·사용자 판단 대상이다.

## 6. 수정 대안 비교

| 칸 | (가) LA-1 범위에 B81 두 꼴을 명시해 층 0 조립으로 해결 | (나) 최소형 층 0에 KVL 출발 규칙 보강(사다리가 y·R도 KVL에서 정함) | (다) 평가 예산만 올림 | (라) W4 창에 하류 게이트 사슬·VDSAT 하한 반영 |
|---|---|---|---|---|
| 물리 정합 | VDS 배분·역산 우선이 KVL 정합 점을 만든다. (C1)(C2)를 덮을 때만 | 같음(국소 규칙) | 정합 점을 만들지 않고 찾을 뿐. sf는 6000에서도 0 | y 축만. R·I·밀도 비정합은 남음 |
| 손계산 일치 | 역산 사슬 = 손계산(DEC-73) | 손계산 규칙 일부 | 무관 | 부분 |
| design 단순성 | LA-1 design 개정 범위 안. 새 card 0 | LA-1 전에 같은 VDS 배분을 한 번 더 만듦 | 가장 단순 | 창 식 변경(IT-2b 커널 창 파일과 겹침) |
| 실측 | sf·current_reuse 봉인점 존재(§3) = 해가 있음. 효과는 구현 뒤 실측 | 손계산 규칙 hp_sf3로 280/672 봉인(규칙이 맞으면 통함을 보임) | current_reuse 2000 성공, sf 6000 실패 | y 몫 16 %만 넓힘(추정) |
| 원칙 | 위반 없음. 계획 문언(DEC-71 기둥 정의에 게이트 고리·R·I)을 먼저 고칠지 확인 필요(S-7) | ⚠ 원칙 경고: graph 단일 정본 -- VDS 배분·헤드룸 분할이 LA-1 층 0과 최소형 사다리 두 곳에서 계산됨(둘째 생산자) -- 계획 1779행 VDS 배분 정본 = LA-1 | ⚠ 원칙 경고: 상수 발명 금지 -- 예산 값을 근거 없이 고르면 상수, 운영 E_B는 `front_budget_s`(PA-2)에서 유도 -- `search/kernel.py:160-163`. harness 측정용은 실측 커널 수(1112)를 근거로 둘 때만 | 부분 해결. 계획 백로그 항목(1537행)으로는 원칙 충돌 없음 |

**권고: (가).** 두 가지를 함께 한다.
- LA-1 착수 전에 design 41 §5(VDS 배분)가 (C1) 게이트 경유 VGS 고리와 (C2) 자기 바이어스 R·I를 덮는지 대조한다. 덮지 않으면 계획 DEC-71 문언부터 고친다(계획 우선).
- LA-1 완료 조건(O-125 '따로 보고')을 'B81 두 회로 층 0 출발점 ≥ 1'로 바꿀지 사용자에게 묻는다.

IT-2c 착수 실측에는 별도로 harness 예산(측정용, 근거 = 실측 커널 1112)을 쓰는 안을 오케스트레이터가 판단한다(엔진 변경 없음).

원칙 점검:
- 새 cache·필드 0
- 상수 0(예산 값은 실측 근거로만)
- 회로 이름 무관 구조 조건
- DC만(봉인)
- 설계점 θ 고정(DEC-103)
- 계획 변경 필요 여부 명시

## 7. 미확인

- LA-1 design 41 §5가 (C1)(C2)를 덮는지(문서 대조 안 함).
- sf SPICE M21·M22 전류가 서로 다른 것(KCL 위반처럼 보임 -- 측정 함정일 수 있음).
- current_reuse 예산 2000 출발점 이후 front 결과(find_front는 돌리지 않음).
- §3.3 26축 곱은 독립 가정 어림이고, 실제 봉인 부피는 재지 않았다.
- 브리핑의 'IT-2c C2'를 Q-D·S1·S5·S7 착수 실측 조건으로 해석했다.
- R1·R2 원문 500 kΩ가 상자 밖인 것이 AC metric에 주는 영향.
- 원문 도면 판독값(특히 M57·M58·M63·M64·M36·M37 치수)은 V-A에서 일부만 썼다. V-B는 노드 전압만 썼다.


## 9. 미확인 확인 (2026-10-26 추가 실측, 같은 가드)

원자료: `wt/_scratch_b81/out/`
- `trace_cr_b2000.jsonl`·`.log`, `trace_cr_b4000_paperVB.jsonl`
- `chk_start.jsonl`
- `hp_sf_area_b.jsonl`
- `spice_sf.jsonl`, `spice/sf_49_kcl.cir`, `spice/sf_hp_sf_area_b_162.cir`

스크립트: `scripts/trace_front.py`(B80 사본, 출력 경로와 벽시계 예산만 환경변수로 바꿈), `chk_start.py`, `hp_sf_area2.py`, `spice_sf2.py`.

엔진은 무수정이고, integ-it12 `git status`는 실행 전후가 같다.

### 9.1 current_reuse: 층 0 출발점 이후 find_front (실측)

실행 조건:
- 예산 2000. 층 0은 §2.2와 같은 결정론 경로이고, Halton 927번째 점에서 커널 1112회를 썼다.
- 벽시계 예산은 7200 s로 두어 끝까지 돌렸다.

| 항목 | 값 |
|---|---|
| front·pending·unmeasured 점 | **0 · 0 · 0** |
| 실행 시간 | 1808.6 s(층 0 약 530 s 포함) |
| 커널 호출 | 1555(요청 1903, `outside_domain` 28) |
| 출발점 수 | `n_starts` 1(층 0 s1), `n_solves` 2 |
| 끝점 power | stop `converged`, 수락 반복 6, 모든 행 ≥ 0인 점이 없어 best = None(`failed_eps`). 후보 실패 재시작(`candidate_failure`) 3회 |
| 끝점 area | stop `slsqp_8`(Positive directional derivative for linesearch), 수락 반복 7, `candidate_failure` 9회 |
| ε 격자 | 두 끝점이 실패해서 돌지 않음(`eps_sweep.py:90`, B80과 같음) |

- status 4가 없어서 QP 실현 가능성 판정(IIS)은 나오지 않았다. 대신 마지막 수락점의 음수 행을 IIS 대용으로 적는다.
  - power 끝점: `spec:area_search_m2<=` c = −7.5e14 하나. P = 277 W, A = 1.57 m²
  - area 끝점: area c = −3.4e15, `ss:2:pm_cm_ss_deg>=` c = −0.68. P = 409 W, A = 7.2 m²
- 층 0 출발점 자체(첫 평가): P = **479 W**, A = **104 m²**. 면적 예산은 4e-8 m²다.
  - θ 전류는 15.9 A(M1a)·44 A(M10)·47 A(M6) 수준이다(`l0diag_current_reuse_telescopic_ota.jsonl` 마지막 줄 θ).
  - 층 0 note는 `meaning: feasibility_only`이고, 전류 상자 상한은 면적 예산에서 유도했다(`current_upper_from_area_budget_IDu_max_A_over_L2`, nmos 292 A·pmos 55 A).
- 미측정 제약: gain·ratio·parasitic_pm는 `view_pending`(MOD5), pm_ss_deg는 `dc_not_above_level`이다(S-1 note, 점 497개). 이 행들은 c 행이 없어서 front를 막지는 않는다. 다만 front 점이 생겨도 판정은 보류 분류로 간다(추정: S-1 규칙).
- front 0의 원인 판정: **B80과 같은 꼴이다**(층 0이 spec·ss 제약을 쓰지 않음). 장애 행이 B80의 rout(ss) 대신 **면적(spec)** 이다.
  - 층 0 max-min은 봉인 여유만 최대화한다. 경성 제약도 W 하한·반전 하한·원뿔뿐이다(`layer0_center.py` 머리, F-LA1).
  - 그래서 θ 전류를 상자 위쪽(A 단위)으로 밀었다.
  - 외층 SLSQP는 면적을 15자릿수 줄여야 하는데, 반복 13회와 후보 실패 재시작 12회 안에 닿지 못했다.
  - 이것은 §0 '봉인점 0' 문제와 다른 둘째 문제이고, card LA-1(DEC-71 (3) 블록 국소 제약·면적 예산)이 덮을 자리다.
- 결정 실험: 원문 전압 보존 점(V-B, y = 0.85)을 `given_starts`로 넣었다(예산 4000, 1507.8 s).
  - 결과는 front 0이고 `n_starts` 1이다. 주어진 출발점이 출발점 확인에서 거부됐다(`chk_start.jsonl`).
  - 거부 사유: `SEAL_VIOLATION lut_mismatch_no_block`, pmos W = 9.5e-8 m. 소자는 M39이고 원문 0.26 µA를 sky130 VSG 0.9 V 밀도로 흘린 결과다. W 하한 0.42 µm보다 작아 mismatch LUT 블록이 없다.
  - 이 점은 MOS 면적도 8.2e-7 m²로 예산 4e-8의 20배다(M25 W 0.80 m, 원문 VSG 0.487 V는 sky130에서 깊은 약반전).
  - **정정(§3.2)**: 원문 전압 보존 점은 DC 봉인(`size_and_seal`)만 통과했다. 커널 평가(W 하한·mismatch 블록)와 면적 예산은 통과하지 못한다. 면적과 W 하한을 함께 만족하는 current_reuse 봉인점은 **찾지 않았다(미확인)**.
- SPICE 대조: front 점이 없어 하지 않았다.

### 9.2 sf_pushpull: SPICE M21·M22 전류 차 (실측)

- 점 hp_sf3 idx 49: SPICE 출력 노드 vout의 KCL을 분해했다(`spice/sf_49_kcl.cir`, BSIM4 `[ibs]`·`[ibd]` 출력).

| 가지 | 전류(SPICE) |
|---|---|
| M22 채널(vdd → vout) | 85.8 µA 들어옴 |
| **M21 소스–벌크 접합(벌크 vdd → 소스 vout, 역바이어스 0.9 V)** | `[ibs]` = −39.3 µA, 곧 39.3 µA 들어옴 |
| M21 채널(vout → vss), `[id]` | 125.0 µA 나감 |
| M21 드레인–벌크 접합 `[ibd]` | −42.5 µA(vss 노드 쪽, vout KCL과 무관) |
| 되먹임 `Vfb`(vin_n–vout) | 4e-19 A(게이트만) |
| CL | DC 0 |

  85.8 + 39.3 = 125.1 µA로 KCL이 닫힌다.
- 원인: M21 W = 1.8e4 m다(넷리스트 `m = 3.6e9`, w = 5 µm). M21의 밀도는 θ 성분이 아니고 KVL 고리 VGS19 + VSG18 = VGS22 + VSG21에서 파생된다. 그 VSG21이 sky130 pmos에서 깊은 약반전(gm/ID 32.6)이라 W가 커졌다. 접합 누설은 W에 비례하므로 µA 단위가 됐다.
- 엔진 KCL은 채널 전류만 쓰므로 M21 = M22 = 100 µA다. SPICE에서는 vout이 단위 되먹임으로 0.900 V에 고정된다. 그래서 M22 VGS가 엔진(vout 0.895)보다 5 mV 작아 85.8 µA가 된다. gm/ID 23에서 exp(−0.005 × 23) = 0.89로 맞는다. 나머지 39 µA는 접합이 채운다.
- 판정:
  - 측정 구성 차이(되먹임이 vout을 고정)와 **모델 차이(엔진에 접합 누설 없음)** 가 겹친 것이다.
  - 엔진 KCL 누락으로 볼 범위는 W가 비현실적인 점뿐이다.
  - 같은 회로에서 면적 예산 안의 봉인점(아래)은 접합 전류가 pA(`[ibs]` −1.1e-12 A)다. 그 점에서 M21·M22 SPICE 전류는 10.03 / 10.03 µA로 서로 같고, 엔진(10 µA)과 0.3 % 차다.
  - **결함 후보(약)**: 봉인(`size_and_seal`)은 면적·W 상한과 접합 누설을 보지 않는다. 그래서 접합 누설이 가지 전류에 견줄 만한 점도 봉인 통과로 낸다. 커널·탐색의 면적 행이 그런 점을 거르므로(§9.1처럼 front에는 못 들어감) 영향은 출발점과 진단 점에 한정된다(추정). 수정하지 않았다.
- **정정(§3.1)**: hp_sf3 봉인 280점은 **모두 면적 예산 2e-8 m²를 넘는다**(M21 W ≥ 150 m). 그래서 '물리적으로 가능한 점'을 다시 쟀다(`hp_sf_area2.py`).
  - 방법: 출력 소자(M18·M19·M21·M22) L ∈ {0.15, 0.25, 0.5} µm, gm/ID 격자, 전류 10~50 µA, y 무작위 3000점
  - 결과: **봉인 482점, 그중 면적 예산 안 56점**. 최소 면적 1.5e-10 m²(L 0.15 µm, M21 W 262 µm, gm/ID 16.3)
  - 그중 vout이 0.9에 가장 가까운 점(줄 162: g18 10·g19 24·g22 22, y 0.181, M21·M22 10 µA, L 0.15 µm)을 SPICE 단위 되먹임 `.op`와 대조했다.
    - 노드 차 ≤ 20 mV. 엔진 vout은 0.9135(자유 y)이고, SPICE는 되먹임으로 0.900에 고정돼 출력 사슬 전체가 13~20 mV 내려간다.
    - 소자 전류 차 ≤ 0.6 %
  - 이 점의 rout spec(≤ 1 kΩ) 충족 여부는 재지 않았다. gm 합은 약 0.4 mS로 추정되어 미충족일 가능성이 있다.
  - 결론은 그대로다: sf_pushpull은 면적 예산 안에서도 봉인 가능한 점이 있고, 층 0이 못 찾는 것이다.

### 9.3 원칙 점검

- graph 단일 정본: 새 필드·cache·사본 0. 진단은 메모리 monkeypatch와 scratch 파일만 썼다.
- 상수: 판정에 새 상수 0. 격자·무작위 범위는 진단 표본 범위다.
- 회로 이름·태그: 판정은 연결(KCL 가지)과 SPICE 단자 전류로만 했다.
- DC/AC 분리: 9.2는 DC `.op`다.
- DEC-103: 봉인점은 θ 고정, SPICE `.op`는 W 고정 KCL 대조다.
- 계획 우선: 9.1의 면적 장애는 계획 F-LA1·DEC-71 (3) 범위(LA-1)라 계획 변경은 불필요하다(추정). 9.2의 '봉인이 접합 누설을 안 봄'은 결함 후보로만 적었다.
