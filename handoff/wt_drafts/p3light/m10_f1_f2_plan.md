# M10·F1·F2 가벼운 절차 준비 (2026-10-07, 읽기 전용 실측)

근거 판: gmid-light `phase3-light` **`cb0ef86`**(6df4bd7 + B26-1 test `90eedb2`·code `cb0ef86`). 메인 저장소·gmid-light는 읽기만 했다(`git clone --no-hardlinks`로 `C:/g454` 아래 복제 -- 원본 쓰기 0, 끝에 `C:/g454` 삭제).
방법(전부 측정 전용, 산출물 아님):
* **M1~M9 모의**: 복제본 `C:/g454/m`에 `_drafts/p3kit_m2_m9/fu_standin.py`(FU 대역: DR·ACF에 `from __future__ import annotations` -- 없으면 `move.py MOD2`가 `import_conflicts(card)` `__future__`로 멈춤, 실측) → `p3light/tools/move.py MOD1 … MOD9 --commit` 8회 모두 성공(단위 8·20·82·104·21·11·30·16).
* **F2(F1 없이) 모의**: M9 모의 위에 `_drafts/p3kit_f12/mk_f2.py --acf`(G1 `SourceIndex`는 `p3light/tools/g1_core.py` 주입) → SR·TL·DR 삭제, SD 재수출 50이름·ACF 2이름 삭제.
* **PT3**(`tools/gates/pytest_gate.ini`, `--gmid-phase=3`, F2는 `--continue-on-collection-errors`): base `cb0ef86` **1179 passed·15 xfailed**(323 s) / M9 모의 **4 failed·1175 passed·15 xfailed** / F2(F1 없음) **122 failed·678 passed·12 xfailed·27 errors**(수집 오류 14파일).
* **호출부 전수 스캔**: 추적 `.py` 전부를 AST로(엔진 split 5파일 자신 제외) -- `from X import`, `import X [as a]` + 별칭 속성·`getattr`류 상수 이름, `import_module("X")`, 모듈 속성 대입(D-17), 문자열 앵커·실행 문자열. 목적지 = `p3light/tools/mp_core.compute_plan`(design 30 §6.2 규칙 A-0~A-7 + D-19 PIN) 배정, 그리고 **M9 모의 트리에서 G1 `binding_origin`으로 다시 푼 정의 파일과 엔진 이름 전부 일치**(다른 것은 엔진 밖 이름 12·정의 없는 이름 2뿐 -- 아래 F1-J).

---

## 1. M10 -- 유일 진입점 `gmid_design_pipeline.run_gmid_design_pipeline`

### 1.1 지금 그 역할을 하는 것(호출 경로)
* 운영 진입은 **CLI 하나**: `python workspaces/run_harness.py <circuit_key>` → `run(circuit_key)`(H 422~529행; `try:` 444, 몸체 445~511, `except Exception as e:` 512~529, 안쪽 감사 `try` 471, 진단 `try` 526).
  `run()` = 키 검사 → `cfg = SPECS[key]` → `topo`·`report_dir`·`stem`·`instance_out`·`report_out` → `spec = cfg["spec_fn"]()` → `setdefault` 2줄(`floorplan_target` = 하네스 상수 1.5/0.5, `max_layout_retry_rounds` = 6)
  → `optimize_full_circuit_budget(topo, spec, grid_points_per_theta=…, search_method=cfg.get("search_method","grid"), slsqp_kwargs=cfg.get("slsqp_kwargs"))`
  → floorplan 판정 print → `run_full_circuit_audit_from_topology(topo)` → `save_instance_json` → `assemble_report_data` → `save_html_report`; 예외는 전부 삼키고 print(+`ValueError`면 `diagnose_sizing_roles_gap`).
* `run()`을 **코드로 부르는 추적 파일은 0**(grep `run_harness.run(`·`H.run(` 0). `import run_harness`는 23파일(probe 21·`unit/_library_sized_contexts.py`·`contracts/test_b26_rail_accessor.py`·`test_restore_plan_functions.py`·`tests/tools/derive_achievable_bounds.py`)인데 전부 `canonical_spec`·`SPECS`·`derived_spec`만 읽는다 -- M10이 그 이름을 바꾸지 않으므로 영향 0.
  `run()`을 실제로 실행하는 것은 E-INST 스크립트(`docs/03-analysis/…30-module-split/scripts/e_inst_p3.py` -- 하네스 소스를 exec 후 `mod.run(circuit)`)뿐이다 -- M10 뒤에도 `run()`이 남으므로 그대로 돈다.
* `optimize_full_circuit_budget`는 엔진 쪽 '사실상 진입점'(R2 비고: "3단계 분리 없음, θ* print만, except Exception으로 실패도 exit 0"). 계획 N3.10 MOD10 행·`00-common` §10.1·design 30 §2.3·`gate_config.json` `after_phase3` 첫 원소가 `gmid_design_pipeline.py::run_gmid_design_pipeline`.

### 1.2 최소 구현안(얇은 래퍼 = `try` 몸체 추출) -- `draft_p3_m10.spec.md` '의도'·계약 2~5에서 코드 변경만
* 새 파일 `A/gmid_design_pipeline.py`: 최상위 = import 문 + `def run_gmid_design_pipeline(spec, *, topology_path, search, output_dir)` 하나(모듈 docstring·대입·`__main__` 없음). 반환 `None`. `instrument`·`activations_out`은 Phase 4(CC-7·CC-8) -- 지금 넣지 않는다.
* 본문 = H 445~511행(`try` 몸체)을 **문장 순서 그대로**: 바뀌는 곳은 (i) `topo` → `topology_path`, (ii) `cfg["grid_points_per_theta"]`·`cfg.get("search_method","grid")`·`cfg.get("slsqp_kwargs")` → `search["grid_points_per_theta"]`·`search["search_method"]`·`search["slsqp_kwargs"]`,
  (iii) `instance_out`·`report_out`을 `output_dir`과 `os.path.basename(topology_path).removesuffix(".topology.json")`에서 만드는 대입 2줄(지금 `stem`은 `cfg["topology_file"]`에서 -- 같은 값), (iv) floorplan 임계값 = `spec["floorplan_target"]["max_aspect_ratio"]`·`["min_packing_density"]`(하네스 상수를 엔진에 다시 적지 않는다 -- `run()`의 `setdefault`가 이미 같은 값을 넣고 SR `optimize_full_circuit_budget`도 그 키를 읽음).
  `print`는 그대로 둔다. **`except Exception` 처리부는 옮기지 않는다** -- 진입점은 예외를 올린다(처리부를 옮기면 V6 `broad_except` 새 발견 2·진입점이 예외를 삼킴 -- 초안 실측; 가벼운 절차에서도 '실패를 삼키는 결함을 새 엔진 파일로 복제하지 않는다'는 이유는 남는다).
* import(정의 모듈에서 직접 -- M9 모의 `binding_origin` 실측): `import os`; `from sizing_layout_convergence import optimize_full_circuit_budget`(MOD8); `from instance_report_builder import save_instance_json, run_full_circuit_audit_from_topology, assemble_report_data, save_html_report`(MOD9). split 파일·`run_harness`·`workspaces` import 0.
* 하네스 `run()`: `stem`·`instance_out`·`report_out` 3대입 삭제, `try:` 몸체를 `run_gmid_design_pipeline(spec, topology_path=topo, output_dir=report_dir, search={"grid_points_per_theta": cfg["grid_points_per_theta"], "search_method": cfg.get("search_method", "grid"), "slsqp_kwargs": cfg.get("slsqp_kwargs")})` 한 줄로, 처리부(512~529)는 바이트 그대로.
  H import: 진입점 import 추가, 더 안 쓰는 `optimize_full_circuit_budget`·`save_instance_json`·`run_full_circuit_audit_from_topology`·`assemble_report_data`·`save_html_report` 삭제, `SemiEmpiricalGmIdLUT`·`dense_candidates`·`layout_grid_L_candidates`·`diagnose_sizing_roles_gap`는 남는다(SPECS·처리부가 씀 -- 그 import 출처 변경은 F1 몫).
* 레지스트리(WP-14 같은 커밋): §4 R1 `### 기타 모듈 (16)`에 `run_gmid_design_pipeline` 행 추가(괄호 16→17, §1 집계 '기타 모듈' R1 16→17), §5 R2 `run` 행은 남기고 비고만 '준비·실패 출력·진단, except는 Phase 4 DF-37'. (레지스트리 '이관 목적지' 열은 D0b 재생성을 버린 판이라 plan과 80단위 다르다 -- 아래 2.1. M10 행은 `gmid_design_pipeline`.)
* 순서 의존: MOD10이 MOD8·MOD9를 import하므로 **M9 뒤**. F1의 `run_harness.py` 수정은 M10 뒤 하네스 import 모양 위에서 한다.

