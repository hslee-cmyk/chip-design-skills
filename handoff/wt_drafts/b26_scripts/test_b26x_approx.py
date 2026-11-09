"""B26-1 v4 추가 계약(E1·E3·E4·E5·7(c))의 b1 근사 -- 변이 판정 측정 전용(scratch, 저장소 test 아님).

b1은 레일을 이름 집합(SD _RAIL_NETS = vdd/gnd/vss, SR 대소문자 6개)으로 판정하므로, card 계약의 선언 레일
`rail_hi`/`rail_lo`를 여기서는 `vdd`/`gnd`로 둔다(review2 §3 근사와 같은 가정). head 계약은 `rails=`를 넘기지만
b1 함수에는 그 인자가 없어 뺐다. 기대값은 card 계약 7(e)·4·14·7(a)·7(c) 문장대로 손으로 적은 값이다.
"""
import inspect
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import stick_diagram as sd  # noqa: E402
import sizing_recipe as sr  # noqa: E402

T = sd.Transistor
FIELDS = ("vds_match_vgs_of", "budget_reference_device", "fold_group")


def _three(res):
    out = {}
    for n, p in res["device_roles_proposals"].items():
        q = {f: p[f] for f in FIELDS if f in p}
        if q:
            out[n] = q
    return out


def _e1_circuit():
    ts = [
        # (i) vds_match_vgs_of
        T("Qy", "nmos", source="gnd", drain="n_out", gate="n_a"),     # 보상단 Y
        T("Qx", "nmos", source="gnd", drain="n_a", gate="n_in"),      # X: drain = Y.gate, source = Y.source
        T("Qz", "nmos", source="gnd", drain="n_o2", gate="vdd"),      # 보상단, gate = 레일
        T("Qw", "nmos", source="gnd", drain="vdd", gate="n_b"),       # drain = 레일(= Qz.gate)
        # (ii) budget_reference_device
        T("Mx", "nmos", source="gnd", drain="n_m", gate="n_g1"),      # 열린 단자 n_m 하나
        T("My", "pmos", source="vdd", drain="n_m", gate="n_g2"),      # 이웃 Y, source = 레일
        T("Nx", "nmos", source="n_q", drain="n_p", gate="n_g3"),      # 열린 단자 둘
        T("Ny", "pmos", source="vdd", drain="n_p", gate="n_g4"),
        T("Kx", "nmos", source="gnd", drain="n_r", gate="n_g5"),      # 이웃 source가 레일 아님 -> budget 없음
        T("Ky", "pmos", source="n_t", drain="n_r", gate="n_g6"),      # (iii) fold_group 양성 짝
        # (iii) fold_group 음성: X.drain = 레일(다른 부분 회로가 drain으로 쓰지 않는 레일 gnd -- Qw가 vdd를 drain으로 쓴다)
        T("Fx", "nmos", source="n_u", drain="gnd", gate="n_g7"),
        T("Fy", "pmos", source="n_v", drain="gnd", gate="n_g8"),
    ]
    roles = {"Qx": {"vertical_stack_id": "S1"}, "Qw": {"vertical_stack_id": "S2"},
             "Mx": {"vertical_stack_id": "S3"}, "My": {"vertical_stack_id": "S3b"},
             "Nx": {"vertical_stack_id": "S4"},
             "Kx": {"vertical_stack_id": "S5"}, "Ky": {"vertical_stack_id": "S6"},
             "Fx": {"vertical_stack_id": "S7"}, "Fy": {"vertical_stack_id": "S8"}}
    return ts, roles


def test_b26_e1_device_roles_rail_sites():
    ts, roles = _e1_circuit()
    res = sd.propose_device_roles_gap_fill(ts, roles, [], compensation_stage_devices=["Qy", "Qz"])
    assert _three(res) == {
        "Qx": {"vds_match_vgs_of": "Qy"},
        "Mx": {"budget_reference_device": "My"},
        "My": {"budget_reference_device": "Mx"},
        "Kx": {"fold_group": "n_r_fold"},
        "Ky": {"fold_group": "n_r_fold"},
    }


def test_b26_e3_default_constants():
    assert inspect.signature(sd.refine_differential_and_mirror_relations).parameters["max_iterations"].default == 5
    assert inspect.signature(sd.repair_matching_safety).parameters["max_iter"].default == 3
    assert inspect.signature(sd.run_full_circuit_audit).parameters["row_width_tol"].default == 1.5


def test_b26_e4_propose_gateless_direct():
    fx = [T("Ma", "pmos", source="vdd", drain="n1"), T("Mb", "nmos", source="gnd", drain="n1")]
    assert sd._propose_gm_id_roles(fx, (), (), (), (), ()) is None
    assert sd._propose_L_roles(fx, {}, (), (), (), (), ()) is None


def test_b26_e5_layer1_positive():
    ts = [T("Da", "nmos", source="n_tail", drain="o1", gate="i1"),
          T("Db", "nmos", source="n_tail", drain="o2", gate="i2"),
          T("Dt", "nmos", source="gnd", drain="n_tail", gate="vb")]
    mc_ = sd.find_matching_candidates(ts)
    assert {k: [t.name for t in v] for k, v in mc_["diff_pair"].items()} == {("nmos", "n_tail"): ["Da", "Db"]}
    assert {k: [t.name for t in v] for k, v in sd._diff_pair_layer1_groups(ts).items()} == {("nmos", "n_tail", None): ["Da", "Db"]}
    c = sd.find_differential_pair_candidates(ts)["candidates"]
    assert {"direction": "layer1_fallback", "position": None, "devices": ("Da", "Db"), "shared_source": "n_tail"} in c


def test_b26_7c_gate_on_rail_not_mirror():
    by = {n: T(n, k, source=s, drain=d, gate=g) for n, k, s, d, g in (
        ("Ma", "nmos", "gnd", "x1", "vdd"), ("Mb", "nmos", "gnd", "x2", "vdd"),
        ("Pc", "pmos", "vdd", "x3", "bp"), ("Pd", "pmos", "vdd", "x4", "bp"))}
    assert sr.true_current_mirror_groups(by) == [["Pc", "Pd"]]
