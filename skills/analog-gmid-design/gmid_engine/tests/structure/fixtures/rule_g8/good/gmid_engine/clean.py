from gmid_engine import pkg_mod
from gmid_engine.pkg_mod import module_fn


class Plain:
    def __init__(self, x):
        self.a = None
        self.b = ()
        self.c = tuple(x)
        self.d = frozenset(x)
        self.e = (1, 2)
        self.table = x

    def put(self, k, v):
        self.table[k] = v


def local():
    d = {}
    return d


other = Plain(1)
other.a = {}


def use(memo):
    memo.call(module_fn, 1)
    return memo.call(pkg_mod.fn, 1)


def not_id(x):
    return x.id(1)
