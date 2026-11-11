"""[NFR-4 card 2] core/blas_env.py -- BLAS 스레드 고정(interface card C1)과 재확인 지점 (a)~(e)(C2). test N-T1~N-T12.

계약(interface card nfr4c2 2절 C1·C2, 설계 40 §2.4.13 (1)):
- `import gmid_engine` 뒤 `os.environ["OPENBLAS_NUM_THREADS"] == "1"`, 적재된 OpenBLAS 라이브러리마다 조회 = 1 -- 호출자가 numpy 를 먼저 import 했어도,
  바깥 값이 1·8·18·미지정 어느 것이어도 같다.
- 거부 `RuntimeError`: 빌드 설정 BLAS 이름에 openblas 없음, openblas 기록의 set/get 기호 없음, 설정 뒤 조회 != 1, mkl·blis 기록, 지원 밖 플랫폼.
  config·corename·parallel 이 없으면 거부하지 않고 그 항목 값이 None.
- `BlasEnvironment` = (Python 구현·판, sys.platform, platform.machine(), numpy 판, scipy 판, BLAS 항목 tuple), 항목 = (family, 소유 패키지, 파일 이름,
  config, corename, parallel, 확인 스레드 수 = 1), 항목 순서 = 사전식 정렬(None 은 빈 문자열), frozen·hashable.
- 재확인 지점 (a) run_stage_a (b) build_search_context (c) find_front (d) layer0_start (e) solve_eps 진입 = blas_environment()(무상태).
- 교체 지점: 모듈 속성 `gmid_engine.core.blas_env.loaded_blas_modules`.

oracle: (독립) 하위 프로세스에서 ctypes 로 numpy·scipy `.libs` 의 OpenBLAS 를 직접 열어 조회·설정(피검 함수를 거치지 않는다), AST, glob.
(비교) 같은 함수 두 출력(`fp_of(blas_environment())`)을 서로 맞댄다 -- 기대값으로 쓰지 않는다. (손) 가짜 BlasModule 의 조회·기호는 test 가 정한다.
(Py) Python 표준 값(sys.platform·platform.machine()·판 문자열). 하위 프로세스는 모두 순차(subprocess.run)다.
"""
from __future__ import annotations

import ast
import dataclasses
import glob
import importlib.util
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parents[1]
SKILL = TESTS.parents[1]
ENGINE = SKILL / "gmid_engine"
FAMILIES = ("openblas", "mkl", "blis")
# OpenBLAS 조회·설정·정보 기호 후보(interface card C1 실측: numpy 64비트 접미 `..64_`, scipy 접미 없음). 순서대로 처음 있는 것을 쓴다.
GET_SYMS = ("scipy_openblas_get_num_threads64_", "scipy_openblas_get_num_threads", "openblas_get_num_threads64_", "openblas_get_num_threads")
SET_SYMS = ("scipy_openblas_set_num_threads64_", "scipy_openblas_set_num_threads", "openblas_set_num_threads64_", "openblas_set_num_threads")
CORE_SYMS = ("scipy_openblas_get_corename64_", "scipy_openblas_get_corename", "openblas_get_corename64_", "openblas_get_corename")
THREAD_ENV = ("OPENBLAS_NUM_THREADS", "GOTO_NUM_THREADS", "OMP_NUM_THREADS")   # OpenBLAS 기본 스레드 수를 정하는 바깥 변수(미지정 = 셋 다 없음)
UNSET = None


# ---------------------------------------------------------------- 독립 관찰 도구 (하위 프로세스에서도 import 해 쓴다)

def _wheel_lib_paths():
    """휠 배치: numpy·scipy 패키지 폴더 형제 `<패키지>.libs` 의 `*openblas*` 파일(import 하지 않고 find_spec 으로 위치만)."""
    out = []
    for pkg in ("numpy", "scipy"):
        spec = importlib.util.find_spec(pkg)
        if spec is None or spec.origin is None:
            continue
        out += sorted(glob.glob(os.path.join(os.path.dirname(spec.origin) + ".libs", "*openblas*")))
    return out


