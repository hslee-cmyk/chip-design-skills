# review_p3_f2_r3 -- F2 spec card r3(`draft_p3_f2.spec.md`) 독립 검토

작성 2026-10-06. 검토자는 F2 초안·시제품·사슬 스크립트·자기 점검표의 작성자가 아니다. 판 = gate `master` `6c724de`(실제 저장소 `HEAD`·`master`·`gate/master` 모두 `6c724deb…`).
환경: 스크래치 `C:/g324`만 사용(TMP/TEMP = `C:/g324/tmp`, `cd` 없음, 모든 경로 인자로 넘김). 실제 저장소는 읽기만 했다(`status --porcelain` md5 `76eea762…` 시작 = 끝, HEAD 불변). 작업 끝에 `C:/g324` 삭제.
게이트 도구 = `git archive 6c724de tools/gates`(`C:/g324/gc`).

**판정: S 0 · minor 4 · 정보 3 -- 블로커 없음. 계약 그대로 test-author·code-author에 넘길 수 있다.** 아래 minor는 사실 문장 정정과 auditor 브리핑 몫이고, 계약 판정은 바뀌지 않는다.

## 1. 재현 환경

* 사슬: `mk_chain_r1.sh C:/g324 <저장소> _drafts/g1_kit/install_proto.py 6c724de` -- **손 단계 없이 exit 0**(D-11 'already present' 빈 커밋, `installed 4`). `APPDATA` export가 들어가 `sim_m_d31.py` import 확인 `import_fail` 전 card `{}`가 첫 실행에서 바로 나옴(자기 점검 D2 해소 확인).
  커밋: G1 `688a9de` → M1~M9 `9440d90` → M9 정정 `9d626b9`(F1 모의 base) → F1 없는 F2 `2e05258` / F1 모의 `862bb1b` = **F2 base** → F2 모의 `c5b0393` = **head**. `f12_f1sim.py` `changed 72`·D-17 8파일.
* 시작 판을 card의 `2183f2e`가 아니라 `6c724de`(그 뒤 한 커밋, 문서만)로 잡았다 -- 아래 수치가 모두 같게 나와 '`2183f2e`+' 판에서도 재현됨을 겸한다.

## 2. 항목별 결과

