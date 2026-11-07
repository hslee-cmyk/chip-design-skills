"""`metrics_aux` 계산 블록과 `ss_evaluate` 배선 -- metrics CONTRACT 10.0·10.7, 설계 40 §3.8(판정 위치 = 외층 전회로 계산 한 곳, DEC-74),
41 §2.2(평가마다 `gain_residual_db`·`ss.block_gain` 기록).

회로·DC 점: `test_ss_evaluate` 와 같은 CS + 저항 부하(toy LUT r6, 실제 sizing 경로 size_and_seal). toy LUT 에는 VDSAT 열·mismatch 감도 표가 없다.

oracle:
* (d) 계약 10.7·설계 40 §3.8-8 문장: AUX 결과 형식 metric 은 metrics_aux 가 계산해 `SsEvaluation.ss` 에 합쳐진다, 입력이 없으면 정의 불가 사유
  (mismatch 없음 `mismatch_source_missing`, LUT mismatch 표 없음 `mismatch_lut_missing`, 포화 열 없음 `sat_unavailable`(DEC-88 근사 안 함),
  단일 출력 기준 미선언 `reference_undeclared`, 구조 입력 없음 `structure_unavailable`). 구조가 있으면 전달 뷰마다 `block_residual`·`nqs_ratio` 보고.
* (a) 단일 블록(CS) 분해 잔차 0, 전회로 이득 = 폐형식 20·log10(gm/(gds + 1/R))(test_ss_evaluate 의 `_expected` 와 같은 독립 npz 해석식).
"""
from __future__ import annotations

import pytest

from gmid_engine.core import PdkMismatchBlock, PdkMismatchModel
from gmid_engine.metrics import (REPORT_BLOCK_RESIDUAL, MetricBundle, MismatchSource, ss_evaluate)
from gmid_engine.sizing import METRICS_KEY, SealedSnapshot

from . import u7_hand as H
from .conftest import codes
from .test_ss_evaluate import _expected, build, theta

AUX = (("offset_in_sigma_mv", "<=", 3.0, None), ("offset_sys_mv", "<=", 3.0, None), ("swing_out_v", ">=", 0.1, None),
       ("ff_gm_ratio", ">=", 1.0, None))
BASE = (("gain_ss_db", ">=", 10.0, None),)


def _struct():
    return H.vstruct("transfer:0", {"in": 1.0}, ("out",), (H.block(("out",), ("in",), ("out",), ("in", "out"), input_cells=("M1",)),),
                     (), ("M1",), ("M1",))


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    spec, ctx, ev, js = build(tmp_path_factory.mktemp("aux"), cons=BASE + AUX)
    return spec, ctx, SealedSnapshot(ev.snapshot, ev.report), js


def _codes_by_metric(bundle):
    return {req.metric: codes(res.undefined) for req, res in bundle.entries}


def test_aux_entries_merged_after_ss_entries_and_field_written(case):
    spec, ctx, sealed, js = case
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js)
    assert [q.metric for q, _ in res.ss.entries] == ["gain_ss_db", "offset_in_sigma_mv", "offset_sys_mv", "swing_out_v", "ff_gm_ratio"]
    aux = res.snapshot.value("graph", METRICS_KEY, "metrics_aux")
    assert isinstance(aux, MetricBundle)
    assert [q.metric for q, _ in aux.entries] == ["offset_in_sigma_mv", "offset_sys_mv", "swing_out_v", "ff_gm_ratio"]
    assert [q.metric for q, _ in res.snapshot.value("graph", METRICS_KEY, "metrics_ss").entries] == ["gain_ss_db"]


def test_missing_inputs_are_undefined_not_silent(case):
    spec, ctx, sealed, js = case
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js)
    got = _codes_by_metric(res.ss)
    assert got["offset_in_sigma_mv"] == {"mismatch_source_missing"}
    assert got["offset_sys_mv"] == {"reference_undeclared"}
    assert got["swing_out_v"] == {"sat_unavailable"}
    assert got["ff_gm_ratio"] == {"structure_unavailable"}
    assert all(res_.value is None for q, res_ in res.ss.entries if q.metric != "gain_ss_db")


