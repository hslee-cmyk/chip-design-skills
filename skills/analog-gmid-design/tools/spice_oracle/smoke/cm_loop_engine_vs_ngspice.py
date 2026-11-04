# -*- coding: utf-8 -*-
"""공통 모드(CMFB) 루프 PM -- 엔진 대 ngspice 대조 (스모크 실행기, 2026-10-08).

입력: 오라클 입력 JSON(`cm_output_loop` true, 소자 기하·수동소자 값·바이어스 예측) 과 `oracle_run.py --bias forced` 가 쓴 산출물.
하는 일
  1. 오라클 forced 넷리스트의 .op 에서 MOS 마다 소신호 값을 ngspice 에서 직접 뽑는다(gm, gmbs, gds, 단자 용량 행렬, 접합 용량).
     엔진 `SsDevice` 의 정의에 맞춘다: cgs = -∂Qg/∂Vs, cgd = -∂Qg/∂Vd, cgb = -∂Qg/∂Vb (ngspice `[cgs]` 등은 ∂Qg/∂V 라 부호 반전),
     cdb = capbd, csb = capbs (엔진 접합 용량 정본 = PDK 접합 모형).
  2. 그 값으로 엔진 계(`ss_circuit` -> `metrics_ss` 와 같은 `_Ledger`/`_plan`/`_analysis` 경로)를 만들어 spec 뷰
     (`default_views`: DM 되먹임 loop, CM loop)의 PM 을 낸다.
  3. 오라클 sim.json 의 `cm_loop`(ngspice Middlebrook) 및 `ac`(DM β 루프) 와 대조한다.
엔진의 LUT -> 소신호 선형화는 이 스크립트가 쓰지 않는다(ngspice 가 낸 소신호 값을 엔진 MNA 에 넣는다) -- 이 대조가 보는 것은
'절단 위치·Middlebrook·PM 정의·안정성 규칙이 같은 회로에서 같은 값을 내는가' 이고, LUT 정확도(gm/ID 표 대 BSIM)는 아니다.
사용: python cm_loop_engine_vs_ngspice.py <oracle_input.json> <oracle_out_dir> <stem> <out.json> [--ngspice EXE]
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

import numpy

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ASSETS)

from gmid_engine.authoring import default_views, load_topology  # noqa: E402
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, ELEMENT_SOURCE  # noqa: E402
from gmid_engine.metrics import ss_metrics as sm  # noqa: E402
from gmid_engine.metrics.ss_circuit import ss_circuit  # noqa: E402
from gmid_engine.metrics.ss_types import MetricRequest, SsDevice  # noqa: E402
from gmid_engine.sizing import CURRENT_SOURCE  # noqa: E402

PARAMS = ("gm", "gmbs", "gds", "cgd", "cgs", "cgb", "capbd", "capbs")


def ngspice_small_signal(cir, devices, exe, work):
    """forced 넷리스트 본문 + .op + MOS 소신호 print -> {소자: {param: 값}} (ngspice 원값)."""
    body = open(cir, encoding="utf-8").read().split(".control")[0]
    probe = {d["name"]: "@m.x%s.m%s[%%s]" % (d["name"].lower(), d["_subckt"]) for d in devices}
    ctl = [".control", "set noaskquit", "op", "echo OPSTART"]
    ctl += ["print " + probe[n] % p for n in probe for p in PARAMS]
    ctl += ["echo OPEND", "quit", ".endc", ".end"]
    path = os.path.join(work, "ss_probe.cir")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body + "\n".join(ctl) + "\n")
    out = subprocess.run([exe, "-b", path], capture_output=True, text=True, errors="replace").stdout
    got = {n: {} for n in probe}
    for n in probe:
        for p in PARAMS:
            m = re.search(re.escape(probe[n] % p) + r"\s*=\s*([-+0-9.eE]+)", out, re.I)
            if m is None:
                raise RuntimeError("ngspice 출력에 %s %s 없음" % (n, p))
            got[n][p] = float(m.group(1))
    return got


def engine_devices(topo, inp, ng):
    bulk = {d["name"]: d["bulk"] for d in inp["devices"]}
    out = []
    for d in sorted(topo.devices, key=lambda x: x.name):
        v = ng[d.name]
        ss = SsDevice(gm=abs(v["gm"]), gmb=abs(v["gmbs"]), gds=abs(v["gds"]), cgg=0.0, cgs=-v["cgs"], cgd=-v["cgd"],
                      cgb=-v["cgb"], cdb=v["capbd"], csb=v["capbs"], cap_model="ngspice_op_matrix",
                      gmb_model="ngspice_gmbs", junction_model="ngspice_capbd_capbs")
        out.append((d.name, ELEMENT_MOS, d.kind, (("d", d.d), ("g", d.g), ("s", d.s)), bulk[d.name], ss))
    for p in sorted(topo.passives, key=lambda x: x.name):
        out.append((p.name, ELEMENT_PASSIVE, p.kind, (("t0", p.terminals[0]), ("t1", p.terminals[1])), None, None))
    for s in topo.sources:
        out.append((s.name, ELEMENT_SOURCE, CURRENT_SOURCE, (("t0", s.terminals[0]), ("t1", s.terminals[1])), None, None))
    return out


def engine_metrics(topo, devices, passive_values, feedback):
    views = default_views(topo, feedback)
    nets = sorted({n for d in topo.devices for n in (d.d, d.g, d.s)} | {n for p in topo.passives for n in p.terminals}
                  | set(topo.rails))
    ground = sorted(views.fixed_nets - {p.net for p in topo.ports if p.direction == "input"})
    inputs = sorted(p.net for p in topo.ports if p.direction == "input")
    ss = ss_circuit(tuple(nets), ground, inputs, tuple(devices), tuple(sorted(passive_values.items())))
    requests = {"pm_ss_deg": MetricRequest("pm_ss_deg", views.loop), "pm_cm_ss_deg": MetricRequest("pm_cm_ss_deg", views.cm_loop)}
    ledger = sm._Ledger(ss)
    plans = {k: sm._plan(r, ledger) for k, r in requests.items()}
    responses, cuts = ledger.solve()
    out = {"views": {"loop": views.loop, "cm_loop": views.cm_loop}}
    for k, r in requests.items():
        analysis, source = sm._analysis(plans[k], responses, cuts)
        res = sm.metric_value(k, analysis)
        out[k] = {"pm_deg": None if res.value is None else float(res.value), "undefined": [(u.quantity, u.code) for u in res.undefined],
                  "dc_db": analysis.gain_db, "ugf_hz": analysis.ugf_hz, "dc_value": analysis.dc_value}
        factor = source[0]
        out[k]["omegas"] = numpy.asarray(factor.response.omegas)
        out[k]["T"] = numpy.asarray(factor.samples)
        out[k]["factor"] = factor
    return out


def ngspice_T(out_dir, stem, key):
    """oracle sim.json 의 루프 파일에서 Middlebrook T(f) (loop_gain) 를 다시 읽는다."""
    sys.path.insert(0, os.path.dirname(HERE))
    from cm_loop_variants import loop_gain
    meta = json.load(open(os.path.join(out_dir, stem + ".cir.meta.json"), encoding="utf-8"))
    lm = meta[key]
    f, re_, im = loop_gain(os.path.join(out_dir, lm["v_file"]), os.path.join(out_dir, lm["i_file"]), lm["weights"])
    return numpy.asarray(f), numpy.asarray(re_) + 1j * numpy.asarray(im)


def linear_reference(topo, inp, ng, exe, work, kind):
    """엔진과 같은 소신호 값(VCCS gm·gmb·gds + 5용량 + 수동소자)을 ngspice 선형 넷리스트로 옮기고 같은 Middlebrook 이중 주입
    (오라클 `loop_gain`)을 건다 -- BSIM 모형 차이를 뺀 '엔진 MNA 대 ngspice' 대조 기준. kind = "cm"(차동 출력 쌍 동일 부호 주입, 소비자 쪽
    단자를 lbx 로) | "dm"(입력 포트 β 루프, feedback_passives). 반환 (f, T)."""
    from cm_loop_variants import loop_gain
    bulk = {d["name"]: d["bulk"] for d in inp["devices"]}
    values = {p["name"]: p["value"] for p in inp["passives"]}
    ports = {pt.net: pt for pt in topo.ports}
    if kind == "cm":
        breaks = sorted(pt.net for pt in topo.ports if pt.direction == "output")
        weights = [1 / len(breaks)] * len(breaks)
        moved = set()
        from gmid_engine.authoring.spec_views import cm_loop_view
        names = dict(cm_loop_view(topo)[0].cuts)                                  # 엔진 cm_partition 이 정한 구동자
        drv_moved = {d.name: next(t for t in ("d", "s") if getattr(d, t) == names[d.name]) for d in topo.devices if d.name in names}
    else:
        breaks = sorted(pt.net for pt in topo.ports if pt.direction == "input")
        weights = [-0.5 if pt.role.endswith("_n") else 0.5 for pt in (ports[n] for n in breaks)]
        moved, drv_moved = set(inp["feedback_passives"]), {}

    def net(n):
        return "0" if n == "gnd" else n
    lines = ["* linear small-signal model of the engine (same values as the engine MNA)"]
    for d in topo.devices:
        v = ng[d.name]
        dd, g, s_, b = net(d.d), net(d.g), net(d.s), net(bulk[d.name])
        if drv_moved.get(d.name) == "d":
            dd = "lbx_" + dd
        elif drv_moved.get(d.name) == "s":
            s_ = "lbx_" + s_
        lines += [f"Gm_{d.name} {dd} {s_} {g} {s_} {abs(v['gm'])}", f"Gb_{d.name} {dd} {s_} {b} {s_} {abs(v['gmbs'])}",
                  f"Gd_{d.name} {dd} {s_} {dd} {s_} {abs(v['gds'])}"]
        for nm, x, y, val in (("gs", g, s_, -v["cgs"]), ("gd", g, dd, -v["cgd"]), ("gb", g, b, -v["cgb"]),
                              ("db", dd, b, v["capbd"]), ("sb", s_, b, v["capbs"])):
            lines.append(f"C{nm}_{d.name} {x} {y} {val}")
    for p in topo.passives:
        a, b = (net(t) for t in p.terminals)
        if p.name in moved:
            a = "lbx_" + a if p.terminals[0] in breaks else a
            b = "lbx_" + b if p.terminals[1] in breaks else b
        lines.append(f"{'R' if p.kind == 'resistor' else 'C'}{p.name} {a} {b} {values[p.name]}")
    lines.append("Vvdd vdd 0 0")
    lines += [f"Vin_{pt.net} {pt.net} 0 0" for pt in topo.ports if pt.direction == "input" and pt.net not in breaks]
    for n, w in zip(breaks, weights):
        lines += [f"Vlb_{n} {n} lbx_{n} DC 0 AC {w}", f"Ilb_{n} 0 {n} DC 0 AC 0"]
    pre = os.path.join(work, "lin_" + kind)
    ac = "ac dec 20 100 1e10"
    lines += [".control", "set noaskquit", "set wr_singlescale", ac,
              f"wrdata {pre}.v.txt " + " ".join(f"v(lbx_{n}) v({n})" for n in breaks)]
    lines += [x for n, w in zip(breaks, weights) for x in (f"alter @vlb_{n.lower()}[acmag] = 0", f"alter @ilb_{n.lower()}[acmag] = {w}")]
    lines += [ac, f"wrdata {pre}.i.txt " + " ".join(f"i(vlb_{n.lower()})" for n in breaks) + "".join(f" v({n})" for n in breaks),
              "quit", ".endc", ".end"]
    with open(pre + ".cir", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    subprocess.run([exe, "-b", pre + ".cir"], capture_output=True, text=True, errors="replace")
    f, re_, im = loop_gain(pre + ".v.txt", pre + ".i.txt", weights)
    return numpy.asarray(f), numpy.asarray(re_) + 1j * numpy.asarray(im)


def compare_curves(eng, f_ng, T_ng):
    """엔진 T(jω) 를 ngspice 와 같은 주파수에서 직접 풀어(`product_at`, 보간 없음) 대조: 크기 dB 차와 위상 차(deg, 2π 정렬)의 최댓값.
    잡음 바닥(|T| <= 1e-6) 아래 표본은 위상이 무의미해 뺀다."""
    from gmid_engine.metrics._helpers_product import product_at
    factors = (eng["factor"],)
    T_eng = numpy.array([product_at(factors, 2 * math.pi * float(f))[0] for f in f_ng])
    sel = numpy.abs(T_ng) > 1e-6
    d_db = 20 * numpy.log10(numpy.abs(T_eng[sel]) / numpy.abs(T_ng[sel]))
    d_deg = numpy.degrees(numpy.angle(T_eng[sel] / T_ng[sel]))
    return {"points": int(sel.sum()), "max_abs_db_diff": float(numpy.max(numpy.abs(d_db))),
            "max_abs_deg_diff": float(numpy.max(numpy.abs(d_deg))), "band_hz": [float(f_ng[0]), float(f_ng[-1])]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("oracle_input")
    ap.add_argument("out_dir")
    ap.add_argument("stem")
    ap.add_argument("out_json")
    ap.add_argument("--ngspice", default="C:/ngspice/Spice64/bin/ngspice_con.exe")
    a = ap.parse_args(argv)
    inp = json.load(open(a.oracle_input, encoding="utf-8"))
    topo = load_topology(os.path.join(ASSETS, "assets", "library", inp["circuit"] + ".topology.json"))
    for d in inp["devices"]:
        d["_subckt"] = inp["process"]["models"][d["kind"]]["subckt"]
    ng = ngspice_small_signal(os.path.join(a.out_dir, a.stem + ".cir"), inp["devices"], a.ngspice, a.out_dir)
    passive_values = {p["name"]: p["value"] for p in inp["passives"]}
    eng = engine_metrics(topo, engine_devices(topo, inp, ng), passive_values, tuple(inp["feedback_passives"]))
    sim = json.load(open(os.path.join(a.out_dir, a.stem + ".sim.json"), encoding="utf-8"))
    cm, ac = sim["cm_loop"], sim["ac"]
    report = {"circuit": inp["circuit"], "stem": a.stem}
    f, T = ngspice_T(a.out_dir, a.stem, "cm_loop")
    report["cm"] = {"engine_pm_deg": eng["pm_cm_ss_deg"]["pm_deg"], "engine_undefined": eng["pm_cm_ss_deg"]["undefined"],
                    "engine_dc_db": eng["pm_cm_ss_deg"]["dc_db"], "engine_ugf_hz": eng["pm_cm_ss_deg"]["ugf_hz"],
                    "ngspice_pm_deg": cm["pm_deg"], "ngspice_pm_undefined": cm["pm_undefined"],
                    "ngspice_pm_deg_raw": cm["pm_deg_raw"], "ngspice_dc_db": (cm["measures"] or {}).get("dc_gain_db"),
                    "ngspice_ugf_hz": (cm["measures"] or {}).get("ugf_hz"), "curve": compare_curves(eng["pm_cm_ss_deg"], f, T)}
    f, T = ngspice_T(a.out_dir, a.stem, "loop")
    report["dm"] = {"engine_pm_deg": eng["pm_ss_deg"]["pm_deg"], "engine_undefined": eng["pm_ss_deg"]["undefined"],
                    "engine_dc_db": eng["pm_ss_deg"]["dc_db"], "engine_ugf_hz": eng["pm_ss_deg"]["ugf_hz"],
                    "ngspice_pm_deg": ac.get("pm_deg"), "ngspice_pm_undefined": ac.get("pm_undefined"),
                    "ngspice_pm_deg_raw": ac.get("pm_deg_raw"), "ngspice_ugf_hz": ac.get("loop_ugf_hz"),
                    "ngspice_dc_db": ac.get("loop_gain_dc_db"), "curve": compare_curves(eng["pm_ss_deg"], f, T)}
    for key, name in (("cm", "pm_cm_ss_deg"), ("dm", "pm_ss_deg")):
        f_lin, T_lin = linear_reference(topo, inp, ng, a.ngspice, a.out_dir, key)
        report[key]["curve_vs_ngspice_linear"] = compare_curves(eng[name], f_lin, T_lin)
    report["cm_view"] = repr(eng["views"]["cm_loop"])
    with open(a.out_json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
