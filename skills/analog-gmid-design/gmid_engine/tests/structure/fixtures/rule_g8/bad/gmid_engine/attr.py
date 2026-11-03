class Holder:
    def __init__(self, x):
        self.a = {}
        self.b: dict = {}
        self.c = [1, 2]
        self.d = {k: 1 for k in x}
        self.e = ({}, 1)
        self.f = defaultdict(list)
        self.g = None
        self.h = ()
        self.i = tuple(x)
        self.j = frozenset(x)
        self.k = (1, 2)
        self.a2 = x

    def run(self, k, v):
        self.a[k] = v

        def inner():
            self.z = set()

        return inner

    @classmethod
    def make(cls):
        cls.reg = []
        return cls


class Outer:
    class Inner:
        def m(self):
            self.q = bytearray()


obj = Holder(1)
obj.a = {}


def free(x):
    d = {}
    x.a = {}
    return d
