# UD-17 결정 자료: F26(LUT VS 축 밖 조용한 클램프)·F27(노드전압 경로 충돌)

> 작성 2026-10-01. 저장소 읽기 전용(쓰기 0, 상태 바꾸는 git 0). topology 파일은 건드리지 않았다.
> 측정 사본: `C:/g67/repo` = HEAD `7535799`의 `git archive HEAD skills/analog-gmid-design skills/analog-grammar workspaces/run_harness.py`. 측정이 끝난 뒤 삭제했다.
> 스크립트: `_drafts/ud17_scripts/`(`ud17_eval.py`·`ud17_spice.py`·`ud17_report.py`·`run_eval.sh`·`run_seed_probe.sh`). 원자료 사본: `_drafts/ud17_scripts/out/`(`eval.jsonl`·`spice.jsonl`·`report.txt`·`eval_noGrammar.jsonl`).
> SPICE 점검은 저장소의 LUT 생성기 `sky130_lut_sweep.py`의 `_gen_netlist`/`_parse_output`을 수정 없이 썼다. ngspice-46, sky130 tt, W_ref 5 µm로 표본 LUT와 같은 넷리스트다. 다른 점은 VGS 49점 × VDS 2점(소자 vds, vds+0.0375)만 돌렸다는 것이다. 이 점검 경로는 LUT 격자점(VS 0·0.4·0.8)에서 LUT 값을 0.1~1 % 안으로 재현한다(아래 표의 "LUT" 열과 비교).

## 0. 요약 (먼저 읽을 것)

| 회로 | F27 충돌 | 근본 원인 수 | F26(축 밖)과의 관계 | 클램프를 없애면 |
|---|---|---|---|---|
| folded_cascode | 4건(1.6·1.6·1.1·1.0 V) | **3개**: (a) M1·M2의 극성 또는 단자 방향 선언(1.6 V 두 건과 1.1 V 중 0.6 V), (b) fold_group singleton 우회가 Y 컬럼 KVL을 닫지 않음(1.1 V 중 0.5 V), (c) 같은 우회가 X–out 컬럼 KVL을 닫지 않음(1.0 V) | θ* 축 밖 소자 4개(M1·M2·M5·M7)가 **전부 F27에서 파생**된다. 일관된 노드전압이면 M5 vsb 0.2, M7 0.45로 축 안이다. M1·M2는 (a)가 결정한다(NMOS면 vsb 0.2) | 거부: θ* = `InfeasibleSizingError`(M7). 일관된 vsb(0.45)로 고쳐도 M7 W가 152.5 µm에서 약 2.5 mm(×16.5, SPICE)로 커져 W_bounds 200 µm 밖이다 |
| current_reuse_telescopic_ota | 4건, 모두 0.222722 V | **1개**: 첫 단 출력 Vom1·Vop1이 두 곳에서 정해진다. 텔레스코픽 컬럼은 0.9 V를 함의하고, 출력단·class-AB 쪽 고정은 0.677 V(M10 `vds_match_vgs_of` M16 등)를 준다. 엔진이 둘을 서로 맞추지 않는다 | 축 밖 소자 4개 중 M2a·M2b(0.9227)는 F27에서 파생된다(일관값 0.7, 축 안). **M9a·M18a(0.825)는 F27과 무관한 진짜 LUT 범위 문제**다. 다만 SPICE로 잰 클램프 오차는 VGS 2.9 mV, 전류밀도 0.7 %로 무시할 수준이다 | 거부: θ* = `InfeasibleSizingError`(M9a, 메시지는 축 밖이 아니라 "gm_id 후보 없음"으로 나간다). 전체 실행 = SLSQP 3회 전부 infeasible → `ValueError` |

결정 사항은 §5에 정리했다. 요점은 세 가지다.
1. folded의 M1·M2 극성·방향과 KCL 부호는 **사용자가 판단할 회로 해석**이다.
2. current_reuse에서 Vom1을 어디에 고정하는지와 그 아래 세 소자의 헤드룸이 실제로 닫히는지도 **사용자 판단**이다.
3. "조용한 클램프·조용한 노드 선택을 거부로 바꾼다"는 원칙으로 기본안을 정할 수 있다.

부수 발견(§6)이 넷 있다.
* M2a W가 vsb 재유도 전 값(vsb 0)으로 남는다. 그래서 매칭쌍 M2a·M2b의 W가 19.8 µm 대 16.7 µm로 다르다.
* 축 밖 거부 오류가 탐색 루프에 먹혀 엉뚱한 원인으로 보고된다.
* analog-grammar가 없으면 current_reuse θ* 평가 결과가 성공에서 실패로 바뀐다(조용한 선택적 의존).
* θ* 한 점 평가 안에서도 VS 2.05 V(VDD보다 큼)가 조회된다.

---

## 1. 재현(정확한 수치)

