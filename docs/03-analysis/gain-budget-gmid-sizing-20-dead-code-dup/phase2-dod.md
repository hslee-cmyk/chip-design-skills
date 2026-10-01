# Phase 2 완료 조건(DoD) 측정 결과 (auditor 원본 -- 오케스트레이터가 phase2-dod.md로 옮김)

대상: 측정 커밋 H = DoD 착수 때의 gate `master` = `5f643a905fbc14c1374063b47fea6428ba088563`(제목 'audit: 20261001-topology-md-sync 판정 기록(test-only, V1~V10 -- V1 1047 passed 15 xfailed, 계약 8 (b) measured_at 58024de 5쌍 FAIL, V8·V9 N/A)'). P10b 판정 기록 커밋 P = `afcf36c1e7ac0d1365870f996c62de238f202984`, P..H 커밋 9개(브리핑 §2 기대와 같음, 끼어든 커밋 없음): `58024de` `7365b88` `378ebe6` `80b9970` `1a464e4` `dc196cd` `19eb475`(runbook 7) + `2de923b`(test: md 일치, Role: test, Change-Id 20261001-topology-md-sync) + `5f643a9`(audit: md 일치 판정 기록). E2 정정 커밋 E = `1a464e42fa5598d50150c6257f73d088a519357b`, 승인 기록 커밋 = `dc196cd30bfe0c68d61c20891246f4186a91a6b3`(target `ddacfe22022dd0b5d5f8bf2cc8c1e80b45c22844fa1624e8968a4fbd676aed64` = 재계산 `ddacfe22022dd0b5d5f8bf2cc8c1e80b45c22844fa1624e8968a4fbd676aed64`). 측정 주체 = gmid-verification-auditor(독립 측정, 2026-10-01).
기준: design 20 §10(2140da8·fe638ab 정정본 + E2 정정 `1a464e4`), 계획 N6.2 Phase 2 행·N6.3, 승인 20260930-phase2-e4-baseline·20260930-phase2-e4-phase·20261001-p2dod-e2-wording(면제 근거 20260929-p4-scan-exempt).
환경: 격리 복제본(--no-hardlinks --no-local, origin 제거, core.longpaths=true) C:/g90/iso, cwd C:/g90, Python 3.14.2/pytest 9.0.2, 게이트 캐시 = `git archive <rev> tools/gates` → `C:/g90/cache_<전체 해시>/tools/gates`. 가드 (1)~(5) 전부 통과(`C:/g90/scripts/guard.sh`, 원출력 `C:/g90/out/guard.txt`). 메인 저장소 쓰기 0(`git status --porcelain --ignored` 전/E4(a) 뒤/E4(c) 뒤/E4(d) 뒤 동일, stamp 이후 파일 0 -- 지정 경로(workspaces·skills·tools·.ai/verification)·루트 모두; 원출력 `C:/g90/out/watch_after_e4a.txt`·`watch_after_e4c.txt`·`watch_after_e4d.txt`).

## 판정
판정: PASS

E0~E5 6항목 PASS, 판별력 대조 3건 기대대로, N6.3 1~5 PASS.


