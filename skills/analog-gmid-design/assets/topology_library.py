#!/usr/bin/env python
"""topology_library.py — 실무에서 자주 쓰는 다단 OTA 토폴로지의 `topology_fn` 모음.

`sizing_recipe.py`의 `optimize_multistage(topology_fn, luts, ...)`는 토폴로지-무관 제네릭
엔진이다 — 토폴로지마다 달라지는 건 "스펙 -> 각 스테이지 필요 gm" 위상보상 방정식뿐이고, 그
관계식만 이 파일에 `topology_fn` 팩토리 함수로 모아둔다. 실무는 매번 새 토폴로지를 설계하지
않고 검증된 강건한 토폴로지(Miller 2단, RHP-zero-free 3단, NGCC 3단 등)를 스펙에 맞게
sizing해서 쓰는 경우가 대부분이라, 이 라이브러리는 시간이 지나며 항목을 늘려가는 구조로 만든다.

각 `topology_fn(prev_cggs) -> list[gm_i]`는 `optimize_multistage`가 반복마다 호출한다:
    prev_cggs=None(첫 반복)이면 스스로 초기 기생커패시턴스 추정치를 쓰고, 이후 반복에서는
    직전 반복에서 얻은 각 스테이지의 실제 Cgg 리스트를 받아 더 정확한 gm을 낼 수 있다(Miller
    OTA처럼 위상보상 방정식 자체가 다음 단 게이트 커패시턴스에 의존하는 경우). 반대로 위상보상
    방정식이 노드 커패시턴스에 의존하지 않는 토폴로지(NMCNR, NGCC — 아래 참고)는 prev_cggs를
    무시하고 매 반복 동일한 gm을 반환해도 무방하다 — optimize_multistage는 두 경우 모두 그대로
    수렴 판정(gm 변화량 < tol)을 적용하므로 엔진 수정 없이 동작한다.

각 함수 docstring은 "무엇을 검증했고 무엇이 근사인가"라는 결론만 짧게 남긴다. 그 결론에 이르는
**유도 과정**(어느 원문 방정식을 어떻게 대입/소거해서 이 gm 식이 나왔는지, 새 토폴로지를 추가할
때 따라야 할 절차)은 ../references/topology-fn-derivation-guide.md에 있다 — **새 topology_fn을
추가하기 전에 그 문서를 먼저 읽을 것.** 방법론 원문 근거: ../references/gm-id-methodology.md
§6.4, §10.2, §10.4.
"""
from __future__ import annotations
import math


# ---------------------------------------------------------------------------
# 1) Miller 2단 OTA — §6.4/§10.2, 완전 검증됨(원문 Eq 8.13/8.14/8.15와 대조 확인)
# ---------------------------------------------------------------------------

def miller_ota_topology(GBW: float, CL: float, Z: float = 10.0, NDP: float = 4.0):
    """2단 Miller OTA(방법론 §6.4) 위상보상 방정식 — optimize_multistage()의 topology_fn 팩토리.

    완전 결정 케이스(자유도 없음) — 유도 과정은 topology-fn-derivation-guide.md §2 참고.
    검증 상태: 원문 수식(Eq 8.13/8.14/8.15) 대조 완료. 실측 sky130 LUT로 gm1=0.3047mS/
    gm2=3.0471mS 재현 확인(sky130-worked-example.md §11 참고).
    """
    wT = 2 * math.pi * GBW

    def topology_fn(prev_cggs):
        if prev_cggs is None:
            C1, C2 = CL * 0.1, CL  # 초기 추정("Cm 초기추정(예 0.5*C)"와 같은 자리)
        else:
            C1, C2 = prev_cggs[1], CL
        Cm = (NDP / Z) * (C1 + C2 + math.sqrt((C1 + C2) ** 2 + 4 * C1 * C2 * Z / NDP))
        gm1 = wT * Cm
        gm2 = Z * gm1
        return [gm1, gm2]

    return topology_fn


