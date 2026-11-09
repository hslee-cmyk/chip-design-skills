"""[F1] 경로 재확인 답('gmid 폴더로 좁힘') 측정 전용: 좁힌 쓰기 경로 행의 해시·allowed·overlaps_any·덮는 추적 .py 수.

    python -B wp_narrow.py <gate 복제본 루트(4a286f0 체크아웃)> <F1 대상 목록 json(equiv_r1_f1.json)> <결과 json>
결과를 파일에 쓴다(stdout은 요약만).
"""
import json
import subprocess
import sys

ROOT, TJ, OUT = sys.argv[1:4]
sys.path.insert(0, ROOT + "/tools/gates")
import merge_gate as mg  # noqa: E402
import role_paths as rp  # noqa: E402

P = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
base = subprocess.run(["git", "-C", ROOT, "show", "4a286f0:" + P], capture_output=True, check=True).stdout.decode("utf-8")
ANCHOR = "| gmid-code-author | `workspaces/run_harness.py` | -- | 없음 |\n"
assert base.count(ANCHOR) == 1
targets = sorted(k for k in json.load(open(TJ, encoding="utf-8"))["files"] if k.startswith("workspaces/") and k != "workspaces/run_harness.py")
folders = sorted({t.rsplit("/", 1)[0] for t in targets})
depths = sorted({t.count("/") for t in targets})
# 가장 좁은 glob: 대상이 모두 폴더 바로 아래(깊이 2 = workspaces/<하위>/<파일>)면 `<폴더>/*.py`, 아니면 `<폴더>/**/*.py`
narrow = [f + ("/*.py" if all(t.rsplit("/", 1)[0] == f for t in targets if t.startswith(f + "/")) else "/**/*.py") for f in folders]
rows = "".join("| gmid-code-author | `%s` | -- | 없음 |\n" % g for g in narrow)
after = base.replace(ANCHOR, ANCHOR + rows)
wide = base.replace(ANCHOR, ANCHOR + "| gmid-code-author | `workspaces/*/**/*.py` | -- | 없음 |\n")
res = {"targets": targets, "folders": folders, "depths": depths, "narrow_globs": narrow, "rows_text": rows,
       "anchor_line": base.split("\n").index(ANCHOR.rstrip("\n")) + 1,
       "hash_before": mg.plan_tables_hash(base), "hash_after": mg.plan_tables_hash(after), "hash_wide": mg.plan_tables_hash(wide),
       "read_plan_tables_same": mg.read_plan_tables_text(after) == mg.read_plan_tables_text(base),
       "rows_before": len(rp.read_write_paths(base)), "rows_after": len(rp.read_write_paths(after))}
rb, ra, rw = rp.read_write_paths(base), rp.read_write_paths(after), rp.read_write_paths(wide)
tracked = subprocess.run(["git", "-C", ROOT, "ls-files", "workspaces"], capture_output=True, check=True).stdout.decode("utf-8").split("\n")
tracked_py = sorted(t for t in tracked if t.endswith(".py"))


def verdicts(rules, path):
    ctx = rp.WriteContext(rules=rules)
    return {a: rp.allowed(a, path, ctx).ok for a in rp.ACTORS}


def ov(rules, path):
    return rp.overlaps_any(path, rules)


cover_after = [t for t in tracked_py if any(rp.match_glob(g, t, None) for g in narrow)]
cover_wide = [t for t in tracked_py if rp.match_glob("workspaces/*/**/*.py", t, None)]
res["tracked_py_workspaces"] = len(tracked_py)
res["covered_after"] = cover_after
res["covered_after_n"] = len(cover_after)
res["covered_after_nontarget"] = [t for t in cover_after if t not in targets]
res["covered_wide_n"] = len(cover_wide)
res["freed_vs_wide"] = [t for t in cover_wide if t not in cover_after]
chk = {}
ok = True
for t in targets:
    v = verdicts(ra, t)
    good = v["gmid-code-author"] and not any(v[a] for a in rp.ACTORS if a != "gmid-code-author")
    chk[t] = v
    ok &= good and ov(ra, t) and not ov(rb, t)
res["targets_code_author_only_after"] = ok
# 좁힌 행 밖 workspaces 추적 .py: 개정 전과 같은 판정·같은 overlaps(= 사용자 쓰기 그대로)
same = []
diff = []
for t in tracked_py:
    if t in cover_after:
        continue
    a = (verdicts(ra, t), ov(ra, t))
    b = (verdicts(rb, t), ov(rb, t))
    (same if a == b else diff).append(t)
res["outside_unchanged_n"] = len(same)
res["outside_changed"] = diff
vrw = [t for t in tracked_py if t.startswith("workspaces/verilog-rtl-workspace/")]
res["verilog_rtl_py"] = {t: {"overlaps_before": ov(rb, t), "overlaps_after": ov(ra, t), "overlaps_wide": ov(rw, t)} for t in vrw}
probes = ["workspaces/run_harness.py", "workspaces/x.py", "workspaces/current-reuse-telescopic-ota-report/__init__.py",
          "workspaces/current-reuse-telescopic-ota-report/conftest.py", "workspaces/two-stage-ota-report/conftest.py",
          "workspaces/current-reuse-telescopic-ota-report/spice/x.py", "workspaces/current-reuse-telescopic-ota-report/a/b/__init__.py",
          "workspaces/two-stage-ota-report/sitecustomize.py", "workspaces/current-reuse-telescopic-ota-report/new_probe.py",
          "workspaces/folded-cascode-ota-report/x.py", "workspaces/verilog-rtl-workspace/desc-opt/gen_html.py",
          "workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py"]
res["probes"] = {p: {"before": verdicts(rb, p), "after": verdicts(ra, p), "ov_before": ov(rb, p), "ov_after": ov(ra, p),
                     "classify": rp.classify(p)} for p in probes}
res["per_target"] = chk
res["ALL_OK"] = bool(ok and not diff and res["read_plan_tables_same"] and res["hash_before"].startswith("7167e028")
                     and not any(v["overlaps_after"] for v in res["verilog_rtl_py"].values()))
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("folders", "depths", "narrow_globs", "anchor_line", "hash_before", "hash_after", "hash_wide",
                                      "rows_before", "rows_after", "tracked_py_workspaces", "covered_after_n", "covered_wide_n",
                                      "covered_after_nontarget", "outside_unchanged_n", "outside_changed",
                                      "targets_code_author_only_after", "ALL_OK")}, ensure_ascii=False, indent=1))
