"""CONTRACT §9 read_pdk_decl -- PDK 선언 파일에서 규칙 값을 원본(tlef·규칙표 csv)으로 계산한다.

독립 검증(작성자 ≠ 검증자): 기대값은 피검 함수를 부르지 않고 이 파일이 원본을 직접 읽어(정규식·csv 모듈) 규칙마다
손으로 쓴 식으로 다시 계산한다. 실패 표(9.3)의 이유 키는 조작한 임시 선언·원본 사본으로 실제 거부를 확인한다.
일반성: 다른 형식 인자(열 번호·절 정규식·단위 표)를 쓰는 가상 PDK 둘째 선언이 코드 변경 없이 동작한다.
DEC-91 형식(spice_model_card·spice_instance_line)·선택 키(base·newline)·sky130 접합 54개·LUT 생성 규칙 선언도 같은 방식
(독립 SPICE 파서 + 9.4 표 + 가상 모델 카드/생성기 원본)으로 확인한다.
"""
import copy
import csv
import dataclasses
import functools
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
    # 9.5 'memo = 원본 수 이상': 상한 = 원본 수(JSON 직접 집계). [결정 11, 2026-10-08] mim_cap_params 추가로 원본 5 -> 옛 상한 4 는
    # 원본 수보다 작아 두 번째 호출에 퇴출이 생긴다(기대 변경: 상한을 원본 수에서 유도).
    memo = BoundedLRU(n_src)
    first = read_pdk_decl(str(SKY130_DECL), memo)
    s1 = memo.stats()
    assert (s1.hits, s1.misses) == (0, n_src)
    second = read_pdk_decl(str(SKY130_DECL), memo)
    s2 = memo.stats()
    assert s2.hits - s1.hits == n_src
    assert s2.misses == s1.misses
    assert first == second
    # 새 memo 면 다시 파싱(모듈 수준 캐시가 있으면 misses 가 0 이 된다)
    other = BoundedLRU(n_src)
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


# ================================================================ SPICE 형식 (9.1 spice_model_card·spice_instance_line, DEC-91)
# 독립 파서: 계약 9.1 의 문장(키=값 정규식, 수+영문자 값 글자, 블록 머리·'+' 줄·주석 규칙, bin 공통/별 이름)을 이 파일이 따로 구현.

_SPICE_KV = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\{[^}]*\}|'[^']*'|[^\s(){}=']+)")
_SPICE_NUM = re.compile(r"^([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)([A-Za-z]*)$")
_SPICE_HEAD = re.compile(r"^\s*\.model\s+(\S+)\s+(\S+)(.*)$", re.IGNORECASE)
_SPICE_TAIL_COMMENT = re.compile(r"\s[$;].*$")


def _spice_pairs(text):
    """`키 = 값` 쌍 -> [(소문자 키, 값 글자, 단위 글자)] (9.1 SPICE 값 글자)."""
    out = []
    for k, v in _SPICE_KV.findall(text):
        m = _SPICE_NUM.match(v)
        out.append((k.lower(),) + ((m.group(1), m.group(2).lower()) if m else (v, "")))
    return out


def _source_bytes(path, src):
    with open(path, "rb") as f:
        raw = f.read()
    return raw.replace(b"\r\n", b"\n") if src.get("newline") == "lf" else raw


def my_model_card_rules(text, model_pattern):
    """-> {규칙 이름: [(값 글자, 단위 글자, 행), ...]} -- 여러 항목이면 쓰일 때 ambiguous."""
    pat = re.compile(model_pattern)
    blocks = []  # [(소문자 이름, 머리 행, {키: [(값, 단위, 행)]})]
    cur = None
    for n, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip("\r")
        if line.strip() == "" or line.lstrip().startswith("*"):
            continue
        line = _SPICE_TAIL_COMMENT.sub("", line)
        head = _SPICE_HEAD.match(line)
        if head:
            if pat.fullmatch(head.group(1)):
                cur = {}
                blocks.append((head.group(1).lower(), n, cur))
                rest = head.group(3)
            else:
                cur = None
                continue
        elif line.lstrip().startswith("+"):
            if cur is None:
                continue
            rest = line.lstrip()[1:]
        else:
            cur = None
            continue
        for k, v, u in _spice_pairs(rest):
            cur.setdefault(k, []).append((v, u, n))
    out = {}
    for name, _, kv in blocks:
        for k, hits in kv.items():
            out[name + "." + k] = list(hits)
    keys = {k for _, _, kv in blocks for k in kv}
    for k in keys:
        per_block = [kv[k][0] if k in kv else ("", "", head_n) for _, head_n, kv in blocks]
        distinct = []
        for v, u, n in per_block:
            if (v, u) not in [(a, b) for a, b, _ in distinct]:
                distinct.append((v, u, n))
        out[k] = distinct
    return out, len(blocks)


def my_instance_line_rules(text, line_pattern):
    pat = re.compile(line_pattern)
    out = {}
    for n, raw in enumerate(text.split("\n"), 1):
        m = pat.search(raw.rstrip("\r"))
        if not m:
            continue
        body = m.group(1) if pat.groups else m.group(0)
        for k, v, u in _spice_pairs(body):
            out.setdefault(k, []).append((v, u, n))
    return out


def _src_full_path(decl, name, decl_path):
    src = decl["sources"][name]
    if src.get("base", "pdk_root") == "decl_dir":
        return os.path.dirname(os.path.abspath(decl_path)).replace("\\", "/") + "/" + src["path"]
    return decl["pdk_root"] + "/" + src["path"]


