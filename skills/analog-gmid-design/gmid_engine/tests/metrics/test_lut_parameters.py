"""`lut_parameters` (LUT 에서 온 MOS 소신호 파라미터·Δp = ε·|p|·단위 스탬프 항목) -- metrics CONTRACT 9.1.

기대값 근거: 9.1 문장(파라미터 집합·Δp 식·필드 뜻·입력 규약), 9.5 예 7 + ε = 0.02, 3.1 MOS 스탬프 식(단위 스탬프 = 파라미터 p 만 1 로 둔
`MosSmallSignal` 의 `mos_stamps` 항목 -- 계약이 정본 재사용을 명시하므로 공개 `mos_stamps` 를 그 정의로 쓴다. 그 식 자체는
test_stamp_mos 가 따로 확인한다).
"""
from __future__ import annotations

import ast
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.metrics import (
    LUT_PARAMETERS,
    Capacitor,
    Factor,
    MosSmallSignal,
    ParameterSet,
    Resistor,
    SmallSignalCircuit,
    analyze_loop,
    lut_parameters,
    metric_resolutions,
    mos_stamps,
    solve_responses,
)

from .conftest import (
    EX7_CAP,
    EX7_MOS12,
    FD_H,
    LUT_P,
    LUT_P_OLD,
    MILLER_V_CAP,
    MILLER_V_MOS,
    MILLER_V_RES,
    MOS_IX,
    circuit12,
    lut_params_of,
    miller_v_system,
    perturbed,
)

CAPS = ("cgs", "cgd", "cgb", "cdb", "csb")           # 용량 스탬프(capacitive) 파라미터 -- [JC-1] cdb·csb 포함


def _ex7():
    return circuit12(EX7_MOS12, (), EX7_CAP)


def _miller():
    return circuit12(MILLER_V_MOS, MILLER_V_RES, MILLER_V_CAP)


def test_lut_parameters_constant():
    """[JC-1 §6] LUT 파라미터 = (gm, gmb, gds, cgs, cgd, cgb, cdb, csb) -- cdb·csb 는 LUT C 열 조회라 목록에 든다. 수동소자는 들지 않는다.
    (옛 '6열, cdb not in' 단언은 R-a 로 대체 -- `retired_tests` covered_by = R-a)"""
    assert tuple(LUT_PARAMETERS) == LUT_P == ("gm", "gmb", "gds", "cgs", "cgd", "cgb", "cdb", "csb")


# ---------------------------------------------------------------- JC-1 R-a·R-c: 구조 단언 (Δp 꼴과 무관)

ENGINE_METRICS = Path(__file__).resolve().parents[2] / "metrics"
LUT_PARAMETERS_SRC = ENGINE_METRICS / "lut_parameters.py"
METRICS_CONTRACT = ENGINE_METRICS / "CONTRACT.md"
LIST_NAMES = ("LUT_PARAMETERS", "_VALUE_FIELDS")


def _iter_uses_name(node, name):
    return any(isinstance(n, ast.Name) and n.id == name for n in ast.walk(node))


def test_jc1_ra_single_iteration_over_lut_parameters_and_no_junction_branch():
    """R-a: `lut_parameters.py` 소스 AST -- `LUT_PARAMETERS` 를 반복 대상으로 쓰는 for·comprehension = 1(8열 모두를 한 순회가 낸다),
    문자열 상수 "cdb"·"csb" 는 `LUT_PARAMETERS`·`_VALUE_FIELDS` 할당 값 안에만 있고(전용 가지·상수 0), `LUT_PARAMETERS` 값에 둘 다 있다. oracle (구조)."""
    tree = ast.parse(LUT_PARAMETERS_SRC.read_text(encoding="utf-8"))
    loops = [n for n in ast.walk(tree) if (isinstance(n, (ast.For, ast.AsyncFor)) and _iter_uses_name(n.iter, "LUT_PARAMETERS"))
             or (isinstance(n, ast.comprehension) and _iter_uses_name(n.iter, "LUT_PARAMETERS"))]
    assert len(loops) == 1, len(loops)
    inside = set()
    for n in ast.walk(tree):
        targets = ()
        if isinstance(n, ast.Assign):
            targets = tuple(t.id for t in n.targets if isinstance(t, ast.Name))
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            targets = (n.target.id,)
        if any(t in LIST_NAMES for t in targets):
            inside.update(id(c) for c in ast.walk(n))
    stray = [c.lineno for c in ast.walk(tree)
             if isinstance(c, ast.Constant) and c.value in ("cdb", "csb") and id(c) not in inside]
    assert stray == [], "cdb·csb 문자열이 목록 정의 밖에 있다(전용 가지): 줄 %r" % (stray,)
    assert "cdb" in LUT_PARAMETERS and "csb" in LUT_PARAMETERS


