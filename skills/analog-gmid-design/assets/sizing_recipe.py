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
    6. 검증(f_nqs, gain, slew-rate)          -> verify()

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
import math
from dataclasses import dataclass


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

def verify_quasi_static(fT: float, gm: float, Cgg: float, margin: float = 0.1) -> bool:
    """f_nqs = gm/(2*pi*Cgg); fT <= margin * f_nqs 이어야 준정적 가정이 성립."""
    f_nqs = gm / (2 * math.pi * Cgg)
    return fT <= margin * f_nqs


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

    def __init__(self, L_grid, VGS_grid, VDS_grid, VS_grid, ID, GM, GDS, CGG, W_ref=None):
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
        expected = (len(self.L_grid), len(self.VGS_grid), len(self.VDS_grid), len(self.VS_grid))
        if self.ID.shape != expected:
            raise ValueError(f"ID 배열 shape {self.ID.shape} != 격자 shape {expected}")

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
                        fT_dev = lut.fT(gm_id, L, VDS, vs)
                        fnqs_ok = fT <= quasi_static_margin * fT_dev
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
                         max_iter: int = 10, tol: float = 1e-3):
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

    반환: dict(gms=[gm_i,...], stages=[find_optimal_sizing 결과,...], cggs=[...], iters, converged)
          또는 어느 스테이지든 실행가능점을 못 찾으면 None.
    """
    def _per_stage(param, i):
        return param[i] if isinstance(param, (list, tuple)) else param

    n = len(luts)
    prev_cggs = None
    prev_gms = None
    result = None
    for it in range(max_iter):
        gms = topology_fn(prev_cggs)
        stages, cggs = [], []
        for i in range(n):
            best, _ = find_optimal_sizing(
                luts[i], L_candidates, VDS_candidates, gm_id_grid, gm=gms[i],
                objective=objective, gain_min=_per_stage(gain_min, i), w_max=_per_stage(w_max, i))
            if best is None:
                return None  # 이 gm 타깃을 실행가능하게 구현 못함 -> 스펙/격자 재검토 필요
            cggs.append(luts[i].cgg_absolute(best["gm_id"], best["L"], best["VDS"], 0.0, best["W"]))
            stages.append(best)
        converged = prev_gms is not None and all(
            abs(g - pg) < tol * pg for g, pg in zip(gms, prev_gms))
        result = dict(gms=gms, stages=stages, cggs=cggs, iters=it + 1, converged=converged)
        if converged:
            break
        prev_cggs, prev_gms = cggs, gms
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
            fnqs_ok = verify_quasi_static(fT_target, r.gm, lut.cgg_absolute(gm_id, L, vds, 0.0, r.W))
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
