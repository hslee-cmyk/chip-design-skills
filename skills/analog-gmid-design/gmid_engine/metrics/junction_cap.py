"""접합 용량 Cdb·Csb (DEC-91 (3)) -- PDK 모델 카드 접합 파라미터 + 역바이어스 + 확산 기하로 BSIM4 접합 모델을 계산한다.

진입점: `junction_caps`.

* 값 정본(DEC-91 (3)): 파라미터 = core PDK 선언(`read_pdk_decl`)의 `junction_<kind>_<BSIM4 이름>` 양(모델 카드 원본),
  기하 = 레이아웃 뒤 MOD7 `ly.diffusion[dev]`(Euler 행 공유 확산, finger 평균) 또는 레이아웃 전 LUT 생성 규칙
  (`DiffusionGeometry.from_lut_rule` -- LUT 규칙 선언의 `lut_diffusion_*` 양). 숫자는 이 파일에 없다.
* 식(BSIM4 4.5 접합 용량, ngspice b4v5ld·b4v5temp 과 같은 식 -- 2026-10-08 ngspice-46 sky130 `@m[capbd]`/`@m[capbs]` 와 대조):
  - 온도(tempMod 0): ΔT = T − tnom, C(T) = C · max(0, 1 + tc · ΔT)(바닥 tcj·STI 측벽 tcjsw·gate 측벽 tcjswg),
    PB(T) = PB − tpb · ΔT(tpb·tpbsw·tpbswg).
  - 쪽(drain/source)마다 영바이어스 용량 c0: 바닥 = C_j · A, STI 측벽 = C_jsw · P_eff, gate 측벽 = C_jswg · Weffcj.
    Weffcj = finger_w − 2·dwj, P_eff = P − Weffcj(perMod 1) 또는 P(perMod 0). **P_eff 를 0 으로 자르지 않는다**(ngspice
    BSIM4v5 = version 4.5 와 같은 동작, 실측): P < Weffcj 면 STI 측벽 c0 이 음수다.
  - 역바이어스 v > 0(접합 전압 −v < 0): 항마다 c0 > 0 이면 c0 · (1 + v / PB)^(−MJ), c0 ≤ 0 이면 0(ngspice 와 같다).
    v ≤ 0(영·순바이어스): 항마다 c0 · (1 − MJ · v / PB)(BSIM4 선형 연장, 음수 c0 도 더한다 -- v = 0 이면 c0 합).
  - 소자 합 = m × finger 하나(ngspice 인스턴스 `m` 배와 같다, spice_oracle C22).
* 바이어스 부호: `v_db`·`v_sb` 는 극성 정규화한 역바이어스(양수 = 역방향). nmos v_db = V(d) − V(b), pmos v_db = V(b) − V(d) --
  LUT 규약으로 v_sb = VSB, v_db = VDS + VSB.
"""
import dataclasses
import math

_PREFIX = "junction_"
_LUT_RULE = ("lut_diffusion_ad_per_w_m", "lut_diffusion_as_per_w_m", "lut_diffusion_pd_extra_m",
             "lut_diffusion_ps_extra_m")
_PERMODS = (0, 1)


