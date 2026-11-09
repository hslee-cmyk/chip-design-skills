# import ast, sys, os
# sys.path.insert(0, "C:/g39")
# import sim_head as s
# import mutate_changed as mc, reachability as rch
# R = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
# appr = rch._approved_ids(R, "cd64170")
# head, _ = s.build_b26(s.BASEF)
# out = open("C:/g39/leak2.txt", "w", encoding="utf-8")
# out.write("approved ids in cd64170 tree: %d\n" % len(appr))
# for label, h in (("base(cd64170) bodies", s.BASEF), ("B26-1 sim head", head), ("P9 sim head", s.build_p9(s.BASEF))):
#     hits = []
#     for path in (s.SD, s.SR):
#         mod = rch.module_name(path)
#         for q, fn in rch.iter_defs(ast.parse(h[path])):
#             if q not in ("load_topology", "save_instance_json", "kcl_series_union"):
#                 continue
#             for op, p, m in mc.mutants(fn, h[path]):
#                 mid = "%s:%s:%s:%s" % (mod, q, op, p)
#                 if mid in appr:
#                     node = mc._get(fn, p.rsplit(".ops", 1)[0] if op == "cmp_flip" else p)
#                     hits.append((mid, getattr(node, "lineno", None), ast.unparse(node).split("\n")[0][:90]))
#     out.write("== %s: approved-id hits %d\n" % (label, len(hits)))
#     for x in hits:
#         out.write("  %s | line %s | %s\n" % x)
,"_propose_L_roles","propose_vertical_stack_id_gap_fill","geometry_colocation_union","load_topology"]
dm = dict(rch.iter_defs(ast.parse(head[s.SD])))
tot=0; hit=0; per=[]
for q in b34:
    ids = ["stick_diagram:%s:%s:%s" % (q, op, p) for op, p, _ in mc.mutants(dm[q], head[s.SD])]
    h = sum(1 for i in ids if i in exempt)
    tot += len(ids); hit += h
    if h: per.append((q, h, len(ids)))
with open("C:/g39/leak.txt","w",encoding="utf-8") as fh:
    fh.write("exempt=%d touched=%d\n" % (len(exempt), len(touched_ids)))
    fh.write("B34 targets on B26-1 head: mutants=%d, ids already in B26-1 exempt set=%d\n" % (tot, hit))
    for x in per: fh.write("  %s %d/%d\n" % x)


# ---- leak2 (기존 승인 id 대조) ----
