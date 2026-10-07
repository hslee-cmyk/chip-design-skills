import builtins


def entry(f):
    try:
        f()
    except:
        pass
    try:
        f()
    except Exception:
        pass
    try:
        f()
    except (ValueError, BaseException):
        pass
    try:
        f()
    except builtins.Exception:
        pass
