"""`resolve_lut_location` -- CONTRACT 1.8 [r6]: 설정 JSON(root·pdk_root 의 env/default, files 의 상대 path·sha256)을 풀어
`LutLocation(config_path, root, manifest_path, cap_npz_path, midpoints_paths, pdk_root, sources, noise_path, mismatch_path,
bin_rule_path)` 로. [LM-1e §1] `files.verify_midpoints` = 배열(원소 {path, sha256}), `midpoints_paths` = 절대 경로 tuple(`path` 오름차순).

- root·pdk_root = env[이름] 이 비어 있지 않으면 그 값(sources "env:<이름>"), 아니면 default("config_default"), 둘 다 없으면 거부.
  env 는 부르는 쪽이 넘긴 매핑만 본다(모듈은 os.environ 를 직접 읽지 않는다). 경로는 os.path.abspath.
- 파일: root 기준 상대 path(절대·`..`·빈 값·sha256 없음 -> lut_location_config_invalid), 없음 -> lut_location_file_missing,
  sha256 다름 -> lut_location_sha256_mismatch. 설정 없음 -> lut_location_config_missing, root 폴더 없음 -> lut_location_root_missing.
- 기대값: 이 파일이 hashlib 으로 직접 잰 sha256 과 os.path.abspath(설정 값).
"""
import dataclasses
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import LutLocation, resolve_lut_location

from .conftest import LOCATION_CONFIG, detail_of


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Cfg:
    """tmp 폴더에 root(파일 3개)·pdk 폴더·설정 JSON 을 만든다."""

    def __init__(self, tmp, name="cfg"):
        self.tmp = Path(tmp)
        self.root = self.tmp / ("data_" + name)
        (self.root / "sub").mkdir(parents=True, exist_ok=True)
        self.files = {"manifest": "manifest.json", "cap_npz": "sub/cap.npz"}
        # [LM-1e §1] 중점 파일 둘(하위 폴더 허용). 설정 안 배열 순서는 일부러 path 오름차순의 반대다.
        self.mids = ("sub/mid_b.npz", "mid_a.npz")
        for i, (item, rel) in enumerate(sorted(self.files.items())):
            (self.root / rel).write_bytes(("%s-%d" % (item, i)).encode())
        for i, rel in enumerate(self.mids):
            (self.root / rel).write_bytes(("mid-%d" % i).encode())
        self.pdk = self.tmp / ("pdk_" + name)
        self.pdk.mkdir(exist_ok=True)
        self.cfg = {"schema": "x", "ignored": 1,
                    "root": {"env": "T_LUT_ROOT", "default": str(self.root)},
                    "pdk_root": {"env": "T_PDK_ROOT", "default": str(self.pdk)},
                    "files": {item: {"path": rel, "sha256": _sha(self.root / rel)} for item, rel in self.files.items()}}
        self.cfg["files"]["verify_midpoints"] = [{"path": rel, "sha256": _sha(self.root / rel), "note": "읽지 않음"}
                                                 for rel in self.mids]
        # [WB-1 §1 위치 선언] 최상위 키 bin_rule (files 밖, path 는 설정 파일 폴더 기준, sha256 = LF 값)
        decl = b"{}\n"
        (self.tmp / ("rule_" + name + ".json")).write_bytes(decl)
        self.cfg["bin_rule"] = {"path": "rule_" + name + ".json", "sha256": hashlib.sha256(decl).hexdigest()}
        self.path = self.tmp / (name + ".json")

    def write(self, cfg=None):
        self.path.write_text(json.dumps(self.cfg if cfg is None else cfg), encoding="utf-8")
        return str(self.path)


def _reject(path, env=None):
    with pytest.raises(SchemaRejectedError) as ei:
        resolve_lut_location(path, {} if env is None else env)
    return detail_of(ei.value)


