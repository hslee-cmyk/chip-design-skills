import json, numpy, os, sys, hashlib
R="C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2"
OUT="C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/work/meta_dump"
os.makedirs(OUT,exist_ok=True)
m=json.load(open(R+"/manifest.json",encoding="utf-8"))
files=[s["file"] for s in m["slices"]]
loc=json.load(open("C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-op7a-audit/skills/analog-gmid-design/assets/lut_v2_location.json",encoding="utf-8"))
for k,v in loc["files"].items():
    if k!="manifest": files.append(v["path"])
for f in files:
    with numpy.load(os.path.join(R,f)) as z:
        names=list(z.files)
        mk=[n for n in names if "meta" in n.lower()]
        rec={"file":f,"members":names[:60],"n_members":len(names),"meta_members":mk}
        for n in mk:
            a=z[n]
            try: rec[n]=json.loads(str(a.item() if a.shape==() else a.tolist()))
            except Exception as e: rec[n]=str(a)[:2000]
    json.dump(rec,open(os.path.join(OUT,f+".json"),"w",encoding="utf-8"),indent=1,sort_keys=True)
    print(f,len(names),mk,flush=True)
