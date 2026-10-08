"""상한 LRU memo -- graph 밖 순수 함수(LUT 조회 등) 전용 (확정 사항 4, 계획 NFR-2·WP-10, DF-07·DF-13 재발 금지).

진입점: `BoundedLRU`.

* 상한은 생성 인자로만 받는다(숫자 상수를 박지 않는다 -- 부르는 쪽이 '한 평가 sweep 작업 집합' 식으로 계산).
* 상한에 닿으면 가장 오래 안 쓴 항목을 밀어낸다(캐싱을 멈추지 않는다 -- DF-07).
* 키는 불변 값만 받고, `canonical_key`(= `fp_of` 와 같은 동치 관계의 hashable 값, 직렬화·sha256 없음)를 dict 키로 쓴다 --
  `id()` 키 없음(DF-13), 0.0 과 -0.0 은 다른 키, 1 / 1.0 / True 도 서로 다른 키, NaN 도 같은 내용이면 적중.
  불변 검사는 `canonical_key` 가 같은 순회에서 한다(가변 값은 `TypeError`).
* 설계 값(graph 필드)은 여기에 두지 않는다 -- graph 가 유일 정본이다(확정 사항 1).
"""
import dataclasses
from collections import OrderedDict

from .canonical_key import canonical_key


@dataclasses.dataclass(frozen=True)
class LruStats:
    """memo 계수 스냅샷. `recomputes_after_eviction` = 밀려난 키를 다시 계산한 횟수(실행 내 같은 키 재계산은 이것뿐)."""

    capacity: int
    size: int
    hits: int
    misses: int
    evictions: int
    recomputes_after_eviction: int


class BoundedLRU:
    """`lookup(key, compute)`: 적중이면 저장 값, 아니면 `compute()` 결과를 저장하고 돌려준다."""

    def __init__(self, capacity):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("BoundedLRU: capacity 는 1 이상 정수여야 한다(부르는 쪽이 계산해 넘긴다)")
        self._capacity = capacity
        self._entries = OrderedDict()
        self._evicted = set()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._recomputes_after_eviction = 0

    def __len__(self):
        return len(self._entries)

    def lookup(self, key, compute):
        """키 `key`(불변 값)의 memo 값. 없으면 `compute()`(인자 없는 호출) 결과를 저장한다.

        `compute` 가 예외를 내면 아무것도 저장하지 않고 그 예외를 그대로 낸다(miss 로는 센다).
        """
        memo_key = canonical_key(key)
        if memo_key in self._entries:
            self._hits += 1
            self._entries.move_to_end(memo_key)
            return self._entries[memo_key]
        self._misses += 1
        if memo_key in self._evicted:
            self._recomputes_after_eviction += 1
            self._evicted.discard(memo_key)
        value = compute()
        self._entries[memo_key] = value
        if len(self._entries) > self._capacity:
            evicted_key, _ = self._entries.popitem(last=False)
            self._evicted.add(evicted_key)
            self._evictions += 1
        return value

    def stats(self):
        """현재 계수의 LruStats."""
        return LruStats(
            self._capacity, len(self._entries), self._hits, self._misses,
            self._evictions, self._recomputes_after_eviction,
        )
