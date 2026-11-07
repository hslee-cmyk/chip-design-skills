"""MOD5 metrics -- 소신호 스탬프·MNA 조립 1회·주파수 풀이·metric·레지스트리(계획 N3.10 circuit_metrics.py).

1단계 = 엔진 상태와 독립인 수치 핵심(입력은 불변 레코드, graph·S2 를 import 하지 않는다). 2단계 = ss_linearize 배선
(봉인 스냅샷 -> `ss_dev`·`metrics_ss`·`metrics_dc` 계산 블록 -> S2 필드, 진입점 `ss_evaluate`). GB4·GB5·ls 는 다음 단계.
계약: `metrics/CONTRACT.md`.
"""

from .achievability import achievability, block_spec
from .achievability_types import (
    REASON_DECOMPOSED_ONLY,
    REASON_LOAD_UNFIXED,
    AreaBound,
    AxisSpec,
    BlockBound,
    BlockModel,
    BlockSpec,
    CurveCheck,
    CurveChecks,
    DofReport,
    GainCheck,
    HeadroomRow,
    LocalInputs,
    LocalView,
    MosLocal,
    ResLocal,
    SliceCurveCheck,
)
from .area import area_search
from .area_lower_bound import area_lower_bound
from .block_gain_bound import block_gain_bound
from .block_gain_rows import row_gains
from .block_param_tables import ParamTables
from .curve_checks import curve_checks
from .dof_report import dof_report
from .headroom_bound import HeadroomResult, headroom_bound
from .junction_field import junction_field
from .mismatch_field import mismatch_field
from .model_error_field import model_error_field
from .s0_fields import (
    ACH_KEY,
    ACH_WRITES,
    ACHIEVABILITY_WRITER,
    JUNCTION_SOURCE_WRITER,
    METRIC_STRUCTURE_WRITER,
    METRICS_S0_WRITERS,
    MISMATCH_SOURCE_WRITER,
    MODEL_ERROR_WRITER,
)
from .aux_types import (
    GATE_EMPTY,
    GATE_ERROR,
    GATE_OK,
    GATE_REASON_BASE_UNDEFINED,
    GATE_REASON_FRONT_EMPTY,
    GATE_REASON_NO_BLOCK_REPORT,
    GATE_REASON_NO_PERTURBATION,
    GATE_REASON_NO_UNREAD_DIRECTION,
    GATE_REASON_PERTURBATION_UNMEASURED,
    GATE_UNDETERMINABLE,
    BlockGain,
    BlockResidual,
    BlockStruct,
    CoupledResidual,
    FfContribution,
    FfRatio,
    FfStruct,
    GateResult,
    IcmConfig,
    IcmPort,
    IcmWindow,
    LsFields,
    LsNode,
    MetricStructure,
    MirrorRatio,
    MismatchSource,
    NodalSystem,
    NqsRatio,
    OffsetAnalysis,
    OffsetContribution,
    OffsetSystematic,
    SatDevice,
    SwingIcmr,
    ViewStruct,
)
from .block_model import block_local_gain
from .block_residual import block_residual
from .coupled_residual import coupled_residual
from .catalog import metric_catalog
from .device_sigma import device_sigmas
from .crossing import find_crossing
from .dc_metrics import metrics_dc
from .dc_limit import solve_dc_limit
from .evaluate import metric_value
from .ff_gm_ratio import ff_gm_ratio
from .junction_cap import DiffusionGeometry, junction_at_vgs_min
from .icm_config import icm_config_window, kvl_sensitivity
from .icm_window import icm_window_metrics
from .junction_source import JunctionSource
from .loop_analysis import analyze_loop
from .loop_cut import cut_circuit
from .ls_fields import ls_fields
from .ls_swing import ls_swing
from .lut_parameters import LUT_PARAMETERS, lut_parameters
from .mna_build import build_mna
from .metric_structure import metric_structure
from .metrics_aux import AUX_TYPES, REPORT_BLOCK_RESIDUAL, REPORT_LS_FIELDS, metrics_aux
from .mirror_ratio import mirror_ratio
from .model_error import model_error_pairs
from .mna_solve import solve_responses
from .mna_types import (
    AreaSearch,
    Crossing,
    CutCircuit,
    DcLimit,
    Factor,
    LoopAnalysis,
    MetricResult,
    MnaSystem,
    OutputResistance,
    ParameterSet,
    PointSolution,
    ProbeFactor,
    Resolution,
    ResponseRatio,
    ResponseSensitivity,
    Roots,
    SupplyCurrents,
    SystemResponse,
    Undefined,
)
from .noise_analysis import noise_analysis
from .noise_devices import noise_devices
from .noise_integral import noise_integral
from .noise_plan import noise_plan
from .noise_sources import noise_sources
from .noise_transfer import noise_transfer
from .noise_types import (
    NoiseAnalysis,
    NoiseDecl,
    NoiseDevice,
    NoiseInput,
    NoisePlan,
    NoiseSetup,
    NoiseSources,
    NoiseTransfer,
)
from .nqs_ratio import nqs_ratio
from .offset_analysis import offset_analysis
from .offset_systematic import offset_systematic
from .omega_grid import omega_grid
from .pencil_roots import pencil_roots
from .phase_lag import phase_lag
from .probe_loop import probe_factor
from .ratio import response_ratio
from .point_solve import solve_point
from .records import (
    Capacitor,
    ChannelCurrent,
    CurrentSource,
    DcOperatingPoint,
    Excitation,
    GateArea,
    LoopCut,
    MosSmallSignal,
    PassiveArea,
    PassiveAreaDecl,
    RailBias,
    Resistor,
    Sense,
    SmallSignalCircuit,
    StampSet,
)
from .passive_values import passive_values, theta_passive_pairs
from .registry import RegisteredMetric, metric_registry
from .resolution import metric_resolutions
from .rout import output_resistance
from .sensitivity import response_sensitivity
from .ss_circuit import ss_circuit, ss_circuit_field
from .ss_evaluate import ss_evaluate
from .ss_nodal import ss_nodal_system
from .ss_off_delta import ss_off_delta
from .ss_off_gate import off_region_gate
from .ss_off_op import ss_off_op
from .ss_linearize import GMB_COLUMN, GMB_VS_CELL_SECANT, JUNCTION_LAYOUT_DIFFUSION, JUNCTION_LUT_RULE, ss_dev
from .ss_metrics import metrics_ss
from .ss_types import MetricBundle, MetricRequest, OffDelta, OffOp, SsCircuit, SsDevice, SsEvaluation
from .stamp_mos import mos_stamps
from .sensitivity_gate import sensitivity_gate
from .stamp_two_terminal import two_terminal_stamps
from .supply import supply_currents
from .verified_by import SPICE_ORACLE, VerifiedBy, verified_by
from .block_gain_model import block_gain_model_of

