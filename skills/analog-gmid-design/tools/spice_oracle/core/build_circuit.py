# -*- coding: utf-8 -*-
"""core/build_circuit.py -- 오라클 입력(JSON dict) -> 본 회로 IR (design §4.2, card 20261104-op23).

넷리스트 텍스트를 만들지 않는다. 입력의 회로 + 테스트벤치 정의(되먹임 DC 경로, 입력 결합, 레일, 게이트 바이어스, 고정, 루프 절단)를 IR 원소로
만들고, 원소의 역할(circuit | testbench)을 표로 가른다. 방언·단위 환산·병렬 배수 전달은 어댑터 몫이다.

옛 막힘(BLOCKED) 조건과 문장은 그대로 `blockers` 로 돌려준다(막힘은 거부가 아니라 판정 BLOCKED, 벤치를 실행하지 않는다).
게이트 전용 넷은 입력 `bias_voltages` 선언으로만 구동한다 -- 예측 노드전압으로 이상 전압원을 지어 넣지 않는다(OP-B3, §11.2 1d).
"""
from __future__ import annotations

import copy
import math

from core.ir import Capacitor, Circuit, Diffusion, ISource, Inductor, Mos, Resistor, VSource, Vcvs

BIASES = ("free", "forced", "iso")
CM_LOOP = "cm"
BETA_LOOP = "beta"
# C27: 개루프 A 의 크기를 쓰는 measure(입력 AC 진폭에 비례하는 값). f3db_hz 는 배율 무관이라 빠진다.
A_SCALED_MEASURES = ("dc_gain_db", "ugf_hz", "pm_deg")


# ---------------------------------------------------------------- 입력 읽기 도우미
def _items(inp):
    return list((inp.get("acceptance") or {}).get("constraints") or []) + list((inp.get("predictions") or {}).get("metrics") or [])


def ratio_views(inp):
    """C24: measure == ratio_db 인 항목의 view 목록(dict 동등 기준 중복 제거, 처음 나온 순서)."""
    out = []
    for it in _items(inp):
        if it.get("measure") == "ratio_db" and it.get("view") is not None and it["view"] not in out:
            out.append(it["view"])
    return out


def sense_key(view):
    """C26: 감지 전용 뷰의 정규형 (sense_p, sense_n 또는 None, sense_mode). sense_n 이 없는 것과 null 은 같은 뷰다."""
    return (view.get("sense_p"), view.get("sense_n"), view.get("sense_mode"))


def rout_views(inp):
    """C26: measure == rout_ohm 인 항목의 view 목록(sense_key 기준 중복 제거, 처음 나온 순서)."""
    out, seen = [], set()
    for it in _items(inp):
        if it.get("measure") != "rout_ohm" or it.get("view") is None:
            continue
        k = sense_key(it["view"])
        if k not in seen:
            seen.add(k)
            out.append({"sense_p": k[0], "sense_n": k[1], "sense_mode": k[2]})
    return out


def excitation_weight_check(inp):
    """C27: A 크기를 쓰는 measure 가 있으면 입력 AC 진폭이 정의값(차동 ±1/2, 단일 1)이어야 한다. 막힘 목록."""
    used = sorted({it.get("measure") for it in _items(inp) if it.get("measure") in A_SCALED_MEASURES})
    if not used:
        return []
    ports, ac = inp["ports"], (inp["testbench"].get("ac") or {})
    if ports.get("input_p") and ports.get("input_n"):
        p, n = ac.get("input_p_ac"), ac.get("input_n_ac")
        if p is None or n is None or (p - n == 1 and p + n == 0):
            return []
        return [f"C27 가중 정의: 차동 입력은 input_p_ac - input_n_ac == 1, input_p_ac + input_n_ac == 0 이어야 한다"
                f"(v_id = 1, v_cm = 0) -- 지금 input_p_ac={p!r}, input_n_ac={n!r} (measure {used})"]
    if ports.get("input"):
        v = ac.get("input_ac")
        if v is None or v == 1:
            return []
        return [f"C27 가중 정의: 단일 입력은 input_ac == 1 이어야 한다 -- 지금 {v!r} (measure {used})"]
    return []


