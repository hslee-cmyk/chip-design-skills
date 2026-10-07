"""CONTRACT §9 read_pdk_decl -- PDK 선언 파일에서 규칙 값을 원본(tlef·규칙표 csv)으로 계산한다.

독립 검증(작성자 ≠ 검증자): 기대값은 피검 함수를 부르지 않고 이 파일이 원본을 직접 읽어(정규식·csv 모듈) 규칙마다
손으로 쓴 식으로 다시 계산한다. 실패 표(9.3)의 이유 키는 조작한 임시 선언·원본 사본으로 실제 거부를 확인한다.
일반성: 다른 형식 인자(열 번호·절 정규식·단위 표)를 쓰는 가상 PDK 둘째 선언이 코드 변경 없이 동작한다.
"""
import copy
import csv
import dataclasses
import hashlib
import json
import math
import os
import re
import shutil
from pathlib import Path

import pytest

from gmid_engine.core import (
    BoundedLRU,
    PdkDecl,
    PdkQuantity,
    PdkRule,
    SchemaRejectedError,
    fp_of,
    read_pdk_decl,
    require_immutable,
)

SKILL_DIR = Path(__file__).resolve().parents[3]
SKY130_DECL = SKILL_DIR / "assets" / "sky130_pdk_decl.json"
REL = 1e-12

# §9.5: LayoutPdk.from_lut 위치 인자 순서(overhead, gap, dummy, tap, well)
PDK_RULE_QUANTITIES = ("finger_pitch_overhead_m", "row_gap_m", "dummy_w_m", "tap_w_m", "well_spacing_m")


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


SKY = _load_json(SKY130_DECL)


def _src_path(decl, name):
    return decl["pdk_root"] + "/" + decl["sources"][name]["path"]


_SKY_FILES_PRESENT = all(os.path.isfile(_src_path(SKY, n)) for n in SKY["sources"])
needs_sky130 = pytest.mark.skipif(not _SKY_FILES_PRESENT, reason="sky130 원본(C:/pdk) 없음 -- 환경 의존")


# ---------------------------------------------------------------- 독립 파서 (계약 9.1 문장 그대로)

def _sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


_LEF_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+([^\s;]+)\s*;\s*$")


def my_lef_rules(path, encoding):
    """줄에서 '#' 뒤를 버리고 `KEY 값 ;` 줄마다 규칙 KEY(단위 글자 "") -> {KEY: [(값 글자, 단위 글자, 행), ...]}."""
    out = {}
    with open(path, encoding=encoding) as f:
        for n, line in enumerate(f, 1):
            m = _LEF_LINE.match(line.split("#", 1)[0])
            if m:
                out.setdefault(m.group(1), []).append((m.group(2), "", n))
    return out


