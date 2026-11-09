"""계약 7 기준값(auditor 독립 정규화, test 파일 정규화 함수를 쓰지 않음): analog-grammar 있음에서 진입점 14 x 9회로 반환을
정규화해 sha256으로 적는다. 순서 7에서 병합본에 같은 스크립트를 돌려 회로·진입점마다 같은지 본다.
정규화: Match류(kind·devices·ports·note·priority) -> 리스트, set/frozenset -> 원소 정규화 후 json 정렬 리스트,
tuple/list -> 리스트, dict -> 키 문자열화+정렬(비문자열 키는 [키,값] 쌍 정렬), float -> repr, dataclass/객체 -> 형 이름+필드.
사용: python -P c7_digest.py <복제본 루트> <out.json>"""
import dataclasses, glob, hashlib, json, os, sys
root, out = sys.argv[1:3]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, A)
import stick_diagram as sd


def norm(x):
    if x is None or isinstance(x, (bool, int, str)):
        return x
    if isinstance(x, float):
        return ["f", repr(x)]
    if not isinstance(x, dict) and all(hasattr(x, a) for a in ("kind", "devices", "ports", "note", "priority")):
        return ["M", norm(x.kind), norm(list(x.devices)), norm(sorted(x.ports.items())), norm(x.note), norm(x.priority)]
    if isinstance(x, dict):
        items = [[norm(k), norm(v)] for k, v in x.items()]
        return ["D", sorted(items, key=lambda kv: json.dumps(kv, sort_keys=True))]
    if isinstance(x, (set, frozenset)):
        return ["S", sorted((norm(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))]
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if dataclasses.is_dataclass(x):
        return ["C", type(x).__name__, [[f.name, norm(getattr(x, f.name))] for f in dataclasses.fields(x)]]
    if hasattr(x, "__dict__"):
        return ["O", type(x).__name__, norm(vars(x))]
    return ["R", repr(x)]


def ov(ts):
    return {t.name: {"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": "stack_" + t.name} for t in ts}


ENTRIES = [
    ("load_topology", lambda p, ts: sd.load_topology(p)),
    ("run_topology_pipeline", lambda p, ts: sd.run_topology_pipeline(p, ov(ts))),
    ("find_stack_edges", lambda p, ts: sd.find_stack_edges(ts)),
    ("find_idiom_matches", lambda p, ts: sd.find_idiom_matches(ts)),
    ("find_differential_and_mirror_forks", lambda p, ts: sd.find_differential_and_mirror_forks(ts)),
    ("suggest_vertical_stack_composites", lambda p, ts: sd.suggest_vertical_stack_composites(ts)),
    ("find_differential_pair_candidates", lambda p, ts: sd.find_differential_pair_candidates(ts)),
    ("find_verified_differential_and_mirror_relations", lambda p, ts: sd.find_verified_differential_and_mirror_relations(ts)),
    ("refine_differential_and_mirror_relations", lambda p, ts: sd.refine_differential_and_mirror_relations(ts)),
    ("audit_theta_root_direction", lambda p, ts: sd.audit_theta_root_direction(ts, None)),
    ("propose_theta_kcl_gap_fill", lambda p, ts: sd.propose_theta_kcl_gap_fill(ts, [])),
    ("propose_device_roles_gap_fill", lambda p, ts: sd.propose_device_roles_gap_fill(ts, {}, [])),
    ("geometry_colocation_union", lambda p, ts: sd.geometry_colocation_union(ts, [])),
    ("propose_vertical_stack_id_gap_fill", lambda p, ts: sd.propose_vertical_stack_id_gap_fill(ts, [], {}, inputs=("vinp",))),
]
paths = sorted(p for p in glob.glob(os.path.join(A, "library", "*.topology.json")) if not os.path.basename(p).startswith("_"))
res = {"seed": os.environ.get("PYTHONHASHSEED"), "digests": {}}
for p in paths:
    ts, _ = sd.load_topology(p)
    c = os.path.basename(p).split(".")[0]
    res["digests"][c] = {}
    for name, f in ENTRIES:
        try:
            v = norm(f(p, ts))
            s = json.dumps(v, sort_keys=True, ensure_ascii=False)
            res["digests"][c][name] = hashlib.sha256(s.encode("utf-8")).hexdigest()
        except Exception as e:  # noqa: BLE001 -- 측정: 예외도 값으로 적는다
            res["digests"][c][name] = "EXC %s: %s" % (type(e).__name__, str(e)[:200])
allh = hashlib.sha256(json.dumps(res["digests"], sort_keys=True).encode()).hexdigest()
res["combined"] = allh
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n = sum(len(v) for v in res["digests"].values())
nexc = sum(1 for v in res["digests"].values() for h in v.values() if h.startswith("EXC"))
print("entries", n, "exceptions", nexc, "combined", allh)
