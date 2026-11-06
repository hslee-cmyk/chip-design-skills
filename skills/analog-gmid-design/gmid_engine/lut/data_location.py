"""LUT 데이터 위치 -- 설정 파일(경로 + sha256)과 환경 변수로 LUT 파일 경로를 정한다 (lut/CONTRACT.md 1.8, r6).

진입점: `resolve_lut_location`.

* 엔진 코드에는 폴더 경로가 없다: 기본 위치·환경 변수 이름·파일 sha256 은 **설정 파일**(예: `assets/lut_v2_location.json`)에
  있고, 환경은 부르는 쪽이 매핑으로 넘긴다(`os.environ` 를 이 모듈이 직접 읽지 않는다 -- 같은 입력이면 같은 결과).
* 설정 형식: `{"root": {"env": <이름>, "default": <폴더>}, "pdk_root": {"env", "default"} (선택),
  "files": {"manifest": {"path", "sha256"}, "cap_npz": {...}, "verify_midpoints": [{"path", "sha256"}, ...] (선택, [LM-1e] 폭별 중점 파일 배열 --
  옛 단일 객체 꼴은 `lut_location_config_invalid`; 파일 sha256 은 파일 바이트 그대로), "noise": {...} (선택, [r7] 잡음 r1),
  "mismatch": {...} (선택, [r7] mismatch 감도 r1)}}`. `path` 는 root 기준 상대 경로
  (절대 경로·`..` 금지). root·pdk_root = 환경 변수가 비어 있지 않으면 그 값, 아니면 `default`.
* 파일마다 sha256 을 다시 재서 설정 값과 대조한다(manifest 가 슬라이스 sha256 을 고정하고 `load_lut_set` 이 그것을 대조하므로
  슬라이스는 여기서 다시 재지 않는다 -- 같은 파일 두 번 해시 안 함). 다르면 거부(조용히 다른 데이터를 쓰지 않음).
* [WB-1 범위 0] 설정 최상위 `"bin_rule": {"path", "sha256"}`(필수, `files` 밖): bin 규칙 선언 파일. `path` 는 **설정 파일 폴더** 기준 상대
  경로(절대 경로·`..` 금지), sha256 은 줄바꿈 LF 환산 값(`core.file_sha256`)과 대조한다(CRLF 로 바뀐 같은 파일은 통과).
* 결과 `LutLocation` 을 `load_lut_set(location.manifest_path, location.cap_npz_path, spec, bin_rule=location.bin_rule_path,
  pdk_root=location.pdk_root, verify_midpoints=location.midpoints_paths, noise_npz=location.noise_path,
  mismatch_npz=location.mismatch_path)` 로 넘긴다.
"""
import hashlib
import json
import os

from gmid_engine.core import file_sha256

from ._helpers_fail import schema_rejected
from .lut_types import LutLocation

_REQUIRED_FILES = ("cap_npz", "manifest")
_OPTIONAL_FILES = ("mismatch", "noise")
_MIDPOINTS = "verify_midpoints"


def _sha256_of(path):
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def _choose(entry, env, item, sources):
    name = entry.get("env")
    value = env.get(name) if name else None
    if value:
        sources.append((item, "env:" + name))
        return value
    if not entry.get("default"):
        raise schema_rejected("lut_location_config_invalid", item=item, why="no env value and no default")
    sources.append((item, "config_default"))
    return entry["default"]


def _entry_rel(item, spec):
    """파일 항목 `{path, sha256}` 의 형식 검사 -> 상대 경로. 오류 -> `lut_location_config_invalid`(item)."""
    rel = spec.get("path") if isinstance(spec, dict) else None
    if not rel or os.path.isabs(rel) or ".." in rel.replace("\\", "/").split("/") or not spec.get("sha256"):
        raise schema_rejected("lut_location_config_invalid", item=item, why="path must be relative without '..', sha256 required")
    return rel


def _file(root, item, spec):
    rel = _entry_rel(item, spec)
    path = os.path.abspath(os.path.join(root, rel))
    if not os.path.isfile(path):
        raise schema_rejected("lut_location_file_missing", item=item, path=path)
    actual = _sha256_of(path)
    if actual != spec["sha256"]:
        raise schema_rejected("lut_location_sha256_mismatch", item=item, path=path, recorded=str(spec["sha256"]),
                              actual=actual)
    return path


