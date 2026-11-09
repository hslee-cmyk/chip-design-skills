---
id: 20261002-p3-shim-delete
phase: 3
evidence_type: red-green
gate_change: no
approval: 20260930-30-module-split-design
---
## 의도

design `30-module-split` **v8.5**(사용자 승인 UD-0 `20260930-30-module-split-design`, 답 2026-10-02) §2.1·§2.2·§3 GONE-SHIM·SD-NAMES·LAYER·REG-DEST·§8 F2 행·D-2·D-9·D-14·D-22 (4)·D-26·§10, card **F2**(Phase 3 마지막 card).
A = `skills/analog-gmid-design/assets`, SR = `A/sizing_recipe.py`, TL = `A/topology_library.py`, DR = `A/design_report.py`, SD = `A/stick_diagram.py`, ACF = `A/audit_current_forced.py`.

**문제**: F1까지 끝나면 SR·TL·DR은 재수출만 남은 shim이고 추적 파일 중 그것을 import하는 곳이 없다(F1 계약 5). SD는 M2·M3·M9가 SD 밖으로 보낸 이름을 임시로 재수출하고, 그중 MOD9 재수출은
SD(7) → MOD9 위쪽 import라 `import_layering`이 FAIL한다(design §2.2 D-22 (4) -- 모의 F2 base exit 1). 계획 534행 "추적 파일 호출부 갱신 후 shim 삭제"와 WP-14(한 이름에 import 경로 하나)대로 shim과 임시 재수출을 지운다.

**처리**: (1) SR·TL·DR 파일 삭제(D-2). (2) SD 최상위 재수출 줄에서 **SD 단위가 어느 유효 범위에서도 읽지 않는 이름**만 지운다 -- SD가 읽는 이름(레이아웃 단위가 쓰는 `Transistor`·`load_topology` 등)의 import는 SD의 의존이라 남는다(design §2.2 3차 검토 m3·v8 정정).
(3) ACF(`--keep` split)의 M card 재수출 줄에도 같은 규칙('결정 필요 항목' 1 기본안). (4) red-green test 하나(계약 6). 엔진 단위의 본문·위치는 바꾸지 않는다.

**원칙**: 범위 최소(import 줄 삭제와 파일 삭제뿐 -- 계약 1), 정의 하나(삭제 집합 = G1 `SourceIndex.global_names`로 계산, 손 목록 아님), 만들면 배선(새 test는 Phase 3 DoD E1·E3·E3b의 상시 판(판정 트리 범위)으로 V1에서 매번 돈다),
작성자≠검증자(판정 = §10 블록 그대로 + auditor 측정), topology 무관.

**자리(design §8.1)**: `… → M10 → T1 → F1 → F2`. base = F1 병합본(+ F1 '결정 필요 항목' 4의 역할 밖 커밋). 이 card 병합본이 **Phase 3 DoD 대상**이다(design §10 -- E0~E6).

## 관찰 가능한 계약

1. **범위(이 card `Change-Id` 커밋들의 diff, auditor)**: code 커밋 = SR·TL·DR 삭제 + SD·ACF의 최상위 `from <N3.10 줄기> import …`(level 0) 문에서 계약 2의 이름을 뺀 것(이름이 모두 빠진 문은 삭제). 그 밖의 바뀐 줄 0
   (엔진 다른 파일·`workspaces/**`·`tools/**`·레지스트리·계획·design·library 변경 0). SD에 남는 import 문의 위치는 그대로 둔다('결정 필요 항목' 2). test 커밋 = 새 파일 `A/tests/contracts/test_p3_shim_delete.py` 하나.
   AST 판정: SD·ACF의 base 모듈 `body`에서 그 import 문들의 `names`만 줄이고(빈 문은 뺌) 나머지 문장의 `ast.dump(include_attributes=False)`가 같다. `move_plan check --card ALL`(D0a 사본, design §10 `MPC`·`MP_ARGS`)을
   base → head에 돌리면 `move-set`·`changed`·`lost`·`move-rejected`·`rebind`·`order`·`shim`·`cache` 모두 빈 목록(옮긴 단위 0, 바뀐 단위 0 -- 재수출만 지웠다).
