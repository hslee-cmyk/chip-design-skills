import json,sys,collections
calls=json.load(open("calls.json",encoding="utf-8"))
shared=set()
for l in open("shared.tsv",encoding="utf-8").read().splitlines()[1:]:
    p=l.split("\t"); shared.add((p[0],p[1]))
skip_mods={"gmid_engine.authoring._rejection","gmid_engine.authoring._spec_fields","gmid_engine.core.determinism","gmid_engine.core.fingerprint","gmid_engine.core.blas_env","gmid_engine.core.exit_code","gmid_engine.core.failure_partial","gmid_engine.core.immutability","gmid_engine.lut._helpers_fail","gmid_engine.lut.axis_guard","gmid_engine.authoring.json_read"}
g=collections.defaultdict(list)
for c in calls:
    k=(c["callee_mod"],c["callee"])
    if k in shared and c["callee_mod"]!=c["caller_mod"] and k[0] not in skip_mods: g[k].append(c)
out=open("sites.txt","w",encoding="utf-8")
for k in sorted(g):
    out.write("## %s.%s\n"%(k[0].replace("gmid_engine.",""),k[1]))
    for c in g[k]:
        out.write("  - %s:%d [%s] blk=%s :: %s\n"%(c["caller_mod"].replace("gmid_engine.",""),c["line"],c["caller_fn"],c["caller_block"],c["text"].replace("\n"," ")[:220]))
print(len(g))
