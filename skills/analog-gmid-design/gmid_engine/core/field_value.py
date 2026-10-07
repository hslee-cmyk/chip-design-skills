"""graph 필드 값 -- 값과 그 값을 만든 writer·입력 버전 (확정 사항 1 '필드가 곧 캐시', 계획 SC-b).

진입점: `FieldValue`.
"""
import dataclasses

from .fingerprint import fp_of
from .immutability import require_immutable


@dataclasses.dataclass(frozen=True)
class FieldValue:
    """graph 레코드 필드 하나의 불변 값.

    * `value`: 불변 값(`require_immutable` 통과).
    * `writer`: 이 값을 쓴 writer 이름(권한표의 배정 writer).
    * `input_version`: 이 값을 만든 입력의 지문 문자열(계산 블록이면 투영·추가 인자·코드 해시의 지문).
    * `write_count`: 이 lineage 에서 이 필드가 쓰인 횟수(첫 쓰기 = 1, SC-b 쓰기 카운터).
    * `value_fp`: `fp_of(value)` -- 생성 시 한 번 계산한다(넘기지 않는다).
    """

    value: object
    writer: str
    input_version: str
    write_count: int = 1
    value_fp: str = dataclasses.field(init=False)

    def __post_init__(self):
        require_immutable(self.value)
        if not isinstance(self.writer, str) or not self.writer:
            raise ValueError("FieldValue.writer 는 비어 있지 않은 문자열이어야 한다")
        if not isinstance(self.input_version, str) or not self.input_version:
            raise ValueError("FieldValue.input_version 은 비어 있지 않은 문자열이어야 한다")
        if isinstance(self.write_count, bool) or not isinstance(self.write_count, int) or self.write_count < 1:
            raise ValueError("FieldValue.write_count 는 1 이상 정수여야 한다")
        object.__setattr__(self, "value_fp", fp_of(self.value))
