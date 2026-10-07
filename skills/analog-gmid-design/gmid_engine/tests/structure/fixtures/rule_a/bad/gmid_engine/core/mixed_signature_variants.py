from .memo import compute_block


@compute_block("gain")
def block_gain(ctx, snap):
    return ctx, snap


@compute_block("power")
def block_power(ctx, snap):
    return ctx, snap


@compute_block("area")
def block_area(ctx, snap, extra):
    return ctx, snap, extra
