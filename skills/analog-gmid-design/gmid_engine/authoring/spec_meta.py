"""spec `meta` 와 topology 의 짝 대조 (설계 design_spec_format 1.1·1.3).

진입점: `meta_cross_check(meta, topology, path) -> tuple[SchemaHit]`.

* `circuit_name_mismatch` -- `meta.circuit` 이 `topology.name` 과 다르거나, 파일 이름 stem(`<circuit>` +
  `SPEC_SUFFIX`)과 다르다(짝 짓기는 파일 이름으로, 내용 검사는 meta 로).
* `topology_fp_mismatch` -- `meta.topology_fp` 가 `topology.connectivity_fp` 와 다르다(파일 sha256 이 아니라 연결
  투영 지문 -- 주석만 바꾼 topology 는 spec 을 깨지 않는다). 이 hit 이 있으면 호출자는 topology 교차 검사를 돌리지
  않는다(다른 회로판에 대한 교차 검사는 의미가 없다 -- `not_evaluated`).
`meta` 의 형식 위반(문자열 아님 등)은 `spec_schema` 몫이라 여기서는 문자열일 때만 비교한다.
"""
from pathlib import Path

from .topology_model import SchemaHit

SPEC_SUFFIX = ".sizing_spec.json"


def meta_cross_check(meta, topology, path):
    hits = []
    circuit = meta.get("circuit")
    if isinstance(circuit, str):
        name = Path(path).name
        stem = name[:-len(SPEC_SUFFIX)] if name.endswith(SPEC_SUFFIX) else None
        if circuit != topology.name:
            hits.append(SchemaHit("circuit_name_mismatch", "meta.circuit", "meta.circuit " + repr(circuit)
                                  + " 이 topology_name " + repr(topology.name) + " 과 다르다", (circuit, topology.name)))
        if circuit != stem:
            hits.append(SchemaHit("circuit_name_mismatch", "meta.circuit", "meta.circuit " + repr(circuit)
                                  + " 이 파일 이름 " + repr(name) + " (<circuit>" + SPEC_SUFFIX + ") 과 맞지 않는다",
                                  (circuit,)))
    fp = meta.get("topology_fp")
    if isinstance(fp, str) and fp != topology.connectivity_fp:
        hits.append(SchemaHit("topology_fp_mismatch", "meta.topology_fp", "meta.topology_fp 가 topology "
                              + repr(topology.name) + " 의 connectivity_fp " + topology.connectivity_fp
                              + " 와 다르다(연결이 바뀌었으면 spec 을 다시 확인해 지문을 갱신한다)"))
    return tuple(hits)
