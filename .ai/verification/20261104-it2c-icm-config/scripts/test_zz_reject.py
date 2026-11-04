"""IT-2c 판정 탐침 -- 새 거부 경로 직접 1회(복제본 전용). 결과는 PROBE_OUT 에 append. 거부가 아니면 그 줄의 ok = False."""
import json
import math
import os
import sys
import types

import numpy
import pytest

from gmid_engine.metrics.aux_types import NodalSystem
from gmid_engine.metrics.icm_config import _end_state, _select, _sensitivity, kvl_sensitivity
from gmid_engine.metrics._helpers_nodal import conductance_matrix, nodal_factor
from gmid_engine.metrics.mna_types import Undefined
from gmid_engine.metrics.records import Resistor, SmallSignalCircuit, StampSet
from gmid_engine.sizing import Circuit, saturation_window

OUT = os.environ["PROBE_OUT"]


def rec(case, ok, **kw):
    with open(OUT, "ab") as f:
        f.write((json.dumps({"case": case, "ok": bool(ok), **kw}, ensure_ascii=False, default=str) + "\n").encode("utf-8"))


def _raises(case, exc, fn):
    try:
        fn()
    except exc as e:
        rec(case, True, exc=type(e).__name__, msg=str(e)[:120])
        return
    except Exception as e:  # 다른 예외 = 계약 위반으로 기록
        rec(case, False, exc=type(e).__name__, msg=str(e)[:120])
        return
    rec(case, False, exc=None)


def _nodal(res, n, fixed, names=None):
    ck = SmallSignalCircuit(resistors=tuple(Resistor(a, b, r) for a, b, r in res))
    g, gb = conductance_matrix(ck, n, bound=True)
    return NodalSystem(tuple(names or ("n%d" % i for i in range(n))), frozenset(fixed), g, gb, nodal_factor(g, frozenset(fixed)))


