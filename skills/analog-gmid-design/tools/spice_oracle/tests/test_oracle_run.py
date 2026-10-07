"""oracle_run.py -- 끝단 실행: 합격 정의(2026-10-07)·C8 반환 코드, BLOCKED 우선순위, 산출물 이름(--tag), 결정론(같은 입력 두 번 = 같은 출력),
C1(엔진 import 없음), C11(테스트벤치 값 숫자 기본값 없음).
"""
import ast
import copy
import filecmp
import json

import pytest

from conftest import (CS, OFF_ZERO, ORACLE_DIR, cs_input, make_lut, run_netlist, run_oracle, require_spice, stem_of)


@pytest.fixture(autouse=True)
def _spice():
    require_spice()


GAIN_FAIL = [{"name": "g", "measure": "dc_gain_db", "op": ">=", "limit": 100.0}]   # SPICE ~22 dB -> FAIL
GAIN_PASS = [{"name": "g", "measure": "dc_gain_db", "op": ">=", "limit": 10.0}]


# ------------------------------------------------------------------ C8 반환 코드
def test_c8_incomplete_returns_0(tmp_path):
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": 0.9, "pout": 0.16},
                   constraints=GAIN_PASS)
    p, res = run_oracle(inp, tmp_path / "o", biases=("free", "forced"))
    assert {b: r["summary"]["verdict"] for b, r in res.items()} == {"free": "INCOMPLETE", "forced": "INCOMPLETE"}
    assert p.returncode == 0, p.stdout + p.stderr


def test_c8_constraint_fail_returns_1(tmp_path):
    inp = cs_input(make_lut(tmp_path / "lut.npz"), constraints=GAIN_FAIL)
    p, res = run_oracle(inp, tmp_path / "o")
    assert res["free"]["summary"]["verdict"] == "FAIL" and p.returncode == 1


@pytest.mark.parametrize("how", ["npz_no_corner", "two_references", "gate_net_no_value"])
def test_c8_blocked_without_fail_returns_2(tmp_path, how):
    lut = make_lut(tmp_path / "lut.npz", corner=None if how == "npz_no_corner" else "tt")
    inp = cs_input(lut, bias_voltages=None if how == "gate_net_no_value" else "default")
    if how == "two_references":
        inp["rails"][1]["reference"] = True
    p, res = run_oracle(inp, tmp_path / "o")
    r = res["free"]
    assert r is not None, p.stdout + p.stderr
    assert r["blockers"], r["summary"]
    assert r["summary"]["verdict"] == "BLOCKED" and p.returncode == 2


def test_c2_npz_without_temp_blocked_returns_2(tmp_path):
    """C2 [변경]: npz 에 temp_c 가 없으면 막힘, .temp 줄 없음, ngspice 를 돌리지 않음(sim.skipped), BLOCKED, 반환 2."""
    inp = cs_input(make_lut(tmp_path / "lut.npz", temp_c=None))
    out = tmp_path / "o"
    p, res = run_oracle(inp, out)
    r = res["free"]
    assert r is not None, f"비교표 없음 rc={p.returncode} {(p.stdout + p.stderr)[-800:]}"
    assert r["blockers"] and r["summary"]["verdict"] == "BLOCKED" and p.returncode == 2
    stem = stem_of(inp, "free")
    cir = (out / f"{stem}.cir").read_text(encoding="utf-8")
    assert not any(ln.lower().startswith(".temp") for ln in cir.splitlines())
    sim = json.loads((out / f"{stem}.sim.json").read_text(encoding="utf-8"))
    assert sim.get("skipped"), sim


def test_c8_pass_returns_0(tmp_path):
    """합격 정의: free, 제약 만족 + 전도 MOS 전부 포화(sat_margin 0.05 V; 손계산 여유 M1 ~0.83 V, MP1 ~1.14 V) -> PASS, 반환 0."""
    # [C23 조정] 전도 문턱 0(옛 ID > 0 규칙)을 소자별로 명시 -- 없으면 PASS 대신 INCOMPLETE
    inp = cs_input(make_lut(tmp_path / "lut.npz"), constraints=GAIN_PASS, preds_devices=copy.deepcopy(OFF_ZERO))
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=0.05)
    assert res["free"]["summary"]["verdict"] == "PASS", res["free"]["summary"]
    assert p.returncode == 0


def test_c8_unsaturated_returns_1(tmp_path):
    inp = cs_input(make_lut(tmp_path / "lut.npz"), constraints=GAIN_PASS)
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=1.0)   # M1 여유 ~0.83 V < 1.0
    assert res["free"]["summary"]["verdict"] == "FAIL" and p.returncode == 1


def test_c8_blocked_beats_fail_returns_2(tmp_path):
    """C8 [변경]: 막힘이 있으면 BLOCKED -- 제약 FAIL·포화 실패가 함께 있어도(반환 2)."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"), constraints=GAIN_FAIL)
    inp["rails"][1]["reference"] = True          # reference 2 개 -> 막힘(C4)
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=5.0)
    r = res["free"]
    assert r["blockers"]
    assert r["summary"]["verdict"] == "BLOCKED" and p.returncode == 2


def test_c8_worst_bias_decides_return_code(tmp_path):
    """free 는 포화 실패로 FAIL, forced 는 늘 INCOMPLETE -> 최악 = FAIL -> 반환 1."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": 0.8, "pout": 0.2})
    p, res = run_oracle(inp, tmp_path / "o", biases=("free", "forced"), sat_margin=1.0)
    assert res["free"]["summary"]["verdict"] == "FAIL"
    assert res["forced"]["summary"]["verdict"] == "INCOMPLETE"
    assert p.returncode == 1


