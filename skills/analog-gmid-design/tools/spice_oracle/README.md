# spice_oracle -- gm/ID 엔진 합격 판정용 SPICE 오라클

엔진이 낸 설계 해(연결·소자 기하·바이어스)와 그 엔진의 예측값을 **엔진 무관 JSON**(`oracle_input.schema.json`)으로
받아 ngspice 로 재고(.op/.ac), 예측 대 SPICE 비교표(JSON + Markdown)와 판정을 낸다.
새 엔진(`skills/analog-gmid-design/gmid_engine/`)과 독립이다 -- 오라클 파일은 어떤 엔진도 import 하지 않는다.
옛 엔진 출력은 `legacy_adapter.py` 하나로 이 형식에 맞춰 기준선(baseline)으로 쓴다.

## 파일 (파일마다 독립 진입점 1개, 다른 파일의 `_` 이름 import 없음)

| 파일 | 진입점 | 역할 |
|---|---|---|
| `oracle_input.schema.json` | - | 입력 형식(JSON Schema 2020-12) |
| `oracle_netlist.py` | `python oracle_netlist.py <input.json> <out.cir> --bias free\|forced` | 넷리스트 + `<out.cir>.meta.json`(probe 이름, 넷, 고정 넷, 경고/막힘) |
| `oracle_simulate.py` | `python oracle_simulate.py <netlist.cir> <sim.json> --ngspice EXE [--timeout-s S]` | `ngspice -b` 실행, .op/.ac 추출 |
| `oracle_compare.py` | `python oracle_compare.py <input.json> <netlist.cir> <sim.json> <out_prefix> [--judge J] [--sat-margin-v V]` | 비교표·판정 |
| `oracle_run.py` | `python oracle_run.py <input.json> <out_dir> --bias free [forced] [--judge J] [--sat-margin-v V] [--ngspice EXE] [--tag T]` | 위 셋을 한 번에(bias 마다) |
| `legacy_adapter.py` | `python legacy_adapter.py <circuit_key> <out_dir> --w-source layout\|sizing --isrc topology\|engine [--from-dump D] [--instance I] [--topology T]` | 옛 엔진 실행(또는 dump) -> 오라클 입력 |
| `legacy_testbench.json` | - | 어댑터가 넣는 테스트벤치 구성값(시제품 하네스 값) |
| `smoke/` | - | 스모크 실행 산출물과 보고서(`smoke/SMOKE_REPORT.md`) |

`python -P` 로 실행해도 된다(`oracle_run.py` 는 자기 디렉터리를 sys.path 에 넣는다). numpy 필요.

## 입력 스키마 요약 (`oracle_input.schema.json` 이 정본)

* `process`: `lut_npz`(코너 `corner`·온도 `temp_c` 메타를 여기서 읽음), `models[kind]`(`subckt`, `includes`(경로의
  `{corner}` 를 npz corner 로 채움), `op_probe`(`@m.{inst}.<내부소자>[{param}]` 틀)), 선택 `diffusion`
  (`ad_per_w_m`, `pd_extra_m`), 선택 `ngspice_exe`.
* `rails`: `[{net, voltage, reference?}]` -- reference 하나가 SPICE 0.
* `devices`: `[{name, kind, drain, gate, source, bulk, L, finger_w, n_fingers, W}]`. 인스턴스는
  `X<name> d g s b <subckt> l=L w=finger_w m=n_fingers`(nf 금지). `W` 는 엔진이 선언한 총폭(finger 곱과의 차를 `W_rel` 로 보고).
* `sources`(이상 전류/전압원, `value_basis` 근거 문자열), `passives`(R/C), `bias_voltages`(게이트 전용 넷), `ports`
  (`input_p/input_n` 또는 `input`, `output_p/output_n` 또는 `output`).
* `predictions`: `nodes`(넷 -> V), `devices`(이름 -> `ID, VGS, VDS, VSB, gm, gds, gm_id, region`), `metrics`
  (`[{name, measure, value, rail?}]`, measure ∈ `dc_gain_db, ugf_hz, pm_deg, f3db_hz, supply_current_A`).
