# 7a 루프 뷰·출력 포트 뷰 design (`pm_ss_deg` view_kind loop, `rout_ss_ohm` view_kind output_port) -- 2026-10-07

- 성격: 설계 문서(코드 없음). 메인 저장소 `chip-design-skills`는 읽기만 했다(HEAD `188c100`). 계약·코드·spec 파일은 고치지 않았다 -- 4절이 코드 작성자용 변경 목록이다.
- 근거 약어: **P** = 계획서 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(N3.8 PM·블록 속성, DEC-53·66·74·90·92, U-48, UD 9번). **MC** = `gmid_engine/metrics/CONTRACT.md`(3.10·3.11·M1). **SC** = `gmid_engine/authoring/SPEC_CONTRACT.md`(2~7절, S1). **GC** = `gmid_engine/graph/CONTRACT.md`(S1 `port_direction`·`port_role`·`ac_ground_class`). **OR** = `tools/spice_oracle/README.md`(PM 정의, C12·C14·C24) + `oracle_netlist.py`(`loop_break_nets`, `build_netlist(loop=True)`) + `oracle_simulate.py`(`loop_gain`). **SF** = `_drafts/engine/design_spec_format.md`(1.7, F12). **M15** = `_drafts/engine/design_mod1_lut_mod5_mna.md`(3.3·3.4, O2). **SY** = `_drafts/engine/reference_review/SYNTHESIS.md`(Q5·Q7). **T** = library `<회로>.topology.json`, **S** = library `<회로>.sizing_spec.json`.
- 상위 원칙(이 문서가 따르는 것): (1) **같은 정의**(U-48, DEC-90 (2)) -- 엔진과 오라클은 같은 양을 잰다. 오라클의 Middlebrook 이중 주입이 이미 사용자 확정 측정이므로, 엔진 루프 뷰는 그 측정이 재는 양을 MNA 로 **같은 수식**으로 계산한다(새 정의를 만들지 않는다). (2) topology 무관 -- 절단 위치·가중·관측은 선언(spec `feedback`, topology `ports` role, 수동소자 단자)과 MNA 구조(용량 전용 노드)에서만 나온다. 이름·상수 없음. (3) 회로 해석은 사용자 몫 -- 9회로 표(5절)에서 해석이 필요한 칸은 7절 질문으로만 남기고 정하지 않았다. (4) 배선 원칙 -- 쓰는 spec 이 없는 선언 키는 만들지 않는다(SC 6절 4와 같은 처리).
- 표기: **[실측]** = 이 문서 작성 중 직접 실행해 확인, **[제안]** = 원칙에서 유도한 기본안, **[질문]** = 7절 사용자 질문.

---

## 1. 결론 요약

| 항목 | 정한 것 |
|---|---|
| `pm_ss_deg` 의 루프 | spec `feedback.elements` 가 비어 있지 않으면 **β 루프**: 그 수동소자들의 입력 포트 넷 쪽 단자를 떼어 새 노드로 옮긴 '절단 회로'에서 오라클과 같은 Middlebrook 식 T = (Tv·Ti − 1)/(Tv + Ti + 2) 를 MNA 로 계산(인수 1개 `ProbeFactor`). 빈 list 면 **β = 1**: T = 포트 전달 뷰 A(입력 포트 role 가중 → 출력 포트), 인수 1개 `Factor` |
| A·β 인수 2개 | **폐기**(MC 3.10 의 '인수 2개(A 응답, β 응답)'). 따로 구한 A·β 곱은 β 망이 A 를 싣는 부하를 빼서 오라클 Middlebrook 값과 다르다(2.7, 예 7 에서 UGF 1.75배 차) |
| 가중 w | 입력 포트 role 에서: 차동 p = +1/|D|, n = −1/|D|(|D| = 차동 입력 포트 수 = 2 → v_id = 1, v_cm = 0), 단일 입력 = +1. 오라클 `input_*_ac`(±0.5, 1.0)와 같은 값 |
| ω → 0 | 절단 노드가 전부 용량 전용이면 '전하 주입 열'(새 `Excitation.charges`)로 전하 보존 극한, 전부 아니면 전류 열 DC 해, 섞이면 정의 불가 값 `loop_cut_mixed_charge`(예외 아님) |
| loop spec 선언 | **view 를 적지 않는다**(기본 = 위 유도 뷰). 명시 모양 `{"cut_weights": {...}}` 은 예약만(첫 소비 spec 이 생길 때 로더 구현) |
| `rout_ss_ohm` 뷰 | **감지 전용** `{sense_p, sense_n?, sense_mode}`(ac_excite 금지). 기본 = 출력 포트가 1개면 그 넷 single_ended. 계산 = 포트 전달 뷰 계(입력 포트 0 V 고정, 레일·gate 전용 넷 교류접지)에 감지 노드 단위 전류 열 하나, ω → 0 극한 / I(MC 3.11 그대로) |
| 오라클 | PM: 엔진과 같은 절단 규칙·가중 검사 추가(C14 보강·C27). Rout: 측정 없음 → **신규 C26 `rout_ohm`**(.ac 1점, 모든 AC 원 0, 감지 노드 AC 전류 1) |
| 파일럿 PM 마일스톤 | 7a 로 정의는 닫힌다. 그러나 파일럿 `feedback` 이 아직 결정 대기(CI-10)라 **PM 판정은 CI-10 결정 뒤에야** 돈다 -- 7절 Q1 |

## 2. 루프 뷰 (`view_kind = loop`, `pm_ss_deg`)

### 2.1 무엇을 재는가 -- 오라클 측정이 정본

OR 'PM 정의'(사용자 확정 2026-10-07)가 이미 측정 절차를 정했다. 그 절차를 수식으로 옮기면(`oracle_netlist.build_netlist(loop=True)`·`oracle_simulate.loop_gain` 실독):

1. 절단: 선언 되먹임 수동소자 f 마다, f 의 단자 중 **입력 포트 넷 n 에 물린 단자**를 새 노드 `lbx_n` 으로 옮긴다(`loop_break_nets`: 절단 넷 = 그 소자들이 물린 입력 포트 넷).
2. 절단 넷 n_k 마다 직렬 전압원 `Vlb_k`(+ = n_k 증폭기 쪽, − = x_k = `lbx_n_k` 되먹임 쪽)과 n_k 로 들어가는 주입 전류원 `Ilb_k`.
3. 1회(전압 주입, `Vlb_k` AC = w_k, `Ilb` 0): Tv = −Σ w_k·V(x_k) / Σ w_k·V(n_k).
4. 2회(전류 주입, `Ilb_k` AC = w_k, `Vlb` AC 0): I_k = i(Vlb_k)(n_k → x_k, 되먹임 쪽으로), Ti = Σ w_k·I_k / Σ w_k·(w_k − I_k).
5. T = (Tv·Ti − 1)/(Tv + Ti + 2). 절단 안 된 입력 포트는 AC 0(결합 C + AC 0 원), 절단 넷의 DC 경로는 `loop_dc_choke_H`(측정 대역에서 열린 것으로 가정).
6. PM = 180° − (기준점 위상 − |T| = 1 첫 하강 교차 위상), 위상 언랩.

