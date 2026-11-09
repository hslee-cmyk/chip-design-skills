import json, collections
rows=[json.loads(l) for l in open("devices.jsonl",encoding="utf-8")]
sf=[r for r in rows if r["cls"]!="B"]
def cnt(V,key,thr=0):
    a=al=0
    for r in sf:
        s=r["summary"][V]
        if s["n_nonempty"]==0: continue
        a+= s[key]>0; al+= s[key]==s["n_nonempty"]
    return a,al
print("N S/F devices",len(sf))
for V in "ABC":
    print(V,"left any/all",cnt(V,"n_left"),"left&>0.1%",cnt(V,"n_left_rel_gt_0p1pct"),"left&>1%",cnt(V,"n_left_rel_gt_1pct"),
      "differ any/all",cnt(V,"n_differ"),">0.1%",cnt(V,"n_differ_rel_gt_0p1pct"),">1%",cnt(V,"n_differ_rel_gt_1pct"),">5%",cnt(V,"n_differ_rel_gt_5pct"),">50mV",cnt(V,"n_differ_dvgs_gt_50mV"))
