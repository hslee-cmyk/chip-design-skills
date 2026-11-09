# B33 준비 -- V7 호출 그래프 간선 누락 (2026-09-30)

읽기 전용 조사. 저장소·worktree에는 쓰지 않았다. scratch는 `C:/g28`(끝나면 삭제). 측정 기준 = 저장소 `HEAD` `cd64170`,
게이트 코드 `tools/gates/reachability.py`를 `sys.path`로 import해 그대로 호출(`read_tree`·`build_graph`·`reach`·`_approved_ids`).
변형 그래프는 scratch `C:/g28/ext.py`(게이트 `build_graph` 사본 + 규칙 스위치)로 쟀다. **아래 수치는 준비용 실측이고, 판정 기록 수치가 아니다**
(작성자≠검증자: card에서는 auditor가 다시 잰다).

---

## 0. 요약

* HEAD에서 운영 루트(`gate_config.json` 두 벌 합집합, head에 파일이 있는 4개)로 도달하지 못하는 소스 분류 def = **115개**
  (백로그의 109 = 엔진 4파일 `sizing_recipe`·`stick_diagram`·`topology_library`·`design_report`만 센 값, `p3v2_g1_measure.py` G2. 나머지 6 = `audit_current_forced.py` 4 + `run_harness.py` 2).
* 115개 분류: **dict 레지스트리 경유 74**(레지스트리 값 직접 38 + 그 값이 부르는 함수 36), **클래스 생성자 3**, **운영 경로 밖 38**(test 전용 20 · workspace 스크립트/probe 전용 4 ·
  루트 아닌 CLI 4 · 앞 셋만 부르는 하위 함수 10). getattr 경유 0, 호출 0건 사망 코드 0, topology.json 문자열 레지스트리 경유는 dict 레지스트리 74 안에 포함(아래 1.3).
* **새로 찾은 결함(반대 방향, 거짓 PASS)**: 이름·속성 폴백(`by_name`)이 운영 파일에서 `tests/`·`workspaces/*` 스크립트의 같은 이름 def로 간선을 만든다. HEAD에서 운영 루트가
  **비운영 노드 64개**에 닿고, 그 경로로 `sizing_recipe.size_transistor`(호출자는 test·probe·workspace 스크립트뿐)가 '도달'로 셈해진다
  (`_solve_vgs` → 속성 `.size` → `workspaces/.../resize.py::size` → `size_transistor`). 같은 누수 때문에 거친 import 규칙을 넣으면 **면제 승인 대상 2개가 거짓으로 '도달'**이 된다(1.4).
* 스펙 판단: 레지스트리 간선은 계획 121행 '운영 경로'와 design 05 §10 V7 행이 **이미 요구한다 → 게이트 결함**. 생성자 간선은 '정적 호출 그래프'의 정의에 들어간다(생성자 호출도 호출) →
  게이트 결함이지만 문구가 명시적이지 않아 design 05 §10 V7 행에 한 줄 명확화가 필요. 비운영 파일 누수 차단은 '운영 경로' 정의에 맞추는 **강화**.
* 제안 규칙 3개(R1 레지스트리 바인딩, R2 생성자, R3 운영 범위) 적용 시 HEAD 미도달 115 → **39**(= 운영 경로 밖 38 + 누수로 가려졌던 `size_transistor` 1). 두 벌(`before_phase3`·`after_phase3`) 모두 39.
* V7 면제 승인 `20260930-restore-unwired-until-6a`(2 id)는 **계속 필요**(둘 다 test 전용). 다른 decision 승인은 V7 대상이 아니다.
* 부작용: `build_graph`는 V3 인벤토리와 공유 -- 인벤토리 (def, test) 쌍 33,991 → 79,809(2.35배), 인벤토리 0인 def 82 → 14. V3 실행 시간 증가 측정이 card 조건.
* 권장: 게이트 변경 card 1건(red-green, `gate_change: yes`, 승인 기록), **B28 뒤·G1 앞**(G1의 차단 조건은 아니다). 이유는 §5.

---

## 1. HEAD 재현과 분류 (과제 1)

### 1.1 재현 방법

```
PYTHONPATH=tools/gates  (scratch: C:/g28/repro.py)
head   = read_tree(repo, "HEAD", GRAPH_PREFIXES)      # A/ 전체 + workspaces/ 전체 .py
nodes, edges = build_graph(head)
roots  = gate_config 두 벌 합집합 중 head에 파일 있는 것
         = run_harness.py::run, run_harness.py::__main__, sky130_lut_sweep.py::__main__, topology_to_markdown.py::__main__
         (gmid_design_pipeline.py::run_gmid_design_pipeline 은 파일 없음 -- 게이트 DESIGN-GAP 주석과 같은 처리)
src    = _is_source 파일(A/*.py 7개 + workspaces/run_harness.py)의 def 494개
미도달 = src - reach(edges, roots) = 115
```

두 벌 따로: `before_phase3` 115, `after_phase3` 121(후 벌은 `run_harness::__main__`이 없어 `run_harness` 모듈 최상위를 못 거친다).
게이트 V7은 합집합을 쓰므로 115가 게이트 동작 그대로다. 결과 파일: `C:/g28/repro.json`(삭제 예정 -- 목록은 아래에 전부 옮김).

### 1.2 왜 빠지나 (게이트 코드 근거)