def _shared_lib_paths():
    """공유 배치(conda 등): numpy·scipy 가 환경 공용 libopenblas 하나를 같이 쓴다 -- 심볼릭 링크를 풀어 실제 파일 하나씩."""
    patterns = (os.path.join(sys.prefix, "lib", "libopenblas*.so*"), os.path.join(sys.prefix, "Library", "bin", "*openblas*.dll"))
    return sorted({os.path.realpath(p) for pattern in patterns for p in glob.glob(pattern)})


def blas_lib_paths():
    """독립 관찰용 OpenBLAS 파일 목록: 휠 배치면 `.libs` 의 파일(numpy·scipy 각각), 아니면 공유 배치의 환경 공용 파일."""
    return _wheel_lib_paths() or _shared_lib_paths()


WHEEL_LAYOUT = bool(_wheel_lib_paths())
MIN_LIBS = 2 if WHEEL_LAYOUT else 1      # 공허 방지 하한: 휠 배치 = numpy·scipy 각각, 공유 배치 = 둘이 같이 쓰는 하나


def package_module_path(pkg):
    """패키지 폴더 안의 확장 모듈 파일 하나(공유 배치에서 가짜 BlasModule 의 '패키지 소유 경로'로 쓴다 -- 소유는 폴더로 정해진다)."""
    spec = importlib.util.find_spec(pkg)
    root = os.path.dirname(spec.origin)
    for pattern in ("**/*.so", "**/*.pyd"):
        found = sorted(glob.glob(os.path.join(root, pattern), recursive=True))
        if found:
            return found[0]
    raise AssertionError("확장 모듈 없음: " + pkg)


def numpy_lib_path():
    """numpy 쪽 OpenBLAS 파일: 휠 배치 = `numpy.libs` 안, 공유 배치 = 공용 파일."""
    paths = blas_lib_paths()
    own = [p for p in paths if "numpy" in os.path.basename(os.path.dirname(p))]
    return (own or paths)[0]


def _sym(lib, names):
    for n in names:
        f = getattr(lib, n, None)
        if f is not None:
            return f
    raise AssertionError("기호 없음: %r" % (names,))


def ctypes_threads(path):
    """ctypes 로 그 라이브러리를 열어(이미 적재됐으면 같은 모듈) OpenBLAS 스레드 수 조회."""
    import ctypes
    f = _sym(ctypes.CDLL(path), GET_SYMS)
    f.restype = ctypes.c_int
    return int(f())


def ctypes_set_threads(path, n):
    import ctypes
    f = _sym(ctypes.CDLL(path), SET_SYMS)
    f.argtypes = [ctypes.c_int]
    f.restype = None
    f(int(n))


def ctypes_corename(path):
    import ctypes
    f = _sym(ctypes.CDLL(path), CORE_SYMS)
    f.restype = ctypes.c_char_p
    return f().decode("utf-8", "replace")


def children(obj):
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return [getattr(obj, f.name) for f in dataclasses.fields(obj)]
    if isinstance(obj, (tuple, list)):
        return list(obj)
    if isinstance(obj, dict):
        return list(obj.values())
    return []


def blas_entries(env):
    """BlasEnvironment 칸 중 BLAS 항목 tuple(원소 = family 로 시작하는 7-tuple) -- C1 '항목 = (family, 소유 패키지, 파일 이름, config, corename,
    parallel, 확인 스레드 수)'. 칸 이름은 계약에 없어 모양으로 찾는다."""
    for v in children(env):
        if isinstance(v, tuple) and v and all(isinstance(e, tuple) and len(e) == 7 and e[0] in FAMILIES for e in v):
            return tuple(v)
    return ()


def nodes(obj, depth=0):
    """값 안의 모든 노드(스칼라·tuple 포함) -- BlasEnvironment 가 Python·플랫폼·판 값을 담는지 본다."""
    yield obj
    if depth < 6:
        for c in children(obj):
            yield from nodes(c, depth + 1)


def sort_key(entry):
    return tuple("" if x is None else x for x in entry)


