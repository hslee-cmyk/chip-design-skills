"""판별력(브리프 3.1 끝): base 엔진(T 복제본 = base SD)에서 계약 1 판정기(pytest.raises(ImportError))가
14 진입점 x 9회로를 부재 세 모드(둘 다·idioms만·netclass만)에서 어떻게 잡는지 센다.
결과: DID_NOT_RAISE(조용히 반환 = 판정기가 실패로 잡음) / RAISED_IMPORT / OTHER(다른 예외).
부재는 모드마다 sys.modules에 None을 넣고 끝나면 되돌린다(test와 같은 방식). 입력 ts는 부재 전에 얻는다.
사용: python -P discrim_b34.py <복제본 루트> <out.json>"""
import collections, glob, json, os, sys
root, out = sys.argv[1:3]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, A)
import pytest
import stick_diagram as sd

paths = sorted(p for p in glob.glob(os.path.join(A, "library", "*.topology.json")) if not os.path.basename(p).startswith("_"))
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
MODES = {"both": ("netclass", "idioms"), "idioms_only": ("idioms",), "netclass_only": ("netclass",)}
res = {"n_paths": len(paths), "modes": {}}
for mode, names in MODES.items():
    cnt = collections.Counter()
    per_entry = collections.defaultdict(collections.Counter)
    others = []
    for p in paths:
        ts, _ = sd.load_topology(p)
        saved = {n: sys.modules.get(n, "<absent>") for n in names}
        for n in names:
            sys.modules[n] = None
        try:
            for name, f in ENTRIES:
                try:
                    with pytest.raises(ImportError):
                        f(p, ts)
                    r = "RAISED_IMPORT"
                except pytest.fail.Exception:
                    r = "DID_NOT_RAISE"
                except Exception as e:  # noqa: BLE001 -- 다른 예외 수를 세는 측정
                    r = "OTHER"
                    others.append([os.path.basename(p), name, "%s: %s" % (type(e).__name__, str(e)[:200])])
                cnt[r] += 1
                per_entry[name][r] += 1
        finally:
            for n, v in saved.items():
                if v == "<absent>":
                    sys.modules.pop(n, None)
                else:
                    sys.modules[n] = v
    res["modes"][mode] = {"total": dict(cnt), "per_entry": {k: dict(v) for k, v in per_entry.items()}, "other": others}
    print(mode, dict(cnt), "load_topology", dict(per_entry["load_topology"]), "find_stack_edges", dict(per_entry["find_stack_edges"]))
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
