"""실제 PDK LUT 용 `LutSpec.min_finger_w_m` 채우기 -- PDK 선언의 `min_finger_w_m`(역할 이름)에서 읽는다 (lut CONTRACT: 부르는 쪽이
PDK 선언에서 채운다, O-197). manifest 슬라이스 최소 폭에서 유도하지 않는다(card 20261104-wb1). toy LUT(합성 슬라이스) spec 은 쓰지 않는다.
"""
from pathlib import Path

from gmid_engine.core import BoundedLRU, read_pdk_decl

_PDK_DECL = Path(__file__).resolve().parents[2] / "assets" / "sky130_pdk_decl.json"
ROLE = "min_finger_w_m"


def min_finger_w_m(kinds):
    """`kinds` (kind 이름들) 각각의 하한 = PDK 선언 양 ROLE. 선언에 없으면 SchemaRejectedError(fail-closed)."""
    w = read_pdk_decl(str(_PDK_DECL), BoundedLRU(16)).value(ROLE)
    return {k: w for k in kinds}
