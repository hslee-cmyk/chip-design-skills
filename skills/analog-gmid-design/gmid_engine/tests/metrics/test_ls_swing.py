"""`ls_swing` -- 설계 40 §3.8-8 `swing_out_v`·`icmr_v`·`icm_margin_v`, 41 §4.6(J-E), 체크리스트 D-SW·D-ICM·D-J5, 계획 N3.8 경로 합,
metrics CONTRACT 10.5.

규칙(계약 10.5·10.9 (1)): 채널 엣지 NMOS V_d − V_s ≥ sat, PMOS V_s − V_d ≥ sat(`linear` 제외), VGS 엣지 V_g − V_s = polarity·|VGS| 는
source 가 레일이 아닌 소자와 diode(g = d)에만, 모든 노드 [rail_min, rail_max], 단일 swing = 2·min 반폭, 차동 출력 쌍 = 4·min 반폭.
[IT-2d 갱신 O-109·O-111~O-113] 입력 창(icmr_v·icm_margin_v)은 이 함수의 일이 아니다 -- `icm_window_metrics`(graph.icm_config V_cm 칸)가 낸다.
서명 = `ls_swing(devices, rails, node_v, outputs, diff_outputs=False)`, 인자 `inputs`·`input_dc_v` 없음. 삭제한 단언: 입력 창·icmr·margin·
required_input_cm_v·입력 포트 정의 불능 사유(모두 icm_window 몫, 새 test_icm_window.py 가 같은 양을 V_cm 칸으로 본다).

oracle:
* (a) 손 toy 경로 합(이 파일 각 test docstring 에 산수) -- 작성자 toy 와 다른 수치로 다시 유도.
* (b) 같은 차분 제약계를 scipy `linprog`(HiGHS 선형계획)으로 노드마다 min/max -- Bellman–Ford 와 다른 방법.
* ngspice `.dc` 대조는 하지 않았다: `SatDevice` 의 sat·|VGS| 는 봉인 점에서 고정된 입력값이라 소자 모델 스윕(점마다 VDSAT 이 바뀐다)과
  같은 양이 아니다(계약 10.9 (2) '선형화와 경로 합 차이' -- 판정은 오라클 D-OR5 몫).
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.optimize import linprog

from gmid_engine.metrics import SatDevice, SwingIcmr, ls_swing

from .conftest import codes

RAILS = (("gnd", 0.0), ("vdd", 1.8))


def n(label, d, g, s, vgs, sat, **kw):
    return SatDevice(label, 1, d, g, s, vgs, sat, **kw)


def p(label, d, g, s, vgs, sat, **kw):
    return SatDevice(label, -1, d, g, s, vgs, sat, **kw)


def lp_bounds(devices, rails, nets):
    """(b) 독립 선형계획: 같은 제약을 손으로 다시 적어 노드마다 min·max."""
    names = sorted(set(nets) | {x for m in devices for x in (m.d, m.g, m.s)} | {r for r, _ in rails})
    idx = {k: i for i, k in enumerate(names)}
    rail = dict(rails)
    lo_r, hi_r = min(rail.values()), max(rail.values())
    a_ub, b_ub, a_eq, b_eq = [], [], [], []
    for m in devices:
        if not m.linear:
            row = np.zeros(len(names))
            hi_net, lo_net = (m.d, m.s) if m.polarity > 0 else (m.s, m.d)
            row[idx[lo_net]], row[idx[hi_net]] = 1.0, -1.0          # V_lo − V_hi ≤ −sat
            a_ub.append(row)
            b_ub.append(-m.sat_v)
        if m.s not in rail or m.g == m.d:
            row = np.zeros(len(names))
            row[idx[m.g]], row[idx[m.s]] = 1.0, -1.0
            a_eq.append(row)
            b_eq.append(m.polarity * m.vgs_v)
    bounds = [(rail[k], rail[k]) if k in rail else (lo_r, hi_r) for k in names]
    out = {}
    for k in nets:
        c = np.zeros(len(names))
        c[idx[k]] = 1.0
        kw = dict(A_ub=np.array(a_ub) if a_ub else None, b_ub=b_ub or None, A_eq=np.array(a_eq) if a_eq else None,
                  b_eq=b_eq or None, bounds=bounds, method="highs")
        lo = linprog(c, **kw)
        hi = linprog(-c, **kw)
        out[k] = (lo.fun if lo.status == 0 else None, -hi.fun if hi.status == 0 else None)
    return out


def bounds_of(got):
    return {k: (lo, hi) for k, lo, hi in got.bounds}


# ---------------------------------------------------------------- (a) 손 toy

CS = (n("M1", "out", "in", "gnd", 0.6, 0.15), p("M2", "out", "vbp", "vdd", 0.7, 0.3))


def test_cs_current_source_load():
    """CS + PMOS 전류원: out ∈ [0.15, 1.8 − 0.3 = 1.5], V_o = 1.0 -> 반폭 min(0.5, 0.85) = 0.5 -> swing 1.0.
    [IT-2d] 입력 창 칸은 이 함수가 채우지 않는다(icm_window 몫): 기본값 그대로."""
    got = ls_swing(CS, RAILS, (("out", 1.0), ("in", 0.6)), ("out",))
    assert isinstance(got, SwingIcmr) and got.undefined == ()
    assert got.swing_out_v == pytest.approx(1.0, abs=1e-12)
    assert got.out_ranges == (("out", pytest.approx(0.15), pytest.approx(1.5), 1.0),)
    assert (got.icmr_v, got.icm_margin_v, got.window, got.v_icm, got.required_input_cm_v, got.input_dc) == \
        (None, None, (), None, None, "")


def test_cascode_raises_low_bound():
    """캐스코드 Mc(d out, g vb, s x; VGS 0.7, sat 0.25) 위 입력 M1(d x, sat 0.2): x ≥ 0.2, out ≥ x + 0.25 ≥ 0.45;
    vb = x + 0.7 ≤ 1.8 -> x ≤ 1.1, vb ≥ 0.9. 부하 PMOS sat 0.3 -> out ≤ 1.5. V_o 0.9 -> 반폭 min(0.6, 0.45) -> swing 0.9."""
    devs = (n("M1", "x", "in", "gnd", 0.6, 0.2), n("Mc", "out", "vb", "x", 0.7, 0.25), p("Ml", "out", "vbp", "vdd", 0.7, 0.3))
    got = ls_swing(devs, RAILS, (("out", 0.9), ("in", 0.6)), ("out",))
    b = bounds_of(got)
    assert b["out"] == (pytest.approx(0.45), pytest.approx(1.5))
    assert b["x"] == (pytest.approx(0.2), pytest.approx(1.1))
    assert b["vb"] == (pytest.approx(0.9), pytest.approx(1.8))
    assert got.swing_out_v == pytest.approx(0.9, abs=1e-12)


def test_nmos_follower_and_input_window():
    """NMOS follower M1(d vdd, g in, s out; VGS 0.55, sat 0.2) + 싱크 M2(sat 0.12): out ≥ 0.12, out ≤ 1.8 − 0.55 = 1.25
    (gate 상한이 레일) 과 ≤ 1.8 − 0.2 = 1.6 중 1.25. V_o 0.7 -> 반폭 min(0.58, 0.55) -> swing 1.1.
    [IT-2d] 입력 창(옛 icmr 1.13·margin 0.55·required)은 icm_window 몫이라 여기서 단언하지 않는다."""
    devs = (n("M1", "vdd", "in", "out", 0.55, 0.2), n("M2", "out", "vb", "gnd", 0.6, 0.12))
    got = ls_swing(devs, RAILS, (("out", 0.7), ("in", 1.25)), ("out",))
    assert got.out_ranges[0][1:3] == (pytest.approx(0.12), pytest.approx(1.25))
    assert got.swing_out_v == pytest.approx(1.1, abs=1e-12)


def test_differential_pair_four_times_min_half_width():
    """차동쌍 M1/M2(s t; VGS 0.65, sat 0.15), 꼬리 M3(d t, sat 0.2), PMOS 부하(sat 0.25): t ≥ 0.2, out ≥ t + 0.15 ≥ 0.35,
    out ≤ 1.55. 출력 DC 0.95/0.9 -> 반폭 min(0.6, 0.55) = 0.55 -> 차동 4·0.55 = 2.2. (입력 창은 icm_window 몫)"""
    devs = (n("M1", "om", "ip", "t", 0.65, 0.15), n("M2", "op", "im", "t", 0.65, 0.15), n("M3", "t", "vb", "gnd", 0.6, 0.2),
            p("M4", "om", "vbp", "vdd", 0.7, 0.25), p("M5", "op", "vbp", "vdd", 0.7, 0.25))
    nv = (("om", 0.95), ("op", 0.9), ("ip", 1.0), ("im", 1.0))
    got = ls_swing(devs, RAILS, nv, ("op", "om"), True)
    assert got.swing_out_v == pytest.approx(2.2, abs=1e-12)
    single = ls_swing(devs, RAILS, nv, ("op", "om"), False)
    assert single.swing_out_v == pytest.approx(1.1, abs=1e-12)                # 차동 표지 없으면 2·min


def test_linear_device_has_no_channel_edge():
    devs = (n("M1", "out", "in", "gnd", 0.6, 0.15, linear=True), p("M2", "out", "vbp", "vdd", 0.7, 0.3))
    got = ls_swing(devs, RAILS, (("out", 1.0), ("in", 0.6)), ("out",))
    assert got.out_ranges[0][1] == pytest.approx(0.0, abs=1e-15)                # 하한 = 레일
    assert got.swing_out_v == pytest.approx(1.0, abs=1e-12)                     # min(0.5, 1.0)·2


def test_resolution_follows_binding_side():
    """분해능 = 구속 쪽 엣지 허용오차 누적(계약 10.5): CS toy 에서 위쪽(0.5) 이 구속 -> M2 sat_tol 0.02 -> swing_res 2·0.02.
    [IT-2d] 옛 icmr_resolution 단언(입력 창 누적)은 삭제 -- icm_window 의 icmr_resolution = 2·tol_v 가 같은 양을 본다."""
    devs = (n("M1", "out", "in", "gnd", 0.6, 0.15, sat_tol_v=0.01), p("M2", "out", "vbp", "vdd", 0.7, 0.3, sat_tol_v=0.02))
    got = ls_swing(devs, RAILS, (("out", 1.0), ("in", 0.6)), ("out",))
    assert got.swing_resolution == pytest.approx(0.04, abs=1e-15)
    missing = (n("M1", "out", "in", "gnd", 0.6, 0.15), p("M2", "out", "vbp", "vdd", 0.7, 0.3, sat_tol_v=0.02))
    assert ls_swing(missing, RAILS, (("out", 1.0), ("in", 0.6)), ("out",)).swing_resolution is not None
    lo_bound = (n("M1", "out", "in", "gnd", 0.6, 0.15), p("M2", "out", "vbp", "vdd", 0.7, 0.3, sat_tol_v=0.02))
    assert ls_swing(lo_bound, RAILS, (("out", 0.3), ("in", 0.6)), ("out",)).swing_resolution is None


# ---------------------------------------------------------------- (b) 선형계획 대조

TOYS = {
    "cs": (CS, ("out", "in")),
    "cascode": ((n("M1", "x", "in", "gnd", 0.6, 0.2), n("Mc", "out", "vb", "x", 0.7, 0.25), p("Ml", "out", "vbp", "vdd", 0.7, 0.3)),
                ("out", "x", "vb", "in")),
    "follower_stack": ((n("M1", "vdd", "in", "a", 0.55, 0.2), p("M2", "gnd", "a", "b", 0.62, 0.18), n("M3", "b", "vbn", "gnd", 0.6, 0.11),
                        p("M4", "a", "vbp", "vdd", 0.7, 0.21)), ("a", "b", "in")),
    "telescopic": ((n("M1", "x1", "ip", "t", 0.65, 0.12), n("M2", "x2", "im", "t", 0.65, 0.12), n("Mt", "t", "vb", "gnd", 0.6, 0.2),
                    n("Mc1", "om", "vc", "x1", 0.7, 0.13), n("Mc2", "op", "vc", "x2", 0.7, 0.13),
                    p("Mp1", "om", "vbp", "vdd", 0.7, 0.22), p("Mp2", "op", "vbp", "vdd", 0.7, 0.22)),
                   ("om", "op", "x1", "t", "vc", "ip")),
}


@pytest.mark.parametrize("name", sorted(TOYS))
def test_bounds_match_linear_program(name):
    devs, nets = TOYS[name]
    nv = tuple((k, 0.9) for k in nets)
    got = ls_swing(devs, RAILS, nv, (nets[0],))
    ref = lp_bounds(devs, RAILS, nets)
    b = bounds_of(got)
    for k in nets[:-1]:                                                          # 마지막 넷 = 입력 포트(입력 창은 icm_window 몫)
        assert b[k][0] == pytest.approx(ref[k][0], abs=1e-12), (k, b[k], ref[k])
        assert b[k][1] == pytest.approx(ref[k][1], abs=1e-12), (k, b[k], ref[k])


# ---------------------------------------------------------------- 정의 불가·불변

def test_undefined_codes_swing_only():
    """[IT-2d] 정의 불능 사유는 스윙 것만(입력 포트 사유 no_input_port 는 icm_window 몫이라 삭제): swing_out_v 하나에 code 하나."""
    for args, want in (((CS, RAILS, (("out", 1.0),), ()), "no_output_port"),
                       (((n("M1", "out", "in", "gnd", 0.6, None),), RAILS, (("out", 1.0), ("in", 0.6)), ("out",)),
                        "sat_unavailable"),
                       # [A-85 D1] 옛 셋째 사례의 전제(입력 인자 ("in",)의 node_v 없음)는 입력 인자와 함께 사라졌다. 출력 넷 out 의 전압이 node_v 에 없는 입력으로 재현한다.
                       ((CS, RAILS, (), ("out",)), "node_v_missing")):
        got = ls_swing(*args)
        assert got.swing_out_v is None
        assert {(u.quantity, u.code) for u in got.undefined} == {("swing_out_v", want)}


def test_sat_unavailable_ignored_for_linear_device():
    devs = (n("M1", "out", "in", "gnd", 0.6, None, linear=True), p("M2", "out", "vbp", "vdd", 0.7, 0.3))
    assert ls_swing(devs, RAILS, (("out", 1.0), ("in", 0.6)), ("out",)).undefined == ()


def test_name_bijection_and_order_invariance():
    devs, _ = TOYS["telescopic"]
    nv = (("om", 1.0), ("op", 1.0), ("ip", 1.1), ("im", 1.1))
    a = ls_swing(devs, RAILS, nv, ("op", "om"), True)
    m = {"om": "q9", "op": "a1", "ip": "zz", "im": "b0", "x1": "c", "x2": "y", "t": "k", "vb": "e", "vc": "f", "vbp": "g",
         "gnd": "rail_lo", "vdd": "rail_hi"}
    devs2 = tuple(SatDevice("D" + str(i), d.polarity, m[d.d], m[d.g], m[d.s], d.vgs_v, d.sat_v) for i, d in enumerate(reversed(devs)))
    b = ls_swing(devs2, (("rail_hi", 1.8), ("rail_lo", 0.0)), tuple((m[k], v) for k, v in reversed(nv)), ("a1", "q9"), True)
    assert b.swing_out_v == pytest.approx(a.swing_out_v, abs=1e-12)


def test_deterministic():
    devs, _ = TOYS["telescopic"]
    args = (devs, RAILS, (("om", 1.0), ("op", 1.0), ("ip", 1.1), ("im", 1.1)), ("op", "om"), True)
    assert ls_swing(*args) == ls_swing(*args)


# ---------------------------------------------------------------- [IT-2d T-LS] 새 서명·입력 칸 기본값

def test_it2d_ls_swing_signature_has_no_input_arguments():
    """interface: `ls_swing(devices, rails, node_v, outputs, diff_outputs=False)`, 인자 `inputs`·`input_dc_v` 없음. oracle (식) interface 서명.
    옛 호출(입력 인자 포함)은 TypeError 로 거부된다."""
    import inspect
    params = inspect.signature(ls_swing).parameters
    assert list(params) == ["devices", "rails", "node_v", "outputs", "diff_outputs"]
    assert params["diff_outputs"].default is False
    nv = (("out", 1.0), ("in", 0.6))
    with pytest.raises(TypeError):
        ls_swing(CS, RAILS, nv, ("out",), ("in",), False, 0.6)
    with pytest.raises(TypeError):
        ls_swing(CS, RAILS, nv, ("out",), inputs=("in",))
    with pytest.raises(TypeError):
        ls_swing(CS, RAILS, nv, ("out",), input_dc_v=0.6)


def test_it2d_ls_swing_input_fields_keep_defaults():
    """interface T-LS: ls_swing 출력의 입력 칸은 기본값 -- icmr_v·icm_margin_v None, window (), v_icm·required_input_cm_v None,
    input_dc "". 차동·단일 둘 다. oracle (식) interface 기본값 문장."""
    devs = (n("M1", "om", "ip", "t", 0.65, 0.15), n("M2", "op", "im", "t", 0.65, 0.15), n("M3", "t", "vb", "gnd", 0.6, 0.2),
            p("M4", "om", "vbp", "vdd", 0.7, 0.25), p("M5", "op", "vbp", "vdd", 0.7, 0.25))
    nv = (("om", 0.95), ("op", 0.9), ("ip", 1.0), ("im", 1.0))
    for got in (ls_swing(devs, RAILS, nv, ("op", "om"), True), ls_swing(devs, RAILS, nv, ("op", "om"))):
        assert (got.icmr_v, got.icm_margin_v, got.window, got.v_icm, got.required_input_cm_v, got.input_dc) == \
            (None, None, (), None, None, "")


def test_it2d_ls_swing_circuit_without_inputs_has_swing_value():
    """interface T-LS: 입력 없는 회로(입력 포트를 아무 곳에도 선언하지 않고 node_v 에 입력 넷이 없다)도 swing_out_v 값이 있다.
    CS 와 같은 회로 -> 손계산 CS 와 같음: out ∈ [0.15, 1.5], V_o 1.0 -> 반폭 0.5 -> swing 1.0. oracle (a) 구성(위 test_cs_current_source_load 산수)."""
    got = ls_swing(CS, RAILS, (("out", 1.0),), ("out",))
    assert got.undefined == ()
    assert got.swing_out_v == pytest.approx(1.0, abs=1e-12)


# ---------------------------------------------------------------- [IT-2d T-G2] (독립) AST: 입력 창 계산 0, 옛 front 전용 이름 0, saturation_window 호출 자리

def _engine_files():
    import gmid_engine
    from pathlib import Path
    root = Path(gmid_engine.__file__).parent
    return root, [p for p in sorted(root.rglob("*.py")) if "tests" not in p.relative_to(root).parts]


def _ids(tree):
    import ast
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.append(n.id)
        elif isinstance(n, ast.Attribute):
            out.append(n.attr)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append(n.name)
        elif isinstance(n, ast.arg):
            out.append(n.arg)
        elif isinstance(n, ast.alias):
            out.append(n.name.rsplit(".", 1)[-1])
        elif isinstance(n, ast.keyword) and n.arg:
            out.append(n.arg)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.append(n.value)
    return out


def test_it2d_g2_ls_swing_source_has_no_input_window_computation():
    """`ls_swing` 소스(함수 본문)에 입력 창 계산이 없다: 입력 인자 이름(inputs·input_dc_v)과 입력 창 칸(required_input_cm_v·v_icm)을
    쓰는 식별자가 0, `saturation_window` 호출 0. 함수는 gmid_engine/metrics/ls_swing.py 에서 찾는다."""
    import ast
    root, _ = _engine_files()
    tree = ast.parse((root / "metrics" / "ls_swing.py").read_text(encoding="utf-8"))
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "ls_swing"]
    assert len(fns) == 1
    bad = {"inputs", "input_dc_v", "required_input_cm_v", "v_icm", "saturation_window"}
    assert not bad & set(_ids(fns[0]))


def test_it2d_g2_no_old_front_names_in_engine_sources():
    """비test 엔진 소스에 `node.dc_window_def`·`dc_window_def_refined`·`dc_window_refine`·`metrics_icm_front`·`refine_front_windows`·`icm_front`
    (그리고 옛 이름 RefinedWindow·WindowEnd) 정의·참조 0 -- 식별자·정의 이름·정확히 같은 문자열 상수 기준(주석·docstring 은 제외)."""
    root, files = _engine_files()
    names = {"dc_window_def", "dc_window_def_refined", "dc_window_refine", "metrics_icm_front", "refine_front_windows", "icm_front",
             "RefinedWindow", "WindowEnd"}
    import ast
    hits = []
    for path in files:
        found = names & set(_ids(ast.parse(path.read_text(encoding="utf-8"))))
        if found:
            hits.append((path.relative_to(root).as_posix(), sorted(found)))
    assert hits == []


def test_it2d_g2_saturation_window_called_only_from_kernel_and_icm_config():
    """`saturation_window` 호출 자리 = `Circuit` 경유 커널(sizing/)과 metrics/icm_config.py 뿐 -- metrics 의 다른 파일(ls_swing·metrics_aux 포함)·
    search·graph 에는 호출이 없다."""
    import ast
    root, files = _engine_files()
    callers = set()
    for path in files:
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call) and (getattr(n.func, "id", None) == "saturation_window"
                                            or getattr(n.func, "attr", None) == "saturation_window"):
                callers.add(path.relative_to(root).as_posix())
    assert callers, "호출 자리가 하나도 없다(전제)"
    assert all(c.startswith("sizing/") or c == "metrics/icm_config.py" for c in callers), callers