### 1.1 F26 축 밖 조회 수 (재측정, `ud17_eval.py`, clamp 모드)

| 실행 | VS 축 밖 조회 | 다른 축 밖 | draft v0.4 값 |
|---|---|---|---|
| folded θ* 한 점 | 436 | 0 | 436 (일치) |
| folded 전체 실행 | 1,137 | 0 | 1,137 (일치) |
| current_reuse θ* 한 점 | 3,537 (값 0.8125~2.05) | 0 | 3,537 (일치) |
| current_reuse 전체 실행 | 16,235 | 0 | 16,235 (일치) |

θ* = folded `{Ibg 5e-7, r_split 0.5, r_mirror 1.5, kcl_fold_M5·M6 1.0}`(Ibg는 하한이다. 제약이 삭제돼 있어 "사이징 판정 보류" 회로다). current_reuse는 `p4_scripts/out/cr_theta.json`.

### 1.2 F27 충돌과 도달 경로 (`trace_propagate`)

`trace_propagate`는 `propagate_node_voltages()`와 같은 순서·규칙으로 노드마다 값을 정한 소자를 기록한다. 엔진 결과와 노드값·충돌 수가 같음을 확인했다(`trace_matches_engine = True`, 두 회로 모두).

엔진은 **이름순(`sorted`)으로 먼저 도달한 경로의 값을 노드에 박는다**. 나중 경로는 `conflicts`에만 남는다. 그 뒤 `reconcile_vsb_from_nodes()`가 먼저 박힌 값으로 vsb를 유도하고, 사이징이 그 vsb로 LUT를 조회한다(충돌이 있어도 멈추지 않는다).

**folded_cascode** (VDD 1.8, 모든 비다이오드 vds = 0.2, 다이오드 M7·M9 vds 0.45)

| 충돌 소자 @ 넷 | 먼저 박힌 값과 경로 | 나중 경로의 값 | 차이 |
|---|---|---|---|
| M4 @ Y | **0.0**: gnd → M11(nmos, +0.2) → tail 0.2 → **M2(pmos, source=tail) −0.2** → Y | 1.6: vdd → M4(pmos, −0.2) → Y | 1.6 |
| M1 @ X | **1.6**: vdd → M3(pmos) → X | 0.0: gnd → M11 → tail 0.2 → M1(pmos, −0.2) → X | 1.6 |
| M9 @ Vg9 | **−0.65**: (Y = 0.0) → M5(pmos, −0.2) → Vg7 −0.2 → M7(nmos 다이오드, source=Vg9, 역산 −0.45) → Vg9 | 0.45: gnd → M9(nmos 다이오드, +0.45) → Vg9 | 1.1 |
| M8 @ out | **1.4**: vdd → M3 → X 1.6 → M6(pmos) → out | 0.4: gnd → M10 → Vg10 0.2 → M8(nmos) → out | 1.0 |

**current_reuse_telescopic_ota** (네 건 모두 같은 크기 0.222722 V)

| 충돌 소자 @ 넷 | 먼저 박힌 값과 경로 | 나중 경로의 값 | 차이 |
|---|---|---|---|
| M5 @ Vy | **0.0273**: vdd → M17(0.825) → Vg25 0.975 → M18a(0.2978) → **Vom1 0.6773** → M3a(0.2) → N3a4a 0.4773 → M4a(0.45) → Vy | 0.25: gnd → M5(0.25) → Vy | 0.2227 |
| M64 @ Vbias3 | **1.4875**: vdd → M61(0.3125) → Vbias3 | 1.2648: (Vy 0.0273) → M63(0.5625) → N64_63 0.5898 → M64(0.675) → Vbias3 | 0.2227 |
| M1a @ N1a2a | **0.8773**: (Vom1 0.6773) → M2a(pmos 0.2, 역산) → N1a2a | 1.1: vdd → M6(0.25) → Vx 1.55 → M1a(0.45) → N1a2a | 0.2227 |
| M1b @ N1b2b | **0.8773**: gnd → M10(0.6773) → **Vop1 0.6773** → M2b(역산) → N1b2b | 1.1: vdd → M6 → Vx → M1b → N1b2b | 0.2227 |

### 1.3 축 밖 소자: 요청 vsb, 클램프 값, SPICE 실측 (`ud17_spice.py`)

열 설명:
* "SPICE": 요청 VS에서 같은 gm/ID(다이오드는 같은 VGS = VDS)로 잰 값.
* "LUT 클램프": 엔진이 실제로 쓴 값(VS 0.8 또는 0으로 잘린 값).
* "일관값": 충돌 상대 경로의 노드전압으로 다시 유도한 vsb에서 잰 값.
* 전류밀도는 엔진과 같은 IDu(= ID(W_ref)·L/W_ref) 정규화다. W ∝ 1/IDu.