@functools.lru_cache(maxsize=16)
def _my_spice_rules_cached(path, fmt, pattern, newline, encoding, sha):
    text = _source_bytes(path, {"newline": newline}).decode(encoding)
    if fmt == "spice_model_card":
        return my_model_card_rules(text, pattern)[0]
    return my_instance_line_rules(text, pattern)


def my_spice_rules(decl, name, decl_path):
    """독립 파서 결과(파일 sha 를 키에 넣어 같은 원본 재파싱 0 -- 반환값은 읽기 전용으로 쓴다)."""
    src = decl["sources"][name]
    path = _src_full_path(decl, name, decl_path)
    pattern = src["model_pattern"] if src["format"] == "spice_model_card" else src["line_pattern"]
    return _my_spice_rules_cached(path, src["format"], pattern, src.get("newline"), src["encoding"], _sha256(path))


def my_spice_rule_m(decl, name, decl_path, rule_id):
    hits = my_spice_rules(decl, name, decl_path)[rule_id]
    assert len(hits) == 1, (rule_id, hits)
    v, u, n = hits[0]
    return float(v) * decl["sources"][name]["units_m"][u], v, u, n


def _same_path(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


# ---------------------------------------------------------------- sky130 접합 파라미터 (9.4 DEC-91 표)

JUNCTION_FIELDS = ("cjs", "cjd", "cjsws", "cjswd", "cjswgs", "cjswgd", "mjs", "mjd", "mjsws", "mjswd", "mjswgs", "mjswgd",
                   "pbs", "pbd", "pbsws", "pbswd", "pbswgs", "pbswgd", "tcj", "tcjsw", "tcjswg", "tpb", "tpbsw", "tpbswg",
                   "tnom", "permod", "dwj")
JUNCTION_SOURCE = {"nmos": "nfet_01v8_tt_model_card", "pmos": "pfet_01v8_tt_model_card"}
# 9.4 표(drain 이름 = source 쪽 값)
JUNCTION_TABLE = {
    "nmos": dict(cjs=0.001339749237, cjsws=3.67354204e-11, cjswgs=2.38232788e-10, mjs=0.44, mjsws=0.0009, mjswgs=0.8,
                 pbs=0.729, pbsws=0.2, pbswgs=0.95578, tcj=0.000792, tcjsw=1e-05, tcjswg=0.0, tpb=0.0012287, tpbsw=0.0,
                 tpbswg=0.0, tnom=30.0, permod=1.0, dwj=0.0),
    "pmos": dict(cjs=0.0007380194454, cjsws=9.888892e-11, cjswgs=2.39155046e-10, mjs=0.34629, mjsws=0.29781,
                 mjswgs=0.9274, pbs=0.6587, pbsws=0.7418, pbswgs=1.4338, tcj=0.0012407, tcjsw=0.00037357, tcjswg=2e-12,
                 tpb=0.0020386, tpbsw=0.001246, tpbswg=0.0, tnom=30.0, permod=1.0, dwj=0.0),
}
JUNCTION_RULE_LINES = {"nmos": {"cjs": 231, "pbs": 230, "tnom": 240, "permod": 47, "dwc": 175, "xw": 216},
                       "pmos": {"cjs": 277, "tnom": 38, "permod": 69}}


def _drain_to_source(field):
    """9.4: drain 쪽 이름은 source 쪽 규칙(cjd -> cjs, cjswd -> cjsws, ..., pbswgd -> pbswgs)."""
    drain = ("cjd", "cjswd", "cjswgd", "mjd", "mjswd", "mjswgd", "pbd", "pbswd", "pbswgd")
    return field[:-1] + "s" if field in drain else field


def _junction_expected(kind):
    src = JUNCTION_SOURCE[kind]

    def rule(r):
        return my_spice_rule_m(SKY, src, str(SKY130_DECL), r)[0]

    exp = {}
    for f in JUNCTION_FIELDS:
        if f == "dwj":
            exp[f] = rule("dwc") - rule("xw") / 2  # 9.4: dwj 미지정 -> dwc, Weffcj 의 xw 포함
        else:
            exp[f] = rule(_drain_to_source(f))
    return exp


def test_drain_to_source_mapping_helper():
    assert [_drain_to_source(f) for f in ("cjd", "cjswd", "cjswgd", "mjd", "mjswd", "mjswgd", "pbd", "pbswd", "pbswgd")] == \
        ["cjs", "cjsws", "cjswgs", "mjs", "mjsws", "mjswgs", "pbs", "pbsws", "pbswgs"]
    assert [_drain_to_source(f) for f in ("tcj", "tpb", "tnom", "permod", "cjs", "dwj")] == ["tcj", "tpb", "tnom", "permod", "cjs", "dwj"]


@needs_sky130
def test_sky130_model_cards_have_declared_block_counts():
    # 9.4: model_pattern 이 고르는 블록 180개(nfet)·108개(pfet)
    for kind, n_blocks in (("nmos", 180), ("pmos", 108)):
        src = SKY["sources"][JUNCTION_SOURCE[kind]]
        text = _source_bytes(_src_path(SKY, JUNCTION_SOURCE[kind]), src).decode(src["encoding"])
        assert my_model_card_rules(text, src["model_pattern"])[1] == n_blocks


@needs_sky130
def test_sky130_declares_exactly_54_junction_quantities():
    names = {n for n in SKY["quantities"] if n.startswith("junction_")}
    assert names == {"junction_%s_%s" % (k, f) for k in ("nmos", "pmos") for f in JUNCTION_FIELDS}
    assert len(names) == 54


@needs_sky130
@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_sky130_junction_values_recomputed_independently(sky_decl, kind):
    exp = _junction_expected(kind)
    for f in JUNCTION_FIELDS:
        got = sky_decl.value("junction_%s_%s" % (kind, f))
        assert isinstance(got, float)
        assert math.isclose(got, exp[f], rel_tol=REL, abs_tol=0.0), (kind, f, got, exp[f])
        table = JUNCTION_TABLE[kind][_drain_to_source(f)]
        assert math.isclose(got, table, rel_tol=1e-12, abs_tol=0.0), (kind, f, got, table)
    # drain = source (BSIM4 기본값)
    for d in ("cjd", "cjswd", "cjswgd", "mjd", "mjswd", "mjswgd", "pbd", "pbswd", "pbswgd"):
        assert sky_decl.value("junction_%s_%s" % (kind, d)) == sky_decl.value("junction_%s_%s" % (kind, _drain_to_source(d)))


@needs_sky130
@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_sky130_junction_rules_are_bin_common_with_first_block_line(sky_decl, kind):
    src_name = JUNCTION_SOURCE[kind]
    path = _src_path(SKY, src_name)
    sha = _sha256(path)
    seen = {}
    for f in JUNCTION_FIELDS:
        for r in sky_decl.quantity("junction_%s_%s" % (kind, f)).rules:
            assert "." not in r.rule_id, r.rule_id  # bin 공통 이름
            vm, text, unit, line = my_spice_rule_m(SKY, src_name, str(SKY130_DECL), r.rule_id)
            assert (r.value_text, r.unit_text, r.line, r.source) == (text, unit, line, src_name)
            assert r.value_m == float(text) * SKY["sources"][src_name]["units_m"][unit]
            assert r.path == path and r.sha256 == sha
            seen[r.rule_id] = r.line
    for rid, ln in JUNCTION_RULE_LINES[kind].items():
        assert seen[rid] == ln, (kind, rid)
    assert tuple(r.rule_id for r in sky_decl.quantity("junction_%s_dwj" % kind).rules) == ("dwc", "xw")


@needs_sky130
def test_sky130_per_bin_rule_name_reads_that_block(tmp_path, sky_copy):
    _, decl = sky_copy
    decl["quantities"]["probe_m"] = {"source": "nfet_01v8_tt_model_card",
                                     "expression": "sky130_fd_pr__nfet_01v8__model.26.cjs", "basis": "test"}
    decl["quantities"]["probe_last_m"] = {"source": "nfet_01v8_tt_model_card",
                                          "expression": "sky130_fd_pr__nfet_01v8__model.179.cjs + 0 * tnom", "basis": "t"}
    d = read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(4))
    q = d.quantity("probe_m")
    assert q.value_m == 0.001339749237
    (r,) = q.rules
    assert (r.rule_id, r.value_text, r.unit_text, r.line) == ("sky130_fd_pr__nfet_01v8__model.26.cjs", "0.001339749237", "", 7199)
    exp_last = my_spice_rule_m(SKY, "nfet_01v8_tt_model_card", str(SKY130_DECL), "sky130_fd_pr__nfet_01v8__model.179.cjs")
    assert d.quantity("probe_last_m").rules[0].line == exp_last[3]
    assert d.value("probe_last_m") == exp_last[0]