def test_mismatch_source_without_lut_table(case):
    spec, ctx, sealed, js = case
    rows = (("toxe", "toy_toxe_slope", 1e-3, 1),)
    model = PdkMismatchModel("nmos", ("toxe",), (PdkMismatchBlock("b", 1e-7, 1e-4, 1e-7, 1e-4, rows, 1),), "0" * 64, "0" * 64)  # [U17 ①-b 3차] 경로 칸 없음
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, mismatch=MismatchSource((("nmos", model),), "1" * 64))
    assert _codes_by_metric(res.ss)["offset_in_sigma_mv"] == {"mismatch_lut_missing"}


def test_structure_gives_block_residual_and_nqs_reports(case):
    spec, ctx, sealed, js = case
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, structure=H.MetricStructure_of(_struct()))
    reports = dict(res.ss.reports)
    br = dict(reports[REPORT_BLOCK_RESIDUAL])
    exp = _expected(res.snapshot)
    assert br["full_gain_db"] == pytest.approx(exp["gain_db"], rel=1e-12)
    assert br["gain_residual_db"] == pytest.approx(0.0, abs=1e-9)
    assert br["view"] == "transfer:0"
    gain = {req.metric: r.value for req, r in res.ss.entries}["gain_ss_db"]
    assert br["full_gain_db"] == pytest.approx(gain, rel=1e-12)            # 같은 계(같은 뷰 = 같은 계, 계약 10.2)
    nqs = dict(reports["nqs_ratio"])
    assert nqs["undefined"] == ("ugf_unavailable",)                          # ugf 제약 없음 -> 분자 없음
    assert _codes_by_metric(res.ss)["ff_gm_ratio"] == {"no_feedforward"}


def test_aux_does_not_change_ss_metric_values(case):
    spec, ctx, sealed, js = case
    plain = ss_evaluate(sealed, ctx, theta(), tuple(c for c in spec.constraints if c.metric == "gain_ss_db"), junction=js)
    full = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, structure=H.MetricStructure_of(_struct()))
    a = {q.metric: r.value for q, r in plain.ss.entries}
    b = {q.metric: r.value for q, r in full.ss.entries}
    assert a["gain_ss_db"] == b["gain_ss_db"]


def test_no_aux_request_no_structure_keeps_metrics_ss_bundle(case):
    spec, ctx, sealed, js = case
    res = ss_evaluate(sealed, ctx, theta(), tuple(c for c in spec.constraints if c.metric == "gain_ss_db"), junction=js)
    assert res.ss is res.snapshot.value("graph", METRICS_KEY, "metrics_ss")


def test_deterministic(case):
    spec, ctx, sealed, js = case
    a = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, structure=H.MetricStructure_of(_struct()))
    b = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, structure=H.MetricStructure_of(_struct()))
    assert a.ss == b.ss


# =====================================================================================================================
# [IT-2d 재동결 20261104-it2d-front-wiring] 세 metric(`icm_margin_v`·`icmr_v`·`required_input_cm_v`)은 `graph.icm_config` V_cm 칸에서, 결측 판정(B77)은
# `MetricSignature.domain` 으로. 회로: search 하네스 회로 C(M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd)), r4 toy LUT(VDSAT 열 있음).
# oracle: (손) interface 세 metric 정의(margin = min(vcm0 − vcm_lo, vcm_hi − vcm0), icmr = vcm_hi − vcm_lo, required = (vcm0, vcm_lo, vcm_hi)
# 또는 None) -- 입력 칸 `graph.icm_config`(IT-2c 가 쓰는 graph 필드, 피검 함수 아님)의 숫자에서 test 가 손 산술로 다시 계산한다.
# vcm0 = 봉인점 입력 포트 전압 평균 = 선언 입력 DC 0.6 V(M1 gate = source(gnd) + VGS 0.6, θ_r4c v1 = 0.6) -- 독립 값.
# (독립) AST·READS·registry 영역 표. 13회로 값은 쓰지 않는다(O-225).
# =====================================================================================================================