def test_jc1_rc_no_junction_closed_form_premise_text():
    """R-c: `lut_parameters.py`·metrics CONTRACT 에서 '폐형식' 과 (접합 | cdb | csb) 가 같은 줄에 있는 줄 = 0 (옛 전제 문언 '접합은 폐형식이라' 삭제)."""
    hits = []
    for p in (LUT_PARAMETERS_SRC, METRICS_CONTRACT):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "폐형식" in line and any(w in line for w in ("접합", "cdb", "csb")):
                hits.append("%s:%d" % (p.name, i))
    assert hits == [], hits


def _miller_loop(mos=MILLER_V_MOS):
    ck, sysm = miller_v_system(mos)
    (resp,) = solve_responses((sysm,))
    f = Factor(resp, 0, 0)
    return ck, analyze_loop((f,)), (f,)


def test_jc1_rb_junction_terms_in_parameter_set_and_resolution_grows(monkeypatch):
    """R-b: Miller 변형(드레인 노드 용량이 극점을 정하고 cdb ≠ 0, 소스 저항으로 소스가 AC 접지 아님 -> csb 감도 ≠ 0, 두 번째 MOS 도 cdb ≠ 0) --
    (1) `ParameterSet.params` ∋ (0, "cdb"), (0, "csb"), 그 두 `delta` 원소 유한·≥ 0 (Δ 값 자체·ε·|p| 꼴은 단언하지 않는다)
    (2) 같은 회로·같은 rel_tol·같은 cdb·csb 값에서 `LUT_PARAMETERS` 를 옛 6열로 바꾼(monkeypatch) 호출의 분해능 LUT 몫 `Resolution.lut` = B₆,
        그대로 = B₈ 이라 하면 ugf·gbw·PM 마다 B₈ > B₆ (엄격; value = max(lut, numeric) 이라 value 로 비교하지 않는다).
    전제(PM): 독립 MNA(conftest `ref_system`) 중심 차분으로 cdb 에 대한 PM 감도가 0 이 아니다 -- 단일 극점 루프의 PM 은 용량과 무관하므로 거짓 red 방지.
    oracle (a): B₈ 와 B₆ 의 대소는 목록에 들어온 음 아닌 항(감도 ≠ 0, Δ > 0)의 합이 늘었다는 구성의 귀결."""
    eps = (0.01, 0.03)
    ck, la, src = _miller_loop()
    exp_params = lut_params_of(MILLER_V_MOS)
    assert (0, "cdb") in exp_params and (0, "csb") in exp_params          # 입력 확인: cdb·csb ≠ 0
    ps8 = lut_parameters(ck, eps)
    assert (0, "cdb") in tuple(ps8.params) and (0, "csb") in tuple(ps8.params)
    for key in ((0, "cdb"), (0, "csb"), (1, "cdb")):
        d = float(ps8.delta[tuple(ps8.params).index(key)])
        assert math.isfinite(d) and d >= 0.0, (key, d)
    # 전제: 접합 용량에 대한 PM·UGF·GBW 감도가 0 이 아니다(독립 MNA 중심 차분)
    for name in ("cdb", "csb"):
        k = 0
        pm_hi, pm_lo = (_own_metrics(perturbed(MILLER_V_MOS, k, name, 1.0 + s * FD_H)) for s in (+1, -1))
        for q in ("ugf_hz", "gbw_hz", "phase_margin_deg"):
            assert pm_hi[q] != pm_lo[q], (name, q)
    res8 = {r.quantity: r for r in metric_resolutions(la, src, ps8)}
    import sys
    mod = sys.modules["gmid_engine.metrics.lut_parameters"]
    monkeypatch.setattr(mod, "LUT_PARAMETERS", LUT_P_OLD)                 # 관찰 지점: 호출 때 읽는 모듈 전역(항 없는 경로)
    ps6 = lut_parameters(ck, eps)
    assert all(name in LUT_P_OLD for _, name in ps6.params)               # 항 없는 경로가 실제로 만들어졌다
    res6 = {r.quantity: r for r in metric_resolutions(la, src, ps6)}
    for q in ("ugf_hz", "gbw_hz", "phase_margin_deg"):
        assert res8[q].lut > res6[q].lut, (q, res8[q].lut, res6[q].lut)


