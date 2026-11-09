"""measure only: compare PT3 junit of base vs head under the T1 id map (old file path -> new file path per test).
    python -B junit_cmp.py <base.junit.xml> <head.junit.xml> <t1_gen report.json> <out.json>"""
import collections
import json
import sys
import xml.etree.ElementTree as ET

bj, hj, rep, out = sys.argv[1:5]
idmap = json.load(open(rep, encoding="utf-8"))["id_map"]   # unit/test_selftest_x.py::name -> unit/test_modk_y.py::name
fmap = {}
for o, n in idmap.items():
    fmap[o] = n


def load(p):
    res = {}
    for tc in ET.parse(p).getroot().iter("testcase"):
        cls, name = tc.get("classname", ""), tc.get("name", "")
        st = "passed"
        for ch in tc:
            if ch.tag in ("failure", "error"):
                st = ch.tag
            elif ch.tag == "skipped":
                st = "xfailed" if "xfail" in (ch.get("type", "") + ch.get("message", "")) else "skipped"
        res[(cls, name)] = st
    return res


def norm_unit(cls):
    # junit classname like skills.analog-gmid-design.assets.tests.unit.test_selftest_x
    i = cls.find("tests.unit.")
    return cls[i + len("tests."):].replace(".", "/") + ".py" if i >= 0 else None


B, H = load(bj), load(hj)
moved = {}
for (cls, name), st in B.items():
    u = norm_unit(cls)
    base_fn = name.split("[", 1)[0]
    if u and ("%s::%s" % (u, base_fn)) in idmap:
        nu = idmap["%s::%s" % (u, base_fn)].split("::")[0]
        ncls = cls[: cls.find("tests.unit.")] + "tests." + nu[:-3].replace("/", ".")
        moved[(ncls, name)] = st
    else:
        moved[(cls, name)] = st
only_b = sorted("%s::%s" % k for k in set(moved) - set(H))
only_h = sorted("%s::%s" % k for k in set(H) - set(moved))
diff = sorted("%s::%s %s->%s" % (k[0], k[1], moved[k], H[k]) for k in set(moved) & set(H) if moved[k] != H[k])
r = {"n_base": len(B), "n_head": len(H), "n_moved_ids": sum(1 for (c, n) in B if norm_unit(c) and "test_selftest_" in c),
     "only_base_mapped": only_b, "only_head": only_h, "result_diff": diff,
     "base_counts": dict(collections.Counter(B.values())), "head_counts": dict(collections.Counter(H.values()))}
json.dump(r, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in r.items()}, ensure_ascii=False))
