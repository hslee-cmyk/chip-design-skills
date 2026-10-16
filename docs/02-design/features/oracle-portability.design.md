---
template: design
version: 0.2.4
plan: ../../01-plan/features/oracle-portability.plan.md
plan_version: 0.6.2
---

# oracle-portability Design Document (card OP-0)

> **Summary**: 계획 `oracle-portability.plan.md` v0.6.2(승인 v0.4.2 + 사용자 결정 O-3·O-4·O-6과 검증 정합 개정, 사용자 승인 O-7)를 오라클 설계로 옮긴다. 계획의 결정은 사용자 결정 O-1~O-7, D-1~D-9이다. 이 문서가 정하는 것은 다음과 같다.
> * 3층 구조(코어 / 시뮬레이터 어댑터 / PDK·오라클 기술자)의 파일 분할과 import 금지
> * 회로 IR, 해석 요청, 정규화 결과의 형식
> * 어댑터 능력 선언 스키마
> * 오라클 기술자 스키마(엔진 선언 sha256 참조, D-9), 기하 단위·병렬 배수 전달 규칙(O-6 D-b), 네이티브 MC 켜는 법과 분포 값 위치(O-6 D-a)
> * 능력 확인 PC-1~PC-10의 벤치·규칙·기록 형식
> * 결정적 섭동 진단 경로의 배선
> * 옛 코드 삭제 목록과 대체 배선표
> * 완료 조건별 test 목록
> * 상위 문서 개정 문안(계획 N3.7)
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (design 작성자 역할)
> **Status**: **design v0.2.4 -- 개정 초안, 독립 검증·사용자 승인 전**(2026-10-16). 계획 v0.6~v0.6.2(O-6 D-a·D-b·D-c, 완료 조건 4·4a, OP-3 병합 조건 (a)(b), G-5·G-9·G-13·G-14)와 OP-1 측정(`wt/_scratch_op1/results/`, §2 S-12~S-20)에서 미뤄 둔 항목, v0.2.3 검증자 정리 둘(§20 OP-2·OP-5 겹침, offset-trim N3.9-3 재대조 §12.8)을 반영했다. 계획과 다른 결정이 필요한 곳 하나를 §19.2 DV-3으로 올렸다(멈춤). 경위는 history H1 v0.2.4.
> * v0.2.3: 사용자 승인됨(2026-10-16 "모두 권고대로", 결정 기록 O-5). 독립 검증 87 → 95점(차단 0).
> * v0.2.2: v0.2 검증(87점, 차단 B-1, 비차단 N-1~N-9)을 반영했다. B-1은 계획 v0.5.1의 완료 조건 8a 예외(`oport-plan-r2` `d9f37c4`)를 따른다.
> * v0.2.1: 사용자 결정 O-4("TR-0T 승인, X-D4 권고대로 해")로 X-D4를 수용했다. offset-trim TR-0T design이 master에 병합됐다(T-40). 그래서 PC-10과 `dc_tolerance_undeclared`의 대조 기준은 master `offset-trim.design.md` §20이다.
> * v0.2 반영 1: offset-trim design TR-0T(v0.2 작성 때 `trim-design-r1`, 지금은 master 병합, T-40)가 G-15를 닫았다. 그래서 PC-10을 정의한다(§12.2, 기준은 새 입력 칸 `output_reference`로 받는다, §11.1).
> * v0.2 반영 2: 사용자 결정 T-39로 trim 잔여 수렴 분해능 = 오라클 DC 풀이 허용오차의 입력 환산 전파값이 됐다. 그래서 DC 풀이 허용오차를 반드시 선언하게 하고, 그 전파값을 결과에 낸다(§6, §8.3, §13.4).
> * v0.1 멈춤 항목 DV-1·DV-2는 사용자 결정 O-3으로 닫혔다. DV-1 (가)는 계획 v0.5(`oport-plan-r1`)에 반영됐고, DV-2 상위 문서 개정은 별도 card(`gb-oracle-rev`)다(§19.2).
> **기준**: 코드 인용은 base `6093d07`(worktree `wt/oport-design`)의 `파일:줄`이다. v0.2.4에서 새로 적은 사실은 base `1ba9461`(worktree `wt/oracle-op0-design`)에서 다시 쟀다. 두 base 사이 `O/` 차이는 `O/README.md` 2줄 추가뿐이라(`git diff --stat 6093d07 1ba9461`) 코드 `파일:줄` 인용은 두 base에서 같다. 경로 약어는 계획 N0과 같다: `O/` = `skills/analog-gmid-design/tools/spice_oracle/`, `E/` = `skills/analog-gmid-design/gmid_engine/`, `A/` = `skills/analog-gmid-design/assets/`. 계획 인용은 `P N3.5`, `P D-7` 식으로 쓴다.
> **이력**: [oracle-portability.design.history.md](oracle-portability.design.history.md)

---

## 0. 문서 안내

* **담는 것**: 계획 결정을 오라클 구조로 옮긴 규칙, 자료 형식, 함수 서명, 실패 코드, 파일 분할, card별 범위, test 목록, 상위 문서 개정 문안.
* **담지 않는 것**: 경위(history 몫)와 수치 상수. 허용 폭은 시뮬레이터 해 정확도 선언(입력 `simulator.options` 또는 출처 있는 어댑터 보정값, §8.3), MC 표본 수 규칙, 기술자가 원본 파일에서 계산한 값에서만 온다(P N0 값 원칙). 예외는 계획 NFR-P2의 '출처 미확인 기존 상수' 여섯뿐이다(§14).
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
| O-6 D-a | 네이티브 MC = 기술자 선언 켜는 법(종류 하나 + 대상), 분포 값은 PDK 원본 선언에서만(기술자는 원본 sha256으로 위치만 가리킴), 난수는 시뮬레이터 RNG, 오라클은 표본 값을 계산하지 않음(P N0.1, X-18 수용) | §10.4, §12.2 |
| O-6 D-b | 기술자에 기하 단위·병렬 배수 전달 규칙 선언, 어댑터는 그대로 소자 줄을 씀, 미선언 kind는 공칭 포함 모든 해석에서 거부, 손 모델 결정적 어댑터 test(완료 조건 4a) | §10.2, §10.6, §18.1 |
| O-6 D-c | 차동 이득 실수 판정 상대 폭 `1e-3`은 '출처 미확인 기존 상수' 예외로 값·동작 그대로 이동(P NFR-P2 여섯째) | §14 |
| O-7 | 계획 v0.6.2 승인·병합(`1ba9461`) | 이 판의 기준 |
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

* 상위 문서 개정(P N3.7)은 v0.2.3 때 반영 전이었고(base `6093d07`의 상위 계획에 `run_ngspice_op_ac`가 남아 있었다), 이 문서 §17이 그 **문안**을 냈다. (v0.2.4) 그 개정은 별도 card `gb-oracle-rev`로 master에 병합됐다(`b105b65`, 2026-10-16. base `1ba9461`의 상위 계획에 `run_ngspice_op_ac` grep 0). 그래서 구현 card(OP-2~)의 공통 착수 조건(P N5.1) 가운데 이 항목은 충족됐다. 병합본이 §17 문안과 같은지는 이 card가 대조하지 않았다(§19.2 아래 '알림').
* offset-trim G-15(출력 기준 DC)는 base에서는 열려 있었지만, offset-trim design TR-0T가 닫았고 master에 병합됐다(T-40). 내용은 선언 기준을 온도 무관하게 그대로 쓰고, 없으면 `reference_undeclared`다. 그래서 v0.2에서 PC-10을 정의했다(§12.2). 대조 정본은 master `offset-trim.design.md` §20이다.

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

**OP-1 측정 사실(v0.2.4).** 검증자 OP-1 산출물을 이 판을 쓰며 다시 읽었다. 위치는 `wt/_scratch_op1/results/`(아래 `R/`), 스크립트는 `wt/_scratch_op1/scripts/`다. 사례 조합은 sky130·ngspice-46이고, 수치는 기록일 뿐 규칙이 아니다.

| ID | 사실 | 근거 |
|---|---|---|
| S-12 | 첫 조합의 네이티브 MC 켜는 법: 모델 카드가 `.param … = 0.0`으로 둔 불일치 변수(`…__{toxe,vth0,voff}_slope_spectre`)를 최상위 `.param … = agauss(0,1,1)`로 다시 선언한다. 분포 값의 출처는 모델 카드의 주석 처리된 통계 블록(`vary … dist=gauss std = 1.0`)이고, 그 시뮬레이터는 이 블록을 실행하지 않는다. 결과: 200 시드에서 소자 A·B의 vth0 표준편차 1.399·1.495 mV, 상관 −0.058(소자별 독립, 13행), 같은 시드 비트 동일·다른 시드 다름(2행), 시드 없으면 실행마다 다름(3행), 같은 시드 표본이 −40·27·85 °C에서 같음(6행), 한 실행 안 재추출 명령 셋 모두 표본 불변 = 표본마다 별도 실행(8~10행), 스위치 0은 공칭과 **출력 자릿수** 동일(15행, 비트 비교 아님), 인스턴스 줄 덮어쓰기는 효과 없고 래퍼 지역 파라미터는 효과 있음(16·17행) | `R/m1_native_mc.jsonl` 행 번호, `scripts/m1_native_mc.py:45`, `C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice:16-27` |
| S-13 | 기하 단위·병렬 배수: 카드 식은 `vth0 = … + slope_spectre*(vth0_slope/sqrt(l*w*mult))`이고(`…tt.pm3.spice:67`), 래퍼 기본 `mult = 1`(`:30`). `.option scale` 없이 SI 기하를 주면 vth0 표본이 −904 V(면적이 10¹²배 작게 읽힘), scale 아래 숫자면 0.4833 V(4행). 인스턴스 `m=4`만 주면 표본이 `m=1`과 같고(배수가 면적에 안 들어감), `m=4 mult=4`면 편차가 절반(11행). 지금 오라클은 SI 기하 + `m=`로 쓰고(`O/oracle_netlist.py:145-153`) 이 둘을 변수값 z·1e-6/√m로 덮는다(`O/oracle_offset_mc.py:22-24`). scale 지시는 PDK 파일 `models/all.spice:2`(`.option scale=1.0u`, 엔진 선언 source `scale_option`)에 있고, 지금 오라클 include 목록에는 그 파일이 없다(smoke 입력 `process.models.*.includes`) | `R/m1_native_mc.jsonl` 4·11행, 위 파일:줄 |
| S-14 | 차동 이득 실수 판정: 기준선 ac 파일 198개 가운데 옛 규칙(`|Im h0| ≤ 1e-3·|h0|`)으로 실수 174개, 결과 파일 자릿수 분해능 `data_rel`로 바꾸면 4개만 실수(170개가 ok → unavailable로 뒤집힘). 그래서 계획 D-c가 값을 유지했다 | `R/m7_gain_imag.json`(`n_ac_files`, `n_old_real`, `n_new_real`, `n_flip_ok_to_unavailable`), `O/oracle_offset_mc.py:137` |
| S-15 | LUT 메타: 슬라이스 38개 모두 `model_files_sha256` 기록이 있고 PDK 원본과 sha256이 맞으며 생성 시뮬레이터 판(`ngspice-46`) 기록이 있다. 메타 칸 이름은 `ngspice`·`ngspice_exe`(사례 이름) | `R/m2_m3_lut_meta.jsonl` 41행 SUMMARY |
| S-16 | 방언 토큰 초안(검증자 소유 `wt/_scratch_op1/g8_dialect_tokens.draft.json`, D1~D12) 사전 점검: 기준선 넷리스트 1158개와 옛 코드 리터럴에서 D11(난수·식 함수 `agauss(` 등)만 어디서도 적중하지 않았다. 코어 어휘(`op`, `ac`, `dc`, `noise`, `tran`, `pz`, `temp`, `reltol`, `vntol`, `abstol`) 단독 적중 0 | `R/g8_check.json` `tokens_with_no_hit_anywhere`, `core_vocab_false_hits` |
| S-17 | `O/oracle_compare.py`의 시뮬레이터 이름 리터럴(문자열, docstring 제외)은 3개다: `:379` 메시지 `"ngspice .op 결과 없음: "`, `:708` 메시지 조각 `' V, ngspice '`와 키 `'ngspice_runs'`. docstring 안 언급은 `:38`(모듈)·`:228`(`signed_id`). 키 `ngspice_runs`의 생산자는 `O/oracle_swing.py:306`, 다른 소비자는 `O/smoke/u6_selfchecks.py:136`이다. 결과 칸 `ngspice_rc`는 `O/oracle_simulate.py:1284` 등 여러 곳이 쓴다(S-3) | `R/g8_check.json` D9 `oracle_compare.py: 3`, `grep -n -i ngspice` (base `1ba9461`) |
| S-18 | 오류 로그: 기준선 로그 860개에서 문장 형태 25묶음. 옛 정규식(`error|fatal|singular|abort`)은 회로 제목 줄 `Circuit: * spice_oracle: tsingular …`에 적중한다(12건, 제목의 'singular'). pz 실패 표지(`giving up`)는 옛 일반 정규식에 걸리지 않고 pz 정규식에만 걸린다(43건) | `R/m8_errlog.json`, `R/m8_errlog.console.txt` |
| S-19 | C10 창당 비용(같은 기계, 순차): 기준선 폐루프 과도 150 실행(조기 종결 12), 지금 합계 137.7 s, (가) 전체 창 한 번 146.8 s, (나) 창별 재실행 463.2 s(판정 창까지)·513.2 s(계획 창 전부), 창 하나 최대 15.97 s | `R/g13_window_cost.json` `aggregate`, `scripts/g13_window_cost.py` 머리 설명(비용 모형) |
| S-20 | DC 풀이 허용오차 선언(X-D4): 옛 형식 입력 593개 가운데 `testbench.options`에 reltol·vntol·abstol 가운데 하나라도 없는 것 2개. 그중 `converted/sizing.engine.new.json`은 변환 뒤 `simulator.options`로 옮긴 파일을 옛 칸으로 읽은 스캐너 결과라 대상이 아니고, 실제 대상은 test 입력 하나(`test_plan_default_reltol0`, reltol 없음)다 | `R/m6_xd4_scan.json`, `scripts/m6_xd4_scan.py:16`(`testbench.options`만 읽음), `R/n4_convert.jsonl` `options_moved` |
| S-21 | 입력 변환 초안(검증자 소유 `wt/_scratch_op1/n4_convert_input.py`)이 §11.1 대응표 밖 `process` 키 2개를 찾았다: `lut_reference_width_m`, `provenance`. 둘 다 생산자 `legacy_adapter.process_from_lut_generator`가 쓰고(`O/legacy_adapter.py:191-192`) 오라클 본체(`O/oracle_*.py`)는 읽지 않는다(grep 0). `lut_reference_width_m`은 `legacy_adapter` 안에서 finger 분할 기준 폭의 대체값으로만 쓰인다(`:261-264`, dump `lut_meta.W_ref_m`이 없을 때) | `R/n4_convert.jsonl` `unmapped_process_keys`, 위 파일:줄 |
| S-22 | MC 수학 재현: 기준선 `offset_mc` 표본(seed 0, 201 표본, 변수 14개)을 옛 순서로 재현한 z가 기준선 넷리스트 값과 비트 동일했고, 기준선 로그의 표본별 op 값으로 다시 계산한 σ_in·mean_in도 비트 동일했다 | `R/m13_mc_replay.jsonl` 1·2행 |

