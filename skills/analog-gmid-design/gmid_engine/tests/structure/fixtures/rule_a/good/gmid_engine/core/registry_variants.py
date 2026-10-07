from .memo import compute_block


@compute_block("gain")
def block_gain(ctx, snap):
    return _common(ctx, snap)


@compute_block("power")
def block_power(ctx, snap):
    return _common(ctx, snap)


@compute_block("area")
def block_area(ctx, snap):
    return _common(ctx, snap)


def _common(ctx, snap):
    return ctx, snap
