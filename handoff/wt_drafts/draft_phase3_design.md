# [초안] gain-budget-gmid-sizing -- Phase 3 `30-module-split` design (준비 자료)

> 상태: **초안(읽기 전용 준비물)**. 저장소 파일은 하나도 바꾸지 않았다. 측정 시점 = 메인 체크아웃 HEAD `070cf69`(2026-09-30).
> 정식 문서 경로(계획 N9.1): `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md` -- **현재 없음**(아래 §0 명령 M0).
> 측정 스크립트(스크래치패드, 결과 JSON도 같은 곳): `p3_measure.py`→`p3_measure.json`, `p3_assign.py`→`p3_assign.json`, `p3_refs.py`.
> 이 초안의 모든 사실 문장 끝의 `[Mn]`은 부록 A의 측정 명령 번호다. 계획서·레지스트리 문장을 사실로 옮긴 곳은 없다(인용은 인용으로 표시).

---

## 0. 다음 Phase 식별과 계획 원문 인용

### 0.1 다음 Phase = **Phase 3**(모듈 분할), design 문서 = `30-module-split`

* 계획 N6.1 순서표(유일한 순서 정본, plan 989행)에서 Phase 2 다음 행이 Phase 3이다 [M1].
* design 문서 존재 여부: `docs/02-design/features/`에 `gain-budget-gmid-sizing.*.design.md`는 `00-common`·`05-role-separation`·`10-test-separation`·`20-dead-code-dup` 4개뿐이고 `30-module-split`은 없다 [M0]. → 새로 작성 대상.
* 참고(순서 이탈 사실): Phase 4 행의 첫 항목인 DF-35·DF-36은 이미 병합됐다(커밋 `57781a7` DF-35, `070cf69` DF-36 spec card) [M2]. `.ai/context.md` 14986행에 사용자 지시("다음 순서 = … DF-35 … DF-36 … B28")로 기록돼 있다 [M3]. Phase 3 범위에는 영향이 없지만 Phase 4 착수 시 N6.1 Phase 4 순서(TS4 → DF-35 → DF-36 → …)의 앞 두 칸이 이미 채워졌음을 `40-defect-fixes`가 반영해야 한다.

### 0.2 원문 인용(줄 번호 = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`)

**N6.1 순서표 Phase 3 행(1000행)**
> `| 3 | 10모듈 이동(N3.10), shim, 추적 파일 호출부 갱신 후 `sizing_recipe.py` 삭제 | equivalence | U-03 | `30-module-split` |`

**N6.1 공통 착수 조건(991행)**
> 모든 Phase의 공통 착수 조건: **해당 design 문서의 사용자 승인**(DEC-51). 이전 Phase DoD PASS.

**N6.2 완료 조건 Phase 3(1018행)**
> `| 3 | MOD1~MOD10 존재, import 계층 위반 0(`import_layering.py`), 이동 커밋마다 AST 해시 동일, `sizing_recipe.py` 삭제, 레지스트리 이관 목적지 열 = 실제 위치 |`

**N3.10 모듈 구조(515~535행)** -- 규칙(517행)
> 규칙: **import는 번호가 작은 모듈 쪽으로만**, 순환 0, 파일당 한 책임. 함수별 목적지는 레지스트리의 "이관 목적지" 열이 정본이고, Phase 3 design 문서가 그 열에서 이관표와 실제 의존 그래프를 생성한다.

표(519~530행)는 MOD1 `gmid_lut.py` … MOD10 `gmid_design_pipeline.py` 10행. 이어서(532~535행):
> * LUT 생성(`sky130_lut_sweep.py`)과 `topology_to_markdown.py`는 도구로 남는다. `canonical_spec()`/`SPECS`는 `workspaces/run_harness.py`에 남고 MOD10에 인자로 넘긴다.
> * **이동 규칙**: 모듈 하나당 이동 전용 커밋. 무변경 증명 = 이동 전후 함수별 `ast.dump`(docstring 제외) 해시 동일 + import 줄만 차이. 해시가 같은 함수는 V3 대상에서 뺀다.
> * **shim**: `sizing_recipe.py`는 이관 중 명시 재수출 목록(인벤토리에서 생성, `_` 접두 심볼 포함, `import *` 금지)만 가진다. 저장소에 추적되는 파일 중 `sizing_recipe`를 import하는 파일을 전부 갱신하면 shim을 삭제한다(추적 안 되는 workspaces 스크래치는 U-03).
> * 등급 D 함수는 옮기기 전에 처리한다(Phase 2). 배선을 고른 함수는 동작 변경이라 Phase 4에서 배선한다.

**N9.1 문서 목록 `30-module-split` 행(1157행)**
> 반드시 담을 것: 레지스트리 목적지 열에서 생성한 함수→모듈 이관표, 계산된 import 그래프, `import_layering.py` 규칙, AST 해시 증명 명령, shim 재수출 목록 생성법, 추적 파일 호출부 목록 / 읽을 plan 절: N3.10 / N6.1·N6.2 Phase 3 / U-03

**N7.2 U-03(1078행)** -- 추가 착수 조건
> `| U-03 | 추적되지 않는 `workspaces/` 스크래치 스크립트가 `sizing_recipe.py` 삭제로 깨지는 것을 허용할지 | 허용(추적 파일만 갱신). 근거: WP-01의 배선 대상은 저장소에 추적되는 파일 | Phase 3 |`

**판정 유형과 card 단위(N3.12.3, 674·686행)**
> 이동 전용 변경(Phase 3)은 모듈 하나가 한 건이고(N3.10 이동 규칙)…
> 동작을 보존하는 변경(TS1, Phase 2 통합, Phase 3 이동)은 `equivalence`(test 커밋이 그대로이고 base와 병합본 모두 통과, 추가로 TS1은 stdout 동일, Phase 3은 AST 해시 동일).

**V2·V3·V7(N4.2, 838·839·843행)** -- 요지 인용
> V2 equivalence: test 커밋 불변 + base·병합본 모두 PASS + 유형별 동등 증명(… Phase 3 AST 해시)
> V3 대상 = diff가 닿은 def 중 AST 해시가 바뀐 것
> V7 새 def가 운영 경로에서 도달하는지(루트 목록은 설정 파일, Phase 3 전·후 두 벌)

**N8 위험(1134행)**
> `| 파일 이동 중 회귀 | test 분리 먼저, 이동 전용 커밋, AST 해시 동일 증명 |`

**다른 design 문서가 Phase 3에 넘긴 것**
* `00-common` §17 표(594행): "레지스트리·N3.10의 `optimize_full_circuit_budget` 목적지 불일치(MOD6 대 MOD8) | `30-module-split`".
* `00-common` §10.1(435행): "Phase 3는 이동만 하므로(N3.10 이동 규칙) 추출은 Phase 4다. 추출된 함수의 목적 모듈은 MOD6이다."
* `10-test-separation` 187행: "`A/tests/unit/test_selftest_<모듈>.py` ×4 … `30-module-split`에서 `unit/test_mod*.py`로 재배치", 413행: "매핑의 test id는 `30-module-split`이 `unit/test_mod*.py`로 옮길 때 그 design이 새 매핑을 낸다."
* `10-test-separation` 45행: 범위 밖 "모듈 분할 뒤 test 파일 재배치(`30-module-split`)".

### 0.3 DF·WP 항목