def loop_break_nets(inp):
    """β 루프를 끊을 넷 = 선언된 되먹임 수동소자가 물린 입력 포트 넷. (넷 목록, 막힘 목록)."""
    names = inp.get("feedback_passives") or []
    if not names:
        return [], []
    ports = inp["ports"]
    in_nets = [ports[k] for k in ("input_p", "input_n", "input") if ports.get(k)]
    by = {p["name"]: p for p in inp.get("passives") or []}
    blockers = [f"feedback_passives 의 {n} 이 passives 에 없다" for n in names if n not in by]
    blockers += [f"feedback_passives 의 {n} 이 입력 포트 넷 {in_nets} 에 물려 있지 않다(단자 {by[n]['terminals']})"
                 for n in names if n in by and not set(by[n]["terminals"]) & set(in_nets)]
    blockers += [f"feedback_passives 의 {n} 은 두 단자 {by[n]['terminals']} 가 모두 입력 포트 넷이다 -- 절단 단자가 "
                 f"하나로 정해지지 않는다(엔진 feedback_cut_ambiguous 와 같은 조건)"
                 for n in names if n in by and sum(t in in_nets for t in by[n]["terminals"]) == 2]
    nets = [n for n in in_nets if any(n in by[x]["terminals"] for x in names if x in by)]
    if not nets:
        blockers.append("feedback_passives 가 어느 입력 포트 넷에도 물려 있지 않다")
    return nets, blockers


def cm_loop_break_nets(inp):
    """공통 모드 루프를 끊는 곳 = 선언된 차동 출력 포트 쌍. 입력 `cm_output_loop` 가 있을 때만. (넷 목록, 막힘 목록)."""
    if not inp.get("cm_output_loop"):
        return [], []
    ports = inp["ports"]
    if not (ports.get("output_p") and ports.get("output_n")):
        return [], ["cm_output_loop: ports 에 차동 출력 output_p/output_n 이 없다"]
    return [ports["output_p"], ports["output_n"]], []


def cm_loop_moved(inp, breaks):
    """출력 넷에서 새 노드 lbx 로 옮길 구동자 단자: {소자 이름: "drain" | "source"}."""
    b = set(breaks)
    by = {d["name"]: d for d in inp["devices"]}
    out = {}
    for name in (inp.get("cm_output_loop") or {}).get("drivers") or []:
        d = by.get(name)
        ends = [] if d is None else [t for t in ("drain", "source") if d[t] in b]
        if len(ends) == 1:
            out[name] = ends[0]
    return out


def cm_loop_blockers(inp, breaks):
    moved = cm_loop_moved(inp, breaks)
    return [f"cm_output_loop.drivers 의 {n} 이 devices 에 없거나 drain·source 중 정확히 하나가 출력 넷 {sorted(breaks)} 이 아니다"
            for n in (inp.get("cm_output_loop") or {}).get("drivers") or [] if n not in moved]


