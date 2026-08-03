#!/usr/bin/env python
"""sizing_recipe.py — gm/ID sizing template (Jespers gm/ID methodology).

이 파일은 §1(LUT 인터페이스)만 "완성된 도구가 아닌 템플릿"이다 — `SemiEmpiricalGmIdLUT`에
자신의 공정 4D 스윕 데이터를 채우면(또는 `build_toy_lut()`처럼 E.K.V. 해석식으로 합성 LUT를
만들면) 나머지는 그대로 실행된다. 방법론 근거: ../references/gm-id-methodology.md
(§2.2 핵심 sizing 방정식, §4 설계 절차, §4.2 기생 커패시턴스 반복), 보간 알고리즘 근거:
../references/lut-generation-checklist.md §7.

사용 흐름 (SKILL.md §1 6단계와 1:1 대응):
    1. gm = 2*pi*fT*C                      -> gm_from_fT()
    2. gm/ID 선택 (moderate inversion 출발) -> 사용자가 스칼라/배열로 지정
    3. ID = gm / (gm/ID)                    -> size_transistor()
    4. W  = L * ID / IDu                    -> size_transistor()
    5. 기생 CJD 반영 반복                    -> converge_with_parasitics()
    6. 검증(f_nqs, gain, slew-rate)          -> check_quasi_static()

"주어진 gm/ID에서 결과가 어떻게 되는가"를 넘어 "스펙을 만족하는 최적 sizing을 찾아라"가 필요하면
`find_optimal_sizing()`(§5) — 단일 소자, (L,VDS,gm/ID) 격자 전체를 스윕해 제약조건(gain_min/
w_max/준정적)을 만족하는 점 중 목적함수(전력 또는 면적) 최소인 것을 반환한다(이산 격자 탐색).

다단 회로(2단 Miller OTA 등)는 `optimize_multistage()`(§6) — 토폴로지별 위상보상 방정식을
`topology_fn` 콜백(예: `miller_ota_topology()`)으로 분리한 **제네릭** 엔진이라, 새 토폴로지를
추가할 때 이 엔진을 다시 짤 필요 없이 topology_fn 하나만 새로 쓰면 된다. real sky130 데이터로
실증된 사례는 ../references/sky130-worked-example.md 참조.

주의: 이 스크립트는 sizing "출발점"을 계산할 뿐이다 — 최종 확인은 항상 SPICE/Spectre로 한다
(방법론 문서 §4.5, 정직한 한계). `SemiEmpiricalGmIdLUT`는 numpy가 필요하다(다른 함수는 불필요).
"""
from __future__ import annotations
import itertools
import json
import math
import operator
from collections import defaultdict
from dataclasses import asdict, dataclass, field, is_dataclass, replace as _dc_replace
from typing import Callable


# ---------------------------------------------------------------------------
# 1) LUT 인터페이스 — 공정별 데이터/모델은 서브클래스가 채운다
# ---------------------------------------------------------------------------

class GmIdLUT:
    """공정별 gm/ID lookup table 인터페이스.

    `gm_id_to_id_density`/`gm_gds_ratio`는 공정 데이터 없이는 계산할 수 없으므로 서브클래스
    책임(semi-empirical LUT는 `SemiEmpiricalGmIdLUT` 참조, model-driven이면 E.K.V. 파라미터로
    직접 구현). `junction_cap`은 Jespers Annex 2(jctCap) 공식이 공정 독립적으로 쓸 만한 1차
    근사이므로 기본 구현을 제공한다 — 필요하면 오버라이드한다.
    """

    def gm_id_to_id_density(self, gm_id: float, L: float, vds: float, vs: float = 0.0) -> float:
        """주어진 gm/ID에 대응하는 단위 전류밀도 IDu(=ID/W, 기준 소자 기준)를 반환.

        semi-empirical: 4D 테이블에서 (L, VGS, vds, vs) 격자를 gm/ID 축으로 재파라미터화한 뒤
                         interpolation (`SemiEmpiricalGmIdLUT` 참조).
        model-driven:   E.K.V. 해석식으로 직접 계산 (방법론 §2.4, §4.3).
        """
        raise NotImplementedError("자신의 LUT 또는 E.K.V. 파라미터로 구현하세요 — "
                                   "gm-id-methodology.md §2.4/§3.4/§4.3 참조. "
                                   "4D 스윕 데이터가 있다면 SemiEmpiricalGmIdLUT를 바로 쓰세요.")

    def gm_gds_ratio(self, gm_id: float, L: float, vds: float, vs: float = 0.0) -> float:
        """intrinsic gain gm/gds = (gm/ID)*VA. LUT의 GDS 열에서 유도(방법론 §2.5)."""
        raise NotImplementedError("자신의 LUT로 구현하세요 (또는 SemiEmpiricalGmIdLUT 사용)")

    def junction_cap(self, L: float, W: float, n_fingers: int = 1, V: float = 0.0,
                      CJ: float = 1e-15, CJsw: float = 1e-16, CJswg: float = 3e-16) -> float:
        """드레인 접합 커패시턴스 CJD — Jespers Annex 2 jctCap() 공식 기반 근사(1차 견적).

        단위: CJ[F/um^2](면적), CJsw[F/um](측면 둘레), CJswg[F/um](게이트측 둘레),
        기본값은 원문 예시 unit-cap(1e-15/1e-16/3e-16). L,W는 um 단위로 넘긴다.
        n_fingers>1이면 폭을 병렬 분할해 측면 둘레를 줄인다(방법론 §4.2 partitioning).
        V(접합 역바이어스, V)가 주어지면 (1+V/0.5)^-0.5 로 감쇠 근사(원문 계수 0.5V 기준).

        ⚠️ 이것은 기하학적 1차 근사다 — 실제 partitioning(최소/최대 R 기준 sub-transistor 개수
        결정) 세부는 재현하지 않는다. 정확한 값은 공정 PDK의 junction cap 모델을 쓴다.
        """
        w_sub = W / n_fingers
        area = L * W
        perim_sw = 2 * (w_sub + L) * n_fingers
        perim_swg = W
        cj_total = CJ * area + CJsw * perim_sw + CJswg * perim_swg
        derate = (1 + V / 0.5) ** (-0.5) if V > 0 else 1.0
        return cj_total * derate


# ---------------------------------------------------------------------------
# 2) 핵심 sizing 방정식 (방법론 §2.2, §4.1 — 변경 금지, LUT만 갈아끼운다)
# ---------------------------------------------------------------------------

def gm_from_fT(fT: float, C: float) -> float:
    """gm = 2*pi*fT*C  (방법론 식 1.6/1.7 — fT 스펙이 gm을 고정한다)."""
    return 2 * math.pi * fT * C


@dataclass
class SizingResult:
    gm: float
    gm_id: float
    ID: float
    W: float
    gain: float | None = None


def size_transistor(gm: float, gm_id: float, L: float, lut: GmIdLUT,
                     vds: float, vs: float = 0.0) -> SizingResult:
    """방법론 식 1.17/1.18: ID = gm/(gm/ID),  W = L * ID / IDu."""
    ID = gm / gm_id
    IDu = lut.gm_id_to_id_density(gm_id, L, vds, vs)
    if IDu <= 0:
        raise ValueError("IDu<=0 — LUT 보간 범위를 벗어났을 가능성 (gm_id/vds 확인)")
    W = L * ID / IDu
    return SizingResult(gm=gm, gm_id=gm_id, ID=ID, W=W)


def converge_with_parasitics(fT: float, C_external: float, gm_id: float, L: float,
                              lut: GmIdLUT, vds: float, vs: float = 0.0,
                              n_fingers: int = 1, max_iter: int = 10, tol: float = 1e-4
                              ) -> SizingResult:
    """방법론 §4.2 — 외부부하 C_external에 기생 CJD를 더해가며 수렴할 때까지 반복.

    ⚠️ weak inversion 쪽으로 gm/ID를 너무 크게 잡으면 W가 급증해 CJD가 C_external을
    압도하고, ID가 다시 커지는 방향으로 반전될 수 있다(방법론 §4.2) — 그 경우 gm/ID를
    moderate inversion 쪽으로 낮추는 것을 검토한다.
    """
    C = C_external
    result = None
    for _ in range(max_iter):
        gm = gm_from_fT(fT, C)
        result = size_transistor(gm, gm_id, L, lut, vds, vs)
        cjd = lut.junction_cap(L * 1e6, result.W * 1e6, n_fingers)  # jctCap은 um 단위 기대, F 반환
        C_new = C_external + cjd
        if C_new > 20 * C_external:
            # 방법론 §4.2가 경고하는 바로 그 현상: weak inversion 쪽으로 너무 깊이 들어가면
            # W(→CJD)가 매 반복 더 커지고 다시 gm(→ID→W)을 키우는 양의 되먹임이 발산한다.
            # 조용히 비정상적으로 큰 숫자를 내는 대신 여기서 멈추고 원인을 알려준다.
            raise ValueError(
                f"gm/ID={gm_id:.1f}에서 기생 커패시턴스 반복이 발산합니다 "
                f"(CJD가 외부부하 C_external의 {C_new / C_external:.0f}배로 증가) — "
                "moderate inversion 쪽으로 gm/ID를 낮추세요 (방법론 §4.2).")
        if abs(C_new - C) < tol * C_external:
            C = C_new
            break
        C = C_new
    result.gain = lut.gm_gds_ratio(gm_id, L, vds, vs)  # A = gm/gds, 방법론 식 6.1 형태
    return result


# ---------------------------------------------------------------------------
# 3) 검증 (방법론 §4.5, §5.3 — SKILL.md §5 체크리스트에 대응)
# ---------------------------------------------------------------------------

@dataclass
class QuasiStaticVerdict:
    ok: bool


def check_quasi_static(fT: float, gm: float, Cgg: float, margin: float = 0.1) -> QuasiStaticVerdict:
    """f_nqs = gm/(2*pi*Cgg); fT <= margin * f_nqs 이어야 준정적 가정이 성립."""
    f_nqs = gm / (2 * math.pi * Cgg)
    return QuasiStaticVerdict(ok=fT <= margin * f_nqs)


def slew_rate(ID: float, C: float) -> float:
    """slew-rate = ID/C = omega_T/(gm/ID)  (방법론 식 6.10)."""
    return ID / C


# ---------------------------------------------------------------------------
# 4) SemiEmpiricalGmIdLUT — 4D (L,VGS,VDS,VS) 배열 기반 실제 동작 구현
#    보간 알고리즘 근거: lut-generation-checklist.md §7 (analytic-derivative 재사용,
#    weak inversion은 ln(ID) 축, 불균등 L 격자 지원). scipy 없이 순수 numpy로 구현.
# ---------------------------------------------------------------------------

def _multilinear_interp(grids, values, points):
    """N차원 격자 다중선형보간(순수 numpy, scipy 불필요, 불균등 monotonic 격자 지원).

    grids: 각 축의 1D 오름차순 배열 튜플(길이 N). values: grids로 색인되는 N차원 배열.
    points: (M, N) 조회 좌표 배열. 반환: (M,) 보간값.
    """
    import numpy as np
    points = np.atleast_2d(np.asarray(points, dtype=float))
    ndim = len(grids)
    idx_lo, frac = [], []
    for d in range(ndim):
        g = np.asarray(grids[d], dtype=float)
        x = np.clip(points[:, d], g[0], g[-1])
        i = np.clip(np.searchsorted(g, x, side="right") - 1, 0, len(g) - 2)
        idx_lo.append(i)
        denom = g[i + 1] - g[i]
        frac.append(np.where(denom != 0, (x - g[i]) / np.where(denom == 0, 1, denom), 0.0))
    result = np.zeros(points.shape[0])
    for corner in range(2 ** ndim):
        weight = np.ones(points.shape[0])
        idx = []
        for d in range(ndim):
            bit = (corner >> d) & 1
            weight = weight * (frac[d] if bit else (1 - frac[d]))
            idx.append(idx_lo[d] + bit)
        result = result + weight * values[tuple(idx)]
    return result


class SemiEmpiricalGmIdLUT(GmIdLUT):
    """4D (L,VGS,VDS,VS) 스윕 데이터 기반 실제 LUT 구현 (numpy 필요).

    - L/VDS/VS 축: 선형 다중보간(불균등 L 격자 그대로 지원).
    - ID 축: ln(ID) 공간에서 보간(weak inversion 지수특성 → 선형오차 방지, checklist §7.2).
    - gm/ID 역조회(목표 gm/ID로부터 VGS를 찾는 것): VGS 격자 전체에서 gm/ID(VGS)를 평가한 뒤
      단조성(gm/ID는 VGS에 단조감소)을 이용해 1D 역보간(np.interp)한다.

    ⚠️ 이 구현은 L/VDS/VS/VGS 네 축 모두 "선형" 보간이다. lut-generation-checklist.md §7.1은
    VGS 축에 LUT가 이미 갖고 있는 gm(=정확한 도함수)을 기울기로 쓰는 cubic-Hermite를 권장한다 —
    더 성긴 VGS 격자에서도 높은 정확도가 필요하면 그 방식으로 업그레이드한다. 여기서는 구현
    단순성과 의존성 없음(scipy 불필요)을 택했다 — VGS 격자를 충분히 촘촘히(예 10~25mV) 스윕하면
    선형 보간도 실용적으로 충분하다.
    """

    def __init__(self, L_grid, VGS_grid, VDS_grid, VS_grid, ID, GM, GDS, CGG, W_ref=None,
                 SID_1F=None):
        """W_ref: ID/GM/GDS/CGG 배열이 실제로 어느 폭에서 측정/합성됐는지.

        - `None`(기본값): `build_toy_lut()`처럼 이미 "W*=L"(단위 소자, W/L=1) 관례로 합성된
          LUT용 — ID 배열이 이미 "W=L일 때의 전류"이므로 추가 스케일링이 필요 없다.
        - 숫자(예 `5e-6`): sky130_lut_sweep.py 등 **고정 기준폭**(예 5µm)으로 스윕한 실측 LUT용 —
          ID 배열은 "그 고정폭에서의 전류"이므로 `size_transistor()`의 `W=L*ID/IDu` 식이 기대하는
          "W/L=1 기준 전류"로 변환하려면 `raw_ID * L/W_ref`가 필요하다(아래 `gm_id_to_id_density`/
          `cgg_absolute` 참고). **sky130 실측 데이터로 이 클래스를 만들 때는 반드시 지정할 것**
          (빠뜨리면 W가 L/W_ref배만큼 실제보다 작게 계산되는 버그 — 2026-07 세션에서 NMCNR
          SPICE 검증 중 발견: 목표 전류를 실제로 흘릴 수 없어 DC 동작점이 발산했다).
        """
        import numpy as np
        self.np = np
        self.L_grid = np.asarray(L_grid, dtype=float)
        self.VGS_grid = np.asarray(VGS_grid, dtype=float)
        self.VDS_grid = np.asarray(VDS_grid, dtype=float)
        self.VS_grid = np.asarray(VS_grid, dtype=float)
        self.grids = (self.L_grid, self.VGS_grid, self.VDS_grid, self.VS_grid)
        self.ID = np.asarray(ID, dtype=float)
        self.GM = np.asarray(GM, dtype=float)
        self.GDS = np.asarray(GDS, dtype=float)
        self.CGG = np.asarray(CGG, dtype=float)
        self.W_ref = None if W_ref is None else float(W_ref)
        # SID_1F(배치 7-3g, 2026-07-31 신설): 1Hz 기준 게이트환산 1/f 노이즈 밀도(V^2/Hz),
        # W_ref에서 측정된 값 — 선택 필드다. 없으면 None으로 두고, noise_1f_density() 호출 시
        # 조용히 0을 반환하는 대신 명시적 ValueError를 낸다(§1.5: 데이터 없음을 숨기지 않음).
        self.SID_1F = None if SID_1F is None else np.asarray(SID_1F, dtype=float)
        expected = (len(self.L_grid), len(self.VGS_grid), len(self.VDS_grid), len(self.VS_grid))
        if self.ID.shape != expected:
            raise ValueError(f"ID 배열 shape {self.ID.shape} != 격자 shape {expected}")
        if self.SID_1F is not None and self.SID_1F.shape != expected:
            raise ValueError(f"SID_1F 배열 shape {self.SID_1F.shape} != 격자 shape {expected}")

    def _w_ref_effective(self, L: float) -> float:
        """이 L에서 ID/CGG 배열이 측정된 실제 기준폭. W_ref=None이면 단위소자(W*=L) 관례."""
        return L if self.W_ref is None else self.W_ref

    def _query(self, array, L, vgs, vds, vs):
        return _multilinear_interp(self.grids, array, [[L, vgs, vds, vs]])[0]

    def _gm_id_curve(self, L, vds, vs):
        """고정 (L,vds,vs)에서 VGS 격자 전체에 대한 (ID, gm/ID) 배열을 반환 (역조회용)."""
        np = self.np
        n = len(self.VGS_grid)
        pts = np.column_stack([
            np.full(n, L), self.VGS_grid, np.full(n, vds), np.full(n, vs),
        ])
        id_vals = np.exp(_multilinear_interp(self.grids, np.log(np.clip(self.ID, 1e-18, None)), pts))
        gm_vals = _multilinear_interp(self.grids, self.GM, pts)
        gm_id_vals = gm_vals / np.clip(id_vals, 1e-18, None)
        return id_vals, gm_id_vals

    def _solve_vgs(self, gm_id: float, L: float, vds: float, vs: float) -> float:
        """목표 gm/ID를 만족하는 VGS를 격자 위에서 역보간으로 찾는다 (gm/ID는 VGS에 단조감소)."""
        np = self.np
        _, gm_id_vals = self._gm_id_curve(L, vds, vs)
        order = np.argsort(gm_id_vals)  # np.interp는 오름차순 x를 요구
        gm_id_sorted, vgs_sorted = gm_id_vals[order], self.VGS_grid[order]
        if gm_id < gm_id_sorted[0] or gm_id > gm_id_sorted[-1]:
            raise ValueError(
                f"gm_id={gm_id:.3g}가 LUT 범위[{gm_id_sorted[0]:.3g},{gm_id_sorted[-1]:.3g}] 밖 — "
                "VGS 스윕 범위를 넓히거나 moderate/weak inversion 쪽 gm/ID로 조정하세요.")
        return float(np.interp(gm_id, gm_id_sorted, vgs_sorted))

    def gm_id_to_id_density(self, gm_id: float, L: float, vds: float, vs: float = 0.0) -> float:
        """size_transistor()의 `W=L*ID/IDu`가 기대하는 "W/L=1 기준 전류"를 반환.

        실측 LUT(W_ref가 고정폭)는 그 폭에서 잰 전류를 raw로 갖고 있으므로 `*L/W_ref`로
        환산해야 한다(`_w_ref_effective` 참고) — 이걸 빠뜨리면 W가 L/W_ref배 작게 나온다.

        ⚠️ **이 반환값(IDu)을 SPICE로 "직접" 검증하지 말 것** (2026-07-24, 실제로 40분을 날린
        실수 — `sky130-worked-example.md` §3 참고): IDu는 "W=L 기준" 전류이지 "W_ref(예 5µm)에서
        실제 SPICE로 잰 전류"가 아니다. `W=W_ref`짜리 소자를 SPICE에 인스턴스화해서 나온 전류를
        이 함수의 반환값과 그냥 나란히 비교하면 **정확히 W_ref/L배 차이가 나는 게 정상**이고, 이걸
        "LUT가 SPICE보다 N배 틀렸다"는 버그로 오인하기 쉽다(실제로 이 세션에서 그렇게 오인해 멀쩡한
        LUT를 스테일 데이터로 의심하고 전체 재스윕까지 실행했었다). LUT를 SPICE와 대조하려면 반드시
        `W = L*ID_target/이 함수의 반환값`으로 사이징한 뒤 **그 W로** SPICE 인스턴스화해서
        `ID_target`이 나오는지 확인할 것 — 정규화가 그 계산 안에서 스스로 상쇄되므로 그렇게 하면
        일치해야 정상이다.
        """
        vgs = self._solve_vgs(gm_id, L, vds, vs)
        raw = math.exp(self._query(self.np.log(self.np.clip(self.ID, 1e-18, None)), L, vgs, vds, vs))
        return raw * L / self._w_ref_effective(L)

    def cgg_absolute(self, gm_id: float, L: float, vds: float, vs: float, W_target: float) -> float:
        """목표 폭 W_target을 갖는 실제 소자의 절대 Cgg(패럿) — LUT는 기준폭에서 잰 값만
        갖고 있으므로 `W_target/W_ref`로 스케일링한다. 다단 회로에서 다음 단 게이트 커패시턴스를
        feedback으로 쓸 때(예 Miller OTA의 prev_cggs) 반드시 이 함수를 쓸 것 — `_query(CGG,...)`를
        직접 쓰면 기준폭(예 5um)의 Cgg를 실제 목표폭(수백 um)의 Cgg인 것처럼 잘못 쓰게 된다.
        """
        vgs = self._solve_vgs(gm_id, L, vds, vs)
        raw = self._query(self.CGG, L, vgs, vds, vs)
        return raw * W_target / self._w_ref_effective(L)

    def gm_gds_ratio(self, gm_id: float, L: float, vds: float, vs: float = 0.0) -> float:
        vgs = self._solve_vgs(gm_id, L, vds, vs)
        gm = self._query(self.GM, L, vgs, vds, vs)
        gds = self._query(self.GDS, L, vgs, vds, vs)
        return gm / gds

    def fT(self, gm_id: float, L: float, vds: float, vs: float = 0.0) -> float:
        """fT = gm/(2*pi*Cgg) — 방법론 §2.6, 준정적 검증에 사용."""
        vgs = self._solve_vgs(gm_id, L, vds, vs)
        gm = self._query(self.GM, L, vgs, vds, vs)
        cgg = self._query(self.CGG, L, vgs, vds, vs)
        return gm / (2 * math.pi * cgg)

    def vgs_for_gm_id(self, gm_id: float, L: float, vds: float, vs: float = 0.0) -> float:
        """목표 gm/ID를 만족하는 VGS 자체가 필요한 호출자를 위한 공개 래퍼(`_solve_vgs()`와
        동일 계산) — diode-stack KVL 역산(C엔진, `solve_diode_stack_current()`, §7.3.2,
        배치 7-3/2026-07-31)처럼 VGS 절대값이 직접 필요한 새 호출자가 생겨 공개 인터페이스로
        추가했다(이전엔 클래스 내부 전용이었다)."""
        return self._solve_vgs(gm_id, L, vds, vs)

    def noise_1f_density(self, gm_id: float, L: float, vds: float, vs: float,
                          W_target: float, freq: float = 1.0) -> float:
        """배치 7-3g(2026-07-31) — 목표 폭 `W_target`에서 1/f(flicker) 게이트환산 전압잡음
        밀도(V^2/Hz)를 `freq`[Hz]에서 반환. `cgg_absolute()`와 완전히 같은 패턴(보간 재사용,
        `SID_1F`는 1Hz 기준·`W_ref`에서 측정된 값 — `W_ref/W_target`로 스케일링, 1/f
        특성이므로 최종적으로 `/freq`).

        ⚠️ `SID_1F`가 없는 LUT(이 프로젝트의 toy LUT/`sky130_nfet_pfet_lut_sample.npz` 전부
        해당 — 아직 `.noise` 해석을 포함한 재스윕이 안 됨, do.md 배치 7-3g "검토 필요" 참고)
        에서 호출하면 즉시 `ValueError`를 낸다 — 데이터가 없다고 조용히 0을 반환하지 않는다
        (§1.5 원칙)."""
        if self.SID_1F is None:
            raise ValueError(
                "이 LUT엔 SID_1F(1/f 노이즈) 배열이 없다 -- sky130_lut_sweep.py를 .noise 해석 "
                "포함해 재실행한 뒤 SemiEmpiricalGmIdLUT(..., SID_1F=...)로 다시 생성하세요 "
                "(analog-topology-json-library.do.md 배치 7-3g 참고).")
        vgs = self._solve_vgs(gm_id, L, vds, vs)
        raw = self._query(self.SID_1F, L, vgs, vds, vs)
        sid_1hz_at_target = raw * self._w_ref_effective(L) / W_target
        return sid_1hz_at_target / freq


