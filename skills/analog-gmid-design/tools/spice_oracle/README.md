# spice_oracle -- gm/ID 엔진 합격 판정용 SPICE 오라클

엔진이 낸 설계 해(연결·소자 기하·바이어스)와 그 엔진의 예측값을 **엔진 무관 JSON**(`oracle_input.schema.json`)으로
받아 ngspice 로 재고(.op/.ac), 합격 판정과 예측 대 SPICE 비교 기록(JSON + Markdown)을 낸다.
새 엔진(`skills/analog-gmid-design/gmid_engine/`)과 독립이다 -- 오라클 파일은 어떤 엔진도 import 하지 않는다.
옛 엔진 출력은 `legacy_adapter.py` 하나로 이 형식에 맞춰 기준선(baseline)으로 쓴다.

## 파일 (파일마다 독립 진입점 1개, 다른 파일의 `_` 이름 import 없음)

| 파일 | 진입점 | 역할 |
|---|---|---|
| `oracle_input.schema.json` | - | 입력 형식(JSON Schema 2020-12). 진입점은 입력을 이것으로 먼저 검증한다 |
| `oracle_netlist.py` | `python oracle_netlist.py <input.json> <out.cir> --bias free\|forced` | 넷리스트 + `<out.cir>.meta.json`, feedback_passives 가 있으면 `<stem>.loop.cir` |
| `oracle_simulate.py` | `python oracle_simulate.py <netlist.cir> <sim.json> --ngspice EXE [--timeout-s S]` | `ngspice -b` 실행, .op/.ac(+β 루프) 추출 |
| `oracle_compare.py` | `python oracle_compare.py <input.json> <netlist.cir> <sim.json> <out_prefix> [--judge J] [--sat-margin-v V]` | 합격 판정 + 비교 기록 |
| `oracle_run.py` | `python oracle_run.py <input.json> <out_dir> --bias free [forced] [--judge J] [--sat-margin-v V] [--ngspice EXE] [--tag T]` | 위 셋을 한 번에(bias 마다) |
| `legacy_adapter.py` | `python legacy_adapter.py <circuit_key> <out_dir> --w-source layout\|sizing --isrc topology\|engine [--from-dump D] [--instance I] [--topology T]` | 옛 엔진 실행(또는 dump) -> 오라클 입력 |
| `legacy_testbench.json` | - | 어댑터가 넣는 테스트벤치 구성값 |
| `smoke/` | - | 스모크 실행 산출물과 보고서(`smoke/SMOKE_REPORT.md`) |

`python -P` 로 실행해도 된다(진입점이 자기 디렉터리를 sys.path 에 넣는다). numpy, jsonschema 필요.

## 입력 스키마 요약 (`oracle_input.schema.json` 이 정본)

* `process`: `lut_npz`(코너 `corner`·온도 `temp_c` 메타를 여기서 읽음), `models[kind]`(`subckt`, `includes`(경로의
  `{corner}` 를 npz corner 로 채움), `op_probe`(`@m.{inst}.<내부소자>[{param}]` 틀)), 선택 `diffusion`
  (`ad_per_w_m`, `pd_extra_m`), 선택 `ngspice_exe`.
* `rails`: `[{net, voltage, reference?}]` -- reference 하나가 SPICE 0.
* `devices`: `[{name, kind, drain, gate, source, bulk, L, finger_w, n_fingers, W}]`. 인스턴스는
  `X<name> d g s b <subckt> l=L w=finger_w m=n_fingers`(nf 금지). `W` 는 엔진이 선언한 총폭(finger 곱과의 차를 `W_rel` 로 기록).
* `sources`(이상 전류/전압원, `value_basis` 근거 문자열), `passives`(R/C), `bias_voltages`(게이트 전용 넷), `ports`
  (`input_p/input_n` 또는 `input`, `output_p/output_n` 또는 `output`).
