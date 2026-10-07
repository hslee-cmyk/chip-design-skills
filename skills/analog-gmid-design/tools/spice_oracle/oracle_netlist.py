# -*- coding: utf-8 -*-
"""oracle_netlist.py -- SPICE 오라클 입력(JSON, oracle_input.schema.json) -> ngspice 넷리스트.

진입점(단독 실행):
    python oracle_netlist.py <oracle_input.json> <out.cir> --bias free|forced|iso
                             [--topology T] [--require-topology] [--omit N ...] [--short N ...]

  넷리스트(.cir)와 그 메타(<out.cir>.meta.json: 소자 probe 이름, 넷 목록, 고정한 넷, 경고/막힘)를 쓴다.
  ngspice 는 부르지 않는다(oracle_simulate.py 몫).

공개 함수: build_netlist(inp, bias, ac_file, loop=False) -> (text, meta), write_netlists(inp, bias, out_cir, ...) -> meta,
          validate_input(inp) -> [위반], loop_break_nets(inp), load_input(path), read_lut_meta(npz_path),
          parse_netlist_elements(text, inp), topology_elements(topo), topology_identity(inp, text, path),
          resolve_topology_path(inp, input_path, override), apply_z1(inp, omit, short)
입력은 먼저 oracle_input.schema.json 으로 검증한다. 위반이면 넷리스트를 쓰지 않고 반환 2(README C13).
  * [신규] C15 topology 연결 동일성: 본 넷리스트를 다시 파싱한 (원소 이름, 종류, 단자 넷) 집합을 topology JSON
    (netlist + passive_elements + ideal_sources)과 비교한다. 다르면 막힘. topology 가 없으면 '미검증' 표시,
    --require-topology(합격 실행)이면 막힘.
  * [신규] bias=iso: 소자마다 단독 인스턴스를 엔진 예측 VGS·VDS·VSB 에 고정(models[kind].polarity 필요).
  * [신규] Z1 제거법: --omit(원소 제거)·--short(수동소자를 0 V 전압원으로 단락). 진단 실행 -- 합격 판정 안 함.

규칙(값은 전부 입력에서 온다 -- 이 파일은 회로·소자·공정 이름과 수치 상수를 갖지 않는다)
  * 코너·온도: process.lut_npz 의 메타(corner, temp_c). include 경로의 '{corner}' 자리를 npz corner 로 채우고
    `.temp` 는 npz temp_c. npz 에 메타가 없으면 막힘.
  * finger: 소자 하나 = 인스턴스 하나, `w=finger_w m=n_fingers`. nf 는 쓰지 않는다(ngspice 는 모델 bin 을
    총폭 w 로 고르고 BSIM4 크기식은 w/nf 로 계산해, nf>1 이면 다른 bin 계수를 외삽한다 -- lut_coverage_study 표 E).
    subckt 의 m 은 내부 소자를 m 배 하고 @ probe 값(id/gm/gds)도 m 배 총합으로 나온다(2026-10-07 실측).
  * 확산 면적: process.diffusion(있으면) ad=as=ad_per_w_m*finger_w, pd=ps=finger_w+pd_extra_m. 없으면 생략.
  * bias=free : 회로가 DC 해를 스스로 찾는다. 입력 DC 는 dc_choke_H 로, AC 는 ac_couple_F 로 넣고
    출력 -> 반대 극성 입력 DC 되먹임으로 출력 DC 를 예측값 근처에 묶는다(차동 출력은 차동 성분만).
    testbench.nodeset_from_predictions 이면 예측 노드전압을 .nodeset(뉴턴 초기값)으로 준다.
  * bias=forced: 예측 전압이 있는 모든 소자 단자 넷을 dc_choke_H 로 예측값에 묶는다. DC = 엔진이 의도한
    바이어스, 각 고정원 전류 = 그 넷의 KCL 잔차, AC 에서는 choke 가 열려 실제 모델의 개루프 응답.
  * 구동 소자 없는 게이트 전용 넷: bias_voltages 선언값, 없으면 예측 노드전압의 이상 전압원(경고로 남김).
"""
import argparse
import json
import os
import sys

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oracle_input.schema.json")
OP_PARAMS = ("id", "gm", "gds", "vth", "vdsat", "vgs", "vds", "vbs")  # BSIM 동작점 파라미터 이름
BIASES = ("free", "forced", "iso")
# 넷리스트 원소 이름 접두사. 회로 원소(topology 대조 대상)와 테스트벤치 원소(대조 제외)를 이 표로만 가른다(C15).
CIRCUIT_PREFIXES = {"X": "device", "Rp_": "resistor", "Cp_": "capacitor", "Isrc_": "current", "Vsrc_": "voltage"}
TESTBENCH_PREFIXES = ("Vrail_", "Efb_", "Vofs_", "Lfb_", "Vdc_", "Ldc_", "Cac_", "Vac_", "Vbias_", "Vhold_", "Lhold_",
                      "Vlb_", "Ilb_", "Vshort_", "Viso_")