| 회로·소자 | kind, L, vds, gm/ID | 요청 vsb (사용값) | 지표 | LUT 클램프 | SPICE @ VS 0.8 | SPICE @ 요청 vsb | SPICE @ 일관값 |
|---|---|---|---|---|---|---|---|
| folded M1·M2 | pmos, 0.34 µm, 0.2, 17.5 | 1.6 (0.8) | VGS / IDu / gm/gds | 1.073 / 4.99e-8 / 35.8 | 1.012 / 1.67e-8 / 35.7 | **1.243** / **1.03e-7** / 34.8 | (극성에 달림, §2.1) |
| folded M5 | pmos, 0.34 µm, 0.2, 19.5 | 1.8 (0.8) | 〃 | 0.886 / 1.74e-9 / 37.8 | 0.887 / 1.73e-9 / 38.0 | **1.046** / 1.73e-9 / 36.9 | vsb 0.2: 0.756 / 1.71e-9 / 38.8 |
| folded M7 (다이오드) | nmos, 0.245 µm, VGS = VDS 0.45 | **−0.65** (0) | gm/ID / IDu | 25.26 / 1.61e-9 | -- | 17.39 / 1.94e-7 (source–bulk 접합 순바이어스 상태) | vsb 0.45: **27.63 / 9.74e-11** |
| CR M2a·M2b | pmos, 1.0 µm, 0.2, 15 | 0.9227 (0.8) | VGS / IDu / gm/gds | 1.245 / 2.98e-7 / 54.4 | 1.246 / 2.99e-7 / 56.6 | 1.269 / 3.03e-7 / 55.4 | vsb 0.7: 1.225 / 2.94e-7 / 57.6 |
| CR M9a·M18a | pmos, 0.15 µm, 0.2978, 15.5 | 0.825 (0.8) | 〃 | 0.905 / 1.649e-7 / 7.436 | 0.905 / 1.649e-7 / 7.437 | 0.908 / 1.661e-7 / 7.424 | (충돌 무관) |

LUT에 VS 0.8보다 큰 데이터가 있는가: **없다.** 표본 LUT의 VS 축은 [0, 0.2, 0.4, 0.6, 0.8]이고, 체크포인트 240개(`ac_sweep_checkpoints/*_VS0~4.npz`)도 같은 5점이다. 그래서 위 "요청 vsb" 열은 LUT에서 얻을 수 없다. 그 값은 이번 ngspice 점검으로만 얻었다(U-27 전체 재생성 약 22 h 대신 소자별 98점, 회당 약 10~20 s).

클램프 오차 크기(같은 SPICE 경로 안에서 VS 0.8과 요청 VS를 비교):

| 소자 | ΔVGS | IDu 변화(W는 역수) | gm/gds |
|---|---|---|---|
| folded M1·M2 (1.6 → 0.8 클램프) | **+231 mV** | **×6.2**(W ×0.16) | −2.4 % |
| folded M5 (1.8) | **+160 mV** | −0.3 % | −2.8 % |
| folded M7 (−0.65 → 0) | -- | 요청점 자체가 비물리(순바이어스). 일관값 0.45와 비교하면 클램프 IDu가 **16.5배 크다**(W 16.5배 과소) | gm/ID 25.26 vs 27.63 |
| CR M2a·M2b (0.9227) | +23 mV | +1.3 % | −2.2 % |
| CR M9a·M18a (0.825) | +2.9 mV | +0.7 % | −0.2 % |

주의: folded M1의 gm/ID 17.5는 PMOS L 0.34 µm gm/ID 곡선의 **평탄부**에 걸려 있다(LUT 곡선 VS 0.8: …18.0, 17.6, **17.5, 17.6, 17.5**, 16.8…). 그래서 같은 VS 0.8에서도 LUT와 SPICE의 근 선택이 갈린다(VGS 1.073 대 1.012, IDu ×3). M1의 수치는 클램프 오차와 근 선택 모호성이 겹친 값이다. CR M9a(L 0.15 µm, gm/ID 15.5)도 VS 0~0.4에서 근이 두 개다(SPICE 첫 근 VGS 0.33~0.44 V, LUT 근 0.84 V). 계획의 B20(PMOS gm/ID 비단조) 종류다.

---

## 2. 회로 관점의 의미

### 2.1 folded_cascode

선언된 연결(넷 표, `folded_cascode.topology.md`):
* `tail` = M1.source, M2.source, M11.drain. M11은 nmos이고 source = gnd다.
* `X` = M1.drain, M3.drain(pmos, source vdd), M6.source(pmos).
* `Y` = M2.drain, M4.drain, M5.source.
* M5 → Vg7 → M7(nmos 다이오드) → Vg9 → M9(nmos 다이오드) → gnd.
* M6 → out → M8(nmos) → Vg10 → M10 → gnd.