---

## 3. 패키지·파일 분할과 import 금지

### 3.1 디렉터리(기본안: P N0.1의 `O/core/`·`O/adapters/<이름>/` 고정을 따른다)

```
O/
  oracle_run.py            진입점(CLI). 입력 검증 -> 기술자 읽기 -> 어댑터 선택·주입 -> 코어 측정 -> 판정 -> 출력
                           (능력 확인 실행도 `oracle_run capability` 하위 명령이다 -- 진입점 하나, X-D2 결정 O-3. 검증자가 실행해 능력 기록을 만든다)
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
    fixtures/
      hand_model/          손 모델 픽스처 정본 하나(OP-5 산출, test 작성자 소유, §12.7): 기술자·그것이 참조하는
                           gmid_pdk_decl/1 형식 선언·손 모델 파일. 4a·OP-6이 재사용하고 새로 만들지 않는다
```

* 옛 파일 `oracle_netlist.py`, `oracle_simulate.py`, `oracle_noise.py`, `oracle_offset_mc.py`, `oracle_swing.py`, `oracle_compare.py`, `oracle_config.json`은 대체 card에서 삭제한다(§15). 각 진입점의 CLI 기능은 `oracle_run`의 하위 명령으로 합친다(결정(O-3), X-D2 수용). 이유는 진입점 정본을 하나로 두기 위해서다. 단 `--bias`별 단독 실행처럼 test가 쓰는 기능은 하위 명령으로 남긴다.
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
* (v0.2.4) 기하: stub은 `geometry_unit_application`을 선언하지 않는다. 그래서 stub 실행 test의 기술자 픽스처는 `geometry_unit = "si"`와 `parallel_multiplier`를 선언한다(미선언 거부는 stub 앞 코어에서 일어나므로 OP-3 병합 조건 (a) test는 stub으로 돈다). 비 SI 단위 기술자를 stub에 주면 `geometry_unit_unsupported`다.

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
* `EarlyStopRule`은 코어 규칙 자체(창 경계, floor', reltol, g↑·g↓·한계 사이클 판정에 필요한 값)를 담는 자료다. 능력이 있는 어댑터는 이것을 방언 스크립트로 옮긴다. 능력이 없는 어댑터에서는 코어가 이 규칙을 사후에 적용한다. 실행 방식(전체 창 한 번 / 창별 재실행)은 §8.4의 G-13 후보 가운데 OP-4가 고른다(측정 S-19).
* `keep_identity`: 같은 `seed`·같은 `n_samples`로 다른 `Condition`(온도)을 요청하면 같은 표본(같은 불일치 값)을 재야 한다는 요구다(PC-6, offset-trim N3.8.2). 어댑터가 이 능력을 선언하지 않으면 코어가 거부한다.

---

## 6. 정규화 결과(G-2, `core/results.py`)

```
RunStatus(rc, timed_out: bool, error: ErrorCode|None, log_excerpt: tuple[str], cache_hit: bool)
OpTable(devices: {name: {param: value}}, nodes: {net: V}, currents: {element: A}, resolution: Resolution,
        instance_geometry: {name: {L, W, multiplier}}|None)   # 시뮬레이터가 보고한 인스턴스 기하를 SI·IR 배수로 되돌린 값(§10.6)
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
* `instance_geometry`는 어댑터 능력 `instance_geometry_readback`(§8.3)이 참일 때 채운다. 어댑터는 기술자 기하 단위·병렬 배수 규칙(§10.6)을 거꾸로 적용해 IR과 같은 단위(SI 길이, IR `n_fingers`)로 돌려준다. 완료 조건 4a의 '인스턴스 기하 단언'이 이 칸을 쓴다.
* 결과 칸 이름에 시뮬레이터 이름을 넣지 않는다. 옛 `ngspice_rc`(S-3)는 `RunStatus.rc`, 옛 `ngspice_runs`(S-17)는 `sim_runs`다(§15.1). 결과 JSON 칸 이름 대응은 동일성 판정의 비교 칸 대응(§11.5)에 함께 적는다.
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
| `oracle_condition_missing` | LUT 메타와 입력 모두 온도·코너가 없음(§11.2) | 코어 |
| `descriptor_source_duplicated` | 같은 원본 파일(경로 또는 sha256)이 엔진 선언 `sources`와 기술자 `extra_sources` 두 곳에 있음(§10.1, 계획 N3.4) | 코어 |
| `pdk_descriptor_stale` | 기술자가 참조한 sha256과 실제 파일 sha256이 다름 | 코어 |
| `model_bundle_mismatch` | 모델 묶음 비교 규칙 위반(§12.5) | 코어 |
| `lut_model_provenance_missing` | LUT 슬라이스 meta 모델 기록이 빈 표 | 코어 |
| `oracle_capability_unverified` | 필요한 능력 기록 없음 | 코어 |
| `oracle_capability_stale` | 능력 기록 지문 불일치 | 코어 |
| `mc_method_unsupported` | 선언되지 않은 MC 방법 | 코어 |
| `diagnostic_not_a_gate` | 진단 결과를 판정 입력으로 쓰려는 호출 | 코어(§13.3) |
| `dc_tolerance_undeclared` | 입력 `simulator.options`에도 어댑터 보정값에도 DC 풀이 허용오차(reltol·vntol·abstol) 선언이 없음(§8.3) | 코어 |
| `reference_undeclared` | V_sys 측정(PC-10, 범위 판정)에 필요한 입력 `output_reference`가 없음(§11.1). offset-trim design §20.1과 같은 사유 이름 | 코어 |
| `descriptor_geometry_undeclared` | (v0.2.4, O-6 D-b) 쓰려는 kind의 기하 단위 또는 병렬 배수 전달 규칙이 기술자에 없음. 공칭 포함 모든 해석에서 낸다(§10.6). 어느 쪽이 없는지 `detail`에 적는다 | 코어 |
| `geometry_unit_unsupported` | (v0.2.4) 기술자가 선언한 기하 단위를 어댑터가 적용할 방법을 선언하지 않음(§8.3 `geometry_unit_application`), 또는 전역 지시의 영향 칸 선언이 없음 | 코어 |
| `mc_distribution_inline` | (v0.2.4, O-6 D-a) 기술자 `mc.distribution`에 분포 값(분포 종류·표준편차 등)이 직접 적혀 있음. 분포 값은 PDK 원본에서만 읽는다(§10.4) | 코어 |
| `mc_distribution_unlocated` | (v0.2.4, O-6 D-a) 기술자가 분포 값 위치를 선언하지 않았거나, 선언한 위치 식이 원본에서 0개를 찾음(P NFR-P6) | 코어 |

* 가리킨 PDK 원본의 sha256이 맞지 않는 경우는 새 코드를 두지 않고 `pdk_descriptor_stale`로 낸다(완료 조건 4 분포 값 출처 깨진 변형 셋째 = 이 코드).

### 7.1 시뮬레이터 로그 → 오류 코드 대응표(초안, 사례 ngspice)

* 규칙(어댑터 공통): 대응은 **로그 문장 형태**(줄 머리의 심각도 표지 + 문구)로 한다. 시뮬레이터가 다시 찍는 회로 제목 줄과 사용자 이름(넷·소자 이름)이 들어가는 부분은 대응에서 뺀다. 옛 부분 문자열 정규식이 제목 줄 `… tsingular …`에 걸린 사례(S-18) 때문이다.
* 아래는 OP-1 기준선 로그(S-18) 25묶음에서 뽑은 **초안**이다. ngspice 어댑터 `errors.py`의 사례 표가 되고, 확정은 OP-3(op·ac 실행)·OP-4(pz·과도) 구현 때 같은 기준선 로그로 다시 대조한다. 방언 문구는 사례이므로 규칙 칸에 넣지 않는다.

| 로그 문장 형태(사례, `#` = 숫자) | 기준선 건수 | 옛 정규식 / pz 정규식 | 초안 코드 | 비고 |
|---|---|---|---|---|
| `Warning: Pole-zero iteration limit reached; giving up after # trials` | 43 | 아니오 / 예 | `sim_convergence_failed` | `Poles.status = 'failed'`와 함께 낸다(pz 실패) |
| `Warning: singular matrix: check node …` | 6 | 예 / 예 | `sim_singular_matrix` | |
| `Warning: Dynamic gmin stepping failed`, `Warning: True gmin stepping failed`, `Warning: source stepping failed` | 각 1 | 아니오 / 아니오 | `sim_convergence_failed` | 옛 정규식이 놓친 실패 |
| `Error: Could not find include file …` | 2 | 예 / 아니오 | `sim_model_not_found` | |
| `ERROR: fatal error in ngspice, exit(#)` | 2 | 예 / 아니오 | `sim_failed_other` | 앞 줄의 구체 코드가 있으면 그것을 우선한다 |
| `Error: no such device or model name …` | 8 | 예 / 아니오 | `sim_failed_other` | 내부 벡터 이름 대응 실패(어댑터 결함)로 드러남 |
| `Error: no such parameter …` | 1 | 예 / 아니오 | `sim_failed_other` | |
| `Warning from checkvalid: vector … is not available …` | 9 | 아니오 / 아니오 | 코드 없음(정보) | 그 op 파라미터는 `None`이 되고(§6) PC-1이 판정한다 |
| `Note: Starting … stepping`, `Note: Dynamic gmin stepping completed`, `Warning: Source/Drain conductance reset to # mho.` | 2·1·1·1·2952·2952 | 아니오 / 아니오 | 코드 없음(정보) | 실패 아님 |
| 회로 제목 줄 `Circuit: * …` | 12 | 예(거짓 적중) / 아니오 | 대응 대상 아님 | 위 규칙 |

* 열린 점(OP-3 몫, 계획과 다르지 않음): 'op 파라미터 이름 없음'과 '소자·모델 이름 없음'을 `sim_failed_other`에서 나눌지. 지금 초안은 나누지 않는다.

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
  "mc_enable_kinds": {"<켜는 법 종류>": {"per_instance_independent": bool, "samples_per_run": int|"many",
                                          "seed": "per_run_seed"|"none", "keep_identity_across_conditions": bool}},
                                          # P N3.3 '지원하는 켜는 법 종류', 표본 시드·정체 보존·소자별 독립(§10.4)
  "mc_distributions": [str],               # 분포 함수로 옮길 수 있는 분포 종류(예: "gauss")
  "geometry_unit_application": [str],      # 비 SI 기하 단위를 적용하는 방법(예: "global_directive", "instance_numbers")
  "instance_geometry_readback": bool,      # 시뮬레이터가 보고한 인스턴스 L·W·배수를 읽을 수 있음(§6, 완료 조건 4a)
  "case_insensitive_names": bool, "model_families": [str]
}
Calibration = {   # 모든 값은 출처 칸 필수
  "default_tolerances": {"reltol": {value, source}, "vntol": {...}, "abstol": {...}},
  "data_digits": {value, source},
  "wall_s_per_window": {value, safety_factor, measured_*..., source},   # 옛 oracle_config.json 그대로 이전
  "simulator_version_probe": {how, source},
  "global_geometry_directive": {"affects": [<IR 칸 경로>], "power": {<IR 칸 경로>: int}, "source": ...}
                                   # geometry_unit_application에 "global_directive"가 있을 때만 필수(§10.6)
}
```

* `mc_enable_kinds`의 값은 그 시뮬레이터의 RNG 성질이다(시드 지정, 실행당 표본 수, 표본 정체 보존, 소자별로 새로 뽑는지). 사례(ngspice, S-12): 켜는 법 `param_redefine`은 소자별 독립, 실행당 표본 1, 실행마다 시드, 조건(온도) 사이 정체 보존이다. 이 값은 OP-1 측정(S-12)을 출처로 OP-5에서 어댑터에 적고, PC-3·PC-6이 조합마다 다시 잰다.
* `global_geometry_directive.affects`는 그 시뮬레이터에서 전역 기하 단위 지시가 **다시 해석하는 IR 칸의 전체 목록**이고 `power`는 칸마다 단위의 거듭제곱(길이 1, 면적 2)이다. 출처는 시뮬레이터 매뉴얼 쪽 번호(R6)다. 목록 밖의 칸(이상 R·C·L 값, 전원 값 등)은 지시의 영향을 받지 않는다고 선언하는 것이 된다. 판정은 §10.6의 N4 동일성이 한다.

* ngspice 어댑터의 보정값은 지금 코드 값을 그대로 옮긴다. 출처 칸도 함께 옮긴다. 출처가 없던 값의 처리는 §14에서 정한다.
* **DC 풀이 허용오차(T-39)**: 쓰는 값의 순서는 (1) 입력 `simulator.options`의 선언값, (2) 어댑터 `default_tolerances` 선언값(출처 필수: 시뮬레이터 문서 쪽 번호 또는 측정 조건)이다. 둘 다 없거나, (2)에 출처가 없으면 실행하지 않고 `dc_tolerance_undeclared`로 멈춘다. 시뮬레이터 내부 기본값을 선언 없이 쓰지 않는다(숨은 상수 금지). 그래서 지금 `_NGSPICE_DEFAULT_TOL`(S-8)은 출처(R6 매뉴얼 쪽)가 채워져야 어댑터 선언값으로 쓸 수 있다. 채워지기 전에는 입력 `simulator.options`에 값이 있어야 한다(§14). 매뉴얼 원문 보관과 쪽 번호 채움은 **OP-2 병합 조건**이다(X-D4, v0.2.2).
* **필요한 키 집합은 양 종류마다 다르다**(N-2). 어느 측정이 어떤 키를 요구하는지 정해 두고, 그 측정에 필요한 키만 검사한다. 쓰지 않는 키가 없다고 멈추지 않는다.

  | 양 종류 | 필요한 허용오차 키 | 쓰는 곳 |
  |---|---|---|
  | 노드 전압과 그 차·비(V_os, V_sys, 스윙 경계, 노드 전압 비교) | reltol, vntol | §13.4 전파, §18.3 |
  | 전류(ID, 레일 전류, 전력) | reltol, abstol | §18.3 |
  | 파생 측정(dB·위상·교차 주파수·PM) | 원천 양의 키 + 데이터 자릿수(`data_digits`) | 옛 `data_rel_resolution`·`mp_resolution` |
  | 과도 창 판정(n_pp, floor') | reltol, vntol | C10 계약 §1(a)·(b) |

  `dc_tolerance_undeclared`는 요청된 측정에 필요한 키 가운데 하나라도 (1)·(2) 어디에도 없을 때 낸다.
* 이 허용오차는 시뮬레이터 성질이지 PDK 성질이 아니므로 오라클 기술자에는 두지 않는다(§10, 계획 N0 값 원칙, 처음 반영 v0.5.1 N0).
* `wall_s_per_window`가 없는 어댑터에서 C10 과도를 요청하면, 사용자 `--timeout-s`가 있을 때만 실행하고 없으면 `adapter_calibration_missing`이다(P N3.3).

### 8.4 C10 조기 종결(D-1, G-13)

| 어댑터 능력 | 실행 | 판정 |
|---|---|---|
| `tran_early_stop` 참 | 어댑터가 `EarlyStopRule`을 방언으로 옮겨 시뮬레이터 안에서 창 단위로 멈춘다 | 코어가 결과 시간열로 같은 기준을 다시 검증(지금 `transient_decision`과 같다) |
| 거짓 | **후보 둘(G-13, 확정은 OP-4)**: (가) tstop까지 전체 창을 한 번 실행하고 코어가 사후 판정 / (나) 창 j마다 tstop = t_end + j·W로 처음부터 다시 실행 | 코어가 같은 기준 적용 |

* 어느 쪽을 기본으로 할지는 OP-1 기준선의 창당 시간으로 비용을 재고 **OP-4가 정한다**(P OP-0 목록 'G-13 후보·측정 방법, 확정은 OP-4'). 이 문서는 후보 둘과 측정 방법만 정하고 고르지 않는다.
* **측정 방법**(OP-1에서 이 방법으로 잼, S-19): 기준선의 폐루프 과도 실행마다 창 하나 비용 c = (실행 끝 파일 시각 − 넷리스트 시각) / 실행 창 수로 두고, (가) = 계획 창 수 K × c, (나) = c·K(K+1)/2(K = 판정이 난 창, 또는 계획 창 전부)를 합한다. 같은 기계·순차 실행·다른 시뮬레이터 부하 없음 조건을 기록한다.
* **측정값**(기록, S-19): 지금 137.7 s, (가) 146.8 s, (나) 463.2 s(판정 창)·513.2 s(계획 창). OP-4는 이 값과, (가)에서 시간 상한에 걸려 `failed`가 되는 사례(X-2)가 기준선에 있는지를 함께 보고 고른다. 그 사례 유무는 OP-4 착수 때 검증자가 같은 기록에서 센다.
* **독립 기준으로 남기는 것**(N-9): 지금 ngspice nutmeg 스크립트(`stability_control`)는 Python `early_window`와 같은 판정을 따로 구현한 것이다. 재구성 뒤에도 이 둘의 일치를 test로 둔다. 어댑터 방언 스크립트의 창 판정 결과를 코어 `early_window`와 비교하는 것이 oracle 종류 (b) '다른 방법의 참조구현' 독립 기준이다(`adapters/ngspice/test_dialect_stability.py`).
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
  * **확정(v0.2, 사용자 결정 O-3 = DV-1 (가), 계획 v0.5 N3.4 '파일마다 정본 한 곳')**: 엔진 선언에 없는 파일만 기술자 `extra_sources = {key: {path, sha256, base, provenance}}`에 둔다. 한 파일이 두 곳에 나오지 않도록 로더가 검사한다(`descriptor_source_duplicated`).
  * `provenance`(v0.2.4, P G-5 O-3): 엔진 선언 `sources`와 같은 수준의 출처다. 원본 `PROVENANCE.txt` 위치, 또는 웹 링크 + 저장소 커밋을 적는다. 비어 있으면 기술자 스키마 검증(`oracle_pdk_descriptor/1` 필수 칸)에서 거부한다.

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
      "geometry_unit": {"source": <엔진 선언 quantity 키>} | "si",      # 모델 카드 면적 의존 식이 전제하는 L·W 단위(§10.6)
      "parallel_multiplier": {                                          # (v0.2.4, O-6 D-b) 병렬 배수 전달 규칙(§10.6)
        "to": [{"target": "instance_multiplier"} | {"target": "model_param", "name": {"value": "..."} | {"expr": ...}}],
        "source": <원본 근거: 모델 파일 source 키 + 그 파라미터가 면적 식에 들어감을 보이는 위치 식>
      },
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
* (v0.2.4) `kinds.<kind>.geometry_unit`·`parallel_multiplier`는 스키마상 선택 칸이지만, 없는 kind를 쓰는 벤치는 실행 전에 거부된다(§10.6). 스키마 단계에서 막지 않는 이유는 '규칙을 선언하지 않은 기술자가 실제로 거부됨'을 실행 경로에서 보이는 것이 OP-3 병합 조건 (a)이기 때문이다.
* (v0.2.4) `mc`·`diagnostic` 칸은 선택이다. OP-2가 만드는 기술자에는 없고 OP-5가 더한다(§20). 없으면 MC·진단 요청은 `mc_method_unsupported`로 거부한다(기술자 쪽 미선언. 어댑터 능력이 없을 때의 `adapter_capability_missing`과 구별한다).

### 10.3 sky130 사례 값

* 사용자가 PDK 문서에서 선언하는 값이다(P N3.4). 값을 채우는 card에서 사용자 확인을 받는다. 채우는 card는 칸마다 다르다(§20): `mc`·`diagnostic` 칸은 OP-5, 나머지는 OP-2다.
* 칸별 상태:
  * `geometry_unit`(OP-2): 엔진 선언 quantity `mismatch_slope_geometry_unit_m`(출처 `models/all.spice` `.option scale`, S-13)를 source로 가리키는 안이 OP-1 측정과 맞는다. 값 확정은 OP-2 사용자 확인이다.
  * `parallel_multiplier`(OP-2): OP-1 측정(S-13 T6)은 '인스턴스 배수 + 래퍼 모델 파라미터 `mult`' 둘 다 줄 때 편차가 면적 의존대로 줄어듦을 보였다. 근거 위치는 카드 식 `sqrt(l*w*mult)`(`…tt.pm3.spice:67`)와 래퍼 기본값(`:30`)이다. 값 확정은 OP-2 사용자 확인이다.
  * `mc.enable`(OP-5): OP-1 측정(S-12)으로 켜는 법 종류는 `param_redefine`(카드의 불일치 변수를 분포 함수로 다시 선언)이 사례로 확인됐다. 대상 변수 목록은 엔진 선언 `mismatch_models.<kind>.parameters`와 모델 카드의 변수 선언 위치 식으로 가리킨다.
  * `mc.distribution`(OP-5): 카드의 통계 블록(`…tt.pm3.spice:19-27`, 주석 처리, S-12)을 위치 식으로 가리킨다. 그 파일은 엔진 선언 source(`nfet_01v8_tt_model_card`·`pfet_01v8_tt_model_card`)이므로 sha256 정본은 엔진 선언이다.
  * `extra_sources`(OP-2): 엔진 선언에 없는 include 파일(사례 pmos `lod.spice`)의 경로·sha256·출처.
  * `corners`: tt 하나만 엔진 선언에 있다. 다른 코너는 범위 밖(P T-32)

### 10.4 네이티브 MC 켜는 법과 분포 값 위치(O-1, O-6 D-a, G-9)

```
"mc": {
  "method": "native",
  "enable": {                                   # 켜는 법 종류 하나와 그 대상(P N3.4)
    "how": "lib_section" | "param_switch" | "include" | "param_redefine",
    "target": <종류별 대상, 아래 표>,
    "source": <원본 근거(source 키 + 위치 식)>
  },
  "distribution": {                             # 분포 값의 위치만. 값은 적지 않는다(O-6 D-a)
    "source": <엔진 선언 sources 키 또는 extra_sources 키>,
    "locate": {"pattern": ..., "fields": {"kind": <그룹>, "std": <그룹>, ...}}    # 엔진 선언 식 형식
  } | null,                                     # how가 PDK 쪽 통계 기능(lib_section·param_switch·include)이면 null 허용
  "mismatch_only": {"global_off": {"how": ..., "value": ...}, "source": <원본 근거>},   # 전역 공정 변동 끄는 법
  "requires": {"per_instance_independent": true, "keep_identity_across_conditions": true}   # 오라클 MC 판정의 요구
}
```

| `enable.how` | `target` | 분포 값 |
|---|---|---|
| `lib_section` | 통계 lib 섹션(source 키 + 섹션 이름) | PDK 섹션 안(오라클은 읽지 않음), `distribution` = null |
| `param_switch` | 스위치 파라미터 이름과 켬·끔 값(원본 근거) | PDK 파일 안, `distribution` = null |
| `include` | 더 include할 원본(source 키) | 그 파일 안, `distribution` = null |
| `param_redefine` | 다시 선언할 불일치 변수 목록(엔진 선언 `mismatch_models.<kind>.parameters` + 모델 파일의 선언 위치 식) | **필수**: PDK 원본의 통계 선언 위치(`distribution`). 어댑터가 읽은 분포 값을 시뮬레이터 분포 함수로 옮긴다 |

* **값의 출처 규칙**(O-6 D-a): 분포 종류·표준편차 같은 분포 값은 `distribution.locate`가 원본에서 읽은 값만 쓴다. 코어 `descriptor.py`가 원본 sha256을 대조한 뒤 읽어 어댑터에 값으로 넘긴다. 기술자에 값이 직접 적혀 있으면(`distribution` 안에 `locate` 대신 숫자·분포 이름 칸) `mc_distribution_inline`, `locate`가 없거나 0개를 찾으면 `mc_distribution_unlocated`, 가리킨 원본 sha256이 다르면 `pdk_descriptor_stale`이다(완료 조건 4의 깨진 변형 셋).
* **난수**: 시뮬레이터 RNG다. 코어는 표본마다 시드만 정하고(요청 `McNative.seed`와 표본 번호에서 정하는 결정적 규칙, 위치 `core/mc_math.py`, 규칙 문안은 OP-5. 같은 seed·같은 번호면 같은 시드가 PC-6의 전제다), 표본 값을 계산하지 않는다. 판정 MC 경로에는 '오라클이 계산한 값을 변수에 넣는' 경로가 없다(진단 경로 §13은 판정 밖).
* **요구 대 능력**(기본안 B-11): 표본 실행 방법(시드 지정, 실행당 표본 수, 조건 사이 정체 보존, 소자별 독립)은 시뮬레이터 RNG 성질이라 어댑터가 켜는 법 종류마다 선언한다(§8.3 `mc_enable_kinds`, P N3.3). 기술자는 그 조합이 만족해야 할 **요구**(`requires`)만 적는다. 코어는 실행 전에 (기술자 `enable.how` ∈ 어댑터 `mc_enable_kinds`), (요구 ⊆ 그 종류의 어댑터 선언), (`distribution`이 있으면 그 분포 종류 ∈ 어댑터 `mc_distributions`)를 확인하고, 하나라도 어기면 `mc_method_unsupported`다. 선언이 실제로 맞는지는 PC-3 (b)(소자별 독립)·PC-6(정체 보존)이 조합마다 잰다.
* **표본마다 별도 실행**: 어댑터 선언 `samples_per_run = 1`이면(사례 ngspice, S-12 T5) 어댑터는 `McNative` 표본마다 실행을 따로 하고 표본 시드를 바꾼다. 결과 `McResult`는 같은 모양이다.
* 오라클은 분포·면적 의존 식을 갖지 않는다. 면적 의존은 모델 카드 식이고, 그 식에 들어가는 기하 단위·병렬 배수는 §10.6 규칙이 전달한다(P N3.4).
* 선언되지 않은 `method`·`enable.how`는 `mc_method_unsupported`다.
* sky130·ngspice 사례: OP-1(S-12)에서 `param_redefine`으로 소자별 독립이 확인됐다(O-1 (4) 사용자 결정 불요, 계획 X-12). 직접 섭동 대안은 설계하지 않는다.

### 10.5 진단 변수(O-1 (5))

```
"diagnostic": {
  "per_kind": {"<kind>": {"variables": {"source": <엔진 선언 mismatch_models.<kind>.parameters>},
                          "instance_param_rule": {"expr": <모델 파일에서 소자별로 덮어쓸 파라미터 이름을 읽는 식>},
                          "value_rule": {"expr": <표본 z를 파라미터 값으로 바꾸는 식, 원본 근거 포함>}}}
}
```

* 진단 경로(§13)만 쓴다. 판정·능력 기록에는 쓰지 않는다.
* (v0.2.4 고침) `value_rule`은 z를 **변수 값**으로 바꾸는 식만 담는다. 그 변수가 면적 의존 식을 지나 파라미터 섭동이 되는 과정은 모델 카드가 하고, 거기에 들어가는 기하 단위·병렬 배수는 §10.6 규칙이 소자 줄로 전달한다. 그래서 옛 `z·1e-6/√m`(S-4)의 단위 배율 `1e-6`과 `1/√m`은 기술자 식에도 옮기지 않는다(그 둘은 §10.6이 넷리스트에서 해결하는 것을 값으로 덮던 것이다, S-13. P N3.6 삭제 목록 '변수값 z·1e-6/√m 배율'). sky130 사례의 `value_rule`은 `distribution`이 가리키는 표준편차를 곱하는 식이고, 값 확정은 OP-5 사용자 확인이다.
* 진단 경로가 옛 넷리스트 형식(SI 기하 + `m=`)의 표본을 재현하는 검증 절차(§13.2)는 이 규칙과 다른 넷리스트를 쓴다. 그 차이가 MC 수학 비트 동일 판정에 주는 영향은 §19.2 DV-3에 올렸다.

### 10.6 기하 단위·병렬 배수 전달(O-6 D-b, P G-5·G-9)

* **선언 위치**: kind마다 `geometry_unit`과 `parallel_multiplier`(§10.2). 둘은 '모델 호출 형식'의 일부다(P N3.4).
* **미선언 거부**(P OP-3, N9): 어댑터의 소자 줄 작성기는 공칭·MC·진단 공용 하나이고 규칙도 하나다. 그래서 공칭을 포함한 모든 해석에서, 벤치가 쓰는 kind의 두 칸 가운데 하나라도 없으면 실행 전에 `descriptor_geometry_undeclared`로 거부한다. 기본값으로 SI나 배수 1을 쓰지 않는다(P NFR-P6).
* **기하 단위 적용**:
  * `geometry_unit = "si"`: 어댑터는 IR 값(SI 길이)을 그대로 쓴다.
  * `geometry_unit = {"source": …}`: 코어가 원본에서 단위 u(m)를 읽어 어댑터에 넘긴다. 어댑터는 자기 `geometry_unit_application` 가운데 하나로 적용한다. 없으면 `geometry_unit_unsupported`.
  * `"global_directive"` 방법(사례: 전역 scale 지시): 그 지시는 벤치 안 다른 원소에도 걸린다. 그래서 어댑터는 보정값 `global_geometry_directive.affects`의 **모든 IR 칸**을 u^power로 나눈 숫자로 쓰고, 목록 밖 칸은 그대로 쓴다. `affects` 선언이 없으면 이 방법을 쓸 수 없다(`geometry_unit_unsupported`). 이 처리가 맞는지의 판정 기준은 계획 G-9대로 **N4 기준선 동일성**이다(OP-3 병합 조건 (b): 공칭 op·ac 결과 N4-2 동일). 예: MOS L·W·확산 ad/as/pd/ps(면적은 power 2), 기하로 주는 수동 소자 칸. 이상 R·C·L 값·전원 값은 목록에 없으면 그대로다.
  * `"instance_numbers"` 방법: 지시 없이 인스턴스 숫자만 바꾸는 방언이 선언할 수 있는 이름이다. 첫 어댑터는 이 방법을 선언하지 않는다(기본안).
* **병렬 배수 전달**: IR `Mos.n_fingers`를 `parallel_multiplier.to`의 모든 대상에 같은 값으로 넘긴다(`instance_multiplier` = 방언의 인스턴스 병렬 배수, `model_param` = 그 이름의 호출 파라미터). 대상을 빼거나 더하지 않는다.
* **소자 줄 변화 기록**(P OP-3 병합 조건 (b)): 첫 조합 선언값을 적용하면 소자 줄 표기가 기준선과 달라질 수 있다(예: 숫자 단위, 배수 파라미터 추가, 전역 지시 줄, 그 지시가 든 include). 검증자는 N4-3 넷리스트 정규화 대조로 차이를 기록하고, 차이가 기하 단위·병렬 배수 선언에서 나온 것뿐임을 기록으로 보인다. 판정은 결과(N4-2)가 한다.
* **전역 지시가 든 원본**: 사례(sky130)에서 scale 지시는 모델 묶음 밖 파일(`models/all.spice`)에 있고 그 파일은 모든 모델을 함께 부른다(S-13). 어댑터가 지시를 넷리스트에 직접 쓰는지, 그 원본을 include하는지는 방언 선택이고 어댑터가 정한다. 어느 쪽이든 모델 묶음 비교(§12.5)와 캐시 키(§9)에 그 결과가 반영된다.
* **읽기 확인**: 어댑터 능력 `instance_geometry_readback`이 참이면 결과 `OpTable.instance_geometry`(§6)에 시뮬레이터가 보고한 L·W·배수를 SI·IR 단위로 돌려준다. 완료 조건 4a는 모든 실행에서 이 값이 IR·기술자 선언대로임을 단언한다. 첫 어댑터는 이 능력을 선언해야 한다(4a 실행 조건).

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
                  | {"kind": "net", "net": "<참조 넷>", "source": "<출처>"}
                  | {"kind": "rule_e_input_cm", "source": "<출처>"}   # 규칙 (e): 출력 = 입력 공통모드
                  # 단일 출력 기준 셋 모두 source 필수(엔진 결과 `output_reference`의 출처를 그대로 옮긴다). 없으면 reference_undeclared
```