* `build_graph`의 노드는 def·`<module>`·`__main__`뿐이고, `<module>`로 가는 간선은 **같은 파일의 `__main__`에서만** 있다(`edges[__main__] |= {<module>}`).
  `import`·`from M import` 문장은 `_refs`에서 아무 참조도 만들지 않는다(`ast.alias`는 `Name`이 아님). → 루트가 import하는 모듈의 최상위 코드(레지스트리 dict 리터럴)가 도달 집합에 안 들어온다.
* 레지스트리를 **읽는** 함수(`compute_metric`의 `_METRICS_REGISTRY.get(...)`, `_build_theta_evaluator._evaluate`의 `_COMPENSATION_REGISTRY[comp["function"]]`,
  `apply_theta_feed`의 `_THETA_FEED_REGISTRY.get(...)`)는 도달하지만, 이름 `_METRICS_REGISTRY`가 def가 아니라서 `resolve`가 빈 집합을 준다.
* 클래스는 노드가 아니고 `by_name` 색인 키는 qualname 마지막 조각(`__init__`)이다. `Cls(...)`의 이름 `Cls`는 어느 def와도 안 맞는다 → `Cls.__init__` 간선 없음.
* 반대 방향: 이름·속성 폴백 `by_name.get(v)`는 파일 범위가 없다. `x.size`(numpy 속성)·`run`·`_rel`·`W` 같은 흔한 이름이 test·probe·workspace 스크립트의 def로 간선을 만든다.

### 1.3 분류표 (115개)

분류 방법: 규칙을 하나씩 켠 변형 그래프에서 도달로 바뀌는지(1차), 남은 것은 전 그래프 역방향 선행 노드의 파일 종류(2차). 경로 표본은 BFS 부모 사슬로 확인
(`C:/g28/why.py`). 경로는 `A/` = `skills/analog-gmid-design/assets/` 생략.

**(a) 클래스 생성자 경유 -- 3**

| def | 도달 경로(규칙 R2 적용 시) |
|---|---|
| `sizing_recipe.py::SemiEmpiricalGmIdLUT.__init__` | `run_harness::__main__` → `run_harness::<module>`(모듈 최상위 `SemiEmpiricalGmIdLUT(...)` 호출) → `__init__` |
| `sizing_recipe.py::InfeasibleSizingError.__init__` | `_build_theta_evaluator` 등 8곳의 `raise InfeasibleSizingError(...)` |
| `stick_diagram.py::Transistor.__post_init__` | `@dataclass Transistor(...)` 호출 84곳 |

엔진에 있는 dunder는 이 셋뿐이다(`grep "def __"` → `sizing_recipe.py:274·6451`, `stick_diagram.py:74`). `__repr__`·`__eq__`·`__call__` 같은 암묵 호출 dunder는 HEAD에 없다.

**(b) dict 레지스트리 경유 -- 74 (직접 값 38 + 하위 36)**

레지스트리(모듈 최상위 `NAME = {…}` 바인딩)와 그 값:

| 레지스트리(행) | 값(미도달이던 def) | 읽는 곳(도달함) |
|---|---|---|
| `_COMPENSATION_REGISTRY`(sizing_recipe 1416) | `topology_library.py::{miller_ota_topology, nmcnr_3stage_topology, ngcc_3stage_topology, current_reuse_telescopic_topology}` 4 | `_build_theta_evaluator._evaluate`(8182·8187) |
| `_THETA_FEED_REGISTRY`(6268, 값은 `FeedHandler(_feed_*, …)`) | `_feed_settling_split, _feed_diode_stack_target, _feed_gm_target_convention, _feed_root_ratio, _feed_root_const, _feed_root_signed_sum, _feed_metric_stage_budget, _feed_l_class` 8 | `apply_theta_feed`(6289) |
| `_METRICS_REGISTRY`(5083) | `_metric_*` 23개(sum_current, sum_area, gain_stages_sum, folded_cascode_gain_db/pm_deg, nmcnr_gain_db/pm_deg, flicker_plus_thermal_sum, pelgrom_mismatch, input_referred_offset, cmrr_estimate, psrr_estimate, supply_current, kcl_residual, parasitic_pm_deg, stack_headroom_slack, mirror_ratio_error, mirror_ratio_error_input_referred, rail_referenced_voltage, battery_centering_deviation, nulling_resistor_ohm, smallsignal_ratio_db, smallsignal_gain_db) | `compute_metric`(5286) |
| `_CMRR_ESTIMATOR_REGISTRY`(4760) / `_PSRR_ESTIMATOR_REGISTRY`(4777) | `_cmrr_diff_pair_tail`, `_psrr_diff_pair_tail` 2 | 5063·5075 |
| `_CONSTRAINT_OPS`(6418, 값이 lambda) | `_constraint_tol` 1 | 제약 판정부 |

하위 36(위 값이 부르는 함수·중첩 함수): `SemiEmpiricalGmIdLUT.noise_1f_density`, `_device_roles_cached`, `_feed_root_ratio._ref_id`, `_feed_root_signed_sum._ref_id`,
`_folded_cascode_rout`, `_full_circuit_devices`, `_full_circuit_response`, `_hashable_key`, `_ideal_sources_cached`, `_metric_parasitic_pm_deg._h`,
`_metric_smallsignal_ratio_db.sense`, `_mirror_ratio_aggregate`, `_mirror_ratio_error_pairs`, `_mna_solve_smallsignal`, `_mna_stamp_capacitance`, `_nmcnr_predict`,
`_nmcnr_stage1_rout`, `_resolve_capacitor_farad`, `_resolve_nulling_resistor_ohm`, `_run_shared_current_joint_scan`, `_vgs_root`, `build_ac_network`, `diode_vds_cached`,
`full_circuit_response_at_omega`, `resolve_feed_vds`, `solve_id_for_target_gm`(+`._gm_at`), `stack_kvl_vgs_limit`(+`._depends_on_name`·`._known_vds`·`._min_need`), `vgs_alias_map`
(이상 sizing_recipe), `topology_library.py::{nmcnr_check_dominant_pole_approximation, nmcnr_compensation_elements, nmcnr_predict_ac_response, nmcnr_predict_ac_response._H}`.

