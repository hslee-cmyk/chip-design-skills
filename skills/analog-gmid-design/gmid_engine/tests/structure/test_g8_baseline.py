"""GL-1 기준선과 래칫: baseline_doc / dump_baseline / load_baseline / ratchet, 진짜 트리 래칫 test.

oracle 종류 (d): interface card 20261103-gl1 §3의 선언(행 키 = (kind, path, detail), 줄 번호는 키가 아님, count = 같은 키 수).
기대 doc·행은 fixtures/rule_g8/bad 의 edges.py·idcall.py 위반을 손으로 읽어 적었다.
  edges.py   1 줄·3 줄  id(...) 둘 -> 키 (g8_id_call, edges.py, <module>) count 2
  idcall.py  2 줄 f / 7 줄 C.m / 10 줄 <module> -> 각 count 1
기준선 파일 S/g8_baseline.json 은 이 파일 작성 주체도 만들지 않는다. 진짜 트리 test 는 그 파일이 없으면 실패한다(skip·xfail 금지).
"""
from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
BASELINE = HERE / "g8_baseline.json"
SHA = "a" * 40

ID = "20261103-gl1"
HAND_ROWS = [
    {"kind": "g8_id_call", "path": "edges.py", "detail": "<module>", "count": 2},
    {"kind": "g8_id_call", "path": "idcall.py", "detail": "<module>", "count": 1},
    {"kind": "g8_id_call", "path": "idcall.py", "detail": "C.m", "count": 1},
    {"kind": "g8_id_call", "path": "idcall.py", "detail": "f", "count": 1},
]
HAND_DOC = {"id": ID, "base_commit": SHA, "rows": HAND_ROWS}
SUBSET = ("edges.py", "idcall.py")


def _subset(violations):
    return [v for v in violations if v.path in SUBSET]


@pytest.fixture
def sub_violations(checks, fixture_tree):
    _, v = checks.check_g8(fixture_tree("rule_g8", "bad"))
    sub = _subset(v)
    assert len(sub) == 5, [str(x) for x in sub]          # edges 2 + idcall 3 (소스를 손으로 센 값)
    return sub


def _write(tmp_path, name, obj):
    p = tmp_path / name
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
    return p


# ---------------------------------------------------------------- baseline_doc

def test_baseline_doc_groups_by_key_and_sorts(checks, sub_violations):
    doc = checks.baseline_doc(sub_violations, ID, SHA)
    assert doc == HAND_DOC


def test_baseline_doc_ignores_input_order(checks, sub_violations):
    a = checks.dump_baseline(checks.baseline_doc(sub_violations, ID, SHA))
    b = checks.dump_baseline(checks.baseline_doc(list(reversed(sub_violations)), ID, SHA))
    assert a == b


def test_baseline_doc_row_key_excludes_line(checks, fixture_tree, tmp_path):
    """같은 키 둘(edges.py 1·3 줄)이 줄이 달라도 한 행 count 2."""
    _, v = checks.check_g8(fixture_tree("rule_g8", "bad"))
    edges = [x for x in v if x.path == "edges.py"]
    assert sorted(x.line for x in edges) == [1, 3]
    doc = checks.baseline_doc(edges, ID, SHA)
    assert doc["rows"] == [HAND_ROWS[0]]


def test_baseline_doc_rejects_empty_record_id(checks, sub_violations):
    with pytest.raises(ValueError):
        checks.baseline_doc(sub_violations, "", SHA)


@pytest.mark.parametrize("sha", [
    "",
    "a" * 39,
    "a" * 41,
    "A" * 40,                  # 대문자 hex 는 40자리 소문자 hex 가 아님
    "g" * 40,                  # hex 아님
    "abc",
])
def test_baseline_doc_rejects_bad_base_commit(checks, sub_violations, sha):
    with pytest.raises(ValueError):
        checks.baseline_doc(sub_violations, ID, sha)


# ---------------------------------------------------------------- dump_baseline

def test_dump_baseline_format(checks):
    raw = checks.dump_baseline(HAND_DOC)
    assert isinstance(raw, bytes)
    text = raw.decode("utf-8")
    assert b"\r" not in raw
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert json.loads(text) == HAND_DOC
    # 최상위 키는 정렬 순서로 나온다
    top = json.loads(text, object_pairs_hook=lambda pairs: [k for k, _ in pairs])
    assert top == ["base_commit", "id", "rows"]


def test_dump_baseline_row_keys_sorted(checks):
    raw = checks.dump_baseline(HAND_DOC).decode("utf-8")
    order = []

    def hook(pairs):
        order.append([k for k, _ in pairs])
        return dict(pairs)

    json.loads(raw, object_pairs_hook=hook)
    assert ["count", "detail", "kind", "path"] in order
    assert all(o == sorted(o) for o in order), order


