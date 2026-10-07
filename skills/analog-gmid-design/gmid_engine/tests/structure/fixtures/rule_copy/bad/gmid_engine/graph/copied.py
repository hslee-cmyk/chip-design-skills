"""copied definitions next to new code (fixture)."""

LIMITS = {"A": 3, "B": 4}


def scan(xs):
    if len(xs) > 40:
        return "A"
    return xs[0]


def extra(xs):
    return xs * 7 if xs else {"B": 0}


CACHE = {}