| ID | 조건(N6.2) | 판정 | 측정 결과 |
|---|---|---|---|
| E0 | 승인된 D 목록 처리 | PASS | `reg_check.py --registry … --root <iso>` exit 0, 출력 `reg_check: 발견 0`(`C:/g90/out/e0_H.txt`). auditor 따로 셈(`e0_counts_H.txt`): §7 행 수 25 = §1 D 합 25, `처리` 열 값 전부 `보류(Phase n)` 형식 -- `보류(Phase 3)` 9 · `보류(Phase 4)` 14 · `보류(Phase 6a)` 2 |
| E1 | DUP 차등 test PASS 후 중복 정의 삭제 | PASS | 수집(`e1_collect_H.txt`): `contracts/test_dup_w_calc.py::` 106, `contracts/test_dup_kcl_edges.py::` 24, 두 모듈 밖 0, `130/1062 tests collected (932 deselected)`. 실행(`e1_run_H.txt`): `130 passed, 932 deselected`, FAILED/ERROR 0, exit 0. 판정 기록 V2: `20260930-dup-w-calc` verdict PASS, evidence_type(기록 그대로) `red-green`, basis 요지 "W 식 18곳 = width_from_id_density 호출 18개 AST 대조 18/18, E-LIB 1d2e3bf6… 출력 base와 바이트 동일, E-INST folded·current_reuse base와 같음, red 25건 AssertionError"; `20260930-p9-kcl-edges` verdict PASS, evidence_type `equivalence`, basis 요지 "DIFF-DUP 9회로 x 2입력 36/36 같음·출력 JSON base와 바이트 동일, E-LIB 9회로 base = 병합본, E-INST 파일럿·folded instance.json 바이트 동일, 계약 1 정본 호출 1·_RAIL_NETS 0·.source/.drain 0" |
| E2 | probe 엔진 식 재구현 0 | PASS | H 판 통과 기준 문구(`d20_H.md` 220행 그대로): "exit 0, 면제되지 않은 발견 0(면제 = `target_kind: decision` 승인 기록이 적은 `<path>::<rule>`로 스캐너가 `"exempt": true`를 붙인 발견 -- 현재 승인 `20260929-p4-scan-exempt` 1건; 면제 발견은 DoD 기록에 path·line·rule·승인 id로 적는다)". 측정(`e2_H.txt`, exit `e2_exit.txt`): (a) exit 0, 출력 1줄(발견 1), (b) `"exempt": false`(또는 키 없음) 0줄, (c) `"exempt": true` 1줄 -- 근거 승인 있음(아래 표, `e2_approvals.txt`: H 트리 decision 승인 15개 중 이 path::rule을 `target`에 가진 것 정확히 1개). 면제 줄 수 1 = 문구 '현재 … 1건' |
| E3 | DF-23 전수 목록 | PASS | auditor 스크립트 `C:/g90/scripts/e3_check.py`(결과 `e3_H.json`): 1 cat-file 성립. 2 items 515 = totals.n_items 515, by_phase(해당 없음 317·4 63·3 61·7b 46·7a 27·6b 1)·by_role(메시지뿐 302·동작을 정함 213) 재계산과 같음. 3 phase 515/515, 전부 닫힌 집합 {3,4,5,6a,6b,6c,7a,7b,7c,해당 없음}(계획 N6.1 순서표에서 auditor가 만든 집합 = 목록 `phase_source.closed_set`). 4 빈 function 0. 5 '동작을 정함' `^DF-(\d+)` 번호별: DF-29 0 · DF-30 27 · DF-31 16 · DF-32 1 · DF-33 12 · DF-34 18(30~34 모두 ≥1); plan_mapping 값별: DF-30 4·DF-30(신규 위치) 7·DF-30(회로별 metric 함수) 16·DF-31 6·DF-31(회로별 보상 함수) 10·DF-32 1·DF-33 12·DF-34 18(그 밖 DF-19 62·DF-23 1). DF-29 0의 근거: P5b `20260923-d-delete-telescopic` 판정 기록(equivalence, V1~V7·V10 PASS -- 계약 1 '9개 정의가 병합본에 없다')과 DF-29 위치 def 검사 H 0건(`e3_df29_defs.txt`; 대조 da03c0e 5건). 6 `measured_at` 766b5c2 ↔ H, scope_files 8개 `git diff --quiet` exit 0, scope_files = H 최상위 `assets/*.py` 7 + `workspaces/run_harness.py` 집합 일치 |
| E4 | 동작 보존 | PASS | (a) `PT2 -q`(`e4_pt2.txt`): **1047 passed, 15 xfailed**, XPASS 0, 실패·오류 0, exit 0, pytest 280.82 s. `PT2 --gmid-dod -q`(`e4_pt2_dod.txt`): **1047 passed, 15 xfailed**, XPASS 0, 실패·오류 0, exit 0, pytest 245.20 s. N(md 일치) = `PT2 --collect-only`에서 `contracts/test_topology_md_sync.py::` 39, 마지막 줄 `1062 tests collected`(= 1023 + 39; md 일치 판정 기록 reproduced_numbers '수집 id 수 base 1023 / T 1062'·V2 basis '새 test 39개'와 같음). (c)(d) 같은 복제본 C:/g90/iso에서 da03c0e 판 → H 판: E-LIB 두 판 9/9 로드(회로마다 load·V1_own_stack·V2_kind_stack true, exc {}), `hash` 두 판 같음. E-INST 두 회로 (a) `without_topology_ref_sha256` 두 판 같음 (b) H 판 `topology_ref_equals_expected_contract1` true, `path_string_hits` [] (c) da03c0e 판 `topology_ref_is_join_of_ASSETS_DIR` true -- 해시 표 아래 |
| E5 | 미래 topology 커버 | PASS | `PT <iso>/…/tests/unit -k new_topology -rA`(`e5_H.txt`): `9 passed, 1053 deselected`, exit 0. 수집 9건, 전부 contracts(test_d_delete_dead 1, test_d_delete_telescopic 8) -- 노드 목록과 기준 문구 덮음 표는 아래 |

