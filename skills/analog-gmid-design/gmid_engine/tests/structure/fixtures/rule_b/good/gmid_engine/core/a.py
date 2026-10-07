from . import _helpers_text
from ._helpers_text import shared


class Box:
    def __init__(self):
        self._value = None

    def get(self):
        return self._value


def entry():
    return _helpers_text.shared(shared(Box().get())), __name__