from . import it2d_toys as T
from .conftest import toy_junction
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
from fs1_wf import size_and_seal      # [FS-1 서명 맞춤] 손 wf 를 끼운 래퍼

ICM_CONS = (("icm_margin_v", ">=", 0.0, None), ("icmr_v", ">=", 0.0, None), ("swing_out_v", ">=", 0.0, None))
GAIN = (("gain_ss_db", ">=", 10.0, None),)
DC_METRICS = ("swing_out_v", "icmr_v", "icm_margin_v")


@pytest.fixture(scope="module")
def r4_lut(tmp_path_factory):
    from sizing.conftest import write_r4_lut
    return write_r4_lut(tmp_path_factory.mktemp("it2d_r4"))


def _circuit_c(with_cap=False, no_input_port=False):
    from search.conftest import circuit_c
    d = circuit_c(with_cap=with_cap)
    if no_input_port:                      # 입력 포트 0: gate in 은 바이어스 입력(gate 전용 넷)으로만 선언
        del d["ports"]["in"]
        d["bias_inputs"] = ["pb", "in"]
    return d


def _theta_declared():
    """입력 DC 를 선언하면 M1 gate 가 선언 값이라 ln_idu(M1)는 θ 성분이 아니다(스키마)."""
    from search.conftest import theta_r4c
    th = dict(theta_r4c())
    del th[("ln_idu", "M1")]
    return th


def _hand_margin(cfg):
    return min(cfg.vcm0 - cfg.vcm_lo, cfg.vcm_hi - cfg.vcm0)


def test_it2d_m1_declared_input_values_from_icm_config(tmp_path, r4_lut):
    """입력 DC 선언(0.6 V) toy: icm_margin_v·icmr_v 는 graph.icm_config V_cm 칸의 손 산술 값, required_input_cm_v None, input_dc declared.
    전제(어기면 무효): 구성 as_is_single_input, V_cm 창이 측정됨(None 아님), vcm0 = 선언 입력 DC 0.6."""
    from search.conftest import CELLS_C
    case = T.build(tmp_path, r4_lut, _circuit_c(), constraints=GAIN + ICM_CONS, input_dc=0.6)
    _, ref = T.sealed_ss(case, _theta_declared(), CELLS_C)
    cfg = ref.snapshot.value("graph", METRICS_KEY, "icm_config")
    assert cfg.config == "as_is_single_input" and None not in (cfg.vcm0, cfg.vcm_lo, cfg.vcm_hi)
    assert cfg.vcm0 == pytest.approx(0.6, abs=1e-9)
    got = T.by_metric(ref.ss)
    assert got["icm_margin_v"].value == pytest.approx(_hand_margin(cfg), abs=1e-12)
    assert got["icmr_v"].value == pytest.approx(cfg.vcm_hi - cfg.vcm_lo, abs=1e-12)
    assert not T.undefined_codes(got["icm_margin_v"]) and not T.undefined_codes(got["icmr_v"])
    rep = dict(ref.ss.reports)["swing_icmr"]
    assert T.field(rep, "required_input_cm_v") is None and T.field(rep, "input_dc") == "declared"
    assert T.field(rep, "v_icm") == pytest.approx(cfg.vcm0, abs=1e-12)
    assert T.field(rep, "window") == pytest.approx((cfg.vcm_lo, cfg.vcm_hi), abs=1e-12)


