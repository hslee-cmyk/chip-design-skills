"""③ L 계산 블록 (설계 3.2 2, 계획 N3.9 LR1·LR3).

진입점: `dc_lengths`(`@compute_block`) -- `dc_lengths(snapshot, theta_lengths)`.

* reads `device.element_class`(MOS 집합), `device.region_decl`(`off` 소자는 MOS 집합에서 뺀다 -- θ 에 L 성분이 없고 선언 `l_m` 이 L). extras `theta_lengths` = ((소자, m), ...) θ 의 L 성분, `off_devices`(생략 가능) = `off` 선언 소자 이름(필드 `device.region_decl` 에서 -- θ 에 L 성분이 없고 선언 `l_m` 이 L 이다).
* writes `device.dc_L`. 노드전압을 읽지 않는다(설계 3.2 2 -- LR 규칙이 VDS 를 읽게 되면 reads 에 들어가 SCC 가 커진다).
* L 동치류(`rel_l_class`)는 status proposed 라 평가 경로가 읽지 않는다 -> 소자마다 L(theta_schema 와 같은 규칙).
* L 의 LUT 축 조건(master lut r3: L 앵커 이산 키, r4: 같은 bin 안 연속)은 이 블록이 아니라 LUT 조회가 판정한다
  (`lut_l_not_anchor`·`lut_axis_out_of_range` -> SEAL_VIOLATION, 소자 이름 덧붙임).
"""
from gmid_engine.authoring import REGION_OFF
from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_MOS

from .s2_values import DC_LENGTHS_WRITER

READS = (("device", "element_class"), ("device", "region_decl"))
WRITES = (("device", "dc_L"),)


@compute_block(DC_LENGTHS_WRITER, reads=READS, writes=WRITES)
def dc_lengths(projection):
    (theta_lengths,) = projection.extras
    lengths = dict(theta_lengths)
    off = frozenset(m for m, r in projection.column("device", "region_decl") if r.region == REGION_OFF)
    mos = {name for name, cls in projection.column("device", "element_class") if cls == ELEMENT_MOS} - off
    if set(lengths) != mos:
        raise ValueError("dc_lengths: θ L 키가 MOS 집합과 다르다: " + repr(sorted(set(lengths) ^ mos)))
    return {("device", "dc_L"): {name: float(value) for name, value in lengths.items()}}
