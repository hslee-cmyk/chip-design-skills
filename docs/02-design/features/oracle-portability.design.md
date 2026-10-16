---
template: design
version: 0.2.1
plan: ../../01-plan/features/oracle-portability.plan.md
plan_version: 0.5
---

# oracle-portability Design Document (card OP-0)

> **Summary**: 승인된 계획 `oracle-portability.plan.md` v0.4.2를 오라클 설계로 옮긴다. 계획의 결정은 사용자 결정 O-1·O-2, D-1~D-9이다. 이 문서가 정하는 것은 다음과 같다.
> * 3층 구조(코어 / 시뮬레이터 어댑터 / PDK·오라클 기술자)의 파일 분할과 import 금지
> * 회로 IR, 해석 요청, 정규화 결과의 형식
> * 어댑터 능력 선언 스키마
> * 오라클 기술자 스키마(엔진 선언 sha256 참조, D-9)와 네이티브 MC 켜는 법
> * 능력 확인 PC-1~PC-10의 벤치·규칙·기록 형식
> * 결정적 섭동 진단 경로의 배선
> * 옛 코드 삭제 목록과 대체 배선표
> * 완료 조건별 test 목록
> * 상위 문서 개정 문안(계획 N3.7)
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (design 작성자 역할)
> **Status**: design 초안 v0.2.1 (2026-10-16). 독립 검증과 사용자 승인 전이다.
> * v0.2.1: 사용자 결정 O-4("TR-0T 승인, X-D4 권고대로 해")로 X-D4를 수용했다. offset-trim TR-0T design이 master에 병합됐다(T-40). 그래서 PC-10과 `dc_tolerance_undeclared`의 대조 기준은 master `offset-trim.design.md` §20이다.
> * v0.2 반영 1: offset-trim design TR-0T(`trim-design-r1`, 미병합)가 G-15를 닫았다. 그래서 PC-10을 정의한다(§12.2, 기준은 새 입력 칸 `output_reference`로 받는다, §11.1).
> * v0.2 반영 2: 사용자 결정 T-39로 trim 잔여 수렴 분해능 = 오라클 DC 풀이 허용오차의 입력 환산 전파값이 됐다. 그래서 DC 풀이 허용오차를 반드시 선언하게 하고, 그 전파값을 결과에 낸다(§6, §8.3, §13.4).
> * v0.1 멈춤 항목 DV-1·DV-2는 사용자 결정 O-3으로 닫혔다. DV-1 (가)는 계획 v0.5(`oport-plan-r1`)에 반영됐고, DV-2 상위 문서 개정은 별도 card(`gb-oracle-rev`)다(§19.2).
> **기준**: 코드 인용은 base `6093d07`(worktree `wt/oport-design`)의 `파일:줄`이다. 경로 약어는 계획 N0과 같다: `O/` = `skills/analog-gmid-design/tools/spice_oracle/`, `E/` = `skills/analog-gmid-design/gmid_engine/`, `A/` = `skills/analog-gmid-design/assets/`. 계획 인용은 `P N3.5`, `P D-7` 식으로 쓴다.
> **이력**: [oracle-portability.design.history.md](oracle-portability.design.history.md)

---

## 0. 문서 안내

* **담는 것**: 계획 결정을 오라클 구조로 옮긴 규칙, 자료 형식, 함수 서명, 실패 코드, 파일 분할, card별 범위, test 목록, 상위 문서 개정 문안.
* **담지 않는 것**: 경위(history 몫)와 수치 상수. 허용 폭은 시뮬레이터 해 정확도 선언(입력 `testbench.options` 또는 어댑터 보정값), MC 표본 수 규칙, 기술자가 원본 파일에서 계산한 값에서만 온다(P N0 값 원칙).
* **이름 원칙**: 회로·PDK·시뮬레이터 이름은 '사례'로만 쓴다. 코어 규칙·스키마 필드 이름에는 넣지 않는다.
* **측정 대기**: OP-1(검증자 측정)이 정해야 하는 칸은 '**측정 대기**'로 두고 값이나 하나의 안을 고르지 않는다. 목록은 §19.3에 있다.
* **오케스트레이터 기본안**: 계획이 정하지 않은 세부를 이 문서가 정할 때 '(기본안)'으로 표시한다. 목록은 §19.1에 있다.
* **용어**: 계획 N0.1을 그대로 쓴다. 이 문서가 더하는 용어는 아래와 같다.

| 용어 | 정의 |
|---|---|
| 벤치 | 코어가 만든 회로 IR 하나와 해석 요청 목록의 묶음. 어댑터 실행 한 번의 단위다 |
| 테스트벤치 원소 | 본 회로 밖에서 측정을 위해 코어가 더하는 원소. 레일 전압원, DC servo, choke, 결합 C, AC 여기원, 감지원, Middlebrook 주입원, 고정 전압원이 있다 |
| 결과 묶음 | 어댑터가 벤치 하나에 대해 돌려주는 정규화 결과(§6)의 묶음 |
| 진단 벡터 | 소자 × 기술자 진단 변수마다 값을 정한 결정적 섭동 입력(§13) |
| 기술자 지문 | 오라클 기술자 파일 sha256 + 그것이 참조한 엔진 선언 sha256 + 기술자가 직접 가진 원본 파일 sha256 묶음 |
| 어댑터 지문 | 어댑터 이름 + 어댑터 코드 지문(어댑터 패키지 `.py` 파일 sha256 묶음) + 실행 파일 sha256 + 읽은 시뮬레이터 판 |

---

## 1. 입력·원칙·선행 전제

### 1.1 확정 결정(인용)

| ID | 요지 | 이 문서에서 쓰는 곳 |
|---|---|---|
| T-31·T-33 | 오라클은 공정·시뮬레이터 무관. 능력 확인은 공정 무관 방법론 | 전체 |
| O-1 | 네이티브 MC, PC-4 삭제(크기 = TR-7 §17-1 비교), PC-3 유지, OP-1에서 네이티브 MC 소자별 독립 먼저 확인, 결정적 섭동은 진단 전용 | §10.4, §12, §13 |
| O-2 | X-15(엔진 σ 기하 전제는 TR-7 비교로 잡음)와 X-17(MC 연속값 동일성 제외) 수용 | §17.3 |
| D-1 | C10 판정 규칙은 코어, 시뮬레이터 안 조기 종결은 어댑터 능력, 능력이 없으면 전체 창 + 코어 사후 판정 | §8.4 |
| D-2 | 생성기 이전 범위 포함, 옛 생성기는 출처 보존본 | §15.3 |
| D-3 | 실제 두 번째 시뮬레이터는 범위 밖, stub 어댑터로 측정 | §3.3, §18 |
| D-4 | bin 경계 규칙 = LUT 생성 실행에 묶은 선언 | §16 |
| D-5 | 새 입력 형식, 옛 형식 거부 | §11 |
| D-6 | 모델 오차·`verified_by`를 능력 기록 id에 묶음 | §17 N3.7 문안 |
| D-7 | 능력 기록은 MC·온도 계층에만, 공칭은 모델 묶음 자동 대조 | §12.5, §12.6 |
| D-8 | 실제 두 번째 PDK는 완료 조건 아님 | §12.7 |
| D-9 | 오라클 기술자는 별도 파일, 엔진 선언 sha256 참조, 엔진 무변경 | §10 |
| T-35 | offset-trim G-14 = 네이티브 MC 표본 안(결정적 벡터 불필요). PC-11 철회 | §12.2 |
| S-7 | 계획과 다른 결정은 계획부터 | §19.2 |

### 1.2 원칙과 이 문서의 강제 장치

| 원칙 | 강제 장치 |
|---|---|
| 코어 무방언·무PDK(P FR-P1) | §3.2 import 금지 test, §18 완료 조건 1 test(검증자 소유 토큰 목록) |
| 상수 발명 금지(P NFR-P2) | §14 옛 리터럴 처리표. 새 판정 상수 없음. 보정값은 출처 칸 필수(§8.3) |
| 만들면 배선(P NFR-P4) | §15 대체 배선표, §13 진단 경로 진입점, 완료 조건 7 test |
| 작성자 ≠ 검증자(P NFR-P5) | 기준선·토큰 목록·입력 변환·능력 기록·동일성 판정의 주체를 검증자로 고정(§18.2) |
| fail-closed(P NFR-P6) | §7 오류 코드, §12.6 게이트, §11.3 옛 형식 거부 |
| 순차 실행(P NFR-P7) | §8.2 실행 계약: 어댑터는 병렬 실행을 하지 않는다 |
| 재계산 재사용(P NFR-P8) | §9 캐시 키 |

### 1.3 선행 전제

* 상위 문서 개정(P N3.7)은 아직 반영되지 않았다(base `6093d07`의 상위 계획에 `run_ngspice_op_ac`가 남아 있다). 이 문서 §17은 그 개정 **문안**만 낸다. 반영은 상위 계획 개정 절차(독립 검증 → 사용자 승인)를 거친다. 구현 card(OP-2~)의 공통 착수 조건이다(P N5.1).
* offset-trim G-15(출력 기준 DC)는 base에서는 열려 있었지만, offset-trim design TR-0T(`trim-design-r1`, 미병합)가 닫았다(선언 기준을 온도 무관하게 그대로, 없으면 `reference_undeclared`). 그래서 v0.2에서 PC-10을 정의했다(§12.2). OP-6 착수는 그 design 병합 뒤다.

---

## 2. 실측 사실(base `6093d07`, 읽기만)