def test_dump_baseline_same_doc_same_bytes(checks):
    a = checks.dump_baseline(copy.deepcopy(HAND_DOC))
    b = checks.dump_baseline(copy.deepcopy(HAND_DOC))
    assert a == b


def test_dump_baseline_keeps_utf8_detail(checks):
    doc = {"id": ID, "base_commit": SHA,
           "rows": [{"kind": "g8_id_call", "path": "x.py", "detail": "한글.m", "count": 1}]}
    raw = checks.dump_baseline(doc)
    assert json.loads(raw.decode("utf-8")) == doc


# ---------------------------------------------------------------- load_baseline

def test_load_baseline_roundtrip(checks, tmp_path):
    p = tmp_path / "b.json"
    p.write_bytes(checks.dump_baseline(HAND_DOC))
    assert checks.load_baseline(p) == HAND_DOC


def test_load_baseline_missing_file(checks, tmp_path):
    with pytest.raises(FileNotFoundError):
        checks.load_baseline(tmp_path / "nope.json")


def _row(**over):
    r = {"kind": "g8_id_call", "path": "x.py", "detail": "f", "count": 1}
    r.update(over)
    return r


def _doc(**over):
    d = {"id": ID, "base_commit": SHA, "rows": [_row()]}
    d.update(over)
    return d


def _drop(d, key):
    d = dict(d)
    del d[key]
    return d


def _row_without(key):
    r = _row()
    del r[key]
    return r


MALFORMED = {
    "not_json": "{not json",
    "empty_text": "",
    "top_list": [],
    "top_string": '"x"',
    "top_null": None,
    "missing_id": _drop(_doc(), "id"),
    "missing_rows": _drop(_doc(), "rows"),
    "missing_base_commit": _drop(_doc(), "base_commit"),
    "extra_top_key": dict(_doc(), extra=1),
    "id_empty": _doc(id=""),
    "base_commit_short": _doc(base_commit="a" * 39),
    "base_commit_long": _doc(base_commit="a" * 41),
    "base_commit_upper": _doc(base_commit="A" * 40),
    "base_commit_nonhex": _doc(base_commit="z" * 40),
    "base_commit_empty": _doc(base_commit=""),
    "row_missing_kind": _doc(rows=[_row_without("kind")]),
    "row_missing_count": _doc(rows=[_row_without("count")]),
    "row_extra_key": _doc(rows=[dict(_row(), extra=1)]),
    "count_bool": _doc(rows=[_row(count=True)]),
    "count_zero": _doc(rows=[_row(count=0)]),
    "count_negative": _doc(rows=[_row(count=-2)]),
    "count_float": _doc(rows=[_row(count=1.5)]),
    "count_string": _doc(rows=[_row(count="1")]),
    "count_null": _doc(rows=[_row(count=None)]),
    "duplicate_key": _doc(rows=[_row(), _row(count=3)]),
}


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_load_baseline_rejects_malformed(checks, tmp_path, name):
    p = _write(tmp_path, "b.json", MALFORMED[name])
    with pytest.raises(ValueError, match="g8_baseline_malformed"):
        checks.load_baseline(p)


# ---------------------------------------------------------------- ratchet

def _ratchet(checks, v, doc):
    return checks.ratchet(v, doc)


def test_ratchet_equal_is_clean(checks, sub_violations):
    r = _ratchet(checks, sub_violations, HAND_DOC)
    assert r.new == ()
    assert r.stale == ()
    assert isinstance(r.new, tuple) and isinstance(r.stale, tuple)


def test_ratchet_ignores_line_shift(checks, fixture_tree, tmp_path):
    """줄 번호만 바뀌면 둘 다 빈 tuple. 복사본 소스 앞에 빈 줄을 넣어 줄을 민다."""
    dst = tmp_path / "gmid_engine"
    shutil.copytree(fixture_tree("rule_g8", "bad"), dst)
    for name in SUBSET:
        p = dst / name
        p.write_bytes(b"# shifted\n# shifted\n" + p.read_bytes())
    _, v0 = checks.check_g8(fixture_tree("rule_g8", "bad"))
    _, v1 = checks.check_g8(dst)
    s0 = sorted(x.line for x in _subset(v0))
    s1 = sorted(x.line for x in _subset(v1))
    assert s0 == [1, 2, 3, 7, 10]            # 소스를 손으로 읽은 줄
    assert s1 == [3, 4, 5, 9, 12]            # 줄이 실제로 밀렸다
    r = _ratchet(checks, _subset(v1), HAND_DOC)
    assert (r.new, r.stale) == ((), ())


def test_ratchet_count_above_baseline_is_new(checks, sub_violations):
    doc = copy.deepcopy(HAND_DOC)
    doc["rows"][0]["count"] = 1            # edges.py 현재 2, 기준선 1
    r = _ratchet(checks, sub_violations, doc)
    assert r.new == (("g8_id_call", "edges.py", "<module>", 1),)
    assert r.stale == ()


