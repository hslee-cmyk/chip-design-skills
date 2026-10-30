"""legacy_adapter.py -- 기본 실행: 커밋된 smoke 산출물 대조(스키마, finger 규칙, 넷리스트 재생성 일치).
(O-180: 옛 엔진을 새로 돌리는 C12 test 는 sample LUT 삭제로 옛 하네스가 실행되지 않아 지웠다.)

smoke 대조의 기대값은 smoke 입력 JSON 자체(finger_w, n_fingers, W)와 커밋된 넷리스트 파일이다.
"""
import json
import math
import os
import sys
from pathlib import Path

import jsonschema
import pytest

from conftest import ORACLE_DIR, SKILL_DIR, _run, kv, run_netlist, x_lines

SMOKE = ORACLE_DIR / "smoke"
SCHEMA = json.loads((ORACLE_DIR / "oracle_input.schema.json").read_text(encoding="utf-8"))
VARIANTS = ["sizing.engine", "layout.engine", "layout.topology"]
CIRCUIT = "current_reuse_telescopic_ota"
sys.path.insert(0, str(SKILL_DIR))
from gmid_engine.lut import resolve_lut_location  # noqa: E402  (엔진 밖 사실만: 오라클은 LUT 의 corner·temp_c 메타만 읽는다)

# LUT = 위치 선언(assets/lut_v2_location.json)이 고정한 기준 LUT 하나(O-180). 오라클 넷리스트는 npz 의 corner·temp_c 만 쓴다.
LUT = Path(resolve_lut_location(str(SKILL_DIR / "assets" / "lut_v2_location.json"), os.environ).cap_npz_path)


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


@pytest.mark.parametrize("v", VARIANTS)
def test_c12_smoke_input_declares_feedback_passives_on_input_ports(v):
    """C12 [변경]: 입력 포트 넷에 단자가 물린 passives 를 feedback_passives 로 선언(smoke 입력 JSON 에서 직접 계산)."""
    inp = smoke_input(v)
    in_nets = {inp["ports"][k] for k in ("input_p", "input_n", "input") if k in inp["ports"]}
    exp = sorted(x["name"] for x in inp["passives"] if set(x["terminals"]) & in_nets)
    assert exp, "입력 넷에 물린 passives 가 없다(조건 점검)"
    assert sorted(inp.get("feedback_passives", [])) == exp


@pytest.mark.parametrize("v", VARIANTS)
@pytest.mark.parametrize("bias", ["free", "forced"])
def test_smoke_loop_netlist_regenerates_identically(tmp_path, v, bias):
    inp = smoke_input(v)
    inp["process"]["lut_npz"] = str(LUT)
    name = f"{CIRCUIT}.{v}"
    p, text, meta = run_netlist(inp, tmp_path, bias=bias, name=name)
    assert p.returncode == 0, (p.stdout + p.stderr)[-1500:]
    got = (tmp_path / f"{name}.{bias}.loop.cir").read_text(encoding="utf-8", errors="replace")
    ref = (SMOKE / f"{CIRCUIT}.{v}.{bias}.loop.cir").read_text(encoding="utf-8", errors="replace")
    assert got.splitlines() == ref.splitlines()


# ------------------------------------------------------------------ C12 (옛 엔진 새 실행)
