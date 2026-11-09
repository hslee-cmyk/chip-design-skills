"""경로 3(refine 후보) 결과와 레거시 폴백(geometry_colocation_union) 결과가 갈리는 입력 찾기(head 사본)."""
import glob, json, os, sys, tempfile
ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "skills/analog-gmid-design/assets"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stick_diagram as SD, sizing_recipe as SR
out = open("C:/g68/out/probe_path3.txt", "w", encoding="utf-8")
def show(label, p):
    t, m = SD.load_topology(p)
    dr = {k: v for k, v in (m.get("device_roles") or {}).items() if not k.startswith("_")}
    if any(isinstance(v, dict) and v.get("vertical_stack_id") for v in dr.values()):
        out.write("%s declared vsid -- skip\n" % label); return
    ref = SD.refine_differential_and_mirror_relations(t, m["ports"].inputs, m["ports"].outputs)
    cand = (ref or {}).get("vertical_stack_id_candidates")
    g3 = SR.resolve_stack_layout(t, [], dr, ports=m["ports"])
    leg = SR.geometry_colocation_union(t, [])
    f = lambda g: sorted(sorted(v) for v in g.values() if len(v) > 1)
    out.write("%s cand=%s path3=%s legacy=%s differ=%s\n" % (label, bool(cand), f(g3), f(leg), f(g3) != f(leg)))
for p in sorted(glob.glob(os.path.join(ROOT, "skills/analog-gmid-design/assets/library/*.topology.json"))):
    if "_TEMPLATE" not in p:
        show(os.path.basename(p), p)
import contracts_syn as C
d = tempfile.mkdtemp(dir="C:/g68")
for name, topo in C.SYN.items():
    p = os.path.join(d, name + ".json"); json.dump(topo, open(p, "w")); show(name, p)
out.close(); print(open("C:/g68/out/probe_path3.txt", encoding="utf-8").read())
