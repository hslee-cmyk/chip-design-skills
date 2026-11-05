"""view_factor 다른 고정 집합 + 씨앗 없음: C 조립 0 확인(입력 넷을 고정에 둔 채 x 를 더 고정). 결과 append."""
import importlib
import json
import pathlib
import sys

skill = sys.argv[1]
sys.path.insert(0, skill)
from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit, SsCircuit
from gmid_engine.metrics._helpers_nodal import capacitance_matrix as real_c

m = lambda n: importlib.import_module("gmid_engine.metrics." + n)
SN, HV = m("ss_nodal"), m("_helpers_view")
sites = {}


def counted(c, s):
    k = sys._getframe(1).f_code.co_name
    sites[k] = sites.get(k, 0) + 1
    return real_c(c, s)


SN.capacitance_matrix = counted
HV.capacitance_matrix = counted
nets = ("gnd", "vdd", "in", "x", "out")
i = {n: k for k, n in enumerate(nets)}
mos = (MosSmallSignal(i["out"], i["x"], i["gnd"], i["gnd"], 1e-3, 0.0, 2e-5, cgs=1e-13, cgd=1e-13, label="M1"), MosSmallSignal(i["x"], i["in"], i["gnd"], i["gnd"], 1e-3, 0.0, 2e-5, cgs=1e-13, label="M0"))
res = (Resistor(i["vdd"], i["out"], 3e4, label="RL"), Resistor(i["vdd"], i["x"], 1e4, label="Rx"))
ss = SsCircuit(nets, SmallSignalCircuit(mos=mos, resistors=res, capacitors=(Capacitor(i["out"], i["gnd"], 1e-12, label="CL"),)), ("RL", "Rx"), ("CL",), ("gnd", "vdd"), ("in",))
nod = SN.nodal_of(ss)
f = HV.view_factor(ss, nod, {i["gnd"], i["vdd"], i["in"], i["x"]})
item = {"case": "1e_view_factor_other_fixed_no_seed", "sites": sites, "charge": f[5], "floating": f[4]}
print(item)
with pathlib.Path(sys.argv[2]).open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(item, ensure_ascii=False, default=repr) + "\n")
