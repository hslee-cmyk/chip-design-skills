"""`layout_input_of(snapshot, pdk, passives, rejected=(), relaxed=()) -> (LayoutInput, undelivered)` (CONTRACT 1절, graph CONTRACT 4.5a 전달 정책,
설계 40 §11 U14 'U12 인계: 봉인 스냅샷 -> LayoutInput 어댑터').

oracle (a): 가짜 스냅샷(피검이 읽는 `column`·`value` 만)에 손으로 둔 S1·S2 필드에서 LayoutDevice·행 그룹·matching 그룹을 손으로 적는다.
oracle (d) 실경로: two_stage_ota topology JSON(사용자 선언 connectivity)의 단자 넷과 회로 해석(M1/M2 차동쌍 hub = 공통 source CS, M3/M4 미러 hub = source vdd).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gmid_engine.convergence import layout_input_of
from gmid_engine.graph import GRAPH_KEY, MOS_TERMINAL_NAMES
from gmid_engine.layout import LayoutInput
from gmid_engine.layout.contract_input import LayoutPassive

from .conftest import FakeSnapshot, op, pdk

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"
PDK = pdk((("nmos", (100,)), ("pmos", (100,))), grid=1e-8)
NETS = {   # 소자: (drain, gate, source, body, kind, diode, coord role)
    "N1": ("o1", "inp", "tail", "gnd", "nmos", False, "writer"),
    "N2": ("o2", "inn", "tail", "gnd", "nmos", False, "dependent"),
    "N3": ("x3", "g3", "s3", "pw", "nmos", False, "writer"),
    "N4": ("b4", "g4", "gnd", "gnd", "nmos", False, "writer"),
    "N5": ("b5", "g5", "gnd", "gnd", "nmos", False, "dependent"),
    "N6": ("x6", "g6", "s3", "gnd", "nmos", False, "writer"),
    "N7": ("x7", "g7", "gnd", "gnd", "nmos", False, "writer"),
    "N8": ("x8", "g8", "gnd", "pw", "nmos", False, "writer"),
    "P1": ("pg", "pg", "vdd", "vdd", "pmos", True, "writer"),
    "P2": ("o1", "pg", "vdd", "vdd", "pmos", False, "dependent"),
    "P3": ("y3", "bp", "vdd", "vdd", "pmos", False, "writer"),
    "P4": ("y4", "bp", "vdd", "vdd", "pmos", False, "dependent"),
}


def group(kind, members, status, rule, nets):
    return SimpleNamespace(kind=kind, members=tuple(members), status=status, evidence=SimpleNamespace(rule=rule, nets=tuple(nets)))


def snapshot():
    ops = {n: op(kind=v[4], W=1e-6 * (i + 1), current=1e-6 * (i + 2), L=2e-7 * (i + 1), gm_id=10.0 + i, vds=0.3 + 0.01 * i,
                 vsb=0.01 * i) for i, (n, v) in enumerate(sorted(NETS.items()))}
    pins = {n: tuple(zip(MOS_TERMINAL_NAMES, v[:3])) for n, v in NETS.items()}
    groups = (
        group("diff_pair", ("N2", "N1"), "derived", "dp", ("tail", "inp", "inn")),
        group("mirror", ("P1", "P2"), "ratified", "mir", ("pg", "vdd")),
        group("branch_symmetric", ("N4", "N5"), "derived", "bs", ("b4", "b5")),
        group("mirror", ("P3", "P1"), "review_needed", "mir2", ("bp", "vdd")),         # 전달 안 함(4.5a)
        group("diff_pair", ("N6", "N3"), "derived", "dp2", ("s3",)),                   # 멤버 body 가 둘 -> undelivered
    )
    disp = (
        group("bias_distribution", ("P4", "P3"), "proposed", "bd", ()),               # 제외 role 그룹
        group("feedback_shared", ("N8", "N7"), "proposed", "fs", ()),                 # 제외 role -- body 가 달라도 넘긴다
        group("feedback_shared", ("N1",), "proposed", "fs", ()),                      # 멤버 하나 -> 그룹 아님
        group("bias_sibling", ("N4", "N7"), "proposed", "sib", ()),                   # layout role 아님 -> 버림
    )
    return FakeSnapshot({
        ("device", "dc_op"): ops,
        ("device", "is_diode"): {n: v[5] for n, v in NETS.items()},
        ("device", "dc_coord"): {n: SimpleNamespace(role=v[6]) for n, v in NETS.items()},
        ("device", "pins"): pins,
        ("device", "bulk"): {n: SimpleNamespace(net=v[3]) for n, v in NETS.items()},
        ("graph", "matching_groups"): {GRAPH_KEY: groups},
        ("graph", "matching_dispositions"): {GRAPH_KEY: disp},
    })


def test_devices_from_dc_op_and_s1_pins():
    snap = snapshot()
    ops = dict(snap.column("device", "dc_op"))
    li, _und = layout_input_of(snap, PDK, ())
    assert isinstance(li, LayoutInput)
    assert [d.name for d in li.devices] == sorted(NETS)
    for d in li.devices:
        o, (dr, g, s, body, kind, diode, role) = ops[d.name], NETS[d.name]
        assert (d.kind, d.drain, d.gate, d.source, d.body, d.diode) == (kind, dr, g, s, body, diode)
        assert (d.W_m, d.L_m, d.ID_A, d.gm_id, d.vds_V, d.vsb_V) == (o.W, o.L, o.current, o.gm_id, o.vds, o.vsb)
        assert d.W_adjustable is (role == "writer")        # 쓰기 소자만 W 를 고정 입력으로 받는다
        assert all(isinstance(x, float) for x in (d.W_m, d.L_m, d.ID_A, d.gm_id, d.vds_V, d.vsb_V))


def test_row_groups_per_kind_and_body_sorted():
    li, _ = layout_input_of(snapshot(), PDK, ())
    assert [(r.rid, r.kind, r.body_net, r.members) for r in li.row_groups] == [
        ("nmos|gnd", "nmos", "gnd", ("N1", "N2", "N4", "N5", "N6", "N7")),
        ("nmos|pw", "nmos", "pw", ("N3", "N8")),
        ("pmos|vdd", "pmos", "vdd", ("P1", "P2", "P3", "P4")),
    ]


def test_matching_groups_delivery_policy_hubs_and_gids():
    li, undelivered = layout_input_of(snapshot(), PDK, ())
    got = {g.gid: (g.members, g.role, g.hub_net, tuple(sorted(g.allowed_patterns))) for g in li.matching_groups}
    allp = ("common_centroid", "interdigitation")
    assert got == {
        "dp|N1+N2": (("N1", "N2"), "diff_pair", "tail", allp),          # hub = evidence 첫 넷(공통 source)
        "mir|P1+P2": (("P1", "P2"), "mirror", "vdd", allp),             # hub = evidence (gate, source) 의 source
        "bs|N4+N5": (("N4", "N5"), "branch_symmetric", None, allp),     # hub 없음
        "bias_distribution|P3+P4": (("P3", "P4"), "bias_distribution", None, allp),
        "feedback_shared|N7+N8": (("N7", "N8"), "feedback_shared", None, allp),
    }
    assert undelivered == (("dp2|N3+N6", "members_span_row_groups"),)


def test_relaxed_changes_only_hubbed_groups():
    li, _ = layout_input_of(snapshot(), PDK, (), relaxed=("dp|N1+N2", "bs|N4+N5"))
    got = {g.gid: (g.role, g.hub_net, tuple(g.allowed_patterns)) for g in li.matching_groups}
    assert got["dp|N1+N2"] == ("mirror", "tail", ("interdigitation",))
    bs = got["bs|N4+N5"]
    assert (bs[0], bs[1], set(bs[2])) == ("branch_symmetric", None, {"common_centroid", "interdigitation"})
    assert got["mir|P1+P2"][0] == "mirror" and set(got["mir|P1+P2"][2]) == {"common_centroid", "interdigitation"}


def test_rejected_passives_pdk_and_input_untouched():
    snap = snapshot()
    before = copy.deepcopy(snap.fields)
    passives = (LayoutPassive("Cc", 1e-10),)
    li, _ = layout_input_of(snap, PDK, passives, rejected=("P2", "N1"))
    assert li.rejected_requests == ("N1", "P2")
    assert li.passives == passives
    assert li.pdk is PDK
    assert snap.fields == before


def test_deterministic():
    a, ua = layout_input_of(snapshot(), PDK, ())
    b, ub = layout_input_of(snapshot(), PDK, ())
    assert a == b and ua == ub


# ---------------------------------------------------------------- 실경로 (two_stage_ota 손 봉인 점)

def test_real_two_stage_snapshot(real):
    _case, _sctx, start = real.start("two_stage_ota")
    doc = json.loads((LIBRARY / "two_stage_ota.topology.json").read_text(encoding="utf-8"))
    nets = {d["name"]: (d["drain"], d["gate"], d["source"], d["kind"]) for d in doc["netlist"]}
    li, undelivered = layout_input_of(start.evaluation.snapshot, real_pdk(real), ())
    assert sorted(d.name for d in li.devices) == sorted(nets)
    for d in li.devices:
        dr, g, s, kind = nets[d.name]
        assert (d.drain, d.gate, d.source, d.kind) == (dr, g, s, kind)
        # body 기본값: nmos -> 가장 낮은 레일 gnd, pmos -> 가장 높은 레일 vdd(spec supplies_v = vdd 1.8, gnd 0)
        assert d.body == ("gnd" if kind == "nmos" else "vdd")
    groups = {g.members: g for g in li.matching_groups}
    assert groups[("M1", "M2")].role == "diff_pair" and groups[("M1", "M2")].hub_net == "CS"
    assert groups[("M3", "M4")].role == "mirror" and groups[("M3", "M4")].hub_net == "vdd"
    assert undelivered == ()


def real_pdk(real):
    from gmid_engine.layout import LayoutPdk
    return LayoutPdk.from_decl(real.env.lut, real.env.pdk)


@pytest.mark.parametrize("bad", ["N1"])
def test_unknown_snapshot_device_name_is_not_invented(bad):
    # 거부/누락 확인: dc_op 에 없는 이름은 장치로 만들지 않는다(dc_op 가 MOS 목록의 정본)
    snap = snapshot()
    del snap.fields[("device", "dc_op")][bad]
    for key in (("device", "is_diode"), ("device", "dc_coord")):
        snap.fields[key].pop(bad)
    snap.fields[("graph", "matching_groups")][GRAPH_KEY] = ()
    snap.fields[("graph", "matching_dispositions")][GRAPH_KEY] = ()
    li, _ = layout_input_of(snap, PDK, ())
    assert bad not in {d.name for d in li.devices}