# ---------------------------------------------------------------- 하위 프로세스

PRELUDE = r"""
import json, os, sys
sys.path.insert(0, {skill!r})
sys.path.insert(0, {tests!r})
from core import test_blas_env as H


def emit(obj):
    print("@@" + json.dumps(obj, default=repr))
"""


def run_py(code, threads=UNSET, timeout=900, extra_env=None):
    """하위 프로세스 하나(순차). threads = 바깥 OPENBLAS_NUM_THREADS 값(UNSET = 스레드 변수 셋 다 없음). -> (proc, 마지막 @@ JSON 또는 None)."""
    env = {k: v for k, v in os.environ.items() if k not in THREAD_ENV}
    if threads is not UNSET:
        env["OPENBLAS_NUM_THREADS"] = threads
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    env.update(extra_env or {})
    src = PRELUDE.format(skill=str(SKILL), tests=str(TESTS)) + code
    proc = subprocess.run([sys.executable, "-P", "-c", src], cwd=str(SKILL), env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("@@")]
    return proc, (json.loads(lines[-1][2:]) if lines else None)


def _ok(proc, got):
    assert proc.returncode == 0 and got is not None, "하위 프로세스 실패 rc=%s\n%s" % (proc.returncode, proc.stderr[-4000:])
    return got


# ---------------------------------------------------------------- N-T1 ~ N-T3: import 시점 고정 (C1)

def test_blas_pin_import_sets_every_openblas_to_one_outer_8():
    """N-T1: 바깥 8 -> import gmid_engine 뒤 numpy·scipy 의 OpenBLAS 조회 = 1(각각), os.environ 값 "1". 공허 방지: 라이브러리 >= 2."""
    proc, got = run_py("import gmid_engine\n"
                       "emit({'env': os.environ.get('OPENBLAS_NUM_THREADS'), "
                       "'threads': {os.path.basename(p): H.ctypes_threads(p) for p in H.blas_lib_paths()}})\n", threads="8")
    got = _ok(proc, got)
    assert len(got["threads"]) >= MIN_LIBS, got                            # 공허 방지: 휠 배치 = numpy·scipy 둘 다, 공유 배치 = 공용 하나
    assert got["threads"] == {k: 1 for k in got["threads"]}, got           # oracle (독립): ctypes 직접 조회
    assert got["env"] == "1", got


def test_blas_pin_holds_when_numpy_imported_first():
    """N-T2: 바깥 미지정, numpy·scipy.linalg 를 먼저 import(전제: 이때 조회 > 1) -> import gmid_engine -> 조회 1."""
    proc, got = run_py("import numpy, scipy.linalg\n"
                       "pre = {os.path.basename(p): H.ctypes_threads(p) for p in H.blas_lib_paths()}\n"
                       "import gmid_engine\n"
                       "post = {os.path.basename(p): H.ctypes_threads(p) for p in H.blas_lib_paths()}\n"
                       "emit({'pre': pre, 'post': post})\n", threads=UNSET)
    got = _ok(proc, got)
    assert len(got["pre"]) >= MIN_LIBS and all(n > 1 for n in got["pre"].values()), got   # 전제: 고정 전에는 1 이 아니다(공허 방지)
    assert got["post"] == {k: 1 for k in got["pre"]}, got


def test_blas_pin_outer_setting_does_not_change_environment_value():
    """N-T3: 바깥 1·8·18·미지정 하위 프로세스 넷(순차) -- 모두 조회 1, fp_of(blas_environment()) 넷이 같다((비교) 같은 함수 네 출력)."""
    code = ("import scipy.linalg\n"
            "import gmid_engine\n"
            "from gmid_engine.core import blas_environment, fp_of\n"
            "emit({'fp': fp_of(blas_environment()), "
            "'threads': {os.path.basename(p): H.ctypes_threads(p) for p in H.blas_lib_paths()}})\n")
    fps = {}
    for outer in ("1", "8", "18", UNSET):
        proc, got = run_py(code, threads=outer)
        got = _ok(proc, got)
        assert len(got["threads"]) >= MIN_LIBS and set(got["threads"].values()) == {1}, (outer, got)
        fps[outer] = got["fp"]
    assert len(set(fps.values())) == 1, fps