# ---------------------------------------------------------------------------
# 5) 단일 소자 그리드서치 최적화 — "주어진 스펙에서 최적 sizing" 자동 탐색
#    (L, VDS, gm/ID) 격자 전체를 스윕해 제약조건을 만족하는 점 중 목적함수 최소인 것을 고른다.
#    이 세션 내내 손으로 하던 "gm/ID 후보 몇 개 계산해서 비교"를 자동화한 것 — 격자점으로만
#    답이 나오는 이산 탐색이다(연속 최적점이 필요하면 scipy.optimize로 확장, 다단 회로의
#    2D sizing space 접점 탐색은 아직 범위 밖 — gm-id-methodology.md §6.4/§10 참조).
# ---------------------------------------------------------------------------

def find_optimal_sizing(lut: "SemiEmpiricalGmIdLUT", L_candidates, VDS_candidates, gm_id_grid,
                         fT: float | None = None, C: float | None = None, gm: float | None = None,
                         objective: str = "power", gain_min: float | None = None,
                         w_max: float | None = None, quasi_static_margin: float = 0.1,
                         vs: float = 0.0):
    """(L, VDS, gm/ID) 격자를 전부 스윕해 제약조건을 만족하는 점 중 objective 최소인 것을 반환.

    gm을 고정할 방법 두 가지: (fT,C) 지정 -> gm=2*pi*fT*C (단일 스테이지, §1 절차 그대로) 또는
    gm을 직접 지정(다단 회로에서 위상보상 방정식이 이미 gm_i를 정해준 경우 — optimize_2stage_
    miller_ota()가 이렇게 쓴다). fT를 지정하면 준정적 조건(fT<=margin*f_nqs)도 같이 검사한다.

    objective: "power"(ID 최소) 또는 "area"(W 최소) — 방법론 §5.1 트레이드오프 삼각형의
    두 축에 대응. gain_min/w_max/quasi_static_margin은 §5 검증 체크리스트 항목을 그대로
    제약조건화한 것.

    반환: (best, all_candidates). best는 dict(L,VDS,gm_id,ID,W,gain,fnqs_ok,feasible) 또는
    실행가능점이 없으면 None. all_candidates는 스윕한 전체 점(탐색 투명성 확보 — best 하나만
    보지 말고 feasible 집합 전체를 살펴보면 사실상의 Pareto 후보군을 알 수 있다).
    """
    if gm is None:
        if fT is None or C is None:
            raise ValueError("gm을 직접 주거나, (fT, C) 쌍을 지정해야 합니다.")
        gm = gm_from_fT(fT, C)
    all_candidates = []
    best = None
    for L in L_candidates:
        for VDS in VDS_candidates:
            for gm_id in gm_id_grid:
                try:
                    IDu = lut.gm_id_to_id_density(gm_id, L, VDS, vs)
                    ID = gm / gm_id
                    W = L * ID / IDu
                    gain = lut.gm_gds_ratio(gm_id, L, VDS, vs)
                    fnqs_ok = True
                    if fT is not None:
                        Cgg = lut.cgg_absolute(gm_id, L, VDS, vs, W)
                        fnqs_ok = check_quasi_static(fT, gm, Cgg, quasi_static_margin).ok
                except (ValueError, ZeroDivisionError):
                    continue
                feasible = (
                    (gain_min is None or gain >= gain_min)
                    and (w_max is None or W <= w_max)
                    and fnqs_ok
                )
                cand = dict(L=L, VDS=VDS, gm_id=gm_id, ID=ID, W=W, gain=gain,
                            fnqs_ok=fnqs_ok, feasible=feasible)
                all_candidates.append(cand)
                if feasible:
                    obj_val = ID if objective == "power" else W
                    best_val = (best["ID"] if objective == "power" else best["W"]) if best else None
                    if best is None or obj_val < best_val:
                        best = cand
    return best, all_candidates


# ---------------------------------------------------------------------------
# 6) 다단 회로 최적화 — 제네릭 엔진(재사용) + 토폴로지별 topology_fn 콜백(교체 대상)
#    "토폴로지가 바뀌면 항상 새 함수를 짜야 하나?" -> 아니다. 바뀌는 건 위상보상 방정식뿐이라
#    그 부분만 작은 콜백으로 분리했다. 새 토폴로지 = 새 topology_fn(몇 줄), 새 엔진 아님.
# ---------------------------------------------------------------------------

def optimize_multistage(topology_fn, luts, L_candidates, VDS_candidates, gm_id_grid,
                         objective: str = "power", gain_min=None, w_max=None,
                         max_iter: int = 10, tol: float = 1e-3,
                         shared_gm_id_groups: list | None = None):
    """제네릭 다단 회로 최적화 엔진 — **토폴로지가 바뀌어도 이 함수는 그대로 재사용**한다.

    다단 회로마다 다른 건 "스펙 → 각 스테이지 필요 gm" 관계식(위상보상 방정식)뿐이고, 그 gm을
    (L,VDS,gm/ID)로 구현하는 부분(find_optimal_sizing)과 기생커패시턴스 반복 수렴 구조(§4.2의
    회로 레벨 버전)는 토폴로지 무관이다. 그래서 토폴로지별 방정식을 `topology_fn`이라는 작은
    콜백으로 분리했다 — 새 토폴로지 하나 추가할 때 이 엔진을 다시 짤 필요 없이 topology_fn
    하나만 새로 쓰면 된다(예: `miller_ota_topology()` 참고, 몇 줄짜리 함수다).

    topology_fn(prev_cggs) -> list[gm_i]:
        prev_cggs는 직전 반복에서 각 스테이지가 얻은 Cgg 리스트(첫 반복엔 None — 이때
        topology_fn은 스스로 초기 기생캐패시턴스 추정치를 써서 초기 gm을 내야 한다).
        토폴로지의 위상보상 방정식(Cm 계산, gm1=wT*Cm 등)을 이 함수 안에 넣는다.

    luts: 스테이지별 LUT 리스트(길이 = 스테이지 수, topology_fn이 반환하는 gm 리스트와 순서 대응).
    gain_min/w_max: 스칼라(전 스테이지 공통) 또는 스테이지별 리스트.

    ⚠️ **모든 토폴로지에 폐형해(gm_i 전부가 스펙만으로 유일하게 정해짐)가 있는 건 아니다** —
    Miller OTA(Z,NDP 지정 시)는 운 좋게 gm1,gm2가 유일하게 정해지지만, NGCC(§10.2)의 gm1,gm2는
    원래 비용함수 최적화(ellipse-line 접점, eq 8a/8b)가 필요해서 이 세션에서도 완전 재현하지
    못했다 — 그런 토폴로지는 topology_fn 안에 "남은 자유도를 고정하는 합리적 근사"(예: 고정
    비율, 혹은 그 자유도에 대한 작은 보조 그리드서치)를 직접 넣어야 한다. 이건 이 아키텍처의
    한계가 아니라 회로 이론 자체의 한계다 — Jespers/NGCC 원문도 이 지점에서 MATLAB
    contour-plot/수치최적화로 넘어간다.

    ⚠️ **objective="power"엔 반드시 w_max를 같이 줘라**: gm_i가 topology_fn에서 이미 고정되므로
    ID=gm/(gm/ID)는 L·VDS와 무관하다 — "전력 최소화"는 사실상 "gm/ID를 격자 최대치로 최대화"와
    같아진다. w_max 없이 돌리면 W가 수백만 um으로 발산한다(sky130-worked-example.md에서 반복
    확인된 현상 — 버그가 아니라 물성).

    - PM(위상마진) 등 회로 레벨 성능은 검증하지 않는다 — topology_fn이 구현하는 방정식이 이미
      "PM 60~70도가 되는 값"이라고 가정할 뿐, 최종 회로의 실제 PM은 SPICE로 확인해야 한다.

    ⚠️ **한계 순환(limit cycle) 대응**: `find_optimal_sizing()`의 `objective="power"` 동점 처리는
    같은 gm_id에서 동점인 (L,VDS) 후보 중 하나를 격자 순서로 고른다(배치 7-1에서 처음 확인된
    "동점은 격자 순서에 의존" 특성). 이 때문에 Cgg 되먹임이 매 반복 미세하게 다른 값으로 바뀌면
    동점 승자가 바뀌면서 단일 고정점이 아니라 **주기적 순환**(예: gm이 3개 값을 계속 순환)에
    빠질 수 있다(current_reuse_telescopic_topology()에서 최초 실측, 2026-07-31). tie-break
    규칙 자체를 바꾸면 이미 확정된 sky130_regression_reference.json 골든값이 흔들릴 위험이 있어
    건드리지 않는다 — 대신 `max_iter`를 다 써도 1-스텝 수렴에 실패하면 최근 이력에서 반복되는
    주기(period)를 탐지하고, 그 주기 구간의 gm 평균을 다시 한 번 sizing해 "안정된 추정치"로
    반환한다(`cycle_detected=True`, `cycle_period=p`). 순환 자체를 없애는 게 아니라 순환 중인 값
    대신 재현 가능한 대표값을 주는 것 — 최종 회로 성능은 여전히 SPICE로 확인해야 한다.

    shared_gm_id_groups(2026-08-03, 배치 7-5 실행 중 발견): `list[list[int]]`, 예 `[[0,1]]` —
    스테이지 인덱스 그룹 중 **물리적으로 같은 직렬 KCL 전류경로**(예: current-reuse 토폴로지의
    PMOS/NMOS 입력쌍이 한 branch를 공유)라 ID까지 같아야 하는 경우에만 지정한다(gm만 같은
    diff pair는 각자 독립 전류라 여기 해당하지 않음 — 그건 그냥 별개 스테이지). 지정된
    그룹은 (L,VDS)는 스테이지(=kind)별로 각자 찾되 **gm_id 하나를 공유**해서 사이징한다 —
    `gm`이 같은 스테이지끼리 묶었다면(topology_fn이 그렇게 만든다) gm_id가 같으면
    `ID=gm/gm_id`도 자동으로 같아진다(KCL이 요구하는 바로 그 조건). 지정하지 않은 스테이지는
    기존과 동일하게 완전히 독립적으로(각자 최적 gm_id) 사이징된다 — 하위호환 100% 보장.
    ⚠️ 발견 경위: `current_reuse_telescopic_topology()`가 반환하는 gmp(M1a/M1b)/gmn(M4a/M4b)는
    Eq.5로 gm은 같게 강제되지만, 이 둘의 실제 디바이스(M1a→M2a→M3a→M4a)는 하나의 물리적
    직렬 스택이라 ID까지 반드시 같아야 한다 — 종전 구현은 두 스테이지를 완전히 독립적으로
    최적화해 서로 다른 gm_id(→다른 ID)를 골라도 몰랐다(`optimize_full_circuit_budget()`을
    이 회로 51개 소자 전체에 처음 실행하면서 A엔진의 KCL 위반 에러로 실측 발견 — 이전
    self-test는 toy LUT로 `optimize_multistage()` 자체의 내부 수렴만 봤지 그 결과를
    `run_topology_pipeline()`의 stack_id 감사에 넣어본 적이 없어 놓쳤다).

    반환: dict(gms=[gm_i,...], stages=[find_optimal_sizing 결과,...], cggs=[...], iters, converged,
               cycle_detected, [cycle_period])
          또는 어느 스테이지든(혹은 shared_gm_id_groups의 어느 그룹이든) 실행가능점을 못 찾으면
          None.
    """
    def _per_stage(param, i):
        return param[i] if isinstance(param, (list, tuple)) else param

    def _size_stage(i, gm):
        best, _ = find_optimal_sizing(
            luts[i], L_candidates, VDS_candidates, gm_id_grid, gm=gm,
            objective=objective, gain_min=_per_stage(gain_min, i), w_max=_per_stage(w_max, i))
        if best is None:
            return None
        return best

    group_of = {}
    for g in (shared_gm_id_groups or []):
        for i in g:
            group_of[i] = tuple(g)

    def _size_group_at_gm_id(indices, gms, gm_id):
        members = []
        for i in indices:
            best, _ = find_optimal_sizing(
                luts[i], L_candidates, VDS_candidates, [gm_id], gm=gms[i],
                objective="area", gain_min=_per_stage(gain_min, i), w_max=_per_stage(w_max, i))
            if best is None:
                return None
            members.append(best)
        return members

    def _size_shared_group(indices, gms):
        # objective="power": ID=gm/gm_id는 gm_id에만 의존(L/VDS 무관) -- 그룹 내 gm이 전부
        # 같다는 전제(topology_fn이 그렇게 반환) 하에 gm_id가 클수록(=약반전=ID 작음) power가
        # 낮아지므로 내림차순으로 훑어 처음 feasible한 gm_id를 채택한다(단일-스테이지의 "약반전
        # 우선" tie-break와 같은 방향). objective="area"는 전 gm_id를 훑어 그룹 총 W가 최소인
        # 것을 채택한다.
        order = sorted(gm_id_grid, reverse=(objective == "power"))
        best_group, best_val = None, None
        for gm_id in order:
            members = _size_group_at_gm_id(indices, gms, gm_id)
            if members is None:
                continue
            if objective == "power":
                return members  # 내림차순 첫 feasible = 최소 ID(=최소 전력) 후보
            val = sum(m["W"] for m in members)
            if best_val is None or val < best_val:
                best_group, best_val = members, val
        return best_group

    def _size_all(gms):
        """stages/cggs 리스트 계산 -- 공유 gm_id 그룹과 독립 스테이지가 섞여도 처리한다.
        실패 시(어느 스테이지/그룹이든 실행가능점 없음) None."""
        stages = [None] * len(gms)
        handled_groups = set()
        for i in range(len(gms)):
            if i in group_of:
                g = group_of[i]
                if g in handled_groups:
                    continue
                handled_groups.add(g)
                members = _size_shared_group(list(g), gms)
                if members is None:
                    return None
                for gi, best in zip(g, members):
                    stages[gi] = best
            else:
                best = _size_stage(i, gms[i])
                if best is None:
                    return None
                stages[i] = best
        cggs = [luts[i].cgg_absolute(stages[i]["gm_id"], stages[i]["L"], stages[i]["VDS"], 0.0,
                                      stages[i]["W"]) for i in range(len(gms))]
        return stages, cggs

    n = len(luts)
    prev_cggs = None
    prev_gms = None
    gms_history = []
    result = None
    for it in range(max_iter):
        gms = topology_fn(prev_cggs)
        sized = _size_all(gms)
        if sized is None:
            return None  # 이 gm 타깃을 실행가능하게 구현 못함 -> 스펙/격자 재검토 필요
        stages, cggs = sized
        gms_history.append(gms)
        converged = prev_gms is not None and all(
            abs(g - pg) < tol * pg for g, pg in zip(gms, prev_gms))
        result = dict(gms=gms, stages=stages, cggs=cggs, iters=it + 1, converged=converged,
                      cycle_detected=False)
        if converged:
            return result
        prev_cggs, prev_gms = cggs, gms

    # max_iter를 다 썼는데도 수렴 못함 -- 한계 순환인지 확인(위 docstring 참고).
    for p in range(1, len(gms_history) // 2 + 1):
        a, b = gms_history[-p], gms_history[-2 * p]
        if all(abs(x - y) < tol * max(abs(y), 1e-15) for x, y in zip(a, b)):
            avg_gms = [sum(gms_history[-p + k][i] for k in range(p)) / p for i in range(n)]
            sized = _size_all(avg_gms)
            if sized is None:
                return None
            stages, cggs = sized
            return dict(gms=avg_gms, stages=stages, cggs=cggs, iters=max_iter, converged=False,
                        cycle_detected=True, cycle_period=p)
    return result


def _invq_newton(x: float, iters: int = 30) -> float:
    """VP/UT = 2(q-1)+ln(q) 를 q에 대해 뉴턴법으로 역산 (Jespers Annex 2 A2.2.2 invq() 참고).

    E.K.V. 정규화 전하 q를 표면전위식에서 구하는 표준 절차 — 합성(toy) LUT 생성에만 쓰인다.
    """
    q = max(x, 0.05) if x > 0 else 0.05
    for _ in range(iters):
        f = 2 * (q - 1) + math.log(q) - x
        fp = 2 + 1.0 / q
        q = max(q - f / fp, 1e-6)
    return q


def build_toy_lut(n: float = 1.3, UT: float = 0.026, VTo: float = 0.4, ISuo: float = 2e-7,
                   L_grid=(0.18e-6, 0.35e-6, 0.5e-6, 1.0e-6),
                   VGS_step: float = 0.02, VGS_max: float = 1.2,
                   VDS_grid=(0.2, 0.4, 0.6, 0.8, 1.0), VS_grid=(0.0,)) -> SemiEmpiricalGmIdLUT:
    """E.K.V. 해석식으로 만든 합성(toy) 4D LUT — 실제 공정 데이터가 아니라 파이프라인 시연용.

    VA(Early 전압)는 L에 비례하는 매우 단순한 가정(5V/um)이고 CGG도 1차 근사다 — 숫자 자체를
    설계에 쓰지 말 것. 실전에는 lut-generation-checklist.md §7.4의 SPICE 스윕으로 이 함수를
    대체한 뒤 SemiEmpiricalGmIdLUT(...)에 실측 배열을 넣는다.
    """
    import numpy as np
    L = np.asarray(L_grid, dtype=float)
    VGS = np.arange(0.0, VGS_max + 1e-9, VGS_step)
    VDS = np.asarray(VDS_grid, dtype=float)
    VS = np.asarray(VS_grid, dtype=float)
    shape = (len(L), len(VGS), len(VDS), len(VS))
    ID = np.zeros(shape)
    GM = np.zeros(shape)
    GDS = np.zeros(shape)
    CGG = np.zeros(shape)
    Cox_per_um2 = 5e-15  # F/um^2, toy 근사(0.5um 세대 감마-옥사이드 오더)

    for iL, l in enumerate(L):
        l_um = l * 1e6
        VA = 5.0 * l_um  # toy Early voltage: L(um)당 5V (짧을수록 이득 작음, 방향성만 유효)
        for ig, vgs in enumerate(VGS):
            VP = vgs - VTo
            q = _invq_newton(VP / UT) if VP > -3 * UT else 1e-6
            i_norm = q ** 2 + q
            IDu = ISuo * i_norm  # 단위(unary, W*=L) 소자 전류 — size_transistor의 W=L*ID/IDu와 짝
            gm_u = IDu / (n * UT) * (1.0 / (1.0 + q))  # 방법론 식(4.34): gm/ID = 1/(nUT)*1/(1+q)
            cgg_u = Cox_per_um2 * l_um * l_um * (2.0 / 3.0)  # toy: 포화 시 (2/3)Cox*W*L, W*=L 이므로 L^2
            for ivd in range(len(VDS)):
                for ivs in range(len(VS)):
                    ID[iL, ig, ivd, ivs] = max(IDu, 1e-15)
                    GM[iL, ig, ivd, ivs] = gm_u
                    GDS[iL, ig, ivd, ivs] = max(IDu, 1e-15) / VA
                    CGG[iL, ig, ivd, ivs] = cgg_u

    return SemiEmpiricalGmIdLUT(L, VGS, VDS, VS, ID, GM, GDS, CGG)


# ---------------------------------------------------------------------------
# 6.5) topology JSON 오케스트레이션 레이어 (2026-07-28 신설) — I/O만 담당한다. 계산 로직은
#      한 줄도 새로 만들지 않는다 — size_transistor()/optimize_multistage()/topology_library.py
#      함수를 기존 인자 그대로 호출한다. 기존 함수 호출 방식(직접 인자 전달)과 공존한다.
#      정본: docs/02-design/features/analog-topology-json-library.design.md
# ---------------------------------------------------------------------------

from topology_library import (miller_ota_topology, nmcnr_3stage_topology, ngcc_3stage_topology,
                               current_reuse_telescopic_topology)

# topology JSON의 "compensation.function" 문자열이 참조할 수 있는 함수의 명시적 allowlist.
# JSON 안의 임의 문자열로 임의 코드를 실행하지 않기 위함 — eval()/getattr(module, name) 금지.
_COMPENSATION_REGISTRY = {
    "miller_ota_topology": miller_ota_topology,
    "nmcnr_3stage_topology": nmcnr_3stage_topology,
    "ngcc_3stage_topology": ngcc_3stage_topology,
    # current_reuse_telescopic_topology: 2026-07-31 원문(Xie & Chen) PDF를 사용자와 함께
    # 직접 확인해 Eq.2-6을 재도출한 뒤 재등록(이전엔 Eq.6 근거 없이 재구성했다가 되돌림).
    "current_reuse_telescopic_topology": current_reuse_telescopic_topology,
}


def load_sizing_targets(json_path: str) -> dict:
    """instance-output JSON(또는 별도 sizing-spec JSON)에서 gm/ID sizing 목표값(fT/CL/
    gain_target 등)을 읽어 반환한다. `design_spec` 키가 있으면 그 안쪽을, 없으면 파일
    전체를 그대로 반환한다(호출자가 직접 만든 단순 스펙 JSON도 지원)."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("design_spec", data)


def write_sizing_results(json_path: str, results: dict) -> None:
    """`size_transistor()`/`optimize_multistage()` 결과(`{name: SizingResult}`)를
    instance-output JSON의 `"sizing"` 섹션에 병합해 쓴다 — 파일이 없으면 새로 만든다.
    기존에 있던 다른 섹션(`layout`/`floorplan`/`audit_row_split` 등, `stick_diagram.py`의
    `save_instance_json()`이 쓴 것)은 건드리지 않는다."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    sizing = data.setdefault("sizing", {})
    for name, result in results.items():
        sizing[name] = asdict(result) if is_dataclass(result) else result
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_sizing_pipeline(topology_json_path: str, design_spec: dict):
    """topology JSON의 `"compensation"` 섹션을 읽어(있으면) `_COMPENSATION_REGISTRY`로
    함수를 조회해 `design_spec`(GBW/CL/PM 등)으로 호출한다.

    **반환값이 두 경우로 갈린다 — 호출자가 구분해서 써야 한다**:
    - `compensation`이 있으면(다단 회로): `topology_library.py`의 세 함수
      (`miller_ota_topology`/`nmcnr_3stage_topology`/`ngcc_3stage_topology`)는 전부
      **`topology_fn(prev_cggs) -> list[gm_i]` 클로저를 반환한다**(gm 숫자 자체가 아니다) —
      이 클로저를 그대로 `optimize_multistage(topology_fn, luts, ...)`에 넘길 것.
    - `compensation`이 `null`이면(단일 스테이지, 또는 기존 3개 함수 중 안 맞는 게 확인된 경우):
      `design_spec` **dict**를 그대로 반환한다 — 다단 클로저가 필요 없으니
      `size_transistor()`를 직접 호출할 것.

    이 함수는 topology -> (topology_fn 또는 design_spec) 변환만 담당한다 — 실제 사이징
    (`size_transistor()`/`optimize_multistage()`) 호출은 호출자가 반환값 종류에 맞게
    별도로 진행한다."""
    with open(topology_json_path, "r", encoding="utf-8") as f:
        topo = json.load(f)
    comp = topo.get("compensation")
    if not comp:
        return dict(design_spec)
    fn_name = comp["function"]
    if fn_name not in _COMPENSATION_REGISTRY:
        raise ValueError(
            f"topology JSON이 참조하는 compensation 함수 '{fn_name}'이 "
            f"_COMPENSATION_REGISTRY(허용된 함수 목록)에 없다 -- "
            f"{sorted(_COMPENSATION_REGISTRY)} 중 하나여야 한다")
    fn = _COMPENSATION_REGISTRY[fn_name]
    params = comp.get("parameters") or []
    kwargs = {p: design_spec[p] for p in params if p in design_spec}
    return fn(**kwargs)


# ---------------------------------------------------------------------------
# 6.5) 공정-무관 회귀 검증 러너 — "무엇을 검증할지"는 전부 reference JSON이 선언하고, 이
#      함수는 그 선언을 읽어 실행·대조만 한다. 새 공정을 추가해도 이 함수는 한 글자도
#      안 바뀐다(<process>_regression_reference.json 파일만 새로 만들면 됨) — 새 회로/새
#      engine 타입을 추가할 때도 _REGRESSION_ENGINES에 등록만 하면 된다(_COMPENSATION_
#      REGISTRY/_METRICS_REGISTRY와 같은 패턴). 배경: analog-topology-json-library.do.md
#      배치 7-1 — sky130 전용 숫자를 이 파일(공정-무관 엔진)에 직접 박았다가(2026-07-31)
#      사용자 지적으로 이 구조로 재설계함.
# ---------------------------------------------------------------------------

@dataclass
class RegressionVerdict:
    ok: bool
    case_key: str
    detail: str
    actual: dict | None = None


def _run_optimize_multistage_case(case: dict, luts_by_kind: dict) -> dict:
    """`"engine": "optimize_multistage"` case를 실제로 실행해 gms/stages를 반환한다.
    `case`는 reference JSON의 한 case 항목 그대로(`topology_fn`/`topology_fn_kwargs`/
    `lut_kinds`/`search`/`constraints`)."""
    fn_name = case["topology_fn"]
    if fn_name not in _COMPENSATION_REGISTRY:
        raise ValueError(
            f"regression case가 참조하는 topology_fn '{fn_name}'이 _COMPENSATION_REGISTRY에 "
            f"없다 -- {sorted(_COMPENSATION_REGISTRY)} 중 하나여야 한다")
    topology_fn = _COMPENSATION_REGISTRY[fn_name](**case["topology_fn_kwargs"])
    luts = [luts_by_kind[k] for k in case["lut_kinds"]]
    search = case["search"]
    constraints = case.get("constraints", {})
    result = optimize_multistage(
        topology_fn, luts,
        L_candidates=search["L_candidates"], VDS_candidates=search["VDS_candidates"],
        gm_id_grid=search["gm_id_grid"],
        objective=constraints.get("objective", "power"),
        gain_min=constraints.get("gain_min"), w_max=constraints.get("w_max"))
    if result is None:
        raise ValueError("optimize_multistage()가 실행가능점을 못 찾음 -- case의 격자/제약 확인")
    return {"gms": result["gms"],
            "stages": [{"L": s["L"], "VDS": s["VDS"], "gm_id": s["gm_id"], "W": s["W"]}
                       for s in result["stages"]]}


_REGRESSION_ENGINES = {
    "optimize_multistage": _run_optimize_multistage_case,
    # 새 engine 타입(예: "run_topology_pipeline", "optimize_full_circuit_budget")을 추가할
    # 때는 여기 한 줄만 등록하면 된다 -- run_regression_case() 자체는 수정하지 않는다.
}


def run_regression_case(reference_json_path: str, case_key: str, rel_tol: float = 0.01) -> RegressionVerdict:
    """`reference_json_path`(공정별 1개 JSON, 예: `sky130_regression_reference.json`)에서
    `case_key`로 지정된 검증 케이스를 로드해 실제로 실행하고 `expected`와 대조한다.

    이 함수 자체는 어느 공정·어느 topology_fn·어느 회로에도 하드코딩되지 않는다 — 전부
    reference JSON의 `case["engine"]`(어느 harness 함수를 돌릴지, `_REGRESSION_ENGINES`로
    조회)과 `case["expected"]`(무엇과 대조할지)가 선언한다. `lut_file`은 `reference_json_
    path`와 같은 디렉터리에서 찾는다(공정 데이터를 reference JSON과 나란히 두는 관례).

    반환: `RegressionVerdict(ok, case_key, detail, actual)` — `ok=False`면 `detail`에
    첫 번째로 어긋난 값을 명시한다."""
    with open(reference_json_path, "r", encoding="utf-8") as f:
        ref = json.load(f)
    if case_key not in ref["cases"]:
        return RegressionVerdict(ok=False, case_key=case_key, detail=(
            f"case_key '{case_key}'가 {reference_json_path}에 없다 -- "
            f"{sorted(ref['cases'])} 중 하나여야 한다"))
    case = ref["cases"][case_key]

    engine = _REGRESSION_ENGINES.get(case["engine"])
    if engine is None:
        return RegressionVerdict(ok=False, case_key=case_key, detail=(
            f"engine '{case['engine']}'이 _REGRESSION_ENGINES에 없다 -- "
            f"{sorted(_REGRESSION_ENGINES)} 중 하나여야 한다"))

    import numpy as _np
    import os as _os_mod
    lut_path = _os_mod.path.join(
        _os_mod.path.dirname(_os_mod.path.abspath(reference_json_path)), ref["lut_file"])
    d = _np.load(lut_path)
    luts_by_kind = {
        "n": SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"],
                                   d["ID_n"], d["GM_n"], d["GDS_n"], d["CGG_n"], W_ref=5e-6),
        "p": SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"],
                                   d["ID_p"], d["GM_p"], d["GDS_p"], d["CGG_p"], W_ref=5e-6),
    }
    search = dict(case.get("search", {}))
    if search.get("L_candidates") == "lut.L":
        search["L_candidates"] = [float(v) for v in d["L"]]
    if search.get("VDS_candidates") == "lut.VDS":
        search["VDS_candidates"] = [float(v) for v in d["VDS"]]
    case = dict(case, search=search)

    try:
        actual = engine(case, luts_by_kind)
    except (ValueError, KeyError) as e:
        return RegressionVerdict(ok=False, case_key=case_key, detail=f"실행 실패: {e}")

    expected = case["expected"]
    for i, (a_gm, e_gm) in enumerate(zip(actual["gms"], expected["gms"])):
        if abs(a_gm - e_gm) / e_gm > rel_tol:
            return RegressionVerdict(ok=False, case_key=case_key, actual=actual, detail=(
                f"gms[{i}] 불일치: 실제 {a_gm} vs 기대 {e_gm}(상대오차 {rel_tol:.0%} 초과)"))
    for i, (a_st, e_st) in enumerate(zip(actual["stages"], expected["stages"])):
        for key in ("L", "VDS", "gm_id", "W"):
            a_val, e_val = a_st[key], e_st[key]
            if abs(a_val - e_val) / max(abs(e_val), 1e-15) > rel_tol:
                return RegressionVerdict(ok=False, case_key=case_key, actual=actual, detail=(
                    f"stages[{i}].{key} 불일치: 실제 {a_val} vs 기대 {e_val}"
                    f"(상대오차 {rel_tol:.0%} 초과)"))
    return RegressionVerdict(ok=True, case_key=case_key, actual=actual,
                              detail=f"{ref.get('source', reference_json_path)}와 일치")