### 1.3 필요한 test(작성자 ≠ code 작성자) -- 기대값 출처
가벼운 절차 4(매 변경 뒤 E-INST·E-LIB base 같음)가 **실제 회로 동작 보존**(파일럿·`folded_cascode` instance.json 해시)을 이미 판정하므로, 새 test는 E-INST가 보지 않는 것만 둔다(실제 회로 실행 test는 두지 않는다 -- `folded_cascode` 한 판 약 50 s, 중복).
| test | 단언 | 기대값 출처(독립) |
|---|---|---|
| T-M10-1 배선 | SPECS 키 4개마다 `run_harness.run(key)`가 `run_harness.run_gmid_design_pipeline`을 **정확히 1회**, 위치 `spec` + `topology_path=<LIBRARY_DIR/topology_file>`·`output_dir=<WORKSPACES_DIR/report_dir>`·`search={3키}`로 부른다(모듈 속성 교체로 기록, 계산 없음) | 구성(oracle a): `SPECS[key]`·하네스 상수에서 기대 인자를 test가 직접 만든다 |
| T-M10-2 예외 전파 | 진입점 모듈의 `optimize_full_circuit_budget`을 `RuntimeError` 내는 대역으로 바꾸면 `run_gmid_design_pipeline(...)`이 그 예외를 올린다(`pytest.raises`) | 구성 |
| T-M10-3 임계값 출처 | `spec["floorplan_target"]`을 하네스 상수와 **다른** 값(예 2.0·0.3)으로, 합성 `pr`(aspect 1.8·density 0.25)로 부르면 floorplan 줄이 `(<= 2.0 ? True)`·`(>= 0.3 ? False)` | 구성(넣은 spec 값이 기대를 정함) -- 숫자 상수를 MOD10에 다시 적으면 FAIL(초안 R-5 실측) |
| T-M10-4 분기 출력 | 진입점 모듈 속성 5개(`optimize_full_circuit_budget`·`run_full_circuit_audit_from_topology`·`save_instance_json`·`assemble_report_data`·`save_html_report`)와 하네스 `diagnose_sizing_roles_gap`을 합성 반환·예외로 바꾸고 `run_harness.run("folded_cascode")`(`WORKSPACES_DIR`는 tmp, `report_dir`는 **미리 만듦**)의 stdout·호출 인자(경로는 `<OUT>`·`<ROOT>`로 정규화)가 기록과 같다. 최소 시나리오 10(초안 계약 6 (b): `pr is None`+감사 ValueError / 재시도 줄 2+감사 성공+report / audit·floorplan·감사 FAIL note 셋 / density만 / aspect만 / 경계 등호 / `pr` 있음+감사 ValueError / 최적화 ValueError→진단 / 진단 자체 실패 / RuntimeError 진단 없음) | **base 기록**(oracle c): M10 전 트리 **사본**(작성자 worktree 밖 임시 경로)에서 같은 모듈 속성 교체로 하네스를 돌린 stdout·인자를 `.py` 리터럴 모듈로 둔다(base에서는 교체 대상이 `run_harness` 모듈 속성 -- 피검 새 코드를 부르지 않는 기록) |
| T-M10-5 모양 | 시그니처(`spec` 위치·키워드 + 키워드 전용 `topology_path`·`search`·`output_dir`, 기본값·`*args`·`**kwargs` 없음), 새 프로세스에서 `import gmid_design_pipeline` 뒤 `sys.modules`에 `run_harness`·`workspaces/` 아래 모듈 0 | 문서(00-common §10.1 431행 + design 30 §2.3 D-5) |
* 함정(초안 실측, 그대로 유효): (1) tmp `WORKSPACES_DIR` 아래 `SPECS[key]["report_dir"]`를 **base 기록과 test 양쪽에서 미리 만든다** -- 안 만들면 `folded_cascode`가 `[FAIL] FileNotFoundError …instance.json`으로 끝나 'None = None' 무발동 통과. (2) 실제 회로 해시를 쓸 경우 E-INST `h()`와 같은 식(`separators=(",", ":")` 포함) -- 빼면 다른 값. (3) 기록은 `.json`이 아니라 `.py` 리터럴(gate를 버렸어도 diff 검토가 쉬움 -- 선택). (4) 기록을 추적 파일 `workspaces/folded-cascode-report/folded_cascode.instance.json` 위에서 만들지 않는다.
* 위치: `A/tests/integration/`(계획 N3.11 end-to-end). base에서 수집 `ModuleNotFoundError: gmid_design_pipeline`(자연 red), 병합본 green.
* 변경 뒤 공통 확인(가벼운 절차 4): 전체 pytest(새 test id만 증가, 기존 결과 같음) + E-INST(파일럿·`folded_cascode`: `engine_origin` 밖 키 같음, stdout `elapsed` 가린 뒤 같음) + E-LIB `hash` 같음. 이동이 아니라 추출이라 절차 3(ast 해시 무변경)은 MOD10에 해당 없음 -- 대신 진입점 본문 문장열 = base `try` 몸체 문장열(위 (i)~(iv) 치환 밖 같음)을 검토자가 AST로 확인(초안 계약 4: `print` 16·`if` 6·`for` 2·안쪽 `try` 1).

### 1.4 초안에서 버린 것
V3 변이·인벤토리(M10-6 비용)·V4 두 번 실행·V5 `.json` 승인·판정 기록·`interface_card.py`·거부 입력 R-1~R-14 판정기 자기 점검·`move_plan check` ORDER/LAYER 계약·IMPORT-ANY 수 대조·spec card id/날짜. (R-1·R-2·R-8·R-10의 '모양' 조건은 검토 체크리스트로만 남김: MOD10이 `run_harness`·split 파일을 import하지 않음, 처리부 미이동, 모듈 docstring 없음.)

---

## 2. F1 -- 호출부를 정의 모듈로

### 2.1 목적지의 근거
* 이름별 목적지 = **실제 M 병합본의 정의 파일**(G1 `binding_origin`). M9 모의에서 잰 값이 `move.py` plan 배정(design 30 §6.2 A-0~A-7 + D-19 PIN `rail_declaration`·`RailDeclaration` → MOD2)과 엔진 이름 전부 일치했다.
  배정 분포: SR 217이름(MOD4 97·MOD3 43·MOD8 30·MOD5 21·MOD6 11·MOD1 8·MOD2 7), SD 170(SD 잔류 111·MOD3 39·MOD2 12·MOD9 8), TL 7(MOD4), DR 6(MOD9), ACF 4(MOD9 2·MOD2 1·ACF 1). plan `upward`·`cycles`·`unassigned`·`conflicts`·`import_time_high` 0.
* **레지스트리 '이관 목적지' 열은 낡았다**: plan 대비 `reg_mismatch` **80단위**(예 `GmIdLUT` 등 18: 레지스트리 `gmid_sizing_engine` → plan `gmid_lut`(A-1); 17: `gmid_sizing_engine` → `circuit_metrics`; 15: `topology_authoring` → `circuit_state_graph`; 10: `circuit_state_graph` → `gmid_sizing_engine`; 7: `theta_search` → `sizing_layout_convergence` …). D0b(열 재생성)를 버렸으므로 **F1 목적지는 레지스트리 열이 아니라 M 병합본 트리에서 푼다**(정의 하나). 레지스트리 열 갱신은 별도 문서 작업(이 계획의 범위 밖 -- 그대로 두면 다음 grep이 틀린 목적지를 가리킨다는 점만 기록).
* F1 착수 때 할 일: 실제 M9(·M10) 병합본에서 이 스캔을 다시 돌려(측정 스크립트 `scan.py`·`classify.py` 형식 -- 판정 도구 아님) 목록을 확정한다. 모의 배정과 실제 배정이 다르면 실제가 이긴다.

### 2.2 규모(cb0ef86 판, D-9 밖)
* 엔진 split 모듈(SR·TL·DR·SD·ACF)을 읽는 추적 `.py` **92파일** → 바꿀 것 **78**(기계적만 55 + 판단 포함 23), 바꿀 것 없음 14(SD 잔류 이름만 읽음). D-9 제외(`.ai/verification/**`·`probe_stage_partition.py`) 15파일은 고치지 않는다(F2 뒤 깨짐 기록만).
* 디렉터리별(바꿀 78): `tests/probes` 32 · `workspaces/current-reuse-telescopic-ota-report` 15 · `tests/contracts` 12 · `tests/unit` 10 · `workspaces/two-stage-ota-report` 4 · `tests/`(루트) 2 · `tests/tools` 2 · `workspaces/run_harness.py` 1.
* 레코드 종류(D-9 밖): `from X import` 57, `import X [as a]` 52(별칭 속성 읽기 213자리), D-17 대입 15, `import_module("X")` 10, 동적 import 1, 동적 `getattr` 1.
* SD에 F2 뒤에도 바인딩이 남는 이름(SD가 스스로 읽어 재수출 유지) **9**: `RailDeclaration`·`Transistor`·`_scan_case_collisions`·`find_hub_merge_candidates`·`find_matching_candidates`·`find_stack_edges`·`find_stacked_matching_candidates`·`kcl_series_union`·`load_topology`(초안 8 + B26-1 `RailDeclaration`). 이 이름을 `stick_diagram`에서 읽는 줄은 F1이 바꾸지 않는다(초안 규칙 -- 정의는 MOD3/MOD2지만 SD 재수출이 남으므로 import 경로 하나). 반대로 **`rail_declaration`은 F2에서 SD 재수출이 지워진다**(SD가 읽지 않음, 모의 실측) -- 읽는 곳은 F1 대상.

### 2.3 기계적으로 바꿀 수 있는 것(규칙 = `draft_p3_f1.spec.md` 계약 2 (i)(ii)(v)(vii)의 코드 변경 부분, `f12_f1sim.py` 규칙 (1)~(6))
* **M1 `from X import a, b`** (X = SR·TL·DR, 또는 SD에서 F2 삭제 이름): 이름마다 정의 모듈로 묶어 `from <정의 모듈> import a [as …]` 줄로 나눈다. SD 잔류 이름은 `from stick_diagram import …`에 남긴다. 줄 끝 주석·들여쓰기 유지.
* **M2 `import X as a` + 속성 읽기가 한 목적지**: import 줄만 `import <정의 모듈> as a`.
* **M3 `import X as a` + 여러 목적지**(37 레코드, probe 대부분): 원래 import 바로 뒤에 `import <정의 모듈> as _f1_<모듈>`을 더하고 `a.<이름>` 자리를 `_f1_<모듈>.<이름>`으로(`<모듈>.<이름>(…)` 속성 호출 모양은 유지 -- B34 test 등). SD 잔류 이름의 `a.X`는 그대로.
* **M4 엔진 밖 이름을 shim 경유로 읽는 줄**(unit selftest 4파일 :24 -- `np`·`json`·`math`·`_dc_replace`(SR), `math`(TL), `os`(DR), `Counter`·`defaultdict`·`json`·`os`·`_dc_asdict`·`_dc_replace`(SD), workspaces probe 3파일의 `from stick_diagram import … replace as _dc_replace`): 원 출처 import로(`import numpy as np`, `from dataclasses import replace as _dc_replace` …). G1 `binding_origin` = `ext`/`ext-module`로 기계 판별. (M9 모의에서는 `move.py`가 shim에 일반 import를 남겨 아직 깨지지 않는다 -- **F2에서 깨진다**: 실측 수집 오류.)
* 도구 후보: `_drafts/p3kit_f12/f12_f1sim.py`(규칙 (1)~(6) 기계 재작성, 실행 문자열 포함)가 그대로 쓰는 `reachability.SourceIndex`를 `p3light/tools/g1_core.py` 주입으로 받으면 재사용 가능(만들면 배선: F1 code/test 작성자에게 건네는 것이 아니라 오케스트레이터가 쓰는 '변경 생성기'로 쓰거나, 안 쓸 거면 손으로). 단 `_import("sizing_recipe")` 같은 반복 자리는 첫 곳만 바꾼 전례(r1 손 보정 4곳)가 있어 결과를 AST로 다시 확인.

