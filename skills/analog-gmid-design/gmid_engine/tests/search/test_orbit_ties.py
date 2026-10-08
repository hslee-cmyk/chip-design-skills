"""search CONTRACT 3.24 [r12] `orbit_ties(dc_ctx, components, untied) -> (대표 성분 tuple, ties)` + 3.7 [r12] `search_domain(..., untie)` 묶음.

oracle:
- (a) 구성: 손 회로 SYM 의 자기동형 σ = (M1 M2)(M3 M4)(CL1 CL2)(inp inn)(o1 o2)(`canon_cases.SYM_SIGMA`) -- 기대 묶음 = σ 로 짝지어지는 같은 종류
  스키마 성분 쌍(`expected_sym_groups`, 스키마 성분 = sizing 4.4 입력 열). 단일 종단 회로 C 는 궤도 모두 단일 -> 묶음 없음.
- (d) 계약 문장: 3.24 7 (a)(d)(e)(f)(g), 2 의 거부 사유 `tied_orbit_bounds_differ`, 5 의 `untie_element_unknown`·`untie_orbit_trivial`(gate `search_domain`).
대표 = 구조 색 dc_colour 최소(3.24 1, U2 개정 -- 스냅샷 입력 열로 확인).
"""
from __future__ import annotations

import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.search import SearchSettings, orbit_ties, search_domain

from .canon_cases import (
    C_BOX,
    SYM_ELEMENTS,
    asym_doc,
    expected_sym_groups,
    make_case,
    rename_doc,
    sym_doc,
    tie_groups,
)
from .conftest import SRC, two

BOXES = {"CL1": C_BOX, "CL2": C_BOX}


def _sym(tmp, lut, **kw):
    kw.setdefault("boxes", BOXES)
    return make_case(tmp, sym_doc(), lut, elements=SYM_ELEMENTS, **kw)


def _domain(case, untie=()):
    return search_domain(case.dc, SearchSettings(600.0, 40, None, SRC), case.pdk, case.spec_bounds, untie=untie)


def _members(ties):
    return {m for _, ms in ties for m in ms}


# ---------------------------------------------------------------- 묶음 = 구성 자기동형 짝

def test_symmetric_pairs_tied_as_constructed(tmp_path, lut_sealed):
    case = _sym(tmp_path, lut_sealed)
    comps = case.dc.schema.components
    want = expected_sym_groups(comps)
    assert want                                                          # 공허한 비교 아님(L·전류·y·C 짝)
    assert tie_groups(case.sctx.domain.ties) == want
    reps, ties = orbit_ties(case.dc, comps, ())
    assert tie_groups(ties) == want


def test_variables_plus_tied_equal_schema_components(tmp_path, lut_sealed):
    """3.24 7 (a): L 밖 성분 = 변수 ⊔ 묶인 L 밖 구성원, L = l_cells 대표 MOS ⊔ 묶인 L 구성원(서로소)."""
    case = _sym(tmp_path, lut_sealed)
    d = case.sctx.domain
    comps = case.dc.schema.components
    members = _members(d.ties)
    var = [v.component for v in d.variables]
    non_l = [c for c in comps if c[0] != "L"]
    assert sorted(var + [m for m in members if m[0] != "L"]) == sorted(non_l)
    assert len(set(var)) == len(var)
    lmos = [m for m, _ in d.l_cells]
    assert sorted([("L", m) for m in lmos] + [m for m in members if m[0] == "L"]) == sorted(c for c in comps if c[0] == "L")
    assert len(var) + len([m for m in members if m[0] != "L"]) == len(comps) - len([c for c in comps if c[0] == "L"])


def test_representative_in_variables_members_not(tmp_path, lut_sealed):
    case = _sym(tmp_path, lut_sealed)
    d = case.sctx.domain
    var = {v.component for v in d.variables} | {("L", m) for m, _ in d.l_cells}
    for rep, members in d.ties:
        assert rep in var
        assert rep not in members and members
        assert not set(members) & var
        assert all(m[0] == rep[0] for m in members)                       # 같은 종류끼리만


def test_representative_is_min_dc_colour(tmp_path, lut_sealed):
    """3.24 1·2: 대표 = 묶음 안 구조 색(dc_colour) 최소(원소 키는 device, y 의 넷 키는 node 색)."""
    case = _sym(tmp_path, lut_sealed)
    dv = dict(case.dc.base.column("device", "dc_colour"))
    nv = dict(case.dc.base.column("node", "dc_colour"))
    col = lambda c: dv.get(c[1], nv.get(c[1]))                              # noqa: E731
    assert case.sctx.domain.ties
    for rep, members in case.sctx.domain.ties:
        assert all(col(rep) < col(m) for m in members)