E4 해시 표(같은 실행 안 두 판 실측, `C:/g90/out/elib_*.json`·`einst_*.json`):

| 값 | da03c0e 판 | H 판 | 같음 |
|---|---|---|---|
| E-LIB `hash`(9/9, 모두 ok·exc 없음) | `1d2e3bf6acf762ebea14aa526405bfe63db9632cfab68672b93948c2be3b7a8f` | `1d2e3bf6acf762ebea14aa526405bfe63db9632cfab68672b93948c2be3b7a8f` | O |
| E-INST crt `without_topology_ref_sha256` | `185b675e9dd363a535d2942c651cddee4cb1a0ee98b703f0c7abef99f50e51ca` | `185b675e9dd363a535d2942c651cddee4cb1a0ee98b703f0c7abef99f50e51ca` | O |
| E-INST fc `without_topology_ref_sha256` | `0ca6746f1cb3d364f26f5ec6b37e931c7fbc3488b610b4e57f377a6067cda754` | `0ca6746f1cb3d364f26f5ec6b37e931c7fbc3488b610b4e57f377a6067cda754` | O |
| crt / fc `n_sizing` | 51 / 13 | 51 / 13 | O |
| crt `topology_ref` | `C:\g90\iso\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json`(join of ASSETS_DIR true) | `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json`(contract1 true, path_string_hits []) | 의도된 차이(DF-36) |
| fc `topology_ref` | `C:\g90\iso\skills\analog-gmid-design\assets\library\folded_cascode.topology.json`(join of ASSETS_DIR true) | `skills/analog-gmid-design/assets/library/folded_cascode.topology.json`(contract1 true, path_string_hits []) | 의도된 차이(DF-36) |

da03c0e base 모드 두 회로: `literal_counts_before` [2, 1], `engine_origin`(sizing_recipe·stick_diagram·design_report)·`sys_path_added`(analog-grammar/assets·analog-gmid-design/assets)·`instance_path`·`harness_file` 전부 `C:\g90\iso` 아래, `fail_in_stdout` false, exit 0. H 판 두 회로 `fail_in_stdout` false, `engine_origin`·`instance_path` 전부 `C:\g90\iso` 아래, exit 0. 브리핑 §5 기대 값과 전부 같다.

E2 면제 줄 표:

| path | line | rule | 승인 id |
|---|---|---|---|
| skills/analog-gmid-design/assets/tests/probes/probe_mirror_gain_ranking.py | 183 | lut-private | 20260929-p4-scan-exempt(`target_kind: decision`, `target: …/probe_mirror_gain_ranking.py::lut-private`) |

E5 수집 노드(전부 PASSED)와 기준 문구 덮음 표:

| 노드(`skills/analog-gmid-design/assets/tests/contracts/` 아래) | (i) 로드·파이프라인 동일 | (ii) 삭제 선언 키 ValueError | (iii) 일반 경로 값 산출 |
|---|---|---|---|
| test_d_delete_dead.py::test_unregistered_metric_type_is_rejected[new_topology_future_metric] | | O | |
| test_d_delete_telescopic.py::test_deleted_family_is_rejected_on_new_topology[cmrr_estimate-telescopic_class_ab] | | O | |
| test_d_delete_telescopic.py::test_deleted_family_is_rejected_on_new_topology[cmrr_estimate-telescopic_class_ab_cmfb] | | O | |
| test_d_delete_telescopic.py::test_deleted_family_is_rejected_on_new_topology[cmrr_estimate-new_topology_future_family] | | O | |
| test_d_delete_telescopic.py::test_deleted_family_is_rejected_on_new_topology[psrr_estimate-telescopic_class_ab] | | O | |
| test_d_delete_telescopic.py::test_deleted_family_is_rejected_on_new_topology[psrr_estimate-telescopic_class_ab_cmfb] | | O | |
| test_d_delete_telescopic.py::test_deleted_family_is_rejected_on_new_topology[psrr_estimate-new_topology_future_family] | | O | |
| test_d_delete_telescopic.py::test_general_path_yields_value_on_new_topology[cmrr_like] | | | O |
| test_d_delete_telescopic.py::test_general_path_yields_value_on_new_topology[psrr_like] | | | O |
| 합계 | 0 | 7 | 2 |