def my_csv_rules(path, src):
    """section 열이 정규식에 맞으면 접두 교체, 아니면 접두 있고 id 열 비지 않을 때 규칙 접두.id (행 = line_num)."""
    pat = re.compile(src["section_pattern"])
    out = {}
    prefix = None
    with open(path, encoding=src["encoding"], newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            def col(i):
                return row[i] if i < len(row) else ""
            m = pat.search(col(src["section_column"]))
            if m:
                prefix = m.group(1)
                continue
            rid = col(src["id_column"])
            if prefix is not None and rid != "":
                out.setdefault(prefix + "." + rid, []).append(
                    (col(src["value_column"]), col(src["unit_column"]), reader.line_num))
    return out


def my_rules(decl, name):
    src = decl["sources"][name]
    path = _src_path(decl, name)
    if src["format"] == "lef_statement":
        return my_lef_rules(path, src["encoding"])
    return my_csv_rules(path, src)


def my_rule_m(decl, source, rule_id):
    """원본에서 유일한 규칙 하나 -> (값 m, 값 글자, 단위 글자, 행)."""
    hits = my_rules(decl, source)[rule_id]
    assert len(hits) == 1, (rule_id, hits)
    text, unit, line = hits[0]
    return float(text) * decl["sources"][source]["units_m"][unit], text, unit, line


def reason(excinfo):
    return dict(excinfo.value.record.detail)["reason"]


# ---------------------------------------------------------------- sky130 손계산 (규칙마다 식을 손으로)

def _sky_expected():
    def lef(r):
        return my_rule_m(SKY, "tech_lef", r)[0]

    def per(r):
        return my_rule_m(SKY, "periphery_rules", r)[0]

    contact = max(per("poly.2"), per("licon.1") + 2 * per("licon.11"))
    return {
        "manufacturing_grid_m": lef("MANUFACTURINGGRID"),
        "finger_pitch_overhead_m": contact,
        "row_gap_m": max(per("difftap.3"), per("poly.8") + per("poly.2") + per("poly.8")),
        "dummy_w_m": per("poly.1a") + per("poly.7") + contact / 2,
        "tap_w_m": per("difftap.3") + max(per("difftap.1"), per("licon.1") + 2 * per("licon.7")),
        "well_spacing_m": max(per("nwell.2a") + 2 * per("difftap.8"), per("difftap.9") + per("difftap.8")),
    }


# 식에 나오는 규칙 -- 첫 등장 순, 중복 없음
SKY_RULE_ORDER = {
    "manufacturing_grid_m": ("MANUFACTURINGGRID",),
    "finger_pitch_overhead_m": ("poly.2", "licon.1", "licon.11"),
    "row_gap_m": ("difftap.3", "poly.8", "poly.2"),
    "dummy_w_m": ("poly.1a", "poly.7", "poly.2", "licon.1", "licon.11"),
    "tap_w_m": ("difftap.3", "difftap.1", "licon.1", "licon.7"),
    "well_spacing_m": ("nwell.2a", "difftap.8", "difftap.9"),
}

# §9.4 표의 값·행 번호
SKY_TABLE_VALUES = {
    "manufacturing_grid_m": 5e-9,
    "finger_pitch_overhead_m": 2.8e-7,
    "row_gap_m": 4.7e-7,
    "dummy_w_m": 5.4e-7,
    "tap_w_m": 6.8e-7,
    "well_spacing_m": 1.63e-6,
}
SKY_TABLE_LINES = {
    "MANUFACTURINGGRID": 29, "poly.2": 402, "licon.1": 624, "licon.11": 642, "difftap.3": 324, "poly.8": 408,
    "poly.1a": 400, "poly.7": 407, "difftap.1": 320, "licon.7": 637, "nwell.2a": 121, "difftap.8": 329,
    "difftap.9": 330,
}


@pytest.fixture(scope="module")
def sky_decl():
    if not _SKY_FILES_PRESENT:
        pytest.skip("sky130 원본 없음")
    return read_pdk_decl(str(SKY130_DECL), BoundedLRU(4))


@needs_sky130
def test_sky130_sources_match_declared_sha256():
    # 전제: 커밋된 선언의 sha256 이 실제 원본과 같다(9.4).
    for name, src in SKY["sources"].items():
        assert _sha256(_src_path(SKY, name)) == src["sha256"], name


@needs_sky130
@pytest.mark.parametrize("name", sorted(SKY_TABLE_VALUES))
def test_sky130_value_recomputed_independently(sky_decl, name):
    exp = _sky_expected()[name]
    got = sky_decl.value(name)
    assert isinstance(got, float)
    assert math.isclose(got, exp, rel_tol=REL), (name, got, exp)
    assert math.isclose(got, SKY_TABLE_VALUES[name], rel_tol=1e-9), (name, got)
    assert sky_decl.quantity(name).value_m == got


@needs_sky130
@pytest.mark.parametrize("name", sorted(SKY_RULE_ORDER))
def test_sky130_rules_carry_provenance(sky_decl, name):
    q = sky_decl.quantity(name)
    assert isinstance(q, PdkQuantity)
    assert q.name == name
    assert q.expression == SKY["quantities"][name]["expression"]
    assert q.basis == SKY["quantities"][name]["basis"]
    assert isinstance(q.rules, tuple)
    assert tuple(r.rule_id for r in q.rules) == SKY_RULE_ORDER[name]
    source = SKY["quantities"][name]["source"]
    path = _src_path(SKY, source)
    sha = _sha256(path)
    for r in q.rules:
        assert isinstance(r, PdkRule)
        value_m, text, unit, line = my_rule_m(SKY, source, r.rule_id)
        assert r.value_text == text
        assert r.unit_text == unit
        assert r.line == line == SKY_TABLE_LINES[r.rule_id]
        assert math.isclose(r.value_m, value_m, rel_tol=REL)
        assert r.value_m == float(text) * SKY["sources"][source]["units_m"][unit]
        assert r.source == source
        assert r.path == path
        assert r.sha256 == sha


@needs_sky130
def test_sky130_empty_unit_rows_read_as_declared_unit(sky_decl):
    # poly.7·poly.8 은 단위 열이 빈 행 -> units_m[""] (선언 note)
    rules = {r.rule_id: r for r in sky_decl.quantity("dummy_w_m").rules}
    assert rules["poly.7"].unit_text == ""
    assert rules["poly.7"].value_text == "0.250"
    assert math.isclose(rules["poly.7"].value_m, 0.25e-6, rel_tol=REL)


@needs_sky130
def test_sky130_decl_record_shape(sky_decl):
    assert isinstance(sky_decl, PdkDecl)
    assert sky_decl.pdk == "sky130"
    assert os.path.normcase(os.path.abspath(sky_decl.decl_path)) == os.path.normcase(os.path.abspath(SKY130_DECL))
    assert sky_decl.decl_sha256 == _sha256(SKY130_DECL)
    exp_sources = tuple(sorted((n, _src_path(SKY, n), _sha256(_src_path(SKY, n))) for n in SKY["sources"]))
    assert tuple(tuple(s) for s in sky_decl.sources) == exp_sources
    names = tuple(n for n, _ in sky_decl.quantities)
    assert names == tuple(sorted(SKY["quantities"]))
    for n, q in sky_decl.quantities:
        assert q == sky_decl.quantity(n)
    require_immutable(sky_decl)
    with pytest.raises(dataclasses.FrozenInstanceError):
        sky_decl.pdk = "other"


@needs_sky130
def test_sky130_fp_deterministic_across_fresh_memos():
    a = read_pdk_decl(str(SKY130_DECL), BoundedLRU(4))
    b = read_pdk_decl(str(SKY130_DECL), BoundedLRU(4))
    assert fp_of(a) == fp_of(b)
    assert a == b


@needs_sky130
def test_values_and_rule_ids_shapes(sky_decl):
    exp = _sky_expected()
    vals = sky_decl.values(PDK_RULE_QUANTITIES)
    assert isinstance(vals, tuple) and len(vals) == len(PDK_RULE_QUANTITIES)
    for v, n in zip(vals, PDK_RULE_QUANTITIES):
        assert math.isclose(v, exp[n], rel_tol=REL)
    rev = tuple(reversed(PDK_RULE_QUANTITIES))
    assert sky_decl.values(rev) == tuple(reversed(vals))
    assert sky_decl.values(()) == ()
    ids = sky_decl.rule_ids(PDK_RULE_QUANTITIES)
    assert ids == tuple((n, SKY["quantities"][n]["expression"]) for n in PDK_RULE_QUANTITIES)
    assert sky_decl.rule_ids(rev) == tuple(reversed(ids))


@needs_sky130
@pytest.mark.parametrize("call", [
    lambda d: d.quantity("no_such_m"),
    lambda d: d.value("no_such_m"),
    lambda d: d.values(("row_gap_m", "no_such_m")),
    lambda d: d.rule_ids(("no_such_m",)),
], ids=["quantity", "value", "values", "rule_ids"])
def test_undeclared_quantity_rejected(sky_decl, call):
    with pytest.raises(SchemaRejectedError) as ei:
        call(sky_decl)
    assert reason(ei) == "pdk_quantity_undeclared"


# ---------------------------------------------------------------- 캐시 (부르는 쪽 BoundedLRU, 모듈 캐시 없음)

@needs_sky130
def test_second_call_hits_memo_and_no_module_cache():
    n_src = len(SKY["sources"])
    memo = BoundedLRU(4)
    first = read_pdk_decl(str(SKY130_DECL), memo)
    s1 = memo.stats()
    assert (s1.hits, s1.misses) == (0, n_src)
    second = read_pdk_decl(str(SKY130_DECL), memo)
    s2 = memo.stats()
    assert s2.hits - s1.hits == n_src
    assert s2.misses == s1.misses
    assert first == second
    # 새 memo 면 다시 파싱(모듈 수준 캐시가 있으면 misses 가 0 이 된다)
    other = BoundedLRU(4)
    read_pdk_decl(str(SKY130_DECL), other)
    assert other.stats().misses == n_src and other.stats().hits == 0


@pytest.mark.parametrize("memo", [None, {}, "memo", 4, object()], ids=["None", "dict", "str", "int", "object"])
def test_memo_must_be_bounded_lru(memo):
    with pytest.raises(TypeError):
        read_pdk_decl(str(SKY130_DECL), memo)


# ---------------------------------------------------------------- 가상 PDK (toy lef + toy csv)

TOY_LEF = (
    "# toy technology lef\n"
    "VERSION 5.8 ;\n"
    "UNITS\n"
    "  DATABASE MICRONS 2000 ;\n"
    "END UNITS\n"
    "GRID 0.002 ;   # trailing comment\n"
    "# PITCH 9.9 ;\n"
    "PITCH 0.4 ;\n"
    "DUP 1 ;\n"
    "DUP 2 ;\n"
    "WORD met1 ;\n"
)
# section 열 1, id 열 2, 값 열 0, 단위 열 3; 절 머리 [name]
TOY_CSV = (
    "value,section,id,unit\n"
    "9.9,,w,um\n"
    ",[met],,\n"
    "0.05,,w,um\n"
    "0.07,,s,um\n"
    "30,,e,nm\n"
    '0.09,"multi\nline note",x,um\n'
    "0.11,,dd,um\n"
    "0.12,,dd,um\n"
    "N/A,,na,um\n"
    "0.170 *L,,star,um\n"
    "0.2,,mmrule,mm\n"
    "0.3,,nounit\n"
    ",[via],,\n"
    "0.1,,w,um\n"
    '0.02,,enc,"um"\n'
)
TOY_LEF_LINES = {"GRID": 6, "PITCH": 8}
TOY_CSV_LINES = {"met.w": 4, "met.s": 5, "met.e": 6, "met.x": 8, "met.nounit": 14, "via.w": 16, "via.enc": 17}


def _write_text(path, text, encoding="utf-8"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding=encoding, newline="") as f:
        f.write(text)


def _toy_decl(root, quantities, csv_encoding="utf-8", csv_text=TOY_CSV):
    _write_text(root / "tech" / "toy.lef", TOY_LEF)
    _write_text(root / "rules" / "toy.csv", csv_text, encoding=csv_encoding)
    return {
        "schema": "gmid_pdk_decl/1",
        "pdk": "toy7",
        "pdk_root": root.as_posix(),
        "sources": {
            "lef": {
                "path": "tech/toy.lef",
                "sha256": _sha256(root / "tech" / "toy.lef"),
                "format": "lef_statement",
                "encoding": "utf-8",
                "units_m": {"": 1e-6},
            },
            "table": {
                "path": "rules/toy.csv",
                "sha256": _sha256(root / "rules" / "toy.csv"),
                "format": "rule_table_csv",
                "encoding": csv_encoding,
                "section_pattern": r"^\[(\w+)\]$",
                "section_column": 1,
                "id_column": 2,
                "value_column": 0,
                "unit_column": 3,
                "units_m": {"um": 1e-6, "nm": 1e-9, "": 1e-6},
            },
        },
        "quantities": {n: {"source": s, "expression": e, "basis": "toy"} for n, (s, e) in quantities.items()},
    }


def _dump(tmp_path, decl, name="decl.json"):
    p = tmp_path / name
    with open(p, "w", encoding="utf-8") as f:
        json.dump(decl, f, ensure_ascii=False)
    return str(p)


TOY_QUANTITIES = {
    "grid_m": ("lef", "GRID"),
    "cell_pitch_m": ("lef", "2 * PITCH + GRID"),
    "lef_mix_m": ("lef", "PITCH * 1e-3 + GRID"),
    "met_pitch_m": ("table", "met.w + met.s"),
    "via_stack_m": ("table", "max(via.w + 2 * via.enc, met.w) - met.e"),
    "neg_ok_m": ("table", "-met.w + (met.s) * 3"),
    "min_half_m": ("table", "min(met.w, via.w, met.x) / 2"),
    "blank_unit_m": ("table", "met.nounit"),
}


def _toy_expected():
    um, nm = 1e-6, 1e-9
    grid, pitch = 0.002 * um, 0.4 * um
    mw, ms, me, mx, nounit = 0.05 * um, 0.07 * um, 30 * nm, 0.09 * um, 0.3 * um
    vw, venc = 0.1 * um, 0.02 * um
    return {
        "grid_m": grid,
        "cell_pitch_m": 2 * pitch + grid,
        "lef_mix_m": pitch * 1e-3 + grid,
        "met_pitch_m": mw + ms,
        "via_stack_m": max(vw + 2 * venc, mw) - me,
        "neg_ok_m": -mw + ms * 3,
        "min_half_m": min(mw, vw, mx) / 2,
        "blank_unit_m": nounit,
    }


@pytest.mark.parametrize("csv_encoding", ["utf-8", "latin-1"])
def test_generality_second_pdk_without_code_change(tmp_path, csv_encoding):
    root = tmp_path / "toypdk"
    csv_text = TOY_CSV.replace(",um\n", ",µm\n") if csv_encoding == "latin-1" else TOY_CSV
    decl = _toy_decl(root, TOY_QUANTITIES, csv_encoding=csv_encoding, csv_text=csv_text)
    if csv_encoding == "latin-1":
        decl["sources"]["table"]["units_m"] = {"µm": 1e-6, "um": 1e-6, "nm": 1e-9, "": 1e-6}
    path = _dump(tmp_path, decl)
    d = read_pdk_decl(path, BoundedLRU(2))
    assert d.pdk == "toy7"
    exp = _toy_expected()
    for n, v in exp.items():
        assert math.isclose(d.value(n), v, rel_tol=REL), (n, d.value(n), v)
    assert tuple(n for n, _ in d.quantities) == tuple(sorted(TOY_QUANTITIES))
    assert tuple(s[0] for s in d.sources) == ("lef", "table")
    # 출처: 독립 파서와 같은 행·글자
    for n, (src, _) in TOY_QUANTITIES.items():
        for r in d.quantity(n).rules:
            vm, text, unit, line = my_rule_m(decl, src, r.rule_id)
            assert (r.value_text, r.unit_text, r.line, r.source) == (text, unit, line, src)
            assert math.isclose(r.value_m, vm, rel_tol=REL)
            assert r.path == _src_path(decl, src)
            assert r.sha256 == decl["sources"][src]["sha256"]
    lines = {r.rule_id: r.line for n in TOY_QUANTITIES for r in d.quantity(n).rules}
    for rid, ln in {**TOY_LEF_LINES, **TOY_CSV_LINES}.items():
        assert lines[rid] == ln, rid
    # 첫 등장 순·중복 없음
    assert tuple(r.rule_id for r in d.quantity("via_stack_m").rules) == ("via.w", "via.enc", "met.w", "met.e")
    assert tuple(r.rule_id for r in d.quantity("lef_mix_m").rules) == ("PITCH", "GRID")
    exp_unit = "um" if csv_encoding == "utf-8" else "µm"
    assert d.quantity("met_pitch_m").rules[0].unit_text == exp_unit


def test_ambiguous_rule_only_rejected_when_used(tmp_path):
    # DUP·met.dd 는 원본에 두 번 -- 쓰지 않으면 통과(위 test), 쓰면 거부
    for i, (src, expr) in enumerate((("lef", "DUP"), ("table", "met.dd + met.w"))):
        decl = _toy_decl(tmp_path / ("pdk%d" % i), {"q_m": (src, expr)})
        with pytest.raises(SchemaRejectedError) as ei:
            read_pdk_decl(_dump(tmp_path, decl, "d%d.json" % i), BoundedLRU(2))
        assert reason(ei) == "pdk_rule_ambiguous", expr


def test_identical_sources_share_one_parse(tmp_path):
    # 같은 원본·같은 파싱 인자 -> memo 키가 같아 둘째 원본은 적중
    decl = _toy_decl(tmp_path / "pdk", {"a_m": ("table", "met.w"), "b_m": ("table2", "via.w")})
    decl["sources"]["table2"] = copy.deepcopy(decl["sources"]["table"])
    memo = BoundedLRU(4)
    d = read_pdk_decl(_dump(tmp_path, decl), memo)
    s = memo.stats()
    assert s.misses == 2 and s.hits == 1  # lef 1 + table 1 미적중, table2 적중
    assert math.isclose(d.value("b_m"), 0.1e-6, rel_tol=REL)


def test_sha256_remeasured_every_call_despite_memo(tmp_path):
    root = tmp_path / "pdk"
    decl = _toy_decl(root, {"a_m": ("table", "met.w")})
    path = _dump(tmp_path, decl)
    memo = BoundedLRU(4)
    read_pdk_decl(path, memo)
    read_pdk_decl(path, memo)
    assert memo.stats().hits == 2
    _write_text(root / "rules" / "toy.csv", TOY_CSV + "0.5,,extra,um\n")
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(path, memo)
    assert reason(ei) == "pdk_source_sha256_mismatch"


# ---------------------------------------------------------------- 실패 표 9.3 (toy 선언 변형)

def _set(path_keys, value):
    def f(d):
        cur = d
        for k in path_keys[:-1]:
            cur = cur[k]
        cur[path_keys[-1]] = value
    return f


def _del(path_keys):
    def f(d):
        cur = d
        for k in path_keys[:-1]:
            cur = cur[k]
        del cur[path_keys[-1]]
    return f


BASE_Q = {"a_m": ("table", "met.w + met.s"), "g_m": ("lef", "GRID")}

DECL_MUTATIONS = [
    # 키 집합
    ("top_extra", _set(["extra"], 1), "pdk_decl_keys"),
    ("top_missing_pdk_root", _del(["pdk_root"]), "pdk_decl_keys"),
    ("top_missing_quantities", _del(["quantities"]), "pdk_decl_keys"),
    ("source_extra", _set(["sources", "table", "foo"], "x"), "pdk_decl_keys"),
    ("source_missing_sha", _del(["sources", "lef", "sha256"]), "pdk_decl_keys"),
    ("source_missing_units", _del(["sources", "lef", "units_m"]), "pdk_decl_keys"),
    ("lef_with_csv_key", _set(["sources", "lef", "section_pattern"], "x"), "pdk_decl_keys"),
    ("csv_missing_unit_column", _del(["sources", "table", "unit_column"]), "pdk_decl_keys"),
    ("quantity_extra", _set(["quantities", "a_m", "unit"], "m"), "pdk_decl_keys"),
    ("quantity_missing_basis", _del(["quantities", "a_m", "basis"]), "pdk_decl_keys"),
    # 모양
    ("pdk_empty", _set(["pdk"], ""), "pdk_decl_shape"),
    ("pdk_not_str", _set(["pdk"], 7), "pdk_decl_shape"),
    ("pdk_root_not_str", _set(["pdk_root"], 5), "pdk_decl_shape"),
    ("pdk_root_empty", _set(["pdk_root"], ""), "pdk_decl_shape"),
    ("sources_list", _set(["sources"], []), "pdk_decl_shape"),
    ("sources_empty", _set(["sources"], {}), "pdk_decl_shape"),
    ("quantities_empty", _set(["quantities"], {}), "pdk_decl_shape"),
    ("quantity_not_obj", _set(["quantities", "a_m"], "met.w"), "pdk_decl_shape"),
    ("expression_not_str", _set(["quantities", "a_m", "expression"], 5), "pdk_decl_shape"),
    # 64 hex 아닌 sha256: 9.3 표에서 '문자열 모양'(shape)과 '선언과 다름'(mismatch) 둘 다 읽힌다 -- 거부만 확정, 키는 둘 중 하나
    ("sha_not_hex64", _set(["sources", "lef", "sha256"], "abc"), ("pdk_decl_shape", "pdk_source_sha256_mismatch")),
    # schema
    ("schema_other", _set(["schema"], "gmid_pdk_decl/2"), "pdk_decl_schema"),
    # 원본
    ("format_unknown", _set(["sources", "lef", "format"], "def_statement"), "pdk_source_format_unknown"),
    ("units_empty", _set(["sources", "lef", "units_m"], {}), "pdk_source_units_invalid"),
    ("units_zero", _set(["sources", "lef", "units_m"], {"": 0}), "pdk_source_units_invalid"),
    ("units_negative", _set(["sources", "lef", "units_m"], {"": -1e-6}), "pdk_source_units_invalid"),
    ("units_string", _set(["sources", "lef", "units_m"], {"": "1e-6"}), "pdk_source_units_invalid"),
    ("units_inf", _set(["sources", "lef", "units_m"], {"": float("inf")}), "pdk_source_units_invalid"),
    ("source_file_missing", _set(["sources", "lef", "path"], "tech/nope.lef"), "pdk_source_missing"),
    ("sha_mismatch", _set(["sources", "table", "sha256"], "0" * 64), "pdk_source_sha256_mismatch"),
    ("quantity_source_undeclared", _set(["quantities", "a_m", "source"], "nope"), "pdk_source_undeclared"),
]


@pytest.mark.parametrize("label,mutate,why", DECL_MUTATIONS, ids=[m[0] for m in DECL_MUTATIONS])
def test_declaration_violations_rejected(tmp_path, label, mutate, why):
    decl = _toy_decl(tmp_path / "pdk", BASE_Q)
    read_pdk_decl(_dump(tmp_path, decl, "ok.json"), BoundedLRU(2))  # 변형 전은 통과(대조군)
    bad = copy.deepcopy(decl)
    mutate(bad)
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, bad), BoundedLRU(2))
    if isinstance(why, tuple):
        assert reason(ei) in why
    else:
        assert reason(ei) == why


