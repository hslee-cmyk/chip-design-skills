# review_p3_f2_r4 -- draft_p3_f2.spec.md r4 변경분 독립 검증

검증자: 독립 verifier(작성자 아님). 대상: `draft_p3_f2.spec.md` vs `draft_p3_f2.spec.md.pre-r4.bak` diff 9 hunk(23, 55~58, 68~69, 101~104, 109, 145~146, 185, 188, 215~219, 246~254).
판: 실제 저장소 `HEAD`·`master` = `6c724debd884dd1d31034f5279ae450f35e67fc4`, 읽기만(`status --porcelain` md5 `76eea762…` 시작 = 끝).
스크래치 `C:/g338`(TMP/TEMP `C:/g338/tmp`, cd 없음, clone `-c core.autocrlf=false`), 작업 끝에 삭제.

## 판정: **B 0 · S 0 · minor 3** -- r4 변경 문장 전부 실측과 일치, 계약 판정 기준 변경 없음

## 1. 재수출 이름 삭제 결과(hunk 101~104, 251)
* 사슬 재구성: `p3kit_f12/mk_chain_r1.sh C:/g338 <저장소> g1_kit/install_proto.py 6c724de` 손 단계 없이 **exit 0**.
  D-11 'already present' 빈 커밋 → G1 → M1~M9 → M9 정정 → F1 모의 → F2 모의(내 해시 `28ec01a`(M9 정정)·`24a500f`(F1 모의)·`afa6cad`(F2 모의) -- 날짜 의존이라 card의 `e50a1e0`·`4dd48ef`·`2f0180c`와 다름은 예상대로).
  `changed 72 notes 1 d17 files 8`, SD dropped 49, ACF dropped 2 -- card 250행과 같음. M 카드 `import_fail` 전부 {}.
* head SD 41·42행 = `from circuit_state_graph import Transistor, …, kcl_series_union, load_topology` / `from topology_authoring import _scan_case_collisions, find_stack_edges` -- card '41·42행 재수출 문' 맞음.
* 이름 하나씩 빼고 측정(새 프로세스, `sys.path`=assets, 시제품 `_sd_unresolved()` 직접 호출):

| 뺀 이름 | `import stick_diagram` | `import audit_current_forced` | 미해석 |
|---|---|---|---|
| (없음) | rc 0 | rc 0 | 0 |
| `load_topology` | rc 0 | rc 1 `ImportError: cannot import name 'load_topology' from 'stick_diagram'` | **12** (ACF·test_b34·test_ic3·test_selftest_stick_diagram·topology_to_markdown) |
| `Transistor` | rc 0 | rc 0 | **9** |
| `find_stack_edges` | rc 0 | rc 0 | **8** |
| `kcl_series_union` | rc 0 | rc 0 | **0** |

  card 문장(넷 다 SD rc 0, ACF는 `load_topology`만 `ImportError`, 12·9·8·0) **전부 일치**.
* 'IMPORT-ANY는 `load_topology`를 지웠을 때만 FAIL' 추가 확인: `topology_to_markdown.py:29`도 `from stick_diagram import load_topology`라 import하면 깨지지만, design 30 §10 `import_any` 집합(head 계획 `mod_table` = gmid_lut topology_authoring circuit_state_graph gmid_sizing_engine circuit_metrics theta_search stick_diagram sizing_layout_convergence instance_report_builder gmid_design_pipeline + `--split` 파일)에 없으므로 IMPORT-ANY에서 FAIL은 ACF 하나 -- card 문장 맞음.

## 2. V3 `make_clone` 브랜치 이름 vs sha(hunk 68~69, 185, 215~219)
* gate `6c724de` `tools/gates/mutate_changed.py` 59~64행: `clone --quiet --no-checkout --no-hardlinks --no-local -c core.longpaths=true` → `remote remove origin` → `checkout --quiet --detach <head>` -- card 인용 맞음. 627행 `make_clone(root, work, ns.head)`.
* 장난감 저장소 재현(`C:/g338/toy`, 브랜치 `main`(HEAD)·`b2`, 태그 `t1`, 같은 clone·remove 순서): 복제본 ref = `refs/heads/main`·`refs/tags/t1`; `checkout --detach b2` **rc 128** `fatal: git checkout: --detach does not take a path argument 'b2'`(card 문장 그대로), 같은 커밋 sha rc 0.
* card의 원인 (가)(나) 설명 맞음. 계약 12 '실행 조건'은 '판정 기준 아님'으로 명시돼 있고 판정 키는 그대로.