# ---------------------------------------------------------------------------
# 2) NMCNR 3단(RHP-zero 완전제거) — §10.4, Leung/Mok/Ki(IEEE 1999). 실무에서 자주 쓰이는
#    "강건한" 3단 보상 구조(nested-Miller 계열의 RHP-zero 문제를 능동소자로 제거) — Eq 6~11
#    전체를 원문 이미지로 직접 대조 검증함. kg(=gm2/gm3)는 원문 자체가 추가 결정식 없이 남겨둔
#    자유도임을 원문에서 확인(재구성 실패가 아니라 확정된 사실).
# ---------------------------------------------------------------------------

def nmcnr_3stage_topology(GBW: float, CL: float, PM_target_deg: float = 65.0, kg: float = 0.5):
    """3단 NMCNR(방법론 §10.4, Leung/Mok/Ki) 위상보상 방정식 — RHP-zero 완전제거 구조.

    gm3 소거 케이스(gm1, gm3는 완전 결정 / kg는 원문이 확정한 자유도) — 유도 과정과 원문
    이미지 판독 근거는 topology-fn-derivation-guide.md §3 참고.

    ⚠️ kg=gm2/gm3는 GBW/PM 헤드라인 식(Eq 10/11)에 나타나지 않는다 — 원문을 이미지로 직접
    확인한 결과, 이건 "찾지 못한 결정식"이 아니라 **원문 자체가 kg에 추가 결정식을 주지 않고
    설계자 자유도로 남긴 것**이다(Cm2 식에만 등장하고 GBW/PM엔 영향 없음). 기본값 0.5는
    Cm2>0 조건(kg<1)만 만족하는 임의값이니, 실제 설계에는 SPICE로 PM/GBW를 재확인할 것.

    ⚠️⚠️ **Eq 10/11이 GBW/PM을 정확히 예측한다는 보장이 없다 — 반드시 사이징 후
    `nmcnr_predict_notch()`로 재검증할 것.** Eq 10/11은 "우세극이 나머지 극점들과 충분히
    떨어져 있다"는 근사 위에서 유도된 식이라, 스테이지2 자신의 고유이득(Av2=gm2·R2, R2는
    사이징 후 실제 출력저항)이 어떤 문턱을 넘으면(실측 사례는 sky130-worked-example.md
    §12.7.4 참고, Av1≈Av3≈24 스펙에서 임계값≈5.1) 이 근사가 무너져 **개루프 응답에 노치
    (0dB 재교차)가 생기고, 실제 GBW/PM이 이 함수가 계산한 값과 크게 달라진다**(sky130
    실측 사례: 목표 GBW=5MHz/PM=70°였는데 실제 1.66MHz/62.0° + 노치, §12.4~§12.7 전체가
    이 발견의 기록). Eq 10/11 자체가 틀린 게 아니라 이 근사의 **적용 가능 조건**이 있다는
    뜻 — `nmcnr_predict_notch()`가 그 조건(근사 없이 정확한 3-노드 전달함수)을 직접 계산해
    검증해준다. 진단 절차 전체는 ../references/topology-behavior-diagnosis-workflow.md 참고.

    검증 상태: Eq 6~11 전체 원문 이미지 대조 검증 완료. kg는 원문이 확정한 자유도(수치 예제 없음).
    """
    wGBW = 2 * math.pi * GBW
    gm3 = 4 * wGBW * CL
    pm_rad = math.radians(PM_target_deg - 60.0)
    if pm_rad <= 0:
        raise ValueError("PM_target_deg는 60도보다 커야 한다(NMCNR 구조상 PM>60도 보장)")
    gm1 = gm3 / math.tan(pm_rad)
    gm2 = kg * gm3

    def topology_fn(prev_cggs):
        return [gm1, gm2, gm3]

    return topology_fn


