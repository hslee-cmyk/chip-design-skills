"""card IT-2c (측정 구성) -- interface `20261104-it2c-icm-config` (계획 v6.38.8 N6.6·N3.6·N3.8, design 41 v1.16.3 §4.7-W) test.

이 파일 = 공개 이름·값 형식·소스 구조(AST) test. 값 판정(손 KCL servo 끝)은 `test_icm_config_servo.py`.

oracle 종류: (독립) 엔진 소스 AST·인스펙션·READS 집합 -- 피검 함수를 불러 기대값을 만들지 않는다. (d) interface 가 선언한 공개 이름·값.
test 작성 주체는 엔진 소스를 열람하지 않았다: 아래 AST 규칙은 interface 의 금지 목록을 그대로 옮긴 것이다.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
from pathlib import Path

import pytest

import gmid_engine

ENGINE = Path(gmid_engine.__file__).resolve().parent


# ---------------------------------------------------------------- 엔진 소스 AST 도구 (test 파일 자신·tests 폴더는 제외)

def _engine_sources():
    out = []
    for p in sorted(ENGINE.rglob("*.py")):
        rel = p.relative_to(ENGINE)
        if "tests" in rel.parts:
            continue
        out.append((rel.as_posix(), ast.parse(p.read_text(encoding="utf-8"), filename=str(p))))
    assert out, "엔진 소스를 찾지 못했다 -- 경로 가정이 틀렸다(통과로 세지 않는다)"
    return out


def _docstring_nodes(tree):
    ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body:
            first = n.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                ids.add(id(first.value))
    return ids


def _tokens(tree):
    """코드에 쓰인 이름·문자열 상수(docstring·주석 제외) 목록: [(종류, 값, 줄)]."""
    doc = _docstring_nodes(tree)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            out.append(("str", n.value, n.lineno))
        elif isinstance(n, ast.Name):
            out.append(("name", n.id, n.lineno))
        elif isinstance(n, ast.Attribute):
            out.append(("attr", n.attr, n.lineno))
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append(("def", n.name, n.lineno))
        elif isinstance(n, ast.arg):
            out.append(("arg", n.arg, n.lineno))
        elif isinstance(n, ast.keyword) and n.arg:
            out.append(("kw", n.arg, n.lineno))
        elif isinstance(n, ast.alias):
            out.append(("alias", n.name.split(".")[-1], getattr(n, "lineno", 0)))
            if n.asname:
                out.append(("alias", n.asname, getattr(n, "lineno", 0)))
    return out


def _called_name(call):
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _calls(name):
    """[(파일, Call)] -- 이름이 name 인 호출."""
    return [(rel, n) for rel, tree in _engine_sources() for n in ast.walk(tree)
            if isinstance(n, ast.Call) and _called_name(n) == name]


def _defs(name):
    return [(rel, n) for rel, tree in _engine_sources() for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]


# ---------------------------------------------------------------- T-L8f 삭제 어휘 0

# interface '정의 불능 code' 의 '없음' 목록과 T-L8f 목록 그대로(문자열/이름 정확 일치)
GONE_EXACT = (
    "declared_feedback", "follower_beta1", "inverting_port", "tied_ports",
    "icm_inverting_port_none", "icm_inverting_port_ambiguous", "icm_inverting_port_unresolved",
    "icm_config_differential_output_undeclared", "icm_config_differential_output_structure",
    "icm_config_feedback_no_dc", "icm_config_feedback_element_unsupported", "icm_config_feedback_outputs_split",
    "icm_config_feedback_cut", "icm_config_output_root_w3", "icm_view_ambiguous", "icm_excite_common_mode",
    "input_window_f_component_undeclared", "f_component_undeclared",
    "_dc_feedback_reaches", "_conduction_rows", "INPUT_STATUS_F_COMPONENT_UNDECLARED", "writer_head",
)
# 부분 문자열로 막는 이름(T-L8f 목록: icmr_view·icm_view·dc_output_structure·_output_structure·dc_window_def)
GONE_SUBSTR = ("icmr_view", "icm_view", "dc_output_structure", "_output_structure", "dc_window_def")
GONE_PREFIX = ("window_end_",)           # 'window_end_*' code


def test_it2c_t_l8f_removed_vocabulary_is_absent_from_engine_source():
    """oracle 대조: (독립) T-L8f. 비test 엔진 소스(docstring·주석 제외, AST)에 삭제 어휘 전부 0. 파일:줄을 실패 메시지에 낸다."""
    hits = []
    for rel, tree in _engine_sources():
        for kind, val, line in _tokens(tree):
            # 문자열 상수는 정확 일치·접두(code·필드 이름 리터럴), 이름류(def·name·attr·arg·kw·alias)는 부분 일치(설명 문장 속 단어는 세지 않는다)
            if (val in GONE_EXACT or any(val.startswith(p) for p in GONE_PREFIX)
                    or (kind != "str" and any(s in val for s in GONE_SUBSTR))
                    or (kind == "str" and val in GONE_SUBSTR)):
                hits.append("%s:%d %s %r" % (rel, line, kind, val))
    assert hits == [], "삭제 어휘가 엔진 소스에 남았다:\n" + "\n".join(hits[:40])


def test_it2c_t_l8f_kvl_sensitivity_signature_has_no_closure():
    """oracle 대조: (독립) T-L8f + interface '`kvl_sensitivity` 계약': 서명 = (nodal, drive, servo=None), `closure` 인자 없음 -> 넘기면 TypeError."""
    from gmid_engine.metrics.icm_config import kvl_sensitivity
    params = inspect.signature(kvl_sensitivity).parameters
    assert list(params) == ["nodal", "drive", "servo"]
    assert params["servo"].default is None
    assert params["nodal"].default is inspect.Parameter.empty and params["drive"].default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        kvl_sensitivity(None, (), closure=lambda *a: None)


# ---------------------------------------------------------------- 공개 이름·값 형식

def test_it2c_public_status_and_writer_names():
    """oracle 대조: (d) interface '공개 이름과 서명': 상태 문자열·writer 이름 상수 값. F 성분 미선언 상태 상수는 없다."""
    import gmid_engine.sizing as S
    assert S.INPUT_STATUS_MEASURED == "measured" and S.INPUT_STATUS_UNMEASURED == "unmeasured"
    assert not hasattr(S, "INPUT_STATUS_F_COMPONENT_UNDECLARED")
    assert (S.SS_CIRCUIT_WRITER, S.SS_NODAL_WRITER, S.ICM_CONFIG_WRITER) == ("ss_circuit", "ss_nodal", "icm_config")


def test_it2c_dc_conducting_passive_is_resistor_only():
    """oracle 대조: (d) interface: `is_dc_conducting_passive(kind)` 는 kind == "resistor" 일 때만 True(DC 전도 경로 = 저항뿐, 용량은 개방).
    `CODE_PASSIVE_MISSING == "passive_value_undeclared"`."""
    from gmid_engine.metrics.ss_circuit import CODE_PASSIVE_MISSING, is_dc_conducting_passive
    assert is_dc_conducting_passive("resistor") is True
    for kind in ("capacitor", "inductor", "current_source", "voltage_source", "nmos", "pmos", ""):
        assert is_dc_conducting_passive(kind) is False, kind
    assert CODE_PASSIVE_MISSING == "passive_value_undeclared"


def test_it2c_icm_config_value_fields_and_frozen():
    """oracle 대조: (d) interface 'IcmConfig 칸': 칸 이름·순서가 정확히 (config, pivot_a_e, pivot_resolution, vcm0, vcm_lo, vcm_hi, undefined),
    frozen. `inverting_port`·`tied_ports`·`transfer`·`kvl`·`output_structure` 칸은 없다. `NodalSystem` 칸 = (nodes, fixed, g, g_bound, factor), frozen."""
    from gmid_engine.metrics.aux_types import IcmConfig, NodalSystem
    assert [f.name for f in dataclasses.fields(IcmConfig)] == ["config", "pivot_a_e", "pivot_resolution", "vcm0", "vcm_lo", "vcm_hi",
                                                                "undefined"]
    assert [f.name for f in dataclasses.fields(NodalSystem)] == ["nodes", "fixed", "g", "g_bound", "factor"]
    for cls in (IcmConfig, NodalSystem):
        assert cls.__dataclass_params__.frozen is True
    for gone in ("inverting_port", "tied_ports", "transfer", "kvl", "output_structure"):
        assert gone not in {f.name for f in dataclasses.fields(IcmConfig)}


def test_it2c_view_seed_and_view_s1v_have_default_port_flag_default_false():
    """oracle 대조: (d) interface: `ViewSeed`·`ViewS1v` 에 칸 `default_port: bool`(기본 False) 추가."""
    from gmid_engine.graph import ViewS1v, ViewSeed
    for cls in (ViewSeed, ViewS1v):
        fl = {f.name: f for f in dataclasses.fields(cls)}
        assert "default_port" in fl, cls.__name__
        assert fl["default_port"].default is False, cls.__name__


# ---------------------------------------------------------------- T-L10 writer 하나씩 (소스 구조, AST)

def test_it2c_t_l10_single_producer_sites():
    """oracle 대조: (독립) T-L10. 소스 호출 자리 수(AST, 비test): `conductance_matrix(..., bound=True)` 호출은 `ss_nodal.py` 한 곳(다른 소비자의 bound 없는 호출은 세지 않는다),
    `kvl_sensitivity` 호출 한 곳, `ss_circuit` 호출 한 곳, `SsCircuit` 생성 한 곳, `_ss_of` 정의 0, `is_dc_conducting_passive` 정의 한 곳이고 호출 파일은
    `ss_circuit.py`·`ss_nodal.py` 두 곳."""
    cm = [(rel, c) for rel, c in _calls("conductance_matrix") if not rel.endswith("_helpers_nodal.py")]
    bound = [(rel, c) for rel, c in cm
             if any(k.arg == "bound" and isinstance(k.value, ast.Constant) and k.value.value is True for k in c.keywords)]
    assert [rel for rel, _ in bound] == ["metrics/ss_nodal.py"], [rel for rel, _ in bound]       # bound=True 자리 하나, 블록 ss_nodal
    assert len(_calls("kvl_sensitivity")) == 1
    assert len(_calls("ss_circuit")) == 1
    assert len(_calls("SsCircuit")) == 1
    assert _defs("_ss_of") == []
    assert len(_defs("is_dc_conducting_passive")) == 1
    assert sorted({rel for rel, _ in _calls("is_dc_conducting_passive")}) == ["metrics/ss_circuit.py", "metrics/ss_nodal.py"]


def _block_reads(block):
    return set(block.reads)


def test_it2c_reads_sets_contain_required_fields():
    """oracle 대조: (독립) interface '필드 -- writer 하나' READS 열. `ss_circuit`·`ss_nodal`·`icm_config` 블록의 READS 가 요구 집합을 포함하고
    '없음' 목록과 겹치지 않는다. `metrics_ss`·`metrics_aux` READS 요구 포함."""
    from gmid_engine.metrics import metrics_aux, metrics_ss
    from gmid_engine.metrics.icm_config import icm_config_window
    from gmid_engine.metrics.ss_circuit import ss_circuit_field
    from gmid_engine.metrics.ss_nodal import ss_nodal_system
    need_circuit = {("device", "element_class"), ("device", "kind"), ("device", "pins"), ("device", "bulk"), ("device", "ss_dev"),
                    ("device", "dc_colour"), ("device", "passive_value"), ("node", "ac_ground_class"), ("node", "dc_colour"),
                    ("node", "port_direction")}
    assert need_circuit <= _block_reads(ss_circuit_field)
    assert {("graph", "ss_circuit"), ("device", "kind")} <= _block_reads(ss_nodal_system)
    need_icm = {("node", "dc_writer"), ("node", "dc_rail_v"), ("node", "port_direction"), ("node", "port_role"), ("node", "dc_v"),
                ("device", "pins"), ("device", "kind"), ("device", "bulk"), ("device", "dc_L"), ("device", "dc_colour"),
                ("device", "dc_coord"), ("device", "dc_tol_v"), ("graph", "ss_nodal"), ("graph", "views")}
    assert need_icm <= _block_reads(icm_config_window)
    forbid_icm = {("node", "dc_window"), ("node", "dc_output_structure"), ("device", "ss_dev"), ("device", "dc_op"),
                  ("device", "dc_conduction_floor"), ("device", "dc_off_current"), ("device", "element_class"),
                  ("device", "dc_nets"), ("device", "unsupported"), ("node", "is_rail")}
    assert _block_reads(icm_config_window) & forbid_icm == set()
    assert {("graph", "ss_circuit"), ("device", "ss_dev")} <= _block_reads(metrics_ss)
    assert {("graph", "ss_circuit"), ("graph", "ss_nodal"), ("device", "ss_dev"), ("device", "dc_colour")} <= _block_reads(metrics_aux)


# ======================================================================================================================
# 값 판정 -- 실제 sizing 경로(toy LUT)로 만든 봉인점에서 `icm_config` 가 낸 구성·창을 손 KCL 로 대조한다.
#
# oracle (a): 소자 스탬프 손 조립. 입력으로 읽는 것 = 봉인 스냅샷의 `device.ss_dev` gm·gds, `device.passive_value`, `device.dc_op` vgs·vds·vsb,
# `device.dc_tol_v`·`device.dc_coord`(interface T-L8a 가 허용한 입력). 피검 함수(icm_config_window·kvl_sensitivity 등)는 부르지 않는다.
# VDSAT = 이 파일이 LUT 에 쓴 닫힌 식 VDSAT(VGS) = 0.1 + 0.2·VGS (VDS·VSB 무관) -- LUT 열을 직접 만든 것이므로 (a) 구성으로 정해진 값이다.
# 경계: VDS = VDSAT, 판정 여유 0(O-204): 행 slack = VDS − VDSAT, tol_VDsat 항 없음.
# 창 끝: 행마다 slack + sign·(s_a − s_b)·Δ >= 0, 입력 포트마다 rail_min <= V_p + s_p·Δ <= rail_max (레일 = 선언 supplies 의 min·max).
# ======================================================================================================================

import hashlib
import json
import math

import numpy as np

from gmid_engine.lut import load_lut_set, LutSpec
from gmid_engine.metrics import ss_evaluate
from gmid_engine.sizing import SealedSnapshot, build_kernel_context, dc_inputs_from_spec, size_and_seal

from .conftest import (LUT_SPEC_ARGS, LUT_VGS, fresh_run, load_case, lut_access, lut_ln_idu, toy_junction, topo_doc,
                       write_lut_v2)

SUP = {"vdd": 1.8, "gnd": 0.0}
L0 = 1e-6
VGS0 = 0.6
VDSAT_C0, VDSAT_C1 = 0.1, 0.2          # 이 파일이 LUT 에 쓰는 VDSAT(VGS) = C0 + C1·VGS


def _vdsat(vgs):
    return VDSAT_C0 + VDSAT_C1 * vgs


def _lut_with_vdsat(root):
    """write_lut_v2 의 toy LUT 슬라이스에 VDSAT 열(VGS 선형)을 더하고 manifest sha 를 갱신해 읽는다."""
    manifest, cap = write_lut_v2(root)
    mj = json.loads(manifest.read_text(encoding="utf-8"))
    for e in mj["slices"]:
        p = manifest.parent / e["file"]
        d = dict(np.load(p, allow_pickle=False))
        g = np.asarray(LUT_VGS)[None, :, None, None]
        d["VDSAT"] = VDSAT_C0 + VDSAT_C1 * g + np.zeros(d["ID"].shape)
        np.savez(p, **d)
        e["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(mj), encoding="utf-8")
    return load_lut_set(str(manifest), str(cap), LutSpec(*LUT_SPEC_ARGS))


def _evaluate(tmp, topo, els, theta, constraints, *, input_dc_v=None, with_vdsat=True, feedback=()):
    """spec 로더 -> build_s1 -> 커널 -> size_and_seal -> ss_evaluate. 반환 (snapshot, ctx)."""
    from gmid_engine.graph import build_s1
    td, spec = load_case(tmp / "case", topo, SUP, els, feedback, constraints, input_dc_v=input_dc_v)
    inputs = dc_inputs_from_spec(spec)
    if with_vdsat:
        lut = _lut_with_vdsat(tmp / "lut")
    else:
        from .conftest import load_lut_v2
        lut = load_lut_v2(tmp / "lut")
    run = fresh_run()
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs, lut_access(lut), **run)
    ev = size_and_seal(ctx, theta)
    js = toy_junction(tmp / "junction", ctx.lut.memo.lut)
    res = ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, theta, spec.constraints, ("vdd",), junction=js)
    return res.snapshot, ctx


def _icm(snap):
    col = dict(snap.column("graph", "icm_config"))
    assert len(col) == 1, col
    return next(iter(col.values()))


def _tol_v(snap):
    """interface cfg 항목: 봉인점 dc_tol_v 가운데 dc_coord MOS 의 None 아닌 값의 최솟값, 모두 None 이면 None."""
    coord = dict(snap.column("device", "dc_coord"))
    vals = [v for k, v in snap.column("device", "dc_tol_v") if coord.get(k) is not None and v is not None]
    return min(vals) if vals else None


def _close(a, b, rtol=1e-9):
    return abs(a - b) <= rtol * max(abs(a), abs(b), 1e-300)


CS_CONS = (("gain_ss_db", ">=", 20.0, None), ("power_dc_w", "<=", 1e-3, None))


def _cs(tmp, i=1e-5, r=9e4, **kw):
    topo = topo_doc("it2c_cs", mos=[("M1", "nmos", "out", "in", "gnd", "gnd")],
                    passives=[("R1", "resistor", "vdd", "out"), ("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"))
    els = (("R1", "resistor", None), ("CL", "capacitor", 1e-12))
    th = {("L", "M1"): L0, ("ln_idu", "M1"): lut_ln_idu("nmos", VGS0, 1.8 - i * r, 0.0), ("current", "R1"): i, ("resistance", "R1"): r}
    return _evaluate(tmp, topo, els, th, CS_CONS, **kw)


def test_it2c_single_input_as_is_window_by_hand_kcl(tmp_path):
    """oracle 대조: (손) T-L8d 단일 입력 갈래 + T-K + T-L8g(V_cm). 공통 소스 증폭기(입력 in 하나, 저항 부하 R1 out-vdd, M1 nmos (out, in, gnd)):
    config == "as_is_single_input". 구동 = in(=1), vdd·gnd 고정. out 노드 KCL(용량 개방, bulk = gnd): gds·v_out + gm·1 + v_out/R = 0
    -> s_out = −gm/(gds + 1/R). 행 (out, gnd, +1, VDS − VDSAT(VGS), "sat") -> Δ <= slack/|s_out|. 레일 자름: 0 <= V_in + Δ <= 1.8.
    포트 창 = [V_in + Δlo, V_in + Δhi] (s_in = 1), cfg 상태 measured, constraints 0, tol_v = 봉인점 dc_tol_v(dc_coord MOS) 최솟값.
    V_cm: vcm0 = V_in, vcm_lo/hi = vcm0 + Δlo/Δhi (한 포트, s̄ = 1)."""
    snap, _ = _cs(tmp_path)
    ss = snap.value("device", "M1", "ss_dev")
    op = snap.value("device", "M1", "dc_op")
    r = snap.value("device", "R1", "passive_value")
    slack = op.vds - _vdsat(op.vgs)
    s_out = -ss.gm / (ss.gds + 1.0 / r)
    # 전제(어기면 이 사례 무효): 행이 실제로 창을 막는다(레일 자름보다 안쪽), 증폭 방향 음수
    assert slack > 0 and s_out < 0
    dhi_row = slack / abs(s_out)
    v_in = op.vgs                                                       # 소스 = gnd, 입력 DC 미선언 -> V(in) = VGS
    assert v_in + dhi_row < SUP["vdd"]
    dlo, dhi = 0.0 - v_in, dhi_row
    cfg = _icm(snap)
    assert cfg.config == "as_is_single_input" and cfg.undefined == ()
    w = snap.value("node", "in", "dc_window_cfg")
    assert w.input_status == "measured" and w.constraints == 0
    assert abs(w.lo - (v_in + dlo)) <= 1e-12
    assert _close(w.hi, v_in + dhi, 1e-9)
    assert w.lo <= w.hi
    assert w.tol_v == _tol_v(snap)
    assert _close(cfg.vcm0, v_in) and abs(cfg.vcm_lo - (v_in + dlo)) <= 1e-12 and _close(cfg.vcm_hi, v_in + dhi, 1e-9)


def test_it2c_boundary_margin_is_zero_not_plus_tol(tmp_path):
    """oracle 대조: (손) T-L8a′ 구별(단일 입력 판). 경계 = VDS = VDSAT 판정 여유 0(O-204). 같은 toy 에서 +tol_VDsat 행 끝(slack − tol)과
    여유 0 끝(slack)의 차 = tol/|s_out| 가 허용을 넘는 전제를 두고, cfg 끝 = 여유 0 끝. tol_VDsat 은 봉인점 `device.dc_tol_v`(dc_coord MOS) 최솟값을 쓴다.
    toy 의 VDSAT 은 VGS 선형이라 LUT tol_VDsat 이 0 이면 두 끝이 같아 사례가 무효이므로 dc_tol_v 가 양수인지 먼저 단언한다(어기면 실패)."""
    snap, _ = _cs(tmp_path)
    ss = snap.value("device", "M1", "ss_dev")
    op = snap.value("device", "M1", "dc_op")
    r = snap.value("device", "R1", "passive_value")
    tol = _tol_v(snap)
    assert tol is not None and tol > 0.0, "tol_v 없음/0 -- 여유 0 대 +tol 구별 사례 무효"
    s_out = -ss.gm / (ss.gds + 1.0 / r)
    slack = op.vds - _vdsat(op.vgs)
    end_zero = op.vgs + slack / abs(s_out)
    end_tol = op.vgs + (slack - tol) / abs(s_out)
    assert abs(end_zero - end_tol) > 1e-9 * end_zero                       # 전제: 두 끝이 구별된다
    w = snap.value("node", "in", "dc_window_cfg")
    assert _close(w.hi, end_zero, 1e-9) and not _close(w.hi, end_tol, 1e-12)


def test_it2c_vdsat_column_missing_gives_unmeasured(tmp_path):
    """oracle 대조: (d) T-K. interface: VDSAT 열이 없으면 `region_rows` 가 None -> 행이 정의되지 않아 모든 입력 포트 `"unmeasured"`,
    cfg 항목 `Window(None, None, 0, input_status="unmeasured")`, V_cm 끝 None(한 포트라도 unmeasured)."""
    snap, _ = _cs(tmp_path, with_vdsat=False)
    w = snap.value("node", "in", "dc_window_cfg")
    assert (w.lo, w.hi, w.constraints, w.input_status) == (None, None, 0, "unmeasured")
    cfg = _icm(snap)
    assert cfg.vcm_lo is None and cfg.vcm_hi is None


# ---------------------------------------------------------------- 입력 둘 servo (차동 출력 toy 둘)

def _two_stage(tmp, i1, r1, i2, r2, *, outputs_swapped=False, input_dc_v=VGS0):
    """독립한 공통 소스 단 둘: M1 (o1, ip, gnd) + R1, M2 (o2, im, gnd) + R2. 입력 ip/im = differential_input_p/n, 출력 o1/o2 = differential_output_p/n
    (outputs_swapped 이면 o1 이 n, o2 가 p). 회로·소자 이름은 규칙이 아니라 이 toy 의 선언이다."""
    outp, outn = ("op", "on") if not outputs_swapped else ("on", "op")
    ports = {"ip": ("input", "differential_input_p"), "im": ("input", "differential_input_n"),
             "op": ("output", "differential_output_p"), "on": ("output", "differential_output_n")}
    if outputs_swapped:
        ports = {**ports, "op": ("output", "differential_output_n"), "on": ("output", "differential_output_p")}
    topo = topo_doc("it2c_pair%s" % ("s" if outputs_swapped else ""),
                    mos=[("M1", "nmos", "op", "ip", "gnd", "gnd"), ("M2", "nmos", "on", "im", "gnd", "gnd")],
                    passives=[("R1", "resistor", "vdd", "op"), ("R2", "resistor", "vdd", "on"),
                              ("CL1", "capacitor", "op", "gnd"), ("CL2", "capacitor", "on", "gnd")],
                    ports=ports, rails=("vdd", "gnd"))
    els = (("R1", "resistor", None), ("R2", "resistor", None), ("CL1", "capacitor", 1e-12), ("CL2", "capacitor", 1e-12))
    # 입력 DC 선언 -> gate 전압이 고정이라 ln_idu 는 θ 성분이 아니다(종속, O-127). θ = L, 저항 전류·값.
    th = {("L", "M1"): L0, ("L", "M2"): L0,
          ("current", "R1"): i1, ("resistance", "R1"): r1, ("current", "R2"): i2, ("resistance", "R2"): r2}
    if input_dc_v is None:                                                  # 입력 DC 미선언 -> ln_idu 가 θ 성분
        # [A-83] IT-1 입력 점 규칙: 차동 입력쌍 두 포트는 한 점으로 묶여 M2 는 parallel_vgs 종속 -> M1 만 θ 성분(M2 의 ln_idu 는 스키마 밖).
        th[("ln_idu", "M1")] = lut_ln_idu("nmos", VGS0, 1.8 - i1 * r1, 0.0)
    return _evaluate(tmp, topo, els, th, (("power_dc_w", "<=", 1e-3, None),), input_dc_v=input_dc_v)


def _servo_hand(snap, p_out="op", n_out="on"):
    """손 조립(독립한 두 단이라 연립이 닫힌 식): A_k = gm_k/(gds_k + 1/R_k) (단 k 의 전압 이득 크기). 감지 c = e_p − e_n.
    vx(입력 둘 =1): v_o1 = −A1, v_o2 = −A2.  ve(ip = +span/2, im = −span/2): v_o1 = −A1/2·span, v_o2 = +A2/2·span.
    a_e = c·ve/span = −(A1 + A2)/2.  c·vx = A2 − A1.  s_n = vx_n − (ve_n/span)(c·vx)/a_e  ->  s_o1 = s_o2 = −2·A1·A2/(A1 + A2),
    구동 넷 s_ip = 1 − e_p·(c·vx)/a_e = 1 − δ,  s_im = 1 + δ,  δ = (A1 − A2)/(A1 + A2).  (식 유도: interface '측정 구성 규칙 -- servo 감도')"""
    out = {}
    for m, r in (("M1", "R1"), ("M2", "R2")):
        ss = snap.value("device", m, "ss_dev")
        rv = snap.value("device", r, "passive_value")
        out[m] = ss.gm / (ss.gds + 1.0 / rv)
    a1, a2 = out["M1"], out["M2"]
    delta = (a1 - a2) / (a1 + a2)
    s_o = -2.0 * a1 * a2 / (a1 + a2)
    return a1, a2, delta, s_o


def _servo_window(snap):
    """손 창: 행 (o, gnd, +1, VDS − VDSAT) 둘 -> Δ <= slack_k/|s_o|, 레일 0 <= V_p + s_p·Δ <= 1.8 (두 입력 포트)."""
    a1, a2, delta, s_o = _servo_hand(snap)
    v = {m: snap.value("device", m, "dc_op") for m in ("M1", "M2")}
    s_p = {"ip": 1.0 - delta, "im": 1.0 + delta}
    vp = {"ip": v["M1"].vgs, "im": v["M2"].vgs}                             # 입력 DC 선언 0.6 = 각 소자 VGS (소스 gnd)
    dlo, dhi = -math.inf, math.inf
    for m in ("M1", "M2"):
        slack = v[m].vds - _vdsat(v[m].vgs)
        assert slack > 0
        dhi = min(dhi, slack / abs(s_o))
    for p in ("ip", "im"):
        dlo = max(dlo, (0.0 - vp[p]) / s_p[p])
        dhi = min(dhi, (SUP["vdd"] - vp[p]) / s_p[p])
    return vp, s_p, dlo, dhi


def test_it2c_servo_window_two_inputs_hand_kcl(tmp_path):
    """oracle 대조: (손) T-L8b·T-L8a 의 servo 갈래(차동 출력 toy, 되먹임 선언 없음·용량만 선언) + T-P(입력 DC 선언) + T-L8g(V_cm).
    toy: 독립한 두 단(비대칭: I1 = I2 = 1e-5, R1 = 9e4, R2 = 5e4 -> 이득 A1 != A2). config == "servo". 포트 창 =
    [V_p + s_p·Δlo, V_p + s_p·Δhi] 의 [min, max], 끝 상태 Δ 는 위 `_servo_window` 손 식. V_cm 끝 = 같은 끝 상태 입력 전압 평균
    (s̄ = (s_ip + s_im)/2 = 1 이므로 vcm0 + Δ). 전제: A1 != A2 (대칭이면 follower·θ 끝과 구별되지 않아 사례 무효)."""
    snap, _ = _two_stage(tmp_path, 1e-5, 9e4, 1e-5, 5e4)
    a1, a2, delta, s_o = _servo_hand(snap)
    assert abs(a1 - a2) > 0.1 * a1 and s_o < 0                              # 전제
    vp, s_p, dlo, dhi = _servo_window(snap)
    cfg = _icm(snap)
    assert cfg.config == "servo" and cfg.undefined == ()
    for p in ("ip", "im"):
        w = snap.value("node", p, "dc_window_cfg")
        e_lo, e_hi = sorted((vp[p] + s_p[p] * dlo, vp[p] + s_p[p] * dhi))
        assert w.input_status == "measured" and w.constraints == 0
        assert _close(w.lo, e_lo, 1e-8) and _close(w.hi, e_hi, 1e-8), (p, w, e_lo, e_hi)
        assert w.lo <= w.hi
    vcm0 = 0.5 * (vp["ip"] + vp["im"])
    sbar = 0.5 * (s_p["ip"] + s_p["im"])
    assert abs(sbar - 1.0) <= 1e-12                                          # 차동쌍 기본 뷰 s̄ = 1
    assert _close(cfg.vcm0, vcm0) and _close(cfg.vcm_lo, vcm0 + sbar * dlo, 1e-8) and _close(cfg.vcm_hi, vcm0 + sbar * dhi, 1e-8)


def test_it2c_swapping_output_roles_gives_same_window_and_vcm(tmp_path):
    """oracle 대조: (식) T-L8e role 맞바꿈 / 계약 '포트 role·회로 이름은 결과를 정하지 않는다': 출력 p/n 을 맞바꾼 toy 의 입력 포트 창·V_cm 칸이 같다
    (c = e_p − e_n 의 부호만 바뀌고 c·s = 0 조건·a_e 비 (c·vx)/a_e 는 부호 불변). 기대값 = 맞바꾸지 않은 사례와의 일치(둘 다 위 손 식과도 같다)."""
    a_snap, _ = _two_stage(tmp_path / "a", 1e-5, 9e4, 1e-5, 5e4)
    b_snap, _ = _two_stage(tmp_path / "b", 1e-5, 9e4, 1e-5, 5e4, outputs_swapped=True)
    vp, s_p, dlo, dhi = _servo_window(a_snap)
    for snap in (a_snap, b_snap):
        for p in ("ip", "im"):
            w = snap.value("node", p, "dc_window_cfg")
            e_lo, e_hi = sorted((vp[p] + s_p[p] * dlo, vp[p] + s_p[p] * dhi))
            assert _close(w.lo, e_lo, 1e-8) and _close(w.hi, e_hi, 1e-8)
    ca, cb = _icm(a_snap), _icm(b_snap)
    assert ca.config == cb.config == "servo"
    assert _close(ca.vcm_lo, cb.vcm_lo, 1e-9) and _close(ca.vcm_hi, cb.vcm_hi, 1e-9)


# ======================================================================================================================
# 정의 불능 갈래(code) -- 갈래 순서표 2·3·4·4′·5 (interface '측정 구성 규칙'). 각 toy 는 입력 DC·θ 를 직접 선언한다.
# oracle: (d) 갈래표가 선언한 code·detail. 포트 role·회로 이름은 결과를 정하지 않는다.
# ======================================================================================================================

def _undef(snap):
    cfg = _icm(snap)
    assert cfg.config is None and len(cfg.undefined) == 1, cfg
    u = cfg.undefined[0]
    return u.code, u.category, dict(u.detail)


def _cs_stage(k, out_role="single_ended_output"):
    return ("M%d" % k, "nmos", "o%d" % k, "i%d" % k, "gnd", "gnd"), ("R%d" % k, "resistor", "vdd", "o%d" % k)


def _stages_topo(name, n, in_roles, out_roles):
    mos, pas = zip(*[_cs_stage(k) for k in range(1, n + 1)])
    ports = {"i%d" % k: ("input", in_roles[k - 1]) for k in range(1, n + 1)}
    ports.update({"o%d" % k: ("output", r) for k, r in out_roles.items()})
    topo = topo_doc(name, mos=list(mos), passives=list(pas), ports=ports, rails=("vdd", "gnd"))
    th = {}
    for k in range(1, n + 1):
        th[("L", "M%d" % k)] = L0
        th[("current", "R%d" % k)] = 1e-5
        th[("resistance", "R%d" % k)] = 9e4
    els = tuple(("R%d" % k, "resistor", None) for k in range(1, n + 1))
    return topo, els, th


PWR = (("power_dc_w", "<=", 1e-3, None),)


def test_it2c_three_inputs_is_icm_inputs_unsupported(tmp_path):
    """oracle 대조: (d) 갈래 2. 입력 포트 셋 -> config None, code `icm_inputs_unsupported`, category definitional, detail inputs = 포트 이름(정렬 비교)."""
    topo, els, th = _stages_topo("it2c_three", 3, ["single_ended_input"] * 3, {1: "single_ended_output"})
    snap, _ = _evaluate(tmp_path, topo, els, th, PWR, input_dc_v=VGS0)
    code, cat, det = _undef(snap)
    assert (code, cat) == ("icm_inputs_unsupported", "definitional")
    assert sorted(det["inputs"]) == ["i1", "i2", "i3"]


def test_it2c_two_single_ended_inputs_give_two_default_views_view_required(tmp_path):
    """oracle 대조: (d) 갈래 4. 입력 둘이 차동 쌍이 아니면 입력마다 기본 포트 뷰 하나 -> 뷰 둘 -> `view_required`, detail default_views = 2."""
    topo, els, th = _stages_topo("it2c_two_se", 2, ["single_ended_input"] * 2, {1: "single_ended_output"})
    snap, _ = _evaluate(tmp_path, topo, els, th, PWR, input_dc_v=VGS0)
    code, cat, det = _undef(snap)
    assert (code, cat, det) == ("view_required", "definitional", {"default_views": 2})


def test_it2c_two_nondifferential_outputs_is_view_required_with_sense(tmp_path):
    """oracle 대조: (d) 갈래 4′. 차동 입력 쌍(뷰 하나)이지만 감지 = 출력 둘이 단일 출력도 차동 출력 쌍도 아니면 `view_required`, detail sense = 출력 넷 tuple."""
    topo, els, th = _stages_topo("it2c_two_out", 2, ["differential_input_p", "differential_input_n"],
                                 {1: "single_ended_output", 2: "single_ended_output"})
    snap, _ = _evaluate(tmp_path, topo, els, th, PWR, input_dc_v=VGS0)
    code, cat, det = _undef(snap)
    assert (code, cat) == ("view_required", "definitional") and sorted(det["sense"]) == ["o1", "o2"]


def test_it2c_zero_inputs_toy_is_rejected_at_topology_load(tmp_path):
    """oracle 대조: (독립) 갈래 3(입력 포트 0 -> `view_required`, default_views 0)의 도달 가능성. topology 로더가 입력 포트 없는 회로를 먼저
    `SchemaRejectedError`(gate topology_load, rule `no_input_port`)로 거부하므로 파이프라인으로는 갈래 3 에 닿지 않는다(실측 사실을 단언하고 갈래 3 의 값은
    미시험으로 표지한다 -- 보고 항목). 로더가 입력 0 을 받게 바뀌면 이 test 가 red 가 되어 갈래 3 test 를 쓰도록 알린다."""
    from gmid_engine.core import SchemaRejectedError
    topo = topo_doc("it2c_zero", mos=[("M1", "nmos", "out", "vb", "gnd", "gnd")], passives=[("R1", "resistor", "vdd", "out")],
                    ports={"out": ("output", "single_ended_output")}, rails=("vdd", "gnd"), bias=["vb"])
    with pytest.raises(SchemaRejectedError) as ei:
        load_case(tmp_path, topo, SUP, (("R1", "resistor", None),), (), PWR)
    hits = dict(ei.value.record.detail)["hits"]
    assert "no_input_port" in [h.rule for h in hits]


def _cap_only_topo(name, connect):
    """M1 (out, in, gnd) + R1 부하, M2 (o2, x, gnd) + R2 부하. 넷 x 는 용량 C1(x, in)과 M2 gate 에만 닿는다. connect 이면 저항 R3(x, vdd)로 DC 전도 경로를 낸다."""
    pas = [("R1", "resistor", "vdd", "out"), ("R2", "resistor", "vdd", "o2"), ("C1", "capacitor", "x", "in")]
    els = [("R1", "resistor", None), ("R2", "resistor", None), ("C1", "capacitor", 1e-12)]
    th = {("L", "M1"): L0, ("L", "M2"): L0, ("current", "R1"): 1e-5, ("resistance", "R1"): 9e4,
          ("current", "R2"): 1e-5, ("resistance", "R2"): 9e4}
    if connect:
        pas.append(("R3", "resistor", "vdd", "x"))
        els.append(("R3", "resistor", 1e6))
    else:
        th[("ln_idu", "M2")] = lut_ln_idu("nmos", VGS0, 0.9, 0.0)
    topo = topo_doc(name, mos=[("M1", "nmos", "out", "in", "gnd", "gnd"), ("M2", "nmos", "o2", "x", "gnd", "gnd")], passives=pas,
                    ports={"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}, rails=("vdd", "gnd"))
    return topo, tuple(els), th


def test_it2c_capacitive_only_node_is_icm_capacitive_only_node(tmp_path):
    """oracle 대조: (d) 갈래 5 / T-L8e′. 넷 x 가 커패시터와 MOS gate 에만 닿아 G 행이 모두 0 -> config None, code `icm_capacitive_only_node`, detail nets = ("x",)."""
    topo, els, th = _cap_only_topo("it2c_cap_only", connect=False)
    snap, _ = _evaluate(tmp_path, topo, els, th, PWR, input_dc_v=VGS0)
    code, cat, det = _undef(snap)
    assert (code, cat) == ("icm_capacitive_only_node", "definitional") and tuple(det["nets"]) == ("x",)


def test_it2c_capacitive_only_node_connected_by_resistor_is_defined(tmp_path):
    """oracle 대조: (d) T-L8e′ 대조: x 를 저항 R3 로 vdd 에 이으면 DC 전도 경로가 생겨 정의된다(단일 입력 -> as_is_single_input, 정의 불능 없음)."""
    topo, els, th = _cap_only_topo("it2c_cap_conn", connect=True)
    snap, _ = _evaluate(tmp_path, topo, els, th, PWR, input_dc_v=VGS0)
    cfg = _icm(snap)
    assert cfg.config == "as_is_single_input" and cfg.undefined == ()


# ---------------------------------------------------------------- 입력 둘 servo: 레일 자름, F 성분 미선언(입력 DC 미선언)

def test_it2c_servo_rail_clip_ends_share_one_end_state(tmp_path):
    """oracle 대조: (손) T-L8g 레일 자름. 이득이 작아(R1 = 1e3, R2 = 2e3, I = 1e-5) 행 끝이 레일 끝보다 멀다: 전제 -- 행 끝 > 레일 끝.
    Δhi = min_p (1.8 − V_p)/s_p (위 `_servo_window` 손 식에 같음). 두 포트의 위 끝 V_p + s_p·Δhi 중 하나는 1.8(레일에 닿은 포트), 다른 하나는 안쪽이고,
    V_cm 위 끝 = vcm0 + s̄·Δhi (같은 끝 상태 평균)."""
    snap, _ = _two_stage(tmp_path, 1e-5, 1e3, 1e-5, 2e3)
    a1, a2, delta, s_o = _servo_hand(snap)
    vp, s_p, dlo, dhi = _servo_window(snap)
    row_hi = min((snap.value("device", m, "dc_op").vds - _vdsat(snap.value("device", m, "dc_op").vgs)) / abs(s_o) for m in ("M1", "M2"))
    assert dhi < row_hi                                                  # 전제: 레일이 창을 정한다
    ends = {}
    for p in ("ip", "im"):
        w = snap.value("node", p, "dc_window_cfg")
        e_lo, e_hi = sorted((vp[p] + s_p[p] * dlo, vp[p] + s_p[p] * dhi))
        assert w.input_status == "measured"
        assert _close(w.lo, e_lo, 1e-8) and _close(w.hi, e_hi, 1e-8)
        ends[p] = w.hi
    assert abs(max(ends.values()) - SUP["vdd"]) <= 1e-9 or abs(min(vp[p] + s_p[p] * dlo for p in vp)) <= 1e-9
    cfg = _icm(snap)
    vcm0 = 0.5 * (vp["ip"] + vp["im"])
    assert _close(cfg.vcm_hi, vcm0 + dhi, 1e-8) and _close(cfg.vcm_lo, vcm0 + dlo, 1e-8)


def test_it2c_servo_undeclared_input_dc_drives_both_ports_together(tmp_path):
    """oracle 대조: (손) T-L12 2입력 변형 + T-K. 입력 DC 미선언 두 입력 포트(F 성분 미선언, gate 전용 넷, source = gnd)도 구동에 든다: 같은 x 로 함께 훑은 창 =
    위 손 식(V_p = 각 소자의 VGS). cfg 두 포트 `measured`, 커널 `node.dc_window` 에 입력 포트 항목 없음(두 입력 모두 W4 뿌리 아님)."""
    snap, _ = _two_stage(tmp_path, 1e-5, 9e4, 1e-5, 5e4, input_dc_v=None)
    vp, s_p, dlo, dhi = _servo_window(snap)
    for p in ("ip", "im"):
        w = snap.value("node", p, "dc_window_cfg")
        e_lo, e_hi = sorted((vp[p] + s_p[p] * dlo, vp[p] + s_p[p] * dhi))
        assert w.input_status == "measured" and _close(w.lo, e_lo, 1e-8) and _close(w.hi, e_hi, 1e-8)
    assert not {"ip", "im"} & set(dict(snap.column("node", "dc_window")))


def test_it2c_single_input_has_no_kernel_window_entry(tmp_path):
    """oracle 대조: (독립) T-L12·T-K. 입력 DC 미선언 단일 입력 toy(F 성분 미선언: gate 전용 in, source = gnd): 커널 `node.dc_window` 에 in 항목이 없다
    (cfg 가 대신 받는다)."""
    snap, _ = _cs(tmp_path)
    assert "in" not in dict(snap.column("node", "dc_window"))
    assert snap.value("node", "in", "dc_window_cfg").input_status == "measured"


# ---------------------------------------------------------------- 선언 뷰 병합 (T-S1V)

def _ota_views(tmp, view, seeds=False):
    """seeds False: graph.views 의 ViewS1v 튜플. seeds True: (ViewS1v 튜플, `collect_views` 가 돌려주는 ViewSeed 튜플) -- 출처(source)는 ViewSeed 에만 있다(A-83)."""
    from gmid_engine.graph import build_s1, build_s1v
    from gmid_engine.graph.net_model import net_model
    from gmid_engine.graph.views import collect_views
    topo = topo_doc("it2c_ota", mos=[("M1", "nmos", "x", "in_p", "tail", "gnd"), ("M2", "nmos", "out", "in_n", "tail", "gnd"),
                                     ("M3", "pmos", "x", "x", "vdd", "vdd"), ("M4", "pmos", "out", "x", "vdd", "vdd"),
                                     ("M0", "nmos", "tail", "vb", "gnd", "gnd")],
                    ports={"in_p": ("input", "differential_input_p"), "in_n": ("input", "differential_input_n"),
                           "out": ("output", "single_ended_output")}, rails=("vdd", "gnd"), bias=["vb"])
    td, spec = load_case(tmp, topo, SUP, (), (), (("gain_ss_db", ">=", 20.0, view),))
    run = fresh_run()
    s1 = build_s1(td, dict(SUP), **run)
    g = build_s1v(s1, spec, count_budget=10 ** 6, stop_on_unsupported=False, **run)
    views = g.value("graph", "s1v", "views")
    if not seeds:
        return views
    return views, collect_views(net_model(s1), spec)[0]


def test_it2c_declared_view_same_key_merges_into_default(tmp_path):
    """oracle 대조: (손) T-S1V 같은 키 (interface 빈칸 답 4). 선언 뷰 excite (in_p 1/2, in_n −1/2)·감지 out 은 기본 포트 뷰와 같은 키 -> 뷰 하나로 합쳐지고
    선언이 먼저라 source == "spec_constraint_view", default_port True."""
    # [A-83] 출처는 `collect_views` 의 ViewSeed.source 로 단언한다(ViewS1v 에는 source 칸이 없다). 합치기 뜻(뷰 하나, 선언 출처, default_port)은 그대로.
    views, seeds = _ota_views(tmp_path, {"ac_excite": {"in_p": 0.5, "in_n": -0.5}, "sense_p": "out", "sense_n": None, "sense_mode": "single_ended"}, seeds=True)
    assert len(views) == 1 and len(seeds) == 1
    v = views[0]
    assert v.excite == (("in_n", -0.5), ("in_p", 0.5)) and v.sense == ("out",)
    assert seeds[0].source == "spec_constraint_view" and v.default_port is True and seeds[0].default_port is True


def test_it2c_declared_view_other_key_coexists_with_default(tmp_path):
    """oracle 대조: (손) T-S1V 다른 키. 선언 뷰 excite (in_p 1) 는 기본 키가 아니므로 뷰 둘 -- 기본 포트 뷰만 default_port True, 선언 뷰는 False(목록 순서 = 키 정렬)."""
    views, seeds = _ota_views(tmp_path, {"ac_excite": {"in_p": 1.0}, "sense_p": "out", "sense_n": None, "sense_mode": "single_ended"}, seeds=True)
    assert len(views) == 2 and len(seeds) == 2
    by = {v.excite: v for v in views}
    seed_by = {v.excite: v for v in seeds}                                  # [A-83] 출처는 ViewSeed.source
    assert seed_by[(("in_p", 1.0),)].source == "spec_constraint_view" and by[(("in_p", 1.0),)].default_port is False
    assert by[(("in_n", -0.5), ("in_p", 0.5))].default_port is True
    assert [v.excite for v in views] == sorted(v.excite for v in views)


# ---------------------------------------------------------------- 용량 결측 (T-L10 결측 toy)

def test_it2c_pending_capacitor_leaves_ss_nodal_defined_and_icm_config_defined(tmp_path):
    """oracle 대조: (d) T-L10 결측 toy(용량만). interface: 용량만 결측이면 `NodalSystem`(용량은 DC 에서 개방이라 G 에 안 든다), icm_config 는 정의된다
    (단일 입력 -> as_is_single_input). `graph.ss_nodal` 값은 Undefined 가 아니라 NodalSystem(ndarray 불변)이다."""
    from gmid_engine.graph import build_s1
    from gmid_engine.metrics.aux_types import NodalSystem
    from .test_ss_evaluate import _spec_with_pending
    topo = topo_doc("it2c_pend", mos=[("M1", "nmos", "out", "in", "gnd", "gnd")],
                    passives=[("R1", "resistor", "vdd", "out"), ("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"))
    td, spec = _spec_with_pending(tmp_path / "p", "it2c_pend", topo, (("R1", "resistor", None),), (("CL", "SP-9"),),
                                  (("gain_ss_db", ">=", 20.0, None), ("power_dc_w", "<=", 1e-3, None)))
    inputs = dc_inputs_from_spec(spec)
    lut = _lut_with_vdsat(tmp_path / "lut")
    run = fresh_run()
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs, lut_access(lut), **run)
    th = {("L", "M1"): L0, ("ln_idu", "M1"): lut_ln_idu("nmos", VGS0, 0.9, 0.0), ("current", "R1"): 1e-5, ("resistance", "R1"): 9e4}
    ev = size_and_seal(ctx, th)
    js = toy_junction(tmp_path / "junction", ctx.lut.memo.lut)
    snap = ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, th, spec.constraints, ("vdd",), junction=js).snapshot
    nod = next(iter(dict(snap.column("graph", "ss_nodal")).values()))
    assert isinstance(nod, NodalSystem)
    for arr in (nod.g, nod.g_bound):
        assert arr.flags.writeable is False
        with pytest.raises(ValueError):
            arr[0, 0] = 1.0
    assert _icm(snap).config == "as_is_single_input"


# ---------------------------------------------------------------- W3 목표 출력 toy (T-L8c)

def test_it2c_w3_target_output_high_impedance_window_by_hand_kcl(tmp_path):
    """oracle 대조: (손) T-L8c W3 목표 출력 toy. M1 nmos (out, in, gnd), 이상 전류원 I1(vdd -> out) 1e-5 A (소신호 개방), 출력 out 은 W3 목표 0.9 V.
    out 노드 KCL(용량 개방): gds·v_out + gm·1 = 0 -> s_out = −gm/gds. 행 (out, gnd, +1, VDS − VDSAT): Δ <= slack/|s_out|, 레일 0 <= V_in + Δ <= 1.8.
    포트 창 = [V_in + Δlo, V_in + Δhi], V_in = VGS. 전제: 목표 V(out) = 0.9 가 실제 동작점 VDS 와 같다."""
    import json
    from pathlib import Path
    from gmid_engine.authoring import load_sizing_spec
    from gmid_engine.graph import build_s1
    from gmid_engine.metrics import metric_catalog
    from .conftest import SS_SRC, spec_json, topo_only
    topo = topo_doc("it2c_w3", mos=[("M1", "nmos", "out", "in", "gnd", "gnd")], passives=[("CL", "capacitor", "out", "gnd")],
                    sources=[("I1", "current_source", "vdd", "out")], rails=("vdd", "gnd"))
    td = topo_only(tmp_path, topo)
    d = spec_json(td, SUP, (("I1", "current_source", 1e-5), ("CL", "capacitor", 1e-12)), (), PWR)
    d["human"]["node_voltage_targets_v"] = {"out": {"value_v": 0.9, "source": SS_SRC}}
    sp = Path(tmp_path) / "it2c_w3.sizing_spec.json"
    sp.write_text(json.dumps(d), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, metric_catalog())
    inputs = dc_inputs_from_spec(spec)
    run = fresh_run()
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs, lut_access(_lut_with_vdsat(tmp_path / "lut")), **run)
    th = {("L", "M1"): L0, ("ln_idu", "M1"): lut_ln_idu("nmos", VGS0, 0.9, 0.0)}
    ev = size_and_seal(ctx, th)
    js = toy_junction(tmp_path / "junction", ctx.lut.memo.lut)
    snap = ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, th, spec.constraints, ("vdd",), junction=js).snapshot
    ss = snap.value("device", "M1", "ss_dev")
    op = snap.value("device", "M1", "dc_op")
    assert abs(op.vds - 0.9) <= 1e-9                                         # 전제: W3 목표가 동작점
    s_out = -ss.gm / ss.gds
    slack = op.vds - _vdsat(op.vgs)
    assert slack > 0 and s_out < 0
    dhi = slack / abs(s_out)
    assert op.vgs + dhi < SUP["vdd"]
    w = snap.value("node", "in", "dc_window_cfg")
    assert w.input_status == "measured"
    assert abs(w.lo - 0.0) <= 1e-12 and _close(w.hi, op.vgs + dhi, 1e-9)
    assert _icm(snap).config == "as_is_single_input"


def test_it2c_servo_boundary_margin_is_zero_not_plus_tol(tmp_path):
    """oracle 대조: (손) T-L8a′ (servo). 비대칭 두 단에서 행 끝을 여유 0 으로 내면 Δhi0 = min_k slack_k/|s_o|, +tol 로 내면 Δhi1 = min_k (slack_k − tol)/|s_o|,
    tol = 봉인점 dc_tol_v(dc_coord MOS) 최솟값. 전제: tol > 0 이고 두 끝이 구별된다(차 > 1e-9). cfg 위 끝 = 여유 0 끝."""
    snap, _ = _two_stage(tmp_path, 1e-5, 9e4, 1e-5, 5e4)
    tol = _tol_v(snap)
    assert tol is not None and tol > 0.0
    a1, a2, delta, s_o = _servo_hand(snap)
    slacks = [snap.value("device", m, "dc_op").vds - _vdsat(snap.value("device", m, "dc_op").vgs) for m in ("M1", "M2")]
    d0 = min(slacks) / abs(s_o)
    d1 = (min(slacks) - tol) / abs(s_o)
    assert abs(d0 - d1) > 1e-9
    vp, s_p, dlo, dhi = _servo_window(snap)
    assert _close(dhi, d0, 1e-12) and dhi != d1                              # 전제: 위 끝은 행에서 나온다(레일 아님)
    cfg = _icm(snap)
    assert _close(cfg.vcm_hi, 0.5 * (vp["ip"] + vp["im"]) + dhi, 1e-8)


# ---------------------------------------------------------------- triode 선언 소자 (T-D)

def _evaluate_region(tmp, topo, els, theta, region_decl, constraints=PWR):
    """_evaluate 와 같되 spec 의 `human.intended_region` 을 채운다(소자 이름 -> {"region": ..., "source": ...})."""
    import json
    from pathlib import Path
    from gmid_engine.authoring import load_sizing_spec
    from gmid_engine.graph import build_s1
    from gmid_engine.metrics import metric_catalog
    from .conftest import SS_SRC, spec_json, topo_only
    td = topo_only(tmp, topo)
    d = spec_json(td, SUP, els, (), constraints)
    d["human"]["intended_region"] = {m: {"region": r, "source": SS_SRC} for m, r in region_decl.items()}
    sp = Path(tmp) / (topo["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(d), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, metric_catalog())
    inputs = dc_inputs_from_spec(spec)
    run = fresh_run()
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs, lut_access(_lut_with_vdsat(tmp / "lut")), **run)
    ev = size_and_seal(ctx, theta)
    js = toy_junction(tmp / "junction", ctx.lut.memo.lut)
    return ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, theta, spec.constraints, ("vdd",), junction=js).snapshot


def test_it2c_triode_declared_device_row_zero_crossing_is_the_window_end(tmp_path):
    """oracle 대조: (손) T-D. `triode` 선언 소자 M1 (out, in, gnd) + 저항 부하(R = 1.7e5, I = 1e-5 -> V(out) = 0.1 < VDSAT = 0.1 + 0.2·0.6 = 0.22, 동작점 triode 전제).
    행 `(d, s, −1, VDSAT − VDS, "triode")`: slack_t = VDSAT − VDS > 0, 기울기 = −(s_out − 0) = |s_out| (s_out = −gm/(gds + 1/R)) -> Δ >= −slack_t/|s_out|
    (VDS = VDSAT 에서 포화로 넘어가는 점, 판정 여유 0). 레일 위 끝 Δ <= 1.8 − V_in. 포트 창 = [V_in − slack_t/|s_out|, 1.8]. cfg 상태 measured."""
    i, r = 1e-5, 1.7e5
    topo = topo_doc("it2c_triode", mos=[("M1", "nmos", "out", "in", "gnd", "gnd")],
                    passives=[("R1", "resistor", "vdd", "out"), ("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"))
    th = {("L", "M1"): L0, ("ln_idu", "M1"): lut_ln_idu("nmos", VGS0, 1.8 - i * r, 0.0), ("current", "R1"): i, ("resistance", "R1"): r}
    snap = _evaluate_region(tmp_path, topo, (("R1", "resistor", None), ("CL", "capacitor", 1e-12)), th, {"M1": "triode"})
    ss = snap.value("device", "M1", "ss_dev")
    op = snap.value("device", "M1", "dc_op")
    rv = snap.value("device", "R1", "passive_value")
    slack_t = _vdsat(op.vgs) - op.vds
    s_out = -ss.gm / (ss.gds + 1.0 / rv)
    assert slack_t > 0 and s_out < 0                                           # 전제: 동작점 triode
    w = snap.value("node", "in", "dc_window_cfg")
    assert w.input_status == "measured"
    assert _close(w.lo, op.vgs - slack_t / abs(s_out), 1e-9) and abs(w.hi - SUP["vdd"]) <= 1e-12


# ======================================================================================================================
# 빈칸 답 2 (interface 24dc09d1): T-L8d(MOS 부하 toy)·T-L8e(정확 0, 단위 상쇄)·T-L8h·T-K 빈 창·값 test(region_rows, NodalSystem)
# ======================================================================================================================

def _l8d_run(tmp, feedback):
    """M1 (x, ip, gnd), M2 (out, im, gnd), Mp pmos (out, vb, vdd). 저항 R1 (vdd, x), Rf (out, im), CL (out, gnd). 저항 고리 없음(Rf 한 끝 im 은 고정 넷)."""
    topo = topo_doc("it2c_l8d", mos=[("M1", "nmos", "x", "ip", "gnd", "gnd"), ("M2", "nmos", "out", "im", "gnd", "gnd"),
                                     ("Mp", "pmos", "out", "vb", "vdd", "vdd")],
                    passives=[("R1", "resistor", "vdd", "x"), ("Rf", "resistor", "out", "im"), ("CL", "capacitor", "out", "gnd")],
                    ports={"ip": ("input", "differential_input_p"), "im": ("input", "differential_input_n"),
                           "out": ("output", "single_ended_output")}, rails=("vdd", "gnd"), bias=["vb"])
    th = {("L", "M1"): L0, ("L", "M2"): L0, ("L", "Mp"): L0, ("current", "R1"): 1e-5, ("resistance", "R1"): 9e4,
          ("resistance", "Rf"): 1e5, ("current", "Mp"): 1e-5, ("ln_idu", "Mp"): lut_ln_idu("pmos", 0.6, 1.2, 0.0)}
    els = (("R1", "resistor", None), ("Rf", "resistor", None), ("CL", "capacitor", 1e-12))
    return _evaluate(tmp, topo, els, th, PWR, input_dc_v=VGS0, feedback=feedback)[0]


def test_it2c_l8d_resistor_feedback_declaration_does_not_change_window(tmp_path):
    """oracle 대조: (손) T-L8d (빈칸 답 2-1). 선언 소자 Rf 는 봉인점 회로 소자로 G 에 든다; `human.feedback` 선언 유무는 창을 바꾸지 않는다(두 실행 같음)
    그리고 창 = 손 감도. Gf = 1/Rf, A = (Gf − gm2)/(gds2 + gdsp + Gf) (out KCL: Rf 가 im 에서 들어옴), A1 = gm1/(gds1 + 1/R1).
    c = e_out, c·vx = A, a_e = −A/2, (c·vx)/a_e = −2 -> s_ip = 2, s_im = 0, s_out = 0, s_x = −2·A1. 행 M1 (x, gnd): Δ <= slack/(2·A1);
    M2·Mp 행 기울기 0 (건너뜀, slack > 0 전제). 레일 0 <= 0.6 + 2Δ <= 1.8. cfg ip = [0.6 + 2Δlo, 0.6 + 2Δhi], im = [0.6, 0.6]. config servo."""
    snap_a = _l8d_run(tmp_path / "a", ("Rf",))
    snap_b = _l8d_run(tmp_path / "b", ())
    ss1, ss2, ssp = (snap_a.value("device", m, "ss_dev") for m in ("M1", "M2", "Mp"))
    rf, r1 = snap_a.value("device", "Rf", "passive_value"), snap_a.value("device", "R1", "passive_value")
    gf = 1.0 / rf
    a = (gf - ss2.gm) / (ss2.gds + ssp.gds + gf)
    a1 = ss1.gm / (ss1.gds + 1.0 / r1)
    ops = {m: snap_a.value("device", m, "dc_op") for m in ("M1", "M2", "Mp")}
    slack1 = ops["M1"].vds - _vdsat(ops["M1"].vgs)
    assert slack1 > 0 and ops["M2"].vds - _vdsat(ops["M2"].vgs) > 0 and ops["Mp"].vds - _vdsat(ops["Mp"].vgs) > 0     # 전제: 건너뛴 행 slack > 0
    assert a1 > 0 and abs(a) > 0
    v0 = ops["M1"].vgs
    dlo, dhi = -v0 / 2.0, min((SUP["vdd"] - v0) / 2.0, slack1 / (2.0 * a1))
    for snap in (snap_a, snap_b):
        assert _icm(snap).config == "servo"
        wp, wm = snap.value("node", "ip", "dc_window_cfg"), snap.value("node", "im", "dc_window_cfg")
        assert wp.input_status == wm.input_status == "measured"
        assert abs(wp.lo - (v0 + 2.0 * dlo)) <= 1e-9 and _close(wp.hi, v0 + 2.0 * dhi, 1e-8)
        assert abs(wm.lo - v0) <= 1e-9 and abs(wm.hi - v0) <= 1e-9
    wa, wb = snap_a.value("node", "ip", "dc_window_cfg"), snap_b.value("node", "ip", "dc_window_cfg")
    assert (wa.lo, wa.hi) == (wb.lo, wb.hi)


def test_it2c_l8e_exact_zero_pivot_pipeline_toy(tmp_path):
    """oracle 대조: (d) T-L8e (a) 정확 0 (빈칸 답 2-2). M1 (vdd, ip, t), M2 (vdd, im, t), M3 (t, vb, gnd), CL (t, gnd), 출력 t, 입력 DC 1.2.
    M1·M2 gm 비트 동일(전제) -> t 행 구동 = (gm1 − gm2)/2 = 0 -> a_e 정확 0 -> `config is None`, code `icm_servo_pivot_unresolved`, cfg 항목 없음."""
    topo = topo_doc("it2c_zero_ae", mos=[("M1", "nmos", "vdd", "ip", "t", "gnd"), ("M2", "nmos", "vdd", "im", "t", "gnd"),
                                         ("M3", "nmos", "t", "vb", "gnd", "gnd")],
                    passives=[("CL", "capacitor", "t", "gnd")],
                    ports={"ip": ("input", "differential_input_p"), "im": ("input", "differential_input_n"),
                           "t": ("output", "single_ended_output")}, rails=("vdd", "gnd"), bias=["vb"])
    th = {("L", "M1"): L0, ("L", "M2"): L0, ("L", "M3"): L0, ("current", "M1"): 1e-5, ("current", "M2"): 1e-5,
          ("ln_idu", "M1"): lut_ln_idu("nmos", 0.6, 1.2, 0.6), ("ln_idu", "M3"): lut_ln_idu("nmos", 0.6, 0.6, 0.0)}
    snap, _ = _evaluate(tmp_path, topo, (("CL", "capacitor", 1e-12),), th, PWR, input_dc_v=1.2)
    assert snap.value("device", "M1", "ss_dev").gm == snap.value("device", "M2", "ss_dev").gm       # 전제: gm 비트 동일
    cfg = _icm(snap)
    assert cfg.config is None and [u.code for u in cfg.undefined] == ["icm_servo_pivot_unresolved"]
    assert not {"ip", "im"} & set(dict(snap.column("node", "dc_window_cfg")))


def test_it2c_l8e_assembly_cancellation_pivot_resolution_unit():
    """oracle 대조: (손) T-L8e (b) 조립 상쇄 (빈칸 답 2-2, `_transfer_resolution` 직접 호출 허용). 저항 스탬프만: R(1,3) 10 ∥ R(1,3) 5, R(2,3) 10/3, R(3,0) 1000,
    고정 {0,1,2}, 구동 v1 = +0.9, v2 = −0.9, 감지 e_3. 참값 = fractions.Fraction 으로 같은 float 저항에서 낸 노드 3 KCL 해(0 이 아니다, ~2e-17).
    단언: 전제 g[3,1] != g[3,2](조립이 정확히 상쇄하지 않는다), 풀이 x != 0, 판정 분해능 δ 가 있고 |x − 참값| <= δ 와 |x| <= δ (판정 불능이 맞다)."""
    from fractions import Fraction
    import numpy as np
    from gmid_engine.metrics import Resistor, SmallSignalCircuit
    from gmid_engine.metrics._helpers_nodal import conductance_matrix, nodal_factor, nodal_solve
    from gmid_engine.metrics.aux_types import NodalSystem
    from gmid_engine.metrics.icm_config import _transfer_resolution
    rs = (10.0, 5.0, 10.0 / 3.0, 1000.0)
    ck = SmallSignalCircuit(resistors=(Resistor(1, 3, rs[0]), Resistor(1, 3, rs[1]), Resistor(2, 3, rs[2]), Resistor(3, 0, rs[3])))
    n, fixed = 4, {0, 1, 2}
    g, gb = conductance_matrix(ck, n, bound=True)
    assert g[3, 1] != g[3, 2]
    sysm = NodalSystem(("gnd", "a", "b", "s"), frozenset(fixed), g, gb, nodal_factor(g, fixed))
    for arr in (sysm.g, sysm.g_bound):
        arr.flags.writeable = False
    volt, _res = nodal_solve(sysm.factor, n, {1: 0.9, 2: -0.9})
    sense = np.zeros(n)
    sense[3] = 1.0
    x = float(volt[3])
    assert x != 0.0
    delta = _transfer_resolution(sysm, volt, sense)
    assert delta is not None and delta > 0.0
    f = [Fraction(1) / Fraction(r) for r in rs]
    true = (( f[0] + f[1]) * Fraction(0.9) + f[2] * Fraction(-0.9)) / (f[0] + f[1] + f[2] + f[3])
    assert abs(Fraction(x) - true) <= Fraction(delta)
    assert abs(x) <= delta


def test_it2c_t_l8h_icmr_is_region_row_window_not_conduction_end(tmp_path):
    """oracle 대조: (손) T-L8h (빈칸 답 2-4). `_two_stage(1e-5, 9e4, 2e-5, 4.5e4)`: 전도 끝(옛 R0 가 있었다면) Δc_k = −ID_k/(gm_k·s_p,k + gds_k·s_o),
    영역 행 창의 아래 끝 Δlo = 레일 끝 max_p (0 − V_p)/s_p (포화 행은 Δ < 0 쪽에서 여유가 늘어 끝을 만들지 않는다). 전제: |Δc| < |Δlo|(전도 끝이 레일 끝보다
    안쪽이라 옛 식이면 달라진다). cfg lo = V_p + s_p·Δlo (영역 행·레일 끝). 전도 끝이면 red."""
    snap, _ = _two_stage(tmp_path, 1e-5, 9e4, 2e-5, 4.5e4)
    a1, a2, delta, s_o = _servo_hand(snap)
    vp, s_p, dlo, dhi = _servo_window(snap)
    cond = []
    for m, pn in (("M1", "ip"), ("M2", "im")):
        ss, op = snap.value("device", m, "ss_dev"), snap.value("device", m, "dc_op")
        cond.append(-op.current / (ss.gm * s_p[pn] + ss.gds * s_o))
    assert dlo == max((0.0 - vp[p]) / s_p[p] for p in vp)                       # 전제: 아래 끝은 레일 끝
    assert all(abs(c) < abs(dlo) for c in cond), (cond, dlo)                    # 전제: |Δc| < |Δlo|
    for pn in ("ip", "im"):
        w = snap.value("node", pn, "dc_window_cfg")
        e_lo, e_hi = sorted((vp[pn] + s_p[pn] * dlo, vp[pn] + s_p[pn] * dhi))
        assert _close(w.lo, e_lo, 1e-8) or abs(w.lo - e_lo) <= 1e-9
        assert all(abs(w.lo - (vp[pn] + s_p[pn] * c)) > 1e-6 for c in cond)     # 전도 끝이 아니다


def _tk_topo(extra_branch):
    mos = [("M1", "nmos", "out", "in", "gnd", "gnd")]
    pas = [("R1", "resistor", "vdd", "out"), ("CL", "capacitor", "out", "gnd")]
    bias = []
    if extra_branch:
        mos.append(("Mb", "nmos", "b", "vb", "gnd", "gnd"))
        pas.append(("Rb", "resistor", "vdd", "b"))
        bias = ["vb"]
    return topo_doc("it2c_tk%s" % ("b" if extra_branch else "a"), mos=mos, passives=pas, rails=("vdd", "gnd"), bias=bias)


def test_it2c_tk_triode_declared_saturated_point_is_rejected_by_seal(tmp_path):
    """[EO-1 범위 4로 옮김; 옛 T-K 빈 창 (a) 'triode 선언 M1 이 봉인점에서 포화 -> cfg unmeasured'] 그 입력은 이제 봉인 단계에서 거부된다
    (interface 20261104-eo1r4-sf1l §1 표 행 10, T-S2·T-M1): `triode` 선언 M1 이 V(out) = 1.8 − I·R = 1.75 V > VDSAT = 0.1 + 0.2·0.6 = 0.22 V(포화)이면
    size_and_seal 이 봉인 7 로 거부(devices (M1,))하므로 icm_config 까지 가지 않는다. 손 유도 전제: 동작점이 포화."""
    from gmid_engine.core import SealViolationError
    i, r = 1e-5, 5e3
    assert 1.8 - i * r > _vdsat(0.6)                                                 # 전제(포화)
    th = {("L", "M1"): L0, ("ln_idu", "M1"): lut_ln_idu("nmos", 0.6, 1.8 - i * r, 0.0), ("current", "R1"): i, ("resistance", "R1"): r}
    with pytest.raises(SealViolationError) as ei:
        _evaluate_region(tmp_path, _tk_topo(False), (("R1", "resistor", None), ("CL", "capacitor", 1e-12)), th, {"M1": "triode"})
    assert dict(ei.value.record.detail)["item"] == 7 and ei.value.record.devices == ("M1",)


def test_it2c_tk_skipped_row_triode_declared_saturated_is_rejected_by_seal(tmp_path):
    """[EO-1 범위 4로 옮김; 옛 T-K 빈 창 (b)] 입력과 무관한 가지 Mb (b, vb, gnd) + Rb (vdd, b) 의 Mb 를 `triode` 로 선언하나 봉인점은 포화(V(b) = 1.75 V > VDSAT 0.22 V)
    -> 봉인 7 거부(devices (Mb,)). 건너뛴 행의 slack < 0 이 cfg unmeasured 로 가던 경로는 봉인이 먼저 막는다."""
    from gmid_engine.core import SealViolationError
    i, r = 1e-5, 5e3
    assert 1.8 - i * r > _vdsat(0.6)                                                 # 전제(포화)
    th = {("L", "M1"): L0, ("L", "Mb"): L0, ("ln_idu", "M1"): lut_ln_idu("nmos", 0.6, 0.9, 0.0),
          ("ln_idu", "Mb"): lut_ln_idu("nmos", 0.6, 1.8 - i * r, 0.0),
          ("current", "R1"): 1e-5, ("resistance", "R1"): 9e4, ("current", "Rb"): i, ("resistance", "Rb"): r}
    with pytest.raises(SealViolationError) as ei:
        _evaluate_region(tmp_path, _tk_topo(True), (("R1", "resistor", None), ("Rb", "resistor", None), ("CL", "capacitor", 1e-12)), th,
                         {"Mb": "triode"})
    assert dict(ei.value.record.detail)["item"] == 7 and ei.value.record.devices == ("Mb",)


def test_it2c_region_rows_hand_values(tmp_path):
    """oracle 대조: (손) 값 test (빈칸 답 2-8). 공통 소스 증폭기 봉인점(V(out) = 0.9, VGS = 0.6): 선언 없음 -> (("out", "gnd", +1, 0.9 − VDSAT, "sat"),),
    VDSAT = 0.1 + 0.2·0.6 (LUT 열 닫힌 식). linear = {M1}(triode 선언) -> ("out", "gnd", −1, VDSAT − 0.9, "triode"). 판정 여유 0(tol 항 없음)."""
    from gmid_engine.sizing._helpers_dc_solve import Circuit
    snap, ctx = _cs(tmp_path, i=1e-5, r=9e4)
    values = dict(snap.column("node", "dc_v"))
    vdsat = _vdsat(0.6)
    rows = Circuit(snap, lut=ctx.lut, linear=frozenset()).region_rows(values)
    assert rows is not None and len(rows) == 1
    a, b, sign, slack, kind = rows[0]
    assert (a, b, sign, kind) == ("out", "gnd", 1, "sat") and abs(slack - (0.9 - vdsat)) <= 1e-9
    rows = Circuit(snap, lut=ctx.lut, linear=frozenset({"M1"})).region_rows(values)
    a, b, sign, slack, kind = rows[0]
    assert (a, b, sign, kind) == ("out", "gnd", -1, "triode") and abs(slack - (vdsat - 0.9)) <= 1e-9


def test_it2c_nodal_system_arrays_immutable_and_fp_sees_g_bound(tmp_path):
    """oracle 대조: (d) 값 test (빈칸 답 2-8). `graph.ss_nodal` 값 `NodalSystem` 의 g·g_bound 는 쓰기 불가(ValueError), g_bound 만 다른 두 NodalSystem 의 `fp_of` 는 다르다."""
    import dataclasses
    from gmid_engine.core import fp_of
    snap, _ = _cs(tmp_path)
    sysm = next(iter(dict(snap.column("graph", "ss_nodal")).values()))
    for arr in (sysm.g, sysm.g_bound):
        assert arr.flags.writeable is False
        with pytest.raises(ValueError):
            arr[0, 0] = 1.0
    other = dataclasses.replace(sysm, g_bound=sysm.g_bound * 2.0)
    assert fp_of(other) != fp_of(sysm)