E0 옆 기록(판정 기준 아님): DF-23 레지스트리 기록 -- 같은 명령 + `--df23-inventory <iso>/docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json` → exit 0, `reg_check: 발견 0`(`e0_df23_H.txt`).

## 판별력 대조

| 대상 | 판 | 결과 | 기대 | 판별 |
|---|---|---|---|---|
| E1 | `7535799302a9ff7cfbfcadb2281d16bf136fadcf`(P9 base) | `--collect-only -k "dup_w_calc or dup_kcl_edges"`: `test_dup_w_calc.py::` 106, `test_dup_kcl_edges.py::` **0**, `106/813 tests collected (707 deselected)`(`C:/g90/out/e1_collect_7535799.txt`) | kcl_edges 0, w_calc ≥1 | O -- H의 dup_kcl_edges 수집 24는 P9로 생겼다 |
| E3 | `766b5c2b486df66e143feb1f9440084a62db0ebc`(P10 문서 커밋 직전, 판 바꾸지 않고 `e3_check.py`로) | verdict **FAIL**(`e3_766b5c2.json`): 1 cat-file 성립, 2 items 590 = n_items지만 totals.by_phase 없음, 3 phase 가진 항목 0/590·`measured_at` 없음, 4 빈 function 414, 5 '동작을 정함' DF-29 42(DF-30 28·31 17·32 1·33 12·34 18), 6 해당 없음 | FAIL | O -- design 문구의 cat-file만으로는 판별하지 못한다(1번은 766b5c2에서도 성립) |
| E3 DF-29 위치 def | H / `da03c0e` | H 0건, da03c0e 5건(`sizing_recipe.py` 5061 `_load_telescopic_topology_cached`·5080 `_telescopic_class_ab_open_loop_response`·5186 `_cmrr_telescopic_class_ab_cmfb`·5272 `_psrr_telescopic_class_ab`·5328 `_psrr_telescopic_class_ab_cmfb`; `e3_df29_defs.txt`) | H 0, da03c0e 5 | O -- 검사가 실제로 찾는다 |

## N6.3 공통 조건 (H 트리, auditor 스크립트 `C:/g90/scripts/n63.py`, 결과 `C:/g90/out/n63.json`)

1. **판정 기록 전수** -- PASS. H 트리 `.ai/verification/*.json`(`_schema.json` 제외) 34건(작업 트리 glob 34 = `git ls-tree H` 34), 34건 모두 `checks.V1`~`V10`이 `PASS` 또는 `N/A`(어긋난 기록 0).
2. **Phase 2 판정 기록 17건** -- PASS. `git grep -l -E '^phase: 2$' H -- docs/02-design/specs` = 18장, 그중 판정 기록 있음 17, 없음 1 = `20260923-probe-promote-consistency`(P3(c), 사용자 결정 2026-09-29 '보류, P5로 진행', 백로그 B21 Phase 4) -- 브리핑이 허용한 유일한 것.

표(V 열 = V1~V10 순서, P = PASS):