2. **삭제 집합(정의 하나 -- auditor가 F2 base에서 계산)**: SD -- F2 base SD 최상위 재수출 줄이 묶는 이름 중 `⋃ global_names(SD)`(G1)에 없는 이름. ACF -- F2 base ACF의 최상위 재수출 줄 중 **B0**(M1 판정 기록 `base_commit`)의 ACF에 없던 줄
   (M card가 더한 임시 재수출 -- ACF의 base import `from stick_diagram import load_topology`는 대상이 아니다)이 묶는 이름 중 `⋃ global_names(ACF)`에 없는 이름. 삭제 뒤 남는 재수출 이름 = 그 파일이 읽는 이름과 같다.
   모의 실측: SD 재수출 58 → 지움 50·남김 8, ACF 재수출 3 → 지움 2(`_as_set`·`_theta_evidence_for_pair`)·남김 1(`audit_topology` -- `render_report`가 읽는다).
3. **GONE-SHIM(design §10 E3 블록 그대로, auditor)**: 세 shim 파일 없음, `E3 INVALID`·`E3 FAIL(도구 오류 …)` 없음, `E3 PASS`(거부 확인은 B0에서 -- 문장·호출 둘 다 0 아님).
4. **SD-NAMES(design §10 E3b 블록 그대로)**: `E3b LIVE moved_out=<m> base_files_reading_moved_out=<f> pre_existing=<p>`에서 m > 0·f > 0, `E3b FAIL`·`ERROR`·`INVALID` 없음, `E3b PASS`. `pre_existing`은 기록만(지금 1 -- design §11-10 `stick.py`).
5. **LAYER(design §10 E0/E1 명령)**: `import_layering.py --root <iso>` exit 0·`findings` 0·`present` 9(MOD10 = M10 card가 더해 10 -- DoD E0). F2 base(SD → MOD9 임시 재수출)는 exit 1이어야 한다(거부 확인).
6. **red-green test `contracts/test_p3_shim_delete.py`(test-author, interface card만 보고)** -- 판정 범위 = D-9 밖 추적 `.py` 중 **판정 트리**(`skills/analog-gmid-design/**`)와 `workspaces/run_harness.py`
   ('결정 필요 항목' 3 -- 그 밖 `workspaces/**` 진단 스크립트는 DoD E3·E3b가 판정한다). test 둘, 각자 base에서 `AssertionError`인 단언을 품는다(base에서 참인 단언만으로 된 test 없음 -- D0b 검토 S1 선례):
   (a) `test_p3sd_shims_gone_and_no_importers`: 세 shim 파일이 A에 없다 **[red]** + 범위의 `.py`에 세 모듈의 import 문·import 호출(`import_module`·`_import`·`__import__`의 상수 첫 인자) 0(AST).
   (b) `test_p3sd_layering_clean_and_sd_names_resolve`: `tools/gates/import_layering.py --root <저장소>` exit 0 **[red]** + 범위의 `.py`가 `stick_diagram`에서 읽는 이름(`from stick_diagram import N`, `import stick_diagram [as a]`의 `a.N`)이
       SD 최상위 바인딩(정의·import, `symtable`)이나 모듈 기본 속성에 있다. (이름 문자열은 shim 파일 이름·모듈 이름 셋만 -- 회로·넷·엔진 함수 이름 없음.)
   red 모양: base(F1 병합본)에서 두 test 모두 `AssertionError`(허용 예외 -- 00-common §8.1), 다른 예외 0. green: head에서 둘 다 통과.
7. **IMPORT-ANY(design §10 `import_any` 그대로)**: `IMPORT-ANY tried=<n> expected=<n> failed=0`(shim 셋이 빠져 F1보다 3 적다).
8. **REG-DEST(design §10 E4와 같은 명령)**: `contracts/test_p3_registry_dest.py`(D0b) PASS, `move_plan plan` exit 0·`reg_mismatch`·`unassigned`·`upward`·`cycles`·`conflicts` 0·`absent_split` = `[sizing_recipe.py, topology_library.py, design_report.py]`·
   SD·ACF 밖 단위의 `rule` 전부 `A-0`, (단위 키 → `mod`) 사상이 F2 base와 같다(D0a 계약 8 (c)).
9. **동작 보존(auditor)**: PT3 전체·PT3 --gmid-dod 전체 head 실패 0(base는 새 test 2개만 실패 -- 그 밖 id 결과 같음). E-INST(`e_inst_p3.py`) 파일럿·`folded_cascode` 출력이 base와 `engine_origin` 밖 같음(shim은 F1 뒤 이미 로드되지 않는다 -- 같음 기대),
   E-LIB(`e_lib.py`) `hash` 같음.