엔진은 이 T 를 **같은 절단 회로의 MNA** 로 계산한다. 오라클의 두 번 `.ac` 는 같은 회로의 두 여기이므로, 엔진에서는 계 하나(조립 1회, I-1)의 여기 열들이다.

### 2.2 절단 위치 -- 선언에서 구조적으로 유도 [제안]

| # | 규칙 | 위반 처리 |
|---|---|---|
| L1 | 되먹임 소자 집합 F = spec `feedback.elements`(SC 3절 `SizingSpecDoc.feedback`). topology 에서 다시 추론하지 않는다(정본 1곳 -- 옛 어댑터 C12 의 '입력 넷에 물린 passives 자동 선언'은 새 엔진 경로에서 쓰지 않는다, 4.3 (6)) | -- |
| L2 | f ∈ F 의 두 단자 중 **입력 포트 넷**(GC `port_direction == "input"`)에 물린 단자가 정확히 1개여야 한다. 그 단자가 절단 단자, 그 넷이 절단 넷 | 0개 → 로드 거부 `feedback_element_not_on_input`(오라클 C14 막힘과 같은 조건). 2개(두 입력 넷 사이 소자) → 로드 거부 `feedback_cut_ambiguous`(오라클도 같은 경우를 막도록 C14 보강, 4.3) |
| L3 | 절단 넷 집합 K = F 의 절단 단자 넷들(중복 제거, 넷 이름순). 절단 넷마다 새 노드 x_k 하나 -- 같은 넷에 물린 F 원소의 절단 단자는 모두 같은 x_k 로 간다(오라클 `lbx_<넷>` 하나와 같음) | -- |
| L4 | 절단 회로의 고정 노드 = 레일 ∪ gate 전용 미구동 넷(GC `ac_ground_class` 비 None) ∪ **절단 안 된 입력 포트 넷**(0 V, 오라클 '되먹임이 없는 입력은 AC 접지'). 절단 넷 n_k 와 x_k 는 미지수 노드다(오라클에서 절단 넷의 결합 C·AC 원이 없음) | -- |
| L5 | F 가 빈 list 면 절단 없음 → 2.5 β = 1 | -- |

- 절단 넷이 입력 포트에 한정되는 것은 오라클 정의(`loop_break_nets`)를 그대로 따른 것이다. 되먹임이 내부 넷으로 들어오는 회로(입력 포트를 거치지 않는 β), 능동 소자만으로 닫힌 내부 루프(CMFB 등)는 이 정의 밖이다 -- 9회로 중 해당 선언은 없다(5절). 필요해지면 새 루프 종류로 사용자 결정(7절 Q2).
- 같은 노드를 '어느 전선에서' 끊느냐는 F 의 구성이 정한다. 예: 파일럿에서 F = {Cf1, Cf2} 면 Cf 와 (Cs + 입력 gate) 사이, F = {Cf1, Cf2, Cs1, Cs2} 면 (Cf + Cs) 와 입력 gate 사이에서 끊는다. Middlebrook T 는 이상 단방향 경로에서는 두 자리가 같지만 cgs·cgd 같은 양방향 결합이 있으면 조금 다르다 -- 어느 쪽인지는 F 선언(CI-10)이 정하고 엔진·오라클이 같이 따른다.

### 2.3 가중 w -- 포트 role 에서 [제안]

- 차동 입력 포트 집합 D(role `differential_input_p`/`_n`): w = s/|D|, s = +1(p)·−1(n). |D| = 2 → ±1/2(v_id = 1, v_cm = 0). 단일 입력(role `single_ended_input`): w = 1. 숫자 리터럴 없이 포트 수와 role 부호로만 정해진다.
- 오라클 `legacy_testbench.json` 의 `input_p_ac = 0.5`, `input_n_ac = −0.5`, `input_ac = 1.0` 과 같다[실측]. β 루프 T 는 w 의 공통 배율에 무관하고(Tv·Ti 가 Z 의 0차 동차식) 부호·비만 쓰지만, β = 1 의 A 는 배율에 비례하므로 v_id = 1 정규화가 필요하다(오라클 `hout` 은 입력 진폭으로 나누지 않는다[실측 `oracle_netlist.py` 419행]).
- 절단 넷만 가중을 쓴다(β 루프). 파일럿처럼 두 입력이 모두 절단되면 (+½, −½) 는 **차동 모드 루프**를 잰다. 같은 회로의 공통 모드 루프(+½, +½)는 다른 양이다 -- 예 7b 에서 DM T(0) = 5, CM T(0) = 25[실측]. 기본은 오라클과 같은 role 가중(DM)이고, CM 루프를 판정할지는 7절 Q2.

### 2.4 엔진 계산 -- 절단 회로 MNA 에서 Z 행렬, 그다음 오라클 식 [제안, 수식 실측 확인]

**계 구성(조립 1회)**: 절단 회로(2.2) 하나, 절단 넷 k 개.
- 여기 열 4k 개: 전류 열 `I(n_j)`, `I(x_j)`(단위 전류 주입, j = 1..k) + 전하 열 `Q(n_j)`, `Q(x_j)`(단위 전하 주입 = 전류 s·q, 새 `Excitation.charges` → `BC` 열, 4.1). 모든 전압 구동 진폭 0(고정 노드는 L4 의 교류접지).
- 관측 2k 개: V(n_j), V(x_j)(새 다중 관측 `senses`, 4.1).
- 결과: 열 종류마다 2k×2k 행렬 Z(ω) = [[Z_nn, Z_nx], [Z_xn, Z_xx]](행 = 관측, 열 = 주입).