* **DF**: Phase 3 행에는 DF가 없다(1000행 원문에 DF 번호 없음) [M1]. DF-23 전수 목록(이름 리터럴)은 Phase 2 기록·Phase 4/7a 교체이므로 Phase 3은 리터럴을 **옮기기만** 한다.
* **WP**: 이 Phase에 직접 걸리는 것 -- WP-01(283행 "만들면 반드시 배선한다. 배선할 수 없으면 사용자 승인을 받는다", U-03의 근거), WP-14(296행 "대체하면 같은 변경 단위에서 옛 함수를 삭제하고 레지스트리를 갱신한다" -- shim 삭제·레지스트리 목적지 갱신), WP-03(285행, 새 도구에 숫자 임계값을 박지 않는다), WP-11(293행, 측정 스크립트 결과 파일 append), WP-12(294행, 장시간 E-INST 실행 background). NFR-2(182행) -- 캐시 정의가 이동으로 둘이 되지 않을 것(§3 판정 CACHE-ID).

### 0.4 이 Phase에 배정된 백로그·보류 항목(실측)

| 항목 | 출처 | Phase 3 관련성 | 처리 제안 |
|---|---|---|---|
| **레지스트리 §7 `보류(Phase 3)` 9행** | 레지스트리 495·505·509~515행 [M4] | 직접. `validate_theta_declaration_order`, `find_idiom_matches`, `DiodeStackMember`, `DiodeStack`, `find_diode_stacks`, `audit_theta_root_direction`, `propose_theta_kcl_gap_fill`, `apply_theta_kcl_gap_fill`, `apply_device_roles_gap_fill` | §9 사용자 결정 UD-3 |
| **B11** | `.ai/context.md` 14883행 "백로그 B11(Phase 3): extract_selftest scan이 비재귀(root.glob) -- 모듈이 하위 디렉터리로 내려가면 D2가 조용히 통과" [M3] | 조건부. `tools/migrate/extract_selftest.py:645` `root.glob("*.py")` 실측 [M5] | 이 design이 **평면 배치**(N3.10 표의 파일이 전부 `assets/` 바로 아래)를 고정하면 해당 없음. 판정 LAYOUT-FLAT(§3)로 닫는다 |
| B28 | 14976행 "V3 게이트 도구 mutate_changed.py가 .git 없는 사본에서 test를 돌려 … 변이 2060개 전부 '생존'(인프라 결함)" | 간접(선행). Phase 3 card 전부가 V3를 탄다 | 이미 다음 작업으로 잡혀 있음(14990행). Phase 3 착수 전 병합이 전제(§7) |
| B19·B21·B24·B26 | 14934·14939·14954·14963행 | **Phase 3 아님**. B19 = 회로 해석 공동분석, B21 = "Phase 4 공동분석", B24 = "(Phase 4)", B26 = "Phase 4 후보"(14972행) | Phase 3 범위 밖. 단 B26 때문에 레지스트리 §2의 7행이 '정본 후보'로 남아 있음(레지스트리 40·42·43·53~56행) -- Phase 3은 이동만 하므로 '후보' 표기를 그대로 옮긴다(이동이 정본 확정이 아니다) |
| B22·B27 | 14943·14966행 | 문서/테스트. Phase 3 아님 | 범위 밖. 다만 B22(c)의 references 문서 위치 안내(`function-selection-map.md` 등)는 이동으로 더 낡으므로 F-card의 '문서 호출부 목록'에 넣을지 §9 기본값으로 정함 |

---

## 1. 범위 (N9.2-1)

구현하는 것(계획 N6.1 Phase 3 행 + N3.10 + 다른 design이 넘긴 것):

1. **이관표 확정**: 레지스트리 '이관 목적지' 열을 N3.10의 10모듈 이름으로 재생성하고, 계층 규칙(import는 작은 번호 쪽으로만, 순환 0)을 **이동 전에** 계산으로 만족시키는 함수→모듈 배정. (N3.10 517행·N9.1)
2. **이동**: 엔진 소스 `sizing_recipe.py`(12,015줄)·`stick_diagram.py`(9,018줄)·`topology_library.py`(520줄)·`design_report.py`(316줄)의 최상위 정의를 MOD1~MOD9로 옮긴다(모듈 하나당 이동 전용 커밋) [M6].
3. **MOD10 진입점**: `run_gmid_design_pipeline` -- 현재 저장소에 **정의가 없다**(`git grep run_gmid_design_pipeline -- '*.py'` 0건) [M7]. `gate_config.json`의 `reachability_roots.after_phase3` 첫 항목이 이 함수다 [M8].
4. **shim과 삭제**: `sizing_recipe.py` 재수출 shim → 추적 호출부 갱신 → 삭제.
5. **test 재배치**: `unit/test_selftest_<모듈>.py` 4개 → `unit/test_mod*.py`, 새 C9 매핑(10-test-separation 187·413행).
6. `00-common` §17이 넘긴 `optimize_full_circuit_budget` 목적지 불일치 해소.

범위 밖(명시): 함수 분할·추출(CC-7 θ 탐색부 추출은 Phase 4, `00-common` 435행), 이름 리터럴 교체(DF-23 → Phase 4/7a), D 함수 배선(Phase 4), 레지스트리 §2 '정본 후보'의 정본 확정(B26, Phase 4), 광범위 except 정리(DF-37, Phase 4).

---

## 2. 실측 현황 (이관표를 만들기 전에 드러난 사실)

### 2.1 레지스트리 목적지 열이 N3.10과 맞지 않는다 -- **이관표는 열을 그대로 읽어 만들 수 없다**

* 레지스트리 함수 행 379개의 목적지 셀을 MOD 파일 이름으로 분류하면: `gmid_sizing_engine` 114, `stick_diagram` 87, `circuit_state_graph` 61, `topology_authoring` 32, `sizing_layout_convergence` 14, `instance_report_builder` 7, `gmid_design_pipeline` 2, **어느 MOD 이름도 없는 셀 62**(`optimizer` 17행, `〃`(위와 같음) 행, `삭제 후보`, `test util`, `LUT 생성 도구 유지` 등) [M9].
* **MOD1 `gmid_lut`·MOD5 `circuit_metrics`·MOD6 `theta_search`로 가는 행이 0개다** [M9]. N3.10 표가 그 모듈의 대표 대상으로 이름을 댄 함수가 레지스트리에서는 다른 곳을 가리킨다 [M10]:

| N3.10 대표 대상 | N3.10 MOD | 레지스트리 목적지(행) |
|---|---|---|
| `GmIdLUT`, `SemiEmpiricalGmIdLUT`(+메서드 14행), `_multilinear_interp` | MOD1 | `gmid_sizing_engine` (69·73~83·278~281) |
| `lut_conditions_from_npz` | MOD1 | `circuit_state_graph S0` (497) |
| `load_topology` | MOD2 | "파싱: circuit_state_graph S0/S1 로더 / 자동채움:…" (439) |
| `require_declared_spec_source` | MOD2 | `gmid_sizing_engine` (142) |
| `solve_stacked_diode_pair` | MOD4 | `circuit_state_graph` (409) |
| `compute_metric`, `build_ac_network`, `_full_circuit_response`, `estimate_mismatch_sigma` | MOD5 | `gmid_sizing_engine` (128·306·325·105) |
| `_build_theta_evaluator` | MOD6 | "gmid_sizing_engine + circuit_state_graph…" (417) |
| `optimize_full_circuit_budget` | MOD6(탐색부) | "sizing_layout_convergence(레이아웃·row_split…" (418) |
| `search_stage_budget_L_warm_start`, `presolve_warm_start`, `_optimize_theta_slsqp`, `repair_infeasible_baseline` | MOD6 | `optimizer` (420·421·422·349) |