| # | 확인 | 결과 | 근거(내 측정) |
|---|---|---|---|
| 1 | 계약 1 diff | 일치 | `diff --numstat f2base f2head`: 5파일, ACF 1/2·DR 0/29·SR 0/57·SD 2/3·TL 0/25 = 3줄 더함·116줄 지움 |
| 2 | 계약 2 삭제 집합 | 일치 | `mk_f2.py`: SD 지움 49(목록 = card 계약 2 문맥), 남는 SD 재수출 41행 6이름 + 42행 2이름 = 8, ACF 지움 `_as_set`·`_theta_evidence_for_pair`, 남김 `audit_topology`. '판 확인': 모의 F1 base·F2 base SD blob `7698f905` 같음, ACF `2b2cd156` 같음 |
| 3 | **계약 6 red-green(test-first)** | **재현** | r3 시제품(`proto_r3.py`로 이름만 바꿔 실행): F2 base `862bb1b` **2 failed** -- (a) `AssertionError: shim 파일이 남아 있다: [sizing_recipe, topology_library, design_report]`, (b) `AssertionError`(`import_layering` exit 1, cycle `instance_report_builder → stick_diagram → instance_report_builder`), 다른 예외 0. head `c5b0393` **2 passed**. F1 없는 F2 `2e05258` 2 failed(둘 다 `AssertionError`, 미해석 69) |
| 4 | **계약 6 (b) 읽기 정의 = E3b `file_reads`** | **일치(구조 + 실측)** | (i) 구조: design 30(`6c724de`) §10 `E3B_AST`에서 `file_reads`를 잘라 시제품 `_file_reads`와 `ast.dump` 비교(docstring 제거) → **같음**. `IMPF`·`ATTRF`·`IMPL` 상수도 같음. (ii) 실측: F1 없는 F2에서 design §10 E3b 블록 그대로(`run_sec10.sh` 사본, B0 = G1 `688a9de`) `E3b FAIL` **78줄·13파일**, 그중 판정 트리 + `workspaces/run_harness.py` 몫 **69**와 시제품 r3 미해석 **69가 집합으로 같음(69/69, 차집합 양쪽 0)**. 파일별: test_b34 29·test_selftest_stick_diagram 27·test_df36 4·test_ic3 4·test_dup_kcl_edges 2·test_selftest_design_report 1·run_harness 2, 범위 밖 workspaces 두 폴더 9 -- card 199행과 같음 |
| 5 | 계약 3·4·7(E3·E3b·IMPORT-ANY) | 일치 | F2 base: `E3 FAIL: <shim> 있음` 3줄 + `E3 PASS`, `E3b LIVE moved_out=57 base_files_reading_moved_out=33 pre_existing=1`·`E3b PASS`, `IMPORT-ANY tried=13 expected=13 failed=0`. head: `E3 PASS`, `E3b LIVE 57/33/1`·`E3b PASS`, `IMPORT-ANY tried=10 expected=10 failed=0` |
| 6 | 계약 5 LAYER | 일치 | 시제품 보고: F2 base `layering_exit=1`, head `0`(모의라 `present` 9) |
| 7 | **계약 10 D-9 27줄** | **정확** | head 측정판(`noexcl`): `E3 FAIL` 1파일 `probe_stage_partition.py`, `E3b base_files_reading_moved_out=45`, `E3b FAIL` **27줄** = `c7_digest.py:42~50·52`(10) + `discrim_b34.py:20~28·30`(10) + `e_lib_inst.py:35 save_instance_json` + `diff_dup.py:17 _import_analog_grammar·:32 _kcl_and_matching_edges` + `probe_stage_partition.py:29 _RAIL_NETS·315 find_structural_symmetry_candidates·633 find_differential_pair_candidates·641 trace_vdd_to_gnd_branches`. 줄 번호·이름 모두 card 문장과 같음 |
| 8 | **계약 12 키 목록** | **실제 출력과 일치** | base 판 도구(모의 F2 base 트리 `tools/gates`, `run_vtools.sh` 사본) `f2base → f2head`: V3 `PASS`·`targets` [ACF, SD]·`mutants` 0·`killed` 0·`survivors` []·`survivor_bindings` []·`exempt_ignored` []·`not_targeted` 0·`targets_by_def` {}·`defs` []·`moved` []·`move_rejected` {}; V6 `PASS`·`findings` []·`moved` []·`move_rejected` {}; V7 `PASS`·`new_defs` []·`unreached` []·`unreached_without_approval` []·`moved` []·`move_rejected` {}; V5 `PASS`·`findings` []·`diff_paths` []. 시제품을 `contracts/test_p3_shim_delete.py`로 더한 커밋(`16fc204`)도 V3·V5·V6·V7 같은 값(V5 `diff_paths` [] -- 새 파일은 V5 대상 아님). 계약 12가 적은 키는 전부 출력에 있고 값이 맞다(적지 않은 키 `killed`·`survivor_bindings`·`exempt_ignored`·`unreached_without_approval`도 모두 빈 값 -- 정보) |
| 9 | 계약 11 references | 일치 | `6c724de`에서 12파일·74줄 |
| 10 | 이름 충돌 | 0 | `git grep -E "p3_shim_delete|p3sd_" 6c724de` 0건 |
| 11 | ACF reader(결정 1 기록) | 일치 | `git grep audit_current_forced 6c724de -- '*.py'`: import 0, 문자열 3(`count_selftest_sections.py:26`·`test_df23_inventory.py:56`·`test_ic5.py:48`) + ACF 자신 사용법 32행 |
| 12 | parse_spec_card | 성공 | gate `6c724de` `role_paths.parse_spec_card(expect_id=…)`: `id` `20261002-p3-shim-delete`, `phase` 3, `evidence_type` red-green, `gate_change` no, `approval` [`20260930-30-module-split-design`], 11절 |

## 3. A3(계약 9 '전체 이력' 전제) -- 정당함, fail-closed 실측

* 얕은 복제(`clone --depth 1 file://<저장소>`, `is-shallow-repository` true, HEAD `6c724de`)에서 PT3(design §10 정의, `--gmid-dod`)로 `test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines` 실행 → **1 failed**, `AssertionError: base 939f926의 …/derive_achievable_bounds.py를 읽지 못했다`(`git show` rc 128). **지금 판의 test(F1 전)도 이미 git 이력에 기대 닫힌 쪽으로 FAIL한다** -- 전제는 F1 (마) 뒤에만 생기는 것이 아니다.
* F1 (A1)/(A3)이 부를 git 명령을 같은 얕은 복제에서 직접 실행: `rev-list --parents -n 1 9d6800e…` rc 128(`bad object`), `merge-base --is-ancestor 9d6800e HEAD` rc 128, `show 9d6800e:<새 자리>` rc 128, `ls-tree a574f97 -- <새 자리>` rc 128 -- F1 계약 1 (d) 문언('읽기 실패는 거부')대로면 전부 거부 → base·head 모두 FAIL. 이동 커밋 부모를 `--shallow-exclude`로 뺀 두 번째 얕은 복제에서도 넷 다 rc 128.
* 대조: 전체 이력 복제본(사슬 `--no-local` clone)에서는 `9d6800e`·`939f926`·`36e170e`·`a574f97` 모두 `commit`, `merge-base --is-ancestor 9d6800e f2head` exit 0. (그 복제본의 모의 F1은 (마)를 적용하지 않아 이 test가 F2 base·head 모두 FAIL하고 head는 앵커 test `test_assets_dir_holds_engine_entry_points`도 FAIL -- card 결정 4·'측정하지 않은 것'과 같은 사실, 환경 탓 아님.)