# ---------------------------------------------------------------------------
# 6.6) B/C/F 엔진 — LUT가 필요한 절반 (§7.3.2, 배치 7-3, 2026-07-31)
#      A엔진(propagate_topology_forced_currents)/C엔진의 그래프 탐지 절반(find_diode_stacks)은
#      LUT가 필요 없어 stick_diagram.py에 있다 — 여기는 그 나머지: B엔진(LUT 역산),
#      C엔진의 실제 전류 역산, F엔진(metrics 계산기 레지스트리).
# ---------------------------------------------------------------------------

def solve_id_for_target_gm(lut: "GmIdLUT", L: float, vds: float, vs: float, W: float,
                            gm_target: float, gm_id_bounds: tuple = (2.0, 30.0),
                            tol: float = 1e-6, max_iter: int = 60) -> SizingResult:
    """B엔진(§7.3.2) — 이미 폭 W가 고정된 소자에서 gm(ID,W)=gm_target을 만족하는 ID를 LUT
    이분탐색으로 역산한다(배치 7-3c Level4 "ID_q = min{ID : gm(ID,W)=gm2_target}"이 이
    함수의 첫 사용처 — `resize.py`의 옛 "1/16 추측 후 gm 잔존율 확인"과 달리 인과관계가
    거꾸로가 아니다).

    gm(gm_id) = gm_id * IDu(gm_id,L,vds,vs) * (W/L)는 gm_id에 대해 **단조감소**한다 — gm/ID가
    VGS에 단조감소하는 것과 표리 관계로, VGS가 커질수록(=gm_id가 작아질수록) 소자의 gm 자체는
    커진다(`_solve_vgs()`가 이미 의존하는 것과 같은 단조성). 이 성질로 표준 이분탐색이 성립한다.
    `gm_id_bounds`는 탐색 범위(기본 2~30, 실용적 gm/ID 범위) — 이 범위에서 만드는 gm이
    `gm_target`을 못 담으면 즉시 `ValueError`(조용히 외삽하지 않음)."""
    def _gm_at(gm_id: float) -> float:
        idu = lut.gm_id_to_id_density(gm_id, L, vds, vs)
        return gm_id * idu * (W / L)

    lo, hi = gm_id_bounds
    gm_lo, gm_hi = _gm_at(lo), _gm_at(hi)  # gm_lo(강반전측) > gm_hi(약반전측), 단조감소
    if not (gm_hi <= gm_target <= gm_lo):
        raise ValueError(
            f"gm_target={gm_target:.3g}가 gm_id_bounds={gm_id_bounds}에서 만드는 gm 범위 "
            f"[{gm_hi:.3g},{gm_lo:.3g}] 밖 -- bounds를 넓히세요.")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        gm_mid = _gm_at(mid)
        if abs(gm_mid - gm_target) <= tol * gm_target:
            lo = hi = mid
            break
        if gm_mid > gm_target:
            lo = mid
        else:
            hi = mid
    gm_id_sol = 0.5 * (lo + hi)
    ID = gm_target / gm_id_sol
    return SizingResult(gm=gm_target, gm_id=gm_id_sol, ID=ID, W=W)


def _invert_gm_id_for_current(lut: "GmIdLUT", current: float, L: float, vds: float, vs: float,
                               W: float, gm_id_bounds: tuple = (2.0, 30.0),
                               tol: float = 1e-9, max_iter: int = 60) -> float:
    """주어진 전류를 만드는 gm_id를 이분탐색으로 역산한다 — ID(gm_id) = IDu(gm_id)*(W/L)가
    gm_id에 단조감소(약반전=높은 gm_id=낮은 전류)이므로 성립. `solve_diode_stack_current()`의
    내부 헬퍼(diode-stack 각 소자의 VGS를 구하려면 먼저 그 소자의 gm_id를 알아야 한다)."""
    def _id_at(gm_id: float) -> float:
        return lut.gm_id_to_id_density(gm_id, L, vds, vs) * (W / L)

    lo, hi = gm_id_bounds
    id_lo, id_hi = _id_at(lo), _id_at(hi)  # id_lo(강반전) > id_hi(약반전), 단조감소
    if not (id_hi <= current <= id_lo):
        raise ValueError(
            f"current={current:.3g}가 gm_id_bounds={gm_id_bounds}에서 만드는 전류 범위 "
            f"[{id_hi:.3g},{id_lo:.3g}] 밖 -- bounds를 넓히세요.")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        id_mid = _id_at(mid)
        if abs(id_mid - current) <= tol * current:
            lo = hi = mid
            break
        if id_mid > current:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def solve_diode_stack_current(lut: "GmIdLUT", known_stack: list, target_voltage: float,
                               i_bounds: tuple = (1e-9, 1e-2), gm_id_bounds: tuple = (2.0, 30.0),
                               tol: float = 1e-9, max_iter: int = 80) -> float:
    """C엔진(§7.3.2) — 직렬 diode-connected 스택(`find_diode_stacks()`가 찾아낸 경로, 예:
    M8->M11a->M11b)이 공통 branch 전류 Ib(A엔진의 직렬-스택 원칙에 따라 스택 내 전부 동일
    전류)로 흐를 때, 각 소자 VGS의 합이 `target_voltage`(예: 이미 B엔진으로 확정된 참조
    소자의 Vgs)와 같아지는 Ib를 이분탐색으로 역산한다("배치 7-3c Level5: Ib = Vg15 KVL
    루프 해").

    `known_stack`: `[{"kind","L","W","vds","vs"}, ...]` — W는 전부 이미 알려져 있어야 한다
    (면적비 K_replica 같은 D유형 theta가 이미 적용된 결과값). `VGS_sum(Ib)`는 Ib에 대해
    단조증가(전류가 커질수록 각 소자 VGS도 커짐)이므로 표준 이분탐색(로그축, 전류의 동적
    범위가 넓어서)이 성립한다.

    ⚠️ 정직한 한계(2026-07-31): 이 함수의 정확한 호출 규약(스택의 어느 쪽을 "known"으로
    두는지, target_voltage를 어디서 가져오는지)은 이 세션에서 `analog-topology-json-library.
    do.md` §7.3c Level5("Ib = Vg15 KVL 루프 해")와 `sky130-worked-example.md` §13.5의 산문
    설명만으로 재구성했다 — 원래 이 KVL 관계를 처음 유도한 세션의 정확한 과정은 이 세션에
    없다. 실제 M9a/M8/M11a/M11b 회로에 처음 연결할 때(배치 7-3d/7-5) 이 계약이 맞는지
    재검증이 필요하다."""
    def _vgs_sum(current: float) -> float:
        total = 0.0
        for dev in known_stack:
            L, W = dev["L"], dev["W"]
            vds, vs = dev.get("vds", 0.0), dev.get("vs", 0.0)
            gm_id = _invert_gm_id_for_current(lut, current, L, vds, vs, W, gm_id_bounds=gm_id_bounds)
            total += lut.vgs_for_gm_id(gm_id, L, vds, vs)
        return total

    lo, hi = i_bounds
    v_lo, v_hi = _vgs_sum(lo), _vgs_sum(hi)
    if not (v_lo <= target_voltage <= v_hi):
        raise ValueError(
            f"target_voltage={target_voltage:.3g}V가 i_bounds={i_bounds}에서 만드는 VGS합 범위 "
            f"[{v_lo:.3g},{v_hi:.3g}]V 밖 -- i_bounds를 넓히세요.")
    for _ in range(max_iter):
        mid = math.sqrt(lo * hi)  # 전류는 동적범위가 넓어 로그축 이분
        v_mid = _vgs_sum(mid)
        if abs(v_mid - target_voltage) <= tol:
            lo = hi = mid
            break
        if v_mid < target_voltage:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


# ---------------------------------------------------------------------------
# 6.8) 역할(role) 기반 헤드룸/gm_id/L 선택 harness (배치 7-3b/7-3e/7-3f, 2026-07-31)
#      `resize.py`의 손-찍은 매직넘버(VDS 상수, GM_ID_SIG=12류, L1=0.15um류)를 대체하는
#      3개 harness — 전부 역할(role) 문자열로 정책을 선택하는 같은 패턴.
# ---------------------------------------------------------------------------

def _default_cascode_headroom(entry: dict) -> float:
    """캐스코드 역할 소자 하나의 헤드룸(VDS) 기본 정책. `entry`에 `"gm_id"`가 있으면
    (배치 7-3e (b) 연동 — `search_gm_id_for_role()`이 이미 고른 gm_id를 공유) Jespers
    표준식 `Vdsat_eff=2/gm_id`로 계산(gm_id가 클수록 필요 헤드룸이 줄어듦, 이득과
    상충하지 않음 — do.md 배치 7-3e "(b) 해결" 참고). 없으면 `entry["min_vds"]`를
    그대로 쓴다(하위호환 — 옛 고정-VDS 방식)."""
    if "gm_id" in entry:
        return 2.0 / entry["gm_id"] + entry.get("margin", 0.05)
    return entry["min_vds"]


@dataclass
class HeadroomPolicy:
    """`allocate_stack_headroom()`의 배정 정책 — cascode 역할 소자의 헤드룸만 정책으로
    갈아끼울 수 있게 분리했다(§7.9 질문 5, 2026-07-31 결정: 정책 객체/콜백으로 설계).
    `cascode_fn(entry) -> float`: `{"name","role","min_vds"[,"gm_id","margin"]}` 하나를
    받아 그 소자에 배정할 VDS를 반환."""
    cascode_fn: Callable[[dict], float] = _default_cascode_headroom


DEFAULT_POLICY = HeadroomPolicy()


def allocate_stack_headroom(vdd: float, stack: list, policy: HeadroomPolicy = DEFAULT_POLICY) -> dict:
    """배치 7-3b — 직렬 스택(예: `resize.py`의 M6/M1/M2/M3/M4/M5, VDS 하드코딩 0.30/0.40/
    0.20/0.20/0.40/0.30)의 VDS를 "캐스코드는 얇게, 입력/tail은 넉넉하게"라는 **의도를 실행하는
    함수**로 대체한다.

    `stack`: `[{"name","role","min_vds"[,"gm_id","margin"]}, ...]` — `role=="cascode"`는
    `policy.cascode_fn(entry)`(기본: gm_id가 있으면 `2/gm_id+margin`, 없으면 `min_vds` 그대로)
    만큼만 배정한다. 나머지 역할(`"input"`/`"tail"` 등)은 남는 예산(`vdd - cascode 합`)을
    인원수로 균등 배분한다(가중치 배분이 필요해지면 `policy`를 확장 — 지금은 이 정책 하나로
    충분함이 이 회로 하나로만 확인됨).

    합이 `vdd`와 정확히 일치함을 함수 자체가 보장한다(assert) — 예전에 이 합을 안 맞춰
    3.2V(1.8V 레일 초과)로 잘못 짰던 실제 사고가 있었다(§3 실측 이력)."""
    cascode_entries = [e for e in stack if e["role"] == "cascode"]
    other_entries = [e for e in stack if e["role"] != "cascode"]

    result = {}
    cascode_total = 0.0
    for e in cascode_entries:
        v = policy.cascode_fn(e)
        result[e["name"]] = v
        cascode_total += v

    remaining = vdd - cascode_total
    if other_entries:
        share = remaining / len(other_entries)
        for e in other_entries:
            result[e["name"]] = share
    total = sum(result.values())
    assert abs(total - vdd) < 1e-9 * max(vdd, 1.0), (
        f"헤드룸 배정 합({total})이 vdd({vdd})와 불일치 -- other_entries가 비어있는데 "
        f"cascode 배정 합이 vdd와 안 맞으면 배분할 곳이 없어 이 assert가 실패한다.")
    return result


def search_gm_id_for_role(lut: "GmIdLUT", L: float, vds: float, vs: float, ID_target: float,
                           role: str, W_bounds: tuple = (1e-6, 200e-6),
                           gm_id_grid: list | None = None) -> float:
    """배치 7-3e — `resize.py`의 균일한 매직넘버(`GM_ID_SIG=12`류, 역할 구분 없음)를
    "이 공정에서 W가 타당범위 안에 들면서 역할이 요구하는 방향의 극단"이라는 실제 LUT
    스캔으로 대체한다(sky130 실측: gm/ID를 논문 명시값 그대로 쓰면 W가 수천~수만 um로
    폭발하는 역할이 실제로 있었다 — 원칙은 gm/ID 자체가 아니라 "이 스캔"이다).

    `gm_id_grid`(기본 2.0~30.0, 0.5 간격)를 스윕해 `W = ID_target*L/IDu(gm_id,L,vds,vs)`가
    `W_bounds` 안에 드는 후보만 남긴 뒤, `role`별 기준으로 하나를 고른다:
    - `"matching"`(전류거울/전류원) — gm_id **최소화**(strong inversion 극단, §7.1: 매칭에
      유리).
    - `"gain"`(캐스코드) — gm/ID가 아니라 **gm/gds를 직접 최대화**(gm/ID 최대화와 다르다는
      게 sky130 실측으로 확인됨 — min-L NMOS만 국소 정점, PMOS/L≥0.35um은 정점 없이 단조증가).
    - `"balanced"`(신호/GBW 고정 등) — W_bounds를 만족하는 아무 지점(결정론적으로 gm_id
      오름차순 중 첫 feasible을 고른다 — `resize.py`의 "17로 순방향 사이징→W 비현실적→W
      상한 고정 후 역산" 수동 flip이 이 role의 특수 사례였다).

    후보가 하나도 없거나 `role`이 셋 중 하나가 아니면 즉시 `ValueError`."""
    if gm_id_grid is None:
        gm_id_grid = [i * 0.5 for i in range(4, 61)]  # 2.0~30.0
    feasible = []
    for gm_id in gm_id_grid:
        try:
            idu = lut.gm_id_to_id_density(gm_id, L, vds, vs)
        except ValueError:
            continue
        if idu <= 0:
            continue
        W = ID_target * L / idu
        if W_bounds[0] <= W <= W_bounds[1]:
            feasible.append(gm_id)
    if not feasible:
        raise ValueError(
            f"W_bounds={W_bounds} 안에 드는 gm_id 후보가 없다(role={role!r}, "
            f"gm_id_grid={gm_id_grid[0]}~{gm_id_grid[-1]}) -- 범위를 넓히세요.")
    if role == "matching":
        return min(feasible)
    if role == "balanced":
        return feasible[0]
    if role == "gain":
        best_gm_id, best_ratio = None, -1.0
        for gm_id in feasible:
            ratio = lut.gm_gds_ratio(gm_id, L, vds, vs)
            if ratio > best_ratio:
                best_ratio, best_gm_id = ratio, gm_id
        return best_gm_id
    raise ValueError(f"알 수 없는 role: {role!r} -- 'matching'/'gain'/'balanced' 중 하나여야 한다")


_L_ROLE_MULTIPLIERS = {
    # edaboard 실무 토론(do.md 배치 7-3f 인용): "서브마이크론 공정에서 최소길이의 2~3배
    # 이상" -- sky130 LUT 실측(gm/gds가 2.3배 L에서 3~5.5배 급증)으로 방향은 확인됐으나
    # "이상"의 정확한 상한은 회로마다 다를 수 있어 범위 내 대표값(중간값)을 고정 배수로 채택.
    "mirror": 2.5,
    # "최소길이보다 살짝만 크게"(near-but-not-at Lmin) -- PVT 민감도 완화가 목적이지
    # 미러의 "출력임피던스 극대화" 목적이 아니므로 훨씬 작은 배수.
    "bias_replica": 1.2,
}