def test_blas_pin_environment_fp_stable_after_more_scipy_imports():
    """회귀(Linux 열거): OpenBLAS 에 링크한 scipy 확장 모듈을 더 import 해도 BLAS 항목 수·env_fp 가 바뀌지 않는다. 바뀌면 같은 실행의 단계 A 와
    find_front 가 기록한 env_fp 가 달라져 비교기 전제 (다)가 판정 불능을 낸다((비교) 같은 함수 두 출력)."""
    code = ("import gmid_engine\n"
            "from gmid_engine.core import blas_environment, fp_of\n"
            "before = blas_environment()\n"
            "import scipy.optimize, scipy.sparse.linalg, scipy.interpolate, scipy.signal, scipy.fft\n"
            "after = blas_environment()\n"
            "emit({'n0': len(H.blas_entries(before)), 'n1': len(H.blas_entries(after)), 'same': fp_of(before) == fp_of(after)})\n")
    proc, got = run_py(code, threads="1")
    got = _ok(proc, got)
    assert got["n0"] == got["n1"] >= 1 and got["same"], got


# ---------------------------------------------------------------- N-T4: BlasEnvironment 구성 (C1)

def test_blas_pin_environment_value_shape():
    import scipy.linalg  # noqa: F401  scipy 의 OpenBLAS 를 싣는다(numpy·scipy 항목 2개 전제)
    import numpy
    import scipy
    from gmid_engine.core import blas_environment, fp_of
    from gmid_engine.core.blas_env import BlasEnvironment
    env = blas_environment()
    assert isinstance(env, BlasEnvironment)
    hash(env)                                                              # hashable
    first = dataclasses.fields(env)[0].name if dataclasses.is_dataclass(env) else None
    with pytest.raises(AttributeError):                                    # frozen: 칸 대입 예외(FrozenInstanceError 는 AttributeError 하위)
        if first is None:
            env.x = 1
        else:
            setattr(env, first, None)
    env2 = blas_environment()
    assert env2 == env and fp_of(env2) == fp_of(env)                       # (비교) 같은 프로세스 두 호출
    allnodes = list(nodes(env))
    strs = {x for x in allnodes if isinstance(x, str)}
    # (Py) Python 구현·판, sys.platform, platform.machine(), numpy·scipy 판이 값에 있다
    assert {s.lower() for s in strs} & {sys.implementation.name, platform.python_implementation().lower()}, strs
    assert (platform.python_version() in strs or sys.version in strs
            or any(isinstance(x, tuple) and tuple(x[:3]) == tuple(sys.version_info[:3]) for x in allnodes)), allnodes[:40]
    assert sys.platform in strs and platform.machine() in strs, strs
    assert numpy.__version__ in strs and scipy.__version__ in strs, strs
    ents = blas_entries(env)
    assert len(ents) == MIN_LIBS, env                                      # 휠 배치 = numpy·scipy 각 1개, 공유 배치 = 공용 1개(지금 환경 실측)
    assert {e[0] for e in ents} == {"openblas"}
    assert {e[1] for e in ents} == ({"numpy", "scipy"} if WHEEL_LAYOUT else {None})   # 공유 배치는 패키지 폴더 밖이라 소유 칸이 None
    names = {os.path.basename(p) for p in blas_lib_paths()}               # (독립) .libs glob 또는 환경 공용 파일
    for e in ents:
        assert isinstance(e[2], str) and "/" not in e[2] and "\\" not in e[2], e
        assert e[2] in names, (e[2], names)
        assert e[6] == 1, e                                                # 확인 스레드 수 = 1
        assert isinstance(e[3], str) and "OpenBLAS" in e[3], e             # config = 그 라이브러리 get_config 문자열
    by_file = {e[2]: e for e in ents}
    for p in blas_lib_paths():
        assert by_file[os.path.basename(p)][4] == ctypes_corename(p)      # (독립) corename = ctypes 직접 조회
    assert list(ents) == sorted(ents, key=sort_key)                        # 항목 순서 = 사전식 정렬(None -> "")


