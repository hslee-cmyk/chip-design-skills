# 원문 설계점 근처 동작점(current_reuse class-AB 반쪽, kv1 oracle 20회 + classab_battery 대표점)에서
# '가장 큰 VGS 해' 규칙이 실제 동작점과 다른 VGS 를 고르는 사례 수. LUT r2(cubic 보간, kv1_tiebreak 와 같은 곡면).
# 판정(상수 없음): 실제 VGS x 에서 gm/ID 곡선 분지 위 max_{x'>x} g(x') >= g(x) 이면 더 큰 VGS 해가 있다 -> 규칙이 x 를 고르지 못한다.
# 결과 append: multiroot_ops.jsonl
import json, pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import kv1_tiebreak as K

HERE = pathlib.Path(__file__).parent
OUT = HERE / "multiroot_ops.jsonl"
SRC = dict(M15="vdd", M16="0", M9a="vg15", M9b="vop1", M11a="vdd", M11b="n11a11b", M14b="0", M14a="n14a_14b")


def check(kind, L, vgs, vds, vsb):
    g, lid = K.curve(kind, L, vds, vsb)
    p = int(np.argmax(g))
    v, gb = K.FINE[p:], g[p:]
    gx = float(np.interp(vgs, K.FINE, g))
    later = gb[v > vgs]
    shadow = bool(len(later) and later.max() >= gx)
    roots = None
    if shadow:
        d = gb - gx
        idx = np.where(d[:-1] * d[1:] <= 0)[0]
        roots = [float(v[i] + (v[i + 1] - v[i]) * d[i] / (d[i] - d[i + 1])) if d[i] != d[i + 1] else float(v[i]) for i in idx]
    return gx, shadow, roots


def main():
    if OUT.exists():
        OUT.unlink()
    n = ns = 0
    for line in (HERE / "results.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("case") != "spice" or "skipped" in r:
            continue
        tag = f"{r['outer']}_{r['point']}_{r['depP']}_{r['depN']}"
        dv = {}
        for ln in (K.RUNS / tag / "op_dev.txt").read_text(errors="replace").splitlines():
            import re
            m = re.match(r"\s*@m\.x(m\w+)\.msky130_fd_pr__[np]fet_01v8\[(\w+)\]\s*=\s*([-+0-9.eE]+)", ln)
            if m:
                dv[f"{m.group(1)}.{m.group(2)}"] = float(m.group(3))
        nodes = dict(r["spice_nodes"]); nodes["vdd"] = 1.8; nodes["0"] = 0.0
        for d, (kind, w, l) in r["sizes"].items():
            vgs, vds = abs(dv[f"{d.lower()}.vgs"]), abs(dv[f"{d.lower()}.vds"])
            vs = nodes[SRC[d]]
            vsb = (1.8 - vs) if kind == "p" else vs
            gx, sh, roots = check(kind, l * 1e-6, vgs, vds, vsb)
            n += 1; ns += sh
            with open(OUT, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(dict(run=tag, dev=d, kind=kind, L_um=l, vgs=vgs, vds=vds, vsb=vsb, gm_id_lut=gx,
                                         gm_id_spice=abs(dv[f"{d.lower()}.gm"] / dv[f"{d.lower()}.id"]), shadowed=sh, roots=roots,
                                         picked=None if not roots else max(roots))) + "\n")
    # classab_battery 대표점 M9a(앞 측정 design_out.jsonl): VSG 0.6847, VSD = vbat 0.300, VSB = VSG15
    gx, sh, roots = check("p", 0.15e-6, 0.6847, 0.300, 1.8 - 0.9243)
    n += 1; ns += sh
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(run="classab_battery_rep", dev="M9a", kind="p", L_um=0.15, vgs=0.6847, vds=0.300, vsb=1.8 - 0.9243,
                                 gm_id_lut=gx, shadowed=sh, roots=roots, picked=None if not roots else max(roots))) + "\n")
        fh.write(json.dumps(dict(summary=True, n_ops=n, n_shadowed=ns)) + "\n")
    print(n, ns)


if __name__ == "__main__":
    main()