# topology ideal_sources 의 kind 어휘 -> 오라클 sources[].kind 어휘(같은 뜻의 두 이름)
TOPOLOGY_SOURCE_KINDS = {"current_source": "current", "voltage_source": "voltage", "current": "current",
                         "voltage": "voltage"}


def load_input(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_lut_meta(npz_path):
    import numpy as np
    z = np.load(npz_path)
    meta = {}
    for k in ("corner", "temp_c"):
        meta[k] = z[k].item() if k in z.files else None
    return meta


def _num(v):
    return format(float(v), ".10g")


class _Nets:
    """넷 이름 -> SPICE 노드 이름. 기준 레일은 '0'. ngspice 는 대소문자를 가리지 않으므로 충돌을 막힘으로 보고."""

    def __init__(self, rails):
        refs = [r["net"] for r in rails if r.get("reference")]
        self.ref = set(refs)
        self.rail_v = {r["net"]: float(r["voltage"]) for r in rails}
        self.seen = {}
        self.blockers = []
        if len(refs) != 1:
            self.blockers.append(f"rails 에 reference=true 가 정확히 1개여야 한다(지금 {len(refs)}개)")

    def __call__(self, net):
        if net in self.ref:
            return "0"
        low = net.lower()
        prev = self.seen.setdefault(low, net)
        if prev != net:
            same_rail = (prev in self.rail_v and net in self.rail_v and self.rail_v[prev] == self.rail_v[net])
            if not same_rail:
                msg = f"넷 '{prev}' 와 '{net}' 이 대소문자만 다르다(ngspice 에서 같은 노드가 된다)"
                if msg not in self.blockers:
                    self.blockers.append(msg)
        return net


def _includes(process, kinds, corner):
    out = []
    seen = set()
    for kind in sorted(kinds):
        for tpl in process["models"][kind]["includes"]:
            p = tpl.replace("{corner}", str(corner))
            if p not in seen:
                seen.add(p)
                out.append(f'.include "{p}"')
    return out


def probe_name(process, kind, inst, param):
    """ngspice @ 표현. models[kind].op_probe 의 {inst}(소문자 인스턴스 이름), {param} 을 채운다."""
    return process["models"][kind]["op_probe"].replace("{inst}", inst.lower()).replace("{param}", param)


def device_line(process, d, nodes):
    m = process["models"][d["kind"]]
    fw = float(d["finger_w"])
    parts = [f"X{d['name']}", nodes[0], nodes[1], nodes[2], nodes[3], m["subckt"],
             f"l={_num(d['L'])}", f"w={_num(fw)}", f"m={int(d['n_fingers'])}"]
    dif = process.get("diffusion")
    if dif:
        ad = float(dif["ad_per_w_m"]) * fw
        pd = fw + float(dif["pd_extra_m"])
        parts += [f"ad={_num(ad)}", f"as={_num(ad)}", f"pd={_num(pd)}", f"ps={_num(pd)}"]
    return " ".join(parts)


def validate_input(inp, schema_path=SCHEMA_PATH):
    """oracle_input.schema.json 위반 목록(빈 목록이면 통과). 위반 입력은 진입점이 거부한다(README C13)."""
    import jsonschema
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    v = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(x) for x in e.absolute_path) or '(최상위)'}: {e.message}"
            for e in sorted(v.iter_errors(inp), key=lambda e: list(map(str, e.absolute_path)))]


def loop_break_nets(inp):
    """β 루프를 끊을 넷 = 선언된 되먹임 수동소자(feedback_passives)가 물린 입력 포트 넷. (넷 목록, 막힘 목록)."""
    names = inp.get("feedback_passives") or []
    if not names:
        return [], []
    ports = inp["ports"]
    in_nets = [ports[k] for k in ("input_p", "input_n", "input") if ports.get(k)]
    by = {p["name"]: p for p in inp.get("passives") or []}
    # 소자 단위 판정(fail-closed): 선언된 되먹임 수동소자 각각이 passives 에 있고 입력 포트 넷에 물려 있어야 한다.
    blockers = [f"feedback_passives 의 {n} 이 passives 에 없다" for n in names if n not in by]
    blockers += [f"feedback_passives 의 {n} 이 입력 포트 넷 {in_nets} 에 물려 있지 않다(단자 {by[n]['terminals']})"
                 for n in names if n in by and not set(by[n]["terminals"]) & set(in_nets)]
    nets =[n for n in in_nets if any(n in by[x]["terminals"] for x in names if x in by)]
    if not nets:
        blockers.append("feedback_passives 가 어느 입력 포트 넷에도 물려 있지 않다")
    return nets, blockers