(a) **M1·M2(pmos, source = tail)와 꼬리 전류원 M11(nmos sink)은 동시에 성립하지 않는다.**
* KCL: PMOS 전류는 source로 들어가 drain으로 나간다. 그러면 tail 노드에서 M11과 M1·M2가 모두 **전류를 빼간다**. 전류를 넣어 주는 소자가 없다.
* 선언된 sizing feed도 스스로 어긋난다. `r_split_M1_M2`는 "M1·M2가 꼬리 전류를 반씩 나눔"(전류가 X·Y → tail → M11로 흐름)을 뜻한다. 반면 `kcl_fold_M6`의 I(M6) = I(M1) + I(M3)(sign 생략 = +1, `_feed_root_signed_sum` 5411행)는 M1 전류가 **X로 들어감**을 뜻한다. 한 소자의 전류 방향이 두 선언에서 반대다.
* θ* 값: I3 = 0.75 µA, I1 = 0.25 µA, I6 = 1.0 µA, I11 = 0.5 µA. NMOS 입력 폴디드의 교과서 식이라면 I6 = I3 − I1 = 0.5 µA다.
* 바이어스: PMOS가 source 0.2 V(tail)에서 gm/ID 17.5로 켜지려면 |VGS| ≈ 1.24 V(SPICE, 요청 vsb 1.6)가 필요하다. 게이트가 약 −1.04 V여야 하므로 레일 [0, 1.8] 밖이다.
* 연결 패턴(nmos tail sink, 폴딩 노드 위 pmos 전류원 M3·M4, pmos 캐스코드 M5·M6이 아래로 접힘, nmos 미러 M7~M10)은 **NMOS 입력 폴디드 캐스코드**의 전형과 같다.
* 이것이 X·Y의 1.6 V 충돌이다. vdd 쪽 경로(M3·M4)는 X·Y = 1.6 V를 주고, tail 쪽 경로는 PMOS 부호로 X·Y = tail − 0.2 = 0.0 V를 준다.

(b) **Y 컬럼의 수직 KVL이 닫히지 않는다.**
* 경로: vdd → M4(0.2) → Y → M5(0.2) → Vg7 → M7(다이오드 0.45) → Vg9 → M9(다이오드 0.45) → gnd. 합은 1.3 V이고 VDD는 1.8 V다.
* 실제 회로에서 Vg7 = VGS9 + VGS7 ≈ 0.9 V는 아래 다이오드가 정한다. Y = V(bias3) + VSG5다. 남는 0.5 V는 M4·M5의 VDS로 간다. 어떻게 나뉘는지는 **선언되지 않은 외부 바이어스 bias3**이 정한다.
* 엔진의 fold_group singleton 우회(`sizing_recipe.py` 7507~7563행)는 소자마다 역할별 최소 vds만 주고, 주석에 "병합 노드 전압의 정확한 KVL 일치는 이 근사가 보장하지 않는다"고 적혀 있다.
* Vg9 충돌 1.1 V = Y 오류에서 넘어온 0.6 V(Y가 1.6이면 Vg7 = 1.4, Vg9 = 0.95) + 이 KVL 공백 0.5 V.

(c) **출력 컬럼의 KVL이 닫히지 않는다.**
* 경로: vdd → M3 → X → M6 → out → M8 → Vg10 → M10 → gnd. vds 합은 0.8 V이고 VDD는 1.8 V다(공백 1.0 V).
* out은 고임피던스 출력이라 DC는 출력 공통모드(부하·궤환)가 정한다. 선언에 출력 CM이 없고, 엔진도 이 공백을 배정하지 않는다.
* out 충돌 1.0 V가 이것이다.

| 소자 | 노드 | 엔진값(먼저 박힌 경로) | 다른 경로의 값 | 물리적으로 기대되는 값(조건부) |
|---|---|---|---|---|
| M1·M2 | X / Y | 1.6 / 0.0 | 0.0 / 1.6 | NMOS 입력이면 X = Y ≈ 1.6(vdd − VSD3), tail ≈ Vin,cm − VGS1 |
| M5 | source Y | 0.0 → vsb 1.8 | 1.6 → vsb 0.2 | Y = V(bias3) + VSG5 (bias3 미선언) |
| M7 | source Vg9 | −0.65 → vsb −0.65 | 0.45 → vsb 0.45 | Vg9 = VGS9 ≈ 0.45 → vsb 0.45 |
| M8 | drain out | 1.4 | 0.4 | 출력 CM(미선언). 두 끝 사이 어딘가이고 공백 1.0 V가 M3·M6·M8·M10에 나뉨 |

### 2.2 current_reuse_telescopic_ota

선언된 연결:
* 첫 단 텔레스코픽 컬럼: vdd → M6·M7(pmos 꼬리) → Vx → M1a(pmos 입력) → N1a2a → M2a(pmos 캐스코드, Vbias2) → **Vom1** → M3a(nmos 캐스코드, Vbias3) → N3a4a → M4a(nmos 입력) → Vy → M5(nmos 꼬리) → gnd.
* Vom1에 붙은 것: M26.gate(2단 출력 nmos), class-AB 배터리 M18a·M18b, 싱크 M19, Rz2.

