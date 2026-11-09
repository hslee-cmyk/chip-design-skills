import json
rows=[json.loads(l) for l in open("devices.jsonl",encoding="utf-8")]
sf=[r for r in rows if r["cls"]!="B"]
def f(x,fmt="{:.3g}"): return "-" if x is None else fmt.format(x)
for V in "BC":
    print("== variant",V)
    print("circuit dev kind cls f_req(MHz) vsb nonempty differ left | dVGS med/max(V) | drel med/max | dlnIDu med/max")
    for r in sf:
        s=r["summary"][V]
        fr="-" if r["f_req"] is None else f"{r['f_req']/1e6:.3g}"
        print(r["circuit"][:14],r["dev"][:10],r["kind"],r["cls"],fr,r["vsb_idx"][:2],f"{s['n_nonempty']}/{s['n_cfg']}",s["n_differ"],s["n_left"],"|",
              f(s["dvgs"] and s["dvgs"]["med"]),f(s["dvgs"] and s["dvgs"]["max"]),"|",f(s["drel"] and s["drel"]["med"]),f(s["drel"] and s["drel"]["max"]),"|",f(s["dlnidu"] and s["dlnidu"]["med"]),f(s["dlnidu"] and s["dlnidu"]["max"]))
