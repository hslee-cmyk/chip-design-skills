"""MOD5 metrics -- 소신호 스탬프·MNA 조립 1회·주파수 풀이·metric·레지스트리(계획 N3.10 circuit_metrics.py).

1단계 = 엔진 상태와 독립인 수치 핵심(입력은 불변 레코드, graph·S2 를 import 하지 않는다). 2단계 = ss_linearize 배선
(봉인 스냅샷 -> `ss_dev`·`metrics_ss`·`metrics_dc` 계산 블록 -> S2 필드, 진입점 `ss_evaluate`). GB4·GB5·ls 는 다음 단계.
계약: `metrics/CONTRACT.md`.
"""

from .area import area_search
from .catalog import metric_catalog
from .crossing import find_crossing
from .dc_metrics import metrics_dc
from .dc_limit import solve_dc_limit
from .evaluate import metric_value
from .junction_cap import DiffusionGeometry, JunctionCaps, JunctionParams, junction_caps
from .loop_analysis import analyze_loop
from .loop_cut import cut_circuit
from .mna_build import build_mna
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
    PointSolution,
    ProbeFactor,
    ResponseRatio,
    Roots,
    SupplyCurrents,
    SystemResponse,
    Undefined,
)
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
    RailBias,
    Resistor,
    Sense,
    SmallSignalCircuit,
    StampSet,
)
from .registry import RegisteredMetric, metric_registry
from .rout import output_resistance
from .ss_circuit import ss_circuit
from .ss_evaluate import ss_evaluate
from .ss_linearize import GMB_COLUMN, GMB_VS_CELL_SECANT, JUNCTION_PENDING, ss_dev
from .ss_metrics import metrics_ss
from .ss_types import MetricBundle, MetricRequest, SsCircuit, SsDevice, SsEvaluation
from .stamp_mos import mos_stamps
from .stamp_two_terminal import two_terminal_stamps
from .supply import supply_currents

__all__ = (
    "AreaSearch",
    "Capacitor",
    "ChannelCurrent",
    "Crossing",
    "CurrentSource",
    "CutCircuit",
    "DcLimit",
    "DcOperatingPoint",
    "DiffusionGeometry",
    "Excitation",
    "Factor",
    "GMB_COLUMN",
    "GMB_VS_CELL_SECANT",
    "GateArea",
    "JUNCTION_PENDING",
    "JunctionCaps",
    "JunctionParams",
    "LoopAnalysis",
    "LoopCut",
    "MetricBundle",
    "MetricRequest",
    "MetricResult",
    "MnaSystem",
    "MosSmallSignal",
    "OutputResistance",
    "PassiveArea",
    "PointSolution",
    "ProbeFactor",
    "RailBias",
    "RegisteredMetric",
    "Resistor",
    "ResponseRatio",
    "Roots",
    "Sense",
    "SmallSignalCircuit",
    "SsCircuit",
    "SsDevice",
    "SsEvaluation",
    "StampSet",
    "SupplyCurrents",
    "SystemResponse",
    "Undefined",
    "analyze_loop",
    "area_search",
    "build_mna",
    "cut_circuit",
    "find_crossing",
    "junction_caps",
    "metric_catalog",
    "metric_registry",
    "metric_value",
    "metrics_dc",
    "metrics_ss",
    "mos_stamps",
    "omega_grid",
    "output_resistance",
    "pencil_roots",
    "phase_lag",
    "probe_factor",
    "response_ratio",
    "solve_dc_limit",
    "solve_point",
    "solve_responses",
    "ss_circuit",
    "ss_dev",
    "ss_evaluate",
    "supply_currents",
    "two_terminal_stamps",
)
