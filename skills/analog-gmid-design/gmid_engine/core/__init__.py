"""core (층 0) -- 내용 지문·불변 graph 스냅샷·계산 블록·LUT memo·실패 규약·결정론. 다른 패키지는 이 `__all__` 만 쓴다."""

from .bounded_lru import BoundedLRU, LruStats
from .canon_pointer import CanonPointer
from .compute_block import BlockStats, ComputeBlock, compute_block
from .determinism import sorted_items
from .failure_record import FailureRecord
from .exit_code import exit_code_for
from .failure_classes import CANDIDATE_FAILURE_CLASSES, FAILURE_CLASSES, UNEXPECTED_EXIT_CODE, FailureClass
from .failure_errors import (
    InfeasibleSizingError,
    InfeasibleTargetError,
    NonconvergentError,
    SchemaRejectedError,
    SealViolationError,
    SearchFailedError,
    StructureUnresolvedError,
)
from .field_value import FieldValue
from .fingerprint import fp_of
from .graph_record import GraphRecord
from .graph_snapshot import GraphSnapshot
from .immutability import require_immutable
from .margin import normalized_margin
from .metric_signature import METRIC_DOMAINS, OBJECTIVE_AXES, VIEW_KINDS, MetricSignature
from .projection import Projection
from .writer_error import WriterPermissionError
from .writer_table import ENTITY_KINDS, WriterTable

__all__ = (
    "BlockStats",
    "BoundedLRU",
    "CANDIDATE_FAILURE_CLASSES",
    "CanonPointer",
    "ComputeBlock",
    "ENTITY_KINDS",
    "FAILURE_CLASSES",
    "FailureClass",
    "FailureRecord",
    "FieldValue",
    "GraphRecord",
    "GraphSnapshot",
    "InfeasibleSizingError",
    "InfeasibleTargetError",
    "LruStats",
    "METRIC_DOMAINS",
    "MetricSignature",
    "NonconvergentError",
    "OBJECTIVE_AXES",
    "Projection",
    "SchemaRejectedError",
    "SealViolationError",
    "SearchFailedError",
    "StructureUnresolvedError",
    "UNEXPECTED_EXIT_CODE",
    "VIEW_KINDS",
    "WriterPermissionError",
    "WriterTable",
    "compute_block",
    "exit_code_for",
    "fp_of",
    "normalized_margin",
    "require_immutable",
    "sorted_items",
)
