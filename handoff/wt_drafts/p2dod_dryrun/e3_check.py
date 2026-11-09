"""Dry-run E3 checker (brief section 4 E3 items 1-6). Usage: e3_check.py <iso> <rev> <out.json> [H]
Reads the inventory via `git -C <iso> show <rev>:<path>`. Item 6 needs H (engine compare); omitted -> N/A.
"""
import collections, json, re, subprocess, sys

ISO, REV, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
H = sys.argv[4] if len(sys.argv) > 4 else None
INV = "docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json"
PLAN = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"


def git(*a, check=False):
    return subprocess.run(["git", "-C", ISO, *a], capture_output=True, check=check)


res = {"rev": REV, "checks": {}}
c1 = git("cat-file", "-e", "%s:%s" % (REV, INV)).returncode
res["checks"]["1_cat_file"] = {"exit": c1, "ok": c1 == 0}
d = json.loads(git("show", "%s:%s" % (REV, INV), check=True).stdout.decode("utf-8")) if c1 == 0 else {}
items = d.get("items", []) if isinstance(d, dict) else d
tot = d.get("totals", {}) if isinstance(d, dict) else {}
by_phase = dict(collections.Counter(i.get("phase") for i in items if "phase" in i))
by_role = dict(collections.Counter(i.get("role") for i in items))
res["checks"]["2_totals"] = {
    "n_items": len(items), "totals_n_items": tot.get("n_items"),
    "by_phase_eq": tot.get("by_phase") == by_phase, "by_role_eq": tot.get("by_role") == by_role,
    "ok": bool(tot) and len(items) == tot.get("n_items") and tot.get("by_phase") == by_phase and tot.get("by_role") == by_role,
}

# closed set from plan N6.1 table (Phase column after '2'), read at REV
plan = git("show", "%s:%s" % (REV, PLAN), check=True).stdout.decode("utf-8")
sec = plan.split("### N6.1", 1)[1].split("### N6.2", 1)[0]
names = []
for ln in sec.splitlines():
    m = re.match(r"^\|\s*\**([0-9][0-9a-z.()문서]*)\**\s*\|", ln)
    if m:
        names.append(m.group(1))
after2 = names[names.index("2") + 1:] if "2" in names else []
closed = set(after2) | {"해당 없음"}
with_phase = [i for i in items if "phase" in i]
bad = [i.get("phase") for i in with_phase if i.get("phase") not in closed]
ps = d.get("phase_source", {}) if isinstance(d, dict) else {}
res["checks"]["3_phase"] = {
    "n6_1_names": names, "closed_set": sorted(closed), "with_phase": len(with_phase), "n": len(items),
    "bad_values": sorted(set(map(str, bad))),
    "phase_source_closed_set": ps.get("closed_set"),
    "closed_set_matches_list": (sorted(ps.get("closed_set") or []) == sorted(closed)) if ps.get("closed_set") is not None else None,
    "ok": len(items) > 0 and len(with_phase) == len(items) and not bad,
}
res["checks"]["4_function"] = {"empty": sum(1 for i in items if not str(i.get("function") or "").strip()),
                               "ok": len(items) > 0 and all(str(i.get("function") or "").strip() for i in items)}
cnt = collections.Counter()
labels = collections.defaultdict(collections.Counter)
for i in items:
    m = re.match(r"^DF-(\d+)", str(i.get("plan_mapping") or ""))
    if m and i.get("role") == "동작을 정함":
        cnt[int(m.group(1))] += 1
        labels[int(m.group(1))][i.get("plan_mapping")] += 1
res["checks"]["5_df29_34"] = {"counts": {k: cnt.get(k, 0) for k in range(29, 35)},
                              "labels": {k: dict(v) for k, v in labels.items() if 29 <= k <= 34},
                              "ok": all(cnt.get(k, 0) >= 1 for k in range(30, 35))}
if H:
    ma = d.get("measured_at")
    sf = d.get("scope_files") or []
    diffq = git("diff", "--quiet", str(ma), H, "--", *sf).returncode if ma and sf else None
    tree = git("ls-tree", "--name-only", H, "skills/analog-gmid-design/assets/").stdout.decode().split()
    top = sorted(p for p in tree if p.endswith(".py")) + ["workspaces/run_harness.py"]
    res["checks"]["6_engine"] = {"measured_at": ma, "diff_quiet_exit": diffq, "scope_files_eq": sorted(sf) == sorted(top),
                                 "expected_scope": top, "ok": diffq == 0 and sorted(sf) == sorted(top)}
else:
    res["checks"]["6_engine"] = {"ok": None, "note": "N/A (no H)", "measured_at": d.get("measured_at") if isinstance(d, dict) else None}
res["verdict"] = "PASS" if all(v["ok"] for v in res["checks"].values() if v["ok"] is not None) else "FAIL"
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(res["verdict"])
