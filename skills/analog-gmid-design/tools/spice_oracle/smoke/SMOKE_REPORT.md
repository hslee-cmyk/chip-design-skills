# spice_oracle 스모크 실행 보고 (2026-10-07)

대상: 옛 엔진 `current_reuse_telescopic_ota` -> `legacy_adapter.py` -> `oracle_run.py --bias free forced`.
대조 기준: 같은 날 시제품 하네스(`_drafts/engine/spice_harness/spice_harness.py`, 저장소 밖)를 **같은 엔진 dump 로 다시 돌린 결과**.
(시제품 `results/` 의 `topo_iref`·`eng_iref` 는 되먹임 방식을 바꾸기 전 버전으로 돌린 것이라 직접 대조하지 않았다 --
그 넷리스트에 `Efb_Vip fbs_Vip 0 Vom 0 1`(출력 공통모드까지 되먹임)이 남아 있다.)

환경: ngspice-46 `ngspice_con.exe -b`, PDK `C:\pdk\sky130_fd_pr`, LUT 옛 sample LUT(smoke 실행 당시, O-180 으로 삭제; 지금 기준 LUT = `assets/lut_v2_location.json`, 같은 corner tt, 27 C),
Python 3.14 + numpy 2.4.6. 임시 경로 `/c/g465`(끝나고 삭제).

## 1. 어댑터 -- 옛 엔진 새로 실행 vs 시제품 dump

* `legacy_adapter.py current_reuse_telescopic_ota <out> --w-source sizing --isrc engine` 로 옛 엔진을 새로 돌렸다(264.7 s, engine_ok).
* 새 dump 와 시제품 dump(`engine.json`) 비교: `sizing`, `metrics`, `theta_star`, `node_pred`, `device_pred` 전부 같음(==),
  `instance.json` 넷리스트도 같음.
* 새 dump 로 만든 오라클 입력 4종(sizing/layout x engine/topology 전류원)과 시제품 dump 로 만든 입력: provenance 를 뺀 모든 키가 같음.
* `oracle_input.schema.json` 으로 jsonschema 검증 통과(3종).
* 어댑터 경고(입력 provenance, 비교표 머리에도 찍힘): Iref topology 1.2 uA 대신 엔진 ID(M18_bg) 0.1993 uA(--isrc engine),
  옛 엔진 노드전압 복원 충돌 4건(최대 0.2227 V), 게이트 넷 VGS 투표 폭(Vbias2 0.89 V, Vbias3 0.646 V, Voc_des 0.546 V ...),
  layout W != sizing W 31소자, **instance.json 행 w != n_fingers*finger_w: M11b, M20b**(행 w=36.02 um, n=2, finger_w=36.02 um).

## 2. 오라클 결과 (2026-10-07 재실행: 새 합격 정의·β 루프 PM 반영)

판정 설정 `smoke_judge.json`: sat_margin 0 V, off |ID|<1 pA(시제품 영역 규칙 재현용, 사용자 확정 기준 아님), 허용오차 미설정.
어댑터가 입력 포트 넷에 물린 Cf1, Cf2, Cs1, Cs2 를 `feedback_passives` 로 선언 -> PM 은 β 루프 기준(README "PM 정의").

| 입력(w_source.isrc) | bias | gain dB(A) | UGF Hz(A) | PM deg(β 루프) | PM deg(A, β=1) | 루프 T 기준점 dB / UGF Hz | I(vdd) uA | 포화 아닌 전도 MOS | 제약 gain>=54 / PM>=70 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| sizing.engine | forced | 54.979 | 1.0451e7 | 90.01 | 79.252 | 43.25 / 4.247e6 | 83.951 | M3a M3b M5 | PASS / PASS | INCOMPLETE(진단 모드) |
| sizing.engine | free | -150.1(동작 안 함) | - | - | - | - | 30.48 | 15개 | FAIL / N/A(측정 불가) | **FAIL** |
| layout.engine | forced | 61.786 | 5.898e7 | 50.77 | 18.11 | 47.88 / 2.582e7 | 87.64 | M3a M3b M5 | PASS / FAIL | INCOMPLETE(진단 모드) |
| layout.engine | free | -176.8 | - | - | - | - | 41.60 | 17개 | FAIL / N/A | **FAIL** |
| layout.topology | forced | 61.786 | 5.898e7 | 50.77 | 18.11 | 47.88 / 2.582e7 | 87.64 | M3a M3b M5 | PASS / FAIL | INCOMPLETE(진단 모드) |
| layout.topology | free | -169.4 | - | - | - | - | 244.96 | 17개 | FAIL / N/A | **FAIL** |

