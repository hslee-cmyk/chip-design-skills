# -*- coding: utf-8 -*-
"""oracle_netlist.py -- SPICE 오라클 입력(JSON, oracle_input.schema.json) -> ngspice 넷리스트.

진입점(단독 실행):
    python oracle_netlist.py <oracle_input.json> <out.cir> --bias free|forced

  넷리스트(.cir)와 그 메타(<out.cir>.meta.json: 소자 probe 이름, 넷 목록, 고정한 넷, 경고/막힘)를 쓴다.
  ngspice 는 부르지 않는다(oracle_simulate.py 몫).

공개 함수: build_netlist(inp, bias, ac_file, loop=False) -> (text, meta), write_netlists(inp, bias, out_cir) -> meta,
          validate_input(inp) -> [위반], loop_break_nets(inp), load_input(path), read_lut_meta(npz_path)
입력은 먼저 oracle_input.schema.json 으로 검증한다. 위반이면 넷리스트를 쓰지 않고 반환 2(README C13).

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
    blockers = [f"feedback_passives 의 {n} 이 passives 에 없다" for n in names if n not in by]
    nets = [n for n in in_nets if any(n in by[x]["terminals"] for x in names if x in by)]
    if not nets:
        blockers.append("feedback_passives 가 어느 입력 포트 넷에도 물려 있지 않다")
    return nets, blockers


def build_netlist(inp, bias, ac_file, loop=False):
    """loop=False: 본 넷리스트(.op + 개루프 A 의 .ac). loop=True: β 루프 이득 측정용 넷리스트
    (되먹임 수동소자의 입력 쪽 단자를 lbx_<넷> 으로 떼고 직렬 전압원 Vlb·주입 전류원 Ilb 를 넣어 .ac 2회 --
    Middlebrook 이중 주입). loop=True 에서 ac_file 은 두 데이터 파일 이름의 접두사."""
    if bias not in ("free", "forced"):
        raise ValueError(f"bias 는 free|forced: {bias!r}")
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


def write_netlists(inp, bias, out_cir):
    """본 넷리스트 + (feedback_passives 가 있으면) 루프 넷리스트를 쓰고 meta 를 돌려준다.
    루프 넷리스트는 <out_cir 확장자 뺀 이름>.loop.cir, meta['loop'] 에 그 메타."""
    stem = os.path.splitext(os.path.basename(out_cir))[0]
    text, meta = build_netlist(inp, bias, f"{stem}.ac.txt")
    meta["loop"] = None
    if inp.get("feedback_passives"):
        ltext, lmeta = build_netlist(inp, bias, f"{stem}.loop", loop=True)
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
    ap.add_argument("--bias", choices=("free", "forced"), required=True)
    a = ap.parse_args(argv)
    inp = load_input(a.oracle_input)
    errs = validate_input(inp)
    if errs:
        print("입력이 oracle_input.schema.json 위반 -- 거부(넷리스트를 쓰지 않음):")
        for e in errs:
            print("  ", e)
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(a.out_cir)), exist_ok=True)
    meta = write_netlists(inp, a.bias, a.out_cir)
    print("wrote", a.out_cir)
    if meta["blockers"]:
        print("BLOCKERS:", meta["blockers"])
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
