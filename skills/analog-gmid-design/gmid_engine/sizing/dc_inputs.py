"""회로 사이징 spec -> GB7 입력 선언 투영 (계획 N3.4 W0·W2(d)·W3, DEC-08·60, 설계 10절 U2·U3·U9).

진입점: `dc_inputs_from_spec(spec) -> DcInputs`.

* `supplies_v` = spec 그대로(레일 정본, DEC-60).
* `input_dc_v`: InputDc mode `net` -> 그 레일의 supplies_v 전압, `value` -> 값, `engine` -> None(엔진이 정함 = W4).
* `node_targets` = spec `node_voltage_targets_v`(W3). `element_values` = mode `value` 인 원소의 값, `engine` -> None(θ).
* `linear_devices` = intended_region 에서 region == `LINEAR_REGION`(= authoring `REGION_TRIODE` "triode") 인 선언 소자(이름순).
* `engine_elements` = mode `engine` 인 원소 이름(정렬) -- 그 수동소자가 DEC-92 θ 연속 성분·영점 상쇄 구조 규칙 대상이다
  (`dc_theta_schema`). `pending`(결정 대기)은 engine 이 아니다 -- 값을 엔진이 고르지 않는다.
* **결정 대기 표지**(`pending`)는 막지 않고 '미선언'으로 투영하며 (경로, 결정 ID) 를 `pending` 에 모은다. 실행 전 정지
  여부는 이 함수가 아니라 파이프라인(MOD10)이 `pending` 을 보고 정한다(authoring SPEC_CONTRACT 3절) -- 이 함수는
  고르지 않고 기록만 한다.
"""
from gmid_engine.authoring import SizingSpecDoc

from .s2_values import LINEAR_REGION, DcInputs

_VALUE = "value"
_NET = "net"
_ENGINE = "engine"


def dc_inputs_from_spec(spec):
    if not isinstance(spec, SizingSpecDoc):
        raise TypeError("dc_inputs_from_spec: spec 는 authoring.load_sizing_spec 결과 SizingSpecDoc 이어야 한다")
    supplies = dict(spec.supplies_v)
    input_dc_v = None
    mode = getattr(spec.input_dc, "mode", None)
    if mode == _NET:
        input_dc_v = supplies[spec.input_dc.net]
    elif mode == _VALUE:
        input_dc_v = spec.input_dc.value_v
    targets = spec.node_voltage_targets_v if isinstance(spec.node_voltage_targets_v, tuple) else ()
    values = tuple((element.name, element.value if element.mode == _VALUE else None)
                   for element in spec.element_values)
    regions = spec.intended_region if isinstance(spec.intended_region, tuple) else ()
    linear = tuple(sorted(r.device for r in regions if r.region == LINEAR_REGION))
    pending = tuple(sorted((mark.path, mark.decision) for mark in spec.pending))
    engine = tuple(sorted(element.name for element in spec.element_values if element.mode == _ENGINE))
    return DcInputs(tuple(spec.supplies_v), input_dc_v, tuple(targets), values, linear, pending, engine)