# ---------------------------------------------------------------- N-T5: 재확인 지점 (a)~(e) (C2)

TOY = r"""
import tempfile
from pathlib import Path
import gmid_engine
import scipy.linalg
from search.conftest import CODE_FP, build_case, circuit_c, theta_r4c, write_r4_lut
from gmid_engine.pipeline import run_stage_a
from gmid_engine.search import AXIS_AREA, build_search_context, find_front, layer0_start, open_run, solve_eps, start_points
tmp = Path(tempfile.mkdtemp(prefix="nt5", dir={work!r}))


def _point_a():
    donors, counters = open_run()   # [XRUN-F1 card B C6] 단계 A 호출 하나 = 새 실행 하나
    return run_stage_a(tp, sp, lut, output_dir=tmp / "a_out", donors=donors, counters=counters)


lut = write_r4_lut(tmp / "lut")
case = build_case(tmp, circuit_c(), lut, eval_budget=12)
st, _ = start_points(case.sctx, [theta_r4c()])
tp = sorted((tmp / "case").glob("*.topology.json"))[0]
sp = sorted((tmp / "case").glob("*.sizing_spec.json"))[0]
POINTS = {{
    "a": _point_a,
    "b": lambda: build_search_context(case.dc, case.spec, case.settings, None, case.pdk, case.rule, code_fp=CODE_FP),
    "c": lambda: find_front(case.sctx, [theta_r4c()]),
    "d": lambda: layer0_start(case.sctx),
    "e": lambda: solve_eps(case.sctx, st[0], AXIS_AREA, None, ("t",)),
}}
NP_LIB = H.numpy_lib_path()


def call(point):
    try:
        POINTS[point]()
    except RuntimeError as e:
        return "RuntimeError"
    return "ok"
"""


@pytest.mark.parametrize("point", ["a", "b", "c", "d", "e"])
def test_blas_pin_recheck_points_reject_changed_threads(point, tmp_path):
    """N-T5: 하위 프로세스에서 ctypes 로 numpy 쪽 OpenBLAS 설정 API 에 2(전제: 조회 2) -> 지점 진입 RuntimeError. 대조군: 같은 프로세스에서 1 로
    되돌리면 같은 호출이 거부 없이 끝난다(거부 원인이 스레드 수임을 보인다)."""
    code = TOY.format(work=str(tmp_path)) + (
        "H.ctypes_set_threads(NP_LIB, 2)\n"
        "pre = H.ctypes_threads(NP_LIB)\n"
        "at2 = call(%r)\n"
        "H.ctypes_set_threads(NP_LIB, 1)\n"
        "at1 = call(%r)\n"
        "emit({'pre': pre, 'at2': at2, 'at1': at1})\n" % (point, point))
    proc, got = run_py(code, threads="1")
    got = _ok(proc, got)
    assert got["pre"] == 2, got                                            # 전제: 설정이 실제로 들었다
    assert got["at2"] == "RuntimeError", got                               # C2: 재확인 지점 진입 거부
    assert got["at1"] == "ok", got                                         # 대조군


# ---------------------------------------------------------------- N-T6: 새 OpenBLAS 모듈 (C2 무상태)