* 목적지 셀이 둘 이상의 모듈로 **쪼개라**고 적은 행(`+`, `파싱:/자동채움:`, `또는`)이 16개다 [M11] -- 예 `_build_theta_evaluator`, `load_topology`, `propagate_topology_forced_currents`, `_full_circuit_response`, `synthesize_l_class_thetas`. 이동 전용 규칙(AST 해시 동일)으로는 함수를 쪼갤 수 없다.
* 레지스트리에 행이 없는 최상위 정의: `sizing_recipe` 3(`knee_L_for_kind`·`feasible_L_window`·`derive_role_L`), `stick_diagram` 23(`FingerWidthVerdict`·`check_euler_condition`·`search_shared_finger_w`·`pack_floorplan_grouped` 등) [M12]. 모듈 수준 상수·레지스트리 dict(`_METRIC_UNITS`, `_THETA_FEED_REGISTRY`, `_DEFAULT_RAIL_HI/LO` 등 최상위 대입 30개 중 다수)는 레지스트리 표 대상이 아니다 [M6·M13].
* 레지스트리 머리(3행): "작성 2026-09-14, 기준 커밋 78b58c6. 계획서 §13(v4.44)의 부속 문서" -- 목적지 열은 10모듈 표(N3.10) 이전 판의 이름(`optimizer` 등)을 쓴다(인용).
* 계획 문장과 레지스트리가 서로 반대인 행: `run_harness._spec_*`·`SPECS`는 레지스트리 "topology_authoring.py(-> json)"(392~395행) 대 계획 532행 "`canonical_spec()`/`SPECS`는 `workspaces/run_harness.py`에 남고" -- 계획이 우선(§8 규칙 A-1).

### 2.2 초안 배정만으로도 계층 위반이 남는다 -- 이동 전에 해소 규칙이 필요

초안 배정(N3.10 대표 대상 우선 → 레지스트리 첫 MOD 이름 → `optimizer`는 MOD6 → `_metric_*`는 MOD5, `optimize_full_circuit_budget`는 MOD8)으로 최상위 정의 사이 이름 참조를 세면 **큰 번호로 향하는 참조 64개**다 [M14]. 쌍별: MOD2→MOD3 17, MOD3→MOD4 14, MOD3→MOD7 9, MOD4→MOD5 8, MOD2→MOD7 6, MOD4→MOD7 3, MOD6→MOD8 2, 그 밖 1씩 [M14]. 대표 원인:

| 원인 | 실측 | 해소 방향(§8 규칙) |
|---|---|---|
| `load_topology`(N3.10 MOD2)가 구조 자동채움을 부른다 | 본문이 `propose_device_roles_gap_fill`·`propose_vertical_stack_id_gap_fill`·`find_authoritative_sizing_devices`·`Transistor`·`check_topology_name_uniqueness`를 참조(`stick_diagram:8550-8739`) [M15]. `propose_device_roles_gap_fill`은 다시 `find_matching_candidates`·`find_structural_symmetry_candidates`(S1 구조 유도)를 부른다 [M15] | 규칙 A-3: 함수를 쪼갤 수 없으므로 `load_topology`를 자기 피호출 중 가장 높은 모듈 이상에 둔다 → **N3.10 표 개정 요청**(MOD2 대표 대상에서 `load_topology` 제외, MOD3로). 쪼개기(R2 '파싱/자동채움 분리')는 6a |
| `Transistor` 레코드가 레지스트리상 "stick_diagram 유지"(359행)인데 MOD2·MOD3 함수가 만든다 | MOD3→MOD7 9건 중 다수 [M14] | 규칙 A-2: 데이터 레코드는 가장 낮은 소비자 모듈로 내린다 |
| `_hr_resolve_vertical_group` 등 `_hr_*`가 레지스트리상 `circuit_state_graph`인데 사이징 함수(`width_from_id_density`·`lut_vdsat_headroom`·`allocate_stack_headroom`)를 부른다 | 이 함수 하나가 위반 9건 [M14] | 규칙 A-1: N3.10 MOD4 대표 대상이 `_hr_*`를 명시(524행) → MOD4 |
| `optimize_full_circuit_budget`가 레이아웃 함수를 부른다 | `stick_diagram` 8개(`assign_finger_geometry`·`run_topology_pipeline`·`repair_matching_safety`·`split_into_stacks`·`audit_row_split`·`apply_explicit_row_split`·`rebuild_floorplan`·`check_stick_diagram_coverage`)와 `run_topology_pipeline_with_finger_fixup`(MOD8)을 참조(`sizing_recipe:9075-9527`) [M15] | **`00-common` §17 불일치 해소**: Phase 3에서는 통째로 **MOD8**. MOD6에 두면 MOD6→MOD7·MOD8 위반. 탐색부는 CC-7이 추출해 MOD6으로(435행과 일치) |
| `validate_theta_declaration_order`(N3.10 MOD2)가 `_build_shared_current_joint_plan`·`_shared_current_groups_from_compensation`을 부른다 | [M15] | 규칙 A-3: 피호출이 MOD3 이상이면 이 함수도 MOD3 이상 → N3.10 개정 요청에 포함. 단 이 함수는 §7 `보류(Phase 3)` D 행이라 UD-3 결정이 먼저 |

→ **결론**: "레지스트리 열에서 이관표를 생성"(517행)은 열을 먼저 고쳐야 성립한다. 이 design은 열 재생성 규칙(§8)과 **계층 사전 검사 도구**(이동 전 배정만으로 위반·순환을 계산)를 첫 card로 둔다.

### 2.3 현재 엔진 모듈 사이 import와 이동 위험 요소

* 모듈 사이 import(함수 안 import 포함 AST 전수): `sizing_recipe` → `stick_diagram`·`topology_library`, `design_report`·`audit_current_forced`·`topology_to_markdown` → `stick_diagram`, `stick_diagram` → 없음 [M16]. 명시 목록: `sizing_recipe.py:1411`(`from topology_library import …`), `:5302`(`from stick_diagram import (Transistor, load_topology, …`) [M17].
* 모듈 수준 가변 상태: `global` 문 0개, `lru_cache` 는 `topology_library` 2곳, 모듈 dict 캐시 3개(`sizing_recipe.py:2391 _KNEE_L_CACHE`, `:2530 _FEASIBLE_L_WINDOW_CACHE`, `:7697 _ACHIEVABLE_BOUND_CACHE`) [M18]. 재바인딩이 없으므로 이름 재수출은 같은 객체를 가리킨다 -- 이동 시 소유 함수와 같은 모듈로 옮기면 캐시가 둘로 갈라지지 않는다(판정 CACHE-ID).
* test의 `monkeypatch`/`setattr`로 엔진 모듈 속성을 바꾸는 곳: `tests/**`(probes 제외) 0건 [M18]. (있으면 shim 이름을 패치해도 새 모듈 안 호출에는 안 닿는 위험이 있었다.)

### 2.4 게이트 도구가 '이동'을 '새 정의'로 본다 -- Phase 3 착수 전 게이트 변경이 필요

