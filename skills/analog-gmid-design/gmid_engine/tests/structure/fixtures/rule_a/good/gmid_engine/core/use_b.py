from . import _helpers_shared


def use_b(x):
    return _helpers_shared.inner(_helpers_shared.shared(x))