* 합격 판정(free): 세 입력 모두 FAIL -- 선언 제약 gain_db>=54 불만족(회로가 DC 해에서 죽음) + 전도 MOS 15~17개 비포화.
  M2a/M2b 는 ID 0.55 pA 로 off(전도 아님) 라 포화 조건에서 빠진다. `oracle_run.py` 반환 1.
* forced 는 진단: β 루프 PM 90.0 deg(sizing W)로 개루프 A 의 79.25 deg 보다 크다(β = T/A = 145.4/561 = 0.26 에서 교차가
  4.25 MHz 로 내려감). 엔진 parasitic_pm_deg 75.02 와의 차이는 기록만.
* 경고 기능 확인(별도 실행, 허용오차 ID_rel=gm_rel=0.1): forced sizing.engine 에서 62건 경고가 비교표 맨 앞에 찍힘
  (예: M1a ID_rel -0.645). 스모크 기본 설정에는 허용오차가 없어 경고 0.
* β 루프 측정 정확도: 이상 gm 증폭기(gm 1 mS, Ro 1 MOhm, CL 1 pF, Cin 0.2 pF, Cf=Cs=0.5 pF)에서 해석식 루프 이득과
  최대 상대차 1.3e-4. 입력 DC 경로를 `dc_choke_H`(1e12 H)로 두면 입력 넷 용량과 ~0.2 Hz 에서 공진해 fstart(0.01 Hz)의
  T 가 틀렸다(PM 270 deg 로 나옴) -- 그래서 `loop_dc_choke_H`(어댑터 1e20 H)를 따로 둔다.

엔진 예측: gain_db 61.56(단 이득 합) / gain_full_circuit_db 67.08(MNA), parasitic_pm_deg 75.02, supply_current 82.02 uA.
forced sizing.engine KCL 잔차(고정원 전류) 상위: Vy +197.7 uA, N64_63 -182.0, Vom1 -38.0, Vop1 -36.8.
free 모드에서 출력 Vop/Vom 은 1.8 V 레일, Vom1/Vop1 ~0.08 V(예측 0.677) -- 엔진 동작점이 자기일관적 DC 해로 실현되지 않는다는 시제품 결론과 같다.

## 3. 시제품 대비 수치 일치 (`prototype_comparison.json`)

아래는 첫 커밋(a622379) 때 대조. 이번 수정에서 개루프 A 측정·.op 경로는 바뀌지 않아(gain/UGF/개루프 PM/I(vdd) 값 동일) 그대로 유효하다.

| 시제품(재실행) | 오라클 | gain dB 차 | UGF 상대차 | PM 차 deg | I(vdd) 차 uA | 소자 ID 최대 상대차(>1 nA) | 노드 최대차 V | KCL 최대차 uA | 영역 목록 |
|---|---|---|---|---|---|---|---|---|---|
| forced sizing W | sizing.engine.forced | 1.0e-5 | 7e-8 | 8e-7 | 0 | 1.5e-6 | 0 | 1e-5 | 같음(5) |
| free sizing W | sizing.engine.free | 6.5e-5 | - | - | 1e-4 | 3.4e-6 | 1e-6 | - | 같음(19) |
| forced layout W | layout.engine.forced | 7.8e-6 | **3.3e-3** | **0.105** | 1e-4 | **0.94(M11b)** | 0 | 0.51 | 같음(5) |
| free layout W, Iref 엔진 | layout.engine.free | 3e-6 | - | - | 3.2e-3 | 7.2e-3(M12) | 0.031 | - | 같음(19) |
| free layout W, Iref topology | layout.topology.free | 9e-6 | - | - | 0.033 | 1.3e-2(M11a) | 0.036 | - | 같음(19) |