* `acceptance.constraints`: `[{name, measure, op(>=|<=), limit}]` -- SPICE 값으로 직접 판정.
* `testbench`: `dc_choke_H`, `ac_couple_F`, `ac{fstart_hz, fstop_hz, points_per_decade, input_*_ac, diff_feedback_gain}`,
  `options`, `nodeset_from_predictions`.
* `judge`: `tolerances{ID_rel, VGS_abs_V, VDS_abs_V, VSB_abs_V, gm_rel, gds_rel, gm_id_rel, node_abs_V, W_rel, kcl_abs_A,
  dc_gain_db_abs, pm_deg_abs, ugf_hz_rel, f3db_hz_rel, supply_current_A_rel}`, `sat_margin_V`, `off_current_A`.
  **기본값 없음** -- 빠진 키는 그 항목 판정이 `N/A`. `--judge` 파일·`--sat-margin-v` 가 덮어쓴다.
* 크기 규칙: 소자 전압·전류는 극성 정규화(PMOS 도 켜진 포화면 ID·VGS·VDS 양수, VSB = |바디-소스| 방향 양수).
  ngspice BSIM4 의 `@` 값이 이미 이 규칙이라(실측) SPICE 쪽은 `VSB=-vbs` 외에 변환하지 않는다.

## 바이어스 모드

