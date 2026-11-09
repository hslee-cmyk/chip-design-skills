# P9 / P10(+B22) pre-measurement (read-only, gate HEAD 070cf69, 2026-09-30)

A = `skills/analog-gmid-design/assets`. SR = `A/sizing_recipe.py`, SD = `A/stick_diagram.py`.
Scratch scripts (read-only, in this scratchpad): `p9_diff.py` (+`.out.txt`), `p10_df23.py` (+`.out.txt`), `b22_scan.py` (+`.out.txt`).
No repository file was modified. `git status` after the scripts showed only the pre-existing entries.

---

## P9 -- KCL / matching edges

### 1. Design doc text (verbatim)

§8 row (design:193):
> `| P9 | `dup-kcl-edges` | `kcl_series_union`·`_metric_kcl_residual` 엣지 → 정본 | equivalence | (c) DIFF-DUP + E-LIB·E-INST | 중복 제거 |`

§6.2 (design:132-137):
> 정본 `stick_diagram._kcl_and_matching_edges`. 중복 `kcl_series_union`(같은 엣지를 따로 구현, 57줄)과 `_metric_kcl_residual`의 엣지 생성부. 둘 다 엔진 운영 경로에 있다(각 2곳).
> * 차등 test: library 회로 전부에서 두 함수가 만드는 엣지 집합이 같은지(집합 동일성, 순서 무관).
> * 다르면 F3 -- 통합하지 않고 레지스트리 상태를 고친다.

§2.2-3: "통합(DUP): 중복 쪽 호출부를 정본 호출로 바꾸고 중복 정의를 지운다. 정본의 시그니처는 바꾸지 않는다."
§10 E1 (design:218): `PT <iso>/…/tests/unit -k "dup_"` 그리고 `git -C <iso> grep -n "kcl_series_union\|_multilinear_interp_point_multi"` → "차등 test PASS, 삭제한 이름의 참조 0".
Plan N6.2 row 2 (plan:1017): "DUP마다 옛 함수 대 정본 차등 test(실행 가능한 library 회로 입력 전수 출력 동일) PASS 후 옛 함수 삭제".
Plan MOD3 (plan:523): `circuit_state_graph.py` 목적지 목록에 `_kcl_and_matching_edges`가 있다(`kcl_series_union`은 없다).

Commands: `Grep "P9|P10|DF-23|B22|E0|E5"` on the design; `Read` design 1-240; python line dump of plan 523/1017.

### 2. Registry rows (docs/03-analysis/gain-budget-gmid-sizing.function-registry.md)

| line | row (verbatim, trimmed) |
|---|---|
| 43 (§2) | `| KCL 엣지 | 정본 후보(`stick_diagram._kcl_and_matching_edges` -- 레일 판정을 `_RAIL_NETS` 넷 이름 리터럴로 읽음(stick_diagram 3148행), B26 해소 뒤 확정) | `kcl_series_union`이 같은 엣지를 따로 구현, `_metric_kcl_residual` | 행동 보존 통합 가능. 정본 함수가 넷 이름을 읽으므로 확정 정본이 아니다(B26) |` |
| 45 (§2) | 레일 넷 집합: 정본 없음 -- `supply_nets` 선언 경로가 후보. SD `_RAIL_NETS`, SR `_DEFAULT_RAIL_HI/_LO` 리터럴. "상수 하나로 합치는 것은 해결이 아니다 ... B26" |
| 308 | `_metric_kcl_residual` ... "국소: 레일 이름을 인라인 튜플(4456)로 다시 정의 -- `_DEFAULT_RAIL_HI/LO`(3882-3883)와 정의 2벌. passive 전류 미계상" (line numbers stale: now 4293 / 3714-3715) |
| 373 | `_kcl_branch_map` -- kcl_series_union을 소자별 branch로 펼침 -- R1 |
| 428 | `trace_vdd_to_gnd_branches` -- "전류방향 규약 3곳: SD:1216-1224, `_kcl_terminal_sign` SD:3580, SR `_metric_kcl_residual` SR:4469-4472" |
| 472 | `kcl_series_union` -- "같은 edge를 `_kcl_and_matching_edges`(SD:3298, docstring '단일 정의로 분리')가 재구성하지만 이 함수 본문 SD:3188-3212는 그것을 쓰지 않고 독자 구현" -- 목적지 circuit_state_graph |
| 473 | `_kcl_and_matching_edges` -- KCL/matching edge 목록(원인 보존) -- 상대: `kcl_series_union` |
| 474 | `_kcl_terminal_sign` -- "운영 0(D). SR `_metric_kcl_residual` SR:4469-4472이 같은 규약 독자 구현" |