SKY_CARD_REJECTIONS = [
    ("nfet_01v8_tt_model_card", "vth0", "pdk_rule_ambiguous"),                                   # bin 마다 다름
    ("pfet_01v8_tt_model_card", "vth0", "pdk_rule_ambiguous"),
    ("nfet_01v8_tt_model_card", "sky130_fd_pr__nfet_01v8__model.26.vth0", "pdk_rule_not_numeric"),  # 값이 {...} 식
    ("nfet_01v8_tt_model_card", "dwj", "pdk_rule_missing"),
    ("nfet_01v8_tt_model_card", "cjd", "pdk_rule_missing"),
    ("nfet_01v8_tt_model_card", "sky130_fd_pr__nfet_01v8__model.180.cjs", "pdk_rule_missing"),     # bin 180 없음
    ("pfet_01v8_tt_model_card", "sky130_fd_pr__nfet_01v8__model.0.cjs", "pdk_rule_missing"),       # 다른 파일의 모델
    ("nfet_01v8_tt_model_card", "sky130_fd_pr__nfet_01v8.cjs", "pdk_rule_missing"),                # 블록 머리 아닌 이름
]


@pytest.mark.parametrize("source,expr,why", SKY_CARD_REJECTIONS, ids=["%s:%s" % (c[0][:4], c[1]) for c in SKY_CARD_REJECTIONS])
def test_sky130_model_card_rejections(tmp_path, sky_copy, source, expr, why):
    _, decl = sky_copy
    decl["quantities"]["probe_m"] = {"source": source, "expression": expr, "basis": "test"}
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(4))
    assert reason(ei) == why


def test_sky130_vth0_really_varies_between_bins():
    # 위 ambiguous 거부의 전제(독립 파서): vth0 은 bin 마다 다르고 접합 키는 하나
    if not _SKY_FILES_PRESENT:
        pytest.skip("sky130 원본 없음")
    rules = my_spice_rules(SKY, "nfet_01v8_tt_model_card", str(SKY130_DECL))
    assert len(rules["vth0"]) > 1
    assert len(rules["cjs"]) == 1


# ---------------------------------------------------------------- LUT 생성 규칙 선언 (9.4, base decl_dir + newline lf)

