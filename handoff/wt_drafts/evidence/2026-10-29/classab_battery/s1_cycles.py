# S1 G_vgs 사이클(kvl_branch·port_diff·vds_saturation) 실측 -- 읽기 전용, 결과는 같은 폴더 s1_cycles.out.txt
import sys, json, pathlib
E = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(E)); sys.path.insert(0, str(E/"gmid_engine/tests/graph"))
from gmid_engine.authoring import load_topology
from gmid_engine.graph import build_s1, GRAPH_KEY
from gmid_engine.search import open_run
out = open(pathlib.Path(__file__).with_suffix(".out.txt"), "w", encoding="utf-8")
names = sys.argv[1:] or ["current_reuse_telescopic_ota"]
import conftest as C
for name in names:
    d, c = open_run()
    try:
        s1 = build_s1(load_topology(str(E/"assets/library"/(name+".topology.json"))), C.supplies_for(name), donors=d, counters=c)
    except Exception as e:
        out.write(f"== {name}: build fail {type(e).__name__} {e}\n"); continue
    out.write(f"== {name}\n")
    for r in s1.value("graph", GRAPH_KEY, "rel_kvl_branch"):
        out.write(f"kvl_branch {r.members} {r.evidence.rule} nets={r.evidence.nets}\n")
    s = s1.value("graph", GRAPH_KEY, "gvgs_summary")
    for r in s.port_diff: out.write(f"port_diff {r.members}\n")
    for r in s.vds_saturation: out.write(f"vds_sat {r.members} nets={r.evidence.nets}\n")
    out.flush()
