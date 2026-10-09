"""[U8 2026-10-09] `noise_integral(setup)` -- noise_out_int_vrms (설계 41 §7.1 '파일럿 적분 범위'·§7.3 '폐루프 모드'·'스위치', metrics CONTRACT 10.1·10.2).

oracle:
* (a) 폐형식: 1극 RC 출력 잡음의 [f_lo, ∞) 적분 = (kT/C)(1 − (2/π)atan(2πf_lo·RC))(평행 RC, 그리고 다이오드 MOS 의 gm²B = 4kT·gm 이면 같은 kT/C),
  1극 flicker(EF = 1) 적분 (k/2)·ln(1 + (fp/f_lo)²), 폐루프 CS(되먹임 Cf·입력 부하 Cs): 출력 노드 어드미턴스 Y = gds + gm·β + jω(CL + CfCs/(Cf+Cs)),
  β = Cf/(Cf+Cs) -> 1극 적분. 샘플링 커패시터 kT/C_s × (C_s/C_f)²(루프 이득이 크면).
* (b) 독립 노드 해석(conftest `ref_system`): Cs 에 직렬인 전압원의 f_lo 전달 T_s(노턴 전하 C_s·e 주입) -> kT/C_s·|T_s|².
* (d) 계약 10.1·10.3: f_lo = LUT 하한, 꼬리 상계 미수렴 -> `noise_tail_not_converged`, 되먹임 미선언 -> `noise_feedback_undeclared`, kT/C 항은 detail.ktc_v2 로 따로.
판정 기준: 엔진이 낸 불확실성(분해능, 없으면 detail.numeric_v)이 폐형식과의 차이를 덮어야 한다(계약 10.2 '분해능 = max(LUT 몫, 수치 몫)', 41 §7.3
'오차가 분해능 이하가 될 때까지 이분').
"""
import math
import os
import re
import subprocess
from pathlib import Path

import pytest

from gmid_engine.metrics import NoiseDecl, noise_analysis, noise_integral

from .noise_cases import (
    F_LO,
    KT,
    TWO_PI,
    Case,
    closed_one_pole_flicker_integral,
    closed_one_pole_integral,
    codes,
    detail,
    dev,
    ref_poles,
    setup_of,
)

R, C = 1e4, 1e-12                               # CONTRACT 10.5 평행 RC 값
GM, GDS, CL, CF, CS = 1e-3, 1e-7, 1e-12, 1e-12, 3e-12
B0, A0 = 1e-16, 1e-12


def kt_over_c_from(f_lo, tau, cap):
    """평행 RC 의 [f_lo, ∞) 적분 = (kT/C)(1 − (2/π)atan(2πf_lo·τ)). oracle (a)."""
    return KT / cap * (1.0 - 2.0 / math.pi * math.atan(TWO_PI * f_lo * tau))


def parallel_rc():
    """in -R- out, C out-gnd, 입력 고정(개루프 출력 잡음 = 출력 노드에서 본 R‖C)."""
    return Case(res=(("R", "in", "out", R),), cap=(("C", "out", "gnd", C),))


def test_parallel_rc_is_kt_over_c():
    """평행 RC: out_int = sqrt(kT/C·(1 − (2/π)atan(2πf_lo RC))). MOS 가 없어 LUT 몫이 없다 -> 분해능 None 이고 수치 오차 추정은 detail.numeric_v
    (계약 10.2). 그 추정이 폐형식과의 실제 차이를 덮어야 한다. oracle (a)."""
    case = parallel_rc()
    r = noise_integral(setup_of(case, poles=ref_poles(case)))
    assert r.undefined == ()
    expect = math.sqrt(kt_over_c_from(F_LO, R * C, C))
    d = detail(r)
    assert d["mode"] == "open" and d["ktc_v2"] is None and d["f_lo_hz"] == F_LO
    claimed = r.resolution if r.resolution is not None else d["numeric_v"]
    assert abs(r.out_int_vrms - expect) <= claimed, (r.out_int_vrms, expect, claimed)


