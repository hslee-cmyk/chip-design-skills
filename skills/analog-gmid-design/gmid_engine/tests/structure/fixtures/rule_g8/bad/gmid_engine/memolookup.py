def a(memo, k):
    return memo.lookup(k)


def b(memo, k):
    return memo.lookup_persistent(k)


def c(p, k):
    return p.memo.lookup(k)


def d(p, k):
    return p.memo.lookup_persistent(k)


def e(memo, k):
    return memo.lookup_other(k)


def f(p, k):
    return p.lookup(k)


def g(memo, k):
    return memo.call(KEY, k)