def apply_z1(inp, omit=(), short=()):
    """Z1 제거법(README C18): omit = 원소 이름 -> 뺌, short = 수동소자 이름 -> 0 V 전압원. (사본, 변경 기록, 막힘)."""
    omit, short = list(omit or []), list(short or [])
    mods = {"omit": omit, "short": short}
    if not omit and not short:
        return inp, None, []
    x = copy.deepcopy(inp)
    names = {"device": {d["name"] for d in x["devices"]}, "passive": {p["name"] for p in x.get("passives") or []},
             "source": {s["name"] for s in x.get("sources") or []}}
    allnames = set().union(*names.values())
    blockers = [f"Z1 --omit {n}: 그런 원소가 없다" for n in omit if n not in allnames]
    blockers += [f"Z1 --short {n}: 수동소자(passives)만 단락할 수 있다" for n in short if n not in names["passive"]]
    blockers += [f"Z1 --{opt} {n}: 같은 원소를 같은 옵션에 두 번 적었다"
                 for opt, lst in (("omit", omit), ("short", short)) for n in sorted({m for m in lst if lst.count(m) > 1})]
    blockers += [f"Z1 --omit/--short {n}: 같은 원소를 두 번 바꿀 수 없다" for n in set(omit) & set(short)]
    fbp = set(x.get("feedback_passives") or [])
    blockers += [f"Z1 변경 대상 {n} 이 feedback_passives 에 있다(β 루프 정의가 바뀐다)" for n in (set(omit) | set(short)) & fbp]
    om = set(omit)
    x["devices"] = [d for d in x["devices"] if d["name"] not in om]
    x["sources"] = [s for s in x.get("sources") or [] if s["name"] not in om]
    ps = []
    for p in x.get("passives") or []:
        if p["name"] in om:
            continue
        if p["name"] in short:
            p = {"name": p["name"], "kind": "short", "terminals": list(p["terminals"]), "value": 0.0}
        ps.append(p)
    x["passives"] = ps
    return x, mods, blockers


def dc_path_isolation(tb, inputs, fb):
    """C27 기록(판정 아님): 입력 넷마다 (2*pi*fstart)^2 * L * C. >> 1 이면 그 입력은 fstart 에서 AC 0 고정(개루프)."""
    f0 = (tb.get("ac") or {}).get("fstart_hz")
    out = []
    for net in inputs:
        Lh, Cf = tb.get("dc_choke_H"), tb.get("ac_couple_F")
        w2lc = None if f0 is None or Lh is None or Cf is None else (2 * math.pi * float(f0)) ** 2 * float(Lh) * float(Cf)
        out.append({"net": net, "choke_H": Lh, "couple_F": Cf, "f_hz": f0, "omega2_LC": w2lc, "output_feedback": net in fb})
    return out


def gate_only_nets(circuit, protected):
    """게이트 전용 넷(§11.2 1d): 그 넷에 닿은 본 회로(role == circuit) 원소 단자가 전부 MOS gate 이고 protected 가 아닌 넷. 사전순."""
    seen: dict = {}
    for e in circuit.elements:
        if circuit.role.get(e.name) != "circuit":
            continue
        if type(e).__name__ == "Mos":
            terms = ((e.d, "d"), (e.g, "g"), (e.s, "s"), (e.b, "b"))
        elif type(e).__name__ in ("Resistor", "Capacitor", "Inductor"):
            terms = ((e.a, "x"), (e.b, "x"))
        else:
            terms = ((e.p, "x"), (e.n, "x"))
        for net, lab in terms:
            seen.setdefault(net, set()).add(lab)
    return sorted(n for n, labs in seen.items() if labs == {"g"} and n not in protected)


def protected_nets(inp):
    ports = inp.get("ports") or {}
    return {r["net"] for r in inp["rails"]} | {v for v in ports.values() if v}


# ---------------------------------------------------------------- 확산 기하(C22)
def _process_diffusion_values(descriptor, devs):
    """기술자 diffusion 키가 가리키는 엔진 선언 값(원본에서 풂). 소자 자신의 diffusion 이 없는 소자가 있을 때만 푼다. 아니면 None."""
    if descriptor is None or all(d.get("diffusion") for d in devs):
        return None
    df = descriptor.doc["diffusion"]
    return {k: descriptor.quantity(df[k]) for k in ("ad_per_w", "as_per_w", "pd_extra", "ps_extra")}


