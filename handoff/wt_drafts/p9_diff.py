import sys, glob, os, json
A = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets"
sys.path.insert(0, A)
import stick_diagram as sd
out = []
def comps(trs, edges):
    parent = {t.name: t.name for t in trs}
    def f(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for a, b, *_ in edges:
        ra, rb = f(a), f(b)
        if ra != rb: parent[ra] = rb
    g = {}
    for t in trs: g.setdefault(f(t.name), []).append(t.name)
    return sorted(sorted(v) for v in g.values())
rails_seen = set()
for p in sorted(glob.glob(os.path.join(A, "library", "*.topology.json"))):
    name = os.path.basename(p)
    try:
        trs, meta = sd.load_topology(p)
    except Exception as e:
        out.append(f"{name}: LOAD FAIL {type(e).__name__}: {e}"[:300]); continue
    raw = json.load(open(p, encoding="utf-8"))
    sup = raw.get("supply_nets") or (raw.get("ports") or {}).get("supply") or raw.get("ports", {})
    forced = [tuple(x["names"]) for x in meta["symmetry"]["matching_pairs"] if x.get("current_forced")]
    for label, pairs in (("forced", forced), ("none", [])):
        u = sorted(sorted(v) for v in sd.kcl_series_union(trs, pairs).values())
        e = comps(trs, sd._kcl_and_matching_edges(trs, pairs))
        out.append(f"{name} [{label}] n_dev={len(trs)} n_pairs={len(pairs)} groups={len(u)} equal={u == e}")
    nets = set()
    for t in trs: nets |= {t.source, t.drain, t.gate, getattr(t, 'bulk', None)}
    railish = sorted(n for n in nets if n and n.lower() in ("vdd","gnd","vss","agnd","avdd","avss","vcc","vee","dvdd","dgnd"))
    out.append(f"   railish nets present={railish} in_RAIL_NETS={[n for n in railish if n in sd._RAIL_NETS]} supply_nets_decl={raw.get('supply_nets')}")
open(os.path.join(os.path.dirname(__file__), "p9_diff.out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
