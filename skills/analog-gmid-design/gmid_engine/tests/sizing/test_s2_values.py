"""`s2_values` (데이터 선언 모듈) -- CONTRACT 2절: S2 dc 필드 권한표 `S2_WRITERS` = S1 권한표 전부 + dc 필드(필드마다 writer
하나), 값 형식은 frozen dataclass, 어휘 상수.

기대 표는 CONTRACT 2절 표를 이 파일에 옮겨 적은 것이다(피검 상수로 기대값을 만들지 않는다).
"""
import dataclasses

import pytest

from gmid_engine.core import WriterPermissionError, require_immutable
from gmid_engine.graph import S1_WRITERS
from gmid_engine import sizing as S

# CONTRACT 2절 표 (kind, field) -> writer  (graph.dc_seal_1/2/3/6/7/8 행은 6개로 풀어 적음)
DC_TABLE = {
    ("node", "dc_rail_v"): "dc_rails",
    # [U17 ①-d] 40 v1.8 §6-8 D-2·§2.4.8: 구조 색 dc_colour·궤도·전류 부호는 graph 대칭 블록(s1_symmetry, S1 권한표)으로 옮겼고 dc_orbit·
    # dc_symmetry 는 graph/s1 orbits·current_symmetry 로 대체됐다 -- dc 표에서 다섯 행을 지운다(S1 권한표 쪽은 tests/graph/test_s1_values.py).
    ("graph", "dc_current_basis"): "dc_current_basis",
    ("node", "dc_writer"): "dc_writer_plan",
    ("device", "dc_coord"): "dc_writer_plan",
    ("graph", "dc_tie_breaks"): "dc_writer_plan",           # [r2]
    # [IT-2b 갱신 -- 표 확대, 약화 아님] design 41 v1.12.8 4.7-1a: 출력 구조 분류 필드의 writer 는 쓰기 계획 블록 하나(DC_WRITES 의
    # DC_WRITER_PLAN_WRITER 행에 더함, 계획 N3.8 '출력 구조 분류 -- 규칙 하나').
    ("node", "dc_output_structure"): "dc_writer_plan",
    # [U17 ①-b] 설계 40 v1.9.1 §2.4.8 '1변수 writer 집합(sctx.cell_floors[("one_var_writers",)]) -> device: dc_self_referential, writer 쓰기 계획 블록(sizing)'
    ("device", "dc_self_referential"): "dc_writer_plan",
    # [U17 ①-b] §2.4.8 '커널 컨텍스트 구조 파생 -> graph/kernel: fixed_values·resistor_values·l_ties, writer build_kernel_context 를 블록으로(sizing)'
    # -- writer 이름은 design 미정이라 구현 이름(kernel_context)에 맞춘다(이름만).
    ("graph", "fixed_values"): "kernel_context",
    ("graph", "resistor_values"): "kernel_context",
    ("graph", "l_ties"): "kernel_context",
    ("graph", "dc_scc_order"): "dc_scc_order",
    ("node", "dc_column_nbrs"): "dc_scc_order",
    # [U17 ①-b] 설계 40 v1.9 §2.4.8 커널 컨텍스트 구조 파생 행 + 오케스트레이터 기본안 D8(2026-10-13): θ 스키마 필드는 graph/kernel 의
    # `theta_schema`(옛 graph/dc `dc_theta_schema` 를 옮김, writer dc_theta_schema 유지).
    ("graph", "theta_schema"): "dc_theta_schema",
    ("device", "dc_current"): "dc_currents",
    ("device", "dc_drop_current"): "dc_currents",
    ("device", "dc_L"): "dc_lengths",
    ("node", "dc_v"): "dc_columns",
    ("node", "dc_path_values"): "dc_columns",
    ("node", "dc_window"): "dc_columns",
    ("device", "dc_ln_idu"): "dc_columns",
    ("graph", "dc_scc_log"): "dc_columns",
    ("device", "dc_op"): "dc_widths",
    ("device", "dc_tol_v"): "dc_tolerances",
    ("device", "dc_gm"): "dc_tolerances",                    # [U17 ①] 설계 40 §2.4.8 소유표·§3.7-3 (옛 dc_gm_bound 폐기)
    ("graph", "dc_seal_1"): "dc_seal_node_conflict",
    ("graph", "dc_seal_2"): "dc_seal_vgs_match",
    ("graph", "dc_seal_3"): "dc_seal_kcl",
    ("graph", "dc_seal_6"): "dc_seal_bulk_reverse",
    ("graph", "dc_seal_7"): "dc_seal_saturation",
    ("graph", "dc_seal_8"): "dc_seal_kvl_branch",
    ("graph", "dc_seal_9"): "dc_seal_conduction",                 # [r8]
    ("device", "dc_off_current"): "dc_seal_conduction",           # [r8]
    ("device", "dc_conduction_floor"): "dc_seal_conduction",      # [r8]
    ("graph", "dc_seal_report"): "dc_seal_report",
}

