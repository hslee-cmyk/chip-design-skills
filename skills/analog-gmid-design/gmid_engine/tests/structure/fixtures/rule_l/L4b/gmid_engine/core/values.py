from dataclasses import dataclass


_OUT = ("listed",)


@dataclass(frozen=True)
class Row:
    used: float
    via_attr: float
    listed: float
