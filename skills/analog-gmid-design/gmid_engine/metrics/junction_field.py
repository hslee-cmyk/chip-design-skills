"""접합 용량 입력 계산 블록 -- `JunctionSource` 를 S0 수준 필드 `graph/kernel: junction_source` 에 쓴다 (설계 40 §2.4.7 'SearchContext 칸 배정'·§2.4.8, DEC-91).

진입점: `junction_field`(`@compute_block`, writer `junction_source`) -- `junction_field(snapshot, pdk_decl, lut_rule_decl, lut)`.

* extras: `pdk_decl`·`lut_rule_decl` = core `read_pdk_decl` 결과(PDK 선언·LUT 생성 규칙 선언), `lut` = sizing `LutAccess`(kind·측정 온도의 출처 = `lut.memo.lut`).
* 값 = `JunctionSource.from_decls(pdk_decl, lut_rule_decl, lut.memo.lut)` -- PDK 선언·LUT 생성 규칙 선언의 파생이라 S0 당 1회(같은 선언·LUT 면 재사용), 평가는 필드를 읽어
  `ss_dev`·`ss_evaluate(junction=)` 에 넘긴다. LUT 에 온도 기록이 없으면 `ValueError`(`JunctionSource.from_decls`).
"""
from gmid_engine.core import compute_block
from gmid_engine.sizing import KERNEL_KEY

from .junction_source import JunctionSource
from .s0_fields import JUNCTION_SOURCE_WRITER, JUNCTION_SOURCE_WRITES


@compute_block(JUNCTION_SOURCE_WRITER, writes=JUNCTION_SOURCE_WRITES)
def junction_field(projection):
    pdk_decl, lut_rule_decl, lut = projection.extras
    return {("graph", "junction_source"): {KERNEL_KEY: JunctionSource.from_decls(pdk_decl, lut_rule_decl, lut.memo.lut)}}
