"""파생 표 디스크 캐시 -- 비싼 첫 계산 표(tol_V·tol_VDsat·곡선 보고)를 프로세스 사이에 파일로 재사용한다 (lut/CONTRACT.md 2.1, 2026-10-08
사용자 승인 "tol_V표를 파일로 캐시해").

진입점: `TableCache`.

* 키(`key_digest`) = sha256(코드 버전 ‖ 입력 지문 ‖ 설정 지문). 입력 지문 = 계산이 읽는 LUT 자료(슬라이스·열 출처의 배열·격자·sha256
  전부)의 내용 해시, 설정 지문 = (LUT 묶음 지문, 함수 이름, 호출 인자, 호출부가 준 설정 상수), 코드 버전 = lut·core 패키지 소스 전부의
  바이트 해시 + numpy·python 버전(코드가 바뀌면 키가 바뀐다). 구성요소 하나라도 다르면 적중하지 않고 다시 계산해 덮어쓴다.
* 파일 위치 = 설정 파일(`assets/lut_v2_location.json` 의 `table_cache` = {"env", "default"})의 폴더. 환경 변수가 비어 있지 않으면 그 값.
  폴더가 없으면 만든다(못 만들면 캐시 끔 -- 계산은 그대로 된다). 데이터 폴더(lut_data)·저장소 밖의 전용 폴더다.
* 칸(slot) 파일 이름 = 함수 이름 + (LUT 묶음 지문, 함수 이름, 호출 인자)의 지문 -- 같은 칸은 새 키로 덮어써서 코드·설정이 바뀌어도 폴더가
  불지 않는다.
* 파일 형식: 머리(MAGIC, 키, 본문 sha256) + 본문(pickle). 읽을 때 머리·키·본문 해시를 모두 확인한다. 깨졌거나(머리·길이·해시·역직렬화
  실패) 키가 다르면 쓰지 않고 다시 계산한 뒤 덮어쓴다(깨짐은 RuntimeWarning + `events` 기록; 예외를 내지 않는다). 본문 해시는 깨짐
  검출용이다 -- 폴더에 쓸 수 있는 사람은 신뢰한다(pickle).
* 쓰기: 같은 폴더의 임시 파일에 쓰고 fsync 한 뒤 `os.replace`(원자적). 여러 프로세스가 동시에 시작해도 읽는 쪽은 옛 완성 파일 또는
  새 완성 파일만 본다(둘 다 계산해도 좋다). 쓰기 실패(교체 중 잠김 포함)는 기록만 하고 계산 결과를 그대로 돌려준다.
* 배열을 품은 결과는 저장하지 않는다(읽기 전용 플래그가 pickle 로 보존되지 않음) -- 이벤트 "unstorable".
"""
import dataclasses
import hashlib
import json
import os
import pickle
import sys
import tempfile
import warnings
from collections.abc import Mapping

import numpy as np

from gmid_engine.core import fp_of

_MAGIC = b"GMIDTBL1"
_NL = b"\n"
_HEX = len(hashlib.sha256().hexdigest())
_HEADER = len(_MAGIC) + len(_NL) + _HEX + len(_NL) + _HEX + len(_NL)
_CONFIG_NAME = "lut_v2_location.json"
_CONFIG_ENTRY = "table_cache"
_LOAD_ERRORS = (pickle.UnpicklingError, EOFError, AttributeError, ImportError, IndexError, ValueError, TypeError)


