# Phase 3 design 30 -- UD-0이 덮는 문서 개정 문안 (초안, 저장소 미반영)

대상 design: `_drafts/draft_phase3_design_v7.md`(정식 경로 `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md`). 3차 검토 `review3_phase3_v5.md` B4 대응, 4차 검토 m2·N1(v7 -- §2).
기준: gate `master` `7535799`(2026-10-01, 읽기 전용 복제본 `C:/g73/repo`에서 줄 번호·원문 확인), `a796468`에서 다시 확인(아래 '사전 적용 실측' 끝 -- v7에서 §2 새 문안을 고친 뒤 재실행). 오케스트레이터가 **design 30 커밋과 같은 커밋**에 아래 교체를 그대로 넣고,
승인 기록(`20260930-30-module-split-design`, `target_kind: diff`)의 `diff_path`가 design 30·계획서·`00-common`·`10-test-separation` 네 경로를 덮는다(선례 `20260922-10-test-separation-design`).
N3.10·N3.12.3은 `plan_tables_hash` 입력이 아니다(`merge_gate.py:107-176`: N4.1·N4.2·N6.1·N3.12.2만) -- `plan_tables` 승인은 필요 없다(3차 검토 실측).

**이 문서가 덮지 않는 것**:
* 계획 N3.10 **533행**의 "V6·V7의 '새'도 같은 규칙" 문장과 design 05 §10 V3·V6·V7 행 -- G1 spec card 계약 13(G1 승인 = UD-5)이 G1 spec card와 같은 커밋에 넣는다.
* D0b가 B26-1·B34 병합본에서 **새로 계산하는** N3.10 개정(아래 §1 밖의 `conflicts`·`upward`) -- UD-0은 위임받지 않는다. 나오면 D0b가 멈추고 그 diff를 따로 사용자 승인(`target_kind: diff`)으로
  받는다(design 30 §9.1·D-11).

교체 표기: **현재**(파일:줄, 원문 그대로) → **새 문안**(그 줄 전체를 바꾼다). 표 행은 셀 수를 유지한다.

---

## §1. 계획 N3.10 표 (`docs/01-plan/features/gain-budget-gmid-sizing.plan.md`)

근거: design 30 §6.2 A-3(계층 강제 계산 결과)·D-3·D-11·D-19. A-1(계획 명시)은 '대표 대상' 열의 **백틱 식별자**를 그 MOD로 배정하므로(D0a 계약 2), 이동 목적지를 바꾸려면 백틱 토큰을
옮겨야 한다 -- 특히 MOD6의 `` `optimize_full_circuit_budget` 탐색부 ``는 지금 문언대로면 함수 전체를 A-1로 MOD6에 보내 MOD8 함수로의 위쪽 참조를 만든다(v6 모의 근사 배정에서도
`optimize_full_circuit_budget` = A-1 MOD6). 그래서 MOD6 행에서는 백틱을 빼고 MOD8 행에 넣는다.

### (a) MOD2 행 -- `load_topology`·`validate_theta_declaration_order` 제거, (D-19 (가)일 때) `rail_declaration` 추가

