"""Phase 2 P9 계약: KCL 엣지 정의 한 곳(20260930-p9-kcl-edges, equivalence).

spec card `docs/02-design/specs/20260930-p9-kcl-edges.spec.md`의 영구 test 몫(계약 2, 3(b))만 판정한다.
계약 1·3(a)·5(a)(b)·6·7(AST 구조 판정)과 계약 4(DIFF-DUP·E-LIB·E-INST base = 병합본)는 auditor 측정이라 여기 두지 않는다
-- equivalence이므로 이 파일의 test는 base와 병합본 모두에서 PASS해야 한다.

판정 입력은 전부 합성 넷리스트다(소자 이름 `q..`, 넷 이름 `nx_..`(공유 내부 넷)·`nl_..`(한 번만 쓰는 끝 넷) -- 라이브러리 밖).
넷리스트 원소는 spec card 계약 2가 정한 `stick_diagram.Transistor(name=, kind=, source=, drain=)`(다른 필드 기본값)다.

oracle 대조(계획 N3.12.3):

* 모든 기대값 -- (a) 구성 입력: 넷리스트를 손으로 짜서 정답이 구성으로 정해진다. 규칙은 spec card 계약 2·3(b)
  문장 그대로다 -- 엣지 = (외부 공급이 없는 내부 넷을 정확히 두 소자가 source/drain으로 한 번씩 쓰면 KCL로 두 소자 전류가 같다
  -- 전하 보존) + (매칭 튜플 안의 이웃 소자 쌍). 그룹 = 엣지 그래프의 연결 성분, 대표 = 성분에서 netlist 순서가 가장 앞선 소자,
  구성원 = netlist 순서, dict 키 순서 = 대표의 netlist 순서, 엣지 없는 소자는 혼자 그룹.
  각 기대 리터럴 옆 주석에 어떤 넷·어떤 매칭 선언이 그 그룹/엣지를 만드는지 적는다.
* 두 피검 함수(`kcl_series_union`, `_kcl_and_matching_edges`)는 서로의 기대값으로 쓰지 않는다(V4 (1), design §6.2).
* 레일 이름 규칙은 계약으로 삼지 않는다(계약 5(c)): 레일 이름 넷(`gnd`)은 세 번 쓰는 입력 하나에만 나오고, 그 결과는
  3회 사용 규칙만으로 정해진다.
"""
import importlib
import inspect
import pathlib
import sys

import pytest

# contracts -> tests -> assets(A)
_ASSETS_DIR = pathlib.Path(__file__).resolve().parents[2]


def _sd():
    if str(_ASSETS_DIR) not in sys.path:
        sys.path.insert(0, str(_ASSETS_DIR))
    return importlib.import_module("stick_diagram")


def _net(*specs):
    """(name, kind, source, drain) 튜플들 -> Transistor 목록(spec card 계약 2의 키워드 생성)."""
    sd = _sd()
    return [sd.Transistor(name=n, kind=k, source=s, drain=d) for (n, k, s, d) in specs]


def _edge_set(edges):
    """정본 반환 `(a, b, kind, detail)` 목록 -> 순서 무관 집합(계약 3(b) '집합으로 판정').

    끝점 쌍도 순서 무관으로 본다(계약은 a·b의 방향을 정하지 않는다).
    """
    out = set()
    for e in edges:
        assert len(e) == 4, e
        a, b, kind, detail = e
        out.add((frozenset((a, b)), kind, detail))
    return out


_IS = "internal_series"
_MP = "declared_matching_pair"


# ---------------------------------------------------------------- 합성 입력(구성으로 정답이 정해진다)

