"""[EO-1 범위 4] `off` 선언 ss 층 test 공용 -- 합성 회로·합성 LUT·손계산 기대값 (interface card 20261104-eo1r4-sf1l §4, T-O*·T-G*·T-N1).

피검 함수로 기대값을 만들지 않는다. 기대값 출처:
* (손) sizing conftest 의 r4 합성 LUT 해석식: ln IDu = ln I0 + B·VGS − C·VGS²/2 + LAM·VDS − A·VS²(L 무관), GM/ID = B − C·VGS, GDS = LAM·ID.
  VGS = 0·VSB = 0(격자점)에서는 IDu = I0·exp(LAM·VDS) 로 닫힌 식이고 GDS 열은 (ln 선형이라) VDS 어디서나 정확히 LAM·ID 이다.
* (식) card §4 의 식: ΔI_off = IDu·w_m/l_m, 주입(nmos: drain -ΔI, source +ΔI / pmos: 반대), G·ΔV = 주입.
* gds 같은 다른 MOS 의 소신호 값은 metrics conftest 의 독립 numpy 보간(`multilinear`)으로 r4 npz 배열에서 직접 계산한다.
입력 생성(회로·spec·θ)은 공개 API 를 쓴다. 두 객체는 `fresh_run()` 한 쌍을 한 사례(case)에 쓴다.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.graph import build_s1
from gmid_engine.metrics import metric_catalog, ss_evaluate
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, size_and_seal

from sizing.conftest import I0, LAM, W_M, kschema, r4_arrays, r4_ln_idu, write_r4_lut

from .conftest import fresh_run, lut_access, multilinear, spec_json, toy_junction, topo_doc

OFF_SRC = {"kind": "user_spec", "record": "off ss test fixture", "decided": "2026-11-04"}
BASE_RAILS = {"vdd": 1.8, "gnd": 0.0}

CONS = (
    ("gain_ss_db", ">=", 20.0, None),
    ("rout_ss_ohm", "<=", 1e6, None),
    ("power_dc_w", "<=", 1e-3, None),
    ("area_search_m2", "<=", 1e-9, None),
)
CONS_FULL = CONS + (
    ("gain_ss_db", "<=", 80.0, None),
    ("pm_ss_deg", ">=", 45.0, None),
    ("parasitic_pm_ss_deg", ">=", 45.0, None),
)


def off_entry(w_m=1e-6, l_m=1e-6, judged=("gain_ss_db",)):
    return {"region": "off", "w_m": w_m, "l_m": l_m, "judged_by": list(judged), "source": dict(OFF_SRC)}


def tri_entry():
    return {"region": "triode", "source": dict(OFF_SRC)}


# ---- 회로 ------------------------------------------------------------------------------------------------------

def circuit_a(off, name="off_a", rails=()):
    """A: M1 nmos (out, in, gnd) + R1 (vdd, out) + CL (out, gnd) + off 소자들. off = [(이름, kind, d, g, s, b)]. rails = 추가 레일 이름."""
    mos = [("M1", "nmos", "out", "in", "gnd", "gnd")] + list(off)
    return topo_doc(name, mos=mos, passives=[("R1", "resistor", "vdd", "out"), ("CL", "capacitor", "out", "gnd")],
                    rails=("vdd", "gnd") + tuple(rails))


def circuit_p(off, name="off_p", rails=()):
    """P: M1 pmos (out, in, vdd) + R1 (out, gnd) + CL (out, gnd) + off 소자들. V(out) = I·R."""
    mos = [("M1", "pmos", "out", "in", "vdd", "vdd")] + list(off)
    return topo_doc(name, mos=mos, passives=[("R1", "resistor", "out", "gnd"), ("CL", "capacitor", "out", "gnd")],
                    rails=("vdd", "gnd") + tuple(rails))


def circuit_s(off, name="off_s"):
    """S: M1 nmos (out, in, ss, gnd) + Rs (ss, gnd) + R1 (vdd, out) + CL (out, gnd) + off 소자들. 소스 노드 ss 가 움직인다(ΔVSB·ΔVGS 항 시험)."""
    mos = [("M1", "nmos", "out", "in", "ss", "gnd")] + list(off)
    return topo_doc(name, mos=mos,
                    passives=[("R1", "resistor", "vdd", "out"), ("Rs", "resistor", "ss", "gnd"),
                              ("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"))


def circuit_two(off, name="off_two"):
    """TWO: 왼쪽 가지 = A (노드 out), 오른쪽 가지 = P 꼴 (M2 pmos (mid, pb, vdd) + R2 (mid, gnd), 노드 mid), off 소자는 out 과 mid 사이."""
    mos = [("M1", "nmos", "out", "in", "gnd", "gnd"), ("M2", "pmos", "mid", "pb", "vdd", "vdd")] + list(off)
    return topo_doc(name, mos=mos,
                    passives=[("R1", "resistor", "vdd", "out"), ("R2", "resistor", "mid", "gnd"),
                              ("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"), bias=("pb",))


# ---- θ ------------------------------------------------------------------------------------------------------------

def theta_from_schema(ctx, points, currents, resistances, l=1e-6):
    """스키마(입력)가 정한 성분마다 값을 채운다. points = {MOS: (kind, vgs, vds, vsb)}, currents/resistances = {원소: 값}."""
    out = {}
    for comp in kschema(ctx).components:
        t, key = comp
        if t == "L":
            out[comp] = l
        elif t == "ln_idu":
            kind, vgs, vds, vsb = points[key]
            out[comp] = r4_ln_idu(kind, vgs, vds, vsb)
        elif t == "current":
            out[comp] = currents[key]
        elif t == "resistance":
            out[comp] = resistances[key]
        else:
            raise AssertionError("test 가 채우지 않는 θ 성분: %r" % (comp,))
    return out


def theta_a(ctx, i=1e-5, r=9e4, vgs=0.6):
    """회로 A 의 θ: V(out) = 1.8 - I·R, M1 이 vgs 가 나오는 좌표(VDS = V(out), VSB 0)."""
    return theta_from_schema(ctx, {"M1": ("nmos", vgs, 1.8 - i * r, 0.0)}, {"R1": i, "M1": i}, {"R1": r})


# ---- 사례 ---------------------------------------------------------------------------------------------------------

def build_case(tmp, topo, regions, theta_fn, rails=None, elements=None, constraints=CONS, extra_regions_cls=None):
    """topology·spec(intended_region = regions)·r4 LUT -> KernelContext -> size_and_seal. 반환 SimpleNamespace.
    regions = {소자: spec 항목 dict}. theta_fn(ctx) -> θ."""
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    tp = tmp / (topo["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(topo, indent=1), encoding="utf-8")
    td = load_topology(str(tp))
    sup = dict(BASE_RAILS if rails is None else rails)
    els = elements if elements is not None else (("R1", "resistor", None), ("CL", "capacitor", 1e-12))
    raw = spec_json(td, sup, els, (), constraints)
    raw["human"]["intended_region"] = dict(regions)
    sp = tmp / (topo["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(raw, indent=1), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, metric_catalog())
    inputs = dc_inputs_from_spec(spec)
    run = fresh_run()
    lut = write_r4_lut(tmp / "lut")
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs, lut_access(lut), **run)
    theta = theta_fn(ctx)
    ev = size_and_seal(ctx, theta)
    return SimpleNamespace(spec=spec, ctx=ctx, ev=ev, theta=theta, sealed=ev.sealed, rails=sup,
                           js=toy_junction(tmp / "junction", ctx.lut.memo.lut))


def evaluate(case):
    ac = tuple(sorted(n for n in case.rails if n != "gnd"))
    return ss_evaluate(case.sealed, case.ctx, case.theta, case.spec.constraints, ac, junction=case.js)


def graph_field(snapshot, name):
    """그래프 종류 필드 하나를 이름으로 찾는다(레코드 키를 test 가 정하지 않는다). 없으면 None."""
    for k in snapshot.keys("graph"):
        f = snapshot.field("graph", k, name)
        if f is not None:
            return f.value
    return None


def graph_key_of(snapshot, name):
    for k in snapshot.keys("graph"):
        if snapshot.field("graph", k, name) is not None:
            return k
    return None


# ---- 손계산 ------------------------------------------------------------------------------------------------------

def i_off(kind, vgs, vds, vsb, w_m, l_m):
    """card §4 ΔI_off = IDu·w_m/l_m, r4 합성 LUT 해석식(sizing conftest `r4_ln_idu`; VS 격자 위 값에서 정확)."""
    return math.exp(r4_ln_idu(kind, vgs, vds, vsb)) * w_m / l_m


def i_off_at_vgs0_vsb0(kind, vds, w_m, l_m):
    """VGS = 0, VSB = 0 의 닫힌 식: IDu = I0·exp(LAM·VDS)."""
    return I0[kind] * math.exp(LAM * vds) * w_m / l_m


def gds_lut(kind, L, vgs, vds, vsb, W):
    """다른 MOS 의 gds: r4 npz 의 GDS 열을 ln 다중선형 보간(독립 numpy, metrics conftest `multilinear`), 폭 W/w_slice 환산."""
    a = r4_arrays(kind)
    grids = (a["L"], a["VGS"], a["VDS"], a["VS"])
    return math.exp(multilinear(grids, np.log(a["GDS"]), (L, vgs, vds, vsb))) / W_M * W


def gds_off(dI):
    """VGS = 0·VSB = 0 의 off 소자 gds = LAM·ID (GDS 열 정의, ln 선형이라 VDS 어디서나 정확) = LAM·ΔI."""
    return LAM * dI