def _midpoint_files(root, entries):
    """`files.verify_midpoints`(`{path, sha256}` 원소의 비어 있지 않은 배열 -- 옛 단일 객체 꼴·빈 배열·같은 `path` 둘은 거부)의 절대 경로 tuple
    (`path` 오름차순). 파일 없음·raw sha256 불일치는 다른 파일 항목과 같은 사유(item `verify_midpoints`)."""
    if not isinstance(entries, list) or not entries:
        raise schema_rejected("lut_location_config_invalid", item=_MIDPOINTS, why="non-empty array of {path, sha256} required")
    rels = [_entry_rel(_MIDPOINTS, spec) for spec in entries]
    if len(set(rel.replace("\\", "/") for rel in rels)) != len(rels):
        raise schema_rejected("lut_location_config_invalid", item=_MIDPOINTS, why="duplicate path")
    ordered = sorted(zip(rels, entries), key=lambda pair: pair[0])
    return tuple(_file(root, _MIDPOINTS, spec) for _rel, spec in ordered)


def _bin_rule(config_path, spec):
    """설정 최상위 `bin_rule`({"path", "sha256"}, `files` 밖)의 선언 파일 절대 경로. `path` 는 **설정 파일 폴더** 기준 상대 경로이고
    sha256 은 LF 환산 값(`core.file_sha256`)과 대조한다. 형식 오류 -> `lut_location_config_invalid`(item "bin_rule"), 파일 없음 ->
    `lut_location_file_missing`, 값 다름 -> `lut_location_sha256_mismatch`."""
    rel = spec.get("path") if isinstance(spec, dict) else None
    if (not isinstance(rel, str) or not rel or os.path.isabs(rel) or rel.startswith(("/", "\\")) or os.path.splitdrive(rel)[0]
            or ".." in rel.replace("\\", "/").split("/") or not spec.get("sha256")):
        raise schema_rejected("lut_location_config_invalid", item="bin_rule",
                              why="object with relative path without '..' and sha256 required")
    path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(config_path)), rel))
    if not os.path.isfile(path):
        raise schema_rejected("lut_location_file_missing", item="bin_rule", path=path)
    actual = file_sha256(path)
    if actual != spec["sha256"]:
        raise schema_rejected("lut_location_sha256_mismatch", item="bin_rule", path=path, recorded=str(spec["sha256"]),
                              actual=actual)
    return path


def resolve_lut_location(config_path, env):
    """설정 파일 `config_path` 와 환경 매핑 `env`(보통 `os.environ`)로 `LutLocation` 을 만든다.

    실패(`SchemaRejectedError`): 설정 없음 `lut_location_config_missing`, 형식 오류 `lut_location_config_invalid`,
    root 폴더 없음 `lut_location_root_missing`, 파일 없음 `lut_location_file_missing`, sha256 불일치 `lut_location_sha256_mismatch`.
    """
    if not os.path.isfile(config_path):
        raise schema_rejected("lut_location_config_missing", path=str(config_path))
    with open(config_path, encoding="utf-8") as fh:
        config = json.load(fh)
    files = config.get("files")
    if not isinstance(config.get("root"), dict) or not isinstance(files, dict):
        raise schema_rejected("lut_location_config_invalid", item="root/files", why="objects required")
    sources = []
    root = os.path.abspath(_choose(config["root"], env, "root", sources))
    if not os.path.isdir(root):
        raise schema_rejected("lut_location_root_missing", path=root)
    paths = {}
    for item in _REQUIRED_FILES + _OPTIONAL_FILES:
        if item in files:
            paths[item] = _file(root, item, files[item])
        elif item in _REQUIRED_FILES:
            raise schema_rejected("lut_location_config_invalid", item=item, why="required file entry missing")
    midpoints_paths = _midpoint_files(root, files[_MIDPOINTS]) if _MIDPOINTS in files else ()
    pdk_root = None
    if isinstance(config.get("pdk_root"), dict):
        pdk_root = os.path.abspath(_choose(config["pdk_root"], env, "pdk_root", sources))
    if "bin_rule" not in config:
        raise schema_rejected("lut_location_config_invalid", item="bin_rule", why="required declaration entry missing")
    bin_rule_path = _bin_rule(config_path, config["bin_rule"])
    return LutLocation(os.path.abspath(config_path), root, paths["manifest"], paths["cap_npz"],
                       midpoints_paths, pdk_root, tuple(sorted(sources)), paths.get("noise"),
                       paths.get("mismatch"), bin_rule_path)
