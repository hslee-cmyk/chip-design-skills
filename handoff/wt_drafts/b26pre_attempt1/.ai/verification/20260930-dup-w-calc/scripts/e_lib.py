"""E-LIB (auditor 독립 작성, 2026-09-30 P6 순서 3).
<root>/skills/analog-gmid-design/assets/library/*.topology.json(_TEMPLATE 제외) 회로마다
  (a) stick_diagram.load_topology 결과, (b) run_topology_pipeline(V1: 소자마다 자기 스택 n_fingers=2·finger_w=1.0·w=2.0
  = test_ic3.py 3 구성, V2: 극성별 스택 stk_<kind>) 결과를 정규화해 sha256.
정규화: dataclass->dict, dict 키 정렬, set/frozenset 정렬 list, tuple->list, float repr, 복제본 루트 문자열 -> '<ROOT>'.
예외는 (타입 이름, 메시지(루트 치환) sha256)으로 넣는다. stick_diagram이 <root> 밖에서 import되면 중단.
사용: python -P e_lib.py <root> <out.json>"""
import dataclasses, enum, glob, hashlib, json, math, os, sys
root = os.path.abspath(sys.argv[1]); out = sys.argv[2]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, A)
import stick_diagram as sd
mf = os.path.normcase(os.path.abspath(sd.__file__))
if not mf.startswith(os.path.normcase(A)):
    sys.exit("stick_diagram imported outside root: %s" % mf)
roots = sorted({root, root.replace("\\", "/"), root.replace("/", "\\")}, key=len, reverse=True)
def rs(s):
    for r in roots:
        s = s.replace(r, "<ROOT>")
    return s
def norm(x, depth=0):
    if depth > 60:
        return "<DEPTH>"
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return {"__dc__": type(x).__name__, **{f.name: norm(getattr(x, f.name), depth + 1) for f in dataclasses.fields(x)}}
    if isinstance(x, dict):
        items = [(json.dumps(norm(k, depth + 1), sort_keys=True, ensure_ascii=False), norm(v, depth + 1)) for k, v in x.items()]
        return {"__dict__": sorted(items, key=lambda kv: kv[0])}
    if isinstance(x, (set, frozenset)):
        return {"__set__": sorted((norm(v, depth + 1) for v in x), key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))}
    if isinstance(x, (list, tuple)):
        return [norm(v, depth + 1) for v in x]
    if isinstance(x, bool) or x is None or isinstance(x, int):
        return x
    if isinstance(x, float):
        return {"__f__": repr(x)}
    if isinstance(x, str):
        return rs(x)
    if isinstance(x, enum.Enum):
        return {"__enum__": repr(x)}
    if hasattr(x, "tolist"):
        return {"__np__": norm(x.tolist(), depth + 1)}
    if hasattr(x, "__dict__"):
        return {"__obj__": type(x).__name__, **{k: norm(v, depth + 1) for k, v in sorted(vars(x).items())}}
    return {"__repr__": rs(repr(x))}
def h(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
def guarded(fn):
    try:
        return {"ok": True, "value": norm(fn())}
    except Exception as e:
        return {"ok": False, "exc": type(e).__name__, "msg_sha256": hashlib.sha256(rs(str(e)).encode("utf-8")).hexdigest()}
res = {"stick_diagram_file": rs(sd.__file__.replace("\\", "/")), "circuits": {}}
full = {}
for p in sorted(glob.glob(os.path.join(A, "library", "*.topology.json"))):
    name = os.path.basename(p)[:-len(".topology.json")]
    if name.startswith("_"):
        continue
    ent = {}
    lt = guarded(lambda: sd.load_topology(p))
    ent["load"] = lt
    per = {"load": h(lt)}
    if lt["ok"]:
        ts, _meta = sd.load_topology(p)
        ent["n_dev"] = len(ts)
        v1 = {t.name: {"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": f"stack_{t.name}"} for t in ts}
        v2 = {t.name: {"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": f"stk_{t.kind}"} for t in ts}
        for tag, ov in (("V1_own_stack", v1), ("V2_kind_stack", v2)):
            r = guarded(lambda: sd.run_topology_pipeline(p, ov))
            ent[tag] = r
            per[tag] = h(r)
    full[name] = ent
    res["circuits"][name] = {"per_hash": per, "n_dev": ent.get("n_dev"),
                             "ok": {k: ent[k]["ok"] for k in ("load", "V1_own_stack", "V2_kind_stack") if k in ent},
                             "exc": {k: ent[k].get("exc") for k in ent if isinstance(ent[k], dict) and not ent[k].get("ok", True)}}
res["hash"] = h(full)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
print("E-LIB", res["hash"])
for k, v in res["circuits"].items():
    print(k, v["n_dev"], v["ok"], v["exc"])