* **[신규]** `feedback_passives`: β 되먹임망을 이루는 passives 이름(입력 포트 넷에 물린 소자). PM 정의를 정한다(아래).
* `predictions`: `nodes`(넷 -> V), `devices`(이름 -> `ID, VGS, VDS, VSB, gm, gds, gm_id, region`), `metrics`
  (`[{name, measure, value, rail?}]`, measure ∈ `dc_gain_db, ugf_hz, pm_deg, f3db_hz, supply_current_A`).
* `acceptance.constraints`: `[{name, measure, op(>=|<=), limit}]` -- 회로 성능 스펙. 합격 판정에 쓰인다.
* `testbench`: `dc_choke_H`, `ac_couple_F`, `ac{fstart_hz, fstop_hz, points_per_decade, input_*_ac, diff_feedback_gain}`,
  `options`, `nodeset_from_predictions`, **[신규]** `loop_dc_choke_H`(β 루프 측정용 입력 DC 경로, feedback_passives 가 있으면 필요).
* `judge`: `sat_margin_V`(합격 판정의 포화 여유), `off_current_A`(선택), `tolerances{ID_rel, VGS_abs_V, VDS_abs_V, VSB_abs_V,
  gm_rel, gds_rel, gm_id_rel, node_abs_V, W_rel, kcl_abs_A, dc_gain_db_abs, pm_deg_abs, ugf_hz_rel, f3db_hz_rel,
  supply_current_A_rel}`(기록·경고용). **기본값 없음**. `--judge` 파일·`--sat-margin-v` 가 덮어쓴다.
* 크기 규칙: 소자 전압·전류는 극성 정규화(PMOS 도 켜진 포화면 ID·VGS·VDS 양수, VSB = |바디-소스| 방향 양수).
  ngspice BSIM4 의 `@` 값이 이미 이 규칙이라(실측) SPICE 쪽은 `VSB=-vbs` 외에 변환하지 않는다.

## 합격 정의 (사용자 확정 2026-10-07)

`summary.verdict` 는 **free 모드에서만** 합격/불합격을 낸다. 합격 조건은 둘뿐이다.
1. `acceptance.constraints` 의 선언 제약(회로 성능 스펙)을 SPICE 값이 전부 만족한다.
2. ID > 0(`off_current_A` 가 있으면 ID > 그 값)인 모든 MOS 가 포화: VDS - VDSAT >= `sat_margin_V`(인자, 기본값 없음).

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
* 선언이 없으면 **β=1 루프**: L = 개루프 A(입력 차동 AC -> 출력)의 위상여유.
* 두 경우 모두 PM = 180 - (기준점 위상 - |L|=1 첫 하강 교차의 위상) [deg], 기준점 = 측정 첫 주파수(fstart), 위상은 언랩.
  `ac.pm_deg` = 이 값, `ac.pm_definition` = `beta_loop`|`beta_1`, `ac.pm_open_loop_deg` = 늘 A 기준 값,
  `ac.loop_gain_dc_db`/`ac.loop_ugf_hz` = T 의 기준점 크기·교차 주파수.
* 검증: 이상 gm 증폭기 + Cf/Cs/Cin 회로에서 해석식 T 와 1.3e-4 이내 일치(2026-10-07).

## 바이어스 모드

