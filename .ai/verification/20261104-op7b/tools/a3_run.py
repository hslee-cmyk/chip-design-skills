# -*- coding: utf-8 -*-
"""A3-4 실행: OP-1b R1~R5 를 새 오라클로 격리 환경(빈 출력 폴더 + 빈 HOME)에서 순차 실행.
변환 = op1b_lib.convert_input (기준선 Rn.converted.json 과 대조), descriptor sha 는 파일 바이트에서 잰다.
사용: a3_run.py <iso_root> <work_root> <exe> <ids,...> [--with-bias-from-table]
"""
import copy, hashlib, json, os, shutil, subprocess, sys, time

ISO, WORK, EXE, IDS = sys.argv[1:5]
O = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle")
BL = os.path.join(ISO, ".ai/verification/20261104-op1b")
sys.path.insert(0, os.path.join(BL, "scripts"))
import op1b_lib as L  # noqa: E402

BIAS = {"R1": ["free"], "R2": ["free"], "R3": ["free", "forced"], "R4": ["free", "forced"], "R5": ["iso"]}
OLD_RAW = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op1b_audit/run/work"
DESC = os.path.join(O, "descriptors/sky130.oracle_descriptor.json")


def lf_sha(p):
    return hashlib.sha256(open(p, "rb").read().replace(b"\r\n", b"\n")).hexdigest()


os.makedirs(WORK, exist_ok=True)
log = []
for rid in IDS.split(","):
    conv = json.load(open(os.path.join(BL, "baseline", f"{rid}.converted.json"), encoding="utf-8"))
    old = json.load(open(os.path.join(OLD_RAW, rid, "t.input.json"), encoding="utf-8"))
    descriptor = {"path": DESC.replace("\\", "/"), "sha256": lf_sha(DESC)}
    new, rec = L.convert_input(old, lut_files=conv["input"]["process"]["lut_files"], descriptor=descriptor, adapter="ngspice", exe=EXE)
    same = copy.deepcopy(new)
    same["process"]["descriptor"] = None
    conv_same = same == conv["input"]
    d = os.path.join(WORK, rid)
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(os.path.join(d, "home"))
    ip = os.path.join(d, "t.input.json")
    with open(ip, "w", encoding="utf-8") as f:
        json.dump(new, f, ensure_ascii=False, indent=1)
    env = dict(os.environ)
    env["HOME"] = env["USERPROFILE"] = os.path.join(d, "home")
    for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
        env.pop(k, None)
    t0 = time.time()
    r = subprocess.run([sys.executable, "-P", os.path.join(O, "oracle_run.py"), ip, os.path.join(d, "o"), "--bias", *BIAS[rid]],
                       cwd=d, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    rec2 = {"id": rid, "rc": r.returncode, "stdout": r.stdout[-1500:], "stderr": r.stderr[-1500:], "convert_equals_baseline_converted": conv_same,
            "descriptor_sha256": descriptor["sha256"], "wall_s": round(time.time() - t0, 2)}
    log.append(rec2)
    print(json.dumps(rec2, ensure_ascii=False))
    with open(os.path.join(WORK, "run_log.jsonl"), "w", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(x, ensure_ascii=False) for x in log) + "\n")