def test_text_entry_sha_independent_of_line_endings(tmp_path):
    """`files.<항목>.newline = "lf"` 면 sha256 은 CRLF→LF 환산 값이다: LF 파일·CRLF 파일 둘 다 같은 설정으로 통과한다. 키가 없으면 원본 바이트
    그대로라 CRLF 로 바뀐 파일은 거부된다(대조군). "lf" 밖 값은 형식 오류."""
    text = b"{\n \"a\": 1\n}\n"
    for crlf in (False, True):
        c = Cfg(tmp_path, name="crlf" if crlf else "lf")
        (c.root / "manifest.json").write_bytes(text.replace(b"\n", b"\r\n") if crlf else text)
        cfg = json.loads(json.dumps(c.cfg))
        cfg["files"]["manifest"] = {"path": "manifest.json", "newline": "lf", "sha256": hashlib.sha256(text).hexdigest()}
        assert resolve_lut_location(c.write(cfg), {}).manifest_path
    c = Cfg(tmp_path, name="ctrl")                                    # 대조군: newline 키 없이 LF 값으로 고정 -> CRLF 파일은 sha 불일치
    (c.root / "manifest.json").write_bytes(text.replace(b"\n", b"\r\n"))
    cfg = json.loads(json.dumps(c.cfg))
    cfg["files"]["manifest"] = {"path": "manifest.json", "sha256": hashlib.sha256(text).hexdigest()}
    assert _reject(c.write(cfg))["reason"] == "lut_location_sha256_mismatch"
    cfg["files"]["manifest"] = {"path": "manifest.json", "newline": "crlf", "sha256": hashlib.sha256(text).hexdigest()}
    assert _reject(c.write(cfg))["reason"] == "lut_location_config_invalid"


def test_defaults_resolved(tmp_path):
    c = Cfg(tmp_path)
    loc = resolve_lut_location(c.write(), {})
    assert isinstance(loc, LutLocation)
    assert loc.root == os.path.abspath(str(c.root))
    assert loc.manifest_path == os.path.abspath(os.path.join(str(c.root), "manifest.json"))
    assert loc.cap_npz_path == os.path.abspath(os.path.join(str(c.root), "sub/cap.npz"))
    # oracle (d) interface §1: 절대 경로 tuple, `path` 오름차순("mid_a.npz" < "sub/mid_b.npz") -- 설정 안 순서와 무관
    assert loc.midpoints_paths == (os.path.abspath(os.path.join(str(c.root), "mid_a.npz")),
                                   os.path.abspath(os.path.join(str(c.root), "sub/mid_b.npz")))
    assert loc.pdk_root == os.path.abspath(str(c.pdk))
    src = tuple(loc.sources)
    assert [k for k, _ in src] == sorted(k for k, _ in src)               # 항목 정렬
    d = dict(src)
    assert d["root"] == "config_default" and d["pdk_root"] == "config_default"
    assert os.path.normcase(os.path.abspath(loc.config_path)) == os.path.normcase(os.path.abspath(c.path))


def test_env_overrides_default_and_empty_env_does_not(tmp_path):
    c = Cfg(tmp_path)
    other = Cfg(tmp_path, "other")                                     # 같은 상대 path·같은 내용 -> sha 같음
    p = c.write()
    loc = resolve_lut_location(p, {"T_LUT_ROOT": str(other.root), "T_PDK_ROOT": str(other.pdk)})
    assert loc.root == os.path.abspath(str(other.root))
    assert loc.manifest_path == os.path.abspath(os.path.join(str(other.root), "manifest.json"))
    assert loc.pdk_root == os.path.abspath(str(other.pdk))
    assert dict(loc.sources)["root"] == "env:T_LUT_ROOT" and dict(loc.sources)["pdk_root"] == "env:T_PDK_ROOT"
    # 빈 값은 '설정 안 됨' -> default
    loc2 = resolve_lut_location(p, {"T_LUT_ROOT": "", "T_PDK_ROOT": ""})
    assert loc2.root == os.path.abspath(str(c.root)) and dict(loc2.sources)["root"] == "config_default"
    assert dict(loc2.sources)["pdk_root"] == "config_default"
    # env 만 있고 default 없음도 된다
    cfg = dict(c.cfg, root={"env": "T_LUT_ROOT"})
    loc3 = resolve_lut_location(c.write(cfg), {"T_LUT_ROOT": str(c.root)})
    assert loc3.root == os.path.abspath(str(c.root)) and dict(loc3.sources)["root"] == "env:T_LUT_ROOT"


def test_relative_root_is_made_absolute(tmp_path, monkeypatch):
    c = Cfg(tmp_path)
    monkeypatch.chdir(tmp_path)
    cfg = dict(c.cfg, root={"default": c.root.name})
    loc = resolve_lut_location(c.write(cfg), {})
    assert os.path.isabs(loc.root) and loc.root == os.path.abspath(c.root.name)
    assert os.path.isabs(loc.manifest_path)


