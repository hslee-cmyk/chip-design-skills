"""U7 test 공용 손 회로·독립 기준 풀이 (metrics CONTRACT 10절 test 입력 생성기).

피검 함수로 기대값을 만들지 않는다. 이 모듈은
* 이름 있는 손 소신호 회로(`SsCircuit`)·전달 뷰(`ViewDecl` mode transfer)·구조 입력(`BlockStruct`·`ViewStruct`·`FfStruct`)을 **구성**하고,
* 독립 기준 풀이 `ref_solve` 를 둔다: 소자 방정식(채널 전류 d->s = gm·(v_g − v_s) + gmb·(v_b − v_s) + gds·(v_d − v_s), 저항 (v_a − v_b)/R)
  으로 KCL 을 이 파일에서 직접 세워 numpy.linalg.solve 로 푼다. 엔진 스탬프(`mos_stamps`)·노달 helper(`_helpers_nodal`)를 쓰지 않는다
  (oracle (b) 다른 방법의 참조 구현 -- 엔진은 LU 1회 수반 해석, 이쪽은 주입마다 직접 정방향 풀이).
* `rename` 은 넷·소자 이름 전단사 + 노드 순서 뒤섞기(이름 전단사 불변 test 입력).
"""
from __future__ import annotations

import math

import numpy as np

from gmid_engine.authoring import ExciteSense, ViewDecl
from gmid_engine.metrics import (BlockStruct, FfStruct, MosSmallSignal, Resistor, SmallSignalCircuit, SsCircuit,
                                 ViewStruct)


def mos(label, d, g, s, b, gm, gds, gmb=0.0, cgs=0.0, cgd=0.0):
    """손 MOS 행(이름 단자)."""
    return dict(label=label, d=d, g=g, s=s, b=b, gm=gm, gds=gds, gmb=gmb, cgs=cgs, cgd=cgd)


def res(label, a, b, ohm):
    return dict(label=label, a=a, b=b, ohm=ohm)


def circuit(nets, mos_rows, res_rows=(), ground=(), inputs=()):
    """이름 단자 손 회로 -> `SsCircuit`(노드 = `nets` 순서 위치). 용량 없음(ω → 0 metric 만 다룬다)."""
    idx = {n: i for i, n in enumerate(nets)}
    m = tuple(MosSmallSignal(idx[r["d"]], idx[r["g"]], idx[r["s"]], idx[r["b"]], r["gm"], r["gmb"], r["gds"],
                             cgs=r["cgs"], cgd=r["cgd"], label=r["label"]) for r in mos_rows)
    rr = tuple(Resistor(idx[r["a"]], idx[r["b"]], r["ohm"], label=r["label"]) for r in res_rows)
    return SsCircuit(tuple(nets), SmallSignalCircuit(mos=m, resistors=rr), tuple(r["label"] for r in res_rows), (),
                     tuple(sorted(ground)), tuple(sorted(inputs)))


def transfer(excite, sense_p, sense_n=None):
    """전달 뷰 선언(mode transfer). `excite` = {넷: 가중}."""
    return ViewDecl("transfer", transfer=ExciteSense(tuple(sorted(excite.items())), sense_p, sense_n,
                                                     "single" if sense_n is None else "differential"))


def ref_solve(mos_rows, res_rows, fixed, inject=None):
    """독립 정방향 풀이. `fixed` = {넷: V}(고정 넷 -- 교류접지·구동), `inject` = {넷: 들어가는 전류 A}.
    미지수 = 고정이 아니고 채널·저항 단자가 닿은 넷. -> {넷: V}."""
    inject = dict(inject or {})
    nets = set(fixed)
    for r in mos_rows:
        nets |= {r["d"], r["g"], r["s"], r["b"]}
    for r in res_rows:
        nets |= {r["a"], r["b"]}
    touched = {r[t] for r in mos_rows for t in ("d", "s")} | {r[t] for r in res_rows for t in ("a", "b")}
    unknown = sorted(n for n in nets if n not in fixed and n in touched)
    pos = {n: i for i, n in enumerate(unknown)}
    a = np.zeros((len(unknown), len(unknown)))
    rhs = np.zeros(len(unknown))
    for n, amount in inject.items():
        if n in pos:
            rhs[pos[n]] += amount

    def add(row_net, coeff, col_net):
        # KCL 행 row_net 의 '나가는 전류' 항 coeff·v(col_net)
        if row_net not in pos:
            return
        if col_net in pos:
            a[pos[row_net], pos[col_net]] += coeff
        else:
            rhs[pos[row_net]] -= coeff * fixed.get(col_net, 0.0)

    for r in mos_rows:
        terms = ((r["g"], r["gm"]), (r["b"], r["gmb"]), (r["d"], r["gds"]), (r["s"], -(r["gm"] + r["gmb"] + r["gds"])))
        for col, coeff in terms:
            add(r["d"], coeff, col)            # 채널 전류가 d 에서 나간다
            add(r["s"], -coeff, col)           # s 로 들어온다
    for r in res_rows:
        g = 1.0 / r["ohm"]
        add(r["a"], g, r["a"])
        add(r["a"], -g, r["b"])
        add(r["b"], g, r["b"])
        add(r["b"], -g, r["a"])
    x = np.linalg.solve(a, rhs) if len(unknown) else np.zeros(0)
    out = {n: float(v) for n, v in fixed.items()}
    out.update({n: float(x[pos[n]]) for n in unknown})
    return out


