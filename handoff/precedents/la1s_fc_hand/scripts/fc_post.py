"""O-255 (5) 확인 루프: 레이아웃 뒤 SPICE 재평가 두 가지.
  (a) 기하만: 손가락별 ad/as/pd/ps 를 추출 넷리스트 값(소자 합 / 손가락 수)으로 바꾼다.
  (b) 기하 + 배선 기생 근사: (a) + 넷별 대지 C(배선 층 면적·둘레 × PDK 추출 계수) + gate li 버스 직렬 R(시트 저항 ×
      L/W 의 1/3, 고르게 분포한 RC 선의 Elmore 등가).
PDK 계수(값은 여기서 쓰지 않고 파일에서 줄 번호로 읽는다): C:/pdk/open_pdks_sky130_magic/sky130.tech extract style
ngspice 첫 변형 -- defaultareacap / defaultperimeter (aF/um^2, aF/um), resist (mOhm/sq).
usage: fc_post.py <design_frozen.json> <extracted.cir> <pex.json> <tag>
"""
import copy, json, re, sys
import fc_spice as SP

TECH = "C:/pdk/open_pdks_sky130_magic/sky130.tech"
# (층, magic 층 이름, 면적 줄, 둘레 줄, 저항 줄)
LINES = {"poly_f": ("*poly", 5622, 5623, 5397), "li": ("allli", 5629, 5630, 5400),
         "met1": ("allm1", 5645, 5646, 5401), "met2": ("allm2", 5671, 5672, 5402)}


