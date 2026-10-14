"""엔진 코드 지문 -- `gmid_engine` 아래 test 가 아닌 모든 패키지의 `.py` 바이트 sha256 (설계 40 §2.4.3 키 (iii)).

진입점: `engine_code_fp(engine_root=None) -> str | None`.

* 대상 = `engine_root`(기본 = 이 파일이 든 `gmid_engine` 폴더) 아래 모든 `.py` 파일. 맨 위 `tests/` 와 숨김 폴더(`.` 으로 시작)·
  `__pycache__` 는 내려가지 않는다. 파일마다 (engine_root 기준 posix 상대 경로, 파일 바이트 sha256)을 상대 경로 문자열로 정렬한
  tuple 의 `fp_of`.
* 블록 입력 버전의 코드 해시는 블록 함수 자신의 코드 객체(중첩 code·`__wrapped__` 사슬 포함, 경로·줄 정보 제외)만 덮으므로(`compute_block`), 실행 사이 재사용(S0 수준 스냅샷 영속화)·
  S3 기록의 코드 지문은 이 값을 쓴다. 옛 `search_context._code_fp`(6개 패키지만)를 대체한다.
* `engine_root` 가 폴더가 아니거나 대상 파일이 하나도 없으면 None(그 checkout 에 엔진이 없다 -- 스냅샷 정리가 쓴다).
"""
import hashlib
import os

from .fingerprint import fp_of

_TESTS_DIR = "tests"
_CACHE_DIR = "__pycache__"
_HIDDEN_PREFIX = "."
_SOURCE_SUFFIX = ".py"


def engine_code_fp(engine_root=None):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if engine_root is None else os.path.abspath(engine_root)
    if not os.path.isdir(root):
        return None
    digests = []
    for folder, dirs, files in os.walk(root):
        top = folder == root
        dirs[:] = [d for d in dirs if d != _CACHE_DIR and not d.startswith(_HIDDEN_PREFIX) and not (top and d == _TESTS_DIR)]
        for name in files:
            if name.endswith(_SOURCE_SUFFIX):
                path = os.path.join(folder, name)
                with open(path, "rb") as fh:
                    digests.append((os.path.relpath(path, root).replace(os.sep, "/"), hashlib.sha256(fh.read()).hexdigest()))
    return fp_of(tuple(sorted(digests))) if digests else None