| card | id | evidence_type(기록) | V1~V10 | audit 커밋(기록 마지막 변경, Role: audit·Change-Id 일치, H 조상) | merge 커밋(H 조상) | base·test·code H 조상 |
|---|---|---|---|---|---|---|
| P1 | `20260923-probe-dead-delete` | test-only | P P P P P P P N/A N/A P | `1cdebc9` (trailer 일치, 조상) | 없음(test-only, `A^` = `4b841d1`, 부모 1) | base O · test O · code null |
| P2 | `20260923-probe-relocate` | equivalence | P P P P P P P N/A N/A P | `af3416a` (trailer 일치, 조상) | `05afe00` (조상) | base O · test O · code O |
| P3(a) | `20260923-probe-promote-clean` | test-only | P P P P P P P N/A N/A P | `db25f7b` (trailer 일치, 조상) | 없음(test-only, `A^` = `80efc66`, 부모 1) | base O · test O · code null |
| P3(b) | `20260923-probe-promote-differential` | test-only | P P P P P P P N/A N/A P | `5e1ca79` (trailer 일치, 조상) | 없음(test-only, `A^` = `64a4791`, 부모 1) | base O · test O · code null |
| P4 | `20260929-probe-engine-dup` | red-green | P P P P P P P N/A N/A P | `a53b8ac` (trailer 일치, 조상) | `427b0c3` (조상) | base O · test O · code O |
| P5 | `20260923-d-delete-dead` | equivalence | P P P P P P P N/A N/A P | `1258efe` (trailer 일치, 조상) | `2a2a7a0` (조상) | base O · test O · code O |
| P5b | `20260923-d-delete-telescopic` | equivalence | P P P P P P P N/A N/A P | `d7bce7a` (trailer 일치, 조상) | `d473f65` (조상) | base O · test O · code O |
| P6 | `20260930-d-move-tests` | red-green | P P P P P P P N/A N/A P | `4e0f325` (trailer 일치, 조상) | `1adbb76` (조상) | base O · test O · code O |
| P7 | `20260930-registry-grade-fix` | red-green | P P P P P P P N/A N/A P | `df77a5f` (trailer 일치, 조상) | `dd3fae4` (조상) | base O · test O · code O |
| P8 | `20260930-dup-w-calc` | red-green | P P P P P P P N/A N/A P | `54dec6a` (trailer 일치, 조상) | `243e6ed` (조상) | base O · test O · code O |
| P9 | `20260930-p9-kcl-edges` | equivalence | P P P P P P P N/A N/A P | `766b5c2` (trailer 일치, 조상) | `93b18db` (조상) | base O · test O · code O |
| P10 | `20260930-p10-df23-inventory` | test-only | P P P P P P P N/A N/A P | `62ae24f` (trailer 일치, 조상) | 없음(test-only, `A^` = `56b86c6`, 부모 1) | base O · test O · code null |
| P10b | `20260930-df23-registry-record` | red-green | P P P P P P P N/A N/A P | `afcf36c` (trailer 일치, 조상) | `54ef51c` (조상) | base O · test O · code O |
| §8 밖 restore | `20260930-restore-plan-functions` | red-green | P P P P P P P N/A N/A P | `4967a82` (trailer 일치, 조상) | `f1c4b7d` (조상) | base O · test O · code O |
| §8 밖 DF-35 | `20260930-df35-harness-paths` | red-green | P P P P P P P N/A N/A P | `34bc75e` (trailer 일치, 조상) | `d23f4bb` (조상) | base O · test O · code O |
| §8 밖 DF-36 | `20260930-df36-instance-relpath` | red-green | P P P P P P P N/A N/A P | `148bd6d` (trailer 일치, 조상) | `b29be01` (조상) | base O · test O · code O |
| B47 md 일치 | `20261001-topology-md-sync` | test-only | P P P P P P P N/A N/A P | `5f643a9` (trailer 일치, 조상) | 없음(test-only, `A^` = `2de923b`, 부모 1) | base O · test O · code null |

evidence_type 집계(기록 그대로): red-green 8(P4·P6·P7·P8·restore·DF-35·DF-36·P10b), equivalence 4(P2·P5·P5b·P9), test-only 5(P1·P3a·P3b·P10·md 일치).
Phase 2 기간에 병합된 0.5 card(Phase 2 목록 밖, 1번 전수에는 포함): `20260930-v3-history-clone`(B28) V1 PASS·V10 PASS·나머지 N/A, `20260929-rejudge-cache` V1 PASS·V10 PASS·나머지 N/A. (H 트리의 phase 0.5 기록은 이 둘 외에 `20260921-gate-flow-liveness`·`20260921-gate-output-utf8`도 있고 같은 모양 -- Phase 2 기간 전.)

