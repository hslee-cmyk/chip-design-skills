"""WB-1 B-4/B-5/B-6 -- 적재 시 bin 선언 적용 (interface card §1 '적재 적용'·'지문'·§4).

oracle (손): 합성 bin toy(conftest `BinToy`, 손계산 bin 표)와 card §1 표. 경계 앵커 소속은 conftest 머리의 손 표에서 유도:
  W = 2e-6 슬라이스(위 범위 (1e-6, 3e-6] 만): A' = [1, 4] µm, D' = [4, 10] µm. 앵커 (1, 1.5, 2, 3, 4, 7, 8, 9) µm 중
  4 µm 은 두 bin 의 공유 경계 -> lower = A'(0), upper = D'(1). 나머지는 규칙 무관.
  W = 1e-6 슬라이스는 W 경계(위 범위 wmin = 아래 범위 wmax = 1e-6) -> lower = 아래 W 행, upper = 위 W 행.
기대값은 피검 함수가 아니라 이 손 표와 독립 hashlib/json 으로 만든다. meta 의 `ngspice`·`model_files_sha256` 는 합성 값이다(PDK 값 아님).
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import load_lut_set, lut_provenance

from .conftest import (BIN_MODEL_REL, BIN_W_HI, BIN_W_LO, TOY_SPEC, bin_cap_arrays, bin_model_text, detail_of)

SIM = "ngspice-46"
EMPTY_SHA = hashlib.sha256(b"").hexdigest()


def lf_sha(b):
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def decl_dict(shas, rule="lower", simulator=None):
    return {"schema": "lut_bin_rule/1", "model_files_sha256": sorted(shas),
            "simulator": simulator or {"name": "ngspice", "version": "46"},
            "compat": {"mode": "default", "spiceinit_text": "", "spiceinit_sha256": EMPTY_SHA},
            "rule": rule,
            "evidence": {"points": [{"L": 2e-6, "W": 2e-6, "chosen_bin": "toyn__model.5"}], "mode": "default",
                         "source_basis": "generator_record", "measured_by": "verifier", "date": "2026-11-04"}}


class Setup:
    """tmp 아래 모델 파일(LF 바이트 고정 또는 CRLF), 슬라이스 둘, cap, 선언을 쓴다."""

    def __init__(self, tmp, bin_toy_build, rule="lower", crlf=False, cap_meta_fn=None, decl_edit=None, ngspice=SIM,
                 extra_files=None):
        text = bin_model_text().replace("\r\n", "\n")
        data = text.replace("\n", "\r\n").encode() if crlf else text.encode()
        self.tmp = Path(tmp)
        self.pdk = self.tmp / "bt" / "pdk"
        self.model = self.pdk / BIN_MODEL_REL
        self.raw_sha = hashlib.sha256(data).hexdigest()
        self.lf = lf_sha(data)
        self.extra_files = extra_files or {}

        def meta_fn(meta):
            self.model.write_bytes(data)                       # BinToy 의 write_text 가 OS 줄바꿈을 섞으므로 바이트로 고정
            return {"pdk_root": str(self.pdk), "model_files_sha256": {BIN_MODEL_REL: self.raw_sha}, "ngspice": ngspice}
        self.toy = bin_toy_build("bt", model_text=text, meta_fn=meta_fn)
        self.model.write_bytes(data)
        for rel, b in self.extra_files.items():
            (self.pdk / rel).write_bytes(b)
        cap_meta = {"pdk_root": str(self.pdk), "model_files_sha256": {BIN_MODEL_REL: self.raw_sha}, "ngspice": ngspice}
        if cap_meta_fn:
            cap_meta = cap_meta_fn(cap_meta)
        arrays = dict(bin_cap_arrays())
        arrays["meta_json"] = np.str_(json.dumps(cap_meta))
        np.savez(self.toy.build.cap, **arrays)
        d = decl_dict([self.lf], rule)
        if decl_edit:
            d = decl_edit(d)
        self.decl = self.tmp / ("decl_%s.json" % rule)
        self.write_decl(d)

    def write_decl(self, d, path=None):
        p = Path(path or self.decl)
        p.write_text(d if isinstance(d, str) else json.dumps(d, indent=1), encoding="utf-8")
        return p

    def args(self):
        return str(self.toy.build.manifest), str(self.toy.build.cap), TOY_SPEC

    def load(self, bin_rule="decl"):
        return load_lut_set(*self.args(), bin_rule=str(self.decl) if bin_rule == "decl" else bin_rule)

    def prov(self):
        return lut_provenance(*self.args(), bin_rule=str(self.decl))


def reject(s, bin_rule="decl"):
    with pytest.raises(SchemaRejectedError) as ei:
        s.load(bin_rule)
    d = dict(ei.value.record.detail)
    assert d["reason"] == "bin_tie_undeclared"
    return d


@pytest.fixture
def base(tmp_path, bin_toy_build):
    return Setup(tmp_path, bin_toy_build)


# ---------------------------------------------------------------- 정상 / 규칙 소속 (B-5)
def test_bin_load_lower_ok_and_records_rule(base):
    lut = base.load()
    assert lut.bin_rule == "lower"
    p = base.prov()
    assert p.bin_rule == "lower"
    assert p.bin_rule_sha256 == lf_sha(base.decl.read_bytes())
    assert lut.slice_map[("nmos", 200)].l_bins.anchor_bin == (0, 0, 0, 0, 0, 1, 1, 1)


def test_bin_load_rule_changes_boundary_anchor_membership(tmp_path, bin_toy_build):
    # 같은 fixture(bin_toy_build)가 tmp_path 아래 "bt" 를 고정하므로 두 규칙은 같은 Setup 에서 선언 파일만 바꿔 적재한다.
    s = Setup(tmp_path, bin_toy_build, rule="lower")
    lower = s.load()
    s.write_decl(decl_dict([s.lf], "upper"))
    upper = s.load()
    a_lo = lower.slice_map[("nmos", 200)].l_bins.anchor_bin
    a_up = upper.slice_map[("nmos", 200)].l_bins.anchor_bin
    assert a_lo == (0, 0, 0, 0, 0, 1, 1, 1)             # 4 µm -> A'
    assert a_up == (0, 0, 0, 0, 1, 1, 1, 1)             # 4 µm -> D'
    # W 경계 슬라이스(폭 1e-6): lower = 아래 W 행, upper = 위 W 행
    assert lower.slice_map[("nmos", 100)].l_bins.w_bin == BIN_W_LO
    assert upper.slice_map[("nmos", 100)].l_bins.w_bin == BIN_W_HI
    assert upper.bin_rule == "upper" and lower.bin_rule == "lower"


def test_bin_load_without_bin_rule_keyword_is_type_error(base):
    base.load()                                          # 호출 >= 1
    with pytest.raises(TypeError):
        load_lut_set(*base.args())


# ---------------------------------------------------------------- 선언 거부
def test_bin_decl_missing(base):
    assert reject(base, None)["why"] == "decl_missing"
    assert reject(base, str(base.tmp / "absent.json"))["why"] == "decl_missing"


@pytest.mark.parametrize("name", ["json_error", "schema", "rule", "empty_list", "no_simulator"])
def test_bin_decl_invalid(base, name):
    base.load()                                          # 정상 먼저
    d = decl_dict([base.lf])
    if name == "json_error":
        d = "{not json"
    elif name == "schema":
        d["schema"] = "lut_bin_rule/2"
    elif name == "rule":
        d["rule"] = "middle"
    elif name == "empty_list":
        d["model_files_sha256"] = []
    else:
        del d["simulator"]
    base.write_decl(d)
    assert reject(base)["why"] == "decl_invalid"


# ---------------------------------------------------------------- 세트 기록 (단언은 cap)
def test_bin_model_unrecorded_cap(tmp_path, bin_toy_build):
    s = Setup(tmp_path, bin_toy_build, cap_meta_fn=lambda m: dict(m, model_files_sha256={}))
    d = reject(s)
    assert d["why"] == "model_unrecorded" and d["set"] == "cap"


def test_bin_simulator_unrecorded_cap(tmp_path, bin_toy_build):
    s = Setup(tmp_path, bin_toy_build, cap_meta_fn=lambda m: {k: v for k, v in m.items() if k != "ngspice"})
    d = reject(s)
    assert d["why"] == "simulator_unrecorded" and d["set"] == "cap"


@pytest.mark.parametrize("text, why", [("ngspice46", "simulator_unparsed"), ("ngspice-", "simulator_unparsed"),
                                       ("-46", "simulator_unparsed"), ("ngspice-45", "simulator_differs"),
                                       ("spice-46", "simulator_differs")])
def test_bin_simulator_text_cap(tmp_path, bin_toy_build, text, why):
    s = Setup(tmp_path, bin_toy_build, cap_meta_fn=lambda m: dict(m, ngspice=text))
    d = reject(s)
    assert d["why"] == why and d["set"] == "cap"


def test_bin_nested_cap_meta_passes(tmp_path, bin_toy_build):
    def nest(m):
        return dict(m, model_files_sha256={"nmos": {BIN_MODEL_REL: m["model_files_sha256"][BIN_MODEL_REL]}})
    s = Setup(tmp_path, bin_toy_build, cap_meta_fn=nest)
    assert s.load().bin_rule == "lower"


# ---------------------------------------------------------------- model 선언 대조 (cap 기록)
def test_bin_model_root_missing(tmp_path, bin_toy_build):
    s = Setup(tmp_path, bin_toy_build,
              cap_meta_fn=lambda m: {"model_files_sha256": {BIN_MODEL_REL: "0" * 64}, "ngspice": SIM})
    d = reject(s)
    assert d["why"] == "model_root_missing" and d["set"] == "cap"


def test_bin_model_file_missing(tmp_path, bin_toy_build):
    s = Setup(tmp_path, bin_toy_build,
              cap_meta_fn=lambda m: dict(m, model_files_sha256={"models/absent.spice": "1" * 64}))
    d = reject(s)
    assert d["why"] == "model_file_missing" and d["set"] == "cap"


def test_bin_model_undeclared_recorded_sha_unknown(tmp_path, bin_toy_build):
    s = Setup(tmp_path, bin_toy_build,
              cap_meta_fn=lambda m: dict(m, model_files_sha256={BIN_MODEL_REL: "2" * 64}))
    d = reject(s)
    assert d["why"] == "model_undeclared" and d["set"] == "cap"


def test_bin_model_undeclared_lf_sha_of_extra_file(tmp_path, bin_toy_build):
    extra = b"* extra model\n"
    rel = "models/extra.spice"
    s = Setup(tmp_path, bin_toy_build, extra_files={rel: extra},
              cap_meta_fn=lambda m: dict(m, model_files_sha256=dict(m["model_files_sha256"],
                                                                    **{rel: hashlib.sha256(extra).hexdigest()})))
    d = reject(s)                                       # X = LF(b) 인데 선언에 없음 -> 통과 아님
    assert d["why"] == "model_undeclared" and d["set"] == "cap"


def test_bin_machine_dependent_crlf_file_passes_and_is_recorded(tmp_path, bin_toy_build):
    s = Setup(tmp_path, bin_toy_build, crlf=True)
    assert s.raw_sha != s.lf                             # 이 환경에서 CRLF 바이트라 두 값이 다르다
    assert s.load().bin_rule == "lower"                  # X = raw(b) 이고 LF(b) 가 선언 안에 있음 -> 통과
    md = tuple(s.prov().bin_rule_machine_dependent)
    assert md == (("bin_w0.npz", BIN_MODEL_REL), ("bin_w1.npz", BIN_MODEL_REL), ("cap", BIN_MODEL_REL))


def test_bin_lf_file_has_no_machine_dependent_entries(base):
    assert tuple(base.prov().bin_rule_machine_dependent) == ()


# ---------------------------------------------------------------- 지문 (B-6)
def test_bin_fingerprint_rule_only_difference(tmp_path, bin_toy_build):
    s = Setup(tmp_path, bin_toy_build, rule="lower")
    fp_lower = s.load().fp
    assert s.load().fp == fp_lower                        # 같은 선언 -> 같다
    s.write_decl(decl_dict([s.lf], "upper"))
    assert s.load().fp != fp_lower                        # 규칙만 다르면 다르다


def test_bin_fingerprint_path_only_difference(base):
    fp1 = base.load().fp
    other = base.tmp / "elsewhere" / "other_name.json"
    other.parent.mkdir()
    other.write_bytes(base.decl.read_bytes())
    fp2 = load_lut_set(*base.args(), bin_rule=str(other)).fp
    assert fp1 == fp2                                     # 경로는 지문에 없다