**하나의 원인**:
* 텔레스코픽 컬럼(`diffpair_branch_a`)은 VDD를 혼자 나눠 갖는다(0.25 + 0.45 + 0.2 | 0.2 + 0.45 + 0.25 = 1.8). 그래서 Vom1 = 0.9 V를 함의한다.
* 반면 Vom1·Vop1은 2단 출력 소자의 게이트다. DC에서 VGS(M26)·VGS(M16)이어야 한다. 선언 `M10.vds_match_vgs_of = "M16"`이 정확히 이 구속이다(물리적으로 맞다). 그 결과 Vop1 = Vom1 = 0.6773 V다.
* 두 값이 0.2227 V 다르다. 엔진에는 "한 vertical_stack 안의 노드가 다른 그룹의 구속으로 고정됐다"는 규칙이 없어서 이 차이를 맞추지 않는다.
* 네 충돌은 모두 이 차이가 다른 경로로 번진 것이다. Vy·Vbias3(아래 반쪽과 그 replica `vbias3_stack`, budget_reference M5), N1a2a·N1b2b(위 반쪽).

**회로 의미**:
* Vom1이 출력단 요구대로 0.677 V라면 아래 반쪽(M3a·M4a·M5)에 **0.677 V만 남는다.** 엔진의 현재 배정 최소합은 0.9 V다.
* 그대로 두면 꼬리 M5의 VDS가 27 mV(경로상 Vy = 0.0273)여서 포화를 벗어난다. 꼬리 전류가 제어되지 않는 동작점이다.
* 반대로 컬럼 배정(0.9)을 믿으면 2단 출력 소자의 게이트가 0.9 V다. 그러면 출력단 전류가 θ*가 가정한 26.2 µA가 아니다.
* 어느 쪽이 설계 의도인지(Vom1을 누가 정하나: CMFB? 출력단 VGS?)와, 0.677 V 안에 아래 세 소자가 들어가는지가 회로 판단이다.

| 소자 | 노드 | 엔진값 | 다른 경로의 값 | 의미 |
|---|---|---|---|---|
| M5 (꼬리) | drain Vy | 0.0273 (Vom1 0.677 기준) | 0.25 (자기 vds) | Vom1 = 0.677이면 VDS5 = 27 mV(triode) |
| M64 (replica) | drain Vbias3 | 1.4875 (M61) | 1.2648 (Vy 기준 replica) | replica가 잘못된 Vy에 기준을 둠 |
| M1a·M1b (입력) | drain N1a2a·N1b2b | 0.8773 | 1.1 | 위 반쪽에 0.2227 V가 더 걸려야 함 |
| M2a·M2b | source N1a2a·N1b2b | vsb 0.9227 (축 밖) | vsb 0.7 (축 안) | F26 중 두 소자는 이 충돌의 파생 |
| M9a·M18a | source Vg15·Vg25 | vsb 0.825 (충돌 없음) | -- | pmos bulk를 vdd에 둔 가정의 결과. bulk를 자기 source(별도 n-well)에 두면 vsb 0 |

---

## 3. 원인 후보 분류 (회로별, 근거 포함)

판정은 하지 않는다. 회로 해석은 공동분석 대상이다(메모리 "회로위상 해석은 항상 공동분석"). 아래는 후보와 근거다.

### 3.1 folded_cascode

| 충돌 / 축 밖 | topology 선언(사용자 공동분석) | 엔진 규칙 | LUT 범위(데이터) |
|---|---|---|---|
| X·Y 1.6 V, M1·M2 vsb 1.6 | **유력.** M1·M2 kind(pmos) 또는 source/drain 방향. 근거: tail KCL 불가, 선언 feed 두 개의 전류 방향 모순, PMOS 게이트가 레일 밖(−1.04 V)이어야 함(SPICE), 연결 패턴이 NMOS 입력 폴디드 전형과 같음. 관련 메타 `kcl_fold_M5/M6`의 부호(I6 = I3 − I1이 전형) | 보조. 충돌 시 이름순 첫 경로 값을 조용히 채택하고 그 값으로 vsb를 유도한다(reconcile이 conflicts를 보지 않음) | 아님(축을 늘려도 비물리 바이어스는 그대로) |
| Vg9 1.1 V, M7 vsb −0.65, M5 vsb 1.8 | 0.6 V분은 위 행의 파생이다. 나머지는 `fold_group`·`headroom_role`의 singleton 우회 선택과 bias3(외부 바이어스) 전압 미선언 | **유력(0.5 V분).** fold_group singleton 우회가 KVL을 닫지 않는다(코드 주석이 명시). 순바이어스(−0.65)를 그대로 LUT에 넘긴다 | 아님. 일관값이면 M5 0.2, M7 0.45로 축 안 |
| out 1.0 V | 출력 공통모드 미선언 | **유력.** 같은 우회로 출력 컬럼 공백 1.0 V가 배정되지 않음 | 아님 |

