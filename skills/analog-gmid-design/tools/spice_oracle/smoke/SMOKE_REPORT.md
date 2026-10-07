# spice_oracle 스모크 실행 보고 (2026-10-07)

대상: 옛 엔진 `current_reuse_telescopic_ota` -> `legacy_adapter.py` -> `oracle_run.py --bias free forced`.
대조 기준: 같은 날 시제품 하네스(`_drafts/engine/spice_harness/spice_harness.py`, 저장소 밖)를 **같은 엔진 dump 로 다시 돌린 결과**.
(시제품 `results/` 의 `topo_iref`·`eng_iref` 는 되먹임 방식을 바꾸기 전 버전으로 돌린 것이라 직접 대조하지 않았다 --
그 넷리스트에 `Efb_Vip fbs_Vip 0 Vom 0 1`(출력 공통모드까지 되먹임)이 남아 있다.)

환경: ngspice-46 `ngspice_con.exe -b`, PDK `C:\pdk\sky130_fd_pr`, LUT `assets/sky130_nfet_pfet_lut_sample.npz`(corner tt, 27 C),
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

## 2. 오라클 결과 (판정 설정 `smoke_judge.json`: sat_margin 0 V, off |ID|<1 pA -- 시제품 영역 규칙 재현용, 허용오차 미설정)

| 입력(w_source.isrc) | bias | gain dB | UGF Hz | PM deg | I(vdd) uA | 포화 | 선언 제약 gain>=54 / PM>=70 | verdict |
|---|---|---|---|---|---|---|---|---|
| sizing.engine | forced | 54.979 | 1.0451e7 | 79.252 | 83.951 | 46/51 (M2a M2b off, M3a M3b M5 triode) | PASS / PASS | FAIL(영역 5) |
| sizing.engine | free | -150.1(동작 안 함) | - | - | 30.48 | 32/51 | FAIL / N/A | FAIL |
| layout.engine | forced | 61.786 | 5.898e7 | 18.11 | 87.64 | 46/51 | PASS / FAIL | FAIL |
| layout.engine | free | -176.8 | - | - | 41.60 | 32/51 | FAIL / N/A | FAIL |
| layout.topology | forced | 61.786 | 5.898e7 | 18.11 | 87.64 | 46/51 | PASS / FAIL | FAIL |
| layout.topology | free | -169.4 | - | - | 244.96 | 32/51 | FAIL / N/A | FAIL |

엔진 예측: gain_db 61.56(단 이득 합) / gain_full_circuit_db 67.08(MNA), parasitic_pm_deg 75.02, supply_current 82.02 uA.
forced sizing.engine KCL 잔차(고정원 전류) 상위: Vy +197.7 uA, N64_63 -182.1, Vom1 -38.0, Vop1 -36.8, N3a4a +34.9, N3b4b +33.8.
free 모드에서 출력 Vop/Vom 은 1.8 V 레일, Vom1/Vop1 ~0.08 V(예측 0.677) -- 엔진 동작점이 자기일관적 DC 해로 실현되지 않는다는 시제품 결론과 같다.

## 3. 시제품 대비 수치 일치 (`prototype_comparison.json`)

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

허용오차 값 전부, `sat_margin_V`, `off_current_A`, 엔진 gain 정의(단 이득 합 vs MNA) 중 어느 것을 SPICE gain 과 대조할지,
PM 정의(개루프 A vs beta 루프 -- current_reuse 의 Cf/Cs 는 회로에 둔 채 입력을 이상 AC 원으로 구동한다), layout W 와 sizing W 중 기준.

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
