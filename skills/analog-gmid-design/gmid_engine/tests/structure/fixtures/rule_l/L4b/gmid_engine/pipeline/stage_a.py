from ..core.values import Row


def run_stage_a(snapshot):
    row = Row(used=1.0, via_attr=2.0, listed=3.0)
    return row.used, getattr(row, "via_attr")