3. **merge gate(EL4) 형식** -- PASS. 17건 모두 판정 기록을 마지막으로 바꾼 커밋이 `Role: audit`·`Change-Id: <id>` trailer를 정확히 갖고 H의 조상. test-only 아닌 12건 모두 제목 `merge <id>` 병합 커밋이 정확히 1개이고 H의 조상. test-only 5건은 병합 없음, `code_commit` null, audit 커밋의 단일 부모 = 기록의 `test_commit`(5/5). 17건 모두 `base_commit`·`test_commit`(·`code_commit` 있으면) H의 조상. md 일치 행: audit 커밋 A `5f643a9`, `A^` = T `2de923b`, 병합 없음, `code_commit` null -- 브리핑 기대 모양과 같음.
4. **카드 밖 엔진 변경 0** -- PASS. `git log --no-merges da03c0e..H -- 'skills/analog-gmid-design/assets/*.py' workspaces/run_harness.py 'skills/analog-gmid-design/assets/library/*.json'` = **31개**, 31개 전부 `Role: code`/`Role: test` 하나와 위 17건 안의 `Change-Id` 하나(어긋난 커밋 0). card별: P2 `probe-relocate` 4(code 1·test 3), P1·P3a·P3b·P10 각 test 1, P10b code 1·test 1, P4·P5·P5b·P6·P7·P8·P9·restore·DF-35·DF-36 각 code 1·test 1, md 일치 test 1. md 일치 문서 커밋 D(`7365b88`)·E2 정정 커밋(`1a464e4`)·문서 커밋 1(`58024de`)은 목록에 나오지 않음.
5. **동작 변경 card의 증거 확인** -- PASS(판정 기록 구조로 잴 수 있는 범위).
   - red-green 8건 `red.test_ids`/`red.failure_hashes` 개수, 8건 모두 `checks.V2` PASS: P4 1/1, P6 5/5, P7 1/1, P8 25/25, restore 34/34, DF-35 6/6, DF-36 21/21, P10b 1/1.
   - md 일치 card(test-only) 기록에 `red` 필드 없음.
   - test-only 5건(P1·P3a·P3b·P10·md 일치): 4번 목록에서 이 card들의 커밋은 `Role: test` 각 1개뿐(code 커밋 0).
   - equivalence 4건 -- `checks.V2.verdict` PASS 4/4, base = 병합본을 말하는 `checks.V2.basis` 문장 인용(`reproduced_numbers`는 P2·P5·P5b 빈 목록, P9는 그룹 수 목록):
     - P2 `20260923-probe-relocate`: "E-LIB -- 같은 경로 복제본에서 base와 병합본을 차례로 checkout해 library 9회로 load_topology 9/9 성공, 정규화 직렬화 sha256 a3cfe21f292ad4ec16625527565bd731659e9623907aace524a9aa08824e9ce8 양쪽 동일. E-INST -- … current_reuse_telescopic_ota exit 0·소자 51·sha256 ea24aba384119a19c1ac785b2e6bce94512132c997af966952b7b3cc81b3afd5 양쪽 동일, folded_cascode exit 0·소자 13·sha256 2cd6a31a0f6891e9da22a794c8d24f87afd1e89fc56d616b1640b01fa39d9e16 양쪽 동일."
     - P5 `20260923-d-delete-dead`: "E-LIB 9/9 로드, 파이프라인 V1 9/9·V2 9/9 성공, 해시 8cb62d21aa119cbd06c79f5ef6eb09c77a45bf0f093cf6c9ca1b82c36300e53e base = T = 병합본(출력 JSON 파일 바이트 동일, PYTHONHASHSEED 1·777 안정); E-INST 파일럿 exit 0·소자 51·785dadb1…, folded_cascode exit 0·소자 13·83956c0a…, base(2회) = T = 병합본"
     - P5b `20260923-d-delete-telescopic`: "E-LIB 9/9 로드, 파이프라인 V1 9/9·V2 9/9, E_LIB_HASH fc5aaca590fa26c40df5c9676c0a6cf22576888fae169126a99b50eee306dceb base = 병합본(출력 JSON 바이트 동일 …); … E-INST 파일럿 exit 0·sizing 51·a36b6e16…, folded_cascode exit 0·sizing 13·24cbd7f5…, base(1차 2회 + 이번 1회) = 병합본"
     - P9 `20260930-p9-kcl-edges`: "DIFF-DUP 9회로 x 2입력 = 18 kcl_series_union 비교 + 18 정본 엣지 목록 비교 36/36 같음, 합성 2입력 같음, 출력 JSON이 base와 바이트 동일; … E-LIB 9회로 base = 병합본(출력 JSON 바이트 동일, 순서 3 값과도 같음). E-INST 파일럿·folded_cascode가 같은 경로·같은 시각대 base 2회·병합본 2회 모두 instance.json 바이트 동일"
   - 삭제 키 `ValueError`는 E5 노드 (ii) 배정분 7건(전부 PASSED)으로 확인.