* `free`: 회로가 DC 해를 스스로 찾는다. 입력 DC 는 choke 로, AC 는 결합 C 로. 출력 -> 반대 극성 입력 DC 되먹임
  (단일 출력: `out -> input_n`, 오프셋 V_out_pred - V_in_pred; 차동 출력: 차동 성분 k*(Vo-Vo') 만, 입력 공통모드는
  예측값). `nodeset_from_predictions` 이면 예측 노드전압을 `.nodeset`(초기값일 뿐).
* `forced`: 예측 전압이 있는 소자 단자 넷 전부를 choke 로 예측값에 묶는다. DC = 엔진이 의도한 바이어스,
  고정원 전류 = 그 넷의 KCL 잔차(`kcl_residual`), AC 는 choke 가 열려 실제 모델 개루프 응답.

## 출력 (`oracle_run.py`, bias 마다)

`<circuit>[.<tag>].<bias>.cir` / `.cir.meta.json` / `.log` / `.ac.txt` / `.sim.json` / `.compare.json` / `.compare.md`.
`compare.json` 최상위: `summary{verdict, counts{PASS,FAIL,N/A}, sat_in_spice, not_sat, spice_ac, rail_current_A}`,
`performance`, `constraints`, `kcl_residual`, `devices`(소자별 예측/SPICE/오차/영역/판정), `nodes`, `blockers`, `notes`,
`judge_config`, `lut_meta`, `provenance`.
측정 정의: gain = |H(fstart)|, UGF = |H|=1 첫 하강 교차(log 보간), PM = 180 - (DC 위상 - UGF 위상),
f-3dB = |H| < |H0|/sqrt2 인 첫 주파수 점, supply_current = 레일 전압원이 공급하는 전류.

## 동작 계약 (test 작성자용 -- 이 디렉터리의 test 는 다른 agent 가 쓴다)

C1. 입력 독립성: `oracle_*.py` 는 엔진 패키지(`gmid_engine`, `legacy`)를 import 하지 않는다. `legacy_adapter.py` 만 legacy 를 import 한다.
C2. 코너·온도: 넷리스트의 `.temp` 는 `process.lut_npz` 의 `temp_c`, include 경로의 `{corner}` 는 npz `corner` 로 채워진다.
    npz 에 둘 중 하나라도 없으면 `meta.blockers` 에 들어가고 `compare.summary.verdict == "BLOCKED"`(FAIL 이 없을 때).
C3. finger 규칙: 소자 하나당 `X<name>` 줄 정확히 1개, `w=finger_w`, `m=n_fingers`, `nf=` 없음.
    `diffusion` 이 있으면 `ad=as=ad_per_w_m*finger_w`, `pd=ps=finger_w+pd_extra_m`, 없으면 ad/as/pd/ps 없음.
C4. 레일: `reference=true` 넷은 SPICE 노드 `0`, 나머지 레일은 `Vrail_<net>` 전압원. reference 가 1개가 아니면 막힘.
    대소문자만 다른 두 넷(전압 같은 레일 별칭 제외)은 막힘.
C5. free: 차동 입력+차동 출력이면 `Efb_<in>` 이 (Vo-Vo') 차동 성분을 `diff_feedback_gain` 배로 되먹이고 `Vofs_<in>` 은 -V_in_pred;
    단일 출력이면 `out -> input_n` 이득 1, 오프셋 V_out_pred - V_in_pred; 되먹임 없는 입력은 `Vdc_<in>` + choke.
    forced: 레일·입력·게이트 전용 바이어스 넷을 뺀 모든 소자 단자 넷(예측 있음)에 `Vhold_<net>` + choke, free 모드 `.nodeset` 없음.
C6. 게이트 전용 넷(드레인/소스/전원/수동소자/입력 어디에도 안 물림): `bias_voltages` 값, 없으면 `predictions.nodes` 값의
    `Vbias_<net>` 과 notes 경고, 둘 다 없으면 막힘.
C7. 판정: 오차 = SPICE - 예측(abs) 또는 (SPICE - 예측)/|예측|(rel); `|오차| <= tol` 이면 PASS. tol 없으면 `N/A(tol 미설정)`.
    `sat_margin_V` 없으면 영역 `None`, 영역 판정 `N/A(sat_margin 미설정)`. 있으면 VDS - VDSAT >= margin 이 sat.
    `off_current_A` 가 있으면 |ID| < 그 값은 `off`. 영역 판정 = SPICE 영역 == predictions.devices[].region.
    테스트벤치가 고정한 넷(forced 고정·게이트 바이어스·입력)의 노드 판정은 `N/A(테스트벤치가 고정)`.
C8. verdict: FAIL 이 하나라도 있으면 `FAIL`; 아니면 막힘이 있으면 `BLOCKED`; 아니면 N/A 가 없으면 `PASS`, 있으면 `INCOMPLETE`.
    `oracle_run.py` 반환 코드: PASS/INCOMPLETE 0, FAIL 1, BLOCKED 2(여러 bias 중 최악).
C9. acceptance 제약: `op` 이 `>=`/`<=` 일 때 SPICE 값으로 PASS/FAIL, SPICE 값 없으면 N/A.
C10. 측정: 위 "측정 정의" 그대로. |H| 가 1 아래로 내려가지 않거나 첫 점부터 1 미만이면 `ugf_hz`/`pm_deg` 는 None.
C11. 숫자 기본값: `oracle_*.py` 에 허용오차·포화 여유·테스트벤치 값의 숫자 기본값이 없다(모두 입력/인자).
C12. legacy_adapter: 같은 dump 를 두 번 변환하면 같은 입력이 나온다(provenance 경로 제외). `--from-dump` 결과와 엔진을 새로 돌린
    결과는 엔진이 결정론적이면 같다(2026-10-07 current_reuse 에서 dump 의 sizing/metrics/node_pred/instance 전부 일치 확인).

## 옛 엔진 기준선 만들기

```bash
PY=C:/Python314/python.exe
T=skills/analog-gmid-design/tools/spice_oracle
$PY -P $T/legacy_adapter.py current_reuse_telescopic_ota /c/tmp/oracle --w-source sizing --isrc engine   # 옛 엔진 ~4.5분
$PY -P $T/oracle_run.py /c/tmp/oracle/current_reuse_telescopic_ota.sizing.engine.oracle_input.json /c/tmp/oracle --bias free forced --judge my_judge.json
```