* V3 `mutate_changed.py` `changed_defs(base_src, head_src)`(50~62행)는 **같은 경로**의 base 소스와만 비교한다(323행 `git show <base>:<path>`, 없으면 `None` → 전부 새 def) [M19]. 새 파일로 옮긴 def는 해시가 같아도 V3 대상이 된다. 계획 533행 "해시가 같은 함수는 V3 대상에서 뺀다"가 도구에 구현돼 있지 않다.
* V7 `reachability.py`: "새 `def`(base에 없던 (파일, qualname))"(모듈 docstring 5행) [M19] -- 옮긴 def는 전부 새 def. 운영 경로에서 도달 못 하는 옮긴 D 함수(§7 `보류(Phase 3)` 9개 포함)가 V7 FAIL.
* V6 `source_lint.py`: "같은 단위(함수 qualname, 모듈 최상위)의 항목 수가 늘었다"(모듈 docstring 5행), `compare(path, base_src, head_src)`(212행) [M19] -- 새 파일의 기존 숫자 리터럴·광범위 except가 전부 '새 항목'.
* `import_layering.py`는 N3.10 표를 계획서에서 직접 읽고 **표에 있고 저장소에 있는 파일만** 본다(63행). 지금 존재하는 표 파일은 `stick_diagram.py`(MOD7) 하나다 [M20]. `sizing_recipe.py`·`topology_library.py`·`design_report.py`는 표에 없어 검사 밖이다.
* AST 해시 동일 증명 도구(계획 1018행 DoD "이동 커밋마다 AST 해시 동일")는 저장소에 없다(`git ls-files | grep -i ast_hash` 0건) [M21]. `mutate_changed.def_hash`(46~47행, docstring 제외 `ast.dump` sha256)가 같은 정의를 쓰므로 재사용 후보.

### 2.5 추적 파일 호출부(shim 삭제 전에 갱신할 대상)

엔진 모듈(`sizing_recipe`·`stick_diagram`·`design_report`·`topology_library`)을 줄 머리 `import`/`from`으로 가져오는 **추적** `.py` [M22]:

| 위치 | 파일 수 |
|---|---|
| `skills/analog-gmid-design/assets/` 루트(엔진·도구) | 4 |
| `assets/tests/unit` | 10 |
| `assets/tests/probes` | 27 |
| `assets/tests/contracts` | 2(줄 머리 import) + `importlib.import_module("sizing_recipe")` 방식 다수(6개 파일이 문자열 `sizing_recipe` 포함) |
| `assets/tests/tools` | 2 |
| `assets/tests/conftest.py` | 1 |
| `workspaces/run_harness.py` | 1 |
| `workspaces/current-reuse-telescopic-ota-report/**` | 27 |
| `workspaces/two-stage-ota-report/**` | 4 |
| `.ai/verification/**/scripts` | 4 |
| `docs/03-analysis/**` | 1 |

* **U-03 문언과 실측의 차이**: U-03은 "추적되지 않는 workspaces 스크래치"를 묻지만, `workspaces/`의 진단 스크립트 31개는 **추적 파일**이다 [M22]. 추적되지 않는 `workspaces/*.py`는 1개(`smoke_run_harness_session18_save.py`, `sizing_recipe`/`stick_diagram` 문자열 2회) [M23]. N3.10 534행 문언대로면 31개를 전부 갱신해야 shim을 지울 수 있다 → §9 UD-1.
* 파일 이름에 묶인 계약 test(모듈 경로를 문자열로 가진 것) [M24]: `contracts/test_ic5.py`(49~68행 `(파일, 함수)` 표 20행 -- `("sizing_recipe.py", "check_quasi_static")` 등), `test_d_delete_dead.py:74`·`test_d_move_tests.py:73` `_REQUIRED_ENGINE_FILES = ("sizing_recipe.py", "stick_diagram.py")`, `test_dup_w_calc.py:56·442`, `test_df35_harness_paths.py:206`, `test_d_delete_telescopic.py:117`, `test_ts6_dead_probes.py:60` `_SIZING_RECIPE`, `test_ts3_no_print_verdicts.py:29` `_LEGACY_SCRIPTS`(재배치 대상 파일 이름). 이 test들은 함수가 옮겨지면 base에서 통과하던 것이 병합본에서 깨지므로 **equivalence 판정(test 불변, 양쪽 PASS)을 막는다** → 이동 전 test 선행 card(T0).
* 게이트 도구의 엔진 파일 이름: `tools/gates/*.py`(redteam 제외)에 `sizing_recipe`/`stick_diagram` 참조는 `test_lint.py:161` docstring 1건뿐이고 `gate_config.json`은 `after_phase3` 루트만 가진다 [M25]. `role_paths.py:61` 소스 분류 glob은 `skills/analog-gmid-design/assets/*.py`라 새 모듈도 소스로 분류된다 [M25].

---

## 3. 판정식 (N9.2-3)

숫자를 박지 않는다(WP-03). 모두 `영역: 없음(스키마)`. 20-dead-code-dup §3의 E-LIB·E-INST는 **그 정의를 인용**해 그대로 쓴다(재서술하지 않는다).

| ID | 판정 | 식 | 입력 |
|---|---|---|---|
| E-LIB / E-INST | 동작 보존 | `20-dead-code-dup` §3 정의 그대로 | library 회로, 하네스 |
| MOVE-AST | 이동 동일성(계획 533·1018행) | 이동 card의 base 트리 최상위 정의 집합 B와 병합본 트리의 정의 집합 H에 대해: 이관표가 이 card에 배정한 정의 d마다 `def_hash_B(원래 파일, d) = def_hash_H(목적 모듈, d)`(docstring 제외 `ast.dump` sha256 = `mutate_changed.def_hash`와 같은 정의), 그리고 병합본 diff에서 **정의 본문 밖**에 바뀐 줄은 import 문·재수출 목록뿐 | 이관표 + base/head |
| MOVE-TOTAL | 정의 보존 | Phase 전 B 전체(엔진 5모듈의 최상위 def·class·대입 이름)와 Phase 후 H 전체가 이름·해시로 1:1(사라진 것 0, 새로 생긴 것은 MOD10 진입점과 재수출 바인딩뿐) | 누적 |
| LAYER | 계층 | `import_layering.py --root <iso>` exit 0 **그리고** 아래 PLAN-LAYER가 exit 0 | 병합본 |
| PLAN-LAYER | 이동 전 계층 사전 검사 | 이관표 배정 σ에서 최상위 정의 사이 참조 그래프를 모듈 그래프로 접은 것에 `σ(u) < σ(v)`인 참조 u→v가 0개, 모듈 순환 0 | 이관표 + base 소스 |
| ORDER | 중간 상태 순환 0 | card k 병합본에서 새 MOD 파일이 import하는 모듈 ⊆ {번호가 작은 MOD} (잔여 `sizing_recipe`·`topology_library`·`design_report`를 import하지 않는다) | card별 병합본 |
| SHIM | 재수출 정확성 | `sizing_recipe`(shim)의 모든 공개·`_` 심볼 s에 대해 `getattr(shim, s) is getattr(목적 모듈, s)`(객체 동일성 -- 사본 아님), `import *` 0 | 병합본 |
| CACHE-ID | 캐시 단일성(NFR-2) | 모듈 수준 캐시(§2.3의 3개 + `lru_cache` 2곳)마다 그것을 읽고 쓰는 모든 함수가 같은 모듈에 있거나, 다른 모듈에서는 같은 객체를 import(`is` 동일) | 병합본 |
| GONE-SHIM | shim 삭제 | 마지막 card 병합본에서 `sizing_recipe.py` 없음, 추적 `.py`에서 `sizing_recipe` import 0(UD-1·UD-2가 정한 제외 집합 밖) | 병합본 |
| REG-DEST | 레지스트리 = 실제 위치(1018행) | 레지스트리 모든 행의 목적지 셀이 MOD 파일 이름 하나이고, 그 이름이 병합본에서 그 정의를 가진 파일과 같다(`reg_check.py` 확장) | 레지스트리 + 병합본 |
| LAYOUT-FLAT | 평면 배치(B11 닫기) | MOD1~MOD10 파일이 전부 `assets/` 바로 아래(하위 디렉터리 0) | 병합본 |
| ENTRY | MOD10 진입점 | `gmid_design_pipeline.run_gmid_design_pipeline`이 존재하고 `workspaces`를 import하지 않으며(532행), 하네스 `run()`이 그것을 부른다. E-INST 동일 | 병합본 |

