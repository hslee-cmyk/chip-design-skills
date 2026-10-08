"""단계 A(`pipeline.run_stage_a`) 9회로 통과 + S1v L 동치류가 sizing θ 스키마에 닿는 배선 확인 (U1 배선).

기대값 없이 불변량만 본다: 보고서 파일이 쓰이고, exit code 가 상태와 맞고(ok = 0, 그 밖 = 2 또는 로드 거부 7), 같은 입력이면 보고서 구조 표가 같고,
정지 사유가 `기록만` 코드이며, structure.json 이 없으면 declared 대조를 하지 않았다고 적힌다. 실 LUT 데이터가 없으면 FAIL(skip 아님).

[U1b 2026-10-09] 설계 40 3.2-3 rule_hash: 단계 A 의 사실 stale 판정 지문은 `structure_rule_fp()`(s1v_rule_fp 대신) -- 사실 파일은 그
지문으로 쓴다.
"""
import json
import os
from pathlib import Path

import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.graph import STATUS_DERIVED, build_s1, structure_rule_fp
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a
from gmid_engine.sizing import DcInputs, LutAccess, build_kernel_context

SKILL = Path(__file__).resolve().parents[3]
LIBRARY = SKILL / "assets" / "library"
CIRCUITS = sorted(p.name.removesuffix(".topology.json") for p in LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))


@pytest.fixture(scope="module")
def real_lut():
    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    manifest = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    mins = {}
    for entry in manifest["slices"]:
        kind = kinds[entry["device"]]
        mins[kind] = min(entry["w_um"] * 1e-6, mins.get(kind, float("inf")))
    grid = float(manifest.get("manufacturing_grid_m", 5e-9))
    spec = LutSpec(grid, tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX)
    return load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path)


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_stage_a_library_circuit(circuit, real_lut, tmp_path):
    topology = LIBRARY / (circuit + ".topology.json")
    first = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "a", supplies_v=_supplies(circuit))
    again = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "b", supplies_v=_supplies(circuit))
    assert first.report["tables"] == again.report["tables"]
    assert all(Path(p).is_file() for p in first.report_paths)
    assert json.loads(Path(first.report_paths[0]).read_text(encoding="utf-8"))["circuit"] == circuit
    assert first.exit_code == (0 if first.status == "ok" else 2)
    assert "not_performed" in first.report["declared_comparison"]
    if first.status == "ok":
        assert not first.report["stop_reasons"] and not first.report["review_needed"]
    assert first.report["count_budget"] > 0


def _supplies(circuit):
    raw = json.loads((LIBRARY / (circuit + ".topology.json")).read_text(encoding="utf-8"))
    declared = raw.get("_declared_target_spec", {}).get("supplies_v")
    return {k: v for k, v in declared.items() if not k.startswith("_")} if declared else {"vdd": 1.8, "gnd": 0.0}


def test_l_classes_reach_theta_schema(real_lut, tmp_path):
    circuit = "two_stage_ota"
    result = run_stage_a(LIBRARY / (circuit + ".topology.json"), None, real_lut, output_dir=tmp_path, supplies_v=_supplies(circuit))
    s1 = build_s1(load_topology(str(LIBRARY / (circuit + ".topology.json"))), _supplies(circuit))
    w_keys = {}
    for (kind, w_key) in sorted(real_lut.slice_map):
        w_keys.setdefault(kind, w_key)
    access = LutAccess(LutMemo(real_lut, point=4096, curve=4096, root=4096), tuple(sorted(w_keys.items())))
    inputs = DcInputs(tuple(sorted(_supplies(circuit).items())))
    plain = build_kernel_context(s1, inputs, access)
    tied = build_kernel_context(s1, inputs, access, l_classes=result.s1v.l_classes)
    expected = tuple(sorted((m, c.owner) for c in result.s1v.l_classes if c.status == STATUS_DERIVED for m in c.members if m != c.owner))
    assert plain.l_ties == ()
    assert tied.l_ties == expected and expected
    assert plain.schema.components == tied.schema.components


def _structure_file(path, topology_hash, rule_hash, stage_a, stage_b):
    facts = [{"concept": "stage_members", "subject": name, "value": value, "status": "ratified",
              "evidence": {"rule": "j_ratified", "nets": []}, "approval_id": "H1-test"}
             for name, value in (("stage_a", stage_a), ("stage_b", stage_b))]
    path.write_text(json.dumps({"schema_version": "1", "topology_hash": topology_hash, "rule_hash": rule_hash, "facts": facts}),
                    encoding="utf-8")


def test_structure_json_declared_comparison(real_lut, tmp_path):
    circuit = "two_stage_ota"
    topology = LIBRARY / (circuit + ".topology.json")
    s1 = build_s1(load_topology(str(topology)), _supplies(circuit))
    good, bad, stale = tmp_path / "g.json", tmp_path / "b.json", tmp_path / "s.json"
    _structure_file(good, s1.key.topology_fp, structure_rule_fp(), "M1 M2", "M6")
    _structure_file(bad, s1.key.topology_fp, structure_rule_fp(), "M1 M6", "M2")
    _structure_file(stale, "0" * 64, structure_rule_fp(), "M1 M2", "M6")
    kw = {"supplies_v": _supplies(circuit)}
    ok = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "o1", structure_path=good, **kw)
    assert ok.report["declared_comparison"] == "performed" and ok.status == "ok"
    mismatch = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "o2", structure_path=bad, **kw)
    assert mismatch.status == "review_needed" and any("declared_stage_mismatch" in r for r in mismatch.report["review_needed"])
    old = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "o3", structure_path=stale, **kw)
    assert old.status == "review_needed" and any("structure_fact_stale" in r for r in old.report["review_needed"])
    assert old.report["declared_comparison"].startswith("not_performed")
