from .a import _secret
from gmid_engine.core import a as amod
import gmid_engine.core.a


def entry():
    amod._secret()
    return gmid_engine.core.a._secret, _secret
