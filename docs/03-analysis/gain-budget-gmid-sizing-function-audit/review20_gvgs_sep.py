import networkx as nx, engine as E, json, os
fn=os.path.join(E.SP,"results5_gvgs_separate_rails.jsonl"); open(fn,"w").close()
for c in E.circuits():
    G=nx.MultiGraph()
    for m in c["devs"]: G.add_edge(m["g"],m["s"],key=m["name"])
    # each rail its own fixed node (not merged together)
    nb=G.number_of_edges()-G.number_of_nodes()+nx.number_connected_components(G)
    # classify: non-v0 basis count = nb - (#parallel same (g,s) duplicates)
    from collections import Counter
    cnt=Counter((m["g"],m["s"]) for m in c["devs"])
    v0=sum(v-1 for v in cnt.values())
    row=dict(circuit=c["name"], basis=nb, v0=v0, non_v0=nb-v0)
    open(fn,"a").write(json.dumps(row)+"\n"); print(row)