def _diffusion(d, proc):
    """소자 d 의 확산 기하: (Diffusion | None, 기록 dict). 출처 순서 devices[].diffusion -> 기술자 규칙 -> 없음."""
    own = d.get("diffusion")
    if own:
        v = dict(source="device", ad=float(own["ad_m2"]), **{"as": float(own["as_m2"])}, pd=float(own["pd_m"]), ps=float(own["ps_m"]))
    elif proc:
        fw = float(d["finger_w"])
        v = dict(source="process_rule", ad=proc["ad_per_w"] * fw, **{"as": proc["as_per_w"] * fw},
                 pd=fw + proc["pd_extra"], ps=fw + proc["ps_extra"])
    else:
        return None, {"source": None, "ad": None, "as": None, "pd": None, "ps": None}
    return Diffusion(ad=v["ad"], as_=v["as"], pd=v["pd"], ps=v["ps"]), v


def diffusion_gate(geometry, bias):
    """C22: 확산 기하가 없는 소자 목록 -> (막힘 목록, 노트 목록). free(합격 실행)만 막힘."""
    missing = sorted(n for n, g in geometry.items() if not (g.get("diffusion") or {}).get("source"))
    if not missing:
        return [], []
    msg = f"C22 접합 용량: 확산 기하 없는 소자 {missing} (devices[].diffusion 도 기술자 diffusion 도 없음)"
    if bias == "free":
        return [msg + " -- 합격 실행(free)은 접합 용량을 넣어야 한다"], []
    return [], [msg + f" -- {bias} 진단 실행이라 막지 않음(그 소자는 접합 용량 없음)"]


def _geometry(d, proc):
    diff, rec = _diffusion(d, proc)
    return diff, {"L": float(d["L"]), "finger_w": float(d["finger_w"]), "n_fingers": int(d["n_fingers"]),
                  "W_from_fingers": float(d["finger_w"]) * int(d["n_fingers"]),
                  "W_declared": None if d.get("W") is None else float(d["W"]), "diffusion": rec}