def build_netlist(inp, bias, ac_file, loop=False):
    """loop=False: 본 넷리스트(.op + 개루프 A 의 .ac). loop=True: β 루프 이득 측정용 넷리스트
    (되먹임 수동소자의 입력 쪽 단자를 lbx_<넷> 으로 떼고 직렬 전압원 Vlb·주입 전류원 Ilb 를 넣어 .ac 2회 --
    Middlebrook 이중 주입). loop=True 에서 ac_file 은 두 데이터 파일 이름의 접두사."""
    if bias not in BIASES:
        raise ValueError(f"bias 는 {'|'.join(BIASES)}: {bias!r}")
    if bias == "iso":
        return build_iso_netlist(inp)
    process, tb = inp["process"], inp["testbench"]
    pred = (inp.get("predictions") or {}).get("nodes") or {}
    lut = read_lut_meta(process["lut_npz"])
    blockers, notes = [], []
    for k in ("corner", "temp_c"):
        if lut[k] is None:
            blockers.append(f"LUT npz 에 {k} 메타가 없다: {process['lut_npz']}")
    N = _Nets(inp["rails"])
    devs = inp["devices"]
    kinds = {d["kind"] for d in devs}
    choke, coup = _num(tb["dc_choke_H"]), _num(tb["ac_couple_F"])

    L = [f"* spice_oracle: {inp.get('circuit', '?')} bias={bias}"]
    L += _includes(process, kinds, lut["corner"])
    if lut["temp_c"] is not None:
        L.append(f".temp {_num(lut['temp_c'])}")
    if tb.get("options"):
        L.append(".option " + " ".join(f"{k}={v}" for k, v in tb["options"].items()))
    rail_src = {}
    for r in inp["rails"]:
        if r.get("reference"):
            continue
        nm = f"Vrail_{r['net']}"
        rail_src[r["net"]] = nm
        L.append(f"{nm} {N(r['net'])} 0 DC {_num(r['voltage'])}")
    rail_nets = set(N.rail_v)

    driven, dev_nets, geometry, probes = set(), [], {}, {}
    for d in devs:
        nodes = [N(d[t]) for t in ("drain", "gate", "source", "bulk")]
        L.append(device_line(process, d, nodes))
        driven.update([d["drain"], d["source"]])
        for t in ("drain", "gate", "source", "bulk"):
            if d[t] not in dev_nets:
                dev_nets.append(d[t])
        W_f = float(d["finger_w"]) * int(d["n_fingers"])
        geometry[d["name"]] = {"L": float(d["L"]), "finger_w": float(d["finger_w"]),
                               "n_fingers": int(d["n_fingers"]), "W_from_fingers": W_f,
                               "W_declared": None if d.get("W") is None else float(d["W"])}
        probes[d["name"]] = {p: probe_name(process, d["kind"], f"X{d['name']}", p) for p in OP_PARAMS}

    for s in inp.get("sources") or []:
        a, b = s["terminals"]
        driven.update([a, b])
        letter = {"current": "I", "voltage": "V"}.get(s["kind"])
        if letter is None:
            blockers.append(f"source {s['name']} kind={s['kind']} 미지원")
            continue
        L.append(f"{letter}src_{s['name']} {N(a)} {N(b)} DC {_num(s['value'])}")
        notes.append(f"{s['kind']} source {s['name']}={_num(s['value'])} ({s.get('value_basis', '근거 미기재')})")

    breaks, bb = loop_break_nets(inp) if loop else ([], [])
    blockers += bb
    fbp = set(inp.get("feedback_passives") or [])
    passive_nets = []
    for p in inp.get("passives") or []:
        a, b = p["terminals"]
        if loop and p["name"] in fbp:
            a, b = (f"lbx_{a}" if a in breaks else a), (f"lbx_{b}" if b in breaks else b)
        driven.update([a, b])
        if p["kind"] == "short":  # Z1 제거법 --short: 0 V 전압원으로 단락(apply_z1 이 만든 원소)
            L.append(f"Vshort_{p['name']} {N(a)} {N(b)} DC 0")
            notes.append(f"Z1 --short: {p['name']} 을 0 V 전압원으로 단락")
            for n in (a, b):
                if n not in dev_nets and n not in passive_nets:
                    passive_nets.append(n)
            continue
        letter = {"resistor": "R", "capacitor": "C"}.get(p["kind"])
        if letter is None:
            blockers.append(f"passive {p['name']} kind={p['kind']} 미지원")
            continue
        L.append(f"{letter}p_{p['name']} {N(a)} {N(b)} {_num(p['value'])}")
        notes.append(f"{p['kind']} {p['name']}={_num(p['value'])} ({p.get('value_basis', '근거 미기재')})")
        for n in (a, b):
            if n not in dev_nets and n not in passive_nets:
                passive_nets.append(n)

    ports = inp["ports"]
    inp_p, inp_n = ports.get("input_p"), ports.get("input_n")
    out_p, out_n, out_se = ports.get("output_p"), ports.get("output_n"), ports.get("output")
    in_se = ports.get("input")
    inputs = [x for x in (inp_p, inp_n, in_se) if x]
    if not inputs:
        blockers.append("ports 에 input_p/input_n 또는 input 이 없다")
    if not (out_se or (out_p and out_n)):
        blockers.append("ports 에 output 또는 output_p/output_n 이 없다")
    # 입력 DC + AC
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
    loop_choke = None
    if loop and breaks:
        if tb.get("loop_dc_choke_H") is None:
            blockers.append("testbench.loop_dc_choke_H 없음 -- β 루프 측정의 입력 DC 경로를 정할 수 없다")
        else:
            loop_choke = _num(tb["loop_dc_choke_H"])
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
            L.append(f"Efb_{net} fbs_{net} 0 {N(o)} {N(o_other)} {_num(tb['ac']['diff_feedback_gain'])}")
            L.append(f"Vofs_{net} fbs_{net} fbd_{net} DC {_num(-vin)}")
            L.append(f"Lfb_{net} fbd_{net} {N(net)} {ch}")
            notes.append(f"free: 차동 DC 되먹임 k*(V({o})-V({o_other})) -> {net}, 입력 공통모드 {vin:.6g} V(예측)")
        elif net in fb:
            o = fb[net][1]
            vo = pred.get(o)
            if vo is None:
                blockers.append(f"출력 {o} 예측 DC 전압 없음 -- 되먹임 오프셋을 정할 수 없다")
                continue
            L.append(f"Efb_{net} fbs_{net} 0 {N(o)} 0 1")
            L.append(f"Vofs_{net} fbs_{net} fbd_{net} DC {_num(vo - vin)}")
            L.append(f"Lfb_{net} fbd_{net} {N(net)} {ch}")
            notes.append(f"free: DC 되먹임 {o} -> {net} (V({o})_pred={vo:.6g}, V({net})_pred={vin:.6g})")
        else:
            L.append(f"Vdc_{net} dcs_{net} 0 DC {_num(vin)}")
            L.append(f"Ldc_{net} dcs_{net} {N(net)} {ch}")
        if net in breaks:
            L.append(f"Vlb_{net} {N(net)} lbx_{net} DC 0 AC {_num(ac_mag.get(net, 0))}")
            L.append(f"Ilb_{net} 0 {N(net)} DC 0 AC 0")
        else:
            L.append(f"Cac_{net} {N(net)} acs_{net} {coup}")
            L.append(f"Vac_{net} acs_{net} 0 DC 0 AC {_num(0 if loop else ac_mag.get(net, 0))}")

    # 게이트 전용 넷
    declared_bias = {b["net"]: float(b["value"]) for b in inp.get("bias_voltages") or []}
    gate_bias = {}
    for d in devs:
        g = d["gate"]
        if g in driven or g in rail_nets or g in gate_bias:
            continue
        if g in declared_bias:
            gate_bias[g] = (declared_bias[g], "bias_voltages 선언")
        elif pred.get(g) is not None:
            gate_bias[g] = (float(pred[g]), "예측 노드전압(선언 없음 -- 자동)")
        else:
            blockers.append(f"구동 소자 없는 게이트 넷 {g}: bias_voltages 선언도 예측 전압도 없다")
            continue
        L.append(f"Vbias_{g} {N(g)} 0 DC {_num(gate_bias[g][0])}")
    for net, (v, why) in gate_bias.items():
        notes.append(f"게이트 전용 넷 {net} = {v:.6g} V ({why})")

    held, unheld = [], []
    if bias == "forced":
        for n in dev_nets:
            if n in rail_nets or n in gate_bias or n in inputs:
                continue
            v = pred.get(n)
            if v is None:
                unheld.append(n)
                continue
            L.append(f"Vhold_{n} hs_{n} 0 DC {_num(v)}")
            L.append(f"Lhold_{n} hs_{n} {N(n)} {choke}")
            held.append(n)
        notes.append(f"forced: 소자 단자 넷 {len(held)}개를 예측 전압에 choke 로 고정")
        if unheld:
            notes.append(f"forced: 예측 전압이 없어 고정 못 한 넷(자유): {unheld}")
    elif tb.get("nodeset_from_predictions"):
        ns = [f"v({N(n)})={_num(pred[n])}" for n in dev_nets + passive_nets
              if n not in rail_nets and n not in gate_bias and pred.get(n) is not None]
        step = max(1, int(tb.get("nodeset_per_line", len(ns) or 1)))
        for i in range(0, len(ns), step):
            L.append(".nodeset " + " ".join(ns[i:i + step]))
        notes.append(f"free: .nodeset {len(ns)}개 = 예측 노드전압(뉴턴 초기값)")

    all_nets = [n for n in dev_nets + passive_nets if N(n) != "0"]
    if loop:
        return _loop_tail(L, tb, breaks, ac_mag, ac_file, N, notes, blockers, bias, lut)
    L.append(".control")
    L.append("set noaskquit")
    L.append("op")
    L.append("echo OPSTART")
    for d in devs:
        for p in OP_PARAMS:
            L.append(f"print {probes[d['name']][p]}")
    for n in all_nets:
        L.append(f"print v({N(n)})")
    for net, nm in rail_src.items():
        L.append(f"print i({nm.lower()})")
    for n in held:
        L.append(f"print i(vhold_{n.lower()})")
    L.append("echo OPEND")
    has_ac = bool(inputs) and bool(out_se or (out_p and out_n))
    if has_ac:
        ac = tb["ac"]
        miss = [k for k in ("points_per_decade", "fstart_hz", "fstop_hz") if ac.get(k) is None]
        if miss:
            blockers.append(f"testbench.ac 에 {miss} 없음")
            ac = {k: ac.get(k) or 0 for k in ("points_per_decade", "fstart_hz", "fstop_hz")}
        L.append(f"ac dec {int(ac['points_per_decade'])} {_num(ac['fstart_hz'])} {_num(ac['fstop_hz'])}")
        L.append(f"let hout = v({N(out_se)})" if out_se else f"let hout = v({N(out_p)}) - v({N(out_n)})")
        L.append("set wr_singlescale")
        L.append(f"wrdata {ac_file} hout")
    L.append("quit")
    L.append(".endc")
    L.append(".end")
    blockers = N.blockers + blockers
    meta = {"bias": bias, "lut_meta": lut, "geometry": geometry, "probes": probes, "nets": all_nets,
            "spice_node": {n: N(n) for n in all_nets}, "rail_sources": rail_src, "held": held,
            "unheld": unheld, "gate_bias": {k: v[0] for k, v in gate_bias.items()},
            "inputs": inputs, "has_ac": has_ac, "ac_file": ac_file if has_ac else None,
            "notes": notes, "blockers": blockers}
    return "\n".join(L) + "\n", meta