def _feed(h, obj):
    """`obj`(배열·tuple/list·Mapping·dataclass·스칼라)를 구조 태그와 함께 해시에 넣는다(같은 내용 = 같은 바이트)."""
    if isinstance(obj, np.ndarray):
        h.update(b"A" + obj.dtype.str.encode("ascii") + repr(obj.shape).encode("ascii") + _NL)
        h.update(np.ascontiguousarray(obj).tobytes())
    elif isinstance(obj, (tuple, list)):
        h.update(b"T" + str(len(obj)).encode("ascii") + _NL)
        for item in obj:
            _feed(h, item)
    elif isinstance(obj, Mapping):
        h.update(b"M" + str(len(obj)).encode("ascii") + _NL)
        for k in sorted(obj, key=repr):
            _feed(h, k)
            _feed(h, obj[k])
    elif dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        h.update(b"D" + type(obj).__qualname__.encode("utf-8") + _NL)
        for f in dataclasses.fields(obj):
            h.update(f.name.encode("utf-8") + _NL)
            _feed(h, getattr(obj, f.name))
    elif isinstance(obj, np.generic):
        h.update(b"G" + obj.dtype.str.encode("ascii") + obj.tobytes())
    else:
        h.update(b"S" + fp_of(obj).encode("ascii"))


def _inputs_digest(inputs):
    h = hashlib.sha256()
    _feed(h, inputs)
    return h.hexdigest()


def _has_array(obj):
    if isinstance(obj, np.ndarray):
        return True
    if isinstance(obj, (tuple, list)):
        return any(_has_array(item) for item in obj)
    if isinstance(obj, Mapping):
        return any(_has_array(k) or _has_array(v) for k, v in obj.items())
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return any(_has_array(getattr(obj, f.name)) for f in dataclasses.fields(obj))
    return False


def _code_version():
    """lut·core 패키지 .py 소스 전부(상대 경로 + 바이트) + numpy·python 버전의 sha256 hex."""
    lut_dir = os.path.dirname(os.path.abspath(__file__))
    h = hashlib.sha256()
    h.update(("numpy " + np.__version__ + "\npython " + sys.version).encode("utf-8") + _NL)
    for pkg in (lut_dir, os.path.join(os.path.dirname(lut_dir), "core")):
        for root, dirs, files in os.walk(pkg):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for name in sorted(files):
                if name.endswith(".py"):
                    path = os.path.join(root, name)
                    h.update(os.path.relpath(path, os.path.dirname(lut_dir)).replace("\\", "/").encode("utf-8") + _NL)
                    with open(path, "rb") as fh:
                        h.update(fh.read())
    return h.hexdigest()


def _config_dir(config_path, env):
    """설정 파일의 `table_cache` 항목 -> 폴더(환경 변수 우선). 설정·항목이 없으면 None."""
    if not os.path.isfile(config_path):
        return None
    with open(config_path, encoding="utf-8") as fh:
        entry = json.load(fh).get(_CONFIG_ENTRY)
    if not isinstance(entry, dict):
        return None
    value = env.get(entry.get("env")) if entry.get("env") else None
    value = value or entry.get("default")
    return os.path.abspath(value) if value else None


