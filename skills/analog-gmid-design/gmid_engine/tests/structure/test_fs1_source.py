"""FS-1 구조 단언 (interface card 20261107-fs1 §7 G-1~G-5). oracle (구조): AST·텍스트 grep (card 가 적은 규칙). 엔진 소스를 AST·텍스트로 훑는다.
각 test 는 훑은 파일 수 >= 1 을 먼저 단언한다(공허 통과 방지). 사라지는 이름은 이 파일 자신이 grep 에 걸리지 않게 조각으로 이어 붙인다.
"""
import ast
import importlib
import pathlib
import re
import subprocess

import pytest

ENGINE = pathlib.Path(__file__).resolve().parents[2]
BASE_COMMIT = "f42a13f8"          # interface §7 G-2 (a): card base -- base 집합은 test 가 이 커밋에서 같은 AST 규칙으로 센다


def _py():
    out = []
    for p in sorted(ENGINE.rglob("*.py")):
        rel = p.relative_to(ENGINE).parts
        if "tests" in rel or "__pycache__" in rel:
            continue
        out.append(p)
    return out


def _text(p):
    return p.read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- G-1 writer 하나
def test_g1_wf_start_and_dc_finger_have_one_writer_each():
    from gmid_engine.search import s0_fields as F
    from gmid_engine.sizing import S2_WRITERS
    assert F.SEARCH_S0_WRITERS.writer_of("graph", "wf_start") == "start_intervals"
    assert S2_WRITERS.writer_of("device", "dc_finger") == "dc_solve"
    writers = [w for kf, w in F.SEARCH_S0_WRITERS.entries if kf == ("graph", "wf_start")]
    assert writers == ["start_intervals"]


# ---------------------------------------------------------------- G-2 폐포 구현 하나
def _reads_matching_groups(tree):
    """@compute_block(..., reads=(... ("graph", "matching_groups") ...)) 데코레이터를 가진 함수 이름 목록."""
    names = []
    consts = {}                                                       # 모듈 수준 `NAME = (...)` 대입 (reads=READS 꼴을 따라간다)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    consts[t.id] = node.value

    def has_pair(root, depth=0):
        for sub in ast.walk(root):
            if isinstance(sub, ast.Tuple) and [getattr(e, "value", None) for e in sub.elts] == ["graph", "matching_groups"]:
                return True
            if isinstance(sub, ast.Name) and sub.id in consts and depth < 3 and sub is not root and has_pair(consts[sub.id], depth + 1):
                return True
        return isinstance(root, ast.Name) and root.id in consts and depth < 3 and has_pair(consts[root.id], depth + 1)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and getattr(dec.func, "id", getattr(dec.func, "attr", None)) == "compute_block":
                    if has_pair(dec):
                        names.append(node.name)
                        break
    return sorted(set(names))


