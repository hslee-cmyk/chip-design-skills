"""IT-2d·2e 판정 탐침(복제본 전용): 새 거부 경로 직접 1회. ok = 계약대로 거부."""
import json
import os
import types

import pytest

from gmid_engine.metrics.aux_types import IcmConfig, IcmPort
from gmid_engine.metrics.icm_window import icm_window_metrics
from gmid_engine.metrics.metrics_aux import _unavailable
from gmid_engine.metrics.mna_types import Undefined
from gmid_engine.sizing.seal_versions import writers_in_scope

OUT = os.environ["PROBE_OUT"]


def rec(case, ok, **kw):
    with open(OUT, "ab") as f:
        f.write((json.dumps({"case": case, "ok": bool(ok), **kw}, ensure_ascii=False, default=str) + "\n").encode("utf-8"))


def raises(case, exc, fn):
    try:
        fn()
    except exc as e:
        rec(case, True, exc=type(e).__name__)
        return
    except Exception as e:
        rec(case, False, exc=type(e).__name__)
        return
    rec(case, False, exc=None)


def test_paths():
    ss0 = types.SimpleNamespace(missing=())
    ss1 = types.SimpleNamespace(missing=("C1",))
    und = Undefined("ss_nodal", "passive_value_undeclared", "definitional", ())
    raises("unavailable_unknown_domain_ls", ValueError, lambda: _unavailable("ls", ss0, object()))
    raises("unavailable_unknown_domain_geom", ValueError, lambda: _unavailable("geom", ss1, und))
    rec("unavailable_dc_resistor_missing", _unavailable("dc", ss1, und) is True)
    rec("unavailable_dc_cap_only", _unavailable("dc", ss1, object()) is False)
    rec("unavailable_ss_cap_only", _unavailable("ss", ss1, object()) is True)
    rec("unavailable_ss_none", _unavailable("ss", ss0, object()) is False)
    good = IcmConfig("servo", 1.0, 0.0, 0.9, 0.3, 1.2)
    port = IcmPort("a", 0.9, 0.3, 1.2, 0.01)
    raises("icm_input_dc_vocab", ValueError, lambda: icm_window_metrics(good, (port,), "engine"))
    raises("icm_config_none_empty_undefined", ValueError, lambda: icm_window_metrics(IcmConfig(None, None, None, None, None, None), (), "pending"))
    raises("icm_no_ports", ValueError, lambda: icm_window_metrics(good, (), "pending"))
    raises("icm_vcm_none_with_measured_ports", ValueError, lambda: icm_window_metrics(IcmConfig("servo", 1.0, 0.0, 0.9, None, None), (port,), "pending"))
    got = icm_window_metrics(good, (IcmPort("a", 0.9, None, None, None, ("window",)),), "pending")
    rec("icm_unmeasured_numeric", got.icmr_v is None and {(u.quantity, u.code, u.category) for u in got.undefined} == {(q, "input_window_unmeasured", "numeric") for q in ("icmr_v", "icm_margin_v", "required_input_cm_v")})
    neg = icm_window_metrics(IcmConfig("servo", 1.0, 0.0, 0.2, 0.3, 1.2), (port,), "declared")
    rec("icm_seal_outside_window_negative_margin", abs(neg.icm_margin_v + 0.1) < 1e-12 and neg.icmr_v > 0 and neg.required_input_cm_v is None, margin=neg.icm_margin_v)
    raises("writers_in_scope_none", TypeError, lambda: writers_in_scope(None, ()))
