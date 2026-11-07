"""접합 용량 Cdb·Csb (DEC-91 (2)(3), DEC-107) -- LUT 기준 폭 표의 VGS 최소 조회 (CDD − CGD)·(CSS − CGS) 에 확산 면적 비를 곱한다.

진입점: `junction_at_vgs_min` (+ 기하 레코드 `DiffusionGeometry`).

* 정의(근사): 접합 용량은 PDK 접합 식이 아니라 LUT 가 측정한 C 열에서 읽는다. 그 소자 (L, VDS, VSB) 단면에서 기준 폭 표 VGS 축의
  첫 격자점을 조회한다 -- 이 VGS 는 **LUT 조회 좌표일 뿐 꺼짐 분류가 아니다**(데이터에서 읽은 값, 상수 0). 그 점의 단자 자기 용량
  CDD(드레인)·CSS(소스)에서 게이트 쪽 용량 CGD·CGS 를 뺀 몫이 접합 몫이다.
* 비례: 면적 비 r_d = (AD·m) / (AD_ref·m_ref), r_s = (AS·m) / (AS_ref·m_ref). `reference` = 그 kind LUT 생성 기하 손가락 하나
  (finger_w = LUT `w_ref_m`, m = 1)라 조회 배율은 1이다. 레이아웃 전 `geometry` 는 LUT 생성 규칙 기하(W = 그 평가가 쓴 W),
  레이아웃 뒤는 MOD7 `ly.diffusion` 확산 면적.
* 순서: 열 판별(CDD -> CSS -> CGS) -> `caps` 조회 -> r -> 곱 -> 음수·NaN 관문(`not (v >= 0)`, 드레인 먼저). 관문 밖 분기·문턱·클램프 0.
* 용량은 PDK 양을 읽지 않는다(PDK 이식성, O-197). 기하의 숫자 규칙은 LUT 생성 규칙 선언(`DiffusionGeometry.from_lut_rule`)에만 있다.
"""
import dataclasses
import math

from gmid_engine.core import SealViolationError
from gmid_engine.lut import caps

REASON_COLUMN_UNAVAILABLE = "lut_column_unavailable"
REASON_JUNCTION_CAP_NEGATIVE = "junction_cap_negative"
_LUT_RULE = ("lut_diffusion_ad_per_w_m", "lut_diffusion_as_per_w_m", "lut_diffusion_pd_extra_m",
             "lut_diffusion_ps_extra_m")


def _finite(owner, name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("%s.%s: 실수여야 한다 (%r)" % (owner, name, value))
    if not math.isfinite(value):
        raise ValueError("%s.%s: 유한해야 한다 (%r)" % (owner, name, value))
    return float(value)


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


def _column_gate(table, kind):
    """열 판별 -- CDD -> CSS -> CGS 순서로 첫 결손을 `lut_column_unavailable`(소자 없음)로 올린다."""
    for column, absent in (("CDD", "CDD" not in table.columns), ("CSS", "CSS" not in table.columns), ("CGS", table.CGS is None)):
        if absent:
            raise SealViolationError(detail={"reason": REASON_COLUMN_UNAVAILABLE, "column": column, "kind": kind})


def _passivity_gate(device, terminal, value):
    if not (value >= 0):
        raise SealViolationError(devices=(device,), detail={"reason": REASON_JUNCTION_CAP_NEGATIVE, "terminal": terminal,
                                                            "value": value})


def junction_at_vgs_min(memo, device, kind, L, vds, vsb, geometry, reference):
    """`(cdb, csb)` -- 소자 전체(m 배) 접합 용량 F(모듈 설명 식).

    `memo` = lut `LutMemo`, `device` = 소자 이름(정지 기록용), `kind`, (L, vds, vsb) = 그 소자 봉인점 값(켜진 점 `caps` 와 같은 인자),
    `geometry` = 그 평가 `DiffusionGeometry`, `reference` = 그 kind LUT 생성 기하 손가락 하나. 순수 함수.
    정지: 열 결손 -> `lut_column_unavailable`(소자 없음), 음수·NaN -> `junction_cap_negative`(소자 있음, d 먼저),
    L·축 실패는 `caps` 의 기존 사유."""
    for name, value in (("geometry", geometry), ("reference", reference)):
        if not isinstance(value, DiffusionGeometry):
            raise TypeError("junction_at_vgs_min: %s 는 DiffusionGeometry (%r)" % (name, value))
    table = memo.lut.cap_map[kind]
    vgs = min(table.grids[1])
    _column_gate(table, kind)
    c = caps(memo, kind, L, vgs, vds, vsb, reference.finger_w_m)
    r_d = (geometry.ad_m2 * geometry.m) / (reference.ad_m2 * reference.m)
    r_s = (geometry.as_m2 * geometry.m) / (reference.as_m2 * reference.m)
    cdb = (c.cdd - c.cgd) * r_d
    csb = (c.css - c.cgs) * r_s
    _passivity_gate(device, "d", cdb)
    _passivity_gate(device, "s", csb)
    return cdb, csb