10. **판정 기록 증거 스크립트(D-9 -- 고치지 않는다, 깨짐 기록)**: auditor는 §10 E3·E3b를 제외 집합을 비운 측정판으로도 돌려 깨지는 D-9 파일을 판정 기록에 적는다(판정 아님 -- design D-9 '기록 불변'): 모의 2 + 원자료 1 =
    `.ai/verification/20260930-df36-instance-relpath/scripts/e_lib_inst.py:35` `save_instance_json`, `.ai/verification/20260930-p9-kcl-edges/scripts/diff_dup.py:17·32` `_import_analog_grammar`·`_kcl_and_matching_edges`,
    `docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition.py`(SR import + SD 경유 4이름 `_RAIL_NETS`·`find_structural_symmetry_candidates`·`find_differential_pair_candidates`·`trace_vdd_to_gnd_branches`).
11. **references 문서(D-14 -- 보고만)**: auditor는 `git grep -c -E "sizing_recipe|topology_library|design_report" -- ':(glob)skills/analog-gmid-design/references/**/*.md' skills/analog-gmid-design/SKILL.md skills/analog-gmid-design/skill-validation-prompt.md`
    목록을 판정 기록에 적는다(갱신은 B22 card). 지금 12파일·74줄.
12. **게이트(판정 때 gate `master` 판 도구)**: V3 대상 def 0·변이 0, V6 `findings` [], V7 `new_defs` []·`unreached` [], V5 PASS(새 test 파일 추가뿐 -- 기존 test 변경 0), V4: 새 test가 엔진 심볼을 부르지 않아 interface card 표가 비면
    `ERROR` -- FU 선례 `--subject`(운영 진입 함수)로 준다.
13. **Phase 3 DoD 의존(이 card가 마지막 -- design §10)**: 아래 표의 '이 card가 만드는 것'이 이 card 판정에서 먼저 성립해야 DoD가 PASS할 수 있다.

    | DoD | 기준(design §10 표) | 이 card가 만드는 것 | 앞 card에 기대는 것 |
    |---|---|---|---|
    | E0 | `present` = N3.10 10행 | -- | M1~M9 파일, M10 `gmid_design_pipeline.py` |
    | E1 | `import_layering` exit 0 | SD의 MOD9 임시 재수출 삭제(계약 5) | M card ORDER, D0b `import_time_high` 0 |
    | E2 | card마다 V3 `defs` []·check 발견 0, `E2 INVALID` 없음 | `tools/**` 변경 0(D-27) | M1~M6·M8·M9 판정 기록 |
    | E3 | `E3 PASS` | shim 셋 삭제(계약 3) | F1 계약 5 (a)(importer 0) |
    | E3b | `E3b PASS` | SD 삭제 집합 계산(계약 2) | F1 계약 5 (b)(reader 0) |
    | E4 | test PASS·plan exit 0·`absent_split` 셋·A-0 | 계약 8 | D0b 레지스트리 열, D0a `plan` |
    | E5 | IMPORT-ANY·PT3 두 번·E-LIB/E-INST(P2D 대 HEAD) | 계약 7·9 | F1 계약 1 (c)(d) 앵커·기준 blob test 갱신(없으면 PT3 실패 9 -- 실측 4), T0(A군) |
    | E6 | `move_plan check --card ALL` exit 0 | 계약 1(바뀐 단위 0) | M10 `--allow-changed` 두 id |

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

**red-green**(design §8 F2 행). 관찰 가능한 상태가 바뀐다: shim 모듈 셋이 import되지 않고(`ImportError`), `import_layering`이 FAIL → PASS가 된다. 그 변화를 새 test(계약 6)가 base에서 `AssertionError`로 red, 병합본에서 green으로 판정한다.
equivalence가 아닌 이유: 'base와 병합본 모두 통과'가 성립할 수 없다(파일 부재·계층 판정은 base에서 거짓). 엔진 동작 보존은 계약 9로 따로 잰다.

## oracle 종류와 출처

