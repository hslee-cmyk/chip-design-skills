"""O-h `check_off_judged_by(region_decl, constraint_classes, declared) -> None` -- interface card 20261104-eo1r4-sf1l §5 (T-J1).

oracle (식): card §5 표 reason 행과 '판정 제약 칸' 정의(`.judged` metric ∪ `declared[i].metric`, i ∈ `.ss`; `.notes` 는 아님)를 행마다 손으로 옮겼다.
metric 종류는 레지스트리 표를 읽어 정한 것이 아니라 metrics 계약 test(test_verified_by)가 선언한 종류를 쓴다:
  spice_oracle = gain_ss_db·pm_ss_deg·swing_out_v·power_dc_w·supply_current_dc, spice_unverifiable = mirror_ratio_sigma_pct,
  engine_only = offset_excess, 레지스트리 밖 = no_such_metric.
거부는 SchemaRejectedError(stop 부류 -- 후보 실패 기록 아님)이고 사유는 `dict(exc.record.detail)["reason"]`.
경로 test: `build_search_context` 가 constraint_classes 뒤 탐색 전 한 번 부르고, 정지 때 평가 블록 호출이 0 이다.
"""
import dataclasses
import json
from pathlib import Path

import pytest

from gmid_engine.authoring import RegionDecl, load_sizing_spec, load_topology
from gmid_engine.core import CANDIDATE_FAILURE_CLASSES, SchemaRejectedError
from gmid_engine.graph import build_s1
from gmid_engine.metrics import metric_catalog
from gmid_engine.search import SearchSettings, build_search_context, check_off_judged_by, open_run
from gmid_engine.search.search_values import ConstraintClasses
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec

from metrics.conftest import spec_json

from .conftest import CODE_FP, SRC, SUPPLIES, block_row, mos, new_access, topo, two, write_decls


@dataclasses.dataclass(frozen=True)
class Decl:
    """spec 판정 제약 선언의 test 쪽 입력 형식(`.metric` 속성만 읽힌다)."""

    metric: str
    op: str = ">="
    value: float = 1.0


def off(name="Moff", judged_by=()):
    return RegionDecl(name, "off", None, tuple(judged_by), 1e-6, 1e-6)


def note(metric):
    return (("metric", metric), ("op", ">="), ("verdict", "unmeasured"))


# declared 순서: 0 gain_ss_db, 1 pm_ss_deg, 2 rout_ss_ohm
DECLARED = (Decl("gain_ss_db"), Decl("pm_ss_deg"), Decl("rout_ss_ohm"))


def classes(judged=(("power_dc_w", "<=", 1e-3),), ss=(0, 1), notes=()):
    return ConstraintClasses(tuple(judged), tuple(ss), tuple(notes))


def reason(exc):
    return dict(exc.value.record.detail)["reason"]


def check(decls, cc=None, declared=DECLARED):
    return check_off_judged_by({d.device: d for d in decls}, cc or classes(), declared)


# ---- 통과 행 --------------------------------------------------------------------------------------------------

def test_off_judged_no_off_device_returns_none():
    assert check([]) is None
    assert check([RegionDecl("Mt", "triode")]) is None                     # triode 는 대상 아님(judged_by 빈 값이어도)


@pytest.mark.parametrize("metric", ["gain_ss_db", "pm_ss_deg", "power_dc_w"],
                         ids=["ss_index0", "ss_index1", "judged_axis"])
def test_off_judged_by_judged_oracle_metric_passes(metric):
    assert check([off(judged_by=(metric,))]) is None


def test_off_judged_multiple_metrics_and_devices_all_ok_returns_none():
    assert check([off("Ma", ("gain_ss_db", "power_dc_w")), off("Mb", ("pm_ss_deg",))]) is None


# ---- 거부 행 --------------------------------------------------------------------------------------------------

def test_off_judged_empty_judged_by_is_undeclared():
    with pytest.raises(SchemaRejectedError) as ei:
        check([off(judged_by=())])
    assert reason(ei) == "off_judged_by_undeclared"
    assert type(ei.value) not in CANDIDATE_FAILURE_CLASSES                  # 후보 실패 기록이 아니라 stop 부류


def test_off_judged_one_empty_among_devices_is_undeclared():
    with pytest.raises(SchemaRejectedError) as ei:
        check([off("Ma", ("gain_ss_db",)), off("Mb", ())])
    assert reason(ei) == "off_judged_by_undeclared"


def test_off_judged_metric_not_in_judged_columns():
    with pytest.raises(SchemaRejectedError) as ei:
        check([off(judged_by=("swing_out_v",))])                            # 레지스트리 metric 이지만 판정 제약 칸에 없음
    assert reason(ei) == "off_judged_by_not_judged"


def test_off_judged_one_bad_metric_among_good_ones_rejects():
    with pytest.raises(SchemaRejectedError) as ei:
        check([off(judged_by=("gain_ss_db", "swing_out_v"))])
    assert reason(ei) == "off_judged_by_not_judged"