**오라클 두 실행의 대수적 등가(중첩, 근사 없음)**: 프로브 전압원을 지운 절단 회로의 Z 로 두 실행을 그대로 다시 쓴다.
- M = Z_nn − Z_nx − Z_xn + Z_xx (k×k, 프로브에서 본 직렬 임피던스 행렬).
- 1회(전압 주입): 프로브 전류 i = M⁻¹w, V_n = (Z_nn − Z_nx)i, V_x = (Z_xn − Z_xx)i, **Tv = −wᵀV_x / wᵀV_n**.
- 2회(전류 주입): 프로브(0 V)로 n → x 로 가는 전류 I = M⁻¹(Z_nn − Z_xn)w, **Ti = wᵀI / wᵀ(w − I)**.
- **T = (Tv·Ti − 1)/(Tv + Ti + 2)** -- 오라클 `loop_gain` 과 같은 식, 같은 부호 규약(`Vlb n x`: V(n) − V(x) = w, `Ilb 0 n`: n 으로 주입, `i(Vlb)`: n → x)[실측: 넷리스트 줄 345~346 과 대조].
- k = 1 에서 정리하면 T = (z12 − z21)/(z11 + z22 − 2·z12)(z = 2×2 Z): 가역 회로(z12 = z21)면 0, 즉 T 는 Z 의 비가역(능동) 부분만 남긴다.

**ω > 0**: 전류 열 Z 로 위 식(전하 열 = jω × 전류 열이라 같은 값을 준다). `solve_point` 1회(LU 1회)로 4k 열이 모두 풀린다 -- 추가 분해 0.

**ω = 0 (DC 극한)**: 절단 노드가 용량으로만 이어진 노드(MC 3.2 `charge_nodes`)이면 전류 열은 `dc_charge_injection`(직류 전하 누적으로 발산)이다. 그런데 Tv·Ti 는 Z 의 **0차 동차식**이라 모든 열에 같은 배율(s)을 곱해도 값이 같다. 그래서:
- 전류 열 중 `dc_charge_injection` 이 하나도 없으면 → 전류 열 DC 해(MC 3.3)로 T(0).
- 전류 열 **전부**가 `dc_charge_injection` 이면(절단 노드 2k 개가 모두 용량 전용) → 전하 열 DC 해로 T(0). 전하 열은 BG_F = 0 이라 MC 3.3 의 전하 보존 식(C_F·x = BC_F)에 그대로 들어가고 새 풀이 규칙이 필요 없다(같은 LU).
- 섞이면 → T(0) = None + `Undefined("pm_ss_deg", "loop_cut_mixed_charge", "definitional", …)`. 1/s 차수가 열마다 달라 0차 동차성만으로 극한을 낼 수 없다(로랑 전개 다음 차수가 필요). 9회로 선언에는 없다(5절) -- 쓰는 회로가 생기면 확장(7절 M7). 조용히 통과하지 않는다.
- M 이 특이(그 ω 에서 프로브 직렬 임피던스 행렬 rank 부족)면 그 점 NaN + `loop_probe_singular`(numeric), Tv·Ti 분모 0 은 기존 `den_zero`.

**사후 오차**: Z 원소의 사후 오차 e_ij(MC 3.7 반복 개선, 관측 행마다)를 1차 전파한 Σ|∂T/∂Z_ij|·e_ij. ∂T/∂Z 는 같은 식의 해석 미분(dM⁻¹ = −M⁻¹·dM·M⁻¹), 상수 없음. `find_crossing` 의 정지 조건(MC 3.8)이 이 값을 쓴다.

**격자**: 루프 계와 포트 전달 계를 **한 번의 `solve_responses`** 로 함께 푼다(공유 격자 = 두 계 근의 합집합, MC 3.6). T 는 Z 원소의 유리식이라 극점(분모 0)이 절단 계 극점과 같지 않다. 프로브를 0 V 로 둔 회로가 원래(절단 안 된) 회로이고 그 자연 주파수는 M 의 영점이므로, 원래 회로 = 포트 전달 계의 근을 격자에 함께 넣는다[추측 -- 충분성은 E2]. 그 밖은 MC 3.9 의 π/2 세분과 3.8 실제 풀이 이분이 맡는다. 전하 열은 영점 계산에서 뺀다(영점 = 전류 열 영점 ∪ {0}, 원점은 격자에서 빠짐 -- 더할 것이 없다).

**분석**: `analyze_loop((ProbeFactor,))` -- 인수 1개. gain_db·ugf_hz·phase_margin_deg 는 MC 3.10 그대로(기준 = T(0) 위상, 관측 부호 무관). `pm_ss_deg` = 그 `phase_margin_deg`.

### 2.5 β = 1 (feedback 빈 list)

- T = 포트 전달 뷰 응답 하나: 여기 = 입력 포트 전압(2.3 가중), 관측 = 출력 포트(출력 1개 → V(out), role `differential_output_p`/`_n` 한 쌍 → V(p) − V(n)). 오라클 `hout = v(out)` 또는 `v(out_p) − v(out_n)` 와 같다[실측 419행].
- 이 계는 `gain_ss_db`·`parasitic_pm_ss_deg` 의 기본 포트 뷰(SF 1.7)와 **같은 MnaSystem** 이다(I-2). 따라서 β = 1 회로에서 `pm_ss_deg` = 기본 포트 뷰 `parasitic_pm_ss_deg`(비트 동일, 4.1 I-15).
- 입력·출력 포트 role 이 위 두 모양(차동쌍 1개 또는 단일 1개)이 아니면 기본 뷰가 정해지지 않는다 → `view_required`(SC 2절 기존 규칙의 loop 쪽 확장).
- 단일 입력 회로(common_gate·pushpull)의 β = 1 은 '출력을 그 입력에 되먹인다'는 뜻인데 비반전 경로면 실제로는 양되먹임이다. PM 은 T(0) 위상 기준이라 값은 나오지만 물리 의미가 약하다 -- 두 회로 모두 `pm_ss_deg` 선언이 없어 지금은 판정에 쓰이지 않는다(5절, 결정 불요).

### 2.6 오라클 측정과의 대응

| 측면 | 오라클(OR) | 엔진(이 문서) | 같은가 |
|---|---|---|---|
| 절단 넷 | `feedback_passives` 가 물린 입력 포트 넷 | L1~L3(spec `feedback`) | 같음. 단 엔진이 쓰는 F 를 오라클 입력 `feedback_passives` 로 넘겨야 한다(4.3 (6)) |
| 절단 단자 | 입력 넷 쪽 단자 → `lbx_<넷>` | 같은 단자 → x_k | 같음. 두 입력 넷 사이 소자: 오라클은 양 단자를 다 떼고 엔진은 거부 → 오라클도 막도록 C14 보강 |
| 주입 | `Vlb`(직렬), `Ilb`(n 쪽) 두 `.ac` | 같은 두 여기를 Z 로 중첩(근사 없음) | 같음 |
| Tv, Ti, T 식 | `loop_gain` | 2.4 | 같음 |
| 가중 | `input_*_ac` | 2.3 role 유도 | 값 같음. 오라클이 정의값(v_id = 1, v_cm = 0)인지 검사하도록 C27 |
| 절단 안 된 입력 | 결합 C + AC 0 | 고정 0 V | fstart 에서 결합 C 가 단락이면 같음 |
| 절단 넷 DC 경로 | `loop_dc_choke_H`(측정 대역에서 열림 가정) | 없음(ω → 0 은 전하 보존 극한) | fstart 에서 choke 가 노드 임피던스보다 충분히 크면 같음 → 오라클이 비를 **기록**(C27, 판정 아님) |
| 기준점 | fstart 위상 | T(0)(ω → 0 극한) | fstart 가 첫 극점보다 충분히 낮으면 같음(기록 차, 판정 아님 -- 오라클 gain 과 같은 관례) |
| β = 1 | 개루프 A(입력 차동 AC → 출력) | 포트 전달 뷰 | 같음 |