def test_module_does_not_read_os_environ(tmp_path, monkeypatch):
    """env 매핑만 본다: os.environ 에 이름이 있어도 넘긴 매핑에 없으면 default."""
    c = Cfg(tmp_path)
    other = Cfg(tmp_path, "other")
    monkeypatch.setenv("T_LUT_ROOT", str(other.root))
    monkeypatch.setenv("T_PDK_ROOT", str(other.pdk))
    loc = resolve_lut_location(c.write(), {})
    assert loc.root == os.path.abspath(str(c.root)) and loc.pdk_root == os.path.abspath(str(c.pdk))
    assert dict(loc.sources)["root"] == "config_default"


def test_env_root_with_wrong_content_rejected(tmp_path):
    """env 로 옮긴 root 의 파일이 sha256 과 다르면 거부(설정이 내용을 고정한다)."""
    c = Cfg(tmp_path)
    other = Cfg(tmp_path, "other")
    (other.root / "manifest.json").write_bytes(b"different")
    det = _reject(c.write(), {"T_LUT_ROOT": str(other.root)})
    assert det["reason"] == "lut_location_sha256_mismatch"
    assert det["item"] == "manifest" and det["recorded"] == c.cfg["files"]["manifest"]["sha256"]
    assert det["actual"] == _sha(other.root / "manifest.json")
    assert os.path.abspath(det["path"]) == os.path.abspath(str(other.root / "manifest.json"))


def test_root_neither_env_nor_default_invalid(tmp_path):
    c = Cfg(tmp_path)
    det = _reject(c.write(dict(c.cfg, root={"env": "T_LUT_ROOT"})), {})
    assert det["reason"] == "lut_location_config_invalid"
    det = _reject(c.write(dict(c.cfg, pdk_root={"env": "T_PDK_ROOT"})), {"T_PDK_ROOT": ""})
    assert det["reason"] == "lut_location_config_invalid"


def test_pdk_root_optional(tmp_path):
    """[해석] pdk_root 항목이 없으면(선택) pdk_root None -- 계약은 '(선택)' 만 적는다."""
    c = Cfg(tmp_path)
    cfg = {k: v for k, v in c.cfg.items() if k != "pdk_root"}
    loc = resolve_lut_location(c.write(cfg), {})
    assert loc.pdk_root is None


def test_verify_midpoints_optional(tmp_path):
    c = Cfg(tmp_path)
    cfg = json.loads(json.dumps(c.cfg))
    del cfg["files"]["verify_midpoints"]
    loc = resolve_lut_location(c.write(cfg), {})
    assert loc.midpoints_paths == ()                       # interface §1 표: 항목 없음 -> ()
    assert loc.manifest_path == os.path.abspath(os.path.join(str(c.root), "manifest.json"))


def test_lm1e_location_fields_and_order():
    """interface §1: 칸 순서 고정, 옛 단수 칸 없음(복수 `midpoints_paths` 만)."""
    assert tuple(f.name for f in dataclasses.fields(LutLocation)) == (
        "config_path", "root", "manifest_path", "cap_npz_path", "midpoints_paths", "pdk_root", "sources", "noise_path",
        "mismatch_path", "bin_rule_path")


def test_lm1e_midpoints_order_independent_of_config_order(tmp_path):
    """interface §1 표: 같은 두 원소 역순 -> 같은 midpoints_paths(정렬)."""
    c = Cfg(tmp_path)
    cfg = json.loads(json.dumps(c.cfg))
    a = resolve_lut_location(c.write(cfg), {}).midpoints_paths
    cfg["files"]["verify_midpoints"].reverse()
    b = resolve_lut_location(c.write(cfg), {}).midpoints_paths
    assert len(a) == 2 and a == b and list(a) == sorted(a)


def _mid_cfg(c, entries):
    cfg = json.loads(json.dumps(c.cfg))
    cfg["files"]["verify_midpoints"] = entries
    return c.write(cfg)