@pytest.mark.parametrize("mode", ["engine", "pending"])
def test_it2d_m1_undeclared_input_gives_required_tuple(tmp_path, r4_lut, mode):
    """입력 DC 미선언(spec `engine`·`pending` 둘 다): input_dc pending, required_input_cm_v = (vcm0, vcm_lo, vcm_hi)(icm_config 칸에서),
    margin·icmr 값은 선언 toy 와 같은 손 산술. vcm0 = M1 gate 전압 = VGS 0.6(source gnd) -- 독립 값."""
    from search.conftest import CELLS_C, theta_r4c
    case = T.build(tmp_path, r4_lut, _circuit_c(), constraints=GAIN + ICM_CONS, input_dc=mode)
    _, ref = T.sealed_ss(case, theta_r4c(), CELLS_C)
    cfg = ref.snapshot.value("graph", METRICS_KEY, "icm_config")
    assert cfg.config == "as_is_single_input" and None not in (cfg.vcm0, cfg.vcm_lo, cfg.vcm_hi)
    assert cfg.vcm0 == pytest.approx(0.6, abs=1e-6)
    got = T.by_metric(ref.ss)
    assert got["icm_margin_v"].value == pytest.approx(_hand_margin(cfg), abs=1e-12)
    assert got["icmr_v"].value == pytest.approx(cfg.vcm_hi - cfg.vcm_lo, abs=1e-12)
    rep = dict(ref.ss.reports)["swing_icmr"]
    assert T.field(rep, "input_dc") == "pending"
    assert T.field(rep, "required_input_cm_v") == pytest.approx((cfg.vcm0, cfg.vcm_lo, cfg.vcm_hi), abs=1e-12)


def test_it2d_m2_config_none_same_definitional_code_for_metrics(tmp_path):
    """구성 None toy(입력 포트 셋 -> icm_config 갈래 2 `icm_inputs_unsupported`): icm_margin_v·icmr_v 가 icm_config 의 code 를 그대로 옮긴다
    (category definitional), 값 None, detail 에 입력 포트 셋. 입력 포트 0 toy 는 로더가 거부한다(no_input_port) -- 쓰지 않는다.
    전제: graph.icm_config.config 가 None 이고 undefined 가 그 code. 회로: M1~M3 nmos 병렬 CS + 저항 부하 + CL(r6 toy LUT)."""
    from .conftest import fresh_run, load_case, load_lut_v2, lut_access, lut_ln_idu, topo_doc
    from gmid_engine.graph import build_s1
    ports = {"in": ("input", "single_ended_input"), "in2": ("input", "single_ended_input"),
             "in3": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}
    topo = topo_doc("it2d_cs3", mos=[("M1", "nmos", "out", "in", "gnd", "gnd"), ("M2", "nmos", "out", "in2", "gnd", "gnd"),
                                     ("M3", "nmos", "out", "in3", "gnd", "gnd")],
                    passives=[("R1", "resistor", "vdd", "out"), ("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"), ports=ports)
    td, spec = load_case(tmp_path / "case", topo, {"vdd": 1.8, "gnd": 0.0}, (("R1", "resistor", None), ("CL", "capacitor", 1e-12)), (),
                         (("icm_margin_v", ">=", 0.0, None), ("icmr_v", ">=", 0.0, None)), input_dc_v=0.6)
    inputs = dc_inputs_from_spec(spec)
    run = fresh_run()
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs, lut_access(load_lut_v2(tmp_path / "lut")), **run)
    i_each, r_load = 1e-5, 3e4                                    # V(out) = 1.8 − 3·1e-5·3e4 = 0.9 (손 KCL)
    # [A-85 D2] 입력 DC 미선언 + 단일 입력 셋은 DEC-106 로 사이징이 먼저 정지(input_cm_undefined)하므로 입력 DC 0.6 을 선언한다: 게이트 전압이 고정이라
    # ln_idu 는 θ 성분이 아니다(O-127). 구성 None 은 icm_config 가 입력 포트 셋을 지원하지 않는 갈래 2 로 파이프라인이 실제로 닿는다.
    th = {("resistance", "R1"): r_load}
    for m in ("M1", "M2", "M3"):
        th.update({("L", m): 1e-6, ("current", m): i_each})
    ev = size_and_seal(ctx, th)
    res = ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, th, spec.constraints, junction=toy_junction(tmp_path / "j", ctx.lut.memo.lut))
    cfg = res.snapshot.value("graph", METRICS_KEY, "icm_config")
    assert cfg.config is None and [u.code for u in cfg.undefined] == ["icm_inputs_unsupported"]
    got = {req.metric: r for req, r in res.ss.entries}
    for m in ("icm_margin_v", "icmr_v"):
        assert got[m].value is None
        assert {(u.code, u.category) for u in got[m].undefined} == {("icm_inputs_unsupported", "definitional")}
        (u,) = got[m].undefined
        assert set(dict(u.detail)["inputs"]) == {"in", "in2", "in3"}


