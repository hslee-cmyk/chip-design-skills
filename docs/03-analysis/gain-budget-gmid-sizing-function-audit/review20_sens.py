import json, os, collections, itertools
import analysis as A, engine as E
import networkx as nx
fn = os.path.join(E.SP, "results4_loop_sensitivity.jsonl"); open(fn, "w").close()
KEYS = ["strict_in_strictorder", "strict_in_loose_order", "node_in_strictorder", "node_in_loose_order"]
for c in E.circuits():
    if c["name"] not in ("current_reuse_telescopic_ota", "sf_pushpull_output_opamp", "ngcc_3stage_ff", "two_stage_ota_sf", "pushpull_follower_buffer"): continue
    for j1 in (True, False):
        for pc in (0, 1):
            for portp in (True, False):
                opt = {"pcost": pc, "no_rule14": not j1, "bfs_port_passive": portp}
                r1, ctx = E.run(c, opt)
                B = A.blocks_merged(ctx)
                Gl = A.loop_graph(ctx)
                dist, _, _ = A.bfs01(ctx, Gl, pc, opt)
                cyc = A.enumerate_cycles(Gl)
                D = nx.DiGraph(); D.add_edges_from(Gl.edges()); D.add_nodes_from(Gl.nodes)
                rt = sum(1 for _ in nx.simple_cycles(D))
                row = dict(circuit=c["name"], J1=j1, pcost=pc, port_passive=portp, n_node=len(cyc), n_incl_roundtrip=rt)
                for k in KEYS:
                    cnt = collections.Counter()
                    for cy in cyc:
                        ks = set()
                        for combo in cy["exps"]:
                            tags, info = A.classify_cycle(ctx, cy, combo, dist, B, opt)
                            ks.add("1.5" if tags == ["1.5"] else A.final_class(tags, info, k))
                        cnt["|".join(sorted(ks))] += 1
                    row[k] = dict(cnt)
                # (2) that also satisfy 3b condition (loose)
                with open(fn, "a", encoding="utf-8") as fh: fh.write(json.dumps(row) + "\n")
                print(json.dumps(row))