def test_lm1e_midpoints_old_single_object_rejected(tmp_path):
    """interface §1 표: 옛 꼴 단일 객체 -> lut_location_config_invalid, item verify_midpoints."""
    c = Cfg(tmp_path)
    det = _reject(_mid_cfg(c, {"path": "mid_a.npz", "sha256": _sha(c.root / "mid_a.npz")}))
    assert det["reason"] == "lut_location_config_invalid" and det["item"] == "verify_midpoints"


def test_lm1e_midpoints_empty_array_rejected(tmp_path):
    c = Cfg(tmp_path)
    det = _reject(_mid_cfg(c, []))
    assert det["reason"] == "lut_location_config_invalid" and det["item"] == "verify_midpoints"


@pytest.mark.parametrize("why", ["not_object", "no_path", "no_sha", "absolute", "dotdot", "duplicate"])
def test_lm1e_midpoints_bad_entries_rejected(tmp_path, why):
    """interface §1 표: 원소가 객체 아님·path/sha256 없음·절대 경로·`..`·같은 path 둘 -> lut_location_config_invalid.
    절대 경로·`..` 은 실제로 있는 같은 파일을 가리켜도 거부(파일 유무 검사가 아님)."""
    c = Cfg(tmp_path)
    good = {"path": "mid_a.npz", "sha256": _sha(c.root / "mid_a.npz")}
    other = {"path": "sub/mid_b.npz", "sha256": _sha(c.root / "sub/mid_b.npz")}
    bad = {"not_object": "mid_a.npz",
           "no_path": {"sha256": good["sha256"]},
           "no_sha": {"path": "mid_a.npz"},
           "absolute": {"path": str((c.root / "mid_a.npz").resolve()), "sha256": good["sha256"]},
           "dotdot": {"path": "sub/../mid_a.npz", "sha256": good["sha256"]},
           "duplicate": dict(good)}[why]
    entries = [good, bad] if why == "duplicate" else [other, bad]
    det = _reject(_mid_cfg(c, entries))
    assert det["reason"] == "lut_location_config_invalid" and det["item"] == "verify_midpoints"


def test_lm1e_midpoints_file_missing(tmp_path):
    c = Cfg(tmp_path)
    p = c.write()
    (c.root / "sub/mid_b.npz").unlink()
    det = _reject(p)
    assert det["reason"] == "lut_location_file_missing" and det["item"] == "verify_midpoints"
    assert os.path.abspath(det["path"]) == os.path.abspath(str(c.root / "sub/mid_b.npz"))


def test_lm1e_midpoints_sha256_mismatch(tmp_path):
    c = Cfg(tmp_path)
    p = c.write()
    f = c.root / "mid_a.npz"
    f.write_bytes(f.read_bytes() + b"!")
    det = _reject(p)
    assert det["reason"] == "lut_location_sha256_mismatch" and det["item"] == "verify_midpoints"
    assert det["recorded"] == hashlib.sha256(b"mid-1").hexdigest() and det["actual"] == _sha(f)   # mid_a = Cfg 의 둘째 파일


def test_config_missing(tmp_path):
    det = _reject(str(tmp_path / "nope.json"))
    assert det["reason"] == "lut_location_config_missing"


def test_root_folder_missing(tmp_path):
    c = Cfg(tmp_path)
    det = _reject(c.write(dict(c.cfg, root={"default": str(tmp_path / "no_such_dir")})))
    assert det["reason"] == "lut_location_root_missing"
    det = _reject(c.write(), {"T_LUT_ROOT": str(tmp_path / "no_such_dir2")})
    assert det["reason"] == "lut_location_root_missing"


@pytest.mark.parametrize("bad", [
    {"root": "C:/x"},                 # root 가 객체가 아님
    {"files": ["manifest.json"]},     # files 가 객체가 아님
])
def test_root_or_files_not_object(tmp_path, bad):
    c = Cfg(tmp_path)
    det = _reject(c.write(dict(c.cfg, **bad)))
    assert det["reason"] == "lut_location_config_invalid"


@pytest.mark.parametrize("item", ["manifest", "cap_npz"])
def test_required_file_items(tmp_path, item):
    c = Cfg(tmp_path)
    cfg = json.loads(json.dumps(c.cfg))
    del cfg["files"][item]
    det = _reject(c.write(cfg))
    assert det["reason"] == "lut_location_config_invalid"


