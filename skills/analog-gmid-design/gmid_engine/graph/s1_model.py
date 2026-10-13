"""S1 그래프 -- core GraphSnapshot 위의 불변 S1 스냅샷과 질의 (설계 design_mod3_s1_graph 3·4절, 확정 사항 1·2, NFR-4).

진입점: `S1Graph(key, snapshot)` -- `build_s1` 이 만든다(직접 만들지 않는다).

* `key`: `S1Key`. `snapshot`: core `GraphSnapshot`(권한표가 `S1_WRITERS` 를 덮는다 -- S0 수준 스냅샷이면 S1v·커널·GB4·출발 구간 필드도 담는다, 설계 40 §2.4.1). 값·writer·입력 버전·쓰기 횟수는
  `snapshot.field(kind, key, field)`(core `FieldValue`)로 본다 -- 필드가 곧 캐시다.
* `column(kind, field)` -> 그 필드가 있는 레코드의 ((key, value), ...) key 정렬 tuple.
* `value(kind, key, field)` -> 값 하나(그 레코드에 필드가 없으면 `KeyError`).
* 둘 다: (kind, field) 가 권한표에 없으면 `KeyError`, 권한표에 있으나 그 writer 가 이 스냅샷에서 아직 돌지 않았으면
  `FieldNotComputed`(빈 tuple 을 돌려주지 않는다).
"""
import dataclasses

from .s1_values import FieldNotComputed, S1Key


@dataclasses.dataclass(frozen=True)
class S1Graph:
    """불변 S1 스냅샷 묶음. `snapshot` 은 eq=False 라 `==` 는 같은 스냅샷 객체일 때만 참이다."""

    key: S1Key
    snapshot: object

    def column(self, kind, field):
        """(kind, field) 열의 ((key, value), ...) -- key 정렬 tuple."""
        self._require_computed(kind, field)
        return self.snapshot.column(kind, field)

    def value(self, kind, key, field):
        """레코드 하나의 필드 값. 레코드나 필드가 없으면 `KeyError`."""
        self._require_computed(kind, field)
        return self.snapshot.value(kind, key, field)

    def _require_computed(self, kind, field):
        writer = self.snapshot.writers.writer_of(kind, field)
        if writer is None:
            raise KeyError("이 스냅샷 권한표 밖 필드: " + repr((kind, field)))
        if self.snapshot.block_version(writer) is None:
            raise FieldNotComputed("필드 " + repr((kind, field)) + " 의 writer " + repr(writer)
                                   + " 가 이 스냅샷에서 아직 돌지 않았다")
