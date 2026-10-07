def run(f, g):
    try:
        f()
    except Exception:
        return None
    try:
        g()
    except BaseException:
        return None
