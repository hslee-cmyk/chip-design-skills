# -*- coding: utf-8 -*-
"""연속시간 CMFB 변형 -- 출력 포트 CM 주입 T_cm: 구조 분류(authoring `cm_loop_view`) + 엔진(ledger `cm_output`) 대 ngspice 선형 (metrics CONTRACT 7.11).

합성 회로(코어: 차동쌍 + PMOS 부하 + 꼬리, CM 제어 = 부하 gate vc)를 topology JSON 으로 쓰고 `load_topology` 로 읽어 `cm_loop_view` 가 구동자/소비자를 가르게 한다.
소신호 값은 소자 이름별로 정한 임의 값(회로 의미 있는 크기). 같은 값을 엔진 MNA 와 ngspice 선형 넷리스트(같은 절단·같은 Middlebrook `loop_gain`)에 넣어 대조한다.
변형: 1 저항 평균 -> 오차 증폭 / 2 소스 팔로어 버퍼 -> 저항 평균 / 3 DDA / 4 triode MOS 평균 / 5 감지 넷 기준 R·C / 6 triode 평균 + 감지 노드에 기준 전류원
(모호 정지, 선언하면 값) / 7 출력 캐스코드 + 이상 전류원(소스 단자 = 레일) / 8 소스 축퇴 출력 단.
사용: WORK=<임시 폴더> python cm_loop_variants.py -- 표를 WORK/variants.json 에 쓴다.
"""
import json
import math
import os
import subprocess
import sys

import numpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gmid_engine.authoring import load_topology  # noqa: E402
from gmid_engine.authoring.spec_views import cm_loop_view  # noqa: E402
from gmid_engine.metrics import ss_metrics as sm  # noqa: E402
from gmid_engine.metrics._helpers_product import product_at  # noqa: E402
from gmid_engine.metrics.records import Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit  # noqa: E402
from gmid_engine.metrics.ss_types import MetricRequest, SsCircuit  # noqa: E402
from core.measures_ac import ac_measures  # noqa: E402
from core.measures_ac import loop_gain as _loop_gain  # noqa: E402
from core.results import FreqSeries, Resolution  # noqa: E402


