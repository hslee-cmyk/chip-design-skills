from ..core.values import Row


def run_stage_a(snapshot):
    row = Row(used=1.0, unused=2.0)
    return row.used