def test_orbit_ties_reps_are_components_minus_members(tmp_path, lut_sealed):
    case = _sym(tmp_path, lut_sealed)
    comps = case.dc.schema.components
    reps, ties = orbit_ties(case.dc, comps, ())
    assert sorted(reps) == sorted(set(comps) - _members(ties))


def test_asymmetric_circuit_no_ties(tmp_path, lut_sealed):
    """3.24 7 (e): 단일 종단 회로 C -- 궤도 모두 단일 -> ties == (), 변수 = L 밖 스키마 성분 전부."""
    case = make_case(tmp_path, asym_doc(), lut_sealed)
    d = case.sctx.domain
    assert d.ties == ()
    comps = case.dc.schema.components
    assert sorted(v.component for v in d.variables) == sorted(c for c in comps if c[0] != "L")
    assert sorted(m for m, _ in d.l_cells) == sorted(c[1] for c in comps if c[0] == "L")
    reps, ties = orbit_ties(case.dc, comps, ())
    assert ties == () and sorted(reps) == sorted(comps)


def test_dc_orbit_pairs_follow_construction(tmp_path, lut_sealed):
    """입력 확인: 묶음의 근거인 dc_orbit 이 σ 짝에서 같고 고정점끼리 다르다(sizing 3.0b)."""
    case = _sym(tmp_path, lut_sealed)
    orb = dict(case.dc.base.column("device", "dc_orbit"))
    assert orb["M1"] == orb["M2"] and orb["M3"] == orb["M4"] and orb["CL1"] == orb["CL2"]
    assert len({orb["M1"], orb["M3"], orb["M5"], orb["CL1"]}) == 4


# ---------------------------------------------------------------- 거부 (3.24 2·5)

def test_bounds_differ_rejected(tmp_path, lut_sealed):
    """같은 궤도 CL1·CL2 에 서로 다른 spec 상자 -> tied_orbit_bounds_differ(gate search_domain)."""
    case = _sym(tmp_path / "a", lut_sealed, boxes={"CL1": C_BOX, "CL2": (1e-13, 1e-10)}, build_sctx=False)
    with pytest.raises(SchemaRejectedError) as e:
        _domain(case)
    det = dict(e.value.record.detail)
    assert (det["gate"], det["reason"]) == ("search_domain", "tied_orbit_bounds_differ")
    assert {"CL1", "CL2"} <= {x[1] if isinstance(x, tuple) else x for x in det["elements"]}   # 원소 또는 (종류, 원소)


def test_bounds_differ_rejected_by_build_search_context(tmp_path, lut_sealed):
    """build_search_context 도 같은 정의역을 만들므로 같은 거부(커널 호출 전)."""
    with pytest.raises(SchemaRejectedError) as e:
        _sym(tmp_path, lut_sealed, boxes={"CL1": (1e-12, 1e-11), "CL2": C_BOX})
    assert dict(e.value.record.detail)["reason"] == "tied_orbit_bounds_differ"


def test_bounds_differ_accepted_when_untied(tmp_path, lut_sealed):
    """비대칭 상자를 선언한 원소는 untie 로 풀면 받는다(3.24 2)."""
    case = _sym(tmp_path, lut_sealed, boxes={"CL1": C_BOX, "CL2": (1e-13, 1e-10)}, untie=("CL2",))
    assert case.untie == ("CL2",)
    d = case.sctx.domain
    caps = {v.component: (v.lo, v.hi) for v in d.variables if v.component[0] == "capacitance"}
    assert set(caps) == {("capacitance", "CL1"), ("capacitance", "CL2")}


def test_untie_unknown_element_rejected(tmp_path, lut_sealed):
    case = _sym(tmp_path, lut_sealed)
    with pytest.raises(SchemaRejectedError) as e:
        _domain(case, ("Nope",))
    det = dict(e.value.record.detail)
    assert (det["gate"], det["reason"]) == ("search_domain", "untie_element_unknown")


def test_untie_trivial_orbit_rejected(tmp_path, lut_sealed):
    """M5(꼬리)는 궤도 단일 -> untie_orbit_trivial."""
    case = _sym(tmp_path, lut_sealed)
    with pytest.raises(SchemaRejectedError) as e:
        _domain(case, ("M5",))
    det = dict(e.value.record.detail)
    assert (det["gate"], det["reason"]) == ("search_domain", "untie_orbit_trivial")


