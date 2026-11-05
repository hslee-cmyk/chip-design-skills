def canon(x):
    return tuple(sorted(x))


def check(simple, g, s, n):
    return simple.setdefault(canon((g, s)), n)


def edges(tree, n):
    out = {}
    for g, s in tree:
        out[(canon(g), canon(s))] = n
    return out