| ID | 사실 | 근거 |
|---|---|---|
| S-1 | 오라클 `*.py` 8개, 합계 5114줄. 진입점: `oracle_netlist.main`, `oracle_simulate.main`, `oracle_noise.main`, `oracle_offset_mc.main`, `oracle_swing.main`, `oracle_compare.main`, `oracle_run.main`, `legacy_adapter.main` | `O/*.py` |
| S-2 | `oracle_run.run_one`: `write_netlists` → `simulate` → (free이고 입력 블록이 있을 때) `noise_measure`·`offset_mc_measure`·`swing_icmr_measure` → `<stem>.sim.json` → `compare` → `<stem>.compare.*` | `O/oracle_run.py:39-61` |
| S-3 | `simulate`의 결과 칸: `devices`, `nodes`, `rail_current_A`, `hold_current_A`, `ngspice_rc`, `cache`, `log`, `log_errors`, `op_ok`, `ac`, `ac_file`, `ratio`, `rout`, `loop`, `cm_loop`(+안정성 칸). 막힌 넷리스트는 `skipped` | `O/oracle_simulate.py:1263-1300` |
| S-4 | `offset_mc_measure`: 표본 0 = 변수 0의 기준 해, 표본 1..n = 소자·변수마다 `rng.standard_normal() * 1e-6 / sqrt(n_fingers)`(`rng = numpy.random.default_rng(seed)`, 소자 순서 = 입력 `devices` 순서, 변수 순서 = `mismatch_vars` 결과 순서). V_os = (V_out − V_out,0)/A − (V_id − V_id,0), A = `.ac` 첫 점의 실수부(허수부가 `1e-3·|h0|` 이하일 때만). 출력 `mismatch_vars`에 소자별 변수 목록이 남는다 | `O/oracle_offset_mc.py:109-196` |
| S-5 | 표본 수 규칙 `sample_count(r)` = ceil(1 + 1/(2 r²)) | `O/oracle_offset_mc.py:43-49` |
| S-6 | 입력 스키마 최상위 칸: `schema, circuit, process, rails, devices, sources, passives, feedback_passives, cm_loop_passives, cm_output_loop, feedback_passives_basis, bias_voltages, ports, predictions, acceptance, testbench, judge, noise, offset_mc, swing_icmr, topology, provenance`. 필수: `circuit, process, rails, devices, ports, predictions, testbench`. `process` 필수: `lut_npz, models`. `models[kind]` 필수: `subckt, includes, op_probe` | `O/oracle_input.schema.json` |
| S-7 | smoke 입력의 pmos `includes`에 `models/parameters/lod.spice`가 있다. 이 파일은 엔진 PDK 선언 `sources`에 없다(엔진 선언 sources: tech LEF, periphery rules, nfet·pfet tt 모델 카드, mismatch 파일 둘, MIM·poly R+C 파라미터, `models/all.spice`) | `O/smoke/current_reuse_telescopic_ota.sizing.engine.oracle_input.json` `process.models.pmos.includes`, `A/sky130_pdk_decl.json` `sources` |
| S-8 | 옛 리터럴 상수: `NYQUIST_K_MAX = 10`, `NOISE_TOP_K_MAX = 8`, `INTEGRAL_K_MAX = 4`, `ZOOM_POINTS = 7`, `ZOOM_ROUNDS = 8`, `WRDATA_NUMDGT = 8`, `_NGSPICE_DEFAULT_TOL`, 차동 이득 실수 판정 `1e-3`. 물리 상수 `_K_B`·`_Q_E`(CODATA) | `O/oracle_simulate.py:398-402, :750`, `O/oracle_noise.py:44-45`, `O/oracle_swing.py:43-44`, `O/oracle_netlist.py:727`, `O/oracle_offset_mc.py:137` |
| S-9 | 원소 이름 접두사 규약: `CIRCUIT_PREFIXES`(`X`, `Rp_`, `Cp_`, `Isrc_`, `Vsrc_`, ...), `TESTBENCH_PREFIXES`(`Vrail_`, `Efb_`, `Vofs_`, `Lfb_`, `Vdc_`, `Ldc_`, `Cac_`, `Vac_`, `Vbias_`, `Vhold_`, ...), `CHOKE_PREFIXES` | `O/oracle_netlist.py:56-60` |
| S-10 | 오라클 test 29개 `.py`(fixture helper `u6_toy5t.py` 포함). 텍스트 단언 파일은 계획 F-15 기준 test 13개 + helper 1개 | `O/tests/`, P F-15 |
| S-11 | 창당 실행 시간 보정값 `stability_transient.wall_s_per_window` = 306.1 s, 측정 방법·코퍼스·기계 메모가 함께 있다(ngspice-46, 2026-10-08) | `O/oracle_config.json` |

---

## 3. 패키지·파일 분할과 import 금지

### 3.1 디렉터리(기본안: P N0.1의 `O/core/`·`O/adapters/<이름>/` 고정을 따른다)

```
O/
  oracle_run.py            진입점(CLI). 입력 검증 -> 기술자 읽기 -> 어댑터 선택·주입 -> 코어 측정 -> 판정 -> 출력
  oracle_capability.py     진입점(CLI). 능력 확인 실행(검증자용) -> 능력 기록
  oracle_input.schema.json 입력 스키마(새 형식, §11)
  core/                    코어 모듈 집합(완료 조건 1의 검사 대상, .py만)
    ir.py                  회로 IR 자료형(§4)
    requests.py            해석 요청 자료형(§5)
    results.py             정규화 결과 자료형·오류 코드(§6, §7)
    adapter_api.py         어댑터 계약(Protocol)·능력 선언 자료형(§8)
    descriptor.py          오라클 기술자 읽기·지문·검증(§10)
    build_circuit.py       입력 -> 본 회로 IR(free/forced/iso), Z1(omit/short)
    build_benches.py       파생 벤치(β 루프, CM 루프, ratio, rout, iso, pz 개루프, noise, MC, swing, C10 과도)
    identity.py            C15 topology 대조(IR 기준)
    measures_ac.py         ac_measures·pm_crosscheck·loop_gain·ratio/rout 수학
    stability.py           Nyquist·창 판정·조기 종결 규칙·tran 계획 수학·stability_judgement
    noise_math.py          잡음 밀도·적분·꼬리 판정
    mc_math.py             표본 수·V_os 식·σ 추정·진단 벡터 적용 순서(§13)
    swing_math.py          경계 탐색·창 계산
    compare.py             판정·비교(옛 oracle_compare 수학)
    capability.py          PC 벤치·판정·기록(§12)
    bundle.py              모델 묶음 비교 규칙(§12.5)
    cache.py               실행 캐시 키 원칙(§9)
  adapters/
    ngspice/               첫 어댑터(사례)
      __init__.py          어댑터 객체(능력 선언 포함)
      dialect.py           IR·요청 -> 방언 텍스트
      run.py               실행(subprocess는 여기만)
      read.py              결과 읽기·내부 벡터 이름 대응·극성 정규화
      errors.py            로그 -> 오류 코드
      calibration.json     보정값(§8.3, 옛 oracle_config.json·_NGSPICE_DEFAULT_TOL·WRDATA_NUMDGT 출처 포함)
  descriptors/
    <pdk>.oracle_descriptor.json   오라클 기술자(사례: sky130, §10)
  capability/
    <기술자 지문>__<어댑터 지문>.json  능력 기록(검증자 생성, §12.4)
  tests/
    core/                  코어 test(stub 어댑터, 텍스트 단언 금지)
    adapters/ngspice/      어댑터 test(손 넷리스트 독립 기준 포함)
    stub_adapter.py        stub 어댑터(test 작성자 소유, §3.3)
    fixtures/              손 모델 기술자 픽스처 포함
```

* 옛 파일 `oracle_netlist.py`, `oracle_simulate.py`, `oracle_noise.py`, `oracle_offset_mc.py`, `oracle_swing.py`, `oracle_compare.py`, `oracle_config.json`은 대체 card에서 삭제한다(§15). 각 진입점의 CLI 기능은 `oracle_run`의 하위 명령으로 합친다(기본안). 이유는 진입점 정본을 하나로 두기 위해서다. 단 `--bias`별 단독 실행처럼 test가 쓰는 기능은 하위 명령으로 남긴다.
* `legacy_adapter.py`·`legacy_testbench.json`은 `O/` 최상위에 남는다(생산자, §11.4).

### 3.2 import 금지(완료 조건 1)

| 모듈 | import 해도 되는 것 | 금지 |
|---|---|---|
| `O/core/*` | 표준 라이브러리(`subprocess` 제외), numpy, `O/core/*` | `O/adapters/**`, `subprocess`, `O/oracle_*.py` 진입점, 엔진(`gmid_engine`) |
| `O/adapters/<이름>/*` | `O/core/adapter_api`, `O/core/ir`, `O/core/requests`, `O/core/results`, 표준 라이브러리 | 다른 어댑터, `O/core`의 측정·판정 모듈, 엔진 |
| 진입점 | 위 전부 | 엔진 |

* `O/core/` 안에는 `.py`만 둔다(`__pycache__` 제외, P N5.3-1).
* 코어가 `O/core/` 밖에서 여는 파일은 셋뿐이다. 입력 JSON, 기술자 JSON(과 그것이 sha256으로 가리키는 파일), 결과 출력 디렉터리. 이 목록 밖의 열기는 test가 거부한다(§18 T1-4).

### 3.3 stub 어댑터(D-3, G-10)

* 위치는 `O/tests/stub_adapter.py`이고 test 작성자가 소유한다. 코어 interface(§5·§6·§8)만 보고 쓴다.
* 능력 선언: `op`, `ac`, `pz`, `tran`(선형 시간 해), `noise`(저항 열잡음만). 선언하지 않는 것: `tran_early_stop`, `mc_native`, `mc_diagnostic`, `op_sweep`, `noise_device_contrib`.
* MOS는 입력 `predictions.devices`의 gm·gds·(cgg 등 있으면) 값으로 선형 스탬프한다. 비선형 op는 풀지 않는다.

| 해석 | stub 처리 | test 종류 |
|---|---|---|
| op(선형), ac, β 루프, ratio, rout | MNA 해석해 | stub 실행 |
| C10 과도 | 선형 시간 해(성장 회로 = 선형 RHP 극 IR) | stub 실행(전체 창 경로, D-1) |
| pz | 해석해 극점 | stub 실행 |
| noise | 저항 4kT/R만 | stub 실행 / MOS 기여는 '능력 없음 거부' test |
| MC(네이티브·진단) | 미선언 | '능력 없음 거부' test |
| swing·ICMR(op 스윕) | 미선언 | '능력 없음 거부' test |

---

## 4. 회로 IR(G-1, G-12)

### 4.1 자료형(`core/ir.py`, frozen dataclass)

```
Net(name: str)                                   # 입력 넷 이름 그대로. 0 넷은 Ground 상수
Mos(name, kind, d, g, s, b, L, finger_w, n_fingers, diffusion: Diffusion|None, lod: Lod|None)
Resistor(name, a, b, value)     Capacitor(name, a, b, value)     Inductor(name, a, b, value)
VSource(name, p, n, dc, ac_mag=0.0, ac_phase=0.0, tran: Pulse|None=None)
ISource(name, p, n, dc, ac_mag=0.0)
Vcvs(name, p, n, cp, cn, gain)                   # 옛 Efb_
Probe(name, kind='current', a, b)                # 0 V 감지원(옛 Vhold_ 등)
Diffusion(ad, as_, pd, ps)      Lod(sa, sb, sd)  Pulse(v1, v2, td, tr, tf, pw, per)
Circuit(elements: tuple, role: dict[name -> 'circuit'|'testbench'], meta: dict)
```

* **원소 종류는 필드다.** 이름 접두사(S-9)는 방언 규약이라 어댑터가 정한다. 그래서 IR 이름은 입력 이름 그대로 쓰고, 테스트벤치 원소 이름은 코어가 `tb:<용도>:<대상>` 형태로 만든다(예: `tb:servo:out`). 어댑터는 그 이름을 방언에서 쓸 수 있는 이름으로 바꾸고 대응표를 결과에 싣는다(§6).
* **역할 표**: `role`은 원소가 본 회로인지 테스트벤치인지 담는다. C15 topology 대조(`core/identity.py`)는 `role == 'circuit'` 원소만 topology와 비교한다. 지금은 넷리스트 텍스트를 다시 파싱해서 하지만(`parse_netlist_elements`, `O/oracle_netlist.py:1105`), 이 경로를 대체한다.
* **대소문자**(G-12): 코어는 넷·원소 이름을 그대로 둔다. 어댑터 능력 `case_insensitive_names`가 참이면, 코어는 벤치를 넘기기 전에 이름을 소문자로 접었을 때 충돌하는지 검사하고 충돌하면 거부한다(`ir_name_collision`). C15 대조는 IR 이름 기준이라 대소문자 접기의 영향을 받지 않는다. 옛 `_Nets`의 충돌 규칙(`O/oracle_netlist.py:86-110`)은 이 검사로 대체한다.