def test_optional_notes_may_be_absent_or_present(tmp_path):
    decl = _toy_decl(tmp_path / "pdk", BASE_Q)
    decl["note"] = "top"
    decl["sources"]["lef"]["note"] = "src"
    a = read_pdk_decl(_dump(tmp_path, decl, "a.json"), BoundedLRU(2))
    del decl["note"], decl["sources"]["lef"]["note"]
    b = read_pdk_decl(_dump(tmp_path, decl, "b.json"), BoundedLRU(2))
    assert a.value("a_m") == b.value("a_m")


def test_decl_file_missing(tmp_path):
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(str(tmp_path / "absent.json"), BoundedLRU(2))
    assert reason(ei) == "pdk_decl_missing"


@pytest.mark.parametrize("text", ['{"schema": ', "{bad json}", ""], ids=["truncated", "bare", "empty"])
def test_decl_json_syntax(tmp_path, text):
    p = tmp_path / "bad.json"
    _write_text(p, text)
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(str(p), BoundedLRU(2))
    assert reason(ei) == "pdk_decl_json"


def test_decl_top_level_not_object(tmp_path):
    p = tmp_path / "list.json"
    _write_text(p, "[1, 2]")
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(str(p), BoundedLRU(2))
    assert reason(ei) == "pdk_decl_shape"


