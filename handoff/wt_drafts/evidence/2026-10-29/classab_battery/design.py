# θ 기저 손계산(설계 방향)으로 class-AB 배터리 고리를 닫고, 같은 W 로 전체 벤치를 돌려 정지 전류·분배를 대조한다.
# 손계산 = 소자 하나 ngspice .dc (LUT 와 같은 단일 소자 특성, 단자 전압은 손계산 노드전압) -- 엔진 LUT 조회의 대용.
# 독립: I_Q, I9a, I9b(θ 전류), M15·M16·M11a·M11b·M14a·M14b 치수(θ 좌표 대용); 종속: M9a·M9b W(고리 KVL 로 결정, DEC-64 ①②).
# 결과 append: results.jsonl / design_out.json
import json, subprocess, pathlib, sys, math
import numpy as np
import bench as B

HERE = pathlib.Path(__file__).parent
VDD = 1.8


def dev_sweep(kind, w, l, vd, vs, vb, corner="tt", temp=27, tag=None):
    """게이트 전압을 훑어 (VG, ID) -- 단자 전압 고정, 단일 소자."""
    tag = tag or f"{kind}_{w:.4g}_{l}_{vd:.3f}_{vs:.3f}_{vb:.3f}_{corner}_{temp}"
    wd = HERE / "runs" / "char" / tag
    wd.mkdir(parents=True, exist_ok=True)
    sub = "sky130_fd_pr__nfet_01v8" if kind == "n" else "sky130_fd_pr__pfet_01v8"
    n = f"* char\n{B.models(corner)}.temp {temp}\n"
    n += f"vd d 0 {vd}\nvs s 0 {vs}\nvb b 0 {vb}\nvg g 0 0\n"
    n += f"X1 d g s b {sub} {B.geom(w, l)}\n"
    n += ".options gmin=1e-15 abstol=1e-16\n.control\nset filetype=ascii\n"
    n += "dc vg -1.8 1.8 0.0005\nwrdata sw.txt i(vd)\nquit\n.endc\n.end\n"
    (wd / "c.cir").write_text(n)
    if (wd / "sw.txt").exists():
        (wd / "sw.txt").unlink()
    subprocess.run([B.NG, "-b", "c.cir"], cwd=wd, capture_output=True)
    a = np.loadtxt(wd / "sw.txt")
    vg, idd = a[:, 0], np.abs(a[:, 1])
    return vg, idd


def vg_at(kind, w, l, i, vd, vs, vb, **kw):
    vg, idd = dev_sweep(kind, w, l, vd, vs, vb, **kw)
    li = np.log(idd + 1e-30)
    if kind == "n":
        return float(np.interp(math.log(i), li, vg))
    order = np.argsort(li)                      # pmos: 게이트 낮을수록 전류 큼
    return float(np.interp(math.log(i), li[order], vg[order]))


def w_for_vg(kind, l, i, vg_target, vd, vs, vb, w0=1.0, **kw):
    """같은 단자 전압에서 ID(W) 가 i 가 되는 W -- 전류 밀도 비례 1회 + 실제 W 재조회 1회 보정."""
    w = w0
    for _ in range(3):
        vg, idd = dev_sweep(kind, w, l, vd, vs, vb, **kw)
        i_w = float(np.exp(np.interp(vg_target, vg, np.log(idd + 1e-30))))
        w = w * i / i_w
    return w


def hand(IQ=20e-6, I9a=0.6e-6, I9b=0.6e-6, I11=2.2e-6, I14=2.5e-6, sizes=None, corner="tt", temp=27):
    S = dict(B.SIZES) if sizes is None else dict(sizes)
    k, w, l = S["M15"]; vg15 = vg_at("p", w, l, IQ, 0.9, VDD, VDD)                # M15 S=vdd D=Vom(0.9)
    k, w, l = S["M16"]; vop1 = vg_at("n", w, l, IQ, 0.9, 0.0, 0.0)                # M16
    # 다이오드 사슬(자기 참조 VDS = VGS): 1회 고정점 x2
    k, w, l = S["M11a"]; x = 1.0
    for _ in range(4):
        x = vg_at("p", w, l, I11, x, VDD, VDD)
    n11a = x
    k, w, l = S["M11b"]; y = n11a - 0.6
    for _ in range(4):
        y = vg_at("p", w, l, I11, y, n11a, VDD)
    n11b = y
    k, w, l = S["M14b"]; u = 0.5
    for _ in range(4):
        u = vg_at("n", w, l, I14, u, 0.0, 0.0)
    n14ab = u
    k, w, l = S["M14a"]; z = n14ab + 0.6
    for _ in range(4):
        z = vg_at("n", w, l, I14, z, n14ab, 0.0)
    n14a = z
    # 종속: M9a (S=Vg15, D=Vop1, G=N11b, B=vdd), M9b (S=Vop1, D=Vg15, G=N14a14b, B=0)
    k, w, l = S["M9a"]; w9a = w_for_vg("p", l, I9a, n11b, vop1, vg15, VDD, w0=w)
    k, w, l = S["M9b"]; w9b = w_for_vg("n", l, I9b, n14a, vg15, vop1, 0.0, w0=w)
    S["M9a"] = ("p", round(w9a, 3), S["M9a"][2]); S["M9b"] = ("n", round(w9b, 3), S["M9b"][2])
    nodes = dict(vg15=vg15, vop1=vop1, n11a11b=n11a, n11b=n11b, n14a_14b=n14ab, n14a14b=n14a,
                 vbat=vg15 - vop1, vsg9a=vg15 - n11b, vgs9b=n14a - vop1)
    return S, nodes


if __name__ == "__main__":
    IQ = float(sys.argv[1]) if len(sys.argv) > 1 else 20e-6
    S, nodes = hand(IQ=IQ)
    B.SIZES.clear(); B.SIZES.update(S)
    B.I8 = B.I10 = 1.2e-6; B.I12 = 2.2e-6; B.I13 = 2.5e-6
    r = B.op(f"design_tt27_IQ{IQ*1e6:.0f}u")
    out = dict(hand_nodes=nodes, sizes=S, spice_nodes=r["nodes"],
               spice=dict(I15=r["dev"]["m15.id"], I16=r["dev"]["m16.id"], I9a=r["dev"]["m9a.id"], I9b=r["dev"]["m9b.id"]))
    with open(HERE / "design_out.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(out) + "\n")
    print(json.dumps(out, indent=1))
