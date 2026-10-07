from ._helpers_shared import inner, shared


def use_a(x):
    return inner(shared(x))