---

## 4. 실패 경로 (N9.2-4)

Phase 4 전이라 N3.14 실패 클래스가 없다(`20-dead-code-dup` §4와 같은 상황, 인용).

| ID | 경우 | 결과 | 처리 |
|---|---|---|---|
| F1 | PLAN-LAYER FAIL(배정만으로 위반) | 이동하지 않는다 | 규칙 A-1~A-4로 배정을 고치고, 규칙으로 안 풀리면 N3.10 개정 요청(UD-4) |
| F2 | MOVE-AST FAIL(옮기며 본문이 바뀜) | V2 FAIL | card 되돌림. 본문 수정이 필요한 이동은 Phase 3이 아니다 |
| F3 | 중간 상태 순환 import | V1 수집 오류 | 순서 재배정(더 낮은 MOD부터). 지연 import로 우회하지 않는다(우회 = skip, 메모리 원칙) |
| F4 | E-LIB/E-INST 차이 | V2 FAIL | 모듈 수준 상태(캐시·전역 dict) 분리를 먼저 의심 -- CACHE-ID로 원인 확인 |
| F5 | 게이트가 옮긴 def를 새 def로 봄(V3·V6·V7) | 판정 불가 | G1 병합 전에는 이동 card를 시작하지 않는다(§7) |

---

## 5. 인터페이스 (N9.2-2)

### 5.1 파일 배치

`A = skills/analog-gmid-design/assets`. 평면 배치(LAYOUT-FLAT): `A/gmid_lut.py` … `A/gmid_design_pipeline.py`. `A/stick_diagram.py`는 MOD7로 **남고 줄어든다**(구조 유도 함수가 MOD2·MOD3로 나간다, N3.10 527행).

### 5.2 shim·임시 재수출

* `A/sizing_recipe.py`: 이동이 진행되는 동안 **잔여 정의 + 명시 재수출 목록**. 재수출 목록은 이관표에서 도구가 생성한다(손으로 쓰지 않는다). `import *` 금지(534행).
* 기본값(원칙 유도, §9 표 D-2): `topology_library.py`·`design_report.py`도 N3.10 표에 없는 파일이라 같은 방식(내용이 MOD4·MOD9로 나간 뒤 재수출 shim → 마지막 card에서 삭제). `stick_diagram.py`는 MOD7이라 남지만, 옮겨 나간 이름의 재수출은 **임시**이고 마지막 card에서 지운다(한 이름에 import 경로 하나, WP-14).
* `audit_current_forced.py`: 레지스트리상 `render_report`는 "audit_current_forced.py" 유지(248행), `audit_topology`는 `〃`로 MOD9(389행) -- 도구로 남기고 `audit_topology`만 옮길지 이관표에서 확정(규칙 A-4).

### 5.3 MOD10 진입점

* 기본 시그니처(원칙 유도): `run_gmid_design_pipeline(spec, *, topology_path, search, output_dir)`. 하네스 `run()`의 파이프라인 몸통(`optimize_full_circuit_budget` → `run_full_circuit_audit_from_topology` → `save_instance_json` → `assemble_report_data`/`save_html_report`, `run_harness.py:444~511`)을 옮긴다 [M26]. stdout 출력·`except Exception`(512행, DF-37 Phase 4)은 하네스에 남긴다.
* `instrument`·`activations_out`은 CC-7·CC-8(Phase 4)이 더한다. **문서 불일치**: `00-common` 103행은 `search`·`output_dir`도 CC-7 몫으로 적었다 → `00-common` 개정 요청(D-5).
* 이 card는 **추출**이라 MOVE-AST가 아니라 E-INST·ENTRY로 판정한다(V3 대상).

### 5.4 새 도구(code-author 소유, `A/tests/tools/`, 그 test는 test-author -- `reg_check.py` 선례)

| 도구 | 입력 | 출력 | 판정 |
|---|---|---|---|
| `move_plan.py` | 레지스트리 + base 소스 | 이관표 JSON(정의 → MOD, 규칙 근거), 재수출 목록, PLAN-LAYER 결과, card 순서(위상 정렬) | PLAN-LAYER·ORDER |
| `move_ast_check.py` | `--base --head --plan <이관표>` | 정의별 해시 대조 | MOVE-AST·MOVE-TOTAL |
| `reg_check.py` 확장 | 레지스트리 + 병합본 | 목적지 셀 = 실제 파일 | REG-DEST |

도구는 회로·소자·넷 이름을 읽지 않는다(코드 구조만 본다 -- topology 무관). 결과는 case마다 파일 append(WP-11).

---

## 6. 이관표 생성 규칙 (N9.1 '레지스트리 목적지 열에서 생성')

우선순위(높은 것이 이긴다). 규칙은 `move_plan.py`가 적용하고 행마다 근거 규칙 ID를 남긴다.

* **A-1 계획 명시**: N3.10 표 '대표 대상' 열에 이름이 있으면 그 MOD. 계획 532행(`canonical_spec`/`SPECS`는 하네스에 남음) 포함.
* **A-2 데이터 레코드 하강**: dataclass·예외·결과 레코드(`Transistor`, `SizingContext`, `InfeasibleSizingError`, `*Verdict` 등)는 그것을 만들거나 받는 정의가 배정된 MOD 중 **가장 낮은 번호**로.
* **A-3 계층 강제**: 함수를 쪼갤 수 없으므로(이동 전용), 목적지 셀이 둘로 쪼개라고 적은 16행은 **피호출 전부를 담을 수 있는 가장 낮은 MOD**로 통째로 보낸다. 쪼개기는 그 행이 적은 담당 Phase(R2 → 6a·6b·7b, CC-7 → Phase 4)로 남긴다. A-1과 충돌하면(예 `load_topology` MOD2) A-1을 바꾸는 **N3.10 개정 요청**을 낸다(UD-4).
* **A-4 레지스트리 열**: 위 셋에 걸리지 않으면 레지스트리 목적지 셀의 MOD 이름. 옛 이름 매핑: `optimizer`(`optimizer(S3 …)` 포함) → MOD6 `theta_search`(N3.10 526행 책임 '실패 캐시, 시작점, 전역 샘플, S3'), `〃` → 위 행. `_metric_*`·metric 레지스트리 → MOD5(525행 책임 'metric 레지스트리').
* **A-5 미배정**: 레지스트리 행이 없는 26개 정의(§2.1)와 최상위 대입은 **참조하는 정의의 가장 낮은 MOD**로(상수·레지스트리 dict는 소비자 따라). 소비자가 없으면 원래 파일에 남기고 목록을 보고한다(삭제는 이 Phase가 아니다).
* 결과 확인: A-1~A-5 적용 후 PLAN-LAYER exit 0이어야 레지스트리 열을 갱신한다(D0b card).

---

## 7. 역할별 산출물 -- spec card 목록 (N9.2-5)

card 단위는 N3.12.3(674행: 이동은 모듈 하나가 한 건). id는 초안 slug.

