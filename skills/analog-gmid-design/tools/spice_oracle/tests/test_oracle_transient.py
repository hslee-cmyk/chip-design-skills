"""C25 슬루·정착(기록 전용): metric slew_rate_v_per_s·settle_s 는 성능 기록 행(SPICE None, 판정 N/A(not_measured: ...)),
compare.summary.transient = {status: "not_measured", measures, reason}. 판정 대상 아님 -- 제약 measure enum 에 없어
선언하면 스키마 위반(C13: 반환 2, 산출물 없음). 근거: README C25·C13, schema metrics/constraints measure enum 만.
"""
import copy

import pytest

from conftest import (by_name, cs_input, independent_cs, make_lut, preds_from_independent, run_oracle, stem_of)

TRAN = [{"name": "sr", "measure": "slew_rate_v_per_s", "value": 1e6},
        {"name": "ts", "measure": "settle_s", "value": 1e-6}]


@pytest.fixture(scope="module")
def ind(ref_root):
    return independent_cs(ref_root)


def _inp(lut, ind, metrics):
    pr = preds_from_independent(ind)
    return cs_input(lut, diffusion="zero", preds_nodes=pr["nodes"], preds_devices=pr["devices"], metrics=metrics)


@pytest.fixture(scope="module")
def ran(tmp_path_factory, ind):
    d = tmp_path_factory.mktemp("tran")
    inp = _inp(make_lut(d / "lut.npz"), ind, copy.deepcopy(TRAN))
    p, res = run_oracle(inp, d / "o", biases=("free", "forced"), sat_margin=0.05)
    assert res["free"] is not None, (p.stdout + p.stderr)[-1500:]
    return d, inp, p, res


@pytest.mark.parametrize("bias", ["free", "forced"])
def test_rows_not_measured(ran, bias):
    _, _, _, res = ran
    for name in ("sr", "ts"):
        r = by_name(res[bias]["performance"], "name", name)
        assert r["spice"] is None and r["judge"].startswith("N/A(not_measured"), r


@pytest.mark.parametrize("bias", ["free", "forced"])
def test_summary_transient(ran, bias):
    _, _, _, res = ran
    t = res[bias]["summary"]["transient"]
    assert t["status"] == "not_measured"
    assert set(t["measures"]) == {"slew_rate_v_per_s", "settle_s"}, t
    assert isinstance(t["reason"], str) and t["reason"].strip()


def test_record_only_verdict_unaffected(ran):
    """판정 대상 아님: 슬루·정착 metric 이 있어도 PASS 가 INCOMPLETE 로 내려가지 않는다(나머지는 전부 합격 조건 만족)."""
    _, _, p, res = ran
    assert res["free"]["summary"]["verdict"] == "PASS", res["free"]["summary"]
    assert p.returncode == 0


def test_no_tran_analysis_in_netlist(ran):
    d, inp, _, _ = ran
    text = (d / "o" / f"{stem_of(inp, 'free')}.cir").read_text(encoding="utf-8").lower()
    assert not any(ln.strip().startswith(("tran", ".tran")) for ln in text.splitlines())


@pytest.mark.parametrize("measure", ["slew_rate_v_per_s", "settle_s"])
def test_transient_constraint_rejected_by_schema(tmp_path, ind, measure):
    inp = _inp(make_lut(tmp_path / "lut.npz"), ind, [])
    inp["acceptance"] = {"constraints": [{"name": "x", "measure": measure, "op": ">=", "limit": 1.0}]}
    out = tmp_path / "o"
    p, res = run_oracle(inp, out, sat_margin=0.05)
    assert p.returncode == 2 and res["free"] is None
    assert sorted(x.name for x in out.iterdir()) == ["t.input.json"]
