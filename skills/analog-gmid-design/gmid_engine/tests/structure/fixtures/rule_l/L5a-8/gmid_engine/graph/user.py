def check(simple, g, s, n):
    return simple.setdefault(tuple(sorted((g, s))), n)
