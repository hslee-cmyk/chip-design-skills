from collections import defaultdict
from functools import lru_cache
import functools

CACHE = {}
TABLE: list = []
SEEN = set()
BY_KEY = defaultdict(list)
SQUARES = {k: k for k in ()}
PAIR = ({}, ())
if CACHE is not None:
    LATE = []
try:
    import json
except ImportError:
    BACKUP = dict()


@lru_cache(maxsize=None)
def lookup(x):
    return x


@functools.cache
def lookup2(x):
    global CACHE
    return x, json
