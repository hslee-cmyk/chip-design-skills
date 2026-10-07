"""`check_name_uniqueness(devices, passives, sources)` -- CONTRACT 3.8 (IC3, 이상원 포함). 반환은 SchemaHit tuple."""
from __future__ import annotations

from gmid_engine.authoring import DeviceDecl, PassiveDecl, SourceDecl, check_name_uniqueness


def D(name):
    return DeviceDecl(name, "nmos", "n_a", "n_b", "n_c")


def P(name):
    return PassiveDecl(name, "capacitor", ("n_a", "n_b"))


def S(name):
    return SourceDecl(name, "current_source", ("n_a", "n_c"))


def _hits(devs, pas, srcs):
    return check_name_uniqueness(tuple(devs), tuple(pas), tuple(srcs))


def test_unique_passes():
    assert _hits([D("Q1"), D("Q2")], [P("Ca")], [S("Ib")]) == ()


def test_empty_passes():
    assert _hits([], [], []) == ()


def test_duplicate_in_every_pairing():
    cases = [
        ([D("Q1"), D("Q1")], [], []),
        ([D("Q1")], [P("Q1")], []),
        ([D("Q1")], [], [S("Q1")]),
        ([], [P("Q1"), P("Q1")], []),
        ([], [P("Q1")], [S("Q1")]),
        ([], [], [S("Q1"), S("Q1")]),
    ]
    for devs, pas, srcs in cases:
        hits = _hits(devs, pas, srcs)
        assert [h.rule for h in hits] == ["name_duplicate"], (devs, pas, srcs)
        assert hits[0].elements == ("Q1",)


def test_duplicate_once_per_name():
    hits = _hits([D("Q1"), D("Q1"), D("Q2")], [P("Q1"), P("Q2")], [S("Q1")])
    assert sorted((h.rule, h.elements) for h in hits) == [("name_duplicate", ("Q1",)), ("name_duplicate", ("Q2",))]


def test_case_collision_group():
    hits = _hits([D("Qa")], [P("QA")], [S("qa")])
    assert [h.rule for h in hits] == ["name_case_collision"]
    assert hits[0].elements == ("QA", "Qa", "qa")


def test_case_collision_one_per_group():
    hits = _hits([D("Qa"), D("Rb")], [P("qa"), P("RB")], [])
    assert sorted((h.rule, h.elements) for h in hits) == [
        ("name_case_collision", ("Qa", "qa")), ("name_case_collision", ("RB", "Rb"))]


def test_casefold_not_lower():
    """casefold 기준: 'ß' 와 'ss' 는 casefold 가 같다."""
    hits = _hits([D("Qß")], [P("Qss")], [])
    assert [h.rule for h in hits] == ["name_case_collision"]
    assert hits[0].elements == tuple(sorted(("Qß", "Qss")))


def test_exact_duplicate_is_not_case_collision():
    hits = _hits([D("Q1"), D("Q1")], [], [])
    assert [h.rule for h in hits] == ["name_duplicate"]


def test_fixture_load(ah):
    from gmid_engine.authoring import load_topology
    exc, detail = ah.rejected(load_topology, str(ah.path("name_uniqueness__name_duplicate")))
    assert [(h.rule, h.elements) for h in detail["hits"]] == [("name_duplicate", ("Q4",))]
    exc, detail = ah.rejected(load_topology, str(ah.path("name_uniqueness__name_case_collision")))
    assert [(h.rule, h.elements) for h in detail["hits"]] == [("name_case_collision", ("Rf", "rf"))]


# ---------------------------------------------------------------------------------------------------------------
# net_case_collision -- CONTRACT 3.8 표 셋째 행 + 7절 [신규]. 넷 집합 = MOS d/g/s/선언 bulk ∪ 2단자 terminals ∪
# supply_nets ∪ port_nets, casefold 같고 글자 다른 묶음마다 hit 하나(elements = 그 넷 이름들). 원소 이름 공간과는 비교 안 함.
# ---------------------------------------------------------------------------------------------------------------
import json  # noqa: E402

from gmid_engine.authoring import load_topology  # noqa: E402

NE_ELEMENTS = {"name_uniqueness", "ports.port_net_unknown", "hidden_rails"}


def _net(devs=(), pas=(), srcs=(), supply=(), ports=()):
    return check_name_uniqueness(tuple(devs), tuple(pas), tuple(srcs), tuple(supply), tuple(ports))


