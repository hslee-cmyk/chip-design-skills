"""실행 계수 -- 실행 하나가 가지는 블록 호출 계수와 '같은 입력 재계산' 증거 집합 (설계 40 §2.4.9, 계획 NFR-2, 사용자 결정 X-5·X-9).

진입점: `RunCounters`. `PerfCounters`(불변 내보내기 값)와 그 행 타입은 `RunCounters` 가 참조하는 같은 파일의 데이터 선언이다.

* 소유: 실행 하나에 `RunCounters` 하나. 계산 블록 객체(`ComputeBlock`)는 상태가 없고 호출이 `counters` 를 인자로 받는다.
  graph 밖 허용 저장소 (c) 이다(설계 값이 아니라 개수만 가진다).
* 생성은 비공개 계약이다 -- `search.open_run` 만 `RunCounters()` 를 부른다(구조 규칙 M (M-b)).
* `record(block, part, outcome, input_version)`: outcome ∈ {reuse, graft, replay, compute}. `compute` 는 같은
  (block, part, input_version) 의 `compute` 가 이미 있었으면 `recomputes_same_input` 도 오른다. reuse·graft·replay 는 바꾸지 않는다.
* `result(block, part, input_version, ok)`: compute 뒤 블록 함수가 성공(True)했는지 결정적 도메인 실패(False)로 끝났는지 알린다.
  한 키에 True 와 False 가 섞이면 섞이는 그 호출에서 `ValueError`(이식이 비트 동일인 전제 위반의 fail-closed).
* `snapshot()` -> `PerfCounters`: 불변 값. (block, part) 정렬, 한 번이라도 `record` 된 행만.
* 항등식: calls = reuses + grafts + replays + computes.
"""
import dataclasses

_OUTCOMES = ("reuse", "graft", "replay", "compute")


@dataclasses.dataclass(frozen=True)
class BlockRow:
    """(block, part) 하나의 계수 행."""

    block: str
    part: str
    calls: int
    reuses: int
    grafts: int
    replays: int
    computes: int
    recomputes_same_input: int


@dataclasses.dataclass(frozen=True)
class BlockTotals:
    """여섯 계수 칸의 행 합."""

    calls: int
    reuses: int
    grafts: int
    replays: int
    computes: int
    recomputes_same_input: int


@dataclasses.dataclass(frozen=True)
class PerfCounters:
    """`RunCounters.snapshot()` 의 불변 값. `blocks` = BlockRow tuple, `block_totals` = BlockTotals."""

    blocks: tuple
    block_totals: BlockTotals


def _require_text(**named):
    for name, value in named.items():
        if not isinstance(value, str):
            raise TypeError("RunCounters: " + name + " 는 문자열이어야 한다")


class RunCounters:
    """실행 하나의 계수. 직접 만들지 않는다(`open_run` 만)."""

    def __init__(self):
        self._rows = {}        # (block, part) -> [reuses, grafts, replays, computes, recomputes_same_input]
        self._computed = set()   # (block, part, input_version) -- compute 를 이미 센 키
        self._results = {}     # (block, part, input_version) -> ok

    def record(self, block, part, outcome, input_version):
        _require_text(block=block, part=part, input_version=input_version)
        if outcome not in _OUTCOMES:
            raise ValueError("RunCounters.record: outcome 은 " + repr(_OUTCOMES) + " 중 하나여야 한다: " + repr(outcome))
        row = self._rows.setdefault((block, part), [0, 0, 0, 0, 0])
        row[_OUTCOMES.index(outcome)] += 1
        if outcome == "compute":
            key = (block, part, input_version)
            if key in self._computed:
                row[4] += 1
            self._computed.add(key)

    def result(self, block, part, input_version, ok):
        _require_text(block=block, part=part, input_version=input_version)
        if not isinstance(ok, bool):
            raise TypeError("RunCounters.result: ok 는 bool 이어야 한다")
        key = (block, part, input_version)
        before = self._results.get(key)
        if before is not None and before != ok:
            raise ValueError(
                "RunCounters.result: 같은 입력 " + repr(key) + " 에서 성공과 결정적 실패가 섞였다 -- 블록 순수성(이식 비트 동일 전제) 위반"
            )
        self._results[key] = ok

    def snapshot(self):
        rows = tuple(
            BlockRow(block, part, sum(counts[:4]), counts[0], counts[1], counts[2], counts[3], counts[4])
            for (block, part), counts in sorted(self._rows.items())
        )
        totals = BlockTotals(*(sum(getattr(row, name) for row in rows) for name in BlockTotals.__dataclass_fields__))
        return PerfCounters(rows, totals)
