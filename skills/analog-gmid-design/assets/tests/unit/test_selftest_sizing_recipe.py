"""TS2(계획 N3.11, C9 20260922-ts2-pytest-split): 이관본 `legacy/selftest_sizing_recipe.py`의 섹션별 pytest test.

정본: design `gain-budget-gmid-sizing.10-test-separation` §6.8, 매핑표
`docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/c9-mapping.json`(test 이름 = 매핑표 `test_ids`).

oracle 대조: 모든 기대값은 (c) 동작 보존 -- head 2dd98f2 이관본(C2가 원본 `sizing_recipe.py`의
`if __name__ == "__main__":` 블록을 그대로 옮긴 것)의 `assert`·거부 try를 그대로 옮겼다. 새 기대값은 없다.
test마다 docstring 끝 줄에 원문 섹션 번호와 줄 범위를 적었다. 거부 try(`try: 호출; raise AssertionError`
+ `except X`)는 `pytest.raises(X)`로, 메시지 단언은 `excinfo.value`로 옮겼다. 판정 없는 print는 옮기지 않았다.
섹션 사이 데이터 의존은 함수 범위 fixture `s<NNN>_state`(그 이름을 만드는 문장만 담는다)로, 전역 `lut`는 세션
fixture `toy_lut`로, `_ASSETS_DIR` 경로는 `assets_dir`·`library_dir`로 바꿨다(design §6.8-3·4).
"""
import os
import sys
import types

import pytest

_ASSETS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
if _ASSETS not in sys.path:
    sys.path.insert(0, _ASSETS)


from sizing_recipe import (SemiEmpiricalGmIdLUT, SizingContext, Transistor, _COMPENSATION_REGISTRY, _blocked_euler_rows, _build_theta_evaluator, _dc_replace, _full_circuit_response, _group_score_interior, _group_score_metric, _invert_gm_id_for_current, _lerp, _load_full_topology_cached, _nmcnr_stage1_rout, allocate_stack_headroom, apply_and_revalidate_matching_finger_growth, apply_and_revalidate_pair_adjustment, apply_theta_feed, build_toy_lut, check_quasi_static, compute_metric, derive_class_L, derive_role_L, diagnose_sizing_roles_gap, diode_vds_window, estimate_area_budget, estimate_mismatch_sigma, feasible_L_window, find_optimal_sizing, json, knee_L_for_kind, load_topology, math, nmcnr_predict_ac_response, np, optimize_full_circuit_budget, optimize_multistage, propagate_topology_forced_currents, require_declared_spec_source, resolve_constraint_references, resolve_stack_layout, revalidate_finger_override, run_matching_safety_with_finger_growth, run_topology_pipeline_with_finger_fixup, search_gm_id_for_role, size_transistor, solve_diode_connected_vds, solve_diode_stack_current, solve_id_for_target_gm, suggest_matching_finger_growth, suggest_pair_finger_adjustments, validate_theta_declaration_order)  # noqa: E402
# 20260930-d-move-tests: 회귀 러너는 엔진에서 test 도구 `A/tests/tools/regression_runner.py`로 이관됐다
# (sys.path 추가 방식은 contracts/test_probe_dup_scan.py 선례).
_TESTS_TOOLS = os.path.join(_ASSETS, "tests", "tools")
if _TESTS_TOOLS not in sys.path:
    sys.path.insert(0, _TESTS_TOOLS)
from regression_runner import run_regression_case  # noqa: E402
import os as _os  # noqa: E402
import tempfile as _tempfile  # noqa: E402
import os as _rsl_os  # noqa: E402
import os as _os_ss  # noqa: E402
import glob as _vtdo_glob  # noqa: E402


def _tst_grids(spec: dict) -> dict:
    """self-test 픽스처 보조(2026-09-10) -- spec의 LUT에서 **격자 3종을 채운다**.

    `derive_role_L()`이 `L_role` 소자의 L을 knee(LUT 실측)에서 유도하는데,
    `knee_L_for_kind()`는 "이 설계가 실제로 탐색하는 격자"에서만 knee를 잰다 --
    선언이 없으면 값을 지어내지 않고 거부한다(그 함수 docstring의 실측 근거 참고).
    실제 설계 spec(`workspaces/run_harness.py`의 `SPECS`)은 이 셋을 전부 직접
    선언하므로, 이 헬퍼는 **toy 픽스처를 실제 spec과 같은 모양으로 맞추는 것**일 뿐
    엔진에 새 폴백을 만드는 게 아니다.
    """
    _l = list(spec["lut_by_kind"].values())[0]
    spec.setdefault("L_candidates", [float(v) for v in _l.L_grid])
    spec.setdefault("VDS_candidates", [float(v) for v in _l.VDS_grid])
    spec.setdefault("gm_id_grid", [i * 0.5 for i in range(4, 61)])
    return spec


@pytest.fixture
def s011_state(toy_lut):
    """섹션 S011(이관본 줄 314-435)이 만드는 이름 _l4c_L, _l4c_gds, _l4c_gm_id, _l4c_m3a_netlist, _l4c_matching_pairs_meta, _l4c_names, _l4c_r, _l4c_vds -- 읽는 섹션: S012. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    lut = toy_lut

    _l4c_m3a_netlist = [
        {"name": "M3a", "kind": "nmos", "source": "N3a4a", "drain": "Vom1", "gate": "Vbias3"},
        {"name": "M3b", "kind": "nmos", "source": "N3b4b", "drain": "Vop1", "gate": "Vbias3"},
        {"name": "M4a", "kind": "nmos", "source": "Vy", "drain": "N3a4a", "gate": "Vip"},
        {"name": "M4b", "kind": "nmos", "source": "Vy", "drain": "N3b4b", "gate": "Vim"},
        {"name": "M5", "kind": "nmos", "source": "gnd", "drain": "Vy", "gate": "Vbias4"},
        {"name": "M9b", "kind": "nmos", "source": "Vop1", "drain": "Vg15", "gate": "N14a14b"},
        {"name": "M10", "kind": "nmos", "source": "gnd", "drain": "Vop1", "gate": "Vbias4"},
        {"name": "M18b", "kind": "nmos", "source": "Vom1", "drain": "Vg25", "gate": "N24b23a"},
        {"name": "M19", "kind": "nmos", "source": "gnd", "drain": "Vom1", "gate": "Vbias4"},
        {"name": "M64", "kind": "nmos", "source": "N64_63", "drain": "Vbias3", "gate": "Vbias3"},
        {"name": "M63", "kind": "nmos", "source": "Vy", "drain": "N64_63", "gate": "Vbias3"},
    ]  # 세션12 M3a 그룹(.ai/context.md, stick_diagram.py Test 5.6)과 connectivity 동일
    _l4c_matching_pairs_meta = [
        {"names": ["M4a", "M4b"], "matching_sensitivity": "offset"},
        {"names": ["M3a", "M3b"], "matching_sensitivity": "ratio"},
        {"names": ["M10", "M19"], "matching_sensitivity": "ratio"},
        {"names": ["M9b", "M18b"], "matching_sensitivity": "ratio"},
    ]
    _l4c_L, _l4c_vds, _l4c_gm_id = 0.5e-6, 0.6, 12.0
    _l4c_r = size_transistor(gm=50e-6, gm_id=_l4c_gm_id, L=_l4c_L, lut=lut, vds=_l4c_vds)
    _l4c_gds = _l4c_r.gm / lut.gm_gds_ratio(_l4c_gm_id, _l4c_L, _l4c_vds, 0.0)
    _l4c_names = [d["name"] for d in _l4c_m3a_netlist]
    _l4c_baseline_area = len(_l4c_names) * _l4c_r.W * _l4c_L

    return types.SimpleNamespace(_l4c_L=_l4c_L, _l4c_gds=_l4c_gds, _l4c_gm_id=_l4c_gm_id, _l4c_m3a_netlist=_l4c_m3a_netlist, _l4c_matching_pairs_meta=_l4c_matching_pairs_meta, _l4c_names=_l4c_names, _l4c_r=_l4c_r, _l4c_vds=_l4c_vds)


@pytest.fixture
def s015_state(assets_dir, toy_lut):
    """섹션 S015(이관본 줄 831-936)이 만드는 이름 _l4d_ctx, _l4d_metrics, _l4d_r, _l4d_tight -- 읽는 섹션: S016. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    lut = toy_lut

    _l4d_L, _l4d_vds = 0.5e-6, 0.6
    _l4d_r = size_transistor(gm=200e-6, gm_id=12.0, L=_l4d_L, lut=lut, vds=_l4d_vds)
    _l4d_gds = _l4d_r.gm / lut.gm_gds_ratio(12.0, _l4d_L, _l4d_vds, 0.0)
    _l4d_g_trs = [Transistor("Ma", "nmos", source="s", drain="d1", n_fingers=1, finger_w=_l4d_r.W),
                  Transistor("Mb", "nmos", source="s", drain="d2", n_fingers=1, finger_w=_l4d_r.W)]
    _g2_trs = [Transistor("Mc", "nmos", source="s", drain="d1", n_fingers=2, finger_w=_l4d_r.W),
               Transistor("Md", "nmos", source="s", drain="d2", n_fingers=2, finger_w=_l4d_r.W)]
    _g3_trs = [Transistor("Me", "nmos", source="s", drain="d1", n_fingers=1, finger_w=_l4d_r.W),
               Transistor("Mf", "nmos", source="s", drain="d2", n_fingers=3, finger_w=_l4d_r.W)]
    _l4d_transistors = [
        Transistor("Ma", "nmos", source="Na1", drain="Nb1", gate="ga",
                   n_fingers=1, finger_w=_l4d_r.W),
        Transistor("Mb", "nmos", source="Na2", drain="Nb2", gate="gb",
                   n_fingers=1, finger_w=_l4d_r.W),
    ]
    _l4d_ctx = SizingContext(sized={
        "Ma": {"ID": _l4d_r.ID, "W": _l4d_r.W, "L": _l4d_L, "gm": _l4d_r.gm, "gm_id": 12.0,
               "gds": _l4d_gds, "kind": "nmos", "vds": _l4d_vds, "vsb": 0.0},
        "Mb": {"ID": _l4d_r.ID, "W": _l4d_r.W, "L": _l4d_L, "gm": _l4d_r.gm, "gm_id": 12.0,
               "gds": _l4d_gds, "kind": "nmos", "vds": _l4d_vds, "vsb": 0.0},
    })
    _l4d_baseline_area = 2 * _l4d_r.W * _l4d_L
    _l4d_metrics = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}
    _l4d_loose = [{"metric": "pair_area", "op": "<=", "value": _l4d_baseline_area * 3.0}]
    _l4d_r1 = apply_and_revalidate_matching_finger_growth(
        ("Ma", "Mb"), _l4d_transistors, _l4d_ctx, {"nmos": lut}, _l4d_metrics, _l4d_loose,
        gm_id_bounds=(2.0, 28.0))
    _l4d_tight = [{"metric": "pair_area", "op": "<=", "value": _l4d_baseline_area * 1.05}]
    _l4d_r2 = apply_and_revalidate_matching_finger_growth(
        ("Ma", "Mb"), _l4d_transistors, _l4d_ctx, {"nmos": lut}, _l4d_metrics, _l4d_tight,
        gm_id_bounds=(2.0, 28.0))
    _l4d_m6_trs, _l4d_m6_meta = load_topology(
        _os.path.join(assets_dir, "library",
                       "current_reuse_telescopic_ota.topology.json"))
    _l4d_m6_by_name = {t.name: t for t in _l4d_m6_trs}
    _l4d_m6_names = ["M1a", "M1b", "M2a", "M2b", "M6", "M7"]
    _l4d_m6_row = [_dc_replace(_l4d_m6_by_name[n], n_fingers=1, finger_w=_l4d_r.W, stack_id="seg1")
                   for n in _l4d_m6_names]

    return types.SimpleNamespace(_l4d_ctx=_l4d_ctx, _l4d_metrics=_l4d_metrics, _l4d_r=_l4d_r, _l4d_tight=_l4d_tight)


@pytest.fixture
def s018_state():
    """섹션 S018(이관본 줄 987-1000)이 만드는 이름 _hr_stack -- 읽는 섹션: S019. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _hr_stack = [
        {"name": "M6", "role": "tail",     "min_vds": 0.30},
        {"name": "M1", "role": "input",    "min_vds": 0.40},
        {"name": "M2", "role": "cascode",  "min_vds": 0.20},
        {"name": "M3", "role": "cascode",  "min_vds": 0.20},
        {"name": "M4", "role": "input",    "min_vds": 0.40},
        {"name": "M5", "role": "tail",     "min_vds": 0.30},
    ]
    _hr_result = allocate_stack_headroom(1.8, _hr_stack)

    return types.SimpleNamespace(_hr_stack=_hr_stack)


@pytest.fixture
def s021_state(toy_lut):
    """섹션 S021(이관본 줄 1036-1058)이 만드는 이름 _feasible_check, _role_L, _role_id_target, _role_vds -- 읽는 섹션: S022, S023. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    lut = toy_lut

    _role_L, _role_vds, _role_id_target = 0.5e-6, 0.6, 40e-6
    _gm_id_matching = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                             role="matching", W_bounds=(1e-6, 200e-6))
    _gm_id_gain = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                         role="gain", W_bounds=(1e-6, 200e-6))
    _gm_id_balanced = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                             role="balanced", W_bounds=(1e-6, 200e-6))
    def _feasible_w(g):
        try:
            return _role_id_target * _role_L / lut.gm_id_to_id_density(g, _role_L, _role_vds, 0.0)
        except ValueError:
            return None
    _feasible_check = [g for g in [i * 0.5 for i in range(4, 61)]
                        if (lambda w: w is not None and 1e-6 <= w <= 200e-6)(_feasible_w(g))]
    _best_ratio_direct = max(lut.gm_gds_ratio(g, _role_L, _role_vds, 0.0) for g in _feasible_check)

    return types.SimpleNamespace(_feasible_check=_feasible_check, _role_L=_role_L, _role_id_target=_role_id_target, _role_vds=_role_vds)