EXPRESSION_CASES = [
    # 규칙 값
    ("table", "met.nope", "pdk_rule_missing"),
    ("lef", "NOPE", "pdk_rule_missing"),
    ("lef", "PITCH + NOPE", "pdk_rule_missing"),
    ("table", "w", "pdk_rule_missing"),           # 접두 없는 이름
    ("table", "via.dd", "pdk_rule_missing"),      # 접두가 다른 절
    ("lef", "DATABASE", "pdk_rule_missing"),      # 세 낱말 줄은 문장 규칙이 아니다
    ("lef", "PITCH_COMMENTED", "pdk_rule_missing"),
    ("table", "met.na", "pdk_rule_not_numeric"),
    ("table", "met.star", "pdk_rule_not_numeric"),
    ("lef", "WORD", "pdk_rule_not_numeric"),
    ("table", "met.mmrule", "pdk_rule_unit_unknown"),
    # 식
    ("table", "", "pdk_expression_invalid"),
    ("table", "   ", "pdk_expression_invalid"),
    ("table", "2 * 3", "pdk_expression_invalid"),
    ("table", "max(2, 3)", "pdk_expression_invalid"),
    ("table", "met.w +", "pdk_expression_invalid"),
    ("table", "(met.w", "pdk_expression_invalid"),
    ("table", "met.w ** 2", "pdk_expression_invalid"),
    ("table", "met.w % 2", "pdk_expression_invalid"),
    ("table", "met.w // 1", "pdk_expression_invalid"),
    ("table", "(met.w).real", "pdk_expression_invalid"),
    # 다른 함수·키워드 인자·문자열: 9.1 정규식상 abs·key 같은 낱말도 '규칙 이름'이라(원본에 없으면 pdk_rule_missing)
    # 허용 밖 노드 자체를 보려고 원본에 실재하는 규칙 이름(PITCH·GRID)을 함수·키워드·문자열 자리에 둔다.
    ("lef", "PITCH(GRID)", "pdk_expression_invalid"),
    ("lef", "max(PITCH, GRID=PITCH)", "pdk_expression_invalid"),
    ("lef", "PITCH + 'GRID'", "pdk_expression_invalid"),
    ("table", "met.w if 1 else met.s", "pdk_expression_invalid"),
    ("table", "met.w < met.s", "pdk_expression_invalid"),
    ("table", "[met.w][0]", "pdk_expression_invalid"),
    ("table", "met.w / 0", "pdk_expression_invalid"),
    ("table", "met.w / (met.s - met.s)", "pdk_expression_invalid"),
    # 결과
    ("table", "met.w - met.s", "pdk_quantity_invalid"),
    ("table", "-met.w", "pdk_quantity_invalid"),
    ("table", "met.w * 1e308 * 1e308", "pdk_quantity_invalid"),
]


