# spice_oracle -- gm/ID 엔진 합격 판정용 SPICE 오라클

엔진이 낸 설계 해(연결·소자 기하·바이어스)와 그 엔진의 예측값을 **엔진 무관 JSON**(`oracle_input.schema.json`)으로
받아 ngspice 로 재고(.op/.ac), 합격 판정과 예측 대 SPICE 비교 기록(JSON + Markdown)을 낸다.
새 엔진(`skills/analog-gmid-design/gmid_engine/`)과 독립이다 -- 오라클 파일은 어떤 엔진도 import 하지 않는다.
옛 엔진 출력은 `legacy_adapter.py` 하나로 이 형식에 맞춰 기준선(baseline)으로 쓴다.

## 파일 (파일마다 독립 진입점 1개, 다른 파일의 `_` 이름 import 없음)

| 파일 | 진입점 | 역할 |
|---|---|---|
| `oracle_input.schema.json` | - | 입력 형식(JSON Schema 2020-12). 진입점은 입력을 이것으로 먼저 검증한다 |
| `oracle_netlist.py` | `python oracle_netlist.py <input.json> <out.cir> --bias free\|forced\|iso [--topology T] [--require-topology] [--omit N..] [--short N..]` | 넷리스트 + `<out.cir>.meta.json`, feedback_passives 가 있으면 `<stem>.loop.cir` |
| `oracle_simulate.py` | `python oracle_simulate.py <netlist.cir> <sim.json> --ngspice EXE [--timeout-s S] [--cache-dir D]` | `ngspice -b` 실행, .op/.ac(+β 루프) 추출, **[신규 C10]** PM 안정성 근거(Nyquist N(위상 펼침 + 적응 세분화) + 독립 `.pz` P + 폐루프 `.tran` 창 단위 조기 종결, `<stem>.stab.cir`·`<stem>.pz.cir`) |
| `oracle_config.json` | - | **[신규 U6]** `stability_transient.wall_s_per_window`(폐루프 과도 창당 ngspice 실행 시간 상한 -- 기본 시간 상한의 근거 `measured_*`·`safety_factor`·`justification` 포함) |
| `oracle_noise.py` | `python oracle_noise.py <input.json> <netlist.cir> <out.json> --ngspice EXE [--timeout-s S] [--cache-dir D]` | **[신규 U6]** ngspice `.noise` 대조: 개루프 입력 환산 열잡음·flicker 코너·excess·소자별 기여, 폐루프 적분 출력 잡음 |
| `oracle_offset_mc.py` | `python oracle_offset_mc.py <input.json> <netlist.cir> <out.json> --ngspice EXE [--timeout-s S] [--cache-dir D]` | **[신규 U6]** 소자별 독립 mismatch Monte-Carlo 입력 환산 offset 1σ |
| `oracle_swing.py` | `python oracle_swing.py <input.json> <netlist.cir> <out.json> --ngspice EXE [--timeout-s S] [--cache-dir D] [--sat-margin-v V]` | **[신규 U6]** 출력 스윙·입력 공통모드 범위(ICMR) `.op` 스윕 |
| `oracle_compare.py` | `python oracle_compare.py <input.json> <netlist.cir> <sim.json> <out_prefix> [--judge J] [--sat-margin-v V] [--forced-compare F]` | 합격 판정 + 비교 기록 |
| `oracle_run.py` | `python oracle_run.py <input.json> <out_dir> --bias free [forced] [iso] [--judge J] [--sat-margin-v V] [--ngspice EXE] [--tag T] [--topology T] [--require-topology] [--omit N..] [--short N..] [--cache-dir D]` | 위 셋을 한 번에(bias 마다). **[신규 U6]** free 에서 입력에 `noise`·`offset_mc`·`swing_icmr` 블록이 있으면 같이 돈다 |
| `legacy_adapter.py` | `python legacy_adapter.py <circuit_key> <out_dir> --w-source layout\|sizing --isrc topology\|engine [--from-dump D] [--instance I] [--topology T]` | 옛 엔진 실행(또는 dump) -> 오라클 입력 |
| `legacy_testbench.json` | - | 어댑터가 넣는 테스트벤치 구성값 |
| `smoke/` | - | 스모크 실행 산출물과 보고서(`smoke/SMOKE_REPORT.md`), **[신규 U6]** 구현 기록 `smoke/U6_REPORT.md`, 자체 점검 `smoke/u6_selfchecks.py`, 시간 상한 근거 측정 `smoke/measure_wall_s_per_window.py` |

`python -P` 로 실행해도 된다(진입점이 자기 디렉터리를 sys.path 에 넣는다). numpy, jsonschema 필요.

## 입력 스키마 요약 (`oracle_input.schema.json` 이 정본)

* `process`: `lut_npz`(코너 `corner`·온도 `temp_c` 메타를 여기서 읽음), `models[kind]`(`subckt`, `includes`(경로의
  `{corner}` 를 npz corner 로 채움), `op_probe`(`@m.{inst}.<내부소자>[{param}]` 틀)), `diffusion`
  (`ad_per_w_m`, `pd_extra_m`, LUT 생성 규칙 -- free 에서는 소자별 `devices[].diffusion` 이 없는 소자가 있으면 필수, C22),
  선택 `ngspice_exe`.
* `rails`: `[{net, voltage, reference?}]` -- reference 하나가 SPICE 0.
* `devices`: `[{name, kind, drain, gate, source, bulk, L, finger_w, n_fingers, W, diffusion?}]`. 인스턴스는
  `X<name> d g s b <subckt> l=L w=finger_w m=n_fingers`(nf 금지). `W` 는 엔진이 선언한 총폭(finger 곱과의 차를 `W_rel` 로 기록).
* `sources`(이상 전류/전압원, `value_basis` 근거 문자열), `passives`(R/C), `bias_voltages`(게이트 전용 넷), `ports`
  (`input_p/input_n` 또는 `input`, `output_p/output_n` 또는 `output`).
* **[신규]** `feedback_passives`: β 되먹임망을 이루는 passives 이름(입력 포트 넷에 물린 소자). PM 정의를 정한다(아래).
  **[신규 C12 보충]** 선택 `feedback_passives_basis`(그 집합을 정한 규칙 문자열, 기록 전용).
* `predictions`: `nodes`(넷 -> V), `devices`(이름 -> `ID, VGS, VDS, VSB, gm, gds, gm_id, region(sat|triode|off),
  off_current_A`), `metrics` (`[{name, measure, value, rail?, view?}]`, measure ∈ `dc_gain_db, ugf_hz, pm_deg, f3db_hz,
  supply_current_A, ratio_db, rout_ohm, slew_rate_v_per_s, settle_s`, **[신규 U6]** `noise_th_in_v2hz, noise_fc_in_hz, noise_excess_th, noise_out_int_vrms, offset_in_sigma_mv,
  swing_out_v, icmr_v, icm_margin_v`).
* `acceptance.constraints`: `[{name, measure, op(>=|<=), limit, view?}]` -- 회로 성능 스펙. 합격 판정에 쓰인다
  (measure 에 `ratio_db`·**[신규 C26]** `rout_ohm`·**[신규 U6]** 위 U6 measure 포함, 과도 measure 제외).
* `testbench`: `dc_choke_H`, `ac_couple_F`, `ac{fstart_hz, fstop_hz, points_per_decade, input_*_ac, diff_feedback_gain}`,
  `options`, `nodeset_from_predictions`, **[신규]** `loop_dc_choke_H`(β 루프 측정용 입력 DC 경로, feedback_passives 가 있으면 필요).
* **[신규 U6]** 선택 측정 블록 `noise`, `offset_mc`, `swing_icmr` (아래 "U6" 절).
* `judge`: `sat_margin_V`(합격 판정의 포화 여유), `off_current_A`(선택), `tolerances{ID_rel, VGS_abs_V, VDS_abs_V, VSB_abs_V,
  gm_rel, gds_rel, gm_id_rel, node_abs_V, W_rel, kcl_abs_A, dc_gain_db_abs, pm_deg_abs, ugf_hz_rel, f3db_hz_rel,
  supply_current_A_rel, ratio_db_abs, rout_ohm_rel}`(기록·경고용). **기본값 없음**. `--judge` 파일·`--sat-margin-v` 가 덮어쓴다.
* 크기 규칙: 소자 전압·전류는 극성 정규화(PMOS 도 켜진 포화면 ID·VGS·VDS 양수, VSB = |바디-소스| 방향 양수).
  ID 는 **부호 포함**: 선언 드레인 기준 정상 방향 전도(NMOS 드레인으로 들어감, PMOS 드레인에서 나옴) = 양수, 역방향 = 음수.
  **[정정 2026-10-07]** ngspice BSIM4 `@` 값 중 vgs·vds·vth·vdsat 는 이 규칙이지만(`@vds = type*(V(d)-V(s))`, 선언 단자
  방향 부호 유지) **`@id` 는 소스/드레인 역할이 뒤바뀌어도 양수**(채널 전류 크기)다. 그래서 SPICE 쪽은
  `ID = @id x sign(@vds)`(@vds = 0 이면 0, 둘 중 하나 없으면 None), `VSB = -vbs`, 나머지는 그대로다. 원값은 소자 행
  `ID_spice_op_id` 에 남긴다. 실측(ngspice-46 sky130 tt, L=0.5 µm W=2 µm m=2, 드레인에 0 V 감지원): NMOS 역방향
  (V(d)=0, V(s)=0.3, VG=1.8) @id = +4.981e-4, @vds = -0.3, 감지원 드레인 유입 전류 -4.981e-4; PMOS 역방향(V(d)=1.6,
  V(s)=1.0) @id = +8.991e-5, @vds = -0.6, 드레인 유입 +8.991e-5(크기 규칙 -8.991e-5); 정상 방향 NMOS/PMOS, VDS 1 mV 경우도
  `@id x sign(@vds)` = 극성 x 감지원 전류(상대차 1e-6 이하). 꺼진 소자(VGS=0)에서는 감지원 전류가 접합 누설을 포함해 @id 와
  다르다(NMOS 2.08e-12 대 2.64e-13) -- 크기는 @id(LUT ID 열과 같은 양, `assets/sky130_lut_sweep.py` 가 `@m...[id]` 로 잼)를
  쓰므로 엔진이 LUT VGS=0 누설로 낸 `off_current_A` 와 같은 양끼리 비교된다.

## 합격 정의 (사용자 확정 2026-10-07, Q5·Q6 보강 같은 날)

`summary.verdict` 는 **free 모드에서만** 합격/불합격을 낸다. 합격 조건은 셋이다.
1. `acceptance.constraints` 의 선언 제약(회로 성능 스펙)을 SPICE 값이 전부 만족한다. **[변경]** CMRR·PSRR(`ratio_db`,
   C24)도 선언되면 여기서 판정한다. **[신규]** 출력 저항(`rout_ohm`, C26)도 같다(음의 실수부는 정의 불가 -> PASS 불가).
   슬루·정착은 판정 대상이 아니다(C25).
2. SPICE 에서 전도하는 모든 MOS 가 포화: VDS - VDSAT >= `sat_margin_V`(인자, 기본값 없음). 전도 = **부호 있는** ID_spice
   (크기 규칙) > 그 소자 문턱(C23 의 소자별 `off_current_A`, 없으면 `judge.off_current_A`) -- 역방향 전류(ID < 0)는 전도가
   아니다(포화 검사 대상 밖, 엔진 예측 전도면 3 에서 FAIL). 문턱이 둘 다 없으면 소자 행 `conduction_threshold_A` 는 None 으로
   기록하고 전도 = ID_spice > 0 이다.
3. **[신규 C23]** 엔진이 전도로 예측한 MOS 가 SPICE 에서 꺼지지 않았다(문턱 = 엔진이 낸 소자별 `off_current_A`).
4. **[신규 U6, 사용자 결정 B·Q10]** 폐루프가 불안정하지 않다: C10 최종 안정성 판정(`summary.stability.verdict`)이 `unstable`(폐루프 과도 unstable -- 한계 사이클 포함 -- 또는 Nyquist Z = N + P >= 1)이면
   pm 제약이 있든 없든 FAIL 이다. 판정을 못 낸 `undetermined` 는 FAIL 이 아니라 pm 제약 N/A -> INCOMPLETE 로 남는다.
그리고 합격 실행(free)은 접합 용량을 넣은 넷리스트여야 한다(C22: 확산 기하 없으면 막힘).

노드전압·소자 ID/gm/gds/VGS/...·성능 metric 의 엔진-SPICE 차이는 **기록만** 한다(verdict 와 무관). 허용오차가 있으면
기록 항목마다 `judge` 칸에 허용오차 안(PASS)/밖(FAIL)을 적지만 verdict 에 들어가지 않는다.
**경고**는 forced 모드에서만: 소자 ID·gm 의 상대차가 `tolerances.ID_rel`/`gm_rel` 을 넘으면 `summary.warnings` 에 모으고
비교표(Markdown) 맨 앞에 찍는다. forced 모드 verdict 는 막힘이 없으면 늘 `INCOMPLETE`(진단 모드).

## PM 정의 (사용자 확정 2026-10-07: 엔진과 같은 정의)

* `feedback_passives` 선언이 있으면 **그 β 루프의 위상여유**: 루프 넷리스트 `<stem>.loop.cir` 에서 되먹임 수동소자의
  입력 쪽 단자를 `lbx_<입력넷>` 으로 떼고, 끊은 자리마다 직렬 전압원 `Vlb_<넷>`(증폭기 쪽 +)과 증폭기 쪽 주입 전류원
  `Ilb_<넷>` 을 넣어 `.ac` 를 두 번 돈다(Middlebrook 이중 주입). 끊은 넷 k 의 가중 w_k = `input_*_ac`(차동이면 ±0.5).
  - 1회(전압 주입, Vlb AC = w_k): Tv = -Σ w·V(lbx) / Σ w·V(넷)
  - 2회(전류 주입, Ilb AC = w_k): Ti = Σ w·I_x / Σ w·(w - I_x), I_x = i(Vlb)(되먹임 쪽으로 가는 전류)
  - T = (Tv·Ti - 1)/(Tv + Ti + 2). 입력 넷의 DC 경로는 `loop_dc_choke_H` 인덕터(측정 대역에서 β 망보다 충분히 큰 임피던스),
    되먹임이 없는 입력은 AC 접지(결합 C + AC 0 원).
  - **[신규 2026-10-08] 분모 0 = 정의 불가**(`oracle_simulate.loop_probe_singular`): 데이터 파일 값으로 Σ w·V(넷) = 0(Tv 정의 불가),
    Σ w·(w − I_x) = 0(Ti 정의 불가 -- 주입 전류가 전부 되먹임 쪽으로 가고 증폭기 쪽 전류가 파일 분해능에서 0, 즉 그 주파수에서
    절단 넷의 증폭기 쪽 어드미턴스가 사실상 choke 뿐), 또는 Tv + Ti + 2 = 0 인 표본이 하나라도 있으면 그 표본의 T 가 정의되지
    않으므로 루프 측정 전체를 쓰지 않는다: `sim.loop.measures = None`, `sim.loop.singular = {count, first{f_hz, which}, points(앞
    20 개)}`, `ac.pm_deg = None`, `ac.pm_undefined = "loop_probe_singular"`, `ac.stability.reason` 에 첫 표본. 측정 실패가
    아니므로 막힘이 아니다(compare 의 'β 루프 측정 결과 없음' 막힘은 singular 가 없을 때만). pm 제약·metric 판정 칸
    `N/A(정의 불가: loop_probe_singular)` -> C8 대로 PASS 불가(INCOMPLETE, 다른 FAIL 이 있으면 FAIL). 0 이 아닌 아주 작은
    분모는 그대로 계산한다(Ti -> ∞ 극한에서 T -> Tv). 재현(2026-10-08, 손 입력 test 아님): 단일 입력 nin, 되먹임 Cf
    (nout–nin, 1 pF)와 입력 결합 Cin(nin–g, 1 pF) 둘 다 feedback_passives(옛 C12 '입력 넷 passives 전부' 규칙과 같은 꼴), 입력 넷에
    접지 C 없음 -> 증폭기 쪽 = loop choke 뿐 -> 891 Hz 부터 170 표본에서 Σ w·(w − I_x) = 0. 고치기 전 oracle_simulate 는
    ZeroDivisionError 로 죽어 compare 가 없었다; 고친 뒤 INCOMPLETE(pm_min `N/A(정의 불가: loop_probe_singular)`), 막힘 없음.
