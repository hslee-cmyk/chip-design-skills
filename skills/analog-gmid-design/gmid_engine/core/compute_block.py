"""계산 블록 데코레이터 -- 선언한 입력만 투영해 넘기고, 입력 버전이 같으면 graph 의 기존 값을 재사용한다
(사용자 대원칙 2026-10-07 '같은 값을 반복 계산하는 loop 금지', 확정 사항 1·5, 계획 NFR-2·SC-a·SC-b·SC-d·SC-e).

진입점: `compute_block(name, reads=..., writes=...)`.

    @compute_block("blk", reads=(("device", "L"),), writes=(("device", "W"),))
    def blk(projection):
        return {("device", "W"): {key: ... for key, value in projection.column("device", "L")}}

    snapshot2 = blk(snapshot1, *extras)

* 블록 함수는 `Projection` 하나만 받는다(선언 밖 열은 읽을 수 없다). 추가 인자(`extras`)는 불변 값만 받고
  (`TypeError` -- dict·list·ndarray 는 거부) 투영에 함께 들어간다.
* 입력 버전 = fp_of((name, 블록 코드 해시, 투영 지문)). `snapshot.block_version(name)` 이 같으면 함수를 부르지 않고
  `snapshot` 을 그대로 돌려준다(재사용). 다르면 함수를 불러 결과를 `snapshot.write(name, 입력 버전, 결과)` 로만 쓴다.
* writer 이름 = 블록 이름. 권한표가 그 열을 이 블록에 배정하지 않았으면 `WriterPermissionError`.
* 계수: calls = reuses + computes. `recomputes_same_input` = 이 블록 객체가 이미 계산한 적 있는 입력 버전으로
  다시 계산한 횟수(구조상 0 이어야 한다 -- 0 이 아니면 스냅샷 lineage 가 값을 버린 것).
"""
import dataclasses
import hashlib
import marshal
from collections.abc import Mapping

from .fingerprint import fp_of
from .immutability import require_immutable
from .projection import Projection
from .writer_table import ENTITY_KINDS


@dataclasses.dataclass(frozen=True)
class BlockStats:
    """블록 하나의 계수 스냅샷."""

    name: str
    calls: int
    reuses: int
    computes: int
    recomputes_same_input: int


def _kind_fields(what, pairs):
    result = []
    for pair in pairs:
        if isinstance(pair, str):
            raise ValueError("compute_block: " + what + " 항목은 (kind, field) 쌍이어야 한다")
        kind, field = tuple(pair)  # 개수가 다르면 언패킹 ValueError
        if kind not in ENTITY_KINDS:
            raise ValueError("compute_block: " + what + " 의 모르는 kind " + repr(kind))
        if not isinstance(field, str) or not field:
            raise ValueError("compute_block: " + what + " 의 field 는 비어 있지 않은 문자열이어야 한다")
        result.append((kind, field))
    if len(set(result)) != len(result):
        raise ValueError("compute_block: " + what + " 에 같은 (kind, field) 중복")
    return tuple(result)


class ComputeBlock:
    """`compute_block` 이 만드는 호출 가능 객체. 직접 만들지 않는다."""

    def __init__(self, fn, name, reads, writes):
        self.fn = fn
        self.name = name
        self.reads = reads
        self.writes = writes
        self.code_hash = hashlib.sha256(marshal.dumps(fn.__code__)).hexdigest()
        self.__doc__ = fn.__doc__
        self._calls = 0
        self._reuses = 0
        self._computes = 0
        self._recomputes = 0
        self._seen_inputs = set()

    def __call__(self, snapshot, *extras):
        for extra in extras:
            require_immutable(extra)
        projection = Projection.from_snapshot(snapshot, self.reads, extras)
        input_version = fp_of((self.name, self.code_hash, projection.fp))
        self._calls += 1
        if snapshot.block_version(self.name) == input_version:
            self._reuses += 1
            return snapshot
        self._computes += 1
        if input_version in self._seen_inputs:
            self._recomputes += 1
        self._seen_inputs.add(input_version)
        result = self.fn(projection)
        if not isinstance(result, Mapping) or set(result) != set(self.writes):
            raise ValueError(
                "compute_block " + repr(self.name) + ": 결과 키는 선언한 writes " + repr(self.writes)
                + " 와 정확히 같아야 한다"
            )
        return snapshot.write(self.name, input_version, result)

    def stats(self):
        """현재 계수의 BlockStats."""
        return BlockStats(self.name, self._calls, self._reuses, self._computes, self._recomputes)

    def reset_stats(self):
        """계수와 '계산한 입력 버전' 기록을 비운다(실행 경계에서 부른다)."""
        self._calls = 0
        self._reuses = 0
        self._computes = 0
        self._recomputes = 0
        self._seen_inputs = set()


def compute_block(name, reads=(), writes=()):
    """계산 블록 데코레이터. `name`: 비어 있지 않은 문자열(= writer 이름). `reads`·`writes`: (kind, field) 쌍들.

    `writes` 는 비어 있으면 안 된다. 선언 형식 위반은 데코레이트할 때 `ValueError`.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("compute_block: name 은 비어 있지 않은 문자열이어야 한다")
    read_pairs = _kind_fields("reads", reads)
    write_pairs = _kind_fields("writes", writes)
    if not write_pairs:
        raise ValueError("compute_block: writes 가 비어 있다 -- 결과를 graph 에 쓰지 않는 블록은 계산 블록이 아니다")

    def decorate(fn):
        return ComputeBlock(fn, name, read_pairs, write_pairs)

    return decorate
