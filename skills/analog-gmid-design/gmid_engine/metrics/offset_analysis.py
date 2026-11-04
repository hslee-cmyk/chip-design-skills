"""입력 환산 랜덤 offset 1σ·구조 가드·소자별 기여 표 -- MNA ω → 0 수반 해석 (설계 40 §3.8-8 `offset_in_sigma_mv`·`offset_excess`·`offset_contrib`,
41 §6.4-2, 체크리스트 D-OF1·D-OF2).

진입점: `offset_analysis(ss, view, sigmas, input_cells=(), rel_tols=None, matching=None, nodal=None) -> OffsetAnalysis`. `nodal` = 필드 `graph.ss_nodal` 값 (G 조립 자리는 그 블록 하나 --
`metrics_aux` 가 넘긴다, 단위 호출은 생략하면 같은 조립 함수를 부른다).

식(40 §3.8-8 표): 회로의 **모든 MOS** i 에 독립 게이트 전압 오차원 σ_VGS,i 를 두고 DC 극한 전달로 출력(감지 쌍이면 차)까지 보내 합친 분산을 차동 이득
A_dm 으로 나눈다:  σ²_in = Σ_i (Z_i·gm_i·σ_VGS,i)² / A_dm².  Z_i = 소자 i 채널 전류(d -> s) 단위 -> 출력 전달 = z[s_i] − z[d_i], z = 수반 풀이
(관측 벡터 하나, LU 한 번 -- 소자마다 풀지 않는다, 잡음 해석 41 §7.3 과 같은 adjoint 해).

* 계: 뷰의 고정 노드 = 교류접지 ∪ 입력 포트 ∪ 뷰 구동 넷(`_helpers_view.view_system` -- `metrics_ss` 와 같은 계). 여기는 뷰 가중(차동 ±1/|D|),
  A_dm = 그 여기에서 관측(감지 쌍의 차)의 DC 값 -- gain_ss_db 의 T(0) 와 같은 양(부호 포함).
* `sigmas` = ((소자 라벨, σ_VGS V, σ tol V 또는 None), ...) 모든 MOS 에 대해(호출자가 U3 `mismatch_sigma_vgs` 로 만든다 -- LUT 를 여기서 부르지 않는다).
* `offset_excess` = σ_in / (입력 셀 소자만의 같은 합 σ) -- 입력 셀 = S1v gain 제약 전달 뷰 첫 이득 블록 input 셀(`input_cells`). 구조 가드 `<= √2`
  (부하 분산 ≤ 입력쌍 분산 <=> 전체 분산 ≤ 2·입력 분산). 입력 셀이 없거나 그 분산이 0 이면 None + 사유.
* 소자별 기여 `contrib`: 분산 점유율 큰 순. `matching`(소자 -> matching 그룹 표지) 은 해석용 표지로만 싣는다(계산 대상 아님).
* 분해능(NFR-5, resolution): 한 파라미터씩 LUT 허용오차만큼 흔든 재풀이의 |Δσ_in| 합 -- gm·gmb·gds 를 각각 +ε_i·|p| 로(ε_i = `rel_tols` = (gm/ID)·tol_V,
  metrics CONTRACT 9.1 과 같은 Δp = ε·|p|), mismatch σ_i 는 +tol_mismatch 로. 풀이 상대 잔차 × σ_in 과 큰 쪽(바닥 = 부동소수 해상도). 허용오차가 없는
  소자가 있으면 None.
* 정의 불가(값으로 담는다): 뷰가 전달 뷰가 아님(`unsupported_view`), 감지 노드가 고정 노드뿐(`sense_fixed`), 계 특이(`singular_dc`), A_dm = 0(`gain_zero`),
  σ 가 없는 MOS(`sigma_missing`).
"""
import math
import sys

import numpy
import scipy.linalg

from gmid_engine.core import MV_PER_V

from ._helpers_nodal import nodal_adjoint, nodal_solve
from ._helpers_view import PARAMETER_ORDER, view_factor, view_system
from .aux_types import OffsetAnalysis, OffsetContribution
from .mna_types import Undefined
from .records import MosSmallSignal
from .stamp_mos import mos_stamps

QUANTITY = "sigma_in_mv"


def _undefined(code, detail=()):
    return (Undefined(QUANTITY, code, "definitional", detail),)


def _bare(code, detail=(), a_dm=None):
    return OffsetAnalysis(None, None, a_dm, undefined=_undefined(code, detail))


def _unit_entries(mos, parameter):
    """그 MOS 의 파라미터 하나(0 gm, 1 gmb, 2 gds)를 1 로 둔 스탬프 항목 ((행, 열, 값), ...) -- 스탬프 정본 `mos_stamps` 를 그대로 써서 파라미터 섭동을
    행렬 사본의 항목 가산으로 한다(행렬을 다시 조립하지 않는다)."""
    args = [0.0 for _name in PARAMETER_ORDER]
    args[parameter] = 1.0
    return mos_stamps(MosSmallSignal(mos.d, mos.g, mos.s, mos.b, args[0], args[1], args[2])).g


