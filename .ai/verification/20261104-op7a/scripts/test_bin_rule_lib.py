"""card 20261104-op7a toy test (interface card 20261104-op7a.interface.md 4절).

oracle: 전부 (d) 선언된 스펙값 + (a) 구성으로 정해진 합성 입력. 기대값은 interface의 toy 표와
격자 정수(손 유도)에서 가져온다. 피검 함수로 기대값을 만들지 않는다. sha256 기대값은 hashlib 직접 호출
(다른 방법의 독립 계산, oracle b).
"""
import copy
import hashlib

import pytest

import bin_rule_lib as B
from bin_rule_lib import BinRuleStop

G = 5e-9


def _bin(model, lmin, lmax, wmin, wmax):
    return {"model": model, "lmin": lmin, "lmax": lmax, "wmin": wmin, "wmax": wmax}


# interface 4절 공통 bin 표 T (d: 선언된 toy 표)
T = [
    _bin("m.0", 0.15e-6, 0.18e-6, 3e-6, 5e-6),
    _bin("m.1", 0.18e-6, 0.25e-6, 3e-6, 5e-6),
    _bin("m.2", 0.15e-6, 0.18e-6, 5e-6, 7e-6),
    _bin("m.3", 0.18e-6, 0.25e-6, 5e-6, 7e-6),
]
M = {b["model"]: b for b in T}


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _idx(x):
    # 격자 정수의 손 정의(원칙: 소속 비교는 정수끼리). 0.18 um / 5 nm = 36 등 손 유도와 일치 확인용.
    return round(x / G)


# ---------------------------------------------------------------- T-1
def test_t1a_tie_L():
    # (d) T-1a: 0.18 um은 m.0.lmax = m.1.lmin, W=4 um는 두 bin 안
    assert B.tie_axes(0.18e-6, 4e-6, T, G) == ("L",)


@pytest.mark.parametrize("l", [0.2e-6, 0.185e-6, 0.15e-6])
def test_t1b_no_tie(l):
    # (d) T-1b: 경계가 아니거나(0.2, 0.185), 이웃 bin 없는 바깥 경계(0.15)
    assert B.tie_axes(l, 4e-6, T, G) == ()


def test_t1c_tie_W():
    # (d) T-1c: L=0.2 um 안, W=5 um = m.1.wmax = m.3.wmin
    assert B.tie_axes(0.2e-6, 5e-6, T, G) == ("W",)


def test_t1d_tie_LW():
    # (d) T-1d
    assert B.tie_axes(0.18e-6, 5e-6, T, G) == ("L", "W")


def test_t1e_float_roundtrip():
    # (a) T-1e: 1e-12 상대 섭동은 격자 정수 36을 바꾸지 않는다
    assert B.tie_axes(0.18e-6 * (1 + 1e-12), 4e-6, T, G) == ("L",)


def test_t1f_anchor_set():
    # (a) T-1f: 손 유도 격자 정수 0.15->30, 0.18->36, 0.20->40, 합집합 3개
    r = B.anchor_set([[0.18e-6, 0.2e-6], [0.18e-6 * (1 + 1e-12), 0.15e-6]], G)
    assert len(r) == 3
    assert [round(v / G) for v in r] == [30, 36, 40]
    assert r[1] == 0.18e-6  # 처음 나온 float


def test_grid_index_definition():
    # (d) 정의 round(x/g): 0.18e-6 -> 36, 5e-6 -> 1000
    assert B.grid_index(0.18e-6, G) == 36
    assert B.grid_index(5e-6, G) == 1000


# ---------------------------------------------------------------- T-2
def test_t2a():
    # (d) T-2a
    assert B.point_direction(0.18e-6, 4e-6, M["m.0"], T, G) == {"L": "lower"}
    assert B.point_direction(0.18e-6, 4e-6, M["m.1"], T, G) == {"L": "upper"}


def test_t2b():
    # (d) T-2b
    assert B.point_direction(0.2e-6, 5e-6, M["m.1"], T, G) == {"W": "lower"}
    assert B.point_direction(0.2e-6, 5e-6, M["m.3"], T, G) == {"W": "upper"}