__all__ = (
    "ACH_KEY",
    "ACH_WRITES",
    "ACHIEVABILITY_WRITER",
    "JUNCTION_SOURCE_WRITER",
    "METRIC_STRUCTURE_WRITER",
    "METRICS_S0_WRITERS",
    "MISMATCH_SOURCE_WRITER",
    "MODEL_ERROR_WRITER",
    "junction_field",
    "mismatch_field",
    "model_error_field",
    "AUX_TYPES",
    "AreaBound",
    "AreaSearch",
    "AxisSpec",
    "BlockBound",
    "BlockGain",
    "BlockModel",
    "BlockResidual",
    "BlockSpec",
    "BlockStruct",
    "Capacitor",
    "ChannelCurrent",
    "CoupledResidual",
    "Crossing",
    "CurrentSource",
    "CurveCheck",
    "CurveChecks",
    "CutCircuit",
    "DcLimit",
    "DcOperatingPoint",
    "DiffusionGeometry",
    "DofReport",
    "Excitation",
    "Factor",
    "FfContribution",
    "FfRatio",
    "FfStruct",
    "GMB_COLUMN",
    "GMB_VS_CELL_SECANT",
    "GainCheck",
    "GateArea",
    "GateResult",
    "GATE_EMPTY",
    "GATE_ERROR",
    "GATE_OK",
    "GATE_REASON_BASE_UNDEFINED",
    "GATE_REASON_FRONT_EMPTY",
    "GATE_REASON_NO_BLOCK_REPORT",
    "GATE_REASON_NO_PERTURBATION",
    "GATE_REASON_NO_UNREAD_DIRECTION",
    "GATE_REASON_PERTURBATION_UNMEASURED",
    "GATE_UNDETERMINABLE",
    "REASON_DECOMPOSED_ONLY",
    "REASON_LOAD_UNFIXED",
    "IcmConfig",
    "IcmPort",
    "IcmWindow",
    "HeadroomResult",
    "HeadroomRow",
    "JUNCTION_LAYOUT_DIFFUSION",
    "JUNCTION_LUT_RULE",
    "JunctionSource",
    "LUT_PARAMETERS",
    "LocalInputs",
    "LocalView",
    "LoopAnalysis",
    "LoopCut",
    "LsFields",
    "LsNode",
    "MetricBundle",
    "MetricRequest",
    "MetricResult",
    "MetricStructure",
    "MirrorRatio",
    "MismatchSource",
    "NodalSystem",
    "MnaSystem",
    "MosLocal",
    "MosSmallSignal",
    "NoiseAnalysis",
    "NoiseDecl",
    "NoiseDevice",
    "NoiseInput",
    "NoisePlan",
    "NoiseSetup",
    "NoiseSources",
    "NoiseTransfer",
    "NqsRatio",
    "OffsetAnalysis",
    "OffsetContribution",
    "OffsetSystematic",
    "OutputResistance",
    "ParamTables",
    "ParameterSet",
    "PassiveArea",
    "PassiveAreaDecl",
    "PointSolution",
    "ProbeFactor",
    "REPORT_BLOCK_RESIDUAL",
    "REPORT_LS_FIELDS",
    "RailBias",
    "RegisteredMetric",
    "ResLocal",
    "Resistor",
    "Resolution",
    "ResponseRatio",
    "ResponseSensitivity",
    "Roots",
    "SatDevice",
    "Sense",
    "SliceCurveCheck",
    "SmallSignalCircuit",
    "SsCircuit",
    "OffDelta",
    "OffOp",
    "SsDevice",
    "SsEvaluation",
    "StampSet",
    "SupplyCurrents",
    "SwingIcmr",
    "SystemResponse",
    "Undefined",
    "VerifiedBy",
    "ViewStruct",
    "achievability",
    "block_spec",
    "analyze_loop",
    "area_lower_bound",
    "area_search",
    "block_gain_bound",
    "block_local_gain",
    "block_gain_model_of",
    "block_residual",
    "build_mna",
    "coupled_residual",
    "curve_checks",
    "cut_circuit",
    "device_sigmas",
    "dof_report",
    "ff_gm_ratio",
    "find_crossing",
    "headroom_bound",
    "junction_at_vgs_min",
    "ls_fields",
    "ls_swing",
    "lut_parameters",
    "metric_catalog",
    "metric_registry",
    "metric_resolutions",
    "metric_structure",
    "metric_value",
    "metrics_aux",
    "metrics_dc",
    "metrics_ss",
    "mirror_ratio",
    "model_error_pairs",
    "mos_stamps",
    "noise_analysis",
    "noise_devices",
    "noise_integral",
    "noise_plan",
    "noise_sources",
    "noise_transfer",
    "nqs_ratio",
    "offset_analysis",
    "offset_systematic",
    "omega_grid",
    "output_resistance",
    "passive_values",
    "pencil_roots",
    "phase_lag",
    "probe_factor",
    "response_ratio",
    "response_sensitivity",
    "row_gains",
    "sensitivity_gate",
    "solve_dc_limit",
    "solve_point",
    "solve_responses",
    "ss_circuit",
    "ss_circuit_field",
    "ss_nodal_system",
    "ss_off_delta",
    "ss_off_op",
    "off_region_gate",
    "icm_config_window",
    "icm_window_metrics",
    "kvl_sensitivity",
    "ss_dev",
    "ss_evaluate",
    "supply_currents",
    "theta_passive_pairs",
    "two_terminal_stamps",
    "SPICE_ORACLE",
    "verified_by",
)