def test_orbit_ties_direct_rejections(tmp_path, lut_sealed):
    case = _sym(tmp_path, lut_sealed)
    comps = case.dc.schema.components
    for bad, reason in ((("Nope",), "untie_element_unknown"), (("M5",), "untie_orbit_trivial")):
        with pytest.raises(SchemaRejectedError) as e:
            orbit_ties(case.dc, comps, bad)
        assert dict(e.value.record.detail)["reason"] == reason


# ---------------------------------------------------------------- 풀기 (3.24 5·7 (d))

def test_untie_member_unties_whole_orbit_increases_variables(tmp_path, lut_sealed):
    """M4(구성원) 하나만 적어도 궤도 {M3, M4} 전체가 풀린다: 전류 변수 +1, L 칸 MOS +1. 다른 궤도(CL·o)는 그대로 묶임."""
    case = _sym(tmp_path, lut_sealed)
    d0 = _domain(case)
    d1 = _domain(case, ("M4",))
    assert len(d1.variables) == len(d0.variables) + 1
    assert len(d1.l_cells) == len(d0.l_cells) + 1
    assert {("current", "M3"), ("current", "M4")} <= {v.component for v in d1.variables}
    assert tie_groups(d1.ties) == {g for g in tie_groups(d0.ties) if not any(c[1] in ("M3", "M4") for c in g)}


def test_spec_untie_orbits_feeds_search_context(tmp_path, lut_sealed):
    """spec human.search.untie_orbits = {M3: {source}} -> build_search_context 의 정의역도 풀린다(3.24 5)."""
    tied = _sym(tmp_path / "t", lut_sealed)
    untied = _sym(tmp_path / "u", lut_sealed, untie=("M3",))
    assert untied.untie == ("M3",)
    assert len(untied.sctx.domain.variables) == len(tied.sctx.domain.variables) + 1
    assert not any(any(c[1] in ("M3", "M4") for c in g) for g in tie_groups(untied.sctx.domain.ties))


def test_untied_members_move_separately(tmp_path, lut_sealed):
    """3.24 7 (d): 푼 궤도의 두 구성원은 따로 값을 받는다 -- 평가 θ 에 서로 다른 값이 그대로 남는다."""
    from gmid_engine.search import evaluate

    from .canon_cases import mid_theta
    case = _sym(tmp_path, lut_sealed, untie=("M3",))
    th, cells = mid_theta(case.sctx.domain)
    th[("current", "M4")] = th[("current", "M3")] * 1.5
    r = evaluate(case.sctx, th, cells)
    got = dict(r.theta)
    assert got[("current", "M4")] == th[("current", "M3")] * 1.5
    assert got[("current", "M3")] == th[("current", "M3")]


# ---------------------------------------------------------------- 이름 치환 (3.24 7 (g))

@pytest.mark.parametrize("seed", [1, 2])
def test_renaming_transports_tie_groups(tmp_path, lut_sealed, seed):
    import random
    base = _sym(tmp_path / "a", lut_sealed)
    names = ["M1", "M2", "M3", "M4", "M5", "CL1", "CL2", "inp", "inn", "o1", "o2", "t", "vb", "pb"]
    new = ["q%02d" % i for i in range(len(names))]
    random.Random(seed).shuffle(new)
    sig = dict(zip(names, new))
    doc = rename_doc(sym_doc(), sig, "hand_sym_canon_r%d" % seed)
    case = make_case(tmp_path / "b", doc, lut_sealed, elements=tuple((sig[n], k, v) for n, k, v in SYM_ELEMENTS),
                     boxes={sig["CL1"]: C_BOX, sig["CL2"]: C_BOX})
    moved = {frozenset((k, sig.get(n, n)) for k, n in g) for g in tie_groups(base.sctx.domain.ties)}
    assert tie_groups(case.sctx.domain.ties) == moved
    assert len(case.sctx.domain.variables) == len(base.sctx.domain.variables)


# ---------------------------------------------------------------- [사용자 결정 2026-10-08 '대칭 묶음 방식: b'] (U2 구현 69679f7 -- 3.24 2·9 (h)(i))
# (b) = 2단자 수동소자는 방향 없음(자기동형이 끝을 맞바꿔도 된다), 묶음 값은 같고, 끝이 뒤집혀 대응하는 원소의 가지 전류는 부호 −1.
# oracle: (a) 구성 -- 끝을 뒤집어 그린 사본과 원본은 같은 무향 그래프라 궤도·차원·묶음이 같아야 한다; 거울 대칭에서 vdd→o1 저항 전류와
# o2→vdd 저항 전류는 크기가 같고 방향이 반대(KCL·거울 대칭). (d) 사용자 결정 문장.