* `output_reference`(v0.2, offset-trim G-15): V_sys 측정의 출력 기준이다. 선언 기준을 온도와 무관하게 그대로 쓰고, 온도마다 다시 풀지 않는다(offset-trim design §20.1). 오라클은 이 값을 엔진 결과 JSON에서 직접 읽지 않고 입력으로만 받는다. 엔진 결과 `output_reference` 칸(offset-trim design §13)을 오라클 입력으로 옮기는 일은 입력 생산자가 한다(§11.4). 이 칸이 없는데 V_sys 측정을 요청하면 `reference_undeclared`로 멈춘다.

* `options`는 옛 `testbench.options`를 옮긴 것이다. 키 이름은 어댑터 방언이라 어댑터가 검증한다(기본안). 코어가 쓰는 해 정확도(`reltol` 등)는 어댑터가 `Resolution`으로 정규화해 돌려준다.
* 삭제 칸: `process.models`(`subckt`·`includes`·`op_probe`·`polarity`), `process.ngspice_exe`, `process.diffusion`(기술자로 이동, 소자별 `devices[].diffusion`은 유지), `testbench.options`(`simulator.options`로 이동), (v0.2.4) `process.lut_reference_width_m`, `process.provenance`(S-21: 오라클 본체가 읽지 않는 생산자 내부 값. 출처 기록은 결과의 기술자 지문(P FR-P9)과 최상위 `provenance`가 맡는다).
* (v0.2.4, 기본안 B-12) 새 스키마의 `process`는 위에 정의한 칸 밖의 키를 거부한다(`additionalProperties: false`). 옛 스키마는 `process`에 정의 밖 키를 허용해(`O/oracle_input.schema.json` `process`에 `additionalProperties` 없음) 생산자 내부 값이 입력에 섞였다(S-21). 최상위 `provenance`(어댑터 출처·경고, `oracle_input.schema.json:229`)는 그대로 둔다.

