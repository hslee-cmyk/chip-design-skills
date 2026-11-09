# -*- coding: utf-8 -*-
"""spice_harness.py -- 엔진 예측(engine_dump.py 산출 JSON) + topology.json -> ngspice 넷리스트 ->
.op/.ac -> 엔진 예측 대 SPICE 비교표(JSON + 짧은 표).

사용법:
    python spice_harness.py <engine.json> <out_dir> [--w-source layout|sizing]
                            [--finger-mode layout|lut_bin] [--cl F] [--tol tol.json]
                            [--sat-margin V] [--fstart Hz] [--fstop Hz]

입력
  engine.json : engine_dump.py 가 쓴 파일(sizing, metrics, theta_star, node_pred, device_pred,
                spec_scalars, lut_meta, instance_json 경로, topology_path, repo_root).
모델/코너/온도
  LUT 를 만든 스크립트(<repo>/skills/analog-gmid-design/assets/sky130_lut_sweep.py)의 PDK_ROOT·
  LOD_SPICE 상수와 include 규칙(nfet: __tt.pm3 + __mismatch.corner, pfet: 그 둘 + lod.spice)을
  그대로 쓴다. 코너·온도는 LUT npz 의 corner/temp_c 필드(engine.json lut_meta)에서 읽는다.
  corner 가 'tt' 가 아니면 멈춘다(LUT 스크립트가 tt 파일 이름만 쓰므로 다른 코너 파일 규칙을 모른다).
테스트벤치(되먹임/부하)
  - 레일: spec vdd, 바디는 NMOS=gnd·PMOS=vdd(엔진 derive_vsb_from_nodes 의 가정과 같다).
  - ideal_sources(전류원): value_amp, 없으면 theta_star[같은 이름]. 둘 다 없으면 막힘으로 보고.
  - passive_elements: 저항 value_ohm / nulling_reference_device(1/gm, 엔진 규칙) / 1e9(엔진
    _DEFAULT_SENSE_RESISTOR_OHM 규칙). 커패시터 value_farad / value_from_spec(spec 키). 못 정하면 막힘.
  - 아무 소자도 구동하지 않는 게이트 전용 넷(포트 아님)은 엔진 예측 게이트 전압으로 고정(바이어스 강제).
  - 입력 포트: DC 는 L(1e12 H)로, AC 는 C(1 F)로 넣는다. 출력과 반대 극성 입력에는 DC 되먹임
    (출력 - (V_out_pred - V_in_pred))을 걸어 DC 동작점의 출력 전압을 엔진 예측값에 묶는다.
    단일 출력: out -> input_n, 차동 출력: output_p -> input_n, output_n -> input_p.
    AC 에서는 L 이 열려 개루프 이득 v(out)/v(id) 를 잰다.
  - 부하 C: --cl > spec 'CL' > metrics 선언 중 'CL' 키(엔진이 PM 계산에 쓴 값) 순.
    topology passive_elements 에 이미 부하 커패시터가 있으면 그것을 쓰고 추가하지 않는다.
허용오차
  정하지 않는다. --tol 로 JSON({"ID_rel":..,"VGS_abs_V":..,"gain_db_abs":..,"ugf_rel":..,
  "pm_deg_abs":..,"node_abs_V":..,"gm_rel":..,"gds_rel":..})을 주면 판정하고, 없으면 'N/A'.
"""
import argparse
import importlib.util
import json
import math
import os
import re
import subprocess
import sys

NGSPICE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
RAIL_LO = ("gnd", "GND", "vss", "VSS", "0")
DEFAULT_SENSE_R = 1.0e9          # sizing_recipe._DEFAULT_SENSE_RESISTOR_OHM 과 같은 규칙(엔진 값)
L_BIG, C_BIG = 1e12, 1.0
OP_PARAMS = ("id", "gm", "gds", "vth", "vdsat", "vgs", "vds", "vbs")


