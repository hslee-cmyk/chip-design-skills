"""판정 탐침(복제본 전용): 창 끝 y = 0·1 의 봉인 여부, 봉인 7 slack_v, tol_v, 독립 여유. 기간 차이(창 여유 0, 봉인 +tol) 실측."""
import json
import os
from types import SimpleNamespace

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import size_and_seal

from .test_input_window import _evaluate_point, _oracle_slacks, _theta, _tol_of_window, pend  # noqa: F401

OUT = os.environ["PROBE_OUT"]


@pytest.mark.parametrize("y", [0.0, 1e-6, 1e-4, 1e-3, 1e-2, 0.5, 0.99, 0.999, 0.9999, 0.999999, 1.0])
def test_we(pend, y):  # noqa: F811
    snap, sealed, slack_v = _evaluate_point(pend, _theta(pend, 0.9, 0.3, y), True)
    sa, sb = _oracle_slacks(SimpleNamespace(snapshot=snap))
    row = {"y": y, "sealed": sealed, "slack_v": slack_v, "oracle": (sa, sb), "tol_v": dict(snap.column("node", "dc_window"))["in"].tol_v,
           "vin": dict(snap.column("node", "dc_v"))["in"]}
    with open(OUT, "ab") as f:
        f.write((json.dumps(row) + "\n").encode("utf-8"))