def _one_net_hit(hits, names):
    assert [(h.rule, h.elements) for h in hits] == [("net_case_collision", tuple(sorted(names)))]
    for n in names:  # 7절: where 도 그 넷 이름들
        assert n in hits[0].where


def test_net_terminal_vs_terminal():
    devs = [DeviceDecl("Q1", "nmos", "n_x", "n_g", "n_s"), DeviceDecl("Q2", "nmos", "N_X", "n_g", "n_s")]
    _one_net_hit(_net(devs), ("N_X", "n_x"))


def test_net_mos_vs_two_terminal_and_bulk():
    devs = [DeviceDecl("Q1", "nmos", "n_d", "n_g", "n_s", "n_bulk")]
    _one_net_hit(_net(devs, [PassiveDecl("C1", "capacitor", ("N_BULK", "n_d"))]), ("N_BULK", "n_bulk"))
    _one_net_hit(_net(devs, (), [SourceDecl("I1", "current_source", ("n_D", "n_s"))]), ("n_D", "n_d"))


def test_net_terminal_vs_rail():
    devs = [DeviceDecl("Q1", "nmos", "n_d", "n_g", "rail_lo")]
    _one_net_hit(_net(devs, supply=("rail_lo", "RAIL_LO")), ("RAIL_LO", "rail_lo"))
    _one_net_hit(_net(devs, supply=("Rail_Lo",)), ("Rail_Lo", "rail_lo"))


def test_net_terminal_vs_port():
    devs = [DeviceDecl("Q1", "nmos", "n_out", "n_in", "n_s")]
    _one_net_hit(_net(devs, ports=("N_IN", "n_out")), ("N_IN", "n_in"))


def test_net_rail_vs_port():
    _one_net_hit(_net(supply=("rail_hi",), ports=("RAIL_HI",)), ("RAIL_HI", "rail_hi"))


def test_net_one_hit_per_group():
    devs = [DeviceDecl("Q1", "nmos", "n_a", "N_A", "N_a"), DeviceDecl("Q2", "nmos", "n_b", "N_B", "n_s")]
    hits = _net(devs)
    assert sorted((h.rule, h.elements) for h in hits) == [
        ("net_case_collision", ("N_A", "N_a", "n_a")), ("net_case_collision", ("N_B", "n_b"))]


def test_net_casefold_not_lower():
    devs = [DeviceDecl("Q1", "nmos", "n_ß", "n_ss", "n_s")]
    _one_net_hit(_net(devs), ("n_ss", "n_ß"))


def test_same_spelling_across_sources_is_not_collision():
    """같은 글자가 단자·레일·포트에 나오는 것은 정상(같은 넷)."""
    devs = [DeviceDecl("Q1", "nmos", "n_out", "n_in", "rail_lo")]
    assert _net(devs, [PassiveDecl("C1", "capacitor", ("n_out", "rail_lo"))], supply=("rail_lo",),
                ports=("n_in", "n_out")) == ()


def test_element_name_and_net_name_are_separate_spaces():
    """원소 이름과 넷 이름은 비교하지 않는다: casefold 같거나 글자까지 같아도 통과."""
    devs = [DeviceDecl("Q1", "nmos", "q1", "n_g", "n_s"), DeviceDecl("Nx", "nmos", "Nx", "NX2", "n_s")]
    pas = [PassiveDecl("Rload", "resistor", ("RLOAD", "n_s"))]
    assert _net(devs, pas, supply=("q1x",), ports=("rload_port",)) == ()


def test_three_arg_call_still_works_and_checks_terminal_nets():
    """7절: 추가 인자 기본값 () -- 기존 3인자 호출은 원소 이름 검사 + 단자 넷 검사."""
    assert check_name_uniqueness((D("Q1"),), (P("C1"),), (S("I1"),)) == ()
    hits = check_name_uniqueness((DeviceDecl("Q1", "nmos", "n_x", "n_g", "n_s"),),
                                 (PassiveDecl("C1", "capacitor", ("N_X", "n_s")),), ())
    _one_net_hit(hits, ("N_X", "n_x"))
    hits = check_name_uniqueness((D("Q1"), D("Q1")), (), ())
    assert [h.rule for h in hits] == ["name_duplicate"]


def test_element_and_net_violations_together():
    devs = [DeviceDecl("Qa", "nmos", "n_x", "n_g", "n_s"), DeviceDecl("QA", "nmos", "N_X", "n_g", "n_s")]
    assert sorted(h.rule for h in _net(devs)) == ["name_case_collision", "net_case_collision"]