@pytest.mark.parametrize("source,expr,why", EXPRESSION_CASES, ids=["%s:%s" % (c[0], c[1]) for c in EXPRESSION_CASES])
def test_expression_and_rule_failures(tmp_path, source, expr, why):
    decl = _toy_decl(tmp_path / "pdk", {"q_m": (source, expr)})
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(2))
    assert reason(ei) == why


def test_reject_is_schema_rejected_record(tmp_path):
    decl = _toy_decl(tmp_path / "pdk", {"q_m": ("table", "met.na")})
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(2))
    assert ei.value.record.failure_class == "SCHEMA_REJECTED"


# ---------------------------------------------------------------- 실패 표 9.3 (진짜 sky130 원본 사본)

@pytest.fixture
def sky_copy(tmp_path):
    if not _SKY_FILES_PRESENT:
        pytest.skip("sky130 원본 없음")
    root = tmp_path / "pdk"
    for n in SKY["sources"]:
        dst = root / SKY["sources"][n]["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_src_path(SKY, n), dst)
    decl = copy.deepcopy(SKY)
    decl["pdk_root"] = root.as_posix()
    return root, decl


def test_sky130_copy_reads_same_values(tmp_path, sky_copy):
    _, decl = sky_copy
    d = read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(4))
    exp = _sky_expected()
    for n in SKY_TABLE_VALUES:
        assert math.isclose(d.value(n), exp[n], rel_tol=REL)


