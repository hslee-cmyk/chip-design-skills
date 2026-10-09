"""MOD7 이름 정준 별칭 -- 레이아웃 계산 블록이 이름 순서를 보지 않게 하는 입·출력 번역 (사용자 대원칙 '이름에 종속된 엔진 금지', U12).

`Canon` = 입력의 구조적 정준 순서로 매긴 별칭표(소자 `D000001`·넷 `N000001`·matching 그룹 id `G000001`·행 그룹 id `R000001`·수동소자 `P000001`,
번호 순서 = 구조 정준 위치 순서, 이름이 아니다 -- 만드는 쪽은 `canonical_naming.build_canon`).

`AliasView`·`real_order` = `canonical_naming.canonical_names`(계산 블록 함수를 감싸는 데코레이터)의 재료: 블록이 읽는 열·값의 이름 문자열을 별칭으로 바꿔 건네고(열은 별칭 순으로 돌려준다,
matching 그룹·행 그룹 `members` 와 그룹·행 그룹·거부·수동소자 tuple 은 별칭 순), 블록이 쓰는 결과의 별칭을 이름으로 되돌린다.
그래서 블록 안의 모든 `sorted(이름)`·이름 키 동률 처리·Euler 섬 시작 넷 선택이 구조 정준 순서를 따른다(이름은 바뀐 입력에서 자리만 다르다).
별칭 문자열 하나가 이름 둘에 겹치면(소자와 넷이 같은 이름 등) 별칭표를 만들지 않는다(빈 `Canon` = 번역 없음).
"""
import dataclasses
import re
from functools import cached_property


_TOKEN = re.compile(r"(?<![A-Za-z0-9])([DNGRP])(\d{6})(?![0-9])")
_SORTED_MEMBERS = ("MatchingGroup", "RowGroup")
_KEYS = ("gid", "rid", "name")


@dataclasses.dataclass(frozen=True)
class Canon:
    """`pairs` = ((이름, 별칭), ...). 빈 tuple 이면 번역 없음."""

    pairs: tuple = ()
    orders: tuple = ()          # ((그룹 id, 입력이 준 members 순서), ...) -- 결과 members 순서를 입력 순서로 되돌린다

    @cached_property
    def forward(self):
        return dict(self.pairs)

    @cached_property
    def member_order(self):
        return dict(self.orders)

    @cached_property
    def inverse(self):
        return {alias: name for name, alias in self.pairs}

    def _walk(self, x, text):
        if isinstance(x, str):
            return text(x)
        if isinstance(x, (float, int, bool, type(None))):
            return x
        if dataclasses.is_dataclass(x) and not isinstance(x, type):
            changes = {f.name: self._walk(getattr(x, f.name), text) for f in dataclasses.fields(x) if f.init}
            return dataclasses.replace(x, **changes)
        if isinstance(x, tuple):
            return tuple(self._walk(v, text) for v in x)
        if isinstance(x, list):
            return [self._walk(v, text) for v in x]
        if isinstance(x, dict):
            return {self._walk(k, text): self._walk(v, text) for k, v in x.items()}
        if isinstance(x, (set, frozenset)):
            return type(x)(self._walk(v, text) for v in x)
        return x

    def to_alias(self, x):
        """이름 -> 별칭(정확히 같은 문자열만). 이름 tuple 들은 별칭 순으로 다시 세운다."""
        if not self.pairs:
            return x
        forward = self.forward
        out = self._walk(x, lambda s: forward.get(s, s))
        return self._ordered(out)

    def _ordered(self, x):
        if isinstance(x, tuple) and x and all(isinstance(v, str) for v in x) and all(v in self.inverse for v in x):
            return tuple(sorted(x))
        return x

    def real_order(self, value):
        return _real_order(self, value)

    def to_name(self, x):
        """별칭 -> 이름(문자열 안에 든 별칭 포함)."""
        if not self.pairs:
            return x
        inverse = self.inverse

        def text(s):
            if s in inverse:
                return inverse[s]
            return _TOKEN.sub(lambda m: inverse.get(m.group(0), m.group(0)), s)

        return self._walk(x, text)


def _sorted_members(obj):
    """matching 그룹·행 그룹의 members 를 별칭 순으로."""
    if type(obj).__name__ in _SORTED_MEMBERS:
        return dataclasses.replace(obj, members=tuple(sorted(obj.members)))
    return obj


class AliasView:
    """블록이 보는 projection -- 읽은 값의 이름을 별칭으로(열은 별칭 키 순)."""

    def __init__(self, projection, canon):
        self._p = projection
        self._c = canon

    def column(self, kind, field):
        rows = [(self._c.to_alias(k), self._c.to_alias(v)) for k, v in self._p.column(kind, field)]
        return tuple(sorted(rows, key=lambda kv: kv[0]) if all(isinstance(k, str) for k, _ in rows) else rows)

    def value(self, kind, key, field):
        value = self._c.to_alias(self._p.value(kind, key, field))
        if isinstance(value, tuple):
            value = tuple(_sorted_members(v) for v in value)
            keyed = [getattr(v, a, None) for v in value for a in ("gid", "rid", "name") if hasattr(v, a)]
            if value and len(keyed) == len(value) and all(isinstance(k, str) for k in keyed):
                value = tuple(sorted(value, key=lambda v: next(getattr(v, a) for a in ("gid", "rid", "name") if hasattr(v, a))))
            elif value and all(isinstance(v, str) for v in value):
                value = tuple(sorted(value))
        return value


def _by_order(order, items, name_of):
    index = {n: i for i, n in enumerate(order)}
    return tuple(sorted(items, key=lambda x: index.get(name_of(x), len(index))))


def _regroup(canon, item):
    """그룹 결과 하나의 members 와 그에 맞춘 열(n_fingers·l_mismatch·w_requests·시도의 정렬된 열)을 입력 members 순서로."""
    order = canon.member_order.get(item.gid)
    if order is None or tuple(item.members) == tuple(order):
        return item
    old = tuple(item.members)
    pos = {n: i for i, n in enumerate(old)}

    def aligned(values):
        return tuple(values[pos[n]] for n in order) if len(values) == len(old) else values

    changes = {"members": tuple(order)}
    if hasattr(item, "n_fingers"):
        changes["n_fingers"] = _by_order(order, item.n_fingers, lambda x: x[0])
        changes["l_mismatch"] = _by_order(order, item.l_mismatch, lambda x: x[0])
        changes["w_requests"] = _by_order(order, item.w_requests, lambda x: x.device)
        changes["attempts"] = tuple(dataclasses.replace(a, n_fingers=aligned(a.n_fingers), W_realized_m=aligned(a.W_realized_m))
                                    if hasattr(a, "W_realized_m") else a for a in item.attempts)
    return dataclasses.replace(item, **changes)


def _real_order(canon, value):
    """결과의 이름 약속을 별칭 순서가 아닌 실제 이름·입력 순서로 다시 세운다(tuple 은 gid/rid/name 순, 행은 행 id 순, 그룹 멤버는 입력 순서)."""
    if type(value).__name__ == "RowsLayout":
        return dataclasses.replace(value, rows=tuple(sorted(value.rows, key=lambda r: r.row_id)))
    if isinstance(value, tuple) and value:
        if all(hasattr(v, "gid") and hasattr(v, "members") for v in value):
            value = tuple(_regroup(canon, v) for v in value)
        for attr in _KEYS:
            if all(isinstance(getattr(v, attr, None), str) for v in value):
                return tuple(sorted(value, key=lambda v: getattr(v, attr)))
    return value