"정본 후보" condition = **B26 해소 뒤 확정** (rail decision reads the name literal `_RAIL_NETS`). Command: `Grep "kcl|KCL|엣지|edge"` on the registry.

### 3. Defs (A/*.py, workspaces/*.py, A/tests/tools)

Command: `Grep "def \w*(kcl|edge|matching)\w*" -i --glob *.py` (repo), AST enclosing-function lookup via python -B.

| def | file:line | signature | engine callers | name literals / name-set constants |
|---|---|---|---|---|
| `kcl_series_union` | SD:3003 | `(netlist: list, matching_pairs: list) -> dict` (`{first_member: [members]}`) | SR:8055 in `_build_theta_evaluator` (`stack_groups_kcl`, import SR:5303); SD:7310 in `_kcl_branch_map` (→ `_branch_composite_pair` SD:7355 → `_composite_collapse_for_crossover` SD:7472, `repair_matching_safety` SD:7625, SR:11840) | `_RAIL_NETS` at SD:3042 |
| `_kcl_and_matching_edges` | SD:3134 | `(transistors: list, matching_pairs: list) -> list[(a,b,kind,detail)]` | SD:3206 `audit_vertical_stack_id_vs_kcl` (← SR:6551, tests); SD:3291 `propose_vertical_stack_id_gap_fill` (← SD:8643 `load_topology`, every load) | `_RAIL_NETS` at SD:3148 |
| `_metric_kcl_residual` | SR:4267 | `(spec: dict, ctx: SizingContext) -> float` | via `_METRICS_REGISTRY["kcl_residual"]` SR:5098 (units SR:5147, footprint SR:9559); declared only by `library/current_reuse_telescopic_ota.topology.json:1997` | default rail tuple literal SR:4293 `("vdd","VDD","gnd","GND","vss","VSS")` when `rail_nets` not declared (pilot does not declare it) |
| `_kcl_branch_map` | SD:7304 | `(devices: list) -> dict` | SD:7355 | none directly (calls kcl_series_union → `_RAIL_NETS`) |
| `_kcl_terminal_sign` | SD:3430 | `(kind, terminal) -> int` | SD:3689, 3694 in `propose_theta_kcl_gap_fill` (보류 Phase 3 D) | none |
| `_RAIL_NETS` | SD:2983 | `frozenset({"vdd","gnd","vss"})` | 20+ uses in SD | name literals (B26) |
| `_DEFAULT_RAIL_HI/_LO` | SR:3714-3715 | `{"vdd","VDD"}` / `{"gnd","GND","vss","VSS"}` | SR:2207, 3728, 3790, 3950, 7282 | name literals (B26) |
| other: `geometry_colocation_union` SD:3062, `find_stack_edges` SD:1083, `netclass.stack_edges` (analog-grammar):336 | -- | not KCL edges (geometry / stack) | -- |
| workspaces: only `spice/vg15_vop1_kcl_sympy_derivation.py:52 node_kcl_terms` (diagnostic, off-path) | | | | |
| A/tests/tools: no KCL/edge def | | | | |

### 4. Behaviour comparison