SKY_REAL_CASES = [
    ("periphery_rules", "x.12d", "pdk_rule_ambiguous"),        # 표에 두 번(31·32행)
    ("tech_lef", "WIDTH", "pdk_rule_ambiguous"),               # 층마다 WIDTH
    ("periphery_rules", "x.1a", "pdk_rule_unit_unknown"),      # 단위 'mm'(선언 단위 표 밖)
    ("periphery_rules", "x.1b", "pdk_rule_unit_unknown"),
    ("periphery_rules", "poly.999", "pdk_rule_missing"),
    ("tech_lef", "SPACING_NOPE", "pdk_rule_missing"),
    ("periphery_rules", "licon.1 - poly.2", "pdk_quantity_invalid"),
    ("periphery_rules", "poly.2 ** 2", "pdk_expression_invalid"),
]


@pytest.mark.parametrize("source,expr,why", SKY_REAL_CASES, ids=["%s:%s" % (c[0], c[1]) for c in SKY_REAL_CASES])
def test_sky130_real_source_rejections(tmp_path, sky_copy, source, expr, why):
    _, decl = sky_copy
    decl["quantities"]["probe_m"] = {"source": source, "expression": expr, "basis": "test"}
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(4))
    assert reason(ei) == why


def test_sky130_tampered_copy_sha_mismatch(tmp_path, sky_copy):
    root, decl = sky_copy
    p = root / SKY["sources"]["periphery_rules"]["path"]
    with open(p, "ab") as f:
        f.write(b"\n")
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(4))
    assert reason(ei) == "pdk_source_sha256_mismatch"


def test_sky130_missing_source_copy(tmp_path, sky_copy):
    root, decl = sky_copy
    os.remove(root / SKY["sources"]["tech_lef"]["path"])
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(4))
    assert reason(ei) == "pdk_source_missing"