### 2.7 왜 A·β 인수 곱이 아닌가 (MC 3.10 의 '인수 2개' 폐기 근거)

MC 3.10 과 예 2·2c 는 A 계(증폭기만)와 β 계(이상 전압원이 구동하는 되먹임 망)를 따로 풀어 곱했다. 그 곱은 **β 망이 증폭기 출력을 싣는 부하와 증폭기 입력이 β 망을 싣는 부하를 뺀다**. 오라클 Middlebrook 은 두 부하를 모두 포함하므로 같은 정의가 아니다. 예 7 수치: 부하 포함(Middlebrook) UGF = 22718224.0239 Hz, 무부하 곱(예 2c 와 같은 계) UGF = 39756892.0418 Hz(1.75배). 단일 극이라 PM 은 둘 다 92.29° 지만, 2극 이상에서는 UGF 위치가 달라 PM 도 달라진다. `analyze_loop` 의 인수 곱 기계 자체(예 2·2c)는 그대로 test 대상으로 남기되 `pm_ss_deg` 의 정의가 아님을 계약에 적는다.

### 2.8 손계산 예 (계약 5절 추가안 -- 엔진과 독립인 폐형식) [실측: numpy 직접 계산이 폐형식과 상대오차 ≤ 3.3e-15]

**예 7 -- CS + 용량 되먹임(β 루프, 단일 절단, 용량 전용 절단 노드)**
- `MosSmallSignal(d=2, g=3, s=0, b=0, gm=1e-3, gmb=0, gds=1e-5)`, `Capacitor(2, 0, CL=1e-12)`, `Cf = Capacitor(2, 3, 1e-12)`, `Cs = Capacitor(3, 0, 3e-12)`. 입력 포트 = 노드 3, F = {Cf}.
- 절단 회로: Cf 의 노드 3 단자 → 새 노드 4(x). n = 3(gate + Cs: 용량 전용), x = 4(Cf 만: 용량 전용) → 전하 열 DC 극한.
- 폐형식(되돌림 비): T(s) = gm·Cf/(Cf + Cs) / (gds + s(CL + Cf·Cs/(Cf + Cs))). T(0) = (gm/gds)·Cf/(Cf + Cs) = 25, ω_p = gds/(CL + 0.75 pF) = 5714285.71429 rad/s.
- 기대: Tv(0) = A0 + Cs/Cf = 103, Ti(0) = (A0 + 1)·Cf/Cs = 101/3(A0 = gm/gds = 100), T(0) = (103·101/3 − 1)/(103 + 101/3 + 2) = 25(정확). 루프 `gain` = 27.9588001734 dB, UGF = ω_p·√624/2π = 22718224.0239 Hz, `pm_ss_deg` = 180° − atan√624 = 92.292442776°. ω = 1e3·1e6·1e7·1e8·1e9 rad/s 에서 Middlebrook T 와 폐형식 상대오차 ≤ 3.3e-15.
- 대조(2.7): 같은 소자로 A·β 곱(무부하)이면 ω_p = gds/CL = 1e7 rad/s, UGF 39756892.0418 Hz -- 이 값을 내면 FAIL 이어야 한다(옛 정의 red).

**예 7b -- 차동 절단 2개, 가중이 모드를 고른다**
- 예 7 반회로 두 벌(a·b), 출력 사이 `Resistor(oa, ob, 5e4)`. F = {Cf_a, Cf_b}, 절단 넷 = 두 입력, 가중 (+½, −½).
- 차동 반회로 폐형식: 출력 부하 gds + 2/Rx → T_DM(0) = gm/(gds + 2/Rx)·0.25 = 5. 가중 (+½, +½) 면 Rx 에 전류가 없어 T_CM(0) = 25. 가중 (1, −1) 은 (½, −½) 와 같은 T(배율 무관).
- 기대[실측]: DM 5.00000000000001, CM 25.00000000000006, 배율 바꿈 값 동일.

**예 7c -- 섞인 절단(정의 불가 값)**: 예 7 에서 Cs 를 `Resistor(3, 0, …)` 로 바꾸면 n 은 전도 노드, x 는 용량 전용 → `pm_ss_deg` = `MetricResult(value=None, undefined=(… "loop_cut_mixed_charge" …))`, 예외 없음(I-10).

### 2.9 spec 선언 모양

- **기본(권장, 9회로 전부)**: loop metric 제약에 `view` 를 적지 않는다. 로더가 2.2·2.3·2.5 로 뷰를 유도해 `ViewDecl(mode="loop", …)` 에 담는다(4.2). 유도 재료는 `feedback`·topology `ports`·수동소자 단자뿐이라 spec 에 더 적을 것이 없다(개념 하나 저장 위치 하나 -- `feedback` 이 β 의 정본).
- `feedback` 이 결정 대기 표지면 유도 뷰도 결정 대기: `ViewDecl(mode="pending", decision=<feedback 의 ID>)`. 파일럿은 CI-10 이 그대로 전파되고 MOD10 실행 전 정지(SC 3절)가 그것을 모은다.
- **명시 모양(예약, 지금 구현하지 않음)**: `"view": {"cut_weights": {"<절단 넷>": <0 아닌 유한 수>, …}}`(β 루프) 또는 `{"cut_weights": {"<입력 포트 넷>": …}}`(β = 1). 키 집합은 유도된 절단 넷 집합(β = 1 은 입력 포트 집합)과 같아야 하고 관측·절단 위치는 바꾸지 못한다(그것은 `feedback`·`ports` 의 몫). 쓰임새는 공통 모드 루프 같은 다른 모드 선택뿐인데 9회로에 그런 선언이 없다 -- 배선 원칙에 따라 첫 소비 spec(예: 7절 Q2 에서 사용자가 CM 루프 판정을 정하면)과 함께 로더에 넣는다. 그때까지 결정 대기 아닌 loop view 는 `view_not_applicable` 로 거부한다.

