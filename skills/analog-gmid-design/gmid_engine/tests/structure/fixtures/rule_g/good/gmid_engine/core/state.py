from types import MappingProxyType

__all__ = ["lookup"]
NAMES = ("a", "b")
KINDS = frozenset({"nmos", "pmos"})
TABLE = MappingProxyType({"x": "y"})
EMPTY = ()


def lookup(x):
    local = {}
    local[x] = [x]
    return local, NAMES, KINDS, TABLE, EMPTY


class Holder:
    items = ()