def _base_readers():
    rel = ENGINE.relative_to(pathlib.Path(subprocess.run(["git", "-C", str(ENGINE), "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                                                         check=True).stdout.strip()))
    top = subprocess.run(["git", "-C", str(ENGINE), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
    files = subprocess.run(["git", "-C", top, "ls-tree", "-r", "--name-only", BASE_COMMIT, "--", rel.as_posix()],
                           capture_output=True, text=True, check=True).stdout.split()
    names = []
    scanned = 0
    for f in files:
        if not f.endswith(".py") or "/tests/" in f:
            continue
        src = subprocess.run(["git", "-C", top, "show", "%s:%s" % (BASE_COMMIT, f)], capture_output=True, text=True, check=True,
                             encoding="utf-8").stdout
        scanned += 1
        names += _reads_matching_groups(ast.parse(src))
    assert scanned > 50
    return sorted(set(names))


def test_g2a_only_start_intervals_is_new_reader_of_matching_groups():
    now = []
    for p in _py():
        now += _reads_matching_groups(ast.parse(_text(p)))
    assert sorted(set(now)) == sorted(set(_base_readers()) | {"start_intervals"})
    assert "start_intervals" in now                                       # 양성 대조


def test_g2b_wf_start_value_defined_once_and_called_only_from_start_intervals():
    defs, callers = [], set()
    for p in _py():
        for node in ast.walk(ast.parse(_text(p))):
            if isinstance(node, ast.FunctionDef) and node.name == "wf_start_value":
                defs.append(str(p.relative_to(ENGINE)))
            if isinstance(node, ast.Call):
                f = node.func
                if (f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)) == "wf_start_value":
                    callers.add(str(p.relative_to(ENGINE)).replace("\\", "/"))
    assert len(defs) == 1
    assert callers == {"search/start_intervals.py"}


def test_g2c_member_union_code_lives_in_one_file():
    """matching_groups 값의 members 를 합치는 코드(AST: 'matching_groups' 를 읽는 함수 안 union·|=·update 집합 연산 또는 union-find 꼴 find/parent 이름)
    = search/wf_start.py 한 파일."""
    files = set()
    scanned = 0
    for p in _py():
        rel = str(p.relative_to(ENGINE)).replace("\\", "/")
        if not (rel.startswith("search/") or rel.startswith("sizing/")) or rel.count("/") != 1:
            continue
        scanned += 1
        for fn in ast.walk(ast.parse(_text(p))):
            if not isinstance(fn, ast.FunctionDef):
                continue
            reads = any(isinstance(n, ast.Constant) and n.value == "matching_groups" for n in ast.walk(fn))
            if not reads:
                continue
            for n in ast.walk(fn):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("union", "update")) \
                        or (isinstance(n, ast.AugAssign) and isinstance(n.op, ast.BitOr)) \
                        or (isinstance(n, ast.FunctionDef) and n.name == "find") \
                        or (isinstance(n, ast.Name) and n.id == "parent"):
                    files.add(rel)
    assert scanned > 10
    assert files == {"search/wf_start.py"}


# ---------------------------------------------------------------- G-3 옛 이름 0
OLD = ["finger_" + "slice", "Finger" + "Slice", "reachable_" + "slices", "slice_" + "cycle", "REASON_SLICE_" + "CYCLE", "slice_" + "rounds",
       "Realized" + "Finger", "polish_l_" + "cells"]


def test_g3_removed_names_zero_in_engine_sources():
    files = _py()
    assert len(files) > 100
    hits = {}
    for p in files:
        t = _text(p)
        rel = str(p.relative_to(ENGINE)).replace("\\", "/")
        for pat in OLD:
            if re.search(r"(?<![A-Za-z0-9_])" + re.escape(pat) + r"(?![A-Za-z0-9_])", t):
                hits.setdefault(pat, []).append(rel)
        if re.search(r"\.w_f_m\b", t):                       # FingerGeom 칸 w_f_m 쓰기·읽기 0 (slice_of_finger 의 인자 이름 w_f_m 은 허용)
            hits.setdefault(".w_f_m", []).append(rel)
        if rel != "lut/slice_of_finger.py" and re.search(r"\bw_f_m=", t):
            hits.setdefault("w_f_m=", []).append(rel)
    assert hits == {}, hits


# ---------------------------------------------------------------- G-4 공개 이름·파일
def test_g4_removed_public_names_and_file():
    names = ["finger_" + "slice", "Finger" + "Slice", "reachable_" + "slices", "WHY_NO_" + "W_HI", "WHY_NO_" + "CANDIDATE", "REASON_SLICE_" + "CYCLE",
             "slice_" + "cycle", "slice_" + "rounds", "Realized" + "Finger", "polish_l_" + "cells"]
    seen = 0
    for mod in ("gmid_engine.lut", "gmid_engine.sizing", "gmid_engine.search"):
        m = importlib.import_module(mod)
        seen += len(dir(m))
        for n in names:
            assert not hasattr(m, n), (mod, n)
    assert seen > 100
    assert not (ENGINE / "lut" / ("finger_" + "slice.py")).exists()
    assert hasattr(importlib.import_module("gmid_engine.sizing"), "realize_fingers")           # 양성 대조: 새 이름은 있다


# ---------------------------------------------------------------- [v6.39.5] G-8 짝 정의 하나
# oracle (구조): interface §7 G-8 -- `git grep` 비test 엔진에 해당하는 텍스트·AST 규칙. 옛 이름은 이 파일 자신이 걸리지 않게 조각으로 이어 붙인다(tests 는 훑지 않지만 관례).
_OLD_PARTNER = ["kvl_" + "partner", "_symmetric_" + "partner"]


def _rel(p):
    return str(p.relative_to(ENGINE)).replace("\\", "/")


def test_g8_old_partner_names_zero_and_start_partner_defined_once_called_from_one_module():
    files = _py()
    assert len(files) > 100
    old_hits = {}
    defs, callers = [], set()
    for p in files:
        t = _text(p)
        for pat in _OLD_PARTNER:
            if re.search(r"(?<![A-Za-z0-9_])" + re.escape(pat) + r"(?![A-Za-z0-9_])", t):
                old_hits.setdefault(pat, []).append(_rel(p))
        for node in ast.walk(ast.parse(t)):
            if isinstance(node, ast.FunctionDef) and node.name == "start_partner":
                defs.append(_rel(p))
            if isinstance(node, ast.Call):
                f = node.func
                if (f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)) == "start_partner":
                    callers.add(_rel(p))
    assert old_hits == {}, old_hits
    assert defs == ["search/wf_partner.py"]
    assert callers == {"search/start_intervals.py"}


def test_g8_reference_start_strings_are_defined_in_one_place():
    """"wf_start_reference"·"reference_start_undefined"·"no_member_partner" 문자열(AST 상수 전체 일치) 정의 자리 = search/wf_start.py 하나 (각각)."""
    want = ["wf_start_reference", "reference_start_undefined", "no_member_partner"]
    places = {w: set() for w in want}
    scanned = 0
    for p in _py():
        scanned += 1
        for node in ast.walk(ast.parse(_text(p))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in places:
                places[node.value].add(_rel(p))
    assert scanned > 100
    assert places == {w: {"search/wf_start.py"} for w in want}, places


# ---------------------------------------------------------------- [v6.39.5] G-9 l_defined = lut 공개 L 위치 판정 하나
# oracle (구조): interface §7 G-9 (AST + inspect). `l_defined` 인자로 넘기는 callable(출발 블록 안)의 본문(같은 모듈 함수 호출은 따라간다)이 부르는 LUT 공개 이름이 정확히 하나이고,
# 그 이름은 `gmid_engine.lut.__all__` 에 있으며 `op_point` 가 정의된 모듈 전역의 같은 이름과 같은 함수 객체(`is`)다. 본문에 op_point·곡선 조회 호출과 전압 이름 참조 0.
_VOLT = {"vgs", "vds", "vsb", "VGS", "VDS", "VSB"}


def _call_name(call):
    f = call.func
    return f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)


def _l_defined_nodes(tree):
    """start_intervals.py 에서 `wf_start_value(...)` 호출의 9째 위치 인자 또는 `l_defined=` 키워드 -> 그 callable 의 본문 노드들(모듈 안 함수 호출은 3단계까지 따라감)."""
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assigns = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    assigns[t.id] = n.value
    arg = None
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and _call_name(n) == "wf_start_value":
            kw = [k.value for k in n.keywords if k.arg == "l_defined"]
            arg = kw[0] if kw else (n.args[8] if len(n.args) > 8 else None)
    assert arg is not None, "wf_start_value 호출에서 l_defined 인자를 찾지 못했다"

    def roots(node, depth=0):
        assert depth < 4, "l_defined callable 을 해석하지 못했다"
        if isinstance(node, ast.Lambda):
            return [node]
        if isinstance(node, ast.Call):
            return roots(ast.Name(id=_call_name(node)), depth + 1)
        if isinstance(node, ast.Name):
            if node.id in funcs:
                return [funcs[node.id]]
            if node.id in assigns:
                return roots(assigns[node.id], depth + 1)
        raise AssertionError("l_defined callable 을 해석하지 못했다: %r" % (ast.dump(node)[:120],))
    out, seen, todo = [], set(), roots(arg)
    while todo:
        nd = todo.pop()
        if id(nd) in seen:
            continue
        seen.add(id(nd))
        out.append(nd)
        for sub in ast.walk(nd):
            if isinstance(sub, ast.Call) and _call_name(sub) in funcs and len(seen) < 40:
                todo.append(funcs[_call_name(sub)])
    return out


def test_g9a_l_defined_is_the_one_public_lut_l_position_judgement():
    lut = importlib.import_module("gmid_engine.lut")
    p = ENGINE / "search" / "start_intervals.py"
    assert p.is_file()
    nodes = _l_defined_nodes(ast.parse(_text(p)))
    assert nodes
    called, voltage = set(), set()
    for nd in nodes:
        for sub in ast.walk(nd):
            if isinstance(sub, ast.Call):
                called.add(_call_name(sub))
            if isinstance(sub, ast.Name) and sub.id in _VOLT:
                voltage.add(sub.id)
            if isinstance(sub, ast.arg) and sub.arg in _VOLT:
                voltage.add(sub.arg)
            if isinstance(sub, ast.Attribute) and sub.attr in _VOLT:
                voltage.add(sub.attr)
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value in _VOLT:
                voltage.add(sub.value)
    assert voltage == set(), voltage                                                     # 전압 이름 참조 0
    public = set(lut.__all__)
    lut_calls = sorted(c for c in called if c in public)
    assert len(lut_calls) == 1, lut_calls                                                # 부르는 LUT 공개 이름 = 하나
    name = lut_calls[0]
    assert not name.startswith("_")
    assert "op_point" not in called and "curve_value" not in called and not [c for c in called if c and c.startswith("curve_bundle")]
    # op_point 가 L 단계에서 부르는 것과 같은 함수 객체 (op_point 모듈 전역의 그 이름 is lut 공개 이름)
    import inspect
    mod = inspect.getmodule(lut.op_point)
    assert mod is not None and getattr(mod, name, None) is getattr(lut, name)


def _bin_hits(src):
    """한 파일 소스의 L bin 판정 접근 목록: `l_bins`·`anchor_bin`·`bin_rule` 속성 읽기, `_helpers_anchor` import."""
    hits = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Attribute) and n.attr in ("l_bins", "anchor_bin", "bin_rule"):
            hits.append(n.attr)
        if isinstance(n, ast.ImportFrom) and ((n.module or "").split(".")[-1] == "_helpers_anchor" or any(a.name == "_helpers_anchor" for a in n.names)):
            hits.append("_helpers_anchor")
        if isinstance(n, ast.Import) and any(a.name.split(".")[-1] == "_helpers_anchor" for a in n.names):
            hits.append("_helpers_anchor")
    return hits


def test_g9b_no_new_l_bin_judgement_code_in_search():
    """G-9 (b): 비test `E/search/*.py` 에 L bin 판정 코드 0 -- 문언대로 읽으면 이 card 와 무관한 as-built 사용처(iv_gain_l·iv_matching_l·find_front 등, card base `f42a13f8` 에서 이미 12곳)까지
    지워야 한다. 판정 의도('search 쪽 l_defined 가 L bin 판정을 새로 구현하지 않는다')에 맞춰 두 단언으로 나눴다 (오케스트레이터 확인 요청 -- 보고 참조):
    (1) FS-1 출발 경로 파일(start_intervals·wf_start·wf_partner·wf_member_w·initial_wf)은 0 (2) 어느 search 파일도 card base 의 그 파일 hit 수를 넘지 않는다(새 hit 0)."""
    top = subprocess.run(["git", "-C", str(ENGINE), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
    rel_engine = ENGINE.relative_to(pathlib.Path(top)).as_posix()
    scanned, over, start_path = 0, [], {}
    for p in _py():
        rel = _rel(p)
        if not (rel.startswith("search/") and rel.count("/") == 1):
            continue
        scanned += 1
        now = _bin_hits(_text(p))
        if rel in ("search/start_intervals.py", "search/wf_start.py", "search/wf_partner.py", "search/wf_member_w.py", "search/initial_wf.py"):
            start_path[rel] = now
        shown = subprocess.run(["git", "-C", top, "show", "%s:%s/%s" % (BASE_COMMIT, rel_engine, rel)], capture_output=True, text=True, encoding="utf-8")
        before = _bin_hits(shown.stdout) if shown.returncode == 0 else []
        if len(now) > len(before):
            over.append((rel, len(before), len(now)))
    assert scanned > 10 and "search/start_intervals.py" in start_path
    assert {k for k, v in start_path.items() if v} == set(), start_path
    assert over == [], over


# ---------------------------------------------------------------- G-5 realize_fingers.py 순수성
def test_g5_realize_fingers_single_entry_and_no_graph_import():
    p = ENGINE / "sizing" / "realize_fingers.py"
    assert p.is_file()
    tree = ast.parse(_text(p))
    public = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
    assert public == ["realize_fingers"]
    mods, names = [], []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods += [a.name for a in n.names]
            names += [a.asname or a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            mods.append(n.module or "")
            names += [a.name for a in n.names]
    assert mods                                                              # import 가 있는 파일을 훑었다
    assert not [m for m in mods if "graph" in m.split(".") or "snapshot" in m.lower()]
    assert not [x for x in names if "graph" in x.lower() or "snapshot" in x.lower()]