LUT_RULE_DECL = SKILL_DIR / "assets" / "sky130_lut_rule_decl.json"
LUT = _load_json(LUT_RULE_DECL)
LUT_TABLE = {"lut_diffusion_ad_per_w_m": 5e-7, "lut_diffusion_as_per_w_m": 5e-7,
             "lut_diffusion_pd_extra_m": 2.0000000000000003e-06, "lut_diffusion_ps_extra_m": 2.0000000000000003e-06}
DUT_TEXT = "xdut d g s b sky130_fd_pr__{devcell} l={L_um}u w=5u ad=2.5p as=2.5p pd=7u ps=7u"


def _lut_expected():
    def r(k):
        return my_spice_rule_m(LUT, "lut_generator", str(LUT_RULE_DECL), k)[0]
    return {"lut_diffusion_ad_per_w_m": r("ad") / r("w"), "lut_diffusion_as_per_w_m": r("as") / r("w"),
            "lut_diffusion_pd_extra_m": r("pd") - r("w"), "lut_diffusion_ps_extra_m": r("ps") - r("w")}


def test_lut_rule_decl_values_and_provenance():
    d = read_pdk_decl(str(LUT_RULE_DECL), BoundedLRU(1))
    exp = _lut_expected()
    assert set(n for n, _ in d.quantities) == set(LUT_TABLE)
    for n, v in LUT_TABLE.items():
        assert math.isclose(d.value(n), exp[n], rel_tol=REL), n
        assert math.isclose(d.value(n), v, rel_tol=1e-12), n
    gen = SKILL_DIR / "assets" / "sky130_lut_sweep.py"
    lf_sha = hashlib.sha256(_source_bytes(gen, {"newline": "lf"})).hexdigest()
    assert lf_sha == LUT["sources"]["lut_generator"]["sha256"]
    (src,) = d.sources
    assert src[0] == "lut_generator" and _same_path(src[1], gen) and src[2] == lf_sha
    for n in LUT_TABLE:
        for r in d.quantity(n).rules:
            vm, text, unit, line = my_spice_rule_m(LUT, "lut_generator", str(LUT_RULE_DECL), r.rule_id)
            assert (r.value_text, r.unit_text, r.line) == (text, unit, line) and line == 90
            assert math.isclose(r.value_m, vm, rel_tol=REL)
            assert _same_path(r.path, gen) and r.sha256 == lf_sha
    ad = d.quantity("lut_diffusion_ad_per_w_m").rules
    assert [(r.rule_id, r.value_text, r.unit_text) for r in ad] == [("ad", "2.5", "p"), ("w", "5", "u")]
    # 원본 DUT 줄(9.4 글자 그대로)
    text = _source_bytes(gen, {"newline": "lf"}).decode("utf-8").split("\n")
    assert re.search(LUT["sources"]["lut_generator"]["line_pattern"], text[89]).group(1) == DUT_TEXT


def _lut_copy(tmp_path, gen_bytes, newline="lf", sha=None, sub="decl"):
    d = tmp_path / sub
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "gen.py", "wb") as f:
        f.write(gen_bytes)
    decl = copy.deepcopy(LUT)
    decl["pdk_root"] = (tmp_path / "no_such_root").as_posix()   # base decl_dir 라 쓰이지 않는다
    s = decl["sources"]["lut_generator"]
    s["path"] = "gen.py"
    if newline is None:
        del s["newline"]
    else:
        s["newline"] = newline
    if sha is not None:
        s["sha256"] = sha
    return _dump(d, decl, "rule.json"), d


def _gen_lf_bytes():
    return _source_bytes(SKILL_DIR / "assets" / "sky130_lut_sweep.py", {"newline": "lf"})


def test_newline_lf_accepts_crlf_and_lf_checkouts_with_same_sha(tmp_path):
    lf = _gen_lf_bytes()
    crlf = lf.replace(b"\n", b"\r\n")
    vals = []
    for i, b in enumerate((lf, crlf)):
        p, d = _lut_copy(tmp_path, b, sub="c%d" % i)
        decl = read_pdk_decl(p, BoundedLRU(1))
        assert decl.sources[0][2] == LUT["sources"]["lut_generator"]["sha256"]
        assert _same_path(decl.sources[0][1], d / "gen.py")   # base decl_dir: 선언 폴더 + "/" + path
        r = decl.quantity("lut_diffusion_pd_extra_m").rules[0]
        assert r.line == 90 and _same_path(r.path, d / "gen.py")
        vals.append(decl.values(tuple(LUT_TABLE)))
    assert vals[0] == vals[1]


def test_without_newline_key_crlf_bytes_are_hashed_raw(tmp_path):
    lf = _gen_lf_bytes()
    p, _ = _lut_copy(tmp_path, lf, newline=None, sub="lf")
    read_pdk_decl(p, BoundedLRU(1))   # LF 그대로면 같은 sha
    p, _ = _lut_copy(tmp_path, lf.replace(b"\n", b"\r\n"), newline=None, sub="crlf")
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(p, BoundedLRU(1))
    assert reason(ei) == "pdk_source_sha256_mismatch"


def test_newline_lf_rejects_declared_raw_crlf_sha(tmp_path):
    crlf = _gen_lf_bytes().replace(b"\n", b"\r\n")
    p, _ = _lut_copy(tmp_path, crlf, sha=hashlib.sha256(crlf).hexdigest())
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(p, BoundedLRU(1))
    assert reason(ei) == "pdk_source_sha256_mismatch"


