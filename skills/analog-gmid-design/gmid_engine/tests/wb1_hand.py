"""WB-1 레이아웃 뒤·실현 재풀이의 손 계산 (interface card 20261104-wb1 §6 R-2·R-6·R-13, 개정 2026-11-06, 판정 MJ-1).

oracle (a) 합성 입력의 닫힌 식에서 손으로 유도한 고정점. 피검 함수를 부르지 않고, 피검 식을 다시 쓰지도 않는다 -- 아래 식은 sizing conftest 의 r4 toy
식 ID ∝ (W/L)·exp(B·VGS − C·VGS²/2 + LAM·VDS − A·VS²) 에서 회로 KCL 로 유도한 것이고, 근은 이분법(독립 스칼라 풀이)으로 구한다.
"""
from __future__ import annotations

import math


def bisect(f, lo, hi, iters=200):
    """f(lo)·f(hi) <= 0 인 구간에서 이분법. 부호 변화가 없으면 AssertionError (구성 오류)."""
    flo, fhi = f(lo), f(hi)
    assert flo * fhi <= 0.0, (lo, hi, flo, fhi)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm <= 0.0) == (flo <= 0.0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


def diff_pair_input_shift(r, vgs0, b, c, lam, vcm_antisymmetric=True):
    """R-2·R-13(a) 의 입력 차 이동 크기 Δ (V_id 는 −Δ 만큼 이동).

    유도: 거울 + 고정 꼬리 전류가 M1·M2 VDS 를 같게 하므로 M1(W′ = W(1 + r)) 의 f(VGS1) + ln(1 + r) = f(VGS2) (f(v) = b·v − c·v²/2, bulk = t 라 VS 항 0).
    VGS1 = VGS2 − Δ 이므로 g2·Δ + c·Δ²/2 = ln(1 + r), g2 = b − c·VGS2 -> Δ = [−g2 + √(g2² + 2c·ln(1 + r))]/c.
    M2 전류 불변: f(VGS2) − f(vgs0) + lam·(VGS2 − vgs0 − ΔV(inn)) = 0, ΔV(inn) = e_n·V_id′/(e_p − e_n) = Δ/2 (공통모드 고정, 반대칭 가중 ±1/2).
    두 식의 고정점을 VGS2 − vgs0 = x 에 대한 한 변수 이분법으로 푼다. -> (Δ, x)
    """
    assert vcm_antisymmetric
    lr = math.log(1.0 + r)

    def delta_of(x):
        g2 = b - c * (vgs0 + x)
        return (-g2 + math.sqrt(g2 * g2 + 2.0 * c * lr)) / c

    def f(v):
        return b * v - 0.5 * c * v * v

    def h(x):
        return f(vgs0 + x) - f(vgs0) + lam * (x - 0.5 * delta_of(x))
    x = bisect(h, -0.2, 0.2)
    return delta_of(x), x


def single_input_out_shift(a, r, lam):
    """R-6·R-13(b) 의 ΔV(out): ΔV = −a·[(1 + r)·e^{lam·ΔV} − 1] (한 변수 고정점).

    유도: 입력 고정, M1 VDS = V(out), source = bulk = gnd. M1 전류 I′ = (1 + r)·I·e^{lam·ΔV}, 출력 KCL (V_dd − V(out)_실현)/R = I′, 탐색 KCL R·I = a.
    G(ΔV) = ΔV + a·[(1 + r)·e^{lam·ΔV} − 1] 은 ΔV 에 대해 증가(lam·a·(1 + r) 항도 증가)라 근이 하나다. 레일 안 근이 없으면 None (R-6c).
    """
    def g(dv):
        return dv + a * ((1.0 + r) * math.exp(lam * dv) - 1.0)
    lo, hi = -a - 1.0, 1.0           # 하한: V(out) = V_dd − a − (a + 1) 아래까지 넓게 (부호 변화 확인용)
    if g(lo) * g(hi) > 0.0:
        return None
    return bisect(g, lo, hi)


def out_kcl_at_gnd(vdd, vgnd, res, i, v_out0, r, lam):
    """R-6c 조건 (판정 MJ-1): F(V) = (V_dd − V)/R − (1 + r)·I·e^{lam·(V − V_out0)} 은 V 에 대해 감소하고 F(V_dd) < 0 이므로 근이 [V_gnd, V_dd] 에 있을 조건은
    F(V_gnd) >= 0 이다. 반환 F(V_gnd) (음수면 레일 안에 근이 없다)."""
    return (vdd - vgnd) / res - (1.0 + r) * i * math.exp(lam * (vgnd - v_out0))


# ---- 레일 소스 꼴 (dispute 7.1, 2026-11-06): M1 pmos (out, in, vdd, bulk = vdd), 저항 R out -> gnd ----
# 유도(r4 식 ID ∝ (W/L)·exp(B·VSG − C·VSG²/2 + LAM·VSD), source = bulk = vdd 라 VS 항 0, VSG = V_dd − V(in) 불변): VSD = V_dd − V(out) 이므로
# M1 전류 I′ = (1 + r)·I·e^{−LAM·ΔV(out)}, 출력 KCL V(out)/R = I′, 탐색 KCL R·I = a = V(out)_탐색 -> ΔV = a·[(1 + r)·e^{−LAM·ΔV} − 1].
# u = V_dd − V(out) 로 거울을 취하면 위 식은 nmos·vdd 저항 꼴(`single_input_out_shift`)과 같은 식이다(ΔV_nmos = −ΔV_pmos, 같은 a).
def source_load_out_shift(a, r, lam):
    """레일 소스 꼴(pmos 소스 = vdd, 저항 out -> gnd)의 ΔV(out) = a·[(1 + r)·e^{−lam·ΔV} − 1] 의 근 (양수 쪽으로 증가). 레일 안 근이 없으면 None."""
    shift = single_input_out_shift(a, r, lam)
    return None if shift is None else -shift


def source_load_kcl_at_vdd(vdd, res, i, v_out0, r, lam):
    """레일 소스 꼴의 R-6c 조건: F(V) = V/R − (1 + r)·I·e^{−lam·(V − V_out0)} 은 V 에 대해 증가하고 F(V_gnd) < 0 이므로 근이 [V_gnd, V_dd] 에 있을 조건은
    F(V_dd) >= 0 이다. 반환 F(V_dd) (음수면 레일 안에 근이 없다). 거울 u = V_dd − V 로 `out_kcl_at_gnd` 와 같은 식(독립 한 줄 식)."""
    return vdd / res - (1.0 + r) * i * math.exp(-lam * (vdd - v_out0))