| # | id(초안) | 대상(파일:줄은 HEAD `070cf69` 재측정) | 판정 유형 | oracle | 원칙 제약 |
|---|---|---|---|---|---|
| **G1** | `p3-gate-move-aware` | `tools/gates/mutate_changed.py:50-62·323`(V3), `reachability.py`(V7 '새 def' 정의), `source_lint.py:212`(V6) -- base 전 파일에 해시가 같은 정의가 있으면 '옮긴 정의'로 보고 V3·V6·V7 대상에서 뺀다(계획 533행 문장의 구현) | 게이트 변경(`05-role-separation` 절차, 20260929-rejudge-cache 선례) | (a) 합성 입력: 해시 같은 이동 = 제외, 이동하며 한 줄 바뀐 def = 대상, 새 def = 대상 | 게이트는 **실제로 거부**함을 먼저 보인다(메모리: 게이트 '통과' 아니라 '거부' 확인). B28 병합 뒤 |
| **T0** | `p3-tests-location-free` | 파일 이름에 묶인 계약 test 8개(§2.5 목록: `test_ic5.py:49-68` 등)를 "정의를 가진 파일을 `A/*.py` 전수에서 찾는" 방식으로 | test-only(단, 리터럴 변경은 V5 R1 승인 가능성) | (c) 이동 전 트리에서 결과 동일 + (a) 합성 트리(함수를 다른 파일로 옮긴 사본)에서도 PASS | 판정 강도를 줄이지 않는다(대상 범위 = 넓힘). 기준 약화면 승인 |
| **D0a** | `p3-move-plan-tool` | 새 `A/tests/tools/move_plan.py`·`move_ast_check.py`, `reg_check.py` REG-DEST 확장 | red-green | (a) 합성 모듈 입력(위반 있는 배정은 FAIL, 순환은 FAIL, 해시 다른 이동은 FAIL) | 새 도구 = 즉시 D1~Mk card의 판정 명령으로 배선(만들면 배선) |
| **D0b** | `p3-registry-dest` | 레지스트리 목적지 열 전 행을 MOD 이름 하나로(규칙 ID 열 추가), §7 `보류(Phase 3)` 9행 처리 열 갱신(UD-3 결과) | test-only(문서) | (d) `move_plan.py` 출력 = 레지스트리 열, PLAN-LAYER exit 0 | 숫자·이름을 손으로 쓰지 않고 도구 출력으로 |
| **M1** | `p3-move-mod1-gmid-lut` | `GmIdLUT`(`sizing_recipe:52`), `SemiEmpiricalGmIdLUT`(`:259`), `_multilinear_interp`(`:141`), `_multilinear_interp_point_multi`, `lut_conditions_from_npz`(`:4782`) 외 이관표 MOD1 전부 | equivalence | (c) MOVE-AST + E-LIB·E-INST + SHIM | CACHE-ID(LUT 조회 캐시가 둘로 갈라지지 않음) |
| **M2** | `p3-move-mod2-authoring` | `validate_metric_units`, `validate_no_legacy_vs_key`, `require_declared_spec_source`(`:7617`) 외 MOD2 전부 | equivalence | 같음 | A-3 결과에 따름(`load_topology`·`validate_theta_declaration_order`는 UD-4 결과) |
| **M3** | `p3-move-mod3-csg` | `is_diode_connected`, `true_current_mirror_groups`, `l_sharing_classes`, `_kcl_and_matching_edges`(`stick_diagram`), `propagate_topology_forced_currents`, `spec_fingerprint`, `Transistor`(A-2) 외 | equivalence | 같음 | 레지스트리 §2 '정본 후보' 표기 유지(B26 -- 이동이 정본 확정이 아니다). 이름 리터럴은 옮기기만(DF-23) |
| **M4** | `p3-move-mod4-engine` | `size_transistor`, `width_from_id_density`, `measure_L_knee`, `_hr_*`, `solve_diode_connected_vds`, `solve_stacked_diode_pair`(`:3491`), `apply_theta_feed`, `topology_library.py` 보상식 7정의 | equivalence | 같음 | 모듈 캐시 `_KNEE_L_CACHE`(`:2391`)·`_FEASIBLE_L_WINDOW_CACHE`(`:2530`) 소유 함수와 함께(CACHE-ID). `lru_cache` 2곳(topology_library) 동일 |
| **M5** | `p3-move-mod5-metrics` | `compute_metric`(`:5280`), `_METRICS_REGISTRY`(`:5083`), `build_ac_network`(`:4067`), `_full_circuit_response`(`:4970`), `estimate_mismatch_sigma`(`:3073`), `_metric_*` | equivalence | 같음 | 문자열 레지스트리(`_METRICS_REGISTRY`)는 V7 그래프가 문자열로 도달을 본다(reachability docstring) -- 이동 후 도달 불변 확인 |
| **M6** | `p3-move-mod6-theta-search` | `_build_theta_evaluator`(`:7930-8933`), `search_stage_budget_L_warm_start`(`:10088`), `presolve_warm_start`(`:10581`), `_optimize_theta_slsqp`(`:10793`), `repair_infeasible_baseline`(`:10410`), `_ACHIEVABLE_BOUND_CACHE`(`:7697`) 소유 함수 | equivalence | 같음 | 평가 커널 빌더는 CC-7 감싸기 지점(00-common 434행)이 된다 -- 본문 무변경 |
| **M7** | `p3-mod7-residual` | `stick_diagram.py`에 레이아웃 함수만 남았는지(N3.10 527행) -- 이동 없음, 검사만 | test-only | (d) 이관표 대비 잔여 목록 | 필요하면 M2·M3에 흡수(빈 card 금지) |
| **M8** | `p3-move-mod8-convergence` | `optimize_full_circuit_budget`(`:9075-9527`, 통째로 -- §2.2), `run_topology_pipeline_with_finger_fixup`, `revalidate_finger_override`, `resolve_stack_layout` | equivalence | 같음 | `00-common` §17 불일치를 MOD8로 닫고 CC-7에 넘김 |
| **M9** | `p3-move-mod9-report` | `save_instance_json` 계열(`stick_diagram`), `design_report.py` 5정의(`render_html_report` 재사용 -- 이름 그대로), `audit_topology`(A-4) | equivalence | 같음 | 레지스트리 57행 "HTML 리포트: 새로 만들지 않는다" |
| **M10** | `p3-mod10-entry` | 새 `gmid_design_pipeline.run_gmid_design_pipeline`, `workspaces/run_harness.py:422-531` `run()`이 그것을 부름 | equivalence(추출, E-INST) | (c) E-INST·E-LIB, ENTRY | 만들면 배선: 하네스가 즉시 호출, `after_phase3` 루트가 도달 |
| **T1** | `p3-test-relocate` | `unit/test_selftest_{sizing_recipe,stick_diagram,topology_library,design_report}.py` → `unit/test_mod*.py`, 새 C9 매핑, `test_ts3_no_print_verdicts.py:29` 목록 | test-only | (c) 옮기기 전후 수집 test id 집합 = 매핑, 전부 PASS | 10-test-separation 413행 |
| **F1** | `p3-callers-update` | §2.5 추적 호출부 import를 목적 모듈로(UD-1·UD-2가 정한 범위) | equivalence | (c) 호출부 파일 AST가 import 줄 외 동일 + E-INST | 스크립트 결과 파일 append |
| **F2** | `p3-shim-delete` | `sizing_recipe.py`(+ 기본값 D-2의 `topology_library.py`·`design_report.py`), `stick_diagram` 임시 재수출 제거, 레지스트리 REG-DEST, `gate_config` 루트 전환 확인 | red-green | (a) GONE-SHIM: shim 이름 import가 `ModuleNotFoundError` | WP-14(같은 변경 단위에서 옛 경로 삭제 + 레지스트리 갱신) |

**card 수: 17**(G1, T0, D0a, D0b, M1~M10, T1, F1, F2). M7이 M2·M3에 흡수되면 16.

---

## 8. 순서·의존과 병렬 준비

```
B28(진행 중 백로그) ─┐
                     ├─> G1 ─┐
T0 ──────────────────────────┤
D0a ─> D0b(UD-3·UD-4 결과 필요) ─┤
                                 ├─> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> [M7] -> M8 -> M9 -> M10 -> T1 -> F1 -> F2
```