현재 `plan.md:522`:
```
| MOD2 | `topology_authoring.py` | topology·spec 로딩, 스키마·단위·참조·선언 순서 게이트, 구조 제안 | `load_topology`, `validate_metric_units`, `validate_no_legacy_vs_key`, `require_declared_spec_source`, `validate_theta_declaration_order` |
```
새 문안 -- D-19 답이 **(가) MOD2**일 때:
```
| MOD2 | `topology_authoring.py` | topology·spec 로딩, 스키마·단위·참조·선언 순서 게이트, 구조 제안 | `validate_metric_units`, `validate_no_legacy_vs_key`, `require_declared_spec_source`, `rail_declaration`(전원 선언 접근자, B26-1). load_topology와 validate_theta_declaration_order는 MOD3 구조 유도 함수를 불러 계층상 MOD3에 둔다(Phase 3 design 30 §6.2) |
```
새 문안 -- D-19 답이 **(나) MOD3**일 때(`rail_declaration` 토큰만 없다):
```
| MOD2 | `topology_authoring.py` | topology·spec 로딩, 스키마·단위·참조·선언 순서 게이트, 구조 제안 | `validate_metric_units`, `validate_no_legacy_vs_key`, `require_declared_spec_source`. load_topology와 validate_theta_declaration_order는 MOD3 구조 유도 함수를 불러 계층상 MOD3에 둔다(Phase 3 design 30 §6.2) |
```
설명 문장의 두 함수 이름에 **백틱을 쓰지 않는다** -- 백틱 식별자는 A-1 토큰이라 MOD2·MOD3 두 행에 걸려 `conflicts`가 된다(D0a 계약 2). 책임 열은 바꾸지 않는다(MOD2에 spec 로딩·나머지 선언 게이트가 남는다).

### (b) MOD3 행 -- 두 함수 추가

현재 `plan.md:523`:
```
| MOD3 | `circuit_state_graph.py` | S0 지문, S1 구조 유도(개념당 정본), S1v, 결합 블록 | `is_diode_connected`, `true_current_mirror_groups`, `l_sharing_classes`, `l_class_owners`, `vgs_alias_map`, `_kcl_and_matching_edges`, `trace_*_branches`, `propagate_topology_forced_currents`, `spec_fingerprint` |
```
새 문안:
```
| MOD3 | `circuit_state_graph.py` | S0 지문, S1 구조 유도(개념당 정본), S1v, 결합 블록, topology 로딩(구조 자동채움을 부르므로) | `is_diode_connected`, `true_current_mirror_groups`, `l_sharing_classes`, `l_class_owners`, `vgs_alias_map`, `_kcl_and_matching_edges`, `trace_*_branches`, `propagate_topology_forced_currents`, `spec_fingerprint`, `load_topology`, `validate_theta_declaration_order` |
```
`validate_theta_declaration_order`의 목적지(v6 확정): 부르는 `_build_shared_current_joint_plan`·`_shared_current_groups_from_compensation`의 레지스트리 목적지 셀이 `circuit_state_graph S1`·
`circuit_state_graph S1 / 유도 DAG`(레지스트리 129·131행)라 A-4로 MOD3 → A-3의 max(셀 최소 MOD, 피참조 최대 MOD) = **MOD3**. v6 모의(`p3_scripts/p3v6_order_shim_sim.py`) 근사 배정에서도
이 함수의 MOD 2 초과 참조는 그 둘(MOD3)뿐이다. 책임 열의 "선언 순서 게이트"는 MOD2에 그대로 둔다(나머지 `validate_*`가 남는다).

### (c) MOD6 행 -- `optimize_full_circuit_budget` 백틱 제거

현재 `plan.md:526`:
```
| MOD6 | `theta_search.py` | 평가 커널 조립, 층 0 기둥 조립 presolve(DEC-71), 할당 층(기본 = 외층 SLSQP / 정밀 = 내층 DP·중층 좌표강하, DEC-73), 실패 캐시, 시작점, 전역 샘플, S3 | `_build_theta_evaluator`, `optimize_full_circuit_budget` 탐색부, `search_stage_budget_L_warm_start`, `presolve_warm_start`, `_optimize_theta_slsqp`, `repair_infeasible_baseline` |
```
새 문안:
```
| MOD6 | `theta_search.py` | 평가 커널 조립, 층 0 기둥 조립 presolve(DEC-71), 할당 층(기본 = 외층 SLSQP / 정밀 = 내층 DP·중층 좌표강하, DEC-73), 실패 캐시, 시작점, 전역 샘플, S3 | `_build_theta_evaluator`, θ 탐색부(CC-7이 optimize_full_circuit_budget에서 추출하는 함수 -- Phase 4, 00-common §10.1. 추출 전 함수 전체는 MOD8), `search_stage_budget_L_warm_start`, `presolve_warm_start`, `_optimize_theta_slsqp`, `repair_infeasible_baseline` |
```

