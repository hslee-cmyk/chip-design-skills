# B26 사전 조사: `supply_nets` 선언을 엔진 전체에 배선

R = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, A = `R/skills/analog-gmid-design/assets`, 기준 HEAD = master `cd64170`.
읽기 전용이다(저장소·worktree 쓰기 없음, git 상태 변경 없음. 끝난 뒤 `git status`가 시작할 때와 같음을 확인했다). 실측 스크립트와 원자료는 C:/g21에 두었다가 삭제했다. 스크립트 내용은 각 절에 요약해 두었다.

---

## 0. 계획서 원문 (docs/01-plan/features/gain-budget-gmid-sizing.plan.md)

- **DF-19**(929행): "레일 넷 집합이 모듈마다 다르다(대소문자) | stick_diagram `_RAIL_NETS`, sizing_recipe `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO` 레일 판정 | 4(DEC-60 `supply_nets`·`supplies_v` 선언으로 교체, MG1, DF-26과 같은 변경 단위, U-26) | **위치 열은 전수여야 한다**: 레일 넷 이름을 동작 조건으로 쓰는 운영부 함수가 실측 29개(`sizing_recipe` 15 · `stick_diagram` 10 · `run_harness` 4)인데 현 목록은 일부만 적는다 -- MNA 고정 노드(`fixed = {"gnd": 0.0}`)와 기둥 추적의 진입 넷 비교가 특히 빠져 있고, 이 둘은 DEC-71 기둥 유도·IC11 3레일이 겨누는 고장이다. Phase 4에 **'운영부 레일 이름 리터럴 0' lint**를 두고 목록을 그 lint 산출로 대체한다(원자료는 history H4)"
- **DF-26**(936행): "레일 판정이 넷 이름 집합 하드코딩이다(sizing_recipe `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO`, stick_diagram `_RAIL_NETS`). 신규 회로 `sf_pushpull_output_opamp`·`pushpull_follower_buffer`의 중간 전위 레일 `agnd`(DC에서는 W0 레일, AC구조에서는 교류접지)를 레일로 읽지 못한다 | sizing_recipe.py 3882~3883, stick_diagram.py 3147 참고 | 4(DEC-60 구현, DF-19와 같은 변경 단위) | DEC-60, DF-19, IC11, U-26"
- 관련: DEC-60(254행, 레일 넷은 `supply_nets`, 레일 전압은 `supplies_v`. 선언이 없는 기존 회로에는 MG1까지 "전환기 이름집합 해석"을 한시 허용), MG1(802행, Phase 4), N3.16 정본표(769~771행: 레일 넷 = `supply_nets`, 옛 이름 `_DEFAULT_RAIL_HI/LO`, `rail_nets`, `_RAIL_NETS` / 레일 전압 = `supplies_v` / metric 인자 `supply_nets`는 이름을 비움), IC11(829행), U-26(1101행: (b) 9/9 선언 완료, (a) `supplies_v` 전압은 미확정, nmcnr만 ±0.9 확정), Phase 4 행(1001행).
- 백로그 원문(`.ai/context.md` 14963행): "B26(DF): P4에서 probe 레일 집합을 _DEFAULT_RAIL_HI/LO(넷 이름 리터럴)로 배선했고 _metric_supply_current는 'vdd'만 본다 -- supply_nets 선언에서 읽도록 고칠 대상". 14972행: "B26 해소 = supply_nets 선언 배선으로 엔진 전반 레일 이름 의존 제거(Phase 4 후보, P3c 재착수 조건 (2)와 같은 일)".
- 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` §2의 40·42·43·45·53~56행이 B26 때문에 '정본 후보'에 머물러 있다.

**중요 실측: 엔진은 지금 `supply_nets`를 한 곳도 읽지 않는다.** `grep -rn "supply_nets\|supplies_v" --include=*.py`에서 A 운영 코드에 걸리는 것은 `sizing_recipe.py:4361` 하나뿐이고, 이것은 topology 최상위 선언이 아니라 **metric 선언 안의 같은 이름 키**다(`spec.get("supply_nets")`, 뜻이 다르다. N3.16이 MG1에서 이름을 비우라고 한 그 키). 최상위 `supply_nets`를 읽는 것은 test 보조 함수 `tests/unit/_library_sized_contexts.py:72 declared_supply_nets`뿐이다.

---

## 1. 이름으로 레일을 판정하는 곳 전수

방법: A의 운영 파일 7개와 `workspaces/run_harness.py`를 AST로 훑었다. docstring은 빼고, (a) 이름 상수 `_DEFAULT_RAIL_HI/_LO`·`_RAIL_NETS`·`_rail_nets` 참조, (b) `.rail_nets` 속성, (c) 레일 이름 문자열 리터럴(`vdd|vss|gnd|avdd|avss|agnd|dvdd|dvss|vcc|vee`, 대소문자)을 모았다. `.lower()`/`startswith` 비교는 레일과 무관한 것만 있었다(sizing_recipe 5190 단위 접미사, stick_diagram 933 대소문자 충돌 검사). design_report·topology_library·audit_current_forced·topology_to_markdown·sky130_lut_sweep에는 해당 없음.

도달 가능성은 최상위 이름 참조 그래프(모듈 간 import 포함, 레지스트리 dict 참조 포함)로 계산했다. `run`=`run_harness.run`에서 도달, `opt`=`optimize_full_circuit_budget`에서 도달, `aud`=`run_full_circuit_audit_from_topology`(하네스 472행)에서 도달. `P3`는 `_drafts/p3_assign.json`을 만든 `p3_assign.py`의 초안 배정을 그대로 다시 계산한 목적 모듈이다.

리터럴을 두 종류로 나눈다.
- **N(넷 이름 판정)**: 넷 이름이 레일인지 이름으로 판정한다. **B26 대상.**
- **V(스칼라 전압 키)**: `spec["vdd"]`처럼 spec의 스칼라 전압 키를 읽는다. 넷 판정이 아니고 MG1(`supplies_v`에서 유도하는 함수 하나)의 대상이다. 참고용으로 따로 적는다(§1.3).

### 1.1 sizing_recipe.py: N 종류

| 줄 | 함수(안쪽) | 무엇 | 정하는 것 | run/opt/aud | 호출자 | P3 |
|---|---|---|---|---|---|---|
| 3714·3715 | 모듈 상수 | `_DEFAULT_RAIL_HI = {"vdd","VDD"}`, `_DEFAULT_RAIL_LO = {"gnd","GND","vss","VSS"}` | 아래 5곳의 기본값 | Y/Y/- | 5곳 | **UNASSIGNED** |
| 2207 | `true_current_mirror_groups` | `rails = HI∪LO`(집합) | 전류미러 그룹 키에서 레일 소스를 빼는 판정 → L 동치류 | Y/Y/- | `l_sharing_classes` | MOD3 |
| 3728 | `propagate_node_voltages` | 기본 인자 `rail_hi/rail_lo`(**극성 필요**) | 노드 DC 전압 시작점(hi=spec vdd, lo=0 V) | Y/Y/- | `_hr_resolve_vertical_group`, `audit_vsb_consistency`, `reconcile_vsb_from_nodes`(모두 기본값 사용, 넘기는 호출부 0) | MOD3 |
| 3790 | `derive_vsb_from_nodes` | 기본 인자 `rail_hi/rail_lo` | 받기만 하고 본문에서 안 쓴다(vsb 식은 `vdd - v`/`v`, DF-24 소관) | Y/Y/- | 같음 | MOD3 |
| 3950 | `node_pole_estimate` | `rails = HI∪LO` | 노드 pole 추정의 레일 제외 | **N**/N/- (test 2곳만) | 없음 | UNASSIGNED |
| 4086 | `build_ac_network` | `fixed = {"gnd": 0.0}` | **MNA 고정 노드**(소신호 접지) | Y/Y/- | `_metric_parasitic_pm_deg`, `full_circuit_response_at_omega` | MOD5 |
| 4991 | `_full_circuit_response` | `fixed = {"gnd": 0.0}` | 같음 | Y/Y/- | `_metric_smallsignal_gain_db`, `_metric_smallsignal_ratio_db` | MOD5 |
| 4293 | `_metric_kcl_residual` | `spec.get("rail_nets") or ("vdd","VDD","gnd","GND","vss","VSS")` | KCL 잔차에서 뺄 레일 | Y/Y/- | `_METRICS_REGISTRY` | MOD4(초안) |
| 4361 | `_metric_supply_current` | `spec.get("supply_nets") or ("vdd","VDD")`(**극성: 높은 레일**) | 공급전류를 셀 레일 | Y/Y/- | `_METRICS_REGISTRY` | MOD4(초안) |
| 4626 | `_metric_rail_referenced_voltage` | `spec["rail"] == "vdd"`이면 spec vdd, 아니면 0.0 | 선언된 레일 이름을 전압으로 바꾸는 판정 | Y/Y/- | 레지스트리, `_metric_battery_centering_deviation` | MOD4(초안) |
| 4650~4653 | `_metric_battery_centering_deviation` | 위 함수에 `rail: "vdd"`/`"gnd"`를 박아 넘김 | class-AB 센터링 metric의 위·아래 레일 | Y/Y/- | 레지스트리 | MOD4(초안) |
| 6881·6886, 6920·6931·6948 | `_hr_thin_singleton_ideal_source_check`, `_hr_fold_group_check` | `topo.rail_nets` 소비 | 열린 단자(레일 아닌 source/drain) 판정 | Y/Y/- | `_build_theta_evaluator`, `_hr_resolve_vertical_group` | MOD3 |
| 7282 | `_hr_resolve_vertical_group` | `_usrc in HI or _usrc in LO` | 위쪽 소자 소스가 레일이면 vsb=0 | Y/Y/- | `_build_theta_evaluator` | MOD3 |
| 8003·8091 | `_build_theta_evaluator` | `_rail_nets = frozenset({"vdd","gnd","vss"})`(세 번째 레일 집합) → `rail_nets=` | 위 `_hr_*`의 `topo.rail_nets` 공급원 | Y/Y/- | `optimize_full_circuit_budget` 외 5 | MOD6 |

레일 이름 집합이 **파일 안에서만 세 벌**이다: `_DEFAULT_RAIL_*`(대소문자 6개), `_metric_kcl_residual` 인라인 튜플(6개), `_build_theta_evaluator` 인라인(소문자 3개). 여기에 `_metric_supply_current`(vdd만)와 MNA(`gnd`만)가 더 있다.

### 1.2 stick_diagram.py: N 종류

| 줄 | 함수(안쪽) | 무엇 | 정하는 것 | run/opt/aud | 호출자 | P3 |
|---|---|---|---|---|---|---|
| 2983 | 모듈 상수 | `_RAIL_NETS = {"vdd","gnd","vss"}` | 아래 10곳 | Y/Y/Y | 10곳 | **MOD7**(사용처는 MOD2·3 → 역방향 import 10건) |
| 1014 | `find_matching_candidates` | `source in _RAIL_NETS` | 차동쌍 후보에서 레일 소스 제외 | Y/Y/Y | `check_symmetry_dispositions`, `propose_device_roles_gap_fill`, `run_full_circuit_audit` | MOD3 |
| 1222·1233·1234 | `trace_vdd_to_gnd_branches`(`_trace`) | 종료 `en in _RAIL_NETS`, **시작 `entry_net(t) == "vdd"`, 종료 라벨 `term == "gnd"`**(극성) | 하향 가지(기둥) 추적 | Y/Y/Y | `find_differential_and_mirror_forks`, `suggest_vertical_stack_composites` | MOD3 |
| 1270·1281·1282 | `trace_gnd_to_vdd_branches` | 시작 `== "gnd"`, 종료 라벨 `== "vdd"` | 상향 가지 추적 | Y/Y/Y | 같음 | MOD3 |
| 1355·1357 | `find_differential_and_mirror_forks` | 라벨 `"gnd"`/`"vdd"` 비교 | 분기 분류 | **N** (test 2곳) | 없음 | MOD7 |
| 1557·1558·1575 | `find_differential_pair_candidates` | 방향별 종료 라벨, `ta.source in _RAIL_NETS` | 차동쌍 후보 | Y/Y/Y | `_propose_L_roles`, `_propose_gm_id_roles`, `refine_differential_and_mirror_relations` | MOD3 |
| 1617 | `_diff_pair_layer1_groups` | `t.source in _RAIL_NETS` | 층위1 차동 그룹 | Y/Y/Y | `find_differential_pair_candidates` | MOD3 |
| 1737 | `find_verified_differential_and_mirror_relations` | 방향별 종료 라벨 | 검증된 차동/미러 관계 | Y/Y/Y | `propose_vertical_stack_id_gap_fill`, `refine_...` | MOD2 |
| 2096 | `_propose_gm_id_roles` | `seeds = {"vdd":"vdd","gnd":"gnd"}` | 넷 대응 씨앗(레일은 자기 자신) -- **`vss` 없음** | Y/Y/Y | `_propose_L_roles`, `refine_...` | MOD2 |
| 2172 | `_propose_L_roles` | 같음 | 같음 | Y/Y/Y | `refine_...` | MOD2 |
| 3042 | `kcl_series_union` | `net in _RAIL_NETS` | KCL 직렬 합집합에서 레일 제외 | Y/Y/- | `_build_theta_evaluator`, `_kcl_branch_map` | MOD3 |
| 3148 | `_kcl_and_matching_edges` | 같음 | KCL 엣지(레지스트리 43행 정본 후보) | Y/Y/Y | `audit_vertical_stack_id_vs_kcl`, `propose_vertical_stack_id_gap_fill` | MOD3 |
| 3253 | `audit_vertical_stack_id_vs_kcl` | 허브 넷에서 레일 제외 | vsid 감사 | Y/Y/- | `resolve_stack_layout` | MOD2 |
| 3559·3561·3719 | `propose_theta_kcl_gap_fill` | 레일 단자 판정 | theta KCL 제안 | **N** (test 6곳) | 없음 | MOD2 |
| 3992, 4171, 4307, 4323, 4370, 4392 | `propose_device_roles_gap_fill` | 씨앗 `{net: net for net in _RAIL_NETS}`, 레일 단자 판정 5곳 | 로드 시 role·매칭쌍 자동 채움 | Y/Y/Y | `load_topology` | MOD2 |
| 6742~6791 | `folded_cascode_example`, `two_stage_ota_example` | `Transistor(source="vdd")` 등 | **판정 아님(예제 데이터)** | N | 없음 | MOD7 |

### 1.3 V 종류(스칼라 `spec["vdd"]`, MG1 대상, B26 아님)

sizing_recipe `stack_kvl_vgs_limit`(1729), `_metric_stack_headroom_slack`(3254), `_metric_rail_referenced_voltage`(4626), `_metric_battery_centering_deviation`(4653), `_hr_verify_group_kvl_sum`(7068), `_hr_resolve_vertical_group`(7222·7228·7290·7295·7296·7445·7449·7450), `_build_theta_evaluator._evaluate`(8233·8242·8277·8652), `search_stage_budget_L_warm_start._centering_dev`(10157~10160), 그리고 run_harness `_spec_two_stage_ota`(105)·`_spec_current_reuse_telescopic_ota`(142)·`_spec_folded_cascode`(234)·`_spec_nmcnr_amplifier`(288)의 `"vdd": 1.8`. 계획이 말한 "run_harness 4"는 이 네 곳이고 넷 판정이 아니라 전압 선언이다. 여기에 더해 가장 낮은 레일을 0 V로 두는 암묵 가정(`nodes[n] = 0.0`, `else 0.0`, `0.0 + vgs_l`)은 DF-24·IC11 소관이다.

### 1.4 집계

- N 종류 운영 함수: sizing_recipe 14개(+상수 2), stick_diagram 14개(+상수 1, 예제 2 제외). 그중 운영 경로에서 도달하지 않는 것은 `node_pole_estimate`, `find_differential_and_mirror_forks`, `propose_theta_kcl_gap_fill` 3개다. 계획의 "29개(15·10·4)"는 옛 review11 줄 번호 스캔이고, 이 AST 전수가 그것을 대체한다(stick_diagram은 `trace_*`·`_propose_*`·씨앗이 추가돼 14개).
- **극성(높은/낮은 레일)이 필요한 곳**: `trace_vdd_to_gnd/gnd_to_vdd`, `find_differential_pair_candidates`·`find_verified_...`·`find_differential_and_mirror_forks`의 방향 라벨, `propagate_node_voltages`, `_metric_supply_current`, `_metric_rail_referenced_voltage`, `_metric_battery_centering_deviation`, MNA 고정 노드. 나머지는 레일 **집합**만 있으면 된다.

---

## 2. `supply_nets`·`supplies_v` 선언 실태와 이름집합 비교

### 2.1 선언

- 스키마: topology 최상위 `"supply_nets": [넷 이름...]` + 주석 키 `_supply_nets_comment`. 9/9 library 회로가 선언한다(`_TEMPLATE`만 없음). `linked_topology_files`를 쓰는 회로는 0개다(값이 전부 `[]` 또는 없음).
- `supplies_v`: topology 안에서는 **문서 필드에만** 있다 -- `ngcc_3stage_ff`(`_declared_target_spec` {vdd 1.8, gnd 0}, `_paper_target_spec` {vdd 1.2, gnd 0}), `nmcnr_amplifier`(`_declared_target_spec` {vdd 0.9, vss −0.9}, `_paper_target_spec` {vdd 1.0, vss −1.0}), `pushpull_follower_buffer`·`sf_pushpull_output_opamp`(`_declared_target_spec` {vdd 1.8, vss 0, agnd 0.9}). `_` 접두 필드라 어떤 코드도 읽지 않는다(DEC-68). 실행 spec(`run_harness._spec_*`)에는 `supplies_v`가 없다(스칼라 `vdd: 1.8`만). `sizing_spec.json`은 저장소에 아직 없다(7b).

### 2.2 선언 집합 = 이름 집합? (회로별 계산)

netlist 단자(source/drain/gate/bulk) ∪ `passive_elements`·`ideal_sources` 단자에 실제로 나오는 넷 기준.

| 회로 | `supply_nets` | stick `_RAIL_NETS`∩넷 | sizing `_DEFAULT_RAIL_*`∩넷 | 같음 | 차이 |
|---|---|---|---|---|---|
| common_gate_amplifier | vdd, gnd | vdd, gnd | vdd, gnd | 예 | |
| current_reuse_telescopic_ota | vdd, gnd | 같음 | 같음 | 예 | |
| folded_cascode | vdd, gnd | 같음 | 같음 | 예 | |
| ngcc_3stage_ff | vdd, gnd | 같음 | 같음 | 예 | |
| nmcnr_amplifier | vdd, vss | vdd, vss | vdd, vss | 예 | 단 `"vdd"/"gnd"` 짝 리터럴을 쓰는 곳에서는 다름(§2.3) |
| pushpull_follower_buffer | vdd, vss, **agnd** | vdd, vss | vdd, vss | **아니오** | `agnd`(커패시터 단자에만 나옴) |
| sf_pushpull_output_opamp | vdd, vss, **agnd** | vdd, vss | vdd, vss | **아니오** | `agnd`(커패시터 2개에만 나옴) |
| two_stage_ota | vdd, gnd | 같음 | 같음 | 예 | |
| two_stage_ota_sf | vdd, gnd | 같음 | 같음 | 예 | |

대문자 변형(`VDD` 등)은 9회로 어디에도 없다. `agnd`는 트랜지스터 단자로 한 번도 나오지 않아서, **트랜지스터 단자만 보는 집합 판정 사이트에서는 두 회로도 결과가 같다**(그 사이트들은 `agnd`를 만날 일이 없다). 달라지는 것은 수동소자 단자까지 보는 사이트(MNA 고정 노드)뿐이다. 두 `agnd` 회로는 사이징 대상이 아니다(`run_harness.SPECS`에 없음).

### 2.3 극성: 이름 없이 높은/낮은 레일을 정할 수 있나

회로별로 선언 레일이 어떤 단자로 나오는지 셌다: PMOS source로만 나오는 레일 = 높은 레일, NMOS source로만 나오는 레일 = 낮은 레일(구조 규칙).

| 회로 | 구조 규칙 hi / lo | 이름 규칙 hi / lo |
|---|---|---|
| 6개 vdd·gnd 회로 | vdd / gnd | 같음 |
| nmcnr_amplifier | vdd / vss | `"vdd"`/`"gnd"` 짝 리터럴 사이트에서는 lo가 **없음** |
| pushpull_follower_buffer, sf_pushpull_output_opamp | vdd / vss (agnd는 어느 쪽도 아님) | 같음(단 `"gnd"` 짝 사이트에서는 lo 없음) |

즉 9/9에서 구조 규칙이 모순 없이 hi/lo를 준다. **vss 레일 회로 3개에서 현 코드가 이미 틀리게 돈다**: `trace_vdd_to_gnd_branches`는 끝 라벨을 `term == "gnd"`로만 붙이고 `trace_gnd_to_vdd_branches`는 `entry_net == "gnd"`에서만 시작한다.

**실측(stick_diagram 사본에 패치해 비교, 저장소 코드는 건드리지 않음)**: 사본에서 `_RAIL_NETS`를 회로의 `supply_nets`로, 시작·종료 판정을 구조 규칙 hi/lo 집합 소속으로, 씨앗을 `{r: r for r in supply_nets}`로 바꾸고 원본과 비교했다.

| 회로 | 하향 완결 가지 원본/패치 | 상향 완결 가지 원본/패치 | `load_topology` meta | `run_full_circuit_audit_from_topology` | `refine_...`·`find_verified_...`·`find_differential_pair_candidates`·`find_..._forks` |
|---|---|---|---|---|---|
| vdd·gnd 6회로(common_gate 포함) | 같음 | 같음 | 같음 | 같음 | 같음 |
| nmcnr_amplifier | **0 / 7** | **0 / 7** | 같음 | 같음(둘 다 같은 ValueError) | 같음 |
| pushpull_follower_buffer | **0 / 3** | **0 / 3** | 같음 | 같음 | 같음 |
| sf_pushpull_output_opamp | **0 / 4** | **0 / 8**(완결 4) | 같음 | 같음 | 같음 |

해석: `trace_*` 함수의 **반환값은 vss 회로 3개에서 바뀐다**(지금은 조용히 빈 결과). 하지만 그 결과를 쓰는 운영 소비처(로드 시 자동 채움 meta, 감사, 관계 정제)는 9/9 모두 같다. 이것은 현재 사이징 결과를 보존한다는 증거다. 다만 "기둥 추적이 vss 회로에서 무동작"(DF-19가 짚은 '기둥 추적 진입 넷 비교')은 실재하는 결함이다. 감사 ValueError는 원본과 패치에서 같은 예외다(`_netlist_sections_structured` 미선언 회로, 레일과 무관).

### 2.4 MNA 고정 노드: 선언 레일 전부를 고정하면 무엇이 바뀌나

실측: 엔진 코드는 고치지 않았다. `tests/unit/_library_sized_contexts.sized_circuits()`(하네스 SPECS 회로마다 bounds 중앙점 theta로 한 번 평가)로 ctx를 만들고, 선언 인자에 레일을 0.0으로 더해 같은 효과를 냈다(gain/pm은 `also_fix`, ratio_db는 `excite_num/den`에 `setdefault`. excite에 레일이 이미 있으면 그 값이 이긴다. PSRR의 `vdd: 1` 여기는 유지된다).

| 회로 | metric | 현재 | 레일 전부 고정 | 차 |
|---|---|---|---|---|
| current_reuse_telescopic_ota | cmrr_estimate_db (제약 ≥ 60) | 73.1449 | 73.3801 | **+0.235 dB** |
| 〃 | psrr_estimate_db | 73.6467 | 73.6467 | 0 |
| 〃 | gain_full_circuit_db | 67.6416 | 67.6416 | 0 |
| 〃 | parasitic_pm_deg | 75.9014 | 75.9014 | 5.7e-6 |
| two_stage_ota | gain_db | 중앙점 theta에서 InfeasibleSizingError(레일과 무관) -- 선언이 이미 `excite`에 `vdd: 0.0`을 적었으므로 이론상 차 0 | | |
| folded_cascode | 소신호 MNA metric 없음 | | | |
| nmcnr_amplifier | 중앙점에서 InfeasibleSizingError. 소신호 MNA metric도 없음(`nmcnr_gain_db`·`nmcnr_pm_deg`는 폐형식) | | | |

current_reuse의 CMRR 선언은 `vdd`를 여기에도 `also_fix`에도 두지 않아, 지금은 `vdd`가 MNA에서 자유 노드다(two_stage_ota 선언 주석 297행이 같은 현상을 "심각한 버그"로 기록해 둔 것과 같은 종류). 레일 전부를 교류접지로 두는 것은 DEC-60("선언이 없으면 그 넷이 신호 넷으로 남아 ... 교류접지 집합이 어긋난다")과 맞지만, **파일럿 회로의 제약 metric 값이 바뀌는 동작 변경**이다. 중앙점 기준이고 θ*에서 다시 재야 한다(auditor 몫). 73 dB > 60 dB라 활성 제약은 아닐 가능성이 높다.

---

## 3. 배선 설계안

### 3.1 정본 접근자 하나

- **`rail_declaration(topology_raw) -> RailDecl`**(frozen dataclass): `nets: frozenset`(= `supply_nets`), `hi: frozenset`, `lo: frozenset`, `mid: frozenset`(= nets − hi − lo, 예: agnd).
  - `nets`: `supply_nets`만 읽는다. **없으면 거부**(ValueError. GB0 규칙 "library 회로 전부 필수"와 같다). 이름집합 대체 경로는 두지 않는다(§4 D0).
  - 극성 `hi/lo`: 구조 규칙(PMOS source로만 나오는 레일 = hi, NMOS source로만 나오는 레일 = lo). 한 레일이 두 극성 source로 다 나오면 거부한다. 9/9 모순 0(§2.3). 실행 spec에 `supplies_v`가 있으면(MG1 이후) 전압 순서와 구조 극성이 맞는지 대조하는 게이트를 둔다(다르면 거부). 이 규칙 채택은 §4 D1.
  - 링크 파일: 진입 파일의 선언이 정본이다. 링크 파일에 다른 값이 선언돼 있으면 거부한다(현재 해당 회로 0개).
- **위치(Phase 3 전)**: `stick_diagram.py`. `load_topology`가 이미 raw JSON을 읽고, sizing_recipe가 stick_diagram을 import한다. `load_topology`는 한 번 계산해 `meta["rails"]`로 싣는다. Phase 3 이후의 목적지는 MOD3 `circuit_state_graph`(S1 노드 `is_rail`, N3.3 364행)이다. MOD2·3·4·5·6 모두 여기서 아래 방향으로 import할 수 있다.
- **캐시(NFR-2)**: 새 캐시를 만들지 않는다. sizing_recipe는 이미 raw를 읽는 `_load_full_topology_cached` 엔트리에 `"rails"` 필드를 얹는다(`matching_pairs`·`ideal_sources`와 같은 방식이고, 같은 파일을 다시 열지 않는다). stick_diagram은 `load_topology` 호출 한 번에 한 번 계산해 인자로 넘긴다. 현재 캐시 키는 **경로 문자열**이고 NFR-2가 요구하는 내용 지문이 아니다. 하지만 이것은 기존 결함이고(S0 지문 = topology 정규화 JSON 해시이며 `supply_nets`를 포함한다, N3.3), B26은 같은 엔트리에 얹기만 해서 결함을 더 키우지 않는다. 키를 내용 해시로 바꾸는 일은 S0 지문 도입(6a/6b) 몫이다. 평가 루프 안에서는 재계산이 0회다(엔트리당 1회).

### 3.2 바꾸는 호출부

- **집합만 필요한 곳(A군)**: stick_diagram `_RAIL_NETS` 사용 10곳 + `_propose_*` 씨앗 2곳, sizing_recipe `true_current_mirror_groups`, `_hr_resolve_vertical_group` 7282, `_build_theta_evaluator` 8003(`topo.rail_nets` 공급원 → `_hr_*` 2개가 따라옴), `_metric_kcl_residual` 기본값, `node_pole_estimate`(도달 불가지만 리터럴 0 lint 대상).
- **극성이 필요한 곳(B군)**: `trace_*` 2개(시작·종료 라벨), 방향 라벨을 비교하는 3개(`find_differential_pair_candidates`, `find_verified_...`, `find_..._forks`. 라벨 `"vdd_to_gnd"` 같은 문자열은 방향 토큰일 뿐 넷 이름이 아니므로 남겨도 lint 대상은 아니다. 다만 lint가 헷갈리지 않도록 `"hi_to_lo"`로 바꾸는 것을 권장한다), `propagate_node_voltages`/`derive_vsb_from_nodes` 기본 인자 제거(호출부 4곳이 `rails.hi/lo`를 넘김), `_metric_supply_current` 기본값 = `rails.hi`, `_metric_rail_referenced_voltage`(`rail in rails.hi`이면 spec vdd, `rail in rails.lo`이면 0.0, 둘 다 아니면 거부. 전압 값 자체는 MG1 전까지 전환기 규칙 그대로 둔다), `_metric_battery_centering_deviation`(리터럴 `"vdd"/"gnd"` 대신 hi/lo 레일, 레일이 각각 정확히 하나가 아니면 거부).
- **MNA(C군)**: `build_ac_network`·`_full_circuit_response`의 `fixed = {"gnd": 0.0}`. 선택지 (i) `{r: 0.0 for r in rails.nets}` 다음에 `also_fix`·`excite`로 덮어쓰기(교류접지 = 레일 전부, 동작 변경 §2.4). (ii) 보존안 `rails.lo`만 고정(vdd·gnd 회로에서는 결과가 같다. vss 회로는 소신호 MNA metric이 없어 지금은 영향 0이지만 agnd를 자유 노드로 남긴다). §4 D2.
- **metric 선언 키 `rail_nets`·`supply_nets`(metric 안)**: library 선언에서 쓰는 곳 0건(실측). 읽기를 없애고 선언값만 쓴다. N3.16 MG1 "metric 인자 `supply_nets` 이름을 비운다"를 앞당기는 것이다. 옛 키 거부 게이트는 MG1 card 몫으로 남긴다.
- **예제 함수**(`*_example`): 데이터라 판정이 아니다. lint에서 "Transistor 생성자 인자" 형태를 면제하거나 tests로 옮긴다(레지스트리 처리 열 확인 필요).
- **스레딩 비용(실측)**: 레일 판정 함수(30개)에서 거꾸로 올라가 topology 접근(`topology_path`/`ctx`/`json_path` 인자)이 있는 함수까지 가는 사슬에서, **레일 인자를 새로 받아야 하는 함수가 40개**다(stick_diagram 레이아웃 쪽 `_kcl_branch_map`→`_branch_composite_pair`→`repair_matching_safety`·`find_min_crossover_layout_with_branch_composite` 경로 포함). 뿌리는 16개(`load_topology`, `_build_theta_evaluator`, `optimize_full_circuit_budget`, metric 4개, MNA 2개 등). 인자는 **기본값 없는 키워드 인자**로 둔다. 기본값을 이름 집합으로 두면 원칙 위반이 되살아나고, `None`→이름 집합도 같은 문제다.

### 3.3 동작 보존 증거와 동작 변경

- **보존(9/9)**: A군 전부. 트랜지스터 단자만 보는 판정이라 `agnd` 차이도 결과에 닿지 않는다. B군 중 `load_topology` meta·감사·관계 정제는 9/9 같다(§2.3 실측). 사이징 대상 4회로의 instance.json·θ*는 같아야 하고, auditor가 E-LIB(library 9회로 로드 결과)·E-INST(사이징 대상 instance.json)로 확인한다.
- **바뀌는 것**: (1) `trace_*` 반환값이 vss 회로 3개(nmcnr, pushpull_follower_buffer, sf_pushpull_output_opamp)에서 빈 결과에서 실제 가지로 바뀐다(red 증거로 쓸 수 있다). (2) C군 (i)을 고르면 current_reuse `cmrr_estimate_db`가 중앙점에서 +0.235 dB 바뀐다.
- **red 형태**: 라이브러리에 없는 레일 이름을 쓰는 합성 topology(선례: `tests/contracts/test_d_delete_telescopic.py:185` `_SYN_RAILS = ["rail_hi","rail_lo"]`)를 공개 진입점(`load_topology` meta의 자동 채움·vsid, `_build_theta_evaluator` 경로의 KCL 합집합, `compute_metric`의 kcl_residual·supply_current)에 넣는다. base에서는 레일을 못 읽어 assertion FAIL이 나고 병합본에서는 PASS다. vss 회로의 `trace_*` 가지 수도 red가 된다.
- **test 파급(test-author 몫)**: 레일 인자를 받게 되는 함수를 직접 부르는 test 호출이 많다(AST 실측: `find_matching_candidates` 9, `refine_...` 9, `propose_device_roles_gap_fill` 8, `propose_theta_kcl_gap_fill` 6, `trace_*` 5, `true_current_mirror_groups` 4, `find_verified_...` 3, `propose_vertical_stack_id_gap_fill` 3, 그 밖 각 1~2). `supply_nets` 없이 topology dict를 만드는 test 파일도 최대 7개다(`test_ic3.py` 10곳, `test_selftest_sizing_recipe.py` 16곳, `test_probe_prevention_wiring.py` 6곳, `test_selftest_stick_diagram.py` 5곳, `test_df36_instance_relpath.py`, `test_probe_lut_L_interpolation.py`, 도구 `apply_b19p_mirror_wiring.py`. 이 수는 `"netlist"` 등장 횟수라 라이브러리 JSON 복사본을 고치는 경우도 섞인 상한이다). 시그니처가 바뀐 기존 test는 base에서 TypeError로 실패한다. 이것은 red(assertion FAIL)로 세지 않으므로 red 증거는 새 합성 test가 맡는다. 판정 기록에서 이 구분을 명시해야 한다(V2).

### 3.4 card 분할(초안)

| # | id(초안) | 범위 | 판정 유형 | 크기(함수/호출부) | 승인 |
|---|---|---|---|---|---|
| B26-1 | `b26-rail-accessor-set` | 접근자 `rail_declaration`(nets만, 없으면 거부) + `load_topology` meta + `_load_full_topology_cached` 엔트리 + **A군** 전부(stick 12곳, sizing 6곳) + 스레딩 | red-green(합성 레일 이름) + E-LIB·E-INST 동일 | 판정 함수 ~18, 새 인자 받는 함수 ~30, 엔진 호출부 ~45 | 없음(D0이 원칙대로 가면) |
| B26-2 | `b26-rail-polarity` | 접근자에 hi/lo/mid(구조 규칙) + **B군**(trace 2, 라벨 3, propagate/derive 기본 인자 제거와 호출 4, supply_current, rail_referenced_voltage, battery_centering) + metric 안 `rail_nets`·`supply_nets` 키 읽기 제거 | red-green(vss 회로 trace 가지 수, 합성 레일의 supply_current) + E-INST 동일 | 함수 ~10, 호출부 ~15 | **D1** |
| B26-3 | `b26-mna-rail-ground` | C군 MNA 고정 노드 | (i)이면 red-green + E-INST 차이표(기준선 변경), (ii)이면 equivalence | 함수 2 | **D2**(+ (i)이면 DEC-40 기준선 승인) |
| B26-4 | `b26-rail-literal-lint` | '운영부 레일 이름 리터럴 0' lint(DF-19가 요구, 이 문서 §1 스캔 규칙을 도구로 만든 것. 예제 데이터 면제 규칙 포함) + 이름 상수 3개 삭제 + 레지스트리 §2 40·42·43·45·53~56행 '정본 후보' → 정본 확정 + DF-19·DF-26 위치 열을 lint 산출로 교체 | red-green(base에서 lint가 FAIL, 병합본에서 0) | 도구 1 + 문서 | 없음 |

B26-1이 가장 크다(stick_diagram 스레딩). 너무 크면 **stick_diagram(로드 경로)** 과 **sizing_recipe(평가 경로)** 로 나눌 수 있다. 접근자는 앞 card에 둔다. 각 card는 작성 즉시 운영 경로에 배선된다(접근자는 첫 card에서 `load_topology`와 `_build_theta_evaluator`가 바로 부른다. 만들면 배선 원칙).

### 3.5 Phase 3(모듈 이동)과의 순서

- 초안 배정(`p3_assign.py`를 다시 계산함)에서 B26 관련 사이트의 목적 모듈 분포: MOD3 `circuit_state_graph` 14함수, MOD2 `topology_authoring` 6, MOD4 `gmid_sizing_engine`(초안상 metric 포함) 6, MOD5 `circuit_metrics` 2, MOD6 `theta_search` 2, MOD7 `stick_diagram` 4(상수 `_RAIL_NETS`, 도달 불가 1, 예제 2), **UNASSIGNED 3**(`_DEFAULT_RAIL_HI/LO`, `node_pole_estimate`).
- **Phase 3 전에 B26을 하면 싸다**. 근거:
  1. 초안 역방향 import 64건 중 **10건이 `_RAIL_NETS` 하나 때문**이다(MOD7 상수를 MOD2·3이 씀). 미배정 34건 중 2건이 `_DEFAULT_RAIL_HI/LO`다. B26이 먼저 들어가면 이 상수들이 사라져 Phase 3이 둘 곳을 정할 필요가 없다. 뒤에 하면 Phase 3이 상수를 MOD3로 옮기는 결정을 따로 해야 하고, 곧 지울 이름을 옮기는 셈이다.
  2. 편집할 파일 수: 지금은 2개(sizing_recipe, stick_diagram)다. Phase 3 뒤에는 같은 편집이 6개 모듈에 퍼진다. 판정 card의 V3 변이 대상 파일과 호출부 추적도 그만큼 늘어난다.
  3. Phase 3 이동 card의 판정은 AST 해시 동일이다. B26 뒤의 AST를 옮기는 것이라 충돌이 없다. 반대 순서로 가도 이동 뒤 B26 diff가 커지지는 않지만, 스레딩 인자가 모듈 경계를 넘는 import 줄까지 건드리게 된다.
  4. 레지스트리 §2의 정본 후보 7행을 Phase 3은 '후보'로 그대로 옮긴다(`draft_phase3_design.md` 74행). B26이 먼저 가면 정본으로 확정된 상태로 옮긴다.
- 제약: Phase 3 착수 전제는 B28 병합(이미 진행 중)이다. B26은 B28과 독립이다. 계획상 B26은 Phase 4(DF-19·26, MG1과 같은 변경 단위)에 있다. **B26-1·B26-4를 Phase 3 앞으로 당기고, 전압 쪽(MG1, `supplies_v`, IC11, DF-24)은 Phase 4에 남기는 분리**가 기본안이다. 계획서 DF-19·26의 "MG1과 같은 변경 단위" 문구를 "넷 판정(B26) / 전압(MG1)" 둘로 나누는 정정이 필요하다(오케스트레이터 몫, 원칙에 따른 기본안).
- 당기지 않는 경우의 최소 조치: Phase 3 초안에서 `_RAIL_NETS`를 MOD7이 아니라 MOD3에 배정해 역방향 10건을 없앤다.

---

## 4. 사용자 결정 (진짜 사용자 몫만)

- **D1. 레일 극성의 정의(회로 해석 규칙)**: topology만으로 높은/낮은 레일을 정해야 하는 곳이 있다(로드 시점 기둥 추적. spec이 없어 `supplies_v`를 못 쓴다). 제안: "PMOS source로만 나오는 선언 레일 = 높은 레일, NMOS source로만 나오는 선언 레일 = 낮은 레일, 둘 다 아니면 중간 레일(agnd), 둘 다면 거부". 9/9 모순 0이다. 대안은 topology 스키마에 극성을 선언하는 것이다(connectivity 파일이라 사용자가 써야 한다). 회로 원리 해석이므로 공동분석 대상이다.
- **D2. 소신호 MNA에서 선언 레일 전부를 교류접지로 둘지**: 예로 두면 current_reuse `cmrr_estimate_db`가 중앙점 theta에서 73.145 → 73.380 dB(+0.235)로 바뀐다(`vdd`가 지금은 자유 노드). 아니오로 두면(낮은 레일만 고정) 현재 값이 보존되지만 `vdd`·`agnd`가 자유 노드로 남는다. 예라면 파일럿 기준선이 바뀌므로 DEC-40 승인도 함께 필요하다.
- **(B26 범위 밖, 참고) U-26 (a)**: two_stage_ota·current_reuse·folded_cascode의 `supplies_v` 값(제안 {vdd 1.8, gnd 0.0}, SPECS `vdd`에서 온 값)과 nmcnr 실행 spec을 ±0.9로 옮기는 시점. 이것은 MG1(전압) card의 착수 조건이고 B26(넷 판정)에는 필요 없다.

**사용자 결정이 아닌 것(원칙으로 기본안 확정)**:
- D0: 선언이 없으면 거부하고 이름집합 대체 경로는 두지 않는다. DEC-60의 '전환기 이름집합 해석'은 선언이 없던 회로를 위한 한시 조항이었는데, 9/9 선언이 끝났고(U-26 (b)) 사용자 원칙("항상 topology와 무관한 엔진 식")이 이름 해석을 금한다. 계획서 DEC-60 문구 정정(한시 조항 종료)은 오케스트레이터가 원칙 근거로 기록한다. 영향은 `supply_nets` 없는 test 픽스처 갱신(test-author)이다.
- card 분할, Phase 3보다 앞당기는 순서(§3.5), 접근자 위치·캐시 방식(§3.1), 방향 라벨 이름 변경, 예제 함수 lint 면제.
