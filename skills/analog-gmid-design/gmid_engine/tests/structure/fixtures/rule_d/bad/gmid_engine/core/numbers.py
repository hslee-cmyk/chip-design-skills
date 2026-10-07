def derive_gain():
    return None


def entry(x, n=10):
    if x == 2:
        return 3
    y = x * 0.5
    z = x - 2
    w = -2 * x
    v = 1e-6 * x  # derive: no_such_function
    u = 4 * x  # derive: derive_gain
    c = 2j
    return x[3], y, z, w, v, u, c, n
