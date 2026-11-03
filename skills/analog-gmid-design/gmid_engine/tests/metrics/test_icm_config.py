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


def _evaluate(tmp, topo, els, theta, constraints, *, input_dc_v=None, with_vdsat=True):
    """spec 로더 -> build_s1 -> 커널 -> size_and_seal -> ss_evaluate. 반환 (snapshot, ctx)."""
    from gmid_engine.graph import build_s1
    td, spec = load_case(tmp / "case", topo, SUP, els, (), constraints, input_dc_v=input_dc_v)
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
