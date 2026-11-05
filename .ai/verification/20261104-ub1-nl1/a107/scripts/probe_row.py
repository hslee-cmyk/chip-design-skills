"""A-107 재판정: 행 모드 둘째 정의. M-1 회로를 행 모드로. n 이 블록 노드 밖이면 charge_node_row_mode, 안이면? 값 누출 여부를 bound 까지 본다. m2 재측정."""
import json
import pathlib
import sys

import numpy as np

skill = sys.argv[1]
sys.path.insert(0, skill)
out = pathlib.Path(sys.argv[2])
out.write_text("", encoding="utf-8")
from gmid_engine.metrics import block_gain_bound, block_gain_model_of, row_gains, sensitivity_gate
from gmid_engine.tests.metrics import test_block_gain_model as T
from gmid_engine.tests.metrics.gb4_hand import block_spec


def rec(name, **kw):
    kw["case"] = name
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False, default=repr) + "\n")
    print(name, kw)


class Tables:
    def __init__(self, n):
        self.vds_of_vgs = np.zeros(n, dtype=int)

    def lookup(self, kind, i_l, i_d, i_s, i_v):
        s = np.shape(i_v)
        return np.full(s, 10.0), np.full(s, 0.1), np.zeros(s)

    def lookup_at_l(self, kind, l_m, i_d, i_s, i_v):
        s = np.shape(i_v)
        return np.full(s, 10.0), np.full(s, 0.1), np.zeros(s)

    def same_l_bin(self, kind, a, b):
        return False


devs = (("M1", "nmos", "out", "in", "gnd"), ("M2", "nmos", "o2", "n", "gnd"))
pas = (("R1", "resistor", "vdd", "out", 3e4), ("R2", "resistor", "vdd", "o2", 2e4), ("Rz", "resistor", "out", "mz", 1e3),
       ("Cc", "capacitor", "mz", "n", 1e-12), ("C2", "capacitor", "n", "gnd", 3e-12))
loc = T._ub1_loc(devs, pas)
for label, nodes in (("n_outside_nodes", ("in", "out", "o2")), ("n_mz_inside_nodes", ("in", "out", "mz", "n", "o2"))):
    spec = block_spec(("o2",), ("M1", "M2"), ("in",), ("o2",), nodes, passives=("R1", "R2", "Rz", "Cc", "C2"))
    m, why = block_gain_model_of(loc, spec)
    item = dict(model=m is not None, why=why)
    if m is not None:
        item["nodes"] = m.nodes
        idx = np.zeros((1, len(m.axes)), dtype=int)
        tables = Tables(64)
        gains = row_gains(m, tables, idx)
        item["row_gain"] = gains.tolist()
        try:
            bound = block_gain_bound(m, tables, 10 ** 7, ("M1", "M2"))
            item.update(status=bound.status, reason=bound.reason, a_max=bound.a_max_db)
        except Exception as exc:
            item["bound_exc"] = repr(exc)[:200]
    rec("row_" + label, **item)

for name, base, runs in (("nan_dec", (40.0, 40.0, 1e-12), (("a", float("nan"), 41.0, 1e-12),)), ("inf_full", (40.0, 40.0, 1e-12), (("a", 40.0, float("inf"), 1e-12),)),
                         ("nan_res", (40.0, 40.0, 1e-12), (("a", 40.0, 41.0, float("nan")),)), ("nan_base", (float("nan"), 40.0, 1e-12), (("a", 40.0, 41.0, 1e-12),)),
                         ("minf_both", (float("-inf"), 40.0, 1e-12), (("a", float("-inf"), 41.0, 1e-12),)), ("inf_res_base", (40.0, 40.0, float("inf")), (("a", 40.0, 41.0, 1e-12),)),
                         ("nan_with_error", (40.0, 40.0, 1e-12), (("a", float("nan"), 41.0, 1e-12), ("b", 40.0, 41.0, 1e-12))), ("clean", (40.0, 40.0, 1e-12), (("a", 40.0, 40.0, 1e-12),))):
    g = sensitivity_gate(base, runs)
    rec("gate_" + name, ok=g.ok, verdict=g.verdict, reason=g.reason, unmeasured=g.unmeasured, errors=g.errors)
