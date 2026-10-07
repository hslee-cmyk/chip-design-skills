"""C21 실행 캐시(--cache-dir): 같은 키면 hit + 결과 동일, 넷리스트·모델 파일이 바뀌면 miss, 모델 파일 못 찾으면 off.

모델 파일은 tmp 로 복사한 사본을 include 해서 바꿔 본다(PDK 원본은 건드리지 않는다).
"""
import json
import shutil

import pytest

from conftest import PDK, NFET, PFET, fb_input, make_lut, run_oracle, stem_of


def _copy_models(dst):
    dst.mkdir(parents=True, exist_ok=True)
    files = {"n_pm3": PDK / "cells/nfet_01v8" / f"{NFET}__tt.pm3.spice",
             "n_mm": PDK / "cells/nfet_01v8" / f"{NFET}__mismatch.corner.spice",
             "lod": PDK / "models/parameters/lod.spice",
             "p_pm3": PDK / "cells/pfet_01v8" / f"{PFET}__tt.pm3.spice",
             "p_mm": PDK / "cells/pfet_01v8" / f"{PFET}__mismatch.corner.spice"}
    out = {}
    for k, f in files.items():
        out[k] = dst / f.name
        shutil.copyfile(f, out[k])
    return out


def _inp(tmp, models):
    inp = fb_input(make_lut(tmp / "lut.npz"))
    pm = inp["process"]["models"]
    pm["nmos"]["includes"] = [models["n_pm3"].as_posix(), models["n_mm"].as_posix()]
    pm["pmos"]["includes"] = [models["lod"].as_posix(), models["p_pm3"].as_posix(), models["p_mm"].as_posix()]
    return inp


def _sim(out, inp):
    return json.loads((out / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))


def _strip(sim):
    s = dict(sim)
    s.pop("cache", None)
    return s


@pytest.fixture(scope="module")
def setup(tmp_path_factory, ref_root):  # ref_root: ngspice/PDK 없으면 skip
    d = tmp_path_factory.mktemp("cache")
    return d, _copy_models(d / "models")


def test_cache_hit_on_rerun_same_results(setup):
    d, models = setup
    inp = _inp(d, models)
    cache = d / "c1"
    p1, r1 = run_oracle(inp, d / "o1", extra=["--cache-dir", cache])
    s1 = _sim(d / "o1", inp)
    assert s1["cache"] == {"main": "miss", "loop": "miss"}, s1["cache"]
    p2, r2 = run_oracle(inp, d / "o2", extra=["--cache-dir", cache])
    s2 = _sim(d / "o2", inp)
    assert s2["cache"] == {"main": "hit", "loop": "hit"}, s2["cache"]
    assert s2["ac"] == s1["ac"] and s2["devices"] == s1["devices"] and s2["nodes"] == s1["nodes"]
    stem = stem_of(inp, "free")
    for ext in (".ac.txt", ".loop.v.txt", ".loop.i.txt"):
        assert (d / "o1" / f"{stem}{ext}").read_bytes() == (d / "o2" / f"{stem}{ext}").read_bytes(), ext
    a, b = r1["free"], r2["free"]
    for k in ("summary", "devices", "nodes", "performance", "constraints"):
        assert a[k] == b[k], k


def test_no_cache_dir_is_none(setup):
    d, models = setup
    inp = _inp(d, models)
    run_oracle(inp, d / "o0")
    assert _sim(d / "o0", inp).get("cache") in (None, {"main": None, "loop": None})


def test_netlist_change_misses(setup):
    d, models = setup
    inp = _inp(d, models)
    cache = d / "c2"
    run_oracle(inp, d / "a", extra=["--cache-dir", cache])
    inp2 = json.loads(json.dumps(inp))
    inp2["passives"][0]["value"] = 1.1e5
    run_oracle(inp2, d / "b", extra=["--cache-dir", cache])
    assert _sim(d / "b", inp2)["cache"]["main"] == "miss"


def test_model_file_change_misses(setup, tmp_path):
    d, _ = setup
    models = _copy_models(tmp_path / "models")
    inp = _inp(tmp_path, models)
    cache = tmp_path / "cache"
    run_oracle(inp, tmp_path / "a", extra=["--cache-dir", cache])
    run_oracle(inp, tmp_path / "b", extra=["--cache-dir", cache])
    assert _sim(tmp_path / "b", inp)["cache"]["main"] == "hit"
    with open(models["n_mm"], "ab") as f:            # 모델 바이트만 바꿈(주석 한 줄)
        f.write(b"\n* cache test touch\n")
    run_oracle(inp, tmp_path / "c", extra=["--cache-dir", cache])
    assert _sim(tmp_path / "c", inp)["cache"]["main"] == "miss"


def test_nested_include_change_misses(setup, tmp_path):
    """재귀: include 한 래퍼 파일이 다시 include 하는 모델 파일이 바뀌어도 miss."""
    models = _copy_models(tmp_path / "models")
    wrap = tmp_path / "models" / "wrap_n.spice"
    wrap.write_text(f'* wrapper\n.include "{models["n_pm3"].as_posix()}"\n', encoding="utf-8")
    inp = _inp(tmp_path, models)
    inp["process"]["models"]["nmos"]["includes"][0] = wrap.as_posix()
    cache = tmp_path / "cache"
    run_oracle(inp, tmp_path / "a", extra=["--cache-dir", cache])
    run_oracle(inp, tmp_path / "b", extra=["--cache-dir", cache])
    assert _sim(tmp_path / "b", inp)["cache"]["main"] == "hit"
    with open(models["n_pm3"], "ab") as f:
        f.write(b"\n* nested touch\n")
    run_oracle(inp, tmp_path / "c", extra=["--cache-dir", cache])
    assert _sim(tmp_path / "c", inp)["cache"]["main"] == "miss"


def test_missing_model_file_cache_off(setup, tmp_path):
    models = _copy_models(tmp_path / "models")
    wrap = tmp_path / "models" / "wrap_n.spice"
    wrap.write_text(f'.include "{models["n_pm3"].as_posix()}"\n.include "{(tmp_path / "nope.spice").as_posix()}"\n',
                    encoding="utf-8")
    inp = _inp(tmp_path, models)
    inp["process"]["models"]["nmos"]["includes"][0] = wrap.as_posix()
    run_oracle(inp, tmp_path / "a", extra=["--cache-dir", tmp_path / "cache"])
    c = _sim(tmp_path / "a", inp)["cache"]
    assert str(c["main"]).startswith("off"), c
