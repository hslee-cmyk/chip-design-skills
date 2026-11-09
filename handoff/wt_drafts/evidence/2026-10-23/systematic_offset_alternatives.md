# 계통 offset 정의 -- 세 대안 측정·비교 (2026-10-23)

이 문서는 측정 결과와 비교표만 담는다. 엔진·계획·design은 고치지 않았다.

- 작성: 측정·대안 비교 분석가 agent
- 엔진: `wt/integ-it12` (HEAD `4fc0ca1d`). 엔진은 import만 했고, `PYTHONDONTWRITEBYTECODE=1`로 돌렸다.
- 작업 폴더: `wt/_scratch_sysoffset/` (스크립트, spec 사본, 넷리스트, 결과 jsonl)
- 원자료
  - `out/<회로>.{base,D1,D2}.json`, `out/results.jsonl`: 엔진
  - `out/spice_servo.jsonl`: SPICE servo `.op`
  - `out/spice_dw.jsonl`: ΔW 성분 SPICE 대조
  - `out/summary.txt`: 요약
- 스크립트
  - `eng_sysoff.py`: 엔진 봉인 + `offset_systematic` 1회 호출 + ΔW 1차 감도
  - `spice_servo_op.py`: servo `.op`
  - `spice_dw.py`: ΔW 성분 대조
  - `summ.py`: 요약

## 0. 결론 요약

1. **(가) 지금 정의(ΔW만)는 실재하는 계통 offset을 놓친다. 원칙 위반 후보다.**
   - 5회로 봉인점(base)에서 (가)는 정의 불능이다. 입력 DC가 `pending SP-2`이고 출력 기준이 `pending CI-15`이기 때문이다.
   - 정의를 무시하고 계산해도 ΔW ≡ 0이라 0이 나온다.
   - SPICE가 잰 '출력을 봉인점 출력에 두는 입력 차'는 −2.41, −7.96, −1.91, −0.66, −46.6 mV다.
2. **(나) Vid0 + ΔW는 SPICE와 4회로에서 ±0.16 mV 안으로 맞는다.**
   - nmcnr은 17.7 mV 어긋난다. 이 어긋남은 봉인점 쪽 문제로 보이며, 감사가 이미 의심한 것과 같다.
   - (나)는 프레임에 불변이다. 입력 DC를 임시로 선언하면(D1) Vid0이 0이 된다. 대신 같은 크기가 입력쌍 W 비대칭으로 옮겨 가고, 그 쌍을 같은 W로 묶을 때의 ΔW 1차 감도가 base의 Vid0과 0.003 mV 안에서 같다.
3. **(다) O-115 servo ε을 글자 그대로 쓰면 x0에서 구조적으로 0이다.** servo의 기준이 봉인점 입력 차를 유지하고, 출력은 봉인점 값에 묶이기 때문이다. 그래서 (가)와 같은 맹점이 생긴다. 절대 입력 차로 다시 정의하면 수치는 (나)와 같다. 하지만 출력 기준 정의 둘(DEC-23과 O-115)이 부딪히고, ICMR 정의 불능 사유가 offset에 섞인다.
4. **ΔW 1차 식(O-46·O-47) 자체는 맞다.** SPICE 대조 5건에서 엔진 예측과 SPICE 변화의 차는 0.4 mV 이하(≤ 5%)다.
5. **권고: (나)를 일반형으로 쓴다.**
   - V_id* = (V_id,seal − V_id,0) + [(V_ref − V_out0) − ΔV_out(ΔW)] / A_dc, '1차'
   - V_ref가 봉인점 출력과 같으면 (V_ref − V_out0) 항은 0이다.

## 1. 실측 -- 엔진 (할 일 1)

### 1.1 변형

| 변형 | spec | 목적 |
|---|---|---|
| base | library spec 그대로 | 지금 상태 |
| D1 | 사본에 `input_dc = {"value_v": x0(base)}`을 진단용 임시 선언 | SP-2가 정의 불능을 만들어서 |
| D2 | D1 사본에 `node_voltage_targets_v = {out: V_out0(base)}`를 더함 | 출력 기준 선언이 있을 때 |

