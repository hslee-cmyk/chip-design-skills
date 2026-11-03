import collections
from collections import OrderedDict
from weakref import WeakValueDictionary

A = BoundedLRU(3)
B = LutMemo()
C = OrderedDict()
D = WeakValueDictionary()
E = collections.OrderedDict()
F = dict()

if True:
    G = BoundedLRU(1)

try:
    H = LutMemo()
except ValueError:
    pass

with open("x") as fh:
    I = OrderedDict()

for _i in range(1):
    J = WeakValueDictionary()

match _i:
    case 0:
        M = LutMemo()


def fn():
    K = BoundedLRU(1)
    return K


class Q:
    L = LutMemo()