def tech_line(n):
    with open(TECH, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if i == n:
                return line
    raise KeyError(n)


def coeffs():
    c = {}
    for k, (mag, la, lp, lr) in LINES.items():
        a, p, r = tech_line(la), tech_line(lp), tech_line(lr)
        assert "defaultareacap" in a and mag in a, (la, a)
        assert "defaultperimeter" in p and mag in p, (lp, p)
        assert "resist" in r, (lr, r)
        c[k] = {"area_aF_um2": float(a.split()[-1]), "perim_aF_um": float(p.split()[-1]),
                "rs_ohm_sq": float(r.split()[-1]) / 1000.0, "src": [la, lp, lr]}
    return c


des = json.load(open(sys.argv[1], encoding="utf-8"))
txt = open(sys.argv[2], encoding="utf-8").read().replace("\n+", " ")
pex = json.load(open(sys.argv[3], encoding="utf-8"))
tag = sys.argv[4]
ext = []
for line in txt.splitlines():
    if line.startswith("M"):
        t = line.split()
        kv = dict(x.split("=") for x in t[6:])
        ext.append({"d": t[1].replace("\\", ""), "g": t[2].replace("\\", ""), "s": t[3].replace("\\", ""), "model": t[5],
                    **{k.upper(): float(v) for k, v in kv.items()}})
model = {"nmos": "sky130_fd_pr__nfet_01v8", "pmos": "sky130_fd_pr__pfet_01v8"}
geo = copy.deepcopy(des)
table = []
used = set()
for n, d in des["devices"].items():
    if d.get("dummy"):
        continue
    W = d["w_s"] * d["m"] * 1e6
    cand = [i for i, e in enumerate(ext) if i not in used and e["model"] == model[d["kind"]] and abs(e["L"] - d["L"] * 1e6) < 1e-6
            and abs(e["W"] - W) < 1e-6 and e["g"] == d["g"] and {e["d"], e["s"]} == {d["d"], d["s"]}]
    if len(cand) != 1:
        raise RuntimeError("match %s: %d" % (n, len(cand)))
    e = ext[cand[0]]
    used.add(cand[0])
    m = d["m"]
    # 추출기는 AS = AD 평균(병합 소자) -- 손가락마다 같은 값으로
    fg = {"ad": e["AD"] * 1e-12 / m, "as": e["AS"] * 1e-12 / m, "pd": e["PD"] * 1e-6 / m, "ps": e["PS"] * 1e-6 / m}
    geo["devices"][n]["finger_geom"] = [dict(fg) for _ in range(m)]
    hand = {t: sum(f[t] for f in d["finger_geom"]) for t in ("ad", "as", "pd", "ps")}
    table.append((n, m, e["W"], e["L"], e["AD"], e["AS"], e["PD"], e["PS"], hand))
# 더미: 같은 규칙(추출 소자 중 남은 것은 더미) -- 손가락 기하는 손 값 유지
co = coeffs()
cnet, rgate = {}, {}
for net, rec in pex.items():
    c = 0.0
    for k in ("poly_f", "li", "met1", "met2"):
        c += rec[k]["area_um2"] * co[k]["area_aF_um2"] + rec[k]["perim_um"] * co[k]["perim_aF_um"]
    cnet[net] = c * 1e-18
    lg = rec["li"]["longest"]
    if lg and lg[1] > 0:
        rgate[net] = co["li"]["rs_ohm_sq"] * lg[0] / lg[1] / 3.0
rser = {}
for n, d in des["devices"].items():
    if d.get("dummy"):
        continue
    if d["g"] in rgate and d["g"] not in ("vdd", "gnd"):
        rser["%s.g" % n] = rgate[d["g"]]
sim = des["sim"]
json.dump(geo, open("../out/post/%s_design_geom.json" % tag, "w", encoding="utf-8"), indent=1)
ra = SP.run(SP.netlist(geo, sim), "../out/post", tag + "_geom")
extra = {"cnet": {k: v for k, v in cnet.items()}, "rser": rser}
rb = SP.run(SP.netlist(geo, sim, extra), "../out/post", tag + "_geom_rc")
rc_only = SP.run(SP.netlist(geo, sim, {"cnet": extra["cnet"]}), "../out/post", tag + "_geom_c")
rr_only = SP.run(SP.netlist(geo, sim, {"rser": rser}), "../out/post", tag + "_geom_r")
pre = SP.run(SP.netlist(des, sim), "../out/post", tag + "_pre")
out = {"pre": pre, "geom": ra, "geom_rc": rb, "geom_c": rc_only, "geom_r": rr_only, "cnet_fF": {k: v * 1e15 for k, v in cnet.items()}, "rser_ohm": rser, "coeffs": co,
       "ext_vs_hand": [{"dev": t[0], "m": t[1], "W_um": t[2], "L_um": t[3], "AD": t[4], "AS": t[5], "PD": t[6], "PS": t[7],
                        "hand_ad_um2": t[8]["ad"] * 1e12, "hand_as_um2": t[8]["as"] * 1e12, "hand_pd_um": t[8]["pd"] * 1e6,
                        "hand_ps_um": t[8]["ps"] * 1e6} for t in table],
       "margins": {k: SP.sat_margins(v, des) for k, v in (("pre", pre), ("geom", ra), ("geom_rc", rb), ("geom_c", rc_only), ("geom_r", rr_only))}}
json.dump(out, open("../out/post/%s.json" % tag, "w", encoding="utf-8"), indent=1)
with open("../out/post/%s.txt" % tag, "w", encoding="utf-8") as f:
    for k in ("pre", "geom", "geom_c", "geom_r", "geom_rc"):
        r = out[k]
        mar = {n: v for n, v in out["margins"][k].items() if not n.startswith("DUM")}
        f.write("%-8s A0 %.3f dB  GBW %.4f MHz  PM %.3f  P %.3f uW  out %.4f  min margin %.4f (%s)\n" % (
            k, r["a0db"], r["fu"] / 1e6, r["pm"], r["power_W"] * 1e6, r["out"], min(mar.values()), min(mar, key=mar.get)))
    f.write("net C (fF): %s\n" % {k: round(v, 2) for k, v in out["cnet_fF"].items()})
    f.write("gate R (ohm, lumped): %s\n" % {k: round(v, 1) for k, v in rgate.items()})
