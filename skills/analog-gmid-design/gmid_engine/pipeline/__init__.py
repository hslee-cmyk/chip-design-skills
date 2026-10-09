"""MOD10 pipeline -- 진입점 run_gmid_design_pipeline·CLI·exit code(계획 N3.10 gmid_design_pipeline.py) 자리.

지금 있는 것: 단계 A 진입점 `run_stage_a`(로드 -> build_s1 -> structure.json -> build_s1v -> 보고서, 계약 pipeline/CONTRACT.md),
단계 B 진입점 `run_stage_b`(GB4 달성가능성: 커널 컨텍스트 -> search 정의역 -> `metrics.achievability` -> 보고서, exit 3).
"""

from .stage_a import StageAResult, run_stage_a
from .stage_a_budget import structure_count_budget
from .stage_b import StageBResult, run_stage_b

__all__ = (
    "StageAResult",
    "StageBResult",
    "run_stage_a",
    "run_stage_b",
    "structure_count_budget",
)