- 사본은 `specs/D1`, `specs/D2`에 있다.
- 같은 폴더의 다른 spec은 원본 그대로 복사했다. `value_from_file` 참조를 풀어야 하기 때문이다.

### 1.2 측정 방법

- 봉인점: layer0 시작점을 봉인했다(`eng_sysoff.py`).
- 이 흐름은 icmr_definition_review `eng_seal.py`와 같다. base의 x0, V_inv0, V_out0이 옛 `_scratch_icmr_def` 값과 자릿수까지 같아서, SPICE 넷리스트를 재사용할 수 있었다.
- as-built 엔진 함수: `metrics/offset_systematic.py` `offset_systematic(ss, view, node_v, targets)`를 1회 호출했다.
  - targets는 spec 선언(`sctx.dc.inputs.node_targets`)을 그대로 넘겼다.
  - 뷰는 그 회로의 판정 제약 전달 뷰다.
- **(가) ΔW 정의(O-46 (1)) 전용 엔진 함수는 없다.**
  - 이 정의는 DE-1 (c) 몫이고 아직 구현되지 않았다. 계획 PL:223에도 '새 엔진 미구현'으로 적혀 있다.
  - 단위 9 전 판정 W는 sizing W이고, 이는 θ 봉인점의 `DeviceOp.W`와 같다. 그래서 정의상 ΔW ≡ 0이다(엔진에 sizing W 반올림·matching 강제 코드 없음, `grep` 확인).
- **ΔW 1차 감도 계산**(O-46 (1)·O-47 식을 엔진 helper로 한 번 계산):
  - ΔV_out = −G⁻¹·ΔI, ΔI_k = |ID_k|·ΔW_k/W_k
  - 계산 도구: `conductance_matrix`, `nodal_factor`, `nodal_adjoint`
  - V_id* = −ΔV_out / A_dc
  - **ΔW 가정은 진단용이다.** matching 그룹(`graph.matching_groups`)을 같은 전류 밀도(W/|I|)로 강제한다고 가정했다. 1:1 쌍이면 같은 W와 같은 뜻이다.
  - 이 강제 규칙은 계획에 없다. 그래서 회로 offset 값이 아니라 ΔW 성분의 크기를 보는 시험 입력이다.

### 1.3 결과표 -- base (지금 spec)

| 회로 | x0 (V) | V_inv0 (V) | V_out0 (V) | 반전 입력 writer | Vid0 = x0 − V_inv0 (mV) | A_dc (V/V, 판정 뷰) | as-built `offset_systematic` | (가) ΔW만 |
|---|---|---|---|---|---|---|---|---|
| two_stage_ota | 1.153344 | 1.155643 | 0.900000 | vgs_gate M1 | **−2.299** | 41.56 | `reference_undeclared` | 정의 불능(SP-2·CI-15). 강제 계산 시 ΔW ≡ 0 → 0 |
| ngcc_3stage_ff | 0.537571 | 0.545369 | 0.900000 | vgs_gate M1 | **−7.798** | 146.0 | `reference_undeclared` | 같음 → 0 |
| folded_cascode | 1.046108 | 1.047990 | 1.131689 | vgs_gate M1 | **−1.882** | 28.76 | `reference_undeclared` | 같음 → 0 |
| two_stage_ota_sf | 1.192855 | 1.193613 | 0.205614 | vgs_gate M1 | **−0.757** | 31.35 | `reference_undeclared` | 같음 → 0 |
| nmcnr_amplifier | 0.300019 | 0.328934 | 1.658240 | vgs_gate M102 | **−28.915** | 162.5 | `reference_undeclared` | 같음 → 0 |

- `offset_systematic` 1회 호출은 26~118 µs다.
- 같은 함수에 targets = {out: V_out0}을 주면 5/5에서 `sys_mv = 0.0`이 나온다. '봉인점 출력 오차가 구조적 0'이라는 말이 실제로 가리키는 것이 이것이다.

### 1.4 결과표 -- D1·D2 (입력 DC 임시 선언)

