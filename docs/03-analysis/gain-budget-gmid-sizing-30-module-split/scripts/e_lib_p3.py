"""E-LIB for Phase 3 DoD E5 (design 30-module-split §10 E5, 초안 v8.2 -- UD-0 (c) 선례 모양).

e_lib.py(.ai/verification/20260930-df36-instance-relpath/scripts/, design 20 §10 E4 정본)와 **한 곳만** 다르다:
인자 `<root> <out.json>` 뒤에 meta 키 이름을 0개 이상 받는다(MASK). 회로마다 `load` 값(= `stick_diagram.load_topology` 반환
(transistors, meta))을 정규화하기 전에 meta에서 MASK 키를 빼고, 뺀 키의 값은 정규화해 `circuits.<회로>.masked.<키>`에 따로 싣는다
(키가 없으면 "<ABSENT>"). `hash`·`per_hash`는 뺀 뒤의 값으로 계산한다. 이유: Phase 2 DoD 대상 커밋과 Phase 3 마지막 병합본 사이 card가
의도적으로 더한 meta 키(B26-1 계약 2·8 `meta["rails"]`)를 해시에서 빼고 그 card 계약값으로 따로 판정한다(선례 승인 20260930-phase2-e4-baseline의
`topology_ref` 처리와 같은 모양). 출력에 `masked_meta_keys`(최상위)와 `circuits.<회로>.masked`(회로마다) 두 키가 더해진다.
MASK가 비었거나 MASK 키가 어느 meta에도 없으면 `hash`·`per_hash`와 그 밖 출력이 e_lib.py와 같아야 한다(E5 '동등 확인').
나머지(정규화, 예외 처리, V1·V2 구성, 출력 순서)는 e_lib.py 그대로다.
사용: python -P e_lib_p3.py <root> <out.json> [MASK_KEY ...]"""
import dataclasses, enum, glob, hashlib, json, math, os, sys
root = os.path.abspath(sys.argv[1]); out = sys.argv[2]; MASK = sorted(set(sys.argv[3:]))
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
res = {"stick_diagram_file": rs(sd.__file__.replace("\\", "/")), "circuits": {}, "masked_meta_keys": MASK}
full = {}
for p in sorted(glob.glob(os.path.join(A, "library", "*.topology.json"))):
    name = os.path.basename(p)[:-len(".topology.json")]
    if name.startswith("_"):
        continue
    ent = {}
    mk = {}
    def masked_load():
        ts_, meta_ = sd.load_topology(p)
        for k in MASK:
            mk[k] = norm(meta_[k]) if k in meta_ else "<ABSENT>"
        return ts_, {k: v for k, v in meta_.items() if k not in MASK}
    lt = guarded(masked_load)
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
                             "exc": {k: ent[k].get("exc") for k in ent if isinstance(ent[k], dict) and not ent[k].get("ok", True)},
                             "masked": mk}
res["hash"] = h(full)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
print("E-LIB", res["hash"])
for k, v in res["circuits"].items():
    print(k, v["n_dev"], v["ok"], v["exc"])
