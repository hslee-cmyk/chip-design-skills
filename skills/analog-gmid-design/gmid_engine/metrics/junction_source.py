"""접합 용량 입력 묶음 (DEC-91, DEC-107) -- LUT 생성 규칙 선언·kind 별 LUT 생성 기하 손가락(비례 기준)·LUT 측정 온도를
`ss_dev` 계산 블록 추가 인자 하나로 묶는다.

데이터 선언 모듈: `JunctionSource` (+ 생성자 `from_decls`).

* `ss_dev` 블록 입력 버전 = fp_of(이름, 코드, 투영(dc_op, extras)) 라서, 이 frozen 묶음이 extras 에 들어가면 LUT 규칙 선언(원본 sha256 포함)·
  비례 기준 기하·온도가 지문에 든다 -- 선언이 바뀌면 재계산, 같으면 재사용(계산 0).
* 비례 기준 `reference` = kind 마다 LUT 생성 기하 손가락 하나(finger_w = 그 kind 기준 폭 표 `w_ref_m`, m = 1) -- `junction_at_vgs_min` 의
  면적 비 r 의 분모. 기준 면적 0 은 비례 기준이 될 수 없어 `pdk_quantity_invalid`.
* kind 집합·온도는 LUT 에서 읽는다(`spec.device_kinds`, `provenance.cap_conditions["temp_c"]` -- LUT 측정 온도 = SPICE 온도).
"""
import dataclasses

from gmid_engine.core import SchemaRejectedError

from .junction_cap import DiffusionGeometry

_TEMP_KEY = "temp_c"
_AD_QUANTITY = "lut_diffusion_ad_per_w_m"
_AS_QUANTITY = "lut_diffusion_as_per_w_m"


def _reference_gate(reference):
    """기준 면적 0 -> `pdk_quantity_invalid`{quantity, value}(AD 먼저). 비례 분모 0 의 나눗셈 전에 분류된 정지."""
    for quantity, area in ((_AD_QUANTITY, reference.ad_m2), (_AS_QUANTITY, reference.as_m2)):
        if not area > 0:
            raise SchemaRejectedError(detail={"reason": "pdk_quantity_invalid", "quantity": quantity, "value": area})


@dataclasses.dataclass(frozen=True)
class JunctionSource:
    """`lut_rule_decl` = LUT 생성 규칙 core `PdkDecl`(레이아웃 전 확산 기하), `reference` = ((kind, `DiffusionGeometry`), ...) kind 정렬
    (kind 마다 LUT 생성 기하 손가락 하나 -- 비례 기준), `temp_c` = 측정 온도 °C."""

    lut_rule_decl: object
    reference: tuple
    temp_c: float

    @classmethod
    def from_decls(cls, lut_rule_decl, lut_set):
        """`lut_rule_decl` = core `read_pdk_decl` 결과, `lut_set` = lut `LutSet`(kind·기준 폭·온도의 출처).
        LUT 에 온도 기록이 없으면 ValueError(엔진과 SPICE 를 같은 온도로 맞출 근거가 없다)."""
        conditions = dict(lut_set.provenance.cap_conditions)
        if _TEMP_KEY not in conditions:
            raise ValueError("JunctionSource: LUT 측정 온도(cap_conditions temp_c) 기록이 없다")
        kinds = sorted({kind for _, kind in lut_set.spec.device_kinds})
        reference = tuple((kind, DiffusionGeometry.from_lut_rule(lut_rule_decl, lut_set.cap_map[kind].w_ref_m, 1)) for kind in kinds)
        for _, geometry in reference:
            _reference_gate(geometry)
        return cls(lut_rule_decl, reference, float(conditions[_TEMP_KEY]))

    def reference_of(self, kind):
        """kind 의 비례 기준 `DiffusionGeometry`. 없으면 KeyError."""
        return dict(self.reference)[kind]

    def pre_layout_geometry(self, finger_w_m, m):
        """레이아웃 전 첫 사이징점 확산 기하(DEC-91 (2)) = LUT 생성 규칙(`DiffusionGeometry.from_lut_rule`)."""
        return DiffusionGeometry.from_lut_rule(self.lut_rule_decl, finger_w_m, m)