* `kcl_series_union` (SD:3023-3048) vs `_kcl_and_matching_edges` (SD:3142-3154): **identical edge rules** -- same `net_uses` over source/drain, same `if net in _RAIL_NETS: continue`, same `len(uses)==2 and uses[0]!=uses[1]`, same `zip(names, names[1:])` over matching_pairs. `kcl_series_union` additionally does union-find + groups sorted by netlist order. So `kcl_series_union(trs, P)` == connected components of `_kcl_and_matching_edges(trs, P)` (root choice irrelevant because the representative is re-picked by netlist order at SD:3050-3058).
* **Measured (p9_diff.py)**: for all 8 loadable library circuits × {current_forced pairs from `load_topology` meta, `[]` (the `_kcl_branch_map` call form)} → `equal=True` 16/16. (`_TEMPLATE.topology.json` fails load -- AttributeError, not a circuit.) Group counts: pilot 17/29, folded_cascode 5/9, ngcc 11/12, nmcnr 7/10, pushpull 3/3, sf_pushpull 11/12, two_stage_ota 3/4, two_stage_ota_sf 4/5, common_gate 1/1.
* Rail names actually used by transistors in all 9 circuits ⊆ `_RAIL_NETS` (gnd/vdd or vdd/vss); every topology declares `supply_nets` (two also list `agnd`, unused by MOS). So switching the rail predicate to `supply_nets` would be behaviour-preserving on the library -- but that is B26, not P9.
* **`_metric_kcl_residual` has no edge construction at all.** It sums signed `ID` injections per node (SR:4301-4309) plus declared ideal current sources (SR:4319-4329) and returns max |residual| over non-rail nodes. Output is a float, not an edge set → §6.2's "엣지 집합 동일성" DIFF-DUP is **inapplicable** (F3 case: "두 함수가 실제로 다른 개념"). What it actually duplicates: (i) the MOS KCL sign convention of `_kcl_terminal_sign` (nmos drain −/source +, pmos source −/drain + -- identical), (ii) the rail name set (third literal copy, and with upper-case variants that `_RAIL_NETS` lacks).
* "각 2곳" check: `kcl_series_union` 2 engine callers (SR:8055, SD:7310) -- true; `_metric_kcl_residual` 0 direct callers, 1 registry dispatch -- the "2곳" claim does not hold for it.
* Out-of-scope observation: union-find is re-implemented 4× (SD:3028-3039, 3096-3107, 3207-3218, 3299-...). Not a registry DUP row; do not fold into P9.

### 5. Tests referencing the names (python scan of A/tests/**)

| name | references |
|---|---|
| `kcl_series_union` | no direct call; docstrings only `unit/test_selftest_stick_diagram.py:2519, 3299` |
| `_kcl_and_matching_edges` | none |
| indirect: `audit_vertical_stack_id_vs_kcl` | `unit/test_selftest_stick_diagram.py:3318, 3727` (test_s140, s052w), `contracts/test_ic5.py:59` (domain tag) |
| indirect: `propose_vertical_stack_id_gap_fill` | `unit/test_selftest_stick_diagram.py:3644, 3664, 3694` |
| indirect: `_branch_composite_pair` / `_composite_collapse_for_crossover` | `unit/test_selftest_stick_diagram.py:2408, 2427, 2443, 2471` (s106/s107) |
| `_metric_kcl_residual` / `kcl_residual` | only `tests/probe_physical_consistency.py:20` (comment), `tests/probes/probe_metric_dashboard.py:9,79,87` -- **no unit test of the metric** |

No existing `dup_` test (E1 `-k "dup_"` has nothing for KCL yet).

### 6. Plan / design mentions

`docs/01-plan/.../plan.md:523` (MOD3 destination of `_kcl_and_matching_edges`); `history.md:567,578,710,1306,1411,3896,3902,4286,4344,4794,4826,4831,5609-5611` (kcl_residual history), `history.md:5201` (`_kcl_and_matching_edges`), `history.md:5270` ('KCL 엣지'); design `20-dead-code-dup` :19, 88, 132-137, 193, 218; specs `20260922-ic5-gate-docstrings.interface.md:98`, `20260923-probe-promote-consistency.{interface.md:9,11; spec.md:21,64}`.
Command: python scan of docs/01-plan, docs/02-design for the names.

### 7. Recommendation (P9)