BLOCKS = {
    "dc_rails": S.dc_rails, "dc_current_basis": S.dc_current_basis, "dc_writer_plan": S.dc_writer_plan,
    "dc_scc_order": S.dc_scc_order, "dc_theta_schema": S.dc_theta_schema, "dc_currents": S.dc_currents,
    "dc_lengths": S.dc_lengths, "dc_columns": S.dc_columns, "dc_widths": S.dc_widths,
    "dc_tolerances": S.dc_tolerances, "dc_seal_node_conflict": S.dc_seal_node_conflict,
    "dc_seal_vgs_match": S.dc_seal_vgs_match, "dc_seal_kcl": S.dc_seal_kcl,
    "dc_seal_bulk_reverse": S.dc_seal_bulk_reverse, "dc_seal_saturation": S.dc_seal_saturation,
    "dc_seal_kvl_branch": S.dc_seal_kvl_branch, "dc_seal_conduction": S.dc_seal_conduction,
    "dc_seal_report": S.dc_seal_report,
}


def test_dc_table_has_34_fields():
    # CONTRACT 2절 표의 행 수(봉인 행을 6개로 풀면 r1 25 + r2 3 = 28, [r8] dc_seal_9·dc_off_current·dc_conduction_floor 3 = 31,
    # [r11] 3.0b node.dc_orbit·device.dc_orbit 2 = 33, [U2] graph.dc_symmetry 1 = 34, [U17 ①-d] 대칭 블록 graph 이동 −5
    # (node/device dc_colour·dc_orbit, graph.dc_symmetry) = 29, [U17 ①-b] 설계 40 v1.9.1 §2.4.8 S0 행 +4: device.dc_self_referential(1변수 writer 집합),
    # graph/kernel fixed_values·resistor_values·l_ties(커널 컨텍스트 구조 파생) = 33. theta_schema 는 dc_theta_schema 를 옮긴 것이라 ±0).
    # [IT-2b 갱신] node.dc_output_structure(writer dc_writer_plan, design 41 4.7-1a) +1 = 34.
    assert len(DC_TABLE) == 34