# --------------------------------------------------------------------------- 입력
def _load_lut_script(repo_root):
    p = os.path.join(repo_root, "skills", "analog-gmid-design", "assets", "sky130_lut_sweep.py")
    spec = importlib.util.spec_from_file_location("sky130_lut_sweep", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, p


def _model(kind):
    return "sky130_fd_pr__nfet_01v8" if kind == "nmos" else "sky130_fd_pr__pfet_01v8"


def _net(n, rails):
    if n in RAIL_LO:
        return "0"
    return n


def load_inputs(engine_json):
    with open(engine_json, encoding="utf-8") as f:
        eng = json.load(f)
    if not eng.get("engine_ok"):
        raise SystemExit(f"엔진이 끝까지 돌지 않은 dump: {eng.get('engine_error','?')[:300]}")
    with open(eng["topology_path"], encoding="utf-8") as f:
        topo = json.load(f)
    inst = None
    if eng.get("instance_json"):
        with open(eng["instance_json"], encoding="utf-8") as f:
            inst = json.load(f)
    return eng, topo, inst


# --------------------------------------------------------------------------- 기하
def device_geometry(eng, topo, inst, w_source, finger_mode):
    """소자별 (W_total, L, nf). w_source=layout 이면 instance netlist(같은 이름 여러 항목은 합산),
    sizing 이면 엔진 sizing W. finger_mode=layout 이면 instance 의 finger 수,
    lut_bin 이면 W/nf 가 LUT 기준폭 W_ref 의 모델 bin([W_ref, 7um))에 들도록 nf=floor(W/W_ref)."""
    W_ref = eng["lut_meta"]["W_ref_m"]
    seg = {}
    if inst is not None:
        for e in inst["netlist"]:
            g = seg.setdefault(e["name"], {"w": 0.0, "nf": 0, "fw": set(), "l": e["l"]})
            g["w"] += e["w"]
            g["nf"] += int(e["n_fingers"])
            g["fw"].add(round(e["finger_w"], 12))
    geo = {}
    for d in topo["netlist"]:
        n = d["name"]
        s = eng["sizing"][n]
        if w_source == "layout":
            if n not in seg:
                raise SystemExit(f"--w-source layout 인데 instance netlist 에 {n} 이 없다")
            W, L = seg[n]["w"], seg[n]["l"]
        else:
            W, L = s["W"], s["L"]
        # ngspice 는 모델 bin 을 nf 로 나누지 않은 총 W 로 고른다(실측: W=10u nf=2 가 5u nf=1 두 개보다
        # 12% 작고, 총 W>100um 이면 'could not find a valid modelname'). 그래서 finger 하나를
        # w=finger_w, nf=1 인스턴스 하나로 두고 병렬로 놓는다(확산 공유 효과는 빠진다).
        if finger_mode == "layout" and n in seg:
            nf, par = 1, seg[n]["nf"]
        else:
            nf, par = 1, max(1, int(math.floor(W / W_ref + 1e-9)))
        geo[n] = {"W": W, "L": L, "nf": nf, "par": par, "W_finger": W / (nf * par),
                  "W_sizing": s["W"], "W_layout": seg[n]["w"] if n in seg else None,
                  "finger_w_layout": sorted(seg[n]["fw"]) if n in seg else None}
    return geo


def _bin_note(wf):
    # sky130 nfet/pfet_01v8 모델 bin 경계(cells/*/…tt.pm3.spice 의 wmin/wmax): ... 3, 5, 7, 100 um
    if wf < 0.36e-6 or wf > 100e-6:
        return "out_of_model_range"
    return "same_bin_as_LUT" if 5e-6 <= wf < 7e-6 else "other_bin"


# --------------------------------------------------------------------------- 넷리스트
def _includes(lutmod, kinds, corner):
    pdk, lod = lutmod.PDK_ROOT, lutmod.LOD_SPICE
    L = []
    for kind in sorted(kinds):
        cell = "nfet_01v8" if kind == "nmos" else "pfet_01v8"
        L.append(f'.include "{pdk}\\cells\\{cell}\\sky130_fd_pr__{cell}__{corner}.pm3.spice"')
        L.append(f'.include "{pdk}\\cells\\{cell}\\sky130_fd_pr__{cell}__mismatch.corner.spice"')
    if "pmos" in kinds:
        L.append(f'.include "{lod}"')
    return L


def _inst_name(name, geo):
    return f"x{name}" if geo["par"] == 1 else f"x{name}_p0"


def _inst_line(name, kind, d, g, s, b, geo):
    nf, par = geo["nf"], geo["par"]
    W = geo["W"] / par
    L = geo["L"]
    wf = W / nf
    # LUT 스크립트의 면적 규칙(w=5u 에 ad=as=2.5p, pd=ps=7u)을 폭에 비례해 그대로 확장
    ad = 0.5e-6 * W
    pd = (wf + 2e-6) * nf
    out = []
    for i in range(par):
        nm = f"X{name}" if par == 1 else f"X{name}_p{i}"
        out.append(f"{nm} {d} {g} {s} {b} {_model(kind)} l={L*1e6:.6f}u w={W*1e6:.6f}u nf={nf} "
                   f"ad={ad*1e12:.6f}p as={ad*1e12:.6f}p pd={pd*1e6:.6f}u ps={pd*1e6:.6f}u")
    return "\n".join(out)


def resolve_passives(eng, topo, cl_cli):
    spec = eng["spec_scalars"]
    out, blockers = [], []
    for p in topo.get("passive_elements") or []:
        a, b = p["terminals"]
        if p.get("kind") == "resistor":
            if p.get("value_ohm") is not None:
                v, src = float(p["value_ohm"]), "value_ohm"
            elif p.get("nulling_reference_device"):
                ref = p["nulling_reference_device"]
                v, src = 1.0 / eng["sizing"][ref]["gm"], f"1/gm({ref}) (엔진 _resolve_nulling_resistor_ohm 규칙)"
            else:
                v, src = DEFAULT_SENSE_R, "엔진 _DEFAULT_SENSE_RESISTOR_OHM(1e9) 규칙"
            out.append(("R", p["name"], a, b, v, src))
        elif p.get("kind") == "capacitor":
            if p.get("value_farad") is not None:
                v, src = float(p["value_farad"]), "value_farad"
            elif p.get("value_from_spec") and p["value_from_spec"] in spec:
                k = p["value_from_spec"]
                v, src = float(spec[k]), f"spec['{k}'] (엔진 ctx.derived 값은 결과 dict 에 없어 spec 폴백)"
            else:
                blockers.append(f"커패시터 {p['name']} 값 없음(value_farad/value_from_spec 미선언 또는 spec 에 키 없음)")
                continue
            out.append(("C", p["name"], a, b, v, src))
        else:
            blockers.append(f"passive {p['name']} kind={p.get('kind')} 미지원")
    return out, blockers


def load_cap_value(eng, topo, cl_cli):
    if cl_cli is not None:
        return cl_cli, "--cl"
    spec = eng["spec_scalars"]
    if spec.get("CL") is not None:
        return float(spec["CL"]), "spec['CL']"
    for mname, m in (topo.get("sizing_roles", {}).get("metrics") or {}).items():
        if isinstance(m, dict) and m.get("CL") is not None:
            return float(m["CL"]), f"topology metrics['{mname}'].CL (엔진 PM 계산 가정)"
    return None, None


def build_testbench(eng, topo, inst, lutmod, opts):
    vdd = float(eng["spec_scalars"]["vdd"])
    corner = eng["lut_meta"]["corner"]
    temp = eng["lut_meta"]["temp_c"]
    if corner != "tt":
        raise SystemExit(f"LUT corner={corner}: LUT 스크립트는 tt 파일 이름만 쓴다 -- 다른 코너 include 규칙 미정")
    geo = device_geometry(eng, topo, inst, opts.w_source, opts.finger_mode)
    devs = topo["netlist"]
    kinds = {d["kind"] for d in devs}
    rails_hi = {"vdd", "VDD"}
    blockers, notes = [], []

    lines = [f"* spice_harness: {eng['circuit_key']}  w_source={opts.w_source} finger_mode={opts.finger_mode}"]
    lines += _includes(lutmod, kinds, corner)
    lines.append(f".temp {temp}")
    lines.append(".option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7 itl1=500 itl2=500")
    lines.append(f"Vvdd vdd 0 DC {vdd}")

    def N(n):
        return "vdd" if n in rails_hi else _net(n, None)

    driven = set()
    for d in devs:
        lines.append(_inst_line(d["name"], d["kind"], N(d["drain"]), N(d["gate"]), N(d["source"]),
                                "0" if d["kind"] == "nmos" else "vdd", geo[d["name"]]))
        driven.update([d["drain"], d["source"]])
    # ideal sources
    for s in topo.get("ideal_sources") or []:
        a, b = s["terminals"]
        driven.update([a, b])
        if s.get("kind") == "current_source":
            v = s.get("value_amp")
            src = "value_amp"
            if opts.isrc == "engine":
                # 엔진이 실제로 쓴 전류: 전류원 비레일 단자에 드레인이 물린 소자의 엔진 ID
                fed = [d for d in devs if d["drain"] in (a, b) and d["drain"] not in rails_hi
                       and d["drain"] not in RAIL_LO]
                if fed:
                    v_eng = eng["sizing"][fed[0]["name"]]["ID"]
                    if v is not None and abs(v_eng - v) > 1e-3 * abs(v):
                        notes.append(f"주의: {s['name']} 선언값 {v:g} A 와 엔진이 {fed[0]['name']} 에 쓴 ID "
                                     f"{v_eng:g} A 가 다르다 -- --isrc engine 이라 엔진 값을 쓴다")
                    v, src = v_eng, f"엔진 ID({fed[0]['name']})"
            if v is None:
                v = (eng.get("theta_star") or {}).get(s["name"])
                src = "theta_star"
            if v is None:
                blockers.append(f"전류원 {s['name']} 값 없음(value_amp=null, theta_star 에도 없음)")
                continue
            lines.append(f"I{s['name']} {N(a)} {N(b)} DC {v}")
            notes.append(f"전류원 {s['name']}={v:g} A ({src})")
        elif s.get("kind") == "voltage_source":
            v = s.get("value_v")
            if v is None:
                blockers.append(f"전압원 {s['name']} 값 없음")
                continue
            lines.append(f"V{s['name']} {N(a)} {N(b)} DC {v}")
        else:
            blockers.append(f"ideal source {s['name']} kind={s.get('kind')} 미지원")
    # passives
    passives, pb = resolve_passives(eng, topo, opts.cl)
    blockers += pb
    has_load_cap = False
    for typ, name, a, b, v, src in passives:
        driven.update([a, b])
        lines.append(f"{typ}{name} {N(a)} {N(b)} {v}")
        notes.append(f"{typ}{name}={v:g} ({src})")
    # ports
    ports = {k: v for k, v in (topo.get("ports") or {}).items() if isinstance(v, dict)}
    role = {v.get("role"): k for k, v in ports.items()}
    outs = []
    if "single_ended_output" in role:
        outs = [("se", role["single_ended_output"])]
    elif "differential_output_p" in role and "differential_output_n" in role:
        outs = [("p", role["differential_output_p"]), ("n", role["differential_output_n"])]
    else:
        blockers.append("ports 에 출력 역할(single_ended_output / differential_output_p,n) 선언 없음")
    inp, inn = role.get("differential_input_p"), role.get("differential_input_n")
    if not (inp and inn):
        blockers.append("ports 에 differential_input_p/n 선언 없음")
    # load cap: passive 중 출력 넷과 레일 사이 C 가 있으면 그것이 부하
    out_nets = [o for _, o in outs]
    for typ, name, a, b, v, src in passives:
        if typ == "C" and ({a, b} & set(out_nets)) and ({a, b} & set(RAIL_LO)):
            has_load_cap = True
    cl, cl_src = load_cap_value(eng, topo, opts.cl)
    if not has_load_cap:
        if cl is None:
            blockers.append("부하 C 를 정할 근거 없음(--cl / spec CL / metrics CL 모두 없음)")
        else:
            for o in out_nets:
                lines.append(f"CLOAD_{o} {N(o)} 0 {cl}")
            notes.append(f"부하 C={cl:g} F 각 출력 ({cl_src})")
    # 입력 + DC 되먹임
    pred = eng["node_pred"]
    fb_map = {}
    if outs and outs[0][0] == "se":
        fb_map[inn] = outs[0][1]
    elif outs:
        fb_map[inn] = role["differential_output_p"]
        fb_map[inp] = role["differential_output_n"]
    for net, acmag in ((inp, 0.5), (inn, -0.5)):
        if net is None:
            continue
        driven.add(net)
        vin = pred.get(net)
        if vin is None:
            blockers.append(f"입력 {net} 의 엔진 예측 DC 전압 없음")
            continue
        if opts.bias == "forced":
            lines.append(f"Vdc_{net} dcs_{net} 0 DC {vin}")
            lines.append(f"Ldc_{net} dcs_{net} {N(net)} {L_BIG}")
        elif net in fb_map and outs and outs[0][0] != "se":
            # 차동 출력: 차동 성분만 되먹인다(입력 공통모드는 엔진 예측값에 고정, 출력 공통모드는
            # 회로 자신의 CMFB 가 정한다). 출력 공통모드까지 입력으로 되먹이면 공통모드 루프가
            # 양되먹임이 되어 출력이 레일에 붙는 해가 실측됐다(current_reuse, 2026-10-07).
            o = fb_map[net]
            o_other = role["differential_output_p"] if o == role["differential_output_n"] else role["differential_output_n"]
            lines.append(f"Efb_{net} fbs_{net} 0 {N(o)} {N(o_other)} 0.5")
            lines.append(f"Vofs_{net} fbs_{net} fbd_{net} DC {-vin}")
            lines.append(f"Lfb_{net} fbd_{net} {N(net)} {L_BIG}")
            notes.append(f"DC 차동 되먹임 0.5*(V({o})-V({o_other})) -> {net}, 입력 공통모드 고정 {vin:.4f} V(엔진 예측)")
        elif net in fb_map:
            o = fb_map[net]
            vo = pred.get(o)
            if vo is None:
                blockers.append(f"출력 {o} 의 엔진 예측 DC 전압 없음 -- DC 되먹임 오프셋을 정할 수 없다")
                continue
            lines.append(f"Efb_{net} fbs_{net} 0 {N(o)} 0 1")
            lines.append(f"Vofs_{net} fbs_{net} fbd_{net} DC {vo - vin}")
            lines.append(f"Lfb_{net} fbd_{net} {N(net)} {L_BIG}")
            notes.append(f"DC 되먹임 {o} -> {net}, V({o})_pred={vo:.4f}, V({net})_pred={vin:.4f}")
        else:
            lines.append(f"Vdc_{net} dcs_{net} 0 DC {vin}")
            lines.append(f"Ldc_{net} dcs_{net} {N(net)} {L_BIG}")
        lines.append(f"Cac_{net} {N(net)} acs_{net} {C_BIG}")
        lines.append(f"Vac_{net} acs_{net} 0 DC 0 AC {acmag}")
    # 구동 안 되는 게이트 전용 넷 -> 엔진 예측 전압으로 고정
    forced = {}
    for d in devs:
        g = d["gate"]
        if g in driven or g in rails_hi or g in RAIL_LO or g in forced:
            continue
        v = pred.get(g)
        if v is None:
            blockers.append(f"게이트 전용 넷 {g} 의 엔진 예측 전압 없음")
            continue
        forced[g] = v
        lines.append(f"Vbias_{g} {N(g)} 0 DC {v}")
    if forced:
        notes.append("바이어스 강제(구동 소자 없는 게이트 넷, 엔진 예측값): "
                     + ", ".join(f"{k}={v:.4f}" for k, v in forced.items()))

    # control
    nets = sorted({N(x) for d in devs for x in (d["drain"], d["gate"], d["source"])} - {"0"})
    held = []
    if opts.bias == "forced":
        # 바이어스 강제 모드: 모든 내부 넷을 엔진 예측 전압에 L(1e12 H)로 묶는다. DC 동작점은 엔진이
        # 의도한 노드전압 그대로가 되고(각 고정원에 흐르는 전류 = 그 넷의 KCL 잔차), AC 에서는 L 이
        # 열려 실제 소자 모델(용량 포함)을 그 바이어스에서 선형화한 개루프 응답을 잰다.
        for n in nets:
            if n == "vdd" or n in forced or n in (inp, inn):
                continue
            v = pred.get(n)
            if v is None:
                blockers.append(f"강제 모드: 넷 {n} 의 엔진 예측 전압 없음 -- 고정 못 함(자유 넷으로 둠)")
                continue
            lines.append(f"Vhold_{n} hs_{n} 0 DC {v}")
            lines.append(f"Lhold_{n} hs_{n} {n} {L_BIG}")
            held.append(n)
        notes.append(f"바이어스 강제 모드: 내부 넷 {len(held)}개를 엔진 예측 전압에 L 로 고정(DC=엔진 의도 바이어스, AC=개방)")
    if opts.nodeset and opts.bias == "free":
        ns = [f"v({n})={pred[n]:.6f}" for n in nets
              if n != "vdd" and n not in forced and pred.get(n) is not None]
        for i in range(0, len(ns), 8):
            lines.append(".nodeset " + " ".join(ns[i:i + 8]))
        notes.append(f".nodeset {len(ns)}개 넷 = 엔진 예측 노드전압(뉴턴 초기값, 해를 강제하지 않음)")
    lines.append(".control")
    lines.append("set noaskquit")
    lines.append("op")
    lines.append("echo OPSTART")
    for d in devs:
        dp = f"@m.{_inst_name(d['name'], geo[d['name']]).lower()}.m{_model(d['kind'])}"
        for p in OP_PARAMS:
            lines.append(f"print {dp}[{p}]")
    for n in nets:
        lines.append(f"print v({n})")
    lines.append("print i(vvdd)")
    for n in held:
        lines.append(f"print i(vhold_{n.lower()})")
    lines.append("echo OPEND")
    if outs and inp and inn:
        lines.append(f"ac dec {opts.ppd} {opts.fstart} {opts.fstop}")
        if outs[0][0] == "se":
            lines.append(f"let hout = v({N(outs[0][1])})")
        else:
            lines.append(f"let hout = v({N(role['differential_output_p'])}) - v({N(role['differential_output_n'])})")
        lines.append("set wr_singlescale")
        lines.append(f"wrdata {opts.acfile} hout")
    lines.append("quit")
    lines.append(".endc")
    lines.append(".end")
    meta = {"geometry": geo, "forced_bias": forced, "held": held, "notes": notes, "blockers": blockers,
            "outputs": outs, "inputs": {"p": inp, "n": inn}, "nets": nets,
            "load_cap": {"value": cl, "source": cl_src, "from_topology": has_load_cap}}
    return "\n".join(lines) + "\n", meta


# --------------------------------------------------------------------------- 실행/파싱
_NUM = r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)"