def loop_gain(v_file, i_file, weights):
    """wrdata 파일 호출 모양을 유지하는 얇은 어댑터(smoke 기록 스크립트용): 열을 FreqSeries 로 감싸 core.measures_ac.loop_gain 에 넘긴다.
    v 파일 열 = [v(lbx_k), v(k)] 쌍, i 파일 열 = [i(Vlb_k)...] 뒤에 [v(k)...]. 끊은 넷 이름은 k0, k1, ... 로 붙인다. 반환 (f, 실수부, 허수부) 또는 None."""
    import numpy as np

    def cols(path):
        rows = [[float(x) for x in ln.split()] for ln in open(path) if ln.strip()]
        a = np.array(rows)
        return a[:, 0], [a[:, 1 + 2 * k] + 1j * a[:, 2 + 2 * k] for k in range((a.shape[1] - 1) // 2)]
    n = len(weights)
    nets = [f"k{k}" for k in range(n)]
    res = Resolution(None, {}, None, "adapter_declared")
    (f, vc), (_, ic) = cols(v_file), cols(i_file)
    v = FreqSeries(f=f, values={**{f"v(lbx_{x})": vc[2 * k] for k, x in enumerate(nets)}, **{f"v({x})": vc[2 * k + 1] for k, x in enumerate(nets)}},
                   resolution=res, error=None)
    i = FreqSeries(f=f, values={**{f"i(tb:lb:{x})": ic[k] for k, x in enumerate(nets)}, **{f"v({x})": ic[n + k] for k, x in enumerate(nets)}},
                   resolution=res, error=None)
    return _loop_gain(v, i, list(weights), nets)

EXE = os.environ.get("NGSPICE", "C:/ngspice/Spice64/bin/ngspice_con.exe")
WORK = os.environ.get("WORK", os.environ.get("TEMP", "."))
RAILS = ("gnd", "vdd")
SS_DEFAULT = dict(gds=1e-5, cgs=5e-14, cgd=1e-14, cgb=0.0, cdb=1e-14, csb=1e-14, gmb=0.0)


class Circuit:
    def __init__(self):
        self.mos, self.passives, self.sources, self.bias = [], [], [], []

    def m(self, name, kind, d, g, s, gm, **kw):
        self.mos.append(dict(name=name, kind=kind, d=d, g=g, s=s, gm=gm, **{**SS_DEFAULT, **kw}))

    def r(self, name, a, b, v):
        self.passives.append((name, "resistor", a, b, v))

    def c(self, name, a, b, v):
        self.passives.append((name, "capacitor", a, b, v))

    def i(self, name, a, b):
        self.sources.append((name, a, b))

    def merge(self, other):
        self.mos += other.mos
        self.passives += other.passives
        self.sources += other.sources
        self.bias += other.bias
        return self

    def topology_dict(self, name):
        return {
            "schema_version": "2.0", "topology_name": name,
            "netlist": [{"name": x["name"], "kind": x["kind"], "drain": x["d"], "gate": x["g"], "source": x["s"],
                         "bulk": "vdd" if x["kind"] == "pmos" else "gnd"} for x in self.mos],
            "supply_nets": list(RAILS),
            "ports": {"in1": {"direction": "input", "role": "differential_input_p"},
                      "in2": {"direction": "input", "role": "differential_input_n"},
                      "op": {"direction": "output", "role": "differential_output_p"},
                      "om": {"direction": "output", "role": "differential_output_n"}},
            "passive_elements": [{"name": n, "kind": k, "terminals": [a, b]} for n, k, a, b, _v in self.passives],
            "ideal_sources": [{"name": n, "kind": "current_source", "terminals": [a, b]} for n, a, b in self.sources],
            "bias_inputs": sorted(set(self.bias)),
        }


def core(degeneration=False, cascode=False):
    c = Circuit()
    c.m("Mn1", "nmos", "op", "in1", "tail", 1e-3)
    c.m("Mn2", "nmos", "om", "in2", "tail", 1e-3)
    c.m("M0", "nmos", "tail", "vb", "gnd", 1e-3, gds=2e-5)
    c.bias.append("vb")
    c.c("CL1", "op", "gnd", 1e-12)
    c.c("CL2", "om", "gnd", 1e-12)
    for k, out in (("1", "op"), ("2", "om")):
        src = "vdd"
        if degeneration:
            src = "sd" + k
            c.r("Rdeg" + k, src, "vdd", 2e3)
        c.m("Mp" + k, "pmos", out, "vc", src, 2e-5)
    if cascode:        # 출력 캐스코드(소스 단자가 이상 전류원 단자인 마디 n1·n2)
        for k, out in (("1", "op"), ("2", "om")):
            c.m("Mc" + k, "nmos", out, "vcasc", "n" + k, 5e-4)
            c.i("Ib" + k, "n" + k, "gnd")
        c.bias.append("vcasc")
    return c


def chain(first_in):
    c = Circuit()
    c.m("Mea1", "nmos", "vc1", first_in, "gnd", 5e-4)
    c.m("Mdl1", "pmos", "vc1", "vc1", "vdd", 2e-4)
    c.m("Mea2", "nmos", "vc", "vc1", "gnd", 5e-4)
    c.m("Mdl2", "pmos", "vc", "vc", "vdd", 2e-4)
    c.c("Cvc", "vc", "gnd", 5e-14)
    c.c("Cvc1", "vc1", "gnd", 5e-14)
    return c


def v1():
    c = core()
    c.r("R1", "op", "vs", 1e5)
    c.r("R2", "vs", "om", 1e5)
    return c.merge(chain("vs"))


def v2():
    c = core()
    c.m("Msf1", "nmos", "vdd", "op", "bp", 1e-3)
    c.m("Msf2", "nmos", "vdd", "om", "bm", 1e-3)
    c.i("Isf1", "bp", "gnd")
    c.i("Isf2", "bm", "gnd")
    c.r("R1", "bp", "vs", 1e5)
    c.r("R2", "vs", "bm", 1e5)
    return c.merge(chain("vs"))


def v3():
    c = core()
    for n, d, g, s, gm, kw in (("Ma1", "n1", "op", "ta", 5e-4, {}), ("Ma2", "n2", "vref", "ta", 5e-4, {}),
                               ("Mb1", "n1", "om", "tb", 5e-4, {}), ("Mb2", "n2", "vref", "tb", 5e-4, {}),
                               ("Mta", "ta", "vb", "gnd", 1e-3, dict(gds=2e-5)), ("Mtb", "tb", "vb", "gnd", 1e-3, dict(gds=2e-5)),
                               ("Mea2", "vc", "n1", "gnd", 5e-4, {})):
        c.m(n, "nmos", d, g, s, gm, **kw)
    c.m("Ml1", "pmos", "n1", "n1", "vdd", 2e-4)
    c.m("Ml2", "pmos", "n2", "n2", "vdd", 2e-4)
    c.m("Mdl2", "pmos", "vc", "vc", "vdd", 2e-4)
    c.bias.append("vref")
    c.c("Cvc", "vc", "gnd", 5e-14)
    c.c("Cn1", "n1", "gnd", 5e-14)
    return c


def triode(c):
    c.m("Mt1", "nmos", "op", "vref", "vs", 2e-6, gds=1e-5)
    c.m("Mt2", "nmos", "om", "vref", "vs", 2e-6, gds=1e-5)
    c.bias.append("vref")


def v4():
    c = core()
    triode(c)
    return c.merge(chain("vs"))


def v5():
    c = core()
    c.r("R1", "op", "vs", 1e5)
    c.r("R2", "vs", "om", 1e5)
    c.r("Rref", "vs", "vbr", 1e6)
    c.c("Cref", "vbr", "gnd", 1e-12)
    c.c("Cs", "vs", "gnd", 1e-13)
    return c.merge(chain("vs"))


def v6():
    c = core()
    triode(c)
    c.i("Iref", "vs", "gnd")
    return c.merge(chain("vs"))


def v7():
    c = core(cascode=True)
    c.r("R1", "op", "vs", 1e5)
    c.r("R2", "vs", "om", 1e5)
    return c.merge(chain("vs"))


def v8():
    c = core(degeneration=True)
    c.r("R1", "op", "vs", 1e5)
    c.r("R2", "vs", "om", 1e5)
    return c.merge(chain("vs"))


VARIANTS = (("1 저항 평균 -> 오차증폭", v1, None), ("2 SF 버퍼 -> 저항 평균", v2, None), ("3 DDA", v3, None),
            ("4 triode MOS 평균", v4, None), ("5 감지 넷 기준 R·C", v5, None), ("6 triode 평균 + 기준 전류원", v6, None),
            ("6' 같은 회로 + 선언 [Mt1, Mt2]", v6, ("Mt1", "Mt2")), ("7 출력 캐스코드 + 이상 전류원", v7, None),
            ("8 소스 축퇴 출력 단", v8, None))


def small_signal(c):
    nets = sorted({n for x in c.mos for n in (x["d"], x["g"], x["s"])} | {n for p in c.passives for n in p[2:4]}
                  | {n for s in c.sources for n in s[1:]} | set(RAILS) | {"in1", "in2", "op", "om"})
    ix = {n: i for i, n in enumerate(nets)}
    bulk = {x["name"]: ("vdd" if x["kind"] == "pmos" else "gnd") for x in c.mos}
    mos = tuple(MosSmallSignal(ix[x["d"]], ix[x["g"]], ix[x["s"]], ix[bulk[x["name"]]], x["gm"], x["gmb"], x["gds"], x["cgs"], x["cgd"],
                               x["cgb"], x["cdb"], x["csb"], label=x["name"]) for x in c.mos)
    res = tuple(Resistor(ix[a], ix[b], v, label=n) for n, k, a, b, v in c.passives if k == "resistor")
    cap = tuple(Capacitor(ix[a], ix[b], v, label=n) for n, k, a, b, v in c.passives if k == "capacitor")
    ground = tuple(sorted(set(RAILS) | set(c.bias)))
    return SsCircuit(tuple(nets), SmallSignalCircuit(mos, res, cap), tuple(n for n, k, *_ in c.passives if k == "resistor"),
                     tuple(n for n, k, *_ in c.passives if k == "capacitor"), ground, ("in1", "in2"))


def engine_side(c, view):
    ledger = sm._Ledger(small_signal(c), RAILS, {n for s in c.sources for n in s[1:]})
    plan = sm._plan(MetricRequest("", view), ledger)
    responses, cutmap = ledger.solve()
    analysis, source = sm._analysis(plan, responses, cutmap)
    reports, _warns = sm._cm_report(analysis, view, False)
    return dict(reports[0][1]), source[0]


def linear_ng(c, view, tag):
    outs = [net for net, _w in view.weights]
    w = 1 / len(outs)
    moved = dict(view.cuts)

    def nn(n):
        return "0" if n == "gnd" else n
    lines = ["* variant " + tag]
    for x in c.mos:
        d, g, s, b = nn(x["d"]), nn(x["g"]), nn(x["s"]), nn("vdd" if x["kind"] == "pmos" else "gnd")
        if x["name"] in moved:
            if x["d"] == moved[x["name"]]:
                d = "lbx_" + d
            else:
                s = "lbx_" + s
        lines += [f"Gm_{x['name']} {d} {s} {g} {s} {x['gm']}", f"Gb_{x['name']} {d} {s} {b} {s} {x['gmb'] or 1e-30}",
                  f"Gd_{x['name']} {d} {s} {d} {s} {x['gds']}"]
        for nm, p, q, val in (("gs", g, s, x["cgs"]), ("gd", g, d, x["cgd"]), ("gb", g, b, x["cgb"]), ("db", d, b, x["cdb"]),
                              ("sb", s, b, x["csb"])):
            if val:
                lines.append(f"C{nm}_{x['name']} {p} {q} {val}")
    for n, k, a, b, v in c.passives:
        lines.append(f"{'R' if k == 'resistor' else 'C'}{n} {nn(a)} {nn(b)} {v}")
    lines += ["Vvdd vdd 0 0"] + [f"Vbias_{n} {n} 0 0" for n in sorted(set(c.bias))] + ["Vin_in1 in1 0 0", "Vin_in2 in2 0 0"]
    for n in outs:
        lines += [f"Vlb_{n} {n} lbx_{n} DC 0 AC {w}", f"Ilb_{n} 0 {n} DC 0 AC 0"]
    pre = os.path.join(WORK, "var_" + tag)
    ac = "ac dec 40 1 1e11"
    lines += [".control", "set noaskquit", "set wr_singlescale", ac,
              f"wrdata {pre}.v.txt " + " ".join(f"v(lbx_{n}) v({n})" for n in outs)]
    lines += [x for n in outs for x in (f"alter @vlb_{n.lower()}[acmag] = 0", f"alter @ilb_{n.lower()}[acmag] = {w}")]
    lines += [ac, f"wrdata {pre}.i.txt " + " ".join(f"i(vlb_{n.lower()})" for n in outs) + "".join(f" v({n})" for n in outs),
              "quit", ".endc", ".end"]
    with open(pre + ".cir", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    subprocess.run([EXE, "-b", pre + ".cir"], capture_output=True)
    f, re_, im = loop_gain(pre + ".v.txt", pre + ".i.txt", [w] * len(outs))
    return numpy.array(f), numpy.array(re_) + 1j * numpy.array(im)


def main():
    rows = []
    for name, build, declared in VARIANTS:
        c = build()
        tag = name.split()[0].replace("'", "p")
        path = os.path.join(WORK, "var_topo_" + tag + ".topology.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(c.topology_dict("var" + tag), fh)
        view, problems = cm_loop_view(load_topology(path), declared)
        row = dict(variant=name, problems=[p[0] for p in problems], drivers=None if view is None else [n for n, _ in view.cuts])
        if view is not None:
            rep, factor = engine_side(c, view)
            f, t_ng = linear_ng(c, view, tag)
            t_eng = numpy.array([product_at((factor,), 2 * math.pi * float(x))[0] for x in f])
            sel = numpy.abs(t_ng) > 1e-3
            m = ac_measures(f, t_ng.real, t_ng.imag)
            row.update(dc_db=rep["dc_db"], ugf_hz=rep["ugf_hz"], pm_deg=rep["pm_deg"], undefined=list(rep["undefined"]),
                       ng_dc_db=m["dc_gain_db"], ng_ugf_hz=m["ugf_hz"], ng_pm_deg=m["pm_deg"],
                       max_db=float(numpy.max(numpy.abs(20 * numpy.log10(numpy.abs(t_eng[sel]) / numpy.abs(t_ng[sel]))))) if sel.any() else None,
                       max_deg=float(numpy.max(numpy.abs(numpy.degrees(numpy.angle(t_eng[sel] / t_ng[sel]))))) if sel.any() else None)
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))
    with open(os.path.join(WORK, "variants.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
