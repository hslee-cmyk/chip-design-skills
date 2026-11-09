# Phase 3 design 30 -- UD-0이 덮는 문서 개정 문안 (초안, 저장소 미반영)

대상 design: `_drafts/draft_phase3_design_v8.md`(정식 경로 `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md`). 3차 검토 `review3_phase3_v5.md` B4 대응, 4차 검토 m2·N1(v7 -- §2), 5차 검토 S1·S2(v8 -- §2 사실 문장, §7 새 파일).
기준: gate `master` `7535799`(2026-10-01, 읽기 전용 복제본 `C:/g73/repo`에서 줄 번호·원문 확인), `a796468`에서 다시 확인(아래 '사전 적용 실측' 끝 -- v7에서 §2 새 문안을 고친 뒤 재실행), v8에서 `0f23786`(`a796468` 대비 승인 기록·P10b spec card 2파일만)에서 다시 적용(같은 절 끝). 오케스트레이터가 **design 30 커밋과 같은 커밋**에 아래 교체를 그대로 넣고,
승인 기록(`20260930-30-module-split-design`, `target_kind: diff`)의 `diff_path`가 design 30·계획서·`00-common`·`10-test-separation` 네 경로와 **v8의 새 측정 스크립트 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`(§7)와 v8.2의 `e_lib_p3.py`(§8)**를 덮는다(선례 `20260922-10-test-separation-design`).
N3.10·N3.12.3은 `plan_tables_hash` 입력이 아니다(`merge_gate.py:107-176`: N4.1·N4.2·N6.1·N3.12.2만) -- `plan_tables` 승인은 필요 없다(3차 검토 실측).
**v8.4(2026-10-01)**: 기준 gate `master` `5f643a9`(= P2D)와 `dd60db6`(작업 끝 -- 그 사이는 Phase 2 완료 판정 기록·V3 면제 묶기 문서, 계획서 839행 한 줄)에서 '현재' 블록을 다시 대조 -- 전부 일치, 결과 JSON이 `0f23786` 판과 키 정렬 동일(design 30 부록 A F1v84). 그리고 **N3.10 표 개정을 3건 + D-19에서
'계층 실측으로 지금 계산되는 A-1 충돌'까지 넓혔다**(§1 (a)~(d) 새 문안 갱신 + §9 세 행) -- D0b 착수 키트가 UD-0 개정을 적용한 모의 트리에서 `plan`이 `upward` 34·`cycles` 1을 낸 것 중
N3.10 토큰(A-1)이 낀 충돌은 규칙으로 풀 수 없기 때문이다(design 30 §6.2 'A-1 충돌'·부록 A F4v84). 수치는 G1·D0a **시제품** 관찰이고 D0b base에서 다시 계산한다 -- 이 밖의 개정은 여전히 D-11(따로 승인).

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
| MOD2 | `topology_authoring.py` | topology·spec 로딩, 스키마·단위·참조·선언 순서 게이트, 구조 제안 | `validate_metric_units`, `metric_unit_scale`, `validate_no_legacy_vs_key`, `rail_declaration`(전원 선언 접근자, B26-1). load_topology와 validate_theta_declaration_order는 MOD3 구조 유도 함수를, require_declared_spec_source는 MOD3 spec_fingerprint를 불러 계층상 MOD3에 둔다(Phase 3 design 30 §6.2) |
```
새 문안 -- D-19 답이 **(나) MOD3**일 때(`rail_declaration` 토큰만 없다):
```
| MOD2 | `topology_authoring.py` | topology·spec 로딩, 스키마·단위·참조·선언 순서 게이트, 구조 제안 | `validate_metric_units`, `metric_unit_scale`, `validate_no_legacy_vs_key`. load_topology와 validate_theta_declaration_order는 MOD3 구조 유도 함수를, require_declared_spec_source는 MOD3 spec_fingerprint를 불러 계층상 MOD3에 둔다(Phase 3 design 30 §6.2) |
```
설명 문장의 함수 이름에 **백틱을 쓰지 않는다** -- 백틱 식별자는 A-1 토큰이라 MOD2·MOD3 두 행에 걸려 `conflicts`가 된다(D0a 계약 2). 책임 열은 바꾸지 않는다(MOD2에 spec 로딩·나머지 선언 게이트가 남는다).
**v8.4 추가 두 토큰**(design 30 §6.2 'A-1 충돌', 부록 A F4v84): `require_declared_spec_source`(MOD2 토큰)는 `spec_fingerprint`(MOD3 토큰, `sizing_recipe.py:7683`)를 부른다 -- 호출자를 MOD3로 옮긴다
(원칙: A-3·D-3과 같이 부르는 쪽이 올라간다; `spec_fingerprint`는 'S0 지문' 책임의 MOD3 대표 대상이라 내리지 않는다). `metric_unit_scale`(레지스트리 칸 `gmid_sizing_engine` → MOD4)은 `validate_metric_units`(MOD2 토큰)가 부른다
(`:5272`) -- 트리 안 참조가 없는 단위 환산 표 함수라 MOD2('단위' 게이트 책임)로 내린다(그 소비자 `compute_metric`은 MOD5라 아래 방향).