@pytest.mark.parametrize("item", ["manifest", "cap_npz"])
@pytest.mark.parametrize("why", ["absolute", "dotdot", "empty", "no_sha"])
def test_bad_file_entries(tmp_path, item, why):
    """절대 경로·`..` 조각은 실제로 있는 같은 파일을 가리켜도 거부(거부가 파일 유무 검사가 아님을 보인다)."""
    c = Cfg(tmp_path)
    cfg = json.loads(json.dumps(c.cfg))
    ent = cfg["files"][item]
    if why == "absolute":
        ent["path"] = str((c.root / c.files[item]).resolve())
    elif why == "dotdot":
        ent["path"] = "sub/../" + c.files[item]
    elif why == "empty":
        ent["path"] = ""
    else:
        del ent["sha256"]
    det = _reject(c.write(cfg))
    assert det["reason"] == "lut_location_config_invalid"
    assert det["item"] == item and "why" in det


@pytest.mark.parametrize("item", ["manifest", "cap_npz"])
def test_file_missing(tmp_path, item):
    c = Cfg(tmp_path)
    p = c.write()
    (c.root / c.files[item]).unlink()
    det = _reject(p)
    assert det["reason"] == "lut_location_file_missing" and det["item"] == item
    assert os.path.abspath(det["path"]) == os.path.abspath(str(c.root / c.files[item]))


@pytest.mark.parametrize("item", ["manifest", "cap_npz"])
def test_sha256_mismatch(tmp_path, item):
    c = Cfg(tmp_path)
    p = c.write()
    f = c.root / c.files[item]
    f.write_bytes(f.read_bytes() + b"!")
    det = _reject(p)
    assert det["reason"] == "lut_location_sha256_mismatch" and det["item"] == item
    assert det["recorded"] == c.cfg["files"][item]["sha256"] and det["actual"] == _sha(f)


# ---------------------------------------------------------------------------
# 저장소 설정(assets/lut_v2_location.json) -- 실데이터
# ---------------------------------------------------------------------------

@pytest.mark.lut_realdata
def test_repo_config_resolves_and_pins_sha(real_location):
    cfg = json.loads(LOCATION_CONFIG.read_text(encoding="utf-8"))
    loc = real_location
    env_root = os.environ.get(cfg["root"]["env"]) or None
    assert loc.root == os.path.abspath(env_root or cfg["root"]["default"])
    for item, attr in (("manifest", "manifest_path"), ("cap_npz", "cap_npz_path")):
        p = getattr(loc, attr)
        assert p == os.path.abspath(os.path.join(loc.root, cfg["files"][item]["path"]))
        assert _sha(p) == cfg["files"][item]["sha256"]                  # 설정이 고정한 내용
    # [LM-1e §1] verify_midpoints = 배열: midpoints_paths = 각 원소의 (path, sha256) -- path 오름차순, 내용 sha 고정
    ents = sorted(cfg["files"]["verify_midpoints"], key=lambda e: e["path"])
    assert loc.midpoints_paths == tuple(os.path.abspath(os.path.join(loc.root, e["path"])) for e in ents)
    assert [_sha(p) for p in loc.midpoints_paths] == [e["sha256"] for e in ents]
    env_pdk = os.environ.get(cfg["pdk_root"]["env"]) or None
    assert loc.pdk_root == os.path.abspath(os.path.join(env_pdk or cfg["pdk_root"]["default"], cfg["pdk_root"].get("subdir", "")))


@pytest.mark.lut_realdata
def test_repo_config_env_precedence_uses_passed_mapping(tmp_path):
    """같은 설정을 env 매핑으로 빈 폴더 root 에 돌리면 파일 없음으로 거부된다(env 가 default 보다 먼저라는 증거).
    매핑을 비우면 다시 default."""
    cfg = json.loads(LOCATION_CONFIG.read_text(encoding="utf-8"))
    empty = tmp_path / "empty_root"
    empty.mkdir()
    with pytest.raises(SchemaRejectedError) as ei:
        resolve_lut_location(str(LOCATION_CONFIG), {cfg["root"]["env"]: str(empty)})
    det = detail_of(ei.value)
    assert det["reason"] == "lut_location_file_missing"
    assert os.path.dirname(os.path.abspath(det["path"])) == os.path.abspath(str(empty))
    default_root = os.path.abspath(cfg["root"]["default"])
    if os.path.isdir(default_root):
        loc = resolve_lut_location(str(LOCATION_CONFIG), {})
        assert dict(loc.sources)["root"] == "config_default"
        assert loc.root == default_root
    else:                                  # 기본값은 선언을 쓴 기계의 폴더라 이 기계에 없을 수 있다 -- 그래도 default 로 풀었다는 증거: 거부 경로가 default 다
        with pytest.raises(SchemaRejectedError) as ei2:
            resolve_lut_location(str(LOCATION_CONFIG), {})
        det2 = detail_of(ei2.value)
        assert det2["reason"] == "lut_location_root_missing" and os.path.abspath(det2["path"]) == default_root