def _own_metrics(mos):
    from .test_resolution import _miller_own
    return _miller_own(mos)


def test_example7_params_and_delta():
    """9.5: 예 7 + ε 0.02 -> params ((0, gm), (0, gds)) (gmb·용량 0 은 빠진다), delta = ε·|p| = (2e-5, 2e-7)."""
    ps = lut_parameters(_ex7(), (0.02,))
    assert isinstance(ps, ParameterSet)
    assert tuple(ps.params) == ((0, "gm"), (0, "gds"))
    assert np.asarray(ps.delta).shape == (2,)
    # Δp = ε·|p| 한 번의 곱(IEEE 곱은 교환 법칙이 정확) -> 같은 곱과 비트 동일
    assert list(ps.delta) == [0.02 * 1e-3, 0.02 * 1e-5]
    assert tuple(ps.rel_tol) == (0.02,)
    assert tuple(ps.undetermined) == ()


def test_all_eight_parameters_and_negative_capacitance_magnitude():
    """9.1 [JC-1]: 값 ≠ 0 인 LUT 파라미터 전부(MOS 순번, LUT_PARAMETERS 순서) -- cdb·csb 포함. 기존 6열 원소의 Δp = ε·|p|(as-built 회귀 -- RS-1 몫, 넓히지 않음;
    음의 cgb 도 양수 Δ); cdb·csb 원소의 delta 는 존재·유한·≥ 0 만 단언한다(Δ 꼴 단언 0)."""
    eps = (0.01, 0.03)
    ps = lut_parameters(_miller(), eps)
    exp = lut_params_of(MILLER_V_MOS)
    assert len(exp) == 15                                # M1 8열 모두 ≠ 0, M2 7열(csb = 0) -- 입력 확인
    assert tuple(ps.params) == exp
    old = [i for i, (k, nm) in enumerate(exp) if nm in LUT_P_OLD]
    assert [ps.delta[i] for i in old] == [eps[exp[i][0]] * abs(MILLER_V_MOS[exp[i][0]][MOS_IX[exp[i][1]]]) for i in old]
    junction = [i for i, (k, nm) in enumerate(exp) if nm in ("cdb", "csb")]
    assert len(junction) == 3
    assert all(math.isfinite(float(ps.delta[i])) and ps.delta[i] >= 0.0 for i in junction)
    cgb = [i for i, (k, nm) in enumerate(exp) if nm == "cgb"]
    assert all(MILLER_V_MOS[exp[i][0]][MOS_IX["cgb"]] < 0.0 for i in cgb)   # 입력 확인: 음의 cgb
    assert all(ps.delta[i] > 0.0 for i in cgb)


def _unit_entries(dev, name):
    """3.1 식의 단위 스탬프: 파라미터 name 만 1, 나머지 0 인 MosSmallSignal 의 mos_stamps 항목 (행, 열, 값, 용량 여부)."""
    kw = {nm: 0.0 for nm in ("gm", "gmb", "gds", "cgs", "cgd", "cgb", "cdb", "csb")}
    kw[name] = 1.0
    st = mos_stamps(MosSmallSignal(dev.d, dev.g, dev.s, dev.b, **kw))
    return Counter([(r, c, v, False) for r, c, v in st.g] + [(r, c, v, True) for r, c, v in st.c])