## 3. 출력 포트 뷰 (`view_kind = output_port`, `rout_ss_ohm`)

### 3.1 모양 -- 감지 전용 [제안]

```json
"view": { "sense_p": "<넷>", "sense_n": "<넷>", "sense_mode": "single_ended" | "differential" }
```

- `ac_excite` 없음(있으면 `view_excite_not_allowed`). 여기는 DEC-66 이 고정했다: 모든 여기원 진폭 0 + 감지 노드 전류 주입. 전달 뷰의 `{ac_excite, sense_*}` 와 키 어휘(`sense_p`, `sense_n`, `sense_mode`)는 같다(SF 1.7·오라클 C24 와 같은 이름).
- `single_ended` 면 `sense_n` 없음, `differential` 이면 필수(형식 위반 `type`).
- 감지 넷은 단자 넷이어야 하고(`view_net_unknown`), **고정 노드가 아니어야 한다**: 레일, gate 전용 미구동 넷(`ac_ground_class` 비 None), 입력 포트 넷이면 `view_sense_fixed_net`(MC 3.11 의 '고정 노드에 전류 주입' ValueError 를 로드 단계에서 잡는다 -- 값과 무관한 배선 결함).
- **기본(view 미기재)**: 출력 포트가 정확히 1개면 `{sense_p: <그 넷>, sense_mode: single_ended}`. 아니면 `view_required`(차동 출력 쌍은 차동 Rout 인지 한쪽 Rout 인지 선언이 정한다 -- SF 1.7 규칙 그대로). 9회로 rout 선언 3건은 모두 출력 1개라 기본으로 정해진다(5절).

### 3.2 엔진 계산 (MC 3.11 그대로, 계 위치만 정함)

- 계 = **포트 전달 뷰 계**(입력 포트 전압 구동 → 고정 0 V, 레일·gate 전용 넷 교류접지). DEC-66 '모든 여기원을 교류접지'와 같다. 이 계에 열 하나 `rout`(전압 진폭 없음, 전류 = 단일: sense_p 에 +1 A / 차동: sense_p +1 A, sense_n −1 A)를 더하고, 관측 = V(sense_p) [− V(sense_n)].
- `rout_ohm` = DC 극한 관측값 / I(부호 그대로, MC 3.11). ω = 0 은 같은 LU 재사용(I-2, 추가 분해 0). 감지 노드가 용량 전용이면 `dc_charge_injection` → None + 사유(9회로 출력은 모두 MOS drain/source 라 해당 없음[실측 5절]).
- 되먹임 수동소자가 있어도 **개루프**다(DEC-66 '저주파 개루프', 입력 포트가 고정이라 β 경로는 부하로만 남는다). 폐루프 출력 저항은 정의 밖 -- 9회로 rout 선언 3건은 `feedback: []` 이고 sf_pushpull 은 계획서 1192행이 '소신호 저주파 개루프'로 이미 적었다.
- 다중 관측(4.1)이 들어오면 rout 열은 포트 전달 계의 관측 행 중 하나를 쓴다. 감지 넷이 출력 포트와 다르면(명시 view) 관측 행을 하나 더 둔다 -- 같은 계, 조립 1회 유지.

### 3.3 오라클 측정 (신규 C26, 4.3)

- 본 넷리스트(.ac 1점 `ac lin 1 fstart fstart`, C24 와 같은 기준점)에서 테스트벤치의 모든 AC 원(`Vac_*`, `Vrail_*`, `Vbias_*`)을 AC 0 으로 두고(`alter @<원>[acmag]` -- C24 수단 재사용), `Irout_<k> 0 <sense_p> AC 1`(차동이면 `Irout_<k>n <sense_n> 0 AC 1` 추가)을 더해 H = V(sense_p) [− V(sense_n)].
- `rout_ohm` = Re(H)(엔진 부호 규약과 같은 쪽), 기록에 Im(H)·|H| 도 남긴다. 제약은 C9 그대로 판정(T5 에 들어간다 -- `spice_unverifiable` 에서 빠짐).
- 유효 조건 기록(판정 아님): free 모드 단일 출력은 `Efb`·`Lfb` 가 출력을 입력으로 DC 되먹이므로 fstart 에서 Lfb 가 충분히 열려 있어야 개루프 값이다. ω_fstart²·L·C_ac(choke 와 그 입력의 결합 C 쌍마다)를 기록한다(≫ 1 이면 개루프). 숫자 문턱은 두지 않는다.

## 4. 변경 목록 (코드 작성자용 -- 이 문서는 고치지 않았다)

### 4.1 `gmid_engine/metrics/CONTRACT.md`