| 회로 | D1 반전 입력 writer | D1 Vid0 | D1 입력쌍 W (µm) | D1 쌍 ΔW 1차 V_id* (mV) | base Vid0 (mV) | D2 as-built |
|---|---|---|---|---|---|---|
| two_stage_ota | input_dc | 0 | M1 8.990 / M2 8.498 (5.8%) | **−2.301** | −2.299 | 0.0 (writer `declared_target`) |
| ngcc_3stage_ff | input_dc | 0 | M1 3.528 / M2 3.997 | **−7.821** | −7.798 | 0.0 |
| folded_cascode | input_dc | 0 | M1 2942 / M2 2802 | **−1.884** | −1.882 | 0.0 |
| two_stage_ota_sf | input_dc | 0 | M1 1.646 / M2 1.616 | **−0.757** | −0.757 | 0.0 |
| nmcnr_amplifier | input_dc | 0 | M102 1207 / M103 12125 | +11.17 (L 다름 -- 같은 단위 셀 아님) | −28.915 | **봉인 실패** `STRUCTURE_UNRESOLVED` (RL `dc_resistor_cycle`) |

- **해석: 입력 DC를 선언하면 θ 프레임은 입력쌍 VDS(CLM) 불균형을 입력 차가 아니라 쌍의 W 비대칭에 흡수한다.**
- 그 쌍을 같은 W로 묶을 때의 ΔW 성분이 base의 Vid0과 같다(4회로 차 ≤ 0.023 mV). 이 성분은 (나)에서 보존되는 양이다.
- (가)는 'D1 프레임 + 판정 W가 쌍을 같게 강제할 때'만 이 양을 잡는다.
  - 지금은 단위 9 전 판정 W가 θ W이므로 front에서 (가) = 0이다.
  - D1 기하(쌍 W 3~13% 비대칭) 그대로라면 그 기하의 offset은 실제로도 약 0이다(**추정**: 봉인점 KCL 정합. D1 넷리스트는 SPICE로 재지 않았다).
- nmcnr D1에서는 V_out0이 1.658 V에서 1.696 V로 바뀐다. 출력 writer가 `resistor_drop`이라 전류에 따라 움직이기 때문이다.

### 1.5 ΔW 성분 크기 (base, 같은 L 그룹만, 진단 가정 '같은 전류 밀도')

| 회로 | 그룹별 V_id* (mV) |
|---|---|
| two_stage_ota | 부하 미러 M3/M4 (ΔW/W ±3%) −2.40, 바이어스 미러 M5/M7 +3.55, 쌍 0 |
| ngcc_3stage_ff | M3/M4/M6B −5.55, M10/M9 +6.34, M0/M12/M5 −4.35, M14/M8 +0.46, M6A/M7 +0.03, 쌍 0 |
| folded_cascode | M3/M4 −7.89, M10/M9 −1.48, M11/MN +1.10, 쌍·branch 0 |
| two_stage_ota_sf | M3/M4 −0.97, M5/M7/M9 +4.51, 쌍 0 |
| nmcnr_amplifier | M104/M105 +46.3, M108/M109 −7.9 (쌍·branch는 L이 달라 뺌) |

- θ 프레임은 미러의 VDS 차도 W에 흡수한다. 예를 들어 two_stage M3/M4는 W가 6% 다르다.
- 그래서 미러 성분은 ΔW(같은 W 강제)가 생길 때만 나타난다. 크기는 Vid0과 같은 자리수(mV)다.
- 바이어스 미러(비율이 있는 그룹)에서 무엇을 '같게 강제'하는지는 계획에 정해져 있지 않다(**미확인**).

## 2. 실측 -- SPICE servo `.op` (할 일 2 대조)

### 2.1 방법

- 넷리스트 본문은 icmr_definition_review `spice_follow_v2.py`가 만든 T 구성 넷리스트의 `.control` 앞 본문을 그대로 쓴다.
  - 기하: 엔진 LUT 정본 slice `w_m` finger, m = W/w_m(실수)
  - 원본은 읽기만 했고, 새 넷리스트는 `_scratch_sysoffset/spice/`에 썼다.
- 바꾼 행은 둘이다.
  - 비반전 입력 = x0(전체 자릿수)
  - `Bsrv_<반전> = x0 − (x0 − V_inv0) + G·(V(out) − V_ref)`
