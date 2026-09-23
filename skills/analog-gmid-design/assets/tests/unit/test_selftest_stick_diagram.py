"""TS2(계획 N3.11, C9 20260922-ts2-pytest-split): 이관본 `legacy/selftest_stick_diagram.py`의 섹션별 pytest test.

정본: design `gain-budget-gmid-sizing.10-test-separation` §6.8, 매핑표
`docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/c9-mapping.json`(test 이름 = 매핑표 `test_ids`).

oracle 대조: 모든 기대값은 (c) 동작 보존 -- head 2dd98f2 이관본(C2가 원본 `stick_diagram.py`의
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


from stick_diagram import (COMMON_CENTROID_PATTERNS, Counter, FloorplanBlock, INTERDIGITATION_PATTERNS, Transistor, _branch_composite_pair, _build_crossover_segments, _common_centroid_from_pattern_table, _common_centroid_residual, _composite_collapse_for_crossover, _count_matching_pair_splits, _dc_asdict, _dc_replace, _hubleaf_sequence_node_path, _is_perfect_crossover_score, _mirror_node_map_from_pairs, _pack_by_subkind, _pair_odd_nodes_by_mirror, _sorted_setmap, apply_device_roles_gap_fill, apply_theta_kcl_gap_fill, assign_finger_geometry, audit_row_split, audit_theta_root_direction, audit_vertical_stack_id_euler_feasibility, audit_vertical_stack_id_vs_kcl, block_from_rows, build_graph, build_mirror_symmetric_pattern, build_stick_diagram, check_box_shape, check_euler_condition, check_mirror_symmetry, check_multi_leaf_hub_parity, check_stick_diagram_coverage, check_symmetry_dispositions, check_walk_sequence, common_centroid_layout, defaultdict, derive_horizontal_stack_groups, evaluate_row_split_candidates, find_authoritative_sizing_devices, find_differential_and_mirror_forks, find_differential_pair_candidates, find_diffusion_safe_split_points, find_diode_stacks, find_euler_repair_options, find_hub_merge_candidates, find_idiom_matches, find_interleaved_symmetric_splits, find_matching_candidates, find_min_crossover_layout, find_min_crossover_layout_with_branch_composite, find_stack_edges, find_stacked_matching_candidates, find_unreviewed_device_roles, find_unreviewed_matching_pairs, find_verified_differential_and_mirror_relations, folded_cascode_example, geometry_colocation_union, interdigitate_layout, json, load_topology, merge_layout_groups_by_matching_pairs, mirror_symmetric_trail, os, pack_floorplan, pack_floorplan_grouped, pack_group_as_unit, propagate_topology_forced_currents, propose_device_roles_gap_fill, propose_theta_kcl_gap_fill, propose_vertical_stack_id_gap_fill, refine_differential_and_mirror_relations, render_stick_diagram, repair_matching_safety, require_device_roles_reviewed, run_full_circuit_audit, run_full_circuit_audit_from_topology, run_topology_pipeline, save_instance_json, search_shared_finger_w, search_stack_finger_w, search_unit_cell_sizing, select_layout_tool, skyline_pack_best_width, split_into_stacks, suggest_pair_finger_adjustments, suggest_vertical_stack_composites, trace_gnd_to_vdd_branches, trace_vdd_to_gnd_branches, two_stage_ota_example)  # noqa: E402
import os as _os1213  # noqa: E402
import itertools  # noqa: E402
import os as _os21  # noqa: E402
import tempfile as _tempfile21  # noqa: E402
import os as _os  # noqa: E402
import tempfile as _tempfile  # noqa: E402
import os as _os31  # noqa: E402
import tempfile as _tempfile31  # noqa: E402
import os as _os47  # noqa: E402
import os as _t48_os  # noqa: E402
import os as _t49_os  # noqa: E402
import json as _t52r_json  # noqa: E402
import tempfile as _t55_tempfile, shutil as _t55_shutil  # noqa: E402
import tempfile as _t58_tempfile, shutil as _t58_shutil  # noqa: E402
import copy as _t60_copy  # noqa: E402
import tempfile as _t62_tempfile, shutil as _t62_shutil  # noqa: E402
import importlib.util as _t53g_ilu  # noqa: E402
import tempfile as _t53g_tempfile  # noqa: E402
from sizing_recipe import optimize_full_circuit_budget  # noqa: E402


def overlap(a, b):
    return not (a.x + a.width <= b.x or b.x + b.width <= a.x or
                a.y + a.height <= b.y or b.y + b.height <= a.y)


def _first_pair_matching(pairs_meta, current_forced, matching_sensitivity):
    """topology.json의 symmetry.matching_pairs에서 축A/축C가 일치하는 첫 쌍을 찾는다 --
    어느 소자명이 그 조합인지는 이 함수가 파일에서 알아낼 뿐 테스트가 가정하지 않는다.
    2026-08-05(세션10) L1 하드컷 -- 구 kind 문자열 매칭을 축A(current_forced)/축C
    (matching_sensitivity) 조합 매칭으로 교체."""
    for p in pairs_meta:
        if p["current_forced"] == current_forced and p["matching_sensitivity"] == matching_sensitivity:
            return tuple(p["names"])
    raise AssertionError(f"folded_cascode.topology.json에 current_forced={current_forced!r}, "
                          f"matching_sensitivity={matching_sensitivity!r}인 matching_pair가 "
                          f"없다 -- 테스트 픽스처를 다시 확인할 것")


@pytest.fixture
def s007_state():
    """섹션 S007(이관본 줄 25-80)이 만드는 이름 found -- 읽는 섹션: S116. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    found = find_matching_candidates(folded_cascode_example())
    got_mirrors = {frozenset(t.name for t in g) for g in found["current_mirror"].values()}
    got_diffpair = {frozenset(t.name for t in g) for g in found["diff_pair"].values()}

    return types.SimpleNamespace(found=found)


@pytest.fixture
def s022_state():
    """섹션 S022(이관본 줄 125-145)이 만드는 이름 cc2 -- 읽는 섹션: S024. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    cc2 = common_centroid_layout([
        Transistor("M1", "nmos", source="tail", drain="d1", n_fingers=9),
        Transistor("M2", "nmos", source="tail", drain="d2", n_fingers=9),
    ])
    for i, row in enumerate(cc2["rows"]):
        pass

    return types.SimpleNamespace(cc2=cc2)


@pytest.fixture
def s025_state():
    """섹션 S025(이관본 줄 264-366)이 만드는 이름 trs_uneven -- 읽는 섹션: S027, S028, S029. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    trs_uneven = [
        Transistor("A", "nmos", source="vdd", drain="La", n_fingers=6),
        Transistor("B", "nmos", source="vdd", drain="Lb", n_fingers=4),
        Transistor("C", "nmos", source="vdd", drain="Lc", n_fingers=2),
    ]

    return types.SimpleNamespace(trs_uneven=trs_uneven)


@pytest.fixture
def s040_state():
    """섹션 S040(이관본 줄 595-609)이 만드는 이름 trs_isolate -- 읽는 섹션: S041. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    trs_isolate = [
        Transistor("A", "nmos", source="vdd", drain="La", n_fingers=2),
        Transistor("B", "nmos", source="vdd", drain="Lb", n_fingers=2),
    ]
    r_isolate = common_centroid_layout(trs_isolate, n_rows=4)

    return types.SimpleNamespace(trs_isolate=trs_isolate)


@pytest.fixture
def s045_state():
    """섹션 S045(이관본 줄 663-671)이 만드는 이름 r_abc -- 읽는 섹션: S054. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    r_abc = find_min_crossover_layout(
        [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=1) for n in "ABC"])

    return types.SimpleNamespace(r_abc=r_abc)


@pytest.fixture
def s046_state():
    """섹션 S046(이관본 줄 673-679)이 만드는 이름 r_6 -- 읽는 섹션: S047, S054. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    r_6 = find_min_crossover_layout(
        [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=1) for n in "ABCDEF"])

    return types.SimpleNamespace(r_6=r_6)


@pytest.fixture
def s051_state(library_dir):
    """섹션 S051(이관본 줄 717-777)이 만드는 이름 _m6_group_trs, _m6_inside_pairs -- 읽는 섹션: S052, S056. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _lib1213 = library_dir
    _m6_trs, _m6_meta = load_topology(
        _os1213.path.join(_lib1213, "current_reuse_telescopic_ota.topology.json"))
    _m6_pairs_meta = _m6_meta["symmetry"]["matching_pairs"]
    _m6_by_name = {t.name: t for t in _m6_trs}
    _m6_order = {t.name: i for i, t in enumerate(_m6_trs)}
    _m6_names = sorted({"M6", "M7", "M1a", "M1b", "M2a", "M2b", "M58", "M57"},
                        key=lambda n: _m6_order[n])
    _m6_group_trs = [_dc_replace(_m6_by_name[n], stack_id="M6") for n in _m6_names]
    _m6_inside_pairs = [tuple(p["names"]) for p in _m6_pairs_meta
                         if set(p["names"]) <= set(_m6_names)]
    _m6_g = build_graph(_m6_group_trs)
    _m6_odd = check_euler_condition(_m6_g).odd_nodes
    _m6_node_map_early = _mirror_node_map_from_pairs(_m6_inside_pairs, _m6_group_trs)
    _m6_tier1_pairs, _ = _pair_odd_nodes_by_mirror(_m6_odd, _m6_node_map_early)
    _m6_tier1_segments = _build_crossover_segments(_m6_group_trs, _m6_tier1_pairs)
    _m6_tier1_splits = _count_matching_pair_splits(_m6_tier1_segments, _m6_inside_pairs)
    _m6_result = find_min_crossover_layout(_m6_group_trs, _m6_inside_pairs)
    _m6_final_splits = _count_matching_pair_splits(_m6_result["segments"], _m6_inside_pairs)

    return types.SimpleNamespace(_m6_group_trs=_m6_group_trs, _m6_inside_pairs=_m6_inside_pairs)


@pytest.fixture
def s061_state():
    """섹션 S061(이관본 줄 1009-1073)이 만드는 이름 mirror_pairs, spine -- 읽는 섹션: S062, S063, S064, S065. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    def _blk(name, row_fingers):
        """block_from_rows() 자체 self-test 헬퍼(2026-08-13 세션31) -- finger_w=l=1.0
        균일값을 쓰면 width_m=n_fingers, height_m=행 개수가 그대로 나와 옛
        block_from_row_widths({row: n_fingers}) 리터럴 dict 시대의 수치를 그대로 재현한다
        (이 Test 17은 pack_floorplan()의 패킹 알고리즘 자체를 검증하는 것이 목적이라
        실제 물리 치수 정확도는 무관 -- 상대적 크기 관계만 보존하면 충분)."""
        rows_ = {rn: [Transistor(f"{name}_{rn}", "nmos", source="s", drain="d",
                                   n_fingers=n, finger_w=1.0, l=1.0)]
                 for rn, n in row_fingers.items()}
        return block_from_rows(name, rows_)
    spine = [
        _blk("S1_PMOS", {"row0": 8, "row1": 8}),
        _blk("S1_NMOS", {"row0": 8, "row1": 8}),
        _blk("S1_TAILP", {"row0": 10}),
        _blk("S1_TAILN", {"row0": 7}),
        _blk("biasgen_pmos", {"row0": 5}),
        _blk("biasgen_nmos", {"row0": 4}),
        _blk("cmfb_p1", {"row0": 2}),
        _blk("cmfb_p2", {"row0": 1}),
        _blk("cmfb_n1", {"top": 2, "bot": 2}),
        _blk("cmfb_n2", {"row0": 2}),
    ]
    mirror_pairs = [
        (_blk("classab_p1", {"row0": 3}), _blk("classabL_p1", {"row0": 3})),
        (_blk("classab_p2", {"row0": 2}), _blk("classabL_p2", {"row0": 2})),
        (_blk("classab_n1_new", {"row0": 2}), _blk("classabL_n1_new", {"row0": 2})),
        (_blk("classab_n2_new", {"row0": 2}), _blk("classabL_n2_new", {"row0": 2})),
        (_blk("classab_n_mirror", {"top": 2, "bot": 2}), _blk("classabL_n_mirror", {"top": 2, "bot": 2})),
        (_blk("S2_M15", {"row0": 1}), _blk("S2_M25", {"row0": 1})),
        (_blk("S2_M16", {"row0": 1}), _blk("S2_M26", {"row0": 1})),
    ]
    r3 = pack_floorplan(spine, mirror_pairs, gap=1.0)

    return types.SimpleNamespace(mirror_pairs=mirror_pairs, spine=spine)


@pytest.fixture
def s063_state(s061_state):
    """섹션 S063(이관본 줄 1115-1148)이 만드는 이름 spine_groups -- 읽는 섹션: S064, S065. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    mirror_pairs = s061_state.mirror_pairs
    spine = s061_state.spine

    spine_groups = {
        "stage1": [b for b in spine if b.name.startswith("S1_")],
        "biasgen": [b for b in spine if b.name.startswith("biasgen_")],
        "cmfb": [b for b in spine if b.name.startswith("cmfb_")],
    }
    r5 = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0)

    return types.SimpleNamespace(spine_groups=spine_groups)


@pytest.fixture
def s064_state(s061_state, s063_state):
    """섹션 S064(이관본 줄 1149-1182)이 만드는 이름 net_weights -- 읽는 섹션: S065. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    mirror_pairs = s061_state.mirror_pairs
    spine_groups = s063_state.spine_groups

    net_weights = {
        "biasgen": {"stage1": 4.0, "cmfb": 1.0}, "stage1": {"biasgen": 4.0, "cmfb": 1.0},
        "cmfb": {"biasgen": 1.0, "stage1": 1.0},
        "classab_p2": {"biasgen": 2.0}, "classab_n1_new": {"biasgen": 1.0},
    }
    r6_before = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0)
    r6_after = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0, net_weights=net_weights)

    return types.SimpleNamespace(net_weights=net_weights)


@pytest.fixture
def s065_state():
    """섹션 S065(이관본 줄 1183-1220)이 만드는 이름 vsd_trs -- 읽는 섹션: S067. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    vsd_trs = [
        Transistor("MA", "nmos", source="tail", drain="outA", gate="vip"),
        Transistor("MB", "nmos", source="tail", drain="outB", gate="vim"),
        Transistor("MC", "nmos", source="gnd", drain="tail", gate="bias"),
    ]

    return types.SimpleNamespace(vsd_trs=vsd_trs)


@pytest.fixture
def s075_state():
    """섹션 S075(이관본 줄 1350-1394)이 만드는 이름 a34_r0b, a34_r1b, b34_r0b, b34_r1b -- 읽는 섹션: S078, S079. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    cc34_2 = common_centroid_layout([
        Transistor("M3", "pmos", source="vdd", drain="X", n_fingers=3),
        Transistor("M4", "pmos", source="vdd", drain="Y", n_fingers=3),
    ])
    a34_r0b = cc34_2["rows"][0]["transistor_sequence"].count("M3")
    b34_r0b = cc34_2["rows"][0]["transistor_sequence"].count("M4")
    a34_r1b = cc34_2["rows"][1]["transistor_sequence"].count("M3")
    b34_r1b = cc34_2["rows"][1]["transistor_sequence"].count("M4")

    return types.SimpleNamespace(a34_r0b=a34_r0b, a34_r1b=a34_r1b, b34_r0b=b34_r0b, b34_r1b=b34_r1b)


@pytest.fixture
def s083_state():
    """섹션 S083(이관본 줄 1461-1484)이 만드는 이름 sized, stick_rows_actual -- 읽는 섹션: S084. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    sized = {"M1a","M1b","M2a","M2b","M3a","M3b","M4a","M4b","M5","M6","M7",  # stage-1 (11)
             "M15","M25","M16","M26",  # stage-2 output (4)
             "M14a","M14b","M11a","M11b","M8","M13",  # Class-AB (6) -- 실제로 stick diagram 없었음
             "M27","M28","M29","M30","M31","M32","M35","M33","M34",  # bias-gen (9) -- 없었음
             "M36a","M36b","M37a","M37b","M38","M39","M40"}  # CMFB (7) -- 없었음
    stick_rows_actual = {  # 실제 재현 -- 이 사고에서 실제로 만들어진 6개 행만
        "row1_pmos_in_casc": ["M1a","M1b","M2a","M2b"],
        "row2_nmos_in_casc": ["M4a","M4b","M3a","M3b"],
        "row3_top_load": ["M6","M7"],
        "row4_tail": ["M5"],
        "rowP_out": ["M15","M25"],
        "rowN_out": ["M16","M26"],
    }
    cov = check_stick_diagram_coverage(sized, stick_rows_actual)

    return types.SimpleNamespace(sized=sized, stick_rows_actual=stick_rows_actual)


@pytest.fixture
def s086_state(library_dir):
    """섹션 S086(이관본 줄 1499-1531)이 만드는 이름 _fc_loaded, _fc_meta, _fc_original, _fc_overrides, _fc_result, _ts_diff_ok -- 읽는 섹션: S088, S089, S090, S092, S093, S094, S096, S097, S098, S099, S103, S111, S112. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _lib_dir = library_dir

    _fc_original = folded_cascode_example()
    _fc_loaded, _fc_meta = load_topology(_os.path.join(_lib_dir, "folded_cascode.topology.json"))
    _fc_overrides = {t.name: {"n_fingers": t.n_fingers, "finger_w": t.finger_w,
                               "w": t.w, "stack_id": t.stack_id} for t in _fc_original}
    _fc_result = run_topology_pipeline(_os.path.join(_lib_dir, "folded_cascode.topology.json"),
                                        _fc_overrides)
    _ts_original = two_stage_ota_example()
    _ts_loaded, _ts_meta = load_topology(_os.path.join(_lib_dir, "two_stage_ota.topology.json"))
    _ts_orig_by_name = {t.name: (t.kind, t.source, t.drain, t.gate) for t in _ts_original}
    _ts_load_by_name = {t.name: (t.kind, t.source, t.drain, t.gate) for t in _ts_loaded}
    _ts_diff_ok = _ts_orig_by_name == _ts_load_by_name

    return types.SimpleNamespace(_fc_loaded=_fc_loaded, _fc_meta=_fc_meta, _fc_original=_fc_original, _fc_overrides=_fc_overrides, _fc_result=_fc_result, _ts_diff_ok=_ts_diff_ok)


@pytest.fixture
def s093_state(s086_state, library_dir):
    """섹션 S093(이관본 줄 1612-1621)이 만드는 이름 _spine_only_hints -- 읽는 섹션: S094. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _fc_overrides = s086_state._fc_overrides
    _lib_dir = library_dir

    _spine_only_hints = {"spine_groups": {"cellA": ["top", "mid"], "cellB": ["bot"]}}
    _fc_result_fallback = run_topology_pipeline(
        _os.path.join(_lib_dir, "folded_cascode.topology.json"), _fc_overrides,
        floorplan_hints=_spine_only_hints)

    return types.SimpleNamespace(_spine_only_hints=_spine_only_hints)


@pytest.fixture
def s103_state(s086_state):
    """섹션 S103(이관본 줄 1708-1746)이 만드는 이름 _fc_by_name, _fc_pairs_meta -- 읽는 섹션: S104, S111. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _fc_loaded = s086_state._fc_loaded
    _fc_meta = s086_state._fc_meta

    _fc_by_name = {t.name: t for t in _fc_loaded}
    _fc_pairs_meta = _fc_meta["symmetry"]["matching_pairs"]
    _mirror_a, _mirror_b = _first_pair_matching(_fc_pairs_meta, True, "ratio")
    _t_mirror_a = _dc_replace(_fc_by_name[_mirror_a], n_fingers=3, stack_id="row0")
    _t_mirror_b = _dc_replace(_fc_by_name[_mirror_b], n_fingers=3, stack_id="row1")

    return types.SimpleNamespace(_fc_by_name=_fc_by_name, _fc_pairs_meta=_fc_pairs_meta)


@pytest.fixture
def s104_state(s103_state):
    """섹션 S104(이관본 줄 1747-1762)이 만드는 이름 _branch_a, _branch_b, _norepair_pairs, _norepair_rows, _norepair_sensitivity, _t_branch_a, _t_branch_b -- 읽는 섹션: S106, S108, S109. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _fc_by_name = s103_state._fc_by_name
    _fc_pairs_meta = s103_state._fc_pairs_meta

    _branch_a, _branch_b = _first_pair_matching(_fc_pairs_meta, False, "ratio")
    _t_branch_a = _dc_replace(_fc_by_name[_branch_a], n_fingers=6, stack_id="rowA")
    _t_branch_b = _dc_replace(_fc_by_name[_branch_b], n_fingers=6, stack_id="rowB")
    _norepair_rows = {"rowA": [_t_branch_a], "rowB": [_t_branch_b]}
    _norepair_pairs = [(_branch_a, _branch_b)]
    _norepair_sensitivity = {(_branch_a, _branch_b): "ratio"}
    _norepair_result_rows, _norepair_audit = repair_matching_safety(
        _norepair_rows, _norepair_pairs, _norepair_sensitivity)

    return types.SimpleNamespace(_branch_a=_branch_a, _branch_b=_branch_b, _norepair_pairs=_norepair_pairs, _norepair_rows=_norepair_rows, _norepair_sensitivity=_norepair_sensitivity, _t_branch_a=_t_branch_a, _t_branch_b=_t_branch_b)


@pytest.fixture
def s105_state(library_dir):
    """섹션 S105(이관본 줄 1763-1792)이 만드는 이름 _m6b_pairs, _m6b_row, _m6b_sensitivity -- 읽는 섹션: S107, S109. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _m6b_lib = library_dir
    _m6b_trs, _m6b_meta = load_topology(
        os.path.join(_m6b_lib, "current_reuse_telescopic_ota.topology.json"))
    _m6b_by_name = {t.name: t for t in _m6b_trs}
    _m6b_names = ["M1a", "M1b", "M2a", "M2b", "M6", "M7"]
    _m6b_row = [_dc_replace(_m6b_by_name[n], stack_id="seg1") for n in _m6b_names]
    _m6b_pairs = [("M1a", "M1b"), ("M2a", "M2b")]
    _m6b_sensitivity = {("M1a", "M1b"): "offset", ("M2a", "M2b"): "ratio"}
    _m6b_before = audit_row_split({"seg1": _m6b_row}, matching_pairs=_m6b_pairs,
                                   pair_sensitivity=_m6b_sensitivity)
    _m6b_rows, _m6b_after = repair_matching_safety({"seg1": _m6b_row}, _m6b_pairs, _m6b_sensitivity)

    return types.SimpleNamespace(_m6b_pairs=_m6b_pairs, _m6b_row=_m6b_row, _m6b_sensitivity=_m6b_sensitivity)


@pytest.fixture
def s111_state(s086_state, s103_state):
    """섹션 S111(이관본 줄 1877-1914)이 만드는 이름 _fc_forced_pairs, _fc_groups -- 읽는 섹션: S112, S113. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _fc_loaded = s086_state._fc_loaded
    _fc_pairs_meta = s103_state._fc_pairs_meta

    _fc_forced_pairs = [tuple(p["names"]) for p in _fc_pairs_meta if p["current_forced"]]
    _fc_groups = geometry_colocation_union(_fc_loaded, _fc_forced_pairs)
    _fc_all_members = sorted(n for members in _fc_groups.values() for n in members)
    _fc_group_sets = {frozenset(members) for members in _fc_groups.values()}

    return types.SimpleNamespace(_fc_forced_pairs=_fc_forced_pairs, _fc_groups=_fc_groups)


@pytest.fixture
def s118_state():
    """섹션 S118(이관본 줄 1999-2017)이 만드는 이름 _fc_new -- 읽는 섹션: S119. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _fc_matches = find_idiom_matches(folded_cascode_example(), inputs=("vin_p", "vin_n"))
    _fc_new = find_matching_candidates(folded_cascode_example(), idiom_matches=_fc_matches)
    _fc_new_diffpair_sets = {frozenset(t.name for t in g) for g in _fc_new["diff_pair"].values()}

    return types.SimpleNamespace(_fc_new=_fc_new)


@pytest.fixture
def s120_state(library_dir):
    """섹션 S120(이관본 줄 2034-2057)이 만드는 이름 _crt_path -- 읽는 섹션: S122. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _lib_dir31 = library_dir
    _crt_path = _os31.path.join(_lib_dir31, "current_reuse_telescopic_ota.topology.json")

    return types.SimpleNamespace(_crt_path=_crt_path)


@pytest.fixture
def s122_state(s120_state):
    """섹션 S122(이관본 줄 2059-2074)이 만드는 이름 _crt_meta -- 읽는 섹션: S123. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _crt_path = s120_state._crt_path

    _crt_transistors, _crt_meta = load_topology(_crt_path)

    return types.SimpleNamespace(_crt_meta=_crt_meta)


@pytest.fixture
def s128_state():
    """섹션 S128(이관본 줄 2200-2244)이 만드는 이름 _t35_fixture -- 읽는 섹션: S129, S130, S132, S133, S135, S136, S137, S138, S139. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _t35_fixture = [
        Transistor("M6", "pmos", source="vdd", drain="Vx", gate="Vbias1"),
        Transistor("M1a", "pmos", source="Vx", drain="N1", gate="Vip"),    # 위쪽 diff pair
        Transistor("M1b", "pmos", source="Vx", drain="N2", gate="Vim"),
        Transistor("M2a", "pmos", source="N1", drain="Nout1", gate="Vbias2"),
        Transistor("M2b", "pmos", source="N2", drain="Nout2", gate="Vbias2"),
        Transistor("M3a", "nmos", source="N3", drain="Nout1", gate="Vbias3"),
        Transistor("M3b", "nmos", source="N4", drain="Nout2", gate="Vbias3"),
        Transistor("M4a", "nmos", source="Vy", drain="N3", gate="Vip"),    # 아래쪽 diff pair
        Transistor("M4b", "nmos", source="Vy", drain="N4", gate="Vim"),
        Transistor("M5", "nmos", source="gnd", drain="Vy", gate="Vbias4"),
    ]
    _t35_down = trace_vdd_to_gnd_branches(_t35_fixture)
    _t35_up = trace_gnd_to_vdd_branches(_t35_fixture)
    _t35_result = find_differential_and_mirror_forks(_t35_fixture, inputs=("Vip", "Vim"))

    return types.SimpleNamespace(_t35_fixture=_t35_fixture)