def offset_analysis(ss, view, sigmas, input_cells=(), rel_tols=None, matching=None, nodal=None):
    system = view_system(ss, view)
    if system is None:
        return _bare("unsupported_view", (("mode", getattr(view, "mode", None)),))
    fixed, drive, sense, _pairs, _decl = system
    if all(int(i) in fixed for i in numpy.nonzero(sense)[0]):
        return _bare("sense_fixed")
    mos = ss.circuit.mos
    sigma_of = {label: (s, t) for label, s, t in sigmas}
    missing = tuple(m.label for m in mos if m.label not in sigma_of)
    if missing:
        return _bare("sigma_missing", (("devices", missing),))
    size = len(ss.nodes)
    factor = view_factor(ss, nodal, fixed)
    volt, residual = nodal_solve(factor, size, drive)
    z = nodal_adjoint(factor, size, sense)
    if volt is None or z is None:
        return _bare("singular_dc")
    a_dm = float(sense @ volt)
    if not abs(a_dm) > 0:
        return _bare("gain_zero", a_dm=a_dm)
    gm = numpy.array([m.gm for m in mos])
    drain = numpy.array([m.d for m in mos], dtype=int)
    source = numpy.array([m.s for m in mos], dtype=int)
    sig = numpy.array([sigma_of[m.label][0] for m in mos])
    z_i = z[source] - z[drain]
    var_out = (gm * sig * z_i) ** 2
    total = float(var_out.sum())
    sigma_in = math.sqrt(total) / abs(a_dm)
    labels = [m.label for m in mos]
    in_set = set(input_cells)
    in_total = float(sum(v for lab, v in zip(labels, var_out) if lab in in_set))
    undefined = ()
    excess = None
    if in_set and in_total > 0:
        excess = math.sqrt(total / in_total)
    else:
        undefined = (Undefined("excess", "input_cell_variance_zero" if in_set else "input_cells_undeclared", "definitional",
                               (("devices", tuple(sorted(in_set))),)),)
    tag = matching or {}
    contrib = tuple(sorted(
        (OffsetContribution(lab, float(v / a_dm ** 2), float(v / total) if total > 0 else 0.0, float(sigma_of[lab][0]), float(zi), tag.get(lab, ""))
         for lab, v, zi in zip(labels, var_out, z_i)),
        key=lambda c: (-c.variance_v2, c.device)))
    state = (factor, volt, z, sense, mos, gm, drain, source, sig, var_out, numpy.array([lab in in_set for lab in labels]))
    res_sigma, res_excess = _resolution(state, labels, sigma_of, rel_tols or {}, sigma_in, excess, residual)
    return OffsetAnalysis(sigma_in * MV_PER_V, excess, a_dm, contrib, None if res_sigma is None else res_sigma * MV_PER_V, res_excess, residual,
                          undefined)


def _ratio(total, in_total):
    return math.sqrt(total / in_total) if in_total > 0 else None


def _resolution(state, labels, sigma_of, tols, sigma_in, excess, residual):
    """분해능 (σ_in [V], excess [무차원]) 또는 (None, None) -- 허용오차가 없으면 정하지 않는다.

    LUT 소신호 허용오차는 한 파라미터씩 Δp = ε·|p| 만큼 흔든 **1차 수반 갱신**이다(금속 재풀이 없음): 스탬프 변화 ΔG = Δp·U(U = 그 소자·파라미터의 단위 스탬프)에 대해
    x' = x − Δp·A⁻¹(U·v)|_미지수, z' = z − Δp·A⁻ᵀ(Uᵀ·z)|_미지수 (A⁻¹ 은 이미 만든 LU 로 한 번 -- 소자·파라미터마다 O(n²) 곱뿐)."""
    factor, volt, z, sense, mos, gm, drain, source, sig, var_out, in_mask = state
    if any(tols.get(lab) is None or sigma_of[lab][1] is None for lab in labels):
        return None, None
    unknown, lu, piv = factor[0], factor[1], factor[2]
    total = float(var_out.sum())
    in_total = float(var_out[in_mask].sum())
    a_abs = math.sqrt(total) / sigma_in
    position = {int(node): k for k, node in enumerate(unknown)}
    inverse = scipy.linalg.lu_solve((lu, piv), numpy.eye(len(unknown))) if len(unknown) else numpy.zeros((0, 0))
    sum_sigma, sum_excess = 0.0, 0.0
    for i, m in enumerate(mos):
        eps = tols[labels[i]]
        for parameter, value in zip(range(len(PARAMETER_ORDER)), (m.gm, m.gmb, m.gds)):
            if value == 0.0 or eps == 0.0:
                continue
            step = eps * value
            r = numpy.zeros(len(unknown))
            w = numpy.zeros(len(unknown))
            for row, col, unit in _unit_entries(m, parameter):
                if row in position:
                    r[position[row]] += unit * volt[col]
                if col in position:
                    w[position[col]] += unit * z[row]
            v1, z1 = volt.copy(), z.copy()
            v1[unknown] -= step * (inverse @ r)
            z1[unknown] -= step * (inverse.T @ w)
            gm1 = gm.copy()
            if parameter == 0:
                gm1[i] += step
            var1 = (gm1 * sig * (z1[source] - z1[drain])) ** 2
            a1 = float(sense @ v1)
            if not abs(a1) > 0:
                return None, None
            t1 = float(var1.sum())
            sum_sigma += abs(math.sqrt(t1) / abs(a1) - sigma_in)
            ratio = _ratio(t1, float(var1[in_mask].sum()))
            if excess is not None and ratio is not None:
                sum_excess += abs(ratio - excess)
    # mismatch σ_i 허용오차(LUT tol_mismatch): σ_i -> σ_i + tol 이면 그 소자 분산이 (1 + tol/σ_i)² 배
    for i, lab in enumerate(labels):
        s_i, tol_i = sigma_of[lab]
        if s_i == 0.0:
            continue
        extra = var_out[i] * ((1.0 + tol_i / s_i) ** 2 - 1.0)
        t1 = total + extra
        sum_sigma += abs(math.sqrt(t1) / a_abs - sigma_in)
        ratio = _ratio(t1, in_total + (extra if in_mask[i] else 0.0))
        if excess is not None and ratio is not None:
            sum_excess += abs(ratio - excess)
    floor = max(residual, sys.float_info.epsilon)
    return max(sum_sigma, floor * sigma_in), (None if excess is None else max(sum_excess, floor * excess))
