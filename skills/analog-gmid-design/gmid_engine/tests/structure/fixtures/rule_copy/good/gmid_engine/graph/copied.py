"""copied definitions (fixture)."""

LIMITS = {"A": 3, "B": 4}


def scan(xs):
    if len(xs) > 40:
        return "A"
    return xs[0]


def local_tool(xs):
    return len(xs) - 1