### 11.2 온도·코너 해석 순서

입력 `process.temp_c`/`corner`가 있으면 그것을 쓰고, 없으면 LUT 메타 값을 쓴다. LUT 메타에 기록이 없으면(`recorded=False`) 둘 다 입력에 있어야 하고, 없으면 거부한다(`oracle_condition_missing`, 기본안).

### 11.3 옛 형식

`process.models` 또는 `process.ngspice_exe`가 있으면 `oracle_input_format_old`로 거부한다. 이중 지원은 하지 않는다(P D-5, X-5).

### 11.4 생산자

* `legacy_adapter.py`(master): `process_from_lut_generator`(`O/legacy_adapter.py:157`)를 지우고, 새 `process`(기술자 참조) + `simulator` 블록을 낸다. 생성기 소스 정규식 읽기는 없어진다.
  * (v0.2.4) 그와 함께 finger 분할 기준 폭의 대체값(`process["lut_reference_width_m"]`, `:261-264`)도 없어진다. 기준 폭은 dump `lut_meta.W_ref_m`만 쓰고, 그 값이 없으면 `blockers`에 사유를 넣고 멈춘다(조용한 대체 금지, P NFR-P6. 기본안 B-13). 대체값은 경고 없이 쓰이므로(`:264`, `:263` 경고는 두 값이 다를 때만), 기준선 생산에 쓴 dump 가운데 `lut_meta.W_ref_m`이 없는 것이 있는지는 OP-2 착수 때 검증자가 dump 파일에서 직접 센다.