(a) 구성: 계약 6의 기대(shim 파일 부재·import 0·`import_layering` exit 0·SD 이름 해석)는 design §3 GONE-SHIM·LAYER·SD-NAMES 정의에서 정한다(엔진 소스를 읽지 않는다 -- 셋의 이름은 design §2.1의 파일 이름).
(c) 동작 보존: PT3·E-INST·E-LIB = base 실행 결과(auditor). DoD 판정식(계약 3·4·5·7·8)은 design §10 블록을 그대로 쓴다.
`_drafts/p3kit_f12/test_p3_shim_delete.proto.py`·`mk_f2.py`는 작성 전 실측용 시제품이고 test·구현의 근거가 아니다(작성자≠검증자).

## 거부해야 할 입력

* SD가 읽는 이름의 재수출까지 지운 head(design v7의 과대 삭제 -- `load_topology`·`Transistor`·`kcl_series_union` 등) → SD 자신 import 시 `NameError`/IMPORT-ANY FAIL, 계약 1·2 FAIL.
* F1이 하나를 빠뜨린 base에서 F2(모의 F1 없는 F2 `0305d7e`) → 계약 3 E3 FAIL 65파일·계약 4 E3b FAIL 50줄·12파일·계약 6 두 test FAIL(실측 6).
* shim 하나를 남긴 head → 계약 6 (a)·계약 3 FAIL. SD의 MOD9 재수출을 남긴 head → 계약 5·6 (b) FAIL.
* 엔진 단위 본문을 같이 고친 head → 계약 1(`changed`) FAIL.

## library 회로 적용 여부

적용 -- E-INST 파일럿·`folded_cascode`, E-LIB 9회로(엔진 동작 불변 대조, 계약 9). 새 test는 회로를 읽지 않는다.

## 무동작 판정 입력(무발동 값)

새 산출물 필드 없음. library 회로 전부·기존 test 전부의 판정·산출물이 base와 같다(계약 9). 발동 계수 ID 없음.

## 재현할 수치

(모의 -- F1 card '작성 전 실측' 머리의 사슬 + F1 모의 `2fd53cc` → F2 모의 `3bcab98`(`mk_f2.py --acf`). 관찰이고 기대값 근거가 아니다 -- F2 base에서 auditor가 다시 잰다.)
* diff: 5파일, 3줄 더함·117줄 지움(SR 57·DR 30·TL 25 삭제, SD 재수출 줄 3 → 2, ACF 재수출 줄 2 → 1).
* E3 `PASS`, E3b `LIVE moved_out=58 base_files_reading_moved_out=31 pre_existing=1`·`PASS`, IMPORT-ANY `tried=10 expected=10 failed=0`, `import_layering` exit 0(F2 base exit 1).
* 측정판(제외 없음): D-9 안 깨짐 = `e_lib_inst.py` 1줄·`diff_dup.py` 2줄·`probe_stage_partition.py`(E3 1 + E3b 4줄).
* `plan`(D-31 모의): 배정 403, `absent_split` 셋, SD·ACF 밖 `A-0` 291, (키 → MOD) 사상 차이 0.
* E-INST 파일럿 `raw_sha256` `2fc426d9ef3a…`·`folded_cascode` `ef3cd9963d0a…` F2 base = head, E-LIB `hash` `1d2e3bf6acf7…` 같음.
* red-green 시제품: F2 base 2 failed(`AssertionError`), head 2 passed, F1 없는 F2 2 failed.

## 결정 필요 항목

1. **ACF의 임시 재수출(design F2 행에 없음)**: M card가 ACF(`--keep` split)에서 옮긴 단위의 재수출 줄을 더한다(모의 `from instance_report_builder import _theta_evidence_for_pair, audit_topology`, `from topology_authoring import _as_set`). ACF가 읽지 않는 2이름은
   F2 뒤에도 남으면 한 이름에 import 경로가 둘이 된다(WP-14 위반). 그 이름을 ACF에서 읽는 추적 파일은 0(`git grep "audit_current_forced"` -- import 0, 문자열 3: `test_ic5.py:48` 영역 키·`test_df23_inventory.py:56`·`count_selftest_sections.py:26`).
   기본안(원칙 WP-14·design §2.2와 같은 규칙): **지운다**(계약 2). E4·E6에는 영향 없음(E6 `--card ALL`은 이름 집합 대조를 하지 않는다 -- design §3 SHIM). 대안: 남긴다(백로그). 판정 기준을 바꾸지 않으므로 오케스트레이터가 정한다 --
   design §8 F2 행 문구에 'ACF 임시 재수출'을 더하는 사실 갱신을 design 정정 목록에 넣는다. 그 줄의 **위치**(머리 묶음 마지막 import 뒤 -- 자산 경로 밖 로드에서 `ModuleNotFoundError` 방지)는 `_drafts/p3_followup_questions.md` §3(W-2)이 M2·M9 몫으로 정한다 --
   F2는 그 줄에서 이름을 뺄 뿐이라 위치와 무관하다.
