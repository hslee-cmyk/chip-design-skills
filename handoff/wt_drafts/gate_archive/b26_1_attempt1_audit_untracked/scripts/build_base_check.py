# 순서 3 base_check.json 작성(BOM 없는 UTF-8). V5는 weakening_diff 출력 JSON 객체 그대로. 다른 곳에 diff_hash·diff_paths 키 없음.
import json, subprocess, sys, collections, hashlib
A = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-audit"
ID = "20260930-b26-rail-accessor-set"
D = A + "/.ai/verification/" + ID
O = D + "/out"
B1 = "6df4bd7fd9920e752da4b16bff9b0513caf78362"
T1 = "c247a7697fad8f4695a89d6c9fd0683b900e86fd"
C = "C:/g412/gmid-gate-cache/" + B1
PY = "C:/Python314/python.exe"
ISO = "C:/g412/iso"
NEWF = "skills/analog-gmid-design/assets/tests/contracts/test_b26_rail_accessor.py"

def git(*a):
    return subprocess.run(["git"] + list(a), capture_output=True, check=True).stdout.decode("utf-8", "replace")

def jl(p):
    return json.load(open(p, encoding="utf-8"))

v5 = jl(O + "/order3_v5_weakening_diff.json")
ra = jl(O + "/order3_red_analysis.json")
v4c = jl(O + "/order3_v4_compare.json")
v4 = jl(O + "/order3_v4_test_lint.json")
exc = jl(O + "/order3_t1_exc_types.json")
exc_by = {e["test"]: e for e in exc}
freeze_txt = open(O + "/freeze.txt", encoding="utf-8").read()
strict_txt = open(O + "/order3_strict_set.txt", encoding="utf-8").read()
v3_txt = open(O + "/order3_v3_testonly.stdout.txt", encoding="utf-8").read()
v3 = json.loads(v3_txt.splitlines()[0])

raw = git("-C", ISO, "diff", "--raw", "--no-abbrev", B1, T1).splitlines()
paths = []
for line in raw:
    meta, path = line.split("\t", 1)
    f = meta.split()
    paths.append({"path": path, "status": f[4], "b1_blob": f[2], "t1_blob": f[3]})

def short(tid):
    return tid.split("::", 1)[1] if "::" in tid else tid

new_rows = []
for r in ra["new_tests"]:
    n = short(r["test_id"])
    e = exc_by.get(n)
    new_rows.append({"test": n, "column": r["column"], "base_outcome(T1 tests, B1 engine)": r["t1_outcome"],
                     "exception": (e["type"] if e else None), "last_E": (e["last_E"] if e else None),
                     "red_capture_exc_type": r["red_capture"]})
col_counts = collections.defaultdict(collections.Counter)
for r in new_rows:
    col_counts[r["column"]]["%s|%s|red=%s" % (r["base_outcome(T1 tests, B1 engine)"], r["exception"], r["red_capture_exc_type"])] += 1
assert_red_bad = [r["test"] for r in new_rows if r["column"] == "단언 red" and r["exception"] in ("TypeError", "AttributeError")]

changed = ra["existing_changed"]
ch_rows = []
for c in changed:
    n = short(c["test_id"])
    e = exc_by.get(n)
    ch_rows.append({"test_id": c["test_id"], "b1": c["b1"], "t1": c["t1"], "red_capture_exc_type": c["red_capture"],
                    "exception": e["type"] if e else None, "last_E": e["last_E"] if e else None})
def reason(r):
    if r["red_capture_exc_type"] == "builtins.AttributeError":
        return "rails= 호출을 위해 stick_diagram.rail_declaration(신규 심볼, base 부재) 호출 -> AttributeError"
    if "test_b34_c8_restored_values_equal_fresh_process" in r["test_id"]:
        return "_B34_FRESH_SCRIPT 새 프로세스가 rail_declaration AttributeError로 종료 -> assert 1 == 0"
    if r["test_id"].endswith("_signature_unchanged"):
        return "P9 시그니처 test 기대에 rails 추가(V5 발견 '비교 완화' 단위) -> base 시그니처와 다름"
    return "그 밖"
reasons = collections.Counter(reason(r) for r in ch_rows)
for r in ch_rows:
    r["reason"] = reason(r)

xfail_red = [x for x in ra["red_capture_s0"] if not x["test_id"].startswith(NEWF)
             and x["test_id"] not in {c["test_id"] for c in changed}]

status = git("-C", A, "status", "--porcelain")
log_after = git("-C", A, "log", "--oneline", "refs/heads/role/test/%s..HEAD" % ID)
head = git("-C", A, "rev-parse", "HEAD").strip()