**topology.json 문자열 레지스트리**: library JSON의 `"function"` 값은 3개(`miller_ota_topology`·`nmcnr_3stage_topology`·`current_reuse_telescopic_topology`),
`ngcc_3stage_ff`는 `"compensation": null`. JSON 문자열은 `_COMPENSATION_REGISTRY`의 **키**로만 코드에 닿는다(`eval`/`getattr(module, name)` 금지 주석 1414~1415행).
그래서 'topology.json 경유'는 dict 레지스트리 경유의 부분집합이고 별도 간선 규칙이 필요 없다. metric·feed의 JSON `"type"` 값(`"A"`, `"sum_current"` …)도 레지스트리 키다.

**(c) getattr 경유 -- 0**. 엔진의 `getattr(`은 전부 속성 읽기(`"stage_fT_targets"`, `"VDS_grid"`, `"topology_path"`, `"files"`, `"exposed_params"`)이고 함수 디스패치가 없다.

**(d) 운영 경로 밖 -- 38 (규칙을 넣어도 미도달로 남아야 하는 것)**

| 하위 분류 | def |
|---|---|
| test 전용 20 (선행 노드가 `A/tests/**`뿐) | `sizing_recipe`: `achievable_metric_bound`, `estimate_area_budget`, `load_derived_bounds`, **`lut_conditions_from_npz`(면제 승인)**, `node_pole_estimate`, `signal_path_nodes`, `solve_diode_stack_current`, `validate_theta_declaration_order`; `stick_diagram`: `apply_device_roles_gap_fill`, `apply_theta_kcl_gap_fill`, `audit_theta_root_direction`, `audit_vertical_stack_id_euler_feasibility`, `check_multi_leaf_hub_parity`, `find_differential_and_mirror_forks`, `find_diode_stacks`, `find_euler_repair_options`, `folded_cascode_example`, `propose_theta_kcl_gap_fill`, `two_stage_ota_example`; `run_harness`: **`derived_spec`(면제 승인)** |
| test·probe·workspace 스크립트 전용 4 | `sizing_recipe::build_toy_lut`(tests/conftest·probe·`workspaces/.../probe_group_split_wiring.py`), `stick_diagram::check_mirror_symmetry`(tests·`workspaces/.../stick.py`), `stick_diagram::search_shared_finger_w`(`workspaces/.../stick.py`만), `run_harness::canonical_spec`(probe 38곳 + `derived_spec`) |
| 루트 아닌 CLI 4 | `audit_current_forced.py::{render_report ← __main__, audit_topology, _theta_evidence_for_pair, _as_set}` -- `audit_current_forced.py::__main__`은 `reachability_roots`에 없다 |
| 위 것만 부르는 하위 10 | `_invq_newton`(← build_toy_lut), `derived_bounds_path`(← load_derived_bounds), `signal_path_nodes._reach`, `solve_diode_stack_current._vgs_sum`, `_kcl_terminal_sign`, `find_differential_and_mirror_forks._classify_forks`·`._forks_of`, `find_idiom_matches`(← audit_theta_root_direction·propose_theta_kcl_gap_fill), `propose_theta_kcl_gap_fill._mark`·`._run_rules_1_to_3` |

