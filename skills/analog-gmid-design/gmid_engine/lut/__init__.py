"""MOD1 lut -- LUT 로드·보간·조회·역산·tol_V (계획 N3.10, 설계 MOD1). 다른 패키지는 이 `__all__` 만 쓴다.

계약: lut/CONTRACT.md. 조회 함수는 첫 인자로 `LutMemo`(LutSet + 상한 LRU memo) 를 받는다.
"""

from .axis_bounds import lut_axis_bounds
from .axis_guard import check_axes
from .cap_query import caps
from .curve_check import curve_report
from .data_location import resolve_lut_location
from .derived_fns import DERIVED_FUNCTIONS, derived
from .finger_slice import FingerSlice, finger_slice, reachable_slices
from .fingerprint import lut_fingerprint
from .ft_curve import ft_curve
from .gm_id_curve import gm_id_curve
from .gmb import gmb
from .id_inverse import gm_id_for_target
from .idu_curve import idu_curve
from .intrinsic_gain_curve import intrinsic_gain_curve
from .lut_memo import DERIVED_TABLES, REGIONS, LutMemo
from .lut_requirements import require_lut_data
from .lut_set import load_lut_set
from .lut_types import (
    AXES,
    CAP_TABLE_COLUMNS,
    CLASS_HERMITE,
    COLUMN_ORIGINS,
    CURVE_QUANTITIES,
    DERIVED_COLUMNS,
    NOISE_B_STATUS,
    SLICE_OPTIONAL_COLUMNS,
    TOL_NOISE_METRICS,
    TOL_V_METRICS,
    TOL_VDSAT_METRICS,
    CapTable,
    Caps,
    ColumnSource,
    Curve,
    CurveReport,
    CurveRow,
    DcSlice,
    EdgeCost,
    GmIdAxisCurve,
    LBin,
    LBinMap,
    LutLocation,
    LutProvenance,
    LutSet,
    LutSpec,
    MidpointChecks,
    MidpointRow,
    MidpointTable,
    MismatchSens,
    MismatchSigma,
    MismatchTable,
    NoiseParams,
    NoisePlanes,
    NoiseTable,
    OpPoint,
    SliceSource,
    TargetSolution,
    TolMismatchCell,
    TolNoiseCell,
    TolVCell,
    TolVdsatCell,
)
from .midpoint_checks import midpoint_l_bin_checks
from .mismatch_query import mismatch_dvgs
from .mismatch_sigma import mismatch_sigma_vgs
from .mismatch_tolerance import TolMismatchTable, tol_mismatch_table
from .noise_planes import noise_planes
from .noise_query import noise_params
from .noise_tolerance import TolNoiseTable, tol_noise_table
from .point_query import op_point
from .provenance import lut_provenance
from .sat_threshold import (
    REASON_LUT_DOMAIN,
    REASON_OFF_DECLARED,
    REASON_REVERSE_VDS,
    REASON_VDSAT_COLUMN_UNAVAILABLE,
    SatBound,
    sat_threshold,
)
from .sat_threshold_grid import sat_threshold_grid
from .table_cache import TableCache
from .tolerance import TolVTable, tol_v_table
from .vdsat_curve import vdsat_curve
from .vdsat_query import vdsat
from .vdsat_tolerance import TolVdsatTable, tol_vdsat_table
from .vgs_current_density import vgs_for_current_density
from .vgs_root import vgs_for_gm_id
from .slice_gap import SLICE_GAP_REASONS, is_slice_gap
from .slice_of_finger import slice_of_finger
from .slice_tables import build_slice_tables
from .widths import widths

__all__ = (
    "AXES",
    "CAP_TABLE_COLUMNS",
    "CLASS_HERMITE",
    "COLUMN_ORIGINS",
    "CURVE_QUANTITIES",
    "CapTable",
    "Caps",
    "ColumnSource",
    "Curve",
    "CurveReport",
    "CurveRow",
    "DERIVED_COLUMNS",
    "DERIVED_TABLES",
    "DcSlice",
    "EdgeCost",
    "DERIVED_FUNCTIONS",
    "derived",
    "GmIdAxisCurve",
    "LBin",
    "FingerSlice",
    "LBinMap",
    "SLICE_GAP_REASONS",
    "build_slice_tables",
    "finger_slice",
    "is_slice_gap",
    "reachable_slices",
    "slice_of_finger",
    "LutLocation",
    "LutMemo",
    "LutProvenance",
    "LutSet",
    "LutSpec",
    "MidpointChecks",
    "MidpointRow",
    "MidpointTable",
    "MismatchSens",
    "MismatchSigma",
    "MismatchTable",
    "NOISE_B_STATUS",
    "NoiseParams",
    "NoisePlanes",
    "NoiseTable",
    "OpPoint",
    "REASON_LUT_DOMAIN",
    "REASON_OFF_DECLARED",
    "REASON_REVERSE_VDS",
    "REASON_VDSAT_COLUMN_UNAVAILABLE",
    "REGIONS",
    "SLICE_OPTIONAL_COLUMNS",
    "SatBound",
    "SliceSource",
    "TOL_NOISE_METRICS",
    "TOL_VDSAT_METRICS",
    "TOL_V_METRICS",
    "TableCache",
    "TargetSolution",
    "TolMismatchCell",
    "TolMismatchTable",
    "TolNoiseCell",
    "TolNoiseTable",
    "TolVCell",
    "TolVTable",
    "TolVdsatCell",
    "TolVdsatTable",
    "caps",
    "check_axes",
    "curve_report",
    "ft_curve",
    "gm_id_curve",
    "gm_id_for_target",
    "gmb",
    "idu_curve",
    "intrinsic_gain_curve",
    "load_lut_set",
    "lut_fingerprint",
    "lut_provenance",
    "midpoint_l_bin_checks",
    "mismatch_dvgs",
    "mismatch_sigma_vgs",
    "noise_params",
    "noise_planes",
    "op_point",
    "require_lut_data",
    "sat_threshold",
    "sat_threshold_grid",
    "resolve_lut_location",
    "tol_mismatch_table",
    "tol_noise_table",
    "tol_v_table",
    "tol_vdsat_table",
    "lut_axis_bounds",
    "vdsat",
    "vdsat_curve",
    "vgs_for_current_density",
    "vgs_for_gm_id",
    "widths",
)