* 미병합 `ng-bridge`: 이 card는 고치지 않는다. 형식 계약 = §11.1 스키마다. U16 흡수 때 맞춘다.
* `output_reference`의 생산: 엔진 결과 JSON의 `output_reference` 칸을 그대로 옮긴다. 생산자는 엔진→오라클 입력 변환기(U16)와 offset-trim 구동기다. `legacy_adapter`는 옛 엔진에 그 칸이 없으므로 내지 않는다. 그 입력으로 V_sys를 요청하면 `reference_undeclared`다.

### 11.5 입력 변환 필드 대응표(P N4-2a, 검증자 변환 스크립트의 유일한 근거)

옛 형식(`spice_oracle_input/1`) → 새 형식. 검증자 소유 변환 스크립트(초안 `wt/_scratch_op1/n4_convert_input.py`)는 이 표만 따른다. 표 밖 `process` 키가 나오면 변환을 거부하고 기록한다(초안의 동작 그대로).

| 옛 칸 | 새 칸 | 처리 |
|---|---|---|
| `process.lut_npz` | `process.lut_npz` | 그대로 |
| `process.models` | (없음) | 삭제. kind 정보는 기술자 `kinds` |
| `process.ngspice_exe` | `simulator.exe` | 옮긴 뒤 삭제 |
| `process.diffusion` | (없음) | 삭제. 기술자 `diffusion`. 옛 값은 변환 기록에 남겨 OP-2 대조에 쓴다 |
| `process.lut_reference_width_m` | (없음) | (v0.2.4) 삭제. 오라클 본체가 읽지 않는다(S-21). 옛 값은 변환 기록에 남긴다 |
| `process.provenance` | (없음) | (v0.2.4) 삭제. 같은 이유(S-21). 옛 값은 변환 기록에 남긴다 |
| `testbench.options` | `simulator.options` | 옮긴 뒤 삭제. 없으면 기록에 `options_absent`(X-D4 영향 대상, S-20) |
| (없음) | `process.descriptor` | 변환 인자로 받은 기술자 경로·sha256. 없으면 그 변환 결과는 N4에 쓰지 않는다 |
| (없음) | `simulator.adapter` | 변환 인자 |
| (없음) | `process.corner`·`temp_c`, `output_reference` | 쓰지 않는다(옛 형식에 없음, §11.2·§11.4) |
| 그 밖 모든 칸 | 같은 칸 | 바꾸지 않는다 |

**결과 칸 이름 대응**(N4 비교 때, v0.2.4): 새 결과에서 이름이 바뀐 칸은 아래 대응으로 비교한다. 값은 바꾸지 않는다.

| 옛 결과 칸 | 새 결과 칸 |
|---|---|
| `ngspice_rc`(모든 실행 기록) | `status.rc`(`RunStatus`) |
| `ngspice_runs`(swing) | `sim_runs` |
| 지문 칸(어댑터·기술자·능력 기록 id) | 새 칸, 비교 제외(P N4-2) |

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
| PC-10 | 차동 입력쌍 + 출력 부하 + DC servo의 최소 IR(회로·PDK 이름 없음). 불일치는 끈다. 입력 `output_reference` 네 종류마다 하나씩 | (a) 온도 점마다 V_sys(T)를 낸다. 부호 규약은 offset-trim 계획 N0.1(V_sys,s = `output_error_v` / A_dm, 부호 있는 계통 offset)과 offset-trim design §0의 V_in(c) = −(V_sys0 + s·t·δ(c))를 따른다. 즉 servo가 출력을 선언 기준에 붙들 때의 입력 차동 전압이 V_in이고, 불일치·DAC가 없으면 V_sys(T) = −V_in(T)다. 기준은 선언값을 온도와 무관하게 그대로 쓴다(offset-trim G-15) (b) 온도 sweep 실행의 T_j 값 = T_j 단독 실행 값(비트 동일) (c) `output_reference`가 없으면 `reference_undeclared`로 멈춘다 (d) 각 값에 DC 풀이 허용오차의 입력 환산 전파값(§13.4)을 함께 낸다 | 기준 해를 버리고 흔들림만 내는 경로, 온도마다 기준을 다시 푸는 경로, `output_reference` 없이 기본 기준을 몰래 쓰는 경로 |

* (v0.2.4) PC-3 (c) '끈 실행 = 공칭 비트 동일'은 OP-1에서 출력 자릿수 동일까지만 확인됐다(S-12 15행). 비트 비교는 OP-6 PC-3 실행이 한다. PC-6의 사례 근거는 S-12 6행(같은 시드 표본이 세 온도에서 같음)이다.
* (v0.2.4) PC-3의 깨진 변형에는 분포 값 출처의 깨진 변형 셋(§10.4: 값 직접 기재, 원본 sha256 불일치, 위치 없음)도 넣는다(완료 조건 4). 이 셋은 실행 전 기술자 검증에서 거부되므로 시뮬레이터를 부르지 않는다.
* PC-4는 삭제됐다(O-1). MC 크기 판정은 offset-trim TR-7 §17-1 비교가 맡는다.
* PC-9는 LUT 생성 측정으로 옮겼다(D-4, §16).
* PC-11은 철회됐다(T-35).

### 12.3 PC-3 표본 수

* 기본안(P 계획): `sample_count(r)` = ceil(1 + 1/(2 r²))를 재사용한다. **r의 출처**(N-5): 능력 확인은 특정 회로 입력에 묶이지 않으므로, r은 `oracle_run capability` 실행 인자 `--rel-resolution`으로 검증자가 선언한다. 기본값은 없고, 없으면 실행을 거부한다. 같은 r을 쓰는 소비 측정(MC offset 판정의 입력 `offset_mc.rel_resolution`)과 비교할 수 있도록 n·r을 능력 기록 지문에 넣는다(§12.4).
* 이 규칙은 σ 추정용이라 존재 판정에는 과하다. 예를 들어 r = 0.05면 201 표본이다.
* 대안(존재 판정 최소 수)은 P G-11에 열려 있다. 기준 확률의 출처를 새 상수 없이 정하지 못해 이 문서도 대안을 고르지 않는다. 비용은 OP-1에서 기록했다(S-12 13행: 소자 쌍 벤치 표본당 0.152 s, 표본마다 별도 실행. r = 0.05의 201 표본이면 약 30 s 규모. PC-3은 (a)(b)와 (d) 두 묶음을 돌린다).

### 12.4 능력 기록 `oracle_capability/1`

```
{
  "schema": "oracle_capability/1", "record_id": "<sha256 of canonical body>",
  "descriptor_fp": {...}, "adapter_fp": {...}, "check_code_fp": "<O/core/capability.py 등 sha256>",
  "lut": {"path", "slice_model_files_sha256": {...}},
  "checks": {"PC-1": {"bench_ir_fp", "requests", "measured", "resolution", "n", "verdict", "notes"}, ...},
  "conditions": {"temps_c": [...], "corner": "..."},
  "mc_sampling": {"rel_resolution": r, "n": n, "seed": ...},     # PC-3·PC-6 표본 규모. record_id 계산에 들어간다(지문)
  "created_by": "verifier", "date": "..."
}
```

* 저장 위치는 `O/capability/<기술자 지문 앞부분>__<어댑터 지문 앞부분>.json`(기본안)이다.
* `record_id`는 내용의 정규 JSON sha256이다. offset-trim Δ_T 출처 지문과 `verified_by`(D-6)가 이 id를 가리킨다.

### 12.5 모델 묶음 비교 규칙(P N3.5, `core/bundle.py`)

kind마다 sha256 **값** 집합으로 비교하고, 경로는 비교하지 않는다.
* (i) 그 kind가 쓴 LUT 슬라이스들의 `model_files_sha256` 값 집합 ⊆ 어댑터 `model_bundle`의 sha256 집합
* (ii) 기술자가 정한 호출 모델(`kinds.<kind>.name`)을 정의한 파일의 sha256 ∈ LUT 기록 집합. 정의 파일은 묶음 파일 가운데 그 이름의 `.subckt`/`.model` 정의가 있는 파일이다.
* LUT 기록이 빈 표이면 `lut_model_provenance_missing`이다. 지금 LUT의 기록은 OP-1 (ii)에서 38/38 있음으로 측정됐다(S-15, 계획 X-14 확인됨).

### 12.6 게이트와 배선

| 게이트 | 위치(진입점) | 요구 |
|---|---|---|
| 공칭 자동 대조 | `oracle_run` 모든 실행, 벤치 실행 직전 | §12.5 통과 |
| MC 게이트 | `oracle_run`의 `offset_mc` 측정 진입 | 유효 능력 기록 + PC-3 통과 |
| 온도 게이트 | 해석 요청 `Condition.temp_c`가 LUT `temp_c`와 다르거나 온도가 여럿인 모든 실행 | 유효 능력 기록 + PC-5·PC-6·PC-8·PC-10 통과 |
| 진단 금지 | `core/compare.py`·`core/capability.py`의 입력 | 진단 결과가 들어오면 `diagnostic_not_a_gate` |

* 기록이 유효하려면 descriptor_fp·adapter_fp·check_code_fp·LUT 기록이 지금 값과 모두 같아야 한다.

### 12.7 공정 무관 증거

같은 `core/capability.py`가 두 기술자에서 돈다. 하나는 sky130 기술자(사례)이고, 다른 하나는 손 모델 픽스처 기술자다(시뮬레이터 내장 단순 모델 + 면적 의존이 있는 선언 불일치 변수, test 작성자 소유). 손 모델 기술자의 네이티브 MC 켜는 법은 픽스처가 정한다. 실제 두 번째 PDK는 완료 조건이 아니다(D-8).

* **손 모델 픽스처는 정본 하나다**(P v0.6.1 B-2): `O/tests/fixtures/hand_model/` 아래 기술자 파일 하나(`hand_model.oracle_descriptor.json`, 기본안 B-14), 그것이 sha256으로 참조하는 `gmid_pdk_decl/1` 형식 선언 파일(엔진 로더는 읽지 않는 픽스처), 손 모델 파일(면적 의존 식은 test 작성자가 쓰고 PDK 공식은 쓰지 않는다)이다. **OP-5가 만들고**(완료 조건 4a), OP-6 능력 확인과 이 절의 공정 무관 증거는 같은 파일을 재사용한다. OP-6은 새 손 모델 기술자를 만들지 않는다.
* 손 모델 기술자도 `geometry_unit`·`parallel_multiplier`·`mc.distribution`을 선언한다. 그래서 §10.4·§10.6의 미선언 거부와 분포 값 출처 거부가 sky130 기술자와 같은 코드 경로로 손 모델에서도 돈다.
* 4a (ii)의 '단위만 다른 둘째 기술자'는 정본 파일이 아니라 test 안에서 정본으로부터 파생한 변형이다(깨진 변형과 같은 지위, P v0.6.2). 저장소에 둘째 파일로 두지 않는다.

### 12.8 offset-trim N3.9-3 재대조(P N3.5.1, v0.2.4)

* **기준 갱신**: 계획 N3.5.1은 offset-trim 계획 v0.5.2(`trim-plan-r1` `a293411`, 미병합) 455-462행을 기준으로 했고, 그 계획이 확정되면 다시 대조하라고 했다(OP-0 design 착수 조건). 지금 master의 offset-trim 계획은 **v0.5.6**(`86e5adc`, 2026-10-16)이고 v0.5.4에서 사용자 승인됐다(`0aac966`, T-29~T-37). N3.9-3은 **466-473행**이다(`docs/01-plan/features/offset-trim.plan.md`, base `1ba9461`에서 다시 잼).
* **대조**(master v0.5.6 N3.9-3 일곱 항목 → 이 문서):

| # | master v0.5.6 N3.9-3(요지, 행) | 이 문서 | 담김 | a293411 대비 |
|---|---|---|---|---|
| 1 | MC 불일치가 실제로 분산을 만든다(네이티브 MC). 크기 일관은 능력 기록이 아니라 TR-7 판정(467) | PC-3(§12.2), MC 게이트(§12.6) | 예 | 크기 일관을 TR-7로 옮긴 문구가 offset-trim 쪽에 이미 반영됐다. 계획 N3.5.1 1행의 '알림 항목'은 처리됨 |
| 2 | 온도 지정이 동작점을 바꾸고, 읽은 온도 = 요청 온도(468) | PC-5 | 예 | 같음 |
| 3 | **같은 seed의 네이티브 MC 표본** 정체가 온도 사이에 보존된다. 꼬리 판정(G-14)이 기댄다(469) | PC-6, `McNative.keep_identity`(§5), 어댑터 `keep_identity_across_conditions`(§8.3) | 예 | 'same seed·네이티브 MC'와 G-14 의존이 더해졌다. PC-6 정의(같은 seed, 비트 동일)와 맞는다 |
| 4 | 오라클 모델 = 엔진 LUT 모델(해시 대조)(470) | PC-7, §12.5 | 예 | 같음 |
| 5 | LUT `temp_c`와 따로 온도를 받는다(471) | PC-8, §11.1 `process.temp_c`, §11.2 | 예 | 같음 |
| 6 | 온도 점마다 V_sys(T)(472) | PC-10, §11.1 `output_reference` | 예 | 같음(G-15는 offset-trim design TR-0T가 닫음, §1.3) |
| 7 | (철회, v0.5.4) 결정적 불일치 벡터 표본 요구(PC-11)는 T-35로 필요 없음. 결정적 섭동은 진단 전용(473) | PC-11 철회(§12.2), 진단 경로 §13 | 해당 없음 | a293411의 '(G-14에서 채택하면) 결정적 벡터'가 철회로 바뀌었다 |

