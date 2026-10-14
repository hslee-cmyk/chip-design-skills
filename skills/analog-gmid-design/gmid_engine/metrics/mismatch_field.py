"""mismatch 출처 계산 블록 -- `MismatchSource` 를 S0 수준 필드 `graph/kernel: mismatch_source` 에 쓴다 (설계 40 §2.4.7 'SearchContext 칸 배정'·§2.4.8).

진입점: `mismatch_field`(`@compute_block`, writer `mismatch_source`) -- `mismatch_field(snapshot, pdk_decl)`.

* extras: `pdk_decl` = core `read_pdk_decl` 결과. 값 = `MismatchSource.from_decl(pdk_decl)`(PDK mismatch 모델 bin slope -- offset·미러비 σ 입력). PDK 선언의 파생이라 S0 당 1회.
"""
from gmid_engine.core import compute_block
from gmid_engine.sizing import KERNEL_KEY

from .aux_types import MismatchSource
from .s0_fields import MISMATCH_SOURCE_WRITER, MISMATCH_SOURCE_WRITES


@compute_block(MISMATCH_SOURCE_WRITER, writes=MISMATCH_SOURCE_WRITES)
def mismatch_field(projection):
    (pdk_decl,) = projection.extras
    return {("graph", "mismatch_source"): {KERNEL_KEY: MismatchSource.from_decl(pdk_decl)}}
