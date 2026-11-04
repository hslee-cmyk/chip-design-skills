"""X-13: 오라클 기술자가 가리키는 엔진 선언 파일 sha256 정합 + 원본 중복 0 (card 20261104-op23, interface §4).

오라클·엔진 모듈을 import하지 않고 JSON과 파일 바이트만 읽는다. oracle (d): 계획 N3.4 규칙 — 기술자 칸은 LF 정규화 값,
`engine_decl`·`extra_engine_decls` 의 sha256 은 그 파일 바이트의 LF 값과 같아야 하고, 엔진 선언 `sources` 전부와 기술자
`extra_sources` 전부는 경로도 바이트에서 다시 잰 LF sha256 도 겹치지 않는다(파일이 없으면 실패).
"""
import hashlib
import json
from pathlib import Path

DESC = (Path(__file__).resolve().parents[3] / "tools" / "spice_oracle" / "descriptors" / "sky130.oracle_descriptor.json")


def lf(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()   # 정규화 한 줄(test 안에 둔다)


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def test_descriptor_decl_sha256_equal_file_lf_sha256():
    d = _load(DESC)
    refs = {"engine_decl": d["engine_decl"], **{f"extra_engine_decl:{k}": v for k, v in d["extra_engine_decls"].items()}}
    assert len(refs) >= 2
    for name, r in refs.items():
        p = (DESC.parent / r["path"]).resolve()
        assert p.is_file(), (name, str(p))
        assert r["sha256"] == lf(p.read_bytes()), name


def _files(decl_path, entries, pdk_root):
    out = {}
    for k, e in entries.items():
        base = pdk_root if e.get("base", "pdk_root") == "pdk_root" else decl_path.parent
        out[k] = (Path(base) / e["path"]).resolve()
    return out


def test_engine_sources_and_extra_sources_do_not_overlap():
    d = _load(DESC)
    decl_path = (DESC.parent / d["engine_decl"]["path"]).resolve()
    decl = _load(decl_path)
    pdk_root = Path(decl["pdk_root"])
    eng = _files(decl_path, decl["sources"], pdk_root)
    ext = _files(decl_path, d["extra_sources"], pdk_root)
    assert eng and ext
    for k, p in {**eng, **ext}.items():
        assert p.is_file(), (k, str(p))                       # 파일 없으면 실패
    assert not (set(eng.values()) & set(ext.values())), "경로 겹침"
    eng_lf = {lf(p.read_bytes()) for p in eng.values()}
    ext_lf = {lf(p.read_bytes()) for p in ext.values()}
    assert not (eng_lf & ext_lf), "바이트 재측정 LF sha256 겹침"