def test_lut_rule_l_is_not_numeric(tmp_path):
    p, d = _lut_copy(tmp_path, _gen_lf_bytes())
    decl = _load_json(p)
    decl["quantities"]["probe_m"] = {"source": "lut_generator", "expression": "l", "basis": "test"}
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(d, decl, "rule2.json"), BoundedLRU(1))
    assert reason(ei) == "pdk_rule_not_numeric"


def test_base_decl_dir_missing_file_and_explicit_pdk_root(tmp_path):
    p, d = _lut_copy(tmp_path, _gen_lf_bytes())
    os.remove(d / "gen.py")
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(p, BoundedLRU(1))
    assert reason(ei) == "pdk_source_missing"
    # base pdk_root(명시)·생략: pdk_root + "/" + path
    root = tmp_path / "root"
    root.mkdir()
    with open(root / "gen.py", "wb") as f:
        f.write(_gen_lf_bytes())
    for base in ("pdk_root", None):
        decl = copy.deepcopy(LUT)
        decl["pdk_root"] = root.as_posix()
        s = decl["sources"]["lut_generator"]
        s["path"] = "gen.py"
        if base is None:
            s.pop("base")
        else:
            s["base"] = base
        got = read_pdk_decl(_dump(tmp_path, decl, "b_%s.json" % base), BoundedLRU(1))
        assert got.sources[0][1] == root.as_posix() + "/gen.py"
        assert math.isclose(got.value("lut_diffusion_ad_per_w_m"), 5e-7, rel_tol=1e-12)


# ---------------------------------------------------------------- 캐시 (모델 카드·생성 규칙 -- 부르는 쪽 BoundedLRU)

@needs_sky130
def test_two_decls_share_one_memo_five_sources():
    # 9.5: 두 선언을 같은 memo 로 읽으면 원본 n 개 -- 상한 n 이상이면 두 번째부터 파싱 0. n = 두 선언 JSON sources 수 직접 집계.
    # [결정 11, 2026-10-08] PDK 선언에 mim_cap_params 원본 추가 -> n = 5 + 1 = 6 (test 이름의 'five' 는 옛 값 -- id 유지).
    n = len(SKY["sources"]) + len(_load_json(LUT_RULE_DECL)["sources"])
    assert n == 6                           # 손 집계: tech_lef·periphery_rules·nfet/pfet 모델 카드·mim_cap_params + lut_generator
    memo = BoundedLRU(n)
    a1 = read_pdk_decl(str(SKY130_DECL), memo)
    b1 = read_pdk_decl(str(LUT_RULE_DECL), memo)
    s1 = memo.stats()
    assert (s1.hits, s1.misses) == (0, n)
    a2 = read_pdk_decl(str(SKY130_DECL), memo)
    b2 = read_pdk_decl(str(LUT_RULE_DECL), memo)
    s2 = memo.stats()
    assert (s2.hits, s2.misses) == (n, n)
    assert (a1, b1) == (a2, b2)
    assert fp_of(a1) == fp_of(a2)


# ---------------------------------------------------------------- 가상 PDK 모델 카드·인스턴스 줄 (일반성·거부)

TOY_CARD = (
    "* toy BSIM card (SPICE 대소문자 무관)\n"                     # 1
    ".param foo = 1\n"                                              # 2
    ".MODEL TOY_N.1 NMOS LEVEL=54 tnom=27\n"                        # 3
    "+ CJS = 1.0e-3 cjsws=2p  $ cjswgs=9\n"                         # 4
    "+ mjs = 0.5 ; trailing\n"                                      # 5
    "* inner comment\n"                                             # 6
    "\n"                                                            # 7
    "+ pbs = {0.7+x} vth0 = 0.40 dwc='a*b'\n"                       # 8
    "+ only1 = 5 neg = -2.5e-1 big = 1.5MEG\n"                      # 9
    ".model Toy_N.4 nmos secret = 1 cjs = 9e-3\n"                   # 10  (대소문자 다름 -> 패턴 밖)
    "+ hidden = 2\n"                                                # 11
    ".model toy_n.2 nmos level = 54 tnom = 27\n"                    # 12
    "+ cjs=1.0e-3 cjsws = 2P mjs=0.5 neg=-0.25 big=1.5meg\n"         # 13
    "+ pbs = 0.71 vth0 = 0.41 dwc = 3n\n"                           # 14
    "+ unk = 4q x2 = 7\n"                                           # 15
    ".ends\n"                                                       # 16  (블록 닫음)
    "+ after = 1\n"                                                 # 17
    ".model toy_n.3x nmos cjs = 7e-3 after = 3\n"                   # 18  (fullmatch 아님)
    ".model toy_n.5 pmos (cjs = 1.0e-3 cjsws=2p mjs = 0.5\n"         # 19  (괄호 꼴)
    "+ tnom = 27 level=54 neg = -0.25e0 big = 1500k )\n"             # 20
)
TOY_UNITS = {"": 1.0, "p": 1e-12, "n": 1e-9, "meg": 1e6, "k": 1e3}
TOY_INST = (
    "# toy generator\n"                                                         # 1
    'REF = "foo"\n'                                                             # 2
    'LINE_A = "xd d g s b cell L=2u W=4U ad=8p as=6P pd=12u ps=10u nf=2"\n'      # 3
    'LINE_B = "xe d g s b cell w=4u l={L}u"\n'                                   # 4
)


