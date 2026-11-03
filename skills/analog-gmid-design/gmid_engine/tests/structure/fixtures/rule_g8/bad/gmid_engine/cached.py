import functools
from functools import cached_property


class Box:
    @cached_property
    def a(self):
        return 1

    @functools.cached_property
    def b(self):
        return 2

    @property
    def c(self):
        return 3