DF-23 레지스트리 기록(계획 DF-23 행 '2(전수 목록·레지스트리 기록)'의 증거, 판정 기준 아님): `reg_check.py … --df23-inventory <iso>/docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json` exit 0, `reg_check: 발견 0`.

## 남긴 관찰(PASS, 차단 아님)

1. **결정 D2 (a) -- P3c 보류(B21 rail-set 재구현 1건)**: P3c 보류(B21, Phase 4) -- `tests/probe_physical_consistency.py`는 tests 루트에 남아 E2 스캐너 범위 밖이며, 스캐너 기준 rail-set 재구현 1건(40행)과 메인 절대 경로 리터럴 2개(33·38행)를 가진다. E2는 design 문구(`tests/probes/**`)대로 판정했다(결정 D2 (a)).
   측정: H 판 파일만 `C:/g90/d2/skills/analog-gmid-design/assets/tests/probes/`에 복사하고 H 판 `engine_dup_scan.py --root C:/g90/d2` → exit 1, 발견 1건 `{"path": "skills/analog-gmid-design/assets/tests/probes/probe_physical_consistency.py", "line": 40, "rule": "rail-set", "concept": "레일 집합 재선언 -> sizing_recipe._DEFAULT_RAIL_HI/_DEFAULT_RAIL_LO", "exempt": false}`(`C:/g90/out/obs1_d2_scan.txt`). 40행 `RAIL_HI, RAIL_LO = {"vdd", "VDD"}, {"gnd", "GND", "vss", "VSS"}`, 33행 `ASSETS = r"C:\Users\HSLEE\…\skills\analog-gmid-design\assets"`, 38행 `INST = r"C:\Users\HSLEE\…\current_reuse_telescopic_ota.instance.json"`(`obs1_literals.txt`). 스캐너 범위 `PROBES_REL = ("skills", "analog-gmid-design", "assets", "tests", "probes")`(engine_dup_scan.py 26행).
2. **E5 명령 경로**: new_topology 노드 9건이 전부 `tests/contracts/`(`test_d_delete_dead.py` 1, `test_d_delete_telescopic.py` 8)이고 명령 인자 `tests/unit`이 아니다 -- `PT`가 `tests` 전체를 이미 수집해 잡힌다(Phase 1 관찰 B13과 같은 현상, 판정 영향 없음). E5 기준 문구 덮음 표에서 (i) 로드·파이프라인 동일을 덮는 new_topology 노드 0 -- 라이브러리 회로의 로드·파이프라인 동일은 E4 E-LIB가 잰다, 합성 topology에 대해서는 덮는 측정 없음.
3. **`--gmid-dod`의 엄격 대상**: E4(a) 두 실행의 xfailed 수가 같다(15 = 15) -- Phase 2 표식 IC 케이스 0, `--gmid-dod`가 Phase 2에서 엄격 대상을 더하지 않음. 근거: `git grep -n -E 'gmid_ic\([^)]*phase="2"' H -- skills/analog-gmid-design/assets/tests` → 0건(`obs3.txt`). 좁히지 않은 `phase="2"` grep은 `contracts/test_df23_inventory.py:354` `_p10_item(phase="2")` 픽스처 1건(IC 표식 아님).
4. **추적 산출물 `workspaces/*/…instance.json`**: H 트리 `workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.instance.json`의 `topology_ref` = `C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json`, `workspaces/folded-cascode-report/folded_cascode.instance.json`의 `topology_ref` = `C:\Users\HSLEE\…\library\folded_cascode.topology.json`(둘 다 메인 절대 경로, `C:/g90/out/obs4.txt`). 추적 산출물이 DF-36 이전 형식, E4는 새로 생성한 파일로 판정해 영향 없음.

## 절차 메모