Principle-derived default (no circuit interpretation involved -- pure connectivity rule, behaviour preserving, measured equal):
1. **Canonical edge generator = `_kcl_and_matching_edges`** (plan MOD3 names it; registry §2 marks it). Replace the inline edge loop in `kcl_series_union` (SD:3023-3026, 3041-3048) with union over `_kcl_and_matching_edges(netlist, matching_pairs)`; keep `kcl_series_union` name/signature/return (it answers a different question -- KCL **groups** -- and has 2 engine callers). The duplicate removed is the edge definition, not the grouping.
2. **Drop `_metric_kcl_residual` from P9.** It is not an edge generator (F3). Fix registry §2 row 43 (dup column → only `kcl_series_union`) and note in row 474/428 that the real overlap is the sign convention (`_kcl_terminal_sign`) + rail set (B26). Sign-convention unification is a different concept → later Phase (with B26 / Phase 3 circuit_state_graph).
3. DIFF-DUP oracle: groups from `kcl_series_union` vs components of `_kcl_and_matching_edges` on all loadable library circuits × {forced pairs, []}, plus NEW-TOPO synthetic netlist (new net/device names, a rail used exactly twice, a same-device source=drain net). Measured baseline: 16/16 equal.
4. **Design correction needed (orchestrator, approved-doc change)**: (a) §6.2/§8 name `_metric_kcl_residual` as a duplicate -- wrong; (b) E1 greps `kcl_series_union` expecting 0 references, which contradicts keeping it. Either amend E1 to "inline edge loop gone from `kcl_series_union` (AST: no `net_uses`/`_RAIL_NETS` in its body)" or delete `kcl_series_union` and move grouping to callers (bigger change, needs a new components helper → registry check; not recommended).
5. Canonical status stays "정본 후보, B26 해소 뒤 확정" -- P9 does not touch `_RAIL_NETS` (topology-independence fix is B26, Phase 4). P9 must not introduce any new name literal.
User decisions: none on circuit interpretation. Only the approved-design amendment (E1 wording / dropping `_metric_kcl_residual`) needs the approval route.

---

## P10 -- DF-23 inventory (+ B22 docs)

### 8. Verbatim text

Design §8 row (design:194):
> `| P10 | `df23-inventory` | DF-23 전수 목록 문서화(`df23_inventory.json` 기준 266건)와 레지스트리 기록, 신규 148건의 담당 Phase 배정 | test-only(문서) | (d) 실측 원자료 | 목록 |`

Design §1 (design:20): "**DF-23 전수 목록**: 엔진 소스의 소자·넷·회로 이름 리터럴과 topology 파일 경로 전수(DF-29~DF-34 포함). Phase 2는 **목록과 기록**이고 일반 규칙으로의 교체는 Phase 4·7a다(DF-23 행)."
Design §10 E3 (design:220): `git -C <iso> cat-file -e HEAD:docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json` 와 목록 항목 수 대조 → "목록이 있고 항목마다 담당 Phase가 적혀 있다".
Design §11-1 (design:230): rail literal 63건 DF 신설 요청(담당 Phase 4). Not yet in plan (DF table ends at DF-37; no rail-name DF).
Plan DF-23 (plan:933):
> | DF-23 | 결정 레지스터의 파일럿 적용 사실(DEC-09·15·27·55의 소자 이름)이 엔진 코드에 이름 리터럴로 박혀 동작을 정하는지 확인되지 않았다(확인 필요). 박혀 있으면 일반 규칙 대신 이름이 동작을 정한다. **점검 대상은 소자 이름만이 아니라 소자·넷·회로 이름과 topology 파일 경로 전부다**(실측: 엔진 운영부의 소자 이름 문자열 리터럴은 0건이고 실제 종속은 넷 이름·회로 이름·파일 경로였다 -- DF-29~DF-34) | 엔진 소스 전수(topology.json에서 읽은 값이 아닌 **소자·넷·회로 이름 문자열 리터럴과 topology 파일 경로 리터럴**) | 2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체) | WP-05, DEC-62, DF-29~DF-34 |

Plan N6.2 Phase 2 DoD (plan:1017): "... DF-23 전수 목록(... DF-29~DF-34의 위치가 목록에 들어 있고 항목마다 담당 Phase가 적혀 있음)".

### 8a. State of the existing inventory (p10_df23.py)

