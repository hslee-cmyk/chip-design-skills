"""B2 측정 비교: <jsonl>의 기준 레코드(label) 대비 다른 레코드의 sized(소자별 vgs·vds·vsb·gm_id·W 등)·metrics 차이.
사용: python -B b2_compare.py <jsonl> <base_label> [out_json]
"""
import json
import sys

rs = {}
for line in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(line)
    rs[r["label"]] = r
base = rs[sys.argv[2]]
KEYS = ("vgs", "vds", "vsb", "gm_id", "W", "L", "ID", "gm", "gds")
summary = {}


def f(h):
    return float.fromhex(h) if isinstance(h, str) else h


for lab, r in rs.items():
    if lab == base["label"] or r["outcome"] != "ok":
        continue
    s = {"theta_same": r.get("theta_star") == base.get("theta_star"), "metric_diff": {}, "device_diff": {}}
    for k, v in (base.get("metrics") or {}).items():
        w = (r.get("metrics") or {}).get(k)
        if w != v:
            s["metric_diff"][k] = [f(v), f(w)]
    bs, hs = base.get("sized") or {}, r.get("sized") or {}
    for d in sorted(set(bs) | set(hs)):
        for k in KEYS:
            a, b = (bs.get(d) or {}).get(k), (hs.get(d) or {}).get(k)
            if a != b:
                s["device_diff"].setdefault(d, {})[k] = [f(a), f(b), (f(b) - f(a)) if a and b else None]
    s["n_devices_diff"] = len(s["device_diff"])
    summary[lab] = s
    print(f"== {lab}: theta_same={s['theta_same']} metric_diff={len(s['metric_diff'])} devices_diff={s['n_devices_diff']}")
    for k, v in s["metric_diff"].items():
        print(f"   metric {k}: {v[0]!r} -> {v[1]!r}")
    for d, kv in list(s["device_diff"].items())[:20]:
        print(f"   {d}: " + ", ".join(f"{k} {a!r}->{b!r}" for k, (a, b, _) in kv.items()))
if len(sys.argv) > 3:
    json.dump(summary, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