# [ss_linearize 커밋이 바꾼 행] S2 권한표 = S1 + dc + ss·metric 필드(sizing CONTRACT 2절 끝 표, metrics CONTRACT 7절).
# 옛 기대 'S1 + dc 만' 은 ss 필드 배선으로 대체된 동작이다 -- 독립 test 작성자가 계약 표에서 다시 확인할 대상.
SS_TABLE = {
    ("device", "ss_dev"): "ss_dev",
    ("graph", "metrics_ss"): "metrics_ss",
    ("graph", "metrics_dc"): "metrics_dc",
    # [U7 2026-10-09] oracle (d): sizing CONTRACT 2절 끝 표 행 'graph.metrics_aux | metrics_aux' + metrics CONTRACT 10.0
    # ('metrics_aux(@compute_block, writer metrics_aux, 필드 graph.metrics_aux)') -- 계약 표에서 옮겨 적은 행이다.
    ("graph", "metrics_aux"): "metrics_aux",
    # [U17 ①] 설계 40 §2.4.8 소유표 행 '게이트 면적·전력 분해능 | graph/metrics: gate_area_m2, power_resolution_w | metrics_dc'
    # (§2.4.7 Objectives 행: metrics_dc 가 쓰고 search 는 다시 계산하지 않는다).
    ("graph", "gate_area_m2"): "metrics_dc",
    ("graph", "power_resolution_w"): "metrics_dc",
    # [U17 ①] 설계 40 §2.4.8 소유표 행 '수동소자 값 | device: passive_value | GB5 수동소자 블록(passive_values 를 블록으로)' -- 블록
    # 이름 = writer 이름 규약(위 metrics_* 행과 같음)이라 writer 는 `passive_values`(구현 공개 이름 PASSIVE_VALUES_WRITER 와 같다).
    ("device", "passive_value"): "passive_values",
}


def test_s2_writers_is_s1_plus_dc_table_exactly():
    s1 = dict(S1_WRITERS.entries)
    s2 = dict(S.S2_WRITERS.entries)
    expected = dict(s1)
    expected.update(DC_TABLE)
    expected.update(SS_TABLE)
    assert s2 == expected
    assert len(S.S2_WRITERS.entries) == len(S1_WRITERS.entries) + len(DC_TABLE) + len(SS_TABLE)
    for k, w in s1.items():
        assert S.S2_WRITERS.writer_of(*k) == w


def test_one_writer_per_field_and_permission_enforced():
    keys = [k for k, _ in S.S2_WRITERS.entries]
    assert len(keys) == len(set(keys))
    for (kind, field), w in DC_TABLE.items():
        assert S.S2_WRITERS.require(w, kind, field) is None
        with pytest.raises(WriterPermissionError):
            S.S2_WRITERS.require("not_" + w, kind, field)


def test_dc_writes_constant_matches_table():
    got = {}
    for w, fields in S.DC_WRITES:
        for f in fields:
            assert f not in got
            got[f] = w
    assert got == DC_TABLE


@pytest.mark.parametrize("name", sorted(BLOCKS))
def test_block_name_and_writes_match_table(name):
    b = BLOCKS[name]
    assert b.name == name
    assert set(b.writes) == {k for k, w in DC_TABLE.items() if w == name}


# CONTRACT 3·4·5절이 reads 를 다 적은 블록(writer_plan·theta_schema 는 이번 판 범위 밖)
READS = {
    "dc_rails": {("node", "is_rail")},
    # [U17 ①-d] 40 §6-3 전류 기저 열 순서 규칙: current_basis 는 graph/s1 orbits 를 읽는다
    "dc_current_basis": {("device", "dc_nets"), ("device", "element_class"), ("device", "kind"), ("device", "pins"),
                         ("device", "dc_colour"), ("node", "is_rail"), ("graph", "dc_pruned"), ("graph", "orbits")},
    "dc_writer_plan": {("device", "element_class"), ("device", "is_diode"), ("device", "kind"), ("device", "pins"),
                       ("device", "dc_colour"), ("node", "is_rail"), ("node", "port_direction"),
                       ("node", "dc_colour"),
                       ("device", "bulk")},      # [U17 ①-b] dc_self_referential(§2.4.8) = 쓰는 노드가 자기 d·s·bulk 중 하나 -- bulk 를 읽는다
    "dc_scc_order": {("node", "dc_writer"), ("device", "pins"), ("device", "bulk"), ("device", "element_class"),
                     ("graph", "columns"), ("graph", "branches")},
    "dc_currents": {("graph", "dc_current_basis")},
    "dc_lengths": {("device", "element_class")},
    "dc_columns": {("node", "dc_writer"), ("node", "dc_rail_v"), ("node", "dc_column_nbrs"),
                   ("device", "dc_drop_current"), ("device", "dc_L"), ("device", "pins"), ("device", "kind"),
                   ("device", "bulk"), ("device", "element_class"), ("device", "dc_coord"),
                   ("graph", "dc_scc_order"),
                   ("device", "dc_self_referential"),   # [U17 ①-b] §2.4.8 1변수 writer 집합은 S0 필드 -- 기둥 블록이 읽는다
                   ("device", "dc_colour"), ("node", "dc_colour"),
                   ("node", "port_direction")},   # [IT-1 K-3 ext, O-84] 41:672 -- 입력 포트 판정은 S1 포트 방향 READS     # [r11] 3.0b: writer·SCC 소자 정렬, 기둥 합산 출발 레일·이웃 정렬 = 색
    "dc_widths": {("node", "dc_v"), ("node", "dc_rail_v"), ("device", "dc_current"), ("device", "dc_L"),
                  ("device", "dc_ln_idu"), ("device", "pins"), ("device", "kind"), ("device", "bulk")},
}