2. **SD에 남는 import 문의 위치**(design D-22 (4) "F2는 끝에 둔 import 줄을 머리로 올려도 된다"): 기본안 = 옮기지 않는다(범위 최소 -- 모의에서 남는 두 줄은 이미 머리 쪽(MOD2·MOD3, D-22 (1)의 '머리' 배치)이고 MOD8·9 재수출은 전부 지워진다).
3. **새 test의 판정 범위**: `workspaces/<하위>/**` 진단 스크립트를 범위에 넣으면 base에서 이미 풀리지 않던 이름(`workspaces/current-reuse-telescopic-ota-report/stick.py` `block_from_row_widths` -- design §11-10)이 영구 FAIL을 만든다(시제품 실측: 넣으면 head에서 FAIL 1).
   기본안 = 범위를 판정 트리 + `workspaces/run_harness.py`로 둔다 -- 그 밖은 DoD E3·E3b(`pre_existing` 장치 있음)가 맡는다. 판정을 줄이는 것이 아니라 상시 test가 새로 더하는 판정의 범위다(DoD 판정 불변).
4. **F1 의존(cross-card)**: F2 base에 F1 계약 1 (c)(d)(엔진 파일 이름 앵커 7줄·기준 blob 대조 test)의 갱신이 없으면 F2 병합본 V1이 깨진다 -- 모의(F1이 앵커를 고치지 않은 판)에서 F2 뒤 PT3 실패 +9
   (`test_d_delete_dead` 2·`test_d_delete_telescopic` 2·`test_d_move_tests::test_moved_names_gone_from_engine`·`test_df35_harness_paths::test_expected_paths_exist`·`test_dup_w_calc::test_no_inline_w_formula_outside_new_function`·
   `test_ts6_probe_relocate::test_assets_dir_holds_engine_entry_points` + T0 몫 `test_ts6_dead_probes::test_sizing_recipe_source_has_no_l_role_multipliers`). F1 card 계약 1 (c)(d)·결정 필요 항목 1이 맡는다(이 card에서 test를 고치지 않는다).
5. **design 정정 목록(사용자 질문 아님 -- 사실 갱신)**: (i) §7.1 B군 표에 `test_ts6_probe_relocate.py:668-673`(F1 card 결정 1) (ii) §8 F2 행 'ACF 임시 재수출'(위 1) (iii) §10 E3b 실측 문장의 '49줄·12파일'(근사 배정) → D-31 모의 50줄·12파일(파일 집합 같음).

## 작성 전 실측

(F1 card '작성 전 실측' 머리와 같은 판·같은 복제본 `C:/g202/r` -- gate `master` `dd60db6`, 2026-10-02, 작업 끝에 `C:/g202` 삭제, 실제 저장소 쓰기 없음. F2 base = F1 모의 `2fd53cc`, head = `3bcab98`.)
1. **사실 문장 재측정**: F2 base SD 재수출 줄 3문(MOD3 머리 1·MOD2 머리 1·MOD9 끝 1), 이름 58. `mk_f2.py`(G1 `global_names(SD)` 합) → 지움 50·남김 8(`Transistor`·`_scan_case_collisions`·`find_hub_merge_candidates`·`find_matching_candidates`·`find_stack_edges`·
   `find_stacked_matching_candidates`·`kcl_series_union`·`load_topology` -- 모두 MOD2·MOD3 출처라 위쪽 import 아님). ACF 재수출 줄 2문·3이름 → 지움 2·남김 1. `import_layering --root`: `3f61526`(M9 모의) exit 1(SD → `instance_report_builder`), F1 모의 exit 1, F2 모의 exit 0.
2. **이름 충돌**: 새 파일 `contracts/test_p3_shim_delete.py`·test 이름 접두 `test_p3sd_` -- 저장소 참조 0(`git grep "p3_shim_delete\|p3sd_"` 0건, `dd60db6`). contracts의 전수 스캔(`rglob`) 8파일(`test_phase2_stale_refs.py`·`test_d_delete_dead.py`·`test_d_move_tests.py`·
   `test_ts6_probe_relocate.py`·`test_probe_dup_scan.py`·`test_d_delete_telescopic.py`·`test_ts6_dead_probes.py`·`test_ts3_no_print_verdicts.py`)이 찾는 토큰(지운 Phase 2 이름·`print` 판정 등)을 새 test가 쓰지 않는다 -- 새 test의 문자열은 shim 파일·모듈 이름 셋과
   `stick_diagram`뿐(T0 계약 9 토큰 목록과 대조는 test-author 몫).