cmd_v5 = "%s %s/weakening_diff.py --root %s --base %s --head %s" % (PY, C, ISO, B1, T1)
cmd_v4 = ("%s %s/test_lint.py --root %s --interface-card %s/docs/02-design/specs/%s.interface.md --base %s --head %s"
          % (PY, C, ISO, ISO, ID, B1, T1))
cmd_v4b = ("%s %s/test_lint.py --root %s --interface-card %s/docs/02-design/specs/%s.interface.md --head %s <B1에 있는 바뀐 파일 9개>"
           % (PY, C, ISO, ISO, ID, B1))
cmd_v3 = ("%s %s/mutate_changed.py --root %s --base %s --head %s --pytest-ini %s/pytest_gate.ini --python %s --gmid-phase=3 --gmid-strict="
          % (PY, C, ISO, B1, T1, C, PY))
def pytest_cmd(clone, red):
    s = ("PYTHONPYCACHEPREFIX=C:/g412/pycache_<tag> PYTHONPATH=%s %s -P -m pytest -c %s/pytest_gate.ini --rootdir=%s --confcutdir=%s "
         "--gmid-phase=3 --gmid-strict= -q -rA" % (C, PY, C, clone, clone))
    if red:
        s = ("GMID_RED_CAPTURE=C:/g412/red_<tag>.jsonl GMID_INTERFACE_CARD=%s/docs/02-design/specs/%s.interface.md " % (clone, ID)) + s \
            + " -p merge_gate --continue-on-collection-errors"
    return s + " %s/skills/analog-gmid-design/assets/tests" % clone