def _finite(owner, name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("%s.%s: 실수여야 한다 (%r)" % (owner, name, value))
    if not math.isfinite(value):
        raise ValueError("%s.%s: 유한해야 한다 (%r)" % (owner, name, value))
    return float(value)


@dataclasses.dataclass(frozen=True)
class JunctionParams:
    """한 소자 kind 의 BSIM4 접합 파라미터(SI, tnom 은 °C). 필드 이름 = BSIM4 모델 카드 이름(s = source 쪽, d = drain 쪽).
    `dwj` = 접합 유효 폭 축소량(Weffcj = finger_w − 2·dwj, xw 를 포함한 값 -- PDK 선언 식이 정한다)."""

    cjs: float
    cjd: float
    cjsws: float
    cjswd: float
    cjswgs: float
    cjswgd: float
    mjs: float
    mjd: float
    mjsws: float
    mjswd: float
    mjswgs: float
    mjswgd: float
    pbs: float
    pbd: float
    pbsws: float
    pbswd: float
    pbswgs: float
    pbswgd: float
    tcj: float
    tcjsw: float
    tcjswg: float
    tpb: float
    tpbsw: float
    tpbswg: float
    tnom: float
    permod: float
    dwj: float

    def __post_init__(self):
        for field in dataclasses.fields(self):
            object.__setattr__(self, field.name, _finite("JunctionParams", field.name, getattr(self, field.name)))
        if self.permod not in _PERMODS:
            raise ValueError("JunctionParams.permod: 0 또는 1 (%r)" % self.permod)
        for name in ("cjs", "cjd", "cjsws", "cjswd", "cjswgs", "cjswgd", "mjs", "mjd", "mjsws", "mjswd",
                     "mjswgs", "mjswgd"):
            if getattr(self, name) < 0:
                raise ValueError("JunctionParams.%s: 0 이상 (%r)" % (name, getattr(self, name)))
        for name in ("pbs", "pbd", "pbsws", "pbswd", "pbswgs", "pbswgd"):
            if getattr(self, name) <= 0:
                raise ValueError("JunctionParams.%s: 양수 (%r)" % (name, getattr(self, name)))

    @classmethod
    def from_pdk_decl(cls, decl, kind):
        """core `PdkDecl` 에서 `junction_<kind>_<필드>` 양을 필드 순서대로 읽는다(없으면 core `pdk_quantity_undeclared`)."""
        names = tuple(_PREFIX + kind + "_" + field.name for field in dataclasses.fields(cls))
        return cls(*decl.values(names))


@dataclasses.dataclass(frozen=True)
class DiffusionGeometry:
    """finger 하나의 확산 기하(SI: finger_w·pd·ps 는 m, ad·as 는 m²)와 finger 수 `m`(> 0, 실수 허용 -- ngspice `m`)."""

    finger_w_m: float
    ad_m2: float
    as_m2: float
    pd_m: float
    ps_m: float
    m: float

    def __post_init__(self):
        for field in dataclasses.fields(self):
            object.__setattr__(self, field.name, _finite("DiffusionGeometry", field.name, getattr(self, field.name)))
        if self.finger_w_m <= 0 or self.m <= 0:
            raise ValueError("DiffusionGeometry: finger_w_m·m 은 양수 (%r, %r)" % (self.finger_w_m, self.m))
        for name in ("ad_m2", "as_m2", "pd_m", "ps_m"):
            if getattr(self, name) < 0:
                raise ValueError("DiffusionGeometry.%s: 0 이상 (%r)" % (name, getattr(self, name)))

    @classmethod
    def from_lut_rule(cls, decl, finger_w_m, m):
        """레이아웃 전 첫 사이징점(DEC-91 (2)): LUT 규칙 선언의 `lut_diffusion_ad_per_w_m`·`as_per_w_m`·`pd_extra_m`·
        `ps_extra_m` 으로 ad = ad_per_w · finger_w, pd = finger_w + pd_extra(as·ps 같은 꼴) -- spice_oracle C22 와 같은 규칙."""
        ad_per_w, as_per_w, pd_extra, ps_extra = decl.values(_LUT_RULE)
        return cls(finger_w_m, ad_per_w * finger_w_m, as_per_w * finger_w_m, finger_w_m + pd_extra,
                   finger_w_m + ps_extra, m)


@dataclasses.dataclass(frozen=True)
class JunctionCaps:
    """소자 전체(m 배) 접합 용량 F: `cdb`(drain–bulk), `csb`(source–bulk)."""

    cdb: float
    csb: float


def _temp_scale(coefficient, delta_t):
    return max(0.0, 1 + coefficient * delta_t)


def _term(c0, grading, potential, v_rev):
    if v_rev > 0:
        return c0 * (1 + v_rev / potential) ** (-grading) if c0 > 0 else 0.0
    return c0 * (1 - grading * v_rev / potential)


def _side(params, unit_caps, gradings, potentials, area, perimeter, weff, v_rev, delta_t):
    """한 쪽 finger 하나의 접합 용량. `unit_caps`·`gradings`·`potentials` = (바닥, STI 측벽, gate 측벽) 그 쪽 파라미터."""
    temp_coefficients = ((params.tcj, params.tpb), (params.tcjsw, params.tpbsw), (params.tcjswg, params.tpbswg))
    potentials_t = tuple(pb - tpb * delta_t for pb, (_, tpb) in zip(potentials, temp_coefficients))
    if min(potentials_t) <= 0:
        raise ValueError("junction_caps: 온도 보정 뒤 내부 전위가 0 이하 (%r)" % (potentials_t,))
    p_eff = perimeter - weff if params.permod == 1 else perimeter
    extents = (area, p_eff, weff)
    zero_bias = tuple(c * _temp_scale(tc, delta_t) * extent
                      for c, (tc, _), extent in zip(unit_caps, temp_coefficients, extents))
    return sum(_term(c0, mj, pb, v_rev) for c0, mj, pb in zip(zero_bias, gradings, potentials_t))


def junction_caps(params, geometry, v_db, v_sb, temp_c):
    """`JunctionCaps(cdb, csb)` -- BSIM4 접합 용량(모듈 설명 식), 소자 전체(m 배).

    `params`: `JunctionParams`, `geometry`: `DiffusionGeometry`(finger 하나 + m), `v_db`·`v_sb`: 극성 정규화 역바이어스 V,
    `temp_c`: 시뮬레이션 온도 °C(LUT 측정 조건 `temp_c` -- 엔진과 SPICE 가 같은 온도). 형식 위반 TypeError, 값 위반 ValueError
    (Weffcj ≤ 0, 온도 보정 뒤 PB ≤ 0 -- ngspice 는 PB < 0.01 V 를 0.01 V 로 자르지만 이 함수는 그 범위를 받지 않는다)."""
    if not isinstance(params, JunctionParams):
        raise TypeError("junction_caps: params 는 JunctionParams (%r)" % (params,))
    if not isinstance(geometry, DiffusionGeometry):
        raise TypeError("junction_caps: geometry 는 DiffusionGeometry (%r)" % (geometry,))
    v_db = _finite("junction_caps", "v_db", v_db)
    v_sb = _finite("junction_caps", "v_sb", v_sb)
    delta_t = _finite("junction_caps", "temp_c", temp_c) - params.tnom
    weff = geometry.finger_w_m - 2 * params.dwj
    if weff <= 0:
        raise ValueError("junction_caps: Weffcj = finger_w − 2·dwj 가 양수가 아니다 (%r)" % weff)
    p = params
    drain = _side(p, (p.cjd, p.cjswd, p.cjswgd), (p.mjd, p.mjswd, p.mjswgd), (p.pbd, p.pbswd, p.pbswgd),
                  geometry.ad_m2, geometry.pd_m, weff, v_db, delta_t)
    source = _side(p, (p.cjs, p.cjsws, p.cjswgs), (p.mjs, p.mjsws, p.mjswgs), (p.pbs, p.pbsws, p.pbswgs),
                   geometry.as_m2, geometry.ps_m, weff, v_sb, delta_t)
    return JunctionCaps(geometry.m * drain, geometry.m * source)
