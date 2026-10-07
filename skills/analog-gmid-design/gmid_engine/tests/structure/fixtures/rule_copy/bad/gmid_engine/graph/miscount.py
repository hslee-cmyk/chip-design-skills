"""registered copy whose literal list is recorded wrong (fixture)."""


def miscounted(xs):
    return xs[:] if len(xs) < 12 else None