### 4.2 IR 생성기(`core/build_circuit.py`, `core/build_benches.py`)

| 옛 기능(텍스트 생성) | 새 IR 함수 | 비고 |
|---|---|---|
| `build_netlist(inp, bias, ...)` 본 회로 부분 | `circuit_ir(inp, bias) -> Circuit` | free/forced/iso, `apply_z1` 포함 |
| 같은 함수의 `.control` 부분 | `main_requests(inp, bias, meta) -> tuple[Request]` | §5 |
| `stability_op_netlist`·`stability_netlist` | `stab_benches(circuit, plan, ...)` | choke → 고정 전류원·초기 조건은 IR 원소와 요청 조건으로 |
| `open_loop_parts`·`pz_netlist`·`openloop_tran_netlist` | `pz_bench`, `openloop_tran_bench` | 동작점 값으로 개루프를 다시 만드는 규칙은 코어(회로 이론), pz 신뢰는 §8.5 |
| `_rout_runs`·`_ratio_runs`·`_loop_tail` | `rout_requests`, `ratio_requests`, `loop_requests` | 여기 전환(`alter @..[acmag]`)은 요청의 `excitation` 덮어쓰기로 바꾼다(§5) |
| `build_iso_netlist` | `iso_bench` | |
| `build_mc_netlist`(래퍼 subckt·`alterparam`) | 삭제. 네이티브 MC 요청(§5 `McNative`) + 진단 요청(§13) | O-1 |
| `_Sweeper`(`alter dc` + `op`) | `OpSweep` 요청(§5) | |
| `_refine_text` | 같은 IR에 좁은 `Ac` 요청을 다시 보냄 | |

---

## 5. 해석 요청(G-2, `core/requests.py`)

```
Condition(temp_c: float, corner: str)                          # 모든 요청에 붙는다. 기본 = LUT 메타(§11.2)
Excitation(overrides: tuple[(source_name, field, value)])       # ac_mag·dc 덮어쓰기(옛 alter)
Op(id, cond, exc=(), outputs: OpOutputs)                        # OpOutputs = (devices: names|'all', nodes, currents)
Ac(id, cond, exc, f_start, f_stop, points_per_decade|None, f_list|None, outputs: tuple[Expr])
Noise(id, cond, exc, out: Expr, src: source_name, f_points, contrib: bool)
Tran(id, cond, exc, plan: TranPlan, outputs: tuple[Expr], save_only: bool, early_stop: EarlyStopRule|None)
Pz(id, cond, exc, in_pair, out_pair, kind='voltage')
OpSweep(id, cond, base_exc, points: tuple[Excitation], outputs)
McNative(id, cond, n_samples, seed, outputs, keep_identity: bool)     # 네이티브 MC(§10.4)
McDiagnostic(id, cond, vectors: tuple[DiagnosticVector], outputs)      # 결정적 섭동(§13), 판정 금지
Expr = NodeV(net) | DiffV(net_p, net_n) | BranchI(element) | Ratio(Expr, Expr)
```

