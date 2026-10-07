"""C20 PM 교차 측정(기록만): C = L/(1+L) 의 peaking Mp = max|C|/|C(fstart)| -> 2차계 z -> PM.

해석식: 되먹임 회로 tfb_cs_rfeedback 의 β 루프 이득 T(conftest.fb_loop_gain, gm/gds 는 독립 .op)에서 같은 정의를
손으로 계산한다. Cin 3 값으로 z ~0.29(강한 peaking), ~0.55(약한 peaking), peaking 없음(z > 1/sqrt2) 세 경우.
  Mp = 1/(2 z sqrt(1-z^2)) -> z^2 = (1 - sqrt(1 - 1/Mp^2))/2,  PM = atan(2z / sqrt(sqrt(1+4z^4) - 2z^2)).
"""
import json
import math
import re

import numpy as np
import pytest

from conftest import ac_grid, fb_input, fb_loop_gain, independent_fb, make_lut, measure, run_netlist, run_simulate

GRID = ac_grid(0.01, 1e10, 40)


def pm_from_z(z):
    return math.degrees(math.atan(2 * z / math.sqrt(math.sqrt(1 + 4 * z ** 4) - 2 * z ** 2)))


def hand_crosscheck(T):
    c = np.abs(T / (1 + T))
    i = int(np.argmax(c))
    mp = c[i] / c[0]
    if i == 0 or mp <= 1:
        return {"mp": mp, "pm": None, "peak_hz": None}
    z = math.sqrt((1 - math.sqrt(1 - 1 / mp ** 2)) / 2)
    return {"mp": mp, "pm": pm_from_z(z), "peak_hz": GRID[i], "z": z}


def _sim(d, cin):
    inp = fb_input(make_lut(d / "lut.npz"), cin=cin)
    p, text, meta = run_netlist(inp, d)
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-800:]
    q = run_simulate(d / "t.free.cir", d / "t.free.sim.json", d)
    assert q.returncode == 0, (q.stdout + q.stderr)[-800:]
    return json.loads((d / "t.free.sim.json").read_text(encoding="utf-8"))["ac"]


CASES = {"z_low": 1e-12, "z_mid": 10e-12, "no_peak": 30e-12}


@pytest.fixture(scope="module")
def ref(ref_root):
    return independent_fb(ref_root)


@pytest.mark.parametrize("case", list(CASES))
def test_pm_crosscheck_matches_hand_2nd_order(tmp_path, ref, case):
    cin = CASES[case]
    T = fb_loop_gain(GRID, ref["gm"], ref["gds"], cin=cin)
    h = hand_crosscheck(T)
    pm_hand = measure(GRID, T)["pm_deg"]
    ac = _sim(tmp_path, cin)
    assert ac["pm_definition"] == "beta_loop"
    assert ac["pm_deg"] == pytest.approx(pm_hand, abs=1.0)
    if case == "no_peak":
        assert h["pm"] is None                                   # 조건 점검
        assert ac["pm_crosscheck_deg"] is None and ac["closed_loop_peaking_db"] is None
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(ac["pm_crosscheck_note"]))]
        assert any(abs(x - pm_from_z(1 / math.sqrt(2))) < 0.1 for x in nums), ac["pm_crosscheck_note"]
        return
    assert {"z_low": (0.2, 0.4), "z_mid": (0.45, 0.65)}[case][0] < h["z"] < {"z_low": (0.2, 0.4),
                                                                             "z_mid": (0.45, 0.65)}[case][1]
    assert ac["closed_loop_peaking_db"] == pytest.approx(20 * math.log10(h["mp"]), abs=0.1)
    assert ac["pm_crosscheck_deg"] == pytest.approx(h["pm"], abs=1.0)
    assert ac["closed_loop_peak_hz"] == pytest.approx(h["peak_hz"], rel=0.07)   # 한 격자점(5.9 %) 이내
    assert ac["pm_crosscheck_gap_deg"] == pytest.approx(ac["pm_crosscheck_deg"] - ac["pm_deg"], abs=1e-9)
