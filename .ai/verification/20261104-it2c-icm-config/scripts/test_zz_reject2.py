"""IT-2c 판정 탐침 2(복제본 전용): 뮤턴트 생존 자리 직접 확인 -- 피벗 분해능 갈래, 기본 뷰 거름, view_factor 다른 고정 집합, tol_v 최솟값, archive 배열, 대칭 toy 포트 끝 차."""
import gzip
import json
import os
import types

import numpy

from gmid_engine.metrics._helpers_nodal import conductance_matrix, nodal_factor, nodal_solve
from gmid_engine.metrics._helpers_view import view_factor
from gmid_engine.metrics.aux_types import NodalSystem
from gmid_engine.metrics.icm_config import _default_port_views, _sensitivity, _tol_v
from gmid_engine.metrics.mna_types import Undefined
from gmid_engine.metrics.records import Resistor, SmallSignalCircuit
from gmid_engine.search.archive import _plain

from .test_icm_config import _two_stage, _servo_window  # noqa: F401

OUT = os.environ["PROBE_OUT"]


def rec(case, ok, **kw):
    with open(OUT, "ab") as f:
        f.write((json.dumps({"case": case, "ok": bool(ok), **kw}, ensure_ascii=False, default=str) + "\n").encode("utf-8"))


def _sys():
    ck = SmallSignalCircuit(resistors=(Resistor(1, 3, 10.0), Resistor(1, 3, 5.0), Resistor(2, 3, 10.0 / 3.0), Resistor(3, 0, 1000.0)))
    g, gb = conductance_matrix(ck, 4, bound=True)
    return NodalSystem(("n0", "n1", "n2", "n3"), frozenset({0, 1, 2}), g, gb, nodal_factor(g, frozenset({0, 1, 2})))


def test_pivot_branch():
    s = _sys()
    r = _sensitivity(s, "servo", ("n1", "n2"), (("n1", 0.5), ("n2", -0.5)), (("n3", 1.0),), 1.8)
    rec("servo_pivot_below_resolution_rejected", isinstance(r, Undefined) and r.code == "icm_servo_pivot_unresolved" and r.detail[0][0] == "a_e", got=r)


def test_view_filter():
    declared = types.SimpleNamespace(kind="transfer", default_port=False, excite=(("a", 1.0),), sense=("o",))
    default = types.SimpleNamespace(kind="transfer", default_port=True, excite=(("a", 0.5), ("b", -0.5)), sense=("o",))
    loop = types.SimpleNamespace(kind="loop", default_port=False, excite=(("g", 1.0),), sense=("g",))

    class P:
        def column(self, kind, field):
            return (("s1v", (declared, default, loop)),)
    got = _default_port_views(P(), {})
    rec("default_view_filter_keeps_default_only", got == (default,), got=[v.excite for v in got])


def test_view_factor_other_fixed():
    s = _sys()
    ss = types.SimpleNamespace(nodes=s.nodes, circuit=None)
    other = view_factor(ss, s, {0, 1, 2, 3})
    want = nodal_factor(s.g, frozenset({0, 1, 2, 3}))
    rec("view_factor_other_fixed_is_new_factor", other is not s.factor and list(other[0]) == list(want[0]), unknown=list(other[0]))
    same = view_factor(ss, s, {0, 1, 2})
    rec("view_factor_same_fixed_reuses_field", same is s.factor)


def test_archive_array():
    s = _sys()
    out = _plain(s)
    json.dumps(out)
    rec("archive_nodal_system_plain", out["g"] == s.g.tolist() and out["g_bound"] == s.g_bound.tolist(), keys=sorted(out))


def test_symmetric_toy_port_ends(tmp_path):
    """옛 pb 대체 확인: 대칭 toy, 입력 DC 둘 선언(같은 값) -> 포트 끝 차 = 선언 차 0."""
    snap, _ = _two_stage(tmp_path, 1e-5, 9e4, 1e-5, 9e4)
    a = snap.value("node", "ip", "dc_window_cfg")
    b = snap.value("node", "im", "dc_window_cfg")
    rec("symmetric_port_ends_equal", a.input_status == "measured" and abs(a.lo - b.lo) <= 1e-12 and abs(a.hi - b.hi) <= 1e-12, a=(a.lo, a.hi), b=(b.lo, b.hi))