### 2.4 판단이 필요한 것(F1-J, 23파일)
| # | 자리(cb0ef86) | 무엇 | 기본안(초안 원칙에서) |
|---|---|---|---|
| J1 | D-17 모듈 속성 덮어쓰기 15자리·10파일: `probes/probe_b22_headroom_attribution.py:104·116`·`probe_diode_gmid_readiness.py:63`·`probe_diode_pass_skips.py:94`·`probe_diode_window_corner.py:100·108`·`probe_matching_pair_divergence.py:124`·`probe_vds_assignment_paths.py:47·53·62·73·79`, `workspaces/current-reuse…/diagnose_cmrr_cmfb.py:24`·`diagnose_cmrr_psrr.py:20`, `contracts/test_b26_rail_accessor.py:334`(`monkeypatch.setattr(stick_diagram, "rail_declaration", …)`) | 이동 뒤 호출자는 자기 MOD 전역에서 이름을 읽으므로 shim 속성을 바꾸면 계측을 **조용히** 잃는다(probe는 수집 밖이라 pytest가 못 잡음; B26-1 test는 M9 모의에서 FAIL로 드러남) | 대상 = **그 이름을 전역으로 읽고 같은 정의로 푸는 MOD 전부**에 한 문장 사슬 대입(`M1.n = M2.n = 값`); 0이면 정의 모듈 하나. 실제 M 병합본에서 G1로 호출자 모듈을 계산(초안 r1 모의 14/14 일치 표 -- 예 `_hr_resolve_vertical_group` → MOD4·MOD8, `repair_matching_safety`(정의 SD) → MOD8). test(`test_b26_rail_accessor`)는 아래 4.1-④ |
| J2 | `import_module("sizing_recipe")` 반환 도우미: `test_d_delete_dead.py:101`·`test_d_delete_telescopic.py:111`·`test_dup_w_calc.py:75`(`_import_sizing_recipe` + 동적 `getattr`), `test_dup_kcl_edges.py:35`(`_sd()`), `test_ts6_dead_probes.py:229~230`(부재 단언 `not hasattr`), `test_restore_plan_functions.py:59`(`_import(name)`)·113·120·127·134·140(`_import("sizing_recipe")`) | 목적지를 이름으로 정할 수 없는 모듈 객체 | 이름을 받는 도우미 = 이름마다 정의 모듈을 돌려줌; **부재 단언 = 'N3.10 모듈 어디에도 없다'**(한 MOD만 보면 약화). `_import("sizing_recipe")` 5곳은 그 결과로 읽는 이름의 정의 모듈 하나로(초안 r4: 5곳 모두 한 모듈). 이 셋은 test 작성자 몫 |
| J3 | 이름 안 읽는 순서용 import: `test_restore_plan_functions.py:54` `import sizing_recipe`('run_harness보다 먼저') | 목적 = 트리의 엔진을 먼저 묶기 | `import gmid_design_pipeline`(MOD10 -- 진입이라 MOD1~9를 끌어옴; M10 뒤라야 함) |
| J4 | 정의 없는 이름: `workspaces/current-reuse…/diagnose_cmrr_cmfb.py:19` `_cmfb_amp_gain_diode_load`(Phase 2 삭제), `workspaces/current-reuse…/stick.py:9` `block_from_row_widths` | base에서 이미 ImportError인 스크립트 | 정의 있는 이름만 옮기고 없는 이름은 같은 문장에 남은 정의 모듈 import 중 하나에 둔다(깨진 상태를 고치지도 숨기지도 않음). 대안: 스크립트 정리(백로그) |
| J5 | 실행 문자열: `contracts/test_b34_grammar_explicit.py:129` `_B34_FRESH_SCRIPT`(subprocess `-c`로 실행 -- SD 삭제 이름 10개: `find_idiom_matches`·`audit_theta_root_direction`(→MOD2), `find_differential_and_mirror_forks`·`find_differential_pair_candidates`·`find_verified_differential_and_mirror_relations`·`refine_differential_and_mirror_relations`·`suggest_vertical_stack_composites`·`propose_theta_kcl_gap_fill`·`propose_device_roles_gap_fill`·`propose_vertical_stack_id_gap_fill`(→MOD3)) | AST 스캔이 문자열 안을 못 봐 F2 뒤 c8 × 9회로 `AttributeError`(F2 모의 실측: `test_b34_c8…` 9 FAIL) | 문자열 내용만 바꾼다(원래 `import stick_diagram` 뒤에 `import circuit_state_graph as _f1_csg`·`import topology_authoring as _f1_ta`, 10자리 접두 교체; SD 잔류 `load_topology`·`run_topology_pipeline`·`find_stack_edges`·`geometry_colocation_union`은 그대로). 157행 `_B34_IMPORT_SCRIPT`(`import stick_diagram`만)는 그대로 |
| J6 | 실행되지 않는 합성 소스 문자열 21개·7파일(`test_d_delete_dead.py:379~386`·`test_d_delete_telescopic.py:495~510`·`test_d_move_tests.py:279~404`·`test_dup_w_calc.py:477`·`test_phase2_stale_refs.py:114`·`test_probe_dup_scan.py:211·292`·`test_ts6_dead_probes.py:251`) | 정적 검사기 입력(판정 대상 소스 조각) | **바꾸지 않는다**(바꾸면 test 입력이 바뀜 -- 초안 b1fix 결론) |
| J7 | 엔진 파일 이름 앵커(F2에서 깨짐): `test_d_delete_dead.py:74`·`test_d_move_tests.py:73` `_REQUIRED_ENGINE_FILES`, `test_d_delete_telescopic.py:117`, `test_df35_harness_paths.py:206`, `test_ts6_probe_relocate.py:528`, `test_dup_w_calc.py:56`(정의 앵커), `test_d_move_tests.py:69` `_REQUIRED_ENGINE_IMPORT = {"regression_runner": "sizing_recipe"}` | 파일·모듈 이름으로 존재·import를 단언 | 부재·경로 앵커 5줄 → "N3.10 MOD 파일 전부가 있다", 정의 앵커 → 그 이름의 정의 파일(`size_transistor`·`width_from_id_density` → MOD4), import 앵커 → "regression_runner가 import한 모듈 ∩ 엔진 모듈 ≠ ∅"(F1 test 커밋이 code 커밋보다 먼저여도 통과하는 모양 -- 초안 B1). 4.2 참조 |
| J8 | `tests/tools/derive_achievable_bounds.py:33` `import sizing_recipe as sr` ↔ `contracts/test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`(base `939f926` blob과 '경로 줄 밖 차이 0') | F1이 도구 import를 바꾸면 이 test FAIL(초안 실측 33 passed → 1 failed) | 4.2-⑤ 참조(사용자 기존 결정 (마)와 연결 -- 오케스트레이터 확인 필요) |

### 2.5 초안에서 버린 것
계약 3 동등 판정기(가)~(사)·표지 정규화·탈출 자리 목록 단위·S1 목록·V5 ①~⑥ 승인·두 해시·운반·두 번 시도·쓰기 경로표 승인(`plan_tables`)·착수 조건 (1)~(3)의 '멈추고 묻는다'·실행 문자열 정의 (s1)~(s3)/(w1)~(w3) 전문(판정 쪽). 남긴 것 = 바꾸는 모양(위 M1~M4·J1~J8 기본안)과 그 근거 실측.
F1 뒤 확인(가벼운 절차 4): 전체 pytest(기존 결과 같음) + E-INST·E-LIB base 같음 + 추가로 AST 한 번: D-9 밖 추적 `.py`에 SR·TL·DR import 문·import 호출 0, SD 삭제 집합 이름을 SD에서 읽는 곳 0(실행 문자열 J5 포함 -- 문자열은 눈으로/파싱으로).

---

## 3. F2 -- shim 삭제와 깨질 것

### 3.1 바꾸는 것(코드)
`A/sizing_recipe.py`·`topology_library.py`·`design_report.py` 삭제 + SD 최상위 `from <N3.10 줄기> import …`에서 SD가 어느 유효 범위에서도 읽지 않는 이름 삭제(모의 **50**: 초안 49 + B26-1 `rail_declaration`) + ACF의 M card 재수출에서 ACF가 안 읽는 이름 삭제(`_as_set`·`_theta_evidence_for_pair` -- `audit_topology`는 `render_report`가 읽어 남김). 남는 import 줄 위치는 그대로.
새 test 하나(초안 계약 6을 가볍게): 세 shim 파일 없음 + 판정 트리·`run_harness.py`에 세 모듈 import 0 + `import_layering --root` exit 0. 둘 다 F2 전 FAIL(실측: M9 모의 `import_layering` exit 1 -- `MOD7 stick_diagram → MOD9 instance_report_builder` 큰 번호 import 1·순환 1; F2 모의 exit 0, findings 0, present 9(M10 있으면 10)).

### 3.2 F1 없이 지우면 깨지는 것(F2 모의 실측 -- F1의 대상 그 자체)
* **PT3 수집 오류 14파일**: `contracts/test_b26_backfill_interdig.py`·`test_b26_rail_accessor.py`·`test_b26pre_existing_paths.py`·`test_restore_plan_functions.py`, `unit/test_probe_gm_id_monotonicity.py`·`test_probe_lut_L_interpolation.py`·`test_probe_parasitic_pm_all_circuits.py`·`test_probe_prevention_wiring.py`·`test_probe_revalidation_scope.py`·`test_probe_role_L_derivation.py`, `unit/test_selftest_{design_report,sizing_recipe,stick_diagram,topology_library}.py`(마지막 넷 중 SD는 `apply_device_roles_gap_fill` ImportError).
* **FAIL/ERROR 12파일 135건**: `test_dup_w_calc` 26 · `test_df36_instance_relpath` 24 · `test_dup_kcl_edges` 23 · `test_b34_grammar_explicit` 20(c1 9·c8 9·c5·c6) · `test_d_delete_dead` 16 · `test_d_delete_telescopic` 12 · `test_df35_harness_paths` 6 · `test_ts6_dead_probes` 3 · `test_d_move_tests` 2 · `test_ic3` 1 · `test_ic5` 1 · `test_ts6_probe_relocate` 1(`test_assets_dir_holds_engine_entry_points`).
  합계 122 failed + 27 errors. 수집된 test 839(base 1194 -- 수집 오류 14파일의 test 355개가 빠짐).
