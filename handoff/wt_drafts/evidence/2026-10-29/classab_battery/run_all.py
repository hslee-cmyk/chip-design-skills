# (a) 루프 전압 섭동 감도 (b) 최소 전류 스윕 (c) PVT (d) 배터리 극점 AC -- 대표 동작점(rep_point). 결과: all_out.jsonl (케이스마다 append)
import json, pathlib, sys, math
import numpy as np
import bench as B
import rep_point as R
HERE = pathlib.Path(__file__).parent
OUT = HERE / "all_out.jsonl"


def put(rec):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec)[:600])


def sweep_il(tag):
    wd = HERE / "runs" / tag
    B.run(tag, B.netlist(sweep="il"), wd)
    a = np.loadtxt(wd / "sweep_out.txt")
    il = a[:, 0]
    cols = a[:, 1::2]
    i15, i16, i9a, i9b = (np.abs(cols[:, k]) for k in range(4))
    vop1, vg15, vom = cols[:, 4], cols[:, 5], cols[:, 6]
    ok = np.abs(vom - 0.9) < 1e-3                      # 서보가 Vom 을 잡는 구간만
    return il, i15, i16, i9a, i9b, vop1, vg15, vom, ok


def ac_pole(tag, **kw):
    wd = HERE / "runs" / tag
    # AC: Vop1 에 AC 전류 주입, Vom 은 큰 C 로 AC 단락(단락 전류 = 2단 Gm(f)); 서보는 1 F 저역이라 AC 에서 끊김
    extra = "iac 0 vop1 dc 0 ac 1\nvsh vom vshn dc 0\ncsh vshn 0 1\n"
    n = B.netlist(ac=True, extra=extra, **kw).replace("wrdata ac_out.txt v(vg15) v(vop1) v(vom)",
                                                      "wrdata ac_out.txt v(vg15) v(vop1) i(vsh)")
    B.run(tag, n, wd)
    a = np.loadtxt(wd / "ac_out.txt")
    f = a[:, 0]
    vg15 = a[:, 1] + 1j * a[:, 2]
    vop1 = a[:, 4] + 1j * a[:, 5]
    ish = a[:, 7] + 1j * a[:, 8]
    return f, vg15 / vop1, ish / vop1


if __name__ == "__main__":
    what = sys.argv[1]
    S, nodes = R.setup()
    if what == "sens":
        base = B.op("sens_0")
        for d in (-0.01, -0.005, 0.005, 0.01):
            r = B.op(f"sens_p{d*1e3:+.0f}mV", delta=d)
            put(dict(case="loop_delta_pmos", delta_V=d, IQ=r["dev"]["m15.id"], IQ0=base["dev"]["m15.id"],
                     I9a=r["dev"]["m9a.id"], I9b=r["dev"]["m9b.id"],
                     dlnIQ_per_V=math.log(r["dev"]["m15.id"] / base["dev"]["m15.id"]) / d))
        dv = base["dev"]
        put(dict(case="gm_over_id", m15=dv["m15.gm"] / dv["m15.id"], m16=dv["m16.gm"] / dv["m16.id"],
                 m9a=dv["m9a.gm"] / dv["m9a.id"], m9b=dv["m9b.gm"] / dv["m9b.id"]))
    elif what == "imin":
        for (a_, b_) in ((0.6e-6, 0.6e-6), (0.3e-6, 0.9e-6), (0.9e-6, 0.3e-6)):
            S, nodes = R.setup(I9a=a_, I9b=b_)
            il, i15, i16, i9a, i9b, vop1, vg15, vom, ok = sweep_il(f"imin_{a_*1e9:.0f}_{b_*1e9:.0f}")
            k0 = int(np.argmin(np.abs(il)))
            IQ = float(i15[k0])
            src = ok & (il > 0)
            snk = ok & (il < 0)
            put(dict(case="imin", I9a_q=float(i9a[k0]), I9b_q=float(i9b[k0]), IQ=IQ,
                     il_range_ok=[float(il[ok].min()), float(il[ok].max())],
                     I16_min_when_sourcing=float(i16[src].min()), I15_min_when_sinking=float(i15[snk].min()),
                     ratio16=float(i16[src].min() / IQ), ratio15=float(i15[snk].min() / IQ),
                     weak_inv_pred16=float(i9b[k0] / (i9a[k0] + i9b[k0])), weak_inv_pred15=float(i9a[k0] / (i9a[k0] + i9b[k0])),
                     samples=[[float(x) for x in (il[j], i15[j], i16[j], i9a[j], i9b[j], vop1[j], vg15[j])]
                              for j in range(0, len(il), 15) if ok[j]]))
    elif what == "pvt":
        for corner in ("tt", "ff", "ss", "fs", "sf"):
            for temp in (-40, 27, 125):
                r = B.op(f"pvt_{corner}_{temp}", corner=corner, temp=temp)
                d = r["dev"]
                nd = r["nodes"]
                put(dict(case="pvt", corner=corner, temp=temp, IQ=d.get("m15.id"), I16=d.get("m16.id"), I9a=d.get("m9a.id"),
                         I9b=d.get("m9b.id"), vbat=(nd.get("vg15", float("nan")) - nd.get("vop1", float("nan"))), n11b=nd.get("n11b")))
    elif what == "ac":
        fu = 36.6e6     # 원문 식 (2) t_lln·ω_c = 6.9, t_lln = 30 ns -> 폐루프 대역 36.6 MHz (참고 주파수)
        for (a_, b_) in ((0.3e-6, 0.3e-6), (1.2e-6, 1.2e-6), (2.4e-6, 2.4e-6)):
            S, nodes = R.setup(I9a=a_, I9b=b_)
            r = B.op(f"ac_op_{a_*1e9:.0f}")
            f, H, G = ac_pole(f"ac_{a_*1e9:.0f}")
            Hm = np.abs(H)
            k3 = int(np.argmax(Hm < Hm[0] / math.sqrt(2)))
            ph = np.degrees(np.unwrap(np.angle(G / G[0])))
            d = r["dev"]
            ghand = d["m9a.gm"] + d["m9a.gmbs"] + d["m9b.gm"] + d["m9b.gmbs"] + d["m9a.gds"] + d["m9b.gds"]
            put(dict(case="battery_pole", I9=a_ + b_, f3dB_H=float(f[k3]), H0=float(Hm[0]),
                     G0=float(abs(G[0])), gm15_plus_gm16=d["m15.gm"] + d["m16.gm"], gm15=d["m15.gm"], gm16=d["m16.gm"],
                     phase_dip_G_deg_min=float(ph[f < 2e9].min()), f_at_dip=float(f[f < 2e9][int(np.argmin(ph[f < 2e9]))]),
                     phase_G_at_fu=float(np.interp(fu, f, ph)), fu=fu,
                     hand_g_bat=ghand, hand_C_m15_cgg=d["m15.cgg"],
                     hand_pole_cgg_only=ghand / (2 * math.pi * d["m15.cgg"])))