3. **원칙의 계약화**: 범위 최소 → 계약 1, 정의 하나 → 계약 2(계산식), 만들면 배선 → 계약 6(상시 test가 V1에서 매번 E1·E3·E3b 판정의 판정 트리 몫을 돈다), 동작 불변 → 계약 9, 작성자≠검증자 → 'oracle'.
4. **쓰기 경로**: SR·TL·DR 삭제·SD·ACF 수정 = gmid-code-author(`A/*.py`), 새 test = gmid-test-author(`A/tests/**`), 판정 기록 = auditor. 역할 밖 경로 없음.
5. **계획서 소비자**: 지우는 파일 이름을 계획·design이 언급한다(계획 534행 shim 문장, design 30 전체) -- 모두 'F2에서 지운다'는 문맥이라 고칠 것 없음. 레지스트리 절 제목 `### sizing_recipe.py (…)`은 D0b 범위(목적지 열만 -- 제목 불변) --
   `reg_check.py`가 절 제목을 파일 존재와 대조하는지 착수 때 확인(F2 base에서 `A/tests/tools/reg_check.py --registry … --root .` exit 0을 판정 기록에 적는다).
6. **미배선**: 새 def 없음(test 파일만). V7 `new_defs` [].
7. **기존 계약 test(PT3 모의, `run_pt3.sh`)**: F1 모의 `2fd53cc` 5 failed(F1·T0 몫 -- F1 card 실측 4) → F2 모의 `3bcab98` 14 failed(+9 = 결정 필요 항목 4 목록). F1이 앵커를 고치면 +9는 0이 되어야 한다 -- F2 판정의 전제.
8. **V3 규모**(`run_vtools.sh`, base 판 = G1 시제품 설치본, F1 모의 → F2 모의): V3 PASS `targets` [ACF, SD]·`mutants` 0·`defs` [](재수출 import 문만 -- def 아님), V6 PASS `findings` [], V7 PASS `new_defs` []·`unreached` [], V5 PASS(test 변경 없음 -- 모의에는 새 test를 넣지 않았다).
   SR·TL·DR 삭제는 def가 없는 파일 삭제라 V3·V6·V7 대상이 아니다(`targets`에 없음).
9. **승인 줄**: 동작 변경 없음(파일·import 경로 정리) -- design 승인 UD-0이 덮는다(D-2·D-9·D-14). 기록 `20260930-30-module-split-design`은 작업 중 gate `master`에 들어왔고(`36e170e`, 지금 `4a286f0`) 범위 설명이 "F2 `p3-shim-delete`"를 slug로 적는다
   (id 날짜는 card 작성 때 -- 이 초안 `20261002-p3-shim-delete`). `dd60db6..4a286f0` 엔진·`workspaces` 변경 0.
10. **범위 계약**: 계약 1은 '이 card `Change-Id` 커밋들의 diff'로 한정.
11. **test 이름·모양**: `test_p3sd_` 접두, 엔진 심볼을 부르지 않는다(`import_layering`은 하위 프로세스) -- V3 인벤토리 간선과 무관. 피검 대상이 파일 트리·게이트 도구라 V4 subject는 '결정 필요 항목' 없이 FU 선례.
12. **같음 판정**: 계약 6은 목록 `== []`·exit 코드 정수, 계약 2는 이름 집합을 정렬 목록으로 비교, 계약 9는 JSON 키별 값.
13. **red 모양**: 시제품(`test_p3_shim_delete.proto.py`, 판정 트리 범위) -- F2 base `2fd53cc` 2 failed 모두 `AssertionError`(shim 파일 셋 있음 / `import_layering` exit 1), head `3bcab98` 2 passed, F1 없는 F2 `0305d7e` 2 failed(importer 남음 / SD 이름 미해석).
    범위를 `workspaces/**` 전체로 넓힌 시제품은 head에서도 FAIL 1(`stick.py` `block_from_row_widths` -- 결정 필요 항목 3).
