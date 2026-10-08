"""search CONTRACT 3.25 [r12] `canonical_row_key(sctx) -> key 함수(행 이름)`.

oracle (d) 계약 문장: key = (접두, 소자 구조 색 `dc_colour` 또는 -1, 나머지 이름), 접두 순서는 사전식, 이름 치환 σ 에 대해 정렬 결과가 σ 로 옮겨진다.
소자 dc_colour 는 스냅샷 입력 열에서 읽는다. 행 이름은 test 가 만든 합성 입력(구성 (a)).
"""
from __future__ import annotations

import random

import pytest

from gmid_engine.search import canonical_row_key

from .canon_cases import C_BOX, SYM_ELEMENTS, colour_maps, make_case, rename_doc, sym_doc

PREFIXES = ("w_min", "seal6_bulk", "inversion_floor", "current_cone")
MOS = ("M1", "M2", "M3", "M4", "M5")


def _sym(tmp, lut, doc=None, sig=None):
    sig = sig or {}
    f = lambda n: sig.get(n, n)                                            # noqa: E731
    return make_case(tmp, doc or sym_doc(), lut, elements=tuple((f(n), k, v) for n, k, v in SYM_ELEMENTS),
                     boxes={f("CL1"): C_BOX, f("CL2"): C_BOX})


def _rows(f=lambda n: n):
    rows = ["%s:%s" % (p, f(m)) for p in PREFIXES for m in MOS]
    rows += ["ss:0:gain_ss_db", "ss:1:pm_deg", "spec:0:power_dc_w<="]
    return rows


def test_device_rows_ordered_by_prefix_then_colour(tmp_path, lut_sealed):
    case = _sym(tmp_path, lut_sealed)
    dv, _ = colour_maps(case.dc)
    rows = _rows()
    random.Random(3).shuffle(rows)
    got = sorted(rows, key=canonical_row_key(case.sctx))
    prefixes = [r.split(":", 1)[0] for r in got]
    assert prefixes == sorted(prefixes)                                    # 접두 사전식
    for p in PREFIXES:
        devs = [r.split(":", 1)[1] for r in got if r.split(":", 1)[0] == p]
        assert [dv[d] for d in devs] == sorted(dv[d] for d in devs)        # 같은 접두 안 = dc_colour 오름차순
        assert len(set(dv[d] for d in devs)) == len(devs)                  # 색이 정점마다 유일 -> 이름이 순서를 정하지 않는다


def test_metric_rows_keep_number_order(tmp_path, lut_sealed):
    case = _sym(tmp_path, lut_sealed)
    k = canonical_row_key(case.sctx)
    assert sorted(["ss:1:pm_deg", "ss:0:gain_ss_db"], key=k) == ["ss:0:gain_ss_db", "ss:1:pm_deg"]


def test_unknown_device_sorts_as_minus_one(tmp_path, lut_sealed):
    """dc_colour 가 없는 이름 -> -1(색 ≥ 0 인 소자보다 앞)."""
    case = _sym(tmp_path, lut_sealed)
    got = sorted(["w_min:M3", "w_min:Nope", "w_min:M1"], key=canonical_row_key(case.sctx))
    assert got[0] == "w_min:Nope"


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_renaming_transports_sorted_rows(tmp_path, lut_sealed, seed):
    """이름 치환 σ: σ 로 옮긴 행 이름을 새 컨텍스트 키로 정렬한 결과 = 원래 정렬 결과를 σ 로 옮긴 것(τ 대응 -- 궤도 구성원은 색 짝)."""
    names = ["M1", "M2", "M3", "M4", "M5", "CL1", "CL2", "inp", "inn", "o1", "o2", "t", "vb", "pb"]
    new = ["r%02d" % i for i in range(len(names))]
    random.Random(seed).shuffle(new)
    sig = dict(zip(names, new))
    a = _sym(tmp_path / "a", lut_sealed)
    b = _sym(tmp_path / "b", lut_sealed, doc=rename_doc(sym_doc(), sig, "hand_sym_rows_r%d" % seed), sig=sig)
    dva, _ = colour_maps(a.dc)
    dvb, _ = colour_maps(b.dc)
    ra = sorted(_rows(), key=canonical_row_key(a.sctx))
    rb = sorted(_rows(lambda n: sig[n]), key=canonical_row_key(b.sctx))

    def shape(rows, dv):
        out = []
        for r in rows:
            p, rest = r.split(":", 1)
            out.append((p, dv[rest]) if rest in dv else (p, rest))
        return out
    assert shape(ra, dva) == shape(rb, dvb)