def run_ngspice(cir_path, log_path, timeout=300):
    with open(log_path, "w", encoding="utf-8", errors="replace") as fo:
        r = subprocess.run([NGSPICE, "-b", cir_path], cwd=os.path.dirname(cir_path),
                           stdout=fo, stderr=subprocess.STDOUT, timeout=timeout)
    with open(log_path, encoding="utf-8", errors="replace") as f:
        return r.returncode, f.read()


def parse_op(log, devs, geo):
    """병렬 인스턴스(par>1)는 첫 인스턴스 값을 읽고 전류·컨덕턴스만 par 배 한다(같은 바이어스)."""
    res = {}
    for d in devs:
        g = geo[d["name"]]
        dp = f"@m.{_inst_name(d['name'], g).lower()}.m{_model(d['kind'])}"
        r = {}
        for p in OP_PARAMS:
            m = re.search(re.escape(f"{dp}[{p}]") + r"\s*=\s*" + _NUM, log, re.I)
            r[p] = float(m.group(1)) if m else None
            if r[p] is not None and p in ("id", "gm", "gds"):
                r[p] *= g["par"]
        res[d["name"]] = r
    nodes = {}
    for m in re.finditer(r"^v\(([^)]+)\)\s*=\s*" + _NUM, log, re.M | re.I):
        nodes[m.group(1)] = float(m.group(2))
    m = re.search(r"i\(vvdd\)\s*=\s*" + _NUM, log, re.I)
    ivdd = float(m.group(1)) if m else None
    hold = {mm.group(1): float(mm.group(2)) for mm in re.finditer(r"i\(vhold_([^)]+)\)\s*=\s*" + _NUM, log, re.I)}
    if hold:
        res["__hold_currents__"] = hold
    return res, nodes, ivdd


