"""legacy_adapter.py -- 기본 실행: 커밋된 smoke 산출물 대조(옛 형식 거부, finger 규칙).
(O-180: 옛 엔진을 새로 돌리는 C12 test 는 sample LUT 삭제로 옛 하네스가 실행되지 않아 지웠다.)

card 20261104-op23 (spec C-3.10, D §18.2): 스키마 적합 test 는 '옛 형식이라 거부(oracle_input_format_old)' test 로 바꾸고,
넷리스트·루프 넷리스트 재생성 일치 test 둘은 지우고 `criteria_weakened` 에 올린다(같은 비교 = 검증자 N4-3).
smoke 대조의 기대값은 smoke 입력 JSON 자체(finger_w, n_fingers, W)와 커밋된 넷리스트 파일이다.
"""
import json
import math
from pathlib import Path

import pytest

from conftest import ORACLE_DIR, _run, kv, x_lines

SMOKE = ORACLE_DIR / "smoke"
VARIANTS = ["sizing.engine", "layout.engine", "layout.topology"]
CIRCUIT = "current_reuse_telescopic_ota"


def smoke_input(v):
    return json.loads((SMOKE / f"{CIRCUIT}.{v}.oracle_input.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("v", VARIANTS)
def test_smoke_input_is_old_format_and_rejected(tmp_path, v):
    """고정 자료 smoke 입력은 옛 형식(spice_oracle_input/1)이다 -> 새 진입점은 이중 지원 없이 거부한다.
    oracle (d) 사용자 선언 규칙(D §11.2 1b 표지 목록): 걸린 표지 = 입력 JSON 에 실제로 있는 표지 전부(입력 파일에서 직접 센다)."""
    inp = smoke_input(v)
    expected = ({"schema"} if inp.get("schema") == "spice_oracle_input/1" else set())
    expected |= {f"process.{k}" for k in ("models", "ngspice_exe", "lut_npz", "diffusion") if k in inp["process"]}
    expected |= {"testbench.options"} if "options" in inp["testbench"] else set()
    assert "schema" in expected and len(expected) >= 4, expected             # 조건 점검: 옛 표지가 실제로 있다
    ip = tmp_path / "in.json"
    ip.write_text(json.dumps(inp), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    p = _run([ORACLE_DIR / "oracle_run.py", ip, out, "--bias", "free"], tmp_path)
    assert p.returncode == 2, (p.stdout + p.stderr)[-1500:]
    rec = json.loads((out / f"{CIRCUIT}.reject.json").read_text(encoding="utf-8"))
    assert rec["code"] == "oracle_input_format_old" and set(rec["detail"]["markers"]) == expected
    assert sorted(p.name for p in out.iterdir()) == [f"{CIRCUIT}.reject.json"]       # 산출물은 거부 기록 하나


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
def test_c12_smoke_input_declares_feedback_passives_on_input_ports(v):
    """C12 [변경]: 입력 포트 넷에 단자가 물린 passives 를 feedback_passives 로 선언(smoke 입력 JSON 에서 직접 계산)."""
    inp = smoke_input(v)
    in_nets = {inp["ports"][k] for k in ("input_p", "input_n", "input") if k in inp["ports"]}
    exp = sorted(x["name"] for x in inp["passives"] if set(x["terminals"]) & in_nets)
    assert exp, "입력 넷에 물린 passives 가 없다(조건 점검)"
    assert sorted(inp.get("feedback_passives", [])) == exp


# ------------------------------------------------------------------ C12 (옛 엔진 새 실행)
