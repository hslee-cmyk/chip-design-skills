"""MOD1 lut -- LUT 로드·보간·조회·역산·tol_V (계획 N3.10, 설계 MOD1). 다른 패키지는 이 `__all__` 만 쓴다.

계약: lut/CONTRACT.md. 조회 함수는 첫 인자로 `LutMemo`(LutSet + 상한 LRU memo) 를 받는다.
"""

from .axis_guard import check_axes
from .cap_query import caps
from .curve_check import curve_report
from .fingerprint import lut_fingerprint
from .gm_id_curve import gm_id_curve
from .gmb import gmb
from .id_inverse import gm_id_for_target
from .lut_memo import DERIVED_TABLES, REGIONS, LutMemo
from .lut_set import load_lut_set
from .lut_types import (
    AXES,
    TOL_V_METRICS,
    CapTable,
    Caps,
    Curve,
    CurveReport,
    CurveRow,
    DcSlice,
    LutProvenance,
    LutSet,
    LutSpec,
    OpPoint,
    SliceSource,
    TargetSolution,
    TolVCell,
)
from .point_query import op_point
from .provenance import lut_provenance
from .tolerance import TolVTable, tol_v_table
from .vgs_root import vgs_for_gm_id
from .widths import widths

__all__ = (
    "AXES",
    "CapTable",
    "Caps",
    "Curve",
    "CurveReport",
    "CurveRow",
    "DERIVED_TABLES",
    "DcSlice",
    "LutMemo",
    "LutProvenance",
    "LutSet",
    "LutSpec",
    "OpPoint",
    "REGIONS",
    "SliceSource",
    "TOL_V_METRICS",
    "TargetSolution",
    "TolVCell",
    "TolVTable",
    "caps",
    "check_axes",
    "curve_report",
    "gm_id_curve",
    "gm_id_for_target",
    "gmb",
    "load_lut_set",
    "lut_fingerprint",
    "lut_provenance",
    "op_point",
    "tol_v_table",
    "vgs_for_gm_id",
    "widths",
)