# ---------------------------------------------------------------- 본 회로 IR
def circuit_ir(inp, bias, omit=(), short=(), *, descriptor=None, mode=None):
    """입력 -> (Circuit, blockers). bias ∈ free|forced (iso 는 build_benches.iso_bench). mode: None(본) | 'beta' | 'cm'(루프 절단 벤치)."""
    if bias not in ("free", "forced"):
        raise ValueError(f"circuit_ir bias 는 free|forced: {bias!r}")
    work, z1, zb = apply_z1(inp, omit, short)
    blockers = list(zb)
    tb = work["testbench"]
    pred = (work.get("predictions") or {}).get("nodes") or {}
    blockers += excitation_weight_check(work)
    cm = mode == CM_LOOP
    loop = mode == BETA_LOOP
    cm_moved = cm_loop_moved(work, cm_loop_break_nets(work)[0]) if cm else {}
    refs = [r["net"] for r in work["rails"] if r.get("reference")]
    ref = set(refs)
    if len(refs) != 1:
        blockers.append(f"rails 에 reference=true 가 정확히 1개여야 한다(지금 {len(refs)}개)")
    ground = refs[0] if len(refs) == 1 else "0"
    N = lambda n: "0" if n in ref else n          # noqa: E731
    devs = work["devices"]
    choke, coup = float(tb["dc_choke_H"]), float(tb["ac_couple_F"])
    proc = _process_diffusion_values(descriptor, devs)
    els: list = []
    role: dict = {}

    def add(e, r):
        els.append(e)
        role[e.name] = r

    rail_src = {}
    for r in work["rails"]:
        if r.get("reference"):
            continue
        nm = f"tb:rail:{r['net']}"
        rail_src[r["net"]] = nm
        add(VSource(nm, N(r["net"]), "0", float(r["voltage"])), "testbench")
    rail_nets = {r["net"] for r in work["rails"]}

    driven, dev_nets, geometry = set(), [], {}
    for d in devs:
        nodes = [N(d[t]) for t in ("drain", "gate", "source", "bulk")]
        if cm and d["name"] in cm_moved:
            slot = 0 if cm_moved[d["name"]] == "drain" else 2
            nodes[slot] = f"lbx_{d[cm_moved[d['name']]]}"
        diff, geometry[d["name"]] = _geometry(d, proc)
        add(Mos(d["name"], d["kind"], nodes[0], nodes[1], nodes[2], nodes[3], float(d["L"]), float(d["finger_w"]),
                int(d["n_fingers"]), diff, None), "circuit")
        driven.update([d["drain"], d["source"]])
        for t in ("drain", "gate", "source", "bulk"):
            if d[t] not in dev_nets:
                dev_nets.append(d[t])
    dg_block, dg_note = diffusion_gate(geometry, bias)
    blockers += dg_block
    notes = list(dg_note)

    for s in work.get("sources") or []:
        a, b = s["terminals"]
        driven.update([a, b])
        if s["kind"] == "current":
            add(ISource(s["name"], N(a), N(b), float(s["value"])), "circuit")
        elif s["kind"] == "voltage":
            add(VSource(s["name"], N(a), N(b), float(s["value"])), "circuit")
        else:
            blockers.append(f"source {s['name']} kind={s['kind']} 미지원")
            continue
        notes.append(f"{s['kind']} source {s['name']}={float(s['value']):.10g} ({s.get('value_basis', '근거 미기재')})")

    if cm:
        breaks, bb = cm_loop_break_nets(work)
        fbp = set()
        bb = bb + cm_loop_blockers(work, breaks)
        driven.update(breaks)
    else:
        breaks, bb = loop_break_nets(work) if loop else ([], [])
        fbp = set(work.get("feedback_passives") or [])
    blockers += bb
    passive_nets = []
    for p in work.get("passives") or []:
        a, b = p["terminals"]
        if loop and p["name"] in fbp:
            a, b = (f"lbx_{a}" if a in breaks else a), (f"lbx_{b}" if b in breaks else b)
        driven.update([a, b])
        if p["kind"] == "short":
            add(VSource(f"tb:short:{p['name']}", N(a), N(b), 0.0), "testbench")
            notes.append(f"Z1 --short: {p['name']} 을 0 V 전압원으로 단락")
        elif p["kind"] in ("resistor", "capacitor"):
            cls = Resistor if p["kind"] == "resistor" else Capacitor
            add(cls(p["name"], N(a), N(b), float(p["value"])), "circuit")
            notes.append(f"{p['kind']} {p['name']}={float(p['value']):.10g} ({p.get('value_basis', '근거 미기재')})")
        else:
            blockers.append(f"passive {p['name']} kind={p['kind']} 미지원")
            continue
        for n in (a, b):
            if n not in dev_nets and n not in passive_nets:
                passive_nets.append(n)

    ports = work["ports"]
    inp_p, inp_n = ports.get("input_p"), ports.get("input_n")
    out_p, out_n, out_se = ports.get("output_p"), ports.get("output_n"), ports.get("output")
    in_se = ports.get("input")
    inputs = [x for x in (inp_p, inp_n, in_se) if x]
    if not inputs:
        blockers.append("ports 에 input_p/input_n 또는 input 이 없다")
    if not (out_se or (out_p and out_n)):
        blockers.append("ports 에 output 또는 output_p/output_n 이 없다")
    fb = {}
    if bias == "free" and inp_p and inp_n:
        if out_se:
            fb[inp_n] = ("se", out_se)
        elif out_p and out_n:
            fb[inp_n] = ("diff", out_p, out_n)
            fb[inp_p] = ("diff", out_n, out_p)
    ac_mag = {}
    need = {inp_p: "input_p_ac", inp_n: "input_n_ac"} if (inp_p and inp_n) else ({in_se: "input_ac"} if in_se else {})
    for net, key in need.items():
        if tb["ac"].get(key) is None:
            blockers.append(f"testbench.ac.{key} 없음 -- 입력 {net} 의 AC 크기를 정할 수 없다")
        else:
            ac_mag[net] = tb["ac"][key]
    ac_src = dict(rail_src)
    loop_choke = None
    if loop and breaks:
        if tb.get("loop_dc_choke_H") is None:
            blockers.append("testbench.loop_dc_choke_H 없음 -- β 루프 측정의 입력 DC 경로를 정할 수 없다")
        else:
            loop_choke = float(tb["loop_dc_choke_H"])
    for net in inputs:
        driven.add(net)
        ch = loop_choke if (loop and net in breaks and loop_choke) else choke
        vin = pred.get(net)
        if vin is None:
            blockers.append(f"입력 {net} 의 예측 DC 전압 없음(predictions.nodes)")
            continue
        if net in fb and fb[net][0] == "diff":
            _, o, o_other = fb[net]
            if tb["ac"].get("diff_feedback_gain") is None:
                blockers.append("testbench.ac.diff_feedback_gain 없음 -- free 차동 되먹임을 만들 수 없다")
                continue
            add(Vcvs(f"tb:fb:{net}", f"fbs_{net}", "0", N(o), N(o_other), float(tb["ac"]["diff_feedback_gain"])), "testbench")
            add(VSource(f"tb:ofs:{net}", f"fbs_{net}", f"fbd_{net}", -float(vin)), "testbench")
            add(Inductor(f"tb:fbl:{net}", f"fbd_{net}", N(net), ch), "testbench")
            notes.append(f"free: 차동 DC 되먹임 k*(V({o})-V({o_other})) -> {net}, 입력 공통모드 {vin:.6g} V(예측)")
        elif net in fb:
            o = fb[net][1]
            vo = pred.get(o)
            if vo is None:
                blockers.append(f"출력 {o} 예측 DC 전압 없음 -- 되먹임 오프셋을 정할 수 없다")
                continue
            add(Vcvs(f"tb:fb:{net}", f"fbs_{net}", "0", N(o), "0", 1.0), "testbench")
            add(VSource(f"tb:ofs:{net}", f"fbs_{net}", f"fbd_{net}", float(vo) - float(vin)), "testbench")
            add(Inductor(f"tb:fbl:{net}", f"fbd_{net}", N(net), ch), "testbench")
            notes.append(f"free: DC 되먹임 {o} -> {net} (V({o})_pred={vo:.6g}, V({net})_pred={vin:.6g})")
        else:
            add(VSource(f"tb:dc:{net}", f"dcs_{net}", "0", float(vin)), "testbench")
            add(Inductor(f"tb:dcl:{net}", f"dcs_{net}", N(net), ch), "testbench")
        if net in breaks:
            add(VSource(f"tb:lb:{net}", N(net), f"lbx_{net}", 0.0, ac_mag=float(ac_mag.get(net, 0))), "testbench")
            add(ISource(f"tb:ilb:{net}", "0", N(net), 0.0, ac_mag=0.0), "testbench")
        else:
            add(Capacitor(f"tb:cac:{net}", N(net), f"acs_{net}", coup), "testbench")
            add(VSource(f"tb:vac:{net}", f"acs_{net}", "0", 0.0, ac_mag=0.0 if loop else float(ac_mag.get(net, 0))), "testbench")
            ac_src[net] = f"tb:vac:{net}"

    if cm and breaks:
        ac_mag = {net: 1 / len(breaks) for net in breaks}
        for net in breaks:
            add(VSource(f"tb:lb:{net}", N(net), f"lbx_{net}", 0.0, ac_mag=float(ac_mag[net])), "testbench")
            add(ISource(f"tb:ilb:{net}", "0", N(net), 0.0, ac_mag=0.0), "testbench")

    # 게이트 전용 넷: 입력 bias_voltages 선언으로만 구동한다(예측 노드전압으로 전압원을 짓지 않는다)
    tmp = Circuit(tuple(els), dict(role), {})
    declared = {b["net"]: float(b["value"]) for b in work.get("bias_voltages") or []}
    gate_bias = {}
    for g in gate_only_nets(tmp, protected_nets(work)):
        if g in declared:
            gate_bias[g] = declared[g]
            add(VSource(f"tb:bias:{g}", N(g), "0", declared[g]), "testbench")
            ac_src[g] = f"tb:bias:{g}"
    for net, v in gate_bias.items():
        notes.append(f"게이트 전용 넷 {net} = {v:.6g} V (bias_voltages 선언)")

    held, unheld, hold_src = [], [], {}
    nodeset = []
    if bias == "forced":
        for n in dev_nets:
            if n in rail_nets or n in gate_bias or n in inputs:
                continue
            v = pred.get(n)
            if v is None:
                unheld.append(n)
                continue
            # 예측 전압원을 그 넷에 직렬로 두고(+ 단자 = 넷), choke 로 접지에 닿는다: DC 는 넷 = v, AC 는 choke 가 열려 개루프.
            # 옛 배치(전압원 hs 0, choke hs 넷)와 DC·AC 가 같다. 전압원 전류 i(V) = 넷에서 빠져나가는 전류(KCL 잔차)로 부호도 같다.
            add(VSource(f"tb:hold:{n}", N(n), f"hs_{n}", float(v)), "testbench")
            add(Inductor(f"tb:holdl:{n}", f"hs_{n}", "0", choke), "testbench")
            hold_src[n] = f"tb:hold:{n}"
            held.append(n)
        notes.append(f"forced: 소자 단자 넷 {len(held)}개를 예측 전압에 choke 로 고정")
        if unheld:
            notes.append(f"forced: 예측 전압이 없어 고정 못 한 넷(자유): {unheld}")
    elif tb.get("nodeset_from_predictions"):
        nodeset = [(N(n), float(pred[n])) for n in dev_nets + passive_nets
                   if n not in rail_nets and n not in gate_bias and pred.get(n) is not None]
        notes.append(f"free: 예측 노드전압 {len(nodeset)}개를 뉴턴 초기값으로 준다")

    all_nets = [n for n in dev_nets + passive_nets if N(n) != "0"]
    rout_plan = [] if loop or cm else _rout_plan(work, ac_src, all_nets, ref, blockers)
    for k, view in enumerate(rout_plan):
        add(ISource(f"tb:rout:{k}", "0", N(view["sense_p"]), 0.0, ac_mag=0.0), "testbench")
        if view["sense_mode"] == "differential":
            add(ISource(f"tb:rout:{k}n", N(view["sense_n"]), "0", 0.0, ac_mag=0.0), "testbench")
    ratio_plan = [] if loop or cm else _ratio_plan(work, ac_src, all_nets, ref, blockers)

    outs = [out_se] if out_se else ([out_p, out_n] if (out_p and out_n) else [])
    meta = {"bias": bias, "ground": ground, "reference_nets": sorted(ref), "nets": all_nets, "rail_sources": rail_src, "held": held,
            "hold_sources": hold_src, "unheld": unheld, "gate_bias": gate_bias, "inputs": inputs, "ac_src": ac_src,
            "has_ac": bool(inputs) and bool(out_se or (out_p and out_n)), "outputs": outs,
            "f_start": (tb.get("ac") or {}).get("fstart_hz"),
            "input_ac_weights": dict(ac_mag), "dc_path_isolation": dc_path_isolation(tb, inputs, fb),
            "geometry": geometry, "z1": z1, "rout_plan": rout_plan, "ratio_plan": ratio_plan, "nodeset": nodeset,
            "nodeset_per_line": int(tb.get("nodeset_per_line", len(nodeset) or 1)) if nodeset else 1,
            "break_nets": list(breaks), "loop_weights": [ac_mag.get(n, 0) for n in breaks], "choke_H": loop_choke,
            "notes": notes,
            "not_in_topology": {e["name"]: e["not_in_topology_reason"] for k in ("passives", "sources")
                                for e in inp.get(k) or [] if e.get("not_in_topology_reason")},
            "bias_nets": sorted(b["net"] for b in inp.get("bias_voltages") or [])}
    return Circuit(tuple(els), role, meta), blockers


