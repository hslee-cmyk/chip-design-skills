"""card 20261104-op23 test 공용 픽스처 -- 기술자 toy, 엔진 선언 toy, LUT toy, 입력 I, 진입점 호출.

근거: interface 20261104-op23 §2, §4, §6 + oracle design §10.2, §11.1~§11.3. 이 파일은 오라클 소스를 열지 않는다.
기대값을 만드는 곳이 아니라 입력을 만드는 곳이다. 기대값은 각 test 에 손으로 적는다(oracle 출처는 test 주석).

해석(interface 가 모호해 정한 것, 한 곳에 모음 -- 바뀌면 여기만 고친다):
  * H-1 기술자 toy 의 `kinds.<k>.parallel_multiplier.source` 는 `{"value": "mult"}`(toy 는 `expr` 대신 `value`, interface §2).
  * H-2 toy 엔진 선언은 `{"schema", "pdk", "pdk_root", "sources", "quantities"}`. 항목은 interface §4 대로 `path`·`sha256`
    (quantities 는 `source`·`expression`·`basis` 셋, `E/core/CONTRACT.md` §9 의 키 이름만 따름).
  * H-3 `oracle_run.main(argv, *, adapters=None) -> int`: 어댑터 이름 -> 어댑터 객체 사전을 주입하는 진입점(D §3.1 '어댑터 선택·주입').
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

import conftest


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def lf_of(b: bytes) -> str:
    """기술자 칸 정의(LF 정규화): 왼쪽부터 \\r\\n -> \\n 한 번 (interface §3 lf_sha256 계약, 픽스처 구성용)."""
    return sha(b.replace(b"\r\n", b"\n"))


def write(p: Path, b: bytes) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b)
    return p


def dump(obj) -> bytes:
    return json.dumps(obj, indent=1, ensure_ascii=False).encode("utf-8")


# interface §4 공통 toy 파일 바이트(손으로 정한 값)
A_LIB = b"* a\r\n.param s = 1\r\n"
B_LIB = b"* b\n"
X_LIB = b"* x\r\n"
M_LIB = b".subckt mod a b\n.ends mod\n"          # T3 world 의 모델 파일(.subckt mod 정의)


class Toy:
    """폴더 F 에 쓴 toy 한 벌. 경로·바이트·기술자 사전을 들고 있고 `rewrite_*` 로 한 칸씩 바꾼다."""

    def __init__(self, F: Path, doc: dict, e: dict, **paths):
        self.F = F
        self.doc = doc
        self.e = e
        self.__dict__.update(paths)

    def write_descriptor(self, doc=None, crlf=False) -> Path:
        b = dump(self.doc if doc is None else doc)
        if crlf:
            b = b.replace(b"\n", b"\r\n")
        write(self.d, b)
        return self.d

    def write_engine_decl(self, e=None, crlf=False, resync=True) -> Path:
        """e.json 을 다시 쓰고(옵션 CRLF) 기술자의 engine_decl.sha256 을 파일 LF 값으로 맞춘다(resync)."""
        e = self.e if e is None else e
        b = dump(e)
        if crlf:
            b = b.replace(b"\n", b"\r\n")
        write(self.e_path, b)
        if resync:
            self.doc["engine_decl"]["sha256"] = lf_of(b)
            self.write_descriptor()
        return self.e_path


def toy_kind(*, includes, name="mod", geometry_unit="si", multiplier=True) -> dict:
    k = {"call_form": "subckt_wrapper", "name": {"value": name}, "inner_device": {"value": "m0"},
         "includes": [{"source": s} for s in includes], "polarity": "n"}
    if geometry_unit is not None:
        k["geometry_unit"] = geometry_unit
    if multiplier:
        k["parallel_multiplier"] = {"to": [{"target": "instance_multiplier"}], "source": {"value": "mult"}}
    return k


def build_toy(F, *, kind="nk", with_model=False, includes=None, e_crlf=False, x_bytes=X_LIB, geometry_unit="si",
              multiplier=True, tnom_quantity=True) -> Toy:
    """interface §4 공통 toy. with_model=True 면 pdk/m.lib(.subckt mod)를 엔진 `sources.m` 으로 더한다(T3 world)."""
    F = Path(F)
    pdk = F / "pdk"
    write(pdk / "a.lib", A_LIB)
    write(pdk / "b.lib", B_LIB)
    write(pdk / "x.lib", x_bytes)
    sources = {"a": {"path": "a.lib", "sha256": sha(A_LIB)}, "b": {"path": "b.lib", "sha256": sha(B_LIB)}}
    if with_model:
        write(pdk / "m.lib", M_LIB)
        sources["m"] = {"path": "m.lib", "sha256": sha(M_LIB)}
    q = {"tnom_q": {"source": "a", "expression": "tnom", "basis": "toy: 값 소비 없음(형식만)"},
         "scale_q": {"source": "a", "expression": "scale", "basis": "toy: 비 SI 단위 거부 경로의 키(값 소비 없음)"}}
    e = {"schema": "gmid_pdk_decl/1", "pdk": "toy", "pdk_root": pdk.as_posix(), "sources": sources, "quantities": q}
    e_b = dump(e)
    if e_crlf:
        e_b = e_b.replace(b"\n", b"\r\n")
    e_path = write(F / "e.json", e_b)
    dl = {"schema": "gmid_pdk_decl/1", "pdk": "toy", "pdk_root": pdk.as_posix(),
          "sources": {"a": {"path": "a.lib", "sha256": sha(A_LIB)}},
          "quantities": {k: {"source": "a", "expression": k, "basis": "toy"}
                         for k in ("ad_q", "as_q", "pd_q", "ps_q")}}
    dl_path = write(F / "dl.json", dump(dl))
    loc = {"schema": "gmid_lut_location/1", "pdk_root": {"env": "PR", "default": pdk.as_posix()}}
    l_path = write(F / "l.json", dump(loc))
    inc = includes if includes is not None else (["m"] if with_model else ["a", "x"])
    doc = {
        "schema": "oracle_pdk_descriptor/1",
        "engine_decl": {"path": "e.json", "sha256": lf_of(e_b)},
        "extra_engine_decls": {"dl": {"path": "dl.json", "sha256": lf_of(dl_path.read_bytes())}},
        "extra_sources": {"x": {"path": "x.lib", "sha256": lf_of(x_bytes), "base": "pdk_root",
                                "provenance": "toy 픽스처(test 작성자가 손으로 만든 파일)"}},
        "lut_record_root": {"location_decl": {"path": "l.json", "sha256": lf_of(l_path.read_bytes())}, "key": "pdk_root"},
        "lut_file_roles": [],
        "model_family": "toy",
        "kinds": {kind: toy_kind(includes=inc, geometry_unit=geometry_unit, multiplier=multiplier)},
        "corners": {"names": ["tt"], "select": {"how": "include_path"}},
        "temperature": {"range_source": "spec"},
        "diffusion": {"decl": "dl", "ad_per_w": "ad_q", "as_per_w": "as_q", "pd_extra": "pd_q", "ps_extra": "ps_q"},
    }
    if tnom_quantity:
        doc["temperature"]["tnom"] = {kind: {"source": "tnom_q"}}
    toy = Toy(F, doc, e, d=F / "d.json", e_path=e_path, dl_path=dl_path, l_path=l_path, pdk=pdk, kind=kind)
    toy.write_descriptor()
    return toy


# ------------------------------------------------------------------ LUT toy
def make_lut_toy(path, *, model_sha=None, meta="flat", corner="tt", temp_c=27.0, nested_key="k", with_meta=True,
                 meta_raw=None) -> Path:
    """npz 키 corner·temp_c·meta_json. model_sha = {상대 경로: raw sha}. meta = flat | nested | none."""
    kw = {}
    if corner is not None:
        kw["corner"] = np.array(corner)
    if temp_c is not None:
        kw["temp_c"] = np.array(float(temp_c))
    if with_meta:
        table = model_sha if model_sha is not None else {}
        body = {"model_files_sha256": table if meta == "flat" else {nested_key: table}}
        if meta_raw is not None:
            body = {"model_files_sha256": meta_raw}
        kw["meta_json"] = np.array(json.dumps(body))
    np.savez(path, **kw)
    return Path(path)


# ------------------------------------------------------------------ 입력 I (D §11.3 예시, 새 형식)
NO_DIFF = {"ad_m2": 0.0, "as_m2": 0.0, "pd_m": 0.0, "ps_m": 0.0, "basis": "test: 면적 0 명시(기술자 확산 값 소비 없이 입력으로 충족, C22)"}


def base_input(toy: Toy, lut: Path, *, kind="nmos", circuit="cs_toy") -> dict:
    """D §11.3 예시. testbench 값만 손 값 검증이 가능하도록 정함(dc_choke_H = 1e12, fstart = 0.01 Hz):
    쵸크 임피던스 2π·0.01·1e12 = 6.3e10 Ω 이 출력 저항 1.5e4 Ω 의 4e6 배라 손 값 오차 2.4e-7 < 1e-6."""
    return {
        "schema": "spice_oracle_input/2",
        "circuit": circuit,
        "process": {"descriptor": {"path": toy.d.as_posix(), "sha256": lf_of(toy.d.read_bytes())},
                    "lut_files": [{"path": Path(lut).as_posix(), "sha256": sha(Path(lut).read_bytes()),
                                   "kinds": {kind: None}}]},
        "simulator": {"adapter": "stub", "exe": sys.executable,
                      "options": {"reltol": "1e-4", "vntol": "1e-7", "abstol": "1e-13"}},
        "rails": [{"net": "vdd", "voltage": 1.8}, {"net": "gnd", "voltage": 0.0, "reference": True}],
        "devices": [{"name": "M1", "kind": kind, "drain": "out", "gate": "in", "source": "gnd", "bulk": "gnd",
                     "L": 5e-7, "finger_w": 1e-6, "n_fingers": 2, "W": 2e-6, "diffusion": dict(NO_DIFF)}],
        "passives": [{"name": "RL", "kind": "resistor", "terminals": ["vdd", "out"], "value": 20000.0}],
        "ports": {"input": "in", "output": "out"},
        "predictions": {"nodes": {"in": 0.6, "out": 0.9},
                        "devices": {"M1": {"ID": 4.5e-5, "VGS": 0.6, "VDS": 0.9, "VSB": 0.0, "gm": 6.0e-4,
                                           "gds": 1.0 / 60000.0, "gm_id": 13.3, "region": "sat", "off_current_A": 1.2e-11}},
                        "metrics": [{"measure": "dc_gain_db", "value": 21.6}]},
        "testbench": {"dc_choke_H": 1e12, "ac_couple_F": 1.0,
                      "ac": {"fstart_hz": 0.01, "fstop_hz": 1e10, "points_per_decade": 20, "input_ac": 1.0}},
        "judge": {"sat_margin_V": 0.0},
    }


class World:
    """with_model toy + 모델 기록을 가진 LUT + 입력 I. `run(...)` 이 stub 로 진입점을 돈다."""

    def __init__(self, tmp: Path, *, kind="nmos", **toy_kw):
        self.tmp = Path(tmp)
        self.toy = build_toy(self.tmp / "world", kind=kind, with_model=True, **toy_kw)
        self.kind = kind
        self.lut = make_lut_toy(self.tmp / "world" / "lut.npz", model_sha={"m.lib": sha(M_LIB)})
        self.inp = base_input(self.toy, self.lut, kind=kind)

    def refresh_input_hashes(self):
        """기술자·LUT 파일을 고친 뒤 입력의 sha 칸을 다시 맞춘다."""
        self.inp["process"]["descriptor"]["sha256"] = lf_of(self.toy.d.read_bytes())
        self.inp["process"]["lut_files"][0]["sha256"] = sha(Path(self.lut).read_bytes())

    def run(self, stub, inp=None, out=None, extra=(), cli_simulator="stub"):
        """진입점 `oracle_run.main` 을 주입 어댑터 `stub` 로 돈다 -> (rc, out_dir). cli_simulator=None 이면 입력 칸만 쓴다."""
        import oracle_run                      # sys.path 는 conftest 가 ORACLE_DIR 로 맞춘다
        out = Path(out) if out is not None else self.tmp / "out"
        out.mkdir(parents=True, exist_ok=True)
        inp = self.inp if inp is None else inp
        ip = conftest.write_json(self.tmp / "inputs" / f"{out.name}.input.json", inp)   # 입력은 출력 폴더 밖(산출물만 센다)
        sim = ["--simulator", cli_simulator] if cli_simulator else []
        rc = oracle_run.main([str(ip), str(out), "--bias", "free", *sim, *map(str, extra)], adapters={"stub": stub})
        return rc, out


def read_reject(out: Path, circuit="cs_toy") -> dict:
    p = out / f"{circuit}.reject.json"
    assert p.exists(), f"거부 기록 없음: {sorted(x.name for x in out.iterdir())}"
    return json.loads(p.read_text(encoding="utf-8"))


def read_json_glob(out: Path, pattern: str) -> dict:
    hits = sorted(out.glob(pattern))
    assert len(hits) == 1, (pattern, [h.name for h in out.iterdir()])
    return json.loads(hits[0].read_text(encoding="utf-8"))


def deep(d):
    return copy.deepcopy(d)