* **pytest가 보지 않는 것**(조용히 깨짐): probe 32·workspaces 20(run_harness 포함)·`tests/tools` 2(`derive_achievable_bounds.py`·`regression_runner.py`)·`tests/` 루트 2(`conftest.py:160` 함수 안 `from sizing_recipe import build_toy_lut` -- 그 fixture를 쓰는 test만 실패, `probe_physical_consistency.py`) -- 2.2 목록 전부. `run_harness.py`가 깨지면 E-INST가 잡는다.
* **D-9 제외 15파일**(`.ai/verification/**` 증거 스크립트 등): 고치지 않는다 -- 깨짐은 기록만(design D-9). references 문서(D-14)는 보고만.

### 3.3 F1을 해도 F2에서 깨지는 것 = F1이 test 쪽에서 미리 바꿔야 할 것
2.4 J7(앵커 7줄·6파일)·J8(TS6 blob 대조)·`test_ts6_dead_probes.py:60·229`(`_SIZING_RECIPE` 파일·`import_module("sizing_recipe")` 부재 단언). 초안 실측: 앵커를 안 고친 F1 위 F2에서 PT3 +9 FAIL. F2 card는 test를 고치지 않는다(F1 몫).

---

## 4. M 이동 중(·F1/F2에서) 깨질 test -- 위치 무관 수정 vs legacy 버림 분류

### 4.1 M 이동이 실제로 깨는 것(M9 모의 PT3 실측 4 FAIL + 공허 1)
| # | test | 깨지는 card | 원인 | 분류 | 근거 |
|---|---|---|---|---|---|
| ① | `contracts/test_dup_w_calc.py::test_size_transistor_calls_new_function`(442행) | M4(`size_transistor` → MOD4) | `sizing_recipe.py` 한 파일에서 정의를 찾음 | **위치 무관 수정** | dup-w-calc 계약(식 정본 `width_from_id_density` 호출)은 엔진 규칙이다. 정의 파일 = `A/*.py`·`run_harness.py` 중 최상위 바인딩이 정확히 하나인 파일(R-DEF, T0 초안 규칙 -- 0이면 공허, 2+면 사본 FAIL) |
| ② | `contracts/test_ic5.py::test_gate_docstring_declares_blind_spots`(`_DOMAIN_TABLE` 47~69행, (파일, 함수) 키 21) | M2·M3·M4·M9 등 | 키에 파일 이름 | **위치 무관 수정** | 판정(게이트 함수 docstring의 사각 선언)은 함수에 붙는다. 키를 함수 이름으로, 파일은 R-DEF로 찾음 |
| ③ | `contracts/test_ts6_dead_probes.py::test_audit_vsb_consistency_has_operational_caller`(259~263행) | M8(호출자 `_build_theta_evaluator` → MOD8) | 호출자를 SR에서만 찾음 | **위치 무관 수정** | '운영 호출자 있음'은 엔진 전체 범위로(넓어지기만 함) |
| ④ | `contracts/test_b26_rail_accessor.py::test_b26_c3_rail_declaration_call_count`(334행 `monkeypatch.setattr(stick_diagram, "rail_declaration", …)`) | M2(`rail_declaration` → MOD2)·M3(`load_topology` → MOD3) | 모듈 속성 하나만 교체 → 이동 뒤 호출 계수 0(`assert 0 == 1`) | **위치 무관 수정** | B26-1 계약 3(재계산 금지)은 엔진 성질. 원래 객체와 같은 객체를 전역으로 묶은 A 아래 로드된 모듈 **전부**에서 교체(정의 위치를 적지 않음). 이번 판에서 막 만든 test라 legacy 아님 |
| ⑤ | `contracts/test_ts6_dead_probes.py::test_sizing_recipe_source_has_no_l_role_multipliers`(219~222행) | M 동안 **조용히 공허**(통과는 함), F2에서 FAIL(파일 없음) | 바인딩 검사 범위가 SR 한 파일 | **위치 무관 수정**(범위를 엔진 전체로) | Phase 2 삭제 보증(TS6) -- 엔진 어디에도 다시 생기지 않음을 보는 편이 원 뜻. 비용 작음 |
* M 동안 **안 깨지는 것**(실측): `unit/test_selftest_*.py` 4개(이 판 `move.py`의 완전 shim이 일반 import를 남겨 `np` 등 재수출 유지 -- T0 W-1 문제는 M에서 안 생기고 F2에서 생김 → F1 M4 규칙이 처리), `import run_harness` 23파일, `test_df23_inventory.py`(과거 측정 기록 대조 -- M9·F2 모의 모두 PASS, 범위 목록 56행은 기록 판의 것이라 고치지 않음).
* M 동안 **pytest 밖에서 조용히 깨지는 것**: 2.4 J1의 probe·workspaces D-17 계측(shim 속성 교체가 MOD 호출자에 안 닿음) -- 실행 결과가 틀려도 실패가 안 남. F1에서 고치거나, M 동안은 probe 결과를 믿지 않는다고 기록.

### 4.2 F1/F2가 건드리는 test(앵커·blob) 분류
| # | test(줄) | 분류 | 근거 |
|---|---|---|---|
| ⑥ | 부재·경로 앵커 5줄: `test_d_delete_dead.py:74`·`test_d_delete_telescopic.py:117`·`test_d_move_tests.py:73`·`test_df35_harness_paths.py:206`·`test_ts6_probe_relocate.py:528` | **위치 무관 수정** | 판정 뜻(지운 이름 부재 범위·ASSETS 경로·A 디렉터리 전제)은 엔진이 있는 한 유효. "SR 파일이 있다" → "N3.10 MOD 파일 전부가 있다"(넓힘, F1 전·후·F2 뒤 모두 참) |
| ⑦ | 정의 앵커 `test_dup_w_calc.py:56`, import 앵커 `test_d_move_tests.py:69`(229·237행 단언) | **위치 무관 수정** | ①과 같은 R-DEF / "엔진 모듈 중 하나를 import" -- 복사 금지 단언(234~235행)은 그대로 |
| ⑧ | 모듈 객체 도우미 J2(`test_d_delete_dead`·`test_d_delete_telescopic`·`test_dup_w_calc` `_import_sizing_recipe`, `test_dup_kcl_edges` `_sd`, `test_ts6_dead_probes:229`, `test_restore_plan_functions` `_import`) | **위치 무관 수정** | 레지스트리·이름 부재 판정은 엔진 규칙. 이름 → 정의 모듈, 부재 → 모든 N3.10 모듈 |
| ⑨ | `contracts/test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`(base `939f926` blob 대조) | **legacy 버림 후보 -- 단 오케스트레이터 확인 필요** | 2026-09-23 TS6 '도구 이동이 계산을 바꾸지 않았다'는 1회성 이동 증거다(이동은 끝났고 F1은 그 도구 import만 바꾼다). 위치 무관하게 고치려면 (마) 전체 정규화 핀(초안 계약 1 (d) -- 별칭표·binds·정규형 N, 수십 줄)이 필요하다. **충돌**: 사용자 결정 `[F1·#2] TS6` "(마) 전체 정규화 핀"(2026-10-02)은 V5 승인 질문의 답이었다 -- 가벼운 절차가 V5를 버렸어도 '이 test를 버림'은 그 답과 다른 처리라 묻거나 (마)를 구현해야 한다. Phase 4 #2(`d4-delete-unwired`)도 이 test 규칙 위에 핀 편집을 얹기로 했다 |
| ⑩ | `contracts/test_ts6_dead_probes.py:229` 모듈 부재 단언(`importlib.import_module("sizing_recipe")`) | ⑧과 같음(수정) | -- |

### 4.3 T0·T1이 다루던 것
* **T0(A군 + W-1)**: 4.1 ①~③·⑤ = T0 A군 그대로(실측으로 재확인), ④ = T0 v5 B26 항목. W-1(selftest 3줄 비엔진 이름)은 이 판 도구로는 M에서 안 깨지고 F1 M4 규칙 몫. → T0는 card로 따로 두지 않고 **M2 전(④는 M2에서 깨짐)**에 위치 무관 수정 한 커밋(test 작성 주체)으로 하면 M1~M9가 매번 전체 pytest를 통과한다. 수정 시점을 뒤로 미루면 M2~M9 사이 '기존 test 깨짐' 보고가 매 card 반복된다.
* **T1(`unit/test_selftest_*.py` 4개 → `unit/test_mod<k>_*.py` 재배치·`test_ts3_no_print_verdicts._LEGACY_SCRIPTS` 갱신)**: **legacy 절차 -- 버림**. 근거: test 파일 이름·위치는 엔진 동작과 무관하고 판정 불변이 계약이었다(옮김만, 본문 그대로). 재배치하지 않으면 깨지는 것이 없다(M9·F2 모의에서 그 4파일의 실패는 전부 import 출처 문제 -- F1 몫). 이름만 낡는다(`test_selftest_sizing_recipe.py`가 없는 모듈 이름). 필요하면 Phase 4 이후 정리.
* 계획서가 test 위치를 가정하는 곳: 계획 N3.11 `unit/test_mod1_gmid_lut.py ... unit/test_mod9_instance_report_builder.py`(541~543행)·`10-test-separation` 187·413행(매핑 test id) -- T1을 버리면 이 문장이 사실과 다르다(문서 정정 대상으로만 기록, 깨지는 test 없음).

---

## 5. 순서 제안(가벼운 절차)
1. (M2 전) 4.1 ①~⑤ 위치 무관 수정(test 주체) -- 전체 pytest base 같음 확인.
2. M1~M9(move.py; FU 대역이 필요 -- `move.py MOD2`가 `__future__` 혼합으로 멈춤, 실측. FU를 버렸다면 DR·ACF에 `from __future__ import annotations` 한 줄씩 넣는 선행 커밋이 필요).
3. M10(1.2 코드 + 1.3 test, 작성자 분리).
4. F1: 실제 M10 병합본에서 스캔 재실행 → test 주체가 `A/tests/**`(J2·J7·⑥⑦⑧, ⑨는 결정 뒤), code 주체가 probe·workspaces·`tests/tools`·`run_harness.py`(M1~M4·J1·J3·J4·J5는 test 파일이므로 test 주체). 확인: pytest·E-INST·E-LIB + AST(SR·TL·DR importer 0, SD 삭제 집합 reader 0).
5. F2: 3.1 + 새 test 1. 확인: pytest 실패 0·`import_layering` exit 0·E-INST·E-LIB.

