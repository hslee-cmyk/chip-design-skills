import dataclasses
from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class Pt:
    x: float


@dataclasses.dataclass(frozen=True)
class Zed:
    z: float


@dataclass(frozen=True)
class Holder:
    p: Pt
    q: tuple[Zed, ...] = ()


@dataclass
class Loose:
    v: int


class Named(NamedTuple):
    v: int


@dataclass(frozen=False)
class NotFrozen:
    v: int
