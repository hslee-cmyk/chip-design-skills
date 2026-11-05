"""회로 사이징 spec -> GB7 입력 선언 투영 (계획 N3.4 W0·W2(d)·W3, DEC-08·60, 설계 10절 U2·U3·U9).

진입점: `dc_inputs_from_spec(spec) -> DcInputs`.

* `supplies_v` = spec 그대로(레일 정본, DEC-60).
* `input_dc_v`: InputDc mode `net` -> 그 레일의 supplies_v 전압, `value` -> 값, `engine` -> None(엔진이 정함 = W4).
* `node_targets` = spec `node_voltage_targets_v`(W3). `element_values` = mode `value` 인 원소의 값, `engine` -> None(θ).
* `regions` = intended_region 의 `RegionDecl` 선언 전부(triode·off, 이름순). 어휘 정본 = authoring `REGION_TRIODE`·`REGION_OFF`.
* `engine_elements` = mode `engine` 인 원소 이름(정렬) -- 그 수동소자가 DEC-92 θ 연속 성분·영점 상쇄 구조 규칙 대상이다
  (`dc_theta_schema`). `pending`(결정 대기)은 engine 이 아니다 -- 값을 엔진이 고르지 않는다.
* `has_gbw_target`·`has_rout_limit`·`has_settling` = GBW 보상 목표(값이 정해진 `gbw_target_hz`)·판정 제약 중 `rout_ss_ohm`·정착 목표(`SettlingDecl`)의 **유무**(TB-1 J-T1, 값은
  읽지 않는다). `theta_class` 블록이 매크로 활성·출력 저항 선언 판정에 쓴다.
* **결정 대기 표지**(`pending`)는 막지 않고 '미선언'으로 투영하며 (경로, 결정 ID) 를 `pending` 에 모은다. 실행 전 정지
  여부는 이 함수가 아니라 파이프라인(MOD10)이 `pending` 을 보고 정한다(authoring SPEC_CONTRACT 3절) -- 이 함수는
  고르지 않고 기록만 한다.
"""
from gmid_engine.authoring import SettlingDecl, SizingSpecDoc, TargetDecl

from .s2_values import DcInputs

_VALUE = "value"
_NET = "net"
_ENGINE = "engine"
_GBW_TARGET = "gbw_target_hz"          # authoring 보상 목표 키(`TARGET_KEYS`)
_ROUT_METRIC = "rout_ss_ohm"           # 출력 저항 metric(metrics 레지스트리 이름과 같은 값 -- sizing 은 metrics 를 import 하지 않는다)


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
    regions = tuple(sorted(spec.intended_region, key=lambda r: r.device)) if isinstance(spec.intended_region, tuple) else ()
    pending = tuple(sorted((mark.path, mark.decision) for mark in spec.pending))
    engine = tuple(sorted(element.name for element in spec.element_values if element.mode == _ENGINE))
    declared = spec.compensation_targets if isinstance(spec.compensation_targets, tuple) else ()
    gbw = any(key == _GBW_TARGET and isinstance(decl, TargetDecl) and decl.value is not None for key, decl in declared)
    settling = any(isinstance(decl, SettlingDecl) for _key, decl in declared)
    rout = any(c.metric == _ROUT_METRIC for c in spec.judged_constraints)
    return DcInputs(tuple(spec.supplies_v), input_dc_v, tuple(targets), values, regions, pending, engine, gbw, rout, settling)
