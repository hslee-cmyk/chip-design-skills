# spice_ref.jsonl -> 기준점 x0 에서 위·아래로 영역 행 창 끝(포화 VDS = VDSAT, O-204·O-205 (3))과 기능 기준 후보별 창 끝(선형 보간).
# 후보: A = 창 안 점별 증분 DC 이득 >= spec gain_ss_db 하한(value_from_constraint, 허용 저하 = G(x0) - 하한),
#       B(X) = G(x0) - X dB (X = 측정 매개변수 1·3·6 dB -- 사용자 선언 꼴의 예시, 값 권고 아님). 결과는 케이스마다 append.
import json, math, pathlib, sys
HERE = pathlib.Path(__file__).parent
R = [json.loads(l) for l in (HERE / "spice_ref.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
spec = json.loads(pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library/"
                               r"nmcnr_amplifier.sizing_spec.json").read_text(encoding="utf-8"))["human"]
GMIN = [c["value"] for c in spec["constraints"] if c["metric"] == "gain_ss_db"][0]
OUT = HERE / "analyze_ref.jsonl"


def app(rec):
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))


def cross(P, i0, step, f):
    """i0 에서 step 방향으로 f(p) 가 처음 거짓이 되는 x(직전 참 점과 선형 보간). 끝까지 참이면 ('rail', x_last)."""
    i = i0
    while 0 <= i + step < len(P):
        a, b = P[i], P[i + step]
        va, vb = f(a), f(b)
        if vb is None or vb < 0:
            if vb is None or va is None:
                return ("undef", b["x"])
            t = va / (va - vb)
            return ("cross", a["x"] + t * (b["x"] - a["x"]))
        i += step
    return ("rail", P[i]["x"])


for tag in sorted({r["tag"] for r in R if r["case"] == "design"}):
    d = [r for r in R if r["case"] == "design" and r["tag"] == tag][-1]
    P = sorted([r for r in R if r["case"] == "point" and r["tag"] == tag], key=lambda r: r["x"])
    i0 = min(range(len(P)), key=lambda i: abs(P[i]["x"] - d["X0"]))
    g0 = P[i0].get("gain_db")
    sat = lambda p: p.get("min_slack", [None, None])[1]
    out = {"tag": tag, "L": d["L"], "X0": d["X0"], "VOUT0": d["VOUT0"], "gmid_pair": d["gmid"]["M102"], "gmid_M101": d["gmid"]["M101"],
           "G0_db": g0, "slack0": P[i0].get("min_slack"), "sat_fail0": P[i0].get("sat_fail"), "spec_gain_min_db": GMIN}
    up = cross(P, i0, +1, sat); dn = cross(P, i0, -1, sat)
    def who(xe, step):
        j = min(range(len(P)), key=lambda i: abs(P[i]["x"] - xe))
        j = min(max(j, 0), len(P) - 1)
        return P[j].get("min_slack")
    out["region_hi"] = [up[0], up[1], who(up[1], 1)]; out["region_lo"] = [dn[0], dn[1], who(dn[1], -1)]
    crit = {"A_spec_floor": (lambda p: None if p.get("gain_db") is None else p["gain_db"] - GMIN)}
    for X in (1.0, 3.0, 6.0):
        crit["B_%gdB" % X] = (lambda X: (lambda p: None if p.get("gain_db") is None or g0 is None else p["gain_db"] - (g0 - X)))(X)
    for name, f in crit.items():
        if g0 is None or f(P[i0]) is None or f(P[i0]) < 0:
            out[name] = "nominal_fail_or_undef"
            continue
        hi = cross(P, i0, +1, f); lo = cross(P, i0, -1, f)
        ihi = min(up[1], hi[1]); ilo = max(dn[1], lo[1])
        out[name] = {"func_lo": lo, "func_hi": hi, "icmr_lo": ilo, "icmr_hi": ihi, "icmr_width_v": ihi - ilo,
                     "binding_hi": "region" if up[1] <= hi[1] else "function", "binding_lo": "region" if dn[1] >= lo[1] else "function"}
    app(out)
    print(json.dumps(out, ensure_ascii=False))
