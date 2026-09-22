# extract_selftest: tools/migrate/extract_selftest.py 로 생성했다(사람이 고치지 마라).
# 원본 경로: C:\Users\HSLEE\Documents\Todoc\fpga\wt\20260922-ts1-legacy-move-test\skills\analog-gmid-design\assets\topology_library.py
# 원본 blob id: 73325a330f1e15dcb40e76bf7a3b5c918b51b6a0
import os
import sys
_ASSETS_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, _ASSETS_DIR)
from topology_library import (current_reuse_telescopic_topology, math, miller_ota_topology, ngcc_3stage_topology, nmcnr_3stage_topology, nmcnr_check_dominant_pole_approximation, nmcnr_compensation_elements, nmcnr_predict_ac_response)

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


    print("# NMCNR 3단 (GBW=5MHz, CL=10pF, PM_target=70deg, kg=0.5)")
    tf2 = nmcnr_3stage_topology(GBW=5e6, CL=10e-12, PM_target_deg=70.0, kg=0.5)
    gm1n, gm2n, gm3n = tf2(None)
    print(f"  gm1={gm1n*1e3:.4f}mS  gm2={gm2n*1e3:.4f}mS  gm3={gm3n*1e3:.4f}mS")
    assert hasattr(tf2, "dominant_pole_check"), \
        "topology_fn.dominant_pole_check가 배선 안 됨(★절대원칙★ 위반 -- 만들고 안 씀)"
    print(f"  dominant_pole_check: valid={tf2.dominant_pole_check['valid']} "
          f"(gbw_ratio={tf2.dominant_pole_check['gbw_ratio']:.2f}배, "
          f"pm_diff={tf2.dominant_pole_check['pm_diff_deg']:+.1f}deg -- PM_target=70도는 "
          f"물리적으로 타당한 구간이라 valid=False가 기대값)")
    assert tf2.dominant_pole_check["valid"] is False


    print("# nmcnr_predict_ac_response() 독립 재유도 회귀 검증(2026-08-19 세션37 연속) —")
    print("  docstring이 명시한 4-노드 KCL 방정식을 sympy로 처음부터 다시 풀어 하드코딩된")
    print("  num/den 계수와 항별로 정확히 일치하는지 확인(대수 오류가 없다는 영구 회귀 가드)")
    import sympy as _sp
    _s, _gm1, _gm2, _gm3, _R1, _R2, _R3, _Cm1, _Cm2, _Rm, _CL, _Vin = _sp.symbols(
        "s gm1 gm2 gm3 R1 R2 R3 Cm1 Cm2 Rm CL Vin")
    _V1, _V2, _Vcm, _Vout = _sp.symbols("V1 V2 Vcm Vout")
    _eqs = [
        _sp.Eq(-_gm1 * _Vin, _V1 / _R1 + _s * _Cm1 * (_V1 - _Vcm)),
        _sp.Eq(_gm2 * _V1, _V2 / _R2 + _s * _Cm2 * (_V2 - _Vcm)),
        _sp.Eq(_s * _Cm1 * (_V1 - _Vcm) + _s * _Cm2 * (_V2 - _Vcm), (_Vcm - _Vout) / _Rm),
        _sp.Eq(-_gm3 * _V2 + (_Vcm - _Vout) / _Rm, _Vout / _R3 + _s * _CL * _Vout),
    ]
    _sol = _sp.solve(_eqs, [_V1, _V2, _Vcm, _Vout], dict=True)[0]
    _H = _sp.together(_sp.simplify(_sol[_Vout] / _Vin))
    _num_sym, _den_sym = _sp.fraction(_H)
    _my_num = _sp.Poly(_sp.expand(_num_sym), _s).all_coeffs()
    _my_den = _sp.Poly(_sp.expand(_den_sym), _s).all_coeffs()
    _hard_num = [
        _Cm1 * _Cm2 * _R1 * _R2 * _R3 * _gm1 * (_Rm * _gm3 - 1),
        _R1 * _R3 * _gm1 * (_Cm1 * _R2 * _Rm * _gm2 * _gm3 - _Cm1
                             + _Cm2 * _R2 * _Rm * _gm2 * _gm3 - _Cm2 * _R2 * _gm2),
        _R1 * _R2 * _R3 * _gm1 * _gm2 * _gm3,
    ]
    _hard_den = [
        _CL * _Cm1 * _Cm2 * _R3 * (-_R1 * _R2 * _Rm * _gm2 + _R1 * _R2 + _R1 * _Rm + _R2 * _Rm),
        _CL * _Cm1 * _R1 * _R3 + _CL * _Cm1 * _R3 * _Rm + _CL * _Cm2 * _R2 * _R3
        + _CL * _Cm2 * _R3 * _Rm - _Cm1 * _Cm2 * _R1 * _R2 * _R3 * _gm2
        + _Cm1 * _Cm2 * _R1 * _R2 * _R3 * _gm3 - _Cm1 * _Cm2 * _R1 * _R2 * _Rm * _gm2
        + _Cm1 * _Cm2 * _R1 * _R2 + _Cm1 * _Cm2 * _R1 * _R3 + _Cm1 * _Cm2 * _R1 * _Rm
        + _Cm1 * _Cm2 * _R2 * _R3 + _Cm1 * _Cm2 * _R2 * _Rm,
        _CL * _R3 + _Cm1 * _R1 * _R2 * _R3 * _gm2 * _gm3 + _Cm1 * _R1 + _Cm1 * _R3 + _Cm1 * _Rm
        + _Cm2 * _R2 * _R3 * _gm3 + _Cm2 * _R2 + _Cm2 * _R3 + _Cm2 * _Rm,
        _sp.Integer(1),
    ]
    _num_diffs = [_sp.simplify(a - b) for a, b in zip(_my_num, _hard_num)]
    _den_diffs = [_sp.simplify(a - b) for a, b in zip(_my_den, _hard_den)]
    assert all(d == 0 for d in _num_diffs), f"num 계수가 재유도와 다름: {_num_diffs}"
    assert all(d == 0 for d in _den_diffs), f"den 계수가 재유도와 다름: {_den_diffs}"

    _diag_bad = nmcnr_check_dominant_pole_approximation(GBW=816000.0, CL=1e-10, PM_target_deg=70.0, kg=0.5)
    print(f"  [nmcnr_amplifier 실제 스펙: GBW=816kHz/CL=1e-10F/PM_target=70도/kg=0.5]")
    print(f"    Eq10/11 예측: GBW={_diag_bad['eq10_gbw_hz']/1e3:.1f}kHz  PM={_diag_bad['eq11_pm_deg']:.1f}deg")
    print(f"    R->무한대 정확해: GBW={_diag_bad['exact_ideal_gbw_hz']/1e6:.3f}MHz  "
          f"PM={_diag_bad['exact_ideal_pm_deg']:.1f}deg")
    print(f"    gbw_ratio={_diag_bad['gbw_ratio']:.2f}배  pm_diff={_diag_bad['pm_diff_deg']:+.1f}deg  "
          f"valid={_diag_bad['valid']}")
    assert _diag_bad["valid"] is False, "이미 실측으로 확인된 위반 사례인데 valid=True로 나옴(회귀)"

    print("  [GBW/CL/kg 불변성 -- gbw_ratio/pm_diff가 PM_target_deg에만 의존하고 GBW/CL/kg와는")
    print("  완전히 무관함을 확인(sympy 인수분해로도 확인: R->무한대 극한에서 (kg-1) 인자가")
    print("  분자/분모에서 정확히 소거돼 H(s) 자체가 kg와 무관해진다)]")
    _diag_gbw2 = nmcnr_check_dominant_pole_approximation(GBW=50e3, CL=1e-10, PM_target_deg=70.0, kg=0.5)
    _diag_cl2 = nmcnr_check_dominant_pole_approximation(GBW=816e3, CL=1e-8, PM_target_deg=70.0, kg=0.5)
    _diag_kg2 = nmcnr_check_dominant_pole_approximation(GBW=816e3, CL=1e-10, PM_target_deg=70.0, kg=0.9)
    for _label, _d in [("GBW 16배 축소", _diag_gbw2), ("CL 100배 확대", _diag_cl2), ("kg=0.9", _diag_kg2)]:
        assert abs(_d["gbw_ratio"] - _diag_bad["gbw_ratio"]) < 1e-5, f"{_label}: gbw_ratio가 달라짐"
        # 1e-2도 오차 허용 -- log-스페이스 주파수 격자(n_points=4000)가 스케일마다 크로스오버를
        # 살짝 다른 지점에서 보간해서 생기는 수치 잡음(실측: 최대 0.006도), 물리적 차이 아님.
        assert abs(_d["pm_diff_deg"] - _diag_bad["pm_diff_deg"]) < 1e-2, f"{_label}: pm_diff가 달라짐"

    print("  [PM_target_deg만 바꿔가며 valid=True가 되는 지점 탐색 -- 물리적으로 타당한 60~90도")
    print("  구간 전체에서 근사가 깨져 있고(ratio 2.5~21배, pm_diff +40~+72도, 전부 valid=False),")
    print("  150도(=tan 특이점) 근처의 비현실적 극단값에서만 valid=True가 됨을 확인]")
    for _pm in (70.0, 90.0, 120.0):
        _d = nmcnr_check_dominant_pole_approximation(GBW=816e3, CL=1e-10, PM_target_deg=_pm, kg=0.5)
        assert _d["valid"] is False, f"PM_target={_pm}도가 물리적으로 타당한 구간인데 valid=True로 나옴"
    _diag_edge = nmcnr_check_dominant_pole_approximation(GBW=816e3, CL=1e-10, PM_target_deg=149.0, kg=0.5)
    assert _diag_edge["valid"] is True, "149도(비현실적 극단값)에서도 valid=False -- 근사가 절대 안 맞는지 재확인 필요"

    tf4 = current_reuse_telescopic_topology(t_lln=30e-9, PM_target_deg=70.0, Cc=500e-15,
                                              Cf=500e-15, Cs=500e-15, C_Ltot=1e-12)

    print("  [Eq.6 ratio=tan(PM_target) -- 원문 수치 예제(PM=70도->2.8)와 검산]")
    _ratio_expected = math.tan(math.radians(70.0))
    print(f"    tan(70deg)={_ratio_expected:.4f} (원문 명시값 2.8과 일치)")
    assert abs(_ratio_expected - 2.8) < 0.06, "원문 수치 예제(2.8)와 너무 다름"

    print("  [Eq.4/5 cold-start(prev_cggs=None) -- Cgg1=0 가정, beta=0.5 정확히, gmp=gmn=gm1/2]")
    gmp_cold, gmn_cold, gmp2_cold, gmn2_cold = tf4(None)
    _beta_cold_expected = 500e-15 / (500e-15 + 500e-15 + 0.0)
    _gm1_cold_expected = (6.9 / 30e-9) * 500e-15 / _beta_cold_expected
    assert abs(gmp_cold - _gm1_cold_expected / 2) / (_gm1_cold_expected / 2) < 1e-9
    assert gmp_cold == gmn_cold, "gmn=gmp 가정(Eq.5)이 깨짐"
    print(f"    beta=0.5(Cgg1=0 초기추정) -> gmp=gmn={gmp_cold*1e6:.2f}uS(합=gm1={gmp_cold*2*1e6:.2f}uS) "
          f"(원문의 beta=0.48 고정 근사와 달리 이 함수는 Cgg1=0에서 출발해 반복 수렴)")

    print("  [Eq.4 -- Cgg1_total(M1a+M4a 합)을 명시적으로 주면 beta/gmp/gmn이 그만큼 변함]")
    gmp_fed, gmn_fed, gmp2_fed, gmn2_fed = tf4([30e-15, 20e-15, 300e-15, 200e-15])
    # M1a Cgg=30fF, M4a Cgg=20fF, M15(PMOS) Cgg=300fF, M16(NMOS) Cgg=200fF 가정
    _beta_fed_expected = 500e-15 / (500e-15 + 500e-15 + 50e-15)
    _gm1_fed_expected = (6.9 / 30e-9) * 500e-15 / _beta_fed_expected
    assert abs(gmp_fed - _gm1_fed_expected / 2) / (_gm1_fed_expected / 2) < 1e-9
    assert gmp_fed > gmp_cold, "Cgg1_total이 커졌는데 beta 감소->gm1 증가라는 관계가 깨짐"
    print(f"    Cgg1_total=30fF+20fF=50fF -> beta={_beta_fed_expected:.4f}, "
          f"gmp=gmn={gmp_fed*1e6:.2f}uS (Cgg1=0일 때보다 커짐 확인)")

    print("  [세션30 -- gm2가 gmp2/gmn2로 분리되고 항상 gmp2=gmn2=gm2/2(50:50 기본값)임을 확인]")
    assert gmp2_cold == gmn2_cold, "gmp2=gmn2(50:50 기본값)이 깨짐"
    assert gmp2_fed == gmn2_fed, "gmp2=gmn2(50:50 기본값)이 깨짐(Cgg 반영 후)"
    print(f"    gmp2=gmn2={gmp2_cold*1e3:.4f}mS(cold) -> {gmp2_fed*1e3:.4f}mS(Cgg2=300f+200f=500fF 반영) "
          f"(합=gm2, Eq.6과 동일 스케일 -- 분할 자체는 50:50, 실제 L 독립화는 topology.json의 "
          f"L_stage2out_p/L_stage2out_n theta가 담당)")

    print("  [Eq.6 -- Cgg2(prev_cggs[2]+prev_cggs[3])를 키우면 gm2(=gmp2+gmn2)도 커짐(단조성)]")
    _gm2_cold, _gm2_fed = gmp2_cold + gmn2_cold, gmp2_fed + gmn2_fed
    assert _gm2_fed > _gm2_cold or abs(_gm2_fed - _gm2_cold) < 1e-15, "Cgg2 반영 확인"
    print(f"    gm2(Cgg2=1pF*0.1 초기추정)={_gm2_cold*1e3:.4f}mS, "
          f"gm2(Cgg2=500fF 명시)={_gm2_fed*1e3:.4f}mS")
    print("  참고: 원문의 beta=0.48/gm1=238uS는 실제 M1a/M4a 사이징에서 나온 Cgg1을 반복")
    print("  수렴시켜야 재현 여부를 알 수 있다(sizing_recipe.py의 optimize_multistage() 통합")
    print("  테스트 참고) -- 이 파일은 topology_fn 자체의 식(Eq.2-6)만 검증한다.")
