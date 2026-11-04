# -*- coding: utf-8 -*-
"""core/build_benches.py -- 벤치별 해석 요청과 파생 회로 IR (design §4.2·§5, card 20261104-op23).

이 card 몫: 본 회로의 op·ac(+ ratio·rout 덮어쓰기), β 루프, CM 루프, iso. 옛 `.control` 텍스트 대신 요청(Op, Ac)과 여기 덮어쓰기
(exc)로 낸다. 안정성(C10)·pz·noise·MC·swing 벤치는 OP-4·OP-5 몫이라 만들지 않는다(기간 동작 D-1).
"""
from __future__ import annotations

from core.build_circuit import (BETA_LOOP, CM_LOOP, _geometry, _process_diffusion_values, circuit_ir, diffusion_gate)
from core.ir import Circuit, Mos, VSource
from core.requests import Ac, Condition, DiffV, NodeV, Op, OpOutputs, BranchI

_UNRESOLVED = Condition(temp_c=None, corner=None)      # 미확정 조건 -- 어댑터가 받으면 거부한다(fail-closed)


def _ac_args(inp):
    ac = inp["testbench"]["ac"]
    return float(ac["fstart_hz"]), float(ac["fstop_hz"]), int(ac["points_per_decade"])


def _sense_expr(p, n, mode):
    return DiffV(p, n) if mode == "differential" else NodeV(p)


def main_requests(inp, bias, circuit, *, cond=None):
    """본 회로 벤치 요청: Op 하나, Ac 하나(개루프 A), ratio·rout 뷰마다 한 점 Ac(여기 덮어쓰기). 입력 testbench 값 그대로."""
    cond = cond or _UNRESOLVED
    m = circuit.meta
    currents = tuple(m["rail_sources"].values()) + tuple(m["hold_sources"].values())
    reqs = [Op("op", cond, (), OpOutputs("all", tuple(m["nets"]), currents))]
    f0, f1, ppd = _ac_args(inp)
    if m["has_ac"]:
        outs = m["outputs"]
        ex = NodeV(outs[0]) if len(outs) == 1 else DiffV(outs[0], outs[1])
        reqs.append(Ac("ac", cond, (), f0, f1, ppd, None, (ex,)))
    ac_src = m["ac_src"]
    for k, view in enumerate(m["ratio_plan"]):
        for side in ("num", "den"):
            tv = view[side]
            exc = tuple((src, "ac_mag", float(tv["ac_excite"].get(net, 0))) for net, src in sorted(ac_src.items()))
            reqs.append(Ac(f"ratio{k}.{side}", cond, exc, f0, f0, None, (f0,), (_sense_expr(tv["sense_p"], tv.get("sense_n"), tv["sense_mode"]),)))
    srcs = []
    for k, view in enumerate(m["rout_plan"]):
        srcs.append(f"tb:rout:{k}")
        if view["sense_mode"] == "differential":
            srcs.append(f"tb:rout:{k}n")
    for k, view in enumerate(m["rout_plan"]):
        mine = {f"tb:rout:{k}", f"tb:rout:{k}n"}
        exc = tuple((src, "ac_mag", 0.0) for _, src in sorted(ac_src.items())) + tuple((s, "ac_mag", 1.0 if s in mine else 0.0) for s in srcs)
        reqs.append(Ac(f"rout{k}", cond, exc, f0, f0, None, (f0,), (_sense_expr(view["sense_p"], view["sense_n"], view["sense_mode"]),)))
    return tuple(reqs)


def _loop(inp, bias, cond, mode, tag, omit, short, descriptor):
    circuit, blockers = circuit_ir(inp, bias, omit, short, descriptor=descriptor, mode=mode)
    cond = cond or _UNRESOLVED
    m = circuit.meta
    breaks, w = m["break_nets"], m["loop_weights"]
    f0, f1, ppd = _ac_args(inp)
    v_out = tuple(x for n in breaks for x in (NodeV(f"lbx_{n}"), NodeV(n)))
    exc = tuple((f"tb:lb:{n}", "ac_mag", 0.0) for n in breaks) + tuple((f"tb:ilb:{n}", "ac_mag", float(w[i])) for i, n in enumerate(breaks))
    i_out = tuple(BranchI(f"tb:lb:{n}") for n in breaks) + tuple(NodeV(n) for n in breaks)
    reqs = (Ac(f"{tag}.v", cond, (), f0, f1, ppd, None, v_out), Ac(f"{tag}.i", cond, exc, f0, f1, ppd, None, i_out))
    return circuit, reqs, blockers