def select_L_by_role(role: str, L_min: float) -> float:
    """배치 7-3f — 고정 배수 규칙류(미러/바이어스)만 다룬다. 캐스코드/신호경로의 L은
    이 함수의 담당이 아니다 — 단별 이득배분이 필요한 값(정답이 없는 트레이드오프)이라
    배치 7-3d의 theta 탐색(`L_cascode`/`L_stage2out`, 총이득 제약을 만족하는 탐색으로
    도출)이 대신 결정한다(do.md 배치 7-3f 정정 문단 참고) — 그래서 `role`이 `"cascode"`
    또는 `"signal"`이면 이 함수를 잘못 호출한 것으로 보고 즉시 `ValueError`."""
    if role in ("cascode", "signal"):
        raise ValueError(
            f"role={role!r}은 select_L_by_role()이 아니라 배치 7-3d의 theta 탐색"
            f"(L_cascode/L_stage2out)이 담당한다 -- 여기서 호출하면 안 됨")
    multiplier = _L_ROLE_MULTIPLIERS.get(role)
    if multiplier is None:
        raise ValueError(
            f"등록되지 않은 role: {role!r} -- _L_ROLE_MULTIPLIERS에 등록된 "
            f"{sorted(_L_ROLE_MULTIPLIERS)} 중 하나이거나 'cascode'/'signal'이어야 한다")
    return L_min * multiplier


def estimate_area_budget(kind: str, role_tag: str, area_priors: dict, n_fingers: int,
                          finger_pitch_area: float = 1.0, cold_start_alpha: float = 0.65) -> float:
    """배치 7-4b 확장(2026-07-31) — `select_layout_tool()`의 `area_budget` 인자를 "맨손으로
    찍는" 대신 근거 있게 계산하는 harness. 디지털의 `gate_count = 면적/NAND2 면적` 개념을
    아날로그에 맞게 각색(문헌: 1D/2D 배치 모델의 가중평균 `A ≈ (1-α)·A_1D + α·A_2D`) —
    `n_fingers`(이미 사이징 결과)만으로 정해지는 `A_1D = n_fingers * finger_pitch_area`
    (컴팩션 없는 1D 배치, 상한)와, `pack_floorplan_grouped()`가 실제 instance마다 내놓는
    `packing_density`를 역할별로 누적한 실측 평균으로 정해지는 `A_2D = A_1D / packing_density`
    (2D 컴팩션 반영 추정) 사이를 잇는다.

    **표본 유무에 따라 계산 방식이 갈린다**(자기참조 sanity check가 성립하는 이유이기도
    하다): `area_priors[role_tag]`에 실측 표본이 있으면(`n_samples>=1`) 그 실측
    `packing_density_mean`으로 `A_2D`를 **그대로** 반환한다 — `packing_density`는
    정의상 `A_1D/실제_bbox면적`이므로, 실제 표본에서 온 값을 그대로 쓰면
    `A_1D/packing_density`가 그 표본의 실제 면적과 정확히 같아진다(블렌딩 없이 100% 신뢰).
    표본이 아직 없으면(`n_samples==0`) 문헌 typical값 `cold_start_alpha`(잠정 0.65, §7.9
    미결 — 표본이 쌓이면 더 정확한 값으로 교체될 수 있음)로 1D/2D를 블렌딩한
    `(1-α)*A_1D + α*(A_1D/α)`를 콜드스타트 추정치로 쓴다.

    `finger_pitch_area`(기본 1.0)는 이 프로젝트의 `FloorplanBlock`과 같은 관례 — 절대
    실리콘 치수가 아니라 **비율 프록시**다. `kind`는 아직 이 함수의 계산에 직접 쓰이지
    않는다(향후 kind별 finger_pitch_area 차등화를 위한 확장 지점으로 시그니처에 남겨둠 —
    `role_tag` 세분화 문제와 같은 미결 사안, do.md 배치 7-4b 확장 "검토 필요" 참고)."""
    prior = area_priors.get(role_tag) or {}
    n_samples = prior.get("n_samples", 0)
    a_1d = n_fingers * finger_pitch_area
    if n_samples and prior.get("packing_density_mean"):
        return a_1d / prior["packing_density_mean"]
    a_2d_cold = a_1d / cold_start_alpha
    return (1 - cold_start_alpha) * a_1d + cold_start_alpha * a_2d_cold


@dataclass
class SizingContext:
    """A/B/C 엔진이 채워나가는 공유 사이징 상태 — theta 탐색(§7.3.2, 배치 7-3d)과 F엔진
    metrics 계산이 공통으로 읽고 쓰는 단일 소자-사이징 결과 저장소. `sized`는
    `{device_name: {"ID":, "gm":, "gds":, "W":, "L":, "gm_id":, "kind":, ...}}` — 필드는
    metric 계산기가 실제로 읽는 것만 채우면 된다(전부 강제하지 않음).

    `spec`/`derived`/`seed_currents`/`mirror_ratios`는 배치 7-3d(`apply_theta_feed()`/
    `optimize_full_circuit_budget()`)가 추가한 필드다: `spec`은 호출자가 넘긴 design spec
    (LUT/design 상수, 읽기 전용으로 취급), `derived`는 `_feed_settling_split()`류가 저장하는
    중간 스칼라(어느 엔진에도 직접 안 닿는 값), `seed_currents`/`mirror_ratios`는
    `propagate_topology_forced_currents()`(A엔진)에 그대로 전달할 입력이다."""
    sized: dict = field(default_factory=dict)
    spec: dict = field(default_factory=dict)
    derived: dict = field(default_factory=dict)
    seed_currents: dict = field(default_factory=dict)
    mirror_ratios: dict = field(default_factory=dict)


def _metric_sum_current(spec: dict, ctx: SizingContext) -> float:
    """F엔진: `devices`(선택, 없으면 ctx.sized 전체)의 ID 합 — 총 전류/전력 예산용."""
    names = spec.get("devices") or list(ctx.sized.keys())
    return sum(ctx.sized[n]["ID"] for n in names)


def _metric_sum_area(spec: dict, ctx: SizingContext) -> float:
    """F엔진: `devices`(선택, 없으면 ctx.sized 전체)의 W*L 합 — 면적 예산용."""
    names = spec.get("devices") or list(ctx.sized.keys())
    return sum(ctx.sized[n]["W"] * ctx.sized[n]["L"] for n in names)


def _metric_gain_stages_sum(spec: dict, ctx: SizingContext) -> float:
    """F엔진: `stages`(`[[dev,...], [dev,...]]`, 스테이지별 병렬 gm/gds 소자 목록)의 각
    스테이지 이득(병렬 gm 합 / 병렬 gds 합)을 dB로 환산해 합산 — 다단 증폭기 총 DC 이득
    (옛 `compute_total_gain()`을 이 레지스트리 계약으로 흡수)."""
    total_db = 0.0
    for stage in spec["stages"]:
        gm_sum = sum(ctx.sized[n]["gm"] for n in stage)
        gds_sum = sum(ctx.sized[n]["gds"] for n in stage)
        total_db += 20 * math.log10(gm_sum / gds_sum)
    return total_db


def _metric_flicker_plus_thermal_sum(spec: dict, ctx: SizingContext) -> float:
    """F엔진(배치 7-3g, 2026-07-31) — `stages`(`[[dev,...], ...]`)의 입력환산 열+1/f 잡음
    밀도를 RMS 합산(독립 잡음원 가정)해 V/√Hz로 반환. `ctx.spec["lut"]`가 `noise_1f_density()`
    (SID_1F 필요)를 지원해야 한다 — 지원 안 하면 `ValueError`가 그대로 전파된다(조용히
    스킵하지 않음). `ctx.spec`의 선택 키: `"gamma"`(기본 2/3, 열잡음 계수),
    `"temperature_K"`(기본 300), `"freq"`(기본 1.0Hz)."""
    lut = ctx.spec["lut"]
    gamma = ctx.spec.get("gamma", 2.0 / 3.0)
    freq = ctx.spec.get("freq", 1.0)
    kT = 1.380649e-23 * ctx.spec.get("temperature_K", 300.0)
    total_variance = 0.0
    for stage in spec["stages"]:
        for name in stage:
            e = ctx.sized[name]
            s_thermal = 4 * kT * gamma / e["gm"]
            s_1f = lut.noise_1f_density(e["gm_id"], e["L"], e.get("vds", 0.6), e.get("vs", 0.0),
                                         e["W"], freq)
            total_variance += s_thermal + s_1f
    return math.sqrt(total_variance)


def estimate_mismatch_sigma(vth0_slope: float, W: float, L: float) -> float:
    """배치 7-3h(2026-07-31) — Pelgrom 폐형식: `sigma_Vth = vth0_slope / sqrt(W*L)`.
    `vth0_slope`는 PDK mismatch 모델 상수(V·µm 단위, sky130 예: NFET 3.356e-3/PFET 5.856e-3
    — PDK mismatch.corner.spice 파일에서 직접 읽는 값, 시뮬레이션 불필요). `W`/`L`은 µm
    단위(다른 함수들의 SI(m) 관례와 다름 — Pelgrom 계수 자체가 관례상 µm 단위이기 때문,
    호출자가 변환할 것)."""
    return vth0_slope / math.sqrt(W * L)


def _metric_pelgrom_mismatch(spec: dict, ctx: SizingContext) -> float:
    """F엔진(배치 7-3h) — `devices`(matching 쌍, 보통 2개)의 Vth mismatch를 `estimate_
    mismatch_sigma()`로 각각 계산하고, 두 소자가 통계적으로 독립이라는 표준 가정 하에
    분산을 합산(RSS)해 쌍(pair) mismatch sigma를 mV로 반환. `kind`(예 `"pfet"`/`"nfet"`)로
    `ctx.spec["vth0_slope"][kind]` PDK 상수를 조회한다."""
    vth0_slope = ctx.spec["vth0_slope"][spec["kind"]]
    sigmas = [estimate_mismatch_sigma(vth0_slope, ctx.sized[d]["W"] * 1e6, ctx.sized[d]["L"] * 1e6)
              for d in spec["devices"]]
    return math.sqrt(sum(s * s for s in sigmas)) * 1e3


def _cmrr_diff_pair_tail(metric_spec: dict, ctx: SizingContext) -> float:
    """`circuit_family="diff_pair_tail"` — CMRR ≈ [(ro_tail/2) + (1/gm_tail)]·gm_tail
    (문헌 표준 1차 근사, do.md 배치 7-3i). `tail_device`의 이미 사이징된 gm/gds만 쓴다."""
    tail = ctx.sized[metric_spec["tail_device"]]
    ro_tail = 1.0 / tail["gds"]
    cmrr_linear = (ro_tail / 2.0 + 1.0 / tail["gm"]) * tail["gm"]
    return 20 * math.log10(cmrr_linear)


def _cmrr_telescopic_class_ab(metric_spec: dict, ctx: SizingContext) -> float:
    """`circuit_family="telescopic_class_ab"` — current-reuse telescopic 1단(Xie&Chen
    논문 Fig.2, current_reuse_telescopic_ota)의 CMRR. 이 논문 자체엔 CMRR 폐형식이 없어서
    (시뮬레이션 수치 94.4dB만 보고) 2026-07-31에 처음부터 유도 -- 노드방정식을 직접 풀고
    (sympy) 이상화 소신호 netlist(sky130 PDK, ngspice AC 해석)로 교차검증했다.

    ⚠️ 처음 시도한 "Acm=Gm_cm_total*R_out(differential R_out과 동일)" 단순화는 **틀렸다**
    (SPICE 대조 중 발견 -- 논문 94.4dB 대비 실제 계산은 31~46dB, 거의 정확히 절반(dB
    스케일 아님, R_out이 CM/DM에서 다른 값이라 소거 불가)). 정확한 노드해석 결과, PMOS
    경로(M1a-M2a, tail=Rx)와 NMOS 경로(M4a-M3a, tail=Ry)가 같은 출력노드에서 서로
    교차결합해 **한쪽 tail 임피던스만 키워도 CMRR이 무한정 좋아지지 않고 다른 쪽 경로가
    만드는 바닥(floor)에 수렴**하는 실제 현상이 나온다(단순 diff_pair_tail의 "gm·R_tail"
    직관과 다름). 아래는 gm·ro≫1 leading-order 근사(SPICE 정확해 대비 스윕 전 구간 오차
    <=0.2dB로 확인, do.md 참고) -- 그래도 실제 최종 확인은 SPICE AC 시뮬레이션 권장.

    metric_spec 키: `input_p`/`cascode_p`(PMOS 입력쌍 M1a·PMOS 캐스코드 M2a),
    `input_n`/`cascode_n`(NMOS 입력쌍 M4a·NMOS 캐스코드 M3a), `tail_p_devices`
    (PMOS tail 전류원 목록, 예 [M6,M7] -- gds 병렬합), `tail_n_device`(NMOS tail, 예 M5)."""
    gmp = ctx.sized[metric_spec["input_p"]]["gm"]
    rop1 = 1.0 / ctx.sized[metric_spec["input_p"]]["gds"]
    rop2 = 1.0 / ctx.sized[metric_spec["cascode_p"]]["gds"]
    gmn = ctx.sized[metric_spec["input_n"]]["gm"]
    ron1 = 1.0 / ctx.sized[metric_spec["input_n"]]["gds"]
    ron2 = 1.0 / ctx.sized[metric_spec["cascode_n"]]["gds"]
    gds_tail_p = sum(ctx.sized[d]["gds"] for d in metric_spec["tail_p_devices"])
    Rx = 1.0 / gds_tail_p
    Ry = 1.0 / ctx.sized[metric_spec["tail_n_device"]]["gds"]

    Kp_prime = gmp * rop1 * rop2   # PMOS 경로(M1a-M2a) 캐스코드 출력임피던스(vom1에서 본)
    Kn_prime = gmn * ron1 * ron2   # NMOS 경로(M4a-M3a) 캐스코드 출력임피던스
    R_out = Kp_prime * Kn_prime / (Kp_prime + Kn_prime)
    Adm = (gmp + gmn) * R_out

    Kp = gmp * Kp_prime
    Kn = gmn * Kn_prime
    Acm = Kn * Kp * (Rx + Ry) / (Kn * Ry + Kp * Rx)

    return 20 * math.log10(Adm / Acm)


_CMRR_ESTIMATOR_REGISTRY = {
    "diff_pair_tail": _cmrr_diff_pair_tail,
    "telescopic_class_ab": _cmrr_telescopic_class_ab,
}


def _psrr_diff_pair_tail(metric_spec: dict, ctx: SizingContext) -> float:
    """`circuit_family="diff_pair_tail"` — ⚠️ order-of-magnitude 근사(정직한 한계,
    2026-07-31): CMRR과 같은 building block(`tail_device`의 gm/gds)을 재사용한 자리표시자
    (`gm_tail/gds_tail`)일 뿐, 이 회로 계열의 검증된 PSRR 폐형식은 이 세션에서 도출하지
    못했다(§7.9 질문10 미결, do.md 배치 7-3i "검토 필요" 참고). 캐스코드 tail 유무 등에 따라
    문헌상 수천 배까지 실제 값과 차이 날 수 있다 — 탐색에서 명백히 나쁜 후보를 거르는
    용도로만 쓸 것, 최종 확인은 SPICE AC 시뮬레이션이 반드시 필요하다."""
    tail = ctx.sized[metric_spec["tail_device"]]
    psrr_linear = tail["gm"] / tail["gds"]
    return 20 * math.log10(psrr_linear)


_PSRR_ESTIMATOR_REGISTRY = {
    "diff_pair_tail": _psrr_diff_pair_tail,
}


def _metric_cmrr_estimate(metric_spec: dict, ctx: SizingContext) -> float:
    """F엔진(배치 7-3i) — `_CMRR_ESTIMATOR_REGISTRY`를 `circuit_family`로 조회하는 2단계
    lookup(`_METRICS_REGISTRY`가 1단계). 등록 안 된 family는 즉시 `ValueError`."""
    family = metric_spec["circuit_family"]
    fn = _CMRR_ESTIMATOR_REGISTRY.get(family)
    if fn is None:
        raise ValueError(f"등록되지 않은 CMRR circuit_family: {family!r} -- "
                          f"_CMRR_ESTIMATOR_REGISTRY에 등록된 "
                          f"{sorted(_CMRR_ESTIMATOR_REGISTRY)} 중 하나여야 한다")
    return fn(metric_spec, ctx)


def _metric_psrr_estimate(metric_spec: dict, ctx: SizingContext) -> float:
    """F엔진(배치 7-3i) — `_PSRR_ESTIMATOR_REGISTRY`를 `circuit_family`로 조회하는 2단계
    lookup. 등록 안 된 family는 즉시 `ValueError`."""
    family = metric_spec["circuit_family"]
    fn = _PSRR_ESTIMATOR_REGISTRY.get(family)
    if fn is None:
        raise ValueError(f"등록되지 않은 PSRR circuit_family: {family!r} -- "
                          f"_PSRR_ESTIMATOR_REGISTRY에 등록된 "
                          f"{sorted(_PSRR_ESTIMATOR_REGISTRY)} 중 하나여야 한다")
    return fn(metric_spec, ctx)


_METRICS_REGISTRY = {
    "sum_current":              _metric_sum_current,
    "sum_area":                 _metric_sum_area,
    "gain_stages_sum":          _metric_gain_stages_sum,
    "flicker_plus_thermal_sum": _metric_flicker_plus_thermal_sum,   # 배치 7-3g
    "pelgrom_mismatch":         _metric_pelgrom_mismatch,            # 배치 7-3h
    "cmrr_estimate":            _metric_cmrr_estimate,               # 배치 7-3i
    "psrr_estimate":            _metric_psrr_estimate,               # 배치 7-3i
}


def compute_metric(metric_spec: dict, ctx: SizingContext) -> float:
    """이미 사이징 완료된 `ctx`(모든 소자의 ID/gm/gds/W/L 확정)에서 `metric_spec`이 지정한
    값 하나를 읽어 계산한다 — `theta_value` 인자가 없다(metric은 자유값을 받는 게 아니라
    이미 정해진 상태를 관찰만 하는 순수 함수이기 때문, §7.3.3 Q2). 등록 안 된 `type`은
    `_COMPENSATION_REGISTRY`/`_THETA_FEED_REGISTRY`와 동일하게 즉시 `ValueError`."""
    metric_type = metric_spec["type"]
    calc = _METRICS_REGISTRY.get(metric_type)
    if calc is None:
        raise ValueError(f"등록되지 않은 metric 타입: {metric_type!r} -- "
                          f"_metric_*() 계산기를 새로 작성해 _METRICS_REGISTRY에 등록할 것")
    return calc(metric_spec, ctx)


# ---------------------------------------------------------------------------
# 6.9) D — optimize_full_circuit_budget() + _THETA_FEED_REGISTRY (배치 7-3d, 2026-07-31)
#      A/B/C/F 4개 엔진(§6.6/§6.8)을 sizing_roles.theta/metrics/objective/constraints
#      선언만 읽어 조립하는 회로-무관 단일 함수. theta 하나하나를 실제 계산 상태에 꽂는
#      것은 이 함수 안에서 분기하지 않고 apply_theta_feed()/_THETA_FEED_REGISTRY로 위임한다.
# ---------------------------------------------------------------------------

from stick_diagram import (Transistor, load_topology, propagate_topology_forced_currents,
                            derive_stack_groups, assign_finger_geometry, run_topology_pipeline,
                            repair_matching_safety, split_into_stacks)


@dataclass
class FeedHandler:
    fn: Callable[[dict, float, "SizingContext"], None]
    touches: list  # 이 feed가 실제로 닿는 엔진 — "A"/"B"/"C"/"F" 중 1개 이상


def _feed_root_ratio(feed_spec: dict, theta_value: float, ctx: SizingContext) -> None:
    """`{"type":"A","tag":...,"root":<device>|[<device>,...],"reference":[<device>,...]}` —
    A엔진 `seed_currents`에 `theta_value * sum(reference 소자들의 이미 확정된 전류)`를 `root`의
    seed 전류로 채운다. `reference` 소자들의 `ID`는 이 feed가 적용되는 시점까지 이미
    `ctx.sized`에 있어야 한다(호출 순서 책임은 `sizing_roles.theta` 배열 순서 — 참조 소자를
    먼저 결정하는 theta를 앞에 선언할 것) 또는 `spec["known_sizing"]`으로 미리 시드해둘 것.

    `root`는 문자열(소자 1개) 또는 리스트(소자 여러 개, 전부 같은 비율로 동시에 시드)를 받는다
    (2026-08-03, 배치 7-5 실행 중 확장) — bias-gen처럼 "같은 레퍼런스를 gate로 읽는 병렬
    전류원이 N개"인 실제 회로에서, 소자마다 theta 차원을 하나씩 늘리면(예: N=8) 격자
    탐색이 `grid_points_per_theta**N`배로 폭발한다(current_reuse_telescopic_ota에서 실측 —
    M6/M8/M13/M22/M17/M60/M61/M66이 전부 M18_bg와 같은 Vbias1/유사 레퍼런스를 읽는 병렬
    전류원). `matching_pairs`(kind=current_mirror)로 우회하는 방법도 시도했으나, 그건
    "같은 L을 써야 하는 진짜 매칭쌍"이라는 별도 의미를 강제해(§L 일치성 검사) 서로 다른
    L_role(mirror/bias_replica 등)을 쓰는 이 소자들에는 안 맞았다(실측 확인: ValueError로
    실패) — `root`를 리스트로 받아 theta 차원 증가 없이 N개를 동시에 seed하는 이 확장이
    두 문제(격자 폭발, 강제 L 일치) 모두를 피한다.

    `reference` 소자는 `ctx.sized`(compensation/A엔진이 이미 확정) 또는 `ctx.seed_currents`
    (같은 평가 안에서 이 feed보다 먼저 실행된 다른 "A" root_ratio feed가 seed만 해두고 아직
    A엔진을 못 거친 상태)에서 조회한다(2026-08-03 확장) — A엔진이 theta 루프 전체가 끝난
    뒤 단 한 번만 도는 구조라, 한 theta의 root가 다른 theta의 reference로 쓰이는 체이닝
    (예: r_classab_src가 seed한 M8/M13을 kcl_diode_M11a가 참조)은 `ctx.sized`만 보면
    KeyError가 난다(실측 발견) — `ctx.seed_currents`도 함께 보게 하면 코드 변경 없이
    바로 풀린다(둘 다 없으면 여전히 명확한 KeyError로 실패)."""
    roots = feed_spec["root"] if isinstance(feed_spec["root"], list) else [feed_spec["root"]]

    def _ref_id(name):
        entry = ctx.sized.get(name)
        if entry is not None and "ID" in entry:
            return entry["ID"]
        return ctx.seed_currents[name]

    total = sum(_ref_id(r) for r in feed_spec["reference"])
    for root in roots:
        ctx.seed_currents[root] = theta_value * total