* 요청은 방언을 모른다. 출력은 IR 넷·원소 이름의 식(`Expr`)이다. 옛 `let hout = ...` 같은 방언식은 어댑터가 만든다.
* `EarlyStopRule`은 코어 규칙 자체(창 경계, floor', reltol, g↑·g↓·한계 사이클 판정에 필요한 값)를 담는 자료다. 능력이 있는 어댑터는 이것을 방언 스크립트로 옮긴다. 능력이 없는 어댑터는 무시하고 전체 창을 실행한다(§8.4).
* `keep_identity`: 같은 `seed`·같은 `n_samples`로 다른 `Condition`(온도)을 요청하면 같은 표본(같은 불일치 값)을 재야 한다는 요구다(PC-6, offset-trim N3.8.2). 어댑터가 이 능력을 선언하지 않으면 코어가 거부한다.

---

## 6. 정규화 결과(G-2, `core/results.py`)

```
RunStatus(rc, timed_out: bool, error: ErrorCode|None, log_excerpt: tuple[str], cache_hit: bool)
OpTable(devices: {name: {param: value}}, nodes: {net: V}, currents: {element: A}, resolution: Resolution)
FreqSeries(f: array, values: {expr_key: complex array}, resolution: Resolution)
NoiseResult(total_in, total_out, density: FreqSeries|None, contrib: {element: {source_kind: value}}|None, resolution)
TimeSeries(t: array, values: {expr_key: array}, stopped_early: bool, windows_done: int, resolution)
Poles(values: tuple[complex], status: 'ok'|'failed', resolution)
SweepResult(points: tuple[OpTable|None])
McResult(samples: tuple[OpTable|None], seed, identity_kept: bool)
Resolution(reltol, abstol: {quantity: value}, data_rel: float|None, source: 'input_options'|'adapter_declared')
                                   # DC 풀이 허용오차(reltol, vntol, abstol)는 이 칸이 정본. 값이 없으면 어댑터가 결과를 내지 않는다(§8.3)
ResultBundle(bench_id, adapter_fp, descriptor_fp, status: RunStatus, by_request: {request_id: result}, name_map: {ir_name: dialect_name})
```

* **극성 정규화는 어댑터 몫이다**(F-9). `OpTable.devices[*]`는 README '크기 규칙'(선언 단자 방향 부호, ID 부호 포함, VSB 양수)을 이미 따른다. 옛 `oracle_compare.signed_id`(`O/oracle_compare.py:226`)는 ngspice 어댑터 `read.py`로 옮긴다.
* op 파라미터 이름은 코어 공통 이름(`id, gm, gds, vth, vdsat, vgs, vds, vbs`)이다. 어댑터는 기술자 `model_family`(§10)에 맞는 표로 자기 시뮬레이터 이름과 대응시킨다. 대응이 없는 파라미터는 `None`이고 조용히 다른 값을 넣지 않는다.
* 결과 JSON에는 그 실행에 쓴 DC 풀이 허용오차(`Resolution`의 reltol·vntol·abstol과 출처)를 그대로 싣는다. offset-trim trim 잔여 수렴 분해능(T-39)은 이 값을 입력 환산으로 전파해 얻는다(§13.4).
* `Resolution`은 판정 분해능 계산(§8.3, 계획 N4-2)의 입력이다. 옛 `data_rel_resolution`·`mp_resolution`·`solver_floor`·`reltol_of`의 수학은 코어에 남고, 자릿수·기본 허용오차 값만 어댑터가 준다.

---

## 7. 오류 분류(G-4)

| 코드 | 뜻 | 낸 곳 |
|---|---|---|
| `sim_convergence_failed` | DC·과도 수렴 실패 | 어댑터 |
| `sim_singular_matrix` | 특이 행렬 | 어댑터 |
| `sim_timestep_too_small` | 시간 걸음 실패 | 어댑터 |
| `sim_timeout` | 실행 시간 상한 초과 | 어댑터 |
| `sim_model_not_found` | 모델·bin을 못 찾음 | 어댑터 |
| `sim_failed_other` | 그 밖(로그 발췌 첨부) | 어댑터 |
| `adapter_capability_missing` | 요청에 필요한 능력 미선언 | 코어 |
| `adapter_calibration_missing` | 보정값 없음(예: 창당 상한, §8.3) | 코어 |
| `ir_name_collision` | 대소문자 접기 충돌(§4.1) | 코어 |
| `oracle_input_format_old` | 옛 입력 형식(D-5) | 코어 |
| `pdk_descriptor_stale` | 기술자가 참조한 sha256과 실제 파일 sha256이 다름 | 코어 |
| `model_bundle_mismatch` | 모델 묶음 비교 규칙 위반(§12.5) | 코어 |
| `lut_model_provenance_missing` | LUT 슬라이스 meta 모델 기록이 빈 표 | 코어 |
| `oracle_capability_unverified` | 필요한 능력 기록 없음 | 코어 |
| `oracle_capability_stale` | 능력 기록 지문 불일치 | 코어 |
| `mc_method_unsupported` | 선언되지 않은 MC 방법 | 코어 |
| `diagnostic_not_a_gate` | 진단 결과를 판정 입력으로 쓰려는 호출 | 코어(§13.3) |
| `dc_tolerance_undeclared` | 입력 `simulator.options`에도 어댑터 보정값에도 DC 풀이 허용오차(reltol·vntol·abstol) 선언이 없음(§8.3) | 코어 |
| `reference_undeclared` | V_sys 측정(PC-10, 범위 판정)에 필요한 입력 `output_reference`가 없음(§11.1). offset-trim design §20.1과 같은 사유 이름 | 코어 |

* 옛 로그 정규식(`error|fatal|singular|abort`)과 `.pz` 실패 표지(`giving up|iteration limit|singular matrix`)는 ngspice 어댑터 `errors.py`의 사례 표로 옮긴다. 정확한 대응표는 OP-3 구현 몫이고, 기준선 로그(OP-1)로 대조한다.

---

## 8. 어댑터 계약·능력·보정(G-3, G-13)

### 8.1 계약(`core/adapter_api.py`)

```
class Adapter(Protocol):
    name: str
    def capabilities(self) -> Capabilities
    def calibration(self) -> Calibration
    def fingerprint(self) -> AdapterFingerprint              # 이름, 코드 지문, 실행 파일 sha256, 시뮬레이터 판
    def run(self, circuit: Circuit, requests: tuple[Request], descriptor: Descriptor,
            work_dir: str, timeout_s: float|None, cache_dir: str|None) -> ResultBundle
    def model_bundle(self, circuit: Circuit, descriptor: Descriptor, cond: Condition) -> {path: sha256}   # §12.5
```

### 8.2 실행 계약

* `run`은 벤치 하나를 순차로 실행한다. 어댑터가 프로세스를 병렬로 띄우지 않는다(P NFR-P7).
* 실행 파일 경로는 입력 `simulator.exe`나 CLI `--sim-exe`로만 받는다. 코드에 경로를 두지 않는다.
* 어댑터는 판정하지 않는다. 판정에 필요한 분해능은 `Resolution`으로 넘긴다.

### 8.3 능력·보정 스키마(어댑터 패키지 안 `calibration.json`과 `capabilities()`)

```
Capabilities = {
  "op": bool, "ac": bool, "noise": bool, "noise_device_contrib": bool, "tran": bool,
  "tran_early_stop": bool, "pz": bool, "op_sweep": bool, "temperature": bool,
  "mc_native": bool, "mc_keep_identity": bool, "mc_diagnostic": bool,
  "case_insensitive_names": bool, "model_families": [str]
}
Calibration = {   # 모든 값은 출처 칸 필수
  "default_tolerances": {"reltol": {value, source}, "vntol": {...}, "abstol": {...}},
  "data_digits": {value, source},
  "wall_s_per_window": {value, safety_factor, measured_*..., source},   # 옛 oracle_config.json 그대로 이전
  "simulator_version_probe": {how, source}
}
```

* ngspice 어댑터의 보정값은 지금 코드 값을 그대로 옮긴다. 출처 칸도 함께 옮긴다. 출처가 없던 값의 처리는 §14에서 정한다.
* **DC 풀이 허용오차(T-39)**: 쓰는 값의 순서는 (1) 입력 `simulator.options`의 선언값, (2) 어댑터 `default_tolerances` 선언값(출처 필수: 시뮬레이터 문서 쪽 번호 또는 측정 조건)이다. 둘 다 없거나, (2)에 출처가 없으면 실행하지 않고 `dc_tolerance_undeclared`로 멈춘다. 시뮬레이터 내부 기본값을 선언 없이 쓰지 않는다(숨은 상수 금지). 그래서 지금 `_NGSPICE_DEFAULT_TOL`(S-8)은 출처(R6 매뉴얼 쪽)가 채워져야 어댑터 선언값으로 쓸 수 있다. 채워지기 전에는 입력 `simulator.options`에 값이 있어야 한다(§14).
* 이 허용오차는 시뮬레이터 성질이지 PDK 성질이 아니므로 오라클 기술자에는 두지 않는다(§10).
* `wall_s_per_window`가 없는 어댑터에서 C10 과도를 요청하면, 사용자 `--timeout-s`가 있을 때만 실행하고 없으면 `adapter_calibration_missing`이다(P N3.3).

### 8.4 C10 조기 종결(D-1, G-13)

| 어댑터 능력 | 실행 | 판정 |
|---|---|---|
| `tran_early_stop` 참 | 어댑터가 `EarlyStopRule`을 방언으로 옮겨 시뮬레이터 안에서 창 단위로 멈춘다 | 코어가 결과 시간열로 같은 기준을 다시 검증(지금 `transient_decision`과 같다) |
| 거짓 | **측정 대기(G-13)**: (가) tstop까지 전체 창을 한 번 실행하고 코어가 사후 판정 / (나) 창 j마다 tstop = t_end + j·W로 처음부터 다시 실행 | 코어가 같은 기준 적용 |

* 어느 쪽을 기본으로 할지는 OP-1 기준선의 창당 시간으로 비용을 재고 정한다. 이 문서는 고르지 않는다.
* 창 판정 규칙의 정본은 계약 문서와 design 40 §4다. 이 문서는 위치(코어)만 바꾸고 식은 바꾸지 않는다.

### 8.5 회로 이론 규칙 대 회피책 분리표(G-3)

| 항목 | 지금 | 분류 | 새 위치 |
|---|---|---|---|
| Nyquist N, 창 판정, 한계 사이클, 조기 unstable | 코어 수학 + nutmeg 스크립트 | 회로 이론 | 코어 `stability.py`(스크립트는 어댑터 능력의 방언 표현) |
| pz 결과 신뢰: '독립 증거(개루프 과도)로 확인될 때만 P 사용' | `stability_judgement`·`pz_validate` | 회로 이론(일반 규칙) | 코어 |
| 'BSIM4 대회로 `.pz`가 거짓 RHP 극을 낸다'는 사실 | 주석·README | 시뮬레이터 결함 사실 | 어댑터 `capabilities()`의 `pz` 신뢰 범위 메모. 판정은 위 일반 규칙이 한다 |
| 개루프를 동작점 값으로 다시 만들기 | `open_loop_parts` | 회로 이론(같은 루프 절단) | 코어 `build_benches.py` |
| β 루프 choke 값(입력 `loop_dc_choke_H`) | 입력·테스트벤치 | 테스트벤치 정의(사용자 입력) | 코어(값은 입력) |
| `>`·`<` 리다이렉션 회피, `stop when time > x`, `delete all` | nutmeg 스크립트 | 방언 회피책 | 어댑터 `dialect.py` |
| tmax·n_pp(`tran_plan`) | 코어 식 + LTE 걸음 제어 전제 | 수학은 회로 이론, '최대 걸음 지정이 실제 걸음을 묶는다'는 어댑터 의미 | 수학 = 코어. 어댑터는 `tran` 능력에 '최대 걸음 지정 지원'을 선언하고, 지원하지 않으면 코어는 `adapter_capability_missing` |
| `WRDATA_NUMDGT`(가수 자릿수 = numdgt+1, ngspice-46 실측) | 상수 | 어댑터 보정값 | `calibration.json` `data_digits` |
| `_NGSPICE_DEFAULT_TOL` | 상수 | 어댑터 보정값(시뮬레이터 문서 기본값) | `calibration.json` `default_tolerances` |

---

## 9. 실행 캐시 키(G-7)

* **원칙(코어)**: 키 = sha256(어댑터 지문 ∥ 방언 텍스트 바이트 ∥ 모델 묶음 sha256 정렬 목록 ∥ 실행 인자). 같은 키는 결과를 재사용한다. 키에 없는 입력이 결과를 바꾸면 결함이다.
* **어댑터 몫**: include 문법을 따라 모델 묶음을 재귀로 모으는 일(지금 `_model_files`·`_INC`, `O/oracle_simulate.py:62-90`), 방언 텍스트 생성.
* 옛 `run_cache_key`(`O/oracle_simulate.py:86`)는 이 원칙으로 대체한다. 키 구성이 바뀌므로 옛 캐시 디렉터리는 재사용하지 않는다.

---

## 10. 오라클 기술자(G-5, G-9, D-9)

### 10.1 위치와 엔진 선언 참조

* 파일: `O/descriptors/<pdk>.oracle_descriptor.json`, 스키마 이름 `oracle_pdk_descriptor/1`(기본안).
* 엔진 선언 참조: `engine_decl = {path, sha256}`. 코어가 읽을 때 파일 sha256을 대조하고, 다르면 `pdk_descriptor_stale`이다. 엔진 선언 `sources`의 파일은 **source 키로만** 가리키고 경로·sha256을 다시 적지 않는다(P N3.4 단일 정본).
* **멈춤 항목 DV-1(§19.2)**: 오라클 넷리스트가 include해야 하는 파일 가운데 엔진 선언 `sources`에 없는 것이 있다. 사례는 pmos의 `lod.spice`(S-7)다. 계획 N3.4는 '원본 PDK 파일의 경로·sha256 정본은 엔진 선언 하나'라고 했고, D-9는 엔진 선언을 바꾸지 않는다고 했다. 둘을 함께 지키면 이 파일을 넣을 곳이 없다. 이 문서는 아래 안을 **임시로** 적는다. S-7에 따라 계획 개정 뒤에 확정한다.
  * **확정(v0.2, 사용자 결정 O-3 = DV-1 (가), 계획 v0.5 N3.4 '파일마다 정본 한 곳')**: 엔진 선언에 없는 파일만 기술자 `extra_sources = {key: {path, sha256, base}}`에 둔다. 한 파일이 두 곳에 나오지 않도록 로더가 검사한다(`descriptor_source_duplicated`).

### 10.2 스키마

```
{
  "schema": "oracle_pdk_descriptor/1",
  "engine_decl": {"path": ".../sky130_pdk_decl.json", "sha256": "..."},     # 사례
  "extra_sources": {...},                                                    # 엔진 선언에 없는 파일만(O-3)
  "model_family": "bsim4",                                                   # 사례 값
  "kinds": {
    "<kind>": {
      "call_form": "subckt_wrapper" | "model_direct",
      "name": {"value": "..."} | {"expr": <엔진 선언 식 형식>},
      "inner_device": {"expr": <모델 파일에서 subckt 안 첫 MOS 소자 이름을 읽는 식>} | null,
      "geometry_unit": {"source": <엔진 선언 quantity 키>} | "si",
      "includes": [{"source": <키>, "corner_section": <선택>}],
      "polarity": "n" | "p"
    }
  },
  "corners": {"names": [...], "select": {"how": "include_path" | "lib_section", ...}},
  "temperature": {"tnom": {"source": <엔진 선언 quantity 키>}, "range_source": "spec"},
  "diffusion": {"source": <엔진 선언 lut_rule_decl quantity 키들>},
  "mc": { ... §10.4 ... },
  "diagnostic": { ... §10.5 ... }
}
```

* `inner_device`는 미병합 `ng-bridge`의 `oracle_models` 내용 판정 규칙(MOS 4단자 subckt 안 첫 M 소자, P F-16)을 식으로 옮긴 것이다. noise 기여 이름 대응(F-8)과 진단 경로가 이 값을 쓴다. 방언 경로 틀(`@m.{inst}.…`)은 기술자에 두지 않고 어댑터가 만든다.
* 엔진 선언 식 형식(원본 파일 + 패턴 + 식)을 그대로 쓰므로, 코어 `descriptor.py`는 그 형식의 읽기 함수를 **새로 쓴다**. 엔진 `read_pdk_decl`을 import하지 않는다(오라클 C1).

### 10.3 sky130 사례 값

* 사용자가 PDK 문서에서 선언하는 값이다(P N3.4). OP-2에서 값을 채울 때 사용자 확인을 받는다.
* 확정되지 않은 칸은 다음과 같다.
  * `mc` 켜는 법: **측정 대기**(OP-1 (i))
  * `extra_sources`: 엔진 선언에 없는 include 파일(사례 pmos `lod.spice`)의 경로·sha256. 값 채움은 OP-2
  * `corners`: tt 하나만 엔진 선언에 있다. 다른 코너는 범위 밖(P T-32)

### 10.4 네이티브 MC 켜는 법(O-1, G-9)

```
"mc": {
  "method": "native",
  "enable": {"how": "lib_section" | "param_switch" | "include", "value": ..., "source": <원본 근거>},
  "mismatch_only": {"global_off": {"how": ..., "value": ...}, "source": <원본 근거>},   # 전역 공정 변동 끄는 법
  "sampling": {"seed": {"how": ...}, "samples": {"how": ...}},
  "per_instance_independent": true | false,     # 선언. PC-3 (b)가 측정으로 확인
  "keep_identity_across_conditions": {"how": ...}
}
```

* 오라클은 분포·면적 의존 식을 갖지 않는다. 모델 카드가 정한다(P N3.4).
* 선언되지 않은 `method`는 `mc_method_unsupported`다.
* sky130·ngspice 사례에서 네이티브 MC가 소자별 독립인지, 어떤 방법으로 켜는지는 **측정 대기**(OP-1 (i))다. 지금 오라클이 직접 섭동 루프를 쓴 이유가 '전역 파라미터가 모든 인스턴스에 같은 값으로 평가된다'인지도 같이 잰다. 독립이 아니면 사용자 결정(그 조합만 직접 섭동 대안, O-1 (4))으로 올린다. 이 문서는 대안을 미리 설계하지 않는다.

### 10.5 진단 변수(O-1 (5))

```
"diagnostic": {
  "per_kind": {"<kind>": {"variables": {"source": <엔진 선언 mismatch_models.<kind>.parameters>},
                          "instance_param_rule": {"expr": <모델 파일에서 소자별로 덮어쓸 파라미터 이름을 읽는 식>},
                          "value_rule": {"expr": <표본 z를 파라미터 값으로 바꾸는 식, 원본 근거 포함>}}}
}
```

* 진단 경로(§13)만 쓴다. 판정·능력 기록에는 쓰지 않는다.
* sky130 사례에서 `value_rule`은 지금 코드의 `z·1e-6/√m`(S-4)을 기술자 값으로 옮긴 것이다. 근거는 엔진 선언 `mismatch_slope_geometry_unit_m`(`.option scale`)과 m이 카드 `mult`에 들어가지 않는다는 사실이다. 그래서 코드 리터럴 `1e-6`은 사라지고 기술자 식이 그 값을 원본에서 읽는다.

---

## 11. 오라클 입력 형식 변경(D-5)

### 11.1 새 `process`·`simulator` 블록

```
"process": {
  "descriptor": {"path": "...", "sha256": "..."},
  "lut_npz": "...",                       # LUT 메타(코너·온도·model_files_sha256)의 출처
  "corner": "<선택, 없으면 LUT 메타>",
  "temp_c": "<선택, 없으면 LUT 메타>"     # LUT temp_c와 다른 온도는 온도 게이트(§12.6)를 지난다
},
"simulator": {"adapter": "<이름>", "exe": "<경로>", "options": {...}},
"output_reference": {"kind": "differential"}
                  | {"kind": "net_value", "value_V": <선언값>, "source": "<출처>"}
                  | {"kind": "net", "net": "<참조 넷>"}
                  | {"kind": "rule_e_input_cm"}            # 규칙 (e): 출력 = 입력 공통모드
```

* `output_reference`(v0.2, offset-trim G-15): V_sys 측정의 출력 기준이다. 선언 기준을 온도와 무관하게 그대로 쓰고, 온도마다 다시 풀지 않는다(offset-trim design §20.1). 오라클은 이 값을 엔진 결과 JSON에서 직접 읽지 않고 입력으로만 받는다. 엔진 결과 `output_reference` 칸(offset-trim design §13)을 오라클 입력으로 옮기는 일은 입력 생산자가 한다(§11.4). 이 칸이 없는데 V_sys 측정을 요청하면 `reference_undeclared`로 멈춘다.

* `options`는 옛 `testbench.options`를 옮긴 것이다. 키 이름은 어댑터 방언이라 어댑터가 검증한다(기본안). 코어가 쓰는 해 정확도(`reltol` 등)는 어댑터가 `Resolution`으로 정규화해 돌려준다.
* 삭제 칸: `process.models`(`subckt`·`includes`·`op_probe`·`polarity`), `process.ngspice_exe`, `process.diffusion`(기술자로 이동, 소자별 `devices[].diffusion`은 유지), `testbench.options`(`simulator.options`로 이동).

### 11.2 온도·코너 해석 순서

입력 `process.temp_c`/`corner`가 있으면 그것을 쓰고, 없으면 LUT 메타 값을 쓴다. LUT 메타에 기록이 없으면(`recorded=False`) 둘 다 입력에 있어야 하고, 없으면 거부한다(`oracle_condition_missing`, 기본안).

### 11.3 옛 형식

`process.models` 또는 `process.ngspice_exe`가 있으면 `oracle_input_format_old`로 거부한다. 이중 지원은 하지 않는다(P D-5, X-5).

### 11.4 생산자

* `legacy_adapter.py`(master): `process_from_lut_generator`(`O/legacy_adapter.py:157`)를 지우고, 새 `process`(기술자 참조) + `simulator` 블록을 낸다. 생성기 소스 정규식 읽기는 없어진다.
* 미병합 `ng-bridge`: 이 card는 고치지 않는다. 형식 계약 = §11.1 스키마다. U16 흡수 때 맞춘다.
* `output_reference`의 생산: 엔진 결과 JSON의 `output_reference` 칸을 그대로 옮긴다. 생산자는 엔진→오라클 입력 변환기(U16)와 offset-trim 구동기다. `legacy_adapter`는 옛 엔진에 그 칸이 없으므로 내지 않는다. 그 입력으로 V_sys를 요청하면 `reference_undeclared`다.

---

## 12. 능력 확인(PC-1~PC-10, G-11)

### 12.1 공통

* 벤치는 소자 하나 또는 쌍의 IR이다. 기하는 기술자가 가리키는 모델 bin 안, LUT 격자 위 점에서 고른다. 고르는 규칙은 'LUT 슬라이스 기준 폭 + 그 L 앵커'이고 회로·PDK 이름이 없다.
* 실행은 일반 경로(코어 요청 → 어댑터)와 같다. 능력 확인 전용 실행 경로를 두지 않는다.
* 모든 PC에 대해 '깨진 변형에서 실제로 거부'를 먼저 test로 보인다(§18 T4).

### 12.2 항목

| PC | 벤치 | 판정(새 상수 없음) | 깨진 변형 픽스처 |
|---|---|---|---|
| PC-1 | 소자 하나, 공칭 바이어스 | op 수렴. 선언 op 파라미터(vdsat 포함) 전부 값이 있다. 모델 묶음 sha256은 어댑터 `model_bundle`이 계산한다(넘긴 묶음의 지문이라는 한계를 기록한다) | 모델 경로 틀림, op 이름 틀린 `model_family` 표 |
| PC-2 | 소자 하나, 정상·역방향 전도 두 점 + 0 V 감지원 | 정규화 ID 부호 = 감지원 전류 부호 × 극성 | 극성 규약을 뒤집은 어댑터 stub |
| PC-3 | 같은 기하·같은 바이어스 소자 둘 A·B, `McNative`(n = §12.3) | (a) A의 같은 ID 기준 VGS가 공칭과 분해능 넘게 다른 표본이 있다 (b) A·B 변화가 분해능 넘게 다른 표본이 있다 (c) MC를 끈 실행은 공칭과 비트 동일 (d) 기술자 `mismatch_only` 방법으로 불일치만 끄고 표본 실행만 켜면 모든 표본이 공칭과 분해능 안이다. 하나라도 벗어나면 전역 변동이 켜진 것으로 실패. A·B 공통 성분과 σ̂는 기록만 한다 | 불일치 꺼진 선언, 전역 공유 MC, 끄기 안 되는 선언, 전역 변동이 함께 켜진 선언 |
| PC-5 | 소자 하나, 같은 바이어스, 선언 온도 범위 끝점과 기준 온도 | ID 차가 해 정확도 전파 폭을 넘는다. 결과에서 읽은 온도 = 요청 온도 | 온도 무시 어댑터 stub |
| PC-6 | PC-3 벤치, 같은 seed로 기준 온도 단독 실행과 온도 여러 점 실행 | 같은 표본의 기준 온도 값이 두 실행에서 비트 동일 | 온도마다 재추출하는 어댑터 stub |
| PC-7 | 소자 하나, LUT 격자 점 몇 개 | 모델 묶음 비교 규칙(§12.5) 통과. 공칭 op(VDSAT 포함)가 LUT 점과 LUT 허용오차 안 | 다른 모델 파일, vdsat 정의가 다른 표 |
| PC-8 | 소자 하나, LUT `temp_c`와 다른 온도 | 그 온도로 실행됨(PC-5의 읽은 온도로 확인) | 입력 온도 무시 |
| PC-10 | 차동 입력쌍 + 출력 부하 + DC servo의 최소 IR(회로·PDK 이름 없음). 불일치는 끈다. 입력 `output_reference` 네 종류마다 하나씩 | (a) 온도 점마다 V_sys(T)를 낸다. V_sys(T)는 servo가 출력을 선언 기준에 붙들 때의 입력 차동 전압이고, 부호 규약은 offset-trim design의 V_sys,s 규약(§20.1, 계획 N3.4)을 따른다. 기준은 선언값을 온도와 무관하게 그대로 쓴다(offset-trim G-15) (b) 온도 sweep 실행의 T_j 값 = T_j 단독 실행 값(비트 동일) (c) `output_reference`가 없으면 `reference_undeclared`로 멈춘다 (d) 각 값에 DC 풀이 허용오차의 입력 환산 전파값(§13.4)을 함께 낸다 | 기준 해를 버리고 흔들림만 내는 경로, 온도마다 기준을 다시 푸는 경로, `output_reference` 없이 기본 기준을 몰래 쓰는 경로 |

* PC-4는 삭제됐다(O-1). MC 크기 판정은 offset-trim TR-7 §17-1 비교가 맡는다.
* PC-9는 LUT 생성 측정으로 옮겼다(D-4, §16).
* PC-11은 철회됐다(T-35).

### 12.3 PC-3 표본 수

* 기본안(P 계획): `sample_count(r)` = ceil(1 + 1/(2 r²))를 재사용한다. r = 입력 `offset_mc.rel_resolution`이다.
* 이 규칙은 σ 추정용이라 존재 판정에는 과하다. 예를 들어 r = 0.05면 201 표본이다.
* 대안(존재 판정 최소 수)은 P G-11에 열려 있다. 기준 확률의 출처를 새 상수 없이 정하지 못해 이 문서도 대안을 고르지 않는다. 비용은 OP-1에서 기록한다(**측정 대기**: 첫 조합에서 r 기본값의 PC-3 실행 시간).

### 12.4 능력 기록 `oracle_capability/1`

```
{
  "schema": "oracle_capability/1", "record_id": "<sha256 of canonical body>",
  "descriptor_fp": {...}, "adapter_fp": {...}, "check_code_fp": "<O/core/capability.py 등 sha256>",
  "lut": {"path", "slice_model_files_sha256": {...}},
  "checks": {"PC-1": {"bench_ir_fp", "requests", "measured", "resolution", "n", "verdict", "notes"}, ...},
  "conditions": {"temps_c": [...], "corner": "..."},
  "created_by": "verifier", "date": "..."
}
```

* 저장 위치는 `O/capability/<기술자 지문 앞부분>__<어댑터 지문 앞부분>.json`(기본안)이다.
* `record_id`는 내용의 정규 JSON sha256이다. offset-trim Δ_T 출처 지문과 `verified_by`(D-6)가 이 id를 가리킨다.

### 12.5 모델 묶음 비교 규칙(P N3.5, `core/bundle.py`)

kind마다 sha256 **값** 집합으로 비교하고, 경로는 비교하지 않는다.
* (i) 그 kind가 쓴 LUT 슬라이스들의 `model_files_sha256` 값 집합 ⊆ 어댑터 `model_bundle`의 sha256 집합
* (ii) 기술자가 정한 호출 모델(`kinds.<kind>.name`)을 정의한 파일의 sha256 ∈ LUT 기록 집합. 정의 파일은 묶음 파일 가운데 그 이름의 `.subckt`/`.model` 정의가 있는 파일이다.
* LUT 기록이 빈 표이면 `lut_model_provenance_missing`이다. 지금 LUT에 기록이 있는지는 **측정 대기**(OP-1 (ii))다.

### 12.6 게이트와 배선

| 게이트 | 위치(진입점) | 요구 |
|---|---|---|
| 공칭 자동 대조 | `oracle_run` 모든 실행, 벤치 실행 직전 | §12.5 통과 |
| MC 게이트 | `oracle_run`의 `offset_mc` 측정 진입 | 유효 능력 기록 + PC-3 통과 |
| 온도 게이트 | 해석 요청 `Condition.temp_c`가 LUT `temp_c`와 다르거나 온도가 여럿인 모든 실행 | 유효 능력 기록 + PC-5·PC-6·PC-8·PC-10 통과 |
| 진단 금지 | `core/compare.py`·`core/capability.py`의 입력 | 진단 결과가 들어오면 `diagnostic_not_a_gate` |

* 기록이 유효하려면 descriptor_fp·adapter_fp·check_code_fp·LUT 기록이 지금 값과 모두 같아야 한다.

### 12.7 공정 무관 증거

같은 `core/capability.py`가 두 기술자에서 돈다. 하나는 sky130 기술자(사례)이고, 다른 하나는 손 모델 픽스처 기술자다(시뮬레이터 내장 단순 모델 + 선언 불일치 변수, test 작성자 소유). 손 모델 기술자의 네이티브 MC 켜는 법은 픽스처가 정한다. 실제 두 번째 PDK는 완료 조건이 아니다(D-8).

---

## 13. 결정적 섭동 진단 경로(O-1 (5), 계획 N3.5)

### 13.1 입력

`oracle_run --diagnostic <파일>`로 받는다. 파일 스키마는 다음과 같다.

```
{"schema": "oracle_diagnostic/1",
 "vectors": [{"id": "...", "values": {"<소자 이름>": {"<진단 변수>": <z 값>}}}],
 "base": "nominal"}
```

* 코어가 `McDiagnostic` 요청을 만든다. 어댑터는 기술자 `diagnostic` 식(§10.5)으로 z를 파라미터 값으로 바꿔 소자별로 넣는다.
* 결과는 벡터마다 `OpTable`과 코어 MC 수학의 V_os다. `mc_math.py`의 표본 처리 함수를 네이티브 MC와 같은 함수로 지난다.

### 13.2 검증자 MC 수학 동일성(P N4)

1. 검증자는 기준선 `offset_mc` 출력의 `seed`, `n_requested`, `mismatch_vars`(소자별 변수 목록)를 읽는다.
2. `numpy.random.default_rng(seed).standard_normal()`을 옛 순서(표본 → 소자(입력 `devices` 순서) → 변수)대로 불러 z를 재현한다. 그 순서는 S-4다.
3. 같은 z를 진단 벡터로 넣는다. 표본 0은 모두 0이다.
4. 표본별 V_os와 σ_in·mean_in이 기준선과 비트 동일이면 통과다. 다르면 멈추고 보고한다.

* 이 절차는 검증 절차이고 게이트가 아니다(O-1 (5)).
* 차동 이득 A의 실수 판정 상수(`1e-3`, S-8)를 바꾸면(§14) 판정 경계 근처 입력의 `status`가 달라질 수 있다. 그런 사례가 기준선에 있는지는 **측정 대기**(OP-1)다.

### 13.3 TR-7 사용

offset-trim TR-7 §17-1에서 엔진 σ_in과 오라클 네이티브 MC σ_in이 어긋나면, 같은 진단 경로로 소자·변수별 결정적 기여를 재서 원인을 가른다. 결과는 진단 보고에만 실린다.

### 13.4 DC 풀이 허용오차의 입력 환산 전파(T-39, `core/mc_math.py`)

* 오라클이 내는 입력 환산 offset은 V_os = (V_out − V_out,ref)/A − (V_id − V_id,ref)다(S-4의 식. V_sys는 기준 표본 쪽 항).
* 각 노드 전압의 DC 풀이 오차 한계는 그 실행 `Resolution`의 reltol·|V| + vntol이다. 이것을 V_os 식에 1차로 전파한다:
  δV_os = (δV_out + δV_out,ref)/|A| + δV_id + δV_id,ref, 여기서 δV = reltol·|V| + vntol.
  차동 전압은 두 노드 오차의 합이다. A는 결정적 값이고 그 오차는 §14 실수 판정 분해능 안이라 1차 전파에서 뺀다. 이 근사는 결과에 표시한다.
* 결과의 표본마다(그리고 V_sys(T)마다) `dc_resolution_in_V`로 싣는다. offset-trim의 trim 잔여 수렴 분해능은 이 값을 쓴다(T-39, offset-trim design §20.6). 새 상수는 없고, 값은 선언된 허용오차와 측정 전압에서만 나온다.

---

## 14. 옛 리터럴 상수 처리(계획이 정한 것과 정하지 않은 것)

| 상수 | 계획 | 이 문서 |
|---|---|---|
| `_NGSPICE_DEFAULT_TOL` | 어댑터 보정값으로(P N3.6) | `calibration.json` `default_tolerances`, 출처 = 시뮬레이터 문서 기본값. 문서 쪽수는 OP-0 원문 보관 뒤 채움(P R6). **출처가 채워지기 전에는 선언값으로 쓰지 않는다**(§8.3, T-39 숨은 상수 금지). 그동안은 입력 `simulator.options`에 허용오차가 있어야 실행된다 |
| `WRDATA_NUMDGT = 8` | 어댑터 보정값(P N3.3) | `calibration.json` `data_digits`, 출처 = 코드 주석의 ngspice-46 실측 |
| 차동 이득 실수 판정 `1e-3·|h0|` | 해 정확도 분해능에서 유도(P N3.6) | `|Im h0| ≤ data_rel(ac 파일)·|h0|`로 바꾼다(`data_rel_resolution`의 값). 기준선 영향은 §13.2 측정 대기 |
| `NYQUIST_K_MAX = 10`, `NOISE_TOP_K_MAX = 8`, `INTEGRAL_K_MAX = 4`, `ZOOM_POINTS = 7`, `ZOOM_ROUNDS = 8` | **계획이 다루지 않음** | 기본안: 값과 동작을 바꾸지 않고 코어로 옮긴다(N4 동일성을 지키기 위해서다). 각 상수에 '출처 미확인 기존 상수' 표시를 단다. 유도로 바꾸는 일은 이 기능 밖의 정리 후보로 보고한다(§19.4 X-D1) |
| `_K_B`, `_Q_E` | -- | 물리 상수(CODATA), 그대로 둔다 |

---

## 15. 삭제 목록과 대체 배선표

### 15.1 오라클 본체

| 옛 것 | 새 것(배선 위치) | 삭제 card |
|---|---|---|
| `oracle_netlist.build_netlist` 텍스트 생성 | `core/build_circuit.circuit_ir` + `main_requests` → 어댑터 `dialect` (`oracle_run`이 호출) | OP-3 |
| `parse_netlist_elements` | `core/identity.py`(IR 대조) | OP-3 |
| `_Nets` 대소문자 규칙 | `core/ir` 충돌 검사(§4.1) | OP-3 |
| `probe_name`, `device_line`, `_includes`, `OP_PARAMS` 이름 표 | 어댑터 `dialect`·`read`(기술자 `model_family`) | OP-3 |
| `run_ngspice`, `run_cache_key`, `_model_files`, `_INC` | 어댑터 `run`, `model_bundle` + `core/cache.py` | OP-3 |
| `parse_op`, `parse_ac_file`, `_cols`, `_grab` | 어댑터 `read` | OP-3 |
| `oracle_compare.signed_id` | 어댑터 `read`(극성 정규화) | OP-3 |
| `stability_control`, `stability_netlist`, `stability_op_netlist`, `open_loop_parts`, `pz_netlist`, `openloop_tran_netlist` | `core/build_benches` + 어댑터 `dialect`(조기 종결은 능력) | OP-4 |
| `_refine_text`, `refine_samples` | 같은 IR에 좁은 `Ac` 재요청(`core/stability.nyquist_adaptive`가 호출) | OP-4 |
| `pz_poles`, `_PZ_POLE` | 어댑터 `read` → `Poles` | OP-4 |
| `oracle_config.json` | 어댑터 `calibration.json` | OP-4 |
| `_NGSPICE_DEFAULT_TOL`, `WRDATA_NUMDGT` | 어댑터 `calibration.json` | OP-4 |
| `oracle_noise._hexpr`, `_first_vac`, `_body`, `_VEC`, `_MOS`, `_RES`, `parse_noise_totals` | `Noise` 요청 + 어댑터 `read`(기여 이름 → IR 소자, 기술자 `inner_device`) | OP-5 |
| `oracle_offset_mc.mismatch_vars`, `build_mc_netlist`, z·1e-6/√m 배율, `"Lfb_" not in text` 검사, `1e-3` 상수, `--ngspice` 필수 인자 | 네이티브 MC(`McNative`) + 진단 경로(`McDiagnostic`) + `core/mc_math`. servo 유무는 IR 역할 표로 본다 | OP-5 |
| `oracle_swing._Sweeper`, `_control_block`, `_src_lines` | `OpSweep` 요청 + `core/swing_math` | OP-5 |
| 스키마 `process.models`, `process.ngspice_exe`, `process.diffusion`, `testbench.options` | §11.1 | OP-2 |
| `legacy_adapter.process_from_lut_generator` | 기술자 참조 출력(§11.4) | OP-2 |
| CLI `--ngspice` | `--simulator`, `--sim-exe` | OP-2(입력), OP-3(실행) |
| 진입점 `oracle_netlist.main`·`oracle_simulate.main`·`oracle_noise.main`·`oracle_offset_mc.main`·`oracle_swing.main`·`oracle_compare.main` | `oracle_run` 하위 명령(§3.1 기본안) | 각 모듈 삭제 card |

### 15.2 남는 수학의 이동(부분 수정, 함수 이름 유지)

`ac_measures`, `pm_crosscheck`, `loop_gain`, `loop_probe_singular`, `ratio_measure`·`rout_measure` 수학부, `loop_choke_ratio`, `nyquist_count`, `gain_crossings`, `low_side_gain_margin`, `thermal_voltage`, `solver_floor`, `reltol_of`, `n_pp_of`, `band_f_crit`, `tran_plan` 수학, `g_up`·`g_down`·`growth_window`·`limit_cycle_window`·`early_window`·`early_unstable`·`limit_cycle_early`·`window_ratios`, `transient_decision`(파일 대신 `TimeSeries` 입력), `extension_plan`, `final_transient_status`, `pz_rhp_count`, `nyquist_adaptive`, `stability_judgement`, `data_rel_resolution`·`mp_resolution`(입력 = `Resolution`), `sample_count`, `sat_violation`, `_window`, `oracle_compare`의 판정·markdown 함수 전부.

### 15.3 생성기(D-2, OP-8)

* 새 생성기는 새 파일(`A/` 아래, 이름에 PDK 없음)이다. 같은 어댑터와 기술자를 쓰고, LUT 메타에 어댑터 지문·기술자 지문·bin 경계 측정(§16)을 쓴다.
* 옛 `A/sky130_lut_sweep.py`·`A/sky130_pair_mc.py`는 출처 보존본으로 남긴다. 엔진 `sky130_lut_rule_decl.json`이 sha256으로 묶고 있기 때문이다(P X-10).
* 실행 경로 없음은 저장소 전체 grep 0으로 보인다. 대상은 모듈 이름 import, `runpy`, `subprocess` 인자, 경로 문자열이다. 엔진 선언 `sources` 칸과 문서 인용은 예외다.

---

## 16. bin 경계 규칙 선언(D-4, G-14, OP-7)

* 정본은 LUT 생성 실행에 묶은 선언 하나다. 묶는 대상(기본 방향, P G-14)은 (LUT가 쓴 모델 파일 sha256 묶음, 생성 시뮬레이터 판)이다.
* 형식(기본안): `<lut 폴더>/bin_rule.json` =
  ```
  {"schema": "lut_bin_rule/1", "model_files_sha256": [...], "simulator": {"name", "version"},
   "rule": "lower" | "upper", "evidence": {"points": [{"L", "W", "chosen_bin"}], "measured_by", "date"}}
  ```
  새 생성기는 LUT 메타에 같은 칸을 쓴다.
* 엔진 읽기: OP-7 엔진 card가 `E/lut/` 쪽에서 이 파일을 읽는다(엔진 변경, D-4 승인 범위). 오라클 능력 기록·오라클 코드 지문은 읽지 않는다.
* **측정 대기**: (a) 지금 LUT 기준 슬라이스 meta에 생성 시뮬레이터 판 기록이 있는가(OP-1 (iii)). 없으면 판 값은 OP-7 옆 선언에 검증자 측정으로 적는다. (b) 지금 LUT의 경계 앵커 점에서 시뮬레이터가 고른 bin(OP-7에서 검증자가 잰다).

---

## 17. 상위 문서 개정 문안(P N3.7)

* 아래는 **문안**이다. 반영은 상위 계획 개정 절차(독립 검증 → 사용자 승인)를 거친다(S-7). 이 card는 상위 문서를 고치지 않는다.
* 분류는 계획 N3.7을 따른다.

### 17.1 공통 치환 문구

| 기호 | 지금 문구 | 새 문구 |
|---|---|---|
| R-A | 'ngspice로 판정', '판정자 = ngspice', 'ngspice 불합격', 'ngspice를 통과' | 'SPICE 오라클로 판정', '판정자 = SPICE 오라클(첫 어댑터 ngspice)', 'SPICE 오라클 불합격', 'SPICE 오라클을 통과' |
| R-B | '전력 = ngspice 측정' | '전력 = SPICE 오라클 측정' |
| R-C | 'ngspice는 측정할 수 있는 항목만 판정한다' | 'SPICE 오라클은 측정할 수 있는 항목만 판정한다' |
| R-D | 'VCCS ngspice 오라클' | 'VCCS SPICE 오라클' |

### 17.2 상위 계획 `gain-budget-gmid-sizing.plan.md`(줄은 base `d783efe` 기준, 계획 N3.7 표와 같은 순서)

| 줄 | 분류 | 문안 |
|---|---|---|
| 11 | 둠 | -- |
| 123 | 고침 | '판정은 ngspice만 하고' → '판정은 SPICE 오라클만 하고(공칭은 모델 묶음 자동 대조, MC·온도는 능력 기록, 첫 어댑터 ngspice)' |
| 152, 284 | 고침 | '9회로 ngspice 합격 시험' → '9회로 SPICE 오라클 합격 시험'(284는 사용자 원문 인용 밖 문구만) |
| 286, 475 | 둠(D-2 뒤 고침) | OP-8 병합 뒤: '칸 중앙을 ngspice로 직접 재는' → '칸 중앙을 LUT 생성 어댑터로 직접 재는' |
| 296 | 둠(둘째는 D-2 뒤 고침) | OP-8 병합 뒤: 'ngspice 소자 쌍 Monte Carlo 대조 test' → 'LUT 생성 어댑터 소자 쌍 Monte Carlo 대조 test' |
| 297 | 고침 | 제목 '엔진 시작점·front를 ngspice로 판정하고' → 'SPICE 오라클로 판정하고'. (1) '판정자 = ngspice' → R-A |
| 478 | 고침 | 'P = 개루프 RHP 극점 수, 오라클이 ngspice `.pz`로 독립 측정' → '오라클이 어댑터 pz 능력으로 독립 측정(능력 없으면 P = 미정 경로, design oracle-portability §8.5)' |
| 542 | 고침(인터페이스·경로) | 인터페이스 문장 전체를 '오라클은 코어·시뮬레이터 어댑터·오라클 기술자 세 층이다(oracle-portability 계획 N3.1). 엔진 GB9는 `oracle_run`을 외부 단계로 부르고, 입력 `simulator` 블록으로 어댑터와 실행 파일을 고른다'로 바꾼다. 같은 절 `verified_by` 칸에 'capability_record_id'를 더한다(D-6). 옛 대조 스크립트 파일 이름은 둔다 |
| 576, 1112 | 고침 | R-D |
| 1140, 1142, 1143, 1145, 1146 | 고침 | R-A, R-B, R-C |
| 1144 | 둠 | -- |
| 1244 | 둠 | D-4 승인 시 끝에 '(경계 규칙 정본 = LUT 생성 실행에 묶은 선언, oracle-portability D-4)' 참조만 더한다 |
| 1293 | 고침(판정 문구) | R-A, R-B, R-C(`2.5p`는 둠) |
| 1335 | 고침 | 'SPICE 모델·ngspice 환경 부재' → 'SPICE 모델·시뮬레이터 환경 부재'. 실행 파일 경로 문장 → '실행 파일은 입력 `simulator.exe`, 보정값은 어댑터 선언' |

### 17.3 design 40 `gain-budget-gmid-sizing.40-engine.design.md`

| 줄 | 분류 | 문안 |
|---|---|---|
| 26 | 둠 | -- |
| 1444 | 고침 | '끊은 개루프 테스트벤치(같은 루프 절단)에 ngspice `.pz`를 돌려' → '끊은 개루프 벤치(같은 루프 절단)에 어댑터 pz 능력으로 극점을 구해(능력이 없거나 독립 증거로 확인되지 않으면 P = 미정)' |
| 1844 | 고침 | '(c) ngspice mismatch 블록 변수를 소자마다 gauss로 둔 MC' → '(c) 오라클 기술자가 선언한 네이티브 MC(능력 확인 PC-3 통과 조합). 크기 일관은 엔진 σ_in 대 MC σ_in 비교(offset-trim TR-7 §17-1)' |
| 1940, 1941, 1942, 1953, 1955, 1956, 1962, 2018 | 고침 | R-A, R-B, R-C |
| 1954 | 둠 | -- |
| 1996 | 둠(D-2 뒤 고침) | OP-8 뒤 '격자점·칸 중앙 LUT 생성 어댑터 대조(c)' |
| 2002 | 고침 | 'ngspice `.noise`(c)' → 'SPICE 오라클 noise(c)' |

### 17.4 그 밖

| 문서 | 문안 요지 |
|---|---|
| C10 계약 §1(b) | 'ngspice 안에서 `stop when`/`resume`로 창 j를 차례로 끝내며' → '어댑터가 조기 종결 능력을 선언하면 시뮬레이터 안에서 창 단위로 멈추고, 선언하지 않으면 design oracle-portability §8.4(G-13 결정)대로 실행한다. 판정 기준은 코어가 정의한다' |
| C10 계약 §1(c) | 'ngspice 실행 시간의 상한' → '어댑터 보정값 `wall_s_per_window`(출처·측정 조건 포함)' |
| C10 계약 §3 | 구현 메모(`>` 리다이렉션, `stop when` 문법, `numdgt`)는 'ngspice 어댑터 방언 메모'로 제목만 바꾸고 둔다 |
| `O/README.md` | 3층 구조, 어댑터 절, 기술자 절, 능력 확인 절로 다시 쓴다(OP-3~OP-6에서 card마다). '확인(… ngspice-46 sky130 tt)' 기록 절은 둔다 |
| `E/lut/CONTRACT.md` 4.0.1 | D-4 승인 시: '규칙 정본 = LUT 생성 실행에 묶은 bin 규칙 선언(oracle-portability §16)'. 실측 문단은 출처로 둔다 |
| `E/lut/CONTRACT.md:528` | 둠 |

---

## 18. test 목록(완료 조건별, 계획 N5.3)

### 18.1 새 test

| 완료 조건 | test(위치 `O/tests/`) | 기준 소유 | 내용 |
|---|---|---|---|
| 1 무방언 | `core/test_no_dialect.py` | 토큰 목록 = 검증자(OP-1) | T1-1 `O/core/` 문자열 리터럴(docstring 제외)의 토큰 정규식 적중 0. T1-2 PDK 이름(모든 기술자·엔진 선언 `pdk` 값과 모델 이름 패턴) 0. T1-3 AST import 금지(§3.2) 0. T1-4 `O/core/` 안 비-.py 파일 0, 코어의 파일 열기 경로 = 입력·기술자·출력만. T1-0(먼저) 토큰 목록이 기준선 넷리스트와 옛 코드 리터럴에서 적중함을 보인다 |
| 2 stub | `core/test_*_stub.py` | test 작성자 | §3.3 표의 stub 실행 항목 전부, '능력 없음 거부' 항목 전부, D-1 전체 창 경로(G-13 결정된 방식) |
| 3 동일성 | `adapters/ngspice/test_equivalence.py`(검증자 실행) | 기준선 = 검증자(OP-1) | 계획 N4: 이산 칸 정확, 연속 칸 비트 동일 또는 분해능 안(§18.3 식), MC 연속 칸 제외 + §13.2 MC 수학 비트 동일, 입력 변환 = 검증자 스크립트 |
| 4 거부 | `core/test_capability_rejects.py`, `core/test_gates.py` | test 작성자 | PC-1~3·5~8마다 §12.2 깨진 변형 거부(먼저), 기록 없음 → `oracle_capability_unverified`, 지문 하나 바꾼 기록 → `oracle_capability_stale`, 모델 묶음 불일치 → `model_bundle_mismatch`, LUT 기록 빈 표 → `lut_model_provenance_missing`, 진단 결과가 판정 입력으로 → `diagnostic_not_a_gate`. 같은 확인 코드가 sky130 기술자와 손 모델 기술자 둘에서 돈다 |
| 5 텍스트 단언 이전 | `core/test_no_dialect.py` T5-1 | 검증자 토큰 | `O/tests/core/` 안 방언 토큰 단언 0 |
| 6 삭제 | `test_deleted_names.py` | test 작성자 | §15.1 옛 이름 grep 0(card별로 그 card 몫만) |
| 7 배선 | `test_wiring.py` | test 작성자 | `oracle_run` 경로에서 코어·어댑터·기술자 읽기·자동 대조·MC·온도 게이트·진단 입력이 호출됨(호출 기록 증거) + 검증자 MC 수학 동일성 판정 기록 존재 |
| 8 엔진(D-4 승인 시) | 엔진 쪽 OP-7 test | 엔진 test 작성자 | 9회로 비트 동일, bin 규칙 선언 없음 → 경계 L 거부 |
| 8a 엔진 무변경 | `test_engine_untouched.py`(검증자 git diff) | 검증자 | OP-2~OP-6·OP-8에서 `E/`와 `A/sky130_pdk_decl.json` diff 0 |
| X-13 | `test_descriptor_engine_sha.py`(엔진 suite에서도 도는 위치, 기본안: `E/tests/` 쪽에 읽기 전용 test 하나) | test 작성자 | 엔진 선언 sha256 ≠ 기술자 참조 sha256이면 실패 |

### 18.2 옛 test 이전표

| 옛 파일 | 처리 |
|---|---|
| `test_oracle_c10_stability.py`, `test_oracle_u6_stability.py`, `test_oracle_transient.py` | 수학 부분 → `core/test_stability.py`(TimeSeries 입력). 넷리스트 텍스트 단언 → `adapters/ngspice/test_dialect_stability.py` |
| `test_oracle_netlist.py`, `test_oracle_netlist_topology.py`, `test_oracle_iso.py`, `test_oracle_z1.py`, `test_oracle_c27_loop_defs.py`, `test_oracle_junction_cap.py`, `test_oracle_conduction.py` | IR 단언 → `core/test_build_*.py`. 방언 줄 단언 → 어댑터 test |
| `test_oracle_rout.py`, `test_oracle_ratio_db.py`, `test_oracle_cm_loop.py`, `test_oracle_loop_singular.py`, `test_oracle_simulate_pm_crosscheck.py` | 수학 → 코어, 실행 → 어댑터 |
| `test_oracle_simulate.py`, `test_oracle_simulate_cache.py`, `test_oracle_run.py` | 어댑터 실행·캐시(§9) test로 다시 씀 |
| `test_oracle_noise.py` | 수학 → 코어, 기여 이름 대응 → 어댑터 |
| `test_oracle_offset_mc.py` | sky130 변수 집합 기대값(직접 섭동) 삭제. 네이티브 MC·진단·MC 수학 test로 다시 씀 |
| `test_oracle_swing_icmr.py` | 수학 → 코어, `OpSweep` 실행 → 어댑터 |
| `test_oracle_compare.py`, `test_oracle_compare_device_tol.py`, `test_oracle_diagnosis.py` | 코어로 이동(함수 이동만) |
| `test_oracle_input_schema.py` | 새 형식 + 옛 형식 거부 test로 다시 씀 |
| `test_legacy_adapter.py`, `test_legacy_testbench.py` | 새 `process` 출력 단언으로 다시 씀 |
| `conftest.py`의 `run_spice`·`independent_cs/fb`, `u6_toy5t.py`(손 넷리스트 독립 기준) | `adapters/ngspice/` 아래로 옮겨 그 어댑터의 독립 기준으로 쓴다(삭제하지 않음) |

* test는 다시 써도 된다는 사용자 방침에 따라 텍스트 단언은 보존하려 하지 않는다. 독립 기준(손 넷리스트)만 지킨다.

### 18.3 연속 칸 분해능 식(G-6)

* 값 x(기준선), y(새)에 대해 |y − x| ≤ reltol·max(|x|, |y|) + abstol_q를 쓴다. reltol·abstol_q는 그 실행의 `Resolution`(입력 options 또는 어댑터 기본값)이고, q는 양 종류(전압 = vntol, 전류 = abstol)다.
* 파생 측정(dB, 위상, 교차 주파수, PM)은 옛 `data_rel_resolution`·`mp_resolution`이 이미 내는 측정 분해능을 쓴다.
* 식이 없는 칸은 비트 동일만 인정한다(기본안).

---

## 19. 열린 항목

### 19.1 오케스트레이터 기본안(이 문서가 정한 세부, 사용자가 바꿀 수 있음)

| ID | 내용 | 절 |
|---|---|---|
| B-1 | 파일 분할과 이름(`core/*.py` 목록, `adapters/ngspice/*`, `descriptors/`, `capability/`) | §3.1 |
| B-2 | 옛 진입점 CLI를 `oracle_run` 하위 명령으로 합침 | §3.1 |
| B-3 | 테스트벤치 원소 IR 이름 `tb:<용도>:<대상>` | §4.1 |
| B-4 | 스키마 이름 `oracle_pdk_descriptor/1`, `oracle_capability/1`, `oracle_diagnostic/1`, `lut_bin_rule/1`, 저장 위치 | §10, §12.4, §13, §16 |
| B-5 | `simulator.options` 키 검증은 어댑터 | §11.1 |
| B-6 | LUT 메타·입력 모두 온도·코너가 없으면 `oracle_condition_missing` | §11.2 |
| B-7 | 차동 이득 실수 판정 = `data_rel` 유도 | §14 |
| B-8 | 계획이 다루지 않은 반복 상한 상수 다섯은 그대로 옮기고 표시만 | §14 |
| B-9 | X-13 test를 엔진 suite 쪽에 둠 | §18.1 |
| B-10 | 식이 없는 연속 칸은 비트 동일만 | §18.3 |

### 19.2 계획과 다른 결정이 필요한 곳(S-7: 멈추고 보고)

**v0.2 상태**: DV-1·DV-2는 사용자 결정 O-3(2026-10-16 "모두 권고대로")으로 닫혔다. DV-1은 (가)로 정해져 계획 v0.5 N3.4에 반영됐고(`oport-plan-r1`), DV-2 상위 문서 개정은 별도 card다(`gb-oracle-rev`). v0.2에서 새로 생긴 멈춤 항목은 없다. 아래 표는 기록으로 남긴다.

| ID | 내용 | 필요한 결정 |
|---|---|---|
| **DV-1** | 오라클이 include해야 하는 모델 파일 가운데 엔진 선언 `sources`에 없는 것이 있다(사례 pmos `lod.spice`, S-7). 계획 N3.4 '원본 파일 경로·sha256 정본은 엔진 선언 하나'와 D-9 '엔진 선언 무변경'을 함께 지킬 수 없다 | (가) 기술자 `extra_sources`에 엔진 선언에 없는 파일만 두고 중복은 금지(§10.1 임시안, '파일마다 정본 한 곳'으로 원칙을 고침) (나) 엔진 선언에 그 파일을 더하는 엔진 card(D-9 예외, 엔진 지문·9회로 기준선 재측정) -- 계획 개정 필요 |
| **DV-2** | 상위 문서 개정(P N3.7)이 아직 반영되지 않았다. 계획 N5.1의 공통 착수 조건이라 구현 card(OP-2~)는 상위 계획 개정 승인 뒤에만 시작할 수 있다. 이 문서는 §17에 문안만 냈다 | 상위 계획 개정 절차를 언제 누가 할지(계획과 다른 결정은 아니고 순서 확인이다) |

### 19.3 측정 대기 칸(OP-1·OP-7, 하나를 고르지 않음)

| 칸 | 측정 | 절 |
|---|---|---|
| D-1 능력 없는 어댑터의 기본 실행 방식(G-13) | OP-1 기준선 창당 시간 | §8.4 |
| sky130·ngspice 네이티브 MC 켜는 법·소자별 독립 여부, 직접 루프를 쓴 이유 | OP-1 (i) | §10.3, §10.4 |
| 지금 LUT 슬라이스 meta의 `model_files_sha256` 존재 | OP-1 (ii) | §12.5 |
| 지금 LUT 슬라이스 meta의 생성 시뮬레이터 판 존재 | OP-1 (iii) | §16 |
| 지금 LUT 경계 앵커 점에서 시뮬레이터가 고른 bin | OP-7 검증자 | §16 |
| PC-3 표본 수 기본값의 실행 비용 | OP-1 | §12.3 |
| 차동 이득 실수 판정 변경이 기준선 `status`를 바꾸는 사례 | OP-1 | §13.2, §14 |
| ngspice 오류 로그 → 오류 코드 대응표 | OP-1 기준선 로그 | §7 |
| ngspice 매뉴얼 원문 보관과 기본 허용오차 쪽 번호 | OP-0 card 범위(원문 보관, 검증자 아닌 문서 작업, X-D4 수용 O-4) | §14 |
| 기준선 입력 가운데 DC 풀이 허용오차 선언이 없는 것(X-D4) | OP-1 | §8.3 |

### 19.4 원래 취지와 다름(따로 보고)

| ID | 내용 |
|---|---|
| X-D1 | 계획이 다루지 않은 옛 반복 상한 상수 다섯(S-8)을 출처 확인 없이 그대로 옮긴다(B-8). '상수 발명 금지' 원칙에서 보면 기존 위반을 이 기능이 정리하지 않고 넘기는 것이다. 정리하면 N4 동일성이 깨질 수 있어서다 |
| X-D2 | 옛 진입점 여섯을 `oracle_run` 하위 명령으로 합친다(B-2). README의 '파일마다 독립 진입점 1개' 원칙(`O/README.md` '파일' 절)과 다르다 |
| X-D3 | (v0.2에서 해소) PC-10은 offset-trim design TR-0T가 G-15를 닫아(선언 기준을 온도 무관하게 그대로) 정의했다(§12.2). 단 그 design은 아직 미병합(`trim-design-r1`)이라 OP-6 착수는 그 병합 뒤다 |
| X-D4 | (v0.2, **수용(O-4)**. 할 일: ngspice 매뉴얼 원문 보관과 기본 허용오차 쪽 번호 채우기 = OP-0 card 범위, 영향받는 기준선 입력 측정 = OP-1) T-39에 따라 DC 풀이 허용오차를 선언 없이 쓰지 않게 했다. 그래서 지금 기본 허용오차(`_NGSPICE_DEFAULT_TOL`)의 출처(매뉴얼 쪽)가 채워지기 전에는, 입력에 허용오차 선언이 없는 기존 오라클 입력이 `dc_tolerance_undeclared`로 멈춘다. 지금 smoke 입력은 `testbench.options`에 reltol·vntol·abstol을 가진다(S-6 사례). 영향받는 기준선 입력이 있는지는 OP-1에서 잰다 |

---

## 20. card별 범위 재확인(계획 N5.1 대 이 문서)

| card | 이 문서 절 | 선행(계획) | 추가 선행(이 문서) |
|---|---|---|---|
| OP-1 | §19.3 측정 전부, §18.1 T1-0 토큰 목록, §13.2 절차 준비, N4 입력 변환 스크립트 | 계획 승인 | -- |
| OP-2 | §10, §11 | OP-0, OP-1 | 상위 문서 개정 card(`gb-oracle-rev`) 승인·병합 |
| OP-3 | §3, §4, §5, §6, §7, §8.1~8.3, §9, §12.5, §15.1 OP-3 행 | OP-2 | -- |
| OP-4 | §8.4, §8.5, §15.1 OP-4 행 | OP-3 | G-13 측정 |
| OP-5 | §10.4, §10.5, §13, §15.1 OP-5 행 | OP-4 | OP-1 (i) 결과(독립 아니면 사용자 결정) |
| OP-6 | §12 | OP-5 | (충족, T-40) offset-trim design TR-0T가 master에 병합됨. PC-10 기준의 대조 정본 = master `offset-trim.design.md` §20 |
| OP-7 | §16 | OP-3, XRUN-F1 C | OP-1 (iii), 경계 재측정 |
| OP-8 | §15.3, §16 | OP-6 | -- |
| OP-9 | §18 전부 | -- | -- |
