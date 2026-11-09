"""B37a 동작 보존 측정(E-LIB·E3·offset·audit·SPECS 평가) -- 사본 하나에서 실행, 결과를 JSON에 쓴다.
사용: python -B measure.py <사본 루트> <out.json> [--specs]
"""
import dataclasses, glob, hashlib, inspect, json, os, sys

ROOT = sys.argv[1]
OUT = sys.argv[2]
SPECS = "--specs" in sys.argv
ASSETS = os.path.join(ROOT, "skills/analog-gmid-design/assets")
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ROOT, "workspaces"))
import stick_diagram as SD  # noqa: E402
import sizing_recipe as SR  # noqa: E402
assert os.path.abspath(SD.__file__).replace("\\", "/").startswith(os.path.abspath(ROOT).replace("\\", "/")), SD.__file__
assert os.path.abspath(SR.__file__).replace("\\", "/").startswith(os.path.abspath(ROOT).replace("\\", "/")), SR.__file__
LIB = os.path.join(ASSETS, "library")


def norm(x):
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return {"__dc__": type(x).__name__, **{f.name: norm(getattr(x, f.name)) for f in dataclasses.fields(x)}}
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (set, frozenset)):
        return sorted((norm(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True, default=str))
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if isinstance(x, float):
        return float.hex(x)
    return x


HAS_PORTS = "ports" in inspect.signature(SR.resolve_stack_layout).parameters
res = {"has_ports_kw": HAS_PORTS, "circuits": {}}
for p in sorted(glob.glob(os.path.join(LIB, "*.topology.json"))):
    name = os.path.basename(p).replace(".topology.json", "")
    if name.startswith("_"):
        continue
    r = {}
    trs, meta = SD.load_topology(p)
    r["transistors"] = norm(trs)
    r["meta"] = norm({k: v for k, v in meta.items() if k != "ports"})
    r["ports"] = norm(meta.get("ports"))
    pairs = [tuple(x["names"]) for x in meta["symmetry"]["matching_pairs"] if x.get("current_forced")]
    droles = {k: v for k, v in (meta.get("device_roles") or {}).items() if not k.startswith("_")}
    declared = any(isinstance(v, dict) and v.get("vertical_stack_id") for v in droles.values())
    try:
        if HAS_PORTS:
            g = SR.resolve_stack_layout(trs, pairs, droles, ports=meta["ports"])
        else:
            g = SR.resolve_stack_layout(trs, pairs, droles)
        r["e3"] = {"declared_vsid": declared, "groups": sorted(sorted(v) for v in g.values())}
    except Exception as e:  # 관찰 기록용
        r["e3"] = {"declared_vsid": declared, "exc": "%s: %s" % (type(e).__name__, str(e)[:200])}
    try:
        r["offset_pairs"] = SR.input_referred_offset_pairs(p)
    except Exception as e:
        r["offset_pairs"] = "%s: %s" % (type(e).__name__, str(e)[:200])
    try:
        a = SD.run_full_circuit_audit_from_topology(p)
        r["audit"] = norm(a)
    except Exception as e:
        r["audit"] = "%s: %s" % (type(e).__name__, str(e).replace(p, "<P>").replace(p.replace("/", "\\"), "<P>")[:300])
    res["circuits"][name] = r

if SPECS:
    sys.path.insert(0, os.path.join(ASSETS, "tests", "unit"))
    import _library_sized_contexts as L  # noqa: E402
    assert os.path.abspath(L.__file__).replace("\\", "/").startswith(os.path.abspath(ROOT).replace("\\", "/"))
    import time
    res["specs"] = {}
    for key, cfg in L.H.SPECS.items():
        t0 = time.time()
        sc = L._evaluate_once(key, cfg)
        d = {"sec": round(time.time() - t0, 1)}
        if sc.refusal is not None:
            d["error"] = "%s: %s" % (type(sc.refusal).__name__, str(sc.refusal)[:300])
        else:
            d["metrics"] = {k: (float.hex(v) if isinstance(v, float) else repr(v)) for k, v in sorted(sc.metrics.items())}
            d["sized_hash"] = hashlib.sha256(json.dumps(norm(sc.ctx.sized), sort_keys=True, default=str).encode()).hexdigest()[:16]
        res["specs"][key] = d

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1, default=str)
print("wrote", OUT)
