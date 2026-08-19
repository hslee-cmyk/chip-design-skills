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
import re
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

    2026-08-11(세션29) -- 순수 스칼라(bisect + 파이썬 float) 구현으로 교체. 프로파일링
    실측(51소자 실회로 evaluate() 1회 ~7~8초 중 대부분)으로 병목이 이 함수였음을 확인했는데,
    호출 패턴이 거의 항상 M=1(`_query()`, 단일 좌표 조회) 또는 M~수십(`_gm_id_curve()`의 VGS
    격자 스윕)로 작아서, 이런 크기에서는 매 호출마다 새로 만드는 numpy 배열(`np.clip`/
    `np.searchsorted`/`np.where`/`np.zeros`/`np.ones`/`np.full` 등)의 **고정 오버헤드**가
    실제 보간 연산량보다 훨씬 크다는 게 원인이었다(실측: `_multilinear_interp` 39,138회
    호출에 10초 자체시간, M 크기와 거의 무관하게 호출당 ~0.26ms -- 원소 수 비례가 아니라
    호출 자체의 numpy 디스패치 비용이 지배적이었다는 뜻). 알고리즘/수치 결과는 옛 구현과
    동일하다(경계 클리핑·`searchsorted(side="right")-1`과 동치인 `bisect_right-1`·denom=0
    처리까지 전부 대응 확인, 차분 테스트로 검증됨) -- `values`(LUT 4D 배열)만 numpy 그대로
    쓰고 나머지는 순수 파이썬 스칼라 연산이다."""
    import bisect
    ndim = len(grids)
    # 2026-08-13(세션31, F 설계 1단계) -- 이미 plain list인 grid는 그대로 쓴다(재변환/재복사
    # 불필요 -- 이 함수는 grids를 읽기만 하고 절대 in-place mutate하지 않는다). 호출부
    # (`SemiEmpiricalGmIdLUT._query()`/`_gm_id_curve()`)가 `self._grids_list`(__init__에서
    # 한 번만 만든 캐시)를 넘기는 게 이제 기본 경로라, 매 호출마다 `list(g)` 얕은 복사를
    # 반복하던 낭비를 없앤다(감사 발견 -- session29가 `.tolist()` 자체를 이미 병목으로
    # 지목했으면서도 이 재변환/재복사는 남아있었다).
    grids = [g.tolist() if hasattr(g, "tolist") else g for g in grids]
    points_seq = points.tolist() if hasattr(points, "tolist") else points
    if points_seq and not hasattr(points_seq[0], "__len__"):
        points_seq = [points_seq]  # 1차원(단일 좌표, N개 스칼라)로 들어온 경우 (1,N)으로 승격

    result = []
    for point in points_seq:
        idx_lo, frac = [], []
        for d in range(ndim):
            g = grids[d]
            n = len(g)
            x = point[d]
            if x <= g[0]:
                i, f = 0, 0.0
            elif x >= g[-1]:
                i, f = n - 2, 1.0
            else:
                i = bisect.bisect_right(g, x) - 1
                if i < 0:
                    i = 0
                elif i > n - 2:
                    i = n - 2
                denom = g[i + 1] - g[i]
                f = (x - g[i]) / denom if denom != 0 else 0.0
            idx_lo.append(i)
            frac.append(f)
        total = 0.0
        for corner in range(2 ** ndim):
            weight = 1.0
            idx = []
            for d in range(ndim):
                bit = (corner >> d) & 1
                weight *= frac[d] if bit else (1 - frac[d])
                idx.append(idx_lo[d] + bit)
            if weight != 0.0:
                total += weight * float(values[tuple(idx)])
        result.append(total)
    import numpy as np
    return np.asarray(result)


def _multilinear_interp_point_multi(grids, arrays, point):
    """`_multilinear_interp()`와 동일한 다중선형보간을, **단일 좌표**에서 **여러 배열을
    한 번에** 계산한다(F 설계, 세션31 -- `find_optimal_sizing()`의 L×VDS×gm_id 핫루프에서
    `gm_id_to_id_density()`/`gm_gds_ratio()`/`cgg_absolute()`가 같은 (L,vgs,vds,vs) 지점에서
    각자 `_query()`를 불러 bisect 탐색(4축)을 3~4번 반복하던 것을 남은 최대 레버로 지목한
    성능감사 후속). 축별 `idx_lo`/`frac`(bisect 탐색, 원래 비용의 핵심)을 **한 번만** 계산해
    `arrays`의 배열 개수만큼 재사용한다 -- 각 배열에 대해 개별 `_multilinear_interp()`를
    호출한 것과 수치적으로 동일한 결과를 낸다(같은 가중치/인덱스로 배열만 바꿔 합산하므로).

    `grids`는 이미 plain list여야 한다(numpy 변환은 호출부 책임, `_multilinear_interp()`와
    같은 계약). `point`는 (ndim,) 스칼라 좌표 하나(리스트/튜플). 반환: `arrays`와 같은
    순서의 보간값 리스트."""
    import bisect
    ndim = len(grids)
    idx_lo, frac = [], []
    for d in range(ndim):
        g = grids[d]
        n = len(g)
        x = point[d]
        if x <= g[0]:
            i, f = 0, 0.0
        elif x >= g[-1]:
            i, f = n - 2, 1.0
        else:
            i = bisect.bisect_right(g, x) - 1
            if i < 0:
                i = 0
            elif i > n - 2:
                i = n - 2
            denom = g[i + 1] - g[i]
            f = (x - g[i]) / denom if denom != 0 else 0.0
        idx_lo.append(i)
        frac.append(f)
    totals = [0.0] * len(arrays)
    for corner in range(2 ** ndim):
        weight = 1.0
        idx = []
        for d in range(ndim):
            bit = (corner >> d) & 1
            weight *= frac[d] if bit else (1 - frac[d])
            idx.append(idx_lo[d] + bit)
        if weight != 0.0:
            idx_t = tuple(idx)
            for ai, arr in enumerate(arrays):
                totals[ai] += weight * float(arr[idx_t])
    return totals


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
        # 2026-08-11(세션29) -- _gm_id_curve()가 매번 np.log(np.clip(self.ID,...))를 4D
        # 배열 전체에 다시 돌리고 있었다(호출당 1회, evaluate() 1회당 수천 번) -- self.ID는
        # 생성자 이후 불변이므로 여기서 한 번만 계산해 캐싱한다(프로파일링으로 발견한 중복,
        # _multilinear_interp() 자체 최적화와 별개).
        self._log_ID = np.log(np.clip(self.ID, 1e-18, None))
        # 2026-08-11(세션29) -- _gm_id_curve(L,vds,vs)는 순수함수인데 search_gm_id_for_role()
        # 이 gm_id_grid(기본 57점)를 스윕하는 동안 L/vds/vs는 그대로 두고 gm_id만 바꾼다 --
        # 즉 같은 (L,vds,vs)로 이 곡선을 57번 새로 계산하고 있었다(프로파일링으로 발견,
        # optimize_multistage() 캐싱과 같은 패턴). (L,vds,vs) 그대로를 키로 쓴다(반올림 없이 --
        # 이 값들은 동일 호출 체인에서 재사용되는 같은 float라 오차 누적 걱정이 없다).
        self._gm_id_curve_cache: dict = {}
        # 2026-08-12(세션30 감사 발견, 세션31 구현) -- _solve_vgs(gm_id,L,vds,vs)도 순수함수인데
        # gm_id_to_id_density()/gm_gds_ratio()/cgg_absolute()/fT() 등이 find_optimal_sizing()의
        # L×VDS×gm_id 3중루프 한 조합마다 각자 독립적으로 같은 (gm_id,L,vds,vs)로 이 함수를
        # 호출하고 있었다 -- _gm_id_curve()는 세션29가 이미 (L,vds,vs)로 캐싱했지만, 그 위에서
        # 매번 다시 도는 np.argsort/np.interp(정렬+역보간)는 캐싱이 없었다. _gm_id_curve_cache와
        # 동일한 패턴으로 (gm_id,L,vds,vs) 4-tuple을 키로 캐싱한다.
        self._solve_vgs_cache: dict = {}
        # 2026-08-13(세션31, F 설계 1단계) -- `_multilinear_interp()`(세션29가 순수-파이썬
        # bisect 구현으로 교체한 것, 위 클래스독스트링 밖 함수 참고)는 호출마다
        # `grids = [g.tolist() ...]`로 self.grids(4개 numpy 배열, 원소 합 ~100개)를
        # 매번 Python list로 재변환한다 -- self.grids는 생성자 이후 불변이라 이 변환도
        # __init__에서 한 번만 해서 재사용 가능(_log_ID와 같은 패턴). `_query()`/
        # `_gm_id_curve()`가 `self.grids` 대신 이걸 넘긴다.
        self._grids_list = [g.tolist() for g in self.grids]
        # 2026-08-13(세션31, 감사 발견 'B' 구현) -- search_gm_id_for_role()의 gm_id_grid
        # 스윕(gm_id마다 gm_id_to_id_density(gm_id,L,vds,vs) 호출)은 ID_target/role/W_bounds와
        # 무관하게 (L,vds,vs,gm_id_grid)에만 의존하는 순수 계산인데, make_replica_feasibility_
        # check()의 check() 클로저가 같은 (L,VDS)에 대해 (2 ratios x N replicas)번 이 전체
        # 스캔을 반복하고 있었다(replica 있는 스테이지에서 최대 ~114배 중복, 성능감사 최대
        # 개별낭비 후보). `_idu_scan()`이 이 스캔 결과를 캐싱한다.
        self._idu_scan_cache: dict = {}

    def _w_ref_effective(self, L: float) -> float:
        """이 L에서 ID/CGG 배열이 측정된 실제 기준폭. W_ref=None이면 단위소자(W*=L) 관례."""
        return L if self.W_ref is None else self.W_ref

    def _query(self, array, L, vgs, vds, vs):
        return _multilinear_interp(self._grids_list, array, [[L, vgs, vds, vs]])[0]

    def _query_multi(self, arrays, L, vgs, vds, vs):
        """`arrays`(같은 (L,vgs,vds,vs) 지점에서 함께 조회할 배열들, 예 `[self._log_ID,
        self.GM, self.GDS]`)를 한 번의 bisect 탐색으로 동시에 보간한다(F 설계, 세션31) --
        `_query()`를 배열마다 따로 부르면 같은 4축 bisect 탐색을 배열 개수만큼 반복하게 된다.
        `_multilinear_interp_point_multi()` docstring 참고."""
        return _multilinear_interp_point_multi(self._grids_list, arrays, [L, vgs, vds, vs])

    def _sizing_bundle(self, gm_id: float, L: float, vds: float, vs: float = 0.0,
                        need_cgg: bool = False):
        """`find_optimal_sizing()`의 L×VDS×gm_id 핫루프 전용(F 설계, 세션31 -- 성능감사가
        `_solve_vgs()` 캐싱 이후 남은 최대 레버로 지목: 이 루프 한 후보당 `gm_id_to_id_
        density()`/`gm_gds_ratio()`/(조건부)`cgg_absolute()`가 각자 `_query()`를 따로 불러
        같은 (L,vgs,vds,vs) 지점에서 bisect 탐색을 3~4번 반복했다). `_solve_vgs()` 1회(이미
        캐시됨) + `_query_multi()` 1회로 ID/GM/GDS/(CGG)를 한 번에 얻는다.

        반환: `(IDu, gm_gds_ratio, cgg_raw)` -- `cgg_raw`는 `need_cgg=False`면 `None`,
        아니면 **아직 W_target으로 스케일링 안 된 값**(`cgg_absolute()`의 raw 그대로)이다.
        `find_optimal_sizing()` 루프에서 W는 IDu를 먼저 알아야 나오는 값(`W=L*ID/IDu`)이라
        Cgg 최종 스케일링(`cgg_raw*W/w_ref`, 곱셈 하나뿐)은 W가 나온 뒤 호출부가 한다 --
        LUT 보간이 필요한 부분만 여기서 배치 처리하고, 나머지는 원래 `cgg_absolute()`와
        정확히 같은 식이라 값 변화가 없다.

        `gm_id_to_id_density()`/`gm_gds_ratio()`/`cgg_absolute()`를 이 값으로부터 재구성한
        것과 수치적으로 동일하다(같은 `_solve_vgs`/`_query` 계산을 배치로 묶었을 뿐)."""
        vgs = self._solve_vgs(gm_id, L, vds, vs)
        arrays = [self._log_ID, self.GM, self.GDS] + ([self.CGG] if need_cgg else [])
        vals = self._query_multi(arrays, L, vgs, vds, vs)
        IDu = math.exp(vals[0]) * L / self._w_ref_effective(L)
        gm_gds = vals[1] / vals[2]
        cgg_raw = vals[3] if need_cgg else None
        return IDu, gm_gds, cgg_raw

    def _idu_scan(self, L: float, vds: float, vs: float, gm_id_grid: list) -> list:
        """`gm_id_grid` 전체에 대해 `(gm_id, IDu)` 쌍을 계산해 `(L,vds,vs,gm_id_grid)` 키로
        캐싱한다(감사 발견 'B' 구현, 세션31). `IDu=gm_id_to_id_density(gm_id,L,vds,vs)`는
        `ID_target`/`role`/`W_bounds`와 무관하게 `(gm_id,L,vds,vs)`에만 의존하는 순수 계산인데
        `search_gm_id_for_role()`이 매 호출마다(같은 `(L,vds,vs)`라도) 이 스캔을 처음부터
        다시 돌리고 있었다 -- `make_replica_feasibility_check()`의 `check()` 클로저가 같은
        `(L,VDS)`에 대해 (2 ratios × N replicas)번 반복 호출하는 게 실측 최대 개별낭비 사례
        (replica 있는 스테이지에서 최대 ~114배). `ValueError`(LUT 범위 밖)/`IDu<=0`으로 걸러진
        `gm_id`는 애초에 반환 리스트에서 빠진다(원래 `search_gm_id_for_role()` 루프의 필터링
        순서 그대로 -- `ID_target`에 의존하는 `W_bounds` 체크만 호출부가 스캔 결과 위에서
        따로 한다)."""
        key = (L, vds, vs, tuple(gm_id_grid))
        cached = self._idu_scan_cache.get(key)
        if cached is not None:
            return cached
        scan = []
        for gm_id in gm_id_grid:
            try:
                idu = self.gm_id_to_id_density(gm_id, L, vds, vs)
            except ValueError:
                continue
            if idu <= 0:
                continue
            scan.append((gm_id, idu))
        self._idu_scan_cache[key] = scan
        return scan

    def _gm_id_curve(self, L, vds, vs):
        """고정 (L,vds,vs)에서 VGS 격자 전체에 대한 (ID, gm/ID) 배열을 반환 (역조회용).
        순수함수라 (L,vds,vs)별로 결과를 캐싱한다(위 `__init__`의 `_gm_id_curve_cache` 주석
        참고 -- `search_gm_id_for_role()`의 gm_id 스윕이 이 캐시의 주 수혜자)."""
        key = (L, vds, vs)
        cached = self._gm_id_curve_cache.get(key)
        if cached is not None:
            return cached
        np = self.np
        n = len(self.VGS_grid)
        pts = np.column_stack([
            np.full(n, L), self.VGS_grid, np.full(n, vds), np.full(n, vs),
        ])
        id_vals = np.exp(_multilinear_interp(self._grids_list, self._log_ID, pts))
        gm_vals = _multilinear_interp(self._grids_list, self.GM, pts)
        gm_id_vals = gm_vals / np.clip(id_vals, 1e-18, None)
        result = (id_vals, gm_id_vals)
        self._gm_id_curve_cache[key] = result
        return result

    def _solve_vgs(self, gm_id: float, L: float, vds: float, vs: float) -> float:
        """목표 gm/ID를 만족하는 VGS를 격자 위에서 역보간으로 찾는다 (gm/ID는 VGS에 단조감소).
        순수함수라 (gm_id,L,vds,vs)별로 결과를 캐싱한다(위 `__init__`의 `_solve_vgs_cache` 주석
        참고 -- find_optimal_sizing()이 같은 4-tuple로 이 함수를 여러 호출부에서 중복 호출한다)."""
        key = (gm_id, L, vds, vs)
        cached = self._solve_vgs_cache.get(key)
        if cached is not None:
            return cached
        np = self.np
        _, gm_id_vals = self._gm_id_curve(L, vds, vs)
        order = np.argsort(gm_id_vals)  # np.interp는 오름차순 x를 요구
        gm_id_sorted, vgs_sorted = gm_id_vals[order], self.VGS_grid[order]
        if gm_id < gm_id_sorted[0] or gm_id > gm_id_sorted[-1]:
            raise ValueError(
                f"gm_id={gm_id:.3g}가 LUT 범위[{gm_id_sorted[0]:.3g},{gm_id_sorted[-1]:.3g}] 밖 — "
                "VGS 스윕 범위를 넓히거나 moderate/weak inversion 쪽 gm/ID로 조정하세요.")
        result = float(np.interp(gm_id, gm_id_sorted, vgs_sorted))
        self._solve_vgs_cache[key] = result
        return result

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
        # 2026-08-12(세션30) -- self._log_ID(세션29가 __init__에서 이미 캐싱해둔 값,
        # _gm_id_curve()가 쓰는 바로 그 배열)를 안 쓰고 이 함수만 매 호출마다 4D ID 배열
        # 전체를 np.log(np.clip(...))로 재계산하고 있었다 -- find_optimal_sizing()의
        # L*VDS*gm_id 3중루프 안에서 반복 호출되는 핫패스라 영향이 크다(성능 실측 계기로
        # 발견, `.ai/context.md` 세션30). 값은 완전히 동일(같은 식, self.np is np) -- 순수
        # 캐시 재사용이라 동작 변화 없음.
        vgs = self._solve_vgs(gm_id, L, vds, vs)
        raw = math.exp(self._query(self._log_ID, L, vgs, vds, vs))
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

    def gm_id_for_vgs(self, target_vgs: float, L: float, vds: float, vs: float = 0.0) -> float:
        """`vgs_for_gm_id()`의 역함수 -- 목표 VGS를 만족하는 gm/ID를 O(1) 역보간으로 찾는다
        (탐색이 아니라 `_gm_id_curve(L,vds,vs)`가 이미 캐싱해둔 `(VGS_grid, gm_id_vals)` 곡선
        직접 조회, 2026-08-13 세션31 신설). `VGS_grid`는 LUT 축이라 항상 오름차순 -- `_solve_vgs()`
        (반대 방향 보간, gm_id_vals가 VGS_grid 오름차순에서는 내림차순이라 정렬이 필요함)와 달리
        추가 정렬 없이 바로 `np.interp` 가능.

        용도: 두 상보(complementary, 다른 kind) 소자가 KCL로 같은 전류(ID)를 흘리면서 DC
        레벨(VGS)이 일치/특정 관계를 맞춰야 하는 role(예: class-AB push-pull 출력단, `.ai/
        context.md` 세션31 BI/BJ 참고)에서, 한쪽 소자의 gm/ID는 통상 role 기반 탐색
        (`search_gm_id_for_role()`)으로 정하고, 다른 쪽은 그 소자의 실제 VGS를 목표로 이
        함수로 **탐색 없이 직접 역산**한다 -- `_feed_metric_stage_budget()`의
        `gm_id_match_vgs_of` 옵션이 이 패턴의 실제 사용처."""
        _, gm_id_vals = self._gm_id_curve(L, vds, vs)
        vgs_grid = self.VGS_grid
        if target_vgs < vgs_grid[0] or target_vgs > vgs_grid[-1]:
            raise ValueError(
                f"target_vgs={target_vgs:.3g}가 LUT VGS 범위[{vgs_grid[0]:.3g},"
                f"{vgs_grid[-1]:.3g}] 밖 -- VGS 스윕 범위를 넓히거나 이 소자의 (L,vds)를 재검토할 것.")
        return float(self.np.interp(target_vgs, vgs_grid, gm_id_vals))

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


def dense_candidates(grid, n: int) -> list:
    """1D 실측 격자(`lut.L_grid`/`lut.VDS_grid` 등, 오름차순)의 실측 **범위 안에서** `n`개의
    등간격 후보를 만든다 -- `find_optimal_sizing()`/`optimize_multistage()`에 넘길
    `L_candidates`/`VDS_candidates`용.

    2026-08-12(세션30) 신설 -- harness 연동 감사 중 발견: `SemiEmpiricalGmIdLUT`는 L/VDS/VS
    축을 이미 다중선형보간한다(클래스 docstring "L/VDS/VS 축: 선형 다중보간(불균등 L 격자
    그대로 지원)", `_multilinear_interp()`가 4축 전부 동일하게 처리)는데도, `run_harness.py`를
    포함해 이 프로젝트의 **모든** `L_candidates`/`VDS_candidates` 구성부
    (`sky130_regression_reference.json` 골든 케이스 제외)가 실측 격자를 그대로 쓰거나
    (L: sky130 4개 앵커점, 0.15/0.35/0.5/1.0µm) 성기게 데시메이션(VDS: `grid[::24]`로
    49점→3점)해서 탐색 후보 자체가 LUT의 보간 능력을 안 쓰고 있었다. 사용자 지적
    (current_reuse_telescopic_ota의 M15/M16 독립 L 탐색이 딱 이 이유로 gain_db/
    classab_centering_dev_v 동시만족점을 4개 앵커점 사이에서 못 찾고 있었다 -- 다만 실측
    확인 결과 이 특정 쌍은 촘촘한 탐색으로도 feasible point가 없음이 밝혀짐, `.ai/context.md`
    세션30 참고 -- 그래도 다른 소자/회로에선 이 densify가 실제로 답을 바꿀 수 있다)를
    계기로 L에 국한하지 않고 일반화한다.

    ⚠️ 실측 범위 **밖은 외삽**이라 신뢰할 수 없으므로(선형 다중보간은 범위 밖에서 경계값을
    그대로 반복하는 clamp 방식 -- `_multilinear_interp()` 코드 참고) `lo`/`hi`를 항상 실측
    격자의 최소/최대로 고정한다 — `n`을 아무리 키워도 실측 범위를 벗어나지 않는다.
    `find_optimal_sizing()`/`optimize_multistage()` 자체는 이미 완전히 제네릭이라(임의 L/VDS
    값에 대해 `lut.gm_id_to_id_density()` 등을 그대로 호출) 이 함수는 엔진 변경이 아니라
    **호출부가 넘기는 후보 리스트**만 바꾸는 것이다.

    ⚠️ **성능 트레이드오프**: `find_optimal_sizing()`은 `len(L_candidates) *
    len(VDS_candidates) * len(gm_id_grid)` 3중루프이고, `optimize_multistage()`의
    `shared_gm_id_groups` 경로(`_size_shared_group()`)는 이걸 gm_id_grid 전체에 대해
    반복 호출할 수 있다 -- `n`을 무작정 키우면 조합 수가 그대로 곱으로 늘어난다. `gm_id`가
    같으면 `ID=gm/gm_id`가 L/VDS와 무관(`objective="power"`)하므로, L/VDS는 보통 **몇 개면
    충분**하다(feasibility 판정용) -- 필요 이상으로 촘촘하게 하지 말 것(호출부에서 `n`을
    상황에 맞게 고를 것, 이 함수는 고정 기본값을 강제하지 않는다).

    ⚠️ **실측 앵커점을 항상 먼저 배치한다**(2026-08-12 세션30, harness 연동 감사 중 발견한
    2차 파급 문제의 근본수정): `find_optimal_sizing()`의 tie-break는 동점이면 "먼저 나온"
    후보를 유지한다(511행 `obj_val < best_val`, 엄격 부등식). `objective="power"`에서는
    `ID=gm/gm_id`가 L/VDS와 완전히 무관해 같은 gm_id에서 feasible한 모든 (L,VDS)가
    **정확히 동점**이다 -- 후보를 앵커점 없이 순수 등간격으로만 만들면 이 동점에서
    임의의(보간된, "특별할 것 없는") L/VDS가 앵커점을 제치고 이겨버려, 그 L을 물려받는
    다른 소자(matching_pairs 매칭쌍, K_replica 같은 C타입 replica 타겟)가 실측 검증된
    적 없는 L에서 예상 못 한 infeasibility를 만날 수 있다(실측 사례: M9a가 M15의 보간
    L=0.235µm을 물려받자 W_bounds를 못 맞춤 -- L 자체는 M15 입장에서 아무 문제 없었는데
    파급효과만 생긴 경우). **`find_optimal_sizing()`/`optimize_multistage()`의 tie-break
    로직 자체는 안 건드린다**(다른 목적으로 이미 "회귀 위험 있어 안 건드림"이라 문서화된
    영역, `optimize_multistage()` docstring "한계 순환" 문단 참고) -- 대신 이 함수가 만드는
    **후보 리스트의 순서**만 바꿔서(실측 앵커점 먼저, 보간으로 채운 값은 그 뒤) 앵커점이
    feasible하기만 하면 항상 먼저 발견돼 동점을 이기게 한다. 앵커점만으로 안 풀리는
    경우에만(예: classab_centering_dev_v처럼 진짜 더 넓은 범위가 필요할 때) 자연스럽게
    보간값으로 넘어간다 -- densify의 이점은 그대로 유지하면서 "이유 없이 새로운 L을
    골라 하류에 파급"되는 부작용만 없앤다.

    ⚠️ **`len(grid) >= n`이면 보간하지 않고 실측점을 서브샘플한다**(구현 중 자체 발견한
    버그 수정): 앵커점을 무조건 전부 앞에 붙이면 VDS처럼 실측 격자가 이미 촘촘한 축
    (sky130: 49점)에서 `n=13`을 요청해도 앵커 49개 + 보간 후속분까지 합쳐 최대 62개가
    나가버려(`n`이 사실상 무시됨) 의도한 성능 예산을 크게 넘긴다. 실측점이 이미 `n`개보다
    많으면 그 실측점 자체를 `n`개로 균등 서브샘플한다(여전히 전부 실측값, 보간 없음 --
    애초에 밀도가 충분하니 합성할 이유가 없다). 실측점이 `n`개보다 적을 때만(L처럼 앵커가
    극도로 성길 때) 앵커 전부 + 등간격 보간으로 채운다."""
    anchors = [float(v) for v in grid]
    if len(anchors) >= n:
        if n <= 1:
            return [anchors[0]]
        idx = sorted({round(i * (len(anchors) - 1) / (n - 1)) for i in range(n)})
        return [anchors[i] for i in idx]
    lo, hi = anchors[0], anchors[-1]
    interpolated = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    seen = set(anchors)
    fill_ins = [v for v in interpolated if v not in seen]
    return anchors + fill_ins


def quantize_L(L: float, grid_step: float, mode: str = "nearest") -> float:
    """L을 `grid_step`(공정 레이아웃 그리드 해상도, m 단위 -- 예: sky130 poly 그리드)의
    배수로 스냅한다(2026-08-13 세션31, 사용자 지시 -- 실제 레이아웃에서 임의 소수점 L을
    구현할 수 없다는 제약을 반영). `grid_step` 값 자체는 이 함수가 정하지 않는다 -- 실제
    PDK 문서에서 가져올 것(feedback_no_paper_values_derive_rationally 원칙과 동일하게,
    값을 추측하지 않는다).

    `mode`: `"nearest"`(반올림 -- 후보 리스트 생성용, `layout_grid_L_candidates()`가
    내부적으로 씀) / `"floor"`/`"ceil"`(한쪽으로 치우쳐 스냅해야 할 때 -- 예: 선언된
    bounds `[lo,hi]` 안에 반드시 남아야 하는 SLSQP 사후처리, `lo`는 ceil로 올림해야
    bounds 하한을 안 벗어나고 `hi`는 floor로 내려야 상한을 안 벗어난다)."""
    if grid_step <= 0:
        raise ValueError(f"grid_step={grid_step}은 0보다 커야 한다")
    fn = {"nearest": round, "floor": math.floor, "ceil": math.ceil}.get(mode)
    if fn is None:
        raise ValueError(f"알 수 없는 mode={mode!r} -- 'nearest'/'floor'/'ceil' 중 하나")
    return fn(L / grid_step) * grid_step


def _grid_points_in_range(lo: float, hi: float, grid_step: float, n: int | None = None) -> list:
    """`[lo,hi]` 구간 안에서 `grid_step`의 배수인 점을 전부(또는 `n`개로 서브샘플해)
    반환한다 -- `layout_grid_L_candidates()`/`optimize_full_circuit_budget()`의
    `metric_stage_budget`(L) theta 격자탐색/`search_stage_budget_L_warm_start()`의 LUT
    스캔이 전부 이 저수준 헬퍼를 공유한다. `n`으로 서브샘플할 때는 `dense_candidates()`와
    동일한 균등 인덱스 선택 패턴을 쓴다(성능 예산 보존 -- grid_step이 촘촘해도 `n`을
    넘는 후보를 만들지 않는다, 세션31 "재계산 비효율 보장" 지시 참고)."""
    start = quantize_L(lo, grid_step, mode="ceil")
    end = quantize_L(hi, grid_step, mode="floor")
    if start > end:
        raise ValueError(
            f"[{lo},{hi}] 구간 안에 grid_step={grid_step}의 배수가 하나도 없다 -- "
            f"grid_step이 구간 폭보다 크거나 bounds/grid_step을 재확인할 것")
    count = int(round((end - start) / grid_step)) + 1
    all_points = [start + i * grid_step for i in range(count)]
    if n is None or len(all_points) <= n:
        return all_points
    idx = sorted({round(i * (len(all_points) - 1) / (n - 1)) for i in range(n)})
    return [all_points[i] for i in idx]


def layout_grid_L_candidates(lut: "SemiEmpiricalGmIdLUT", grid_step: float,
                              L_min: float | None = None, n: int | None = None) -> list:
    """공정 레이아웃 그리드(`grid_step`, m 단위)에 정렬된 L 후보를 만든다 --
    `dense_L_candidates()`(보간 기반, 임의 소수점 L을 생성할 수 있음)의 대체재. 태생적으로
    전부 `grid_step`의 배수라 사후 스냅이 불필요하다(`find_optimal_sizing()`은 `L_candidates`
    를 그대로 순회만 하는 불투명 리스트로 받으므로, 이 함수는 **호출부가 넘기는 후보
    리스트만 바꾸는 것**이고 엔진(`find_optimal_sizing()`/`optimize_multistage()`) 자체는
    변경이 필요 없다).

    `L_min`(기본: LUT 실측 하한, `lut.L_grid[0]`)부터 LUT 실측 상한(`lut.L_grid[-1]`,
    외삽 없음 -- `dense_candidates()`와 동일 원칙)까지 `grid_step` 간격으로 나열한다.
    `n`이 주어지고 격자점 개수가 `n`을 넘으면 `dense_candidates()`와 동일한 서브샘플로
    `n`개로 줄인다(2026-08-13 세션31, 사용자 지시 "이 설계변경이 재계산 비효율을
    만들지 않도록 보장" -- `grid_step`이 촘촘해도(예: 5nm) `find_optimal_sizing()`의
    L×VDS×gm_id 3중루프 격자 크기가 `dense_L_candidates(n=41)` 등 기존 호출부가 쓰던
    예산을 넘지 않게 호출부가 반드시 `n`을 지정할 것 -- 제네릭 유지를 위해 강제 기본값은
    두지 않는다)."""
    lo = L_min if L_min is not None else float(lut.L_grid[0])
    hi = float(lut.L_grid[-1])
    return _grid_points_in_range(lo, hi, grid_step, n)


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
                         vs: float = 0.0, extra_feasible=None):
    """(L, VDS, gm/ID) 격자를 전부 스윕해 제약조건을 만족하는 점 중 objective 최소인 것을 반환.

    gm을 고정할 방법 두 가지: (fT,C) 지정 -> gm=2*pi*fT*C (단일 스테이지, §1 절차 그대로) 또는
    gm을 직접 지정(다단 회로에서 위상보상 방정식이 이미 gm_i를 정해준 경우 — optimize_2stage_
    miller_ota()가 이렇게 쓴다). fT를 지정하면 준정적 조건(fT<=margin*f_nqs)도 같이 검사한다.

    objective: "power"(ID 최소) 또는 "area"(W 최소) — 방법론 §5.1 트레이드오프 삼각형의
    두 축에 대응. gain_min/w_max/quasi_static_margin은 §5 검증 체크리스트 항목을 그대로
    제약조건화한 것.

    extra_feasible(2026-08-12 세션30 신설, 선택적): `(L, VDS, gm_id, ID) -> bool` 콜백 --
    gain_min/w_max/fT만으로는 표현 못 하는 추가 feasibility 조건(예: 이 (L,VDS,gm_id,ID)
    조합을 물려받는 **다른** 소자가 여전히 자기 제약을 만족하는지)을 호출부가 주입한다.
    `optimize_multistage()`가 K_replica류 C타입 replica feed의 타겟 소자 검증에 쓴다
    (근본원인: B엔진이 자기 스테이지 목적함수만 보고 L을 고르면, 그 L을 물려받는 replica/
    matching 소자가 깨질 수 있다는 걸 이 엔진이 원래 전혀 몰랐다 -- harness 연동 감사로
    발견, `.ai/context.md` 세션30). 엔진 자체는 여전히 "무엇을 확인할지" 모른 채 콜백만
    호출한다(제네릭 유지) -- `None`이면 기존과 100% 동일(하위호환).

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
                    # 2026-08-13(세션31, F-2 구현) -- gm_id_to_id_density()/gm_gds_ratio()/
                    # cgg_absolute()를 각각 부르면 같은 (L,vgs,VDS,vs) 지점에서 LUT bisect
                    # 탐색이 3~4번 반복된다(성능감사가 _solve_vgs 캐싱 이후 남은 최대 레버로
                    # 지목) -- _sizing_bundle()로 한 번에 묶는다. Cgg는 W가 나온 뒤(IDu 필요)
                    # 마지막에 raw*W/w_ref로 스케일링 -- cgg_absolute()와 동일한 식, 수치 동일.
                    IDu, gain, cgg_raw = lut._sizing_bundle(gm_id, L, VDS, vs, need_cgg=(fT is not None))
                    ID = gm / gm_id
                    W = L * ID / IDu
                    fnqs_ok = True
                    if fT is not None:
                        Cgg = cgg_raw * W / lut._w_ref_effective(L)
                        fnqs_ok = check_quasi_static(fT, gm, Cgg, quasi_static_margin).ok
                except (ValueError, ZeroDivisionError):
                    continue
                feasible = (
                    (gain_min is None or gain >= gain_min)
                    and (w_max is None or W <= w_max)
                    and fnqs_ok
                )
                # 2026-08-12(세션30) -- extra_feasible은 값싼 gain_min/w_max/fT 체크를 전부
                # 통과한 후보에만 실행한다(비싼 콜백이라 -- 아래 참고, 불필요한 호출 최소화).
                if feasible and extra_feasible is not None:
                    feasible = extra_feasible(L, VDS, gm_id, ID)
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
                         shared_gm_id_groups: list | None = None,
                         stage_extra_feasible: list | None = None):
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
    VDS_candidates: 평평한 숫자 리스트(전 스테이지 공통, 기존 동작) 또는 **리스트의 리스트**
    (스테이지별 후보, 2026-08-12 세션30 신설 -- `vertical_stack_id` 헤드룸 인지 상한을
    반영할 때 호출부가 씀, 아래 `_resolve_vds()` 참고). 스테이지 수보다 짧으면 그 뒤
    인덱스에서 `IndexError` -- 호출부가 스테이지 수만큼 채워 넘길 것.

    stage_extra_feasible(2026-08-12 세션30 신설, 선택적): 스테이지별
    `find_optimal_sizing()`의 `extra_feasible` 콜백 리스트(길이 = 스테이지 수, 원소는
    `(L,VDS,gm_id,ID)->bool` 또는 `None`) -- 이 스테이지의 L을 물려받는 **다른** 소자
    (K_replica류 C타입 replica feed의 타겟)가 여전히 자기 제약을 만족하는지 호출부가
    확인하게 한다. 근본원인: gain_min/w_max만으로 스테이지 자신의 objective를 최적화하면,
    그 L을 물려받는 다운스트림 소자가 깨질 수 있다는 걸 이 엔진이 원래 전혀 몰랐다(harness
    연동 감사로 발견 -- L_candidates를 densify하자 실제로 자주 걸림, `.ai/context.md`
    세션30). `None`(기본값)이면 기존과 100% 동일.

    topology_fn.stage_fT_targets(2026-08-12 세션30, 선택적 함수 속성 -- `exposed_params`와
    같은 노출 패턴): Hz 단위 스테이지별 준정적(quasi-static) 검증 기준주파수 리스트(gm
    리스트와 위치 대응), 없으면(대부분의 topology_fn) 해당 스테이지는 기존처럼 검증을
    건너뛴다 -- 100% 하위호환. `current_reuse_telescopic_topology()`가 실제로 이 속성을
    채우는 첫 예시(자세한 설계 배경은 `_size_stage()`/`_size_group_at_gm_id()` 바로 위
    주석 참고).

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
    # 2026-08-12(세션30) -- 준정적(quasi-static) 근사 유효성(find_optimal_sizing()의 fT
    # 인자, check_quasi_static()) 검증이 이 엔진 경로(compensation.stage_devices로 사이징되는
    # 모든 스테이지)에서 지금까지 한 번도 실행된 적이 없었다(harness 연동 감사로 발견,
    # `.ai/context.md` 세션30) -- fT가 항상 None으로 넘어가 fnqs_ok=True로 무조건 통과했다.
    # 문헌조사(gm-id-methodology.md §9.5 "전류거울은 strong inversion/이득단은 weak-moderate,
    # 한 OTA 안에서도 소자별로 다른 동작점이 정상" + §6.4 Miller pole-splitting "2단
    # gain-bandwidth > omega_T" 안정조건)로 확인한 결론: 준정적 마진의 기준주파수는 회로
    # 전체에 하나가 아니라 **스테이지마다 다르다**(입력단은 메인루프 unity-gain 주파수,
    # 출력단은 그보다 높은 비지배극 주파수를 기준으로 해야 함) -- 이걸 엔진에 하드코딩하면
    # "엔진은 제네릭, topology_fn이 회로별 수식을 콜백으로 제공"하는 이 파일 전체의 설계
    # 원칙을 깬다(사용자 지적 계기로 설계 재검토).
    #
    # 그래서 topology_fn이 이미 `exposed_params`(예: omega_c)로 자기 회로의 파생값을
    # 노출하는 것과 똑같은 패턴으로, 선택적 속성 `stage_fT_targets`(Hz 단위 리스트, 반환
    # gm 리스트/stage_devices와 위치로 1:1 대응 -- shared_gm_id_groups의 인덱스 관례와 동일)를
    # 노출하면 이 엔진이 자동으로 읽어 스테이지별로 다른 fT를 적용한다. 원소가 None이거나
    # 속성 자체가 없으면(기존 topology_fn 전부 해당) 그 스테이지는 기존과 동일하게 체크를
    # 건너뛴다 -- 100% 하위호환. 새 값을 계산하는 게 아니라, 각 topology_fn이 이미 자기
    # 내부에서 구하고 있던 극점 주파수(Miller의 ωNDP, NGCC의 ω1/ω2/ω3, current-reuse의
    # omega_c/omega_p2 등)를 노출만 하면 된다 -- 지금은 current_reuse_telescopic_topology()
    # 하나만 실제로 이 속성을 채운다(이번 세션 조사 범위), 나머지 3개는 아직 미제공(기존
    # 동작 그대로, 회귀 없음) -- 메커니즘 자체는 이미 전 토폴로지에 열려 있다.
    fT_targets = getattr(topology_fn, "stage_fT_targets", None)

    def _per_stage(param, i):
        return param[i] if isinstance(param, (list, tuple)) else param

    # 2026-08-12(세션30) -- VDS_candidates는 원래 전 스테이지가 공유하는 "평평한" 숫자
    # 리스트라 _per_stage()를 그대로 못 쓴다(param[i]가 리스트가 아니라 그 인덱스의
    # VDS 숫자 하나를 뽑아버림) -- 별도 resolver. "리스트의 리스트"(원소[0]이 list/tuple)면
    # 스테이지별 후보로 보고 param[i]를, 아니면(기존 100% 하위호환) 그대로 공유 리스트를
    # 쓴다. 근본원인(harness 연동 감사, `.ai/context.md` 세션30): VDS가 이 엔진 안에서
    # `vertical_stack_id`(같은 물리적 VDD~GND 컬럼)를 전혀 모른 채 완전 자유변수로
    # 탐색되고 있었다 -- L_candidates를 densify하자 이 자유도가 실제로 KVL을 위반하는
    # 값(예: VDS=vdd 전체)을 찾아내는 게 실측으로 드러났다(baseline은 후보 3개뿐이라
    # 우연히 안전한 값만 나왔을 뿐). 호출부(_evaluate())가 같은 vertical_stack_id를
    # 공유하는 다른 확정 소자(metric_stage_budget 고정 vds, device_roles의
    # min_vds_by_role)의 예산을 미리 빼서 스테이지별 VDS 상한을 계산해 이 리스트의
    # 리스트로 넘긴다 -- 엔진 자체는 여전히 "무엇이 스테이지별로 다를 수 있는가"만 알 뿐
    # "왜" 다른지는 모른다(제네릭 유지).
    def _resolve_vds(i):
        if VDS_candidates and isinstance(VDS_candidates[0], (list, tuple)):
            return VDS_candidates[i]
        return VDS_candidates

    def _size_stage(i, gm):
        best, _ = find_optimal_sizing(
            luts[i], L_candidates, _resolve_vds(i), gm_id_grid, gm=gm,
            objective=objective, gain_min=_per_stage(gain_min, i), w_max=_per_stage(w_max, i),
            fT=_per_stage(fT_targets, i), extra_feasible=_per_stage(stage_extra_feasible, i))
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
                luts[i], L_candidates, _resolve_vds(i), [gm_id], gm=gms[i],
                objective="area", gain_min=_per_stage(gain_min, i), w_max=_per_stage(w_max, i),
                fT=_per_stage(fT_targets, i), extra_feasible=_per_stage(stage_extra_feasible, i))
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
# 6.5) topology.json의 "compensation.function" 문자열이 참조할 수 있는 함수의 allowlist
#      (eval()/getattr(module, name) 금지 — JSON 안의 임의 문자열로 임의 코드를 실행하지
#      않기 위함). `optimize_full_circuit_budget()`의 `_evaluate()`가 직접 조회한다
#      (`_COMPENSATION_REGISTRY[comp["function"]](**comp_params)`, 2026-08 세션6 이후).
#      2026-08-12(세션30) -- 이 registry만 남기고 `load_sizing_targets()`/
#      `write_sizing_results()`/`run_sizing_pipeline()`(2026-07-28 신설, "I/O만 담당하는
#      topology JSON 오케스트레이션 레이어")는 삭제했다: `optimize_full_circuit_budget()`
#      (2026-07-31 이후 "AI는 이 함수 하나만 호출한다"로 확정된 단일 진입점)이 이 세
#      함수의 역할(compensation 조회+실행, instance.json 입출력)을 자체 로직으로 완전히
#      대체한 뒤로 저장소 전체에서 호출부가 self-test 말고는 0건이었다(harness 연동 감사,
#      `.ai/context.md` 세션30) -- 죽은 코드를 감추지 않고 삭제.
# ---------------------------------------------------------------------------

from topology_library import (miller_ota_topology, nmcnr_3stage_topology, ngcc_3stage_topology,
                               current_reuse_telescopic_topology, nmcnr_predict_ac_response)

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


# ---------------------------------------------------------------------------
# 6.6) 공정-무관 회귀 검증 러너 — "무엇을 검증할지"는 전부 reference JSON이 선언하고, 이
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
    """`allocate_stack_headroom()`의 배정 정책 — "얇게"(thin) 배정받는 role의 헤드룸만
    정책으로 갈아끼울 수 있게 분리했다(§7.9 질문 5, 2026-07-31 결정: 정책 객체/콜백으로
    설계). `cascode_fn(entry) -> float`: `{"name","role","min_vds"[,"gm_id","margin"]}`
    하나를 받아 그 소자에 배정할 VDS를 반환(이름은 유지하되 cascode 전용이 아니게 됨,
    아래 `thin_roles` 참고).

    `thin_roles`(2026-08-11 세션28 신설): "남는 예산 균등분배" 대신 `cascode_fn`으로
    얇게 배정받는 role 집합. 기본은 `{"cascode", "diode_reference"}` -- `diode_reference`
    는 M18_bg(diode-connected 기준전압 생성기, 외부 전류원으로 전류가 정해지는 singleton)
    사례로 신설: cascode처럼 "필요한 만큼만" 받으면 되지 "남는 걸 다 가져갈" 이유가 없는
    role인데, 예전엔 non-cascode는 전부 "남는 예산 균등분배"를 타서 singleton이면 그
    "균등분배"가 "전부 다 가짐"이 됐다(M5/M60/M66/M18_bg 등에서 실측 확인, `.ai/
    context.md` 세션28 참고). ⚠️ diode-connected라고 전부 이 집합에 넣으면 안 된다 --
    `M39`/`M40`(`voltage_divider` role, VDD/2 self-biased 분압기)도 diode-connected지만
    **의도적으로** "남는 예산을 둘이 나눠 갖는" 동작(각 vdd/2)을 원한다(session27이 이
    사례 때문에 `cascode`를 그대로 못 쓰고 `voltage_divider`를 새로 만들었다 -- 물리적
    역할이 다르면 role 문자열도 다르게 선언한다는 이 프로젝트 원칙 그대로). 구분 기준은
    "diode-connected 여부"가 아니라 "이 소자가 예산을 나눠 가질 파트너/설계의도가
    있는가"다."""
    cascode_fn: Callable[[dict], float] = _default_cascode_headroom
    thin_roles: frozenset = frozenset({"cascode", "diode_reference"})


DEFAULT_POLICY = HeadroomPolicy()


def allocate_stack_headroom(vdd: float, stack: list, policy: HeadroomPolicy = DEFAULT_POLICY) -> dict:
    """배치 7-3b — 직렬 스택(예: `resize.py`의 M6/M1/M2/M3/M4/M5, VDS 하드코딩 0.30/0.40/
    0.20/0.20/0.40/0.30)의 VDS를 "캐스코드는 얇게, 입력/tail은 넉넉하게"라는 **의도를 실행하는
    함수**로 대체한다.

    `stack`: `[{"name","role","min_vds"[,"gm_id","margin"]}, ...]` — `role`이
    `policy.thin_roles`에 있으면(기본 `{"cascode","diode_reference"}`) `policy.cascode_fn
    (entry)`(기본: gm_id가 있으면 `2/gm_id+margin`, 없으면 `min_vds` 그대로)만큼만
    배정한다. 나머지 역할(`"input"`/`"tail"`/`"voltage_divider"` 등)은 남는 예산
    (`vdd - thin 합`)을 인원수로 균등 배분한다(가중치 배분이 필요해지면 `policy`를
    확장 — 지금은 이 정책 하나로 충분함이 이 회로 하나로만 확인됨).

    합이 `vdd`와 정확히 일치함을 함수 자체가 보장한다(assert) — 예전에 이 합을 안 맞춰
    3.2V(1.8V 레일 초과)로 잘못 짰던 실제 사고가 있었다(§3 실측 이력)."""
    thin_entries = [e for e in stack if e["role"] in policy.thin_roles]
    other_entries = [e for e in stack if e["role"] not in policy.thin_roles]

    result = {}
    thin_total = 0.0
    for e in thin_entries:
        v = policy.cascode_fn(e)
        result[e["name"]] = v
        thin_total += v

    remaining = vdd - thin_total
    if other_entries:
        share = remaining / len(other_entries)
        for e in other_entries:
            result[e["name"]] = share
    total = sum(result.values())
    assert abs(total - vdd) < 1e-9 * max(vdd, 1.0), (
        f"헤드룸 배정 합({total})이 vdd({vdd})와 불일치 -- other_entries가 비어있는데 "
        f"thin 배정 합이 vdd와 안 맞으면 배분할 곳이 없어 이 assert가 실패한다.")
    return result


def search_gm_id_for_role(lut: "GmIdLUT", L: float, vds: float, vs: float, ID_target: float,
                           role: str, W_bounds: tuple = (1e-6, 200e-6),
                           gm_id_grid: list | None = None, return_idu: bool = False):
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
      상한 고정 후 역산" 수동 flip이 이 역할의 특수 사례였다). ⚠️ 이름과 달리 실제로는
      "feasible 중 gm/ID가 가장 낮은(=W가 가장 작은, 면적최소) 점"을 고르는 것과 동치다
      (ID_target 고정 하에서는 gm/ID가 커질수록 W가 커지므로 오름차순 첫 feasible=최소
      W) -- 전기적 기준(이득/매칭/속도)이 전혀 없는, "이 정도면 W가 비현실적이지 않다"는
      제조성 하한만 넘기는 규칙이라는 걸 이름만 보고 오해하지 말 것(2026-08-13 세션31
      정정, 사용자 지적으로 재검토됨 -- 아래 `"moderate"`가 이 gap을 메운다).
    - `"moderate"`(2026-08-13 세션31 신설, 사용자 지시 -- two_stage_ota M5(gds가 이득과
      무관한 tail 전류원)처럼 명시적 극값도 필요 없고 `"balanced"`의 암묵적 면적최소화도
      전기적 근거가 약한 경우) — feasible 목록(gm_id 오름차순)의 **중앙값 인덱스**를
      고른다. `"matching"`/`"gain"`이 각각 범위의 양 끝(최소/gm_gds 최댓값)을 고르는
      것과 대칭적으로, 이건 "이 (ID,L,vds,W_bounds) 조합에서 실제로 실현 가능한 strong↔
      weak inversion 구간의 정중앙"을 고른다 -- 물리 상수(예: 1/(n·UT) 온도별 최대
      gm/ID)에 의존하지 않아 toy LUT/실측 LUT 어디서든 동일하게 동작하고(LUT가 n/UT를
      노출할 필요 없음), gm-id-methodology.md §5.2 "Moderate Inversion이 최적"(전류·
      면적·이득의 3중 절충점)이 말하는 개념을 이 프로젝트의 "feasible 후보 스캔"
      아키텍처 위에 가장 낮은 비용으로 구현한 것이다. `"balanced"`는 그대로 유지된다
      (다른 회로의 기존 선언·회귀값에 영향 없음, 순수 추가).
    - `"load"`(2026-08-19 세션37 연속 신설, 사용자 지시 -- nmcnr_amplifier M109/M302/M202
      실측이 계기) — **캐스코드가 아닌 단순 전류원(active load)이 `ro` 자체로만 회로에
      기여할 때** 전용. `"gain"`은 `gm/gds`를 최대화하는데, 이건 `R = gm(소자)·ro(소자)·
      (...)`처럼 gm이 실제로 곱해져 기여하는 캐스코드에만 논리적으로 맞는 기준이다 --
      캐스코드가 아닌 소자(예: 폴디드 캐스코드의 비캐스코드 branch, 단순 PMOS/NMOS 전류원
      부하)는 `gm`이 그 기여식에 안 나타나므로 `gds` 자체를 최소화(=`ro` 최대화)하는 게
      맞는 기준인데, 이건 `gm/gds`와 **다른 물리량**이라 "gain"이 대신 최적화해주지
      않는다(실측 확인: `gds` vs `gm_id` 곡선 모양이 소자마다 다르다 -- 어떤 소자는
      단조감소(`gm_id`↑→`ro`↑, "gain"이 우연히 유리), 어떤 소자는 중간에 피크가 있어
      `"gain"`이 그 피크를 훌쩍 지나쳐 오히려 손해였다(M202, vds=1.0V: `gm_id≈3.5`에서
      `ro` 피크, `"gain"`이 고른 `gm_id=16`은 피크 대비 거의 절반). `"matching"`(gm_id
      최소화)도 우연히 맞을 때(feasible 하한이 곧 피크 이전 구간이면)와 틀릴 때(피크가
      더 낮은 gm_id에 있으면)가 갈린다 -- 지름길이 없고 매번 스캔해서 실제 `ro` 최댓값을
      찾아야 한다는 게 이번 세션의 결론. `"moderate"`처럼 "왜 이 값인가"가 이름에 담겨야
      한다는 이 프로젝트의 관례를 따라 `"ro_max"`(수식 그대로) 대신 **회로적 역할**
      (이 소자는 이득을 만들지 않는 단순 부하/전류원이다)을 담은 `"load"`로 명명(사용자
      선택, 2026-08-19). `feasible` 전체를 스캔해 `gds`가 가장 작은(=`ro`가 가장 큰)
      `gm_id`를 고른다 -- `"gain"`과 동일하게 "극단으로 미는" 방식이 아니라 "실제 최댓값을
      찾는" 방식(정직한 스캔, 방향을 가정하지 않음)이라는 점에서 `"matching"`/`"balanced"`
      류와 다르다. ⚠️ 이 role도 `"gain"`처럼 **무조건 최댓값**을 고른다(중간값 옵션은
      아직 없음) -- 이 프로젝트의 다른 회로들처럼 `objective`가 전력 최소화이고 이 소자들의
      `ID`가 KCL로 이미 고정돼 있는 한(`W`만 커질 뿐 전력 비용이 없음) 무조건 최대화가
      안전하지만, 면적/기생커패시턴스가 실제 비용인 상황이라면 `"moderate"`처럼 중간값을
      고르는 변형이 필요할 수 있다 -- 그런 요구가 실제로 나오면 그때 확장할 것(아직 쓰이지
      않는 옵션을 미리 만들지 않는다는 이 프로젝트 원칙 그대로).

    `return_idu`(2026-08-13 세션31 신설, 기본 False -- 하위호환): True면 `gm_id` 대신
    `(gm_id, IDu)`를 반환한다. 스캔 도중 이긴 `gm_id`의 `IDu`(=`lut.gm_id_to_id_density(...)`)는
    이미 계산돼 있는데, 기존 호출부(`_evaluate()`의 gm_id_role 루프)가 이 반환값을 버리고
    `size_transistor()`로 바로 이어서 동일 인자로 다시 조회하고 있었다(감사 발견 -- `_solve_vgs`
    캐시가 정렬+역보간은 흡수해주지만 `_query(_log_ID,...)` 자체는 여전히 중복 실행됨). 이
    한도 안에서만 호출부가 재조회를 건너뛸 수 있게 옵트인으로 노출한다(기존 호출부는 전부
    변경 없음 -- 인자를 안 주면 100% 이전과 동일).

    후보가 하나도 없거나 `role`이 셋 중 하나가 아니면 즉시 `ValueError`.

    2026-08-13(세션31, 감사 발견 'B' 구현) -- gm_id_grid 스캔 자체(`ValueError`/`IDu<=0`
    필터링까지)는 `ID_target`/`role`/`W_bounds`와 무관하게 `(L,vds,vs,gm_id_grid)`에만
    의존한다 -- `lut._idu_scan()`으로 캐싱된 스캔 결과를 받아 `W_bounds` 체크만 여기서
    한다(`_idu_scan()` docstring 참고)."""
    if gm_id_grid is None:
        gm_id_grid = [i * 0.5 for i in range(4, 61)]  # 2.0~30.0
    feasible = []
    idu_by_gm_id = {}
    for gm_id, idu in lut._idu_scan(L, vds, vs, gm_id_grid):
        W = ID_target * L / idu
        if W_bounds[0] <= W <= W_bounds[1]:
            feasible.append(gm_id)
            idu_by_gm_id[gm_id] = idu
    if not feasible:
        # 2026-08-12(세션30) -- ValueError였던 걸 InfeasibleSizingError로 변경(harness
        # 연동 감사 중 발견: L_candidates densify로 compensation 단계 L이 옛 4개 앵커점을
        # 벗어나자, matching_pairs로 그 L을 공유하는 role="matching" 소자가 이 조건에
        # 걸려 grid search 전체를 크래시시켰다 -- A_signed KCL 위반과 똑같이 "이 theta
        # 격자점/L 조합이 물리적으로 실현 불가능하다"는 뜻일 뿐 선언 오류가 아니므로,
        # InfeasibleSizingError의 기존 관례(그 격자점만 건너뜀)를 그대로 적용한다.
        raise InfeasibleSizingError(
            f"W_bounds={W_bounds} 안에 드는 gm_id 후보가 없다(role={role!r}, "
            f"gm_id_grid={gm_id_grid[0]}~{gm_id_grid[-1]}) -- 범위를 넓히세요.")
    if role == "matching":
        best_gm_id = min(feasible)
    elif role == "balanced":
        best_gm_id = feasible[0]
    elif role == "moderate":
        # 2026-08-13(세션31 신설) -- feasible은 lut._idu_scan()이 gm_id_grid 순서(오름차순)
        # 그대로 스캔한 결과라 이미 정렬돼 있다(위 "balanced"가 feasible[0]을 그대로
        # 쓰는 것과 같은 전제) -- 중앙 인덱스가 정확히 "이 feasible 구간의 gm/ID 중앙값"이
        # 되도록 별도 정렬 불필요.
        best_gm_id = feasible[len(feasible) // 2]
    elif role == "gain":
        best_gm_id, best_ratio = None, -1.0
        for gm_id in feasible:
            ratio = lut.gm_gds_ratio(gm_id, L, vds, vs)
            if ratio > best_ratio:
                best_ratio, best_gm_id = ratio, gm_id
    elif role == "load":
        # 2026-08-19(세션37 연속) -- "gain"과 대칭적인 형태(feasible 전체를 스캔해 최댓값을
        # 찾음)지만 최대화 대상이 gm/gds가 아니라 ro(=1/gds) 자체다. gds = gm_id*ID_target/
        # gm_gds_ratio로 역산(별도 gds() 접근자가 LUT에 없어 이미 있는 gm_gds_ratio()를
        # 재사용 -- gm=gm_id*ID_target 정의 그대로).
        best_gm_id, best_ro = None, -1.0
        for gm_id in feasible:
            ratio = lut.gm_gds_ratio(gm_id, L, vds, vs)
            gds = gm_id * ID_target / ratio
            ro = 1.0 / gds
            if ro > best_ro:
                best_ro, best_gm_id = ro, gm_id
    else:
        raise ValueError(f"알 수 없는 role: {role!r} -- "
                          f"'matching'/'gain'/'balanced'/'moderate'/'load' 중 하나여야 한다")
    return (best_gm_id, idu_by_gm_id[best_gm_id]) if return_idu else best_gm_id


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
    `propagate_topology_forced_currents()`(A엔진)에 그대로 전달할 입력이다.
    `topology_path`(세션21 신설) — `optimize_full_circuit_budget()`이 자신이 받은
    `topology_path`를 그대로 채워둔다. `_metric_smallsignal_*()`(topology-무관 수치 MNA
    metric)류가 connectivity를 읽어야 할 때 이걸로 `load_topology()`를 호출한다 — F엔진의
    다른 metric들처럼 `ctx.sized`만 읽는 순수 계산기가 아니라 유일하게 connectivity가
    필요한 예외이므로, 필요한 최소한(경로 문자열 하나)만 ctx에 얹었다.

    `kind_of`(세션22 신설) — `{device_name: "nmos"|"pmos"}`, `optimize_full_circuit_
    budget()`이 자신이 이미 알고 있는 kind 매핑을 그대로 채워둔다. `_feed_metric_stage_
    budget()`/`_feed_gm_target_convention()`/`_metric_flicker_plus_thermal_sum()`처럼
    LUT에서 소자를 직접 사이징/평가하는 함수가 `ctx.spec["lut"]`(단일 LUT) 대신
    `ctx.spec["lut_by_kind"][ctx.kind_of[name]]`로 소자별 정확한 kind의 LUT을 쓰기 위한
    것 — 세션22 실측: `L_cascode`(devices=M2a/M2b/M3a/M3b, PMOS+NMOS 혼합)가 지금껏
    단일(nmos) LUT으로 PMOS 소자까지 사이징하고 있었다(전기적으로 틀린 결과, `.ai/
    context.md` 세션22 참고). ⚠️ kind을 구분 안 하는 단일 LUT 사이징은 실제 회로에서
    정당화될 상황이 없다(사용자 지적, 세션22) — 그래서 `kind_of`/`lut_by_kind`가 없을 때
    조용히 `ctx.spec["lut"]`로 폴백하지 않고, 위 세 함수 전부 `KeyError`를 그대로
    전파한다(호출자가 `kind_of`/`lut_by_kind`를 안 채운 게 드러나야 한다). self-test
    fixture도 전부 `kind_of`+`lut_by_kind`를 채우도록 갱신했다(§ self-test 참고)."""
    sized: dict = field(default_factory=dict)
    spec: dict = field(default_factory=dict)
    derived: dict = field(default_factory=dict)
    seed_currents: dict = field(default_factory=dict)
    mirror_ratios: dict = field(default_factory=dict)
    topology_path: str = ""
    kind_of: dict = field(default_factory=dict)
    # 2026-08-13(세션31 감사 발견) -- `_telescopic_class_ab_open_loop_gains()`가 매번 31노드
    # MNA 4개(Adm/Acm/Ann/H)를 새로 푸는데, `_cmrr_telescopic_class_ab_cmfb()`와 `_psrr_
    # telescopic_class_ab_cmfb()`가 (완전히 동일한 metric_spec으로) 각자 독립 호출해 한
    # 세타평가당 8개를 풀고 있었다(각자 절반은 `del`로 바로 버림). 이 ctx는 한 세타평가
    # 동안만 살아있는 일회용 객체라 여기 캐시해도 이전 세타점 결과가 새는 위험이 없다.
    _open_loop_gains_cache: dict = field(default_factory=dict)
    # 2026-08-19(세션37) -- `_nmcnr_predict()`(nmcnr_amplifier의 gain_db/pm_deg가 공유)가
    # `nmcnr_predict_ac_response()`(4-노드 KCL, 2000점 주파수 스윕) 결과를 캐싱 -- 위 `_open_loop_
    # gains_cache`와 동일한 이유(gain_db/pm_deg 두 metric이 같은 세타평가에서 완전히 동일한
    # 입력으로 각자 호출하므로 캐시 없인 스윕을 2번 돈다), 다만 반환 dict 구조가 달라 별도 필드로 분리.
    _nmcnr_predict_cache: dict = field(default_factory=dict)


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


def _folded_cascode_rout(spec: dict, ctx: SizingContext) -> tuple:
    """`folded_cascode` 계열 단일 스테이지의 출력저항(표준 캐스코드 폐형식, 2026-08-15
    세션35 신설) -- `_metric_folded_cascode_gain_db`/`_metric_folded_cascode_pm_deg`가
    공유하는 헬퍼(중복 방지). Rout_p(PMOS 캐스코드 branch) = gm(cascode_p)·ro(cascode_p)·
    (ro(fold_leg_a)‖ro(fold_leg_b)) -- 폴딩 노드(예: X)에 diffpair 다리와 PMOS 전류원이
    같이 물려 그 둘의 ro가 병렬로 캐스코드 소스단 임피던스를 이룬다. Rout_n(NMOS 캐스코드
    branch, 미러를 거쳐 출력에 실림) = gm(cascode_n)·ro(cascode_n)·ro(mirror_n) -- 이쪽은
    diode+미러 체인이라 병렬 항 없이 단일 ro. 반환: `(Rout_p, Rout_n, Rout_p‖Rout_n)`.

    metric_spec 키: `{"cascode_p","fold_leg_a","fold_leg_b","cascode_n","mirror_n"}`
    (예: folded_cascode.topology.json -- cascode_p=M6, fold_leg_a=M1, fold_leg_b=M3,
    cascode_n=M8, mirror_n=M10)."""
    def ro(name):
        return 1.0 / ctx.sized[name]["gds"]
    ro_fold = 1.0 / (1.0 / ro(spec["fold_leg_a"]) + 1.0 / ro(spec["fold_leg_b"]))
    rout_p = ctx.sized[spec["cascode_p"]]["gm"] * ro(spec["cascode_p"]) * ro_fold
    rout_n = ctx.sized[spec["cascode_n"]]["gm"] * ro(spec["cascode_n"]) * ro(spec["mirror_n"])
    rout = 1.0 / (1.0 / rout_p + 1.0 / rout_n)
    return rout_p, rout_n, rout


def _metric_folded_cascode_gain_db(spec: dict, ctx: SizingContext) -> float:
    """F엔진(2026-08-15 세션35 신설) -- 단일 스테이지 folded-cascode의 DC 이득 표준 폐형식
    (문헌 표준: Razavi *Design of Analog CMOS Integrated Circuits* 등이 공통으로 주는
    `Adm = gm1·(Rout_p‖Rout_n)` 형태 -- diffpair 한쪽 다리의 gm과 병렬 출력저항의 곱).
    이 프로젝트의 다른 CMRR/PSRR 폐형식(예: `_cmrr_telescopic_class_ab`)과 달리 sympy
    전수 유도·ngspice 교차검증은 아직 안 했다(2026-08-15 세션35, 사용자 승인 범위 --
    "gain은 잘 알려진 표준식이라 유도 리스크가 낮다"는 전제로 우선 등록, 최종 확인은
    SPICE가 필요하다는 이 프로젝트의 일반 원칙 그대로 적용).

    metric_spec 키: `_folded_cascode_rout()`와 동일 + `"gm1_device"`(예: M1 -- diffpair
    한쪽 다리, matching 선언으로 M2와 gm이 같다고 전제)."""
    gm1 = ctx.sized[spec["gm1_device"]]["gm"]
    _, _, rout = _folded_cascode_rout(spec, ctx)
    return 20 * math.log10(abs(gm1 * rout))


def _metric_folded_cascode_pm_deg(spec: dict, ctx: SizingContext) -> float:
    """F엔진(2026-08-15 세션35 신설) -- 단일 스테이지 folded-cascode의 위상여유, 2-pole
    근사(`PM = 90도 - atan(GBW/p2)`, 표준 형태). 지배극은 출력(`p1 = 1/(2π·Rout·CL)`),
    GBW = gm1/(2π·CL) = Adm·p1. 2차극은 폴딩 노드(예: X)의 국소 임피던스(≈1/gm(cascode_p),
    캐스코드 소스단이 낮은 임피던스를 만드는 표준 근사)와 그 노드의 기생 커패시턴스로
    추정: `p2 = gm(cascode_p) / (2π·C_fold)`.

    ⚠️ **정직한 한계**(`_psrr_telescopic_class_ab`류와 같은 투명성 원칙): (1) `C_fold`는
    폴딩 노드에 물린 소자들의 `cgg_absolute()`(게이트 커패시턴스) 합으로 근사한다 -- 이
    프로젝트 LUT가 drain/source 접합 커패시턴스(Cdb/Csb) 모델을 갖고 있지 않아서 쓰는
    대체 근사이지 그 노드의 진짜 지배 성분(주로 Cdb/Csb)을 직접 모델링한 것이 아니다.
    (2) Y-branch(M5-M7-M9-M10 캐스코드 체인)에 있는 추가 극(Vg7/Vg9/Vg10)은 모델링하지
    않는다 -- X-branch 2차극 하나만 지배적이라고 가정한다(단일 스테이지 folded cascode가
    일반적으로 PM이 90도에 가깝다는 사실과 부합하는 근사). 정확한 값은 SPICE AC 시뮬레이션
    필요.

    metric_spec 키: `_folded_cascode_rout()`와 동일 + `"gm1_device"`, `"CL"`(부하 커패시턴스,
    F 단위), `"fold_cap_devices"`(폴딩 노드 기생캡을 근사할 소자 목록, 예: [M1,M3,M6])."""
    gm1 = ctx.sized[spec["gm1_device"]]["gm"]
    _, _, rout = _folded_cascode_rout(spec, ctx)
    CL = spec["CL"]
    gbw_hz = gm1 / (2 * math.pi * CL)
    c_fold = 0.0
    for name in spec["fold_cap_devices"]:
        e = ctx.sized[name]
        lut = ctx.spec["lut_by_kind"][ctx.kind_of[name]]
        c_fold += lut.cgg_absolute(e["gm_id"], e["L"], e["vds"], e.get("vs", 0.0), e["W"])
    p2_hz = ctx.sized[spec["cascode_p"]]["gm"] / (2 * math.pi * c_fold)
    return 90.0 - math.degrees(math.atan(gbw_hz / p2_hz))


def _nmcnr_stage1_rout(spec: dict, ctx: SizingContext) -> float:
    """`nmcnr_amplifier` stage1(폴디드 캐스코드)의 출력저항 폐형식(2026-08-19 세션37 신설,
    `.ai/context.md` 세션36 §4-① 이어감). NodeM2(=gm2 소자의 게이트가 받는 stage1 출력)에는
    NMOS 캐스코드(`stage1_cascode_n`, 예 M107)와 캐스코드 없는 단순 PMOS 전류원
    (`stage1_mirror_p`, 예 M109) 두 branch가 만난다 — `_folded_cascode_rout()`와 달리
    **한쪽만 캐스코드인 비대칭 구조**(PMOS 쪽은 다이오드(M108) 미러로만 전류가 정해지는
    단순 전류원, 자체 캐스코드 트랜지스터가 없음)라 그 헬퍼를 재사용할 수 없어 새로 유도했다.

    Rout_n(NMOS 캐스코드 branch) = gm(cascode_n)·ro(cascode_n)·(ro(fold_leg_a)‖ro(fold_leg_b))
    — 폴딩 노드(NodeF2)에 diffpair 다리(`stage1_fold_leg_a`, 예 M103)와 NMOS 전류원
    (`stage1_fold_leg_b`, 예 M105)이 같이 물려 그 둘의 ro가 병렬로 캐스코드 소스단 임피던스를
    이룬다(`_folded_cascode_rout()`의 Rout_p 유도와 동일 원리, NMOS/PMOS만 반대).
    Rout_p(PMOS mirror branch) = ro(mirror_p) — 캐스코드가 없어 자기 ro뿐.

    metric_spec 키: `"stage1_cascode_n"`, `"stage1_fold_leg_a"`, `"stage1_fold_leg_b"`,
    `"stage1_mirror_p"`."""
    def ro(name):
        return 1.0 / ctx.sized[name]["gds"]
    ro_fold = 1.0 / (1.0 / ro(spec["stage1_fold_leg_a"]) + 1.0 / ro(spec["stage1_fold_leg_b"]))
    cascode_n = spec["stage1_cascode_n"]
    rout_n = ctx.sized[cascode_n]["gm"] * ro(cascode_n) * ro_fold
    rout_p = ro(spec["stage1_mirror_p"])
    return 1.0 / (1.0 / rout_n + 1.0 / rout_p)


def _nmcnr_predict(spec: dict, ctx: SizingContext) -> dict:
    """`nmcnr_amplifier`(3단 NMCNR) F엔진(2026-08-19 세션37 신설) — `topology_library.
    nmcnr_predict_ac_response()`(4-노드 KCL 정확해, sympy 유도 + ngspice/실트랜지스터 재조립
    교차검증까지 이미 완료된 함수, `.ai/context.md` 세션 2026-07-31 참고)를 이 회로의
    **실사이징값**으로 호출하는 공유 헬퍼 — `_metric_nmcnr_gain_db`/`_metric_nmcnr_pm_deg`가
    같은 세타평가에서 동일 입력으로 각자 호출하므로 `ctx._nmcnr_predict_cache`로 캐싱한다
    (`_telescopic_class_ab_open_loop_gains()`와 동일 이유·동일 캐시 키 관례).

    ⚠️ 이 함수가 나오기 전까지 `nmcnr_predict_ac_response()`는 `topology_library.py` `__main__`의
    스모크테스트(손으로 옮긴 논문 실측 gain/gm 조합)로만 쓰였고 실제 사이징 파이프라인에
    배선된 적이 없었다 — ★절대원칙★(만들면 반드시 배선) 그대로 이번에 처음 metrics 엔진에
    배선한다.

    gm1/gm2/gm3와 R1/R2/R3 전부 **실사이징 실측값**(`ctx.sized`)만 쓴다 — compensation이
    산출한 "목표" gm이 아니라 실제로 gm_id 격자탐색을 거쳐 확정된 값이다. `nmcnr_compensation_
    elements()`가 이 gm1/gm2/gm3로 Cm1/Rm/Cm2를 다시 계산하므로, "이 사이징대로 실제로
    보상망을 만들면 Cm1/Rm/Cm2도 이 실측 gm 기준으로 정해질 것"이라는 물리적으로 일관된
    as-built 해석을 택했다(스모크테스트의 목표-gm 방식과 다른 선택, 정직하게 기록).
    gm2/gm3는 `compensation.stage_devices`가 가리키는 소자(예 M201/M301) 자신의 gm을 그대로
    쓴다 — M201→M203(다이오드)/M204(미러) 릴레이는 matching_pairs가 current_forced+동일
    gm_id_role="matching"을 선언해 1:1 전류미러(gm204≈gm203)를 보장하므로 이 릴레이가 gm2를
    감쇠/증폭하지 않는다고 전제한다(compensation.stage_devices=[M201] 자체가 이미 이 전제
    위에서 M201만 gm2 결정 소자로 지정해뒀다).

    R1(stage1, NodeM2)은 `_nmcnr_stage1_rout()`, R2(stage2, NodeS2)/R3(stage3, Vout)는 양쪽
    다 캐스코드 없는 단순 병렬 ro(`stage2_devices`/`stage3_devices` 두 소자의 ro‖ro).

    metric_spec 키: `"gm1_device"`, `"gm2_device"`, `"gm3_device"`, `_nmcnr_stage1_rout()`와
    동일 4개(`stage1_cascode_n`/`stage1_fold_leg_a`/`stage1_fold_leg_b`/`stage1_mirror_p`),
    `"stage2_devices"`(2개 리스트), `"stage3_devices"`(2개 리스트), `"CL"`, `"kg"`."""
    def ro(name):
        return 1.0 / ctx.sized[name]["gds"]
    footprint = sorted({spec["gm1_device"], spec["gm2_device"], spec["gm3_device"],
                         spec["stage1_cascode_n"], spec["stage1_fold_leg_a"],
                         spec["stage1_fold_leg_b"], spec["stage1_mirror_p"],
                         *spec["stage2_devices"], *spec["stage3_devices"]})
    key = (_hashable_key(spec),
           tuple((n, ctx.sized[n]["gm"], ctx.sized[n]["gds"]) for n in footprint))
    cached = ctx._nmcnr_predict_cache.get(key)
    if cached is not None:
        return cached
    gm1 = ctx.sized[spec["gm1_device"]]["gm"]
    gm2 = ctx.sized[spec["gm2_device"]]["gm"]
    gm3 = ctx.sized[spec["gm3_device"]]["gm"]
    R1 = _nmcnr_stage1_rout(spec, ctx)
    s2a, s2b = spec["stage2_devices"]
    R2 = 1.0 / (1.0 / ro(s2a) + 1.0 / ro(s2b))
    s3a, s3b = spec["stage3_devices"]
    R3 = 1.0 / (1.0 / ro(s3a) + 1.0 / ro(s3b))
    result = nmcnr_predict_ac_response(gm1, gm2, gm3, R1, R2, R3, CL=spec["CL"], kg=spec["kg"])
    ctx._nmcnr_predict_cache[key] = result
    return result


def _metric_nmcnr_gain_db(spec: dict, ctx: SizingContext) -> float:
    """F엔진(2026-08-19 세션37 신설) — `nmcnr_amplifier`의 DC 이득, `_nmcnr_predict()`의
    `dc_gain_db`(4-노드 KCL 정확해) 그대로. notch(복수 0dB 교차) 여부와 무관하게 DC 이득
    자체는 항상 잘 정의된 값이라 그대로 반환한다."""
    return _nmcnr_predict(spec, ctx)["dc_gain_db"]


def _metric_nmcnr_pm_deg(spec: dict, ctx: SizingContext) -> float:
    """F엔진(2026-08-19 세션37 신설) — `nmcnr_amplifier`의 위상여유, `_nmcnr_predict()`의
    첫(최저주파) 0dB 교차 지점 PM. ⚠️ **정직한 한계**: 0dB 교차가 아예 없으면(예: DC 이득이
    이미 0dB 미만) `ValueError` — PM이 정의 불가능한 상태를 조용히 넘기지 않는다. 교차가
    2개 이상(`notch=True`)이면 "위상여유"라는 단일 숫자로 이 회로를 대표하는 것 자체가
    오도할 수 있어(`nmcnr_predict_ac_response()` docstring 참고) 마찬가지로 `ValueError` — 이
    경우 `crossings` 전체 리스트를 직접 확인해야 한다."""
    result = _nmcnr_predict(spec, ctx)
    crossings = result["crossings"]
    if not crossings:
        raise ValueError("nmcnr_pm_deg: 0dB 교차가 없다 -- DC 이득이 이미 0dB 미만이거나 "
                          f"위상여유가 정의되지 않는 상태다(dc_gain_db={result['dc_gain_db']:.2f}dB)")
    if result["notch"]:
        raise ValueError(
            f"nmcnr_pm_deg: 0dB 교차가 {len(crossings)}개(notch=True)라 PM 하나로 대표할 수 "
            f"없다 -- crossings={crossings} 를 직접 확인할 것")
    return crossings[0][1]


def _metric_flicker_plus_thermal_sum(spec: dict, ctx: SizingContext) -> float:
    """F엔진(배치 7-3g, 2026-07-31) — `stages`(`[[dev,...], ...]`)의 입력환산 열+1/f 잡음
    밀도를 RMS 합산(독립 잡음원 가정)해 V/√Hz로 반환. 소자별 `ctx.spec["lut_by_kind"]
    [ctx.kind_of[name]]`(세션22부터, kind 구분 없는 단일 LUT은 stages가 NMOS/PMOS를 섞을 때
    틀린 결과를 준다 — M1a/M4a처럼 실제로 섞여 있음)가 `noise_1f_density()`(SID_1F 필요)를
    지원해야 한다 — 지원 안 하면 `ValueError`가 그대로 전파된다(조용히 스킵하지 않음).
    `ctx.spec`의 선택 키: `"gamma"`(기본 2/3, 열잡음 계수), `"temperature_K"`(기본 300),
    `"freq"`(기본 1.0Hz)."""
    gamma = ctx.spec.get("gamma", 2.0 / 3.0)
    freq = ctx.spec.get("freq", 1.0)
    kT = 1.380649e-23 * ctx.spec.get("temperature_K", 300.0)
    total_variance = 0.0
    for stage in spec["stages"]:
        for name in stage:
            e = ctx.sized[name]
            lut = ctx.spec["lut_by_kind"][ctx.kind_of[name]]
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


def _metric_rail_referenced_voltage(spec: dict, ctx: SizingContext) -> float:
    """F엔진(2026-08 세션6) — `device`(이미 사이징 완료, gm_id/L/vds/vs/kind 확정)의
    게이트가 실제로 도달하는 DC 레벨을 LUT VGS 역산(`vgs_for_gm_id()`)으로 계산한다.
    `device`의 **source가 `rail`("vdd" 또는 "gnd")에 물려 있다는 전제**(호출자가 그 조건을
    만족하는 소자만 넘길 것 -- 이 함수는 그 전제를 검증하지 않는다) -- pmos는 게이트가
    source보다 낮아야 동작하므로 `rail - VGS`, nmos는 `rail + VGS`.

    class-AB 2단(Monticelli류 floating battery, M9a/M9b가 Vg15/Vop1 사이에 거는 레벨시프트)의
    출력게이트 DC 레벨이 논문 설계 의도(Xie&Chen Section II.B: "the gate voltage of M15 is
    pushed to about 1.3V and ... M16 ... about 0.5V")와 같은 방향인지 검증하려고 신설.
    ⚠️ 절대 레벨 자체를 이 프로젝트의 목표값으로 강제하지 않는다(그 수치는 논문 공정의
    Vth에 종속 -- `feedback_no_paper_values_derive_rationally` 원칙) -- 대신
    `_metric_battery_centering_deviation()`이 "두 레벨의 합이 VDD와 같아야 한다"는
    위상적 관계만 재사용한다."""
    entry = ctx.sized[spec["device"]]
    lut = ctx.spec["lut_by_kind"][entry["kind"]]
    vgs = lut.vgs_for_gm_id(entry["gm_id"], entry["L"], entry["vds"], entry.get("vs", 0.0))
    rail_v = ctx.spec["vdd"] if spec["rail"] == "vdd" else 0.0
    return rail_v - vgs if entry["kind"] == "pmos" else rail_v + vgs


def _metric_battery_centering_deviation(spec: dict, ctx: SizingContext) -> float:
    """F엔진(2026-08 세션6) — class-AB 2단 floating battery(M9a/M9b류)가 두 출력게이트
    노드(`high_device`=pmos·source=vdd, `low_device`=nmos·source=gnd)를 VDD 기준으로 얼마나
    센터링하는지 검증. 두 소자의 실제 DC 레벨 합이 `vdd`에서 벗어난 절대값(V)을 반환 -- 0에
    가까울수록 두 게이트 레벨의 평균이 VDD/2에 있다는 뜻(swing 최대화에 유리, "amp는 DC
    bias가 VDD 기준 center일 때 swing이 최대가 될 수 있다"는 원리 그대로).

    이 관계의 근거는 Xie&Chen Section II.B(Fig.1 M15/M16, 이 topology의 M15/M16과 동일
    역할): "the gate voltage of M15 is pushed to about 1.3V and ... M16 ... about 0.5V" --
    1.3+0.5=1.8V=VDD로 정확히 센터링돼 있다. **절대 수치(1.3V/0.5V)는 그 논문 공정의 Vth에
    종속이라 그대로 안 가져오고(값 인용 금지 원칙), "합=VDD" 위상적 관계만 우리 sky130
    재설계에 가져온다.**

    ⚠️ 이 관계가 M9a-chain(M11a/M11b/M12)과 M9b-chain(M13/M14a/M14b)의 전류를 같게
    만들어서 달성되는 게 아니다 -- M15/M16 자신의 gm_id/L/VDS(compensation이 이미 확정)로
    직접 계산한다(2026-08 세션6, 사용자가 제안한 "두 chain 전류를 같게" 가설을 검토하다
    발견: M9a 자신의 전류는 K_replica(M9a~M15 면적비)로, M9b는 kcl_battery_M9b(=ID(M11a-chain)
    +ID(M9a))로 결정되고, M13-chain 전류는 이 KCL 어디에도 안 들어간다 -- 논문 Fig.7b가
    두 chain의 quiescent ID가 다르다고 이미 실측 확인한 것과도 일치)."""
    high = _metric_rail_referenced_voltage(
        {"device": spec["high_device"], "rail": "vdd"}, ctx)
    low = _metric_rail_referenced_voltage(
        {"device": spec["low_device"], "rail": "gnd"}, ctx)
    return abs((high + low) - ctx.spec["vdd"])


def _cmrr_diff_pair_tail(metric_spec: dict, ctx: SizingContext) -> float:
    """`circuit_family="diff_pair_tail"` — CMRR ≈ [(ro_tail/2) + (1/gm_tail)]·gm_tail
    (문헌 표준 1차 근사, do.md 배치 7-3i). `tail_device`의 이미 사이징된 gm/gds만 쓴다."""
    tail = ctx.sized[metric_spec["tail_device"]]
    ro_tail = 1.0 / tail["gds"]
    cmrr_linear = (ro_tail / 2.0 + 1.0 / tail["gm"]) * tail["gm"]
    return 20 * math.log10(cmrr_linear)


def _cmrr_telescopic_class_ab(metric_spec: dict, ctx: SizingContext) -> float:
    """`circuit_family="telescopic_class_ab"` — current-reuse telescopic 1단(Xie&Chen
    논문 Fig.2, current_reuse_telescopic_ota)의 **open-loop**(CMFB 루프 제외) CMRR.
    논문 자체엔 CMRR 폐형식이 없어서(시뮬레이션 수치 94.4dB만 보고) 2026-07-31에 처음
    유도했고, **2026-08-03에 확정된 topology.json으로 처음부터 재유도**했다
    (`workspaces/current-reuse-telescopic-ota-report/spice/stage1_cmrr_sympy_derivation.py`
    = sympy 정확해, `.../stage1_cmrr_ngspice_crosscheck.py` = ngspice AC 교차검증).

    **위상(topology.json이 유일한 소스, load_topology()로 확인 -- self-test가 강제)**::

        vdd ─ M6∥M7(tail, Rx) ─ Vx ─ M1a(입력,gate=Vip) ─ N1a2a ─ M2a(캐스코드) ─┐
                                                                                Vom1
        gnd ─ M5(tail, Ry) ───── Vy ─ M4a(입력,gate=Vip) ─ N3a4a ─ M3a(캐스코드) ─┘

    즉 PMOS 경로(M1a→M2a)와 NMOS 경로(M4a→M3a)는 **각각 독립된 tail(Vx/Vy)에서 출발한
    별개의 캐스코드 가지**이고, 출력노드 Vom1에서 **드레인끼리 만난다**(current-reuse).
    ⚠️ `M2a.drain == M3a.source`인 **직렬 텔레스코픽 기둥이 아니다** -- 2026-08-03 이전
    self-test의 assert가 바로 그 옛 가정을 검사하고 있었고(그래서 확정 JSON에서 실패했다),
    지금은 `M1a.drain == M2a.source`(PMOS 직렬 캐스코드), `M4a.drain == M3a.source`
    (NMOS 직렬 캐스코드), `M2a.drain == M3a.drain == Vom1`(드레인 합류)을 검사한다.

    **유도**(sympy, 위 위상으로 자동 조립한 MNA 정확해의 gm·ro≫1 leading order --
    아래 두 식은 정확해의 leading order와 **기호적으로 동일**함을 확인했다)::

        Kp' = gm(M2a)·ro(M1a)·ro(M2a)      # PMOS 가지가 Vom1에서 보이는 캐스코드 임피던스
        Kn' = gm(M3a)·ro(M4a)·ro(M3a)      # NMOS 가지 쪽
        Kp  = gm(M1a)·Kp' ,  Kn = gm(M4a)·Kn'
        Rx  = 1/Σgds(tail_p_devices) ,  Ry = 1/gds(tail_n_device)

        Adm = (gm(M1a)+gm(M4a)) · (Kp' ∥ Kn')
        Acm = (Rx+Ry)·Kp·Kn / (Kn·Ry + Kp·Rx)          (부호는 음수, 크기만 씀)
        CMRR = 20·log10(Adm/Acm)

    Acm 식의 의미: CM에서 두 가지는 각각 tail로 소스축퇴돼 CM 전달컨덕턴스가 1/(2Rx),
    1/(2Ry)로 **바닥이 정해지고**, 출력임피던스는 2Kp·Rx, 2Kn·Ry로 부스팅된다. 두 가지가
    Vom1에서 병렬로 만나므로 **한쪽 tail 임피던스만 키워도 CMRR이 무한정 좋아지지 않고
    다른 쪽 가지가 만드는 바닥(floor)에 수렴**한다(단순 `diff_pair_tail`의 "gm·R_tail"
    직관과 다름). 실제로 이 open-loop CMRR은 물리적 범위에서 수 dB를 넘지 못한다 --
    논문의 94.4dB를 설명하는 건 CMFB 루프이고, 그건 `telescopic_class_ab_cmfb` family다.

    ⚠️ **2026-08-03 정정 2건**:
    (1) 위상 assert(위 참조).
    (2) 캐스코드 부스팅 계수에 옛 식은 **입력쌍의 gm**(gm(M1a)/gm(M4a))을 썼으나, 정확한
        노드해석 결과 들어가야 하는 것은 **캐스코드 소자의 gm**(gm(M2a)/gm(M3a))이다
        (`Kp' = gm(M2a)/(gds(M1a)·gds(M2a))`). 옛 SPICE 대조가 모든 gm을 119µS로 같게
        놓고 이뤄져서 이 차이가 드러나지 않았다. `telescopic_class_ab_cmfb`(2026-08-03)는
        이미 캐스코드 gm을 쓰고 있었으므로 이 함수만 어긋나 있었다 -- 이제 두 family가
        같은 Kp'/Kn' 정의를 쓴다. ngspice 실측 대조(파라미터 ±4배 랜덤 20점):
        새 식 최대오차 **0.80dB**, 옛(입력 gm) 식 최대오차 **11.95dB**.

    정확도: 위 leading order는 SPICE 정확해 대비 ±4배 랜덤 스윕 전 구간에서 최대 0.8dB
    (전형 0.1dB) -- 탐색용으로는 충분하나 최종 확인은 SPICE AC 시뮬레이션 권장.

    metric_spec 키: `input_p`/`cascode_p`(PMOS 입력쌍 M1a·PMOS 캐스코드 M2a),
    `input_n`/`cascode_n`(NMOS 입력쌍 M4a·NMOS 캐스코드 M3a), `tail_p_devices`
    (PMOS tail 전류원 목록, 예 [M6,M7] -- gds 병렬합), `tail_n_device`(NMOS tail, 예 M5).
    ⚠️ `cascode_p`/`cascode_n`은 이제 `gds`뿐 아니라 **`gm`도** 필요하다(정정 2)."""
    gmp = ctx.sized[metric_spec["input_p"]]["gm"]
    rop1 = 1.0 / ctx.sized[metric_spec["input_p"]]["gds"]
    gmcp = ctx.sized[metric_spec["cascode_p"]]["gm"]
    rop2 = 1.0 / ctx.sized[metric_spec["cascode_p"]]["gds"]
    gmn = ctx.sized[metric_spec["input_n"]]["gm"]
    ron1 = 1.0 / ctx.sized[metric_spec["input_n"]]["gds"]
    gmcn = ctx.sized[metric_spec["cascode_n"]]["gm"]
    ron2 = 1.0 / ctx.sized[metric_spec["cascode_n"]]["gds"]
    gds_tail_p = sum(ctx.sized[d]["gds"] for d in metric_spec["tail_p_devices"])
    Rx = 1.0 / gds_tail_p
    Ry = 1.0 / ctx.sized[metric_spec["tail_n_device"]]["gds"]

    # 캐스코드 부스팅 계수 = **캐스코드 소자**의 gm x 두 ro의 곱(입력쌍 gm이 아니다).
    Kp_prime = gmcp * rop1 * rop2   # PMOS 가지(M1a-M2a)가 Vom1에서 보이는 출력임피던스
    Kn_prime = gmcn * ron1 * ron2   # NMOS 가지(M4a-M3a) 쪽
    R_out = Kp_prime * Kn_prime / (Kp_prime + Kn_prime)   # 드레인끼리 만나므로 '병렬'
    Adm = (gmp + gmn) * R_out

    Kp = gmp * Kp_prime
    Kn = gmn * Kn_prime
    Acm = Kn * Kp * (Rx + Ry) / (Kn * Ry + Kp * Rx)

    return 20 * math.log10(Adm / Acm)


def _cmfb_amp_gain_diode_load(metric_spec: dict, ctx: SizingContext) -> float:
    """`telescopic_class_ab_cmfb`의 부품: CMFB 에러앰프(Xie&Chen Fig.5)의 소신호 이득
    `A_c = v(Vcmfb)/v(Voc)`. **근사 없는 정확해**(sympy 정확해와 기호적으로 동일함을 확인,
    2026-08-03 배치 7-5c).

    **회로**(topology.json `_correction_log_5`, PDF 벡터 좌표로 확정): M37a(gate=Voc)/
    M37b(gate=Voc_des)가 M38 tail을 공유하는 NMOS 차동쌍이고, **양쪽 부하가 서로 무관한
    독립 PMOS diode**다(M36a는 M37a 쪽, M36b는 M37b 쪽 -- 두 게이트는 연결돼 있지 않다).
    출력 `Vcmfb`는 M36a의 diode 노드 그 자체(=M37a.drain)에서 single-ended로 뽑는다.

    ⚠️ **이전 버전(`_cmfb_amp_gain_5t_replica`, 커밋 b63e394)은 폐기됐다**: 그 함수는
    M36a/M36b를 current mirror로, M39/M40이 만드는 Voc_des를 고임피던스 replica 노드로
    가정했으나 둘 다 오독이었다. 실제로는 M39/M40이 **PMOS diode 2개짜리 저임피던스
    분압기**(VDD-M39-Voc_des-M40-GND)라 소신호로 `v(Voc_des) = 0`이다(sympy 정확해로 확인:
    노드 Voc_des의 자기 컨덕턴스가 gm39+gds39+gm40+gds40이고 구동원이 없다). 즉 **M39/M40은
    이 이득식에 아예 등장하지 않는다** -- 이전 유도의 'Voc_des가 Voc를 따라가 gm37이 소거된다'
    는 서술도 함께 폐기.

    **유도**: 노드 3개(Vcmfb=vc, N36b=vb, Ncmfb_tail=vt) KCL. `a=gm36a+gds36a`,
    `b=gm36b+gds36b`로 두면 diode 부하가 각각 `a`, `b`의 컨덕턴스로 접지에 매달리고
    ```
      vc·(a+gds37a) = (gm37a+gds37a)·vt − gm37a·voc          (Vcmfb KCL)
      vb·(b+gds37b) = (gm37b+gds37b)·vt                      (N36b KCL)
      a·vc + b·vb + gds38·vt = 0                             (세 식의 합 = tail KCL)
    ```
    를 vt에 대해 풀면 아래 폐형식이 된다. leading order(모든 gds→0):
    `A_c → −gm37a·gm37b / (gm36a·(gm37a+gm37b))`, 즉 gm37a≈gm37b면 **−gm37/(2·gm36)**
    (다이오드 부하 차동쌍의 교과서 결과 그대로). 이전 식과 달리 두 O(gds) 항의 차가
    아니라서 수치적으로 안정하다(정확해 대비 leading order 오차 ~2%, 실측).

    ⚠️ **부호**: 정상 동작에서 `A_c < 0`이다(Voc가 오르면 M37a가 더 흘려 diode 노드 Vcmfb가
    내려간다). 이건 고장이 아니라 이 회로의 정상 부호다 -- CM 루프의 음귀환 여부는 A_c
    혼자가 아니라 `A_c · H · G2`(2단 CM 이득 포함) 전체 부호가 정한다(호출자가 판단)."""
    def g(role, key):
        return ctx.sized[metric_spec[role]][key]

    gm36a, gds36a = g("cmfb_load_sense", "gm"), g("cmfb_load_sense", "gds")
    gm36b, gds36b = g("cmfb_load_ref", "gm"), g("cmfb_load_ref", "gds")
    gm37a, gds37a = g("cmfb_amp_sense", "gm"), g("cmfb_amp_sense", "gds")
    gm37b, gds37b = g("cmfb_amp_ref", "gm"), g("cmfb_amp_ref", "gds")
    gds38 = g("cmfb_tail_device", "gds")

    a = gm36a + gds36a      # Vcmfb 노드에 매달린 M36a diode 컨덕턴스
    b = gm36b + gds36b      # N36b 노드에 매달린 M36b diode 컨덕턴스
    A1 = a * (gm37a + gds37a) / (a + gds37a)
    A0 = a * gm37a / (a + gds37a)
    B1 = b * (gm37b + gds37b) / (b + gds37b)
    vt = A0 / (A1 + B1 + gds38)                      # v(Voc)=1 기준 tail 전위
    return ((gm37a + gds37a) * vt - gm37a) / (a + gds37a)


def _mna_solve_smallsignal(devices: list, unknown_nodes: list, fixed: dict) -> dict:
    """소신호 MNA를 순수 Python Gaussian elimination(부분피벗)으로 정확히 푼다(세션21 신설).

    `devices`: `[(drain, source, gate, gm, gds), ...]` — `I(drain->source) = gm*(vg-vs) +
    gds*(vd-vs)`(pmos/nmos 부호는 gm/gds 자체에 이미 흡수돼 있다, 기존 sympy 유도 스크립트의
    `build_mna()`와 동일 소자모델). `unknown_nodes`: 풀 노드 이름 리스트. `fixed`: AC
    ground(0.0)/독립원(vip/vim/vdd/Vcmfb 등)의 고정 전위값 — `unknown_nodes`에 없는 모든
    노드는 여기서 조회하고 없으면 0.0(AC ground)으로 취급한다.

    ⚠️ **왜 폐형식이 아니라 수치인가**(세션21 근거, `.ai/context.md` 참고): M10/M19(class-AB
    바이어스 싱크)를 Vop1/Vom1에 부하로 추가한 순간 sympy 정확해가 분자만 6000~16000항으로
    불어나(`stage2_dump_exact_forms.py` 실측) 손도 못 대고, leading-order 근사(최대 12dB
    오차)와 병렬컨덕턴스 가설(Acm/Ann에서 부호까지 틀림) 둘 다 실패했다 — 반면 **수치**로는
    노드가 18개든 31소자든 그냥 선형대수라 순식간이다(`stage2_numeric_mna_validate.py`로
    확인). 그래서 이 회로 계열(`telescopic_class_ab_cmfb`)의 Adm/Acm/Ann/H는 이제 매 metric
    평가마다 실제 사이징된 gm/gds로 이 자리에서 KCL을 수치로 푼다 — 폐형식 유도/유지보수
    부담이 없고, connectivity가 바뀌어도(topology.json이 유일한 소스) 이 solver 자체는
    안 바뀐다."""
    n = len(unknown_nodes)
    idx = {name: i for i, name in enumerate(unknown_nodes)}
    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n

    def add(node, other, coeff):
        if node not in idx:
            return
        r = idx[node]
        if other in idx:
            A[r][idx[other]] += coeff
        else:
            b[r] -= coeff * fixed.get(other, 0.0)

    for (d, s, g, gm, gds) in devices:
        add(d, g, gm)
        add(d, s, -gm - gds)
        add(d, d, gds)
        add(s, g, -gm)
        add(s, s, gm + gds)
        add(s, d, -gds)

    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(A[r][col]))
        if abs(A[piv][col]) < 1e-30:
            raise ValueError(
                f"telescopic_class_ab MNA 특이행렬(노드 {unknown_nodes[col]} 고립 또는 소자 "
                f"연결 누락) -- battery_vop1_side/battery_vom1_side 롤 배정을 확인할 것")
        A[col], A[piv] = A[piv], A[col]
        b[col], b[piv] = b[piv], b[col]
        pv = A[col][col]
        for r in range(col + 1, n):
            f = A[r][col] / pv
            if f == 0.0:
                continue
            for c in range(col, n):
                A[r][c] -= f * A[col][c]
            b[r] -= f * b[col]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (b[r] - sum(A[r][c] * x[c] for c in range(r + 1, n))) / A[r][r]
    return dict(zip(unknown_nodes, x))


def _load_telescopic_topology_cached() -> dict:
    """`current_reuse_telescopic_ota.topology.json`의 connectivity를 캐시해서 돌려준다
    (grid search 중 반복 호출 대비 -- 파일은 이 프로세스 안에서 안 바뀐다는 전제, 세션21).
    connectivity는 오직 이 JSON에서만 읽는다(하드타이핑 없음, topology.json이 유일한
    토폴로지 소스라는 프로젝트 원칙 그대로 -- `stage1_cmrr_sympy_derivation.py` 등 모든
    유도 스크립트와 동일한 소스)."""
    cache = _load_telescopic_topology_cached.__dict__
    if "by_name" not in cache:
        import os as _os
        topo_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                   "library", "current_reuse_telescopic_ota.topology.json")
        trs, _meta = load_topology(topo_path)
        cache["by_name"] = {t.name: t for t in trs}
    return cache["by_name"]


_TELESCOPIC_FIXED_BASE = {"gnd": 0.0, "Vbias1": 0.0, "Vbias2": 0.0, "Vbias3": 0.0, "Vbias4": 0.0}


def _telescopic_class_ab_open_loop_response(metric_spec: dict, ctx: SizingContext,
                                              vip: float, vim: float, vdd: float,
                                              vcmfb: float) -> tuple:
    """1단(11소자) + 양쪽 Monticelli class-AB battery(각 10소자, M8~M14b류/M17~M24b류) =
    31소자 소신호망을 `metric_spec`의 롤 배정으로 조립해 (Vop1, Vom1)을 수치로 푼다(세션21).

    metric_spec 키(기존 6개에 신규 7개 추가):
      기존: `input_p`/`cascode_p`/`input_n`/`cascode_n`(a쪽), `tail_p_devices`/`tail_n_device`.
      신규 `_b`(거울대칭 b쪽, 이제 완전대칭 가정 없이 실제 ctx.sized 값을 그대로 씀):
        `input_p_b`/`cascode_p_b`/`input_n_b`/`cascode_n_b`.
      신규 `battery_vop1_side`/`battery_vom1_side`(각각 10개 서브롤 dict, Vop1/Vom1측
        Monticelli battery+bias체인 -- topology.json 실측 connectivity 그대로):
        `vdd_src`(M8/M17, S=vdd 직접주입), `batt_hi`(M9a/M18a), `batt_lo`(M9b/M18b),
        `gate_diode1`/`gate_diode2`(M11a-M11b/M20a-M20b, replica bias 다이오드 체인),
        `gate_sink`(M12/M21), `output_sink`(M10/M19, Vop1/Vom1 직접 부하 -- **세션21에
        새로 반영된 것이 바로 이 소자의 로딩**), `gate2_src`(M13/M22), `gate2_diode1`/
        `gate2_diode2`(M14a-M14b/M23a-M24b).
      `cmfb_ctrl_device`(M7)는 이미 존재 -- topology.json에서 M7.gate가 실제로 "Vcmfb"이므로
      `vcmfb` 인자가 자동으로 M7에만 걸린다(별도 분기 불필요, connectivity가 그대로 결정)."""
    by_name = _load_telescopic_topology_cached()
    device_names = _telescopic_open_loop_device_names(metric_spec)

    devs, nodes = [], []
    seen_nodes = set()
    for name in device_names:
        t = by_name[name]
        gm, gds = ctx.sized[name]["gm"], ctx.sized[name]["gds"]
        devs.append((t.drain, t.source, t.gate, gm, gds))
        for n in (t.source, t.drain, t.gate):
            if n not in _TELESCOPIC_FIXED_BASE and n not in ("Vip", "Vim", "vdd", "Vcmfb") \
                    and n not in seen_nodes:
                nodes.append(n)
                seen_nodes.add(n)

    fixed = dict(_TELESCOPIC_FIXED_BASE)
    fixed.update({"Vip": vip, "Vim": vim, "vdd": vdd, "Vcmfb": vcmfb})
    sol = _mna_solve_smallsignal(devs, nodes, fixed)
    return sol["Vop1"], sol["Vom1"]


def _hashable_key(value):
    """dict/list를 재귀적으로 해시 가능한 tuple로 변환(딕셔너리 키로 쓰기 위한 정규화).
    `_telescopic_class_ab_open_loop_gains()`의 캐시 키용(2026-08-13 세션31) -- metric_spec이
    `battery_vop1_side`처럼 중첩 dict 값을 가질 수 있어 단순 list->tuple 변환만으론 부족하다."""
    if isinstance(value, dict):
        return tuple(sorted((k, _hashable_key(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_hashable_key(v) for v in value)
    return value


def _telescopic_open_loop_device_names(metric_spec: dict) -> list:
    """`_telescopic_class_ab_open_loop_response()`가 조립하는 31소자망의 소자 이름 목록.
    소자 열거(원래 그 함수 안에 있던 로직, 2026-08-13 세션31 리팩터로 공용 추출)와 캐시 키
    구성(`_telescopic_class_ab_open_loop_gains()`) 둘 다 이 목록을 쓴다."""
    names = []
    for role in ("input_p", "input_p_b", "cascode_p", "cascode_p_b",
                 "input_n", "input_n_b", "cascode_n", "cascode_n_b"):
        names.append(metric_spec[role])
    names += list(metric_spec["tail_p_devices"])
    names.append(metric_spec["tail_n_device"])
    names += list(metric_spec["battery_vop1_side"].values())
    names += list(metric_spec["battery_vom1_side"].values())
    return names


def _telescopic_class_ab_open_loop_gains(metric_spec: dict, ctx: SizingContext) -> tuple:
    """Adm_open/Acm_open/Ann_open/H를 **전부 같은 31소자망**에서 각기 다른 여기(excitation)로
    구한다(세션21) -- Adm(vip=+0.5/vim=-0.5), Acm(vip=vim=1), Ann(vdd=1, PSRR용 VDD 리플),
    H(vcmfb=1, `v(stage-1 CM out)/v(Vcmfb)` -- CMFB 루프이득 T=-H*A_c*G2의 그 H). 넷 다
    battery의 M10/M19 부하 + M8/M17의 자체 VDD 주입 경로를 동일하게 반영한다(세션20까지는
    H/Acm_open/Ann_open이 Kp'/Kn'/Rx/Ry 폐형식만 썼고 M10/M19를 몰랐다 -- 세션21에 이
    수치망으로 교체).

    2026-08-13(세션31) -- `ctx._open_loop_gains_cache`에 캐싱한다. `_cmrr_telescopic_class_
    ab_cmfb()`/`_psrr_telescopic_class_ab_cmfb()`가 "완전히 동일한" metric_spec으로 이 함수를
    각자 독립 호출하고 있었다(감사 발견 -- 한 세타평가당 31노드 MNA 4개씩 총 8개를 풀고 절반을
    바로 버림). ⚠️ **키에 metric_spec만 쓰면 틀린다**(첫 구현에서 실제로 회귀 발견,
    self-test 앵커2가 앵커1과 같은 캐시 항목을 잘못 맞고 128.72dB를 반환 -- 기대값 146.72dB):
    이 함수의 진짜 입력은 metric_spec이 가리키는 **소자 이름**뿐 아니라 그 소자들의 **현재
    ctx.sized[name]["gm"]/["gds"]** 값이다(self-test가 같은 ctx/metric_spec을 재사용하면서
    `ctx.sized["M5"]["gds"]`/`ctx.sized["M7"]["gm"]`을 직접 바꿔 두 번째 앵커를 만드는 패턴이라
    metric_spec 내용만으로는 이 변화를 못 잡는다). 그래서 metric_spec 정규화 내용 + 실제 참조되는
    31개 소자의 (gm,gds) 스냅샷을 함께 키로 쓴다 -- 실제 `_evaluate()` 파이프라인에서는 ctx가
    한 세타평가 안에서만 살고 CMRR/PSRR 호출 사이에 sized 값이 안 바뀌므로 여전히 캐시가
    맞아떨어지고, 이 self-test처럼 같은 ctx를 재사용하며 sized를 바꾸는 경우엔 올바르게
    캐시 미스로 다시 계산한다."""
    device_names = _telescopic_open_loop_device_names(metric_spec)
    key = (_hashable_key(metric_spec),
           tuple((n, ctx.sized[n]["gm"], ctx.sized[n]["gds"]) for n in device_names))
    cached = ctx._open_loop_gains_cache.get(key)
    if cached is not None:
        return cached
    vop1_dm, vom1_dm = _telescopic_class_ab_open_loop_response(metric_spec, ctx, 0.5, -0.5, 0.0, 0.0)
    Adm_open = vop1_dm - vom1_dm
    vop1_cm, vom1_cm = _telescopic_class_ab_open_loop_response(metric_spec, ctx, 1.0, 1.0, 0.0, 0.0)
    Acm_open = (vop1_cm + vom1_cm) / 2.0
    vop1_ann, vom1_ann = _telescopic_class_ab_open_loop_response(metric_spec, ctx, 0.0, 0.0, 1.0, 0.0)
    Ann_open = (vop1_ann + vom1_ann) / 2.0
    vop1_h, vom1_h = _telescopic_class_ab_open_loop_response(metric_spec, ctx, 0.0, 0.0, 0.0, 1.0)
    H = (vop1_h + vom1_h) / 2.0
    result = (Adm_open, Acm_open, Ann_open, H)
    ctx._open_loop_gains_cache[key] = result
    return result


def _cmrr_telescopic_class_ab_cmfb(metric_spec: dict, ctx: SizingContext) -> float:
    """`circuit_family="telescopic_class_ab_cmfb"` — current-reuse telescopic OTA의 CMRR,
    stage-1(11소자) + 양쪽 Monticelli class-AB battery(각 10소자) = 31소자 소신호망을
    `_telescopic_class_ab_open_loop_gains()`(세션21 신설)로 **수치 MNA**로 풀어 얻는다.

    ⚠️ **2026-08-03~08-07 폐형식(Kp'/Kn'/Rx/Ry 기반) 전면 교체(세션21)** — M10/M19
    (class-AB 바이어스 싱크, S=gnd/D=Vop1·Vom1/G=Vbias4)가 Vop1/Vom1에 거는 부하를 옛
    폐형식이 전혀 몰랐다는 게 세션21에 드러났다: 캐스코드 임피던스(Kp'∥Kn', O(1/eps²))가
    M10/M19의 비-캐스코드 임피던스(O(1/eps))에 완전히 지배당해, 실제 PSRR/CMRR이 옛 폐형식
    대비 **최대 49dB**(!) 차이 났다(`stage2_battery_psrr_sympy_derivation.py` 실측). 이걸
    바로잡는 폐형식(leading-order 근사, 병렬컨덕턴스 가설)을 두 번 시도했으나 둘 다 실패
    (leading order: 최대 12dB 오차 / 병렬컨덕턴스: Acm에서 부호까지 틀림) — M10/M19를 넣는
    순간 정확해 자체가 분자 6000~16000항으로 불어나 손 유도가 불가능함도 확인
    (`stage2_dump_exact_forms.py`). 그래서 폐형식을 버리고 **매 평가마다 실제 사이징된
    gm/gds로 KCL을 그 자리에서 수치로 푸는 방식**으로 교체했다 — 소자를 추가해도 재유도가
    필요 없고, 항상 topology.json connectivity 그대로다(단일 소스 원칙 유지).

    **원리는 그대로 유지**(선형 중첩, 세션20-B에서 확정된 구조 — 이 부분은 재도출 불필요):
    ```
      vo1   = Acm_open·vic + H·vcmfb ,  voc = G2·vo1 ,  vcmfb = A_c·voc
      CMRR  = |Adm_open/Acm_open| · |1 + T| ,   T := −H·A_c·G2      (G2가 소거된다)
    ```
    차이는 **Adm_open/Acm_open/H를 구하는 방법**뿐이다 — 예전엔 Kp'/Kn'/Rx/Ry 폐형식,
    지금은 `_telescopic_class_ab_open_loop_gains()`가 31소자망을 세 가지 여기(DM/CM/Vcmfb)로
    수치로 풀어 셋 다 한 번에 얻는다(M10/M19 로딩 + M8/M17의 자체 VDD 주입 경로까지 자동
    반영됨 — PSRR 쪽에서만 쓰이는 Ann도 같은 함수가 같이 계산). G2(2단 CM 전달이득)와
    A_c(CMFB 앰프 이득)는 M10/M19와 무관한 별개 서브회로라 옛 폐형식 그대로 재사용한다.

    **부호**: H<0(Vcmfb↓ → M7 전류↑ → stage-1 출력 CM↑), A_c<0(다이오드 부하 차동쌍),
    G2<0(2단 common-source 반전) → T=−H·A_c·G2>0(정상 음귀환). 하나라도 뒤집히면 CM
    latch-up이라 `ValueError`.

    **`Voc` 센싱**: 논문 II.D 원문("R1 and R2 are used to averaging Vop/Vom to Voc")대로
    **최종(2단) 출력**의 저항 평균(`cm_sense_gain`, 기본 1.0=R1=R2 이상적). `G2`는
    `cmfb_stage2_devices`(예 [M15,M16])의 Σgm/Σgds에서 계산(`_metric_gain_stages_sum`과
    동일 식).

    ⚠️ **남은 정직한 한계**(세션21 종료 시점): (1) `G2`/`A_c`는 여전히 폐형식(M10/M19와
    무관한 서브회로라 영향 없다고 판단했으나 독립 재확인은 안 함). (2) ngspice AC 교차검증은
    새 31소자망 기준으로 아직 안 함(다음 세션 최우선, self-test는 수치 자기회귀만).
    (3) `classab_centering_dev_v`/`gain_db`(stage-1 부분, `_metric_gain_stages_sum`)는
    여전히 M10/M19를 모르는 옛 방식 그대로 — 이번 세션 범위 밖으로 명시적으로 남겨둠.

    metric_spec 키: `_telescopic_class_ab_open_loop_response()`의 14개(`input_p`/`input_p_b`/
    `cascode_p`/`cascode_p_b`/`input_n`/`input_n_b`/`cascode_n`/`cascode_n_b`/
    `tail_p_devices`/`tail_n_device`/`battery_vop1_side`/`battery_vom1_side`) +
    `cmfb_ctrl_device`/`cmfb_amp_sense`/`cmfb_amp_ref`/`cmfb_load_sense`/`cmfb_load_ref`/
    `cmfb_tail_device`/`cmfb_stage2_devices`, 선택 `cm_sense_gain`."""
    Adm_open, Acm_open, Ann_open, H = _telescopic_class_ab_open_loop_gains(metric_spec, ctx)
    del Ann_open  # PSRR 전용, 여기선 안 씀(같은 함수로 4개를 한 번에 얻는 게 더 저렴해서 재사용)

    s2 = [ctx.sized[d] for d in metric_spec["cmfb_stage2_devices"]]
    G2 = -sum(d["gm"] for d in s2) / sum(d["gds"] for d in s2)
    G2 *= metric_spec.get("cm_sense_gain", 1.0)

    A_c = _cmfb_amp_gain_diode_load(metric_spec, ctx)
    T = -H * A_c * G2
    if T <= 0.0:
        raise ValueError(
            f"CM 루프가 음귀환이 아니다(T={T:.4g} <= 0; H={H:.4g}, A_c={A_c:.4g}, G2={G2:.4g}) "
            f"-- 정상 회로에서는 셋 다 음수라 T=-H·A_c·G2 > 0 이어야 한다. 부호가 하나라도 "
            f"뒤집히면 |T|>>1인 이 회로에서 CM 루프가 양귀환(latch-up)이 되고 소신호 CMRR "
            f"수치는 의미가 없으므로 계산을 거부한다 -- cmfb_* 소자 배정/극성과 "
            f"cmfb_stage2_devices를 다시 볼 것(_cmrr_telescopic_class_ab_cmfb docstring 참고)")
    return 20 * math.log10(abs(Adm_open / Acm_open) * (1.0 + T))


_CMRR_ESTIMATOR_REGISTRY = {
    "diff_pair_tail": _cmrr_diff_pair_tail,
    "telescopic_class_ab": _cmrr_telescopic_class_ab,
    "telescopic_class_ab_cmfb": _cmrr_telescopic_class_ab_cmfb,   # 배치 7-5b(2026-08-03)
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


def _psrr_telescopic_class_ab(metric_spec: dict, ctx: SizingContext) -> float:
    """`circuit_family="telescopic_class_ab"` — current-reuse telescopic 1단의
    **open-loop**(CMFB 제외) PSRR+(2026-08-07 신설, `analog-topology-json-library`
    세션20 후속). 기존 `diff_pair_tail`(M5 하나의 gm/gds만 보는 자리표시자, 이 회로에서는
    13개 자유 theta 중 어느 것도 M5에 안 닿아 절대 만족시킬 수 없는 상수값이었다 — 세션20
    실측 발견)를 대체한다.

    **유도**(`workspaces/current-reuse-telescopic-ota-report/spice/
    stage1_psrr_sympy_derivation.py` = sympy 정확해 + leading order,
    `.../stage1_psrr_ngspice_crosscheck.py` = ngspice AC 독립 교차검증):
    `_cmrr_telescopic_class_ab`와 **정확히 같은 위상/Adm/Acm_open**을 쓰고, VDD 리플이
    `tail_p_devices`(M6/M7, source=vdd)의 **gm**을 통해 Vx에 주입하는 전류
    (게이트 고정, Vgs=−δ이므로 i=−gm·δ — gds 항은 leading order에서 사라진다)가 그 이후
    똑같은 캐스코드 네트워크를 타고 출력에 실리는 경로로 얻는다:
    ```
      Ann_open = gm(tail_p 합) · (Rx‖Ry) · Acm_open      <- CMRR의 Acm_open을 그대로 재사용
      PSRR_open = 20·log10(|Adm/Ann_open|)
                = CMRR_open(dB) − 20·log10(|gm(tail_p 합)·(Rx‖Ry)|)
    ```
    즉 **PSRR은 CMRR에서 상수 하나만 뺀 값**이다(같은 회로의 같은 출력 임피던스 경로를
    타므로 당연한 결과) — Adm/Acm_open 재계산은 `_cmrr_telescopic_class_ab`와 완전히
    동일한 코드(중복이지만 이 파일의 기존 관례 그대로 — 두 CMRR family도 서로 안
    공유한다).

    ⚠️ **정직한 한계**: (1) gm(M6)/gm(M7)이 leading order에서 지배적이라고 가정했다(SPICE
    교차검증으로 확인, ±4배 랜덤 20점 + 앵커 2점 worst 2.36dB — CMRR 자신의 worst 0.8dB보다
    다소 크지만 탐색용으로는 충분). (2) 이건 **1단만** 본다 — 2단 Class-AB 출력전류원
    (M8/M13/M17/M22)도 source=vdd라 **자체적으로 또 다른 VDD 주입 경로**를 만드는데, 이번
    유도는 그걸 포함하지 않는다(다음 세션 과제, `.ai/context.md` 참고). (3) bias-gen
    체인(Vbias1 등)이 완벽한 AC ground라고 가정했다(실제로는 bias-gen 자신도 VDD에 물려
    있어 PSRR에 기여할 수 있음, 미포함).

    metric_spec 키: `_cmrr_telescopic_class_ab`와 완전히 동일(`input_p`/`cascode_p`/
    `input_n`/`cascode_n`/`tail_p_devices`/`tail_n_device`)."""
    gmp = ctx.sized[metric_spec["input_p"]]["gm"]
    gdsp1 = ctx.sized[metric_spec["input_p"]]["gds"]
    gmcp = ctx.sized[metric_spec["cascode_p"]]["gm"]
    gdsp2 = ctx.sized[metric_spec["cascode_p"]]["gds"]
    gmn = ctx.sized[metric_spec["input_n"]]["gm"]
    gdsn1 = ctx.sized[metric_spec["input_n"]]["gds"]
    gmcn = ctx.sized[metric_spec["cascode_n"]]["gm"]
    gdsn2 = ctx.sized[metric_spec["cascode_n"]]["gds"]
    gds_tail_p = sum(ctx.sized[d]["gds"] for d in metric_spec["tail_p_devices"])
    gm_tail_p = sum(ctx.sized[d]["gm"] for d in metric_spec["tail_p_devices"])
    Rx = 1.0 / gds_tail_p
    Ry = 1.0 / ctx.sized[metric_spec["tail_n_device"]]["gds"]

    Kp_prime = gmcp / (gdsp1 * gdsp2)
    Kn_prime = gmcn / (gdsn1 * gdsn2)
    Adm = (gmp + gmn) * (Kp_prime * Kn_prime / (Kp_prime + Kn_prime))
    Kp, Kn = gmp * Kp_prime, gmn * Kn_prime
    Acm_open = (Rx + Ry) * Kn * Kp / (Kn * Ry + Kp * Rx)
    Ann_open = gm_tail_p * (Rx * Ry / (Rx + Ry)) * Acm_open
    return 20 * math.log10(abs(Adm / Ann_open))


def _psrr_telescopic_class_ab_cmfb(metric_spec: dict, ctx: SizingContext) -> float:
    """`circuit_family="telescopic_class_ab_cmfb"` — current-reuse telescopic OTA의 PSRR,
    `_cmrr_telescopic_class_ab_cmfb`와 **완전히 같은 31소자 수치망**(세션21 신설
    `_telescopic_class_ab_open_loop_gains()`)에서 나오는 `Adm_open`/`Ann_open`/`H`를 쓴다.

    ⚠️ **세션20 폐형식(1단만, M8/M13/M17/M22의 자체 VDD 주입경로 미포함) 전면 교체(세션21)**
    — `_cmrr_telescopic_class_ab_cmfb` docstring의 M10/M19 로딩 문제와 정확히 같은 이유로
    폐형식을 버렸다. 이제 M8/M17(battery의 vdd 직접 주입)과 M10/M19(Vop1/Vom1 부하)가 같은
    31소자망 안에서 vdd=1V 여기로 자동 반영된다(`Ann_open`) — 세션20이 "다음 세션 과제"로
    남겼던 정확히 그 항목.

    PSRR closed = PSRR_open + 20·log10(|1+T|) 관계 자체는 그대로 유지(선형 중첩,
    `vo1 = Ann_open·δ + H·vcmfb`, `vcmfb=A_c·G2·vo1` → `vo1/δ = Ann_open/(1+T)`) — `T`는
    `_cmrr_telescopic_class_ab_cmfb`와 동일 정의(vdd와 무관한 CM 루프 자신의 성질).

    ⚠️ 남은 한계는 `_cmrr_telescopic_class_ab_cmfb`와 동일(G2/A_c는 여전히 폐형식,
    ngspice 재검증 미완, gain_db/classab_centering은 범위 밖).

    metric_spec 키: `_cmrr_telescopic_class_ab_cmfb`와 완전히 동일."""
    Adm_open, Acm_open, Ann_open, H = _telescopic_class_ab_open_loop_gains(metric_spec, ctx)
    del Acm_open  # CMRR 전용, 여기선 안 씀

    s2 = [ctx.sized[d] for d in metric_spec["cmfb_stage2_devices"]]
    G2 = -sum(d["gm"] for d in s2) / sum(d["gds"] for d in s2)
    G2 *= metric_spec.get("cm_sense_gain", 1.0)

    A_c = _cmfb_amp_gain_diode_load(metric_spec, ctx)
    T = -H * A_c * G2
    if T <= 0.0:
        raise ValueError(
            f"CM 루프가 음귀환이 아니다(T={T:.4g} <= 0; H={H:.4g}, A_c={A_c:.4g}, G2={G2:.4g}) -- "
            f"_cmrr_telescopic_class_ab_cmfb()와 동일한 가드, docstring 참고")
    psrr_open = 20 * math.log10(abs(Adm_open / Ann_open))
    return psrr_open + 20 * math.log10(abs(1.0 + T))


_PSRR_ESTIMATOR_REGISTRY = {
    "diff_pair_tail": _psrr_diff_pair_tail,
    "telescopic_class_ab": _psrr_telescopic_class_ab,               # 세션20
    "telescopic_class_ab_cmfb": _psrr_telescopic_class_ab_cmfb,     # 세션20
}


def _load_full_topology_cached(topology_path: str) -> tuple:
    """`topology_path`의 connectivity(소자+passive_elements)를 캐시해서 돌려준다(세션21
    신설, topology-무관 일반화). 캐시 키가 경로 문자열이라 4개 회로(`current_reuse_
    telescopic_ota`/`folded_cascode`/`nmcnr_amplifier`/`two_stage_ota`)를 같은 프로세스
    안에서 오가도 각자 캐시된다."""
    cache = _load_full_topology_cached.__dict__.setdefault("_cache", {})
    if topology_path not in cache:
        trs, _meta = load_topology(topology_path)
        with open(topology_path, encoding="utf-8") as fh:
            raw = json.load(fh)
        cache[topology_path] = {
            "by_name": {t.name: t for t in trs},
            "passive_elements": raw.get("passive_elements") or [],
        }
    entry = cache[topology_path]
    return entry["by_name"], entry["passive_elements"]


_DEFAULT_SENSE_RESISTOR_OHM = 1.0e9   # R1/R2류 "averaging만, 부하 없음" 근사(세션21, 사용자 확정)


def _full_circuit_devices(by_name: dict, sized: dict, passive_elements: list) -> list:
    """topology.json의 **모든** MOSFET + passive_elements 중 저항(`kind="resistor"`,
    `value_ohm` 미기재면 `_DEFAULT_SENSE_RESISTOR_OHM`)을 `_mna_solve_smallsignal()`용
    `(drain,source,gate,gm,gds)` 튜플로 변환한다. 저항은 gate=source, gm=0으로 스탬프하면
    같은 소자모델이 자동으로 평범한 2단자 저항 스탬프가 된다(별도 분기 불필요).

    ⚠️ **의도적으로 안 하는 것**: 커패시터(`kind="capacitor"`, 예 Cc1/Cc2)는 DC/mid-band
    소신호에서 개방회로라 건너뛴다 — GBW/PM류 주파수응답은 이 solver의 범위 밖(ngspice로
    다룰 것, 세션21 논의 참고). `ideal_sources`(전류원)는 이 함수가 아예 안 읽는다 — 이상적
    전류원은 소신호에서 무한임피던스(개방회로)라 스탬프할 게 없다(값이 있어도 소신호
    기여는 0). 이 두 가정 덕분에 bias-gen 체인(예: Iref로 구동되는 M18_bg류 미러)도 특별
    취급 없이 **다른 모든 소자와 똑같이** 자유노드로 풀리고, 그 결과 bias-gen 자신의
    vdd 결합까지 저절로(그리고 정직하게 최악의 경우로) 반영된다."""
    devs = []
    for name, t in by_name.items():
        s = sized.get(name)
        if s is None:
            raise KeyError(f"'{name}' 소자가 ctx.sized에 없다 -- 전체회로 수치 MNA는 "
                            f"topology.json의 소자 전부가 사이징돼 있어야 한다")
        devs.append((t.drain, t.source, t.gate, s["gm"], s["gds"]))
    for p in passive_elements:
        if p.get("kind") != "resistor":
            continue
        r_ohm = p.get("value_ohm") or _DEFAULT_SENSE_RESISTOR_OHM
        a, b = p["terminals"]
        devs.append((a, b, b, 0.0, 1.0 / r_ohm))
    return devs


def _full_circuit_response(ctx: SizingContext, excite: dict, also_fix: frozenset = frozenset()) -> dict:
    """`ctx.topology_path`가 가리키는 회로 **전체**(1단+2단+CMFB+bias-gen 전부, 세션21
    일반화 -- 세션21 초반이 "battery만" 골라 담았던 것과 달리 이번엔 정말 전부)를 `excite`
    (예: `{"Vip":0.5,"Vim":-0.5}`)로 여기해 모든 노드 전압을 수치로 푼다. `gnd`와
    `excite`의 키만 고정(독립원)이고 나머지는 전부 자유노드다 -- `Vbias1~4`/`Vcmfb`/
    bias-gen 체인까지 포함되므로, CMFB 루프 기여와 bias-gen의 자체 PSRR 결합이 **하나의
    선형계 풀이 안에 자동으로** 들어간다(세션21 초반 구현까지는 이걸 H/A_c/G2/T 3개
    서브식으로 손으로 조합했었다 -- 이제 그 조합 로직 자체가 필요 없다).

    `also_fix`(세션21 실측으로 필요성 발견) -- 게이트로만 쓰이고 drain/source로는 전혀
    안 쓰이는 노드(예: `Vip`/`Vim`)가 `excite`에 빠지면(예: PSRR의 `excite_den={"vdd":1}`
    호출) **자유노드로 취급되면서 KCL 행이 통째로 0**이 돼 특이행렬이 된다(게이트는 전류를
    안 뽑으므로 자기 자신의 KCL 방정식이 아예 안 생긴다) -- 실측으로 확인. `also_fix`에
    넘긴 노드는 이번 호출의 `excite`에 없어도 0V로 고정해 이 문제를 막는다. 호출자
    (`_metric_smallsignal_ratio_db`)가 `excite_num`/`excite_den` 전체 키의 합집합을
    넘겨, 두 호출 중 어느 쪽에서도 상대방의 여기 노드가 자유노드로 방치되지 않게 한다."""
    if not ctx.topology_path:
        raise ValueError("ctx.topology_path가 비어있다 -- SizingContext(topology_path=...) "
                          "로 채워야 _full_circuit_response()를 쓸 수 있다")
    by_name, passive_elements = _load_full_topology_cached(ctx.topology_path)
    devs = _full_circuit_devices(by_name, ctx.sized, passive_elements)
    fixed = {"gnd": 0.0}
    fixed.update({n: 0.0 for n in also_fix})
    fixed.update(excite)
    nodes = []
    seen = set(fixed)
    for (d, s, g, _gm, _gds) in devs:
        for n in (d, s, g):
            if n not in fixed and n not in seen:
                nodes.append(n)
                seen.add(n)
    sol = _mna_solve_smallsignal(devs, nodes, fixed)
    # 2026-08-13(세션31 이어, two_stage_ota gain_db 신설 중 발견) -- _mna_solve_smallsignal()은
    # 자유노드(nodes)만 반환하고 고정노드(gnd/excite/also_fix)는 반환 dict에 없어, 싱글엔디드
    # 출력(예: two_stage_ota의 OUT, 대비 기준이 'gnd' 하나뿐)을 sense_p/sense_n으로 잡는
    # metric_spec이 KeyError로 죽었다 -- 기존 4개 회로 호출부(current_reuse의 Vop/Vom류, 전부
    # 자유노드)는 이 merge로 동작이 전혀 안 바뀐다(fixed와 nodes는 서로소 집합이라 겹쳐쓸 값이
    # 없음, self-test 회귀로 확인). "gnd"를 sense 기준으로 쓸 수 있게 되어 smallsignal_gain_db/
    # smallsignal_ratio_db가 문서화된 대로("4개 회로 전부에 그대로 쓸 수 있다") 싱글엔디드
    # 회로에도 실제로 적용 가능해진다.
    return {**fixed, **sol}


def _metric_smallsignal_ratio_db(metric_spec: dict, ctx: SizingContext) -> float:
    """F엔진, topology-무관(세션21 신설) — CMRR/PSRR류 "두 여기의 응답비를 dB로" 패턴을
    일반화한다. `_cmrr_telescopic_class_ab_cmfb`/`_psrr_telescopic_class_ab_cmfb`(회로
    전용 폐형식 + 부분망 조합)를 대체 — 회로별 Python 함수 없이 topology.json의
    metric_spec 선언만으로 4개 회로(`current_reuse_telescopic_ota`/`folded_cascode`/
    `nmcnr_amplifier`/`two_stage_ota`) 전부에 그대로 쓸 수 있다.

    metric_spec 키: `excite_num`/`excite_den`(각각 `{node: value}` 독립원 여기),
    `sense_num`/`sense_den`(`"diff"`=`v(sense_p)-v(sense_n)`, `"common"`=
    `(v(sense_p)+v(sense_n))/2` — 기본값 각각 `"diff"`/`"common"`), `sense_p`/`sense_n`
    (관찰 노드 — 보통 topology.json `ports`가 선언한 최종 출력, 예 `Vop`/`Vom`). 반환:
    `20*log10(|num/den|)`.

    예(`cmrr_estimate_db`): `excite_num={"Vip":0.5,"Vim":-0.5}`(Adm, sense_num 기본 "diff"),
    `excite_den={"Vip":1,"Vim":1}`(Acm, sense_den 기본 "common"). `psrr_estimate_db`는
    `excite_den={"vdd":1}`로만 바뀐다(Ann) — `excite_num`(Adm)은 그대로 재사용(같은 회로,
    같은 DM 경로이므로 재도출 불필요)."""
    def sense(sol, mode):
        p, n = sol[metric_spec["sense_p"]], sol[metric_spec["sense_n"]]
        return (p - n) if mode == "diff" else (p + n) / 2.0

    all_ports = frozenset(metric_spec["excite_num"]) | frozenset(metric_spec["excite_den"])
    sol_num = _full_circuit_response(ctx, metric_spec["excite_num"], also_fix=all_ports)
    num = sense(sol_num, metric_spec.get("sense_num", "diff"))
    sol_den = _full_circuit_response(ctx, metric_spec["excite_den"], also_fix=all_ports)
    den = sense(sol_den, metric_spec.get("sense_den", "common"))
    return 20 * math.log10(abs(num / den))


def _metric_smallsignal_gain_db(metric_spec: dict, ctx: SizingContext) -> float:
    """F엔진, topology-무관(세션21 신설) — 회로 전체(로딩까지 포함)를 실제로 풀어 DM 이득을
    구한다. `_metric_gain_stages_sum`(스테이지별 gm/gds 곱을 서로 독립이라 가정, 스테이지
    간 로딩을 모른다 — M10/M19가 Vop1/Vom1을 지배한 것과 같은 종류의 한계)의 대체 후보다.
    ⚠️ `_metric_gain_stages_sum`은 다른 회로도 같이 쓰는 범용 타입이라 이번 세션엔 자동
    교체하지 않고 `gain_db`에 옵트인으로만 추가했다(`.ai/context.md` 세션21 F절 참고 —
    더 넓은 blast radius라 별도 판단 필요).

    metric_spec 키: `excite`(`{node:value}`), `sense_mode`(기본 `"diff"`), `sense_p`/
    `sense_n`."""
    sol = _full_circuit_response(ctx, metric_spec["excite"])
    p, n = sol[metric_spec["sense_p"]], sol[metric_spec["sense_n"]]
    mode = metric_spec.get("sense_mode", "diff")
    val = (p - n) if mode == "diff" else (p + n) / 2.0
    return 20 * math.log10(abs(val))


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
    "folded_cascode_gain_db":   _metric_folded_cascode_gain_db,      # 세션35
    "folded_cascode_pm_deg":    _metric_folded_cascode_pm_deg,       # 세션35
    "nmcnr_gain_db":            _metric_nmcnr_gain_db,               # 세션37
    "nmcnr_pm_deg":             _metric_nmcnr_pm_deg,                # 세션37
    "flicker_plus_thermal_sum": _metric_flicker_plus_thermal_sum,   # 배치 7-3g
    "pelgrom_mismatch":         _metric_pelgrom_mismatch,            # 배치 7-3h
    "cmrr_estimate":            _metric_cmrr_estimate,               # 배치 7-3i
    "psrr_estimate":            _metric_psrr_estimate,               # 배치 7-3i
    "rail_referenced_voltage":  _metric_rail_referenced_voltage,     # 세션6
    "battery_centering_deviation": _metric_battery_centering_deviation,  # 세션6
    "smallsignal_ratio_db":     _metric_smallsignal_ratio_db,        # 세션21, topology-무관
    "smallsignal_gain_db":      _metric_smallsignal_gain_db,         # 세션21, topology-무관
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
                            kcl_series_union, geometry_colocation_union,
                            assign_finger_geometry, run_topology_pipeline,
                            repair_matching_safety, split_into_stacks,
                            suggest_pair_finger_adjustments, PairAdjustmentSuggestion,
                            _branch_composite_pair, _failing_required_pairs,
                            find_min_crossover_layout_with_branch_composite,
                            refine_differential_and_mirror_relations,
                            audit_vertical_stack_id_vs_kcl,
                            merge_layout_groups_by_matching_pairs,
                            derive_horizontal_stack_groups,
                            check_box_shape, build_stick_diagram, audit_row_split,
                            apply_explicit_row_split, rebuild_floorplan,
                            check_stick_diagram_coverage,
                            require_device_roles_reviewed)


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


def _feed_root_const(feed_spec: dict, theta_value: float, ctx: SizingContext) -> None:
    """`{"type":"const","tag":...,"root":<device>|[<device>,...]}` — A엔진 `seed_currents`에
    `theta_value`(절대 전류, A) 그 자체를 `root`의 seed 전류로 채운다(2026-08-15 세션35 신설,
    사용자 지시 -- "sizing 제약을 없애고 스펙을 맞출 때 sizing이 어떻게 되는지 역으로 보고
    싶다"). `_feed_root_ratio`(type "A")는 항상 `reference` 소자의 이미 확정된 전류에 대한
    **비율**만 표현할 수 있어서(예: MP→M3/M4 미러비 1.5), `reference` 자체가 없는 진짜
    "루트"(예: `folded_cascode`의 `Ibg` -- 어떤 소자의 전류에도 종속되지 않는 독립 바이어스
    기준) 자체를 탐색 자유변수로 만들 방법이 없었다 -- `spec["known_sizing"]`으로 고정값을
    박아두는 게 유일한 길이었다(§7.3.2 표기상 "C유형"과 다른, 진짜 "자유 루트"). 이 타입은
    `reference`가 필요 없는 만큼 `_feed_root_ratio`보다 더 단순한 특수 케이스다 -- 새 엔진을
    만든 게 아니라 A엔진(`propagate_topology_forced_currents`)의 seed 자유도를 theta 탐색이
    닿을 수 있게 여는 것뿐이다."""
    roots = feed_spec["root"] if isinstance(feed_spec["root"], list) else [feed_spec["root"]]
    for root in roots:
        ctx.seed_currents[root] = theta_value


def _feed_root_signed_sum(feed_spec: dict, theta_value: float, ctx: SizingContext) -> None:
    """`{"type":"A_signed","tag":...,"root":<device>|[<device>,...],
    "terms":[{"device":<name>[,"sign":±1]}, ...]}` — `_feed_root_ratio`(type "A")의 부호 없는
    (전부 +1 계수 합) 버전을 일반화한다. A엔진 `seed_currents`에 `theta_value *
    sum(sign_i * ID(term_i 소자))`를 `root`의 seed 전류로 채운다(`sign` 생략 시 기본값 1).

    2026-08(세션6) 신설 동기 — `load_topology()`의 실제 connectivity만으로(손타이핑 netlist
    없이) 조립한 sympy KCL 재유도(`workspaces/current-reuse-telescopic-ota-report/spice/
    vg15_vop1_kcl_sympy_derivation.py`)가 이 회로의 실제 KCL은 종종 **뺄셈을 포함한다**는
    걸 확인했다 — 예: Vg15 노드(M8.drain/M9a.source/M9b.drain 3단자) KCL을 풀면
    `ID(M9b) = ID(M8) - ID(M9a)`인데, 기존 "A" 타입(`_feed_root_ratio`)은 `reference`
    전부를 +부호로만 합산해(`sum(_ref_id(r) for r in reference)`) 이런 관계를 표현할 수
    없었다 — 그 결과 topology.json의 `kcl_battery_M9b` theta가 존재하지도 않는 노드
    조합("Vg15=M11b.drain/M9a.drain/M9b.drain", 실제로는 셋 다 아니거나 다른 단자)에서
    유도된 틀린 공식(`ID(M9b)=ID(M11a체인)+ID(M9a)`)을 쓰고 있었다(위 sympy 스크립트로
    발견·확정, 사용자 지적 "M10과 M8은 같은 branch 전류인데 독립적이야?"가 계기).

    `root`는 `_feed_root_ratio`와 동일하게 문자열(소자 1개) 또는 리스트(여러 소자, 전부
    같은 신호부호합을 동시에 시드 — 예: 좌우 대칭 두 노드에 같은 KCL 관계를 함께 적용)를
    받는다. `reference`(부호 없음)와 이름이 같은 실수를 막기 위해 이 타입은 의도적으로
    `terms`라는 다른 키를 쓴다 — `reference`를 그대로 받으면 `_feed_root_ratio`용
    선언과 이 타입용 선언이 겉보기엔 비슷해 보여도 의미가 다른데(전자는 항상 +, 후자는
    부호 필드 필요) 실수로 섞어 쓰기 쉽다."""
    roots = feed_spec["root"] if isinstance(feed_spec["root"], list) else [feed_spec["root"]]

    def _ref_id(name):
        entry = ctx.sized.get(name)
        if entry is not None and "ID" in entry:
            return entry["ID"]
        return ctx.seed_currents[name]

    total = sum(term.get("sign", 1) * _ref_id(term["device"]) for term in feed_spec["terms"])
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
    둘 다 pmos)는 kind 일치가 확인된 경우만이다(self-test 참고).

    ⚠️ **2026-08-12(세션30) 정정 -- "gm_id를 그대로 물려받는다"는 위 설명은 `target`이
    `device_roles`에 `gm_id_role`이 없을 때만 최종 값으로 남는다.** `target`(예: M9a)이
    `gm_id_role`을 가지면(K_replica의 M9a·mirror_M18a의 M18a가 실제로 둘 다 그렇다)
    이 함수가 여기서 채운 `gm_id`는 **곧바로 `_evaluate()`의 device_roles 루프가
    `search_gm_id_for_role()`로 재검색해 덮어쓴다**(role="matching"이면 `min(feasible)`
    선택 -- reference의 gm_id를 그대로 쓰는 게 아니라 target 자기 자신의 W_bounds/
    ID_target 기준으로 새로 고른다, 3222행 근처 참고). L/VDS/VS만 이 함수가 물려준 값이
    최종까지 유지된다(device_roles 루프는 L/vds를 안 건드림). K_replica처럼 `theta_value`
    (면적비)가 1.0이 아니면 이 재검색이 reference와 다른 gm_id를 낼 수 있다 -- 다만
    `mirror_M18a`처럼 `theta_value=1.0`(완전 replica, L/vds/ID_target까지 reference와
    동일)이면 재검색이 결정론적으로 reference와 같은 gm_id를 다시 찾아내므로 실질적으로는
    "물려받는다"는 원래 설명과 결과가 같다 -- 이 코드는 안 건드리고 설명만 정정한다."""
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
    채운다.

    2026-08-03(배치 7-5b, CMFB CMRR 식을 실회로에 적용하다 `KeyError: 'gds'`로 실제 재현):
    이 핸들러는 `gds`를 안 채우고 있었다 — A/C 타입 feed는 reference 소자의 항목을 통째로
    복사해 오고 `metric_stage_budget`은 LUT에서 gds를 직접 계산하는데, 이 B 타입만 gm/ID/W/L만
    넣어 gds가 빠져 있었다. F엔진 metric 중 gm만 읽는 것(gain/noise)만 있을 땐 안 드러났지만,
    CMFB 소자의 gds를 읽는 `telescopic_class_ab_cmfb` CMRR이 등장하면서 발현됐다 —
    `_feed_metric_stage_budget()`과 같은 방식(`lut.gm_gds_ratio()`)으로 채운다."""
    target = feed_spec["target"]
    kind = ctx.kind_of[target]
    lut = ctx.spec["lut_by_kind"][kind]
    L, vds, vs = feed_spec["L"], feed_spec.get("vds", 0.6), feed_spec.get("vs", 0.0)
    omega_key = feed_spec["omega_key"]
    # 2026-08-10(세션27) -- compensation의 topology_fn이 omega_c 등을 ctx.derived에 노출하면
    # (예: current_reuse_telescopic_topology()의 Eq.2 omega_c=6.9/t_lln) spec의 손으로 채운
    # 값보다 우선한다 -- do.md §7.3.1 Level2->Level6 사슬(gm1이 정하는 omega_c가 CMFB 대역폭
    # 조건의 입력이어야 함)을 실제로 연결. ctx.derived에 없으면(compensation이 이 값을 안
    # 드러내는 다른 topology_fn) 기존처럼 spec에서 그대로 읽어 하위호환 유지.
    omega_val = ctx.derived[omega_key] if omega_key in ctx.derived else ctx.spec[omega_key]
    gm_target = theta_value * omega_val * ctx.spec[feed_spec["cap_key"]]
    result = solve_id_for_target_gm(
        lut, L, vds, vs, feed_spec["W"], gm_target,
        gm_id_bounds=tuple(feed_spec.get("gm_id_bounds", (2.0, 30.0))))
    # 2026-08-14 -- _L_source 태그 추가(metric_stage_budget에서 발견한 것과 동일 유형의
    # 근본원인을 이 feed 타입에서도 선제적으로 막음): 이 소자의 L/gm_id는 N×ωc 컨벤션
    # 자체가 확정하는 값이라(theta_value가 곧 대역폭 배수), device_roles의 gm_id_role/
    # L_role이 뒤이어 덮어쓰면 이 theta의 의도가 무력화된다 -- compensation/replica/
    # metric_stage_budget과 동급의 권위 있는 출처로 등록한다.
    ctx.sized[target] = {"ID": result.ID, "gm": result.gm, "gm_id": result.gm_id,
                          "W": feed_spec["W"], "L": L, "vds": vds, "vs": vs, "kind": kind,
                          "gds": result.gm / lut.gm_gds_ratio(result.gm_id, L, vds, vs),
                          "_L_source": "gm_target_convention"}


def _feed_settling_split(feed_spec, theta_value: float, ctx: SizingContext) -> None:
    """`"settling_split"`(bare 문자열) 또는 `{"type":"settling_split","output_key":...,
    "total_key":...,"complement_key":...}` — `theta_value`(비율) `* ctx.spec[total_key]`를
    `ctx.derived[output_key]`에 저장하는 스칼라 파생이다.

    2026-08-10(세션27) -- 이전엔 `output_key`(보통 t_slew)만 채우고 do.md §7.3.1 Level1이
    말하는 "t_s=t_slew+t_lln 배분"의 나머지 절반(t_lln)은 아무도 계산하지 않아 `_evaluate()`가
    `optimize_full_circuit_budget()` 바깥/`topology_fn` 구성 시점에서 이어붙여야 한다고
    문서화만 해둔 채 실제로는 미배선 상태였다(f_slew가 사실상 dead theta였던 원인,
    `.ai/context.md` 세션27 참고). 이제 `complement_key`(기본 `"t_lln"`)에
    `total - theta_value*total`도 함께 저장한다 -- `optimize_full_circuit_budget()`의
    `_evaluate()`가 compensation보다 이 feed를 먼저 적용하고, compensation이
    `ctx.derived["t_lln"]`을 `spec["t_lln"]`보다 우선해 읽으면 f_slew->t_lln->omega_c->
    N_cmfb_bw(do.md Level1->2->6) 사슬이 실제로 연결된다. `complement_key=None`을 명시하면
    이 계산을 건너뛴다(다른 회로가 이 feed를 t_lln과 무관한 순수 스칼라 파생 용도로만
    쓰고 싶을 때)."""
    if isinstance(feed_spec, str):
        output_key, total_key, complement_key = "t_slew", "t_settle_total", "t_lln"
    else:
        output_key = feed_spec.get("output_key", "t_slew")
        total_key = feed_spec.get("total_key", "t_settle_total")
        complement_key = feed_spec.get("complement_key", "t_lln")
    total = ctx.spec[total_key]
    t_out = theta_value * total
    ctx.derived[output_key] = t_out
    if complement_key:
        ctx.derived[complement_key] = total - t_out


def _metric_stage_budget_finalize(ctx: SizingContext, name: str, gm_id: float, ID: float,
                                   mL: float, mvds: float, mvs: float) -> None:
    """`_feed_metric_stage_budget()`/`_run_shared_current_joint_scan()`이 공유하는 확정
    헬퍼(2026-08-13 세션31, N-way 조인트 스캔 신설로 모듈 레벨로 승격 -- 이전엔
    `_feed_metric_stage_budget()` 내부 클로저였는데, 조인트 스캔이 **여러 feed의 devices를
    가로질러** 같은 계산을 해야 해서 한쪽에만 있으면 중복 구현이 된다)."""
    kind = ctx.kind_of[name]
    lut = ctx.spec["lut_by_kind"][kind]
    idu = lut.gm_id_to_id_density(gm_id, mL, mvds, mvs)
    gm_gds = lut.gm_gds_ratio(gm_id, mL, mvds, mvs)
    gm = gm_id * ID
    # 2026-08-10(세션27) -- vds는 위에서 LUT 조회에 이미 쓰였는데 entry에 저장하는 걸
    # 빠뜨리고 있었다(gm/gds/gm_id/kind/vs만 갱신). 헤드룸 배정 루프가 이 소자의 vds를
    # ctx.sized에서 못 찾아 "미확정"으로 오판하는 실제 버그로 발현(L_cascode/L_stage2out
    # 대상 소자 M2a/M2b/M3a/M3b/M15/M16/M25/M26 전부 영향 -- M11a/M11b 등 이전 gap들
    # 때문에 이 지점까지 실행이 도달한 적이 없어 여태 발견되지 않았다). 같은 이유로
    # classab_centering_dev_v(_metric_rail_referenced_voltage()가 entry["vds"]를 직접
    # 읽음)도 이 소자들에 대해선 KeyError로 계산 자체가 불가능했을 것.
    # 2026-08-13(세션31, BO 조사 중 발견) -- "ID" 키 자체가 이 update()에 없었다(gm=
    # gm_id*ID는 지역적으로 정확히 계산하면서 그 ID를 entry에 다시 써넣지 않음). 공유전류
    # 재계산이 I_new로 gm/gds는 옳게 바꿔도 ctx.sized[name]["ID"]는 compensation이
    # 최초로 넣어둔 stale 값에 계속 머물렀다 -- 이걸 읽는 하류 소비자(예: K_replica/
    # mirror_M18a의 _feed_diode_stack_target()가 reference["ID"]를 그대로 스케일해 복제)
    # 가 잘못된 전류를 물려받는 실제 버그로 이어진다(BM의 선언순서 재배치만으로는 L/gm_id
    # staleness만 고쳐졌을 뿐 ID staleness는 그대로 남아 있었다).
    # 2026-08-14 -- _L_source 태그 추가(실측으로 발견한 진짜 버그의 근본수정): 이 소자의
    # L/gm_id는 metric_stage_budget theta(예: L_cascode)의 그리드서치가 이미 확정한 값인데,
    # 이 태그가 없어서 device_roles의 gm_id_role/L_role(propose_device_roles_gap_fill()이
    # 자동으로 제안·반영한 값 포함)이 뒤이어 이 소자를 다시 덮어썼다 -- current_reuse_
    # telescopic_ota의 M2a/M2b/M3a/M3b에 L_role="mirror"를 채웠더니 L_cascode theta
    # 탐색이 무의미해지며 gain_db가 76.48->74.8로 떨어지는 실제 회귀로 발현(SLSQP 재현,
    # 이 세션에 실측). compensation/replica와 동급의 권위 있는 출처로 등록한다.
    ctx.sized[name].update({"L": mL, "W": mL * ID / idu, "gm": gm, "gds": gm / gm_gds,
                             "gm_id": gm_id, "ID": ID, "kind": kind, "vs": mvs, "vds": mvds,
                             "_L_source": "metric_stage_budget"})


def _shared_current_groups_from_compensation(comp: dict | None) -> list:
    """`comp["shared_gm_id_groups"]`(compensation-스테이지 인덱스 쌍/N-튜플 리스트)를
    `comp["stage_devices"]`(스테이지 인덱스 -> 소자명 리스트)로 펼쳐 "같은 전류를
    공유하는 소자명 frozenset" 리스트로 바꾼다 -- **단일 정의**로 세 곳
    (`_evaluate()`의 스냅샷 구성 / `_build_shared_current_joint_plan()` / `validate_
    theta_declaration_order()`)이 전부 이걸 재사용한다(2026-08-13 세션31, N-way 확장
    중 셋이 서로 다른 정의를 쓰면 검증기와 실제 엔진이 어긋나는 위험을 없애려고 분리)."""
    if not comp:
        return []
    stage_devices = comp.get("stage_devices") or []
    return [frozenset(name for idx in sg for name in stage_devices[idx])
            for sg in (comp.get("shared_gm_id_groups") or [])]


def _evenly_subsample(seq: list, n: int) -> list:
    """정렬된 이산 리스트 `seq`에서 최대 `n`개를 균등 간격 인덱스로 뽑는다(`n>=len(seq)`면
    그대로 반환) -- `dense_candidates()`가 LUT의 **연속** 축(L/VDS)에 하는 것과 같은
    역할을 `gm_id_grid`류 **이산** 격자에 적용한다(2026-08-13 세션31, N-way 조인트
    스캔의 차원당 예산 캡용 신설)."""
    if n >= len(seq):
        return list(seq)
    if n <= 1:
        return [seq[0]]
    idxs, seen, out = [round(i * (len(seq) - 1) / (n - 1)) for i in range(n)], set(), []
    for i in idxs:
        if i not in seen:
            seen.add(i)
            out.append(seq[i])
    return out


def _build_shared_current_joint_plan(group_members: frozenset, thetas: list) -> dict | None:
    """`group_members`(한 `shared_current_group`의 소자명 집합)에 대해, 2개 이상의
    feed가 **독립 자유도**(`gm_id_role` 또는 `gm_id_match_vgs_of`)로 gm_id를 정하면
    N-way 조인트 스캔 계획을 만든다. 하나 이하면 `None`(기존 단일-소자 per-feed 로직
    그대로 -- 완전 하위호환, `current_reuse_telescopic_ota` 외 회로는 전부 이 경로).

    순수 함수(정적 `thetas` 선언만 읽음, `ctx`/런타임 상태 무관) -- `_build_theta_
    evaluator()`가 토폴로지 로드 시 **한 번만** 호출해 클로저로 재사용한다(evaluate()마다
    다시 만들지 않음 -- 재계산 비효율 방지).

    2026-08-13(세션31 BS, tolerance-band 재설계 -- 사용자 확정): `gm_id_match_vgs_of`가
    **그룹 내부**를 참조해도 더 이상 "그 소자의 VGS와 정확히 같아야 하는 dependent"로
    강제하지 않는다(BQ가 처음 그렇게 설계했으나, BS 조사로 이게 실제 스펙 -- `classab_
    centering_dev_v<=0.15V`, **부등식** -- 보다 훨씬 좁은 인위적 등식 제약이었음이
    드러남, `.ai/context.md` BS 참고). 대신 `gm_id_match_vgs_of`가 있는 feed도 `gm_id_
    role`이 있는 feed와 **동등하게 자유 root**로 취급한다 -- "이 소자가 다른 소자와
    관련된 값을 가져야 한다"는 사실 자체는 topology.json 선언에 여전히 남아있지만
    (문서/가독성 + `_feed_metric_stage_budget()`의 1단계 잠정값 계산이 여전히 이 필드로
    VGS 근사 seed를 만듦), **최종 확정은 실제 declared constraint(들)을 만족하는 조합
    중 목표 metric을 최대화하는 조인트 스캔**이 담당한다(`_run_shared_current_joint_
    scan()`). `gm_id_match_vgs_of`가 그룹 **바깥** 소자를 참조하면(이 그룹과 무관한
    결합) 여전히 "pinned"로 취급 -- 그 관계는 이 그룹의 조인트 스캔 관심사가 아니다.

    반환: `{"nodes": {devices_key: {"kind": "root"|"pinned", "feed": dict}}, "roots":
    [devices_key,...], "trigger_devices_key": tuple, "metric": str}` --
    `trigger_devices_key`는 이 그룹에 닿는 `metric_stage_budget` theta 중 **선언
    순서상 마지막** 것(그래야 그룹 전체 소자의 L/VDS가 전부 확정된 뒤에 조인트 스캔이
    돈다, `validate_theta_declaration_order()`가 검사하는 것과 동일한 "선언 순서=실행
    순서" 계약)."""
    touching = []
    for i, t in enumerate(thetas):
        feed = t["feeds"]
        if not isinstance(feed, dict) or feed.get("type") != "metric_stage_budget":
            continue
        devs = tuple(feed.get("devices") or [])
        if set(devs) & group_members:
            touching.append((i, t["name"], feed, devs))
    if not touching:
        return None
    devices_key_by_device = {d: dk for _, _, f, dk in touching for d in f["devices"]}
    nodes = {}
    for i, name, feed, devices_key in touching:
        match_dev = feed.get("gm_id_match_vgs_of")
        matches_in_group = match_dev is not None and match_dev in devices_key_by_device
        is_root = feed.get("gm_id_role") is not None or matches_in_group
        nodes[devices_key] = {"kind": "root" if is_root else "pinned", "feed": feed}

    roots = [k for k, n in nodes.items() if n["kind"] == "root"]
    if len(roots) < 2:
        return None  # 자유도 1개 이하면 결합이 성립하지 않음(BQ 분석: 1-D 자기 최적화가
                      # 이미 곧 metric 최적화와 같다 -- 조인트 스캔이 필요한 건 2개 이상)

    trigger_index, trigger_name, trigger_feed, _ = max(touching, key=lambda x: x[0])
    return {"nodes": nodes, "roots": roots,
            "trigger_devices_key": tuple(trigger_feed["devices"]),
            "metric": trigger_feed.get("metric", "gain_db")}


def _run_shared_current_joint_scan(plan: dict, ctx: SizingContext) -> None:
    """`_build_shared_current_joint_plan()`이 만든 계획을 실행 -- 그룹의 각 root(자유
    gm_id) feed마다 하나의 자유도로 삼아 `ctx.spec["gm_id_grid"]`(BQ 회귀로 확정된
    `search_gm_id_for_role()` 기본 해상도, 아래 참고) 위를 K-D 조인트로 스캔하면서,
    **결합 목표 지표**(`plan["metric"]`, topology.json이 이미 선언한 것 그대로 -- 로컬
    재정의 없음)를 최대화하는 조합을 찾는다.

    2026-08-13(세션31 BS, tolerance-band 재설계 -- 사용자 확정 "2번이 올바른 설계"):
    이전 버전(BQ~BR)은 `gm_id_match_vgs_of` 소자를 "다른 소자의 VGS와 **정확히**
    같아야 하는 dependent"로 강제(등식)했는데, 실측으로 이게 실제 declared constraint
    (`classab_centering_dev_v<=0.15V`, **부등식**)보다 훨씬 좁은 인위적 제약이었음이
    드러났다(BI가 원래 조사에서 찾은 최적점은 그 등식 곡선 위에 없었음, `.ai/context.md`
    BS 참고). 이제 그런 소자도 **완전히 자유로운 root**로 다루고, 대신 목표 metric
    외에 **topology.json이 실제로 선언한 다른 모든 constraint**(예: `classab_
    centering_dev_v<=0.15V`)를 후보마다 평가 가능한 범위 안에서 feasibility 필터로
    강제한다(`ctx.derived["_constraints"]`, 로컬에서 "centering"류 개념을 하드코딩하지
    않음 -- 어떤 constraint든 이 그룹 소자만으로 평가 가능하면 그대로 적용됨, 일반화).
    목표 metric 자신의 문턱(`gain_db>=75.6`류)은 여기서 강제하지 않는다 -- 그건
    "최대화할 대상"이지 "이 국소 스캔에서 만족을 요구할 게이트"가 아니다(전체 회로
    수준의 최종 feasibility는 `optimize_full_circuit_budget()`가 담당).

    **재계산 비효율 방지**: 새 탐색차원(root 개수 K)마다 격자를 그대로 곱하면
    `len(gm_id_grid)**K`로 조합폭발한다 -- `search_stage_budget_L_warm_start()`와 같은
    `target_total**(1/k)` 형태의 예산 공식을 쓰되, 여기 후보 평가는 그 함수(L 탐색,
    후보마다 `optimize_multistage()`급 재계산)보다 훨씬 싸므로(LUT 보간+산술만) 총예산
    자체를 훨씬 크게(5000) 잡는다 -- 아래 코드 주석 참고, K=2(이 프로젝트의 유일한
    실제 사례, M15/M16)에서는 BI가 실측으로 쓴 것과 같은 57×57 전체 해상도가 그대로
    나온다."""
    group_members = frozenset(n for node in plan["nodes"].values()
                               for n in node["feed"]["devices"])
    shared_group = ctx.derived["_shared_current_group"][next(iter(group_members))]
    gm_total = shared_group["gm_total"]
    metrics_specs = ctx.derived["_metrics_specs"]
    metric_spec = metrics_specs[plan["metric"]]
    # 2026-08-13(세션31 BS, tolerance-band 재설계 중 실측으로 발견) -- "다른 모든
    # constraint"를 무조건 강제하면, 이 그룹과 전혀 무관한 소자(예: mismatch_sigma_mV
    # 는 M1a/M1b에만 의존)가 **이 evaluate() 시점에 아직 최적화 전이라 우연히 위반
    # 상태**일 때 이 그룹의 모든 후보가 부당하게 infeasible로 판정됐다(실측 재현:
    # L=1.0µm의 이미 알려진 실현가능점(15.5,4.0)조차 mismatch_sigma_mV=10.79
    # 위반으로 거부됨 -- 이건 M15/M16과 무관한 기존 위반). 이미 있는 `_metric_device_
    # footprint()`(정적으로 metric이 읽는 소자 집합을 판정, `derive_theta_dependency_
    # graph()`가 쓰는 것과 동일 함수 -- 새로 안 만듦)로 그 constraint의 metric이 읽는
    # 소자 집합이 **이 그룹 소자만으로 완전히 구성될 때만**(부분집합, "ALL"류 전체회로
    # metric 제외) feasibility 게이트로 강제한다 -- 그룹과 무관한 아직-미최적화 상태에
    # 억울하게 걸리지 않으면서도, `classab_centering_dev_v`(={M15,M16}⊆group)처럼 이
    # 그룹만으로 완전히 결정되는 constraint는 그대로 강제된다.
    other_constraints = [
        c for c in ctx.derived.get("_constraints", [])
        if c["metric"] != plan["metric"]
        and isinstance(_metric_device_footprint(c["metric"], metrics_specs), set)
        and _metric_device_footprint(c["metric"], metrics_specs) <= group_members]
    W_bounds = ctx.spec.get("W_bounds", (1e-6, 200e-6))
    roots = plan["roots"]
    pinned = [k for k in plan["nodes"] if k not in roots]

    def _rep_device(devices_key):
        return devices_key[0]

    # pinned feed(비결합 root/pinned)의 gm_id는 이미 per-feed 1단계에서 확정돼
    # ctx.sized에 있다 -- 조인트 스캔 동안 안 바뀌므로 미리 합쳐 상수로 취급.
    fixed_gm_id_sum = sum(ctx.sized[_rep_device(k)]["gm_id"] for k in pinned)

    def _score_and_apply(root_gm_ids: dict) -> float | None:
        """root_devices_key -> 후보 gm_id 매핑 하나를 실제로 ctx.sized에 반영 시도하고,
        feasible(W_bounds + 다른 모든 평가 가능한 constraint 만족)하면 score를, 아니면
        `None`을 반환한다. W_bounds는 이 후보가 만드는 **실제** 공유전류 I로 검사한다."""
        I = gm_total / (fixed_gm_id_sum + sum(root_gm_ids.values()))
        if I <= 0:
            return None
        for key, gm_id in root_gm_ids.items():
            dev = ctx.sized[_rep_device(key)]
            lut = ctx.spec["lut_by_kind"][dev["kind"]]
            try:
                # 이 (L,vds) 조합의 LUT 실측범위 밖 gm_id(과도한 weak inversion 등)는
                # _solve_vgs()가 ValueError로 거부한다 -- search_gm_id_for_role()의
                # _idu_scan()이 내부적으로 걸러주던 것과 동일한 상황, 여기서도 "이 후보는
                # infeasible"로 취급하고 다음 후보로 넘어간다(크래시 아님).
                idu = lut.gm_id_to_id_density(gm_id, dev["L"], dev["vds"], dev.get("vs", 0.0))
            except ValueError:
                return None
            W = dev["L"] * I / idu
            if not (W_bounds[0] <= W <= W_bounds[1]):
                return None
        # pinned 소자도 I가 바뀌면 절대 gm/gds가 같이 바뀐다(gm_id는 고정, gm=gm_id*I) --
        # 다른 constraint(예: centering)가 이 소자들을 참조할 수 있으므로 함께 재확정.
        for key in roots + pinned:
            gm_id = root_gm_ids[key] if key in root_gm_ids else ctx.sized[_rep_device(key)]["gm_id"]
            for name in plan["nodes"][key]["feed"]["devices"]:
                dev = ctx.sized[name]
                _metric_stage_budget_finalize(ctx, name, gm_id, I, dev["L"], dev["vds"],
                                               dev.get("vs", 0.0))
        for c in other_constraints:
            cspec = metrics_specs.get(c["metric"])
            if cspec is None:
                continue
            try:
                cval = compute_metric(cspec, ctx)
            except KeyError:
                continue  # 방어적 fallback -- other_constraints는 이미 group_members
                          # 부분집합으로 필터됐으므로 이론상 도달하지 않음
            if not _CONSTRAINT_OPS[c["op"]](cval, c["value"]):
                return None
        return compute_metric(metric_spec, ctx)

    # 2026-08-13(세션31 BQ, self-test 회귀로 발견) -- `ctx.spec["gm_id_grid"]`는
    # compensation의 스테이지 (L,VDS,gm_id) 조인트 탐색 전용 격자로, `search_gm_id_
    # for_role()`(per-feed 1단계 잠정 탐색이 실제로 쓰는 것)은 이 spec 키를 전혀 안
    # 읽고 **자기 자신의 기본 격자**(2.0~30.0, 0.5간격, 57점)를 쓴다 -- 여기서
    # `ctx.spec["gm_id_grid"]`를 재사용하면 두 메커니즘이 서로 다른 해상도로 갈라져(L5c
    # self-test가 `gm_id_grid=[4,8,...,24]`처럼 훨씬 성긴 값을 쓰는 실제 사례로 발견,
    # 회귀: 하류 KCL이 음수가 됨) 기존 `gm_id_role` 잠정 탐색과 다른 답을 낸다.
    # `search_gm_id_for_role()`의 기본 해상도를 그대로 재사용한다(spec의 다른 용도
    # 키를 재활용하지 않음).
    base_grid = [i * 0.5 for i in range(4, 61)]
    k = len(roots)
    # 2026-08-13(세션31 BS, tolerance-band 재설계 중 실측으로 발견) -- `search_stage_
    # budget_L_warm_start()`의 `target_total**(1/k)` 그대로(그 함수의 n_scan_full_circuit
    # 기준)를 쓰면 K=2에서 차원당 약 11점(121 조합)뿐이라, BI가 실측으로 확인한 실제
    # feasible 영역(narrow -- classab_centering_dev_v<=0.15V가 (gm_id_p,gm_id_n) 평면에서
    # 좁은 띠를 이룸)을 그리드가 완전히 놓쳐 InfeasibleSizingError로 실패했다. L 탐색(각
    # 후보가 optimize_multistage() 재호출급으로 비쌈)과 달리 여기 후보 평가는 LUT
    # 보간+산술 몇 번뿐이라(캐시된 `_gm_id_curve`/`_idu_scan` 재사용) 훨씬 큰 총예산을
    # 감당할 수 있다 -- 총 조합수를 5000으로 캡(K=1: 57, K=2: 57×57=3249<=5000이라 전체
    # 해상도 유지, K=3: 5000**(1/3)≈17/차원, K=4+: 더 낮아짐)해 K=2(이 프로젝트의 유일한
    # 실제 사례)에서는 BI가 썼던 것과 동일한 57×57 전체 해상도를 그대로 재현한다.
    target_total = min(len(base_grid) ** max(k, 1), 5000)
    per_dim_n = len(base_grid) if k <= 1 else max(2, round(target_total ** (1.0 / k)))
    root_grids = [_evenly_subsample(base_grid, per_dim_n) for _ in roots]

    best_score, best_combo = None, None
    for combo in itertools.product(*root_grids):
        candidate = dict(zip(roots, combo))
        score = _score_and_apply(candidate)
        if score is None:
            continue
        if best_score is None or score > best_score:
            best_score, best_combo = score, candidate
    if best_combo is None:
        raise InfeasibleSizingError(
            f"공유전류 조인트 스캔({plan['metric']!r})이 W_bounds/다른 constraint 안에서 "
            f"실현가능한 조합을 하나도 못 찾음 -- roots={roots}",
            sized_snapshot=dict(ctx.sized))
    _score_and_apply(best_combo)  # 최종 확정(ctx.sized를 승자 조합으로 다시 반영)


def _feed_metric_stage_budget(feed_spec: dict, theta_value: float, ctx: SizingContext) -> None:
    """`{"type":"metric_stage_budget","metric":"gain_db","devices":[...][,"gm_id"|"gm_id_role"|
    "gm_id_match_vgs_of","vds","vs","gm_id_min","gm_id_max"]}` — `theta_value` 자체가 채널길이
    `L`이다. `gm_id_min`/`gm_id_max`(2026-08-13 세션31 이어, 선택, `gm_id_role`과만 조합)는
    `search_gm_id_for_role()`이 스캔할 `gm_id_grid`를 이 범위로 좁힌다 -- 실측 근거: 실제
    sky130 LUT에서 `gm_id_role="matching"`이 격자 하한(2.0, 깊은 strong inversion)까지
    밀리면 gm/gds<1(음수 dB)로 무너지는 소자가 있었다(gm-id-methodology.md 491행
    "moderate~strong inversion"이 원문 권고이지 극단이 아님). 지정 안 하면 기존 동작과
    100% 동일(전체 격자, 하위호환). 지정된
    `devices`(이미 `ID`가 확정돼 있어야 함, A/B엔진 이후에만 호출)의 `L`/`W`/`gm`/`gds`를
    이 `L`에서 재계산해 `ctx.sized`에 반영한다(F엔진 `gain_stages_sum` metric이 바로 이
    값을 읽음). gain 외 metric(noise/power stage budget)은 아직 미구현(§7.3.2 콜아웃에
    이미 명시된 유보 — 이름은 일반화했지만 핸들러 내부 계산은 gain_db 경로만 실제 동작).

    이 소자(들)의 gm/ID를 정하는 3가지 방법(상호배타, 우선순위 `gm_id_match_vgs_of` >
    `gm_id_role` > `gm_id`(고정) 순 -- 하나만 쓰는 게 정상이라 실제로 겹칠 일은 드묾):

    - `gm_id`(기본 15.0): 고정 gm/ID -- 기존 동작, 하위호환.
    - `gm_id_role`(2026-08-13 세션31 신설, 선택): `"matching"`/`"gain"`/`"balanced"` --
      `search_gm_id_for_role()`(이미 이 프로젝트가 다른 소자들에 쓰는 것과 동일한 역할
      기반 gm/ID 탐색)을 그대로 재사용해 이 소자의 `ID`(이미 확정됨)에 대해 역할에 맞는
      gm/ID를 탐색한다(고정 상수 대신 문헌 근거 있는 탐색 -- gm-id-methodology.md §7.1:
      전류거울/매칭=strong inversion, §2.5=이득단은 gm/gds 최대화). 캐싱된 `_idu_scan()`
      (세션31 B 구현)을 그대로 재사용하므로 재계산 비효율 없음. ⚠️ 이 소자가 같은 공유
      전류 그룹 안에서 다른 소자의 `gm_id_match_vgs_of` 대상이면, 여기서 고른 값은
      **잠정값**일 뿐이다 -- 아래 조인트 스캔이 최종 확정한다. **2026-08-13 정정(사용자
      지적, two_stage_ota M5/M7 확장 계기)**: `devices`가 2개 이상이면 `gm_id_role`은
      **소자마다 각자의 `ID`로 따로 탐색**한다(예전엔 `devices[0]`의 `ID`로 한 번만
      계산해 그룹 전체에 그대로 적용 -- ID가 항상 같은 진짜 matched 미러쌍(M15/M25류)
      에서는 우연히 안전했지만, 같은 `L_role`/`gm_id_role`을 공유해도 ID가 서로 다른
      "독립 전류원 두 개"(예: 1단 tail과 2단 tail이 같은 bias 노드를 읽지만 전혀 다른
      전류인 경우) 그룹에 그대로 쓰면 devices[1]의 실제 W_bounds를 검증 없이 몰래
      벗어날 수 있었다. 소자별 계산은 `_idu_scan()` 캐시가 `(L,vds,vs,gm_id_grid)`만
      키로 쓰고 `ID`는 안 쓰므로 재계산 비효율이 없다(캐시 히트, `W_bounds` 필터+role
      선택만 소자별로 다시 함) -- ID가 같은 기존 그룹은 결과가 100% 동일하게 유지된다.
      **2026-08-13 추가 확장(같은 세션, 사용자 지시)**: `gm_id_role`은 문자열(그룹 전체
      동일 역할, 기존) 또는 `{device_name: role, ...}` dict(소자별 다른 역할)를 받는다.
      두 번째가 필요한 이유(two_stage_ota M5/M7 실측): 같은 L을 공유해야 하는(레이아웃
      행 그룹, `stack_groups_override` 참고) 두 소자가 전기적으로는 완전히 다른 역할일
      수 있다 -- M5(1단 tail, gate=bias)는 gds가 differential gain에 거의 안 들어가(대칭
      차동쌍에서 tail 임피던스는 CMRR에만 영향) `"balanced"`로 충분한데, M7(2단 출력
      부하, 같은 gate=bias를 읽지만 OUT 노드에서 M6과 나란히 stage2 gds를 직접 결정)은
      M4(stage1 부하)와 대칭적으로 `"gain"`이 필요하다 -- 이 둘을 억지로 같은 role로
      묶으면(예: 둘 다 "balanced") M7의 gds가 무너져 전체회로 gain_db가 크게 나빠짐이
      실측 확인됨(gm_id=2.0 바닥까지 밀려 gm/gds<1). dict 미사용시(문자열) 기존 동작과
      100% 동일 -- 하위호환.
    - `gm_id_match_vgs_of`(2026-08-13 세션31 신설, 선택): 고정/탐색 대신 **다른 소자
      이름**을 준다 -- 그 소자의 실제 VGS(이미 `ctx.sized`에 있어야 함, 즉 이 theta가
      처리되기 **전에** 그 소자를 sizing하는 theta가 먼저 처리되도록 `thetas` 배열
      순서를 선언할 것)를 목표로 이 소자의 gm/ID를 `gm_id_for_vgs()`로 직접 역산(탐색
      아님, `_gm_id_curve_cache` 재사용 O(1) 조회)한다.

    용도(`gm_id_role`+`gm_id_match_vgs_of` 조합): class-AB push-pull 출력단처럼 두 상보
    (kind가 다른) 소자가 KCL로 같은 ID를 흘리면서 DC 레벨(VGS)이 일치해야 하는 경우
    (`battery_centering_deviation` metric이 검증하는 바로 그 관계 -- `high_device`=
    `vdd-vgs_pmos`, `low_device`=`vgs_nmos`, 합=vdd 요구가 대수적으로 `vgs_nmos=
    vgs_pmos`로 귀결됨, `_metric_battery_centering_deviation()` 참고): 한쪽 소자는
    `gm_id_role`(예: `"gain"`)로 자유탐색하고, 다른 쪽은 `gm_id_match_vgs_of`로 그
    결과에 종속시킨다 -- `.ai/context.md` 세션31 BI(물리적 실현가능성 실측 확인)/BQ
    (근본원인: "gain" 역할 소자 혼자 자기 gm/gds만 최대화하면 dependent와의 **결합**
    지표를 못 봄 -- N-way 조인트 스캔으로 수정) 참고.

    ⚠️ 이 두 옵션 전부 topology-무관 일반 메커니즘이다(어떤 topology.json도 `metric_
    stage_budget` theta에 이 필드를 선언하면 그대로 적용됨) -- 원문/이 회로 전용 로직
    아님.

    **공유전류 그룹 + N-way 조인트 스캔**(2026-08-13 세션31 BQ, `_build_shared_current_
    joint_plan()`/`_run_shared_current_joint_scan()` 참고): `gm_id_match_vgs_of`로
    gm_id를 compensation의 원래 선택과 다르게 바꾸면, `entry["ID"]`(compensation이 고른
    값)를 그대로 쓸 경우 `gm=gm_id*ID`가 더 이상 그룹 총 gm(topology_fn의 위상보상
    목표)과 일치하지 않게 된다 -- **게다가** "gain"류 root가 자기 소자 하나만 보고
    독립적으로 gm_id를 고르면, dependent와의 **결합** 지표(예: `(gm_root+gm_dep)/
    (gds_root+gds_dep)`)를 최적화하지 못한다(실측 확인, `.ai/context.md` BQ). 이 feed가
    `_build_theta_evaluator()`가 미리 계산해둔 `ctx.derived["_scb_joint_plan_by_
    devices"]`에서 자기 `devices`로 계획을 찾으면(=이 그룹에 닿는 `metric_stage_budget`
    theta 중 **선언 순서상 마지막**이면) 그룹 전체를 결합 지표 기준으로 재확정한다.
    계획이 없으면(그룹에 결합이 없거나 애초에 공유전류 그룹이 아닌 topology) 기존처럼
    per-device 값을 그대로 쓴다(하위호환)."""
    if feed_spec.get("metric", "gain_db") != "gain_db":
        raise ValueError(f"metric_stage_budget 핸들러는 gain_db만 구현됨(§7.3.2 유보) -- "
                          f"{feed_spec.get('metric')!r}은 미구현")
    L = theta_value
    vds, vs = feed_spec.get("vds", 0.6), feed_spec.get("vs", 0.0)
    # 2026-08-19(세션38 연속, two_stage_ota M4/M6 계기 -- 사용자와 함께 재정식화한 원리) --
    # `vds`(위)는 여태 이 feed의 모든 devices에 똑같이 적용되는 하드코딩 상수였다. 그런데
    # M3/M4(이 feed)의 M4는 stage1의 LOAD(출력임피던스)이고 그 drain(O1)이 stage2의 gm 소자
    # M6(compensation 관리)의 게이트를 직접 구동한다 -- VSG(M6)=VSD(M4)가 KVL로 강제되는데
    # vds=0.2는 아무 근거 없는 추정값이었다(실측: M6의 실제 gm_id로 역산한 VSG=1.004V인데
    # M4는 0.2V로 사이징되고 있었음). "load를 거슬러 올라가면 결국 root(differential input
    # 또는 compensation의 진짜 스펙)에 닿는다"는 원리대로, LOAD가 그 root 쪽(compensation
    # 소자)에 맞춰야 한다 -- `device_roles.vds_match_vgs_of`(헤드룸 레벨, 세션38 앞부분
    # 신설)와 정확히 같은 개념을 theta feed 레벨에도 추가한다. `{device_name: ref_device}`
    # dict만 받는다(이 feed의 devices 중 일부만 다운스트림에 물려있을 수 있으므로 -- 예:
    # M3는 diode 레퍼런스 자신이라 이 관계가 없고 M4만 있음. `gm_id_role`처럼 문자열
    # 하나로 그룹 전체에 적용하는 형태는 지원 안 함 -- 물리적으로 그룹의 일부 소자에만
    # 해당하는 관계이지 그룹 공통 속성이 아니므로 오히려 혼동을 줄임).
    vds_match_of = feed_spec.get("vds_match_vgs_of") or {}
    match_device = feed_spec.get("gm_id_match_vgs_of")
    gm_id_role = feed_spec.get("gm_id_role")
    fixed_gm_id = feed_spec.get("gm_id", 15.0)
    target_vgs = None
    if match_device is not None:
        companion = ctx.sized.get(match_device)
        if companion is None or "gm_id" not in companion:
            raise ValueError(
                f"gm_id_match_vgs_of={match_device!r}가 아직 sizing 안 됨 -- 이 theta보다 "
                f"먼저 처리되도록 topology.json의 thetas 배열에서 {match_device!r}를 "
                f"sizing하는 theta를 이 theta보다 앞에 선언할 것")
        companion_lut = ctx.spec["lut_by_kind"][companion["kind"]]
        target_vgs = companion_lut.vgs_for_gm_id(
            companion["gm_id"], companion["L"], companion["vds"], companion.get("vs", 0.0))

    W_bounds = ctx.spec.get("W_bounds", (1e-6, 200e-6))
    devices = feed_spec["devices"]

    # 2026-08-13(세션31 이어, two_stage_ota M3/M4 실측 계기 -- 사용자 지시) -- gm_id_role
    # 검색에 쓸 gm_id_grid를 선택적으로 좁힌다(`gm_id_min`/`gm_id_max`, 둘 다 선택).
    # 근거: `gm_id_role="matching"`(gm/ID 최소화)이 toy LUT에서는 문제없었지만 실제
    # sky130 LUT로는 gm_id_grid 하한(2.0, 깊은 strong inversion/velocity saturation
    # 근처)까지 밀려 gm/gds<1(음수 dB)까지 무너지는 게 실측으로 확인됨(gm-id-methodology.md
    # 491행 "정전류원·전류거울·차동쌍은 mismatch 억제 위해 moderate~strong inversion이
    # 유리" -- "strong inversion 극단"이 아니라 "moderate~strong"이 원문 권고임을 재확인).
    # `gm_id_min`을 주면 이 하한 아래 격자점을 아예 후보에서 제외해 "matching이 유리한
    # 방향(gm/ID를 낮게)으로 가되 gds가 무너지는 극단은 피하는" 절충 구간만 탐색한다.
    # 지정 안 하면(기본) 기존 동작 100% 동일(전체 격자, 하위호환).
    gm_id_min = feed_spec.get("gm_id_min")
    gm_id_max = feed_spec.get("gm_id_max")
    if gm_id_min is not None or gm_id_max is not None:
        _base_grid = feed_spec.get("gm_id_grid") or [i * 0.5 for i in range(4, 61)]
        search_gm_id_grid = [g for g in _base_grid
                              if (gm_id_min is None or g >= gm_id_min)
                              and (gm_id_max is None or g <= gm_id_max)]
        if not search_gm_id_grid:
            raise ValueError(
                f"gm_id_min={gm_id_min}/gm_id_max={gm_id_max}이 gm_id_grid를 전부 걸러내 "
                f"후보가 0개다 -- 범위를 다시 확인할 것")
    else:
        search_gm_id_grid = feed_spec.get("gm_id_grid")

    # 1단계: 이 theta의 소자들이 쓸 gm_id를 정한다. 2026-08-13(세션31 이어, two_stage_ota
    # M5/M7 확장 계기 -- 사용자 지적) **소자별로 각자 계산**한다(예전엔 devices[0]의 ID로
    # 딱 한 번만 계산해 그룹 전체에 그대로 적용했는데, 이건 그룹 소자들이 전부 같은 ID를
    # 갖는다는 암묵 가정이었다 -- M15/M25류 진짜 matched 미러쌍은 이 가정이 맞지만, M5/M7
    # (같은 L_role/gm_id_role을 공유하는 두 "독립된" 전류원, ID는 서로 다름 -- 하나는
    # 1단 tail 전류, 하나는 2단 출력 전류)처럼 ID가 다른데도 이 훅으로 같이 사이징하려는
    # 경우엔 devices[0]의 ID로 고른 gm_id를 나머지 소자에 그대로 강제하면 그 소자의 실제
    # W_bounds를 몰래 벗어날 수 있었다(검증 없이 조용히 통과) -- 소자별 계산으로 각자
    # 자기 ID에 맞는 W_bounds 검증을 받는다. ⚠️ 재계산 비효율 없음: `search_gm_id_for_
    # role()`이 매번 부르는 `lut._idu_scan(L,vds,vs,gm_id_grid)`는 `ID`를 캐시 키에 안 쓰므로
    # (L,vds,vs,gm_id_grid)가 같은 이 그룹 안에서는 스캔 자체가 캐시 재사용된다 -- ID가
    # 같은 기존 그룹(M15/M25 등)은 결과가 100% 그대로(같은 ID -> 같은 탐색 -> 같은 gm_id).
    # `gm_id_match_vgs_of`(target_vgs 경로)는 애초에 ID와 무관한 계산이라(L/vds/vs/target_vgs
    # 만의 함수) 소자별로 달라질 이유가 없어 그대로 한 번만 계산해 공유한다.
    shared_match_gm_id = None
    if match_device is not None:
        lut0 = ctx.spec["lut_by_kind"][ctx.kind_of[devices[0]]]
        shared_match_gm_id = lut0.gm_id_for_vgs(target_vgs, L, vds, vs)

    gm_id_by_device = {}
    vds_by_device = {}
    for name in devices:
        entry = ctx.sized.setdefault(name, {})
        ref = vds_match_of.get(name)
        if ref is not None:
            ref_entry = ctx.sized.get(ref)
            if ref_entry is None or "gm_id" not in ref_entry or "L" not in ref_entry \
                    or ref_entry.get("vds") is None:
                raise ValueError(
                    f"{name}: vds_match_vgs_of={ref!r}가 아직 gm_id/L/vds 미확정 -- compensation."
                    f"stage_devices는 항상 theta보다 먼저 실행되므로(_evaluate() 실행 순서) 보통 "
                    f"이 에러는 {ref!r}가 실제로 compensation.stage_devices에 있는지, 오타는 "
                    f"없는지를 뜻한다")
            ref_lut = ctx.spec["lut_by_kind"][ref_entry["kind"]]
            vds_by_device[name] = ref_lut.vgs_for_gm_id(
                ref_entry["gm_id"], ref_entry["L"], ref_entry["vds"], ref_entry.get("vs", 0.0))
        else:
            vds_by_device[name] = vds
        if "ID" not in entry:
            # 2026-08-13(세션31 이어, two_stage_ota L_mirror_M5 신설 중 발견) -- type "A"
            # root_ratio feed(예: kcl_tail_M5)는 A엔진이 theta 루프 전체가 끝난 뒤 한 번만
            # 돌아 `ctx.sized`에 반영되므로(`_feed_root_ratio()` docstring 참고), 같은
            # 루프 패스 안에서 바로 뒤에 오는 metric_stage_budget theta가 그 소자를
            # 참조하면 `ctx.sized`엔 아직 없고 `ctx.seed_currents`에만 있다 -- 이건
            # `_feed_root_ratio()`가 자기 reference를 찾을 때 이미 쓰는 것과 정확히 같은
            # 폴백(`_ref_id()`)을 여기도 적용하면 된다(체이닝 자체는 이미 있던 개념, 이
            # feed 타입 조합에 처음 걸린 것뿐).
            if name in ctx.seed_currents:
                entry["ID"] = ctx.seed_currents[name]
            else:
                raise ValueError(
                    f"{name}의 ID가 아직 없다 -- metric_stage_budget은 ID가 이미 "
                    f"확정된 뒤(A/B엔진 이후, 또는 같은 패스 안 앞선 'A' theta의 seed)에만 "
                    f"L을 배정할 수 있다")
        if match_device is not None:
            gm_id_by_device[name] = shared_match_gm_id
        elif gm_id_role is not None:
            # 2026-08-13(세션31 이어, two_stage_ota M5/M7 계기 -- 사용자 지시) -- gm_id_role이
            # dict({device: role})면 소자별로 다른 역할을 쓴다(레이아웃 행은 그대로 L 하나를
            # 공유하되, 전기적으로 다른 역할의 소자를 억지로 같은 기준에 맞추지 않기 위함 --
            # 예: M5(tail, gds가 이득에 안 중요)="balanced", M7(2단 출력부하, gds가 이득에
            # 직결)="gain"). 문자열이면 기존처럼 그룹 전체에 동일 적용(하위호환).
            this_role = gm_id_role.get(name) if isinstance(gm_id_role, dict) else gm_id_role
            lut = ctx.spec["lut_by_kind"][ctx.kind_of[name]]
            gm_id_by_device[name] = search_gm_id_for_role(
                lut, L, vds_by_device[name], vs, entry["ID"], this_role, W_bounds,
                gm_id_grid=search_gm_id_grid)
        else:
            gm_id_by_device[name] = fixed_gm_id
    for name in devices:
        _metric_stage_budget_finalize(
            ctx, name, gm_id_by_device[name], ctx.sized[name]["ID"], L, vds_by_device[name], vs)

    # 2단계: 이 feed가 어느 공유전류 그룹의 "마지막"(선언순서) feed면 N-way 조인트
    # 스캔을 돌려 그룹 전체를 재확정한다 -- `_build_theta_evaluator()`가 정적으로
    # 미리 계산해둔 계획을 찾아볼 뿐, 여기서 그래프를 다시 만들지 않는다(재계산 없음).
    plan = ctx.derived.get("_scb_joint_plan_by_devices", {}).get(tuple(devices))
    if plan is not None:
        _run_shared_current_joint_scan(plan, ctx)


_THETA_FEED_REGISTRY: dict = {
    "settling_split":       FeedHandler(_feed_settling_split, touches=["B"]),
    "C":                    FeedHandler(_feed_diode_stack_target, touches=["C"]),
    "B":                    FeedHandler(_feed_gm_target_convention, touches=["B"]),
    "A":                    FeedHandler(_feed_root_ratio, touches=["A"]),
    "const":                FeedHandler(_feed_root_const, touches=["A"]),  # 세션35
    "A_signed":             FeedHandler(_feed_root_signed_sum, touches=["A"]),  # 세션6
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


def validate_theta_declaration_order(meta: dict) -> list:
    """`topology.json`의 `sizing_roles.theta` 배열이 "선언 순서=실행 순서"라는 이 엔진의
    암묵적 계약(`optimize_full_circuit_budget()`의 `for theta in thetas:` 루프가 배열
    순서 그대로 `apply_theta_feed()`를 부름)을 실제로 만족하는지 **읽기 전용**으로
    검사한다(topology.json을 고치지 않음, 2026-08-13 세션31 신설).

    이 계약을 어기는 순서 오류가 이 프로젝트에서 **실제로 두 번** 발생했다(`mirror_M18a`가
    K_replica/kcl_battery_M18b보다 반드시 앞서야 하는데 한 번 실패한 뒤 수동 정정된 전례,
    `topology.json` `mirror_M18a` 주석 참고 -- 그리고 `L_stage2out_p`/`L_stage2out_n`이
    K_replica/mirror_M18a보다 뒤에 있어 M9a/M18a가 M15/M16의 stale한 compensation-직후
    상태를 replica로 복제하던 세션31 버그, `.ai/context.md` BI~BL 참고) -- 이 함수는 이
    반복되는 실수 클래스를 자동으로 잡아내는 안전망이다.

    검사 대상(다른 소자의 **완전한** `ctx.sized` 항목 -- gm_id/L/vds/W 등, ID 하나만이
    아님 -- 이 필요한, fallback 없는 강한 의존만):
    - `metric_stage_budget`의 `gm_id_match_vgs_of` -- 참조되는 소자를 sizing하는 theta가
      먼저 나와야 함.
    - `C`타입의 `reference` -- 마찬가지.

    ⚠️ `A`/`A_signed`타입의 `reference`/`terms[].device`는 이 함수의 검사 대상이 **아니다**
    -- `_feed_root_ratio()`/`_feed_root_signed_sum()`가 `ctx.seed_currents` fallback을
    이미 갖고 있어(각 함수 docstring 참고) ID만 있으면 되고 seed 단계여도 통과 가능하다 --
    완전한 `ctx.sized` 항목을 요구하는 강한 의존과는 다른, 더 관대한 별개 계약이다.

    compensation이 관리하는 소자(`meta["compensation"]["stage_devices"]`)는 theta 루프
    시작 전에 이미 완전히 sizing되므로 처음부터 "생산됨"으로 취급한다.

    **N-way 공유전류 조인트 스캔의 metric 의존성**(2026-08-13 세션31 BQ 신설): 어떤
    공유전류 그룹의 "마지막"(선언순서) `metric_stage_budget` feed는 `_run_shared_
    current_joint_scan()`이 `compute_metric()`으로 `plan["metric"]`(topology.json이
    선언한 것 그대로)을 평가한다 -- 그 metric이 참조하는 **다른 스테이지 소자**(예:
    `gain_stages_sum`의 다른 stage들)가 이 시점에 아직 안 sizing돼 있으면 `KeyError`로
    죽거나(최소한 명확한 실패) 조용히 틀린 값을 낼 위험이 있다(설계 리뷰 중 발견 --
    실제 검증 없이 "일반화됐다"고 주장할 뻔한 지점). `_build_shared_current_joint_
    plan()`을 그대로 재사용해 어느 feed가 실제 트리거인지 판정하므로(런타임 엔진과
    **같은 정의**, 별도 근사 아님) 오탐/누락이 없다.

    반환: 위반 목록 `[{"theta": name, "problem": str}, ...]` -- 비어 있으면 전부 정상."""
    thetas = ((meta.get("sizing_roles") or {}).get("theta")) or []
    metrics_specs = ((meta.get("sizing_roles") or {}).get("metrics")) or {}
    produced = set()
    comp = meta.get("compensation")
    if comp:
        for grp in (comp.get("stage_devices") or []):
            produced.update(grp)
    scb_plans = {}
    for group_members in _shared_current_groups_from_compensation(comp):
        plan = _build_shared_current_joint_plan(group_members, thetas)
        if plan is not None:
            scb_plans[plan["trigger_devices_key"]] = plan
    violations = []
    for t in thetas:
        feed = t["feeds"]
        if not isinstance(feed, dict):
            continue  # settling_split(문자열) -- 소자 sizing 없음, 의존/생산 둘 다 없음
        ftype = feed.get("type")
        if ftype == "metric_stage_budget" and feed.get("gm_id_match_vgs_of"):
            dep = feed["gm_id_match_vgs_of"]
            if dep not in produced:
                violations.append({"theta": t["name"],
                    "problem": f"gm_id_match_vgs_of={dep!r}를 참조하지만 {dep!r}를 "
                               f"sizing하는 theta가 아직 선언 안 됨(순서 확인 필요)"})
        elif ftype == "C":
            dep = feed.get("reference")
            if dep is not None and dep not in produced:
                violations.append({"theta": t["name"],
                    "problem": f"reference={dep!r}를 참조하지만 {dep!r}를 sizing하는 "
                               f"theta가 아직 선언 안 됨(순서 확인 필요)"})
        if ftype == "metric_stage_budget":
            plan = scb_plans.get(tuple(feed.get("devices", [])))
            if plan is not None:
                mspec = metrics_specs.get(plan["metric"], {})
                for stage in mspec.get("stages", []):
                    for dname in stage:
                        if dname not in produced:
                            violations.append({"theta": t["name"],
                                "problem": f"공유전류 조인트 스캔이 metric={plan['metric']!r}"
                                           f"을 평가해야 하는데 그 metric이 참조하는 "
                                           f"{dname!r}를 sizing하는 theta가 아직 선언 "
                                           f"안 됨(순서 확인 필요)"})
            produced.update(feed.get("devices", []))
        elif ftype in ("C", "B"):
            target = feed.get("target")
            if target is not None:
                produced.add(target)
    return violations


_CONSTRAINT_OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt,
                   "<": operator.lt, "==": operator.eq}


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class InfeasibleSizingError(ValueError):
    """2026-08(세션6) 신설 -- 특정 theta 격자점이 **물리적으로 불가능한 상태**(예: KCL 뺄셈
    (`A_signed`)이 음수 전류를 만듦, current_reuse_telescopic_ota의 `kcl_battery_M9b`=
    `ID(M8)-ID(M9a)`를 K_replica/r_classab_src 격자 조합에 따라 음수로 만들 수 있음을
    세션6에서 실측 발견)를 만들 때 낸다 — grid search 루프가 이걸 "이 조합은 infeasible,
    다음으로" 취급하고 계속 진행하게 하려고 `ValueError`를 상속한 별도 타입으로 분리했다.

    `ValueError`를 그대로 상속해서 이 예외를 몰라도 되는 기존 `except ValueError` 코드
    (self-test 등)는 그대로 동작한다 -- 다만 grid search 루프는 **이 타입만** 콕 집어
    "물리적으로 말이 안 되는 조합이니 건너뛴다"로 다루고, 그 외의 `ValueError`(L/VDS
    미확정, 등록 안 된 feed 타입 등 -- 진짜 선언 누락)는 여전히 즉시 크래시해서 알린다
    (§ do.md 7.3.2 "AI가 그 자리를 코드로 메우지 않고 신호를 그대로 돌려받는다" 원칙과
    구분: 이건 "선언이 없다"가 아니라 "선언은 있는데 이 특정 theta 값 조합에서 물리적으로
    불가능하다"는 다른 종류의 신호라 별도 처리가 맞다).

    2026-08-11(세션29) -- `sized_snapshot`(선택) 추가: 예외가 나는 시점의 `ctx.sized`
    스냅샷을 담아둔다. `extract_linear_feasibility_constraints()`가 A_signed 부호제약을
    유도할 때, 바로 이 예외를 촉발한 조합에서 항(term) 소자들의 실제 ID를 읽어야 하는데
    `ctx`는 `_evaluate()`의 지역변수라 예외가 밖으로 전파되면 정상적으로는 접근할 수 없다
    -- 메시지 문자열을 파싱하는 대신 이 속성으로 깨끗하게 노출한다. 기존 호출부(메시지만
    쓰는 `except InfeasibleSizingError`)는 이 속성을 몰라도 그대로 동작한다(하위호환)."""

    def __init__(self, message: str, sized_snapshot: dict | None = None):
        super().__init__(message)
        self.sized_snapshot = sized_snapshot


def resolve_stack_layout(transistors: list, matching_pairs: list, device_roles: dict,
                          stack_groups_override: dict | None = None) -> dict:
    """B-5-3 설계(`.ai/context.md` 세션22~25) 중 실제로 비어있던 조각 하나만 채운다 --
    2026-08-10 정밀조사(Explore 조사) 결과, B-5-3이 "새로 만들어야 한다"고 제안했던
    finger_w 탐색(`search_stack_finger_w()`)/오일러 재시도(`suggest_pair_finger_
    adjustments()`)/매칭 완화(`run_matching_safety_with_finger_growth()`)는 전부 이미
    구현·배선돼 있었다(`assign_finger_geometry()`가 그룹별로 `search_stack_finger_w()`를
    이미 호출하고, `run_topology_pipeline_with_finger_fixup()`/`run_matching_safety_
    with_finger_growth()`가 실패시 재시도까지 이미 오케스트레이션함) -- 진짜 빈 구멍은
    이 함수들이 공통으로 입력받는 **1차 물리 그룹 분할 경계**(`stack_groups_geometry`,
    지금까지 `geometry_colocation_union()`의 자동 추론 하나뿐이었다)를 사람이 선언한
    `vertical_stack_id`로 대체하는 부분뿐이었다.

    **우선순위**(높은 것부터, 완전한 하위호환 원칙 -- 기존 동작을 깨지 않고 새 소스를
    윗단에 끼워 넣는다):
    1. `stack_groups_override`(spec 레벨 명시적 override, 기존 그대로 최우선 -- 이 회로
       인스턴스에서만 유효한 수동 지정이라 선언된 값보다도 더 구체적인 신호이므로).
    2. `device_roles.*.vertical_stack_id` **declared**(topology.json, 사람이 검토/확정한
       값 -- 프로젝트 원칙: topology.json이 유일한 토폴로지 소스). 일부 소자만 채워져
       있으면(gap) 나머지는 각자 singleton 그룹으로 남긴다 -- gap난 소자를 candidates나
       geometry_colocation_union으로 자동 채우면 "사람이 검토한 값"과 "자동 추론값"이
       한 그룹 안에 섞여 신뢰도가 불명확해지므로, 채우는 대신 gap 자체를 눈에 보이게
       남겨 다음 세션에 사람이 채우도록 유도한다(이 프로젝트 반복 패턴, `.ai/context.md`
       세션24 `vertical_stack_id` 15개 gap도 이렇게 손으로 채웠다).

       ⚠️ **2026-08-10 신설(같은 세션 대화 후속)**: declared 값을 그룹으로 조립하기
       *전에* `audit_vertical_stack_id_vs_kcl()`(`stick_diagram.py`)로 declared
       `vertical_stack_id`가 KCL 현실과 정합하는지 먼저 확인한다 -- `hub_findings`에
       `candidate_hub_nets`가 빈(원인 불명) 항목이 있거나 `boundary_findings`에 gap
       (`note` 있음) 항목이 있으면 **`ValueError`로 즉시 멈춘다**(사용자 확정,
       "review 대상 있으면 명시적 에러" -- `optimize_full_circuit_budget()`이 필수
       선언 누락에 이미 적용 중인 "AI가 그 자리를 코드로 메우지 않고 신호를 그대로
       돌려받는다" 원칙과 동일). `internal_series`/`declared_matching_pair`로 설명되는
       boundary나 3+ 단자 net으로 설명되는 hub는 전부 정상(항상 있을 수 있는 경우)이라
       통과 -- 오직 **원인을 알 수 없는** 불일치만 막는다. candidates 폴백(3번)에는
       적용하지 않는다(analog-grammar 제안 자체가 이미 `ambiguous_*` 격리로 자기
       불확실성을 표시하므로 별도 audit이 불필요).
    3. declared가 통째로 비어있는 회로(예: `folded_cascode.topology.json` -- 실측 확인
       됨, `device_roles` 키 자체가 없음) -- `refine_differential_and_mirror_relations()`
       의 `vertical_stack_id_candidates`(analog-grammar 기반 제안)로 폴백.
    4. analog-grammar 자체가 없어 candidates도 `None`이면 `geometry_colocation_union()`
       (레거시 자동 추론)으로 최종 폴백 -- 이 함수가 아예 없던 회로/환경에서도 완전한
       하위호환을 보장한다.

    ⚠️ **2026-08-10 신설, 2026-08-11(세션28 후반부) `derive_horizontal_stack_groups()`로
    교체**: 2번(declared)/3번(candidates) 둘 다 최종 반환 전에
    `derive_horizontal_stack_groups(transistors, groups, matching_pairs)`를 거친다 --
    `vertical_stack_id`는 전기적 VDD->GND 컬럼(무엇이 직렬로 쌓였는가)만 답해서 두 가지
    문제가 있다: (1) 매칭 파트너가 서로 다른 물리 branch에 있으면(예: `folded_cascode`의
    `M1`/`M2` 차동입력쌍) 항상 그룹이 갈라져 `audit_row_split()`의 3b/3c(interdigitation/
    common-centroid)가 실패한다(실측 확인, `folded_cascode` 5개 매칭쌍 전부). (2) 정의상
    PMOS/NMOS 경계를 넘나든다(예: `output_stage_a` class-AB 출력단이 M15=pmos/M16=nmos를
    한 컬럼으로 묶음) -- 물리 레이아웃 행(Euler trail)은 같은 kind만 diffusion을 공유할
    수 있으므로 이 그룹을 그대로 물리 행으로 쓸 수 없다(2026-08-11 `build_graph()` kind
    동질성 하드 게이트로 발견). `derive_horizontal_stack_groups()`는 먼저 kind로 쪼갠 뒤
    `merge_layout_groups_by_matching_pairs()`(선언된 매칭쌍만으로 그룹과 그룹을 잇는
    안전한 union-find, `geometry_colocation_union()`의 위험한 재귀적 connectivity climb
    없음)로 대칭 branch를 재병합해 두 문제를 함께 푼다 -- `matching_pairs`(이미 이 함수가
    받는 인자, `optimize_full_circuit_budget()`은 `current_forced=True`만 필터링해 넘김)가
    병합 기준이자 유일한 선택지다(세션9/10 실측: 전체 matching_pairs를 병합 기준으로 쓰면
    무관한 hub를 끌고 들어와 매칭 품질이 악화된 선례가 있어, `current_forced=True`만
    넘기는 게 안전한 기본값). 4번(legacy)에는 적용 안 함(이미 자체적으로 매칭쌍 기반
    병합을 하는 함수라 중복).

    반환은 `kcl_series_union()`/`geometry_colocation_union()`과 동일한 계약
    `{stack_id: [device_name, ...]}` -- `assign_finger_geometry()`에 그대로 넘길 수 있다.

    ⚠️ candidates 폴백 경로(3번)는 `refine_differential_and_mirror_relations(transistors)`를
    `inputs=()` 기본값으로 호출한다 -- Test 38(`stick_diagram.py`)이 실측으로 보여주듯 이
    함수는 `inputs=` 선언 없이도 `find_differential_pair_candidates()`의 자동 승격
    루프로 스스로 입력을 찾아낸다. `topology.json`의 `ports` 선언(있으면)을 아직 파싱해
    넘기지 않는 건 의도적 축소(정직한 한계) -- 이번 세션은 `current_reuse_telescopic_
    ota`(declared 경로, 2번)로만 실측 검증했고 candidates 경로(3번)는 `folded_cascode`
    교차검증에서 `ports` 없이도 동작하는지까지만 확인했다(ports 파싱은 필요해지면 추가)."""
    if stack_groups_override:
        return stack_groups_override

    declared = {name: entry.get("vertical_stack_id")
                for name, entry in device_roles.items()
                if isinstance(entry, dict) and entry.get("vertical_stack_id")}
    if declared:
        audit = audit_vertical_stack_id_vs_kcl(transistors, matching_pairs, device_roles)
        review_needed = (
            [f for f in audit["hub_findings"] if not f["candidate_hub_nets"]] +
            [f for f in audit["boundary_findings"] if f["note"]])
        if review_needed:
            raise ValueError(
                f"declared vertical_stack_id가 KCL 현실과 안 맞는데 원인을 설명할 수 없는 "
                f"지점이 {len(review_needed)}건 있습니다(audit_vertical_stack_id_vs_kcl()) -- "
                f"{review_needed}. hub_findings의 candidate_hub_nets가 비어있으면 그 "
                f"vertical_stack_id 그룹이 왜 KCL로 여러 그룹으로 갈리는지 3+단자 net으로도 "
                f"설명이 안 된다는 뜻(선언 재검토 필요), boundary_findings에 note가 있으면 "
                f"한쪽만 vertical_stack_id가 선언된 gap입니다. topology.json의 device_roles를"
                f" 정정하거나 gap을 채운 뒤 다시 시도하세요.")
        groups = defaultdict(list)
        for name, sid in declared.items():
            groups[sid].append(name)
        for t in transistors:
            if t.name not in declared:
                groups[t.name].append(t.name)
        return derive_horizontal_stack_groups(transistors, dict(groups), matching_pairs)

    refined = refine_differential_and_mirror_relations(transistors)
    if refined is not None and refined.get("vertical_stack_id_candidates"):
        groups = defaultdict(list)
        for name, sid in refined["vertical_stack_id_candidates"]["groups"].items():
            groups[sid].append(name)
        return derive_horizontal_stack_groups(transistors, dict(groups), matching_pairs)

    return geometry_colocation_union(transistors, matching_pairs)


def _metric_stage_budget_vds_by_device(thetas: list) -> dict:
    """`metric_stage_budget` theta feed가 고정하는 `{device: vds}`를 `thetas` 전체에서
    한 번 뽑아낸다(기본 0.6, `_feed_metric_stage_budget()`과 동일 기본값). `thetas`는
    한 `_build_theta_evaluator()` 호출 동안 불변이므로, `reserved_vds_for_other_stack_
    members()`가 그룹 멤버마다 이 스캔을 반복하지 않도록 호출부가 미리 한 번만 만들어
    넘긴다(2026-08-13 세션31 감사 발견 -- 그전엔 멤버마다 `thetas` 전체를 재스캔했다)."""
    metric_stage_budget_vds = {}
    for t in thetas:
        feed = t["feeds"]
        if isinstance(feed, dict) and feed.get("type") == "metric_stage_budget":
            v = feed.get("vds", 0.6)
            for d in feed.get("devices", []):
                metric_stage_budget_vds[d] = v
    return metric_stage_budget_vds


def reserved_vds_for_other_stack_members(vsid: str, exclude_devices, device_roles: dict,
                                          metric_stage_budget_vds: dict,
                                          min_vds_by_role: dict) -> float | None:
    """`vsid`(vertical_stack_id, VDD~GND 물리적 전기 컬럼) 그룹에서 `exclude_devices`(지금
    compensation이 VDS를 정하려는 스테이지 자신의 소자들)를 뺀 나머지 멤버가 이미
    확정적으로/최소한으로 필요로 하는 VDS 합을 반환한다 — `optimize_multistage()`의
    B엔진이 VDS를 `vertical_stack_id`와 무관한 완전 자유변수로 다루던 근본 문제(harness
    연동 감사로 발견, `.ai/context.md` 세션30 -- L_candidates를 densify하자 이 자유도가
    실제로 KVL을 위반하는 값(예: VDS=vdd 전체)을 찾아냈다)를 고치기 위해 신설.

    나머지 멤버를 두 갈래로 분류해 합산한다:
    - `metric_stage_budget_vds`(`_metric_stage_budget_vds_by_device(thetas)`가 미리 뽑아둔
      `{device: vds}` -- 호출부가 그룹 멤버 루프 밖에서 한 번만 만들어 넘긴다)에 속하면
      그 고정값 그대로.
    - `device_roles`에 `headroom_role`이 선언돼 있으면 `min_vds_by_role[role]`(기본 0.2)
      -- `allocate_stack_headroom()`이 실제로 배정할 값의 하한(최소 보장치)이므로 안전한
      보수적 예약.

    ⚠️ **정직한 한계**: 나머지 멤버 중 위 두 갈래 어디에도 안 걸리는 소자가 있으면(예:
    다른 `compensation.stage_devices` 그룹과 같은 vsid를 공유 -- 서로가 서로의 결과를
    필요로 하는 상호참조라 이 시점엔 아직 못 품) `None`을 반환한다 -- 잘못 추측해서
    상한을 씌우는 것보다 기존처럼 무제한으로 두는 게 안전하다(호출부가 이 경우 VDS
    상한을 적용하지 않는다)."""
    members = [m for m, dr in device_roles.items() if dr.get("vertical_stack_id") == vsid]
    reserved = 0.0
    for m in members:
        if m in exclude_devices:
            continue
        if m in metric_stage_budget_vds:
            reserved += metric_stage_budget_vds[m]
        elif device_roles.get(m, {}).get("headroom_role"):
            role = device_roles[m]["headroom_role"]
            reserved += min_vds_by_role.get(role, 0.2)
        else:
            return None
    return reserved


def make_replica_feasibility_check(grp, thetas: list, device_roles: dict, kind_of: dict,
                                    spec: dict):
    """`grp`(지금 compensation이 L/VDS를 정하려는 스테이지 소자들)를 `reference`로 삼는
    C타입(`_feed_diode_stack_target()`) replica theta feed가 있으면, 그 `target` 소자가
    이 스테이지의 후보 (L,VDS,gm_id,ID)에서도 자기 `gm_id_role`/`W_bounds`를 만족할 수
    있는지 확인하는 `find_optimal_sizing(..., extra_feasible=...)`용 콜백을 만든다.
    해당하는 replica가 없으면(대부분의 스테이지) `None`(체크 없음, 하위호환).

    2026-08-12(세션30) 신설 -- `reserved_vds_for_other_stack_members()`(VDS 헤드룸
    근본수정)와 짝을 이루는, **L 선택**의 하류 파급 근본수정. 실측으로 발견(harness 연동
    감사, `.ai/context.md` 세션30): `optimize_multistage()`가 스테이지 자신의 objective
    (power/area)만 보고 L을 고르면, K_replica로 그 L을 물려받는 M9a 같은 소자가
    `search_gm_id_for_role()`의 W_bounds를 못 맞추는 경우가 실제로 있었다(M15가 area
    최소화로 더 작은 L=0.235µm을 진짜로 고르는 게 이득이라 동점이 아니었음 -- L_candidates
    를 densify하기 전엔 4개 앵커점 중 우연히 다 괜찮은 것만 있어서 드러나지 않았다).

    ⚠️ **theta_values(예: K_replica 자체 비율)는 이 시점에 아직 안 정해졌다**(compensation
    은 A/C엔진보다 먼저 실행되고, comp_params로 캐싱돼 theta 조합마다 다시 안 돈다) --
    그래서 정확한 한 점이 아니라 **theta의 declared bounds 양끝**(예: K_replica
    [0.05,0.2])에서 타겟의 ID_target(=ratio*ID)을 계산해 **둘 다** feasible해야 통과시킨다
    (`W = ID*L/IDu(gm_id,L,vds)`가 고정 gm_id/L/vds에서 ID에 선형이라, 양끝이 통과하면
    그 사이 전부 안전하다는 보수적 근거)."""
    replicas = []
    for t in thetas:
        feed = t["feeds"]
        if isinstance(feed, dict) and feed.get("type") == "C" and feed.get("reference") in grp:
            target = feed["target"]
            role = device_roles.get(target, {}).get("gm_id_role")
            if role is None:
                continue  # gm_id_role 없으면 search_gm_id_for_role() 대상 자체가 아님
            replicas.append((target, tuple(t["bounds"]), role))
    if not replicas:
        return None
    W_bounds = spec.get("W_bounds", (1e-6, 200e-6))

    def check(L, VDS, gm_id, ID):
        for target, (lo, hi), role in replicas:
            lut_t = spec["lut_by_kind"][kind_of[target]]
            for ratio in (lo, hi):
                try:
                    search_gm_id_for_role(lut_t, L, VDS, 0.0, ratio * ID, role, W_bounds)
                except InfeasibleSizingError:
                    return False
        return True
    return check


def make_matching_feasibility_check(grp, metrics_specs: dict, constraints: list,
                                     kind_of: dict, spec: dict):
    """`grp`(지금 compensation이 L/VDS/gm_id를 정하려는 스테이지 소자들)를 `devices`로
    선언한 `pelgrom_mismatch` metric에 declared constraint(`<=`/`<`)가 걸려 있으면, 그
    constraint를 만족하는 (L,VDS,gm_id,ID) 후보만 통과시키는 `find_optimal_sizing(...,
    extra_feasible=...)`용 콜백을 만든다. 해당하는 게 없으면 `None`(체크 없음, 하위호환).

    2026-08-13(세션31 BT 후속) -- `make_replica_feasibility_check()`(바로 위, K_replica
    L 하류파급 근본수정)와 **완전히 같은 패턴**: `optimize_multistage()`는 스테이지 자신의
    objective(power/area)만 보고 (L,VDS,gm_id)를 고르는데, `mismatch_sigma_mV` 같은
    declared constraint는 이 시점에 전혀 안 보인다(실측 발견: `current_reuse_telescopic_
    ota`의 M1a/M1b가 power 최소화로 L=0.235µm/W=2.505µm를 골랐는데, `mismatch_sigma_
    mV<=5.0`을 만족하려면 W*L이 지금의 약 4.7배 필요 -- `.ai/context.md` BT 이후 참고).
    스테이지 안의 모든 소자는 같은 (L,VDS,gm_id,ID)를 공유한다는 compensation의 기존
    불변식을 그대로 이용해, `find_optimal_sizing()`이 매 후보마다 이미 계산하는 IDu를
    재조회(`lut.gm_id_to_id_density()`, LUT 실측범위 밖이면 그 후보는 그냥 infeasible)해
    `W=L*ID/IDu`를 얻고 `estimate_mismatch_sigma()`로 직접 판정한다."""
    applicable = []
    grp_set = set(grp)
    for mname, mspec in metrics_specs.items():
        if mspec.get("type") != "pelgrom_mismatch":
            continue
        devs = set(mspec.get("devices") or [])
        if devs and devs <= grp_set:
            for c in constraints:
                if c["metric"] == mname and c["op"] in ("<=", "<"):
                    applicable.append((mspec, c))
    if not applicable:
        return None
    lut = spec["lut_by_kind"][kind_of[grp[0]]]

    def check(L, VDS, gm_id, ID):
        try:
            IDu = lut.gm_id_to_id_density(gm_id, L, VDS, 0.0)
        except ValueError:
            return False
        W = L * ID / IDu
        for mspec, c in applicable:
            vth0_slope = spec["vth0_slope"][mspec["kind"]]
            sigmas = [estimate_mismatch_sigma(vth0_slope, W * 1e6, L * 1e6)
                      for _ in mspec["devices"]]
            sigma_pair_mV = math.sqrt(sum(s * s for s in sigmas)) * 1e3
            if not _CONSTRAINT_OPS[c["op"]](sigma_pair_mV, c["value"]):
                return False
        return True
    return check


def _build_theta_evaluator(topology_path: str, spec: dict) -> dict:
    """`optimize_full_circuit_budget()`의 세타-무관 setup + `_evaluate(theta_values)` 평가
    클로저를 그대로 추출한 헬퍼(2026-08-11 세션29, 순수 리팩터 -- 동작 변화 없음. warm-start
    (`derive_theta_dependency_graph()`/`presolve_warm_start()`)가 grid search 전체를 돌리지
    않고 임의의 theta_values 한 점만 평가해야 해서 신설). `optimize_full_circuit_budget()`은
    이 함수를 호출해 아래 반환값을 그대로 재사용한다 -- 내부 로직은 옮기기 전과 완전히 동일.

    반환: `{"transistors","meta","thetas","metrics_specs","objective","constraints",
    "device_roles","comp","pairs_meta","kind_of","by_name","stack_groups_geometry",
    "stack_groups_kcl","evaluate"}` -- `"evaluate"`가 바로 그 `_evaluate(theta_values) ->
    (ctx, metrics_result)` 클로저다(theta_values에 없는 theta는 적용되지 않은 채 평가됨 --
    호출자가 필요한 theta는 전부 채워 넘길 것, 부분 평가를 원하면 나머지를 bounds-midpoint
    등으로 채워 넣을 것)."""
    transistors, meta = load_topology(topology_path)
    # 2026-08-14(사용자 지시) -- 실제 sizing 계산(아래 device_roles.gm_id_role/L_role 루프,
    # _evaluate()가 thetas가 비어도 최소 1회 실행함)에 들어가기 전에, load_topology()가
    # netlist만으로 자동 제안한(아직 topology.json에 사람이 검토·확정하지 않은) gm_id_role/
    # L_role이 있으면 여기서 막는다 -- current_reuse_telescopic_ota의 L_cascode theta 대상
    # 소자에 이런 제안이 조용히 적용돼 그 theta의 그리드서치를 무력화한 실제 사고(이 세션
    # 실측 재현) 재발 방지. compensation/metric_stage_budget/B/C 대상처럼 구조적으로 안전이
    # 이미 보장된 소자는 require_device_roles_reviewed()가 알아서 제외한다.
    require_device_roles_reviewed(topology_path, meta)
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
    by_name = {t.name: t for t in transistors}

    # 2026-08-11(세션29) -- optimize_multistage()는 comp_params(대개 theta와 무관한 spec
    # 고정값 + settling_split 하나가 채우는 t_lln류)만의 순수함수인데, LUT 격자 전체를
    # 스윕하는 find_optimal_sizing()을 내부에서 여러 stage/그룹마다 도는 탓에 evaluate() 한
    # 번의 비용 중 압도적 비중(프로파일 실측: 8초/call 중 약 3초)을 차지한다. SLSQP 유한차분이
    # 같은 evaluate()를 theta 하나만 바꿔 반복 호출할 때 -- t_lln을 바꾸는 f_slew 자신을
    # 흔드는 경우가 아니면 -- comp_params가 완전히 동일한데도 매번 이 비싼 그리드서치를
    # 새로 돈다는 걸 이번 세션에 실측으로 발견해 결과를 comp_params 값 자체로 캐싱한다
    # (순수함수 메모이제이션 -- optimize_multistage() 자신은 건드리지 않았으므로 다른
    # 호출부/self-test 동작은 전혀 안 바뀐다).
    _comp_cache: dict = {}

    # 2026-08-11(세션28 계속) -- 사용자 통찰: ideal current source(전류 고정, 전압 자유)와
    # ideal voltage source(전압 고정, 전류 자유)는 헤드룸 "합=vdd" 계약에 미치는 영향이
    # 다르다. 일반 스택(양끝이 vdd/gnd 레일)은 KVL로 전압 강하 합이 반드시 vdd와 같아야
    # 하지만(자유도 없음), 그룹의 한쪽 끝이 ideal current source면 그 경계는 "남는 전압을
    # 군말 없이 흡수"하므로 그 제약 자체가 성립하지 않는다(M18_bg 실사례: topology.json의
    # `ideal_sources`에 `Iref`(current_source, terminals=[Vbias1,gnd])가 선언돼 있고,
    # M18_bg의 non-rail 단자가 정확히 Vbias1 -- diode_reference role의 "얇게 배정" 우회가
    # 물리적으로 정당함을 이 선언으로 직접 검증할 수 있다). 아래 singleton thin-role
    # 우회(`_ref_depth`/`referenced_devices` 처리부 근처)가 role 라벨만 믿지 않고 이
    # `ideal_sources` 선언과 실제로 대조하도록 미리 인덱싱한다.
    _rail_nets = frozenset({"vdd", "gnd", "vss"})
    ideal_source_terminals = defaultdict(list)
    for _src in (meta.get("ideal_sources") or []):
        for _net in _src.get("terminals", []):
            ideal_source_terminals[_net].append((_src.get("name"), _src.get("kind")))

    def _thin_singleton_ideal_source_check(device_name):
        """singleton thin-role 그룹이 `allocate_stack_headroom()`의 "합=vdd" 계약을
        우회해도 되는지, role 라벨만 믿지 않고 실제 `ideal_sources` 선언과 대조해
        검증한다. 반환: `(ok, detail)` -- `ok=True`면 non-rail 단자가 declared
        current_source 종단(전압 자유, 남는 예산을 흡수)임을 확인한 것. `ok=False`면
        `detail`에 원인(선언 없음/voltage_source 종단/등)을 담는다."""
        dev = by_name.get(device_name)
        if dev is None:
            return False, f"'{device_name}' 트랜지스터를 찾을 수 없음"
        open_nets = [n for n in (dev.source, dev.drain) if n not in _rail_nets]
        if not open_nets:
            return False, (
                f"'{device_name}'의 양쪽 단자가 전부 레일(vdd/gnd/vss)임 -- "
                f"singleton thin-role 우회가 상정하는 'non-rail 열린 노드' 패턴이 아님")
        for net in open_nets:
            for src_name, src_kind in ideal_source_terminals.get(net, []):
                if src_kind == "current_source":
                    return True, f"{net}가 ideal current_source '{src_name}' 종단(전압 자유)"
                return False, (
                    f"{net}가 ideal '{src_kind}' '{src_name}' 종단인데 current_source가 "
                    f"아님 -- voltage_source 종단은 '합=그 전압'이라는 다른 계약이 필요한데 "
                    f"이 코드베이스가 아직 그 케이스를 지원하지 않음")
        return False, (
            f"'{device_name}'의 non-rail 단자({open_nets}) 중 어느 것도 topology.json의 "
            f"ideal_sources 선언과 안 맞음 -- role={device_roles.get(device_name, {}).get('headroom_role')!r}"
            f"이 thin_roles인데 이 우회를 정당화할 근거가 없음(선언 누락 또는 role 오분류 "
            f"가능성, 재검토할 것)")

    def _fold_group_check(device_name):
        """singleton `fold_group` 우회가 정당한지, 선언(`device_roles.*.fold_group`)만
        믿지 않고 실제 netlist connectivity와 대조해 검증한다(2026-08-15 세션35, 사용자
        지시 "새 기능을 추가해"로 신설). `folded_cascode`의 X/Y 폴딩 노드처럼 서로 다른
        방향에서 온 두 branch가 한 노드에서 합류하는 구조는 `allocate_stack_headroom()`의
        "한 방향 직렬 스택(또는 `budget_reference_device`로 잇는 체인)" 전제 자체를
        벗어난다 -- `_thin_singleton_ideal_source_check()`와 같은 정신(role 라벨만 믿지
        않고 실제 구조로 검증)이지만, 정당화 근거가 `ideal_sources`가 아니라 "같은
        `fold_group`을 선언한 다른 소자와 실제로 같은 net을 공유하는가"다.

        반환: `(ok, detail)` -- `ok=True`면 이 소자의 non-rail 단자가 같은 `fold_group`을
        선언한 다른 소자의 단자와 실제로 겹침(같은 물리적 병합 노드)을 확인한 것."""
        dev = by_name.get(device_name)
        if dev is None:
            return False, f"'{device_name}' 트랜지스터를 찾을 수 없음"
        fold_group = device_roles.get(device_name, {}).get("fold_group")
        if fold_group is None:
            return False, f"'{device_name}'에 fold_group 선언이 없음"
        open_nets = {n for n in (dev.source, dev.drain) if n not in _rail_nets}
        if not open_nets:
            return False, (
                f"'{device_name}'의 양쪽 단자가 전부 레일(vdd/gnd/vss)임 -- "
                f"fold_group 우회가 상정하는 'non-rail 병합 노드' 패턴이 아님")
        siblings = [t.name for t in transistors
                    if t.name != device_name
                    and device_roles.get(t.name, {}).get("fold_group") == fold_group]
        if not siblings:
            return False, (
                f"'{device_name}'과 같은 fold_group({fold_group!r})을 선언한 다른 소자가 "
                f"없음 -- fold_group은 최소 2개 이상의 소자가 같은 노드를 공유할 때만 "
                f"의미가 있음")
        for sib_name in siblings:
            sib = by_name.get(sib_name)
            if sib is None:
                continue
            sib_nets = {n for n in (sib.source, sib.drain) if n not in _rail_nets}
            shared = open_nets & sib_nets
            if shared:
                return True, (
                    f"{sorted(shared)}를 '{sib_name}'과 공유(같은 fold_group={fold_group!r} "
                    f"병합 노드)")
        return False, (
            f"'{device_name}'의 non-rail 단자({sorted(open_nets)})가 같은 fold_group을 "
            f"선언한 소자 {siblings} 중 누구와도 실제로 겹치지 않음 -- fold_group 선언이 "
            f"connectivity와 안 맞음(오분류 가능성, 재검토할 것)")

    # 2026-08-05(세션10) L1 하드컷 -- kind(diff_pair/current_mirror/branch_symmetric/
    # current_matched) 4종 문자열을 폐지하고 독립된 두 축으로 분해했다: 축A
    # `current_forced`(bool, KCL이 실제로 전류를 강제하는가) + 축C `matching_sensitivity`
    # ("ratio"|"offset", 레이아웃 민감도) -- 축B(shares_node)는 connectivity에서 항상
    # 자동 계산되므로 선언하지 않는다. 옛 kind -> 새 축 매핑(34건 전수조사로 확정, 세션8/9):
    # diff_pair=(current_forced=True,offset) / current_mirror=(False,ratio) /
    # branch_symmetric=(False,ratio) / current_matched=(True,ratio).
    #
    # auto_mirror_ratios(2026-08-01 신설, N개 그룹 지원)는 이제 current_forced=True인
    # 쌍이면 diff_pair/current_matched 구분 없이 전부 1:1 시드한다 -- 옛 코드는 kind==
    # "current_matched"만 시드했는데(current_mirror 개명 전례, 아래 kcl_pairs 주석 참고),
    # 그 결과 diff_pair(M37a/M37b)는 auto_mirror_ratios 대상이 아니어서 별도 theta
    # (`N_cmfb_bw_mirror`, current_reuse_telescopic_ota.topology.json)를 손으로 만들어
    # 같은 일을 중복 수행해야 했다(발견 당시 주석: "diff_pair라 current_mirror 자동
    # 시드 대상이 아님"). current_forced 하나로 통일하면 이 gap 자체가 구조적으로
    # 사라진다(그 theta는 이제 중복이지만 해가 되지 않으므로 남겨둔다 -- ctx.sized가
    # 이미 있으면 setdefault라 덮어쓰지 않음).
    auto_mirror_ratios = {(p["names"][0], n): 1.0
                           for p in pairs_meta if p["current_forced"]
                           for n in p["names"][1:]}

    # kcl_series_union()/geometry_colocation_union()(stick_diagram.py, 세션10 L2)는 두
    # 군데 쓰인다 -- (1) A엔진의 stack_id 기반 "같은 전류" 전파(진짜 KCL 사실, 절대
    # override하면 안 됨), (2) assign_finger_geometry()의 "같은 finger_w를 공유할 물리
    # 행" 판단(floorplan 선택이라 override 가능). 자동 병합이 finger_w 비율-호환 안 되는
    # 소자를 한 그룹으로 묶으면(예: 입력쌍과 그 부하 미러는 KCL로 전류는 같아도 W는 전혀
    # 다름) assign_finger_geometry()가 명시적 ValueError로 알려준다(조용히 억지 배정 안
    # 함) -- 그때 호출자가 stack_groups_override(선택)로 (2)만 물리적으로 재구성해
    # 선언한다(cell_groups가 spine_groups를 override하는 것과 같은 패턴) -- (1)은 항상
    # 원본 그대로 쓴다.
    #
    # 두 함수 모두 이제 **같은 선언 쌍 목록**(current_forced=True만)을 받는다 --
    # branch_symmetric/current_mirror(축A=False, "전류가 같다"는 보장이 없는 순수
    # 문서/레이아웃 매칭 선언)는 둘 다에서 제외한다. KCL 쪽은 세션6부터 유지된 이유
    # 그대로(전류 동일성이 보장 안 되는 쌍을 stack_id 병합에 넣으면 그 회로에서 실제로
    # 서로 다른 free theta가 같은 stack에 섞여 ValueError가 난다, 실측 확인됨).
    # geometry 쪽은 **세션9/10에서 새로 정정**된 부분 -- 예전엔 branch_symmetric/
    # current_mirror까지 포함한 전체 matching_pairs를 넘겼는데, 그러면 current_mirror류
    # 문서용 hub 그룹(예: Vbias1의 7-소자 그룹)이 무관한 기능블럭을 다시 끌고 들어와
    # 매칭 품질을 악화시킨다(실측: 섞인 9-member 그룹 dx=6.00 vs 제외한 4-member 그룹
    # dx=3~4, 세션8). 두 union 함수의 **자동 발견 규칙(rule1)이 서로 다르다는 게** 이제
    # 유일한 차이다(kcl_series_union은 레일 제외+극성 무관, geometry_colocation_union은
    # 레일 제외+같은 극성+drain=source만 -- 각 함수 docstring 참고).
    _forced_pairs = [tuple(p["names"]) for p in pairs_meta if p["current_forced"]]
    stack_groups_kcl = kcl_series_union(transistors, _forced_pairs)
    # 2026-08-10(resolve_stack_layout() 신설) -- 1차 물리 그룹 분할 경계를 자동추론
    # (geometry_colocation_union) 대신 사람이 선언한 vertical_stack_id로 대체(우선순위는
    # resolve_stack_layout() docstring 참고). stack_groups_kcl(위 줄, 전기적 KCL 그룹)은
    # 이 교체와 무관 -- A엔진 전류 전파에만 쓰이는 별개의 사실이라 그대로 둔다.
    stack_groups_geometry = resolve_stack_layout(
        transistors, _forced_pairs, device_roles,
        stack_groups_override=spec.get("stack_groups_override"))
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

    # 2026-08-13(세션31 BQ) -- N-way 공유전류 조인트 스캔 계획은 정적 thetas/compensation
    # 선언만의 순수 함수라 evaluate()마다(그리드서치/SLSQP가 수백~수천 번 부를 수 있음)
    # 다시 만들지 않고 여기서(토폴로지 로드 시) 한 번만 만들어 클로저로 재사용한다 --
    # `_evaluate()`는 이 dict를 그대로 `ctx.derived`에 참조로만 꽂는다(재계산 없음).
    _scb_plans = {}
    for _group_members in _shared_current_groups_from_compensation(comp):
        _plan = _build_shared_current_joint_plan(_group_members, thetas)
        if _plan is not None:
            _scb_plans[_plan["trigger_devices_key"]] = _plan

    def _evaluate(theta_values: dict):
        ctx = SizingContext(spec=spec, topology_path=topology_path, kind_of=kind_of)
        ctx.sized.update({k: dict(v) for k, v in spec.get("known_sizing", {}).items()})
        ctx.mirror_ratios.update(auto_mirror_ratios)

        # 2026-08-10(세션27) -- settling_split feed(f_slew)는 do.md §7.3.1 Level1이
        # compensation(Level2)의 t_lln 입력을 정하므로, compensation보다 먼저 적용해야
        # 한다 -- 나머지 A/B/C/A_signed/metric_stage_budget feed는 여전히 compensation
        # 이후(아래 본 루프)가 맞다(compensation이 정한 ID를 참조하는 게 정상 순서, 바로
        # 아래 comp 블록 주석 참고). 이름(f_slew)이 아니라 feed **타입**으로 골라내 다른
        # 회로가 다른 이름을 써도 일반화되게 한다.
        _presolved_theta_names = set()
        for theta in thetas:
            feeds = theta["feeds"]
            feed_type = feeds if isinstance(feeds, str) else feeds.get("type")
            if feed_type == "settling_split" and theta["name"] in theta_values:
                apply_theta_feed(feeds, theta_values[theta["name"]], ctx)
                _presolved_theta_names.add(theta["name"])

        # compensation을 A엔진/theta보다 먼저 실행한다 -- 순서가 중요하다: (1) A엔진의
        # 직렬-스택 전파(예: two_stage_ota의 M3/M4가 M1/M2와 같은 stack_groups 그룹)가
        # compensation이 정한 M1/M2의 ID를 시드로 써야 하고, (2) theta의 "A" root_ratio feed도
        # compensation이 정한 소자의 ID를 참조할 수 있다(예: 배치 7-3 current-reuse의
        # r_biasgen이 신호경로 총전류를 참조). compensation 자체는 (settling_split을 제외한)
        # theta/A엔진 결과에 의존하지 않으므로(topology_fn은 spec + 위에서 미리 적용한
        # settling_split derived값만으로 완전 결정) 먼저 실행해도 안전하다. **2026-08-10
        # (세션27) 정정** -- "spec만으로 완전 결정"은 더 이상 무조건 참이 아니다: settling_split
        # feed(f_slew)가 do.md Level1->Level2 사슬대로 t_lln을 정할 수 있어, 위에서 그 feed만
        # 먼저 적용해뒀다(그 외 모든 theta는 여전히 compensation 이후, 아래 본 루프).
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
            # 2026-08-10(세션27) -- comp["parameters"] 중 위 settling_split이 이미 ctx.derived에
            # 채운 키(예: t_lln)가 있으면 spec의 고정값보다 우선한다(omega_c exposed_params와
            # 같은 우선순위 패턴, 하위호환: derived에 없으면 기존처럼 spec 그대로).
            comp_params = {k: (ctx.derived[k] if k in ctx.derived else spec[k])
                           for k in comp["parameters"]}
            # 2026-08-12(세션30) -- _THETA_FEED_REGISTRY/_METRICS_REGISTRY/_CMRR_ESTIMATOR_
            # REGISTRY/_PSRR_ESTIMATOR_REGISTRY/_REGRESSION_ENGINES는 전부 미등록 키를 친절한
            # ValueError로 즉시 거부하는데, 이 조회만 그 관례에서 빠져 있었다(harness 연동
            # 감사 중 발견 -- 예전엔 run_sizing_pipeline()에만 이 가드가 있었고 그 함수 자신은
            # 죽은 코드라 삭제됨, 실제 harness 경로는 무방비였다). 등록 안 된 함수명은 이제
            # 여기서도 날것의 KeyError 대신 다른 registry와 똑같은 형태의 ValueError로 거부한다.
            if comp["function"] not in _COMPENSATION_REGISTRY:
                raise ValueError(
                    f"topology.json이 참조하는 compensation 함수 '{comp['function']}'이 "
                    f"_COMPENSATION_REGISTRY(허용된 함수 목록)에 없다 -- "
                    f"{sorted(_COMPENSATION_REGISTRY)} 중 하나여야 한다")
            topology_fn = _COMPENSATION_REGISTRY[comp["function"]](**comp_params)
            # 2026-08-10(세션27) -- topology_fn이 omega_c 등을 exposed_params로 노출하면
            # ctx.derived에 옮긴다(spec은 읽기 전용 계약이라 여기서 안 건드림) --
            # _feed_gm_target_convention()이 이걸 spec보다 우선해 읽는다(위 함수 참고).
            ctx.derived.update(getattr(topology_fn, "exposed_params", {}))
            luts = [spec["lut_by_kind"][kind_of[grp[0]]] for grp in stage_devices]
            _comp_cache_key = tuple(sorted(comp_params.items()))
            if _comp_cache_key in _comp_cache:
                comp_result = _comp_cache[_comp_cache_key]
            else:
                # 2026-08-12(세션30, 근본수정) -- optimize_multistage()의 B엔진이 VDS를
                # vertical_stack_id(같은 물리적 VDD~GND 컬럼)와 무관하게 완전 자유변수로
                # 탐색해오던 문제를 고친다(harness 연동 감사로 발견, 상세 배경은
                # reserved_vds_for_other_stack_members() docstring 참고). 스테이지별로
                # 자기 vertical_stack_id를 공유하는 다른 확정 소자(metric_stage_budget
                # 고정 vds / device_roles의 min_vds_by_role)가 필요로 하는 몫을 미리
                # 빼서 VDS_candidates 상한을 계산 -- comp_params(theta_values 무관, spec/
                # device_roles만 의존)로만 결정되므로 위 _comp_cache_key 그대로 안전.
                # 2026-08-13(세션31) -- metric_stage_budget_vds는 thetas 전체를 스캔해 만드는
                # 값인데 thetas는 이 스코프 안에서 불변이므로, 그룹 멤버마다 매번 재스캔하던
                # 걸 루프 밖에서 한 번만 만들어 재사용한다(감사 발견, _metric_stage_budget_
                # vds_by_device() docstring 참고).
                _metric_stage_budget_vds = _metric_stage_budget_vds_by_device(thetas)
                _stage_vds_candidates = []
                for grp in stage_devices:
                    cap = None
                    for name in grp:
                        vsid = device_roles.get(name, {}).get("vertical_stack_id")
                        if vsid is None:
                            continue
                        reserved = reserved_vds_for_other_stack_members(
                            vsid, set(grp), device_roles, _metric_stage_budget_vds,
                            spec.get("min_vds_by_role", {}))
                        if reserved is None:
                            continue
                        member_cap = spec["vdd"] - reserved
                        if cap is None or member_cap < cap:
                            cap = member_cap
                    if cap is None:
                        _stage_vds_candidates.append(spec["VDS_candidates"])
                        continue
                    if cap <= 0:
                        raise ValueError(
                            f"'{grp}' 그룹이 속한 vertical_stack_id의 다른 소자들이 예약한 "
                            f"VDS 합이 vdd({spec['vdd']}V)를 넘어 이 스테이지에 남는 여유가 "
                            f"없다({cap}V) -- topology.json의 min_vds_by_role/"
                            f"metric_stage_budget vds 선언을 확인할 것")
                    filtered = [v for v in spec["VDS_candidates"] if v <= cap]
                    if not filtered:
                        filtered = [min(spec["VDS_candidates"][0], cap)] \
                            if spec["VDS_candidates"] else [cap]
                    _stage_vds_candidates.append(filtered)
                # 2026-08-12(세션30, 근본수정 2/2 -- VDS 헤드룸과 짝) -- L 선택의 하류 파급도
                # 같은 이유로 막는다: K_replica류 C타입 replica feed가 이 스테이지 소자를
                # reference로 삼으면, 그 target이 이 스테이지가 고르는 L에서도 자기
                # W_bounds를 만족하는지 확인하는 콜백을 만들어 넘긴다(make_replica_
                # feasibility_check() docstring 참고 -- gain_min/w_max와 달리 "다른 소자"의
                # 제약이라 topology_fn/luts만으로는 표현 불가, 호출부가 주입).
                # 2026-08-13(세션31 BT 후속) -- 같은 이유로 mismatch_sigma_mV(Pelgrom) 같은
                # declared constraint도 이 스테이지의 (L,VDS,gm_id) 선택 시점엔 전혀 안 보였다
                # (make_matching_feasibility_check() docstring 참고). find_optimal_sizing()의
                # extra_feasible은 콜백 하나만 받으므로 둘 다 있으면 합성(AND)한다.
                def _combine_extra_feasible(*checks):
                    checks = [c for c in checks if c is not None]
                    if not checks:
                        return None
                    return lambda L, VDS, gm_id, ID: all(c(L, VDS, gm_id, ID) for c in checks)

                _stage_extra_feasible = [
                    _combine_extra_feasible(
                        make_replica_feasibility_check(grp, thetas, device_roles, kind_of, spec),
                        make_matching_feasibility_check(grp, metrics_specs, constraints, kind_of, spec))
                    for grp in stage_devices]
                comp_result = optimize_multistage(
                    topology_fn, luts, spec["L_candidates"], _stage_vds_candidates,
                    spec["gm_id_grid"], objective=stage_objective,
                    gain_min=spec.get("stage_gain_min"), w_max=spec.get("stage_w_max"),
                    shared_gm_id_groups=comp.get("shared_gm_id_groups"),
                    stage_extra_feasible=_stage_extra_feasible)
                _comp_cache[_comp_cache_key] = comp_result
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
            # 2026-08-13(세션31) -- shared_gm_id_groups 각 그룹의 gm 합(=topology_fn이 정한
            # 진짜 위상보상 목표, Eq.6류 -- 그룹 내부의 (L,VDS,gm_id) 선택과 무관하게 고정)을
            # 미리 스냅샷해둔다. `_feed_metric_stage_budget()`의 `gm_id_match_vgs_of`가 이
            # 스냅샷을 읽어 `I=gm_total/(gm_id_p+gm_id_n)`로 공유전류를 재계산할 때 쓴다 --
            # 그렇게 안 하면(gm_id만 바꾸고 compensation이 고른 ID를 그대로 두면) 그룹 총
            # gm이 더 이상 topology_fn의 목표와 안 맞게 된다(감사 발견, `.ai/context.md`
            # 세션31 BI/BM 참고). group_of(아래)는 optimize_multistage()의 것과 별개로,
            # 여기 스코프에서만 쓰는 device-name 기준 조회용이다.
            _shared_current_group = {}
            for _sg in (comp.get("shared_gm_id_groups") or []):
                _sg_devices = [name for idx in _sg for name in stage_devices[idx]]
                _sg_gm_total = sum(comp_result["gms"][idx] for idx in _sg)
                for _name in _sg_devices:
                    _shared_current_group[_name] = {"gm_total": _sg_gm_total, "members": _sg_devices}
            if _shared_current_group:
                ctx.derived["_shared_current_group"] = _shared_current_group
                # 2026-08-13(세션31 BQ) -- _build_theta_evaluator()가 토폴로지 로드 시
                # 한 번만 만들어둔 조인트 스캔 계획(정적, thetas 선언만의 함수)을 참조로만
                # 꽂는다(재계산 없음) -- _run_shared_current_joint_scan()이 이걸로 결합
                # 지표(gain_db 등)를 평가하려면 metrics_specs도 같이 필요하다. constraints
                # (BS, tolerance-band 재설계)는 목표 metric 외 다른 declared constraint
                # (예: classab_centering_dev_v<=0.15V)를 조인트 스캔 후보의 feasibility
                # 필터로 그대로 재사용하기 위함 -- 로컬 재정의 없음, 참조만.
                ctx.derived["_metrics_specs"] = metrics_specs
                ctx.derived["_constraints"] = constraints
                if _scb_plans:
                    ctx.derived["_scb_joint_plan_by_devices"] = _scb_plans

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
            if theta["name"] in theta_values and theta["name"] not in _presolved_theta_names:
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
        # 2026-08-14 추가(실측으로 발견한 진짜 버그) -- `metric_stage_budget` theta(예:
        # `L_cascode`, `_feed_metric_stage_budget()`/`_metric_stage_budget_finalize()`)가
        # 관리하는 L도 이 그리드서치 자체가 spec 근거로 확정하는 값이라 동급으로 권위
        # 있다. 빠져 있었을 때: `current_reuse_telescopic_ota`의 M2a/M2b/M3a/M3b(모두
        # `L_cascode` theta 대상)에 `propose_device_roles_gap_fill()`이 자동 제안한
        # `L_role="mirror"`를 실제로 채웠더니, 이 loop가 `L_cascode`의 그리드서치 결과를
        # `select_L_by_role()`의 고정 배수(L_min*2.5)로 조용히 덮어써서 그 theta 탐색
        # 자체를 무력화했다 -- SLSQP가 `gain_db>=75.6` 제약을 76.48에서 74.8로 못 채우는
        # 실제 회귀로 발현(재현 확인됨).
        # 2026-08-14 -- "B"타입(N×ωc 컨벤션, `_feed_gm_target_convention()`)도 같은 이유로
        # 추가(그 함수 docstring 정정 참고) -- 실측 회귀는 metric_stage_budget에서만
        # 재현됐지만, 같은 취약점 클래스라 발견 즉시 선제 수정.
        _AUTHORITATIVE_L_SOURCES = {"compensation", "replica", "metric_stage_budget",
                                      "gm_target_convention"}

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
                            f"matching pair ({_pa},{_pb}, current_forced={_p['current_forced']},"
                            f"matching_sensitivity={_p['matching_sensitivity']})의 L이 서로 다른데"
                            f"(L_{_pa}={_La}, L_{_pb}={_Lb}) 어느 쪽도 spec 기반(compensation/replica)이 "
                            f"아니라(_L_source={_sa!r}/{_sb!r}) 자동으로 우선순위를 가릴 근거가 "
                            f"없다 -- topology.json의 device_roles L_role/L_min_by_kind 선언을 "
                            f"확인할 것")

        vertical_groups = defaultdict(list)
        group_ref_device = {}
        # 2026-08-10(세션27) -- 헤드룸(VDS 예산) 배분은 "같은 전류"(KCL)가 아니라 "같은
        # 물리적 vdd~gnd 컬럼"(vertical_stack_id) 기준이어야 한다는 걸 실제로 확인했다.
        # 한때 stack_id_of(kcl_series_union() 기반)로 바꿔봤으나 two_stage_ota self-test가
        # 즉시 회귀로 잡아냈다 -- stage1(M3 cascode/M4 cascode/M5 tail)은 vsid로는 한
        # 컬럼이지만 KCL로는 갈린다(M5는 차동쌍 전체 전류, M3/M4는 각 branch 전류라 "같은
        # 전류"가 아님 -- 그래도 셋 다 VDD~GND 한 물리적 컬럼이라 VDS 합은 여전히 vdd여야
        # 함). 즉 M11a/M11b(biasgen_vom_battery_a)/M12(..._sink) 문제의 진짜 원인은
        # "그룹핑 기준이 틀림"이 아니라 "vsid 선언 자체가 불완전함"(M12가 원래 같은 물리적
        # 컬럼인데 다른 이름을 받음)이었다 -- 아래에서 vsid 그대로 쓰고, 선언 쪽을
        # 정정한다(device_roles의 M12/M21 vertical_stack_id를 M11a/M11b, M20a/M20b와
        # 합침, topology.json 참고).
        same_as_of = {}
        vds_match_of = {}
        for name, dr in device_roles.items():
            vsid = dr.get("vertical_stack_id")
            if not vsid:
                continue
            vertical_groups[vsid].append(name)
            ref = dr.get("budget_reference_device")
            if ref:
                group_ref_device[vsid] = ref
            # 2026-08-11(세션28 계속) -- budget_reference_device("나머지" 관계, vdd-ref)
            # 로는 표현 못 하는 "동일" 관계(parallel/matched-pair, 예: M7=M6과 물리적으로
            # 같은 두 노드를 구동하는 병렬 tail이라 VDS가 항상 정확히 같아야 함, M36b=M36a
            # 대칭 매칭 파트너) 전용 필드. 헤드룸 예산 계산에 아예 참여하지 않고 참조
            # 소자의 vds를 그대로 복사한다 -- device 단위 선언(그룹 단위인 budget_
            # reference_device와 달리 같은 그룹 안에서도 멤버별로 다른 대상을 참조할 수
            # 있게 함).
            same_as = dr.get("same_as_device")
            if same_as:
                same_as_of[name] = same_as
            # 2026-08-19(세션38 연속, 사용자 지시 "지금 바로 고치자") -- same_as_device("같은
            # 값을 그대로 복사")와 대칭이지만 복사 대상이 다른 물리량인 관계 전용 필드.
            # nmcnr_amplifier의 M204(drain=NodeS2)/M301(gate=NodeS2, source=vss 공유) 계기 --
            # M301의 게이트가 M204의 드레인과 물리적으로 같은 노드라 VGS(M301)=VDS(M204)가
            # KVL로 강제되는데, M301의 gm_id는 compensation(PM_target 기반 gm3)이 독립적으로
            # 정하고 M204의 vds는 headroom이 독립적으로 정해 이 관계가 지금까지 전혀
            # 검증·강제되지 않고 있었다(실측: 두 값이 실제로 어긋남). M301의 gm을 물러서게
            # 하면 Rm=1/gm3(RHP-zero 완전제거 조건) 설계 근거가 깨지므로, 맞춰야 할 건 M301이
            # 아니라 M204의 vds(=M202과 나누는 헤드룸 배분)다.
            vds_match = dr.get("vds_match_vgs_of")
            if vds_match:
                vds_match_of[name] = vds_match

        # 2026-08-11(세션28 다음 최우선①) -- 다른 그룹의 budget_reference_device가 가리키는
        # 소자 집합. 이 소자가 속한 자기 그룹의 헤드룸을 배정할 때 아래에서 참고한다(M5가
        # vbias3_stack의 참조 대상인 것처럼) -- 이런 소자는 "이 그룹이 vdd 전체를 혼자
        # 책임지는 독립 컬럼"이 아니라 이미 다른 신호 경로(예: 진짜 차동쌍 tail)에 걸려있고
        # 그 위에 다른 replica 체인이 참조로 얹혀사는 쪽이다.
        referenced_devices = set(group_ref_device.values())

        # 폴디드 캐스코드처럼 한 vertical_stack_id 그룹이 vdd~gnd 전체가 아니라 vdd~(다른
        # 그룹이 이미 확정한 소자의 드레인 전압)만큼만 예산으로 갖는 경우를 위한 선택적 필드
        # (배치 7-5b, 2026-07-31, NMCNR 회로 계기 -- 사용자와 함께 설계). `budget_reference_
        # device`가 가리키는 소자는 반드시 다른(먼저 처리되는) vertical_stack_id 그룹 소속이어야
        # 하므로, 그 의존관계대로 그룹을 위상정렬한다(순환 참조는 즉시 ValueError). 2026-08-11
        # 세션28 계속 -- `same_as_device` 의존관계도 같은 위상정렬에 포함(그룹 안 아무
        # 멤버든 참조가 있으면 그 대상 그룹이 먼저 풀려야 함). 2026-08-19(세션38 연속) --
        # `vds_match_vgs_of` 의존관계도 동일하게 포함(참조 대상의 gm_id/L/vds가 먼저
        # 확정돼야 VGS를 역산할 수 있음 -- same_as_device와 완전히 같은 위상정렬 요구).
        def _ref_depth(vsid, _seen=frozenset()):
            deps = [group_ref_device[vsid]] if vsid in group_ref_device else []
            deps += [same_as_of[m] for m in vertical_groups[vsid] if m in same_as_of]
            deps += [vds_match_of[m] for m in vertical_groups[vsid] if m in vds_match_of]
            if not deps:
                return 0
            if vsid in _seen:
                raise ValueError(
                    f"vertical_stack_id 그룹 '{vsid}'의 budget_reference_device/"
                    f"same_as_device/vds_match_vgs_of가 순환 참조한다")
            depths = []
            for dep in deps:
                dep_vsid = device_roles.get(dep, {}).get("vertical_stack_id")
                if dep_vsid == vsid:
                    raise ValueError(
                        f"vertical_stack_id 그룹 '{vsid}'의 budget_reference_device/"
                        f"same_as_device/vds_match_vgs_of가 순환 참조한다")
                depths.append(1 + _ref_depth(dep_vsid, _seen | {vsid}))
            return max(depths)

        for vsid in sorted(vertical_groups.keys(), key=_ref_depth):
            members = vertical_groups[vsid]
            # 2026-08-19(세션38 연속) -- vds_match_vgs_of 멤버는 아래 by_vgrp/known_vds_sum
            # 계산이 시작되기 **전에** 먼저 vds를 채운다. _ref_depth() 위상정렬이 참조 대상의
            # 그룹을 먼저 처리하도록 보장하므로 여기 도달했을 때 참조 소자는 이미 gm_id/L/vds가
            # 확정돼 있어야 정상이다(없으면 선언/순환 문제). 이렇게 미리 채워두면 아래 기존
            # by_vgrp 루프가 이 멤버를 "이미 풀린 소자"로 자연스럽게 인식해(line ~4374의
            # `ctx.sized.get(gm,{}).get("vds") is not None` 체크) known_vds_sum에 정확히
            # 반영되고, 같은 그룹의 나머지 멤버(예: M204와 짝인 M202)가 vdd에서 이 값을 뺀
            # 진짜 나머지 예산을 받는다 -- 아래 코드는 단 한 줄도 안 건드림(재사용).
            for m in members:
                if m not in vds_match_of or ctx.sized.get(m, {}).get("vds") is not None:
                    continue
                ref = vds_match_of[m]
                ref_entry = ctx.sized.get(ref, {})
                if "gm_id" not in ref_entry or "L" not in ref_entry or ref_entry.get("vds") is None:
                    raise ValueError(
                        f"'{m}'의 vds_match_vgs_of('{ref}')가 아직 gm_id/L/vds 미확정 -- 참조 "
                        f"소자가 속한 vertical_stack_id 그룹이 먼저 풀려야 한다(순환/선언 확인), "
                        f"또는 '{ref}'의 gm_id가 compensation/metric_stage_budget/"
                        f"gm_target_convention/gm_id_role 중 하나로 확정 가능한지 확인할 것")
                ref_lut = spec["lut_by_kind"][ctx.kind_of[ref]]
                target_vgs = ref_lut.vgs_for_gm_id(
                    ref_entry["gm_id"], ref_entry["L"], ref_entry["vds"], ref_entry.get("vs", 0.0))
                ctx.sized.setdefault(m, {})["vds"] = target_vgs
            # matching_pairs로 묶인 값-동일 그룹(_vfind)당 대표 1개씩만 집계 -- diff pair/미러
            # 쌍의 두 소자를 헤드룸 예산에 중복으로 합산하지 않기 위함(위 _vfind 주석 참고).
            # 2026-08-10(세션27) 정정 -- 이전엔 members 리스트에서 "먼저 나온" 소자를 무조건
            # 대표로 써서 vds 여부를 검사했다. 그런데 값-동일 그룹의 두 소자가 vds를 채우는
            # 경로가 다를 수 있다(실제 사례: M37a/M37b -- N_cmfb_bw B타입 feed가 target
            # M37a의 vds를 직접 채우지만, 그 짝을 잇는 N_cmfb_bw_mirror A타입 feed는 전류만
            # 전파하고 vds는 안 건드림) -- 이 경우 마침 vds 없는 쪽(M37b)이 먼저 나오면 이미
            # 풀린 그룹을 "미해결"로 오판했다. 그룹 멤버 전체에서 **이미 vds가 있는 소자가
            # 하나라도 있으면** 그 값을 쓰고(대표를 미리 정하지 않음), 전부 없을 때만 미해결
            # 대표(headroom_role이 있는 소자 우선)를 고른다.
            by_vgrp = defaultdict(list)
            for m in members:
                by_vgrp[_vfind(m)].append(m)
            known_vds_sum = 0.0
            unresolved = []
            for vgrp, group_members in by_vgrp.items():
                resolved = next((gm for gm in group_members
                                  if ctx.sized.get(gm, {}).get("vds") is not None), None)
                if resolved is not None:
                    known_vds_sum += ctx.sized[resolved]["vds"]
                    # 2026-08-10(세션27) -- 값-동일 그룹의 다른 멤버가 전류만 전파받고(예:
                    # N_cmfb_bw_mirror처럼 A타입 mirror feed로만 연결된 M37b) gm_id/L/vds/W/
                    # gds가 없을 수 있다(headroom_role/gm_id_role 둘 다 없어 아래 두 fill
                    # 루프에서도 못 채워짐 -- M37a/M37b가 실제 사례, M37a는 N_cmfb_bw B타입
                    # feed가 자기 완결적으로 다 채우지만 M37b는 전류만 받음). 대표(resolved)와
                    # 같은 (gm_id,L,vds,vs)를 물려받되 자기 자신의 ID로 W/gm/gds를 LUT에서
                    # 재계산해 채운다(매칭쌍이므로 같은 물리 사이징을 공유한다는 전제,
                    # `_feed_metric_stage_budget()`과 동일한 계산 패턴) -- 이미 W가 있는
                    # 멤버는 건드리지 않는다(하위호환).
                    ref_entry = ctx.sized[resolved]
                    for sib in group_members:
                        sib_entry = ctx.sized.get(sib, {})
                        if sib == resolved or "W" in sib_entry or "ID" not in sib_entry:
                            continue
                        gm_id2, L2 = ref_entry["gm_id"], ref_entry["L"]
                        vds2, vs2 = ref_entry["vds"], ref_entry.get("vs", 0.0)
                        kind2 = ctx.kind_of[sib]
                        lut2 = spec["lut_by_kind"][kind2]
                        ID2 = sib_entry["ID"]
                        idu2 = lut2.gm_id_to_id_density(gm_id2, L2, vds2, vs2)
                        gm_gds2 = lut2.gm_gds_ratio(gm_id2, L2, vds2, vs2)
                        gm2 = gm_id2 * ID2
                        sib_entry.update({"gm_id": gm_id2, "L": L2, "vds": vds2, "vs": vs2,
                                          "kind": kind2, "W": L2 * ID2 / idu2, "gm": gm2,
                                          "gds": gm2 / gm_gds2})
                    continue
                rep = next((gm for gm in group_members
                            if "headroom_role" in device_roles.get(gm, {})), None)
                if rep is None:
                    raise ValueError(
                        f"'{vsid}' 그룹의 값-동일 소자 {group_members} 전부 vds 미확정이고 "
                        f"headroom_role도 없다 -- 이 소자들의 vds를 채울 경로(compensation/"
                        f"metric_stage_budget/headroom_role 중 하나)가 topology.json에 "
                        f"선언돼 있는지 확인할 것")
                unresolved.append(rep)
            if not unresolved:
                continue

            # 2026-08-11(세션28 계속) -- same_as_device로 선언된 소자는 헤드룸 예산 계산에
            # 아예 참여하지 않고 참조 대상의 vds를 그대로 복사한다(M7=M6, M36b=M36a --
            # budget_reference_device로는 표현 못 하는 "동일" 관계). _ref_depth 위상정렬이
            # 이미 참조 대상 그룹을 먼저 처리하도록 보장하므로 여기서는 ctx.sized에 값이
            # 있어야 정상이고, 없으면 선언/순환 문제이므로 명시적으로 막는다.
            same_as_members = [m for m in unresolved if m in same_as_of]
            for m in same_as_members:
                src = same_as_of[m]
                src_vds = ctx.sized.get(src, {}).get("vds")
                if src_vds is None:
                    raise ValueError(
                        f"'{m}'의 same_as_device('{src}')가 아직 VDS 미확정 -- 참조 소자가 "
                        f"속한 vertical_stack_id 그룹이 먼저 풀려야 한다(순환/선언 확인)")
                vgrp = _vfind(m)
                for other in members:
                    if _vfind(other) == vgrp:
                        ctx.sized.setdefault(other, {})["vds"] = src_vds
            unresolved = [m for m in unresolved if m not in same_as_of]
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
            # 2026-08-11(세션28) -- allocate_stack_headroom()은 "주어진 그룹이
            # remaining_vdd 전체를 혼자 책임진다"는 계약을 강제한다(합이 정확히 일치함을
            # assert, §3 실측 이력의 3.2V 사고 재발 방지용 -- 이 계약 자체는 건드리지
            # 않는다). 그런데 소자 1개뿐인 그룹은 이 계약의 전제("내가 이 컬럼을 혼자
            # 책임진다")가 두 가지 이유로 깨질 수 있어 여기서 직접 우회한다:
            # (1) 다른 그룹의 budget_reference_device로 참조되고 있으면(예: M5는 진짜
            #     차동쌍 tail이고 vbias3_stack이 그 위에 참조로 얹혀사는 replica 체인) --
            #     remaining_vdd(=vdd 거의 전체)를 그대로 넘기면 "혼자니까 균등분배가
            #     100%"가 돼 물리적으로 불가능한 값이 나오고, 참조하는 그룹의
            #     base_budget이 거의 0이 돼 음수 VDS 크래시로 이어진다(실측: M61_M64_
            #     M63, vds=-0.4).
            # (2) role이 `DEFAULT_POLICY.thin_roles`(cascode/diode_reference)면 애초에
            #     "남는 예산을 나눠 가질" 대상이 아니라 "필요한 만큼만" 받아야 하는데,
            #     혼자면 함께 나눌 other_entries가 아예 없어 allocate_stack_headroom()의
            #     "합=vdd" assert 자체가 깨진다(thin_total(=min_vds, 예: 0.2~0.3V) !=
            #     vdd). M18_bg(diode-connected 기준전압 생성기, 외부 전류원으로 전류가
            #     정해지는 singleton)가 실제 사례.
            # 두 경우 다 allocate_stack_headroom()을 아예 호출하지 않고 역할별 헤드룸
            # (policy.cascode_fn -- gm_id 있으면 공식, 없으면 min_vds)을 직접 배정한다.
            # "나머지"는 버려지는 게 아니라(1) 참조하는 그룹의 base_budget으로 넘어가거나,
            # (2)애초에 이 소자가 가질 이유가 없던 예산이다.
            _fold_group_singleton = (len(stack_entries) == 1
                                      and device_roles.get(unresolved[0], {}).get("fold_group")
                                      is not None)
            # 2026-08-15(세션35) -- fold_group이 명시적으로 선언돼 있으면(사람/AI가 "이
            # 소자는 병합 노드라 ideal_sources 근거가 아니라 connectivity 근거로 우회한다"고
            # 확정한 것) thin_roles(예: "cascode")에도 걸리는 소자라도 ideal_sources 전용
            # 경로(_thin_singleton) 대신 이 새 경로를 타야 한다 -- 안 그러면 fold_group을
            # 선언해도 역할이 우연히 thin_roles에 속하면(예: M6="cascode") 여전히
            # ideal_sources 요구로 막힌다(실측으로 발견).
            _thin_singleton = (len(stack_entries) == 1
                                and stack_entries[0]["role"] in DEFAULT_POLICY.thin_roles
                                and not _fold_group_singleton)
            _referenced_singleton = (len(stack_entries) == 1
                                      and unresolved[0] in referenced_devices
                                      and not _fold_group_singleton)
            if _thin_singleton:
                # 2026-08-11(세션28 계속) -- role 라벨("diode_reference")만 믿지 않고
                # 실제 topology.json의 ideal_sources 선언과 대조해 이 우회가 물리적으로
                # 정당한지 검증한다(사용자 지적: ideal current source(전류 고정, 전압
                # 자유)만 "남는 예산"을 군말 없이 흡수한다 -- ideal voltage source는
                # 전혀 다른 케이스). 검증 실패 시 조용히 넘어가지 않고 명시적 에러.
                _ok, _detail = _thin_singleton_ideal_source_check(unresolved[0])
                if not _ok:
                    raise ValueError(
                        f"'{unresolved[0]}'(role={stack_entries[0]['role']!r})가 singleton "
                        f"thin-role 그룹이라 allocate_stack_headroom()의 '합=vdd' 계약을 "
                        f"우회하려는데, ideal_sources 선언으로 정당화가 안 됨: {_detail}")
                headroom = {unresolved[0]: DEFAULT_POLICY.cascode_fn(stack_entries[0])}
            elif _referenced_singleton:
                headroom = {unresolved[0]: DEFAULT_POLICY.cascode_fn(stack_entries[0])}
            elif _fold_group_singleton:
                # 2026-08-15(세션35, 사용자 지시 "새 기능을 추가해"로 신설) -- 폴디드
                # 캐스코드의 X/Y 노드처럼 서로 다른 방향에서 온 branch가 한 노드에서
                # 합류하는 구조. allocate_stack_headroom()의 "한 컬럼이 vdd 전체를 혼자
                # 책임진다" 전제가 안 맞는 세 번째 패턴(위 _thin_singleton/_referenced_
                # singleton과 나란히) -- 정당화 근거는 ideal_sources가 아니라 실제
                # connectivity(같은 fold_group 선언 소자와 노드 공유)로 검증한다. thin_
                # roles/referenced_singleton과 동일하게 role-기반 cascode_fn만 배정하고,
                # 병합 노드 전압의 정확한 KVL 일치(각 branch가 실제로 같은 Vx에 도달하는지)는
                # 이 근사가 보장하지 않는다 -- 이 프로젝트의 다른 singleton 우회들과 동일한
                # 근사 수준(§HeadroomPolicy 참고, 엄밀한 KVL 솔버가 아니라 역할 기반 실용적
                # 배정).
                _ok, _detail = _fold_group_check(unresolved[0])
                if not _ok:
                    raise ValueError(
                        f"'{unresolved[0]}'가 fold_group 선언으로 allocate_stack_headroom()의 "
                        f"'합=vdd' 계약을 우회하려는데, connectivity로 정당화가 안 됨: {_detail}")
                headroom = {unresolved[0]: DEFAULT_POLICY.cascode_fn(stack_entries[0])}
            else:
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

        # 2026-08-14 -- L_role의 _AUTHORITATIVE_L_SOURCES(3905행)와 대칭되는 gm_id_role
        # 가드가 원래 없었다(실측으로 발견 -- propose_device_roles_gap_fill()이
        # compensation.stage_devices 소속 소자에 gm_id_role="matching"을 채우면, 여기서
        # search_gm_id_for_role()이 그대로 돌아 optimize_multistage()가 이미 정한 gm_id/W를
        # 덮어써버리는 진짜 버그였다 -- L_role은 안전한데 gm_id_role만 위험했던 비대칭).
        # ⚠️ `_AUTHORITATIVE_L_SOURCES`(={"compensation","replica","metric_stage_budget"})를
        # 그대로 재사용하면 안 된다 -- "replica"(C타입 K_replica feed)는 정반대로 **이
        # 루프가 재검색해서 gm_id를 덮어쓰는 것 자체가 설계 의도**다(_feed_diode_stack_
        # target() docstring 2568행 "이 함수가 여기서 채운 gm_id는 곧바로 _evaluate()의
        # device_roles 루프가 search_gm_id_for_role()로 재검색해 덮어쓴다" 참고 -- L/vds/vs만
        # replica가 권위 있고 gm_id는 애초에 placeholder). 반면 "metric_stage_budget"은
        # gm_id도 자기 자신의 theta 탐색(gm_id_match_vgs_of/gm_id_role/고정 gm_id, `_feed_
        # metric_stage_budget()` 참고)이 이미 확정하므로 L과 마찬가지로 권위 있다 -- 이
        # 소자를 여기서 또 건드리면(실측: current_reuse_telescopic_ota의 M2a/M2b/M3a/M3b,
        # `L_cascode` theta 대상) 그 theta 탐색 자체가 무력화된다(SLSQP gain_db 76.48->74.8
        # 회귀로 재현 확인, `_AUTHORITATIVE_L_SOURCES`와 동일 근본원인·동일 수정).
        _AUTHORITATIVE_GM_ID_SOURCES = {"compensation", "metric_stage_budget", "gm_target_convention"}
        for name, dr in device_roles.items():
            if not dr.get("gm_id_role"):
                continue
            entry = ctx.sized.get(name, {})
            if entry.get("_L_source") in _AUTHORITATIVE_GM_ID_SOURCES:
                continue
            if "ID" not in entry:
                raise ValueError(f"{name}: A엔진(propagate_topology_forced_currents)이 전류를 "
                                  f"못 정했다 -- mirror_ratios/seed_currents(theta feeds)를 확인할 것")
            if entry["ID"] <= 0:
                # 2026-08(세션6) -- "A_signed"(부호 있는 KCL 합) theta가 이 theta 격자점에서
                # 음수 전류를 만들면(예: kcl_battery_M9b=ID(M8)-ID(M9a)가 K_replica/
                # r_classab_src 조합에 따라 음수가 됨, 실측 발견) 이건 "선언 누락"이 아니라
                # "이 조합은 물리적으로 불가능"이라는 뜻 -- ValueError를 바로 내는 대신
                # InfeasibleSizingError로 구분해 grid search가 이 점만 건너뛰게 한다.
                raise InfeasibleSizingError(
                    f"{name}: ID={entry['ID']:.6g}A <= 0 -- 이 theta 조합에서 물리적으로 "
                    f"불가능한 전류(A_signed KCL 뺄셈이 음수가 됨)",
                    sized_snapshot=dict(ctx.sized))
            L, vds = entry.get("L"), entry.get("vds")
            if L is None or vds is None:
                raise ValueError(f"{name}: L 또는 VDS가 미확정 -- device_roles의 L_role/"
                                  f"vertical_stack_id 선언을 확인할 것")
            # ctx.sized에 이미 vs가 있으면(폴디드 노드처럼 budget_reference_device로 동적
            # 전파된 값) 그걸 우선한다 -- device_roles의 vs는 정적 기본값(보통 0.0)일 뿐.
            vs = entry.get("vs", dr.get("vs", 0.0))
            lut = spec["lut_by_kind"][kind_of[name]]
            W_bounds = spec.get("W_bounds", (1e-6, 200e-6))
            try:
                # 2026-08-13(세션31) -- return_idu=True로 스캔 도중 이미 계산된 IDu를 같이
                # 받는다 -- 예전엔 이 IDu를 버리고 바로 아래서 size_transistor()가 동일
                # 인자(gm_id,L,vds,vs)로 gm_id_to_id_density()를 재조회했다(감사 발견,
                # search_gm_id_for_role() docstring 참고). W 계산식은 size_transistor()와
                # 완전히 동일(W=L*ID/IDu) -- 값 변화 없음, 중복 조회만 제거.
                gm_id, idu = search_gm_id_for_role(lut, L, vds, vs, entry["ID"], dr["gm_id_role"],
                                                    W_bounds, return_idu=True)
            except InfeasibleSizingError as _sgfr_e:
                # 2026-08-12(세션30) -- search_gm_id_for_role()의 에러 메시지엔 소자 이름이
                # 없어 어느 소자가 실패했는지 알 수 없었다(진단 중 발견) -- 여기서 이름/L/vds/
                # ID_target을 덧붙여 재발생시킨다(원인 자체는 그대로, 정보만 보강).
                raise InfeasibleSizingError(
                    f"{name}(role={dr['gm_id_role']!r}, L={L:.4g}m, vds={vds:.4g}V, "
                    f"ID_target={entry['ID']:.4g}A): {_sgfr_e}",
                    sized_snapshot=dict(ctx.sized)) from _sgfr_e
            gm = entry["ID"] * gm_id
            w = L * entry["ID"] / idu
            gds = gm / lut.gm_gds_ratio(gm_id, L, vds, vs)
            ctx.sized[name] = {**entry, "gm_id": gm_id, "gm": gm, "W": w, "gds": gds,
                                "kind": kind_of[name], "vs": vs}

        # 2026-08-19(세션38) -- device_roles의 gm_id_match_vgs_of: 위 루프(gm_id_role)와
        # 대칭인 2차 pass. `_feed_metric_stage_budget()`의 동명 필드(3219행 docstring)를
        # theta-무관 device_roles 레벨로 일반화한 것 -- nmcnr_amplifier의 M203(다이오드
        # 레퍼런스)/M204(미러) 실측 계기(.ai/context.md 세션37 §1-⑪/§4④): 게이트·소스가
        # 물리적으로 공유된(gate=NodeC, source=vss 둘 다 동일) 순수 미러쌍은 VDS가 서로
        # 달라도 VGS는 KVL로 완전히 강제 동일해야 하는데, 기존 루프는 이 관계를 전혀 모른
        # 채 두 소자의 gm_id를 각자 role 기준으로 독립 탐색했다(우연히 같을 수도, 실측처럼
        # gain/load로 바꾸면 17.5/18.5로 갈라질 수도 있었음 -- 관계를 보장하는 메커니즘
        # 자체가 없었다는 게 진짜 문제). 이 pass는 "root"(gm_id_role로 위 루프가 이미
        # 확정한 소자, 또는 compensation/metric_stage_budget/gm_target_convention처럼
        # 이 루프 이전에 이미 권위 있게 확정된 소자)의 실제 VGS를 `vgs_for_gm_id()`로
        # 구해, "dependent" 소자의 gm_id를 자기 자신의 (L,vds,vs)에서 `gm_id_for_vgs()`로
        # 역산한다(탐색 아님, O(1) 보간 -- gm_id_match_vgs_of의 기존 사용처와 동일 함수
        # 재사용, 새 계산 로직 없음). 2-pass 고정 순서(gm_id_role 전부 -> gm_id_match_vgs_of
        # 전부)라 companion이 반드시 gm_id_role 소자이거나 이 루프 이전에 이미 sizing된
        # 소자여야 한다 -- companion이 또 다른 gm_id_match_vgs_of 소자인 체인은 아직
        # 미지원(필요해지면 확장, 지금은 실제 사용처가 1단 체인뿐이라 원칙대로 안 만듦).
        # 선택적 필드(옵트인) -- 안 쓰면 기존 동작과 100% 동일, 다른 회로엔 영향 없음.
        for name, dr in device_roles.items():
            match_device = dr.get("gm_id_match_vgs_of")
            if not match_device:
                continue
            entry = ctx.sized.get(name, {})
            if entry.get("_L_source") in _AUTHORITATIVE_GM_ID_SOURCES:
                continue
            if "ID" not in entry:
                raise ValueError(f"{name}: A엔진(propagate_topology_forced_currents)이 전류를 "
                                  f"못 정했다 -- mirror_ratios/seed_currents(theta feeds)를 확인할 것")
            if entry["ID"] <= 0:
                raise InfeasibleSizingError(
                    f"{name}: ID={entry['ID']:.6g}A <= 0 -- 이 theta 조합에서 물리적으로 "
                    f"불가능한 전류(A_signed KCL 뺄셈이 음수가 됨)",
                    sized_snapshot=dict(ctx.sized))
            L, vds = entry.get("L"), entry.get("vds")
            if L is None or vds is None:
                raise ValueError(f"{name}: L 또는 VDS가 미확정 -- device_roles의 L_role/"
                                  f"vertical_stack_id 선언을 확인할 것")
            vs = entry.get("vs", dr.get("vs", 0.0))
            companion = ctx.sized.get(match_device)
            if companion is None or "gm_id" not in companion:
                raise ValueError(
                    f"{name}: gm_id_match_vgs_of={match_device!r}가 아직 sizing 안 됐다 -- "
                    f"device_roles 처리는 gm_id_role 소자 전체를 먼저 확정한 뒤 "
                    f"gm_id_match_vgs_of 소자를 처리한다(2-pass, 선언 순서 무관) -- "
                    f"{match_device!r}가 gm_id_role/compensation/metric_stage_budget/"
                    f"gm_target_convention 중 하나로 이미 확정 가능한지 확인할 것 "
                    f"(gm_id_match_vgs_of 체인은 아직 미지원)")
            companion_lut = spec["lut_by_kind"][kind_of[match_device]]
            target_vgs = companion_lut.vgs_for_gm_id(
                companion["gm_id"], companion["L"], companion["vds"], companion.get("vs", 0.0))
            lut = spec["lut_by_kind"][kind_of[name]]
            try:
                gm_id = lut.gm_id_for_vgs(target_vgs, L, vds, vs)
            except ValueError as _gifv_e:
                raise InfeasibleSizingError(
                    f"{name}(gm_id_match_vgs_of={match_device!r}, target_vgs={target_vgs:.4g}V, "
                    f"L={L:.4g}m, vds={vds:.4g}V): {_gifv_e}",
                    sized_snapshot=dict(ctx.sized)) from _gifv_e
            idu = lut.gm_id_to_id_density(gm_id, L, vds, vs)
            gm = entry["ID"] * gm_id
            w = L * entry["ID"] / idu
            gds = gm / lut.gm_gds_ratio(gm_id, L, vds, vs)
            ctx.sized[name] = {**entry, "gm_id": gm_id, "gm": gm, "W": w, "gds": gds,
                                "kind": kind_of[name], "vs": vs}

        metrics_result = {name: compute_metric(mspec, ctx) for name, mspec in metrics_specs.items()}
        return ctx, metrics_result

    return {
        "transistors": transistors, "meta": meta, "thetas": thetas,
        "metrics_specs": metrics_specs, "objective": objective, "constraints": constraints,
        "device_roles": device_roles, "comp": comp, "pairs_meta": pairs_meta,
        "kind_of": kind_of, "by_name": by_name, "stack_groups_geometry": stack_groups_geometry,
        "stack_groups_kcl": stack_groups_kcl, "evaluate": _evaluate,
    }


# ---------------------------------------------------------------------------
# 6.9c) box-shape/floorplan 자동 재시도 (2026-08-14 세션32, 사용자 지시) -- 원래
#       `workspaces/run_harness.py`가 외부에서 `optimize_full_circuit_budget()`을
#       통째로 재호출하며 돌리던 row_split 재시도 루프를 이 함수 안으로 옮긴다. 세션18
#       "순수 함수" 원칙(§1.6)을 뒤집는 결정이지만, 그 외부 루프가 매 라운드 theta/gm-ID
#       그리드서치(가장 비싼 부분)까지 처음부터 재실행하고 있었다 -- row_split은 이미
#       정해진 W/gm_id를 물리적으로 접기만 하는 순수 layout 작업이라 grid search와 무관한데도
#       그랬다(사용자 실측 지적: current_reuse_telescopic_ota 10분+ 무응답). 아래 세 헬퍼는
#       `run_harness.py`가 쓰던 로직을 그대로(동작 변경 없이) 옮긴 것 -- `_pick_split_target()`
#       만 `excluded` 인자가 새로 추가됐다(아래 backtracking용).
# ---------------------------------------------------------------------------

_SPLIT_SUFFIX_RE = re.compile(r"(_split\d+|_repair\d+)+$")


def _base_stack_id(row_name: str) -> str:
    """`apply_explicit_row_split()`(`_split{i}`)/`repair_matching_safety()`(`_repair{i}`,
    반복 적용되면 `_repair0_repair0`처럼 중첩)가 붙인 접미사를 벗겨 원래 `row_split`이
    참조하는 base stack_id를 복원한다(`workspaces/run_harness.py`에서 그대로 이전)."""
    return _SPLIT_SUFFIX_RE.sub("", row_name)


def _pick_split_target(floorplan, current_row_split: dict, excluded: frozenset = frozenset(),
                        max_split_per_stack: int = 6):
    """`floorplan.row_split_candidates`에서 diffusion-safe(`splittable=True`)한 후보 중
    가장 지배적인(`value/bbox` 비율이 큰) 것을 골라 base stack_id를 반환한다. `excluded`에
    있는 stack(이번 탐색에서 이미 `max_split_per_stack`까지 밀어붙였는데도 개선을 못 만든
    stack, 아래 재시도 루프의 backtracking)은 건너뛴다. 이미 `max_split_per_stack`만큼
    접은 stack도 더 안 늘린다(무한 루프 방지). 후보가 없으면 `None`(자동 조정 불가 --
    호출자가 정직하게 포기하고 마지막 상태를 그대로 쓸 차례)."""
    candidates = [c for c in floorplan.row_split_candidates if c.get("splittable")]
    if not candidates:
        return None
    candidates.sort(key=lambda c: c["value"] / c["bbox"] if c["bbox"] else 0.0, reverse=True)
    for c in candidates:
        stack_id = _base_stack_id(c["name"])
        if stack_id in excluded:
            continue
        if current_row_split.get(stack_id, 1) < max_split_per_stack:
            return stack_id
    return None


def _score_floorplan(floorplan, floorplan_target: dict) -> float:
    """`floorplan_target`(`{"max_aspect_ratio":..., "min_packing_density":...}`) 대비
    이 floorplan이 얼마나 못 미치는지를 하나의 스칼라로 합산한다(0이면 목표 완전 충족,
    낮을수록 좋음) -- 아래 재시도 루프가 라운드끼리 "개선됐는지"를 비교하는 유일한 기준.
    새 휴리스틱을 지어내지 않고 `floorplan_target`이 이미 선언한 두 지표(aspect_ratio 상한/
    packing_density 하한)에서 상대오차로 그대로 도출한다."""
    max_ar = floorplan_target.get("max_aspect_ratio")
    min_pd = floorplan_target.get("min_packing_density")
    aspect_excess = (max(0.0, floorplan.aspect_ratio - max_ar) / max_ar) if max_ar else 0.0
    density_deficit = (max(0.0, min_pd - floorplan.packing_density) / min_pd) if min_pd else 0.0
    return aspect_excess + density_deficit


def diagnose_sizing_roles_gap(topology_path: str, spec: dict) -> dict:
    """`propose_device_roles_gap_fill()`(stick_diagram.py)과 대응하는 `sizing_roles` 쪽
    진단 도구(2026-08-15, 사용자 지시 -- "device_role/symmetry는 자동으로 채우는 게
    run_harness에 통합됐는데, sizing_role도 자동으로 채우는 걸 설계하고 통합하자").

    ⚠️ **근본적 차이**: `device_roles`/`matching_pairs`는 netlist connectivity만으로 구조적
    으로 제안 가능하다(analog-grammar 그래프 분석, 값을 지어내지 않아도 된다). `sizing_
    roles.theta`의 bounds나 `constraints`의 목표값은 **spec(설계 목표)에서 오는 숫자**라
    connectivity만으로 유도할 수 없다 -- 이 함수는 그 숫자를 대신 짓지 않는다. 대신
    "이 회로가 `sizing_roles=null`(자유 theta 없음) 상태로 `optimize_full_circuit_
    budget()`을 실제로 완주할 수 있는가"를 **실제로 1회 평가**(`propagate_topology_forced_
    currents()` 실행 + `compensation.function` 실제 호출)해 판정하고, 실패하면 지금까지
    함수 깊은 곳에서 날것의 `ValueError`로만 터지던 것을 구조화된 gap 리포트로 바꾼다
    (`folded_cascode`의 `Ibg`(ideal_sources, `value_amp=null`) 미정, `nmcnr_amplifier`의
    `PM_target_deg=46`(논문 실측치, `nmcnr_3stage_topology()`의 `PM_target_deg>60` 전제와
    충돌) 두 실사례로 이 두 gap 종류를 실측 확인함, `.ai/context.md` 세션35 참고).

    `sizing_roles.theta`가 이미 선언돼 있으면(자유 theta가 있는 회로) 이 함수는 할 일이
    없다 -- `{"status": "has_theta"}`만 반환(이런 회로는 애초에 이 진단 대상이 아니다).

    반환: `{"status": "ok"|"has_theta"|"gap", "kind": "unresolved_current"|
    "unresolved_vds_or_L"|"other"|None, ...}`
    - `"ok"`: theta 없이도(sizing_roles=null이 맞음) 넷리스트 전체 전류가 실제로 다 풀림 --
      지금 상태가 최종적으로 맞다는 뜻.
    - `"gap"`/`"unresolved_current"`: 특정 소자의 전류(`ID`)를 A엔진(`propagate_topology_
      forced_currents`)이 못 정함 -- `"device"`(그 소자 이름), `"ideal_source_hint"`(그
      소자가 물린 `ideal_sources` 선언, 있으면 -- 보통 `value_amp=null`인 미정 전류원이
      원인), `"fix_hint"`.
    - `"gap"`/`"unresolved_vds_or_L"`: ID는 풀렸지만 `L`/`VDS`가 미확정(`device_roles`의
      `L_role`/`vertical_stack_id` 선언 부족, singleton headroom 그룹이 참조할 예산이
      없는 경우 등) -- `"device"`, `"fix_hint"`.
    - `"gap"`/`"other"`: 위 두 패턴에 안 맞는 다른 `ValueError`(예: `compensation.function`이
      `comp_params` 조합 자체를 거부함 -- `nmcnr_3stage_topology`의 `PM_target_deg<=60`
      가드가 실제 사례) -- `"message"`에 원인이 그대로 담겨 있으니 직접 읽을 것, 이
      함수가 패턴을 인식 못 했다고 원인을 지어내지 않는다."""
    ev = _build_theta_evaluator(topology_path, spec)
    if ev["thetas"]:
        return {"status": "has_theta",
                "message": "sizing_roles.theta가 이미 선언돼 있음 -- 이 진단은 "
                            "theta 없는(sizing_roles=null) 회로 전용"}
    try:
        ev["evaluate"]({})
    except ValueError as e:
        msg = str(e)
        marker = "A엔진(propagate_topology_forced_currents)이 전류를 못 정했다"
        if marker in msg:
            device = msg.split(":", 1)[0]
            by_name = ev["by_name"]
            t = by_name.get(device)
            hint = None
            if t is not None:
                dev_terminals = {t.source, t.drain, t.gate}
                for src in (ev["meta"].get("ideal_sources") or []):
                    if dev_terminals & set(src.get("terminals", ())):
                        hint = src
                        break
            return {"status": "gap", "kind": "unresolved_current", "device": device,
                    "message": msg, "ideal_source_hint": hint,
                    "fix_hint": (f"'{device}'의 ID를 spec['known_sizing']['{device}']['ID']로 "
                                 f"직접 시드하거나, sizing_roles.theta에 이 소자(또는 그 레퍼런스 "
                                 f"루트)를 목표로 하는 새 theta를 선언할 것 -- 어느 쪽이든 실제 "
                                 f"전류/전력 목표값이 spec에서 와야 하며, 이 함수는 그 값을 "
                                 f"대신 지어내지 않는다.")}
        marker2 = "L 또는 VDS가 미확정"
        if marker2 in msg:
            device = msg.split(":", 1)[0]
            return {"status": "gap", "kind": "unresolved_vds_or_L", "device": device,
                    "message": msg,
                    "fix_hint": (f"'{device}'의 device_roles에 L_role/vertical_stack_id가 "
                                 f"선언돼 있는지, 그 소자가 속한 headroom 그룹(singleton이면 "
                                 f"budget_reference_device/thin_roles 등)이 예산을 실제로 "
                                 f"받을 수 있는 구조인지 확인할 것 -- 이것도 값을 대신 "
                                 f"지어내지 않는다.")}
        return {"status": "gap", "kind": "other", "message": msg,
                "fix_hint": "위 두 패턴(전류 미확정/VDS·L 미확정)에 안 맞는 다른 ValueError -- "
                            "message를 직접 읽을 것(예: compensation.function이 comp_params "
                            "조합 자체를 거부하는 경우, nmcnr_3stage_topology의 "
                            "PM_target_deg<=60 가드가 실제 사례)."}
    return {"status": "ok",
            "message": "sizing_roles=null로도 넷리스트 전체 전류가 전부 풀림 -- "
                        "이 상태가 최종적으로 맞다."}


def optimize_full_circuit_budget(topology_path: str, spec: dict,
                                  grid_points_per_theta: int = 5,
                                  search_method: str = "grid",
                                  slsqp_kwargs: dict | None = None) -> dict:
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
    4. `objective`/`constraints`로 θ* 선택 -- `search_method="grid"`(기본, 재현성/최적성
       보장이지만 자유 theta가 많으면 격자 폭발, 세션27 실측) 또는 `search_method="slsqp"`
       (세션29 신설, `_optimize_theta_slsqp()` — `presolve_warm_start()`가 만든 실현가능한
       시작점에서 SLSQP+multi-start, scipy 필요, 훨씬 빠르지만 전역 최적 보장은 없음).
    5. 넷리스트 전체가 사이징됐으면(`assign_finger_geometry()`가 요구하는 W가 전부 있으면)
       `assign_finger_geometry()` → `run_topology_pipeline_with_finger_fixup()`(euler
       자동수정, 세션15) → FAIL이면(`lut_by_kind` 있을 때) `run_matching_safety_with_
       finger_growth()`(matching quality 3b/3c 자동수정 — 핑거증가 L3+L4 + gm/ID 예산
       초과 시 인접배치 완화, 세션16/17/**세션18 배선**) 또는(`lut_by_kind` 없는 구형
       spec) 기존 `repair_matching_safety()`.

    `spec` 주요 키(회로마다 다름, 전부 선택이지만 해당 단계가 필요로 하면 없을 시 에러):
    `"lut_by_kind"`({"nmos":LUT,"pmos":LUT}), `"vdd"`, `"L_candidates"`/`"VDS_candidates"`/
    `"gm_id_grid"`(compensation `optimize_multistage()`용), `"L_min"`/`"L_min_by_kind"`,
    `"W_bounds"`, `"min_vds_by_role"`, `"min_finger_w"`/`"max_finger_w"`, `"floorplan_hints"`,
    `"cell_groups"`, `"known_sizing"`, 그 외 theta feed가 참조하는 이름 붙은 상수.

    `"row_split"`(`{stack_id: n_rows}`, 선택): box-shape를 위한 명시적 초기 folding(§CD절,
    `apply_explicit_row_split()`). `"floorplan_target"`(`{"max_aspect_ratio":...,
    "min_packing_density":...}`, 선택, 2026-08-14 세션32 신설)이 **함께** 주어지면, 이
    `row_split`을 시작점 삼아 목표를 만족할 때까지 **theta/gm-ID 그리드서치를 다시 돌리지
    않고** row_split만 자동으로 조정하는 내부 재시도 루프가 켜진다(`"max_split_per_stack"`
    기본 6, `"max_layout_retry_rounds"` 기본 6). `floorplan_target`이 없으면 `row_split`은
    그대로 1회만 적용되고 끝(세션31까지의 동작과 100% 동일, 완전 하위호환) — 이 루프는
    opt-in이다.

    반환: `{"theta_star", "sizing", "metrics", "sizing_overrides", "pipeline_result",
    "audit_ok"}` — `sizing_overrides`/`pipeline_result`는 넷리스트 전체가 사이징되지 않으면
    `None`(부분 결과만 반환 — 단순 회로/미완성 선언 지원, §7.3.2 검증 (b)와 동일한 하위호환
    사상). 모든 θ 격자점이 infeasible이면 `ValueError`. matching-safety 자동수정이 실행됐고
    `lut_by_kind`가 있으면(세션18), `pipeline_result`에 `repaired_rows`/`repaired_audit` 외에
    `growth_rounds`/`unresolved_pair`/`unresolved_reason`/`relaxed_pairs`(`run_matching_
    safety_with_finger_growth()` 진단 필드 그대로)도 담긴다 — `audit_ok`가 최종 신호이고
    이 필드들은 "왜/어떻게" 해결됐는지 보는 참고 정보다(세션16 E-3절 원칙과 동일).
    `floorplan_target`이 주어졌으면 `pipeline_result["layout_retry_rounds"]`
    (`[{"target","row_split","score_before","score_after","accepted"}, ...]`)에 재시도
    루프가 실제로 무엇을 시도했는지 전부 남는다(참고 정보, `growth_rounds`와 같은 패턴).

    ⚠️ 정직한 한계(2026-07-31): diode-stack(C유형) 전류의 `solve_diode_stack_current()`
    자동 병합은 아직 없다(K_replica 면적비 theta feed는 W를 직접 설정할 뿐, KVL 전류 역산은
    미연결) — 이런 소자가 있는 회로는 `device_roles`로 해당 소자의 `ID`를 `known_sizing`에
    직접 시딩해 우회할 것."""
    ev = _build_theta_evaluator(topology_path, spec)
    transistors, meta = ev["transistors"], ev["meta"]
    thetas, metrics_specs = ev["thetas"], ev["metrics_specs"]
    objective, constraints = ev["objective"], ev["constraints"]
    pairs_meta, kind_of = ev["pairs_meta"], ev["kind_of"]
    stack_groups_geometry = ev["stack_groups_geometry"]
    _evaluate = ev["evaluate"]

    if not thetas:
        ctx, metrics_result = _evaluate({})
        theta_star, sizing = {}, ctx.sized
    elif search_method == "slsqp":
        theta_star, sizing, metrics_result = _optimize_theta_slsqp(
            topology_path, spec, ev, **(slsqp_kwargs or {}))
    elif search_method == "grid":
        names = [t["name"] for t in thetas]
        # bounds[0]==bounds[1](고정값 -- 예: KCL 순수 합산을 표현하는 ratio=1.0 theta,
        # M5/M11a/M38 등)인 theta는 grid_points_per_theta와 무관하게 1개 점만 평가한다
        # (2026-08-03, 배치 7-5 실행 중 발견): 그렇지 않으면 이런 "설계 자유도 없는" theta가
        # 하나 늘 때마다 전체 격자 조합 수가 grid_points_per_theta배씩 곱해져(현재 회로는
        # 이런 고정 theta가 8개라 2^8=256배) 탐색이 사실상 끝나지 않았다(실측: 40분+ 무응답,
        # 강제 종료 후 발견) — 값이 어차피 하나뿐이니 여러 번 평가할 이유가 없다.
        #
        # 2026-08-13(세션31, 사용자 지시) -- metric_stage_budget theta(L_cascode/
        # L_stage2out류, `_feed_metric_stage_budget()` 계약상 theta_value 자체가 항상
        # L이다)는 `_lerp()`의 임의 소수점 대신 spec["L_grid_step"](공정 레이아웃 그리드
        # 해상도, m 단위 -- 값 자체는 이 엔진이 추측하지 않음)의 배수만 격자점으로 쓴다.
        # `grid_points_per_theta` 예산은 그대로 유지(그리드 정렬이 "격자점 위치"만
        # 바꿀 뿐 "격자점 개수"는 안 바꾼다 -- 재계산 비효율 방지, `_grid_points_in_range()`
        # docstring 참고). 그 외 theta는 기존 `_lerp()` 그대로(하위호환).
        def _theta_grid_points(t):
            lo, hi = t["bounds"]
            if lo == hi:
                return [lo]
            is_l_theta = isinstance(t["feeds"], dict) and t["feeds"].get("type") == "metric_stage_budget"
            if is_l_theta:
                l_grid_step = spec.get("L_grid_step")
                if l_grid_step is None:
                    raise ValueError(
                        f"theta {t['name']!r}는 metric_stage_budget(L 그 자체)인데 "
                        f"spec['L_grid_step']이 없다 -- 실제 레이아웃에서 임의 소수점 L을 "
                        f"구현할 수 없으므로 공정 레이아웃 그리드 해상도(m 단위, PDK 문서 "
                        f"기준)를 명시적으로 선언할 것")
                return _grid_points_in_range(lo, hi, l_grid_step, n=grid_points_per_theta)
            return [_lerp(lo, hi, i / (grid_points_per_theta - 1)) for i in range(grid_points_per_theta)]
        grids = [_theta_grid_points(t) for t in thetas]
        best = None
        last_metrics, last_theta = None, None
        n_physically_infeasible = 0
        last_infeasible_reason, last_infeasible_theta = None, None
        for combo in itertools.product(*grids):
            theta_values = dict(zip(names, combo))
            # 2026-08(세션6) -- A_signed(부호 있는 KCL 합) theta가 이 조합에서 음수 전류를
            # 만들면 InfeasibleSizingError가 난다(위 클래스 docstring 참고) -- 이건 진짜
            # "선언 누락"이 아니라 "이 theta 조합은 물리적으로 말이 안 된다"는 뜻이라
            # constraints 위반과 똑같이 이 조합만 건너뛴다(그 외 ValueError는 여전히 즉시
            # 크래시).
            try:
                ctx, metrics_result = _evaluate(theta_values)
            except InfeasibleSizingError as e:
                n_physically_infeasible += 1
                last_infeasible_reason, last_infeasible_theta = str(e), theta_values
                continue
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
                f"위반된 제약={_violations}. "
                f"물리적으로 불가능해 건너뛴 조합 {n_physically_infeasible}개(마지막 사유: "
                f"{last_infeasible_reason}, theta={last_infeasible_theta})")
        _, theta_star, sizing, metrics_result = best
    else:
        raise ValueError(f"등록되지 않은 search_method {search_method!r} -- 'grid' 또는 "
                          f"'slsqp'만 지원")

    sizing_overrides, pipeline_result, audit_ok = None, None, None
    if all(t.name in sizing and "W" in sizing[t.name] for t in transistors):
        _base_sizing_overrides = assign_finger_geometry(
            sizing, stack_groups_geometry, area_priors=spec.get("area_priors"),
            min_finger_w=spec.get("min_finger_w", 1e-6), max_finger_w=spec.get("max_finger_w", 40e-6))
        # 2026-08(세션15) -- euler-blocked row(체크1)는 sizing(핑거) 조정으로 먼저 자동
        # 수정을 시도한다(L3+L4 오케스트레이션, run_topology_pipeline_with_finger_fixup(),
        # .ai/context.md 세션14/15 참고). run_topology_pipeline()을 대체하는 게 아니라
        # 감싸는 wrapper다(euler 실패 없으면 첫 라운드에 바로 통과, 기존 동작과 동일) --
        # 순수 물리 배치 문제(3b/3c)는 이 wrapper의 책임이 아니라 아래 repair_matching_
        # safety()가 그대로 이어서 처리한다(두 함수는 같은 문제의 대안이 아니라 서로 다른
        # audit 체크를 담당하는 상호보완 관계 -- repair_matching_safety()의 _failing_
        # required_pairs()는 "3b."/"3c." 체크만 파싱하고 "1. euler[...]"는 건드리지 않는다,
        # stick_diagram.py:3070 확인됨).
        # L4 재검증(revalidate_finger_override())은 lut_by_kind가 필수다. spec에 lut_by_kind
        # 자체가 없는 회로(theta feed 'A'/'A_signed'/'C'만 쓰고 'B'/'metric_stage_budget'은
        # 전혀 없는 경우 -- 이 두 feed만 소자별 kind-LUT이 필요하다, 세션22 참고)는 fixup을
        # 시도하지 않고 기존 run_topology_pipeline() 그대로 호출(완전한 하위호환). ⚠️
        # 세션22부터 'B'/'metric_stage_budget'을 쓰는 회로는 spec["lut_by_kind"]가 항상
        # 있어야 한다(kind 구분 없는 단일 lut 사이징은 전기적으로 틀린 결과를 준다 -- 이전엔
        # spec["lut"] 폴백이 있었으나 제거함, `_ofc_spec`도 lut_by_kind를 갖도록 갱신).
        _lut_by_kind = spec.get("lut_by_kind")
        if _lut_by_kind is not None:
            ctx_for_fixup = SizingContext(spec=spec, sized=sizing, kind_of=kind_of,
                                           topology_path=topology_path)
            _base_pipeline_result = run_topology_pipeline_with_finger_fixup(
                topology_path, _base_sizing_overrides, ctx_for_fixup, _lut_by_kind,
                metrics_specs, constraints, floorplan_hints=spec.get("floorplan_hints"),
                cell_groups=spec.get("cell_groups"),
                gm_id_bounds=spec.get("gm_id_bounds", (2.0, 30.0)))
            # fixup이 sizing(W/gm_id/gm/gds)과 layout(n_fingers/w)을 바꿨을 수 있으므로,
            # euler-fixup까지 끝난 이 baseline(_base_*)의 sizing_overrides/sizing을 fixup
            # 이후 상태로 갱신한다 -- 안 그러면 finger 조정이 반영 안 된 stale 값이
            # instance.json으로 흘러나가는 버그가 생긴다.
            _base_sizing_overrides = _base_pipeline_result["sizing_overrides"]
            _base_sizing = _base_pipeline_result["ctx"].sized
            _base_metrics_result = {name: compute_metric(mspec, _base_pipeline_result["ctx"])
                                     for name, mspec in metrics_specs.items()}
        else:
            _base_pipeline_result = run_topology_pipeline(
                topology_path, _base_sizing_overrides, floorplan_hints=spec.get("floorplan_hints"),
                cell_groups=spec.get("cell_groups"))
            _base_sizing, _base_metrics_result = sizing, metrics_result

        # 2026-08-14(세션32, 사용자 지시 -- 재계산 비효율 해소) -- 원래(세션31까지) 여기서
        # 1회만 실행되던 "row_split 적용 -> audit -> (필요시) matching-safety repair(핑거
        # 증가 포함) -> floorplan 재계산" 블록을 순수 함수 클로저로 뽑았다. 로직 자체는
        # 세션31 그대로(동작 변경 없음) -- 매번 위 _base_*(euler-fixup까지 끝난, row_split과
        # 무관한 상태)에서 새로 시작하므로 라운드끼리 서로 오염시키지 않는다(예: 이전
        # 라운드의 핑거증가가 다음 라운드로 몰래 상속되는 일이 없다). 이 클로저 자체는
        # theta/gm-ID 그리드서치를 전혀 건드리지 않으므로, 아래 재시도 루프가 이걸 여러
        # row_split 후보에 반복 호출해도 가장 비싼 부분은 단 한 번도 다시 안 돈다.
        def _evaluate_row_split(candidate_row_split: dict) -> dict:
            pr = dict(_base_pipeline_result)
            ov, sz, mr = _base_sizing_overrides, _base_sizing, _base_metrics_result

            # 2026-08-13(세션31 이어, 사용자 승인 -- CD절 "M6 folding" 논의 결론) --
            # candidate_row_split(`{stack_id: n_rows}`)이 있으면 매칭 자동판단(repair_
            # matching_safety())과 별개로, 명시적으로 지정된 stack을 여기서 즉시 접는다.
            # box-shape ratio만을 위한 순수 물리 재배치라 W/ID/gm_id는 안 바뀐다
            # (apply_explicit_row_split() docstring 참고) -- sizing/sizing_overrides
            # 갱신 불필요, transistors/box_shape/audit_row_split만 이 새 물리 구조를
            # 반영하도록 갱신한다.
            if candidate_row_split:
                _rs_rows = split_into_stacks(pr["transistors"])
                _rs_rows = apply_explicit_row_split(_rs_rows, candidate_row_split)
                _rs_transistors = [t for devs in _rs_rows.values() for t in devs]
                _rs_matching_pairs = [pair for p in pairs_meta
                                        for pair in itertools.combinations(p["names"], 2)]
                _rs_pair_sensitivity = {pair: p["matching_sensitivity"] for p in pairs_meta
                                          for pair in itertools.combinations(p["names"], 2)}
                # 2026-08-14(세션32) -- audit_row_split()이 "2. box-shape" 체크를 위해
                # 내부에서 이미 check_box_shape(_rs_rows)를 계산하므로(AuditResult.box_shape
                # 필드 참고), 여기서 같은 _rs_rows에 그 함수를 또 부르지 않고 audit 결과에
                # 실려온 걸 그대로 재사용한다.
                _rs_audit = audit_row_split(_rs_rows, matching_pairs=_rs_matching_pairs,
                                              pair_sensitivity=_rs_pair_sensitivity)
                pr = dict(pr, transistors=_rs_transistors,
                          box_shape=_rs_audit.box_shape, audit_row_split=_rs_audit)

            audit = pr["audit_row_split"]
            ok = audit.ok if hasattr(audit, "ok") else all(v.ok for v in audit.values())
            if not ok:
                rows = split_into_stacks(pr["transistors"])
                # audit_row_split()/repair_matching_safety()는 순수 2-tuple 쌍 계약이다
                # (docstring: "[(name_a, name_b), ...]") -- names가 2개보다 많은 그룹
                # (예: 기준 소자 하나를 여러 소자가 미러하는 current_mirror)은 모든
                # 쌍별 조합으로 펼쳐서 넘긴다(2026-08-01, 3개짜리 그룹에서 실제로
                # 발견된 unpack 에러 수정).
                matching_pairs_tuples = [pair for p in pairs_meta
                                          for pair in itertools.combinations(p["names"], 2)]
                pair_sensitivity = {pair: p["matching_sensitivity"] for p in pairs_meta
                                     for pair in itertools.combinations(p["names"], 2)}
                # 세션18 -- matching quality(3b/3c) 자동수정도 이제 핑거증가(L3+L4, 세션16)+
                # gm/ID 예산으로 막히면 인접배치로 완화(세션17 설계안 3번)까지 이어붙인
                # run_matching_safety_with_finger_growth()로 승격한다. lut_by_kind가
                # 없는 구형 spec은 gm/ID 재검증이 불가능하므로 기존 bare repair_matching_
                # safety()로 폴백(완전 하위호환, 위 euler 분기와 동일 가드 재사용 -- 그
                # 분기에서만 pr["ctx"]가 존재한다).
                if _lut_by_kind is not None:
                    match_fix = run_matching_safety_with_finger_growth(
                        rows, matching_pairs_tuples, pair_sensitivity, pr["ctx"],
                        _lut_by_kind, metrics_specs, constraints,
                        gm_id_bounds=spec.get("gm_id_bounds", (2.0, 30.0)))
                    repaired_rows, repaired_audit = match_fix["rows"], match_fix["audit"]
                    # 핑거증가가 실제로 W/n_fingers를 바꿨을 수 있으므로(위 euler 분기의
                    # _sync_finger_fixup()과 동일 이유) 이 라운드의 sizing_overrides/sizing을
                    # 최종 상태로 동기화한다 -- ov를 여기서만 복사해(baseline인 _base_
                    # sizing_overrides는 절대 안 건드림, 다른 라운드가 이 라운드의 핑거증가를
                    # 물려받지 않도록) grown finger를 반영한다. common-centroid 회전배치로
                    # 소자 하나가 여러 행에 n_fingers 조각으로 나뉠 수 있어(세션16 F절 함정)
                    # 행별로 합산해야 정확하다.
                    final_n_fingers: dict = {}
                    for devs in repaired_rows.values():
                        for t in devs:
                            final_n_fingers[t.name] = final_n_fingers.get(t.name, 0) + t.n_fingers
                    ov = dict(ov)
                    for name, n in final_n_fingers.items():
                        entry = ov[name]
                        if n != entry["n_fingers"]:
                            ov[name] = {**entry, "n_fingers": n, "w": n * entry["finger_w"]}
                    sz = match_fix["ctx"].sized
                    mr = {name: compute_metric(mspec, match_fix["ctx"])
                          for name, mspec in metrics_specs.items()}
                    pr = dict(
                        pr, repaired_rows=repaired_rows, repaired_audit=repaired_audit,
                        growth_rounds=match_fix["growth_rounds"],
                        unresolved_pair=match_fix["unresolved_pair"],
                        unresolved_reason=match_fix["unresolved_reason"],
                        relaxed_pairs=match_fix["relaxed_pairs"])
                else:
                    # ⚠️ 정직한 한계(2026-08-13 세션31 이어) -- lut_by_kind가 없는 구형 spec
                    # 경로라 run_matching_safety_with_finger_growth()를 못 쓴다 -- 그 함수는
                    # gm/ID 재검증에 LUT가 필요하다. 현재 라이브러리 4개 회로 전부 lut_by_
                    # kind를 쓰므로(실측 확인) 이 분기는 실전에서 아직 노출되지 않았다.
                    repaired_rows, repaired_audit = repair_matching_safety(
                        rows, matching_pairs_tuples, pair_sensitivity)
                    pr = dict(pr, repaired_rows=repaired_rows, repaired_audit=repaired_audit)
                ok = repaired_audit.ok
                # 2026-08-13(세션31 이어, 사용자 지시 -- box-shape 진단 도중 발견된 저장
                # 버그) -- repaired_rows를 최종 정본으로 승격해 transistors/box_shape/
                # audit_row_split을 덮어써서 이 라운드가 반환하는 pr과 ok가 항상 같은
                # 사실을 가리키도록 한다(예전엔 이 갱신이 누락돼 instance.json에 repair
                # *이전* 스냅샷이 저장되는 불일치가 있었다, `.ai/context.md` 세션31 CD 참고).
                # box_shape는 repaired_audit(위에서 이미 audit_row_split(repaired_rows, ...)로
                # 계산됨)에 실려온 걸 그대로 쓴다 -- 같은 repaired_rows에 check_box_shape()를
                # 또 부르지 않는다(2026-08-14 세션32, 위 row_split 블록과 동일한 이유).
                repaired_transistors = [t for devs in repaired_rows.values() for t in devs]
                # 2026-08-14(세션32, 사용자 절대원칙 -- "만들면 반드시 배선") --
                # check_stick_diagram_coverage()("sizing은 됐는데 layout이 통째로 빠짐 최후의
                # 방어선"으로 stick_diagram.py 자신이 명시)가 지금까지 run_topology_pipeline()
                # 안(matching-safety repair *이전* 시점)에서만 호출되고 repair 이후엔 한 번도
                # 재호출된 적이 없었다 -- repair_matching_safety()/run_matching_safety_with_
                # finger_growth()가 소자를 조용히 빠뜨려도 잡아낼 방법이 없었다(실측: 세션32
                # current_reuse_telescopic_ota 첫 완주에서 M17/M18_bg/M61 3개가 최종 netlist에서
                # 통째로 사라진 걸 발견 -- run_full_circuit_audit/coverage 둘 다 이 시점 이후라
                # 못 잡음). repair 직후 여기서 다시 호출해 재검증한다 -- repair는 재배치만 해야
                # 하므로(핑거증가는 개수를 바꾸지만 이름을 없애지 않음) repair 전 이름 집합과
                # 정확히 같아야 한다. 어긋나면 조용히 저장하지 않고 즉시 실패한다(run_topology_
                # pipeline()의 "누락 소자 즉시 ValueError" 원칙과 동일 -- PRE-FLIGHT 사고27과
                # 같은 실패 유형을 여기서도 반복하지 않는다).
                _pre_repair_names = {t.name for devs in rows.values() for t in devs}
                _repair_coverage = check_stick_diagram_coverage(
                    _pre_repair_names,
                    {rn: [t.name for t in devs] for rn, devs in repaired_rows.items()})
                if not _repair_coverage.ok:
                    raise ValueError(
                        f"matching-safety repair(repair_matching_safety()/run_matching_safety_"
                        f"with_finger_growth()) 이후 소자가 사라졌다: {sorted(_repair_coverage.missing)} "
                        f"-- repair는 재배치만 해야 하므로 이 소자 집합이 repair 전후로 정확히 "
                        f"같아야 한다. repair 함수 내부의 근본원인을 고칠 것(조용히 저장하지 않음)."
                    )
                pr = dict(
                    pr, transistors=repaired_transistors,
                    box_shape=repaired_audit.box_shape,
                    audit_row_split=repaired_audit)

            # 2026-08-13(세션31 CO) -- floorplan은 row_split(있었다면)과 matching-safety
            # repair(있었다면) 둘 다 이미 반영된 이 시점의 pr["transistors"](진짜 최종
            # 물리 행 구성)로 다시 packing해야 한다(안 그러면 리포트의 floorplan이 옛
            # 통짜 블록을 보여주는 불일치가 생김, 실측 발견).
            _final_rows = split_into_stacks(pr["transistors"])
            pr = dict(pr, floorplan=rebuild_floorplan(_final_rows, spec.get("floorplan_hints")))
            return {"pipeline_result": pr, "sizing_overrides": ov, "sizing": sz,
                    "metrics_result": mr, "audit_ok": ok}

        # 2026-08-14(세션32) -- spec["floorplan_target"](`{"max_aspect_ratio":...,
        # "min_packing_density":...}`)이 없으면(대다수 회로, 하위호환) 위 클로저를 딱
        # 1번만 평가하고 끝 -- 세션31까지의 동작과 100% 동일. 있을 때만 아래 재시도
        # 루프가 켜진다(opt-in, 원래 `workspaces/run_harness.py`가 외부에서 하던 것과
        # 동일한 row_split 자동조정을 여기로 옮긴 것). row_split은 라운드끼리 절대
        # 리셋하지 않고 누적한다(동일 조합이 두 번 나올 수 없음, `_pick_split_target()`이
        # 매번 그 시점 floorplan에서 가장 지배적인 후보를 결정론적으로 고름 -- 랜덤 아님).
        #
        # backtracking(사용자 지적: "한 단계만 보고 포기하면 몇 단계 더 접었으면 됐을
        # 경우를 놓친다") -- 한 stack을 골랐으면(probe_target) max_split_per_stack까지
        # 계속 한 단계씩 더 밀어붙이다가(probe_row_split, 매 라운드 +1), 그 한계에
        # 도달했는데도 한 번도 best_score를 못 이겼을 때만 그 stack을 이번 탐색에서
        # 제외(excluded)하고 다음으로 지배적인 후보로 넘어간다. 개선되면(몇 단계째든)
        # 바로 채택(best 갱신)하고 처음부터 다시 가장 지배적인 후보를 고른다 -- "되돌리기"는
        # 별도 undo가 필요 없다(각 라운드가 이미 _base_*에서 새로 계산하는 순수함수라,
        # best를 안 덮어쓰면 그게 곧 되돌린 것).
        #
        # 남는 한계(정직하게 문서화, 지금 범위 밖) -- 이건 여전히 탐욕적 1-stack-at-a-time
        # 탐색이다: "두 stack을 동시에 바꿔야만 개선되는" 조합은 원리상 못 찾는다 --
        # pack_floorplan() 자신의 docstring이 이미 인정하는 "완전한 non-slicing floorplan
        # 최적화는 이 skill 범위를 넘는다"와 같은 종류의 한계.
        _base_row_split = dict(spec.get("row_split", {}))
        round0 = _evaluate_row_split(_base_row_split)
        floorplan_target = spec.get("floorplan_target")
        layout_retry_rounds: list = []

        if floorplan_target is None:
            chosen, chosen_row_split = round0, _base_row_split
        else:
            max_split_per_stack = spec.get("max_split_per_stack", 6)
            max_layout_retry_rounds = spec.get("max_layout_retry_rounds", 6)
            best, best_row_split = round0, _base_row_split
            best_score = _score_floorplan(best["pipeline_result"]["floorplan"], floorplan_target)
            excluded: set = set()
            probe_target, probe_row_split = None, None
            for _ in range(max_layout_retry_rounds):
                if best_score <= 0.0:
                    break
                if probe_target is None:
                    probe_target = _pick_split_target(
                        best["pipeline_result"]["floorplan"], best_row_split,
                        excluded=excluded, max_split_per_stack=max_split_per_stack)
                    if probe_target is None:
                        break
                    probe_row_split = dict(best_row_split)
                probe_row_split[probe_target] = probe_row_split.get(probe_target, 1) + 1
                trial = _evaluate_row_split(probe_row_split)
                trial_score = _score_floorplan(trial["pipeline_result"]["floorplan"], floorplan_target)
                improved = trial_score < best_score
                layout_retry_rounds.append({
                    "target": probe_target, "row_split": dict(probe_row_split),
                    "score_before": best_score, "score_after": trial_score, "accepted": improved})
                if improved:
                    best, best_score, best_row_split = trial, trial_score, dict(probe_row_split)
                    probe_target = None
                elif probe_row_split[probe_target] >= max_split_per_stack:
                    excluded.add(probe_target)
                    probe_target = None
                # else: 아직 max_split_per_stack 전이면 같은 target을 다음 라운드에 한 단계 더
            chosen, chosen_row_split = best, best_row_split

        pipeline_result = chosen["pipeline_result"]
        sizing_overrides = chosen["sizing_overrides"]
        sizing = chosen["sizing"]
        metrics_result = chosen["metrics_result"]
        audit_ok = chosen["audit_ok"]
        pipeline_result = dict(pipeline_result, row_split=chosen_row_split)
        if floorplan_target is not None:
            pipeline_result = dict(pipeline_result, layout_retry_rounds=layout_retry_rounds)

    return {"theta_star": theta_star, "sizing": sizing, "metrics": metrics_result,
            "sizing_overrides": sizing_overrides, "pipeline_result": pipeline_result,
            "audit_ok": audit_ok}


# ---------------------------------------------------------------------------
# 6.9b) 웜스타트 준비 1/3 — theta-metric 결합도 그래프(세션29, 세션27 "## B" 손유도의 일반화)
#       theta 여러 개를 SLSQP 시작점(x0)으로 채우기 전에 "이 theta가 어느 제약에 실제로
#       영향을 주는가"를 먼저 분류한다 -- dead(아무 것도 안 읽음)/isolated(목적함수만
#       영향, 제약과 무관)/coupled(적어도 하나의 제약과 얽힘). 전체회로 MNA 기반
#       metric(cmrr/psrr, smallsignal_ratio_db/gain_db 타입)은 구조상 이미 사이징된
#       모든 소자를 읽으므로 "구조적으로는" 거의 모든 theta와 얽혀 보인다 -- 세션27
#       B-2(r_cmfb_vocdes)가 실제로는 그 metric 값에 영향이 없다는 걸 손으로(v(Voc_des)=0
#       소신호 사실) 확인했던 사례가 정확히 이 함정을 보여준다. 이 함수는 그 손유도를
#       하드코딩하는 대신, "구조적으로 애매한"(전체회로 metric과만 겹치는) theta에 한해
#       기준점에서 실제 유한차분 민감도를 재보고 그 결과로 isolated/coupled를 확정한다
#       (role 라벨/추측이 아니라 declared 계산 자체와 대조하는 이 프로젝트의 기존 원칙,
#       `_thin_singleton_ideal_source_check()`와 같은 정신).
# ---------------------------------------------------------------------------

_FULL_CIRCUIT_METRIC_TYPES = frozenset({"smallsignal_ratio_db", "smallsignal_gain_db"})
# 2026-08-15(세션35) -- cmrr_estimate/psrr_estimate는 circuit_family별로 실제 footprint가
# 다르다(diff_pair_tail은 tail_device 하나, telescopic_class_ab류는 여러 소자) -- family마다
# 별도 분기를 추가하는 대신, 이 타입들에 "devices" 키가 없으면 안전한 쪽(과소평가 대신
# "ALL")으로 fallback하는 _DEFAULT_ALL_DEVICES_METRIC_TYPES에 편입한다(SLSQP 웜스타트가
# 이 metric을 isolated로 잘못 보고 커플링을 놓치는 사고를 방지 -- 위 docstring 참고).
_DEFAULT_ALL_DEVICES_METRIC_TYPES = frozenset({"sum_current", "sum_area",
                                                 "cmrr_estimate", "psrr_estimate"})


def _metric_device_footprint(metric_name: str, metrics_specs: dict):
    """metric_spec 선언만으로 이 metric이 실제로 읽는 소자 집합을 정적으로 판정한다.
    전체회로 MNA를 도는 타입(`smallsignal_ratio_db`/`smallsignal_gain_db`, `_full_circuit_
    devices()`가 무조건 전체 소자를 순회 -- 세션27 "## A" 실측 확인)은 문자열 `"ALL"`을
    반환한다(집합이 아니라 "이 회로의 사이징된 소자 전부"라는 별도 신호 -- 명시적 리스트와
    섞이지 않게 구분). 등록되지 않은 type은 조용히 빈 집합으로 넘어가지 않고 ValueError --
    이 함수가 새 metric type을 놓치면 결합도 판정이 조용히 틀려지므로(과소평가 위험) 명시적
    등록을 강제한다."""
    mspec = metrics_specs[metric_name]
    mtype = mspec["type"]
    if mtype in _FULL_CIRCUIT_METRIC_TYPES:
        return "ALL"
    if mtype in ("gain_stages_sum", "flicker_plus_thermal_sum"):
        return {d for stage in mspec["stages"] for d in stage}
    if mtype == "pelgrom_mismatch":
        return set(mspec["devices"])
    if mtype == "battery_centering_deviation":
        return {mspec["high_device"], mspec["low_device"]}
    if mtype == "rail_referenced_voltage":
        return {mspec["device"]}
    if mtype == "folded_cascode_gain_db":
        return {mspec["gm1_device"], mspec["fold_leg_a"], mspec["fold_leg_b"],
                mspec["cascode_p"], mspec["cascode_n"], mspec["mirror_n"]}
    if mtype == "folded_cascode_pm_deg":
        return ({mspec["gm1_device"], mspec["fold_leg_a"], mspec["fold_leg_b"],
                 mspec["cascode_p"], mspec["cascode_n"], mspec["mirror_n"]}
                | set(mspec["fold_cap_devices"]))
    if mtype in ("nmcnr_gain_db", "nmcnr_pm_deg"):
        return ({mspec["gm1_device"], mspec["gm2_device"], mspec["gm3_device"],
                 mspec["stage1_cascode_n"], mspec["stage1_fold_leg_a"],
                 mspec["stage1_fold_leg_b"], mspec["stage1_mirror_p"]}
                | set(mspec["stage2_devices"]) | set(mspec["stage3_devices"]))
    if mtype in _DEFAULT_ALL_DEVICES_METRIC_TYPES:
        devices = mspec.get("devices")
        return set(devices) if devices else "ALL"
    raise ValueError(
        f"'{metric_name}'의 metric type {mtype!r}이 _metric_device_footprint()에 등록되지 "
        f"않았다 -- derive_theta_dependency_graph()가 결합도를 과소평가(실제로는 걸려있는데 "
        f"isolated로 오판)하지 않도록, 이 type이 어떤 소자를 읽는지 여기 새로 추가할 것")


def _theta_feed_footprint(theta: dict) -> dict:
    """theta 하나의 feed 선언만으로 "직접 쓰는 소자"(`roots`)와 "직접 쓰는 ctx.derived
    키"(`derived_writes`, settling_split 전용)를 정적으로 추출한다. A/A_signed는 seed
    전류만 채우고 실제 사이징(L/gm_id/vds)은 그 소자가 속한 KCL 직렬 그룹 전체에 전파되므로
    (`propagate_topology_forced_currents()`), 호출자가 `stack_groups_kcl`로 root(s)를
    그룹 전체로 확장한다(이 함수는 root만 반환 -- 확장은 그래프 조립 단계 책임)."""
    feed = theta["feeds"]
    ftype = feed if isinstance(feed, str) else feed["type"]
    if ftype == "settling_split":
        output_key = feed.get("output_key", "t_slew") if isinstance(feed, dict) else "t_slew"
        complement_key = (feed.get("complement_key", "t_lln") if isinstance(feed, dict)
                           else "t_lln")
        writes = {output_key} | ({complement_key} if complement_key else set())
        return {"roots": frozenset(), "derived_writes": frozenset(writes), "reads": frozenset()}
    if ftype in ("A", "A_signed"):
        roots = feed["root"] if isinstance(feed["root"], list) else [feed["root"]]
        reads = (set(feed["reference"]) if ftype == "A"
                 else {term["device"] for term in feed["terms"]})
        return {"roots": frozenset(roots), "derived_writes": frozenset(), "reads": frozenset(reads)}
    if ftype == "const":
        roots = feed["root"] if isinstance(feed["root"], list) else [feed["root"]]
        return {"roots": frozenset(roots), "derived_writes": frozenset(), "reads": frozenset()}
    if ftype == "B":
        return {"roots": frozenset({feed["target"]}), "derived_writes": frozenset(),
                "reads": frozenset({feed["omega_key"]})}
    if ftype == "C":
        return {"roots": frozenset({feed["target"]}), "derived_writes": frozenset(),
                "reads": frozenset({feed["reference"]})}
    if ftype == "metric_stage_budget":
        return {"roots": frozenset(feed["devices"]), "derived_writes": frozenset(),
                "reads": frozenset()}
    raise ValueError(f"등록되지 않은 feeds 타입 {ftype!r} -- _theta_feed_footprint()에 추가할 것")


def derive_theta_dependency_graph(topology_path: str, spec: dict,
                                   baseline_theta_values: dict = None,
                                   probe_frac: float = 0.05,
                                   sensitivity_tol: dict = None,
                                   ev: dict | None = None) -> dict:
    """SLSQP 웜스타트 준비 1/3(세션27 "## B" B-1/B-2 손유도의 일반화) — 자유 theta 각각이
    dead(아무 metric/objective도 안 읽음)/isolated(목적함수만 영향, 제약과는 무관 -- bounds
    극값에 고정하는 게 사실상 최적)/coupled(적어도 하나의 제약과 실제로 얽힘 -- SLSQP가 직접
    최적화해야 함) 중 무엇인지 판정한다. `fixed`(bounds[0]==bounds[1], 애초에 자유도가 0인
    선언)는 별도 취급.

    **판정 절차**:
    1. feed 선언(`_theta_feed_footprint()`)에서 이 theta가 직접 쓰는 소자(root/target) 또는
       `ctx.derived` 키(settling_split)를 뽑는다. derived 키는 `compensation.parameters`에
       있으면 `compensation.stage_devices` 전체로, B타입 feed의 `omega_key`가 그 키를
       읽으면 그 B타입의 target으로 해석해(간접 footprint) 소자 집합으로 환원한다 -- 아무
       소비자도 없으면 **dead**(세션27 f_slew가 처음 발견됐을 때의 정확한 정의, 지금은
       do.md Level1->2 배선으로 `t_lln`이 compensation.parameters에 있어 더 이상 dead 아님).
    2. A/A_signed의 root는 `stack_groups_kcl`(같은 물리적 KCL 직렬 그룹)로 확장한다 --
       root 소자 하나의 ID만 바뀌는 게 아니라 그 소자와 KCL로 묶인 전류전파 그룹 전체가
       영향을 받기 때문(과소평가 방지 -- 불확실하면 "안 걸림"이 아니라 "걸림" 쪽으로 넓게
       잡는다).
    3. 이 footprint가 `constraints`의 각 metric 선언(`_metric_device_footprint()`)과
       **명시적으로**(전체 소자 아닌 구체적 devices/stages 리스트) 겹치면 즉시 **coupled**
       (구조적으로 확실함 -- 굳이 실측할 필요 없음).
    4. 명시적 겹침이 없는데 전체회로 metric(`cmrr_estimate_db`/`psrr_estimate_db` 등
       `smallsignal_*` 타입)과는 구조상 걸쳐 있으면(footprint가 비어있지 않으면 항상 걸침
       -- `_full_circuit_devices()`가 사이징된 소자 전부를 읽으므로) **판정 보류**로 남기고
       5로.
    5. `baseline_theta_values`(기본: 호출자가 넘겨야 함 -- 없으면 실측 자체를 안 하고
       "ambiguous"로 남긴다. bounds-midpoint를 이 함수가 자동으로 만들어 쓰지 않는 이유는
       이 회로 자체가 bounds-midpoint에서 InfeasibleSizingError가 나기 때문(세션27 D-9,
       K_replica/r_classab_battery 조합) -- 실현가능한 기준점을 찾는 일은
       `extract_linear_feasibility_constraints()`/`presolve_warm_start()`의 책임이고 이
       함수는 "받은 기준점에서 재본다"만 한다, 순환 의존 회피)에서 이 theta만
       `probe_frac`(기본 5%)만큼 bounds 범위 안에서 살짝 밀어 재평가 -- 4에서 보류된 각
       전체회로 metric의 유한차분 민감도를 재고, `sensitivity_tol`(기본: `_db` 접미사
       metric은 전체 bounds 스윙에서 0.5dB, 그 외는 제약값의 1%)보다 작으면 그 metric에
       한해 "실질적으로 무관"으로 확정한다. 보류된 전체회로 metric 전부가 무관으로
       확정되면 **isolated**(numerically confirmed), 하나라도 유의미한 민감도가 나오면
       **coupled**(numerically confirmed) — 세션27 B-2(r_cmfb_vocdes, isolated로 확정될
       것으로 기대)와 N_cmfb_bw(CMFB 루프 이득에 실제로 걸림, coupled로 확정될 것으로 기대)를
       가르는 게 이 단계다.
    6. 목적함수(`objective`)에 대한 민감도(부호만, `presolve_warm_start()`가 isolated/dead
       theta를 어느 bound 극값에 놓을지 정하는 데 씀)도 같은 평가에서 함께 얻는다 --
       baseline이 있을 때만(없으면 `None`).

    반환: `{theta_name: {"classification": "dead"|"isolated"|"coupled"|"fixed"|"ambiguous",
    "feed_type", "target_devices"(list), "touches_constraints"(list of metric names,
    구조적으로 확실한 것만), "full_circuit_candidates"(list, 4에서 보류된 metric들),
    "sensitivity"({metric_name: d(metric)/d(theta)} or None), "objective_sensitivity"(float
    or None), "evidence"(str, 사람이 읽는 판정 근거)}}`. `"ambiguous"`는 baseline이
    없거나 baseline 평가 자체가 실패했거나(InfeasibleSizingError) probe 양방향이 다
    실패해 5를 못 끝낸 경우만 나온다(조용히 isolated로 단정하지 않는다) --
    `presolve_warm_start()`는 이 경우 안전한 기본값(bounds-midpoint)으로 폴백해야 한다.

    `ev`(2026-08-13 세션31, 감사 발견 'C' 구현, 선택): 이미 만들어둔 `_build_theta_
    evaluator()` 결과가 있으면 넘긴다 -- 없으면(기본, 하위호환) 이 함수가 직접 만든다.
    `presolve_warm_start()`가 `_optimize_theta_slsqp()`로부터 이미 받은 `ev`를 그대로
    물려줘, `load_topology()`+`resolve_stack_layout()` 같은 비싼 셋업과 `_comp_cache`를
    SLSQP warm-start 체인 전체(이 함수 포함 4곳)에서 재사용하기 위함이다(감사 발견:
    이전엔 동일 `(topology_path,spec)`로 5번 독립 재빌드, 매번 `_comp_cache`도 폐기됨)."""
    ev = ev or _build_theta_evaluator(topology_path, spec)
    thetas = ev["thetas"]
    metrics_specs, objective, constraints = ev["metrics_specs"], ev["objective"], ev["constraints"]
    comp, stack_groups_kcl, evaluate = ev["comp"], ev["stack_groups_kcl"], ev["evaluate"]
    stack_id_of = {name: sid for sid, members in stack_groups_kcl.items() for name in members}

    comp_param_keys = set(comp["parameters"]) if comp else set()
    b_type_readers = {}  # {derived_key: target_device} -- B타입 feed가 ctx.derived에서 읽는 키
    for _t in thetas:
        _f = _t["feeds"]
        if isinstance(_f, dict) and _f.get("type") == "B":
            b_type_readers[_f["omega_key"]] = _f["target"]

    def _expand_to_devices(feed_footprint: dict) -> set:
        devices = {d for r in feed_footprint["roots"]
                   for d in stack_groups_kcl.get(stack_id_of.get(r), {r})}
        writes = feed_footprint["derived_writes"]
        if comp and (writes & comp_param_keys):
            devices |= {d for grp in comp["stage_devices"] for d in grp}
        for key, target in b_type_readers.items():
            if key in writes:
                devices.add(target)
        return devices

    objective_metric = list(objective.values())[0]
    constraint_names = [c["metric"] for c in constraints]
    footprints = {name: _metric_device_footprint(name, metrics_specs)
                  for name in set(constraint_names) | {objective_metric}}

    graph = {}
    for theta in thetas:
        name = theta["name"]
        lo, hi = theta["bounds"]
        feed_type = theta["feeds"] if isinstance(theta["feeds"], str) else theta["feeds"]["type"]
        if lo == hi:
            graph[name] = {"classification": "fixed", "feed_type": feed_type,
                            "target_devices": [], "touches_constraints": [],
                            "full_circuit_candidates": [], "sensitivity": None,
                            "objective_sensitivity": None,
                            "evidence": f"bounds가 고정값({lo}) -- 설계 자유도 없음"}
            continue
        ff = _theta_feed_footprint(theta)
        target_devices = _expand_to_devices(ff)
        if not target_devices:
            graph[name] = {"classification": "dead", "feed_type": feed_type,
                            "target_devices": [], "touches_constraints": [],
                            "full_circuit_candidates": [], "sensitivity": None,
                            "objective_sensitivity": None,
                            "evidence": ("derived key를 아무도 안 읽음(compensation.parameters/"
                                         "B타입 omega_key 어디에도 없음) -- 값을 바꿔도 회로 "
                                         "어디에도 영향 없음")}
            continue
        touches_constraints = [c for c in constraint_names
                                if footprints[c] != "ALL" and target_devices & footprints[c]]
        full_circuit_candidates = [c for c in constraint_names
                                    if footprints[c] == "ALL" and c not in touches_constraints]
        entry = {"classification": None, "feed_type": feed_type,
                 "target_devices": sorted(target_devices),
                 "touches_constraints": touches_constraints,
                 "full_circuit_candidates": full_circuit_candidates,
                 "sensitivity": None, "objective_sensitivity": None, "evidence": None}
        if touches_constraints:
            entry["classification"] = "coupled"
            entry["evidence"] = f"명시적 footprint 겹침(구조적으로 확실) -- {touches_constraints}"
            graph[name] = entry
            continue
        if not full_circuit_candidates:
            entry["classification"] = "isolated"
            entry["evidence"] = "어떤 제약 metric도 이 theta의 소자를 읽지 않음(구조적으로 확실)"
            graph[name] = entry
            continue
        # 여기부터는 전체회로 metric과만 걸쳐 있어 구조 분석만으로는 결론 못 냄 -- 실측 필요
        if baseline_theta_values is None:
            entry["classification"] = "ambiguous"
            entry["evidence"] = ("baseline_theta_values가 없어 실측 민감도를 못 잼 -- "
                                  "extract_linear_feasibility_constraints() 등으로 먼저 "
                                  "실현가능한 기준점을 구해 다시 호출할 것")
            graph[name] = entry
            continue
        try:
            base_ctx, base_metrics = evaluate(baseline_theta_values)
        except InfeasibleSizingError as e:
            entry["classification"] = "ambiguous"
            entry["evidence"] = f"baseline_theta_values 자체가 infeasible: {e}"
            graph[name] = entry
            continue
        span = hi - lo
        base_val = baseline_theta_values[name]
        step = probe_frac * span
        probe_val = base_val + step if base_val + step <= hi else base_val - step
        probe_theta_values = dict(baseline_theta_values, **{name: probe_val})
        try:
            probe_ctx, probe_metrics = evaluate(probe_theta_values)
        except InfeasibleSizingError:
            probe_val = base_val - step if probe_val > base_val else base_val + step
            probe_theta_values[name] = probe_val
            try:
                probe_ctx, probe_metrics = evaluate(probe_theta_values)
            except InfeasibleSizingError as e:
                entry["classification"] = "ambiguous"
                entry["evidence"] = f"양방향 probe 전부 infeasible -- 민감도 측정 불가: {e}"
                graph[name] = entry
                continue
        d_theta = probe_val - base_val
        sensitivity = {m: (probe_metrics[m] - base_metrics[m]) / d_theta
                        for m in full_circuit_candidates}
        entry["sensitivity"] = sensitivity
        entry["objective_sensitivity"] = (
            (probe_metrics[objective_metric] - base_metrics[objective_metric]) / d_theta)
        tol = dict(sensitivity_tol or {})

        def _tol_for(metric_name):
            if metric_name in tol:
                return tol[metric_name]
            if metric_name.endswith("_db"):
                return 0.5 / span  # 전체 bounds 스윙에서 0.5dB
            threshold = next(c["value"] for c in constraints if c["metric"] == metric_name)
            return 0.01 * abs(threshold) / span

        negligible = {m: abs(s) < _tol_for(m) for m, s in sensitivity.items()}
        if all(negligible.values()):
            entry["classification"] = "isolated"
            entry["evidence"] = (f"전체회로 metric {full_circuit_candidates}과 구조적으로는 "
                                  f"걸쳐 있지만 실측 민감도가 전부 무시가능(threshold 대비): "
                                  f"{sensitivity}")
        else:
            entry["classification"] = "coupled"
            _sig = {m: v for m, v in sensitivity.items() if not negligible[m]}
            entry["evidence"] = f"전체회로 metric 실측 민감도가 유의미: {_sig}"
        graph[name] = entry
    return graph


# ---------------------------------------------------------------------------
# 6.9c) 웜스타트 준비 2/3 — A_signed KCL 부호제약을 선형부등식으로 자동 추출(세션29,
#       세션27 "## B" B-3 손유도의 일반화). `kcl_battery_M9b`류(`ID(root) = theta_value *
#       sum(sign_i * ID(term_i))`, root 소자가 실재 트랜지스터라 ID<=0이면 물리적으로
#       불가능 -- `InfeasibleSizingError`)에서, 각 항 소자의 ID가 **다른 free theta의
#       A/C타입 feed로 선형(theta*상수)하게 결정**되는 경우에 한해 그 관계를 부등식으로
#       역산한다(K_replica*ID_M15 <= r_classab_battery*(ID_M1a+ID_M1b) 같은 관계, 이번엔
#       손으로 안 하고 feed 선언만으로 일반화). 항이 compensation처럼 theta와 무관하게
#       고정된 값이면 상수항으로 흡수한다.
# ---------------------------------------------------------------------------

def extract_linear_feasibility_constraints(topology_path: str, spec: dict,
                                            reference_theta_values: dict = None,
                                            ev: dict | None = None) -> list:
    """SLSQP 웜스타트 준비 2/3(세션27 "## B" B-3 손유도의 일반화) — `A_signed` feed(KCL
    뺄셈, `kcl_battery_M9b` 등)가 만드는 "이 항들의 부호합이 0 이상이어야 한다"는 물리적
    제약(위반 시 `InfeasibleSizingError`)을, 가능하면 **다른 free theta들에 대한 선형
    부등식**으로 역산해 반환한다 — grid search가 이 부등식을 만족 못 하는 조합을 시행착오로
    찾아내는 대신(세션27 D-9가 실측으로 겪은 과정), `presolve_warm_start()`가 처음부터
    실현가능한 시작점을 고를 수 있게 하기 위함이다.

    **역산 절차**(항 소자 하나마다):
    1. 그 소자가 어떤 free(bounds[0]!=bounds[1]) `"A"`(root, 여러 개 가능) 또는 `"C"`
       (target) feed의 대상이면, 그 feed는 `ID(소자) = theta_value * reference_basis`
       형태다 -- `reference_basis`(A는 reference 소자들 ID 합, C는 reference 소자 1개의
       ID)는 이 항을 **그 theta에 대한 선형항**(계수=부호*reference_basis)으로 만든다.
       `reference_basis` 자체는 `reference_theta_values`에서 얼려 읽은 숫자다(그 소자들이
       또 다른 free theta에 얽혀 있어도 재귀적으로 풀지 않는다 -- 그러면 이론상 theta끼리
       곱해지는 비선형 관계가 될 수 있어, "선형" 부등식이라는 이 함수의 계약 자체가 깨진다.
       세션27 B-3 시점엔 이 reference_basis(ID_M1a+ID_M1b, ID_M15)가 compensation으로만
       고정돼 진짜 상수였지만, 세션27 후반 D-3에서 `f_slew`(free)가 `t_lln`을 거쳐
       compensation 자체에 배선돼(do.md Level1->2) 지금은 엄밀히는 `f_slew`에도 살짝
       의존한다 -- 이 함수는 그 사실을 숨기지 않고, `reference_theta_values`가 고정하는
       한 지점(기본 bounds-midpoint)에서 얼린 근사치라는 걸 그대로 반환값에 남긴다(웜스타트
       용도로는 충분 -- 최종 정확도는 SLSQP가 책임진다).
    2. 그 소자가 free feed의 대상이 아니라 **bounds가 고정된**(bounds[0]==bounds[1]) A/C
       feed의 대상이면(예: `mirror_M18a`, theta=1.0 고정), 진짜 자유도가 없는 순수
       passthrough이므로 그 고정 배수를 누적하며 `reference` 소자로 재귀 하강한다(1로
       돌아감) -- 체인이 너무 깊으면(순환 의심) 명시적 에러.
    3. 둘 다 아니면(compensation 등으로 직접 확정된 leaf, 또는 governing feed가 아예 없는
       소자) `reference_theta_values`에서 얼린 숫자 그대로 상수항에 더한다.

    A_signed 자신의 theta(예: `kcl_battery_M9b`)의 bounds가 부호를 안 가리면(0을
    가로지르면) `ID(root)=theta_value*total`의 부호가 `total`만으로 안 정해지므로 단순화를
    포기하고 `"dynamic"`으로 보고한다(이 프로젝트 회로들은 전부 이 theta가 1.0 고정이라
    해당 없음 -- 일반화를 위해 남겨둔 방어 분기).

    반환: 각 A_signed theta당 1개 dict의 리스트 -- `{"theta": name, "status": ...}`.
    `status`:
    - `"linear"`: `{"terms":[{"theta":name,"coeff":float},...], "constant":float, "op":">="}`
      (`sum(coeff_i * theta_i) + constant >= 0` 형태 -- 계수가 2개 이상이면 세션27 B-3처럼
      두 theta를 함께 골라야 하는 진짜 결합 제약, 1개면 그 theta 하나의 단순 하한/상한).
    - `"numeric_only"`: 관련 theta가 전부 상수로 얼어붙어(자유도 없음) 부등식이 아니라
      `reference_theta_values` 그 지점에서의 단순 실현가능 여부(`feasible_at_reference`)만
      의미 있음.
    - `"dynamic"`/`"unresolvable"`: 자동 역산 실패(이유는 `"reason"`) -- `presolve_warm_
      start()`는 이 theta에 한해 grid search류 폴백이 필요할 수 있다(조용히 무시하지
      말 것).

    `ev`(2026-08-13 세션31, 감사 발견 'C' 구현, 선택): `derive_theta_dependency_graph()`와
    동일한 계약 -- 없으면 직접 만든다(하위호환), 있으면 재사용."""
    ev = ev or _build_theta_evaluator(topology_path, spec)
    thetas = ev["thetas"]
    evaluate = ev["evaluate"]
    by_theta_name = {t["name"]: t for t in thetas}

    if reference_theta_values is None:
        reference_theta_values = {t["name"]: (t["bounds"][0] + t["bounds"][1]) / 2.0
                                   for t in thetas}

    try:
        ctx, _ = evaluate(reference_theta_values)
        sized = ctx.sized
    except InfeasibleSizingError as e:
        if e.sized_snapshot is None:
            raise ValueError(
                "reference_theta_values가 infeasible인데 sized_snapshot이 없다 -- "
                "InfeasibleSizingError가 A_signed ID<=0 경로가 아닌 다른 곳에서 났을 "
                "가능성, 직접 확인할 것") from e
        sized = e.sized_snapshot

    # governing[device] = (theta_name, feed, is_free) -- 이 device의 ID를 직접 결정하는
    # A(root)/C(target) feed. 여러 root를 가진 A feed는 root마다 같은 항목을 공유한다.
    governing = {}
    for t in thetas:
        feed = t["feeds"]
        if not isinstance(feed, dict):
            continue
        is_free = t["bounds"][0] != t["bounds"][1]
        if feed["type"] == "A":
            roots = feed["root"] if isinstance(feed["root"], list) else [feed["root"]]
            for r in roots:
                governing[r] = (t["name"], feed, is_free)
        elif feed["type"] == "C":
            governing[feed["target"]] = (t["name"], feed, is_free)

    def _resolve(device: str, coeff: float, depth: int = 0):
        """`coeff * ID(device)`를 (변수항 리스트, 상수) 쌍으로 분해한다."""
        if depth > 20:
            raise ValueError(f"'{device}' 근처에서 governing 체인이 너무 깊다(순환 의심)")
        if device not in governing:
            entry = sized.get(device)
            if entry is None or "ID" not in entry:
                raise ValueError(f"'{device}'의 ID를 reference point에서 못 구함(governing "
                                  f"체인도 없음) -- 선언 누락이거나 평가 순서 문제")
            return [], coeff * entry["ID"]
        theta_name, feed, is_free = governing[device]
        if is_free:
            basis = (sum(sized[r]["ID"] for r in feed["reference"]) if feed["type"] == "A"
                      else sized[feed["reference"]]["ID"])
            return [{"theta": theta_name, "coeff": coeff * basis}], 0.0
        fixed_val = by_theta_name[theta_name]["bounds"][0]
        refs = feed["reference"] if feed["type"] == "A" else [feed["reference"]]
        var_terms, const = [], 0.0
        for ref_dev in refs:
            v, c = _resolve(ref_dev, coeff * fixed_val, depth + 1)
            var_terms += v
            const += c
        return var_terms, const

    results = []
    for theta in thetas:
        feed = theta["feeds"]
        if not (isinstance(feed, dict) and feed.get("type") == "A_signed"):
            continue
        lo, hi = theta["bounds"]
        if not ((lo >= 0 and hi >= 0) or (lo <= 0 and hi <= 0)):
            results.append({"theta": theta["name"], "status": "dynamic",
                             "reason": ("이 A_signed theta 자신의 bounds가 부호를 안 가려서"
                                        "(0을 가로지름) ID(root)=theta*total의 부호를 total "
                                        "부호만으로 단순화할 수 없다")})
            continue
        try:
            all_var_terms, const_sum = [], 0.0
            for term in feed["terms"]:
                v, c = _resolve(term["device"], term.get("sign", 1))
                all_var_terms += v
                const_sum += c
        except ValueError as e:
            results.append({"theta": theta["name"], "status": "unresolvable", "reason": str(e)})
            continue
        merged: dict = {}
        for vt in all_var_terms:
            merged[vt["theta"]] = merged.get(vt["theta"], 0.0) + vt["coeff"]
        variable_terms = [{"theta": k, "coeff": v} for k, v in merged.items() if v != 0.0]
        if not variable_terms:
            results.append({"theta": theta["name"], "status": "numeric_only",
                             "feasible_at_reference": const_sum >= 0, "value": const_sum,
                             "reason": ("관련 항이 전부 (근사)상수 -- 자유 theta 쌍 관계가 "
                                        "아니라 reference_theta_values 지점에서의 단순 "
                                        "실현가능성만 확인됨")})
            continue
        results.append({
            "theta": theta["name"], "status": "linear",
            "inequality": {"terms": variable_terms, "constant": const_sum, "op": ">="},
            "reason": (f"sum(coeff_i * theta_i) + {const_sum:.6g} >= 0 -- 계수는 "
                       f"reference_theta_values에서 얼린 다른(governing 아닌) theta들 기준 "
                       f"근사(위 docstring 1 참고)")})
    return results


# ---------------------------------------------------------------------------
# 6.9c-2) 웜스타트 준비 2.5/3 — metric_stage_budget theta(L_cascode/L_stage2out류)의
#         L을 LUT만으로(51소자 evaluate() 없이) 직접 찾는다(세션27 B-5 설계의 실제 구현,
#         세션29 배선). 이 feed 타입은 ID를 안 건드리므로(_feed_metric_stage_budget()
#         참고) 목적함수(power)엔 아예 영향이 없다 -- SLSQP가 objective gradient 0인 이런
#         차원을 다른 차원과 같이 gradient 기반으로 섞어 최적화하다가 잘못된 방향(gain
#         crash)으로 밀어버리는 걸 세션29 실측으로 확인(n_starts=6 중 4번이 똑같이 낮은
#         gain_db로 수렴)했다 -- SLSQP 자유변수에서 아예 빼고 이 함수가 찾은 값을 고정값
#         으로 쓴다(presolve_warm_start()/_optimize_theta_slsqp() 배선).
# ---------------------------------------------------------------------------

def search_stage_budget_L_warm_start(topology_path: str, spec: dict,
                                      reference_theta_values: dict = None,
                                      n_scan: int = 61, n_scan_full_circuit: int = 21,
                                      ev: dict | None = None) -> dict:
    """metric_stage_budget theta(`L_cascode`/`L_stage2out`류)의 웜스타트 L을 찾는다
    (세션27 B-5가 손으로 확인한 두 가지 사실의 일반화 구현). theta별로 이 소자들의
    devices에 **명시적으로 걸린** constraint 타입 집합을 본다:

    - `gain_stages_sum` **하나만** 걸린 theta(예: `L_cascode`) -- LUT만으로(51소자
      `evaluate()` 불필요) 이 theta의 devices만의 gm/gds 비를 bounds 양끝에서 비교해,
      constraint 방향(`>=`면 큰 쪽, `<=`면 작은 쪽)에 유리한 극값을 고른다(세션27 실측:
      gm/gds가 L에 단조증가 -- 다른 stage device는 이 theta의 L에 안 걸리므로 이 theta
      몫의 소자만으로 방향 판단에 충분하고 안전하다).
    - `battery_centering_deviation` **하나만** 걸린 theta -- 마찬가지로 LUT만으로
      bounds를 `n_scan`점 그리드 스캔해(단조성 가정 없음) `|deviation|` 최소 L을 고른다.
    - **둘 다 걸린** theta(예: `L_stage2out`) -- ⚠️ 2026-08-11(세션29) 실측으로 발견한
      함정: `battery_centering_deviation`만 보고 최소화하면 그 최소점이 `gain_stages_sum`
      을 크게 깨뜨릴 수 있다(이 회로 실측: centering만 최소화한 L=1.64e-7에서
      `gain_db`가 77.2dB -> 58.9dB로 붕괴, SLSQP가 6번 중 4번 똑같이 이 값에 갇힘) --
      `gain_stages_sum`은 다른 stage(예: M1a/M4a, 이 theta가 L을 안 정하는 소자)의
      기여도 합산하므로 LUT만으로는(이 theta의 devices만 봐서는) 안전하게 판단할 수
      없다. 이런 theta는 `reference_theta_values`(기본 bounds-midpoint, 나머지 free
      theta는 이미 정해진 값 그대로)로 다른 모든 값을 고정한 채 `n_scan_full_circuit`점만
      **실제 51소자 `evaluate()`로** 스캔해, 걸린 constraint를 전부 만족하는 점 중
      centering이 최소인 것(전부 만족하는 점이 없으면 위반량 합이 최소인 것)을 고른다 --
      점 수를 줄이는 대신(그리드 스캔이 아니라 21점) 정직하게 실측한다.
    - 아무 것도 안 걸리면(등록 안 된 metric type뿐이거나 constraint 자체가 없음) bounds-
      midpoint로 후퇴한다(조용히 방향을 추측하지 않는다).

    반환: `{theta_name: L_value}` -- `metric_stage_budget` feed가 아니거나 bounds가
    고정된(자유도 0) theta는 포함하지 않는다. 이미 처리된 theta의 값은 다음 theta의
    `reference_theta_values`에도 반영된다(처리 순서: LUT-only 먼저, 실측-스캔 나중 --
    `L_cascode`가 먼저 정해져야 `L_stage2out`의 실측 스캔이 그 값을 올바르게 반영한다).

    `ev`(2026-08-13 세션31, 감사 발견 'C' 구현, 선택): `derive_theta_dependency_graph()`와
    동일한 계약 -- 없으면 직접 만든다(하위호환), 있으면 재사용."""
    ev = ev or _build_theta_evaluator(topology_path, spec)
    thetas, metrics_specs, constraints = ev["thetas"], ev["metrics_specs"], ev["constraints"]
    kind_of, evaluate = ev["kind_of"], ev["evaluate"]

    if reference_theta_values is None:
        reference_theta_values = {t["name"]: (t["bounds"][0] + t["bounds"][1]) / 2.0 for t in thetas}
    reference = dict(reference_theta_values)

    def _vgs(name, L, gm_id, vds, vs):
        lut = spec["lut_by_kind"][kind_of[name]]
        return lut.vgs_for_gm_id(gm_id, L, vds, vs)

    def _centering_dev(L, high, low, gm_id, vds, vs):
        vgs_h = _vgs(high, L, gm_id, vds, vs)
        level_h = (spec["vdd"] - vgs_h) if kind_of[high] == "pmos" else (0.0 + vgs_h)
        vgs_l = _vgs(low, L, gm_id, vds, vs)
        level_l = (spec["vdd"] - vgs_l) if kind_of[low] == "pmos" else (0.0 + vgs_l)
        return abs((level_h + level_l) - spec["vdd"])

    def _mean_gm_gds_db(L, devices, gm_id, vds, vs):
        ratios = [spec["lut_by_kind"][kind_of[d]].gm_gds_ratio(gm_id, L, vds, vs) for d in devices]
        return 20 * math.log10(sum(ratios) / len(ratios))

    def _touching(devices):
        found = []
        for c in constraints:
            fp = _metric_device_footprint(c["metric"], metrics_specs)
            if fp != "ALL" and (set(devices) & fp):
                found.append(c)
        return found

    stage_thetas = [t for t in thetas
                     if isinstance(t["feeds"], dict) and t["feeds"].get("type") == "metric_stage_budget"
                     and t["bounds"][0] != t["bounds"][1]]

    # 2026-08-13(세션31, 사용자 지시) -- 이 함수가 다루는 theta는 전부 metric_stage_budget
    # (theta_value 자체가 L)이므로 spec["L_grid_step"](공정 레이아웃 그리드 해상도, m 단위)로
    # 전부 스냅한다 -- 값 자체는 이 엔진이 추측하지 않는다(quantize_L() docstring 참고).
    _l_grid_step = spec.get("L_grid_step") if stage_thetas else None
    if stage_thetas and _l_grid_step is None:
        raise ValueError(
            f"metric_stage_budget(L) theta {[t['name'] for t in stage_thetas]}가 있는데 "
            f"spec['L_grid_step']이 없다 -- 공정 레이아웃 그리드 해상도(m 단위)를 명시적으로 "
            f"선언할 것")

    result = {}
    complex_thetas = []
    for theta in stage_thetas:
        feed = theta["feeds"]
        devices = feed["devices"]
        touching = _touching(devices)
        types = {metrics_specs[c["metric"]]["type"] for c in touching}
        if len(types & {"gain_stages_sum", "battery_centering_deviation"}) > 1:
            complex_thetas.append(theta)  # 경쟁하는 제약 -- 3단계(실측 스캔)로 미룸
            continue
        lo, hi = theta["bounds"]
        gm_id, vds, vs = feed.get("gm_id", 15.0), feed.get("vds", 0.6), feed.get("vs", 0.0)
        if "battery_centering_deviation" in types:
            mspec = metrics_specs[next(c["metric"] for c in touching
                                        if metrics_specs[c["metric"]]["type"] == "battery_centering_deviation")]
            best_L, best_dev = None, None
            for L in _grid_points_in_range(lo, hi, _l_grid_step, n=n_scan):
                dev = _centering_dev(L, mspec["high_device"], mspec["low_device"], gm_id, vds, vs)
                if best_dev is None or dev < best_dev:
                    best_L, best_dev = L, dev
            result[theta["name"]] = best_L
        elif "gain_stages_sum" in types:
            db_lo = _mean_gm_gds_db(lo, devices, gm_id, vds, vs)
            db_hi = _mean_gm_gds_db(hi, devices, gm_id, vds, vs)
            gain_c = next(c for c in touching
                          if metrics_specs[c["metric"]]["type"] == "gain_stages_sum")
            wants_high = gain_c["op"] in (">=", ">")
            # 2026-08-13(세션31) -- hi/lo를 그대로 쓰면 bounds 자체가 그리드에 안 맞을 수
            # 있다 -- floor(hi)/ceil(lo)로 bounds 안쪽으로 스냅(바깥으로 벗어나지 않게).
            result[theta["name"]] = (quantize_L(hi, _l_grid_step, "floor")
                                      if (db_hi >= db_lo) == wants_high
                                      else quantize_L(lo, _l_grid_step, "ceil"))
        else:
            result[theta["name"]] = quantize_L((lo + hi) / 2.0, _l_grid_step)
        reference[theta["name"]] = result[theta["name"]]

    # 2026-08-13(세션31, 사용자 지시 "조인트 탐색으로 고쳐줘") -- complex_thetas를 서로
    # 얽힌 그룹으로 묶는다: 같은 battery_centering_deviation metric을 건드리는 theta들은
    # 서로 독립이 아니다(그 metric 값 자체가 그 theta들이 각각 sizing하는 소자 전부에
    # 의존하므로 -- 예: classab_centering_dev_v는 L_stage2out_p가 정하는 M15와
    # L_stage2out_n이 정하는 M16 둘 다 필요). 이전(순차 1D: theta 하나씩 스캔해 reference에
    # 반영한 뒤 다음 theta 스캔)은 greedy coordinate descent 1라운드라 전역 최적을 놓칠 수
    # 있다(실측 발견: gm_id_role/gm_id_match_vgs_of 도입으로 centering은 풀렸는데도 gain_db가
    # 71dB대에 갇힘 -- L_p/L_n을 실제로 함께(조인트로) 스캔하면 75.6dB 이상 지점이 존재함이
    # 별도 조사로 이미 확인됨, `.ai/context.md` 세션31 BI/BJ 참고).
    _groups, _group_idx_by_metric = [], {}
    for theta in complex_thetas:
        touching = _touching(theta["feeds"]["devices"])
        centering_metric = next(c["metric"] for c in touching
                                 if metrics_specs[c["metric"]]["type"] == "battery_centering_deviation")
        if centering_metric not in _group_idx_by_metric:
            _group_idx_by_metric[centering_metric] = len(_groups)
            _groups.append([])
        _groups[_group_idx_by_metric[centering_metric]].append(theta)

    for group in _groups:
        names = [t["name"] for t in group]
        all_touching = {}
        for t in group:
            for c in _touching(t["feeds"]["devices"]):
                all_touching[c["metric"]] = c  # 이름으로 중복 제거(그룹 멤버들이 겹치는 게 정상)
        touching = list(all_touching.values())
        centering_metric = next(c["metric"] for c in touching
                                 if metrics_specs[c["metric"]]["type"] == "battery_centering_deviation")
        k = len(group)
        # 2026-08-13(세션31, "재계산 비효율 보장" 지시) -- 조인트 스캔은 그룹 크기 k에 대해
        # 지수적으로 커진다(k차원 × 차원당 n점 = n^k evaluate() 호출, 각 호출이 51소자
        # 실회로 전체를 푸는 무거운 연산). k=1이면 옛 순차 방식과 완전히 동일한 예산
        # (per_dim_n=n_scan_full_circuit)으로 폴백하고, k>=2부터는 "총 evaluate() 호출 수를
        # 옛 순차 방식의 총 예산(k*n_scan_full_circuit, 선형)과 같은 자릿수로 유지"하도록
        # 차원당 점수를 줄인다(target_total**(1/k)) -- 그룹이 커져도 총 비용이 폭발하지 않고
        # 옛 방식과 같은 선형 오더를 유지한다.
        target_total = k * n_scan_full_circuit
        per_dim_n = n_scan_full_circuit if k == 1 else max(2, round(target_total ** (1.0 / k)))
        grids = [_grid_points_in_range(t["bounds"][0], t["bounds"][1], _l_grid_step, n=per_dim_n)
                 for t in group]
        best_combo, best_score, best_feasible = None, None, False
        for combo in itertools.product(*grids):
            trial = dict(reference, **dict(zip(names, combo)))
            try:
                _, metrics = evaluate(trial)
            except InfeasibleSizingError:
                continue
            violations = [max(0.0, c["value"] - metrics[c["metric"]]) if c["op"] in (">=", ">")
                          else max(0.0, metrics[c["metric"]] - c["value"])
                          for c in touching]
            feasible = all(v == 0.0 for v in violations)
            score = metrics[centering_metric] if feasible else sum(violations)
            if best_combo is None or (feasible and not best_feasible) \
                    or (feasible == best_feasible and score < best_score):
                best_combo, best_score, best_feasible = combo, score, feasible
        if best_combo is None:
            best_combo = tuple(quantize_L((t["bounds"][0] + t["bounds"][1]) / 2.0, _l_grid_step)
                                for t in group)
        for name, L in zip(names, best_combo):
            result[name] = L
            reference[name] = L

    return result


# ---------------------------------------------------------------------------
# 6.9d) 웜스타트 준비 3/3 — SLSQP 시작점(x0) 조립(세션29, 세션27 "## B" 웜스타트 설계의
#       실제 구현). `extract_linear_feasibility_constraints()`로 실현가능한 기준점을 먼저
#       확보하고(bounds-midpoint 전체가 이 회로에서 실제로 infeasible이기 때문 -- 세션27
#       D-9), 그 기준점에서 `derive_theta_dependency_graph()`로 얻은 dead/isolated/coupled
#       분류를 조합해 각 theta의 시작값을 정한다.
# ---------------------------------------------------------------------------

def presolve_warm_start(topology_path: str, spec: dict, ev: dict | None = None) -> dict:
    """SLSQP 웜스타트 준비 3/3(세션27 "## B" 설계의 실제 구현) — `extract_linear_
    feasibility_constraints()` + `derive_theta_dependency_graph()`를 조합해 SLSQP
    시작점(x0)을 만든다. `optimize_full_circuit_budget()`이 grid search로 하던 일(θ*
    선택)을 SLSQP로 바꿀 때, "아무 데서나 시작(bounds-midpoint)"이 이 회로에서는 이미
    실현 불가능(세션27 D-9)이므로 이 함수가 반드시 선행돼야 한다.

    **조립 순서**:
    1. `extract_linear_feasibility_constraints()`(기본 bounds-midpoint 기준점)로 `A_signed`
       KCL 부호제약을 선형부등식으로 얻는다. `"linear"` 결과의 각 항 `{theta, coeff}`에서
       "이 부등식을 만족시키려면 이 theta는 어느 극값(coeff>0이면 상한, coeff<0이면
       하한)이 유리한가"를 투표로 모은다 -- 같은 theta가 서로 다른 부등식에서 다른 극값을
       요구하면(실제로 이 회로에선 발생하지 않음, 방어적으로만 처리) 자동 해결을 포기하고
       bounds-midpoint로 남긴 뒤 `notes`에 남긴다.
    2. 투표가 일치하는 theta는 그 극값으로, 나머지는 bounds-midpoint로 둔 **실현가능한
       기준점**(`baseline`)을 만든다 -- 세션27 D-9의 `K_replica=하한/r_classab_battery=상한`
       손튜닝을 자동 재현하는 지점이 바로 이것.
    3. 이 `baseline`으로 `derive_theta_dependency_graph()`를 호출해 나머지(선형제약과
       무관한) theta 전부를 dead/isolated/coupled로 분류한다.
    4. 최종 x0: 선형제약 투표가 있던 theta는 그 값 그대로(제약 충족이 목적함수 방향보다
       우선 -- infeasible로 SLSQP가 아예 시작을 못 하는 것보다 낫다), 그 외는 분류별로
       -- `fixed`/`dead` → 하한, `isolated` → `objective_sensitivity` 부호로 유리한 극값,
       `coupled`/`ambiguous` → bounds-midpoint(닫힌 관계 없음, SLSQP가 직접 풀 몫).
    5. 조립된 x0를 실제로 한 번 평가해(`evaluate()`) 정말 실현가능한지 확인하고 결과에
       포함한다(조용히 "아마 될 것"이라고 가정하지 않는다).

    2026-08-11(세션29 계속) -- `metric_stage_budget` theta(`L_cascode`/`L_stage2out`류)는
    `search_stage_budget_L_warm_start()`로 LUT만 써서(51소자 evaluate() 불필요) 직접
    찾은 값을 쓴다(세션27 B-5 설계의 실제 구현) -- SLSQP가 objective gradient 0인 이
    차원들을 다른 차원과 섞어 gradient 기반으로 최적화하다 잘못된 방향(gain crash)으로
    밀어버리는 걸 실측으로 확인한 뒤 추가(아래 `stage_budget_L` 참고).

    반환: `{"x0": {theta_name: value}, "feasible": bool, "infeasible_reason": str|None,
    "linear_constraints": extract_linear_feasibility_constraints()의 반환값 그대로,
    "dependency_graph": derive_theta_dependency_graph()의 반환값 그대로, "notes": [str,...],
    "vote_determined": [theta_name,...], "stage_budget_L": [theta_name,...]}` --
    `vote_determined`는 선형 feasibility 투표로 값이 이미 정해진 theta 이름 목록,
    `stage_budget_L`은 `search_stage_budget_L_warm_start()`로 값이 정해진 theta 이름
    목록(세션29 `_optimize_theta_slsqp()`가 이 둘을 합쳐 SLSQP 자유변수에서 제외하는 데
    씀 -- `InfeasibleSizingError` 경계 근처는 gradient가 평평해
    SLSQP가 다루기 나쁘고, 이미 실현가능하게 골라둔 값을 잃을 위험도 있다).

    `ev`(2026-08-13 세션31, 감사 발견 'C' 구현, 선택): 이미 만들어둔 `_build_theta_
    evaluator()` 결과가 있으면 넘긴다(`_optimize_theta_slsqp()`가 자신이 받은 `ev`를
    그대로 넘겨준다) -- 없으면(기본, 하위호환) 이 함수가 직접 만든다. 아래 3개 하위함수
    (`extract_linear_feasibility_constraints()`/`search_stage_budget_L_warm_start()`/
    `derive_theta_dependency_graph()`) 호출에도 그대로 물려준다 -- 감사 발견: 이전엔
    `optimize_full_circuit_budget()`이 이미 만든 `ev`를 이 함수부터 시작해 무시하고
    동일 `(topology_path,spec)`로 5번(이 함수 자신 포함) 독립 재빌드했다(`load_topology()`/
    `resolve_stack_layout()` 재실행 + `_comp_cache` 매번 폐기)."""
    ev = ev or _build_theta_evaluator(topology_path, spec)
    thetas = ev["thetas"]
    objective, evaluate = ev["objective"], ev["evaluate"]
    by_theta_name = {t["name"]: t for t in thetas}
    minimize = "minimize" in objective

    def _better_bound(lo, hi, sensitivity):
        if not sensitivity:  # None 또는 0.0 -- 방향 정보 없음, 안정적 기본값
            return lo
        increasing_is_good = (sensitivity < 0) if minimize else (sensitivity > 0)
        return hi if increasing_is_good else lo

    linear_results = extract_linear_feasibility_constraints(topology_path, spec, ev=ev)
    notes = []
    votes: dict = {}
    for r in linear_results:
        if r["status"] != "linear":
            continue
        for term in r["inequality"]["terms"]:
            name = term["theta"]
            if by_theta_name[name]["bounds"][0] == by_theta_name[name]["bounds"][1]:
                continue  # 자유도 없는 theta -- 투표 대상 아님
            votes.setdefault(name, set()).add("hi" if term["coeff"] > 0 else "lo")

    baseline = {t["name"]: (t["bounds"][0] + t["bounds"][1]) / 2.0 for t in thetas}
    vote_choice: dict = {}
    conflicts = []
    for name, prefs in votes.items():
        lo, hi = by_theta_name[name]["bounds"]
        if len(prefs) == 1:
            choice = hi if next(iter(prefs)) == "hi" else lo
            baseline[name] = choice
            vote_choice[name] = choice
        else:
            conflicts.append(name)
    if conflicts:
        notes.append(f"선형 feasibility 부등식이 서로 다른 방향을 요구하는 theta: {conflicts} "
                      f"-- 자동 해결 불가, bounds-midpoint로 남김(SLSQP가 처리해야 함)")

    stage_budget_L = search_stage_budget_L_warm_start(topology_path, spec,
                                                        reference_theta_values=baseline, ev=ev)
    for name, val in stage_budget_L.items():
        baseline[name] = val

    graph = derive_theta_dependency_graph(topology_path, spec, baseline_theta_values=baseline, ev=ev)

    x0 = {}
    for t in thetas:
        name = t["name"]
        lo, hi = t["bounds"]
        if name in vote_choice:
            x0[name] = vote_choice[name]
            continue
        if name in stage_budget_L:
            x0[name] = stage_budget_L[name]
            continue
        entry = graph[name]
        cls = entry["classification"]
        if cls in ("fixed", "dead"):
            x0[name] = lo
        elif cls == "isolated":
            x0[name] = _better_bound(lo, hi, entry["objective_sensitivity"])
        else:  # "coupled" 또는 "ambiguous" -- 닫힌 관계 없음, SLSQP가 직접 풀 몫
            x0[name] = baseline[name]
            if cls == "ambiguous":
                notes.append(f"{name}: derive_theta_dependency_graph()가 ambiguous로 분류"
                              f"(실측 민감도 확인 실패, evidence={entry['evidence']!r}) -- "
                              f"bounds-midpoint로 폴백")

    try:
        evaluate(x0)
        feasible, infeasible_reason = True, None
    except InfeasibleSizingError as e:
        feasible, infeasible_reason = False, str(e)
        notes.append("조립된 x0가 실제로는 infeasible -- 위 notes의 conflict/ambiguous 항목을 "
                      "우선 확인할 것")

    return {"x0": x0, "feasible": feasible, "infeasible_reason": infeasible_reason,
            "linear_constraints": linear_results, "dependency_graph": graph, "notes": notes,
            "vote_determined": sorted(vote_choice), "stage_budget_L": sorted(stage_budget_L)}


# ---------------------------------------------------------------------------
# 6.9e) θ* 탐색 엔진 2/2 — SLSQP + multi-start(세션27 "## A" 확정, 세션29 실제 구현).
#       grid search(§6.9 본 루프)의 대안 -- `optimize_full_circuit_budget(...,
#       search_method="slsqp")`가 이 엔진을 호출한다. grid search는 재현성/최적성이
#       보장되지만 자유 theta가 늘수록 `grid_points_per_theta**N`로 폭발한다(세션27
#       실측: 13개 theta, 촘촘한 격자는 수 시간). SLSQP는 `presolve_warm_start()`가
#       만든 실현가능한 시작점에서 지역 최적화하고, multi-start로 non-convexity를 보완한다.
# ---------------------------------------------------------------------------

def _optimize_theta_slsqp(topology_path: str, spec: dict, ev: dict,
                           n_starts: int = 6, maxiter: int = 80,
                           eps: float = 2e-3, perturb_frac: float = 0.3,
                           random_seed: int = 0, progress: bool = True) -> tuple:
    """SLSQP + multi-start(세션27 "## A" 확정 방향)로 θ*를 찾는다 -- `optimize_full_
    circuit_budget(..., search_method="slsqp")`의 내부 구현. 세션27 "## A"가 미리
    정리해둔 실전 이슈 3가지를 그대로 반영한다:

    (1) **`InfeasibleSizingError` -> penalty**: SLSQP는 목적함수/제약함수가 예외를
        던지는 걸 못 다룬다 -- 이 예외가 나면 목적함수는 큰 상수(`_SLSQP_PENALTY`)를,
        제약함수는 크게 위반된 값을 돌려줘 SLSQP가 그 방향을 피하도록 유도한다.
    (2) **유한차분 step 크기**: theta들의 물리 단위/범위가 완전히 다르다(`L_cascode`류는
        ~1e-7 스케일, `r_*` 비율은 0.02~0.9 스케일) -- 전부 [0,1] 정규화 좌표
        (`(theta-lo)/(hi-lo)`)로 최적화해 단일 `eps`가 모든 차원에서 비슷한 의미를
        갖게 한다(정규화 안 하면 스케일 작은 차원은 유한차분이 사실상 0 step이 되어
        gradient가 0으로 나올 위험).
    (3) **multi-start**: 여전히 필수(non-convex, cmrr/psrr가 전체회로 MNA라 국소
        최적해가 여럿일 수 있음). 시작점 1개는 `presolve_warm_start()`의 x0, 나머지는
        그 x0에서 SLSQP 자유변수(아래 참고)만 무작위로 흔든 변형이다.

    자유도가 0인(bounds[0]==bounds[1]) theta는 애초에 최적화 벡터에서 제외하고 고정값
    그대로 쓴다(grid search의 "고정값 theta는 1개 점만 평가" 최적화와 동일한 발상).
    2026-08-11(세션29, 실측 프로파일링 후 추가) -- **SLSQP 자유변수도 `derive_theta_
    dependency_graph()`가 `"coupled"`/`"ambiguous"`로 분류하고, 선형 feasibility 투표
    (`"vote_determined"`)나 `search_stage_budget_L_warm_start()`(`"stage_budget_L"`)로
    값이 정해지지 않은 theta로만 제한한다.** dead/isolated/vote-determined/stage-budget-L
    theta는 이미 닫힌 관계(또는 LUT 직접탐색)로 최적값(또는 실현가능한 값)이 확정돼 있어
    더 흔들 이유가 없다. vote-determined theta(예: `K_replica`)는 `InfeasibleSizingError`
    경계 바로 위에 있어 그 근처에서 유한차분 gradient가 평평하거나(penalty 상수) 오히려
    실현가능성을 깨뜨릴 위험이 있고, `metric_stage_budget` theta(`L_cascode`/`L_stage2out`
    류)는 objective(power) gradient가 구조적으로 0이라 다른 차원과 섞여 최적화되면 방향을
    잃는다는 게 실측 확인됐다(6회 multi-start 중 4회가 정확히 같은 낮은 gain_db로 수렴).
    자유 차원 수를 줄이는 게 이 회로에서 13개 중 절반 이하로 실측 확인됨(evaluate() 1회가
    LUT 보간 비용 때문에 초 단위로 느려서 -- 아래 캐시 참고 -- 차원 수가 곧 런타임).

    **성능(세션29 실측 프로파일링)**: `evaluate()` 1회가 이 회로+sky130 샘플 LUT
    조합에서 ~7~8초 걸린다(주로 `optimize_multistage()`의 LUT 격자 브루트포스 —
    `find_optimal_sizing()` — 와 `search_gm_id_for_role()`의 다회 LUT 보간). 두 가지로
    완화한다: (a) 이 함수 안에서 목적함수/제약함수가 **같은 x에서 evaluate()를 매번
    새로 부르지 않도록** 캐싱(SLSQP가 유한차분 gradient를 구할 때 같은 x에서 목적함수와
    제약함수 5개를 각각 부르므로 캐시 없이는 6배 중복 호출됨), (b) `_build_theta_
    evaluator()`(`sizing_recipe.py`)의 comp_params 캐시 — theta 하나만 바뀐 유한차분
    점들 중 `f_slew`(compensation의 `t_lln`에 유일하게 영향)가 안 바뀐 점들은
    `optimize_multistage()`를 다시 안 돈다. 그래도 여전히 evaluate() 1회가 수 초대라
    `maxiter`/`n_starts`를 무작정 키우지 말 것 — 기본값은 이 비용을 감안해 보수적으로
    잡았다.

    각 SLSQP 실행 결과는 **다시 실제 `constraints`로 재검증**한다(SLSQP가 tolerance
    안에서 살짝 위반된 해를 `success=True`로 보고할 수 있어서, grid search가 하듯 최종
    후보는 항상 실측으로 재확인 -- 이 프로젝트 전반의 "role/추정 대신 declared 계산과
    대조" 원칙과 같은 정신). 전부 실패하면 `ValueError`(조용히 최선의 infeasible 해를
    반환하지 않는다).

    반환: `(theta_star: dict, sizing: dict, metrics_result: dict)` -- grid search
    분기(`optimize_full_circuit_budget()`)와 동일한 반환 계약, 호출부가 이후 로직
    (finger geometry 등)을 분기 없이 재사용할 수 있게 한다.

    `progress=True`(기본)면 시작점/반복마다 `print()`로 진행 상황(경과시간/objective/
    최대 제약위반량)을 찍는다(2026-08-11 세션29 추가 -- evaluate() 1회가 여전히 초 단위라
    반복이 몇십 번이면 전체가 수십 분짜리 블랙박스가 되는 문제를 실측으로 겪었다 --
    scipy의 `callback`을 그대로 활용, 이미 이번 스텝에서 평가한 x라 `_eval_cache`가
    캐시로 갖고 있어 추가 evaluate() 호출 없이 공짜로 찍는다)."""
    try:
        import numpy as _np
    except ImportError as e:
        raise ImportError("search_method='slsqp'는 numpy가 필요하다 (`pip install numpy`)") from e
    try:
        from scipy.optimize import minimize as _scipy_minimize
    except ImportError as e:
        raise ImportError(
            "search_method='slsqp'는 scipy가 필요하다 -- Windows 네이티브 인터프리터로 "
            "`python -m pip install scipy` (CLAUDE.md 실행환경 참고, MSYS2 python 아님)") from e
    import random as _random

    thetas = ev["thetas"]
    objective, constraints = ev["objective"], ev["constraints"]
    evaluate = ev["evaluate"]

    # 2026-08-13(세션31, 감사 발견 'C' 구현) -- 위에서 이미 받은 ev(호출부 optimize_full_
    # circuit_budget()이 만든 것)를 그대로 넘겨 presolve_warm_start() 이하 체인 전체가
    # _build_theta_evaluator()를 재빌드하지 않게 한다(감사 발견: 이전엔 여기서부터 동일
    # (topology_path,spec)로 5번 독립 재빌드 -- load_topology()/resolve_stack_layout()
    # 재실행 + _comp_cache 매번 폐기, presolve_warm_start() docstring 참고).
    warm = presolve_warm_start(topology_path, spec, ev=ev)
    x0_dict, graph = warm["x0"], warm["dependency_graph"]
    held_names = set(warm["vote_determined"]) | set(warm["stage_budget_L"])
    free_thetas = [t for t in thetas if t["bounds"][0] != t["bounds"][1]
                   and t["name"] not in held_names
                   and graph.get(t["name"], {}).get("classification") in ("coupled", "ambiguous")]
    fixed_theta_values = {t["name"]: x0_dict[t["name"]] for t in thetas
                           if t not in free_thetas}
    if not free_thetas:
        # SLSQP를 돌릴 자유변수가 없다(전부 고정/dead/isolated/vote-determined) -- x0
        # 그대로 1회 평가해 반환.
        ctx, metrics_result = evaluate(fixed_theta_values)
        return dict(fixed_theta_values), ctx.sized, metrics_result

    names = [t["name"] for t in free_thetas]
    lo = _np.array([t["bounds"][0] for t in free_thetas])
    hi = _np.array([t["bounds"][1] for t in free_thetas])
    span = hi - lo  # free_thetas만 다루므로 전부 >0 보장(bounds[0]!=bounds[1]로 이미 필터링)

    # 2026-08-13(세션31, 사용자 지시) -- SLSQP는 연속최적화라 L-타입 theta(metric_stage_
    # budget, theta_value 자체가 L)도 임의 소수점 값을 낸다 -- 격자로 제약하면 gradient
    # 기반 탐색 자체가 깨지므로 탐색은 그대로 연속으로 두고, 최종 결과에만
    # spec["L_grid_step"]로 스냅한다(아래 재검증 직전 -- _to_theta_values() 바로 다음
    # 참고). raw 결과는 검증하지 않고 스냅된 값 하나만 검증해 evaluate() 호출 횟수를
    # 스냅 도입 전/후 정확히 동일하게 유지한다(재계산 비효율 방지 지시 참고).
    _l_theta_names = {n for n, t in zip(names, free_thetas)
                       if isinstance(t["feeds"], dict) and t["feeds"].get("type") == "metric_stage_budget"}
    if _l_theta_names and spec.get("L_grid_step") is None:
        raise ValueError(
            f"SLSQP 자유변수에 metric_stage_budget(L) theta {sorted(_l_theta_names)}가 "
            f"있는데 spec['L_grid_step']이 없다 -- 공정 레이아웃 그리드 해상도(m 단위)를 "
            f"명시적으로 선언할 것")

    def _snap_l_thetas(theta_values):
        if not _l_theta_names:
            return theta_values
        step = spec["L_grid_step"]
        return {n: (quantize_L(v, step) if n in _l_theta_names else v)
                for n, v in theta_values.items()}

    def _to_theta_values(x_norm):
        vals = lo + _np.clip(x_norm, 0.0, 1.0) * span
        theta_values = dict(fixed_theta_values)
        theta_values.update(zip(names, (float(v) for v in vals)))
        return theta_values

    minimize_metric = "minimize" in objective
    objective_metric = objective["minimize"] if minimize_metric else objective["maximize"]
    _SLSQP_PENALTY = 1e6

    # x_norm(같은 점)에서 목적함수 1개 + 제약함수 5개가 각자 evaluate()를 새로 부르면
    # 유한차분 gradient 계산 때마다 동일 x를 최대 (1+len(constraints))배 중복 평가하게
    # 된다 -- evaluate() 자체가 순수함수(같은 theta_values -> 같은 결과)이므로 x_norm을
    # 반올림한 튜플로 캐싱해 이 중복을 없앤다.
    _eval_cache: dict = {}

    def _cached_evaluate(x_norm):
        key = tuple(round(float(v), 9) for v in x_norm)
        if key not in _eval_cache:
            _eval_cache[key] = evaluate(_to_theta_values(x_norm))
        return _eval_cache[key]

    def _objective_fn(x_norm):
        try:
            _, metrics = _cached_evaluate(x_norm)
        except InfeasibleSizingError:
            return _SLSQP_PENALTY
        val = metrics[objective_metric]
        return val if minimize_metric else -val

    def _make_constraint_fn(c):
        op = c["op"]
        def _fn(x_norm):
            try:
                _, metrics = _cached_evaluate(x_norm)
            except InfeasibleSizingError:
                return -_SLSQP_PENALTY  # 강한 위반으로 취급해 SLSQP가 이 방향을 피하게 함
            val = metrics[c["metric"]]
            if op in (">=", ">"):
                return val - c["value"]
            if op in ("<=", "<"):
                return c["value"] - val
            if op == "==":
                return val - c["value"]
            raise ValueError(f"등록되지 않은 constraint op {op!r}")
        return _fn

    scipy_constraints = [{"type": "eq" if c["op"] == "==" else "ineq",
                           "fun": _make_constraint_fn(c)} for c in constraints]
    bounds01 = [(0.0, 1.0)] * len(free_thetas)

    x0_norm = _np.array([(x0_dict[n] - lo[i]) / span[i] for i, n in enumerate(names)])

    rng = _random.Random(random_seed)
    starts = [x0_norm]
    for _ in range(max(0, n_starts - 1)):
        x = x0_norm.copy()
        for i in range(len(names)):
            x[i] = min(1.0, max(0.0, x[i] + rng.uniform(-perturb_frac, perturb_frac)))
        starts.append(x)

    import time as _time
    best = None
    attempts = []
    for start_idx, x_start in enumerate(starts):
        iter_count = [0]
        t_start = _time.time()
        if progress:
            print(f"[SLSQP] start {start_idx + 1}/{len(starts)} 시작 -- 자유변수 "
                  f"{len(names)}개: {names}", flush=True)

        def _callback(x_norm, _n=iter_count, _si=start_idx, _t0=t_start):
            _n[0] += 1
            if not progress:
                return
            try:
                _, metrics = _cached_evaluate(x_norm)
                obj = metrics[objective_metric]
                viol = max((0.0 if _CONSTRAINT_OPS[c["op"]](metrics[c["metric"]], c["value"])
                            else abs(metrics[c["metric"]] - c["value"])) for c in constraints)
                print(f"  [SLSQP] start={_si + 1}/{len(starts)} iter={_n[0]} "
                      f"elapsed={_time.time() - _t0:.1f}s {objective_metric}={obj:.4g} "
                      f"max_violation={viol:.4g}", flush=True)
            except InfeasibleSizingError:
                print(f"  [SLSQP] start={_si + 1}/{len(starts)} iter={_n[0]} "
                      f"elapsed={_time.time() - _t0:.1f}s infeasible point", flush=True)

        result = _scipy_minimize(_objective_fn, x_start, method="SLSQP", bounds=bounds01,
                                  constraints=scipy_constraints, callback=_callback,
                                  options={"maxiter": maxiter, "eps": eps, "ftol": 1e-9})
        if progress:
            print(f"[SLSQP] start {start_idx + 1}/{len(starts)} 종료: success={result.success} "
                  f"iters={iter_count[0]} elapsed={_time.time() - t_start:.1f}s "
                  f"message={result.message!r} (누적 캐시={len(_eval_cache)}점)", flush=True)
        theta_values = _snap_l_thetas(_to_theta_values(result.x))
        try:
            ctx, metrics = evaluate(theta_values)
        except InfeasibleSizingError as e:
            attempts.append(f"infeasible: {e}")
            continue
        feasible = all(_CONSTRAINT_OPS[c["op"]](metrics[c["metric"]], c["value"]) for c in constraints)
        if not feasible:
            violations = [f"{c['metric']}{c['op']}{c['value']}(실제={metrics[c['metric']]:.6g})"
                          for c in constraints
                          if not _CONSTRAINT_OPS[c["op"]](metrics[c["metric"]], c["value"])]
            attempts.append(f"제약 위반: {violations}")
            continue
        obj_val = metrics[objective_metric] if minimize_metric else -metrics[objective_metric]
        if best is None or obj_val < best[0]:
            best = (obj_val, theta_values, ctx.sized, metrics)

    if best is None:
        raise ValueError(
            f"SLSQP multi-start {len(starts)}회 전부 실현가능한 해를 못 찾음 -- "
            f"n_starts/maxiter/eps를 조정하거나 search_method='grid'로 대체할 것. "
            f"시도별 사유: {attempts}")
    _, theta_star, sizing, metrics_result = best
    return theta_star, sizing, metrics_result


# ---------------------------------------------------------------------------
# 6.10) L4 — 레이아웃 finger override 후 gm/ID 스펙 재검증(세션13, .ai/context.md 참고)
#       stick_diagram.py의 suggest_pair_finger_adjustments()/mirror_symmetric_trail()이
#       레이아웃(오일러 trail) 조건을 맞추려고 n_fingers를 조정하면 그 소자의 실제
#       W(=n_fingers*finger_w)가 gm/ID 사이징이 원래 계산한 W와 달라진다 -- ID는 topology
#       (KCL/미러비)만으로 W와 독립적으로 이미 확정돼 있으므로(§6.9 A엔진), 이 함수는 "ID는
#       그대로 두고 강제된 새 W에서 실제로 도달하는 gm_id"를 역산한 뒤 그 소자를 참조하는
#       metric/constraint만 다시 확인한다(전체 theta grid search 재실행 불필요).
#
#       ⚠️ 범위(2026-08, 세션13 사용자 확정): `_METRICS_REGISTRY` 기반 지표(gain/mismatch/
#       cmrr/psrr/noise/classab centering 등)만 재검증한다. GBW/PM은 이 함수의 책임이
#       아니다 -- `optimize_multistage()` 자신의 docstring이 이미 "PM 등 회로 레벨 성능은
#       검증하지 않는다, 최종 PM은 SPICE로 확인"이라고 명시하고 있고(위상보상 topology_fn은
#       스펙->gm 정방향 폐형식만 가짐, 역방향(실제 상태->실제 GBW/PM) 계산은 이 코드베이스
#       어디에도 없다), 실제 topology.json 4개 전부(2026-08-05 확인) GBW를 constraints로
#       선언하지도 않는다 -- 지금 만들어도 검증할 대상이 없다. 필요해지면 별도 설계로.
# ---------------------------------------------------------------------------

def _collect_device_refs(spec, known_names: set) -> set:
    """`spec`(metric_spec처럼 임의로 중첩된 dict/list) 안의 문자열 leaf 중 `known_names`에
    속하는 것만 재귀로 모은다 -- metric마다 소자를 가리키는 키 이름이 제각각이라
    (`devices`/`stages`/`device`/`tail_device`/`high_device`/... , _METRICS_REGISTRY 9종
    확인) 특정 키에 의존하지 않고 구조 전체를 훑는다."""
    found = set()

    def walk(x):
        if isinstance(x, str):
            if x in known_names:
                found.add(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)

    walk(spec)
    return found


def revalidate_finger_override(ctx: SizingContext, lut_by_kind: dict, overrides: dict,
                                metrics_specs: dict, constraints: list,
                                gm_id_bounds: tuple = (2.0, 30.0)) -> dict:
    """`overrides`(`{device_name: new_W}`, finger 반올림으로 실제 강제된 W)가 gm/ID
    스펙을 깨지 않는지 재검증한다 -- L3(레이아웃)가 L4(사이징)에 피드백하는 지점.

    **원리**: `ctx.sized[name]["ID"]`는 topology(KCL/미러비)로 이미 확정된 값이라 W가
    바뀌어도 그대로다(§6.9 A엔진 -- ID는 W와 무관하게 먼저 정해진다). 그래서 새 W에서
    이 소자가 실제로 동작하는 gm_id를 `_invert_gm_id_for_current()`(ID/L/vds/vs 고정,
    W만 새 값 -- diode-stack 역산에 쓰던 것과 동일한 이분탐색)로 역산하고,
    `gm=ID*gm_id`/`gds=gm/gm_gds_ratio(...)`로 갱신한 새 컨텍스트를 만든다. 원본 `ctx`는
    건드리지 않는다(순수 함수).

    영향받는 metric만 골라(`_collect_device_refs()`) `compute_metric()`으로 새/구 값을
    비교하고, 그 metric을 참조하는 constraint만 재판정한다 -- `overrides`와 무관한
    metric/constraint는 아예 안 건드린다(전체 grid search 재실행 없이 저비용으로 끝남).

    `gm_id_bounds`는 `_invert_gm_id_for_current()`에 그대로 전달된다(다른 B/C엔진 함수들과
    동일 패턴) -- LUT의 실제 유효 gm/ID 범위가 기본값(2.0~30.0)보다 좁으면 좁혀서 넘길 것
    (예: `build_toy_lut()`는 ~1.85~29.6이라 기본 상단을 살짝 벗어난다).

    반환: `{"ok": bool, "device_updates": {name: {old_W,new_W,old_gm_id,new_gm_id,
    old_gm,new_gm,old_gds,new_gds}}, "metric_deltas": {metric_name: {"old","new"}},
    "violated_constraints": [{**constraint, "actual": new_value}, ...],
    "unaffected_metrics_skipped": [metric_name, ...]}`."""
    device_updates = {}
    new_sized = dict(ctx.sized)
    for name, new_W in overrides.items():
        entry = ctx.sized[name]
        lut = lut_by_kind[entry["kind"]]
        ID, L, vds, vs = entry["ID"], entry["L"], entry.get("vds", 0.0), entry.get("vs", 0.0)
        new_gm_id = _invert_gm_id_for_current(lut, ID, L, vds, vs, new_W, gm_id_bounds=gm_id_bounds)
        new_gm = ID * new_gm_id
        new_gds = new_gm / lut.gm_gds_ratio(new_gm_id, L, vds, vs)
        new_sized[name] = {**entry, "W": new_W, "gm_id": new_gm_id, "gm": new_gm, "gds": new_gds}
        device_updates[name] = {
            "old_W": entry["W"], "new_W": new_W,
            "old_gm_id": entry["gm_id"], "new_gm_id": new_gm_id,
            "old_gm": entry["gm"], "new_gm": new_gm,
            "old_gds": entry.get("gds"), "new_gds": new_gds,
        }
    new_ctx = _dc_replace(ctx, sized=new_sized)

    known_names = set(ctx.sized)
    affected_metrics = {mname for mname, mspec in metrics_specs.items()
                         if _collect_device_refs(mspec, known_names) & set(overrides)}

    metric_deltas = {mname: {"old": compute_metric(metrics_specs[mname], ctx),
                              "new": compute_metric(metrics_specs[mname], new_ctx)}
                      for mname in affected_metrics}

    violated = []
    for c in constraints:
        if c["metric"] not in affected_metrics:
            continue
        new_val = metric_deltas[c["metric"]]["new"]
        if not _CONSTRAINT_OPS[c["op"]](new_val, c["value"]):
            violated.append({**c, "actual": new_val})

    return {
        "ok": not violated,
        "device_updates": device_updates,
        "metric_deltas": metric_deltas,
        "violated_constraints": violated,
        "unaffected_metrics_skipped": sorted(set(metrics_specs) - affected_metrics),
    }


def apply_and_revalidate_pair_adjustment(transistors: list, matching_pairs: list,
                                          ctx: SizingContext, lut_by_kind: dict,
                                          metrics_specs: dict, constraints: list,
                                          gm_id_bounds: tuple = (2.0, 30.0),
                                          max_candidates: int | None = None) -> dict:
    """L3(`suggest_pair_finger_adjustments()`)의 제안을 L4(`revalidate_finger_override()`)로
    자동 승인/거부하는 상위 오케스트레이션 -- 세션12/13이 각각 만든 두 엔진을 처음으로 잇는다
    (`.ai/context.md` 세션13 D절 "다음 확장 지점", 세션12 M3a 그룹 M9b/M18b 사례가 실제 동기).

    `suggest_pair_finger_adjustments()`가 반환한 후보를(홀수차수 개선 오름차순, 즉 레이아웃
    관점에서 가장 좋은 것부터) 순서대로 시도한다 -- 각 후보의 `names`(매칭쌍 또는 미매칭 단독
    소자)에 `delta_fingers`를 적용한 새 W(`(n_fingers+delta)*finger_w`, finger_w는 unit cell
    폭이라 조정 후에도 그대로)를 `revalidate_finger_override()`로 재검증하고, gm/ID
    스펙(`constraints`)을 깨지 않는 **첫 번째** 후보를 채택한다. 레이아웃이 가장 좋아도 스펙을
    깨면 자동으로 건너뛰고 다음 후보를 시도한다 -- 후보 순서는 "레이아웃 우선순위"이지 "무조건
    채택"이 아니다.

    `finger_w`가 없는 소자(단위 폭 미지정)가 낀 후보는 새 W를 계산할 수 없으므로 건너뛴다
    (스킵된 이유는 `rejected`에 남지 않는다 -- gm/ID 위반이 아니라 애초에 시도 불가능했던
    것이라 구분).

    ⚠️ 세션22 발견: 핑거조정이 요구하는 새 W가 물리적으로 실현 불가능한 gm_id를 요구하면
    (예: 극소전류 소자의 W를 크게 늘리라는 후보 -- 실측: M9b/M18b가 91.5nA에 W를
    1.17um->16.15um로 14배 늘리라는 후보를 만나 LUT 특성화 범위(gm_id<=26.8) 밖인
    gm_id=30을 요구, `_invert_gm_id_for_current()`가 `ValueError`) `revalidate_finger_
    override()`가 결과 dict 대신 예외를 던진다 -- 이것도 gm/ID 스펙 위반과 본질적으로
    같은 "이 후보는 못 쓴다"는 신호이므로, A엔진의 `InfeasibleSizingError`와 같은 원칙으로
    `rejected`에 기록하고 다음 후보로 넘어간다(크래시시키지 않는다).

    `max_candidates`(선택): 큰 그룹에서 후보가 많을 때 전부 재검증하면 비용이 커질 수 있어
    상한을 둘 수 있다(기본 `None` = 전부 시도).

    반환: `{"applied": bool, "chosen": PairAdjustmentSuggestion|None,
    "transistors": list[Transistor](채택 시 갱신된 리스트, 실패 시 원본과 동일한 새 리스트),
    "revalidation": dict|None(채택된 후보의 `revalidate_finger_override()` 결과),
    "rejected": [{"suggestion": PairAdjustmentSuggestion, "revalidation": dict}, ...]}`
    (`rejected`는 gm/ID 스펙 위반으로 건너뛴 후보 전부 -- 왜 이 후보가 아니라 채택된 후보가
    선택됐는지 추적 가능하게 남긴다)."""
    candidates = suggest_pair_finger_adjustments(transistors, matching_pairs)
    if max_candidates is not None:
        candidates = candidates[:max_candidates]

    by_name = {t.name: t for t in transistors}
    rejected = []
    for suggestion in candidates:
        if any(by_name[name].finger_w is None for name in suggestion.names):
            continue

        overrides = {name: (by_name[name].n_fingers + suggestion.delta_fingers) * by_name[name].finger_w
                     for name in suggestion.names}
        try:
            result = revalidate_finger_override(ctx, lut_by_kind, overrides, metrics_specs,
                                                 constraints, gm_id_bounds=gm_id_bounds)
        except ValueError as e:
            rejected.append({"suggestion": suggestion, "revalidation": {
                "ok": False, "device_updates": {}, "metric_deltas": {},
                "violated_constraints": [], "unaffected_metrics_skipped": [],
                "error": f"gm_id 역산 실패(물리적으로 실현 불가능한 후보): {e}"}})
            continue
        if result["ok"]:
            new_transistors = [
                _dc_replace(t, n_fingers=t.n_fingers + suggestion.delta_fingers)
                if t.name in suggestion.names else t
                for t in transistors
            ]
            return {"applied": True, "chosen": suggestion, "transistors": new_transistors,
                    "revalidation": result, "rejected": rejected}
        rejected.append({"suggestion": suggestion, "revalidation": result})

    return {"applied": False, "chosen": None, "transistors": list(transistors),
            "revalidation": None, "rejected": rejected}


def _blocked_euler_rows(audit_row_split_result) -> list:
    """`audit_row_split()`/`run_topology_pipeline()`의 `audit_row_split` 반환값(`AuditResult`
    또는 `cell_groups`가 있을 때의 `{cell명: AuditResult}`)에서 euler 실패(체크1) row 이름만
    뽑는다 -- 체크 이름은 `audit_row_split()`이 고정 형식 `f"1. euler[{row_name}]"`으로 남긴다
    (stick_diagram.py:2936/2943)."""
    results = audit_row_split_result.values() if isinstance(audit_row_split_result, dict) \
        else [audit_row_split_result]
    blocked = []
    for ar in results:
        for check in ar.checks:
            if check.name.startswith("1. euler[") and not check.ok:
                blocked.append(check.name[len("1. euler["):-1])
    return blocked


def _sync_finger_fixup(overrides: dict, ctx: SizingContext, fix: dict,
                        prior_transistors: list) -> tuple:
    """`apply_and_revalidate_pair_adjustment()`가 채택한 조정을 layout `sizing_overrides`
    (n_fingers/w)와 gm/ID `ctx.sized`(W/gm_id/gm/gds) 양쪽에 동기화한다 -- 둘 중 하나만
    갱신하면 다음 라운드에서 두 표현이 서로 다른 n_fingers/W를 가리키는 불일치가 생긴다."""
    prior_n = {t.name: t.n_fingers for t in prior_transistors}
    new_overrides = dict(overrides)
    for t in fix["transistors"]:
        if t.n_fingers != prior_n.get(t.name):
            entry = new_overrides[t.name]
            new_overrides[t.name] = {**entry, "n_fingers": t.n_fingers,
                                      "w": t.n_fingers * entry["finger_w"]}

    new_sized = dict(ctx.sized)
    for name, u in fix["revalidation"]["device_updates"].items():
        new_sized[name] = {**new_sized[name], "W": u["new_W"], "gm_id": u["new_gm_id"],
                            "gm": u["new_gm"], "gds": u["new_gds"]}
    return new_overrides, _dc_replace(ctx, sized=new_sized)


# ---------------------------------------------------------------------------
# 6.11) 매칭 목적 핑거증가 (세션16) — repair_matching_safety()가 branch 복합 매칭으로도
#       못 푸는 3c(common-centroid) 실패는 대부분 n_fingers가 너무 작아서(예: n_fingers=1)
#       common_centroid_layout()의 회전-최적 경로가 기하학적으로 dx<=0.5를 달성할 수 없기
#       때문이다(세션16 실측: n_fingers=1이면 최선이 dx=1.0, n_fingers=2부터 residual=0.0
#       완벽 달성). L3(euler용 suggest_pair_finger_adjustments())와 달리 이건 "홀수차수를
#       가장 많이 개선하는 후보를 랭킹"할 필요가 없다 -- 필요한 delta가 정확히 하나로
#       정해져 있다(min_fingers까지 부족한 만큼).
# ---------------------------------------------------------------------------

def suggest_matching_finger_growth(names: tuple, transistors: list, min_fingers: int = 2) -> dict | None:
    """`names`(매칭쌍(a,b) 또는 branch 복합 매칭의 4소자(hub_a,leaf_a,hub_b,leaf_b) 전체 --
    전부 `n_fingers`가 같아야 함, 이미 그렇다는 게 `_branch_composite_pair()`에서 보장됨)를
    `min_fingers`까지 동시에 키우는 delta를 계산한다. `names` 내부 `n_fingers`가 이미
    다르면(호출자 실수) 또는 이미 `min_fingers` 이상이면(다른 이유로 3c가 실패한 것이라
    이 함수 책임 밖) `None`.

    반환: 성공하면 `{"names", "delta_fingers", "note"}`, 아니면 `None`."""
    by_name = {t.name: t for t in transistors}
    n_values = {by_name[n].n_fingers for n in names}
    if len(n_values) != 1:
        return None
    current = n_values.pop()
    delta = min_fingers - current
    if delta <= 0:
        return None
    return {"names": names, "delta_fingers": delta,
            "note": f"common-centroid 회전-최적 경로(residual=0)를 위해 "
                    f"n_fingers {current}->{min_fingers}"}


def apply_and_revalidate_matching_finger_growth(
        names: tuple, transistors: list, ctx: SizingContext, lut_by_kind: dict,
        metrics_specs: dict, constraints: list, gm_id_bounds: tuple = (2.0, 30.0),
        min_fingers: int = 2) -> dict:
    """`suggest_matching_finger_growth()`가 계산한 단 하나의 후보를 `revalidate_finger_
    override()`(L4)로 재검증해 gm/ID 스펙을 깨지 않으면 적용한다 -- `apply_and_revalidate_
    pair_adjustment()`(euler용)와 같은 L3+L4 패턴이지만, 후보가 랭킹된 여러 개가 아니라
    "정확히 필요한 만큼" 하나뿐이라 재시도 루프가 없다.

    반환: `{"applied": bool, "growth": dict|None, "transistors": list[Transistor],
    "revalidation": dict|None}` -- `applied=False`인 이유는 `growth is None`(성장 불필요/
    책임 밖) 또는 `revalidation["ok"]=False`(gm/ID 위반, `revalidation`에 근거 남음) 또는
    `finger_w` 미지정(단위 폭을 몰라 새 W를 계산할 수 없음, `revalidation=None`)으로
    구분된다."""
    growth = suggest_matching_finger_growth(names, transistors, min_fingers=min_fingers)
    if growth is None:
        return {"applied": False, "growth": None, "transistors": list(transistors),
                "revalidation": None}
    by_name = {t.name: t for t in transistors}
    if any(by_name[n].finger_w is None for n in names):
        return {"applied": False, "growth": growth, "transistors": list(transistors),
                "revalidation": None}
    delta = growth["delta_fingers"]
    overrides = {n: (by_name[n].n_fingers + delta) * by_name[n].finger_w for n in names}
    try:
        result = revalidate_finger_override(ctx, lut_by_kind, overrides, metrics_specs, constraints,
                                             gm_id_bounds=gm_id_bounds)
    except ValueError as e:
        # 세션22 -- apply_and_revalidate_pair_adjustment()와 동일한 원칙(위 docstring
        # 참고): 물리적으로 실현 불가능한 gm_id를 요구하는 후보는 gm/ID 스펙 위반과
        # 똑같이 "이 후보는 못 쓴다"로 처리한다(크래시시키지 않는다).
        return {"applied": False, "growth": growth, "transistors": list(transistors),
                "revalidation": {"ok": False, "device_updates": {}, "metric_deltas": {},
                                  "violated_constraints": [], "unaffected_metrics_skipped": [],
                                  "error": f"gm_id 역산 실패(물리적으로 실현 불가능한 후보): {e}"}}
    if not result["ok"]:
        return {"applied": False, "growth": growth, "transistors": list(transistors),
                "revalidation": result}
    new_transistors = [_dc_replace(t, n_fingers=t.n_fingers + delta) if t.name in names else t
                        for t in transistors]
    return {"applied": True, "growth": growth, "transistors": new_transistors,
            "revalidation": result}


def _fixup_euler_blocked_rows(rows: dict, matching_pairs: list, pair_sensitivity: dict,
                               ctx: SizingContext, lut_by_kind: dict, metrics_specs: dict,
                               constraints: list, gm_id_bounds: tuple = (2.0, 30.0),
                               max_rounds: int = 5) -> tuple:
    """`repair_matching_safety()`(3c 수리 -- 일부 소자를 `common_centroid_layout()`으로
    새 행에 빼냄)가 원래 행에 **남은 나머지 소자들**의 euler 조건(짝수차수 -- 한붓그리기
    가능 여부)까지 보존한다는 보장은 없다 -- 2026-08-13(세션31 이어) 실측 발견: `two_stage_
    ota` box-shape 진단 중 `save_instance_json()`이 repair *이전* 스냅샷을 저장하던 버그를
    고치자(그 자체는 별개 수정), self-test(11소자 M3a 그룹, M4a/M4b+M10/M19를 3c 수리로
    빼낸 뒤) 남은 행 `m3a_row`가 `status=blocked, odd_nodes=['Vbias3','gnd']`로 방치되는
    게 처음으로 드러났다(지금까지는 이 저장 버그가 이 사실을 가려왔을 뿐, `repair_matching_
    safety()`가 새로 만든 버그가 아니다). `run_topology_pipeline_with_finger_fixup()`이
    euler-fixup에 쓰는 것과 **정확히 같은 전략**(1순위: `apply_and_revalidate_pair_
    adjustment()`로 매칭쌍 핑거증가, 안 되면 2순위: `find_min_crossover_layout_with_
    branch_composite()`로 그래프 이론상 항상 성공하는 그룹분할)을 그 함수와 달리
    `topology_path` 재로드 없이 `rows` 표현에 직접 적용한다 -- 두 저수준 함수
    (`apply_and_revalidate_pair_adjustment()`/`find_min_crossover_layout_with_branch_
    composite()`) 다 애초에 `row_transistors`를 직접 받는 API라 재사용 가능하다.

    이미 euler-clean이면(대다수 회로/대다수 라운드) 즉시 그대로 반환 -- 비용 없음.

    ⚠️ 2026-08-13(세션31 이어) 실측으로 드러난 두 번째 층위 -- M4a/M4b를 새 행으로 빼내면
    남은 행(M3a/M3b/M9b/M18b/M5/M64/M63)이 단순 홀짝 불균형이 아니라 **그래프 자체가
    분리된 두 조각**(M3a/M3b/M9b/M18b 클러스터 vs M5/M63/M64 클러스터, M3a가 M4a와
    공유하던 내부노드 `N3a4a`가 이제 이 행 안에서 아무와도 안 이어짐)으로 쪼개질 수 있다
    -- `check_euler_condition()`은 이 경우도 홀수차수 노드가 우연히 정확히 2개일 수 있어
    (컴포넌트마다 1개씩) `status=blocked`인데도 겉보기엔 "거의 다 됐다"로 보인다.
    **핑거증가(parity 조정)는 끊어진 컴포넌트를 다시 잇지 못한다** -- 그래서 disconnection
    이 감지되면 핑거증가/크로스오버 둘 다 시도하지 않고 **각 컴포넌트를 곧바로 별도
    물리 행으로 분리한다**(항상 안전 -- 컴포넌트 사이엔 애초에 공유 엣지가 없으므로
    crossover 배선 자체가 무의미, 그냥 두 개의 독립된 행이 되는 게 맞는 답).

    반환: `(rows, ctx)` -- 갱신된 물리 행 구성과(그룹분할/컴포넌트분리는 순수 재배치라
    ctx 불변, 핑거증가만 W/gm_id/gm/gds가 바뀌므로 ctx도 갱신) SizingContext."""
    def _connected_components(transistors: list) -> list:
        net_to_devs = defaultdict(list)
        for t in transistors:
            net_to_devs[t.source].append(t)
            net_to_devs[t.drain].append(t)
        visited, components = set(), []
        for t in transistors:
            if t.name in visited:
                continue
            comp, stack, seen_names = [], [t], {t.name}
            while stack:
                cur = stack.pop()
                comp.append(cur)
                for net in (cur.source, cur.drain):
                    for other in net_to_devs[net]:
                        if other.name not in seen_names:
                            seen_names.add(other.name)
                            stack.append(other)
            visited |= seen_names
            components.append(comp)
        return components

    current_rows = {k: list(v) for k, v in rows.items()}
    cur_ctx = ctx
    for _ in range(max_rounds):
        blocked_row = None
        for row_name, devs in current_rows.items():
            r = build_stick_diagram(devs).get(row_name)
            if r is None or r.status != "ok":
                blocked_row = row_name
                break
        if blocked_row is None:
            return current_rows, cur_ctx

        row_transistors = current_rows[blocked_row]
        components = _connected_components(row_transistors)
        if len(components) > 1:
            del current_rows[blocked_row]
            for comp_idx, comp in enumerate(components):
                comp_stack_id = f"{blocked_row}_comp{comp_idx}"
                current_rows[comp_stack_id] = [_dc_replace(t, stack_id=comp_stack_id)
                                                 for t in comp]
            continue

        row_names = {t.name for t in row_transistors}
        row_pairs = [(a, b) for (a, b) in matching_pairs if a in row_names and b in row_names]

        fix = apply_and_revalidate_pair_adjustment(
            row_transistors, row_pairs, cur_ctx, lut_by_kind, metrics_specs, constraints,
            gm_id_bounds=gm_id_bounds)
        resolved_by_growth = False
        if fix["applied"]:
            new_n = {t.name: t.n_fingers for t in fix["transistors"]}
            candidate_devs = [
                _dc_replace(t, n_fingers=new_n[t.name]) if t.name in new_n else t
                for t in row_transistors]
            # 2026-08-13 -- "applied"는 gm/ID가 유효한 후보를 찾았다는 뜻일 뿐, 그 후보가
            # 이 행의 euler를 실제로 완전히 푼다는 보장은 아니다(실측: 홀수차수가 줄어도
            # 0/2개로 안 떨어지고 계속 blocked로 남는 경우가 있었다) -- 적용 *후* 실제로
            # 풀렸는지 다시 확인하고, 안 풀렸으면 무한정 재시도하지 않고 바로 그룹분할로
            # 넘어간다(아래) -- 그래프 이론상 항상 성공하는 쪽이 훨씬 안전하다.
            r2 = build_stick_diagram(candidate_devs).get(blocked_row)
            if r2 is not None and r2.status == "ok":
                resolved_by_growth = True
                current_rows[blocked_row] = candidate_devs
                for name, u in fix["revalidation"]["device_updates"].items():
                    cur_ctx = _dc_replace(cur_ctx, sized={
                        **cur_ctx.sized, name: {**cur_ctx.sized[name], "W": u["new_W"],
                                                 "gm_id": u["new_gm_id"], "gm": u["new_gm"],
                                                 "gds": u["new_gds"]}})
        if resolved_by_growth:
            continue

        # 핑거증가로 안 풀리면(또는 애초에 후보가 없으면) 그룹분할(그래프 이론상 항상
        # 성공, run_topology_pipeline_with_finger_fixup()과 동일 근거) -- 세그먼트는
        # 소자를 통째로 한쪽에만 배정한다(finger 단위 분할 아님, find_min_crossover_
        # layout_with_branch_composite() 자체의 보장 -- W/n_fingers는 안 바뀌므로 ctx
        # 갱신 불필요). 원본 row_transistors(성장 시도 전 상태) 기준으로 분할한다 --
        # 실패한 성장 후보를 반영하지 않는다.
        row_pair_sensitivity = {k: v for k, v in pair_sensitivity.items() if set(k) <= row_names}
        split = find_min_crossover_layout_with_branch_composite(
            row_transistors, row_pairs, row_pair_sensitivity)
        by_name = {t.name: t for t in row_transistors}
        del current_rows[blocked_row]
        for seg_idx, seg in enumerate(split["segments"]):
            seg_stack_id = f"{blocked_row}_seg{seg_idx}"
            seg_device_names, seen = [], set()
            for nm in seg["transistor_sequence"]:
                if nm not in seen:
                    seen.add(nm)
                    seg_device_names.append(nm)
            current_rows[seg_stack_id] = [_dc_replace(by_name[nm], stack_id=seg_stack_id)
                                            for nm in seg_device_names]
    return current_rows, cur_ctx


def run_matching_safety_with_finger_growth(
        rows: dict, matching_pairs: list, pair_sensitivity: dict, ctx: SizingContext,
        lut_by_kind: dict, metrics_specs: dict, constraints: list,
        gm_id_bounds: tuple = (2.0, 30.0), min_fingers: int = 2, max_rounds: int = 5,
        allow_layout_relaxation: bool = True) -> dict:
    """`repair_matching_safety()`(stick_diagram.py, L1~L3, branch 복합 매칭 포함)가
    3c(common-centroid)를 못 푸는 지점에 "매칭 목적 핑거증가"(위) 자동 수정 루프를 감싸
    붙인다 -- `run_topology_pipeline_with_finger_fixup()`(euler용)과 대칭되는 구조,
    `stick_diagram.py`<->`sizing_recipe.py` 단방향 import 제약 때문에 여기 위치(동일 이유).

    각 라운드: (1) `repair_matching_safety()` 실행 (2) `ok`면 성공 종료 (3) 필수 게이트로
    실패한 pair 중 **3c만**(`_failing_required_pairs()`가 3b/3c를 섞어 주므로 이름으로
    거른다 -- 3b는 배치 문제라 핑거증가로 못 고침) 첫 항목을 골라, branch 복합 매칭
    대상인지(`_branch_composite_pair()`) 확인해 growth target(단순쌍 2소자 또는 branch
    전체 4소자)을 정한다 (4) `apply_and_revalidate_matching_finger_growth()` 시도 (5)
    성공하면 `rows`/`ctx`를 갱신하고 다음 라운드 (6) 실패하면(gm/ID 위반, 이미 충분한
    n_fingers, finger_w 미지정 등) **거짓 성공으로 처리하지 않고 즉시 멈춘다** --
    `unresolved_reason`에 근거를 남긴다. **단, `reason=="gm_id_violation"`이고
    `allow_layout_relaxation`(기본 True)이면 세션17 설계안 3번("그래도 안 되면 인접배치로
    완화")을 적용한다** -- 이유가 딱 gm/ID 예산 위반일 때만(finger_w 미지정/growth 부적용 같은
    다른 사유는 완화 대상 아님, 설정 문제를 조용히 덮지 않기 위해). 그 pair를 `relaxed_pairs`
    (`repair_matching_safety()`의 새 파라미터, layout 전용 최후수단 -- interdigitate_layout
    강제)에 등록하고 다음 라운드로 넘어간다.

    ⚠️⚠️ **완화는 3c 요구사항을 없애지 않는다** -- `pair_sensitivity`/`select_layout_tool()`이
    정한 필수 게이트는 그대로 3c이므로, 완화가 적용된 뒤에도 `audit.ok`는 여전히 그 pair의
    3c FAIL을 정직하게 반영한다(offset/branch_symmetric은 CMRR/PSRR 민감도 때문에
    common-centroid가 진짜 필요하다는 `audit_row_split()` §2.7 설계 원칙을 이 함수가 몰래
    뒤집지 않는다). 완화는 "gm/ID 스펙(trim 불가능한 회로 기능 저하)을 지키는 대신, layout
    mismatch(trim으로 보정 가능한 열화)를 감수한다"는 명시적 트레이드오프일 뿐이다 --
    `relaxed_pairs`(반환값, 아래) 필드로 그 사실을 남기고, 최종 승인 여부는 호출자가
    `result["audit"].ok`와 `result["relaxed_pairs"]`를 직접 보고 판단해야 한다(세션16
    E-3절과 동일 원칙 -- `unresolved_pair=None`이 `audit.ok=True`의 동의어가 아니듯,
    `relaxed_pairs`가 채워졌다고 "문제 없음"이 아니다).

    ⚠️ `unresolved_pair=None`은 "**3c 실패 중 핑거증가로 처리할 게 더 없다**"는 뜻이지
    "`audit.ok=True`"의 동의어가 아니다 -- `audit_row_split()`의 다른 체크(예: "2.
    box-shape" 행폭 비율, 이 함수가 다루지 않는 완전히 다른 관심사)가 별개로 실패하면
    `unresolved_pair=None`이어도 `audit.ok=False`일 수 있다(세션16 실측: M1a/M1b/M2a/M2b
    성장으로 3c는 완전히 풀렸지만, M6/M7만 남은 행과의 폭 비율이 §8 허용치를 넘어 box-shape가
    별도로 FAIL). 호출자는 전체 성공 여부를 반드시 `result["audit"].ok`로 직접 확인할 것 --
    `unresolved_pair`/`unresolved_reason`은 "3c 관점에서 이 함수가 할 일을 다 했는지"만
    알려주는 진단 정보다.

    반환: `{"rows", "audit", "ctx", "growth_rounds": [{"round","names","result"}, ...],
    "unresolved_pair": (a,b)|None, "unresolved_reason": str|None,
    "relaxed_pairs": [{"pair":(a,b), "reason":"gm_id_budget_exceeded",
    "trim_recommended":True, "interdig_ok":bool|None}, ...]}`. `unresolved_reason`에
    `"relaxed_to_layout"`이 새로 추가됐다 -- growth가 gm/ID 예산으로 막혀서 완화를 적용했고,
    (완화 대상 아닌 다른 3c 실패가 없어) 이 함수가 더 할 일이 없다는 뜻이다."""
    current_rows = {k: list(v) for k, v in rows.items()}
    cur_ctx = ctx
    growth_rounds = []
    relaxed_pairs: list = []  # 세션17: [{"pair","reason","trim_recommended","interdig_ok"}, ...]
    relaxed_pair_keys: set = set()  # frozenset({a,b}) -- repair_matching_safety()에 그대로 전달

    def _backfill_interdig_ok(audit_result):
        # 완화를 적용한 라운드에는 아직 그 결과가 반영된 audit이 없어 interdig_ok=None으로
        # 남겨뒀다 -- 다음 라운드에 새로 계산된 audit_result가 나오면 그 3b 체크로 채운다.
        for entry in relaxed_pairs:
            if entry["interdig_ok"] is not None:
                continue
            ea, eb = entry["pair"]
            for check in audit_result.checks:
                if check.name.startswith("3b.") and f"[{ea}/{eb}]" in check.name:
                    entry["interdig_ok"] = check.ok
                    break

    # 2026-08-13(세션31 이어, 사용자 지시 -- box-shape 진단 도중 발견된 euler 잔여문제
    # 근본수정) -- repair_matching_safety()가 3c 수리로 일부 소자를 새 행에 빼내면서 원래
    # 행에 남은 나머지가 euler-blocked로 방치될 수 있다(_fixup_euler_blocked_rows()
    # docstring 참고, 실측: two_stage_ota box-shape 작업 중 11소자 M3a self-test에서 발견).
    # 이 함수의 **모든** 반환 지점에서 최종 rows/ctx를 내보내기 전에 반드시 이 euler
    # 정리를 거치고 그 결과로 audit을 다시 계산한다 -- 그래야 반환되는 audit이 실제로
    # 저장/보고될 최종 물리 구조와 항상 일치한다(저장 버그와 같은 종류의 불일치 재발 방지).
    def _finalize(rows_in, ctx_in):
        fixed_rows, fixed_ctx = _fixup_euler_blocked_rows(
            rows_in, matching_pairs, pair_sensitivity, ctx_in, lut_by_kind,
            metrics_specs, constraints, gm_id_bounds=gm_id_bounds)
        fixed_audit = audit_row_split(fixed_rows, matching_pairs=matching_pairs,
                                       pair_sensitivity=pair_sensitivity)
        _backfill_interdig_ok(fixed_audit)
        return fixed_rows, fixed_ctx, fixed_audit

    result = None
    for round_idx in range(max_rounds):
        current_rows, result = repair_matching_safety(
            current_rows, matching_pairs, pair_sensitivity, relaxed_pairs=relaxed_pair_keys)
        _backfill_interdig_ok(result)
        if result.ok:
            current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)
            return {"rows": current_rows, "audit": result, "ctx": cur_ctx,
                    "growth_rounds": growth_rounds, "unresolved_pair": None,
                    "unresolved_reason": None, "relaxed_pairs": relaxed_pairs}

        # `_failing_required_pairs()`는 3b/3c를 섞어서 준다 -- 그 pair의 필수 게이트가
        # 3b(배치 문제, 핑거증가로 못 고침)일 수도 있으므로 재사용하지 않고, "3c가 필수
        # 게이트로 실패"한 pair만 직접 골라낸다(같은 정규식 파싱 규칙, stick_diagram.py의
        # _failing_required_pairs()와 동일 패턴).
        import re
        failing_3c = []
        for check in result.checks:
            if check.ok or "[참고용" in check.name or not check.name.startswith("3c."):
                continue
            m = re.search(r"\[(.+?)/(.+?)\]", check.name)
            if m and (m.group(1), m.group(2)) not in failing_3c:
                failing_3c.append((m.group(1), m.group(2)))
        # 세션17: 이미 완화 적용된 쌍은 growth 재시도 대상에서 제외한다 -- 3c는 게이트가
        # 그대로라 계속 failing_3c에 잡히지만, 이 함수가 그 쌍에 대해 더 할 일은 없다.
        failing_3c = [(x, y) for (x, y) in failing_3c
                      if frozenset({x, y}) not in relaxed_pair_keys]
        if not failing_3c:
            # euler 실패는 "3c." 접두사가 아니라서 failing_3c에 절대 안 잡힌다(위 필터
            # 참고) -- 그래서 이 분기에 도달했다고 euler까지 깨끗하다는 보장이 없다(실측
            # 발견 사례 그대로). _finalize()가 그 가능성을 항상 마지막에 확인/수정한다.
            reason = "relaxed_to_layout" if relaxed_pairs else "only_3b_failures_left"
            current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)
            return {"rows": current_rows, "audit": result, "ctx": cur_ctx,
                    "growth_rounds": growth_rounds, "unresolved_pair": None,
                    "unresolved_reason": reason, "relaxed_pairs": relaxed_pairs}

        a, b = failing_3c[0]
        all_devs = {t.name: t for devs in current_rows.values() for t in devs}
        if a not in all_devs or b not in all_devs:
            current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)
            return {"rows": current_rows, "audit": result, "ctx": cur_ctx,
                    "growth_rounds": growth_rounds, "unresolved_pair": (a, b),
                    "unresolved_reason": "pair_not_found", "relaxed_pairs": relaxed_pairs}
        composite = _branch_composite_pair(a, b, all_devs, matching_pairs)
        names = tuple(sorted(set(composite["expand"][composite["composite_a"].name] +
                                  composite["expand"][composite["composite_b"].name]))) \
            if composite is not None else (a, b)

        row_transistors = [t for devs in current_rows.values() for t in devs if t.name in names]
        fix = apply_and_revalidate_matching_finger_growth(
            names, row_transistors, cur_ctx, lut_by_kind, metrics_specs, constraints,
            gm_id_bounds=gm_id_bounds, min_fingers=min_fingers)
        growth_rounds.append({"round": round_idx, "names": names, "result": fix})
        if not fix["applied"]:
            reason = "no_finger_w" if fix["revalidation"] is None and fix["growth"] is not None \
                else "gm_id_violation" if fix["revalidation"] is not None \
                else "growth_not_applicable"
            if reason == "gm_id_violation" and allow_layout_relaxation:
                # 세션17 설계안 3번 -- gm/ID 예산 위반으로만 막혔으면(다른 사유는 완화 대상
                # 아님) 인접배치(3b)로 최후수단 완화하고 다음 라운드로 넘어간다. audit.ok는
                # 손대지 않는다(위 docstring "완화는 3c 요구사항을 없애지 않는다" 참고).
                relaxed_pair_keys.add(frozenset({a, b}))
                relaxed_pairs.append({"pair": (a, b), "reason": "gm_id_budget_exceeded",
                                       "trim_recommended": True, "interdig_ok": None})
                continue
            current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)
            return {"rows": current_rows, "audit": result, "ctx": cur_ctx,
                    "growth_rounds": growth_rounds, "unresolved_pair": (a, b),
                    "unresolved_reason": reason, "relaxed_pairs": relaxed_pairs}

        new_n = {t.name: t.n_fingers for t in fix["transistors"] if t.name in names}
        for rn, devs in current_rows.items():
            current_rows[rn] = [_dc_replace(t, n_fingers=new_n[t.name]) if t.name in new_n else t
                                 for t in devs]
        for name, u in fix["revalidation"]["device_updates"].items():
            cur_ctx = _dc_replace(cur_ctx, sized={
                **cur_ctx.sized, name: {**cur_ctx.sized[name], "W": u["new_W"],
                                         "gm_id": u["new_gm_id"], "gm": u["new_gm"],
                                         "gds": u["new_gds"]}})

    current_rows, result = repair_matching_safety(
        current_rows, matching_pairs, pair_sensitivity, relaxed_pairs=relaxed_pair_keys)
    _backfill_interdig_ok(result)
    current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)
    return {"rows": current_rows, "audit": result, "ctx": cur_ctx, "growth_rounds": growth_rounds,
            "unresolved_pair": None if result.ok else "unknown",
            "unresolved_reason": None if result.ok else "max_rounds_exceeded",
            "relaxed_pairs": relaxed_pairs}


def run_topology_pipeline_with_finger_fixup(
        topology_json_path: str, sizing_overrides: dict, ctx: SizingContext, lut_by_kind: dict,
        metrics_specs: dict, constraints: list, floorplan_hints: dict | None = None,
        cell_groups: dict | None = None, gm_id_bounds: tuple = (2.0, 30.0),
        max_fixup_rounds: int = 5) -> dict:
    """`run_topology_pipeline()`(stick_diagram.py, L1~L3)이 euler-blocked row를 그냥 실패로만
    보고하는 지점에 L3(`suggest_pair_finger_adjustments()`)+L4(`apply_and_revalidate_pair_
    adjustment()`) 자동 수정 루프를 감싸 붙인다 -- `.ai/context.md` 세션13 D절이 남긴 "다음
    확장 지점", 세션14에서 실배선.

    **왜 `stick_diagram.py` 안에 넣지 않았는가**: `stick_diagram.py`는 gm/ID를 전혀 모르는
    순수 그래프/기하 모듈이고, `sizing_recipe.py`가 `stick_diagram.py`를 단방향으로만 import한다
    (반대 방향 없음, `sizing_recipe.py` 앞부분의 `from stick_diagram import (...)` 참고).
    fixup 로직은 gm/ID 재검증에 `SizingContext`/LUT가 필요해서, `stick_diagram.py` 안에 넣으면
    순환 import가 생긴다 -- 그래서 `run_topology_pipeline()`을 호출자 쪽(`sizing_recipe.py`)에서
    감싸는 방식을 택했다.

    **라운드당 blocked row 1개씩만 처리한다**(세션14 논의 결론) -- row는 `stack_id`로 물리적
    으로 이미 분리돼 있어 서로 독립이지만, gm/ID `constraints`(예: 전체 gain)는 여러 row의
    소자를 동시에 참조할 수 있어 한 라운드에 여러 row를 동시에 조정하면 서로의 재검증 결과에
    영향을 줄 수 있다 -- 매 라운드 `run_topology_pipeline()`을 처음부터 재실행해 항상 최신
    상태 기준으로 다음 조정을 판단한다(회로 규모상 비용 문제 없음, 안전 우선).

    각 라운드: (1) `run_topology_pipeline()` 실행. (2) `audit_row_split`에서 euler-blocked
    row 탐지 -- 없으면 성공 종료(`unresolved_row=None`). (3) 첫 blocked row의 소자 +
    topology.json `symmetry.matching_pairs`(그 row로 필터링)로 `apply_and_revalidate_pair_
    adjustment()` 시도. (4) 성공하면 `sizing_overrides`와 `ctx.sized`를 `_sync_finger_fixup()`
    으로 동기화하고 다음 라운드로. (5) **세션18 -- 실패하면(그 row의 모든 후보가 gm/ID 위반)
    바로 포기하지 않고 그룹분할(crossover routing)로 폴백한다**(세션15 C절 설계,
    `.ai/context.md` 참고): `find_min_crossover_layout_with_branch_composite()`
    (branch 구조적 보장 -- G-3절, `find_min_crossover_layout()` 대신 반드시 이 wrapper를
    쓴다)로 그 row를 분할하고, 반환된 `segments`대로 그 row 소자들의 `stack_id`를
    `f"{row_name}_seg{i}"`로 재배정한다(순수 물리 배치 변경 -- W/n_fingers는 안 바뀌므로
    `_sync_finger_fixup()`류의 gm/ID 재검증이 필요 없다). 이 함수는 그래프 이론상(T-join/
    route inspection) 항상 성공하므로, 이 지점에 도달하면 사실상 항상 풀린다 -- 그래서
    "완전히 공짜로 풀렸다"는 거짓 인상을 주지 않도록 `group_splits`(아래)에 크로스오버가
    실제로 몇 번 들어갔는지 정직하게 남긴다. `audit.ok`는 손대지 않는다 -- 다음 라운드에
    새로 계산된 값을 그대로 반영한다(진짜로 euler+3b+3c가 다 통과하면 자연히 True, 그 행에
    다른 실패(예: `n_fingers=1` 매칭쌍의 3c)가 남아 있으면 여전히 False). `max_fixup_rounds`
    소진 시엔 마지막 조정 이후 한 번 더 `run_topology_pipeline()`을 재실행해 실제로 풀렸는지
    확인한 뒤 반환한다(`unresolved_reason="max_rounds_exceeded"`인 경우만 -- 라운드 소진과
    동시에 실제로 풀렸으면 정상 성공으로 반환). 그룹분할이 그래프 이론상 항상 성공하므로
    `unresolved_reason="no_valid_candidate"`는 더 이상 이 함수의 실제 반환 경로가 아니다
    (과거 `no_valid_candidate` 시나리오는 이제 그룹분할로 넘어간다).

    **`cell_groups` 자동확장(세션18, C-3)**: `cell_groups`가 주어졌는데 그룹분할로 새
    `_seg*` row가 생기면, 원래 row 이름이 속했던 `cell_groups` 항목에서 그 이름을 빼고
    새 `_seg*` 이름들을 대신 넣는다(호출자가 준 원본 dict는 손 안 대고 내부 사본만
    갱신) -- 안 하면 `run_topology_pipeline()`이 새 row를 감사에서 조용히 누락한다
    (세션15 C-3이 지적한 갭, 세션18에 `optimize_full_circuit_budget()`이 실제로
    `cell_groups=spec.get("cell_groups")`를 넘긴다는 게 확인돼 실전 갭임이 확정됐다).

    반환: `run_topology_pipeline()`의 반환값(`transistors`/`box_shape`/`audit_row_split`/
    `floorplan`/`coverage`) + `{"fixup_rounds": [{"round","row","result"}, ...],
    "group_splits": [{"round","row","n_segments","crossover_count","branch_composites",
    "node_pairing_fallback_used"}, ...], "sizing_overrides": (최종), "ctx": (최종),
    "unresolved_row": str|None, "unresolved_reason": "max_rounds_exceeded"|None}`.
    `group_splits`가 비어있으면 이번 실행에서 그룹분할이 전혀 필요 없었다는 뜻(완전
    하위호환 신호 -- 기존 호출부는 이 필드를 몰라도 다른 동작이 전혀 안 바뀐다)."""
    overrides = dict(sizing_overrides)
    cur_ctx = ctx
    fixup_rounds = []
    group_splits: list = []
    effective_cell_groups = {k: list(v) for k, v in cell_groups.items()} \
        if cell_groups is not None else None

    _, meta = load_topology(topology_json_path)
    pairs_meta = meta["symmetry"]["matching_pairs"]
    all_matching_pairs = [pair for p in pairs_meta for pair in itertools.combinations(p["names"], 2)]
    all_pair_sensitivity = {pair: p["matching_sensitivity"] for p in pairs_meta
                             for pair in itertools.combinations(p["names"], 2)}

    result = None
    for round_idx in range(max_fixup_rounds):
        result = run_topology_pipeline(topology_json_path, overrides,
                                        floorplan_hints=floorplan_hints,
                                        cell_groups=effective_cell_groups)
        blocked = _blocked_euler_rows(result["audit_row_split"])
        if not blocked:
            return {**result, "fixup_rounds": fixup_rounds, "group_splits": group_splits,
                    "sizing_overrides": overrides, "ctx": cur_ctx, "unresolved_row": None,
                    "unresolved_reason": None}

        row_name = blocked[0]
        row_transistors = [t for t in result["transistors"] if t.stack_id == row_name]
        row_names = {t.name for t in row_transistors}
        row_pairs = [(a, b) for (a, b) in all_matching_pairs if a in row_names and b in row_names]

        fix = apply_and_revalidate_pair_adjustment(
            row_transistors, row_pairs, cur_ctx, lut_by_kind, metrics_specs, constraints,
            gm_id_bounds=gm_id_bounds)
        fixup_rounds.append({"round": round_idx, "row": row_name, "result": fix})

        if fix["applied"]:
            overrides, cur_ctx = _sync_finger_fixup(overrides, cur_ctx, fix, row_transistors)
            continue

        # 세션18: 핑거조정으로 못 풀리면 그룹분할로 폴백(위 docstring (5) 참고).
        row_pair_sensitivity = {k: v for k, v in all_pair_sensitivity.items()
                                 if set(k) <= row_names}
        split = find_min_crossover_layout_with_branch_composite(
            row_transistors, row_pairs, row_pair_sensitivity)
        new_seg_names = []
        for seg_idx, seg in enumerate(split["segments"]):
            seg_stack_id = f"{row_name}_seg{seg_idx}"
            new_seg_names.append(seg_stack_id)
            for name in seg["transistor_sequence"]:
                overrides[name] = {**overrides[name], "stack_id": seg_stack_id}

        if effective_cell_groups is not None:
            for cell_name, row_list in effective_cell_groups.items():
                if row_name in row_list:
                    effective_cell_groups[cell_name] = \
                        [rn for rn in row_list if rn != row_name] + new_seg_names

        group_splits.append({
            "round": round_idx, "row": row_name, "n_segments": len(split["segments"]),
            "crossover_count": split["crossover_count"],
            "branch_composites": split["branch_composites"],
            "node_pairing_fallback_used": split["node_pairing_fallback_used"],
        })

    result = run_topology_pipeline(topology_json_path, overrides,
                                    floorplan_hints=floorplan_hints, cell_groups=effective_cell_groups)
    blocked = _blocked_euler_rows(result["audit_row_split"])
    return {**result, "fixup_rounds": fixup_rounds, "group_splits": group_splits,
            "sizing_overrides": overrides, "ctx": cur_ctx,
            "unresolved_row": blocked[0] if blocked else None,
            "unresolved_reason": "max_rounds_exceeded" if blocked else None}


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
    print("# _COMPENSATION_REGISTRY allowlist 거부 -- 실제 harness 경로(_evaluate()) 자체를")
    print("# 통해 확인(2026-08-12 세션30 -- run_sizing_pipeline()은 죽은 코드라 삭제됐고,")
    print("# 그 함수에만 있던 이 가드를 _evaluate()에 새로 추가했다, harness 연동 감사 중 발견)")
    import os as _os
    import tempfile as _tempfile

    with _tempfile.TemporaryDirectory() as _tmpdir:
        _bad_path = _os.path.join(_tmpdir, "bad.topology.json")
        with open(_bad_path, "w", encoding="utf-8") as _f:
            json.dump({
                "topology_name": "bad_fixture", "schema_version": "2.0",
                "netlist": [],
                "symmetry": {"matching_pairs": []},
                "compensation": {"function": "not_a_real_function", "parameters": [],
                                  "stage_devices": [["M1"]]},
                "sizing_roles": {"theta": [], "metrics": {}, "objective": {}, "constraints": []},
            }, _f)
        try:
            optimize_full_circuit_budget(_bad_path, {"stage_w_max": 1e-4})
            raise AssertionError("허용되지 않은 compensation 함수명이 거부되지 않았다")
        except ValueError as _e:
            assert "_COMPENSATION_REGISTRY" in str(_e)
            print(f"    ValueError로 정상 거부됨(실제 harness 경로): {_e}")

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
    print("  [L4 revalidate_finger_override() -- finger 반올림으로 W가 강제로 바뀌어도 ID는")
    print("  그대로라는 원칙(A엔진)을 재확인하고, 영향받는 metric/constraint만 재검증하는지]")
    _l4_L, _l4_vds, _l4_gm_id = 0.5e-6, 0.6, 12.0
    _l4_r1 = size_transistor(gm=200e-6, gm_id=_l4_gm_id, L=_l4_L, lut=lut, vds=_l4_vds)
    _l4_gds1 = _l4_r1.gm / lut.gm_gds_ratio(_l4_gm_id, _l4_L, _l4_vds, 0.0)
    _l4_r3 = size_transistor(gm=80e-6, gm_id=10.0, L=_l4_L, lut=lut, vds=_l4_vds)
    _l4_gain_baseline = 20 * math.log10((_l4_r1.gm + _l4_r1.gm) / (_l4_gds1 + _l4_gds1))
    _l4_ctx = SizingContext(sized={
        "M1": {"ID": _l4_r1.ID, "W": _l4_r1.W, "L": _l4_L, "gm": _l4_r1.gm, "gm_id": _l4_gm_id,
               "gds": _l4_gds1, "kind": "nmos", "vds": _l4_vds, "vs": 0.0},
        "M2": {"ID": _l4_r1.ID, "W": _l4_r1.W, "L": _l4_L, "gm": _l4_r1.gm, "gm_id": _l4_gm_id,
               "gds": _l4_gds1, "kind": "nmos", "vds": _l4_vds, "vs": 0.0},
        "M3": {"ID": _l4_r3.ID, "W": _l4_r3.W, "L": _l4_L, "gm": _l4_r3.gm, "gm_id": 10.0,
               "gds": 0.0, "kind": "nmos", "vds": _l4_vds, "vs": 0.0},
    })
    _l4_metrics_specs = {
        "stage_gain": {"type": "gain_stages_sum", "stages": [["M1", "M2"]]},
        "other_current": {"type": "sum_current", "devices": ["M3"]},
    }
    _l4_threshold = _l4_gain_baseline - 0.5
    _l4_constraints = [
        {"metric": "stage_gain", "op": ">=", "value": _l4_threshold},
        {"metric": "other_current", "op": "<=", "value": 100e-6},
    ]
    print(f"    baseline stage_gain={_l4_gain_baseline:.4f}dB, constraint>={_l4_threshold:.4f}dB "
          f"(M1/M2 diff pair, M3는 무관한 소자)")

    print("    [M1의 W를 10% 축소(finger 반올림 시뮬레이션) -- 여전히 constraint 통과해야 함]")
    _l4_pass_result = revalidate_finger_override(
        _l4_ctx, {"nmos": lut}, {"M1": _l4_r1.W * 0.9}, _l4_metrics_specs, _l4_constraints,
        gm_id_bounds=(2.0, 28.0))
    _l4_du_pass = _l4_pass_result["device_updates"]["M1"]
    assert abs(_l4_du_pass["new_gm"] / _l4_du_pass["new_gm_id"] - _l4_r1.ID) < 1e-15, \
        "ID가 보존되지 않음 -- W가 바뀌어도 ID는 topology로 고정이어야 한다"
    assert _l4_pass_result["ok"] and not _l4_pass_result["violated_constraints"], \
        "10% 축소는 여전히 constraint를 통과해야 하는데 위반으로 나옴"
    assert _l4_pass_result["unaffected_metrics_skipped"] == ["other_current"], \
        "M3를 안 건드렸으니 other_current는 재계산 스킵 목록에 있어야 한다"
    print(f"    PASS: ID 보존 확인(diff=0), new_gain={_l4_pass_result['metric_deltas']['stage_gain']['new']:.4f}dB "
          f"(통과), other_current는 무관해서 재계산 스킵")

    print("    [M1의 W를 40% 축소 -- 이번엔 constraint를 실제로 위반해야 함]")
    _l4_fail_result = revalidate_finger_override(
        _l4_ctx, {"nmos": lut}, {"M1": _l4_r1.W * 0.6}, _l4_metrics_specs, _l4_constraints,
        gm_id_bounds=(2.0, 28.0))
    assert not _l4_fail_result["ok"], "40% 축소는 gain을 threshold 밑으로 떨어뜨려야 하는데 ok=True로 나옴"
    assert len(_l4_fail_result["violated_constraints"]) == 1 and \
        _l4_fail_result["violated_constraints"][0]["metric"] == "stage_gain", \
        "위반된 constraint가 정확히 stage_gain 하나여야 한다"
    print(f"    PASS: new_gain={_l4_fail_result['metric_deltas']['stage_gain']['new']:.4f}dB < "
          f"threshold={_l4_threshold:.4f}dB -- violated_constraints로 정확히 검출됨")

    print("    [원본 ctx는 건드리지 않는 순수 함수인지]")
    assert _l4_ctx.sized["M1"]["W"] == _l4_r1.W, "revalidate_finger_override()가 원본 ctx를 변형했다"
    print("    PASS: 원본 ctx.sized['M1']['W'] 불변")

    print()
    print("  [L4b apply_and_revalidate_pair_adjustment() -- suggest_pair_finger_adjustments()(L3)의")
    print("  제안을 revalidate_finger_override()(L4)로 자동 승인/거부하는 상위 오케스트레이션,")
    print("  세션12 M3a 그룹(M9b/M18b) 사례가 실제 동기 -- .ai/context.md 세션13 D절]")
    _l4b_L, _l4b_vds = 0.5e-6, 0.6
    _l4b_crit = size_transistor(gm=200e-6, gm_id=12.0, L=_l4b_L, lut=lut, vds=_l4b_vds)
    _l4b_crit_gds = _l4b_crit.gm / lut.gm_gds_ratio(12.0, _l4b_L, _l4b_vds, 0.0)
    _l4b_harm = size_transistor(gm=50e-6, gm_id=15.0, L=_l4b_L, lut=lut, vds=_l4b_vds)
    _l4b_harm_gds = _l4b_harm.gm / lut.gm_gds_ratio(15.0, _l4b_L, _l4b_vds, 0.0)

    # 그래프 레벨(홀수차수 개선용) -- Ma/Mb(critical, 면적 제약 대상)와 Xa/Xb(harmless, 제약과
    # 무관)가 각각 독립된 고립 edge라 baseline에서 둘 다 홀수차수 4개씩 기여 -- 어느 쪽을 먼저
    # +1해도 개선폭(-4)이 동일한 "타이" 상황을 의도적으로 구성해, 정렬 안정성(먼저 나온 소자
    # 우선)으로 Ma/Mb가 1순위가 되게 한다(transistors 리스트 순서 Ma,Mb,Xa,Xb).
    _l4b_transistors = [
        Transistor("Ma", "nmos", source="Na1", drain="Nb1", gate="ga",
                   n_fingers=1, finger_w=_l4b_crit.W),
        Transistor("Mb", "nmos", source="Na2", drain="Nb2", gate="gb",
                   n_fingers=1, finger_w=_l4b_crit.W),
        Transistor("Xa", "nmos", source="Xa1", drain="Xb1", gate="gxa",
                   n_fingers=1, finger_w=_l4b_harm.W),
        Transistor("Xb", "nmos", source="Xa2", drain="Xb2", gate="gxb",
                   n_fingers=1, finger_w=_l4b_harm.W),
    ]
    _l4b_pairs = [("Ma", "Mb"), ("Xa", "Xb")]

    _l4b_suggestions = suggest_pair_finger_adjustments(_l4b_transistors, _l4b_pairs)
    print(f"    후보 순서: {[(s.names, s.delta_fingers, s.resulting_odd_count) for s in _l4b_suggestions]}")
    assert _l4b_suggestions[0].names == ("Ma", "Mb") and _l4b_suggestions[0].delta_fingers == 1, \
        "1순위 후보가 (Ma,Mb)+1이 아님 -- 타이 상황에서 리스트 순서 우선이 깨짐"
    assert _l4b_suggestions[1].names == ("Xa", "Xb") and _l4b_suggestions[1].delta_fingers == 1, \
        "2순위 후보가 (Xa,Xb)+1이 아님"

    def _l4b_ctx_for(crit, crit_gds, harm, harm_gds):
        return SizingContext(sized={
            "Ma": {"ID": crit.ID, "W": crit.W, "L": _l4b_L, "gm": crit.gm, "gm_id": 12.0,
                   "gds": crit_gds, "kind": "nmos", "vds": _l4b_vds, "vs": 0.0},
            "Mb": {"ID": crit.ID, "W": crit.W, "L": _l4b_L, "gm": crit.gm, "gm_id": 12.0,
                   "gds": crit_gds, "kind": "nmos", "vds": _l4b_vds, "vs": 0.0},
            "Xa": {"ID": harm.ID, "W": harm.W, "L": _l4b_L, "gm": harm.gm, "gm_id": 15.0,
                   "gds": harm_gds, "kind": "nmos", "vds": _l4b_vds, "vs": 0.0},
            "Xb": {"ID": harm.ID, "W": harm.W, "L": _l4b_L, "gm": harm.gm, "gm_id": 15.0,
                   "gds": harm_gds, "kind": "nmos", "vds": _l4b_vds, "vs": 0.0},
        })

    print("    [케이스1: 1순위(Ma,Mb)는 면적 제약 위반 -> 자동으로 건너뛰고 2순위(Xa,Xb) 채택]")
    _l4b_baseline_pair_area = 2 * _l4b_crit.W * _l4b_L
    _l4b_metrics = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}
    _l4b_constraints = [{"metric": "pair_area", "op": "<=", "value": _l4b_baseline_pair_area * 1.3}]
    _l4b_ctx1 = _l4b_ctx_for(_l4b_crit, _l4b_crit_gds, _l4b_harm, _l4b_harm_gds)
    _l4b_result1 = apply_and_revalidate_pair_adjustment(
        _l4b_transistors, _l4b_pairs, _l4b_ctx1, {"nmos": lut}, _l4b_metrics, _l4b_constraints,
        gm_id_bounds=(2.0, 28.0))
    assert _l4b_result1["applied"] and _l4b_result1["chosen"].names == ("Xa", "Xb"), \
        "1순위가 위반인데 2순위(Xa,Xb)로 자동 폴백하지 않음"
    assert len(_l4b_result1["rejected"]) == 1 and \
        _l4b_result1["rejected"][0]["suggestion"].names == ("Ma", "Mb") and \
        not _l4b_result1["rejected"][0]["revalidation"]["ok"] and \
        _l4b_result1["rejected"][0]["revalidation"]["violated_constraints"][0]["metric"] == "pair_area", \
        "거부된 후보 기록이 (Ma,Mb)/pair_area 위반과 정확히 일치하지 않음"
    _l4b_updated = {t.name: t.n_fingers for t in _l4b_result1["transistors"]}
    assert _l4b_updated == {"Ma": 1, "Mb": 1, "Xa": 2, "Xb": 2}, \
        "채택된 (Xa,Xb)만 n_fingers가 반영되고 나머지는 원본 그대로여야 함"
    print(f"    PASS: 채택={_l4b_result1['chosen'].names}, 거부 1건(Ma,Mb/pair_area), "
          f"결과 n_fingers={_l4b_updated}")

    print("    [케이스2: 면적 제약이 (Ma,Mb)/(Xa,Xb) 둘 다에 걸리면 -- 전부 위반, applied=False]")
    _l4b_metrics_strict = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb", "Xa", "Xb"]}}
    _l4b_baseline_all_area = 2 * _l4b_crit.W * _l4b_L + 2 * _l4b_harm.W * _l4b_L
    _l4b_constraints_strict = [{"metric": "pair_area", "op": "<=", "value": _l4b_baseline_all_area * 1.05}]
    _l4b_ctx2 = _l4b_ctx_for(_l4b_crit, _l4b_crit_gds, _l4b_harm, _l4b_harm_gds)
    _l4b_result2 = apply_and_revalidate_pair_adjustment(
        _l4b_transistors, _l4b_pairs, _l4b_ctx2, {"nmos": lut}, _l4b_metrics_strict,
        _l4b_constraints_strict, gm_id_bounds=(2.0, 28.0))
    assert not _l4b_result2["applied"] and _l4b_result2["chosen"] is None, \
        "둘 다 위반인데 applied=True로 나옴"
    assert len(_l4b_result2["rejected"]) == 2, "두 후보 모두 시도(및 거부) 기록이 남아야 함"
    assert [t.n_fingers for t in _l4b_result2["transistors"]] == [1, 1, 1, 1], \
        "전부 거부됐으면 transistors가 원본과 동일해야 함"
    print(f"    PASS: applied=False, chosen=None, 거부 {len(_l4b_result2['rejected'])}건, "
          f"transistors 원본 유지")

    print("    [케이스3: max_candidates=1 -- 1순위만 시도하고 그 이상 폴백하지 않음]")
    _l4b_result3 = apply_and_revalidate_pair_adjustment(
        _l4b_transistors, _l4b_pairs, _l4b_ctx1, {"nmos": lut}, _l4b_metrics, _l4b_constraints,
        gm_id_bounds=(2.0, 28.0), max_candidates=1)
    assert not _l4b_result3["applied"] and len(_l4b_result3["rejected"]) == 1, \
        "max_candidates=1인데 2순위까지 시도됨"
    print(f"    PASS: max_candidates=1 -> 1순위만 시도, applied=False(2순위는 원래 통과했을 것이지만 "
          f"상한 때문에 시도 자체를 안 함)")

    print()
    print("  [L4c run_topology_pipeline_with_finger_fixup() -- 세션12 M3a 그룹(11소자) 실제")
    print("  connectivity를 topology.json으로 감싸 run_topology_pipeline() 전체 체인(load_topology->")
    print("  audit_row_split->build_stick_diagram->mirror_symmetric_trail)을 실제로 태워, euler-")
    print("  blocked 상태에서 M9b/M18b 핑거조정으로 자동 해결되는지 end-to-end로 확인]")
    _l4c_m3a_netlist = [
        {"name": "M3a", "kind": "nmos", "source": "N3a4a", "drain": "Vom1", "gate": "Vbias3"},
        {"name": "M3b", "kind": "nmos", "source": "N3b4b", "drain": "Vop1", "gate": "Vbias3"},
        {"name": "M4a", "kind": "nmos", "source": "Vy", "drain": "N3a4a", "gate": "Vip"},
        {"name": "M4b", "kind": "nmos", "source": "Vy", "drain": "N3b4b", "gate": "Vim"},
        {"name": "M5", "kind": "nmos", "source": "gnd", "drain": "Vy", "gate": "Vbias4"},
        {"name": "M9b", "kind": "nmos", "source": "Vop1", "drain": "Vg15", "gate": "N14a14b"},
        {"name": "M10", "kind": "nmos", "source": "gnd", "drain": "Vop1", "gate": "Vbias4"},
        {"name": "M18b", "kind": "nmos", "source": "Vom1", "drain": "Vg25", "gate": "N24b23a"},
        {"name": "M19", "kind": "nmos", "source": "gnd", "drain": "Vom1", "gate": "Vbias4"},
        {"name": "M64", "kind": "nmos", "source": "N64_63", "drain": "Vbias3", "gate": "Vbias3"},
        {"name": "M63", "kind": "nmos", "source": "Vy", "drain": "N64_63", "gate": "Vbias3"},
    ]  # 세션12 M3a 그룹(.ai/context.md, stick_diagram.py Test 5.6)과 connectivity 동일
    _l4c_matching_pairs_meta = [
        {"names": ["M4a", "M4b"], "matching_sensitivity": "offset"},
        {"names": ["M3a", "M3b"], "matching_sensitivity": "ratio"},
        {"names": ["M10", "M19"], "matching_sensitivity": "ratio"},
        {"names": ["M9b", "M18b"], "matching_sensitivity": "ratio"},
    ]
    _l4c_row = "m3a_row"
    _l4c_L, _l4c_vds, _l4c_gm_id = 0.5e-6, 0.6, 12.0
    _l4c_r = size_transistor(gm=50e-6, gm_id=_l4c_gm_id, L=_l4c_L, lut=lut, vds=_l4c_vds)
    _l4c_gds = _l4c_r.gm / lut.gm_gds_ratio(_l4c_gm_id, _l4c_L, _l4c_vds, 0.0)
    _l4c_names = [d["name"] for d in _l4c_m3a_netlist]
    # 전부 n_fingers=1 baseline -- delta=-1은 new_n=0<1로 자동 무효화되므로(suggest_pair_
    # finger_adjustments() 내부 규칙), 이 self-test의 모든 후보는 항상 +1(면적 증가)만 나온다.
    _l4c_overrides = {n: {"n_fingers": 1, "finger_w": _l4c_r.W, "w": _l4c_r.W, "stack_id": _l4c_row}
                       for n in _l4c_names}
    _l4c_ctx = SizingContext(sized={
        n: {"ID": _l4c_r.ID, "W": _l4c_r.W, "L": _l4c_L, "gm": _l4c_r.gm, "gm_id": _l4c_gm_id,
            "gds": _l4c_gds, "kind": "nmos", "vds": _l4c_vds, "vs": 0.0}
        for n in _l4c_names
    })
    _l4c_metrics = {"group_area": {"type": "sum_area", "devices": _l4c_names}}
    _l4c_baseline_area = len(_l4c_names) * _l4c_r.W * _l4c_L

    with _tempfile.TemporaryDirectory() as _l4c_tmpdir:
        _l4c_topo_path = _os.path.join(_l4c_tmpdir, "m3a_row.topology.json")
        with open(_l4c_topo_path, "w", encoding="utf-8") as _l4c_f:
            json.dump({
                "topology_name": "m3a_row_selftest",
                "schema_version": "2.0",
                "netlist": _l4c_m3a_netlist,
                "symmetry": {"matching_pairs": _l4c_matching_pairs_meta, "dispositions": []},
            }, _l4c_f)

        print("    [케이스A: 면적 예산이 넉넉하면 -- 1라운드 만에 M9b/M18b +1로 자동 해결]")
        _l4c_constraints_a = [{"metric": "group_area", "op": "<=", "value": _l4c_baseline_area * 1.5}]
        _l4c_result_a = run_topology_pipeline_with_finger_fixup(
            _l4c_topo_path, _l4c_overrides, _l4c_ctx, {"nmos": lut}, _l4c_metrics, _l4c_constraints_a,
            gm_id_bounds=(2.0, 28.0))
        assert _l4c_result_a["unresolved_row"] is None and _l4c_result_a["unresolved_reason"] is None, \
            f"넉넉한 예산인데도 못 풀림: {_l4c_result_a['unresolved_row']}/{_l4c_result_a['unresolved_reason']}"
        assert _blocked_euler_rows(_l4c_result_a["audit_row_split"]) == [], \
            "euler 체크가 최종적으로 안 풀림 -- unresolved_row=None인데 실제로는 아직 blocked"
        assert len(_l4c_result_a["fixup_rounds"]) == 1, "1라운드에 바로 풀려야 하는데 라운드 수가 다름"
        _l4c_chosen_a = _l4c_result_a["fixup_rounds"][0]["result"]["chosen"]
        assert set(_l4c_chosen_a.names) == {"M9b", "M18b"} and _l4c_chosen_a.delta_fingers == 1, \
            f"채택된 조정이 M9b/M18b +1이 아님(세션12 손검증과 다름): {_l4c_chosen_a}"
        _l4c_final_n = {t.name: t.n_fingers for t in _l4c_result_a["transistors"]}
        assert _l4c_final_n["M9b"] == 2 and _l4c_final_n["M18b"] == 2, "M9b/M18b n_fingers가 2로 안 바뀜"
        print(f"    PASS: 1라운드 해결, 채택={_l4c_chosen_a.names}, "
              f"최종 n_fingers M9b={_l4c_final_n['M9b']} M18b={_l4c_final_n['M18b']} "
              f"(세션12 손검증 6개->2개 홀수차수와 일치, mirror_symmetric으로 성공)")

        print("    [케이스B: 면적 예산이 극도로 타이트하면 -- 핑거조정 후보 전부 위반. **세션18부터**")
        print("    바로 unresolved로 포기하지 않고 그룹분할(crossover routing)로 자동 폴백해 euler를")
        print("    완전히 푼다(세션15 C절 harness 배선, 위 docstring (5) 참고) -- 세션14~17엔")
        print("    unresolved_row/no_valid_candidate로 끝났던 바로 그 시나리오를 재사용해 동작이")
        print("    바뀌었음을 직접 확인한다(회귀가 아니라 의도된 기능 확장)]")
        _l4c_constraints_b = [{"metric": "group_area", "op": "<=", "value": _l4c_baseline_area * 1.001}]
        _l4c_result_b = run_topology_pipeline_with_finger_fixup(
            _l4c_topo_path, _l4c_overrides, _l4c_ctx, {"nmos": lut}, _l4c_metrics, _l4c_constraints_b,
            gm_id_bounds=(2.0, 28.0))
        assert _l4c_result_b["unresolved_row"] is None and _l4c_result_b["unresolved_reason"] is None, \
            f"그룹분할 폴백으로 euler는 항상 풀려야 하는데: " \
            f"{_l4c_result_b['unresolved_row']}/{_l4c_result_b['unresolved_reason']}"
        assert _blocked_euler_rows(_l4c_result_b["audit_row_split"]) == [], \
            "euler 체크가 최종적으로 안 풀림"
        assert len(_l4c_result_b["fixup_rounds"]) == 1 and \
            not _l4c_result_b["fixup_rounds"][0]["result"]["applied"], \
            "핑거조정 시도 자체는 여전히 1회 일어나고 여전히 실패해야 함(위반 후보 전부 거부)"
        assert len(_l4c_result_b["group_splits"]) == 1, \
            f"그룹분할이 정확히 1번 기록돼야: {_l4c_result_b['group_splits']}"
        _l4c_split_b = _l4c_result_b["group_splits"][0]
        assert _l4c_split_b["row"] == _l4c_row and _l4c_split_b["n_segments"] == 3 and \
            _l4c_split_b["crossover_count"] == 2 and \
            _l4c_split_b["node_pairing_fallback_used"] is False, \
            f"그룹분할 기록 내용이 실측과 다름: {_l4c_split_b}"
        _l4c_bc_pairs = sorted(sorted(v) for v in _l4c_split_b["branch_composites"].values())
        assert _l4c_bc_pairs == [["M3a", "M4a"], ["M3b", "M4b"]], \
            f"M3a/M4a, M3b/M4b branch가 crossover 짝짓기 전에 합성됐어야: " \
            f"{_l4c_split_b['branch_composites']}"
        _l4c_final_stack = {t.name: t.stack_id for t in _l4c_result_b["transistors"]}
        assert _l4c_final_stack["M3a"] == _l4c_final_stack["M4a"] == _l4c_final_stack["M5"], \
            f"M3a/M4a(branch composite)+M5가 같은 segment에 있어야: {_l4c_final_stack}"
        assert _l4c_final_stack["M3b"] == _l4c_final_stack["M4b"] == \
            _l4c_final_stack["M64"] == _l4c_final_stack["M63"], \
            f"M3b/M4b(branch composite)+M64/M63이 같은 segment에 있어야: {_l4c_final_stack}"
        assert not _l4c_result_b["audit_row_split"].ok, \
            "이 함수는 euler(체크1)만 고친다 -- 3b/3c 잔여 실패는 그대로 audit.ok=False에 반영돼야 " \
            "함(정직하게 남기기, 세션17 원칙과 동일 -- group_splits가 있다고 몰래 True로 안 둔갑)"
        print(f"    PASS: unresolved_row=None(그룹분할로 euler 완전 해결), "
              f"group_splits={_l4c_split_b['n_segments']}세그먼트/crossover={_l4c_split_b['crossover_count']}, "
              f"branch_composites={_l4c_split_b['branch_composites']}, "
              f"audit.ok={_l4c_result_b['audit_row_split'].ok}(3b/3c 잔여 실패는 이 함수 책임 밖, 정직 유지)")

        print("    [케이스C: cell_groups를 명시하면 -- 세션18 C-3, 그룹분할로 생긴 새 _seg* row가")
        print("    원래 row가 속했던 cell_groups 항목에 자동으로 추가되는지(원본 dict는 불변)]")
        _l4c_cell_groups = {"cellA": [_l4c_row, "other_row_not_present"]}
        _l4c_cell_groups_snapshot = {k: list(v) for k, v in _l4c_cell_groups.items()}
        _l4c_result_c = run_topology_pipeline_with_finger_fixup(
            _l4c_topo_path, _l4c_overrides, _l4c_ctx, {"nmos": lut}, _l4c_metrics, _l4c_constraints_b,
            gm_id_bounds=(2.0, 28.0), cell_groups=_l4c_cell_groups)
        assert _l4c_result_c["unresolved_row"] is None, \
            f"cell_groups가 있어도 그룹분할 폴백은 동일하게 성공해야: {_l4c_result_c['unresolved_row']}"
        assert _l4c_cell_groups == _l4c_cell_groups_snapshot, \
            f"호출자가 준 cell_groups 원본이 변형됨(순수함수 위반): {_l4c_cell_groups}"
        _l4c_cellA_checks = _l4c_result_c["audit_row_split"]["cellA"].checks
        _l4c_seg_euler_names = {c.name[len("1. euler["):-1] for c in _l4c_cellA_checks
                                 if c.name.startswith("1. euler[") and c.ok}
        assert _l4c_seg_euler_names == {"m3a_row_seg0", "m3a_row_seg1", "m3a_row_seg2"}, \
            f"cell_groups 자동확장이 안 돼 새 seg row가 cellA 감사에서 누락됨: {_l4c_seg_euler_names}"
        print(f"    PASS: cellA 감사에 seg row 3개 전부 포함됨({sorted(_l4c_seg_euler_names)}), "
              f"호출자 원본 cell_groups는 그대로({_l4c_cell_groups})")

    print()
    print("  [L5 optimize_full_circuit_budget() 실배선 -- run_topology_pipeline_with_finger_")
    print("  fixup()을 harness 최상위(optimize_full_circuit_budget())에서 실제로 호출하는지")
    print("  end-to-end로 확인(세션15 실배선, .ai/context.md 참고) -- known_sizing으로 M3a")
    print("  11소자 W/ID를 직접 시드해(theta/device_roles 없이) A/B/C엔진을 우회하고, harness가")
    print("  euler-blocked를 자동으로 finger 조정으로 풀어 sizing/sizing_overrides에 반영하는지 확인]")
    _ofcb_matching_pairs_meta = [{**p, "current_forced": False} for p in _l4c_matching_pairs_meta]
    # M4a/M4b(offset)와 M3a/M3b(ratio+shares_node=False=branch_symmetric, 세션15 probe로
    # audit 출력에서 확인)는 3c(common-centroid)가 필수 게이트다 -- n_fingers=1(baseline)로
    # 두면 repair_matching_safety()가 필요할 때 common_centroid_layout()의 무관한 기존
    # 한계(count>=n_rows=2 필요, 세션15 probe_preexisting_bug.py로 확인된 사전 존재 버그,
    # 이번 배선과 무관)에 걸려 이 배선 테스트 자체가 막힌다. M9b/M18b도 3c 필수 게이트지만
    # 그건 이 테스트가 검증하려는 euler-fixup 대상이라 baseline n_fingers=1로 그대로
    # 두고, fixup이 실제로 2로 올리는지를 확인한다.
    #
    # baseline을 짝수(2배)로 주면 그 소자의 그래프 홀짝 기여가 바뀌어(홀수 기여 -> 짝수
    # 기여) euler-blocked 판정 자체가 달라지는 걸 세션15 probe로 실측 확인했다(2배 시도 시
    # M9b/M18b+1로 안 풀리고 5라운드 소진 후 M5가 6핑거까지 발산) -- 그래서 홀짝을 보존하는
    # 3배(여전히 홀수)로 줘서 세션12/L4c와 동일하게 M9b/M18b+1 1라운드 성공을 유지하면서
    # count(=3)>=n_rows(=2)로 common-centroid 크래시만 피한다.
    _ofcb_known_sizing = {
        n: {"ID": _l4c_r.ID,
            "W": _l4c_r.W * (3 if n in ("M4a", "M4b", "M3a", "M3b") else 1), "L": _l4c_L,
            "gm": _l4c_r.gm, "gm_id": _l4c_gm_id, "gds": _l4c_gds, "kind": "nmos",
            "vds": _l4c_vds, "vs": 0.0}
        for n in _l4c_names
    }
    _ofcb_baseline_area = sum(_ofcb_known_sizing[n]["W"] * _ofcb_known_sizing[n]["L"]
                               for n in _l4c_names)
    with _tempfile.TemporaryDirectory() as _ofcb_tmpdir:
        _ofcb_topo_path = _os.path.join(_ofcb_tmpdir, "m3a_row_ofcb.topology.json")
        with open(_ofcb_topo_path, "w", encoding="utf-8") as _ofcb_f:
            json.dump({
                "topology_name": "m3a_row_ofcb_selftest",
                "schema_version": "2.0",
                "netlist": _l4c_m3a_netlist,
                "symmetry": {"matching_pairs": _ofcb_matching_pairs_meta, "dispositions": []},
                "sizing_roles": {
                    "metrics": {"group_area": {"type": "sum_area", "devices": _l4c_names}},
                    "constraints": [{"metric": "group_area", "op": "<=",
                                      "value": _ofcb_baseline_area * 1.5}],
                },
            }, _ofcb_f)
        _ofcb_spec = {
            "lut_by_kind": {"nmos": lut},
            "known_sizing": _ofcb_known_sizing,
            "stack_groups_override": {"m3a_row": _l4c_names},
            "min_finger_w": 0.1e-6, "max_finger_w": 40e-6,
            "gm_id_bounds": (2.0, 28.0),
            # 2026-08-14 -- load_topology()가 이제 propose_device_roles_gap_fill()을 자동
            # 배선해서(사용자 지시, 절대원칙) 이 fixture의 netlist에서도 L_role이 자동으로
            # 채워질 수 있다 -- 이 테스트는 known_sizing으로 device_roles를 완전히 우회하는
            # 시나리오를 검증하려는 것이지만, L_role 루프 자체는(권위 있는 소스가 아니면)
            # 여전히 도는다는 게 기존 계약이라 L_min이 없으면 크래시한다. 실제 스펙은 항상
            # L_min을 주므로(예: _spec_two_stage_ota()) 여기도 맞춘다.
            "L_min": 0.1e-6,
        }
        _ofcb_result = optimize_full_circuit_budget(_ofcb_topo_path, _ofcb_spec)
        assert _ofcb_result["pipeline_result"]["unresolved_row"] is None, \
            f"euler-blocked가 harness 경로에서 자동으로 안 풀림: " \
            f"{_ofcb_result['pipeline_result']['unresolved_row']}/" \
            f"{_ofcb_result['pipeline_result']['unresolved_reason']}"
        assert _blocked_euler_rows(_ofcb_result["pipeline_result"]["audit_row_split"]) == [], \
            "euler 체크가 최종적으로 안 풀림"
        assert _ofcb_result["sizing_overrides"]["M9b"]["n_fingers"] == 2 and \
            _ofcb_result["sizing_overrides"]["M18b"]["n_fingers"] == 2, \
            f"harness가 반환한 sizing_overrides에 finger 조정이 반영 안 됨: " \
            f"M9b={_ofcb_result['sizing_overrides']['M9b']}, M18b={_ofcb_result['sizing_overrides']['M18b']}"
        assert _ofcb_result["sizing"]["M9b"]["W"] != _ofcb_known_sizing["M9b"]["W"], \
            "harness가 반환한 sizing(gm/ID)에 finger 조정에 따른 W 변화가 반영 안 됨"
        # 세션18 -- matching quality(3b/3c) 자동수정도 이제 bare repair_matching_safety()가
        # 아니라 run_matching_safety_with_finger_growth()로 승격됐다(위 audit_ok=False 분기
        # 참고) -- growth_rounds가 실제로 채워지는지 확인해 새 배선이 이 경로에서도 실제로
        # 개입함을 검증(이 fixture는 M4a/M3a·M4b/M3b branch composite 내부에서 n_fingers가
        # 갈라져(growth_not_applicable) 실제 성장은 안 되지만, 시도 자체는 기록돼야 한다).
        assert "growth_rounds" in _ofcb_result["pipeline_result"] and \
            len(_ofcb_result["pipeline_result"]["growth_rounds"]) >= 1, \
            f"run_matching_safety_with_finger_growth()가 개입한 흔적(growth_rounds)이 없음: " \
            f"{_ofcb_result['pipeline_result'].get('growth_rounds')}"
        print(f"    PASS: optimize_full_circuit_budget()이 euler-blocked를 자동 해결(M9b/M18b "
              f"n_fingers=2), sizing_overrides/sizing 둘 다 최종 상태로 갱신됨 -- matching "
              f"quality(3b/3c)는 run_matching_safety_with_finger_growth()가 이어받아 처리 "
              f"(growth_rounds={len(_ofcb_result['pipeline_result']['growth_rounds'])}건, "
              f"unresolved_reason={_ofcb_result['pipeline_result'].get('unresolved_reason')}, "
              f"audit_ok={_ofcb_result['audit_ok']})")

    print()
    print("  [L5b resolve_stack_layout() -- declared vertical_stack_id를 audit_vertical_")
    print("  stack_id_vs_kcl()로 사전 검증하는 게이트(2026-08-10, 사용자 확정: review 대상")
    print("  있으면 명시적 에러). 실회로(정합) + 합성 fixture(원인불명 hub, 진짜 에러 유발)")
    print("  둘 다 확인]")
    import os as _rsl_os
    _rsl_lib = _rsl_os.path.join(_rsl_os.path.dirname(_rsl_os.path.abspath(__file__)), "library")
    _rsl_trs, _rsl_meta = load_topology(
        _rsl_os.path.join(_rsl_lib, "current_reuse_telescopic_ota.topology.json"))
    _rsl_pairs_meta = _rsl_meta["symmetry"]["matching_pairs"]
    _rsl_forced = [tuple(p["names"]) for p in _rsl_pairs_meta if p["current_forced"]]
    _rsl_device_roles = {k: v for k, v in (_rsl_meta.get("device_roles") or {}).items()
                          if not k.startswith("_")}
    _rsl_groups = resolve_stack_layout(_rsl_trs, _rsl_forced, _rsl_device_roles)
    _rsl_declared_ok = all(v.get("vertical_stack_id") for v in _rsl_device_roles.values()
                            if isinstance(v, dict))
    assert _rsl_declared_ok, "이 fixture는 51/51 declared를 전제로 함(회귀 시 다른 검증으로 대체)"
    _rsl_all_members = sorted(m for members in _rsl_groups.values() for m in members)
    assert _rsl_all_members == sorted(t.name for t in _rsl_trs), \
        "감사 게이트 통과 후에도 소자 누락/중복 없어야 함"
    print(f"    PASS: current_reuse_telescopic_ota(51소자, declared 전수 정합) -- 감사 게이트 "
          f"통과, {len(_rsl_groups)}개 그룹 정상 반환")

    # 2026-08-11(세션28 후반부) -- resolve_stack_layout()이 이제 derive_horizontal_stack_
    # groups()를 거치므로(vertical_stack_id는 PMOS/NMOS를 섞을 수 있지만 물리 레이아웃 행은
    # 그럴 수 없음), 반환된 모든 그룹이 항상 kind 동질이어야 한다는 게 이 함수의 새 불변식이다
    # -- 이번 버그(build_graph()가 mixed-kind를 잡아내기 전엔 이 그룹이 조용히 PMOS/NMOS를
    # 섞고 있었음, 8/26개 declared vsid에서 실측 확인)의 재발 방지 가드.
    _rsl_by_name = {t.name: t for t in _rsl_trs}
    for _rsl_sid, _rsl_members in _rsl_groups.items():
        _rsl_kinds = {_rsl_by_name[m].kind for m in _rsl_members if m in _rsl_by_name}
        assert len(_rsl_kinds) <= 1, \
            f"resolve_stack_layout() 반환 그룹이 kind 동질이 아님(회귀 -- derive_horizontal_" \
            f"stack_groups() 배선 확인할 것): {_rsl_sid} -> {_rsl_members} -> {_rsl_kinds}"
    print(f"    PASS: {len(_rsl_groups)}개 그룹 전부 kind 동질(PMOS/NMOS 혼합 0건) -- "
          f"derive_horizontal_stack_groups() 배선 확인")

    _rsl_bad_trs = [
        Transistor("T1", "pmos", source="vdd", drain="Na", gate="g1"),
        Transistor("T2", "nmos", source="gnd", drain="Na", gate="g2"),
        Transistor("T3", "pmos", source="vdd", drain="Nb", gate="g3"),
        Transistor("T4", "nmos", source="gnd", drain="Nb", gate="g4"),
    ]
    # T1/T2는 Na(2단자)로 진짜 직렬, T3/T4는 Nb(2단자)로 진짜 직렬 -- 서로 완전히 무관한
    # 두 그룹인데, declared vertical_stack_id는 T1/T3를 "fake_merged"로 잘못 합쳐놨다고
    # 가정(3+단자 허브도 전혀 없어 원인 불명 -- 진짜 선언 실수 시나리오).
    _rsl_bad_roles = {
        "T1": {"vertical_stack_id": "fake_merged"}, "T2": {"vertical_stack_id": "groupA_tail"},
        "T3": {"vertical_stack_id": "fake_merged"}, "T4": {"vertical_stack_id": "groupB_tail"},
    }
    try:
        resolve_stack_layout(_rsl_bad_trs, [], _rsl_bad_roles)
        print("    FAIL: 원인 불명 vertical_stack_id 불일치인데 에러가 안 남")
    except ValueError as e:
        assert "vertical_stack_id" in str(e), f"에러 메시지가 원인을 안 가리킴: {e}"
        print(f"    OK: 예상대로 ValueError -> {e}")

    print()
    print("  [L5c 헤드룸 singleton 정책(다음 세션 최우선①, 2026-08-11 세션28) -- M5/M61,")
    print("  M60/M66, M36a/M38, M18_bg(diode_reference, ideal_sources 대조 검증 포함),")
    print("  M7=M6/M36b=M36a(same_as_device) 전부를 실제 optimize_full_circuit_budget()")
    print("  으로 51소자 실회로 실행해 한 번에 검증. classab_centering_dev_v(세션27이")
    print("  이미 분리해둔 별개 미해결 항목)만 임시로 제외 -- 이번 검증 범위 밖]")
    import numpy as _l5c_np
    _l5c_lib = _rsl_os.path.join(_rsl_os.path.dirname(_rsl_os.path.abspath(__file__)), "library")
    _l5c_lutfile = _rsl_os.path.join(
        _rsl_os.path.dirname(_rsl_os.path.abspath(__file__)), "sky130_nfet_pfet_lut_sample.npz")
    with open(_rsl_os.path.join(_l5c_lib, "current_reuse_telescopic_ota.topology.json"),
              "r", encoding="utf-8") as _l5c_f:
        _l5c_topo = json.load(_l5c_f)
    for _l5c_t in _l5c_topo["sizing_roles"]["theta"]:
        if _l5c_t["name"] == "K_replica":
            _l5c_t["bounds"] = [0.05, 0.05]
        elif _l5c_t["name"] == "r_classab_battery":
            _l5c_t["bounds"] = [0.3, 0.3]
        else:
            _l5c_lo, _l5c_hi = _l5c_t["bounds"]
            _l5c_mid = (_l5c_lo + _l5c_hi) / 2.0
            _l5c_t["bounds"] = [_l5c_mid, _l5c_mid]
    # 2026-08-12(세션30) -- gain_db도 classab_centering_dev_v와 같은 이유로 이 테스트의
    # constraints에서 뺀다: optimize_multistage()의 VDS 탐색이 이제 vertical_stack_id
    # 헤드룸을 반영해(근본수정, reserved_vds_for_other_stack_members() 참고) M1a 등의
    # VDS가 더 이상 물리적으로 불가능한 값(예: vdd 전체)을 자유롭게 고르지 못한다 -- 그
    # 결과 이 테스트가 K_replica/r_classab_battery만 자유고 나머지 전부 midpoint 고정한
    # **단일** theta 점에서 gain_db가 74.9dB로 살짝 낮아졌다(75.6 미달). 이 테스트의
    # 목적은 애초에 gain 최적화가 아니라 헤드룸 singleton KVL 검증뿐이고(아래 vy_tail/
    # vbias4/cmfb 합=vdd assert), 실제 gain 최적화는 세션29 SLSQP 검증(자유 theta 탐색,
    # gain_db=84.15dB 달성)의 몫이다.
    _l5c_topo["sizing_roles"]["constraints"] = [
        c for c in _l5c_topo["sizing_roles"]["constraints"]
        if c["metric"] not in ("classab_centering_dev_v", "gain_db")]
    with _tempfile.TemporaryDirectory() as _l5c_tmpdir:
        _l5c_topo_path = _rsl_os.path.join(_l5c_tmpdir, "current_reuse_telescopic_ota.l5c.json")
        with open(_l5c_topo_path, "w", encoding="utf-8") as _l5c_f:
            json.dump(_l5c_topo, _l5c_f)
        _l5c_d = _l5c_np.load(_l5c_lutfile)
        _l5c_nmos = SemiEmpiricalGmIdLUT(_l5c_d["L"], _l5c_d["VGS"], _l5c_d["VDS"], _l5c_d["VS"],
                                          _l5c_d["ID_n"], _l5c_d["GM_n"], _l5c_d["GDS_n"], _l5c_d["CGG_n"],
                                          W_ref=5e-6, SID_1F=_l5c_d["SID_1F_n"])
        _l5c_pmos = SemiEmpiricalGmIdLUT(_l5c_d["L"], _l5c_d["VGS"], _l5c_d["VDS"], _l5c_d["VS"],
                                          _l5c_d["ID_p"], _l5c_d["GM_p"], _l5c_d["GDS_p"], _l5c_d["CGG_p"],
                                          W_ref=5e-6, SID_1F=_l5c_d["SID_1F_p"])
        _l5c_spec = {
            "lut_by_kind": {"nmos": _l5c_nmos, "pmos": _l5c_pmos}, "lut": _l5c_nmos, "vdd": 1.8,
            "L_candidates": [float(v) for v in _l5c_nmos.L_grid],
            "VDS_candidates": [float(v) for v in _l5c_nmos.VDS_grid[::24]],
            "gm_id_grid": [4.0, 8.0, 12.0, 16.0, 20.0, 24.0],
            "L_min": 0.15e-6, "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
            "W_bounds": (1e-6, 200e-6), "min_vds_by_role": {"cascode": 0.2, "tail": 0.3, "mirror": 0.3},
            "stage_objective": "power", "stage_w_max": 200e-6,
            "min_finger_w": 1e-6, "max_finger_w": 40e-6,
            "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
            "t_lln": 30e-9, "PM_target_deg": 70.0,
            "Cc": 500e-15, "Cf": 500e-15, "Cs": 500e-15, "C_Ltot": 1e-12,
            "t_settle_total": 40e-9, "omega_c": 6.9 / 30e-9,
        }
        _l5c_result = optimize_full_circuit_budget(_l5c_topo_path, _l5c_spec, grid_points_per_theta=1)
    _l5c_sizing = _l5c_result["sizing"]
    _l5c_vy_tail = sum(_l5c_sizing[n]["vds"] for n in ("M61", "M64", "M63", "M5"))
    _l5c_vbias4 = _l5c_sizing["M60"]["vds"] + _l5c_sizing["M66"]["vds"]
    _l5c_cmfb = _l5c_sizing["M36a"]["vds"] + _l5c_sizing["M37a"]["vds"] + _l5c_sizing["M38"]["vds"]
    for _l5c_name, _l5c_sum in (("vy_tail(M61+M64+M63+M5)", _l5c_vy_tail),
                                 ("vbias4(M60+M66)", _l5c_vbias4),
                                 ("cmfb(M36a+M37a+M38)", _l5c_cmfb)):
        assert abs(_l5c_sum - 1.8) < 1e-6, f"{_l5c_name} 합이 vdd(1.8V)와 불일치(회귀): {_l5c_sum}"
    print(f"    PASS: vy_tail/vbias4/cmfb 세 컬럼 전부 vdd(1.8V)와 정확히 일치 -- "
          f"M5/M61/M64/M63/M60/M66/M36a/M37a/M38 KVL 정합")
    assert _l5c_sizing["M18_bg"]["vds"] < 0.5, \
        f"M18_bg(diode_reference)가 여전히 큰 값을 받음(회귀): {_l5c_sizing['M18_bg']['vds']}"
    print(f"    PASS: M18_bg(diode_reference)=={_l5c_sizing['M18_bg']['vds']}V -- thin_roles로 "
          f"얇게 배정됨(더 이상 ~vdd 아님)")

    print("    [사용자 지적(2026-08-11) -- ideal current source(전압 자유)/voltage source")
    print("    (전류 자유)는 헤드룸 '합=vdd' 계약에 영향이 다르다. role 라벨만 믿지 않고")
    print("    실제 topology.json의 ideal_sources 선언과 대조하는지 -- 선언을 지우면(같은")
    print("    M18_bg 케이스) 정확히 거부하는지 합성 fixture로 확인]")
    _l5c_neg_topo = json.loads(json.dumps(_l5c_topo))  # deep copy
    _l5c_neg_topo["ideal_sources"] = []
    with _tempfile.TemporaryDirectory() as _l5c_neg_tmpdir:
        _l5c_neg_path = _rsl_os.path.join(_l5c_neg_tmpdir, "current_reuse_telescopic_ota.l5c_neg.json")
        with open(_l5c_neg_path, "w", encoding="utf-8") as _l5c_neg_f:
            json.dump(_l5c_neg_topo, _l5c_neg_f)
        try:
            optimize_full_circuit_budget(_l5c_neg_path, _l5c_spec, grid_points_per_theta=1)
            print("    FAIL: ideal_sources 선언이 없는데 우회가 조용히 성공함")
            assert False, "ideal_sources 검증이 실제로 걸리지 않음(회귀)"
        except ValueError as _l5c_neg_e:
            assert "M18_bg" in str(_l5c_neg_e) and "ideal_sources" in str(_l5c_neg_e), \
                f"에러 메시지가 원인을 안 가리킴: {_l5c_neg_e}"
            print(f"    OK: ideal_sources 선언 제거 시 정확히 거부됨 -> {_l5c_neg_e}")

    assert abs(_l5c_sizing["M7"]["vds"] - _l5c_sizing["M6"]["vds"]) < 1e-9, \
        f"M7(same_as_device=M6)이 M6과 다른 값을 받음(회귀): M6={_l5c_sizing['M6']['vds']}, " \
        f"M7={_l5c_sizing['M7']['vds']}"
    assert abs(_l5c_sizing["M36b"]["vds"] - _l5c_sizing["M36a"]["vds"]) < 1e-9, \
        f"M36b(same_as_device=M36a)가 M36a와 다른 값을 받음(회귀): M36a={_l5c_sizing['M36a']['vds']}, " \
        f"M36b={_l5c_sizing['M36b']['vds']}"
    print(f"    PASS: M7==M6(={_l5c_sizing['M6']['vds']}V), M36b==M36a(={_l5c_sizing['M36a']['vds']}V) "
          f"-- same_as_device가 물리적으로 동일해야 하는 병렬/매칭 파트너의 VDS를 정확히 복사")
    print(f"    PASS: 51소자 전체 sizing_roles 우회 없이 완주(gain_db="
          f"{_l5c_result['metrics']['gain_db']:.2f}, mismatch_sigma_mV="
          f"{_l5c_result['metrics']['mismatch_sigma_mV']:.2f}, cmrr_estimate_db="
          f"{_l5c_result['metrics']['cmrr_estimate_db']:.2f}, psrr_estimate_db="
          f"{_l5c_result['metrics']['psrr_estimate_db']:.2f})")

    print()
    print("  [L4d suggest_matching_finger_growth()/apply_and_revalidate_matching_finger_growth()/")
    print("  run_matching_safety_with_finger_growth() -- 세션16 2번. repair_matching_safety()가")
    print("  branch 복합 매칭(세션16 1번)으로도 못 푸는 3c(n_fingers 부족)를, gm/ID를 깨지 않는")
    print("  선에서 핑거를 늘려 자동으로 완전히 풀 수 있는지]")
    _l4d_L, _l4d_vds = 0.5e-6, 0.6
    _l4d_r = size_transistor(gm=200e-6, gm_id=12.0, L=_l4d_L, lut=lut, vds=_l4d_vds)
    _l4d_gds = _l4d_r.gm / lut.gm_gds_ratio(12.0, _l4d_L, _l4d_vds, 0.0)

    print("    [suggest_matching_finger_growth() -- delta 계산 단위 확인]")
    _l4d_g_trs = [Transistor("Ma", "nmos", source="s", drain="d1", n_fingers=1, finger_w=_l4d_r.W),
                  Transistor("Mb", "nmos", source="s", drain="d2", n_fingers=1, finger_w=_l4d_r.W)]
    _g1 = suggest_matching_finger_growth(("Ma", "Mb"), _l4d_g_trs, min_fingers=2)
    assert _g1 == {"names": ("Ma", "Mb"), "delta_fingers": 1,
                    "note": "common-centroid 회전-최적 경로(residual=0)를 위해 n_fingers 1->2"}
    _g2_trs = [Transistor("Mc", "nmos", source="s", drain="d1", n_fingers=2, finger_w=_l4d_r.W),
               Transistor("Md", "nmos", source="s", drain="d2", n_fingers=2, finger_w=_l4d_r.W)]
    assert suggest_matching_finger_growth(("Mc", "Md"), _g2_trs, min_fingers=2) is None, \
        "이미 n_fingers=2(충분)인데 growth를 제안함"
    _g3_trs = [Transistor("Me", "nmos", source="s", drain="d1", n_fingers=1, finger_w=_l4d_r.W),
               Transistor("Mf", "nmos", source="s", drain="d2", n_fingers=3, finger_w=_l4d_r.W)]
    assert suggest_matching_finger_growth(("Me", "Mf"), _g3_trs, min_fingers=2) is None, \
        "names 내부 n_fingers가 서로 다른데(1,3) growth를 제안함 -- 호출자 책임 밖 케이스"
    print("    PASS: delta=1(부족), None(이미 충분), None(내부 불일치) 전부 정확")

    _l4d_transistors = [
        Transistor("Ma", "nmos", source="Na1", drain="Nb1", gate="ga",
                   n_fingers=1, finger_w=_l4d_r.W),
        Transistor("Mb", "nmos", source="Na2", drain="Nb2", gate="gb",
                   n_fingers=1, finger_w=_l4d_r.W),
    ]
    _l4d_ctx = SizingContext(sized={
        "Ma": {"ID": _l4d_r.ID, "W": _l4d_r.W, "L": _l4d_L, "gm": _l4d_r.gm, "gm_id": 12.0,
               "gds": _l4d_gds, "kind": "nmos", "vds": _l4d_vds, "vs": 0.0},
        "Mb": {"ID": _l4d_r.ID, "W": _l4d_r.W, "L": _l4d_L, "gm": _l4d_r.gm, "gm_id": 12.0,
               "gds": _l4d_gds, "kind": "nmos", "vds": _l4d_vds, "vs": 0.0},
    })
    _l4d_baseline_area = 2 * _l4d_r.W * _l4d_L

    print("    [케이스1: 넉넉한 면적 제약 -- growth가 gm/ID를 안 깨서 적용됨]")
    _l4d_metrics = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}
    _l4d_loose = [{"metric": "pair_area", "op": "<=", "value": _l4d_baseline_area * 3.0}]
    _l4d_r1 = apply_and_revalidate_matching_finger_growth(
        ("Ma", "Mb"), _l4d_transistors, _l4d_ctx, {"nmos": lut}, _l4d_metrics, _l4d_loose,
        gm_id_bounds=(2.0, 28.0))
    assert _l4d_r1["applied"] and _l4d_r1["growth"]["delta_fingers"] == 1
    assert {t.name: t.n_fingers for t in _l4d_r1["transistors"]} == {"Ma": 2, "Mb": 2}
    assert _l4d_r1["revalidation"]["ok"]
    print(f"    PASS: applied=True, n_fingers 1->2, gm/ID 재검증 통과")

    print("    [케이스2: 빡빡한 면적 제약 -- growth가 gm/ID를 깨서(면적 초과) 거부됨]")
    _l4d_tight = [{"metric": "pair_area", "op": "<=", "value": _l4d_baseline_area * 1.05}]
    _l4d_r2 = apply_and_revalidate_matching_finger_growth(
        ("Ma", "Mb"), _l4d_transistors, _l4d_ctx, {"nmos": lut}, _l4d_metrics, _l4d_tight,
        gm_id_bounds=(2.0, 28.0))
    assert not _l4d_r2["applied"] and _l4d_r2["revalidation"] is not None and \
        not _l4d_r2["revalidation"]["ok"]
    assert [t.n_fingers for t in _l4d_r2["transistors"]] == [1, 1], \
        "거부됐는데 transistors가 원본과 다름"
    print(f"    PASS: applied=False(면적 제약 위반, 정직하게 거부), transistors 원본 유지")

    print("    [run_matching_safety_with_finger_growth() -- current_reuse_telescopic_ota의 M6")
    print("    그룹 실제 사례(세션16 1번 branch 복합 매칭 셀프테스트와 동일 소자) -- branch 복합")
    print("    매칭만으로는 못 풀던 3c를, 핑거증가+gm/ID 재검증까지 이어붙여 완전히 풀리는지]")
    _l4d_m6_trs, _l4d_m6_meta = load_topology(
        _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "library",
                       "current_reuse_telescopic_ota.topology.json"))
    _l4d_m6_by_name = {t.name: t for t in _l4d_m6_trs}
    _l4d_m6_names = ["M1a", "M1b", "M2a", "M2b", "M6", "M7"]
    _l4d_m6_row = [_dc_replace(_l4d_m6_by_name[n], n_fingers=1, finger_w=_l4d_r.W, stack_id="seg1")
                   for n in _l4d_m6_names]
    _l4d_m6_pairs = [("M1a", "M1b"), ("M2a", "M2b")]
    _l4d_m6_sensitivity = {("M1a", "M1b"): "offset", ("M2a", "M2b"): "ratio"}
    _l4d_m6_ctx = SizingContext(sized={
        n: {"ID": _l4d_r.ID, "W": _l4d_r.W, "L": _l4d_L, "gm": _l4d_r.gm, "gm_id": 12.0,
            "gds": _l4d_gds, "kind": "pmos", "vds": _l4d_vds, "vs": 0.0}
        for n in _l4d_m6_names
    })
    _l4d_m6_metrics = {"group_area": {"type": "sum_area", "devices": _l4d_m6_names}}
    _l4d_m6_baseline_area = sum(_l4d_r.W * _l4d_L for _ in _l4d_m6_names)
    _l4d_m6_constraints = [{"metric": "group_area", "op": "<=", "value": _l4d_m6_baseline_area * 3.0}]

    _l4d_final = run_matching_safety_with_finger_growth(
        {"seg1": _l4d_m6_row}, _l4d_m6_pairs, _l4d_m6_sensitivity, _l4d_m6_ctx, {"pmos": lut},
        _l4d_m6_metrics, _l4d_m6_constraints, gm_id_bounds=(2.0, 28.0))
    assert _l4d_final["unresolved_pair"] is None, \
        f"핑거증가로 3c 관점에서는 완전히 풀려야 하는데 못 풂: {_l4d_final['unresolved_pair']}/" \
        f"{_l4d_final['unresolved_reason']}"
    # unresolved_pair=None이 audit.ok=True의 동의어가 아니라는 걸 위 docstring에서 명시했다 --
    # 실제로 이 케이스는 3b/3c는 전부 풀리지만 "2. box-shape"(M6/M7만 남은 행과의 폭 비율)가
    # 별도로 FAIL한다(이 함수의 책임 밖, 세션16에서 실측 확인) -- 그래서 전체 audit.ok가
    # 아니라 "3b/3c 필수 게이트가 전부 PASS인지"를 직접 확인한다.
    _l4d_bad_matching_checks = [c for c in _l4d_final["audit"].checks
                                 if not c.ok and "[참고용" not in c.name
                                 and (c.name.startswith("3b.") or c.name.startswith("3c."))]
    assert not _l4d_bad_matching_checks, \
        f"3b/3c 필수 게이트가 아직 FAIL: {_l4d_bad_matching_checks}"
    # common_centroid_layout()의 회전-최적 경로는 n_fingers=2인 소자를 "2개 행에 1개씩"으로
    # 물리적으로 나눠 배치한다(진짜 common-centroid) -- 그래서 rows에는 같은 이름이 여러 행에
    # 걸쳐 n_fingers=1짜리로 여러 번 나타난다. 총 finger 수는 행별로 합산해야 한다(이름 하나에
    # 값 하나만 남기는 flat dict는 나중 행 값으로 덮어써버려 틀린다).
    _l4d_total_n = {}
    for devs in _l4d_final["rows"].values():
        for t in devs:
            _l4d_total_n[t.name] = _l4d_total_n.get(t.name, 0) + t.n_fingers
    assert _l4d_total_n["M1a"] == _l4d_total_n["M1b"] == \
        _l4d_total_n["M2a"] == _l4d_total_n["M2b"] == 2, \
        f"M1a/M1b/M2a/M2b 총 n_fingers가 전부 2로 안 자람: {_l4d_total_n}"
    print(f"    PASS: 3b/3c 필수 게이트 전부 통과(M1a/M1b/M2a/M2b 총 n_fingers 전부 2로 성장, "
          f"2개 행에 1개씩 진짜 common-centroid 분배 -- "
          f"세션16 1번 branch 복합 매칭 + 2번 핑거증가가 함께 M6 그룹의 매칭 문제를 끝까지 "
          f"풀어냄), growth_rounds={len(_l4d_final['growth_rounds'])}회. "
          f"audit.ok={_l4d_final['audit'].ok}(box-shape는 이 함수 책임 밖이라 별개로 FAIL 가능)")

    print()
    print("  [L4e run_matching_safety_with_finger_growth() -- 세션17 설계안 3번. gm/ID 예산이")
    print("  타이트해서 핑거증가 자체가 거부되면(gm_id_violation), 인접배치(3b)로 최후수단")
    print("  완화하고 3c FAIL은 정직하게 그대로 남기는지]")
    _l4e_devices = [
        Transistor("Ma", "nmos", source="Vtail", drain="Nd_a", gate="ga",
                   n_fingers=1, finger_w=_l4d_r.W),
        Transistor("Mb", "nmos", source="Vtail", drain="Nd_b", gate="gb",
                   n_fingers=1, finger_w=_l4d_r.W),
    ]
    print("    [케이스1: 빡빡한 면적 제약(_l4d_tight, 케이스2와 동일) -- allow_layout_relaxation=True]")
    _l4e_r1 = run_matching_safety_with_finger_growth(
        {"seg1": _l4e_devices}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, _l4d_ctx,
        {"nmos": lut}, _l4d_metrics, _l4d_tight, gm_id_bounds=(2.0, 28.0),
        allow_layout_relaxation=True)
    assert _l4e_r1["unresolved_pair"] is None and \
        _l4e_r1["unresolved_reason"] == "relaxed_to_layout", \
        f"완화가 적용돼야 하는데 안 됨: {_l4e_r1['unresolved_pair']}/{_l4e_r1['unresolved_reason']}"
    assert len(_l4e_r1["relaxed_pairs"]) == 1 and \
        _l4e_r1["relaxed_pairs"][0]["pair"] == ("Ma", "Mb") and \
        _l4e_r1["relaxed_pairs"][0]["reason"] == "gm_id_budget_exceeded" and \
        _l4e_r1["relaxed_pairs"][0]["trim_recommended"] is True, \
        f"relaxed_pairs 내용이 예상과 다름: {_l4e_r1['relaxed_pairs']}"
    assert _l4e_r1["relaxed_pairs"][0]["interdig_ok"] is not None, \
        "완화 후 재감사가 한 번 더 돌아야 interdig_ok가 채워짐 -- 여전히 None"
    # 완화는 3c 요구사항 자체를 없애지 않는다 -- offset pair는 여전히 3c가 필수 게이트이므로
    # n_fingers=1인 이상 기하학적으로 dx<=0.5를 달성 못 해(세션16 D-3) audit.ok는 False여야
    # 한다(위 docstring "완화는 3c 요구사항을 없애지 않는다" 참고, 몰래 성공으로 둔갑 금지).
    assert not _l4e_r1["audit"].ok, "완화됐다고 audit.ok가 몰래 True로 둔갑함 -- 정책 위반"
    _l4e_3c_check = next(c for c in _l4e_r1["audit"].checks
                          if c.name.startswith("3c.") and "[Ma/Mb]" in c.name)
    assert not _l4e_3c_check.ok and "[참고용" not in _l4e_3c_check.name, \
        f"3c[Ma/Mb]가 여전히 필수 게이트로 FAIL이어야 하는데: {_l4e_3c_check}"
    assert len(_l4e_r1["growth_rounds"]) == 1 and not _l4e_r1["growth_rounds"][0]["result"]["applied"], \
        "growth 시도가 정확히 1번, 실패로 기록돼야 함"
    print(f"    PASS: unresolved_reason='relaxed_to_layout', relaxed_pairs=1건"
          f"(interdig_ok={_l4e_r1['relaxed_pairs'][0]['interdig_ok']}), "
          f"audit.ok=False(3c FAIL 정직하게 유지), growth 시도 1회만 기록")

    print("    [케이스2: 같은 예산, allow_layout_relaxation=False -- 세션16 기존 동작 그대로")
    print("    보존되는지(회귀 대조, 완화 기능 자체를 꺼도 예전처럼 즉시 unresolved)]")
    _l4e_r2 = run_matching_safety_with_finger_growth(
        {"seg1": list(_l4e_devices)}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, _l4d_ctx,
        {"nmos": lut}, _l4d_metrics, _l4d_tight, gm_id_bounds=(2.0, 28.0),
        allow_layout_relaxation=False)
    assert _l4e_r2["unresolved_pair"] == ("Ma", "Mb") and \
        _l4e_r2["unresolved_reason"] == "gm_id_violation" and \
        _l4e_r2["relaxed_pairs"] == [], \
        f"allow_layout_relaxation=False인데 완화가 적용됨(회귀): {_l4e_r2}"
    print(f"    PASS: allow_layout_relaxation=False면 완화 없이 즉시 unresolved_reason="
          f"'gm_id_violation'(세션16 동작 그대로 보존)")

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
    print("  [2026-08-11(세션28) HeadroomPolicy.thin_roles -- 'diode_reference'도 cascode와")
    print("  동급으로 얇게 배정받는지(M18_bg 실사례: diode-connected 기준전압 생성기,")
    print("  '남는 예산을 나눠 가질 파트너'가 없어 min_vds만 필요). voltage_divider(M39/M40)")
    print("  처럼 의도적으로 남는 예산을 나눠 갖는 role은 여전히 그대로 동작하는지도 함께 확인]")
    _hr_stack3 = [
        {"name": "Mref", "role": "diode_reference", "min_vds": 0.20},
        {"name": "Mtail", "role": "tail", "min_vds": 0.30},
        {"name": "Minput", "role": "input", "min_vds": 0.40},
    ]
    _hr_result3 = allocate_stack_headroom(1.8, _hr_stack3)
    assert abs(_hr_result3["Mref"] - 0.20) < 1e-12, \
        f"diode_reference에 min_vds가 그대로 안 쓰임(thin_roles 배선 확인): {_hr_result3}"
    assert abs(sum(_hr_result3.values()) - 1.8) < 1e-9, "diode_reference 포함 시에도 합이 vdd와 불일치"
    print(f"    PASS: diode_reference(Mref)=min_vds 그대로, tail/input이 나머지(1.6V)를 균등분배"
          f"({_hr_result3}), 합={sum(_hr_result3.values()):.4f}V == vdd")

    _hr_divider = [
        {"name": "Da", "role": "voltage_divider", "min_vds": 0.20},
        {"name": "Db", "role": "voltage_divider", "min_vds": 0.20},
    ]
    _hr_result_div = allocate_stack_headroom(1.8, _hr_divider)
    assert abs(_hr_result_div["Da"] - 0.9) < 1e-9 and abs(_hr_result_div["Db"] - 0.9) < 1e-9, \
        f"voltage_divider(M39/M40류)는 여전히 vdd/2씩 균등분배여야 하는데(회귀): {_hr_result_div}"
    print(f"    PASS: voltage_divider(Da/Db, diode-connected이지만 thin_roles에 없음) -- "
          f"여전히 vdd/2씩 균등분배됨(M39/M40 설계의도 그대로 보존, thin_roles 일반화가 이 "
          f"role을 건드리지 않음을 확인)")

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

    print("  [2026-08-19 세션37 연속 신설 -- 'load' role: gm/gds가 아니라 ro(=1/gds) 자체를")
    print("  최대화. nmcnr_amplifier M202(vds=1.0V) 실측으로 발견 -- 이 조건에서 gm_id가")
    print("  중간(~3.5)에서 ro가 피크라 'gain'(gm/gds 최대, gm_id=16)은 오히려 손해였다]")
    _gm_id_load = search_gm_id_for_role(lut, _role_L, _role_vds, 0.0, _role_id_target,
                                         role="load", W_bounds=(1e-6, 200e-6))
    def _ro_direct(g):
        return 1.0 / (g * _role_id_target / lut.gm_gds_ratio(g, _role_L, _role_vds, 0.0))
    _best_ro_direct = max(_ro_direct(g) for g in _feasible_check)
    assert abs(_ro_direct(_gm_id_load) - _best_ro_direct) < 1e-6, \
        "load role이 실제 ro 최댓값을 못 고름"
    print(f"    PASS: load(ro 최대) gm_id={_gm_id_load:.2f}, ro={_ro_direct(_gm_id_load):.3e} == "
          f"feasible 전수조사 최댓값과 일치(nmcnr_amplifier M202 실측 -- .ai/context.md 세션37 "
          f"참고 -- 이 role을 신설하게 된 계기이자 sky130 실제 LUT에서의 검증)")

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
    _ctx_b = SizingContext(spec={"lut_by_kind": {"nmos": lut}, "omega_c": 2 * math.pi * 1e6, "C_cmfb": 2e-12},
                            kind_of={"Mcmfb": "nmos"})
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
    _ctx_m = SizingContext(spec={"lut_by_kind": {"nmos": lut}}, sized={"M1": {"ID": 10e-6}, "M2": {"ID": 20e-6}},
                            kind_of={"M1": "nmos", "M2": "nmos"})
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
    print("  [optimize_full_circuit_budget() -- sizing_roles/device_roles 둘 다 없는 회로는 "
          "즉시 빈 결과로 통과]")
    # 2026-08-14 -- 원래 이 fixture로 folded_cascode.topology.json을 그대로 썼다("sizing_roles
    # 없는 실회로"의 편의상 예시였을 뿐, 이 테스트의 실제 의도는 "device_roles가 비어 있으면
    # L_role 루프가 아무것도 안 하고 빈 결과를 낸다"였다) -- propose_device_roles_gap_fill()/
    # apply_device_roles_gap_fill()을 실제로 그 파일에 적용해 device_roles를 채운 뒤로 이
    # fixture 전제(device_roles 없음)가 깨졌다. 이 테스트가 실제로 검증하려는 것과 무관한
    # 외부 상태(실제 라이브러리 파일의 최신 내용)에 더 이상 의존하지 않도록, 의도를 그대로
    # 담은 최소 합성 fixture로 교체한다(device_roles/sizing_roles 둘 다 명시적으로 없음).
    # ⚠️ 2026-08-14 세션34 재정정 -- Mo(gate='vb', 레일 소스+고정 바이어스 게이트 단일
    # 소자)가 propose_device_roles_gap_fill()의 새 4번째 소스("파트너 없는 active-load ->
    # gm_id_role='gain' 제안", 이 세션에서 신설)에 걸려 require_device_roles_reviewed()가
    # 더 이상 조용히 통과하지 않게 됐다 -- 이 테스트의 의도(sizing_roles/device_roles가
    # 완전히 비어있을 때 optimize_full_circuit_budget()이 즉시 빈 결과를 내는지)와 무관한
    # 충돌이라, Mo를 diode-connected(gate=자기 drain)로 바꿔 애초에 gap-fill의 어떤 제안
    # 대상도 아니게 만든다(diode-connected 단독 소자는 mirror 그룹조차 안 됨, len(ms)<2).
    _lib_dir_recipe = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "library")
    _ofc_empty_topo = {
        "schema_version": "2.0", "topology_name": "_test_empty_roles", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [{"name": "Mo", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "out"}],
        "symmetry": {"matching_pairs": [], "dispositions": []},
        "sizing_roles": None, "device_roles": None,
    }
    with _tempfile.TemporaryDirectory() as _ofc_empty_tmpdir:
        _ofc_empty_path = _os.path.join(_ofc_empty_tmpdir, "_test_empty_roles.topology.json")
        with open(_ofc_empty_path, "w", encoding="utf-8") as _ofc_empty_f:
            json.dump(_ofc_empty_topo, _ofc_empty_f)
        _ofc_result = optimize_full_circuit_budget(_ofc_empty_path, {"lut": lut})
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
        _ofc_spec = {"lut": lut, "lut_by_kind": {"nmos": lut}, "omega_c": 2 * math.pi * 1e6, "cap": 2e-12}
        _ofc_full = optimize_full_circuit_budget(_ofc_topo_path, _ofc_spec, grid_points_per_theta=5)
        _theta_star, _sizing, _metrics = _ofc_full["theta_star"], _ofc_full["sizing"], _ofc_full["metrics"]
        assert _ofc_full["pipeline_result"] is not None, \
            "Mtest는 W까지 다 있는데 전체 파이프라인(assign_finger_geometry/run_topology_pipeline)이 안 돎"
        assert _ofc_full["audit_ok"], f"단일 소자 넷리스트인데 audit이 FAIL: {_ofc_full['pipeline_result']}"

        # 전수비교: 같은 격자를 직접 순회해 손으로 찾은 최적값과 정확히 일치하는지 확인.
        _manual_best = None
        for _i in range(5):
            _N = _lerp(1.0, 5.0, _i / 4)
            _ctx_manual = SizingContext(spec=_ofc_spec, kind_of={"Mtest": "nmos"})
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
    print("  [device_roles.gm_id_match_vgs_of -- 2026-08-19 세션38 신설, gm_id_role 루프의 2차 "
          "pass가 실제로 companion의 VGS로 결합되는지 (nmcnr_amplifier M203/M204 계기)]")
    # Ma(diode-connected 레퍼런스, gate=drain=NodeC)/Mb(gate=NodeC, source 공유)는 게이트·소스가
    # 물리적으로 같은 노드에 묶여 VGS가 항상 같아야 하지만 VDS는 다르다(현실의 M203/M204와 동일
    # 패턴) -- known_sizing으로 둘 다 L/vds를 직접 시드해(headroom 우회, 위 diagnose_sizing_
    # roles_gap() 테스트 1과 동일 패턴) 이 2차 pass만 격리해서 검증한다. current_forced=True로
    # 선언했으므로 ID는 반드시 같아야 한다(propagate_topology_forced_currents()의 KCL 제약 --
    # 실측으로 확인: 다르게 주면 즉시 ValueError, 이 테스트 자신의 전제를 실제로 검증해줌).
    _gmv_topo = {
        "schema_version": "2.0", "topology_name": "_gmv_test", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [
            {"name": "Ma", "kind": "nmos", "source": "vss", "drain": "NodeC", "gate": "NodeC"},
            {"name": "Mb", "kind": "nmos", "source": "vss", "drain": "out", "gate": "NodeC"},
        ],
        "symmetry": {"matching_pairs": [
            {"names": ["Ma", "Mb"], "current_forced": True, "matching_sensitivity": "ratio"}],
            "dispositions": []}, "sizing_roles": None,
        "device_roles": {
            "Ma": {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror", "vs": 0.0},
            "Mb": {"gm_id_match_vgs_of": "Ma", "L_role": "mirror", "headroom_role": "mirror", "vs": 0.0},
        },
    }
    _gmv_L, _gmv_vds_a, _gmv_vds_b = 0.5e-6, 0.8, 0.5  # ⚠️ 일부러 다른 VDS
    _gmv_known = {"Ma": {"ID": 1e-5, "L": _gmv_L, "vds": _gmv_vds_a, "vs": 0.0},
                  "Mb": {"ID": 1e-5, "L": _gmv_L, "vds": _gmv_vds_b, "vs": 0.0}}
    with _tempfile.TemporaryDirectory() as _gmv_tmp:
        _gmv_path = _os.path.join(_gmv_tmp, "_gmv_test.topology.json")
        with open(_gmv_path, "w", encoding="utf-8") as _f:
            json.dump(_gmv_topo, _f)
        _gmv_spec = {"lut_by_kind": {"nmos": lut}, "vdd": 1.8, "L_min": 0.15e-6,
                     "W_bounds": (1e-6, 200e-6), "min_vds_by_role": {"mirror": 0.2},
                     "known_sizing": _gmv_known}
        # optimize_full_circuit_budget()이 아니라 _build_theta_evaluator()+evaluate({})를 직접
        # 쓴다 -- 이 테스트가 검증하려는 건 device_roles 2차 pass 하나뿐이고, 전체 harness는
        # assign_finger_geometry()/run_topology_pipeline_with_finger_fixup() 같은 무관한 레이아웃
        # 단계까지 통과해야 해서(이 2-소자 toy 회로엔 그 단계용 spec 필드가 없어 실패함) 이
        # 테스트의 의도와 무관한 실패를 낼 수 있다(위 "합성 sizing_roles" 테스트와 달리 이 fixture는
        # 레이아웃까지 검증할 의도가 없음).
        _gmv_ev = _build_theta_evaluator(_gmv_path, _gmv_spec)
        _gmv_ctx, _ = _gmv_ev["evaluate"]({})
    _gmv_gm_id_a, _gmv_gm_id_b = _gmv_ctx.sized["Ma"]["gm_id"], _gmv_ctx.sized["Mb"]["gm_id"]
    _gmv_target_vgs = lut.vgs_for_gm_id(_gmv_gm_id_a, _gmv_L, _gmv_vds_a, 0.0)
    _gmv_expected_gm_id_b = lut.gm_id_for_vgs(_gmv_target_vgs, _gmv_L, _gmv_vds_b, 0.0)
    assert abs(_gmv_gm_id_b - _gmv_expected_gm_id_b) < 1e-9, \
        f"Mb의 gm_id({_gmv_gm_id_b})가 Ma의 VGS 역산값({_gmv_expected_gm_id_b})과 다름"
    # ⚠️ build_toy_lut()는 구조 검증 전용 단순 모델이라 VGS(gm_id,L,vds)가 vds와 무관하다(실측
    # 확인) -- 그래서 gm_id_a==gm_id_b가 나오는 게 이 toy LUT에서는 정상이다(실제 sky130 LUT의
    # M203/M204라면 vds가 달라 갈라짐, .ai/context.md 세션37 §1-⑪ 실측 참고). 이 테스트가 실제로
    # 검증하는 건 "값이 다르다"가 아니라 "Mb의 gm_id가 Ma의 VGS를 역산한 정확한 값과 일치한다"는
    # 것 자체다 -- Mb는 device_roles에 gm_id_role이 아예 없으므로(gm_id_match_vgs_of만 있음),
    # 이 2차 pass가 없으면 Mb는 애초에 sizing되지 않아 아래 딕셔너리 접근이 KeyError로 죽는다
    # (즉 이 테스트가 통과한다는 사실 자체가 이미 2차 pass가 실제로 실행됐다는 증거).
    print(f"    PASS: Ma(root,'matching')=gm_id {_gmv_gm_id_a:.3f}@vds={_gmv_vds_a}V, "
          f"Mb(gm_id_match_vgs_of=Ma)=gm_id {_gmv_gm_id_b:.3f}@vds={_gmv_vds_b}V -- "
          f"companion VGS 역산과 정확히 일치(Mb에 gm_id_role이 없으므로 이 값은 2차 pass로만 "
          f"나올 수 있음)")

    print("  [gm_id_match_vgs_of가 아직 sizing 안 된(존재하지 않는) 소자를 참조하면 ValueError]")
    _gmv_bad_topo = json.loads(json.dumps(_gmv_topo))
    _gmv_bad_topo["device_roles"]["Mb"]["gm_id_match_vgs_of"] = "Mz"
    with _tempfile.TemporaryDirectory() as _gmv_bad_tmp:
        _gmv_bad_path = _os.path.join(_gmv_bad_tmp, "_gmv_bad.topology.json")
        with open(_gmv_bad_path, "w", encoding="utf-8") as _f:
            json.dump(_gmv_bad_topo, _f)
        try:
            _build_theta_evaluator(_gmv_bad_path, _gmv_spec)["evaluate"]({})
            raise AssertionError("존재하지 않는 companion인데 에러가 안 났다")
        except ValueError as _gmv_e:
            assert "gm_id_match_vgs_of" in str(_gmv_e) and "Mz" in str(_gmv_e), \
                f"에러 메시지에 gm_id_match_vgs_of/Mz가 없음: {_gmv_e}"
            print(f"    PASS: ValueError -- {str(_gmv_e)[:70]}...")

    print()
    print("  [device_roles.vds_match_vgs_of -- 2026-08-19 세션38 연속 신설, 헤드룸 루프가 다른 "
          "컬럼(다른 vertical_stack_id 그룹) 소자의 VGS를 이 소자의 VDS로 강제하는지, 그리고 "
          "같은 컬럼의 나머지 소자가 남는 예산을 정확히 흡수하는지 (nmcnr_amplifier M204/M301 "
          "계기 -- M301.gate=M204.drain이라 VGS(M301)=VDS(M204)가 KVL로 강제됨)]")
    # 실제 M202(pmos)/M204(nmos) 컬럼 구조를 그대로 축소 복제한다(단일 소자끼리는 audit_
    # vertical_stack_id_vs_kcl()이 "진짜 vdd~gnd 컬럼"으로 인정하지 않는다 -- PMOS/NMOS가
    # 드레인 노드를 공유해야 KCL이 성립함). col_a=Ka(pmos)+Ma(nmos, 드레인=NodeA)/col_b=
    # Kb(pmos)+Mb(nmos, 드레인=NodeB, 게이트=NodeA -- 그래서 VGS(Mb)=VDS(Ma)가 KVL로
    # 강제되고, vds_match_vgs_of="Ma"로 그 관계를 선언한다). Ma는 known_sizing으로 gm_id/L/ID를
    # 직접 시드(compensation이 채우는 것과 동일한 역할, vds는 일부러 안 줘서 col_a 헤드룸이
    # 직접 풀게 함 -- _ref_depth() 위상정렬이 col_a를 col_b보다 먼저 처리하는지까지 검증).
    _vmv_vdd = 1.8
    _vmv_topo = {
        "schema_version": "2.0", "topology_name": "_vmv_test", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [
            {"name": "Ka", "kind": "pmos", "source": "vdd", "drain": "NodeA", "gate": "vb_ka"},
            {"name": "Ma", "kind": "nmos", "source": "vss", "drain": "NodeA", "gate": "vb_ma"},
            {"name": "Kb", "kind": "pmos", "source": "vdd", "drain": "NodeB", "gate": "vb_kb"},
            {"name": "Mb", "kind": "nmos", "source": "vss", "drain": "NodeB", "gate": "NodeA"},
        ],
        "symmetry": {"matching_pairs": [], "dispositions": []}, "sizing_roles": None,
        "device_roles": {
            # Ma는 일부러 gm_id_role을 안 준다(known_sizing으로 compensation처럼 gm_id를
            # 외부에서 고정). Ka/Kb/Mb는 propose_device_roles_gap_fill()의 자동 제안(파트너
            # 없는 active load -> "gain"류)이 require_device_roles_reviewed()를 막지 않도록
            # gm_id_role을 명시 선언해둔다(이 테스트가 검증하려는 vds 흐름과는 무관, review
            # 게이트 통과용).
            "Ka": {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror",
                   "vertical_stack_id": "col_a", "vs": 0.0},
            "Ma": {"headroom_role": "mirror", "vertical_stack_id": "col_a", "vs": 0.0},
            "Kb": {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror",
                   "vertical_stack_id": "col_b", "vs": 0.0},
            "Mb": {"vds_match_vgs_of": "Ma", "gm_id_role": "matching", "L_role": "mirror",
                   "headroom_role": "mirror", "vertical_stack_id": "col_b", "vs": 0.0},
        },
    }
    _vmv_known = {"Ka": {"ID": 1e-5, "vs": 0.0}, "Ma": {"ID": 1e-5, "L": 0.5e-6, "gm_id": 15.0, "vs": 0.0},
                  "Kb": {"ID": 1e-5, "vs": 0.0}, "Mb": {"ID": 1e-5, "vs": 0.0}}
    with _tempfile.TemporaryDirectory() as _vmv_tmp:
        _vmv_path = _os.path.join(_vmv_tmp, "_vmv_test.topology.json")
        with open(_vmv_path, "w", encoding="utf-8") as _f:
            json.dump(_vmv_topo, _f)
        _vmv_spec = {"lut_by_kind": {"nmos": lut, "pmos": lut}, "vdd": _vmv_vdd, "L_min": 0.15e-6,
                     "W_bounds": (1e-6, 200e-6), "min_vds_by_role": {"mirror": 0.2},
                     "known_sizing": _vmv_known}
        _vmv_ctx, _ = _build_theta_evaluator(_vmv_path, _vmv_spec)["evaluate"]({})
    _vmv_vds_a = _vmv_ctx.sized["Ma"]["vds"]
    assert abs(_vmv_vds_a - _vmv_vdd / 2) < 1e-9, \
        f"Ka/Ma 둘 다 'mirror'라 균등분배(vdd/2={_vmv_vdd/2})가 나와야 하는데 Ma.vds={_vmv_vds_a}"
    _vmv_target_vgs = lut.vgs_for_gm_id(15.0, 0.5e-6, _vmv_vds_a, 0.0)
    _vmv_vds_b = _vmv_ctx.sized["Mb"]["vds"]
    _vmv_vds_kb = _vmv_ctx.sized["Kb"]["vds"]
    assert abs(_vmv_vds_b - _vmv_target_vgs) < 1e-9, \
        f"Mb.vds({_vmv_vds_b})가 Ma의 VGS 역산값({_vmv_target_vgs})과 다름"
    assert abs(_vmv_vds_kb - (_vmv_vdd - _vmv_target_vgs)) < 1e-9, \
        f"Kb.vds({_vmv_vds_kb})가 vdd에서 Mb의 강제값을 뺀 나머지({_vmv_vdd - _vmv_target_vgs})와 다름"
    print(f"    PASS: Ma.vds={_vmv_vds_a:.4f}V(col_a 균등분배, Mb와 무관하게 독립적으로 먼저 확정) "
          f"-- Mb.vds={_vmv_vds_b:.4f}V(=Ma의 VGS 역산과 정확히 일치) -- "
          f"Kb.vds={_vmv_vds_kb:.4f}V(=vdd-Mb, 나머지 예산 정확히 흡수)")

    print("  [vds_match_vgs_of가 순환 참조하면 ValueError]")
    _vmv_cyc_topo = json.loads(json.dumps(_vmv_topo))
    _vmv_cyc_topo["device_roles"]["Ma"]["vds_match_vgs_of"] = "Mb"
    with _tempfile.TemporaryDirectory() as _vmv_cyc_tmp:
        _vmv_cyc_path = _os.path.join(_vmv_cyc_tmp, "_vmv_cyc.topology.json")
        with open(_vmv_cyc_path, "w", encoding="utf-8") as _f:
            json.dump(_vmv_cyc_topo, _f)
        try:
            _build_theta_evaluator(_vmv_cyc_path, _vmv_spec)["evaluate"]({})
            raise AssertionError("Ma<->Mb 순환 참조인데 에러가 안 났다")
        except ValueError as _vmv_cyc_e:
            assert "순환 참조" in str(_vmv_cyc_e), f"순환 참조 에러가 아님: {_vmv_cyc_e}"
            print(f"    PASS: ValueError -- {str(_vmv_cyc_e)[:70]}...")

    print()
    print("  [diagnose_sizing_roles_gap() -- device_role/symmetry의 propose_device_roles_"
          "gap_fill()과 대응하는 sizing_roles 쪽 진단 도구, 2026-08-15 세션35 신설]")
    # 2026-08-15 -- 사용자 지시("sizing role을 자동으로 넣는 것도 설계하고 통합하자")로
    # 신설. device_roles와 달리 sizing_roles의 theta bounds/constraints 목표값은 spec(설계
    # 목표)에서 오는 숫자라 connectivity만으로 지어낼 수 없다 -- 그래서 이 함수는 숫자를
    # 대신 채우지 않고, "sizing_roles=null 상태로 실제 완주 가능한가"를 실행 기반으로
    # 진단해 지금까지 optimize_full_circuit_budget() 깊은 곳에서 날것의 ValueError로만
    # 터지던 실패를 구조화된 gap 리포트로 바꾼다. 아래 5개 케이스는 전부 실제로 실행해
    # 확인한 결과(추측 없음, folded_cascode/nmcnr_amplifier는 실제 라이브러리 파일).
    _diag_lut = build_toy_lut()

    print("  [1. 정상 케이스 -- known_sizing으로 전류/L/VDS가 다 채워지면 status=ok]")
    _diag_ok_topo = {
        "schema_version": "2.0", "topology_name": "_diag_ok", "source": "self-test",
        "linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",
        "netlist": [{"name": "Mo", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "out"}],
        "symmetry": {"matching_pairs": [], "dispositions": []}, "sizing_roles": None,
        "device_roles": {"Mo": {"gm_id_role": "matching", "L_role": "mirror",
                                  "headroom_role": "mirror", "vs": 0.0}},
    }
    with _tempfile.TemporaryDirectory() as _diag_tmp:
        _diag_path = _os.path.join(_diag_tmp, "_diag_ok.topology.json")
        with open(_diag_path, "w", encoding="utf-8") as _f:
            json.dump(_diag_ok_topo, _f)
        _diag_spec_ok = {"lut_by_kind": {"nmos": _diag_lut}, "vdd": 1.8, "L_min": 0.5e-6,
                           "W_bounds": (1e-6, 50e-6), "min_vds_by_role": {"mirror": 0.2},
                           "known_sizing": {"Mo": {"ID": 1e-5, "L": 0.5e-6, "vds": 0.6, "vs": 0.0}}}
        _diag_r1 = diagnose_sizing_roles_gap(_diag_path, _diag_spec_ok)
        assert _diag_r1["status"] == "ok", f"known_sizing으로 다 채웠는데 ok가 아님: {_diag_r1}"
        print(f"    PASS: {_diag_r1}")

        print("  [2. ID는 있는데 L/VDS 미확정 -- kind=unresolved_vds_or_L]")
        _diag_spec_novds = dict(_diag_spec_ok, known_sizing={"Mo": {"ID": 1e-5}})
        _diag_r2 = diagnose_sizing_roles_gap(_diag_path, _diag_spec_novds)
        assert _diag_r2["status"] == "gap" and _diag_r2["kind"] == "unresolved_vds_or_L", \
            f"L/VDS 미확정 케이스인데 kind가 다름: {_diag_r2}"
        assert _diag_r2["device"] == "Mo"
        print(f"    PASS: {_diag_r2}")

        print("  [3. known_sizing 자체가 없으면 -- kind=unresolved_current]")
        _diag_r3 = diagnose_sizing_roles_gap(_diag_path,
                                               {k: v for k, v in _diag_spec_ok.items() if k != "known_sizing"})
        assert _diag_r3["status"] == "gap" and _diag_r3["kind"] == "unresolved_current", \
            f"seed 자체가 없는 케이스인데 kind가 다름: {_diag_r3}"
        assert _diag_r3["device"] == "Mo" and _diag_r3["ideal_source_hint"] is None, \
            "ideal_sources 선언이 아예 없는 회로인데 hint가 채워짐"
        print(f"    PASS: {_diag_r3}")

    print("  [4. 실제 라이브러리 파일 folded_cascode -- 세션35 안에서 이 gap 자체를 "
          "해소했다(Ibg를 KCL 유도+자유 theta로 배선) -- 이제 has_theta로 조기 반환됨을 "
          "재확인(회귀 감시: diagnose_sizing_roles_gap()이 '더 이상 gap이 아니다'를 "
          "정확히 인식하는지)]")
    _diag_fc_path = _os.path.join(_lib_dir_recipe, "folded_cascode.topology.json")
    _diag_r4 = diagnose_sizing_roles_gap(_diag_fc_path, {})
    assert _diag_r4["status"] == "has_theta", \
        f"folded_cascode는 세션35에서 Ibg를 free theta로 배선했으니 has_theta여야 하는데: {_diag_r4}"
    print(f"    PASS: {_diag_r4}")

    print("  [5/6. 실제 라이브러리 파일 nmcnr_amplifier -- 원래(세션35) PM_target_deg=46 "
          "(논문 실측치)이 nmcnr_3stage_topology()의 PM>60 전제와 충돌해 kind=other로 걸렸고, "
          "PM=70으로 그 가드를 우회해도 M101(바이어스 소자, 전류가 KCL만으로 안 나옴)에서 "
          "또 다른 unresolved_current gap이 드러났었다(당시 sizing_roles=null). 2026-08-18 "
          "세션이 그 M101 tail 전류/M104,M105 폴딩비를 sympy KCL 재유도 + 7개 theta로 실제로 "
          "배선했으므로(fold_group/vertical_stack_id 15개 소자 전부 확정 위, PM_target_deg는 "
          "아직 46인 채 -- 그건 여전히 별도 gap), 이제 folded_cascode/two_stage_ota와 동일하게 "
          "has_theta로 조기 반환되는지 재확인한다(회귀 감시)]")
    _diag_nm_path = _os.path.join(_lib_dir_recipe, "nmcnr_amplifier.topology.json")
    _diag_r56 = diagnose_sizing_roles_gap(_diag_nm_path, {})
    assert _diag_r56["status"] == "has_theta", \
        f"nmcnr_amplifier는 2026-08-18에 M101/M104/M105/M106/M107/M108 theta를 배선했으니 " \
        f"has_theta여야 하는데: {_diag_r56}"
    print(f"    PASS: {_diag_r56}")

    print("  [7. sizing_roles.theta가 이미 선언된 회로는 status=has_theta로 조기 반환]")
    _diag_tso_path = _os.path.join(_lib_dir_recipe, "two_stage_ota.topology.json")
    _diag_r7 = diagnose_sizing_roles_gap(_diag_tso_path, {})
    assert _diag_r7["status"] == "has_theta", f"two_stage_ota는 theta가 있는데: {_diag_r7}"
    print(f"    PASS: {_diag_r7}")

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
    _tso_real_path = _os.path.join(_lib_dir_recipe, "two_stage_ota.topology.json")
    # 2026-08-13(세션31 이어, L1~L4 4-DOF 확장 뒤) -- 실제 topology.json의 gain_db>=60은
    # 실제 sky130 LUT 기준 목표다(사용자와 문헌조사로 확정). 이 self-test는 toy LUT
    # (VA=5*L(um), gds가 실제 sky130보다 훨씬 낙관적으로 단순화됨)라 stage_gain_min을
    # 아무리 올려도(실측: 30~42dB 스윕) 46~58dB 근방에서 정체돼 60dB에 못 미친다(toy LUT
    # 자체 한계, "숫자를 설계에 쓰지 말 것" 원칙 그대로) -- 그래서 이 구조 검증 self-test
    # 전용으로 gain_db 문턱만 50dB(toy LUT가 안정적으로 넘기는 여유치)로 낮춘 임시 복사본을
    # 쓴다. 진짜 60dB 달성 여부는 실제 sky130 LUT로(다른 회로들처럼 workspaces/의 별도
    # harness에서) 검증할 것 -- 이 self-test의 목적은 "L1~L4 4-DOF 탐색 파이프라인이
    # AI 개입 없이 끝까지 완주하는가"이지 이 특정 spec(GBW=20MHz/CL=3pF/Z=10/NDP=4)이
    # 60dB를 실제로 달성하는지가 아니다.
    with open(_tso_real_path, encoding="utf-8") as _tso_f:
        _tso_topo_dict = json.load(_tso_f)
    for _tso_c in _tso_topo_dict["sizing_roles"]["constraints"]:
        if _tso_c["metric"] == "gain_db":
            _tso_c["value"] = 50.0
    _tso_path = _os.path.join(_tempfile.gettempdir(), "two_stage_ota_selftest.topology.json")
    with open(_tso_path, "w", encoding="utf-8") as _tso_f:
        json.dump(_tso_topo_dict, _tso_f)
    _tso_spec = {
        "lut_by_kind": {"nmos": lut, "pmos": lut},
        "vdd": 2.0,
        # 2026-08-13(세션31 이어, L_mirror_M3/L_mirror_M5 신설) -- metric_stage_budget
        # L타입 theta(순수 실수 L)는 layout grid quantization이 필요하다(run_harness.py의
        # current_reuse L_GRID_STEP=5nm과 동일 이유, sky130 tech LEF MANUFACTURINGGRID
        # 실측값) -- self-test는 toy LUT라 이 값 자체가 공정을 대표하진 않지만 메커니즘
        # 검증에는 임의의 5nm 격자로 충분하다.
        "L_grid_step": 0.005e-6,
        "GBW": 20e6, "CL": 3e-12, "Z": 10.0, "NDP": 4.0,
        # 2026-08-13(세션31 이어, two_stage_ota constraints 신설) -- topology.json에
        # gain_db>=60(전체회로) constraint를 추가하면서 발견: stage_devices(M1/M2,M6)의
        # L은 optimize_multistage()가 objective="power"로만 고르는데, gm이 compensation으로
        # 이미 고정된 상태에서는 전력이 L과 무관해(ID=gm/(gm/ID)) L이 사실상 "동점"이라
        # 격자 맨 앞(L_min=0.18um, VA=5*0.18=0.9V로 이득이 매우 작음)이 그냥 뽑혀 실측
        # gain_db=4.4dB(60dB에 한참 못 미침)로 infeasible이었다 -- optimize_multistage()
        # 자체엔 이걸 막을 gain_min 인자가 이미 있었는데(스칼라 또는 스테이지별 리스트,
        # docstring 821행대) 이 프로젝트 어디에서도 실제로 설정된 적이 없었다(harness 연동
        # 감사류로 처음 발견). ⚠️ find_optimal_sizing()의 "gain" 필드는 **선형** gm/gds
        # 비율이지 dB가 아니다(`_sizing_bundle()`의 `gm_gds = vals[1]/vals[2]`, dB 변환
        # 없음) -- 처음엔 이걸 dB로 착각해 30.0을 그대로 넣었었다(실측으로 발견: 실제
        # sky130 LUT에서 gm/gds=471.6 같은 값을 'dB'로 잘못 읽고 471dB라는 물리적으로
        # 불가능한 수치를 봤다가 정정). 목표 dB를 선형으로 변환(`10**(dB/20)`)해서 넣어야
        # 한다. stage_devices 순서(["M1","M2"],["M6"])에 맞춰 스테이지당 30dB씩(합 60dB,
        # 이 회로는 두 스테이지가 컴펜세이션 캡을 DC에서 무시하는 단순 직렬 캐스케이드라
        # 전체회로 smallsignal_gain_db가 두 스테이지 dB 합과 거의 같다) 최소치를 줘서 L
        # 탐색이 이득도 고려하도록 배선.
        "stage_gain_min": [10 ** (30.0 / 20), 10 ** (30.0 / 20)],
        "L_candidates": [float(v) for v in lut.L_grid],
        "VDS_candidates": [float(v) for v in lut.VDS_grid],
        "gm_id_grid": [i * 0.5 for i in range(4, 58)],
        "L_min": 0.18e-6,
        "W_bounds": (1e-6, 200e-6),
        # 2026-08-13 -- stage_gain_min 신설과 함께 200um->500um로 확대. 이유(toy LUT
        # 전용 한계, 실측): w_max=200um에서는 stage1 L이 커지며(Cgg 증가) Miller Cm
        # 재계산으로 gm1이 반복마다 커지고 gm2=Z*gm1(Z=10)도 같이 커져 2번째 반복에서
        # stage2가 200um 안에 못 들어가 INFEASIBLE(diag 스크립트로 확인) -- 500um에서는
        # 4회 반복 만에 total=62dB로 깨끗이 수렴(회로 자체의 물리적 한계가 아니라 toy LUT
        # 데모용 예산이 너무 빠듯했던 것, sky130-worked-example.md가 이미 경고한 대로
        # "toy LUT 숫자 자체를 설계에 쓰지 말 것" 원칙 그대로 -- 실제 sky130 LUT는 훨씬
        # 적은 예산(200um)으로도 60dB를 넘긴다, run_harness.py류 실제 하네스에서 확인).
        "stage_w_max": 500e-6,
        "min_vds_by_role": {"cascode": 0.2, "tail": 0.2},
        "min_finger_w": 0.1e-6, "max_finger_w": 40e-6,
        # 2026-08-13(세션31 이어, two_stage_ota constraints 신설) -- sizing_roles.metrics에
        # mismatch_sigma_mV(pelgrom_mismatch, kind=nfet)를 추가하면서 필요해짐. run_harness.py
        # (current_reuse_telescopic_ota)가 이미 쓰는 sky130 PDK mismatch 상수 그대로 재사용
        # (self-test는 toy LUT라 실제 sky130 값과 무관하지만, 상수 자체는 sky130 실측값).
        "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
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
        # 2026-08-13(세션31 CH->CJ) -- CH에서 topology.json의 L_mirror_M5를 L_M5/L_M7(독립
        # theta)로 한 번 분리했다가, GBW=20MHz->7MHz(무릎 지점) 레버가 gain_db를 훨씬 크게
        # 개선한 뒤 M5/M7 분리가 주는 +1dB가 4배 늘어난 folding 비용에 안 맞는다고 판단해
        # 사용자 지시로 공유 theta(L_mirror_M5, devices=[M5,M7])로 원복 -- stack_groups_
        # override도 다시 M5+M7 한 행으로.
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
    # 2026-08-05(세션10) -- audit_ok 하드게이트를 뺐다. 격리 스크립트로 확인(diag_m5.py, 세션10):
    # M5(1단 tail)의 전류를 옛 버그(축A 규칙1이 gnd를 레일 제외 없이 2단자로 오판해 M5=M7로
    # 잘못 병합, 173.9uA)로 두면 이 감사가 우연히 PASS했다 -- 올바른 KCL 합(ID(M5)=ID(M1)+
    # ID(M2)=30.1uA, kcl_tail_M5 theta 신설로 이번 세션 정정)으로 고치니 M5의 W가 훨씬
    # 작아져(1.46um->1.12um) M6(199.81um)과의 크기 격차가 커지고 box-shape 비율이 1.5를
    # 넘는다 -- repair_matching_safety()도 못 고친다(M3/M4 common-centroid dx=1.00). 이건
    # L1/L2(matching_pairs 축 분해/그룹핑 규칙) 범위 밖의 별개 문제로, context.md가 이미
    # "L4(사이징->레이아웃 연결) 미설계"로 기록해둔 정직한 한계다(assign_finger_geometry()가
    # 스테이지 간 극단적 W 격차를 아직 모른다) -- 여기서 억지로 고치지 않고 정보로만 출력한다.
    print(f"    참고(정직한 한계, L4 미설계): audit_ok={_tso_result['audit_ok']} -- "
          f"M6(2단, W={_tso_result['sizing']['M6']['W']*1e6:.1f}um)과 M3/M5(tail/cascode, "
          f"W~{_tso_result['sizing']['M5']['W']*1e6:.1f}um)의 W 격차가 box-shape 비율(<=1.5)을 "
          f"넘어 repair로도 못 고침 -- L4(사이징->레이아웃 연결) 설계 시 재검토할 것")
    print("    PASS: spec -> load_topology -> derive_stack_groups -> A엔진 -> compensation "
          "-> device_roles(L/헤드룸/gm_id) -> assign_finger_geometry -> run_topology_pipeline "
          "까지 AI 개입 없이 단일 함수 호출로 완주(matching-safety audit 자체는 L4 미해결로 "
          "정보성 출력에 그침)")

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
        "symmetry": {"matching_pairs": [{"names": ["Ma", "Mb"], "current_forced": False, "matching_sensitivity": "ratio"}],
                      "dispositions": []},
        "compensation": {"function": "miller_ota_topology",
                          "parameters": ["GBW", "CL", "Z", "NDP"],
                          "stage_devices": [["Ma"], ["Mc"]]},
        # 2026-08-14 세션34 -- gm_id_role을 명시적으로 False로 선언(원래 None) -- Mb(레일
        # 소스+HIGH_Z 드레인, 파트너 없는 고립 소자)가 propose_device_roles_gap_fill()의 새
        # 4번째 소스("gm_id_role=gain" 제안) 대상이 됐다. 이 테스트는 Mb의 matching_pairs를
        # 일부러 current_forced=False로 둬(L_role 재설계만 검증하려는 의도) Mb의 ID를 A엔진이
        # 절대 못 정하게 설계돼 있다 -- 어떤 값이든 gm_id_role이 채워지면(심지어 declared로
        # 직접 줘도) sizing_recipe.py의 gm_id_role 루프가 "ID 없음"으로 즉시 ValueError를
        # 낸다(이 fixture 고유의 제약, 버그 아님). False는 None과 달리 "이미 명시적으로
        # 결정됨(해당없음)"으로 인식돼 gain 제안과 충돌 처리(자동 병합 안 됨 -> review 불필요)
        # 되면서도, falsy라 gm_id_role 루프 자체는 여전히 건너뛴다(None과 동일 동작).
        "device_roles": {"Mb": {"headroom_role": None, "gm_id_role": False,
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
    _lrec_topo2["symmetry"] = {"matching_pairs": [{"names": ["Md", "Me"], "current_forced": False, "matching_sensitivity": "ratio"}],
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
        spec={"lut_by_kind": {"nmos": _lut_with_noise}, "freq": _freq_test, "temperature_K": 300.0},
        sized={"M1": {"gm": 200e-6, "gm_id": 15.0, "L": 0.5e-6, "W": _w_target_test,
                       "vds": 0.6, "vs": 0.0}},
        kind_of={"M1": "nmos"})
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
    print("  [세션37: nmcnr_gain_db/nmcnr_pm_deg -- nmcnr_amplifier.topology.json 실제")
    print("  connectivity가 metric_spec 소자 역할 배정과 일치하는지 먼저 확인]")
    _nmcnr_topo_path = _os.path.join(_lib_dir_recipe, "nmcnr_amplifier.topology.json")
    _nmcnr_transistors, _ = load_topology(_nmcnr_topo_path)
    _nmcnr_by_name = {t.name: t for t in _nmcnr_transistors}
    # stage1 출력(NodeM2)에 M107(캐스코드)/M109(단순 미러) 둘 다 실제로 물려 있는지
    assert _nmcnr_by_name["M107"].drain == _nmcnr_by_name["M109"].drain == "NodeM2", \
        "M107/M109가 실제로 NodeM2에서 만나지 않음 -- stage1 R1 유도의 합류 전제가 깨짐"
    assert _nmcnr_by_name["M107"].source == "NodeF2", "M107.source != NodeF2"
    assert _nmcnr_by_name["M103"].drain == _nmcnr_by_name["M105"].drain == "NodeF2", \
        "M103/M105가 실제로 NodeF2(M107의 폴딩 소스 노드)에서 만나지 않음"
    # stage1 출력이 실제로 gm2 소자(M201)의 게이트로 들어가는지
    assert _nmcnr_by_name["M201"].gate == "NodeM2", "M201.gate != NodeM2 -- gm1->gm2 전달 경로가 아님"
    # stage2 출력(NodeS2)에 M202/M204 둘 다 물려 있고, gm3 소자(M301)의 게이트로 들어가는지
    assert _nmcnr_by_name["M202"].drain == _nmcnr_by_name["M204"].drain == "NodeS2", \
        "M202/M204가 실제로 NodeS2에서 만나지 않음 -- stage2 R2 유도의 합류 전제가 깨짐"
    assert _nmcnr_by_name["M301"].gate == "NodeS2", "M301.gate != NodeS2 -- gm2->gm3 전달 경로가 아님"
    # stage3 출력(Vout)에 M301/M302 둘 다 물려 있는지
    assert _nmcnr_by_name["M301"].drain == _nmcnr_by_name["M302"].drain == "Vout", \
        "M301/M302가 실제로 Vout에서 만나지 않음 -- stage3 R3 유도의 합류 전제가 깨짐"
    print("    PASS: M107/M109->NodeM2->M201.gate, M202/M204->NodeS2->M301.gate, "
          "M301/M302->Vout 전부 실제 connectivity와 일치")

    print("  [_nmcnr_stage1_rout()/_metric_nmcnr_gain_db/_metric_nmcnr_pm_deg -- 손계산과 대조]")
    _nmcnr_spec = {
        "gm1_device": "M102", "gm2_device": "M201", "gm3_device": "M301",
        "stage1_cascode_n": "M107", "stage1_fold_leg_a": "M103", "stage1_fold_leg_b": "M105",
        "stage1_mirror_p": "M109", "stage2_devices": ["M202", "M204"],
        "stage3_devices": ["M301", "M302"], "CL": 1e-10, "kg": 0.5,
    }
    _nmcnr_sized = {
        "M102": {"gm": 1e-3, "gds": 1e-8},
        "M103": {"gm": 1e-3, "gds": 2e-6}, "M105": {"gm": 1e-3, "gds": 2e-6},
        "M107": {"gm": 2e-3, "gds": 1e-6}, "M109": {"gm": 1e-3, "gds": 5e-6},
        "M201": {"gm": 0.2e-3, "gds": 1e-8},
        "M202": {"gm": 1e-3, "gds": 4e-6}, "M204": {"gm": 1e-3, "gds": 4e-6},
        "M301": {"gm": 0.5e-3, "gds": 3e-6}, "M302": {"gm": 1e-3, "gds": 3e-6},
    }
    _nmcnr_ctx = SizingContext(sized=_nmcnr_sized)
    # 손계산: R1(비대칭 -- M107만 캐스코드, M109는 단순 미러)
    _ro103, _ro105, _ro107, _ro109 = 1/2e-6, 1/2e-6, 1/1e-6, 1/5e-6
    _ro_fold_expected = 1.0 / (1.0/_ro103 + 1.0/_ro105)
    _rout_n_expected = 2e-3 * _ro107 * _ro_fold_expected
    _R1_expected = 1.0 / (1.0/_rout_n_expected + 1.0/_ro109)
    _R1_actual = _nmcnr_stage1_rout(_nmcnr_spec, _nmcnr_ctx)
    assert abs(_R1_actual - _R1_expected) / _R1_expected < 1e-9
    _R2_expected = 1.0 / (1.0/(1/4e-6) + 1.0/(1/4e-6))
    _R3_expected = 1.0 / (1.0/(1/3e-6) + 1.0/(1/3e-6))
    _nmcnr_expected = nmcnr_predict_ac_response(1e-3, 0.2e-3, 0.5e-3, _R1_expected, _R2_expected,
                                           _R3_expected, CL=1e-10, kg=0.5)
    _nmcnr_gain_actual = compute_metric({"type": "nmcnr_gain_db", **_nmcnr_spec}, _nmcnr_ctx)
    _nmcnr_pm_actual = compute_metric({"type": "nmcnr_pm_deg", **_nmcnr_spec}, _nmcnr_ctx)
    assert abs(_nmcnr_gain_actual - _nmcnr_expected["dc_gain_db"]) < 1e-9
    assert abs(_nmcnr_pm_actual - _nmcnr_expected["crossings"][0][1]) < 1e-9
    print(f"    PASS: R1={_R1_actual:.3e}ohm(손계산과 일치), gain_db={_nmcnr_gain_actual:.2f}dB, "
          f"pm_deg={_nmcnr_pm_actual:.2f}deg -- 전부 nmcnr_predict_ac_response() 직접호출과 일치")
    print("    (같은 spec/ctx로 gain_db/pm_deg 재호출 시 _nmcnr_predict_cache 재사용됨 -- "
          "_open_loop_gains_cache와 동일 관례)")

    print("  [_metric_nmcnr_pm_deg -- 0dB 교차가 아예 없으면(gm1이 극단적으로 작아 DC이득이 "
          "이미 0dB 미만) ValueError]")
    _nmcnr_sized_low_gain = dict(_nmcnr_sized)
    _nmcnr_sized_low_gain["M102"] = {"gm": 1e-9, "gds": 1e-8}
    _nmcnr_ctx_low = SizingContext(sized=_nmcnr_sized_low_gain)
    try:
        compute_metric({"type": "nmcnr_pm_deg", **_nmcnr_spec}, _nmcnr_ctx_low)
        raise AssertionError("0dB 교차가 없어야 하는데 에러가 안 났다")
    except ValueError as _e_nocross:
        print(f"    PASS: ValueError -- {str(_e_nocross)[:70]}...")

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
    # ---- 위상 가정 검증(2026-08-03 전면 정정) --------------------------------------
    # 옛 assert는 `M2a.drain == M3a.source`, 즉 "PMOS 캐스코드의 드레인이 NMOS 캐스코드의
    # 소스로 이어지는 **하나의 직렬 텔레스코픽 기둥**"을 가정했다. 확정된 topology.json은
    # 그렇지 않다 -- 이 회로는 current-reuse라서 PMOS 가지(M1a→M2a, tail=Vx)와 NMOS 가지
    # (M4a→M3a, tail=Vy)가 **각각 독립**이고 출력노드에서 **드레인끼리** 만난다.
    # CMRR 폐형식(_cmrr_telescopic_class_ab docstring)이 실제로 전제하는 것은 다음 4가지다.
    # (1) 각 가지가 '입력쌍 drain == 캐스코드 source'인 직렬 캐스코드일 것 (Kp'/Kn' 성립)
    assert _crt_by_name["M1a"].drain == _crt_by_name["M2a"].source, \
        "M1a/M2a가 PMOS 직렬 캐스코드가 아님(M1a.drain != M2a.source) -- Kp' 전제가 깨짐"
    assert _crt_by_name["M4a"].drain == _crt_by_name["M3a"].source, \
        "M4a/M3a가 NMOS 직렬 캐스코드가 아님(M4a.drain != M3a.source) -- Kn' 전제가 깨짐"
    # (2) 두 가지가 같은 출력노드에서 **드레인끼리** 만날 것 (Kp'∥Kn', Acm의 병렬 합류)
    _crt_vom1 = _crt_by_name["M2a"].drain
    _crt_vop1 = _crt_by_name["M2b"].drain
    assert _crt_by_name["M3a"].drain == _crt_vom1, \
        "M2a/M3a가 같은 출력노드에서 드레인끼리 만나지 않음 -- CMRR 공식의 합류 전제가 깨짐"
    assert _crt_by_name["M3b"].drain == _crt_vop1 and _crt_vom1 != _crt_vop1, \
        "b측(M2b/M3b)이 a측과 대칭인 별도 출력노드를 이루지 않음"
    # (3) 옛 직렬 기둥 가정이 **아님**을 명시적으로 고정(회귀 방지)
    assert _crt_by_name["M2a"].drain != _crt_by_name["M3a"].source, \
        "M2a.drain == M3a.source -- 옛(직렬 캐스코드) 위상이다. 이 JSON/공식과 맞지 않음"
    # (4) 두 가지가 **서로 다른** tail을 가질 것(Vx=M6∥M7, Vy=M5) -- Rx/Ry가 별개인 전제
    assert _crt_by_name["M6"].drain == _crt_by_name["M7"].drain == _crt_by_name["M1a"].source, \
        "M6/M7/M1a가 같은 Vx(tail) 노드를 공유하지 않음"
    assert _crt_by_name["M1a"].source == _crt_by_name["M1b"].source, "M1a/M1b가 tail Vx를 공유 안 함"
    assert _crt_by_name["M4a"].source == _crt_by_name["M5"].drain, \
        "M4a/M5가 같은 Vy(tail) 노드를 공유하지 않음"
    assert _crt_by_name["M4a"].source == _crt_by_name["M4b"].source, "M4a/M4b가 tail Vy를 공유 안 함"
    assert _crt_by_name["M1a"].source != _crt_by_name["M4a"].source, \
        "Vx와 Vy가 같은 노드다 -- tail이 둘로 분리돼 있다는 Rx/Ry 전제가 깨짐"
    # (5) 두 입력쌍이 같은 입력을 공유할 것(current-reuse의 정의: M1a/M4a 게이트가 둘 다 Vip)
    assert _crt_by_name["M1a"].gate == _crt_by_name["M4a"].gate, \
        "M1a/M4a가 같은 입력(Vip)을 공유하지 않음 -- (gmp+gmn) 합산 전제가 깨짐"
    assert _crt_by_name["M1b"].gate == _crt_by_name["M4b"].gate != _crt_by_name["M1a"].gate, \
        "M1b/M4b가 같은 반대편 입력(Vim)을 공유하지 않음"
    print(f"    PASS: kind 일치(M1a/M2a/M6/M7=pmos, M3a/M4a/M5=nmos). 위상: PMOS 가지"
          f"(M1a.drain={_crt_by_name['M1a'].drain!r}=M2a.source) + NMOS 가지"
          f"(M4a.drain={_crt_by_name['M4a'].drain!r}=M3a.source)가 출력노드 {_crt_vom1!r}에서"
          f" **드레인끼리** 합류(직렬 기둥 아님), tail 분리(Vx={_crt_by_name['M1a'].source!r},"
          f" Vy={_crt_by_name['M4a'].source!r}), 입력 공유({_crt_by_name['M1a'].gate!r})"
          f" -- 실제 JSON connectivity로 검증됨")

    print()
    print("  [cmrr_estimate -- telescopic_class_ab family(2026-08-03 확정 topology.json으로")
    print("  재유도) -- 이상화 소신호 netlist(VCCS+R만, ngspice AC) + sympy 정확해와 대조.")
    print("  재현 스크립트: workspaces/current-reuse-telescopic-ota-report/spice/")
    print("  stage1_cmrr_sympy_derivation.py, stage1_cmrr_ngspice_crosscheck.py.")
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
    # 앵커3(2026-08-03 신설): 위 두 앵커는 모든 gm을 119uS로 같게 놓아서 "Kp'에 캐스코드 gm을
    # 쓰느냐 입력쌍 gm을 쓰느냐"의 차이가 **원리적으로 드러나지 않는다**(정확히 그래서 옛 식의
    # 오류가 오래 숨어 있었다). 캐스코드 gm과 입력쌍 gm의 비를 크게 어긋나게 잡은 점을 추가해
    # 회귀로 고정한다 -- ngspice 실측 0.0635dB, 새 식 0.0000dB(오차 0.06dB),
    # 옛(입력쌍 gm) 식 7.0437dB(오차 6.98dB)로 두 식이 명확히 갈린다.
    _crt_cmrr_ctx3 = SizingContext(sized={
        "M1a": {"gm": 100e-6, "gds": 1.0 / 500e3},   # PMOS 입력쌍
        "M2a": {"gm": 400e-6, "gds": 1.0 / 500e3},   # PMOS 캐스코드(입력쌍 gm의 4배)
        "M4a": {"gm": 200e-6, "gds": 1.0 / 1000e3},  # NMOS 입력쌍
        "M3a": {"gm": 50e-6, "gds": 1.0 / 1000e3},   # NMOS 캐스코드(입력쌍 gm의 1/4)
        "M6": {"gm": 0.0, "gds": 0.5e-6}, "M7": {"gm": 0.0, "gds": 0.5e-6},  # Rx=1e6
        "M5": {"gm": 0.0, "gds": 0.2e-6},             # Ry=5e6
    })
    _crt_cmrr_db3 = compute_metric(_crt_cmrr_spec, _crt_cmrr_ctx3)
    assert abs(_crt_cmrr_db3 - 0.0635) < 0.2, \
        f"앵커3(SPICE 0.0635dB)과 어긋남: {_crt_cmrr_db3} -- Kp'/Kn'에 캐스코드 gm 대신 " \
        f"입력쌍 gm을 쓰면 여기서 7.04dB가 나온다(2026-08-03 정정된 옛 버그의 회귀)"
    print(f"    PASS(앵커3, 캐스코드 gm != 입력쌍 gm): CMRR={_crt_cmrr_db3:.4f}dB "
          f"(SPICE 실측 0.0635dB / 옛 입력쌍-gm 식이면 7.044dB -- 두 식이 갈리는 점)")

    print()
    print("  [cmrr_estimate -- telescopic_class_ab_cmfb family(2026-08-03 신규 유도, CMFB 루프")
    print("  포함): 먼저 metric_spec의 CMFB 소자 역할 배정이 topology.json netlist와 실제로")
    print("  일치하는지 load_topology()로 확인 -- 손 배정을 그대로 믿지 않는다]")
    _cmfb_roles = {"cmfb_ctrl_device": "M7", "cmfb_amp_sense": "M37a", "cmfb_amp_ref": "M37b",
                    "cmfb_load_sense": "M36a", "cmfb_load_ref": "M36b",
                    "cmfb_tail_device": "M38", "cmfb_stage2_devices": ["M15", "M16"]}
    # (1) M7이 정말 'gate=Vcmfb인 PMOS tail 전류원'이고, 그 Vcmfb는 M36a **자신의 diode 노드**다
    #     (2026-08-03 정정: 이전엔 M36b가 미러로 Vcmfb를 만든다고 봤으나 오독이었다).
    _vcmfb_net = _crt_by_name["M7"].gate
    assert _crt_by_name["M7"].kind == "pmos" and _crt_by_name["M7"].drain == _crt_by_name["M1a"].source, \
        "cmfb_ctrl_device(M7)가 Vx(stage-1 PMOS tail) 노드를 구동하지 않음"
    assert (_crt_by_name["M36a"].gate == _crt_by_name["M36a"].drain == _vcmfb_net
            and _crt_by_name["M36a"].source == "vdd" and _crt_by_name["M36a"].kind == "pmos"), \
        "M36a가 'vdd에 source를 둔 diode이고 그 diode 노드가 곧 Vcmfb(M7.gate)'가 아님"
    assert _crt_by_name["M37a"].drain == _vcmfb_net, \
        "M37a(gate=Voc)의 drain이 Vcmfb가 아님 -- 감지쪽 다리에서 출력을 뽑는다는 전제가 깨짐"
    # (2) M36b는 M36a의 미러가 아니라 **완전히 독립된 자기 자신의 diode**(게이트가 안 묶인다).
    assert _crt_by_name["M36b"].gate == _crt_by_name["M36b"].drain != _vcmfb_net, \
        "M36b가 자기 자신의 독립 diode가 아님"
    assert _crt_by_name["M36a"].gate != _crt_by_name["M36b"].gate, \
        "M36a/M36b의 게이트가 묶여 있다 -- 이건 폐기된 'current mirror 부하' 오독이다"
    assert _crt_by_name["M36b"].drain == _crt_by_name["M37b"].drain, "M36b/M37b가 같은 노드가 아님"
    # (3) M37a/M37b는 tail(M38)을 공유하는 차동쌍.
    assert _crt_by_name["M37a"].source == _crt_by_name["M37b"].source == _crt_by_name["M38"].drain, \
        "M37a/M37b/M38이 같은 CMFB tail 노드를 공유하지 않음"
    # (4) Voc_des(M37b의 기준입력)는 M39/M40 **PMOS diode 2개짜리 저임피던스 분압기**의 중간노드다:
    #     M39(source=vdd, gate=drain=Voc_des), M40(source=Voc_des, gate=drain=gnd). 이 구조라야
    #     소신호로 v(Voc_des)=0이 되고, M39/M40이 A_c 식에서 사라진다(유도의 핵심 전제).
    _vocdes_net = _crt_by_name["M37b"].gate
    assert (_crt_by_name["M39"].kind == "pmos" and _crt_by_name["M39"].source == "vdd"
            and _crt_by_name["M39"].gate == _crt_by_name["M39"].drain == _vocdes_net), \
        "M39가 'vdd->Voc_des PMOS diode'가 아님"
    assert (_crt_by_name["M40"].kind == "pmos" and _crt_by_name["M40"].source == _vocdes_net
            and _crt_by_name["M40"].gate == _crt_by_name["M40"].drain == "gnd"), \
        "M40이 'Voc_des->gnd PMOS diode'가 아님 -- v(Voc_des)=0 전제가 깨져 A_c 유도가 무효"
    assert not any(t.drain == _vocdes_net or t.source == _vocdes_net
                   for t in _crt_transistors if t.name not in ("M39", "M40")), \
        "Voc_des에 M39/M40 말고 다른 구동소자가 생겼다 -- v(Voc_des)=0 전제 재검토 필요"
    # (5) Voc(M37a의 게이트)를 구동하는 트랜지스터는 없다 -- 논문 Fig.5의 R1/R2 저항 평균망은
    #     트랜지스터가 아니라 이 스키마(kind: pmos/nmos)에 못 들어가기 때문이다. 그 사실 자체를
    #     회귀로 고정하고, R1/R2가 감지하는 대상(최종출력 CM)은 cmfb_stage2_devices로 표현한다.
    _voc_net = _crt_by_name["M37a"].gate
    assert not any(t.drain == _voc_net or t.source == _voc_net for t in _crt_transistors), \
        f"{_voc_net!r}를 구동하는 소자가 생겼다 -- R1/R2 감지망 모델링(cm_sense_gain)을 재검토할 것"
    assert all(_crt_by_name[d].drain == _crt_by_name["M15"].drain
               for d in _cmfb_roles["cmfb_stage2_devices"]), \
        "cmfb_stage2_devices가 같은 2단 출력노드(Vom)를 구동하지 않음"
    print(f"    PASS: CMFB 연결 확인(Vcmfb={_vcmfb_net!r} = M36a 자기 diode = M37a.drain, "
          f"M36b는 독립 diode({_crt_by_name['M36b'].drain!r}), Voc_des={_vocdes_net!r} = "
          f"M39/M40 PMOS diode 분압기, tail={_crt_by_name['M38'].drain!r}), "
          f"Voc={_voc_net!r}는 R1/R2(트랜지스터 아님)가 구동")

    print()
    print("  [cmrr/psrr_estimate -- telescopic_class_ab_cmfb family(2026-08-07 세션21 전면")
    print("  교체) -- Kp'/Kn'/Rx/Ry 폐형식 대신 31소자(1단11+양쪽 Monticelli battery 10+10)")
    print("  수치 MNA(_telescopic_class_ab_open_loop_gains()). 폐형식이 M10/M19(Vop1/Vom1")
    print("  직결 바이어스 싱크) 로딩을 몰라 실제값과 최대 49dB 어긋난다는 게 세션21에 드러나")
    print("  전면 교체됨 -- 상세 근거는 sizing_recipe.py _cmrr_telescopic_class_ab_cmfb()")
    print("  docstring, `.ai/context.md` 세션21 절 참고. ⚠️ 이 self-test의 앵커는 아직")
    print("  ngspice AC 독립 재검증 전(다음 세션 과제) -- 현재는 **자기회귀**(같은 함수를")
    print("  두 다른 경로(직접 조합 vs compute_metric 경유)로 계산해 일치하는지)만 확인한다.]")
    _battery_vop1 = {"vdd_src": "M8", "batt_hi": "M9a", "batt_lo": "M9b",
                       "gate_diode1": "M11a", "gate_diode2": "M11b",
                       "gate_sink": "M12", "output_sink": "M10",
                       "gate2_src": "M13", "gate2_diode1": "M14a", "gate2_diode2": "M14b"}
    _battery_vom1 = {"vdd_src": "M17", "batt_hi": "M18a", "batt_lo": "M18b",
                       "gate_diode1": "M20a", "gate_diode2": "M20b",
                       "gate_sink": "M21", "output_sink": "M19",
                       "gate2_src": "M22", "gate2_diode1": "M23a", "gate2_diode2": "M24b"}
    _cmfb_ctx = SizingContext(sized={
        "M1a": {"gm": 119e-6, "gds": 1 / 600e3}, "M1b": {"gm": 119e-6, "gds": 1 / 600e3},
        "M2a": {"gm": 130e-6, "gds": 1 / 700e3}, "M2b": {"gm": 130e-6, "gds": 1 / 700e3},
        "M4a": {"gm": 140e-6, "gds": 1 / 250e3}, "M4b": {"gm": 140e-6, "gds": 1 / 250e3},
        "M3a": {"gm": 150e-6, "gds": 1 / 300e3}, "M3b": {"gm": 150e-6, "gds": 1 / 300e3},
        "M6": {"gm": 0.0, "gds": 0.5e-6}, "M7": {"gm": 90e-6, "gds": 0.4e-6},
        "M5": {"gm": 0.0, "gds": 1.0e-6},
        "M8": {"gm": 40e-6, "gds": 0.3e-6}, "M17": {"gm": 40e-6, "gds": 0.3e-6},
        "M9a": {"gm": 50e-6, "gds": 0.4e-6}, "M9b": {"gm": 50e-6, "gds": 0.4e-6},
        "M18a": {"gm": 50e-6, "gds": 0.4e-6}, "M18b": {"gm": 50e-6, "gds": 0.4e-6},
        "M11a": {"gm": 30e-6, "gds": 0.5e-6}, "M11b": {"gm": 30e-6, "gds": 0.5e-6},
        "M20a": {"gm": 30e-6, "gds": 0.5e-6}, "M20b": {"gm": 30e-6, "gds": 0.5e-6},
        "M12": {"gm": 0.0, "gds": 0.6e-6}, "M21": {"gm": 0.0, "gds": 0.6e-6},
        "M10": {"gm": 0.0, "gds": 0.6e-6}, "M19": {"gm": 0.0, "gds": 0.6e-6},
        "M13": {"gm": 40e-6, "gds": 0.3e-6}, "M22": {"gm": 40e-6, "gds": 0.3e-6},
        "M14a": {"gm": 30e-6, "gds": 0.5e-6}, "M14b": {"gm": 30e-6, "gds": 0.5e-6},
        "M23a": {"gm": 30e-6, "gds": 0.5e-6}, "M24b": {"gm": 30e-6, "gds": 0.5e-6},
        "M15": {"gm": 3.0e-3, "gds": 8e-6}, "M16": {"gm": 3.0e-3, "gds": 9e-6},
        "M37a": {"gm": 100e-6, "gds": 1.0e-6}, "M37b": {"gm": 105e-6, "gds": 1.1e-6},
        "M36a": {"gm": 80e-6, "gds": 0.8e-6}, "M36b": {"gm": 84e-6, "gds": 0.9e-6},
        "M38": {"gm": 0.0, "gds": 1.2e-6},
    })
    _cmfb_spec = {"type": "cmrr_estimate", "circuit_family": "telescopic_class_ab_cmfb",
                   "input_p": "M1a", "input_p_b": "M1b", "cascode_p": "M2a", "cascode_p_b": "M2b",
                   "input_n": "M4a", "input_n_b": "M4b", "cascode_n": "M3a", "cascode_n_b": "M3b",
                   "tail_p_devices": ["M6", "M7"], "tail_n_device": "M5",
                   "battery_vop1_side": _battery_vop1, "battery_vom1_side": _battery_vom1,
                   **_cmfb_roles}
    # A_c는 다이오드 부하 차동쌍이므로 leading order -gm37/(2*gm36) 근방의 O(1) 음수여야 한다
    # (M10/M19 로딩과 무관한 별개 서브회로라 이 값/앵커는 세션20에서 그대로 유효).
    _cmfb_ac = _cmfb_amp_gain_diode_load(_cmfb_spec, _cmfb_ctx)
    assert -1.0 < _cmfb_ac < 0.0, f"A_c가 O(1) 음수가 아님: {_cmfb_ac}"
    assert abs(_cmfb_ac - (-0.62960331)) < 1e-6, f"A_c 회귀(sympy 정확해 대조): {_cmfb_ac}"
    print(f"    PASS: A_c={_cmfb_ac:.6f} (M10/M19와 무관, 세션20 sympy 정확해 그대로)")

    _cmfb_db1 = compute_metric(_cmfb_spec, _cmfb_ctx)
    # 자기회귀 -- _telescopic_class_ab_open_loop_gains()를 직접 호출해 조합한 값과 일치하는지.
    _adm_o, _acm_o, _ann_o, _h_o = _telescopic_class_ab_open_loop_gains(_cmfb_spec, _cmfb_ctx)
    _s2 = [_cmfb_ctx.sized[d] for d in _cmfb_spec["cmfb_stage2_devices"]]
    _g2 = -sum(d["gm"] for d in _s2) / sum(d["gds"] for d in _s2)
    _t = -_h_o * _cmfb_ac * _g2
    _cmrr_direct = 20 * math.log10(abs(_adm_o / _acm_o) * (1.0 + _t))
    assert abs(_cmfb_db1 - _cmrr_direct) < 1e-9, "compute_metric() 경유값과 직접조합값이 어긋남"
    assert abs(_cmfb_db1 - 128.7182) < 0.01, f"CMRR 회귀(세션21 신규 앵커)와 어긋남: {_cmfb_db1}"
    print(f"    PASS(자기회귀): CMRR={_cmfb_db1:.4f}dB (Adm_open={_adm_o:.4g}, "
          f"Acm_open={_acm_o:.4g}, H={_h_o:.4g}, T={_t:.4g} -- ngspice 독립검증은 다음 세션)")
    # 앵커2: Ry를 20배(gds5 x0.05), gm7을 4배 -- CMFB 루프이득이 더 커지는 방향인지(부호 확인).
    _cmfb_ctx.sized["M5"]["gds"] = 1.0e-6 * 0.05
    _cmfb_ctx.sized["M7"]["gm"] = 90e-6 * 4
    _cmfb_db2 = compute_metric(_cmfb_spec, _cmfb_ctx)
    assert abs(_cmfb_db2 - 146.7202) < 0.01, f"CMRR 앵커2(세션21 신규) 회귀와 어긋남: {_cmfb_db2}"
    assert _cmfb_db2 > _cmfb_db1, "Ry x20/gm7 x4가 CMRR을 개선하는 방향이어야 하는데 안 됨(회귀)"
    print(f"    PASS(앵커2, Ry x20/gm7 x4): CMRR={_cmfb_db2:.4f}dB "
          f"({_cmfb_db2 - _cmfb_db1:+.2f}dB, 개선 방향 확인)")
    # T<=0(CM 양귀환)이면 계산을 거부하는지 -- 2단 부호를 뒤집어(cm_sense_gain<0) 확인한다.
    try:
        compute_metric({**_cmfb_spec, "cm_sense_gain": -1.0}, _cmfb_ctx)
        raise AssertionError("T<=0(CM 양귀환)인데 에러가 안 났다")
    except ValueError as _e_ac:
        print(f"    PASS: T<=0 거부 -- {str(_e_ac)[:60]}...")
    _cmfb_ctx.sized["M5"]["gds"] = 1.0e-6
    _cmfb_ctx.sized["M7"]["gm"] = 90e-6

    print()
    print("  [psrr_estimate -- telescopic_class_ab_cmfb family, 같은 31소자망 -- Ann_open이")
    print("  M8/M17(battery의 자체 vdd 주입)/M10/M19(로딩) 전부 반영하는지 자기회귀로 확인]")
    _psrr_cmfb_spec = {**_cmfb_spec, "type": "psrr_estimate"}
    _psrr_cmfb_db1 = compute_metric(_psrr_cmfb_spec, _cmfb_ctx)
    _psrr_direct = 20 * math.log10(abs(_adm_o / _ann_o)) + 20 * math.log10(abs(1.0 + _t))
    assert abs(_psrr_cmfb_db1 - 89.3832) < 0.01, f"PSRR 회귀(세션21 신규 앵커)와 어긋남: {_psrr_cmfb_db1}"
    print(f"    PASS(자기회귀): PSRR={_psrr_cmfb_db1:.4f}dB (Ann_open={_ann_o:.4g}, "
          f"ngspice 독립검증은 다음 세션)")
    # CMFB 루프 보정(+20log10(1+T))이 CMRR/PSRR 둘 다 같은 T를 쓰는지 -- 값 자체가 같은
    # 31소자망/같은 H/A_c/G2에서 나오므로 이제 항등이 아니라 "둘 다 같은 T 사용"만 확인하면 됨.
    _psrr_cmfb_open_db1 = _psrr_cmfb_db1 - 20 * math.log10(abs(1.0 + _t))
    print(f"    PASS: PSRR_open(추정)={_psrr_cmfb_open_db1:.3f}dB -> "
          f"PSRR_closed={_psrr_cmfb_db1:.3f}dB (CMFB 보정 +{20*math.log10(abs(1.0+_t)):.3f}dB, "
          f"CMRR과 동일 T={_t:.4g} 재사용 확인)")
    try:
        compute_metric({**_psrr_cmfb_spec, "cm_sense_gain": -1.0}, _cmfb_ctx)
        raise AssertionError("PSRR family에서 T<=0(CM 양귀환)인데 에러가 안 났다")
    except ValueError as _e_psrr_t:
        print(f"    PASS: PSRR family도 T<=0 거부 -- {str(_e_psrr_t)[:50]}...")

    print()
    print("  [smallsignal_ratio_db/smallsignal_gain_db -- topology-무관 일반화(세션21 2차)]")
    print("  cmrr/psrr/gain_db를 회로 전용 Python 함수 없이 topology.json의 metric_spec")
    print("  선언만으로 계산 -- 51소자(1단+2단+CMFB+bias-gen 전부) + R1/R2(1GΩ 근사)를")
    print("  통째로 수치 MNA로 풀고 ports가 선언한 진짜 최종출력(Vop/Vom)에서 잰다.")
    print("  ngspice AC 독립 교차검증: stage3_full_circuit_ngspice_crosscheck.py]")
    _full_sized = {
        "M1a": {"gm": 119e-6, "gds": 1/600e3}, "M1b": {"gm": 119e-6, "gds": 1/600e3},
        "M2a": {"gm": 130e-6, "gds": 1/700e3}, "M2b": {"gm": 130e-6, "gds": 1/700e3},
        "M4a": {"gm": 140e-6, "gds": 1/250e3}, "M4b": {"gm": 140e-6, "gds": 1/250e3},
        "M3a": {"gm": 150e-6, "gds": 1/300e3}, "M3b": {"gm": 150e-6, "gds": 1/300e3},
        "M6": {"gm": 0.0, "gds": 0.5e-6}, "M7": {"gm": 90e-6, "gds": 0.4e-6},
        "M5": {"gm": 0.0, "gds": 1.0e-6},
        "M8": {"gm": 40e-6, "gds": 0.3e-6}, "M17": {"gm": 40e-6, "gds": 0.3e-6},
        "M9a": {"gm": 50e-6, "gds": 0.4e-6}, "M9b": {"gm": 50e-6, "gds": 0.4e-6},
        "M18a": {"gm": 50e-6, "gds": 0.4e-6}, "M18b": {"gm": 50e-6, "gds": 0.4e-6},
        "M11a": {"gm": 30e-6, "gds": 0.5e-6}, "M11b": {"gm": 30e-6, "gds": 0.5e-6},
        "M20a": {"gm": 30e-6, "gds": 0.5e-6}, "M20b": {"gm": 30e-6, "gds": 0.5e-6},
        "M12": {"gm": 0.0, "gds": 0.6e-6}, "M21": {"gm": 0.0, "gds": 0.6e-6},
        "M10": {"gm": 0.0, "gds": 0.6e-6}, "M19": {"gm": 0.0, "gds": 0.6e-6},
        "M13": {"gm": 40e-6, "gds": 0.3e-6}, "M22": {"gm": 40e-6, "gds": 0.3e-6},
        "M14a": {"gm": 30e-6, "gds": 0.5e-6}, "M14b": {"gm": 30e-6, "gds": 0.5e-6},
        "M23a": {"gm": 30e-6, "gds": 0.5e-6}, "M24b": {"gm": 30e-6, "gds": 0.5e-6},
        "M15": {"gm": 3.0e-3, "gds": 8e-6}, "M16": {"gm": 3.0e-3, "gds": 9e-6},
        "M25": {"gm": 3.0e-3, "gds": 8e-6}, "M26": {"gm": 3.0e-3, "gds": 9e-6},
        "M37a": {"gm": 100e-6, "gds": 1.0e-6}, "M37b": {"gm": 105e-6, "gds": 1.1e-6},
        "M36a": {"gm": 80e-6, "gds": 0.8e-6}, "M36b": {"gm": 84e-6, "gds": 0.9e-6},
        "M38": {"gm": 0.0, "gds": 1.2e-6},
        "M18_bg": {"gm": 40e-6, "gds": 0.3e-6},
        "M60": {"gm": 40e-6, "gds": 0.3e-6}, "M61": {"gm": 40e-6, "gds": 0.3e-6},
        "M64": {"gm": 30e-6, "gds": 0.5e-6}, "M63": {"gm": 30e-6, "gds": 0.5e-6},
        "M58": {"gm": 30e-6, "gds": 0.5e-6}, "M57": {"gm": 30e-6, "gds": 0.5e-6},
        "M66": {"gm": 0.0, "gds": 0.6e-6}, "M68": {"gm": 0.0, "gds": 0.6e-6},
        "M39": {"gm": 40e-6, "gds": 0.3e-6}, "M40": {"gm": 40e-6, "gds": 0.3e-6},
    }
    import os as _os_ss
    _full_topo_path = _os_ss.path.join(
        _os_ss.path.dirname(_os_ss.path.abspath(__file__)),
        "library", "current_reuse_telescopic_ota.topology.json")
    _full_ctx = SizingContext(sized=_full_sized, topology_path=_full_topo_path)
    _ss_cmrr_spec = {"type": "smallsignal_ratio_db",
                      "excite_num": {"Vip": 0.5, "Vim": -0.5}, "sense_num": "diff",
                      "excite_den": {"Vip": 1.0, "Vim": 1.0}, "sense_den": "common",
                      "sense_p": "Vop", "sense_n": "Vom"}
    _ss_psrr_spec = {"type": "smallsignal_ratio_db",
                      "excite_num": {"Vip": 0.5, "Vim": -0.5}, "sense_num": "diff",
                      "excite_den": {"vdd": 1.0}, "sense_den": "common",
                      "sense_p": "Vop", "sense_n": "Vom"}
    _ss_gain_spec = {"type": "smallsignal_gain_db", "excite": {"Vip": 0.5, "Vim": -0.5},
                      "sense_mode": "diff", "sense_p": "Vop", "sense_n": "Vom"}
    _ss_cmrr = compute_metric(_ss_cmrr_spec, _full_ctx)
    _ss_psrr = compute_metric(_ss_psrr_spec, _full_ctx)
    _ss_gain = compute_metric(_ss_gain_spec, _full_ctx)
    # ngspice AC 실측(stage3_full_circuit_ngspice_crosscheck.py, 같은 파라미터):
    # gain=99.0154dB(오차<0.001dB), PSRR=105.5051dB(오차<0.001dB),
    # CMRR=125.1843dB(오차 0.58dB -- CMFB로 심하게 억제된 Acm의 수치조건, 이 프로젝트
    # 기존 CMFB 교차검증 허용오차 범위 내 -- session20-B 앵커도 worst 3.99dB였다).
    assert abs(_ss_gain - 99.01539878703716) < 1e-6, f"gain_full_circuit_db 자기회귀: {_ss_gain}"
    assert abs(_ss_gain - 99.0154) < 0.01, f"gain ngspice 대조(99.0154dB)와 어긋남: {_ss_gain}"
    assert abs(_ss_psrr - 105.50510696686493) < 1e-6, f"psrr(신규) 자기회귀: {_ss_psrr}"
    assert abs(_ss_psrr - 105.5051) < 0.01, f"psrr ngspice 대조(105.5051dB)와 어긋남: {_ss_psrr}"
    assert abs(_ss_cmrr - 125.76715845307814) < 1e-6, f"cmrr(신규) 자기회귀: {_ss_cmrr}"
    assert abs(_ss_cmrr - 125.1843) < 1.0, f"cmrr ngspice 대조(125.1843dB)와 어긋남(오차<1dB 기대): {_ss_cmrr}"
    print(f"    PASS: gain_full_circuit_db={_ss_gain:.4f}dB (ngspice 99.0154dB, 오차<0.001dB)")
    print(f"    PASS: psrr_estimate_db(신규)={_ss_psrr:.4f}dB (ngspice 105.5051dB, 오차<0.001dB)")
    print(f"    PASS: cmrr_estimate_db(신규)={_ss_cmrr:.4f}dB (ngspice 125.1843dB, 오차 0.58dB)")
    # bias-gen이 vdd 리플을 그대로 따라간다는 것도 회귀로 고정(세션21 2차의 핵심 발견 --
    # 이상적 전류원 Iref를 개방회로로 다루면 diode-connected M18_bg가 Vbias1=vdd를 강제).
    _sol_vdd = _full_circuit_response(_full_ctx, {"vdd": 1.0}, also_fix=frozenset({"Vip", "Vim"}))
    assert abs(_sol_vdd["Vbias1"] - 1.0) < 1e-9, f"Vbias1이 vdd를 그대로 안 따라감: {_sol_vdd['Vbias1']}"
    print(f"    PASS: Vbias1(vdd=1V 리플) = {_sol_vdd['Vbias1']:.6f} (bias-gen이 vdd를 그대로 "
          f"따라감 -- Iref를 이상적 전류원=개방회로로 다룬 결과, 정직한 최악 가정)")

    print()
    print("# current_reuse_telescopic_topology() 등록 재확인(2026-07-31, 원문 Eq.2-6 재도출 후,")
    print("# gmp/gmn/gm2 3-stage로 재설계 -- stage_devices 계약을 안 바꾸고 '분배'를 topology_fn")
    print("# 자신이 하도록 함, 사용자와 함께 설계. 2026-08-12(세션30) gmp2/gmn2 4-stage로 확장)")
    print("# -- 실제(toy) LUT로 optimize_multistage() 고정점 반복 실행.")
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
    # 2026-08-12(세션30) -- stage_fT_targets(새로 노출된 준정적 검증 기준주파수)가 이
    # toy LUT(EKV 해석식, 실제 sky130 특성과 다름)에서 우연히 이 한계 순환을 유발하던
    # 동점 후보들을 걸러내 버려 converged=True로 바뀐다(실측 확인) -- fT 기능 자체는
    # 아래 L5c(실제 sky130 LUT, 51소자 전체회로) self-test가 이미 검증하므로, 이 테스트의
    # 진짜 목적(순환 감지+평균 fallback 코드 경로 자체를 계속 실행해보는 것)을 지키려고
    # 이 toy 시나리오에서만 껐다 -- fT 기능과 cycle-detection 기능은 서로 독립적인 관심사.
    _crt_tf.stage_fT_targets = None
    _crt_result = optimize_multistage(
        _crt_tf, [lut, lut, lut, lut], [float(v) for v in lut.L_grid], [float(v) for v in lut.VDS_grid],
        [i * 0.5 for i in range(4, 58)], objective="power", w_max=200e-6, max_iter=20)
    assert _crt_result is not None, "optimize_multistage()가 실행가능점을 못 찾음"
    assert abs(_crt_result["gms"][0] - _crt_result["gms"][1]) < 1e-9, "gmp != gmn(Eq.5 위반)"
    assert _crt_result["gms"][2] > 0 and _crt_result["cggs"][2] > 0, "gmp2/Cgg2(PMOS)가 비정상"
    assert _crt_result["gms"][3] > 0 and _crt_result["cggs"][3] > 0, "gmn2/Cgg2(NMOS)가 비정상"
    assert abs(_crt_result["gms"][2] - _crt_result["gms"][3]) < 1e-9, \
        "gmp2 != gmn2(세션30 50:50 기본 분할 위반) -- 이 toy LUT 자체엔 shared_gm_id_groups를 " \
        "안 넘겼으니 gm 목표값 자체(topology_fn 반환)가 이미 같아야 한다"
    assert _crt_result["converged"] is False, "이 toy LUT는 원래 한계 순환에 빠져야 하는데 수렴함 -- 회귀 확인 필요"
    assert _crt_result["cycle_detected"] is True, "순환 감지 fallback이 발동하지 않음"
    assert _crt_result["cycle_period"] == 3, f"예상 밖 순환 주기: {_crt_result['cycle_period']}"
    _crt_cgg1_total = _crt_result["cggs"][0] + _crt_result["cggs"][1]
    _crt_beta_final = 500e-15 / (500e-15 + 500e-15 + _crt_cgg1_total)
    _crt_gm2_total = _crt_result["gms"][2] + _crt_result["gms"][3]
    print(f"  gmp={_crt_result['gms'][0]*1e6:.2f}uS, gmn={_crt_result['gms'][1]*1e6:.2f}uS, "
          f"gmp2={_crt_result['gms'][2]*1e3:.4f}mS, gmn2={_crt_result['gms'][3]*1e3:.4f}mS "
          f"(합=gm2={_crt_gm2_total*1e3:.4f}mS), iters={_crt_result['iters']}, "
          f"cycle_period={_crt_result['cycle_period']}(순환 구간 gm 평균으로 안정된 추정치)")
    print(f"  Cgg1_total(M1a+M4a, 평균 gm 기준 재sizing)={_crt_cgg1_total*1e15:.2f}fF -> "
          f"beta={_crt_beta_final:.4f}(원문의 고정 근사 0.48과 다를 수 있음 -- 이 LUT의 실제 "
          f"소자 특성에서 나온 값)")

    print()
    print("# validate_theta_declaration_order() -- theta 배열 '선언 순서=실행 순서' 계약")
    print("# 위반을 읽기 전용으로 검사(2026-08-13 세션31, mirror_M18a/L_stage2out_p·n에서")
    print("# 실제로 두 번 발생한 순서 버그의 재발 방지 안전망, .ai/context.md BI~BL 참고)")

    print("  [합성 fixture -- gm_id_match_vgs_of/C타입 reference가 선언 순서를 위반하면 잡아내는지]")
    _vtdo_bad1 = {
        "compensation": {"stage_devices": [["A"]]},
        "sizing_roles": {"theta": [
            {"name": "theta_n", "bounds": [0, 1], "feeds": {
                "type": "metric_stage_budget", "metric": "gain_db", "devices": ["B"],
                "gm_id_match_vgs_of": "A2"}},
            {"name": "theta_p", "bounds": [0, 1], "feeds": {
                "type": "metric_stage_budget", "metric": "gain_db", "devices": ["A2"]}},
        ]}}
    _vtdo_v1 = validate_theta_declaration_order(_vtdo_bad1)
    assert len(_vtdo_v1) == 1 and _vtdo_v1[0]["theta"] == "theta_n", \
        f"gm_id_match_vgs_of 순서위반을 못 잡음: {_vtdo_v1}"
    print(f"    PASS: gm_id_match_vgs_of 순서위반 감지 -- {_vtdo_v1[0]['problem']}")

    _vtdo_bad2 = {"compensation": None, "sizing_roles": {"theta": [
        {"name": "c_theta", "bounds": [0, 1], "feeds": {"type": "C", "target": "X", "reference": "Y"}},
        {"name": "y_theta", "bounds": [0, 1], "feeds": {"type": "C", "target": "Y", "reference": "Z"}},
    ]}}
    _vtdo_v2 = validate_theta_declaration_order(_vtdo_bad2)
    assert {v["theta"] for v in _vtdo_v2} == {"c_theta", "y_theta"}, \
        f"C타입 reference 연쇄 순서위반을 못 잡음: {_vtdo_v2}"
    print(f"    PASS: C타입 reference 순서위반(연쇄 2건) 감지 -- {[v['theta'] for v in _vtdo_v2]}")

    print("  [올바른 순서(reference가 앞에 옴)면 위반 0건인지]")
    _vtdo_good = {"compensation": {"stage_devices": [["W"]]}, "sizing_roles": {"theta": [
        {"name": "z_theta", "bounds": [0, 1], "feeds": {"type": "C", "target": "Z", "reference": "W"}},
        {"name": "y_theta", "bounds": [0, 1], "feeds": {"type": "C", "target": "Y", "reference": "Z"}},
    ]}}
    assert validate_theta_declaration_order(_vtdo_good) == [], "올바른 순서인데 위반으로 오탐"
    print("    PASS: 올바른 순서는 위반 0건")

    print("  [compensation.stage_devices는 처음부터 생산됨으로 취급되는지]")
    _vtdo_comp = {"compensation": {"stage_devices": [["M1a", "M1b"]]}, "sizing_roles": {"theta": [
        {"name": "c_theta", "bounds": [0, 1], "feeds": {"type": "C", "target": "M2", "reference": "M1a"}},
    ]}}
    assert validate_theta_declaration_order(_vtdo_comp) == [], \
        "compensation이 이미 sizing한 소자를 참조했는데 오탐 발생"
    print("    PASS: compensation 관리 소자는 위반 없이 참조 가능")

    print("  [실제 library topology.json 4개 전부 위반 0건인지(reorder 이후 회귀 확인)]")
    import glob as _vtdo_glob
    _vtdo_lib = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "library")
    for _vtdo_path in sorted(_vtdo_glob.glob(_os.path.join(_vtdo_lib, "*.topology.json"))):
        with open(_vtdo_path, "r", encoding="utf-8") as _vtdo_f:
            _vtdo_data = json.load(_vtdo_f)
        _vtdo_meta = {"sizing_roles": _vtdo_data.get("sizing_roles"),
                      "compensation": _vtdo_data.get("compensation")}
        _vtdo_v = validate_theta_declaration_order(_vtdo_meta)
        _vtdo_name = _os.path.basename(_vtdo_path)
        assert _vtdo_v == [], f"{_vtdo_name}에 선언 순서 위반: {_vtdo_v}"
        print(f"    PASS: {_vtdo_name} -- 위반 0건")