* 선언이 없으면 **β=1 루프**: L = 개루프 A(입력 차동 AC -> 출력)의 위상여유.
* 두 경우 모두 PM = 180 - (기준점 위상 - |L|=1 첫 하강 교차의 위상) [deg], 기준점 = 측정 첫 주파수(fstart), 위상은 언랩.
  `ac.pm_deg` = 이 값, `ac.pm_definition` = `beta_loop`|`beta_1`, `ac.pm_open_loop_deg` = 늘 A 기준 값,
  `ac.loop_gain_dc_db`/`ac.loop_ugf_hz` = T 의 기준점 크기·교차 주파수.
* **[신규 2026-10-08] 안정 여유 조건**: 위 식은 개루프 L 에 RHP 극이 없을 때(P = 0)만 안정 여유다. 오라클은 P = 0 을
  SPICE 로 증명할 때만 `ac.pm_deg` 를 값으로 두고, 아니면 정의 불가(`ac.pm_deg = None`, `ac.pm_undefined = <이유>`,
  Bode 식 원값은 `ac.pm_deg_raw`)다 -- 절차·이유 어휘는 아래 "[신규] C10 PM 안정성 근거".
* 검증: 이상 gm 증폭기 + Cf/Cs/Cin 회로에서 해석식 T 와 1.3e-4 이내 일치(2026-10-07).
* **[신규 7a]** 엔진 `pm_ss_deg` 는 같은 절단(`feedback` 소자의 입력 포트 넷 쪽 단자)·같은 두 주입을 절단 회로 MNA 의 Z 행렬로
  중첩 계산한다(`_drafts/engine/design_7a_loop_output_views.md` 2.4) -- 수식 T = (Tv·Ti − 1)/(Tv + Ti + 2) 동일.
* **[신규 7a] 가중 정의**: 차동 입력(`input_p`·`input_n`)은 v_id = `input_p_ac − input_n_ac` = 1, v_cm = `input_p_ac + input_n_ac`
  = 0(즉 +½, −½), 단일 입력(`input`)은 `input_ac` = 1. β 루프 T 는 가중의 공통 배율에 무관하지만 부호·비가 모드(차동/공통)를
  고르고, β=1 의 A 는 배율에 비례하므로 이 정의값이어야 엔진과 같은 양이다(C27 이 검사).
* **[신규 7a]** 엔진과의 차이(기록으로만 드러냄, 판정 아님): 엔진 기준점은 ω → 0 극한, 오라클은 fstart(C10 과 같은 관례);
  엔진은 절단 넷의 DC 경로가 없고 오라클은 `loop_dc_choke_H` 를 둔다 -> C27 의 `ac.loop_choke_ratio` 가 그 근사의 크기.

## 바이어스 모드

