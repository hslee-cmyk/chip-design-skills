"""접합 용량 입력 묶음 (DEC-91) -- PDK 선언·LUT 생성 규칙 선언·LUT 측정 온도를 `ss_dev` 계산 블록 추가 인자 하나로 묶는다.

데이터 선언 모듈: `JunctionSource` (+ 생성자 `from_decls`).

* `ss_dev` 블록 입력 버전 = fp_of(이름, 코드, 투영(dc_op, extras)) 라서, 이 frozen 묶음이 extras 에 들어가면 접합 파라미터 값·
  LUT 규칙 선언(원본 sha256 포함)·온도·PDK 선언 sha256 이 지문에 든다 -- 선언이 바뀌면 재계산, 같으면 재사용(계산 0).
* PDK 선언 전체(양 60개)를 지문에 넣지 않고 쓰는 kind 의 `JunctionParams` 값만 넣는다(+ 선언 sha256) -- 블록 호출마다 지문 비용을 작게.
* kind 집합·온도는 LUT 에서 읽는다(`spec.device_kinds`, `provenance.cap_conditions["temp_c"]` -- LUT 측정 온도 = SPICE 온도).
"""
import dataclasses

from .junction_cap import DiffusionGeometry, JunctionParams

_TEMP_KEY = "temp_c"


@dataclasses.dataclass(frozen=True)
class JunctionSource:
    """`params` = ((kind, JunctionParams), ...) kind 정렬, `lut_rule_decl` = LUT 생성 규칙 core `PdkDecl`(레이아웃 전 확산 기하),
    `temp_c` = 측정 온도 °C, `pdk_decl_sha256` = 접합 파라미터를 읽은 PDK 선언 파일 sha256(지문용 출처)."""

    params: tuple
    lut_rule_decl: object
    temp_c: float
    pdk_decl_sha256: str

    @classmethod
    def from_decls(cls, pdk_decl, lut_rule_decl, lut_set):
        """`pdk_decl`·`lut_rule_decl` = core `read_pdk_decl` 결과, `lut_set` = lut `LutSet`(kind·온도의 출처).
        LUT 에 온도 기록이 없으면 ValueError(엔진과 SPICE 를 같은 온도로 맞출 근거가 없다)."""
        conditions = dict(lut_set.provenance.cap_conditions)
        if _TEMP_KEY not in conditions:
            raise ValueError("JunctionSource: LUT 측정 온도(cap_conditions temp_c) 기록이 없다")
        kinds = sorted({kind for _, kind in lut_set.spec.device_kinds})
        params = tuple((kind, JunctionParams.from_pdk_decl(pdk_decl, kind)) for kind in kinds)
        return cls(params, lut_rule_decl, float(conditions[_TEMP_KEY]), pdk_decl.decl_sha256)

    def params_of(self, kind):
        """kind 의 `JunctionParams`. 없으면 KeyError."""
        return dict(self.params)[kind]

    def pre_layout_geometry(self, finger_w_m, m):
        """레이아웃 전 첫 사이징점 확산 기하(DEC-91 (2)) = LUT 생성 규칙(`DiffusionGeometry.from_lut_rule`)."""
        return DiffusionGeometry.from_lut_rule(self.lut_rule_decl, finger_w_m, m)
