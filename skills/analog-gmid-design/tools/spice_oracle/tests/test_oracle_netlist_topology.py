"""C15 topology 연결 동일성 -- oracle_netlist.py(meta) / oracle_run.py(compare, verdict).

기준: 손으로 쓴 픽스처 fixtures/tcs_nmos_rload.topology.json(conftest.cs_input 회로 + 이상 전류원 I1).
변형은 픽스처를 복사해 한 곳만 바꾼 topology 파일로 만든다. 기대값은 계약 문장(같아야 하는 것: 원소 이름 집합,
종류, 단자 넷 -- MOS 는 (d, g, s) 순서 + topology 가 선언한 bulk, R/C 순서 무관, 이상원 순서 그대로).
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from conftest import OFF_ZERO, ORACLE_DIR, cs_input, make_lut, require_spice, run_netlist, run_oracle, write_json

FIX = Path(__file__).resolve().parent / "fixtures" / "tcs_nmos_rload.topology.json"
REL = "skills/analog-gmid-design/tools/spice_oracle/tests/fixtures/tcs_nmos_rload.topology.json"
TOPO = json.loads(FIX.read_text(encoding="utf-8"))


def base_input(lut, topo_path=None, **kw):
    kw.setdefault("preds_devices", copy.deepcopy(OFF_ZERO))  # [C23 조정] 전도 문턱 0(옛 ID > 0 규칙) 명시
    inp = cs_input(lut, **kw)
    inp["sources"] = [{"name": "I1", "kind": "current", "terminals": ["vdd", "nout"], "value": 1e-7}]
    if topo_path is not None:
        inp["topology"] = {"path": str(topo_path)}
    return inp


def variant(tmp, mutate, name="topo.json"):
    t = copy.deepcopy(TOPO)
    mutate(t)
    return write_json(tmp / name, t)


def ti(meta):
    assert meta is not None and "topology_identity" in meta, meta
    return meta["topology_identity"]


@pytest.fixture
def lut(tmp_path):
    return make_lut(tmp_path / "lut.npz")


# ------------------------------------------------------------------ 일치
@pytest.mark.parametrize("bias", ["free", "forced"])
def test_repo_relative_path_verified(tmp_path, lut, bias):
    """저장소 상대 경로: 입력이 .git 없는 tmp 에 있으면 오라클 코드 폴더에서 위로 찾은 저장소 루트 기준."""
    inp = base_input(lut, REL, preds_nodes={"nout": 0.9, "pout": 0.16})
    p, text, meta = run_netlist(inp, tmp_path, bias)
    assert p.returncode == 0, (p.stdout + p.stderr)[-1500:]
    t = ti(meta)
    assert t["status"] == "verified", t
    assert t["diffs"] == [] and meta["blockers"] == []
    assert t["sha256_actual"] == hashlib.sha256(FIX.read_bytes()).hexdigest()
    exc = set(t["excluded_testbench"])
    assert {"Vrail_vdd", "Vrail_vsp", "Vbias_pb"} <= exc, exc
    assert "MP1" in t["bulk_compared"] and "M1" not in t["bulk_compared"]


def test_repo_root_from_input_folder_git(tmp_path, lut):
    """입력 폴더 위에 .git 이 있으면 그 폴더가 루트. 같은 상대 문자열이 그 루트 아래 파일로 풀린다."""
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    rel = "topo/x.topology.json"
    (root / "topo").mkdir()
    (root / rel).write_bytes(FIX.read_bytes())
    work = root / "work" / "deep"
    work.mkdir(parents=True)
    p, text, meta = run_netlist(base_input(lut, rel), work)
    assert ti(meta)["status"] == "verified", ti(meta)
    # 같은 상대 경로가 오라클 저장소 루트에는 없다 -> 루트가 정말 입력 쪽에서 잡혔다
    assert not (ORACLE_DIR.parents[3] / rel).exists()


def test_cli_topology_overrides_input_path(tmp_path, lut):
    bad = variant(tmp_path, lambda t: t["netlist"][0].update(gate="nout"))
    inp = base_input(lut, bad)
    p, text, meta = run_netlist(inp, tmp_path, extra=["--topology", FIX])
    assert ti(meta)["status"] == "verified"


def test_resistor_order_free_source_order_matters(tmp_path, lut):
    ok = variant(tmp_path, lambda t: t["passive_elements"][0].update(terminals=["nout", "vdd"]), "ok.json")
    p, text, meta = run_netlist(base_input(lut, ok), tmp_path / "a")
    assert ti(meta)["status"] == "verified", ti(meta)["diffs"]
    rev = variant(tmp_path, lambda t: t["ideal_sources"][0].update(terminals=["nout", "vdd"]), "rev.json")
    p, text, meta = run_netlist(base_input(lut, rev), tmp_path / "b")
    assert ti(meta)["status"] == "mismatch" and meta["blockers"]


# ------------------------------------------------------------------ 불일치 -> 막힘
MUTATIONS = {
    "gate_net_changed": lambda t: t["netlist"][0].update(gate="nout"),
    "drain_source_swapped": lambda t: t["netlist"][0].update(drain="gnd", source="nout"),
    "bulk_declared_wrong": lambda t: t["netlist"][1].update(bulk="vsp"),
    "kind_changed": lambda t: t["netlist"][0].update(kind="pmos"),
    "passive_kind_changed": lambda t: t["passive_elements"][1].update(kind="resistor"),
    "topology_has_extra_element": lambda t: t["passive_elements"].append(
        {"name": "Cx", "kind": "capacitor", "terminals": ["nout", "gnd"]}),
    "topology_missing_element": lambda t: t["passive_elements"].pop(2),
    "topology_missing_device": lambda t: t["netlist"].pop(1),
    "passive_net_changed": lambda t: t["passive_elements"][2].update(terminals=["pout", "vdd"]),
}


@pytest.mark.parametrize("case", sorted(MUTATIONS))
def test_mismatch_blocks(tmp_path, lut, case):
    tp = variant(tmp_path, MUTATIONS[case])
    p, text, meta = run_netlist(base_input(lut, tp), tmp_path)
    t = ti(meta)
    assert t["status"] == "mismatch" and t["diffs"], (case, t)
    assert meta["blockers"], case


def test_input_extra_element_blocks(tmp_path, lut):
    inp = base_input(lut, FIX)
    inp["passives"].append({"name": "Rx", "kind": "resistor", "terminals": ["nout", "gnd"], "value": 1e6})
    p, text, meta = run_netlist(inp, tmp_path)
    assert ti(meta)["status"] == "mismatch" and meta["blockers"]
    assert any("Rx" in json.dumps(d, ensure_ascii=False) for d in ti(meta)["diffs"])


def test_mismatch_blocked_in_run(tmp_path, lut):
    require_spice()
    tp = variant(tmp_path, MUTATIONS["gate_net_changed"])
    p, res = run_oracle(base_input(lut, tp), tmp_path / "o", sat_margin=0.05)
    r = res["free"]
    assert r["summary"]["verdict"] == "BLOCKED" and p.returncode == 2
    assert r["summary"]["topology_identity"]["status"] == "mismatch"
    assert r["summary"]["topology_identity"]["diff_count"] >= 1


# ------------------------------------------------------------------ not_in_topology_reason
def test_not_in_topology_reason_excluded(tmp_path, lut):
    inp = base_input(lut, FIX)
    inp["passives"].append({"name": "CLOAD", "kind": "capacitor", "terminals": ["nout", "gnd"], "value": 1e-12,
                            "not_in_topology_reason": "spec 부하"})
    p, text, meta = run_netlist(inp, tmp_path)
    t = ti(meta)
    assert t["status"] == "verified", t["diffs"]
    assert "CLOAD" in json.dumps(t["declared_not_in_topology"], ensure_ascii=False)
    assert "spec 부하" in json.dumps(t["declared_not_in_topology"], ensure_ascii=False)


def test_reason_on_element_that_topology_has_is_a_diff(tmp_path, lut):
    inp = base_input(lut, FIX)
    inp["passives"][2]["not_in_topology_reason"] = "잘못 단 이유"   # RP 는 topology 에 있다
    p, text, meta = run_netlist(inp, tmp_path)
    assert ti(meta)["status"] == "mismatch" and meta["blockers"]


# ------------------------------------------------------------------ unverified / required
def test_no_topology_unverified_not_blocking(tmp_path, lut):
    require_spice()
    p, res = run_oracle(base_input(lut), tmp_path / "o", sat_margin=0.05)
    r = res["free"]
    assert r["topology_identity"]["status"] == "unverified"
    assert r["summary"]["topology_identity"]["required"] is False
    assert r["blockers"] == [] and r["summary"]["verdict"] == "PASS" and p.returncode == 0


def test_missing_file_unverified(tmp_path, lut):
    p, text, meta = run_netlist(base_input(lut, "no/such/file.topology.json"), tmp_path)
    assert ti(meta)["status"] == "unverified" and meta["blockers"] == []


@pytest.mark.parametrize("how", ["none", "missing_file"])
def test_require_topology_blocks_unverified(tmp_path, lut, how):
    inp = base_input(lut, None if how == "none" else "no/such/file.topology.json")
    p, text, meta = run_netlist(inp, tmp_path, extra=["--require-topology"])
    assert ti(meta)["status"] == "unverified" and ti(meta)["required"] is True
    assert meta["blockers"]
    require_spice()
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=0.05, extra=["--require-topology"])
    assert res["free"]["summary"]["verdict"] == "BLOCKED" and p.returncode == 2


def test_require_topology_verified_passes(tmp_path, lut):
    require_spice()
    p, res = run_oracle(base_input(lut, REL), tmp_path / "o", sat_margin=0.05, extra=["--require-topology"])
    r = res["free"]
    assert r["summary"]["topology_identity"] == {**r["summary"]["topology_identity"], "status": "verified",
                                                  "required": True, "diff_count": 0}
    assert r["summary"]["verdict"] == "PASS" and p.returncode == 0


# ------------------------------------------------------------------ sha256
def test_sha256_mismatch_noted_only(tmp_path, lut):
    inp = base_input(lut, REL)
    inp["topology"]["sha256"] = "0" * 64
    p, text, meta = run_netlist(inp, tmp_path)
    t = ti(meta)
    assert t["status"] == "verified" and meta["blockers"] == []
    assert t["sha256_declared"] == "0" * 64
    assert t["sha256_actual"] == hashlib.sha256(FIX.read_bytes()).hexdigest()
    assert any("sha256" in str(n) for n in t["notes"] + meta["notes"]), (t["notes"], meta["notes"])


def test_sha256_match_no_note(tmp_path, lut):
    inp = base_input(lut, REL)
    inp["topology"]["sha256"] = hashlib.sha256(FIX.read_bytes()).hexdigest()
    p, text, meta = run_netlist(inp, tmp_path)
    t = ti(meta)
    assert t["status"] == "verified"
    assert not any("sha256" in str(n) for n in t["notes"]), t["notes"]


# ------------------------------------------------------------------ iso / Z1
def test_iso_not_applicable(tmp_path, lut):
    inp = base_input(lut, REL)
    for kind, pol in (("nmos", "n"), ("pmos", "p")):
        inp["process"]["models"][kind]["polarity"] = pol
    inp["predictions"]["devices"] = {"M1": {"VGS": 0.7, "VDS": 0.9, "VSB": 0.0}}
    p, text, meta = run_netlist(inp, tmp_path, "iso")
    assert ti(meta)["status"] == "not_applicable"


def test_z1_compares_unmodified_netlist(tmp_path, lut):
    """C15: Z1 실행은 변경 전 넷리스트로 비교 -> RP 를 빼고 CL 을 단락해도 verified."""
    p, text, meta = run_netlist(base_input(lut, REL), tmp_path, extra=["--omit", "RP", "--short", "CL"])
    assert p.returncode == 0, (p.stdout + p.stderr)[-800:]
    assert ti(meta)["status"] == "verified", ti(meta)["diffs"]


# ------------------------------------------------------------------ [신규 Q6] C6/C15: bias_voltages 넷 집합 == topology bias_inputs
# 근거: README C6 [신규 Q6] "bias_voltages 의 넷 집합은 topology bias_inputs(키가 있을 때만 대조)와 같아야 한다. 다르면 C15
# diffs 에 들어가 막힘". oracle (a): 픽스처 topology 의 bias_inputs 는 손으로 확인한 gate 전용 넷 {pb}(MP1 gate 에만 물림;
# nin 은 오라클 입력 포트라 C6 게이트 전용 넷이 아니다). 입력 bias_voltages 기본 = [pb](conftest.cs_input).
# 값이 빠진 경우 C6 막힘과 섞이지 않게 predictions.nodes 에 pb 값을 준다.
PB_NODES = {"nout": 0.9, "pout": 0.16, "pb": 0.3}


def _diff_text(t):
    return json.dumps(t["diffs"], ensure_ascii=False)


def test_fixture_bias_inputs_is_hand_derived_gate_only_set():
    """픽스처 선언이 손 계산과 맞는다: MOS gate 넷 - (d/s/bulk ∪ 2단자 terminals ∪ 오라클 입력 포트 nin)."""
    gates = {e["gate"] for e in TOPO["netlist"]}
    other = {n for e in TOPO["netlist"] for n in (e["drain"], e["source"], e.get("bulk")) if n}
    other |= {n for k in ("passive_elements", "ideal_sources") for e in TOPO.get(k, []) for n in e["terminals"]}
    other |= {"nin"}                                    # cs_input ports.input
    assert sorted(gates - other) == TOPO["bias_inputs"] == ["pb"]


@pytest.mark.parametrize("bias", ["free", "forced"])
def test_bias_voltages_equal_bias_inputs_verified(tmp_path, lut, bias):
    p, text, meta = run_netlist(base_input(lut, FIX, preds_nodes=PB_NODES), tmp_path, bias)
    t = ti(meta)
    assert t["status"] == "verified", t["diffs"]
    assert meta["blockers"] == []


@pytest.mark.parametrize("bias_voltages", [None, []], ids=["key_absent", "empty_list"])
def test_bias_voltages_missing_declared_net_blocks(tmp_path, lut, bias_voltages):
    """topology bias_inputs {pb} 인데 입력 bias_voltages 에 pb 가 없다(키 없음/빈 list) -> C15 mismatch, diff 에 pb."""
    inp = base_input(lut, FIX, preds_nodes=PB_NODES, bias_voltages=bias_voltages)
    p, text, meta = run_netlist(inp, tmp_path)
    t = ti(meta)
    assert t["status"] == "mismatch", t
    assert "pb" in _diff_text(t)
    assert meta["blockers"]


def test_bias_voltages_extra_net_blocks(tmp_path, lut):
    """topology bias_inputs 가 빈 list(키는 있음)인데 입력이 pb 를 선언 -> 남는 넷 pb 가 diff."""
    tp = variant(tmp_path, lambda t: t.update(bias_inputs=[]))
    p, text, meta = run_netlist(base_input(lut, tp, preds_nodes=PB_NODES), tmp_path)
    t = ti(meta)
    assert t["status"] == "mismatch", t
    assert "pb" in _diff_text(t)
    assert meta["blockers"]


def test_bias_inputs_net_missing_from_input_named_in_diff(tmp_path, lut):
    """topology 가 넷 하나(nzz)를 더 선언 -> 입력 bias_voltages 에 없는 그 넷이 diff."""
    tp = variant(tmp_path, lambda t: t.update(bias_inputs=["nzz", "pb"]))
    p, text, meta = run_netlist(base_input(lut, tp, preds_nodes=PB_NODES), tmp_path)
    t = ti(meta)
    assert t["status"] == "mismatch", t
    assert "nzz" in _diff_text(t)
    assert meta["blockers"]


def test_bias_inputs_key_absent_strict_mismatch(tmp_path, lut):
    """README C6(78ebbbd 엄격): topology 에 bias_inputs 키가 없으면 빈 집합과 대조 -> 입력 bias_voltages {pb} 는 남는 넷."""
    tp = variant(tmp_path, lambda t: t.pop("bias_inputs"))
    p, text, meta = run_netlist(base_input(lut, tp, preds_nodes=PB_NODES), tmp_path)
    t = ti(meta)
    assert t["status"] == "mismatch", t
    assert "pb" in _diff_text(t)
    assert meta["blockers"]


@pytest.mark.parametrize("bias_voltages", [None, []], ids=["input_key_absent", "input_empty_list"])
def test_bias_inputs_key_absent_and_no_bias_voltages_verified(tmp_path, lut, bias_voltages):
    """키 없음(빈 집합) + 입력 bias_voltages 없음/[] -> 같은 빈 집합이라 verified (pb 값은 predictions.nodes 로 C6 통과)."""
    tp = variant(tmp_path, lambda t: t.pop("bias_inputs"))
    p, text, meta = run_netlist(base_input(lut, tp, preds_nodes=PB_NODES, bias_voltages=bias_voltages), tmp_path)
    assert ti(meta)["status"] == "verified", ti(meta)["diffs"]


def test_bias_mismatch_blocked_in_run(tmp_path, lut):
    require_spice()
    tp = variant(tmp_path, lambda t: t.update(bias_inputs=[]))
    p, res = run_oracle(base_input(lut, tp, preds_nodes=PB_NODES), tmp_path / "o", sat_margin=0.05)
    r = res["free"]
    assert r["summary"]["verdict"] == "BLOCKED" and p.returncode == 2
    assert r["summary"]["topology_identity"]["status"] == "mismatch"
    assert r["summary"]["topology_identity"]["diff_count"] >= 1