### 3.2 current_reuse_telescopic_ota

| 충돌 / 축 밖 | topology 선언(사용자 공동분석) | 엔진 규칙 | LUT 범위(데이터) |
|---|---|---|---|
| 네 충돌(0.2227 V), M2a·M2b vsb 0.9227 | 가능. `diffpair_branch_a` 컬럼을 Vom1·Vop1에서 위·아래로 나누고 아래 반쪽을 출력단 VGS 구속(M10·M19 쪽)에 묶는 선언(`budget_reference_device` 등). 이것이 설계 의도인지가 질문이다 | **유력.** 다른 그룹이 고정한 공유 노드를 컬럼 배정이 모른다(교차 그룹 노드 구속 없음). 충돌 노드 값을 이름순으로 고르고 그 값으로 vsb를 유도한다 | 아님. 일관값 0.7로 축 안 |
| M9a·M18a vsb 0.825 | 가능. class-AB 배터리 pmos의 bulk 연결(vdd vs 자기 source). DEC-61의 `bulk` 필드로 선언할 수 있다 | 아님 | **해당.** 0.025 V 초과. 클램프 오차는 ΔVGS 2.9 mV, IDu 0.7 %(SPICE) |
| θ* 평가 중 VS 0.8125~2.05 조회(3,537회) | -- | 탐색·중간 계산이 VDD보다 큰 vsb를 만든다(2.05 > 1.8). DEC-61의 \|V(s) − V(b)\| ≤ 레일 폭이면 물리적으로 나올 수 없는 값이다 | U-27(VS 0~1.8)도 2.05는 덮지 못한다 |

---

## 4. 사이징 결과에 대한 영향(감도)