- 실행: `ngspice_con -b`, `.op` 1점, G = 1e3과 1e4.
- 출력 잔차 |V_out − V_ref|는 G = 1e4에서 ≤ 0.0018 mV다(nmcnr 포함).
- Vid_spice = x0 − V(반전)이다.

### 2.2 결과 (V_ref = V_out0, 봉인점 출력)

| 회로 | SPICE Vid (mV) | (나) 엔진 Vid0 + ΔW(=0) (mV) | 차 (mV) | (가) (mV) | (다) 글자 그대로 ε(x0) |
|---|---|---|---|---|---|
| two_stage_ota | −2.411 | −2.299 | +0.112 | 0 (실제는 정의 불능) | 0 (구조적) |
| ngcc_3stage_ff | −7.961 | −7.798 | +0.164 | 0 | 0 |
| folded_cascode | −1.912 | −1.882 | +0.031 | 0 | 0 |
| two_stage_ota_sf | −0.657 | −0.757 | −0.100 | 0 | 0 |
| nmcnr_amplifier | −46.587 | −28.915 | **+17.67** | 0 | 0 |

### 2.3 ΔW 성분 SPICE 대조 (`spice_dw.py`)

방법: 한 그룹의 m을 같은 전류 밀도로 바꾸고 servo `.op`를 다시 돌린다.

| 회로·그룹 | SPICE ΔVid (mV) | 엔진 1차 예측 (mV) | 차 |
|---|---|---|---|
| two_stage_ota M3/M4 | −2.418 | −2.402 | 0.7% |
| folded_cascode M3/M4 | −7.883 | −7.892 | 0.1% |
| two_stage_ota_sf M3/M4 | −0.974 | −0.969 | 0.5% |
| ngcc_3stage_ff M10/M9 | +6.019 | +6.342 | 5.4% |
| two_stage_ota M5/M7 | +3.509 | +3.550 | 1.2% |

→ O-46/O-47의 1차 식은 '1차' 표기로 쓸 만하다. 결함은 식이 아니라 **범위(Vid0 누락)**에 있다.

## 3. 교과서 정의 (물리 정합 축)

- **Razavi**, *Design of Analog CMOS Integrated Circuits* (1판), §13.2 p.466 (PDF p.487) [Fig. 13.21(b)]
  - 원문: "input-referred offset voltage, defined as the input level that forces the output voltage to go to zero"
  - |V_os,in| = |V_os,out|/A_v
  - 로컬 PDF: `G:/내 드라이브/work/Todoc/기술문서/Gm_over_Id/(E-book) Design of Analog CMOS Integrated Circuits (Behzad Razavi)marcado.pdf`
  - 웹 링크: 없음(**미확인**)
- 같은 책 §5.2 p.145 (PDF p.166): V_DS 차가 CLM을 거쳐 미러에 '계통 불일치(systematic mismatch)'를 만든다. 입력쌍·미러 VDS 성분의 물리 근거다.
- **Allen–Holberg** 2단 OTA 계통 offset 조건: 로컬 사본이 없어 쪽 번호는 **미확인**이다.
- 계획 DEC-23(PL:223)의 정의 문장은 "출력을 기준값에 고정하고 입력 차를 미지수로 푼 DC 해의 입력 차"(v6.18, O-26 (1))다. oracle 값도 이 해의 입력 좌표 − V_id,0으로 정해져 있다.
  - → **정의와 oracle은 이미 (나)이고, 엔진 계산법 (가)만 다르다.**

## 4. 기준 출력 V_ref의 정의 (할 일 3)

### 4.1 계획 문언 두 자리

| 자리 | 문언 | 미선언 단일 출력 |
|---|---|---|
| DEC-23 (PL:223, O-53 B3 "출력 기준의 정의 자리 = 이 DEC 하나") | spec 선언 3종: (값) `node_voltage_targets_v`, (넷) 다른 넷과 같음, (입력 추종). 차동 출력은 미선언이면 V(p) − V(n) = 0 | `reference_undeclared` 정의 불능 (fail-closed, 추론 금지) |
| N3.8 ICMR 측정 구성 (PL:603, O-115) | 감지 s를 봉인점 값 `node.dc_v[out]`에 묶음(W3 목표 출력이면 목표값, 고임피던스면 봉인 풀이 값). 차동은 V_op − V_on 봉인점 차 | 봉인점 값을 쓴다 (정의됨) |