def nmcnr_compensation_elements(gm1: float, gm2: float, gm3: float, CL: float, kg: float):
    """NMCNR 보상소자 실값(Cm1, Rm, Cm2) — 원문 Eq 8/9. 실제 SPICE/레이아웃에 넣을 값이다.

    `nmcnr_3stage_topology()`는 gm1/gm2/gm3(목표)만 반환하고 보상소자 값 자체는 반환하지
    않는다 — 사이징 완료 후 실제 회로를 조립하거나 `nmcnr_predict_notch()`로 검증할 때
    이 함수로 Cm1/Rm/Cm2를 구한다(직접 대입하지 말고 항상 이 함수를 통해서 — Eq 8/9를
    실수로 잘못 옮겨적는 걸 방지).

    검증 상태: Eq 8/9 원문 이미지 대조 검증 완료(topology-fn-derivation-guide.md §3).
    """
    Cm1 = 4 * (gm1 / gm3) * CL       # Eq 8
    Rm = 1 / gm3                      # 본문(RHP-zero 완전제거 조건)
    Cm2 = (2 / (1 - kg)) * (gm2 / gm3) * CL  # Eq 9
    return Cm1, Rm, Cm2


def nmcnr_predict_notch(gm1: float, gm2: float, gm3: float, R1: float, R2: float, R3: float,
                         CL: float, kg: float, f_start: float = 1.0, f_stop: float = 1e9,
                         n_points: int = 2000) -> dict:
    """사이징 완료 후 실제 GBW/PM/노치 여부를 검증 — Eq 10/11의 근사 없이 3-노드 KCL을 정확히
    풀어 계산한다(sky130-worked-example.md §12.7.3의 유도를 그대로 코드화한 것 — **다시 유도할
    필요 없이 이 함수를 그대로 쓸 것**).

    입력: gm1/gm2/gm3(목표 gm, `nmcnr_3stage_topology()`가 반환한 값), R1/R2/R3(각 스테이지
    **실제 사이징 결과**의 출력저항 = gain_i/gm_i, 즉 `find_optimal_sizing()`/`optimize_multistage()`
    결과의 `gain` 필드를 gm_i로 나눈 값), CL, kg.

    반환: dict(crossings=[(f_Hz, PM_deg), ...] 0dB 교차 전부, notch=bool(교차 2개 이상이면 True),
    dc_gain_db=float). `notch=True`면 Eq 10/11이 예측한 GBW/PM을 믿지 말고 실제 SPICE로
    재확인할 것 — 이 함수 자체도 이상화(VCCS+ro, 실소자 기생 없음) 모델이라 최종 확인은 항상
    SPICE다(방법론 문서 §4.5 원칙 그대로).

    ⚠️ 정확도: gm1/gm2/gm3 근처의 "전형적인"(스테이지 고유이득이 극단적으로 낮지 않은) 동작점에서는
    실측 sky130 SPICE와 주파수 <10%, PM 수 도 이내로 일치했다(§12.7.2/§12.7.4 교차검증). 다만
    스테이지 고유이득을 의도적으로 아주 낮게(예 <5) 만든 극단적 사이징에서는 이 함수의 DC 이득
    예측(gm1·R1·gm2·R2·gm3·R3 기반)이 실측과 수십 dB까지 벌어질 수 있다(LUT가 그 영역에서 덜
    정확하거나, 실소자의 다른 비이상성이 커지기 때문으로 추정 — 완전히 규명되지 않음, 정직한 한계).
    극단적 동작점을 다룰 땐 이 함수의 예측을 정성적 신호(노치 유무)로만 쓰고, 정량값(GBW/PM/DC이득)은
    반드시 SPICE로 재확인할 것.

    검증 상태: kg=0.5(§12.4)·kg=0.1(§12.6) 실측 SPICE와 대조 검증 완료. 정확한 유도 과정은
    topology-behavior-diagnosis-workflow.md §4, sky130-worked-example.md §12.7.3 참고.
    """
    Cm1, Rm, Cm2 = nmcnr_compensation_elements(gm1, gm2, gm3, CL, kg)

    # 3-노드(V1,V2,Vout) KCL을 근사 없이 직접 푼 정확한 전달함수(분자 2차/분모 3차) 계수.
    # 유도: topology-behavior-diagnosis-workflow.md §4, sky130-worked-example.md §12.7.3.
    num = [
        Cm1 * Cm2 * R1 * R3 * gm1 * (-R2 - Rm),
        R1 * R3 * gm1 * (-Cm1 - Cm2 * R2 * Rm * gm2 * gm3 + Cm2 * R2 * gm2),
        -R1 * R2 * R3 * gm1 * gm2 * gm3,
    ]
    den = [
        CL * Cm1 * Cm2 * R1 * R3 * (R2 + Rm),
        CL * Cm1 * R1 * R3 + CL * Cm2 * R2 * R3 + CL * Cm2 * R3 * Rm
        - Cm1 * Cm2 * R1 * R2 * R3 * Rm * gm2 * gm3 + Cm1 * Cm2 * R1 * R2 * R3 * gm2
        + Cm1 * Cm2 * R1 * R2 * R3 * gm3 + Cm1 * Cm2 * R1 * R2 + Cm1 * Cm2 * R1 * R3
        + Cm1 * Cm2 * R1 * Rm + Cm1 * Cm2 * R2 * R3 + Cm1 * Cm2 * R3 * Rm,
        CL * R3 - Cm1 * R1 * R2 * R3 * gm2 * gm3 + Cm1 * R1 + Cm1 * R3
        + Cm2 * R2 * R3 * gm3 + Cm2 * R2 + Cm2 * R3 + Cm2 * Rm,
        1.0,
    ]

    def _H(w):
        s = 1j * w
        n = num[0] * s ** 2 + num[1] * s + num[2]
        d = den[0] * s ** 3 + den[1] * s ** 2 + den[2] * s + den[3]
        return n / d

    freqs = [f_start * (f_stop / f_start) ** (i / (n_points - 1)) for i in range(n_points)]
    Hs = [_H(2 * math.pi * f) for f in freqs]
    mags = [abs(h) for h in Hs]
    phases = []
    prev = None
    for h in Hs:
        p = math.degrees(math.atan2(h.imag, h.real))
        if prev is not None:
            while p - prev > 180:
                p -= 360
            while p - prev < -180:
                p += 360
        phases.append(p)
        prev = p
    dc_phase = phases[0]
    dc_gain_db = 20 * math.log10(mags[0])

    crossings = []
    for i in range(len(mags) - 1):
        if mags[i] >= 1 and mags[i + 1] < 1:
            frac = (0 - math.log10(mags[i])) / (math.log10(mags[i + 1]) - math.log10(mags[i]))
            f_c = freqs[i] * (freqs[i + 1] / freqs[i]) ** frac
            p_c = phases[i] + frac * (phases[i + 1] - phases[i])
            pm = 180 - abs(p_c - dc_phase)
            crossings.append((f_c, pm))

    return dict(crossings=crossings, notch=len(crossings) > 1, dc_gain_db=dc_gain_db)