def test_c8_forced_only_is_incomplete_returns_0(tmp_path):
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": 0.8, "pout": 0.2}, constraints=GAIN_FAIL)
    p, res = run_oracle(inp, tmp_path / "o", biases=("forced",), sat_margin=1.0)
    assert res["forced"]["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0


# ------------------------------------------------------------------ 산출물 이름
def test_outputs_named_by_circuit_tag_bias(tmp_path):
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": 0.9, "pout": 0.16})
    out = tmp_path / "o"
    p, res = run_oracle(inp, out, biases=("free", "forced"), tag="v1")
    for b in ("free", "forced"):
        stem = stem_of(inp, b, "v1")
        for ext in (".cir", ".cir.meta.json", ".log", ".ac.txt", ".sim.json", ".compare.json", ".compare.md"):
            assert (out / f"{stem}{ext}").exists(), f"{stem}{ext}"
        assert res[b]["bias"] == b


# ------------------------------------------------------------------ 결정론
def test_deterministic_same_input_same_outputs(tmp_path):
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": 0.9, "pout": 0.16},
                   constraints=GAIN_PASS)
    out = tmp_path / "o"
    run_oracle(inp, out, biases=("free", "forced"))
    snap = tmp_path / "first"
    snap.mkdir()
    exts = (".cir", ".cir.meta.json", ".ac.txt", ".sim.json", ".compare.json", ".compare.md")
    names = [f"{stem_of(inp, b)}{e}" for b in ("free", "forced") for e in exts]
    for n in names:
        (snap / n).write_bytes((out / n).read_bytes())
    run_oracle(copy.deepcopy(inp), out, biases=("free", "forced"))
    diff = [n for n in names if not filecmp.cmp(snap / n, out / n, shallow=False)]
    assert not diff, diff


# ------------------------------------------------------------------ C1
def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            mods.add(node.module or "")
        elif isinstance(node, ast.Call) and getattr(node.func, "attr", getattr(node.func, "id", "")) in (
                "import_module", "__import__"):
            mods |= {a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)}
    return mods


ORACLE_FILES = sorted(p.name for p in ORACLE_DIR.glob("oracle_*.py"))


def test_c1_oracle_files_exist():
    assert set(ORACLE_FILES) >= {"oracle_netlist.py", "oracle_simulate.py", "oracle_compare.py", "oracle_run.py"}


@pytest.mark.parametrize("name", ORACLE_FILES)
def test_c1_oracle_does_not_import_engines(name):
    bad = [m for m in _imports(ORACLE_DIR / name)
           if m.split(".")[0] in ("gmid_engine", "legacy") or "gmid_engine" in m or m.startswith("legacy")]
    assert not bad, f"{name}: {bad}"


# ------------------------------------------------------------------ C11
@pytest.mark.parametrize("key", ["fstop_hz", "points_per_decade"])
def test_c11_missing_required_testbench_value_rejected(tmp_path, key):
    """C11: 스키마 필수 testbench 값이 빠지면 C13 거부(반환 2, 넷리스트 없음)."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"))
    del inp["testbench"]["ac"][key]
    p, text, meta = run_netlist(inp, tmp_path)
    assert p.returncode == 2 and text is None and meta is None, p.returncode


def test_c11_missing_optional_input_ac_blocks(tmp_path):
    """C11: 필요한 선택 값(input_ac, 단일 입력) 이 없으면 막힘 -- 지어낸 AC 크기로 넷리스트를 만들지 않는다."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"))
    del inp["testbench"]["ac"]["input_ac"]
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta is not None and meta["blockers"], f"rc={p.returncode} {(p.stdout + p.stderr)[-500:]}"


@pytest.mark.parametrize("key", ["diff_feedback_gain", "input_p_ac"])
def test_c11_missing_optional_diff_values_block(tmp_path, key):
    """C11: 차동 입력·차동 출력 회로에서 diff_feedback_gain / input_p_ac 가 없으면 막힘."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": 0.9, "nout2": 0.95, "nin2": 0.65})
    inp["devices"].append({"name": "M2", "kind": "nmos", "drain": "nout2", "gate": "nin2", "source": "gnd",
                           "bulk": "gnd", "L": 0.5e-6, "finger_w": 2e-6, "n_fingers": 2, "W": 4e-6})
    inp["passives"].append({"name": "RL2", "kind": "resistor", "terminals": ["vdd", "nout2"], "value": 1e5})
    inp["ports"] = {"input_p": "nin", "input_n": "nin2", "output_p": "nout", "output_n": "nout2"}
    p0, _, meta0 = run_netlist(inp, tmp_path / "ok")
    assert p0.returncode == 0 and meta0["blockers"] == []        # 양성 대조
    del inp["testbench"]["ac"][key]
    p, text, meta = run_netlist(inp, tmp_path / "bad")
    assert meta is not None and meta["blockers"], f"rc={p.returncode} {(p.stdout + p.stderr)[-500:]}"


def test_c11_no_default_sat_margin_or_tolerance(tmp_path):
    """판정 설정이 없으면 포화 여유·허용오차가 숫자 기본값으로 채워지지 않는다(judge_config 가 비어 있음)."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"))
    p, res = run_oracle(inp, tmp_path / "o")
    jc = res["free"]["judge_config"]
    assert not jc.get("tolerances") and jc.get("sat_margin_V") is None and jc.get("off_current_A") is None