@pytest.mark.parametrize("rel_tol", [1e-2, 1e-4])
def test_diode_mos_kt_over_c_within_resolution(rel_tol):
    """다이오드 연결 MOS(gm, gds = 0) ‖ C, S_vg 열 성분 B = 4kT/gm(γ = 1): 출력 PSD = gm²B/(gm² + (ωC)²) -> 적분 = kT/C(1 − (2/π)atan(2πf_lo C/gm)).
    LUT 불확실성이 정해져 분해능이 있으면 |값 − 폐형식| ≤ 분해능(41 §7.3). oracle (a)."""
    gm = 1e-4
    case = Case(mos=(("M1", "out", "out", "gnd", "gnd", gm, 0.0),), cap=(("C", "out", "gnd", C),))
    s = setup_of(case, (dev("M1", b=4 * KT / gm, tol_thermal=0.0, tol_flicker=0.0),), rel_tol=rel_tol, poles=ref_poles(case))
    r = noise_integral(s)
    expect = math.sqrt(kt_over_c_from(F_LO, C / gm, C))
    assert r.resolution is not None and r.resolution > 0
    assert abs(r.out_int_vrms - expect) <= r.resolution
    assert r.resolution < 0.05 * expect                    # 분해능이 값보다 훨씬 작다(판정에 쓸 수 있는 크기)


def test_cs_thermal_plus_flicker_closed_form():
    """CS(입력 고정) + CL: S_out = (gm²B + gm²A/f)/(gds² + (ωCL)²). 적분 = gm²B/gds²·fp(π/2 − atan(f_lo/fp)) + (gm²A/gds²/2)·ln(1 + (fp/f_lo)²),
    fp = gds/(2πCL). oracle (a)."""
    gds = 1e-5
    case = Case(mos=(("M1", "out", "in", "gnd", "gnd", GM, gds),), cap=(("CL", "out", "gnd", CL),))
    s = setup_of(case, (dev("M1", a=A0, b=B0, ef=1.0, tol_thermal=0.0, tol_flicker=0.0),), rel_tol=1e-3, poles=ref_poles(case))
    r = noise_integral(s)
    fp = gds / (TWO_PI * CL)
    v2 = (closed_one_pole_integral(GM ** 2 * B0 / gds ** 2, fp, F_LO)
          + closed_one_pole_flicker_integral(GM ** 2 * A0 / gds ** 2, fp, F_LO))
    assert abs(r.out_int_vrms - math.sqrt(v2)) <= r.resolution
    contrib = dict(r.contrib)["M1"]
    th, fl = dict(contrib)["thermal"], dict(contrib)["flicker"]
    # 소자별 기여(계약 10.1: 규칙의 선형화로 귀속한 근사): 열·flicker 몫의 합 = 적분, 각 몫의 폐형식 오차 합은 적분 분해능을 V² 로 옮긴
    # 2·v·분해능(δI = 2v·δv, 계약 10.2) 안
    assert th + fl == pytest.approx(r.out_int_vrms ** 2, rel=1e-12)
    err = (abs(th - closed_one_pole_integral(GM ** 2 * B0 / gds ** 2, fp, F_LO))
           + abs(fl - closed_one_pole_flicker_integral(GM ** 2 * A0 / gds ** 2, fp, F_LO)))
    assert err <= 2 * r.out_int_vrms * r.resolution


def sc_amp(names=None, order=None):
    """폐루프 CS: M1 (out, in, gnd), CL(out, gnd), Cf(out, in) 되먹임, Cs(in, gnd) 입력 부하(CI-10)."""
    return Case(mos=(("M1", "out", "in", "gnd", "gnd", GM, GDS),),
                cap=(("CL", "out", "gnd", CL), ("Cf", "out", "in", CF), ("Cs", "in", "gnd", CS)), names=names, order=order)


def sc_setup(case, decl, nm=lambda x: x, rel_tol=1e-3):
    return setup_of(case, (dev(nm("M1"), b=B0, tol_thermal=0.0, tol_flicker=0.0),), decl, mode="closed", rel_tol=rel_tol,
                    poles=ref_poles(case, closed=True))


