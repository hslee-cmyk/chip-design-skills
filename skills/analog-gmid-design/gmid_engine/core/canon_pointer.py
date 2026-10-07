"""현재 정본 포인터 -- 채택된 GraphSnapshot 하나를 가리킨다 (확정 사항 2 '현재 정본 = 채택 스냅샷 포인터').

진입점: `CanonPointer`.

스냅샷 자체는 불변이고, 바뀌는 것은 '어느 스냅샷이 정본인가' 하나뿐이다. 후보 스냅샷은 각자 만들어지고
채택될 때만 `adopt` 로 포인터가 옮겨진다.
"""
from .graph_snapshot import GraphSnapshot


class CanonPointer:
    """`current` = 채택된 스냅샷, `history` = 채택 순서대로의 스냅샷 fp tuple(처음 것 포함)."""

    def __init__(self, initial):
        if not isinstance(initial, GraphSnapshot):
            raise TypeError("CanonPointer: GraphSnapshot 만 채택한다")
        self._current = initial
        self._history = (initial.fp,)

    @property
    def current(self):
        return self._current

    @property
    def history(self):
        return self._history

    def adopt(self, snapshot):
        """`snapshot` 을 정본으로 채택한다. 권한표(WriterTable)가 현재 정본과 다르면 `ValueError`."""
        if not isinstance(snapshot, GraphSnapshot):
            raise TypeError("CanonPointer: GraphSnapshot 만 채택한다")
        if snapshot.writers != self._current.writers:
            raise ValueError("CanonPointer: writer 권한표가 다른 스냅샷은 같은 정본 lineage 가 아니다")
        self._current = snapshot
        self._history = self._history + (snapshot.fp,)
        return snapshot