### 4.2 두 기준이 갈리는 경우 (실측)

- **값 선언**은 W3 writer(`declared_target`)가 V_out0 = V_ref로 만든다. 그래서 두 기준이 같다(D2 4회로, as-built 0.0). 기준 차 항은 0이다.
- **선언을 봉인할 수 없으면 봉인점 자체가 없다.** nmcnr D2는 출력이 RL로 agnd에 묶여 `STRUCTURE_UNRESOLVED`가 난다. 이때 세 대안 모두 정의 불능이다.
- **(넷)·(입력 추종) 선언, 차동 출력 기본값 0**: 봉인점이 그 값을 반드시 지키는지는 **미확인**이다(쓰기 계획 확인 필요).
- **선언 기준 ≠ 봉인점 출력** (가상 V_ref = 0.9 V 진단, SPICE servo):

| 회로 | V_out0 | SPICE Vid@0.9 (mV) | (나′) 1차 = Vid0 + (V_ref − V_out0)/A_dc | as-built (V_ref − V_out0)/A만 | (가) | (다) O-115 그대로 |
|---|---|---|---|---|---|---|
| two_stage_ota | 0.900 | −2.411 | −2.299 | 0 | 0 | 0 |
| ngcc_3stage_ff | 0.900 | −7.961 | −7.798 | 0 | 0 | 0 |
| folded_cascode | 1.132 | −10.240 | −9.938 | 8.056 (크기만) | 0 | 0 (V_out0에 묶임) |
| two_stage_ota_sf | 0.206 | +25.49 | +21.40 ('추정', 0.69 V 대신호) | 22.15 | 0 | 0 |
| nmcnr_amplifier | 1.658 | **servo 해 없음** (출력이 0.9 V에 못 감, 잔차 65 mV) | −33.58 (거짓 값) | 4.67 | 0 | 0 |

- **세 대안이 갈리는 방식**
  - (가)는 기준 차 항이 없다.
  - (다)는 O-115 기준(봉인점)을 쓰므로 선언 기준과 다르면 다른 양이 된다.
  - (나)는 기준 차 항 (V_ref − V_out0)/A_dc를 더한 일반형 (나′)이어야 같은 정의가 된다.
- as-built `offset_systematic`(출력 오차/A_dm)은 이 기준 차 항 하나만 잰다. Vid0 성분은 빠진다.
- nmcnr처럼 선언 기준에 도달할 수 없는 경우, 1차식은 거짓 값을 낸다. **도달 가능성 판정 자리가 필요하다(미확인, 설계 몫).**

## 5. 대안 비교표 (할 일 2)

