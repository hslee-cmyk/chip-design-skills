import json,numpy as np,pathlib
LOC=json.loads(pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/lut_v2_location.json").read_text(encoding="utf-8"))
Z=np.load(pathlib.Path(LOC["root"]["default"])/LOC["files"]["cap_npz"]["path"],allow_pickle=True)
VG=Z["VGS"]
for k in "np":
  for li in (0,9,17):
    for nm in ("VDSAT","CGG","GM","ID"):
        a=Z[nm+"_"+k][li,:,32,0]
        print(k,Z["L"][li],nm, np.array2string(a[[0,8,16,24,32,40,48]],precision=3))
  print("nan counts",{nm:int(np.isnan(Z[nm+"_"+k]).sum()) for nm in ("ID","GM","CGG","VDSAT")}, "ID<=0",int((Z["ID_"+k]<=0).sum()), "CGG<=0", int((Z["CGG_"+k]<=0).sum()))
print(json.loads(str(Z["meta_json"]))["notes"] if "notes" in json.loads(str(Z["meta_json"])) else list(json.loads(str(Z["meta_json"])).keys())[:20])
