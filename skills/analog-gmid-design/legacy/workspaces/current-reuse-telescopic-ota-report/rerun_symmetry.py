import sys, json, io
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from stick_diagram import load_topology, find_matching_candidates, find_hub_merge_candidates, check_symmetry_dispositions

JSON_PATH = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"

transistors, meta = load_topology(JSON_PATH)
matching_pairs = meta["symmetry"]["matching_pairs"]
disp_list = meta["symmetry"]["dispositions"]

# convert JSON list-of-dicts dispositions -> dict[(tag,kind,key)] = (category,reason)
disp_dict = {}
for d in disp_list:
    key = (d["tag"], d["kind"], d["key"])
    disp_dict[key] = (d.get("category"), d.get("reason"))

verdict = check_symmetry_dispositions(transistors, matching_pairs, disp_dict)
print("=== case_collisions ===")
print(verdict.case_collisions)
print("=== undisposed (new candidates needing a decision) ===")
for u in verdict.undisposed:
    print(u)
print("ok =", verdict.ok)

print()
print("=== raw find_matching_candidates() ===")
mc = find_matching_candidates(transistors)
for tag in ("current_mirror", "diff_pair"):
    print(f"-- {tag} --")
    for key, group in mc[tag].items():
        print(key, "->", sorted(t.name for t in group))

print()
print("=== raw find_hub_merge_candidates() ===")
hc = find_hub_merge_candidates(transistors)
for key, group in hc.items():
    print(key, "->", sorted(t.name for t in group))

print()
print("=== stale disposition entries (key not found in any current candidate) ===")
all_keys = set()
for tag in ("current_mirror", "diff_pair"):
    for key in mc[tag].keys():
        all_keys.add((tag,) + key)
for key in hc.keys():
    all_keys.add(("hub_merge",) + key)

for d in disp_list:
    k = (d["tag"], d["kind"], d["key"])
    if k not in all_keys:
        print("STALE:", k)
