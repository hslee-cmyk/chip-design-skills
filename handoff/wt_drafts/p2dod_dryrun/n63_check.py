"""Dry-run N6.3 checks 1-5 (brief section 6). Usage: n63_check.py <iso> <H> <out.json>
Read-only: git show/log/merge-base only, working tree not touched.
nomerge(2026-10-06 user-approved): section 4 git log has no --no-merges. Default history simplification drops merges
TREESAME to one parent; a remaining merge is rebuilt with `git merge-tree --write-tree` (both parents) -- same content on
the pathspec = 'clean' (normal --no-ff gate merge, skipped, listed in merges_clean), different = 'evil' (merge-only
content, conflict resolution included, >2 parents included) = always bad. merge-tree objects go to a temp object dir
(GIT_OBJECT_DIRECTORY + alternates): the clone's object contents and object count are unchanged, but git may refresh
(freshen) the mtime of loose objects that already exist in the clone when merge-tree would write them again.
The temp object dir is a tempfile.TemporaryDirectory (cleanup also removes git's read-only loose objects on Windows)."""
import atexit, collections, json, os, re, subprocess, sys, tempfile

ISO, H, OUT = sys.argv[1:4]


def git(*a, env=None):
    p = subprocess.run(["git", "-C", ISO, *a], capture_output=True, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace")


_OBJTMP = tempfile.TemporaryDirectory(prefix="n63_objs_")   # m1: shutil.rmtree(..., True) left read-only loose objects behind on Windows
atexit.register(_OBJTMP.cleanup)
_OBJDIR = _OBJTMP.name
_MENV = dict(os.environ, GIT_OBJECT_DIRECTORY=_OBJDIR,
             GIT_ALTERNATE_OBJECT_DIRECTORIES=git("rev-parse", "--path-format=absolute", "--git-path", "objects")[1].strip())


def merge_class(c, paths):
    """(None, []) non-merge | ('clean', []) auto-merge equal on paths | ('evil', paths differing)."""
    par = git("show", "-s", "--format=%P", c)[1].split()
    if len(par) < 2:
        return None, []
    if len(par) > 2:
        return "evil", ["(%d parents)" % len(par)]
    rc, mt = git("merge-tree", "--write-tree", "--no-messages", par[0], par[1], env=_MENV)
    if rc not in (0, 1) or not mt.split():
        return "evil", ["(merge-tree failed rc=%d)" % rc]
    d = git("diff", "--name-only", mt.split()[0], c, "--", *paths, env=_MENV)[1].split()
    return ("evil", d + (["(conflicted merge)"] if rc == 1 else [])) if d else ("clean", [])


def anc(c):
    return bool(c) and git("merge-base", "--is-ancestor", c, H)[0] == 0


res = {"H": H}
_, ls = git("ls-tree", "--name-only", H, ".ai/verification/")
recs = sorted(p for p in ls.split() if p.endswith(".json") and not p.endswith("_schema.json"))
allv = {}
for p in recs:
    d = json.loads(git("show", "%s:%s" % (H, p))[1])
    allv[d["id"]] = {"evidence_type": d.get("evidence_type"),
                     "V": {k: d["checks"].get(k, {}).get("verdict") for k in ["V%d" % i for i in range(1, 11)]},
                     "base": d.get("base_commit"), "test": d.get("test_commit"), "code": d.get("code_commit"),
                     "red": d.get("red"), "equivalence": d.get("equivalence")}
bad1 = {i: v["V"] for i, v in allv.items() if any(x not in ("PASS", "N/A") for x in v["V"].values())}
res["1_all_records"] = {"n": len(allv), "bad": bad1, "ok": not bad1}

_, cards = git("grep", "-l", "-E", "^phase: 2$", H, "--", "docs/02-design/specs")
ids2 = sorted(re.sub(r"^.*/(.*)\.spec\.md$", r"\1", c) for c in cards.split())
EXPECT16 = ["20260923-probe-dead-delete", "20260923-probe-relocate", "20260923-probe-promote-clean",
            "20260923-probe-promote-differential", "20260929-probe-engine-dup", "20260923-d-delete-dead",
            "20260923-d-delete-telescopic", "20260930-d-move-tests", "20260930-registry-grade-fix",
            "20260930-dup-w-calc", "20260930-p9-kcl-edges", "20260930-p10-df23-inventory",
            "20260930-df23-registry-record", "20260930-restore-plan-functions", "20260930-df35-harness-paths",
            "20260930-df36-instance-relpath"]
with_rec = [i for i in ids2 if i in allv]
without = [i for i in ids2 if i not in allv]
res["2_phase2"] = {"n_cards": len(ids2), "with_record": len(with_rec), "without_record": without,
                   "expected_missing": [i for i in EXPECT16 if i not in allv],
                   "unexpected_cards": [i for i in ids2 if i not in EXPECT16 and i != "20260923-probe-promote-consistency"],
                   "ok": len(with_rec) == 16 and without == ["20260923-probe-promote-consistency"]}
rows = []
_, merges = git("log", "--merges", "--format=%H%x09%s", H)
mtitle = {}
for ln in merges.splitlines():
    h, s = ln.split("\t", 1)
    m = re.match(r"^merge (\S+)", s)
    if m:
        mtitle.setdefault(m.group(1), []).append(h)
for i in EXPECT16:
    if i not in allv:
        rows.append({"id": i, "missing": True}); continue
    v = allv[i]
    _, ac = git("log", "-1", "--format=%H", H, "--", ".ai/verification/%s.json" % i)
    ac = ac.strip()
    _, tr = git("show", "-s", "--format=%(trailers:only,unfold)", ac)
    role_ok = "Role: audit" in tr and ("Change-Id: %s" % i) in tr
    mc = mtitle.get(i, [])
    rows.append({"id": i, "evidence_type": v["evidence_type"], "V": "".join("P" if x == "PASS" else ("-" if x == "N/A" else "X") for x in v["V"].values()),
                 "audit_commit": ac[:7], "audit_trailers_ok": role_ok and anc(ac), "merge_commits": [m[:7] for m in mc],
                 "merge_ok": (bool(mc) and all(anc(m) for m in mc)) if v["evidence_type"] != "test-only" else (not mc and v["code"] is None),
                 "base_test_code_anc": all(anc(c) for c in (v["base"], v["test"], v["code"]) if c),
                 "red_present": bool(v["red"]), "equivalence_present": bool(v["equivalence"])})
res["3_rows"] = rows
res["3_ok"] = all(r.get("audit_trailers_ok") and r.get("merge_ok") and r.get("base_test_code_anc") for r in rows if not r.get("missing"))
ENG = ["skills/analog-gmid-design/assets/*.py", "workspaces/run_harness.py", "skills/analog-gmid-design/assets/library/*.json"]
_, cs_all = git("log", "--format=%H", "da03c0e..%s" % H, "--", *ENG)   # no --no-merges (nomerge, see docstring)
cs = []; merges_clean = []
for c in cs_all.split():
    k, dp = merge_class(c, ENG)
    if k == "clean":
        merges_clean.append(c[:7])
    else:
        cs.append((c, k, dp))
per = collections.Counter(); badc = []
for c, k, dp in cs:
    _, tr = git("show", "-s", "--format=%(trailers:only,unfold)", c)
    role = re.search(r"^Role: (\S+)", tr, re.M); cid = re.search(r"^Change-Id: (\S+)", tr, re.M)
    if not k and role and role.group(1) in ("code", "test") and cid and cid.group(1) in EXPECT16:   # evil merge = always bad
        per[cid.group(1)] += 1
    else:
        badc.append({"c": c[:7], "role": role and role.group(1), "cid": cid and cid.group(1),
                     **({"merge": k, "merge_only_paths": dp} if k else {})})
res["4_engine_commits"] = {"n": len(cs), "merges_clean": merges_clean, "per_card": dict(per), "bad": badc, "ok": not badc}
res["0.5_cards"] = {i: allv[i]["V"] for i in ("20260930-v3-history-clone", "20260929-rejudge-cache") if i in allv}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("1", res["1_all_records"]["ok"], res["1_all_records"]["n"], "| 2", res["2_phase2"]["ok"], "| 3", res["3_ok"], "| 4", res["4_engine_commits"]["ok"], res["4_engine_commits"]["n"])