* `free`: 회로가 DC 해를 스스로 찾는다. 입력 DC 는 choke 로, AC 는 결합 C 로. 출력 -> 반대 극성 입력 DC 되먹임
  (단일 출력: `out -> input_n`, 오프셋 V_out_pred - V_in_pred; 차동 출력: 차동 성분 k*(Vo-Vo') 만, 입력 공통모드는
  예측값). `nodeset_from_predictions` 이면 예측 노드전압을 `.nodeset`(초기값일 뿐).
* `forced`: 예측 전압이 있는 소자 단자 넷 전부를 choke 로 예측값에 묶는다. DC = 엔진이 의도한 바이어스,
  고정원 전류 = 그 넷의 KCL 잔차(`kcl_residual`), AC 는 choke 가 열려 실제 모델 개루프 응답. 진단용.

## 출력 (`oracle_run.py`, bias 마다)

`<circuit>[.<tag>].<bias>.cir` / `.cir.meta.json` / `.log` / `.ac.txt` / `.sim.json` / `.compare.json` / `.compare.md`
(+ feedback_passives 가 있으면 `.loop.cir` / `.loop.log` / `.loop.v.txt` / `.loop.i.txt`, **[신규]** ratio_db 뷰가 있으면
`.ratio<k>.num.txt` / `.ratio<k>.den.txt`, **[신규 C26]** rout_ohm 뷰가 있으면 `.rout<k>.txt`, **[신규 C10]** PM 값이 있으면
`.stabop.cir` / `.stabop.log` / `.stab.cir` / `.stab.log` / `.stab.txt`, 연장 실행을 했으면 `.stab2.cir` / `.stab2.log` /
`.stab2.txt`).
`compare.json` 최상위: `summary{verdict, verdict_reason, warnings, acceptance{constraints_failed, constraints_unmeasured,
conducting_devices, unsaturated_conducting, sat_margin_V, off_current_A, off_in_spice, conduction_not_evaluated},
junction_capacitance, transient, record_counts, sat_in_spice, not_sat, spice_ac, spice_ratio, spice_rout, pm_loop,
stability, rail_current_A}`(**[신규 C10]** `stability`),
`performance`, `constraints`, `kcl_residual`, `devices`(행마다 **[신규]** `off_current_A_pred`, `conduction_threshold_A`,
`predicted_conducting`, `conduction_check`, `diffusion`), `nodes`, `blockers`, `notes`, `judge_config`, `lut_meta`, `provenance`.
측정 정의(개루프 A): gain = |H(fstart)|, UGF = |H|=1 첫 하강 교차(log 보간), f-3dB = |H| < |H0|/sqrt2 인 첫 주파수 점,
supply_current = 레일 전압원이 공급하는 전류. PM 은 위 "PM 정의". **[신규]** ratio_db(CMRR·PSRR)는 C24, 슬루·정착은 C25,
**[신규]** 출력 저항 rout_ohm 은 C26.

## 동작 계약 (test 작성자용 -- 이 디렉터리의 test 는 다른 agent 가 쓴다)

표시: **[변경]** = 2026-10-07 사용자 확정 반영으로 바뀐 항목, **[신규]** = 추가.

C1. 입력 독립성: `oracle_*.py` 는 엔진 패키지(`gmid_engine`, `legacy`)를 import 하지 않는다. `legacy_adapter.py` 만 legacy 를 import 한다.
C2. **[변경]** 코너·온도: 넷리스트의 `.temp` 는 `process.lut_npz` 의 `temp_c`, include 경로의 `{corner}` 는 npz `corner` 로 채워진다.
    npz 에 둘 중 하나라도 없으면 `meta.blockers` 에 들어가고(.temp 줄은 쓰지 않음), ngspice 를 돌리지 않으며(`sim.skipped`),
    `compare.summary.verdict == "BLOCKED"`, `oracle_run.py` 반환 2.
C3. **[변경]** finger 규칙: 소자 하나당 `X<name>` 줄 정확히 1개, `w=finger_w`, `m=n_fingers`, `nf=` 없음.
    확산 기하(C22 출처 순서): `devices[].diffusion` 이 있으면 `ad=ad_m2 as=as_m2 pd=pd_m ps=ps_m`, 없고 `process.diffusion`
    이 있으면 `ad=as=ad_per_w_m*finger_w`, `pd=ps=finger_w+pd_extra_m`, 둘 다 없으면 ad/as/pd/ps 없음(free 면 C22 막힘).
C4. 레일: `reference=true` 넷은 SPICE 노드 `0`, 나머지 레일은 `Vrail_<net>` 전압원. reference 가 1개가 아니면 막힘.
    대소문자만 다른 두 넷(전압 같은 레일 별칭 제외)은 막힘.
C5. free: 차동 입력+차동 출력이면 `Efb_<in>` 이 (Vo-Vo') 차동 성분을 `diff_feedback_gain` 배로 되먹이고 `Vofs_<in>` 은 -V_in_pred;
    단일 출력이면 `out -> input_n` 이득 1, 오프셋 V_out_pred - V_in_pred; 되먹임 없는 입력은 `Vdc_<in>` + choke.
    **[명확화]** 출력 DC 되먹임(`Efb_`·`Vofs_`·`Lfb_`)은 **차동 입력(`input_p`·`input_n` 둘 다 있음)에만** 건다. 단일 입력
    (`input`) 회로는 출력 종류와 무관하게 되먹임이 없고 그 입력은 `Vdc_<in>`(예측 DC) + `Ldc_<in>` choke 이다. 차동 입력 +
    단일 출력이면 `input_n` 에만 `Efb`(`input_p` 는 `Vdc`), 차동 입력 + 차동 출력이면 두 입력 모두 `Efb`.
    forced: 레일·입력·게이트 전용 바이어스 넷을 뺀 모든 소자 단자 넷(예측 있음)에 `Vhold_<net>` + choke, free 모드 `.nodeset` 없음.
C6. 게이트 전용 넷(드레인/소스/전원/수동소자/입력 어디에도 안 물림): `bias_voltages` 값, 없으면 `predictions.nodes` 값의
    `Vbias_<net>` 과 notes 경고, 둘 다 없으면 막힘.
    **[신규 Q6]** topology 가 연결 동일성(C15) 대상일 때 `bias_voltages` 의 넷 집합은 topology `bias_inputs`(키가 없으면 빈 집합과 대조 -- 엄격,
    authoring 게이트 `gate_only_undeclared`/`bias_input_not_gate_only` 가 gate 전용 넷 전부임을 보장)와 **같아야** 한다.
    다르면 C15 diffs 에 들어가 막힘. 옛 어댑터는 `bias_inputs` 넷마다 엔진 예측 노드전압을 `bias_voltages` 로 선언한다.
C7. **[변경]** 기록: 오차 = SPICE - 예측(abs) 또는 (SPICE - 예측)/|예측|(rel). 허용오차가 있으면 기록 칸 `judge` 에 `|오차| <= tol`
    PASS / 밖 FAIL, 없으면 `N/A(tol 미설정)` -- **verdict 와 무관**. 영역: `sat_margin_V` 없으면 `None`(+`N/A(sat_margin 미설정)`),
    있으면 VDS - VDSAT >= margin 이 `sat`, 아니면 `triode`; 그 소자 문턱(**[변경]** `predictions.devices[].off_current_A`,
    없으면 `judge.off_current_A`)이 있으면 |ID| < 그 값은 `off`.
    영역 기록 칸 = SPICE 영역 == predictions.devices[].region. 테스트벤치가 고정한 넷의 노드 기록은 `N/A(테스트벤치가 고정)`.
    forced 모드에서 |ID_rel| > tolerances.ID_rel 또는 |gm_rel| > tolerances.gm_rel 인 소자는 `summary.warnings` 와 Markdown 맨 앞.
C8. **[변경]** verdict: 막힘이 있으면 `BLOCKED`. forced 모드는 그 밖에 늘 `INCOMPLETE`. free 모드는 선언 제약 FAIL 이 있거나
    포화 아닌 전도 MOS(ID > 그 소자 문턱, 합격 정의 2)가 있거나 **[신규]** SPICE 에서 꺼진 '엔진 예측 전도' MOS(C23)가 있으면
    `FAIL`; 아니면 `sat_margin_V` 미설정이거나 SPICE 값을 못 얻은 제약이 있거나 **[신규]** 전도 확인을 판정 못 한 소자(C23)가
    있으면 `INCOMPLETE`; 아니면 `PASS`. `oracle_run.py` 반환 코드: PASS/INCOMPLETE 0, FAIL 1, BLOCKED 2(여러 bias 중 최악).
C9. **[변경]** acceptance 제약: `op` 이 `>=`/`<=` 일 때 SPICE 값으로 PASS/FAIL, SPICE 값 없으면 `N/A(SPICE 값 없음)`. 제약은 판정 대상.
C10. **[변경]** 측정: 위 "측정 정의"와 "PM 정의" 그대로. |L| 가 1 아래로 내려가지 않거나 첫 점부터 1 미만이면 `ugf_hz`/`pm_deg` 는 None.
    **[변경 2026-10-08]** PM 값이 나와도 그것이 안정 여유임(개루프 RHP 극 수 P = 0)이 증명되지 않으면 `ac.pm_deg` 는 None 이고
    `ac.pm_undefined` 에 이유가 있다(원값 `ac.pm_deg_raw`). pm_deg 제약·metric 판정 칸은 `N/A(정의 불가: <이유>)`, 제약이면
    C8 의 'SPICE 로 값을 못 얻은 제약'이라 free verdict 는 **PASS 불가 -> INCOMPLETE**(다른 FAIL 이 있으면 FAIL).
    정의·절차·어휘는 아래 "[신규] C10 PM 안정성 근거".
C11. 숫자 기본값: `oracle_*.py` 에 허용오차·포화 여유·테스트벤치 값의 숫자 기본값이 없다(모두 입력/인자). 스키마 필수 testbench 값이
    빠지면 C13 거부, 선택 값(`input_*_ac`, `diff_feedback_gain`, `loop_dc_choke_H`)이 필요한데 없으면 막힘.
    **[신규]** C27 의 가중 검사(차동 차 1·합 0, 단일 1)는 정의값 검사이지 숫자 기본값이 아니다 -- 값은 여전히 입력에서만 온다.
C12. legacy_adapter: 같은 dump 를 두 번 변환하면 같은 입력이 나온다(provenance 경로 제외). `--from-dump` 결과와 엔진을 새로 돌린
    결과는 엔진이 결정론적이면 같다. **[변경]** 입력 포트 넷에 단자가 물린 passives 를 `feedback_passives` 로 선언한다.
    **[신규 7a 보충]** 이 '입력 넷에 물린 passives 전부' 규칙은 **옛 엔진 기준선 전용**이다. 어댑터는 그 표지로
    `feedback_passives_basis = "legacy_c12_input_net_passives"` 를 쓴다. 새 엔진이 오라클 입력을 만들 때는
    `feedback_passives` = spec `feedback.elements` 그대로(다시 추론하지 않음, 7a design 2.2 L1)이고 표지는
    `"spec_feedback_elements"` 다. 두 규칙이 다른 집합을 고르면(예: 파일럿 CI-10 이 {Cf1, Cf2} 를 고르면 옛 규칙은
    {Cf1, Cf2, Cs1, Cs2}) 두 PM 은 **다른 루프**를 잰 값이라 직접 비교하지 않는다 -- 비교하는 쪽은
    `compare.summary.pm_loop{pm_definition, feedback_passives, feedback_passives_basis, loop_break_nets, loop_weights}` 를 보고
    가른다. 오라클은 표지를 해석하지 않고 그대로 옮긴다(판정 무관, 없으면 None).
C13. **[신규]** 스키마 검증: `oracle_netlist.py`, `oracle_compare.py`, `oracle_run.py` 는 입력을 `oracle_input.schema.json`
    (Draft 2020-12)으로 검증하고, 위반이면 위반 목록을 출력하고 **아무 산출물도 쓰지 않고** 반환 2 로 끝난다.
C14. **[신규]** β 루프: `feedback_passives` 가 있으면 `<stem>.loop.cir` 에서 그 소자들의 입력 넷 단자만 `lbx_<넷>` 으로 바뀌고,
    끊은 넷마다 `Vlb_<넷> <넷> lbx_<넷>` 과 `Ilb_<넷> 0 <넷>` 이 있고, 그 넷의 결합 C/AC 원은 없다. **[변경]** 판정은 소자 단위(fail-closed):
    선언된 되먹임 수동소자 **각각**이 passives 에 있고 입력 포트 넷에 물려 있어야 하며, 하나라도 아니면 막힘이고 blocker 문장에
    그 소자 이름을 적는다. `loop_dc_choke_H` 가 없어도 막힘.
    **[신규 7a 보강]** 선언된 되먹임 수동소자의 두 단자 중 입력 포트 넷에 물린 단자는 **정확히 1개**여야 한다. 두 단자가 모두
    입력 포트 넷(서로 다른 두 입력 넷 사이, 또는 같은 입력 넷 양단)이면 절단 단자가 정해지지 않으므로 막힘이고 blocker 문장에
    그 소자 이름과 단자를 적는다(엔진 `feedback_cut_ambiguous` 와 같은 조건; 0개는 위 기존 막힘 = 엔진
    `feedback_element_not_on_input`). 막힌 입력은 ngspice 를 돌리지 않는다(C8 BLOCKED).
    **[신규 7a]** 루프 넷리스트의 2회(전류 주입) 데이터 파일 `<stem>.loop.i.txt` 는 끊은 넷마다 `i(Vlb_<넷>)` 열 뒤에
    (C27 기록용) 끊은 넷마다 `v(<넷>)` 열을 같은 넷 순서로 덧붙인다. T 계산은 앞의 i 열만 쓴다(값 변화 없음).

## [신규] 연결 동일성·단독 소자·진단 도구 (2026-10-07, 근거 `_drafts/engine/reference_review/` SYNTHESIS T09·T05(4), G4-11·G4-12, G3-06·G3-07·G3-14)

### 입력 스키마 추가(전부 선택 필드)

* `topology{path, sha256?}`: C15 대조용 topology JSON. `path` 는 **저장소 루트 기준 상대 경로**(`/` 구분, 예
  `skills/analog-gmid-design/assets/library/<회로>.topology.json`) -- 기계·worktree 에 무관하게 같은 문자열. 저장소 루트 =
  입력 파일 폴더에서 위로 올라가며 처음 `.git`(폴더 또는 worktree 파일)이 있는 폴더, 없으면 오라클 코드 폴더에서 같은 방법.
  루트를 못 찾거나 파일이 없으면 `unverified`. 절대 경로도 받지만 이식성이 없다. 진입점 `--topology`(그대로 절대화)가 우선.
  `sha256` 대조는 C15 대로.
* `passives[].not_in_topology_reason`, `sources[].not_in_topology_reason`: topology 에 없는 원소(예: 어댑터가 spec CL 로 넣은
  부하)를 C15 비교에서 뺄 때 그 이유. 비교 결과 `declared_not_in_topology` 에 그대로 남는다.
* `process.models[kind].polarity` (`n`|`p`): iso 모드가 크기 규칙 예측을 단자 전압으로 바꿀 때 쓴다.
* `predictions.devices[].tol{ID_rel, gm_rel, basis?}`: 소자별 LUT 계산 허용오차(엔진이 그 소자 셀 tol 에서 계산한 값).

### 동작 계약 추가

C15. **[신규]** topology 연결 동일성(free/forced): `oracle_netlist.py` 가 자기가 쓴 본 넷리스트(.control 앞)를 다시 파싱해
    회로 원소 표(이름, 종류, 단자 넷)를 만들고 topology JSON(`netlist` + `passive_elements` + `ideal_sources`)과 비교한다.
    - 원소 분류는 넷리스트 이름 접두사로만: `X`=소자(종류 = subckt -> models kind), `Rp_`/`Cp_`=저항/커패시터,
      `Isrc_`/`Vsrc_`=전류/전압원(topology `current_source`/`voltage_source` 와 같은 뜻). 테스트벤치 원소(`Vrail_ Efb_ Vofs_
      Lfb_ Vdc_ Ldc_ Cac_ Vac_ Vbias_ Vhold_ Lhold_ Vlb_ Ilb_ Vshort_ Viso_ Irout_`)는 빼고 `excluded_testbench` 에 적는다
      (**[신규]** `Irout_` = C26 감지 전류원).
      어느 쪽에도 안 맞는 원소는 차이(fail-closed). SPICE 노드 `0` 은 reference 레일 넷 이름으로 되돌려 비교한다.
    - 같아야 하는 것: 원소 이름 집합, 원소마다 종류, 단자 넷. MOS 는 (drain, gate, source) 순서 그대로(+ topology 가
      `bulk` 를 선언한 원소는 bulk 도), 저항·커패시터는 순서 무관, 이상원은 순서 그대로(방향).
    - `not_in_topology_reason` 이 있는 입력 원소는 비교에서 뺀다(topology 에 같은 이름이 있으면 '넷리스트에 없음' 차이).
    - 결과 `meta.topology_identity` / `compare.topology_identity` = `{status, topology_path, sha256_actual, sha256_declared,
      diffs, compared, excluded_testbench, declared_not_in_topology, bulk_compared, notes, required}`,
      `compare.summary.topology_identity = {status, required, diff_count, path}`. status:
      `verified`(차이 0) / `mismatch` -> **막힘**(blocker 문장에 차이 목록) / `unverified`(topology 없음 또는 파일 없음 -- 표시만,
      verdict 무관) / `not_applicable`(iso).
    - `--require-topology`(합격 실행 플래그, `oracle_netlist.py`·`oracle_run.py`): `unverified` 이면 막힘.
    - 입력 `topology.sha256` 이 실제 파일 sha256 과 다르면 notes 에 기록만 한다(판정은 연결 비교로).
    - Z1 실행(C18)에서는 변경 **전** 넷리스트로 비교한다.
C16. **[신규]** 소자별 허용오차: `predictions.devices` 중 하나라도 `tol` 이 있으면 소자별 모드 -- 소자 기록의 ID·gm 판정,
    forced 경고(C7), iso 판정(C17), forced 진단(C19)이 그 소자의 `tol.ID_rel`/`tol.gm_rel` 만 쓰고, 없는 소자는
    `N/A(tol 미설정)`(judge.tolerances 의 ID_rel/gm_rel 스칼라로 채우지 않는다). 아무 소자도 `tol` 이 없으면 기존 스칼라 동작.
    소자 기록에 `tol_ID_rel`, `tol_gm_rel`, `tol_source`(`device`|`device(없음)`|`scalar`|`none`)를 남긴다.
C17. **[신규]** `--bias iso`(단독 소자, K3): 소자마다 `X<name>` 인스턴스 하나(C3 finger·확산 규칙 동일)를 자기 노드
    `iso_d_/iso_g_/iso_b_<name>` 에 두고 소스를 0 으로, `Viso_g/d/b_<name>` 이상 전압원으로 V(g) = s·VGS, V(d) = s·VDS,
    V(b) = -s·VSB 를 건다(s = polarity n:+1, p:-1, 값은 predictions.devices 크기 규칙). `.op` 만, 회로 연결·테스트벤치 없음.
    예측 VGS/VDS/VSB 나 polarity 가 없는 소자는 인스턴스를 만들지 않고 `meta.iso_skipped` 에 이유. 한 소자도 못 만들면 막힘.
    `compare.summary.iso = {verdict, within_tol, outside_tol, not_judged, rule}`: |ID_rel| <= 그 소자 허용오차(C16)면 안,
    verdict = 하나라도 밖이면 FAIL, 판정 못 한 소자가 있거나 판정한 소자가 없으면 INCOMPLETE, 아니면 PASS.
    iso 의 `summary.verdict` 는 진단 모드라 막힘이 없으면 늘 `INCOMPLETE`(C8 의 forced 와 같은 규칙).
C18. **[신규]** Z1 제거법 `--omit <원소..>`(소자·수동소자·이상원을 넷리스트에서 뺌), `--short <수동소자..>`(`Vshort_<name>` 0 V
    전압원으로 단락). 없는 이름, 수동소자가 아닌 단락, 같은 원소 중복(같은 옵션 안 반복 예 `--omit RL RL`, 또는 omit·short
    사이 중복), `feedback_passives` 원소 변경은 막힘.
    뺀 소자는 비교 행이 없고 `summary.z1.omitted_devices` 에 적는다. free 모드 verdict 는 막힘이 없으면 `INCOMPLETE`
    (회로를 바꾼 진단 실행이라 합격/불합격을 내지 않는다). 결과 이름이 섞이지 않게 `--tag` 를 같이 쓴다.
C19. **[신규]** 진단(기록만, verdict 무관):
    - forced compare `diagnosis`: (1) 고정원 넷마다 |KCL 잔차| 대 그 넷에 드레인/소스가 물린 소자들의 tol_I = |ID_pred|·tol_ID_rel
      합(C16 허용오차, 없는 소자가 물리면 그 넷은 판정 안 함) -> `kcl_nets[]`, `kcl_nets_exceeding`, `dc_consistent`
      (판정한 넷 전부 안 True / 하나라도 밖 False / 판정한 넷 없음 None). (2) 게이트 공유 넷(게이트에 소자 2개 이상)마다
      소자별 등가 dVGS = (ID_spice - ID_pred)/gm_pred 와 퍼짐(최대-최소), 퍼짐 큰 순.
    - free compare `diagnosis_free`(`oracle_run.py` 가 free 와 forced 를 함께 돌렸을 때, 또는 `oracle_compare.py --forced-compare`):
      free verdict 가 FAIL 이 아니면 `not_applicable`; forced 결과가 없거나 막힘이면 `unknown`; forced `dc_consistent` True ->
      `boundary_condition`(엔진 DC 정합, free 수렴·경계조건 쪽), False -> `engine_dc_inconsistent`, None -> `unknown`.
C20. **[신규]** PM 교차 측정(기록만): `ac.pm_deg` 를 정한 루프 이득 L(β 루프면 T, 아니면 A)로 폐루프 C = L/(1+L) 의 peaking
    Mp = max|C|/|C(fstart)| 를 재고 2차계 관계 Mp = 1/(2z·sqrt(1-z²)) 로 z, PM = atan(2z/sqrt(sqrt(1+4z⁴)-2z²)) 를 역산해
    `ac.pm_crosscheck_deg`, `ac.closed_loop_peaking_db`, `ac.closed_loop_peak_hz`, `ac.pm_crosscheck_gap_deg`(= 교차 - pm_deg).
    peaking 이 없으면(최대가 첫 점, 또는 Mp <= 1 + δ) `pm_crosscheck_deg`·`closed_loop_peaking_db`·`closed_loop_peak_hz` 는
    None 이고 `pm_crosscheck_note` 에 2차 근사 하한(z = 1/sqrt2 의 PM)을 적는다. δ = Mp 의 데이터 분해능
    = 2·n·u (`ac.pm_crosscheck_mp_resolution`): u = 0.5·10^(1-d) 는 ngspice 가 L 데이터 파일(wrdata)에 실제로 찍은 가수
    유효숫자 d(파일 전체 최솟값, 루프면 v·i 두 파일 중 거친 쪽)의 반올림 반 단위, n 은 L 한 표본을 만드는 파일 실수 개수
    (A: 2, β 루프 T: 끊은 넷마다 6), 2 는 Mp 가 두 표본의 비라서. 엔진 pencil_roots 원점 판정(차원·eps·‖A‖)과 같은 꼴의
    1차 반올림 한계이고 상수가 없다(분해능 아래의 Mp-1 은 수치 잡음).
    같은 AC 데이터의 다른 측정 방법이라 교차점·위상 언랩 오류를 잡는 용도이고, 2차계가 아닌 루프에서는 근사다.
    **[변경 2026-10-08]** PM 이 정의 불가(C10 `ac.pm_undefined` 있음)면 교차 측정도 위상여유가 아니다(개루프 RHP 극·불안정
    폐루프의 |L/(1+L)| peaking 은 2차계 PM 관계를 따르지 않는다 -- 실측 ngcc 프로브: 교차 63.1 deg, 폐루프 과도 지속 진동):
    `ac.pm_crosscheck_deg = None`, `ac.pm_crosscheck_gap_deg = None`, 원값 `ac.pm_crosscheck_deg_raw`(peaking 이 없었으면 None),
    `ac.pm_crosscheck_note` = `정의 불가(<이유>) -- ...`. `closed_loop_peaking_db`·`closed_loop_peak_hz`·
    `pm_crosscheck_mp_resolution` 는 |C| 측정값이라 그대로 남긴다. PM 이 유효하면 C20 값은 이전과 같다.
C21. **[신규]** 실행 캐시(선택, `--cache-dir`): 키 = sha256(넷리스트 바이트 + 넷리스트가 `.include`/`.inc`/`.lib` 로 읽는 모델 파일
    전부(재귀, 경로+바이트) + ngspice 실행 파일 경로 + `-b`). 같은 키면 ngspice 를 돌리지 않고 저장한 로그·데이터 파일
    (`.ac.txt`, 루프 `.v.txt`/`.i.txt`, C24 `.ratio<k>.*.txt`, **[신규]** C26 `.rout<k>.txt`, **[신규 C10]** `.stab.txt`·`.stab2.txt`)을 복원한다. 모델 파일을 하나라도 못 찾으면 캐시를 쓰지 않는다. `sim.cache =
    {main, loop}` 이 `hit`/`miss`/`off(모델 파일 못 찾음)`/None(캐시 미사용). **[신규 C10]** 폐루프 과도 실행의 캐시 상태는
    `sim.stability_cache = {op_pass, transient}`(+ 연장 실행을 했을 때만 `extension` 키; 같은 어휘; 결과가 아니라 `ac` 밖에 둔다 --
    hit·miss 에서 `ac` 는 같다).
C12 보충. **[신규]** legacy_adapter: `topology{path, sha256}` 를 쓰고, topology 에 없는 출력 부하(`LOAD_<출력>`)에
    `not_in_topology_reason` 을 달며, `models[kind].polarity` 를 LUT 생성기 `run_device(..., polarity=±1)` 에서 읽는다.

### 구현하지 않은 것(근거 문서의 뜻이 정해지지 않음)

* `--ideal`(엔진 `ss` 의 VCCS+gds+C 등가 넷리스트): 입력에 소신호 용량(cgs·cgd·cdb·…)이 없고, 재사용하라는 'MNA 오라클'이
  아직 계획만 있어 등가회로의 원소 구성을 정할 근거가 없다.
* 결과 JSON `connectivity_fp` 대조: 엔진 `fp_of` 정의를 오라클이 import 없이(C1) 똑같이 재현한다는 보장이 없다. 대신 C15 가
  topology 파일 자체와 직접 비교하고 파일 sha256 을 기록한다.
* 슬루·정착의 `.tran` 측정(C25): 정의가 계약에 없어 `not_measured` 로 기록만 한다.

## [신규] Q5·Q6 사용자 결정 반영 -- 꺼진 소자, CMRR·PSRR, 슬루·정착, 접합 용량 (2026-10-07, 근거 `_drafts/engine/reference_review/` SYNTHESIS Q5·Q6, T03·T07·T09, G5-01·G6-02·G3-10·G1-02·G3-02·G2-16·G6-10·G1-12)

### 입력 스키마 추가

* `predictions.devices[].off_current_A`(≥ 0): 소자별 전도 문턱. **엔진이** 그 소자의 LUT VGS=0 누설 ID(그 소자 기하·VDS·VSB)로
  계산해 넣는다. 오라클은 이 값을 만들거나 대신할 상수를 두지 않는다.
* `predictions.devices[].region` 에 `off` 추가: 엔진이 꺼짐으로 예측한 소자(전도 확인 대상 아님).
* `devices[].diffusion{ad_m2, as_m2, pd_m, ps_m, basis?}`: 소자별 확산 기하(finger 하나 = m 단위 하나당 값).
* measure `ratio_db`(제약·metric 모두) + 항목 `view{num, den}`(각각 `{ac_excite{넷: 진폭}, sense_p, sense_n, sense_mode}`,
  measure 가 `ratio_db` 면 필수). metric measure `slew_rate_v_per_s`·`settle_s`(기록 전용, 제약 enum 에는 없음).
  허용오차 키 `tolerances.ratio_db_abs`.

### 동작 계약 추가

C22. **[신규]** 접합 용량·확산 기하(Q6):
    - 넷리스트 소자 줄의 ad/as/pd/ps 출처 순서: (1) `devices[].diffusion` -> `ad=<ad_m2> as=<as_m2> pd=<pd_m> ps=<ps_m>`
      (Euler 행 공유 확산: MOD7 `ly.diffusion[dev]` 통계에서 엔진·어댑터가 소자 전체 값을 n_fingers 로 나눈 finger 평균;
      인스턴스는 `m=n_fingers` 를 유지하고 ngspice 가 m 배 한다 -- nf 인스턴스는 C3 그대로 금지), (2) 없으면 `process.diffusion`
      규칙(레이아웃 전 첫 사이징점: **LUT 생성 규칙** -- `assets/sky130_lut_sweep.py` 의 DUT 줄 `w=5u ad=2.5p pd=7u` 에서
      `ad_per_w_m = 2.5e-12/5e-6 = 0.5e-6 m`, `pd_extra_m = 7e-6 - 5e-6 = 2e-6 m`; legacy_adapter 가 이 줄에서 읽어 넣는다),
      (3) 둘 다 없으면 ad/as/pd/ps 를 쓰지 않는다.
    - free 모드(합격 실행, Z1 free 포함)에서 (3)인 소자가 하나라도 있으면 **막힘**: blocker 문장
      `C22 접합 용량: 확산 기하 없는 소자 [...]`(이름 정렬). forced·iso 는 막지 않고 notes 에 그 소자 목록을 남긴다.
    - meta `geometry[<소자>].diffusion` = `{source: "device"|"process_rule"|null, ad, as, pd, ps}`(null 출처면 값 4개 None).
      `compare.summary.junction_capacitance = {included(전 소자 출처 있음 bool), by_source{device, process_rule, none},
      missing[소자], zero_area[소자]}`. 값 0(ad=as=pd=ps=0)은 '접합 용량 없음'을 **명시한** 선언이라 막지 않지만
      `zero_area` 에 이름을 남긴다(test 픽스처가 접합 용량 없는 독립 넷리스트와 같은 회로를 free 로 돌릴 때 쓴다 --
      실제 엔진 입력에서 나오면 기하 출처를 의심할 표지).
    - 값은 오라클이 계산하지 않는다: ngspice 가 PDK 모델카드 접합 파라미터(CJ·CJSW·MJ·MJSW·PB 등)와 ad/as/pd/ps 로 계산한다.
      확인(2026-10-07, ngspice-46, sky130 tt, nfet_01v8 L=0.5 µm W=5 µm VDS=0.9 V VGS=0.7 V, 1 MHz 드레인 AC 전류의
      허수부/ω): m=1 1.927 fF -> ad=as=2.5p pd=ps=7u 4.350 fF, m=2 3.854 fF -> 8.700 fF(접합분 2.42 / 4.85 fF, m 배).
      subckt 가 `ad = {ad}` 등을 내부 소자로 넘긴다(`.param ad = 0 ...`, 기본 0 = 접합 용량 없음).
C23. **[신규]** 꺼진 소자(Q5 (i)): free·forced·iso 모든 비교 행에 `off_current_A_pred`, `predicted_conducting`,
    `conduction_check` 를 남긴다. 소자 행마다:
    - `predicted_conducting`: `predictions.devices[이름]` 이 없으면 None, 있고 `region == "off"` 면 False, 아니면 True.
    - `conduction_check`: None 예측 -> `N/A(예측 없음)`; False -> `N/A(엔진 예측 off)`; True 이고 `off_current_A` 없음 ->
      `N/A(off_current_A 없음)`; SPICE ID 없음 -> `N/A(SPICE ID 없음)`; ID_spice(크기 규칙, 부호 포함) <= off_current_A ->
      `FAIL`(꺼짐 -- 역방향 전류도 여기에 든다); 아니면 `PASS`.
    - free verdict(C8): `FAIL` 이 하나라도 있으면 FAIL. `N/A(off_current_A 없음)`·`N/A(예측 없음)`·`N/A(SPICE ID 없음)` 인 소자가
      있으면 PASS 가 될 수 없고 INCOMPLETE(조용한 통과 금지). `N/A(엔진 예측 off)` 는 verdict 에 영향 없음.
    - `summary.acceptance` 에 `off_in_spice[소자]`, `conduction_not_evaluated{소자: 이유}` 를 더한다.
    - 합격 정의 2(포화)의 전도 문턱도 소자별 `off_current_A` 가 우선이다(없으면 `judge.off_current_A`). 행 칸
      `conduction_threshold_A` = 그 문턱, 둘 다 없으면 None(이때 전도 = 부호 있는 ID_spice > 0). 영역 기록 `off` 는 문턱이
      있을 때 |ID_spice| < 문턱.
C24. **[신규]** CMRR·PSRR = `ratio_db`(Q5 (ii) (A), 엔진 `ratio_ss_db` 와 같은 여기 정의):
    - 정의: 뷰 `{num, den}` 각각에 대해 .ac 한 번(모두 2회). 한 번의 .ac 에서 `ac_excite` 에 적힌 넷은 그 진폭(위상 0, 음수
      진폭 = 반대 위상)의 AC 전압으로, 테스트벤치가 이상 전압원으로 구동하는 **나머지 넷**(레일·입력·게이트 바이어스)은 AC 0 이다
      (엔진 MNA 가 여기 넷과 상대 뷰의 여기 넷을 고정하는 것과 같은 꼴). 응답 H = V(sense_p) - V(sense_n)(differential) 또는
      V(sense_p)(single_ended). `ratio_db = 20*log10(|H_num|/|H_den|)`.
    - 측정 주파수 = `testbench.ac.fstart_hz` 한 점(`ac lin 1 f f`) -- 오라클의 DC 대용 기준점(측정 정의의 gain 과 같음).
    - 여기 수단(넷리스트 이름은 그대로, `.control` 안에서 `alter @<원>[acmag]`): 입력 넷 = `Vac_<넷>`(결합 C 경유), 레일 =
      `Vrail_<넷>`, 게이트 전용 바이어스 넷 = `Vbias_<넷>`. 이 셋 밖의 넷(내부 넷, forced 고정 넷 포함)이나 reference 레일을
      `ac_excite` 에 적으면 **막힘**(이 넷을 AC 로만 고정할 수단이 없다 -- DC 를 바꾸지 않고 엔진 정의를 재현할 수 없음).
      sense 넷이 회로 넷(reference 제외)이 아니어도 막힘.
    - 같은 뷰(dict 동등)는 한 번만 잰다. 데이터 파일 `<stem>.ratio<k>.num.txt`/`.den.txt`(C21 캐시에 함께 저장·복원).
    - `sim.ratio = [{view, f_hz, num{re, im, mag}, den{re, im, mag}, ratio_db}]`(|H_den| = 0 이거나 파일이 없으면 ratio_db None).
      제약·metric 의 SPICE 값 = 같은 view 를 가진 항목의 ratio_db. 제약은 C9 그대로 판정 대상(PASS/FAIL, 값 없으면 N/A ->
      INCOMPLETE), metric 은 기록(tolerances.ratio_db_abs).
    - free·forced 둘 다 잰다(forced 는 진단 기록). iso·β 루프 넷리스트에는 없다.
    - **[가정 -- 엔진 `ratio_ss_db` 구현(MOD5 `gain.py`) 전이라 대조 못 함]** (a) 엔진 정의 문장은 "같은 MnaSystem 두 여기 열의
      응답비 dB"(design_mod1_lut_mod5_mna 3.4)뿐이라 평가 주파수는 `gain_ss_db` 의 H(0) 와 같은 DC 로 보고 오라클 DC 대용
      fstart 를 쓴다. (b) 여기 안 한 테스트벤치 원 = AC 0 은 옛 `_metric_smallsignal_ratio_db`(also_fix = 두 여기 넷 합집합 0 고정)
      와 같은 꼴이고, 그 밖의 레일·입력도 0 으로 둔다(이상 전압원이라 SPICE 에서 다른 선택이 없다). 엔진이 다르게 정하면 이
      항목을 바꾼다. 파일럿 spec 의 CMRR·PSRR 뷰는 아직 `{"pending": "MOD5"}` 라 어댑터가 넣을 뷰가 없다.
C25. **[신규]** 슬루·정착(Q5 (ii) (B), 기록 전용): metric measure `slew_rate_v_per_s`·`settle_s` 는 성능 기록 행을 만들지만
    SPICE 값은 None, 판정 칸 `N/A(not_measured: ...)`. `compare.summary.transient = {status: "not_measured", measures,
    reason}`. 이유: β 루프 `.tran` 정의(입력 계단 크기와 여기 넷, 정착 오차 대역, 슬루 측정 구간)가 엔진·spec 계약
    (`gmid_engine/authoring/SPEC_CONTRACT.md`, `_drafts/engine/design_spec_format.md` F11 -- settling 은 `{total_s, linear_s}`
    뿐이고 오차 대역 없음, `driving_spec.slew_rate_*` 는 MOD5 레지스트리 미정)에 없다 -- 추측으로 정하지 않는다. 정의가 정해지면
    이 항목을 측정으로 바꾼다. 제약 measure enum 에는 넣지 않았다(판정 대상 아님 -- 선언하려면 스키마 위반으로 드러난다).

## [신규] 7a 루프·출력 포트 뷰 -- 출력 저항, 정의 일치 검사 (2026-10-07, 근거 `_drafts/engine/design_7a_loop_output_views.md` 2.3·2.6·3.3·4.3)

### 입력 스키마 추가

* measure `rout_ohm`(제약·metric 모두) + 항목 `view` = 감지 전용 뷰 `$defs/sense_view`
  `{sense_p, sense_n?, sense_mode}`(measure 가 `rout_ohm` 이면 필수). `additionalProperties: false` 라 `ac_excite` 를 두면
  **스키마 위반**(C13: 아무 산출물도 쓰지 않고 반환 2). `sense_mode = "differential"` 이면 `sense_n` 은 필수 비빈 문자열,
  `"single_ended"` 면 `sense_n` 이 없거나 null(문자열이면 스키마 위반). 허용오차 키 `tolerances.rout_ohm_rel`(기록 전용, rel).
* `feedback_passives_basis`(C12 보충, 위).

### 동작 계약 추가

C26. **[신규]** 출력 저항 `rout_ohm`(엔진 `rout_ss_ohm` 의 출력 포트 뷰와 같은 여기 정의, 7a design 3.1·3.2·3.3):
    - 정의: 뷰마다 .ac 한 번, 주파수 = `testbench.ac.fstart_hz` 한 점(`ac lin 1 f f`, C24 와 같은 DC 대용 기준점). 그 .ac 에서
      테스트벤치가 이상 전압원으로 구동하는 **모든** 여기 원(레일 `Vrail_`, 입력 `Vac_`(결합 C 경유), 게이트 바이어스 `Vbias_`)의
      AC 진폭은 0 이고(`alter @<원>[acmag] = 0`, C24 수단), 감지 넷에 단위 AC 전류를 넣는다: single_ended 는
      `Irout_<k> 0 <sense_p> DC 0 AC …`(sense_p 로 +1 A 주입), differential 은 거기에 `Irout_<k>n <sense_n> 0 DC 0 AC …`
      (sense_n 에서 1 A 뽑음)을 더한다. 두 전류원은 넷리스트 본문에 `DC 0 AC 0` 으로 있고(.op·개루프 A·C24 실행에 영향 없음)
      자기 .ac 직전에만 `alter @irout_<k>[acmag] = 1`(다른 뷰의 것은 0)로 켠다. k = 뷰 번호(0부터, 아래 중복 제거 뒤 순서).
    - 응답 H = V(sense_p) − V(sense_n)(differential) 또는 V(sense_p)(single_ended) [V/A = Ohm]. **`rout_ohm` = Re(H)**(부호
      그대로가 아니라 아래 규칙), 기록에 Im(H)·|H| 도 남긴다.
    - **음의 실수부 = 정의 불가**(엔진 결정: 음의 출력 저항은 정의 불가 값이며 통과하지 않는다): Re(H) < 0 이면 `rout_ohm` = None,
      `undefined = "negative_real_part"`. 제약이면 판정 칸 `N/A(정의 불가: negative_real_part)`, 항목 `undefined` 칸에 같은 이유
      -> C8 에서 'SPICE 로 값을 못 얻은 제약'으로 세어 **free verdict 는 PASS 가 될 수 없고 INCOMPLETE**(다른 FAIL 이 있으면 FAIL).
      metric 이면 성능 기록 판정 칸이 같은 `N/A(정의 불가: …)`. Re(H) = 0 은 값 0(정의 불가 아님). 데이터 파일이 없으면
      `rout_ohm` None, `undefined = "no_data"` -> 판정 칸은 기존 `N/A(SPICE 값 없음)`.
    - 뷰 동일성: (sense_p, sense_n(없으면 null), sense_mode) 가 같으면 같은 뷰(`sense_n` 키 없음 = null)이고 한 번만 잰다
      (제약을 먼저, 그다음 metric 순서로 처음 나온 순서). 제약·metric 의 SPICE 값 = 같은 뷰의 측정 결과.
    - 막힘(넷리스트 meta.blockers, 문장이 `C26 rout_ohm` 으로 시작, 하나라도 있으면 rout 실행을 하나도 넣지 않음):
      `fstart_hz` 없음; 감지 넷(single_ended 는 sense_p, differential 은 둘 다)이 reference 레일; 회로 넷(소자·수동소자 단자 넷,
      reference 제외)이 아님; 테스트벤치가 이상 전압원으로 구동하는 넷(비-reference 레일, 입력 포트 넷, 게이트 전용 바이어스 넷 --
      엔진 출력 포트 뷰의 고정 노드라 정의 밖); differential 에서 sense_p == sense_n.
    - 데이터 파일 `<stem>.rout<k>.txt`(wrdata, C21 캐시에 함께 저장·복원). `meta.rout_runs = [{view, f_hz, file}]`,
      `sim.rout = [{view, f_hz, re, im, mag, rout_ohm, undefined}]`(view 는 정규형 `{sense_p, sense_n, sense_mode}`),
      `compare.summary.spice_rout = sim.rout`. 막힌 넷리스트의 sim 은 `rout: []`.
    - free·forced 둘 다 잰다(forced 는 진단 기록, verdict 는 C8 대로 INCOMPLETE). iso·β 루프 넷리스트에는 없다.
    - 개루프 값의 유효 조건(판정 아님, C27 `ac.dc_path_isolation`): free 단일 출력의 `Efb`·`Lfb` 처럼 choke 로 들어오는 DC 경로가
      fstart 에서 충분히 열려 있어야(ω²LC ≫ 1) 입력 AC 0 고정 = 엔진 고정 노드와 같다.
    - 확인(2026-10-07, ngspice-46 sky130 tt, 손으로 쓴 독립 넷리스트 + 손계산 대조, test 아님): NMOS CS(RL 100 kΩ) Re(H) =
      91430.56 Ω = RL‖(1/gds)(상대차 6e-8); 소스 팔로워(RS 10 kΩ) 1963.696 Ω = 1/(gm + gmbs + gds + 1/RS)(2e-7; 1/(gm+gmbs)
      = 2457 Ω 은 RS·gds 를 뺀 근사); 반회로 두 개 차동 139384.8 Ω = Ro1 + Ro2(독립 넷리스트와 1.4e-7); 교차 결합 쌍 차동
      Re(H) = −106960.5 Ω = 2/(1/RL + gds − gm) -> `negative_real_part`, 제약 N/A, verdict INCOMPLETE.
C27. **[신규]** 정의 일치 검사(엔진과 같은 양을 재는지):
    - 가중: metric·제약 중 하나라도 measure 가 `dc_gain_db`·`ugf_hz`·`pm_deg`(개루프 A 의 크기를 쓰는 값; `f3db_hz` 는 배율
      무관이라 제외)이면, 차동 입력(ports 에 `input_p`·`input_n`)은 `input_p_ac − input_n_ac == 1` 이고
      `input_p_ac + input_n_ac == 0`, 단일 입력(`input`)은 `input_ac == 1` 이어야 한다(부동소수 정확 비교). 아니면 막힘(문장이
      `C27 가중 정의` 로 시작, 실제 값과 해당 measure 를 적음). 해당 키가 없으면 이 검사는 보지 않는다(C11 이 막는다). 같은 키가
      β 루프 절단 가중이라(PM 정의) 이 검사가 루프 가중(차동 ±½, 단일 1)도 보장한다. 검사는 본·루프 넷리스트 모두에 걸린다.
    - 기록(판정 아님, 숫자 문턱 없음):
      `ac.dc_path_isolation = [{net, choke_H, couple_F, f_hz, omega2_LC, output_feedback}]` -- 본 넷리스트 입력 넷마다
      (2π·fstart)²·`dc_choke_H`·`ac_couple_F`, `output_feedback` = 그 입력에 free 출력 DC 되먹임(Efb)이 걸렸는가.
      `ac.loop_choke_ratio = [{net, f_hz, choke_H, node_impedance_ohm, ratio}]`(β 루프일 때, 아니면 None) -- 2회(전류 주입)
      실행의 첫 점에서 끊은 넷 k 마다 node_impedance = |V(n_k)/w_k|, ratio = |2π·f·`loop_dc_choke_H`| / node_impedance
      (w_k = 0 이면 둘 다 None). ≫ 1 이면 choke 가 열린 것으로 본다.
    - 루프 정의 노출: `ac.loop_break_nets`(β 루프 = 끊은 넷, β=1 = 빈 목록), `ac.loop_weights`({넷: 가중} -- β 루프 = 끊은 넷
      가중, β=1 = 입력 넷의 AC 여기 진폭), 그리고 `compare.summary.pm_loop`(C12 보충).

### 구현하지 않은 것

* 엔진 쪽 ω → 0 극한과 오라클 fstart 값의 차이 보정: 정의상 기록 차(C27 기록)로만 둔다. 숫자 문턱을 두지 않는다.
* 공통 모드 루프·CMFB 루프 PM(7a design 7절 Q2), 명시 루프 뷰 `cut_weights`: 사용자 결정 전이라 입력 형식에 없다.

## [신규] C10 PM 안정성 근거 (2026-10-08, 결함: ngcc 프로브에서 PM 211.3 deg·free 판정 PASS 인데 폐루프 과도가 0.73 Vpp 지속 진동)

PM = 180 − (기준점 위상 − |L|=1 위상) 은 개루프 L 에 RHP 극이 없을 때(P = 0)만 안정 여유다. Nyquist: **Z = N + P**
(Z = 폐루프 RHP 극 수, N = 측정 L(jω) 곡선이 −1 을 **시계 방향**으로 감는 수, P = 개루프 RHP 극 수). 오라클은
**P 를 ngspice `.pz` 로 독립 측정**하고 N 을 측정 `.ac` 표본에서(위상 펼침 + 적응 세분화) 세어 Z 를 직접 구하며(사용자 결정 Q10,
2026-10-08), 폐루프 `.tran` 을 별도 증거로 같이 본다. **최종 안정성 판정(절차 8): 폐루프 과도 unstable(한계 사이클 포함) 또는 Z >= 1 이면
FAIL, Z = 0 이고 과도가 unstable 이 아니면 안정, 둘 다 결론을 못 내면 INCOMPLETE.**

### 방법 선택 (개정 2026-10-08, 사용자 결정 Q10)

* **[개정] ngspice `.pz` 채택.** 옛 기각 근거(2026-10-08 실측, smoke current_reuse_telescopic_ota 루프 넷리스트: 극 205 개 중 190 개가
  같은 값(−5.52e6 ± j1e8) 반복, +5.9e13 + j1e12 같은 가짜 RHP 극, 입력을 전압원 노드로 주면 극 0 개)은 두 가지 원인으로 갈린다.
  (1) **테스트벤치의 큰 L·C**: 1e12 H DC choke 와 1 F 결합 용량이 1e-12 ~ 1e11 rad/s 동적 범위를 만들어 근 찾기가 반복 한도에 걸린다
  (5T OTA 실측: 본 넷리스트에 `.pz` -> `Pole-zero iteration limit reached; giving up`, 가짜 극 9.99976 ± j1e8). 그래서 `.pz` 넷리스트는
  **동작점 패스 값으로 큰 L·C 없이** 만든다(절차 7) -- 같은 5T OTA 가 극 15 개를 정상으로 낸다(−1.30e6 rad/s 지배극 …).
  (2) **포트가 이미 전압원에 묶인 노드**: `.pz` 가 'input signal is shorted' 로 거부한다. 극점은 포트와 무관한 자연 주파수라 포트를 출력 노드의
  **전류 입력**(`pz <출력> 0 <출력> 0 cur pol`)으로 둔다(회로를 바꾸지 않는다).
  그래도 **`.pz` 는 큰 BSIM4 회로에서 근을 놓치거나 가짜 RHP 근을 낸다**(smoke 파일럿 forced, 소자 51 개: 경고 없이 RHP 극 23 개 -- 포트를 바꿔도 같은 값이 반복되는
  결정적 오답이고, 같은 회로의 400 ns 개루프 과도 `.tran` 에는 지수 증가가 없다). 그래서 **신뢰 규칙**을 둔다: (a) `.pz` 가 반복 한도·오류를 내거나 극을 못 내면 P = None('알 수 없음',
  0 으로 두지 않는다), (b) RHP 후보 극이 `.ac` 스윕 상한(2π·fstop) 밖이면(가짜 +5.9e13 형) P = None + `beyond_sweep` 기록, (c) 실수부는
  극 자신의 크기에 대한 상대 reltol 로 판정(`Re p > reltol·|p|`; 0 근처 극을 양으로 세지 않는다), (d) **폐루프 과도가 stable 로 정해졌으면 Z = 0, P_eff = −N 이 정확하다(Nyquist)** --
  `.pz` 는 판정에 쓰지 않고(설계 40 §4 C10 8), 어긋나면 `pz_conflict` 에만 적는다(Z·P_eff 를 비우지 않는다), (e) 폐루프 과도가 정해지지 않았으면(undetermined·failed) `.pz` 의 P >= 1 은 **개루프 과도 `.tran` 이 변위의 증가를
  보일 때만**(`pz.validated`, 절차 7) 판정에 쓴다 -- 확인 못 하면 INCOMPLETE. (정직한 한계: 이 규칙은 사용자 결정 Q10 의 'Z >= 1 이면 FAIL' 에서 `.pz` 오답이 안정 회로를 FAIL 시키는 것을
  막으려고 둔 것이다. 폐루프 과도가 stable 인데 실제로는 불안정한 회로(킥이 그 모드를 못 들뜨게 함)는 FAIL 이 아니라 stable 로 남는다.)
* **측정 L(jω) 만으로는 P 를 셀 수 없다**: 편각 원리로 얻는 것은 차(Z − P, 또는 RHP 극 − RHP 영점)뿐이다. 그래서 P 는 `.pz`, N 은 `.ac`.
* 폐루프 `.tran` 은 사용자가 결함을 확인한 방법과 같고, `.pz`/Nyquist 가 못 보는 비선형 한계 사이클(포화로 진폭이 묶이는 진동)을 본다.

### 절차(`oracle_simulate.stability_check`, PM 원값이 있을 때만 -- 없으면 `ac.stability.reason` 에 '검사 대상 아님')

1. 루프와 닫기 부호: β 루프(feedback_passives 있음)면 L = 측정 T(실제 루프, 회전 없음). β=1 이면 L = sign·A,
   sign = 기준점(fstart) Re A 의 부호(PM 정의가 기준점 위상을 0 으로 보는 것 = 기준점에서 음되먹임으로 닫는 것).
   Re A(fstart) = 0 이면 닫기 부호를 정할 수 없어 N = None, 과도 안 돌림. `ac.stability.loop`, `closure_sign`.
2. **N**(`nyquist_count`, `nyquist_adaptive`): 닫힌 곡선 = 켤레 반쪽(ω: −f_last → −f_first) + 측정 반쪽(f_first → f_last), 두 끝은 직선.
   N = −(1+L 편각 변화 합)/2π(표본 사이 변화는 ±π 로 접음 = 위상 펼침). 유효 조건(아니면 N = None + `reason`):
   (a) |L(f_last)| < 1 -- 스윕 위 꼬리가 −1 을 감을 수 없다(측정 정의의 UGF 와 같은 가정, 스윕 상한 부족이면 실패),
   (b) 두 닫는 직선을 포함한 모든 표본 간격에서 1+L 편각 변화 < 90 deg(π/2) -- 접기 모호성(180)의 절반 여유, (c) L = −1 인 표본 없음.
   **[개정 Q10] 적응 세분화**: (b)를 어기는 양의 주파수 구간(`nyquist.bad_intervals_hz`)이 있으면 그 구간을 (로그) 이분하는 점을 `ac dec` 로
   다시 잰다(`refine_samples`: 원래 L 을 만든 넷리스트의 `ac` 줄 구간·밀도와 `wrdata` 파일 이름만 바꿔 다시 돌림 -- β=1 은 본 넷리스트, β 루프는
   Middlebrook 두 `ac` 둘 다) -> 합쳐 다시 센다. 최대 `NYQUIST_K_MAX` = 10 라운드(한 라운드가 구간을 이분 = 1024 분할; 그래도 π/2 를 넘으면 L 이 −1 을
   극히 가까이 지나는 특이 구조라 N 미정). 두 닫는 직선(저주파·고주파 끝)의 큰 간격은 표본을 더할 수 없어 그대로 N = None.
   기록 `ac.stability.nyquist = {encirclements_cw, reason, max_step_deg, max_step_hz, bad_intervals_hz, closing_step_deg, f_first_hz,
   f_last_hz, L_first, L_last, refinement{rounds, samples_added, k_max, history}}`. 플랜·f_crit 은 **세분화 전** 원래 스윕 표본으로 정한다.
3. **폐루프 과도 넷리스트** `<stem>.stab.cir`(`oracle_netlist.stability_netlist`, 원 넷리스트의 .control 앞 본문에서 만든다):
   - **자극·관측 위치 = 루프 끊는 점**(설계 40 §4 C10 8 '자극 위치'): 킥도 관측 H 도 끊는 점에 둔다(출력 노드 관측 아님 -- 그 루프의 폐루프 극이 끊는 점에서 들뜨고 관측된다).
     관측 H = 가중이 있는 끊는 점 노드 전압의 가중치 부호 합(`plan.observe = [[노드, 부호], ...]`; 노드 하나면 `v(노드)`): β=1 은 루프를 닫는 입력 넷의 노드(`Ecl_` 이 구동), β 루프는 절단 넷의 증폭기 쪽 노드(`Vlb_` 직렬원 옆).
     개루프 과도 확인(절차 7, 입력이 전압원에 묶임)만 출력 노드를 본다.
   - β 루프: 루프 넷리스트 그대로(Vlb = 0 이면 실제 폐루프), 끊은 넷 k 의 `Vlb_<넷>` 을 `DC 0 PULSE(0 w_k·kick ...)` 로.
   - β=1: 본 넷리스트에서 입력 넷마다 그 넷의 테스트벤치 원(`Cac_ Vac_ Vdc_ Ldc_ Efb_ Vofs_ Lfb_`)을 빼고
     `Ecl_<넷> <넷> ecl_<넷> <출력 p> <출력 n 또는 0> g` + `Vcl_<넷> ecl_<넷> 0 PULSE(V0 V0+w_k·kick ...)`,
     g = −sign·w_k, V0 = V_op(넷) − g·H_op(H = 출력 차동/단일 전압, H_op = 동작점 패스 값). 입력 AC = −sign·w_k·H 라 루프 이득 =
     sign·A, H = H_op 에서 본 동작점과 같다(결합 C 1 F 를 이상 VCVS 로 구동하면 큰 진동에서 'Timestep too small' -- 실측).
   - 남은 테스트벤치 choke(`Lfb_ Ldc_ Lhold_ <tb 노드> <회로 노드> L`)는 `Itb_<choke 이름> <tb 노드> <회로 노드> DC <I_op>`
     + `.ic v(<회로 노드>)=<V_op>`. I_op·V_op = **동작점 패스** `<stem>.stabop.cir`(같은 본문 + `op` + choke 마다
     `print i(<choke>)`, 입력·출력·choke 회로 쪽·절단 양쪽 노드 `print v(..)`, `oracle_netlist.stability_op_netlist`)의 값 -- 본·루프
     넷리스트 텍스트는 바꾸지 않는다. 기록 `ac.stability.transient.op_pass = {netlist, ngspice_rc, choke_current_A,
     node_V}`. β=1 의 V_op(입력)·H_op 도 이 패스 값이다. uic 없는 .ic 는 바이어스 해에서만 노드를 묶고 t > 0 에서 푼다 -- 과도 중 전류가
     얼어 있는 이상 choke 와 같다(1e12·1e20 H 를 그대로 두면 .tran 이 멈춤, 1e8 H 는 성공 -- 실측). 이 패스는 `.pz`(절차 7)도 같이 쓴다.
   - **[개정 조기 종결 계약 1(b)(d), d56ba66] `.control` 은 창 단위 실행**(`oracle_netlist.stability_control`): `.save v(<H 식 피연산자>)`
     (+ time) 만 저장(전체 벡터 저장 안 함 -- 메모리 오류 완화), `set numdgt=8`(wrdata 가수 9 자리 = 파일 반올림 반 단위 u = 5e-9 를 .control 과 파이썬이
     같은 값으로 쓴다), `stop when time > <창 j 끝>` -> `tran` 이 멈추면 창 j 의 M_j = max|H − H(0)| 를 계산해 로그에 **`STABWIN j M_j`** 한 줄을 쓰고,
     조기 기준(절차 5)을 충족하면 즉시 `wrdata` 하고 끝, 아니면 `delete all`(끝난 조건을 지우지 않으면 resume 이 같은 조건에서 곧바로 다시 멈춘다 -- 실측)
     + 다음 `stop when` + `resume`. (계약 문안의 `time >= x` 는 ngspice 가 `>=` 를 받지 않아 `>` 로 썼다 -- 경계를 처음 넘은 표본에서 멈추고 그 표본은 창 j 밖.
     ngspice 명령 줄의 `>`·`<` 는 출력/입력 리다이렉션이라 `let x = (a > b)` 가 **조용히 틀린다 -- 실측**: 스크립트 안 비교는 `>=` 만, 한 줄에 하나씩
     `let x = (a >= b)`.) 데이터 파일 `<stem>.stab.txt` 는 멈춘 시각까지 쓴다. 마지막 시각이 창 끝에 못 닿으면(ngspice 가 중간에 죽음) 더 돌리지 않고 파일만 쓴다.
4. **과도 계획**(`tran_plan`, 조정 상수 없음 -- 측정 L 과 입력에서 유도): f_lo/f_hi = 가장 낮은/높은 |L|=1 교차
   (`gain_crossings_hz`, log 보간), kick = V_T = k_B·T/q(T = LUT temp_c + 273.15 K; 소신호 선형화의 물리 척도).
   **시간 척도 f_lo**: td = tr = tf = pw = 1/(2π f_lo), 킥 끝 t_end = td + tr + pw + tf, 창 W = 1/f_lo (f_lo = PM 을 정의한 교차).
   **[개정 조기 종결 계약 1(a)] 걸음 상한 tmax = min(1/(2π f_lo), 1/(f_crit·n_pp))**:
   * f_crit = **불안정 관련 대역** 안에서 |1+L| 이 최소인 표본의 주파수(`band_f_crit`). 대역 = 스윕 첫 표본부터 **가장 높은 |L|=1 교차를 지난 첫 표본**까지(닫기
     부호 반영 L). 근거: Nyquist 에서 |L| < 1 인 꼬리는 −1 을 감지 못한다 -- 꼬리에서는 |1+L| → 1 이라 argmin 이 스윕 끝(1e10 Hz)에 붙는다.
   * n_pp = ceil(π / arccos(1 − reltol)) (`n_pp_of`; reltol = 입력 `testbench.options.reltol`, 없으면 ngspice 기본 1e-3 -> 71, 1e-4 -> 223).
     유도: 표본 간격 Δ = 주기/n 일 때 정현파 봉우리를 놓치는 최대 상대 오차 1 − cos(π/n) 가 reltol 이하인 최소 n.
   * f_hi 는 계획에 쓰지 않는다(기록만). 옛 tmax = 1/(2π f_hi) 는 교차가 많은 L 에서 끝나지 않았다(two_stage_ota_sf 시작점 59 교차 0.48 Hz ~ 9.5 GHz,
     tmax 1.7e-11 s·tstop 14.9 s, ~8.8e11 걸음). f_crit 이 f_lo 근처면 tmax 는 옛 값과 같다(min 이 f_lo 항).
   창 수 K = ceil(ln(kick/floor)), floor(해 분해능) = **관측 노드(루프 끊는 점)**마다 reltol·|V_op| + vntol 의 합(V_op = 동작점 패스 값)(ngspice 기본 reltol 1e-3·vntol 1e-6),
   tstop = t_end + K·W. kick <= floor 이거나 K < 2 면 계획 없음(과도 `not_run`). 기록 `ac.stability.transient.plan` = {kick_V, td, tr, pw, tmax,
   window_s, windows, **windows_planned**, t_kick_end, tstop, f_lo_hz, f_hi_hz, **f_crit_hz, n_pp, reltol, wall_cap_s**, floor_V, sign, observe}.
   **[개정 계약 1(c)] 기본 시간 상한**: 설정 `oracle_config.json` 의 `stability_transient.wall_s_per_window`(창 하나를 끝내는 ngspice 실행 시간 상한) x 창 수.
   `plan.wall_cap_s` = wall_s_per_window × K, 연장 실행은 `extension.wall_cap_s` = wall_s_per_window × (K + n)(n = extension_windows; 연장은 K+n 창을 처음부터
   다시 돌린다). 적용 상한 `transient.wall_cap_s` = `--timeout-s` 가 있으면 그것(사용자 지정 우선), 없으면 `plan.wall_cap_s`. 동작점 패스·`.pz`에는 이 상한을 쓰지
   않는다(`--timeout-s` 가 있을 때만, `.pz` 는 없으면 wall_s_per_window 1 회분). 끊기면(`subprocess.TimeoutExpired`) 또는 ngspice 가 치명 오류로 tstop 에 못
   닿으면 `failed`(사유 '과도 시간 초과'/'과도가 tstop 까지 가지 않았다') -> '모름' -> PM 정의 불가 -> PASS 불가. **이 경로는 `unstable` 이 아니다**(진동을 확인한
   것이 아니므로). 안정성 근거의 세 실행은 `TimeoutExpired` 를 잡는다(`_run_stab`): 끊기면 죽지 않고 그 실행 기록에 `timeout` 을 남긴다.
   `oracle_config.json` 의 값은 `measured_*`·`safety_factor`·`justification` 으로 근거를 같이 둔다(`smoke/measure_wall_s_per_window.py` 로 잰다).
5. **과도 판정**(`transient_decision`, **분해능 인식형**): e(t) = H(t) − H(0), 창 j = 1..K(t_end 부터 W 씩)의 M_j = max|e| (창 끝까지 표본이 닿은 창만),
   floor' = floor + u·max|H|(u = .stab.txt 반올림 반 단위, C20 의 data_rel_resolution), reltol = `plan.reltol`.
   g↑(a,b) := b(1 − reltol) > a(1 + reltol) + floor' (b 가 a 보다 측정 분해능을 넘게 큼), g↓(a,b) := a(1 − reltol) > b(1 + reltol) + floor'. (M_j 는 표본
   봉우리라 상대 오차 <= reltol, 절대 분해능 floor' -- 두 창의 측정 불확실 구간이 겹치지 않을 때만 커졌다/작아졌다고 인정.) 순서대로:
   * **조기 종결**(끝난 창들에서 첫 j >= 3): (growth) g↑(M_{j−2},M_{j−1}) 그리고 g↑(M_{j−1},M_j) 그리고 g↑(M_1,M_j) -- 엄격한 연속 증가;
     (**limit_cycle = 감쇠하지 않음, 사용자 결정 2026-10-09**, 설계 40 §4 C10 8 이 2 의 '분해능 안 일정'을 대체) 창 j−1 과 창 j 가 둘 다 **감쇠하지 않음**:
     nd(j) := M_j(1−reltol) > floor'(바닥 위; 해 분해능 바닥에 붙은 안정 회로의 창은 진동이 아니다) 이고 g↓(M_{j−1},M_j) 아님(앞 창보다 분해능 이상 줄지 않음).
     출렁이는 지속 진동(rb1e6형)·증가도 포함한다. 창마다 분해능 이상 계속 줄면(slow decay) 이 기준에 걸리지 않고 판정을 이어 간다. 충족하면 `status = unstable`, `early_stop = {window, M[1..j], reason, kind}`, `windows_run = j`, 연장 없음.
     순수 함수: `early_unstable(M, floor', reltol)` = growth 만(엄격 증가가 아닌 감쇠하지 않음은 False), `limit_cycle_early(...)` = limit_cycle 만, `early_window` = 둘 중 첫 창.
   * 조기가 아니고 마지막 시각이 tstop·(1 − 2u) 보다 이르면 `failed`.
   * M_K <= floor' -> `stable`; g↑(M_1, M_K) -> `unstable`; 모든 연속 창 g↓ -> `decaying`; 그 밖(분해능 안의 같음 포함) -> `undetermined`.
   **감쇠하지 않는 지속 진동 = 불안정(한계 사이클)이다**(사용자 결정 4, 2026-10-08; 2026-10-09 에 '일정 진폭'에서 '감쇠하지 않음'으로 넓혔다). 이 판정은 고Q 로 창당 감쇠가 분해능보다 작은 **안정** 회로와
   K 창 안에서 구별되지 않는다 -> 보수적으로 `unstable(limit_cycle)` -> FAIL 이고, 대신 `transient.limit_cycle_vs_slow_decay_unresolved = {M[1..j], window_ratios, floor_V,
   reltol, reason}` 를 `ac.stability` 에 올리고 비교표 맨 앞에 찍는다(사용자가 이 FAIL 이 판정 한계에서 나왔을 수 있음을 알아보도록).
   **안정 판정 불변 조건**: 안정(`stable`/`decaying` -> `stable`)인 모든 test 회로·fixture 에서 조기 기준(growth·limit_cycle)이 한 번도 충족되지 않는다
   (창 변화비가 e 이하로 감쇠 -- 측정 기록: 아래 '확인').
   - `decaying` 이면 **연장 실행** `<stem>.stab2.cir` / `.stab2.log` / `.stab2.txt`(같은 킥·같은 창, 같은 동작점 패스 값, 같은 `.control`):
     마지막 창 감쇠비 r = M_K/M_{K−1} 의 기하 감쇠로 floor' 에 닿는 창 수 n = ceil(ln(floor'/M_K)/ln r) 만큼 늘린다
     (창 수 K + n, tstop = t_end + (K + n)·W). 연장 실행을 같은 규칙으로 판정해 `stable` 또는 `decaying` -> 최종 `stable`, `unstable` -> `unstable`, 그 밖
     (`undetermined`·`failed`) -> `undetermined`.
   - 첫 실행이 `decaying` 이 아니면 그 상태가 최종이다(연장 없음, `.stab2.*` 없음).
   기록 `ac.stability.transient = {status(최종), first_status, reason, M(첫 실행), floor_V, plan, op_pass, netlist, file, ngspice_rc, **windows_run, wall_cap_s,
   early_stop{window, M, reason, kind}(조기일 때), limit_cycle_vs_slow_decay_unresolved(limit_cycle 일 때), timeout(끊겼을 때)**, extension{... wall_cap_s}(연장했을 때만)}`.
6. **추론(P 를 모를 때의 옛 표, `_judgement_legacy`)**: `.pz` 가 못 믿을 때(P = None) N + 과도로 P 를 추론한다. pm_raw = Bode 식 원값.
   폐루프가 불안정(S unstable 또는 N >= 1)이고 N >= 1 일 때 P = 0(Z = N)과 맞는 Bode 결과는 PM < 0 이다 -- 이때 PM 값을 유지하고 pm 제약은 이전처럼 FAIL.
   PM >= 0 이면 증거 충돌 -> `stability_evidence_inconsistent`.

| S | N | pm_raw | `closed_loop` | `open_loop_rhp_poles`(`_bound`) | PM | `pm_undefined` |
|---|---|---|---|---|---|---|
| stable | 0 | 아무 값 | stable | 0 (`==`) | **값 유지** | None |
| stable | < 0 | 아무 값 | stable | −N (`==`) | None | `open_loop_rhp_poles` |
| stable | > 0 | 아무 값 | stable | None | None | `stability_evidence_inconsistent` |
| stable | None | 아무 값 | stable | None | None | `nyquist_count_unavailable` |
| unstable | <= 0 | 아무 값 | unstable | 1 − N (`>=`) | None | `open_loop_rhp_poles` |
| unstable | >= 1 | < 0 | unstable | 0 (`== (Z = N 과 일치)`) | **값 유지(음수)** | None |
| unstable | >= 1 | >= 0 | unstable | None | None | `stability_evidence_inconsistent` |
| unstable | None | 아무 값 | unstable | None | None | `closed_loop_unstable` |
| 모름 | >= 1 | < 0 | unstable | 0 (`== (Z = N 과 일치)`) | **값 유지(음수)** | None |
| 모름 | >= 1 | >= 0 | unstable | None | None | `stability_evidence_inconsistent` |
| 모름 | < 0 | 아무 값 | None | −N (`>=`) | None | `open_loop_rhp_poles` |
| 모름 | 0 또는 None | 아무 값 | None | None | None | `stability_unverified` |

7. **P = 독립 `.pz`**(`pz_check`, `oracle_netlist.open_loop_parts`·`pz_netlist`, 사용자 결정 Q10): 동작점 패스(절차 3)의 V_op·I_op 로 **큰 L·C 없는** 개루프 넷리스트
   `<stem>.pz.cir` 를 만든다: 입력 넷의 테스트벤치 사슬(`Cac_ Vac_ Vdc_ Ldc_ Efb_ Vofs_ Lfb_ Vlb_ Ilb_`)을 빼고 입력 노드를 `Vpz_<넷> <노드> 0 DC V_op`(AC 단락)로
   구동, 남은 choke(Lhold_)는 `Itb_ ... DC I_op` + `.nodeset`. β 루프(`dm`): 절단 양쪽(증폭기 쪽 n 과 되먹임 망 쪽 `lbx_<넷>`)을 모두 V_op 의 이상 전압원으로 구동한다(Vlb·Ilb 제거;
   닫힌 루프에서 n 은 가상 접지라 되먹임 소자의 반대편이 AC 접지에 놓이는 부하와 같고, 용량만 물린 lbx 를 띄우면 `.pz` 가 'singular matrix' 로 실패 -- 파일럿 실측).
   CM 루프(`cm`): 소비자 쪽 lbx 를 V_op 로 구동하고 구동자 쪽(출력)은 둔다. `.control`: `op`, `pz <출력> 0 <출력> 0 cur pol`(입력 포트가 전압원에 묶인 노드는 `.pz` 가 거부 --
   극점은 포트와 무관), `print all`. 극점 파싱(`pz_poles`)·RHP 개수(`pz_rhp_count`)로
   `ac.stability.pz = {status ok|failed|unavailable, P, rhp, beyond_sweep, n_poles, poles(상위 40), reason, netlist, ngspice_rc, method, open_loop, validated, validation}`.
   **개루프 과도 확인**(`pz_validate`, 폐루프 과도가 정해지지 않고 P >= 1 일 때만): 같은 개루프 본문(`.nodeset` 대신 `.ic`)에 출력 노드 하나의 초기 변위 `.ic v(<출력>) = V_op + V_T`
   (uic 없는 `.ic` 는 바이어스 해에서만 그 노드를 묶고 t > 0 에서 푼다 = 풀려 나가는 과도)를 주고 같은 창 계획(K 창, t_kick_end = 0, 기준 = 동작점 H)과 같은 판정 규칙
   (`transient_decision`)으로 돌린다 -> `pz.validated` = True(unstable: 변위 증가 또는 일정 진폭 지속) / False(stable·decaying) / None(undetermined·failed·시간 초과).
   파일 `<stem>.pzv.cir/.log/.txt`, 캐시 상태는 `sim.stability_cache.pz_validation`. 시간 예산: 확인에는 과도가 쓰고 남은 계획 상한(`plan.wall_cap_s` − 과도 시간)을 주되 최소 창 하나 몫(`wall_s_per_window`)은 보장한다(`--timeout-s` 가 있으면 그것) --
   증가하는 회로는 창 3 안에 확인되어 짧다. 끊기거나 판정 못 하면 `pz.validated` = None.
   (RHP 극은 능동 증폭기 내부(국소 양되먹임)에서만 나오고 수동 β 망은 RHP 극을 만들지 않는다.)
8. **최종 안정성 판정**(`stability_judgement`, 사용자 결정 Q10 + 결정 B·4): `verdict` =
   * `unstable`: 폐루프 과도 unstable(limit_cycle 포함) **또는** N >= 1 (P >= 0 이라 Z >= N >= 1) **또는** Z = N + P >= 1 이고 P 가 쓸 수 있음(위 신뢰 규칙: 과도 unstable 이거나
     `pz.validated`);
   * `stable`: 폐루프 과도 stable (`verdict_basis` = transient+nyquist: Z = 0, P_eff = −N. `.pz` 는 쓰지 않고 −N 과 다르면 `pz_conflict` 만 기록);
   * `undetermined`: 그 밖 -- 둘 다 결론을 못 낸 경우(INCOMPLETE). Z = 0 이라도 과도가 안 정해졌으면 Nyquist 만으로는 안정이라 하지 않는다(P = 0 은 `.pz` 가 근을 놓치지
     않았다는 가정에 기댄다).
   P_eff(쓸 수 있는 P)가 정수면 PM 유효성은 옛 추론표 대신: P_eff = 0 이고 verdict stable -> PM 값; P_eff = 0 이고 unstable -> N >= 1 & pm_raw < 0 만 값(Z = N 과 일치), 그 밖
   `stability_evidence_inconsistent`; P_eff >= 1 이고 Z = 0 이고 안정 -> **조건부 안정**(`conditionally_stable`, PM 원값을 값으로 둠 -- 개루프 RHP 극이 있어도 폐루프 안정이면
   합격 가능; 단 이 PM 은 Bode 식 원값이라 안정 여유의 의미는 N + P 로 확인한 것); P_eff >= 1 그 밖 -> `open_loop_rhp_poles`; Z < 0 -> `stability_evidence_inconsistent`.
   P_eff 를 모르면 옛 추론표(절차 6).
   **조건부 안정과 하측 이득 여유**(설계 40 §4 C10 8): verdict stable 인데 교차 주파수 아래 |T| > 1 구간에서 위상이 −180° 를 넘는 곡선(L 이 음의 실축을 x < −1 에서 지남)은 P = 0 이어도
   `conditionally_stable = True` 로 표시하고(`pm_valid` 유지, PM = 모든 |T| = 1 교차의 최솟값), **`low_side_gain_margin_db`** = 20·log10(min|x|)(루프 이득을 이만큼 줄이면 −1 이 그 교차에 놓여
   감김 수가 바뀐다; 같은 `.ac` 표본에서 `low_side_gain_margin(freq, L)`, 표본 사이 선형 보간) 을 `ac.stability` 와 `summary.stability` 에 보고한다(`low_side_crossings`·`low_side_crossing_hz` 포함).
   spec 값이 없으므로 제약이 아니라 보고다(verdict 는 PASS 그대로).
   `pm_valid` = (pm_undefined 가 None). 정의 불가면: `ac.pm_deg = None`, `ac.pm_undefined = <이유>`, `ac.pm_deg_raw` = 원값(유효해도 `pm_deg_raw` = `pm_deg`), β=1 이면
   `ac.pm_open_loop_deg = None`(같은 양), C20 교차 측정은 PM 이 아니라 `pm_crosscheck_deg = None`(원값 `_raw`).
   기록 `ac.stability.{closed_loop, open_loop_rhp_poles(_bound), pm_valid, pm_undefined, verdict, verdict_basis, Z, P_pz, P_eff, pz_conflict, conditionally_stable, low_side_gain_margin_db}`.
9. compare: pm_deg 제약·metric 판정 칸 `N/A(정의 불가: <pm_undefined>)`, 제약 행 `undefined` 칸 = 같은 이유(C26 rout 과 같은 경로 `measure_undefined`).
   **[신규 U6] `verdict == unstable` 이면 pm 제약이 있든 없든 free verdict = FAIL**(사유 '폐루프 불안정(Z, 과도, 근거)'; `summary.acceptance.closed_loop_unstable`).
   `summary.stability = {pm_valid, pm_undefined, pm_deg_raw, loop, closed_loop, open_loop_rhp_poles(_bound), nyquist_encirclements_cw, nyquist_reason,
   nyquist_refinement_rounds, pz_status, pz_P, pz_reason, Z, verdict, verdict_basis, conditionally_stable, transient_status, transient_reason, early_stop,
   limit_cycle_vs_slow_decay_unresolved, reason}`(PM 원값이 없으면 `pm_valid` None + reason), Markdown 에 `- C10 PM 안정성 근거: ...` 한 줄과(limit_cycle 일 때) 맨 앞
   `limit_cycle_vs_slow_decay_unresolved` 줄(`summary.limit_cycle_vs_slow_decay_unresolved` 최상위 키에도 같은 값). free·forced(진단) 모두 같은 검사를 한다(forced verdict 는 C8 대로 INCOMPLETE). iso 는 AC 가 없어 해당 없음.

### 한계(판정 안에서 드러나는 것은 fail-closed)

* 스윕 밖: f < fstart 의 L(기준점을 DC 로 보는 오라클 관례)과 f > fstop 꼬리(|L(fstop)| < 1 만 확인)는 보지 않는다.
* 과도는 끊는 점(β 루프 절단 넷 / β=1 입력)에서 자극하고 관측한다 -- 그 루프의 폐루프 극은 끊는 점에서 들뜨고 관측되지만, 다른 루프 뷰(예: DM 루프 과도로 CM 모드)의 불안정은 그 루프 뷰가 따로 본다. 킥이 거의 안 들뜨게 하는 모드는 놓칠 수 있다 -- `.pz` P 는 판정에 쓸 수 있을 때만 별도 증거다.
* `.pz` 는 큰 BSIM4 회로에서 근을 놓치거나 가짜 극을 낼 수 있다(위 방법 선택). 가짜 극은 (b)로 거르고, 놓친 극은 Z 를 낮게 보이게 하므로 **Z = 0 은 과도와 함께** 읽는다.
  P 를 못 믿으면 P = None 이라 옛 표로 돌아가 N + 과도로만 판정한다.
* 'unstable' 은 Z >= 1 만 안다(Z 의 개수는 모름). P 를 못 쓸 때 P 는 하한(`>=`)만 낸다.
* 감쇠하지 않는 지속 진동의 한계 사이클 판정은 고Q 안정 회로와 구별되지 않는다(위 `limit_cycle_vs_slow_decay_unresolved`). 창 진폭이 분해능 밖으로 출렁이는 이완 진동(rb1e6형)은
  2026-10-09 부터 한계 사이클이다. 앞 창보다 줄었다가 늘어나는 맥놀이([1, 0.5, 1.2])처럼 최근 두 창이 연속으로 '줄지 않음'이 아닌 경우는 여전히 `undetermined` 이다 -- 이때 `.pz` P >= 1 이 개루프 과도로 확인되면 FAIL, 아니면 INCOMPLETE.
* 고전적 불안정(P = 0, PM < 0, 예 nmcnr_amplifier 프로브 PM −49.4 deg)은 PM 값이 남고 pm 제약은 이전처럼 FAIL 이며 안정성 판정도 FAIL 이다.

### 확인(2026-10-08, ngspice-46 sky130 tt, 기록 -- test 아님)

* 손으로 쓴 독립 회로(개루프 RHP 극을 알고 있음): nin -> M1(CS, R1 115 kΩ) -> n1 -> M2(CS, R2 100 kΩ) -> n2(출력), n2 -Cc 1 pF-
  n3(Rb 1 MΩ 로 0.7 V 레일) -> M3(드레인 n1) = DC 를 막은 양되먹임. 손 .op(gm·gds) 모형 A = A0(1+sτ)/(1+sτ(1−K)),
  A0 = 21.7, K = 178.6, τ = 1 µs -> RHP 극 p = 1/(τ(K−1)) = 5630 rad/s; 독립 개루프 .tran(입력 고정, n3 에 1 pA·1 µs 킥)의
  지수 증가율 5619 rad/s(0.2 %), 독립 폐루프 .tran(이상 단위 되먹임) 0.86 V 로 포화. 옛 오라클: PM 274.5 deg, pm_deg >= 60
  제약 **PASS**. 새 오라클: `.pz` 가 RHP 극 둘을 낸다(Rb 100 kΩ 판 5.12e4 rad/s 와 6.19e9 rad/s(0.99 GHz), Rb 1 MΩ 판 5.09e3 rad/s(손 모형 5.63e3 의 ±10 %)와 6.33e9 rad/s -- 같은
  양되먹임이 GHz 대에서도 루프 이득 > 1 인 증거이고 rb1e7 의 GHz 버스트가 이것이다), Rb 100 kΩ 판은 폐루프 과도가 한계 사이클(창 4 에서 일정 진폭 조기 종결)이라 free verdict FAIL,
  Rb 1 MΩ 판은 과도가 undetermined(이완 진동, M 이 분해능 밖으로 출렁임)지만 개루프 과도가 변위 증가를 확인해(`pz.validated`) Z = 0 + 2 >= 1 로 FAIL. 제약은 `N/A(정의 불가: open_loop_rhp_poles)`.
* **`.pz` 오답 실측**: smoke 파일럿(current_reuse_telescopic_ota forced, 소자 51 개)은 `.pz` 가 경고 없이 RHP 극 23 개(3.9e6 ± j5.1e6 rad/s ... 1e9)를 낸다 -- 출력 포트를 바꿔도 같은 값이 반복되는 결정적 오답이고,
  같은 개루프 회로의 400 ns `.tran`(출력에 킥)에는 지수 증가가 없다. 폐루프 과도는 stable(창 변화비 ~1e-2 ~ 1e-3)이므로 판정은 stable(`pz` 무시)이다(절차 8).
* ngcc_3stage_ff 프로브(β=1, free·forced): 원값 211.3 / 211.6 deg -> N = 0, 과도 unstable -> `open_loop_rhp_poles`.
  nmcnr_amplifier·two_stage_ota_sf 프로브: N = 2, 과도 unstable, PM −49.4 / −23.7 deg -> P = 0 과 일치, PM 값 유지(제약 FAIL).
* 안정 회로(값 불변 확인, 옛·새 오라클 비교에서 `pm_deg`·`pm_open_loop_deg`·`pm_crosscheck_deg`·`gap`·`ugf_hz`·`dc_gain_db`·
  `loop_ugf_hz` 비트 동일): test 회로 tcs_nmos_rload(94.22), tfb_cs_rfeedback β 루프(58.21), 같은 회로 β=1(94.87),
  Cin 1 pF(34.10), two_stage_ota 프로브 free 7.70 / forced 7.20, smoke current_reuse_telescopic_ota 차동 β 루프 forced
  (sizing 90.01, layout 50.77) -- 전부 N = 0, 과도 stable, PM 그대로.
* U6 조기 종결·`.pz` 구현 후 같은 fixture 판정 비교는 `smoke/U6_REPORT.md`.

## [신규] U6 -- `.noise` 대조, offset Monte-Carlo, 스윙·ICMR 스윕 (2026-10-08, 설계 40 §4·§10.2·§11 U6, 41 §7.6, 사용자 결정 Q3·Q4·Q11)

세 측정 모두 **입력 JSON 에 해당 블록이 있을 때만** 돈다(없으면 sim 에 키가 없고 기존 출력은 바뀌지 않는다). free 모드에서만 돌고(`oracle_run.run_one`), 엔진을 import 하지 않는다.
결과는 `sim.noise` / `sim.offset_mc` / `sim.swing_icmr` 와 `compare.summary.u6`, 비교표(Markdown)의 `U6 ...` 줄로 나온다. 새 measure 이름은
`acceptance.constraints[].measure`·`predictions.metrics[].measure` 에 쓸 수 있고(`noise_th_in_v2hz, noise_fc_in_hz, noise_excess_th, noise_out_int_vrms, offset_in_sigma_mv,
swing_out_v, icmr_v, icm_margin_v`), 제약은 `>=`/`<=` 로 판정하며 값이 없으면 `N/A(SPICE 값 없음)` 또는 `N/A(정의 불가: <이유>)` -> INCOMPLETE(PASS 불가).
엔진 예측과의 차이(`predictions.metrics`)는 다른 metric 과 같이 기록만 한다(`judge.tolerances.<measure>_rel|_abs` 키, DEC-72 의 `model_error_*` 재료).

### 입력 블록 (스키마 `noise`, `offset_mc`, `swing_icmr`)

| 블록 | 필드 | 뜻 |
|---|---|---|
| `noise` | `f_lo_hz`(필수) | 열잡음 평탄값 평가·적분 하한(엔진 LUT 가 실측한 가장 낮은 잡음 점 -- 외삽 안 함) |
| | `points_per_decade` | 주파수 격자 밀도(기본 `testbench.ac.points_per_decade`) |
| | `input_cell_devices` | `noise_excess_th` 분모(입력 셀) 소자 이름 목록 |
| | `closed_loop` | true 면 feedback_passives 로 닫은 루프 넷리스트에서 `noise_out_int_vrms` 를 잰다 |
| | `rel_resolution` | 적분 꼬리 판정의 상대 분해능 r(기본 = ngspice reltol) |
| `offset_mc` | `rel_resolution`(필수) | 목표 상대 표준오차 r(엔진 offset resolution). N = ceil(1 + 1/(2 r²)) |
| | `seed`, `max_samples` | 난수 시드(기본 0, 결과에 기록), 표본 수 상한(넘으면 `n_capped`) |
| `swing_icmr` | `swing`, `icmr` | 어느 스윕을 할지 |
| | `input_dc_V`, `input_dc_pending` | `icm_margin_v` 용 선언 입력 DC (없으면 예측 입력 DC); pending 이면 `icm_margin_v` 를 내지 않고 `input_dc_pending` 으로 보고(SP-2 대기) |

### `.noise` (`oracle_noise.py`)

* **개루프**(`noise_th_in_v2hz`, `noise_fc_in_hz`, `noise_excess_th`, `noise_contrib`): free 본 넷리스트에서 주파수 f 마다 `ac lin 1 f f`(차동/단일 AC 이득 H) +
  `noise v(out[,out_n]) <Vac_..> lin 2 f f(1+δ) 1`(δ = reltol) 을 한 번의 ngspice 실행으로 이어 돌려, `print all` 의 소스별 합계(ngspice 는 sqrt(∫S df) [V] 를 낸다)에서
  S_k(f) = v_k²/Δf 를 얻고 입력 환산 S_in(f) = Σ_k S_k(f)/|H(f)|² 를 만든다. 열 성분 = `1overf` 가 아닌 모든 소스(MOS `.id .rd .rs .rg .rb* .ig*`, 저항 thermal),
  flicker = `1overf` 소스(MOS `.1overf`, 저항 `_1overf`).
  * `noise_th_in_v2hz` = 열 성분 입력 환산 합의 f_lo 값(저주파 평탄 영역 -- 엔진 정의 Σ|Z_k/H|² gm_k² B_k 와 같은 양).
  * `noise_fc_in_hz` = 입력 환산 flicker 합이 `noise_th_in_v2hz` 와 같아지는 주파수: f_lo 부터 격자를 올려 첫 교차를 로그-로그 보간. f_lo 에서 이미 아래면 None +
    `fc_reason = below_f_lo`, `testbench.ac.fstop_hz` 까지 못 만나면 None + `above_cap`.
  * `noise_excess_th` = `noise_th_in_v2hz` / (`input_cell_devices` 소자만의 열 성분 합). 입력 셀이 없으면 None + `excess_reason`. 소자 이름은 오라클 넷리스트 이름으로 사상해 찾는다
    (`oracle_noise.oracle_element_names`: MOS `M1a` -> `m1a`, 수동소자 `RL` -> `rp_rl`·`cp_rl`·`isrc_rl`·`vsrc_rl` -- `oracle_netlist.CIRCUIT_PREFIXES` 접두; 못 찾은 이름은 `input_cell_missing`). **fail-closed**: 선언 이름 중 하나라도 못 찾으면(`input_cell_missing` 비어 있지 않음) 찾은 부분집합으로 계산하지 않고 `noise_excess_th` = None + `excess_reason`(누락 이름 명시) -> 이 metric 제약은 PASS 가 아니라 INCOMPLETE/N/A.
  * `noise_contrib` = 소자·저항별 `{element, thermal_in_v2hz, flicker_in_v2hz, share_thermal}` (f_lo).
* **폐루프**(`noise_out_int_vrms`, `noise.closed_loop = true`, feedback_passives 필요): 루프 넷리스트를 닫은 채(Vlb DC 0) `noise v(out) Vlb_<넷> dec ppd f_lo f_top` 의
  `onoise_spectrum` 을 로그 격자 사다리꼴로 적분한다. 격자 밀도를 두 배씩 올려(최대 4 회) 같은 구간 적분이 reltol 안에 일치하면 멈춘다. f_top 은 `fstop_hz` 에서 시작해
  꼬리 상계 S(f)·f(>= 1 극 감쇠에서 성립)가 (r·v_rms)² 이하가 될 때까지 10 배씩 올린다(상한 8 회) -- 못 맞추면 `converged = false` + `tail_bound_v2` 를 같이 보고(값은 f_hi 까지의 적분).
  **스위치 kT/C 항은 이 모듈이 재지 않는다**(`ktc_sampling.status = not_measured`): 샘플링 위상 과도(trnoise) 평균이 필요하다. 오라클 입력의 스위치를 저항 passive 로 넣으면 그 열잡음은
  `.noise` 에 이미 들어간다(스위치 포함 실제 SC 테스트벤치 증폭 위상).
* 손계산 점검(`smoke/u6_selfchecks.py noise_rc`): 저항 분압 RC (Ra = Rb = 2 kΩ, H0 = 0.5)의 입력 환산 열잡음 = 4kT·(Ra‖Rb)/H0² = 6.6304e-17 V²/Hz 와 상대 6e-7 일치, 두 저항 몫 각 0.5.
  폐루프 적분은 같은 `.noise` 의 ngspice 자체 `onoise_total` 과 4e-5 상대 일치(tfb_cs_rfeedback).

### offset Monte-Carlo (`oracle_offset_mc.py`)

* **소자마다 독립** mismatch 변수: 모델 카드의 `<subckt>__*_slope_spectre`(PDK 가 `.param ... = 0.0` 으로 선언, 카드 안 `p = p0 + slope_spectre·(p_slope/sqrt(l·w·mult))`; sky130 nfet 은 toxe·vth0·voff,
  pfet 은 nfactor 포함)를 소자 k 마다 래퍼 subckt `mmv_<이름>` 안 지역 `.param` 으로 덮는다(ngspice 가 모델 `{식}` 을 래퍼 인스턴스 범위에서 평가함 -- 실측: 두 인스턴스가 다른 vth0 를 갖는다).
  표본마다 `alterparam pv_<이름>_<j> = z·1e-6/sqrt(m)` (z ~ N(0,1), 시드 고정) + `reset` + `op` 를 한 번의 ngspice 실행에 펼친다.
* **단위**: 카드는 l·w 가 µm 숫자(`.option scale=1u`)라고 가정하지만 오라클 넷리스트는 SI 숫자를 주므로 카드 안 sqrt(l·w·mult) 가 1e-6 배이고, 인스턴스 `m`(병렬)은 카드의 `mult` 가 아니라 면적에
  안 들어간다. 그래서 변수값 = z·1e-6/sqrt(m) 로 두어 σ(ΔP) = slope/sqrt(L_µm·W_µm·m) (엔진 41 §6.4-2 A_eff 모델과 같은 면적 의존)을 얻는다. 점검: 5T OTA M1 의 vth0 감도 = 1.1843 mV
  (손계산 3.356e-3/sqrt(1·8) = 1.1865 mV, 0.2 % 일치).
* 입력 환산 offset(차동 입력 쌍 + free 넷리스트의 DC servo): 표본마다 DC 해에서 V_os,k = (V_out,k − V_out,0)/A − (V_id,k − V_id,0) (A = 같은 넷리스트 `.ac` 첫 점의 부호 있는 차동 DC 이득, 0 = 흔들림
  없는 기준 해). 입력이 차동 쌍이 아니거나 servo(`Lfb_`)가 없으면 `status = unavailable` + 이유. 표본 수 N = ceil(1 + 1/(2 r²)) (정규 표본 표준편차의 상대 표준오차 1/sqrt(2(N−1)) = r).
  결과 `sigma_in_mV`(= `offset_in_sigma_mv`), `mean_in_mV`, `n_samples`, `rel_se_achieved`, `n_failed`, `mismatch_vars`.
* 독립 점검(`smoke/u6_selfchecks.py mc_5t`, 5T OTA, r = 0.05 -> 201 표본): MC σ_in = 3.236 mV (상대 표준오차 0.05), 같은 모델의 소자·변수별 1σ 결정적 섭동 감도 RSS = 3.212 mV (비 1.008).

### 스윙·ICMR (`oracle_swing.py`)

* 포화 조건(한 점): 도통 중인(|ID| > `judge.off_current_A`, 없으면 0) MOS 전부 VDS >= VDSAT + `judge.sat_margin_V`(없으면 0), 회로 노드 전압이 레일 ± reltol·레일 폭 안(이상 전류원 꼬리가 레일 밖으로
  내려가는 비물리 해를 창에 넣지 않는다). 풀이가 안 되는 점은 포화 아님(fail-closed). 도통 소자가 하나도 없는 점도 통과가 아니다.
* 스윕은 free 넷리스트의 DC servo 기준원을 `alter` 로 바꾸는 `.op` 들이다(회로를 고치지 않는다): 입력 공통모드 Δ = 입력 넷의 `Vofs_`(servo 입력)에서 Δ 를 빼고 `Vdc_`(servo 없는 입력)에 Δ 를 더한다
  (출력은 servo 로 예측 DC 에 묶인 채); 단일 출력 목표 Vt = `Vofs_<servo 입력>` 에 (Vt − Vo,pred) 를 더한다; 차동 출력 목표 D = V(op) − V(on) = 두 servo 기준을 ∓k·D 만큼 민다(k = `diff_feedback_gain`).
  servo 가 없는 쪽은 `status = unavailable` + 이유.
* 창 = 공칭점에서 이어지는 연속 구간. 거친 격자(간격 V_T = kT/q) 한 번의 ngspice 실행 -> 경계 괄호([마지막 통과, 첫 실패])를 7 점 부분 격자로 좁혀 간다(최대 8 라운드, 목표 분해능 reltol·레일 폭).
* `swing_out_v`: 단일 출력 2·min(V_hi − Vo, Vo − V_lo), 차동 출력 2·min(D_hi, −D_lo) (설계 40 §3.8-8 '출력마다 반폭의 최솟값 × 4' 와 같다). `icmr_v` = [Vin,min, Vin,max] ∩ [rail_lo, rail_hi] 의 폭(좌표 = 점마다 **실제 입력 공통모드** (V_inp + V_inn)/2 -- 엔진 `icmr_v` 와 같은 정의; 차동 입력 `input_p`·`input_n` 이 없는 회로의 ICMR 은 `unavailable`),
  `icm_margin_v` = min(V_icm − Vin,min, Vin,max − V_icm). 공칭점이 이미 포화 조건을 어기면 창이 비어 있다: `swing_out_v`·`icmr_v` 는 음수(−최대 부족량 [V]).
* 점검(`smoke/u6_selfchecks.py swing_5t`, 5T OTA 입력 DC 0.9 V): 스윙 1.2065 V (출력 창 0.2967 ~ 1.6142 V), ICMR 0.6289 V (입력 창 0.6701 ~ 1.2990 V, 하한은 꼬리 노드 ≥ 0 에 의한 것), icm_margin 0.2299 V.

## [신규] CM 루프 PM -- 공통 모드(CMFB) 루프 위상여유 (2026-10-08, 사용자 결정 "6번도 네 의견에 동의하고 제안한 값을 사용해": 완전 차동 회로의 CMFB 루프 PM 하한 60 deg)

엔진 `pm_cm_ss_deg`(metrics CONTRACT 7.11, 출력 포트 CM 주입)와 같은 정의를 재는 측정. DM β 루프(`feedback_passives`)와 독립이다(둘이 함께 있어도 된다).

### 입력 스키마 추가(선택 필드)
* `cm_output_loop`(object, `{"drivers": [소자 이름…]}`): 있으면 공통 모드 루프를 **선언된 차동 출력 포트 쌍(ports.output_p·output_n)** 에서 끊는다(output_p·output_n 이 없으면 막힘). `drivers` = 구동자(x 쪽) MOS 이름 --
  엔진 `cm_partition` 이 정한 집합을 부르는 쪽(어댑터·엔진 브리지)이 넣는다(오라클은 엔진을 import 하지 않는다). 각 소자는 drain·source 중 정확히 하나가 출력 넷이어야 한다(아니면 막힘). CM 감지가 평균 저항이든 DDA 든 버퍼든
  triode 평균이든 오라클은 보지 않는다. (옛 `cm_loop_passives` 입력과 boolean `cm_output_loop` 는 스키마 거부.)
* 닫힌 어휘: 삭제된 옛 입력 `cm_loop_passives` 는 스키마가 명시적으로 거부한다(`false` 스키마 -- 있으면 스키마 위반, 넷리스트를 쓰지 않음).
* measure `cm_pm_deg`(predictions.metrics, acceptance.constraints): 허용오차 키는 `pm_deg_abs`.

### 동작 계약
* 넷리스트: `cm_output_loop` 가 있으면 `<stem>.cmloop.cir`(+ `meta.cm_loop`)를 더 쓴다 -- `drivers` 각 MOS 의 출력 넷 쪽 channel 단자를 `lbx_<넷>` 으로 뗀다.
  수동소자·MOS gate·소비자(감지망) MOS 는 원래 넷(n 쪽)에 남는다(Middlebrook 관례 n = 받는 쪽, x = 되돌림을 내는 쪽; 엔진 `cm_cuts` 와 같은 분할). 넷마다 직렬 전압원
  `Vlb_<넷>`(수신 쪽 +, AC 1/2, DC 0)과 수신 쪽 주입 전류원 `Ilb_<넷>` 을 넣어 두 출력에 **동일 부호** 가중(1/2, 1/2)으로 Middlebrook 이중 주입한다. 입력 포트는 **전부 AC 접지**(`Vac_*` AC 0, DC 는 Vlb 0 V 가 이어 준다). `.ac` 2회 + `loop_gain`
  (DM 과 같은 식). `feedback_passives`·`cm_output_loop` 가 없는 입력은 이 파일들을 만들지 않는다(기존 출력 비트 동일).
* 시뮬레이션: `sim.cm_loop` = {ngspice_rc, break_nets, weights, measures(`ac_measures`), singular, pm_deg, pm_deg_raw, pm_undefined, stability,
  stability_cache}. PM 값이 있으면 DM 과 같은 C10 안정성 근거(Nyquist 감은 수 + 폐루프 .tran `<stem>.cmloop.stab*.cir/txt`)를 건다: P = 0 이 증명되지 않으면
  `pm_deg = None` + `pm_undefined`(이유), 원값 `pm_deg_raw`. Middlebrook 분모 0 은 `loop_probe_singular`(정의 불가, 막힘 아님).
* 비교: measure `cm_pm_deg` 의 SPICE 값 = `sim.cm_loop.pm_deg`; 정의 불가 이유 = `sim.cm_loop.pm_undefined`(제약이면 N/A -> PASS 불가);
  `summary.cm_loop`(break_nets, pm_deg, pm_deg_raw, pm_undefined, loop_gain_dc_db, loop_ugf_hz, singular, stability 요약), 비교표에 'CM 루프(공통 모드 CMFB) PM' 줄.
  루프 측정 결과가 없고 singular 도 아니면 막힘('CM 루프 측정 결과 없음').
* 한계: 루프 이득 T_cm 이 전 대역에서 1 보다 작으면 UGF 가 없어 PM 값이 없다(`ac_measures` 의 pm_deg None -> 'PM 값 없음 -- 검사 대상 아님').
* **판정(사용자 결정 2026-10-08 A, 엔진과 같은 평결)**: acceptance 제약 `cm_pm_deg` 는 `sim.cm_loop` 의 기준점 |T_cm| ≤ 1(`measures.gain_dc` ≤ 1)이고 UGF·`pm_undefined` 모두 없으면 **FAIL**(`undefined = cm_loop_ineffective`, SPICE PM 값 None 이어도) -- CMFB 무효 = 위반. `pm_undefined`(RHP 극·불안정)는 기존 N/A. DM `pm_deg` 는 불변.

### 확인(2026-10-08, ngspice-46 sky130 tt, 기록 -- test 아님)
* 파일럿 옛 엔진 사이징 점(forced, R1 = R2 = 1 MΩ, fstart 100 Hz): `cm_loop` 측정이 끝까지 돈다(T_cm(100 Hz) = −39.38 dB, UGF 없음 -> PM 값 없음; acceptance `cm_pm_deg >= 60` 은 FAIL `cm_loop_ineffective`).
  엔진과의 대조: `smoke/cm_loop_engine_vs_ngspice.py`(엔진 T_cm(0) −39.365 dB, 엔진 대 ngspice 선형 3.3e-7 dB), 결과 `smoke/current_reuse_telescopic_ota.cm_loop_engine_vs_ngspice.json`·`…cm_loop.forced.compare.md`.
* 연속시간 CMFB 변형 5종(합성 소신호): `smoke/cm_loop_variants.py`(결과 `…result.json`) -- metrics CONTRACT 7.11 표.
* 섞인 절단 폐형식 예(CS + Rf, gate 쪽 용량 전용 n): `smoke/cm_loop_mixed_cut_example.py` -- 엔진 PM 17.144891°, 폐형식 같음, 오라클 `loop_gain` 17.14966°.
* 전체 test 스위트에서 C10 `test_rhp_fixture_closed_loop_oscillates_and_n_is_zero[rb1e5]` 가 master 에서도 실패한다(이 변경 밖 -- ngspice 출력 파싱).

## 옛 엔진 기준선 만들기

```bash
PY=C:/Python314/python.exe
T=skills/analog-gmid-design/tools/spice_oracle
$PY -P $T/legacy_adapter.py current_reuse_telescopic_ota /c/tmp/oracle --w-source sizing --isrc engine   # 옛 엔진 ~4.5분
$PY -P $T/oracle_run.py /c/tmp/oracle/current_reuse_telescopic_ota.sizing.engine.oracle_input.json /c/tmp/oracle --bias free forced --judge my_judge.json --require-topology
```
