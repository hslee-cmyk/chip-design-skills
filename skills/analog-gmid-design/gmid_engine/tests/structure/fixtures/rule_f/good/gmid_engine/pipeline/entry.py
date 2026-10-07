def run(f):
    try:
        f()
    except Exception:
        return None
