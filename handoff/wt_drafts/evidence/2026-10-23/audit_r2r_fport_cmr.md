# 결정 감사 3번·8번(r2r) -- F 성분 미선언 입력 포트와 레일 밖 CMR, 실측·대안 비교

- 작성: 2026-10-23, 측정·대안 비교 agent. 엔진·계획·design·spec은 고치지 않았다. git은 읽기만 했다.
- 대상 감사: `wt/_drafts/evidence/2026-10-23/decision_audit_O61_O117.md` §3.1(O-61 P4 (b) → O-117 F 성분), §3.8(O-117 레일 자름).
- 엔진: `wt/integ-it12` `4fc0ca1d`(계획 v6.35.1 병합본). 계획 = `wt/integ-it12/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(이하 P).
- 작업 폴더: `wt/_scratch_audit_r2r/`
  - `scripts/`: `eng_seal_r2r.py`(원 `icmr_definition_review/scripts/eng_seal.py`를 경로만 바꿔 재사용, heldout·spec 경로 인자), `stage_a.py`, `mknet.py`(봉인점 → ngspice, 기하 finger w = LUT `slice_map[(kind, w_key)].w_m`, m = W/w_m), `runspice.py`(.op·servo·개루프 훑기), `kcl_servo.py`(P:603 KCL servo 감도), `ana.py`·`perdev.py`·`cmp_op.py`(판정)
  - `out/`: 봉인점 `r2r_opamp{,.dc0.9,.dc1.48}.engine.json`, `kcl_servo*.json`, `ana_*.json`, `perdev_*.json`, `op_compare.jsonl`, `runs.log`
  - `spice/`: 넷리스트·로그·wrdata
- ⚠ heldout 주의: r2r은 heldout이다(P:1272, DEC-98, U-75 -- 엔진 개발 측정에 쓰지 않는다). 이 측정은 지시에 따른 감사 측정이다. 엔진·test·spec은 바꾸지 않았다. 이 결과를 근거로 규칙을 바꾸면 'heldout을 엔진 개발 근거로 썼다'에 해당하는지는 사용자가 판단할 몫이다(§5 원래 취지와 다름 3).

---

## 0. 결론

1. **F 성분 미선언 포트의 정체**: r2r의 두 입력 `Vinn`·`Vinp`는 MOS gate에만 닿는 넷이다(topology: Vinn = M1·M3 gate, Vinp = M2·M4 gate).
   - θ 고정 쓰기 계획에서는 이 넷을 "입력쌍 VGS로 쓴다". 사슬은 `VDD →(M31 diode) n_m31 →(M8 VGS) tail_p →(M1 VGS) Vinn →(M3) tail_n →(M4) Vinp`다(엔진 writer 실측, §1.2).
   - 사슬 머리가 레일 VDD(F)라서 `writer_head` = rail이다. 그래서 '`F 성분 미선언`'으로 분류된다(`E/sizing/block_columns.py:240,804`).
   - 그러나 gate 전용 넷에는 DC 전류가 들어가지 않는다. 회로는 이 넷의 DC를 정하지 않는다. 'writer'는 θ 틀이 M1 전류를 θ로 고정해서 생긴 장부상 방향일 뿐이다.
2. **KCL 틀에서 함께 구동할 수 있다(실측)**. 연립은 특이하지 않다.
   - 엔진 `graph.ss_nodal`은 이미 두 포트를 고정 노드로 둔다(`ss_inputs = [Vinn, Vinp]`). 이득 계산과 **같은 인수분해**다.
   - 함께 구동은 우변만 바꾼다. servo 피벗 a_e = 40.4 V/V로 0이 아니다.
3. **SPICE 실측**: 두 포트를 함께 구동하는 servo 훑기는 V_cm −0.59 ~ 2.29 V 전 구간에서 수렴했다. 출력은 봉인점에 0.22 mV 안으로 묶였다. 그 포트를 함께 구동한 ICMR은 물리적으로 정의된다.
   - 영역 창(모든 MOS VDS ≥ VDsat)은 SPICE로 [1.4530, 1.5023] V다.
   - 엔진 KCL 선형 끝은 [1.4736, 1.4977] V다. 보수적이고, 끝 소자가 같다(M13 아래, M17 위).
4. **같은 회로에 input_dc만 선언하면** 지금 규칙도 두 포트를 '선언 포트'로 함께 구동한다. 그때 정의 불능이 풀린다(실측: 0.9 V 선언 시 봉인·SPICE 일치, KCL 창 [0.896, 0.958] V, SPICE [0.865, 0.969] V).
   - 즉 지금 규칙에서 정의 가능 여부는 물리가 아니라 **무관한 선언 유무**가 정한다.
5. **레일 밖 CMR**: 원문 CMR 'VSS−0.4 ~ VDD+0.5'는 실측 기능 범위다(PDF p.7 / JSSC p.1511 본문, PDF p.8 / JSSC p.1512 Table I). 입력 전압이 실제로 레일 밖에 있다는 뜻이다. 'all-sat' 정의도, ESD 언급도 없다.
   - 지금 1.8 V 이식 봉인점에서는 영역 창이 레일 안에서 끝나 레일 자름이 발동하지 않는다(영향 0).
   - 원문 3.3 V 조건이면 레일 자름이 4.2 V를 3.3 V로 줄인다(−21 %).
6. **권고**: 3번은 (나) KCL 함께 구동이다. θ 틀 `node.dc_window`의 `f_component_undeclared`는 그대로 둔다. 8번은 (가) 레일 자름 유지이고, (나) spec 선언 허용 범위는 발동 조건부 기록으로만 남긴다.

---

## 1. F 성분 미선언 입력 포트 -- 무엇이고 왜 쓰기 사슬로 정해지나

### 1.1 계획·엔진 정의

- P:603: "F 성분 미선언 입력 포트(N6.6 범위 1 -- 성분이 레일·W3에 닿아 writer 사슬로 DC가 정해지는 입력 DC 미선언 포트)는 함께 훑는 구동에서 빼고 봉인점 값에 고정하며, 그 회로의 ICMR 세 metric은 정의 불능이다 … 그 포트를 x로 움직이는 일반형은 포트 노드의 writer를 바꾸는 회로 해석이라 공동분석 대상이고, 채택하지 않은 결정(O-61 P4 (b) (가))을 유지한다."
- P:1409 F-IT9: "r2r_opamp는 그 성분이 레일 F에 닿아 입력 포트가 W4 뿌리도 아니다." G_vgs 엣지는 MOS (gate, source)와 저항 단자다.
- 엔진(θ 틀, `node.dc_window`)
  - `E/sizing/block_columns.py:240` `writer_head`: writer 사슬을 `known` 쪽으로 거슬러 간 끝이 고정 관계(F)이면 F 성분이다.
  - `:804`: 입력 DC 미선언이고 뿌리가 아닌 입력 포트가 F 성분이면 `Window(None, None, 0, "f_component_undeclared")`다.
  - test `E/tests/sizing/test_block_columns.py:1159`(toy: in = M1 gate, source = gnd)가 이를 고정한다.
- KCL ICMR(`icm_config`·`node.dc_window_cfg`)은 integ-it12에 아직 구현이 없다(`grep icm_config` → test_writer_plan.py 문서 문자열만). 그래서 이 규칙이 KCL에 미치는 영향은 지금 계획·design 수준이다.

### 1.2 r2r 실측 writer(엔진 layer0 시작 봉인점, `out/r2r_opamp.engine.json`)

| 넷 | writer 관계 | 소자 | known |
|---|---|---|---|
| n_m31 | vgs_gate | M31(diode) | VDD (F) |
| tail_p | vgs_source | M8 | n_m31 |
| **Vinn** | vgs_gate | M1 | tail_p |
| tail_n | vgs_source | M3 | Vinn |
| **Vinp** | vgs_gate | M4 | tail_n |

- 두 포트의 사슬 머리는 VDD다. 둘 다 F 성분 미선언 포트이고, 구동할 포트가 0개다. 그래서 지금 규칙으로 ICMR 세 metric은 정의 불능이다.
- 쓰기 사슬로 '정해지는' 이유: θ 틀은 M8·M1 전류를 θ(좌표)로 고정한다. 그러면 VGS가 LUT에서 정해지고, gate 전용 넷의 전압이 역산된다. 즉 입력 공통모드 x0는 M8(전류 스위치) 전류 θ의 함수다. 봉인점 x0 = Vinn 1.4828 V, Vinp 1.4759 V(차 7 mV)다.
- 물리: gate 전용 넷의 DC는 외부 구동원이 정한다. 회로는 전류를 넣지 않는다. 'writer를 바꾼다'는 θ 틀의 장부 문제이지 회로의 물리 변화가 아니다.

### 1.3 S1 정지 사유(감사 보고서 정정)

- 감사 §3.1은 "이상 전압원 5개 때문에 S1 정지"라고 적었다. 지금 integ-it12에서는 사유가 다르다.
  - 바이어스 전압원은 `bias_inputs`(vb1·vb3·vb4·vb5n·vb6n)로 바뀌어 이상 전압원이 아니다.
  - Stage A 정지 사유는 `unsupported_rule_branch|loop_record_only|transfer:0|{n_fn1,n_mn},{n_fp1,n_mp},{n_m6,n_m9,tail_n,tail_p}|global_feedback_or_cross_coupled` 3건이다(`out/r2r_opamp.stage.json`).
  - 앞의 두 loop는 summing circuit의 floating 전류원 루프다. 셋째는 gm 제어 전류 스위치 루프다.
- 그러나 진단 경로(`run_stage_b(diagnostic=True)` → `build_kernel_context` → `layer0_start` → `size_and_seal`)는 봉인점을 낸다. 그래서 이 감사는 엔진 봉인점으로 측정했다.
- 봉인점은 탐색 전 layer0 시작점이다. 설계 품질은 없다(예: M26 m = 31879, 여유 0.003 V 소자 다수). 정의 가능 여부와 연립 특이성을 판정하는 데만 쓴다.

---

## 2. KCL(봉인점 DC 야코비안 + servo Schur 1칸)로 함께 구동 -- 판정

### 2.1 손계산(특이성)

- KCL 계는 G·v = 0이고, 고정 노드 = ac 접지 ∪ 입력 넷이다(P:603 'ICMR servo 감도 -- KCL').
- 고정 노드는 미지수에서 빠지고, 그 열은 우변으로 간다. 함께 구동(모든 입력 +x)과 여기(e)는 **우변 두 개**일 뿐이다. 인수분해할 행렬은 내부 노드 G_ii 하나다.
- G_ii가 특이하면 이득(T) 계산도 이미 불가능하다. 그 경우는 기존 fail-closed 갈래(연립 특이·DC 전도 결측)가 잡는다.
- 그러므로 함께 구동이 **새로** 특이성을 만들 수 없다. 남는 조건은 servo 피벗 a_e = ve_s ≠ 0 하나이고, 이것도 기존 갈래(|a_e| 판정 불능)다.
- 반례가 될 꼴: 입력 넷이 ac 접지 집합(레일·바이어스)에 직결된 경우. 그때는 입력이 아니고, `ss_nodal` 조립 단계에서 이미 걸린다.

### 2.2 엔진 실측(`out/kcl_servo.json`, `out/r2r_opamp.engine.json`)

| 항목 | 값 |
|---|---|
| `ss_nodal` 고정 노드 | ac 접지 [VDD, VSS, vb1, vb3, vb4, vb5n, vb6n] ∪ 입력 [Vinn, Vinp] -- F 성분 포트가 **이미** 구동 노드다 |
| 인수분해 | `nodal_factor` 성공, T(Vinn) = −42.57, T(Vinp) = +38.30 V/V |
| servo 피벗 a_e (e = Vinp +½, Vinn −½) | 40.43 V/V(≠ 0) |
| CM 구동 출력 응답 vx_out | −4.27 V/V → 보정 ε/x = +0.106 |
| 포트 감도 s(Vinp), s(Vinn) | 1.053, 0.947(출력 s = 0) |
| 선형 끝 Δ (엔진 `saturation_window`, 행 = region_rows, 여유 = VDS−VDsat−tol) | −5.8 mV / +18.3 mV |
| V_cm0, V_cm 끝 | 1.4794 V, [1.4736, 1.4977] V |
| 끝 소자 | 아래 M13(여유 2.5 mV), 위 M17(여유 3.3 mV) |

### 2.3 SPICE 실측(sky130 tt 27 °C, ngspice-46)

**.op 대조**(입력 = 봉인점 값 고정, `out/op_compare.jsonl`)

| 봉인점 | 노드 최대 차 | 전류 최대 상대차 | SPICE 비포화 |
|---|---|---|---|
| layer0(input_dc 미선언) | 11.4 mV(n_gp) | 22 %(M20 0.68 µA, 출력 class-AB 조절 소자) | 0 |
| input_dc 0.9 V 가상 선언 | 11.7 mV(Vo) | 20 %(M20) | 0 |
| input_dc 1.48 V 가상 선언 | 15.9 mV(Vo) | 23 %(M20) | 0 |

- 입력을 고정한 SPICE `.op`는 곧 'KCL에서 입력을 구동 노드로 둔 계'다. 이것이 엔진 봉인점과 일치한다.

**servo 훑기**(구성 T: Vinp = x, Vinn = x − (x0 − Vinn0) + 1000·(V(Vo) − Vo0), 2 mV 간격; `out/ana_T1000.json`·`perdev_T1000.json`)

| 항목 | 위로(x0 → 2.4) | 아래로(x0 → −0.6) |
|---|---|---|
| 수렴 | 전 구간 | 전 구간 |
| V_cm 끝(훑기 끝) | 2.293 V | −0.586 V |
| 출력 묶임 max\|ΔVo\| | 0.22 mV | 0.02 mV |
| 영역 창 끝(모든 MOS VDS ≥ VDsat, 여유 0) | 1.5023 V(다음 점 M17 이탈) | 1.4530 V(M13 이탈) |
| 소자별 첫 이탈 V_cm | M17 1.504, M7 1.593, M6 1.817, **M4 2.096, M3 2.111(N 입력쌍 triode)** | M13 1.451, M9 0.960(P 입력쌍 이탈 없음, −0.59까지) |
| 입력쌍 전류 | P쌍 6.7 µA → 7e−13 A(꺼짐), N쌍 4.9 → 10.2 µA, M8(스위치) 2.15 → 4.00 µA | P쌍 6.7 → 167 µA, N쌍 → 0, M8 → 0 |

- 대조(엔진 KCL 선형 끝 vs SPICE 영역 창)
  - 아래 −5.8 mV / −26.4 mV, 위 +18.3 mV / +22.9 mV다. 끝 소자는 같다(M13, M17).
  - 엔진이 좁은 것은 tol_VDsat 여유와 선형 끝 때문이다. O-109 C1 'SPICE 확정'과 맞는 보수 방향이다.
- 개루프 CM 훑기(구성 F, 입력 차 고정, servo 없음)는 x0에서 ±0.3 V 안에 출력이 레일(0 / 1.799 V)로 간다. 그래서 servo 구성(O-115)이 필요하다는 것이 다시 확인됐다.

**input_dc 0.9 V 가상 선언 봉인점**(`out/kcl_servo.dc0.9.json`, `perdev_dc0.9.T1000.json`)

- writer: Vinn·Vinp = `input_dc`(선언 포트). 지금 규칙(P3)대로 함께 구동된다.
- 엔진 KCL a_e = 36.2. 창은 [0.8960, 0.9578] V이고, SPICE 영역 창은 [0.8653, 0.9693] V다(끝 소자 M13 / M7·M17).
- 같은 회로·같은 θ 구조인데, 선언 하나로 '정의 불능'이 '정의됨'으로 바뀐다.

### 2.4 판정

- KCL에서 F 성분 미선언 포트를 함께 구동할 수 있다.
  - 연립은 이득 계산과 같은 인수분해이고 새 특이성이 없다.
  - SPICE에서 그 ICMR은 물리적으로 정의된다.
- O-61 P4 (b)의 '포트 노드의 writer를 바꾸는 회로 해석' 논거는 θ 틀(`node.dc_window`, W4 y 범위)에만 성립한다. KCL ICMR에는 writer 개념이 없다.
- 그래서 감사 §3.1의 '위반(추정)'은 실측으로 **위반(확인)**이다. DEC-103 '계산 틀은 질문에 맞춘다'와 충돌한다.
- '공동분석 대상인 회로 해석'인가: gate 전용 입력 넷을 외부가 구동한다는 것은 connectivity 사실이다(그 넷에 source·drain·저항이 없다). 회로 원리 해석이 아니다.
  - 일반 규칙으로는 '입력 포트는 KCL에서 고정 노드'(P:603 이미 정의)의 귀결이다. 포트 종류를 가를 필요가 없다.
  - 사용자 확인은 받아야 한다. 결정 자체는 사용자 몫이다.

---

## 3. 레일 밖 CMR(8번 일부)

### 3.1 원문(Hogervorst et al., IEEE JSSC 29(12), 1994)

- 웹: https://repository.tudelft.nl/file/File_0fc107fa-6796-4bae-9159-8537a431f171
- 로컬 PDF: `skills/analog-gmid-design/assets/heldout/sources/r2r_opamp__hogervorst_1994/source.pdf`(= `wt/_heldout/tudelft_0fc1.pdf`), 텍스트 `paper.md`
- PDF p.7(JSSC p.1511) 본문(`paper.md`:810-820): "At supply voltages between 2.5 and 2.9 V the opamp is able to deal with common-mode voltages in the range from VSS − 0.4 V to VDD − 1.4 V. At supply voltages above 2.9 V, the opamps are able to deal with common-mode input voltages from rail-to-rail, or **even beyond the rails**. The common-mode input range is from VSS − 0.4 V to VDD + 0.5 V."
- PDF p.8(JSSC p.1512) Table I(측정값, Vsupply 3.3 V): CMR 'VSS−0.4 to VDD+0.5'(Vsup 3–6 V), 'VSS−0.4 to VDD−1.4'(2.5–2.9 V). CMRR 70 dB의 측정 V_cm 구간에 'VSS−0.4~VSS+1'과 'VDD−1~VDD+0.5'가 들어 있다.
  - 즉 레일 밖 입력에서 실제로 CMRR을 쟀다.
- PDF p.1(JSSC p.1505) II절, `paper.md`:113-118: N쌍은 양의 레일까지, P쌍은 음의 레일까지 도달한다. 이것이 구조 근거다.
- 정의: 원문 CMR은 '증폭기가 동작하는(able to deal with) 입력 공통모드 범위'의 **측정값**이다. '모든 소자 포화' 같은 소자 영역 정의가 아니다.
- ESD·입력 보호: 원문에 'ESD'·'protect' 언급이 없다(`paper.md` grep 0). 레일 밖 0.4–0.5 V를 허용하는 근거(ESD 다이오드 문턱 아래인지)는 원문으로 **확인 불가**다.
  - 물리적으로 gate 입력이라 접합 순방향이 없다. 칩 패드 ESD 다이오드 문턱(약 0.6 V) 아래 범위다(일반 지식, 원문 근거 아님).

### 3.2 레일 자름(O-117)을 쓰면 값이 얼마나 달라지나

| 조건 | 레일 자름 없는 끝 | 레일 자름 뒤 | 변화 |
|---|---|---|---|
| 원문 3.3 V 측정(Table I) | −0.4 ~ 3.8 V(폭 4.2 V) | 0 ~ 3.3 V(폭 3.3 V) | 폭 −0.9 V(−21 %); 원문 'beyond the rails' 표현 불가 |
| 1.8 V 이식, layer0 봉인점(이 실측) | 영역 창 1.453 ~ 1.502 V | 같음 | 0(창이 레일 안에서 바이어스 여유 소자로 끝남) |
| 1.8 V 이식, 입력쌍 자체 한계(SPICE 소자별 첫 이탈, 참고) | 위: N쌍 triode V_cm ≈ 2.10 V(VDD+0.30); 아래: P쌍 이탈 없음(−0.59 V까지) | 위 1.8 V, 아래 0 V | 바이어스 여유 소자(M13·M17·M7·M9)를 잘 사이징한 설계라면 자름이 위 ≈0.3 V, 아래 ≥0.59 V를 깎을 것(추정 -- 봉인점이 최적화되지 않아 실측 아님) |

- 주의: 1.8 V 이식 회로에는 원문 CMR이 없다.
  - 원문 공급 감지(M29–M31)는 2.9 V 미만에서 M8을 끄고, 그때 CMR은 VSS−0.4 ~ VDD−1.4로 줄어든다(PDF p.3 / JSSC p.1507, p.7 본문). 이는 원 공정 Vt 기준이다.
  - 그래서 'r2r 원문 CMR과 레일 자름의 충돌'은 원 조건(3.3 V)의 이야기다. 지금 spec(1.8 V, ICMR 제약 없음)에서는 발동이 0이다.
- 측정 정의의 축 차이: 엔진 ICMR은 '모든 MOS 선언 영역'(VDS ≥ VDsat, off 행 없음)이고, 원문은 '기능 범위'다. 축이 다르므로(graph 규칙 3) 값을 직접 비교하지 말고 그 축을 적는다.
  - 실측에서 꺼진 P쌍(전류 7e−13 A)도 VDS ≫ VDsat이라 'sat' 행을 통과한다. 엔진 정의가 꺼짐을 막지 않는다는 것은 r2r에 유리한 성질이다. 기능 범위와 가까워진다.

---

## 4. 대안 비교표

### 4.1 3번 -- F 성분 미선언 입력 포트

| 칸 | (가) 지금 규칙: 구동 제외·봉인점 고정, ICMR 정의 불능 | (나) KCL 함께 구동: 모든 입력 포트를 x로 구동(F 성분 예외 삭제) | (다) input_dc 선언(U-75)으로 우회 -- 규칙 유지, spec이 포트를 '선언 포트'로 만든다 |
|---|---|---|---|
| 물리 정합 | ✗ gate 전용 넷은 외부가 구동한다. 정의 불능은 θ 틀 장부의 산물이다(SPICE: −0.59~2.29 V 전 구간 정의됨) | ✓ SPICE servo와 같은 구성. 끝 소자 일치 | △ 물리는 (나)와 같은 계산이 된다. 다만 정의 가능 여부가 선언에 매인다 |
| 교과서·원문 정의 | ✗ 손계산 ICMR은 입력 게이트 전압을 자유 변수로 둔다(Razavi 식 4.1, `icmr_definition_review.md` §3.3) | ✓ 같은 양 | ✓ 같은 양 |
| design 단순성 | 갈래 +1(F 성분 판정·구동 집합 예외) | 갈래 −1, 구동 집합 = `ss_nodal.input_nets` 그대로 | 엔진 변경 0, spec 결정 1 |
| gm/ID 손계산 속도 | 같음 | 같음(같은 인수분해, 우변 2) | 같음 |
| graph 정본 | 규칙 1 준수 | 규칙 1 준수: 구동 집합을 `graph.ss_nodal`에서 READS. 새 필드·cache 0. F 성분 판정 소비자 하나가 줄어든다 | 준수 |
| fail-closed | 과잉(정의되는 양을 버림) | 유지: 연립 특이·\|a_e\| 판정 불능·DC 전도 결측·입력 셋 이상 갈래 그대로 | 선언 전까지 (가)와 같음 |
| 상수 발명 | 0 | 0 | ⚠ 원칙 경고: 원문에 입력 CM 값이 없다(spec_source §1). 값을 고르면 출처 없는 값이 된다(논문 값·상수 발명 금지) |
| 일반성 | ✗ 같은 회로가 선언 유무로 정의/불능이 갈림 | ✓ 포트 종류 무관 | ✗ 회로마다 선언에 의존 |
| 실측 | r2r: 정의 불능(구동 포트 0) | r2r layer0: KCL [1.4736, 1.4977] V vs SPICE [1.4530, 1.5023] V; a_e 40.4 | r2r 0.9 V 선언: KCL [0.896, 0.958] V vs SPICE [0.865, 0.969] V |
| 원칙 | ⚠ 원칙 경고: DEC-103(θ 틀 제약을 섭동 질문에 가져옴), '물리 최우선·가장 일반형' 위반 | -- | ⚠ 원칙 경고: 규칙 결함을 spec 값으로 덮는다(우회 금지 원칙) |

**권고 3: (나)**
- 범위: KCL ICMR 측정 구성(P:603 'ICMR 측정 구성', design 41 4.7-3b `icm_config`)에서 F 성분 예외 문장을 지운다. 구동 집합 = 모든 입력 포트(`graph.ss_nodal` input_nets)다.
- **θ 틀 `node.dc_window`의 `f_component_undeclared`(block_columns.py:804, test_block_columns.py:1159)는 유지한다.** 그 창은 W4 y의 범위(설계점 질문)다. F 성분 포트에는 y가 없으므로 θ 틀에서 정의 불능은 맞다(DEC-103 그대로).
- 근거
  - 연립이 이득 계산과 같아 새 특이성이 없다(§2.1).
  - r2r 실측에서 정의되고 SPICE와 끝 소자가 일치한다(§2.2–2.3).
  - 같은 회로가 선언 유무로 갈리는 비일반성을 없앤다(§2.3).
- 이것은 결정 변경이다(§5).
- 구현 영향: IT-2c가 미구현이라 code 삭제는 0이다. design 41의 해당 문장과 IT-2c card 완료 조건만 바뀐다.

### 4.2 8번 일부 -- 레일 밖 CMR

| 칸 | (가) 끝 상태 레일 자름 유지(O-117, DEC-96 (2)) | (나) 레일 자름을 spec 선언 입력 허용 범위로 바꿈(기본 = 레일) | (다) 레일 자름 삭제 |
|---|---|---|---|
| 물리 정합 | △ gate 입력은 레일 밖이 물리적으로 가능하다. 레일은 보수적 근사다 | ✓ 실제 한계(ESD·접합)는 공정·패드가 정한다. 선언값으로 받는 것이 물리에 맞다 | ✗ 선형 끝이 상한 없이 레일 밖으로 갈 수 있다(ESD·산화막 무시) |
| 교과서·원문 정의 | ✗ r2r 원문 'beyond the rails'(PDF p.7)를 표현할 수 없다(3.3 V 조건 −21 %) | ✓ 원문 값을 출처와 함께 선언하면 표현된다 | △ |
| design 단순성 | 지금 그대로 | spec 키 +1, 읽기 1(기본값 = 레일이라 갈래 0) | 갈래 −1 |
| gm/ID 손계산 속도 | 같음 | 같음 | 같음 |
| graph 정본 | 준수 | 준수: 사람 선언(spec)을 READS. 새 계산 필드 0 | 준수 |
| fail-closed | ✓ | ✓(기본 = 레일) | ⚠ 원칙 경고: 상한 없음 |
| 상수 발명 | 0 | 0(값은 spec 출처) -- 단, 이식 1.8 V 회로에 원문 값을 그대로 옮기면 ⚠(논문 값 그대로 인용 금지) | 0 |
| 일반성 | ✓ | ✓ | ✓ |
| 실측 | 1.8 V layer0: 발동 0(창 1.453~1.502 V) | 발동 0(r2r spec에 ICMR 제약·출처 있는 범위 없음) | 발동 0 |
| 원칙 | -- | ⚠ 원칙 경고(경미): 지금 소비자 0 → 만들면 배선·'인프라는 엔진을 막을 때만'에 걸린다 | ⚠ 원칙 경고: fail-closed·물리 |

**권고 8: (가) 유지**
- 근거
  - 이식 1.8 V r2r에는 원문 CMR 출처가 없다(원 조건은 3.3 V이고, 2.9 V 미만이면 원문도 VDD−1.4로 줄어든다).
  - spec에 ICMR 제약이 없다.
  - 실측 봉인점에서 발동이 0이다.
- (나)는 계획 백로그 조건으로만 적는다. 조건: '출처가 있는 레일 밖 CMR 사양을 가진 회로가 spec에 들어올 때'. 그 전에 만들지 않는다(만들면 배선).
- 감사 의심(낮음)은 '지금 영향 0, 원 조건에서는 −21 %'로 정량화되어 닫힌다.

---

## 5. 원래 취지와 다름(바뀌는 결정)

1. **3번 (나)를 채택하면** O-61 P4 (b) (가)와 O-117 'F 성분 미선언 입력 포트 = 구동 제외·ICMR 정의 불능'(P:603)을 KCL ICMR 범위에서 뒤집는다. θ 틀 `node.dc_window` 범위는 유지한다.
   - '회로 해석이라 공동분석 대상'이라는 O-117 근거 문장도 바뀐다.
   - 사용자 결정이 필요하고, 계획 개정(P:603, P3 문장 'F 성분 미선언 포트를 뺀 모든 입력 포트')이 먼저다.
2. **감사 보고서 사실 정정**: r2r S1 정지 사유는 '이상 전압원 5개'가 아니다. 지금은 `loop_record_only|global_feedback_or_cross_coupled` 3건이다(§1.3). 진단 경로로는 봉인점을 얻을 수 있다.
3. **heldout 사용**: 이 실측은 heldout r2r에 엔진 봉인·SPICE를 돌렸다. P:1272는 엔진 개발 측정을 금하고, F-IT9는 '연결만 읽는 사실 확인'으로 범위를 좁혔다.
   - 이 감사 측정을 규칙 변경의 근거로 쓰는 것이 heldout 오염인지는 **사용자 판단**이다.
   - 오염을 피하려면 구현 card의 red·근거를 library 쪽 toy로 다시 세운다. 예: `test_block_columns.py:1159`의 toy 'in = M1 gate, source = gnd'를 KCL ICMR 판정에 쓰는 것으로, test 작성자 몫이다. r2r 결과는 감사 기록으로만 둔다.

---

## 6. r2r 실측을 막는 것과 풀 card

| 막는 것 | 실측 | 풀 card(제안 -- 결정은 사용자) |
|---|---|---|
| S1 정지: 루프 3개 `loop_record_only`(floating 전류원 CM 루프 2, gm 제어 전류 스위치 루프 1) | Stage A exit 2 | 'global_feedback_or_cross_coupled 루프 지원' card. 단 heldout이라 고치면 개발 회로로 옮긴다(P:1272) |
| `input_dc` 미선언(U-75) | θ 봉인점 x0가 M8 전류 θ로 정해짐 | 사용자 결정 U-75(원문에 값 없음 -- 출처 없는 값 금지) |
| 바이어스 목표 CI-15, 영역 CI-18 | 미결 | 사용자 결정 |
| KCL ICMR(IT-2c `icm_config`) 미구현 | integ-it12 grep 0 | IT-2c card(3번 (나) 반영 문장 포함) |
| 설계 품질: layer0 봉인점은 여유 0.002–0.007 V 소자 5개(M13·M14·M17·M26·M7) | 창이 49 mV로 좁음 | 탐색 실행이 필요하다. 위 정지가 풀려야 한다 |

---

## 7. 미확인

- 최적화된 r2r 봉인점에서의 ICMR과 레일 자름의 실제 발동(탐색 정지로 layer0만 측정). §3.2의 '위 ≈0.3 V, 아래 ≥0.59 V 깎임'은 추정이다.
- 원문 CMR이 ESD 보호 문턱으로 제한되는지(원문 언급 없음).
- servo 훑기 G = 1000에서 input_dc 0.9 V 봉인점의 위쪽 끝 근처(V_cm > 2.2 V)는 servo가 출력을 2.6 mV까지만 묶었다(V_cm 끝 3.7 V까지 밀림). 영역 창(0.969 V)과는 무관하다.
- 입력 포트가 하나만 F 성분인 회로의 동작(코퍼스 0, F-IT9)은 측정하지 않았다. (나)에서는 포트 종류를 가르지 않으므로 같은 계산이다.
- 감사 §3.1 확인 항목 (1)(2)는 답했다. (1) G_vgs 경로 = M1(gate)–tail_p–M8(gate n_m31)–M31 diode–VDD. (2) servo 연립 비특이(a_e 40.4, 이득과 같은 인수분해).
