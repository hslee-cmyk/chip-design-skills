# -*- coding: utf-8 -*-
"""실행 뒤 대조의 실제 경로: 복제본에서 .spiceinit 쓰기를 뺀 뮤턴트 + 독이 든 HOME 으로 R1 oracle_run. 사용: a7_mut.py <iso_m> <exe> <work> <out.json>"""
import hashlib, json, os, re, shutil, subprocess, sys
ISO, EXE, WORK, OUT = sys.argv[1:5]
O = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle")
p = os.path.join(O, "adapters/ngspice/run.py")
s = open(p, encoding="utf-8", newline="").read()
s2, n = re.subn(r'    with open\(os\.path\.join\(work_dir, "\.spiceinit"\), "wb"\) as f:\r?\n        f\.write\(spiceinit_text\.encode\("utf-8"\)\)\r?\n', "", s)
assert n == 1
open(p, "w", encoding="utf-8", newline="").write(s2)
BL = os.path.join(ISO, ".ai/verification/20261104-op1b/baseline/R1.converted.json")
i = json.load(open(BL, encoding="utf-8"))["input"]
dp = os.path.join(O, "descriptors/sky130.oracle_descriptor.json")
i["process"]["descriptor"] = {"path": dp.replace("\\", "/"), "sha256": hashlib.sha256(open(dp, "rb").read().replace(b"\r\n", b"\n")).hexdigest()}
shutil.rmtree(WORK, ignore_errors=True)
home = os.path.join(WORK, "home")
os.makedirs(home)
open(os.path.join(home, ".spiceinit"), "w", newline="\n").write("set ngbehavior=hsa\n")
ip = os.path.join(WORK, "t.input.json")
json.dump(i, open(ip, "w", encoding="utf-8"), ensure_ascii=False)
e = dict(os.environ)
e["HOME"] = e["USERPROFILE"] = home
for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
    e.pop(k, None)
r = subprocess.run([sys.executable, "-P", os.path.join(O, "oracle_run.py"), ip, os.path.join(WORK, "o"), "--bias", "free"], cwd=WORK, env=e, capture_output=True, text=True, encoding="utf-8", errors="replace")
tree = []
for root, _, fs in os.walk(os.path.join(WORK, "o")):
    tree += [os.path.relpath(os.path.join(root, f), os.path.join(WORK, "o")).replace("\\", "/") for f in fs]
rej = [f for f in tree if f.endswith(".reject.json")]
res = {"rc": r.returncode, "files": sorted(tree), "reject": json.load(open(os.path.join(WORK, "o", rej[0]), encoding="utf-8")) if rej else None}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"rc": res["rc"], "files": res["files"], "code": res["reject"] and res["reject"]["code"], "detail": res["reject"] and res["reject"]["detail"], "stage": res["reject"] and res["reject"]["stage"]}, ensure_ascii=False))
