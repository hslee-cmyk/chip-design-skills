"""C16 소자별 허용오차: 한 소자라도 predictions.devices[].tol 이 있으면 소자별 모드 -- 그 소자의 tol 만 쓰고, 없는 소자는
N/A(tol 미설정)(judge.tolerances 의 ID_rel/gm_rel 스칼라로 채우지 않는다). tol 이 아무에도 없으면 스칼라 동작.
기대값: '엔진 예측'을 독립 ngspice 값(conftest.independent_cs)에서 정한 비율만큼 벗어나게 만든 손계산 오차.
"""
import copy

import pytest

from conftest import by_name, cs_input, independent_cs, make_lut, preds_from_independent
from test_oracle_compare import Case

SCALAR_STRICT = {"ID_rel": 1e-12, "gm_rel": 1e-12}   # 스칼라가 쓰이면 무조건 FAIL 이 나는 값


@pytest.fixture(scope="module")
def ind(ref_root):
    return independent_cs(ref_root)


def _inp(lut, ind, tols, id_scale=None):
    pr = preds_from_independent(ind)
    devs = copy.deepcopy(pr["devices"])
    for n, s in (id_scale or {}).items():
        devs[n]["ID"] = ind[n]["id"] * s
    for n, t in tols.items():
        devs[n]["tol"] = t
    return cs_input(lut, diffusion="zero", preds_nodes=pr["nodes"], preds_devices=devs)


@pytest.fixture(scope="module")
def free_case(tmp_path_factory, ind):
    d = tmp_path_factory.mktemp("c16_free")
    return Case(d, _inp(make_lut(d / "lut.npz"), ind, {}), "free")


@pytest.fixture(scope="module")
def forced_case(tmp_path_factory, ind):
    d = tmp_path_factory.mktemp("c16_forced")
    return Case(d, _inp(make_lut(d / "lut.npz"), ind, {}), "forced")


@pytest.mark.parametrize("scale,expect", [(1 / 1.005, "PASS"), (1 / 1.02, "FAIL")])
def test_device_mode_uses_device_tol_not_scalar(free_case, ind, scale, expect):
    """M1 tol ID 1 %, gm 2 %; ID 예측 오차 +0.5 % -> PASS, +2 % -> FAIL. 스칼라(1e-12)는 쓰이지 않는다."""
    inp = _inp(free_case.inp["process"]["lut_npz"], ind, {"M1": {"ID_rel": 0.01, "gm_rel": 0.02}},
               id_scale={"M1": scale})
    _, c = free_case.cmp(inp, judge={"tolerances": SCALAR_STRICT})
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["tol_source"] == "device" and m1["tol_ID_rel"] == 0.01 and m1["tol_gm_rel"] == 0.02
    assert m1["judge"]["ID"] == expect
    assert m1["judge"]["gm"] == "PASS"   # gm 예측 = 독립 값(오차 ~0) <= 2 %, 스칼라였다면 FAIL 가능


def test_device_mode_missing_device_is_na_no_scalar_fallback(free_case, ind):
    inp = _inp(free_case.inp["process"]["lut_npz"], ind, {"M1": {"ID_rel": 0.01, "gm_rel": 0.02}},
               id_scale={"MP1": 1.5})                    # MP1 오차 -33 %: 스칼라가 쓰이면 FAIL
    _, c = free_case.cmp(inp, judge={"tolerances": {"ID_rel": 0.05, "gm_rel": 0.05}})
    mp = by_name(c["devices"], "name", "MP1")
    assert mp["tol_source"] == "device(없음)"
    assert mp["tol_ID_rel"] is None and mp["tol_gm_rel"] is None
    assert mp["judge"]["ID"] == "N/A(tol 미설정)" and mp["judge"]["gm"] == "N/A(tol 미설정)"


def test_device_tol_only_ID_leaves_gm_na(free_case, ind):
    inp = _inp(free_case.inp["process"]["lut_npz"], ind, {"M1": {"ID_rel": 0.01}})
    _, c = free_case.cmp(inp, judge={"tolerances": SCALAR_STRICT})
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["judge"]["ID"] == "PASS" and m1["judge"]["gm"] == "N/A(tol 미설정)"


def test_scalar_mode_when_no_device_tol(free_case, ind):
    inp = _inp(free_case.inp["process"]["lut_npz"], ind, {}, id_scale={"MP1": 1.5})
    _, c = free_case.cmp(inp, judge={"tolerances": {"ID_rel": 0.05, "gm_rel": 0.05}})
    for n, exp in (("M1", "PASS"), ("MP1", "FAIL")):
        d = by_name(c["devices"], "name", n)
        assert d["tol_source"] == "scalar" and d["tol_ID_rel"] == 0.05
        assert d["judge"]["ID"] == exp


def test_no_tol_anywhere_is_none(free_case):
    _, c = free_case.cmp()
    for d in c["devices"]:
        assert d["tol_source"] == "none" and d["judge"]["ID"] == "N/A(tol 미설정)"


def test_forced_warnings_use_device_tol(forced_case, ind):
    """M1(tol 1 %) ID 오차 +5 % -> 경고. MP1(tol 없음) 오차 -33 % -> 스칼라(5 %) 가 있어도 경고 없음."""
    inp = _inp(forced_case.inp["process"]["lut_npz"], ind, {"M1": {"ID_rel": 0.01, "gm_rel": 0.02}},
               id_scale={"M1": 1 / 1.05, "MP1": 1.5})
    inp["predictions"]["nodes"] = forced_case.inp["predictions"]["nodes"]
    _, c = forced_case.cmp(inp, judge={"tolerances": {"ID_rel": 0.05, "gm_rel": 0.05}})
    w = " ".join(map(str, c["summary"]["warnings"]))
    assert "M1" in w.replace("MP1", ""), w
    assert "MP1" not in w, w
