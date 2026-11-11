"""BLAS 스레드 1 고정과 확인, 실행 환경 값 (설계 40 §2.4.13 (1), EP-9, 계획 NFR-4).

진입점: `pin_blas_threads() -> BlasEnvironment`(`gmid_engine/__init__.py` 가 import 때 1회 부른다).

같은 파일의 앞 정의가 이름으로 서로를 부른다(규칙 A -- 진입점은 `pin_blas_threads` 하나):
* `BlasModule` -- 프로세스에 적재된 BLAS 모듈 하나의 기록(frozen): `path`·`family`("openblas"|"mkl"|"blis")·`set_threads`·`get_threads`·
  `config`·`corename`·`parallel`(호출 가능 객체, 그 모듈이 기호를 내보내지 않으면 None).
* `BlasEnvironment` -- 확인 결과 값(frozen·hashable): Python 구현·판, `sys.platform`, `platform.machine()`, numpy·scipy 판, BLAS 항목 tuple
  (family, 소유 패키지, 파일 이름, config, corename, parallel, 확인한 스레드 수) -- 항목 순서는 사전식 정렬(None 은 빈 문자열)이라 열거 순서와 무관하다.
* `loaded_blas_modules() -> tuple[BlasModule, ...]` -- 적재 모듈 열거와 알려진 스레드 API 기호 찾기(Windows `EnumProcessModules`, Linux
  `/proc/self/maps`, 그 밖 플랫폼 `RuntimeError`). **test 교체 지점**: 이름·인자 없는 서명·`BlasModule` tuple 반환·`blas_environment`·
  `pin_blas_threads` 가 모듈 전역 이름으로 부르는 방식은 바꾸지 않는다.
* `blas_environment() -> BlasEnvironment` -- 설정하지 않고 열거·조회만 해 확인하고 값을 돌려준다. 재확인 지점((a)~(e))이 부르며 **무상태**다
  (모듈 집합을 보관하지 않는다 -- 지금 적재된 모듈 전부가 조건을 만족하는지와 numpy·scipy 각각의 소유 BLAS 항목이 있는지만 본다).
* `pin_blas_threads()` -- 환경 변수 `OPENBLAS_NUM_THREADS` = "1" -> numpy·`scipy.linalg` 적재 -> 적재된 OpenBLAS 모듈마다 설정 API 로 1 -> `blas_environment()` 로 확인.

거부(`RuntimeError`, 조용한 대체 없음): numpy·scipy 빌드 설정(`show_config(mode="dicts")`)의 BLAS 이름에 `openblas`(대소문자 무시)가 없고 범용 이름 `blas`(conda-forge 등 공유 libblas)도 아님, 그 패키지의
BLAS 라이브러리를 못 찾음(고정·재확인 (a)~(e) 모두), OpenBLAS 기록의 설정·조회 기호 없음, 조회 값 != 1, MKL·BLIS 기호 모듈이 있음, 열거 미구현 플랫폼.
Linux 는 기호를 그 라이브러리가 **직접 정의한** 경우만 BLAS 모듈로 센다(dladdr -- 의존 라이브러리 기호까지 찾는 dlsym 때문에 OpenBLAS 에 링크한 scipy 확장 모듈이 모두 모듈로 세어져
모듈을 더 import 할 때마다 항목·`env_fp` 가 바뀌는 것을 막는다; Windows 는 원래 자기 기호만 찾는다). 패키지 폴더 밖의 공유 OpenBLAS(conda-forge 등)는 소유 패키지 칸이 None 이고,
그 패키지의 확장 모듈이 조회 기호를 그 라이브러리에서 가져올 때만 그 패키지의 BLAS 로 인정한다(`_links_to_provider`).
`config`·`corename`·`parallel` 기호가 없는 것은 거부 사유가 아니다(해당 항목 값이 None). 알려진 스레드 API 기호를 내보내지 않는 BLAS 는 찾을 수 없다(범위 밖).
numpy·scipy 는 함수 안에서 import 한다(core 는 모듈 수준에서 numpy·scipy 를 import 하지 않는다).
"""
import ctypes
import dataclasses
import os
import platform
import sys