## 3. 계약 9 전제 + `base_blob_text` 239~242행(hunk 55~58)
* gate `6c724de` `contracts/test_ts6_probe_relocate.py`: 237행 `def base_blob_text`, 239행 `subprocess.run(["git","-C",str(_REPO_ROOT),"show",f"{_BASE_COMMIT}:{rel_path}"]…)`, 241~242행 `assert proc.returncode == 0` → `AssertionError`. 96행 `_BASE_COMMIT = "939f926fe97b…"` -- card 인용 맞음.
* 실측: 얕은 복제(`--depth 1`, `rev-list --count` 1, `939f926` 객체 없음)에서 이 파일 **2 failed·31 passed** -- `test_moved_tool_matches_base_except_path_lines` + `test_base_blob_reader_reads_the_base_tree`(둘 다 241행 `AssertionError`). 전체 이력 `--no-local` 복제본 `6c724de`에서 **33 passed**. 전제 문장 맞음(→ minor m1).

## 4. 파일 수 18·4 / 12·4(hunk 145~146)
* `git ls-tree --name-only 6c724de workspaces/<폴더>/` `.py`: current-reuse-telescopic-ota-report **18**, two-stage-ota-report **4** = 22.
* 내 사슬 `diff --name-only` M9 정정 → F1 모의, 두 폴더 바로 아래 `.py`: **12·4** = 16(그 밖 workspaces 변경은 `workspaces/run_harness.py` 하나). card 일치.

## 5. 계획 N3.12.2 603·604행과 '+2' 예(hunk 23, 145, 188)
* 603·604행 = 두 좁힌 행, 602행 = `workspaces/run_harness.py` 행 -- `fd4ef8c`·`7243f28`·`2183f2e`·`6c724de` 모두 같음. `fd4ef8c~1`에서는 602 = run_harness, 603 = function-registry 행(삽입 전). card 정정 맞음.
* '+2' 예 실측(`fd4ef8c~1` 1191줄 → `fd4ef8c` 1193줄, `fd4ef8c~1..6c724de` 계획 변경 커밋은 `fd4ef8c` 하나):
  * Phase 표: 전 1000행 = Phase 3 행(`| 3 | 10모듈 이동(N3.10)…`) → 후 1002행 같은 행 ✓
  * 공통 착수 조건: 전 991 → 후 993 ✓
  * N3.12.3: 전 680(순서 3 auditor 행)·686(`* 판정 유형:`) → 후 682·688 같은 행 ✓
  * 534행(shim 문장)은 전후 그대로 ✓
  예 셋 모두 맞다(측정 표기만 없음 → minor m3).

## 6. 계약 판정 기준 변경 여부
* 계약 영역 hunk는 둘: 계약 9 전제 문구(전체 이력 저장소 범위를 'clone 또는 그 worktree'로 명시 + 근거 추가 -- 판정식 'head 실패 0·base 새 test 2개만 실패' 불변), 계약 12 '실행 조건(판정 기준 아님)' 두 줄 추가(V3·V5·V6·V7 키 목록 불변).
* 나머지 hunk는 '거부해야 할 입력' 설명·측정 기록·줄 번호 정정. **판정 기준 변경 없음** -- card 254행 자기 서술과 일치.

## minor
* **m1** (hunk 56): 얕은 복제에서 FAIL하는 test는 `test_moved_tool_matches_base_except_path_lines`만이 아니라 `test_base_blob_reader_reads_the_base_tree`도(2 failed). 전제의 결론은 그대로지만 괄호를 'FAIL 2(…·…)'로 하면 auditor가 원인 추적 때 헷갈리지 않는다.
* **m2** (hunk 68~69, 215~219): (i) `--base`는 `mutate_changed`에서 `--root` 저장소에만 쓰인다(618·665·667행) -- 복제본에서 풀려야 하는 것은 `--head`뿐. 'base·head 모두 40자 sha'는 보수적 실행 조건으로 무해하나 이유 문장은 head에만 해당. 'ref에서 닿아야 한다'도 엄밀히는 head만. (ii) '복제본 ref는 원 저장소 HEAD 브랜치 하나뿐'은 태그가 있으면 태그도 남는다(장난감 실측 `refs/tags/t1`). 실제 저장소 태그 0개라 지금 판에서는 참.
* **m3** (hunk 188): '+2' 예(1000→1002·991→993·680·686→682·688)는 맞지만 card에 실측 근거(rev·명령)가 없다 -- 이 review 5절 값으로 '`fd4ef8c~1`→`fd4ef8c` 실측'을 붙이면 된다.
