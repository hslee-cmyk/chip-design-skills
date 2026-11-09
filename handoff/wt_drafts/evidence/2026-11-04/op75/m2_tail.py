# F-24 + A-24: 기준선 기록의 폐루프 noise 집계, n̂ 엄격 비교의 자릿수 잡음(시뮬레이터 호출 0). 결과 m2.jsonl
import glob, json, os
import numpy as np
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/docs-op75"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m2.jsonl")
open(OUT, "w").close()


def w(o):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")


ROOT = W + "/.ai/verification/20261016-op1-baseline"
cl, n = [], 0
KEYS = ("status", "top_extensions", "converged", "f_lo_hz", "f_hi_hz", "points_per_decade", "tail_bound_v2", "out_int_v2", "rel_resolution")


def walk(o, p):
    if isinstance(o, dict):
        if "top_extensions" in o:
            cl.append((os.path.relpath(p, ROOT), {k: o.get(k) for k in KEYS}))
        for v in o.values():
            walk(v, p)
    elif isinstance(o, list):
        for v in o:
            walk(v, p)


for p in glob.glob(ROOT + "/**/*.json", recursive=True):
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    walk(d, p)
    n += 1
seen = {}
for p, r in cl:
    seen.setdefault(json.dumps(r, sort_keys=True), (p, r))
w({"files_scanned": n, "closed_loop_records": len(cl), "distinct": len(seen)})
for p, r in seen.values():
    t = r.get("tail_bound_v2"); i = r.get("out_int_v2"); q = r.get("rel_resolution")
    w({"file": p, **r, "tail_over_eps_I": (t / (q * q * i)) if t and i and q else None})


def round_sig(x, d):
    return np.array([float(f"{v:.{d - 1}e}") for v in x])


for d in (7, 12, 15):
    for ppd in (10, 20, 80, 320):
        for dec_above in (1, 2, 3, 4, 5, 6):
            f0 = 1e3 * 10 ** dec_above
            f = f0 * 10 ** (np.arange(-2, 1) / ppd)
            bad = 0
            for sh in np.linspace(0, 1, 200):
                ff = f * 10 ** (sh / ppd)
                s = round_sig(1e-14 / (1 + (ff / 1e3) ** 2), d)
                g = -np.diff(np.log(s)) / np.diff(np.log(ff))
                bad += int(not (g[1] >= g[0]))
            w({"digits": d, "ppd": ppd, "decades_above_pole": dec_above, "strict_reject": bad, "of": 200})