## 4. 거부해야 할 입력 -- 경계 사례(시제품 r3, head 트리에 판정 트리 파일을 index에 더해 실행)

| 사례 | (a) | (b) | 미해석 보고 |
|---|---|---|---|
| `_sd()` 반환 함수 호출(card 사례) | pass | **FAIL** | `:6 _kcl_and_matching_edges` |
| 다음 줄로 이어진 `from stick_diagram import (\n load_topology,\n save_instance_json,\n)` | pass | **FAIL** | `:1 save_instance_json`(문장 첫 줄 번호로 보고, `load_topology`는 남는 이름이라 통과) |
| 파일 첫 줄 `import stick_diagram as s; s.find_idiom_matches` | pass | **FAIL** | `:1` |
| 중복(같은 이름 한 파일 두 번 + 다른 파일 from-import) | pass | **FAIL** | 3자리 모두 |
| 한 문장 여러 별칭 `import stick_diagram as a, stick_diagram as b` | pass | **FAIL** | `b.` 자리 |
| 함수 사슬 `_a()`→`_b()`→`import_module` (고정점) | pass | **FAIL** | |
| `getattr(s, "상수")` / `getattr(s, 변수)` | pass | **FAIL** / **FAIL** | 이름 / `<동적 이름>` |
| `__import__("stick_diagram").X`, walrus 대입, `from stick_diagram import *` | pass | **FAIL** | |
| 남는 이름만 읽기(`load_topology`·`Transistor`) -- 수용 | pass | pass | 0 |
| shim: 함수 안 `import topology_library`, `__import__("design_report.x")`, 첫 줄 `from sizing_recipe import x` | **FAIL** | pass | |
| 과대 삭제 head(SD 41행에서 `load_topology` 제거) | pass | **FAIL** | 12자리(ACF:43·test_b34 등) |

공통 사각(시제품 = design E3b/E3과 **같은 정의라 F2 고유 결함 아님**, 정보): `lambda: import_module("stick_diagram")` 대입, 메서드 `self._sd()`, `from importlib import import_module as im`, `sys.modules["stick_diagram"]`, 비상수 `import_module(n)`, 상대 import `from .sizing_recipe` -- 모두 통과(놓침). 지금 `6c724de` 추적 `.py`에 그 꼴 0(`git grep`). 넓히려면 design §10 E3/E3b와 함께 바꿔야 한다(정의 하나).

## 5. minor

