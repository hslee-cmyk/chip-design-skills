def check(ms, pins):
    return sorted(ms, key=lambda m: (pins[m]["g"], pins[m]["s"]))