def test_closed_loop_device_noise_and_sampling_ktc():
    """폐루프 모드(feedback = (Cf,)): 소자 잡음 = 1극 적분(G = gds + gm·β, C_eff = CL + CfCs/(Cf+Cs)), 스위치 kT/C 항 = kT/Cs·|T_s|²
    (detail.ktc_v2 로 따로), 값² = 소자 + kT/C. oracle (a)+(b)."""
    case = sc_amp()
    r = noise_integral(sc_setup(case, NoiseDecl(feedback=("Cf",), sampling_caps=("Cs",))))
    assert r.undefined == ()
    d = detail(r)
    assert d["mode"] == "closed"
    beta = CF / (CF + CS)
    g_out = GDS + GM * beta
    c_eff = CL + CF * CS / (CF + CS)
    device = closed_one_pole_integral(GM ** 2 * B0 / g_out ** 2, g_out / (TWO_PI * c_eff), F_LO)
    assert d["device_v2"] == pytest.approx(device, rel=1e-4)
    t_s = case.ref_series_cap("Cs", TWO_PI * F_LO, closed=True)            # (b) 독립 노드 해석
    assert d["ktc_v2"] == pytest.approx(KT / CS * abs(t_s) ** 2, rel=1e-9)
    loop_gain = GM / GDS * beta
    assert d["ktc_v2"] == pytest.approx(KT / CS * (CS / CF) ** 2, rel=3.0 / loop_gain)   # (a) 큰 루프 이득 극한 (Cs/Cf)²
    assert r.out_int_vrms ** 2 == pytest.approx(d["device_v2"] + d["ktc_v2"], rel=1e-12)
    total = math.sqrt(device + KT / CS * abs(t_s) ** 2)
    assert abs(r.out_int_vrms - total) <= r.resolution
    ktc_rows = [kv for name, kv in r.contrib if name == "Cs"]
    assert ktc_rows and dict(ktc_rows[0])["ktc"] == pytest.approx(d["ktc_v2"], rel=1e-12)


def test_no_sampling_caps_records_none():
    r = noise_integral(sc_setup(sc_amp(), NoiseDecl(feedback=("Cf",))))
    assert detail(r)["ktc_v2"] is None
    assert r.out_int_vrms ** 2 == pytest.approx(detail(r)["device_v2"], rel=1e-12)


def test_closed_loop_name_bijection_invariance():
    """넷·소자 이름 전단사 + 노드 번호 순서 변경 -> 같은 값(구조로 정해진다). 기준 = 원래 이름 회로의 폐형식. oracle (a)."""
    names = {"in": "n7", "out": "n2", "gnd": "n0", "M1": "Mq", "CL": "C3", "Cf": "C1", "Cs": "C9"}
    a = noise_integral(sc_setup(sc_amp(), NoiseDecl(feedback=("Cf",), sampling_caps=("Cs",))))
    moved = sc_amp(names=names, order=("out", "in", "gnd"))
    b = noise_integral(sc_setup(moved, NoiseDecl(feedback=("C1",), sampling_caps=("C9",)), nm=names.get))
    assert b.undefined == ()
    assert b.out_int_vrms == pytest.approx(a.out_int_vrms, rel=1e-9)
    assert detail(b)["ktc_v2"] == pytest.approx(detail(a)["ktc_v2"], rel=1e-12)


# ---------------------------------------------------------------- 정의 불가 사유

def test_tail_not_converged_when_psd_does_not_fall():
    """저항만(커패시터 없음 -> 극점 없음): 출력 PSD 가 평탄해 꼬리 상계 f·S(f) 가 줄지 않는다 -> 값 없이 `noise_tail_not_converged`
    (꼬리 상계를 detail 에 싣는다). oracle (a) 구성 + (d) 41 §7.1 'K_max번 두 배 확장'·계약 10.1."""
    case = Case(res=(("Ra", "in", "out", 1e3), ("Rb", "out", "gnd", 1e3)))
    r = noise_integral(setup_of(case, poles=()))
    assert r.out_int_vrms is None
    assert codes(r) == ("noise_tail_not_converged",)
    info = dict(r.undefined[0].detail)
    assert info["tail_bound_v2"] > info["target_v2"]
    assert info["f_hi_hz"] > F_LO


@pytest.mark.parametrize("decl, code", [
    (NoiseDecl(feedback=None), "noise_feedback_undeclared"),
    (NoiseDecl(feedback=("Cx",)), "noise_feedback_element_unknown"),
    (NoiseDecl(feedback=("CL",)), "noise_feedback_cut_ambiguous"),          # CL(out, gnd) 은 입력 포트 단자가 없다
    (NoiseDecl(feedback=("Cf",), sampling_caps=("Cnope",)), "noise_sampling_cap_unknown"),
])
def test_closed_loop_declaration_reasons(decl, code):
    r = noise_integral(sc_setup(sc_amp(), decl))
    assert r.out_int_vrms is None and codes(r) == (code,)