def test_ratchet_key_absent_from_baseline_is_new_with_current_count(checks, sub_violations):
    doc = copy.deepcopy(HAND_DOC)
    del doc["rows"][0]                      # edges.py 행 제거 -> 현재 수 2 가 n
    r = _ratchet(checks, sub_violations, doc)
    assert r.new == (("g8_id_call", "edges.py", "<module>", 2),)
    assert r.stale == ()


def test_ratchet_count_below_baseline_is_stale(checks, sub_violations):
    doc = copy.deepcopy(HAND_DOC)
    doc["rows"][0]["count"] = 5            # 현재 2, 기준선 5 -> 차이 3
    r = _ratchet(checks, sub_violations, doc)
    assert r.new == ()
    assert r.stale == (("g8_id_call", "edges.py", "<module>", 3),)


def test_ratchet_key_gone_is_stale_with_baseline_count(checks, sub_violations):
    doc = copy.deepcopy(HAND_DOC)
    doc["rows"].append({"kind": "g8_id_call", "path": "zzz.py", "detail": "gone", "count": 4})
    r = _ratchet(checks, sub_violations, doc)
    assert r.new == ()
    assert r.stale == (("g8_id_call", "zzz.py", "gone", 4),)


def test_ratchet_new_and_stale_together_sorted(checks, sub_violations):
    doc = copy.deepcopy(HAND_DOC)
    # idcall.py f 행과 C.m 행을 지움 -> 둘 다 new(n=1), 정렬은 (kind, path, detail): "C.m" < "f"
    doc["rows"] = [r for r in doc["rows"] if r["detail"] not in ("f", "C.m")]
    doc["rows"].append({"kind": "g8_id_call", "path": "aaa.py", "detail": "gone2", "count": 2})
    doc["rows"].append({"kind": "g8_id_call", "path": "zzz.py", "detail": "gone1", "count": 1})
    r = _ratchet(checks, sub_violations, doc)
    assert r.new == (
        ("g8_id_call", "idcall.py", "C.m", 1),
        ("g8_id_call", "idcall.py", "f", 1),
    )
    assert r.stale == (
        ("g8_id_call", "aaa.py", "gone2", 2),
        ("g8_id_call", "zzz.py", "gone1", 1),
    )


def test_ratchet_empty_violations_makes_everything_stale(checks):
    r = _ratchet(checks, [], HAND_DOC)
    assert r.new == ()
    assert r.stale == (
        ("g8_id_call", "edges.py", "<module>", 2),
        ("g8_id_call", "idcall.py", "<module>", 1),
        ("g8_id_call", "idcall.py", "C.m", 1),
        ("g8_id_call", "idcall.py", "f", 1),
    )


def test_ratchet_does_not_raise_on_empty_baseline(checks, sub_violations):
    doc = {"id": ID, "base_commit": SHA, "rows": []}
    r = _ratchet(checks, sub_violations, doc)
    assert r.new == (
        ("g8_id_call", "edges.py", "<module>", 2),
        ("g8_id_call", "idcall.py", "<module>", 1),
        ("g8_id_call", "idcall.py", "C.m", 1),
        ("g8_id_call", "idcall.py", "f", 1),
    )
    assert r.stale == ()


def test_ratchet_result_is_immutable(checks, sub_violations):
    r = _ratchet(checks, sub_violations, HAND_DOC)
    with pytest.raises(AttributeError):
        r.new = (("x", "y", "z", 1),)
    with pytest.raises(AttributeError):
        r.stale = ()


def test_ratchet_new_violation_added_to_tree_is_new(checks, fixture_tree, tmp_path):
    """기준선 밖 위반 추가 -> new."""
    dst = tmp_path / "gmid_engine"
    shutil.copytree(fixture_tree("rule_g8", "bad"), dst)
    p = dst / "idcall.py"
    p.write_bytes(p.read_bytes() + b"extra = id(4)\n")          # idcall.py <module> 2 건째
    _, v = checks.check_g8(dst)
    r = _ratchet(checks, _subset(v), HAND_DOC)
    assert r.new == (("g8_id_call", "idcall.py", "<module>", 1),)
    assert r.stale == ()


# ---------------------------------------------------------------- 진짜 트리

def test_rule_g8_baseline_ratchet(checks, engine_root, report, capsys):
    n8, v8 = checks.check_g8(engine_root)
    nv, vv = checks.check_value_types(engine_root)
    assert n8 >= 1
    assert nv >= 1
    doc = checks.load_baseline(BASELINE)         # 파일이 없으면 FileNotFoundError 로 실패(fail-closed)
    r = checks.ratchet(list(v8) + list(vv), doc)
    report(n8, len(v8) + len(vv))
    with capsys.disabled():
        print("\n[g8 ratchet] stale %d 건: %s" % (len(r.stale), list(r.stale)))
    assert r.new == (), "\n".join(str(x) for x in r.new)
