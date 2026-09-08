# -*- coding: utf-8 -*-
"""diode가 **W 한계 안에서 허용하는 vds 구간**을 재는 조사 도구(2026-09-08, B16 후속).

B1 5단계 배선을 하다 막힌 지점의 근거다. diode는 `Vgs = Vds`가 강제되므로, `L/ID/vsb`가
정해지면 vds 하나가 gm_id를 정하고 gm_id가 W를 정한다:

    W(v) = L * ID / IDu( gm_id_for_vgs(v, L, v, vsb), L, v, vsb )

즉 **diode의 vds는 헤드룸이 나눠줄 수 있는 몫이 아니다** -- 그건 W를 고르는 것과 같은 일이다.
현재 헤드룸은 role 기반 상수(min_vds_by_role, 기본 0.2V)를 그대로 주는데, 배선하고 나니
M11a가 vds=0.2V에서 **W=403m**를 요구했다(=그 vds로는 그 전류를 못 흘린다).

그럼 각 diode가 **낼 수 있는 vds 범위**는 얼마인가? W(v)는 v에 대해 단조감소(전압이 높을수록
전류밀도가 커져 같은 ID에 더 좁은 소자면 된다)이므로, W_bounds가 곧 vds 구간으로 번역된다.
이 표가 있어야 "헤드룸이 diode에게 줄 수 있는 몫"을 제대로 제약할 수 있다.

실행: assets 디렉터리에서 `python tests/probe_diode_vds_window.py`
"""
import sys
import os
import json

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr

TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
INST = (r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces"
        r"\current-reuse-telescopic-ota-report\current_reuse_telescopic_ota.instance.json")
W_BOUNDS = (1e-6, 200e-6)

trs, meta = sr.load_topology(TOPO)
by = {t.name: t for t in trs}
diode = sorted(n for n, t in by.items() if sr.is_diode_connected(t))
sized = json.load(open(INST, encoding="utf-8"))["sizing"]
for v in sized.values():
    if "vs" in v and "vsb" not in v:
        v["vsb"] = v.pop("vs")

npz = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(npz["L"], npz["VGS"], npz["VDS"], npz["VS"],
                                        npz["ID_" + k], npz["GM_" + k], npz["GDS_" + k],
                                        npz["CGG_" + k], W_ref=5e-6)
lut = {"nmos": mk("n"), "pmos": mk("p")}
VDS_GRID = [float(x) for x in npz["VDS"]]


def w_at(kind, L, ID, vsb, v):
    g = lut[kind].gm_id_for_vgs(v, L, v, vsb)
    idu = lut[kind].gm_id_to_id_density(g, L, v, vsb)
    if idu <= 0:
        raise ValueError("IDu<=0")
    return L * ID / idu, g


print("W 한계 %.3g~%.3g um 안에서 각 diode가 허용하는 vds 구간" % (W_BOUNDS[0] * 1e6, W_BOUNDS[1] * 1e6))
print("(L/ID/vsb는 현재 파일럿 산출물 값을 그대로 사용 -- 재탐색하면 달라진다)")
print()
print("%-8s %-5s %-8s %-9s %-8s | %-9s %-9s | %-9s %s"
      % ("소자", "kind", "L(um)", "ID(uA)", "현재vds", "vds 하한", "vds 상한", "폭(V)", "현재vds 판정"))
print("-" * 96)
rows = []
for n in diode:
    e = sized.get(n)
    if not e:
        continue
    kind, L, ID, vsb = e["kind"], e["L"], e["ID"], e.get("vsb", 0.0)
    lo = hi = None
    for v in VDS_GRID:
        if v <= 0:
            continue
        try:
            w, _ = w_at(kind, L, ID, vsb, v)
        except (ValueError, KeyError):
            continue
        if W_BOUNDS[0] <= w <= W_BOUNDS[1]:
            lo = v if lo is None else min(lo, v)
            hi = v if hi is None else max(hi, v)
    cur = e.get("vds")
    if lo is None:
        verdict = "★가능한 vds 없음"
        rows.append((n, lo, hi))
        print("%-8s %-5s %-8.3f %-9.4f %-8.4f | %-9s %-9s | %-9s %s"
              % (n, kind, L * 1e6, ID * 1e6, cur, "-", "-", "-", verdict))
        continue
    inside = lo <= cur <= hi
    verdict = "OK" if inside else ("★너무 낮음" if cur < lo else "★너무 높음")
    rows.append((n, lo, hi))
    print("%-8s %-5s %-8.3f %-9.4f %-8.4f | %-9.4f %-9.4f | %-9.4f %s"
          % (n, kind, L * 1e6, ID * 1e6, cur, lo, hi, hi - lo, verdict))

ok = [r for r in rows if r[1] is not None]
print()
print("가능한 vds 구간이 존재하는 diode: %d/%d개" % (len(ok), len(rows)))

# 스택별로: diode 하한의 합만으로 예산을 넘는가
print()
print("=== 스택별: diode의 vds 하한 합이 예산 안에 들어가는가 ===")
roles = meta.get("device_roles", {})
lo_by = {n: lo for n, lo, _ in rows if lo is not None}
groups = {}
for n in sized:
    vsid = (roles.get(n) or {}).get("vertical_stack_id")
    if vsid:
        groups.setdefault(vsid, []).append(n)
VDD = 1.8
bad = 0
for vsid in sorted(groups):
    members = sorted(groups[vsid])
    ds = [m for m in members if m in lo_by]
    if not ds:
        continue
    nd = [m for m in members if m not in set(diode)]
    d_lo = sum(lo_by[m] for m in ds)
    nd_cur = sum((sized[m].get("vds") or 0.0) for m in nd)
    over = d_lo + nd_cur - VDD
    flag = "★초과 %+.3fV" % over if over > 1e-9 else ""
    if over > 1e-9:
        bad += 1
    print("  %-28s diode하한합=%.4f (%d개) + 비diode현재합=%.4f = %.4f / %.1f %s"
          % (vsid, d_lo, len(ds), nd_cur, d_lo + nd_cur, VDD, flag))
print()
print("diode 하한만으로도 예산을 넘는 스택: %d개" % bad)