def test_t2c():
    # (d) T-2c
    assert B.point_direction(0.18e-6, 5e-6, M["m.0"], T, G) == {"L": "lower", "W": "lower"}
    assert B.point_direction(0.18e-6, 5e-6, M["m.3"], T, G) == {"L": "upper", "W": "upper"}
    assert B.point_direction(0.18e-6, 5e-6, M["m.2"], T, G) == {"L": "lower", "W": "upper"}


def test_t2d_no_tie():
    # (d) T-2d
    assert B.point_direction(0.2e-6, 4e-6, M["m.1"], T, G) == {}


def test_t2e_bin_outside():
    # (d) T-2e: m.0은 L<=0.18이라 0.2를 품지 않는다
    with pytest.raises(BinRuleStop) as e:
        B.point_direction(0.2e-6, 4e-6, M["m.0"], T, G)
    assert e.value.reason == "bin_outside"


def test_t2f_tie_interior():
    # (d) T-2f: chosen이 경계 0.18을 안쪽에 둔다(0.15..0.25)
    x = _bin("x", 0.15e-6, 0.25e-6, 3e-6, 5e-6)
    with pytest.raises(BinRuleStop) as e:
        B.point_direction(0.18e-6, 4e-6, x, T, G)
    assert e.value.reason == "tie_interior"


# ---------------------------------------------------------------- T-3
@pytest.mark.parametrize("ds", [[], [{}]])
def test_t3a(ds):
    assert B.derive_rule(ds) == (None, "no_tie_point")


def test_t3b():
    assert B.derive_rule([{"L": "lower"}, {}, {"W": "lower"}]) == ("lower", None)


def test_t3c():
    assert B.derive_rule([{"L": "upper"}]) == ("upper", None)


@pytest.mark.parametrize("ds", [[{"L": "lower"}, {"L": "upper"}], [{"L": "lower", "W": "upper"}]])
def test_t3d(ds):
    assert B.derive_rule(ds) == (None, "mixed_direction")


# ---------------------------------------------------------------- T-4
def test_t4a_machine_dependent():
    # (b) T-4a: hashlib 직접 계산
    a = b"x\r\ny\n"
    lf, md = B.union_model_sha([("a", _sha(a))], lambda p: a)
    assert lf == [_sha(b"x\ny\n")]
    assert md == ["a"]


def test_t4b_record_is_lf():
    a = b"x\r\ny\n"
    lf, md = B.union_model_sha([("a", _sha(b"x\ny\n"))], lambda p: a)
    assert lf == [_sha(b"x\ny\n")]
    assert md == []


def test_t4c_same_value_two_paths():
    b = b"z\n"
    lf, md = B.union_model_sha([("p", _sha(b)), ("q", _sha(b))], lambda p: b)
    assert lf == [_sha(b)]
    assert md == []


def test_t4d_mismatch():
    with pytest.raises(BinRuleStop) as e:
        B.union_model_sha([("a", "0" * 64)], lambda p: b"abc")
    assert e.value.reason == "record_sha_mismatch"
    assert e.value.detail == "a"


def test_t4d_missing():
    def rb(p):
        raise FileNotFoundError(p)

    with pytest.raises(BinRuleStop) as e:
        B.union_model_sha([("a", "0" * 64)], rb)
    assert e.value.reason == "record_file_missing"
    assert e.value.detail == "a"


def test_t4_sorted_unique_output():
    # (a) 구성: 두 파일 값 오름차순, 기계 의존 경로 오름차순
    files = {"b": b"1\r\n", "a": b"2\r\n"}
    recs = [(p, _sha(v)) for p, v in files.items()]
    lf, md = B.union_model_sha(recs, lambda p: files[p])
    assert lf == sorted([_sha(b"1\n"), _sha(b"2\n")])
    assert md == ["a", "b"]


# ---------------------------------------------------------------- T-5
def test_t5a():
    r = B.set_versions({"a": "ngspice-46", "b": "ngspice-46", "c": None})
    assert r == (("ngspice", "46"), ("c",))


def test_t5b_mixed():
    with pytest.raises(BinRuleStop) as e:
        B.set_versions({"a": "ngspice-46", "b": "ngspice-45"})
    assert e.value.reason == "simulator_version_mixed"


