from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: float

    def shifted(self, d):
        return Point(self.x + d)


@dataclass(frozen=True)
class Box:
    lo: float
