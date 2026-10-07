"""MOD5 metrics -- 소신호 스탬프·MNA 조립 1회·주파수 풀이·metric·레지스트리(계획 N3.10 circuit_metrics.py).

이번 단계 = 엔진 상태와 독립인 수치 핵심(입력은 불변 레코드, graph·S2 를 import 하지 않는다). ss_linearize(봉인 스냅샷 ->
레코드)·GB4·GB5·ls·계산 블록 배선은 다음 단계. 계약: `metrics/CONTRACT.md`.
"""

from .area import area_search
from .catalog import metric_catalog
from .crossing import find_crossing
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
    "GateArea",
    "JunctionCaps",
    "JunctionParams",
    "LoopAnalysis",
    "LoopCut",
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
    "supply_currents",
    "two_terminal_stamps",
)