def _loop_tail(L, tb, breaks, ac_mag, prefix, N, notes, blockers, bias, lut):
    ac = tb["ac"]
    L.append(".control")
    L.append("set noaskquit")
    L.append("set wr_singlescale")
    L.append(f"ac dec {int(ac['points_per_decade'])} {_num(ac['fstart_hz'])} {_num(ac['fstop_hz'])}")
    L.append("wrdata " + f"{prefix}.v.txt " + " ".join(f"v(lbx_{n}) v({N(n)})" for n in breaks))
    for n in breaks:
        L.append(f"alter @vlb_{n.lower()}[acmag] = 0")
        L.append(f"alter @ilb_{n.lower()}[acmag] = {_num(ac_mag.get(n, 0))}")
    L.append(f"ac dec {int(ac['points_per_decade'])} {_num(ac['fstart_hz'])} {_num(ac['fstop_hz'])}")
    L.append("wrdata " + f"{prefix}.i.txt " + " ".join(f"i(vlb_{n.lower()})" for n in breaks))
    L.append("quit")
    L.append(".endc")
    L.append(".end")
    meta = {"bias": bias, "lut_meta": lut, "break_nets": breaks, "weights": [ac_mag.get(n, 0) for n in breaks],
            "v_file": f"{prefix}.v.txt", "i_file": f"{prefix}.i.txt", "notes": notes,
            "blockers": N.blockers + blockers}
    return "\n".join(L) + "\n", meta


