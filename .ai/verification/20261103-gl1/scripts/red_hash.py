"""Red table from junit at base+T (tree ccbb0dc2). usage: python -I red_hash.py <R.xml> <H.xml> <out json>
Node id is rebuilt from classname (dotted file path) + name. Exception type is read from the junit message."""
import hashlib, json, re, sys, collections
import xml.etree.ElementTree as ET

NEW = ("test_g8_baseline", "test_g8_lint", "test_scan_shared_calls_tool", "test_value_types_lint")
S = "skills/analog-gmid-design/gmid_engine/tests/structure/"


def load(p):
    r = {}
    for tc in ET.parse(p).getroot().iter("testcase"):
        cn = tc.get("classname")
        mod = cn.split(".")[-1]
        st, msg = "passed", ""
        for ch in tc:
            if ch.tag in ("failure", "error", "skipped"):
                st = ch.tag
                msg = (ch.get("message") or "") + "\n" + (ch.text or "")
        r[(mod, tc.get("name"))] = (st, msg)
    return r


R, H = load(sys.argv[1]), load(sys.argv[2])
rows, ids, hashes = [], [], []
causes = collections.Counter()
for (mod, name), (st, msg) in sorted(R.items()):
    if mod not in NEW:
        continue
    m = re.search(r"AttributeError: .*has no attribute '(\w+)'", msg)
    if m:
        exc, cause = "builtins.AttributeError", "AttributeError:" + m.group(1)
    elif st != "passed" and ("assert" in msg.lower() or "AssertionError" in msg):
        exc, cause = "builtins.AssertionError", "AssertionError:" + ("tool_missing" if "scan_shared_calls" in msg else msg[:80])
    elif st == "passed":
        exc, cause = None, "PASSED_AT_BASE"
    else:
        exc, cause = "OTHER", msg[:200]
    causes[(st, cause)] += 1
    node = "%s%s.py::%s" % (S, mod, name)
    if exc and exc != "OTHER":
        ids.append(node)
        hashes.append(hashlib.sha256(("%s\n%s" % (node, exc)).encode("utf-8")).hexdigest())
    rows.append({"id": node, "state_base": st, "exc": exc, "state_head": H.get((mod, name), ("MISSING",))[0]})
old = {k: v for k, v in R.items() if k[0] not in NEW}
old_h = {k: H.get(k, ("MISSING",))[0] for k in old}
changed = [list(k) for k, v in old.items() if v[0] != old_h[k]]
d = {"n_new_at_base": len(rows), "n_red": len(ids), "n_old": len(old), "old_changed": changed,
     "old_failed_at_base": [list(k) for k, v in old.items() if v[0] != "passed"],
     "causes": {"%s|%s" % k: v for k, v in sorted(causes.items())},
     "head_counts": dict(collections.Counter(v[0] for v in H.values())), "head_new_not_passed": [r["id"] for r in rows if r["state_head"] != "passed"],
     "test_ids": ids, "failure_hashes": hashes, "rows": rows}
open(sys.argv[3], "w", encoding="utf-8", newline="\n").write(json.dumps(d, ensure_ascii=False, indent=1))
print({k: d[k] for k in ("n_new_at_base", "n_red", "n_old", "old_changed", "old_failed_at_base", "causes", "head_counts", "head_new_not_passed")})
