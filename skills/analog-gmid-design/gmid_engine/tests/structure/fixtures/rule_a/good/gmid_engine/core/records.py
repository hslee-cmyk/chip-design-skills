from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


@dataclass(frozen=True)
class Point:
    """좌표 한 점."""
    x: float
    y: float

    def __post_init__(self):
        return None

    @property
    def norm1(self):
        return abs(self.x) + abs(self.y)

    @classmethod
    def from_tuple(cls, t):
        return cls(*t)


class Kind(Enum):
    N = "n"
    P = "p"


class Pair(NamedTuple):
    first: str
    second: str


class BadInput(ValueError):
    pass


class Deeper(BadInput):
    def __str__(self):
        return "deeper"