def sense_of(volts, p, n=None):
    return volts.get(p, 0.0) - (0.0 if n is None else volts.get(n, 0.0))


def rename(nets, mos_rows, res_rows, net_map, dev_map, order_seed=1):
    """넷·소자 이름 전단사 + 노드 순서 뒤섞기. -> (nets', mos', res')."""
    f = lambda n: net_map.get(n, n)  # noqa: E731
    g = lambda d: dev_map.get(d, d)  # noqa: E731
    rng = np.random.default_rng(order_seed)
    new_nets = [f(n) for n in nets]
    rng.shuffle(new_nets)
    m2 = [dict(r, label=g(r["label"]), d=f(r["d"]), g=f(r["g"]), s=f(r["s"]), b=f(r["b"])) for r in mos_rows]
    r2 = [dict(r, label=g(r["label"]), a=f(r["a"]), b=f(r["b"])) for r in res_rows]
    m2.reverse()
    r2.reverse()
    return tuple(new_nets), tuple(m2), tuple(r2)


def par(*conductances):
    """병렬 컨덕턴스 합의 역수(Ω)."""
    return 1.0 / sum(conductances)


def db(x):
    return 20.0 * math.log10(abs(x))


def _has_field(cls, name):
    import dataclasses
    return name in {f.name for f in dataclasses.fields(cls)}


def block(key, inputs, outputs, nodes, kind="gain", stage=1, input_cells=(), members=()):
    """[UB-1] `members` = S1v 블록 소자 이름(MOS·수동소자) 정렬. 칸이 없는 판(base)에서는 칸 없이 만든다(그 판의 단정이 AssertionError 로 빨갛다)."""
    kw = {"members": tuple(sorted(members))} if members and _has_field(BlockStruct, "members") else {}
    return BlockStruct(tuple(key), kind, stage, tuple(inputs), tuple(outputs), tuple(nodes), tuple(input_cells), **kw)


def ff(fid, tap, merge, members, merge_block, bypassed, bypassed_input_cells):
    return FfStruct(fid, tap, merge, tuple(sorted(members)), tuple(merge_block), tuple(bypassed), tuple(bypassed_input_cells))


def vstruct(vid, excite, sense, blocks, ffs=(), input_cells=(), signal_devices=(), pole_nets=(), directions=(), ac_ground=()):
    """[UB-1] `ac_ground` = 그 뷰 교류접지 넷 정렬(칸이 없는 판에서는 칸 없이 만든다)."""
    kw = {"ac_ground": tuple(sorted(ac_ground))} if ac_ground and _has_field(ViewStruct, "ac_ground") else {}
    return ViewStruct(vid, tuple(sorted(excite.items())), tuple(sorted(sense)), tuple(blocks), tuple(ffs), tuple(input_cells),
                      tuple(sorted(signal_devices)), tuple(sorted(pole_nets)), tuple(directions), **kw)


def MetricStructure_of(*views):  # noqa: N802
    from gmid_engine.metrics import MetricStructure
    return MetricStructure(tuple(views))


# ---------------------------------------------------------------- 손 회로 묶음 (값은 test 입력 -- 기준값 아님)

# 저항 부하 차동쌍(이름 없음): M1(d om, g ip, s t), M2(d op, g im, s t), 꼬리 전류원 M3(d t, g vb, s gnd), 부하 R1(vdd-om)·R2(vdd-op).
DP_GM, DP_GDS, DP_R, DP_GDS_TAIL = 1e-3, 1e-5, 1e4, 2e-6


