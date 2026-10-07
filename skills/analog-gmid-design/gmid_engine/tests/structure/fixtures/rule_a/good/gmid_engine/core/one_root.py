class Result:
    pass


def run(x):
    return Result() if _check(x) else None


def _check(x):
    return x
