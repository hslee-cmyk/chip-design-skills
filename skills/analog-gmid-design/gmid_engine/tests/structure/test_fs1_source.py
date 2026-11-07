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