| 축 | (가) ΔW만 (현행 O-46·DEC-23) | (나) Vid0 + ΔW (일반형 (나′): + 기준 차 항) | (다) O-115 servo ε을 offset으로 |
|---|---|---|---|
| 물리 정합 (Razavi p.466 정의와 같은 양) | ✗. base 프레임에서 입력쌍 CLM 성분을 통째로 놓친다. D1 프레임에서는 판정 W가 쌍을 강제할 때만 잡는다. 프레임(어느 writer가 흡수하느냐)에 따라 값이 바뀐다 | ✓. 같은 양이고 프레임에 불변이다(base Vid0 = D1 쌍 ΔW, ≤ 0.023 mV) | 글자 그대로는 ✗(x0에서 ε ≡ 0). 절대 입력 차로 고치면 ✓ |
| 5회로 대조 (SPICE servo, V_ref = V_out0) | 0 대 −2.41/−7.96/−1.91/−0.66/−46.6 mV. 5/5 불일치 | 4/5에서 ±0.16 mV. nmcnr +17.7 mV(봉인점 의심, 감사 EV:194와 같음) | 글자 그대로 0 → 5/5 불일치. 고친 꼴은 (나)와 같음 |
| ΔW 성분 식 | SPICE 대조 ≤ 5.4% | 같은 식을 성분으로 포함 | 섭동 W로 servo를 다시 풀면 같은 1차 결과 |
| gm/ID 손계산 속도 | 빠름 | 빠름. Vid0 = `node.dc_v` 두 값의 차, A_dc는 이미 계산, ΔW 항은 같은 LU에 수반 1회 | 빠름(Schur 1칸). 다만 icm_config 전체(뷰 선택·창)에 묶임 |
| graph 단일 정본 | 위반 없음 | V_id* 한 칸, writer = DE-1 (c) offset 블록 하나. `node.dc_v`·A_dc(I-H2로 a_e와 합친 정본) READS. 새 필드·cache 없음. Vid0은 블록 안 지역 차(저장 안 함) | V_id*와 'x0 servo 상태의 입력 차'가 같은 정의 → 규칙 1·3에 따라 필드를 합쳐야 한다(writer = `icm_config`, offset은 READS). servo ε(x0 상대값 = 0)은 정의가 달라 별개 칸 |
| fail-closed | 지금 base 5/5 정의 불능(SP-2·CI-15)이라 맹점이 가려진다 | 유지: V_id,0 미선언·출력 기준 미선언·A_dc 갈래 → 정의 불능. **추가 필요**: 기준 도달 불가(nmcnr@0.9) 판정 자리(미확인) | ICMR 정의 불능 사유(뷰 선택 (i) pending, 입력 셋 이상, e 평행 등)가 offset으로 번진다 → 원인 오귀속 위험 |
| 상수 발명 | 없음 | 없음 | 없음 |
| 일반성(회로 이름 code 없음) | ✓ | ✓ (13회로 공통 식) | ✓ |
| design 단순성 | 가장 단순(하지만 틀림) | 단순: 항 셋을 더함 | 복잡: 두 metric 계열 결합, 기준 정의 충돌 해소가 필요 |
| 원칙 경고 | **⚠ 원칙 경고: 물리 정합 최우선 위반(실재 성분 누락), '근거 + 확인 후'(구조적 0 주장이 실측 없이 채택됨)** | -- | **⚠ 원칙 경고(글자 그대로): 물리 정합 위반(x0에서 0). (고친 꼴) 출력 기준 정의 자리 둘(DEC-23·O-115)이 충돌한다 -- graph 규칙 3에 따라 축을 적어 분리하거나 하나로 합쳐야 함** |

## 6. 권고

**(나)를 일반형 (나′)로 채택하기를 권고한다.**

- 식: **V_id\* = (V_id,seal − V_id,0) + [(V_ref − V_out0) − ΔV_out(ΔW)] / A_dc**
  - V_id,seal = 봉인점 입력의 여기 방향 좌표(`node.dc_v`에서 읽음)
  - V_id,0 = 선언 입력 좌표(O-59 (4) 유지)
  - V_ref = DEC-23 선언 기준
  - V_out0 = `node.dc_v[out]`
  - ΔV_out = −G⁻¹·ΔI(O-46·O-47 식 유지)
  - A_dc = I-H2로 합친 정본 하나
  - '1차' 표기
- 근거
  1. 교과서 정의와 계획 정의 문장(DEC-23 '출력을 기준에 고정하고 입력 차를 미지수로 푼 해'), oracle 측정 정의와 같은 양이다. 그래서 엔진과 oracle 사이의 '값 불일치'가 사라진다.
  2. SPICE와 4/5에서 ±0.16 mV 안으로 맞는다. ΔW 성분 식은 SPICE와 ≤ 5.4% 차이다.
  3. 프레임에 불변이다. 입력 DC 선언 여부와 반전 입력 writer가 어느 것인지에 값이 흔들리지 않는다.
  4. 무거운 계산이 없고, 새 graph 필드·cache도 없다. 값은 기존 필드를 읽고 계산한다.
  5. as-built `offset_systematic`의 (출력 오차/A) 항은 (나′)의 기준 차 항으로 흡수된다. 그래서 같은 양의 둘째 생산자가 남지 않는다(DE-1 (c)에서 옛 함수를 대체·삭제).
