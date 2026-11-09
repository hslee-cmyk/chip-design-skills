"""(마) 덤 확인: 동점 순서 역전 변이에서 계약 10 입력의 채택 소자가 실제로 Mx1 -> Mx2로 바뀌는지(변이가 의미 있는지).
argv: <작업 사본 루트(C:/g342/kt)> <출력 json>. 원본 바이트로 되돌리고 git diff --quiet 확인."""
import json
import os
import subprocess
import sys

KT, OUTP = sys.argv[1:3]
SDP = KT + "/skills/analog-gmid-design/assets/stick_diagram.py"
OLD = "        pending.sort(key=lambda item: (-len(item[1]), item[0].name))\n"
NEW = "        pending.sort(key=lambda item: item[0].name, reverse=True)\n        pending.sort(key=lambda item: -len(item[1]))\n"
orig = open(SDP, "rb").read()
code = r'''
import json, os, sys
sys.path.insert(0, sys.argv[1] + "/skills/analog-gmid-design/assets")
os.makedirs("C:/g342/tmp/tie", exist_ok=True); os.chdir("C:/g342/tmp/tie")
import stick_diagram as sd
def nl(n,k,s,d,g): return {"name":n,"kind":k,"source":s,"drain":d,"gate":g}
out = {}
for tag, tap, oth in (("tap_p","ninp","ninn"),("tap_n","ninn","ninp")):
    doc = {"topology_name": tag, "schema_version": "2.0", "supply_nets": ["vdd","gnd"],
           "netlist": [nl("M1","nmos","ntail","nd1","ninp"), nl("M2","nmos","ntail","nd2","ninn"), nl("M3","pmos","vdd","nd1","nbp"),
                       nl("M4","pmos","vdd","nd2","nbp"), nl("M5","nmos","gnd","ntail","nvb"), nl("Mx1","nmos","gnd","nx1",tap),
                       nl("Mx2","nmos","gnd","nx2",tap), nl("My","nmos","gnd","ny",oth)],
           "symmetry": {"matching_pairs": [], "dispositions": []}}
    p = tag + ".topology.json"; json.dump(doc, open(p, "w"))
    _t, m = sd.load_topology(p); af = m["_device_roles_autofilled"]
    out[tag] = [n for n in ("Mx1","Mx2") if (af.get(n,{}).get("gm_id_role"), af.get(n,{}).get("L_role")) == ("matching","mirror")]
print(json.dumps(out))
'''
res = {}
for label, data in (("original", orig), ("tie_reversed", orig.decode("utf-8").replace(OLD, NEW).encode("utf-8"))):
    assert label == "original" or data != orig
    open(SDP, "wb").write(data)
    try:
        r = subprocess.run([sys.executable, "-B", "-c", code, KT], capture_output=True, text=True,
                           env=dict(os.environ, PYTHONPYCACHEPREFIX="C:/g342/pyc/tie_" + label))
        res[label] = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else {"error": r.stderr[-500:]}
    finally:
        open(SDP, "wb").write(orig)
assert subprocess.run(["git", "-C", KT, "diff", "--quiet"]).returncode == 0
res["restored_clean"] = True
json.dump(res, open(OUTP, "w", encoding="utf-8"))
print(res)