def _rload(flip):
    """저항 부하 차동단: R1 (vdd -> o1), R2 (vdd -> o2) 또는 flip 이면 R2 (o2 -> vdd) 로 끝을 뒤집어 그림. vb: M5 gate(선언)."""
    from .conftest import mos, topo
    return topo("hand_rload" + ("_flip" if flip else ""),
                [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"), mos("M5", "nmos", "t", "vb", "gnd")],
                {"inp": ("input", "a"), "inn": ("input", "a"), "o1": ("output", "b"), "o2": ("output", "b")},
                passives=[two("R1", "resistor", "vdd", "o1"),
                          two("R2", "resistor", "o2", "vdd") if flip else two("R2", "resistor", "vdd", "o2")],
                bias=["vb"])


R_ELEMENTS = (("R1", "resistor", None), ("R2", "resistor", None))
R_BOXES = {"R1": (1e3, 1e6), "R2": (1e3, 1e6)}


def _dimension(domain):
    """탐색 차원 = 정의역 변수 + L 칸 대표 MOS(3.24 4)."""
    return len(domain.variables) + len(domain.l_cells)


def test_b_reversed_resistor_same_ties_as_drawn_alike(tmp_path, lut_sealed):
    """(b): R2 를 뒤집어 그려도 R1·R2 같은 궤도, 묶음 그룹(저항 값)·차원이 같게 그린 회로와 같다(무향)."""
    same = make_case(tmp_path / "s", _rload(False), lut_sealed, elements=R_ELEMENTS, boxes=R_BOXES)
    flip = make_case(tmp_path / "f", _rload(True), lut_sealed, elements=R_ELEMENTS, boxes=R_BOXES)
    assert frozenset({("resistance", "R1"), ("resistance", "R2")}) in tie_groups(same.sctx.domain.ties)   # 대조(현재도 통과)
    orb = dict(flip.dc.base.column("device", "dc_orbit"))
    assert orb["R1"] == orb["R2"] and orb["M1"] == orb["M2"]
    assert frozenset({("resistance", "R1"), ("resistance", "R2")}) in tie_groups(flip.sctx.domain.ties)
    assert _dimension(flip.sctx.domain) == _dimension(same.sctx.domain)


def test_b_reversed_resistor_current_tie_sign_minus_one(tmp_path, lut_sealed):
    """(b) '묶음 값은 같고 가지 전류는 부호 −1': 뒤집어 그린 R2 의 θ 전류는 R1 의 θ 전류와 묶이되 평가 θ 에서 −1 배(부호만 다름).
    저항 값(resistance)은 같은 값. 거울 대칭에서 vdd→o1 전류 = −(o2→vdd 전류)(구성)."""
    from gmid_engine.search import evaluate

    from .canon_cases import mid_theta
    flip = make_case(tmp_path, _rload(True), lut_sealed, elements=R_ELEMENTS, boxes=R_BOXES)
    comps = set(flip.dc.schema.components)
    assert {("current", "R1"), ("current", "R2")} <= comps                       # 입력 확인(현재 스키마)
    assert frozenset({("current", "R1"), ("current", "R2")}) in tie_groups(flip.sctx.domain.ties)
    th, cells = mid_theta(flip.sctx.domain)
    got = dict(evaluate(flip.sctx, th, cells).theta)
    assert got[("current", "R2")] == -got[("current", "R1")]
    assert got[("resistance", "R2")] == got[("resistance", "R1")]


def test_b_pilot_current_reuse_r1_r2_tied(tmp_path, lut_sealed):
    """파일럿 current_reuse_telescopic_ota(R1 (Vom -> Voc)·R2 (Voc -> Vop) 끝이 뒤집혀 그려짐): (b) 에서는 R1·R2 같은 궤도이고 묶음이 서서
    차원 = R2 를 뒤집은 사본의 차원(search CONTRACT 3.24 8 실측 107 -> 73; 숫자 대신 사본과의 같음으로 본다 -- 무향이라 같은 그래프)."""
    from .canon_cases import build_library_case, flip_terminals, library_doc
    raw, spec = library_doc("current_reuse_telescopic_ota")
    orig = build_library_case(tmp_path / "o", raw, spec, lut_sealed)
    flipped = build_library_case(tmp_path / "f", flip_terminals(raw, "R2"), spec, lut_sealed)
    assert flipped.domain.ties                                                     # 전제(현재 코드도 통과)
    assert _dimension(flipped.domain) < len(flipped.dc.schema.components)
    orb = dict(orig.dc.base.column("device", "dc_orbit"))
    assert orb["R1"] == orb["R2"]
    assert orig.domain.ties
    assert _dimension(orig.domain) == _dimension(flipped.domain)
    assert len(tie_groups(orig.domain.ties)) == len(tie_groups(flipped.domain.ties))