* 결론: 일곱 모두 이 문서 항목과 맞고, 이 문서가 바꿀 것은 없다. 계획 N3.5.1의 기준 커밋 문구(`a293411`)는 계획 소유라 이 card가 고치지 않는다(§19.2 아래 '알림').
* offset-trim N3.9 '순서 의존' 문단(master 477행)은 아직 'oracle-portability 계획은 초안(브랜치 oport-plan, 승인 전)'이라고 적는다. 그 문구는 offset-trim 소유라 고치지 않고 알림만 한다(§19.2 아래 '알림').

---

## 13. 결정적 섭동 진단 경로(O-1 (5), 계획 N3.5)

### 13.1 입력

`oracle_run --diagnostic <파일>`로 받는다. 파일 스키마는 다음과 같다.

```
{"schema": "oracle_diagnostic/1",
 "vectors": [{"id": "...", "values": {"<소자 이름>": {"<진단 변수>": <z 값>}}}],
 "base": "nominal"}
```

* 코어가 `McDiagnostic` 요청을 만든다. 어댑터는 기술자 `diagnostic` 식(§10.5)으로 z를 변수 값으로 바꿔 소자별로 넣는다. 기하 단위·병렬 배수는 공칭과 같은 소자 줄 규칙(§10.6)으로 전달한다.
* 결과는 벡터마다 `OpTable`과 코어 MC 수학의 V_os다. `mc_math.py`의 표본 처리 함수를 네이티브 MC와 같은 함수로 지난다.

### 13.2 검증자 MC 수학 동일성(P N4)

1. 검증자는 기준선 `offset_mc` 출력의 `seed`, `n_requested`, `mismatch_vars`(소자별 변수 목록)를 읽는다.
2. `numpy.random.default_rng(seed).standard_normal()`을 옛 순서(표본 → 소자(입력 `devices` 순서) → 변수)대로 불러 z를 재현한다. 그 순서는 S-4다.
3. 같은 z를 진단 벡터로 넣는다. 표본 0은 모두 0이다.
4. 표본별 V_os와 σ_in·mean_in이 기준선과 비트 동일이면 통과다. 다르면 멈추고 보고한다.

* 이 절차는 검증 절차이고 게이트가 아니다(O-1 (5)).
* OP-1이 1·2단계를 기준선 안에서 해 봤다(S-22): 재현 z가 기준선 넷리스트 값과 비트 동일, 기준선 로그의 표본별 op 값으로 다시 낸 σ_in·mean_in도 비트 동일이다.
* 옛 넷리스트는 변수 값으로 z·1e-6/√m를 넣고 SI 기하 + `m=`를 썼다(S-4, S-13). 새 경로는 §10.5·§10.6대로 변수 값 z와 선언된 기하 단위·병렬 배수를 쓴다. 같은 물리 표본이지만 넷리스트가 달라 시뮬레이터 출력이 마지막 자리에서 다를 수 있다. 그때 4단계 '비트 동일'을 어떻게 판정할지는 계획 문구와 다른 결정이 필요해 §19.2 DV-3으로 올렸다(멈춤).
* (v0.2.4) 차동 이득 A의 실수 판정 상수 `1e-3`은 값·동작 그대로 옮긴다(O-6 D-c, §14). 그래서 이 상수로 기준선 `status`가 바뀌는 사례는 없다. 바꿨다면 170건이 뒤집혔다는 측정(S-14)이 D-c의 근거다.

### 13.3 TR-7 사용

offset-trim TR-7 §17-1에서 엔진 σ_in과 오라클 네이티브 MC σ_in이 어긋나면, 같은 진단 경로로 소자·변수별 결정적 기여를 재서 원인을 가른다. 결과는 진단 보고에만 실린다.

### 13.4 DC 풀이 허용오차의 입력 환산 전파(T-39, `core/mc_math.py`)

* 오라클이 내는 입력 환산 offset은 V_os = (V_out − V_out,ref)/A − (V_id − V_id,ref)다(S-4의 식. V_sys는 기준 표본 쪽 항).
* 각 노드 전압의 DC 풀이 오차 한계는 그 실행 `Resolution`의 reltol·|V| + vntol이다. 이것을 V_os 식에 1차로 전파한다:
  δV_os = (δV_out + δV_out,ref)/|A| + δV_id + δV_id,ref, 여기서 δV = reltol·|V| + vntol.
  차동 전압은 두 노드 오차의 합이다. A는 결정적 값이고 1차 전파에서 뺀다. 이 근사는 결과에 표시한다.
* 결과의 표본마다(그리고 V_sys(T)마다) `dc_resolution_in_V`로 싣는다. offset-trim의 trim 잔여 수렴 분해능은 이 값을 쓴다(T-39, offset-trim design §20.6). 새 상수는 없고, 값은 선언된 허용오차와 측정 전압에서만 나온다.

---

## 14. 옛 리터럴 상수 처리(계획이 정한 것과 정하지 않은 것)

| 상수 | 계획 | 이 문서 |
|---|---|---|
| `_NGSPICE_DEFAULT_TOL` | 어댑터 보정값으로(P N3.6) | `calibration.json` `default_tolerances`, 출처 = 시뮬레이터 문서 기본값. 문서 쪽수는 OP-0 원문 보관 뒤 채움(P R6). **출처가 채워지기 전에는 선언값으로 쓰지 않는다**(§8.3, T-39 숨은 상수 금지). 그동안은 입력 `simulator.options`에 허용오차가 있어야 실행된다 |
| `WRDATA_NUMDGT = 8` | 어댑터 보정값(P N3.3) | `calibration.json` `data_digits`, 출처 = 코드 주석의 ngspice-46 실측 |
| 차동 이득 실수 판정 상대 폭 `1e-3`(`|Im h0| ≤ 1e-3·|h0|`, `O/oracle_offset_mc.py:137`) | (v0.6, O-6 D-c) **NFR-P2 허용 예외 여섯째**: 값·동작 그대로 이동, 유도식은 백로그. N3.6 삭제 목록에서 뺐다 | (v0.2.4 고침) 값과 동작을 바꾸지 않고 `core/mc_math.py`로 옮기고 '출처 미확인 기존 상수' 표시를 단다. v0.2.3의 `data_rel` 유도 대체안은 기준선 판정 170건을 뒤집어(S-14) 버렸다 |
| `NYQUIST_K_MAX = 10`, `NOISE_TOP_K_MAX = 8`, `INTEGRAL_K_MAX = 4`, `ZOOM_POINTS = 7`, `ZOOM_ROUNDS = 8` | **NFR-P2 허용 예외 다섯**(X-D1 수용 O-3) | 값과 동작을 바꾸지 않고 코어로 옮긴다(N4 동일성). 각 상수에 '출처 미확인 기존 상수' 표시를 단다. 유도는 백로그(§19.4 X-D1) |

* 감사(완료 조건 9 gap 분석 포함)는 위 여섯 밖의 리터럴 판정 상수를 0으로 본다(P NFR-P2). 물리 상수(`_K_B`, `_Q_E`)와 어댑터 보정값(출처 칸 있음)은 판정 상수 목록에 들지 않는다.
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
| `oracle_offset_mc.mismatch_vars`, `build_mc_netlist`, z·1e-6/√m 배율, `"Lfb_" not in text` 검사, `--ngspice` 필수 인자 | 네이티브 MC(`McNative`) + 진단 경로(`McDiagnostic`) + `core/mc_math`. servo 유무는 IR 역할 표로 본다. (v0.2.4) `1e-3` 상수는 삭제하지 않고 `core/mc_math`로 옮긴다(§14, O-6 D-c) | OP-5 |
| (v0.2.4) `oracle_compare.py:379` 메시지 `"ngspice .op 결과 없음: "` | 시뮬레이터 이름·방언 토큰 없는 메시지(예: '시뮬레이터 동작점 결과 없음: '). 어댑터 이름이 필요하면 결과의 어댑터 지문에서 읽는다(토큰 초안 D9 open point) | OP-3(compare 코어 이동) |
| (v0.2.4) `oracle_compare.py:708` 메시지 조각 `' V, ngspice '`와 키 `'ngspice_runs'`, 생산자 `oracle_swing.py:306`, 소비자 `smoke/u6_selfchecks.py:136` | 메시지 '시뮬레이터 실행 {n} 회', 키 `sim_runs`(§11.5 결과 칸 대응). 생산자·소비자를 같은 변경에서 바꾼다 | OP-5(swing 이전) |
| (v0.2.4) 결과 칸 `ngspice_rc`(S-3, `oracle_simulate.py:1284` 등, `oracle_noise.py:151`, `oracle_offset_mc.py:165`) | `RunStatus.rc`(§6) | 그 결과를 내는 모듈의 대체 card(OP-3·OP-4·OP-5) |
| `oracle_compare.py:38`(모듈 docstring)·`:228`(`signed_id` docstring)의 시뮬레이터 이름 | `:228`은 `signed_id`와 함께 어댑터 `read.py`로 간다. `:38` '크기 규칙' 설명은 극성 정규화 규칙(어댑터 공통)으로 다시 쓰고 시뮬레이터 이름은 '사례'로만 남긴다(docstring은 T1-1 검사 밖이지만 P NFR-P1 이름 원칙) | OP-3 |
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
  새 생성기는 LUT 메타에 같은 칸(`bin_rule` 객체, 위와 같은 스키마)을 쓴다(OP-8). 새 메타의 시뮬레이터 칸 이름은 `simulator.name`·`simulator.version`이고 시뮬레이터 이름을 칸 이름에 넣지 않는다(옛 메타 칸 `ngspice`·`ngspice_exe`, S-15, 은 기존 LUT에 그대로 남는다).
* **묶는 LUT 범위**(P G-14, v0.2.4): 선언 하나는 (모델 파일 sha256 집합, 생성 시뮬레이터 이름·판) 한 쌍에 묶이고 LUT 파일 sha256에는 묶이지 않는다(계획 기본 방향). 엔진은 L·W bin 소속을 쓰는 세트(기준 슬라이스, cap, noise, mismatch)마다 그 세트 메타의 `model_files_sha256` 값 집합이 선언 `model_files_sha256` 집합에 포함되고 세트의 생성 시뮬레이터 판이 선언 판과 같을 때만 그 선언을 적용한다. 그래서 같은 모델로 일부 세트만 다시 만들어도 선언이 그대로 맞고, 모델이나 판이 다른 세트에는 적용되지 않아 경계 위 L이 거부된다(`bin_tie_undeclared`, P D-4).
  * 세트의 판 기록 위치(base `1ba9461`에서 다시 잼): 기준 슬라이스는 meta(S-15, 기록 있음), noise 세트는 meta 계약 `E/lut/CONTRACT.md:887`, mismatch 세트는 `:951`('ngspice 버전' 칸). 계획 G-14는 base `d783efe`의 881·945행을 'cap·noise'로 적었고, 그 뒤 CONTRACT가 바뀌어(`be2d6b6`, `b105b65` 등) 행이 옮겨졌다. cap 세트의 판 기록 유무는 OP-7 착수 때 검증자가 잰다. 기록이 없는 세트에는 선언을 적용하지 않는다(fail-closed).
* 엔진 읽기: OP-7 엔진 card가 `E/lut/` 쪽에서 이 파일을 읽는다(엔진 변경, D-4 승인됨(O-1)). 오라클 능력 기록·오라클 코드 지문은 읽지 않는다.
* **측정 상태**: (a) 지금 LUT 기준 슬라이스 meta의 생성 시뮬레이터 판 기록 -- **측정됨**(OP-1 (iii), S-15: 38 슬라이스 모두 `ngspice-46`, 모델 파일 sha256 원본 일치). 그래서 기존 LUT 옆 선언의 판 값은 이 meta 기록을 출처로 적는다. (b) 지금 LUT의 경계 앵커 점에서 시뮬레이터가 고른 bin -- **측정 대기**(OP-7 검증자).

---

## 17. 상위 문서 개정 문안(P N3.7)