def test_it2d_m2_unmeasured_window_is_numeric_input_window_unmeasured(case_icm):
    """측정 실패 toy(VDSAT 열 없는 toy LUT r6 -> cfg 상태 unmeasured -> V_cm 칸 None): icm_margin_v·icmr_v 값 None(제약 판정 불능),
    code input_window_unmeasured, category numeric, detail 에 ("port", 입력 넷). 구성은 있다(definitional 아님)."""
    spec, ctx, sealed, js = case_icm
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js)
    cfg = res.snapshot.value("graph", METRICS_KEY, "icm_config")
    assert cfg.config == "as_is_single_input" and cfg.vcm_lo is None            # 전제
    got = {req.metric: r for req, r in res.ss.entries}
    for m in ("icm_margin_v", "icmr_v"):
        assert got[m].value is None
        assert {(u.code, u.category) for u in got[m].undefined} == {("input_window_unmeasured", "numeric")}
        assert any(("port", "in") in u.detail for u in got[m].undefined)


@pytest.fixture(scope="module")
def case_icm(tmp_path_factory):
    spec, ctx, ev, js = build(tmp_path_factory.mktemp("icm_aux"), cons=BASE + (("icm_margin_v", ">=", 0.0, None),
                                                                          ("icmr_v", ">=", 0.0, None)))
    return spec, ctx, SealedSnapshot(ev.snapshot, ev.report), js


# ---------------------------------------------------------------- T-M3 (독립): AST·READS

def _engine_dir():
    import gmid_engine
    from pathlib import Path
    return Path(gmid_engine.__file__).parent


def _functions(path, name):
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]


def _lo_hi_operand(node):
    import ast
    return any((isinstance(s, ast.Name) and s.id in ("lo", "hi")) or (isinstance(s, ast.Attribute) and s.attr in ("lo", "hi"))
               for s in ast.walk(node))


def _lo_hi_arithmetic(fn, with_reducers):
    import ast
    hits = []
    for node in ast.walk(fn):
        if isinstance(node, ast.BinOp) and _lo_hi_operand(node):
            hits.append(node.lineno)
        if with_reducers and isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            if name in ("sum", "min", "max", "mean", "fsum") and any(_lo_hi_operand(a) for a in node.args):
                hits.append(node.lineno)
    return hits


def test_it2d_m3_no_lo_hi_arithmetic_in_icm_window_functions():
    """interface T-M3: `lo`·`hi` 는 보고 열 전용 -- `icm_window_metrics` 소스에 lo·hi 를 피연산자로 쓰는 산술(BinOp, sum·min·max·mean 인자) 0.
    `_icm_ports` 는 포트 창을 정렬해 열을 만들 수 있으므로(min/max 로 정렬) BinOp 산술만 본다. 함수는 gmid_engine/metrics/*.py 에서 찾는다
    (전제: icm_window_metrics 정의가 하나 있다)."""
    found = {"icm_window_metrics": [], "_icm_ports": []}
    for path in sorted((_engine_dir() / "metrics").glob("*.py")):
        for name in found:
            found[name] += [(path, f) for f in _functions(path, name)]
    assert len(found["icm_window_metrics"]) == 1
    for name, with_reducers in (("icm_window_metrics", True), ("_icm_ports", False)):
        for path, fn in found[name]:
            assert _lo_hi_arithmetic(fn, with_reducers) == [], (path.name, name)