def test_seal_conduction_reads_cover_contract_inputs():
    """[r8] 6절 9행: 판정은 device.dc_op(kind·w_key·L·vds·vsb·W·current·gm_id)와 device.dc_tol_v 를 읽는다
    (계약이 reads 를 전부 열거하지 않아 부분집합으로만 확인)."""
    assert {("device", "dc_op"), ("device", "dc_tol_v")} <= set(S.dc_seal_conduction.reads)


@pytest.mark.parametrize("name", sorted(READS))
def test_block_reads_declared_as_contract(name):
    assert set(BLOCKS[name].reads) == READS[name]


def test_theta_schema_reads_include_structural_rule_fields():
    """[r5] 4.4: dc_theta_schema 의 reads 에 구조 규칙용 S1 필드 device.{pins, bulk}, node.{terminals, is_rail,
    port_direction, ac_ground_class} 가 든다(나머지 reads 는 4.4 가 다 적지 않아 부분집합으로만 확인)."""
    need = {("device", "pins"), ("device", "bulk"), ("node", "terminals"), ("node", "is_rail"),
            ("node", "port_direction"), ("node", "ac_ground_class")}
    assert need <= set(S.dc_theta_schema.reads)


def test_vocabulary_constants():
    assert S.DC_KEY == "dc"
    assert (S.TIER_W0, S.TIER_W1, S.TIER_W2, S.TIER_W3, S.TIER_W4) == ("W0", "W1", "W2", "W3", "W4")
    assert (S.REL_RAIL, S.REL_TARGET, S.REL_INPUT_DC, S.REL_VGS_GATE, S.REL_VGS_SOURCE, S.REL_RESISTOR,
            S.REL_WINDOW, S.REL_INPUT_POINT) == ("rail", "declared_target", "input_dc", "vgs_gate", "vgs_source",
                                                 "resistor_drop", "free_window", "input_point")        # [IT-1 DEC-106] 여덟째 relation
    assert (S.COORD_WRITER, S.COORD_DEPENDENT) == ("writer", "dependent")
    assert (S.DEP_TREE, S.DEP_PARALLEL, S.DEP_CYCLE, S.DEP_FIXED) == ("tree", "parallel_vgs", "cycle_vgs", "fixed_vgs")
    assert not hasattr(S, "INPUT_GROUP_KEY") and not hasattr(S, "REL_TIE")          # [IT-1 K-3] 어휘 제거
    assert (S.REPORT_VIOLATED, S.REPORT_UNDEFINED, S.REPORT_SEALED) == ("violated", "undefined", "sealed")
    assert (S.SEAL_NODE_CONFLICT, S.SEAL_VGS_MATCH, S.SEAL_KCL, S.SEAL_VERSIONS, S.SEAL_WRITER_UNIQUE,
            S.SEAL_BULK_REVERSE, S.SEAL_SATURATION, S.SEAL_KVL_BRANCH, S.SEAL_CONDUCTION) == (1, 2, 3, 4, 5, 6, 7, 8, 9)
    assert (S.REASON_EMPTY_WINDOW, S.REASON_LUT_QUERY, S.REASON_TOL_UNDEFINED,
            S.REASON_VDSAT_MISSING, S.REASON_DECLARED_KCL, S.REASON_NO_ROOT, S.REASON_STRICT_RECHECK) == (
        "empty_window", "lut_query_failed", "tol_v_undefined",
        "lut_vdsat_column_missing", "declared_source_kcl_conflict", "no_root_in_window", "strict_recheck_residual")
    # [r2] 옛 device_current_nonpositive 는 없어졌다(정의역 밖 = ValueError)
    assert not hasattr(S, "REASON_CURRENT_NONPOSITIVE")
    assert (S.TIE_KRUSKAL, S.TIE_ROOT, S.TIE_CURRENT_PIVOT) == (
        "writer_edge", "w4_root", "current_pivot")
    assert not hasattr(S, "TIE_INPUT_ORDER")
    assert not hasattr(S, "BRANCH_INPUT_MULTIPLE_ROOTS")                             # [IT-1 DEC-106] 옛 사유 삭제
    from gmid_engine.sizing import s2_values as _s2v
    assert _s2v.BRANCH_INPUT_CM_UNDEFINED == "input_cm_undefined"
    assert not hasattr(_s2v, "BRANCH_INPUT_MULTIPLE_ROOTS")
    assert S.BRANCH_RESISTOR_CYCLE == "dc_resistor_cycle"
    assert S.BRANCH_MOS_ZERO_CURRENT == "mos_zero_current_structural"
    # [r5] 4.4: capacitance(engine 커패시터)·ss_resistance(DC 전류 0 engine 저항 중 구조 규칙 밖) 추가, 둘 다 DC 블록이 읽지 않는
    # THETA_PASSIVE_KINDS(4.4·7절)
    assert set(S.THETA_KINDS) == {"ln_idu", "L", "y", "current", "resistance", "capacitance", "ss_resistance"}
    assert set(S.THETA_PASSIVE_KINDS) == {"capacitance", "ss_resistance"}
    assert set(S.THETA_PASSIVE_KINDS) <= set(S.THETA_KINDS)
    # [r5] 4.4 영점 상쇄 구조 규칙 판정 reason 어휘
    assert (S.ZC_NO_CAPACITOR, S.ZC_MULTIPLE_RESISTORS, S.ZC_RESISTOR_END, S.ZC_NO_CELL, S.ZC_MIXED_DIRECTION) == (
        "network_without_capacitor", "network_multiple_resistors", "resistor_end_not_unique", "no_cs_cell",
        "cs_cell_direction_mixed")