def parse_ac(path):
    import numpy as np
    if not os.path.exists(path):
        return None
    rows = []
    with open(path) as f:
        for line in f:
            parts = line.split()
            try:
                rows.append([float(x) for x in parts])
            except ValueError:
                continue
    a = np.array(rows)
    f, H = a[:, 0], a[:, 1] + 1j * a[:, 2]
    mag = np.abs(H)
    ph = np.unwrap(np.angle(H))
    out = {"gain_dc": float(mag[0]), "gain_dc_db": float(20 * np.log10(mag[0])),
           "phase_dc_deg": float(np.degrees(ph[0])), "f_first_hz": float(f[0])}
    # -3dB
    i3 = np.where(mag < mag[0] / math.sqrt(2))[0]
    out["f3db_hz"] = float(f[i3[0]]) if len(i3) else None
    iu = np.where(mag < 1.0)[0]
    if len(iu) and iu[0] > 0:
        k = iu[0]
        lf = np.interp(0.0, [np.log10(mag[k]), np.log10(mag[k - 1])], [np.log10(f[k]), np.log10(f[k - 1])])
        fu = 10 ** lf
        phu = np.interp(lf, [np.log10(f[k - 1]), np.log10(f[k])], [ph[k - 1], ph[k]])
        lag = math.degrees(ph[0] - phu)
        out["ugf_hz"] = float(fu)
        out["phase_lag_at_ugf_deg"] = float(lag)
        out["pm_deg"] = float(180.0 - lag)
    else:
        out["ugf_hz"] = None
        out["pm_deg"] = None
    if out["f3db_hz"]:
        out["gbw_a0_f3db_hz"] = out["gain_dc"] * out["f3db_hz"]
    return out