def test_t5b_unrecorded():
    with pytest.raises(BinRuleStop) as e:
        B.set_versions({"a": None})
    assert e.value.reason == "simulator_version_unrecorded"


@pytest.mark.parametrize("t", ["46", "ngspice-"])
def test_t5c_unparsed(t):
    with pytest.raises(BinRuleStop) as e:
        B.split_version(t)
    assert e.value.reason == "simulator_version_unparsed"


def test_t5_split_last_dash():
    # (d) 마지막 '-'로 나눈다
    assert B.split_version("ngspice-46") == ("ngspice", "46")
    assert B.split_version("a-b-7") == ("a-b", "7")


# ---------------------------------------------------------------- T-6
def test_t6():
    assert B.spiceinit_sha("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert B.spiceinit_sha("set ngbehavior=hsa\n") == _sha(b"set ngbehavior=hsa\n")


# ---------------------------------------------------------------- T-7
S1 = min(_sha(b"a"), _sha(b"b"))
S2 = max(_sha(b"a"), _sha(b"b"))


def _decl(s1=S1, s2=S2):
    return B.build_decl([s1, s2], ("ngspice", "46"), "default", "", "lower",
                        [(1.8e-7, 4e-6, "m.0")], "2026-11-04")


def test_t7a_valid():
    d = _decl()
    assert B.validate_decl(d) == []
    # 닫힌 스키마 기대 (interface 2절)
    assert d["schema"] == "lut_bin_rule/1"
    assert d["evidence"]["measured_by"] == "verifier"
    assert d["evidence"]["mode"] == "default"
    assert d["compat"]["spiceinit_sha256"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert d["model_files_sha256"] == [S1, S2]
    assert d["rule"] == "lower"


def _mut_top(d):
    d["x"] = 1


def _mut_rule(d):
    d["rule"] = "both"


def _mut_schema(d):
    d["schema"] = "lut_bin_rule/2"


def _mut_spiceinit(d):
    d["compat"]["spiceinit_sha256"] = "0" * 64


def _mut_empty_models(d):
    d["model_files_sha256"] = []


def _mut_reverse(d):
    d["model_files_sha256"] = [S2, S1]


def _mut_dup(d):
    d["model_files_sha256"] = [S1, S1]


def _mut_points_empty(d):
    d["evidence"]["points"] = []


def _mut_chosen(d):
    del d["evidence"]["points"][0]["chosen_bin"]


def _mut_ev_mode(d):
    d["evidence"]["mode"] = "hsa"


def _mut_sim(d):
    d["simulator"]["extra"] = 1


@pytest.mark.parametrize("mut,ptr", [
    (_mut_top, "/x"),
    (_mut_rule, "/rule"),
    (_mut_schema, "/schema"),
    (_mut_spiceinit, "/compat/spiceinit_sha256"),
    (_mut_empty_models, "/model_files_sha256"),
    (_mut_reverse, "/model_files_sha256"),
    (_mut_dup, "/model_files_sha256"),
    (_mut_points_empty, "/evidence/points"),
    (_mut_chosen, "/evidence/points/0"),
    (_mut_ev_mode, "/evidence/mode"),
    (_mut_sim, "/simulator"),
])
def test_t7b_mutations(mut, ptr):
    d = copy.deepcopy(_decl())
    mut(d)
    assert B.validate_decl(d) == [ptr]


def test_t7c_hex_format():
    assert B.validate_decl(_decl(s1="ABC")) == ["/model_files_sha256"]


# ---------------------------------------------------------------- T-8, T-9
@pytest.mark.parametrize("args,exp", [
    (("lower", "upper", "upper"), ("ok", "home_read_isolated")),
    (("lower", "upper", "lower"), ("ok", "home_not_read")),
    (("lower", "lower", "upper"), ("stop", "control_not_discriminating")),
    ((None, "upper", "upper"), ("stop", "default_undetermined")),
    (("lower", None, "upper"), ("stop", "control_undetermined")),
    (("lower", "upper", None), ("stop", "control_undetermined")),
])
def test_t8_judge_controls(args, exp):
    assert B.judge_controls(*args) == exp


def test_t8b_judge_empty_init():
    assert B.judge_empty_init({"p0": "m.0"}, {"p0": "m.0"}) == ("ok", None)
    assert B.judge_empty_init({"p0": "m.0"}, {"p0": "m.1"}) == ("stop", "control_undetermined")


def test_t9_isolated_env():
    env = {"HOME": "x", "USERPROFILE": "y", "HOMEDRIVE": "C:", "HOMEPATH": "z",
           "SPICE_USERINIT_DIR": "u", "PATH": "p"}
    before = copy.deepcopy(env)
    out = B.isolated_env(env, "h")
    assert out == {"HOME": "h", "USERPROFILE": "h", "PATH": "p"}
    assert env == before


# ---------------------------------------------------------------- T-10
def test_t10_netlist_lines():
    got = B.netlist_lines("sub", ['.include "a"'], [(0.18, 5.0), (20.0, 0.42)])
    assert got == [
        '* bin probe sub', '.include "a"',
        'vgs g 0 dc 0', 'vds d 0 dc 0', 'vsrc s 0 dc 0', 'vb b 0 dc 0',
        'xp0 d g s b sub l=0.18u w=5u',
        'xp1 d g s b sub l=20u w=0.42u',
        '.control', 'op',
        'echo SHOWMOD p0', 'showmod m.xp0.msub : lmin lmax wmin wmax',
        'echo SHOWMOD p1', 'showmod m.xp1.msub : lmin lmax wmin wmax',
        'quit', '.endc', '.end',
    ]


# ---------------------------------------------------------------- T-11
_P0 = "SHOWMOD p0\nlmin 1.5e-07\nlmax 1.8e-07\nwmin 3e-06\nwmax 5e-06\n"
_P1 = "SHOWMOD p1\nlmin 1.8e-07\nlmax 2.5e-07\nwmin 5e-06\nwmax 7e-06\n"


def test_t11a():
    assert B.parse_probe_log(_P0 + _P1, T, G) == {"p0": "m.0", "p1": "m.3"}


def test_t11a_ignores_other_lines():
    # interface: SHOWMOD/네 경계 키가 아닌 줄은 무시
    noise = "ngspice 46 banner\n" + _P0 + "some other line 123\n" + _P1
    assert B.parse_probe_log(noise, T, G) == {"p0": "m.0", "p1": "m.3"}


def test_t11b_incomplete():
    txt = _P0.replace("wmax 5e-06\n", "") + _P1
    with pytest.raises(BinRuleStop) as e:
        B.parse_probe_log(txt, T, G)
    assert e.value.reason == "showmod_incomplete"


def test_t11b_unmatched():
    txt = _P0.replace("lmin 1.5e-07", "lmin 1.0e-07")
    with pytest.raises(BinRuleStop) as e:
        B.parse_probe_log(txt, T, G)
    assert e.value.reason == "showmod_bin_unmatched"


def test_t11b_ambiguous():
    dup = T + [_bin("m.0dup", 0.15e-6, 0.18e-6, 3e-6, 5e-6)]
    with pytest.raises(BinRuleStop) as e:
        B.parse_probe_log(_P0, dup, G)
    assert e.value.reason == "showmod_bin_ambiguous"


# ---------------------------------------------------------------- T-12
def test_t12a():
    r = B.w_boundary_points(T, G)
    assert len(r) == 2
    # 손 유도: L 중점 (0.15+0.18)/2 = 0.165 um -> 33, (0.18+0.25)/2 = 0.215 -> 43; W 5 um -> 1000
    assert [(round(l / G), round(w / G)) for l, w in r] == [(33, 1000), (43, 1000)]


def test_t12b_no_interior():
    a = _bin("a", 0.18e-6, 0.18e-6, 3e-6, 5e-6)
    b = _bin("b", 0.18e-6, 0.18e-6, 5e-6, 7e-6)
    with pytest.raises(BinRuleStop) as e:
        B.w_boundary_points([a, b], G)
    assert e.value.reason == "w_boundary_no_interior"


def test_t12b_no_w_boundary():
    assert B.w_boundary_points([M["m.0"], M["m.1"]], G) == ()


def test_t12c_not_product():
    a = _bin("a", 0.15e-6, 0.25e-6, 3e-6, 5e-6)
    b = _bin("b", 0.18e-6, 0.25e-6, 5e-6, 7e-6)
    with pytest.raises(BinRuleStop) as e:
        B.w_boundary_points([a, b], G)
    assert e.value.reason == "w_boundary_not_product"


# ---------------------------------------------------------------- T-16 slice_tie_cells
# oracle (d)+(a): interface T-16 표. 격자 정수는 손 유도(0.18um/5nm=36, 0.2um=40, 4um=800, 5um=1000).
_M16 = {(36, 800): ("m.0", "m.1"), (40, 800): ("m.1", "m.1")}
_PER16 = {"0.18": "m.0", "0.2": "m.1"}


def test_t16a_cells():
    # 0.18은 L 동률 칸, 0.2는 동률 아님 -> 칸 하나. 기록 m.0, 기본 m.0, 대조 m.1
    got = B.slice_tie_cells([0.18e-6, 0.2e-6], 4e-6, dict(_PER16), dict(_M16), T, G)
    assert got == [{"l_m": 0.18e-6, "w_m": 4e-6, "recorded": "m.0", "default": "m.0", "hsa": "m.1"}]


def test_t16b_recorded_key_absent():
    got = B.slice_tie_cells([0.18e-6, 0.2e-6], 4e-6, {"0.2": "m.1"}, dict(_M16), T, G)
    assert len(got) == 1
    assert got[0]["recorded"] is None


def test_t16b_unmeasured():
    got = B.slice_tie_cells([0.18e-6, 0.2e-6], 4e-6, dict(_PER16), {}, T, G)
    assert len(got) == 1
    assert got[0]["default"] is None and got[0]["hsa"] is None
    assert got[0]["recorded"] == "m.0"


@pytest.mark.parametrize("per_l", [
    None,                                  # per_l 없음
    {"x": "m.0"},                          # 키가 숫자 아님
    {"0.18": "m.0", "0.1800000001": "m.1"},  # 두 키가 같은 격자 정수 36
    {"0.18": 7},                           # 값이 문자열 아님
])
def test_t16c_source_record_missing(per_l):
    with pytest.raises(BinRuleStop) as e:
        B.slice_tie_cells([0.18e-6, 0.2e-6], 4e-6, per_l, dict(_M16), T, G)
    assert e.value.reason == "source_record_missing"


def test_t16c_not_dict():
    # 구성: dict 아닌 per_l(리스트)
    with pytest.raises(BinRuleStop) as e:
        B.slice_tie_cells([0.18e-6], 4e-6, [("0.18", "m.0")], dict(_M16), T, G)
    assert e.value.reason == "source_record_missing"


def test_t16d_W_tie_is_cell():
    # L=0.2 um 안, W=5 um = m.1.wmax = m.3.wmin -> W 동률도 칸. 격자 정수 (40, 1000)
    got = B.slice_tie_cells([0.2e-6], 5e-6, {"0.2": "m.1"}, {(40, 1000): ("m.1", "m.3")}, T, G)
    assert got == [{"l_m": 0.2e-6, "w_m": 5e-6, "recorded": "m.1", "default": "m.1", "hsa": "m.3"}]


def test_t16_no_tie_cells_empty():
    # 구성: 0.2 um, 4 um는 동률 아님 -> 칸 없음
    assert B.slice_tie_cells([0.2e-6], 4e-6, {"0.2": "m.1"}, dict(_M16), T, G) == []


# ---------------------------------------------------------------- T-17 record_source_mode
# oracle (d): interface T-17 표(이름 비교, 합성 칸)
def _c(r, d, h):
    return {"l_m": 1.0, "w_m": 1.0, "recorded": r, "default": d, "hsa": h}


def test_t17a_default():
    # 칸1: 기록=기본(a), 칸2: 기록=기본(x) -> "default"
    assert B.record_source_mode([_c("a", "a", "b"), _c("x", "x", "y")], "default") == "default"


def test_t17b_hsa():
    assert B.record_source_mode([_c("b", "a", "b")], "hsa") == "hsa"


@pytest.mark.parametrize("cells,declared,reason", [
    ([], "default", "source_no_tie_cell"),
    ([_c(None, "a", "b")], "default", "source_record_missing"),
    ([_c("a", None, "b")], "default", "source_cell_unmeasured"),
    ([_c("a", "a", None)], "default", "source_cell_unmeasured"),
    ([_c("a", "a", "a")], "default", "source_record_both_modes"),
    ([_c("z", "a", "b")], "default", "source_record_no_mode"),
    ([_c("a", "a", "b"), _c("b", "a", "b")], "default", "source_record_mixed"),
    ([_c("b", "a", "b")], "default", "source_mode_differs"),
    ([_c("b", "a", "b"), _c(None, "a", "b")], "default", "source_record_missing"),  # 칸 사유가 먼저
])
def test_t17_stops(cells, declared, reason):
    with pytest.raises(BinRuleStop) as e:
        B.record_source_mode(cells, declared)
    assert e.value.reason == reason


def test_t17_detail_is_cell():
    # interface: detail = 그 칸
    cell = _c("z", "a", "b")
    with pytest.raises(BinRuleStop) as e:
        B.record_source_mode([cell], "default")
    assert e.value.detail == cell


# ---------------------------------------------------------------- T-18 combined_bin_check
def test_t18_ok():
    assert B.combined_bin_check({"p0": {"model": "m.0"}}, {"p0": "m.0"}) is None


@pytest.mark.parametrize("recorded,reason", [
    (None, "combined_bin_missing"),
    ({}, "combined_bin_missing"),
    ({"p0": {"lmin": 1}}, "combined_bin_unparsed"),     # model 키 없음
    ({"p0": "m.0"}, "combined_bin_unparsed"),            # 칸이 dict 아님
    ({"p1": {"model": "m.0"}}, "combined_bin_unmeasured"),
    ({"p0": {"model": "m.1"}}, "combined_bin_differs"),
])
def test_t18b_stops(recorded, reason):
    with pytest.raises(BinRuleStop) as e:
        B.combined_bin_check(recorded, {"p0": "m.0"})
    assert e.value.reason == reason


# ---------------------------------------------------------------- T-19 cap_bind_check
def test_t19_ok():
    assert B.cap_bind_check("a", "a") is None


@pytest.mark.parametrize("rec,pin,reason", [
    (None, "a", "cap_bind_missing"),
    ("a", None, "cap_bind_missing"),
    ("a", "b", "cap_bind_differs"),
])
def test_t19_stops(rec, pin, reason):
    with pytest.raises(BinRuleStop) as e:
        B.cap_bind_check(rec, pin)
    assert e.value.reason == reason


# ---------------------------------------------------------------- T-20 record_only_files
def test_t20a_record_only():
    # 기록 a/p = LF 값 l (닿는 파일 p와 같음), a/q = z (어느 값과도 다름) -> 기록 전용 a/q
    assert B.record_only_files({"p": ("l", "r")}, {"a/p": "l", "a/q": "z"}) == ("a/q",)


def test_t20a_record_is_raw():
    # 기록이 raw 값이어도 닿는 파일과 같으므로 기록 전용 없음
    assert B.record_only_files({"p": ("l", "r")}, {"a/p": "r"}) == ()


def test_t20_sorted():
    # 구성: 기록 전용 둘, 입력 순서와 무관하게 오름차순
    got = B.record_only_files({"p": ("l", "r")}, {"a/z": "9", "a/p": "l", "a/q": "8"})
    assert got == ("a/q", "a/z")


@pytest.mark.parametrize("reached,recorded", [
    ({"p": ("l", "r")}, {"a/q": "z"}),   # 닿는 파일 값이 기록에 없음
    ({"p": ("l", "r")}, None),
    ({"p": ("l", "r")}, {}),
    ({}, {"a/q": "z"}),                  # reached 빔
])
def test_t20b_include_not_recorded(reached, recorded):
    with pytest.raises(BinRuleStop) as e:
        B.record_only_files(reached, recorded)
    assert e.value.reason == "include_not_recorded"


def test_t20b_detail_path_when_file_unrecorded():
    # interface: 닿는 파일 값이 기록에 없으면 detail = 그 파일 경로
    with pytest.raises(BinRuleStop) as e:
        B.record_only_files({"p": ("l", "r")}, {"a/q": "z"})
    assert e.value.detail == "p"


def test_binrulestop_attrs():
    e = BinRuleStop("r", "d")
    assert e.reason == "r" and e.detail == "d"
    assert isinstance(e, Exception)