def _chain_interleaved():
    # 사슬 qa1 -nx_1- qb2 -nx_2- qc3, 사이에 고립 소자 qz9. netlist 순서는 qb2, qz9, qa1, qc3로 섞는다
    # (대표가 사슬 가운데 소자 qb2가 되고, 구성원 순서가 이름순이 아니라 netlist 순서임을 드러내게).
    return _net(
        ("qb2", "nmos", "nx_1", "nx_2"),
        ("qz9", "pmos", "nl_z1", "nl_z2"),
        ("qa1", "nmos", "nl_a", "nx_1"),
        ("qc3", "nmos", "nx_2", "nl_c"),
    )


def _three_use():
    # nx_3을 세 소자가 쓴다 -> 2단자 넷이 아니므로 어떤 엣지도 없다.
    return _net(
        ("qa1", "nmos", "nx_3", "nl_1"),
        ("qb2", "nmos", "nx_3", "nl_2"),
        ("qc3", "pmos", "nl_3", "nx_3"),
    )


def _self_loop():
    # qa1의 source = drain = nx_5: 사용 2회지만 같은 소자 -> 엣지 아님. qb2는 끝 넷만.
    return _net(
        ("qa1", "nmos", "nx_5", "nx_5"),
        ("qb2", "pmos", "nl_1", "nl_2"),
    )


def _leaves3():
    # 넷을 공유하지 않는 세 소자(매칭 선언만으로 묶이는지 보는 입력).
    return _net(
        ("qa1", "nmos", "nl_a1", "nl_a2"),
        ("qb2", "nmos", "nl_b1", "nl_b2"),
        ("qc3", "nmos", "nl_c1", "nl_c2"),
    )


def _leaves4():
    return _net(
        ("qa1", "pmos", "nl_a1", "nl_a2"),
        ("qb2", "pmos", "nl_b1", "nl_b2"),
        ("qc3", "pmos", "nl_c1", "nl_c2"),
        ("qd4", "pmos", "nl_d1", "nl_d2"),
    )


def _rail_three_use():
    # 레일 이름 넷 gnd를 세 소자가 쓴다 -> 3회 사용 규칙만으로 엣지 없음(계약 5(c)).
    return _net(
        ("qa1", "nmos", "gnd", "nl_1"),
        ("qb2", "nmos", "gnd", "nl_2"),
        ("qc3", "nmos", "gnd", "nl_3"),
    )


def _mixed():
    # 두 가지(PMOS 위 / NMOS 아래) + 매칭으로만 묶이는 쌍, netlist 순서를 섞는다.
    #   nx_o1: qp1.drain, qn1.drain       -> qp1-qn1
    #   nx_t : qn2.drain, qn1.source      -> qn1-qn2
    #   nx_o2: qp2.drain, qn3.drain       -> qp2-qn3
    #   qx7·qy8: 끝 넷만(매칭 선언이 있으면 한 그룹)
    return _net(
        ("qn2", "nmos", "nl_g1", "nx_t"),
        ("qp2", "pmos", "nl_v2", "nx_o2"),
        ("qx7", "nmos", "nl_x1", "nl_x2"),
        ("qp1", "pmos", "nl_v1", "nx_o1"),
        ("qn1", "nmos", "nx_t", "nx_o1"),
        ("qn3", "nmos", "nl_g3", "nx_o2"),
        ("qy8", "pmos", "nl_y1", "nl_y2"),
    )