def _spice_toy_decl(root, quantities, card=TOY_CARD, inst=TOY_INST):
    _write_text(root / "models" / "toy.spice", card)
    _write_text(root / "gen" / "toy_gen.py", inst)
    return {
        "schema": "gmid_pdk_decl/1",
        "pdk": "toyspice",
        "pdk_root": root.as_posix(),
        "sources": {
            "card": {"path": "models/toy.spice", "sha256": _sha256(root / "models" / "toy.spice"),
                     "format": "spice_model_card", "encoding": "utf-8", "model_pattern": r"(?:TOY_N|toy_n)\.[0-9]+",
                     "units_m": dict(TOY_UNITS)},
            "inst": {"path": "gen/toy_gen.py", "sha256": _sha256(root / "gen" / "toy_gen.py"),
                     "format": "spice_instance_line", "encoding": "utf-8", "line_pattern": r'^LINE_A\s*=\s*"([^"]*)"',
                     "units_m": {"": 1.0, "u": 1e-6, "p": 1e-12}},
        },
        "quantities": {n: {"source": s, "expression": e, "basis": "toy"} for n, (s, e) in quantities.items()},
    }


TOY_SPICE_Q = {
    "cj_m": ("card", "cjs"),                              # bin 공통(블록 3개 모두 1.0e-3)
    "cjsw_m": ("card", "cjsws"),                          # 2p / 2P -> 단위 글자 소문자
    "mj_m": ("card", "mjs + tnom - level / 2"),           # '; trailing' 주석 버림, 머리 줄 키
    "neg_m": ("card", "-toy_n.1.neg"),                    # 부호
    "big_m": ("card", "toy_n.2.big / toy_n.1.big"),       # meg 배율
    "bin_dwc_m": ("card", "toy_n.2.dwc"),                 # bin 별 이름, 3n
    "bin_pbs_m": ("card", "toy_n.2.pbs + toy_n.1.only1"),
    "paren_m": ("card", "toy_n.5.big + toy_n.5.neg"),     # 괄호 꼴 머리 줄·'+' 줄
    "ad_per_w_m": ("inst", "ad / w"),
    "as_m": ("inst", "as"),
    "ps_extra_m": ("inst", "ps - w + nf * 0"),
}


def test_generality_toy_spice_formats_without_code_change(tmp_path):
    root = tmp_path / "spdk"
    decl = _spice_toy_decl(root, TOY_SPICE_Q)
    p = _dump(tmp_path, decl)
    d = read_pdk_decl(p, BoundedLRU(2))
    exp = {
        "cj_m": 1.0e-3, "cjsw_m": 2e-12, "mj_m": 0.5 + 27 - 27.0, "neg_m": 0.25, "big_m": 1.0, "bin_dwc_m": 3e-9,
        "bin_pbs_m": 0.71 + 5, "paren_m": 1500e3 - 0.25, "ad_per_w_m": 8e-12 / 4e-6, "as_m": 6e-12, "ps_extra_m": 10e-6 - 4e-6,
    }
    for n, v in exp.items():
        assert math.isclose(d.value(n), v, rel_tol=REL), (n, d.value(n), v)
    # 행·글자: 독립 파서와 같고, bin 공통은 첫 블록 행
    for n, (src, _) in TOY_SPICE_Q.items():
        for r in d.quantity(n).rules:
            vm, text, unit, line = my_spice_rule_m(decl, src, p, r.rule_id)
            assert (r.value_text, r.unit_text, r.line, r.source) == (text, unit, line, src), r.rule_id
            assert math.isclose(r.value_m, vm, rel_tol=REL)
    rules = {r.rule_id: r for n in TOY_SPICE_Q for r in d.quantity(n).rules}
    assert (rules["cjs"].line, rules["cjs"].value_text, rules["cjs"].unit_text) == (4, "1.0e-3", "")
    assert (rules["cjsws"].line, rules["cjsws"].value_text, rules["cjsws"].unit_text) == (4, "2", "p")
    assert (rules["mjs"].line, rules["mjs"].value_text) == (5, "0.5")
    assert (rules["tnom"].line, rules["level"].line) == (3, 3)
    assert (rules["toy_n.2.dwc"].line, rules["toy_n.2.dwc"].unit_text) == (14, "n")
    assert (rules["toy_n.1.big"].value_text, rules["toy_n.1.big"].unit_text) == ("1.5", "meg")
    assert (rules["toy_n.1.only1"].line, rules["toy_n.5.big"].line) == (9, 20)
    assert (rules["w"].line, rules["w"].value_text, rules["w"].unit_text) == (3, "4", "u")
    assert (rules["as"].unit_text, rules["nf"].unit_text) == ("p", "")


TOY_SPICE_REJECT = [
    ("card", "vth0", "pdk_rule_ambiguous"),            # 0.40 / 0.41
    ("card", "pbs", "pdk_rule_ambiguous"),             # {식} / 0.71
    ("card", "only1", "pdk_rule_ambiguous"),           # 한 블록에만
    ("card", "dwc", "pdk_rule_ambiguous"),
    ("card", "toy_n.1.pbs", "pdk_rule_not_numeric"),   # {0.7+x}
    ("card", "toy_n.1.dwc", "pdk_rule_not_numeric"),   # 'a*b'
    ("card", "toy_n.2.unk", "pdk_rule_unit_unknown"),  # q
    ("card", "cjswgs", "pdk_rule_missing"),            # ' $' 뒤 주석
    ("card", "toy_n.1.cjswgs", "pdk_rule_missing"),
    ("card", "secret", "pdk_rule_missing"),            # 패턴 밖 블록(Toy_N.4 -- 대소문자 그대로 fullmatch)
    ("card", "hidden", "pdk_rule_missing"),            # 패턴 밖 블록의 '+' 줄
    ("card", "toy_n.4.secret", "pdk_rule_missing"),
    ("card", "after", "pdk_rule_missing"),             # .ends 뒤 '+' 줄·fullmatch 아닌 toy_n.3x
    ("card", "toy_n.3x.cjs", "pdk_rule_missing"),
    ("card", "foo", "pdk_rule_missing"),               # .param 은 블록 아님
    ("card", "toy_n.1.x2", "pdk_rule_missing"),        # 다른 블록의 키
    ("inst", "line_a", "pdk_rule_missing"),            # 그룹 1 밖(LINE_A = 는 키가 아니다)
    ("inst", "ref", "pdk_rule_missing"),               # 패턴이 고르지 않은 줄
]


