"""card 20261104-op1b toy test: op1b_lib (interface card 20261104-op1b.interface.md 4 toy 표).

oracle 출처 (모두 (d) interface card 선언값 + (a) 구성으로 정해진 합성 입력):
- 기대값은 interface 4 toy 표의 손 유도값 또는 아래 주석의 손 계산이다. op1b_lib 출력을 옮기지 않았다.
- sha256은 입력 바이트를 구성하는 데만 hashlib로 쓴다(피검 함수 아님).
"""
import copy
import hashlib
import json
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import op1b_lib as L  # noqa: E402


def sha(b):
    return hashlib.sha256(b).hexdigest()


def reason_of(exc_info):
    e = exc_info.value
    r = getattr(e, "reason", None)
    return r if r is not None else e.args[0]


def detail_of(exc_info):
    e = exc_info.value
    d = getattr(e, "detail", None)
    if d is not None:
        return d
    return e.args[1] if len(e.args) > 1 else None


# ---------------------------------------------------------------- T-1
def test_t1a_rewrite_lut_ref():
    # oracle (d): interface T-1a. 구성: lut_npz만 "a" -> "b".
    old = {"process": {"lut_npz": "a", "models": {"nmos": {"subckt": "s"}}, "x": 1},
           "devices": [{"L": 1e-6}]}
    snap = copy.deepcopy(old)
    new = L.rewrite_lut_ref(old, "b")
    assert new["process"]["lut_npz"] == "b"
    exp = copy.deepcopy(snap)
    exp["process"]["lut_npz"] = "b"
    assert new == exp
    assert json.dumps(new) == json.dumps(exp)  # 키 순서 유지
    assert old == snap and old["process"]["lut_npz"] == "a"  # 입력 불변
    new["devices"][0]["L"] = 9.0  # 깊은 사본
    assert old["devices"][0]["L"] == 1e-6


@pytest.mark.parametrize("bad", [{"process": {}}, {}])
def test_t1b_rewrite_lut_ref_absent(bad):
    with pytest.raises(L.Op1bStop) as ei:
        L.rewrite_lut_ref(bad, "b")
    assert reason_of(ei) == "lut_npz_absent"


# ---------------------------------------------------------------- T-2
@pytest.mark.parametrize("txt", [None, '{"model_files_sha256": {}}', "{}"])
def test_t2_provenance_missing(txt):
    # oracle (d): interface T-2
    assert L.provenance_shape(txt) == "missing"


def test_t2_provenance_flat_nested_unknown():
    assert L.provenance_shape('{"model_files_sha256": {"a": "x"}}') == "flat"
    assert L.provenance_shape('{"model_files_sha256": {"n": {"a": "x"}}}') == "nested"
    assert L.provenance_shape('{"model_files_sha256": {"a": "x", "n": {"b": "y"}}}') == "unknown"


# ---------------------------------------------------------------- T-3
def _reader(files):
    def rb(p):
        if p not in files:
            raise FileNotFoundError(p)
        return files[p]
    return rb


def test_t3a_include_bundle():
    # oracle (a): 구성으로 정해진 합성 파일. d/a -> d/b -> d/../c = c. 주석 줄 z는 따라가지 않는다.
    files = {"d/a": b'.include "b"\n* .include "z"\n',
             "d/b": b'.LIB "../c" tt\r\n',
             "c": b"x\n"}
    out = L.include_bundle(["d/a"], _reader(files))
    assert set(out) == {"d/a", "d/b", "c"}
    assert out["d/b"] == (sha(b'.LIB "../c" tt\n'), sha(b'.LIB "../c" tt\r\n'))
    assert out["c"] == (sha(b"x\n"), sha(b"x\n"))
    assert out["d/a"][1] == sha(files["d/a"])


def test_t3b_include_cycle_once():
    files = {"a": b'.include "b"\n', "b": b'.include "a"\n'}
    assert set(L.include_bundle(["a"], _reader(files))) == {"a", "b"}


def test_t3c_include_missing():
    files = {"a": b'.include "nope"\n'}
    with pytest.raises(L.Op1bStop) as ei:
        L.include_bundle(["a"], _reader(files))
    assert reason_of(ei) == "include_missing"


# ---------------------------------------------------------------- T-4
S1, S2, S3, S4 = "1" * 64, "2" * 64, "3" * 64, sha(b"aux")


def _no_aux(_p):
    raise AssertionError("aux_read must not be called")


def _base():
    return dict(
        records={"m": S1, "x": S2},
        roles={},
        bundle={"/p/m": (S1, S1), "/p/x": (S2, S2)},
        texts={"/p/m": ".subckt mod a b", "/p/x": ""},
        model_name="mod",
        aux_read=_no_aux,
    )


def test_t4_base():
    assert L.bundle_rules(**_base()) == ([], [])


def test_t4a_record_not_in_bundle():
    k = _base()
    k["records"]["y"] = S3
    assert L.bundle_rules(**k) == (["model_bundle_mismatch"], [])