@pytest.fixture
def s037_state(toy_lut):
    """섹션 S037(이관본 줄 1323-1374)이 만드는 이름 _ofc_spec, _ofc_topo -- 읽는 섹션: S050. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    lut = toy_lut

    _ofc_topo = {
        "schema_version": "2.0", "topology_name": "_test_only", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [{"name": "Mtest", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "vb"}],
        "symmetry": {"matching_pairs": [], "dispositions": []},
        "sizing_roles": {
            "theta": [{"name": "N", "bounds": [1.0, 5.0],
                       "feeds": {"type": "B", "tag": "servo", "target": "Mtest",
                                 "omega_key": "omega_c", "cap_key": "cap", "L": 0.5e-6, "W": 30e-6,
                                 "vds": 0.6, "gm_id_bounds": [2.0, 28.0]}}],
            # A12(2026-09-08) -- 이 픽스처 자신이 A12 사례였다: 이름은 `power_uA`인데
            # constraint 임계값 1e-3은 SI(A)였다(=1mA). 이름을 정직하게 `power_A`로 바꾸고
            # unit="A"를 선언한다 -- 환산 계수 1.0이라 값도 임계도 그대로다.
            "metrics": {"power_A": {"type": "sum_current", "unit": "A"}},
            "objective": {"minimize": "power_A"},
            "constraints": [{"metric": "power_A", "op": "<=", "value": 1e-3}],
        },
    }
    with _tempfile.TemporaryDirectory() as _ofc_tmpdir:
        _ofc_topo_path = _os.path.join(_ofc_tmpdir, "_test_only.topology.json")
        with open(_ofc_topo_path, "w", encoding="utf-8") as _f:
            json.dump(_ofc_topo, _f)
        _ofc_spec = {"lut": lut, "lut_by_kind": {"nmos": lut}, "omega_c": 2 * math.pi * 1e6, "cap": 2e-12}
        _ofc_full = optimize_full_circuit_budget(_ofc_topo_path, _ofc_spec, grid_points_per_theta=5)
        _theta_star, _sizing, _metrics = _ofc_full["theta_star"], _ofc_full["sizing"], _ofc_full["metrics"]
        assert _ofc_full["pipeline_result"] is not None, \
            "Mtest는 W까지 다 있는데 전체 파이프라인(assign_finger_geometry/run_topology_pipeline)이 안 돎"
        assert _ofc_full["audit_ok"], f"단일 소자 넷리스트인데 audit이 FAIL: {_ofc_full['pipeline_result']}"

        # 전수비교: 같은 격자를 직접 순회해 손으로 찾은 최적값과 정확히 일치하는지 확인.
        _manual_best = None
        for _i in range(5):
            _N = _lerp(1.0, 5.0, _i / 4)
            _ctx_manual = SizingContext(spec=_ofc_spec, kind_of={"Mtest": "nmos"})
            apply_theta_feed(_ofc_topo["sizing_roles"]["theta"][0]["feeds"], _N, _ctx_manual)
            _a_ids = propagate_topology_forced_currents(
                [Transistor("Mtest", "nmos", source="gnd", drain="out", gate="vb")],
                _ctx_manual.seed_currents, _ctx_manual.mirror_ratios)
            for _name, _idv in _a_ids.items():
                _ctx_manual.sized.setdefault(_name, {})["ID"] = _idv
            _power = compute_metric({"type": "sum_current"}, _ctx_manual)
            if _power <= 1e-3 and (_manual_best is None or _power < _manual_best[0]):
                _manual_best = (_power, _N)
        assert _manual_best is not None, "전수비교 자체가 infeasible -- 테스트 설계 오류"
        assert abs(_metrics["power_A"] - _manual_best[0]) < 1e-12, \
            f"함수 결과({_metrics['power_A']})가 전수비교 최적값({_manual_best[0]})과 다름"
        assert abs(_theta_star["N"] - _manual_best[1]) < 1e-9, \
            f"theta*(N={_theta_star['N']})가 전수비교 최적 N({_manual_best[1]})과 다름"

    return types.SimpleNamespace(_ofc_spec=_ofc_spec, _ofc_topo=_ofc_topo)


@pytest.fixture
def s038_state(toy_lut):
    """섹션 S038(이관본 줄 1375-1436)이 만드는 이름 _gmv_spec, _gmv_topo -- 읽는 섹션: S039. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    lut = toy_lut

    _gmv_topo = {
        "schema_version": "2.0", "topology_name": "_gmv_test", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [
            {"name": "Ma", "kind": "nmos", "source": "vss", "drain": "NodeC", "gate": "NodeC"},
            {"name": "Mb", "kind": "nmos", "source": "vss", "drain": "out", "gate": "NodeC"},
        ],
        "symmetry": {"matching_pairs": [
            {"names": ["Ma", "Mb"], "current_forced": True, "matching_sensitivity": "ratio"}],
            "dispositions": []}, "sizing_roles": None,
        "device_roles": {
            "Ma": {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror", "vsb": 0.0},
            "Mb": {"gm_id_match_vgs_of": "Ma", "L_role": "mirror", "headroom_role": "mirror", "vsb": 0.0},
        },
    }
    _gmv_L, _gmv_ID = 0.5e-6, 1e-5
    _gmv_lo, _gmv_hi = diode_vds_window(lut, "nmos", _gmv_L, _gmv_ID, 0.0, (1e-6, 200e-6))
    _gmv_vds_a = 0.5 * (_gmv_lo + _gmv_hi)
    _gmv_vds_b = _gmv_lo                                 # ⚠️ 일부러 다른 VDS
    _gmv_known = {"Ma": {"ID": _gmv_ID, "L": _gmv_L, "vds": _gmv_vds_a, "vsb": 0.0},
                  "Mb": {"ID": _gmv_ID, "L": _gmv_L, "vds": _gmv_vds_b, "vsb": 0.0}}
    with _tempfile.TemporaryDirectory() as _gmv_tmp:
        _gmv_path = _os.path.join(_gmv_tmp, "_gmv_test.topology.json")
        with open(_gmv_path, "w", encoding="utf-8") as _f:
            json.dump(_gmv_topo, _f)
        # 2026-09-10 -- 격자 3종을 선언한다. L_role의 L은 이제 knee(LUT 실측)에서 유도되고
        # knee는 "이 설계가 실제로 탐색하는 격자"에서만 잰다(knee_L_for_kind() 참고).
        # 선언이 없으면 엔진이 값을 지어내지 않고 거부한다 -- 실제 spec은 전부 선언한다.
        _gmv_spec = {"lut_by_kind": {"nmos": lut}, "vdd": 1.8, "L_min": 0.15e-6,
                     "W_bounds": (1e-6, 200e-6), "min_vds_by_role": {"mirror": 0.2},
                     "L_candidates": [float(v) for v in lut.L_grid],
                     "VDS_candidates": [float(v) for v in lut.VDS_grid],
                     "gm_id_grid": [i * 0.5 for i in range(4, 61)],
                     "known_sizing": _gmv_known}
        # optimize_full_circuit_budget()이 아니라 _build_theta_evaluator()+evaluate({})를 직접
        # 쓴다 -- 이 테스트가 검증하려는 건 device_roles 2차 pass 하나뿐이고, 전체 harness는
        # assign_finger_geometry()/run_topology_pipeline_with_finger_fixup() 같은 무관한 레이아웃
        # 단계까지 통과해야 해서(이 2-소자 toy 회로엔 그 단계용 spec 필드가 없어 실패함) 이
        # 테스트의 의도와 무관한 실패를 낼 수 있다(위 "합성 sizing_roles" 테스트와 달리 이 fixture는
        # 레이아웃까지 검증할 의도가 없음).
        _gmv_ev = _build_theta_evaluator(_gmv_path, _gmv_spec)
        _gmv_ctx, _ = _gmv_ev["evaluate"]({})

    return types.SimpleNamespace(_gmv_spec=_gmv_spec, _gmv_topo=_gmv_topo)


@pytest.fixture
def s040_state(toy_lut):
    """섹션 S040(이관본 줄 1460-1516)이 만드는 이름 _vmv_spec, _vmv_topo -- 읽는 섹션: S041. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    lut = toy_lut

    _vmv_vdd = 1.8
    _vmv_topo = {
        "schema_version": "2.0", "topology_name": "_vmv_test", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [
            {"name": "Ka", "kind": "pmos", "source": "vdd", "drain": "NodeA", "gate": "vb_ka"},
            {"name": "Ma", "kind": "nmos", "source": "vss", "drain": "NodeA", "gate": "vb_ma"},
            {"name": "Kb", "kind": "pmos", "source": "vdd", "drain": "NodeB", "gate": "vb_kb"},
            {"name": "Mb", "kind": "nmos", "source": "vss", "drain": "NodeB", "gate": "NodeA"},
        ],
        "symmetry": {"matching_pairs": [], "dispositions": []}, "sizing_roles": None,
        "device_roles": {
            # Ma는 일부러 gm_id_role을 안 준다(known_sizing으로 compensation처럼 gm_id를
            # 외부에서 고정). Ka/Kb/Mb는 propose_device_roles_gap_fill()의 자동 제안(파트너
            # 없는 active load -> "gain"류)이 require_device_roles_reviewed()를 막지 않도록
            # gm_id_role을 명시 선언해둔다(이 테스트가 검증하려는 vds 흐름과는 무관, review
            # 게이트 통과용).
            "Ka": {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror",
                   "vertical_stack_id": "col_a", "vsb": 0.0},
            "Ma": {"headroom_role": "mirror", "vertical_stack_id": "col_a", "vsb": 0.0},
            "Kb": {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror",
                   "vertical_stack_id": "col_b", "vsb": 0.0},
            "Mb": {"vds_match_vgs_of": "Ma", "gm_id_role": "matching", "L_role": "mirror",
                   "headroom_role": "mirror", "vertical_stack_id": "col_b", "vsb": 0.0},
        },
    }
    _vmv_known = {"Ka": {"ID": 1e-5, "vsb": 0.0}, "Ma": {"ID": 1e-5, "L": 0.5e-6, "gm_id": 15.0, "vsb": 0.0},
                  "Kb": {"ID": 1e-5, "vsb": 0.0}, "Mb": {"ID": 1e-5, "vsb": 0.0}}
    with _tempfile.TemporaryDirectory() as _vmv_tmp:
        _vmv_path = _os.path.join(_vmv_tmp, "_vmv_test.topology.json")
        with open(_vmv_path, "w", encoding="utf-8") as _f:
            json.dump(_vmv_topo, _f)
        _vmv_spec = _tst_grids({"lut_by_kind": {"nmos": lut, "pmos": lut}, "vdd": _vmv_vdd, "L_min": 0.15e-6,
                     "W_bounds": (1e-6, 200e-6), "min_vds_by_role": {"mirror": 0.2},
                     "known_sizing": _vmv_known})
        _vmv_ctx, _ = _build_theta_evaluator(_vmv_path, _vmv_spec)["evaluate"]({})

    return types.SimpleNamespace(_vmv_spec=_vmv_spec, _vmv_topo=_vmv_topo)


@pytest.fixture
def s042_state():
    """섹션 S042(이관본 줄 1532-1598)이 만드는 이름 _fpw_vdd -- 읽는 섹션: S043. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _fpw_vdd = 1.8

    return types.SimpleNamespace(_fpw_vdd=_fpw_vdd)


@pytest.fixture
def s043_state():
    """섹션 S043(이관본 줄 1600-1645)이 만드는 이름 _diag_lut -- 읽는 섹션: S045. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _diag_lut = build_toy_lut()

    return types.SimpleNamespace(_diag_lut=_diag_lut)


@pytest.fixture
def s051_state(library_dir, toy_lut):
    """섹션 S051(이관본 줄 1752-1887)의 입력(`_tso_path`·`_tso_spec`)을 만드는 문장. 피검 호출
    `optimize_full_circuit_budget()`은 ValueError(I-C11)를 내므로 fixture가 아니라 test 본문에 둔다(spec card
    계약 4 -- fixture setup의 예외는 xfail이 아니라 ERROR다). 읽는 test: S051·S054 네 개."""
    _lib_dir_recipe = library_dir
    lut = toy_lut

    _tso_real_path = _os.path.join(_lib_dir_recipe, "two_stage_ota.topology.json")
    # 2026-08-13(세션31 이어, L1~L4 4-DOF 확장 뒤) -- 실제 topology.json의 gain_db>=60은
    # 실제 sky130 LUT 기준 목표다(사용자와 문헌조사로 확정). 이 self-test는 toy LUT
    # (VA=5*L(um), gds가 실제 sky130보다 훨씬 낙관적으로 단순화됨)라 stage_gain_min을
    # 아무리 올려도(실측: 30~42dB 스윕) 46~58dB 근방에서 정체돼 60dB에 못 미친다(toy LUT
    # 자체 한계, "숫자를 설계에 쓰지 말 것" 원칙 그대로) -- 그래서 이 구조 검증 self-test
    # 전용으로 gain_db 문턱만 50dB(toy LUT가 안정적으로 넘기는 여유치)로 낮춘 임시 복사본을
    # 쓴다. 진짜 60dB 달성 여부는 실제 sky130 LUT로(다른 회로들처럼 workspaces/의 별도
    # harness에서) 검증할 것 -- 이 self-test의 목적은 "L1~L4 4-DOF 탐색 파이프라인이
    # AI 개입 없이 끝까지 완주하는가"이지 이 특정 spec(GBW=20MHz/CL=3pF/Z=10/NDP=4)이
    # 60dB를 실제로 달성하는지가 아니다.
    with open(_tso_real_path, encoding="utf-8") as _tso_f:
        _tso_topo_dict = json.load(_tso_f)
    for _tso_c in _tso_topo_dict["sizing_roles"]["constraints"]:
        if _tso_c["metric"] == "gain_db":
            _tso_c["value"] = 50.0
    _tso_path = _os.path.join(_tempfile.gettempdir(), "two_stage_ota_selftest.topology.json")
    with open(_tso_path, "w", encoding="utf-8") as _tso_f:
        json.dump(_tso_topo_dict, _tso_f)
    _tso_spec = {
        "lut_by_kind": {"nmos": lut, "pmos": lut},
        "vdd": 2.0,
        # 2026-08-13(세션31 이어, L_mirror_M3/L_mirror_M5 신설) -- metric_stage_budget
        # L타입 theta(순수 실수 L)는 layout grid quantization이 필요하다(run_harness.py의
        # current_reuse L_GRID_STEP=5nm과 동일 이유, sky130 tech LEF MANUFACTURINGGRID
        # 실측값) -- self-test는 toy LUT라 이 값 자체가 공정을 대표하진 않지만 메커니즘
        # 검증에는 임의의 5nm 격자로 충분하다.
        "L_grid_step": 0.005e-6,
        "GBW": 20e6, "CL": 3e-12, "Z": 10.0, "NDP": 4.0,
        # 2026-08-13(세션31 이어, two_stage_ota constraints 신설) -- topology.json에
        # gain_db>=60(전체회로) constraint를 추가하면서 발견: stage_devices(M1/M2,M6)의
        # L은 optimize_multistage()가 objective="power"로만 고르는데, gm이 compensation으로
        # 이미 고정된 상태에서는 전력이 L과 무관해(ID=gm/(gm/ID)) L이 사실상 "동점"이라
        # 격자 맨 앞(L_min=0.18um, VA=5*0.18=0.9V로 이득이 매우 작음)이 그냥 뽑혀 실측
        # gain_db=4.4dB(60dB에 한참 못 미침)로 infeasible이었다 -- optimize_multistage()
        # 자체엔 이걸 막을 gain_min 인자가 이미 있었는데(스칼라 또는 스테이지별 리스트,
        # docstring 821행대) 이 프로젝트 어디에서도 실제로 설정된 적이 없었다(harness 연동
        # 감사류로 처음 발견). ⚠️ find_optimal_sizing()의 "gain" 필드는 **선형** gm/gds
        # 비율이지 dB가 아니다(`_sizing_bundle()`의 `gm_gds = vals[1]/vals[2]`, dB 변환
        # 없음) -- 처음엔 이걸 dB로 착각해 30.0을 그대로 넣었었다(실측으로 발견: 실제
        # sky130 LUT에서 gm/gds=471.6 같은 값을 'dB'로 잘못 읽고 471dB라는 물리적으로
        # 불가능한 수치를 봤다가 정정). 목표 dB를 선형으로 변환(`10**(dB/20)`)해서 넣어야
        # 한다. stage_devices 순서(["M1","M2"],["M6"])에 맞춰 스테이지당 30dB씩(합 60dB,
        # 이 회로는 두 스테이지가 컴펜세이션 캡을 DC에서 무시하는 단순 직렬 캐스케이드라
        # 전체회로 smallsignal_gain_db가 두 스테이지 dB 합과 거의 같다) 최소치를 줘서 L
        # 탐색이 이득도 고려하도록 배선.
        "stage_gain_min": [10 ** (30.0 / 20), 10 ** (30.0 / 20)],
        "L_candidates": [float(v) for v in lut.L_grid],
        "VDS_candidates": [float(v) for v in lut.VDS_grid],
        "gm_id_grid": [i * 0.5 for i in range(4, 58)],
        "L_min": 0.18e-6,
        "W_bounds": (1e-6, 200e-6),
        # 2026-08-13 -- stage_gain_min 신설과 함께 200um->500um로 확대. 이유(toy LUT
        # 전용 한계, 실측): w_max=200um에서는 stage1 L이 커지며(Cgg 증가) Miller Cm
        # 재계산으로 gm1이 반복마다 커지고 gm2=Z*gm1(Z=10)도 같이 커져 2번째 반복에서
        # stage2가 200um 안에 못 들어가 INFEASIBLE(diag 스크립트로 확인) -- 500um에서는
        # 4회 반복 만에 total=62dB로 깨끗이 수렴(회로 자체의 물리적 한계가 아니라 toy LUT
        # 데모용 예산이 너무 빠듯했던 것, sky130-worked-example.md가 이미 경고한 대로
        # "toy LUT 숫자 자체를 설계에 쓰지 말 것" 원칙 그대로 -- 실제 sky130 LUT는 훨씬
        # 적은 예산(200um)으로도 60dB를 넘긴다, run_harness.py류 실제 하네스에서 확인).
        "stage_w_max": 500e-6,
        "min_vds_by_role": {"cascode": 0.2, "tail": 0.2},
        "min_finger_w": 0.1e-6, "max_finger_w": 40e-6,
        # 2026-08-13(세션31 이어, two_stage_ota constraints 신설) -- sizing_roles.metrics에
        # mismatch_sigma_mV(pelgrom_mismatch, kind=nfet)를 추가하면서 필요해짐. run_harness.py
        # (current_reuse_telescopic_ota)가 이미 쓰는 sky130 PDK mismatch 상수 그대로 재사용
        # (self-test는 toy LUT라 실제 sky130 값과 무관하지만, 상수 자체는 sky130 실측값).
        "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
        # derive_stack_groups()의 자동 병합은 {M1,M2,M3,M4}를 한 그룹으로 묶는데(D3/O1
        # 2단자 내부노드 + matching_pairs), 입력쌍(M1/M2)과 부하 미러(M3/M4)는 전류는 같아도
        # W가 서로 달라 finger_w 비율-호환이 안 될 수 있다 -- 물리적으로 더 타당한(입력쌍과
        # 부하를 별도 행으로 두는) 분할을 선언으로 override(§ stack_groups_override 참고).
        # [교훈, 2026-07-31] stack_groups_geometry(레이아웃 행 그룹핑)는 KCL 직렬연결이 아니라
        # symmetry.matching_pairs 선언을 따라야 한다 -- 처음엔 M6/M7이 같은 KCL 스택(전류가
        # 같음)이라는 이유로 묶었다가, 실제 matching pair는 M5/M7(current_mirror)이고 M6은
        # 짝이 없는 단독 소자라는 걸 놓쳐 box-shape 감사가 실패했다(M5/M7이 서로 다른 행에
        # 있어 repair가 나중에 억지로 합치며 각자 독립 배정된 finger 수가 그대로 더해져 폭이
        # 2배로 부풀었음). matching_pairs 그대로 묶으니(M5+M7 한 그룹, M6 단독) 알고리즘
        # 변경 없이 바로 box-shape 비율 1.20으로 통과.
        # 2026-08-13(세션31 CH->CJ) -- CH에서 topology.json의 L_mirror_M5를 L_M5/L_M7(독립
        # theta)로 한 번 분리했다가, GBW=20MHz->7MHz(무릎 지점) 레버가 gain_db를 훨씬 크게
        # 개선한 뒤 M5/M7 분리가 주는 +1dB가 4배 늘어난 folding 비용에 안 맞는다고 판단해
        # 사용자 지시로 공유 theta(L_mirror_M5, devices=[M5,M7])로 원복 -- stack_groups_
        # override도 다시 M5+M7 한 행으로.
        "stack_groups_override": {"M1": ["M1", "M2"], "M3": ["M3", "M4"],
                                    "M5": ["M5", "M7"], "M6": ["M6"]},
    }
    # 2026-08-24(세션42) -- 세션41이 `stage1_ref`/`stage1_out` 분리 + `vds` 고정값 제거로
    # two_stage_ota.topology.json을 고친 뒤, 이 라이브러리 파일을 읽는 이 self-test(세션31
    # 이전부터 있던 배치 7-5)가 세션41이 이미 발견·기록한 바로 그 DC/AC 미해결 갭
    # (compensation이 정하는 M1/M2/M6과 헤드룸이 정하는 M3/M4/M5/M7이 서로 KVL로 안 맞음,
    # `.ai/context.md` 세션41 §3 참고)을 이제 이 self-test에서도 실제로 드러낸다 -- 사용자가
    # 세션41에서 이미 "DC/AC 조율 없이는 못 푸는 문제, 별도 세션으로 넘김"으로 확정했으므로
    # (재설계는 이 세션 범위 밖), 여기서 억지로 고치지 않고 바로 위 audit_ok 정보성 출력과
    # 같은 패턴으로 **정확히 그 이유로만** 실패하는지 검증한 뒤 정보로만 남긴다 -- 다른
    # 이유(예: 새 KeyError/AttributeError)로 실패하면 그건 회귀이므로 그대로 크래시시킨다.

    return types.SimpleNamespace(_tso_path=_tso_path, _tso_spec=_tso_spec)


@pytest.fixture
def s052_state(toy_lut):
    """섹션 S052(이관본 줄 1888-1937)이 만드는 이름 _lrec_topo -- 읽는 섹션: S053. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    lut = toy_lut

    _lrec_topo = {
        "schema_version": "2.0", "topology_name": "_test_L_reconcile", "source": "self-test",
        "linked_topology_files": [], "_compensation_status": "resolved",
        "netlist": [{"name": "Ma", "kind": "nmos", "source": "gnd", "drain": "d1", "gate": "g1"},
                     {"name": "Mc", "kind": "nmos", "source": "gnd", "drain": "d2", "gate": "g2"},
                     {"name": "Mb", "kind": "nmos", "source": "gnd", "drain": "d3", "gate": "g3"}],
        "symmetry": {"matching_pairs": [{"names": ["Ma", "Mb"], "current_forced": False, "matching_sensitivity": "ratio"}],
                      "dispositions": []},
        "compensation": {"function": "miller_ota_topology",
                          "parameters": ["GBW", "CL", "Z", "NDP"],
                          "stage_devices": [["Ma"], ["Mc"]]},
        # 2026-08-14 세션34 -- gm_id_role을 명시적으로 False로 선언(원래 None) -- Mb(레일
        # 소스+HIGH_Z 드레인, 파트너 없는 고립 소자)가 propose_device_roles_gap_fill()의 새
        # 4번째 소스("gm_id_role=gain" 제안) 대상이 됐다. 이 테스트는 Mb의 matching_pairs를
        # 일부러 current_forced=False로 둬(L_role 재설계만 검증하려는 의도) Mb의 ID를 A엔진이
        # 절대 못 정하게 설계돼 있다 -- 어떤 값이든 gm_id_role이 채워지면(심지어 declared로
        # 직접 줘도) sizing_recipe.py의 gm_id_role 루프가 "ID 없음"으로 즉시 ValueError를
        # 낸다(이 fixture 고유의 제약, 버그 아님). False는 None과 달리 "이미 명시적으로
        # 결정됨(해당없음)"으로 인식돼 gain 제안과 충돌 처리(자동 병합 안 됨 -> review 불필요)
        # 되면서도, falsy라 gm_id_role 루프 자체는 여전히 건너뛴다(None과 동일 동작).
        "device_roles": {"Mb": {"headroom_role": None, "gm_id_role": False,
                                  "L_role": "mirror", "vertical_stack_id": None, "vsb": 0.0}},
    }
    with _tempfile.TemporaryDirectory() as _lrec_tmpdir:
        _lrec_path = _os.path.join(_lrec_tmpdir, "_test_L_reconcile.topology.json")
        with open(_lrec_path, "w", encoding="utf-8") as _f:
            json.dump(_lrec_topo, _f)
        _lrec_spec = _tst_grids({
            "lut_by_kind": {"nmos": lut}, "GBW": 20e6, "CL": 3e-12, "Z": 10.0, "NDP": 4.0,
            "L_candidates": [float(v) for v in lut.L_grid],
            "VDS_candidates": [float(v) for v in lut.VDS_grid],
            "gm_id_grid": [i * 0.5 for i in range(4, 58)],
            "stage_w_max": 200e-6,
            # Mb의 L_role="mirror"이 낼 L(=L_min_by_kind*2.5)이 compensation이 Ma에 고른 L과
            # 반드시 달라지도록 L_min_by_kind를 일부러 compensation 후보와 안 맞는 값으로 지정.
            "L_min_by_kind": {"nmos": 0.35e-6},
        })
        _lrec_result = optimize_full_circuit_budget(_lrec_path, _lrec_spec)
        _La_final = _lrec_result["sizing"]["Ma"]["L"]
        _Lb_final = _lrec_result["sizing"]["Mb"]["L"]
        # Mb가 단독이었으면(=compensation이 안 덮었으면) derive_role_L()이 냈을 값.
        # 2026-09-10 이전에는 `0.35e-6 * 2.5`(select_L_by_role의 고정배수)였다.
        _Lb_heuristic = knee_L_for_kind(_lrec_spec["lut_by_kind"]["nmos"], _lrec_spec)
        assert abs(_La_final - _Lb_final) < 1e-15, \
            f"matching pair L이 여전히 다름(에러 없이 통과했는데 재설계가 안 됨): Ma={_La_final}, Mb={_Lb_final}"
        assert abs(_Lb_heuristic - _La_final) > 1e-15, \
            "테스트 설계 오류 -- L_role 휴리스틱값과 compensation값이 우연히 같아서 재설계 여부를 구분 못 함"

    return types.SimpleNamespace(_lrec_topo=_lrec_topo)


@pytest.fixture
def s057_state(toy_lut):
    """섹션 S057(이관본 줄 1995-2007)이 만드는 이름 _freq_test, _lut_with_noise, _sid1f_expected, _w_target_test -- 읽는 섹션: S058. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    lut = toy_lut

    _lut_np = lut.np
    _sid1f_at_wref = 4e-16  # 임의 상수(V^2/Hz @ 1Hz, W_ref 기준) -- 격자 전체 동일값으로 합성
    _sid1f_array = _lut_np.full(lut.ID.shape, _sid1f_at_wref)
    _lut_with_noise = SemiEmpiricalGmIdLUT(lut.L_grid, lut.VGS_grid, lut.VDS_grid, lut.VS_grid,
                                            lut.ID, lut.GM, lut.GDS, lut.CGG, W_ref=lut.W_ref,
                                            SID_1F=_sid1f_array)
    _w_ref_eff = lut._w_ref_effective(0.5e-6)
    _w_target_test = 20e-6
    _freq_test = 10.0
    _sid1f_result = _lut_with_noise.noise_1f_density(15.0, 0.5e-6, 0.6, 0.0, _w_target_test, _freq_test)
    _sid1f_expected = _sid1f_at_wref * _w_ref_eff / _w_target_test / _freq_test

    return types.SimpleNamespace(_freq_test=_freq_test, _lut_with_noise=_lut_with_noise, _sid1f_expected=_sid1f_expected, _w_target_test=_w_target_test)


@pytest.fixture
def s060_state():
    """섹션 S060(이관본 줄 2036-2045)이 만드는 이름 _ctx_cmrr -- 읽는 섹션: S061. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _ctx_cmrr = SizingContext(sized={"M5": {"gm": 500e-6, "gds": 5e-6}})  # tail 소자
    _cmrr_db = compute_metric(
        {"type": "cmrr_estimate", "tail_device": "M5", "circuit_family": "diff_pair_tail"}, _ctx_cmrr)
    _psrr_db = compute_metric(
        {"type": "psrr_estimate", "tail_device": "M5", "circuit_family": "diff_pair_tail"}, _ctx_cmrr)

    return types.SimpleNamespace(_ctx_cmrr=_ctx_cmrr)


@pytest.fixture
def s063_state():
    """섹션 S063(이관본 줄 2077-2109)이 만드는 이름 _nmcnr_sized, _nmcnr_spec -- 읽는 섹션: S064. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _nmcnr_spec = {
        "gm1_device": "M102", "gm2_device": "M201", "gm3_device": "M301",
        "stage1_cascode_n": "M107", "stage1_fold_leg_a": "M103", "stage1_fold_leg_b": "M105",
        "stage1_mirror_p": "M109", "stage2_devices": ["M202", "M204"],
        "stage3_devices": ["M301", "M302"], "CL": 1e-10, "kg": 0.5,
    }
    _nmcnr_sized = {
        "M102": {"gm": 1e-3, "gds": 1e-8},
        "M103": {"gm": 1e-3, "gds": 2e-6}, "M105": {"gm": 1e-3, "gds": 2e-6},
        "M107": {"gm": 2e-3, "gds": 1e-6}, "M109": {"gm": 1e-3, "gds": 5e-6},
        "M201": {"gm": 0.2e-3, "gds": 1e-8},
        "M202": {"gm": 1e-3, "gds": 4e-6}, "M204": {"gm": 1e-3, "gds": 4e-6},
        "M301": {"gm": 0.5e-3, "gds": 3e-6}, "M302": {"gm": 1e-3, "gds": 3e-6},
    }
    _nmcnr_ctx = SizingContext(sized=_nmcnr_sized)
    _R1_actual = _nmcnr_stage1_rout(_nmcnr_spec, _nmcnr_ctx)

    return types.SimpleNamespace(_nmcnr_sized=_nmcnr_sized, _nmcnr_spec=_nmcnr_spec)


@pytest.fixture
def s065_state(library_dir):
    """섹션 S065(이관본 줄 2123-2175)이 만드는 이름 _crt_by_name, _crt_transistors -- 읽는 섹션: S067. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _lib_dir_recipe = library_dir

    _crt_topo_path = _os.path.join(_lib_dir_recipe, "current_reuse_telescopic_ota.topology.json")
    _crt_transistors, _ = load_topology(_crt_topo_path)
    _crt_by_name = {t.name: t for t in _crt_transistors}

    return types.SimpleNamespace(_crt_by_name=_crt_by_name, _crt_transistors=_crt_transistors)


def test_s003__evaluate():
    """# _COMPENSATION_REGISTRY allowlist 거부 -- 실제 harness 경로(_evaluate()) 자체를
    # 통해 확인(2026-08-12 세션30 -- run_sizing_pipeline()은 죽은 코드라 삭제됐고,
    # 그 함수에만 있던 이 가드를 _evaluate()에 새로 추가했다, harness 연동 감사 중 발견)

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S003(줄 63-87, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    with _tempfile.TemporaryDirectory() as _tmpdir:
        _bad_path = _os.path.join(_tmpdir, "bad.topology.json")
        with open(_bad_path, "w", encoding="utf-8") as _f:
            json.dump({
                "topology_name": "bad_fixture", "schema_version": "2.0",
                "netlist": [],
                "symmetry": {"matching_pairs": []},
                "compensation": {"function": "not_a_real_function", "parameters": [],
                                  "stage_devices": [["M1"]]},
                "sizing_roles": {"theta": [], "metrics": {}, "objective": {}, "constraints": []},
            }, _f)
        with pytest.raises(ValueError) as _e_info:
            optimize_full_circuit_budget(_bad_path, {"stage_w_max": 1e-4})
        _e = _e_info.value
        assert "_COMPENSATION_REGISTRY" in str(_e)


def test_s004_optimize_multistage(assets_dir):
    """# 배치 7-1(analog-topology-json-library.do.md) — optimize_multistage() 실제 실행 확보 (2026-07-31)
    # 정의 이후 저장소 전체 호출 0건이었음(do.md 배치 7-1 문제 행) — run_regression_case()로 공정-무관하게 검증한다. sky130 숫자는 이 파일이 아니라 sky130_regression_reference.json에만 있다(2026-07-31 재설계 — 이 파일에 공정별
    # 숫자를 직접 박으면 새 공정 LUT로는 이 self-test 자체가 항상 깨진다는 사용자 지적 반영).

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S004(줄 88-107, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _ref_json_path = _os.path.join(
        assets_dir, "sky130_regression_reference.json")
    _verdict = run_regression_case(
        _ref_json_path, "nmcnr_3stage_GBW5M_CL10p_PM70_kg0.5")
    if _verdict.actual:
        for _i, _st in enumerate(_verdict.actual["stages"], 1):
            pass
    assert _verdict.ok, _verdict.detail


def test_s006_solve_id_for_target_gm(toy_lut):
    """# 배치 7-3 B/C/F 엔진(analog-topology-json-library.do.md §7.3.2, 2026-07-31) -- # LUT가 필요한 절반: solve_id_for_target_gm()/solve_diode_stack_current()/ # compute_metric()+_METRICS_REGISTRY. toy LUT(build_toy_lut(), W_ref=None)로 검증.

    [B엔진 solve_id_for_target_gm() -- 순방향으로 만든 gm_target을 역산해 gm_id 복원]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S006(줄 113-127, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _b_L, _b_vds, _b_W, _b_gm_id_known = 0.5e-6, 0.6, 50e-6, 15.0
    _b_idu = lut.gm_id_to_id_density(_b_gm_id_known, _b_L, _b_vds, 0.0)
    _b_id_known = _b_idu * _b_W / _b_L
    _b_gm_known = _b_gm_id_known * _b_id_known
    # toy LUT의 gm/ID 유효범위가 ~[1.85,29.6]이라(build_toy_lut() VGS 스윕 범위) 기본
    # bounds(2~30)의 상단이 살짝 밖으로 나간다 -- 이 LUT에 맞는 범위를 명시로 좁혀서 호출.
    _b_result = solve_id_for_target_gm(lut, _b_L, _b_vds, 0.0, _b_W, _b_gm_known,
                                        gm_id_bounds=(2.0, 28.0))
    assert abs(_b_result.gm_id - _b_gm_id_known) < 1e-3, "B엔진 gm_id 역산 오차 과다"
    assert abs(_b_result.ID - _b_id_known) / _b_id_known < 1e-3, "B엔진 ID 역산 오차 과다"


def test_s007_solve_diode_stack_current(toy_lut):
    """[C엔진 solve_diode_stack_current() -- 순방향으로 만든 VGS합을 역산해 전류 복원]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S007(줄 128-145, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _c_stack = [
        {"kind": "nmos", "L": 0.5e-6, "W": 20e-6, "vds": 0.6, "vsb": 0.0},
        {"kind": "nmos", "L": 0.5e-6, "W": 10e-6, "vds": 0.6, "vsb": 0.0},
    ]
    _c_i_known = 30e-6
    _c_vgs_target = 0.0
    for _dev in _c_stack:
        _gm_id = _invert_gm_id_for_current(lut, _c_i_known, _dev["L"], _dev["vds"], _dev["vsb"], _dev["W"],
                                            gm_id_bounds=(2.0, 28.0))
        _c_vgs_target += lut.vgs_for_gm_id(_gm_id, _dev["L"], _dev["vds"], _dev["vsb"])
    _c_i_solved = solve_diode_stack_current(lut, _c_stack, _c_vgs_target,
                                             i_bounds=(1e-9, 3e-4), gm_id_bounds=(2.0, 28.0))
    assert abs(_c_i_solved - _c_i_known) / _c_i_known < 1e-3, "C엔진 전류 역산 오차 과다"


def test_s008_compute_metric():
    """[F엔진 compute_metric()/_METRICS_REGISTRY -- sum_current/sum_area/gain_stages_sum]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S008(줄 146-166, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _f_ctx = SizingContext(sized={
        "M1": {"ID": 10e-6, "W": 20e-6, "L": 0.5e-6, "gm": 100e-6, "gds": 1e-6},
        "M2": {"ID": 20e-6, "W": 30e-6, "L": 0.5e-6, "gm": 150e-6, "gds": 2e-6},
    })
    _f_current = compute_metric({"type": "sum_current"}, _f_ctx)
    _f_area = compute_metric({"type": "sum_area"}, _f_ctx)
    _f_gain = compute_metric({"type": "gain_stages_sum", "stages": [["M1", "M2"]]}, _f_ctx)
    assert abs(_f_current - 30e-6) < 1e-12, "sum_current 오류"
    assert abs(_f_area - (20e-6 * 0.5e-6 + 30e-6 * 0.5e-6)) < 1e-18, "sum_area 오류"
    _f_gain_expected = 20 * math.log10((100e-6 + 150e-6) / (1e-6 + 2e-6))
    assert abs(_f_gain - _f_gain_expected) < 1e-9, "gain_stages_sum 오류"
    with pytest.raises(ValueError):
        compute_metric({"type": "not_a_real_metric"}, _f_ctx)


def test_s009_revalidate_finger_override(toy_lut):
    """[L4 revalidate_finger_override() -- finger 반올림으로 W가 강제로 바뀌어도 ID는
    그대로라는 원칙(A엔진)을 재확인하고, 영향받는 metric/constraint만 재검증하는지]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S009(줄 167-228, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _l4_L, _l4_vds, _l4_gm_id = 0.5e-6, 0.6, 12.0
    _l4_r1 = size_transistor(gm=200e-6, gm_id=_l4_gm_id, L=_l4_L, lut=lut, vds=_l4_vds)
    _l4_gds1 = _l4_r1.gm / lut.gm_gds_ratio(_l4_gm_id, _l4_L, _l4_vds, 0.0)
    _l4_r3 = size_transistor(gm=80e-6, gm_id=10.0, L=_l4_L, lut=lut, vds=_l4_vds)
    _l4_gain_baseline = 20 * math.log10((_l4_r1.gm + _l4_r1.gm) / (_l4_gds1 + _l4_gds1))
    _l4_ctx = SizingContext(sized={
        "M1": {"ID": _l4_r1.ID, "W": _l4_r1.W, "L": _l4_L, "gm": _l4_r1.gm, "gm_id": _l4_gm_id,
               "gds": _l4_gds1, "kind": "nmos", "vds": _l4_vds, "vsb": 0.0},
        "M2": {"ID": _l4_r1.ID, "W": _l4_r1.W, "L": _l4_L, "gm": _l4_r1.gm, "gm_id": _l4_gm_id,
               "gds": _l4_gds1, "kind": "nmos", "vds": _l4_vds, "vsb": 0.0},
        "M3": {"ID": _l4_r3.ID, "W": _l4_r3.W, "L": _l4_L, "gm": _l4_r3.gm, "gm_id": 10.0,
               "gds": 0.0, "kind": "nmos", "vds": _l4_vds, "vsb": 0.0},
    })
    _l4_metrics_specs = {
        "stage_gain": {"type": "gain_stages_sum", "stages": [["M1", "M2"]]},
        "other_current": {"type": "sum_current", "devices": ["M3"]},
    }
    _l4_threshold = _l4_gain_baseline - 0.5
    _l4_constraints = [
        {"metric": "stage_gain", "op": ">=", "value": _l4_threshold},
        {"metric": "other_current", "op": "<=", "value": 100e-6},
    ]

    _l4_pass_result = revalidate_finger_override(
        _l4_ctx, {"nmos": lut}, {"M1": _l4_r1.W * 0.9}, _l4_metrics_specs, _l4_constraints,
        gm_id_bounds=(2.0, 28.0))
    _l4_du_pass = _l4_pass_result["device_updates"]["M1"]
    assert abs(_l4_du_pass["new_gm"] / _l4_du_pass["new_gm_id"] - _l4_r1.ID) < 1e-15, \
        "ID가 보존되지 않음 -- W가 바뀌어도 ID는 topology로 고정이어야 한다"
    assert _l4_pass_result["ok"] and not _l4_pass_result["violated_constraints"], \
        "10% 축소는 여전히 constraint를 통과해야 하는데 위반으로 나옴"
    # 2026-09-08 -- 예전엔 `unaffected_metrics_skipped == ["other_current"]`를 단정해
    # "무관한 metric은 재계산을 건너뛴다"는 최적화를 검증했다. 그 최적화 자체를 폐기했으므로
    # (metric spec이 소자를 명시하지 않으면 참조가 빈 집합이라 전 소자를 읽는 metric까지
    # "무관"으로 분류돼 조용히 건너뛰었다 -- `revalidate_finger_override()` 주석 참고)
    # 단정도 새 계약으로 바꾼다: **아무것도 건너뛰지 않고**, 진단 정보는 이름이 정확한
    # 새 키로 옮겼다.
    assert _l4_pass_result["unaffected_metrics_skipped"] == [], \
        "이제 어떤 metric도 재계산을 건너뛰지 않는다"
    assert set(_l4_pass_result["metric_deltas"]) == {"stage_gain", "other_current"}, \
        "모든 metric이 재계산돼 metric_deltas에 있어야 한다"
    assert _l4_pass_result["metrics_not_referencing_changed_devices"] == ["other_current"], \
        "M3를 안 건드렸으니 other_current는 '바뀐 소자를 참조하지 않는' 목록에 있어야 한다"

    _l4_fail_result = revalidate_finger_override(
        _l4_ctx, {"nmos": lut}, {"M1": _l4_r1.W * 0.6}, _l4_metrics_specs, _l4_constraints,
        gm_id_bounds=(2.0, 28.0))
    assert not _l4_fail_result["ok"], "40% 축소는 gain을 threshold 밑으로 떨어뜨려야 하는데 ok=True로 나옴"
    assert len(_l4_fail_result["violated_constraints"]) == 1 and \
        _l4_fail_result["violated_constraints"][0]["metric"] == "stage_gain", \
        "위반된 constraint가 정확히 stage_gain 하나여야 한다"

    assert _l4_ctx.sized["M1"]["W"] == _l4_r1.W, "revalidate_finger_override()가 원본 ctx를 변형했다"


def test_s010_apply_and_revalidate_pair_adjustment(toy_lut):
    """[L4b apply_and_revalidate_pair_adjustment() -- suggest_pair_finger_adjustments()(L3)의
    제안을 revalidate_finger_override()(L4)로 자동 승인/거부하는 상위 오케스트레이션,
    세션12 M3a 그룹(M9b/M18b) 사례가 실제 동기 -- .ai/context.md 세션13 D절]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S010(줄 229-313, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _l4b_L, _l4b_vds = 0.5e-6, 0.6
    _l4b_crit = size_transistor(gm=200e-6, gm_id=12.0, L=_l4b_L, lut=lut, vds=_l4b_vds)
    _l4b_crit_gds = _l4b_crit.gm / lut.gm_gds_ratio(12.0, _l4b_L, _l4b_vds, 0.0)
    _l4b_harm = size_transistor(gm=50e-6, gm_id=15.0, L=_l4b_L, lut=lut, vds=_l4b_vds)
    _l4b_harm_gds = _l4b_harm.gm / lut.gm_gds_ratio(15.0, _l4b_L, _l4b_vds, 0.0)

    # 그래프 레벨(홀수차수 개선용) -- Ma/Mb(critical, 면적 제약 대상)와 Xa/Xb(harmless, 제약과
    # 무관)가 각각 독립된 고립 edge라 baseline에서 둘 다 홀수차수 4개씩 기여 -- 어느 쪽을 먼저
    # +1해도 개선폭(-4)이 동일한 "타이" 상황을 의도적으로 구성해, 정렬 안정성(먼저 나온 소자
    # 우선)으로 Ma/Mb가 1순위가 되게 한다(transistors 리스트 순서 Ma,Mb,Xa,Xb).
    _l4b_transistors = [
        Transistor("Ma", "nmos", source="Na1", drain="Nb1", gate="ga",
                   n_fingers=1, finger_w=_l4b_crit.W),
        Transistor("Mb", "nmos", source="Na2", drain="Nb2", gate="gb",
                   n_fingers=1, finger_w=_l4b_crit.W),
        Transistor("Xa", "nmos", source="Xa1", drain="Xb1", gate="gxa",
                   n_fingers=1, finger_w=_l4b_harm.W),
        Transistor("Xb", "nmos", source="Xa2", drain="Xb2", gate="gxb",
                   n_fingers=1, finger_w=_l4b_harm.W),
    ]
    _l4b_pairs = [("Ma", "Mb"), ("Xa", "Xb")]

    _l4b_suggestions = suggest_pair_finger_adjustments(_l4b_transistors, _l4b_pairs)
    assert _l4b_suggestions[0].names == ("Ma", "Mb") and _l4b_suggestions[0].delta_fingers == 1, \
        "1순위 후보가 (Ma,Mb)+1이 아님 -- 타이 상황에서 리스트 순서 우선이 깨짐"
    assert _l4b_suggestions[1].names == ("Xa", "Xb") and _l4b_suggestions[1].delta_fingers == 1, \
        "2순위 후보가 (Xa,Xb)+1이 아님"

    def _l4b_ctx_for(crit, crit_gds, harm, harm_gds):
        return SizingContext(sized={
            "Ma": {"ID": crit.ID, "W": crit.W, "L": _l4b_L, "gm": crit.gm, "gm_id": 12.0,
                   "gds": crit_gds, "kind": "nmos", "vds": _l4b_vds, "vsb": 0.0},
            "Mb": {"ID": crit.ID, "W": crit.W, "L": _l4b_L, "gm": crit.gm, "gm_id": 12.0,
                   "gds": crit_gds, "kind": "nmos", "vds": _l4b_vds, "vsb": 0.0},
            "Xa": {"ID": harm.ID, "W": harm.W, "L": _l4b_L, "gm": harm.gm, "gm_id": 15.0,
                   "gds": harm_gds, "kind": "nmos", "vds": _l4b_vds, "vsb": 0.0},
            "Xb": {"ID": harm.ID, "W": harm.W, "L": _l4b_L, "gm": harm.gm, "gm_id": 15.0,
                   "gds": harm_gds, "kind": "nmos", "vds": _l4b_vds, "vsb": 0.0},
        })

    _l4b_baseline_pair_area = 2 * _l4b_crit.W * _l4b_L
    _l4b_metrics = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}
    _l4b_constraints = [{"metric": "pair_area", "op": "<=", "value": _l4b_baseline_pair_area * 1.3}]
    _l4b_ctx1 = _l4b_ctx_for(_l4b_crit, _l4b_crit_gds, _l4b_harm, _l4b_harm_gds)
    _l4b_result1 = apply_and_revalidate_pair_adjustment(
        _l4b_transistors, _l4b_pairs, _l4b_ctx1, {"nmos": lut}, _l4b_metrics, _l4b_constraints,
        gm_id_bounds=(2.0, 28.0))
    assert _l4b_result1["applied"] and _l4b_result1["chosen"].names == ("Xa", "Xb"), \
        "1순위가 위반인데 2순위(Xa,Xb)로 자동 폴백하지 않음"
    assert len(_l4b_result1["rejected"]) == 1 and \
        _l4b_result1["rejected"][0]["suggestion"].names == ("Ma", "Mb") and \
        not _l4b_result1["rejected"][0]["revalidation"]["ok"] and \
        _l4b_result1["rejected"][0]["revalidation"]["violated_constraints"][0]["metric"] == "pair_area", \
        "거부된 후보 기록이 (Ma,Mb)/pair_area 위반과 정확히 일치하지 않음"
    _l4b_updated = {t.name: t.n_fingers for t in _l4b_result1["transistors"]}
    assert _l4b_updated == {"Ma": 1, "Mb": 1, "Xa": 2, "Xb": 2}, \
        "채택된 (Xa,Xb)만 n_fingers가 반영되고 나머지는 원본 그대로여야 함"

    _l4b_metrics_strict = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb", "Xa", "Xb"]}}
    _l4b_baseline_all_area = 2 * _l4b_crit.W * _l4b_L + 2 * _l4b_harm.W * _l4b_L
    _l4b_constraints_strict = [{"metric": "pair_area", "op": "<=", "value": _l4b_baseline_all_area * 1.05}]
    _l4b_ctx2 = _l4b_ctx_for(_l4b_crit, _l4b_crit_gds, _l4b_harm, _l4b_harm_gds)
    _l4b_result2 = apply_and_revalidate_pair_adjustment(
        _l4b_transistors, _l4b_pairs, _l4b_ctx2, {"nmos": lut}, _l4b_metrics_strict,
        _l4b_constraints_strict, gm_id_bounds=(2.0, 28.0))
    assert not _l4b_result2["applied"] and _l4b_result2["chosen"] is None, \
        "둘 다 위반인데 applied=True로 나옴"
    assert len(_l4b_result2["rejected"]) == 2, "두 후보 모두 시도(및 거부) 기록이 남아야 함"
    assert [t.n_fingers for t in _l4b_result2["transistors"]] == [1, 1, 1, 1], \
        "전부 거부됐으면 transistors가 원본과 동일해야 함"

    _l4b_result3 = apply_and_revalidate_pair_adjustment(
        _l4b_transistors, _l4b_pairs, _l4b_ctx1, {"nmos": lut}, _l4b_metrics, _l4b_constraints,
        gm_id_bounds=(2.0, 28.0), max_candidates=1)
    assert not _l4b_result3["applied"] and len(_l4b_result3["rejected"]) == 1, \
        "max_candidates=1인데 2순위까지 시도됨"


def test_s011_run_topology_pipeline_with_finger_fixup(toy_lut):
    """[L4c run_topology_pipeline_with_finger_fixup() -- 세션12 M3a 그룹(11소자) 실제
    connectivity를 topology.json으로 감싸 run_topology_pipeline() 전체 체인(load_topology->
    audit_row_split->build_stick_diagram->mirror_symmetric_trail)을 실제로 태워, euler-
    blocked 상태에서 M9b/M18b 핑거조정으로 자동 해결되는지 end-to-end로 확인]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S011(줄 314-435, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _l4c_m3a_netlist = [
        {"name": "M3a", "kind": "nmos", "source": "N3a4a", "drain": "Vom1", "gate": "Vbias3"},
        {"name": "M3b", "kind": "nmos", "source": "N3b4b", "drain": "Vop1", "gate": "Vbias3"},
        {"name": "M4a", "kind": "nmos", "source": "Vy", "drain": "N3a4a", "gate": "Vip"},
        {"name": "M4b", "kind": "nmos", "source": "Vy", "drain": "N3b4b", "gate": "Vim"},
        {"name": "M5", "kind": "nmos", "source": "gnd", "drain": "Vy", "gate": "Vbias4"},
        {"name": "M9b", "kind": "nmos", "source": "Vop1", "drain": "Vg15", "gate": "N14a14b"},
        {"name": "M10", "kind": "nmos", "source": "gnd", "drain": "Vop1", "gate": "Vbias4"},
        {"name": "M18b", "kind": "nmos", "source": "Vom1", "drain": "Vg25", "gate": "N24b23a"},
        {"name": "M19", "kind": "nmos", "source": "gnd", "drain": "Vom1", "gate": "Vbias4"},
        {"name": "M64", "kind": "nmos", "source": "N64_63", "drain": "Vbias3", "gate": "Vbias3"},
        {"name": "M63", "kind": "nmos", "source": "Vy", "drain": "N64_63", "gate": "Vbias3"},
    ]  # 세션12 M3a 그룹(.ai/context.md, stick_diagram.py Test 5.6)과 connectivity 동일
    _l4c_matching_pairs_meta = [
        {"names": ["M4a", "M4b"], "matching_sensitivity": "offset"},
        {"names": ["M3a", "M3b"], "matching_sensitivity": "ratio"},
        {"names": ["M10", "M19"], "matching_sensitivity": "ratio"},
        {"names": ["M9b", "M18b"], "matching_sensitivity": "ratio"},
    ]
    _l4c_row = "m3a_row"
    _l4c_L, _l4c_vds, _l4c_gm_id = 0.5e-6, 0.6, 12.0
    _l4c_r = size_transistor(gm=50e-6, gm_id=_l4c_gm_id, L=_l4c_L, lut=lut, vds=_l4c_vds)
    _l4c_gds = _l4c_r.gm / lut.gm_gds_ratio(_l4c_gm_id, _l4c_L, _l4c_vds, 0.0)
    _l4c_names = [d["name"] for d in _l4c_m3a_netlist]
    # 전부 n_fingers=1 baseline -- delta=-1은 new_n=0<1로 자동 무효화되므로(suggest_pair_
    # finger_adjustments() 내부 규칙), 이 self-test의 모든 후보는 항상 +1(면적 증가)만 나온다.
    _l4c_overrides = {n: {"n_fingers": 1, "finger_w": _l4c_r.W, "w": _l4c_r.W, "stack_id": _l4c_row}
                       for n in _l4c_names}
    _l4c_ctx = SizingContext(sized={
        n: {"ID": _l4c_r.ID, "W": _l4c_r.W, "L": _l4c_L, "gm": _l4c_r.gm, "gm_id": _l4c_gm_id,
            "gds": _l4c_gds, "kind": "nmos", "vds": _l4c_vds, "vsb": 0.0}
        for n in _l4c_names
    })
    _l4c_metrics = {"group_area": {"type": "sum_area", "devices": _l4c_names}}
    _l4c_baseline_area = len(_l4c_names) * _l4c_r.W * _l4c_L

    with _tempfile.TemporaryDirectory() as _l4c_tmpdir:
        _l4c_topo_path = _os.path.join(_l4c_tmpdir, "m3a_row.topology.json")
        with open(_l4c_topo_path, "w", encoding="utf-8") as _l4c_f:
            json.dump({
                "topology_name": "m3a_row_selftest",
                "schema_version": "2.0",
                "netlist": _l4c_m3a_netlist,
                "symmetry": {"matching_pairs": _l4c_matching_pairs_meta, "dispositions": []},
            }, _l4c_f)

        _l4c_constraints_a = [{"metric": "group_area", "op": "<=", "value": _l4c_baseline_area * 1.5}]
        _l4c_result_a = run_topology_pipeline_with_finger_fixup(
            _l4c_topo_path, _l4c_overrides, _l4c_ctx, {"nmos": lut}, _l4c_metrics, _l4c_constraints_a,
            gm_id_bounds=(2.0, 28.0))
        assert _l4c_result_a["unresolved_row"] is None and _l4c_result_a["unresolved_reason"] is None, \
            f"넉넉한 예산인데도 못 풀림: {_l4c_result_a['unresolved_row']}/{_l4c_result_a['unresolved_reason']}"
        assert _blocked_euler_rows(_l4c_result_a["audit_row_split"]) == [], \
            "euler 체크가 최종적으로 안 풀림 -- unresolved_row=None인데 실제로는 아직 blocked"
        assert len(_l4c_result_a["fixup_rounds"]) == 1, "1라운드에 바로 풀려야 하는데 라운드 수가 다름"
        _l4c_chosen_a = _l4c_result_a["fixup_rounds"][0]["result"]["chosen"]
        assert set(_l4c_chosen_a.names) == {"M9b", "M18b"} and _l4c_chosen_a.delta_fingers == 1, \
            f"채택된 조정이 M9b/M18b +1이 아님(세션12 손검증과 다름): {_l4c_chosen_a}"
        _l4c_final_n = {t.name: t.n_fingers for t in _l4c_result_a["transistors"]}
        assert _l4c_final_n["M9b"] == 2 and _l4c_final_n["M18b"] == 2, "M9b/M18b n_fingers가 2로 안 바뀜"

        _l4c_constraints_b = [{"metric": "group_area", "op": "<=", "value": _l4c_baseline_area * 1.001}]
        _l4c_result_b = run_topology_pipeline_with_finger_fixup(
            _l4c_topo_path, _l4c_overrides, _l4c_ctx, {"nmos": lut}, _l4c_metrics, _l4c_constraints_b,
            gm_id_bounds=(2.0, 28.0))
        assert _l4c_result_b["unresolved_row"] is None and _l4c_result_b["unresolved_reason"] is None, \
            f"그룹분할 폴백으로 euler는 항상 풀려야 하는데: " \
            f"{_l4c_result_b['unresolved_row']}/{_l4c_result_b['unresolved_reason']}"
        assert _blocked_euler_rows(_l4c_result_b["audit_row_split"]) == [], \
            "euler 체크가 최종적으로 안 풀림"
        assert len(_l4c_result_b["fixup_rounds"]) == 1 and \
            not _l4c_result_b["fixup_rounds"][0]["result"]["applied"], \
            "핑거조정 시도 자체는 여전히 1회 일어나고 여전히 실패해야 함(위반 후보 전부 거부)"
        assert len(_l4c_result_b["group_splits"]) == 1, \
            f"그룹분할이 정확히 1번 기록돼야: {_l4c_result_b['group_splits']}"
        _l4c_split_b = _l4c_result_b["group_splits"][0]
        assert _l4c_split_b["row"] == _l4c_row and _l4c_split_b["n_segments"] == 3 and \
            _l4c_split_b["crossover_count"] == 2 and \
            _l4c_split_b["node_pairing_fallback_used"] is False, \
            f"그룹분할 기록 내용이 실측과 다름: {_l4c_split_b}"
        _l4c_bc_pairs = sorted(sorted(v) for v in _l4c_split_b["branch_composites"].values())
        assert _l4c_bc_pairs == [["M3a", "M4a"], ["M3b", "M4b"]], \
            f"M3a/M4a, M3b/M4b branch가 crossover 짝짓기 전에 합성됐어야: " \
            f"{_l4c_split_b['branch_composites']}"
        _l4c_final_stack = {t.name: t.stack_id for t in _l4c_result_b["transistors"]}
        assert _l4c_final_stack["M3a"] == _l4c_final_stack["M4a"] == _l4c_final_stack["M5"], \
            f"M3a/M4a(branch composite)+M5가 같은 segment에 있어야: {_l4c_final_stack}"
        assert _l4c_final_stack["M3b"] == _l4c_final_stack["M4b"] == \
            _l4c_final_stack["M64"] == _l4c_final_stack["M63"], \
            f"M3b/M4b(branch composite)+M64/M63이 같은 segment에 있어야: {_l4c_final_stack}"
        assert not _l4c_result_b["audit_row_split"].ok, \
            "이 함수는 euler(체크1)만 고친다 -- 3b/3c 잔여 실패는 그대로 audit.ok=False에 반영돼야 " \
            "함(정직하게 남기기, 세션17 원칙과 동일 -- group_splits가 있다고 몰래 True로 안 둔갑)"

        _l4c_cell_groups = {"cellA": [_l4c_row, "other_row_not_present"]}
        _l4c_cell_groups_snapshot = {k: list(v) for k, v in _l4c_cell_groups.items()}
        _l4c_result_c = run_topology_pipeline_with_finger_fixup(
            _l4c_topo_path, _l4c_overrides, _l4c_ctx, {"nmos": lut}, _l4c_metrics, _l4c_constraints_b,
            gm_id_bounds=(2.0, 28.0), cell_groups=_l4c_cell_groups)
        assert _l4c_result_c["unresolved_row"] is None, \
            f"cell_groups가 있어도 그룹분할 폴백은 동일하게 성공해야: {_l4c_result_c['unresolved_row']}"
        assert _l4c_cell_groups == _l4c_cell_groups_snapshot, \
            f"호출자가 준 cell_groups 원본이 변형됨(순수함수 위반): {_l4c_cell_groups}"
        _l4c_cellA_checks = _l4c_result_c["audit_row_split"]["cellA"].checks
        _l4c_seg_euler_names = {c.name[len("1. euler["):-1] for c in _l4c_cellA_checks
                                 if c.name.startswith("1. euler[") and c.ok}
        assert _l4c_seg_euler_names == {"m3a_row_seg0", "m3a_row_seg1", "m3a_row_seg2"}, \
            f"cell_groups 자동확장이 안 돼 새 seg row가 cellA 감사에서 누락됨: {_l4c_seg_euler_names}"


def test_s012_optimize_full_circuit_budget(s011_state, toy_lut):
    """[L5 optimize_full_circuit_budget() 실배선 -- run_topology_pipeline_with_finger_
    fixup()을 harness 최상위(optimize_full_circuit_budget())에서 실제로 호출하는지
    end-to-end로 확인(세션15 실배선, .ai/context.md 참고) -- known_sizing으로 M3a
    11소자 W/ID를 직접 시드해(theta/device_roles 없이) A/B/C엔진을 우회하고, harness가
    euler-blocked를 자동으로 finger 조정으로 풀어 sizing/sizing_overrides에 반영하는지 확인]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S012(줄 436-532, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _l4c_L = s011_state._l4c_L
    _l4c_gds = s011_state._l4c_gds
    _l4c_gm_id = s011_state._l4c_gm_id
    _l4c_m3a_netlist = s011_state._l4c_m3a_netlist
    _l4c_matching_pairs_meta = s011_state._l4c_matching_pairs_meta
    _l4c_names = s011_state._l4c_names
    _l4c_r = s011_state._l4c_r
    _l4c_vds = s011_state._l4c_vds
    lut = toy_lut

    _ofcb_matching_pairs_meta = [{**p, "current_forced": False} for p in _l4c_matching_pairs_meta]
    # M4a/M4b(offset)와 M3a/M3b(ratio+shares_node=False=branch_symmetric, 세션15 probe로
    # audit 출력에서 확인)는 3c(common-centroid)가 필수 게이트다 -- n_fingers=1(baseline)로
    # 두면 repair_matching_safety()가 필요할 때 common_centroid_layout()의 무관한 기존
    # 한계(count>=n_rows=2 필요, 세션15 probe_preexisting_bug.py로 확인된 사전 존재 버그,
    # 이번 배선과 무관)에 걸려 이 배선 테스트 자체가 막힌다. M9b/M18b도 3c 필수 게이트지만
    # 그건 이 테스트가 검증하려는 euler-fixup 대상이라 baseline n_fingers=1로 그대로
    # 두고, fixup이 실제로 2로 올리는지를 확인한다.
    #
    # baseline을 짝수(2배)로 주면 그 소자의 그래프 홀짝 기여가 바뀌어(홀수 기여 -> 짝수
    # 기여) euler-blocked 판정 자체가 달라지는 걸 세션15 probe로 실측 확인했다(2배 시도 시
    # M9b/M18b+1로 안 풀리고 5라운드 소진 후 M5가 6핑거까지 발산) -- 그래서 홀짝을 보존하는
    # 3배(여전히 홀수)로 줘서 세션12/L4c와 동일하게 M9b/M18b+1 1라운드 성공을 유지하면서
    # count(=3)>=n_rows(=2)로 common-centroid 크래시만 피한다.
    # 2026-09-08(B16) -- M64는 이 넷리스트에서 `gate == drain == "Vbias3"`, 즉 **진짜
    # diode-connected**다(세션12의 실제 M3a 그룹 connectivity를 그대로 복사한 결과). 그런데
    # 이 픽스처는 11소자 전부에 같은 `gm_id=12 @ vds=0.6`을 시드하고 있었다 -- diode는
    # Vgs=Vds가 물리적으로 강제되므로 그 조합은 **불가능한 시드**다(vds=0.6V가 요구하는
    # gm_id는 21.3). `apply_diode_self_consistent_gm_id()`를 배선하면서 이 기존 오류가
    # 드러났다.
    #
    # 고치는 방향은 **vds 쪽**이다: gm_id/W를 바꾸면 이 테스트가 실제로 검증하려는
    # euler/finger fixup의 기하(W·L·n_fingers 의존)가 통째로 달라진다. vds만 옮기면
    # 기하는 그대로이고 물리만 맞는다. 값을 하드코딩하지 않고 LUT에서 유도하는 이유는
    # LUT이 바뀌면(공정 변경/앵커 추가) 이 값도 따라 움직여야 하기 때문이다.
    _l4c_m64_vds = solve_diode_connected_vds(lut, _l4c_gm_id, _l4c_L, 0.0)
    _l4c_m64_gds = _l4c_r.gm / lut.gm_gds_ratio(_l4c_gm_id, _l4c_L, _l4c_m64_vds, 0.0)
    _ofcb_known_sizing = {
        n: {"ID": _l4c_r.ID,
            "W": _l4c_r.W * (3 if n in ("M4a", "M4b", "M3a", "M3b") else 1), "L": _l4c_L,
            "gm": _l4c_r.gm, "gm_id": _l4c_gm_id,
            "gds": _l4c_m64_gds if n == "M64" else _l4c_gds, "kind": "nmos",
            "vds": _l4c_m64_vds if n == "M64" else _l4c_vds, "vsb": 0.0}
        for n in _l4c_names
    }
    _ofcb_baseline_area = sum(_ofcb_known_sizing[n]["W"] * _ofcb_known_sizing[n]["L"]
                               for n in _l4c_names)
    with _tempfile.TemporaryDirectory() as _ofcb_tmpdir:
        _ofcb_topo_path = _os.path.join(_ofcb_tmpdir, "m3a_row_ofcb.topology.json")
        with open(_ofcb_topo_path, "w", encoding="utf-8") as _ofcb_f:
            json.dump({
                "topology_name": "m3a_row_ofcb_selftest",
                "schema_version": "2.0",
                "netlist": _l4c_m3a_netlist,
                "symmetry": {"matching_pairs": _ofcb_matching_pairs_meta, "dispositions": []},
                "sizing_roles": {
                    # A12(2026-09-08) -- unit 필수. 이름에 단위 접미사가 없으므로 정규
                    # 단위 m^2를 그대로 선언한다(환산 계수 1.0이라 값은 불변).
                    "metrics": {"group_area": {"type": "sum_area", "unit": "m^2",
                                                "devices": _l4c_names}},
                    "constraints": [{"metric": "group_area", "op": "<=",
                                      "value": _ofcb_baseline_area * 1.5}],
                },
            }, _ofcb_f)
        _ofcb_spec = {
            "lut_by_kind": {"nmos": lut},
            "known_sizing": _ofcb_known_sizing,
            "stack_groups_override": {"m3a_row": _l4c_names},
            "min_finger_w": 0.1e-6, "max_finger_w": 40e-6,
            "gm_id_bounds": (2.0, 28.0),
            # 2026-08-14 -- load_topology()가 이제 propose_device_roles_gap_fill()을 자동
            # 배선해서(사용자 지시, 절대원칙) 이 fixture의 netlist에서도 L_role이 자동으로
            # 채워질 수 있다 -- 이 테스트는 known_sizing으로 device_roles를 완전히 우회하는
            # 시나리오를 검증하려는 것이지만, L_role 루프 자체는(권위 있는 소스가 아니면)
            # 여전히 도는다는 게 기존 계약이라 L_min이 없으면 크래시한다. 실제 스펙은 항상
            # L_min을 주므로(예: _spec_two_stage_ota()) 여기도 맞춘다.
            "L_min": 0.1e-6,
        }
        _ofcb_result = optimize_full_circuit_budget(_ofcb_topo_path, _ofcb_spec)
        assert _ofcb_result["pipeline_result"]["unresolved_row"] is None, \
            f"euler-blocked가 harness 경로에서 자동으로 안 풀림: " \
            f"{_ofcb_result['pipeline_result']['unresolved_row']}/" \
            f"{_ofcb_result['pipeline_result']['unresolved_reason']}"
        assert _blocked_euler_rows(_ofcb_result["pipeline_result"]["audit_row_split"]) == [], \
            "euler 체크가 최종적으로 안 풀림"
        assert _ofcb_result["sizing_overrides"]["M9b"]["n_fingers"] == 2 and \
            _ofcb_result["sizing_overrides"]["M18b"]["n_fingers"] == 2, \
            f"harness가 반환한 sizing_overrides에 finger 조정이 반영 안 됨: " \
            f"M9b={_ofcb_result['sizing_overrides']['M9b']}, M18b={_ofcb_result['sizing_overrides']['M18b']}"
        assert _ofcb_result["sizing"]["M9b"]["W"] != _ofcb_known_sizing["M9b"]["W"], \
            "harness가 반환한 sizing(gm/ID)에 finger 조정에 따른 W 변화가 반영 안 됨"
        # 세션18 -- matching quality(3b/3c) 자동수정도 이제 bare repair_matching_safety()가
        # 아니라 run_matching_safety_with_finger_growth()로 승격됐다(위 audit_ok=False 분기
        # 참고) -- growth_rounds가 실제로 채워지는지 확인해 새 배선이 이 경로에서도 실제로
        # 개입함을 검증(이 fixture는 M4a/M3a·M4b/M3b branch composite 내부에서 n_fingers가
        # 갈라져(growth_not_applicable) 실제 성장은 안 되지만, 시도 자체는 기록돼야 한다).
        assert "growth_rounds" in _ofcb_result["pipeline_result"] and \
            len(_ofcb_result["pipeline_result"]["growth_rounds"]) >= 1, \
            f"run_matching_safety_with_finger_growth()가 개입한 흔적(growth_rounds)이 없음: " \
            f"{_ofcb_result['pipeline_result'].get('growth_rounds')}"


def test_s013_resolve_stack_layout(library_dir):
    """[L5b resolve_stack_layout() -- declared vertical_stack_id를 audit_vertical_
    stack_id_vs_kcl()로 사전 검증하는 게이트(2026-08-10, 사용자 확정: review 대상
    있으면 명시적 에러). 실회로(정합) + 합성 fixture(원인불명 hub, 진짜 에러 유발)
    둘 다 확인]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S013(줄 533-586, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _rsl_lib = library_dir
    _rsl_trs, _rsl_meta = load_topology(
        _rsl_os.path.join(_rsl_lib, "current_reuse_telescopic_ota.topology.json"))
    _rsl_pairs_meta = _rsl_meta["symmetry"]["matching_pairs"]
    _rsl_forced = [tuple(p["names"]) for p in _rsl_pairs_meta if p["current_forced"]]
    _rsl_device_roles = {k: v for k, v in (_rsl_meta.get("device_roles") or {}).items()
                          if not k.startswith("_")}
    _rsl_groups = resolve_stack_layout(_rsl_trs, _rsl_forced, _rsl_device_roles)
    _rsl_declared_ok = all(v.get("vertical_stack_id") for v in _rsl_device_roles.values()
                            if isinstance(v, dict))
    assert _rsl_declared_ok, "이 fixture는 51/51 declared를 전제로 함(회귀 시 다른 검증으로 대체)"
    _rsl_all_members = sorted(m for members in _rsl_groups.values() for m in members)
    assert _rsl_all_members == sorted(t.name for t in _rsl_trs), \
        "감사 게이트 통과 후에도 소자 누락/중복 없어야 함"

    # 2026-08-11(세션28 후반부) -- resolve_stack_layout()이 이제 derive_horizontal_stack_
    # groups()를 거치므로(vertical_stack_id는 PMOS/NMOS를 섞을 수 있지만 물리 레이아웃 행은
    # 그럴 수 없음), 반환된 모든 그룹이 항상 kind 동질이어야 한다는 게 이 함수의 새 불변식이다
    # -- 이번 버그(build_graph()가 mixed-kind를 잡아내기 전엔 이 그룹이 조용히 PMOS/NMOS를
    # 섞고 있었음, 8/26개 declared vsid에서 실측 확인)의 재발 방지 가드.
    _rsl_by_name = {t.name: t for t in _rsl_trs}
    for _rsl_sid, _rsl_members in _rsl_groups.items():
        _rsl_kinds = {_rsl_by_name[m].kind for m in _rsl_members if m in _rsl_by_name}
        assert len(_rsl_kinds) <= 1, \
            f"resolve_stack_layout() 반환 그룹이 kind 동질이 아님(회귀 -- derive_horizontal_" \
            f"stack_groups() 배선 확인할 것): {_rsl_sid} -> {_rsl_members} -> {_rsl_kinds}"

    _rsl_bad_trs = [
        Transistor("T1", "pmos", source="vdd", drain="Na", gate="g1"),
        Transistor("T2", "nmos", source="gnd", drain="Na", gate="g2"),
        Transistor("T3", "pmos", source="vdd", drain="Nb", gate="g3"),
        Transistor("T4", "nmos", source="gnd", drain="Nb", gate="g4"),
    ]
    # T1/T2는 Na(2단자)로 진짜 직렬, T3/T4는 Nb(2단자)로 진짜 직렬 -- 서로 완전히 무관한
    # 두 그룹인데, declared vertical_stack_id는 T1/T3를 "fake_merged"로 잘못 합쳐놨다고
    # 가정(3+단자 허브도 전혀 없어 원인 불명 -- 진짜 선언 실수 시나리오).
    _rsl_bad_roles = {
        "T1": {"vertical_stack_id": "fake_merged"}, "T2": {"vertical_stack_id": "groupA_tail"},
        "T3": {"vertical_stack_id": "fake_merged"}, "T4": {"vertical_stack_id": "groupB_tail"},
    }
    with pytest.raises(ValueError) as e_info:
        resolve_stack_layout(_rsl_bad_trs, [], _rsl_bad_roles)
    e = e_info.value
    assert "vertical_stack_id" in str(e), f"에러 메시지가 원인을 안 가리킴: {e}"


def test_s014_section(library_dir, real_lut):
    """[L5c 헤드룸 singleton 정책(다음 세션 최우선①, 2026-08-11 세션28) -- M5/M61,
    M60/M66, M36a/M38, M18_bg(diode_reference, ideal_sources 대조 검증 포함),
    M7=M6/M36b=M36a(same_as_device) 전부를 실제 optimize_full_circuit_budget()
    으로 51소자 실회로 실행해 한 번에 검증. classab_centering_dev_v(세션27이
    이미 분리해둔 별개 미해결 항목)만 임시로 제외 -- 이번 검증 범위 밖]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S014(줄 587-830, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _l5c_lib = library_dir
    _l5c_lutfile = real_lut
    with open(_rsl_os.path.join(_l5c_lib, "current_reuse_telescopic_ota.topology.json"),
              "r", encoding="utf-8") as _l5c_f:
        _l5c_topo = json.load(_l5c_f)
    for _l5c_t in _l5c_topo["sizing_roles"]["theta"]:
        if _l5c_t["name"] == "K_replica":
            _l5c_t["bounds"] = [0.05, 0.05]
        elif _l5c_t["name"] == "r_classab_battery":
            _l5c_t["bounds"] = [0.3, 0.3]
        elif _l5c_t["name"] in ("L_stage2out_p", "L_stage2out_n"):
            # 2026-09-10(class-AB 배터리 KVL 배선 후) -- 중점(0.575um)이 물리적으로
            # 도달 불가능해졌다. 이 L에서는 출력단 VGS 합이 vdd를 넘어 배터리 몫
            # `V_bat = vdd - VGS(M15) - VGS(M16)`가 **음수**가 된다(실측 -0.024V) --
            # 지금까지는 그 KVL을 아무도 안 봐서 통과했을 뿐이고, `stack_kvl_vgs_limit()`
            # 배선 후에는 gm_id 탐색이 정확히 이 지점을 거부한다.
            #
            # 실측한 실현가능 구간은 **L <= 0.2um**이다(W 상한 200um과 VGS 상한이
            # 양립하는 구간). 그 안에서 이 픽스처의 선언된 제약 4개를 **전부** 만족하는
            # 값을 실제로 훑어 골랐다(tests/probe_l5c_stage2out_L.py + L_cascode 2D 스캔):
            #
            #     L_s2o=0.15um : cmrr 53.0~54.1  -> 어떤 L_cascode로도 60 미만
            #     L_s2o=0.175um: cmrr 55.6~57.0  -> 마찬가지
            #     L_s2o=0.20um : cmrr 58.9~60.04 -> **L_cascode >= 0.717um이면 전부 만족**
            #
            # 그래서 0.2um으로 고정하고, 아래 optimize_full_circuit_budget() 호출의
            # grid_points_per_theta를 1 -> 3으로 올린다(자유 theta가 L_cascode 하나뿐이라
            # 평가 3회면 된다). 격자가 1점이면 L_cascode가 중점 0.575um에 묶여 cmrr이
            # 59.86으로 **0.14dB 차이**로 떨어졌다 -- 제약을 지우지 않고 격자만 올려
            # 푼다(우회 금지 원칙: "우회 없이 고칠 방법이 있는가"에 답이 있었다).
            #
            # r_cmfb_vocdes(바로 아래)와 같은 성격의 고정이다 -- 픽스처 본연의 목적
            # (헤드룸 singleton KVL 검증)은 그대로 두고 고정점만 도달 가능한 값으로 옮긴다.
            # ⚠️ 이 값이 "최적"이라는 뜻은 아니다: 자유탐색(SLSQP)이 이 구간에 **도달하지
            # 못하는 것**은 별개 미해결 항목이다. 실측한 원인(2026-09-10):
            # `search_stage_budget_L_warm_start()`는 `presolve_warm_start()` 안에 이미
            # 배선돼 있고 실제로 돈다(6.1초). 그런데 그 스캔은 **다른 theta를 bounds-
            # midpoint에 고정한 채** L만 훑는데, 이 회로는 `r_cmfb_vocdes`가 중점(0.11)
            # 이면 **어떤 L도 성립하지 않는다**(M39/M40 적층 diode가 1.8V를 못 나눈다, B25).
            # 그래서 스캔점이 전부 크래시하고 조용히 bounds-midpoint(0.575um)로 후퇴한다 --
            # 실측 반환값이 정확히 그 값이고, notes에도 "baseline_theta_values 자체가
            # infeasible"이 전 theta에 걸쳐 남는다. 즉 (L_stage2out, r_cmfb_vocdes)는
            # **함께 움직여야 하는 쌍**이라 한 변수씩 훑는 스캔으로는 원리적으로 못 찾는다.
            _l5c_t["bounds"] = [2.0e-07, 2.0e-07]
        elif _l5c_t["name"] == "r_cmfb_vocdes":
            # 2026-09-09(B25 후속, 사용자 확정) -- 중점(0.11)이 아니라 **하한(0.02)**에
            # 고정한다. 중점은 CMFB 기준분배기 M39/M40에 8.197uA를 흘리는데, 이는 실제
            # 최적점(0.020000, 즉 하한)의 **17배**다. 바디효과를 제대로 넣은 뒤로는 그
            # 전류에서 M39/M40이 1.8V를 나눌 수 없다 -- 함께 푼 쌍의 최소합이 1.837V다
            # (B25). L로는 못 고친다: 0.375um면 파일럿만, 0.180um면 이 점만 성립해 두
            # 동작점을 동시에 만족하는 L이 없음을 실측 확인했다(계획 §10.3 B25).
            #
            # 즉 고정값 0.11 자체가 물리적으로 도달 불가능해진 것이라, 이 픽스처 본연의
            # 목적(헤드룸 singleton KVL 검증)을 지키면서 실제 설계가 고르는 값으로 옮긴다.
            # K_replica/r_classab_battery를 이미 특별 고정하고 있는 것과 같은 방식이다.
            _l5c_t["bounds"] = [0.02, 0.02]
        elif _l5c_t["name"] == "L_cascode":
            # 2026-09-10 -- 이 픽스처 머리말(세션42)은 "L_cascode를 **제외한** 모든 theta를
            # 중간값에 고정한다"라고 적고 있는데, 실제 코드는 아래 else가 L_cascode까지
            # 잡아 **자유도 0**이었다(그래서 grid_points_per_theta를 올려도 평가 횟수가
            # 그대로였다 -- 전부 lo==hi라 theta당 1점). 주석이 말하는 의도대로 되돌린다.
            #
            # 이게 필요한 이유: class-AB 배터리 KVL을 배선한 뒤 L_stage2out=0.2um에서
            # cmrr_estimate_db가 L_cascode에 민감해졌다 -- 중점(0.575um)이면 59.86으로
            # 제약(>=60)을 **0.14dB 차이**로 놓치고, 0.717um 이상이면 60.04로 통과한다
            # (2D 스캔 실측). 제약을 지우는 대신 이 자유도를 돌려주는 게 맞다.
            pass
        else:
            _l5c_lo, _l5c_hi = _l5c_t["bounds"]
            _l5c_mid = (_l5c_lo + _l5c_hi) / 2.0
            _l5c_t["bounds"] = [_l5c_mid, _l5c_mid]
    # 2026-08-12(세션30) -- gain_db도 classab_centering_dev_v와 같은 이유로 이 테스트의
    # constraints에서 뺀다: optimize_multistage()의 VDS 탐색이 이제 vertical_stack_id
    # 헤드룸을 반영해(근본수정, reserved_vds_for_other_stack_members() 참고) M1a 등의
    # VDS가 더 이상 물리적으로 불가능한 값(예: vdd 전체)을 자유롭게 고르지 못한다 -- 그
    # 결과 이 테스트가 K_replica/r_classab_battery만 자유고 나머지 전부 midpoint 고정한
    # **단일** theta 점에서 gain_db가 74.9dB로 살짝 낮아졌다(75.6 미달). 이 테스트의
    # 목적은 애초에 gain 최적화가 아니라 헤드룸 singleton KVL 검증뿐이고(아래 vy_tail/
    # vbias4/cmfb 합=vdd assert), 실제 gain 최적화는 세션29 SLSQP 검증(자유 theta 탐색,
    # gain_db=84.15dB 달성)의 몫이다.
    _l5c_topo["sizing_roles"]["constraints"] = [
        c for c in _l5c_topo["sizing_roles"]["constraints"]
        # 2026-09-10(§7.11 L2) -- `parasitic_pm_deg`도 같은 이유로 뺀다. 이 제약은
        # **L의 상한**(L↑ -> Cgg↑ -> 노드 pole↓ -> PM↓)이라 L을 자유롭게 고를 수 있어야
        # 만족할 수 있는데, 이 픽스처는 거의 모든 theta를 중점에 고정한 인위적 한 점이다
        # (여기서 51.06도). 반면 **실제 자유탐색은 71.87도로 만족한다**(정본 spec + SLSQP,
        # 보상망 전체 포함). 즉 제약이 과한 게 아니라 이 픽스처가 그걸 검증할 자리가
        # 아니다 -- 이 픽스처가 보는 것은 헤드룸 singleton KVL이고 그건 아래 assert들이
        # 그대로 검증한다. `classab_centering_dev_v`/`gain_db`를 뺀 것과 같은 판단이다.
        # 2026-09-10(사용자 지시로 상한 신설) -- `mirror_ratio_error_mV`도 같은 이유로
        # 뺀다. 이 metric은 ratio 쌍의 **VDS 차이 / V_A / (gm/ID)**이고 `V_A = ID/gds`는 L에
        # 비례한다 -- 즉 L을 자유롭게 고를 수 있어야 만족할 수 있는데, 이 픽스처는 거의 모든
        # theta를 중점에 고정한 인위적 한 점이다. 반면 **실제 자유탐색은 만족한다**(정본
        # spec + SLSQP, 이 제약을 켠 상태에서 측정) -- 즉 제약이 과한 게 아니라 이 픽스처가
        # 그걸 검증할 자리가 아니다. 위 세 metric을 뺀 것과 같은 판단이고, 근거 제시 방식도
        # 같다(픽스처 값 vs 자유탐색 값을 나란히 적는다).
        # 2026-09-10 -- `mismatch_sigma_mV`도 뺀다. 이유는 위 넷과 **다르다**: 이 제약은
        # 임계값을 `value_from_achievable`로 유도하는데, 그 유도는 **정본 spec 지문**에
        # 묶여 사이드카에 저장된다(`derived_bounds_path()`). 이 픽스처는 임시 경로 + 다른
        # 격자(spec)를 쓰므로 그 유도가 적용될 수 없다 -- 엔진이 "옛 값을 조용히 쓰지 않고"
        # 거부하는 게 **맞는 동작**이고, 이 픽스처가 그걸 검증할 자리가 아닐 뿐이다.
        # (정본 spec에서는 정상 해석된다 -- run_harness 실측.)
        if c["metric"] not in ("classab_centering_dev_v", "gain_db", "parasitic_pm_deg",
                               "mirror_ratio_error_mV", "mismatch_sigma_mV")]
    with _tempfile.TemporaryDirectory() as _l5c_tmpdir:
        _l5c_topo_path = _rsl_os.path.join(_l5c_tmpdir, "current_reuse_telescopic_ota.l5c.json")
        with open(_l5c_topo_path, "w", encoding="utf-8") as _l5c_f:
            json.dump(_l5c_topo, _l5c_f)
        _l5c_d = np.load(_l5c_lutfile)
        _l5c_nmos = SemiEmpiricalGmIdLUT(_l5c_d["L"], _l5c_d["VGS"], _l5c_d["VDS"], _l5c_d["VS"],
                                          _l5c_d["ID_n"], _l5c_d["GM_n"], _l5c_d["GDS_n"], _l5c_d["CGG_n"],
                                          W_ref=5e-6, SID_1F=_l5c_d["SID_1F_n"])
        _l5c_pmos = SemiEmpiricalGmIdLUT(_l5c_d["L"], _l5c_d["VGS"], _l5c_d["VDS"], _l5c_d["VS"],
                                          _l5c_d["ID_p"], _l5c_d["GM_p"], _l5c_d["GDS_p"], _l5c_d["CGG_p"],
                                          W_ref=5e-6, SID_1F=_l5c_d["SID_1F_p"])
        _l5c_spec = {
            "lut_by_kind": {"nmos": _l5c_nmos, "pmos": _l5c_pmos}, "lut": _l5c_nmos, "vdd": 1.8,
            "L_candidates": [float(v) for v in _l5c_nmos.L_grid],
            # 2026-09-03(세션43) -- 24칸씩 건너뛰면 3점(0.0/0.9/1.8)뿐이라 diffpair_top_a/
            # bottom_a의 정확한 cap(reserved_vds_for_other_stack_members() 재귀 확장,
            # ≈0.6V)이 물리적으로 무의미한 0.0V 하나만 남겨 이 픽스처 자체가 통째로
            # infeasible해졌다(로직 결함이 아니라 이 3점 격자가 새 cap을 못 담을 만큼
            # 성겼던 것) -- 4칸씩(0.15V 간격, 13점)으로 촘촘히 해 cap 윈도우 안에도 정상
            # 후보가 있게 한다.
            "VDS_candidates": [float(v) for v in _l5c_nmos.VDS_grid[::4]],
            "gm_id_grid": [4.0, 8.0, 12.0, 16.0, 20.0, 24.0],
            "L_min": 0.15e-6, "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
            "W_bounds": (1e-6, 200e-6), "min_vds_by_role": {"cascode": 0.2, "tail": 0.3, "mirror": 0.3},
            "stage_objective": "power", "stage_w_max": 200e-6,
            "min_finger_w": 1e-6, "max_finger_w": 40e-6,
            "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
            "t_lln": 30e-9, "PM_target_deg": 70.0,
            "Cc": 500e-15, "Cf": 500e-15, "Cs": 500e-15, "C_Ltot": 1e-12,
            "t_settle_total": 40e-9, "omega_c": 6.9 / 30e-9,
            # 2026-09-10 -- L_cascode를 (주석이 말하던 의도대로) 자유로 되돌리자 이 spec에
            # `L_grid_step`이 없다는 게 처음 드러났다: 자유 L theta가 하나도 없던 동안은
            # `_theta_grid_points()`의 이 요구가 실행될 일이 없었다. 정본
            # (`run_harness.L_GRID_STEP`)과 같은 값을 쓴다 -- 픽스처만 다른 레이아웃 격자를
            # 쓸 이유가 없다.
            "L_grid_step": 5e-9,
        }
        # 2026-08-24(세션42) -- L_cascode를 제외한 모든 theta를 자기 bounds의 "중간값"에
        # 강제 고정하는 이 L5c 시나리오는(K_replica=0.05/r_classab_battery=0.3 등도 임의
        # 고정) 진짜 최적화가 아니라 임의의 한 점일 뿐이다. `budget_reference_device`
        # list 확장(세션42, 사용자 지시 옵션1)으로 diffpair_top_a/bottom_a의 KVL이 이제
        # 제대로 검증되는데, 이 임의 조합에서는 compensation이 고른 M1a/M4a 값과 headroom/
        # theta가 독립적으로 고른 M6/M2a/M3a/M5 값이 우연히 vdd로 안 닫힌다 -- **실제
        # SLSQP 자유탐색(run_harness.py current_reuse_telescopic_ota)으로 재확인한 결과
        # 이 두 그룹은 정상적으로 vdd에 닫힌다**(diffpair 관련 에러 없음, `.ai/context.md`
        # 세션42 참고) -- 즉 이건 L5c 픽스처 자체의 인위성이지 진짜 설계 결함이 아니다.
        # 다른 이유로 실패하면(예: output_stage_a -- compensation의 AC 스테이지 분리가
        # DC KVL과 실제로 상충하는, session29/30부터 이미 알려진 별개의 미해결 갭) 그건
        # 조용히 넘기지 않고 그대로 크래시시킨다.
        # 2026-09-03(세션43) -- `reserved_vds_for_other_stack_members()`가 diffpair_top_a/
        # bottom_a의 sibling(M2a/M3a)이 참조하는 나머지 소자(M6/M3a-or-M1a/M4a/M5)까지
        # 재귀적으로 반영해 M1a/M4a의 VDS grid를 정확히 캡핑하도록 근본수정됐다(더 이상
        # M1a=1.5V처럼 명백히 과도한 값을 독립적으로 못 고름). 그런데 **이 L5c 픽스처만**
        # `VDS_candidates=[0.0, 0.9, 1.8]`(LUT 격자를 24칸씩 건너뛴 극도로 성긴 3점) 인데,
        # 새로 계산된 cap(≈0.6V)이 이 성긴 격자에서 물리적으로 무의미한 `0.0V` 하나만 남겨
        # `find_optimal_sizing()`이 그 자체로 실행가능점을 못 찾는다 -- 실제 production
        # spec(수백 점 격자)에서는 cap 안에 정상 후보가 얼마든지 있으므로 이 실패는 진짜
        # 설계 결함이 아니라 이 픽스처의 격자 성김(coarseness)이 만든 인위적 한계다(위
        # diffpair KVL 불일치와 뿌리가 같음 -- 둘 다 "L5c가 K_replica/r_classab_battery만
        # 자유고 나머지 전부 임의 고정"이라는 이 픽스처 자체의 인위성에서 나옴).
        # 2026-09-10 -- 1 -> 3. 자유 theta가 `L_cascode` 하나뿐이라 평가 3회다.
        # 1점이면 L_cascode가 bounds 중점(0.575um)에 묶여 cmrr_estimate_db가 59.86으로
        # 제약(>=60)을 0.14dB 차이로 놓친다(위 L_stage2out 주석의 2D 스캔 참고).
        # 2026-09-10(사용자 선택 "레이아웃까지 가지 않게 분리") -- 이 픽스처가 검증하는
        # 것은 헤드룸 singleton KVL(M5/M61, M60/M66, M36a/M38, M18_bg, same_as_device)
        # 이고 그건 전부 **사이징 단계**에서 끝난다. 레이아웃(핑거 배정)은 별개 관심사라
        # `stop_after_sizing=True`로 거기까지 가지 않는다.
        _l5c_result = optimize_full_circuit_budget(
            _l5c_topo_path, _l5c_spec, grid_points_per_theta=3, stop_after_sizing=True)
    assert _l5c_result is not None  # spec card 계약 4: head 이관본 실행 출력에 이 섹션의 '참고(정직한 한계' 줄이 없다(성공 분기)
    _l5c_sizing = _l5c_result["sizing"]
    _l5c_vy_tail = sum(_l5c_sizing[n]["vds"] for n in ("M61", "M64", "M63", "M5"))
    _l5c_vbias4 = _l5c_sizing["M60"]["vds"] + _l5c_sizing["M66"]["vds"]
    _l5c_cmfb = _l5c_sizing["M36a"]["vds"] + _l5c_sizing["M37a"]["vds"] + _l5c_sizing["M38"]["vds"]
    for _l5c_name, _l5c_sum in (("vy_tail(M61+M64+M63+M5)", _l5c_vy_tail),
                                 ("vbias4(M60+M66)", _l5c_vbias4),
                                 ("cmfb(M36a+M37a+M38)", _l5c_cmfb)):
        assert abs(_l5c_sum - 1.8) < 1e-6, f"{_l5c_name} 합이 vdd(1.8V)와 불일치(회귀): {_l5c_sum}"
    # 2026-09-08(B16) -- 예전 단정은 `vds < 0.5`라는 **임의 상수**였다. 의도(세션28)는
    # "M18_bg가 ~vdd를 통째로 받던 회귀가 재발하지 않는지"였지만, 0.5라는 문턱 자체는
    # "diode_reference는 얇게 받는다"는 role 기반 믿음에서 나온 값이고 그건 이 재설계가
    # 고치는 대상이다. M18_bg는 diode-connected라 vds가 W를 정하는 종속값이고, 실제
    # 물리가 요구하는 값은 0.75V다(0.5보다 크다).
    #
    # 그래서 상수 대신 **물리 구간**으로 검사한다 -- 훨씬 강한 검사다(단순히 "작다"가
    # 아니라 "제작 가능한 폭이 나오는 구간 안에 있다").
    _l5c_bg = _l5c_sizing["M18_bg"]
    _l5c_bg_lo, _l5c_bg_hi = diode_vds_window(
        _l5c_spec["lut_by_kind"][_l5c_bg["kind"]], _l5c_bg["kind"],
        _l5c_bg["L"], _l5c_bg["ID"], _l5c_bg.get("vsb", 0.0),
        tuple(_l5c_spec.get("W_bounds", (1e-6, 200e-6))))
    assert _l5c_bg_lo is not None and _l5c_bg_lo <= _l5c_bg["vds"] <= _l5c_bg_hi, \
        (f"M18_bg(diode-connected)의 vds={_l5c_bg['vds']}가 W 한계가 허용하는 구간 "
         f"[{_l5c_bg_lo}, {_l5c_bg_hi}] 밖이다(회귀)")
    assert _l5c_bg["vds"] < 0.9 * 1.8, \
        f"M18_bg가 ~vdd를 통째로 받는 세션28 회귀가 재발함: {_l5c_bg['vds']}"

    _l5c_neg_topo = json.loads(json.dumps(_l5c_topo))  # deep copy
    _l5c_neg_topo["ideal_sources"] = []
    with _tempfile.TemporaryDirectory() as _l5c_neg_tmpdir:
        _l5c_neg_path = _rsl_os.path.join(_l5c_neg_tmpdir, "current_reuse_telescopic_ota.l5c_neg.json")
        with open(_l5c_neg_path, "w", encoding="utf-8") as _l5c_neg_f:
            json.dump(_l5c_neg_topo, _l5c_neg_f)
        with pytest.raises(ValueError) as _l5c_neg_e_info:
            optimize_full_circuit_budget(_l5c_neg_path, _l5c_spec, grid_points_per_theta=1)
        _l5c_neg_e = _l5c_neg_e_info.value
        assert "M18_bg" in str(_l5c_neg_e) and "ideal_sources" in str(_l5c_neg_e), \
            f"에러 메시지가 원인을 안 가리킴: {_l5c_neg_e}"

    assert abs(_l5c_sizing["M7"]["vds"] - _l5c_sizing["M6"]["vds"]) < 1e-9, \
        f"M7(same_as_device=M6)이 M6과 다른 값을 받음(회귀): M6={_l5c_sizing['M6']['vds']}, " \
        f"M7={_l5c_sizing['M7']['vds']}"
    assert abs(_l5c_sizing["M36b"]["vds"] - _l5c_sizing["M36a"]["vds"]) < 1e-9, \
        f"M36b(same_as_device=M36a)가 M36a와 다른 값을 받음(회귀): M36a={_l5c_sizing['M36a']['vds']}, " \
        f"M36b={_l5c_sizing['M36b']['vds']}"


def test_s015_suggest_matching_finger_growth(assets_dir, toy_lut):
    """[L4d suggest_matching_finger_growth()/apply_and_revalidate_matching_finger_growth()/
    run_matching_safety_with_finger_growth() -- 세션16 2번. repair_matching_safety()가
    branch 복합 매칭(세션16 1번)으로도 못 푸는 3c(n_fingers 부족)를, gm/ID를 깨지 않는
    선에서 핑거를 늘려 자동으로 완전히 풀 수 있는지]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S015(줄 831-936, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _l4d_L, _l4d_vds = 0.5e-6, 0.6
    _l4d_r = size_transistor(gm=200e-6, gm_id=12.0, L=_l4d_L, lut=lut, vds=_l4d_vds)
    _l4d_gds = _l4d_r.gm / lut.gm_gds_ratio(12.0, _l4d_L, _l4d_vds, 0.0)

    _l4d_g_trs = [Transistor("Ma", "nmos", source="s", drain="d1", n_fingers=1, finger_w=_l4d_r.W),
                  Transistor("Mb", "nmos", source="s", drain="d2", n_fingers=1, finger_w=_l4d_r.W)]
    _g1 = suggest_matching_finger_growth(("Ma", "Mb"), _l4d_g_trs, min_fingers=2)
    assert _g1 == {"names": ("Ma", "Mb"), "delta_fingers": 1,
                    "note": "common-centroid 회전-최적 경로(residual=0)를 위해 n_fingers 1->2"}
    _g2_trs = [Transistor("Mc", "nmos", source="s", drain="d1", n_fingers=2, finger_w=_l4d_r.W),
               Transistor("Md", "nmos", source="s", drain="d2", n_fingers=2, finger_w=_l4d_r.W)]
    assert suggest_matching_finger_growth(("Mc", "Md"), _g2_trs, min_fingers=2) is None, \
        "이미 n_fingers=2(충분)인데 growth를 제안함"
    _g3_trs = [Transistor("Me", "nmos", source="s", drain="d1", n_fingers=1, finger_w=_l4d_r.W),
               Transistor("Mf", "nmos", source="s", drain="d2", n_fingers=3, finger_w=_l4d_r.W)]
    assert suggest_matching_finger_growth(("Me", "Mf"), _g3_trs, min_fingers=2) is None, \
        "names 내부 n_fingers가 서로 다른데(1,3) growth를 제안함 -- 호출자 책임 밖 케이스"

    _l4d_transistors = [
        Transistor("Ma", "nmos", source="Na1", drain="Nb1", gate="ga",
                   n_fingers=1, finger_w=_l4d_r.W),
        Transistor("Mb", "nmos", source="Na2", drain="Nb2", gate="gb",
                   n_fingers=1, finger_w=_l4d_r.W),
    ]
    _l4d_ctx = SizingContext(sized={
        "Ma": {"ID": _l4d_r.ID, "W": _l4d_r.W, "L": _l4d_L, "gm": _l4d_r.gm, "gm_id": 12.0,
               "gds": _l4d_gds, "kind": "nmos", "vds": _l4d_vds, "vsb": 0.0},
        "Mb": {"ID": _l4d_r.ID, "W": _l4d_r.W, "L": _l4d_L, "gm": _l4d_r.gm, "gm_id": 12.0,
               "gds": _l4d_gds, "kind": "nmos", "vds": _l4d_vds, "vsb": 0.0},
    })
    _l4d_baseline_area = 2 * _l4d_r.W * _l4d_L

    _l4d_metrics = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}
    _l4d_loose = [{"metric": "pair_area", "op": "<=", "value": _l4d_baseline_area * 3.0}]
    _l4d_r1 = apply_and_revalidate_matching_finger_growth(
        ("Ma", "Mb"), _l4d_transistors, _l4d_ctx, {"nmos": lut}, _l4d_metrics, _l4d_loose,
        gm_id_bounds=(2.0, 28.0))
    assert _l4d_r1["applied"] and _l4d_r1["growth"]["delta_fingers"] == 1
    assert {t.name: t.n_fingers for t in _l4d_r1["transistors"]} == {"Ma": 2, "Mb": 2}
    assert _l4d_r1["revalidation"]["ok"]

    _l4d_tight = [{"metric": "pair_area", "op": "<=", "value": _l4d_baseline_area * 1.05}]
    _l4d_r2 = apply_and_revalidate_matching_finger_growth(
        ("Ma", "Mb"), _l4d_transistors, _l4d_ctx, {"nmos": lut}, _l4d_metrics, _l4d_tight,
        gm_id_bounds=(2.0, 28.0))
    assert not _l4d_r2["applied"] and _l4d_r2["revalidation"] is not None and \
        not _l4d_r2["revalidation"]["ok"]
    assert [t.n_fingers for t in _l4d_r2["transistors"]] == [1, 1], \
        "거부됐는데 transistors가 원본과 다름"

    _l4d_m6_trs, _l4d_m6_meta = load_topology(
        _os.path.join(assets_dir, "library",
                       "current_reuse_telescopic_ota.topology.json"))
    _l4d_m6_by_name = {t.name: t for t in _l4d_m6_trs}
    _l4d_m6_names = ["M1a", "M1b", "M2a", "M2b", "M6", "M7"]
    _l4d_m6_row = [_dc_replace(_l4d_m6_by_name[n], n_fingers=1, finger_w=_l4d_r.W, stack_id="seg1")
                   for n in _l4d_m6_names]
    _l4d_m6_pairs = [("M1a", "M1b"), ("M2a", "M2b")]
    _l4d_m6_sensitivity = {("M1a", "M1b"): "offset", ("M2a", "M2b"): "ratio"}
    _l4d_m6_ctx = SizingContext(sized={
        n: {"ID": _l4d_r.ID, "W": _l4d_r.W, "L": _l4d_L, "gm": _l4d_r.gm, "gm_id": 12.0,
            "gds": _l4d_gds, "kind": "pmos", "vds": _l4d_vds, "vsb": 0.0}
        for n in _l4d_m6_names
    })
    _l4d_m6_metrics = {"group_area": {"type": "sum_area", "devices": _l4d_m6_names}}
    _l4d_m6_baseline_area = sum(_l4d_r.W * _l4d_L for _ in _l4d_m6_names)
    _l4d_m6_constraints = [{"metric": "group_area", "op": "<=", "value": _l4d_m6_baseline_area * 3.0}]

    _l4d_final = run_matching_safety_with_finger_growth(
        {"seg1": _l4d_m6_row}, _l4d_m6_pairs, _l4d_m6_sensitivity, _l4d_m6_ctx, {"pmos": lut},
        _l4d_m6_metrics, _l4d_m6_constraints, gm_id_bounds=(2.0, 28.0))
    assert _l4d_final["unresolved_pair"] is None, \
        f"핑거증가로 3c 관점에서는 완전히 풀려야 하는데 못 풂: {_l4d_final['unresolved_pair']}/" \
        f"{_l4d_final['unresolved_reason']}"
    # unresolved_pair=None이 audit.ok=True의 동의어가 아니라는 걸 위 docstring에서 명시했다 --
    # 실제로 이 케이스는 3b/3c는 전부 풀리지만 "2. box-shape"(M6/M7만 남은 행과의 폭 비율)가
    # 별도로 FAIL한다(이 함수의 책임 밖, 세션16에서 실측 확인) -- 그래서 전체 audit.ok가
    # 아니라 "3b/3c 필수 게이트가 전부 PASS인지"를 직접 확인한다.
    _l4d_bad_matching_checks = [c for c in _l4d_final["audit"].checks
                                 if not c.ok and "[참고용" not in c.name
                                 and (c.name.startswith("3b.") or c.name.startswith("3c."))]
    assert not _l4d_bad_matching_checks, \
        f"3b/3c 필수 게이트가 아직 FAIL: {_l4d_bad_matching_checks}"
    # common_centroid_layout()의 회전-최적 경로는 n_fingers=2인 소자를 "2개 행에 1개씩"으로
    # 물리적으로 나눠 배치한다(진짜 common-centroid) -- 그래서 rows에는 같은 이름이 여러 행에
    # 걸쳐 n_fingers=1짜리로 여러 번 나타난다. 총 finger 수는 행별로 합산해야 한다(이름 하나에
    # 값 하나만 남기는 flat dict는 나중 행 값으로 덮어써버려 틀린다).
    _l4d_total_n = {}
    for devs in _l4d_final["rows"].values():
        for t in devs:
            _l4d_total_n[t.name] = _l4d_total_n.get(t.name, 0) + t.n_fingers
    assert _l4d_total_n["M1a"] == _l4d_total_n["M1b"] == \
        _l4d_total_n["M2a"] == _l4d_total_n["M2b"] == 2, \
        f"M1a/M1b/M2a/M2b 총 n_fingers가 전부 2로 안 자람: {_l4d_total_n}"


def test_s016_run_matching_safety_with_finger_growth(s015_state, toy_lut):
    """[L4e run_matching_safety_with_finger_growth() -- 세션17 설계안 3번. gm/ID 예산이
    타이트해서 핑거증가 자체가 거부되면(gm_id_violation), 인접배치(3b)로 최후수단

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S016(줄 937-982, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _l4d_ctx = s015_state._l4d_ctx
    _l4d_metrics = s015_state._l4d_metrics
    _l4d_r = s015_state._l4d_r
    _l4d_tight = s015_state._l4d_tight
    lut = toy_lut

    _l4e_devices = [
        Transistor("Ma", "nmos", source="Vtail", drain="Nd_a", gate="ga",
                   n_fingers=1, finger_w=_l4d_r.W),
        Transistor("Mb", "nmos", source="Vtail", drain="Nd_b", gate="gb",
                   n_fingers=1, finger_w=_l4d_r.W),
    ]
    _l4e_r1 = run_matching_safety_with_finger_growth(
        {"seg1": _l4e_devices}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, _l4d_ctx,
        {"nmos": lut}, _l4d_metrics, _l4d_tight, gm_id_bounds=(2.0, 28.0),
        allow_layout_relaxation=True)
    assert _l4e_r1["unresolved_pair"] is None and \
        _l4e_r1["unresolved_reason"] == "relaxed_to_layout", \
        f"완화가 적용돼야 하는데 안 됨: {_l4e_r1['unresolved_pair']}/{_l4e_r1['unresolved_reason']}"
    assert len(_l4e_r1["relaxed_pairs"]) == 1 and \
        _l4e_r1["relaxed_pairs"][0]["pair"] == ("Ma", "Mb") and \
        _l4e_r1["relaxed_pairs"][0]["reason"] == "gm_id_budget_exceeded" and \
        _l4e_r1["relaxed_pairs"][0]["trim_recommended"] is True, \
        f"relaxed_pairs 내용이 예상과 다름: {_l4e_r1['relaxed_pairs']}"
    assert _l4e_r1["relaxed_pairs"][0]["interdig_ok"] is not None, \
        "완화 후 재감사가 한 번 더 돌아야 interdig_ok가 채워짐 -- 여전히 None"
    # 완화는 3c 요구사항 자체를 없애지 않는다 -- offset pair는 여전히 3c가 필수 게이트이므로
    # n_fingers=1인 이상 기하학적으로 dx<=0.5를 달성 못 해(세션16 D-3) audit.ok는 False여야
    # 한다(위 docstring "완화는 3c 요구사항을 없애지 않는다" 참고, 몰래 성공으로 둔갑 금지).
    assert not _l4e_r1["audit"].ok, "완화됐다고 audit.ok가 몰래 True로 둔갑함 -- 정책 위반"
    _l4e_3c_check = next(c for c in _l4e_r1["audit"].checks
                          if c.name.startswith("3c.") and "[Ma/Mb]" in c.name)
    assert not _l4e_3c_check.ok and "[참고용" not in _l4e_3c_check.name, \
        f"3c[Ma/Mb]가 여전히 필수 게이트로 FAIL이어야 하는데: {_l4e_3c_check}"
    assert len(_l4e_r1["growth_rounds"]) == 1 and not _l4e_r1["growth_rounds"][0]["result"]["applied"], \
        "growth 시도가 정확히 1번, 실패로 기록돼야 함"

    _l4e_r2 = run_matching_safety_with_finger_growth(
        {"seg1": list(_l4e_devices)}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, _l4d_ctx,
        {"nmos": lut}, _l4d_metrics, _l4d_tight, gm_id_bounds=(2.0, 28.0),
        allow_layout_relaxation=False)
    assert _l4e_r2["unresolved_pair"] == ("Ma", "Mb") and \
        _l4e_r2["unresolved_reason"] == "gm_id_violation" and \
        _l4e_r2["relaxed_pairs"] == [], \
        f"allow_layout_relaxation=False인데 완화가 적용됨(회귀): {_l4e_r2}"


def test_s018_allocate_stack_headroom():
    """# 배치 7-3b/e/f(analog-topology-json-library.do.md, 2026-07-31) -- # allocate_stack_headroom()/search_gm_id_for_role()/derive_role_L()

    [7-3b allocate_stack_headroom() -- resize.py 6개 소자 스택, vdd=1.8V]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S018(줄 987-1000, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _hr_stack = [
        {"name": "M6", "role": "tail",     "min_vds": 0.30},
        {"name": "M1", "role": "input",    "min_vds": 0.40},
        {"name": "M2", "role": "cascode",  "min_vds": 0.20},
        {"name": "M3", "role": "cascode",  "min_vds": 0.20},
        {"name": "M4", "role": "input",    "min_vds": 0.40},
        {"name": "M5", "role": "tail",     "min_vds": 0.30},
    ]
    _hr_result = allocate_stack_headroom(1.8, _hr_stack)
    assert abs(_hr_result["M2"] - 0.20) < 1e-12 and abs(_hr_result["M3"] - 0.20) < 1e-12, \
        "cascode에 min_vds가 그대로 안 쓰임"
    assert abs(sum(_hr_result.values()) - 1.8) < 1e-9, "배정 합이 vdd(1.8V)와 불일치"


def test_s019_section(s018_state):
    """[gm_id가 있으면 2/gm_id+margin으로 캐스코드 헤드룸이 자동 연동되는지(§7-3e (b))]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S019(줄 1002-1012, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _hr_stack = s018_state._hr_stack

    _hr_stack2 = [dict(e) for e in _hr_stack]
    for _e in _hr_stack2:
        if _e["role"] == "cascode":
            _e["gm_id"] = 17.0  # sky130 실측 min-L NMOS 정점 부근값(참고용 예시)
    _hr_result2 = allocate_stack_headroom(1.8, _hr_stack2)
    _expected_cascode_v = 2.0 / 17.0 + 0.05
    assert abs(_hr_result2["M2"] - _expected_cascode_v) < 1e-9, "gm_id 연동 헤드룸 계산 오류"
    assert abs(sum(_hr_result2.values()) - 1.8) < 1e-9, "gm_id 연동 시에도 합이 vdd와 불일치"


def test_s020_section():
    """[2026-08-11(세션28) HeadroomPolicy.thin_roles -- 'diode_reference'도 cascode와
    동급으로 얇게 배정받는지(M18_bg 실사례: diode-connected 기준전압 생성기,
    '남는 예산을 나눠 가질 파트너'가 없어 min_vds만 필요). voltage_divider(M39/M40)
    처럼 의도적으로 남는 예산을 나눠 갖는 role은 여전히 그대로 동작하는지도 함께 확인]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S020(줄 1013-1035, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _hr_stack3 = [
        {"name": "Mref", "role": "diode_reference", "min_vds": 0.20},
        {"name": "Mtail", "role": "tail", "min_vds": 0.30},
        {"name": "Minput", "role": "input", "min_vds": 0.40},
    ]
    _hr_result3 = allocate_stack_headroom(1.8, _hr_stack3)
    assert abs(_hr_result3["Mref"] - 0.20) < 1e-12, \
        f"diode_reference에 min_vds가 그대로 안 쓰임(thin_roles 배선 확인): {_hr_result3}"
    assert abs(sum(_hr_result3.values()) - 1.8) < 1e-9, "diode_reference 포함 시에도 합이 vdd와 불일치"

    _hr_divider = [
        {"name": "Da", "role": "voltage_divider", "min_vds": 0.20},
        {"name": "Db", "role": "voltage_divider", "min_vds": 0.20},
    ]
    _hr_result_div = allocate_stack_headroom(1.8, _hr_divider)
    assert abs(_hr_result_div["Da"] - 0.9) < 1e-9 and abs(_hr_result_div["Db"] - 0.9) < 1e-9, \
        f"voltage_divider(M39/M40류)는 여전히 vdd/2씩 균등분배여야 하는데(회귀): {_hr_result_div}"


def test_s021_search_gm_id_for_role(toy_lut):
    """[7-3e search_gm_id_for_role() -- role별 선택 방향(matching=최소, gain=gm/gds 최대, balanced=첫 feasible)]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S021(줄 1036-1058, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _role_L, _role_vds, _role_id_target = 0.5e-6, 0.6, 40e-6
    _gm_id_matching = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                             role="matching", W_bounds=(1e-6, 200e-6))
    _gm_id_gain = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                         role="gain", W_bounds=(1e-6, 200e-6))
    _gm_id_balanced = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                             role="balanced", W_bounds=(1e-6, 200e-6))
    def _feasible_w(g):
        try:
            return _role_id_target * _role_L / lut.gm_id_to_id_density(g, _role_L, _role_vds, 0.0)
        except ValueError:
            return None
    _feasible_check = [g for g in [i * 0.5 for i in range(4, 61)]
                        if (lambda w: w is not None and 1e-6 <= w <= 200e-6)(_feasible_w(g))]
    assert _gm_id_matching == min(_feasible_check), "matching이 feasible 중 최소 gm_id가 아님"
    assert _gm_id_balanced == min(_feasible_check), "balanced가 첫 feasible(오름차순 최소)이 아님"
    _best_ratio_direct = max(lut.gm_gds_ratio(g, _role_L, _role_vds, 0.0) for g in _feasible_check)
    assert abs(lut.gm_gds_ratio(_gm_id_gain, _role_L, _role_vds, 0.0) - _best_ratio_direct) < 1e-9, \
        "gain role이 실제 gm/gds 최댓값을 못 고름"


def test_s022_ro(s021_state, toy_lut):
    """[2026-08-19 세션37 연속 신설 -- 'load' role: gm/gds가 아니라 ro(=1/gds) 자체를
    최대화. nmcnr_amplifier M202(vds=1.0V) 실측으로 발견 -- 이 조건에서 gm_id가
    중간(~3.5)에서 ro가 피크라 'gain'(gm/gds 최대, gm_id=16)은 오히려 손해였다]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S022(줄 1060-1069, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _feasible_check = s021_state._feasible_check
    _role_L = s021_state._role_L
    _role_id_target = s021_state._role_id_target
    _role_vds = s021_state._role_vds
    lut = toy_lut

    _gm_id_load = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                         role="load", W_bounds=(1e-6, 200e-6))
    def _ro_direct(g):
        return 1.0 / (g * _role_id_target / lut.gm_gds_ratio(g, _role_L, _role_vds, 0.0))
    _best_ro_direct = max(_ro_direct(g) for g in _feasible_check)
    assert abs(_ro_direct(_gm_id_load) - _best_ro_direct) < 1e-6, \
        "load role이 실제 ro 최댓값을 못 고름"


def test_s023_section(s021_state, toy_lut):
    """[W_bounds 안에 후보가 하나도 없으면 즉시 ValueError]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S023(줄 1071-1079, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _role_L = s021_state._role_L
    _role_id_target = s021_state._role_id_target
    _role_vds = s021_state._role_vds
    lut = toy_lut

    with pytest.raises(ValueError):
        search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                               role="matching", W_bounds=(1e-9, 1e-9))


@pytest.mark.parametrize("_ID, _wb, _want", [
    (30e-3, (1e-6, 200e-6), "down"),     # 큰 전류 -> 큰 L에서 W가 상한 초과
    (1e-8, (120e-6, 200e-6), "up"),      # 높은 W 하한 -> 작은 L에서 W 미달
], ids=["down", "up"])
def test_s024_section(toy_lut, _ID, _wb, _want):
    """[7-3f 대체(2026-09-10, 사용자 지시 "bias_replica 상수도 없애") --
    derive_role_L(): L = clamp(knee(LUT 실측), W 실현가능 창). 옛 _L_ROLE_MULTIPLIERS
    (mirror 2.5 / bias_replica 1.2)는 삭제됐다 -- 아래는 그 자리를 대신하는 게이트다]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S024(줄 1080-1149, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _drl_spec = {
        "lut_by_kind": {"nmos": lut},
        "gm_id_grid": [i * 0.5 for i in range(4, 61)],
        "L_candidates": [float(v) for v in lut.L_grid],
        "VDS_candidates": [float(v) for v in lut.VDS_grid],
        "W_bounds": (1e-6, 200e-6),
    }
    _drl_ctx = SizingContext(spec=_drl_spec, kind_of={"Mm": "nmos"})
    _drl_knee = knee_L_for_kind(lut, _drl_spec)

    # (1) ID를 아직 모르면 knee 그대로 -- 창을 못 그리니 clamp도 없다.
    _drl_ctx.sized["Mm"] = {}
    assert abs(derive_role_L(_drl_ctx, "Mm", _drl_spec, "mirror") - _drl_knee) < 1e-18

    # (2) ★ clamp가 **양방향으로 실제 값을 바꾸는지**를 본다. 게이트는 '통과'가 아니라
    #     '동작'을 보여야 한다(프로젝트 원칙: 무동작 게이트는 게이트가 아니다).
    #       - 아래로: 전류가 크면 큰 L에서 W가 상한을 넘어 창의 **위쪽**이 잘린다.
    #       - 위로:   W 하한이 높으면 작은 L에서 W가 미달해 창의 **아래쪽**이 잘린다.
    #     두 경우 모두 새 규칙은 knee가 아니라 **창의 끝**을 고른다 -- 옛 고정배수라면
    #     이 상황에서도 그대로 L_min x 2.5를 냈을 것이다.
    _drl_vds = sorted(float(v) for v in lut.VDS_grid)[len(lut.VDS_grid) // 2]

    # `_drl_case` 두 호출(이관본) -> parametrize 두 케이스(케이스마다 새 ctx, design §6.8-4):
    #   _drl_case(30e-3, (1e-6, 200e-6), "down")     # 큰 전류 -> 큰 L에서 W가 상한 초과
    #   _drl_case(1e-8, (120e-6, 200e-6), "up")      # 높은 W 하한 -> 작은 L에서 W 미달
    _s = dict(_drl_spec, W_bounds=_wb)
    _drl_ctx.sized["Mm"] = {"ID": _ID, "vds": _drl_vds, "vsb": 0.0}
    _lo, _hi = feasible_L_window(lut, _ID, _drl_vds, 0.0, _s["L_candidates"],
                                  _s["gm_id_grid"], _wb)
    assert _lo is not None, f"ID={_ID}, W_bounds={_wb}에서 실현가능 창이 비었다(픽스처 설계 오류)"
    _L = derive_role_L(_drl_ctx, "Mm", _s, "mirror")
    assert _lo <= _L <= _hi, f"유도된 L={_L}이 실현가능 창 [{_lo},{_hi}] 밖이다"
    assert abs(_L - _drl_knee) > 1e-18, \
        f"clamp가 안 물렸다(L==knee) -- ID={_ID}, W_bounds={_wb}에서 이 게이트는 무동작이다"
    assert (_L < _drl_knee) == (_want == "down"), f"clamp 방향이 {_want}가 아니다"

    # (3) knee를 잴 근거(격자)가 없으면 값을 지어내지 않고 None -- 호출부가 거부한다.
    _drl_nogrid = dict(_drl_spec)
    del _drl_nogrid["gm_id_grid"]
    assert derive_role_L(_drl_ctx, "Mm", _drl_nogrid, "mirror") is None

    # (4) cascode/signal은 theta 탐색 담당 -- 없어진 select_L_by_role()의 가드를 이관했다.
    for _bad_role in ("cascode", "signal"):
        with pytest.raises(ValueError):
            derive_role_L(_drl_ctx, "Mm", _drl_spec, _bad_role)

    # (5) 류 단위 유도는 멤버 창의 **교집합** 안에 있어야 한다(미러비 보존).
    _drl_ctx.kind_of["Mn"] = "nmos"
    _drl_cls_ID = 10e-3
    _drl_ctx.sized["Mn"] = {"ID": _drl_cls_ID * 4.0, "vds": _drl_vds, "vsb": 0.0}
    _drl_ctx.sized["Mm"] = {"ID": _drl_cls_ID, "vds": _drl_vds, "vsb": 0.0}
    _cL = derive_class_L(_drl_ctx, ["Mm", "Mn"], _drl_spec)
    if _cL:
        for _mm in ("Mm", "Mn"):
            _e = _drl_ctx.sized[_mm]
            _l2, _h2 = feasible_L_window(lut, _e["ID"], _drl_vds, 0.0,
                                          _drl_spec["L_candidates"], _drl_spec["gm_id_grid"],
                                          _drl_spec["W_bounds"])
            assert _l2 <= _cL <= _h2, f"류 공통 L={_cL}이 {_mm}의 창 밖이다"


def test_s025_section():
    """[계통 미러비 오차를 **선언된 랜덤 예산과 같은 단위**로 재기(2026-09-10) --
    숫자를 박지 않으려고 만든 것이다: 임계값이 mismatch_sigma_mV 참조로 끝난다]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S025(줄 1150-1169, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _mre_ctx = SizingContext(topology_path="_mre_fake", kind_of={"Ma": "nmos", "Mb": "nmos"})
    # V_A = ID/gds = 10uA/1uS = 10V, dVDS = 0.5V -> dI/I = 5%. gm/ID = 20/V -> 입력환산 2.5mV.
    _mre_ctx.sized = {"Ma": {"ID": 10e-6, "gds": 1e-6, "vds": 0.4, "gm_id": 20.0},
                      "Mb": {"ID": 10e-6, "gds": 1e-6, "vds": 0.9, "gm_id": 20.0}}
    # `_matching_pairs_cached()`가 읽는 바로 그 캐시 엔트리를 채운다(파일을 만들지 않고
    # 이 metric만 격리해서 보기 위함 -- 끝나면 되돌린다).
    _load_full_topology_cached.__dict__.setdefault("_cache", {})["_mre_fake"] = {
        "matching_pairs": [{"names": ["Ma", "Mb"], "matching_sensitivity": "ratio"}],
        "by_name": {}, "passive_elements": []}
    try:
        _mre_pct = compute_metric({"type": "mirror_ratio_error", "unit": "%"}, _mre_ctx)
        _mre_mv = compute_metric({"type": "mirror_ratio_error_input_referred",
                                   "unit": "mV"}, _mre_ctx)
    finally:
        _load_full_topology_cached.__dict__["_cache"].pop("_mre_fake", None)
    assert abs(_mre_pct - 5.0) < 1e-9, f"계통 전류비 오차가 5%가 아님: {_mre_pct}"
    assert abs(_mre_mv - 2.5) < 1e-9, f"입력환산이 2.5mV가 아님: {_mre_mv}"
    assert _mre_ctx.derived.get("_mirror_ratio_error_pairs") is not None,         "쌍별 표가 ctx.derived에 안 남았다 -- 두 metric이 같은 계산을 두 번 하게 된다"


def test_s026_section():
    """[value_from_constraint -- 임계값을 다른 제약에서 그대로 참조(숫자 복제 금지)]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S026(줄 1171-1193, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _vfc_ok = resolve_constraint_references([
        {"metric": "mismatch_sigma_mV", "op": "<=", "value": 5.0},
        {"metric": "mirror_ratio_error_mV", "op": "<=",
         "value_from_constraint": "mismatch_sigma_mV"}], {})
    assert [c["value"] for c in _vfc_ok] == [5.0, 5.0], _vfc_ok
    # ★ 게이트는 '통과'가 아니라 '실제로 거부한다'를 보여야 한다.
    for _bad, _why in (
            ([{"metric": "x", "op": "<=", "value_from_constraint": "없는제약"}],
             "참조 대상이 없음"),
            ([{"metric": "y", "op": "<=", "value_from_spec": "k"},
              {"metric": "x", "op": "<=", "value_from_constraint": "y"}],
             "참조 대상이 자기도 참조(연쇄)"),
            ([{"metric": "y", "op": "<=", "value": 3.0},
              {"metric": "x", "op": "<=", "value": 9.0, "value_from_constraint": "y"}],
             "value와 참조가 둘 다 있고 다름")):
        with pytest.raises(ValueError):
            resolve_constraint_references(_bad, {"k": 1.0})


def test_s027_section():
    """[웜스타트 조인트 스캔 점수(2026-09-10, l_class 포함) -- 그룹마다 기준이 다르다]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S027(줄 1194-1223, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _gs_ms = {"dev_v": {"type": "battery_centering_deviation"}}
    _gs_m = _group_score_metric("dev_v", _gs_ms)
    assert _gs_m({"dev_v": 0.31, "power_uA": 100.0}) == 0.31
    # l_class 그룹: 전용 metric이 없어 **선언된 objective**를 쓴다. 부호 규약은
    # _optimize_theta_slsqp()와 같다(minimize는 그대로, maximize는 반전).
    # l_class 그룹: 전용 metric이 없어 **선언된 제약의 최소 여유**를 최대화한다(내부점).
    # 점수는 "작을수록 좋다" 규약이라 최소여유의 부호를 뒤집은 값이다.
    _gs_cons = [{"metric": "cmrr_db", "op": ">=", "value": 60.0},
                {"metric": "pm_deg", "op": ">=", "value": 60.0},
                {"metric": "area", "op": "<=", "value": 800.0}]
    _gs_i = _group_score_interior(_gs_cons)
    # 여유: cmrr (66-60)/60=0.10, pm (72-60)/60=0.20, area (800-720)/800=0.10 -> min 0.10
    assert abs(_gs_i({"cmrr_db": 66.0, "pm_deg": 72.0, "area": 720.0}) - (-0.10)) < 1e-12
    # 경계에 붙은 후보(여유 0)는 내부점보다 **나쁜 점수**여야 한다 -- 이게 이 기준의 요점이다.
    _gs_edge = _gs_i({"cmrr_db": 60.0, "pm_deg": 72.0, "area": 720.0})
    assert _gs_edge == 0.0 and _gs_edge > _gs_i({"cmrr_db": 66.0, "pm_deg": 72.0, "area": 720.0})
    # ★ 게이트는 '통과'가 아니라 '실제로 거부한다'를 보여야 한다.
    with pytest.raises(ValueError):
        _group_score_interior([])
    with pytest.raises(KeyError):
        _group_score_metric("not_declared", _gs_ms)


def test_s028_estimate_area_budget():
    """[7-4b 확장 estimate_area_budget() -- 콜드스타트 블렌딩 vs 실측 자기참조]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S028(줄 1224-1242, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _n_fingers_demo = 100
    _area_cold = estimate_area_budget("cascode", "unseen_role", area_priors={}, n_fingers=_n_fingers_demo)
    _a1d_demo = _n_fingers_demo * 1.0
    _a2d_cold_expected = _a1d_demo / 0.65
    _area_cold_expected = (1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected
    assert abs(_area_cold - _area_cold_expected) < 1e-9, "콜드스타트 블렌딩 공식 불일치"

    _area_priors_real = {"cascode": {"n_samples": 1, "packing_density_mean": 0.731,
                                       "packing_density_var": 0.0}}
    _area_real = estimate_area_budget("cascode", "cascode", _area_priors_real, _n_fingers_demo)
    _area_real_expected = _a1d_demo / 0.731
    assert abs(_area_real - _area_real_expected) < 1e-9


def test_s030_section():
    """# 배치 7-3d(analog-topology-json-library.do.md §7.3.2 D, 2026-07-31) -- # _THETA_FEED_REGISTRY 5개 핸들러 + optimize_full_circuit_budget() 그리드서치 골격

    [feed 'A' (_feed_root_ratio) -- theta*reference 전류합을 root의 seed로]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S030(줄 1247-1251, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _ctx_a = SizingContext(sized={"Mref": {"ID": 10e-6}})
    apply_theta_feed({"type": "A", "tag": "biasgen_root", "root": "Mtarget", "reference": ["Mref"]},
                      0.5, _ctx_a)
    assert abs(_ctx_a.seed_currents["Mtarget"] - 5e-6) < 1e-15


def test_s031_section():
    """[feed 'C' (_feed_diode_stack_target) -- theta*reference W를 target W로]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S031(줄 1253-1256, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _ctx_c = SizingContext(sized={"Mref": {"W": 40e-6}})
    apply_theta_feed({"type": "C", "target": "Mrepl", "reference": "Mref"}, 0.1, _ctx_c)
    assert abs(_ctx_c.sized["Mrepl"]["W"] - 4e-6) < 1e-15


def test_s032_section(toy_lut):
    """[feed 'B' (_feed_gm_target_convention) -- N*omega_c*C_cmfb를 gm_target으로 사이징]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S032(줄 1258-1265, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _ctx_b = SizingContext(spec={"lut_by_kind": {"nmos": lut}, "omega_c": 2 * math.pi * 1e6, "C_cmfb": 2e-12},
                            kind_of={"Mcmfb": "nmos"})
    apply_theta_feed({"type": "B", "tag": "servo", "target": "Mcmfb", "omega_key": "omega_c",
                       "cap_key": "C_cmfb", "L": 0.5e-6, "W": 30e-6, "vds": 0.6,
                       "gm_id_bounds": [2.0, 28.0]}, 3.0, _ctx_b)
    _gm_target_expected = 3.0 * 2 * math.pi * 1e6 * 2e-12
    assert abs(_ctx_b.sized["Mcmfb"]["gm"] - _gm_target_expected) / _gm_target_expected < 1e-3


def test_s033_section():
    """[feed 'settling_split' (_feed_settling_split) -- theta*total을 derived로]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S033(줄 1267-1270, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _ctx_s = SizingContext(spec={"t_settle_total": 40e-9})
    apply_theta_feed("settling_split", 0.25, _ctx_s)
    assert abs(_ctx_s.derived["t_slew"] - 10e-9) < 1e-18


def test_s034_theta(toy_lut):
    """[feed 'metric_stage_budget' -- theta(L)로 지정 devices의 L/W/gm/gds 재계산]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S034(줄 1272-1278, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _ctx_m = SizingContext(spec={"lut_by_kind": {"nmos": lut}}, sized={"M1": {"ID": 10e-6}, "M2": {"ID": 20e-6}},
                            kind_of={"M1": "nmos", "M2": "nmos"})
    apply_theta_feed({"type": "metric_stage_budget", "metric": "gain_db", "devices": ["M1", "M2"],
                       "gm_id": 15.0, "vds": 0.6}, 0.5e-6, _ctx_m)
    assert _ctx_m.sized["M1"]["L"] == 0.5e-6 and _ctx_m.sized["M2"]["L"] == 0.5e-6
    _gain_check = compute_metric({"type": "gain_stages_sum", "stages": [["M1", "M2"]]}, _ctx_m)


def test_s035_section():
    """[등록 안 된 feed 타입은 즉시 ValueError]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S035(줄 1280-1287, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    with pytest.raises(ValueError):
        apply_theta_feed({"type": "not_a_real_feed"}, 1.0, SizingContext())


def test_s036_optimize_full_circuit_budget(library_dir, toy_lut):
    """[optimize_full_circuit_budget() -- sizing_roles/device_roles 둘 다 없는 회로는 즉시 빈 결과로 통과]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S036(줄 1288-1322, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    # 2026-08-14 -- 원래 이 fixture로 folded_cascode.topology.json을 그대로 썼다("sizing_roles
    # 없는 실회로"의 편의상 예시였을 뿐, 이 테스트의 실제 의도는 "device_roles가 비어 있으면
    # L_role 루프가 아무것도 안 하고 빈 결과를 낸다"였다) -- propose_device_roles_gap_fill()/
    # apply_device_roles_gap_fill()을 실제로 그 파일에 적용해 device_roles를 채운 뒤로 이
    # fixture 전제(device_roles 없음)가 깨졌다. 이 테스트가 실제로 검증하려는 것과 무관한
    # 외부 상태(실제 라이브러리 파일의 최신 내용)에 더 이상 의존하지 않도록, 의도를 그대로
    # 담은 최소 합성 fixture로 교체한다(device_roles/sizing_roles 둘 다 명시적으로 없음).
    # ⚠️ 2026-08-14 세션34 재정정 -- Mo(gate='vb', 레일 소스+고정 바이어스 게이트 단일
    # 소자)가 propose_device_roles_gap_fill()의 새 4번째 소스("파트너 없는 active-load ->
    # gm_id_role='gain' 제안", 이 세션에서 신설)에 걸려 require_device_roles_reviewed()가
    # 더 이상 조용히 통과하지 않게 됐다 -- 이 테스트의 의도(sizing_roles/device_roles가
    # 완전히 비어있을 때 optimize_full_circuit_budget()이 즉시 빈 결과를 내는지)와 무관한
    # 충돌이라, Mo를 diode-connected(gate=자기 drain)로 바꿔 애초에 gap-fill의 어떤 제안
    # 대상도 아니게 만든다(diode-connected 단독 소자는 mirror 그룹조차 안 됨, len(ms)<2).
    _lib_dir_recipe = library_dir
    _ofc_empty_topo = {
        "schema_version": "2.0", "topology_name": "_test_empty_roles", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [{"name": "Mo", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "out"}],
        "symmetry": {"matching_pairs": [], "dispositions": []},
        "sizing_roles": None, "device_roles": None,
    }
    with _tempfile.TemporaryDirectory() as _ofc_empty_tmpdir:
        _ofc_empty_path = _os.path.join(_ofc_empty_tmpdir, "_test_empty_roles.topology.json")
        with open(_ofc_empty_path, "w", encoding="utf-8") as _ofc_empty_f:
            json.dump(_ofc_empty_topo, _ofc_empty_f)
        _ofc_result = optimize_full_circuit_budget(_ofc_empty_path, {"lut": lut})
    assert _ofc_result["theta_star"] == {} and _ofc_result["metrics"] == {}, \
        "sizing_roles 없는데 빈 결과가 아님"
    assert _ofc_result["sizing_overrides"] is None and _ofc_result["pipeline_result"] is None, \
        "device_roles/compensation 없이 넷리스트 전체가 사이징될 리 없는데 전체 파이프라인이 실행됨"


def test_s037_optimize_full_circuit_budget(toy_lut):
    """[optimize_full_circuit_budget() -- 합성 sizing_roles로 그리드서치가 실제 최적값을 찾는지 전수비교]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S037(줄 1323-1374, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _ofc_topo = {
        "schema_version": "2.0", "topology_name": "_test_only", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [{"name": "Mtest", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "vb"}],
        "symmetry": {"matching_pairs": [], "dispositions": []},
        "sizing_roles": {
            "theta": [{"name": "N", "bounds": [1.0, 5.0],
                       "feeds": {"type": "B", "tag": "servo", "target": "Mtest",
                                 "omega_key": "omega_c", "cap_key": "cap", "L": 0.5e-6, "W": 30e-6,
                                 "vds": 0.6, "gm_id_bounds": [2.0, 28.0]}}],
            # A12(2026-09-08) -- 이 픽스처 자신이 A12 사례였다: 이름은 `power_uA`인데
            # constraint 임계값 1e-3은 SI(A)였다(=1mA). 이름을 정직하게 `power_A`로 바꾸고
            # unit="A"를 선언한다 -- 환산 계수 1.0이라 값도 임계도 그대로다.
            "metrics": {"power_A": {"type": "sum_current", "unit": "A"}},
            "objective": {"minimize": "power_A"},
            "constraints": [{"metric": "power_A", "op": "<=", "value": 1e-3}],
        },
    }
    with _tempfile.TemporaryDirectory() as _ofc_tmpdir:
        _ofc_topo_path = _os.path.join(_ofc_tmpdir, "_test_only.topology.json")
        with open(_ofc_topo_path, "w", encoding="utf-8") as _f:
            json.dump(_ofc_topo, _f)
        _ofc_spec = {"lut": lut, "lut_by_kind": {"nmos": lut}, "omega_c": 2 * math.pi * 1e6, "cap": 2e-12}
        _ofc_full = optimize_full_circuit_budget(_ofc_topo_path, _ofc_spec, grid_points_per_theta=5)
        _theta_star, _sizing, _metrics = _ofc_full["theta_star"], _ofc_full["sizing"], _ofc_full["metrics"]
        assert _ofc_full["pipeline_result"] is not None, \
            "Mtest는 W까지 다 있는데 전체 파이프라인(assign_finger_geometry/run_topology_pipeline)이 안 돎"
        assert _ofc_full["audit_ok"], f"단일 소자 넷리스트인데 audit이 FAIL: {_ofc_full['pipeline_result']}"

        # 전수비교: 같은 격자를 직접 순회해 손으로 찾은 최적값과 정확히 일치하는지 확인.
        _manual_best = None
        for _i in range(5):
            _N = _lerp(1.0, 5.0, _i / 4)
            _ctx_manual = SizingContext(spec=_ofc_spec, kind_of={"Mtest": "nmos"})
            apply_theta_feed(_ofc_topo["sizing_roles"]["theta"][0]["feeds"], _N, _ctx_manual)
            _a_ids = propagate_topology_forced_currents(
                [Transistor("Mtest", "nmos", source="gnd", drain="out", gate="vb")],
                _ctx_manual.seed_currents, _ctx_manual.mirror_ratios)
            for _name, _idv in _a_ids.items():
                _ctx_manual.sized.setdefault(_name, {})["ID"] = _idv
            _power = compute_metric({"type": "sum_current"}, _ctx_manual)
            if _power <= 1e-3 and (_manual_best is None or _power < _manual_best[0]):
                _manual_best = (_power, _N)
        assert _manual_best is not None, "전수비교 자체가 infeasible -- 테스트 설계 오류"
        assert abs(_metrics["power_A"] - _manual_best[0]) < 1e-12, \
            f"함수 결과({_metrics['power_A']})가 전수비교 최적값({_manual_best[0]})과 다름"
        assert abs(_theta_star["N"] - _manual_best[1]) < 1e-9, \
            f"theta*(N={_theta_star['N']})가 전수비교 최적 N({_manual_best[1]})과 다름"


def test_s038_section(toy_lut):
    """[device_roles.gm_id_match_vgs_of -- 2026-08-19 세션38 신설, gm_id_role 루프의 2차 pass가 실제로 companion의 VGS로 결합되는지 (nmcnr_amplifier M203/M204 계기)]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S038(줄 1375-1436, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    # Ma(diode-connected 레퍼런스, gate=drain=NodeC)/Mb(gate=NodeC, source 공유)는 게이트·소스가
    # 물리적으로 같은 노드에 묶여 VGS가 항상 같아야 하지만 VDS는 다르다(현실의 M203/M204와 동일
    # 패턴) -- known_sizing으로 둘 다 L/vds를 직접 시드해(headroom 우회, 위 diagnose_sizing_
    # roles_gap() 테스트 1과 동일 패턴) 이 2차 pass만 격리해서 검증한다. current_forced=True로
    # 선언했으므로 ID는 반드시 같아야 한다(propagate_topology_forced_currents()의 KCL 제약 --
    # 실측으로 확인: 다르게 주면 즉시 ValueError, 이 테스트 자신의 전제를 실제로 검증해줌).
    _gmv_topo = {
        "schema_version": "2.0", "topology_name": "_gmv_test", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [
            {"name": "Ma", "kind": "nmos", "source": "vss", "drain": "NodeC", "gate": "NodeC"},
            {"name": "Mb", "kind": "nmos", "source": "vss", "drain": "out", "gate": "NodeC"},
        ],
        "symmetry": {"matching_pairs": [
            {"names": ["Ma", "Mb"], "current_forced": True, "matching_sensitivity": "ratio"}],
            "dispositions": []}, "sizing_roles": None,
        "device_roles": {
            "Ma": {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror", "vsb": 0.0},
            "Mb": {"gm_id_match_vgs_of": "Ma", "L_role": "mirror", "headroom_role": "mirror", "vsb": 0.0},
        },
    }
    _gmv_L, _gmv_ID = 0.5e-6, 1e-5
    # 2026-09-08(B16) -- Ma는 `gate == drain == NodeC`, 즉 **diode-connected**다. 그래서
    # vds를 임의로 줄 수 없다(vds가 gm_id를, gm_id가 W를 정한다). 예전엔 0.8V를 박아뒀는데
    # 이 LUT에서는 그 값이 W=0.28um(하한 1um 미달)를 요구했다 -- 배선하고 나서야 드러난
    # 기존 오류다. 값을 다시 박지 않고 **구간을 런타임에 계산해 그 중앙을 쓴다**(LUT이
    # 바뀌면 따라간다). Mb는 diode가 아니므로 자유이고, 이 테스트의 의도대로 일부러 다르게 둔다.
    _gmv_lo, _gmv_hi = diode_vds_window(lut, "nmos", _gmv_L, _gmv_ID, 0.0, (1e-6, 200e-6))
    assert _gmv_lo is not None, "toy LUT에서 Ma의 diode 가능 vds 구간이 비었다(fixture 재검토 필요)"
    _gmv_vds_a = 0.5 * (_gmv_lo + _gmv_hi)
    _gmv_vds_b = _gmv_lo                                 # ⚠️ 일부러 다른 VDS
    assert abs(_gmv_vds_a - _gmv_vds_b) > 1e-6, "이 테스트는 두 소자의 VDS가 달라야 의미가 있다"
    _gmv_known = {"Ma": {"ID": _gmv_ID, "L": _gmv_L, "vds": _gmv_vds_a, "vsb": 0.0},
                  "Mb": {"ID": _gmv_ID, "L": _gmv_L, "vds": _gmv_vds_b, "vsb": 0.0}}
    with _tempfile.TemporaryDirectory() as _gmv_tmp:
        _gmv_path = _os.path.join(_gmv_tmp, "_gmv_test.topology.json")
        with open(_gmv_path, "w", encoding="utf-8") as _f:
            json.dump(_gmv_topo, _f)
        # 2026-09-10 -- 격자 3종을 선언한다. L_role의 L은 이제 knee(LUT 실측)에서 유도되고
        # knee는 "이 설계가 실제로 탐색하는 격자"에서만 잰다(knee_L_for_kind() 참고).
        # 선언이 없으면 엔진이 값을 지어내지 않고 거부한다 -- 실제 spec은 전부 선언한다.
        _gmv_spec = {"lut_by_kind": {"nmos": lut}, "vdd": 1.8, "L_min": 0.15e-6,
                     "W_bounds": (1e-6, 200e-6), "min_vds_by_role": {"mirror": 0.2},
                     "L_candidates": [float(v) for v in lut.L_grid],
                     "VDS_candidates": [float(v) for v in lut.VDS_grid],
                     "gm_id_grid": [i * 0.5 for i in range(4, 61)],
                     "known_sizing": _gmv_known}
        # optimize_full_circuit_budget()이 아니라 _build_theta_evaluator()+evaluate({})를 직접
        # 쓴다 -- 이 테스트가 검증하려는 건 device_roles 2차 pass 하나뿐이고, 전체 harness는
        # assign_finger_geometry()/run_topology_pipeline_with_finger_fixup() 같은 무관한 레이아웃
        # 단계까지 통과해야 해서(이 2-소자 toy 회로엔 그 단계용 spec 필드가 없어 실패함) 이
        # 테스트의 의도와 무관한 실패를 낼 수 있다(위 "합성 sizing_roles" 테스트와 달리 이 fixture는
        # 레이아웃까지 검증할 의도가 없음).
        _gmv_ev = _build_theta_evaluator(_gmv_path, _gmv_spec)
        _gmv_ctx, _ = _gmv_ev["evaluate"]({})
    _gmv_gm_id_a, _gmv_gm_id_b = _gmv_ctx.sized["Ma"]["gm_id"], _gmv_ctx.sized["Mb"]["gm_id"]
    _gmv_target_vgs = lut.vgs_for_gm_id(_gmv_gm_id_a, _gmv_L, _gmv_vds_a, 0.0)
    _gmv_expected_gm_id_b = lut.gm_id_for_vgs(_gmv_target_vgs, _gmv_L, _gmv_vds_b, 0.0)
    assert abs(_gmv_gm_id_b - _gmv_expected_gm_id_b) < 1e-9, \
        f"Mb의 gm_id({_gmv_gm_id_b})가 Ma의 VGS 역산값({_gmv_expected_gm_id_b})과 다름"


def test_s039_section(s038_state):
    """[gm_id_match_vgs_of가 아직 sizing 안 된(존재하지 않는) 소자를 참조하면 ValueError]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S039(줄 1445-1459, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _gmv_spec = s038_state._gmv_spec
    _gmv_topo = s038_state._gmv_topo

    _gmv_bad_topo = json.loads(json.dumps(_gmv_topo))
    _gmv_bad_topo["device_roles"]["Mb"]["gm_id_match_vgs_of"] = "Mz"
    with _tempfile.TemporaryDirectory() as _gmv_bad_tmp:
        _gmv_bad_path = _os.path.join(_gmv_bad_tmp, "_gmv_bad.topology.json")
        with open(_gmv_bad_path, "w", encoding="utf-8") as _f:
            json.dump(_gmv_bad_topo, _f)
        with pytest.raises(ValueError) as _gmv_e_info:
            _build_theta_evaluator(_gmv_bad_path, _gmv_spec)["evaluate"]({})
        _gmv_e = _gmv_e_info.value
        assert "gm_id_match_vgs_of" in str(_gmv_e) and "Mz" in str(_gmv_e), \
            f"에러 메시지에 gm_id_match_vgs_of/Mz가 없음: {_gmv_e}"


def test_s040_VGS(toy_lut):
    """[device_roles.vds_match_vgs_of -- 2026-08-19 세션38 연속 신설, 헤드룸 루프가 다른 컬럼(다른 vertical_stack_id 그룹) 소자의 VGS를 이 소자의 VDS로 강제하는지, 그리고 같은 컬럼의 나머지 소자가 남는 예산을 정확히 흡수하는지 (nmcnr_amplifier M204/M301 계기 -- M301.gate=M204.drain이라 VGS(M301)=VDS(M204)가 KVL로 강제됨)]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S040(줄 1460-1516, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    # 실제 M202(pmos)/M204(nmos) 컬럼 구조를 그대로 축소 복제한다(단일 소자끼리는 audit_
    # vertical_stack_id_vs_kcl()이 "진짜 vdd~gnd 컬럼"으로 인정하지 않는다 -- PMOS/NMOS가
    # 드레인 노드를 공유해야 KCL이 성립함). col_a=Ka(pmos)+Ma(nmos, 드레인=NodeA)/col_b=
    # Kb(pmos)+Mb(nmos, 드레인=NodeB, 게이트=NodeA -- 그래서 VGS(Mb)=VDS(Ma)가 KVL로
    # 강제되고, vds_match_vgs_of="Ma"로 그 관계를 선언한다). Ma는 known_sizing으로 gm_id/L/ID를
    # 직접 시드(compensation이 채우는 것과 동일한 역할, vds는 일부러 안 줘서 col_a 헤드룸이
    # 직접 풀게 함 -- _ref_depth() 위상정렬이 col_a를 col_b보다 먼저 처리하는지까지 검증).
    _vmv_vdd = 1.8
    _vmv_topo = {
        "schema_version": "2.0", "topology_name": "_vmv_test", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [
            {"name": "Ka", "kind": "pmos", "source": "vdd", "drain": "NodeA", "gate": "vb_ka"},
            {"name": "Ma", "kind": "nmos", "source": "vss", "drain": "NodeA", "gate": "vb_ma"},
            {"name": "Kb", "kind": "pmos", "source": "vdd", "drain": "NodeB", "gate": "vb_kb"},
            {"name": "Mb", "kind": "nmos", "source": "vss", "drain": "NodeB", "gate": "NodeA"},
        ],
        "symmetry": {"matching_pairs": [], "dispositions": []}, "sizing_roles": None,
        "device_roles": {
            # Ma는 일부러 gm_id_role을 안 준다(known_sizing으로 compensation처럼 gm_id를
            # 외부에서 고정). Ka/Kb/Mb는 propose_device_roles_gap_fill()의 자동 제안(파트너
            # 없는 active load -> "gain"류)이 require_device_roles_reviewed()를 막지 않도록
            # gm_id_role을 명시 선언해둔다(이 테스트가 검증하려는 vds 흐름과는 무관, review
            # 게이트 통과용).
            "Ka": {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror",
                   "vertical_stack_id": "col_a", "vsb": 0.0},
            "Ma": {"headroom_role": "mirror", "vertical_stack_id": "col_a", "vsb": 0.0},
            "Kb": {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror",
                   "vertical_stack_id": "col_b", "vsb": 0.0},
            "Mb": {"vds_match_vgs_of": "Ma", "gm_id_role": "matching", "L_role": "mirror",
                   "headroom_role": "mirror", "vertical_stack_id": "col_b", "vsb": 0.0},
        },
    }
    _vmv_known = {"Ka": {"ID": 1e-5, "vsb": 0.0}, "Ma": {"ID": 1e-5, "L": 0.5e-6, "gm_id": 15.0, "vsb": 0.0},
                  "Kb": {"ID": 1e-5, "vsb": 0.0}, "Mb": {"ID": 1e-5, "vsb": 0.0}}
    with _tempfile.TemporaryDirectory() as _vmv_tmp:
        _vmv_path = _os.path.join(_vmv_tmp, "_vmv_test.topology.json")
        with open(_vmv_path, "w", encoding="utf-8") as _f:
            json.dump(_vmv_topo, _f)
        _vmv_spec = _tst_grids({"lut_by_kind": {"nmos": lut, "pmos": lut}, "vdd": _vmv_vdd, "L_min": 0.15e-6,
                     "W_bounds": (1e-6, 200e-6), "min_vds_by_role": {"mirror": 0.2},
                     "known_sizing": _vmv_known})
        _vmv_ctx, _ = _build_theta_evaluator(_vmv_path, _vmv_spec)["evaluate"]({})
    _vmv_vds_a = _vmv_ctx.sized["Ma"]["vds"]
    assert abs(_vmv_vds_a - _vmv_vdd / 2) < 1e-9, \
        f"Ka/Ma 둘 다 'mirror'라 균등분배(vdd/2={_vmv_vdd/2})가 나와야 하는데 Ma.vds={_vmv_vds_a}"
    _vmv_target_vgs = lut.vgs_for_gm_id(15.0, 0.5e-6, _vmv_vds_a, 0.0)
    _vmv_vds_b = _vmv_ctx.sized["Mb"]["vds"]
    _vmv_vds_kb = _vmv_ctx.sized["Kb"]["vds"]
    assert abs(_vmv_vds_b - _vmv_target_vgs) < 1e-9, \
        f"Mb.vds({_vmv_vds_b})가 Ma의 VGS 역산값({_vmv_target_vgs})과 다름"
    assert abs(_vmv_vds_kb - (_vmv_vdd - _vmv_target_vgs)) < 1e-9, \
        f"Kb.vds({_vmv_vds_kb})가 vdd에서 Mb의 강제값을 뺀 나머지({_vmv_vdd - _vmv_target_vgs})와 다름"


def test_s041_section(s040_state):
    """[vds_match_vgs_of가 순환 참조하면 ValueError]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S041(줄 1518-1531, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _vmv_spec = s040_state._vmv_spec
    _vmv_topo = s040_state._vmv_topo

    _vmv_cyc_topo = json.loads(json.dumps(_vmv_topo))
    _vmv_cyc_topo["device_roles"]["Ma"]["vds_match_vgs_of"] = "Mb"
    with _tempfile.TemporaryDirectory() as _vmv_cyc_tmp:
        _vmv_cyc_path = _os.path.join(_vmv_cyc_tmp, "_vmv_cyc.topology.json")
        with open(_vmv_cyc_path, "w", encoding="utf-8") as _f:
            json.dump(_vmv_cyc_topo, _f)
        with pytest.raises(ValueError) as _vmv_cyc_e_info:
            _build_theta_evaluator(_vmv_cyc_path, _vmv_spec)["evaluate"]({})
        _vmv_cyc_e = _vmv_cyc_e_info.value
        assert "순환 참조" in str(_vmv_cyc_e), f"순환 참조 에러가 아님: {_vmv_cyc_e}"


def test_s042__ref_depth(toy_lut):
    """[fixed-point worklist -- 2026-08-19 세션39 신설, _ref_depth() 단일재귀 정렬을 대체. 두 vertical_stack_id 그룹이 서로 다른 멤버를 통해 맞물릴 때(Monticelli floating battery -- nmcnr M9a/M9b/M11a/M11b/M12 계기, `.ai/context.md` 세션38→39 참고) 예전엔 순환 참조로 오판했다. 실제로는 grpB의 pre-pass(vds_match_vgs_of, N만 있으면 즉시 가능) -> grpA 완결(budget_reference_device로 grpB의 pre-pass 결과 참조) -> grpB의 나머지 멤버 완결(budget_reference_device로 grpA 결과 참조) 순으로 풀리는 선형 순서가 있다]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S042(줄 1532-1598, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    # N: 이미 완전히 확정된 소자(compensation+자기 headroom 그룹까지 다 끝난 M16을 모사) --
    # known_sizing으로 gm_id/L/vds를 전부 직접 시드해 자기 그룹 없이 독립적으로 참조 가능.
    # S(=M10 모사): vds_match_vgs_of="N" (드레인이 N의 게이트와 물리적으로 같다고 가정).
    # F(=M9b 모사): S와 같은 grpB, 자유 헤드룸 배정 대상.
    # T2(=M9a 모사)/T(=M8 모사): grpA. T2.budget_reference_device="S"(grpA가 grpB의 pre-pass
    # 결과를 참조) -- grpB는 반대로 F.budget_reference_device="T2"(grpB가 grpA의 메인 결과를
    # 참조) -- 이 둘이 바로 "서로 다른 멤버를 통해 맞물리는" 진짜 상호참조다.
    _fpw_vdd = 1.8
    _fpw_topo = {
        "schema_version": "2.0", "topology_name": "_fpw_test", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [
            {"name": "N", "kind": "nmos", "source": "vss", "drain": "NodeOut", "gate": "vb_n"},
            {"name": "S", "kind": "nmos", "source": "vss", "drain": "NodeMid", "gate": "vb_s"},
            {"name": "F", "kind": "nmos", "source": "NodeMid", "drain": "NodeTop", "gate": "vb_f"},
            {"name": "T2", "kind": "pmos", "source": "NodeX", "drain": "NodeTop", "gate": "vb_t2"},
            {"name": "T", "kind": "pmos", "source": "vdd", "drain": "NodeX", "gate": "vb_t"},
        ],
        "symmetry": {"matching_pairs": [], "dispositions": []}, "sizing_roles": None,
        "device_roles": {
            "N": {"gm_id_role": "matching", "L_role": "mirror", "vsb": 0.0},
            "S": {"vds_match_vgs_of": "N", "gm_id_role": "matching", "L_role": "mirror",
                  "headroom_role": "mirror", "vertical_stack_id": "grpB", "vsb": 0.0},
            "F": {"budget_reference_device": "T2", "gm_id_role": "matching", "L_role": "mirror",
                  "headroom_role": "mirror", "vertical_stack_id": "grpB", "vsb": 0.0},
            "T2": {"budget_reference_device": "S", "gm_id_role": "matching", "L_role": "mirror",
                   "headroom_role": "mirror", "vertical_stack_id": "grpA", "vsb": 0.0},
            "T": {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror",
                  "vertical_stack_id": "grpA", "vsb": 0.0},
        },
    }
    _fpw_known = {"N": {"ID": 1e-5, "L": 0.5e-6, "gm_id": 15.0, "vds": 0.9, "vsb": 0.0},
                  "S": {"ID": 1e-5, "vsb": 0.0}, "F": {"ID": 1e-5, "vsb": 0.0},
                  "T2": {"ID": 1e-5, "vsb": 0.0}, "T": {"ID": 1e-5, "vsb": 0.0}}
    with _tempfile.TemporaryDirectory() as _fpw_tmp:
        _fpw_path = _os.path.join(_fpw_tmp, "_fpw_test.topology.json")
        with open(_fpw_path, "w", encoding="utf-8") as _f:
            json.dump(_fpw_topo, _f)
        _fpw_spec = _tst_grids({"lut_by_kind": {"nmos": lut, "pmos": lut}, "vdd": _fpw_vdd, "L_min": 0.15e-6,
                     "W_bounds": (1e-6, 200e-6), "min_vds_by_role": {"mirror": 0.2},
                     "known_sizing": _fpw_known})
        _fpw_ctx, _ = _build_theta_evaluator(_fpw_path, _fpw_spec)["evaluate"]({})
    # 기대값 손계산: S.vds = VGS(N) (vds_match_vgs_of) -- grpB pre-pass.
    _fpw_target_vgs_n = lut.vgs_for_gm_id(15.0, 0.5e-6, 0.9, 0.0)
    _fpw_vds_s = _fpw_ctx.sized["S"]["vds"]
    assert abs(_fpw_vds_s - _fpw_target_vgs_n) < 1e-9, \
        f"S.vds({_fpw_vds_s})가 N의 VGS 역산값({_fpw_target_vgs_n})과 다름"
    # grpA(T+T2) base_budget = vdd - S.vds, T/T2 둘 다 role="mirror"라 균등분배.
    _fpw_vds_t = _fpw_ctx.sized["T"]["vds"]
    _fpw_vds_t2 = _fpw_ctx.sized["T2"]["vds"]
    _fpw_base_a = _fpw_vdd - _fpw_vds_s
    assert abs((_fpw_vds_t + _fpw_vds_t2) - _fpw_base_a) < 1e-9, \
        f"T.vds+T2.vds({_fpw_vds_t + _fpw_vds_t2})가 grpA base_budget({_fpw_base_a})과 다름"
    assert abs(_fpw_vds_t - _fpw_vds_t2) < 1e-9, \
        f"T/T2 둘 다 role=mirror라 균등분배여야 하는데 T.vds={_fpw_vds_t}, T2.vds={_fpw_vds_t2}"
    # grpB(F+S) base_budget = vdd - T2.vds(grpA 완결 후에야 확정) -- F.vds = base_budget_B - S.vds.
    _fpw_vds_f = _fpw_ctx.sized["F"]["vds"]
    _fpw_base_b = _fpw_vdd - _fpw_vds_t2
    assert abs((_fpw_vds_f + _fpw_vds_s) - _fpw_base_b) < 1e-9, \
        f"F.vds+S.vds({_fpw_vds_f + _fpw_vds_s})가 grpB base_budget({_fpw_base_b})과 다름"


def test_s043_section(s042_state, toy_lut):
    """[두 그룹의 budget_reference_device가 서로를 직접 가리키면(pre-pass로도 못 뚫리는 진짜 순환) 여전히 ValueError -- 어느 pass에서도 vds가 하나도 안 늘어나야 함]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S043(줄 1600-1645, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fpw_vdd = s042_state._fpw_vdd
    lut = toy_lut

    # grpX={X}, grpY={Y} -- singleton 그룹끼리 budget_reference_device로 서로를 가리킨다
    # (vds_match_vgs_of/pre-pass 탈출구 자체가 없는 가장 단순한 진짜 순환). referenced_
    # singleton 분기에서도 ref_dev 준비 여부 확인은 stack_entries 구성보다 먼저 실행되므로
    # (본문 코드 순서 확인됨) headroom_role 없이도 이 지점에서 막힌다.
    _fpw_cyc2_topo = {
        "schema_version": "2.0", "topology_name": "_fpw_cyc2_test", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [
            {"name": "X", "kind": "pmos", "source": "vdd", "drain": "NodeX", "gate": "vb_x"},
            {"name": "Y", "kind": "nmos", "source": "vss", "drain": "NodeX", "gate": "vb_y"},
        ],
        "symmetry": {"matching_pairs": [], "dispositions": []}, "sizing_roles": None,
        "device_roles": {
            "X": {"budget_reference_device": "Y", "gm_id_role": "matching", "L_role": "mirror",
                  "headroom_role": "mirror", "vertical_stack_id": "grpX", "vsb": 0.0},
            "Y": {"budget_reference_device": "X", "gm_id_role": "matching", "L_role": "mirror",
                  "headroom_role": "mirror", "vertical_stack_id": "grpY", "vsb": 0.0},
        },
    }
    _fpw_cyc2_known = {"X": {"ID": 1e-5, "vsb": 0.0}, "Y": {"ID": 1e-5, "vsb": 0.0}}
    with _tempfile.TemporaryDirectory() as _fpw_cyc2_tmp:
        _fpw_cyc2_path = _os.path.join(_fpw_cyc2_tmp, "_fpw_cyc2.topology.json")
        with open(_fpw_cyc2_path, "w", encoding="utf-8") as _f:
            json.dump(_fpw_cyc2_topo, _f)
        _fpw_cyc2_spec = _tst_grids({"lut_by_kind": {"nmos": lut, "pmos": lut}, "vdd": _fpw_vdd,
                           "L_min": 0.15e-6, "W_bounds": (1e-6, 200e-6),
                           "min_vds_by_role": {"mirror": 0.2}, "known_sizing": _fpw_cyc2_known})
        with pytest.raises(ValueError) as _fpw_cyc2_e_info:
            _build_theta_evaluator(_fpw_cyc2_path, _fpw_cyc2_spec)["evaluate"]({})
        _fpw_cyc2_e = _fpw_cyc2_e_info.value
        assert "grpX" in str(_fpw_cyc2_e) and "grpY" in str(_fpw_cyc2_e), \
            f"막힌 그룹(grpX/grpY)이 에러 메시지에 없음: {_fpw_cyc2_e}"

    # 2026-08-15 -- 사용자 지시("sizing role을 자동으로 넣는 것도 설계하고 통합하자")로
    # 신설. device_roles와 달리 sizing_roles의 theta bounds/constraints 목표값은 spec(설계
    # 목표)에서 오는 숫자라 connectivity만으로 지어낼 수 없다 -- 그래서 이 함수는 숫자를
    # 대신 채우지 않고, "sizing_roles=null 상태로 실제 완주 가능한가"를 실행 기반으로
    # 진단해 지금까지 optimize_full_circuit_budget() 깊은 곳에서 날것의 ValueError로만
    # 터지던 실패를 구조화된 gap 리포트로 바꾼다. 아래 5개 케이스는 전부 실제로 실행해
    # 확인한 결과(추측 없음, folded_cascode/nmcnr_amplifier는 실제 라이브러리 파일).
    _diag_lut = build_toy_lut()


def test_s045_section(s043_state):
    """[1. 정상 케이스 -- known_sizing으로 전류/L/VDS가 다 채워지면 status=ok]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S045(줄 1647-1683, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _diag_lut = s043_state._diag_lut

    _diag_ok_topo = {
        "schema_version": "2.0", "topology_name": "_diag_ok", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [{"name": "Mo", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "out"}],
        "symmetry": {"matching_pairs": [], "dispositions": []}, "sizing_roles": None,
        "device_roles": {"Mo": {"gm_id_role": "matching", "L_role": "mirror",
                                  "headroom_role": "mirror", "vsb": 0.0}},
    }
    with _tempfile.TemporaryDirectory() as _diag_tmp:
        _diag_path = _os.path.join(_diag_tmp, "_diag_ok.topology.json")
        with open(_diag_path, "w", encoding="utf-8") as _f:
            json.dump(_diag_ok_topo, _f)
        # 2026-09-10 -- knee_L_for_kind() docstring이 기록한 반례가 바로 이 픽스처였다
        # (known_sizing.L=0.5um, W_bounds 1~50um에서 knee를 그대로 쓰면 diode 자기일관
        # 사이징이 W=0.824um로 하한 1um을 깬다). 이제 격자를 선언해도 통과한다 --
        # feasible_L_window()가 diode에 대해 diode_vds_window()로 판정하기 때문이다.
        _diag_spec_ok = _tst_grids({"lut_by_kind": {"nmos": _diag_lut}, "vdd": 1.8, "L_min": 0.5e-6,
                           "W_bounds": (1e-6, 50e-6), "min_vds_by_role": {"mirror": 0.2},
                           "known_sizing": {"Mo": {"ID": 1e-5, "L": 0.5e-6, "vds": 0.6, "vsb": 0.0}}})
        _diag_r1 = diagnose_sizing_roles_gap(_diag_path, _diag_spec_ok)
        assert _diag_r1["status"] == "ok", f"known_sizing으로 다 채웠는데 ok가 아님: {_diag_r1}"

        _diag_spec_novds = dict(_diag_spec_ok, known_sizing={"Mo": {"ID": 1e-5}})
        _diag_r2 = diagnose_sizing_roles_gap(_diag_path, _diag_spec_novds)
        assert _diag_r2["status"] == "gap" and _diag_r2["kind"] == "unresolved_vds_or_L", \
            f"L/VDS 미확정 케이스인데 kind가 다름: {_diag_r2}"
        assert _diag_r2["device"] == "Mo"

        _diag_r3 = diagnose_sizing_roles_gap(_diag_path,
                                               {k: v for k, v in _diag_spec_ok.items() if k != "known_sizing"})
        assert _diag_r3["status"] == "gap" and _diag_r3["kind"] == "unresolved_current", \
            f"seed 자체가 없는 케이스인데 kind가 다름: {_diag_r3}"
        assert _diag_r3["device"] == "Mo" and _diag_r3["ideal_source_hint"] is None, \
            "ideal_sources 선언이 아예 없는 회로인데 hint가 채워짐"


def test_s046_diagnose_sizing_roles_gap(library_dir):
    """[4. 실제 라이브러리 파일 folded_cascode -- 세션35 안에서 이 gap 자체를 해소했다(Ibg를 KCL 유도+자유 theta로 배선) -- 이제 has_theta로 조기 반환됨을 재확인(회귀 감시: diagnose_sizing_roles_gap()이 '더 이상 gap이 아니다'를 정확히 인식하는지)]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S046(줄 1685-1692, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib_dir_recipe = library_dir

    _diag_fc_path = _os.path.join(_lib_dir_recipe, "folded_cascode.topology.json")
    _diag_r4 = diagnose_sizing_roles_gap(_diag_fc_path, {})
    assert _diag_r4["status"] == "has_theta", \
        f"folded_cascode는 세션35에서 Ibg를 free theta로 배선했으니 has_theta여야 하는데: {_diag_r4}"


def test_s047_nmcnr_3stage_topology(library_dir):
    """[5/6. 실제 라이브러리 파일 nmcnr_amplifier -- 원래(세션35) PM_target_deg=46 (논문 실측치)이 nmcnr_3stage_topology()의 PM>60 전제와 충돌해 kind=other로 걸렸고, PM=70으로 그 가드를 우회해도 M101(바이어스 소자, 전류가 KCL만으로 안 나옴)에서 또 다른 unresolved_current gap이 드러났었다(당시 sizing_roles=null). 2026-08-18 세션이 그 M101 tail 전류/M104,M105 폴딩비를 sympy KCL 재유도 + 7개 theta로 실제로 배선했으므로(fold_group/vertical_stack_id 15개 소자 전부 확정 위, PM_target_deg는 아직 46인 채 -- 그건 여전히 별도 gap), 이제 folded_cascode/two_stage_ota와 동일하게 has_theta로 조기 반환되는지 재확인한다(회귀 감시)]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S047(줄 1694-1708, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib_dir_recipe = library_dir

    _diag_nm_path = _os.path.join(_lib_dir_recipe, "nmcnr_amplifier.topology.json")
    _diag_r56 = diagnose_sizing_roles_gap(_diag_nm_path, {})
    assert _diag_r56["status"] == "has_theta", \
        f"nmcnr_amplifier는 2026-08-18에 M101/M104/M105/M106/M107/M108 theta를 배선했으니 " \
        f"has_theta여야 하는데: {_diag_r56}"


def test_s048_require_declared_spec_source(library_dir):
    """[require_declared_spec_source() -- 라이브러리 회로를 **출처 없는 spec**으로
    사이징하려 하면 거부한다. 2026-09-10 사고 재발 방지: 조사 스크립트들이 spec을
    손으로 복붙해 쓰다가 정본(run_harness.SPECS)과 갈렸고(gm_id_grid 21점 vs 57점,
    L_candidates 12점 vs 41점, stage_power_tolerance 누락) 한 세션치 측정이 전부
    비정본 기준이었다. 이 자기시험이 있는 이유는 게이트를 **처음 만들었을 때 그것이
    조용히 죽어 있었기** 때문이다 -- 이 모듈은 os를 최상위 import하지 않는데 게이트
    본문이 os.path를 쓰면서 NameError를 냈고, 그것을 `except Exception: return`이
    삼켜 늘 통과했다. 재발 방지 장치가 재발 방지 없이 죽는 것을 여기서 막는다]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S048(줄 1709-1728, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib_dir_recipe = library_dir

    _rds_lib = _os.path.join(_lib_dir_recipe, "current_reuse_telescopic_ota.topology.json")
    with pytest.raises(ValueError) as _e_rds_info:
        require_declared_spec_source(_rds_lib, {"gm_id_grid": [4.0], "L_candidates": [1e-6]})
    _e_rds = _e_rds_info.value
    assert "_spec_source" in str(_e_rds), f"거부 사유가 출처 선언이 아님: {_e_rds}"
    require_declared_spec_source(_rds_lib, {"gm_id_grid": [4.0],
                                            "_spec_source": "run_harness.SPECS"})
    require_declared_spec_source(_rds_lib, {})
    with _tempfile.TemporaryDirectory() as _rds_tmp:
        _rds_fx = _os.path.join(_rds_tmp, "_fixture.topology.json")
        require_declared_spec_source(_rds_fx, {"gm_id_grid": [4.0]})


def test_s049_section(library_dir):
    """[7. sizing_roles.theta가 이미 선언된 회로는 status=has_theta로 조기 반환]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S049(줄 1730-1735, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib_dir_recipe = library_dir

    _diag_tso_path = _os.path.join(_lib_dir_recipe, "two_stage_ota.topology.json")
    _diag_r7 = diagnose_sizing_roles_gap(_diag_tso_path, {})
    assert _diag_r7["status"] == "has_theta", f"two_stage_ota는 theta가 있는데: {_diag_r7}"


def test_s050_section(s037_state):
    """[제약을 만족하는 격자점이 하나도 없으면 즉시 ValueError]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S050(줄 1736-1751, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _ofc_spec = s037_state._ofc_spec
    _ofc_topo = s037_state._ofc_topo

    _ofc_topo_infeasible = dict(_ofc_topo)
    _ofc_topo_infeasible["sizing_roles"] = dict(_ofc_topo["sizing_roles"])
    _ofc_topo_infeasible["sizing_roles"]["constraints"] = [
        {"metric": "power_A", "op": "<=", "value": 1e-15}]  # 불가능한 제약
    with _tempfile.TemporaryDirectory() as _ofc_tmpdir2:
        _ofc_topo_path2 = _os.path.join(_ofc_tmpdir2, "_test_infeasible.topology.json")
        with open(_ofc_topo_path2, "w", encoding="utf-8") as _f:
            json.dump(_ofc_topo_infeasible, _f)
        with pytest.raises(ValueError):
            optimize_full_circuit_budget(_ofc_topo_path2, _ofc_spec, grid_points_per_theta=5)


@pytest.mark.xfail(raises=ValueError, strict=True,
                   reason="I-C11 two_stage_ota stage1_out KVL -- 담당 Phase 4")
def test_s051_optimize_full_circuit_budget(s051_state):
    """[optimize_full_circuit_budget() -- 실제 회로(two_stage_ota, 7개 소자) 전체를
    spec만 넣고 AI 개입 없이 instance-ready 결과까지 끝까지 실행(배치 7-5 1차 실증,
    2026-07-31) -- device_roles/compensation.stage_devices는 topology.json에 이미
    선언돼 있고(이번에 추가), 이 함수는 그 선언만 읽어 조립한다]

    I-C11(계획, U-09 Phase 4): 지금은 `optimize_full_circuit_budget()`이 two_stage_ota stage1_out KVL ValueError를
    낸다(head 이관본 실행 출력의 '참고(정직한 한계, DC/AC 아키텍처 미분리' 줄). 성공 경로 assert를 그대로 담고
    strict xfail로 둔다(승인 20260922-c9-ic11-split). 지금 동작은 `..._known_limitation`이 단언한다.

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S051(줄 1752-1887)의 `if _tso_result is not None:` 아래
    판정을 조건 밖에서 그대로 옮겼다.
    """
    _tso_path = s051_state._tso_path
    _tso_spec = s051_state._tso_spec

    _tso_result = optimize_full_circuit_budget(_tso_path, _tso_spec)
    _tso_all_names = {"M1", "M2", "M3", "M4", "M5", "M6", "M7"}
    assert set(_tso_result["sizing"].keys()) == _tso_all_names, \
        f"7개 소자 전부 사이징돼야 하는데: {sorted(_tso_result['sizing'].keys())}"
    assert all("W" in _tso_result["sizing"][n] for n in _tso_all_names), "일부 소자에 W가 없음"
    assert _tso_result["pipeline_result"] is not None, "넷리스트 전체가 사이징됐는데 전체 파이프라인이 안 돎"
    assert _tso_result["pipeline_result"]["coverage"].ok, "7개 소자 중 일부가 stick diagram에서 빠짐"
    # 2026-08-05(세션10) -- audit_ok 하드게이트를 뺐다. 격리 스크립트로 확인(diag_m5.py, 세션10):
    # M5(1단 tail)의 전류를 옛 버그(축A 규칙1이 gnd를 레일 제외 없이 2단자로 오판해 M5=M7로
    # 잘못 병합, 173.9uA)로 두면 이 감사가 우연히 PASS했다 -- 올바른 KCL 합(ID(M5)=ID(M1)+
    # ID(M2)=30.1uA, kcl_tail_M5 theta 신설로 이번 세션 정정)으로 고치니 M5의 W가 훨씬
    # 작아져(1.46um->1.12um) M6(199.81um)과의 크기 격차가 커지고 box-shape 비율이 1.5를
    # 넘는다 -- repair_matching_safety()도 못 고친다(M3/M4 common-centroid dx=1.00). 이건
    # L1/L2(matching_pairs 축 분해/그룹핑 규칙) 범위 밖의 별개 문제로, context.md가 이미
    # "L4(사이징->레이아웃 연결) 미설계"로 기록해둔 정직한 한계다(assign_finger_geometry()가
    # 스테이지 간 극단적 W 격차를 아직 모른다) -- 여기서 억지로 고치지 않고 정보로만 출력한다.


def test_s051_optimize_full_circuit_budget_known_limitation(s051_state):
    """[optimize_full_circuit_budget() -- 실제 회로(two_stage_ota, 7개 소자) 전체를
    spec만 넣고 AI 개입 없이 instance-ready 결과까지 끝까지 실행(배치 7-5 1차 실증,
    2026-07-31) -- device_roles/compensation.stage_devices는 topology.json에 이미
    선언돼 있고(이번에 추가), 이 함수는 그 선언만 읽어 조립한다]

    I-C11 지금 동작: ValueError 메시지에 'stage1_out'과 'KVL'이 있다(이관본 except 분기의 조건 그대로 -- 다른 이유의
    ValueError는 이관본도 다시 raise했다).

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S051(줄 1752-1887)의 except 분기 조건.
    """
    _tso_path = s051_state._tso_path
    _tso_spec = s051_state._tso_spec

    with pytest.raises(ValueError) as _tso_e_info:
        optimize_full_circuit_budget(_tso_path, _tso_spec)
    _tso_e = _tso_e_info.value
    assert "stage1_out" in str(_tso_e) and "KVL" in str(_tso_e), \
        f"known-limitation(I-C11)이 아닌 다른 이유의 ValueError(회귀 의심): {_tso_e}"


def test_s052_compensation(toy_lut):
    """[matching_pairs L 강제 일치 -- compensation(spec 기반) vs device_roles.L_role(휴리스틱)이 독립적으로 다른 L을 정했을 때 에러로 끝내지 않고 spec 기반 쪽으로 재설계되는지 확인]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S052(줄 1888-1937, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _lrec_topo = {
        "schema_version": "2.0", "topology_name": "_test_L_reconcile", "source": "self-test",
        "linked_topology_files": [], "_compensation_status": "resolved",
        "netlist": [{"name": "Ma", "kind": "nmos", "source": "gnd", "drain": "d1", "gate": "g1"},
                     {"name": "Mc", "kind": "nmos", "source": "gnd", "drain": "d2", "gate": "g2"},
                     {"name": "Mb", "kind": "nmos", "source": "gnd", "drain": "d3", "gate": "g3"}],
        "symmetry": {"matching_pairs": [{"names": ["Ma", "Mb"], "current_forced": False, "matching_sensitivity": "ratio"}],
                      "dispositions": []},
        "compensation": {"function": "miller_ota_topology",
                          "parameters": ["GBW", "CL", "Z", "NDP"],
                          "stage_devices": [["Ma"], ["Mc"]]},
        # 2026-08-14 세션34 -- gm_id_role을 명시적으로 False로 선언(원래 None) -- Mb(레일
        # 소스+HIGH_Z 드레인, 파트너 없는 고립 소자)가 propose_device_roles_gap_fill()의 새
        # 4번째 소스("gm_id_role=gain" 제안) 대상이 됐다. 이 테스트는 Mb의 matching_pairs를
        # 일부러 current_forced=False로 둬(L_role 재설계만 검증하려는 의도) Mb의 ID를 A엔진이
        # 절대 못 정하게 설계돼 있다 -- 어떤 값이든 gm_id_role이 채워지면(심지어 declared로
        # 직접 줘도) sizing_recipe.py의 gm_id_role 루프가 "ID 없음"으로 즉시 ValueError를
        # 낸다(이 fixture 고유의 제약, 버그 아님). False는 None과 달리 "이미 명시적으로
        # 결정됨(해당없음)"으로 인식돼 gain 제안과 충돌 처리(자동 병합 안 됨 -> review 불필요)
        # 되면서도, falsy라 gm_id_role 루프 자체는 여전히 건너뛴다(None과 동일 동작).
        "device_roles": {"Mb": {"headroom_role": None, "gm_id_role": False,
                                  "L_role": "mirror", "vertical_stack_id": None, "vsb": 0.0}},
    }
    with _tempfile.TemporaryDirectory() as _lrec_tmpdir:
        _lrec_path = _os.path.join(_lrec_tmpdir, "_test_L_reconcile.topology.json")
        with open(_lrec_path, "w", encoding="utf-8") as _f:
            json.dump(_lrec_topo, _f)
        _lrec_spec = _tst_grids({
            "lut_by_kind": {"nmos": lut}, "GBW": 20e6, "CL": 3e-12, "Z": 10.0, "NDP": 4.0,
            "L_candidates": [float(v) for v in lut.L_grid],
            "VDS_candidates": [float(v) for v in lut.VDS_grid],
            "gm_id_grid": [i * 0.5 for i in range(4, 58)],
            "stage_w_max": 200e-6,
            # Mb의 L_role="mirror"이 낼 L(=L_min_by_kind*2.5)이 compensation이 Ma에 고른 L과
            # 반드시 달라지도록 L_min_by_kind를 일부러 compensation 후보와 안 맞는 값으로 지정.
            "L_min_by_kind": {"nmos": 0.35e-6},
        })
        _lrec_result = optimize_full_circuit_budget(_lrec_path, _lrec_spec)
        _La_final = _lrec_result["sizing"]["Ma"]["L"]
        _Lb_final = _lrec_result["sizing"]["Mb"]["L"]
        # Mb가 단독이었으면(=compensation이 안 덮었으면) derive_role_L()이 냈을 값.
        # 2026-09-10 이전에는 `0.35e-6 * 2.5`(select_L_by_role의 고정배수)였다.
        _Lb_heuristic = knee_L_for_kind(_lrec_spec["lut_by_kind"]["nmos"], _lrec_spec)
        assert abs(_La_final - _Lb_final) < 1e-15, \
            f"matching pair L이 여전히 다름(에러 없이 통과했는데 재설계가 안 됨): Ma={_La_final}, Mb={_Lb_final}"
        assert abs(_Lb_heuristic - _La_final) > 1e-15, \
            "테스트 설계 오류 -- L_role 휴리스틱값과 compensation값이 우연히 같아서 재설계 여부를 구분 못 함"


def test_s053_L_role(s052_state, toy_lut):
    """[matching_pairs L 강제 일치 -- 양쪽 다 L_role(휴리스틱)인데 값이 다르면(스펙 근거로 우선순위를 가릴 수 없음) 즉시 ValueError]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S053(줄 1939-1964, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lrec_topo = s052_state._lrec_topo
    lut = toy_lut

    _lrec_topo2 = dict(_lrec_topo)
    _lrec_topo2["netlist"] = [{"name": "Md", "kind": "nmos", "source": "gnd", "drain": "d4", "gate": "g4"},
                                {"name": "Me", "kind": "pmos", "source": "vdd", "drain": "d5", "gate": "g5"}]
    _lrec_topo2["symmetry"] = {"matching_pairs": [{"names": ["Md", "Me"], "current_forced": False, "matching_sensitivity": "ratio"}],
                                 "dispositions": []}
    _lrec_topo2["compensation"] = None
    _lrec_topo2["device_roles"] = {
        "Md": {"headroom_role": None, "gm_id_role": None, "L_role": "mirror",
                "vertical_stack_id": None, "vsb": 0.0},
        "Me": {"headroom_role": None, "gm_id_role": None, "L_role": "bias_replica",
                "vertical_stack_id": None, "vsb": 0.0}}
    with _tempfile.TemporaryDirectory() as _lrec_tmpdir2:
        _lrec_path2 = _os.path.join(_lrec_tmpdir2, "_test_L_reconcile2.topology.json")
        with open(_lrec_path2, "w", encoding="utf-8") as _f:
            json.dump(_lrec_topo2, _f)
        _lrec_spec2 = _tst_grids({"lut_by_kind": {"nmos": lut, "pmos": lut},
                        "L_min_by_kind": {"nmos": 0.35e-6, "pmos": 0.35e-6}})
        with pytest.raises(ValueError):
            optimize_full_circuit_budget(_lrec_path2, _lrec_spec2)


@pytest.mark.xfail(raises=ValueError, strict=True,
                   reason="I-C11 two_stage_ota stage1_out KVL -- 담당 Phase 4")
def test_s054_section(s051_state):
    """[재현성: 같은 spec으로 다시 호출하면 완전히 같은 sizing]

    I-C11: 첫 호출이 ValueError(stage1_out KVL)라 성공 경로(재현성 비교)에 닿지 못한다. 이관본 else 분기의 판정을
    그대로 담고 strict xfail로 둔다(승인 20260922-c9-ic11-split). `_tso_all_names`는 이관본 S051이 성공 분기에서 만든
    이름 그대로다.

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S054(줄 1965-1983)의 else 분기.
    """
    _tso_path = s051_state._tso_path
    _tso_spec = s051_state._tso_spec

    _tso_result = optimize_full_circuit_budget(_tso_path, _tso_spec)
    _tso_all_names = {"M1", "M2", "M3", "M4", "M5", "M6", "M7"}
    _tso_result2 = optimize_full_circuit_budget(_tso_path, _tso_spec)
    for _n in _tso_all_names:
        assert _tso_result["sizing"][_n]["W"] == _tso_result2["sizing"][_n]["W"], \
            f"{_n}: 재실행 결과가 다름 -- 재현성 위반"


def test_s054_section_known_limitation(s051_state):
    """[재현성: 같은 spec으로 다시 호출하면 완전히 같은 sizing]

    I-C11 지금 동작: 첫 호출(이관본 S051)과 재호출(이관본 S054 `if _tso_result is None:` 분기)이 둘 다 같은 이유
    (메시지에 'stage1_out'과 'KVL')의 ValueError다 -- 비결정적 회귀가 아니라는 이관본의 판정 그대로.

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S051 except 분기 조건 + 섹션 S054(줄 1965-1983)의
    거부 try.
    """
    _tso_path = s051_state._tso_path
    _tso_spec = s051_state._tso_spec

    with pytest.raises(ValueError) as _tso_e_info:
        optimize_full_circuit_budget(_tso_path, _tso_spec)
    _tso_e = _tso_e_info.value
    assert "stage1_out" in str(_tso_e) and "KVL" in str(_tso_e), \
        f"known-limitation(I-C11)이 아닌 다른 이유의 ValueError(회귀 의심): {_tso_e}"
    with pytest.raises(ValueError) as _tso_e2_info:
        optimize_full_circuit_budget(_tso_path, _tso_spec)
    _tso_e2 = _tso_e2_info.value
    assert "stage1_out" in str(_tso_e2) and "KVL" in str(_tso_e2), \
        f"재호출이 다른 이유로 실패함(회귀 의심): {_tso_e2}"


def test_s056_noise_1f_density(toy_lut):
    """# 배치 7-3g/h/i(analog-topology-json-library.do.md, 2026-07-31) -- # noise_1f_density()/estimate_mismatch_sigma() + 4개 신규 metric

    [7-3g noise_1f_density() -- SID_1F 없는 LUT는 즉시 ValueError(데이터 없음을 숨기지 않음)]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S056(줄 1988-1993, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    with pytest.raises(ValueError):
        lut.noise_1f_density(15.0, 0.5e-6, 0.6, 0.0, 30e-6)


def test_s057_section(toy_lut):
    """[SID_1F 있는 합성 LUT -- W_ref/W_target 스케일링 + 1/freq 반영 확인]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S057(줄 1995-2007, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    _lut_np = lut.np
    _sid1f_at_wref = 4e-16  # 임의 상수(V^2/Hz @ 1Hz, W_ref 기준) -- 격자 전체 동일값으로 합성
    _sid1f_array = _lut_np.full(lut.ID.shape, _sid1f_at_wref)
    _lut_with_noise = SemiEmpiricalGmIdLUT(lut.L_grid, lut.VGS_grid, lut.VDS_grid, lut.VS_grid,
                                            lut.ID, lut.GM, lut.GDS, lut.CGG, W_ref=lut.W_ref,
                                            SID_1F=_sid1f_array)
    _w_ref_eff = lut._w_ref_effective(0.5e-6)
    _w_target_test = 20e-6
    _freq_test = 10.0
    _sid1f_result = _lut_with_noise.noise_1f_density(15.0, 0.5e-6, 0.6, 0.0, _w_target_test, _freq_test)
    _sid1f_expected = _sid1f_at_wref * _w_ref_eff / _w_target_test / _freq_test
    assert abs(_sid1f_result - _sid1f_expected) / _sid1f_expected < 1e-9


def test_s058__metric_flicker_plus_thermal_sum(s057_state):
    """[_metric_flicker_plus_thermal_sum() -- 열+1/f 합산이 손계산과 일치]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S058(줄 2009-2021, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _freq_test = s057_state._freq_test
    _lut_with_noise = s057_state._lut_with_noise
    _sid1f_expected = s057_state._sid1f_expected
    _w_target_test = s057_state._w_target_test

    _ctx_noise = SizingContext(
        spec={"lut_by_kind": {"nmos": _lut_with_noise}, "freq": _freq_test, "temperature_K": 300.0},
        sized={"M1": {"gm": 200e-6, "gm_id": 15.0, "L": 0.5e-6, "W": _w_target_test,
                       "vds": 0.6, "vsb": 0.0}},
        kind_of={"M1": "nmos"})
    _noise_result = compute_metric({"type": "flicker_plus_thermal_sum", "stages": [["M1"]]}, _ctx_noise)
    _kT = 1.380649e-23 * 300.0
    _s_th_expected = 4 * _kT * (2.0 / 3.0) / 200e-6
    _noise_expected = math.sqrt(_s_th_expected + _sid1f_expected)
    assert abs(_noise_result - _noise_expected) / _noise_expected < 1e-9


def test_s059_estimate_mismatch_sigma():
    """[7-3h estimate_mismatch_sigma()/pelgrom_mismatch metric -- sky130 실측 vth0_slope로 확인]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S059(줄 2022-2035, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _sigma_single = estimate_mismatch_sigma(3.356e-3, 20.0, 0.5)  # W=20um, L=0.5um (NFET)
    assert abs(_sigma_single - 3.356e-3 / math.sqrt(20.0 * 0.5)) < 1e-15

    _ctx_mismatch = SizingContext(
        spec={"vth0_slope": {"nfet": 3.356e-3}},
        sized={"M1a": {"W": 20e-6, "L": 0.5e-6}, "M1b": {"W": 20e-6, "L": 0.5e-6}})
    _pair_sigma = compute_metric(
        {"type": "pelgrom_mismatch", "devices": ["M1a", "M1b"], "kind": "nfet"}, _ctx_mismatch)
    _pair_sigma_expected = math.sqrt(2) * _sigma_single * 1e3
    assert abs(_pair_sigma - _pair_sigma_expected) < 1e-9


def test_s060_section():
    """[7-3i cmrr_estimate/psrr_estimate metric -- diff_pair_tail family 계산 확인]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S060(줄 2036-2045, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _ctx_cmrr = SizingContext(sized={"M5": {"gm": 500e-6, "gds": 5e-6}})  # tail 소자
    _cmrr_db = compute_metric(
        {"type": "cmrr_estimate", "tail_device": "M5", "circuit_family": "diff_pair_tail"}, _ctx_cmrr)
    _ro_tail = 1.0 / 5e-6
    _cmrr_linear_expected = (_ro_tail / 2.0 + 1.0 / 500e-6) * 500e-6
    assert abs(_cmrr_db - 20 * math.log10(_cmrr_linear_expected)) < 1e-9
    _psrr_db = compute_metric(
        {"type": "psrr_estimate", "tail_device": "M5", "circuit_family": "diff_pair_tail"}, _ctx_cmrr)
    assert abs(_psrr_db - 20 * math.log10(500e-6 / 5e-6)) < 1e-9


def test_s061_section(s060_state):
    """[등록 안 된 circuit_family는 즉시 ValueError]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S061(줄 2047-2055, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _ctx_cmrr = s060_state._ctx_cmrr

    with pytest.raises(ValueError):
        compute_metric({"type": "cmrr_estimate", "tail_device": "M5",
                         "circuit_family": "_not_registered_family"}, _ctx_cmrr)


def test_s062_section(library_dir):
    """[세션37: nmcnr_gain_db/nmcnr_pm_deg -- nmcnr_amplifier.topology.json 실제
    connectivity가 metric_spec 소자 역할 배정과 일치하는지 먼저 확인]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S062(줄 2056-2075, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib_dir_recipe = library_dir

    _nmcnr_topo_path = _os.path.join(_lib_dir_recipe, "nmcnr_amplifier.topology.json")
    _nmcnr_transistors, _ = load_topology(_nmcnr_topo_path)
    _nmcnr_by_name = {t.name: t for t in _nmcnr_transistors}
    # stage1 출력(NodeM2)에 M107(캐스코드)/M109(단순 미러) 둘 다 실제로 물려 있는지
    assert _nmcnr_by_name["M107"].drain == _nmcnr_by_name["M109"].drain == "NodeM2", \
        "M107/M109가 실제로 NodeM2에서 만나지 않음 -- stage1 R1 유도의 합류 전제가 깨짐"
    assert _nmcnr_by_name["M107"].source == "NodeF2", "M107.source != NodeF2"
    assert _nmcnr_by_name["M103"].drain == _nmcnr_by_name["M105"].drain == "NodeF2", \
        "M103/M105가 실제로 NodeF2(M107의 폴딩 소스 노드)에서 만나지 않음"
    # stage1 출력이 실제로 gm2 소자(M201)의 게이트로 들어가는지
    assert _nmcnr_by_name["M201"].gate == "NodeM2", "M201.gate != NodeM2 -- gm1->gm2 전달 경로가 아님"
    # stage2 출력(NodeS2)에 M202/M204 둘 다 물려 있고, gm3 소자(M301)의 게이트로 들어가는지
    assert _nmcnr_by_name["M202"].drain == _nmcnr_by_name["M204"].drain == "NodeS2", \
        "M202/M204가 실제로 NodeS2에서 만나지 않음 -- stage2 R2 유도의 합류 전제가 깨짐"
    assert _nmcnr_by_name["M301"].gate == "NodeS2", "M301.gate != NodeS2 -- gm2->gm3 전달 경로가 아님"
    # stage3 출력(Vout)에 M301/M302 둘 다 물려 있는지
    assert _nmcnr_by_name["M301"].drain == _nmcnr_by_name["M302"].drain == "Vout", \
        "M301/M302가 실제로 Vout에서 만나지 않음 -- stage3 R3 유도의 합류 전제가 깨짐"


def test_s063__nmcnr_stage1_rout():
    """[_nmcnr_stage1_rout()/_metric_nmcnr_gain_db/_metric_nmcnr_pm_deg -- 손계산과 대조]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S063(줄 2077-2109, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _nmcnr_spec = {
        "gm1_device": "M102", "gm2_device": "M201", "gm3_device": "M301",
        "stage1_cascode_n": "M107", "stage1_fold_leg_a": "M103", "stage1_fold_leg_b": "M105",
        "stage1_mirror_p": "M109", "stage2_devices": ["M202", "M204"],
        "stage3_devices": ["M301", "M302"], "CL": 1e-10, "kg": 0.5,
    }
    _nmcnr_sized = {
        "M102": {"gm": 1e-3, "gds": 1e-8},
        "M103": {"gm": 1e-3, "gds": 2e-6}, "M105": {"gm": 1e-3, "gds": 2e-6},
        "M107": {"gm": 2e-3, "gds": 1e-6}, "M109": {"gm": 1e-3, "gds": 5e-6},
        "M201": {"gm": 0.2e-3, "gds": 1e-8},
        "M202": {"gm": 1e-3, "gds": 4e-6}, "M204": {"gm": 1e-3, "gds": 4e-6},
        "M301": {"gm": 0.5e-3, "gds": 3e-6}, "M302": {"gm": 1e-3, "gds": 3e-6},
    }
    _nmcnr_ctx = SizingContext(sized=_nmcnr_sized)
    # 손계산: R1(비대칭 -- M107만 캐스코드, M109는 단순 미러)
    _ro103, _ro105, _ro107, _ro109 = 1/2e-6, 1/2e-6, 1/1e-6, 1/5e-6
    _ro_fold_expected = 1.0 / (1.0/_ro103 + 1.0/_ro105)
    _rout_n_expected = 2e-3 * _ro107 * _ro_fold_expected
    _R1_expected = 1.0 / (1.0/_rout_n_expected + 1.0/_ro109)
    _R1_actual = _nmcnr_stage1_rout(_nmcnr_spec, _nmcnr_ctx)
    assert abs(_R1_actual - _R1_expected) / _R1_expected < 1e-9
    _R2_expected = 1.0 / (1.0/(1/4e-6) + 1.0/(1/4e-6))
    _R3_expected = 1.0 / (1.0/(1/3e-6) + 1.0/(1/3e-6))
    _nmcnr_expected = nmcnr_predict_ac_response(1e-3, 0.2e-3, 0.5e-3, _R1_expected, _R2_expected,
                                           _R3_expected, CL=1e-10, kg=0.5)
    _nmcnr_gain_actual = compute_metric({"type": "nmcnr_gain_db", **_nmcnr_spec}, _nmcnr_ctx)
    _nmcnr_pm_actual = compute_metric({"type": "nmcnr_pm_deg", **_nmcnr_spec}, _nmcnr_ctx)
    assert abs(_nmcnr_gain_actual - _nmcnr_expected["dc_gain_db"]) < 1e-9
    assert abs(_nmcnr_pm_actual - _nmcnr_expected["crossings"][0][1]) < 1e-9


def test_s064_section(s063_state):
    """[_metric_nmcnr_pm_deg -- 0dB 교차가 아예 없으면(gm1이 극단적으로 작아 DC이득이 이미 0dB 미만) ValueError]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S064(줄 2111-2122, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _nmcnr_sized = s063_state._nmcnr_sized
    _nmcnr_spec = s063_state._nmcnr_spec

    _nmcnr_sized_low_gain = dict(_nmcnr_sized)
    _nmcnr_sized_low_gain["M102"] = {"gm": 1e-9, "gds": 1e-8}
    _nmcnr_ctx_low = SizingContext(sized=_nmcnr_sized_low_gain)
    with pytest.raises(ValueError):
        compute_metric({"type": "nmcnr_pm_deg", **_nmcnr_spec}, _nmcnr_ctx_low)


def test_s065_section(library_dir):
    """[cmrr_estimate -- telescopic_class_ab family: metric_spec의 소자 역할 배정이
    current_reuse_telescopic_ota.topology.json의 실제 kind/connectivity와 일치하는지
    load_topology()로 먼저 확인 -- 논문 Fig.2를 읽고 손으로 배정한 것을 절대 그대로
    믿지 않는다(topology.json이 유일한 토폴로지 소스 원칙)]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S065(줄 2123-2175, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib_dir_recipe = library_dir

    _crt_topo_path = _os.path.join(_lib_dir_recipe, "current_reuse_telescopic_ota.topology.json")
    _crt_transistors, _ = load_topology(_crt_topo_path)
    _crt_by_name = {t.name: t for t in _crt_transistors}
    _crt_role_map = {"input_p": "M1a", "cascode_p": "M2a", "input_n": "M4a", "cascode_n": "M3a",
                      "tail_p_devices": ["M6", "M7"], "tail_n_device": "M5"}
    assert _crt_by_name["M1a"].kind == "pmos" and _crt_by_name["M2a"].kind == "pmos", \
        "input_p/cascode_p로 배정한 소자가 실제로는 pmos가 아님"
    assert _crt_by_name["M4a"].kind == "nmos" and _crt_by_name["M3a"].kind == "nmos", \
        "input_n/cascode_n으로 배정한 소자가 실제로는 nmos가 아님"
    assert all(_crt_by_name[d].kind == "pmos" for d in _crt_role_map["tail_p_devices"]), \
        "tail_p_devices가 실제로는 pmos가 아님"
    assert _crt_by_name["M5"].kind == "nmos", "tail_n_device가 실제로는 nmos가 아님"
    # ---- 위상 가정 검증(2026-08-03 전면 정정) --------------------------------------
    # 옛 assert는 `M2a.drain == M3a.source`, 즉 "PMOS 캐스코드의 드레인이 NMOS 캐스코드의
    # 소스로 이어지는 **하나의 직렬 텔레스코픽 기둥**"을 가정했다. 확정된 topology.json은
    # 그렇지 않다 -- 이 회로는 current-reuse라서 PMOS 가지(M1a→M2a, tail=Vx)와 NMOS 가지
    # (M4a→M3a, tail=Vy)가 **각각 독립**이고 출력노드에서 **드레인끼리** 만난다.
    # CMRR 폐형식(_cmrr_telescopic_class_ab docstring)이 실제로 전제하는 것은 다음 4가지다.
    # (1) 각 가지가 '입력쌍 drain == 캐스코드 source'인 직렬 캐스코드일 것 (Kp'/Kn' 성립)
    assert _crt_by_name["M1a"].drain == _crt_by_name["M2a"].source, \
        "M1a/M2a가 PMOS 직렬 캐스코드가 아님(M1a.drain != M2a.source) -- Kp' 전제가 깨짐"
    assert _crt_by_name["M4a"].drain == _crt_by_name["M3a"].source, \
        "M4a/M3a가 NMOS 직렬 캐스코드가 아님(M4a.drain != M3a.source) -- Kn' 전제가 깨짐"
    # (2) 두 가지가 같은 출력노드에서 **드레인끼리** 만날 것 (Kp'∥Kn', Acm의 병렬 합류)
    _crt_vom1 = _crt_by_name["M2a"].drain
    _crt_vop1 = _crt_by_name["M2b"].drain
    assert _crt_by_name["M3a"].drain == _crt_vom1, \
        "M2a/M3a가 같은 출력노드에서 드레인끼리 만나지 않음 -- CMRR 공식의 합류 전제가 깨짐"
    assert _crt_by_name["M3b"].drain == _crt_vop1 and _crt_vom1 != _crt_vop1, \
        "b측(M2b/M3b)이 a측과 대칭인 별도 출력노드를 이루지 않음"
    # (3) 옛 직렬 기둥 가정이 **아님**을 명시적으로 고정(회귀 방지)
    assert _crt_by_name["M2a"].drain != _crt_by_name["M3a"].source, \
        "M2a.drain == M3a.source -- 옛(직렬 캐스코드) 위상이다. 이 JSON/공식과 맞지 않음"
    # (4) 두 가지가 **서로 다른** tail을 가질 것(Vx=M6∥M7, Vy=M5) -- Rx/Ry가 별개인 전제
    assert _crt_by_name["M6"].drain == _crt_by_name["M7"].drain == _crt_by_name["M1a"].source, \
        "M6/M7/M1a가 같은 Vx(tail) 노드를 공유하지 않음"
    assert _crt_by_name["M1a"].source == _crt_by_name["M1b"].source, "M1a/M1b가 tail Vx를 공유 안 함"
    assert _crt_by_name["M4a"].source == _crt_by_name["M5"].drain, \
        "M4a/M5가 같은 Vy(tail) 노드를 공유하지 않음"
    assert _crt_by_name["M4a"].source == _crt_by_name["M4b"].source, "M4a/M4b가 tail Vy를 공유 안 함"
    assert _crt_by_name["M1a"].source != _crt_by_name["M4a"].source, \
        "Vx와 Vy가 같은 노드다 -- tail이 둘로 분리돼 있다는 Rx/Ry 전제가 깨짐"
    # (5) 두 입력쌍이 같은 입력을 공유할 것(current-reuse의 정의: M1a/M4a 게이트가 둘 다 Vip)
    assert _crt_by_name["M1a"].gate == _crt_by_name["M4a"].gate, \
        "M1a/M4a가 같은 입력(Vip)을 공유하지 않음 -- (gmp+gmn) 합산 전제가 깨짐"
    assert _crt_by_name["M1b"].gate == _crt_by_name["M4b"].gate != _crt_by_name["M1a"].gate, \
        "M1b/M4b가 같은 반대편 입력(Vim)을 공유하지 않음"


def test_s067_family(s065_state):
    """[cmrr_estimate -- telescopic_class_ab_cmfb family(2026-08-03 신규 유도, CMFB 루프
    포함): 먼저 metric_spec의 CMFB 소자 역할 배정이 topology.json netlist와 실제로
    일치하는지 load_topology()로 확인 -- 손 배정을 그대로 믿지 않는다]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S067(줄 2221-2269, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _crt_by_name = s065_state._crt_by_name
    _crt_transistors = s065_state._crt_transistors

    _cmfb_roles = {"cmfb_ctrl_device": "M7", "cmfb_amp_sense": "M37a", "cmfb_amp_ref": "M37b",
                    "cmfb_load_sense": "M36a", "cmfb_load_ref": "M36b",
                    "cmfb_tail_device": "M38", "cmfb_stage2_devices": ["M15", "M16"]}
    # (1) M7이 정말 'gate=Vcmfb인 PMOS tail 전류원'이고, 그 Vcmfb는 M36a **자신의 diode 노드**다
    #     (2026-08-03 정정: 이전엔 M36b가 미러로 Vcmfb를 만든다고 봤으나 오독이었다).
    _vcmfb_net = _crt_by_name["M7"].gate
    assert _crt_by_name["M7"].kind == "pmos" and _crt_by_name["M7"].drain == _crt_by_name["M1a"].source, \
        "cmfb_ctrl_device(M7)가 Vx(stage-1 PMOS tail) 노드를 구동하지 않음"
    assert (_crt_by_name["M36a"].gate == _crt_by_name["M36a"].drain == _vcmfb_net
            and _crt_by_name["M36a"].source == "vdd" and _crt_by_name["M36a"].kind == "pmos"), \
        "M36a가 'vdd에 source를 둔 diode이고 그 diode 노드가 곧 Vcmfb(M7.gate)'가 아님"
    assert _crt_by_name["M37a"].drain == _vcmfb_net, \
        "M37a(gate=Voc)의 drain이 Vcmfb가 아님 -- 감지쪽 다리에서 출력을 뽑는다는 전제가 깨짐"
    # (2) M36b는 M36a의 미러가 아니라 **완전히 독립된 자기 자신의 diode**(게이트가 안 묶인다).
    assert _crt_by_name["M36b"].gate == _crt_by_name["M36b"].drain != _vcmfb_net, \
        "M36b가 자기 자신의 독립 diode가 아님"
    assert _crt_by_name["M36a"].gate != _crt_by_name["M36b"].gate, \
        "M36a/M36b의 게이트가 묶여 있다 -- 이건 폐기된 'current mirror 부하' 오독이다"
    assert _crt_by_name["M36b"].drain == _crt_by_name["M37b"].drain, "M36b/M37b가 같은 노드가 아님"
    # (3) M37a/M37b는 tail(M38)을 공유하는 차동쌍.
    assert _crt_by_name["M37a"].source == _crt_by_name["M37b"].source == _crt_by_name["M38"].drain, \
        "M37a/M37b/M38이 같은 CMFB tail 노드를 공유하지 않음"
    # (4) Voc_des(M37b의 기준입력)는 M39/M40 **PMOS diode 2개짜리 저임피던스 분압기**의 중간노드다:
    #     M39(source=vdd, gate=drain=Voc_des), M40(source=Voc_des, gate=drain=gnd). 이 구조라야
    #     소신호로 v(Voc_des)=0이 되고, M39/M40이 A_c 식에서 사라진다(유도의 핵심 전제).
    _vocdes_net = _crt_by_name["M37b"].gate
    assert (_crt_by_name["M39"].kind == "pmos" and _crt_by_name["M39"].source == "vdd"
            and _crt_by_name["M39"].gate == _crt_by_name["M39"].drain == _vocdes_net), \
        "M39가 'vdd->Voc_des PMOS diode'가 아님"
    assert (_crt_by_name["M40"].kind == "pmos" and _crt_by_name["M40"].source == _vocdes_net
            and _crt_by_name["M40"].gate == _crt_by_name["M40"].drain == "gnd"), \
        "M40이 'Voc_des->gnd PMOS diode'가 아님 -- v(Voc_des)=0 전제가 깨져 A_c 유도가 무효"
    assert not any(t.drain == _vocdes_net or t.source == _vocdes_net
                   for t in _crt_transistors if t.name not in ("M39", "M40")), \
        "Voc_des에 M39/M40 말고 다른 구동소자가 생겼다 -- v(Voc_des)=0 전제 재검토 필요"
    # (5) Voc(M37a의 게이트)를 구동하는 트랜지스터는 없다 -- 논문 Fig.5의 R1/R2 저항 평균망은
    #     트랜지스터가 아니라 이 스키마(kind: pmos/nmos)에 못 들어가기 때문이다. 그 사실 자체를
    #     회귀로 고정하고, R1/R2가 감지하는 대상(최종출력 CM)은 cmfb_stage2_devices로 표현한다.
    _voc_net = _crt_by_name["M37a"].gate
    assert not any(t.drain == _voc_net or t.source == _voc_net for t in _crt_transistors), \
        f"{_voc_net!r}를 구동하는 소자가 생겼다 -- R1/R2 감지망 모델링(cm_sense_gain)을 재검토할 것"
    assert all(_crt_by_name[d].drain == _crt_by_name["M15"].drain
               for d in _cmfb_roles["cmfb_stage2_devices"]), \
        "cmfb_stage2_devices가 같은 2단 출력노드(Vom)를 구동하지 않음"


def test_s070_section(assets_dir):
    """[smallsignal_ratio_db/smallsignal_gain_db -- topology-무관 일반화(세션21 2차)]
    cmrr/psrr/gain_db를 회로 전용 Python 함수 없이 topology.json의 metric_spec
    선언만으로 계산 -- 51소자(1단+2단+CMFB+bias-gen 전부) + R1/R2(1GΩ 근사)를
    통째로 수치 MNA로 풀고 ports가 선언한 진짜 최종출력(Vop/Vom)에서 잰다.
    ngspice AC 독립 교차검증: stage3_full_circuit_ngspice_crosscheck.py]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S070(줄 2361-2428, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _full_sized = {
        "M1a": {"gm": 119e-6, "gds": 1/600e3}, "M1b": {"gm": 119e-6, "gds": 1/600e3},
        "M2a": {"gm": 130e-6, "gds": 1/700e3}, "M2b": {"gm": 130e-6, "gds": 1/700e3},
        "M4a": {"gm": 140e-6, "gds": 1/250e3}, "M4b": {"gm": 140e-6, "gds": 1/250e3},
        "M3a": {"gm": 150e-6, "gds": 1/300e3}, "M3b": {"gm": 150e-6, "gds": 1/300e3},
        "M6": {"gm": 0.0, "gds": 0.5e-6}, "M7": {"gm": 90e-6, "gds": 0.4e-6},
        "M5": {"gm": 0.0, "gds": 1.0e-6},
        "M8": {"gm": 40e-6, "gds": 0.3e-6}, "M17": {"gm": 40e-6, "gds": 0.3e-6},
        "M9a": {"gm": 50e-6, "gds": 0.4e-6}, "M9b": {"gm": 50e-6, "gds": 0.4e-6},
        "M18a": {"gm": 50e-6, "gds": 0.4e-6}, "M18b": {"gm": 50e-6, "gds": 0.4e-6},
        "M11a": {"gm": 30e-6, "gds": 0.5e-6}, "M11b": {"gm": 30e-6, "gds": 0.5e-6},
        "M20a": {"gm": 30e-6, "gds": 0.5e-6}, "M20b": {"gm": 30e-6, "gds": 0.5e-6},
        "M12": {"gm": 0.0, "gds": 0.6e-6}, "M21": {"gm": 0.0, "gds": 0.6e-6},
        "M10": {"gm": 0.0, "gds": 0.6e-6}, "M19": {"gm": 0.0, "gds": 0.6e-6},
        "M13": {"gm": 40e-6, "gds": 0.3e-6}, "M22": {"gm": 40e-6, "gds": 0.3e-6},
        "M14a": {"gm": 30e-6, "gds": 0.5e-6}, "M14b": {"gm": 30e-6, "gds": 0.5e-6},
        "M23a": {"gm": 30e-6, "gds": 0.5e-6}, "M24b": {"gm": 30e-6, "gds": 0.5e-6},
        "M15": {"gm": 3.0e-3, "gds": 8e-6}, "M16": {"gm": 3.0e-3, "gds": 9e-6},
        "M25": {"gm": 3.0e-3, "gds": 8e-6}, "M26": {"gm": 3.0e-3, "gds": 9e-6},
        "M37a": {"gm": 100e-6, "gds": 1.0e-6}, "M37b": {"gm": 105e-6, "gds": 1.1e-6},
        "M36a": {"gm": 80e-6, "gds": 0.8e-6}, "M36b": {"gm": 84e-6, "gds": 0.9e-6},
        "M38": {"gm": 0.0, "gds": 1.2e-6},
        "M18_bg": {"gm": 40e-6, "gds": 0.3e-6},
        "M60": {"gm": 40e-6, "gds": 0.3e-6}, "M61": {"gm": 40e-6, "gds": 0.3e-6},
        "M64": {"gm": 30e-6, "gds": 0.5e-6}, "M63": {"gm": 30e-6, "gds": 0.5e-6},
        "M58": {"gm": 30e-6, "gds": 0.5e-6}, "M57": {"gm": 30e-6, "gds": 0.5e-6},
        "M66": {"gm": 0.0, "gds": 0.6e-6}, "M68": {"gm": 0.0, "gds": 0.6e-6},
        "M39": {"gm": 40e-6, "gds": 0.3e-6}, "M40": {"gm": 40e-6, "gds": 0.3e-6},
    }
    _full_topo_path = _os_ss.path.join(
        assets_dir,
        "library", "current_reuse_telescopic_ota.topology.json")
    _full_ctx = SizingContext(sized=_full_sized, topology_path=_full_topo_path)
    _ss_cmrr_spec = {"type": "smallsignal_ratio_db",
                      "excite_num": {"Vip": 0.5, "Vim": -0.5}, "sense_num": "diff",
                      "excite_den": {"Vip": 1.0, "Vim": 1.0}, "sense_den": "common",
                      "sense_p": "Vop", "sense_n": "Vom"}
    _ss_psrr_spec = {"type": "smallsignal_ratio_db",
                      "excite_num": {"Vip": 0.5, "Vim": -0.5}, "sense_num": "diff",
                      "excite_den": {"vdd": 1.0}, "sense_den": "common",
                      "sense_p": "Vop", "sense_n": "Vom"}
    _ss_gain_spec = {"type": "smallsignal_gain_db", "excite": {"Vip": 0.5, "Vim": -0.5},
                      "sense_mode": "diff", "sense_p": "Vop", "sense_n": "Vom"}
    _ss_cmrr = compute_metric(_ss_cmrr_spec, _full_ctx)
    _ss_psrr = compute_metric(_ss_psrr_spec, _full_ctx)
    _ss_gain = compute_metric(_ss_gain_spec, _full_ctx)
    # ngspice AC 실측(stage3_full_circuit_ngspice_crosscheck.py, 같은 파라미터):
    # gain=99.0154dB(오차<0.001dB), PSRR=105.5051dB(오차<0.001dB),
    # CMRR=125.1843dB(오차 0.58dB -- CMFB로 심하게 억제된 Acm의 수치조건, 이 프로젝트
    # 기존 CMFB 교차검증 허용오차 범위 내 -- session20-B 앵커도 worst 3.99dB였다).
    assert abs(_ss_gain - 99.01539878703716) < 1e-6, f"gain_full_circuit_db 자기회귀: {_ss_gain}"
    assert abs(_ss_gain - 99.0154) < 0.01, f"gain ngspice 대조(99.0154dB)와 어긋남: {_ss_gain}"
    assert abs(_ss_psrr - 105.50510696686493) < 1e-6, f"psrr(신규) 자기회귀: {_ss_psrr}"
    assert abs(_ss_psrr - 105.5051) < 0.01, f"psrr ngspice 대조(105.5051dB)와 어긋남: {_ss_psrr}"
    assert abs(_ss_cmrr - 125.76715845307814) < 1e-6, f"cmrr(신규) 자기회귀: {_ss_cmrr}"
    assert abs(_ss_cmrr - 125.1843) < 1.0, f"cmrr ngspice 대조(125.1843dB)와 어긋남(오차<1dB 기대): {_ss_cmrr}"
    # bias-gen이 vdd 리플을 그대로 따라간다는 것도 회귀로 고정(세션21 2차의 핵심 발견 --
    # 이상적 전류원 Iref를 개방회로로 다루면 diode-connected M18_bg가 Vbias1=vdd를 강제).
    _sol_vdd = _full_circuit_response(_full_ctx, {"vdd": 1.0}, also_fix=frozenset({"Vip", "Vim"}))
    assert abs(_sol_vdd["Vbias1"] - 1.0) < 1e-9, f"Vbias1이 vdd를 그대로 안 따라감: {_sol_vdd['Vbias1']}"


def test_s071_current_reuse_telescopic_topology(toy_lut):
    """# current_reuse_telescopic_topology() 등록 재확인(2026-07-31, 원문 Eq.2-6 재도출 후,
    # gmp/gmn/gm2 3-stage로 재설계 -- stage_devices 계약을 안 바꾸고 '분배'를 topology_fn
    # 자신이 하도록 함, 사용자와 함께 설계. 2026-08-12(세션30) gmp2/gmn2 4-stage로 확장)
    # -- 실제(toy) LUT로 optimize_multistage() 고정점 반복 실행.
    # [!] 실측 발견(2026-07-31): gm2/Cgg2(2단)는 5회 안에 안정적으로 수렴하지만,
    # gmp/gmn(1단, Cgg1_total 되먹임)은 이 toy LUT에서 3-주기 한계 순환(limit cycle)에
    # 빠진다 -- find_optimal_sizing()의 objective=power 동점 처리가 Cgg1이 미세하게
    # 바뀔 때마다 서로 다른 (L,VDS,gm_id) 격자점으로 튀는 현상(배치 7-1이 이미 발견한
    # '동점은 격자 순서에 의존' 현상과 같은 근본원인). damping(under-relaxation)으로
    # 막아보려 했으나 진동의 주기/진폭만 바뀔 뿐 근본적으로 없어지지 않음을 실측 확인 --
    # 그래서 optimize_multistage()에 순환 감지+평균 fallback을 추가했다(이 함수 docstring
    # 참고): max_iter를 다 쓰고도 1-스텝 수렴에 실패하면 최근 이력에서 반복 주기를 찾아
    # 그 구간의 gm 평균으로 재sizing한 안정된 추정치를 cycle_detected=True로 반환한다.

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S071(줄 2429-2476, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    lut = toy_lut

    assert "current_reuse_telescopic_topology" in _COMPENSATION_REGISTRY
    _crt_tf = _COMPENSATION_REGISTRY["current_reuse_telescopic_topology"](
        t_lln=30e-9, PM_target_deg=70.0, Cc=500e-15, Cf=500e-15, Cs=500e-15, C_Ltot=1e-12)
    # 2026-08-12(세션30) -- stage_fT_targets(새로 노출된 준정적 검증 기준주파수)가 이
    # toy LUT(EKV 해석식, 실제 sky130 특성과 다름)에서 우연히 이 한계 순환을 유발하던
    # 동점 후보들을 걸러내 버려 converged=True로 바뀐다(실측 확인) -- fT 기능 자체는
    # 아래 L5c(실제 sky130 LUT, 51소자 전체회로) self-test가 이미 검증하므로, 이 테스트의
    # 진짜 목적(순환 감지+평균 fallback 코드 경로 자체를 계속 실행해보는 것)을 지키려고
    # 이 toy 시나리오에서만 껐다 -- fT 기능과 cycle-detection 기능은 서로 독립적인 관심사.
    _crt_tf.stage_fT_targets = None
    _crt_result = optimize_multistage(
        _crt_tf, [lut, lut, lut, lut], [float(v) for v in lut.L_grid], [float(v) for v in lut.VDS_grid],
        [i * 0.5 for i in range(4, 58)], objective="power", w_max=200e-6, max_iter=20)
    assert _crt_result is not None, "optimize_multistage()가 실행가능점을 못 찾음"
    assert abs(_crt_result["gms"][0] - _crt_result["gms"][1]) < 1e-9, "gmp != gmn(Eq.5 위반)"
    assert _crt_result["gms"][2] > 0 and _crt_result["cggs"][2] > 0, "gmp2/Cgg2(PMOS)가 비정상"
    assert _crt_result["gms"][3] > 0 and _crt_result["cggs"][3] > 0, "gmn2/Cgg2(NMOS)가 비정상"
    assert abs(_crt_result["gms"][2] - _crt_result["gms"][3]) < 1e-9, \
        "gmp2 != gmn2(세션30 50:50 기본 분할 위반) -- 이 toy LUT 자체엔 shared_gm_id_groups를 " \
        "안 넘겼으니 gm 목표값 자체(topology_fn 반환)가 이미 같아야 한다"
    assert _crt_result["converged"] is False, "이 toy LUT는 원래 한계 순환에 빠져야 하는데 수렴함 -- 회귀 확인 필요"
    assert _crt_result["cycle_detected"] is True, "순환 감지 fallback이 발동하지 않음"
    assert _crt_result["cycle_period"] == 3, f"예상 밖 순환 주기: {_crt_result['cycle_period']}"
    _crt_cgg1_total = _crt_result["cggs"][0] + _crt_result["cggs"][1]
    _crt_beta_final = 500e-15 / (500e-15 + 500e-15 + _crt_cgg1_total)
    _crt_gm2_total = _crt_result["gms"][2] + _crt_result["gms"][3]


def test_s073_section():
    """# validate_theta_declaration_order() -- theta 배열 '선언 순서=실행 순서' 계약 # 위반을 읽기 전용으로 검사(2026-08-13 세션31, mirror_M18a/L_stage2out_p·n에서 # 실제로 두 번 발생한 순서 버그의 재발 방지 안전망, .ai/context.md BI~BL 참고)

    [합성 fixture -- gm_id_match_vgs_of/C타입 reference가 선언 순서를 위반하면 잡아내는지]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S073(줄 2481-2501, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _vtdo_bad1 = {
        "compensation": {"stage_devices": [["A"]]},
        "sizing_roles": {"theta": [
            {"name": "theta_n", "bounds": [0, 1], "feeds": {
                "type": "metric_stage_budget", "metric": "gain_db", "devices": ["B"],
                "gm_id_match_vgs_of": "A2"}},
            {"name": "theta_p", "bounds": [0, 1], "feeds": {
                "type": "metric_stage_budget", "metric": "gain_db", "devices": ["A2"]}},
        ]}}
    _vtdo_v1 = validate_theta_declaration_order(_vtdo_bad1)
    assert len(_vtdo_v1) == 1 and _vtdo_v1[0]["theta"] == "theta_n", \
        f"gm_id_match_vgs_of 순서위반을 못 잡음: {_vtdo_v1}"

    _vtdo_bad2 = {"compensation": None, "sizing_roles": {"theta": [
        {"name": "c_theta", "bounds": [0, 1], "feeds": {"type": "C", "target": "X", "reference": "Y"}},
        {"name": "y_theta", "bounds": [0, 1], "feeds": {"type": "C", "target": "Y", "reference": "Z"}},
    ]}}
    _vtdo_v2 = validate_theta_declaration_order(_vtdo_bad2)
    assert {v["theta"] for v in _vtdo_v2} == {"c_theta", "y_theta"}, \
        f"C타입 reference 연쇄 순서위반을 못 잡음: {_vtdo_v2}"


def test_s074_section():
    """[올바른 순서(reference가 앞에 옴)면 위반 0건인지]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S074(줄 2503-2508, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _vtdo_good = {"compensation": {"stage_devices": [["W"]]}, "sizing_roles": {"theta": [
        {"name": "z_theta", "bounds": [0, 1], "feeds": {"type": "C", "target": "Z", "reference": "W"}},
        {"name": "y_theta", "bounds": [0, 1], "feeds": {"type": "C", "target": "Y", "reference": "Z"}},
    ]}}
    assert validate_theta_declaration_order(_vtdo_good) == [], "올바른 순서인데 위반으로 오탐"


def test_s075_section():
    """[compensation.stage_devices는 처음부터 생산됨으로 취급되는지]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S075(줄 2510-2515, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _vtdo_comp = {"compensation": {"stage_devices": [["M1a", "M1b"]]}, "sizing_roles": {"theta": [
        {"name": "c_theta", "bounds": [0, 1], "feeds": {"type": "C", "target": "M2", "reference": "M1a"}},
    ]}}
    assert validate_theta_declaration_order(_vtdo_comp) == [], \
        "compensation이 이미 sizing한 소자를 참조했는데 오탐 발생"


def test_s076_section(library_dir):
    """[실제 library topology.json 4개 전부 위반 0건인지(reorder 이후 회귀 확인)]

    oracle (c) 이관본 legacy/selftest_sizing_recipe.py 섹션 S076(줄 2517-2527, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _vtdo_lib = library_dir
    for _vtdo_path in sorted(_vtdo_glob.glob(_os.path.join(_vtdo_lib, "*.topology.json"))):
        with open(_vtdo_path, "r", encoding="utf-8") as _vtdo_f:
            _vtdo_data = json.load(_vtdo_f)
        _vtdo_meta = {"sizing_roles": _vtdo_data.get("sizing_roles"),
                      "compensation": _vtdo_data.get("compensation")}
        _vtdo_v = validate_theta_declaration_order(_vtdo_meta)
        _vtdo_name = _os.path.basename(_vtdo_path)
        assert _vtdo_v == [], f"{_vtdo_name}에 선언 순서 위반: {_vtdo_v}"
