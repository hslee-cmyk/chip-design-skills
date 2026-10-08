"""MOD10 pipeline -- 진입점 run_gmid_design_pipeline·CLI·exit code(계획 N3.10 gmid_design_pipeline.py) 자리.

지금 있는 것: 단계 A 진입점 `run_stage_a`(로드 -> build_s1 -> structure.json -> build_s1v -> 보고서, 계약 pipeline/CONTRACT.md).
"""

from .stage_a import StageAResult, run_stage_a
from .stage_a_budget import structure_count_budget

__all__ = (
    "StageAResult",
    "run_stage_a",
    "structure_count_budget",
)
