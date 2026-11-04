# -*- coding: utf-8 -*-
"""A7-4 뒤 대조: 모든 실행 로그 모드, status.error, fingerprints.compat_sha256, 기준선 데이터 파일 바이트, OP-3 판정 실행(run1)과 sim 칸·넷리스트 비교. 사용: a7_4b.py <run> <op3_run1> <out.json>"""
import glob, json, os, sys
RUN, OP3, OUT = sys.argv[1:4]
OLD = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op1b_audit/run/work"
res = {"logs": {}, "compat_sha": {}, "sim_vs_op3": {}, "cir_vs_op3": {}, "data_vs_baseline": {"same": 0, "diff": [], "missing": []}}
for rid in ("R1", "R2", "R3", "R4", "R5"):
    for log in sorted(glob.glob(f"{RUN}/{rid}/o/*/bench.log")):
        t = open(log, encoding="utf-8", errors="replace").read()
        k = os.path.relpath(log, RUN).replace("\\", "/")
        si = os.path.join(os.path.dirname(log), ".spiceinit")
        res["logs"][k] = {"default_line": "Note: No compatibility mode selected!" in t, "spiceinit_bytes": os.path.getsize(si) if os.path.exists(si) else None}
        cir = os.path.join(os.path.dirname(log), "bench.cir")
        c3 = os.path.join(OP3, os.path.relpath(cir, RUN))
        res["cir_vs_op3"][k] = open(cir, "rb").read() == open(c3, "rb").read()
    for p in sorted(glob.glob(f"{RUN}/{rid}/o/*.compare.json")):
        res["compat_sha"][os.path.basename(p)] = json.load(open(p, encoding="utf-8"))["fingerprints"]["compat_sha256"]
    for p in sorted(glob.glob(f"{RUN}/{rid}/o/*.sim.json")):
        n = json.load(open(p, encoding="utf-8"))
        o = json.load(open(os.path.join(OP3, rid, "o", os.path.basename(p)), encoding="utf-8"))
        res["sim_vs_op3"][os.path.basename(p)] = {"equal": n == o, "status_error": (n.get("status") or {}).get("error"), "loop_error": ((n.get("loop") or {}).get("status") or {}).get("error")}
    for p in glob.glob(f"{OLD}/{rid}/o/*.txt"):
        b = os.path.basename(p)
        for tag in (".free.", ".forced.", ".iso."):
            if tag in b:
                stem, rest = b.split(tag, 1)
                break
        if rest.startswith(("stab", "pz")):
            continue
        sub = stem + tag.rstrip(".")
        if rest.startswith("loop."):
            new = f"{RUN}/{rid}/o/{sub}.loop/bench.{rest}"
        else:
            new = f"{RUN}/{rid}/o/{sub}/bench.{rest}"
        if not os.path.exists(new):
            res["data_vs_baseline"]["missing"].append(b)
        elif open(p, "rb").read() == open(new, "rb").read():
            res["data_vs_baseline"]["same"] += 1
        else:
            res["data_vs_baseline"]["diff"].append(b)
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("logs", len(res["logs"]), "default", sum(v["default_line"] for v in res["logs"].values()), "spiceinit0", sum(v["spiceinit_bytes"] == 0 for v in res["logs"].values()))
print("cir same as OP-3", sum(res["cir_vs_op3"].values()), "/", len(res["cir_vs_op3"]))
print("compat", set(res["compat_sha"].values()))
print("sim_vs_op3", res["sim_vs_op3"])
print("data", res["data_vs_baseline"]["same"], res["data_vs_baseline"]["diff"], res["data_vs_baseline"]["missing"])
