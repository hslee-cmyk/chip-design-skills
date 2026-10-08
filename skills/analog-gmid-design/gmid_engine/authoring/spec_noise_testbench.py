"""잡음 테스트벤치 선언 `human.noise_testbench` (설계 41 §7.1 폐루프 모드 '스위치', 계획 N3.15 잡음 metric 행, D-NZ1).

진입점: `noise_testbench_declaration(raw, topology) -> (NoiseTestbenchDecl | None, tuple[SchemaHit])`.

모양: `{"sampling_caps": [{"element": <커패시터 이름>, "source": {...}}, ...]}`. 키가 없으면(None) `None`.
* 설계 41 §7.1 은 '`noise_testbench.sampling_caps[]`(요소 이름과 출력 전달 이득 출처)'라고만 쓴다 -- 항목 = 요소 이름 + 값마다 출처(원칙 1)로
  읽었다(출력 전달 이득 자체는 엔진이 as-built MNA 에서 구하므로 선언하지 않는다. 항목에 다른 칸이 필요한지는 설계 미정 -- 설계 공백으로 보고).
* `sampling_caps` 필수, 비어 있지 않은 list(`type`). 항목은 객체(`type`), 받는 키 {element, source}(`key_hits`).
* `element` = topology 수동소자 중 kind `capacitor` 인 이름(`noise_cap_unknown`: topology 에 없음·커패시터 아님). 같은 이름 둘이면 `noise_cap_duplicate`.
  `topology` 가 None 이면(meta 지문 불일치) 존재 검사는 건너뛴다(교차 검사 불가).
* `source` 필수, kind `user_spec` 만.
결과 `sampling_caps` 는 이름순 tuple. 소비자는 잡음 계산 단위(U8 `noise_out_int_vrms` 폐루프 모드)이고 선언은 그 전에 로드·지문(`noise_testbench_fp`)에 든다.
"""
from ._spec_fields import at, key_hits
from .spec_model import NoiseTestbenchDecl, SamplingCapDecl
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

WHERE = "human.noise_testbench"
SECTION = "noise_testbench"
CAP_KIND = "capacitor"


def noise_testbench_declaration(raw, topology):
    if raw is None:
        return None, ()
    if not isinstance(raw, dict):
        return None, (SchemaHit("type", WHERE, "noise_testbench 는 {sampling_caps} 객체여야 한다: " + type(raw).__name__),)
    hits = key_hits(raw, ("sampling_caps",), WHERE)
    caps_raw = raw.get("sampling_caps")
    place = at(WHERE, "sampling_caps")
    caps = []
    if not isinstance(caps_raw, list) or not caps_raw:
        hits.append(SchemaHit("type", place, "sampling_caps 는 비어 있지 않은 list 여야 한다: " + repr(caps_raw)))
    else:
        known = None if topology is None else {p.name: p.kind for p in topology.passives}
        seen = set()
        for index, item in enumerate(caps_raw):
            where = at(place, index)
            if not isinstance(item, dict):
                hits.append(SchemaHit("type", where, "항목은 {element, source} 객체여야 한다"))
                continue
            before = len(hits)
            hits.extend(key_hits(item, ("element", "source"), where))
            element = item.get("element")
            if not isinstance(element, str) or not element:
                hits.append(SchemaHit("type", at(where, "element"), "element 는 비어 있지 않은 문자열이어야 한다: " + repr(element)))
            else:
                if known is not None and known.get(element) != CAP_KIND:
                    hits.append(SchemaHit("noise_cap_unknown", at(where, "element"),
                                          "샘플링 커패시터는 topology 의 capacitor 수동소자여야 한다: " + repr(element), (element,)))
                if element in seen:
                    hits.append(SchemaHit("noise_cap_duplicate", where, "같은 샘플링 커패시터가 두 번: " + repr(element), (element,)))
                seen.add(element)
            source, source_hits = source_declaration_checks(item.get("source"), where, SECTION)
            hits.extend(source_hits)
            if len(hits) == before:
                caps.append(SamplingCapDecl(element, source))
    if hits:
        return None, tuple(hits)
    return NoiseTestbenchDecl(tuple(sorted(caps, key=lambda c: c.element))), ()
