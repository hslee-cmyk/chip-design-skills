"""DIFF-DUP (auditor 독립 작성, 2026-09-30 P9 순서 3) -- spec card 20260930-p9-kcl-edges 계약 4.
실행 환경(계약 4): 저장소 트리 그대로의 복제본 <root>에서 A=<root>/skills/analog-gmid-design/assets를 sys.path 맨 앞에 넣고
모듈 이름 stick_diagram으로 import한다. stick_diagram이 A 밖에서 import되거나 analog-grammar(netclass·idioms)가 <root> 밖에서
import되거나 import되지 않으면 중단(B34: 조용한 ImportError가 입력 (i)을 바꾼다).
회로마다(library/*.topology.json, '_' 시작 제외) 입력 (i) current_forced 매칭 쌍(SR _build_theta_evaluator와 같은 식)
(ii) [] 에서 list(kcl_series_union(trs,P).items())와 _kcl_and_matching_edges(trs,P)를 그대로 JSON에 싣는다.
더해 라이브러리 밖 이름의 합성 넷리스트(레일 이름 넷 2회 사용 포함)를 같은 방식으로 싣는다.
사용: python -P diff_dup.py <root> <out.json>"""
import hashlib, json, os, sys
root = os.path.abspath(sys.argv[1]); out = sys.argv[2]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, A)
import stick_diagram as sd
nc = os.path.normcase
if not nc(os.path.abspath(sd.__file__)).startswith(nc(A)):
    sys.exit("stick_diagram imported outside root: %s" % sd.__file__)
netclass, idioms = sd._import_analog_grammar("netclass", "idioms")
AG = os.path.join(root, "skills", "analog-grammar", "assets")
if netclass is None or idioms is None:
    sys.exit("analog-grammar import failed")
for m in (netclass, idioms):
    if not nc(os.path.abspath(m.__file__)).startswith(nc(AG)):
        sys.exit("analog-grammar imported outside root: %s" % m.__file__)


def h(o):
    return hashlib.sha256(json.dumps(o, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def run(trs, P):
    g = [[k, list(v)] for k, v in sd.kcl_series_union(trs, P).items()]
    e = [list(x) for x in sd._kcl_and_matching_edges(trs, P)]
    return {"groups": g, "n_groups": len(g), "edges": e, "n_edges": len(e)}


def components(trs, edges):
    """엣지 목록의 연결 성분을 netlist 순서 대표·구성원·키 순서로(자기 점검용, 피검 함수와 독립 구현)."""
    names = [t.name for t in trs]
    adj = {n: set() for n in names}
    for a, b, _k, _d in edges:
        adj[a].add(b); adj[b].add(a)
    seen, comps = set(), []
    for n in names:
        if n in seen:
            continue
        stack, comp = [n], set()
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp.add(x); stack.extend(adj[x] - comp)
        seen |= comp
        mem = [m for m in names if m in comp]
        comps.append([mem[0], mem])
    return comps


res = {"stick_diagram_file": os.path.relpath(sd.__file__, root).replace("\\", "/"),
       "analog_grammar": {m.__name__: os.path.relpath(m.__file__, root).replace("\\", "/") for m in (netclass, idioms)},
       "circuits": {}, "load_failures": {}}
import glob
for p in sorted(glob.glob(os.path.join(A, "library", "*.topology.json"))):
    name = os.path.basename(p)[:-len(".topology.json")]
    try:
        trs, meta = sd.load_topology(p)
    except Exception as ex:
        res["load_failures"][name] = type(ex).__name__
        continue
    forced = [tuple(q["names"]) for q in meta["symmetry"]["matching_pairs"] if q["current_forced"]]
    ent = {"n_dev": len(trs), "forced_pairs": [list(x) for x in forced]}
    for tag, P in (("i_forced", forced), ("ii_empty", [])):
        r = run(trs, P)
        r["components_of_edges_equal_groups"] = components(trs, r["edges"]) == r["groups"]
        ent[tag] = r
    # 레일 이름 넷 정확히 2회 사용
    uses = {}
    for t in trs:
        for n in (t.source, t.drain):
            uses[n] = uses.get(n, 0) + 1
    ent["rail_name_nets_used_twice"] = sorted(n for n, c in uses.items() if n in ("vdd", "gnd", "vss") and c == 2)
    res["circuits"][name] = ent

T = sd.Transistor
syn = [T(name="qa1", kind="nmos", source="gnd", drain="nx_1"),
       T(name="qa2", kind="nmos", source="nx_1", drain="nx_2"),
       T(name="qb1", kind="pmos", source="vdd", drain="nx_2"),
       T(name="qb2", kind="nmos", source="gnd", drain="nx_3"),
       T(name="qc1", kind="pmos", source="nx_4", drain="nx_4"),
       T(name="qc2", kind="nmos", source="nx_5", drain="nx_6"),
       T(name="qc3", kind="nmos", source="nx_5", drain="nx_7"),
       T(name="qc4", kind="pmos", source="nx_5", drain="nx_8")]
res["synthetic"] = {"netlist": [[t.name, t.kind, t.source, t.drain] for t in syn],
                    "note": "gnd 2회(qa1, qb2 -- 레일 이름 넷 정확히 2회), vdd 1회, nx_5 3회, nx_4 같은 소자 2회(source=drain)",
                    "P_pairs": [["qc2", "qb2"], ["qc4", "qc3", "qa1"]]}
suses = {}
for t in syn:
    for n in (t.source, t.drain):
        suses[n] = suses.get(n, 0) + 1
res["synthetic"]["net_use_counts"] = dict(sorted(suses.items()))
for tag, P in (("i_pairs", [("qc2", "qb2"), ("qc4", "qc3", "qa1")]), ("ii_empty", [])):
    r = run(syn, P)
    r["components_of_edges_equal_groups"] = components(syn, r["edges"]) == r["groups"]
    res["synthetic"][tag] = r

res["summary_n_groups"] = {k: [v["i_forced"]["n_groups"], v["ii_empty"]["n_groups"]] for k, v in res["circuits"].items()}
res["hash_circuits"] = h(res["circuits"])
res["hash_synthetic"] = h(res["synthetic"])
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("load_failures", res["load_failures"])
print("analog_grammar", res["analog_grammar"])
for k, v in res["summary_n_groups"].items():
    c = res["circuits"][k]
    print(k, v, "comp_eq", c["i_forced"]["components_of_edges_equal_groups"], c["ii_empty"]["components_of_edges_equal_groups"],
          "rail2", c["rail_name_nets_used_twice"])
print("synthetic", res["synthetic"]["net_use_counts"], res["synthetic"]["i_pairs"]["n_groups"], res["synthetic"]["ii_empty"]["n_groups"],
      res["synthetic"]["i_pairs"]["components_of_edges_equal_groups"], res["synthetic"]["ii_empty"]["components_of_edges_equal_groups"])
print("hash_circuits", res["hash_circuits"]); print("hash_synthetic", res["hash_synthetic"])