def build_iso_netlist(inp):
    """bias=iso(단독 소자): 소자마다 X<name> 인스턴스 하나를 자기 전용 노드에 두고 소스를 0 으로, 게이트·드레인·바디를
    엔진 예측 VGS·VDS·VSB(크기 규칙)에 이상 전압원으로 고정한다. 극성 부호 = models[kind].polarity(n: +1, p: -1):
    V(g) = s*VGS, V(d) = s*VDS, V(b) = -s*VSB. 회로 연결·테스트벤치 없음(.op 만). 예측이나 polarity 가 없는 소자는
    인스턴스를 만들지 않고 meta.iso_skipped 에 이유를 적는다(비교 N/A). 한 소자도 못 만들면 막힘."""
    process = inp["process"]
    pdev = (inp.get("predictions") or {}).get("devices") or {}
    lut = read_lut_meta(process["lut_npz"])
    blockers, notes = [], []
    for k in ("corner", "temp_c"):
        if lut[k] is None:
            blockers.append(f"LUT npz 에 {k} 메타가 없다: {process['lut_npz']}")
    devs = inp["devices"]
    L = [f"* spice_oracle: {inp.get('circuit', '?')} bias=iso (단독 소자, 엔진 예측 VGS/VDS/VSB 고정)"]
    L += _includes(process, {d["kind"] for d in devs}, lut["corner"])
    if lut["temp_c"] is not None:
        L.append(f".temp {_num(lut['temp_c'])}")
    tb = inp.get("testbench") or {}
    if tb.get("options"):
        L.append(".option " + " ".join(f"{k}={v}" for k, v in tb["options"].items()))
    geometry, probes, skipped, applied = {}, {}, {}, {}
    sign = {"n": 1.0, "p": -1.0}
    for d in devs:
        n = d["name"]
        W_f = float(d["finger_w"]) * int(d["n_fingers"])
        geometry[n] = {"L": float(d["L"]), "finger_w": float(d["finger_w"]), "n_fingers": int(d["n_fingers"]),
                       "W_from_fingers": W_f, "W_declared": None if d.get("W") is None else float(d["W"])}
        pol = process["models"][d["kind"]].get("polarity")
        p = pdev.get(n) or {}
        miss = [k for k in ("VGS", "VDS", "VSB") if p.get(k) is None]
        if pol not in sign:
            skipped[n] = f"process.models[{d['kind']}].polarity 없음(n|p)"
            continue
        if miss:
            skipped[n] = f"예측 {miss} 없음"
            continue
        sg = sign[pol]
        vg, vd, vb = sg * float(p["VGS"]), sg * float(p["VDS"]), -sg * float(p["VSB"])
        g_, d_, b_ = f"iso_g_{n}", f"iso_d_{n}", f"iso_b_{n}"
        L.append(f"Viso_g_{n} {g_} 0 DC {_num(vg)}")
        L.append(f"Viso_d_{n} {d_} 0 DC {_num(vd)}")
        L.append(f"Viso_b_{n} {b_} 0 DC {_num(vb)}")
        L.append(device_line(process, d, [d_, g_, "0", b_]))
        probes[n] = {q: probe_name(process, d["kind"], f"X{n}", q) for q in OP_PARAMS}
        applied[n] = {"V_g": vg, "V_d": vd, "V_s": 0.0, "V_b": vb, "polarity": pol}
    if not probes:
        blockers.append("iso: 단독 인스턴스를 만들 소자가 없다(예측 VGS/VDS/VSB 또는 polarity 없음)")
    for n, why in skipped.items():
        notes.append(f"iso: {n} 단독 인스턴스 안 만듦 -- {why}")
    L += [".control", "set noaskquit", "op", "echo OPSTART"]
    for n, pr in probes.items():
        for q in OP_PARAMS:
            L.append(f"print {pr[q]}")
    L += ["echo OPEND", "quit", ".endc", ".end"]
    meta = {"bias": "iso", "lut_meta": lut, "geometry": geometry, "probes": probes, "nets": [], "spice_node": {},
            "rail_sources": {}, "held": [], "unheld": [], "gate_bias": {}, "inputs": [], "has_ac": False,
            "ac_file": None, "iso_applied": applied, "iso_skipped": skipped, "notes": notes, "blockers": blockers}
    return "\n".join(L) + "\n", meta


