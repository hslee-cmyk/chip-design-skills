"""P9 2차 순서 3 base_check.json 조립(auditor)."""
import json
D = 'C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p9-kcl-edges-audit/.ai/verification/20260930-p9-kcl-edges/'
C = "C:/g47/gmid-gate-cache/7535799302a9ff7cfbfcadb2281d16bf136fadcf"
a1 = json.load(open(D + 'attempt1_base_check.json', encoding='utf-8'))
r = {
 "note": ("05-role-separation §12 순서 3, P9 2차 시도. 1차(T c8d55db·K 16a71fa·M b7765b0)는 순서 7 V2 FAIL(계약 8(c): 레지스트리 428행 'SD:1216-1224' 잔존, 판정 기록 미커밋). "
          "2차 T2는 base가 같고 test blob·T 트리가 1차와 같다. 그래서 엔진·test 트리에만 기대는 base 기준값(DIFF-DUP·구조 AST·E-LIB·E-INST·V3 기준 시간)은 1차 측정을 재사용하고, "
          "이력·커밋에 기댈 수 있는 것(freeze, T2 수집, T2 red 수집 전체 실행, V5 base->T2, strict, V3 인벤토리)은 T2로 다시 쟀다. 모든 수치는 auditor가 C:/g47/*에서 직접 쟀다. "
          "1차 산출물은 이 폴더 attempt1_base_check.json·attempt1_order7/(1차 판정 기록 초안 record_draft_attempt1.json 포함)과 최상위 기준값 파일들. 커밋은 순서 7."),
 "id": "20260930-p9-kcl-edges", "attempt": 2, "evidence_type": "equivalence", "phase": "2",
 "approval": ["20260923-20-dead-code-dup-design", "20260930-p9-e1-correction"],
 "measured_at": "2026-10-01 (2차 순서 3)",
 "environment": a1["environment"],
 "freeze": {
  "base_commit": "7535799302a9ff7cfbfcadb2281d16bf136fadcf", "base_is_gate_master": True,
  "base_is_gate_master_how": "git -C <주 저장소> rev-parse master = 7535799302a9ff7cfbfcadb2281d16bf136fadcf",
  "test_commit_T": "6bf510b6c7bf427129224338cd64930f0343d5d0", "T_tree": "97e27db70a1a4445bfaf89edd7c068be8a7cb40b",
  "T_parent": "7535799302a9ff7cfbfcadb2281d16bf136fadcf", "T_trailers": ["Role: test", "Change-Id: 20260930-p9-kcl-edges"],
  "audit_branch": "role/audit/20260930-p9-kcl-edges", "audit_branch_head_at_freeze": "6bf510b6c7bf427129224338cd64930f0343d5d0",
  "worktree_status_at_freeze": "git status --porcelain 0줄(이 기록 폴더를 쓰기 전)",
  "changed_paths_base_to_T": {"added": ["skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py"], "modified": []},
  "test_blob": "003c0d1d691ba81b6336c579a40441fb61985362 -- auditor git ls-tree T2로 확인, 1차 T c8d55db의 같은 경로 blob과 같다(test-author 보고는 대조용)",
  "T_tree_equals_attempt1": "T2 트리 97e27db7 = 1차 T c8d55db 트리(git rev-parse <rev>^{tree})",
  "outside_tests_diff": "git diff --name-only 7535799 T2 -- ':(exclude)skills/analog-gmid-design/assets/tests/**' 0줄",
  "code_commit_K": None},
 "isolation": {
  "clones": {
   "C:/g47/iso2": "T2(6bf510b) -- 2차 수집·red 수집·V5·strict·V3 인벤토리. clone -c core.longpaths=true --no-hardlinks --no-local --no-checkout <audit worktree> -> remote remove origin -> checkout --detach, remote 0·status 0줄(측정 뒤도 0줄)",
   "C:/g47/base, C:/g47/eq, C:/g47/m": "1차 그대로(remote 0, status 0줄). eq는 마지막 checkout이 1차 M b7765b0 -- 순서 7에서 쓰면 checkout --detach + clean -fdxq"},
  "gate_code": {"how": "C:/Python314/python.exe -P C:/g47/scripts/extract_gate.py C:/g47/iso2 7535799… C:/g47/gate2_check -> %s와 diff -r 차이 0" % C,
                "file_set_sha256": "705036ea1039e7abb0e449918a8209b229f4a685ab2da9d0e03907bf571d82c4 (1차와 같음)"}},
 "strict_set": {"how": "base 판 strict_check.py C:/g47/iso2 … -> 출력 strict_check2.txt가 1차 strict_check.txt와 바이트 동일",
                "strict_needed": [], "v1_option": "--gmid-phase=2 --gmid-strict=", "new_symbols_from_interface_card": []},
 "v1_command_template": a1["v1_command_template"],
 "base_run": {
  "script": "bash C:/g47/scripts/run2.sh collect|red (run.sh의 루트를 C:/g47/iso2, 출력 이름을 *_T2로 바꾼 판)",
  "collection": {"base_collected": 813, "base_reused": "1차 순서 3 base 수집 813(base 커밋 같음)", "T_collected": 837, "T_collect_exit": 0,
                 "T_ids_equal_attempt1": True, "new_by_file": {"skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py": 24}},
  "full_run": {"base": "1차 순서 3 재사용: 798 passed, 15 xfailed, exit 0(base 커밋 같음)",
               "T2_on_base_engine": "822 passed, 15 xfailed, exit 0, 371.24s (C:/g47/iso2, -p merge_gate --continue-on-collection-errors, out/full_T2_red.txt), FAILED/ERROR 0"},
  "red_capture": {
   "command": ("GMID_RED_CAPTURE=C:/g47/out/red_T2.jsonl GMID_INTERFACE_CARD=C:/g47/iso2/docs/02-design/specs/20260930-p9-kcl-edges.interface.md PYTHONPYCACHEPREFIX=C:/g47/pyc2_full_iso "
               "PYTHONPATH=%s C:/Python314/python.exe -P -m pytest -c %s/pytest_gate.ini --rootdir=C:/g47/iso2 --confcutdir=C:/g47/iso2 -p merge_gate --continue-on-collection-errors "
               "--gmid-phase=2 --gmid-strict= C:/g47/iso2/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider") % (C, C),
   "capture_file_sha256": "db2ffce300415eef967e0926969d2b84550bbf1d878bd270054ef8924a8dba78",
   "identical_to_attempt1": "red_T2.jsonl이 1차 red_T.jsonl과 바이트 동일(cmp) -- 12줄 전부 IC xfail builtins.Failed, AssertionError 0, test_dup_kcl_edges 항목 0",
   "equivalence_judgement": "새 test 24개 전부 base 엔진에서 PASS, red 없음 -- equivalence 순서 3 조건 충족. 판정 기록 red 필드는 비운다"}},
 "v5_base_to_T2": {
  "command": "PYTHONPYCACHEPREFIX=C:/g47/pyc2_v5 C:/Python314/python.exe %s/weakening_diff.py --root C:/g47/iso2 --base 7535799302a9ff7cfbfcadb2281d16bf136fadcf --head 6bf510b6c7bf427129224338cd64930f0343d5d0" % C,
  "exit": 0,
  "output": "{\"tool\": \"V5\", \"verdict\": \"PASS\", \"findings\": [], \"diff_paths\": [], \"diff_hash\": null, \"approved\": false}",
  "auditor_judgement": "1차 base->T 출력과 바이트 동일. 새 파일 추가뿐, 약화 대상·diff 해시 없음"},
 "reuse_judgement": {
  "rule": ("base 커밋 7535799 동일 + T2 트리 = 1차 T 트리(97e27db7) -> skills·workspaces·tools·library 트리 id가 1차 base·T와 같다. DIFF-DUP·구조 AST·E-LIB·E-INST 기준값은 "
           "base 트리(엔진·library·analog-grammar·run_harness)에만 기대고 docs·이력을 읽지 않으므로 1차 값을 그대로 쓴다"),
  "reused": {"diff_dup_baseline": a1["diff_dup_baseline"], "ast_structure_baseline": a1["ast_structure_baseline"], "e_lib_e_inst_baseline": a1["e_lib_e_inst_baseline"],
             "attempt1_order7_base_side": "1차 순서 7의 같은 시각대 base 재측정(E-INST o7base1·o7base2, E-LIB elib_base_o7.json)은 attempt1_order7/에 있다 -- 2차 순서 7 동등 비교 기준으로도 쓴다"},
  "remeasured": "freeze, T2 수집(837, id 집합 1차 T와 같음), T2 전체 red 수집, V5 base->T2, strict, V3 인벤토리(T2: kcl_series_union 72, find 144, _kcl_and_matching_edges 142 -- 1차 T와 test 목록까지 같음, v3_inv_6bf510b.json)"},
 "v3_preparation": {
  "inventory_T2": {"kcl_series_union": 72, "kcl_series_union.find": 144, "_kcl_and_matching_edges": 142},
  "attempt1_order7": ("1차 병합본 V3: 28변이 전부 죽음(timeout 4), --timeout 720 = 병합본 기준 218.49s의 3.3배, 3782s. 2차 병합본의 stick_diagram.py blob이 1차 K와 같고 "
                      "tests 트리가 같으면 변이 대상·변이 id·인벤토리가 같으므로 재사용한다(o7_reuse.py가 조건을 판정)")},
 "order7_reuse_plan": {
  "script": ("bash C:/g47/scripts/o7_attempt2.sh <M2> (이 폴더 scripts/o7_attempt2.sh): C:/g47/m2 격리 복제 -> o7_reuse.py(재사용 조건: M2 첫 부모 = T2, stick_diagram.py blob = "
             "1차 K 16a71fa blob, skills·workspaces·tools 트리 = 1차 M, 1차 M->M2 diff ⊆ 레지스트리 1파일; 계약 8 레지스트리 행별 줄 번호 표기·부호 규약/레일 이름 집합 언급) -> reg_check -> "
             "V4·V5·V6·V7. 자기 점검: 1차 M b7765b0에 돌리면 428행 'SD:1216-1224'를 찾고 reuse_ok False(첫 부모가 T2 아님)"),
  "if_reuse_ok": "V1·V3·DIFF-DUP·E-LIB·E-INST·구조 AST는 1차 순서 7 측정을 재사용(엔진·tests 트리 동일 근거를 basis에 적는다), 레지스트리 대조·reg_check·V4~V7·receive 사전 판정만 다시 돈다",
  "if_not": "엔진이나 tests가 다르면 1차 순서 7 전 과정을 다시 돈다"},
 "outputs_kept": {
  "C:/g47/out/red_T2.jsonl": "db2ffce300415eef967e0926969d2b84550bbf1d878bd270054ef8924a8dba78",
  "C:/g47/out/full_T2_red.txt": "69d03ffad59c25dffe16b5fecb58ea075898819df270b861ec2e33ea536a133d",
  "C:/g47/out/collect_iso2.txt": "e232715391807176d1497faf6fc50866c6ea4ccd400951c7c0078fe36ae11e34",
  "C:/g47/out/v5_base_T2.txt": "a2e2fe0f2d96c3292853a13755dd1223457711294e7e1ac0e8fa0d0bcae2cf54"}}
with open(D + 'base_check.json', 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(json.dumps(r, ensure_ascii=False, indent=1) + '\n')
print('ok')