| 절 | 바꿀 것 |
|---|---|
| 0 표 | 층 1 `loop_cut.py` 진입점 `cut_circuit(circuit, cuts) -> CutCircuit`(순수 함수: `LoopCut(kind ∈ {resistor, capacitor}, index, terminal ∈ {a, b})` 마다 그 단자를 새 노드 인덱스로 옮기고, 같은 원래 노드에서 옮긴 단자는 같은 새 노드; 결과에 (n_k, x_k) 쌍 정렬 tuple. 원래 노드가 그 원소에 없거나 같은 (kind, index, terminal) 중복이면 ValueError). 층 4 `probe_loop.py` 진입점 `probe_factor(response, pairs, weights) -> ProbeFactor`(2.4 식). `mna_types.py` 에 `CutCircuit`, `ProbeFactor`(+ 인수 공통 규약: 'PointSolution → (복소값, 사후 오차, 사유)') |
| 1 입력 관례 | `Excitation` 에 `charges=((노드, C),…)`(노드로 들어가는 전하, 열의 `BC` 에 들어감 = 전류 s·q). 고정 노드에 전하 주입은 ValueError(전류와 같음). `build_mna(circuit, excitations, senses)` -- `senses` = `Sense` tuple(1개 이상), 기존 단일 관측 호출은 1-tuple |
| 2 표 | 행 추가: `loop_cut_mixed_charge`(definitional, `probe_factor` ω = 0) -- 권고 대응 STRUCTURE_UNRESOLVED / 후보 실패 `structure_inconsistent`; `loop_probe_singular`(numeric, 프로브 직렬 임피던스 행렬 특이) -- STRUCTURE_UNRESOLVED / NONCONVERGENT |
| 3.2 | `sense_row`(n) → `sense_rows`(r×n), `sense_direct`(m) → (r×m). `BC` 에 전하 열 항 |
| 3.3 | 변경 없음을 명시: 전하 열은 BG_F = 0 이라 `C_F·x = BC_F` 에 그대로 들어간다(새 규칙 없음, `dc_charge_injection` 아님) |
| 3.4 | 영점 = 관측 행 × 열마다. 전하 열은 영점 계산에서 뺀다(전류 열 영점 ∪ {0}) |
| 3.6·3.7 | `values` 모양 (k, r, m), `errors` (r, m) |
| 3.8·3.9 | 인수 = `Factor` 또는 `ProbeFactor`(공통 규약). `product_at` 이 공통 규약으로 평가(같은 계는 한 번만 풀기 유지) |
| 3.10 | 'PM 정의' 문단 교체: "`pm_ss_deg` 의 인수: spec `feedback` 이 비어 있지 않으면 절단 회로(`cut_circuit`) 계의 `ProbeFactor` 1개(오라클 Middlebrook 과 같은 식 T = (Tv·Ti − 1)/(Tv + Ti + 2)), 빈 list 면 포트 전달 뷰 `Factor` 1개(β = 1). A·β 를 따로 푼 인수 2개는 β 망 부하를 빼므로 `pm_ss_deg` 정의가 아니다(인수 곱 기계 test 로만 남는다, 예 2·2c). 절단 위치·가중 = 7a design 2.2·2.3" |
| 3.11 | 문장 추가: "계 = 포트 전달 뷰 계(입력 포트 고정 0 V). output_port 뷰 = 감지 전용(sense_p, sense_n, sense_mode)" |
| 3.15 표 | `pm_ss_deg` 결과 형식.필드 = `LoopAnalysis.phase_margin_deg`(β 루프 `ProbeFactor` / β = 1 포트 `Factor`). 레지스트리 항목 `oracle_measure`(DEC-90 (3), 아직 계약에 없음 -- 넣을 때): `pm_ss_deg` → `pm_deg`, `rout_ss_ohm` → `rout_ohm`(C26) |
| 4 불변식 | I-12 Middlebrook T = 단일 제어원 루프의 되돌림 비(예 7, 상대오차 ≤ 차원·eps 규모), I-13 가중 공통 배율 불변(예 7b), I-14 절단 계 조립 1회(4k 열·2k 관측, 스탬프 추가 호출 0), I-15 β = 1 에서 `pm_ss_deg` = 기본 포트 뷰 `parasitic_pm_ss_deg` 비트 동일, I-16 A·β 무부하 곱 값을 내면 FAIL(예 7 대조, 옛 정의 red) |
| 5 예 | 예 7·7b·7c(2.8) 추가. 예 2·2c 머리에 "인수 곱 기계 test -- `pm_ss_deg` 정의 아님" 표시 |
| 6 열린 항목 | M1 닫음(→ 이 문서). 새 M7 '섞인 절단(전도 노드와 용량 전용 노드가 함께인 절단)의 ω → 0 극한 -- 로랑 다음 차수, 쓰는 회로가 생기면' |

### 4.2 `gmid_engine/authoring/SPEC_CONTRACT.md`

| 절 | 바꿀 것 |
|---|---|
| 1 | 변경 없음(`feedback` 모양 그대로). 결정 대기 표지 받는 자리 목록에 '제약 view' 는 이미 있음 |
| 2 규칙 표 | **삭제** `view_not_defined_yet`. **수정** `view_not_applicable`: "view_kind None 인 metric 에 view, metric 결정 대기 제약에 view, **loop metric 에 결정 대기 아닌 view**(명시 루프 뷰는 예약 -- 7a design 2.9)". **수정** `view_required`: "ratio 에 view 없음 / transfer·loop(β = 1) 에 view 없고 입력 포트가 차동쌍 1개·단일 1개가 아니거나 출력 포트가 단일 1개·차동쌍 1개가 아님 / output_port 에 view 없고 출력 포트가 1개가 아님". **추가** `feedback_element_not_on_input`(되먹임 소자 단자 중 입력 포트 넷이 없음, gate elements), `feedback_cut_ambiguous`(두 단자가 모두 입력 포트 넷, gate elements), `view_excite_not_allowed`(output_port view 에 ac_excite, gate constraints), `view_sense_fixed_net`(output_port 감지 넷이 레일·`ac_ground_class` 비 None·입력 포트, gate constraints) |
| 3 | `ViewDecl.mode` 에 `loop`, `sense` 추가. `loop` 필드: `beta` ∈ {declared, unity}, `cuts`((소자, 절단 넷) 이름순), `weights`((넷, w) 이름순), `sense`(β = 1 만: sense_p, sense_n, sense_mode). `sense` 필드: sense_p, sense_n, sense_mode. `feedback` 이 결정 대기면 loop 제약의 view = `pending`(decision = feedback 의 ID). 유도된 내용이 ViewDecl 에 들어가므로 `constraints_fp` 가 feedback·ports 변경을 따라간다 |
| 4 | 문장 추가: loop·output_port 뷰는 7a design 에서 정의되어 판정한다(pending 전용 해제) |
| 5 | 재측정(이 문서는 숫자를 옮기지 않는다): 파일럿 표지 수(pm 의 `view: {"pending": "MOD5"}` 제거 뒤), `feedback_*` 두 규칙과 `view_*` 새 규칙의 실제 거부 실측 |
| 6 항목 9 | 교체: "`pm_ss_deg` = loop(view 미기재 → `feedback`·ports 유도 뷰), `rout_ss_ohm` = output_port(감지 전용, 미기재 → 단일 출력 포트). 정의는 7a design" |
| 7 S1 | 닫음(→ 이 문서). 새 S3 '명시 loop view `cut_weights` -- 첫 소비 spec 과 함께' |

### 4.3 `tools/spice_oracle/README.md`(+ `oracle_input.schema.json`, 오라클 코드)