# ---- load_topology 경유 (7절: gate name_uniqueness, rails·ports 거부돼도 넷 검사, 원소 거부면 전체 not_evaluated) ----

def _load_rejected(ah, tmp_path, doc):
    exc, detail = ah.rejected(load_topology, ah.write(tmp_path, doc))
    return detail


def _net_hit(detail):
    return next(h for h in detail["hits"] if h.rule == "net_case_collision")


def test_load_terminal_collision_single_hit(ah, tmp_path):
    d = ah.base()
    ah.dev(d, "Q1")["drain"] = "N_MID"     # 다른 소자의 n_mid 와 casefold 같음
    detail = _load_rejected(ah, tmp_path, d)
    assert [(h.rule, h.elements) for h in detail["hits"]] == [("net_case_collision", ("N_MID", "n_mid"))]
    assert detail["rejected_gates"] == ("name_uniqueness",)
    assert detail["not_evaluated"] == ()


def test_load_rail_variant_also_rail_not_connected(ah, tmp_path):
    d = ah.base()
    d["supply_nets"].append("RAIL_HI")
    detail = _load_rejected(ah, tmp_path, d)
    assert sorted(h.rule for h in detail["hits"]) == ["net_case_collision", "rail_not_connected"]
    assert _net_hit(detail).elements == ("RAIL_HI", "rail_hi")
    assert "name_uniqueness" in detail["rejected_gates"]


def test_load_port_variant_also_port_net_unknown(ah, tmp_path):
    d = ah.base()
    ah.dev(d, "Q1")["gate"] = "N_INP"        # 포트 키 n_inp 는 그대로
    d["ports"]["n_mid"] = {"direction": "input", "role": "aux_input"}   # 위반 없는 input 을 남겨 no_input_port 배제
    detail = _load_rejected(ah, tmp_path, d)
    assert sorted(h.rule for h in detail["hits"]) == ["net_case_collision", "port_net_unknown"]
    assert _net_hit(detail).elements == ("N_INP", "n_inp")
    assert set(detail["rejected_gates"]) == {"name_uniqueness", "ports"}


def test_load_net_check_runs_when_rails_rejected(ah, tmp_path):
    d = ah.base()
    d["supply_nets"] += ["rail_lo", "RAIL_AC"]       # supply_net_duplicate(rails 거부) + 대소문자 변형
    detail = _load_rejected(ah, tmp_path, d)
    rules = [h.rule for h in detail["hits"]]
    assert "supply_net_duplicate" in rules and "net_case_collision" in rules
    assert _net_hit(detail).elements == ("RAIL_AC", "rail_ac")
    assert set(detail["rejected_gates"]) == {"name_uniqueness", "rails"}
    assert "name_uniqueness" not in detail["not_evaluated"]


def test_load_net_check_runs_when_ports_rejected(ah, tmp_path):
    d = ah.base()
    d["ports"]["N_MID"] = {"direction": "sideways", "role": "aux"}   # ports 거부 + 포트 키가 단자 n_mid 의 변형
    detail = _load_rejected(ah, tmp_path, d)
    rules = [h.rule for h in detail["hits"]]
    assert "port_direction" in rules and "net_case_collision" in rules
    assert _net_hit(detail).elements == ("N_MID", "n_mid")
    assert {"name_uniqueness", "ports"} <= set(detail["rejected_gates"])
    assert "name_uniqueness" not in detail["not_evaluated"]


def test_load_net_check_skipped_when_element_rejected(ah, tmp_path):
    """원소 선언 하나라도 거부되면 name_uniqueness 전체(넷 검사 포함)가 not_evaluated."""
    d = ah.base()
    ah.dev(d, "Q1")["drain"] = "N_MID"
    ah.dev(d, "Q2")["w"] = 1.0                       # devices 거부
    detail = _load_rejected(ah, tmp_path, d)
    assert "net_case_collision" not in [h.rule for h in detail["hits"]]
    assert set(detail["not_evaluated"]) == NE_ELEMENTS


def test_load_element_name_equal_to_net_name_passes(ah, tmp_path):
    """넷 n_outp 를 원소 이름 Q3 과 casefold 같은 'q3' 로 바꿔도(단자·포트 전부) 통과 -- 다른 이름 공간."""
    d = json.loads(json.dumps(ah.base()).replace('"n_outp"', '"q3"'))
    assert "q3" in d["ports"]
    load_topology(ah.write(tmp_path, d))
