"""legacy_adapter.py -- 기본 실행: 커밋된 smoke 산출물 대조(스키마, finger 규칙, 넷리스트 재생성 일치).
--run-legacy: C12(같은 dump 두 번 변환 = 같은 입력, 엔진 새 실행 = --from-dump 결과) -- 옛 엔진 ~260 s.

smoke 대조의 기대값은 smoke 입력 JSON 자체(finger_w, n_fingers, W)와 커밋된 넷리스트 파일이다.
"""
import json
import math


import jsonschema
import pytest

from conftest import ORACLE_DIR, SKILL_DIR, _run, kv, run_netlist, x_lines

SMOKE = ORACLE_DIR / "smoke"
SCHEMA = json.loads((ORACLE_DIR / "oracle_input.schema.json").read_text(encoding="utf-8"))
VARIANTS = ["sizing.engine", "layout.engine", "layout.topology"]
CIRCUIT = "current_reuse_telescopic_ota"
LUT = SKILL_DIR / "assets" / "sky130_nfet_pfet_lut_sample.npz"


def smoke_input(v):
    return json.loads((SMOKE / f"{CIRCUIT}.{v}.oracle_input.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("v", VARIANTS)
def test_smoke_input_conforms_to_schema(v):
    errs = list(jsonschema.Draft202012Validator(SCHEMA).iter_errors(smoke_input(v)))
    assert not errs, [e.message for e in errs][:5]


@pytest.mark.parametrize("v", VARIANTS)
@pytest.mark.parametrize("bias", ["free", "forced"])
def test_smoke_netlist_obeys_finger_rule(v, bias):
    """커밋된 smoke 넷리스트: 소자마다 X 줄 1개, w=finger_w, m=n_fingers, nf 없음(입력 JSON 대조)."""
    inp = smoke_input(v)
    text = (SMOKE / f"{CIRCUIT}.{v}.{bias}.cir").read_text(encoding="utf-8", errors="replace")
    xs = x_lines(text)
    assert len(xs) == len(inp["devices"])
    for d in inp["devices"]:
        hit = [ln for ln in xs if ln.split()[0].lower() == f"x{d['name']}".lower()]
        assert len(hit) == 1, d["name"]
        p = kv(hit[0].split())
        assert "nf" not in p
        assert math.isclose(float(p["w"]), d["finger_w"], rel_tol=1e-9)
        assert float(p["m"]) == d["n_fingers"]


def test_smoke_layout_self_contradicting_rows_visible_as_w_mismatch():
    """SMOKE_REPORT: layout 입력의 M11b/M20b 는 선언 W(행 w) 와 finger_w*n 이 2 배 다르다 -> W_rel +100 %."""
    inp = smoke_input("layout.engine")
    for name in ("M11b", "M20b"):
        d = next(x for x in inp["devices"] if x["name"] == name)
        rel = (d["finger_w"] * d["n_fingers"] - d["W"]) / abs(d["W"])
        assert rel == pytest.approx(1.0, abs=1e-3), (name, rel)


@pytest.mark.parametrize("v", VARIANTS)
@pytest.mark.parametrize("bias", ["free", "forced"])
def test_smoke_netlist_regenerates_identically(tmp_path, v, bias):
    """smoke 입력으로 지금 oracle_netlist.py 를 돌리면 커밋된 smoke 넷리스트와 같다(LUT 경로만 이 worktree 로)."""
    inp = smoke_input(v)
    inp["process"]["lut_npz"] = str(LUT)
    name = f"{CIRCUIT}.{v}"
    p, text, meta = run_netlist(inp, tmp_path, bias=bias, name=name)
    assert p.returncode == 0, (p.stdout + p.stderr)[-1500:]
    ref = (SMOKE / f"{CIRCUIT}.{v}.{bias}.cir").read_text(encoding="utf-8", errors="replace")
    assert text.replace("\r\n", "\n") == ref.replace("\r\n", "\n")


# ------------------------------------------------------------------ C12 (옛 엔진 새 실행)
def _strip(inp):
    x = json.loads(json.dumps(inp))
    x.pop("provenance", None)
    return x


def _adapter(args, cwd):
    p = _run([ORACLE_DIR / "legacy_adapter.py", *args], cwd)
    assert p.returncode == 0, (p.stdout + p.stderr)[-3000:]
    return p


@pytest.fixture(scope="module")
def fresh(tmp_path_factory):
    d = tmp_path_factory.mktemp("legacy_fresh")
    _adapter([CIRCUIT, d, "--w-source", "sizing", "--isrc", "engine"], d)
    dump = d / f"{CIRCUIT}.legacy_dump.json"
    assert dump.exists(), sorted(x.name for x in d.iterdir())
    return d, dump


@pytest.mark.legacy_slow
@pytest.mark.parametrize("ws,isrc", [("sizing", "engine"), ("layout", "engine"), ("layout", "topology")])
def test_c12_same_dump_twice_same_input(fresh, tmp_path, ws, isrc):
    _, dump = fresh
    outs = []
    for k in ("a", "b"):
        o = tmp_path / k
        o.mkdir()
        _adapter([CIRCUIT, o, "--from-dump", dump, "--w-source", ws, "--isrc", isrc], o)
        outs.append(json.loads((o / f"{CIRCUIT}.{ws}.{isrc}.oracle_input.json").read_text(encoding="utf-8")))
    assert _strip(outs[0]) == _strip(outs[1])


@pytest.mark.legacy_slow
def test_c12_fresh_engine_equals_from_dump(fresh, tmp_path):
    d, dump = fresh
    a = json.loads((d / f"{CIRCUIT}.sizing.engine.oracle_input.json").read_text(encoding="utf-8"))
    _adapter([CIRCUIT, tmp_path, "--from-dump", dump, "--w-source", "sizing", "--isrc", "engine"], tmp_path)
    b = json.loads((tmp_path / f"{CIRCUIT}.sizing.engine.oracle_input.json").read_text(encoding="utf-8"))
    assert _strip(a) == _strip(b)


@pytest.mark.legacy_slow
def test_c12_fresh_engine_equals_committed_smoke_input(fresh):
    """옛 엔진이 결정론적이면 새 실행 결과 = 커밋된 smoke 입력(provenance, LUT 절대 경로 제외)."""
    d, _ = fresh
    a = _strip(json.loads((d / f"{CIRCUIT}.sizing.engine.oracle_input.json").read_text(encoding="utf-8")))
    b = _strip(smoke_input("sizing.engine"))
    for x in (a, b):
        x["process"].pop("lut_npz", None)
    assert a == b