def test_it2b_output_structure_vocabulary_and_window_status_defaults():
    """oracle 대조: (d) 사용자 선언 스펙값 -- design 41 v1.12.8 4.7-1a·4.7-2: 출력 구조 분류 값은 두 문자열뿐이고(상수 `OUTPUT_HIGH_IMPEDANCE`·
    `OUTPUT_KVL_FIXED`, 모듈 `gmid_engine.sizing.s2_values`), `Window` 의 새 칸 기본값은 (input_status None, tol_v None).
    [O-98 반영] `status_detail` 칸은 (S4-나)에서 IT-2b 에 없다 -- 동작점 불일치 묶음은 EO-1 card 몫(계획 v6.33)."""
    from gmid_engine.sizing import s2_values
    assert s2_values.OUTPUT_HIGH_IMPEDANCE == "high_impedance"
    assert s2_values.OUTPUT_KVL_FIXED == "kvl_fixed"
    w = s2_values.Window(0.31, 1.12, 2, input_status="measured", tol_v=1.2e-4)         # 설계 예시 리터럴 (41 4.7-2)
    assert (w.lo, w.hi, w.constraints, w.input_status, w.tol_v) == (0.31, 1.12, 2, "measured", 1.2e-4)
    undefined = s2_values.Window(None, None, 0, input_status="f_component_undeclared")
    assert (undefined.lo, undefined.hi, undefined.input_status) == (None, None, "f_component_undeclared")