def _rout_plan(inp, ac_src, all_nets, ref, blockers):
    """C26: rout_ohm 뷰 목록을 검사해 잴 뷰만 돌려준다(하나라도 막히면 빈 목록 + 막힘)."""
    views = rout_views(inp)
    if not views:
        return []
    if (inp["testbench"].get("ac") or {}).get("fstart_hz") is None:
        blockers.append("C26 rout_ohm: testbench.ac.fstart_hz 없음 -- 측정 주파수를 정할 수 없다")
        return []
    circuit = set(all_nets)
    ok = True
    for k, view in enumerate(views):
        keys = ("sense_p", "sense_n") if view["sense_mode"] == "differential" else ("sense_p",)
        for key in keys:
            net = view[key]
            if net in ref:
                blockers.append(f"C26 rout_ohm 뷰 {k}: {key} {net} 은 reference 레일(SPICE 노드 0)이다")
                ok = False
            elif net not in circuit:
                blockers.append(f"C26 rout_ohm 뷰 {k}: {key} {net} 이 회로 넷(reference 제외)이 아니다")
                ok = False
            elif net in ac_src:
                blockers.append(f"C26 rout_ohm 뷰 {k}: {key} {net} 은 테스트벤치가 이상 전압원으로 구동하는 넷"
                                f"(레일·입력·게이트 바이어스 {sorted(ac_src)})이다 -- 엔진 출력 포트 뷰의 고정 노드라 정의 밖")
                ok = False
        if view["sense_mode"] == "differential" and view["sense_p"] == view["sense_n"]:
            blockers.append(f"C26 rout_ohm 뷰 {k}: sense_p 와 sense_n 이 같은 넷 {view['sense_p']} 이다")
            ok = False
    return views if ok else []