## 6. 열린 것(오케스트레이터)
* ⑨ TS6 blob test: 버림(legacy) vs (마) 구현 -- 사용자 기존 답과 충돌 여부 판단.
* FU 대역: 가벼운 절차 순서에 FU가 없는데 `move.py MOD2`가 멈춘다.
* 레지스트리 '이관 목적지' 열 80단위 낡음(정정 여부).
* J4 깨진 workspaces 스크립트 2개(백로그 유지 vs 정리).

## 부록 A. F1 전수 목록(cb0ef86, M9 모의 배정) -- `파일:행 종류 모듈 -- 이름->목적지 [분류]`
(`SD유지` = F2 뒤에도 `stick_diagram`에 바인딩이 남는 이름 -- 그 읽기는 바꾸지 않음. `기계적(다중)` = 별칭 하나에 목적지 여럿 -- 2.3 M3. 속성 줄의 (n)은 첫 줄 번호.)

#### F1-기계적만 (55파일)

* `A/tests/conftest.py`
  * :160 from `sizing_recipe` -- build_toy_lut->gmid_lut [기계적]
* `A/tests/contracts/test_b26_backfill_interdig.py`
  * :49 import `sizing_recipe` -- alias=sizing_recipe [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_sizing_engine, sizing_layout_convergence)
    * 속성: SizingContext->gmid_sizing_engine(98), Transistor->circuit_state_graph(72), run_matching_safety_with_finger_growth->sizing_layout_convergence(99), size_transistor->gmid_sizing_engine(61)
* `A/tests/contracts/test_b26pre_existing_paths.py`
  * :33 import `sizing_recipe` -- alias=sizing_recipe [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_sizing_engine, sizing_layout_convergence)
    * 속성: SizingContext->gmid_sizing_engine(108), Transistor->circuit_state_graph(56), optimize_full_circuit_budget->sizing_layout_convergence(162), resolve_stack_layout->sizing_layout_convergence(419), run_matching_safety_with_finger_growth->sizing_layout_convergence(195), size_transistor->gmid_sizing_engine(45)
  * :34 import `stick_diagram` -- alias=stick_diagram [기계적(다중)] -- 목적지 4개: 별칭 추가+속성 접두 교체 ((유지)stick_diagram, circuit_state_graph, instance_report_builder, topology_authoring)
    * 속성: build_stick_diagram->SD유지(122), find_differential_pair_candidates->circuit_state_graph(576), load_topology->SD유지(475), propose_vertical_stack_id_gap_fill->circuit_state_graph(436), rail_declaration->topology_authoring(418), run_full_circuit_audit_from_topology->instance_report_builder(356)
* `A/tests/contracts/test_b34_grammar_explicit.py`
  * :45 import `stick_diagram` -- alias=stick_diagram [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 ((유지)stick_diagram, circuit_state_graph, topology_authoring)
    * 속성: Transistor->SD유지(247), audit_theta_root_direction->topology_authoring(273), find_differential_and_mirror_forks->circuit_state_graph(195), find_differential_pair_candidates->circuit_state_graph(201), find_idiom_matches->topology_authoring(192), find_stack_edges->SD유지(252), find_verified_differential_and_mirror_relations->circuit_state_graph(204), geometry_colocation_union->SD유지(219), load_topology->SD유지(177), propose_device_roles_gap_fill->circuit_state_graph(216), propose_theta_kcl_gap_fill->circuit_state_graph(213), propose_vertical_stack_id_gap_fill->circuit_state_graph(222), rail_declaration->topology_authoring(268), refine_differential_and_mirror_relations->circuit_state_graph(207), run_topology_pipeline->SD유지(186), suggest_vertical_stack_composites->circuit_state_graph(198)
* `A/tests/contracts/test_df36_instance_relpath.py`
  * :76 from `stick_diagram` -- run_topology_pipeline->SD유지 [변경없음(SD/ACF 잔류 이름)]
  * :87 from `stick_diagram` -- save_instance_json->instance_report_builder [기계적]
  * :237 from `stick_diagram` -- save_instance_json->instance_report_builder [기계적]
  * :274 from `stick_diagram` -- save_instance_json->instance_report_builder [기계적]
  * :288 from `stick_diagram` -- save_instance_json->instance_report_builder [기계적]
* `A/tests/contracts/test_ic3.py`
  * :107 from `stick_diagram` -- INSTANCE_SIZING_FIELDS->instance_report_builder, INSTANCE_TOP_FIELDS->SD유지, check_instance_completeness->instance_report_builder, check_stick_diagram_coverage->SD유지, check_topology_name_uniqueness->circuit_state_graph, load_topology->SD유지, run_topology_pipeline->SD유지, save_instance_json->instance_report_builder [기계적]
  * :271 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `A/tests/probe_physical_consistency.py`
  * :35 import `sizing_recipe` -- alias=sr [기계적] -- import 줄만 -> import circuit_state_graph as sr
    * 속성: load_topology->circuit_state_graph(42)
* `A/tests/probes/probe_L_search_window.py`
  * :33 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(46), _build_theta_evaluator->sizing_layout_convergence(59), presolve_warm_start->sizing_layout_convergence(60)
* `A/tests/probes/probe_allocation_solvers.py`
  * :27 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (gmid_lut, gmid_sizing_engine)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(30), size_transistor->gmid_sizing_engine(41)
* `A/tests/probes/probe_area_pareto.py`
  * :38 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(60), is_diode_connected->circuit_state_graph(85), load_topology->circuit_state_graph(84), optimize_full_circuit_budget->sizing_layout_convergence(99)
* `A/tests/probes/probe_classab_battery_headroom.py`
  * :47 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (gmid_sizing_engine, sizing_layout_convergence)
    * 속성: InfeasibleSizingError->gmid_sizing_engine(87), _DEFAULT_MIN_VDS_FALLBACK->gmid_sizing_engine(67), _build_theta_evaluator->sizing_layout_convergence(80)
* `A/tests/probes/probe_diode_min_vgs.py`
  * :28 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, gmid_sizing_engine)
    * 속성: DiodeSelfConsistencyError->gmid_sizing_engine(75), SemiEmpiricalGmIdLUT->gmid_lut(40), is_diode_connected->circuit_state_graph(46), load_topology->circuit_state_graph(34), solve_diode_connected_vds->gmid_sizing_engine(74)
* `A/tests/probes/probe_diode_self_consistency.py`
  * :39 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, gmid_sizing_engine)
    * 속성: DiodeSelfConsistencyError->gmid_sizing_engine(74), SemiEmpiricalGmIdLUT->gmid_lut(50), is_diode_connected->circuit_state_graph(57), load_topology->circuit_state_graph(44), solve_diode_connected_vds->gmid_sizing_engine(69)
* `A/tests/probes/probe_diode_vds_window.py`
  * :26 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, gmid_sizing_engine)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(63), is_diode_connected->circuit_state_graph(56), load_topology->circuit_state_graph(54), size_transistor->gmid_sizing_engine(73)
* `A/tests/probes/probe_full_research.py`
  * :33 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(52), audit_vsb_consistency->circuit_state_graph(142), load_topology->circuit_state_graph(140), optimize_full_circuit_budget->sizing_layout_convergence(71)
* `A/tests/probes/probe_gmid_gain_landscape.py`
  * :22 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (gmid_lut, gmid_sizing_engine)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(25), size_transistor->gmid_sizing_engine(90)
* `A/tests/probes/probe_interp_scheme_loo.py`
  * :42 import `sizing_recipe` -- alias=sr [기계적] -- import 줄만 -> import gmid_lut as sr
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(87), _multilinear_interp->gmid_lut(97)
* `A/tests/probes/probe_l5c_stage2out_L.py`
  * :29 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(72), _build_theta_evaluator->sizing_layout_convergence(103)
* `A/tests/probes/probe_lclass_warm_start.py`
  * :29 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (circuit_state_graph, sizing_layout_convergence)
    * 속성: _build_theta_evaluator->sizing_layout_convergence(54), _metric_device_footprint->circuit_state_graph(65), presolve_warm_start->sizing_layout_convergence(83)
* `A/tests/probes/probe_metric_dashboard.py`
  * :30 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(59), is_diode_connected->circuit_state_graph(101), load_topology->circuit_state_graph(100), optimize_full_circuit_budget->sizing_layout_convergence(74)
* `A/tests/probes/probe_metric_tiers.py`
  * :27 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 4개: 별칭 추가+속성 접두 교체 (circuit_metrics, circuit_state_graph, gmid_lut, gmid_sizing_engine)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(34), SizingContext->gmid_sizing_engine(43), compute_metric->circuit_metrics(52), load_topology->circuit_state_graph(30)
* `A/tests/probes/probe_mirror_common_L.py`
  * :44 import `sizing_recipe` -- alias=sr [기계적] -- import 줄만 -> import gmid_lut as sr
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(62)
* `A/tests/probes/probe_mirror_design_space.py`
  * :97 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(117), is_diode_connected->circuit_state_graph(171), load_topology->circuit_state_graph(144), optimize_full_circuit_budget->sizing_layout_convergence(137), true_current_mirror_groups->circuit_state_graph(165)
* `A/tests/probes/probe_mirror_gain_ranking.py`
  * :92 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 4개: 별칭 추가+속성 접두 교체 (circuit_metrics, circuit_state_graph, gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(112), _build_theta_evaluator->sizing_layout_convergence(138), compute_metric->circuit_metrics(328), is_diode_connected->circuit_state_graph(167), load_topology->circuit_state_graph(158), optimize_full_circuit_budget->sizing_layout_convergence(132), true_current_mirror_groups->circuit_state_graph(161)
* `A/tests/probes/probe_mirror_infeasibility.py`
  * :36 import `sizing_recipe` -- alias=sr [기계적] -- import 줄만 -> import gmid_lut as sr
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(52)
* `A/tests/probes/probe_mirror_ratio_bound.py`
  * :36 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_metrics, circuit_state_graph, sizing_layout_convergence)
    * 속성: _build_theta_evaluator->sizing_layout_convergence(61), _matching_pairs_cached->circuit_state_graph(70), estimate_mismatch_sigma->circuit_metrics(118)
* `A/tests/probes/probe_mirror_ratio_error.py`
  * :34 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (circuit_metrics, topology_authoring)
    * 속성: _METRIC_UNITS->topology_authoring(89), estimate_mismatch_sigma->circuit_metrics(84)
* `A/tests/probes/probe_mirror_wiring_readiness.py`
  * :40 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(58), _build_theta_evaluator->sizing_layout_convergence(84), _gm_id_already_authoritative->circuit_state_graph(126), is_diode_connected->circuit_state_graph(105), load_topology->circuit_state_graph(96), optimize_full_circuit_budget->sizing_layout_convergence(78), true_current_mirror_groups->circuit_state_graph(99)