### (d) MOD8 행 -- `optimize_full_circuit_budget` 추가

현재 `plan.md:528`:
```
| MOD8 | `sizing_layout_convergence.py` | 사이징↔레이아웃 수렴 루프 | `run_topology_pipeline_with_finger_fixup`, `revalidate_finger_override`, `resolve_stack_layout` |
```
새 문안:
```
| MOD8 | `sizing_layout_convergence.py` | 사이징↔레이아웃 수렴 루프 | `run_topology_pipeline_with_finger_fixup`, `revalidate_finger_override`, `resolve_stack_layout`, `optimize_full_circuit_budget`(Phase 3 위치 -- 레이아웃 함수와 MOD8 함수를 부른다. θ 탐색부는 CC-7이 MOD6로 추출) |
```

(D-19는 (a)의 `rail_declaration` 한 토큰이다 -- 답이 (나)면 그 토큰을 넣지 않고, 규칙 A-5가 `rail_declaration`을 MOD3로 보낸다. `RailDeclaration`은 어느 쪽이든 A-2로 MOD2라 표에 넣지 않는다.)

---

## §2. 계획 534행 shim 문장 (D-2·D-9, 3차 검토 B2와 같은 정합)

현재 `plan.md:534`:
```
* **shim**: `sizing_recipe.py`는 이관 중 명시 재수출 목록(인벤토리에서 생성, `_` 접두 심볼 포함, `import *` 금지)만 가진다. 저장소에 추적되는 파일 중 `sizing_recipe`를 import하는 파일을 전부 갱신하면 shim을 삭제한다(추적 안 되는 workspaces 스크래치는 U-03).
```
새 문안:
```
* **shim**: `sizing_recipe.py`(와 같은 방식으로 `topology_library.py`·`design_report.py` -- 내용이 MOD4·MOD9로 나간다)는 이관 중 아직 옮기지 않은 정의와 명시 재수출 목록(인벤토리에서 생성, `_` 접두 심볼 포함, `import *` 금지)을 가지고, 배정된 정의가 다 옮겨지면 명시 재수출 목록만 가진다. 저장소에 추적되는 파일 중 이 셋을 import하는 파일을 전부 갱신하면 shim을 삭제한다(추적 안 되는 workspaces 스크래치는 U-03). `stick_diagram.py`가 다른 MOD로 나간 이름을 임시로 재수출하는 줄도 같은 조건(그 이름을 `stick_diagram`에서 읽는 추적 파일을 전부 갱신)으로 지운다. 예외: 판정 기록 증거 스크립트(`.ai/verification/**`)와 기준 커밋 측정 원자료(`docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition.py`)는 기록 불변이라 갱신하지 않는다 -- shim 삭제 뒤 이 파일들의 import는 깨진 채 남고 기록된 base 커밋에서만 재실행한다(Phase 3 design 30 D-9).
```
**기준에 닿는 점**(승인 질문에 드러냄): 원문 "추적 파일 전부 갱신"의 예외(D-9). v6 실측: E3 대상 셋(SR·TL·DR) 기준으로 예외 집합 안에 드는 파일은 지금 `probe_stage_partition.py` 1개이고,
`.ai/verification/**` 스크립트는 `stick_diagram` 경유 이름(예 `e_lib_inst.py:35` `sd.save_instance_json`)으로 깨질 수 있다(F2가 SD의 임시 재수출을 지운 뒤).
v7(`a796468`, 4차 검토 m2): E3 AST로 SR·TL·DR import가 걸리는 `.ai/verification/**` 파일 **0**, `import stick_diagram as sd` **8파일**. SD 재수출 문장(위 새 문안 셋째 문장)은 design 30 D-26의
E3b가 판정한다(4차 검토 N1) -- 같은 제외 집합을 쓴다.

---

## §3. 계획 N3.12.3 test-only 열거

현재 `plan.md:687`:
```
* test 전용 변경(판정 유형 `test-only`: TS0·TS2·TS3·TS5·TS7, TS6의 probe 승격·삭제, redteam 데이터만 바꾸는 게이트 변경): 순서 4·5를 생략한다. 증거 = 변경 전 test 집합이 base에서 통과시킨 섹션을 변경 후 test가 모두 PASS함(섹션->test 매핑표는 `10-test-separation` design).
```
새 문안:
```
* test 전용 변경(판정 유형 `test-only`: TS0·TS2·TS3·TS5·TS7, TS6의 probe 승격·삭제, Phase 3 T0·T1(계약 test의 정의 위치 독립화·test 파일 재배치 -- Phase 3 design 30 §8), redteam 데이터만 바꾸는 게이트 변경): 순서 4·5를 생략한다. 증거 = 변경 전 test 집합이 base에서 통과시킨 섹션을 변경 후 test가 모두 PASS함(섹션->test 매핑표는 `10-test-separation` design).
```

---

## §4. `00-common` 103행(§3.3 표)·431행(§10.1) -- MOD10 인자 (D-5)

design 30 v5까지 "§3.2 103행"으로 적었으나 103행은 **§3.3 '이 문서 자신의 분류' 표**다(82행 §3.2는 양식, 93행 §3.3 표 시작 -- v6 실측). 내용은 같다.

현재 `docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md:103`:
```
| 계측 인터페이스 | MOD10 `search`·`output_dir`·`instrument`·`activations_out` 인자, 평가 커널 빌더의 감싸기 | `코드` | 2 -- 보고 수치·판정 입력 | red-green | `gmid-code-author` | `gmid-test-author` | CC-7, CC-8 |
```
새 문안:
```
| 계측 인터페이스 | MOD10 `instrument`·`activations_out` 인자, 평가 커널 빌더의 감싸기(진입점 `run_gmid_design_pipeline`과 `topology_path`·`search`·`output_dir` 인자는 Phase 3 M10이 만든다 -- design 30 §2.3) | `코드` | 2 -- 보고 수치·판정 입력 | red-green | `gmid-code-author` | `gmid-test-author` | CC-7, CC-8 |
```

현재 `…00-common.design.md:431`:
```
* 운영 진입점 `run_gmid_design_pipeline(spec, *, search, output_dir, instrument=None, activations_out=None)`(MOD10). `search`는 탐색 설정(`grid_points_per_theta`, `search_method`, `slsqp_kwargs` -- 지금 `SPECS[circuit]`에 있고 spec에는 없는 값)이다. 하네스 `run()`은 `spec_fn()` 반환값에 자기 기본값(`floorplan_target`, `max_layout_retry_rounds`)을 채운 spec과 `search`를 이 진입점에 넘기고, 받은 `output_dir`·`instrument`·`activations_out`을 그대로 넘긴다.
```
새 문안:
```
* 운영 진입점 `run_gmid_design_pipeline(spec, *, topology_path, search, output_dir, instrument=None, activations_out=None)`(MOD10). `topology_path`는 topology 파일 경로다(지금 하네스가 `SPECS[circuit]["topology_file"]`에서 만들어 `optimize_full_circuit_budget`에 따로 넘긴다 -- spec에 없는 값, design 30 D-5). `search`는 탐색 설정(`grid_points_per_theta`, `search_method`, `slsqp_kwargs` -- 지금 `SPECS[circuit]`에 있고 spec에는 없는 값)이다. 하네스 `run()`은 `spec_fn()` 반환값에 자기 기본값(`floorplan_target`, `max_layout_retry_rounds`)을 채운 spec과 `topology_path`·`search`를 이 진입점에 넘기고, 받은 `output_dir`·`instrument`·`activations_out`을 그대로 넘긴다. 진입점과 `topology_path`·`search`·`output_dir`는 Phase 3(M10)이, `instrument`·`activations_out`은 CC-7·CC-8(Phase 4)이 만든다.
```

---

## §5. `10-test-separation` §5.6 영역 표 '파일' 열 (T0)

현재 `docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md:250`:
```
**영역 표**(현존 21개, test가 이 값과 같음을 단언 -- oracle (d) = 이 문서 승인):
```
새 문안:
```
**영역 표**(현존 21개, test가 이 값과 같음을 단언 -- oracle (d) = 이 문서 승인). '파일' 열은 이 표를 쓸 때(Phase 3 전)의 정의 위치를 적은 **설명**이고 판정 키가 아니다 -- test는 함수 이름으로 대조하고, 정의 위치는 엔진 소스(`skills/analog-gmid-design/assets/*.py`, `workspaces/run_harness.py`)에서 그 이름을 최상위로 정의하는 파일이 정확히 하나인지로 찾는다(Phase 3 T0, design 30 §7.1 R-DEF). 판정 기준은 '영역' 값이다:
```
현재 같은 파일 `:252`:
```
| 파일 | 함수 | 영역 | 이유(N0.4 '영역') |
```
새 문안:
```
| 파일(설명, Phase 3 전 위치) | 함수 | 영역 | 이유(N0.4 '영역') |
```
영역 값 21개·함수 이름·이유 열은 바꾸지 않는다(oracle (d) 불변). 이 표를 파싱하는 코드는 없다(`test_ic5.py`는 자기 상수 `_DOMAIN_TABLE`을 쓴다 -- `git grep "영역 표"` 실측).

---

## §6. D-19 (`rail_declaration`) -- §1 (a)에 포함

D-19는 별도 문서 문장이 아니라 §1 (a)의 `rail_declaration` 토큰 하나다. 승인 질문 D-19의 답에 따라 (a)의 두 안 중 하나를 쓴다. B37a(`port_declaration`)의 모듈 이름은 B37a card 커밋 때
같은 결정을 따라 적는다(design 30 §6.4).

---

## 적용 확인(오케스트레이터, design 커밋 직후)

1. `PYTHONPATH=tools/gates $PY -c "import role_paths as rp, import_layering as il; t=open('docs/01-plan/features/gain-budget-gmid-sizing.plan.md',encoding='utf-8').read(); print(il.mod_table(t)); h,r=rp.read_section_table(t,'### N3.10 '); print(len(h), len(r))"`
   → `mod_table` 10행 그대로, 머리 4열·10행(표 파손 0).
2. '대표 대상' 백틱 식별자에서 `load_topology`·`validate_theta_declaration_order`가 MOD3 행에만, `optimize_full_circuit_budget`가 MOD8 행에만 있다(같은 이름이 두 행에 없음 -- A-1 `conflicts` 0).
3. `$PY tools/gates/import_layering.py --root .` exit 0(표 개정이 계층 표를 바꾸지 않는다 -- 파일·ID 열 불변).

**사전 적용 실측**(v6, `p3_scripts/p3v6_amend_check.py` → `p3v6_amend_check.json`, `7535799` 복제본 사본에 이 문서의 블록을 그대로 적용): '현재' 블록 10개가 모두 해당 줄과 정확히 같다.
D-19 두 안 각각: `mod_table` 10행, N3.10 표 4열·10행, 두 행 이상에 걸린 백틱 식별자 0, `load_topology`·`validate_theta_declaration_order` = MOD3 행만, `optimize_full_circuit_budget` = MOD8 행만,
`rail_declaration` = (가) MOD2 행 / (나) 없음, `import_layering --root` exit 0, `10-test-separation` §5.6 표 21행 그대로.
작성 중 gate `master`가 `a796468`(계획 A2 정정 `8356c1e` 포함)로 나아가 그 판에서 다시 적용: 결과 동일(`p3_scripts/p3v6_amend_check.a796468.json`) -- 줄 번호·원문 그대로 유효.