* 아래는 **문안**이다. 반영은 상위 계획 개정 절차(독립 검증 → 사용자 승인)를 거친다(S-7). 이 card는 상위 문서를 고치지 않는다.
* (v0.2.4) 상위 계획·design 40·C10 계약 개정은 별도 card `gb-oracle-rev`로 master에 병합됐다(`b105b65`). 이 절은 그 card의 입력 문안 기록으로 남긴다. 그 card는 `O/README.md`(2줄)·`E/lut/CONTRACT.md`(1줄)에도 줄을 더했다(`git show --stat b105b65`). §17.4의 README 3층 재작성과 CONTRACT 4.0.1 규칙 정본 문구는 해당 구현 card(OP-3~OP-7) 몫으로 남는다. 더해진 줄의 내용은 이 card가 대조하지 않았다.
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
| 1 무방언 | `core/test_no_dialect.py` | 토큰 목록 = 검증자(OP-1) | T1-1 `O/core/` 문자열 리터럴(docstring 제외)의 토큰 정규식 적중 0. T1-2 PDK 이름(모든 기술자·엔진 선언 `pdk` 값과 모델 이름 패턴) 0. T1-3 AST import 금지(§3.2) 0. T1-4 `O/core/` 안 비-.py 파일 0. 코어의 파일 열기 경로가 입력·기술자(와 그것이 sha256으로 가리키는 원본)·출력 디렉터리뿐인지는 **실행 중 기록**으로 잰다: 코어 test 전체를 도는 동안 `builtins.open`·`io.open`·`os.open`·`numpy.load`·`pathlib.Path.open`을 감싸 연 경로를 모으고, 모든 경로가 그 test가 넘긴 허용 뿌리(입력 파일, 기술자 파일·원본 뿌리, 출력 tmp 디렉터리) 아래인지 확인한다. 보조로 AST에서 코어 모듈의 열기 호출 인자가 문자열 리터럴 경로가 아님(경로를 코드에 두지 않음)을 본다. T1-0(먼저) 토큰 목록이 기준선 넷리스트와 옛 코드 리터럴에서 적중함을 보인다. (v0.2.4) **D11(난수·식 함수 형태) 연기**: OP-1 사전 점검에서 D11만 기준선 어디서도 적중하지 않았다(S-16). 지금 오라클은 분포 함수를 쓰지 않기 때문이다. 그래서 D11은 OP-5(네이티브 MC 켜는 법 `param_redefine`을 어댑터가 쓰는 card) 병합 뒤에 목록에 넣고, 그때 T1-0 적중 증거는 OP-5 어댑터가 쓴 MC 넷리스트로 보인다. 그 전까지 T1-0은 D11을 뺀 목록으로 돈다(검증자 소유 목록의 단계 표시) |
| 2 stub | `core/test_*_stub.py` | test 작성자 | §3.3 표의 stub 실행 항목 전부, '능력 없음 거부' 항목 전부, D-1 전체 창 경로(G-13 결정된 방식) |
| 3 동일성 | `adapters/ngspice/test_equivalence.py`(검증자 실행) | 기준선 = 검증자(OP-1) | 계획 N4: 이산 칸 정확, 연속 칸 비트 동일 또는 분해능 안(§18.3 식), MC 연속 칸 제외 + §13.2 MC 수학 비트 동일, 입력 변환 = 검증자 스크립트 |
| 4 거부 | `core/test_capability_rejects.py`, `core/test_gates.py` | test 작성자 | PC-1~3·5~8마다 §12.2 깨진 변형 거부(먼저), 기록 없음 → `oracle_capability_unverified`, 지문 하나 바꾼 기록 → `oracle_capability_stale`, 모델 묶음 불일치 → `model_bundle_mismatch`, LUT 기록 빈 표 → `lut_model_provenance_missing`, 진단 결과가 판정 입력으로 → `diagnostic_not_a_gate`. (v0.2.4, O-6 D-a) **분포 값 출처 깨진 변형 셋**: 분포 값을 기술자에 직접 적은 기술자 → `mc_distribution_inline`, 가리킨 원본 sha256이 맞지 않는 기술자 → `pdk_descriptor_stale`, 분포 값 위치가 없거나 0개를 찾는 기술자 → `mc_distribution_unlocated`. 켜는 법 종류가 어댑터 `mc_enable_kinds` 밖이거나 요구가 어댑터 선언을 넘으면 → `mc_method_unsupported`. 같은 확인 코드가 sky130 기술자와 손 모델 기술자 둘에서 돈다 |
| 4a 기하·배수(OP-5) | `adapters/ngspice/test_geometry_multiplier.py` | test 작성자(interface만 보고 씀) | **손 모델 픽스처 정본**(§12.7, OP-5 산출)으로 결정적 어댑터 test. 측정 양 = 회로 출력(같은 바이어스에서 같은 ID 기준 VGS 편차), 모델 파라미터 재독 값으로 판정하지 않는다. 같은 시드에서 (i) 피검 소자의 `n_fingers`만 바꾸면 편차 비 = 손 모델 식이 정하는 비 (ii) 손 모델 식이 전제하는 기하 단위만 다른 둘째 기술자(test 안 파생 변형, §12.7)에서 같은 물리 기하의 편차 비 = 두 식과 단위 환산비가 정하는 비. **표본 정체 보존**: 같은 벤치에 배수를 바꾸지 않는 기준 소자를 두고 두 실행에서 그 값이 같음. **인스턴스 기하 단언**: 모든 실행에서 `OpTable.instance_geometry`(§6)가 IR·기술자 선언대로. **비교 폭**: 편차 Δ = V₁ − V₂의 분해능 δΔ = Σ(reltol·|Vᵢ| + vntol)(§18.3), 비 ρ = Δa/Δb의 폭 |ρ|·(δΔa/|Δa| + δΔb/|Δb|)(새 상수 없음). **거부 먼저**: (a) 배수를 모델 파라미터로 넘기지 않는 변형은 편차 비가 달라 실패 (b) 단위 선언을 무시하는 변형은 회로 출력이 아니라 어댑터가 쓴 넷리스트와 `instance_geometry`로 실패 판정. PDK 공식에 기대값을 걸지 않는다(PC-4와 다름) |
| OP-3 병합 (a) | `core/test_geometry_undeclared.py` | test 작성자 | `geometry_unit` 또는 `parallel_multiplier`가 없는 기술자로 공칭 op·ac·MC 요청을 각각 보내면 실행 전에 `descriptor_geometry_undeclared`로 거부됨(stub 어댑터로 충분, 시뮬레이터 호출 0). `global_directive` 방법인데 `affects` 선언이 없는 어댑터 stub → `geometry_unit_unsupported` |
| OP-3 병합 (b) | `adapters/ngspice/test_equivalence.py`의 공칭 op·ac 부분(검증자 실행) | 검증자 | 첫 조합 선언값(§10.3)으로 쓴 공칭 op·ac 결과가 N4-2로 기준선과 동일. 소자 줄 차이는 N4-3 정규화 대조로 기록만 하고, 차이가 기하 단위·병렬 배수 선언에서 나온 것뿐임을 기록으로 보인다(§10.6) |
| 5 텍스트 단언 이전 | `core/test_no_dialect.py` T5-1 | 검증자 토큰 | `O/tests/core/` 안 방언 토큰 단언 0 |
| 6 삭제 | `test_deleted_names.py` | test 작성자 | §15.1 옛 이름 grep 0(card별로 그 card 몫만) |
| 7 배선 | `test_wiring.py` | test 작성자 | `oracle_run` 경로에서 코어·어댑터·기술자 읽기·자동 대조·MC·온도 게이트·진단 입력이 호출됨(호출 기록 증거) + 검증자 MC 수학 동일성 판정 기록 존재 |
| 8 엔진(D-4 승인 시) | 엔진 쪽 OP-7 test | 엔진 test 작성자 | 9회로 비트 동일, bin 규칙 선언 없음 → 경계 L 거부 |
| 8a 엔진 무변경 | `test_engine_untouched.py`(검증자 git diff) | 검증자 | OP-2~OP-6·OP-8에서 엔진 소스(`E/` 아래 test 밖 파일)·기존 test 파일·`A/sky130_pdk_decl.json` diff 0. **예외**(계획 v0.5.1 8a): `E/tests/` 아래에 엔진 선언·오라클 기술자만 읽는 새 test 파일 추가는 허용(아래 X-13 test 하나) |
| X-13 | `E/tests/core/test_oracle_descriptor_engine_sha.py`(엔진 suite에서 돈다, 계획 v0.5.1 8a 예외) | test 작성자 | (a) 엔진 선언 파일 sha256 ≠ 기술자 `engine_decl.sha256`이면 실패 (b) 엔진 선언 `sources` 파일 집합 ∩ 기술자 `extra_sources` 파일 집합 = ∅(경로와 sha256 둘 다). 엔진 코드를 import하지 않고 JSON만 읽는다 |

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
| B-2 | 옛 진입점 CLI를 `oracle_run` 하위 명령으로 합침(능력 확인 `oracle_run capability` 포함). **결정(O-3, X-D2 수용)** | §3.1 |
| B-3 | 테스트벤치 원소 IR 이름 `tb:<용도>:<대상>` | §4.1 |
| B-4 | 스키마 이름 `oracle_pdk_descriptor/1`, `oracle_capability/1`, `oracle_diagnostic/1`, `lut_bin_rule/1`, 저장 위치 | §10, §12.4, §13, §16 |
| B-5 | `simulator.options` 키 검증은 어댑터 | §11.1 |
| B-6 | LUT 메타·입력 모두 온도·코너가 없으면 `oracle_condition_missing` | §11.2 |
| B-7 | (v0.2.4 철회) 차동 이득 실수 판정 = `data_rel` 유도. 계획 v0.6 O-6 D-c로 `1e-3` 유지(NFR-P2 예외)가 정해져 이 기본안은 없어졌다 | §14 |
| B-8 | 계획이 다루지 않은 반복 상한 상수 다섯은 그대로 옮기고 표시만. **결정(O-3, X-D1 수용, 계획 NFR-P2 허용 예외 목록)** | §14 |
| B-9 | X-13 test를 엔진 suite 쪽(`E/tests/` 아래 읽기 전용 test)에 둠. **계획 v0.5.1 완료 조건 8a 예외에 따름** | §18.1 |
| B-10 | 식이 없는 연속 칸은 비트 동일만 | §18.3 |
| B-11 | (v0.2.4) 네이티브 MC 표본 실행 방법(시드, 실행당 표본 수, 정체 보존, 소자별 독립)은 어댑터가 켜는 법 종류마다 선언하고(P N3.3), 기술자는 요구(`requires`)만 적는다. 코어가 요구 ⊆ 능력을 확인한다. 계획 N3.4 MC 행의 '표본 실행 방법'은 이 요구 칸과 어댑터 선언의 짝으로 담는다 | §8.3, §10.4 |
| B-12 | (v0.2.4) 새 스키마 `process`는 정의 밖 키를 거부(`additionalProperties: false`) | §11.1 |
| B-13 | (v0.2.4) `legacy_adapter` finger 분할 기준 폭은 dump `lut_meta.W_ref_m`만, 없으면 막힘 | §11.4 |
| B-14 | (v0.2.4) 손 모델 픽스처 위치·이름 `O/tests/fixtures/hand_model/hand_model.oracle_descriptor.json` | §3.1, §12.7 |
| B-15 | (v0.2.4) 오류 코드 `descriptor_geometry_undeclared`, `geometry_unit_unsupported`, `mc_distribution_inline`, `mc_distribution_unlocated`의 이름과, 분포 값 원본 sha256 불일치를 `pdk_descriptor_stale`로 내는 것 | §7 |
| B-16 | (v0.2.4) 기하 단위 적용 방법 이름 `global_directive`·`instance_numbers`, 전역 지시 영향 칸 선언 `global_geometry_directive.affects`·`power` | §8.3, §10.6 |
| B-17 | (v0.2.4) 결과 칸 이름 `ngspice_rc` → `RunStatus.rc`, `ngspice_runs` → `sim_runs`, compare 메시지 일반화 문구 | §6, §11.5, §15.1 |

### 19.2 계획과 다른 결정이 필요한 곳(S-7: 멈추고 보고)

**v0.2 상태**: DV-1·DV-2는 사용자 결정 O-3(2026-10-16 "모두 권고대로")으로 닫혔다. DV-1은 (가)로 정해져 계획 v0.5 N3.4에 반영됐고(`oport-plan-r1`), DV-2 상위 문서 개정은 별도 card다(`gb-oracle-rev`). v0.2에서 새로 생긴 멈춤 항목은 없다. 아래 표는 기록으로 남긴다.

