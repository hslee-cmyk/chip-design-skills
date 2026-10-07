"""W0 레일 전압 계산 블록 (계획 N3.4 W0, DEC-60: 레일 전압 = spec `supplies_v`, 스칼라 vdd 폴백 없음).

진입점: `dc_rails`(`@compute_block`) -- `dc_rails(snapshot, supplies)`.

* reads `node.is_rail`. extras `supplies` = graph `supplies_declaration` 이 정규화한 ((레일, V), ...)(커널 컨텍스트가 검사).
* writes `node.dc_rail_v` = 레일 노드마다 V. 레일 밖 노드에는 쓰지 않는다(노드전압 하나 = writer 하나: 레일은 이 블록,
  나머지는 `dc_columns`).
"""
from gmid_engine.core import compute_block

from .s2_values import DC_RAILS_WRITER

READS = (("node", "is_rail"),)
WRITES = (("node", "dc_rail_v"),)


@compute_block(DC_RAILS_WRITER, reads=READS, writes=WRITES)
def dc_rails(projection):
    (supplies,) = projection.extras
    volts = dict(supplies)
    rails = tuple(net for net, is_rail in projection.column("node", "is_rail") if is_rail)
    return {("node", "dc_rail_v"): {net: float(volts[net]) for net in rails}}
