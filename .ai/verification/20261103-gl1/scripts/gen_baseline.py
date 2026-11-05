"""usage: python -I gen_baseline.py <clone root> <base sha> <out bytes file> <out summary json>"""
import sys, json, hashlib, collections
from pathlib import Path
root, base, out, summ = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
S = root / "skills/analog-gmid-design/gmid_engine/tests/structure"
E = root / "skills/analog-gmid-design/gmid_engine"
sys.dont_write_bytecode = True
sys.path.insert(0, str(S))
import structure_checks as c
n8, v8 = c.check_g8(E)
nv, vv = c.check_value_types(E)
viol = list(v8) + list(vv)
doc = c.baseline_doc(viol, "20261103-gl1-baseline", base)
raw = c.dump_baseline(doc)
out.write_bytes(raw)
loaded = c.load_baseline(out)
r = c.ratchet(viol, loaded)
rows = collections.Counter(x["kind"] for x in doc["rows"])
cnt = collections.Counter()
for x in doc["rows"]:
    cnt[x["kind"]] += x["count"]
vk = collections.Counter(v.kind for v in viol)
assert dict(cnt) == dict(vk)
Path(summ).write_text(json.dumps({"n_targets_g8": n8, "n_targets_vt": nv, "n_viol_g8": len(v8), "n_viol_vt": len(vv),
    "rows_by_kind": dict(sorted(rows.items())), "viol_by_kind": dict(sorted(vk.items())), "n_rows": len(doc["rows"]),
    "new": len(r.new), "stale": len(r.stale), "sha256": hashlib.sha256(raw).hexdigest()}, ensure_ascii=False, indent=1), encoding="utf-8")
with open(str(summ) + ".viol.tsv", "w", encoding="utf-8", newline="\n") as f:
    for v in sorted(viol):
        f.write("%s\t%s\t%d\t%s\n" % (v.kind, v.path, v.line, v.detail))
