import functools
from functools import cache, lru_cache


def f(x):
    return x


g = lru_cache(maxsize=1)(f)
h = functools.lru_cache(maxsize=2)(f)
k = cache(f)
m = functools.cache(f)
n = obj.cache(f)


@lru_cache(maxsize=3)
def deco(x):
    return x


def user(obj):
    return obj.cache(1)


class C:
    def meth(self):
        return lru_cache(maxsize=4)