def apply_z1(inp, omit=(), short=()):
    """Z1 제거법(README C18): omit = 원소(소자·수동소자·이상원) 이름 -> 넷리스트에서 뺌, short = 수동소자 이름 -> 0 V 전압원.
    입력을 바꾸지 않고 바뀐 사본을 돌려준다. 반환 (사본, 변경 기록, 막힘). 변경 대상이 feedback_passives 이면 막힘
    (β 루프 정의가 바뀐다)."""
    import copy
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


def resolve_topology_path(inp, input_path=None, override=None):
    """topology JSON 경로: --topology 인자가 우선, 없으면 입력 topology.path(상대 경로면 입력 파일 폴더 기준). 없으면 None."""
    if override:
        return os.path.abspath(override)
    p = (inp.get("topology") or {}).get("path")
    if not p:
        return None
    if not os.path.isabs(p) and input_path:
        p = os.path.join(os.path.dirname(os.path.abspath(input_path)), p)
    return os.path.abspath(p)


def parse_netlist_elements(text, inp):
    """오라클이 쓴 넷리스트 본문(.control 앞)을 다시 읽어 회로 원소 표를 만든다(C15). 반환
    (elements{이름: (종류, 단자 넷 tuple)}, testbench[원소 이름], unclassified[원소 이름]).
    노드 '0' 은 reference 레일 넷 이름으로 되돌린다. 소자 종류 = subckt 이름 -> models 의 kind(같은 subckt 가 여러 kind 면
    정렬해 '|' 로 이은 문자열)."""
    ref = [r["net"] for r in inp["rails"] if r.get("reference")]
    ref_net = ref[0] if len(ref) == 1 else "0"
    by_sub = {}
    for kind, m in inp["process"]["models"].items():
        by_sub.setdefault(m["subckt"].lower(), []).append(kind)
    elems, tbe, unk = {}, [], []
    back = lambda n: ref_net if n == "0" else n  # noqa: E731
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("*") or ln.startswith("+"):
            continue
        if ln.lower().startswith(".control"):
            break
        if ln.startswith("."):
            continue
        tok = ln.split()
        nm = tok[0]
        if any(nm.startswith(pfx) for pfx in TESTBENCH_PREFIXES):
            tbe.append(nm)
            continue
        hit = None
        for pfx, kind in CIRCUIT_PREFIXES.items():
            if nm.startswith(pfx):
                hit = (pfx, kind)
                break
        if hit is None:
            unk.append(nm)
            continue
        pfx, kind = hit
        name = nm[len(pfx):]
        if kind == "device":
            nodes = tuple(back(n) for n in tok[1:5])
            kinds = sorted(by_sub.get(tok[5].lower(), [])) if len(tok) > 5 else []
            elems[name] = ("|".join(kinds) or f"subckt:{tok[5] if len(tok) > 5 else '?'}", nodes)
        else:
            elems[name] = (kind, tuple(back(n) for n in tok[1:3]))
    return elems, tbe, unk


