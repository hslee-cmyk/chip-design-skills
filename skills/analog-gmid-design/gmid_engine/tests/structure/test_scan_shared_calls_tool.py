"""GL-1 공유 호출 감사 도구 `tools/audit/scan_shared_calls.py`: 표본 toy 9종, 종료 코드 2 입력, 바이트 동일.

oracle 종류 (a) 구성으로 정답이 정해진 합성 입력: 픽스처 fixtures/shared_calls/<case>/gmid_engine 은 같은 인자를 넘기는지·
다른 필드를 넘기는지·재수출·지역 추적을 구성으로 정했고 기대 class 는 interface card 20261103-gl1 §4 표(사용자 선언)에 있다.
기대 줄 번호·인자 키·호출 수는 픽스처 소스를 손으로 읽어 적었다. 도구는 프로세스로만 부른다(subprocess).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
TOOL = ROOT / "tools" / "audit" / "scan_shared_calls.py"
OUTPUTS = ("calls.json", "shared.tsv", "b_candidates.tsv", "limits.json")
SHARED_HEADER = "callee_mod\tcallee\tn_caller_mods\tn_sites\tcaller_mods"
B_HEADER = "callee_mod\tcallee\tclass\tn_sites\tpairs_b\tpairs_not_b\tpairs_d"
CASES = ("same_input", "diff_input", "local_trace", "helper_trace", "reexport",
         "param_only", "one_caller", "method", "touching")
FIELD = "F[device.dc_op]"


def run_tool(engine, out, *touching, seed="0"):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = str(seed)
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, str(TOOL), "--engine", str(engine), "--out", str(out)]
    if touching:
        cmd += ["--touching"] + list(touching)
    return subprocess.run(cmd, cwd=str(out.parent), env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def read_tsv(path):
    raw = path.read_bytes()
    assert b"\r" not in raw
    text = raw.decode("utf-8")
    assert text == "" or text.endswith("\n")
    return text.splitlines()


def load(out):
    calls = json.loads((out / "calls.json").read_text(encoding="utf-8"))
    return {
        "calls": calls,
        "shared": read_tsv(out / "shared.tsv"),
        "cand": read_tsv(out / "b_candidates.tsv"),
        "limits": json.loads((out / "limits.json").read_text(encoding="utf-8")),
    }


def rows(lines, header):
    assert lines[0] == header, lines[:1]
    return [dict(zip(header.split("\t"), ln.split("\t"))) for ln in lines[1:]]


@pytest.fixture
def case_run(fixture_tree, tmp_path):
    def go(case, *touching):
        out = tmp_path / ("out_" + case)
        r = run_tool(fixture_tree("shared_calls", case), out, *touching)
        assert r.returncode == 0, r.stdout + r.stderr
        return load(out)
    return go


def test_tool_exists():
    assert TOOL.is_file(), TOOL


def test_outputs_exist_and_calls_json_keys(case_run):
    d = case_run("same_input")
    assert isinstance(d["calls"], list) and d["calls"]
    keys = {"callee_mod", "callee", "caller_mod", "caller_fn", "line", "text", "arg_keys", "leaves"}
    for c in d["calls"]:
        assert set(c) == keys
    sort_key = [(c["callee_mod"], c["callee"], c["caller_mod"], c["line"]) for c in d["calls"]]
    assert sort_key == sorted(sort_key)
    assert set(d["limits"]) == {"method_calls_unresolved", "sites_with_param_leaf"}


def _f_sites(d):
    return [c for c in d["calls"] if c["callee"] == "f"]


def test_same_input_is_B(case_run):
    d = case_run("same_input")
    sites = _f_sites(d)
    assert len(sites) == 2
    assert len({c["callee_mod"] for c in sites}) == 1
    assert sites[0]["callee_mod"].endswith("defs")
    assert len({c["caller_mod"] for c in sites}) == 2
    assert [c["line"] for c in sites] == [5, 5]
    assert sorted(c["caller_fn"] for c in sites) == ["run_a", "run_b"]
    for c in sites:
        assert c["arg_keys"] == [FIELD]
        assert any(FIELD == str(x) for x in c["leaves"]), c["leaves"]
    sh = rows(d["shared"], SHARED_HEADER)
    assert len(sh) == 1
    assert (sh[0]["callee"], sh[0]["n_caller_mods"], sh[0]["n_sites"]) == ("f", "2", "2")
    for c in sites:
        assert c["caller_mod"] in sh[0]["caller_mods"]
    cand = rows(d["cand"], B_HEADER)
    assert len(cand) == 1
    c = cand[0]
    assert (c["callee"], c["class"], c["n_sites"], c["pairs_b"], c["pairs_not_b"], c["pairs_d"]) == \
        ("f", "B", "2", "1", "0", "0")
    assert d["limits"]["sites_with_param_leaf"] == 0


def test_diff_input_is_not_B(case_run):
    d = case_run("diff_input")
    sites = sorted(_f_sites(d), key=lambda c: c["caller_fn"])
    assert [c["arg_keys"] for c in sites] == [[FIELD], ["F[device.ss_dev]"]]
    cand = rows(d["cand"], B_HEADER)
    assert len(cand) == 1
    c = cand[0]
    assert (c["callee"], c["class"], c["pairs_b"], c["pairs_not_b"], c["pairs_d"]) == ("f", "not_B", "0", "1", "0")


def test_local_trace_is_B(case_run):
    d = case_run("local_trace")
    by_fn = {c["caller_fn"]: c for c in _f_sites(d)}
    assert set(by_fn) == {"run_a", "run_b"}
    assert by_fn["run_a"]["line"] == 6          # f(v) 는 a.py 6 줄
    assert by_fn["run_b"]["line"] == 5
    assert by_fn["run_a"]["arg_keys"] == [FIELD]      # v 를 대입 식으로 치환
    assert by_fn["run_b"]["arg_keys"] == [FIELD]
    cand = rows(d["cand"], B_HEADER)
    assert [(c["callee"], c["class"], c["pairs_b"]) for c in cand] == [("f", "B", "1")]


def test_helper_trace_is_B(case_run):
    d = case_run("helper_trace")
    by_fn = {c["caller_fn"]: c for c in _f_sites(d)}
    assert set(by_fn) == {"_row", "run_b"}
    assert by_fn["_row"]["line"] == 5            # a.py 5 줄 f(x) 의 x 를 같은 모듈 호출자의 인자로 치환
    assert by_fn["_row"]["arg_keys"] == [FIELD]
    assert by_fn["run_b"]["arg_keys"] == [FIELD]
    cand = rows(d["cand"], B_HEADER)
    assert [(c["callee"], c["class"], c["pairs_b"], c["pairs_d"]) for c in cand] == [("f", "B", "1", "0")]


def test_reexport_resolves_to_defining_module(case_run):
    d = case_run("reexport")
    sites = _f_sites(d)
    assert len(sites) == 2
    mods = {c["callee_mod"] for c in sites}
    assert len(mods) == 1
    mod = mods.pop()
    assert "defs" in mod                          # 정의 파일 pkg/defs.py
    assert not mod.endswith("pkg")                # 재수출 패키지 pkg/__init__.py 가 아님
    sh = rows(d["shared"], SHARED_HEADER)
    assert [(r["callee"], r["n_caller_mods"], r["n_sites"]) for r in sh] == [("f", "2", "2")]
    assert sh[0]["callee_mod"] == mod
    cand = rows(d["cand"], B_HEADER)
    assert [(c["callee"], c["class"], c["pairs_b"]) for c in cand] == [("f", "B", "1")]
    assert cand[0]["callee_mod"] == mod


def test_param_only_is_D(case_run):
    d = case_run("param_only")
    sites = _f_sites(d)
    assert len(sites) == 2
    for c in sites:
        assert c["arg_keys"] == ["P[x]"]
        assert c["line"] == 5
    cand = rows(d["cand"], B_HEADER)
    assert [(c["callee"], c["class"], c["pairs_b"], c["pairs_not_b"], c["pairs_d"]) for c in cand] == \
        [("f", "D", "0", "0", "1")]
    assert d["limits"]["sites_with_param_leaf"] == 2


def test_one_caller_not_listed(case_run):
    d = case_run("one_caller")
    assert d["shared"] == [SHARED_HEADER]
    assert d["cand"] == [B_HEADER]


def test_method_calls_are_not_sites(case_run):
    d = case_run("method")
    assert d["calls"] == []
    assert d["shared"] == [SHARED_HEADER]
    assert d["cand"] == [B_HEADER]
    assert d["limits"]["method_calls_unresolved"] == 4         # obj.f(1), obj.f(2), obj.f(3), obj.f(4)


def test_touching_filters_candidates(case_run):
    both = rows(case_run("touching")["cand"], B_HEADER)
    assert sorted((c["callee"], c["class"], c["n_sites"], c["pairs_b"], c["pairs_not_b"], c["pairs_d"])
                  for c in both) == [("f", "B", "2", "1", "0", "0"), ("h", "not_B", "2", "0", "1", "0")]
    # shared.tsv 는 touching 으로 줄지 않는다(두 callee 모두 호출 모듈 2)
    assert sorted(r["callee"] for r in rows(case_run("touching")["shared"], SHARED_HEADER)) == ["f", "h"]
    only_a = rows(case_run("touching", "a.py")["cand"], B_HEADER)
    assert [c["callee"] for c in only_a] == ["f"]
    only_c = rows(case_run("touching", "c.py")["cand"], B_HEADER)
    assert [c["callee"] for c in only_c] == ["h"]
    via_b = rows(case_run("touching", "b.py")["cand"], B_HEADER)
    assert sorted(c["callee"] for c in via_b) == ["f", "h"]
    two = rows(case_run("touching", "a.py", "c.py")["cand"], B_HEADER)
    assert sorted(c["callee"] for c in two) == ["f", "h"]


def test_tool_does_not_execute_target(fixture_tree, tmp_path):
    eng = tmp_path / "gmid_engine"
    shutil.copytree(fixture_tree("shared_calls", "same_input"), eng)
    for name in ("defs.py", "a.py", "b.py"):
        p = eng / name
        p.write_bytes(p.read_bytes() + b"\nraise SystemExit(99)\n")
    r = run_tool(eng, tmp_path / "out")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "out" / "calls.json").is_file()


def test_out_dir_is_created(fixture_tree, tmp_path):
    out = tmp_path / "new_out_dir"
    assert not out.exists()
    r = run_tool(fixture_tree("shared_calls", "same_input"), out)
    assert r.returncode == 0, r.stdout + r.stderr
    assert all((out / n).is_file() for n in OUTPUTS)


# ---------------------------------------------------------------- 종료 코드 2

def _expect_input_error(r, out):
    # 도구가 없을 때 인터프리터도 종료 코드 2를 내므로, 도구 존재와 인터프리터 오류가 아님을 먼저 확인한다
    assert TOOL.is_file(), TOOL
    assert "can't open file" not in r.stderr, r.stderr
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert not (out / "b_candidates.tsv").exists()


def test_exit2_engine_dir_missing(tmp_path):
    out = tmp_path / "out"
    _expect_input_error(run_tool(tmp_path / "gmid_engine", out), out)


def test_exit2_engine_dir_wrong_name(fixture_tree, tmp_path):
    other = tmp_path / "other_name"
    shutil.copytree(fixture_tree("shared_calls", "same_input"), other)
    out = tmp_path / "out"
    _expect_input_error(run_tool(other, out), out)


def test_exit2_no_py_files(tmp_path):
    eng = tmp_path / "gmid_engine"
    eng.mkdir()
    (eng / "note.txt").write_text("no python here\n", encoding="utf-8")
    out = tmp_path / "out"
    _expect_input_error(run_tool(eng, out), out)


def test_exit2_syntax_error_file(fixture_tree, tmp_path):
    eng = tmp_path / "gmid_engine"
    shutil.copytree(fixture_tree("shared_calls", "same_input"), eng)
    (eng / "broken.py").write_text("def (:\n", encoding="utf-8")
    out = tmp_path / "out"
    _expect_input_error(run_tool(eng, out), out)


def test_exit2_touching_path_not_in_targets(fixture_tree, tmp_path):
    out = tmp_path / "out"
    r = run_tool(fixture_tree("shared_calls", "touching"), out, "no_such_file.py")
    _expect_input_error(r, out)


def test_exit2_one_missing_touching_among_valid(fixture_tree, tmp_path):
    out = tmp_path / "out"
    r = run_tool(fixture_tree("shared_calls", "touching"), out, "a.py", "no_such_file.py")
    _expect_input_error(r, out)


# ---------------------------------------------------------------- 결정성

@pytest.mark.parametrize("case", CASES)
def test_outputs_byte_identical_across_hashseed_and_out(case, fixture_tree, tmp_path):
    eng = fixture_tree("shared_calls", case)
    o1, o2 = tmp_path / "o1", tmp_path / "o2"
    r1 = run_tool(eng, o1, seed="1")
    r2 = run_tool(eng, o2, seed="4242")
    assert r1.returncode == 0, r1.stdout + r1.stderr
    assert r2.returncode == 0, r2.stdout + r2.stderr
    for name in OUTPUTS:
        b1, b2 = (o1 / name).read_bytes(), (o2 / name).read_bytes()
        assert b1 == b2, name
        assert b"\r" not in b1, name
        text = b1.decode("utf-8")
        assert not re.search(r"[A-Za-z]:[\\/]", text), (name, "절대 경로")
        for forbidden in (str(tmp_path), tmp_path.as_posix(), str(eng), eng.as_posix(), str(ROOT), ROOT.as_posix()):
            assert forbidden not in text, (name, forbidden)


def test_touching_outputs_byte_identical(fixture_tree, tmp_path):
    eng = fixture_tree("shared_calls", "touching")
    o1, o2 = tmp_path / "o1", tmp_path / "o2"
    assert run_tool(eng, o1, "b.py", "a.py", seed="7").returncode == 0
    assert run_tool(eng, o2, "a.py", "b.py", seed="99").returncode == 0
    for name in OUTPUTS:
        assert (o1 / name).read_bytes() == (o2 / name).read_bytes(), name