@pytest.mark.parametrize("source,expr,why", TOY_SPICE_REJECT, ids=["%s:%s" % (c[0], c[1]) for c in TOY_SPICE_REJECT])
def test_toy_spice_rule_failures(tmp_path, source, expr, why):
    decl = _spice_toy_decl(tmp_path / "spdk", {"q_m": (source, expr)})
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(2))
    assert reason(ei) == why


def test_toy_card_without_matching_block_misses_every_rule(tmp_path):
    decl = _spice_toy_decl(tmp_path / "spdk", {"q_m": ("card", "cjs")})
    decl["sources"]["card"]["model_pattern"] = r"nothing\.[0-9]+"
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(2))
    assert reason(ei) == "pdk_rule_missing"


def test_toy_card_model_pattern_is_fullmatch_case_sensitive(tmp_path):
    # 패턴이 Toy_N 도 고르면 secret 이 보이고 cjs 는 블록마다 달라(9e-3) ambiguous
    decl = _spice_toy_decl(tmp_path / "spdk", {"q_m": ("card", "toy_n.4.secret")})
    decl["sources"]["card"]["model_pattern"] = r"(?:TOY_N|toy_n|Toy_N)\.[0-9]+"
    d = read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(2))
    assert d.value("q_m") == 1.0
    assert d.quantity("q_m").rules[0].line == 10
    decl["quantities"] = {"q_m": {"source": "card", "expression": "cjs", "basis": "t"}}
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl, "d2.json"), BoundedLRU(2))
    assert reason(ei) == "pdk_rule_ambiguous"


def test_toy_instance_line_group_versus_whole_match(tmp_path):
    # 그룹 없는 정규식이면 맞은 글자 전체에서 키=값 -> LINE_A = "xd 도 키(값 '"xd' 는 수 아님)
    decl = _spice_toy_decl(tmp_path / "spdk", {"q_m": ("inst", "line_a")})
    decl["sources"]["inst"]["line_pattern"] = r'^LINE_A\s*=\s*"[^"]*"'
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(2))
    assert reason(ei) == "pdk_rule_not_numeric"
    decl["quantities"] = {"q_m": {"source": "inst", "expression": "ad / w", "basis": "t"}}
    d = read_pdk_decl(_dump(tmp_path, decl, "d2.json"), BoundedLRU(2))
    assert math.isclose(d.value("q_m"), 2e-6, rel_tol=REL)


def test_toy_instance_line_key_on_two_lines_ambiguous_only_when_used(tmp_path):
    decl = _spice_toy_decl(tmp_path / "spdk", {"q_m": ("inst", "ad")})
    decl["sources"]["inst"]["line_pattern"] = r'^LINE_[AB]\s*=\s*"([^"]*)"'
    d = read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(2))   # ad 는 A 줄에만
    assert d.value("q_m") == 8e-12
    for expr, why in (("w", "pdk_rule_ambiguous"), ("l", "pdk_rule_ambiguous")):
        decl["quantities"] = {"q_m": {"source": "inst", "expression": expr, "basis": "t"}}
        with pytest.raises(SchemaRejectedError) as ei:
            read_pdk_decl(_dump(tmp_path, decl, "d_%s.json" % expr), BoundedLRU(2))
        assert reason(ei) == why, expr
    # B 줄만 고르면 l 은 {L}u -> 수 아님
    decl["sources"]["inst"]["line_pattern"] = r'^LINE_B\s*=\s*"([^"]*)"'
    decl["quantities"] = {"q_m": {"source": "inst", "expression": "l", "basis": "t"}}
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, decl, "d_b.json"), BoundedLRU(2))
    assert reason(ei) == "pdk_rule_not_numeric"


def test_spice_memo_key_includes_parse_arguments(tmp_path):
    # 같은 모델 카드·같은 패턴 -> 둘째 원본 적중; 패턴이 다르면 따로 파싱
    decl = _spice_toy_decl(tmp_path / "spdk", {"a_m": ("card", "cjs"), "b_m": ("card2", "cjs")})
    decl["sources"]["card2"] = copy.deepcopy(decl["sources"]["card"])
    memo = BoundedLRU(4)
    d = read_pdk_decl(_dump(tmp_path, decl), memo)
    assert (memo.stats().misses, memo.stats().hits) == (2, 1)   # card + inst 미적중, card2 적중
    assert d.value("a_m") == d.value("b_m")
    decl["sources"]["card2"]["model_pattern"] = r"toy_n\.[0-9]+"
    memo = BoundedLRU(4)
    read_pdk_decl(_dump(tmp_path, decl, "d2.json"), memo)
    assert (memo.stats().misses, memo.stats().hits) == (3, 0)
    # 같은 memo 로 다시 부르면 전부 적중
    read_pdk_decl(_dump(tmp_path, decl, "d2.json"), memo)
    assert (memo.stats().misses, memo.stats().hits) == (3, 3)