1. **PM 정의 절**: "엔진 `pm_ss_deg` 는 같은 절단·주입을 절단 회로 MNA 의 Z 행렬로 중첩 계산한다(7a design 2.4) -- 수식 동일" 한 줄과 가중 정의(v_id = 1, v_cm = 0) 명시.
2. **C14 보강**: 선언 되먹임 수동소자의 두 단자가 모두 입력 포트 넷이면 막힘(지금은 양 단자를 다 `lbx_` 로 뗀다 -- 엔진 `feedback_cut_ambiguous` 와 같은 조건으로).
3. **신규 C26 `rout_ohm`**(3.3): schema measure enum(제약·metric 둘 다)에 `rout_ohm`, 항목 `view{sense_p, sense_n?, sense_mode}` 필수·`ac_excite` 금지, 허용오차 키 `tolerances.rout_ohm_rel`. 데이터 파일 `<stem>.rout<k>.txt`(C21 캐시에 포함), `sim.rout = [{view, f_hz, re, im, mag, rout_ohm}]`. 감지 넷이 회로 넷이 아니거나 reference 레일·테스트벤치 구동 넷이면 막힘. free·forced 모두 잰다(forced 는 진단 기록). iso·β 루프 넷리스트에는 없다.
4. **신규 C27 정의 일치 검사**: `pm_deg`(또는 `dc_gain_db`) 측정이 있으면 `input_p_ac − input_n_ac == 1` 이고 `input_p_ac + input_n_ac == 0`(차동) 또는 `input_ac == 1`(단일)이 아니면 막힘(정의값 검사 -- 숫자 기본값이 아니다, C11 과 충돌 없음). β 루프 넷리스트에서 절단 넷마다 choke 대 노드 임피던스 비 |jω_fstart·L| / |V(n)/I_inj|(2회 실행 값으로 계산)를 `ac.loop_choke_ratio` 로, 3.3 의 ω²LC 를 `ac.dc_path_isolation` 으로 **기록만**.
5. `ac.pm_definition` 에 절단 넷·가중을 함께 기록(`ac.loop_break_nets`, `ac.loop_weights` -- meta 에 이미 있는 값의 노출).
6. **C12 보충**: 옛 어댑터의 '입력 넷에 물린 passives 를 `feedback_passives` 로 선언'은 옛 엔진 기준선 전용으로 남긴다. 새 엔진이 오라클 입력을 만들 때는 `feedback_passives` = spec `feedback.elements`(2.2 L1) 그대로다 -- 파일럿에서 두 규칙이 갈리면(7절 Q1 이 {Cf1, Cf2} 를 고르면) 옛 기준선 PM 과 새 PM 은 다른 루프를 잰 값이라 직접 비교하지 않는다고 기록 칸에 적는다.

### 4.4 그 밖 (오케스트레이터 몫 -- 코드 작성자가 아님)

- library `current_reuse_telescopic_ota.sizing_spec.json`: `pm_ss_deg` 제약의 `"view": {"pending": "MOD5"}` 삭제(뷰 정의 자리 표지였고 사용자 값이 아니다; 이후 view 는 CI-10 에서 전파). 다른 회로 spec 은 변경 없음(5절).
- 계획서 N3.8 PM 마지막 문장 "루프를 어디서 끊어 … 7a design이 정한다" → 이 문서 참조, DEC-53 'loop·output_port 제약은 pending 전용' 해제, N3.16 metric 서명 행 같은 문구.
- `design_mod1_lut_mod5_mna.md` O2 의 '루프 뷰에서 T 냐 H 냐' → 해소(U-48 + 이 문서: β 루프는 T, β = 1 은 H = A).
- `design_spec_format.md` 1.7 `view` 문단에 output_port 감지 전용 모양과 loop 미기재 규칙 한 줄.

### 4.5 작업 순서(카드 단위 제안)

1. metrics: 다중 관측 + `Excitation.charges`(기반, 다른 것의 전제).
2. metrics: `cut_circuit` + `probe_factor` + `analyze_loop`·`product_at` 인수 규약 + 예 7·7b·7c test.
3. authoring: 2절 규칙·`ViewDecl` 모드·유도(9회로 로드 재측정). 1·2 와 병렬 가능(데이터만 공유).
4. oracle: C14 보강·C26·C27(엔진과 독립, 병렬 가능).
5. ss_linearize(MOD5 다음 단계, MC '이번 범위 밖'): `ViewDecl` → 계 레코드 사상(소자 이름 → 인덱스, 절단 노드 새 인덱스). 이 단계가 배선 지점이다 -- 1~3 은 이것 없이 test 만 도는 상태로 끝나지 않게 같은 묶음으로 잡는다(배선 원칙).

## 5. 9회로 표 [실측: library T·S 2026-10-07, 구조 판정은 소자 drain/source·저항 단자 여부]

| 회로 | 입력 포트(role) | 출력 포트 | `feedback` | `pm_ss_deg` 루프 | `rout_ss_ohm` 뷰 | 상태 / 표시 |
|---|---|---|---|---|---|---|
| common_gate_amplifier | vin(단일) | vout | `[]` | β = 1, A = vin → vout(w = 1) | 선언 없음 | pm 선언 없음(SP-4·5 만 대기). vin 은 전도 노드(소스 입력). β = 1 이 비반전 경로라 물리 의미 약함(2.5) -- 선언 생길 때만 문제 |
| current_reuse_telescopic_ota (파일럿) | Vip/Vim(차동) | Vop/Vom(차동) | **결정 대기 CI-10** | 후보 {Cf1, Cf2} 또는 {Cf1, Cf2, Cs1, Cs2}: 절단 넷 {Vim, Vip}, 가중 ±½(DM), 절단 노드 n(입력 gate M1a·M4a / M1b·M4b, Cs 포함 여부 무관) 과 x(Cf, Cs 포함 시 Cf+Cs) 모두 용량 전용 → 전하 열 극한, **계산 가능**. 후보 `[]` 면 β = 1, A = (Vop − Vom)/v_id | 선언 없음 | `pm_ss_deg ≥ 70` 판정은 **CI-10 결정 뒤**(7절 Q1). 입력 넷에 물린 수동소자 = 정확히 Cf1·Cf2·Cs1·Cs2(L2 위반 없음, 두 입력 넷 사이 소자 없음). CMFB 루프(R1·R2 → Voc → M37a …)와 CM 루프는 이 정의 밖(Q2) |
| folded_cascode | vin_p/vin_n | out | `[]` | β = 1, A_dm → out | 선언 없음 | pm 결정 대기 SP-3 |
| ngcc_3stage_ff | Vinp/Vinn | Vout | `[]` | β = 1(Cm1·Cm2 는 A 안의 Miller 보상) | 선언 없음 | `pm_ss_deg ≥ 63.4` **판정 가능** |
| nmcnr_amplifier | Vin_p/Vin_n | Vout | `[]` | β = 1(Cm1·Cm2·Rm 은 A 안, RL·CL 부하 포함) | 선언 없음 | `pm_ss_deg ≥ 70` **판정 가능** |
| pushpull_follower_buffer | vin(단일) | vout | `[]` | (pm 선언 없음) | 기본: sense_p = vout single_ended. vin 고정 0 V, agnd 레일 교류접지 | `rout_ss_ohm ≤ 1000` **판정 가능**(엔진). 오라클은 C26 전까지 `spice_unverifiable` |
| sf_pushpull_output_opamp | vin_p/vin_n | vout | `[]` | (pm 결정 대기 SP-3) | 기본: vout | `rout ≤ 1000` 판정 가능(개루프, 계획 1192행). 오라클 C26 전 unverifiable |
| two_stage_ota | vin_p/vin_n | OUT | `[]` | β = 1 | 선언 없음 | pm 결정 대기 SP-3 |
| two_stage_ota_sf | vin_p/vin_n | vout | `[]` | β = 1 | 기본: vout(OUT 은 내부 2단 출력) | `rout ≤ 1000` 판정 가능. 오라클 C26 전 unverifiable. pm 결정 대기 SP-3 |

