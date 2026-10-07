def entry(f):
    try:
        f()
    except ValueError:
        pass
    try:
        f()
    except (KeyError, TypeError) as e:
        return e