* **sizing W(엔진 sizing W 를 LUT 폭 bin finger 로)**: 시제품과 수치 일치(차이는 넷리스트 숫자 표기 자릿수 수준). 시제품의 병렬
  인스턴스 n 개(nf=1)와 오라클의 단일 인스턴스 `m=n` 이 같은 결과를 낸다(ngspice subckt m 은 @id/gm/gds 를 m 배 총합으로 보고 -- 실측).
* **layout W 의 차이 원인은 하나 -- M11b/M20b**: instance.json 행이 `w=36.02 um, n_fingers=2, finger_w=36.02 um` 로 자기모순이다.
  시제품은 행 w(36.02)를 2로 나눠 18.0 um x 2 를, 오라클은 finger 규칙대로 36.02 um x m=2(=72.03 um, 엔진 sizing W 와 같음)를 넣는다.
  진단용 변형(두 소자만 finger_w = 행 w / n 으로 바꾼 입력, 커밋 안 함)으로 다시 돌리면 세 layout 조건 모두 시제품과 일치:
  forced UGF 5.91787e7 / PM 18.00697(시제품 5.91787e7 / 18.00697), 소자 ID 최대 상대차 1.6e-6, 노드 최대차 1e-7 V.
  오라클은 이 모순을 `devices[].W`(행 w 합) 대 `finger_w*n_fingers` 의 `W_rel`(+100 %)로 비교표에 드러낸다.
* VGS 표기 차이: 시제품은 SPICE VGS 를 절댓값으로 적어 역바이어스 게이트를 숨겼다(free sizing 의 M9a -0.297 V, M18a -0.299 V 를 +로 표시).
  오라클은 BSIM4 극성 정규화 값을 그대로 쓴다(VSB 도 시제품은 PMOS 부호가 반대였다).

## 4. 판정 기준 관련 남은 사용자 결정 (오라클은 값을 정하지 않음)

확정됨(2026-10-07): 합격 정의(free 제약 + 포화), PM 정의(β 루프 / β=1). 남은 것: `sat_margin_V`·`off_current_A` 값,
경고용 허용오차(ID_rel, gm_rel) 값, layout W 와 sizing W 중 기준.

## 재현

```bash
PY=C:/Python314/python.exe; T=skills/analog-gmid-design/tools/spice_oracle; O=/c/tmp/oracle
$PY -P $T/legacy_adapter.py current_reuse_telescopic_ota $O --w-source sizing --isrc engine
for ws in layout; do for is in engine topology; do
  $PY -P $T/legacy_adapter.py current_reuse_telescopic_ota $O --from-dump $O/current_reuse_telescopic_ota.legacy_dump.json --w-source $ws --isrc $is; done; done
for v in sizing.engine layout.engine layout.topology; do
  $PY -P $T/oracle_run.py $O/current_reuse_telescopic_ota.$v.oracle_input.json $O --bias free forced --tag $v --judge $T/smoke/smoke_judge.json; done
```

이 디렉터리의 `*.oracle_input.json` 은 위 첫 줄(옛 엔진 새 실행)로 만든 것이고, 안의 절대 경로는 작업 worktree 경로다.
`*.cir`, `*.compare.md` 는 그 입력으로 돌린 산출물이다.

**재생성 2026-10-08**(C12 보충 `feedback_passives_basis` 반영): 위 재현 절차를 그대로 다시 돌렸다(옛 엔진 새 실행 engine_ok).
입력 3개는 provenance·LUT 절대 경로를 빼면 이전 것과 `feedback_passives_basis = "legacy_c12_input_net_passives"` 한 키만 다르고,
`*.cir`·`*.loop.cir` 는 바이트 동일, 2절 표의 수치(gain·UGF·PM·I(vdd)·verdict)도 같다. `*.compare.md` 는 그사이 추가된 기록
행(C15·C22·C23·C25·C27·PM 루프·PM 교차 측정·forced 진단)이 붙은 현재 형식으로 바뀌었다.
