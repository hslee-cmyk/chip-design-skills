# 검토 -- Phase 4 첫 card 초안(B41 + #2) gate `master` `863a037` 재확인

대상(읽기 전용): `draft_b41_scope_note.spec.md`(B41, `20261002-b41-scope-note-test`), `b41_briefs.md`, `b41_kit/`, `draft_p4_first.spec.md`(#2, `20261002-d4-delete-unwired`), `p4_first_briefs.md`,
`draft_phase4_design.md` v0.9.11, `phase4_approval_question.md`. 대조: Phase 3 초안(`draft_p3_d0b`·`draft_p3_m3/m4/m6/m8/m9/m10`·`draft_p3_t0`·`draft_p3_t1`·`draft_p3_f1`), design 30 v8.5(gate), T1 모의 `p3kit_m10_t1/out/r2/t1_map.json`, M 모의 `p3kit_m2_m9/out/cards_data.json`.
이 문서 밖 파일은 고치지 않았다.

측정 조건: 실제 저장소는 `git -C`로만 읽음. 실행은 모래상자 `C:/g398`만(`git clone --no-local --no-hardlinks -c core.autocrlf=false -c core.hooksPath=`, origin 제거, `863a037` detached, `git archive 863a037 tools/gates`, TMP/TEMP = `C:/g398/tmp`), 끝에 `C:/g398` 삭제.
실제 저장소 시작·끝: HEAD `863a037cc0d7…`, `status --porcelain` md5 `0474ab6d…`, reflog 359줄 -- 같음. python `C:\Python314\python.exe -B`. 이 문서의 수치는 검토자 측정이고 판정 수치가 아니다.

---

## 0. 요약

| 등급 | id | card | 한 줄 |
|---|---|---|---|
| **막음** | B1 | #2 | D0b 영구 계약 test(`test_p3_registry_dest.py` T-E 결정 사실 표본)가 #2의 삭제 대상 3개(`solve_diode_stack_current` A-6, `MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity` A-7)를 표본으로 고정한다 -- #2 병합본에서 T-E가 FAIL. #2 계약·V5 목록·UD-0 문안 어디에도 없다 |
| **막음** | B2 | #2 | T1이 `unit/test_selftest_{sizing_recipe,stick_diagram}.py`를 없애고 `unit/test_mod<k>_*.py`로 옮긴다 -- 계약 7·V5 목록 6~8·브리프 쓰기 경로·test id 집합이 모두 사라지는 파일을 가리킨다. 또 T1은 옛 머리 import를 목적 파일마다 **원문 그대로** 복사하므로 지울 import 이름이 여러 파일에 퍼질 수 있다 |
| **막음** | B3 | B41·#2 | V8 basis `'N/A -- 계측 미도입 …'`(P-38)는 `863a037` rule10(merge_gate 532~545)이 거부한다(phase 4 = V8 도입 4, basis 형식도 아님). `phase4_approval_question.md` [V8 도입] 질문이 이미 짚었으나 두 card 문장·B41 브리프·B41 '결정 필요 항목: 사용자 결정 없음'이 그대로다 -- 그 답과 계획 커밋이 B41 착수 조건이다 |
| 중요 | S1 | #2 | #2는 design 40 부록 C 사이트 **둘을 지운다**: C.2 `n_samples` `0`(SR 2789, `estimate_area_budget`), C.2 `vsb` `0.0` 31곳 중 1527(`solve_diode_stack_current`). card '부록 C 사이트를 지우거나 바꾸지 않는다'·[V8 도입] 권고 basis 문구 '부록 C 사이트 불변'은 #2에 틀리다 |
| 중요 | S2 | #2 | V4: `test_lint`는 바뀐 test 파일 **전체**를 lint한다. #2 interface card 피검(22)에 `optimize_full_circuit_budget`·`revalidate_finger_override`가 있어, T1 뒤 `test_mod8_sizing_layout_convergence.py`(#2가 고치는 파일)의 `test_s052_compensation`·`test_s054_section`이 규칙 (1)에 걸린다 -- T1 새 id 면제 `20261006-p3-t1-v4-exempt`가 head 트리에 없으면 V4 FAIL. 실측(`863a037`, 옛 파일): (1) exempt 2·(2) FAIL 1(`test_s028` -- #2가 지움) |
| 중요 | S3 | #2 | 계약 2 G-1: `_THETA_FEED_REGISTRY`는 `AnnAssign`(`_THETA_FEED_REGISTRY: dict = {`, SR 6268)이다 -- `ast.Assign`만 보는 스캐너는 이 딕셔너리를 놓친다(design 30 §2.2 V6 `unbounded_cache`와 같은 함정). 계약에 '`Assign`·`AnnAssign` 둘 다' |
| 중요 | S4 | #2 | 계약 5와 계약 3의 충돌 가능성(F1 뒤 도구): 사이드카 두 호출을 지우면 F1이 그 두 이름 때문에 넣은 엔진 import(`theta_search` -- F1 배정)가 죽은 import가 된다. F1이 from-import 모양을 골랐다면 `from theta_search import load_derived_bounds, derived_bounds_path`가 남아 **계약 3 GONE(import 참조, `A/tests/tools/**` 포함)이 FAIL**인데 계약 5는 import 줄 변경을 금한다 |
| 중요 | S5 | B41 | M10 뒤 운영 호출은 `workspaces/run_harness.py` 492행이 아니라 `A/gmid_design_pipeline.py`(진입점 `run_gmid_design_pipeline`)에 있고, `run_harness.py:42` import는 F1/M10이 바꾼다 -- '공백'·'무동작' 문장과 '작성 전 실측' 1의 운영 경로 사실이 Phase 3 뒤 틀린다. P 항목에 없다 |
| 중요 | S6 | #2 | P3-1이 낡음: `solve_diode_stack_current` 목적지는 이제 `gmid_sizing_engine`(D0b (d)-1 A-6, M4 초안)로 정해졌다('미정' 아님). 그리고 V3 `targets`는 '정의 파일'이 아니라 **바뀐 소스 .py 전부**(`mutate_changed.py` 619행) -- 분할 뒤 6파일 예상 |
| 경미 | m1~m10 | 둘 | 줄 번호 이동, 계약 test 파일 수 29→31, `analog-grammar-integration.md` 384→385, 백로그 인용 위치, design 40 판 표기, `b41_kit` 낡음 등(§2·§6) |

`parse_spec_card`·`interface_card`는 두 초안 모두 `863a037` gate 도구로 통과(§3).

---

## 1. 근거 -- 막음·중요 항목

### B1 (#2) D0b T-E 표본
* D0b 초안(`draft_p3_d0b.spec.md`) 계약 11 (a) 표 99행: T-E `test_p3rd_fact_samples`(이름은 예시, 접두 `test_p3rd_`) = "(d)-1 표의 각 행: 행 있는 표본은 대상 행이고 칸 == 기대 줄기, 모든 표본은 `plan` `mod` 줄기 == 기대 줄기 -- 어긋난 표본을 모아 빈 목록 단언".
  (d)-1 표(130~165행) 28행 중 161~163행: `solve_diode_stack_current`(`gmid_sizing_engine`, ○, **A-6 유일 표본**), `MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity`(`stick_diagram`, ○, **A-7 유일 표본 둘**).
* D0b (d)-2 '실제 트리 drift guard'는 영구 test가 실제 `HEAD`에서 돈다(170행) -- Phase 4에서도 매 suite. #2가 정의·레지스트리 행을 지우면 그 세 표본은 '대상 행 아님'·`plan` `mod` 없음 → T-E FAIL. skip은 금지(메모리 원칙).
* 결과: #2 T가 그 test에서 세 표본 행을 지워야 하고(test-author, V5 -- 표본 삭제 = 판정 대상 축소), V5 목록·UD-0 #2 문단(사용자가 보는 승인 범위)·브리프 쓰기 경로에 들어가야 한다.
  A-6·A-7 규칙의 남는 표본이 0이 되는 것도 범위 설명에 적는다(D0b oracle (d)-1 '규칙마다 한 행 이상'은 D0b 시점 문장 -- 대체 표본을 고르는 것은 D0b의 oracle 몫이라 #2가 손적용하지 않는다; 백로그 후보).
* 착수 때 확인: D0b가 실제 커밋한 test 본문(함수 이름·표 자료 구조)과 표본 수.

### B2 (#2) T1 이동
* T1 초안(`draft_p3_t1.spec.md`) 의도·계약 1~3: `U/test_selftest_{sizing_recipe,stick_diagram,design_report,topology_library}.py` 삭제 → `U/test_mod<k>_<N3.10 줄기>.py`(test 이름 불변), 새 파일 머리 = 그 파일에 test를 보낸 옛 파일들의 머리 문장 **원문**(계약 3).
* T1 모의 매핑(`p3kit_m10_t1/out/r2/t1_map.json`, rev `7fd4b16…` -- 모의, 착수 때 실제 `t1-mapping.json`으로 재확인):

  | 옛 id(`unit/test_selftest_…`) | k | 새 파일 |
  |---|---|---|
  | `sizing_recipe::test_s007_solve_diode_stack_current` | 4 | `unit/test_mod4_gmid_sizing_engine.py` |
  | `sizing_recipe::test_s006_solve_id_for_target_gm`(계약 7 docstring 수정) | 4 | `unit/test_mod4_gmid_sizing_engine.py` |
  | `sizing_recipe::test_s028_estimate_area_budget` | 8 | `unit/test_mod8_sizing_layout_convergence.py` |
  | `sizing_recipe::test_s014_section`(계약 7 `mismatch_sigma_mV` 주석 -- `863a037` 1219~1221행이 이 test 안) | 8 | `unit/test_mod8_sizing_layout_convergence.py` |
  | `stick_diagram::test_s058_section` | 7 | `unit/test_mod7_stick_diagram.py` |
  | (B41 참고) `stick_diagram::test_s088_save_instance_json` | 9 | `unit/test_mod9_instance_report_builder.py` |

* import 퍼짐: SR 출신 test는 k ∈ {1,3,4,5,6,8}, SD 출신은 {3,7,8,9}(같은 매핑 `summary.k_by_old`). 머리 원문 복사라 T1 병합본에서 SR 머리(`estimate_area_budget`·`solve_diode_stack_current`·`_invert_gm_id_for_current` 포함, `863a037` 24행)는 최대 6파일, SD 머리(`check_multi_leaf_hub_parity` 포함, 24행)는 최대 4파일에 있다.
  F1이 그 import를 정의 모듈로 다시 쓸 때 안 쓰는 이름을 빼는지는 F1 초안에서 확인되지 않는다 -- 빼지 않으면 계약 3 GONE(`A/tests/**`의 `import` 참조 0)을 맞추려고 #2 T가 **그 모든 파일**에서 이름을 지워야 한다. card base에서 `git grep -n -w` 6 이름 -- `A/tests` 결과로 파일 목록을 정한다.
* `_invert_gm_id_for_current`의 test 사용은 `863a037`에서도 `test_selftest_sizing_recipe.py:651`(test_s007 안) 하나뿐 -- 사실 문장은 맞다(파일 이름만 바뀜).

### B3 (B41·#2) V8 basis
* `863a037` `tools/gates/merge_gate.py` `rule10_phase` 532~545행(7243f28 이후 `tools/gates` 변경 0): N/A면 `order.index(spec_phase) < order.index(intro)` 아니면 거부, basis는 `^도입 (\S+?): `로 시작하고 그 값 = 도입. 계획 N4.2 846행 V8 도입 = `4`(`863a037` 그대로).
* B41 card 90행·#2 card 125행·`b41_briefs.md` 2.2 V8 행은 P-38 문구 그대로 → 로더 거부. `phase4_approval_question.md` 105~145행 [V8 도입] 질문(권고 '도입 5 + 늘지 않음 test')은 **미답**(`user_decisions.md`에 기록 없음, `.ai/approvals/`에 `plan-v8-intro`·`40-defect-fixes` 0).
* 그 문서 109행 "늦어도 B41 push 전에 답과 계획 커밋이 gate에 있어야" -- 그런데 B41 card '결정 필요 항목'은 "사용자 결정 없음"이고 착수 조건 1~5에 V8이 없다.

### S1 (#2) 부록 C 사이트 삭제
* design 40 v0.9.11 부록 C.2(1367행~): 1388행 `| sizing_recipe.py | n_samples | 0 | 2789 (1; estimate_area_budget) | 아니오(근사) | #13 발동 규칙 §10.1-4 |`, 1398행 `vsb` `0.0` 목록 첫 값 1527.
* `863a037` SR: 2789 `n_samples = prior.get("n_samples", 0)`(`estimate_area_budget` 2765~ 안), 1527 `vds, vsb = dev["vds"], dev.get("vsb", 0.0)`(`solve_diode_stack_current` 1499~ 안). #2가 두 def를 지우므로 두 사이트가 사라진다(폴백 지점 감소 -- 늘림 아님).
* P-38(844행)과 §10.1-0(1007행)은 "부록 C 사이트를 바꾼 card는 사이트 id를 적음". [V8 도입] 권고 답의 basis 문안('이 card는 부록 C 사이트 불변', 질문 문서 140행)은 B41에는 맞고 #2에는 틀리다.

### S2 (#2) V4 전체 파일 lint
* `test_lint.py` 717~721행: `--base/--head`면 `diff --name-only --no-renames --diff-filter=AM`의 test 파일 **전체**를 lint, 728~734행: head 트리의 `target_kind: decision` 승인 target에 그 id가 있으면 규칙 (1)만 `exempt`.
* 모래상자 실측(`863a037`, #2 초안으로 만든 interface card 22행, 파일 = 옛 `test_selftest_sizing_recipe.py`·`test_selftest_stick_diagram.py`·`test_ic5.py`·`test_ts6_probe_relocate.py`): verdict FAIL --
  (2) FAIL 1 = `test_s028_estimate_area_budget` 1795(#2가 지우므로 병합본에서 사라짐), (1) exempt 2 = `test_s052_compensation` 2502·`test_s054_section` 2555(옛 id 면제 `20260923-c9-v4-exempt`), 그 밖 (3)(4)(5) 0.
* T1 뒤 두 test는 `test_mod8_sizing_layout_convergence.py`(#2가 test_s028을 지우는 파일)로 가고 옛 면제는 id가 바뀌어 풀린다(그 기록 '덮지 않는 것'). T1 '결정 필요 항목' T1-2 기본안 (가)면 `20261006-p3-t1-v4-exempt`가 새 id를 덮는다 -- (나)를 고르면 덮는 기록이 없다.
* 그래서 #2 V4 PASS의 전제 = T1 새 id 면제가 head 트리에 있음. #2 판정 기록 `approvals[]`에 넣을 필요는 없으나(도구가 head 트리를 읽음) V4 basis에 그 id를 적는다.

### S3 (#2) G-1 스캐너
* `863a037` SR: `_COMPENSATION_REGISTRY = {`(1416, Assign)·`_CMRR_ESTIMATOR_REGISTRY`(4760)·`_PSRR_ESTIMATOR_REGISTRY`(4777)·`_METRICS_REGISTRY`(5083) Assign, `_THETA_FEED_REGISTRY: dict = {`(6268) **AnnAssign**. 분할 뒤 위치는 MOD4·MOD5 등으로 갈린다(계약이 이미 'A/*.py 전체'라 위치는 무관).

### S4 (#2) 도구 import
* F1 초안 계약 1 (d)·수용 표본: F1 도구 모양은 `_f1_<정의 모듈>` 별칭(r2·r3 모의 `f12_f1sim.py` 규칙 (2): 사이드카 두 함수 → `theta_search`) 또는 from-import. 이 card 계약 8 r3 실측 S2b·S2f(`theta_search` import까지 지운 판)는 (마) 핀 PASS -- import 줄 삭제는 정규형 밖이라 핀과 충돌하지 않는다.
* 그러나 계약 5 41행 "그 밖의 줄(… 최상위 import 줄)은 바꾸지 않는다"와 브리프 2.1-3 "최상위 import 줄은 바꾸지 않는다"가 그 삭제를 막는다 → 별칭 모양이면 죽은 import가 남고(만들면 배선 원칙 위반 -- 쓰는 곳 0인 바인딩), from-import 모양이면 GONE 계약 3이 FAIL.

### S5 (B41) 운영 호출 위치
* M10 초안 30·55행: MOD10이 MOD9 `save_instance_json`을 정의 모듈에서 import하고, 하네스 `run()`은 진입점을 부른다(계약 5 (b): "진입점 모듈 속성 … `save_instance_json` …"). 그래서 Phase 3 뒤 운영 호출 = `A/gmid_design_pipeline.py` 안.
* `863a037` 사실(지금은 맞음): `run_harness.py:42` `from stick_diagram import save_instance_json, run_full_circuit_audit_from_topology`, `:492` `save_instance_json(instance_out, topo, result["sizing"], result["pipeline_result"])`.

### S6 (#2) 목적지와 V3 대상
* 분할 뒤 정의 파일(D0b (d)-1 표·M 초안 단위 목록·M 모의 `cards_data.json` -- 착수 때 R-DEF로 다시 확인): `estimate_area_budget` → `sizing_layout_convergence.py`(M8 초안 102행 A-5), `solve_diode_stack_current` → `gmid_sizing_engine.py`(D0b 161행 A-6, M4 초안 101행), `load_derived_bounds`·`derived_bounds_path` → `theta_search.py`(M6 초안 92행 A-4), `MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity` → `stick_diagram.py`(남음, A-7).
* `mutate_changed.py` 619행 `targets = [p for p in diff … if p.endswith(".py") and rch._is_source(p)]` -- 바뀐 소스 전부. 계약 4 docstring만 바뀌는 파일(`gmid_lut.py`·`circuit_state_graph.py`)도 `targets`에 들어간다(변이 0은 그대로 -- `def_hash`가 docstring 제외).

---

## 2. 사실·줄 인용 재측정 (`863a037`)과 다시 움직일 곳

### 2.1 B41

| card 인용(측정 판 `4a286f0`/`fd4ef8c`) | `863a037` | 이동 원인 | 뒤에 또 움직이나 |
|---|---|---|---|
| SD `def save_instance_json` 8973 | **8959** | B34(SD −14) | B26-1(SD 1014행부터 편집 -- 뒤쪽 전부 이동), M9(정의가 `instance_report_builder.py`로 -- 판 전체가 바뀜) |
| docstring 첫 단락 8975~8977 | **8961~8963** | 〃 | 〃 |
| 둘째 단락 `scope_note` 문장 8985~8987 | **8971~8973** | 〃 | 〃 |
| 분기 9006~9007 | **8992~8993** | 〃 | 〃 |
| `with open(path, "w", …)` 9023 / `json.dump(…, indent=2, …)` 9024 | **9009 / 9010** | 〃 | 〃 |
| `INSTANCE_TOP_FIELDS` 주석 8410 | **8396** | 〃 | B26-1. M9 뒤에도 SD에 남음(D0b 실측 '`INSTANCE_TOP_FIELDS`가 MOD9 → SD 잔류(A-4)') |
| `bind_hash` `4a96ecf0…ceee` | **같음**(모래상자 재계산), `body[2]` If·`body[6]` With 그대로 | -- | M9는 def를 그대로 옮기므로(`include_attributes=False`) 같음 기대. 변이 id 접두만 `instance_report_builder:` |
| design 10 235행 '선택 키 `scope_note`' | 235 같음 | -- | Phase 3 문서 개정 여부 확인 |
| `test_ic3.py` 39·44·77 | 같음 | -- | -- |
| `git grep scope_note -- A/tests` 3줄 | 3줄 같음 | -- | -- |
| `run_harness.py` 42 import·492 호출 | 같음 | -- | **F1(42 import 목적지)·M10(호출이 진입점으로)** -- S5 |
| 추적 `*.instance.json` 12개·`scope_note` 0 | 12·0 같음 | -- | -- |
| `A/tests/contracts/` 29개 | **31**(`test_b34_grammar_explicit.py`·`test_b26pre_existing_paths.py` 추가) | B34·b26pre | T0 `_engine_defs.py`, D0b `test_p3_registry_dest.py` 등 -- 착수 때 다시 셈(이름 충돌 확인 목적이라 수는 판정 무관) |
| `REPORT_DATA.json` 1682·1895 | 같음(같은 문장이 2319·2533에도 있다) | -- | -- |
| `.ai/context.md` 15025행 B41 | 같음. 처리 방침·B41a = 15043~15045행 | b4734cd가 백로그 이관 | -- |
| `_drafts/backlog_additions.md` 27행 '기본안' | 27행 = 'B41 분석 완료', 처리 방침 = 28행 | 파일 갱신 | 정본은 gate의 `.ai/context.md` 15043~15045 -- 그쪽을 인용 |
| library 9회로(`_TEMPLATE` 제외) | 같음 | -- | -- |
| `phase_order`에 `4` | 같음 | -- | -- |
| rule10 거부(V8 N/A) | 532~545(B3) | -- | [V8 도입] 답 |

### 2.2 #2

| card 인용(`dd60db6` 판) | `863a037` | 비고 |
|---|---|---|
| SR `solve_diode_stack_current` 1499, `estimate_area_budget` 2765(식 2793~2794) | 1499, 2765 같음 | |
| SR `derived_bounds_path` 7700, `load_derived_bounds` 7712, 서로 부름 7715 | **7699, 7711, 7714** | B34(SR 6507~ −1) |
| `revalidate_finger_override`의 `_invert…` 호출 11333 | **11332** | 〃 |
| docstring 언급 SR 627·1475·7757·9140 | **627·1475·7756·9139**(감싸는 def 같음: `vgs_for_gm_id`·`_invert_gm_id_for_current`·`achievable_metric_bound`·`optimize_full_circuit_budget`) | |
| SD `@dataclass` 2799·`MultiLeafHubParityVerdict` 2800·`check_multi_leaf_hub_parity` 2806 | **2793·2794·2800** | B34(SD −6/−14) |
| SD 언급 2657·2659·2851·6063·6213·7004 | **2651·2653·2845·6049·6199·6990**(감싸는 def·절 머리 주석 같음) | |
| SR `area_priors` 전달 9272 | **9271** | |
| 도구 `derive_achievable_bounds.py:69·112`, 33행 `import sizing_recipe as sr` | 같음. blob `a3e97b7…` = `9d6800e` blob, E_#2 ①·② 기준 문자열 각 정확히 1회(모래상자 재확인) | |
| test 참조: import 24행, s007 637~656, s028 1785~1801, S058 1420~1470(1436·1466 호출), s006 617, 주석 1221 | 같음 | 1221행은 `test_s014_section`(1114~1341) 안 |
| `test_ic5.py:58·62`(표 행), 251(`len == 21`) | 같음 | T0가 키를 함수 이름으로 바꿈(§4) |
| 레지스트리 §7 491·492·496·507·508행, §3 R0 143행, §2 '스택 KVL 합' 44행 | 같음 | D0b 재생성이 열·행을 다시 씀 |
| references `analog-grammar-integration.md:384` | **385** | B34(298089b) |
| 그 밖 references(`consistency-map.md:385`, `design-report-spec.md:370·400·454·492`, `function-selection-map.md:69`, `stick-diagram-euler-layout.md:647·652·672·1068·1135·1188`) | 같음 | |
| 계획 561·921·993행, design 10 264행, design 05 318·456행 | 같음 | 새 소비자: design 30 445행(A-7 규칙 예시 -- Phase 3 설계 기록, 고치지 않음 권고) |
| 운영 호출자 `revalidate_finger_override`(11298 def) | 같음 | |

### 2.3 backfill·B26-1 뒤 다시 움직일 곳

* **backfill**(`20261001-b26-backfill-interdig-final-audit`, spec card 커밋됨): `b26_1_precheck_863a037.md` 모의 = SR `_backfill_interdig_ok(result)` 두 줄(11799·11878) 삭제만 -- 두 card의 인용(SR 최대 11332) **영향 0**. code-author가 docstring 등을 더 고치면 그 판에서 `git diff -U0`로 다시 본다.
* **B26-1**: 사이트 SD 1014·1570·1612·2090·2166·3130·3235·3967·4146·4282·4298·4345·4367, SR 2207·3728~·4293 등(`draft_b26_1.spec.md` 16·66행). 그래서
  * B41: SD 8396·8959~9010 **전부 이동**(SD 1014 뒤). `bind_hash`는 `save_instance_json` 본문을 바꾸지 않으면 같음(착수 조건 4가 잡음).
  * #2: SD 2651~6990 **전부 이동**. SR 2207 뒤(2765·2789·7699·7711·7721·7756·9074·9139·9271·11298·11332) **이동**, SR 2207 앞(625·627·1471·1475·1499·1527) 그대로(B26-1이 그 앞을 고치지 않으면).
* **Phase 3(M1~M10·T1·F1·F2)**가 정의를 새 파일로 옮기므로 위 줄 번호는 모두 Phase 3 전 판 기록이 된다 -- card는 이미 '심볼로 적고 F2 병합본에서 다시 잰다'(B41 P, #2 P3)라 방향은 맞다. 고칠 것은 아래 §4의 **경로·이름**이다.

---

## 3. `parse_spec_card`·`interface_card` (gate `863a037` 도구, 모래상자)

* `role_paths.parse_spec_card(text, "20261002-b41-scope-note-test")` 통과 -- phase `4`, `test-only`, `gate_change: no`, approval `['20261002-40-defect-fixes-design']`.
* `role_paths.parse_spec_card(text, "20261002-d4-delete-unwired")` 통과 -- phase `4`, `equivalence`, `no`, 같은 approval.
* `interface_card.py <card> --root <863a037 복제본>`: B41 **2행**(`stick_diagram.save_instance_json`·`stick_diagram.run_topology_pipeline`), #2 **22행**(SR 11·SD 11, 클래스 `MultiLeafHubParityVerdict`는 표에 없음). 신규 시그니처 0.
* Phase 3 뒤 기대 모듈 열: B41 `save_instance_json` → `instance_report_builder`, `run_topology_pipeline` → `stick_diagram`(레지스트리 374행 목적지 `stick_diagram`, M 모의 이동 없음).
  #2 22행 → `gmid_lut`(`SemiEmpiricalGmIdLUT.vgs_for_gm_id`), `gmid_sizing_engine`(`_invert_gm_id_for_current`·`solve_stacked_diode_pair`·`solve_diode_stack_current`), `circuit_state_graph`(`find_hub_merge_candidates`·`resolve_constraint_references`·`propagate_topology_forced_currents`·`load_topology`),
  `theta_search`(`load_derived_bounds`·`derived_bounds_path`), `sizing_layout_convergence`(`revalidate_finger_override`·`achievable_metric_bound`·`optimize_full_circuit_budget`·`estimate_area_budget`), `stick_diagram`(`build_graph`·`check_euler_condition`·`assign_finger_geometry`·`select_layout_tool`·`audit_vertical_stack_id_euler_feasibility`·`search_shared_finger_w`·`check_multi_leaf_hub_parity`·`run_topology_pipeline`).
  (근거: D0b (d)-1 표·M3/M4/M6/M8/M9 초안 단위 목록·`cards_data.json`. stick_diagram 잔류 항목은 M 모의에 이동 기록 없음으로 추론 -- 착수 때 R-DEF로 확인.)

---

## 4. Phase 3 뒤 틀리는 경로·이름과 기대 위치 (design 30 §2.1·§8, N3.10, D0b·M·T0·T1·F1 초안)

| card·문서 | 지금 문장 | Phase 3 뒤(기대) | 근거 |
|---|---|---|---|
| B41 의도·oracle·작성 전 실측 1 | `stick_diagram.py` 8985~8987 등 docstring 위치 | `instance_report_builder.py`의 `save_instance_json`(MOD9, M9) | N3.10 529행, M9 초안 105행 |
| B41 계약 머리 | "MOD9 `instance_report_builder` … `stick_diagram`로 보이나 정본은 표" | 맞음 | -- |
| B41 '공백'·'무동작 판정 입력' | 운영 경로 `workspaces/run_harness.py` 492행 | `A/gmid_design_pipeline.py`(`run_gmid_design_pipeline` 안 호출), 하네스 import는 F1/M10 판 | S5 |
| B41 '거부해야 할 입력' | 변이 id `stick_diagram:save_instance_json:` | `instance_report_builder:save_instance_json:`(경로 `body[2]`·`body[6]` 같음 기대) | card 225행이 이미 적음 |
| B41 재현할 수치 (B)·P | 기존 대표 test `test_selftest_stick_diagram.py::test_s088_save_instance_json`, "F1이 옮긴 test" | `unit/test_mod9_instance_report_builder.py::test_s088_save_instance_json`, 옮기는 card는 **T1** | T1 매핑 k=9 |
| B41 착수 조건 5 | `test_b41`·`b41_` 0건 | 같음 + 진행 중 역할 브랜치 0 | -- |
| #2 의도 표·계약 1 | "card base의 정의 파일" | `sizing_layout_convergence.py`·`gmid_sizing_engine.py`·`theta_search.py`·`stick_diagram.py` | S6 |
| #2 P3-1 | `solve_diode_stack_current` → 시제품 `unassigned` | `gmid_sizing_engine`(A-6) | D0b 161행 |
| #2 계약 4 언급 목록 | 감싸는 def 이름 | 파일: `gmid_lut.py`(`vgs_for_gm_id`), `gmid_sizing_engine.py`(`_invert…`), `sizing_layout_convergence.py`(`achievable_metric_bound`·`optimize_full_circuit_budget`), `circuit_state_graph.py`(`find_hub_merge_candidates` 2곳), `stick_diagram.py`(`assign_finger_geometry`·`search_shared_finger_w`·`select_layout_tool`). **절 머리 주석 `# 1.8) A/C 엔진 …`**은 `propagate_topology_forced_currents`(→ MOD3)와 떨어질 수 있다(M 모의 생성기는 데코레이터~`end_lineno`만 옮김 -- `p3kit_m1/gen_move.py` 64행) -- '바로 위' 서술 대신 단어 일치 전수(P3-4)로 | M3·M4·M8 초안 |
| #2 계약 6 | `_DOMAIN_TABLE` `("stick_diagram.py", …)` 키 | T0 뒤 키 = 함수 이름(`"check_multi_leaf_hub_parity"`·`"audit_vertical_stack_id_euler_feasibility"`), 값 21개·`len == 21` 그대로 | T0 초안 계약 2 |
| #2 계약 7 | `tests/unit/test_selftest_sizing_recipe.py`, `tests/unit/test_selftest_stick_diagram.py` | test_s007·s006 → `unit/test_mod4_gmid_sizing_engine.py`, test_s028·s014(주석) → `unit/test_mod8_sizing_layout_convergence.py`, test_s058 → `unit/test_mod7_stick_diagram.py`; import 정리 = F1 판 import 문(정의 모듈), **6 이름을 import하는 모든 `unit/test_mod*.py`** | B2 |
| #2 계약 7 test id 집합 | base − {`test_s007…`, `test_s028…`} | node id = `…/unit/test_mod4_gmid_sizing_engine.py::test_s007_solve_diode_stack_current`, `…/unit/test_mod8_sizing_layout_convergence.py::test_s028_estimate_area_budget` | T1 계약 2(이름 불변) |
| #2 계약 5 도구 | `<별칭>`(일반) | F1 판 `_f1_theta_search.`(또는 from-import), 사이드카 import 처리 = S4 | F1 초안 |
| #2 계약 9 레지스트리 | §7 5행·§3 R0 1행·§2 행 | D0b 재생성 뒤 표(`근거 규칙` 열 추가, `보류(Phase 4)` 23) -- 행 수·§1 수 다시 셈 | D0b 계약 6·7 |
| #2 (새) D0b T-E | 없음 | `A/tests/contracts/test_p3_registry_dest.py` T-E 표본 3행 삭제 | B1 |
| #2 V5 목록 6·7·8 | 옛 파일 | 위 새 파일 + D0b T-E 단위 | B1·B2 |
| #2 V3 기대 `targets` | "R-DEF 정의 파일(P3-1)" | 바뀐 소스 전부(정의 4파일 ∪ 언급 파일 `gmid_lut.py`·`circuit_state_graph.py` -- 6 기대) | S6 |
| `p4_first_briefs.md` 1절 쓰기 경로·1.1 표·3.1 `git diff --name-only` 기대·3.3 V5 목록 | 옛 두 파일 다섯 개 | 새 파일 + D0b test(+ import가 퍼진 `test_mod*.py`) | B1·B2 |
| `p4_first_briefs.md` 2.1-3 | "최상위 import 줄 … 바꾸지 않는다" | S4 문장으로 | S4 |
| `b41_briefs.md` 1절 열람 허용 | `test_ic3.py`·`test_df36_instance_relpath.py` | 같음(contracts는 T1 대상 아님) | -- |
| `b41_kit/` | `stick_diagram` 하드코딩(`b41_measure.py` 17~22·69행, `b41_kill.py` 14행, `b41_run_a.sh` 32행 test id), `/c/g211`, `$(cd …)`, 변수 든 `rm -rf "$S/gate"` | Phase 3 뒤 그대로 쓸 수 없음 -- 재사용하지 않는다(브리프가 이미 역할 agent에 주지 않음). 키트 머리에 '`36e170e` 판 분석 기록, 재실행 금지' 한 줄 권고 | m |

---

## 5. V4 `test_lint` 규칙 (1)·(4) 위험 (b26pre 1차 FAIL 6건 교훈)

규칙(도구 문언 -- `review_b26pre_att2.md` 18·20행과 `863a037` `test_lint.py`): (1) 지역 대입 인라인 뒤 판정 쌍 **두 쪽에 같은 피검 호출**(인자 정규형 같음) → FAIL, (4) test 본문(중첩 def 제외)의 `assert` 문 + 이름이 `assert`로 시작하는 호출 + `pytest.raises/warns/fail/deprecated_call`이 0개 → FAIL. 도우미 안 `assert`는 세지 않는다.

* **B41**
  * (1): 피검 `save_instance_json`은 `None`을 돌려주고 판정은 `json.load` 결과끼리라 쌍에 피검 호출이 없다(NO-SUBJECT). `run_topology_pipeline`(피검)은 입력 구성에만 쓴다. 계약 3은 같은 피검 두 출력의 관계지만 파일을 거쳐 도구 (1) 대상이 아니다 -- card 99행 서술과 맞다. 위험 낮음.
    단, test-author가 `PR(n)`을 판정 쌍 한쪽에 직접 쓰면(예: `W["netlist"] == …run_topology_pipeline(…)…`) 계약에 없는 비교라 생길 일 없음.
  * (4): card 51행 "각 test 함수에 `if`·`try` 밖의 `assert`" -- 도우미(`_b41_…`)에 판정을 모으면 test 본문 assert 0으로 FAIL. **"test 함수 본문(중첩 def·`_b41_` 도우미 밖)"을 문장에 넣을 것**(수정안 §6.1-④).
* **#2**
  * (1): S058 (i)·(iii)은 '실제 그래프 kind' 대 '손 규칙' -- 한쪽만 피검(`check_euler_condition`)이라 (1) 아님. 다만 피검 집합이 22개라 **바뀐 파일 전체**에서 다른 test가 걸린다 -- S2(test_s052·s054, T1 면제 전제).
  * (4): GONE·G-1 '판정 함수'·손 규칙 helper를 도우미로 두면 assert는 반드시 test 본문에 -- 도우미는 목록/값을 돌려주고 test가 `assert … == []`. 브리프 1.3의 '판정 함수가 보고' 문장이 도우미 안 assert로 읽히지 않게(수정안 §6.2-⑥).
  * (2)(참고): S058 비교 쌍의 피검 쪽은 `Call`이 아니라 `.kind`·비교식이라 UNJUDGED -- auditor oracle 대조 대상(basis에 손 규칙 출처 문장). FAIL 아님.
  * 재사용: T0가 `A/tests/contracts/_engine_defs.py` `engine_source_files()`(A/*.py + `run_harness.py`)를 만든다 -- GONE·G-1 스캔 대상 목록은 그것을 쓰라고 적으면 정의 하나 원칙에 맞다(메모리 '재사용 레지스트리 확인').

---

## 6. 정확한 수정안

### 6.1 `draft_b41_scope_note.spec.md`

① 90행 교체(B3 -- [V8 도입] 권고 답 기준. '도입 4 + 게이트 예외' 답이면 그 판 형식으로):
```
* V8: **N/A**, basis `도입 5: 폴백 계측은 Phase 4 작업(N6.1), V8은 Phase 4 DoD(E1)에서 도입 -- 이 card는 test 파일 하나만 더하고 부록 C 사이트 불변`(계획 N4.2 V8 도입 = 5 -- [V8 도입] 답·계획 승인 기록 `<날짜>-plan-v8-intro`가 이 card push 전 gate에 있어야 한다; 지금 도입 4에서는 rule10이 N/A를 거부한다 -- merge_gate 541~545행).
  V9: **N/A**, basis `도입 6b: 물리 불변식 검사는 Phase 6b부터(N4.2 V9 도입 = 6b)`.
```
② '결정 필요 항목' 165행 "사용자 결정 없음 -- 아래는 원칙으로 정한 기본안이다." → "이 card 고유의 사용자 결정 없음 -- 아래는 원칙으로 정한 기본안이다. **단 V8 판정 모양은 Phase 4 승인 묶음의 [V8 도입] 답(`phase4_approval_question.md`)에 달렸다**(착수 조건 6)."
③ 착수 조건 5 뒤에 추가:
```
6. [V8 도입] 답과 그 계획 커밋: `git -C "$R" show "$H:docs/01-plan/features/gain-budget-gmid-sizing.plan.md" | grep -n '^| V8 '`의 도입 칸이 답과 같고(권고 답이면 `5`), 그 `plan_tables` 승인 기록이 `$H`에 있다. 없으면 V8을 어떤 모양으로도 통과할 수 없으므로 멈춘다.
```
④ 51행 "각 test 함수에 `if`·`try` 밖의 `assert`가 하나 이상 있다." → "각 test 함수 **본문**(중첩 def·`_b41_` 도우미 밖)에 `if`·`try` 밖의 `assert`가 하나 이상 있다(도우미 안 `assert`는 V4 규칙 (4)가 세지 않는다 -- b26pre 1차 V4 FAIL 238·494·505행)."
⑤ '작성 전 실측' P(218행) 끝에 추가: "`save_instance_json`의 운영 호출 위치(M10 뒤 `A/gmid_design_pipeline.py` -- 거기서 `scope_note`를 넣지 않음을 다시 확인)와 `run_harness.py`의 그 import(F1·M10 판), 기존 대표 test 위치는 **T1**이 옮긴 `unit/test_mod9_instance_report_builder.py::test_s088_save_instance_json`." 그리고 같은 줄의 "(F1이 옮긴 test 위치 포함)" → "(T1이 옮긴 test 위치 포함)".
⑥ 19행 '공백'의 "운영 경로 `workspaces/run_harness.py` 492행 호출도 넣지 않고" → "운영 경로(측정 판 `workspaces/run_harness.py` 492행 -- Phase 3 M10 뒤에는 `A/gmid_design_pipeline.py`의 진입점, P에서 다시 잼) 호출도 넣지 않고". 139행 무동작 문장의 "운영 경로(`run_harness.py`)" → "운영 경로(M10 뒤 진입점 `run_gmid_design_pipeline`과 그것을 부르는 하네스)".
⑦ 10행 "기본안 `_drafts/backlog_additions.md` 27행" → "처리 방침 `.ai/context.md` 15044행(B41a 15045행)".
⑧ '작성 전 실측' 끝에 판 갱신 문단(선택): "(gate master `863a037` 재확인 2026-10-07) B34로 SD −14: `def save_instance_json` 8959, 첫 단락 8961~8963, `scope_note` 문장 8971~8973, 분기 8992~8993, `with` 9009, `json.dump` 9010, `INSTANCE_TOP_FIELDS` 주석 8396. `bind_hash` 같음, `body[2]`·`body[6]` 같음. contracts 31개. 다른 사실 같음. B26-1(SD 1014~ 편집) 뒤 다시 이동, M9 뒤 정의 파일 `instance_report_builder.py`."

### 6.2 `draft_p4_first.spec.md`

① 125행 교체(B3+S1):
```
V8: **N/A**, basis `도입 5: 폴백 계측은 Phase 4 작업(N6.1), V8은 Phase 4 DoD(E1)에서 도입 -- 이 card는 부록 C.2 사이트 둘을 정의와 함께 지운다(SR `estimate_area_budget` 안 `n_samples` 기본값 `0`, `solve_diode_stack_current` 안 `vsb` 기본값 `0.0` -- design 40 부록 C.2 1388행·1398행 첫 값), 더하거나 바꾸는 사이트 0`([V8 도입] 답이 '도입 5'일 때. 답이 다르면 그 형식으로. 지금 계획 N4.2 V8 도입 = 4에서는 rule10이 N/A를 거부한다).
```
② 의도 표 아래(21행 '함께:' 앞)에 추가(B1):
```
함께(Phase 3 D0b 영구 test): `A/tests/contracts/test_p3_registry_dest.py`의 결정 사실 표본 test(D0b T-E, 접두 `test_p3rd_`)에서 이 card가 지우는 단위의 표본 세 행(`solve_diode_stack_current` A-6, `MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity` A-7)을 지운다 -- 남기면 병합본에서 '행 있는 표본은 대상 행' 단언이 FAIL한다(정의·레지스트리 행이 없다). 다른 표본은 바꾸지 않는다. A-6·A-7 규칙의 남는 표본이 0이 된다(대체 표본은 D0b oracle (d)-1 몫 -- 백로그).
```
   계약 7 끝에 같은 내용을 test 계약으로 한 항목(7-b) 더하고, '결정 필요 항목' V5 목록에 "9 `tests/contracts/test_p3_registry_dest.py`, <T-E 함수>(예: 표 행 삭제 -- 리터럴 변경·비교 완화)"를 더한다(→ 8건).
③ 계약 7 첫 문장 교체(B2):
```
7. **기존 test 정리(test, V5)**: T1 매핑(`docs/03-analysis/gain-budget-gmid-sizing-30-module-split/t1-mapping.json`)으로 옮겨진 파일에서 -- `test_s007_solve_diode_stack_current`(T1 모의 k=4 → `A/tests/unit/test_mod4_gmid_sizing_engine.py`)·`test_s028_estimate_area_budget`(k=8 → `A/tests/unit/test_mod8_sizing_layout_convergence.py`)을 지우고,
   card base의 `A/tests/**` 중 6 이름을 import하는 **모든** 파일(T1이 옛 머리를 목적 파일마다 원문 복사하므로 여럿일 수 있다 -- card base에서 `git grep -n -w` 결과로 정한다)의 import 문(F1이 정의 모듈로 바꾼 판)에서 `estimate_area_budget`·`solve_diode_stack_current`·`check_multi_leaf_hub_parity`를, 그리고 `_invert_gm_id_for_current`를 그것을 더 쓰지 않는 파일에서 뺀다.
```
   이어지는 '낡은 언급 두 곳'의 파일을 "`test_s006_solve_id_for_target_gm`(k=4 → `test_mod4_gmid_sizing_engine.py`) docstring", "`test_s014_section`(SR 출신, k=8 → `test_mod8_sizing_layout_convergence.py`) 안 `mismatch_sigma_mV` 제외 사유 주석"으로, `test_s058_section`은 "(k=7 → `A/tests/unit/test_mod7_stick_diagram.py`)"로. 57행 test id 집합도 새 node id로.
④ 계약 2에 한 구절(S3): "… 값으로 등록돼 있지 않다 -- 딕셔너리는 `Assign`과 `AnnAssign`(예: `_THETA_FEED_REGISTRY: dict = {…}`) 둘 다의 값 dict이다(base에서 판정 …)". 스캔 대상 목록은 T0 `_engine_defs.engine_source_files()`를 쓴다는 구절을 계약 3·4에도.
⑤ 계약 5 41행 "그 밖의 줄(경로 줄·계산·탐색 인자·선언 기록 블록)은 바꾸지 않는다(범위 계약)." 뒤에 추가(S4):
```
   예외 하나: card base 도구에서 최상위 엔진 import(F1 판 -- 별칭 `import <정의 모듈> as <별칭>` 또는 `from <정의 모듈> import …`)가 **지운 두 이름만** 위해 있으면 그 import(또는 from-import의 두 이름)를 지운다 -- 남기면 쓰는 곳 0인 바인딩이고, from-import 모양이면 계약 3 GONE(import 참조)이 FAIL한다. 최상위 엔진 import는 (A3) 정규형 밖이라 핀과 무관하다(r3 실측 S2b·S2f PASS).
```
   (`p4_first_briefs.md` 2.1-3 끝 "최상위 import 줄은 바꾸지 않는다"도 같은 예외로.)
⑥ '거부해야 할 입력' 첫 글머리 끝에 추가(§5): "판정 함수·손 규칙 helper는 목록·값을 돌려주고 `assert`는 test 함수 본문에 둔다(V4 규칙 (4)는 도우미 안 `assert`를 세지 않는다)."
⑦ '판정 유형 근거'에 V4 한 줄(S2): "V4: 바뀐 test 파일 전체가 lint 대상이다. #2 피검(22)에 `optimize_full_circuit_budget`·`revalidate_finger_override`가 있어 `test_mod8_sizing_layout_convergence.py`의 `test_s052_compensation`·`test_s054_section`(·`test_s009_revalidate_finger_override`)이 규칙 (1)에 걸린다 -- T1 새 id decision 면제 `20261006-p3-t1-v4-exempt`가 head 트리에 있으면 `exempt`(`863a037` 옛 파일 실측: (1) exempt 2, (2) FAIL 1 = 지우는 `test_s028`). 그 기록이 없으면 착수하지 않는다."
⑧ P3-1 교체: "`solve_diode_stack_current` → 시제품 `unassigned`" → "`solve_diode_stack_current` → `gmid_sizing_engine.py`(D0b (d)-1 A-6, M4 초안)". P3-7·P3-10 (a)의 V3 기대 "`targets`는 R-DEF 정의 파일" → "`targets` = 바뀐 소스 전부(정의 4파일 + 계약 4 언급만 바뀌는 파일 -- 6 기대), `mutants` 0".
⑨ P3 절에 P3-11 추가: "**D0b T-E 표본**(B1)·**T1 매핑과 import 퍼짐**(B2)·**T1 V4 면제 기록**(S2)·**F1 도구 import 모양**(S4)을 card base에서 확인."
⑩ 10행 "초안 v0.9.9, 승인 전" → "초안 v0.9.11, 승인 전". '작성 전 실측' 5의 `analog-grammar-integration.md:384` → `:385`(B34). 새 소비자 design 30 445행(A-7 규칙 예시)은 Phase 3 설계 기록이라 고치지 않는다는 한 구절.

### 6.3 `p4_first_briefs.md`

* 1절 test-author 쓰기 경로 5파일 → "새 `tests/contracts/test_d4_delete_unwired.py`, `tests/contracts/test_ic5.py`, `tests/contracts/test_ts6_probe_relocate.py`, `tests/contracts/test_p3_registry_dest.py`(D0b T-E 표본 3행), card 계약 7이 정한 `tests/unit/test_mod*.py`(최소 `test_mod4_gmid_sizing_engine.py`·`test_mod7_stick_diagram.py`·`test_mod8_sizing_layout_convergence.py`)". 1.1 표·3.1 `git diff --name-only` 기대·3.3 V5 목록(6·7·8 파일 이름, 9 추가)을 같게.
* 3.3 V3 행 `targets` = 바뀐 소스 전부(6 기대). V4 행에 "T1 V4 면제 기록이 head 트리에 있어 s052·s054(·s009) 규칙 (1) = `exempt`, 그 밖 FAIL 0" 기대.
* 0.1 C-5/0.2: S1(부록 C 사이트 2개 삭제) 사실을 basis 문안에 반영(위 6.2-①).
* 0.3 표에 P3-12 "D0b T-E 표본·T1 매핑·T1 V4 면제·F1 도구 import 모양" 행.

### 6.4 `b41_briefs.md`

* 2.2 V8 행 → 6.1-① basis 문안, V9 행 → `도입 6b: …` 형식. 0.2에 "6. [V8 도입] 답·계획 커밋이 gate에 있음(card 착수 조건 6)".
* 2.2 V2 행 "변이 위치는 (def, 문장 원문)으로 base에서 찾고" 뒤에 "(정의 파일 = `instance_report_builder.py`, 변이 id 접두 `instance_report_builder:`)".

### 6.5 `phase4_approval_question.md`

* UD-0 #2 문단 27행 "영역 표 두 행 삭제(21 → 19), 지운 함수의 test 두 개 삭제, 그리고 …" → "영역 표 두 행 삭제(21 → 19), 지운 함수의 test 두 개 삭제, **Phase 3 이관표 확인 test(D0b)의 결정 사실 표본 중 지운 함수 세 개의 표본 삭제(그 규칙 A-6·A-7의 표본이 남지 않음)**, 그리고 …" (B1 -- 사용자가 보는 승인 범위).
* [V8 도입] '답 뒤 고칠 파일' 3번의 basis 문안을 card별로: B41 = '부록 C 사이트 불변', #2 = '부록 C.2 사이트 둘 삭제(…), 더하는 사이트 0'(S1).

### 6.6 `draft_phase4_design.md` (참고)

* 부록 C.2 1388행(`n_samples`)·1398행(`vsb` 첫 값 1527)의 담당 칸을 "#2 (정의 삭제)"로, C.4 계수를 그만큼(S1). §5.1 #2 행에 D0b T-E 표본 삭제(B1)와 T1 파일 이름(B2).

---

## 7. 검토 범위 밖·남은 확인

* D0b 실제 test 본문(함수 이름·표 구조), T1 실제 매핑 표와 F1의 import 정리 규칙(안 쓰는 이름을 빼는지), T1-2 답(면제 (가)/(나))은 아직 gate에 없다 -- 위 B1·B2·S2·S4는 초안 문장과 모의 출력에 근거한 예보이고, 착수 때 card base에서 다시 잰다.
* 이 검토는 test·모의 병합을 돌리지 않았다(실행은 `bind_hash`·E_#2 기준 문자열 1회·`parse_spec_card`·`interface_card`·`test_lint` 한 번뿐).
