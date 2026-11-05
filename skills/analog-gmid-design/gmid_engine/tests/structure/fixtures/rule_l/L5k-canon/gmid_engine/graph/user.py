def canon(x):
    return tuple(sorted(x))


def check(simple, g, s, n):
    return simple.setdefault(canon((g, s)), n)
