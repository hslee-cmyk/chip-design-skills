"""작성자 임의 사항 직접 대조: view_factor(다른 고정 집합 + 전하 넷), ss_nodal_system(missing + 전하), icm _sensitivity(gate 전용 C 없음), 그 외. 손 유도와 대조."""
import importlib
import json
import pathlib
import sys
import types

import numpy as np

skill = sys.argv[1]
sys.path.insert(0, skill)
out = pathlib.Path(sys.argv[2])
out.write_text("", encoding="utf-8")
from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit, SsCircuit
from gmid_engine.metrics._helpers_nodal import nodal_solve
HV = importlib.import_module("gmid_engine.metrics._helpers_view")
SN = importlib.import_module("gmid_engine.metrics.ss_nodal")
IC = importlib.import_module("gmid_engine.metrics.icm_config")


def rec(name, **kw):
    kw["case"] = name
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False, default=repr) + "\n")
    print(name, kw)


def ss_of(nets, mos, res, caps, ground, inputs, missing=()):
    return SsCircuit(tuple(nets), SmallSignalCircuit(mos=tuple(mos), resistors=tuple(res), capacitors=tuple(caps)),
                     tuple(r.label for r in res), tuple(c.label for c in caps), tuple(sorted(ground)), tuple(sorted(inputs)), tuple(missing))


# a. view_factor: 고정 집합이 전회로와 다름(뷰 여기 넷 x 가 입력 밖), n 은 전하 넷
nets = ("gnd", "vdd", "x", "n", "out")
i = {n: k for k, n in enumerate(nets)}
c1, c2, cgs, cgd, gm, gds, rl = 2e-12, 3e-12, 5e-13, 2e-13, 1e-3, 2e-5, 3e4
mos = [MosSmallSignal(i["out"], i["n"], i["gnd"], i["gnd"], gm, 0.0, gds, cgs=cgs, cgd=cgd, label="M1"),
       MosSmallSignal(i["x"], i["vdd"], i["gnd"], i["gnd"], 1e-4, 0.0, 1e-5, label="Mx")]
ss = ss_of(nets, mos, [Resistor(i["vdd"], i["out"], rl, label="RL"), Resistor(i["vdd"], i["x"], 1e4, label="Rx")],
           [Capacitor(i["x"], i["n"], c1, label="C1"), Capacitor(i["n"], i["gnd"], c2, label="C2")], ("gnd", "vdd"), ())
nod = SN.nodal_of(ss)
fixed = {i["gnd"], i["vdd"], i["x"]}
f = HV.view_factor(ss, nod, fixed)
v, res = nodal_solve(f, len(nets), {i["x"]: 1.0})
rp = 1 / (gds + 1 / rl)
d = c1 + c2 + cgs + cgd * (1 + gm * rp)
rec("a_view_factor_other_fixed_charge", engine_out=None if v is None else float(v[i["out"]]), hand_out=-gm * rp * c1 / d, charge=[nets[k] for k in f[5]])

# b. ss_nodal_system: missing + 전하 넷 -> Undefined, missing + 전하 넷 없음 -> 값, missing 이 넷의 유일한 용량 -> lu None
proj = lambda s: types.SimpleNamespace(value=lambda *a: s, column=lambda *a: tuple((m, "capacitor") for m in s.missing))
fn = SN.ss_nodal_system
fn = getattr(fn, "__wrapped__", None) or getattr(fn, "fn", None) or getattr(fn, "func", None) or fn
ssm = ss_of(nets, mos, [Resistor(i["vdd"], i["out"], rl, label="RL"), Resistor(i["vdd"], i["x"], 1e4, label="Rx")],
            [Capacitor(i["n"], i["gnd"], c2, label="C2")], ("gnd", "vdd"), (), missing=("C1",))
try:
    v1 = list(fn(proj(ssm)).values())[0]
    v1 = list(v1.values())[0]
    rec("b1_missing_and_charge", value=repr(v1)[:220])
except Exception as exc:
    rec("b1_missing_and_charge", exc=repr(exc)[:300])
ssm2 = ss_of(nets, mos, [Resistor(i["vdd"], i["out"], rl, label="RL"), Resistor(i["vdd"], i["x"], 1e4, label="Rx")], [], ("gnd", "vdd"), (), missing=("C1", "C2"))
try:
    v2 = list(list(fn(proj(ssm2)).values())[0].values())[0]
    rec("b2_missing_all_caps_on_net", type=type(v2).__name__, lu_none=getattr(v2, "factor", (0, "x"))[1] is None if hasattr(v2, "factor") else None, repr=repr(v2)[:160] if not hasattr(v2, "factor") else "")
    if hasattr(v2, "factor"):
        rec("b2_solve", solve=str(nodal_solve(v2.factor, 5, {i["x"]: 1.0})))
except Exception as exc:
    rec("b2_missing_all_caps_on_net", exc=repr(exc)[:300])

# c. icm _sensitivity: gate 전용 C 없음(옛 floating -> capacitive_only, 새 lu None)
nets = ("gnd", "vdd", "in", "n", "out")
i = {n: k for k, n in enumerate(nets)}
mos = [MosSmallSignal(i["out"], i["n"], i["gnd"], i["gnd"], 1e-3, 0.0, 2e-5, label="M1"), MosSmallSignal(i["out"], i["in"], i["gnd"], i["gnd"], 1e-3, 0.0, 2e-5, label="M2")]
ss = ss_of(nets, mos, [Resistor(i["vdd"], i["out"], 1e4, label="R1")], [], ("gnd", "vdd"), ("in",))
nod = SN.nodal_of(ss)
rec("c0_classify", floating=nod.factor[4], charge=nod.factor[5], lu_none=nod.factor[1] is None)
for cfg, name in ((IC.CONFIG_SERVO, "servo"), (IC.CONFIGS[0], "as_is")):
    try:
        got = IC._sensitivity(nod, cfg, ("in",), (("in", 1.0),), ("out",) if False else (("out", 1),), 1.8)
        rec("c1_icm_" + name, got=repr(got)[:240])
    except Exception as exc:
        rec("c1_icm_" + name, exc=repr(exc)[:300])