def test_off_judged_ss_position_is_judged_but_declared_not_in_ss_is_not():
    """ss = (0,) 이면 declared[1]·declared[2] 의 metric 은 판정 제약 칸이 아니다."""
    cc = classes(judged=(), ss=(0,))
    assert check([off(judged_by=("gain_ss_db",))], cc) is None
    for metric in ("pm_ss_deg", "rout_ss_ohm"):
        with pytest.raises(SchemaRejectedError) as ei:
            check([off(judged_by=(metric,))], cc)
        assert reason(ei) == "off_judged_by_not_judged"


def test_off_judged_notes_metric_is_not_judged():
    """`.notes` 쪽 metric 은 판정 제약 칸이 아니다(spice_oracle 종류여도)."""
    cc = classes(judged=(), ss=(), notes=(note("supply_current_dc"),))
    with pytest.raises(SchemaRejectedError) as ei:
        check([off(judged_by=("supply_current_dc",))], cc)
    assert reason(ei) == "off_judged_by_not_judged"


@pytest.mark.parametrize("metric", ["mirror_ratio_sigma_pct", "offset_excess", "no_such_metric"],
                         ids=["spice_unverifiable", "engine_only", "outside_registry"])
def test_off_judged_by_not_oracle_verified_is_unverified(metric):
    cc = classes(judged=(("power_dc_w", "<=", 1e-3), (metric, "<=", 1.0)))     # 판정 제약 칸에는 있다
    with pytest.raises(SchemaRejectedError) as ei:
        check([off(judged_by=(metric,))], cc)
    assert reason(ei) == "off_judged_by_unverified"


def test_off_judged_return_value_is_none_not_truthy_report():
    assert check([off(judged_by=("gain_ss_db",))]) is None


# ---- 경로: build_search_context ------------------------------------------------------------------------------

EVAL_BLOCKS = ("dc_currents", "dc_lengths", "dc_columns", "dc_widths", "dc_tolerances", "dc_seal_region",
               "dc_seal_bulk_reverse", "dc_seal_vgs_match")
OFF_SRC = {"kind": "user_spec", "record": "off judged path test", "decided": "2026-11-04"}


def _path_case(tmp_path, lut, judged_by, constraints=(("gain_ss_db", ">=", 20.0, None),)):
    """회로: nmos M1 (out, in, gnd) + R1 (vdd, out) + pmos Mp (out, vdd, vdd) 를 off 로 선언. 반환 (dc, spec, settings, pdk, rule)."""
    doc = topo("hand_offpath", [mos("M1", "nmos", "out", "in", "gnd"), mos("Mp", "pmos", "out", "vdd", "vdd")],
               {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
               passives=[two("R1", "resistor", "vdd", "out")])
    tmp = Path(tmp_path)
    tmp.mkdir(parents=True, exist_ok=True)
    tp = tmp / "hand_offpath.topology.json"
    tp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    td = load_topology(str(tp))
    raw = spec_json(td, SUPPLIES, [("R1", "resistor", None)], (), constraints)
    entry = {"region": "off", "w_m": 1e-6, "l_m": 1e-6, "source": dict(OFF_SRC)}
    if judged_by is not None:
        entry["judged_by"] = list(judged_by)
    raw["human"]["intended_region"] = {"Mp": entry}
    sp = tmp / "hand_offpath.sizing_spec.json"
    sp.write_text(json.dumps(raw, indent=1), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, metric_catalog())
    inputs = dc_inputs_from_spec(spec)
    donors, counters = open_run()
    dc = build_kernel_context(build_s1(td, dict(inputs.supplies_v), donors=donors, counters=counters), inputs,
                              new_access(lut), donors=donors, counters=counters)
    pdk, rule = write_decls(tmp / "pdk")
    return dc, spec, SearchSettings(600.0, 40, (1e3, 1e6), SRC), pdk, rule


def test_off_judged_path_passes_when_declared_metric_is_judged(tmp_path, lut_sealed):
    dc, spec, settings, pdk, rule = _path_case(tmp_path, lut_sealed, ["gain_ss_db"])
    assert build_search_context(dc, spec, settings, None, pdk, rule, code_fp=CODE_FP) is not None


@pytest.mark.parametrize("judged_by,constraints,expected", [
    ([], (("gain_ss_db", ">=", 20.0, None),), "off_judged_by_undeclared"),
    (None, (("gain_ss_db", ">=", 20.0, None),), "off_judged_by_undeclared"),
    (["rout_ss_ohm"], (("gain_ss_db", ">=", 20.0, None),), "off_judged_by_not_judged"),
    (["supply_current_dc"], (("gain_ss_db", ">=", 20.0, None), ("supply_current_dc", "<=", 2e-4, None)),
     "off_judged_by_not_judged"),                                       # .notes 위치(ss 뷰 없는 metric)
], ids=["empty", "missing", "not_a_constraint", "notes_position"])
def test_off_judged_path_stops_before_any_evaluation(tmp_path, lut_sealed, judged_by, constraints, expected):
    dc, spec, settings, pdk, rule = _path_case(tmp_path, lut_sealed, judged_by, constraints)
    with pytest.raises(SchemaRejectedError) as ei:
        build_search_context(dc, spec, settings, None, pdk, rule, code_fp=CODE_FP)
    assert reason(ei) == expected
    assert [(b, block_row(dc.counters, b)[0]) for b in EVAL_BLOCKS if block_row(dc.counters, b)[0] != 0] == []