def _ratio_plan(inp, ac_src, all_nets, ref, blockers):
    """C24: ratio_db 뷰를 검사해 잴 뷰만 돌려준다."""
    views = ratio_views(inp)
    if not views:
        return []
    if (inp["testbench"].get("ac") or {}).get("fstart_hz") is None:
        blockers.append("C24 ratio_db: testbench.ac.fstart_hz 없음 -- 측정 주파수를 정할 수 없다")
        return []
    circuit = set(all_nets)
    ok = True
    for k, view in enumerate(views):
        for side in ("num", "den"):
            tv = view[side]
            for net in sorted(tv["ac_excite"]):
                if net in ref:
                    blockers.append(f"C24 ratio_db 뷰 {k} {side}: reference 레일 {net} 은 여기할 수 없다(SPICE 노드 0)")
                    ok = False
                elif net not in ac_src:
                    blockers.append(f"C24 ratio_db 뷰 {k} {side}: 여기 넷 {net} 을 테스트벤치가 이상 전압원으로 구동하지 않는다"
                                    f"(여기 가능 넷 = 레일·입력·게이트 바이어스 {sorted(ac_src)}) -- DC 를 바꾸지 않고 AC 만 고정할 수 없다")
                    ok = False
            for key in ("sense_p", "sense_n"):
                net = tv.get(key)
                if net is not None and net not in circuit:
                    blockers.append(f"C24 ratio_db 뷰 {k} {side}: {key} {net} 이 회로 넷(reference 제외)이 아니다")
                    ok = False
    return views if ok else []


def fold_collisions(circuit) -> list:
    """대소문자 접기 충돌(design §4.1 `ir_name_collision`): 접으면 같아지는 서로 다른 넷 이름 / 원소 이름 묶음."""
    from core.ir import element_nets
    out = []
    nets = {n for e in circuit.elements for n in element_nets(e)}
    for what, names in (("net", nets), ("element", {e.name for e in circuit.elements})):
        groups: dict = {}
        for n in names:
            groups.setdefault(n.lower(), set()).add(n)
        out += [{"kind": what, "names": sorted(g)} for g in groups.values() if len(g) > 1]
    return sorted(out, key=lambda x: (x["kind"], x["names"]))
