"""S0 수준 스냅샷 자리 -- 한 S0 의 저장소와 키 입력을 묶은 값 (설계 40 §2.4.3, v1.9.1 D6 저장 시점).

진입점: `S0Slot(store, inputs, sources)`.

* 단계 A(`pipeline.run_stage_a`)가 S0 키 입력(`inputs` = ((이름, 지문 | None), ...), `sources` = ((역할, (경로 | None, sha256 | None)), ...))을 한 번
  만들어 이 값으로 넘긴다. 단계 A·B 는 `load` 로 읽기만 하고, S0 수준 블록이 모두 끝나는 `search.build_search_context` 끝에서 `save` 를 한 번 부른다
  (부분 스냅샷이 디스크에 남지 않는다 -- 단일 writer).
* `load()` -> (GraphSnapshot | None, outcome), `save(snapshot, transient=())` -> 경로 | None -- core `S0SnapshotStore` 그대로(`transient` = 직렬화하지
  않는 writer, 단계 B 층).
"""
import dataclasses

from .snapshot_codec import S0SnapshotStore


@dataclasses.dataclass(frozen=True)
class S0Slot:
    """`store` = `S0SnapshotStore`, `inputs` = ((키 이름, 문자열 | None), ...), `sources` = ((역할, (경로 | None, sha256 | None)), ...)."""

    store: S0SnapshotStore
    inputs: tuple
    sources: tuple

    def __post_init__(self):
        if not isinstance(self.store, S0SnapshotStore):
            raise TypeError("S0Slot.store 는 S0SnapshotStore 여야 한다")
        if not isinstance(self.inputs, tuple) or not isinstance(self.sources, tuple):
            raise TypeError("S0Slot.inputs·sources 는 (이름, 값) tuple 이어야 한다")

    def load(self):
        """(GraphSnapshot | None, outcome)."""
        return self.store.load(dict(self.inputs), dict(self.sources))

    def save(self, snapshot, transient=()):
        """`snapshot` 을 이 S0 키로 쓴다(이미 검증되는 파일이 있으면 쓰지 않는다). 쓴 경로 또는 None."""
        return self.store.save(dict(self.inputs), dict(self.sources), snapshot, transient)
