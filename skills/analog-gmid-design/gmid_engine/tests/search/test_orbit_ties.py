"""search CONTRACT 3.24 [r12] `orbit_ties(dc_ctx, components, untied) -> (대표 성분 tuple, ties)` + 3.7 [r12] `search_domain(..., untie)` 묶음.
[U17 ①-b] 첫 인자 = 필드 질의가 되는 스냅샷(`dc.base`); 정의역은 블록 필드 `graph/kernel: search_domain`(conftest `domain_of`).

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
from .conftest import domain_of  # [U17 ①-b] graph/kernel: search_domain 필드 읽기
from .conftest import schema_of  # [U17 ①-b] graph/kernel 필드 읽기
from .conftest import SRC, two

BOXES = {"CL1": C_BOX, "CL2": C_BOX}


def _sym(tmp, lut, **kw):
    kw.setdefault("boxes", BOXES)
    return make_case(tmp, sym_doc(), lut, elements=SYM_ELEMENTS, **kw)


def _domain(case, untie=()):
    return domain_of(case.dc, SearchSettings(600.0, 40, None, SRC), case.pdk, case.spec_bounds, untie=untie)


def _members(ties):
    return {m for _, ms in ties for m in ms}


# ---------------------------------------------------------------- 묶음 = 구성 자기동형 짝

def test_symmetric_pairs_tied_as_constructed(tmp_path, lut_sealed):
    case = _sym(tmp_path, lut_sealed)
    comps = schema_of(case.dc).components
    want = expected_sym_groups(comps)
    assert want                                                          # 공허한 비교 아님(L·전류·y·C 짝)
    assert tie_groups(case.sctx.domain.ties) == want
    reps, ties = orbit_ties(case.dc.base, comps, ())
    assert tie_groups(ties) == want


def test_variables_plus_tied_equal_schema_components(tmp_path, lut_sealed):
    """3.24 7 (a): L 밖 성분 = 변수 ⊔ 묶인 L 밖 구성원, L = l_cells 대표 MOS ⊔ 묶인 L 구성원(서로소)."""
    case = _sym(tmp_path, lut_sealed)
    d = case.sctx.domain
    comps = schema_of(case.dc).components
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
    comps = schema_of(case.dc).components
    reps, ties = orbit_ties(case.dc.base, comps, ())
    assert sorted(reps) == sorted(set(comps) - _members(ties))


def test_asymmetric_circuit_no_ties(tmp_path, lut_sealed):
    """3.24 7 (e): 단일 종단 회로 C -- 궤도 모두 단일 -> ties == (), 변수 = L 밖 스키마 성분 전부."""
    case = make_case(tmp_path, asym_doc(), lut_sealed)
    d = case.sctx.domain
    assert d.ties == ()
    comps = schema_of(case.dc).components
    assert sorted(v.component for v in d.variables) == sorted(c for c in comps if c[0] != "L")
    assert sorted(m for m, _ in d.l_cells) == sorted(c[1] for c in comps if c[0] == "L")
    reps, ties = orbit_ties(case.dc.base, comps, ())
    assert ties == () and sorted(reps) == sorted(comps)


def test_dc_orbit_pairs_follow_construction(tmp_path, lut_sealed):
    """입력 확인: 묶음의 근거인 궤도(graph/s1 orbits -- [U17 ①-d] 옛 sizing dc_orbit 대체, 40 §2.4.8)가 σ 짝에서 같고 고정점끼리 다르다."""
    case = _sym(tmp_path, lut_sealed)
    orb = dict(case.dc.base.value("graph", "s1", "orbits").devices)
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
    comps = schema_of(case.dc).components
    for bad, reason in ((("Nope",), "untie_element_unknown"), (("M5",), "untie_orbit_trivial")):
        with pytest.raises(SchemaRejectedError) as e:
            orbit_ties(case.dc.base, comps, bad)
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
                {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"),               # [IT-1 DEC-106]
                 "o1": ("output", "b"), "o2": ("output", "b")},
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
    orb = dict(flip.dc.base.value("graph", "s1", "orbits").devices)
    assert orb["R1"] == orb["R2"] and orb["M1"] == orb["M2"]
    assert frozenset({("resistance", "R1"), ("resistance", "R2")}) in tie_groups(flip.sctx.domain.ties)
    assert _dimension(flip.sctx.domain) == _dimension(same.sctx.domain)


def test_b_reversed_resistor_current_tie_sign_minus_one(tmp_path, lut_sealed):
    """(b) '묶음 값은 같고 가지 전류는 부호 −1': 뒤집어 그린 R2 의 θ 전류는 R1 의 θ 전류와 묶이되 평가 θ 에서 −1 배(부호만 다름).
    저항 값(resistance)은 같은 값. 거울 대칭에서 vdd→o1 전류 = −(o2→vdd 전류)(구성)."""
    from gmid_engine.search import evaluate

    from .canon_cases import mid_theta
    flip = make_case(tmp_path, _rload(True), lut_sealed, elements=R_ELEMENTS, boxes=R_BOXES)
    comps = set(schema_of(flip.dc).components)
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
    # [U8 2026-10-09] 잡음 제약(noise_out_int_vrms)은 잡음 LUT 를 요구한다(search CONTRACT 11절 noise_lut_missing) -- 이 test 는 궤도 묶음만 보므로
    # 잡음 r1 이 없는 toy LUT(lut_sealed)에 맞춰 잡음 제약만 뺀다(정의역·묶음은 제약과 무관)
    # [U13 후속 2026-10-09] offset 제약(offset_in_sigma_mv·offset_excess)도 mismatch r1 을 요구한다(search CONTRACT 11절 mismatch_lut_missing,
    # fail-closed) -- toy LUT 는 mismatch r1 도 없으므로 같은 이유로 그 두 제약과, 값을 그 제약에서 가져오는(value_from_constraint) 제약을 뺀다
    # (궤도 묶음과 무관)
    offset = ("offset_in_sigma_mv", "offset_excess")
    spec["human"]["constraints"] = [c for c in spec["human"]["constraints"]
                                    if not str(c.get("metric", "")).startswith("noise_") and c.get("metric") not in offset
                                    and c.get("value_from_constraint") not in offset]
    orig = build_library_case(tmp_path / "o", raw, spec, lut_sealed)
    flipped = build_library_case(tmp_path / "f", flip_terminals(raw, "R2"), spec, lut_sealed)
    assert flipped.domain.ties                                                     # 전제(현재 코드도 통과)
    assert _dimension(flipped.domain) < len(schema_of(flipped.dc).components)
    orb = dict(orig.dc.base.value("graph", "s1", "orbits").devices)
    assert orb["R1"] == orb["R2"]
    assert orig.domain.ties
    assert _dimension(orig.domain) == _dimension(flipped.domain)
    assert len(tie_groups(orig.domain.ties)) == len(tie_groups(flipped.domain.ties))


# ---------------------------------------------------------------- [U17 ①-d] 설계 40 §6-8 MOS d/s 맞바꿈 (D-3 비트 동일 -- 대칭 결과까지)
# 범위 결정(사용자 결정 2026-10-13 "1은 권고", (라)) 원문 요지(오케스트레이터 전달): "topology d/s 표기 = 물리 방향 선언. design 40 §6-8 D-3 비트 동일은
# **대칭 결과(궤도·정준 위치·dc_colour·전류 부호)까지만**, 사이징 결과(writer 계획·θ 스키마·ties)는 선언 방향을 따름. 틀린 선언은 봉인 7(VDS−VDsat ≥ tol)이
# 거부." -> 옛 판정 'd/s 뒤집기 전후 SearchDomain.ties 가 같다'(사이징 결과)는 삭제하고 대칭 결과만 본다(봉인 7 거부는
# tests/sizing/test_block_columns.py::test_reversed_ds_declaration_rejected_by_seal7).
# 전류 부호(graph/s1 current_symmetry)는 '표기된 drain 이 상의 표기된 drain 으로 가는가'(§6-8) 기준이라 표기를 뒤집은 소자는 기준 방향이 바뀐다.
# 그래서 비트 동일의 뜻 = 뒤집은 집합 F 에 대해 (원소, 상, 부호) 행이 부호 × f(원소) × f(상)(f = F 에 들면 −1)으로 옮겨진 것과 같다(손 유도: 기준 방향
# 하나를 바꾸면 그 원소가 낀 관계 I(γe) = σ·I(e) 의 σ 가 한 번 뒤집힌다). 행은 '움직이거나 방향을 뒤집는 원소만' 적히므로 그 규칙으로 정규화해 비교한다.
# 뒤집기 대상 = gate 가 drain·source 어느 쪽도 아닌 MOS(SYM 의 다섯 MOS 모두).

def _flip_ds(doc, names, new_name):
    import json
    d = json.loads(json.dumps(doc))
    for e in d["netlist"]:
        if e["name"] in names:
            e["drain"], e["source"] = e["source"], e["drain"]
    d["topology_name"] = new_name
    return d


def _sign_rows(dc, flipped=()):
    """current_symmetry 생성자 행을 뒤집은 집합 기준으로 옮겨 정규화: {(원소, 상, 부호')}(부호' = 부호 × f(원소) × f(상)), 고정·부호 +1 행은 뺀다."""
    f = {n: -1 for n in flipped}
    out = []
    for g in dc.base.value("graph", "s1", "current_symmetry").generators:
        rows = {(e, i, s * f.get(e, 1) * f.get(i, 1)) for e, i, s in g}
        out.append(frozenset(r for r in rows if r[0] != r[1] or r[2] == -1))
    return sorted(out, key=sorted)


def _s1_case(tmp, doc):
    """doc 을 S1 까지만 지은 case: SimpleNamespace(dc = SimpleNamespace(base = S1 스냅샷)) -- 대칭 필드(orbits·dc_colour·current_symmetry)는 S1 필드."""
    import json
    from pathlib import Path
    from types import SimpleNamespace
    from gmid_engine.authoring import load_topology
    from gmid_engine.graph import build_s1
    from gmid_engine.search import open_run
    from .canon_cases import SUPPLIES
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    tp = tmp / (doc["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    donors, counters = open_run()
    s1 = build_s1(load_topology(str(tp)), dict(SUPPLIES), donors=donors, counters=counters)
    return SimpleNamespace(dc=SimpleNamespace(base=s1), td=None)


@pytest.mark.parametrize("names", [("M1",), ("M3",), ("M5",), ("M1", "M2", "M3", "M4", "M5")])
def test_ds_flip_symmetry_bit_identical(names, tmp_path, lut_sealed):
    base = make_case(tmp_path / "b", sym_doc(), lut_sealed, elements=SYM_ELEMENTS, boxes=BOXES, build_sctx=False)
    # [IT-1 K-3 ext, O-84] 뒤집은 쪽은 S1 까지만 짓는다: d/s 표기 = 물리 방향 선언(사용자 결정 2026-10-13 (라), design 40 §6-8)이라 뒤집은
    # 선언은 물리적으로 다른 선언이고, 커널 컨텍스트(S0)는 입력 포트 뿌리 둘 이상으로 정지한다(올바른 fail-closed). 대칭 단언 6개는 그대로.
    flip = _s1_case(tmp_path / "f", _flip_ds(sym_doc(), names, "hand_sym_canon_ds"))
    orb = dict(base.dc.base.value("graph", "s1", "orbits").devices)
    assert orb["M1"] == orb["M2"] and orb["M3"] == orb["M4"]                # 공허한 비교 아님(비자명 궤도)
    assert dict(flip.dc.base.value("graph", "s1", "orbits").devices) == orb
    assert dict(flip.dc.base.value("graph", "s1", "orbits").nodes) == dict(base.dc.base.value("graph", "s1", "orbits").nodes)
    assert dict(flip.dc.base.column("device", "dc_colour")) == dict(base.dc.base.column("device", "dc_colour"))
    assert dict(flip.dc.base.column("node", "dc_colour")) == dict(base.dc.base.column("node", "dc_colour"))
    assert _sign_rows(flip.dc, names) == _sign_rows(base.dc)


def test_ds_flip_m1_kernel_context_builds_one_input_point(tmp_path, lut_sealed):
    """[IT-1 DEC-106] M1 의 d/s 를 뒤집은 선언: 입력 포트 둘(p inp, n inn)이 한 입력 점 P 라 커널 컨텍스트(S0)는 정지하지 않는다(옛
    input_port_multiple_roots 삭제). (손) 뒤집은 G_vgs: P-o1(M1), P-t(M2) -> 성분 {P,o1,t} 에 F 없음 -> W4 뿌리 = 입력 점, 두 포트 모두 input_point.
    물리적으로 틀린 선언은 봉인 7 이 거부한다(tests/sizing/test_block_columns.py::test_reversed_ds_declaration_rejected_by_seal7)."""
    case = make_case(tmp_path / "f", _flip_ds(sym_doc(), ("M1",), "hand_sym_canon_ds"), lut_sealed, elements=SYM_ELEMENTS,
                     boxes=BOXES, build_sctx=False)
    nw = dict(case.dc.base.column("node", "dc_writer"))
    assert [(nw[x].tier, nw[x].relation, nw[x].y_key) for x in ("inp", "inn")] == [("W4", "input_point", "inp")] * 2


# ---------------------------------------------------------------- [IT-1 T-1f] 입력 점 + 자기동형 궤도 묶음 (이중 차감 0)

def test_it1_t1f_input_point_with_orbit_ties_no_double_subtraction(tmp_path, lut_sealed):
    """T-1f (손): 대칭 차동 toy(sym_doc: p inp, n inn). (1) 입력 점 규칙: y 성분 = 입력 점 하나(inp)와 출력 o1·o2 = 3 (n 포트 inn 의 y 키 없음).
    ln_idu 성분 3 = 입력쌍 트리 하나·꼬리 M5·부하쌍 트리 하나(평행 종속 둘은 θ 성분이 아니다). (2) 자기동형 σ 의 짝: y 에서는 (o1, o2) 뿐 --
    (inp, inn) 짝은 inn 이 스키마에 없어 묶음 대상이 아니다. domain.ties = σ 짝(`expected_sym_groups`, 구성) 그대로. (3) 이중 차감 0: y 성분 3 =
    정의역 변수 y 2(inp, 궤도 대표 하나) + 묶인 구성원 y 1 -- 입력 점 병합과 궤도 묶음이 같은 성분을 두 번 줄이지 않는다."""
    import collections
    case = _sym(tmp_path, lut_sealed)
    d = case.sctx.domain
    comps = schema_of(case.dc).components
    kinds = collections.Counter(k for k, _ in comps)
    assert {n for k, n in comps if k == "y"} == {"inp", "o1", "o2"}
    assert kinds["ln_idu"] == 3
    want = expected_sym_groups(comps)
    assert frozenset({("y", "o1"), ("y", "o2")}) in want
    assert not any(("y", "inp") in g or ("y", "inn") in g for g in want)
    assert tie_groups(d.ties) == want
    var_y = [v.component for v in d.variables if v.component[0] == "y"]
    tied_y = [m for _rep, ms in d.ties for m in ms if m[0] == "y"]
    assert ("y", "inp") in var_y
    assert (len(var_y), len(tied_y), len(var_y) + len(tied_y)) == (2, 1, 3)
    # 손 유도 리터럴(interface T-1f): θ 성분 15 = L 5 + 커패시터 2 + 전류 2 + ln_idu 3 + y 3, 묶인 구성원 5, 정의역 변수 7(L 제외).
    # 구조 rank·DOF(= 변수 수 - 구조 rank = 12, 커패시터 없는 toy)는 tests/pipeline/test_stage_b.py::test_it1_t1f_structural_dof_of_symmetric_pair.
    assert dict(collections.Counter(k for k, _ in comps)) == {"L": 5, "capacitance": 2, "current": 2, "ln_idu": 3, "y": 3}
    assert len(comps) == 15
    assert len(_members(d.ties)) == 5
    assert len(d.variables) == 7