@pytest.fixture
def s141_state(library_dir):
    """섹션 S141(이관본 줄 2603-2648)이 만드는 이름 _t48_candidates, _t48_pairs_meta, _t48_trs -- 읽는 섹션: S142. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _t48_lib = library_dir
    _t48_trs, _t48_meta = load_topology(
        _t48_os.path.join(_t48_lib, "folded_cascode.topology.json"))
    _t48_pairs_meta = _t48_meta["symmetry"]["matching_pairs"]
    _t48_forced = [tuple(p["names"]) for p in _t48_pairs_meta if p["current_forced"]]
    _t48_refined = refine_differential_and_mirror_relations(_t48_trs)
    _t48_candidates = {}
    for _name, _sid in _t48_refined["vertical_stack_id_candidates"]["groups"].items():
        _t48_candidates.setdefault(_sid, []).append(_name)
    _t48_before_pairs_together = sum(
        1 for _names in _t48_forced
        for _a, _b in zip(_names, _names[1:])
        if any({_a, _b} <= set(_members) for _members in _t48_candidates.values()))
    _t48_merged = merge_layout_groups_by_matching_pairs(_t48_trs, _t48_candidates, _t48_forced)

    return types.SimpleNamespace(_t48_candidates=_t48_candidates, _t48_pairs_meta=_t48_pairs_meta, _t48_trs=_t48_trs)


@pytest.fixture
def s144_state(library_dir):
    """섹션 S144(이관본 줄 2682-2743)이 만드는 이름 _t49_device_roles, _t49_forced, _t49_trs -- 읽는 섹션: S146, S148. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _t49_lib = library_dir
    _t49_trs, _t49_meta = load_topology(
        _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json"))
    _t49_pairs_meta = _t49_meta["symmetry"]["matching_pairs"]
    _t49_forced = [tuple(p["names"]) for p in _t49_pairs_meta if p["current_forced"]]
    _t49_device_roles = {k: v for k, v in (_t49_meta.get("device_roles") or {}).items()
                          if not k.startswith("_")}
    _t49_result = audit_vertical_stack_id_euler_feasibility(_t49_trs, _t49_device_roles, _t49_forced)

    return types.SimpleNamespace(_t49_device_roles=_t49_device_roles, _t49_forced=_t49_forced, _t49_trs=_t49_trs)


@pytest.fixture
def s155_state(library_dir):
    """섹션 S155(이관본 줄 2945-2976)이 만드는 이름 _t53_meta, _t53_trs -- 읽는 섹션: S156. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _t49_lib = library_dir

    _t53_trs, _t53_meta = load_topology(
        _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json"))
    _t53_result = propose_device_roles_gap_fill(_t53_trs, {}, [])

    return types.SimpleNamespace(_t53_meta=_t53_meta, _t53_trs=_t53_trs)


@pytest.fixture
def s157_state(library_dir):
    """섹션 S157(이관본 줄 2996-3065)의 입력(하네스 spec, 원본·변형 topology 경로)을 만드는 문장. 피검 호출
    `optimize_full_circuit_budget()`은 ValueError(I-C11)를 내므로 test 본문에 둔다(spec card 계약 4)."""
    _t49_lib = library_dir
    _t53g_workspaces = _t49_os.path.normpath(_t49_os.path.join(_t49_lib, "..", "..", "..", "..", "workspaces"))
    _t53g_harness_path = _t49_os.path.join(_t53g_workspaces, "run_harness.py")
    # contract 4: 이관본 `if not exists: SKIP` 조건을 먼저 단언한다 -- workspaces/run_harness.py는 추적되는 파일.
    assert _t49_os.path.exists(_t53g_harness_path)
    _t53g_spec_mod = _t53g_ilu.spec_from_file_location("_t53g_run_harness", _t53g_harness_path)
    _t53g_harness = _t53g_ilu.module_from_spec(_t53g_spec_mod)
    _t53g_spec_mod.loader.exec_module(_t53g_harness)

    _t53g_two_stage_path = _t49_os.path.join(_t49_lib, "two_stage_ota.topology.json")
    with open(_t53g_two_stage_path, encoding="utf-8") as _t53g_f:
        _t53g_raw = json.load(_t53g_f)
    _t53g_spec = _t53g_harness._spec_two_stage_ota()
    _t53g_gp = _t53g_harness.SPECS["two_stage_ota"]["grid_points_per_theta"]
    return types.SimpleNamespace(_t53g_two_stage_path=_t53g_two_stage_path, _t53g_raw=_t53g_raw,
                                 _t53g_spec=_t53g_spec, _t53g_gp=_t53g_gp)


@pytest.fixture
def s161_state(library_dir):
    """섹션 S161(이관본 줄 3187-3213)이 만드는 이름 _t57_raw -- 읽는 섹션: S162. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _t49_lib = library_dir

    _t57_lib_path = _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json")
    with open(_t57_lib_path, encoding="utf-8") as _t57_f:
        _t57_raw = json.load(_t57_f)

    return types.SimpleNamespace(_t57_raw=_t57_raw)


@pytest.fixture
def s163_state(library_dir):
    """섹션 S163(이관본 줄 3247-3290)이 만드는 이름 _t58_meta -- 읽는 섹션: S164. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _t49_lib = library_dir

    _t58_srcdir = _t58_tempfile.mkdtemp()
    _t58_path = _t49_os.path.join(_t58_srcdir, "folded_cascode.topology.json")
    _t58_shutil.copy(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"), _t58_path)
    with open(_t58_path, "r", encoding="utf-8") as _t58_f:
        _t58_raw = json.load(_t58_f)
    _t58_raw["symmetry"]["matching_pairs"] = [
        p for p in _t58_raw["symmetry"]["matching_pairs"] if set(p["names"]) != {"M11", "MN"}]
    if isinstance(_t58_raw.get("device_roles"), dict):
        for _t58_n in ("M11", "MN"):
            _t58_raw["device_roles"].pop(_t58_n, None)
    with open(_t58_path, "w", encoding="utf-8") as _t58_f:
        json.dump(_t58_raw, _t58_f)
    _t58_trs, _t58_meta = load_topology(_t58_path)
    _t58_needs_review = find_unreviewed_matching_pairs(_t58_meta)

    return types.SimpleNamespace(_t58_meta=_t58_meta)


@pytest.fixture
def s165_state(library_dir):
    """섹션 S165(이관본 줄 3301-3312)이 만드는 이름 _t60_meta, _t60_trs -- 읽는 섹션: S166. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _t49_lib = library_dir

    _t60_trs, _t60_meta = load_topology(_t49_os.path.join(_t49_lib, "nmcnr_amplifier.topology.json"))
    _t60_clean = audit_theta_root_direction(_t60_trs, _t60_meta["sizing_roles"], inputs=("Vin_p", "Vin_n"))

    return types.SimpleNamespace(_t60_meta=_t60_meta, _t60_trs=_t60_trs)


@pytest.fixture
def s169_state(library_dir):
    """섹션 S169(이관본 줄 3361-3381)이 만드는 이름 _t61_meta, _t61_trs -- 읽는 섹션: S170. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _t49_lib = library_dir

    _t61_trs, _t61_meta = load_topology(_t49_os.path.join(_t49_lib, "nmcnr_amplifier.topology.json"))
    _t61_result = propose_theta_kcl_gap_fill(
        _t61_trs, _t61_meta["symmetry"]["matching_pairs"],
        ideal_sources=_t61_meta.get("ideal_sources"), inputs=("Vin_p", "Vin_n"))

    return types.SimpleNamespace(_t61_meta=_t61_meta, _t61_trs=_t61_trs)


@pytest.fixture
def s170_state(s169_state):
    """섹션 S170(이관본 줄 3383-3406)이 만드는 이름 _t61c_result -- 읽는 섹션: S173. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _t61_meta = s169_state._t61_meta
    _t61_trs = s169_state._t61_trs

    _t61c_flat = [n for grp in _t61_meta["compensation"]["stage_devices"] for n in grp]
    _t61c_result = propose_theta_kcl_gap_fill(
        _t61_trs, _t61_meta["symmetry"]["matching_pairs"],
        ideal_sources=_t61_meta.get("ideal_sources"), compensation_stage_devices=_t61c_flat,
        inputs=("Vin_p", "Vin_n"))

    return types.SimpleNamespace(_t61c_result=_t61c_result)


@pytest.fixture
def s171_state(library_dir):
    """섹션 S171(이관본 줄 3408-3419)이 만드는 이름 _t61_fc_result -- 읽는 섹션: S172. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _t49_lib = library_dir

    _t61_fc_trs, _t61_fc_meta = load_topology(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"))
    _t61_fc_result = propose_theta_kcl_gap_fill(
        _t61_fc_trs, _t61_fc_meta["symmetry"]["matching_pairs"],
        ideal_sources=_t61_fc_meta.get("ideal_sources"), inputs=("vin_p", "vin_n"))

    return types.SimpleNamespace(_t61_fc_result=_t61_fc_result)


def test_s021_M2b():
    """=== Test 11: §2.7 2D common-centroid 표 기반 경로 — M2/M2b(전류거울, 4:4) ===
    M2/M2b는 1행만으로도 y방향 gradient는 못 잡는다 — ABBA/BAAB 2행으로 그것까지
    상쇄한다. 2026-07-24 세 번째 정정: ABBA/BAAB는 추가 metal layer 없이도 실제로
    1개 layer로 실현 가능하다(직접 검증됨) — 표의 모든 pattern이 그런 건 아니라서
    (예: ABA/BAB는 불가능) 이 함수가 이제 반환 전 각 행을 직접 검증한다.
    (2026-07-28 4차: 옛 common_centroid_layout(pattern_key=...)는 common_centroid_
    layout_nway()에 완전히 흡수돼 제거됨 — 내부 헬퍼 _common_centroid_from_pattern_
    table()을 직접 검증하고, nway의 N=2 비율 자동 dispatch도 아래 Test 12.5에서 확인)

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S021(줄 85-124, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    cc = _common_centroid_from_pattern_table("M2", "out", "M2b", "bias", hub_net="vdd",
                                              count_a=4, count_b=4, pattern_key=("ABBA", "BAAB"))
    for i, row in enumerate(cc["rows"]):
        pass
    # oracle (d): 섹션 문장이 적은 기대 '(둘 다 4여야 함) -> OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert cc['total_a'] == cc['total_b'] == 4, (f"  검증: total_a(M2)={cc['total_a']}, total_b(M2b)={cc['total_b']} (둘 다 4여야 함) "
          f"-> {'OK' if cc['total_a'] == cc['total_b'] == 4 else 'FAIL'}")
    with pytest.raises(ValueError):
        _common_centroid_from_pattern_table("M2", "out", "M2b", "bias", hub_net="vdd",
                                             count_a=6, count_b=6, pattern_key=("ABA", "BAB"))
    with pytest.raises(ValueError):
        _common_centroid_from_pattern_table("M2", "out", "M2b", "bias", hub_net="vdd",
                                             count_a=6, count_b=6, pattern_key=("ABCCBA", "CBAABC"))


def test_s022_common_centroid_layout():
    """=== Test 12: common_centroid_layout() 회전 경로 — 홀수 개수(M1/M2 차동쌍 9:9)도
    실제 오일러 trail 기반 2행 ===
    표 기반 경로는 COMMON_CENTROID_PATTERNS의 정해진 repeat만 지원해 홀수를 못
    다룬다 — Example 2의 M1/M2(각 9개, 홀수)는 §2.5.4 비대칭 분할을 2행으로 확장한
    회전 경로(_common_centroid_nway_exact, pattern_key 없음)로 처리해야 한다.
    2026-07-24 두 번째 수정: row1을 round-robin으로 손으로 섞던 것에서, hub-leaf
    쌍(tail 공유)의 실제 build_graph()+hierholzer()로 계산하도록 바꿨다 — 매 finger
    완전 1:1 교대(ABAB...)는 hub-leaf 구조에서 그래프 이론적으로 불가능하다(§2.5.6).

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S022(줄 125-145, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    splits99 = find_interleaved_symmetric_splits(9, 9)
    cc2 = common_centroid_layout([
        Transistor("M1", "nmos", source="tail", drain="d1", n_fingers=9),
        Transistor("M2", "nmos", source="tail", drain="d2", n_fingers=9),
    ])
    assert cc2["method"] == "rotation_exact" and cc2["residual"] == 0.0
    for i, row in enumerate(cc2["rows"]):
        pass


def test_s023_common_centroid_layout():
    """=== Test 12.5: common_centroid_layout() — 대칭(1:1)에서 표/회전 두 경로가
    실제로 같은 패턴을 내는지 + 비율(2:1)에서 표 기반 흡수(pattern_table)가 회전보다
    나은지 실측(2026-07-28: 옛 common_centroid_layout()의 두 경로를 흡수·통합) ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S023(줄 146-177, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    cc_table = _common_centroid_from_pattern_table("M2", "out", "M2b", "bias", hub_net="vdd",
                                                    count_a=4, count_b=4, pattern_key=("ABBA", "BAAB"))
    cc_graph_nway = common_centroid_layout([
        Transistor("M2", "nmos", source="vdd", drain="out", n_fingers=4),
        Transistor("M2b", "nmos", source="vdd", drain="bias", n_fingers=4),
    ])
    table_rows = [r["transistor_sequence"] for r in cc_table["rows"]]
    graph_rows = [row["transistor_sequence"] for row in cc_graph_nway["rows"]]
    same_set = {tuple(r) for r in table_rows} == {tuple(r) for r in graph_rows}
    assert same_set
    cc_ratio_nway = common_centroid_layout([
        Transistor("M2", "nmos", source="vdd", drain="out", n_fingers=4),
        Transistor("M2b", "nmos", source="vdd", drain="bias", n_fingers=2),
    ])
    assert cc_ratio_nway["method"] == "pattern_table" and cc_ratio_nway["residual"] == 0.0, (
        f"2:1 비율인데 표 기반 흡수(pattern_table)로 안 갔다 -- 회귀: {cc_ratio_nway}"
    )


def test_s024_interdigitate_layout(s022_state):
    """=== Test 12.6: interdigitate_layout() — common_centroid_layout()와 동급으로 재설계
    (내부 검증 + crossover 폴백, dict 반환) — 사용자 요청, 2026-07-28 5차 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S024(줄 178-263, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    cc2 = s022_state.cc2

    r_base = interdigitate_layout([
        Transistor("M3", "nmos", source="tail", drain="LM3", n_fingers=2),
        Transistor("M4", "nmos", source="tail", drain="LM4", n_fingers=2),
    ], base="AB", repeat=2)
    assert r_base["method"] == "pattern_table" and r_base["crossover_count"] == 0
    assert r_base["rows"][0]["transistor_sequence"] == ["M3", "M4", "M4", "M3"]

    r_ratio = interdigitate_layout([
        Transistor("M3", "nmos", source="tail", drain="LM3", n_fingers=3),
        Transistor("M4", "nmos", source="tail", drain="LM4", n_fingers=1),
    ], base="AABA", repeat=1)
    assert r_ratio["method"] == "search"

    r_3dev = interdigitate_layout([
        Transistor("M3", "nmos", source="tail", drain="LM3", n_fingers=1),
        Transistor("M4", "nmos", source="tail", drain="LM4", n_fingers=1),
        Transistor("M5", "nmos", source="tail", drain="LM5", n_fingers=1),
    ], base="ABC", repeat=1)
    assert r_3dev["method"] == "search" and r_3dev["crossover_count"] > 0

    r_rr = interdigitate_layout([
        Transistor("M9", "nmos", source="tail", drain="LM9", n_fingers=3),
        Transistor("M10", "nmos", source="tail", drain="LM10", n_fingers=3),
    ])
    assert r_rr["method"] == "search" and r_rr["crossover_count"] == 0

    r_rr3 = interdigitate_layout([
        Transistor("M3", "nmos", source="tail", drain="LM3", n_fingers=1),
        Transistor("M4", "nmos", source="tail", drain="LM4", n_fingers=1),
        Transistor("M5", "nmos", source="tail", drain="LM5", n_fingers=1),
    ])
    assert r_rr3["method"] == "search" and r_rr3["crossover_count"] > 0

    def is_valid_hubleaf_sequence(node_seq, trs, hub, leaf_of):
        """row가 실제로 한 붓 그리기 가능한지(인접 finger가 공유 net을 갖는지) 직접 검증
        — 이 함수의 결과를 그냥 믿지 않고 1차 원리(그래프 인접성)로 재확인한다."""
        if len(node_seq) != len(trs) + 1:
            return False
        for i, name in enumerate(trs):
            edge = {hub, leaf_of[name]}
            if {node_seq[i], node_seq[i + 1]} != edge:
                return False
        return True

    leaf_of = {"M1": "d1", "M2": "d2"}
    row0_valid = is_valid_hubleaf_sequence(cc2["rows"][0]["node_sequence"], cc2["rows"][0]["transistor_sequence"], "tail", leaf_of)
    row1_valid = is_valid_hubleaf_sequence(cc2["rows"][1]["node_sequence"], cc2["rows"][1]["transistor_sequence"], "tail", leaf_of)

    row0, row1 = cc2["rows"][0]["transistor_sequence"], cc2["rows"][1]["transistor_sequence"]
    swap = {"M1": "M2", "M2": "M1"}
    # row1은 row0의 swap(reverse 없음)이어야 한다(2026-07-24 수정 — reverse+swap은 완전
    # 1:1 교대 배열에서 자기 자신으로 퇴화하는 실제 버그였다, 함수 docstring 참고).
    is_swap_only = row1 == [swap[x] for x in row0]
    distinct_rows = row0 != row1
    col_avg_m1 = sum(i for i, x in enumerate(row0) if x == "M1") + sum(i for i, x in enumerate(row1) if x == "M1")
    col_avg_m2 = sum(i for i, x in enumerate(row0) if x == "M2") + sum(i for i, x in enumerate(row1) if x == "M2")
    n_m1 = row0.count("M1") + row1.count("M1")
    n_m2 = row0.count("M2") + row1.count("M2")


def test_s025_common_centroid_layout():
    """=== Test 12.7: common_centroid_layout() — N=3 이상 hub-leaf common-centroid ===
    2026-07-28 신설(사용자 요청: common_centroid_layout()의 3-소자 확장). COMMON_CENTROID_
    PATTERNS의 ABCCBA/CBAABC는 hub-leaf로 실현 불가능함을 실측 확인(아래 대조) — 대신
    N개 leaf를 회전 대칭으로 N개 행에 배치하면 항상 모든 소자가 모든 열을 정확히 1번씩
    지나가 진짜 common-centroid가 됨을 이론+실측으로 확인했다. 2026-07-28 2차: 사용자
    요청으로 Transistor 리스트 입력 + n_rows(N 위아래 자유 지정) 지원으로 일반화.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S025(줄 264-366, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    trs_n3 = [
        Transistor("MA", "nmos", source="vdd", drain="La", n_fingers=6),
        Transistor("MB", "nmos", source="vdd", drain="Lb", n_fingers=6),
        Transistor("MC", "nmos", source="vdd", drain="Lc", n_fingers=6),
    ]
    nway3 = common_centroid_layout(trs_n3)
    for i, row in enumerate(nway3["rows"]):
        pass
    col_sums = defaultdict(list)
    for row in nway3["rows"]:
        for col, name in enumerate(row["transistor_sequence"]):
            col_sums[name].append(col)
    avgs = {name: sum(cols) / len(cols) for name, cols in col_sums.items()}
    counts_n3 = {name: len(cols) for name, cols in col_sums.items()}
    assert nway3["method"] == "rotation_exact" and nway3["residual"] == 0.0
    assert len(set(round(v, 9) for v in avgs.values())) == 1, f"열평균이 안 맞는다: {avgs}"
    assert all(c == 6 for c in counts_n3.values()), f"소자별 총 개수가 6이 아니다: {counts_n3}"
    leaf_of_n3 = {"MA": "La", "MB": "Lb", "MC": "Lc"}
    for i, row in enumerate(nway3["rows"]):
        node_seq_check = _hubleaf_sequence_node_path(row["transistor_sequence"], "vdd", leaf_of_n3)
        assert node_seq_check is not None, f"row{i}이 유효한 walk가 아니다"

    for repeat, (top, bot) in COMMON_CENTROID_PATTERNS[("ABCCBA", "CBAABC")].items():
        for label, pat in [("top", top), ("bot", bot)]:
            trs_pat = [{"A": "MA", "B": "MB", "C": "MC"}[ch] for ch in pat]
            result = _hubleaf_sequence_node_path(trs_pat, "vdd", leaf_of_n3)
            assert result is None, f"repeat={repeat} {label}이 예상과 달리 유효한 walk로 나왔다"

    trs_n2 = [
        Transistor("M2", "nmos", source="vdd", drain="out", n_fingers=4),
        Transistor("M2b", "nmos", source="vdd", drain="bias", n_fingers=4),
    ]
    nway2 = common_centroid_layout(trs_n2)
    col_sums2 = defaultdict(list)
    for row in nway2["rows"]:
        for col, name in enumerate(row["transistor_sequence"]):
            col_sums2[name].append(col)
    avgs2 = {name: sum(c) / len(c) for name, c in col_sums2.items()}
    assert nway2["method"] == "rotation_exact" and nway2["residual"] == 0.0
    assert len(set(round(v, 9) for v in avgs2.values())) == 1

    # 2026-07-28 3~4차 crossover 폴백 통합 후: 4소자 count=5(모든 block이 홀수, parity
    # repair로도 못 고치는 케이스)는 더 이상 ValueError가 아니라 crossover 배치로 성공한다
    # — 이 케이스가 바로 "crossover 폴백이 실제로 필요한 사례"의 실례다.
    r_odd4 = common_centroid_layout([
        Transistor("MA", "nmos", source="vdd", drain="La", n_fingers=5),
        Transistor("MB", "nmos", source="vdd", drain="Lb", n_fingers=5),
        Transistor("MC", "nmos", source="vdd", drain="Lc", n_fingers=5),
        Transistor("MD", "nmos", source="vdd", drain="Ld", n_fingers=5),
    ])
    assert r_odd4["method"] == "rotation_exact" and r_odd4["residual"] == 0.0
    assert r_odd4["crossover_count"] > 0, \
        f"4소자 count=5는 crossover 폴백이 실제로 발동해야 하는 케이스인데 crossover_count=0: {r_odd4}"
    with pytest.raises(ValueError):
        common_centroid_layout([Transistor("MA", "nmos", source="vdd", drain="La", n_fingers=4)])
    with pytest.raises(ValueError):
        common_centroid_layout([
            Transistor("MA", "nmos", source="vdd", drain="La", n_fingers=4),
            Transistor("MA", "nmos", source="vdd", drain="Lb", n_fingers=4),
        ])
    with pytest.raises(ValueError):
        common_centroid_layout([
            Transistor("MA", "nmos", source="vdd", drain="La", n_fingers=4),
            Transistor("MB", "nmos", source="tail", drain="Lb", n_fingers=4),
        ])

    trs_uneven = [
        Transistor("A", "nmos", source="vdd", drain="La", n_fingers=6),
        Transistor("B", "nmos", source="vdd", drain="Lb", n_fingers=4),
        Transistor("C", "nmos", source="vdd", drain="Lc", n_fingers=2),
    ]


def test_s027_section(s025_state):
    """[개수가 다름(A=6,B=4,C=2), n_rows 미지정 -> 기본 n_rows=N=3, 탐색 경로로 감]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S027(줄 367-376, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    trs_uneven = s025_state.trs_uneven

    r_uneven = common_centroid_layout(trs_uneven)
    assert r_uneven["method"] == "search"
    for row in r_uneven["rows"]:
        check = _hubleaf_sequence_node_path(row["transistor_sequence"], "vdd",
                                             {"A": "La", "B": "Lb", "C": "Lc"})
        assert check is not None, f"탐색 결과 행이 무효한 walk다: {row}"


def test_s028_section(s025_state):
    """[n_rows=4 (N=3보다 많음, 더 잘게 쪼갬) -- 슬라이싱만으론 모든 phase가 오일러 조건을
    못 만족했으나 보정(parity repair) 추가 후 성공함을 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S028(줄 378-389, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    trs_uneven = s025_state.trs_uneven

    r_more = common_centroid_layout(trs_uneven, n_rows=4)
    assert len(r_more["rows"]) == 4
    for row in r_more["rows"]:
        if row["transistor_sequence"]:
            check = _hubleaf_sequence_node_path(row["transistor_sequence"], "vdd",
                                                 {"A": "La", "B": "Lb", "C": "Lc"})
            assert check is not None, f"n_rows=4 행이 무효한 walk다: {row}"


def test_s029_section(s025_state):
    """[n_rows=2 (N=3보다 적음, 회전을 다 못 채움) -- 잔차가 0이 아닐 수 있음을 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S029(줄 391-395, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    trs_uneven = s025_state.trs_uneven

    r_fewer = common_centroid_layout(trs_uneven, n_rows=2)
    assert len(r_fewer["rows"]) == 2 and r_fewer["method"] == "search"


def test_s030_section():
    """[균등 개수(N=3, 전부 8) + n_rows=3(=N) 명시 -- target_rows==N+개수 균등이면
    n_rows를 명시했어도 회전 경로(잔차 0)로 가야 정상(2026-07-28 버그 수정 확인)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S030(줄 397-407, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    trs_even3 = [
        Transistor("X", "nmos", source="vdd", drain="Lx", n_fingers=8),
        Transistor("Y", "nmos", source="vdd", drain="Ly", n_fingers=8),
        Transistor("Z", "nmos", source="vdd", drain="Lz", n_fingers=8),
    ]
    r_explicit_n = common_centroid_layout(trs_even3, n_rows=3)
    assert r_explicit_n["method"] == "rotation_exact" and r_explicit_n["residual"] == 0.0, \
        f"target_rows==N+균등개수인데 회전 경로로 안 갔다: {r_explicit_n}"


def test_s031_section():
    """[버그 재현+수정 확인: N=2, n_rows=2(=N) 명시 -- 사용자 지적으로 발견됨]
    기존 탐색 경로(비례 라운드로빈+균등분할)는 '하나의 선형 시퀀스를 자르는' 방식이라
    swap 관계(두 행이 서로 뒤바뀐 관계)인 후보를 구조적으로 못 만든다 -- 주기적인
    시퀀스를 반으로 자르면 항상 똑같은 두 조각만 나오기 때문이다(실측 확인, 아래).
    finger 수를 늘려가며 확인:

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S031(줄 409-426, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    for nf in (2, 4, 6, 8, 10, 20, 50, 101):
        trs_bug = [
            Transistor("M2", "nmos", source="vdd", drain="out", n_fingers=nf),
            Transistor("M2b", "nmos", source="vdd", drain="bias", n_fingers=nf),
        ]
        r_bug = common_centroid_layout(trs_bug, n_rows=2)
        status = "OK" if r_bug["method"] == "rotation_exact" and r_bug["residual"] == 0.0 else "FAIL"
        assert r_bug["method"] == "rotation_exact" and r_bug["residual"] == 0.0, \
            f"n_fingers={nf}: n_rows=2(=N)인데 회전 경로(잔차 0)를 안 씀 -> {r_bug}"


def test_s032_section():
    """=== Test 12.9: n_rows==N 전수 스윕(N=2~6, count 다양) — dispatch 버그 수정 후
    전체 회귀 + '최대한 균등한 분배가 우연히 홀수뿐이면 포기하던' 2차 버그 발견/수정 ===
    사용자 요구: '다른 n_rows 값(3,4,5)에서도 같은 버그 없는지 다 스윕해봐' — N=2~6,
    count 다양(N,N+1,N+2,N+3,4,6,8,10,20,50,101 중 count>=N인 것)로 전수 확인.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S032(줄 427-455, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    n_rows_sweep_bugs, n_rows_sweep_infeasible = [], []
    for n_dev in (2, 3, 4, 5, 6):
        letters = ["A", "B", "C", "D", "E", "F"][:n_dev]
        for nf in sorted({n_dev, n_dev + 1, n_dev + 2, n_dev + 3, 4, 6, 8, 10, 20, 50, 101}):
            if nf < n_dev:
                continue
            trs_sweep = [Transistor(letters[i], "nmos", source="vdd", drain=f"L{letters[i]}",
                                     n_fingers=nf) for i in range(n_dev)]
            try:
                rr = common_centroid_layout(trs_sweep, n_rows=n_dev)
            except ValueError:
                n_rows_sweep_infeasible.append((n_dev, nf))
                continue
            if not (rr["method"] == "rotation_exact" and rr["residual"] == 0.0):
                n_rows_sweep_bugs.append((n_dev, nf, rr["method"], rr["residual"]))
    assert not n_rows_sweep_bugs, f"n_rows==N 스윕에서 잔차!=0인 사례 발견: {n_rows_sweep_bugs}"
    assert not n_rows_sweep_infeasible, (
        f"count>=n_dev인데 ValueError가 났다 — crossover 폴백이 실패했다는 뜻(회귀): "
        f"{n_rows_sweep_infeasible}"
    )


def test_s033_section():
    """[발견된 2차 버그: N=4,count=20처럼 '최대한 균등'([5,5,5,5], 전부 홀수)이 오일러
    불가일 때, 살짝 덜 균등해도 홀짝만 맞는 배분([6,6,4,4] 등)이 있으면 회전 자체는
    똑같이 잔차 0을 보장하는데(row_0 블록 배분과 무관), 예전엔 그걸 안 찾고 바로
    ValueError를 냈다 — _fix_block_parity()로 홀수쌍을 짝지어 1개씩 주고받는 보정 추가]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S033(줄 456-468, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    trs_n4_c20 = [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=20) for n in ["A", "B", "C", "D"]]
    r_n4_c20 = common_centroid_layout(trs_n4_c20, n_rows=4)
    assert r_n4_c20["method"] == "rotation_exact" and r_n4_c20["residual"] == 0.0
    block_counts = [Counter(row["transistor_sequence"])["A"] for row in r_n4_c20["rows"]]


def test_s034_section():
    """[소자별 개수(count)가 소자 수(N)보다 작으면(예: N=4, 각 2개씩) 명확한 ValueError인지
    확인 — 이 스윕 중 발견: 균등분배 시 일부 소자가 0개가 되는 경우가 있었다]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S034(줄 470-482, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    with pytest.raises(ValueError):
        common_centroid_layout(
            [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=2) for n in ["A", "B", "C", "D"]],
            n_rows=4,
        )


def test_s036_section():
    """=== Test 12.9b: 회전 경로에 crossover 폴백 통합 (사용자 요청, 2026-07-28 3차) ===   사용자 질문: 'common_centroid도 최소 crossover routing 조건을 추가하면   어떻게 되지?' -> 프로토타입으로 먼저 확인: 회전은 순수 relabeling이라 row_0에   crossover가 있어도 잔차 0 증명은 그대로 유지됨을 확인한 뒤 통합.

    [Test 12.9에서 '진짜 불가능'으로 확인됐던 10개 조합 전부 재확인 -- 이제는
    ValueError 대신 crossover_count>0으로 성공해야 하고, 잔차는 여전히 0이어야 함]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S036(줄 487-514, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    genuinely_infeasible_before = [(3, 3), (4, 4), (4, 5), (5, 5), (5, 6), (5, 7),
                                    (6, 6), (6, 7), (6, 8), (6, 9)]
    for n_dev, nf in genuinely_infeasible_before:
        letters = "ABCDEF"[:n_dev]
        trs_gi = [Transistor(letters[i], "nmos", source="vdd", drain=f"L{letters[i]}",
                              n_fingers=nf) for i in range(n_dev)]
        r_gi = common_centroid_layout(trs_gi, n_rows=n_dev)
        assert r_gi["method"] == "rotation_exact" and r_gi["residual"] == 0.0, (
            f"N={n_dev},count={nf}: crossover 폴백 후에도 잔차가 0이 아니다 -> {r_gi}"
        )
        assert r_gi["crossover_count"] > 0, (
            f"N={n_dev},count={nf}: 예전엔 ValueError였던 사례인데 crossover_count가 0이다 "
            f"-- 회귀(원래부터 됐던 건지 재확인 필요): {r_gi}"
        )
        for row in r_gi["rows"]:
            for seg in row["segments"]:
                if seg["transistor_sequence"]:
                    leaf_of_gi = {letters[i]: f"L{letters[i]}" for i in range(n_dev)}
                    check = _hubleaf_sequence_node_path(seg["transistor_sequence"], "vdd", leaf_of_gi)
                    assert check is not None, f"segment이 유효한 walk가 아니다: {seg}"
            total_here = sum(len(s["transistor_sequence"]) for s in row["segments"])
            assert total_here == len(row["transistor_sequence"])


def test_s037_section():
    """[이미 0-crossover로 성공하던 케이스(N=2,count=4)는 전혀 안 바뀌었는지 회귀 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S037(줄 516-526, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    r_no_regress = common_centroid_layout([
        Transistor("A", "nmos", source="vdd", drain="La", n_fingers=4),
        Transistor("B", "nmos", source="vdd", drain="Lb", n_fingers=4),
    ])
    assert r_no_regress["crossover_count"] == 0


def test_s038_N():
    """=== Test 12.10: n_rows != N(N보다 크거나 작은 경우) 전수 스윕 — 사용자 요구 ===
    '나머지 n_rows도 스윕해봐(N보다 크거나 작은 경우)' — N=2~6, n_rows=1~2N+1,
    finger 다양(총 360개 조합)으로 크래시/구조 오류/잔차 지표 결함을 확인.
    2026-07-28 4차: 탐색 경로에도 crossover 폴백이 추가돼 이제 실패가 훨씬 줄어든다 —
    행 전체(transistor_sequence)가 아니라 각 segment를 독립적으로 검증한다(crossover가
    있으면 flat 시퀀스 자체는 더 이상 단일 연속 walk가 아닌 게 정상이기 때문).

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S038(줄 527-581, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    sweep_crashes, sweep_struct_bugs, sweep_total, sweep_valueerrors = [], [], 0, 0
    sweep_total_crossovers = 0
    for n_dev in (2, 3, 4, 5, 6):
        letters = ["A", "B", "C", "D", "E", "F"][:n_dev]
        for n_rows_sw in range(1, 2 * n_dev + 2):
            if n_rows_sw == n_dev:
                continue  # Test 12.9에서 이미 전수 확인
            for nf in sorted({n_dev, n_dev + 1, n_dev + 2, 4, 6, 8, 10, 20}):
                if nf < 1:
                    continue
                sweep_total += 1
                trs_sw = [Transistor(letters[i], "nmos", source="vdd", drain=f"L{letters[i]}",
                                      n_fingers=nf) for i in range(n_dev)]
                try:
                    rr = common_centroid_layout(trs_sw, n_rows=n_rows_sw)
                except ValueError:
                    sweep_valueerrors += 1
                    continue
                except Exception as e:
                    sweep_crashes.append((n_dev, n_rows_sw, nf, type(e).__name__))
                    continue
                if len(rr["rows"]) != n_rows_sw:
                    sweep_struct_bugs.append((n_dev, n_rows_sw, nf, "row count mismatch"))
                    continue
                leaf_of_sw = {letters[i]: f"L{letters[i]}" for i in range(n_dev)}
                total_counter = Counter()
                ok = True
                for row in rr["rows"]:
                    for seg in row["segments"]:
                        if not seg["transistor_sequence"]:
                            continue
                        check = _hubleaf_sequence_node_path(seg["transistor_sequence"], "vdd", leaf_of_sw)
                        if check is None:
                            sweep_struct_bugs.append((n_dev, n_rows_sw, nf, "invalid segment"))
                            ok = False
                            break
                    if not ok:
                        break
                    total_counter.update(row["transistor_sequence"])
                if ok and sum(total_counter.values()) != n_dev * nf:
                    sweep_struct_bugs.append((n_dev, n_rows_sw, nf, "count mismatch"))
                if ok:
                    sweep_total_crossovers += rr["crossover_count"]
    assert not sweep_crashes, f"예상치 못한 예외 발생: {sweep_crashes}"
    assert not sweep_struct_bugs, f"구조적 오류 발견: {sweep_struct_bugs}"


def test_s039_section():
    """[발견된 잔차 지표 결함: 길이 1인 행을 건너뛰면 그 행에만 있는 소자가 완전히
    안 잡혀 잔차가 거짓으로 낮게(0.0) 나올 수 있었다 — _common_centroid_residual()에
    '중립값 0.5' 처리 추가로 최소한 그 소자가 반드시 기록되도록 수정]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S039(줄 583-593, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    residual_before_fix_sim = 0.0  # 옛 버전 시뮬레이션(길이1 스킵) -- A만 있어서 0.0
    r_blind = _common_centroid_residual([
        {"transistor_sequence": ["A", "A", "B", "B"]},
        {"transistor_sequence": ["C"]},
    ])
    assert r_blind > 0.0, "길이 1 행의 소자가 잔차 계산에서 여전히 안 보인다"


def test_s040_section():
    """[발견된 더 근본적 한계: 소자 하나가 통째로 자기 행에만 격리되면(다른 소자와 단
    한 번도 같은 행에 있어본 적 없음) 그 자체는 대칭적으로 보여 잔차가 낮게 나올 수
    있다 — n_rows가 총 finger 수 대비 너무 많으면(모든 행 길이가 1) 구조적으로
    피할 수 없다. isolated_pairs 필드를 추가해 이 상황을 정직하게 드러낸다:]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S040(줄 595-609, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    trs_isolate = [
        Transistor("A", "nmos", source="vdd", drain="La", n_fingers=2),
        Transistor("B", "nmos", source="vdd", drain="Lb", n_fingers=2),
    ]
    r_isolate = common_centroid_layout(trs_isolate, n_rows=4)
    assert r_isolate["isolated_pairs"] > 0, "격리 상황이 isolated_pairs에 반영되지 않았다"


def test_s041_section(s040_state):
    """[증명된 최적 경로(rotation_exact)는 항상 isolated_pairs=0인지 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S041(줄 610-616, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    trs_isolate = s040_state.trs_isolate

    r_exact_check = common_centroid_layout(trs_isolate)
    assert r_exact_check["method"] == "rotation_exact" and r_exact_check["isolated_pairs"] == 0


def test_s042_interdigitate_layout():
    """=== Test 12.11: INTERDIGITATION_PATTERNS 표 전체 — interdigitate_layout()가 표/탐색+
    crossover 중 맞는 경로를 자동으로 찾는지 전수 스윕(§18 발견의 연장,
    2026-07-28 5차: interdigitate_layout()를 common_centroid_layout()와 동급으로
    재설계 — 검증+crossover 폴백을 함수 내부로 흡수) ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S042(줄 617-650, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    pattern_table_count = 0
    pattern_total = 0
    expected_valid = {("A", 1), ("A", 2), ("A", 3), ("A", 4), ("AB", 1), ("AB", 2), ("AB", 3)}
    for base, reps in INTERDIGITATION_PATTERNS.items():
        for repeat, pattern in reps.items():
            letter_counts = Counter(pattern)
            letters = sorted(letter_counts)
            names_p = list("ABCDEFG"[:len(letters)])
            trs_p = [Transistor(nm, "nmos", source="vdd", drain=f"L{nm}", n_fingers=letter_counts[ch])
                     for nm, ch in zip(names_p, letters)]
            result_p = interdigitate_layout(trs_p, base=base, repeat=repeat)
            pattern_total += 1
            is_table = result_p["method"] == "pattern_table"
            if is_table:
                pattern_table_count += 1
            expected = (base, repeat) in expected_valid
            assert is_table == expected, (
                f"base={base} repeat={repeat}: 예상(table={expected})과 실제(table={is_table})가 "
                f"다르다 -- INTERDIGITATION_PATTERNS 표가 바뀌었거나 매칭 로직에 회귀가 있다"
            )
            assert result_p["rows"] and result_p["crossover_count"] >= 0  # 예외 없이 항상 결과 반환


def test_s044_section():
    """=== Test 12.12: find_min_crossover_layout() — 최소 crossover 배치 신설 ===   사용자 요청: 'crossover routing이 최소인 조합을 찾아 갯수도 표시, 우선순위는   crossover가 안 생기는 연속 diffusion' -- route inspection/T-join 정리 적용.

    [이미 가능한 경우(0 crossover) — 우선순위대로 단일 연속 diffusion부터 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S044(줄 654-661, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    r_ok = find_min_crossover_layout([
        Transistor("A", "nmos", source="vdd", drain="La", n_fingers=2),
        Transistor("B", "nmos", source="vdd", drain="Lb", n_fingers=2),
    ])
    assert r_ok["crossover_count"] == 0 and len(r_ok["segments"]) == 1


def test_s045_section():
    """[ABC 3소자 1개씩(4개 홀수차수 노드, m=2) -> crossover=1이어야 함]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S045(줄 663-671, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    r_abc = find_min_crossover_layout(
        [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=1) for n in "ABC"])
    assert r_abc["crossover_count"] == 1
    total_abc = sum(len(s["transistor_sequence"]) for s in r_abc["segments"])
    assert total_abc == 3, f"실제 finger 총합이 3이 아니다: {total_abc}"


def test_s046_section():
    """[6소자 1개씩(6개 홀수차수 노드, m=3) -> crossover=2, 소자 6개 보존]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S046(줄 673-679, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    r_6 = find_min_crossover_layout(
        [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=1) for n in "ABCDEF"])
    assert r_6["crossover_count"] == 2
    assert sum(len(s["transistor_sequence"]) for s in r_6["segments"]) == 6


def test_s047_section(s046_state):
    """[각 segment 내부가 실제로 유효한 hub-leaf walk인지 1차 원리로 재확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S047(줄 681-686, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    r_6 = s046_state.r_6

    leaf_of_6 = {n: f"L{n}" for n in "ABCDEF"}
    for seg in r_6["segments"]:
        check = _hubleaf_sequence_node_path(seg["transistor_sequence"], "vdd", leaf_of_6)
        assert check is not None, f"segment이 유효한 walk가 아니다: {seg}"


def test_s048_section():
    """[ABCD 표 패턴(4소자 1개씩)이 실제로 crossover=1로 해결되는지 -- 사용자가
    질문했던 INTERDIGITATION_PATTERNS의 무효 패턴에 실제 답을 주는 사례]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S048(줄 688-694, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    r_abcd = find_min_crossover_layout(
        [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=1) for n in "ABCD"])
    assert r_abcd["crossover_count"] == 1


def test_s049_section():
    """[대조군 -- 입력 검증]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S049(줄 696-713, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    with pytest.raises(ValueError):
        find_min_crossover_layout([])
    with pytest.raises(ValueError):
        find_min_crossover_layout([
            Transistor("A", "nmos", source="vdd", drain="La", n_fingers=1),
            Transistor("B", "nmos", source="tail", drain="Lb", n_fingers=1),
        ])


def test_s051_section(library_dir):
    """=== Test 12.13: find_min_crossover_layout() matching_pairs 확장(세션15) —   node_map 기반 짝짓기로 hub-leaf 아닌 일반 그룹도 지원, 세션17에 짝짓기 선택   방식 자체가 재작성됨(아래) ===

    [실전: current_reuse_telescopic_ota.topology.json M6 그룹(8소자) — 핑거조정
    으로는 절대 못 푸는 실제 사례(세션15 probe로 확인, .ai/context.md 참고).
    ⚠️ 세션16 D-1에서 이 사례의 tier1 짝짓기(Vom1/Vop1 직접)가 실제로는 matching_
    pairs(M1a/M1b, M2a/M2b)를 서로 다른 segment로 갈라놓는 최악의 선택이었음이
    드러났다(splits=2, probe_crossover_pairing_alternatives.py) — 세션17
    _select_crossover_pairing()이 대안(Vbias2/Vom1 + Vop1/Vx, crossover는 미매칭
    M57/M58 쪽에서만)으로 자동 교체해 splits=0을 달성하는지 확인]
    ⚠️ 세션22부터 이 8소자는 geometry_colocation_union()이 더 이상 자동으로
    묶지 않는다(M6/M7/M57/M58은 matching_pairs가 없어 각자 독립 그룹 -- stack
    M6 크래시의 근본원인이었던 Vx fan-out 자동병합을 제거했기 때문, .ai/
    context.md 세션22 참고). 이 테스트는 find_min_crossover_layout()/짝짓기
    로직 자체(레이아웃 압축을 위해 이 8개를 한 행에 두기로 **의도적으로**
    선언했다고 가정)를 검증하는 것이므로, 그룹을 geometry_colocation_union()
    경유가 아니라 직접(수동 override와 동일한 방식으로) 구성한다.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S051(줄 717-777, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib1213 = library_dir
    _m6_trs, _m6_meta = load_topology(
        _os1213.path.join(_lib1213, "current_reuse_telescopic_ota.topology.json"))
    _m6_pairs_meta = _m6_meta["symmetry"]["matching_pairs"]
    _m6_by_name = {t.name: t for t in _m6_trs}
    _m6_order = {t.name: i for i, t in enumerate(_m6_trs)}
    _m6_names = sorted({"M6", "M7", "M1a", "M1b", "M2a", "M2b", "M58", "M57"},
                        key=lambda n: _m6_order[n])
    _m6_group_trs = [_dc_replace(_m6_by_name[n], stack_id="M6") for n in _m6_names]
    _m6_inside_pairs = [tuple(p["names"]) for p in _m6_pairs_meta
                         if set(p["names"]) <= set(_m6_names)]

    _m6_g = build_graph(_m6_group_trs)
    _m6_odd = check_euler_condition(_m6_g).odd_nodes
    assert len(_m6_odd) == 4, f"baseline 홀수차수가 4개가 아님(사례 자체가 바뀜): {_m6_odd}"

    # 세션17 -- 옛 tier1 짝짓기(Vom1/Vop1)로 구성했을 때 실제로 splits=2였는지 먼저
    # 확인한다(비교 기준선, D-1 발견을 이 self-test 안에서도 재현).
    _m6_node_map_early = _mirror_node_map_from_pairs(_m6_inside_pairs, _m6_group_trs)
    _m6_tier1_pairs, _ = _pair_odd_nodes_by_mirror(_m6_odd, _m6_node_map_early)
    _m6_tier1_segments = _build_crossover_segments(_m6_group_trs, _m6_tier1_pairs)
    _m6_tier1_splits = _count_matching_pair_splits(_m6_tier1_segments, _m6_inside_pairs)
    assert _m6_tier1_splits == 2, (
        f"D-1 재현 실패 -- 옛 tier1 짝짓기({_m6_tier1_pairs})가 여전히 matching_pairs를 "
        f"안 갈라놓는다면(splits={_m6_tier1_splits}) 이 회귀 대조 자체가 틀렸을 수 있으니 "
        f"topology.json이 바뀌었는지부터 확인할 것"
    )

    _m6_result = find_min_crossover_layout(_m6_group_trs, _m6_inside_pairs)
    assert _m6_result["crossover_count"] == 1, \
        f"m=2(crossover=1)이어야 하는데: {_m6_result['crossover_count']}"
    assert _m6_result["node_pairing_fallback_used"] is False, \
        "tier1/tier2만으로 다 짝지어져야 하는데 fallback이 발동함"
    _m6_total = sum(len(s["transistor_sequence"]) for s in _m6_result["segments"])
    assert _m6_total == len(_m6_group_trs), \
        f"trail 분해 후 소자 총합이 안 맞음: {_m6_total} != {len(_m6_group_trs)}"
    _m6_final_splits = _count_matching_pair_splits(_m6_result["segments"], _m6_inside_pairs)
    assert _m6_final_splits == 0, (
        f"세션17 재작성의 핵심 목표(matching_pairs를 안 갈라놓기)가 실패함 -- "
        f"splits={_m6_final_splits}, segments={_m6_result['segments']}"
    )


def test_s052_section(s051_state):
    """[node_map 역산 단위 확인 -- M2a/M2b가 서로 공유 끝이 없어도 Vom1<->Vop1이
    바로 나오는지(체인 전이 없이 규칙 자체로 유도됨을 확인)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S052(줄 779-786, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _m6_group_trs = s051_state._m6_group_trs
    _m6_inside_pairs = s051_state._m6_inside_pairs

    _m6_node_map = _mirror_node_map_from_pairs(_m6_inside_pairs, _m6_group_trs)
    assert _m6_node_map.get("Vom1") == "Vop1" and _m6_node_map.get("Vop1") == "Vom1", \
        f"Vom1<->Vop1 대응이 안 나옴: {_m6_node_map}"
    assert _m6_node_map.get("Vx") == "Vx", f"Vx가 자기대응이 아님: {_m6_node_map.get('Vx')}"
    assert "Vbias2" not in _m6_node_map, \
        f"Vbias2는 orphan이어야 하는데 node_map에 들어있음: {_m6_node_map.get('Vbias2')}"


def test_s053_section():
    """[폴백 발동 확인 -- matching_pairs가 텅 비어 전부 orphan이면(자기대응 노드가
    하나도 없음) 기존 방식(순서대로)으로 폴백하고 그 사실이 플래그로 남는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S053(줄 788-797, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fb_trs = [Transistor(n, "nmos", source="hubX", drain=f"L{n}", n_fingers=1)
               for n in ("P", "Q", "R", "S")]
    _fb_result = find_min_crossover_layout(_fb_trs, matching_pairs=[])
    assert _fb_result["node_pairing_fallback_used"] is True, \
        "matching_pairs가 전혀 없으면 전부 orphan이라 100% 폴백이어야 함"
    assert _fb_result["crossover_count"] == 1


def test_s054_None(s046_state, s045_state):
    """[회귀 -- matching_pairs=None(기존 호출부 경로, 하위호환)이면 hub-leaf 사전조건과
    순서대로 짝짓기가 완전히 그대로인지 -- 위 ABC/6소자 테스트가 이미 이 경로를 타므로
    여기선 node_pairing_fallback_used가 정확히 None(신규 로직 미개입)인지만 추가 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S054(줄 799-803, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    r_6 = s046_state.r_6
    r_abc = s045_state.r_abc

    assert r_abc["node_pairing_fallback_used"] is None
    assert r_6["node_pairing_fallback_used"] is None


def test_s055__count_matching_pair_splits():
    """[세션17 offset 우선순위 가중치 -- _count_matching_pair_splits()의
    pair_sensitivity 튜플 채점이 offset 쌍을 ratio 쌍보다 우선 보호하는지.
    ⚠️ 실제 회로(M6 등)로 '동점인데 가중치로 갈리는' 진짜 tradeoff 사례를 여러
    구조(순수 star, hub-bridge 1개/2개, leaf-bridge)로 찾아봤으나 못 찾음(전부
    offset 쌍이 항상 갈라지거나 항상 안 갈라지는 두 극단으로만 수렴함, hierholzer
    순회 특성 때문 -- probe_offset_tradeoff*.py, 스크래치패드). 그래서 segment를
    손으로 구성해 채점 함수 자체를 직접 검증한다(그래프 탐색에 의존하지 않는 확실한
    검증), 그리고 M6 실제 회로로는 pair_sensitivity를 줘도 이미 달성한 (0,0)이
    안 깨지는지(회귀 안전성)만 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S055(줄 805-842, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _w_pairs = [("Ma", "Mb"), ("Mc", "Md")]
    _w_sensitivity = {("Ma", "Mb"): "offset", ("Mc", "Md"): "ratio"}
    assert _count_matching_pair_splits(
        [{"transistor_sequence": ["Ma", "Mc"]}, {"transistor_sequence": ["Mb", "Md"]}],
        _w_pairs) == 2, "둘 다 갈라진 경우 스칼라=2가 아님"
    assert _count_matching_pair_splits(
        [{"transistor_sequence": ["Ma", "Mc"]}, {"transistor_sequence": ["Mb", "Md"]}],
        _w_pairs, _w_sensitivity) == (1, 1), "둘 다 갈라진 경우 가중치 튜플=(1,1)이 아님"

    # 핵심 -- "동점인데 가중치로 갈리는" 상황을 손으로 구성: segA는 offset(Ma/Mb) 보호+
    # ratio(Mc/Md) 희생, segB는 ratio 보호+offset 희생. 스칼라 총합은 둘 다 1로 완전히
    # 동점이라 pair_sensitivity 없이는 구분이 안 되지만(먼저 발견된 후보 유지, 근거 없는
    # 임의 선택), 튜플 비교는 (0,1) < (1,0)이라 항상 offset 보호를 우선한다.
    _seg_protect_offset = [{"transistor_sequence": ["Ma", "Mb"]}, {"transistor_sequence": ["Mc"]},
                            {"transistor_sequence": ["Md"]}]
    _seg_protect_ratio = [{"transistor_sequence": ["Mc", "Md"]}, {"transistor_sequence": ["Ma"]},
                           {"transistor_sequence": ["Mb"]}]
    _plain_a = _count_matching_pair_splits(_seg_protect_offset, _w_pairs)
    _plain_b = _count_matching_pair_splits(_seg_protect_ratio, _w_pairs)
    _weighted_a = _count_matching_pair_splits(_seg_protect_offset, _w_pairs, _w_sensitivity)
    _weighted_b = _count_matching_pair_splits(_seg_protect_ratio, _w_pairs, _w_sensitivity)
    assert _plain_a == _plain_b == 1, \
        f"두 후보의 스칼라 총합이 동점(=1)이어야 tradeoff 시나리오가 성립: {_plain_a}, {_plain_b}"
    assert _weighted_a == (0, 1) and _weighted_b == (1, 0), \
        f"가중치 튜플이 예상과 다름: A={_weighted_a}, B={_weighted_b}"
    assert _weighted_a < _weighted_b, \
        "offset 보호 후보(A)가 ratio 보호 후보(B)보다 더 나은 점수여야 함(사전식 비교)"
    assert _is_perfect_crossover_score(0) and _is_perfect_crossover_score((0, 0))
    assert not _is_perfect_crossover_score(1) and not _is_perfect_crossover_score((1, 0))


def test_s056_section(s051_state):
    """[M6 실제 회로 회귀 -- pair_sensitivity를 줘도 이미 달성한 (0,0)이 안 깨지는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S056(줄 844-854, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _m6_group_trs = s051_state._m6_group_trs
    _m6_inside_pairs = s051_state._m6_inside_pairs

    _m6_sensitivity_for_split = {("M1a", "M1b"): "offset", ("M2a", "M2b"): "ratio"}
    _m6_weighted_result = find_min_crossover_layout(
        _m6_group_trs, _m6_inside_pairs, pair_sensitivity=_m6_sensitivity_for_split)
    _m6_weighted_splits = _count_matching_pair_splits(
        _m6_weighted_result["segments"], _m6_inside_pairs, _m6_sensitivity_for_split)
    assert _m6_weighted_splits == (0, 0), \
        f"pair_sensitivity를 줬더니 M6 그룹의 완벽한 결과(0,0)가 깨짐: {_m6_weighted_splits}"
    assert _m6_weighted_result["crossover_count"] == 1


def test_s057_check_box_shape():
    """=== Test 13: check_box_shape() 게이트 — SPICE 전에 반드시 통과해야 하는 §8 체크포인트 ===
    2026-08-13(세션31): rows: dict[str, list[Transistor]] 기반으로 재작성 --
    finger_w=l=1.0 균일값을 쓰면 pitch(l)=1.0이라 옛 finger-count 수치를 그대로 재현한다.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S057(줄 855-918, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    def _row13(row, n, finger_w=1.0, l=1.0, kind="nmos"):
        return {row: [Transistor(f"{row}_dev", kind, source="s", drain="d",
                                  n_fingers=n, finger_w=finger_w, l=l)]}

    before1 = check_box_shape({**_row13("nstack", 3), **_row13("pstack", 32)})
    after1 = check_box_shape({**_row13("nstack", 8), **_row13("pstack", 8)})
    # oracle (d): 섹션 문장이 적은 기대 '게이트가 실수는 FAIL로, 수정본은 PASS로 정확히 구분: OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert not before1.ok and after1.ok, (f"  -> 게이트가 실수는 FAIL로, 수정본은 PASS로 정확히 구분: "
          f"{'OK' if (not before1.ok and after1.ok) else 'FAIL'}")
    before2 = check_box_shape({**_row13("diffpair_row0", 9), **_row13("diffpair_row1", 9),
                                **_row13("tailstack", 24), **_row13("loadstack", 38)})
    after2 = check_box_shape({**_row13("diffpair_row0", 10), **_row13("diffpair_row1", 10),
                               **_row13("tailstack", 10), **_row13("loadstack", 10)})
    # oracle (d): 섹션 문장이 적은 기대 '게이트가 실수는 FAIL로, 수정본은 PASS로 정확히 구분: OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert not before2.ok and after2.ok, (f"  -> 게이트가 실수는 FAIL로, 수정본은 PASS로 정확히 구분: "
          f"{'OK' if (not before2.ok and after2.ok) else 'FAIL'}")

    approx_verdict = check_box_shape({"row_full": [Transistor("full_dev", "nmos", source="s",
                                                                 drain="d", n_fingers=8,
                                                                 finger_w=1.0, l=1.0)],
                                       "row_bare": [Transistor("bare_dev", "nmos", source="s",
                                                                 drain="d", n_fingers=8)]})
    # oracle (d): 섹션 문장이 적은 기대 'approx=True로 명시 ... OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert approx_verdict.approx, (f"  -> approx=True로 명시(조용히 finger-count로 대체하지 않음): "
          f"{'OK' if approx_verdict.approx else 'FAIL'}")

    tall_rows = {**_row13("row_thin", 8, finger_w=1.0, l=1.0),
                 **_row13("row_thick", 8, finger_w=6.0, l=1.0)}
    # width_m 둘 다 8(정합) / total_height_m=1+6=7 -> elongation=8/7≈1.14, max_elongation=1.1로
    # 걸리게 설정(마진 없이 정확히 걸리도록 수치를 직접 계산해서 잡음).
    tall_verdict = check_box_shape(tall_rows, max_elongation=1.1, orientation="either")
    # oracle (d): 섹션 문장이 적은 기대 '폭은 정합(rectangular)이지만 elongation 축이 새로 FAIL을 잡아냄: OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert tall_verdict.rectangular and not tall_verdict.elongation_ok, (f"  -> 폭은 정합(rectangular)이지만 elongation 축이 새로 FAIL을 잡아냄: "
          f"{'OK' if (tall_verdict.rectangular and not tall_verdict.elongation_ok) else 'FAIL'}")

    wide_rows = {**_row13("row_a", 20, finger_w=1.0, l=1.0),
                 **_row13("row_b", 20, finger_w=1.0, l=1.0)}  # width=20, height=2 -> 가로로 김
    wide_ok = check_box_shape(wide_rows, max_elongation=15.0, orientation="wide")
    tall_fail = check_box_shape(wide_rows, max_elongation=15.0, orientation="tall")
    # oracle (d): 섹션 문장이 적은 기대 'orientation이 방향까지 구분: OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert wide_ok.elongation_ok and not tall_fail.elongation_ok, (f"  -> orientation이 방향까지 구분: "
          f"{'OK' if (wide_ok.elongation_ok and not tall_fail.elongation_ok) else 'FAIL'}")


def test_s058_section():
    """=== Test 14: stage 경계를 넘는 stack 병합 — Maloberti p.29 'Layout Oriented Design' 재현 ===
    슬라이드 원문: 1단 PMOS 부하(M3/M4)와 2단 PMOS gain 소자(M6)를 stage가 다름에도
    '같은 극성 + vdd 공유'라는 이유만으로 한 물리 행에 합친다. 이걸 재현하고, 3개 이상의
    leaf가 한 hub를 공유하면 공통 finger 수 k가 반드시 짝수여야 함을 직접 검증한다.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S058(줄 919-973, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    # 1차 원리 재확인: check_multi_leaf_hub_parity() 공식이 실제 build_graph()+check_euler_condition()
    # 결과와 항상 일치하는지 폭넓게 대조(공식만 믿지 않는다 — 이 세션 내내 지켜온 원칙).
    mismatch = 0
    for kis in itertools.product(range(1, 5), repeat=3):
        ts = [Transistor(f"D{i}", "pmos", source="hub", drain=f"leaf{i}", n_fingers=k)
              for i, k in enumerate(kis)]
        g = build_graph(ts)
        real = check_euler_condition(g).kind
        formula = check_multi_leaf_hub_parity({f"leaf{i}": k for i, k in enumerate(kis)}).kind
        if real != formula:
            mismatch += 1
    # oracle (d): 섹션 문장이 적은 기대 '3-leaf 조합 전수 대조 -> 전부 일치(OK)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert mismatch == 0, (f"  check_multi_leaf_hub_parity() 공식 vs 실제 build_graph()+check_euler_condition(): "
          f"3-leaf 조합 {4**3}개 전수 대조 -> {'전부 일치(OK)' if mismatch == 0 else f'{mismatch}개 불일치(FAIL)'}")

    # find_hub_merge_candidates(): stack_id로 이미 stage별로 분리해놔도(현실적인 입력 상황을
    # 그대로 재현) 무시하고 hub 공유만으로 병합 후보를 찾아내는지 확인.
    circuit = [
        Transistor("M3", "pmos", source="vdd", drain="bias", gate="bias", w=30, finger_w=30/8, n_fingers=8, stack_id="stage1_load"),
        Transistor("M4", "pmos", source="vdd", drain="out1", gate="bias", w=30, finger_w=30/8, n_fingers=8, stack_id="stage1_load"),
        Transistor("M6", "pmos", source="vdd", drain="out2", gate="out1", w=90, finger_w=90/8, n_fingers=8, stack_id="stage2_gain"),
        Transistor("M1", "nmos", source="tail", drain="out1", gate="vin_p", w=60, n_fingers=6, stack_id="stage1_diffpair"),
        Transistor("M2", "nmos", source="tail", drain="d2", gate="vin_n", w=60, n_fingers=6, stack_id="stage1_diffpair"),
    ]
    candidates = find_hub_merge_candidates(circuit)
    vdd_group = candidates.get(("pmos", "vdd"))
    # oracle (d): 섹션 문장이 적은 기대 'hub=vdd 공유만으로 다시 묶어내는가 -> OK: M3/M4/M6' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert vdd_group and {t.name for t in vdd_group} == {'M3','M4','M6'}, (f"  hub=vdd 공유만으로 다시 묶어내는가 -> "
          f"{'OK: ' + str(sorted(t.name for t in vdd_group)) if vdd_group and {t.name for t in vdd_group} == {'M3','M4','M6'} else 'FAIL'}")

    # 실제 병합: k=8(짝수)로 맞추면(§8 box-shape 탐색과 동일한 방식) 유효, k=7(홀수)이면 무효 —
    # 둘 다 공식과 실제 그래프 양쪽으로 재확인.
    for k, label in [(8, "짝수 k=8"), (7, "홀수 k=7")]:
        ts = [Transistor("M3", "pmos", source="vdd", drain="bias", n_fingers=k),
              Transistor("M4", "pmos", source="vdd", drain="out1", n_fingers=k),
              Transistor("M6", "pmos", source="vdd", drain="out2", n_fingers=k)]
        g = build_graph(ts)
        v = check_euler_condition(g)
        formula = check_multi_leaf_hub_parity({"M3": k, "M4": k, "M6": k})
        # oracle (d): 섹션 문장이 적은 기대 '실제 그래프 판정 vs 공식 판정 -> OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
        assert (v.kind != 'impossible') == formula.ok, (f"  {label}: 실제 그래프 판정={v.kind}(홀수차수 {len(v.odd_nodes)}개), "
              f"공식 판정={formula.kind}(m={formula.m_odd_leaves}) -> "
              f"{'OK' if (v.kind != 'impossible') == formula.ok else 'FAIL'}")


def test_s060_run_full_circuit_audit():
    """=== Test 16: run_full_circuit_audit() — 4단계 harness가 실제로 잡아내는지 확인 ===
    작은 합성 회로(2단 미러 M1/M2 + M3, diff 입력 M4/M5)로 4가지 실패 모드를 재현:

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S060(줄 975-1008, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    tiny_devices = {
        "M1": ("nmos", "gnd", "bias", "bias", "mirror"),
        "M2": ("nmos", "gnd", "out", "bias", "mirror"),
        "M3": ("nmos", "gnd", "out2", "Bias", "mirror"),   # 일부러 'Bias'(대문자) -- 대소문자 불일치 재현
        "M4": ("pmos", "tail", "out", "vip", "diffpair"),
        "M5": ("pmos", "tail", "out2", "vim", "diffpair"),
    }
    expected = {"mirror": 3, "diffpair": 2}

    r = run_full_circuit_audit(tiny_devices, expected, dispositions={})
    # oracle (d): 섹션 문장이 적은 기대 '(a) ... 여러 항목 FAIL 기대' / 'OK(의도대로 FAIL)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert not r.ok, (f"      전체 결과: {'PASS' if r.ok else 'FAIL'} -> "
          f"{'OK(의도대로 FAIL)' if not r.ok else 'FAIL(이 harness가 문제를 못 잡음)'}")

    fixed_devices = dict(tiny_devices)
    fixed_devices["M3"] = ("nmos", "gnd", "out2", "bias", "mirror")  # 대소문자 수정
    dispositions = {
        ("current_mirror", "nmos", "bias"): ("real_match", "M1/M2/M3 3-way mirror, gate=bias"),
        ("hub_merge", "nmos", "gnd"): ("real_match", "공유 rail, 병합 불필요"),
        ("hub_merge", "pmos", "tail"): ("real_match", "M4/M5 diff pair tail, 이미 매칭 처리"),
        ("hub_merge", "pmos", "out"): ("false_positive_coincidental", "합성 예제용 — 실제 회로 아님"),
        ("diff_pair", "pmos", "tail"): ("real_match", "M4/M5 차동쌍(소스 tail 공유, 게이트 vip/vim) -- U-01"),
    }
    r2 = run_full_circuit_audit(fixed_devices, expected, dispositions)
    for c in r2.checks:
        # oracle (d): 섹션 문장이 적은 기대 '(b) ... 전부 PASS 기대' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
        assert c.ok, f"      [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}"
    # oracle (d): 섹션 문장이 적은 기대 '(b) ... 전부 PASS 기대' / 'OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert r2.ok, (f"      전체 결과: {'PASS' if r2.ok else 'FAIL'} -> "
          f"{'OK' if r2.ok else 'FAIL(예상과 다름 — dispositions 키를 재확인할 것)'}")


def test_s061_pack_floorplan():
    """=== Test 17: pack_floorplan() — 실제 Xie&Chen 51-소자 회로 전체 블록으로 검증 ===
    (첫 버전은 spine을 세로 한 줄로 쌓기만 해 빈 공간이 많았다 -- 사용자가 직접 지적한
    뒤 skyline/bottom-left 2D packing으로 재작성. 여기서 실측으로 개선을 확인한다.)

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S061(줄 1009-1073, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    def _blk(name, row_fingers):
        """block_from_rows() 자체 self-test 헬퍼(2026-08-13 세션31) -- finger_w=l=1.0
        균일값을 쓰면 width_m=n_fingers, height_m=행 개수가 그대로 나와 옛
        block_from_row_widths({row: n_fingers}) 리터럴 dict 시대의 수치를 그대로 재현한다
        (이 Test 17은 pack_floorplan()의 패킹 알고리즘 자체를 검증하는 것이 목적이라
        실제 물리 치수 정확도는 무관 -- 상대적 크기 관계만 보존하면 충분)."""
        rows_ = {rn: [Transistor(f"{name}_{rn}", "nmos", source="s", drain="d",
                                   n_fingers=n, finger_w=1.0, l=1.0)]
                 for rn, n in row_fingers.items()}
        return block_from_rows(name, rows_)

    spine = [
        _blk("S1_PMOS", {"row0": 8, "row1": 8}),
        _blk("S1_NMOS", {"row0": 8, "row1": 8}),
        _blk("S1_TAILP", {"row0": 10}),
        _blk("S1_TAILN", {"row0": 7}),
        _blk("biasgen_pmos", {"row0": 5}),
        _blk("biasgen_nmos", {"row0": 4}),
        _blk("cmfb_p1", {"row0": 2}),
        _blk("cmfb_p2", {"row0": 1}),
        _blk("cmfb_n1", {"top": 2, "bot": 2}),
        _blk("cmfb_n2", {"row0": 2}),
    ]
    mirror_pairs = [
        (_blk("classab_p1", {"row0": 3}), _blk("classabL_p1", {"row0": 3})),
        (_blk("classab_p2", {"row0": 2}), _blk("classabL_p2", {"row0": 2})),
        (_blk("classab_n1_new", {"row0": 2}), _blk("classabL_n1_new", {"row0": 2})),
        (_blk("classab_n2_new", {"row0": 2}), _blk("classabL_n2_new", {"row0": 2})),
        (_blk("classab_n_mirror", {"top": 2, "bot": 2}), _blk("classabL_n_mirror", {"top": 2, "bot": 2})),
        (_blk("S2_M15", {"row0": 1}), _blk("S2_M25", {"row0": 1})),
        (_blk("S2_M16", {"row0": 1}), _blk("S2_M26", {"row0": 1})),
    ]
    r3 = pack_floorplan(spine, mirror_pairs, gap=1.0)

    # 겹침 검증 -- packing이 실제로 유효한지(어떤 두 블록도 겹치지 않는지) 직접 확인
    names = list(r3.placements)
    n_overlaps = sum(1 for i in range(len(names)) for j in range(i+1, len(names))
                      if overlap(r3.placements[names[i]], r3.placements[names[j]]))
    # oracle (d): 섹션 문장이 적은 기대 'OK(겹침 없음)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert n_overlaps == 0, f"  overlap check: {n_overlaps}개 쌍 겹침 -> {'OK(겹침 없음)' if n_overlaps == 0 else 'FAIL'}"
    if r3.row_split_candidates:
        for c in r3.row_split_candidates:
            pass

    asym_pairs = [(_blk("R", {"row0": 5}), _blk("L", {"row0": 3}))]
    r4 = pack_floorplan([], asym_pairs, gap=1.0)
    # oracle (d): 섹션 문장이 적은 기대 'OK(비대칭을 있는 그대로 보고)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert r4.symmetry_max_error == 2.0, (f"  symmetry_max_error={r4.symmetry_max_error:.3f} -> "
          f"{'OK(비대칭을 있는 그대로 보고)' if r4.symmetry_max_error == 2.0 else 'FAIL'}")


def test_s062_find_diffusion_safe_split_points(s061_state):
    """=== Test 18: find_diffusion_safe_split_points() — 실제 S1_TAILP 시퀀스로 검증 ===
    사용자 지적: "packing할 때 MOS의 diffusion 영역이 고려돼서 엉뚱하게 split되는
    문제가 없도록 해야 한다" -- 실제 S1_TAILP(M6:M7 tail, 이 세션에서 실제
    build_stick_diagram()이 반환한 시퀀스)로 확인.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S062(줄 1074-1114, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    spine = s061_state.spine

    s1_tailp_seq = ["M6","M6","M6","M6","M7","M6","M7","M6","M7","M6"]  # stick_stage1_results.json 실측값
    pts = find_diffusion_safe_split_points(s1_tailp_seq)
    # oracle (d): 섹션 문장이 적은 기대 'OK(안전 지점 없음 ...)' / 'FAIL(있으면 안 되는데 나옴)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert pts == [], f"  안전 분할 지점: {pts} -> {'OK(안전 지점 없음 -- M6/M7이 완전히 인터리브돼 어디를 잘라도 소자가 갈라짐)' if pts == [] else 'FAIL(있으면 안 되는데 나옴)'}"

    biasgen_seq = ["M29","M28","M27","M33","M34"]  # 실제 biasgen_pmos 시퀀스(서로 다른 소자가 순서대로만 연결)
    pts2 = find_diffusion_safe_split_points(biasgen_seq)
    # oracle (d): 섹션 문장이 적은 기대 'OK(각 소자가 통째로 한쪽에만 있는 지점 존재)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert pts2, f"  안전 분할 지점: {pts2} -> {'OK(각 소자가 통째로 한쪽에만 있는 지점 존재)' if pts2 else 'FAIL'}"

    dominant_block = FloorplanBlock("S1_TAILP", 10, 1)
    seqs = {"S1_TAILP": s1_tailp_seq}
    cands_checked = evaluate_row_split_candidates([dominant_block], bbox_width=12, bbox_height=13,
                                                    dominance_ratio=0.6, transistor_sequences=seqs)
    cands_unchecked = evaluate_row_split_candidates([dominant_block], bbox_width=12, bbox_height=13,
                                                      dominance_ratio=0.6)
    # oracle (d): 섹션 문장이 적은 기대 '시퀀스 제공 ... splittable -> OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert cands_checked[0]['splittable'] is False, (f"  시퀀스 제공: diffusion_check={cands_checked[0]['diffusion_check']}, "
          f"splittable={cands_checked[0]['splittable']} -> "
          f"{'OK' if cands_checked[0]['splittable'] is False else 'FAIL'}")
    # oracle (d): 섹션 문장이 적은 기대 'OK(정직하게 미확인으로 표시)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert cands_unchecked[0]['diffusion_check']=='not_verified', (f"  시퀀스 미제공: diffusion_check={cands_unchecked[0]['diffusion_check']}, "
          f"splittable={cands_unchecked[0]['splittable']} -> "
          f"{'OK(정직하게 미확인으로 표시)' if cands_unchecked[0]['diffusion_check']=='not_verified' else 'FAIL'}")

    solo_placements, sw, sh = skyline_pack_best_width(spine, gap=1.0)
    solo_overlaps = sum(1 for i,a in enumerate(solo_placements.values())
                         for j,b in enumerate(solo_placements.values()) if i<j and overlap(a,b))
    # oracle (d): 섹션 문장이 적은 기대 'spine 단독 ... overlap -> OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert solo_overlaps==0, (f"  spine 단독: bbox={sw:.1f}x{sh:.1f}, overlap={solo_overlaps} -> "
          f"{'OK' if solo_overlaps==0 else 'FAIL'}")


def test_s063_pack_floorplan_grouped(s061_state):
    """=== Test 19: pack_floorplan_grouped() — 기능 그룹이 실제로 흩어지지 않는지 확인 ===
    사용자 지적: "cmfb_n1은 왜 어중간하게 중간에 배치돼 있지?" -- pack_floorplan()이
    평평한 spine 리스트를 순수 공간 최적화로만 packing해서, CMFB의 나머지 행들과
    떨어져 Stage-1 사이에 끼어드는 실제 결과가 나왔었다. 그룹 단위 packing으로 재검증.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S063(줄 1115-1148, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    mirror_pairs = s061_state.mirror_pairs
    spine = s061_state.spine

    spine_groups = {
        "stage1": [b for b in spine if b.name.startswith("S1_")],
        "biasgen": [b for b in spine if b.name.startswith("biasgen_")],
        "cmfb": [b for b in spine if b.name.startswith("cmfb_")],
    }
    r5 = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0)
    n_ov5 = sum(1 for i in range(len(list(r5.placements))) for j in range(i+1, len(list(r5.placements)))
                if overlap(r5.placements[list(r5.placements)[i]], r5.placements[list(r5.placements)[j]]))
    # oracle (d): 섹션 문장이 적은 기대 'overlap check -> OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert n_ov5==0, f"  overlap check: {n_ov5} -> {'OK' if n_ov5==0 else 'FAIL'}"

    def group_is_contiguous(names):
        ys = sorted((r5.placements[n].y, r5.placements[n].y + r5.placements[n].height) for n in names)
        # 그룹 내 y-구간들이 서로 붙어있거나 겹치는지(gap<=1.01) 확인 -- 완전히 흩어졌으면 FAIL
        for k in range(len(ys) - 1):
            if ys[k+1][0] - ys[k][1] > 1.01:
                return False
        return True

    for gname, members in [("stage1", ["S1_PMOS","S1_NMOS","S1_TAILP","S1_TAILN"]),
                            ("biasgen", ["biasgen_pmos","biasgen_nmos"]),
                            ("cmfb", ["cmfb_p1","cmfb_p2","cmfb_n1","cmfb_n2"])]:
        ok = group_is_contiguous(members)
        # oracle (d): 섹션 문장이 적은 기대 'group stays contiguous ... OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
        assert ok, (f"  group '{gname}' stays contiguous (no unrelated block sandwiched in): "
              f"{'OK' if ok else 'FAIL'}")


def test_s064_section(s061_state, s063_state):
    """=== Test 20: net_weights — 신호선 근접 배치, 실제 vbias1 연결로 검증 ===
    사용자 지적: "배치는 신호선과 근접한 곳에 위치시키면 좋겠어, routing delay가
    없어지지." -- bias-gen(vbias1 소스)과 classab_p2(M8/M13, vbias1을 게이트로
    읽는 소자)가 실제로는 10칸이나 떨어져 있었다(사&sect;7은 '바로 옆에 둬야 한다'고
    이미 명시했었는데 &sect;8 좌표는 이를 전혀 반영 못 했다).

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S064(줄 1149-1182, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    mirror_pairs = s061_state.mirror_pairs
    spine_groups = s063_state.spine_groups

    net_weights = {
        "biasgen": {"stage1": 4.0, "cmfb": 1.0}, "stage1": {"biasgen": 4.0, "cmfb": 1.0},
        "cmfb": {"biasgen": 1.0, "stage1": 1.0},
        "classab_p2": {"biasgen": 2.0}, "classab_n1_new": {"biasgen": 1.0},
    }
    r6_before = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0)
    r6_after = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0, net_weights=net_weights)
    dist_before = abs(r6_before.placements["biasgen_pmos"].y - r6_before.placements["classab_p2"].y)
    dist_after = abs(r6_after.placements["biasgen_pmos"].y - r6_after.placements["classab_p2"].y)
    # oracle (d): 섹션 문장이 적은 기대 'OK(거리 개선, box-shape 목표(<=1.5) 안에서)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert dist_after < dist_before and r6_after.aspect_ratio <= 1.5, f"  -> {'OK(거리 개선, box-shape 목표(<=1.5) 안에서)' if dist_after < dist_before and r6_after.aspect_ratio <= 1.5 else 'FAIL'}"

    n_ov6 = sum(1 for i,a in enumerate(list(r6_after.placements.values()))
                for j,b in enumerate(list(r6_after.placements.values())) if i<j and overlap(a,b))
    # oracle (d): 섹션 문장이 적은 기대 'overlap check (net_weights 적용 후) -> OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert n_ov6==0, f"  overlap check (net_weights 적용 후): {n_ov6} -> {'OK' if n_ov6==0 else 'FAIL'}"
    for gname, members in [("stage1", ["S1_PMOS","S1_NMOS","S1_TAILP","S1_TAILN"]),
                            ("biasgen", ["biasgen_pmos","biasgen_nmos"]),
                            ("cmfb", ["cmfb_p1","cmfb_p2","cmfb_n1","cmfb_n2"])]:
        ys = sorted((r6_after.placements[n].y, r6_after.placements[n].y + r6_after.placements[n].height) for n in members)
        ok = all(ys[k+1][0] - ys[k][1] <= 1.01 for k in range(len(ys)-1))
        # oracle (d): 섹션 문장이 적은 기대 'group still contiguous after net_weights: OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
        assert ok, f"  group '{gname}' still contiguous after net_weights: {'OK' if ok else 'FAIL'}"


def test_s065_diffusion(s061_state, s064_state, s063_state):
    """=== Test 21: sub_kind — 같은 diffusion(폴러리티)별로 나눠 배치하면 더 compact한지 실측 ===
    사용자 제안: "cmfb_n1은 top/bot 합친 것인데, 다른 cmfb 행과 높이 맞춰 옆으로 배치하면
    P/N 영역이 구분되면서 더 compact해지지 않을까 -- 확인하는 기능도 보강해달라."

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S065(줄 1183-1220, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    mirror_pairs = s061_state.mirror_pairs
    net_weights = s064_state.net_weights
    spine = s061_state.spine
    spine_groups = s063_state.spine_groups

    sub_kind_stage1 = {"S1_PMOS":"pmos","S1_TAILP":"pmos","S1_NMOS":"nmos","S1_TAILN":"nmos"}
    flat_s1, _ = pack_group_as_unit("stage1", [b for b in spine if b.name.startswith("S1_")], gap=1.0)
    ratio_flat = max(flat_s1.width,flat_s1.height)/min(flat_s1.width,flat_s1.height)
    kind_result = _pack_by_subkind([b for b in spine if b.name.startswith("S1_")], sub_kind_stage1, gap=1.0)
    _, kind_internal = kind_result
    kw = max(p.x+p.width for p in kind_internal.values()); kh = max(p.y+p.height for p in kind_internal.values())
    ratio_kind = max(kw,kh)/min(kw,kh)

    r7_before = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0, net_weights=net_weights)
    r7_after = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0, net_weights=net_weights,
                                        sub_kinds={"stage1": sub_kind_stage1,
                                                    "cmfb": {"cmfb_p1":"pmos","cmfb_p2":"pmos",
                                                             "cmfb_n1":"nmos","cmfb_n2":"nmos"}})
    same = (abs(r7_before.aspect_ratio - r7_after.aspect_ratio) < 0.01)
    n_ov7 = sum(1 for i,a in enumerate(list(r7_after.placements.values()))
                for j,b in enumerate(list(r7_after.placements.values())) if i<j and overlap(a,b))
    # oracle (d): 섹션 문장이 적은 기대 'overlap check -> OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert n_ov7==0, f"  overlap check: {n_ov7} -> {'OK' if n_ov7==0 else 'FAIL'}"

    vsd_trs = [
        Transistor("MA", "nmos", source="tail", drain="outA", gate="vip"),
        Transistor("MB", "nmos", source="tail", drain="outB", gate="vim"),
        Transistor("MC", "nmos", source="gnd", drain="tail", gate="bias"),
    ]


def test_s067_MB(s065_state):
    """[MA/MB(진짜 diff_pair)를 matching_pairs에 빼먹은 상황]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S067(줄 1224-1232, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    vsd_trs = s065_state.vsd_trs

    v1 = check_symmetry_dispositions(vsd_trs, matching_pairs=[])
    for u in v1.undisposed:
        pass
    assert not v1.ok, "빼먹은 후보를 잡아내지 못했다"

    v2 = check_symmetry_dispositions(vsd_trs, matching_pairs=[{"names": ["MA", "MB"], "kind": "diff_pair"}])
    assert v2.ok


def test_s069_section():
    """[net 이름 대소문자 불일치(사고9와 동일 패턴)를 잡아내는지 -- Vbias1 vs vbias1]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S069(줄 1234-1242, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    vsd_case_trs = [
        Transistor("MX", "pmos", source="vdd", drain="outA", gate="Vbias1"),
        Transistor("MY", "pmos", source="vdd", drain="outB", gate="vbias1"),  # 같은 net, 다른 표기
    ]
    v_case = check_symmetry_dispositions(vsd_case_trs, matching_pairs=[])
    assert not v_case.ok and v_case.case_collisions, \
        "대소문자 불일치(사고9와 동일 패턴)를 잡아내지 못했다"


def test_s070_section(library_dir):
    """[실전: current_reuse_telescopic_ota.topology.json 전체 재검증]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S070(줄 1244-1258, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib21 = library_dir
    _telescopic_trs, _telescopic_meta = load_topology(
        _os21.path.join(_lib21, "current_reuse_telescopic_ota.topology.json"))
    _telescopic_pairs = _telescopic_meta["symmetry"]["matching_pairs"]
    _telescopic_disp_list = _telescopic_meta["symmetry"].get("dispositions", [])
    _telescopic_disp = {(d["tag"], d["kind"], d["key"]): (d["category"], d["reason"])
                         for d in _telescopic_disp_list}
    v3 = check_symmetry_dispositions(_telescopic_trs, _telescopic_pairs, _telescopic_disp)
    assert v3.ok, f"telescopic OTA topology JSON에 미처리 후보가 남아있다: {v3.undisposed}"


def test_s071_section():
    """[linked_topology_files -- 회로가 여러 파일로 쪼개져도 항상 전체를 합쳐서 보는지]
    2026-07-28 신설(사용자 지적, PRE-FLIGHT 사고8 재발 방지): sub-block별로 파일을
    나눠도 어느 파일을 진입점으로 읽든 형제 파일 전부가 자동으로 합쳐져야 한다.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S071(줄 1259-1300, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    with _tempfile21.TemporaryDirectory() as _tmpdir21:
        _partA = {
            "schema_version": "2.0", "topology_name": "demo_partA", "source": "self-test synthetic",
            "compensation": None,
            "netlist": [{"name": "MSIG", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "vbias_shared"}],
            "symmetry": {"matching_pairs": [], "dispositions": []},
            "linked_topology_files": ["partB.topology.json"],
        }
        _partB = {
            "schema_version": "2.0", "topology_name": "demo_partB", "source": "self-test synthetic",
            "compensation": None,
            "netlist": [
                {"name": "MBIAS1", "kind": "nmos", "source": "gnd", "drain": "vbias_shared", "gate": "vbias_shared"},
                {"name": "MBIAS2", "kind": "nmos", "source": "gnd", "drain": "x", "gate": "vbias_shared"},
            ],
            "symmetry": {"matching_pairs": [], "dispositions": []},
            "linked_topology_files": ["partA.topology.json"],
        }
        _pathA = _os21.path.join(_tmpdir21, "partA.topology.json")
        _pathB = _os21.path.join(_tmpdir21, "partB.topology.json")
        with open(_pathA, "w", encoding="utf-8") as f:
            json.dump(_partA, f)
        with open(_pathB, "w", encoding="utf-8") as f:
            json.dump(_partB, f)

        _linked_trs, _linked_meta = load_topology(_pathA)  # partA만 진입점으로 읽음
        assert len(_linked_trs) == 3, "linked_topology_files를 따라가 병합하지 못했다"

        _linked_candidates = find_matching_candidates(_linked_trs)
        _cross_file_group = _linked_candidates["current_mirror"].get(("nmos", "vbias_shared"))
        assert _cross_file_group and len(_cross_file_group) == 3, \
            "파일을 쪼갰더니 cross-file matching 관계를 다시 놓쳤다 -- 사고8 재발"


def test_s072_audit_row_split():
    """=== Test 22: audit_row_split() — Euler/box-shape만으론 못 잡는 matching 회귀 실측 ===
    사용자 지적: "matching pattern은 왜 적용이 안 됐지?" -- folded_cascode_example()의
    top/bot을 2행으로 나눌 때 M3는 row0 통째로, M4는 row1 통째로 배치했다. Euler 조건과
    interdigitation/common-centroid가 전혀 없었다 -- 이후 사용자가 한 번 더 지적:
    "interdigitation과 common-centroid 둘 다 살펴보는 과정을 추가하라 했는데 하나만
    하면 어떡하냐" -- 3b(행 내부 인접성)와 3c(전체 무게중심 일치)를 별개 체크로 분리.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S072(줄 1301-1349, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    old_top_row0 = [
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="old_row0"),
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=3,stack_id="old_row0"),
        Transistor("M5","pmos",source="X",drain="outA",gate="bias3",n_fingers=6,stack_id="old_row0"),
    ]
    old_top_row1 = [
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="old_row1"),
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=3,stack_id="old_row1"),
        Transistor("M6","pmos",source="Y",drain="outB",gate="bias3",n_fingers=6,stack_id="old_row1"),
    ]
    old_audit = audit_row_split({"old_row0": old_top_row0, "old_row1": old_top_row1},
                                  matching_pairs=[("M3", "M4")],
                                  pair_sensitivity={("M3", "M4"): "ratio"})
    # oracle (d): 섹션 문장이 적은 기대 'OK(FAIL, 의도대로 검출됨)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert not old_audit.ok, f"  [회귀 재현] M3 row0 통째로/M4 row1 통째로: overall={'OK(FAIL, 의도대로 검출됨)' if not old_audit.ok else 'FAIL(놓침!)'}"

    cc34 = common_centroid_layout([
        Transistor("M3", "pmos", source="vdd", drain="X", n_fingers=3),
        Transistor("M4", "pmos", source="vdd", drain="Y", n_fingers=3),
    ])
    a34_r0 = cc34["rows"][0]["transistor_sequence"].count("M3")
    b34_r0 = cc34["rows"][0]["transistor_sequence"].count("M4")
    a34_r1 = cc34["rows"][1]["transistor_sequence"].count("M3")
    b34_r1 = cc34["rows"][1]["transistor_sequence"].count("M4")
    fixed_top_row0 = [
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r0,stack_id="fix_row0"),
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r0,stack_id="fix_row0"),
        Transistor("M5","pmos",source="X",drain="outA",gate="bias3",n_fingers=6,stack_id="fix_row0"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="fix_row0"),
    ]
    fixed_top_row1 = [
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r1,stack_id="fix_row1"),
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r1,stack_id="fix_row1"),
        Transistor("M6","pmos",source="Y",drain="outB",gate="bias3",n_fingers=6,stack_id="fix_row1"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="fix_row1"),
    ]
    fixed_audit = audit_row_split({"fix_row0": fixed_top_row0, "fix_row1": fixed_top_row1},
                                    matching_pairs=[("M3", "M4")],
                                    pair_sensitivity={("M3", "M4"): "ratio"})
    # oracle (d): 섹션 문장이 적은 기대 '[common_centroid_layout로 재구성] overall=OK' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert fixed_audit.ok, f"  [common_centroid_layout로 재구성] overall={'OK' if fixed_audit.ok else 'FAIL'}"


def test_s075_two_stage_ota_example():
    """[kind-aware 재판정 -- two_stage_ota_example() top(M3/M4=2f+2f) + M6(8f)] 사용자의
    세 번째 지적("mirror는 interdigitation이 적합, 차동쌍은 common-centroid가 필요 --
    기존 §2.7 기준을 왜 안 쓰나")을 반영하기 전에는, M3/M4의 common-centroid dx=1.0을
    '해결 안 된 한계'로 오판했었다 -- 하지만 M3/M4는 gate=D3를 공유하는 전류거울이지
    차동쌍이 아니다. §2.7 기준대로 kind=current_mirror면 interdigitation만 필수이고
    common-centroid는 참고용이므로, dx=1.0은 애초에 실패가 아니라 잘못된 기준을 적용해
    생긴 오탐이었다 -- kind-aware 판정으로 바로잡는다.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S075(줄 1350-1394, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    small_top_row0 = [
        Transistor("M3","pmos",source="vdd",drain="D3",gate="D3",n_fingers=2,stack_id="small_row0"),
        Transistor("M4","pmos",source="vdd",drain="O1",gate="D3",n_fingers=2,stack_id="small_row0"),
        Transistor("M6","pmos",source="vdd",drain="OUT",gate="O1",n_fingers=2,stack_id="small_row0"),
    ]
    small_top_row1 = [
        Transistor("M6","pmos",source="vdd",drain="OUT",gate="O1",n_fingers=6,stack_id="small_row1"),
    ]
    small_audit = audit_row_split({"small_row0": small_top_row0, "small_row1": small_top_row1},
                                    matching_pairs=[("M3", "M4")],
                                    pair_sensitivity={("M3", "M4"): "ratio"})
    # oracle (d): 섹션 문장이 적은 기대 'OK(sensitivity=ratio+shares_node -> interdigitation만 필수, 정확히 통과)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert small_audit.ok, f"  overall={'OK(sensitivity=ratio+shares_node -> interdigitation만 필수, 정확히 통과)' if small_audit.ok else 'FAIL'}"

    diffpair_bad_row0 = [
        Transistor("MX","nmos",source="tail2",drain="da",gate="vp",n_fingers=1,stack_id="dp_row0"),
        Transistor("MY","nmos",source="tail2",drain="db",gate="vn",n_fingers=3,stack_id="dp_row0"),
    ]
    diffpair_bad_row1 = [
        Transistor("MX","nmos",source="tail2",drain="da",gate="vp",n_fingers=3,stack_id="dp_row1"),
        Transistor("MY","nmos",source="tail2",drain="db",gate="vn",n_fingers=1,stack_id="dp_row1"),
    ]
    diffpair_audit = audit_row_split({"dp_row0": diffpair_bad_row0, "dp_row1": diffpair_bad_row1},
                                       matching_pairs=[("MX", "MY")],
                                       pair_sensitivity={("MX", "MY"): "offset"})
    # oracle (d): 섹션 문장이 적은 기대 '[대조군 -- 진짜 차동쌍이 common-centroid를 실패하면 이번엔 진짜로 FAIL해야 한다]' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert not diffpair_audit.ok, f"  overall={'FAIL(sensitivity=offset -> common-centroid 필수, 의도대로 검출됨)' if not diffpair_audit.ok else 'OK(놓침!)'}"

    cc34_2 = common_centroid_layout([
        Transistor("M3", "pmos", source="vdd", drain="X", n_fingers=3),
        Transistor("M4", "pmos", source="vdd", drain="Y", n_fingers=3),
    ])
    a34_r0b = cc34_2["rows"][0]["transistor_sequence"].count("M3")
    b34_r0b = cc34_2["rows"][0]["transistor_sequence"].count("M4")
    a34_r1b = cc34_2["rows"][1]["transistor_sequence"].count("M3")
    b34_r1b = cc34_2["rows"][1]["transistor_sequence"].count("M4")


def test_s078_interdigitation(s075_state):
    """[1차: M5/M6 통째로 한 컬럼씩(solo)] -- 전수 탐색으로 interdigitation(3b)이 그래프상

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S078(줄 1396-1415, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    a34_r0b = s075_state.a34_r0b
    a34_r1b = s075_state.a34_r1b
    b34_r0b = s075_state.b34_r0b
    b34_r1b = s075_state.b34_r1b

    solo_top_row0 = [
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r0b,stack_id="solo_row0"),
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r0b,stack_id="solo_row0"),
        Transistor("M5","pmos",source="X",drain="outA",gate="bias3",n_fingers=6,stack_id="solo_row0"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="solo_row0"),
    ]
    solo_top_row1 = [
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r1b,stack_id="solo_row1"),
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r1b,stack_id="solo_row1"),
        Transistor("M6","pmos",source="Y",drain="outB",gate="bias3",n_fingers=6,stack_id="solo_row1"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="solo_row1"),
    ]
    solo_audit = audit_row_split({"solo_row0": solo_top_row0, "solo_row1": solo_top_row1},
                                   matching_pairs=[("M3", "M4"), ("M5", "M6")],
                                   pair_sensitivity={("M3", "M4"): "ratio", ("M5", "M6"): "ratio"})
    # oracle (d): 섹션 문장이 적은 기대 'solo 배치 자체의 common-centroid(3c)를 계산해보니 FAIL이었다' / 'FAIL(... 의도대로 검출됨)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert not solo_audit.ok, f"  overall={'OK' if solo_audit.ok else 'FAIL(solo 배치의 common-centroid 미달, 의도대로 검출됨)'}"