def test_value_defaults():
    nw = S.NodeWrite("W0", "rail")
    assert (nw.element, nw.known, nw.y_key, nw.order) == (None, None, None, 0)
    assert S.DeviceCoord("writer", "tree").partner is None
    si = S.SealItem(1, "pass")
    assert (si.magnitude, si.tol, si.margin, si.devices, si.nodes, si.detail) == (None, None, None, (), (), ())
    assert S.DcEvaluation(None, None).sealed is None
    di = S.DcInputs((("gnd", 0.0),))
    assert (di.input_dc_v, di.node_targets, di.element_values, di.linear_devices, di.pending) == (None, (), (), (), ())


VALUE_INSTANCES = [
    S.NodeWrite("W2", "vgs_gate", "M1", "gnd", None, 3),
    S.DeviceCoord("dependent", "parallel_vgs", "M1"),
    S.CurrentTerm("M2", 1, 1),
    S.ColumnNeighbor(("gnd", "vdd"), "gnd", "vdd", 1, 2),
    S.SccEntry(0, ("out",), False, ("M1",)),
    S.PathValue(("vgs", "M1"), 0.5),
    S.Window(0.0, 1.8, 2),
    S.SealItem(1, "pass", 0.0, 1.0, 0.0, (), (), (("n_checked", 1),)),
    S.DeviceOp("nmos", 1e-5, -13.0, 10.0, 1e-6, 2e-6, 0.6, 0.9, 0.0, 100, 1e-6),
    S.DcInputs((("gnd", 0.0), ("vdd", 1.8))),
    S.DcInputs((("gnd", 0.0), ("vdd", 1.8)), engine_elements=("Cc", "Rz")),
    S.ZeroCancel("Rz", "out", ("in",), ("M1",)),
    S.ThetaSchema((("L", "M1"),), zero_cancel=(S.ZeroCancel("Rz", None, (), (), "resistor_end_not_unique"),)),
]


@pytest.mark.parametrize("obj", VALUE_INSTANCES, ids=lambda o: type(o).__name__)
def test_values_frozen_and_immutable(obj):
    assert dataclasses.is_dataclass(obj)
    assert require_immutable(obj) is None
    f = dataclasses.fields(obj)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(obj, f, None)