def test_blas_pin_new_openblas_module_changes_environment_fp(tmp_path):
    """N-T6: 고정 뒤 numpy OpenBLAS DLL 을 임시 폴더에 다른 이름으로 복사해 ctypes.CDLL(전제: 별도 핸들, 조회 1) -> 재확인 지점(d) 통과,
    blas_environment() BLAS 항목 3개, fp_of 가 적재 전과 다르다((비교) 같은 함수 두 출력)."""
    code = TOY.format(work=str(tmp_path)) + r"""
import ctypes, shutil
from gmid_engine.core import blas_environment, fp_of
env0 = blas_environment()
fp0, n0 = fp_of(env0), len(H.blas_entries(env0))
dst = os.path.join(str(tmp), "libscipy_openblas64_nfr4copy" + os.path.splitext(NP_LIB)[1])
shutil.copyfile(NP_LIB, dst)
copy = ctypes.CDLL(dst)
orig = ctypes.CDLL(NP_LIB)
separate = copy._handle != orig._handle
copy_threads = H.ctypes_threads(dst)
d = call("d")
env1 = blas_environment()
emit({"n0": n0, "separate": separate, "copy_threads": copy_threads, "d": d, "n1": len(H.blas_entries(env1)),
      "fp_changed": fp_of(env1) != fp0, "owners1": sorted(str(e[1]) for e in H.blas_entries(env1))})
"""
    proc, got = run_py(code, threads="1")
    got = _ok(proc, got)
    assert got["n0"] == MIN_LIBS and got["separate"] and got["copy_threads"] == 1, got     # 전제
    assert got["d"] == "ok", got                                                    # 무상태: 조회 1 이면 재확인 통과
    assert got["n1"] == MIN_LIBS + 1 and got["fp_changed"], got
    expected = ["None", "numpy", "scipy"] if WHEEL_LAYOUT else ["None", "None"]     # 임시 폴더 = 패키지 밖 -> 소유 None(공유 배치는 공용 파일도 None)
    assert got["owners1"] == expected, got


# ---------------------------------------------------------------- N-T7 ~ N-T9: 교체 지점 loaded_blas_modules (C1, 손)

def _fake(module, path, family="openblas", get=1, sticky=None, no_set=False, no_get=False, info=True):
    """가짜 BlasModule(손): get = 초기 조회 값, sticky = 설정이 듣지 않고 늘 그 값, no_set/no_get = 기호 없음(None), info=False = config·corename·
    parallel 기호 없음(None)."""
    state = {"n": get}

    def set_threads(n):
        if sticky is None:
            state["n"] = n

    def get_threads():
        return state["n"] if sticky is None else sticky

    return module.BlasModule(path=path, family=family, set_threads=None if no_set else set_threads,
                             get_threads=None if no_get else get_threads,
                             config=(lambda: "OpenBLAS fake-%s" % family) if info else None,
                             corename=(lambda: "FakeCore") if info else None,
                             parallel=(lambda: 0) if info else None)


def _pkg_paths():
    """가짜 BlasModule 의 '패키지 소유 경로' 둘(numpy 쪽·scipy 쪽). 휠 배치 = 각 `.libs` 의 파일, 공유 배치 = 각 패키지 폴더 안의 확장 모듈 파일
    (소유는 파일 위치로만 정해지고 가짜 모듈은 파일을 열지 않는다)."""
    paths = blas_lib_paths()
    np_lib = [p for p in paths if os.path.basename(os.path.dirname(p)) == "numpy.libs"]
    sp_lib = [p for p in paths if os.path.basename(os.path.dirname(p)) == "scipy.libs"]
    if np_lib and sp_lib:
        return np_lib[0], sp_lib[0]
    assert not WHEEL_LAYOUT, paths
    return package_module_path("numpy"), package_module_path("scipy")


def _swap(monkeypatch, mods):
    import gmid_engine.core.blas_env as be
    monkeypatch.setattr(be, "loaded_blas_modules", lambda: tuple(mods))
    return be


def test_blas_pin_rejects_setting_that_does_not_take(monkeypatch):
    """N-T7: 설정이 듣지 않는 가짜(조회 2 고정) -> blas_environment()·pin_blas_threads() RuntimeError. 대조군: 같은 경로의 정상 가짜는 거부 없음."""
    import gmid_engine.core.blas_env as be
    np_lib, sp_lib = _pkg_paths()
    _swap(monkeypatch, [_fake(be, np_lib), _fake(be, sp_lib)])
    be.pin_blas_threads()                                                  # 대조군
    be.blas_environment()
    _swap(monkeypatch, [_fake(be, np_lib, sticky=2), _fake(be, sp_lib)])
    with pytest.raises(RuntimeError):
        be.blas_environment()
    with pytest.raises(RuntimeError):
        be.pin_blas_threads()