# (id, 넷리스트 생성기, matching_pairs, kcl_series_union 기대 list(items()), _kcl_and_matching_edges 기대 집합)
_CASES = [
    (
        "chain_interleaved",
        _chain_interleaved,
        [],
        # (a) nx_1: qa1-qb2, nx_2: qb2-qc3 -> {qb2, qa1, qc3}, 대표 = netlist 첫 qb2, 구성원 netlist 순서.
        # qz9는 엣지 없음 -> 혼자. 키 순서 = 대표 순서 qb2(0) < qz9(1).
        [("qb2", ["qb2", "qa1", "qc3"]), ("qz9", ["qz9"])],
        {(frozenset(("qa1", "qb2")), _IS, "nx_1"), (frozenset(("qb2", "qc3")), _IS, "nx_2")},
    ),
    (
        "three_use_net_not_merged",
        _three_use,
        [],
        # (a) nx_3 사용 3회 -> 엣지 없음, 모두 혼자.
        [("qa1", ["qa1"]), ("qb2", ["qb2"]), ("qc3", ["qc3"])],
        set(),
    ),
    (
        "source_equals_drain_not_merged",
        _self_loop,
        [],
        # (a) nx_5 사용 2회가 같은 소자 qa1 -> 엣지 없음.
        [("qa1", ["qa1"]), ("qb2", ["qb2"])],
        set(),
    ),
    (
        "matching_pair_without_shared_net",
        _leaves3,
        [("qa1", "qb2")],
        # (a) 넷 공유 없음, 매칭 선언 (qa1, qb2) 하나 -> {qa1, qb2}, qc3 혼자.
        [("qa1", ["qa1", "qb2"]), ("qc3", ["qc3"])],
        {(frozenset(("qa1", "qb2")), _MP, None)},
    ),
    (
        "matching_pair_reversed_order",
        _leaves3,
        [("qc3", "qa1")],
        # (a) 매칭을 netlist 역순으로 선언 -> 대표는 netlist 순서 첫 qa1(선언 첫 원소 qc3가 아니다).
        # qb2(1)는 혼자, 키 순서 qa1(0) < qb2(1).
        [("qa1", ["qa1", "qc3"]), ("qb2", ["qb2"])],
        {(frozenset(("qc3", "qa1")), _MP, None)},
    ),
    (
        "matching_triple_chains",
        _leaves4,
        [("qa1", "qc3", "qd4")],
        # (a) 세 소자 매칭 튜플 -> 이웃 쌍 (qa1,qc3)·(qc3,qd4) 사슬로 한 그룹. qb2 혼자.
        [("qa1", ["qa1", "qc3", "qd4"]), ("qb2", ["qb2"])],
        {(frozenset(("qa1", "qc3")), _MP, None), (frozenset(("qc3", "qd4")), _MP, None)},
    ),
    (
        "matching_triple_reversed_rep_last_declared",
        _leaves4,
        [("qd4", "qc3", "qb2")],
        # (a) 역순 세 소자 튜플 -> {qb2, qc3, qd4}, 대표 = netlist 첫 qb2(선언 마지막 원소). qa1 혼자가 먼저 키.
        [("qa1", ["qa1"]), ("qb2", ["qb2", "qc3", "qd4"])],
        {(frozenset(("qd4", "qc3")), _MP, None), (frozenset(("qc3", "qb2")), _MP, None)},
    ),
    (
        "rail_named_net_three_uses_not_merged",
        _rail_three_use,
        [],
        # (a) gnd 사용 3회 -> 3회 사용 규칙으로 엣지 없음(레일 이름 규칙에 기대지 않는다, 계약 5(c)).
        [("qa1", ["qa1"]), ("qb2", ["qb2"]), ("qc3", ["qc3"])],
        set(),
    ),
    (
        "mixed_no_matching",
        _mixed,
        [],
        # (a) nx_o1·nx_t -> {qn2, qp1, qn1}(대표 qn2), nx_o2 -> {qp2, qn3}(대표 qp2), qx7·qy8 혼자.
        # 키 순서 = 대표 netlist 위치 qn2(0) < qp2(1) < qx7(2) < qy8(6).
        [
            ("qn2", ["qn2", "qp1", "qn1"]),
            ("qp2", ["qp2", "qn3"]),
            ("qx7", ["qx7"]),
            ("qy8", ["qy8"]),
        ],
        {
            (frozenset(("qp1", "qn1")), _IS, "nx_o1"),
            (frozenset(("qn2", "qn1")), _IS, "nx_t"),
            (frozenset(("qp2", "qn3")), _IS, "nx_o2"),
        },
    ),
    (
        "mixed_matching_joins_isolated",
        _mixed,
        [("qy8", "qx7")],
        # (a) 위와 같고 매칭 (qy8, qx7)이 두 고립 소자를 묶는다 -> {qx7, qy8}, 대표 qx7(netlist 2).
        [
            ("qn2", ["qn2", "qp1", "qn1"]),
            ("qp2", ["qp2", "qn3"]),
            ("qx7", ["qx7", "qy8"]),
        ],
        {
            (frozenset(("qp1", "qn1")), _IS, "nx_o1"),
            (frozenset(("qn2", "qn1")), _IS, "nx_t"),
            (frozenset(("qp2", "qn3")), _IS, "nx_o2"),
            (frozenset(("qy8", "qx7")), _MP, None),
        },
    ),
    (
        "mixed_matching_joins_two_branches",
        _mixed,
        [("qn3", "qn1")],
        # (a) 매칭 (qn3, qn1)이 두 가지를 잇는다 -> {qn2, qp2, qp1, qn1, qn3} 한 그룹, 대표 qn2(netlist 0),
        # 구성원 netlist 순서 qn2, qp2, qp1, qn1, qn3. qx7·qy8 혼자.
        [
            ("qn2", ["qn2", "qp2", "qp1", "qn1", "qn3"]),
            ("qx7", ["qx7"]),
            ("qy8", ["qy8"]),
        ],
        {
            (frozenset(("qp1", "qn1")), _IS, "nx_o1"),
            (frozenset(("qn2", "qn1")), _IS, "nx_t"),
            (frozenset(("qp2", "qn3")), _IS, "nx_o2"),
            (frozenset(("qn3", "qn1")), _MP, None),
        },
    ),
]