@pytest.mark.lut_realdata
def test_repo_config_feeds_load(real_location, real_lut):
    """1.8 '쓰는 법' 으로 로드한 세트: provenance 가 설정의 파일 sha256 을 가진다(중점 sha256 포함)."""
    cfg = json.loads(LOCATION_CONFIG.read_text(encoding="utf-8"))
    p = real_lut.provenance
    assert p.manifest_sha256 == cfg["files"]["manifest"]["sha256"]
    assert p.cap_sha256 == cfg["files"]["cap_npz"]["sha256"]
    assert p.midpoints_sha256 == tuple(sorted(e["sha256"] for e in cfg["files"]["verify_midpoints"]))   # interface §2 결과


# ---------------------------------------------------------------------------
# [2026-10-08 중점 변경] r2 데이터 파일 (CONTRACT 8절 '데이터 = 버전 파일 r2') -- 실데이터, 읽기 전용
# ---------------------------------------------------------------------------

L_GRID_FILE = LOCATION_CONFIG.parent / "sky130_lut_L_grid.json"
# CONTRACT 8절: r2 파일 이름 (O-180: r1 원본 LUT 는 지웠다 -- 옛 대 새 비트 동일 대조 test 도 지웠다)
R2_NAMES = {"cap_npz": "sky130_nfet_pfet_lut_v2_r2.npz"}      # [LM-1e] verify_midpoints 는 r2 단일 파일이 아니라 폭별 파일 배열


def _cfg_root(cfg):
    """설정의 root 를 resolve_lut_location 없이 직접 푼다(env 가 비어 있지 않으면 env, 아니면 default -- 1.8 문장)."""
    return os.environ.get(cfg["root"]["env"]) or cfg["root"]["default"]


def _npz_raw(path):
    with np.load(path, allow_pickle=False) as z:
        return {k: np.array(z[k]) for k in z.files}


@pytest.mark.lut_realdata
def test_repo_config_r2_sha256_match_files_directly():
    """설정의 cap_npz·verify_midpoints 가 r2 파일을 가리키고(8절 이름), 기록 sha256 = 파일을 hashlib 으로 직접 잰 값(읽기 전용).
    두 r2 파일의 meta `L_source.sha256` = 저장소 승인 L 파일(assets/sky130_lut_L_grid.json)의 실제 sha256 (1.7 (2) 대조가 요구하는 값).
    oracle: (a) 파일 바이트의 sha256 을 직접 잼."""
    cfg = json.loads(LOCATION_CONFIG.read_text(encoding="utf-8"))
    root = _cfg_root(cfg)
    l_bytes = L_GRID_FILE.read_bytes().replace(b"\r\n", b"\n")
    l_shas = {hashlib.sha256(l_bytes).hexdigest(), hashlib.sha256(l_bytes.replace(b"\n", b"\r\n")).hexdigest()}   # LUT 메타는 Windows(CRLF) 체크아웃에서 기록됐다 -- 같은 내용이면 줄바꿈과 무관
    for item, name in R2_NAMES.items():
        ent = cfg["files"][item]
        assert ent["path"] == name, item
        p = os.path.join(root, ent["path"])
        assert _sha(p) == ent["sha256"], item
        meta = json.loads(str(_npz_raw(p)["meta_json"]))
        assert meta["L_source"]["sha256"] in l_shas, item
    man = cfg["files"]["manifest"]
    assert man.get("newline") == "lf"            # 텍스트 항목은 줄바꿈 LF 환산 값으로 고정한다
    assert hashlib.sha256(Path(os.path.join(root, man["path"])).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == man["sha256"]