모드 설명:
* "거부" = VS 축 밖 조회에서 `ValueError`(DF-27 #25 상당).
* "외삽" = 축 밖만 마지막 구간 기울기로 선형 외삽한 가상의 연장 LUT. U-27 대용이 아니라 감도 추정용이다. 선형 외삽이 실측을 대신하지 못한다는 점은 아래 SPICE 비교가 보여 준다.

### 4.1 거부(클램프 → 거부)

| 실행 | 결과 |
|---|---|
| folded θ* | `InfeasibleSizingError`: M7 다이오드, vsb −0.65가 LUT 범위 밖(18 s) |
| folded 전체 | 400 격자점 전부 infeasible → `ValueError`(draft v0.4 C4 측정, 같은 HEAD) |
| current_reuse θ* | `InfeasibleSizingError` M9a: "W_bounds 안에 드는 gm_id 후보가 없다". **실제 원인(축 밖)이 메시지에 안 나온다**(탐색 루프가 축 오류를 '후보 없음'으로 흡수) |
| current_reuse 전체 | SLSQP 3회 전부 infeasible → `ValueError`(598.7 s). 시도별 사유는 M63 "gm_id 후보 없음", M39/M40 적층 다이오드, M11a W 범위. 역시 축 밖이라는 말이 없다 |

즉 #25를 그대로 병합하면 두 회로 모두 정본 실행이 실패하고, current_reuse는 **원인 표시가 틀린 실패**가 된다(§6.2).

### 4.2 외삽(가상의 연장 LUT) -- θ* 한 점

| 회로 | metric 변화 | 소자 변화(주요) |
|---|---|---|
| folded | gain_db 41.02 → 44.65 (+3.6 dB), pm_deg 87.26 → 86.02 | M1·M2 gm/ID 17.5 → 25.5, W 1.70 → 1.19 µm. M5 gm/ID 19.5 → 29, **W 195 → 4.2 µm**. M7 W 152.5 → 2.18 µm. M7은 음수 방향 외삽이라 비물리이고, SPICE 일관값으로는 오히려 ×16.5로 커진다 |
| current_reuse | area −0.35 %, parasitic_pm +0.25°, 나머지 < 0.01 % | M2b W 16.70 → 14.66 µm(−12 %. SPICE는 −1.3 %로 외삽이 과장), M9a·M18a W −1.3 % |

### 4.3 외삽 -- 하네스 전체 실행

| 회로 | θ* | metric 변화 |
|---|---|---|
| folded | 동일(Ibg 하한) | gain_db 41.06 → 44.31, pm_deg 87.22 → 85.96 |
| current_reuse | **이동**: L_class__M68 0.511 → 0.466 µm, L_class__M8 0.474 → 0.455 µm, f_slew 미세 | area 806.9 → 724.5 µm²(−10.2 %), gain_full_circuit 67.08 → 66.24 dB, cmrr 72.55 → 71.03 dB, psrr 72.49 → 71.49 dB, parasitic_pm 75.0 → 76.1°, mirror_ratio_error 3.19 → 3.54 mV, power 동일 |

해석:
* **current_reuse**: 물리적 클램프 오차는 작다(M9a 0.7 %, M2b 1.3 %). 하지만 SLSQP 정본 해는 θ 연속변수가 움직여 area가 10 % 바뀔 정도로 민감하다. 그리고 탐색 중에는 VS 2.05까지 조회된다. "작은 오차라 무해"라고 말할 수 없고, 결과 숫자가 클램프 규칙에 의존한다.
* **folded**: 수치 변화(gain 3.3~3.6 dB, W 수십 배)는 크다. 그러나 원인이 LUT 범위가 아니라 §2.1의 비물리 노드전압이다. 외삽도 클램프도 둘 다 틀린 입력에 대한 답이다. 일관된 노드전압(M7 vsb 0.45)이면 M7 W가 약 2.5 mm(SPICE IDu 비 16.5)로 W_bounds를 넘어 θ*가 infeasible이 된다. 지금 보고되는 folded 사이징(θ* = Ibg 하한, gain 41 dB)은 물리적으로 성립하지 않는 동작점 위의 값이다. 이 회로는 제약 삭제로 이미 "사이징 판정 보류"다.

---

## 5. 사용자 결정과 기본안

### 5.1 사용자가 정할 것 (회로 해석 / connectivity -- 착수 조건)

| id(제안) | 질문 | 자료 | 막는 것 |
|---|---|---|---|
| **UD-17a** | folded M1·M2: (1) kind를 nmos로 바꾼다(NMOS 입력 폴디드), (2) pmos 유지하되 source/drain을 바꾼다(X·Y = source), (3) 원문(Maloberti p.34)이 정말 pmos 입력이고 꼬리를 다른 곳에 둬야 한다 -- 중 무엇인가 | §2.1 (a), §3.1. tail KCL, feed 전류 방향 모순, 게이트 −1.04 V(SPICE) | folded의 F26·F27 해소 전부. connectivity라 사용자만 고친다 |
| UD-17b | folded `kcl_fold_M5`·`kcl_fold_M6` 부호(I6 = I3 − I1?). UD-17a 결과를 따른다 | §2.1 (a) | 같은 card |
| UD-17c | folded Y 컬럼 공백 0.5 V와 출력 컬럼 공백 1.0 V를 어디에 둘지: bias3 전압과 출력 CM을 선언할지, 엔진이 fold_group 컬럼 KVL을 풀게 할지 | §2.1 (b)(c) | folded 충돌 2건 |
| **UD-17d** | current_reuse: Vom1·Vop1 DC를 무엇이 정하는가(출력단 VGS = 0.677 V가 의도인가). 그렇다면 아래 반쪽 M3a·M4a·M5가 0.677 V 안에 들어가야 하는데 현재 최소합은 0.9 V다. 설계를 바꿀지(VDS 배분, 출력단 VGS), 컬럼 분할 선언을 할지 | §2.2, §3.2 | current_reuse 충돌 4건, M2a·M2b 축 밖 |
| UD-17e | current_reuse class-AB 배터리 pmos M9a·M18a의 bulk: vdd인가 자기 source인가(DEC-61 `bulk` 필드) | §2.2 표 끝 행 | M9a·M18a 축 밖(0.825) |

### 5.2 원칙으로 정할 수 있는 기본안 (근거)

1. **조용한 클램프 금지(DF-27 #25 계획대로).** 근거: 사용자 원칙(조용한 폴백 금지), §1.3에서 클램프 값이 물리값과 최대 6배(M1)·16배(M7) 다름.
2. **충돌 노드에서 vsb를 유도하지 않는다.** conflicts > tol_V이면 #23의 SEAL_VIOLATION으로 멈추고, `reconcile_vsb_from_nodes()`가 충돌 노드의 값으로 vsb를 쓰지 않게 한다(#23 범위에 포함하거나 #23 직후 card). 근거: folded F26 4개 중 3개(M5·M7, 그리고 극성을 고치면 M1·M2)와 current_reuse 2개(M2a·M2b)가 이름순 첫 경로 선택의 파생이다.
3. **축 밖 오류는 고유 클래스로 끝까지 올린다.** 탐색 루프가 `lut_axis_out_of_range`를 "gm_id 후보 없음"으로 흡수하지 않게 한다(DF-27 계약에 test 추가). 근거: §4.1 current_reuse 두 실패의 메시지가 원인을 가림.
4. **선형 외삽은 대안으로 쓰지 않는다.** 근거: M2b 외삽 −12 % 대 SPICE −1.3 %, M7은 음수 방향이라 비물리. 축 연장은 U-27 실측 데이터로만 한다.
5. **U-27의 VS 상한 1.8 V는 유지.** VDD를 넘는 vsb(2.05)는 연장으로 덮을 대상이 아니라 거부 대상이다(DEC-61 \|V(s) − V(b)\| ≤ 레일 폭). 근거: §3.2 마지막 행.
6. **#22(DEC-61 abs)만으로 M7을 덮지 않는다.** abs(−0.65) = 0.65는 일관값 0.45와도 다르다. 순바이어스는 6b가 거부해야 한다(draft #22 문언 그대로). UD-17 자료에 이 수치를 적는다.
7. **IC11 대상 우선순위**(draft §10.6-0) current_reuse → folded는 유지한다. 근거: current_reuse 충돌은 원인 하나이고, 진짜 축 밖은 0.025 V(오차 0.7 %)뿐이다. folded는 UD-17a 전에는 물리적 동작점이 없다.

### 5.3 draft v0.4에 반영할 사실 (제안)

* F27 행: "folded 4건 = 원인 3개, current_reuse 4건 = 원인 1개(Vom1 이중 구속)". 경로 표는 §1.2.
* F26 행: "folded θ* 축 밖 4소자 전부 F27 파생, current_reuse는 M2a·M2b 파생 + M9a·M18a 진짜(0.025 V, 오차 0.7 %)".
* #25 행: 거부 시 current_reuse 메시지 오귀속(§4.1). 기본안 3을 test (a)에 더할 것.
* UD-17 행: 위 UD-17a~e로 쪼갠다. a·d가 착수 조건이다.

---

## 6. 부수 발견 (이번 측정에서 나온 것, 범위 판단 필요)

1. **M2a W가 vsb 재유도 이전 값이다(엔진).**
   * current_reuse θ*에서 M2a W = 19.795 µm다. 이것은 LUT vsb **0**에서의 값이다(`gm_id_to_id_density` 역산이 비트 일치).
   * 매칭 파트너 M2b W = 16.701 µm는 vsb 0.8(클램프)에서의 값이다. 같은 ID·gm/ID·L인데 매칭쌍 W가 18 % 다르다.
   * M2a는 `L_cascode` theta의 권위 있는 소스(metric_stage_budget)라 reconcile 뒤 재사이징이 건너뛰어지는 것으로 보인다. clamp·외삽 두 모드에서 M2a W가 같다는 점이 근거다.
   * SPICE 일관값(vsb 0.7)과 비교하면 M2a W는 16 % 과대다.
2. **축 밖 거부 오류가 원인을 잃는다**(§4.1). DF-27 card의 계약 test 후보.
3. **analog-grammar 선택적 의존이 결과를 바꾼다(인프라).**
   * `skills/analog-grammar`를 빼고 `skills/analog-gmid-design`만 archive한 첫 사본에서는 current_reuse θ* 평가가 `vertical_stack_id 그룹 ['biasgen_vop_a', 'biasgen_vop_floatsrc_sink'] 순환 의존` `ValueError`로 실패했다. 해시 시드 0~7, CRLF 무관, 8/8 재현.
   * analog-grammar를 넣으면 성공한다.
   * 원인: `stick_diagram._import_analog_grammar()`가 ImportError에서 조용히 None을 돌려주는 폴백이다.
   * 메모리 "인프라 작업은 엔진을 막을 때만"에 따라 백로그 후보로만 둔다. 측정 스크립트가 analog-grammar를 함께 복사해야 한다는 점은 다음 측정 브리핑에 넣을 것.
4. **gm/ID 근 모호성(B20 종류).** folded M1(gm/ID 17.5, PMOS L 0.34)은 곡선 평탄부에 있다. LUT와 SPICE가 VS 0.8에서도 근을 다르게 고른다(IDu ×3). CR M9a(PMOS L 0.15)는 VS ≤ 0.4에서 근이 두 개다. 클램프 문제와 별개로 이 소자들의 W는 근 선택에 민감하다.

## 부록: 측정 명령

| 단계 | 명령 | 결과 |
|---|---|---|
| 사본 | `git -C <repo> archive HEAD skills/analog-gmid-design skills/analog-grammar workspaces/run_harness.py \| tar -x -C C:/g67/repo` | `7535799` |
| 평가 | `run_eval.sh`: θ* clamp·extrap, 전체 clamp·extrap, 두 회로. 그 뒤 raise θ* 두 회로 + current_reuse 전체 | `out/eval.jsonl` |
| 경로 추적 | `ud17_eval.py`의 `trace_propagate`(엔진과 대조 True) | §1.2 |
| SPICE | `ud17_spice.py`(sky130_lut_sweep 생성기 그대로, VGS 49 × VDS 2) | `out/spice.jsonl` |
| 요약 | `ud17_report.py` | `out/report.txt` |
| 시드·CRLF 점검 | `run_seed_probe.sh`, CRLF 사본(삭제됨) | §6.3 |