@pytest.mark.parametrize("which", ["ex7", "miller"])
def test_unit_stamps_are_mos_stamps_of_unit_parameter(which):
    """9.1: rows·cols·values·capacitive·owner = 파라미터 p 만 1 로 둔 MosSmallSignal 의 mos_stamps 항목(owner = params 위치)."""
    ck = _ex7() if which == "ex7" else _miller()
    eps = (0.02,) if which == "ex7" else (0.01, 0.03)
    ps = lut_parameters(ck, eps)
    rows, cols, vals = np.asarray(ps.rows), np.asarray(ps.cols), np.asarray(ps.values)
    capf, owner = np.asarray(ps.capacitive), np.asarray(ps.owner)
    assert rows.shape == cols.shape == vals.shape == capf.shape == owner.shape
    assert set(owner.tolist()) == set(range(len(ps.params)))
    for i, (k, name) in enumerate(ps.params):
        sel = owner == i
        got = Counter(zip(rows[sel].tolist(), cols[sel].tolist(), vals[sel].tolist(), [bool(x) for x in capf[sel]]))
        assert got == _unit_entries(ck.mos[k], name), (k, name)
        assert all(bool(x) == (name in CAPS) for x in capf[sel])


def test_epsilon_zero_and_none():
    """ε = 0 -> Δ 0(허용, 음수만 거부). None -> undetermined 에 그 MOS 순번(9.1 '미정')."""
    ps0 = lut_parameters(_miller(), (0.0, 0.03))
    for i, (k, nm) in enumerate(ps0.params):
        if nm in LUT_P_OLD:                              # [JC-1] 기존 6열 원소 한정(cdb·csb 의 Δ 꼴은 RS-1 몫 -- 단언하지 않는다)
            assert (ps0.delta[i] == 0.0) if k == 0 else (ps0.delta[i] > 0.0)
    assert tuple(ps0.undetermined) == ()
    assert tuple(lut_parameters(_miller(), (None, 0.03)).undetermined) == (0,)
    assert tuple(lut_parameters(_miller(), (0.01, None)).undetermined) == (1,)
    assert tuple(lut_parameters(_ex7(), (None,)).undetermined) == (0,)


def test_rel_tol_normalized_tuple():
    """9.1 `rel_tol` = 정규화 tuple -- 정수 ε 도 실수로."""
    ps = lut_parameters(_ex7(), (1,))
    assert tuple(ps.rel_tol) == (1.0,) and isinstance(ps.rel_tol[0], float)
    assert list(ps.delta) == [1e-3, 1e-5]


def test_no_mos_circuit_empty():
    """MOS 없는 회로(예 6) -> params () (9.5 예 6)."""
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 3, 1e4)), ac_ground=(0,))
    ps = lut_parameters(ck, ())
    assert tuple(ps.params) == () and np.asarray(ps.delta).shape == (0,)


def test_passives_not_parameters():
    """수동소자 값은 Δp 대상이 아니다(9.1)."""
    ck = SmallSignalCircuit(mos=(MosSmallSignal(2, 1, 0, 0, 1e-3, 0.0, 1e-5),), resistors=(Resistor(2, 0, 1e4),),
                            capacitors=(Capacitor(2, 0, 1e-12),), ac_ground=(0,))
    assert tuple(lut_parameters(ck, (0.05,)).params) == ((0, "gm"), (0, "gds"))


@pytest.mark.parametrize("bad", ["not_circuit", "list", "short", "long", "bool", "str"])
def test_type_errors(bad):
    """9.1 입력 규약: circuit 형식·rel_tol tuple 아님·길이 ≠ MOS 수·원소 bool·비수 -> TypeError."""
    ck = _ex7()
    args = {"not_circuit": (ck.mos, (0.02,)), "list": (ck, [0.02]), "short": (ck, ()), "long": (ck, (0.02, 0.02)),
            "bool": (ck, (True,)), "str": (ck, ("0.02",))}[bad]
    with pytest.raises(TypeError):
        lut_parameters(*args)


@pytest.mark.parametrize("bad", [-0.01, math.nan, math.inf, -math.inf])
def test_value_errors(bad):
    """9.1: 원소 음수·비유한 -> ValueError."""
    with pytest.raises(ValueError):
        lut_parameters(_ex7(), (bad,))


@pytest.mark.parametrize("ok", [0.0, 0.02, 1, None])
def test_negative_check_valid_inputs_do_not_raise(ok):
    """거부 게이트의 음성 대조 -- 유효한 ε 는 통과한다."""
    assert isinstance(lut_parameters(_ex7(), (ok,)), ParameterSet)
