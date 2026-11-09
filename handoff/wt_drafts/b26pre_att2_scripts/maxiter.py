import sys, json
sys.path.insert(0, r"C:/g344/iso/skills/analog-gmid-design/assets")
import sizing_recipe as sr, stick_diagram as sd
lut = sr.build_toy_lut()
r = sr.size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=lut, vds=0.6)
def pair():
    return [sr.Transistor("Ma", "nmos", source="vtail", drain="nda", gate="ga", n_fingers=1, finger_w=r.W, stack_id="pair_row"),
            sr.Transistor("Mb", "nmos", source="vtail", drain="ndb", gate="gb", n_fingers=1, finger_w=r.W, stack_id="pair_row")]
out = {}
for mi in (1, 2, 3, 4):
    rows, res = sd.repair_matching_safety({"pair_row": pair()}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, max_iter=mi)
    out[mi] = sorted(rows)
rows, res = sd.repair_matching_safety({"pair_row": pair()}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"})
out["default"] = sorted(rows)
open(r"C:/g344/tmp/maxiter.json", "w").write(json.dumps(out))