* `free`: 회로가 DC 해를 스스로 찾는다. 입력 DC 는 choke 로, AC 는 결합 C 로. 출력 -> 반대 극성 입력 DC 되먹임
  (단일 출력: `out -> input_n`, 오프셋 V_out_pred - V_in_pred; 차동 출력: 차동 성분 k*(Vo-Vo') 만, 입력 공통모드는
  예측값). `nodeset_from_predictions` 이면 예측 노드전압을 `.nodeset`(초기값일 뿐).
* `forced`: 예측 전압이 있는 소자 단자 넷 전부를 choke 로 예측값에 묶는다. DC = 엔진이 의도한 바이어스,
  고정원 전류 = 그 넷의 KCL 잔차(`kcl_residual`), AC 는 choke 가 열려 실제 모델 개루프 응답. 진단용.

## 출력 (`oracle_run.py`, bias 마다)

`<circuit>[.<tag>].<bias>.cir` / `.cir.meta.json` / `.log` / `.ac.txt` / `.sim.json` / `.compare.json` / `.compare.md`
(+ feedback_passives 가 있으면 `.loop.cir` / `.loop.log` / `.loop.v.txt` / `.loop.i.txt`).
`compare.json` 최상위: `summary{verdict, verdict_reason, warnings, acceptance{constraints_failed, constraints_unmeasured,
conducting_devices, unsaturated_conducting, sat_margin_V, off_current_A}, record_counts, sat_in_spice, not_sat, spice_ac,
rail_current_A}`, `performance`, `constraints`, `kcl_residual`, `devices`, `nodes`, `blockers`, `notes`, `judge_config`,
`lut_meta`, `provenance`.
측정 정의(개루프 A): gain = |H(fstart)|, UGF = |H|=1 첫 하강 교차(log 보간), f-3dB = |H| < |H0|/sqrt2 인 첫 주파수 점,
supply_current = 레일 전압원이 공급하는 전류. PM 은 위 "PM 정의".

## 동작 계약 (test 작성자용 -- 이 디렉터리의 test 는 다른 agent 가 쓴다)

표시: **[변경]** = 2026-10-07 사용자 확정 반영으로 바뀐 항목, **[신규]** = 추가.

C1. 입력 독립성: `oracle_*.py` 는 엔진 패키지(`gmid_engine`, `legacy`)를 import 하지 않는다. `legacy_adapter.py` 만 legacy 를 import 한다.
C2. **[변경]** 코너·온도: 넷리스트의 `.temp` 는 `process.lut_npz` 의 `temp_c`, include 경로의 `{corner}` 는 npz `corner` 로 채워진다.
    npz 에 둘 중 하나라도 없으면 `meta.blockers` 에 들어가고(.temp 줄은 쓰지 않음), ngspice 를 돌리지 않으며(`sim.skipped`),
    `compare.summary.verdict == "BLOCKED"`, `oracle_run.py` 반환 2.
C3. finger 규칙: 소자 하나당 `X<name>` 줄 정확히 1개, `w=finger_w`, `m=n_fingers`, `nf=` 없음.
    `diffusion` 이 있으면 `ad=as=ad_per_w_m*finger_w`, `pd=ps=finger_w+pd_extra_m`, 없으면 ad/as/pd/ps 없음.
C4. 레일: `reference=true` 넷은 SPICE 노드 `0`, 나머지 레일은 `Vrail_<net>` 전압원. reference 가 1개가 아니면 막힘.
    대소문자만 다른 두 넷(전압 같은 레일 별칭 제외)은 막힘.
C5. free: 차동 입력+차동 출력이면 `Efb_<in>` 이 (Vo-Vo') 차동 성분을 `diff_feedback_gain` 배로 되먹이고 `Vofs_<in>` 은 -V_in_pred;
    단일 출력이면 `out -> input_n` 이득 1, 오프셋 V_out_pred - V_in_pred; 되먹임 없는 입력은 `Vdc_<in>` + choke.
    forced: 레일·입력·게이트 전용 바이어스 넷을 뺀 모든 소자 단자 넷(예측 있음)에 `Vhold_<net>` + choke, free 모드 `.nodeset` 없음.
C6. 게이트 전용 넷(드레인/소스/전원/수동소자/입력 어디에도 안 물림): `bias_voltages` 값, 없으면 `predictions.nodes` 값의
    `Vbias_<net>` 과 notes 경고, 둘 다 없으면 막힘.
C7. **[변경]** 기록: 오차 = SPICE - 예측(abs) 또는 (SPICE - 예측)/|예측|(rel). 허용오차가 있으면 기록 칸 `judge` 에 `|오차| <= tol`
    PASS / 밖 FAIL, 없으면 `N/A(tol 미설정)` -- **verdict 와 무관**. 영역: `sat_margin_V` 없으면 `None`(+`N/A(sat_margin 미설정)`),
    있으면 VDS - VDSAT >= margin 이 `sat`, 아니면 `triode`; `off_current_A` 가 있으면 |ID| < 그 값은 `off`.
    영역 기록 칸 = SPICE 영역 == predictions.devices[].region. 테스트벤치가 고정한 넷의 노드 기록은 `N/A(테스트벤치가 고정)`.
    forced 모드에서 |ID_rel| > tolerances.ID_rel 또는 |gm_rel| > tolerances.gm_rel 인 소자는 `summary.warnings` 와 Markdown 맨 앞.
C8. **[변경]** verdict: 막힘이 있으면 `BLOCKED`. forced 모드는 그 밖에 늘 `INCOMPLETE`. free 모드는 선언 제약 FAIL 이 있거나
    포화 아닌 전도 MOS(ID > 0, 또는 > off_current_A)가 있으면 `FAIL`; 아니면 `sat_margin_V` 미설정이거나 SPICE 값을 못 얻은 제약이
    있으면 `INCOMPLETE`; 아니면 `PASS`. `oracle_run.py` 반환 코드: PASS/INCOMPLETE 0, FAIL 1, BLOCKED 2(여러 bias 중 최악).
C9. **[변경]** acceptance 제약: `op` 이 `>=`/`<=` 일 때 SPICE 값으로 PASS/FAIL, SPICE 값 없으면 `N/A(SPICE 값 없음)`. 제약은 판정 대상.
C10. **[변경]** 측정: 위 "측정 정의"와 "PM 정의" 그대로. |L| 가 1 아래로 내려가지 않거나 첫 점부터 1 미만이면 `ugf_hz`/`pm_deg` 는 None.
C11. 숫자 기본값: `oracle_*.py` 에 허용오차·포화 여유·테스트벤치 값의 숫자 기본값이 없다(모두 입력/인자). 스키마 필수 testbench 값이
    빠지면 C13 거부, 선택 값(`input_*_ac`, `diff_feedback_gain`, `loop_dc_choke_H`)이 필요한데 없으면 막힘.
C12. legacy_adapter: 같은 dump 를 두 번 변환하면 같은 입력이 나온다(provenance 경로 제외). `--from-dump` 결과와 엔진을 새로 돌린
    결과는 엔진이 결정론적이면 같다. **[변경]** 입력 포트 넷에 단자가 물린 passives 를 `feedback_passives` 로 선언한다.
C13. **[신규]** 스키마 검증: `oracle_netlist.py`, `oracle_compare.py`, `oracle_run.py` 는 입력을 `oracle_input.schema.json`
    (Draft 2020-12)으로 검증하고, 위반이면 위반 목록을 출력하고 **아무 산출물도 쓰지 않고** 반환 2 로 끝난다.
C14. **[신규]** β 루프: `feedback_passives` 가 있으면 `<stem>.loop.cir` 에서 그 소자들의 입력 넷 단자만 `lbx_<넷>` 으로 바뀌고,
    끊은 넷마다 `Vlb_<넷> <넷> lbx_<넷>` 과 `Ilb_<넷> 0 <넷>` 이 있고, 그 넷의 결합 C/AC 원은 없다. **[변경]** 판정은 소자 단위(fail-closed):
    선언된 되먹임 수동소자 **각각**이 passives 에 있고 입력 포트 넷에 물려 있어야 하며, 하나라도 아니면 막힘이고 blocker 문장에
    그 소자 이름을 적는다. `loop_dc_choke_H` 가 없어도 막힘.

## 옛 엔진 기준선 만들기

```bash
PY=C:/Python314/python.exe
T=skills/analog-gmid-design/tools/spice_oracle
$PY -P $T/legacy_adapter.py current_reuse_telescopic_ota /c/tmp/oracle --w-source sizing --isrc engine   # 옛 엔진 ~4.5분
$PY -P $T/oracle_run.py /c/tmp/oracle/current_reuse_telescopic_ota.sizing.engine.oracle_input.json /c/tmp/oracle --bias free forced --judge my_judge.json
```