def diff_pair(gm=DP_GM, gds=DP_GDS, r=DP_R, gds_tail=DP_GDS_TAIL, gmb=0.0):
    nets = ("gnd", "vdd", "vb", "ip", "im", "t", "om", "op")
    m = (mos("M1", "om", "ip", "t", "gnd", gm, gds, gmb), mos("M2", "op", "im", "t", "gnd", gm, gds, gmb),
         mos("M3", "t", "vb", "gnd", "gnd", 5e-4, gds_tail))
    rr = (res("R1", "vdd", "om", r), res("R2", "vdd", "op", r))
    return nets, m, rr, ("gnd", "vdd", "vb"), ("im", "ip")


# 5T OTA: 입력쌍 M1(d x, g ip, s t)·M2(d out, g im, s t), 꼬리 M5(d t, g vb, s gnd), PMOS 미러 M3(diode d x, g x, s vdd)·M4(d out, g x, s vdd).
def ota5(gm1=1e-3, gm3=4e-4, gds_in=2e-6, gds_ld=3e-6, gds_tail=1e-6, gmb_in=1.5e-4, gm5=5e-4):
    nets = ("gnd", "vdd", "vb", "ip", "im", "t", "x", "out")
    m = (mos("M1", "x", "ip", "t", "gnd", gm1, gds_in, gmb_in), mos("M2", "out", "im", "t", "gnd", gm1, gds_in, gmb_in),
         mos("M3", "x", "x", "vdd", "vdd", gm3, gds_ld), mos("M4", "out", "x", "vdd", "vdd", gm3, gds_ld),
         mos("M5", "t", "vb", "gnd", "gnd", gm5, gds_tail))
    return nets, m, (), ("gnd", "vdd", "vb"), ("im", "ip")


# 단일 입력 캐스코드 CS: 입력 M1(d x, g in, s gnd), 캐스코드 Mc(d out, g vc, s x), PMOS 전류원 부하 Ml(d out, g vp, s vdd).
def cascode_cs(gm1=1e-3, gds1=2e-5, gmc=8e-4, gdsc=1.5e-5, gml=6e-4, gdsl=1e-5):
    nets = ("gnd", "vdd", "vc", "vp", "in", "x", "out")
    m = (mos("M1", "x", "in", "gnd", "gnd", gm1, gds1), mos("Mc", "out", "vc", "x", "gnd", gmc, gdsc),
         mos("Ml", "out", "vp", "vdd", "vdd", gml, gdsl))
    return nets, m, (), ("gnd", "vdd", "vc", "vp"), ("in",)


# 3단 CS 사슬 + 2단 우회 FF: in -M1-> v1 -M2-> v2 -M3-> out, 부하 R1~R3(→vdd), FF Mf(d out, g v1) -- 탭 v1, merge out, 처음 우회 블록 (v2,).
CH = dict(gm1=1e-3, gds1=1e-5, r1=5e4, gm2=8e-4, gds2=2e-5, r2=4e4, gm3=2e-3, gds3=3e-5, r3=2e4, gmf=6e-4, gdsf=4e-5)


def chain3(p=None, with_ff=True):
    p = dict(CH, **(p or {}))
    nets = ("gnd", "vdd", "in", "v1", "v2", "out")
    m = [mos("M1", "v1", "in", "gnd", "gnd", p["gm1"], p["gds1"]), mos("M2", "v2", "v1", "gnd", "gnd", p["gm2"], p["gds2"]),
         mos("M3", "out", "v2", "gnd", "gnd", p["gm3"], p["gds3"])]
    if with_ff:
        m.append(mos("Mf", "out", "v1", "gnd", "gnd", p["gmf"], p["gdsf"]))
    rr = (res("R1", "vdd", "v1", p["r1"]), res("R2", "vdd", "v2", p["r2"]), res("R3", "vdd", "out", p["r3"]))
    return nets, tuple(m), rr, ("gnd", "vdd"), ("in",)


def chain3_struct(with_ff=True):
    b1 = block(("v1",), ("in",), ("v1",), ("in", "v1"), stage=1, input_cells=("M1",))
    b2 = block(("v2",), ("v1",), ("v2",), ("v1", "v2"), stage=2, input_cells=("M2",))
    b3 = block(("out",), ("v2",), ("out",), ("v2", "out"), stage=3, input_cells=("M3",))
    ffs = (ff("v1->out", "v1", "out", ("Mf",), ("out",), ("v2",), ("M2",)),) if with_ff else ()
    return vstruct("transfer:0", {"in": 1.0}, ("out",), (b1, b2, b3), ffs, ("M1",), ("M1", "M2", "M3") + (("Mf",) if with_ff else ()))
