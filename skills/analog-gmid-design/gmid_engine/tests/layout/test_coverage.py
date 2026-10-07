"""layout/coverage.py -- `check_stick_diagram_coverage`(+`CoverageVerdict`) 복사. 기대값: 손계산(집합 차) + 옛 SD 대조."""
from __future__ import annotations

import pytest

from gmid_engine.layout.coverage import CoverageVerdict, check_stick_diagram_coverage

CASES = [
    (["M1", "M2", "M3"], {"r0": ["M1", "M2"], "r1": ["M3"]}, True, set()),
    (["M1", "M2", "M3"], {"r0": ["M1"], "r1": []}, False, {"M2", "M3"}),
    ({"M1"}, {}, False, {"M1"}),
    ([], {"r0": ["X"]}, True, set()),                 # 행에만 있는 이름은 missing 이 아니다
    (["M1", "M1"], {"r0": ["M1"], "r1": ["M1"]}, True, set()),
]


@pytest.mark.parametrize("sized,rows,ok,missing", CASES)
def test_hand(sized, rows, ok, missing):
    v = check_stick_diagram_coverage(sized, rows)
    assert isinstance(v, CoverageVerdict)
    assert v.ok is ok
    assert v.missing == missing


@pytest.mark.parametrize("sized,rows,ok,missing", CASES)
def test_same_as_oracle(sized, rows, ok, missing, sd, serialize):
    assert serialize(check_stick_diagram_coverage(sized, rows)) == serialize(sd.check_stick_diagram_coverage(sized, rows))