def _feed_diode_stack_target(feed_spec: dict, theta_value: float, ctx: SizingContext) -> None:
    """`{"type":"C","target":<device>,"reference":<device>}` — diode-stack replica 면적
    원칙: `target`을 `reference`의 replica(같은 gm_id/L/VDS/VS 동작점을 그대로 물려받고,
    W/ID/gm/gds는 `theta_value`(면적비 K_replica) 배)로 채운다.

    2026-08-03 확장(배치 7-5 실행 중 발견): 원래는 `W`만 설정했는데, `target`이
    `device_roles`의 `gm_id_role`을 갖는 경우(예: K_replica의 M9a) 그 단계가 "ID가 아직
    없다"로 실패했다 — replica는 reference와 같은 VGS(=같은 gm_id/L/VDS/VS)를 그대로
    물려받는다는 전제이므로 `gm=ID*gm_id`, `gds=gm/gm_gds_ratio(gm_id,L,VDS,VS)` 둘 다
    gm_id/L/VDS/VS가 불변이면 `ID`와 같은 비율로 스케일된다(LUT 재조회 없이 산술만으로
    정확) — `ID`/`gm`/`gds`도 함께 스케일해 채운다. ⚠️ `target`의 kind가 `reference`와
    다르면(예: 상보쌍 replica) 이 근사가 성립하지 않는다 — 지금 쓰는 K_replica(M9a<-M15,
    둘 다 pmos)는 kind 일치가 확인된 경우만이다(self-test 참고)."""
    target, reference = feed_spec["target"], feed_spec["reference"]
    ref = ctx.sized[reference]
    entry = {"W": theta_value * ref["W"]}
    for key in ("gm_id", "L", "vds", "vs", "kind"):
        if key in ref:
            entry[key] = ref[key]
    for key in ("ID", "gm", "gds"):
        if key in ref:
            entry[key] = theta_value * ref[key]
    if "L" in entry:
        # "compensation"과 동급으로 취급되는 권위 있는 L 출처(아래 matching_pairs L 우선순위
        # 검사의 _AUTHORITATIVE_L_SOURCES 참고) -- device_roles의 L_role(휴리스틱 배수)이
        # 함부로 덮어쓰지 못하게 표시한다.
        entry["_L_source"] = "replica"
    ctx.sized[target] = entry


def _feed_gm_target_convention(feed_spec: dict, theta_value: float, ctx: SizingContext) -> None:
    """`{"type":"B","tag":"servo","target":<device>,"omega_key":...,"cap_key":...,"L":...,
    "W":...[,"vds","vs","gm_id_bounds"]}` — N×ωc 컨벤션(예: CMFB 대역폭 배수): `gm_target =
    theta_value(N) * ctx.spec[omega_key] * ctx.spec[cap_key]`를 계산해
    `solve_id_for_target_gm()`(B엔진)으로 `target`을 사이징하고 결과를 `ctx.sized[target]`에
    채운다."""
    target = feed_spec["target"]
    gm_target = theta_value * ctx.spec[feed_spec["omega_key"]] * ctx.spec[feed_spec["cap_key"]]
    result = solve_id_for_target_gm(
        ctx.spec["lut"], feed_spec["L"], feed_spec.get("vds", 0.6), feed_spec.get("vs", 0.0),
        feed_spec["W"], gm_target, gm_id_bounds=tuple(feed_spec.get("gm_id_bounds", (2.0, 30.0))))
    ctx.sized[target] = {"ID": result.ID, "gm": result.gm, "gm_id": result.gm_id,
                          "W": feed_spec["W"], "L": feed_spec["L"]}


def _feed_settling_split(feed_spec, theta_value: float, ctx: SizingContext) -> None:
    """`"settling_split"`(bare 문자열) 또는 `{"type":"settling_split","output_key":...,
    "total_key":...}` — B엔진에 직접 붙지 않고(§7.3.2 콜아웃 "진짜 예외") `theta_value`(비율)
    `* ctx.spec[total_key]`를 `ctx.derived[output_key]`에 저장하는 순수 스칼라 파생이다 —
    이 값을 소비해 실제 gm 목표를 만드는 닫힌식(Level1→3)은 호출자가 `optimize_full_circuit_
    budget()` 바깥/`topology_fn` 구성 시점에서 이어붙인다."""
    if isinstance(feed_spec, str):
        output_key, total_key = "t_slew", "t_settle_total"
    else:
        output_key = feed_spec.get("output_key", "t_slew")
        total_key = feed_spec.get("total_key", "t_settle_total")
    ctx.derived[output_key] = theta_value * ctx.spec[total_key]


def _feed_metric_stage_budget(feed_spec: dict, theta_value: float, ctx: SizingContext) -> None:
    """`{"type":"metric_stage_budget","metric":"gain_db","devices":[...][,"gm_id","vds","vs"]}`
    — `theta_value` 자체가 채널길이 `L`이다. 지정된 `devices`(이미 `ID`가 확정돼 있어야 함,
    A/B엔진 이후에만 호출)의 `L`/`W`/`gm`/`gds`를 이 `L`에서 재계산해 `ctx.sized`에 반영한다
    (F엔진 `gain_stages_sum` metric이 바로 이 값을 읽음). gain 외 metric(noise/power stage
    budget)은 아직 미구현(§7.3.2 콜아웃에 이미 명시된 유보 — 이름은 일반화했지만 핸들러
    내부 계산은 gain_db 경로만 실제 동작)."""
    if feed_spec.get("metric", "gain_db") != "gain_db":
        raise ValueError(f"metric_stage_budget 핸들러는 gain_db만 구현됨(§7.3.2 유보) -- "
                          f"{feed_spec.get('metric')!r}은 미구현")
    L = theta_value
    lut = ctx.spec["lut"]
    vds, vs = feed_spec.get("vds", 0.6), feed_spec.get("vs", 0.0)
    gm_id = feed_spec.get("gm_id", 15.0)
    for name in feed_spec["devices"]:
        entry = ctx.sized.setdefault(name, {})
        if "ID" not in entry:
            raise ValueError(f"{name}의 ID가 아직 없다 -- metric_stage_budget은 ID가 이미 "
                              f"확정된 뒤(A/B엔진 이후)에만 L을 배정할 수 있다")
        ID = entry["ID"]
        idu = lut.gm_id_to_id_density(gm_id, L, vds, vs)
        gm_gds = lut.gm_gds_ratio(gm_id, L, vds, vs)
        gm = gm_id * ID
        entry.update({"L": L, "W": L * ID / idu, "gm": gm, "gds": gm / gm_gds, "gm_id": gm_id})


_THETA_FEED_REGISTRY: dict = {
    "settling_split":       FeedHandler(_feed_settling_split, touches=["B"]),
    "C":                    FeedHandler(_feed_diode_stack_target, touches=["C"]),
    "B":                    FeedHandler(_feed_gm_target_convention, touches=["B"]),
    "A":                    FeedHandler(_feed_root_ratio, touches=["A"]),
    "metric_stage_budget":  FeedHandler(_feed_metric_stage_budget, touches=["B", "F"]),
    # 새 feed 타입이 필요해지면 여기 한 줄만 등록하면 된다 -- optimize_full_circuit_budget()은
    # 수정하지 않는다(§7.3.2 확정 설계, _COMPENSATION_REGISTRY/_METRICS_REGISTRY와 동일 계약).
}


def apply_theta_feed(feed_spec, theta_value: float, ctx: SizingContext) -> None:
    """theta 값 하나를 A/B/C/F 엔진의 실제 계산 상태(`ctx`)에 반영한다. `feed_spec`은
    문자열(`"settling_split"`) 또는 `{"type": ..., ...}` 형태 — 어느 쪽이든 `feed_type`만
    뽑아 registry에서 핸들러를 찾는다. 등록 안 된 타입은 즉시 `ValueError`."""
    feed_type = feed_spec if isinstance(feed_spec, str) else feed_spec["type"]
    entry = _THETA_FEED_REGISTRY.get(feed_type)
    if entry is None:
        raise ValueError(f"등록되지 않은 feeds 타입: {feed_type!r} -- "
                          f"_feed_*() 핸들러를 새로 작성해 _THETA_FEED_REGISTRY에 등록할 것")
    entry.fn(feed_spec, theta_value, ctx)


_CONSTRAINT_OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt,
                   "<": operator.lt, "==": operator.eq}


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def optimize_full_circuit_budget(topology_path: str, spec: dict,
                                  grid_points_per_theta: int = 5) -> dict:
    """배치 7-3d/7-5 — spec(topology.json 경로 + design spec)만 받아 instance.json에 바로
    옮길 수 있는 완성된 결과를 반환하는 **단일 진입점 harness**(2026-07-31 확장,
    do.md §10 "spec→instance.json 전체 workflow"를 실제로 실행 가능한 함수 하나로 묶음).

    **AI는 이 함수 하나만 호출한다** — `propagate_topology_forced_currents()`/
    `solve_id_for_target_gm()`/`select_layout_tool()` 등 원소 함수는 이 함수 내부에서만
    호출되고, 실패 원인 분석 시에만 개별적으로 들여다보는 대상이다(2026-07-31 사용자 확정:
    "이걸 순차적으로 실행시키는 harness함수 하나로 만들고 ai는 그걸 하나만 실행할 수 있도록").
    이 함수가 필요한 선언(theta/metrics/device_roles/compensation.stage_devices)을 만나지
    못하면 즉시 구체적인 `ValueError`를 낸다 — AI가 그 자리를 코드/공식으로 메우는 대신
    "topology.json의 어느 필드가 비어있다"는 신호를 그대로 돌려받는다(2026-07-31 사고 재발
    방지: Eq.6을 근거 없이 재구성해 등록했다가 되돌린 사건 참고).

    **내부 실행 순서**(do.md §10과 대응):
    1. `load_topology()` — connectivity + `sizing_roles`/`device_roles`/`compensation` 선언.
    2. `derive_stack_groups()` — θ-무관, 1회만(플로어플랜용 가로 그룹).
    3. θ 후보마다(또는 θ 없으면 1회): `apply_theta_feed()` → A엔진(`propagate_topology_
       forced_currents()`, `matching_pairs`의 `current_mirror` 쌍은 비율 미선언 시 1:1
       기본값으로 자동 시드) → compensation 있으면 `optimize_multistage()` 실행 후
       `compensation.stage_devices`로 소자별 병합 → `device_roles`의 `L_role`/
       `vertical_stack_id`(헤드룸, `allocate_stack_headroom()`)/`gm_id_role`
       (`search_gm_id_for_role()`) 순서로 나머지 소자 사이징 → `compute_metric()`.
    4. `objective`/`constraints`로 θ* 선택(grid search, 재현성/최적성 보장).
    5. 넷리스트 전체가 사이징됐으면(`assign_finger_geometry()`가 요구하는 W가 전부 있으면)
       `assign_finger_geometry()` → `run_topology_pipeline()` → FAIL이면
       `repair_matching_safety()`.

    `spec` 주요 키(회로마다 다름, 전부 선택이지만 해당 단계가 필요로 하면 없을 시 에러):
    `"lut_by_kind"`({"nmos":LUT,"pmos":LUT}), `"vdd"`, `"L_candidates"`/`"VDS_candidates"`/
    `"gm_id_grid"`(compensation `optimize_multistage()`용), `"L_min"`/`"L_min_by_kind"`,
    `"W_bounds"`, `"min_vds_by_role"`, `"min_finger_w"`/`"max_finger_w"`, `"floorplan_hints"`,
    `"cell_groups"`, `"known_sizing"`, 그 외 theta feed가 참조하는 이름 붙은 상수.

    반환: `{"theta_star", "sizing", "metrics", "sizing_overrides", "pipeline_result",
    "audit_ok"}` — `sizing_overrides`/`pipeline_result`는 넷리스트 전체가 사이징되지 않으면
    `None`(부분 결과만 반환 — 단순 회로/미완성 선언 지원, §7.3.2 검증 (b)와 동일한 하위호환
    사상). 모든 θ 격자점이 infeasible이면 `ValueError`.

    ⚠️ 정직한 한계(2026-07-31): diode-stack(C유형) 전류의 `solve_diode_stack_current()`
    자동 병합은 아직 없다(K_replica 면적비 theta feed는 W를 직접 설정할 뿐, KVL 전류 역산은
    미연결) — 이런 소자가 있는 회로는 `device_roles`로 해당 소자의 `ID`를 `known_sizing`에
    직접 시딩해 우회할 것."""
    transistors, meta = load_topology(topology_path)
    roles = meta.get("sizing_roles") or {}
    thetas = roles.get("theta") or []
    metrics_specs = roles.get("metrics") or {}
    objective = roles.get("objective") or {}
    constraints = roles.get("constraints") or []
    # "_"로 시작하는 키(예: "_comment")는 이 프로젝트 전역 관례상 문서용 주석 필드다 --
    # 실제 소자 이름이 "_"로 시작할 일은 없으므로 안전하게 걸러낸다.
    device_roles = {k: v for k, v in (meta.get("device_roles") or {}).items()
                     if not k.startswith("_")}
    comp = meta.get("compensation")
    pairs_meta = meta["symmetry"]["matching_pairs"]
    kind_of = {t.name: t.kind for t in transistors}

    # current_mirror 그룹은 2개 이름뿐 아니라 N개(예: 하나의 기준을 여러 소자가 미러하는
    # 경우, current_reuse_telescopic_ota의 M36a/M36b/M39)일 수 있다 -- names[0]을 기준으로
    # 나머지 전부에 1:1 비율을 시드한다(2026-08-01, 3개짜리 그룹에서 실제로 발견된 gap 수정).
    auto_mirror_ratios = {(p["names"][0], n): 1.0
                           for p in pairs_meta if p["kind"] == "current_mirror"
                           for n in p["names"][1:]}

    # derive_stack_groups()는 두 군데 쓰인다 -- (1) A엔진의 stack_id 기반 "같은 전류" 전파
    # (2단자 내부노드로 병합된 진짜 KCL 사실, 절대 override하면 안 됨), (2) assign_finger_
    # geometry()의 "같은 finger_w를 공유할 물리 행" 판단(floorplan 선택이라 override 가능).
    # 자동 병합이 finger_w 비율-호환 안 되는 소자를 한 그룹으로 묶으면(예: 입력쌍과 그 부하
    # 미러는 KCL로 전류는 같아도 W는 전혀 다름) assign_finger_geometry()가 명시적 ValueError로
    # 알려준다(조용히 억지 배정 안 함) -- 그때 호출자가 stack_groups_override(선택)로 (2)만
    # 물리적으로 재구성해 선언한다(cell_groups가 spine_groups를 override하는 것과 같은 패턴,
    # 여전히 선언일 뿐 AI가 즉석 코드로 우회하는 게 아니다) -- (1)은 항상 원본 그대로 쓴다.
    stack_groups_kcl = derive_stack_groups(transistors, [tuple(p["names"]) for p in pairs_meta])
    stack_groups_geometry = spec.get("stack_groups_override") or stack_groups_kcl
    stack_id_of = {name: sid for sid, members in stack_groups_kcl.items() for name in members}
    transistors_stackid = [_dc_replace(t, stack_id=stack_id_of.get(t.name)) for t in transistors]

    # matching_pairs만으로 만든 "동일 사이징값" 그룹(위 stack_groups와 다른 개념 -- stack_groups는
    # 2단자 내부노드까지 병합해 "같은 전류"를 묶지만, 여기는 순수 matching_pairs만으로 "같은
    # gm_id/VDS/W를 가져야 하는 매칭쌍"만 묶는다. 예: two_stage_ota의 M3(load)와 M1(input)은
    # D3 노드로 전류는 같지만 VDS/W는 서로 다르다 -- stack_groups로 묶으면 헤드룸 집계 때
    # M1/M2(diff pair) 값을 두 번 합산하는 버그가 생겨 별도로 둔다).
    _vparent = {t.name: t.name for t in transistors}

    def _vfind(x):
        while _vparent[x] != x:
            _vparent[x] = _vparent[_vparent[x]]
            x = _vparent[x]
        return x

    for p in pairs_meta:
        # matching_pairs의 names는 2개뿐 아니라 N개일 수 있다(current_mirror 기준 소자를
        # 여러 소자가 미러하는 경우) -- 인접 쌍을 체인으로 union하면 그룹 전체가 하나로
        # 묶인다(2026-08-01, 3개짜리 그룹에서 실제로 발견된 unpack 에러 수정).
        for a, b in zip(p["names"], p["names"][1:]):
            ra, rb = _vfind(a), _vfind(b)
            if ra != rb:
                _vparent[ra] = rb

    def _evaluate(theta_values: dict):
        ctx = SizingContext(spec=spec)
        ctx.sized.update({k: dict(v) for k, v in spec.get("known_sizing", {}).items()})
        ctx.mirror_ratios.update(auto_mirror_ratios)

        # compensation을 A엔진/theta보다 먼저 실행한다 -- 순서가 중요하다: (1) A엔진의
        # 직렬-스택 전파(예: two_stage_ota의 M3/M4가 M1/M2와 같은 stack_groups 그룹)가
        # compensation이 정한 M1/M2의 ID를 시드로 써야 하고, (2) theta의 "A" root_ratio feed도
        # compensation이 정한 소자의 ID를 참조할 수 있다(예: 배치 7-3 current-reuse의
        # r_biasgen이 신호경로 총전류를 참조). compensation 자체는 theta/A엔진 결과에
        # 의존하지 않으므로(topology_fn은 spec만으로 완전 결정) 먼저 실행해도 안전하다.
        if comp:
            stage_devices = comp.get("stage_devices")
            if not stage_devices:
                raise ValueError(
                    f"compensation이 있는데 stage_devices가 없다({topology_path}) -- "
                    f"topology.json의 compensation.stage_devices를 채울 것")
            stage_objective = spec.get("stage_objective", "power")
            if stage_objective == "power" and spec.get("stage_w_max") is None:
                raise ValueError(
                    "compensation objective='power'인데 spec['stage_w_max']가 없다 -- "
                    "optimize_multistage()의 gm은 topology_fn이 이미 고정하므로 w_max 없이는 "
                    "'전력 최소화'가 'gm/ID를 격자 최대치로'와 같아져 W가 발산한다(문서화된 물성, "
                    "optimize_multistage() docstring 참고) -- spec['stage_w_max']를 지정할 것")
            topology_fn = _COMPENSATION_REGISTRY[comp["function"]](
                **{k: spec[k] for k in comp["parameters"]})
            luts = [spec["lut_by_kind"][kind_of[grp[0]]] for grp in stage_devices]
            comp_result = optimize_multistage(
                topology_fn, luts, spec["L_candidates"], spec["VDS_candidates"], spec["gm_id_grid"],
                objective=stage_objective, gain_min=spec.get("stage_gain_min"),
                w_max=spec.get("stage_w_max"),
                shared_gm_id_groups=comp.get("shared_gm_id_groups"))
            if comp_result is None:
                raise ValueError("optimize_multistage()가 실행가능점을 못 찾음 -- "
                                  "L_candidates/VDS_candidates/gm_id_grid를 확인하세요")
            for i, grp in enumerate(stage_devices):
                st = comp_result["stages"][i]
                gm_i = comp_result["gms"][i]
                lut_i = luts[i]
                gds_i = gm_i / lut_i.gm_gds_ratio(st["gm_id"], st["L"], st["VDS"], 0.0)
                for name in grp:
                    ctx.sized[name] = {"gm": gm_i, "gm_id": st["gm_id"], "L": st["L"],
                                        "vds": st["VDS"], "vs": 0.0, "W": st["W"],
                                        "ID": gm_i / st["gm_id"], "gds": gds_i, "kind": kind_of[name],
                                        "_L_source": "compensation"}

        # A엔진 1차 패스(theta 루프보다 먼저, 2026-08-03 배치 7-5 실행 중 발견) -- compensation이
        # 정한 ID만으로 이미 결정되는 KCL 스택(예: current_reuse_telescopic_ota의 M1a-M2a-
        # M3a-M4a-M5, compensation이 M1a/M4a를 정하는 순간 나머지 스택 멤버 전부가 이미 위상만으로
        # 확정됨)은 theta 루프가 시작되기 전에 미리 풀어둬야 한다 -- `metric_stage_budget`
        # feed(L_cascode 등)가 "devices의 ID가 이미 있어야 한다"고 요구하는데, 그 ID가 A엔진
        # 산출물이면 이 feed가 theta 루프 "안에서" 호출되는 이상 이 시점에 이미 있어야 한다.
        # (r_biasgen처럼 theta 자신이 새로 시드하는 전류는 아직 없으므로 이 1차 패스에서 못 풀리는
        # 게 정상 -- 그건 아래 2차 패스가 담당한다.)
        pre_theta_seeds = {n: e["ID"] for n, e in ctx.sized.items() if "ID" in e}
        for name, idv in propagate_topology_forced_currents(
                transistors_stackid, pre_theta_seeds, ctx.mirror_ratios).items():
            ctx.sized.setdefault(name, {}).setdefault("ID", idv)

        for theta in thetas:
            if theta["name"] in theta_values:
                apply_theta_feed(theta["feeds"], theta_values[theta["name"]], ctx)

        # A엔진 2차 패스 seed = compensation + 1차 패스가 이미 정한 ID 전부(위 병합 결과) +
        # theta가 명시적으로 시드한 것(ctx.seed_currents) -- 이래야 compensation-stage 소자와
        # 같은 stack_groups 그룹(2단자 내부노드로 병합된 A유형 소자, 예: two_stage_ota의 M3/M4)이
        # 그 ID를 물려받고, r_biasgen처럼 theta가 새로 시드한 전류도 전파된다. propagate_
        # topology_forced_currents()는 이미 알려진 이름을 다시 계산하지 않으므로(고정점까지
        # 반복하는 멱등 연산) 1차 패스와 결과가 겹쳐도 안전하다.
        combined_seeds = {n: e["ID"] for n, e in ctx.sized.items() if "ID" in e}
        combined_seeds.update(ctx.seed_currents)
        a_ids = propagate_topology_forced_currents(transistors_stackid, combined_seeds,
                                                    ctx.mirror_ratios)
        for name, idv in a_ids.items():
            ctx.sized.setdefault(name, {}).setdefault("ID", idv)

        # "권위 있는"(휴리스틱이 아니라 spec/replica 관계에서 직접 유도된) L 출처 태그 —
        # 2026-08-03 확장: 원래 "compensation"만 있었는데, C타입 replica feed(K_replica 등,
        # `_feed_diode_stack_target()`)가 reference의 L을 그대로 물려받는 것도 같은 성격의
        # 권위 있는 값이라 device_roles의 L_role(휴리스틱 배수)이 덮어쓰면 안 된다 —
        # "compensation"이었을 때와 정확히 같은 이유(spec 기반 근거가 있는 쪽이 이긴다)로
        # "replica"도 이 집합에 추가.
        _AUTHORITATIVE_L_SOURCES = {"compensation", "replica"}

        for name, dr in device_roles.items():
            if dr.get("L_role"):
                entry = ctx.sized.setdefault(name, {})
                if entry.get("_L_source") not in _AUTHORITATIVE_L_SOURCES:
                    L_min = spec.get("L_min_by_kind", {}).get(kind_of[name], spec.get("L_min"))
                    entry["L"] = select_L_by_role(dr["L_role"], L_min)
                    entry["_L_source"] = "L_role"

        # matching_pairs로 선언된 두 소자는 반드시 같은 L을 써야 매칭이 성립한다(전류미러/
        # 차동쌍의 표준 관례 -- 실제 전류미러가 서로 다른 L을 쓰면 매칭 정확도가 무너진다).
        # compensation(stage_devices)/replica(C타입 feed)과 device_roles(L_role)은 서로
        # 독립된 경로로 L을 정하므로 "우연히 같음"에 기대지 않고 명시적으로 검증+전파한다.
        # 값이 다를 때 무조건 에러로 끝내지 않는다 -- compensation/replica는 실제 스펙(GBW/
        # PM/Z 등)이나 명시적 replica 관계에서 유도된 값이라 "더 근거 있는" 쪽이고, L_role은
        # (mirror/bias_replica 등) 휴리스틱이라 그 값에 맞춰 재설계돼도 무방하다: 한쪽이
        # 권위 있는 출처면 그 값으로 다른 쪽을 덮어써서 전파한다(L_role 쪽은 아직 gm_id/W가
        # 확정 전이므로 이후 gm_id_role 루프가 새 L로 자연히 다시 사이징한다 -- 별도 재계산
        # 코드 불필요). 양쪽 다 권위 있는 출처거나 양쪽 다 L_role인데 값이 다르면 스펙 근거로
        # 우선순위를 가릴 수 없는 진짜 선언 불일치이므로 그때만 ValueError(조용히 넘어가지
        # 않음 -- 매칭 정확도는 안전-critical).
        for _p in pairs_meta:
            # names는 2개뿐 아니라 N개일 수 있다(current_mirror 기준 소자를 여러 소자가
            # 미러하는 경우) -- 인접 쌍 체인으로 같은 검증+전파 로직을 적용한다(2026-08-01,
            # 3개짜리 그룹에서 실제로 발견된 unpack 에러 수정).
            for _pa, _pb in zip(_p["names"], _p["names"][1:]):
                _ea = ctx.sized.setdefault(_pa, {})
                _eb = ctx.sized.setdefault(_pb, {})
                _La, _Lb = _ea.get("L"), _eb.get("L")
                if _La is None and _Lb is not None:
                    _ea["L"] = _Lb
                elif _Lb is None and _La is not None:
                    _eb["L"] = _La
                elif _La is not None and _Lb is not None and abs(_La - _Lb) > 1e-15:
                    _sa, _sb = _ea.get("_L_source"), _eb.get("_L_source")
                    _sa_auth, _sb_auth = _sa in _AUTHORITATIVE_L_SOURCES, _sb in _AUTHORITATIVE_L_SOURCES
                    if _sa_auth and not _sb_auth:
                        _eb["L"] = _La
                    elif _sb_auth and not _sa_auth:
                        _ea["L"] = _Lb
                    else:
                        raise ValueError(
                            f"matching pair ({_pa},{_pb}, kind={_p['kind']})의 L이 서로 다른데"
                            f"(L_{_pa}={_La}, L_{_pb}={_Lb}) 어느 쪽도 spec 기반(compensation/replica)이 "
                            f"아니라(_L_source={_sa!r}/{_sb!r}) 자동으로 우선순위를 가릴 근거가 "
                            f"없다 -- topology.json의 device_roles L_role/L_min_by_kind 선언을 "
                            f"확인할 것")

        vertical_groups = defaultdict(list)
        group_ref_device = {}
        for name, dr in device_roles.items():
            vsid = dr.get("vertical_stack_id")
            if vsid:
                vertical_groups[vsid].append(name)
                ref = dr.get("budget_reference_device")
                if ref:
                    group_ref_device[vsid] = ref

        # 폴디드 캐스코드처럼 한 vertical_stack_id 그룹이 vdd~gnd 전체가 아니라 vdd~(다른
        # 그룹이 이미 확정한 소자의 드레인 전압)만큼만 예산으로 갖는 경우를 위한 선택적 필드
        # (배치 7-5b, 2026-07-31, NMCNR 회로 계기 -- 사용자와 함께 설계). `budget_reference_
        # device`가 가리키는 소자는 반드시 다른(먼저 처리되는) vertical_stack_id 그룹 소속이어야
        # 하므로, 그 의존관계대로 그룹을 위상정렬한다(순환 참조는 즉시 ValueError).
        def _ref_depth(vsid, _seen=frozenset()):
            ref_dev = group_ref_device.get(vsid)
            if ref_dev is None:
                return 0
            ref_vsid = device_roles.get(ref_dev, {}).get("vertical_stack_id")
            if ref_vsid == vsid or vsid in _seen:
                raise ValueError(
                    f"vertical_stack_id 그룹 '{vsid}'의 budget_reference_device가 순환 참조한다")
            return 1 + _ref_depth(ref_vsid, _seen | {vsid})

        for vsid in sorted(vertical_groups.keys(), key=_ref_depth):
            members = vertical_groups[vsid]
            # matching_pairs로 묶인 값-동일 그룹(_vfind)당 대표 1개씩만 집계 -- diff pair/미러
            # 쌍의 두 소자를 헤드룸 예산에 중복으로 합산하지 않기 위함(위 _vfind 주석 참고).
            seen_value_groups = set()
            known_vds_sum = 0.0
            unresolved = []
            for m in members:
                vgrp = _vfind(m)
                if vgrp in seen_value_groups:
                    continue
                seen_value_groups.add(vgrp)
                vds = ctx.sized.get(m, {}).get("vds")
                if vds is not None:
                    known_vds_sum += vds
                else:
                    unresolved.append(m)
            if not unresolved:
                continue
            base_budget = spec["vdd"]
            ref_dev = group_ref_device.get(vsid)
            if ref_dev is not None:
                ref_vds = ctx.sized.get(ref_dev, {}).get("vds")
                if ref_vds is None:
                    raise ValueError(
                        f"'{vsid}'의 budget_reference_device('{ref_dev}')가 아직 VDS 미확정 -- "
                        f"참조 소자가 속한 vertical_stack_id 그룹이 먼저 풀려야 한다(순환/선언 확인)")
                base_budget = spec["vdd"] - ref_vds
            remaining_vdd = base_budget - known_vds_sum
            stack_entries = [{"name": m, "role": device_roles[m]["headroom_role"],
                               "min_vds": spec.get("min_vds_by_role", {}).get(
                                   device_roles[m]["headroom_role"], 0.2)}
                              for m in unresolved]
            headroom = allocate_stack_headroom(remaining_vdd, stack_entries)
            for m in unresolved:
                vds_val = headroom[m]
                vgrp = _vfind(m)
                for other in members:  # 같은 값-그룹의 나머지 멤버(예: M4)에도 동일 VDS 전파
                    if _vfind(other) == vgrp:
                        other_entry = ctx.sized.setdefault(other, {})
                        other_entry["vds"] = vds_val
                        if ref_dev is not None:
                            # 이 그룹의 실제 소스 기준점은 0V(vss)가 아니라 ref_dev의 드레인
                            # 전압(=ref_dev 자신의 vds, source=vss이므로) -- 폴딩 노드 위에
                            # 앉은 소자의 body-effect/LUT 조회가 vs=0을 잘못 쓰지 않도록 전파.
                            other_entry.setdefault("vs", ref_vds)

        for name, dr in device_roles.items():
            if not dr.get("gm_id_role"):
                continue
            entry = ctx.sized.get(name, {})
            if "ID" not in entry:
                raise ValueError(f"{name}: A엔진(propagate_topology_forced_currents)이 전류를 "
                                  f"못 정했다 -- mirror_ratios/seed_currents(theta feeds)를 확인할 것")
            L, vds = entry.get("L"), entry.get("vds")
            if L is None or vds is None:
                raise ValueError(f"{name}: L 또는 VDS가 미확정 -- device_roles의 L_role/"
                                  f"vertical_stack_id 선언을 확인할 것")
            # ctx.sized에 이미 vs가 있으면(폴디드 노드처럼 budget_reference_device로 동적
            # 전파된 값) 그걸 우선한다 -- device_roles의 vs는 정적 기본값(보통 0.0)일 뿐.
            vs = entry.get("vs", dr.get("vs", 0.0))
            lut = spec["lut_by_kind"][kind_of[name]]
            W_bounds = spec.get("W_bounds", (1e-6, 200e-6))
            gm_id = search_gm_id_for_role(lut, L, vds, vs, entry["ID"], dr["gm_id_role"], W_bounds)
            gm = entry["ID"] * gm_id
            w = size_transistor(gm, gm_id, L, lut, vds, vs).W
            gds = gm / lut.gm_gds_ratio(gm_id, L, vds, vs)
            ctx.sized[name] = {**entry, "gm_id": gm_id, "gm": gm, "W": w, "gds": gds,
                                "kind": kind_of[name], "vs": vs}

        metrics_result = {name: compute_metric(mspec, ctx) for name, mspec in metrics_specs.items()}
        return ctx, metrics_result

    if not thetas:
        ctx, metrics_result = _evaluate({})
        theta_star, sizing = {}, ctx.sized
    else:
        names = [t["name"] for t in thetas]
        # bounds[0]==bounds[1](고정값 -- 예: KCL 순수 합산을 표현하는 ratio=1.0 theta,
        # M5/M11a/M38 등)인 theta는 grid_points_per_theta와 무관하게 1개 점만 평가한다
        # (2026-08-03, 배치 7-5 실행 중 발견): 그렇지 않으면 이런 "설계 자유도 없는" theta가
        # 하나 늘 때마다 전체 격자 조합 수가 grid_points_per_theta배씩 곱해져(현재 회로는
        # 이런 고정 theta가 8개라 2^8=256배) 탐색이 사실상 끝나지 않았다(실측: 40분+ 무응답,
        # 강제 종료 후 발견) — 값이 어차피 하나뿐이니 여러 번 평가할 이유가 없다.
        grids = [[t["bounds"][0]] if t["bounds"][0] == t["bounds"][1] else
                 [_lerp(t["bounds"][0], t["bounds"][1], i / (grid_points_per_theta - 1))
                  for i in range(grid_points_per_theta)] for t in thetas]
        best = None
        last_metrics, last_theta = None, None
        for combo in itertools.product(*grids):
            theta_values = dict(zip(names, combo))
            ctx, metrics_result = _evaluate(theta_values)
            last_metrics, last_theta = metrics_result, theta_values
            feasible = all(_CONSTRAINT_OPS[c["op"]](metrics_result[c["metric"]], c["value"])
                           for c in constraints)
            if not feasible:
                continue
            obj_val = metrics_result[objective["minimize"]] if "minimize" in objective \
                else -metrics_result[objective["maximize"]]
            if best is None or obj_val < best[0]:
                best = (obj_val, theta_values, ctx.sized, metrics_result)
        if best is None:
            # 2026-08-03(배치 7-5 디버깅 중 추가) -- "infeasible"만 알려주면 어느 제약이 왜
            # 안 맞는지 알 방법이 없어 매번 코드를 임시로 고쳐 값을 찍어봐야 했다 -- 마지막으로
            # 평가한 조합의 실제 metrics와 위반된 제약을 에러 메시지에 그대로 포함시킨다.
            _violations = [f"{c['metric']}{c['op']}{c['value']}(실제={last_metrics.get(c['metric'])})"
                            for c in constraints
                            if last_metrics is not None and
                            not _CONSTRAINT_OPS[c["op"]](last_metrics[c["metric"]], c["value"])]
            raise ValueError(
                f"모든 theta 격자점이 infeasible -- bounds/constraints를 확인하세요. "
                f"마지막 평가 조합의 theta={last_theta}, metrics={last_metrics}, "
                f"위반된 제약={_violations}")
        _, theta_star, sizing, metrics_result = best

    sizing_overrides, pipeline_result, audit_ok = None, None, None
    if all(t.name in sizing and "W" in sizing[t.name] for t in transistors):
        sizing_overrides = assign_finger_geometry(
            sizing, stack_groups_geometry, area_priors=spec.get("area_priors"),
            min_finger_w=spec.get("min_finger_w", 1e-6), max_finger_w=spec.get("max_finger_w", 40e-6))
        pipeline_result = run_topology_pipeline(
            topology_path, sizing_overrides, floorplan_hints=spec.get("floorplan_hints"),
            cell_groups=spec.get("cell_groups"))
        audit = pipeline_result["audit_row_split"]
        audit_ok = audit.ok if hasattr(audit, "ok") else all(v.ok for v in audit.values())
        if not audit_ok:
            rows = split_into_stacks(pipeline_result["transistors"])
            # audit_row_split()/repair_matching_safety()는 순수 2-tuple 쌍 계약이다(docstring:
            # "[(name_a, name_b), ...]") -- names가 2개보다 많은 그룹(예: 기준 소자 하나를
            # 여러 소자가 미러하는 current_mirror)은 모든 쌍별 조합으로 펼쳐서 넘긴다
            # (2026-08-01, 3개짜리 그룹에서 실제로 발견된 unpack 에러 수정).
            matching_pairs_tuples = [pair for p in pairs_meta
                                      for pair in itertools.combinations(p["names"], 2)]
            pair_kinds = {pair: p["kind"] for p in pairs_meta
                          for pair in itertools.combinations(p["names"], 2)}
            repaired_rows, repaired_audit = repair_matching_safety(rows, matching_pairs_tuples, pair_kinds)
            pipeline_result = dict(pipeline_result, repaired_rows=repaired_rows,
                                    repaired_audit=repaired_audit)
            audit_ok = repaired_audit.ok

    return {"theta_star": theta_star, "sizing": sizing, "metrics": metrics_result,
            "sizing_overrides": sizing_overrides, "pipeline_result": pipeline_result,
            "audit_ok": audit_ok}