def test_thermal_unknown_withholds_integral():
    s = setup_of(sc_amp(), (dev("M1", b=None),), NoiseDecl(feedback=("Cf",)), mode="closed", rel_tol=1e-3)
    r = noise_integral(s)
    assert r.out_int_vrms is None and codes(r) == ("noise_thermal_unknown",)


# ---------------------------------------------------------------- ngspice `.noise` 대조 (oracle (c) 다른 구현: ngspice-46, 엔진 import 없음)
# 같은 소신호 CS 를 두 쪽에 만든다: ngspice 는 이상 VCCS G(gm) + 게이트 직렬 저항 Rn(게이트 전류가 없어 그 열잡음 4kT·Rn 이 그대로 게이트 환산 전압 잡음) +
# 부하 RL·CL, 엔진은 MOS(gm, gds 0) + 같은 RL·CL 에 S_vg 열 성분 B = 4kT·Rn(a = 0). 입력 환산 열잡음(f_lo = 1 Hz, ngspice inoise_spectrum²)과
# [f_lo, 상한] 출력 적분(ngspice onoise_total, 상한 1e13 Hz -- 극점 1.6 MHz 위 꼬리는 무시할 크기)을 비교한다.

NGSPICE = Path(os.environ.get("GMID_NGSPICE", "C:/ngspice/Spice64/bin/ngspice_con.exe"))
NG_GM, NG_RN, NG_RL, NG_CL = 1e-3, 2.5e3, 1e5, 1e-12
DECK = """* U8 CS noise cross-check
Vin in 0 DC 0 AC 1
Rn in g {rn}
G1 out 0 g 0 {gm}
RL out 0 {rl}
CL out 0 {cl}
.options temp=27 tnom=27
.control
noise v(out) Vin dec 50 1 1e13
setplot noise1
let in1 = inoise_spectrum[0]
print in1
setplot noise2
print onoise_total
.endc
.end
"""


def _ngspice(tmp_path):
    if not NGSPICE.is_file():
        pytest.fail("ngspice 없음: %s (GMID_NGSPICE) -- 대조 test 는 skip 하지 않는다" % NGSPICE, pytrace=False)
    cir = Path(tmp_path) / "cs_noise.cir"
    cir.write_text(DECK.format(rn=NG_RN, gm=NG_GM, rl=NG_RL, cl=NG_CL), encoding="ascii")
    out = subprocess.run([str(NGSPICE), "-b", str(cir)], capture_output=True, text=True, timeout=300).stdout
    vals = dict(re.findall(r"^(in1|onoise_total)\s*=\s*([-+0-9.eE]+)", out, re.M))
    assert set(vals) == {"in1", "onoise_total"}, out
    return float(vals["in1"]) ** 2, float(vals["onoise_total"])


def test_cs_against_ngspice_noise(tmp_path):
    th_ng, v_ng = _ngspice(tmp_path)
    case = Case(mos=(("M1", "out", "in", "gnd", "gnd", NG_GM, 0.0),), res=(("RL", "out", "gnd", NG_RL),),
                cap=(("CL", "out", "gnd", NG_CL),))
    s = setup_of(case, (dev("M1", a=0.0, b=4 * KT * NG_RN, tol_thermal=0.0, tol_flicker=0.0),), rel_tol=1e-4,
                 poles=ref_poles(case))
    th = noise_analysis("th_in_v2hz", s, {}).th_in_v2hz
    v = noise_integral(s)
    # ngspice 는 7자리로 찍는다(상대 ~1e-6, 제곱 2e-6) + 볼츠만 상수 판(ngspice 내장 값 대 CODATA, 상대 1e-6 미만)
    assert th == pytest.approx(th_ng, rel=1e-5)
    # 출력 적분: 엔진 분해능 + ngspice 의 자체 적분(10년당 50점) 오차 -- 상대 1e-3 안
    assert v.out_int_vrms == pytest.approx(v_ng, rel=1e-3)