- 브리핑과 기준 문서의 어긋남: 없음. 가드 (1)의 '판정 기록을 마지막으로 바꾼 커밋 != P' 주의는 나오지 않았다(P = afcf36c가 마지막 변경). E2 면제 줄 수 1 = 문구 '현재 … 1건'. md 일치 판정 기록의 test 수(1023 → 1062, 새 39)와 auditor가 H에서 센 N = 39가 같다.
- 결과 파일 형식: 오케스트레이터 추가 지시에 따라 `## 판정` 바로 다음 줄에 `판정: PASS` 한 줄을 두었다(E0~E5·N6.3 1~5 모두 PASS).
- 실행 방식: 브리핑 §2 블록을 공통 머리 `C:/g90/scripts/common.sh`(export·변수·`ts`/`mark`·`PT`/`PT2`·판 바꾸기·쓰기 감시 함수)와 스크립트 `guard.sh`·`s1_e0_e1_e5.sh`·`s2_readonly.sh`·`s3_e4a.sh`·`s4_e4b.sh`·`s5_revs.sh`로 나눠 `bash`로 돌렸다. N6.3은 `n63.py`, E3은 `e3_check.py`(auditor 작성), 결과 파일 조립은 `assemble.py`. 판 바꾸기는 매번 `checkout -- workspaces; clean -fdxq; checkout --detach <전체 해시>; HEAD 대조; status --porcelain --ignored 0줄`을 확인했다.
- E5 실행(23:08:32~23:09:04)과 읽기 전용 E2·E3·관찰 1/3(23:08:56~23:09:02)이 시간상 겹쳤다(브리핑이 허용한 읽기 전용 병행; E2·E3은 git 객체와 추적 파일만 읽는다). E4(b) 사본·관찰 4는 E4(a) PT2 실행 중 H 판에서 했다(추적 파일 읽기만).
- E5 덮음 표 빈 부분: (i)을 덮는 new_topology 노드 없음 -- 라이브러리 회로의 로드·파이프라인 동일은 E4 E-LIB가 잰다, 합성 topology에 대해서는 덮는 측정 없음.
- E4(b) 스크립트 사본(H 판에서 복사, 두 판에 같은 사본): sha256 `e_lib.py` 045f65c8cc05e98699518ca123ef8aac0c93b6b51932179aae707e1d21f46201, `e_inst_df35.py` 575fcb32acc1bbd93090d51888959439d6cb27199d53ac54daf8638388fba384, `e_inst_df36.py` aa76989eb30fa6d41a536a6e0e5a2754777e4c99f8877c8a418064bc73ddccb7; blob id 00fbb20f1177fb9899c75374dd73e9077b087547, 67df1684a8d18e455c72e954c2d65e80597cfc1f, ef43c49f2aa9c06e47504cc611029ee70dfb2c39(사전 실행 H' 값과 같음).
- 단계별 소요(`C:/g90/out/timeline.txt`, 모두 단계 예산 안): 복제 24 s(가드 포함 약 1분), E0+DF-23 4 s, E1 수집 32 s / 실행 33 s, E5 32 s, E2 1 s, E3 2 s, N 수집 34 s, E4(a) `PT2` 4분 52초(pytest 280.82 s), `PT2 --gmid-dod` 4분 16초(pytest 245.20 s), E1 판별력 28 s, E4(c) e_lib 3 s / crt 4분 59초 / fc 37 s, E4(d) e_lib 4 s / crt 4분 30초 / fc 42 s. 전체 벽시계 약 25분(23:06:28~23:31:07).
- 복제본 reflog(`iso_reflog.txt`): clone → `5f643a9`(H) → `7535799` → `da03c0e` → `5f643a9`(H). 끝 HEAD = H. 끝 status = E4(d) 산출 3줄(` M workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.instance.json`, ` M workspaces/folded-cascode-report/folded_cascode.instance.json`, `?? workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.report.html`) -- 정상, 그 밖 0줄(E4(c) 직후에도 같은 3줄이었고 E4(d) 판 바꾸기에서 지운 뒤 status 0줄을 확인했다).
- 메인: HEAD 실행 전 `5f643a905fbc14c1374063b47fea6428ba088563` = 실행 뒤 같음, `status --porcelain --ignored` 실행 전과 E4(a)·E4(c)·E4(d) 뒤 모두 동일, stamp 이후 파일 0(지정 경로·루트). 메인 저장소에 상태를 바꾸는 git 명령을 쓰지 않았다(fetch 포함).

## 범위 밖 메모

- 없음(메인 쓰기 감시 불일치 0건, (나) 판정분 없음).

종료: 2026-10-01 23:31, 항목 E0~E5·판별력 3·N6.3 1~5·관찰 1~4 전부 기록.
복제본: HEAD = 5f643a905fbc14c1374063b47fea6428ba088563, reflog 이동 clone→H→7535799→da03c0e→H, status = E4(d) 산출 3줄(정상).
메인: HEAD = 5f643a905fbc14c1374063b47fea6428ba088563, status 차이 0, stamp 이후 파일 0(지정 경로·루트).
