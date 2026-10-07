"""θ 스키마(DOF 표) 계산 블록 (설계 3.1 5, 계획 DEC-70 결정변수, DEC-88, N3.7 DOF 입력).

진입점: `dc_theta_schema`(`@compute_block`) -- `dc_theta_schema(snapshot, declared_resistors)`. θ 무관(S0 당 1회).

성분 (kind, key):
* `ln_idu`(쓰기 소자 -- DEC-88 반전 좌표 ln IDu, IDu = ID·L/W), `L`(모든 MOS -- `l_class` 관계는 status `proposed`
  (J-U4-a 미확정)라 평가 경로가 읽지 않는다(계획 N3.3: 평가는 declared·derived·ratified 만) -> 소자마다 L),
* `y`(W4 키마다, [0, 1] 창 안 위치), `current`(원소 단위 KCL 독립 기저), `resistance`(DC 경로 저항 중 spec 값 미선언).
`declared_resistors` = spec 에 값이 선언된 저항 이름 tuple.
"""
from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE

from .s2_values import (
    COORD_WRITER,
    DC_KEY,
    DC_THETA_SCHEMA_WRITER,
    REL_WINDOW,
    RESISTOR,
    THETA_CURRENT,
    THETA_L,
    THETA_LN_IDU,
    THETA_RESISTANCE,
    THETA_Y,
    ThetaSchema,
)

READS = (
    ("device", "dc_coord"), ("node", "dc_writer"), ("graph", "dc_current_basis"), ("device", "element_class"),
    ("device", "kind"),
)
WRITES = (("graph", "dc_theta_schema"),)


@compute_block(DC_THETA_SCHEMA_WRITER, reads=READS, writes=WRITES)
def dc_theta_schema(projection):
    (declared_resistors,) = projection.extras
    classes = dict(projection.column("device", "element_class"))
    kinds = dict(projection.column("device", "kind"))
    basis = projection.value("graph", DC_KEY, "dc_current_basis")
    components = set()
    for name, coord in projection.column("device", "dc_coord"):
        if coord.role == COORD_WRITER:
            components.add((THETA_LN_IDU, name))
    components.update((THETA_L, name) for name, cls in classes.items() if cls == ELEMENT_MOS)
    components.update((THETA_Y, w.y_key) for _net, w in projection.column("node", "dc_writer")
                      if w.relation == REL_WINDOW)
    components.update((THETA_CURRENT, name) for name in basis.free)
    components.update((THETA_RESISTANCE, name) for name, _a, _b in basis.ends
                      if classes[name] == ELEMENT_PASSIVE and kinds[name] == RESISTOR and name not in declared_resistors)
    return {("graph", "dc_theta_schema"): {DC_KEY: ThetaSchema(tuple(sorted(components)))}}