def test_t4b_no_defining_file():
    k = _base()
    k["texts"]["/p/m"] = ""
    assert L.bundle_rules(**k) == (["model_bundle_mismatch"], [])


def test_t4c_defining_sha_not_recorded():
    k = _base()
    k["records"].pop("m")
    assert L.bundle_rules(**k) == (["model_bundle_mismatch"], [])


def test_t4d_empty_records():
    k = _base()
    k["records"] = {}
    assert L.bundle_rules(**k) == (["lut_model_provenance_missing"], [])


def test_t4e_aux_ok():
    k = _base()
    k["records"]["b.csv"] = S4
    k["roles"]["b.csv"] = "generation_aux_input"
    k["aux_read"] = lambda p: b"aux" if p == "b.csv" else None
    assert L.bundle_rules(**k) == ([], [])


@pytest.mark.parametrize("reader", [lambda p: b"other", lambda p: None])
def test_t4f_aux_mismatch(reader):
    k = _base()
    k["records"]["b.csv"] = S4
    k["roles"]["b.csv"] = "generation_aux_input"
    k["aux_read"] = reader
    assert L.bundle_rules(**k) == (["lut_aux_input_mismatch"], [])


def test_t4g_role_undeclared_no_silent_exemption():
    k = _base()
    k["records"]["b.csv"] = S4
    assert L.bundle_rules(**k) == (["model_bundle_mismatch"], [])


def test_t4h_machine_dependent_raw_only():
    k = _base()
    k["bundle"]["/p/m"] = (S3, S1)  # LF 값 S3, raw 값 S1
    k["records"]["m"] = S1  # 기록 = raw
    assert L.bundle_rules(**k) == ([], ["m"])


# ---------------------------------------------------------------- T-5
def test_t5a_cache_excluded():
    a = {"ac": {"x": 1.0}, "cache": {"a": 1}}
    b = {"ac": {"x": 1.0}, "cache": {"a": 2}}
    assert L.compare_runs(a, b) == []


def test_t5b_one_ulp():
    assert L.compare_runs({"ac": {"x": 1.0}}, {"ac": {"x": math.nextafter(1.0, 2.0)}}) == ["/ac/x"]


def test_t5c_nan_equals_nan():
    assert L.compare_runs({"a": [1.0, float("nan")]}, {"a": [1.0, float("nan")]}) == []


def test_t5d_key_and_index_pointers():
    assert L.compare_runs({"a": 1}, {"a": 1, "b": 2}) == ["/b"]
    assert L.compare_runs({"a": [1, 2]}, {"a": [1, 3]}) == ["/a/1"]


def test_t5e_comparable_deep_exclusion_and_immutable():
    src = {"x": {"stability_cache": 1, "y": 2}, "cache": 3}
    snap = copy.deepcopy(src)
    assert L.comparable(src) == {"x": {"y": 2}}
    assert src == snap


# ---------------------------------------------------------------- T-6
def test_t6_category_present_true_and_empty_false():
    # oracle (d): interface T-6 술어. 칸이 없으면 거짓.
    true_cases = {
        "op": {"op_ok": True},
        "ac": {"ac": {"dc_gain_db": 40.0}},
        "rail": {"rail_current_A": {"vdd": 1e-3}},
        "ratio": {"ratio": {"a": 1}},
        "rout": {"rout": {"a": 1}},
        "beta_loop": {"loop": {}, "ac": {"stability": {"loop": "beta_loop"}}},
        "stability": {"ac": {"stability": {"verdict": "stable"}}},
        "stable": {"ac": {"stability": {"verdict": "stable"}}},
        "unstable": {"ac": {"stability": {"verdict": "unstable"}}},
        "noise": {"noise": {"status": "ok"}},
        "mc": {"offset_mc": {"n_requested": 5}},
    }
    for cat, sim in true_cases.items():
        assert L.category_present(sim, cat) is True, cat
        assert L.category_present({}, cat) is False, cat


def test_t6_category_present_negatives():
    assert L.category_present({"op_ok": False}, "op") is False
    assert L.category_present({"ac": {"dc_gain_db": None}}, "ac") is False
    assert L.category_present({"rail_current_A": {}}, "rail") is False
    assert L.category_present({"ratio": {}}, "ratio") is False
    assert L.category_present({"rout": {}}, "rout") is False
    assert L.category_present({"loop": {}, "ac": {"stability": {"loop": "other"}}}, "beta_loop") is False
    assert L.category_present({"ac": {"stability": {"verdict": "stable"}}}, "unstable") is False
    assert L.category_present({"ac": {"stability": {"verdict": "unstable"}}}, "stable") is False
    assert L.category_present({"ac": {"stability": None}}, "stability") is False
    assert L.category_present({"noise": {"status": "unavailable"}}, "noise") is False
    assert L.category_present({"offset_mc": {"n_requested": None}}, "mc") is False


def test_t6_category_unknown():
    with pytest.raises(L.Op1bStop) as ei:
        L.category_present({}, "no_such_category")
    assert reason_of(ei) == "category_unknown"


