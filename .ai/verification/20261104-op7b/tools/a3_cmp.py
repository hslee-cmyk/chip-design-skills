# -*- coding: utf-8 -*-
"""A3-4 비교: 새 오라클 sim/compare 대 OP-1b 기준선. 칸 대응 D §11.5, 분해능 D §18.3. 오라클 코드를 import 하지 않는다.
사용: a3_cmp.py <baseline_files> <run_a> <run_b> <out.json>
"""
import glob, json, math, os, sys

BL, RA, RB, OUT = sys.argv[1:5]
BIAS = {"R1": ["free"], "R2": ["free"], "R3": ["free", "forced"], "R4": ["free", "forced"], "R5": ["iso"]}
# 카드 제외 칸: 절대 경로, 캐시, method, 지문, 안정성 파일 칸 + [D-1] OP-4 비교로 넘긴 칸. log_errors = D §11.5 '옛 상태 칸' 제외
EXCL_KEYS = {"cache", "stability_cache", "ac_file", "log", "netlist", "method", "stability", "log_errors", "fingerprints"}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def walk(a, b, ptr, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k in EXCL_KEYS:
                continue
            if k not in a:
                out.append(("only_new", ptr + "/" + k, None, b[k]))
            elif k not in b:
                out.append(("only_old", ptr + "/" + k, a[k], None))
            else:
                walk(a[k], b[k], ptr + "/" + k, out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(("len", ptr, len(a), len(b)))
        for i in range(min(len(a), len(b))):
            walk(a[i], b[i], f"{ptr}/{i}", out)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        if float(a).hex() != float(b).hex():
            out.append(("num", ptr, a, b))
    elif a != b:
        out.append(("other", ptr, a, b))


def stem(rid, bias):
    return [p for p in glob.glob(os.path.join(BL, rid, "o", f"*.{bias}.sim.json"))][0]


res = {"pairs": {}, "two_runs": {}, "summary": {}}
for rid, biases in BIAS.items():
    for bias in biases:
        op = stem(rid, bias)
        base = os.path.basename(op)[:-len(".sim.json")]
        old = load(op)
        olc = load(op[:-len(".sim.json")] + ".compare.json")
        for run in (RA, RB):
            pass
        na = load(os.path.join(RA, rid, "o", base + ".sim.json"))
        nb = load(os.path.join(RB, rid, "o", base + ".sim.json"))
        nac = load(os.path.join(RA, rid, "o", base + ".compare.json"))
        nbc = load(os.path.join(RB, rid, "o", base + ".compare.json"))
        # 2회 비트 동일
        d2 = []
        walk(na, nb, "", d2)
        d2c = []
        walk(nac, nbc, "", d2c)
        res["two_runs"][f"{rid}.{bias}"] = {"sim": [x[1] for x in d2], "compare": [x[1] for x in d2c]}
        # 칸 대응
        o = json.loads(json.dumps(old))
        n = json.loads(json.dumps(na))
        o_status = o.pop("ngspice_rc", None)
        n_status = n.pop("status", None)
        rc_ok = (o_status == (n_status or {}).get("rc"))
        n.pop("instance_geometry_reported", None)      # 새 칸(기간 예외 표지, A3-6 이 읽음)
        if isinstance(o.get("loop"), dict):
            lo = o["loop"].pop("ngspice_rc", None)
            ln = (n.get("loop") or {}).pop("status", None)
            rc_ok = rc_ok and lo == (ln or {}).get("rc")
        # [D-1] 기간 비교 칸
        if isinstance(o.get("ac"), dict) and isinstance(n.get("ac"), dict):
            oa, na_ = o["ac"], n["ac"]
            pm_old, pm_new = oa.get("pm_deg_raw"), na_.get("pm_deg_raw")
            xc_old, xc_new = oa.get("pm_crosscheck_deg"), na_.get("pm_crosscheck_deg_raw")
            pm_ok = (pm_old is None and pm_new is None) or (pm_old is not None and pm_new is not None and float(pm_old).hex() == float(pm_new).hex())
            xc_ok = (xc_old is None and xc_new is None) or (xc_old is not None and xc_new is not None and float(xc_old).hex() == float(xc_new).hex())
            # OP-4 비교로 넘긴 칸 + 기간 표지 문장
            for k in ("pm_deg", "pm_deg_raw", "pm_undefined", "pm_crosscheck_deg", "pm_crosscheck_deg_raw", "pm_crosscheck_gap_deg",
                      "pm_crosscheck_note", "pm_open_loop_deg"):
                oa.pop(k, None)
                na_.pop(k, None)
        else:
            pm_ok = xc_ok = None
            pm_old = pm_new = xc_old = xc_new = None
        # ID 부호: 기준선 @id(크기) -> 새 signed_id = @id x sign(@vds). 기준선 쪽에 같은 식을 적용해 비교(옛 compare 와 같은 식)
        for name, row in (o.get("devices") or {}).items():
            if row.get("id") is not None and row.get("vds") is not None:
                row["id"] = row["id"] * (1.0 if row["vds"] > 0 else (-1.0 if row["vds"] < 0 else 0.0))
        diffs = []
        walk(o, n, "", diffs)
        # 연속 칸은 비트 비교. 다르면 기록(분해능 판단은 아래 표)
        cdiffs = []
        oc, nc = json.loads(json.dumps(olc)), json.loads(json.dumps(nac))
        walk(oc, nc, "", cdiffs)
        res["pairs"][f"{rid}.{bias}"] = {"rc_ok": rc_ok, "rc_old": o_status, "rc_new": (n_status or {}).get("rc"), "pm_ok": pm_ok, "xc_ok": xc_ok,
                                         "pm": [pm_old, pm_new], "xc": [xc_old, xc_new],
                                         "verdict": [olc["summary"]["verdict"], nac["summary"]["verdict"]],
                                         "blockers": [len(olc.get("blockers") or []), len(nac.get("blockers") or [])],
                                         "sim_diffs": diffs, "compare_diffs": cdiffs}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)
for k, v in res["pairs"].items():
    print(k, "rc", v["rc_ok"], v["rc_old"], v["rc_new"], "pm", v["pm_ok"], "xc", v["xc_ok"], "verdict", v["verdict"], "blockers", v["blockers"],
          "sim_diffs", len(v["sim_diffs"]), "cmp_diffs", len(v["compare_diffs"]))
    for t in v["sim_diffs"][:60]:
        print("   S", str(t)[:230])
print("two_runs", {k: (len(v["sim"]), len(v["compare"])) for k, v in res["two_runs"].items()})