# --------------------------------------------------------------------------- 단독 소자 대조
def isolated_netlist(eng, topo, geo, lutmod, devs):
    """소자마다 엔진 예측 VGS/VDS/VSB 를 이상 전원으로 그대로 걸어 ID/gm/gds 만 본다
    (회로 바이어스 오차와 LUT/모델/기하 오차를 분리하기 위함)."""
    kinds = {d["kind"] for d in devs}
    L = [f"* isolated device check {eng['circuit_key']}"] + _includes(lutmod, kinds, eng["lut_meta"]["corner"])
    L.append(f".temp {eng['lut_meta']['temp_c']}")
    skipped = {}
    used = []
    for d in devs:
        n = d["name"]
        s, p = eng["sizing"][n], eng["device_pred"][n]
        if p.get("vgs") is None:
            skipped[n] = "엔진 VGS 예측 없음"
            continue
        sg = 1 if d["kind"] == "nmos" else -1
        L.append(f"Vg_{n} g_{n} 0 DC {sg*p['vgs']}")
        L.append(f"Vd_{n} d_{n} 0 DC {sg*s['vds']}")
        L.append(f"Vb_{n} b_{n} 0 DC {-sg*s['vsb']}")
        L.append(_inst_line(n, d["kind"], f"d_{n}", f"g_{n}", "0", f"b_{n}", geo[n]))
        used.append(d)
    L.append(".control")
    L.append("op")
    for d in used:
        dp = f"@m.{_inst_name(d['name'], geo[d['name']]).lower()}.m{_model(d['kind'])}"
        for prm in OP_PARAMS:
            L.append(f"print {dp}[{prm}]")
    L.append("quit")
    L.append(".endc")
    L.append(".end")
    return "\n".join(L) + "\n", used, skipped


# --------------------------------------------------------------------------- 비교
def _rel(a, b):
    if a is None or b is None or b == 0:
        return None
    return (a - b) / abs(b)