def test_value_fields_as_contract():
    def names(c):
        return tuple(f.name for f in dataclasses.fields(c))
    assert names(S.NodeWrite) == ("tier", "relation", "element", "known", "y_key", "order")
    assert names(S.DeviceCoord) == ("role", "relation", "partner")
    assert names(S.CurrentTerm) == ("source", "num", "den")
    assert names(S.CurrentBasis) == ("ends", "mos", "free", "fixed", "rows", "pruned", "resistors", "ties")
    assert names(S.TieBreak) == ("decision", "candidates", "chosen")
    assert names(S.ThetaSchema) == ("components", "current_cone", "fixed", "zero_cancel")      # [r5]
    ts = S.ThetaSchema((("L", "M1"),))
    assert ts.current_cone == () and ts.fixed == () and ts.zero_cancel == ()
    assert names(S.ZeroCancel) == ("resistor", "end_net", "far_nets", "cells", "reason")        # [r5]
    assert S.ZeroCancel("Rz", "out", ("in",), ("M1",)).reason is None
    assert names(S.ColumnNeighbor) == ("rails", "pred", "succ", "position", "length")
    assert names(S.SccEntry) == ("index", "nodes", "cyclic", "devices")
    # [IT-2b 갱신 -- 칸 확대] design 41 4.7-2: 기본값 있는 칸 둘(input_status·tol_v)을 뒤에 더한다(옛 3칸 생성 호환).
    # [O-98 반영] `status_detail` 칸은 IT-2b 에 없다(동작점 불일치 묶음 = EO-1 card, 계획 v6.33).
    assert names(S.Window) == ("lo", "hi", "constraints", "input_status", "tol_v")
    old_window = S.Window(0.0, 1.8, 2)
    assert (old_window.input_status, old_window.tol_v) == (None, None)
    # [r6] method·fallback 필드 추가(옛 6칸 뒤, 6칸 생성 호환). [r7] 2절: 기본값 method="direct", fallback=None.
    assert names(S.SccLog) == ("index", "nodes", "iterations", "deltas", "tol", "k_max", "method", "fallback")
    old = S.SccLog(0, ("x",), 1, (0.0,), 1e-3, 11)
    assert (old.index, old.nodes, old.iterations, old.deltas, old.tol, old.k_max) == (0, ("x",), 1, (0.0,), 1e-3, 11)
    assert old.method == "direct" == S.SCC_DIRECT and old.fallback is None
    # [r6] 5.4 SccLog.method 어휘·5.5b 실패 사유 어휘
    assert (S.SCC_DIRECT, S.SCC_BISECTION, S.SCC_GAUSS_SEIDEL, S.SCC_NEWTON) == (
        "direct", "bisection", "gauss_seidel", "newton")
    assert (S.REASON_NEWTON_START, S.REASON_NEWTON_SINGULAR, S.REASON_NEWTON_LINE_SEARCH, S.REASON_NEWTON_CAP) == (
        "newton_start_outside_domain", "newton_singular", "newton_line_search", "newton_iteration_cap")
    assert names(S.DeviceOp) == ("kind", "current", "ln_idu", "gm_id", "L", "W", "vgs", "vds", "vsb", "w_key",
                                 "idu_forward")
    assert names(S.SealItem) == ("item", "status", "magnitude", "tol", "margin", "devices", "nodes", "detail")
    assert names(S.SealReport) == ("items", "status")
    assert names(S.SealedSnapshot) == ("snapshot", "report")
    assert names(S.DcEvaluation) == ("snapshot", "report", "sealed")
    # [U17 ①-b] KernelContext 칸은 아래 test_kernel_context_holds_only_references 가 본다(옛 8칸 단언 대체).
    # [U4] 국소 봉인 값 형식(41 §5.3 LocalSeal{ok, failures, snapshot_fragment, gain_db, power_w, area_m2})
    assert names(S.LocalSeal) == ("ok", "failures", "snapshot_fragment", "gain_db", "power_w", "area_m2")
    assert names(S.SnapshotFragment) == ("devices", "nodes")
    assert names(S.OrderHints) == ("independent", "gm_required", "stage")
    assert S.NO_ORDER_HINTS == S.OrderHints((), (), ())
    assert names(S.DcInputs) == ("supplies_v", "input_dc_v", "node_targets", "element_values", "linear_devices",
                                 "pending", "engine_elements")                                   # [r5]


def test_kernel_context_holds_only_references():
    """[U17 ①-b] 설계 40 v1.9 §2.4.7 KernelContext 행: 설계 값 사본(`schema`(θ 스키마)·`fixed_values`·`resistor_values`·`l_ties`)은 S0 수준
    필드 `graph/kernel: theta_schema·fixed_values·resistor_values·l_ties`(§2.4.8)로 가고 `plan_versions` 는 쓰기 계획 블록의 block_version
    읽기로 대체된다. '남는 칸은 참조(`base` = S0 수준 스냅샷, `lut` = LUT memo 와 폭 키, `inputs` = spec 파싱 결과)' -> 칸 이름은 그 셋 안.
    [XRUN-F1 card B C6] + 실행 두 객체 참조 칸 `donors`·`counters`('결과 KernelContext 칸 donors·counters(is)') -- 역시 참조라 위 원칙과 맞다."""
    fields = {f.name for f in dataclasses.fields(S.KernelContext)}
    assert not fields & {"schema", "fixed_values", "resistor_values", "plan_versions", "l_ties"}, fields
    assert fields <= {"base", "inputs", "lut", "donors", "counters"}, fields
    assert {"donors", "counters"} <= fields, fields
