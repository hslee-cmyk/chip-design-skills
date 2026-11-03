import dataclasses
from dataclasses import dataclass, field


@dataclass
class Rec:
    a: dict = field(default_factory=dict)
    b: list = dataclasses.field(default_factory=list)
    c: set = field(default_factory=set)
    d: int = field(default=0)
    e: tuple = field(default_factory=tuple)


def build():
    return field(default_factory=dict)