def test_it2d_m3_metrics_aux_reads_icm_config_not_kernel_window():
    """metrics_aux READS ∋ graph.icm_config·node.dc_window_cfg·node.dc_colour, ∌ node.dc_window(커널 창은 입력 창 정본이 아니다)."""
    from gmid_engine.metrics import metrics_aux
    reads = set(metrics_aux.reads)
    assert {("graph", "icm_config"), ("node", "dc_window_cfg"), ("node", "dc_colour")} <= reads
    assert ("node", "dc_window") not in reads


# ---------------------------------------------------------------- B77 결측 판정

def _missing_case(tmp, lut, topo, elements, structure_theta=None):
    from search.conftest import CELLS_C, theta_r4c
    case = T.build(tmp, lut, topo, elements=elements, constraints=GAIN + ICM_CONS + (("ff_gm_ratio", ">=", 0.0, None),),
                   input_dc="engine")
    return case, CELLS_C, theta_r4c()


def _struct_c():
    return H.MetricStructure_of(H.vstruct("transfer:0", {"in": 1.0}, ("out",),
                                          (H.block(("out",), ("in",), ("out",), ("in", "out"), input_cells=("M1",)),),
                                          (), ("M1",), ("M1",)))


def test_it2d_b77a_capacitor_only_missing_dc_defined_ss_undefined(tmp_path, r4_lut):
    """용량만 결측 toy(CL 값 미선언): 전제 -- ss_circuit.missing = (CL,) 하나, 전부 커패시터(비전도). dc 영역 metric(swing_out_v·icmr_v·
    icm_margin_v)은 전부 정의되고 값이 '그 커패시터 값만 선언한 대조 실행(같은 θ·봉인점)'과 비트 동일. ss 영역 ff_gm_ratio 는
    passive_value_undeclared. 전달 뷰 보고(block_residual·nqs_ratio)는 없고(대조 실행에는 있다), metric별 보고 swing_icmr 는 함께 나온다."""
    from search.conftest import PENDING
    miss, cells, th = _missing_case(tmp_path / "m", r4_lut, _circuit_c(with_cap=True), (("CL", "capacitor", PENDING),))
    ctrl, _, _ = _missing_case(tmp_path / "c", r4_lut, _circuit_c(with_cap=True), (("CL", "capacitor", 1e-12),))
    st = _struct_c()
    _, rm = T.sealed_ss(miss, th, cells, structure=st)
    _, rc = T.sealed_ss(ctrl, th, cells, structure=st)
    sc = rm.snapshot.value("graph", METRICS_KEY, "ss_circuit")
    assert tuple(sc.missing) == ("CL",)                                           # 전제: 결측 = 용량 하나
    assert not rc.snapshot.value("graph", METRICS_KEY, "ss_circuit").missing
    gm, gc = T.by_metric(rm.ss), T.by_metric(rc.ss)
    for m in DC_METRICS:
        assert gm[m].value is not None and not T.undefined_codes(gm[m]), m
        assert gm[m].value == gc[m].value, m                                       # 비트 동일
    assert T.undefined_codes(gm["ff_gm_ratio"]) == {"passive_value_undeclared"}
    rep_m, rep_c = dict(rm.ss.reports), dict(rc.ss.reports)
    assert "block_residual" in rep_c and "nqs_ratio" in rep_c                      # 전제: 대조 실행에는 전달 뷰 보고가 있다
    for key in ("block_residual", "nqs_ratio", "ls_fields"):
        assert key not in rep_m, key
    assert "swing_icmr" in rep_m