def _judge(err, tol):
    if err is None:
        return "N/A"
    if tol is None:
        return "N/A(tol 미설정)"
    return "PASS" if abs(err) <= tol else "FAIL"


def region_of(kind, op, margin):
    if op.get("id") is None or op.get("vds") is None or op.get("vdsat") is None:
        return None
    vds, vdsat = abs(op["vds"]), abs(op["vdsat"])
    vov = (abs(op["vgs"]) - abs(op["vth"])) if op.get("vgs") is not None and op.get("vth") is not None else None
    inv = None if vov is None else ("strong" if vov > 0.1 else ("moderate" if vov > -0.1 else "weak"))
    if abs(op["id"]) < 1e-12:
        return {"region": "off", "inversion": inv, "vov": vov, "sat_margin_V": vds - vdsat}
    return {"region": "sat" if vds >= vdsat + margin else "triode",
            "inversion": inv, "vov": vov, "sat_margin_V": vds - vdsat}


def compare(eng, topo, meta, op, nodes_sim, ivdd, ac, iso, tol, sat_margin):
    devs = topo["netlist"]
    rows = []
    for d in devs:
        n = d["name"]
        s, p, o = eng["sizing"][n], eng["device_pred"][n], op.get(n, {})
        g = meta["geometry"][n]
        reg = region_of(d["kind"], o, sat_margin) or {}
        id_s = abs(o["id"]) if o.get("id") is not None else None
        gm_s, gds_s = o.get("gm"), o.get("gds")
        r = {"name": n, "kind": d["kind"],
             "W_sizing_um": s["W"] * 1e6, "W_spice_um": g["W"] * 1e6, "L_um": g["L"] * 1e6,
             "nf": g["nf"], "par": g["par"], "W_finger_um": g["W_finger"] * 1e6, "finger_bin": _bin_note(g["W_finger"]),
             "ID_pred_uA": s["ID"] * 1e6, "ID_spice_uA": None if id_s is None else id_s * 1e6,
             "ID_rel": _rel(id_s, s["ID"]),
             "VGS_pred": p.get("vgs"), "VGS_spice": None if o.get("vgs") is None else abs(o["vgs"]),
             "VDS_pred": s["vds"], "VDS_spice": None if o.get("vds") is None else abs(o["vds"]),
             "VSB_pred": s["vsb"], "VSB_spice": None if o.get("vbs") is None else -o["vbs"] * (1 if d["kind"] == "nmos" else -1),
             "gm_pred": s["gm"], "gm_spice": gm_s, "gm_rel": _rel(gm_s, s["gm"]),
             "gds_pred": s["gds"], "gds_spice": gds_s, "gds_rel": _rel(gds_s, s["gds"]),
             "gm_id_pred": s["gm_id"], "gm_id_spice": (gm_s / id_s) if gm_s and id_s else None,
             "VDSAT_spice": None if o.get("vdsat") is None else abs(o["vdsat"]),
             "VTH_spice": None if o.get("vth") is None else abs(o["vth"]),
             "region_spice": reg.get("region"), "inversion_spice": reg.get("inversion"),
             "sat_margin_spice_V": reg.get("sat_margin_V"),
             "region_pred": "sat(엔진 가정)"}
        r["VGS_err_V"] = None if r["VGS_spice"] is None or r["VGS_pred"] is None else r["VGS_spice"] - r["VGS_pred"]
        r["VDS_err_V"] = None if r["VDS_spice"] is None else r["VDS_spice"] - r["VDS_pred"]
        r["judge_ID"] = _judge(r["ID_rel"], tol.get("ID_rel"))
        r["judge_VGS"] = _judge(r["VGS_err_V"], tol.get("VGS_abs_V"))
        r["judge_gm"] = _judge(r["gm_rel"], tol.get("gm_rel"))
        r["judge_gds"] = _judge(r["gds_rel"], tol.get("gds_rel"))
        r["judge_region"] = "PASS" if r["region_spice"] == "sat" else ("FAIL" if r["region_spice"] else "N/A")
        if iso is not None and n in iso:
            ii = iso[n]
            r["iso_ID_uA"] = None if ii.get("id") is None else abs(ii["id"]) * 1e6
            r["iso_ID_rel"] = _rel(None if ii.get("id") is None else abs(ii["id"]), s["ID"])
            r["iso_gm_rel"] = _rel(ii.get("gm"), s["gm"])
            r["iso_gds_rel"] = _rel(ii.get("gds"), s["gds"])
            r["iso_region"] = (None if ii.get("vdsat") is None
                               else ("sat" if s["vds"] >= abs(ii["vdsat"]) + sat_margin else "triode"))
        rows.append(r)
    # nodes
    pred = eng["node_pred"]
    node_rows = []
    for n in meta["nets"]:
        key = n
        pv = pred.get(n)
        if pv is None and n == "vdd":
            pv = eng["spec_scalars"]["vdd"]
        sv = nodes_sim.get(n.lower())
        node_rows.append({"net": key, "V_pred": pv, "V_spice": sv,
                          "err_V": None if pv is None or sv is None else sv - pv,
                          "forced": n in meta["forced_bias"],
                          "judge": _judge(None if pv is None or sv is None else sv - pv, tol.get("node_abs_V"))})
    # performance
    m = eng.get("metrics") or {}
    perf = []
    spec = eng["spec_scalars"]
    gain_keys = [k for k in m if "gain" in k and k.endswith("_db")]
    for k in gain_keys:
        sv = ac["gain_dc_db"] if ac else None
        perf.append({"item": f"gain_db (엔진 {k})", "pred": m[k], "spice": sv,
                     "err": None if sv is None else sv - m[k], "judge": _judge(None if sv is None else sv - m[k], tol.get("gain_db_abs"))})
    for k in [k for k in m if k.endswith("pm_deg")]:
        sv = ac.get("pm_deg") if ac else None
        perf.append({"item": f"PM_deg (엔진 {k})", "pred": m[k], "spice": sv,
                     "err": None if sv is None else sv - m[k], "judge": _judge(None if sv is None else sv - m[k], tol.get("pm_deg_abs"))})
    if spec.get("GBW") is not None:
        sv = ac.get("ugf_hz") if ac else None
        perf.append({"item": "GBW_Hz (spec 설계목표 vs SPICE UGF)", "pred": spec["GBW"], "spice": sv,
                     "err": _rel(sv, spec["GBW"]), "judge": _judge(_rel(sv, spec["GBW"]), tol.get("ugf_rel"))})
    else:
        perf.append({"item": "GBW_Hz", "pred": None, "spice": ac.get("ugf_hz") if ac else None,
                     "err": None, "judge": "N/A(엔진 GBW 예측 없음)"})
    if spec.get("PM_target_deg") is not None:
        sv = ac.get("pm_deg") if ac else None
        perf.append({"item": "PM_deg (spec PM_target_deg 하한)", "pred": spec["PM_target_deg"], "spice": sv,
                     "err": None if sv is None else sv - spec["PM_target_deg"],
                     "judge": "N/A" if sv is None else ("PASS" if sv >= spec["PM_target_deg"] else "FAIL")})
    isup = None if ivdd is None else abs(ivdd) * 1e6
    for k in ("supply_current_uA", "power_uA"):
        if k in m:
            perf.append({"item": f"I(vdd)_uA (엔진 {k})", "pred": m[k], "spice": isup,
                         "err": _rel(None if isup is None else isup, m[k]), "judge": _judge(_rel(isup, m[k]), tol.get("supply_rel"))})
    # 선언 제약(topology constraints) 중 SPICE 로 잴 수 있는 것
    cons = []
    for c in (topo.get("sizing_roles", {}).get("constraints") or []):
        if not isinstance(c, dict):
            continue
        name = c.get("metric") or c.get("name")
        sv = None
        if name and "gain" in name:
            sv = ac["gain_dc_db"] if ac else None
        elif name and name.endswith("pm_deg"):
            sv = ac.get("pm_deg") if ac else None
        if sv is None:
            continue
        lim = c.get("value")
        if lim is None and c.get("value_from_spec"):
            lim = spec.get(c["value_from_spec"])
        op_ = c.get("op") or c.get("type")
        ok = None
        if lim is not None and op_ in (">=", "min", "ge"):
            ok = sv >= lim
        elif lim is not None and op_ in ("<=", "max", "le"):
            ok = sv <= lim
        cons.append({"constraint": c, "spice": sv, "ok": ok})
    return rows, node_rows, perf, cons


