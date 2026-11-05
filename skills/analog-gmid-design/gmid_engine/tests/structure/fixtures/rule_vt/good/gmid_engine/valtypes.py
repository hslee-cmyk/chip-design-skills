import dataclasses
from dataclasses import dataclass


@dataclass(frozen=True)
class Pt:
    x: float


@dataclasses.dataclass(frozen=True)
class Zed:
    z: float
