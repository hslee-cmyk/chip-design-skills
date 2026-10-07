"""oracle_run.py -- 끝단 실행: C8 반환 코드, BLOCKED 우선순위, 산출물 이름(--tag), 결정론(같은 입력 두 번 = 같은 출력),
C1(엔진 import 없음), C11(테스트벤치 값 숫자 기본값 없음).
"""
import ast
import copy
import filecmp

import pytest

from conftest import (CS, ORACLE_DIR, cs_input, make_lut, run_netlist, run_oracle, require_spice, stem_of)


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
    """C2: npz 에 temp_c 가 없으면 막힘 -> BLOCKED(반환 2). (계약 문장 그대로)"""
    inp = cs_input(make_lut(tmp_path / "lut.npz", temp_c=None))
    p, res = run_oracle(inp, tmp_path / "o")
    r = res["free"]
    assert r is not None, f"비교표 없음 rc={p.returncode}\n{(p.stdout + p.stderr)[-800:]}"
    assert r["blockers"] and r["summary"]["verdict"] == "BLOCKED" and p.returncode == 2


@pytest.mark.acceptance_change_pending
def test_pending_accept_c8_fail_beats_blocked_returns_1(tmp_path):
    """[합격 정의 변경 예정(2026-10-07 확정)] FAIL 이 하나라도 있으면 막힘이 있어도 FAIL(반환 1).
    FAIL 원천은 시뮬레이션과 무관한 W_rel(선언 W 2 um vs finger 곱 4 um, 허용오차 1 %) -- 현재 계약의 W 판정."""
    inp = cs_input(make_lut(tmp_path / "lut.npz", corner=None), W=2e-6, judge={"tolerances": {"W_rel": 0.01}})
    p, res = run_oracle(inp, tmp_path / "o")
    r = res["free"]
    assert r["blockers"]
    assert r["summary"]["verdict"] == "FAIL" and p.returncode == 1


@pytest.mark.acceptance_change_pending
def test_pending_accept_c8_worst_bias_decides_return_code(tmp_path):
    """[합격 정의 변경 예정(2026-10-07 확정)] free 는 INCOMPLETE(노드 허용오차 없음), forced 는 KCL 허용오차 FAIL
    (nout 을 자기일관적이지 않은 0.8 V 로 고정) -> 최악 = FAIL -> 반환 1."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": 0.8, "pout": 0.2},
                   judge={"tolerances": {"kcl_abs_A": 1e-8}})
    p, res = run_oracle(inp, tmp_path / "o", biases=("free", "forced"))
    assert res["free"]["summary"]["verdict"] == "INCOMPLETE"
    assert res["forced"]["summary"]["verdict"] == "FAIL"
    assert p.returncode == 1


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
@pytest.mark.parametrize("key", ["input_ac", "fstop_hz", "points_per_decade"])
def test_c11_no_default_for_missing_testbench_value(tmp_path, key):
    """테스트벤치 숫자를 빼면 오라클이 지어낸 값으로 넷리스트를 만들지 않는다(거부 또는 막힘)."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"))
    del inp["testbench"]["ac"][key]
    p, text, meta = run_netlist(inp, tmp_path)
    assert p.returncode != 0 or (meta is not None and meta["blockers"]), (
        f"{key} 없음인데 넷리스트를 만들었다:\n" + "\n".join(
            ln for ln in (text or "").splitlines() if ln.lower().startswith(("vac", "ac "))))


def test_c11_no_default_sat_margin_or_tolerance(tmp_path):
    """판정 설정이 없으면 포화 여유·허용오차가 숫자 기본값으로 채워지지 않는다(judge_config 가 비어 있음)."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"))
    p, res = run_oracle(inp, tmp_path / "o")
    jc = res["free"]["judge_config"]
    assert not jc.get("tolerances") and jc.get("sat_margin_V") is None and jc.get("off_current_A") is None
