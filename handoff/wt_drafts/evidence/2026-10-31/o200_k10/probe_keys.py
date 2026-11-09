import json, pathlib, numpy as np
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
LOC = json.loads((ENG / "assets/lut_v2_location.json").read_text(encoding="utf-8"))
p = pathlib.Path(LOC["root"]["default"]) / LOC["files"]["cap_npz"]["path"]
print(p)
Z = np.load(p, allow_pickle=True)
for k in Z.files: print(k, Z[k].shape if hasattr(Z[k],'shape') else '')
print("L", Z["L"]); print("VGS", Z["VGS"][:5], Z["VGS"][-1], len(Z["VGS"])); print("VDS", Z["VDS"]); print("VS", Z["VS"])
for k in ("temp","temperature","T"):
    if k in Z.files: print(k, Z[k])
