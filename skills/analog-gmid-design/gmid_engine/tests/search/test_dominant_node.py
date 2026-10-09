"""search/dominant_node.py -- `dominant_node(view) -> DominantNode(nets, rule)` (설계 41 §6.3 '주극점 노드(구조로 결정, N3)', D-DN).

oracle (d) 설계 41 §6.3 규칙 문장 + (a) 손 회로 구조(어느 넷이 Miller 앞 노드·출력 포트인지는 회로 구성으로 정해진다):
- Miller (2) 루프가 있으면 그 수동소자 구간이 잇는 두 노드 중 앞 노드(BFS 거리 작은 쪽).
- Miller 루프가 없으면 출력 포트 노드.
- 출력 포트가 낮은 임피던스(팔로워 소스)면: 설계 41 §6.3 은 '등급이 높음이 아닌 노드는 후보에서 뺀다'까지만 정한다. CONTRACT U13 은 버퍼 앞 마지막 이득 블록
  노드(`last_gain_block_node`)를 쓴다고 주장한다(설계 공백) -- 아래 test 는 그 주장을 확인한다.
매크로 모델을 쓰지 않는 구조 판정이므로(N3) 매크로 목표가 없어도 같은 답이어야 한다.
"""
import pytest

from gmid_engine.search import DominantNode, dominant_node

from .u13_hand import cs_chain, cs_follower, miller_two_stage, toy_case, transfer_view

TARGETS = (("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0))
CAPS2 = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12))


def _view(doc, elements, constraints=TARGETS):
    return transfer_view(toy_case(doc, elements=elements, constraints=constraints).s1v)


def test_no_miller_dominant_is_output_port():
    got = dominant_node(_view(cs_chain(2), CAPS2))
    assert isinstance(got, DominantNode)
    assert (got.nets, got.rule) == (("out",), "output_port_node")


def test_miller_dominant_is_front_node():
    got = dominant_node(_view(miller_two_stage(), (("Cc", "capacitor", 1e-12), ("CL", "capacitor", 1e-12))))
    assert (got.nets, got.rule) == (("n1",), "miller_front_node")


def test_low_impedance_output_uses_last_gain_block_node():
    # CONTRACT 주장(설계 공백): 팔로워 출력(out, 낮은 임피던스)은 후보가 아니다 -> 버퍼 앞 마지막 이득 블록 출력 n1
    got = dominant_node(_view(cs_follower(), (("CL", "capacitor", 1e-12),)))
    assert "out" not in got.nets
    assert (got.nets, got.rule) == (("n1",), "last_gain_block_node")


def test_structural_rule_does_not_depend_on_macro_targets():
    # N3: 주극점 노드는 구조로만 정한다 -- 보상 목표가 없어도 같은 답
    a = dominant_node(_view(miller_two_stage(), (("Cc", "capacitor", 1e-12), ("CL", "capacitor", 1e-12))))
    b = dominant_node(_view(miller_two_stage(), (("Cc", "capacitor", 1e-12), ("CL", "capacitor", 1e-12)), constraints=()))
    assert (a.nets, a.rule) == (b.nets, b.rule)


@pytest.mark.parametrize("seed_map", [{"n1": "zz_mid", "out": "aa_o", "in": "qq_i", "MN1": "Q9", "MN2": "Q0",
                                       "MP1": "Q5", "MP2": "Q1", "C1": "CX", "C2": "CA", "pb1": "bb2", "pb2": "bb1"}])
def test_name_bijection_maps_dominant_net(seed_map):
    # 이름 전단사: 넷·소자 이름만 바꾼 회로의 답 = 원래 답의 이름을 바꾼 것
    ren = cs_chain(2, name="u13cs2r", ren=seed_map)
    els = (("CX", "capacitor", 1e-12), ("CA", "capacitor", 1e-12))
    got = dominant_node(_view(ren, els))
    assert (got.nets, got.rule) == ((seed_map["out"],), "output_port_node")
