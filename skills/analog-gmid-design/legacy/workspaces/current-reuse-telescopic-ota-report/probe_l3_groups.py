"""
L3 half-cutting 교차검증용 -- current_reuse_telescopic_ota의 실제 geometry_colocation_union()
그룹 중 다중 matching_pairs가 섞인 후보를 뽑아 손 검증 대상으로 출력한다.
"""
import sys, json, itertools
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
from stick_diagram import load_topology, geometry_colocation_union

TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"

transistors, meta = load_topology(TOPO)
pairs_meta = meta["symmetry"]["matching_pairs"]
forced_pairs = [tuple(p["names"]) for p in pairs_meta if p.get("current_forced")]
all_pairs = [tuple(sorted(p["names"])) for p in pairs_meta]

groups = geometry_colocation_union(transistors, forced_pairs)
by_name = {t.name: t for t in transistors}

print(f"총 그룹 수: {len(groups)}")
for gid, names in groups.items():
    if len(names) < 4:
        continue
    # 이 그룹 내부에 걸린 matching_pairs(양쪽 다 이 그룹에 속하는 것)만 필터
    name_set = set(names)
    inside_pairs = [p for p in pairs_meta if set(p["names"]) <= name_set]
    if len(inside_pairs) < 2:
        continue
    print(f"\n=== 그룹 {gid} (소자 {len(names)}개, 내부 matching_pairs {len(inside_pairs)}개) ===")
    for n in names:
        t = by_name[n]
        print(f"  {n}: kind={t.kind} source={t.source} drain={t.drain} gate={t.gate} n_fingers={t.n_fingers}")
    for p in inside_pairs:
        print(f"  pair: {p['names']} current_forced={p.get('current_forced')} "
              f"matching_sensitivity={p.get('matching_sensitivity')}")