def topology_elements(topo):
    """topology JSON(netlist + passive_elements + ideal_sources) -> {이름: (종류, 단자 넷 tuple, 바디 선언 여부)}.
    MOS 단자 = (drain, gate, source[, bulk]) -- bulk 는 topology 가 선언한 원소만. 2단자 = terminals 순서 그대로.
    _ 로 시작하는 키·dict 가 아닌 원소는 무시한다(주석). 반환 (원소 표, 이름 중복 목록)."""
    out, dup = {}, []

    def put(name, val):
        if name in out:
            dup.append(name)
        out[name] = val
    for e in topo.get("netlist") or []:
        if not isinstance(e, dict):
            continue
        t = (e.get("drain"), e.get("gate"), e.get("source")) + ((e["bulk"],) if "bulk" in e else ())
        put(e.get("name"), (e.get("kind"), t, "bulk" in e))
    for e in topo.get("passive_elements") or []:
        if isinstance(e, dict):
            put(e.get("name"), (e.get("kind"), tuple(e.get("terminals") or ()), False))
    for e in topo.get("ideal_sources") or []:
        if isinstance(e, dict):
            put(e.get("name"), (TOPOLOGY_SOURCE_KINDS.get(e.get("kind"), f"topology:{e.get('kind')}"),
                                tuple(e.get("terminals") or ()), False))
    return out, dup


def topology_identity(inp, text, topology_path):
    """C15: 넷리스트(text)를 다시 파싱한 원소 집합과 topology JSON 의 집합 비교. 반환 dict
    {status: verified|mismatch|unverified, topology_path, sha256_actual, sha256_declared, diffs[...], compared,
     excluded_testbench, declared_not_in_topology{이름: 이유}, bulk_compared, notes}.
    비교 규칙: 원소 이름 집합이 같고, 원소마다 종류가 같고, 단자 넷이 같아야 한다. MOS 는 (d, g, s) 순서 그대로(+ topology
    가 bulk 를 선언했으면 bulk), 저항·커패시터는 순서 무관, 이상원은 순서 그대로(방향). 입력 passives/sources 중
    not_in_topology_reason 이 있는 원소는 비교에서 빼고 이유와 함께 기록한다(topology 에 같은 이름이 있으면 차이)."""
    import hashlib
    res = {"status": "unverified", "topology_path": topology_path, "sha256_actual": None,
           "sha256_declared": (inp.get("topology") or {}).get("sha256"), "diffs": [], "compared": 0,
           "excluded_testbench": [], "declared_not_in_topology": {}, "bulk_compared": [], "notes": []}
    if not topology_path:
        res["notes"].append("topology 미지정(입력 topology.path 도 --topology 도 없음) -- 연결 동일성 미검증")
        return res
    if not os.path.exists(topology_path):
        res["notes"].append(f"topology 파일 없음: {topology_path} -- 연결 동일성 미검증")
        return res
    with open(topology_path, "rb") as f:
        raw = f.read()
    res["sha256_actual"] = hashlib.sha256(raw).hexdigest()
    if res["sha256_declared"] and res["sha256_declared"] != res["sha256_actual"]:
        res["notes"].append(f"topology 파일 sha256 이 입력 선언값과 다르다(입력 변환 뒤 파일이 바뀜): "
                            f"선언 {res['sha256_declared'][:12]}.. 실제 {res['sha256_actual'][:12]}..")
    try:
        topo = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        res["status"] = "mismatch"
        res["diffs"].append(f"topology JSON 을 읽을 수 없다: {e}")
        return res
    want, dup = topology_elements(topo)
    got, tbe, unk = parse_netlist_elements(text, inp)
    res["excluded_testbench"] = tbe
    diffs = [f"topology 원소 이름 중복: {n}" for n in sorted(set(dup))]
    diffs += [f"넷리스트 원소 {n}: 접두사로 회로/테스트벤치를 가를 수 없다" for n in unk]
    extra = {e["name"]: e["not_in_topology_reason"] for k in ("passives", "sources") for e in inp.get(k) or []
             if e.get("not_in_topology_reason")}
    res["declared_not_in_topology"] = extra
    for n in sorted(extra):
        got.pop(n, None)
    for n in sorted(set(want) - set(got)):
        diffs.append(f"{n}: topology 에 있고 넷리스트에 없다")
    for n in sorted(set(got) - set(want)):
        diffs.append(f"{n}: 넷리스트에 있고 topology 에 없다")
    for n in sorted(set(want) & set(got)):
        wk, wt, has_bulk = want[n]
        gk, gt = got[n]
        res["compared"] += 1
        if gk != wk:
            diffs.append(f"{n}: 종류 topology {wk} != 넷리스트 {gk}")
        if wk in ("resistor", "capacitor"):
            same = sorted(wt) == sorted(gt)
        elif len(gt) == 4 and not has_bulk:
            same = tuple(gt[:3]) == tuple(wt)
        else:
            same = tuple(gt) == tuple(wt)
        if has_bulk:
            res["bulk_compared"].append(n)
        if not same:
            diffs.append(f"{n}: 단자 넷 topology {list(wt)} != 넷리스트 {list(gt[:len(wt)]) if len(gt) == 4 else list(gt)}")
    res["diffs"] = diffs
    res["status"] = "mismatch" if diffs else "verified"
    return res


