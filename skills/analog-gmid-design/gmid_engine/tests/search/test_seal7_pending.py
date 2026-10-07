"""CONTRACT 3.3·4절 `seal_status` -- 봉인 7 대기 스위치 표.

입력: (a) 손으로 만든 `SealReport`/`DcEvaluation`(sizing 공개 값 형식), (b) toy LUT 두 벌로 실제 `size_and_seal` 결과
(VDSAT 열 있음 -> 봉인, 없음 -> 봉인 7 만 undefined). 기대 상태는 report 항목을 test 가 직접 읽어 표에 대입한다.
"""
import pytest

from gmid_engine.search import (
    STATUS_PENDING_SEAL7,
    STATUS_SEALED,
    STATUS_UNDEFINED,
    seal_status,
)
from gmid_engine.sizing import (
    REASON_VDSAT_MISSING,
    REPORT_SEALED,
    REPORT_UNDEFINED,
    REPORT_VIOLATED,
    DcEvaluation,
    SealItem,
    SealReport,
    SealedSnapshot,
    size_and_seal,
)

from .conftest import build_case, circuit_c, theta_r4c


def _items(undef=(), fail=(), reason7=REASON_VDSAT_MISSING):
    out = []
    for n in range(1, 9):
        if n in fail:
            out.append(SealItem(n, "fail", 2.0, 1.0, 2.0))
        elif n in undef:
            det = (("n_checked", 1), ("n_undefined", 1), ("reason", reason7)) if n == 7 else (("n_checked", 1),)
            out.append(SealItem(n, "undefined", detail=det))
        else:
            out.append(SealItem(n, "pass", 0.0, 1.0, 0.0))
    return tuple(out)


def test_hand_table():
    rep_ok = SealReport(_items(), REPORT_SEALED)
    assert seal_status(DcEvaluation(None, rep_ok, SealedSnapshot(None, rep_ok))) == STATUS_SEALED
    rep_p = SealReport(_items(undef=(7,)), REPORT_UNDEFINED)
    assert seal_status(DcEvaluation(None, rep_p, None)) == STATUS_PENDING_SEAL7
    rep_other = SealReport(_items(undef=(7,), reason7="something_else"), REPORT_UNDEFINED)
    assert seal_status(DcEvaluation(None, rep_other, None)) == STATUS_UNDEFINED
    rep_two = SealReport(_items(undef=(3, 7)), REPORT_UNDEFINED)
    assert seal_status(DcEvaluation(None, rep_two, None)) == STATUS_UNDEFINED
    rep_3 = SealReport(_items(undef=(3,)), REPORT_UNDEFINED)
    assert seal_status(DcEvaluation(None, rep_3, None)) == STATUS_UNDEFINED


def test_violated_is_value_error():
    rep = SealReport(_items(fail=(6,)), REPORT_VIOLATED)
    with pytest.raises(ValueError):
        seal_status(DcEvaluation(None, rep, None))


@pytest.mark.parametrize("bad", [None, "sealed", 3])
def test_not_dc_evaluation_is_type_error(bad):
    with pytest.raises(TypeError):
        seal_status(bad)


def test_sealed_snapshot_itself_is_type_error():
    rep = SealReport(_items(), REPORT_SEALED)
    with pytest.raises(TypeError):
        seal_status(SealedSnapshot(None, rep))


def _report_rows(report):
    return {it.item: (it.status, dict(it.detail).get("reason")) for it in report.items}


def test_real_evaluations(tmp_path, lut_sealed, lut_pending):
    """VDSAT 열 있는 LUT: 1~8 pass -> SealedSnapshot -> sealed. 열 없는 LUT: 7 만 undefined + reason -> pending."""
    th = theta_r4c()
    c1 = build_case(tmp_path / "a", circuit_c(), lut_sealed)
    ev1 = size_and_seal(c1.dc, th)
    rows1 = _report_rows(ev1.report)
    assert all(s == "pass" for s, _ in rows1.values()) and ev1.sealed is not None
    assert seal_status(ev1) == STATUS_SEALED
    c2 = build_case(tmp_path / "b", circuit_c(), lut_pending)
    ev2 = size_and_seal(c2.dc, th)
    rows2 = _report_rows(ev2.report)
    undef = [n for n, (s, _) in rows2.items() if s == "undefined"]
    assert undef == [7] and rows2[7][1] == REASON_VDSAT_MISSING and ev2.sealed is None
    assert seal_status(ev2) == STATUS_PENDING_SEAL7