| ID | 내용 | 필요한 결정 |
|---|---|---|
| **DV-1** | 오라클이 include해야 하는 모델 파일 가운데 엔진 선언 `sources`에 없는 것이 있다(사례 pmos `lod.spice`, S-7). 계획 N3.4 '원본 파일 경로·sha256 정본은 엔진 선언 하나'와 D-9 '엔진 선언 무변경'을 함께 지킬 수 없다 | (가) 기술자 `extra_sources`에 엔진 선언에 없는 파일만 두고 중복은 금지(§10.1 임시안, '파일마다 정본 한 곳'으로 원칙을 고침) (나) 엔진 선언에 그 파일을 더하는 엔진 card(D-9 예외, 엔진 지문·9회로 기준선 재측정) -- 계획 개정 필요 |
| **DV-2** | 상위 문서 개정(P N3.7)이 아직 반영되지 않았다. 계획 N5.1의 공통 착수 조건이라 구현 card(OP-2~)는 상위 계획 개정 승인 뒤에만 시작할 수 있다. 이 문서는 §17에 문안만 냈다 | 상위 계획 개정 절차를 언제 누가 할지(계획과 다른 결정은 아니고 순서 확인이다). (v0.2.4) `gb-oracle-rev`가 master에 병합됨(`b105b65`, §1.3) |

**v0.2.4 새 멈춤 항목**(이 문서는 아래를 정하지 않았다. 계획 개정 또는 사용자 결정이 먼저다):

| ID | 내용 | 필요한 결정 |
|---|---|---|
| **DV-3** | 계획 N3.5 '결정적 섭동 = 진단 도구' (ii)와 N4-2 MC 칸은 '기준선 MC 표본을 같은 시드·같은 RNG로 재현해 진단 경로로 넣고, 표본별 V_os·σ_in이 기준선과 **비트 동일**'을 요구한다. 그런데 같은 계획 v0.6 D-b(OP-3 병합 조건 (b), v0.6.2 B-3)는 기하 단위·병렬 배수 선언 때문에 소자 줄이 기준선과 달라질 수 있음을 인정하고 공칭 결과를 'N4-2 동일'(비트 동일이 목표, 아니면 분해능 안 + 차 기록)로 판정한다. 진단 경로도 같은 소자 줄 작성기(§10.6)를 지나므로, 같은 물리 표본이라도 시뮬레이터 출력이 마지막 자리에서 다를 수 있고 그러면 V_os·σ_in의 비트 동일이 깨진다. 옛 넷리스트 형식으로 재현하면 옛 코드를 남겨야 해서 P N3.6('진단 도구는 새로 쓰고 옛 코드를 옮기지 않는다')과 맞지 않는다. OP-1 재현(S-22)은 옛 넷리스트 안에서만 비트 동일을 보였다 | (가) **권고**: 둘로 나눈다. (가-1) 코어 MC 수학 비트 동일 = 기준선 로그의 표본별 op 값을 새 `core/mc_math`에 그대로 넣어 V_os·σ_in·mean_in이 비트 동일(S-22 두 번째 방식, 시뮬레이터 없음) (가-2) 진단 경로 끝까지 재현 = 비트 동일이 목표, 다르면 N4-2 분해능(§13.4 `dc_resolution_in_V`) 안이고 차를 기록, 넘으면 실패. 계획 N3.5 (ii)·N4-2 MC 문구 개정이 필요하다 (나) 지금 문구 그대로 끝까지 비트 동일을 요구하고, 깨지면 그때 멈추고 보고 -- 맞는 구현이 막힐 수 있다(v0.6.2 B-3과 같은 종류) |

**알림**(계획과 다른 결정은 아니고, 다른 문서 소유자에게 넘길 것):
* 계획 N3.5.1의 기준 문구('offset-trim v0.5.2 `a293411` 455-462행')는 master v0.5.6 `86e5adc` 466-473행으로 다시 대조됐고 내용 차이가 없다(§12.8). 계획 문구 갱신은 계획 소유다.
* offset-trim 계획 N3.9 '순서 의존'(master 477행)이 oracle-portability 계획을 '초안, 승인 전'으로 적는다. offset-trim 소유 문구다.
* 상위 문서 개정 병합본(`b105b65`)과 §17 문안의 일치는 이 card가 대조하지 않았다.

### 19.3 측정 대기 칸(OP-1·OP-7, 하나를 고르지 않음)

| 칸 | 측정 | 상태(v0.2.4) | 절 |
|---|---|---|---|
| D-1 능력 없는 어댑터의 기본 실행 방식(G-13) | OP-1 기준선 창당 시간 | **측정됨**(S-19). 확정은 OP-4 | §8.4 |
| sky130·ngspice 네이티브 MC 켜는 법·소자별 독립 여부, 직접 루프를 쓴 이유 | OP-1 (i) | **측정됨**(S-12·S-13): `param_redefine`으로 소자별 독립('전역 파라미터가 모든 인스턴스에 같은 값' 가설은 아님). 직접 루프를 고른 경위 자체는 재지 않았고, 옛 코드 주석(`O/oracle_offset_mc.py:22-24`)은 그 배율이 기하 단위·배수 차이를 덮는다고 적는다(S-13, O-6 D-b) | §10.3, §10.4, §10.6 |
| 지금 LUT 슬라이스 meta의 `model_files_sha256` 존재 | OP-1 (ii) | **측정됨**(S-15): 38/38 있음 | §12.5 |
| 지금 LUT 슬라이스 meta의 생성 시뮬레이터 판 존재 | OP-1 (iii) | **측정됨**(S-15): 38/38 `ngspice-46` | §16 |
| 지금 LUT 경계 앵커 점에서 시뮬레이터가 고른 bin | OP-7 검증자 | 대기 | §16 |
| cap·mismatch 세트 메타의 생성 시뮬레이터 판 기록 | OP-7 검증자 | 대기(v0.2.4 추가) | §16 |
| PC-3 표본 수 기본값의 실행 비용 | OP-1 | **측정됨**(S-12 13행): 소자 쌍 벤치 표본당 0.152 s, 200 표본 30.3 s(r = 0.05면 201 표본) | §12.3 |
| 차동 이득 실수 판정 변경이 기준선 `status`를 바꾸는 사례 | OP-1 | **측정됨**(S-14): 바꾸면 170건. D-c로 바꾸지 않음 | §13.2, §14 |
| ngspice 오류 로그 → 오류 코드 대응표 | OP-1 기준선 로그 | **초안**(§7.1, S-18). 확정은 OP-3·OP-4 | §7 |
| ngspice 매뉴얼 원문 보관과 기본 허용오차 쪽 번호 | 원문 보관 문서 작업(X-D4 수용 O-4). **OP-2 병합 조건**(v0.2.2) | 대기. 전역 기하 지시 `affects`의 출처(§8.3)도 같은 원문에서 채운다 | §8.3, §14 |
| 기준선 입력 가운데 DC 풀이 허용오차 선언이 없는 것(X-D4) | OP-1 | **측정됨**(S-20): test 입력 1개(reltol 없음) | §8.3 |
| dump `lut_meta.W_ref_m`이 없는 기준선 생산 dump | OP-2 착수 검증자 | 대기(v0.2.4 추가) | §11.4 |
| 기준선 C10 과도 가운데 (가) 방식에서 시간 상한에 걸릴 사례 | OP-4 착수 검증자 | 대기(v0.2.4 추가) | §8.4 |

### 19.4 원래 취지와 다름(따로 보고)

| ID | 내용 |
|---|---|
| X-D1 | (**수용(O-3)**, v0.6 O-6 D-c로 하나 더함) '출처 미확인 기존 상수' 여섯(옛 반복 상한 다섯 + 차동 이득 실수 판정 `1e-3`)을 출처 확인 없이 그대로 옮긴다(B-8, §14). '상수 발명 금지' 원칙에서 보면 기존 위반을 이 기능이 정리하지 않고 넘기는 것이다. 정리하면 N4 동일성이 깨질 수 있어서다(`1e-3`은 실측 170건, S-14). 유도는 백로그 |
| X-D2 | 옛 진입점 여섯을 `oracle_run` 하위 명령으로 합친다(B-2). README의 '파일마다 독립 진입점 1개' 원칙(`O/README.md` '파일' 절)과 다르다 |
| X-D3 | (v0.2에서 해소) PC-10은 offset-trim design TR-0T가 G-15를 닫아(선언 기준을 온도 무관하게 그대로) 정의했다(§12.2). 그 design은 master에 병합됐다(T-40) |
| X-D4 | (v0.2, **수용(O-4)**. 할 일: ngspice 매뉴얼 원문 보관과 기본 허용오차 쪽 번호 채우기 = 원문 보관 문서 작업이고 **OP-2 병합 조건**(v0.2.2), 영향받는 기준선 입력 측정 = OP-1) T-39에 따라 DC 풀이 허용오차를 선언 없이 쓰지 않게 했다. 그래서 지금 기본 허용오차(`_NGSPICE_DEFAULT_TOL`)의 출처(매뉴얼 쪽)가 채워지기 전에는, 입력에 허용오차 선언이 없는 기존 오라클 입력이 `dc_tolerance_undeclared`로 멈춘다. 지금 smoke 입력은 `testbench.options`에 reltol·vntol·abstol을 가진다(S-6 사례). 영향받는 기준선 입력은 OP-1에서 test 입력 하나로 쟀다(S-20) |
| X-18 | (계획 X-18, **수용(O-6)**) 네이티브 MC가 '켜기만'이 아니라, 첫 조합에서는 '불일치 변수를 시뮬레이터 분포 함수로 다시 선언'(`param_redefine`)이다(S-12). 겉모양은 O-1이 지운 직접 덮어쓰기와 비슷하지만 값은 시뮬레이터 RNG가 소자마다 뽑고 분포 값은 PDK 원본 선언에서만 온다(§10.4). 이 문서는 계획 정의를 그대로 옮겼다 |

---

## 20. card별 범위 재확인(계획 N5.1 대 이 문서)

| card | 이 문서 절 | 선행(계획) | 추가 선행(이 문서) |
|---|---|---|---|
| OP-1 | §19.3 측정 전부, §18.1 T1-0 토큰 목록, §13.2 절차 준비, N4 입력 변환 스크립트(§11.5 대응표) | 계획 승인 | -- (v0.2.4: 측정 대부분 끝남, §19.3 상태 칸) |
| OP-2 | §10.1, §10.2·§10.3 가운데 `mc`·`diagnostic` 칸을 **뺀** 기술자 전부(기하 단위·병렬 배수 선언 칸 포함, P G-5), §11(§11.5 포함) | OP-0, OP-1 | (충족, `b105b65`) 상위 문서 개정 card `gb-oracle-rev` 병합. **병합 조건**: ngspice 매뉴얼 원문 보관과 기본 허용오차 쪽 번호(R6) 채움(X-D4) |
| OP-3 | §3, §4, §5, §6(`instance_geometry` 포함), §7(§7.1 op·ac 몫), §8.1~8.3, §9, §10.6(소자 줄 작성·미선언 거부), §12.5, §15.1 OP-3 행 | OP-2 | **병합 조건**(P OP-3): (a) 기하 규칙 미선언 기술자의 실제 거부 test (b) 첫 조합 선언값의 공칭 op·ac 결과 N4-2 기준선 동일(검증자), 소자 줄 차이는 기록만·선언 기인 한정(§18.1 'OP-3 병합' 두 행) |
| OP-4 | §8.4(G-13 확정), §8.5, §7.1 pz·과도 몫, §14 반복 상한 다섯, §15.1 OP-4 행 | OP-3 | G-13 측정(S-19 있음) + (가) 시간 상한 사례 수(§19.3) |
| OP-5 | §10.4·§10.5와 기술자 파일의 `mc`·`diagnostic` 칸(sky130 값, 사용자 확인), §12.7 손 모델 픽스처 정본(만듦), §13, §14 `1e-3`, §15.1 OP-5 행, §18.1 4a | OP-4 | (충족) OP-1 (i) 결과 = 소자별 독립(S-12). §19.2 DV-3 결정(§13.2 MC 수학 동일성 판정 방식) |
| OP-6 | §12(§12.7은 OP-5 산출물 재사용, 새로 만들지 않음) | OP-5 | (충족, T-40) offset-trim design TR-0T가 master에 병합됨. PC-10 기준의 대조 정본 = master `offset-trim.design.md` §20 |
| OP-7 | §16 | OP-3, XRUN-F1 C | (충족) OP-1 (iii) = S-15. 경계 재측정, cap·mismatch 세트 판 기록 확인 |
| OP-8 | §15.3, §16 | OP-6 | -- |
| OP-9 | §18 전부 | -- | -- |

* (v0.2.4, 검증자 정리) v0.2.3에서는 OP-2가 '§10'(전체), OP-5가 '§10.4·§10.5'를 함께 가져 §10.4가 겹쳤다. 위 표는 칸 단위로 나눴다: 기술자 파일 하나를 OP-2가 만들고(`mc`·`diagnostic` 칸 없음), OP-5가 같은 파일에 그 두 칸을 더한다. 계획 N5.1(OP-2 = 기술자·기하 규칙, OP-5 = 네이티브 MC·진단)과 같다.
