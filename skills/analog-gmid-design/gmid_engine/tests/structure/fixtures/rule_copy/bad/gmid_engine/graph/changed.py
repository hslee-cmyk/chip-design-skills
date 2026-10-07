"""registered copy whose body was edited (fixture)."""


def renamed(xs):
    acc = 0
    for x in xs:
        acc += x * 5
    return acc
