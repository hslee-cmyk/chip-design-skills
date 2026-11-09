"""DF-36 2차 시도 순서 7 판정 기록 생성(auditor). red 필드는 순서 3 캡처(red_T.jsonl)의 새 test 파일 줄(AssertionError 20 + Failed 1)을
순서대로 옮긴다(오케스트레이터 결정: red 21건, 새 다른 드라이브 2건은 허용 예외 타입 밖이라 red 미기록).
사용: python -P make_record36.py <red_T.jsonl> <out.json> <time>"""
import json, sys
red_f, out, now = sys.argv[1:4]
red = [json.loads(l) for l in open(red_f, encoding="utf-8")]
red = [d for d in red if "test_df36_instance_relpath.py::" in d["test_id"]]
assert len(red) == 21 and {d["exc_type"] for d in red} == {"builtins.AssertionError", "builtins.Failed"}
B = "070cf6937e2841bdd3b4781eb9b8ba5bba9cc606"
T = "6444a031e9c4d3e03c9c11714e6580f14b0e3e1c"
K = "ed98d35b22b9d3dfac5b26e7794709e1e39b1673"
M = "b29be01281e66cc041e7e507a946b5373092a346"
C = "C:/g16/gmid-gate-cache/" + B
ID = "20260930-df36-instance-relpath"
checks = {
 "V1": {"verdict": "PASS", "basis": (
  "병합본 M b29be01(부모 [T 6444a03, K ed98d35], 트리 98bfad45 = K 트리, Role: doc·Change-Id 일치)의 격리 복제본 C:/g16/m(git clone --no-hardlinks --no-local "
  "--no-checkout, origin 제거, checkout --detach, remote 0·status 0줄, 실행 뒤 status 0줄)에서 base 판 캐시 070cf69의 pytest_gate.ini로 slow 포함 전체 실행(-k·"
  "--deselect·-x·-m 없음, --gmid-phase=2 --gmid-strict=): 798 passed, 15 xfailed, 실패·오류·skip·xpass 0, 수집 813(T 수집 수와 같음, T->M diff는 stick_diagram.py뿐), "
  "수집 오류 0, exit 0, 123.79s. 798 = base 759 + 새 파일 39. 엄격 집합은 base 판 merge_gate.strict_set = 빈 집합, v1_command_check 실패 0건(순서 3). 게이트 코드는 "
  "git cat-file blob 070cf69:tools/gates/<파일>로 auditor가 redteam 밖 22개를 직접 뽑았다(file_set 해시 ab7afccd…, 1차와 같음). code-author 보고는 증거로 쓰지 않았다")},
 "V2": {"verdict": "PASS", "basis": (
  "red-green. [사슬] base 070cf69(gate master; spec card·설계 예시 정정 포함) -> T 6444a03(Role: test, 새 contracts/test_df36_instance_relpath.py 하나, tests 밖 diff 0) -> "
  "K ed98d35(Role: code, stick_diagram.py +18/-1, blob dbd35acd = 1차 K a78dd02의 blob과 같다) -> M b29be01(Role: doc, 부모 [T, K], 트리 = K 트리). test 커밋 불변: git diff T M = "
  "stick_diagram.py뿐. [red] 순서 3(이 폴더 base_check.json): T 복제본에서 base 판 red 수집 플러그인이 기록한 red 21건(_ALWAYS_RED): 계약 1 library 9회로 절대 경로 9, "
  "계약 3 체크아웃 루트 누출 9, 계약 2 표기·cwd·출력 위치 2(AssertionError), 계약 4 저장소 밖 topology 수용 1(builtins.Failed, DID NOT RAISE); failure_hash는 auditor가 "
  "따로 계산해 같다. 새 test 2건 test_other_drive_topology_rejected[backslash|slash](계약 4 보강: 다른 드라이브 절대 경로 -> ValueError·파일 없음)은 base에서 "
  "builtins.FileNotFoundError(save_instance_json이 Z: 경로 topology를 열다 실패)로 실패한다 -- 00-common §8.1 허용 예외 타입 밖이라 플러그인이 red로 기록하지 않았고 red 필드에 "
  "없다(오케스트레이터 결정: red 21건 유지, 계약 4의 red-green은 test_outside_repo_topology_rejected가 증거하고 새 2건은 병합본 PASS와 V3로 확인). [green] 병합본 V1 798 passed; "
  "새 파일을 red 수집 플러그인으로 따로 돌려 39 passed, red 기록 0; red 21 test id 21/21 PASSED, 새 2건 PASSED(새 test 23건 green). [순수 변경 범위] scripts/scope_cmp36.py: "
  "병합본 최상위에서 새 def _topology_ref_relpath(save_instance_json 바로 앞)를 빼면 최상위 176문장 중 save_instance_json만 다르고, 그 함수의 data['topology_ref'] 값 식 "
  "_topology_ref_relpath(topology_json_path)를 base 식 topology_json_path로 되돌리면 base 함수 ast.dump와 같다; 변경 경로 = stick_diagram.py(numstat 18/1) + 새 test. "
  "헬퍼에 library 회로 이름·'.topology.json'·'library' 문자열 0 -- 경로 규칙만(루트 = __file__의 ../../.., realpath 뒤 relpath, 다른 드라이브·'..' 시작·절대면 ValueError). "
  "[계약 5 동작 보존] E-INST(scripts/e_inst_df36.py·einst.sh, 같은 경로 C:/g16/eq에서 base와 M): 두 회로 모두 (a) topology_ref 뺀 해시 = base(folded 0ca6746f…, pilot 185b675e…) "
  "(b) topology_ref 외 7필드 해시 = base (c) topology_ref 값 표기만 가린 파일 바이트 해시 = base(folded a783cbe5…, pilot f555c89c…; 키 순서·서식 동일) (d) topology_ref = 계약 1 "
  "기대값 skills/analog-gmid-design/assets/library/<파일> (e) 경로 문자열 잎 0. E-LIB-INST(scripts/e_lib_inst.py, library 9회로로 save_instance_json 직접, 출력 저장소 밖): "
  "합산 해시 두 개(topology_ref 뺀 e4762cff…, 가린 바이트 1f0956cb…)와 회로마다 topology_ref 뺀·가린 바이트·7필드 해시가 base와 같고, 9회로 topology_ref = 계약 1 기대값, "
  "루트 누출 0. E-LIB(scripts/e_lib.py) 1d2e3bf6… 출력 파일이 base와 바이트 동일. base 기준값은 1차 값을 트리 동일 근거로 재사용할 수 있으나 순서 3에서 C:/g16/eq로 다시 재 "
  "같음을 확인했다. [계약 6] 설계 문서 analog-topology-json-library.design.md 143행 예시 = skills/analog-gmid-design/assets/library/folded_cascode.topology.json(base 070cf69 "
  "문서 커밋, M에서 확인). reg_check.py 병합본 exit 0 '발견 0'(auditor 실행)")},
 "V3": {"verdict": "PASS", "basis": (
  "도구: base 판 캐시 mutate_changed.py --root C:/g16/m --base 070cf69 --head b29be01 --pytest-ini <캐시>/pytest_gate.ini --gmid-phase=2 --gmid-strict= -> verdict FAIL, "
  "mutants 26, killed 0 -- 22개 '변이 없는 기준 실행에서 인벤토리 test가 통과하지 않음'(면제 4는 exempt). 원인(scripts/v3_baseline_probe.py): 도구가 저장소를 .git 없이 복사해 "
  "인벤토리의 기존 test contracts/test_ts6_probe_relocate.py::test_base_blob_reader_reads_the_base_tree가 'not a git repository'로 실패 -- 도구 환경 한계(B28로 추적, handoff). "
  "대체 측정(scripts/mut_def.py: 같은 도구 함수 changed_defs·mutants·_replace_def·inventory·_approved_ids와 같은 pytest 명령을 .git이 있는 격리 복제본 C:/g16/mut에서; "
  "list 모드로 면제 id 4개가 M에서도 같은 변이 id이고 같은 문장(save_instance_json body[2] scope_note 분기·body[2].body[0], json.dump indent=2 ±1)을 가리킴을 확인; 기준 실행 "
  "인벤토리 69개 97 passed·3 xfailed): 26 중 killed 22, exempt 4(head 트리 승인 20260922-ic3-v3-exempt), 생존 0. 새 코드 _topology_ref_relpath 변이 12개 전부 killed -- "
  "1차 생존 변이 except_body_delete:body[3].handlers[0](다른 드라이브 분기)도 killed이고, 그 변이를 넣으면 test_other_drive_topology_rejected 2건이 실패함을 따로 확인"
  "(scripts/probe_t2_vs_1st_survivor.py, 변이 없음 2 passed)")},
 "V4": {"verdict": "PASS", "basis": (
  "oracle 대조: 기대값마다 spec card oracle과 대조했다(아래, 모두 일치). 도구: base 판 캐시 test_lint.py --root C:/g16/m --base 070cf69 --head b29be01 --subject "
  "stick_diagram:save_instance_json --subject stick_diagram:_topology_ref_relpath -> verdict PASS, exit 0, 대상 파일 1(test_df36_instance_relpath.py), findings 25 전부 (2) "
  "NO-SUBJECT, UNJUDGED·FAIL 0. PASS는 독립의 증거가 아니다(피검 출력을 파일로 쓰고 다시 읽어 도구가 참조를 못 본다). 기대값별 대조(auditor가 소스를 읽음): "
  "repo_relative 9·same_for_path_spellings_and_cwd·same_for_output_locations = card oracle (a) 구성 -- 기대값은 test 파일 __file__의 루트와 입력 topology 경로로 test가 만든다"
  "(피검 출력 아님; 일치: auditor E-INST·E-LIB-INST의 기대 계약 1 값도 따로 계산해 병합본 값과 같음); no_checkout_root 9 = 계약 3 금지 문자열이 test 쪽 루트 표기 (a)(일치); "
  "outside_repo_topology_rejected·missing_sizing_still_rejected = card 계약 4·'거부해야 할 입력' ValueError·파일 없음 (a)(일치); other_drive_topology_rejected 2 = 계약 4 "
  "'저장소 밖 topology -> ValueError, 출력 파일 없음'의 다른 드라이브 입력(루트 드라이브와 다른 문자를 test가 골라 만든 경로, 기대값은 예외 타입·파일 없음뿐) (a)(일치); "
  "relative_ref_check rejects·accepts·leak_and_pointer_checks = 판정기 자기 점검, 손으로 만든 값이 card '거부해야 할 입력'과 하나씩 대응 (a)(일치). 계약 5는 test에 박지 않고 "
  "auditor E-INST로 판정(V2)")},
 "V5": {"verdict": "PASS", "basis": (
  "base 판 캐시 weakening_diff.py --root C:/g16/m --base 070cf69 --head b29be01 -> verdict PASS, findings 없음, diff_paths 없음, diff_hash null, approved false, exit 0. "
  "순서 3 base -> T 출력과 같다(K는 test를 건드리지 않았다). 새 test 파일은 추가라 약화 대상이 아니다. 기록할 diff 해시 없음")},
 "V6": {"verdict": "PASS", "basis": (
  "base 판 캐시 source_lint.py --root C:/g16/m --base 070cf69 --head b29be01 -> verdict PASS, targets [skills/analog-gmid-design/assets/stick_diagram.py], findings 0, exit 0")},
 "V7": {"verdict": "PASS", "basis": (
  "base 판 캐시 reachability.py --root C:/g16/m --base 070cf69 --head b29be01 -> verdict PASS, new_defs [stick_diagram.py::_topology_ref_relpath], unreached 없음, "
  "unreached_without_approval 없음, exit 0. 호출부: stick_diagram.py 9001행 save_instance_json의 data['topology_ref'] 한 곳(auditor grep, assets·workspaces·tools에서 유일); "
  "운영 경로 run_harness.run -> save_instance_json -> _topology_ref_relpath(E-INST 산출의 topology_ref가 헬퍼 값, V2)")},
 "V8": {"verdict": "N/A", "basis": "도입 4: 폴백 발동 0 검사는 Phase 4부터(N4.2 v_intro[V8] = 4). 이 card는 Phase 2이고 저장소 밖 입력은 폴백 없이 ValueError다(계약 4)"},
 "V9": {"verdict": "N/A", "basis": "도입 6b: 물리 불변식 검사는 Phase 6b부터(N4.2 v_intro[V9] = 6b). 엔진 식 변경 없음, E-LIB·E-LIB-INST·E-INST 나머지 필드가 base와 같다(V2)"},
 "V10": {"verdict": "PASS", "basis": (
  "spec card '재현할 수치'가 '없음'이라 reproduced_numbers는 빈 배열이다. 이 기록의 수치(수집 774 -> 813, 병합본 798 passed·15 xfailed, base red 21건과 해시, 새 2건 base "
  "FileNotFoundError, AST 대조, E-LIB·E-LIB-INST·E-INST 값, 변이 결과, 도구 출력, reg_check)는 전부 auditor가 격리 복제본 C:/g16/*에서 직접 쟀다(순서 3은 이 폴더 "
  "base_check.json). code-author 보고('798 passed·15 xfailed', 1차와 같은 코드)는 증거로 쓰지 않았고 auditor 실행 결과가 같았다")},
}
rec = {
 "id": ID,
 "spec_card": "docs/02-design/specs/" + ID + ".spec.md",
 "evidence_type": "red-green",
 "base_commit": B,
 "test_commit": T,
 "code_commit": K,
 "red": {"test_ids": [d["test_id"] for d in red], "failure_hashes": [d["failure_hash"] for d in red]},
 "checks": checks,
 "reproduced_numbers": [],
 "approvals": ["20260923-20-dead-code-dup-design", "20260922-ic3-v3-exempt"],
 "auditor_run": {
  "time": now,
  "worktree": "C:/Users/HSLEE/Documents/Todoc/fpga/wt/" + ID + "-audit",
  "commands": [
   "환경: $PY = C:/Python314/python.exe(3.14.2), export APPDATA=C:/Users/HSLEE/AppData/Roaming, 출력 C:/g16/out, 스크립트 C:/g16/scripts/(사본 .ai/verification/" + ID + "/scripts/)",
   "게이트 코드: C:/Python314/python.exe -P C:/g16/scripts/extract_gate.py C:/g16/m " + B + " " + C + " (git ls-tree + git cat-file blob, tools/gates/ 중 redteam/ 밖 22개)",
   "격리: git clone -q -c core.longpaths=true --no-hardlinks --no-local --no-checkout C:/Users/HSLEE/Documents/Todoc/fpga/wt/" + ID + "-audit C:/g16/<이름>; git -C C:/g16/<이름> remote remove origin; git -C C:/g16/<이름> checkout -q --detach <rev> -- 순서 3: iso = T 6444a03, base = 070cf69, eq = base; 순서 7: m = M b29be01, mut = M(변이 전용), eq = M(새 복제), 모두 remote 0, status 0줄",
   "V1: PYTHONPYCACHEPREFIX=C:/g16/pyc_v1_m PYTHONPATH=" + C + " C:/Python314/python.exe -P -m pytest -c " + C + "/pytest_gate.ini --rootdir=C:/g16/m --confcutdir=C:/g16/m --gmid-phase=2 --gmid-strict= C:/g16/m/skills/analog-gmid-design/assets/tests",
   "수집·green: bash C:/g16/scripts/run_m.sh v1|green (green = 새 파일 -p merge_gate, GMID_RED_CAPTURE=C:/g16/out/red_M.jsonl, -rA)",
   "base red(순서 3): GMID_RED_CAPTURE=C:/g16/out/red_T.jsonl GMID_INTERFACE_CARD=C:/g16/iso/docs/02-design/specs/" + ID + ".interface.md PYTHONPYCACHEPREFIX=C:/g16/pyc_full_iso PYTHONPATH=" + C + " C:/Python314/python.exe -P -m pytest -c " + C + "/pytest_gate.ini --rootdir=C:/g16/iso --confcutdir=C:/g16/iso -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= C:/g16/iso/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider (bash C:/g16/scripts/run.sh red)",
   "변경 범위: C:/Python314/python.exe -P C:/g16/scripts/scope_cmp36.py C:/g16/m " + B[:7] + " " + M[:7] + " C:/g16/out/scope_cmp36.json",
   "E-LIB: PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g16/scripts/e_lib.py C:/g16/eq C:/g16/out/elib_<base|m>.json",
   "E-LIB-INST: rm -rf C:/g16/ws_lib; PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g16/scripts/e_lib_inst.py C:/g16/eq C:/g16/ws_lib C:/g16/out/elibinst_<base|m>.json",
   "E-INST: bash C:/g16/scripts/einst.sh C:/g16/eq <base|m> <folded_cascode|current_reuse_telescopic_ota> (e_inst_df36.py; 실행 전후 git checkout -- workspaces + clean -fdxq)",
   "게이트 도구(V3·V4·V5·V6·V7): bash C:/g16/scripts/tools_m.sh fast|v3 (base 판 캐시 도구를 --root C:/g16/m --base " + B[:7] + " --head " + M[:7] + " 로, -P 없이; V4 --subject stick_diagram:save_instance_json --subject stick_diagram:_topology_ref_relpath)",
   "V3 진단·대체: PYTHONPATH=" + C + " C:/Python314/python.exe -P C:/g16/scripts/v3_baseline_probe.py C:/g16/m " + M[:7] + " C:/g16/diag C:/g16/out/v3_probe.txt; PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=" + C + " C:/Python314/python.exe -P C:/g16/scripts/mut_def.py C:/g16/mut " + B + " " + M + " <list|baseline|0:13|13:26|summary> C:/g16/out/mut_def.jsonl --gmid-phase=2 --gmid-strict=; PYTHONPATH=" + C + " C:/Python314/python.exe -P C:/g16/scripts/probe_t2_vs_1st_survivor.py C:/g16/mut " + B[:7] + " " + M[:7] + " <M의 test 파일> " + C,
   "reg_check: PYTHONPYCACHEPREFIX=C:/g16/pyc_reg_m C:/Python314/python.exe C:/g16/m/skills/analog-gmid-design/assets/tests/tools/reg_check.py --registry C:/g16/m/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root C:/g16/m"
  ]
 }
}
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(rec, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
print("ok")
