from dataclasses import dataclass


@dataclass(frozen=True)
class Row:
    used: float
    unused: float
