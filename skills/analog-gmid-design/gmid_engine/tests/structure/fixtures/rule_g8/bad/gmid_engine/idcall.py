def f(x):
    return id(x)


class C:
    def m(self, x):
        return [id(y) for y in x]


key = id(3)