# ---------------------------------------------------------------------------
# 7) 사용 예시 — toy LUT로 end-to-end 실행 (실제 공정 데이터로 교체 시 동일하게 동작)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    try:  # Windows 콘솔 기본 코드페이지(cp949/cp1252)가 한글/em-dash를 못 찍는 문제 방지
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # 예시 스펙 — 실제 값은 자신의 설계 스펙으로 교체
    fT_target = 100e6      # 100 MHz
    C_load = 1e-12         # 1 pF
    L = 0.5e-6             # 500nm
    vds = 0.6
    gm_id_candidates = [10, 15, 20, 25]  # V^-1, moderate~weak inversion 후보 스윕

    try:
        import numpy  # noqa: F401
    except ImportError:
        print("[skip] numpy가 없어 SemiEmpiricalGmIdLUT/build_toy_lut을 실행할 수 없습니다 "
              "(`pip install numpy`). 그 외 함수(gm_from_fT, size_transistor 등)는 numpy 없이도 동작합니다.")
        raise SystemExit(0)

    print("# toy LUT(E.K.V. 해석식 합성 데이터) 기반 실행 예시 — 숫자는 데모용, 실제 공정값 아님")
    lut = build_toy_lut()

    for gm_id in gm_id_candidates:
        try:
            r = converge_with_parasitics(fT_target, C_load, gm_id, L, lut, vds)
            fnqs_ok = check_quasi_static(fT_target, r.gm, lut.cgg_absolute(gm_id, L, vds, 0.0, r.W)).ok
            print(f"gm/ID={gm_id:5.1f}  ID={r.ID*1e6:8.2f}uA  W={r.W*1e6:8.2f}um  "
                  f"gain={r.gain:6.1f}  quasi-static={'OK' if fnqs_ok else 'FAIL'}")
        except ValueError as e:
            print(f"gm/ID={gm_id:5.1f}  [불가] {e}")

    print()
    print("# find_optimal_sizing() 데모 — gain 제약에서 전력/면적 각각 최소인 점 자동 탐색")
    gm_id_grid = [i * 0.5 for i in range(4, 58)]  # 2.0 ~ 28.5 S/A
    L_candidates = lut.L_grid
    VDS_candidates = lut.VDS_grid
    gain_min_demo = 30  # toy LUT 규모에 맞춘 데모용 임계값(실제 스펙은 자신의 것으로 교체)
    best_power, cands = find_optimal_sizing(
        lut, L_candidates, VDS_candidates, gm_id_grid, fT=fT_target, C=C_load,
        objective="power", gain_min=gain_min_demo, quasi_static_margin=0.1)
    best_area, _ = find_optimal_sizing(
        lut, L_candidates, VDS_candidates, gm_id_grid, fT=fT_target, C=C_load,
        objective="area", gain_min=gain_min_demo, quasi_static_margin=0.1)
    n_feasible = sum(1 for c in cands if c["feasible"])
    print(f"{len(cands)}개 후보 평가, {n_feasible}개 실행가능(gain>={gain_min_demo}, 준정적 만족)")
    for label, best in [("전력 최소", best_power), ("면적 최소", best_area)]:
        if best:
            print(f"  {label}: L={best['L']*1e6:.2f}um VDS={best['VDS']:.2f}V gm/ID={best['gm_id']:.1f} "
                  f"ID={best['ID']*1e6:.2f}uA W={best['W']*1e6:.3f}um gain={best['gain']:.1f}")
        else:
            print(f"  {label}: 실행가능점 없음")

    print()
    print("# topology JSON 오케스트레이션 레이어 데모 (2026-07-28 신설) — "
          "load_sizing_targets()/write_sizing_results()/run_sizing_pipeline()")
    import os as _os
    import tempfile as _tempfile

    _lib_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "library")

    print("  [compensation=null인 folded_cascode: design_spec을 그대로 반환하는지]")
    _fc_path = _os.path.join(_lib_dir, "folded_cascode.topology.json")
    _fc_spec = run_sizing_pipeline(_fc_path, {"fT": 100e6, "CL": 5e-12})
    print(f"    반환값(dict 그대로): {_fc_spec}")
    assert isinstance(_fc_spec, dict) and _fc_spec == {"fT": 100e6, "CL": 5e-12}

    print("  [compensation 있는 two_stage_ota: miller_ota_topology()의 topology_fn 반환하는지]")
    _ts_path = _os.path.join(_lib_dir, "two_stage_ota.topology.json")
    _ts_topology_fn = run_sizing_pipeline(_ts_path, {"GBW": 5e6, "CL": 5e-12})
    _gm1, _gm2 = _ts_topology_fn(None)
    print(f"    topology_fn(None) -> gm1={_gm1*1e3:.4f}mS, gm2={_gm2*1e3:.4f}mS "
          f"(gm2/gm1={_gm2/_gm1:.1f}, 기본 Z=10.0과 일치해야 함)")
    assert callable(_ts_topology_fn) and abs(_gm2 / _gm1 - 10.0) < 1e-9

    print("  [allowlist 밖 함수명은 안전하게 거부되는지]")
    with _tempfile.TemporaryDirectory() as _tmpdir:
        _bad_path = _os.path.join(_tmpdir, "bad.topology.json")
        with open(_bad_path, "w", encoding="utf-8") as _f:
            json.dump({"compensation": {"function": "not_a_real_function", "parameters": []}}, _f)
        try:
            run_sizing_pipeline(_bad_path, {})
            raise AssertionError("허용되지 않은 함수명이 거부되지 않았다")
        except ValueError as _e:
            print(f"    ValueError로 정상 거부됨: {_e}")

    print("  [write_sizing_results() -> load_sizing_targets() 왕복]")
    with _tempfile.TemporaryDirectory() as _tmpdir:
        _inst_path = _os.path.join(_tmpdir, "test.instance.json")
        write_sizing_results(_inst_path, {"M1": SizingResult(gm=1e-3, gm_id=15.0, ID=66.7e-6, W=50e-6)})
        _loaded = load_sizing_targets(_inst_path)
        print(f"    design_spec 키 없을 때 파일 전체 반환: {_loaded}")
        assert "sizing" in _loaded and _loaded["sizing"]["M1"]["gm"] == 1e-3

    print()
    print("  topology JSON 오케스트레이션 데모 PASS: null/함수참조 두 경로 + allowlist 거부 "
          "+ 왕복 전부 확인")

    print()
    print("# 배치 7-1(analog-topology-json-library.do.md) — optimize_multistage() 실제 실행 "
          "확보 (2026-07-31)")
    print("# 정의 이후 저장소 전체 호출 0건이었음(do.md 배치 7-1 문제 행) — run_regression_"
          "case()로 공정-무관하게 검증한다. sky130 숫자는 이 파일이 아니라 "
          "sky130_regression_reference.json에만 있다(2026-07-31 재설계 — 이 파일에 공정별")
    print("# 숫자를 직접 박으면 새 공정 LUT로는 이 self-test 자체가 항상 깨진다는 사용자 "
          "지적 반영).")

    _ref_json_path = _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)), "sky130_regression_reference.json")
    _verdict = run_regression_case(
        _ref_json_path, "nmcnr_3stage_GBW5M_CL10p_PM70_kg0.5")
    if _verdict.actual:
        print(f"  gms={[f'{g*1e3:.4f}mS' for g in _verdict.actual['gms']]}")
        for _i, _st in enumerate(_verdict.actual["stages"], 1):
            print(f"    stage{_i}: L={_st['L']*1e6:.3f}um VDS={_st['VDS']:.3f}V "
                  f"gm/ID={_st['gm_id']:.2f} W={_st['W']*1e6:.3f}um")
    assert _verdict.ok, _verdict.detail
    print(f"  [PASS] {_verdict.detail} -- optimize_multistage()가 real LUT로 처음부터 끝까지 "
          f"실제 실행됨(공정-무관 러너, 이 파일에 하드코딩된 공정별 숫자 없음)")

    print()
    print("# 배치 7-3 B/C/F 엔진(analog-topology-json-library.do.md §7.3.2, 2026-07-31) --")
    print("# LUT가 필요한 절반: solve_id_for_target_gm()/solve_diode_stack_current()/")
    print("# compute_metric()+_METRICS_REGISTRY. toy LUT(build_toy_lut(), W_ref=None)로 검증.")

    print()
    print("  [B엔진 solve_id_for_target_gm() -- 순방향으로 만든 gm_target을 역산해 gm_id 복원]")
    _b_L, _b_vds, _b_W, _b_gm_id_known = 0.5e-6, 0.6, 50e-6, 15.0
    _b_idu = lut.gm_id_to_id_density(_b_gm_id_known, _b_L, _b_vds, 0.0)
    _b_id_known = _b_idu * _b_W / _b_L
    _b_gm_known = _b_gm_id_known * _b_id_known
    # toy LUT의 gm/ID 유효범위가 ~[1.85,29.6]이라(build_toy_lut() VGS 스윕 범위) 기본
    # bounds(2~30)의 상단이 살짝 밖으로 나간다 -- 이 LUT에 맞는 범위를 명시로 좁혀서 호출.
    _b_result = solve_id_for_target_gm(lut, _b_L, _b_vds, 0.0, _b_W, _b_gm_known,
                                        gm_id_bounds=(2.0, 28.0))
    print(f"    순방향: gm_id={_b_gm_id_known}, ID={_b_id_known*1e6:.4f}uA, gm={_b_gm_known*1e3:.4f}mS")
    print(f"    역산:   gm_id={_b_result.gm_id:.4f}, ID={_b_result.ID*1e6:.4f}uA")
    assert abs(_b_result.gm_id - _b_gm_id_known) < 1e-3, "B엔진 gm_id 역산 오차 과다"
    assert abs(_b_result.ID - _b_id_known) / _b_id_known < 1e-3, "B엔진 ID 역산 오차 과다"
    print("    PASS: 순방향 gm_id를 오차 1e-3 이내로 복원")

    print()
    print("  [C엔진 solve_diode_stack_current() -- 순방향으로 만든 VGS합을 역산해 전류 복원]")
    _c_stack = [
        {"kind": "nmos", "L": 0.5e-6, "W": 20e-6, "vds": 0.6, "vs": 0.0},
        {"kind": "nmos", "L": 0.5e-6, "W": 10e-6, "vds": 0.6, "vs": 0.0},
    ]
    _c_i_known = 30e-6
    _c_vgs_target = 0.0
    for _dev in _c_stack:
        _gm_id = _invert_gm_id_for_current(lut, _c_i_known, _dev["L"], _dev["vds"], _dev["vs"], _dev["W"],
                                            gm_id_bounds=(2.0, 28.0))
        _c_vgs_target += lut.vgs_for_gm_id(_gm_id, _dev["L"], _dev["vds"], _dev["vs"])
    _c_i_solved = solve_diode_stack_current(lut, _c_stack, _c_vgs_target,
                                             i_bounds=(1e-9, 3e-4), gm_id_bounds=(2.0, 28.0))
    print(f"    순방향: I={_c_i_known*1e6:.4f}uA -> VGS합={_c_vgs_target:.6f}V")
    print(f"    역산:   VGS합={_c_vgs_target:.6f}V -> I={_c_i_solved*1e6:.4f}uA")
    assert abs(_c_i_solved - _c_i_known) / _c_i_known < 1e-3, "C엔진 전류 역산 오차 과다"
    print("    PASS: 순방향 전류를 오차 1e-3 이내로 복원")

    print()
    print("  [F엔진 compute_metric()/_METRICS_REGISTRY -- sum_current/sum_area/gain_stages_sum]")
    _f_ctx = SizingContext(sized={
        "M1": {"ID": 10e-6, "W": 20e-6, "L": 0.5e-6, "gm": 100e-6, "gds": 1e-6},
        "M2": {"ID": 20e-6, "W": 30e-6, "L": 0.5e-6, "gm": 150e-6, "gds": 2e-6},
    })
    _f_current = compute_metric({"type": "sum_current"}, _f_ctx)
    _f_area = compute_metric({"type": "sum_area"}, _f_ctx)
    _f_gain = compute_metric({"type": "gain_stages_sum", "stages": [["M1", "M2"]]}, _f_ctx)
    assert abs(_f_current - 30e-6) < 1e-12, "sum_current 오류"
    assert abs(_f_area - (20e-6 * 0.5e-6 + 30e-6 * 0.5e-6)) < 1e-18, "sum_area 오류"
    _f_gain_expected = 20 * math.log10((100e-6 + 150e-6) / (1e-6 + 2e-6))
    assert abs(_f_gain - _f_gain_expected) < 1e-9, "gain_stages_sum 오류"
    print(f"    sum_current={_f_current*1e6:.1f}uA, sum_area={_f_area*1e12:.1f}um^2, "
          f"gain_stages_sum={_f_gain:.2f}dB -- 전부 손계산과 일치")
    try:
        compute_metric({"type": "not_a_real_metric"}, _f_ctx)
        raise AssertionError("등록 안 된 metric 타입인데 에러가 안 났다")
    except ValueError as _e_metric:
        print(f"    PASS: 등록 안 된 metric 타입은 ValueError로 즉시 거부 -- {str(_e_metric)[:60]}...")

    print()
    print("# 배치 7-3b/e/f(analog-topology-json-library.do.md, 2026-07-31) --")
    print("# allocate_stack_headroom()/search_gm_id_for_role()/select_L_by_role()")

    print()
    print("  [7-3b allocate_stack_headroom() -- resize.py 6개 소자 스택, vdd=1.8V]")
    _hr_stack = [
        {"name": "M6", "role": "tail",     "min_vds": 0.30},
        {"name": "M1", "role": "input",    "min_vds": 0.40},
        {"name": "M2", "role": "cascode",  "min_vds": 0.20},
        {"name": "M3", "role": "cascode",  "min_vds": 0.20},
        {"name": "M4", "role": "input",    "min_vds": 0.40},
        {"name": "M5", "role": "tail",     "min_vds": 0.30},
    ]
    _hr_result = allocate_stack_headroom(1.8, _hr_stack)
    print(f"    기본 정책(gm_id 없음 -- min_vds 그대로): {_hr_result}")
    assert abs(_hr_result["M2"] - 0.20) < 1e-12 and abs(_hr_result["M3"] - 0.20) < 1e-12, \
        "cascode에 min_vds가 그대로 안 쓰임"
    assert abs(sum(_hr_result.values()) - 1.8) < 1e-9, "배정 합이 vdd(1.8V)와 불일치"
    print(f"    PASS: 합={sum(_hr_result.values()):.4f}V == vdd, cascode(M2/M3)는 min_vds 그대로")

    print("  [gm_id가 있으면 2/gm_id+margin으로 캐스코드 헤드룸이 자동 연동되는지(§7-3e (b))]")
    _hr_stack2 = [dict(e) for e in _hr_stack]
    for _e in _hr_stack2:
        if _e["role"] == "cascode":
            _e["gm_id"] = 17.0  # sky130 실측 min-L NMOS 정점 부근값(참고용 예시)
    _hr_result2 = allocate_stack_headroom(1.8, _hr_stack2)
    _expected_cascode_v = 2.0 / 17.0 + 0.05
    assert abs(_hr_result2["M2"] - _expected_cascode_v) < 1e-9, "gm_id 연동 헤드룸 계산 오류"
    assert abs(sum(_hr_result2.values()) - 1.8) < 1e-9, "gm_id 연동 시에도 합이 vdd와 불일치"
    print(f"    PASS: gm_id=17 -> cascode VDS={_expected_cascode_v:.4f}V(=2/17+0.05), 합 여전히 vdd와 일치")

    print()
    print("  [7-3e search_gm_id_for_role() -- role별 선택 방향(matching=최소, gain=gm/gds 최대, "
          "balanced=첫 feasible)]")
    _role_L, _role_vds, _role_id_target = 0.5e-6, 0.6, 40e-6
    _gm_id_matching = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                             role="matching", W_bounds=(1e-6, 200e-6))
    _gm_id_gain = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                         role="gain", W_bounds=(1e-6, 200e-6))
    _gm_id_balanced = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                             role="balanced", W_bounds=(1e-6, 200e-6))
    print(f"    matching(strong 극단) gm_id={_gm_id_matching:.2f}, "
          f"gain(gm/gds 최대) gm_id={_gm_id_gain:.2f}, balanced(첫 feasible) gm_id={_gm_id_balanced:.2f}")
    def _feasible_w(g):
        try:
            return _role_id_target * _role_L / lut.gm_id_to_id_density(g, _role_L, _role_vds, 0.0)
        except ValueError:
            return None
    _feasible_check = [g for g in [i * 0.5 for i in range(4, 61)]
                        if (lambda w: w is not None and 1e-6 <= w <= 200e-6)(_feasible_w(g))]
    assert _gm_id_matching == min(_feasible_check), "matching이 feasible 중 최소 gm_id가 아님"
    assert _gm_id_balanced == min(_feasible_check), "balanced가 첫 feasible(오름차순 최소)이 아님"
    _best_ratio_direct = max(lut.gm_gds_ratio(g, _role_L, _role_vds, 0.0) for g in _feasible_check)
    assert abs(lut.gm_gds_ratio(_gm_id_gain, _role_L, _role_vds, 0.0) - _best_ratio_direct) < 1e-9, \
        "gain role이 실제 gm/gds 최댓값을 못 고름"
    print("    PASS: matching=최소gm_id, gain=gm/gds 실측 최댓값과 일치, balanced=오름차순 첫 feasible")

    print("  [W_bounds 안에 후보가 하나도 없으면 즉시 ValueError]")
    try:
        search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                               role="matching", W_bounds=(1e-9, 1e-9))
        raise AssertionError("불가능한 W_bounds인데 에러가 안 났다")
    except ValueError as _e_role:
        print(f"    PASS: ValueError -- {str(_e_role)[:70]}...")

    print()
    print("  [7-3f select_L_by_role() -- mirror/bias_replica는 배수, cascode/signal은 ValueError]")
    _L_min_demo = 0.15e-6
    _L_mirror = select_L_by_role("mirror", _L_min_demo)
    _L_bias = select_L_by_role("bias_replica", _L_min_demo)
    assert abs(_L_mirror - 2.5 * _L_min_demo) < 1e-15
    assert abs(_L_bias - 1.2 * _L_min_demo) < 1e-15
    print(f"    mirror: L={_L_mirror*1e6:.3f}um(={_L_min_demo*1e6:.2f}um*2.5), "
          f"bias_replica: L={_L_bias*1e6:.3f}um(={_L_min_demo*1e6:.2f}um*1.2)")
    for _bad_role in ("cascode", "signal"):
        try:
            select_L_by_role(_bad_role, _L_min_demo)
            raise AssertionError(f"role={_bad_role}인데 에러가 안 났다")
        except ValueError as _e_L:
            print(f"    PASS: role={_bad_role!r} -> ValueError -- {str(_e_L)[:60]}...")

    print()
    print("  [7-4b 확장 estimate_area_budget() -- 콜드스타트 블렌딩 vs 실측 자기참조]")
    _n_fingers_demo = 100
    _area_cold = estimate_area_budget("cascode", "unseen_role", area_priors={}, n_fingers=_n_fingers_demo)
    _a1d_demo = _n_fingers_demo * 1.0
    _a2d_cold_expected = _a1d_demo / 0.65
    _area_cold_expected = (1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected
    assert abs(_area_cold - _area_cold_expected) < 1e-9, "콜드스타트 블렌딩 공식 불일치"
    print(f"    표본 0개(콜드스타트, alpha=0.65): A_1D={_a1d_demo:.1f} -> 추정={_area_cold:.2f} "
          f"(블렌딩 공식과 일치)")

    _area_priors_real = {"cascode": {"n_samples": 1, "packing_density_mean": 0.731,
                                       "packing_density_var": 0.0}}
    _area_real = estimate_area_budget("cascode", "cascode", _area_priors_real, _n_fingers_demo)
    _area_real_expected = _a1d_demo / 0.731
    assert abs(_area_real - _area_real_expected) < 1e-9
    print(f"    표본 1개(실측 packing_density=0.731): 추정={_area_real:.2f} == A_1D/0.731 "
          f"(자기참조 sanity check -- 그 표본을 만든 실제 면적과 정확히 일치)")

    print()
    print("# 배치 7-3d(analog-topology-json-library.do.md §7.3.2 D, 2026-07-31) --")
    print("# _THETA_FEED_REGISTRY 5개 핸들러 + optimize_full_circuit_budget() 그리드서치 골격")

    print()
    print("  [feed 'A' (_feed_root_ratio) -- theta*reference 전류합을 root의 seed로]")
    _ctx_a = SizingContext(sized={"Mref": {"ID": 10e-6}})
    apply_theta_feed({"type": "A", "tag": "biasgen_root", "root": "Mtarget", "reference": ["Mref"]},
                      0.5, _ctx_a)
    assert abs(_ctx_a.seed_currents["Mtarget"] - 5e-6) < 1e-15
    print(f"    PASS: Mref=10uA, theta=0.5 -> seed_currents[Mtarget]={_ctx_a.seed_currents['Mtarget']*1e6:.2f}uA")

    print("  [feed 'C' (_feed_diode_stack_target) -- theta*reference W를 target W로]")
    _ctx_c = SizingContext(sized={"Mref": {"W": 40e-6}})
    apply_theta_feed({"type": "C", "target": "Mrepl", "reference": "Mref"}, 0.1, _ctx_c)
    assert abs(_ctx_c.sized["Mrepl"]["W"] - 4e-6) < 1e-15
    print(f"    PASS: Mref W=40um, K=0.1 -> Mrepl W={_ctx_c.sized['Mrepl']['W']*1e6:.2f}um")

    print("  [feed 'B' (_feed_gm_target_convention) -- N*omega_c*C_cmfb를 gm_target으로 사이징]")
    _ctx_b = SizingContext(spec={"lut": lut, "omega_c": 2 * math.pi * 1e6, "C_cmfb": 2e-12})
    apply_theta_feed({"type": "B", "tag": "servo", "target": "Mcmfb", "omega_key": "omega_c",
                       "cap_key": "C_cmfb", "L": 0.5e-6, "W": 30e-6, "vds": 0.6,
                       "gm_id_bounds": [2.0, 28.0]}, 3.0, _ctx_b)
    _gm_target_expected = 3.0 * 2 * math.pi * 1e6 * 2e-12
    assert abs(_ctx_b.sized["Mcmfb"]["gm"] - _gm_target_expected) / _gm_target_expected < 1e-3
    print(f"    PASS: N=3 -> gm_target={_gm_target_expected*1e6:.4f}uS, "
          f"사이징 결과 gm={_ctx_b.sized['Mcmfb']['gm']*1e6:.4f}uS (오차 1e-3 이내 일치)")

    print("  [feed 'settling_split' (_feed_settling_split) -- theta*total을 derived로]")
    _ctx_s = SizingContext(spec={"t_settle_total": 40e-9})
    apply_theta_feed("settling_split", 0.25, _ctx_s)
    assert abs(_ctx_s.derived["t_slew"] - 10e-9) < 1e-18
    print(f"    PASS: t_settle_total=40ns, f_slew=0.25 -> derived[t_slew]={_ctx_s.derived['t_slew']*1e9:.2f}ns")

    print("  [feed 'metric_stage_budget' -- theta(L)로 지정 devices의 L/W/gm/gds 재계산]")
    _ctx_m = SizingContext(spec={"lut": lut}, sized={"M1": {"ID": 10e-6}, "M2": {"ID": 20e-6}})
    apply_theta_feed({"type": "metric_stage_budget", "metric": "gain_db", "devices": ["M1", "M2"],
                       "gm_id": 15.0, "vds": 0.6}, 0.5e-6, _ctx_m)
    assert _ctx_m.sized["M1"]["L"] == 0.5e-6 and _ctx_m.sized["M2"]["L"] == 0.5e-6
    _gain_check = compute_metric({"type": "gain_stages_sum", "stages": [["M1", "M2"]]}, _ctx_m)
    print(f"    PASS: L={_ctx_m.sized['M1']['L']*1e6}um 배정, gain_stages_sum={_gain_check:.2f}dB 계산 가능")

    print("  [등록 안 된 feed 타입은 즉시 ValueError]")
    try:
        apply_theta_feed({"type": "not_a_real_feed"}, 1.0, SizingContext())
        raise AssertionError("등록 안 된 feed 타입인데 에러가 안 났다")
    except ValueError as _e_feed:
        print(f"    PASS: ValueError -- {str(_e_feed)[:60]}...")

    print()
    print("  [optimize_full_circuit_budget() -- sizing_roles 없는 회로(folded_cascode)는 "
          "즉시 빈 결과로 통과]")
    _lib_dir_recipe = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "library")
    _ofc_result = optimize_full_circuit_budget(
        _os.path.join(_lib_dir_recipe, "folded_cascode.topology.json"), {"lut": lut})
    assert _ofc_result["theta_star"] == {} and _ofc_result["metrics"] == {}, \
        "sizing_roles 없는데 빈 결과가 아님"
    assert _ofc_result["sizing_overrides"] is None and _ofc_result["pipeline_result"] is None, \
        "device_roles/compensation 없이 넷리스트 전체가 사이징될 리 없는데 전체 파이프라인이 실행됨"
    print(f"    PASS: theta*={_ofc_result['theta_star']}, metrics={_ofc_result['metrics']} "
          f"(즉시 1회 평가, 넷리스트 미완성이라 전체 파이프라인은 건너뜀 -- 하위호환)")

    print()
    print("  [optimize_full_circuit_budget() -- 합성 sizing_roles로 그리드서치가 실제 최적값을 "
          "찾는지 전수비교]")
    _ofc_topo = {
        "schema_version": "2.0", "topology_name": "_test_only", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [{"name": "Mtest", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "vb"}],
        "symmetry": {"matching_pairs": [], "dispositions": []},
        "sizing_roles": {
            "theta": [{"name": "N", "bounds": [1.0, 5.0],
                       "feeds": {"type": "B", "tag": "servo", "target": "Mtest",
                                 "omega_key": "omega_c", "cap_key": "cap", "L": 0.5e-6, "W": 30e-6,
                                 "vds": 0.6, "gm_id_bounds": [2.0, 28.0]}}],
            "metrics": {"power_uA": {"type": "sum_current"}},
            "objective": {"minimize": "power_uA"},
            "constraints": [{"metric": "power_uA", "op": "<=", "value": 1e-3}],
        },
    }
    with _tempfile.TemporaryDirectory() as _ofc_tmpdir:
        _ofc_topo_path = _os.path.join(_ofc_tmpdir, "_test_only.topology.json")
        with open(_ofc_topo_path, "w", encoding="utf-8") as _f:
            json.dump(_ofc_topo, _f)
        _ofc_spec = {"lut": lut, "omega_c": 2 * math.pi * 1e6, "cap": 2e-12}
        _ofc_full = optimize_full_circuit_budget(_ofc_topo_path, _ofc_spec, grid_points_per_theta=5)
        _theta_star, _sizing, _metrics = _ofc_full["theta_star"], _ofc_full["sizing"], _ofc_full["metrics"]
        assert _ofc_full["pipeline_result"] is not None, \
            "Mtest는 W까지 다 있는데 전체 파이프라인(assign_finger_geometry/run_topology_pipeline)이 안 돎"
        assert _ofc_full["audit_ok"], f"단일 소자 넷리스트인데 audit이 FAIL: {_ofc_full['pipeline_result']}"

        # 전수비교: 같은 격자를 직접 순회해 손으로 찾은 최적값과 정확히 일치하는지 확인.
        _manual_best = None
        for _i in range(5):
            _N = _lerp(1.0, 5.0, _i / 4)
            _ctx_manual = SizingContext(spec=_ofc_spec)
            apply_theta_feed(_ofc_topo["sizing_roles"]["theta"][0]["feeds"], _N, _ctx_manual)
            _a_ids = propagate_topology_forced_currents(
                [Transistor("Mtest", "nmos", source="gnd", drain="out", gate="vb")],
                _ctx_manual.seed_currents, _ctx_manual.mirror_ratios)
            for _name, _idv in _a_ids.items():
                _ctx_manual.sized.setdefault(_name, {})["ID"] = _idv
            _power = compute_metric({"type": "sum_current"}, _ctx_manual)
            if _power <= 1e-3 and (_manual_best is None or _power < _manual_best[0]):
                _manual_best = (_power, _N)
        assert _manual_best is not None, "전수비교 자체가 infeasible -- 테스트 설계 오류"
        assert abs(_metrics["power_uA"] - _manual_best[0]) < 1e-12, \
            f"함수 결과({_metrics['power_uA']})가 전수비교 최적값({_manual_best[0]})과 다름"
        assert abs(_theta_star["N"] - _manual_best[1]) < 1e-9, \
            f"theta*(N={_theta_star['N']})가 전수비교 최적 N({_manual_best[1]})과 다름"
        print(f"    PASS: theta*=N={_theta_star['N']:.3f}, power_uA={_metrics['power_uA']*1e6:.4f}uA "
              f"-- {5}개 격자점 전수비교와 정확히 일치(재현성+최적성 확인)")

    print()
    print("  [제약을 만족하는 격자점이 하나도 없으면 즉시 ValueError]")
    _ofc_topo_infeasible = dict(_ofc_topo)
    _ofc_topo_infeasible["sizing_roles"] = dict(_ofc_topo["sizing_roles"])
    _ofc_topo_infeasible["sizing_roles"]["constraints"] = [
        {"metric": "power_uA", "op": "<=", "value": 1e-15}]  # 불가능한 제약
    with _tempfile.TemporaryDirectory() as _ofc_tmpdir2:
        _ofc_topo_path2 = _os.path.join(_ofc_tmpdir2, "_test_infeasible.topology.json")
        with open(_ofc_topo_path2, "w", encoding="utf-8") as _f:
            json.dump(_ofc_topo_infeasible, _f)
        try:
            optimize_full_circuit_budget(_ofc_topo_path2, _ofc_spec, grid_points_per_theta=5)
            raise AssertionError("불가능한 제약인데 에러가 안 났다")
        except ValueError as _e_ofc:
            print(f"    PASS: ValueError -- {str(_e_ofc)[:60]}...")

    print()
    print("  [optimize_full_circuit_budget() -- 실제 회로(two_stage_ota, 7개 소자) 전체를")
    print("  spec만 넣고 AI 개입 없이 instance-ready 결과까지 끝까지 실행(배치 7-5 1차 실증,")
    print("  2026-07-31) -- device_roles/compensation.stage_devices는 topology.json에 이미")
    print("  선언돼 있고(이번에 추가), 이 함수는 그 선언만 읽어 조립한다]")
    _tso_path = _os.path.join(_lib_dir_recipe, "two_stage_ota.topology.json")
    _tso_spec = {
        "lut_by_kind": {"nmos": lut, "pmos": lut},
        "vdd": 2.0,
        "GBW": 20e6, "CL": 3e-12, "Z": 10.0, "NDP": 4.0,
        "L_candidates": [float(v) for v in lut.L_grid],
        "VDS_candidates": [float(v) for v in lut.VDS_grid],
        "gm_id_grid": [i * 0.5 for i in range(4, 58)],
        "L_min": 0.18e-6,
        "W_bounds": (1e-6, 200e-6),
        "stage_w_max": 200e-6,
        "min_vds_by_role": {"cascode": 0.2, "tail": 0.2},
        "min_finger_w": 0.1e-6, "max_finger_w": 40e-6,
        # derive_stack_groups()의 자동 병합은 {M1,M2,M3,M4}를 한 그룹으로 묶는데(D3/O1
        # 2단자 내부노드 + matching_pairs), 입력쌍(M1/M2)과 부하 미러(M3/M4)는 전류는 같아도
        # W가 서로 달라 finger_w 비율-호환이 안 될 수 있다 -- 물리적으로 더 타당한(입력쌍과
        # 부하를 별도 행으로 두는) 분할을 선언으로 override(§ stack_groups_override 참고).
        # [교훈, 2026-07-31] stack_groups_geometry(레이아웃 행 그룹핑)는 KCL 직렬연결이 아니라
        # symmetry.matching_pairs 선언을 따라야 한다 -- 처음엔 M6/M7이 같은 KCL 스택(전류가
        # 같음)이라는 이유로 묶었다가, 실제 matching pair는 M5/M7(current_mirror)이고 M6은
        # 짝이 없는 단독 소자라는 걸 놓쳐 box-shape 감사가 실패했다(M5/M7이 서로 다른 행에
        # 있어 repair가 나중에 억지로 합치며 각자 독립 배정된 finger 수가 그대로 더해져 폭이
        # 2배로 부풀었음). matching_pairs 그대로 묶으니(M5+M7 한 그룹, M6 단독) 알고리즘
        # 변경 없이 바로 box-shape 비율 1.20으로 통과.
        "stack_groups_override": {"M1": ["M1", "M2"], "M3": ["M3", "M4"],
                                    "M5": ["M5", "M7"], "M6": ["M6"]},
    }
    _tso_result = optimize_full_circuit_budget(_tso_path, _tso_spec)
    _tso_all_names = {"M1", "M2", "M3", "M4", "M5", "M6", "M7"}
    assert set(_tso_result["sizing"].keys()) == _tso_all_names, \
        f"7개 소자 전부 사이징돼야 하는데: {sorted(_tso_result['sizing'].keys())}"
    assert all("W" in _tso_result["sizing"][n] for n in _tso_all_names), "일부 소자에 W가 없음"
    assert _tso_result["pipeline_result"] is not None, "넷리스트 전체가 사이징됐는데 전체 파이프라인이 안 돎"
    print(f"    사이징 결과: " + ", ".join(
        f"{n}(gm_id={_tso_result['sizing'][n]['gm_id']:.2f},W={_tso_result['sizing'][n]['W']*1e6:.2f}um)"
        for n in ["M1", "M3", "M5", "M6", "M7"]))
    print(f"    box_shape.ok={_tso_result['pipeline_result']['box_shape'].ok}, "
          f"coverage.ok={_tso_result['pipeline_result']['coverage'].ok}, audit_ok={_tso_result['audit_ok']}")
    assert _tso_result["pipeline_result"]["coverage"].ok, "7개 소자 중 일부가 stick diagram에서 빠짐"
    assert _tso_result["audit_ok"], (
        "matching-safety audit이 repair_matching_safety()로도 끝내 FAIL -- "
        f"{_tso_result['pipeline_result'].get('repaired_audit')}")
    print("    PASS: spec -> load_topology -> derive_stack_groups -> A엔진 -> compensation "
          "-> device_roles(L/헤드룸/gm_id) -> assign_finger_geometry -> run_topology_pipeline "
          "-> audit(+repair 필요시)까지 AI 개입 없이 단일 함수 호출로 완주")

    print()
    print("  [matching_pairs L 강제 일치 -- compensation(spec 기반) vs device_roles.L_role"
          "(휴리스틱)이 독립적으로 다른 L을 정했을 때 에러로 끝내지 않고 spec 기반 쪽으로"
          " 재설계되는지 확인]")
    _lrec_topo = {
        "schema_version": "2.0", "topology_name": "_test_L_reconcile", "source": "self-test",
        "linked_topology_files": [], "_compensation_status": "resolved",
        "netlist": [{"name": "Ma", "kind": "nmos", "source": "gnd", "drain": "d1", "gate": "g1"},
                     {"name": "Mc", "kind": "nmos", "source": "gnd", "drain": "d2", "gate": "g2"},
                     {"name": "Mb", "kind": "nmos", "source": "gnd", "drain": "d3", "gate": "g3"}],
        "symmetry": {"matching_pairs": [{"names": ["Ma", "Mb"], "kind": "current_mirror"}],
                      "dispositions": []},
        "compensation": {"function": "miller_ota_topology",
                          "parameters": ["GBW", "CL", "Z", "NDP"],
                          "stage_devices": [["Ma"], ["Mc"]]},
        "device_roles": {"Mb": {"headroom_role": None, "gm_id_role": None,
                                  "L_role": "mirror", "vertical_stack_id": None, "vs": 0.0}},
    }
    with _tempfile.TemporaryDirectory() as _lrec_tmpdir:
        _lrec_path = _os.path.join(_lrec_tmpdir, "_test_L_reconcile.topology.json")
        with open(_lrec_path, "w", encoding="utf-8") as _f:
            json.dump(_lrec_topo, _f)
        _lrec_spec = {
            "lut_by_kind": {"nmos": lut}, "GBW": 20e6, "CL": 3e-12, "Z": 10.0, "NDP": 4.0,
            "L_candidates": [float(v) for v in lut.L_grid],
            "VDS_candidates": [float(v) for v in lut.VDS_grid],
            "gm_id_grid": [i * 0.5 for i in range(4, 58)],
            "stage_w_max": 200e-6,
            # Mb의 L_role="mirror"이 낼 L(=L_min_by_kind*2.5)이 compensation이 Ma에 고른 L과
            # 반드시 달라지도록 L_min_by_kind를 일부러 compensation 후보와 안 맞는 값으로 지정.
            "L_min_by_kind": {"nmos": 0.35e-6},
        }
        _lrec_result = optimize_full_circuit_budget(_lrec_path, _lrec_spec)
        _La_final = _lrec_result["sizing"]["Ma"]["L"]
        _Lb_final = _lrec_result["sizing"]["Mb"]["L"]
        _Lb_heuristic = 0.35e-6 * 2.5  # select_L_by_role("mirror", 0.35e-6)이 원래 냈을 값
        assert abs(_La_final - _Lb_final) < 1e-15, \
            f"matching pair L이 여전히 다름(에러 없이 통과했는데 재설계가 안 됨): Ma={_La_final}, Mb={_Lb_final}"
        assert abs(_Lb_heuristic - _La_final) > 1e-15, \
            "테스트 설계 오류 -- L_role 휴리스틱값과 compensation값이 우연히 같아서 재설계 여부를 구분 못 함"
        print(f"    PASS: compensation이 Ma에 고른 L={_La_final*1e6:.3f}um -- Mb의 L_role 휴리스틱"
              f"(단독이면 {_Lb_heuristic*1e6:.3f}um)을 덮어쓰고 그 값으로 재설계됨(ValueError 없이)")

    print("  [matching_pairs L 강제 일치 -- 양쪽 다 L_role(휴리스틱)인데 값이 다르면(스펙 근거로"
          " 우선순위를 가릴 수 없음) 즉시 ValueError]")
    _lrec_topo2 = dict(_lrec_topo)
    _lrec_topo2["netlist"] = [{"name": "Md", "kind": "nmos", "source": "gnd", "drain": "d4", "gate": "g4"},
                                {"name": "Me", "kind": "pmos", "source": "vdd", "drain": "d5", "gate": "g5"}]
    _lrec_topo2["symmetry"] = {"matching_pairs": [{"names": ["Md", "Me"], "kind": "current_mirror"}],
                                 "dispositions": []}
    _lrec_topo2["compensation"] = None
    _lrec_topo2["device_roles"] = {
        "Md": {"headroom_role": None, "gm_id_role": None, "L_role": "mirror",
                "vertical_stack_id": None, "vs": 0.0},
        "Me": {"headroom_role": None, "gm_id_role": None, "L_role": "bias_replica",
                "vertical_stack_id": None, "vs": 0.0}}
    with _tempfile.TemporaryDirectory() as _lrec_tmpdir2:
        _lrec_path2 = _os.path.join(_lrec_tmpdir2, "_test_L_reconcile2.topology.json")
        with open(_lrec_path2, "w", encoding="utf-8") as _f:
            json.dump(_lrec_topo2, _f)
        _lrec_spec2 = {"lut_by_kind": {"nmos": lut, "pmos": lut},
                        "L_min_by_kind": {"nmos": 0.35e-6, "pmos": 0.35e-6}}
        try:
            optimize_full_circuit_budget(_lrec_path2, _lrec_spec2)
            raise AssertionError("양쪽 다 휴리스틱인데 L이 다른데도 에러가 안 났다")
        except ValueError as _e_lrec:
            print(f"    PASS: ValueError -- {str(_e_lrec)[:70]}...")

    print()
    print("  [재현성: 같은 spec으로 다시 호출하면 완전히 같은 sizing]")
    _tso_result2 = optimize_full_circuit_budget(_tso_path, _tso_spec)
    for _n in _tso_all_names:
        assert _tso_result["sizing"][_n]["W"] == _tso_result2["sizing"][_n]["W"], \
            f"{_n}: 재실행 결과가 다름 -- 재현성 위반"
    print("    PASS: 재실행 결과 완전 동일(W 전부 bit-identical)")

    print()
    print("# 배치 7-3g/h/i(analog-topology-json-library.do.md, 2026-07-31) --")
    print("# noise_1f_density()/estimate_mismatch_sigma() + 4개 신규 metric")

    print()
    print("  [7-3g noise_1f_density() -- SID_1F 없는 LUT는 즉시 ValueError(데이터 없음을 숨기지 않음)]")
    try:
        lut.noise_1f_density(15.0, 0.5e-6, 0.6, 0.0, 30e-6)
        raise AssertionError("SID_1F 없는데 에러가 안 났다")
    except ValueError as _e_1f:
        print(f"    PASS: ValueError -- {str(_e_1f)[:70]}...")

    print("  [SID_1F 있는 합성 LUT -- W_ref/W_target 스케일링 + 1/freq 반영 확인]")
    _lut_np = lut.np
    _sid1f_at_wref = 4e-16  # 임의 상수(V^2/Hz @ 1Hz, W_ref 기준) -- 격자 전체 동일값으로 합성
    _sid1f_array = _lut_np.full(lut.ID.shape, _sid1f_at_wref)
    _lut_with_noise = SemiEmpiricalGmIdLUT(lut.L_grid, lut.VGS_grid, lut.VDS_grid, lut.VS_grid,
                                            lut.ID, lut.GM, lut.GDS, lut.CGG, W_ref=lut.W_ref,
                                            SID_1F=_sid1f_array)
    _w_ref_eff = lut._w_ref_effective(0.5e-6)
    _w_target_test = 20e-6
    _freq_test = 10.0
    _sid1f_result = _lut_with_noise.noise_1f_density(15.0, 0.5e-6, 0.6, 0.0, _w_target_test, _freq_test)
    _sid1f_expected = _sid1f_at_wref * _w_ref_eff / _w_target_test / _freq_test
    assert abs(_sid1f_result - _sid1f_expected) / _sid1f_expected < 1e-9
    print(f"    PASS: SID_1F(1Hz,W_ref)={_sid1f_at_wref:.2e} -> W_target={_w_target_test*1e6}um, "
          f"freq={_freq_test}Hz에서 {_sid1f_result:.3e}V^2/Hz(손계산과 일치)")

    print("  [_metric_flicker_plus_thermal_sum() -- 열+1/f 합산이 손계산과 일치]")
    _ctx_noise = SizingContext(
        spec={"lut": _lut_with_noise, "freq": _freq_test, "temperature_K": 300.0},
        sized={"M1": {"gm": 200e-6, "gm_id": 15.0, "L": 0.5e-6, "W": _w_target_test,
                       "vds": 0.6, "vs": 0.0}})
    _noise_result = compute_metric({"type": "flicker_plus_thermal_sum", "stages": [["M1"]]}, _ctx_noise)
    _kT = 1.380649e-23 * 300.0
    _s_th_expected = 4 * _kT * (2.0 / 3.0) / 200e-6
    _noise_expected = math.sqrt(_s_th_expected + _sid1f_expected)
    assert abs(_noise_result - _noise_expected) / _noise_expected < 1e-9
    print(f"    PASS: sqrt(S_thermal+S_1f)={_noise_result:.3e}V/rtHz (손계산과 일치)")

    print()
    print("  [7-3h estimate_mismatch_sigma()/pelgrom_mismatch metric -- sky130 실측 vth0_slope로 확인]")
    _sigma_single = estimate_mismatch_sigma(3.356e-3, 20.0, 0.5)  # W=20um, L=0.5um (NFET)
    assert abs(_sigma_single - 3.356e-3 / math.sqrt(20.0 * 0.5)) < 1e-15
    print(f"    단일소자 sigma_Vth(W=20um,L=0.5um,vth0_slope=3.356e-3)={_sigma_single*1e3:.4f}mV")

    _ctx_mismatch = SizingContext(
        spec={"vth0_slope": {"nfet": 3.356e-3}},
        sized={"M1a": {"W": 20e-6, "L": 0.5e-6}, "M1b": {"W": 20e-6, "L": 0.5e-6}})
    _pair_sigma = compute_metric(
        {"type": "pelgrom_mismatch", "devices": ["M1a", "M1b"], "kind": "nfet"}, _ctx_mismatch)
    _pair_sigma_expected = math.sqrt(2) * _sigma_single * 1e3
    assert abs(_pair_sigma - _pair_sigma_expected) < 1e-9
    print(f"    PASS: pair sigma(M1a/M1b, 동일 W/L)={_pair_sigma:.4f}mV == sqrt(2)*단일소자 (RSS 합산 확인)")

    print()
    print("  [7-3i cmrr_estimate/psrr_estimate metric -- diff_pair_tail family 계산 확인]")
    _ctx_cmrr = SizingContext(sized={"M5": {"gm": 500e-6, "gds": 5e-6}})  # tail 소자
    _cmrr_db = compute_metric(
        {"type": "cmrr_estimate", "tail_device": "M5", "circuit_family": "diff_pair_tail"}, _ctx_cmrr)
    _ro_tail = 1.0 / 5e-6
    _cmrr_linear_expected = (_ro_tail / 2.0 + 1.0 / 500e-6) * 500e-6
    assert abs(_cmrr_db - 20 * math.log10(_cmrr_linear_expected)) < 1e-9
    _psrr_db = compute_metric(
        {"type": "psrr_estimate", "tail_device": "M5", "circuit_family": "diff_pair_tail"}, _ctx_cmrr)
    assert abs(_psrr_db - 20 * math.log10(500e-6 / 5e-6)) < 1e-9
    print(f"    PASS: CMRR={_cmrr_db:.2f}dB, PSRR={_psrr_db:.2f}dB(order-of-magnitude 근사, 손계산과 일치)")

    print("  [등록 안 된 circuit_family는 즉시 ValueError]")
    try:
        compute_metric({"type": "cmrr_estimate", "tail_device": "M5",
                         "circuit_family": "_not_registered_family"}, _ctx_cmrr)
        raise AssertionError("미등록 circuit_family인데 에러가 안 났다")
    except ValueError as _e_fam:
        print(f"    PASS: ValueError -- {str(_e_fam)[:70]}...")

    print()
    print("  [cmrr_estimate -- telescopic_class_ab family: metric_spec의 소자 역할 배정이")
    print("  current_reuse_telescopic_ota.topology.json의 실제 kind/connectivity와 일치하는지")
    print("  load_topology()로 먼저 확인 -- 논문 Fig.2를 읽고 손으로 배정한 것을 절대 그대로")
    print("  믿지 않는다(topology.json이 유일한 토폴로지 소스 원칙)]")
    _crt_topo_path = _os.path.join(_lib_dir_recipe, "current_reuse_telescopic_ota.topology.json")
    _crt_transistors, _ = load_topology(_crt_topo_path)
    _crt_by_name = {t.name: t for t in _crt_transistors}
    _crt_role_map = {"input_p": "M1a", "cascode_p": "M2a", "input_n": "M4a", "cascode_n": "M3a",
                      "tail_p_devices": ["M6", "M7"], "tail_n_device": "M5"}
    assert _crt_by_name["M1a"].kind == "pmos" and _crt_by_name["M2a"].kind == "pmos", \
        "input_p/cascode_p로 배정한 소자가 실제로는 pmos가 아님"
    assert _crt_by_name["M4a"].kind == "nmos" and _crt_by_name["M3a"].kind == "nmos", \
        "input_n/cascode_n으로 배정한 소자가 실제로는 nmos가 아님"
    assert all(_crt_by_name[d].kind == "pmos" for d in _crt_role_map["tail_p_devices"]), \
        "tail_p_devices가 실제로는 pmos가 아님"
    assert _crt_by_name["M5"].kind == "nmos", "tail_n_device가 실제로는 nmos가 아님"
    # 캐스코드 접합(M2a 드레인 == M3a 소스, 두 캐스코드가 정말 같은 노드를 공유하는지 -- 이게
    # 이 CMRR 공식의 핵심 위상 가정)과 tail 노드 공유(M6/M7 드레인 == M1a 소스, M4a 소스 ==
    # M5 드레인)를 실제 connectivity로 확인한다.
    assert _crt_by_name["M2a"].drain == _crt_by_name["M3a"].source, \
        "M2a/M3a가 같은 캐스코드 접합노드를 공유하지 않음 -- CMRR 공식의 위상 가정이 이 JSON과 안 맞음"
    assert _crt_by_name["M6"].drain == _crt_by_name["M7"].drain == _crt_by_name["M1a"].source, \
        "M6/M7/M1a가 같은 Vx(tail) 노드를 공유하지 않음"
    assert _crt_by_name["M4a"].source == _crt_by_name["M5"].drain, \
        "M4a/M5가 같은 Vy(tail) 노드를 공유하지 않음"
    print(f"    PASS: kind 일치(M1a/M2a/M6/M7=pmos, M3a/M4a/M5=nmos), 캐스코드 접합노드"
          f"({_crt_by_name['M2a'].drain!r}) 및 tail 노드(Vx={_crt_by_name['M1a'].source!r}, "
          f"Vy={_crt_by_name['M4a'].source!r}) 공유 확인 -- 실제 JSON connectivity로 검증됨")

    print()
    print("  [cmrr_estimate -- telescopic_class_ab family(2026-07-31 신규 유도) -- 이상화")
    print("  소신호 netlist(sky130 PDK, ngspice AC 해석) + sympy 노드해석 교차검증값과 대조.")
    print("  gm/gds 자체는 topology.json에 없는 사이징 결과물이라(하네스를 실행해야 나옴)")
    print("  여기선 SPICE 대조에 쓴 수치를 그대로 넣어 수식 자체만 검증한다 -- 소자 역할/kind는")
    print("  위에서 이미 실제 JSON으로 확인됨]")
    _crt_cmrr_ctx = SizingContext(sized={
        "M1a": {"gm": 119e-6, "gds": 1.0 / 600e3},   # PMOS 입력쌍
        "M2a": {"gm": 119e-6, "gds": 1.0 / 600e3},   # PMOS 캐스코드
        "M4a": {"gm": 119e-6, "gds": 1.0 / 250e3},   # NMOS 입력쌍
        "M3a": {"gm": 119e-6, "gds": 1.0 / 250e3},   # NMOS 캐스코드
        "M6": {"gm": 0.0, "gds": 0.5e-6}, "M7": {"gm": 0.0, "gds": 0.5e-6},  # PMOS tail(Rx=1e6)
        "M5": {"gm": 0.0, "gds": 1.0e-6},             # NMOS tail(Ry=1e6)
    })
    _crt_cmrr_spec = {"type": "cmrr_estimate", "circuit_family": "telescopic_class_ab",
                        "input_p": "M1a", "cascode_p": "M2a", "input_n": "M4a", "cascode_n": "M3a",
                        "tail_p_devices": ["M6", "M7"], "tail_n_device": "M5"}
    _crt_cmrr_db = compute_metric(_crt_cmrr_spec, _crt_cmrr_ctx)
    # SPICE(ngspice AC, sky130 무관 -- 이상화 gm/ro만 쓴 소신호 netlist) 실측 대조값(Rx=Ry=1e6): -0.00dB.
    assert abs(_crt_cmrr_db - 0.0) < 0.1, f"Rx=Ry=1e6 기준값(SPICE -0.00dB)과 어긋남: {_crt_cmrr_db}"
    print(f"    PASS(Rx=Ry=1e6): CMRR={_crt_cmrr_db:.3f}dB (SPICE 대조값 -0.00dB, 오차<0.1dB)")
    # 비대칭 Rx(=1e8)로 두 번째 대조점 확인(SPICE 실측 4.59dB, 근사식 4.56dB -- 0.2dB 이내 확인됨).
    _crt_cmrr_ctx.sized["M6"]["gds"] = 0.5e-8
    _crt_cmrr_ctx.sized["M7"]["gds"] = 0.5e-8
    _crt_cmrr_db2 = compute_metric(_crt_cmrr_spec, _crt_cmrr_ctx)
    assert abs(_crt_cmrr_db2 - 4.59) < 0.2, f"Rx=1e8 기준값(SPICE 4.59dB)과 어긋남: {_crt_cmrr_db2}"
    print(f"    PASS(Rx=1e8,Ry=1e6): CMRR={_crt_cmrr_db2:.3f}dB (SPICE 대조값 4.59dB, 오차<0.2dB)")

    print()
    print("# current_reuse_telescopic_topology() 등록 재확인(2026-07-31, 원문 Eq.2-6 재도출 후,")
    print("# gmp/gmn/gm2 3-stage로 재설계 -- stage_devices 계약을 안 바꾸고 '분배'를 topology_fn")
    print("# 자신이 하도록 함, 사용자와 함께 설계) -- 실제(toy) LUT로 optimize_multistage()")
    print("# 고정점 반복 실행.")
    print("# [!] 실측 발견(2026-07-31): gm2/Cgg2(2단)는 5회 안에 안정적으로 수렴하지만,")
    print("# gmp/gmn(1단, Cgg1_total 되먹임)은 이 toy LUT에서 3-주기 한계 순환(limit cycle)에")
    print("# 빠진다 -- find_optimal_sizing()의 objective=power 동점 처리가 Cgg1이 미세하게")
    print("# 바뀔 때마다 서로 다른 (L,VDS,gm_id) 격자점으로 튀는 현상(배치 7-1이 이미 발견한")
    print("# '동점은 격자 순서에 의존' 현상과 같은 근본원인). damping(under-relaxation)으로")
    print("# 막아보려 했으나 진동의 주기/진폭만 바뀔 뿐 근본적으로 없어지지 않음을 실측 확인 --")
    print("# 그래서 optimize_multistage()에 순환 감지+평균 fallback을 추가했다(이 함수 docstring")
    print("# 참고): max_iter를 다 쓰고도 1-스텝 수렴에 실패하면 최근 이력에서 반복 주기를 찾아")
    print("# 그 구간의 gm 평균으로 재sizing한 안정된 추정치를 cycle_detected=True로 반환한다.")
    assert "current_reuse_telescopic_topology" in _COMPENSATION_REGISTRY
    _crt_tf = _COMPENSATION_REGISTRY["current_reuse_telescopic_topology"](
        t_lln=30e-9, PM_target_deg=70.0, Cc=500e-15, Cf=500e-15, Cs=500e-15, C_Ltot=1e-12)
    _crt_result = optimize_multistage(
        _crt_tf, [lut, lut, lut], [float(v) for v in lut.L_grid], [float(v) for v in lut.VDS_grid],
        [i * 0.5 for i in range(4, 58)], objective="power", w_max=200e-6, max_iter=20)
    assert _crt_result is not None, "optimize_multistage()가 실행가능점을 못 찾음"
    assert abs(_crt_result["gms"][0] - _crt_result["gms"][1]) < 1e-9, "gmp != gmn(Eq.5 위반)"
    assert _crt_result["gms"][2] > 0 and _crt_result["cggs"][2] > 0, "gm2/Cgg2가 비정상"
    assert _crt_result["converged"] is False, "이 toy LUT는 원래 한계 순환에 빠져야 하는데 수렴함 -- 회귀 확인 필요"
    assert _crt_result["cycle_detected"] is True, "순환 감지 fallback이 발동하지 않음"
    assert _crt_result["cycle_period"] == 3, f"예상 밖 순환 주기: {_crt_result['cycle_period']}"
    _crt_cgg1_total = _crt_result["cggs"][0] + _crt_result["cggs"][1]
    _crt_beta_final = 500e-15 / (500e-15 + 500e-15 + _crt_cgg1_total)
    print(f"  gmp={_crt_result['gms'][0]*1e6:.2f}uS, gmn={_crt_result['gms'][1]*1e6:.2f}uS, "
          f"gm2={_crt_result['gms'][2]*1e3:.4f}mS, iters={_crt_result['iters']}, "
          f"cycle_period={_crt_result['cycle_period']}(순환 구간 gm 평균으로 안정된 추정치)")
    print(f"  Cgg1_total(M1a+M4a, 평균 gm 기준 재sizing)={_crt_cgg1_total*1e15:.2f}fF -> "
          f"beta={_crt_beta_final:.4f}(원문의 고정 근사 0.48과 다를 수 있음 -- 이 LUT의 실제 "
          f"소자 특성에서 나온 값)")
