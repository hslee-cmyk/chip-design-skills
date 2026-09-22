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
import functools
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

    ⚠️ **Eq 10/11은 "우세극이 나머지 극점들과 충분히 떨어져 있다"는 근사 위에서 유도된 식이다**
    — 정확한 GBW/PM은 사이징 후 `nmcnr_predict_ac_response()`(근사 없는 정확한 4-노드 전달함수)로
    재확인할 것. 한때(2026-07-31 이전) 보상망 배선을 잘못 조립한 채로 "이 근사가 무너져 개루프
    응답에 노치가 생긴다"는 사례를 발견했다고 기록했으나, 배선 오류(Cm1/Cm2가 실제로는 한
    노드에서 만나 Rm 하나를 공유하는데 각각 독립 경로로 잘못 조립함)를 바로잡고 같은 동작점을
    재검증하니 **노치가 없었다** — 그 사례 자체가 무효였다(sky130-worked-example.md §12.3
    참고). `nmcnr_predict_ac_response()`는 여전히 유효한 검증 도구이므로 계속 사용할 것 — 다만
    "노치가 흔하다"는 인상은 정정 전 잘못된 조사에서 온 것이니 새 회로에서 노치 유무를 실제로
    확인하기 전까지 가정하지 말 것.

    ⚠️⚠️ **(2026-08-19 세션37 연속) Eq10/11 근사는 물리적으로 타당한 PM_target(60~90도)
    전 구간에서 사실상 항상 깨져 있다는 게 `nmcnr_check_dominant_pole_approximation()`으로
    정량 확인됐다** — GBW·CL·kg와 무관하게(대수적으로 완전히 소거됨) PM_target_deg 하나에만
    좌우되며, 60~90도 구간에서 "이상화된(R→무한대) 정확해" 기준 GBW가 Eq10 예측보다 2.5~21배
    높고 PM은 +40~+72도 더 나온다(비현실적인 149도 근처에서만 근사가 성립). 이 함수가 반환하는
    gm1/gm2/gm3로 실제 사이징하면, `PM_target_deg`로 지정한 값을 그대로 믿지 말고 **반드시**
    `nmcnr_predict_ac_response()`(또는 사이징 전 스크리닝용으로 `nmcnr_check_dominant_pole_
    approximation(GBW, CL, PM_target_deg, kg)`)로 실제 PM을 재확인할 것 — 이 함수 자체는
    Eq10/11의 검증 상태(아래)와 무관하게 **원문 수식을 그대로 구현**해 반환하므로(원문 대조는
    이미 완료됨, 문제는 원문 수식 자체의 근사 정확도), 이 경고와 별개로 계속 동작한다. 아래
    `topology_fn.dominant_pole_check`(호출 시 자동 계산, `nmcnr_check_dominant_pole_
    approximation()`의 반환값 그대로)로 이 특정 스펙의 위반 정도를 바로 확인할 수 있다.

    검증 상태: Eq 6~11 전체 원문 이미지 대조 검증 완료. kg는 원문이 확정한 자유도(수치 예제 없음).
    Eq10/11 자체의 근사 정확도는 위 경고 참고(원문 전사는 맞지만 근사가 실전에서 잘 안 맞음).
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

    # 2026-08-19(세션37 연속) -- ngcc_3stage_topology()의 topology_fn.stage_fT_targets와
    # 동일 관례로 진단 결과를 반환 함수에 매달아둔다(★절대원칙★ "만들면 반드시 배선하라" --
    # nmcnr_check_dominant_pole_approximation()을 만들고 끝내지 않고, 이 실제 진입점에서
    # 항상 자동으로 계산되게 배선함). 계산 비용(주파수 스윕 4000점)이 작지 않아 호출자가
    # 필요할 때만 보게 지연 평가하고 싶을 수 있으나, optimize_multistage()가 topology_fn을
    # 반복 호출하는 빈도(회로당 수 회)를 감안하면 매번 재계산해도 실사용에 문제없는 비용이라
    # 단순하게 즉시 계산해 붙인다.
    topology_fn.dominant_pole_check = nmcnr_check_dominant_pole_approximation(GBW, CL, PM_target_deg, kg)
    return topology_fn


def nmcnr_compensation_elements(gm1: float, gm2: float, gm3: float, CL: float, kg: float):
    """NMCNR 보상소자 실값(Cm1, Rm, Cm2) — 원문 Eq 8/9. 실제 SPICE/레이아웃에 넣을 값이다.

    `nmcnr_3stage_topology()`는 gm1/gm2/gm3(목표)만 반환하고 보상소자 값 자체는 반환하지
    않는다 — 사이징 완료 후 실제 회로를 조립하거나 `nmcnr_predict_ac_response()`로 검증할 때
    이 함수로 Cm1/Rm/Cm2를 구한다(직접 대입하지 말고 항상 이 함수를 통해서 — Eq 8/9를
    실수로 잘못 옮겨적는 걸 방지).

    검증 상태: Eq 8/9 원문 이미지 대조 검증 완료(topology-fn-derivation-guide.md §3).
    """
    Cm1 = 4 * (gm1 / gm3) * CL       # Eq 8
    Rm = 1 / gm3                      # 본문(RHP-zero 완전제거 조건)
    Cm2 = (2 / (1 - kg)) * (gm2 / gm3) * CL  # Eq 9
    return Cm1, Rm, Cm2