_THREADS_ENV = "OPENBLAS_NUM_THREADS"
_OPENBLAS = "openblas"
_GENERIC_BLAS_NAMES = ("blas",)      # conda-forge 등 범용 libblas 로 빌드된 numpy·scipy 의 빌드 설정 BLAS 이름 -- 실제 공급자는 적재 모듈 검사(OpenBLAS 기호·스레드 1·MKL/BLIS 없음)가 가른다
_MKL = "mkl"
_BLIS = "blis"
_BUILD_PACKAGES = ("numpy", "scipy")
_NAME_PREFIXES = ("", "scipy_")
_NAME_SUFFIXES = ("", "64_")
_MKL_SET_NAMES = ("MKL_Set_Num_Threads", "mkl_set_num_threads")
_BLIS_SET_NAMES = ("bli_thread_set_num_threads",)
_PLATFORM_WINDOWS = "win32"
_PLATFORM_LINUX = "linux"


@dataclasses.dataclass(frozen=True)
class BlasModule:
    path: str
    family: str
    set_threads: object
    get_threads: object
    config: object
    corename: object
    parallel: object


@dataclasses.dataclass(frozen=True)
class BlasEnvironment:
    python_implementation: str
    python_version: str
    platform: str
    machine: str
    numpy_version: str
    scipy_version: str
    blas: tuple


def _require_platform():
    if sys.platform != _PLATFORM_WINDOWS and not sys.platform.startswith(_PLATFORM_LINUX):
        raise RuntimeError("BLAS 스레드 고정: 모듈 열거가 구현되지 않은 플랫폼이다: " + sys.platform)


