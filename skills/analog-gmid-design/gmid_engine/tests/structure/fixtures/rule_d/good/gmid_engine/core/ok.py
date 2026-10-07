def derive_scale():
    return None


def entry(x, items):
    a = 0 + 1 - 1 + 0.0 + 1.0
    b = 2 * x + x ** 2 + x / 2
    b += 2
    c = items[3] + items[-2]
    d = items[1:5]
    e = items[:, 2]
    f = 7 * x  # derive: derive_scale
    return a, b, c, d, e, f
