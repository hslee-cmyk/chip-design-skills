class SealError(Exception):
    pass


class LutError(Exception):
    pass


def exit_code_for(e):
    return isinstance(e, SealError)


def normalized_margin(x):
    return x
