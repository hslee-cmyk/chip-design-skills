"""결정론 도우미 -- 순회는 정렬된 tuple 위에서만 한다 (계획 NFR-4, IC2).

진입점: `sorted_items(items, *, key=None) -> tuple`.
"""
from collections.abc import Mapping


def sorted_items(items, *, key=None):
    """정렬된 tuple 을 돌려준다.

    * `items` 가 Mapping 이면 `(키, 값)` 쌍을 키 순서로(`key` 가 있으면 키에 `key` 를 적용한 순서로).
    * 그 밖의 iterable 이면 원소를 정렬한 tuple(`key` 는 `sorted` 의 key 와 같다).
    비교할 수 없는 원소가 섞이면 `sorted` 의 `TypeError` 를 그대로 낸다(임의 순서로 대신하지 않는다).
    """
    if isinstance(items, Mapping):
        if key is None:
            return tuple(sorted(items.items(), key=lambda pair: pair[0]))
        return tuple(sorted(items.items(), key=lambda pair: key(pair[0])))
    return tuple(sorted(items, key=key))