레지스트리 등급과 대조(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`): `lut_conditions_from_npz`·`derived_spec` "보류(Phase 6a)" + 면제 승인,
`find_euler_repair_options` "보류(Phase 4) 배선 승인 필요, 운영 0", `propose_theta_kcl_gap_fill` "보류(Phase 3) 배선 승인 필요, 운영 호출 0". 즉 (d)는 계획이 이미 '미배선'으로
관리하는 집합이다. 이 def들은 **기존 def라 지금 V7 FAIL을 내지 않는다**(V7은 새 def만 본다) -- 옮기며 바뀌거나 새로 생길 때만 문제가 된다.

**(e) 누수로 가려진 것 -- 1 (지금 '도달'로 잘못 셈)**: `sizing_recipe.py::size_transistor`. 호출자는 tests 11곳·probe·`workspaces/.../resize.py::size`·
`probe_group_split_wiring.py`뿐. 도달 사슬 `run → optimize_full_circuit_budget → _build_theta_evaluator._evaluate → SemiEmpiricalGmIdLUT.vgs_for_gm_id → _solve_vgs →
(속성 .size) workspaces/current-reuse-telescopic-ota-report/resize.py::size → size_transistor`.

### 1.4 누수 실측 (현 게이트의 거짓 PASS 면)

HEAD 원 그래프에서 운영 루트가 닿는 **비운영 노드 64개**(표본): `tests/contracts/test_d_delete_dead.py::_rel`(← `stick_diagram._topology_ref_relpath`의 `_rel` 이름 폴백),
`tests/probes/probe_diode_window_corner.py::run`(← `sky130_lut_sweep._run_combo`의 `run`), `tests/probes/probe_allocation_solvers.py::table`, `tests/tools/reg_check.py::check`,
`workspaces/current-reuse-telescopic-ota-report/stick.py::W`(← `optimize_full_circuit_budget`의 `W`) …

이 누수가 거친 규칙과 결합하면 약화가 된다. 'import하면 그 모듈 최상위 전체가 도달' 규칙(아래 R0)만 넣은 변형에서 **면제 승인 대상 두 개가 '도달'로 바뀐다**:
`run → save_instance_json → _topology_ref_relpath → tests/contracts/test_d_delete_dead.py::_rel → test_d_delete_dead.py::<module>(_RESTORED_NAMES 문자열) → lut_conditions_from_npz / derived_spec`.
즉 test 파일 최상위의 문자열 상수가 엔진 def를 '배선'한 것으로 셈된다 -- R3(운영 범위)가 필요한 직접 증거.

---

## 2. 스펙 원문과 판단 (과제 2)

**계획 N4.2 V7 행**(`docs/01-plan/features/gain-budget-gmid-sizing.plan.md` 843행):

> | V7 | 배선 | 새 def가 운영 경로에서 도달하는지(루트 목록은 설정 파일, Phase 3 전·후 두 벌). 도달 못 하면 레지스트리 등급 D 기록 + 승인 기록 | `tools/gates/reachability.py` | 2 |

**계획 용어표 '운영 경로'**(같은 파일 121행):

> | 운영 경로 | Phase 3 전: `workspaces/run_harness.py` -> `optimize_full_circuit_budget` -> `_evaluate`. Phase 3 후: `run_gmid_design_pipeline` 이하. 문자열 레지스트리(`_METRICS_REGISTRY`, `_COMPENSATION_REGISTRY`, topology.json `"function"`)로 도달하는 것 포함 |

**design 05 §10 V7 행**(`docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md` 321행):

> | `reachability.py`(V7) | 배선 | 새 `def`가 `gate_config.json`의 `reachability_roots`에서 정적 호출 그래프(문자열 레지스트리 포함)로 도달하는지 |

(같은 절 338행: "거부 증명: … V7 → `redteam/v7_unwired`". 317행 V3 ③: "인벤토리 = 정적 호출 그래프(V7과 같은 그래프)".)

게이트 docstring은 '문자열 레지스트리'를 "def 이름과 같은 문자열 상수" 간선으로 구현했다. 이것은 키가 함수 이름과 같은 `_COMPENSATION_REGISTRY`만 부분적으로 덮고(그것도 레지스트리가 있는
모듈 최상위가 도달해야 의미가 있는데 도달하지 않는다), 키가 `"A"`·`"sum_current"`인 `_THETA_FEED_REGISTRY`·`_METRICS_REGISTRY`는 못 덮는다.

| 누락 | 스펙이 요구하나 | 판단 |
|---|---|---|
| 레지스트리 dict → 값 함수 | **예**. 121행이 `_METRICS_REGISTRY`·`_COMPENSATION_REGISTRY`·topology.json `"function"`을 이름으로 들어 '운영 경로에 포함'이라 하고, §10이 "문자열 레지스트리 포함"이라 한다. HEAD에서 이 셋의 값 27개(+feed 8·CMRR/PSRR 2·`_CONSTRAINT_OPS` 1)와 하위 36개가 미도달 | **게이트 결함**(스펙 불일치). 스펙 문구 변경 불필요 |
| 클래스 인스턴스화 → `__init__`/`__post_init__` | 문구로 명시는 없다. '정적 호출 그래프'의 표준 정의에서 `Cls(...)`는 `Cls.__init__`(dataclass면 생성된 `__init__` → `__post_init__`) 호출이다. 운영 경로가 실제로 `SemiEmpiricalGmIdLUT(...)`·`Transistor(...)`·`raise InfeasibleSizingError(...)`로 이 셋을 실행한다 | **게이트 결함**(호출 그래프 정의 미구현). 다만 문구가 명시적이지 않으므로 §10 V7 행에 규칙을 적는 **명확화**가 필요(판정 문구 개정 = 승인 대상) |
| 비운영 파일로의 이름 폴백 누수 | 121행 '운영 경로'는 run_harness·엔진 호출 사슬이다. test·probe·workspace 조사 스크립트는 운영 경로가 아니다 | **게이트 결함**(거짓 PASS, 강화 방향). 스펙 문구 변경 불필요, §10 행에 범위를 적는 명확화 권장 |
| topology.json `"function"` 직접 읽기 | 121행이 포함을 요구하지만, JSON 문자열은 레지스트리 키로만 코드에 닿으므로 레지스트리 규칙이 이미 덮는다(1.3) | 별도 규칙 **불필요**. 게이트가 JSON을 읽으면 topology 의존이 생긴다(G1 계약 7 '회로 무관'과 같은 원칙 위반) |
| getattr 디스패치 | 스펙 언급 없음, HEAD 0건 | 범위 밖(규칙 만들지 않는다) |

결론: 이 card는 **스펙 확장이 아니라 게이트를 스펙에 맞추는 수정**이다. design 05 §10 V7 행에 그래프 규칙을 한 줄 명시하는 명확화가 같이 필요하다(승인 기록 범위에 포함).

---

## 3. 최소 간선 규칙 (과제 3)

원칙: **간선은 도달 가능한 코드에 그 참조가 문법적으로 있을 때만** 만든다. 기존 그래프의 과대 근사 성격(이름 참조 = 간선, 콜백 전달 포함)은 유지하되,
새 규칙이 '참조가 없는 def'를 도달로 만들지 않게 한다. 각 규칙의 HEAD 효과는 규칙을 하나씩 켠 변형에서 잰 값(합집합 루트, R3 적용 여부 표기).

### R1 레지스트리 바인딩 노드 (dict 레지스트리 → 값)

* 노드 추가: 모듈 최상위의 `NAME = <식>` / `NAME: T = <식>`(타깃이 전부 단순 `Name`)마다 `<파일>::=NAME`.
* 간선: 바인딩 노드 → `resolve(_refs(<식>))`(dict·list·tuple·`FeedHandler(...)` 호출·lambda 본문의 이름 참조 전부 -- 기존 `_refs` 그대로).
* 참조 해석: 도달 가능한 노드 몸체의 `Name` Load `NAME` → 같은 파일 바인딩, 없으면 `from M import NAME`의 M 바인딩, `M.NAME`(모듈 별칭 속성) → M 바인딩.
  **Phase 3 재수출 대비**: `(M, NAME)` 바인딩이 없으면(M이 다시 import해 재수출) 기존 def 규칙처럼 같은 이름의 바인딩 전체로 폴백(`by_mod` 없으면 `by_name`과 같은 모양). 단 R3 범위 안에서만.
* 모듈 최상위의 나머지(바인딩이 아닌 문장)는 지금처럼 `<module>` 노드에 둔다. **import 문장 → 대상 `<module>` 간선(R0)은 넣지 않는다**(아래 반례 3).
* HEAD 효과: 미도달 115 → 42(R1+R3) / 40(R1만). 레지스트리 값 38 + 하위 36 = 74개가 도달.

반례 검토:
1. 등록만 하고 아무도 읽지 않는 레지스트리 `_ORPHAN = {"c": _f_c}` → 바인딩 노드에 들어오는 간선이 없으니 `_f_c` 미도달 유지(FAIL). **redteam 거부 단계로 고정**.
2. 레지스트리를 dead code만 읽음 → 미도달 유지.
3. (거절한 대안 R0) "import하면 모듈 최상위 전체 도달": 레지스트리를 읽지 않아도 등록만으로 도달이 되고(반례 1을 통과시킴), 1.4의 누수와 합쳐 면제 대상 2개를 거짓 도달시킨다 → **약화**. HEAD에서 R1+R2+R3에 R0를 더해도 추가 도달 0이라 이득도 없다.
4. (거절한 대안) "topology.json 키에 있는 항목만 도달": `_THETA_FEED_REGISTRY`의 `"l_class"`·`"settling_split"`은 JSON에 없고 코드(`synthesize_l_class_thetas`)가 키를 만든다 → 거짓 FAIL. 게이트의 회로 무관 원칙 위반.
5. 알려진 과대 근사(기존 def 규칙과 같은 수준): 함수 지역변수·인자가 모듈 바인딩과 같은 이름이면 그 Load가 바인딩으로 해석된다. 같은 이름 def 폴백과 같은 성격이라 이번 범위 밖으로 기록.
6. 범위 밖(HEAD 0건, 기록만): 데코레이터 등록(`@register`), 최상위 `REG["k"] = f`/`REG.update(...)`, 클래스 본문 속성 레지스트리. `grep`으로 엔진에 없음 확인(최상위 데코레이터는 `@functools.lru_cache` 1건).

### R2 생성자 간선 (클래스 인스턴스화 → `__init__`·`__new__`·`__post_init__`)

* 간선: 도달 가능한 노드 몸체의 **호출 위치** `Cls(...)`(`Name`/`from M import Cls`/`M.Cls`로 해석) 또는 `raise Cls` → 그 클래스의 `__init__`·`__new__`·`__post_init__` def,
  그리고 그 클래스에 없으면 **기반 클래스**(클래스 정의의 bases 이름으로 해석, 재귀)의 같은 dunder.
* HEAD 효과: 3개 도달(115 → 112 단독). `SemiEmpiricalGmIdLUT(GmIdLUT)`는 자기 `__init__`이 있다.

반례 검토:
1. `isinstance(x, Cls)`·`except Cls:`·타입 주석에만 나오는 클래스 → 생성자 미도달 유지(인스턴스가 안 만들어진다). **redteam 거부 단계로 고정**.
2. 팩토리로 넘김(`defaultdict(Cls)`, `{"k": Cls}`) → 호출 위치가 아니라 간선 없음 → 거짓 FAIL 쪽(엄격). 필요하면 decision 승인. 대안 'Name 참조 전부' 규칙(함수 콜백 규칙과 대칭)은 HEAD에서 결과가 같다(35 = 35) -- 엄격한 쪽을 기본으로 제안하고, 대칭안을 승인 질문의 선택지로 둔다.
3. `cls(...)`(classmethod)·`type(self)(...)` → 해석 불가, 간선 없음(엄격). HEAD 0건.
4. 이미 있는 과대 근사: 속성 `x.__init__`/`super().__init__()`는 기존 `attr` 규칙으로 **모든** `__init__`에 간선을 만든다. HEAD 운영 경로에 0건이라 지금은 무해. 이번 card에서 바꾸지 않고 기록.
5. 암묵 dunder(`__repr__`·`__eq__`·`__hash__`·`__call__`·`__enter__`…)는 문법적 참조가 없으므로 간선을 만들지 않는다(HEAD 0건).

### R3 운영 범위 (V7 도달 계산만)

* V7 `main`의 도달 계산에서 **소스 분류 파일(`_is_source`) 노드만 따라간다**(루트 파일은 전부 소스 분류). `build_graph` 자체는 바꾸지 않는다 -- V3 인벤토리는 test 노드에서 출발해야 하므로.
* 근거: 엔진 파일이 test·probe·workspace 스크립트를 import하는 곳 0건(`grep` 확인: 엔진 내부 import는 엔진끼리뿐, `stick_diagram._import_analog_grammar`는 그래프 밖 `analog-grammar`).
  그래서 운영 경로가 비운영 파일을 경유해야만 닿는 def는 실제로 존재하지 않는다 -- 이 제한은 거짓 FAIL을 만들지 않고 폴백 누수만 끊는다.
* HEAD 효과: 원 그래프에서 116(= 115 + `size_transistor`). R1+R2와 합쳐 **39**.

반례 검토:
1. 누수 재현: 엔진이 속성 `.size`를 쓰고, 새 엔진 def `g`를 `tests/probes/p.py::size`만 부른다 → 지금 게이트 exit 0(거짓 PASS), R3 후 exit 1. **redteam red 단계**.
2. test 파일 최상위 문자열(`_RESTORED_NAMES`)이 엔진 def 이름과 같음 → R3 후 영향 없음(1.4 경로 차단).
3. Phase 3 뒤 새 운영 모듈이 `A/` 바로 아래가 아니면 `_is_source`(`p.count("/") == 3`)에서 빠져 R3가 거짓 FAIL을 낸다. Phase 3 design v2의 목적지 파일은 `A/` 바로 아래라 해당 없음 -- card 계약에 "운영 범위 = `_is_source`와 같은 판정식(정의 하나)"을 적어 두면 목적지 규칙이 바뀔 때 함께 따라간다.

### 규칙 조합 실측 (HEAD, 합집합 루트, 소스 분류 def 494)

| 변형 | R3 없음 | R3 있음 |
|---|---|---|
| 현 게이트 | 115 | 116 |
| R2만 | 112 | 113 |
| R1만 | 40 | 42 |
| R1+R2 (**제안**) | 37 | **39** |
| R0(import→최상위 전체)만 | 36 | 42 |
| R0+R1+R2 | 35 | 39 |

R3 없는 열이 더 작은 것은 전부 누수 효과(가짜 도달)다. 제안안 39 = 1.3 (d) 38 + (e) 1. 두 벌(`before_phase3`/`after_phase3`) 각각도 39.

---

## 4. Phase 3 이동(G1)과 면제 승인과의 관계 (과제 4)

### 4.1 G1(`_drafts/draft_p3_g1.spec.md`, `20260930-p3-gate-move-aware`)

* 겹치는 파일: 둘 다 `tools/gates/reachability.py`. G1은 `moved_defs`·`def_hash` 추가와 `main`의 `new_defs` 선택, B33은 `_refs`/`build_graph`(R1·R2)와 `main`의 도달 계산(R3).
  함수 단위로 겹치지 않지만 같은 파일이라 **순서를 정해야** 한다(test worktree base, '작성 전 실측' 줄 번호).
* 판정 효과가 독립이다: G1은 "무엇이 새 def인가", B33은 "무엇이 도달하는가". G1의 이동 판정(M-1~M-3 해시)은 그래프와 무관하다.
* B33 없이 G1만 있으면: 바이트 그대로 옮긴 def는 V7이 보지 않으니 문제없다. 그러나 (i) 옮기며 바뀐 def·Phase 3에서 새로 생기는 def(파사드·`run_gmid_design_pipeline` 하위 등)가
  레지스트리·생성자로만 닿으면 **거짓 FAIL**(매 card decision 승인 잡음), (ii) test 전용 def가 흔한 이름 폴백으로 **거짓 PASS**(R3 누수) -- Phase 3에서 파일이 쪼개지며 같은 이름 def가 늘수록 누수 면이 커진다.
* B33이 먼저면: G1 design v2 §5·부록 A G2의 'V7 미도달 108/109'는 엔진 4파일 기준 **33**으로 바뀐다(39 − audit_current_forced 4 − run_harness 2). G1의 V7 부분은 여전히 필요하다(그 33개 --
  test 전용·보류 def -- 를 옮기면 새 def 미도달). G1 계약 9(무동작 redteam 목록)에 B33의 새 케이스를 더한다.
* R1의 재수출 폴백은 Phase 3에서 레지스트리가 새 모듈로 옮겨지고 옛 모듈이 `from 새모듈 import _METRICS_REGISTRY`로 재수출하는 모양을 위해 필요하다. 없으면 이동 뒤 레지스트리 값이 다시 미도달이 된다.
* after_phase3 루트 벌(`gmid_design_pipeline.py::run_gmid_design_pipeline` 단독, `run_harness::__main__` 없음): R2가 모듈 최상위 생성자 호출(`run_harness::<module>`의 `SemiEmpiricalGmIdLUT(...)`)에 기대지
  않도록, 파이프라인이 LUT를 만드는 호출이 자기 몸체에 있으면 도달한다. 현 HEAD 후 벌 실측도 39이고 미도달 **집합**이 전 벌·합집합과 같다(집합 비교 True).

### 4.2 V3 인벤토리 부작용 (공유 그래프)

`mutate_changed.py` 279행이 `rch.build_graph(head_files)`를 그대로 쓰고 177행 `reach(graph_edges, [test])`로 인벤토리를 만든다. R1·R2는 `build_graph`를 바꾸므로 V3도 바뀐다(R3는 V7 `main`에만 둔다).

| 측정(HEAD, test 함수 454개) | 현 그래프 | R1+R2 |
|---|---|---|
| (소스 def, 도달하는 test) 쌍 | 33,991 | 79,809 (2.35배) |
| 인벤토리 0인 소스 def | 82 | 14 |

* 방향: 인벤토리 0이던 레지스트리 값(`_metric_*`·`_feed_*` 등)은 지금 V3에서 '인벤토리 없음 → 생존 → FAIL'이 된다(거짓 FAIL). R1·R2 뒤에는 `compute_metric`을 거치는 test가 인벤토리가 된다.
  변이를 죽이는 것은 그 test의 실제 실패뿐이라 **약화가 아니다**(도달이 과대여도 kill 증거는 실행 결과).
* 비용: 변이당 실행하는 test 수가 늘어 V3 시간이 늘어난다. card에서 auditor가 최근 판정 기록 1건(예 `20260930-dup-w-calc`)의 V3를 base 도구·병합본 도구로 재서 시간·kill 수를 기록하게 한다(NFR-2).
  선택지: V3는 옛 그래프를 유지(스펙 '같은 그래프' 위반 → 문구 개정 필요)하는 대안은 권하지 않는다.

### 4.3 V7 면제 승인(`.ai/approvals/*.md`, `target_kind: decision`)

HEAD의 decision 승인 11건 중 V7 def id를 target으로 가진 것은 1건이다.

| 승인 | target | 제안 규칙 후 | 판단 |
|---|---|---|---|
| `20260930-restore-unwired-until-6a` | `sizing_recipe.py::lut_conditions_from_npz`, `workspaces/run_harness.py::derived_spec` | 둘 다 미도달 유지(test 전용, 1.3 (d)) | **계속 필요**. 재검토 조건(6a S0 배선·spec 변형 첫 사용처) 그대로 |
| 나머지 10건 | `U-38`·`F4`·`U-01`·`U-39`·`C2-E4`·`C9-IC11-SPLIT`·`U-02`(결정 id), `20260922-ic3-v3-exempt`(V3 변이 id 14), `20260923-c9-v4-exempt`(V4 test id 2), `20260929-p4-scan-exempt`(`probe_mirror_gain_ranking.py::lut-private`) | V7 판정과 무관 | 영향 없음 |

주의: R0(거친 import 규칙)나 R3 없는 R1이면 위 두 id가 누수로 '도달'이 되어 면제가 **불필요해 보이게** 된다 -- 그건 배선이 아니라 누수이므로 승인을 지우면 안 된다(1.4).
제안안(R1+R2+R3)에서는 두 id 모두 미도달이라 이 함정이 없다.

과거 판정 기록의 V7 결과 무동작 미리보기: §6 참조.

---

## 5. card 모양 권고 (과제 5)

**id(안)**: `2026MMDD-v7-registry-ctor-scope`, `phase: 0.5`, `evidence_type: red-green`, `gate_change: yes`, 승인 기록 필요(게이트 변경 + design 05 §10 V7 행 문구 명확화).

**관찰 가능한 계약(초안)**

1. R1: 모듈 최상위 단순 이름 바인딩은 그래프 노드다. 도달 가능한 코드가 그 이름(같은 파일·`from M import`·`M.NAME`, 재수출이면 같은 이름 바인딩)을 참조하면 바인딩 값이 참조하는 def가 도달한다.
   참조가 없는 바인딩의 값은 도달하지 않는다.
2. R2: 도달 가능한 코드의 `Cls(...)`·`raise Cls`는 `Cls`(없으면 기반 클래스)의 `__init__`·`__new__`·`__post_init__`에 도달한다. 호출이 아닌 클래스 이름 참조(`isinstance`·`except`·주석)는 생성자에 도달하지 않는다.
3. R3: V7 도달 계산은 소스 분류(`_is_source`) 파일 노드만 따라간다. `build_graph`의 노드·간선 집합에서 비운영 파일 노드를 지우지 않는다(V3 인벤토리 유지).
4. import 문장은 대상 모듈 최상위 전체를 도달시키지 않는다(R0 배제).
5. 판정 JSON 형식·exit 규칙·면제(`_approved_ids`)는 그대로.
6. V3는 같은 `build_graph`를 쓴다(스펙 '같은 그래프') -- auditor가 인벤토리 변화와 실행 시간을 한 건에서 기록.
7. topology 무관: 게이트 소스에 회로·넷·소자 이름, `library/`·`.topology.json` 리터럴 없음. JSON을 읽지 않는다.
8. 재계산 없음: 바인딩·클래스 색인은 `build_graph` 한 번에 만든다(파일당 AST 1회 -- 지금과 같음).

**redteam 새 케이스** `tools/gates/redteam/attacks/<다음 번호>-v7-graph-edges/`(B28 31, G1 32 예정이면 그 다음 -- 병합 순서에 맞춰 `ls attacks`로 확정). 합성 저장소에 `workspaces/run_harness.py::run`을 둬서
실제 루트가 있게 한다(기존 `v7_unwired`는 루트 파일이 없어 무엇이든 미도달이라 green 단계를 만들 수 없다).

| 단계 | head 변경 | base 도구 | 새 도구 | 역할 |
|---|---|---|---|---|
| `registry-wired` | 새 `_f_b`를 `run`이 읽는 `_REG = {"b": _f_b}`에 등록 | exit 1 | exit 0 | red → green (R1) |
| `registry-orphan` | 새 `_f_c`를 아무도 안 읽는 `_ORPHAN`에만 등록 | exit 1 | exit 1 | 거부 (R1 반례 1) |
| `ctor-wired` | 새 클래스 `C.__init__`, `run`이 `C(...)` | exit 1 | exit 0 | red → green (R2) |
| `ctor-isinstance-only` | 새 클래스 `D.__init__`, `run`은 `isinstance(x, D)`만 | exit 1 | exit 1 | 거부 (R2 반례 1) |
| `leak-test-name` | 엔진 `run`이 `x.size` 속성 사용, 새 엔진 def `g`를 `A/tests/probes/p.py::size`만 호출 | **exit 0** | exit 1 | red(거짓 PASS) → green (R3) |
| `leak-test-string` | test 파일 최상위 `_NAMES = ("g",)`, 새 엔진 def `g` 호출 0 | exit 1 | exit 1 | 거부 (R0 배제·R3) |
| `approved-still-exempt` | `registry-orphan` + decision 승인 기록(`target` = `_f_c` id) | exit 0 | exit 0 | 면제 불변 |

oracle (a) 구성: 기대 exit는 위 계약 문장에서 정한다(피검 도구 출력으로 만들지 않는다).

**무동작 판정 입력**: 기존 `v7_unwired`·`v3_survivor`·`run_all.py --phase 0.5 --mode direct`·`--cases 0.5` 전 케이스 판정 불변. 최근 판정 기록들의 V7 base·head 쌍에서 판정 불변(§6 미리보기).
HEAD 전체 미도달 수(115 → 39)는 보고 수치로 auditor가 잰다(이 문서 수치는 인용 금지).

**작성 전 실측 항목(카드 작성 때 다시 잴 것)**: `grep -n "def _refs\|def build_graph\|def reach\|seen = reach" tools/gates/reachability.py`(지금 `_refs` 69·`build_graph` 97·`reach` 160·`_is_source` 175·`seen = reach` 223행),
`mutate_changed.py` 177·279행, `ls tools/gates/redteam/attacks`, 새 이름 충돌 `git grep -n "_is_source\|bind" -- tools/gates`.

**순서 권고: B28 → B33 → G1** (G1의 차단 조건은 아님)

* B33이 먼저인 이유: (1) R3가 막는 거짓 PASS는 지금 모든 card의 V7에 걸려 있는 게이트 약점이다. (2) Phase 3 M card는 파일을 쪼개 같은 이름 def를 늘리므로 누수 면이 커지고,
  편집 이동·새 파사드 def가 레지스트리·생성자로만 닿으면 매번 decision 승인 잡음이 된다. (3) G1의 design 수치(V7 미도달 108)와 무동작 목록을 B33 반영 base에서 한 번에 확정할 수 있다.
  (4) 변경이 `reachability.py` 한 파일 + redteam 1케이스로 작다.
* G1이 먼저여도 되는 이유: 판정 효과가 독립이고(4.1), G1의 이동 판정은 그래프와 무관하다. 일정상 G1을 먼저 하면 B33의 무동작 목록에 G1 케이스(32)를 넣고 B33 test worktree는 G1 병합 뒤 base에서 만든다.
* 비용 위험: V3 인벤토리 2.35배(4.2). B33 card의 auditor 판정에 V3 시간 측정 1건을 넣어 Phase 3 이후 card 처리 속도 영향을 미리 본다.

**승인 질문(사용자 몫)**: 게이트 변경 승인 + design 05 §10 V7 행 명확화 문구 -- 제안
"정적 호출 그래프 = 이름·속성 호출 + 모듈 최상위 바인딩(레지스트리) 참조 + 클래스 호출의 생성자. 도달 계산은 소스 분류 파일 안에서만." R2 선택지: 호출 위치만(기본, 엄격) / 이름 참조 전부(함수 콜백 규칙과 대칭).

---

## 6. 과거 판정 기록 V7 무동작 미리보기

방법: `.ai/verification/2026*.json` 중 V7 근거에 `reachability.py … --base X --head Y`가 있는 27건의 쌍마다 현 게이트(원 그래프, 합집합 루트)와 제안안(R1+R2+R3)으로
new_defs·미도달·면제 없는 미도달을 계산(scratch `C:/g28/noop.py`, 저장소 이력 커밋 직접 읽기, `gate_config.json`은 HEAD 것 -- 루트는 기록 당시와 같음). scratch는 삭제함.

결과: **27건 모두 판정 같음**(면제 없는 미도달 0 → 0).

| 기록 | new_defs | 미도달(현/제안) | 면제 없는 미도달(현/제안) |
|---|---|---|---|
| `20260922-ic3-completeness` | 2 | 0 / 0 | 0 / 0 |
| `20260930-df36-instance-relpath` | 1 | 0 / 0 | 0 / 0 |
| `20260930-dup-w-calc` | 1 | 0 / 0 | 0 / 0 |
| `20260930-restore-plan-functions` | 2 | 2 / 2 (`lut_conditions_from_npz`, `derived_spec`) | 0 / 0 (면제 승인) |
| 나머지 23건 | 0 | 0 / 0 | 0 / 0 |

지금까지의 card에는 새 엔진 def가 거의 없어 규칙 차이가 드러날 기회가 적었다 -- 무동작 근거로는 충분하지만 새 규칙의 거부 동작 증명은 §5 redteam 케이스가 맡아야 한다.
card에서는 auditor가 같은 방식으로 다시 잰다(이 표는 인용 금지).