v4_rule1 = v4c["t1_rule1"]
out = {
    "change_id": ID, "attempt": 1, "order": 3, "base_B1": B1, "test_end_T1": T1,
    "isolation": ["git clone --no-hardlinks --no-local -c core.autocrlf=false -c core.longpaths=true --no-checkout %s C:/g412/iso" % A,
                  "git -C C:/g412/iso remote remove origin", "test -z \"$(git -C C:/g412/iso remote)\"",
                  "git -C C:/g412/iso checkout --detach %s" % T1,
                  "(B1 기준값용 같은 절차) C:/g412/isob, checkout --detach %s" % B1],
    "gate_code": {"cache": C, "gate_master": B1, "orchestrator_cache_cmp": "16개 파일 모두 cmp 같음(out/cache_cmp.txt)"},
    "freeze": {
        "audit_wt_HEAD": head, "role_test_tip": T1,
        "commits_B1_to_T1": [{"commit": "61751ab1756c371953be188ede0fc08e3f02240c", "parent": B1,
                              "trailers": ["Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>", "Role: test",
                                           "Change-Id: " + ID],
                              "note": "트레일러 셋(Co-Authored-By 포함) -- '정확히 두 줄' 조건과 다름. 1차는 병합 없는 측정 시도라 멈추지 않음(오케스트레이터 지시), 2차에서 다시 씀"},
                             {"commit": T1, "parent": "61751ab1756c371953be188ede0fc08e3f02240c",
                              "trailers": ["Role: test", "Change-Id: " + ID]}],
        "first_parent_chain_on_B1": True, "merges": 0,
        "changed_paths": paths,
        "all_under_tests_not_tools": all(p["path"].startswith("skills/analog-gmid-design/assets/tests/")
                                         and not p["path"].startswith("skills/analog-gmid-design/assets/tests/tools/") for p in paths),
    },
    "strict_set": {"value": "", "source": "base 판 merge_gate.strict_set(TreeView(B1), parse_spec_card(B1 card)) -- phase 3, activated_ic_case [] -> 빈 집합",
                   "raw": strict_txt.strip()},
    "V5": v5,
    "V5_check": {"command": cmd_v5, "verdict": v5["verdict"], "approved": v5["approved"],
                 "expected_by_user_decision_20261007": "2경로(test_dup_kcl_edges.py·test_b34_grammar_explicit.py), 발견 = P9 시그니처 test 2건 '비교 완화' + test_b34 <module> '리터럴 변경' 1건",
                 "findings_units": [[f["path"].rsplit("/", 1)[1], f["unit"], f["pattern"]] for f in v5["findings"]],
                 "matches_expectation": True,
                 "note": "V5 출력의 해시는 sha256 64자리(키 V5 안). 승인 기록은 2차 운반에서(사용자 답 '(가) 합친 V5 승인')."},
    "red_preview": {
        "commands": [pytest_cmd("C:/g412/iso", True) + "  (PYTHONHASHSEED=0, 1)"],
        "summary_T1_tests_B1_engine": {"seed0": ra["t1_s0_tail"], "seed1": ra["t1_s1_tail"],
                                       "outcomes_identical_across_seeds": ra["t1_seed_outcomes_identical"]},
        "red_capture": {"n_seed0": ra["red_s0_n"], "n_seed1": ra["red_s1_n"], "identical_across_seeds": ra["red_seed_identical"],
                        "set_sha256_of_sorted_testid_tab_exctype_lines": ra["red_set_sha256_testid_exctype"],
                        "file": "out/red_t1red_s0.jsonl, out/red_t1red_s1.jsonl",
                        "xfail_tests_recorded_as_Failed(base에서도 XFAIL, 판정 변화 없음)": [x["test_id"] for x in xfail_red]},
        "new_tests_total": len(new_rows),
        "four_columns_counts": {k: dict(v) for k, v in col_counts.items()},
        "assertion_red_column_TypeError_or_AttributeError": assert_red_bad,
        "new_tests": new_rows,
        "facts": [
            "단언 red 칸 33개: red 수집 19(AssertionError 10, Failed 9), 그 밖 FAILED 3(test_b26_c2_meta_rails_is_entry_declaration·c2_linked_same_set_other_order_accepted·c2_linked_without_declaration_uses_entry -- KeyError 'rails', 허용 예외 밖이라 red 아님), PASSED 11(c6 가지 8개 -- 동작 보존 가지, oracle (b) current_reuse_telescopic_ota·folded_cascode·nmcnr_amplifier 3개). TypeError·AttributeError 0 -> 진입점 결함 없음",
            "oracle (b) two_stage_ota만 base AssertionError(card 문장과 같음)",
            "card 'base TypeError(집계 밖)' 칸 16개: 15개는 TypeError가 아니라 stick_diagram.rail_declaration AttributeError(신규 심볼 쌍이라 red 수집이 신규 심볼 red로 기록), test_b26_c4_rails_keyword_only_without_default는 KeyError 'rails'(red 아님)",
            "신규 심볼 칸 15개: 14개 AttributeError(rail_declaration) red, test_b26_c1_rejection_check_fails_on_silent_or_unlabeled_refusal은 base PASSED(합성 구현만 판정 -- 신규 심볼 미사용)",
            "green 칸 test_b26_c4_existing_defaults_unchanged base PASSED",
        ],
        "existing_tests_changed_B1_to_T1": {"n": len(ch_rows), "by_reason": dict(reasons),
                                             "outside_rails_cause": [r["test_id"] for r in ch_rows if r["reason"] == "그 밖"],
                                             "rows": ch_rows},
    },
    "V4_preview": {
        "command": cmd_v4, "b1_comparison_command": cmd_v4b, "verdict": v4["verdict"],
        "rule1": v4_rule1,
        "rule1_new_or_changed_line_FAIL": [r for r in v4_rule1 if r["output"] == "FAIL" and r["class"] == "새"],
        "rule1_existing_FAIL_lines_T1": [r["t1_line"] for r in v4_rule1 if r["output"] == "FAIL" and r["class"] == "기존"],
        "rule1_existing_FAIL_lines_B1": [r["b1_same_finding"][0]["b1_line"] for r in v4_rule1 if r["output"] == "FAIL" and r["class"] == "기존"],
        "rule2_counts": v4c["t1_rule2_counts"],
        "note": "SD selftest 기존 7건(B1 s133 3090·3092·3094·3096, s134 3129, s135 3153, s159 3926 = T1 3120·3122·3124·3126·3159·3183·3956)은 B1 트리 같은 도구에서 같은 줄 글·같은 FAIL -- '기존'(사용자 답 '(가′) 면제 + 재검토 줄', 면제 기록은 2차 전). SR s052·s054 exempt. 새 파일(test_b26_rail_accessor.py)·바뀐 줄 FAIL 0.",
        "files": "out/order3_v4_test_lint.json, out/order3_v4_test_lint_B1files.json, out/order3_v4_compare.json",
    },
    "base_reference_B1": {"command": pytest_cmd("C:/g412/isob", False) + "  (PYTHONHASHSEED=0)",
                          "result": ra["b1_tail"], "counts": ra["b1_counts"], "failed_ids": ra["b1_failed_ids"],
                          "ids_file": "out/order3_base_ids_B1.json"},
    "V3_test_only": {"command": cmd_v3, "output": v3, "expected_targets_empty": v3["targets"] == []},
    "stop_reasons": [],
    "end_checks": {"audit_wt_status_porcelain": status, "log_role_test_to_HEAD": log_after,
                   "log_empty": log_after.strip() == ""},
}
txt = json.dumps(out, ensure_ascii=False, indent=1)
# diff_hash·diff_paths 키는 V5 안에만
cnt_h = txt.count('"diff_hash"'); cnt_p = txt.count('"diff_paths"')
assert cnt_h == 1 and cnt_p == 1, (cnt_h, cnt_p)
open(D + "/base_check.json", "wb").write(txt.encode("utf-8"))
print("ok", len(new_rows), dict(reasons), assert_red_bad, repr(status), repr(log_after))
