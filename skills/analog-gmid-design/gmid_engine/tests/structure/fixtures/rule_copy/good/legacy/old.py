"""old engine source (fixture original, outside gmid_engine)."""


def helper(v):
    return v + 1


LIMITS = {"A": 3, "B": 4}


def scan(xs):
    if len(xs) > 40:
        return "A"
    return xs[0]


def renamed(xs):
    total = 0
    for x in xs:
        total += x * 5
    return total


def miscounted(xs):
    return xs[:] if len(xs) < 12 else None