* `A/tests/probes/probe_ratio_pair_analysis.py`
  * :76 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(94), is_diode_connected->circuit_state_graph(145), load_topology->circuit_state_graph(110), optimize_full_circuit_budget->sizing_layout_convergence(107), true_current_mirror_groups->circuit_state_graph(112)
* `A/tests/probes/probe_runtime_budget.py`
  * :27 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(32), _build_theta_evaluator->sizing_layout_convergence(46), presolve_warm_start->sizing_layout_convergence(54)
* `A/tests/probes/probe_stack_headroom_feasibility.py`
  * :24 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, gmid_sizing_engine)
    * 속성: DiodeSelfConsistencyError->gmid_sizing_engine(50), SemiEmpiricalGmIdLUT->gmid_lut(36), is_diode_connected->circuit_state_graph(42), load_topology->circuit_state_graph(30), solve_diode_connected_vds->gmid_sizing_engine(49)
* `A/tests/probes/probe_stacked_diode_options.py`
  * :48 import `sizing_recipe` -- alias=sr [기계적] -- import 줄만 -> import gmid_lut as sr
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(66)
* `A/tests/probes/probe_supply_current.py`
  * :35 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_sizing_engine)
    * 속성: SizingContext->gmid_sizing_engine(69), _DEFAULT_RAIL_HI->circuit_state_graph(44), _DEFAULT_RAIL_LO->circuit_state_graph(45), _metric_supply_current->gmid_sizing_engine(69), load_topology->circuit_state_graph(39)
* `A/tests/tools/derive_achievable_bounds.py`
  * :33 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_state_graph, sizing_layout_convergence, theta_search)
    * 속성: achievable_metric_bound->sizing_layout_convergence(78), derived_bounds_path->theta_search(112), load_derived_bounds->theta_search(69), spec_fingerprint->circuit_state_graph(68)
* `A/tests/tools/regression_runner.py`
  * :17 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, _COMPENSATION_REGISTRY->gmid_sizing_engine, optimize_multistage->gmid_sizing_engine [기계적]
* `A/tests/unit/_library_sized_contexts.py`
  * :33 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (gmid_sizing_engine, sizing_layout_convergence)
    * 속성: InfeasibleSizingError->gmid_sizing_engine(157), _build_theta_evaluator->sizing_layout_convergence(155)
* `A/tests/unit/test_probe_lut_L_interpolation.py`
  * :34 import `sizing_recipe` -- alias=sr [기계적] -- import 줄만 -> import gmid_lut as sr
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(175)
* `A/tests/unit/test_probe_parasitic_pm_all_circuits.py`
  * :36 import `sizing_recipe` -- alias=sr [기계적] -- import 줄만 -> import circuit_state_graph as sr
    * 속성: _load_full_topology_cached->circuit_state_graph(156), node_pole_estimate->circuit_state_graph(188), signal_path_nodes->circuit_state_graph(159)
* `A/tests/unit/test_probe_prevention_wiring.py`
  * :47 import `sizing_recipe` -- alias=sr [기계적] -- import 줄만 -> import circuit_state_graph as sr
    * 속성: is_diode_connected->circuit_state_graph(84), load_topology->circuit_state_graph(83)
* `A/tests/unit/test_probe_revalidation_scope.py`
  * :39 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (circuit_metrics, gmid_sizing_engine, sizing_layout_convergence)
    * 속성: SizingContext->gmid_sizing_engine(145), _collect_device_refs->sizing_layout_convergence(103), compute_metric->circuit_metrics(144), revalidate_finger_override->sizing_layout_convergence(169), size_transistor->gmid_sizing_engine(118)
* `A/tests/unit/test_probe_role_L_derivation.py`
  * :31 import `sizing_recipe` -- alias=sr [기계적] -- import 줄만 -> import gmid_sizing_engine as sr
    * 속성: _L_ROLE_TARGETS->gmid_sizing_engine(79)
* `workspaces/current-reuse-telescopic-ota-report/probe_group_split_wiring.py`
  * :4 from `sizing_recipe` -- build_toy_lut->gmid_lut, size_transistor->gmid_sizing_engine, SizingContext->gmid_sizing_engine, run_topology_pipeline_with_finger_fixup->sizing_layout_convergence, _blocked_euler_rows->sizing_layout_convergence [기계적]
* `workspaces/current-reuse-telescopic-ota-report/rerun_symmetry.py`
  * :5 from `stick_diagram` -- load_topology->SD유지, find_matching_candidates->SD유지, find_hub_merge_candidates->SD유지, check_symmetry_dispositions->circuit_state_graph [기계적]
* `workspaces/current-reuse-telescopic-ota-report/resize.py`
  * :20 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, size_transistor->gmid_sizing_engine, gm_from_fT->gmid_sizing_engine [기계적]
* `workspaces/current-reuse-telescopic-ota-report/run_harness_smoke.py`
  * :9 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence [기계적]
* `workspaces/current-reuse-telescopic-ota-report/sample_metrics_session22.py`
  * :16 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence [기계적]
* `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session11.py`
  * :10 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence [기계적]
* `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session20.py`
  * :27 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence [기계적]
  * :28 from `stick_diagram` -- save_instance_json->instance_report_builder, run_full_circuit_audit_from_topology->instance_report_builder [기계적]
  * :29 from `design_report` -- assemble_report_data->instance_report_builder, save_html_report->instance_report_builder [기계적]
* `workspaces/current-reuse-telescopic-ota-report/structural_symmetry_probe.py`
  * :10 from `stick_diagram` -- load_topology->SD유지, find_structural_symmetry_candidates->circuit_state_graph [기계적]
* `workspaces/current-reuse-telescopic-ota-report/theta_sensitivity_session22.py`
  * :21 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence, InfeasibleSizingError->gmid_sizing_engine [기계적]
* `workspaces/run_harness.py`
  * :40 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence, dense_candidates->theta_search, layout_grid_L_candidates->theta_search, diagnose_sizing_roles_gap->sizing_layout_convergence [기계적]
  * :42 from `stick_diagram` -- save_instance_json->instance_report_builder, run_full_circuit_audit_from_topology->instance_report_builder [기계적]
  * :43 from `design_report` -- assemble_report_data->instance_report_builder, save_html_report->instance_report_builder [기계적]
* `workspaces/two-stage-ota-report/check_box_shape.py`
  * :18 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence, dense_candidates->theta_search, layout_grid_L_candidates->theta_search [기계적]
  * :19 from `stick_diagram` -- save_instance_json->instance_report_builder, run_full_circuit_audit_from_topology->instance_report_builder [기계적]
  * :20 from `design_report` -- assemble_report_data->instance_report_builder, save_html_report->instance_report_builder [기계적]
* `workspaces/two-stage-ota-report/check_box_shape_M5M7split.py`
  * :16 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence, dense_candidates->theta_search, layout_grid_L_candidates->theta_search [기계적]
  * :17 from `stick_diagram` -- save_instance_json->instance_report_builder, run_full_circuit_audit_from_topology->instance_report_builder [기계적]
  * :18 from `design_report` -- assemble_report_data->instance_report_builder, save_html_report->instance_report_builder [기계적]
* `workspaces/two-stage-ota-report/diagnose_gain_sweep.py`
  * :11 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence, dense_candidates->theta_search, layout_grid_L_candidates->theta_search [기계적]
* `workspaces/two-stage-ota-report/diagnose_gain_sweep2.py`
  * :14 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence, dense_candidates->theta_search, layout_grid_L_candidates->theta_search [기계적]

#### F1-판단 포함 (23파일)

