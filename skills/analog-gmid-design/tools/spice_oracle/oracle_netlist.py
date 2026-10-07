# -*- coding: utf-8 -*-
"""oracle_netlist.py -- SPICE 오라클 입력(JSON, oracle_input.schema.json) -> ngspice 넷리스트.

진입점(단독 실행):
    python oracle_netlist.py <oracle_input.json> <out.cir> --bias free|forced

  넷리스트(.cir)와 그 메타(<out.cir>.meta.json: 소자 probe 이름, 넷 목록, 고정한 넷, 경고/막힘)를 쓴다.
  ngspice 는 부르지 않는다(oracle_simulate.py 몫).

공개 함수: build_netlist(inp, bias, ac_file) -> (text, meta), load_input(path), read_lut_meta(npz_path)

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

OP_PARAMS = ("id", "gm", "gds", "vth", "vdsat", "vgs", "vds", "vbs")  # BSIM 동작점 파라미터 이름


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


def build_netlist(inp, bias, ac_file):
    if bias not in ("free", "forced"):
        raise ValueError(f"bias 는 free|forced: {bias!r}")
    process, tb = inp["process"], inp["testbench"]
    pred = (inp.get("predictions") or {}).get("nodes") or {}
    lut = read_lut_meta(process["lut_npz"])
    blockers, notes = [], []
    if lut["corner"] is None or lut["temp_c"] is None:
        blockers.append(f"LUT npz 에 corner/temp_c 메타가 없다: {process['lut_npz']}")
    N = _Nets(inp["rails"])
    devs = inp["devices"]
    kinds = {d["kind"] for d in devs}
    choke, coup = _num(tb["dc_choke_H"]), _num(tb["ac_couple_F"])

    L = [f"* spice_oracle: {inp.get('circuit', '?')} bias={bias}"]
    L += _includes(process, kinds, lut["corner"])
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

    passive_nets = []
    for p in inp.get("passives") or []:
        a, b = p["terminals"]
        driven.update([a, b])
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
    if inp_p and inp_n:
        ac_mag = {inp_p: tb["ac"]["input_p_ac"], inp_n: tb["ac"]["input_n_ac"]}
    elif in_se:
        ac_mag = {in_se: tb["ac"]["input_ac"]}
    for net in inputs:
        driven.add(net)
        vin = pred.get(net)
        if vin is None:
            blockers.append(f"입력 {net} 의 예측 DC 전압 없음(predictions.nodes)")
            continue
        if net in fb and fb[net][0] == "diff":
            _, o, o_other = fb[net]
            L.append(f"Efb_{net} fbs_{net} 0 {N(o)} {N(o_other)} {_num(tb['ac']['diff_feedback_gain'])}")
            L.append(f"Vofs_{net} fbs_{net} fbd_{net} DC {_num(-vin)}")
            L.append(f"Lfb_{net} fbd_{net} {N(net)} {choke}")
            notes.append(f"free: 차동 DC 되먹임 k*(V({o})-V({o_other})) -> {net}, 입력 공통모드 {vin:.6g} V(예측)")
        elif net in fb:
            o = fb[net][1]
            vo = pred.get(o)
            if vo is None:
                blockers.append(f"출력 {o} 예측 DC 전압 없음 -- 되먹임 오프셋을 정할 수 없다")
                continue
            L.append(f"Efb_{net} fbs_{net} 0 {N(o)} 0 1")
            L.append(f"Vofs_{net} fbs_{net} fbd_{net} DC {_num(vo - vin)}")
            L.append(f"Lfb_{net} fbd_{net} {N(net)} {choke}")
            notes.append(f"free: DC 되먹임 {o} -> {net} (V({o})_pred={vo:.6g}, V({net})_pred={vin:.6g})")
        else:
            L.append(f"Vdc_{net} dcs_{net} 0 DC {_num(vin)}")
            L.append(f"Ldc_{net} dcs_{net} {N(net)} {choke}")
        L.append(f"Cac_{net} {N(net)} acs_{net} {coup}")
        L.append(f"Vac_{net} acs_{net} 0 DC 0 AC {_num(ac_mag.get(net, 0))}")

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


def main(argv=None):
    ap = argparse.ArgumentParser(description="오라클 입력 JSON -> ngspice 넷리스트")
    ap.add_argument("oracle_input")
    ap.add_argument("out_cir")
    ap.add_argument("--bias", choices=("free", "forced"), required=True)
    a = ap.parse_args(argv)
    inp = load_input(a.oracle_input)
    stem = os.path.splitext(os.path.basename(a.out_cir))[0]
    text, meta = build_netlist(inp, a.bias, f"{stem}.ac.txt")
    os.makedirs(os.path.dirname(os.path.abspath(a.out_cir)), exist_ok=True)
    with open(a.out_cir, "w", encoding="utf-8") as f:
        f.write(text)
    with open(a.out_cir + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("wrote", a.out_cir)
    if meta["blockers"]:
        print("BLOCKERS:", meta["blockers"])
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
