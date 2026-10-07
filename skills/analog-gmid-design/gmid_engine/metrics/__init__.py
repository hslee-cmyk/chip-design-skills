"""MOD5 metrics -- 소신호 스탬프·MNA 조립 1회·주파수 풀이·metric·레지스트리(계획 N3.10 circuit_metrics.py).

이번 단계 = 엔진 상태와 독립인 수치 핵심(입력은 불변 레코드, graph·S2 를 import 하지 않는다). ss_linearize(봉인 스냅샷 ->
레코드)·GB4·GB5·ls·계산 블록 배선은 다음 단계. 계약: `metrics/CONTRACT.md`.
"""

from .area import area_search
from .catalog import metric_catalog
from .crossing import find_crossing
from .evaluate import metric_value
from .loop_analysis import analyze_loop
from .mna_build import build_mna
from .mna_solve import solve_responses
from .mna_types import (
    AreaSearch,
    Crossing,
    Factor,
    LoopAnalysis,
    MnaSystem,
    OutputResistance,
    PointSolution,
    Roots,
    SupplyCurrents,
    SystemResponse,
)
from .omega_grid import omega_grid
from .pencil_roots import pencil_roots
from .phase_lag import phase_lag
from .point_solve import solve_point
from .records import (
    Capacitor,
    ChannelCurrent,
    CurrentSource,
    DcOperatingPoint,
    Excitation,
    GateArea,
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
    "DcOperatingPoint",
    "Excitation",
    "Factor",
    "GateArea",
    "LoopAnalysis",
    "MnaSystem",
    "MosSmallSignal",
    "OutputResistance",
    "PassiveArea",
    "PointSolution",
    "RailBias",
    "RegisteredMetric",
    "Resistor",
    "Roots",
    "Sense",
    "SmallSignalCircuit",
    "StampSet",
    "SupplyCurrents",
    "SystemResponse",
    "analyze_loop",
    "area_search",
    "build_mna",
    "find_crossing",
    "metric_catalog",
    "metric_registry",
    "metric_value",
    "mos_stamps",
    "omega_grid",
    "output_resistance",
    "pencil_roots",
    "phase_lag",
    "solve_point",
    "solve_responses",
    "supply_currents",
    "two_terminal_stamps",
)