- (다)를 고르지 않는 이유
  - 글자 그대로는 x0에서 0이다.
  - 고친 꼴은 (나)와 같은 수치인데, ICMR 블록에 offset을 묶어 fail-closed 원인이 섞이고, 출력 기준 정의 충돌을 먼저 풀어야 한다.
  - 다만 A_dc는 a_e와 같은 정본 칸을 읽는다(I-H2, 이미 계획됨).

### 함께 정해야 할 것 (설계 전 사용자 결정 몫)

- (i) V_ref ≠ V_out0이고 출력이 V_ref에 도달할 수 없을 때(nmcnr@0.9 V)의 정의 불능 판정 자리. 판정 기준을 새 상수 없이 정해야 한다(**미확인**).
- (ii) 단위 9 전 판정 W에 matching 강제를 적용할지(D1 프레임 쌍 W 비대칭 3~13%).
  - 이것은 offset 정의가 아니라 판정 W 정의의 문제다.
  - (나′)는 어느 쪽이든 '판정 기하의 offset'을 맞게 잰다.
- (iii) (넷)·(입력 추종) 기준과 차동 출력 기본값 0을 봉인점이 지키는지 확인.

## 7. 바뀌는 결정 -- 원래 취지와 다름

| 결정 | 지금 | (나′) 채택 시 |
|---|---|---|
| O-43 D1 (c)·O-33 (4) (DEC-74 front 전용 예외의 근거) | 'θ 봉인점에서 구조적 0이라 커널 판정 제외' | 근거 문장이 틀렸다(반전 입력 writer가 `vgs_gate`인 프레임에서 Vid0 ≠ 0). 값을 봉인점마다 싸게 낼 수 있으므로 커널 제외 이유가 사라진다. 커널로 옮길지, front 예외를 유지할지는 **사용자 결정**이다 |
| O-46 (1)·O-47 | offset = ΔW 1차 감도 | ΔW 항은 세 성분 가운데 하나로 남는다(식 유지, SPICE 검증됨) |
| DEC-23 (PL:223)·O-62 (3) | 'ΔW = 0 → 0(통과)' 엔진 1차 규칙 | 삭제. ΔW = 0이어도 Vid0과 기준 차 항이 남는다 |
| O-59 (4) | V_id,0 = 선언 입력 좌표, '봉인점 입력과 같음', DE-1 (c) 착수 실측 '다르면 멈춤' | V_id,0 정의는 유지한다. '같음' 전제와 '다르면 멈춤'은 (V_id,seal − V_id,0) 항으로 바뀐다 |
| O-53 B3 | 출력 기준 정의 자리 = DEC-23 | 유지. 다만 (V_ref − V_out0)/A_dc 항을 계산법에 명시해야 한다. O-115 ICMR 기준(봉인점)과의 축 차이를 graph 규칙 3에 따라 적어야 한다 |
| 계획 PL:617 metric 표 `offset_sys_mv` 행, PL:1613·1627 (c)·1630·1640 '구조적 0' 문언 | 그대로 | 고쳐 쓴다(계획 개정 → 검증 → 승인) |

변하지 않는 것:
- O-50 G1(부호 있는 한 칸)
- O-53 A2(k·σ + |V_id*| 합성)
- O-63 (1)(A_dc 갈래 먼저)
- O-58 DV-11(A_dc 정의)

## 8. 미확인

- Allen–Holberg 계통 offset 조건의 쪽 번호(로컬 사본 없음). Razavi 웹 링크.
- nmcnr 17.7 mV 어긋남의 원인(봉인점 θ 비대칭 M102 / M103 전류 12.7배 의심). 이번에는 재지 않았다.
- D1 프레임 기하의 SPICE offset(넷리스트를 만들지 않음). '약 0'은 **추정**이다.
- 바이어스 미러(비율 그룹)에서 matching이 무엇을 같게 강제하는지. layout `pattern_select`가 W를 같게 만드는지도 확인하지 못했다.
- (넷)·(입력 추종) 출력 기준과 차동 출력 기본값을 봉인점이 지키는지.
- 기준 도달 불가를 판정하는 자리와 기준.