def test_it2d_b77b_resistor_missing_dc_and_ss_undefined(tmp_path, r4_lut):
    """저항 결측 toy(출력과 gnd 사이 직렬 CL–Rx 가지에서 Rx 값 미선언, DC 전류 0 -- 용량이 막는다): ss_nodal 이 Undefined 라 dc·ss 모두
    passive_value_undeclared. 전제: ss_circuit.missing = (Rx,)."""
    from search.conftest import PENDING, two
    topo = _circuit_c()
    topo["passive_elements"] = [two("CL", "capacitor", "out", "x"), two("Rx", "resistor", "x", "gnd")]
    case, cells, th = _missing_case(tmp_path, r4_lut, topo, (("CL", "capacitor", 1e-12), ("Rx", "resistor", PENDING)))
    _, ref = T.sealed_ss(case, th, cells)
    assert tuple(ref.snapshot.value("graph", METRICS_KEY, "ss_circuit").missing) == ("Rx",)
    got = T.by_metric(ref.ss)
    for m in DC_METRICS + ("ff_gm_ratio",):
        assert "passive_value_undeclared" in T.undefined_codes(got[m]), m
        assert got[m].value is None, m


# ---------------------------------------------------------------- B77 (독립): 이름 분기 0, 새 code 0

def _metrics_aux_tree():
    import ast
    return ast.parse((_engine_dir() / "metrics" / "metrics_aux.py").read_text(encoding="utf-8"))


def _calls_named(fn, name):
    import ast
    return [n for n in ast.walk(fn) if isinstance(n, ast.Call)
            and (getattr(n.func, "id", None) == name or getattr(n.func, "attr", None) == name)]


def _refers_missing(fn):
    import ast
    return any((isinstance(n, ast.Attribute) and n.attr == "missing") or (isinstance(n, ast.Name) and n.id == "CODE_PASSIVE_MISSING")
               or (isinstance(n, ast.Constant) and n.value == "passive_value_undeclared") for n in ast.walk(fn))


def test_it2d_b77c_missing_judgement_has_no_metric_name_branch():
    """결측 판정을 하는 함수(SsCircuit.missing·CODE_PASSIVE_MISSING 를 읽는 함수)와 그것을 부르는 함수에는 metric 이름 비교가 0 --
    영역은 MetricSignature.domain 만 읽는다. metric 이름 = 레지스트리 이름 집합(metric_registry 키). `is_dc_conducting_passive` 는
    metrics_aux 가 부르지 않는다(ss_circuit·ss_nodal 몫)."""
    import ast
    from gmid_engine.metrics import metric_registry
    names = set(metric_registry())
    tree = _metrics_aux_tree()
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    fns = [f for f in fns if f.name != "metrics_aux"]                 # 최상위 블록(계산 분배)은 제외: 결측 판정 helper 와 그 호출자만 본다
    judges = [f for f in fns if _refers_missing(f)]
    assert judges, "결측 판정 함수가 metrics_aux 에 없다(전제)"
    judge_names = {f.name for f in judges}
    callers = [f for f in fns if any(_calls_named(f, j) for j in judge_names - {f.name})]
    for fn in judges + callers:
        for cmp in (n for n in ast.walk(fn) if isinstance(n, ast.Compare)):
            consts = {c.value for c in ast.walk(cmp) if isinstance(c, ast.Constant) and isinstance(c.value, str)}
            assert not consts & names, (fn.name, consts & names)
    assert not _calls_named(tree, "is_dc_conducting_passive")


def test_it2d_b77d_no_new_missing_code_constant():
    """새 결측 code 상수 0: metrics 패키지 문자열 상수 가운데 passive 와 undeclared·missing 이 함께 든 것은 `passive_value_undeclared` 뿐.
    (base 에도 0 이면 green 후보 -- red 목록 제외.)"""
    import ast
    import re
    pat = re.compile(r"passive.*(undeclared|missing)|(undeclared|missing).*passive")
    found = set()
    for path in (_engine_dir() / "metrics").glob("*.py"):
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) < 60 and " " not in n.value \
                    and pat.search(n.value):
                found.add(n.value)
    old_other_codes = {"missing_passives", "passive_area_undeclared", "passive_value_missing"}    # 다른 뜻(면적·옛 경로)의 기존 code
    assert found <= {"passive_value_undeclared"} | old_other_codes, found
