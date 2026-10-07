from .memo import compute_block


@compute_block("gain")
def block_gain(ctx, snap):
    return ctx, snap


def standalone(x):
    return x