def test_reject_paths():
    # saturation_window
    rows = (("a", "b", 1, -0.1, "sat"),)
    rec("sw_skip_negative_slack_none", saturation_window(None, None, None, None, rows, slope={"a": 0.0, "b": 0.0}) is None)
    rec("sw_skip_zero_slack_not_none", saturation_window(None, None, None, None, (("a", "b", 1, 0.0, "sat"),), slope={"a": 0.0, "b": 0.0}) is not None)
    rec("sw_skip_positive_slack_inf", saturation_window(None, None, None, None, (("a", "b", 1, 0.1, "sat"),), slope={"a": 0.0, "b": 0.0})[:2] == (-math.inf, math.inf))
    got = saturation_window(None, None, None, None, (("a", "b", 1, -0.1, "sat"),), slope={"a": 1.0, "b": 0.0})
    rec("sw_nonskip_negative_slack_window_excludes_zero", got[0] > 0, lo=got[0], hi=got[1])
    got2 = saturation_window(None, None, None, None, (("a", "b", 1, -0.1, "sat"), ("a", "b", -1, 0.05, "sat")), slope={"a": 1.0, "b": 0.0})
    rec("sw_empty_dlo_gt_dhi", got2 is not None and got2[0] > got2[1], lo=got2 and got2[0], hi=got2 and got2[1])
    _raises("sw_root_pair_typeerror", TypeError, lambda: saturation_window(("x",), ("x", "y"), {}, None, ()))
    _raises("sw_root_not_unknown_valueerror", ValueError, lambda: saturation_window(("x",), "z", {}, None, ()))
    # _end_state
    fake = types.SimpleNamespace(lo=0.0, hi=1.8)
    rec("end_state_empty_none", _end_state(fake, (("a", "b", 1, -0.1, "sat"), ("a", "b", -1, 0.05, "sat")), {"a": 1.0, "b": 0.0, "p": 1.0}, ("p",), {"p": 0.9}) is None)
    rec("end_state_skip_negative_none", _end_state(fake, (("a", "b", 1, -0.1, "sat"),), {"a": 0.0, "b": 0.0, "p": 1.0}, ("p",), {"p": 0.9}) is None)
    # kvl_sensitivity
    good = _nodal(((1, 2, 1e3), (2, 0, 1e3)), 3, {0, 1})
    _raises("kvl_drive_not_fixed_valueerror", ValueError, lambda: kvl_sensitivity(good, ("n2",)))
    _raises("kvl_closure_typeerror", TypeError, lambda: kvl_sensitivity(good, ("n1",), closure=None))
    # 특이: 미지수 둘이 서로만 이어져 고정 넷과 끊긴 저항 섬(떠 있는 행 아님)
    sing = _nodal(((2, 3, 1e3), (1, 0, 1e3)), 4, {0, 1})
    rec("kvl_singular_none", kvl_sensitivity(sing, ("n1",)) is None, floating=list(sing.factor[4]))
    # _sensitivity 갈래
    r = _sensitivity(good, "servo", ("n1",), (("n1", 1.0),), ((("n2"), 1.0),), 0.0)
    rec("servo_rail_span_zero", isinstance(r, Undefined) and r.code == "icm_servo_pivot_unresolved" and r.detail == (("rail_span", 0.0),), got=r)
    r = _sensitivity(good, "servo", ("n1",), (("n1", 1.0),), ((("n2"), 1.0),), None)
    rec("servo_rail_span_none", isinstance(r, Undefined) and r.code == "icm_servo_pivot_unresolved", got=r)
    r = _sensitivity(sing, "servo", ("n1",), (("n1", 1.0),), ((("n2"), 1.0),), 1.8)
    rec("servo_singular", isinstance(r, Undefined) and r.detail == (("singular", True),), got=r)
    r = _sensitivity(sing, "as_is_single_input", ("n1",), (("n1", 1.0),), ((("n2"), 1.0),), 1.8)
    rec("as_is_singular_slope_none", not isinstance(r, Undefined) and r[0] is None, got=r)
    # a_e = 0 정확(감지 넷이 구동과 끊김): 고정 넷 감지
    zero = _nodal(((1, 0, 1e3), (2, 0, 1e3)), 3, {0, 1})
    rec("kvl_ae_exact_zero_none", kvl_sensitivity(zero, ("n1",), ((("n1", 1.0),), (("n2", 1.0),), 1.8)) is None)
    # 값 칸 불변·길이
    _raises("stampset_len_valueerror", ValueError, lambda: StampSet(g=((0, 0, 1.0),), g_ops=()))

    def write():
        good.g[0, 0] = 1.0
    _raises("nodal_system_write_valueerror", ValueError, write)

    def write2():
        good.g_bound[0, 0] = 1.0
    _raises("nodal_system_bound_write_valueerror", ValueError, write2)
    _raises("circuit_keyword_typeerror", TypeError, lambda: Circuit(None))
    # _select 갈래 (투영 가짜 -- 열만)

    class P:
        def __init__(self, views, roles):
            self.v, self.r = views, roles

        def column(self, kind, field):
            if field == "views":
                return (("s1v", self.v),)
            if field == "port_role":
                return tuple(self.r.items())
            raise KeyError(field)
    vw = types.SimpleNamespace(kind="transfer", default_port=True, excite=(("n1", 1.0),), sense=("a", "b"))
    und = Undefined("ss_nodal", "passive_value_undeclared", "definitional", (("elements", ("R1",)),))
    r = _select(P((vw,), {}), und, ("n1",), {})
    rec("select_1_undefined_propagates", r.quantity == "icm_config" and r.code == und.code and r.detail == und.detail, got=r)
    r = _select(P((vw,), {}), good, ("a", "b", "c"), {})
    rec("select_2_three_inputs", r.code == "icm_inputs_unsupported" and r.detail == (("inputs", ("a", "b", "c")),), got=r)
    r = _select(P((), {}), good, (), {})
    rec("select_3_zero_inputs", r.code == "view_required" and r.detail == (("default_views", 0),), got=r)
    r = _select(P((vw, vw), {}), good, ("a",), {})
    rec("select_4_two_views", r.code == "view_required" and r.detail == (("default_views", 2),), got=r)
    r = _select(P((vw,), {"a": "single_ended_output", "b": "single_ended_output"}), good, ("n1",), {})
    rec("select_4p_sense", r.code == "view_required" and r.detail == (("sense", ("a", "b")),), got=r)
    vw1 = types.SimpleNamespace(kind="transfer", default_port=True, excite=(("n1", 1.0),), sense=("n2",))
    fl = _nodal(((1, 0, 1e3),), 3, {0, 1})
    r = _select(P((vw1,), {}), fl, ("n1",), {})
    rec("select_5_capacitive_only", r.code == "icm_capacitive_only_node" and r.detail == (("nets", ("n2",)),), got=r)
    r = _select(P((vw1,), {}), good, ("n1",), {})
    rec("select_6_as_is", r[0] == "as_is_single_input", got=r)
    r = _select(P((vw1,), {}), good, ("n1", "n0"), {})
    rec("select_7_servo", r[0] == "servo", got=r)