def write_netlists(inp, bias, out_cir, topology_path=None, require_topology=False, omit=(), short=()):
    """본 넷리스트 + (feedback_passives 가 있으면) 루프 넷리스트를 쓰고 meta 를 돌려준다.
    루프 넷리스트는 <out_cir 확장자 뺀 이름>.loop.cir, meta['loop'] 에 그 메타.
    [신규] meta['topology_identity'] = C15 결과(free/forced: 변경 전 본 넷리스트로 비교, iso: 해당 없음).
    mismatch 이면 막힘, unverified 이고 require_topology 이면 막힘. omit/short 가 있으면 Z1 제거법(meta['z1'])."""
    stem = os.path.splitext(os.path.basename(out_cir))[0]
    work, z1, zb = apply_z1(inp, omit, short)
    text, meta = build_netlist(work, bias, f"{stem}.ac.txt")
    meta["blockers"] = meta["blockers"] + [b for b in zb if b not in meta["blockers"]]
    meta["z1"] = z1
    if bias == "iso":
        ti = {"status": "not_applicable", "topology_path": topology_path, "diffs": [],
              "notes": ["iso 는 회로 연결이 없는 단독 소자 넷리스트 -- C15 대상 아님"]}
    else:
        base_text = text if z1 is None else build_netlist(inp, bias, f"{stem}.ac.txt")[0]
        ti = topology_identity(inp, base_text, topology_path)
        if z1 is not None:
            ti["notes"].append("Z1 변경 전 넷리스트로 비교했다(제거·단락은 진단용 의도된 변경)")
        if ti["status"] == "mismatch":
            meta["blockers"].append(f"C15 topology 연결 동일성 불일치 {len(ti['diffs'])}건: " + "; ".join(ti["diffs"][:8]))
        elif ti["status"] == "unverified" and require_topology:
            meta["blockers"].append("C15 topology 연결 동일성 미검증(--require-topology): " + "; ".join(ti["notes"]))
    ti["required"] = bool(require_topology)
    meta["topology_identity"] = ti
    meta["loop"] = None
    if work.get("feedback_passives") and bias != "iso":
        ltext, lmeta = build_netlist(work, bias, f"{stem}.loop", loop=True)
        lcir = os.path.join(os.path.dirname(os.path.abspath(out_cir)), f"{stem}.loop.cir")
        with open(lcir, "w", encoding="utf-8") as f:
            f.write(ltext)
        lmeta["netlist"] = os.path.basename(lcir)
        meta["loop"] = lmeta
        for b in lmeta["blockers"]:
            if b not in meta["blockers"]:
                meta["blockers"].append(b)
    with open(out_cir, "w", encoding="utf-8") as f:
        f.write(text)
    with open(out_cir + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return meta


def main(argv=None):
    ap = argparse.ArgumentParser(description="오라클 입력 JSON -> ngspice 넷리스트")
    ap.add_argument("oracle_input")
    ap.add_argument("out_cir")
    ap.add_argument("--bias", choices=BIASES, required=True)
    ap.add_argument("--topology", default=None, help="C15 대조용 topology JSON(입력 topology.path 보다 우선)")
    ap.add_argument("--require-topology", action="store_true", help="합격 실행: topology 미검증이면 막힘")
    ap.add_argument("--omit", nargs="+", default=[], help="Z1 제거법: 뺄 원소 이름")
    ap.add_argument("--short", nargs="+", default=[], help="Z1 제거법: 0 V 로 단락할 수동소자 이름")
    a = ap.parse_args(argv)
    inp = load_input(a.oracle_input)
    errs = validate_input(inp)
    if errs:
        print("입력이 oracle_input.schema.json 위반 -- 거부(넷리스트를 쓰지 않음):")
        for e in errs:
            print("  ", e)
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(a.out_cir)), exist_ok=True)
    meta = write_netlists(inp, a.bias, a.out_cir, resolve_topology_path(inp, a.oracle_input, a.topology),
                          a.require_topology, a.omit, a.short)
    print("wrote", a.out_cir, "| C15 topology:", meta["topology_identity"]["status"])
    if meta["blockers"]:
        print("BLOCKERS:", meta["blockers"])
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