@pytest.mark.parametrize("missing", ["no_set", "no_get"])
def test_blas_pin_rejects_missing_thread_symbols(monkeypatch, missing):
    """N-T8 앞: openblas 기록의 set_threads 또는 get_threads 가 None(기호 없음) -> RuntimeError."""
    import gmid_engine.core.blas_env as be
    np_lib, sp_lib = _pkg_paths()
    _swap(monkeypatch, [_fake(be, np_lib, **{missing: True}), _fake(be, sp_lib)])
    with pytest.raises(RuntimeError):
        be.blas_environment()
    with pytest.raises(RuntimeError):
        be.pin_blas_threads()


def test_blas_pin_missing_info_symbols_are_none_not_rejected(monkeypatch):
    """N-T8 뒤: config·corename·parallel 기호 없는 가짜(조회 1) -> 거부 없음, 그 항목의 config·corename·parallel = None."""
    import gmid_engine.core.blas_env as be
    np_lib, sp_lib = _pkg_paths()
    _swap(monkeypatch, [_fake(be, np_lib, info=False), _fake(be, sp_lib)])
    be.pin_blas_threads()
    ents = {e[1]: e for e in blas_entries(be.blas_environment())}
    assert set(ents) == {"numpy", "scipy"}, ents
    assert ents["numpy"][3:6] == (None, None, None), ents["numpy"]
    assert ents["numpy"][6] == 1
    assert ents["scipy"][3:6] == ("OpenBLAS fake-openblas", "FakeCore", 0), ents["scipy"]     # 손: 가짜가 돌려준 값 그대로


@pytest.mark.parametrize("family", ["mkl", "blis"])
def test_blas_pin_rejects_mkl_and_blis_records(monkeypatch, tmp_path, family):
    """N-T9: family "mkl"·"blis" 기록이 하나라도 있으면 RuntimeError(OpenBLAS 둘은 정상 가짜)."""
    import gmid_engine.core.blas_env as be
    np_lib, sp_lib = _pkg_paths()
    other = str(tmp_path / ("lib%s_fake.dll" % family))
    _swap(monkeypatch, [_fake(be, np_lib), _fake(be, sp_lib), _fake(be, other, family=family)])
    with pytest.raises(RuntimeError):
        be.blas_environment()
    with pytest.raises(RuntimeError):
        be.pin_blas_threads()


@pytest.mark.parametrize("missing", ["numpy", "scipy"])
def test_blas_recheck_rejects_missing_owned_blas(monkeypatch, tmp_path, missing):
    """nfr4c2-r1 (사용자 N-6, 설계 40 §2.4.13 (1) '재확인' 행): 재확인 blas_environment() 도 고정 때와 같이 numpy·scipy 각각의 소유 BLAS 항목이
    적재 모듈에 없으면 RuntimeError. 가짜(손) = 남은 한 패키지의 정상 기록 + 패키지 폴더 밖(tmp) openblas 기록(조회 1, 소유 없음).
    대조군(손): 같은 바깥 기록에 numpy·scipy 둘 다 있으면 거부 없음 -- 거부 원인이 빠진 소유 항목임을 보인다."""
    import gmid_engine.core.blas_env as be
    np_lib, sp_lib = _pkg_paths()
    outside = str(tmp_path / "libopenblas_outside_fake.dll")               # 손: numpy·scipy 패키지 폴더(.libs 포함) 밖
    _swap(monkeypatch, [_fake(be, np_lib), _fake(be, sp_lib), _fake(be, outside)])
    be.blas_environment()                                                  # 대조군: 소유 항목 둘 다 있음 -> 거부 없음
    kept = sp_lib if missing == "numpy" else np_lib
    _swap(monkeypatch, [_fake(be, kept), _fake(be, outside)])
    with pytest.raises(RuntimeError) as ei:
        be.blas_environment()
    assert missing in str(ei.value), str(ei.value)                         # 손: 메시지에 빠진 패키지 이름(문구 전체는 단언하지 않는다)


# ---------------------------------------------------------------- N-T10: 빌드 설정·플랫폼 거부 (C1, 하위 프로세스)

