"""의도 영역 선언 술어 필드 계산 블록 (EO-1 범위 4, 설계 40 §2.4.8 소유표 `device.region_decl`, 41 §4.8-4).

진입점: `dc_region_decl`(`@compute_block`) -- `dc_region_decl(snapshot, regions)`. S0 블록, 쓰기 계획 앞.

* extras `regions` = `DcInputs.regions`(authoring `RegionDecl` tuple, 이름순). writes `device.region_decl` = {선언 소자: RegionDecl} -- 선언 소자만(선언 없는
  소자에는 칸이 없다). 이 필드가 '소자가 어느 영역으로 선언됐는가'의 유일한 자리이고, 소비자(봉인 7·9 `dc_seal_region`, 소자 열거 뿌리 넷, `ss_off_op`·`ss_off_delta`,
  대칭 표시)는 READS 로 읽는다.
* 소비자는 이 필드를 `r.region` 으로 거른다(`REGION_OFF`·`REGION_TRIODE` = authoring 어휘 정본). 거른 결과를 저장하지 않는다.
"""
from gmid_engine.core import compute_block

from .s2_values import DC_REGION_DECL_WRITER

READS = ()
WRITES = (("device", "region_decl"),)


@compute_block(DC_REGION_DECL_WRITER, reads=READS, writes=WRITES)
def dc_region_decl(projection):
    (regions,) = projection.extras
    return {("device", "region_decl"): {r.device: r for r in regions}}