# ---------------------------------------------------------------------------
# 3) NGCC 3단(Nested Gm-C Compensation) — §10.2, Lee et al. square-law 기반 논문이라 gm/ID
#    엄밀 적용은 아니지만(§10.2 caveat 참고), 위상보상 위치/구조 자체는 gm/ID로도 그대로 쓸 수
#    있는 실무 토폴로지다. gm3, gm1, gm2 전부 원문 Eq 8.a/8.b로 완전 결정됨(원문 이미지 직접
#    판독으로 확인 — 이전에 "OCR 손상으로 재현 불가"였던 자유도가 이번에 해소됐다).
# ---------------------------------------------------------------------------

def ngcc_3stage_topology(GB: float, k: float, CL: float, alpha: float, mu_ratio: float = None):
    """3단 NGCC(방법론 §10.2, Lee et al.) 위상보상 방정식 — Eq 8.a/8.b로 gm1,gm2 완전 결정.

    완전 결정 케이스(mu_ratio만 알면 gm1,gm2,gm3 전부 유일해) — 유도 과정과 원문 이미지 판독
    근거는 topology-fn-derivation-guide.md §4 참고.

    mu_ratio = μn/μp(해당 공정의 NMOS/PMOS 이동도 비) — 이건 설계 자유도가 아니라 **공정
    파라미터**다(BSIM UO_n/UO_p 비 등으로 구할 수 있다). 기본값(3.9775)은 원 논문 0.18um
    공정 예제(Table 4)를 Eq 8.a/8.b 양쪽에서 역산해 얻은 값 — 자신의 공정이면 반드시 실제
    μn/μp로 교체할 것.

    검증 상태: gm3/gm1/gm2/선형 제약식 모두 원문 Table 4 수치와 대조 검증 완료(gm1=0.105mS,
    gm2=0.186mS 재현). 남은 근사는 mu_ratio 기본값(원 논문 특정 공정 예제에서 역산한 값)뿐.
    """
    w1 = 2 * math.pi * GB
    w3 = k * w1
    gm3 = w3 * CL
    r = mu_ratio if mu_ratio is not None else 3.9775  # mu_n/mu_p, 원 논문 0.18um 예제 역산값
    gm1 = alpha * (1 + 2 * k) ** 2 / (k * (r * k ** 2 + (1 + 2 * k) ** 2)) * gm3   # Eq 8.a
    gm2 = alpha * (1 + 2 * k) / (k ** 2 + (1 + 2 * k) ** 2 / r) * gm3              # Eq 8.b

    def topology_fn(prev_cggs):
        return [gm1, gm2, gm3]

    return topology_fn