IMPORT_GUARDED = r"""
try:
    import gmid_engine
    import gmid_engine.core
    emit({"result": "ok"})
except RuntimeError as e:
    emit({"result": "RuntimeError", "msg": str(e)[:300]})
"""


def test_blas_pin_rejects_non_openblas_build_config():
    """N-T10 앞: numpy.show_config 를 BLAS 이름이 openblas 아닌 dict 로 바꾼 뒤 import gmid_engine -> RuntimeError(손: 바꾼 이름 'mkl-sdl')."""
    code = r"""
import copy, numpy, scipy.linalg
_orig = numpy.show_config


def _fake_show(mode="stdout"):
    d = copy.deepcopy(_orig(mode="dicts"))
    d["Build Dependencies"]["blas"]["name"] = "mkl-sdl"
    return d


_real = _orig(mode="dicts")["Build Dependencies"]["blas"]["name"].lower()
assert "openblas" in _real or _real == "blas"   # 전제: 진짜 설정은 openblas(휠) 또는 범용 blas(conda-forge 등 공유 libblas)
numpy.show_config = _fake_show
""" + IMPORT_GUARDED
    proc, got = run_py(code, threads="1")
    got = _ok(proc, got)
    assert got["result"] == "RuntimeError", got


def test_blas_pin_rejects_unsupported_platform():
    """N-T10 뒤: sys.platform 을 지원 밖 값('sunos5', 손)으로 대입한 뒤 import gmid_engine -> RuntimeError."""
    code = r"""
import ctypes, ctypes.util, numpy, scipy.linalg
sys.platform = "sunos5"
""" + IMPORT_GUARDED
    proc, got = run_py(code, threads="1")
    got = _ok(proc, got)
    assert got["result"] == "RuntimeError", got


# ---------------------------------------------------------------- N-T11 ~ N-T12: 모듈 구조 (C1)

def _module_level_imports(tree):
    """모듈 최상위(함수·클래스 밖 -- if/try/with/for/while 블록 안 포함)의 import 대상 이름 목록."""
    out = []

    def visit(stmts):
        for s in stmts:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(s, ast.Import):
                out.extend(a.name for a in s.names)
            elif isinstance(s, ast.ImportFrom) and s.level == 0 and s.module:
                out.append(s.module)
            for field in ("body", "orelse", "finalbody"):
                visit(getattr(s, field, []) or [])
            for h in getattr(s, "handlers", []) or []:
                visit(h.body)
            for c in getattr(s, "cases", []) or []:
                visit(c.body)
    visit(tree.body)
    return out


def _heavy(names):
    return [n for n in names if n.split(".")[0] in ("numpy", "scipy")]


def test_blas_pin_core_has_no_module_level_numpy_scipy_import():
    """N-T11 (독립, AST): `gmid_engine/core/*.py` 모듈 최상위에 numpy·scipy import 0. 검사기 자체 확인: 심은 예시는 잡는다."""
    planted = ast.parse("try:\n    import numpy as np\nexcept ImportError:\n    pass\nif True:\n    from scipy import linalg\n"
                        "def f():\n    import numpy\nclass C:\n    import scipy\n")
    assert _heavy(_module_level_imports(planted)) == ["numpy", "scipy"]   # 함수·클래스 안 것은 세지 않는다
    files = sorted((ENGINE / "core").glob("*.py"))
    assert files
    bad = {f.name: _heavy(_module_level_imports(ast.parse(f.read_text(encoding="utf-8")))) for f in files}
    assert {k: v for k, v in bad.items() if v} == {}


def test_blas_pin_core_public_names():
    """N-T12 (식): gmid_engine.core.__all__ 에 pin_blas_threads·blas_environment 가 있고 loaded_blas_modules·BlasModule·BlasEnvironment 는 없다."""
    import gmid_engine.core as core
    names = set(core.__all__)
    assert {"pin_blas_threads", "blas_environment"} <= names
    assert not names & {"loaded_blas_modules", "BlasModule", "BlasEnvironment"}