- 표현할 수 없는 회로: **없음**. 9회로 출력 넷은 모두 MOS drain/source 에 물린 전도 노드(rout `dc_charge_injection` 없음), 입력 넷은 common_gate 의 vin 만 전도 노드이고 나머지는 용량 전용이다 -- 섞인 절단(`loop_cut_mixed_charge`)은 선언된 β 루프(파일럿 후보)에서 생기지 않는다.
- 정의 밖이라 표현되지 않는 것(선언이 없어 지금 막지는 않음): 파일럿 CMFB 루프·CM 루프 PM(Q2), 내부 넷으로 들어오는 β, 섞인 절단(M7).

## 6. topology 독립성 논증

- **읽는 것**: spec `feedback.elements`(이름은 값으로만), topology 수동소자 단자 넷, S1 `port_direction`·`port_role`·`ac_ground_class`, MNA 의 `charge_nodes`/`dc_charge_injection`(계 구조에서 계산). 회로 이름·넷 이름·소자 이름 리터럴, 숫자 상수가 없다(가중 ±1/|D| 는 포트 수와 role 부호, 0·1 은 정의값).
- **같은 엔진 식**: β 루프든 β = 1 이든 `analyze_loop` 하나, 인수 종류만 선언이 고른다. 절단 수 k 는 가변(1, 2, … -- 차동·단일 구분 없이 같은 행렬식).
- **무동작 증거(측정 대상)**: 9회로 중 8회로는 `feedback: []` 라 `cut_circuit`·`probe_factor` 가 불리지 않고 `pm_ss_deg` = 포트 뷰 값(I-15 비트 동일)이다 -- 4.5 의 3 단계 test 가 9회로 로드에서 "β 루프 뷰 유도 0건(8회로) / 파일럿은 CI-10 pending 전파"를 확인해야 한다. 파일럿 후보 두 집합을 test 픽스처 spec(origin `fixture`)으로 넣으면 각각 절단 넷 {Vim, Vip}·전하 열 극한 경로를 탄다.
- **노드 재번호·이름 불변**: 절단 노드는 원래 노드 최대 인덱스 뒤에 정렬 순서로 붙고(I-7 확장), 넷 이름을 바꾼 같은 회로에서 유도 뷰의 내용(이름 제외)과 metric 이 같아야 한다.

## 7. 열린 항목·사용자 질문

### 7.1 사용자 질문 (회로 해석 -- 정하지 않았다)

- **Q1 (= CI-10, 파일럿 β)**: 파일럿 `feedback.elements` 를 (a) {Cf1, Cf2} (b) {Cf1, Cf2, Cs1, Cs2} (c) `[]`(β = 1) 중 무엇으로 할까요? 이것이 파일럿 `pm_ss_deg ≥ 70` 판정의 유일한 남은 조건입니다. 참고: (a)(b) 모두 계산 가능하고 차이는 끊는 전선의 위치(Cf–노드 사이 vs 노드–입력 gate 사이)라 cgs·cgd 결합만큼 값이 다릅니다. 옛 어댑터는 C12 규칙으로 지금 (b) 를 넣고 있습니다(옛 기준선 PM 이 (b) 루프 값). (c) 면 Cf·Cs 는 입력 0 V 고정 아래 부하로만 남습니다.
- **Q2 (파일럿 공통 모드·CMFB 루프)**: role 가중은 차동 모드 루프만 잽니다. 같은 Cf 를 지나는 공통 모드 루프와, R1·R2 로 Voc 를 감지해 M37a 로 돌아오는 CMFB 루프(수동 β 가 아니라 능동 내부 루프 -- U-48 정의 밖)의 PM 도 판정해야 합니까? 예라면 루프 종류(내부 넷 절단)와 그 하한 값이 새로 필요합니다(그때 2.9 의 `cut_weights` 를 쓰는 첫 spec 이 됩니다).
- **Q3 (rout 부호)**: 엔진·오라클은 Rout 을 부호 그대로 냅니다(MC 3.11). 음의 출력 저항(양되먹임)이 나오면 `rout_ss_ohm ≤ 1000` 은 그대로 통과합니다. 판정을 |rout| 로 할까요, 음수를 정의 불가(후보 실패)로 둘까요, 부호 그대로 둘까요? (9회로 rout 회로 3개는 모두 개루프 팔로워/출력단이라 정상 해에서는 양수가 예상되지만 탐색 중 후보에서는 생길 수 있습니다.)

### 7.2 엔진 쪽 열린 항목 (사용자 결정 아님)

| # | 항목 | 처리 |
|---|---|---|
| M7 | 섞인 절단의 ω → 0 극한 | 정의 불가 값 `loop_cut_mixed_charge`. 쓰는 회로가 생기면 로랑 다음 차수로 확장 |
| E1 | fstart 대 ω → 0 기준점 차, choke·결합 C 유효 조건 | 오라클 C27 기록(판정 아님). 기록이 ≫ 1 이 아닌 실행은 엔진-SPICE PM·rout 차를 해석할 때 먼저 본다 |
| E2 | 공유 격자에 T 고유의 극점(분모 0)이 직접 들어가지 않음 | 원래 회로 근 + π/2 세분 + 실제 풀이 이분으로 충분하다고 본다 [추측 -- 파일럿 실측 때 격자 세분 횟수를 기록해 확인] |
| E3 | 다중 관측 도입이 기존 test·호출부(1-tuple)에 주는 영향 | 4.5 의 1 단계 카드에서 호출부 grep 후 같은 커밋에서 갱신 |

## 8. 이 문서가 정하지 않은 것

- `parasitic_pm_ss_deg`·`gain_ss_db` 의 파일럿 transfer 뷰 표지(`{"pending": "MOD5"}`) -- 전달 뷰 정의 몫(MOD5 design).
- `ratio_ss_db`(CMRR·PSRR) 뷰 -- 오라클 C24 와 MOD5 design 몫.
- 슬루·정착(.tran β 루프) -- 오라클 C25 대로 기록 전용, 정의 미정.
- 블록 국소 테브난 출력 저항(DEC-66 잔차 기록)의 계산 -- `7a-gain-metric` design 몫. 이 문서의 `rout_ss_ohm` 은 전회로 값만.