* **병렬로 준비 가능(서로 독립, 병합 순서만 지킴)**: G1(게이트), T0(test), D0a(도구). 셋 다 엔진 소스를 바꾸지 않는다.
* **순차 필수**: M1~M10은 앞 card 병합본이 다음 card의 base다(모듈 k를 만들 때 번호가 작은 모듈이 이미 있어야 ORDER가 성립). 단 **작성 전 실측(spec card '## 작성 전 실측' 절)은 D0b 이관표 한 벌로 M1~M10을 한꺼번에 미리 뽑아 둘 수 있다** -- 이관표가 고정되면 card마다 옮길 정의 목록·줄 범위·재수출 목록이 결정적이다(메모리 card 처리 속도 규칙: 재측정은 쓰는 자리에서, 정의 목록은 도구 출력으로).
* M 순서가 번호순인 이유: 번호가 큰 모듈만 작은 모듈을 import하므로, 작은 번호부터 만들면 매 card 병합본에서 새 파일이 잔여 `sizing_recipe`를 import할 일이 없다(ORDER). `stick_diagram`(MOD7)이 이미 존재하므로 M2·M3가 `stick_diagram`에서 가져가는 정의를 `stick_diagram`이 다시 import하는 것은 아래 방향이라 허용된다.
* T1은 M 전부 뒤(selftest 파일이 가리키는 모듈이 확정된 뒤), F1·F2는 맨 끝.

---

## 9. 착수 조건과 결정 (N9.2-7)

### 9.1 착수 조건

* 공통(991행): 이 문서의 사용자 승인(DEC-51), **Phase 2 DoD PASS** -- 현재 Phase 2 남은 것: P9(`dup-kcl-edges`), P10(`df23-inventory`), DoD E0~E5(`20-dead-code-dup` §10). P3c는 보류(B21, `.ai/context.md` 14938행). Phase 2 DoD 판정에서 P3c 보류를 어떻게 셀지는 Phase 2 쪽 결정이다.
* U-03(1078행): 아직 승인 기록 없음(`.ai/approvals`에 u03·30-module 관련 파일 0) [M27].
* 게이트 선행: B28(V3 도구 `.git` 없는 사본 결함)과 G1.

### 9.2 사용자 결정 (진짜 사용자 몫 -- 삭제·배선 승인, 회로 해석, 공유 범위, 게이트·계획 개정 승인)

| ID | 결정 | 기본안(원칙에서) | 왜 사용자 몫인가 |
|---|---|---|---|
| **UD-1** | U-03 범위 재정의: 추적된 `workspaces/` 진단 스크립트 31개(+ 추적 안 된 1개)를 갱신할지, 깨지게 둘지 | 계획 534행 문언대로 추적 31개는 import만 갱신(F1), 추적 안 된 1개는 U-03 기본안대로 허용 | U-03이 묻는 대상(추적 안 됨)과 실측(대부분 추적됨)이 다르다. 스크래치 보존/폐기는 사용자 공유 설정 |
| **UD-2** | `.ai/verification/**/scripts` 4개·`docs/03-analysis/**` 스크립트를 갱신할지 | 갱신하지 않는다(판정 기록은 그 base 커밋에서 재실행되는 증거 -- 고치면 기록이 바뀐다). GONE-SHIM 제외 집합에 명시 | 판정 기록의 불변성·보존 정책 |
| **UD-3** | 레지스트리 §7 `보류(Phase 3)` 9행: 옮김(D 유지, 배선은 Phase 4) / 삭제 / 배선. 계획 535행은 "등급 D 함수는 옮기기 전에 처리한다(Phase 2)"라 적었는데 U-02가 Phase 3으로 넘겼다 | 8개(`validate_theta_declaration_order`, `find_idiom_matches`, `audit_theta_root_direction`, `propose_theta_kcl_gap_fill`, `apply_theta_kcl_gap_fill`, `apply_device_roles_gap_fill`, `DiodeStack`, `DiodeStackMember`)는 **옮기되 D 유지·처리 '보류(Phase 4 배선 판단)'**, `find_diode_stacks`는 ★ diode 정의 공동분석(레지스트리 39행)이라 **6a로 넘김**. G1이 해시 같은 이동을 V7에서 빼므로 추가 면제 불필요 | 삭제·배선 승인은 사용자 몫(WP-01), `find_diode_stacks`는 회로 해석 |
| **UD-4** | N3.10 표 개정: `load_topology`를 MOD2 → MOD3(계층 강제 A-3), `validate_theta_declaration_order` 동반 여부, `optimize_full_circuit_budget` 대표 대상을 MOD6 '탐색부'로 둔 채 Phase 3 위치 = MOD8 명시 | §2.2 계산 결과대로 개정. 대안(함수 분할)은 이동 전용 규칙 위반이라 제외 | 계획서 표 변경은 승인 대상(plan_tables) |
| **UD-5** | G1 게이트 변경 승인 | §7 G1 | 게이트 변경은 `05` 절차상 사용자 승인 |
| **UD-6** | T0에서 `weakening_diff`가 리터럴 변경을 '기준 약화'로 잡으면 V5 R1 승인 | 판정 대상 범위를 넓히는 변경임을 근거로 승인 요청 | 기준 변경 승인(DEC-40) |

### 9.3 원칙 유도 기본값(이 design 승인으로 확정 -- 따로 묻지 않는다)

| ID | 기본값 | 근거 |
|---|---|---|
| D-1 | 평면 배치, B11은 LAYOUT-FLAT으로 해당 없음 처리 | N3.10 표 파일 이름이 전부 경로 없는 이름, `extract_selftest.py:645` 비재귀 |
| D-2 | `topology_library.py`·`design_report.py`도 shim 경유 후 삭제, `stick_diagram` 재수출은 임시 | N3.10 표에 없는 파일, 파일당 한 책임, WP-14 |
| D-3 | `optimize_full_circuit_budget` → MOD8(통째) | 레이아웃 함수 8개 + MOD8 함수 참조(§2.2), 00-common 435행 |
| D-4 | 쪼개라고 적힌 16행은 쪼개지 않고 통째로(A-3), 쪼개기는 원래 담당 Phase | 이동 전용 규칙(533행) |
| D-5 | MOD10 시그니처 `(spec, *, topology_path, search, output_dir)`; `00-common` 103행 개정 요청(오케스트레이터 문서 수정) | 하네스 몸통 추출에 탐색 설정·출력 경로가 필요 |
| D-6 | `canonical_spec`/`SPECS`/`_spec_*`는 하네스에 남김(레지스트리 392~395행 목적지 정정) | 계획 532행 |
| D-7 | 새 도구 3개는 `A/tests/tools/`(code-author), test는 test-author | `reg_check.py` 선례, 00-common 성능 도구 소유 규칙 |
| D-8 | references 문서(`function-selection-map.md` 등)의 모듈 위치 안내는 F2에서 grep 목록만 보고하고 갱신은 B22 별도 card | B22가 이미 그 card |

---

## 10. DoD 측정 명령 (N9.2-6)

auditor가 Phase 3 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행. `PT`는 `10-test-separation` §10 정의 인용.

