"""Summarise run_by_file.py results.jsonl (latest record per file). usage: summarize.py <out dir> [<compare out dir>]"""
import json
import sys
from pathlib import Path


def latest(out):
    rows = {}
    for line in (Path(out) / "results.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            rows[record["file"]] = record
    return rows


def bad_ids(rows):
    return {i for r in rows.values() for i in r.get("failed_ids", []) + r.get("error_ids", [])}


rows = latest(sys.argv[1])
total = {k: sum(r.get(k, 0) for r in rows.values()) for k in ("tests", "failures", "errors", "skipped")}
print("files", len(rows), total, "sec", sum(r["sec"] for r in rows.values()),
      "min_free_mb", min(r["min_free_mb"] for r in rows.values() if r["min_free_mb"] is not None))
print("not done", [(f, r["status"]) for f, r in rows.items() if r["status"] != "done"])
print("rc not in 0,1", [(f, r["rc"]) for f, r in rows.items() if r["rc"] not in (0, 1)])
print("zero tests", [f for f, r in rows.items() if r.get("tests", 0) == 0])
for f, r in rows.items():
    if r.get("failures") or r.get("errors"):
        print("FILE", f, "F", r.get("failures"), "E", r.get("errors"))
if len(sys.argv) > 2:
    base = latest(sys.argv[2])
    print("base files", len(base), "not done", [(f, r["status"]) for f, r in base.items() if r["status"] != "done"])
    print("base rc not in 0,1", [(f, r["rc"]) for f, r in base.items() if r["rc"] not in (0, 1)])
    print("base counts", {k: sum(r.get(k, 0) for r in base.values()) for k in ("tests", "failures", "errors", "skipped")})
    merged_bad, base_bad = bad_ids(rows), bad_ids(base)
    print("merged bad", len(merged_bad), "base bad", len(base_bad))
    print("== merged only")
    for i in sorted(merged_bad - base_bad):
        print(" ", i)
    print("== both")
    for i in sorted(merged_bad & base_bad):
        print(" ", i)
    print("== base only")
    for i in sorted(base_bad - merged_bad):
        print(" ", i)
else:
    for i in sorted(bad_ids(rows)):
        print(" ", i)
