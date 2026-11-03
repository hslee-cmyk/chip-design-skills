from gmid_engine import pkg_mod
from gmid_engine.pkg_mod import module_fn


def module_level(a):
    return a


def ok(memo, p):
    memo.call(module_fn, 1)
    memo.call(pkg_mod.fn, 1)
    p.memo.call(module_fn, 2)
    memo.call(module_level, 3)


def bad_noarg(memo):
    return memo.call()


def bad_lambda(memo):
    return memo.call(lambda: 1)


def bad_partial(memo):
    return memo.call(partial(module_fn, 1))


def bad_param(memo, fn):
    return memo.call(fn, 1)


def bad_param_attr(memo, obj):
    return memo.call(obj.method, 1)


def bad_local(memo):
    helper = module_fn
    return memo.call(helper, 1)


def bad_nested(memo):
    def inner(x):
        return x

    return memo.call(inner, 1)


def bad_expr_memo(p):
    return p.memo.call(lambda: 2)