| ID | N6.2 `3` 조건 | 명령 | 통과 기준 |
|---|---|---|---|
| E0 | MOD1~MOD10 존재 | `$PY -c "import os,sys; A=r'<iso>/skills/analog-gmid-design/assets'; m=['gmid_lut','topology_authoring','circuit_state_graph','gmid_sizing_engine','circuit_metrics','theta_search','stick_diagram','sizing_layout_convergence','instance_report_builder','gmid_design_pipeline']; miss=[x for x in m if not os.path.isfile(os.path.join(A,x+'.py'))]; print(miss); sys.exit(1 if miss else 0)"` (목록은 계획 N3.10 표에서 `import_layering.mod_table`로 읽는 판이 정본 -- 위는 설명용) | exit 0 |
| E1 | import 계층 위반 0 | `$PY <iso>/tools/gates/import_layering.py --root <iso>` | exit 0, `present`에 10개 |
| E2 | 이동 커밋마다 AST 해시 동일 | Phase 3 이동 card(M1~M9)마다 `$PY <iso>/…/tests/tools/move_ast_check.py --root <iso> --base <card base> --head <card M 커밋> --plan <이관표>` + 누적 `--base <Phase 3 시작> --head HEAD` (MOVE-TOTAL) | 전부 exit 0 |
| E3 | `sizing_recipe.py` 삭제 | `git -C <iso> cat-file -e HEAD:skills/analog-gmid-design/assets/sizing_recipe.py` 가 실패 + `git -C <iso> grep -l -E "^\s*(import|from)\s+sizing_recipe\b" -- '*.py'` 결과 ⊆ UD-2 제외 집합 | 둘 다 |
| E4 | 레지스트리 목적지 = 실제 위치 | `$PY <iso>/…/tests/tools/reg_check.py --registry <iso>/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root <iso>` (REG-DEST 확장판) | exit 0 |
| E5 | 동작 보존(N6.3 동작 보존 Phase) | `PT` 전체 + E-LIB·E-INST 재측정 | Phase 2 DoD와 같은 해시 |

---

## 11. 열린 질문 (N9.2-8)

없음(목표). §9.2의 UD-1~UD-6은 열린 질문이 아니라 착수 전 사용자 결정 대기 항목이다. 이 초안 작성 중 드러난 **계획·문서 개정 요청**:
1. N3.10 표 대표 대상과 레지스트리 목적지 열의 불일치(§2.1 표 9행) -- 517행 "레지스트리 열이 정본"이 성립하려면 열 재생성(D0b)이 먼저다.
2. U-03 문언(추적 안 됨)과 실측(workspaces 진단 스크립트 31개가 추적됨)의 차이(UD-1).
3. 계획 535행 "D 함수는 Phase 2에서 처리"와 레지스트리 `보류(Phase 3)` 9행의 충돌(UD-3).
4. `00-common` 103행 MOD10 인자 담당(D-5).
5. N3.12.3 686행 equivalence 정의와 MOD10 추출 card의 판정(AST 해시가 아니라 E-INST) -- Phase 3 안의 유일한 비이동 card임을 계획 Phase 3 행 '판정 유형' 칸에 적을지.

---

## 부록 A. 측정 명령 (모두 읽기 전용, HEAD `070cf69`)

`SP` = 스크래치패드 `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/fe0941dd-c225-43df-8d44-48951ea014a8/scratchpad`, `R` = 저장소 루트.

| # | 명령 | 결과 요지 |
|---|---|---|
| M0 | Glob `docs/02-design/features/gain-budget-gmid-sizing*` | 00·05·10·20 네 개 |
| M1 | Read plan 985~1035행 | N6.1·N6.2 표 |
| M2 | `git -C R log --oneline -5` (gitStatus 스냅샷) | 57781a7 DF-35, 070cf69 DF-36 spec card |
| M3 | Read `.ai/context.md` 14900~14993행 | B11·B19~B28 정의, 다음 작업 |
| M4 | `grep -n "보류(Phase 3)" docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` | 9행 |
| M5 | `grep -n "glob" R/tools/migrate/extract_selftest.py` | 645행 `root.glob("*.py")` |
| M6 | `wc -l R/skills/analog-gmid-design/assets/*.py`; `SP/p3_measure.py` `toplevel_counts` | SR 12015줄(Class 13·Func 174·Assign 30), SD 9018줄(Class 28·Func 131·Assign 8), topology_library 7, design_report 5+1 |
| M7 | `git -C R grep -n "run_gmid_design_pipeline" -- '*.py'` | 0건 |
| M8 | Read `R/tools/gates/gate_config.json` | `after_phase3` 루트 |
| M9 | `$PY SP/p3_measure.py` → `registry_dest_mod_counts`, `registry_unmapped` | §2.1 분포, MOD1·5·6 0행 |
| M10 | 같은 JSON `plan_rep_vs_registry` | §2.1 표 |
| M11 | `awk -F'|' '/^\| `/ && NF>=5 {d=$4; if (d ~ /\+|파싱|\/ 자동|또는/) n++} END{print n}' <레지스트리>` | 16 |
| M12 | 같은 JSON `coverage` | SR 3, SD 23 미등록 |
| M13 | 같은 JSON `unassigned_toplevel`, `SP/p3_assign.py` `unassigned` | 미배정 34(대입 포함) |
| M14 | `$PY SP/p3_assign.py` → `upward`, `upward_by_pair`, `upward_by_from` | 64, 쌍별 분포 |
| M15 | `$PY SP/p3_refs.py` | `optimize_full_circuit_budget` 9075-9527 SD 8개 참조, `load_topology` 8550-8739, `validate_theta_declaration_order` 6296-6388 |
| M16 | `SP/p3_measure.json` `current_intra_imports` | SR→SD·TL, DR·ACF·T2M→SD |
| M17 | `grep -n "^\s*\(from\|import\) \(stick_diagram\|topology_library\|sizing_recipe\|design_report\)" R/skills/analog-gmid-design/assets/*.py` | 1411·5302 등 |
| M18 | `grep -n "^\s*global "`, `grep -c lru_cache`, `git grep -n -E "monkeypatch\|setattr\(" -- tests`(probes 제외), 모듈 dict 캐시 grep | 0 / TL 2 / 0 / 2391·2530·7697 |
| M19 | Read `R/tools/gates/mutate_changed.py` 1~65·323행, `reachability.py` 1~30행, `source_lint.py` 1~25·212행 | 같은 경로 비교 |
| M20 | Read `R/tools/gates/import_layering.py` | 표∩존재 파일만 |
| M21 | `git -C R ls-files \| grep -i "import_layering\|ast_hash\|layering"` | `import_layering.py`만 |
| M22 | `git -C R grep -l -E "^[[:space:]]*(import\|from)[[:space:]]+(sizing_recipe\|stick_diagram\|design_report\|topology_library)\b" -- '*.py'` 디렉터리별 집계 | §2.5 표 |
| M23 | `git -C R status --porcelain workspaces`; `grep -c "sizing_recipe\|stick_diagram" <해당 파일>` | 추적 안 된 .py 1개, 2회 |
| M24 | `git -C R grep -n -E "\"(sizing_recipe\|stick_diagram\|…)\.py\"" -- skills/analog-gmid-design/assets/tests` | §2.5 목록 |
| M25 | `git -C R grep -n "sizing_recipe\|stick_diagram" -- tools/gates ':!tools/gates/redteam'`; `grep -n "assets/\*" R/tools/gates/role_paths.py` | test_lint 161 docstring 1건, role_paths 61 |
| M26 | Read `R/workspaces/run_harness.py` 422~536행 | run() 몸통 |
| M27 | `ls R/.ai/approvals \| grep -i -E "u03\|u-03\|30-module\|phase3"` | 0건 |

주의(측정 한계): M14의 64건은 **초안 배정**(§2.2에 적은 규칙) 기준이고 최상위 정의 사이 이름 참조(`ast.Name`)만 센다. 속성 호출(`x.f`)·문자열 레지스트리 경유 참조는 세지 않았다 -- 정식 PLAN-LAYER는 D0a 도구가 V7과 같은 그래프(`reachability.build_graph`)로 재측정한다.
