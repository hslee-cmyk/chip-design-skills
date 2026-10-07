from ._helpers_lonely import shared
from ._helpers_alias import impl


def user_one(x):
    return impl(shared(x))
