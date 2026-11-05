from ..graph.blk import blk


def run_stage_a(snapshot, registry):
    snapshot = blk(snapshot)
    return (
        registry.column("zzz", "alpha"),
        registry.value("zzz", "k", "alpha"),
        registry.field("zzz", "k", "alpha"),
    )
