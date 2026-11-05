def _key(x):
    return x


def run_stage_a(snapshot):
    return sorted(snapshot, key=_key)