def fmt(v, f="{:.4g}"):
    if v is None:
        return "-"
    if isinstance(v, str):
        return v
    return f.format(v)


def table_md(eng, rows, node_rows, perf, cons, meta, ac):
    L = [f"### {eng['circuit_key']} -- 엔진 예측 vs SPICE",
         f"- 모델: sky130 {eng['lut_meta']['corner']}, {eng['lut_meta']['temp_c']} C (LUT npz 메타와 같음)",
         f"- 기하: " + meta["mode"]]
    for n in meta["notes"]:
        L.append(f"- {n}")
    L.append("")
    L.append("| 항목 | 엔진 | SPICE | 차이 | 판정 |")
    L.append("|---|---|---|---|---|")
    for p in perf:
        L.append(f"| {p['item']} | {fmt(p['pred'])} | {fmt(p['spice'])} | {fmt(p['err'])} | {p['judge']} |")
    if ac:
        L.append(f"| (참고) f-3dB / A0*f-3dB | - | {fmt(ac.get('f3db_hz'))} / {fmt(ac.get('gbw_a0_f3db_hz'))} | | |")
    for c in cons:
        L.append(f"| 선언 제약 {json.dumps({k: v for k, v in c['constraint'].items() if not k.startswith('_')}, ensure_ascii=False)} | | {fmt(c['spice'])} | | {c['ok']} |")
    L.append("")
    L.append("| 소자 | W엔진/W_spice um | nf x 병렬(bin) | ID엔진/SPICE uA | ID차 | VGS엔진/SPICE | VDS엔진/SPICE | VDSAT | 영역 | gm차 | gds차 | 단독 ID차(sizing W, LUT bin) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['name']} | {fmt(r['W_sizing_um'])}/{fmt(r['W_spice_um'])} | {r['nf']}x{r['par']}({r['finger_bin']}) | "
                 f"{fmt(r['ID_pred_uA'])}/{fmt(r['ID_spice_uA'])} | {fmt(r['ID_rel'], '{:+.1%}')} | "
                 f"{fmt(r['VGS_pred'], '{:.3f}')}/{fmt(r['VGS_spice'], '{:.3f}')} | {fmt(r['VDS_pred'], '{:.3f}')}/{fmt(r['VDS_spice'], '{:.3f}')} | "
                 f"{fmt(r['VDSAT_spice'], '{:.3f}')} | {r['region_spice']}/{r['inversion_spice']} | "
                 f"{fmt(r['gm_rel'], '{:+.1%}')} | {fmt(r['gds_rel'], '{:+.1%}')} | {fmt(r.get('iso_ID_rel'), '{:+.1%}')} |")
    L.append("")
    L.append("| 넷 | 엔진 V | SPICE V | 차 | 강제 |")
    L.append("|---|---|---|---|---|")
    for n in node_rows:
        L.append(f"| {n['net']} | {fmt(n['V_pred'], '{:.4f}')} | {fmt(n['V_spice'], '{:.4f}')} | {fmt(n['err_V'], '{:+.4f}')} | {'Y' if n['forced'] else ''} |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("engine_json")
    ap.add_argument("out_dir")
    ap.add_argument("--w-source", choices=("layout", "sizing"), default="layout")
    ap.add_argument("--finger-mode", choices=("layout", "lut_bin"), default="layout")
    ap.add_argument("--cl", type=float, default=None)
    ap.add_argument("--tol", default=None, help="허용오차 JSON 파일(사용자 결정). 없으면 판정 N/A")
    ap.add_argument("--sat-margin", type=float, default=0.0, help="포화 판정 VDS-VDSAT 여유(V, 사용자 결정)")
    ap.add_argument("--fstart", type=float, default=1e-2)
    ap.add_argument("--fstop", type=float, default=1e10)
    ap.add_argument("--ppd", type=int, default=40)
    ap.add_argument("--tag", default="")
    ap.add_argument("--isrc", choices=("topology", "engine"), default="topology",
                    help="ideal 전류원 값: topology 선언값 또는 엔진이 그 소자에 쓴 ID")
    ap.add_argument("--no-nodeset", dest="nodeset", action="store_false")
    ap.add_argument("--bias", choices=("free", "forced"), default="free",
                    help="free: 회로가 스스로 DC 해를 찾음 / forced: 내부 넷을 엔진 예측 전압에 L 로 고정")
    opts = ap.parse_args(argv)
    os.makedirs(opts.out_dir, exist_ok=True)
    eng, topo, inst = load_inputs(opts.engine_json)
    lutmod, lutpath = _load_lut_script(eng["repo_root"])
    tol = {}
    if opts.tol:
        with open(opts.tol, encoding="utf-8") as f:
            tol = json.load(f)
    tag = f"{eng['circuit_key']}{('.' + opts.tag) if opts.tag else ''}"
    opts.acfile = os.path.join(opts.out_dir, f"{tag}.ac.txt").replace("\\", "/")
    if os.path.exists(opts.acfile):
        os.remove(opts.acfile)
    cir, meta = build_testbench(eng, topo, inst, lutmod, opts)
    meta["mode"] = (f"bias={opts.bias}, w_source={opts.w_source}, finger_mode={opts.finger_mode}, isrc={opts.isrc}, "
                    f"nodeset={opts.nodeset}")
    cir_path = os.path.join(opts.out_dir, f"{tag}.cir")
    with open(cir_path, "w") as f:
        f.write(cir)
    result = {"circuit_key": eng["circuit_key"], "lut_script": lutpath, "netlist": cir_path,
              "mode": meta["mode"], "notes": meta["notes"], "blockers": list(meta["blockers"]),
              "tolerances": tol or None, "sat_margin_V": opts.sat_margin}
    if meta["blockers"]:
        print("BLOCKERS:", meta["blockers"])
    rc, log = run_ngspice(cir_path, os.path.join(opts.out_dir, f"{tag}.log"))
    op, nodes_sim, ivdd = parse_op(log, topo["netlist"], meta["geometry"])
    hold_i = op.pop("__hold_currents__", {})
    if all(v.get("id") is None for v in op.values()):
        result["blockers"].append(f"ngspice .op 결과 파싱 실패(rc={rc}) -- 로그 {tag}.log 참고: "
                                  + " | ".join(l for l in log.splitlines() if "rror" in l)[:600])
    ac = parse_ac(opts.acfile)
    # 단독 소자
    # 단독 소자 대조는 LUT 충실도만 본다: 엔진 sizing W 를 LUT 기준폭 bin 의 nf=1 병렬 인스턴스로
    # (spice-verification-workflow.md §2: W=L*ID/IDu 로 만든 W 로 인스턴스화해 ID 가 나오는지 확인).
    geo_iso = device_geometry(eng, topo, inst, "sizing", "lut_bin")
    iso_cir, used, skipped = isolated_netlist(eng, topo, geo_iso, lutmod, topo["netlist"])
    iso_path = os.path.join(opts.out_dir, f"{tag}.iso.cir")
    with open(iso_path, "w") as f:
        f.write(iso_cir)
    _, iso_log = run_ngspice(iso_path, os.path.join(opts.out_dir, f"{tag}.iso.log"))
    iso_raw, _, _ = parse_op(iso_log, used, geo_iso)
    iso_raw.pop("__hold_currents__", None)
    rows, node_rows, perf, cons = compare(eng, topo, meta, op, nodes_sim, ivdd, ac, iso_raw, tol, opts.sat_margin)
    result.update({"engine_metrics": eng.get("metrics"), "theta_star": eng.get("theta_star"),
                   "spice_ac": ac, "spice_supply_current_uA": None if ivdd is None else abs(ivdd) * 1e6,
                   "kcl_residual_uA_by_net(강제 모드: 고정원 전류)": {k: v * 1e6 for k, v in sorted(hold_i.items(), key=lambda kv: -abs(kv[1]))},
                   "performance": perf, "declared_constraints_spice": cons,
                   "devices": rows, "nodes": node_rows, "iso_skipped": skipped,
                   "engine_node_conflicts": eng.get("node_voltage_report", {}).get("conflicts")})
    n_sat = sum(1 for r in rows if r["region_spice"] == "sat")
    result["summary"] = {"devices": len(rows), "sat_in_spice": n_sat,
                         "not_sat": [r["name"] for r in rows if r["region_spice"] != "sat"]}
    jp = os.path.join(opts.out_dir, f"{tag}.compare.json")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, default=str)
    md = table_md(eng, rows, node_rows, perf, cons, meta, ac)
    mp = os.path.join(opts.out_dir, f"{tag}.compare.md")
    with open(mp, "w", encoding="utf-8") as f:
        f.write(md)
    print(md)
    print("wrote", jp, mp)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