# ---------------------------------------------------------------- T-7
def test_t7_vos_samples():
    # 손 유도: k=1: (1.1-1.0)/100 - 0 = 1e-3 ; k=2: (0.9-1.0)/100 - 0 = -1e-3
    out = L.vos_samples([0.0, 0.0, 0.0], [1.0, 1.1, 0.9], 100.0)
    assert len(out) == 2
    assert out == [pytest.approx(0.001, rel=1e-12), pytest.approx(-0.001, rel=1e-12)]


def test_t7a_vos_samples_vid_term():
    # 손 유도: (0-0)/1 - (1e-3 - 0) = -1e-3
    assert L.vos_samples([0.0, 1e-3], [0.0, 0.0], 1.0) == [pytest.approx(-1e-3, rel=1e-12)]


# ---------------------------------------------------------------- T-8
OLD8 = {"process": {"lut_npz": "p",
                    "models": {"nmos": {"subckt": "pre__nfet"}, "pmos": {"subckt": "pre__pfet"}}},
        "devices": [{"kind": "nmos"}, {"kind": "pmos"}]}


def test_t8a_nested():
    assert L.lut_files_row(OLD8, "S", "nested", ["nfet", "pfet"]) == [
        {"path": "p", "sha256": "S", "kinds": {"nmos": "nfet", "pmos": "pfet"}}]


def test_t8b_unresolved_zero_and_two():
    # ["nfet"]: pmos 끝이 맞는 키 0개. ["nfet","fet","pfet"]: nmos가 nfet·fet 둘.
    with pytest.raises(L.Op1bStop) as e0:
        L.lut_files_row(OLD8, "S", "nested", ["nfet"])
    assert reason_of(e0) == "lut_kind_key_unresolved"
    with pytest.raises(L.Op1bStop) as e2:
        L.lut_files_row(OLD8, "S", "nested", ["nfet", "fet", "pfet"])
    assert reason_of(e2) == "lut_kind_key_unresolved"


@pytest.mark.parametrize("shape", ["missing", "flat"])
def test_t8c_flat_missing_none(shape):
    rows = L.lut_files_row(OLD8, "S", shape, [])
    assert len(rows) == 1
    assert rows[0]["path"] == "p" and rows[0]["sha256"] == "S"
    assert rows[0]["kinds"] == {"nmos": None, "pmos": None}


def test_t8d_unknown_shape():
    with pytest.raises(L.Op1bStop) as ei:
        L.lut_files_row(OLD8, "S", "unknown", [])
    assert reason_of(ei) == "lut_shape_unknown"


# ---------------------------------------------------------------- T-9
def _old9():
    return {"schema": "spice_oracle_input/1",
            "process": {"lut_npz": "p", "models": {}, "ngspice_exe": "e",
                        "diffusion": {"d": 1}, "lut_reference_width_m": 5e-6, "provenance": "x"},
            "testbench": {"options": {"reltol": "1e-4"}, "ac": {}},
            "devices": [], "keep": 1}


def test_t9a_convert():
    old = _old9()
    snap = copy.deepcopy(old)
    new, rec = L.convert_input(old, lut_files=["L"], descriptor=None, adapter="a")
    assert new["schema"] == "spice_oracle_input/2"
    assert new["process"] == {"lut_files": ["L"], "descriptor": None}
    assert new["simulator"] == {"exe": "e", "options": {"reltol": "1e-4"}, "adapter": "a"}
    assert new["testbench"] == {"ac": {}}
    assert new["keep"] == 1
    assert new["devices"] == []
    for k in ("schema", "diffusion", "lut_reference_width_m", "provenance", "draft"):
        assert k in rec, k
    assert rec["draft"] is True
    assert old == snap  # 입력 불변


def test_t9b_descriptor():
    d = {"path": "d", "sha256": "s"}
    new, rec = L.convert_input(_old9(), lut_files=["L"], descriptor=d, adapter="a")
    assert new["process"]["descriptor"] == d
    assert rec["draft"] is False


def test_t9e_exe_from_arg():
    old = _old9()
    del old["process"]["ngspice_exe"]
    new, rec = L.convert_input(old, lut_files=["L"], descriptor=None, adapter="a", exe="x")
    assert new["simulator"]["exe"] == "x"
    assert rec["exe_absent"] is True


def test_t9f_exe_unresolved():
    old = _old9()
    del old["process"]["ngspice_exe"]
    with pytest.raises(L.Op1bStop) as ei:
        L.convert_input(old, lut_files=["L"], descriptor=None, adapter="a")
    assert reason_of(ei) == "exe_unresolved"


def test_t9c_options_absent():
    old = _old9()
    del old["testbench"]["options"]
    new, rec = L.convert_input(old, lut_files=["L"], descriptor=None, adapter="a")
    assert rec["options_absent"] is True
    assert "options" not in new["simulator"]


def test_t9d_process_key_unmapped():
    old = _old9()
    old["process"]["z"] = 1
    with pytest.raises(L.Op1bStop) as ei:
        L.convert_input(old, lut_files=["L"], descriptor=None, adapter="a")
    assert reason_of(ei) == "process_key_unmapped"
    assert detail_of(ei) == "z"