# ---------------------------------------------------------------------------
# 4) 사용 예시 — 각 토폴로지의 gm 산출만 확인(실제 sizing은 sizing_recipe.optimize_multistage
#    + real LUT 필요). 원문 수치 예제와의 교차검증 포함.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    print("# Miller 2단 OTA (GBW=20MHz, CL=3pF, Z=10, NDP=4) — prev_cggs=None(초기 반복) 기준")
    tf = miller_ota_topology(GBW=20e6, CL=3e-12, Z=10.0, NDP=4.0)
    gm1, gm2 = tf(None)
    print(f"  gm1={gm1*1e3:.4f}mS  gm2={gm2*1e3:.4f}mS")

    print("# NMCNR 3단 (GBW=5MHz, CL=10pF, PM_target=70deg, kg=0.5)")
    tf2 = nmcnr_3stage_topology(GBW=5e6, CL=10e-12, PM_target_deg=70.0, kg=0.5)
    gm1n, gm2n, gm3n = tf2(None)
    print(f"  gm1={gm1n*1e3:.4f}mS  gm2={gm2n*1e3:.4f}mS  gm3={gm3n*1e3:.4f}mS")

    print("# nmcnr_predict_notch() 스모크 테스트 — sky130-worked-example.md §12.4 실측치로 대조")
    Cm1, Rm, Cm2 = nmcnr_compensation_elements(gm1n, gm2n, gm3n, CL=10e-12, kg=0.5)
    print(f"  Cm1={Cm1*1e12:.3f}pF  Rm={Rm:.2f}ohm  Cm2={Cm2*1e12:.3f}pF")
    # R1/R2/R3 = 실측(§12.4) stage1/2/3 gain을 각 gm으로 나눈 값(gain=24.69/56.67/24.21)
    R1, R2, R3 = 24.69 / gm1n, 56.67 / gm2n, 24.21 / gm3n
    result = nmcnr_predict_notch(gm1n, gm2n, gm3n, R1, R2, R3, CL=10e-12, kg=0.5)
    print(f"  notch={result['notch']}  dc_gain={result['dc_gain_db']:.1f}dB")
    for f_c, pm in result["crossings"]:
        print(f"    교차: f={f_c/1e6:.3f}MHz  PM={pm:.1f}deg")
    print("  (실측 SPICE §12.4: GBW=1.66MHz/PM=62.0deg, 2차교차 102.7MHz/PM=-102.3deg, notch=True)")

    print("# NGCC 3단 (Lee et al. Table 4 예제: k=4, GB=10MHz, CL=10pF, alpha=0.3) — 전체 재현")
    tf3 = ngcc_3stage_topology(GB=10e6, k=4.0, CL=10e-12, alpha=0.3)
    gm1c, gm2c, gm3c = tf3(None)
    print(f"  gm1={gm1c*1e3:.4f}mS  gm2={gm2c*1e3:.4f}mS  gm3={gm3c*1e3:.4f}mS  "
          f"(원문 Table 4: gm1=0.105mS gm2=0.186mS gm3=2.5mS)")