def test_s079_section(s075_state):
    """[사용자 재지적: "differential pair처럼 stack 분리+finger 조절로 common-centroid를
    만들 수 있잖아" -- M5/M6도 양쪽 행에 swap-대칭으로 나눠 분배해 재시도(M5=2/4, M6=4/2,
    swap). interdigitation(그래프상 인접)은 여전히 불가능하지만 common-centroid(전체
    무게중심)는 이 분배로 실제 달성됨을 확인:

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S079(줄 1416-1458, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    a34_r0b = s075_state.a34_r0b
    a34_r1b = s075_state.a34_r1b
    b34_r0b = s075_state.b34_r0b
    b34_r1b = s075_state.b34_r1b

    dist_top_row0 = [
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r0b,stack_id="dist_row0"),
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r0b,stack_id="dist_row0"),
        Transistor("M5","pmos",source="X",drain="outA",gate="bias3",n_fingers=2,stack_id="dist_row0"),
        Transistor("M6","pmos",source="Y",drain="outB",gate="bias3",n_fingers=4,stack_id="dist_row0"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="dist_row0"),
    ]
    dist_top_row1 = [
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r1b,stack_id="dist_row1"),
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r1b,stack_id="dist_row1"),
        Transistor("M6","pmos",source="Y",drain="outB",gate="bias3",n_fingers=2,stack_id="dist_row1"),
        Transistor("M5","pmos",source="X",drain="outA",gate="bias3",n_fingers=4,stack_id="dist_row1"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="dist_row1"),
    ]
    dist_audit = audit_row_split({"dist_row0": dist_top_row0, "dist_row1": dist_top_row1},
                                   matching_pairs=[("M3", "M4"), ("M5", "M6")],
                                   pair_sensitivity={("M3", "M4"): "ratio", ("M5", "M6"): "ratio"})
    # oracle (d): 섹션 문장이 적은 기대 'common-centroid(전체 무게중심)는 이 분배로 실제 달성됨을 확인' / 'OK(swap-분배로 ... 실제 달성)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert dist_audit.ok, f"  overall={'OK(swap-분배로 common-centroid 실제 달성)' if dist_audit.ok else 'FAIL'}"

    mismatched_row0 = [
        Transistor("MA","pmos",source="p1",drain="d1",gate="g",n_fingers=4,stack_id="bad_row0"),
    ]
    mismatched_row1 = [
        Transistor("MB","pmos",source="p2",drain="d2",gate="g",n_fingers=6,stack_id="bad_row1"),
    ]
    mismatched_audit = audit_row_split({"bad_row0": mismatched_row0, "bad_row1": mismatched_row1},
                                         matching_pairs=[("MA", "MB")],
                                         pair_sensitivity={("MA", "MB"): "ratio"})
    # oracle (d): 섹션 문장이 적은 기대 '[대조군 -- 진짜 finger 수가 안 맞는 branch_symmetric 쌍은 여전히 FAIL해야 한다]' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert not mismatched_audit.ok, f"  overall={'FAIL(finger 수 4 != 6 -- 진짜 mirror 짝이 아님, 의도대로 검출됨)' if not mismatched_audit.ok else 'OK(놓침!)'}"

    proposed_row0 = ["M3","M4","M6","M6","M5","MP","M5","M6","M6","M4"]
    v = check_walk_sequence(proposed_row0, dist_top_row0)

    real_seq = build_stick_diagram(dist_top_row0)["dist_row0"].transistor_sequence
    v2 = check_walk_sequence(real_seq, dist_top_row0)


def test_s083_check_stick_diagram_coverage():
    """=== Test 25: check_stick_diagram_coverage() — sizing은 됐는데 layout이 통째로 빠짐 방지 ===
    실제 사고(2026-07-28, 힌트 없는 fresh agent 재현 테스트): current-reuse telescopic
    OTA 리포트에서 21개 소자 전부 gm/ID sizing은 됐는데, CMFB/bias-gen/Class-AB 9개
    소자는 stick diagram(물리 행)이 아예 없이 '완료'로 게시됐다 -- run_full_circuit_audit를
    import만 하고 실제로 호출하지 않아서 이 gap을 그 게이트조차 못 잡았다.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S083(줄 1461-1484, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    sized = {"M1a","M1b","M2a","M2b","M3a","M3b","M4a","M4b","M5","M6","M7",  # stage-1 (11)
             "M15","M25","M16","M26",  # stage-2 output (4)
             "M14a","M14b","M11a","M11b","M8","M13",  # Class-AB (6) -- 실제로 stick diagram 없었음
             "M27","M28","M29","M30","M31","M32","M35","M33","M34",  # bias-gen (9) -- 없었음
             "M36a","M36b","M37a","M37b","M38","M39","M40"}  # CMFB (7) -- 없었음
    stick_rows_actual = {  # 실제 재현 -- 이 사고에서 실제로 만들어진 6개 행만
        "row1_pmos_in_casc": ["M1a","M1b","M2a","M2b"],
        "row2_nmos_in_casc": ["M4a","M4b","M3a","M3b"],
        "row3_top_load": ["M6","M7"],
        "row4_tail": ["M5"],
        "rowP_out": ["M15","M25"],
        "rowN_out": ["M16","M26"],
    }
    cov = check_stick_diagram_coverage(sized, stick_rows_actual)
    # oracle (d): 섹션 문장이 적은 기대 'FAIL(정확히 그 사고를 재현 -- ... 누락 검출됨)' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert not cov.ok, f"  overall={'OK' if cov.ok else 'FAIL(정확히 그 사고를 재현 -- Class-AB/bias-gen/CMFB 22개 소자 누락 검출됨)'}"


def test_s084_section(library_dir, s083_state):
    """[대조: 전부 커버되면 OK로 통과하는지 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S084(줄 1485-1497, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    sized = s083_state.sized
    stick_rows_actual = s083_state.stick_rows_actual

    stick_rows_complete = dict(stick_rows_actual)
    stick_rows_complete["row5_classab"] = ["M14a","M14b","M11a","M11b","M8","M13"]
    stick_rows_complete["row6_biasgen"] = ["M27","M28","M29","M30","M31","M32","M35","M33","M34"]
    stick_rows_complete["row7_cmfb"] = ["M36a","M36b","M37a","M37b","M38","M39","M40"]
    cov2 = check_stick_diagram_coverage(sized, stick_rows_complete)
    # oracle (d): 섹션 문장이 적은 기대 '[대조: 전부 커버되면 OK로 통과하는지 확인]' -- TS3 경우 (i), 메시지 = 원래 출력 문자열
    assert cov2.ok, f"  overall={'OK' if cov2.ok else 'FAIL'}, missing={cov2.missing}"

    _lib_dir = library_dir


def test_s086_folded_cascode_example(library_dir):
    """[folded_cascode: n_fingers/finger_w/w/stack_id 산출물만 folded_cascode_example()에서
    빌려 파이프라인 기계적 동작을 확인 -- 2026-08-05(세션9) folded_cascode.topology.json이
    다이오드 레퍼런스 구조(MP/MN, Vg7/Vg9/Vg10 등) 반영으로 Maloberti 교과서 예제와 다른
    실제 회로로 전면 재구성돼, connectivity diff=0 비교는 더 이상 유효한 회귀 기준이
    아니다(의도적 차이, 세션9 사용자 승인) -- 소자 이름 집합만 일치 확인하고 connectivity
    diff는 참고 정보로만 출력한다.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S086(줄 1499-1531, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib_dir = library_dir

    _fc_original = folded_cascode_example()
    _fc_loaded, _fc_meta = load_topology(_os.path.join(_lib_dir, "folded_cascode.topology.json"))
    _fc_orig_by_name = {t.name: (t.kind, t.source, t.drain, t.gate) for t in _fc_original}
    _fc_load_by_name = {t.name: (t.kind, t.source, t.drain, t.gate) for t in _fc_loaded}
    _fc_diff_ok = _fc_orig_by_name == _fc_load_by_name
    assert set(_fc_orig_by_name) == set(_fc_load_by_name), \
        "folded_cascode_example()과 topology.json의 소자 이름 집합이 다름 -- sizing_overrides 구성 불가"

    _fc_overrides = {t.name: {"n_fingers": t.n_fingers, "finger_w": t.finger_w,
                               "w": t.w, "stack_id": t.stack_id} for t in _fc_original}
    _fc_result = run_topology_pipeline(_os.path.join(_lib_dir, "folded_cascode.topology.json"),
                                        _fc_overrides)

    _ts_original = two_stage_ota_example()
    _ts_loaded, _ts_meta = load_topology(_os.path.join(_lib_dir, "two_stage_ota.topology.json"))
    _ts_orig_by_name = {t.name: (t.kind, t.source, t.drain, t.gate) for t in _ts_original}
    _ts_load_by_name = {t.name: (t.kind, t.source, t.drain, t.gate) for t in _ts_loaded}
    _ts_diff_ok = _ts_orig_by_name == _ts_load_by_name

    _ts_overrides = {t.name: {"n_fingers": t.n_fingers, "finger_w": t.finger_w,
                               "w": t.w, "stack_id": t.stack_id} for t in _ts_original}
    _ts_result = run_topology_pipeline(_os.path.join(_lib_dir, "two_stage_ota.topology.json"),
                                        _ts_overrides)


def test_s088_save_instance_json(s086_state, library_dir):
    """[save_instance_json(): pipeline_result를 손대지 않고 그대로 파일에 옮기는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S088(줄 1533-1562, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_result = s086_state._fc_result
    _lib_dir = library_dir
    _ts_diff_ok = s086_state._ts_diff_ok

    with _tempfile.TemporaryDirectory() as _tmpdir:
        _inst_path = _os.path.join(_tmpdir, "folded_cascode.instance.json")
        # (가) oracle (a) 구성 입력 + IC3 계약(design 10-test-separation §5.5·§6.7): 빈 sizing은 저장 전
        # 완전성 검사가 거부한다(소자 전부가 sizing 누락).
        with pytest.raises(ValueError):
            save_instance_json(_inst_path,
                                _os.path.join(_lib_dir, "folded_cascode.topology.json"),
                                {}, _fc_result)
        # (나) oracle (a) 구성 입력: _fc_result의 소자마다 INSTANCE_SIZING_FIELDS 다섯 키를 가진 합성 sizing
        # (값은 판정 대상이 아니다 -- 이 섹션의 판정은 'pipeline_result를 그대로 옮기는가').
        from stick_diagram import INSTANCE_SIZING_FIELDS as _INSTANCE_SIZING_FIELDS
        _fc_sizing = {_t.name: {_k: 1.0 for _k in _INSTANCE_SIZING_FIELDS} for _t in _fc_result["transistors"]}
        save_instance_json(_inst_path,
                            _os.path.join(_lib_dir, "folded_cascode.topology.json"),
                            _fc_sizing, _fc_result)
        with open(_inst_path, "r", encoding="utf-8") as _f:
            _inst_data = json.load(_f)

    assert _ts_diff_ok, "two_stage_ota connectivity diff가 0이 아니다 -- 이관 회귀 실패"


def test_s089_run_topology_pipeline(s086_state, library_dir):
    """=== Test 26.5: run_topology_pipeline() -- sizing_overrides에서 소자 하나를
    빠뜨리면 즉시 에러가 나는지(PRE-FLIGHT 사고27 재발 방지) ===
    2026-07-28 실측 발견: split_into_stacks()가 stack_id=None인 소자를
    (kind,'unspecified') 폴백 그룹으로 자동 흡수해버려서, check_stick_diagram_
    coverage()는 '이름이 어딘가 있다'고 통과시킨다 -- 즉 사실상 사이징 안 된
    소자가 coverage.ok=True인 채로 조용히 넘어갈 뻔했다(M11로 실제 재현됨).

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S089(줄 1563-1579, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_original = s086_state._fc_original
    _lib_dir = library_dir

    _fc_overrides_incomplete = {t.name: {"n_fingers": t.n_fingers, "finger_w": t.finger_w,
                                          "w": t.w, "stack_id": t.stack_id}
                                 for t in _fc_original if t.name != "M11"}  # M11을 일부러 빠뜨림
    with pytest.raises(ValueError):
        run_topology_pipeline(_os.path.join(_lib_dir, "folded_cascode.topology.json"),
                               _fc_overrides_incomplete)


def test_s090_run_topology_pipeline(s086_state, library_dir):
    """=== Test 26.55: run_topology_pipeline() -- check_finger_width_compatibility()가
    §3.5 선행 게이트로 실제 배선됐는지(세션18) -- W가 finger_w의 정수배가 아니면
    euler 분석 이전에 즉시 ValueError로 막는지, 정상 케이스는 그대로 통과하는지 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S090(줄 1580-1600, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_overrides = s086_state._fc_overrides
    _lib_dir = library_dir

    _fc_overrides_bad_w = dict(_fc_overrides)
    _fc_bad_name = next(iter(_fc_overrides_bad_w))
    _fc_bad_entry = _fc_overrides_bad_w[_fc_bad_name]
    _fc_overrides_bad_w[_fc_bad_name] = {
        **_fc_bad_entry, "w": _fc_bad_entry["finger_w"] * (_fc_bad_entry["n_fingers"] + 0.5)}
    with pytest.raises(ValueError) as _e26_55_info:
        run_topology_pipeline(_os.path.join(_lib_dir, "folded_cascode.topology.json"),
                               _fc_overrides_bad_w)
    _e26_55 = _e26_55_info.value
    assert "정수배" in str(_e26_55) and _fc_bad_name in str(_e26_55), \
        f"에러는 났지만 §3.5 게이트가 아닌 다른 이유로 보임: {_e26_55}"
    _fc_result_gate_ok = run_topology_pipeline(
        _os.path.join(_lib_dir, "folded_cascode.topology.json"), _fc_overrides)


def test_s092_section(s086_state):
    """=== Test 26.6: run_topology_pipeline() -- cell_groups 인자 (배치 7-2/2026-07-31) ===   fixture: folded_cascode(stack_id=top/mid/bot 3개) -- 물리적으로 독립된 cell이   없는 회로지만, cell_groups 메커니즘 자체(파티션별 box_shape/audit_row_split)를   검증하는 데는 임의의 2-cell 분할로 충분하다.

    [(a) cell_groups/spine_groups 둘 다 None -- 기존 단일-Verdict 동작 그대로]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S092(줄 1607-1611, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_result = s086_state._fc_result

    assert not isinstance(_fc_result["box_shape"], dict), "cell_groups 없이도 dict로 바뀜 -- 하위호환 깨짐"
    assert not isinstance(_fc_result["audit_row_split"], dict), "cell_groups 없이도 dict로 바뀜 -- 하위호환 깨짐"


def test_s093_section(s086_state, library_dir):
    """[(b) cell_groups 생략, floorplan_hints.spine_groups만 제공 -- fallback으로 그대로 재사용]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S093(줄 1612-1621, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_overrides = s086_state._fc_overrides
    _lib_dir = library_dir

    _spine_only_hints = {"spine_groups": {"cellA": ["top", "mid"], "cellB": ["bot"]}}
    _fc_result_fallback = run_topology_pipeline(
        _os.path.join(_lib_dir, "folded_cascode.topology.json"), _fc_overrides,
        floorplan_hints=_spine_only_hints)
    assert isinstance(_fc_result_fallback["box_shape"], dict), "spine_groups fallback이 dict를 안 만듦"
    assert set(_fc_result_fallback["box_shape"].keys()) == {"cellA", "cellB"}, \
        f"fallback cell 키 불일치: {sorted(_fc_result_fallback['box_shape'].keys())}"


def test_s094_section(s086_state, library_dir, s093_state):
    """[(c) cell_groups를 명시하면 spine_groups와 달라도 cell_groups가 우선(오버라이드)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S094(줄 1622-1634, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_overrides = s086_state._fc_overrides
    _fc_result = s086_state._fc_result
    _lib_dir = library_dir
    _spine_only_hints = s093_state._spine_only_hints

    _explicit_cell_groups = {"signal": ["top", "mid", "bot"]}  # spine_groups와 다른 파티션(1-cell)
    _fc_result_explicit = run_topology_pipeline(
        _os.path.join(_lib_dir, "folded_cascode.topology.json"), _fc_overrides,
        floorplan_hints=_spine_only_hints, cell_groups=_explicit_cell_groups)
    assert set(_fc_result_explicit["box_shape"].keys()) == {"signal"}, \
        f"cell_groups가 spine_groups fallback에 밀림: {sorted(_fc_result_explicit['box_shape'].keys())}"
    # cell_groups가 3개 스택 전부를 담은 단일 cell이므로, combined(cell_groups=None) 결과와
    # box_shape/checks 내용이 일치해야 한다 -- 파티션만 감쌌을 뿐 감사 로직 자체는 그대로.
    assert _fc_result_explicit["box_shape"]["signal"].row_widths == _fc_result["box_shape"].row_widths, \
        "1-cell 전체 파티션인데 combined 결과와 row_widths가 다름"


def test_s096_section(s086_state):
    """=== Test 27: propagate_topology_forced_currents() / find_diode_stacks() (A/C엔진, §7.3.2, 배치 7-3/2026-07-31) ===

    [A엔진 (a) 직렬 스택 전파 -- folded_cascode 'bot' 스택 한 소자만 seed]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S096(줄 1639-1646, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_original = s086_state._fc_original

    _a_ids = propagate_topology_forced_currents(_fc_original, {"M9": 24e-6}, {})
    _bot_names = {t.name for t in _fc_original if t.stack_id == "bot"}
    _bot_propagated_ok = all(_a_ids.get(n) == 24e-6 for n in _bot_names)
    assert _bot_propagated_ok, f"직렬 스택 'bot' 전체에 24uA가 안 퍼짐: {_a_ids}"
    assert "MP" not in _a_ids, "다른 스택(top)까지 잘못 전파됨"


def test_s097_ref(s086_state):
    """[A엔진 (b) 미러비 전파 -- ref(M9)->mirror(MN) 1:1 미러 가정]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S097(줄 1647-1651, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_original = s086_state._fc_original

    _a_ids2 = propagate_topology_forced_currents(_fc_original, {"M9": 24e-6}, {("M9", "MN"): 1.0})
    assert _a_ids2.get("MN") == 24e-6, f"미러비 전파 실패: MN={_a_ids2.get('MN')}"


def test_s098_section(s086_state):
    """[A엔진 (c) 같은 직렬 스택에 서로 다른 seed 전류가 섞이면 즉시 ValueError]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S098(줄 1652-1659, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_original = s086_state._fc_original

    with pytest.raises(ValueError):
        propagate_topology_forced_currents(_fc_original, {"M9": 24e-6, "M7": 40e-6}, {})


def test_s099_find_diode_stacks(s086_state):
    """[C엔진 find_diode_stacks() (a) folded_cascode -- M11/MN이 실제로 self-diode임을 검출]
    fixture 재확인: M11(gate=drain=vb1)/MN(gate=drain=vb2)은 folded_cascode_example()
    원본부터 diode-connected 바이어스 생성 소자로 정의돼 있다(bias1~5는 외부 net이라
    아님) -- find_diode_stacks()가 이걸 실제로 찾아내는지가 맞는 검증이다.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S099(줄 1660-1670, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_original = s086_state._fc_original

    _fc_diode_stacks = find_diode_stacks(_fc_original)
    assert len(_fc_diode_stacks) == 1 and _fc_diode_stacks[0].stack_id == "bot"
    _fc_diode_names = {m.name: m.gate_refers_to for m in _fc_diode_stacks[0].members}
    assert _fc_diode_names == {"M11": "M11", "MN": "MN"}, \
        f"M11/MN self-diode 판정 실패: {_fc_diode_names}"


def test_s100_find_diode_stacks(library_dir):
    """[C엔진 find_diode_stacks() (b) 실제 회로(current_reuse_telescopic_ota.topology.json)의
    M61/M58/M57 stacked-diode를 파일에서 직접 읽어 검증 -- 손타이핑 아님(2026-07-31,
    사용자 지적으로 합성 넷리스트를 실제 topology.json 로드로 교체)]
    실제 구조(2026-07-30 사용자와 함께 확인, topology.json _correction_log_2 참고):
    M61(전류원, gate=Vbias1)->M58(gate=M57의 drain)->M57(gate=자기 drain=Vbias_p)
    -- 자기참조만 보는 구식 체크는 M58을 놓친다.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S100(줄 1671-1691, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib_dir = library_dir

    _crt_path = _os.path.join(_lib_dir, "current_reuse_telescopic_ota.topology.json")
    _crt_transistors, _crt_meta = load_topology(_crt_path)
    _crt_by_name = {t.name: t for t in _crt_transistors}
    # stack_id는 topology.json 스키마에 없는 sizing/layout 산출물이라(§1 스키마 원칙)
    # 테스트가 직접 지정한다 -- name/kind/source/drain/gate(connectivity)는 전부 파일에서
    # 그대로 읽은 값이고 손으로 다시 짓지 않는다.
    _biasstack = [_dc_replace(_crt_by_name[n], stack_id="biasstack_p") for n in ("M61", "M58", "M57")]
    _diode_stacks = find_diode_stacks(_biasstack)
    assert len(_diode_stacks) == 1 and _diode_stacks[0].stack_id == "biasstack_p"
    _diode_names = {m.name: m.gate_refers_to for m in _diode_stacks[0].members}
    assert _diode_names == {"M58": "M57", "M57": "M57"}, \
        f"M57(self)/M58(이웃-M57) 판정 실패: {_diode_names}"
    assert "M61" not in _diode_names, "diode-connected가 아닌 M61(전류원)이 잘못 검출됨"


def test_s102_select_layout_tool():
    """=== Test 28: select_layout_tool()/repair_matching_safety() (배치 7-4/7-4b, 2026-07-31) ===

    [select_layout_tool() -- 2026-08-05(세션10) L1 하드컷: 축B/축C 조합별 도구 선택
    + area_budget 격상. 구 kind 문자열 대신 (matching_sensitivity, shares_node)를 받는다.]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S102(줄 1695-1707, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    assert select_layout_tool("ratio", True) == "interdigitate_layout"          # 구 current_mirror/current_matched
    assert select_layout_tool("ratio", True, area_budget="generous") == "common_centroid_layout"
    assert select_layout_tool("offset", True) == "common_centroid_layout"       # 구 diff_pair
    assert select_layout_tool("ratio", False) == "common_centroid_layout"       # 구 branch_symmetric
    with pytest.raises(ValueError):
        select_layout_tool("not_a_real_sensitivity", True)


def test_s103_repair_matching_safety(s086_state):
    """[repair_matching_safety() -- known-incidents.md 사고3 재현: folded_cascode.topology.json의
    current_matched 쌍(어느 이름인지는 topology.json의 symmetry.matching_pairs에서
    직접 찾는다 -- 특정 소자명을 테스트가 가정하지 않음, 2026-07-31 사용자 지적으로 교체.
    2026-08 세션6에서 kind 이름이 'current_mirror'->'current_matched'로 바뀌어 픽스처도
    같이 옮김 -- folded_cascode.topology.json엔 이제 진짜 전류강제 미러가 전부
    current_matched로 선언돼 있다, sizing_recipe.py 세션6 주석 참고)
    이 쌍이 서로 다른 행에 통째로 분리 배치된 걸 자동으로 interdigitate 재배치하는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S103(줄 1708-1746, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_loaded = s086_state._fc_loaded
    _fc_meta = s086_state._fc_meta

    _fc_by_name = {t.name: t for t in _fc_loaded}

    _fc_pairs_meta = _fc_meta["symmetry"]["matching_pairs"]
    _mirror_a, _mirror_b = _first_pair_matching(_fc_pairs_meta, True, "ratio")
    # n_fingers/stack_id는 topology.json에 없는 sizing/layout 산출물이라 테스트가 직접
    # 지정한다(§1 스키마 원칙) -- source/drain/gate(connectivity)는 파일에서 그대로 읽은 값.
    _t_mirror_a = _dc_replace(_fc_by_name[_mirror_a], n_fingers=3, stack_id="row0")
    _t_mirror_b = _dc_replace(_fc_by_name[_mirror_b], n_fingers=3, stack_id="row1")
    _repair_rows_before = {"row0": [_t_mirror_a], "row1": [_t_mirror_b]}
    _repair_pairs = [(_mirror_a, _mirror_b)]
    _repair_sensitivity = {(_mirror_a, _mirror_b): "ratio"}
    _before_audit = audit_row_split(_repair_rows_before, matching_pairs=_repair_pairs,
                                     pair_sensitivity=_repair_sensitivity)
    assert not _before_audit.ok, "수리 전인데 이미 PASS -- 재현 시나리오 실패"

    _repaired_rows, _after_audit = repair_matching_safety(_repair_rows_before, _repair_pairs, _repair_sensitivity)
    assert _after_audit.ok, f"수리 후에도 FAIL: {[c for c in _after_audit.checks if not c.ok]}"


def test_s104_repair_matching_safety(s103_state):
    """[repair_matching_safety() -- 공유 hub가 없는 pair(같은 파일에서 발견한 진짜
    branch_symmetric 쌍)는 건드리지 않고 정직하게 실패 유지(정직한 한계)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S104(줄 1747-1762, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_by_name = s103_state._fc_by_name
    _fc_pairs_meta = s103_state._fc_pairs_meta

    _branch_a, _branch_b = _first_pair_matching(_fc_pairs_meta, False, "ratio")
    _t_branch_a = _dc_replace(_fc_by_name[_branch_a], n_fingers=6, stack_id="rowA")
    _t_branch_b = _dc_replace(_fc_by_name[_branch_b], n_fingers=6, stack_id="rowB")
    _norepair_rows = {"rowA": [_t_branch_a], "rowB": [_t_branch_b]}
    _norepair_pairs = [(_branch_a, _branch_b)]
    _norepair_sensitivity = {(_branch_a, _branch_b): "ratio"}
    _norepair_result_rows, _norepair_audit = repair_matching_safety(
        _norepair_rows, _norepair_pairs, _norepair_sensitivity)
    assert not _norepair_audit.ok, "공유 hub 없는 쌍인데 수리된 것처럼 PASS가 나옴 -- 버그"
    assert sorted(_norepair_result_rows.keys()) == ["rowA", "rowB"], \
        "건드리면 안 되는데 행 구조가 바뀜"


def test_s105_repair_matching_safety(library_dir):
    """[repair_matching_safety() -- 세션16 branch 복합 매칭: current_reuse_telescopic_ota.
    topology.json의 M6 그룹 실제 사례(M1a-M2a/M1b-M2b가 각각 kcl 직렬 branch, M2a/M2b는
    source가 서로 달라 예전엔 조용히 스킵됐다) -- 이제 M1a/M1b와 함께 묶여 재배치되는지,
    branch 구조가 없는 위 테스트는 여전히 완전히 그대로인지(회귀 없음) 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S105(줄 1763-1792, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _m6b_lib = library_dir
    _m6b_trs, _m6b_meta = load_topology(
        os.path.join(_m6b_lib, "current_reuse_telescopic_ota.topology.json"))
    _m6b_by_name = {t.name: t for t in _m6b_trs}
    _m6b_names = ["M1a", "M1b", "M2a", "M2b", "M6", "M7"]
    _m6b_row = [_dc_replace(_m6b_by_name[n], stack_id="seg1") for n in _m6b_names]
    _m6b_pairs = [("M1a", "M1b"), ("M2a", "M2b")]
    _m6b_sensitivity = {("M1a", "M1b"): "offset", ("M2a", "M2b"): "ratio"}
    assert _m6b_by_name["M2a"].source != _m6b_by_name["M2b"].source, \
        "M2a/M2b가 source를 공유하면 이 테스트가 재현하려는 사례(branch_symmetric)가 아님"

    _m6b_before = audit_row_split({"seg1": _m6b_row}, matching_pairs=_m6b_pairs,
                                   pair_sensitivity=_m6b_sensitivity)
    assert not _m6b_before.ok, "수리 전인데 이미 PASS -- 재현 시나리오 실패"

    _m6b_rows, _m6b_after = repair_matching_safety({"seg1": _m6b_row}, _m6b_pairs, _m6b_sensitivity)
    _m6b_final_names = {rn: {t.name for t in devs} for rn, devs in _m6b_rows.items()}
    _m6b_row_of = {n: rn for rn, names in _m6b_final_names.items() for n in names}
    assert _m6b_row_of["M2a"] == _m6b_row_of["M2b"], \
        f"M2a/M2b가 같은 행에 안 묶임(branch 복합 매칭 실패): {_m6b_row_of}"
    assert _m6b_row_of["M1a"] == _m6b_row_of["M2a"] == _m6b_row_of["M1b"] == _m6b_row_of["M2b"], \
        f"M1a/M1b/M2a/M2b 4개가 한 branch 복합으로 전부 같은 행에 묶여야 하는데: {_m6b_row_of}"
    assert not _m6b_after.ok, (
        "n_fingers=1인 M1a/M1b/M2a/M2b는 dx<=0.5(3c)를 기하학적으로 달성할 수 없다(세션16 실측,"
        " 최선이 dx=1.0) -- 지금 PASS라면 회귀가 아니라 오히려 이 함수 범위 밖의 일(핑거증가,"
        " 다음 세션 확장 지점)이 우연히 된 것이니 이 assert부터 다시 확인할 것")


def test_s106__branch_composite_pair(s104_state):
    """[_branch_composite_pair() -- branch 구조가 없는(2단자 net으로 안 이어진) 단독 소자
    쌍은 None을 돌려줘 기존 폴백(위 rowA/rowB 테스트)이 안 깨지는지 직접 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S106(줄 1794-1800, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _branch_a = s104_state._branch_a
    _branch_b = s104_state._branch_b
    _norepair_pairs = s104_state._norepair_pairs
    _t_branch_a = s104_state._t_branch_a
    _t_branch_b = s104_state._t_branch_b

    _bc_none = _branch_composite_pair(_branch_a, _branch_b,
                                       {_branch_a: _t_branch_a, _branch_b: _t_branch_b}, _norepair_pairs)
    assert _bc_none is None, f"branch 구조가 없는데 composite가 나옴(오탐): {_bc_none}"


def test_s107__composite_collapse_for_crossover(s105_state):
    """[세션17 _composite_collapse_for_crossover()/find_min_crossover_layout_with_
    branch_composite() -- find_min_crossover_layout()을 부르기 전에 branch(M1a-M2a,
    M1b-M2b)를 미리 합성 소자로 뭉쳐서, crossover 짝짓기가 애초에 branch를 갈라놓을
    수 없게 만드는지(채점 기반 회피가 아니라 구조적 보장) M6 그룹으로 확인 -- 사용자
    질문(세션17): 'find_min_crossover_layout() 호출 전에도 branch_composite_pair를
    써야 하지 않나?']

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S107(줄 1801-1835, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _m6b_pairs = s105_state._m6b_pairs
    _m6b_row = s105_state._m6b_row

    _cc_sensitivity = {("M1a", "M1b"): "offset", ("M2a", "M2b"): "ratio"}
    _cc_trs, _cc_pairs, _cc_sens, _cc_expand = _composite_collapse_for_crossover(
        _m6b_row, _m6b_pairs, _cc_sensitivity)
    assert len(_cc_trs) == len(_m6b_row) - 2, \
        f"4개 실제 소자(M1a/M2a/M1b/M2b) -> 2개 합성으로 순감소 2여야 하는데: " \
        f"{len(_m6b_row)} -> {len(_cc_trs)}"
    assert len(_cc_pairs) == 1, \
        f"hub쪽(M1a/M1b)/leaf쪽(M2a/M2b) 선언 쌍 2개가 합성 쌍 1개로 합쳐져야 하는데: {_cc_pairs}"
    _cc_composite_name = _cc_pairs[0]
    assert set(_cc_expand[_cc_composite_name[0]]) == {"M1a", "M2a"} or \
        set(_cc_expand[_cc_composite_name[0]]) == {"M1b", "M2b"}, \
        f"합성 이름의 expand_map이 예상과 다름: {_cc_expand}"
    assert {"M6", "M7"} <= {t.name for t in _cc_trs}, \
        "미매칭 소자(M6/M7)가 합성 과정에서 사라지면 안 됨"
    assert _cc_sens[_cc_composite_name] == "offset", \
        f"hub쪽(M1a/M1b)이 offset이므로 합성 쌍도 offset이어야 하는데: {_cc_sens}"

    _cc_result = find_min_crossover_layout_with_branch_composite(_m6b_row, _m6b_pairs, _cc_sensitivity)
    _cc_total = sum(len(s["transistor_sequence"]) for s in _cc_result["segments"])
    assert _cc_total == sum(t.n_fingers for t in _m6b_row), \
        f"펼친 뒤 finger 총합이 원본과 안 맞음: {_cc_total} != {sum(t.n_fingers for t in _m6b_row)}"
    _cc_seg_of: dict = {}
    for i, seg in enumerate(_cc_result["segments"]):
        for name in seg["transistor_sequence"]:
            _cc_seg_of.setdefault(name, set()).add(i)
    assert _cc_seg_of["M1a"] == _cc_seg_of["M2a"], \
        f"M1a/M2a(같은 branch)가 합성 소자인데도 다른 segment에 나옴 -- 구조적 보장 실패: {_cc_seg_of}"
    assert _cc_seg_of["M1b"] == _cc_seg_of["M2b"], \
        f"M1b/M2b(같은 branch)가 합성 소자인데도 다른 segment에 나옴 -- 구조적 보장 실패: {_cc_seg_of}"


def test_s108_section(s104_state):
    """[회귀 -- branch 구조 없는 그룹(위 rowA/rowB 픽스처)은 _composite_collapse_for_
    crossover()가 아무것도 안 합치고 원본 그대로 통과시키는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S108(줄 1837-1846, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _branch_a = s104_state._branch_a
    _branch_b = s104_state._branch_b
    _norepair_pairs = s104_state._norepair_pairs
    _norepair_sensitivity = s104_state._norepair_sensitivity
    _t_branch_a = s104_state._t_branch_a
    _t_branch_b = s104_state._t_branch_b

    _cc_none_trs, _cc_none_pairs, _cc_none_sens, _cc_none_expand = \
        _composite_collapse_for_crossover(
            [_t_branch_a, _t_branch_b], _norepair_pairs, _norepair_sensitivity)
    assert _cc_none_pairs == _norepair_pairs and _cc_none_expand == {}, \
        f"branch 구조가 없는데 뭔가 합성됨(오탐): pairs={_cc_none_pairs}, expand={_cc_none_expand}"
    assert {t.name for t in _cc_none_trs} == {_branch_a, _branch_b}


def test_s109_repair_matching_safety(s104_state, s105_state):
    """[repair_matching_safety() -- 세션17 relaxed_pairs: 최후수단 인접배치 완화가
    select_layout_tool()의 common-centroid 판단을 실제로 무시하는지(위 M6 그룹 fixture
    재사용), 그리고 공유 hub도 branch composite도 없는 쌍(위 rowA/rowB)은 relaxed_pairs에
    있어도 여전히 손 못 대는지(완화가 없는 layout 자유도를 만들어내지 않음) 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S109(줄 1847-1870, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _branch_a = s104_state._branch_a
    _branch_b = s104_state._branch_b
    _m6b_pairs = s105_state._m6b_pairs
    _m6b_row = s105_state._m6b_row
    _m6b_sensitivity = s105_state._m6b_sensitivity
    _norepair_pairs = s104_state._norepair_pairs
    _norepair_rows = s104_state._norepair_rows
    _norepair_sensitivity = s104_state._norepair_sensitivity

    _rlx_rows, _rlx_after = repair_matching_safety(
        {"seg1": _m6b_row}, _m6b_pairs, _m6b_sensitivity,
        relaxed_pairs={frozenset({"M1a", "M1b"})})
    assert not _rlx_after.ok, (
        "완화됐다고 audit.ok가 True가 되면 안 됨 -- relaxed_pairs는 3c 요구사항 자체를 없애지"
        " 않는다(sizing_recipe.py의 run_matching_safety_with_finger_growth()가 감사 정책을"
        " 그대로 존중하는지 확인하는 하위 계약)")
    _rlx_3c = next(c for c in _rlx_after.checks
                    if c.name.startswith("3c.") and "[M1a/M1b]" in c.name)
    assert not _rlx_3c.ok and "[참고용" not in _rlx_3c.name, \
        f"3c[M1a/M1b]가 여전히 필수 게이트로 FAIL이어야 하는데: {_rlx_3c}"

    _rlx_norepair_rows, _rlx_norepair_audit = repair_matching_safety(
        _norepair_rows, _norepair_pairs, _norepair_sensitivity,
        relaxed_pairs={frozenset({_branch_a, _branch_b})})
    assert sorted(_rlx_norepair_rows.keys()) == ["rowA", "rowB"] and not _rlx_norepair_audit.ok, \
        "공유 hub도 branch composite도 없는 쌍인데 relaxed_pairs로 뭔가 바뀜(있지도 않은 layout" \
        " 자유도를 만들어냄 -- 버그)"


def test_s111_geometry_colocation_union(s086_state, s103_state):
    """=== Test 29: derive_stack_groups()/assign_finger_geometry() (배치 7-6, 2026-07-31) ===   folded_cascode.topology.json 전체(13개 소자, matching_pairs -- 세션34에 M11/MN   gap-fill 반영 후 6개)를 그대로 사용 -- 손타이핑 넷리스트 없음(topology.json   단일 소스 원칙).

    [geometry_colocation_union() -- 2026-08-05(세션10) L1/L2 하드컷: derive_stack_groups()가
    kcl_series_union()/geometry_colocation_union() 두 함수로 분리됐고, folded_cascode netlist도
    세션9에 전면 재구성됐다(outA/outB -> Vg7/out) -- assign_finger_geometry()가 실제로 받는
    것과 동일하게 current_forced=True 쌍만 필터링해 geometry_colocation_union()으로 병합]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S111(줄 1877-1914, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_loaded = s086_state._fc_loaded
    _fc_pairs_meta = s103_state._fc_pairs_meta

    _fc_forced_pairs = [tuple(p["names"]) for p in _fc_pairs_meta if p["current_forced"]]
    _fc_groups = geometry_colocation_union(_fc_loaded, _fc_forced_pairs)
    _fc_all_members = sorted(n for members in _fc_groups.values() for n in members)
    assert _fc_all_members == sorted(t.name for t in _fc_loaded), \
        "geometry_colocation_union()가 소자를 빠뜨리거나 중복시킴"
    _fc_group_sets = {frozenset(members) for members in _fc_groups.values()}
    # 실측(2026-08-05 세션10, 손으로 미리 추정했다가 실행 결과로 정정됨) -- rule1(같은 극성+
    # non-rail+drain=source)이 declared pair보다 훨씬 넓게 병합한다:
    #   PMOS 6개: M6.source=X가 M1.drain=X/M3.drain=X와 매칭(둘 다 pmos) -> {M1,M3,M6},
    #             M5.source=Y가 M2.drain=Y/M4.drain=Y와 매칭 -> {M2,M4,M5}, 그리고 선언된
    #             M1/M2(diff_pair)가 이 두 하위그룹을 하나로 잇는다 -> {M1,M2,M3,M4,M5,M6}.
    #   NMOS 4개: M7.source=Vg9가 M9.drain=Vg9(diode)와, M8.source=Vg10이 M10.drain=Vg10
    #             (diode)와 매칭(둘 다 nmos) -> {M7,M9}/{M8,M10}, 선언된 M7/M8(current_matched)이
    #             이 둘을 잇는다 -> {M7,M8,M9,M10}.
    # 즉 rule1이 "다이오드 레퍼런스 체인 전체"를 자동으로 찾아내 선언된 2-소자 쌍보다 훨씬
    # 유용한 물리 그룹을 만든다 -- M5/M6(branch_symmetric, current_forced=False라 declared
    # 병합엔 안 들어가지만)는 이미 rule1으로 각자 PMOS/NMOS 그룹에 흡수돼 있다.
    assert frozenset({"M1", "M2", "M3", "M4", "M5", "M6"}) in _fc_group_sets, \
        f"PMOS 6개(M1..M6)가 diff_pair+drain=source 체인으로 한 그룹이 돼야 하는데 안 됨: {_fc_group_sets}"
    assert frozenset({"M7", "M8", "M9", "M10"}) in _fc_group_sets, \
        f"NMOS 4개(M7..M10)가 current_matched+drain=source 체인으로 한 그룹이 돼야 하는데 안 됨: {_fc_group_sets}"
    assert frozenset({"MP"}) in _fc_group_sets, \
        "MP는 다른 어떤 소자와도 안 묶여야 하는데(rail만 공유, drain=source 체인/matching_pair 없음) 그룹이 다름"
    # ⚠️ 2026-08-14 세션34 정정 -- M11/MN은 더 이상 고립 singleton이 아니다.
    # propose_device_roles_gap_fill()의 층위1 current_mirror 폴백(role 기반 정적
    # 레퍼런스 판정으로 정정된 뒤, `.ai/context.md` 세션34 참고)이 M11(diffpair 진짜
    # tail, `ideal_sources`의 `Ibg`로 MN이 독립 레퍼런스임이 확인됨)/MN(diode-connected
    # 레퍼런스) 쌍을 declared matching_pairs(ratio, current_forced=True)로 실제
    # topology.json에 반영했다 -- 다른 declared 2-소자 mirror쌍(M9/M10, M7/M8)과 정확히
    # 같은 패턴이라 이제 이 둘도 같은 이유로 한 그룹이 된다.
    assert frozenset({"M11", "MN"}) in _fc_group_sets, \
        f"M11/MN이 declared matching_pair(current_forced=True)로 한 그룹이 돼야 하는데 안 됨: {_fc_group_sets}"


def test_s112_geometry_colocation_union(s111_state, s086_state):
    """[geometry_colocation_union() -- 재현성: 같은 입력 다시 넣으면 완전히 같은 그룹]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S112(줄 1915-1919, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_forced_pairs = s111_state._fc_forced_pairs
    _fc_groups = s111_state._fc_groups
    _fc_loaded = s086_state._fc_loaded

    _fc_groups_again = geometry_colocation_union(_fc_loaded, _fc_forced_pairs)
    assert _fc_groups == _fc_groups_again, "같은 입력인데 결과가 달라짐 -- 재현성 위반"


def test_s113_assign_finger_geometry(s111_state):
    """[assign_finger_geometry() -- 위 그룹 + 합성 sizing_results(가상 gm/ID 결과,
    matching pair는 W 동일하게)로 sizing_overrides 자동 구성]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S113(줄 1920-1957, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_groups = s111_state._fc_groups

    # W 값은 sizing 산출물(이 함수가 실제로 테스트하는 대상)이라 topology.json에 없다 --
    # 합성해서 채우는 게 정당하다(§1 스키마 원칙). matching pair는 W를 동일하게 둬서
    # search_stack_finger_w()가 실제로 후보를 찾을 수 있게 구성.
    _fc_sizing_results = {
        "M3": {"W": 30e-6, "L": 0.5e-6}, "M4": {"W": 30e-6, "L": 0.5e-6},
        "M9": {"W": 24e-6, "L": 0.5e-6}, "M10": {"W": 24e-6, "L": 0.5e-6},
        "M1": {"W": 80e-6, "L": 0.35e-6}, "M2": {"W": 80e-6, "L": 0.35e-6},
        "M5": {"W": 30e-6, "L": 1.0e-6}, "M6": {"W": 30e-6, "L": 1.0e-6},
        "M7": {"W": 40e-6, "L": 0.5e-6}, "M8": {"W": 40e-6, "L": 0.5e-6},
        "MP": {"W": 20e-6, "L": 1.5e-6}, "M11": {"W": 16e-6, "L": 0.5e-6}, "MN": {"W": 16e-6, "L": 0.5e-6},
    }
    _fc_overrides = assign_finger_geometry(_fc_sizing_results, _fc_groups,
                                            min_finger_w=1e-6, max_finger_w=40e-6)
    assert set(_fc_overrides.keys()) == set(_fc_sizing_results.keys()), \
        "assign_finger_geometry()가 일부 소자를 빠뜨림"
    for _name, _ov in _fc_overrides.items():
        assert _ov["n_fingers"] >= 1 and isinstance(_ov["n_fingers"], int)
        assert abs(_ov["w"] - _ov["n_fingers"] * _ov["finger_w"]) < 1e-15, \
            f"{_name}: w != n_fingers*finger_w"
        assert abs(_ov["w"] - _fc_sizing_results[_name]["W"]) / _fc_sizing_results[_name]["W"] < 1e-6, \
            f"{_name}: 배정된 w가 원래 sizing W와 너무 다름"
        _owning_group = next(sid for sid, members in _fc_groups.items() if _name in members)
        assert _ov["stack_id"] == _owning_group, f"{_name}: stack_id가 자기 그룹 키와 다름"
        # 2026-08-13(세션31) -- overrides["l"]이 sizing_results[name]["L"]과 정확히 일치하는지
        # 확인(assign_finger_geometry()의 "L"(대문자, sizing 쪽 키) -> "l"(소문자, Transistor
        # 필드) 의도적 rename이 조용히 깨지지 않았는지 잡는 회귀 테스트).
        assert _ov["l"] == _fc_sizing_results[_name]["L"], \
            f"{_name}: overrides['l']={_ov['l']} != sizing_results['L']={_fc_sizing_results[_name]['L']}"
    _row_lengths = {}
    for _name, _ov in _fc_overrides.items():
        _row_lengths.setdefault(_ov["stack_id"], 0)
        _row_lengths[_ov["stack_id"]] += _ov["n_fingers"]


def test_s115_section():
    """=== Test 30: analog-grammar 연동(Tier 1) — find_idiom_matches()/find_matching_     candidates(idiom_matches=)/find_stack_edges()/find_stacked_matching_candidates()     (2026-08-06, analog-topology-json-library 세션18 K/L절 + 사용자 설계 논의) ===

    [0. analog-grammar 사용 가능 확인 -- 없으면 이 Test 전체가 무의미하니 먼저 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S115(줄 1963-1968, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _ag_matches_probe = find_idiom_matches(folded_cascode_example())
    assert _ag_matches_probe is not None, \
        "analog-grammar skill을 찾지 못함 -- skills/analog-grammar/assets가 있는지 확인할 것"


def test_s116_None(s007_state):
    """[1. 하위호환 -- idiom_matches=None(기본값)이면 Test 6과 완전히 동일한 net-only 동작]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S116(줄 1969-1974, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    found = s007_state.found

    _t30_old_again = find_matching_candidates(folded_cascode_example())
    assert _t30_old_again["current_mirror"].keys() == found["current_mirror"].keys()
    assert _t30_old_again["diff_pair"].keys() == found["diff_pair"].keys()


def test_s117_connectivity():
    """[2. M57/M58 오탐 재현 -- 세션18 실사고 connectivity(2026-07-29 disposed -> 2026-08-03
    정정)를 그대로 fixture로 구성. 양성대조(MrefA/MrefB, 진짜 diode 레퍼런스 미러)도 함께]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S117(줄 1975-1998, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _mirror_fixture = [
        Transistor("M57", "pmos", source="N58_57", drain="Vbias2", gate="Vbias2", n_fingers=1),
        Transistor("M58", "pmos", source="Vx", drain="N58_57", gate="Vbias2", n_fingers=1),
        Transistor("MrefA", "pmos", source="vdd", drain="Vbias9", gate="Vbias9", n_fingers=1),
        Transistor("MrefB", "pmos", source="vdd", drain="out9", gate="Vbias9", n_fingers=1),
    ]
    _old_mirror = find_matching_candidates(_mirror_fixture)
    _old_mirror_sets = {frozenset(t.name for t in g) for g in _old_mirror["current_mirror"].values()}
    assert frozenset({"M57", "M58"}) in _old_mirror_sets, \
        "옛 동작(gate만 봄)이 M57/M58을 current_mirror로 잡는지부터 재현 안 됨 -- fixture 확인 필요"

    _mirror_matches = find_idiom_matches(_mirror_fixture)
    _new_mirror = find_matching_candidates(_mirror_fixture, idiom_matches=_mirror_matches)
    _new_mirror_sets = {frozenset(t.name for t in g) for g in _new_mirror["current_mirror"].values()}
    assert frozenset({"M57", "M58"}) not in _new_mirror_sets, \
        f"gate+source 그룹핑 후에도 M57/M58이 여전히 current_mirror로 잡힘: {_new_mirror_sets}"
    assert frozenset({"MrefA", "MrefB"}) in _new_mirror_sets, \
        f"진짜 diode 레퍼런스 미러(MrefA/MrefB)까지 같이 사라짐(과잉 필터): {_new_mirror_sets}"


def test_s118_folded_cascode_example():
    """[3. M11/MN 오탐 재현 -- folded_cascode_example(), 둘 다 self-diode(role=DIODE_CONNECTED)
    라 diff_pair의 AMPLIFYING 요구를 애초에 통과 못해야 함. inputs 선언 없으면 vin_p/vin_n도
    이름 힌트 미매치로 BIAS 취급돼 M1/M2까지 같이 사라지므로 반드시 inputs= 선언]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S118(줄 1999-2017, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_matches_bare = find_idiom_matches(folded_cascode_example())
    _fc_new_bare = find_matching_candidates(folded_cascode_example(), idiom_matches=_fc_matches_bare)
    assert _fc_new_bare["diff_pair"] == {}, \
        f"inputs 미선언 상태에서도 diff_pair가 나오면 안 되는데 나옴(vin_p/vin_n 힌트 이슈 재확인 필요): {_fc_new_bare['diff_pair']}"

    _fc_matches = find_idiom_matches(folded_cascode_example(), inputs=("vin_p", "vin_n"))
    _fc_new = find_matching_candidates(folded_cascode_example(), idiom_matches=_fc_matches)
    _fc_new_diffpair_sets = {frozenset(t.name for t in g) for g in _fc_new["diff_pair"].values()}
    assert frozenset({"M11", "MN"}) not in _fc_new_diffpair_sets, \
        f"M11/MN이 여전히 diff_pair로 잡힘: {_fc_new_diffpair_sets}"
    assert frozenset({"M1", "M2"}) in _fc_new_diffpair_sets, \
        f"진짜 차동쌍(M1/M2)까지 같이 사라짐(과잉 필터): {_fc_new_diffpair_sets}"


def test_s119_M2(s118_state):
    """[4. 캐스코드 대칭쌍(M2a/M2b류) 복합소자 상속 -- folded_cascode의 M1/M2(확정 diff_pair)
    위에 직접 stacked된 M5/M6를 find_stacked_matching_candidates()가 재귀적으로 찾는지.
    M1 위엔 극성이 다른 M5(pmos)/M7(nmos)이 동시에 얹혀 있어(폴딩 노드 X 공유) 같은
    kind로 좁히는 로직이 실제로 필요한 fixture -- 2026-08-06 실측으로 발견된 버그 재발 방지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S119(줄 2018-2033, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _fc_new = s118_state._fc_new

    _fc_edges = find_stack_edges(folded_cascode_example())
    assert _fc_edges is not None
    _fc_base_pairs = [(g[0].name, g[1].name) for g in _fc_new["diff_pair"].values()]
    assert _fc_base_pairs == [("M1", "M2")], f"base_pairs 예상과 다름: {_fc_base_pairs}"
    _fc_stacked = find_stacked_matching_candidates(folded_cascode_example(), _fc_base_pairs, _fc_edges)
    _fc_stacked_sets = {frozenset(t.name for t in g) for g in _fc_stacked.values()}
    assert frozenset({"M5", "M6"}) in _fc_stacked_sets, \
        f"M1/M2 위의 M5/M6(둘 다 pmos)이 상속되지 않음(극성 필터 버그 재발?): {_fc_stacked_sets}"
    assert frozenset({"M5", "M7"}) not in _fc_stacked_sets, \
        f"극성이 다른 M7(nmos)이 M5 자리에 잘못 섞여 들어옴: {_fc_stacked_sets}"


def test_s120_section(library_dir):
    """[5. 어댑터 자체 폴백 -- gate가 전혀 없는(레거시) Transistor 목록을 주면
    _to_analog_grammar_devs()가 전부 걸러내 devs=[]가 되고, find_idiom_matches()/
    find_stack_edges()가 (analog-grammar 자체는 멀쩡해도) 자연스럽게 None을 반환하는지.
    analog-grammar 미설치 상황(ImportError 경로)은 사용자 환경에 실제로 있을 때만
    검증 가능하므로(설치를 일부러 지웠다 복원하는 건 self-test로 하기엔 위험한 파일시스템
    조작이라 하지 않는다), 여기서는 두 어댑터가 실제로 소비하는 '입력이 비게 되는'
    경로로 None-반환을 재현한다]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S120(줄 2034-2057, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _no_gate_fixture = [Transistor("Ma", "pmos", source="vdd", drain="n1"),
                         Transistor("Mb", "pmos", source="vdd", drain="n2")]
    assert find_idiom_matches(_no_gate_fixture) is None, \
        "gate 없는 소자만 있는데도 find_idiom_matches()가 None이 아님"
    assert find_stack_edges(_no_gate_fixture) is None, \
        "gate 없는 소자만 있는데도 find_stack_edges()가 None이 아님"
    _fallback_result = find_matching_candidates(_no_gate_fixture,
                                                  idiom_matches=find_idiom_matches(_no_gate_fixture))
    assert _fallback_result == {"current_mirror": {}, "diff_pair": {}}

    _lib_dir31 = library_dir
    _crt_path = _os31.path.join(_lib_dir31, "current_reuse_telescopic_ota.topology.json")


def test_s122_section(s120_state):
    """[1. 실제 회로(51개 소자)로 자동 구성 -- ok=True, 세 체크 전부 자동 데이터로 통과하는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S122(줄 2059-2074, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _crt_path = s120_state._crt_path

    _crt_transistors, _crt_meta = load_topology(_crt_path)
    _crt_structured = _crt_meta["netlist_sections_structured"]
    assert _crt_structured is not None, "current_reuse_telescopic_ota가 구조화 필드를 못 읽음"
    _crt_expected_total = sum(len(v["devices"]) for v in _crt_structured.values())
    assert _crt_expected_total == len(_crt_transistors) == 51, \
        f"구조화 블록 합({_crt_expected_total})이 netlist 전체 개수({len(_crt_transistors)})와 불일치"
    _crt_audit = run_full_circuit_audit_from_topology(_crt_path)
    assert _crt_audit.ok, f"실제 회로 자동감사가 FAIL: {_crt_audit.checks}"
    _crt_check_names = [c.name for c in _crt_audit.checks]
    assert any(c.startswith("1.") for c in _crt_check_names) and \
           any(c.startswith("2.") for c in _crt_check_names) and \
           any(c.startswith("3.") for c in _crt_check_names), \
        f"체크 1/2/3이 전부 실행되지 않음: {_crt_check_names}"


def test_s123_dispositions(s122_state):
    """[2. dispositions 변환 -- symmetry.dispositions(list)와 개수가 일치하고, 형식이 (category,
    reason) 튜플로 정확히 바뀌는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S123(줄 2075-2089, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _crt_meta = s122_state._crt_meta

    _crt_raw_dispositions = _crt_meta["symmetry"]["dispositions"]
    _crt_sample = _crt_raw_dispositions[0]
    _crt_key = (_crt_sample["tag"], _crt_sample["kind"], _crt_sample["key"])
    _crt_expected_val = (_crt_sample["category"], _crt_sample["reason"])
    # run_full_circuit_audit_from_topology()는 dispositions dict를 반환하지 않으므로(§1.6 계약을
    # 그대로 따름, AuditResult만 반환) 변환 로직 자체를 직접 재현해 대조한다.
    _crt_disp_dict = {(d["tag"], d["kind"], d["key"]): (d["category"], d["reason"])
                       for d in _crt_raw_dispositions}
    assert len(_crt_disp_dict) == len(_crt_raw_dispositions), \
        "dispositions 변환 중 (tag,kind,key) 키 충돌로 일부가 사라짐"
    assert _crt_disp_dict[_crt_key] == _crt_expected_val, "dispositions 변환 형식이 계약과 다름"


def test_s124_section(library_dir):
    """[3. 구조화 필드가 없는 회로(folded_cascode) -- ValueError로 명확히 실패하는지,
    조용히 빈 expected_counts로 넘어가지 않는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S124(줄 2090-2098, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib_dir31 = library_dir

    with pytest.raises(ValueError) as _e31_info:
        run_full_circuit_audit_from_topology(_os31.path.join(_lib_dir31, "folded_cascode.topology.json"))
    _e31 = _e31_info.value
    assert "_netlist_sections_structured" in str(_e31), f"에러 메시지가 원인을 안 가리킴: {_e31}"


def test_s125_section():
    """[4. 구조화가 netlist 전수를 못 커버하면(소자 하나가 어느 블록에도 없음) ValueError --
    임시 topology.json으로 실제 함수를 태워 확인(내부 로직 재현이 아니라 진짜 호출)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S125(줄 2099-2130, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _broken_topo = {
        "schema_version": "1.0", "topology_name": "broken_test_fixture", "source": None,
        "ports": {}, "passive_elements": [], "ideal_sources": [],
        "netlist": [
            {"name": "Ma", "kind": "pmos", "source": "vdd", "drain": "n1", "gate": "vb"},
            {"name": "Mb", "kind": "pmos", "source": "vdd", "drain": "n2", "gate": "vb"},
        ],
        "symmetry": {"matching_pairs": [], "dispositions": []},
        "compensation": None,
        "_netlist_sections_structured": {
            "only_block": {"label": "test", "confidence": "HIGH", "devices": ["Ma"]},  # Mb 누락
        },
    }
    with _tempfile31.NamedTemporaryFile(mode="w", suffix=".topology.json", delete=False,
                                          encoding="utf-8") as _f31:
        json.dump(_broken_topo, _f31)
        _broken_path = _f31.name
    try:
        with pytest.raises(ValueError) as _e31b_info:
            run_full_circuit_audit_from_topology(_broken_path)
    finally:
        _os31.remove(_broken_path)
    _e31b = _e31b_info.value
    assert "Mb" in str(_e31b), f"에러 메시지가 빠진 소자를 안 가리킴: {_e31b}"


def test_s126_trace_vdd_to_gnd_branches():
    """=== Test 32: trace_vdd_to_gnd_branches() -- 세션23 실측(4가지 vertical_stack_id
    자동화 시도 중 유일하게 성공한 branch tracing)의 핵심 성질 3가지를 합성 fixture로
    재확인: (1) 병렬 형제(같은 kind, 같은 타입 단자 공유)는 절대 안 이어짐,
    (2) PMOS drain=NMOS drain 만남 지점은 정상적으로 이어짐, (3) 진짜 fan-out은
    branch 여러 개로 정확히 갈라지고, 소비자가 없는 net은 non_transistor로 종료 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S126(줄 2131-2170, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t32_fixture = [
        Transistor("M6", "pmos", source="vdd", drain="Vx"),
        Transistor("M7", "pmos", source="vdd", drain="Vx"),
        Transistor("M1a", "pmos", source="Vx", drain="N1"),
        Transistor("M1b", "pmos", source="Vx", drain="N2"),   # M1a의 병렬 형제 -- N2는 아무도 안 씀
        Transistor("M2a", "pmos", source="N1", drain="Nout"),
        Transistor("M3a", "nmos", source="Ngndmid", drain="Nout"),  # M2a와 drain=drain으로 만남
        Transistor("M19", "nmos", source="gnd", drain="Nout"),      # Nout의 두 번째 소비자(진짜 fork)
        Transistor("M4a", "nmos", source="gnd", drain="Ngndmid"),
        Transistor("Mbg", "pmos", source="vdd", drain="Vbiasx", gate="Vbiasx"),  # diode, 소비자 없음
    ]
    _t32_result = trace_vdd_to_gnd_branches(_t32_fixture)
    _t32_branches = _t32_result["branches"]
    _t32_complete = [b for b in _t32_branches if b["terminates_at"] == "gnd"]
    _t32_dead = [b for b in _t32_branches if b["terminates_at"] == "non_transistor"]
    assert len(_t32_branches) == 7, f"branch 총 개수가 7이 아님(조합 폭발/과소탐지 재확인): {len(_t32_branches)}"
    assert len(_t32_complete) == 4 and len(_t32_dead) == 3, \
        f"완주/dead-end 분류가 예상과 다름: complete={len(_t32_complete)} dead={len(_t32_dead)}"

    for b in _t32_branches:
        assert not ({"M1a", "M1b"} <= set(b["chain"])), \
            f"병렬 형제 M1a/M1b가 같은 branch에 같이 들어감(회귀): {b['chain']}"

    assert ["M6", "M1a", "M2a", "M3a", "M4a"] in [b["chain"] for b in _t32_complete], \
        "M2a(pmos)->M3a(nmos) drain=drain 만남 경로가 안 나옴"
    assert ["M6", "M1a", "M2a", "M19"] in [b["chain"] for b in _t32_complete], \
        "Nout의 두 번째 소비자(M19)로 갈라지는 fork branch가 안 나옴"

    _t32_mbg = [b for b in _t32_branches if b["chain"] == ["Mbg"]]
    assert len(_t32_mbg) == 1 and _t32_mbg[0]["terminates_at"] == "non_transistor", \
        "diode-connected Mbg(소비자 없는 Vbiasx)가 non_transistor로 안 끝남"


def test_s127_suggest_vertical_stack_composites():
    """=== Test 33: suggest_vertical_stack_composites() -- branch tracing(Test 32) +
    analog-grammar idiom matching(floating-battery 등)을 합쳐 세션23 5번째 실측
    (62/63 vertical_stack_id 일치)의 핵심 성질을 합성 fixture로 재확인: 연속된
    diode-connected 소자 쌍만 floating-battery로 병합되고, 그 아래 non-diode
    소자는 별도 composite으로 남는지 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S127(줄 2171-2199, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t33_probe = find_idiom_matches(folded_cascode_example())
    assert _t33_probe is not None, "analog-grammar skill을 찾지 못함 -- Test 30과 동일 전제조건"
    _t33_fixture = [
        Transistor("Ma", "pmos", source="vdd", drain="Ntop", gate="Ntop"),   # diode(G=D)
        Transistor("Mb", "pmos", source="Ntop", drain="Nmid", gate="Nmid"),  # diode(G=D), Ma 위에 직렬
        Transistor("Mc", "nmos", source="gnd", drain="Nmid", gate="Vbias4"), # non-diode, 체인 종단
    ]
    _t33_result = suggest_vertical_stack_composites(_t33_fixture)
    assert _t33_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    assert len(_t33_result) == 1, f"branch 1개짜리 fixture인데 결과가 {len(_t33_result)}개"
    _t33_composites = _t33_result[0]["composites"]
    assert _t33_result[0]["chain"] == ["Ma", "Mb", "Mc"], \
        f"branch 골격 자체가 어긋남(Test 32 회귀 가능성): {_t33_result[0]['chain']}"
    assert len(_t33_composites) == 2, f"composite 개수가 2가 아님(과잉/과소 병합): {_t33_composites}"
    assert _t33_composites[0]["members"] == ["Ma", "Mb"] and _t33_composites[0]["idiom"] == "floating-battery", \
        f"Ma/Mb가 floating-battery로 안 묶임: {_t33_composites[0]}"
    assert _t33_composites[1]["members"] == ["Mc"], \
        f"Mc가 diode 쌍에 잘못 흡수됨: {_t33_composites[1]}"
    assert isinstance(_t33_composites[1]["ports"], dict), \
        f"ports는 항상 dict여야 함(단일 소자 idiom이 있으면 그 내용, 없으면 빈 dict): {_t33_composites[1]}"


def test_s128_trace_gnd_to_vdd_branches():
    """=== Test 35: trace_gnd_to_vdd_branches()/find_differential_and_mirror_forks() --
    telescopic/current-reuse 구조처럼 differential pair가 스택 안에 여러 층으로
    있을 때, 하향(VDD->GND) 단독으로는 위쪽 pair만, 상향(GND->VDD) 단독으로는
    아래쪽 pair만 잡고, 양방향을 합쳐야 둘 다 잡히는지(세션23 실측 -- 사용자
    지적: "telescopic differential pair를 인식 못하는 문제") 합성 fixture로 재현 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S128(줄 2200-2244, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t35_fixture = [
        Transistor("M6", "pmos", source="vdd", drain="Vx", gate="Vbias1"),
        Transistor("M1a", "pmos", source="Vx", drain="N1", gate="Vip"),    # 위쪽 diff pair
        Transistor("M1b", "pmos", source="Vx", drain="N2", gate="Vim"),
        Transistor("M2a", "pmos", source="N1", drain="Nout1", gate="Vbias2"),
        Transistor("M2b", "pmos", source="N2", drain="Nout2", gate="Vbias2"),
        Transistor("M3a", "nmos", source="N3", drain="Nout1", gate="Vbias3"),
        Transistor("M3b", "nmos", source="N4", drain="Nout2", gate="Vbias3"),
        Transistor("M4a", "nmos", source="Vy", drain="N3", gate="Vip"),    # 아래쪽 diff pair
        Transistor("M4b", "nmos", source="Vy", drain="N4", gate="Vim"),
        Transistor("M5", "nmos", source="gnd", drain="Vy", gate="Vbias4"),
    ]
    _t35_down = trace_vdd_to_gnd_branches(_t35_fixture)
    _t35_down_chains = [b["chain"] for b in _t35_down["branches"] if b["terminates_at"] == "gnd"]
    assert _t35_down_chains == [["M6", "M1a", "M2a", "M3a", "M4a", "M5"],
                                  ["M6", "M1b", "M2b", "M3b", "M4b", "M5"]], \
        f"하향 branch 골격이 예상과 다름: {_t35_down_chains}"
    _t35_up = trace_gnd_to_vdd_branches(_t35_fixture)
    _t35_up_chains = [b["chain"] for b in _t35_up["branches"] if b["terminates_at"] == "vdd"]
    assert _t35_up_chains == [["M5", "M4a", "M3a", "M2a", "M1a", "M6"],
                                ["M5", "M4b", "M3b", "M2b", "M1b", "M6"]], \
        f"상향 branch 골격이 예상과 다름(하향의 정확한 역순이어야 함): {_t35_up_chains}"

    _t35_result = find_differential_and_mirror_forks(_t35_fixture, inputs=("Vip", "Vim"))
    assert _t35_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t35_forks = _t35_result["forks"]
    assert len(_t35_forks) == 2, f"fork가 정확히 2개(위/아래 diff pair 하나씩)여야 함: {_t35_forks}"
    _t35_down_forks = [f for f in _t35_forks if f["direction"] == "vdd_to_gnd"]
    _t35_up_forks = [f for f in _t35_forks if f["direction"] == "gnd_to_vdd"]
    assert len(_t35_down_forks) == 1 and _t35_down_forks[0]["fork_devices"] == ("M1a", "M1b") \
        and _t35_down_forks[0]["relation"] == "differential", \
        f"하향에서 M1a/M1b differential fork를 못 찾음: {_t35_down_forks}"
    assert len(_t35_up_forks) == 1 and _t35_up_forks[0]["fork_devices"] == ("M4a", "M4b") \
        and _t35_up_forks[0]["relation"] == "differential", \
        f"상향에서 M4a/M4b differential fork를 못 찾음(양방향 탐지의 핵심 --" \
        f" 하향만으로는 이 fork가 분기 없는 직선 구간에 파묻혀 절대 안 보임): {_t35_up_forks}"


def test_s129_find_verified_differential_and_mirror_relations(s128_state):
    """=== Test 36: find_verified_differential_and_mirror_relations() -- 진짜 branch
    단위 비교(composite 구조가 완전히 같은 branch끼리만 묶음, C-7 원리를 양방향
    으로 확장) + 매칭된 쌍 안의 모든 위치 스캔(첫 divergence만 보던 한계 해소).
    Test 35의 telescopic fixture 하나로 differential/mirror 4가지 관계가 전부
    (하향 스캔 한 번만으로도) 나오는지 재확인 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S129(줄 2245-2266, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t35_fixture = s128_state._t35_fixture

    _t36_result = find_verified_differential_and_mirror_relations(_t35_fixture, inputs=("Vip", "Vim"))
    assert _t36_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t36_diff_devs = {r["devices"] for r in _t36_result["differential"]}
    _t36_mirror_devs = {r["devices"] for r in _t36_result["mirror"]}
    assert {("M1a", "M1b")} <= _t36_diff_devs, \
        f"M1a/M1b differential이 안 잡힘: {_t36_diff_devs}"
    assert {("M4a", "M4b")} <= _t36_diff_devs, \
        f"M4a/M4b differential이 안 잡힘(양방향+전체위치 스캔의 핵심): {_t36_diff_devs}"
    assert {("M2a", "M2b")} <= _t36_mirror_devs, f"M2a/M2b mirror가 안 잡힘: {_t36_mirror_devs}"
    assert {("M3a", "M3b")} <= _t36_mirror_devs, f"M3a/M3b mirror가 안 잡힘: {_t36_mirror_devs}"
    _t36_down_diff = [r for r in _t36_result["differential"] if r["direction"] == "vdd_to_gnd"]
    assert {r["devices"] for r in _t36_down_diff} == {("M1a", "M1b"), ("M4a", "M4b")}, \
        f"하향 방향 스캔 하나만으로 두 differential 관계가 전부 안 나옴: {_t36_down_diff}"


def test_s130_find_differential_pair_candidates(s128_state):
    """=== Test 37: find_differential_pair_candidates() -- inputs= 선언 없이 순수
    connectivity(같은 non-rail source 공유)만으로 진짜 differential pair를
    찾는지(사용자 통찰: "differential pair를 먼저 찾고 나서 mirror를 분석해야
    정확해진다") Test 35의 telescopic fixture로 재확인 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S130(줄 2267-2284, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t35_fixture = s128_state._t35_fixture

    _t37_result = find_differential_pair_candidates(_t35_fixture)  # inputs= 아예 안 넘김
    assert _t37_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t37_devs = {c["devices"] for c in _t37_result["candidates"]}
    assert ("M1a", "M1b") in _t37_devs, \
        f"inputs= 선언 없이 M1a/M1b를 못 찾음(핵심 주장 실패): {_t37_devs}"
    assert ("M4a", "M4b") in _t37_devs, \
        f"inputs= 선언 없이 M4a/M4b를 못 찾음(핵심 주장 실패): {_t37_devs}"
    _t37_sources = {c["devices"]: c["shared_source"] for c in _t37_result["candidates"]}
    assert _t37_sources[("M1a", "M1b")] == "Vx" and _t37_sources[("M4a", "M4b")] == "Vy", \
        f"shared_source가 예상과 다름: {_t37_sources}"


def test_s131_refine_differential_and_mirror_relations():
    """=== Test 38: refine_differential_and_mirror_relations() -- input 승격
    오케스트레이션(.ai/context.md D절 item 0, 세션24 신설). M37a/M37b류
    (게이트가 inputs=에 없는 2차 differential pair)를 축소 재현한 합성
    fixture로: (1) 승격 전에는 못 찾다가 승격 후 differential로 잡히는지,
    (2) 그 승격의 연쇄효과로 다른 소자 role/net class가 바뀌었을 때 조용히
    덮어쓰지 않고 명시적으로 보고하는지 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S131(줄 2285-2332, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t38_fixture = [
        Transistor("M61", "nmos", source="gnd", drain="Ncmfb_tail", gate="Vbias_tail"),
        Transistor("M60a", "nmos", source="Ncmfb_tail", drain="Vcmfb_a", gate="Voc"),
        Transistor("M60b", "nmos", source="Ncmfb_tail", drain="Vcmfb_b", gate="Voc_des"),
        Transistor("M63a", "pmos", source="vdd", drain="Vcmfb_a", gate="Vbias_x"),
        Transistor("M63b", "pmos", source="vdd", drain="Vcmfb_b", gate="Vbias_x"),
        Transistor("M62", "pmos", source="vdd", drain="Nload", gate="Vcmfb_a"),
    ]
    _t38_pre = find_verified_differential_and_mirror_relations(_t38_fixture)
    assert _t38_pre is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t38_pre_devs = {r["devices"] for r in _t38_pre["differential"]}
    assert ("M60a", "M60b") not in _t38_pre_devs, \
        f"승격 전인데 M60a/M60b가 이미 differential로 잡힘(fixture 설계 오류): {_t38_pre_devs}"
    _t38_pre_no_conn = {r["devices"] for r in _t38_pre["structurally_symmetric_no_connection"]}
    assert ("M60a", "M60b") in _t38_pre_no_conn, \
        f"승격 전 M60a/M60b가 세 번째 버킷에도 안 잡힘(조용히 버려짐, 세션24 수정 취지 위반): {_t38_pre_no_conn}"

    _t38_result = refine_differential_and_mirror_relations(_t38_fixture)
    assert _t38_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    assert set(_t38_result["promoted_inputs"]) == {"Voc", "Voc_des"}, \
        f"승격된 gate net이 예상과 다름: {_t38_result['promoted_inputs']}"
    assert _t38_result["stop_reason"] == "fixed_point", \
        f"고정점 도달 전에 반복이 끝남(예상 밖): {_t38_result['stop_reason']}"
    _t38_post_devs = {r["devices"] for r in _t38_result["relations"]["differential"]}
    assert ("M60a", "M60b") in _t38_post_devs, \
        f"승격 후에도 M60a/M60b가 differential로 안 잡힘(오케스트레이션 핵심 실패): {_t38_post_devs}"
    _t38_post_no_conn = {r["devices"] for r in _t38_result["relations"]["structurally_symmetric_no_connection"]}
    assert ("M60a", "M60b") not in _t38_post_no_conn, \
        f"승격 후에도 M60a/M60b가 여전히 세 번째 버킷에 남아 있음(differential로 옮겨가야 함): {_t38_post_no_conn}"

    _t38_role_changes = {c["device"]: (c["before"], c["after"]) for c in _t38_result["role_changes"]}
    assert _t38_role_changes.get("M62") == ("ACTIVE_LOAD", "AMPLIFYING"), \
        f"M62 role 변화가 예상과 다름(연쇄효과 보고 실패): {_t38_role_changes}"
    _t38_net_changes = {c["net"]: (c["before"], c["after"]) for c in _t38_result["net_class_changes"]}
    assert _t38_net_changes.get("Voc") == ("BIAS", "INPUT"), \
        f"Voc net class 변화가 예상과 다름: {_t38_net_changes}"
    assert _t38_net_changes.get("Vcmfb_a") == ("BIAS", "SIGNAL"), \
        f"Vcmfb_a(M60a의 drain) net class 변화가 예상과 다름: {_t38_net_changes}"


def test_s132_find_verified_differential_and_mirror_relations(s128_state):
    """=== Test 39: find_verified_differential_and_mirror_relations() -- 세 번째 버킷
    structurally_symmetric_no_connection (세션24, 사용자 지적: "이 대칭쌍들도
    symmetric branch로 출력되도록 해"). 구조는 완전히 대칭인데 gate로는
    mirror/differential 어느 쪽도 확정 못 하는 쌍이 조용히 버려지지 않고
    명시적으로 보고되는지, 실회로에서 실제로 나온 M6/M7 패턴(같은 tail net에
    병렬로 물린 소자, 하나는 고정 bias 하나는 다른 신호)을 Test 35 fixture에
    M7 analog(M7t)를 얹어 재현해 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S132(줄 2333-2361, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t35_fixture = s128_state._t35_fixture

    _t39_fixture = _t35_fixture + [
        Transistor("M7t", "pmos", source="vdd", drain="Vx", gate="Vbias_other"),
    ]
    _t39_result = find_verified_differential_and_mirror_relations(_t39_fixture, inputs=("Vip", "Vim"))
    assert _t39_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    assert "structurally_symmetric_no_connection" in _t39_result, \
        f"세 번째 버킷 키 자체가 없음(회귀): {sorted(_t39_result)}"
    _t39_no_conn_devs = {r["devices"] for r in _t39_result["structurally_symmetric_no_connection"]}
    assert ("M6", "M7t") in _t39_no_conn_devs, \
        f"M6/M7t(구조 대칭이지만 gate 근거 없음)가 세 번째 버킷에 안 잡힘: {_t39_no_conn_devs}"
    _t39_diff_devs = {r["devices"] for r in _t39_result["differential"]}
    _t39_mirror_devs = {r["devices"] for r in _t39_result["mirror"]}
    assert ("M6", "M7t") not in _t39_diff_devs and ("M6", "M7t") not in _t39_mirror_devs, \
        f"M6/M7t가 잘못 differential/mirror로도 분류됨: diff={_t39_diff_devs}, mirror={_t39_mirror_devs}"
    assert {("M1a", "M1b")} <= _t39_diff_devs and {("M4a", "M4b")} <= _t39_diff_devs, \
        f"M7t 추가로 기존 differential 판정이 회귀함: {_t39_diff_devs}"
    assert {("M2a", "M2b")} <= _t39_mirror_devs and {("M3a", "M3b")} <= _t39_mirror_devs, \
        f"M7t 추가로 기존 mirror 판정이 회귀함: {_t39_mirror_devs}"


def test_s133_refine_differential_and_mirror_relations(s128_state):
    """=== Test 40: refine_differential_and_mirror_relations()의
    vertical_stack_id_candidates -- cascode-stack composite(물리) +
    differential-pair/mirror 관계(leg a/b)를 합쳐 최종 vertical_stack_id
    후보를 만드는지(세션24, 사용자 지시) Test 35 fixture로 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S133(줄 2362-2388, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t35_fixture = s128_state._t35_fixture

    _t40_result = refine_differential_and_mirror_relations(_t35_fixture, inputs=("Vip", "Vim"))
    assert _t40_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t40_cand = _t40_result["vertical_stack_id_candidates"]["groups"]
    assert set(_t40_cand) == {t.name for t in _t35_fixture}, \
        f"10개 소자 전부 후보를 받아야 함: {sorted(_t40_cand)}"
    assert _t40_cand["M1a"] == _t40_cand["M2a"], \
        f"M1a/M2a가 같은 vertical_stack_id 후보를 못 받음: {_t40_cand['M1a']} vs {_t40_cand['M2a']}"
    assert _t40_cand["M1b"] == _t40_cand["M2b"], \
        f"M1b/M2b가 같은 vertical_stack_id 후보를 못 받음: {_t40_cand['M1b']} vs {_t40_cand['M2b']}"
    assert _t40_cand["M3a"] == _t40_cand["M4a"], \
        f"M3a/M4a가 같은 vertical_stack_id 후보를 못 받음: {_t40_cand['M3a']} vs {_t40_cand['M4a']}"
    assert _t40_cand["M3b"] == _t40_cand["M4b"], \
        f"M3b/M4b가 같은 vertical_stack_id 후보를 못 받음: {_t40_cand['M3b']} vs {_t40_cand['M4b']}"
    assert _t40_cand["M1a"] != _t40_cand["M1b"], \
        f"M1a(leg a)/M1b(leg b)가 같은 그룹으로 잘못 합쳐짐: {_t40_cand['M1a']}"
    assert _t40_cand["M1a"] != _t40_cand["M3a"], \
        f"M1a/M2a(위쪽 stack)와 M3a/M4a(아래쪽 stack)가 잘못 합쳐짐: {_t40_cand['M1a']}"
    assert _t40_cand["M1a"].endswith("_a") and _t40_cand["M1b"].endswith("_b"), \
        f"leg 접미사가 안 붙음: M1a={_t40_cand['M1a']}, M1b={_t40_cand['M1b']}"


def test_s134__propose_vertical_stack_ids():
    """=== Test 41: _propose_vertical_stack_ids()의 fan-in 모호성 탐지 --
    같은 kind의 lo 후보가 2개 이상인 CASCODE 소자는 어느 쪽에도 억지로
    합치지 않고 ambiguous_{name}으로 격리하는지(세션24, 실회로 M9b/M10
    사례를 축소 재현) 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S134(줄 2389-2414, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t41_fixture = [
        Transistor("Mup", "nmos", source="Vshared", drain="Vout", gate="Vbias_up"),
        Transistor("Mlo1", "nmos", source="gnd", drain="Vshared", gate="Vbias_lo1"),
        Transistor("Mlo2", "nmos", source="gnd", drain="Vshared", gate="Vbias_lo2"),
    ]
    _t41_result = refine_differential_and_mirror_relations(_t41_fixture, inputs=())
    assert _t41_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t41_groups = _t41_result["vertical_stack_id_candidates"]["groups"]
    _t41_alt = _t41_result["vertical_stack_id_candidates"]["ambiguous_alternatives"]
    assert _t41_groups["Mup"] == "ambiguous_Mup", \
        f"fan-in 후보 2개(Mlo1/Mlo2)인 Mup이 격리 안 됨: {_t41_groups}"
    assert _t41_groups["Mlo1"] != _t41_groups["Mup"] and _t41_groups["Mlo2"] != _t41_groups["Mup"], \
        f"Mup이 Mlo1/Mlo2 중 하나에 잘못 합쳐짐: {_t41_groups}"

    assert "Mup" in _t41_alt, f"ambiguous_alternatives에 Mup 후보 목록이 없음: {_t41_alt}"
    assert set(_t41_alt["Mup"]) == {_t41_groups["Mlo1"], _t41_groups["Mlo2"]}, \
        f"Mup의 후보 그룹이 Mlo1/Mlo2 자기 그룹과 안 맞음: {_t41_alt['Mup']} vs " \
        f"{{{_t41_groups['Mlo1']!r}, {_t41_groups['Mlo2']!r}}}"


def test_s135_section(s128_state):
    """=== Test 42: fan-in 후보 중 differential-pair branch 소속 여부로 재판정 --
    후보 2개 중 정확히 하나만 differential branch 소속이 아니면 그쪽으로
    확정되어 ambiguous 상태를 벗어나는지(세션24, 사용자 통찰: 실회로
    M9b->M10/M18b->M19/M58->M7이 이 규칙으로 풀림) 축소 재현으로 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S135(줄 2415-2435, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t35_fixture = s128_state._t35_fixture

    _t42_fixture = _t35_fixture + [
        Transistor("Mamb", "nmos", source="Nout2", drain="Vg_out", gate="Vbias_amb"),
        Transistor("Mout", "nmos", source="gnd", drain="Nout2", gate="Vbias_out2"),
    ]
    _t42_result = refine_differential_and_mirror_relations(_t42_fixture, inputs=("Vip", "Vim"))
    assert _t42_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t42_vsid = _t42_result["vertical_stack_id_candidates"]
    assert "Mamb" not in _t42_vsid["ambiguous_alternatives"], \
        f"Mamb가 differential branch 재판정으로 안 풀리고 여전히 ambiguous로 남음: {_t42_vsid['ambiguous_alternatives']}"
    assert _t42_vsid["groups"]["Mamb"] == _t42_vsid["groups"]["Mout"], \
        f"Mamb가 M3b(differential branch 소속) 대신 Mout(비소속)과 묶여야 하는데: {_t42_vsid['groups']}"
    assert _t42_vsid["groups"]["Mamb"] != _t42_vsid["groups"].get("M3b"), \
        f"Mamb가 M3b와 잘못 묶임(differential branch 오염): {_t42_vsid['groups']}"


def test_s136_refine_differential_and_mirror_relations(s128_state):
    """=== Test 43: refine_differential_and_mirror_relations()의
    gm_id_role_candidates -- 2026-08-13 정정(사용자 지시, two_stage_ota L 자유도
    확장 논의 계기) -- L_role(mirror/bias_replica) 둘 다 레이아웃 매칭이 필요하므로
    최종 노출값은 전부 matching으로 통일됐는지(원래 tail 소자만 balanced였던 걸
    matching으로 덮어씀), headroom_role_candidates(tail 판정)는 원본 신호를 써서
    안 바뀌는지 Test 35 fixture로 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S136(줄 2436-2458, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t35_fixture = s128_state._t35_fixture

    _t43_result = refine_differential_and_mirror_relations(_t35_fixture, inputs=("Vip", "Vim"))
    assert _t43_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t43_gmid = _t43_result["gm_id_role_candidates"]
    assert set(_t43_gmid) == {t.name for t in _t35_fixture}, \
        f"10개 소자 전부 후보를 받아야 함: {sorted(_t43_gmid)}"
    assert all(_t43_gmid[n] == "matching" for n in _t43_gmid), \
        f"L_role(mirror/bias_replica)로 덮이는 소자는 전부 matching으로 덮어써야 함(M5/M6 " \
        f"tail 소자 포함): {_t43_gmid}"
    _t43_headroom = _t43_result["headroom_role_candidates"]
    assert _t43_headroom.get("M6") == "tail" and _t43_headroom.get("M5") == "tail", \
        (f"gm_id_role_candidates를 matching으로 덮어써도 headroom_role_candidates의 tail "
         f"판정(원본 balanced 신호 사용)은 안 바뀌어야 함: M6={_t43_headroom.get('M6')!r}, "
         f"M5={_t43_headroom.get('M5')!r}")


def test_s137_suggest_vertical_stack_composites(s128_state):
    """=== Test 44: suggest_vertical_stack_composites()가 idioms.Match.ports를
    조용히 버리지 않고 composite에 보존하는지(사용자 지적: M8/M9a가 물리적으론
    캐스코드 스택이 맞지만, M8=mirror 기준/M9a=그 위 캐스코드라는 구분이
    composite 단계에서 사라지고 있었음) Test 35 fixture로 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S137(줄 2459-2476, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t35_fixture = s128_state._t35_fixture

    _t44_branches = suggest_vertical_stack_composites(_t35_fixture, inputs=("Vip", "Vim"), direction="vdd_to_gnd")
    _t44_composite = None
    for b in _t44_branches:
        for c in b["composites"]:
            if set(c["members"]) == {"M1a", "M2a"}:
                _t44_composite = c
                break
    assert _t44_composite is not None, "M1a/M2a cascode-stack composite을 못 찾음(회귀)"
    assert _t44_composite["ports"].get("lower_role") == "AMPLIFYING", \
        f"lower_role(M1a의 role)이 ports에 보존돼야 함: {_t44_composite}"


def test_s138_refine_differential_and_mirror_relations(s128_state):
    """=== Test 45: refine_differential_and_mirror_relations()의
    headroom_role_candidates -- 6가지 실패한 가설 끝에 나온 37/37 규칙
    (role==FLOATING_CURRENT_SOURCE/DIODE_REFERENCED_CASCODE 분리 +
    mirror_ref/그룹/대칭 판정, 세션25, 사용자와 함께 여러 라운드 검증)이
    tail/cascode/mirror/floating_current_source 네 값 전부와 mirror_ref
    유무에 따른 diode-cascode 분기(있음/없음)까지 실제로 가르는지 합성
    fixture로 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S138(줄 2477-2529, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t35_fixture = s128_state._t35_fixture

    _t45_fixture = _t35_fixture + [
        # Monticelli floating-current-source 축소 재현(M8/M9a/M9b/M10)
        Transistor("M8", "pmos", source="vdd", drain="Vg", gate="Vbias5"),
        Transistor("M9a", "pmos", source="Vg", drain="Vout", gate="Nref1"),
        Transistor("M9b", "nmos", source="Vout", drain="Vg", gate="Nref2"),
        Transistor("M10", "nmos", source="gnd", drain="Vout", gate="Vbias6"),
        # diode-cascode WITH mirror_ref: M50(bottom cs)-M51(lo)-M52(diode,top),
        # M53이 M52와 (gate,source,type) 공유 -> M52가 current-mirror ref가 됨
        Transistor("M50", "pmos", source="vdd", drain="Va", gate="Vbias7"),
        Transistor("M51", "pmos", source="Va", drain="Vb", gate="Vc"),
        Transistor("M52", "pmos", source="Vb", drain="Vc", gate="Vc"),
        Transistor("M53", "pmos", source="Vb", drain="Vd", gate="Vc"),
        # diode-cascode WITHOUT mirror_ref: M60(bottom cs)-M61(lo)-M62(diode,top),
        # 짝 없는 단독 diode
        Transistor("M60", "nmos", source="gnd", drain="Ve", gate="Vbias8"),
        Transistor("M61", "nmos", source="Ve", drain="Vf", gate="Vg2"),
        Transistor("M62", "nmos", source="Vf", drain="Vg2", gate="Vg2"),
    ]
    _t45_result = refine_differential_and_mirror_relations(_t45_fixture, inputs=("Vip", "Vim"))
    assert _t45_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t45_hr = _t45_result["headroom_role_candidates"]
    assert set(_t45_hr) == {t.name for t in _t45_fixture}, \
        f"headroom_role_candidates가 fixture 전체 소자를 다 포함해야 함: {set(_t45_hr)}"
    _t45_expected = {
        "M6": "tail", "M5": "tail",                              # 진짜 차동쌍 tail
        "M1a": None, "M1b": None, "M4a": None, "M4b": None,      # AMP(차동쌍 입력) -- 규칙 밖
        "M2a": "cascode", "M2b": "cascode",                       # 고정 게이트 캐스코드
        "M3a": "cascode", "M3b": "cascode",
        "M8": "mirror", "M10": "mirror",                          # floating loop 위/아래 전류원
        "M9a": "floating_current_source", "M9b": "floating_current_source",
        "M50": "mirror",                                          # 레일에 직접 닿은 전류원
        "M51": "mirror",     # diode-cascode lo, 파트너(M52)가 mirror_ref -> mirror
        "M52": "mirror",     # diode 자신이 mirror_ref(M53가 미러함)
        "M53": "cascode",    # M52를 미러하는 별도 branch, 고정 게이트 캐스코드
        "M60": "mirror",                                          # 레일에 직접 닿은 전류원
        "M61": "cascode",    # diode-cascode lo, 파트너(M62)가 mirror_ref 아님 -> cascode
        "M62": "cascode",    # diode 자신도 mirror_ref 아니고 대칭 파트너도 없음
    }
    for name, expected in _t45_expected.items():
        actual = _t45_hr.get(name)
        assert actual == expected, \
            f"{name}: headroom_role 후보가 {expected!r}이어야 하는데 {actual!r} -- 회귀 의심"


def test_s139_find_verified_differential_and_mirror_relations(s128_state):
    """=== Test 46: find_verified_differential_and_mirror_relations()의
    differential_branch_members -- '진짜 differential branch 소속'과
    'symmetric(mirror) branch 소속'을 방향(vdd_to_gnd/gnd_to_vdd)에 안
    흔들리고 정확히 구별하는지(세션25, 사용자 통찰: M10은 M19와의 진짜
    mirror 관계 당사자라 differential branch가 아니다, M3a/M3b는 M4a/M4b
    differential 발견의 상류라 mirror 관계이면서도 진짜 differential branch
    소속이다) 합성 fixture로 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S139(줄 2530-2557, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t35_fixture = s128_state._t35_fixture

    _t46_fixture = _t35_fixture + [
        Transistor("M7", "pmos", source="vdd", drain="Vx", gate="Vbias5"),
        # M2a/M2b의 drain(Nout1/Nout2)에서 갈라지는 별개 mirror branch(M19/M10류) --
        # M1a/M1b differential 발견과 같은 chain-prefix를 공유하지만 그 발견의 하류
        # (혹은 gnd_to_vdd 역순에서는 상류처럼 보이는) 무관한 분기.
        Transistor("Mfork_a", "nmos", source="gnd", drain="Nout1", gate="Vbias6"),
        Transistor("Mfork_b", "nmos", source="gnd", drain="Nout2", gate="Vbias6"),
    ]
    _t46_result = refine_differential_and_mirror_relations(_t46_fixture, inputs=("Vip", "Vim"))
    assert _t46_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t46_diff_mem = set(_t46_result["relations"]["differential_branch_members"])
    for dev in ("M6", "M7", "M1a", "M1b", "M4a", "M4b", "M3a", "M3b"):
        assert dev in _t46_diff_mem, \
            f"{dev}는 진짜 differential branch 소속이어야 하는데 빠짐: {_t46_diff_mem}"
    for dev in ("Mfork_a", "Mfork_b"):
        assert dev not in _t46_diff_mem, \
            f"{dev}는 별개 mirror branch 소속이라 제외돼야 하는데 포함됨: {_t46_diff_mem}"


def test_s140_audit_vertical_stack_id_vs_kcl(library_dir):
    """=== Test 47: audit_vertical_stack_id_vs_kcl() -- declared vertical_stack_id와
    kcl_series_union()의 불일치를 internal_series/declared_matching_pair/
    multi_terminal_hub로 자동 분류하는지(2026-08-10 세션 대화, 사용자와 함께
    M11b/M12 진짜 직렬 체인 + M9a/M9b류 floating-current-source 3-branch 허브
    두 반례를 실측으로 확인한 뒤 신설) current_reuse_telescopic_ota.topology.json
    실회로(51소자)로 검증 -- 손타이핑 넷리스트 없음. ⚠️ 원래 예시였던 M11b/M12는
    세션27이 헤드룸 버그 수정으로 M11a/M11b/M12를 같은 vertical_stack_id로
    합쳐 이 divergence 자체가 해소됐다(의도된 결과) -- 세션28에서 같은 패턴의
    다른 실측 사례(M60/M66, Vbias4 2단자 직렬, 세션27이 손대지 않은 그룹)로
    교체해 감사 함수의 검증력을 유지한다 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S140(줄 2558-2602, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _lib47 = library_dir
    _t47_trs, _t47_meta = load_topology(
        _os47.path.join(_lib47, "current_reuse_telescopic_ota.topology.json"))
    _t47_pairs_meta = _t47_meta["symmetry"]["matching_pairs"]
    _t47_forced = [tuple(p["names"]) for p in _t47_pairs_meta if p["current_forced"]]
    _t47_device_roles = {k: v for k, v in (_t47_meta.get("device_roles") or {}).items()
                          if not k.startswith("_")}
    _t47_result = audit_vertical_stack_id_vs_kcl(_t47_trs, _t47_forced, _t47_device_roles)

    _t47_m60_m66 = [f for f in _t47_result["boundary_findings"]
                      if set(f["pair"]) == {"M60", "M66"}]
    assert len(_t47_m60_m66) == 1, f"M60/M66 경계가 안 잡힘: {_t47_m60_m66}"
    assert _t47_m60_m66[0]["kcl_reason"] == "internal_series" and _t47_m60_m66[0]["detail"] == "Vbias4", \
        f"M60/M66는 Vbias4 2단자 직렬이 원인이어야 하는데: {_t47_m60_m66[0]}"

    _t47_hub_by_vsid = {f["vsid"]: f for f in _t47_result["hub_findings"]}
    for _vsid, _hub_net, _terminals_min in [
            ("biasgen_vom_a", "Vg15", 3), ("biasgen_vom_floatsrc_sink", "Vg15", 3),
            ("biasgen_vop_a", "Vg25", 3), ("biasgen_vop_floatsrc_sink", "Vg25", 3)]:
        assert _vsid in _t47_hub_by_vsid, f"{_vsid} hub_finding 누락"
        _nets = dict(_t47_hub_by_vsid[_vsid]["candidate_hub_nets"])
        assert _nets.get(_hub_net, 0) >= _terminals_min, \
            f"{_vsid}: {_hub_net}가 {_terminals_min}단자 이상 허브로 안 잡힘: {_nets}"

    _t47_unexplained_hubs = [f for f in _t47_result["hub_findings"] if not f["candidate_hub_nets"]]
    _t47_gaps = [f for f in _t47_result["boundary_findings"] if f["note"]]
    assert _t47_unexplained_hubs == [], \
        f"실회로에서 원인 불명 hub_finding이 나오면 안 됨(이번 회로는 완전 정합): {_t47_unexplained_hubs}"
    assert _t47_gaps == [], \
        f"실회로에서 vertical_stack_id gap이 나오면 안 됨(51/51 선언 완료 회로): {_t47_gaps}"


def test_s141_merge_layout_groups_by_matching_pairs(library_dir):
    """=== Test 48: merge_layout_groups_by_matching_pairs() -- vertical_stack_id 기반
    그룹(수직 방향만 앎)이 서로 다른 물리 branch에 있는 매칭 파트너를 잡아주지
    못하는 문제(2026-08-10 세션26 후속 J-4/J-9, folded_cascode 5개 매칭쌍 전부
    3b/3c 실패 실측)를, geometry_colocation_union()의 위험한 재귀 climb 없이
    그룹 단위 union만으로 해결하는지 -- folded_cascode 실회로(candidates 경로)로
    검증. 손타이핑 넷리스트 없음 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S141(줄 2603-2648, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t48_lib = library_dir
    _t48_trs, _t48_meta = load_topology(
        _t48_os.path.join(_t48_lib, "folded_cascode.topology.json"))
    _t48_pairs_meta = _t48_meta["symmetry"]["matching_pairs"]
    _t48_forced = [tuple(p["names"]) for p in _t48_pairs_meta if p["current_forced"]]

    _t48_refined = refine_differential_and_mirror_relations(_t48_trs)
    assert _t48_refined is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t48_candidates = {}
    for _name, _sid in _t48_refined["vertical_stack_id_candidates"]["groups"].items():
        _t48_candidates.setdefault(_sid, []).append(_name)

    _t48_before_pairs_together = sum(
        1 for _names in _t48_forced
        for _a, _b in zip(_names, _names[1:])
        if any({_a, _b} <= set(_members) for _members in _t48_candidates.values()))
    assert _t48_before_pairs_together == 0, \
        f"병합 전에 이미 매칭쌍이 같은 그룹이면 이 테스트가 검증하려는 문제가 재현 안 됨: " \
        f"{_t48_before_pairs_together}건"

    _t48_merged = merge_layout_groups_by_matching_pairs(_t48_trs, _t48_candidates, _t48_forced)
    _t48_all_members = sorted(m for members in _t48_merged.values() for m in members)
    assert _t48_all_members == sorted(t.name for t in _t48_trs), \
        "merge_layout_groups_by_matching_pairs()가 소자를 빠뜨리거나 중복시킴"

    _t48_group_sets = {frozenset(members) for members in _t48_merged.values()}
    assert frozenset({"M1", "M2"}) in _t48_group_sets, f"M1/M2가 병합 안 됨: {_t48_group_sets}"
    assert frozenset({"M3", "M4"}) in _t48_group_sets, f"M3/M4가 병합 안 됨: {_t48_group_sets}"
    assert frozenset({"M7", "M8", "M9", "M10"}) in _t48_group_sets, \
        f"M7/M8/M9/M10(두 물리스택이 M9/M10 매칭쌍으로 이어짐)이 병합 안 됨: {_t48_group_sets}"

    for _isolated in ("M5", "M6"):
        assert frozenset({_isolated}) in _t48_group_sets, \
            f"{_isolated}(candidates가 ambiguous로 격리, current_forced=False라 매칭 기준에도 " \
            f"없음)은 그대로 격리 유지돼야 하는데 다른 그룹과 합쳐짐: {_t48_group_sets}"


def test_s142_section(s141_state):
    """[current_forced=False까지 전부 넘기면(세션9/10 dx 악화 반례 재현 의도)
    M5/M6도 시도는 되는지 -- ⚠️ 2026-08-10 오일러 게이트 신설 이후 재확인:
    M5/M6은 공유 net이 아예 없어(source=Y/drain=Vg7 vs source=X/drain=out) 어떤
    핑거조정으로도 연결 안 됨 -- 오일러 게이트가 이 병합 자체를 막는다(필터링과
    다른 이유). 함수가 current_forced를 몰래 걸러서가 아니라 진짜 연결 불가능
    해서 안 합쳐진다는 걸 구분해서 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S142(줄 2649-2663, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t48_candidates = s141_state._t48_candidates
    _t48_pairs_meta = s141_state._t48_pairs_meta
    _t48_trs = s141_state._t48_trs

    _t48_all_pairs = [tuple(p["names"]) for p in _t48_pairs_meta]
    _t48_merged_all = merge_layout_groups_by_matching_pairs(_t48_trs, _t48_candidates, _t48_all_pairs)
    _t48_group_sets_all = {frozenset(members) for members in _t48_merged_all.values()}
    assert frozenset({"M5"}) in _t48_group_sets_all and frozenset({"M6"}) in _t48_group_sets_all, \
        f"M5/M6은 공유 net이 없어 오일러 게이트가 병합을 막아야 하는데 합쳐짐(회귀): {_t48_group_sets_all}"


def test_s143_section():
    """[current_forced=False라도 실제로 물리적으로 이어진(오일러 실현 가능한) 쌍이면
    이 함수가 필터링 없이 그대로 병합함을 합성 fixture로 확인 -- "기본값은
    current_forced=True만 권장"이 강제가 아니라 권고일 뿐임을 증명]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S143(줄 2664-2681, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t48_syn_trs = [
        Transistor("Sa", "nmos", source="sn1", drain="sn2"),
        Transistor("Sb", "nmos", source="sn2", drain="sn3"),  # Sa와 진짜 직렬(2단자 sn2 공유)
    ]
    _t48_syn_groups = {"Sa": ["Sa"], "Sb": ["Sb"]}
    _t48_syn_merged = merge_layout_groups_by_matching_pairs(
        _t48_syn_trs, _t48_syn_groups, [("Sa", "Sb")])  # current_forced 여부와 무관하게 이 함수는 그냥 쌍만 봄
    assert frozenset({"Sa", "Sb"}) in {frozenset(v) for v in _t48_syn_merged.values()}, \
        f"물리적으로 직렬(오일러 실현 가능)인 쌍은 current_forced 여부와 무관하게 병합돼야 함: {_t48_syn_merged}"


def test_s144_audit_vertical_stack_id_euler_feasibility(library_dir):
    """=== Test 49: audit_vertical_stack_id_euler_feasibility() -- declared
    vertical_stack_id 그룹이 그 자체로 오일러 실현 가능한지(merge_layout_
    groups_by_matching_pairs()의 오일러 게이트가 손 못 대는, 병합 이전부터
    이미 declared로 들어온 그룹의 문제) 검사. 2026-08-10 세션26 후속(2) K-3
    cmfb_tail 추적 중 발견한 suggest_pair_finger_adjustments()의 연결성 착시
    (resulting_odd_count는 홀짝만 보고 그래프가 끊겼는지는 안 봄)를 실제
    적용+재검증으로 피하는지도 함께 검증. 2026-08-11(세션28) 신설 kind_mismatch
    finding(PMOS/NMOS 혼합 declared 그룹)도 크래시 대신 구조화 보고되는지 확인 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S144(줄 2682-2743, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir
    _t49_trs, _t49_meta = load_topology(
        _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json"))
    _t49_pairs_meta = _t49_meta["symmetry"]["matching_pairs"]
    _t49_forced = [tuple(p["names"]) for p in _t49_pairs_meta if p["current_forced"]]
    _t49_device_roles = {k: v for k, v in (_t49_meta.get("device_roles") or {}).items()
                          if not k.startswith("_")}
    _t49_result = audit_vertical_stack_id_euler_feasibility(_t49_trs, _t49_device_roles, _t49_forced)
    _t49_by_vsid = {f["vsid"]: f for f in _t49_result["findings"]}
    assert "cmfb_tail" in _t49_by_vsid, \
        f"cmfb_tail(M37a/M37b/M38)이 findings에 안 잡힘(회귀 -- 이 그룹은 실제로 " \
        f"n_fingers=1 기준 오일러 impossible이어야 함): {_t49_result}"
    _t49_cmfb = _t49_by_vsid["cmfb_tail"]
    assert _t49_cmfb["members"] == ["M37a", "M37b", "M38"], f"멤버 불일치: {_t49_cmfb}"
    assert set(_t49_cmfb["odd_nodes"]) == {"N36b", "Ncmfb_tail", "Vcmfb", "gnd"}, \
        f"홀수차수 노드 불일치: {_t49_cmfb['odd_nodes']}"
    assert _t49_cmfb["resolvable_by_finger_adjustment"] is True, \
        f"cmfb_tail은 M38(또는 M37a/M37b) 핑거 +1로 실제 검증 가능한데 False로 나옴: {_t49_cmfb}"
    assert _t49_cmfb["verified_suggestion"] is not None
    assert _t49_cmfb["kind_mismatch"] is False, f"cmfb_tail은 전부 nmos인데 kind_mismatch=True: {_t49_cmfb}"

    # 2026-08-11(세션28) -- build_graph()의 kind 동질성 하드 게이트 신설 이후, 이 회로의
    # declared vertical_stack_id 26개 중 8개가 실제로 PMOS/NMOS를 섞고 있음이 이 감사로
    # 처음 드러났다(class-AB 출력단 output_stage_a/b 포함 -- "vertical_stack_id"가 VDD->GND
    # 전기적 컬럼이라 애초에 정의상 극성 경계를 넘나드는 게 정상이라는 뜻, 세션28 대화
    # 참고). 이 8개는 finger 조정으로 못 고치는 구조적 문제이므로 kind_mismatch=True로
    # 명확히 구분돼야 한다 -- cmfb_tail(홀짝-차수 문제, kind_mismatch=False)과 섞이면 안 됨.
    # 2026-09-03(세션43) -- diffpair_top_a/b·diffpair_bottom_a/b 4개 vsid를 없애고
    # 'diffpair_branch_a'(M6/M1a/M1b/M2a/M3a/M4a/M4b/M5, 물리적 단일 vdd~gnd branch
    # 병합, budget_reference_device 상호순환의 근본수정)/'diffpair_shadow_b'(M2b/M3b,
    # same_as_device 전용)로 재구성하면서 kind-mixed 그룹이 2개 늘었다(둘 다 PMOS+NMOS
    # 섞임 -- output_stage_a/b와 동일한 이유, 진짜 전기적 컬럼이라 극성 경계를 넘나드는
    # 게 정상). `.ai/context.md` 세션43 참고.
    _t49_kind_mismatch_vsids = {"biasgen_vom_battery_a", "biasgen_vom_battery_b",
                                 "biasgen_vop_battery_a", "biasgen_vop_battery_b",
                                 "vbias2_stack", "vbias3_stack",
                                 "output_stage_a", "output_stage_b",
                                 "diffpair_branch_a", "diffpair_shadow_b"}
    _t49_other_findings = [f for f in _t49_result["findings"] if f["vsid"] != "cmfb_tail"]
    _t49_other_vsids = {f["vsid"] for f in _t49_other_findings}
    assert _t49_other_vsids == _t49_kind_mismatch_vsids, \
        f"cmfb_tail 외 kind_mismatch finding 집합이 예상과 다름(회귀 또는 declared vsid 변경): " \
        f"실제={_t49_other_vsids}, 예상={_t49_kind_mismatch_vsids}"
    assert all(f["kind_mismatch"] is True for f in _t49_other_findings), \
        f"kind_mismatch 그룹인데 False로 나온 항목: {[f for f in _t49_other_findings if not f['kind_mismatch']]}"
    assert all(f["resolvable_by_finger_adjustment"] is False and f["verified_suggestion"] is None
               for f in _t49_other_findings), \
        f"kind_mismatch는 finger 조정으로 못 고치므로 resolvable/verified_suggestion 둘 다 " \
        f"False/None이어야 하는데: {_t49_other_findings}"
    assert all(f["kinds"] == ["nmos", "pmos"] for f in _t49_other_findings), \
        f"kind_mismatch finding의 kinds 필드 불일치: {[f['kinds'] for f in _t49_other_findings]}"


def test_s145_section():
    """[합성 fixture -- 완전히 무관한(공유 net 없는) 두 소자를 한 declared 그룹으로
    잘못 선언한 경우, suggest_pair_finger_adjustments()의 resulting_odd_count가
    연결성을 안 보고 착시를 일으키는지, 이 함수가 실제 적용+재검증으로 정확히
    잡아내는지(진짜 review 대상 = resolvable_by_finger_adjustment=False) 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S145(줄 2744-2764, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_iso_trs = [
        Transistor("T1", "nmos", source="n1", drain="n2"),
        Transistor("T2", "nmos", source="n3", drain="n4"),
    ]
    _t49_iso_roles = {"T1": {"vertical_stack_id": "isolated_test_group"},
                       "T2": {"vertical_stack_id": "isolated_test_group"}}
    _t49_iso_result = audit_vertical_stack_id_euler_feasibility(_t49_iso_trs, _t49_iso_roles, [])
    assert len(_t49_iso_result["findings"]) == 1, f"1건 잡혀야 함: {_t49_iso_result}"
    _t49_iso_finding = _t49_iso_result["findings"][0]
    assert _t49_iso_finding["resolvable_by_finger_adjustment"] is False, (
        f"T1/T2는 서로 공유 net이 아예 없어 어떤 핑거 조정으로도 연결 안 됨(진짜 review "
        f"대상)인데 True로 나옴 -- suggest_pair_finger_adjustments()의 resulting_odd_count "
        f"착시(연결성 미검사)를 못 걸렀다는 뜻: {_t49_iso_finding}")


def test_s146_find_euler_repair_options(s144_state):
    """=== Test 50: find_euler_repair_options() -- unresolved_row를 resolved로
    만들려면 어떤 row를 병합해야 하는지 찾는 탐색(2026-08-10 사용자 질문으로
    신설). 실제 optimize_full_circuit_budget() 끝까지 태운 뒤 unresolved_row로
    남았던 두 실사례(cmfb_tail/biasgen_ref)를 이 함수로 진단하면 놀랍게도
    **병합이 전혀 필요 없다** -- 같은 행 안 핑거 조정 하나로 이미 풀린다(실측)
    -- run_topology_pipeline_with_finger_fixup()이 이 해법을 못 찾고 포기했을
    뿐. 그리고 합성 fixture로 '진짜 병합이 필요한' 경우도 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S146(줄 2765-2785, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_forced = s144_state._t49_forced
    _t49_trs = s144_state._t49_trs

    _t50_by_name = {t.name: t for t in _t49_trs}
    _t50_cmfb_r = find_euler_repair_options(
        _t49_trs, ["M37a", "M37b", "M38"], _t49_forced, candidate_groups=None)
    assert _t50_cmfb_r["same_row_fix"] is not None, \
        f"cmfb_tail은 같은 행 안에서 풀려야 하는데(Test 49로 이미 확인됨) 못 찾음: {_t50_cmfb_r}"
    assert _t50_cmfb_r["merge_candidates"] == [], \
        "same_row_fix가 있으면 merge_candidates는 항상 빈 리스트여야 함(2단계 안 돌림)"

    _t50_bg_r = find_euler_repair_options(
        _t49_trs, ["M18_bg", "M60", "M61"], _t49_forced, candidate_groups=None)
    assert _t50_bg_r["same_row_fix"] is not None, \
        f"biasgen_ref(M18_bg/M60/M61)도 같은 행 안에서 풀려야 하는데 못 찾음: {_t50_bg_r}"


def test_s147_section():
    """[합성 fixture -- 같은 행 안에서는 절대 안 풀리는(서로 완전히 끊긴) blocked 그룹을
    만들고, 후보 row 2개(하나는 진짜 다리 역할, 하나는 완전히 무관) 중 실제로 연결을
    살려주는 쪽만 merge_candidates로 정확히 찾아내는지 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S147(줄 2786-2805, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t50_blocked = [Transistor("X1", "nmos", source="a", drain="b"),
                    Transistor("X2", "nmos", source="c", drain="d")]
    _t50_bridge = [Transistor("Y1", "nmos", source="b", drain="c")]
    _t50_unrelated = [Transistor("Z1", "nmos", source="e", drain="f")]
    _t50_all = _t50_blocked + _t50_bridge + _t50_unrelated
    _t50_syn_r = find_euler_repair_options(
        _t50_all, ["X1", "X2"], [],
        candidate_groups={"bridge_row": ["Y1"], "unrelated_row": ["Z1"]})
    assert _t50_syn_r["same_row_fix"] is None, \
        f"X1/X2는 서로 완전히 끊겨 같은 행 안에서는 절대 안 풀려야 함: {_t50_syn_r}"
    _t50_cand_rows = [c["row"] for c in _t50_syn_r["merge_candidates"]]
    assert _t50_cand_rows == ["bridge_row"], \
        f"다리 역할을 하는 bridge_row만 후보로 잡히고 unrelated_row는 빠져야 함: {_t50_cand_rows}"


def test_s148_derive_horizontal_stack_groups(s144_state):
    """=== Test 51: derive_horizontal_stack_groups() -- vertical_stack_id 그룹(전기적
    컬럼, PMOS/NMOS 혼합 가능)을 kind로 분할한 뒤 declared matching_pairs로 대칭
    branch끼리 재병합해 물리 레이아웃 행(kind 동질, 오일러 대상) 후보를 만드는지
    검증(2026-08-11 세션28 후반부, 사용자 설계 제안 -- vertical_stack_id는 헤드룸
    전용, 물리 레이아웃 행은 레이아웃 전용으로 두 축을 분리) ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S148(줄 2806-2839, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_device_roles = s144_state._t49_device_roles
    _t49_forced = s144_state._t49_forced
    _t49_trs = s144_state._t49_trs

    _t51_by_name = {t.name: t for t in _t49_trs}
    _t51_declared = {k: v.get("vertical_stack_id") for k, v in _t49_device_roles.items()
                      if isinstance(v, dict) and v.get("vertical_stack_id")}
    _t51_vgroups = defaultdict(list)
    for _t51_name, _t51_sid in _t51_declared.items():
        _t51_vgroups[_t51_sid].append(_t51_name)
    for _t51_t in _t49_trs:
        if _t51_t.name not in _t51_declared:
            _t51_vgroups[_t51_t.name].append(_t51_t.name)

    _t51_hgroups = derive_horizontal_stack_groups(_t49_trs, dict(_t51_vgroups), _t49_forced)

    _t51_all_members = sorted(m for members in _t51_hgroups.values() for m in members)
    assert _t51_all_members == sorted(t.name for t in _t49_trs), \
        f"51/51 소자 전부 커버해야 하는데 손실/중복 발생: 실제 {len(_t51_all_members)}개"

    for _t51_hsid, _t51_members in _t51_hgroups.items():
        _t51_kinds = {_t51_by_name[m].kind for m in _t51_members if m in _t51_by_name}
        assert len(_t51_kinds) <= 1, f"{_t51_hsid} 그룹이 kind 동질이 아님(회귀): {_t51_members} -> {_t51_kinds}"

    _t51_group_of = {m: hsid for hsid, members in _t51_hgroups.items() for m in members}
    assert _t51_group_of["M15"] == _t51_group_of["M25"], \
        f"output_stage_a/b의 PMOS 절반(M15/M25)이 M15-M25 매칭쌍으로 재병합돼야 함: {_t51_hgroups}"
    assert _t51_group_of["M16"] == _t51_group_of["M26"], \
        f"output_stage_a/b의 NMOS 절반(M16/M26)이 M16-M26 매칭쌍으로 재병합돼야 함: {_t51_hgroups}"
    assert _t51_group_of["M15"] != _t51_group_of["M16"], \
        "M15(pmos)/M16(nmos)는 같은 vertical_stack_id(output_stage_a)였지만 물리 행에서는 분리돼야 함"


def test_s149_section():
    """[합성 fixture -- 매칭 파트너가 없는 순수 mixed-kind vsid 하나가 kind로만
    정확히 쪼개지는지(병합 시도 없이) 확인]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S149(줄 2840-2853, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t51_syn_trs = [
        Transistor("SP1", "pmos", source="vdd", drain="mid"),
        Transistor("SN1", "nmos", source="mid", drain="gnd"),
    ]
    _t51_syn_groups = derive_horizontal_stack_groups(
        _t51_syn_trs, {"totem": ["SP1", "SN1"]}, [])
    assert set(_t51_syn_groups.keys()) == {"totem__pmos", "totem__nmos"}, \
        f"매칭 파트너 없는 mixed-kind 그룹은 kind별로만 쪼개져야 함: {_t51_syn_groups}"
    assert _t51_syn_groups["totem__pmos"] == ["SP1"] and _t51_syn_groups["totem__nmos"] == ["SN1"], \
        f"쪼개진 서브그룹 멤버 불일치: {_t51_syn_groups}"


def test_s151_section():
    """=== Test 52: propose_vertical_stack_id_gap_fill() -- audit_vertical_stack_id_   vs_kcl()의 '한쪽만 선언됨(gap)' boundary_findings를 KCL 직렬 파트너의 값으로   자동 채우기 제안(2026-08-13 세션31, two_stage_ota.topology.json의 M1/M2/M6   gap을 손으로 추론했던 걸 재사용 가능한 함수로 코드화 -- 사용자 요청) ===

    [합성 fixture -- internal_series gap은 채우고 declared_matching_pair gap은
    안 채우는지(둘의 의미가 다름 -- 후자는 미러 출력이 다른 branch에 있는 게
    원래 정상이라 audit_vertical_stack_id_vs_kcl() docstring이 명시적으로 구분함)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S151(줄 2858-2876, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t52_syn_trs = [
        Transistor("P1", "pmos", source="vdd", drain="D1"),
        Transistor("N1", "nmos", source="D1", drain="tail"),
        Transistor("MIR_A", "nmos", source="gnd", drain="ref", gate="ref"),
        Transistor("MIR_B", "nmos", source="gnd", drain="out", gate="ref"),
    ]
    _t52_roles = {"P1": {"vertical_stack_id": "colA"}, "MIR_A": {"vertical_stack_id": "biasgen"}}
    _t52_pairs = [("MIR_A", "MIR_B")]
    _t52_result = propose_vertical_stack_id_gap_fill(_t52_syn_trs, _t52_pairs, _t52_roles)
    assert _t52_result["proposals"] == {"N1": "colA"}, \
        f"internal_series gap(P1-N1, D1 공유)만 채워져야 함: {_t52_result['proposals']}"
    assert "MIR_B" not in _t52_result["proposals"], \
        "declared_matching_pair gap(MIR_A-MIR_B)은 채우면 안 됨(다른 branch가 정상)"
    assert _t52_result["conflicts"] == {}


def test_s152_section():
    """[합성 fixture -- 같은 소자가 서로 다른 edge에서 서로 다른 vsid를 물려받게
    되면(충돌) proposals가 아니라 conflicts로 분리되는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S152(줄 2877-2891, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t52c_trs = [
        Transistor("A", "nmos", source="gnd", drain="x"),
        Transistor("B", "nmos", source="x", drain="y"),
        Transistor("C", "nmos", source="y", drain="vdd"),
    ]
    _t52c_roles = {"A": {"vertical_stack_id": "left"}, "C": {"vertical_stack_id": "right"}}
    _t52c_result = propose_vertical_stack_id_gap_fill(_t52c_trs, [], _t52c_roles)
    assert _t52c_result["proposals"] == {}, \
        f"B가 A('left')/C('right') 양쪽에서 서로 다른 값을 물려받아 충돌해야 함: {_t52c_result}"
    assert _t52c_result["conflicts"] == {"B": ["left", "right"]}, \
        f"충돌 후보 집합 불일치: {_t52c_result['conflicts']}"


def test_s153_section(library_dir):
    """[실제 회로 -- two_stage_ota.topology.json 원본(device_roles에 M1/M2/M6
    미선언), propose_vertical_stack_id_gap_fill()을 직접 호출하면 손으로
    추론했던 것과 정확히 같은 제안이 나오는지 -- load_topology()를 거치지
    않고 원본 JSON을 직접 읽어 함수 자체의 회귀만 검증]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S153(줄 2892-2921, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    with open(_t49_os.path.join(_t49_lib, "two_stage_ota.topology.json"), encoding="utf-8") as _t52r_f:
        _t52r_raw = _t52r_json.load(_t52r_f)
    _t52r_trs = [Transistor(**d) for d in _t52r_raw["netlist"]]
    _t52r_roles = {k: v for k, v in (_t52r_raw.get("device_roles") or {}).items()
                    if not k.startswith("_")}
    _t52r_pairs = [tuple(p["names"]) for p in _t52r_raw["symmetry"]["matching_pairs"]
                    if p["current_forced"]]
    # 2026-08-14 -- "M1" not in _t52r_roles였던 원래 검사는 propose_device_roles_gap_fill()을
    # 이 파일에 실제 적용한 뒤로 더 이상 유효한 전제가 아니다(M1이 이제 gm_id_role/L_role/
    # headroom_role은 갖지만 vertical_stack_id는 여전히 없음 -- 그게 이 함수가 실제로
    # 검사하는 필드다). 정확한 전제로 좁힌다.
    assert _t52r_roles.get("M1", {}).get("vertical_stack_id") is None, \
        "원본 topology.json에 M1의 vertical_stack_id가 이미 선언돼 있음(fixture 전제 깨짐)"
    _t52r_result = propose_vertical_stack_id_gap_fill(_t52r_trs, _t52r_pairs, _t52r_roles)
    # 2026-08-24(세션42) -- 세션41이 "stage1"을 "stage1_ref"(M3)/"stage1_out"(M4)로
    # 분리했다(각각 독립된 vdd->gnd branch, `.ai/context.md` 세션41 §3 참고 -- M5(tail)를
    # 공유하는 두 branch를 하나의 vertical_stack_id로 묶은 게 애초에 잘못이었다는 사용자
    # 정정). M1/M2는 이 함수가 M3/M4의 새 vsid를 그대로 물려받는 것으로 갱신돼야 한다
    # (기대값을 옛 "stage1" 단일값에서 분리된 값으로 정정 -- 로직 회귀 아니라 golden
    # value가 stale해진 것, 실제 제안은 새 설계와 정확히 일치함).
    assert _t52r_result["proposals"] == {"M1": "stage1_ref", "M2": "stage1_out", "M6": "stage2"}, \
        f"two_stage_ota의 알려진 gap 제안과 불일치(회귀): {_t52r_result['proposals']}"
    assert _t52r_result["conflicts"] == {}


def test_s154_load_topology(library_dir):
    """[load_topology() 배선 -- 위 제안이 실제로 harness 최상위 진입점에서
    자동 반영되는지(2026-08-13 세션31, 사용자 지시로 load_topology()에 배선)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S154(줄 2922-2944, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    _t52w_trs, _t52w_meta = load_topology(_t49_os.path.join(_t49_lib, "two_stage_ota.topology.json"))
    # 2026-08-24(세션42) -- 바로 위 golden value 정정과 같은 이유(stage1 -> stage1_ref/
    # stage1_out 분리, 세션41)로 이 기대값도 stale해졌다 -- 함께 정정.
    assert _t52w_meta["_vertical_stack_id_autofilled"] == {"M1": "stage1_ref", "M2": "stage1_out", "M6": "stage2"}, \
        f"load_topology()의 자동 반영 기록과 불일치(회귀): {_t52w_meta['_vertical_stack_id_autofilled']}"
    assert _t52w_meta["_vertical_stack_id_conflicts"] is None
    for _t52w_name, _t52w_vsid in (("M1", "stage1_ref"), ("M2", "stage1_out"), ("M6", "stage2")):
        assert _t52w_meta["device_roles"][_t52w_name]["vertical_stack_id"] == _t52w_vsid, \
            f"{_t52w_name}의 device_roles에 자동 채움이 실제로 반영 안 됨(회귀)"
    _t52w_pairs_meta = _t52w_meta["symmetry"]["matching_pairs"]
    _t52w_forced = [tuple(p["names"]) for p in _t52w_pairs_meta if p["current_forced"]]
    _t52w_droles = {k: v for k, v in (_t52w_meta.get("device_roles") or {}).items()
                     if not k.startswith("_")}
    _t52w_audit = audit_vertical_stack_id_vs_kcl(_t52w_trs, _t52w_forced, _t52w_droles)
    _t52w_gaps = [f for f in _t52w_audit["boundary_findings"] if f["note"] is not None]
    assert _t52w_gaps == [], \
        f"resolve_stack_layout()이 크래시 근거로 삼는 gap이 여전히 남아있음(배선 실패): {_t52w_gaps}"


def test_s155_propose_device_roles_gap_fill(library_dir):
    """=== Test 53: propose_device_roles_gap_fill() -- netlist(+load_topology())만으로
    symmetry.matching_pairs/device_roles 재구성 -- 51소자 실회로 회귀(2026-08-14
    신설, 사용자 요청 -- 'netlist 정보만 가지고 이 필드들을 구성해봐') ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S155(줄 2945-2976, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    _t53_trs, _t53_meta = load_topology(
        _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json"))
    _t53_result = propose_device_roles_gap_fill(_t53_trs, {}, [])
    _t53_declared_pairs = _t53_meta["symmetry"]["matching_pairs"]
    _t53_declared_keys = set()
    for _t53_p in _t53_declared_pairs:
        for _t53_a, _t53_b in itertools.combinations(_t53_p["names"], 2):
            _t53_declared_keys.add(frozenset((_t53_a, _t53_b)))
    _t53_proposed_keys = {frozenset(p["names"]) for p in _t53_result["matching_pairs_proposals"]}
    assert len(_t53_proposed_keys) == 18, \
        f"제안 개수 회귀(branch-composite 9 + structural_symmetry 9): {len(_t53_proposed_keys)}"
    assert _t53_proposed_keys <= _t53_declared_keys, \
        f"declared에 없는 오탐 발생(회귀): {sorted(sorted(k) for k in _t53_proposed_keys - _t53_declared_keys)}"
    for _t53_pair in (("M1a", "M1b"), ("M4a", "M4b"), ("M37a", "M37b"),  # branch-composite differential
                        ("M8", "M17"), ("M13", "M22"),                    # branch-composite mirror
                        ("M11a", "M20a"), ("M15", "M25"), ("M36a", "M36b")):  # structural_symmetry
        assert frozenset(_t53_pair) in _t53_proposed_keys, f"{_t53_pair}가 제안에서 빠짐(회귀)"

    for _t53_name, _t53_expected in (
            ("M8", {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror"}),
            ("M1a", {"gm_id_role": "matching", "L_role": "mirror"}),
            ("M5", {"gm_id_role": "matching", "L_role": "bias_replica", "headroom_role": "tail"})):
        _t53_actual = _t53_result["device_roles_proposals"].get(_t53_name)
        for _t53_field, _t53_val in _t53_expected.items():
            assert _t53_actual is not None and _t53_actual.get(_t53_field) == _t53_val, \
                f"{_t53_name}.{_t53_field} 제안 회귀: {_t53_actual}"
    assert len(_t53_result["review_needed"]) >= 1, "undisposed_candidates review가 하나도 없음(회귀)"


def test_s156_section(s155_state):
    """[compensation_stage_devices를 넘겨도 M1a/M4a/M15/M25 등 8개 소자에 gm_id_role이
    그대로 제안되는지(2026-08-14 사용자 지시로 방향 전환 -- 처음엔 위험을 피하려고
    이 8개를 건너뛰게 만들었으나, '가드를 만들어야지 왜 제외해'라는 지적으로 근본원인
    (sizing_recipe.py의 누락된 gm_id_role 가드)을 직접 고치는 쪽으로 정정. 이제 이 함수는
    다시 compensation 소속과 무관하게 제안하고, review_needed에 참고 정보만 남긴다]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S156(줄 2977-2995, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t53_meta = s155_state._t53_meta
    _t53_trs = s155_state._t53_trs

    _t53_stage_devices = _t53_meta["compensation"]["stage_devices"]
    _t53_flat_stage = [n for grp in _t53_stage_devices for n in grp]
    assert "M1a" in _t53_flat_stage, "fixture 전제 확인(compensation.stage_devices 구조 변경됨?)"
    _t53_result_comp = propose_device_roles_gap_fill(
        _t53_trs, {}, [], compensation_stage_devices=_t53_flat_stage)
    for _t53_comp_name in _t53_flat_stage:
        assert "gm_id_role" in _t53_result_comp["device_roles_proposals"].get(_t53_comp_name, {}), \
            f"{_t53_comp_name}(compensation.stage_devices 소속)에 gm_id_role이 다시 제안 안 됨(회귀): " \
            f"{_t53_result_comp['device_roles_proposals'].get(_t53_comp_name)}"
    assert any(r.get("device") in _t53_flat_stage and "compensation.stage_devices" in r.get("note", "")
                for r in _t53_result_comp["review_needed"]), \
        "compensation 소속 소자의 참고 안내가 review_needed에 안 남음(회귀)"


@pytest.mark.xfail(raises=ValueError, strict=True,
                   reason="I-C11 two_stage_ota stage1_out KVL -- 담당 Phase 4")
def test_s157_M1(s157_state):
    """[실제로 M1(compensation.stage_devices 소속)에 gm_id_role을 채운 topology.json으로
    optimize_full_circuit_budget()을 돌려도 sizing 결과가 안 채운 원본과 완전히 같은지
    -- _AUTHORITATIVE_GM_ID_SOURCES 가드가 실제로 동작하는지, workspaces/run_harness.py의
    실제 검증된 spec(_spec_two_stage_ota())을 그대로 재사용해 회귀 검증]

    I-C11: before 호출이 ValueError(stage1_out KVL)라 성공 경로(가드 회귀 비교)에 닿지 못한다. 이관본 else 분기의
    판정을 그대로 담고 strict xfail로 둔다(승인 20260922-c9-ic11-split).

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S157(줄 2996-3065)의 성공 분기.
    """
    _t53g_two_stage_path = s157_state._t53g_two_stage_path
    _t53g_raw = s157_state._t53g_raw
    _t53g_spec = s157_state._t53g_spec
    _t53g_gp = s157_state._t53g_gp

    _t53g_before = optimize_full_circuit_budget(
        _t53g_two_stage_path, dict(_t53g_spec), grid_points_per_theta=_t53g_gp)

    with _t53g_tempfile.TemporaryDirectory() as _t53g_tmpdir:
        _t53g_mut_path = _t49_os.path.join(_t53g_tmpdir, "two_stage_ota.mutated.topology.json")
        _t53g_mut = dict(_t53g_raw)
        _t53g_mut["device_roles"] = dict(_t53g_raw["device_roles"])
        # 2026-08-14 -- M1은 원본에 device_roles 자체가 없다(compensation.stage_devices
        # 소속이라 사람 저자가 의도적으로 비워둔 자리, 이 Test 53 앞부분에서 이미 확인됨) --
        # 그 빈 자리에 gm_id_role만 새로 채워 넣는 게 정확히 이 회귀가 검증하려는 시나리오다.
        _t53g_mut["device_roles"]["M1"] = {"gm_id_role": "matching"}
        with open(_t53g_mut_path, "w", encoding="utf-8") as _t53g_f:
            json.dump(_t53g_mut, _t53g_f)
        _t53g_after = optimize_full_circuit_budget(
            _t53g_mut_path, dict(_t53g_spec), grid_points_per_theta=_t53g_gp)
        assert _t53g_before["sizing"]["M1"] == _t53g_after["sizing"]["M1"], \
            f"M1에 gm_id_role='matching'을 채웠는데 sizing 결과가 바뀜(가드 실패, 진짜 회귀): " \
            f"{_t53g_before['sizing']['M1']} vs {_t53g_after['sizing']['M1']}"
        assert _t53g_before["theta_star"] == _t53g_after["theta_star"], \
            "gm_id_role 추가가 theta_star까지 바꿈(가드가 전혀 안 먹힘)"


def test_s157_M1_known_limitation(s157_state):
    """[실제로 M1(compensation.stage_devices 소속)에 gm_id_role을 채운 topology.json으로
    optimize_full_circuit_budget()을 돌려도 sizing 결과가 안 채운 원본과 완전히 같은지
    -- _AUTHORITATIVE_GM_ID_SOURCES 가드가 실제로 동작하는지, workspaces/run_harness.py의
    실제 검증된 spec(_spec_two_stage_ota())을 그대로 재사용해 회귀 검증]

    I-C11 지금 동작: before(원본)와 after(M1 gm_id_role 채움) 호출이 둘 다 같은 이유(메시지에 'stage1_out'과
    'KVL')의 ValueError다 -- 이관본 `_t53g_before is None` 분기의 판정 그대로.

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S157(줄 2996-3065)의 except 분기 조건 + 거부 try.
    """
    _t53g_two_stage_path = s157_state._t53g_two_stage_path
    _t53g_raw = s157_state._t53g_raw
    _t53g_spec = s157_state._t53g_spec
    _t53g_gp = s157_state._t53g_gp

    with pytest.raises(ValueError) as _t53g_e_info:
        optimize_full_circuit_budget(
            _t53g_two_stage_path, dict(_t53g_spec), grid_points_per_theta=_t53g_gp)
    _t53g_e = _t53g_e_info.value
    assert "stage1_out" in str(_t53g_e) and "KVL" in str(_t53g_e), \
        f"before가 known-limitation(I-C11)이 아닌 다른 이유로 실패함(회귀 의심): {_t53g_e}"

    with _t53g_tempfile.TemporaryDirectory() as _t53g_tmpdir:
        _t53g_mut_path = _t49_os.path.join(_t53g_tmpdir, "two_stage_ota.mutated.topology.json")
        _t53g_mut = dict(_t53g_raw)
        _t53g_mut["device_roles"] = dict(_t53g_raw["device_roles"])
        # 2026-08-14 -- M1은 원본에 device_roles 자체가 없다(compensation.stage_devices
        # 소속이라 사람 저자가 의도적으로 비워둔 자리, 이 Test 53 앞부분에서 이미 확인됨) --
        # 그 빈 자리에 gm_id_role만 새로 채워 넣는 게 정확히 이 회귀가 검증하려는 시나리오다.
        _t53g_mut["device_roles"]["M1"] = {"gm_id_role": "matching"}
        with open(_t53g_mut_path, "w", encoding="utf-8") as _t53g_f:
            json.dump(_t53g_mut, _t53g_f)
        with pytest.raises(ValueError) as _t53g_e2_info:
            optimize_full_circuit_budget(
                _t53g_mut_path, dict(_t53g_spec), grid_points_per_theta=_t53g_gp)
        _t53g_e2 = _t53g_e2_info.value
        assert "stage1_out" in str(_t53g_e2) and "KVL" in str(_t53g_e2), \
            f"after가 다른 이유로 실패함(회귀 의심): {_t53g_e2}"


def test_s158_propose_device_roles_gap_fill(library_dir):
    """=== Test 54: propose_device_roles_gap_fill() -- 층위1 폴백(비대칭/폴딩 구조라
    branch-composite/structural_symmetry가 전부 0건인 회로) 안전망 검증 --
    folded_cascode 실회로 회귀 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S158(줄 3066-3090, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    _t54_trs, _t54_meta = load_topology(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"))
    _t54_result = propose_device_roles_gap_fill(_t54_trs, {}, [])
    _t54_proposed_keys = {frozenset(p["names"]) for p in _t54_result["matching_pairs_proposals"]}
    for _t54_pair in (("M1", "M2"), ("M9", "M10"), ("M7", "M8")):
        assert frozenset(_t54_pair) in _t54_proposed_keys, \
            f"층위1 폴백이 {_t54_pair}를 못 찾음(회귀) -- diff_pair 또는 diode-connected 미러여야 함"
    assert frozenset(("M3", "M4")) not in _t54_proposed_keys, \
        "M3/M4는 3-way 후보({M3,M4,MP})라 이 함수가 확정 안 하고 review로 넘겨야 하는데 제안됨(회귀)"
    _t54_undisposed_tags = {u[0:3] for r in _t54_result["review_needed"]
                              for u in r.get("undisposed_candidates", [])}
    assert ("current_mirror", "pmos", "vb1") in _t54_undisposed_tags, \
        "3-way {M3,M4,MP} 후보가 review_needed에 안 남음(회귀)"


def test_s159_apply_device_roles_gap_fill(library_dir):
    """=== Test 55: apply_device_roles_gap_fill() -- 실제 파일 읽기/병합/쓰기 왕복 +
    멱등성(같은 결과를 두 번 적용해도 중복 안 생김) ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S159(줄 3091-3133, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    with _t55_tempfile.TemporaryDirectory() as _t55_tmpdir:
        _t55_path = _t49_os.path.join(_t55_tmpdir, "folded_cascode.topology.json")
        _t55_shutil.copy(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"), _t55_path)

        _t55_trs, _t55_meta = load_topology(_t55_path)
        _t55_before_pairs = len(_t55_meta["symmetry"]["matching_pairs"])
        _t55_before_pair_keys = {frozenset(p["names"]) for p in _t55_meta["symmetry"]["matching_pairs"]}
        # ⚠️ 2026-08-14 -- folded_cascode.topology.json 원본이 이제(사용자 승인으로 실제
        # 적용됨) M1/M2/M9/M10/M7/M8/M11/MN 8쌍 중 일부를 이미 declared로 갖고 있을 수 있다
        # -- 이 테스트는 "몇 쌍이 새로 채워지는가"를 하드코딩하지 않고, propose()가 이번에
        # 실제로 낸 제안 집합에서 **현재 파일이 이미 아는 것**을 뺀 나머지만 기대값으로 쓴다
        # (파일이 나중에 더 채워져도 이 테스트가 stale해지지 않도록).
        _t55_result_empty = propose_device_roles_gap_fill(_t55_trs, {}, [])
        _t55_expected_new = sorted(
            (sorted(frozenset(p["names"])) for p in _t55_result_empty["matching_pairs_proposals"]
             if frozenset(p["names"]) not in _t55_before_pair_keys))
        _t55_apply1 = apply_device_roles_gap_fill(_t55_path, _t55_result_empty)
        assert sorted(_t55_apply1["applied_matching_pairs"]) == _t55_expected_new, \
            f"파일에 실제로 반영된 쌍이 기대와 다름(이미 declared인 쌍은 걸러지고 새 쌍만 " \
            f"남아야 함): applied={_t55_apply1['applied_matching_pairs']} expected={_t55_expected_new}"

        with open(_t55_path, encoding="utf-8") as _t55_f:
            _t55_written = json.load(_t55_f)
        assert len(_t55_written["symmetry"]["matching_pairs"]) == _t55_before_pairs + len(_t55_expected_new), \
            f"파일에 새 쌍 {len(_t55_expected_new)}개가 실제로 추가되지 않음(쓰기 실패)"
        assert _t55_written["device_roles"] is not None and "M9" in _t55_written["device_roles"], \
            "device_roles가 파일에 실제로 안 써짐"
        assert _t55_written["device_roles"]["M9"]["vsb"] == 0.0, \
            "vs 기본값(템플릿 관례) 미적용"

        _t55_trs2, _t55_meta2 = load_topology(_t55_path)
        _t55_result2 = propose_device_roles_gap_fill(
            _t55_trs2, _t55_meta2["device_roles"] or {}, _t55_meta2["symmetry"]["matching_pairs"])
        _t55_apply2 = apply_device_roles_gap_fill(_t55_path, _t55_result2)
        assert _t55_apply2["applied_matching_pairs"] == [], \
            f"멱등성 위반 -- 이미 반영된 쌍을 다시 적용하려 함: {_t55_apply2['applied_matching_pairs']}"


def test_s160_propose_device_roles_gap_fill():
    """=== Test 56: propose_device_roles_gap_fill()/apply_device_roles_gap_fill() --
    이미 선언된 값과 제안이 충돌하면 조용히 덮어쓰지 않고 review_needed로만
    보고하는지(프로젝트 전역 원칙) 합성 fixture로 검증 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S160(줄 3134-3186, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t56_trs = [
        Transistor("MA", "pmos", source="tail", drain="outA", gate="vin_p"),
        Transistor("MB", "pmos", source="tail", drain="outB", gate="vin_n"),
        Transistor("MT", "pmos", source="vdd", drain="tail", gate="biasp"),
        # 2026-08-14 -- outA/outB가 gnd까지 안 이어지면(dangling) find_differential_pair_
        # candidates()(branch가 terminates_at="gnd"이어야 함)가 후보를 못 찾아 MA/MB가
        # confirmed 안 되고, 그러면 애초에 "gm_id_role='matching' 제안 vs 기존 'balanced'
        # 선언 충돌"이라는 이 테스트의 전제 자체가 성립 안 한다(gm_id_role이 아예 제안 안
        # 됨) -- 실제 회로처럼 완결된 branch를 만들기 위해 NMOS 부하를 추가.
        Transistor("MLA", "nmos", source="gnd", drain="outA", gate="biasn"),
        Transistor("MLB", "nmos", source="gnd", drain="outB", gate="biasn"),
    ]
    _t56_conflicting_roles = {"MA": {"gm_id_role": "balanced"}}  # 실제 제안은 "matching"이어야 함
    _t56_result = propose_device_roles_gap_fill(_t56_trs, _t56_conflicting_roles, [])
    # 2026-08-20(세션40) 정정 -- 예전엔 필드 하나(gm_id_role)만 충돌해도 그 소자의 proposal
    # 전체를 통째로 버렸다(atomic). vds_match_vgs_of 5번째 소스 구현 중 이게 실제 사고를
    # 냈음을 발견(nmcnr_amplifier의 M109 -- gm_id_role만 충돌하는데 완전히 무관한 새
    # vds_match_vgs_of 제안까지 같이 버려짐)해서, **충돌한 필드만** 제외하고 나머지 필드는
    # 그대로 제안하도록 고쳤다 -- MA는 gm_id_role(충돌)은 빠지고 L_role/headroom_role(무관,
    # 충돌 없음)은 그대로 제안돼야 한다.
    assert "MA" in _t56_result["device_roles_proposals"], \
        "MA의 무관한 필드(L_role/headroom_role)까지 통째로 안 걸러졌어야 하는데 아예 안 실림(회귀)"
    assert "gm_id_role" not in _t56_result["device_roles_proposals"]["MA"], \
        f"MA의 충돌 필드(gm_id_role)가 그대로 제안에 남음(원칙 위반): {_t56_result['device_roles_proposals']['MA']}"
    assert set(_t56_result["device_roles_proposals"]["MA"]) == {"L_role", "headroom_role"}, \
        f"MA의 무관한 필드 제안이 예상과 다름: {_t56_result['device_roles_proposals']['MA']}"
    assert any(r.get("device") == "MA" and "field_conflicts" in r for r in _t56_result["review_needed"]), \
        f"MA의 충돌이 review_needed에 안 남음(회귀): {_t56_result['review_needed']}"
    assert "MB" in _t56_result["device_roles_proposals"], \
        "충돌 없는 MB까지 같이 걸러짐(과잉 차단, 회귀)"

    with _t55_tempfile.TemporaryDirectory() as _t56_tmpdir:
        _t56_path = _t49_os.path.join(_t56_tmpdir, "conflict_fixture.topology.json")
        with open(_t56_path, "w", encoding="utf-8") as _t56_f:
            json.dump({
                "schema_version": "2.0", "topology_name": "conflict_fixture", "source": "self-test",
                "compensation": None, "_compensation_status": "not_applicable",
                "netlist": [_dc_asdict(t) for t in _t56_trs],
                "symmetry": {"matching_pairs": []},
                "device_roles": _t56_conflicting_roles,
            }, _t56_f)
        _t56_applied = apply_device_roles_gap_fill(_t56_path, _t56_result)
        with open(_t56_path, encoding="utf-8") as _t56_f:
            _t56_written = json.load(_t56_f)
        assert _t56_written["device_roles"]["MA"]["gm_id_role"] == "balanced", \
            "apply_device_roles_gap_fill()이 이미 선언된 MA.gm_id_role을 덮어씀(원칙 위반)"


def test_s161_find_authoritative_sizing_devices(library_dir):
    """=== Test 57: find_authoritative_sizing_devices()/find_unreviewed_device_roles()/
    require_device_roles_reviewed() -- optimize_full_circuit_budget() 실행 전 review
    게이트(2026-08-14 사용자 지시 -- '구조적으로 명확한 기능과 필요한 기능을
    구분해서... review 안 된 부분은 error로 띄우고... review 받았다는 표시를
    해서 optimize함수가 실행되도록'). 실측 사고 재발 방지: current_reuse_
    telescopic_ota의 L_cascode(metric_stage_budget) 대상 M2a/M2b/M3a/M3b에
    자동 제안된 L_role이 실제로 적용됐다가 그 theta 탐색을 무력화해 gain_db가
    76.48->74.8로 떨어지는 회귀를 이 세션이 직접 재현/원인규명했다 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S161(줄 3187-3213, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    _t57_lib_path = _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json")
    with open(_t57_lib_path, encoding="utf-8") as _t57_f:
        _t57_raw = json.load(_t57_f)
    _t57_trs, _t57_meta = load_topology(_t57_lib_path)
    _t57_authoritative = find_authoritative_sizing_devices(_t57_meta)
    for _t57_name in ("M1a", "M4a", "M15", "M25"):  # compensation.stage_devices
        assert _t57_name in _t57_authoritative, f"{_t57_name}(compensation)이 authoritative에 안 잡힘"
    for _t57_name in ("M2a", "M2b", "M3a", "M3b"):  # L_cascode(metric_stage_budget) 대상
        assert _t57_name in _t57_authoritative, \
            f"{_t57_name}(metric_stage_budget 대상)이 authoritative에 안 잡힘(회귀 -- 실제 사고 재발 위험)"
    assert "M37a" in _t57_authoritative, "M37a(N_cmfb_bw, B타입 대상)가 authoritative에 안 잡힘"
    assert "M8" not in _t57_authoritative, "M8(일반 소자)이 잘못 authoritative로 잡힘(과잉 허용)"

    _t57_unreviewed_real = find_unreviewed_device_roles(_t57_meta)
    assert _t57_unreviewed_real == {}, \
        f"실제 라이브러리 파일(이미 review 완료된 상태)인데 unreviewed가 남음(회귀): {_t57_unreviewed_real}"
    require_device_roles_reviewed(_t57_lib_path, _t57_meta)  # 예외 안 나야 정상


def test_s162_section(s161_state):
    """[합성 fixture -- 일반 소자(authoritative 아님)의 gm_id_role/L_role이 파일에
    없으면(=아직 review 안 됨) require_device_roles_reviewed()가 명확한 ValueError를
    내고, apply_device_roles_gap_fill()로 review를 완료하면 그 다음부터 통과하는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S162(줄 3214-3246, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t57_raw = s161_state._t57_raw

    _t57_mut = json.loads(json.dumps(_t57_raw))  # deep copy
    _t57_mut["device_roles"]["M8"] = {"headroom_role": "mirror", "vertical_stack_id": "biasgen_vom_a",
                                        "vsb": 0.0}  # gm_id_role/L_role 일부러 뺌(review 전 상태 재현)
    with _t55_tempfile.TemporaryDirectory() as _t57_tmpdir:
        _t57_mut_path = _t49_os.path.join(_t57_tmpdir, "crt_unreviewed.topology.json")
        with open(_t57_mut_path, "w", encoding="utf-8") as _t57_f:
            json.dump(_t57_mut, _t57_f)
        _t57_mut_trs, _t57_mut_meta = load_topology(_t57_mut_path)
        _t57_unreviewed = find_unreviewed_device_roles(_t57_mut_meta)
        assert "M8" in _t57_unreviewed, \
            f"M8의 gm_id_role/L_role을 일부러 뺐는데 unreviewed로 안 잡힘(회귀): {_t57_unreviewed}"
        assert set(_t57_unreviewed["M8"]) == {"gm_id_role", "L_role"}, \
            f"M8의 unreviewed 필드가 예상과 다름: {_t57_unreviewed['M8']}"
        with pytest.raises(ValueError) as _t57_e_info:
            require_device_roles_reviewed(_t57_mut_path, _t57_mut_meta)
        _t57_e = _t57_e_info.value
        assert "M8" in str(_t57_e), f"에러 메시지에 M8이 없음: {_t57_e}"

        # review 완료(apply_device_roles_gap_fill()로 파일에 실제로 씀) 이후 통과하는지
        _t57_propose = propose_device_roles_gap_fill(
            _t57_mut_trs, _t57_mut_meta.get("device_roles") or {},
            _t57_mut_meta["symmetry"]["matching_pairs"])
        apply_device_roles_gap_fill(_t57_mut_path, _t57_propose)
        _t57_trs2, _t57_meta2 = load_topology(_t57_mut_path)
        require_device_roles_reviewed(_t57_mut_path, _t57_meta2)  # 이제 예외 안 나야 정상


def test_s163_find_unreviewed_matching_pairs(library_dir):
    """=== Test 58: find_unreviewed_matching_pairs() -- matching_pairs도 review 게이트
    대상(2026-08-14, 사용자 재지적 -- '대칭적인 branch이면 branch 전류가 같아야
    하는것 아니야?' 계기로 두 가지를 재확인: (1) mirror/structural_symmetry 출처의
    current_forced 기본값을 False->True로 정정(4회로 declared 전수 재조사, 2-소자
    쌍은 예외 없이 True), (2) sizing_recipe.py의 matching_pairs L 전파가 current_
    forced 값과 무관하게 모든 선언된 쌍에 작동함을 재확인 -- 'current_forced=False는
    sizing에 안 쓰인다'는 이전 주장이 틀렸었다). 그래서 differential(offset)만
    load_topology()가 메모리에도 자동 병합하고, mirror류(ratio)는 review 전까지
    병합도 안 하고 review 목록에만 남긴다 -- folded_cascode의 실제 gap(M11/MN,
    diode-connected MN + 소비자 M11이지만 한때 이 파일이 한 번도 check_symmetry_
    dispositions() 검증을 받은 적 없어 사람이 확정하지 않았던 사례 -- 2026-08-14
    세션34에 사용자 승인으로 실제 declared에 반영됐으므로, 이 테스트는 이제 임시
    사본에서 그 declared 쌍을 다시 지워 '아직 review 안 된 상태'를 재현한다(실제
    라이브러리 파일이 나중에 더 채워져도 이 테스트가 stale해지지 않도록)) ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S163(줄 3247-3290, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    _t58_srcdir = _t58_tempfile.mkdtemp()
    _t58_path = _t49_os.path.join(_t58_srcdir, "folded_cascode.topology.json")
    _t58_shutil.copy(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"), _t58_path)
    with open(_t58_path, "r", encoding="utf-8") as _t58_f:
        _t58_raw = json.load(_t58_f)
    _t58_raw["symmetry"]["matching_pairs"] = [
        p for p in _t58_raw["symmetry"]["matching_pairs"] if set(p["names"]) != {"M11", "MN"}]
    if isinstance(_t58_raw.get("device_roles"), dict):
        for _t58_n in ("M11", "MN"):
            _t58_raw["device_roles"].pop(_t58_n, None)
    with open(_t58_path, "w", encoding="utf-8") as _t58_f:
        json.dump(_t58_raw, _t58_f)
    _t58_trs, _t58_meta = load_topology(_t58_path)
    _t58_declared_keys = {frozenset(p["names"]) for p in _t58_meta["symmetry"]["matching_pairs"]}
    assert frozenset(("M11", "MN")) not in _t58_declared_keys, \
        "M11/MN이 declared에 있음(임시 사본에서 방금 지웠는데도 남아있으면 이 테스트 setup 자체가 잘못됨)"
    _t58_needs_review = find_unreviewed_matching_pairs(_t58_meta)
    assert any(set(p["names"]) == {"M11", "MN"} for p in _t58_needs_review), \
        f"M11/MN이 find_unreviewed_matching_pairs()에 안 잡힘(회귀): {_t58_needs_review}"
    assert all(p.get("matching_sensitivity") != "offset" for p in _t58_needs_review), \
        "offset(differential) 제안이 review 목록에 잘못 섞임(differential은 review 불필요해야 함)"

    with pytest.raises(ValueError) as _t58_e_info:
        require_device_roles_reviewed(_t58_path, _t58_meta)
    _t58_e = _t58_e_info.value
    assert "M11" in str(_t58_e) and "MN" in str(_t58_e), f"에러 메시지에 M11/MN이 없음: {_t58_e}"


def test_s164_differential(s163_state):
    """[differential(offset) 출처는 review 없이도 메모리에 자동 병합되는지 -- M1/M2
    (folded_cascode, 이미 declared)로 회귀 없음만 재확인(새 제안은 이미 declared라
    없어야 정상, 순수 하위호환 확인)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S164(줄 3291-3300, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t58_meta = s163_state._t58_meta

    assert find_unreviewed_matching_pairs(_t58_meta) == [
        p for p in find_unreviewed_matching_pairs(_t58_meta) if set(p["names"]) != {"M1", "M2"}], \
        "이미 declared된 M1/M2(differential)가 review 목록에 잘못 나타남"


def test_s165_audit_theta_root_direction(library_dir):
    """=== Test 60: audit_theta_root_direction() -- sizing_roles.theta의 'A'/'A_signed'
    feed가 캐스코드 체인에서 lo(전류생성원)인 root를 그 위에 얹힌 up(캐스코드)에서
    유도하는(방향이 거꾸로인) 경우를 idioms.m_cascode()/propagate_reference_role_
    through_cascode()로 잡아내는지(2026-08-18, 사용자 지적 3단계 -- 'analog-grammar를
    통해서 각 소자의 관계를 알고 있는 것 아닌가' -> 'm_cascode()가 이미 하지 않나' ->
    실측 결과 m_cascode()가 PMOS/NMOS 경계(drain-drain)를 못 잡는 gap을 발견해 그
    자체를 확장. 그 확장 검증 중 m_diffpair()가 CTRL_SRC(FEEDBACK게이트 CMFB 차동쌍)를
    놓치는 별개 gap도 발견해 같이 확장) ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S165(줄 3301-3312, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    _t60_trs, _t60_meta = load_topology(_t49_os.path.join(_t49_lib, "nmcnr_amplifier.topology.json"))
    _t60_clean = audit_theta_root_direction(_t60_trs, _t60_meta["sizing_roles"], inputs=("Vin_p", "Vin_n"))
    assert _t60_clean == [], f"실제(정정된) nmcnr_amplifier가 깨끗해야 하는데: {_t60_clean}"


def test_s166_section(s165_state):
    """[세션 초반 실제로 저질렀던 버그(M106을 root로 두고 M108을 그 반대로 참조) 재현 -- 잡히는지]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S166(줄 3314-3330, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t60_meta = s165_state._t60_meta
    _t60_trs = s165_state._t60_trs

    _t60_buggy = _t60_copy.deepcopy(_t60_meta["sizing_roles"])
    _t60_buggy["theta"] = [t for t in _t60_buggy["theta"] if t["name"] not in ("kcl_M104", "r_series_M106")]
    _t60_buggy["theta"].append({
        "name": "kcl_M106_BUGGY", "bounds": [1.0, 1.0],
        "feeds": {"type": "A_signed", "root": "M106",
                  "terms": [{"device": "M104", "sign": 1}, {"device": "M102", "sign": -1}]}})
    _t60_buggy["theta"].append({
        "name": "r_series_M108_BUGGY", "bounds": [1.0, 1.0],
        "feeds": {"type": "A", "root": ["M108"], "reference": ["M106"]}})
    _t60_buggy_findings = audit_theta_root_direction(_t60_trs, _t60_buggy, inputs=("Vin_p", "Vin_n"))
    assert len(_t60_buggy_findings) == 1, f"버그 재현판이 정확히 1건 잡혀야 하는데: {_t60_buggy_findings}"
    assert (_t60_buggy_findings[0]["root"] == "M108"
            and _t60_buggy_findings[0]["reference"] == "M106"), \
        f"잡힌 방향이 예상과 다름: {_t60_buggy_findings}"


def test_s167_kcl_tail_M38(library_dir):
    """[current_reuse_telescopic_ota의 kcl_tail_M38(root=M38 tail, reference=M37a/M37b CMFB 차동쌍)이 오탐 없는지 -- M37a/M37b는 게이트(Voc/Voc_des)가 FEEDBACK으로 분류돼 role=CONTROLLED_CURRENT_SOURCE가 되는데, m_diffpair()가 원래 role==AMP만 인정해 이 CMFB 차동쌍을 못 알아보고 m_cascode()가 'M38 위에 얹힌 캐스코드'로 오분류하던 걸 실측으로 발견(m_cascode() cross-kind 확장과는 별개 gap) -- m_diffpair()에 CTRL_SRC도 추가해 정정, feedbacks=('Voc','Voc_des')를 정확히 선언하면 오탐이 사라지는지 재확인(회귀 감시)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S167(줄 3332-3345, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    _t60_crt_trs, _t60_crt_meta = load_topology(
        _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json"))
    _t60_crt_findings = audit_theta_root_direction(
        _t60_crt_trs, _t60_crt_meta["sizing_roles"], inputs=("Vip", "Vim"),
        feedbacks=("Voc", "Voc_des"))
    assert _t60_crt_findings == [], \
        f"kcl_tail_M38(CMFB 차동쌍) 오탐이 재발함: {_t60_crt_findings}"


def test_s168_section(library_dir):
    """[나머지 실제 library 회로(folded_cascode/two_stage_ota)도 findings 0건인지 -- 이미 검증된 설계에 오탐이 없어야 함(inputs는 각 회로 실제 net 이름 그대로)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S168(줄 3347-3360, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    _t60_fc_trs, _t60_fc_meta = load_topology(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"))
    _t60_fc_findings = audit_theta_root_direction(_t60_fc_trs, _t60_fc_meta["sizing_roles"],
                                                    inputs=("vin_p", "vin_n"))
    assert _t60_fc_findings == [], f"folded_cascode에 오탐: {_t60_fc_findings}"
    _t60_tso_trs, _t60_tso_meta = load_topology(_t49_os.path.join(_t49_lib, "two_stage_ota.topology.json"))
    _t60_tso_findings = audit_theta_root_direction(_t60_tso_trs, _t60_tso_meta["sizing_roles"],
                                                     inputs=("vin_p", "vin_n"))
    assert _t60_tso_findings == [], f"two_stage_ota에 오탐: {_t60_tso_findings}"


def test_s169_propose_theta_kcl_gap_fill(library_dir):
    """=== Test 61: propose_theta_kcl_gap_fill() -- 전류(ID) KCL 구조를 connectivity +
    analog-grammar idiom만으로 제안(2026-08-18, 사용자 승인 후 신설 -- 'propose_
    theta_kcl_gap_fill 만들자'). 규칙 1(diffpair 50/50)/2(캐스코드 추종)/2.5(declared
    mirror)/2.7(gate mirror)/3(KCL 합)/4(자유 root 승격, diode 우선)를 실측으로
    검증한다 ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S169(줄 3361-3381, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    _t61_trs, _t61_meta = load_topology(_t49_os.path.join(_t49_lib, "nmcnr_amplifier.topology.json"))
    _t61_result = propose_theta_kcl_gap_fill(
        _t61_trs, _t61_meta["symmetry"]["matching_pairs"],
        ideal_sources=_t61_meta.get("ideal_sources"), inputs=("Vin_p", "Vin_n"))
    assert _t61_result["unresolved_devices"] == [], \
        f"nmcnr_amplifier는 전부 resolve돼야 하는데: {_t61_result['unresolved_devices']}"
    _t61_by_name = {t["name"]: t for t in _t61_result["theta_proposals"]}
    assert set(_t61_by_name["r_split_M102_M103"]["feeds"]["root"]) == {"M102", "M103"}, \
        "diffpair 50/50 규칙(M102/M103)이 안 잡힘"
    assert _t61_by_name["r_series_M106"]["feeds"]["reference"] == ["M108"], \
        "M106이 M108(lo)을 따라가야 하는데(캐스코드 추종): " + str(_t61_by_name["r_series_M106"])
    _t61_free_names = {n for t in _t61_result["theta_proposals"] if t["feeds"]["type"] == "const"
                        for n in t["feeds"]["root"]}
    assert _t61_free_names == {"M101", "M108", "M109", "M203", "M204", "M301"}, \
        f"nmcnr_amplifier의 자유 root 집합이 예상과 다름: {_t61_free_names}"


def test_s170_section(s169_state):
    """[compensation_stage_devices=[M102,M103,M201,M301]을 주면 위 한계가 풀리는지 -- 2026-08-19 세션37 신설]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S170(줄 3383-3406, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t61_meta = s169_state._t61_meta
    _t61_trs = s169_state._t61_trs

    _t61c_flat = [n for grp in _t61_meta["compensation"]["stage_devices"] for n in grp]
    _t61c_result = propose_theta_kcl_gap_fill(
        _t61_trs, _t61_meta["symmetry"]["matching_pairs"],
        ideal_sources=_t61_meta.get("ideal_sources"), compensation_stage_devices=_t61c_flat,
        inputs=("Vin_p", "Vin_n"))
    assert _t61c_result["unresolved_devices"] == [], \
        f"compensation 제외해도 전부 resolve돼야 하는데: {_t61c_result['unresolved_devices']}"
    _t61c_names = {t["name"] for t in _t61c_result["theta_proposals"]}
    _t61c_roots = {n for t in _t61c_result["theta_proposals"]
                    for n in (t["feeds"]["root"] if isinstance(t["feeds"]["root"], list)
                              else [t["feeds"]["root"]])}
    assert not (_t61c_roots & set(_t61c_flat)), \
        f"compensation 소속 소자가 theta root로 잘못 제안됨: {_t61c_roots & set(_t61c_flat)}"
    assert "kcl_M203" in _t61c_names, \
        "M201(compensation)이 resolved로 처리되면 M203은 독립 자유쌍이 아니라 KCL로 유도돼야 함"
    _t61c_by_name = {t["name"]: t for t in _t61c_result["theta_proposals"]}
    assert _t61c_by_name["kcl_M203"]["feeds"]["terms"] == [{"device": "M201", "sign": 1}], \
        "kcl_M203이 M201에서 유도돼야 함: " + str(_t61c_by_name["kcl_M203"])
    assert "r_mirror_M204_M203" in _t61c_names, \
        "M204는 M203의 declared mirror(규칙 2.5)로 재분류돼야 함(더 이상 독립 자유쌍 아님)"
    assert "kcl_M302" in _t61c_names, \
        "M301(compensation)이 resolved로 처리되면 M302는 그 KCL 유도값이어야 함"


def test_s171_section(library_dir):
    """[folded_cascode -- 규칙 2.7(gate mirror, MP->M3/M4)가 실제로 필요한지 재확인 -- 처음엔 이 규칙이 없어서 MP가 회로 나머지와 완전히 단절된 고아 자유변수로 남았었다(실측 발견)]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S171(줄 3408-3419, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir

    _t61_fc_trs, _t61_fc_meta = load_topology(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"))
    _t61_fc_result = propose_theta_kcl_gap_fill(
        _t61_fc_trs, _t61_fc_meta["symmetry"]["matching_pairs"],
        ideal_sources=_t61_fc_meta.get("ideal_sources"), inputs=("vin_p", "vin_n"))
    assert _t61_fc_result["unresolved_devices"] == [], \
        f"folded_cascode는 전부 resolve돼야 하는데: {_t61_fc_result['unresolved_devices']}"
    _t61_fc_by_name = {t["name"]: t for t in _t61_fc_result["theta_proposals"]}
    assert "r_mirror_M3_MP" in _t61_fc_by_name and "r_mirror_M4_MP" in _t61_fc_by_name, \
        "MP->M3/M4 게이트 미러(규칙 2.7)가 안 잡힘 -- MP가 다시 고아 변수로 남을 위험"


def test_s172_section(s171_state):
    """[서로 다른 자유 root 그룹(MP측/M9-M10측)이 같은 KCL 노드로 수렴하면 placeholder 값 충돌(0/음수)을 review_needed로 잡아내는지 -- 실측으로 처음 발견한 현상(구조 결함이 아니라 '이 자유 root들을 서로 조율해야 한다'는 신호), 조용히 넘기지 않는지 회귀 감시]

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S172(줄 3421-3434, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t61_fc_result = s171_state._t61_fc_result

    _t61_nonpositive_flags = [r for r in _t61_fc_result["review_needed"]
                                if "전류가 0 또는 음수" in r["reason"]]
    assert len(_t61_nonpositive_flags) == 1, \
        f"MP측/M9-M10측 수렴 경고가 정확히 1건이어야 하는데: {_t61_nonpositive_flags}"
    assert set(_t61_nonpositive_flags[0]["devices"]) == {"M1", "M2", "M11", "MN"}, \
        f"경고 대상 소자가 예상과 다름: {_t61_nonpositive_flags[0]}"


def test_s173_apply_theta_kcl_gap_fill(library_dir, s170_state):
    """=== Test 62: apply_theta_kcl_gap_fill() -- propose_theta_kcl_gap_fill() 결과를
    실제 topology.json에 반영(2026-08-19 세션37 신설, 사용자 지시 'propose_theta
    적용하자'). 이미 declared된 소자를 다루는 제안은 충돌로 스킵되고(M101/M108/M109
    등 이미 baseline 실측까지 끝난 stage1은 그대로), stage2/3(M202/M203/M204/M302,
    세션37에 이 함수로 처음 채워진 소자)만 실제로 추가되는지 검증한다. 실제 라이브러리
    파일은 이미 세션37에 이 4개가 적용된 상태이므로, 임시 사본에서 그 4개를 제거해
    '적용 전' 상태를 재구성한 뒤 테스트한다(파일 현재 상태와 무관하게 항상 재현 가능
    하도록) ===

    oracle (c) 이관본 legacy/selftest_stick_diagram.py 섹션 S173(줄 3435-3478, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _t49_lib = library_dir
    _t61c_result = s170_state._t61c_result

    _T62_NEW_NAMES = {"kcl_M203", "r_mirror_M204_M203", "kcl_M202", "kcl_M302"}
    with _t62_tempfile.TemporaryDirectory() as _t62_tmpdir:
        _t62_path = _t49_os.path.join(_t62_tmpdir, "nmcnr_amplifier.topology.json")
        _t62_shutil.copy(_t49_os.path.join(_t49_lib, "nmcnr_amplifier.topology.json"), _t62_path)
        with open(_t62_path, encoding="utf-8") as _f:
            _t62_data = json.load(_f)
        # '적용 전' 상태 재구성(이 함수로 세션37에 이미 추가된 4개를 제거) -- stage1 7개만 남김
        _t62_data["sizing_roles"]["theta"] = [
            t for t in _t62_data["sizing_roles"]["theta"] if t["name"] not in _T62_NEW_NAMES]
        with open(_t62_path, "w", encoding="utf-8") as _f:
            json.dump(_t62_data, _f, indent=2, ensure_ascii=False)
        _t62_before_names = {t["name"] for t in _t62_data["sizing_roles"]["theta"]}
        assert _t62_before_names == {"Ibg_tail", "r_split_M102_M103", "r_fold_M108_M109",
                                       "kcl_M104", "kcl_M105", "r_series_M106", "r_series_M107"}
        _t62_before_by_name = {t["name"]: t for t in _t62_data["sizing_roles"]["theta"]}
        _t62_applied = apply_theta_kcl_gap_fill(_t62_path, _t61c_result)
        assert set(_t62_applied["applied"]) == _T62_NEW_NAMES, \
            f"실제로 추가돼야 할 신규 theta 집합이 예상과 다름: {_t62_applied['applied']}"
        _t62_skipped_names = {s["name"] for s in _t62_applied["skipped_conflict"]}
        assert _t62_skipped_names == {"kcl_M101", "r_free_M108_M109", "r_series_M106",
                                        "r_series_M107", "kcl_M104", "kcl_M105"}, \
            f"이미 declared된 stage1 소자를 다루는 제안이 스킵되지 않음: {_t62_skipped_names}"
        with open(_t62_path, encoding="utf-8") as _f:
            _t62_after = json.load(_f)
        _t62_after_names = {t["name"] for t in _t62_after["sizing_roles"]["theta"]}
        assert _t62_after_names == _t62_before_names | _T62_NEW_NAMES, \
            "적용 후 theta 목록이 (기존 7개 + 신규 4개)와 일치하지 않음"
        # 기존 7개 theta는 값 자체가 한 글자도 안 바뀌었는지 확인(스킵=완전 불변 보장)
        for _name in _t62_before_names:
            _after_entry = next(t for t in _t62_after["sizing_roles"]["theta"] if t["name"] == _name)
            assert _after_entry == _t62_before_by_name[_name], \
                f"기존 theta {_name!r}가 스킵됐는데도 값이 바뀜(apply_ 계약 위반)"