### (b) MOD3 행 -- 두 함수 추가

현재 `plan.md:523`:
```
| MOD3 | `circuit_state_graph.py` | S0 지문, S1 구조 유도(개념당 정본), S1v, 결합 블록 | `is_diode_connected`, `true_current_mirror_groups`, `l_sharing_classes`, `l_class_owners`, `vgs_alias_map`, `_kcl_and_matching_edges`, `trace_*_branches`, `propagate_topology_forced_currents`, `spec_fingerprint` |
```
새 문안:
```
| MOD3 | `circuit_state_graph.py` | S0 지문, S1 구조 유도(개념당 정본), S1v, 결합 블록, topology 로딩(구조 자동채움을 부르므로) | `is_diode_connected`, `true_current_mirror_groups`, `l_sharing_classes`, `l_class_owners`, `vgs_alias_map`, `_kcl_and_matching_edges`, `trace_*_branches`, `propagate_topology_forced_currents`, `signal_path_nodes`, `find_hub_merge_candidates`, `spec_fingerprint`, `require_declared_spec_source`, `load_topology`, `validate_theta_declaration_order` |
```
**v8.4 추가 세 토큰**(design 30 §6.2 'A-1 충돌', 부록 A F4v84): `require_declared_spec_source`(위 (a)). `find_hub_merge_candidates`(레지스트리 칸 `stick_diagram` → MOD7, 트리 안 참조 0)는
구조 제안 쪽 `check_symmetry_dispositions`가 부르고 그것을 `propose_device_roles_gap_fill` → `load_topology`(MOD3 토큰)가 부른다 -- 승격 규칙만으로는 이 사슬 전체가 MOD7로 올라가 `load_topology`가 위로
부르게 되므로 피참조 쪽(같은 hub 공유 후보 -- 구조 후보 탐색)을 MOD3로 내린다. `signal_path_nodes`(레지스트리 §7 `보류(Phase 4)` '삭제 후보', 칸에 MOD 없음, 트리 안 참조·참조자 0)는 규칙으로 정할 곳이 없어
`sizing_recipe.py`가 F2에서 지워질 때 갈 곳이 없다 -- 게이트·소스 그래프 함수라 MOD3('S1 구조 유도')에 둔다(삭제 판단은 Phase 4 그대로, D-10과 같이 '옮기고 D 유지').
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
| MOD6 | `theta_search.py` | 평가 커널 조립, 층 0 기둥 조립 presolve(DEC-71), 할당 층(기본 = 외층 SLSQP / 정밀 = 내층 DP·중층 좌표강하, DEC-73), 실패 캐시, 시작점, 전역 샘플, S3 | θ 탐색부(CC-7이 optimize_full_circuit_budget에서 추출하는 함수 -- Phase 4, 00-common §10.1. 추출 전 함수 전체는 MOD8), `repair_infeasible_baseline`. 평가 커널 조립(_build_theta_evaluator)·시작점(search_stage_budget_L_warm_start·presolve_warm_start)·SLSQP(_optimize_theta_slsqp)는 지금 코드에서 레이아웃 해석(resolve_stack_layout, MOD8)을 불러 Phase 3 동안 MOD8에 둔다 -- CC-7 추출 때 MOD6(Phase 3 design 30 §6.2) |
```
**v8.4 -- 네 토큰을 MOD8로**(design 30 §6.2 'A-1 충돌', 부록 A F4v84): `_build_theta_evaluator`(MOD6 토큰)가 `resolve_stack_layout`(MOD8 토큰)을 부른다(`sizing_recipe.py:8060`). `resolve_stack_layout`은
`stick_diagram` 레이아웃 함수(MOD7)를 불러 내릴 수 없으므로 부르는 쪽이 올라간다 -- 그런데 `_build_theta_evaluator` 하나만 옮기면 그것을 부르는 MOD6 토큰 `search_stage_budget_L_warm_start`·`presolve_warm_start`가,
그 둘을 옮기면 `_optimize_theta_slsqp`(→ `presolve_warm_start`)가 새로 위로 부른다(시제품 실측, 나머지 개정·design 30 §6.2 v8.4 규칙 모두 적용: 하나만 옮김 `upward` 4, 셋 1, 넷 0) -- 네 토큰을 함께 MOD8로 옮겨야 닫힌다. `optimize_full_circuit_budget`의 D-3('Phase 3 위치 MOD8,
θ 탐색부 추출 뒤 MOD6')과 같은 모양이고 이동만 하는 Phase 3에서 호출 관계를 바꾸지 않는 유일한 배치다. 설명 문장의 함수 이름은 백틱 없이 쓴다(두 행 `conflicts` 방지).

### (d) MOD8 행 -- `optimize_full_circuit_budget` 추가

현재 `plan.md:528`:
```
| MOD8 | `sizing_layout_convergence.py` | 사이징↔레이아웃 수렴 루프 | `run_topology_pipeline_with_finger_fixup`, `revalidate_finger_override`, `resolve_stack_layout` |
```
새 문안:
```
| MOD8 | `sizing_layout_convergence.py` | 사이징↔레이아웃 수렴 루프 | `run_topology_pipeline_with_finger_fixup`, `revalidate_finger_override`, `resolve_stack_layout`, `_build_theta_evaluator`, `search_stage_budget_L_warm_start`, `presolve_warm_start`, `_optimize_theta_slsqp`(이 넷은 Phase 3 위치 -- resolve_stack_layout을 부른다. CC-7 추출 때 MOD6), `optimize_full_circuit_budget`(Phase 3 위치 -- 레이아웃 함수와 MOD8 함수를 부른다. θ 탐색부는 CC-7이 MOD6로 추출) |
```

(v8.4: MOD1·MOD4·MOD5 행 개정은 §9 -- '현재' 블록 순서를 바꾸지 않으려고 문서 끝에 둔다. 적용은 §1과 §9를 함께 한다.)

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
v7(`a796468`, 4차 검토 m2): E3 AST로 SR·TL·DR import가 걸리는 `.ai/verification/**` 파일 **0**, `import stick_diagram as sd` **8파일**.
v8(`0f23786`, 5차 검토 S2 -- 근사 배정 모의 F2에서 E3b 식을 제외 집합 없이 실행, design 30 부록 A F1v8): 8파일 중 F2 뒤 SD에 남지 않는 이름을 읽어 **깨지는 것은 2개**(`df36-instance-relpath/scripts/e_lib_inst.py` -- `save_instance_json`, `p9-kcl-edges/scripts/diff_dup.py` -- `_import_analog_grammar`·`_kcl_and_matching_edges`), 나머지 6개 `e_lib.py`는 깨지지 않는다(정확한 수는 D0b 배정 뒤). SD 재수출 문장(위 새 문안 셋째 문장)은 design 30 D-26의
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
v8: gate `master` `0f23786`(C:/g113 복제본)에서 이 문서(v8 -- §1~§6 블록은 v7과 같고 §2 사실 문장·§7만 더함)를 다시 적용: `p3_scripts/p3v8_amend_check.0f23786.json`이 `p3v7_amend_check.a796468.json`과 키 정렬 동일(블록 21개, '현재' 10개 일치, 두 안 모두 표 4열·10행·`import_layering` exit 0).
v8.4: gate `master` `5f643a9`(C:/g164 복제본) -- v8.3 문서 그대로 `p3v6_amend_check.py`를 돌린 결과가 `0f23786` 판과 키 정렬 동일. v8.4 문서(블록 27개 -- §1 (a)~(d) 새 문안 갱신 + §9 여섯 블록)로 다시: '현재' 10개 일치,
D-19 두 안 모두 `mod_table` 10행·N3.10 4열·10행·두 행 이상에 걸린 백틱 식별자 0·`import_layering --root` exit 0·§5.6 표 21행. 그 스크립트는 §9를 적용하지 않으므로 §1+§9를 모두 적용한 계획서를 따로 만들어
'현재' 13개(§9의 521·524·525행 포함) 일치, 8행의 백틱 토큰 집합 = 시제품 측정에 쓴 표(design 30 부록 A F4v84)와 같음, 두 행 이상 토큰 0, `import_layering` exit 0, 표 4열·10행을 확인했다.
**적용 확인 2의 v8.4 확장**: 위 셋에 더해 `_build_theta_evaluator`·`search_stage_budget_L_warm_start`·`presolve_warm_start`·`_optimize_theta_slsqp`가 MOD8 행에만, `require_declared_spec_source`·`find_hub_merge_candidates`·`signal_path_nodes`가 MOD3 행에만,
`metric_unit_scale` MOD2, `_multilinear_interp_point_multi` MOD1, `_metric_nulling_resistor_ohm` MOD4, `apply_theta_feed` MOD5 행에만 있다.

---

## §7. 새 파일 -- Phase 3 E-INST 측정 스크립트 (D-28, v8 -- 5차 검토 S1)

경로: `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`(지금 없음 -- 새 파일). 내용 = `_drafts/p3_scripts/e_inst_p3_proposed/e_inst_p3.py` 그대로(sha256 `7d26134ad00ec50412bf65b1fcc3aa046845a315b8edf28dc93f4a102c25e283`).
오케스트레이터가 design 30 커밋에 같은 바이트로 넣고, 승인 기록 `diff_path`가 덮는다. `e_inst_df36.py`(design 20 §10 E4 정본, `.ai/verification/20260930-df36-instance-relpath/scripts/`)와의 차이는 엔진 출처 확인 한 곳뿐이다
(고정 모듈 이름 셋의 `sys.modules` 항목 → 실행 뒤 `skills/analog-gmid-design/assets` 디렉터리에서 로드된 모듈 전부가 `<root>` 안, 하나 이상). 이유·동등 근거는 design 30 D-28·§10 E5(동등 확인은 DoD가 비교 판 P2D -- 대안이면 B0 -- 에서 먼저 잰다, v8.2).
계획서·design 문장이 아니므로 아래 '적용 확인'의 표 점검 대상이 아니다 -- 적용 확인은 `sha256sum`이 위 값과 같은지만 본다.

## §8. 새 파일 -- Phase 3 E-LIB 측정 스크립트 (D-28 (e), v8.2 -- UD-0 (c) 선례 모양)

경로: `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_lib_p3.py`(지금 없음 -- 새 파일). 내용 = `_drafts/p3_scripts/e_lib_p3_proposed/e_lib_p3.py` 그대로(sha256 `c6b82fc7b4cd974ce06032559c92ecdcc8cf21e327b154e4a56bda0772aa140e`).
오케스트레이터가 design 30 커밋에 같은 바이트로 넣고, 승인 기록 `diff_path`가 덮는다. `e_lib.py`(design 20 §10 E4 정본, `.ai/verification/20260930-df36-instance-relpath/scripts/`)와의 차이는 한 곳뿐이다
(`<root> <out.json>` 뒤에 meta 키 이름을 받아, 회로마다 `load_topology` 반환의 meta에서 그 키를 빼고 해시를 계산하며 뺀 값은 `circuits.<회로>.masked`에 따로 싣는다 -- 출력에 `masked_meta_keys`·`circuits.*.masked` 두 키가 더해진다).
키를 주지 않으면 `hash`와 나머지 출력이 `e_lib.py`와 같다(실측 design 30 부록 A F2v82). DoD E5만 쓴다(M card는 `e_lib.py` 그대로). 이유·판정은 design 30 D-28 (e)·§10 E5.
계획서·design 문장이 아니므로 '적용 확인'의 표 점검 대상이 아니다 -- `sha256sum`이 위 값과 같은지만 본다.

## §9. 계획 N3.10 표 -- 계층 실측으로 더한 세 행 (v8.4, design 30 §6.2 'A-1 충돌')

§1과 같은 교체 표기. §1 (a)~(d) 새 문안의 v8.4 토큰과 함께 적용한다(§1의 '현재' 블록 순서를 유지하려고 여기 둔다). 근거 수치는 G1·D0a **시제품**(G1 `g1_core.py` 23:16판 `b3c4e391…`,
D0a `move_plan_proto.py` `d2f3da97…`) 관찰이고 D0b base에서 다시 계산한다(design 30 부록 A F4v84). 원칙: (P1) 부르는 쪽이 올라간다(A-3·D-3 선례) -- 피참조가 그 MOD의 대표 대상이거나 더 큰 번호를 부를 때,
(P2) 트리 안 참조가 없는 도우미는 부르는 쪽 MOD의 책임에 맞으면 내려간다.

### (e) MOD1 행 -- `_multilinear_interp_point_multi` 추가 (P2)

`SemiEmpiricalGmIdLUT`(MOD1 토큰)가 `_multilinear_interp_point_multi`(레지스트리 칸 `gmid_sizing_engine.py` → MOD4, 트리 안 참조 0)를 부른다(`sizing_recipe.py:399`). '보간' 책임 MOD1로 내린다(같은 행의 `_multilinear_interp`와 짝).

현재 `plan.md:521`:
```
| MOD1 | `gmid_lut.py` | LUT 인터페이스·보간·역산·곡선 검사·보간 오차 | `GmIdLUT`, `SemiEmpiricalGmIdLUT`, `_multilinear_interp`, `_solve_vgs`, `lut_conditions_from_npz`, gmb 유도(`∂ID/∂VSB`) |
```
새 문안:
```
| MOD1 | `gmid_lut.py` | LUT 인터페이스·보간·역산·곡선 검사·보간 오차 | `GmIdLUT`, `SemiEmpiricalGmIdLUT`, `_multilinear_interp`, `_multilinear_interp_point_multi`, `_solve_vgs`, `lut_conditions_from_npz`, gmb 유도(`∂ID/∂VSB`) |
```

### (f) MOD4 행 -- `apply_theta_feed` 빼고 `_metric_nulling_resistor_ohm` 추가

* `apply_theta_feed`(MOD4 토큰)가 읽는 theta feed 레지스트리(`_THETA_FEED_REGISTRY` 문장)의 `metric_stage_budget` 처리기(`_feed_metric_stage_budget`)가 공유 전류 조인트 스캔(`_run_shared_current_joint_scan` --
  `compute_metric`(MOD5)을 부른다)을 부른다 -- 레지스트리 문장·처리기는 승격으로 MOD5가 되고 `apply_theta_feed`만 MOD4에 남으면 위로 부른다. 부르는 쪽을 MOD5로 올린다(P1, 아래 (g)).
* `_metric_nulling_resistor_ohm`은 `_METRICS_REGISTRY`(MOD5 토큰)가 부르는데 레지스트리 칸 "instance_report_builder.py(보고) 또는 gmid_s…"가 MOD 하나(MOD9)로 읽혀 위로 부른다. 칸이 적은 두 번째 후보이자
  다른 `_metric_*` 함수(레지스트리 칸 `gmid_sizing_engine` -- 26개 중 24개 MOD4)와 같은 MOD4로 둔다(P2 -- 그 함수의 트리 안 참조는 MOD4 `SizingContext`·`_resolve_nulling_resistor_ohm`뿐).

현재 `plan.md:524`:
```
| MOD4 | `gmid_sizing_engine.py` | 소자 사이징, DC 해석(W 티어·순환 블록·봉인), 달성가능성·DOF, 보상 레지스트리, theta feed | `size_transistor`, `feasible_gm_ids`, `measure_L_knee`, `_hr_*`, `solve_diode_connected_vds`, `solve_stacked_diode_pair`, `apply_theta_feed`, `topology_library.py` 보상식 |
```
새 문안:
```
| MOD4 | `gmid_sizing_engine.py` | 소자 사이징, DC 해석(W 티어·순환 블록·봉인), 달성가능성·DOF, 보상 레지스트리, theta feed | `size_transistor`, `feasible_gm_ids`, `measure_L_knee`, `_hr_*`, `solve_diode_connected_vds`, `solve_stacked_diode_pair`, `_metric_nulling_resistor_ohm`, `topology_library.py` 보상식. theta feed 처리 함수는 여기 두되 적용 함수 apply_theta_feed와 feed 레지스트리는 metric을 부르는 처리기 때문에 Phase 3 동안 MOD5(Phase 3 design 30 §6.2) |
```

### (g) MOD5 행 -- `apply_theta_feed` 추가 (P1)

현재 `plan.md:525`:
```
| MOD5 | `circuit_metrics.py` | metric 레지스트리, 소신호 MNA, 사후검증 metric, SPICE 대조 | `compute_metric`, `_METRICS_REGISTRY`, `build_ac_network`, `_full_circuit_response`, `estimate_mismatch_sigma` |
```
새 문안:
```
| MOD5 | `circuit_metrics.py` | metric 레지스트리, 소신호 MNA, 사후검증 metric, SPICE 대조 | `compute_metric`, `apply_theta_feed`(Phase 3 위치 -- feed 레지스트리의 metric_stage_budget 처리기가 compute_metric을 부르는 조인트 스캔을 부른다), `_METRICS_REGISTRY`, `build_ac_network`, `_full_circuit_response`, `estimate_mismatch_sigma` |
```

### 적용 실측 (v8.4 -- design 30 부록 A F4v84)

`5f643a9` 복제본에 §1 (a)(가)~(d)와 이 절 (e)~(g)를 적용한 계획서 + design 30 §6.2 v8.4 규칙(모듈 docstring 제외·A-K·승격(MOD7 상한)·A-6·A-7)을 G1·D0a 시제품 변형으로 돌린 `plan`:
`upward` 0 · `cycles` 0 · `unassigned` 0 · `conflicts` 0 · `import_time_high` [] · MOD7 파일 밖 단위의 MOD7 배정 0 · 배정 403(재생성 전 `reg_mismatch` 78 = D0b red의 크기). 열을 그 출력으로 다시 쓴 커밋에서
`plan` exit 0 · `reg_mismatch` 0 · (단위 키 → MOD) 사상 차이 0(멱등). 개정 없이(UD-0 원래 3건 + D-19만) 같은 규칙: `upward` 7 -- 7건 모두 원천이 A-1 토큰이다(규칙으로는 풀 수 없다).
토큰을 덜 옮긴 변형: MOD6 → MOD8 넷 중 하나만 `upward` 4, 셋 1; `find_hub_merge_candidates` 없이 2(승격 MOD7 상한이 `check_symmetry_dispositions` → `find_hub_merge_candidates`를 위반으로 남긴다).
설명 문장 안 함수 이름은 백틱 없이 쓴다 -- 두 행 이상에 걸린 백틱 식별자 0(A-1 `conflicts` 0)을 같은 실측이 확인했다.