def _windows_libraries():
    from ctypes import wintypes

    psapi = ctypes.WinDLL("psapi")
    kernel = ctypes.WinDLL("kernel32")
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.EnumProcessModules.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD,
                                         ctypes.POINTER(wintypes.DWORD)]
    kernel.GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    process = kernel.GetCurrentProcess()
    needed = wintypes.DWORD(0)
    count = 1
    while True:
        handles = (wintypes.HMODULE * count)()
        if not psapi.EnumProcessModules(process, handles, ctypes.sizeof(handles), ctypes.byref(needed)):
            raise RuntimeError("BLAS 스레드 고정: 적재 모듈 열거(EnumProcessModules)가 실패했다")
        if needed.value <= ctypes.sizeof(handles):
            break
        count = needed.value // ctypes.sizeof(wintypes.HMODULE) + 1      # 열거 사이에 모듈이 더 실렸을 수 있어 한 칸 여유
    for handle in handles[:needed.value // ctypes.sizeof(wintypes.HMODULE)]:
        size = wintypes.MAX_PATH
        while True:
            buffer = ctypes.create_unicode_buffer(size)
            length = kernel.GetModuleFileNameW(handle, buffer, size)
            if length < size:
                break
            size *= 2
        if length:
            yield buffer.value, ctypes.CDLL(buffer.value, handle=handle)


def _linux_libraries():
    seen = set()
    with open("/proc/self/maps", encoding="utf-8") as maps:
        for line in maps:
            path = " ".join(line.split()[5:])
            if path.startswith("/") and ".so" in os.path.basename(path) and path not in seen:
                seen.add(path)
                try:
                    yield path, ctypes.CDLL(path)
                except OSError:
                    continue


def _libraries():
    _require_platform()
    if sys.platform == _PLATFORM_WINDOWS:
        return _windows_libraries()
    return _linux_libraries()


class _DlInfo(ctypes.Structure):
    _fields_ = (("dli_fname", ctypes.c_char_p), ("dli_fbase", ctypes.c_void_p), ("dli_sname", ctypes.c_char_p),
                ("dli_saddr", ctypes.c_void_p))


def _dladdr():
    try:
        function = ctypes.CDLL(None).dladdr
    except (AttributeError, OSError):
        function = ctypes.CDLL("libdl.so.2").dladdr
    function.argtypes = [ctypes.c_void_p, ctypes.POINTER(_DlInfo)]
    function.restype = ctypes.c_int
    return function


def _defining_path(function):
    """Linux: 기호 `function` 을 **정의한** 공유 객체의 실제 경로(dladdr), 못 구하면 None."""
    address = ctypes.cast(function, ctypes.c_void_p).value
    info = _DlInfo()
    if not address or not _dladdr()(address, ctypes.byref(info)) or not info.dli_fname:
        return None
    return os.path.realpath(os.fsdecode(info.dli_fname))


def _symbol(library, names, path=None):
    """`library` 의 첫 기호. Linux 에서 `path` 를 주면 그 라이브러리가 기호를 직접 정의한 경우만 인정한다 -- Linux 의 dlsym 은 의존 라이브러리의
    기호도 찾으므로(OpenBLAS 에 링크한 scipy 확장 모듈마다 BLAS 모듈로 세어져 모듈을 더 import 할 때마다 항목·`env_fp` 가 바뀐다), Windows
    `GetProcAddress`(자기 기호만)와 같게 맞춘다."""
    for name in names:
        try:
            function = getattr(library, name)
        except AttributeError:
            continue
        if path is not None and sys.platform.startswith(_PLATFORM_LINUX) and _defining_path(function) != os.path.realpath(path):
            continue
        return function
    return None


def _typed(function, restype, argtypes):
    if function is not None:
        function.restype = restype
        function.argtypes = argtypes
    return function


def _as_text(function):
    if function is None:
        return None

    def call():
        value = function()
        return value.decode("utf-8") if isinstance(value, bytes) else value

    return call


def _openblas_names(base):
    return tuple(prefix + "openblas_" + base + suffix for prefix in _NAME_PREFIXES for suffix in _NAME_SUFFIXES)


def _module_record(path, library):
    set_threads = _symbol(library, _openblas_names("set_num_threads"), path)
    get_threads = _symbol(library, _openblas_names("get_num_threads"), path)
    if set_threads is not None or get_threads is not None:
        return BlasModule(
            path, _OPENBLAS, _typed(set_threads, None, (ctypes.c_int,)), _typed(get_threads, ctypes.c_int, ()),
            _as_text(_typed(_symbol(library, _openblas_names("get_config"), path), ctypes.c_char_p, ())),
            _as_text(_typed(_symbol(library, _openblas_names("get_corename"), path), ctypes.c_char_p, ())),
            _typed(_symbol(library, _openblas_names("get_parallel"), path), ctypes.c_int, ()))
    for family, names in ((_MKL, _MKL_SET_NAMES), (_BLIS, _BLIS_SET_NAMES)):
        found = _symbol(library, names, path)
        if found is not None:
            return BlasModule(path, family, found, None, None, None, None)
    return None


def loaded_blas_modules():
    records = (_module_record(path, library) for path, library in _libraries())
    return tuple(record for record in records if record is not None)


def _packages():
    import numpy
    import scipy
    import scipy.linalg        # scipy 쪽 OpenBLAS 를 싣는다

    return numpy, scipy


def _require_openblas_build(packages):
    for package in packages:
        try:
            blas_name = package.show_config(mode="dicts")["Build Dependencies"]["blas"]["name"]
        except (KeyError, TypeError) as exc:
            raise RuntimeError("BLAS 스레드 고정: " + package.__name__ + " 빌드 설정에서 BLAS 이름을 읽지 못했다: " + repr(exc)) from exc
        name = str(blas_name).casefold()
        if _OPENBLAS not in name and name not in _GENERIC_BLAS_NAMES:
            raise RuntimeError("BLAS 스레드 고정: " + package.__name__ + " 의 빌드 BLAS 가 OpenBLAS 계열이 아니다: " + str(blas_name)
                               + " (이 BLAS 의 고정·확인 방법은 design 40 §2.4.13 (1) 에 없다)")


def _package_folders():
    folders = []
    for name, module in tuple(sys.modules.items()):
        if "." in name:
            continue
        file = getattr(module, "__file__", None)
        if isinstance(file, str) and os.path.basename(file).startswith("__init__."):
            folders.append((name, os.path.normcase(os.path.dirname(os.path.abspath(file)))))
    return tuple(sorted(folders))


def _owner(path, folders):
    target = os.path.normcase(os.path.abspath(path))
    for name, folder in folders:
        for root in (folder, folder + ".libs"):
            if target.startswith(root + os.sep):
                return name
    return None


def _text(function):
    if function is None:
        return None
    value = function()
    return value.decode("utf-8") if isinstance(value, bytes) else value


def _entry(module, folders):
    if module.family != _OPENBLAS:
        raise RuntimeError("BLAS 스레드 고정: 지원 밖 BLAS 모듈이 적재돼 있다(" + module.family + "): " + module.path
                           + " (고정 방법은 design 40 §2.4.13 (1) 에 OpenBLAS 만 있다)")
    if module.set_threads is None or module.get_threads is None:
        raise RuntimeError("BLAS 스레드 고정: OpenBLAS 모듈에 스레드 설정·조회 기호가 없다: " + module.path)
    threads = module.get_threads()
    if threads != 1:
        raise RuntimeError("BLAS 스레드 고정: OpenBLAS 스레드 수가 1 이 아니다(" + str(threads) + "): " + module.path)
    parallel = None if module.parallel is None else module.parallel()
    return (module.family, _owner(module.path, folders), os.path.basename(module.path), _text(module.config), _text(module.corename),
            parallel, threads)


def _sort_key(entry):
    return tuple("" if value is None else value for value in entry)


def _links_to_provider(name, folders, providers):
    """Linux: 패키지 `name` 의 확장 모듈이 OpenBLAS 스레드 조회 기호를 `providers`(적재 BLAS 모듈의 실제 경로) 중 하나에서 가져오는가.
    공유 libblas 로 빌드된 패키지(conda-forge 등)는 자기 폴더에 BLAS 파일이 없어 소유 패키지 칸이 None 이므로, 실제 연결을 증거로 삼는다."""
    if not sys.platform.startswith(_PLATFORM_LINUX):
        return False
    roots = [folder + os.sep for owner, folder in folders if owner == name]
    for path, library in _linux_libraries():
        if any(os.path.normcase(os.path.abspath(path)).startswith(root) for root in roots):
            function = _symbol(library, _openblas_names("get_num_threads"))
            if function is not None and _defining_path(function) in providers:
                return True
    return False


def blas_environment():
    numpy, scipy = packages = _packages()
    _require_openblas_build(packages)
    folders = _package_folders()
    modules = loaded_blas_modules()
    entries = sorted((_entry(module, folders) for module in modules), key=_sort_key)
    owners = {entry[1] for entry in entries}
    providers = {os.path.realpath(module.path) for module in modules}
    for name in _BUILD_PACKAGES:
        if name not in owners and not _links_to_provider(name, folders, providers):
            raise RuntimeError("BLAS 스레드 고정: " + name + " 의 BLAS 라이브러리를 적재 모듈에서 찾지 못했다")
    return BlasEnvironment(platform.python_implementation(), platform.python_version(), sys.platform, platform.machine(),
                           numpy.__version__, scipy.__version__, tuple(entries))


def pin_blas_threads():
    _require_platform()
    os.environ[_THREADS_ENV] = "1"
    _packages()
    for module in loaded_blas_modules():
        if module.family == _OPENBLAS and module.set_threads is not None:
            module.set_threads(1)
    return blas_environment()
