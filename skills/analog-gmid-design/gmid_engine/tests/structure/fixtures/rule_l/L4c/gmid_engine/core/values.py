from dataclasses import dataclass


@dataclass(frozen=True)
class Row:
    used: float
    inner: float

    def total(self):
        return self.inner