| fact | value |
|---|---|
| file | `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json` (tracked), keys scope/method/vocabulary/totals/items |
| items | 590 (324 메시지뿐 + **266 동작을 정함**) |
| behaviour by plan_mapping | 신규 **148**, DF-29 40, DF-34 18, DF-30(회로별 metric) 17, DF-33 12, DF-31(보상) 11, DF-30(신규 위치) 7, DF-31 6, DF-30 4, DF-29(신규 위치) 2, DF-32 1 |
| 신규 148 subcategories | 레일 넷 이름 리터럴 63, 픽스처 넷리스트(SD folded_cascode_example/two_stage_ota_example, 운영 호출 0) 61, 기타 넷/소자 이름 9, 어휘 충돌(넷·소자 이름 아님) 9, 파일 이름 규약(.topology.json 등) 6 |
| **phase field** | **absent** -- item keys: file, line, literal, kind, function, role, role_reason, context, declared_in, source_line, plan_mapping, stems, scan, new_subcategory. E3 "항목마다 담당 Phase" is not yet satisfiable. |
| **staleness** | measured at `1e2e243`, 93 commits ago. Of 266 behaviour items: line still matches 13, text moved 211, **text gone 42** (`_telescopic_class_ab_open_loop_response` 10, `_load_telescopic_topology_cached` 1, `suggest_headroom_stack_groups` 1, `<module>` 5, '' 25 -- P5/P5b deletions and DF-35 harness path change). The 266/148 numbers are no longer current → must be **re-measured at card base** (card-throughput rule). |
| scope | 7 A/*.py + run_harness.py; A/*.py list unchanged (audit_current_forced, design_report, sizing_recipe, sky130_lut_sweep, stick_diagram, topology_library, topology_to_markdown). |

Principle-derived default phase map (for the orchestrator to confirm; the DF table owns it): DF-29 → 7a (but P5b already deleted most -- re-measure), DF-30 → 7a, DF-31 → 7b, DF-32 → per plan row, DF-33/34 → 7b (DF-34 also 4), rail literals 63 → 4 (B26 / §11-1 DF 신설 요청), fixture netlists 61 → tests 이관 후보 (Phase 2 D-처리 or 3), 기타 9 / 파일 이름 규약 6 → 4, 어휘 충돌 9 → "해당 없음(넷·소자 이름 아님)" with reason.

### 9. Stale mentions (names with no `def` in engine)

Commands: `Grep "converge_with_parasitics|\bslew_rate\b|render_stick_diagram|..."` over `skills/analog-gmid-design`; `b22_scan.py` (backtick `name(` in references/**.md + SKILL.md, code blocks included, checked against AST defs of A/*.py + run_harness.py); `git log -S "def <n>(" -- skills` for deletion commit; `git show <c> | grep '^-def'` for P5 (2a123ba), P5b (6612902), P6 (1c5b920).

**(A) Names deleted/moved by Phase 2 (B22 core scope)**

| name | deleted/moved by | stale mention file:line |
|---|---|---|
| `converge_with_parasitics` | 2a123ba (P5) | references/function-selection-map.md:35 (usage row); references/sky130-worked-example.md:256, 262 (history narrative "수정 완료(현재 커밋에 반영됨)") |
| `slew_rate` | 2a123ba | function-selection-map.md:38; `A/library/nmcnr_amplifier.topology.json:74` (`_settling_slew_comment` "slew_rate()(sizing_recipe.py:166)") |
| `render_stick_diagram` | 2a123ba | function-selection-map.md:80; stick-diagram-euler-layout.md:1065 (import in example), :1102 |
| `suggest_headroom_stack_groups` | 2a123ba | `A/library/current_reuse_telescopic_ota.topology.json:1250, 1281` (`_vertical_stack_id_comment`) |
| `SemiEmpiricalGmIdLUT.fT` (`lut.fT(`) | 2a123ba | references/consistency-map.md:207, 209 |
| `_cmrr_telescopic_class_ab` / `_cmfb` / `_psrr_telescopic_class_ab_cmfb` | 6612902 (P5b) | references/known-incidents.md:104; SR:5015 docstring of `_metric_smallsignal_ratio_db` ("…를 대체" -- history, arguably fine); `tests/unit/test_selftest_sizing_recipe.py:2791` (comment in test_s065_section); pilot topology.json:1872 `_metrics_comment` |
| `find_interleaved_symmetric_splits` | 1c5b920 (P6, moved to `A/tests/tools/interleave_splits.py:8`) | function-selection-map.md:99 (B27: location guidance stale); design-report-spec.md:92, 308; stick-diagram-euler-layout.md:113, 215, 464, 1223 |
| SR module docstring (B22 a) | -- | `SR:15` "5. 기생 CJD 반영 반복 -> optimize_multistage()의 cgg 반복" (engine text) |
| `derived_spec`, `lut_conditions_from_npz` | restored (exists: SR:4782, run_harness) | not stale |

**(B) Pre-existing stale names (deleted before Phase 2 -- outside B22 as recorded, report only)**

`run_sizing_pipeline` (SKILL.md:52; function-selection-map.md:18, 160; consistency-map.md:37), `load_sizing_targets` / `write_sizing_results` (function-selection-map.md:26-27, 158-159) -- all removed 9e12032 (2026-08-12); `block_from_row_widths` (design-report-spec.md:259; function-selection-map.md:124) -- fa2fcfb; `classify_device_roles` (analog-grammar-integration.md:92,134,139,150,167,176,208,353) -- d4bd4d9; `ngcc_compensation_elements` (function-selection-map.md:59, "추가할 것" -- intent, not stale); `verify_symmetry_dispositions` (consistency-map.md:810,826,851,857,883), `common_centroid_2row`, `interdigitate`, `euler_condition`, `verify_walk_sequence`, `expand_interdigitation_pattern`, `detect_matching_candidates`, `generate_stick_diagram`, `common_centroid_layout_nway`, `_common_centroid_from_graph`, `verify_mirror_symmetry`, `verify_quasi_static` (consistency-map.md, many lines), `detect_extraction_anomalies` (topology-extraction-checklist.md:98,129,137), `propose/apply_fold_group_gap_fill` (analog-grammar-integration.md:475), `derive_stack_groups` (known-incidents.md:326, history), `_resolve_device_headroom` (known-incidents.md:622), `renderCircuit`/`renderMultiRowStack` (consistency-map.md:350; not in report_template.html). Full list: `b22_scan.out.txt` (222 raw hits incl. builtins/JS). `renderSchematic/renderStack/renderFloorplan/...` exist in `A/report_template.html` (not stale).

### 10. Can P10 + B22 be one doc-only card?

Partly. Recommendation:
* **One card "P10 + B22(b)"** is coherent as test-only(문서) if it touches only docs: `docs/03-analysis/.../df23_inventory.json` (re-measured + `phase` field), a registry DF-23 record, and `skills/analog-gmid-design/references/*.md` (+ SKILL.md if (B) is included). No engine `.py`, no topology.json → E-LIB/E-INST trivially unchanged.
* **Exclude from that card**: (a) `SR:15` docstring and SR:5015 -- engine source text (changes `ast.dump`; needs a `Role: code` commit → attach to a code card, e.g. an equivalence card); test-file comments (`test_selftest_sizing_recipe.py:2791`, s065/s067 docstrings) → test-author role; library `topology.json` `_*_comment` fields (1250, 1281, 1872, nmcnr:74) → topology.json is user-owned for connectivity, metadata edits are allowed but they are loaded by E-LIB → treat as separate/confirm with user.
* Scope decision (orchestrator, principle "쓸데없는 결함을 만들지 않는 5단계"): B22 as recorded = Phase-2 deletions only (table A). Table B is pre-existing; including it enlarges the card (consistency-map.md alone has ~20 stale names) -- default: record B as a new backlog item, not in this card.

Candidate contracts:
1. `df23_inventory.json` is re-measured at the card base (scope = A/*.py + run_harness.py), every `role=="동작을 정함"` item has a `phase` value from a closed set (e.g. {2,3,4,6a,7a,7b,"해당 없음(사유)"}) and every DF-29~DF-34 item keeps its `plan_mapping`; totals recomputed = item counts (E3 machine check: count items, count items without phase = 0).
2. Items' `line`/`source_line` match the base source (0 stale lines).
3. Registry has a DF-23 record pointing at the inventory with counts equal to the JSON totals; `reg_check.py` (E0) still exits 0.
4. For every name in the Phase-2 deleted/moved set, `references/**.md` + SKILL.md contain no usage guidance for it (grep 0), except lines explicitly marked as deleted/moved with the new location (e.g. `tests/tools/interleave_splits.py`).
5. No change outside `docs/**` and `skills/analog-gmid-design/references/**` (+SKILL.md) -- `git diff --stat base..merge` path filter.