* `A/tests/contracts/test_b26_rail_accessor.py`
  * :54 import `sizing_recipe` -- alias=sizing_recipe [기계적(다중)] -- 목적지 4개: 별칭 추가+속성 접두 교체 (circuit_metrics, circuit_state_graph, gmid_sizing_engine, sizing_layout_convergence)
    * 속성: SizingContext->gmid_sizing_engine(102), _build_theta_evaluator->sizing_layout_convergence(741), _metric_kcl_residual->gmid_sizing_engine(464), compute_metric->circuit_metrics(339), l_sharing_classes->circuit_state_graph(344), resolve_stack_layout->sizing_layout_convergence(393), true_current_mirror_groups->circuit_state_graph(375)
  * :55 import `stick_diagram` -- alias=stick_diagram [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 ((유지)stick_diagram, circuit_state_graph, topology_authoring)
    * 속성: RailDeclaration->SD유지(170), Transistor->SD유지(95), _branch_composite_pair->SD유지(386), _composite_collapse_for_crossover->SD유지(387), _diff_pair_layer1_groups->circuit_state_graph(515), _kcl_and_matching_edges->circuit_state_graph(370), _kcl_branch_map->SD유지(385), _propose_L_roles->circuit_state_graph(367), _propose_gm_id_roles->circuit_state_graph(365), audit_vertical_stack_id_vs_kcl->circuit_state_graph(371), check_symmetry_dispositions->circuit_state_graph(376), find_differential_pair_candidates->circuit_state_graph(517), find_matching_candidates->SD유지(361), find_min_crossover_layout_with_branch_composite->SD유지(389), kcl_series_union->SD유지(369), load_topology->SD유지(259), propose_device_roles_gap_fill->circuit_state_graph(619), propose_vertical_stack_id_gap_fill->circuit_state_graph(382), rail_declaration->topology_authoring(327), refine_differential_and_mirror_relations->circuit_state_graph(380), repair_matching_safety->SD유지(391), run_full_circuit_audit->SD유지(377)
  * :334 D17_assign `stick_diagram` -- stick_diagram.rail_declaration = ... (정의 topology_authoring) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
* `A/tests/contracts/test_d_delete_dead.py`
  * :101 import_call `sizing_recipe` -- "sizing_recipe" [판단] -- import_module 문자열 -- 그 결과로 읽는 이름의 목적지 수에 따름
* `A/tests/contracts/test_d_delete_telescopic.py`
  * :111 import_call `sizing_recipe` -- "sizing_recipe" [판단] -- import_module 문자열 -- 그 결과로 읽는 이름의 목적지 수에 따름
* `A/tests/contracts/test_dup_kcl_edges.py`
  * :35 import_call `stick_diagram` -- "stick_diagram" [판단] -- import_module 문자열 -- 그 결과로 읽는 이름의 목적지 수에 따름
* `A/tests/contracts/test_dup_w_calc.py`
  * :75 import_call `sizing_recipe` -- "sizing_recipe" [판단] -- import_module 문자열 -- 그 결과로 읽는 이름의 목적지 수에 따름
* `A/tests/contracts/test_restore_plan_functions.py`
  * :54 import `sizing_recipe` -- alias=sizing_recipe [판단] -- 이름을 읽지 않는 import(순서·존재 확인용)
  * :59 dynamic_import_call `?` -- ? [판단] -- dynamic_import_call
  * :113 import_call `sizing_recipe` -- "sizing_recipe" [판단] -- import_module 문자열 -- 그 결과로 읽는 이름의 목적지 수에 따름
  * :120 import_call `sizing_recipe` -- "sizing_recipe" [판단] -- import_module 문자열 -- 그 결과로 읽는 이름의 목적지 수에 따름
  * :127 import_call `sizing_recipe` -- "sizing_recipe" [판단] -- import_module 문자열 -- 그 결과로 읽는 이름의 목적지 수에 따름
  * :134 import_call `sizing_recipe` -- "sizing_recipe" [판단] -- import_module 문자열 -- 그 결과로 읽는 이름의 목적지 수에 따름
  * :140 import_call `sizing_recipe` -- "sizing_recipe" [판단] -- import_module 문자열 -- 그 결과로 읽는 이름의 목적지 수에 따름
* `A/tests/contracts/test_ts6_dead_probes.py`
  * :229 import_call `sizing_recipe` -- "sizing_recipe" [판단] -- import_module 문자열 -- 그 결과로 읽는 이름의 목적지 수에 따름
  * :230 dynamic_getattr `sizing_recipe` -- sizing_recipe [판단] -- dynamic_getattr
* `A/tests/probes/probe_b22_headroom_attribution.py`
  * :38 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 3개: 별칭 추가+속성 접두 교체 (gmid_lut, gmid_sizing_engine, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(56), _build_theta_evaluator->sizing_layout_convergence(107), diode_vds_window->gmid_sizing_engine(95), optimize_full_circuit_budget->sizing_layout_convergence(130)
  * :104 D17_assign `sizing_recipe` -- sizing_recipe.diode_vds_window = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
  * :116 D17_assign `sizing_recipe` -- sizing_recipe.diode_vds_window = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
* `A/tests/probes/probe_diode_gmid_readiness.py`
  * :16 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 4개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, gmid_sizing_engine, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(66), _hr_resolve_vertical_group->gmid_sizing_engine(52), is_diode_connected->circuit_state_graph(46), load_topology->circuit_state_graph(44), optimize_full_circuit_budget->sizing_layout_convergence(81)
  * :63 D17_assign `sizing_recipe` -- sizing_recipe._hr_resolve_vertical_group = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
* `A/tests/probes/probe_diode_pass_skips.py`
  * :34 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 4개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, gmid_sizing_engine, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(97), _AUTHORITATIVE_GM_ID_SOURCES->circuit_state_graph(78), apply_diode_self_consistent_gm_id->gmid_sizing_engine(69), is_diode_connected->circuit_state_graph(63), load_topology->circuit_state_graph(62), optimize_full_circuit_budget->sizing_layout_convergence(113)
  * :94 D17_assign `sizing_recipe` -- sizing_recipe.apply_diode_self_consistent_gm_id = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
* `A/tests/probes/probe_diode_window_corner.py`
  * :43 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 4개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, gmid_sizing_engine, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(70), allocate_stack_headroom->gmid_sizing_engine(86), diode_vds_window->gmid_sizing_engine(87), is_diode_connected->circuit_state_graph(84), load_topology->circuit_state_graph(83), optimize_full_circuit_budget->sizing_layout_convergence(102)
  * :100 D17_assign `sizing_recipe` -- sizing_recipe.diode_vds_window = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
  * :108 D17_assign `sizing_recipe` -- sizing_recipe.diode_vds_window = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
* `A/tests/probes/probe_matching_pair_divergence.py`
  * :80 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 2개: 별칭 추가+속성 접두 교체 (gmid_lut, sizing_layout_convergence)
    * 속성: SemiEmpiricalGmIdLUT->gmid_lut(99), _optimize_theta_slsqp->sizing_layout_convergence(114), optimize_full_circuit_budget->sizing_layout_convergence(126)
  * :124 D17_assign `sizing_recipe` -- sizing_recipe._optimize_theta_slsqp = ... (정의 sizing_layout_convergence) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
* `A/tests/probes/probe_vds_assignment_paths.py`
  * :26 import `sizing_recipe` -- alias=sr [기계적(다중)] -- 목적지 4개: 별칭 추가+속성 접두 교체 (circuit_state_graph, gmid_lut, gmid_sizing_engine, sizing_layout_convergence)
    * 속성: DEFAULT_POLICY->gmid_sizing_engine(56), SemiEmpiricalGmIdLUT->gmid_lut(87), _feed_vds_fallback->gmid_sizing_engine(49), _hr_resolve_vertical_group->gmid_sizing_engine(75), _metric_stage_budget_vds_by_device->gmid_sizing_engine(64), allocate_stack_headroom->gmid_sizing_engine(55), is_diode_connected->circuit_state_graph(128), load_topology->circuit_state_graph(117), optimize_full_circuit_budget->sizing_layout_convergence(102), resolve_feed_vds->gmid_sizing_engine(36)
  * :47 D17_assign `sizing_recipe` -- sizing_recipe.resolve_feed_vds = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
  * :53 D17_assign `sizing_recipe` -- sizing_recipe._feed_vds_fallback = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
  * :62 D17_assign `sizing_recipe` -- sizing_recipe.allocate_stack_headroom = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
  * :73 D17_assign `sizing_recipe` -- sizing_recipe._metric_stage_budget_vds_by_device = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
  * :79 D17_assign `sizing_recipe` -- sizing_recipe._hr_resolve_vertical_group = ... (정의 gmid_sizing_engine) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
* `A/tests/unit/test_selftest_design_report.py`
  * :24 from `design_report` -- assemble_report_data->instance_report_builder, build_topology_device_table->instance_report_builder, os->EXT:os, render_html_report->instance_report_builder [판단] -- 비엔진/미정의: os=EXT:os
  * :25 from `stick_diagram` -- run_full_circuit_audit_from_topology->instance_report_builder [기계적]
* `A/tests/unit/test_selftest_sizing_recipe.py`
  * :24 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, SizingContext->gmid_sizing_engine, Transistor->circuit_state_graph, _COMPENSATION_REGISTRY->gmid_sizing_engine, _blocked_euler_rows->sizing_layout_convergence, _build_theta_evaluator->sizing_layout_convergence, _dc_replace->EXT:dataclasses.replace, _full_circuit_response->circuit_metrics, _group_score_interior->theta_search, _group_score_metric->theta_search, _invert_gm_id_for_current->gmid_sizing_engine, _lerp->theta_search, _load_full_topology_cached->circuit_state_graph, _nmcnr_stage1_rout->gmid_sizing_engine, allocate_stack_headroom->gmid_sizing_engine, apply_and_revalidate_matching_finger_growth->sizing_layout_convergence, apply_and_revalidate_pair_adjustment->sizing_layout_convergence, apply_theta_feed->circuit_metrics, build_toy_lut->gmid_lut, check_quasi_static->gmid_sizing_engine, compute_metric->circuit_metrics, derive_class_L->gmid_sizing_engine, derive_role_L->sizing_layout_convergence, diagnose_sizing_roles_gap->sizing_layout_convergence, diode_vds_window->gmid_sizing_engine, estimate_area_budget->sizing_layout_convergence, estimate_mismatch_sigma->circuit_metrics, feasible_L_window->gmid_sizing_engine, find_optimal_sizing->gmid_sizing_engine, json->EXT:json, knee_L_for_kind->gmid_sizing_engine, load_topology->circuit_state_graph, math->EXT:math, nmcnr_predict_ac_response->gmid_sizing_engine, np->EXT:numpy, optimize_full_circuit_budget->sizing_layout_convergence, optimize_multistage->gmid_sizing_engine, propagate_topology_forced_currents->circuit_state_graph, require_declared_spec_source->circuit_state_graph, resolve_constraint_references->circuit_state_graph, resolve_stack_layout->sizing_layout_convergence, revalidate_finger_override->sizing_layout_convergence, run_matching_safety_with_finger_growth->sizing_layout_convergence, run_topology_pipeline_with_finger_fixup->sizing_layout_convergence, search_gm_id_for_role->gmid_sizing_engine, size_transistor->gmid_sizing_engine, solve_diode_connected_vds->gmid_sizing_engine, solve_diode_stack_current->gmid_sizing_engine, solve_id_for_target_gm->gmid_sizing_engine, suggest_matching_finger_growth->sizing_layout_convergence, suggest_pair_finger_adjustments->stick_diagram, validate_theta_declaration_order->circuit_state_graph [판단] -- 비엔진/미정의: _dc_replace=EXT:dataclasses.replace, json=EXT:json, math=EXT:math, np=EXT:numpy
  * :36 import `stick_diagram` -- alias=_b26_sd [기계적] -- import 줄만 -> import topology_authoring as _b26_sd
    * 속성: rail_declaration->topology_authoring(53)
* `A/tests/unit/test_selftest_stick_diagram.py`
  * :24 from `stick_diagram` -- COMMON_CENTROID_PATTERNS->SD유지, Counter->EXT:collections.Counter, FloorplanBlock->SD유지, INTERDIGITATION_PATTERNS->SD유지, Transistor->SD유지, _branch_composite_pair->SD유지, _build_crossover_segments->SD유지, _common_centroid_from_pattern_table->SD유지, _common_centroid_residual->SD유지, _composite_collapse_for_crossover->SD유지, _count_matching_pair_splits->SD유지, _dc_asdict->EXT:dataclasses.asdict, _dc_replace->EXT:dataclasses.replace, _hubleaf_sequence_node_path->SD유지, _is_perfect_crossover_score->SD유지, _mirror_node_map_from_pairs->SD유지, _pack_by_subkind->SD유지, _pair_odd_nodes_by_mirror->SD유지, _sorted_setmap->SD유지, apply_device_roles_gap_fill->topology_authoring, apply_theta_kcl_gap_fill->topology_authoring, assign_finger_geometry->SD유지, audit_row_split->SD유지, audit_theta_root_direction->topology_authoring, audit_vertical_stack_id_euler_feasibility->SD유지, audit_vertical_stack_id_vs_kcl->circuit_state_graph, block_from_rows->SD유지, build_graph->SD유지, build_mirror_symmetric_pattern->SD유지, build_stick_diagram->SD유지, check_box_shape->SD유지, check_euler_condition->SD유지, check_mirror_symmetry->SD유지, check_multi_leaf_hub_parity->SD유지, check_stick_diagram_coverage->SD유지, check_symmetry_dispositions->circuit_state_graph, check_walk_sequence->SD유지, common_centroid_layout->SD유지, defaultdict->EXT:collections.defaultdict, derive_horizontal_stack_groups->SD유지, evaluate_row_split_candidates->SD유지, find_authoritative_sizing_devices->topology_authoring, find_differential_and_mirror_forks->circuit_state_graph, find_differential_pair_candidates->circuit_state_graph, find_diffusion_safe_split_points->SD유지, find_diode_stacks->circuit_state_graph, find_euler_repair_options->SD유지, find_hub_merge_candidates->SD유지, find_idiom_matches->topology_authoring, find_matching_candidates->SD유지, find_min_crossover_layout->SD유지, find_min_crossover_layout_with_branch_composite->SD유지, find_stack_edges->SD유지, find_stacked_matching_candidates->SD유지, find_unreviewed_device_roles->circuit_state_graph, find_unreviewed_matching_pairs->circuit_state_graph, find_verified_differential_and_mirror_relations->circuit_state_graph, folded_cascode_example->circuit_state_graph, geometry_colocation_union->SD유지, interdigitate_layout->SD유지, json->EXT:json, load_topology->SD유지, merge_layout_groups_by_matching_pairs->SD유지, mirror_symmetric_trail->SD유지, os->EXT:os, pack_floorplan->SD유지, pack_floorplan_grouped->SD유지, pack_group_as_unit->SD유지, propagate_topology_forced_currents->circuit_state_graph, propose_device_roles_gap_fill->circuit_state_graph, propose_theta_kcl_gap_fill->circuit_state_graph, propose_vertical_stack_id_gap_fill->circuit_state_graph, refine_differential_and_mirror_relations->circuit_state_graph, repair_matching_safety->SD유지, require_device_roles_reviewed->circuit_state_graph, run_full_circuit_audit->SD유지, run_full_circuit_audit_from_topology->instance_report_builder, run_topology_pipeline->SD유지, save_instance_json->instance_report_builder, search_shared_finger_w->SD유지, search_stack_finger_w->SD유지, search_unit_cell_sizing->SD유지, select_layout_tool->SD유지, skyline_pack_best_width->SD유지, split_into_stacks->SD유지, suggest_pair_finger_adjustments->SD유지, suggest_vertical_stack_composites->circuit_state_graph, trace_gnd_to_vdd_branches->circuit_state_graph, trace_vdd_to_gnd_branches->circuit_state_graph, two_stage_ota_example->circuit_state_graph [판단] -- 비엔진/미정의: Counter=EXT:collections.Counter, _dc_asdict=EXT:dataclasses.asdict, _dc_replace=EXT:dataclasses.replace, defaultdict=EXT:collections.defaultdict, json=EXT:json, os=EXT:os
  * :43 from `sizing_recipe` -- optimize_full_circuit_budget->sizing_layout_convergence [기계적]
  * :50 import `stick_diagram` -- alias=_b26_sd [기계적] -- import 줄만 -> import topology_authoring as _b26_sd
    * 속성: rail_declaration->topology_authoring(60)
  * :2127 from `stick_diagram` -- INSTANCE_SIZING_FIELDS->instance_report_builder [기계적]
* `A/tests/unit/test_selftest_topology_library.py`
  * :24 from `topology_library` -- current_reuse_telescopic_topology->gmid_sizing_engine, math->EXT:math, miller_ota_topology->gmid_sizing_engine, ngcc_3stage_topology->gmid_sizing_engine, nmcnr_3stage_topology->gmid_sizing_engine, nmcnr_check_dominant_pole_approximation->gmid_sizing_engine, nmcnr_compensation_elements->gmid_sizing_engine, nmcnr_predict_ac_response->gmid_sizing_engine [판단] -- 비엔진/미정의: math=EXT:math
* `workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py`
  * :18 import `sizing_recipe` -- alias=sizing_recipe [기계적] -- import 줄만 -> import stick_diagram as sizing_recipe
    * 속성: repair_matching_safety->stick_diagram(24)
  * :19 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence, compute_metric->circuit_metrics, SizingContext->gmid_sizing_engine, _cmfb_amp_gain_diode_load->UNDEFINED [판단] -- 비엔진/미정의: _cmfb_amp_gain_diode_load=UNDEFINED
  * :24 D17_assign `sizing_recipe` -- sizing_recipe.repair_matching_safety = ... (정의 stick_diagram) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
* `workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_psrr.py`
  * :11 import `sizing_recipe` -- alias=sizing_recipe [기계적] -- import 줄만 -> import stick_diagram as sizing_recipe
    * 속성: repair_matching_safety->stick_diagram(20)
  * :12 from `sizing_recipe` -- SemiEmpiricalGmIdLUT->gmid_lut, optimize_full_circuit_budget->sizing_layout_convergence, search_gm_id_for_role->gmid_sizing_engine [기계적]
  * :20 D17_assign `sizing_recipe` -- sizing_recipe.repair_matching_safety = ... (정의 stick_diagram) [판단] -- D-17 모듈 속성 덮어쓰기(계측) -- 대상 = 그 이름을 전역으로 읽는 MOD 전부
* `workspaces/current-reuse-telescopic-ota-report/probe_crossover_pairing_alternatives.py`
  * :16 from `stick_diagram` -- load_topology->SD유지, geometry_colocation_union->SD유지, build_graph->SD유지, check_euler_condition->SD유지, hierholzer->SD유지, _dc_replace->EXT:dataclasses.replace [판단] -- 비엔진/미정의: _dc_replace=EXT:dataclasses.replace
* `workspaces/current-reuse-telescopic-ota-report/probe_d1_verify.py`
  * :16 from `stick_diagram` -- load_topology->SD유지, geometry_colocation_union->SD유지, build_graph->SD유지, check_euler_condition->SD유지, _dc_replace->EXT:dataclasses.replace, _mirror_node_map_from_pairs->SD유지, _pair_odd_nodes_by_mirror->SD유지, _build_crossover_segments->SD유지, _count_matching_pair_splits->SD유지, _select_crossover_pairing->SD유지 [판단] -- 비엔진/미정의: _dc_replace=EXT:dataclasses.replace
* `workspaces/current-reuse-telescopic-ota-report/probe_group_split_reassembly.py`
  * :20 from `stick_diagram` -- load_topology->SD유지, geometry_colocation_union->SD유지, find_min_crossover_layout->SD유지, build_stick_diagram->SD유지, check_walk_sequence->SD유지, _dc_replace->EXT:dataclasses.replace, audit_row_split->SD유지 [판단] -- 비엔진/미정의: _dc_replace=EXT:dataclasses.replace
* `workspaces/current-reuse-telescopic-ota-report/stick.py`
  * :9 from `stick_diagram` -- Transistor->SD유지, search_shared_finger_w->SD유지, search_stack_finger_w->SD유지, check_box_shape->SD유지, build_stick_diagram->SD유지, find_matching_candidates->SD유지, find_hub_merge_candidates->SD유지, check_mirror_symmetry->SD유지, build_mirror_symmetric_pattern->SD유지, run_full_circuit_audit->SD유지, block_from_row_widths->UNDEFINED, pack_floorplan_grouped->SD유지, audit_row_split->SD유지, check_stick_diagram_coverage->SD유지, save_instance_json->instance_report_builder [판단] -- 비엔진/미정의: block_from_row_widths=UNDEFINED

#### F1-변경없음 (14파일)

* `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_lib_p3.py`
  * :16 import `stick_diagram` -- alias=sd [변경없음(SD 잔류 이름만)]
    * 속성: load_topology->SD유지(66), run_topology_pipeline->SD유지(79)
* `A/topology_to_markdown.py`
  * :29 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/probe_l3_groups.py`
  * :7 from `stick_diagram` -- load_topology->SD유지, geometry_colocation_union->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/stage1_cmrr_ngspice_crosscheck.py`
  * :30 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/stage1_cmrr_sympy_derivation.py`
  * :44 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/stage1_psrr_ngspice_crosscheck.py`
  * :24 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/stage1_psrr_sympy_derivation.py`
  * :39 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/stage2_battery_psrr_ngspice_crosscheck.py`
  * :19 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/stage2_battery_psrr_sympy_derivation.py`
  * :43 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/stage2_dump_exact_forms.py`
  * :14 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/stage2_numeric_mna_validate.py`
  * :20 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/stage2_rout_parallel_conjecture_check.py`
  * :19 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/stage3_full_circuit_ngspice_crosscheck.py`
  * :18 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]
* `workspaces/current-reuse-telescopic-ota-report/spice/vg15_vop1_kcl_sympy_derivation.py`
  * :38 from `stick_diagram` -- load_topology->SD유지 [변경없음(SD/ACF 잔류 이름)]

#### F1-D-9 제외(고치지 않음) (15파일)

`.ai/verification/20260930-b26-pre-test-strengthen/scripts/v4_oracle.py`, `.ai/verification/20260930-b34-grammar-explicit/scripts/c7_digest.py`, `.ai/verification/20260930-b34-grammar-explicit/scripts/discrim_b34.py`, `.ai/verification/20260930-b34-grammar-explicit/scripts/e_lib.py`, `.ai/verification/20260930-d-move-tests/scripts/e_lib.py`, `.ai/verification/20260930-df35-harness-paths/scripts/e_lib.py`, `.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py`, `.ai/verification/20260930-df36-instance-relpath/scripts/e_lib_inst.py`, `.ai/verification/20260930-dup-w-calc/scripts/e_lib.py`, `.ai/verification/20260930-p9-kcl-edges/scripts/diff_dup.py`, `.ai/verification/20260930-p9-kcl-edges/scripts/e_lib.py`, `.ai/verification/20260930-restore-plan-functions/scripts/e_lib.py`, `.ai/verification/20261001-b26-backfill-interdig-final-audit/scripts/order7/contract2.py`, `.ai/verification/20261001-b26-backfill-interdig-final-audit/scripts/order7/einst.py`, `docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition.py`

