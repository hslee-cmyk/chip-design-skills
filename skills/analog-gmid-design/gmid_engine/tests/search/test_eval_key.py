"""CONTRACT 3.2 `eval_key`: 키 정렬 θ 쌍만, 값마다 float.hex(1 ulp 다르면 다른 키)."""
import math

import pytest

from gmid_engine.search import EvalKey, eval_key

TH = ((("L", "M1"), 1e-6), (("current", "M2"), 1e-5), (("y", "out"), 0.5))


def test_fields_and_hex():
    k = eval_key("ctx", "sch", TH, (0, 1), None)
    assert isinstance(k, EvalKey)
    assert (k.context_fp, k.schema_fp, k.cells, k.w_fixed_fp) == ("ctx", "sch", (0, 1), None)
    assert tuple(k.theta_hex) == tuple(float(v).hex() for _, v in TH)


def test_one_ulp_is_a_different_key():
    a = eval_key("c", "s", TH, (0,), None)
    th2 = list(TH)
    th2[1] = (th2[1][0], math.nextafter(th2[1][1], 1.0))
    b = eval_key("c", "s", tuple(th2), (0,), None)
    assert a != b
    same = eval_key("c", "s", tuple(TH), (0,), None)
    assert a == same and hash(a) == hash(same)


@pytest.mark.parametrize("field", ["context_fp", "schema_fp", "cells", "w_fixed_fp"])
def test_other_fields_separate_keys(field):
    args = {"context_fp": "c", "schema_fp": "s", "cells": (0,), "w_fixed_fp": None}
    a = eval_key(args["context_fp"], args["schema_fp"], TH, args["cells"], args["w_fixed_fp"])
    args[field] = {"context_fp": "c2", "schema_fp": "s2", "cells": (1,), "w_fixed_fp": "w"}[field]
    b = eval_key(args["context_fp"], args["schema_fp"], TH, args["cells"], args["w_fixed_fp"])
    assert a != b


def test_unsorted_theta_rejected():
    with pytest.raises(ValueError):
        eval_key("c", "s", tuple(reversed(TH)), (0,), None)


def test_non_pair_theta_rejected():
    with pytest.raises(ValueError):
        eval_key("c", "s", (1.0, 2.0), (0,), None)


@pytest.mark.parametrize("bad", [
    ([("L", "M1"), 1e-6],),                         # list 쌍
    ((("L", "M1"), 1e-6, 0.0),),                     # 원소 수 3
])
def test_r5_malformed_pairs_are_value_error(bad):
    """r5: ((kind, key), 값) 2-tuple 들이 아니면(쌍 아님·원소 수 ≠ 2·list 쌍) ValueError."""
    with pytest.raises(ValueError):
        eval_key("c", "s", bad, (0,), None)