def nmcnr_predict_ac_response(gm1: float, gm2: float, gm3: float, R1: float, R2: float, R3: float,
                         CL: float, kg: float, f_start: float = 1.0, f_stop: float = 1e9,
                         n_points: int = 2000) -> dict:
    """사이징 완료 후 실제 GBW/PM/노치 여부를 검증 — Eq 10/11의 근사 없이 **4-노드**(V1, V2,
    NodeCM, Vout) KCL을 정확히 풀어 계산한다.

    ⚠️ **개명 이력(2026-08-19 세션37 연속) -- 원래 이름 `nmcnr_predict_notch()`에서 변경**:
    옛 이름은 "이 함수의 핵심 임무가 노치 탐지"라는 인상을 주지만, 실제로는 그 반대다 --
    노치는 **잘못 조립된(3-노드) 보상망에서만 나타났던 증상**이었고(아래 2026-07-31 재유도
    문단), 올바르게 조립된 회로(현재 4-노드 모델)에서는 노치가 없는 게 정상이다(`notch=False`가
    기대값). 이 함수의 진짜 임무는 "Eq 10/11 근사 없이 실제 사이징값으로 정확한 AC 응답(DC
    이득/위상/0dB 교차/PM)을 계산"하는 것이고, `notch`는 그 계산이 내놓는 여러 진단 필드 중
    하나(다중 교차 여부)일 뿐이다 -- 사용자 지적으로 이름을 그 실제 임무에 맞게 정정.

    이 개명과 함께 **독립 재유도로 재검증**도 했다(사용자 동기: "이전에 잘못 연결된 topology
    때문에 notch가 유도되었었는데, 지금(4-노드) 버전도 혹시 비슷한 문제가 있는지 불확실해서" --
    2026-07-31 수정 이후 처음으로 이 함수 자체를 처음부터 다시 검증). 아래 4개 KCL 방정식
    (V1/V2/NodeCM/Vout, `-Av1/+Av2/-Av3` 부호 관례 그대로)을 sympy로 처음부터 다시 풀어
    Vout/Vin의 분자/분모 다항식을 구했고, 이 함수에 하드코딩된 `num`/`den` 계수와 **항별로
    완전히 일치**함을 확인했다(`sp.simplify(차이)`가 7개 계수 전부 정확히 0). 즉 토폴로지→
    전달함수 변환 자체(대수)에는 오류가 없다 -- 2026-08-19 세션의 `pm_deg=48.32도`(PM_target_
    deg=70도 목표 대비 낮음)는 이 함수의 버그가 아니라 실제 사이징 결과가 만드는 물리적으로
    정직한 값이라는 뜻(Eq 10/11 근사의 한계, 아래 및 `nmcnr_3stage_topology()` 참고).

    ⚠️ **2026-07-31 재유도(중요한 정정)**: 원래 이 함수(및 그 유도처인 sky130-worked-example.md
    §12.7.3)는 "Cm1은 V1↔Vout 직결, Rm+Cm2가 직렬로 V2↔Vout"이라는 **3-노드** 모델로 세워졌었다.
    그런데 논문 원문 Fig.3을 실제 이미지로 다시 확인(사용자와 함께, node-by-node 대화형 검증)한
    결과 실제 구조는 **Cm1과 Cm2가 하나의 공통 노드(NodeCM)에서 만나고, 그 뒤에 Rm 하나를
    Cm1/Cm2가 공유**하는 구조였다(논문 abstract가 명시한 "only ONE null resistor"와 정확히
    일치 — 예전 3-노드 모델은 이 문장과도 안 맞았다). 그래서 KCL 노드가 하나 늘어(V1/V2/NodeCM/
    Vout, 4개) 재유도했다 — num/den 차수 자체는 우연히 예전과 같다(분자 2차/분모 3차, NodeCM
    도입이 새 커패시터를 추가한 게 아니라 기존 Cm1/Cm2가 만나는 방식만 바꿨기 때문).

    입력: gm1/gm2/gm3(목표 gm, `nmcnr_3stage_topology()`가 반환한 값), R1/R2/R3(각 스테이지
    **실제 사이징 결과**의 출력저항 = gain_i/gm_i, 즉 `find_optimal_sizing()`/`optimize_multistage()`
    결과의 `gain` 필드를 gm_i로 나눈 값), CL, kg.

    반환: dict(crossings=[(f_Hz, PM_deg), ...] 0dB 교차 전부, notch=bool(교차 2개 이상이면 True),
    dc_gain_db=float). `notch=True`면 Eq 10/11이 예측한 GBW/PM을 믿지 말고 실제 SPICE로
    재확인할 것 — 이 함수 자체도 이상화(VCCS+ro, 실소자 기생 없음) 모델이라 최종 확인은 항상
    SPICE다(방법론 문서 §4.5 원칙 그대로).

    ⚠️ 이 함수도 이상화(VCCS+ro, 실소자 기생 없음) 모델이라 최종 확인은 항상 SPICE다(방법론
    문서 §4.5 원칙 그대로) — 정량값(GBW/PM/DC이득)은 반드시 실제 회로로 재확인할 것.

    검증 상태: 대표 동작점(gm1=7.1267mS/gm2=0.6283mS/gm3=1.2566mS/R1=3465Ω/R2=90188Ω/
    R3=19269Ω/kg=0.5)에서 이상화 SPICE(ngspice AC) 및 실제 sky130 트랜지스터 재조립 둘 다와
    교차검증 완료(DC이득/DC위상/PM/교차횟수 전부 일치). 유도 과정은 sky130-worked-example.md
    §12.3 참고.
    """
    Cm1, Rm, Cm2 = nmcnr_compensation_elements(gm1, gm2, gm3, CL, kg)

    # 4-노드(V1,V2,NodeCM,Vout) KCL을 근사 없이 직접 푼 정확한 전달함수(분자 2차/분모 3차) 계수.
    # 유도(2026-07-31 재유도, sympy): V1(gm1*Vin=V1/R1+sCm1(V1-Vcm)), V2(gm2*V1=V2/R2+sCm2(V2-Vcm)),
    # NodeCM(sCm1(V1-Vcm)+sCm2(V2-Vcm)=(Vcm-Vout)/Rm), Vout(gm3*V2+(Vcm-Vout)/Rm=Vout/R3+sCL*Vout).
    # Fig.1 부호 관례(-Av1, +Av2, -Av3 -- 스테이지1/3은 반전, 스테이지2는 비반전)를 그대로
    # 반영(2026-07-31 정정 -- 첫 유도는 전부 +gm으로 둬서 PM이 음수로 나오는 오류가 있었다,
    # 이상화 SPICE(ngspice AC, -Av1/+Av2/-Av3 극성으로 조립)와 DC이득/DC위상/PM 전부 정확히
    # 일치함을 확인한 버전).
    num = [
        Cm1 * Cm2 * R1 * R2 * R3 * gm1 * (Rm * gm3 - 1),
        R1 * R3 * gm1 * (Cm1 * R2 * Rm * gm2 * gm3 - Cm1 + Cm2 * R2 * Rm * gm2 * gm3
                           - Cm2 * R2 * gm2),
        R1 * R2 * R3 * gm1 * gm2 * gm3,
    ]
    den = [
        CL * Cm1 * Cm2 * R3 * (-R1 * R2 * Rm * gm2 + R1 * R2 + R1 * Rm + R2 * Rm),
        CL * Cm1 * R1 * R3 + CL * Cm1 * R3 * Rm + CL * Cm2 * R2 * R3 + CL * Cm2 * R3 * Rm
        - Cm1 * Cm2 * R1 * R2 * R3 * gm2 + Cm1 * Cm2 * R1 * R2 * R3 * gm3
        - Cm1 * Cm2 * R1 * R2 * Rm * gm2 + Cm1 * Cm2 * R1 * R2 + Cm1 * Cm2 * R1 * R3
        + Cm1 * Cm2 * R1 * Rm + Cm1 * Cm2 * R2 * R3 + Cm1 * Cm2 * R2 * Rm,
        CL * R3 + Cm1 * R1 * R2 * R3 * gm2 * gm3 + Cm1 * R1 + Cm1 * R3 + Cm1 * Rm
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


@functools.lru_cache(maxsize=256)
# 2026-08-19(세션37 연속) -- `nmcnr_3stage_topology()`가 이 함수를 topology_fn에 자동으로
# 붙이는데(아래), 그 팩토리 자체는 `sizing_recipe.py`의 `_COMPENSATION_REGISTRY[...](**comp_
# params)` 호출부(4017행 근처)가 **theta 그리드서치 평가마다** 재호출한다(comp_params가
# 변하지 않아도 `_comp_cache`는 그 다음 단계(`comp_result`)만 캐싱, 이 팩토리 자체는 무방비) --
# 4000점 주파수 스윕을 매 그리드점마다 반복 계산하지 않도록 순수함수(입력 4개 float)를 그대로
# `lru_cache`. nmcnr_amplifier는 현재 theta가 전부 고정 단일점이라 실질 영향은 없지만, 앞으로
# nmcnr 회로에 실제 grid search가 붙으면 이게 없으면 재계산 폭발이 된다("수정마다 재계산 효율
# 점검을 설계 단계부터" 원칙 적용).
def nmcnr_check_dominant_pole_approximation(GBW: float, CL: float, PM_target_deg: float, kg: float,
                                             R_ideal: float = 1e15) -> dict:
    """`nmcnr_3stage_topology()`의 Eq 10/11이 전제하는 "우세극이 나머지 극점들과 충분히
    떨어져 있다"는 근사가 **주어진 스펙(GBW/PM_target/kg)에서 실제로 성립하는지** 검증한다
    (2026-08-19 세션37 연속, 사용자 지시 "Eq10/11 근사 한계도 다시 유도하자"로 신설).

    **방법**: Eq 10/11로 gm1/gm2/gm3를 구한 뒤, `nmcnr_predict_ac_response()`를 `R1=R2=R3=
    R_ideal`(기본 1e15Ω, "무한대"에 근접한 값)로 호출해 **R1/R2/R3가 유한해서 생기는 오차를
    배제한, Cm1/Cm2/Rm만으로 결정되는 이상화된 정확해**의 GBW/PM을 구한다(R을 1e3→1e15까지
    스윕해 1e9 이상에서 수치적으로 수렴함을 실측 확인 — `.ai/context.md` 세션37 참고). 이
    "R→무한대 극한의 정확해"를 Eq 10/11이 예측한 값과 비교한다 — **둘이 안 맞으면 그 자체가
    이미 Eq10/11의 결함**(R을 무한대로 보내 이상화까지 했는데도 안 맞으므로, R1/R2/R3가
    유한해서 생기는 오차와는 무관하게 근사식 자체의 문제)이라는 뜻이다.

    **발견 1 -- GBW/CL/kg는 무관, PM_target_deg 하나만 좌우한다(놀랍지만 대수로 확인됨)**:
    Cm1/Cm2/Rm(=`nmcnr_compensation_elements()`)을 대입해 R→무한대 극한을 sympy로 풀면
    `H(s) = gm3·(4·CL·gm1·s+gm3²) / [4·CL·s·(2·CL²·s²+2·CL·gm3·s+gm3²)]`로 정리되는데,
    분모의 `D(s)=2·CL²·(gm2-gm3)·s²+2·CL·gm3·(gm2-gm3)·s+gm3³·(kg-1)`가 `gm2=kg·gm3`를
    대입하면 `gm3·(kg-1)·[2·CL²·s²+2·CL·gm3·s+gm3²]`로 인수분해되고, 이 `(kg-1)` 인자가
    분자의 `(kg-1)`과 **정확히 소거**돼 최종 `H(s)`엔 `kg`가 아예 안 남는다(수치로도 확인:
    kg=0.05~0.95 스윕에도 crossing이 소수점 8자리까지 불변). 또한 `gm1=gm3/tan(PM_target-60°)`
    `gm3=4·wGBW·CL`이 전부 (GBW·CL) 곱에 선형 비례하므로, GBW나 CL을 아무리 바꿔도
    (`gm1/gm3`, 즉 PM_target_deg만 고정하면) `gbw_ratio`/`pm_diff_deg`는 **완전히 불변**이다
    (실측: GBW 16배 축소, CL 100배 확대 둘 다 소수점 6자리까지 동일값). **즉 이 근사가
    성립하는지는 GBW·CL·kg와 무관하게 오직 PM_target_deg 하나로만 결정된다.**

    **발견 2 -- 물리적으로 타당한 PM_target 60~90도 전 구간에서 근사가 사실상 항상 깨져
    있다**: PM_target_deg를 61도~140도까지 스윕하면 `gbw_ratio`(실제/Eq10)가 21.4배(61도)에서
    시작해 단조감소하지만 90도 근처에서도 여전히 2.5~3배, 140도에서야 겨우 1.0배 근처로
    수렴한다(`pm_diff_deg`는 61도에서 +40도, 90도 근처에서 +68~72도로 오히려 더 벌어졌다가
    140도 이후 줄어듦). `valid=True`(문턱: ratio 0.5~2.0, |diff|<15도)가 나오는 지점은
    149도 근처(`tan(PM-60°)`의 특이점 150도 바로 아래) 뿐 -- **실무에서 쓸 일이 없는 값**이다.
    결론: **NMCNR 구조에서 Eq10/11의 "우세극 분리" 전제는 물리적으로 의미 있는 PM_target
    범위(60~90도) 전체에서 사실상 항상 깨져 있다** — 이 프로젝트의 `nmcnr_amplifier`
    (GBW=816kHz/CL=1e-10F/PM_target=70도)가 특별히 나쁜 경우가 아니라 NMCNR 토폴로지
    자체의 구조적 특성으로 보인다(다른 논문 예제/공정으로 일반화됐는지는 검증 안 함).

    ⚠️ **정직한 한계 -- 이 R→무한대 진단과 실제 `nmcnr_amplifier` 실측(pm_deg=48.32도, 목표
    70도 대비 **낮음**)은 방향이 다르다**: 이 함수(R→무한대 극한)는 PM이 목표보다 오히려
    **높게**(70도→124.6도) 나온다고 진단하는데, 실제 유한 R1/R2/R3(진짜 스테이지 출력저항)를
    쓰는 `nmcnr_predict_ac_response()`의 실측은 PM이 목표보다 **낮게**(70도→48.32도) 나왔다
    (`.ai/context.md` 세션37 초반 참고). 즉 Eq10/11 자체의 근사 오류(이 함수가 진단하는 것)와
    R1/R2/R3가 유한해서 생기는 별도 오차가 **서로 다른 방향으로 작용**하며, 실제 회로에서는
    후자가 더 강하게 지배한다는 뜻이다 — 이 함수는 전자만 분리해서 정량화한다(둘을 합친
    "진짜 원인"은 아직 완전히 규명 안 됨, 다음 세션 이월 가능).

    반환: `{"gm1","gm2","gm3", "eq10_gbw_hz","eq11_pm_deg" (Eq10/11이 예측한 값),
    "exact_ideal_gbw_hz","exact_ideal_pm_deg" (R→무한대 극한 정확해), "gbw_ratio" (exact/eq10),
    "pm_diff_deg" (exact-eq11), "valid"(bool, `gbw_ratio`가 0.5~2.0 안이고 `pm_diff_deg`
    절댓값이 15도 미만이면 True -- 두 문턱 다 임의값, 엄밀한 이론적 근거는 없고 "6.7배/54도"
    같은 명백한 위반과 "정상 근사"를 가르는 실용적 눈금일 뿐이니 경계 근처 값은 항상 사람이
    직접 `nmcnr_predict_ac_response()`로 재확인할 것)}`."""
    wGBW = 2 * math.pi * GBW
    gm3 = 4 * wGBW * CL
    pm_rad = math.radians(PM_target_deg - 60.0)
    if pm_rad <= 0:
        raise ValueError("PM_target_deg는 60도보다 커야 한다(NMCNR 구조상 PM>60도 보장)")
    gm1 = gm3 / math.tan(pm_rad)
    gm2 = kg * gm3

    exact = nmcnr_predict_ac_response(gm1, gm2, gm3, R_ideal, R_ideal, R_ideal, CL=CL, kg=kg,
                                       f_start=1.0, f_stop=1e10, n_points=4000)
    if not exact["crossings"]:
        return dict(gm1=gm1, gm2=gm2, gm3=gm3, eq10_gbw_hz=GBW, eq11_pm_deg=PM_target_deg,
                    exact_ideal_gbw_hz=None, exact_ideal_pm_deg=None,
                    gbw_ratio=None, pm_diff_deg=None, valid=False)
    exact_gbw_hz, exact_pm_deg = exact["crossings"][0]
    gbw_ratio = exact_gbw_hz / GBW
    pm_diff_deg = exact_pm_deg - PM_target_deg
    valid = (0.5 <= gbw_ratio <= 2.0) and (abs(pm_diff_deg) < 15.0)
    return dict(gm1=gm1, gm2=gm2, gm3=gm3, eq10_gbw_hz=GBW, eq11_pm_deg=PM_target_deg,
                exact_ideal_gbw_hz=exact_gbw_hz, exact_ideal_pm_deg=exact_pm_deg,
                gbw_ratio=gbw_ratio, pm_diff_deg=pm_diff_deg, valid=valid)


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
# 4) Current-reuse telescopic OTA(Class-AB 2단) — Xie & Chen, "A 126uW Current-Reuse
#    Telescopic OTA with Class-AB Output Stage"(UT Austin) 원문 Eq.2-6 그대로(2026-07-31,
#    사용자와 함께 원문 PDF를 직접 열어 재도출 -- 이전에 AI가 근거 없이 재구성해 등록했다가
#    사용자 지적으로 되돌린 뒤, 이번엔 원문 p.3-4를 실제로 확인하고 다시 구현).
# ---------------------------------------------------------------------------

def current_reuse_telescopic_topology(t_lln: float, PM_target_deg: float,
                                       Cf: float, Cs: float, C_Ltot: float,
                                       Cc: float | None = None):
    """current-reuse telescopic OTA(Class-AB 2단) 위상보상 방정식 — 원문(Xie & Chen)
    Section III "Circuit Parameters Derivation" Eq.2-6 그대로:

    - Eq.2(p.3): `t_lln * omega_c = 6.9` (정착오차 ε_d≤0.1%의 1차 지수감쇠 정착식,
      `-ln(0.001)=6.908`과 정확히 일치 — 직접 검산 확인) → `omega_c = 6.9/t_lln`.
    - Eq.3(p.4): `gm1 = omega_c * Cc / beta`.
    - Eq.4(p.3): `beta = Cf/(Cf+Cs+Cgg1)` — 원문 원문 그대로 인용: **"assuming Cgg1 is
      negligible... In reality, Cgg1 is not negligible, therefore we assume beta is
      around 0.48"**. 즉 원문 자신도 Cgg1을 정밀 계산하지 않고 상수로 가정한다. 이 함수는
      원문의 가정(β=0.48 고정)보다 한 단계 더 엄밀하게 간다 — Cgg1은 실제로 1단 자신의
      게이트 커패시턴스(M1a/M4a, W가 gm1 자체에서 나옴)라 **gm1→W(M1a)→Cgg1→β→gm1**로
      순환한다(Cgg2가 gm2에 순환하는 것과 정확히 같은 구조). `miller_ota_topology()`가
      이미 쓰는 `prev_cggs` 고정점 반복 패턴을 1단에도 그대로 적용해 β를 "가정된 상수"가
      아니라 **1단 자신의 실제 사이징에서 수렴하는 값**으로 만든다(2026-07-31 사용자와
      함께 결정 — β를 유도 없이 그냥 받아쓰지 않기로 함). 초기 추정(Cgg1=0, prev_cggs=None)
      은 원문의 "Cgg1 negligible" 가정과 동일한 출발점이다.
    - Eq.5(p.4): `gm1 = gmn + gmp`(gmn=gmp 가정, current-reuse라 NMOS/PMOS 둘 다 같은 입력
      핀에 물려 입력을 받음 — p.2 "gain shows as ((gmn4+gmp1)*ro)^2"). **이 함수는 gm1을
      합으로 반환하지 않고 `gmp`/`gmn`을 별개 stage로 나눠 반환한다**(2026-07-31 사용자와
      설계 — `stage_devices`의 기존 계약("그룹의 모든 소자가 그 stage의 gm을 동일하게
      받음")을 안 바꾸고, "합을 나누는 일"을 이 함수 자신이 하도록 함: PMOS M1a/M1b는
      `gmp`만, NMOS M4a/M4b는 `gmn`만 받아야 하는데, 이건 diff pair처럼 "각자 gm1을 온전히
      가짐"과 다른 패턴이라 그대로 두면 안 됨). `optimize_multistage()`는 스테이지 개수를
      전혀 하드코딩하지 않는 제네릭 엔진(`n = len(luts)`)이라, 반환 리스트 길이를 늘리는 데
      엔진 쪽 변경이 전혀 필요 없다 — `nmcnr_3stage_topology()`가 이미 3개(gm1/gm2/gm3)를
      반환하는 것과 정확히 같은 메커니즘 재사용일 뿐이다.
    - Eq.6(p.4): `omega_p2 ≈ gm2 / (C_Ltot*Cgg2/Cc + Cgg2 + C_Ltot)`, 그리고 **"Given
      phase margin PM = tan⁻¹(ωp2/ωc) [9]"**(원문이 직접 인용하는 참고문헌 — 표준 2-pole
      위상마진식) → `ωp2/ωc = tan(PM_target)`(원문 검산: PM=70°→tan(70°)=2.7475≈2.8,
      원문이 준 "2.8"과 일치). `Cgg2`는 2단 게이트 커패시턴스(`miller_ota_topology()`와
      동일한 고정점 반복 패턴).

    ⚠️ **2026-08-12(세션30) 정정 -- `gm2`를 `gmp2`/`gmn2`(M15/M25=PMOS, M16/M26=NMOS)로
    분리 반환**: Eq.5와 같은 이유(gm1→gmp/gmn)가 아니라 정반대 이유다 -- Eq.5의 gmp/gmn은
    "물리적으로 같은 값이어야 한다"(gmn=gmp 가정)는 게 원문 근거지만, Eq.6의 2단(M15/M25
    PMOS·M16/M26 NMOS)은 서로 다른 kind라 **원문이 두 kind의 L을 같게 두라고 요구한 적이
    없다**(원문 어디에도 M15/M16 간 matching 요구가 없음 -- 문헌조사로도 cross-kind 상보
    출력쌍의 L 통일을 요구하는 회로이론적 원칙은 없음을 확인, `.ai/context.md` 세션30
    참고). 오히려 `classab_centering_dev_v`(M15=Vop1 레벨/M16=Vg15 레벨, 합=VDD 요구)가
    실측으로 확인한 건 **두 소자가 서로 다른 DC 동작점 제약을 각자 책임진다**는 것 --
    같은 L 하나로 억지로 묶으면(세션29 "## AN") gain_db와 정반대 방향으로 상충한다.
    `topology.json`의 declared `matching_pairs`도 이미 M15-M25(PMOS끼리)/M16-M26(NMOS끼리)
    로만 선언돼 있고 M15-M16 cross-kind 매칭은 애초에 없다 -- 이 함수의 반환 분리는 그
    선언을 그대로 따르는 것뿐이다. `gm2 = gmp2 + gmn2`(Eq.5의 gm1=gmp+gmn과 동일 항등식,
    `gain_stages_sum` metric이 이미 `gm(M15)+gm(M16)` 병렬 합으로 계산하고 있었다 --
    sizing_recipe.py `_metric_gain_stages_sum()` 참고, 이번 분리로 그 계산과 정확히
    일치하게 됨). **분할 비율은 원문이 근거를 안 주므로 Eq.5와 같은 관례로 50:50
    (`gmp2=gmn2=gm2/2`)을 기본값으로 둔다** -- 실제로 M15/M25(PMOS)와 M16/M26(NMOS)의
    L이 서로 갈라지는 지점은 이 초기 분할이 아니라, 그 이후 `L_stage2out_p`/
    `L_stage2out_n`(topology.json 별도 theta, 각자 독립 탐색)에서 결정된다 -- 이 함수는
    "M15/M25가 gmp2를, M16/M26이 gmn2를 받는다"는 stage_devices 위치 매핑만 책임진다.
    ⚠️ L은 독립이어도 **ID(M15)=ID(M16)는 여전히 강제돼야 한다** -- Vom이 M15.drain/
    M16.drain 둘뿐인 2단자 net이라(사이징 엔진이 읽는 netlist 기준) push-pull 출력단의
    순수 connectivity KCL이 요구하는 것(선언이 아니라 회로 위상 자체의 귀결, 세션30
    self-test가 `propagate_topology_forced_currents()` ValueError로 실측 확인). gmp2=gmn2
    50:50만으로는 부족하다 -- 두 스테이지가 각자 다른 kind LUT에서 독립적으로 gm_id를
    고르면 ID=gm/gm_id가 갈라진다. topology.json의 `compensation.shared_gm_id_groups`에
    `[2,3]`(이 함수의 stage index, M15/M25 그룹·M16/M26 그룹)을 추가해 gm_id만 공유시켜
    해결한다(L은 `_size_group_at_gm_id()`가 그룹 안에서도 스테이지별로 독립 탐색 —
    `shared_gm_id_groups`는 gm_id 공유일 뿐 L 공유가 아니다, sizing_recipe.py 확인).

    반환: `topology_fn(prev_cggs) -> [gmp, gmn, gmp2, gmn2]`(4개, `prev_cggs`도 그에 맞춰
    4개 — `prev_cggs[0]`=M1a/M1b PMOS의 Cgg, `prev_cggs[1]`=M4a/M4b NMOS의 Cgg,
    `prev_cggs[2]`=M15/M25(PMOS) 2단 소자의 Cgg, `prev_cggs[3]`=M16/M26(NMOS) 2단 소자의
    Cgg). β의 `Cgg1`은 `prev_cggs[0]+prev_cggs[1]`의 **합**이다 — M1a와 M4a 게이트가
    물리적으로 같은 입력 핀(Vip/Vim)을 공유하므로, 그 핀에서 보이는 총 커패시턴스는 두
    소자 게이트 커패시턴스의 합이기 때문이다. Eq.6의 `Cgg2`는 `prev_cggs[2]+prev_cggs[3]`
    의 **합**을 그대로 쓴다(Cgg1과 같은 패턴 재사용, 세션29까지의 근사 수준을 유지 --
    이전엔 4소자 전체를 PMOS LUT 하나로 뭉뚱그린 값이었는데 이제 각 kind 전용 LUT로 계산된
    두 값의 합이라 오히려 더 정확해졌다. Cc가 실제로 M16.gate에만 물린다는 물리적 사실을
    반영해 `prev_cggs[3]`만 쓰는 게 더 정밀할 수 있으나, 이건 Eq.6 자체의 물리적 재검토라
    이번 세션 범위(L 독립화) 밖 -- 다음 조사 항목으로 남긴다).

    함수 속성으로 `exposed_params`(omega_c) 외에 `stage_fT_targets`(2026-08-12 세션30
    신설, `optimize_multistage()`가 읽는 선택적 속성 -- 스테이지별 준정적 검증 기준주파수
    Hz 리스트, 함수 정의 아래 주석 참고)도 노출한다.

    검증 상태: Eq.2/3/5/6 전부 원문 수식과 대조 확인(원문 수치 예제로 gm1(=gmp+gmn)=238µS/
    ωp2/ωc=2.8 재현). β는 원문의 고정 근사(0.48) 대신 `prev_cggs[0]+prev_cggs[1]` 고정점
    반복으로 대체했으므로, 실제 공정 LUT에서 나오는 값은 원문의 0.48과 다를 수 있다(공정이
    다르면 Cgg1 자체가 다르므로 정상 — do.md 배치 7-3/7-5 참고)."""
    omega_c = 6.9 / t_lln
    ratio = math.tan(math.radians(PM_target_deg))  # 원문 p.4 "PM = tan^-1(omega_p2/omega_c) [9]"
    omega_p2 = ratio * omega_c

    def topology_fn(prev_cggs):
        if prev_cggs is None:
            cgg1_total = 0.0  # 초기 추정: 원문의 "Cgg1 negligible" 가정과 동일
            cgg2 = C_Ltot * 0.1  # 초기 추정(miller_ota_topology와 같은 관례)
        else:
            cgg1_total = prev_cggs[0] + prev_cggs[1]  # M1a(PMOS)+M4a(NMOS), 같은 입력 핀 공유
            cgg2 = prev_cggs[2] + prev_cggs[3]  # M15/M25(PMOS)+M16/M26(NMOS), Cgg1과 동일 패턴
        beta = Cf / (Cf + Cs + cgg1_total)
        # 2026-09-10(사용자 지시 "Cc와 Rz는 보상망이 계산해서 확정해야지") -- Cc는 더
        # 이상 손으로 넣는 상수가 아니다. 원문은 "By setting Cc to 500fF"로 **사람이
        # 골랐지만**, 그 값은 원문 자신의 Eq.3/Eq.6에서 **유도된다**:
        #
        #     gm1 = omega_c*Cc/beta                              (Eq.3)
        #     gm2 = omega_p2*(C_Ltot*Cgg2/Cc + Cgg2 + C_Ltot)    (Eq.6)
        #
        # Cc를 키우면 gm1은 선형으로 늘고 gm2는 준다(Miller 항 C_Ltot*Cgg2/Cc가 작아짐).
        # 선언된 목적이 전력 최소화이고 전력은 sum(gm_i/gm_id_i)이므로, 두 단의 gm/ID가
        # 같다는 1차 가정에서 d(gm1+gm2)/dCc = 0 을 풀면
        #
        #     Cc = sqrt( beta * tan(PM_target) * C_Ltot * Cgg2 )
        #
        # 가 나온다(omega_p2 = omega_c*tan(PM_target)을 대입하면 omega_c가 소거된다).
        # **새 상수가 하나도 없다**: beta는 Cf/Cs/Cgg1(실측), tan(PM_target)/C_Ltot은
        # 선언, Cgg2는 prev_cggs로 들어오는 실측값이다. miller_ota_topology()가 Cm을
        # 실측 용량에서 계산하는 것과 정확히 같은 성격이다(그쪽도 pole-splitting 최적점).
        #
        # 검산(2026-09-10 파일럿): beta=0.4514(원문 ~0.48), Cgg2=112.8fF -> Cc=374fF이고
        # gm 합이 917.1 -> 903.6uS로 낮아진다. 원문의 500fF는 **그들의** Cgg2에 대한
        # 값이라, 이 식은 회로가 바뀌면 따라간다 -- 그게 상수와 다른 점이다.
        #
        # Cc 인자를 명시로 주면(하위호환/실험용) 그 값이 이긴다.
        cc_used = Cc if Cc is not None else math.sqrt(
            beta * math.tan(math.radians(PM_target_deg)) * C_Ltot * cgg2)
        # MNA(_resolve_capacitor_farad())도 이 값을 읽어야 하므로 노출한다 -- prev_cggs에
        # 따라 매 반복 갱신되므로 팩토리가 아니라 여기서 쓴다(팩토리는 cgg2를 모른다).
        topology_fn.exposed_params = dict(getattr(topology_fn, "exposed_params", {}),
                                          omega_c=omega_c, Cc=cc_used)
        gm1 = omega_c * cc_used / beta
        gmp, gmn = gm1 / 2.0, gm1 / 2.0  # Eq.5: gmn=gmp 가정
        gm2 = omega_p2 * (C_Ltot * cgg2 / cc_used + cgg2 + C_Ltot)
        gmp2, gmn2 = gm2 / 2.0, gm2 / 2.0  # 세션30: kind 경계 분리, 분할비 50:50은 기본값(위 docstring 참고)
        return [gmp, gmn, gmp2, gmn2]

    # 2026-08-10(세션27) -- omega_c(Eq.2)는 do.md §7.3.1 Level2->Level6 사슬에서 CMFB
    # 대역폭조건(N_cmfb_bw)의 입력이어야 하는데, 지금까지는 이 클로저 안에 갇혀 호출자가
    # 꺼낼 방법이 없었다(N_cmfb_bw는 spec["omega_c"]라는 별도 손채움 상수를 읽어 t_lln과
    # 무관하게 어긋날 수 있었음). optimize_multistage()/_evaluate()의 기존 반환 계약(gm
    # 리스트만)을 안 바꾸려고, 함수 속성으로 노출한다 -- sizing_recipe.py의 _evaluate()가
    # 있으면 ctx.derived로 옮겨 _feed_gm_target_convention()이 spec보다 우선해 읽는다.
    topology_fn.exposed_params = {"omega_c": omega_c}
    # 2026-08-12(세션30) -- optimize_multistage()가 읽는 선택적 속성(engine 문서 참고,
    # sizing_recipe.py) -- 준정적(quasi-static) 유효성 검증의 스테이지별 기준주파수(Hz).
    # 이미 위에서 구한 omega_c/omega_p2(rad/s)를 Hz로만 바꿔 재사용한다(새 수식 없음).
    # 반환 gm 리스트[gmp,gmn,gmp2,gmn2]와 위치로 대응: 1단(M1a/M4a)은 메인루프
    # unity-gain 주파수(omega_c) 기준, 2단(M15/M16류)은 그보다 높은 비지배극 목표
    # (omega_p2, Eq.6) 기준 -- gm-id-methodology.md §6.4 Miller pole-splitting 안정조건
    # "2단 gain-bandwidth > omega_T"(2단이 1단보다 더 빨라야 함)와 일치하는 방향.
    topology_fn.stage_fT_targets = [omega_c / (2 * math.pi), omega_c / (2 * math.pi),
                                     omega_p2 / (2 * math.pi), omega_p2 / (2 * math.pi)]
    return topology_fn
