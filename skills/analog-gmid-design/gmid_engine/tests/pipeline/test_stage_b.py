"""pipeline/stage_b.py -- `run_stage_b(stage_a, memo, pdk_decl, *, output_dir, diagnostic=False) -> StageBResult`
(pipeline CONTRACT 5절, 설계 41 0절 A5~A7·4절, 40 3.4, FR-8).

입력은 해석식 toy LUT(metrics/gb4_hand: x = gm/ID = 20 − 8·VGS, y = gds/ID = 0.1, z = gmb/ID = 4·VS; VGS 0..1.8/0.1, L 2 점, VDS 7 점,
VS (−0.45, 0, 0.45, 0.9, 1.35, 1.8))와 toy PDK 선언(제조 격자 1e-8 m, 최소 finger 0.5 µm, MIM 4e-3 F/m² -- search conftest), 손 회로.
oracle (a) 손 계산:
- 소스 팔로워 + 이상 전류원 부하: A_max = max x/(x + y + z) = 5.6/3.9 (VGS 1.8, VS −0.45), b = 20·log10((5.6/3.9)/(5.6/5.7)),
  Π = 19·2·7·6 = 1596. gain ≥ 10 dB 는 인증된 상한 + b(≈ 6.44 dB)보다 커서 exit 3(`gain_target_above_upper_bound`).
- CS(전류원 부하): A_max = 20/(0.1 + 0.1) = 100 = 40 dB, b = 20·log10(20/19.2), Π = 19²·2²·7² = 70756 -- 기본 N_S(3192)를 넘어 미상,
  spec `structure_count_budget` 10⁶ 선언이면 인증.
- 두 단 CS 사슬: 체인 상한 = 40 + 40 dB, b = 2·20·log10(20/19.2).
- 면적: 값 선언 전류원 1e-4 A 가 정하는 팔로워 전류 + 값 선언 커패시터 1 pF: A_lb = 1e-4·L_min²/IDu_max + 1e-12/4e-3.
- 헤드룸: 인버터 입력(두 극성 gate 공유) 창은 레일 안이라 폭 ≤ 1.8 V -> `icmr_v >= 2.0` 은 인증된 상한으로 exit 3.
oracle (d) 계약: 단계 A 가 ok 가 아니면 GB4 앞 정지(status skipped, 단계 A exit code), diagnostic 이면 계산만 하고 정지 판정은 그대로.
N_S 는 단계 A 와 같은 정의(회로가 쓰는 kind 의 격자점 합, 41 0절 '같은 S0 이면 결과가 늘 같다').
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.pipeline import StageBResult, run_stage_a, run_stage_b

TESTS = Path(__file__).resolve().parents[1]
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
from metrics.gb4_hand import (A, GRIDS, I0, L_GRID, LAM, TOY_MIM_DENSITY, VDS_GRID, VGS_GRID, VS_GRID, db, f_default,  # noqa: E402
                              gain_blocks, memo_of, mos_e, stage_ab, toy_pdk, topology, two_e, write_case, write_lut)

PI_FOL = 19 * 2 * 7 * 6
PI_CS = 19 ** 2 * 2 ** 2 * 7 ** 2
FOL_AMAX_DB = db(5.6 / 3.9)
FOL_B_DB = db((5.6 / 3.9) / (5.6 / 5.7))
CS_B_DB = db(20.0 / 19.2)


@pytest.fixture(scope="module")
def toy(tmp_path_factory):
    return write_lut(tmp_path_factory.mktemp("sb_lut"))


@pytest.fixture(scope="module")
def pdk(tmp_path_factory):
    return toy_pdk(tmp_path_factory.mktemp("sb_pdk"))


def follower(name="sbfol"):
    return topology(name, [mos_e("M1", "nmos", "vdd", "in", "out")], sources=[two_e("I1", "current_source", "out", "gnd")])


def cs(name="sbcs", ren=None, dev=None):
    r = (ren or {}).get
    d = (dev or {}).get
    return topology(name, [mos_e(d("M1", "M1"), "nmos", r("out", "out"), r("in", "in"), "gnd"),
                           mos_e(d("M2", "M2"), "pmos", r("out", "out"), r("pb", "pb"), "vdd")],
                    ports={r("in", "in"): ("input", "single_ended_input"), r("out", "out"): ("output", "single_ended_output")},
                    bias=[r("pb", "pb")])


def test_follower_gain_target_above_certified_bound_is_exit_3(tmp_path, toy, pdk):
    tp, sp = write_case(tmp_path, follower(), elements=(("I1", "current_source", None),), constraints=(("gain_ss_db", ">=", 10.0),))
    a, b = stage_ab(tmp_path, toy, tp, sp, pdk)
    assert (a.status, a.exit_code) == ("ok", 0)
    assert isinstance(b, StageBResult)
    assert (b.status, b.exit_code) == ("infeasible", 3)
    assert any(s.startswith("gain_target_above_upper_bound") for s in b.report["stop_reasons"])
    (blk,) = gain_blocks(b.report).values()
    assert blk["status"] == "certified" and blk["pi"] == PI_FOL
    assert blk["a_max_db"] == pytest.approx(FOL_AMAX_DB, abs=1e-9)
    assert blk["b_db"] == pytest.approx(FOL_B_DB, abs=1e-9)
    g = b.report["achievability"]["gain"]
    assert g["verdict"] == "infeasible" and g["target_db"] == 10.0
    assert g["sum_db"] == pytest.approx(FOL_AMAX_DB, abs=1e-9)
    assert b.achievability is not None and b.achievability.verdict == "infeasible"
    # 보고서는 항상 쓴다(json·md)
    jp, mp = (Path(p) for p in b.report_paths)
    assert jp.name == "sbfol.stage_b.json" and mp.name == "sbfol.stage_b.md"
    on_disk = json.loads(jp.read_text(encoding="utf-8"))
    assert on_disk["exit_code"] == 3 and on_disk["status"] == "infeasible" and on_disk["circuit"] == "sbfol"
    assert mp.read_text(encoding="utf-8").strip()


def test_follower_without_gain_constraint_is_ok(tmp_path, toy, pdk):
    tp, sp = write_case(tmp_path, follower(), elements=(("I1", "current_source", None),))
    _, b = stage_ab(tmp_path, toy, tp, sp, pdk)
    assert (b.status, b.exit_code) == ("ok", 0)
    assert b.report["stop_reasons"] == []


def test_stage_b_count_budget_equals_stage_a_for_same_s0(tmp_path, toy, pdk):
    # 41 0절: N_S = 이 회로에 쓰이는 kind 의 격자점 합(같은 S0 -> 같은 값). 팔로워는 nmos 만 쓴다 -> 1596(nmos 슬라이스 1 개)
    tp, sp = write_case(tmp_path, follower(), elements=(("I1", "current_source", None),))
    a, b = stage_ab(tmp_path, toy, tp, sp, pdk)
    assert a.report["count_budget"] == PI_FOL
    assert b.report["count_budget"] == a.report["count_budget"]


def test_cs_unknown_under_default_budget_and_certified_with_declared_budget(tmp_path, toy, pdk):
    tp, sp = write_case(tmp_path / "d", cs(), constraints=(("gain_ss_db", ">=", 60.0),))
    _, b = stage_ab(tmp_path / "d", toy, tp, sp, pdk)
    (blk,) = gain_blocks(b.report).values()
    assert blk["pi"] == PI_CS
    assert PI_CS > b.report["count_budget"]
    assert blk["status"] == "unknown" and blk["reason"] == "grid_product_over_budget"
    # 미상이면 판정하지 않는다 -> 정지 없음(41 4.3)
    assert (b.status, b.exit_code) == ("ok", 0)
    assert b.report["achievability"]["gain"]["verdict"] == "undetermined"

    tp, sp = write_case(tmp_path / "c", cs(), constraints=(("gain_ss_db", ">=", 60.0),), count_budget=10 ** 6)
    _, b = stage_ab(tmp_path / "c", toy, tp, sp, pdk)
    assert b.report["count_budget"] == 10 ** 6
    (blk,) = gain_blocks(b.report).values()
    assert blk["status"] == "certified"
    assert blk["a_max_db"] == pytest.approx(40.0, abs=1e-9) and blk["b_db"] == pytest.approx(CS_B_DB, abs=1e-9)
    assert (b.status, b.exit_code) == ("infeasible", 3)


def test_cs_target_within_bound_plus_resolution_is_not_stopped(tmp_path, toy, pdk):
    # 40 + 0.3546 = 40.35 >= 40.2 -> 'Σ(A + b) < G' 가 아니다 -> 정지 없음
    tp, sp = write_case(tmp_path, cs(), constraints=(("gain_ss_db", ">=", 40.2),), count_budget=10 ** 6)
    _, b = stage_ab(tmp_path, toy, tp, sp, pdk)
    assert (b.status, b.exit_code) == ("ok", 0)
    assert b.report["achievability"]["gain"]["verdict"] != "infeasible"


def _cs2():
    return topology("sbcs2", [mos_e("M1", "nmos", "a", "in", "gnd"), mos_e("M2", "pmos", "a", "pb", "vdd"),
                              mos_e("M3", "nmos", "out", "a", "gnd"), mos_e("M4", "pmos", "out", "pc", "vdd")],
                    bias=["pb", "pc"])


@pytest.mark.parametrize("target,stops", [(81.0, True), (80.5, False)])
def test_two_stage_chain_sum_check(tmp_path, toy, pdk, target, stops):
    # 체인 상한 = 40 + 40 dB, b 합 = 2·0.3546 -> 80.709: 81 이면 정지, 80.5 면 정지 없음
    tp, sp = write_case(tmp_path, _cs2(), constraints=(("gain_ss_db", ">=", target),), count_budget=10 ** 6)
    _, b = stage_ab(tmp_path, toy, tp, sp, pdk)
    blocks = gain_blocks(b.report)
    assert sorted(blocks) == [("a",), ("out",)]
    assert all(x["status"] == "certified" and x["a_max_db"] == pytest.approx(40.0, abs=1e-9) for x in blocks.values())
    g = b.report["achievability"]["gain"]
    assert g["sum_db"] == pytest.approx(80.0, abs=1e-9)
    assert g["b_db"] == pytest.approx(2 * CS_B_DB, abs=1e-9)
    assert (b.exit_code == 3) is stops


def _idu_max_nmos():
    g = np.asarray(VGS_GRID)[:, None, None]
    d = np.asarray(VDS_GRID)[None, :, None]
    s = np.asarray(VS_GRID)[None, None, :]
    return I0["nmos"] * float(np.exp(f_default(g) + LAM * d - A * s * s).max())


def test_area_lower_bound_above_budget_is_exit_3(tmp_path, toy, pdk):
    topo = topology("sbarea", [mos_e("M1", "nmos", "vdd", "in", "out")],
                    passives=[two_e("C1", "capacitor", "out", "gnd")], sources=[two_e("I1", "current_source", "out", "gnd")])
    lb = 1e-4 * min(L_GRID) ** 2 / _idu_max_nmos() + 1e-12 / TOY_MIM_DENSITY
    elements = (("I1", "current_source", 1e-4), ("C1", "capacitor", 1e-12))
    tp, sp = write_case(tmp_path / "x", topo, elements=elements, constraints=(("area_search_m2", "<=", 1e-10),))
    _, b = stage_ab(tmp_path / "x", toy, tp, sp, pdk)
    area = b.report["achievability"]["area"]
    assert area["a_lb_m2"] == pytest.approx(lb, rel=1e-9)
    assert dict((k, v) for k, v in area["terms"])["C1"] == pytest.approx(2.5e-10, rel=1e-12)
    assert area["verdict"] == "infeasible"
    assert (b.status, b.exit_code) == ("infeasible", 3)
    assert any(s.startswith("area_budget_below_lower_bound") for s in b.report["stop_reasons"])

    tp, sp = write_case(tmp_path / "y", topo, elements=elements, constraints=(("area_search_m2", "<=", 1e-9),))
    _, b = stage_ab(tmp_path / "y", toy, tp, sp, pdk)
    assert b.report["achievability"]["area"]["verdict"] == "not_excluded"
    assert (b.status, b.exit_code) == ("ok", 0)


def _inverter():
    return topology("sbinv", [mos_e("M1", "nmos", "out", "in", "gnd"), mos_e("M2", "pmos", "out", "in", "vdd")])


def test_headroom_icmr_wider_than_rails_is_exit_3(tmp_path, toy, pdk):
    tp, sp = write_case(tmp_path, _inverter(), constraints=(("icmr_v", ">=", 2.0),))
    _, b = stage_ab(tmp_path, toy, tp, sp, pdk)
    rows = [h for h in b.report["achievability"]["headroom"] if h["window_kind"] == "input"]
    assert rows and all(h["upper_bound_v"] <= 1.8 + 1e-12 for h in rows)
    assert (b.status, b.exit_code) == ("infeasible", 3)
    assert any(s.startswith("headroom_unattainable") for s in b.report["stop_reasons"])


def test_skipped_when_stage_a_is_not_ok(tmp_path, toy, pdk):
    import s1v_hand as H
    tp, sp = write_case(tmp_path, H.FOLDED)
    a, b = stage_ab(tmp_path, toy, tp, sp, pdk)
    assert a.status == "review_needed" and a.exit_code == 2
    assert b.status == "skipped" and b.exit_code == a.exit_code
    assert b.achievability is None and b.diagnostic is False
    assert all(Path(p).is_file() for p in b.report_paths)


def test_diagnostic_measures_but_keeps_stage_a_stop(tmp_path, toy, pdk):
    # 계약 5절: diagnostic=True 면 정지 상태에서도 계산해 측정만 한다 -- 정지 판정은 안 바뀐다(exit code = 단계 A 의 것)
    import s1v_hand as H
    tp, sp = write_case(tmp_path, H.FOLDED)
    a, b = stage_ab(tmp_path, toy, tp, sp, pdk, diagnostic=True)
    assert a.exit_code == 2
    assert b.diagnostic is True and b.achievability is not None
    assert b.exit_code == a.exit_code
    assert b.status != "ok"


def _numbers(rep):
    ach = rep["achievability"]
    g = ach["gain"]
    return (rep["status"], rep["exit_code"], rep["count_budget"],
            sorted((x["status"], x["pi"], x["a_max_db"], x["b_db"]) for x in g["blocks"]), g["sum_db"], g["b_db"], g["verdict"],
            ach["area"]["a_lb_m2"], sorted((h["window_kind"], h["upper_bound_v"], h["status"]) for h in ach["headroom"]),
            (ach["dof"]["status"], ach["dof"]["structural_rank"], len(ach["dof"]["free_variables"])))


def test_deterministic_and_name_bijection_invariant(tmp_path, toy, pdk):
    cons = (("gain_ss_db", ">=", 60.0),)
    tp, sp = write_case(tmp_path / "a", cs(), constraints=cons, count_budget=10 ** 6)
    _, b1 = stage_ab(tmp_path / "a", toy, tp, sp, pdk)
    _, b2 = stage_ab(tmp_path / "a", toy, tp, sp, pdk, out="out2")
    assert _numbers(b1.report) == _numbers(b2.report)
    ren = {"in": "zin", "out": "aout", "pb": "mbias"}
    dev = {"M1": "Q9", "M2": "A0"}
    tp, sp = write_case(tmp_path / "b", cs("sbcsr", ren, dev), constraints=cons, count_budget=10 ** 6)
    _, b3 = stage_ab(tmp_path / "b", toy, tp, sp, pdk)
    assert _numbers(b3.report) == _numbers(b1.report)