def loop_bench(inp, bias, cond=None, omit=(), short=(), descriptor=None):
    """β 루프(Middlebrook 이중 주입) 벤치: 되먹임 수동소자의 입력 쪽 단자를 lbx_<넷> 으로 떼고 직렬 전압원·주입 전류원을 둔다."""
    return _loop(inp, bias, cond, BETA_LOOP, "loop", omit, short, descriptor)


def cm_loop_bench(inp, bias, cond=None, omit=(), short=(), descriptor=None):
    """공통 모드 루프 벤치: 차동 출력 포트 쌍을 같은 부호로 끊는 Middlebrook 이중 주입."""
    return _loop(inp, bias, cond, CM_LOOP, "cm", omit, short, descriptor)


def iso_bench(inp, cond=None, descriptor=None):
    """단독 소자(iso): 소자마다 자기 전용 노드에 두고 소스를 0 으로, 게이트·드레인·바디를 엔진 예측 VGS·VDS·VSB 에 이상 전압원으로 고정.
    극성 부호 = 기술자 kinds.<kind>.polarity(n: +1, p: -1): V(g) = s*VGS, V(d) = s*VDS, V(b) = -s*VSB. 회로 연결·테스트벤치 없음(.op 만)."""
    cond = cond or _UNRESOLVED
    pdev = (inp.get("predictions") or {}).get("devices") or {}
    proc = _process_diffusion_values(descriptor, inp["devices"])
    sign = {"n": 1.0, "p": -1.0}
    els, role, geometry, skipped, applied, notes, blockers = [], {}, {}, {}, {}, [], []
    for d in inp["devices"]:
        n = d["name"]
        diff, geometry[n] = _geometry(d, proc)
        kd = ((descriptor.doc["kinds"].get(d["kind"]) if descriptor is not None else None) or {})
        pol = kd.get("polarity")
        p = pdev.get(n) or {}
        miss = [k for k in ("VGS", "VDS", "VSB") if p.get(k) is None]
        if pol not in sign:
            skipped[n] = f"기술자 kinds[{d['kind']}].polarity 없음(n|p)"
            continue
        if miss:
            skipped[n] = f"예측 {miss} 없음"
            continue
        sg = sign[pol]
        vg, vd, vb = sg * float(p["VGS"]), sg * float(p["VDS"]), -sg * float(p["VSB"])
        g_, d_, b_ = f"iso_g_{n}", f"iso_d_{n}", f"iso_b_{n}"
        for tag, node, v in (("g", g_, vg), ("d", d_, vd), ("b", b_, vb)):
            els.append(VSource(f"tb:iso_{tag}:{n}", node, "0", v))
            role[f"tb:iso_{tag}:{n}"] = "testbench"
        els.append(Mos(n, d["kind"], d_, g_, "0", b_, float(d["L"]), float(d["finger_w"]), int(d["n_fingers"]), diff, None))
        role[n] = "circuit"
        applied[n] = {"V_g": vg, "V_d": vd, "V_s": 0.0, "V_b": vb, "polarity": pol}
    if not applied:
        blockers.append("iso: 단독 인스턴스를 만들 소자가 없다(예측 VGS/VDS/VSB 또는 polarity 없음)")
    notes += diffusion_gate(geometry, "iso")[1]
    for n, why in skipped.items():
        notes.append(f"iso: {n} 단독 인스턴스 안 만듦 -- {why}")
    meta = {"bias": "iso", "ground": "0", "reference_nets": [], "nets": [], "rail_sources": {}, "held": [], "hold_sources": {},
            "unheld": [], "gate_bias": {}, "inputs": [], "ac_src": {}, "has_ac": False, "outputs": [], "input_ac_weights": {},
            "dc_path_isolation": [], "geometry": geometry, "z1": None, "rout_plan": [], "ratio_plan": [], "nodeset": [],
            "break_nets": [], "loop_weights": [], "choke_H": None, "notes": notes, "iso_applied": applied, "iso_skipped": skipped,
            "not_in_topology": {}, "bias_nets": []}
    circuit = Circuit(tuple(els), role, meta)
    reqs = (Op("op", cond, (), OpOutputs(tuple(applied), (), ())),)
    return circuit, reqs, blockers