class TableCache:
    """디스크 캐시 하나. `TableCache(directory)`: directory 가 None 이면 꺼짐(`fetch` 는 계산만 한다). 폴더는 없으면 만든다.

    * `TableCache.from_config(config_path, env)`: 설정 파일 + 환경 매핑으로 폴더를 정한다(모듈이 `os.environ` 를 직접 읽지 않는다).
    * `TableCache.default()`: 저장소 설정(`assets/lut_v2_location.json`) + `os.environ` -- `LutMemo` 의 기본값.
    * `fetch(lut_fp, fn_name, key, inputs, settings, compute)`: 적중이면 저장 값, 아니면 `compute()` 를 부르고 저장.
    * `stats()`: ((이벤트, 횟수), ...) 이름 정렬. 이벤트 = hit·miss·stale_key·corrupt·read_error·write·write_error·unstorable·disabled.
    * `events`: ((이벤트, 함수 이름), ...) 발생 순서.
    """

    def __init__(self, directory):
        self.events = ()
        self._code = None
        self.directory = None
        if directory is None:
            return
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as exc:
            warnings.warn("TableCache: 폴더를 만들 수 없어 캐시를 끈다: %s (%s)" % (directory, exc), RuntimeWarning)
            self._note("disabled", "")
            return
        self.directory = directory

    @classmethod
    def from_config(cls, config_path, env):
        return cls(_config_dir(config_path, env))

    @classmethod
    def default(cls):
        skill_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return cls.from_config(os.path.join(skill_dir, "assets", _CONFIG_NAME), os.environ)

    def _note(self, event, fn_name):
        self.events = self.events + ((event, fn_name),)

    def stats(self):
        counts = {}
        for event, _ in self.events:
            counts[event] = counts.get(event, 0) + 1
        return tuple(sorted(counts.items()))

    def key_digest(self, lut_fp, fn_name, key, inputs, settings):
        """키 sha256 hex -- 코드 버전·입력 지문·설정 지문(LUT 묶음 지문·함수 이름·호출 인자·설정 상수)."""
        if self._code is None:
            self._code = _code_version()
        parts = (self._code, _inputs_digest(inputs), fp_of((lut_fp, fn_name, tuple(key), settings)))
        return hashlib.sha256("\n".join(parts).encode("ascii")).hexdigest()

    def path_of(self, lut_fp, fn_name, key):
        """칸 파일 경로(폴더 없음 -> None)."""
        if self.directory is None:
            return None
        return os.path.join(self.directory, "%s-%s.tbl" % (fn_name, fp_of((lut_fp, fn_name, tuple(key)))))

    def _read(self, path, digest, fn_name):
        """(True, 값) 또는 None -- 없음·깨짐·키 다름은 None(이벤트 기록)."""
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except FileNotFoundError:
            self._note("miss", fn_name)
            return None
        except OSError as exc:
            warnings.warn("TableCache: 읽을 수 없다 %s (%s)" % (path, exc), RuntimeWarning)
            self._note("read_error", fn_name)
            return None
        magic_end = len(_MAGIC) + len(_NL)
        key_end = magic_end + _HEX
        sha_start = key_end + len(_NL)
        sha_end = sha_start + _HEX
        body = data[_HEADER:]
        intact = (len(data) >= _HEADER and data[:magic_end] == _MAGIC + _NL and data[key_end:sha_start] == _NL
                  and data[sha_end:_HEADER] == _NL
                  and hashlib.sha256(body).hexdigest().encode("ascii") == data[sha_start:sha_end])
        if not intact:
            warnings.warn("TableCache: 깨진 캐시 파일을 버리고 다시 계산한다: %s" % path, RuntimeWarning)
            self._note("corrupt", fn_name)
            return None
        if data[magic_end:key_end] != digest.encode("ascii"):
            self._note("stale_key", fn_name)
            return None
        try:
            value = pickle.loads(body)
        except _LOAD_ERRORS as exc:
            warnings.warn("TableCache: 역직렬화 실패, 다시 계산한다: %s (%s)" % (path, exc), RuntimeWarning)
            self._note("corrupt", fn_name)
            return None
        self._note("hit", fn_name)
        return (True, value)

    def _write(self, path, digest, value, fn_name):
        if _has_array(value):
            self._note("unstorable", fn_name)
            return
        body = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        blob = (_MAGIC + _NL + digest.encode("ascii") + _NL + hashlib.sha256(body).hexdigest().encode("ascii") + _NL + body)
        tmp = None
        try:
            fd, tmp = tempfile.mkstemp(dir=self.directory, prefix=os.path.basename(path) + ".", suffix=".tmp")
            with os.fdopen(fd, "wb") as fh:
                fh.write(blob)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
            tmp = None
            self._note("write", fn_name)
        except OSError as exc:
            warnings.warn("TableCache: 쓰지 못했다 %s (%s)" % (path, exc), RuntimeWarning)
            self._note("write_error", fn_name)
        finally:
            if tmp is not None:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def fetch(self, lut_fp, fn_name, key, inputs, settings, compute):
        """칸 (lut_fp, fn_name, key) 의 값. 키가 맞는 완성 파일이 있으면 그 값, 아니면 `compute()` 결과를 저장하고 돌려준다."""
        path = self.path_of(lut_fp, fn_name, key)
        if path is None:
            return compute()
        digest = self.key_digest(lut_fp, fn_name, key, inputs, settings)
        found = self._read(path, digest, fn_name)
        if found is not None:
            return found[1]
        value = compute()
        self._write(path, digest, value, fn_name)
        return value