SPICE_DECL_MUTATIONS = [
    ("card_missing_model_pattern", _del(["sources", "card", "model_pattern"]), "pdk_decl_keys"),
    ("card_with_line_pattern", _set(["sources", "card", "line_pattern"], "x"), "pdk_decl_keys"),
    ("card_with_section_column", _set(["sources", "card", "section_column"], 0), "pdk_decl_keys"),
    ("inst_missing_line_pattern", _del(["sources", "inst", "line_pattern"]), "pdk_decl_keys"),
    ("inst_with_model_pattern", _set(["sources", "inst", "model_pattern"], "x"), "pdk_decl_keys"),
    ("card_unknown_key", _set(["sources", "card", "newlines"], "lf"), "pdk_decl_keys"),
    ("model_pattern_int", _set(["sources", "card", "model_pattern"], 5), "pdk_decl_shape"),
    ("model_pattern_bad_regex", _set(["sources", "card", "model_pattern"], "(toy"), "pdk_decl_shape"),
    ("line_pattern_list", _set(["sources", "inst", "line_pattern"], ["x"]), "pdk_decl_shape"),
    ("line_pattern_bad_regex", _set(["sources", "inst", "line_pattern"], "[a-"), "pdk_decl_shape"),
    ("base_other", _set(["sources", "card", "base"], "root"), "pdk_decl_shape"),
    ("base_int", _set(["sources", "card", "base"], 1), "pdk_decl_shape"),
    ("base_null", _set(["sources", "card", "base"], None), "pdk_decl_shape"),
    ("base_empty", _set(["sources", "inst", "base"], ""), "pdk_decl_shape"),
    ("newline_crlf", _set(["sources", "card", "newline"], "crlf"), "pdk_decl_shape"),
    ("newline_upper", _set(["sources", "card", "newline"], "LF"), "pdk_decl_shape"),
    ("newline_bool", _set(["sources", "inst", "newline"], True), "pdk_decl_shape"),
    ("encoding_unknown", _set(["sources", "card", "encoding"], "utf-99"), "pdk_decl_shape"),
    ("format_typo", _set(["sources", "card", "format"], "spice_model_cards"), "pdk_source_format_unknown"),
    ("units_negative", _set(["sources", "card", "units_m"], {"": 1.0, "p": -1e-12}), "pdk_source_units_invalid"),
    ("units_bool", _set(["sources", "inst", "units_m"], {"": True}), "pdk_source_units_invalid"),
    ("decl_dir_file_absent", _set(["sources", "card", "base"], "decl_dir"), "pdk_source_missing"),
    ("sha_mismatch", _set(["sources", "inst", "sha256"], "f" * 64), "pdk_source_sha256_mismatch"),
    # 검사 순서(9.1): format -> 키 집합 -> units_m -> 값 모양 -> 파일 존재 -> sha256
    ("order_format_before_keys", lambda d: (_set(["sources", "card", "format"], "nope")(d),
                                            _del(["sources", "card", "model_pattern"])(d)), "pdk_source_format_unknown"),
    ("order_keys_before_units", lambda d: (_set(["sources", "card", "units_m"], {})(d),
                                           _set(["sources", "card", "line_pattern"], "x")(d)), "pdk_decl_keys"),
    ("order_units_before_shape", lambda d: (_set(["sources", "card", "units_m"], {})(d),
                                            _set(["sources", "card", "base"], "x")(d)), "pdk_source_units_invalid"),
    ("order_shape_before_missing", lambda d: (_set(["sources", "card", "path"], "models/none.spice")(d),
                                              _set(["sources", "card", "newline"], "cr")(d)), "pdk_decl_shape"),
    ("order_missing_before_sha", lambda d: (_set(["sources", "card", "path"], "models/none.spice")(d),
                                            _set(["sources", "card", "sha256"], "0" * 64)(d)), "pdk_source_missing"),
]


@pytest.mark.parametrize("label,mutate,why", SPICE_DECL_MUTATIONS, ids=[m[0] for m in SPICE_DECL_MUTATIONS])
def test_spice_declaration_violations_rejected(tmp_path, label, mutate, why):
    decl = _spice_toy_decl(tmp_path / "spdk", {"a_m": ("card", "cjs"), "b_m": ("inst", "ad")})
    decl["sources"]["card"]["newline"] = "lf"   # 선택 키 둘 다 있는 대조군
    decl["sources"]["inst"]["base"] = "pdk_root"
    read_pdk_decl(_dump(tmp_path, decl, "ok.json"), BoundedLRU(2))
    bad = copy.deepcopy(decl)
    mutate(bad)
    with pytest.raises(SchemaRejectedError) as ei:
        read_pdk_decl(_dump(tmp_path, bad), BoundedLRU(2))
    assert reason(ei) == why


def test_base_and_newline_allowed_on_older_formats(tmp_path):
    # 선택 키는 원본 공통 -- lef/csv 원본에도 쓸 수 있다
    decl = _toy_decl(tmp_path / "pdk", BASE_Q)
    decl["sources"]["lef"]["base"] = "pdk_root"
    decl["sources"]["table"]["newline"] = "lf"
    d = read_pdk_decl(_dump(tmp_path, decl), BoundedLRU(2))
    assert math.isclose(d.value("a_m"), 0.12e-6, rel_tol=REL)