* **m1 거부 입력 첫 항목의 결과 문장이 사실과 다르다.** "SD가 읽는 이름의 재수출까지 지운 head → **SD 자신 import 시 `NameError`**/IMPORT-ANY FAIL". 실측: SD 41행에서 `load_topology`를 빼도 `import stick_diagram` 성공(`Transistor`·`kcl_series_union`·`find_stack_edges`를 각각 빼도 성공 -- 모두 함수 본문 안에서만 읽힘). 실제로 FAIL하는 것은 (i) 계약 1·2(삭제 집합 불일치) (ii) 계약 6 (b)·E3b(그 이름을 읽는 reader가 있으면 -- `load_topology`는 12자리) (iii) IMPORT-ANY는 `load_topology`일 때만 ACF `from stick_diagram import load_topology`의 `ImportError`로. 권고: "SD 자신 import 시 `NameError`"를 "호출 시 `NameError`; 판정은 계약 1·2, reader가 있으면 계약 6 (b)·E3b, `load_topology`는 ACF import로 IMPORT-ANY FAIL"로.
* **m2 V3 `ERROR` 원인 문장(작성 전 실측 r3 'review D3 원인 확정')이 재현과 다르다.** 내 재현: 커밋이 ref(`f2headT` 브랜치)에서 닿는데도 **브랜치 이름**을 `--base/--head`로 주면 `git checkout: --detach does not take a path argument 'f2headT'`로 V3 `ERROR`, 같은 커밋을 **40자 sha**로 주면 `PASS`(위 표 8 값). 원인: `mutate_changed.make_clone`의 `--no-local` 복제본에는 원 저장소 HEAD 브랜치 하나만 `refs/heads/`로 생기고 나머지는 `refs/remotes/origin/*`이라, 그 밖의 브랜치 이름은 커밋으로 풀리지 않는다(내 복제본 `for-each-ref`: 로컬 브랜치 `f2head` 하나). '어느 ref에서도 닿지 않는 커밋'도 같은 오류를 낼 수 있지만 그것만이 원인은 아니다. 그래서 "auditor worktree는 브랜치 위에서 판정하므로 생기지 않는다"는 **sha를 넘길 때만** 맞다. 권고: 문장 정정 + auditor 브리핑에 'V 도구 `--base/--head`는 40자 sha'(계약 변경 아님).
* **m3 계약 9 전제의 근거 범위.** 전제는 F1 (마)에만 기대지 않는다 -- 지금 판 test도 `git show 939f926:…`로 얕은 복제에서 FAIL한다(3절). 그리고 '`git clone --no-local` 전체 clone'만 적어 두면 역할 정의의 audit **worktree**(`<W>/<id>-audit`, 전체 이력 저장소의 worktree)가 허용되는지 문면상 애매하다. 권고: "전체 이력을 가진 저장소(`--no-local` 전체 clone 또는 그 worktree)"로, 근거에 '지금 판 test의 `939f926` blob 읽기도 같다'를 한 줄. 덧붙여 `git archive` 트리를 다른 git 저장소 **안**에 풀면 `git -C` 가 바깥 저장소를 찾아 닫힌 쪽이 아니게 될 수 있다 -- 금지 목록에 이미 있으므로 문장 그대로 충분.
* **m4 F1과의 정합(TS6 규칙·좁힌 쓰기 경로 행) -- 어긋남 없음, 표현만.** F2 계약 1(test 커밋 = 새 파일 하나·그 밖 0)이 F1 '핀 변경 규칙'(정규형 불변 card는 핀 불변)을 강제하고, 거부 입력 'TS6 핀을 고친 head'가 그것을 문서로 잇는다 -- F1 계약 1 (d) 문언과 같다. 좁힌 두 행(`workspaces/current-reuse-telescopic-ota-report/*.py`·`workspaces/two-stage-ota-report/*.py`)은 F2가 쓰지 않으므로 `approval:`에 없는 것이 맞고, 결정 3이 '그 22파일은 상시 test 밖(DoD E3·E3b만)'을 이제 명시한다(실측: F1 없는 F2 E3b 9줄이 그 두 폴더). 단 결정 3 문장 '두 폴더 바로 아래 `.py` 18·4 = 22파일'은 내가 세지 않았다(검토 범위 밖, 정보).

## 6. 정보

* i1 계약 6 (b)의 판정 범위에서 E3b의 `pre_existing` 면제는 쓰지 않는다 -- 범위(판정 트리 + 하네스) 안 `pre_existing` 쌍이 0이라 지금은 차이 없음(유일한 1쌍 `stick.py`는 범위 밖). 범위 안에서 base에 이미 풀리지 않는 이름이 생기면 상시 test가 E3b보다 엄격해진다(닫힌 쪽 -- 문제 아님).
* i2 시제품 파일 이름 `test_p3_shim_delete.proto.py`는 점 때문에 pytest가 모듈로 import하지 못한다(`ModuleNotFoundError: No module named 'test_p3_shim_delete'`) -- card의 시제품 실행 명령(`python -m pytest test_p3_shim_delete.proto.py`)은 이름을 바꿔야 돈다. 측정 키트 문제, card 계약 무관.
* i3 사슬 스크립트 `mk_chain_r1.sh`의 r3 수정(APPDATA·HOME export)은 효과 확인됨. F1 없는 F2 커밋은 분리 HEAD라 reflog에서만 찾을 수 있다(브랜치를 남기지 않는다) -- V 도구에 sha를 넘기면 무관.

## 7. 재현 수치 요약(내 스크립트, `C:/g324`)

E3b F1 없는 F2 78줄·13파일, 범위 69 = 시제품 69(집합 같음); D-9 측정판 27줄·E3 1파일; IMPORT-ANY 13 → 10; diff 5파일 +3/−116; SD 57 → 49·8, ACF 3 → 2·1; red 2 failed(AssertionError 둘)/green 2 passed; V3·V5·V6·V7 키 값 = 계약 12; references 12파일·74줄; 얕은 복제 TS6 test FAIL(rc 128). card '작성 전 실측' r3 단락의 수치와 모두 같다.