_IDS = [c[0] for c in _CASES]


@pytest.mark.parametrize("case", _CASES, ids=_IDS)
def test_kcl_series_union_groups_on_synthetic_netlist(case):
    """계약 2: 그룹(연결 성분)·대표·구성원 순서·키 순서를 손 리터럴과 비교한다."""
    _id, make, pairs, expected_groups, _expected_edges = case
    result = _sd().kcl_series_union(make(), pairs)
    assert isinstance(result, dict)
    assert list(result.items()) == expected_groups


@pytest.mark.parametrize("case", _CASES, ids=_IDS)
def test_kcl_and_matching_edges_shape_on_synthetic_netlist(case):
    """계약 3(b): 정본 반환 `(a, b, kind, detail)`의 집합과 kind·detail 모양."""
    _id, make, pairs, _expected_groups, expected_edges = case
    edges = _sd()._kcl_and_matching_edges(make(), pairs)
    assert isinstance(edges, list)
    for e in edges:
        assert (e[2] == _IS and isinstance(e[3], str)) or (e[2] == _MP and e[3] is None), e
    assert _edge_set(edges) == expected_edges


def test_kcl_series_union_signature_unchanged():
    """계약 2: 시그니처 불변 -- (d) interface card 표 `def kcl_series_union(netlist: list, matching_pairs: list) -> dict`."""
    sig = inspect.signature(_sd().kcl_series_union)
    assert list(sig.parameters) == ["netlist", "matching_pairs"]
    for p in sig.parameters.values():
        assert p.default is inspect.Parameter.empty
        assert p.annotation in (list, "list")
    assert sig.return_annotation in (dict, "dict")


def test_kcl_and_matching_edges_signature_unchanged():
    """계약 3: 정본 시그니처 불변 -- (d) interface card 표 `def _kcl_and_matching_edges(transistors: list, matching_pairs: list) -> list`."""
    sig = inspect.signature(_sd()._kcl_and_matching_edges)
    assert list(sig.parameters) == ["transistors", "matching_pairs"]
    for p in sig.parameters.values():
        assert p.default is inspect.Parameter.empty
        assert p.annotation in (list, "list")
    assert sig.return_annotation in (list, "list")
