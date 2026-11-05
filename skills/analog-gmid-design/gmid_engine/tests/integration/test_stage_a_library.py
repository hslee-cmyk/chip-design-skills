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
from gmid_engine.graph import S1V_KEY, STATUS_DERIVED, build_s1, structure_rule_fp
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a
from gmid_engine.search import open_run
from gmid_engine.sizing import KERNEL_KEY, DcInputs, LutAccess, build_kernel_context

# [XRUN-F1 card B C6·규칙 M M-c] run_stage_a 호출마다 같은 함수 본문의 `a, b = open_run()` 1:1(한 함수 두 번 이상이면 호출마다 자기 쌍).

# [xrun, 사용자 결정 J-1 2026-10-15] run_stage_a 는 PDK 선언·LUT 생성 규칙 선언과 두 선언 경로 인자를 받지 않는다(S0 키에만 쓰이던 인자 --
# 설계 40 v1.10 §2.4.3 'PDK 선언 경로 인자와 진입 sha 대조' 삭제, interface card C1). 옛 상수 PDK_DECL·LUT_RULE_DECL·두 경로를 지웠다.

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
    return load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path, bin_rule=loc.bin_rule_path)


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_stage_a_library_circuit(circuit, real_lut, tmp_path):
    topology = LIBRARY / (circuit + ".topology.json")
    d0, c0 = open_run()
    first = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "a", supplies_v=_supplies(circuit), donors=d0, counters=c0)
    d1, c1 = open_run()
    again = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "b", supplies_v=_supplies(circuit), donors=d1, counters=c1)
    assert first.report["tables"] == again.report["tables"]
    assert all(Path(p).is_file() for p in first.report_paths)
    assert json.loads(Path(first.report_paths[0]).read_text(encoding="utf-8"))["circuit"] == circuit
    assert first.exit_code == (0 if first.status == "ok" else 2)
    assert "not_performed" in first.report["declared_comparison"]
    if first.status == "ok":
        assert not first.report["stop_reasons"] and not first.report["review_needed"]
    assert first.report["count_budget"] > 0


def _supplies(circuit):
    """공급 전압 = 회로의 sizing_spec `human.supplies_v.values`(정본 하나). 기본값을 발명하지 않는다 -- 선언이 없으면 KeyError 로 이 회로만 실패한다."""
    raw = json.loads((LIBRARY / (circuit + ".sizing_spec.json")).read_text(encoding="utf-8"))
    return {k: float(v) for k, v in raw["human"]["supplies_v"]["values"].items()}


def test_l_classes_reach_theta_schema(real_lut, tmp_path):
    circuit = "two_stage_ota"
    donors, counters = open_run()
    result = run_stage_a(LIBRARY / (circuit + ".topology.json"), None, real_lut, output_dir=tmp_path, supplies_v=_supplies(circuit),
                         donors=donors, counters=counters)
    d_plain, c_plain = open_run()          # [card B C6] S1 만 있는 비교 쪽 = 다른 실행(build_s1·build_kernel_context 가 같은 쌍)
    s1 = build_s1(load_topology(str(LIBRARY / (circuit + ".topology.json"))), _supplies(circuit), donors=d_plain, counters=c_plain)
    w_keys = {}
    for (kind, w_key) in sorted(real_lut.slice_map):
        w_keys.setdefault(kind, w_key)
    access = LutAccess(LutMemo(real_lut, point=4096, curve=4096, root=4096), tuple(sorted(w_keys.items())))
    inputs = DcInputs(tuple(sorted(_supplies(circuit).items())))
    # [U17 ①-b] build_kernel_context(l_classes=) 삭제(설계 40 v1.9.1 §2.4.7·§2.4.8 커널 컨텍스트 구조 파생 행): L 동치류는 S1v 필드 graph/s1v: l_classes 에서
    # 읽는다 -> S1 만 있는 s1 이면 L 공유 없음, 단계 A 결과 S1Graph(S1v 필드 포함)면 L 공유. l_ties·θ 스키마는 graph/kernel 필드.
    plain = build_kernel_context(s1, inputs, access, donors=d_plain, counters=c_plain)
    tied = build_kernel_context(result.s1, inputs, access, donors=result.donors, counters=result.counters)
    l_classes = result.s1.value("graph", S1V_KEY, "l_classes")
    expected = tuple(sorted((m, c.owner) for c in l_classes if c.status == STATUS_DERIVED for m in c.members if m != c.owner))
    assert _kernel(plain, "l_ties") == ()
    assert _kernel(tied, "l_ties") == expected and expected
    # oracle (d) D-GB7a(40 §3.7·§11 U4): θ 는 동치류마다 주인 L 하나 -- 멤버 ("L", m) 성분만 빠지고 나머지·순서는 그대로.
    # 기대는 단계 A 의 l_classes(derived) 멤버에서 독립으로 센다(U1 시절 '성분 불변' 단언은 D-GB7a 와 모순이라 교체).
    members = {("L", m) for m, _ in expected}
    owners = {("L", o) for _, o in expected}
    assert members <= set(_kernel(plain, "theta_schema").components)
    assert _kernel(tied, "theta_schema").components == tuple(c for c in _kernel(plain, "theta_schema").components if c not in members)
    assert owners <= set(_kernel(tied, "theta_schema").components)


def _kernel(ctx, field):
    """[U17 ①-b] 커널 컨텍스트 구조 파생 = S0 수준 필드 graph/kernel(설계 40 v1.9.1 §2.4.8, D8)."""
    return ctx.base.value("graph", KERNEL_KEY, field)


def _structure_file(path, topology_hash, rule_hash, stage_a, stage_b):
    facts = [{"concept": "stage_members", "subject": name, "value": value, "status": "ratified",
              "evidence": {"rule": "j_ratified", "nets": []}, "approval_id": "H1-test"}
             for name, value in (("stage_a", stage_a), ("stage_b", stage_b))]
    path.write_text(json.dumps({"schema_version": "1", "topology_hash": topology_hash, "rule_hash": rule_hash, "facts": facts}),
                    encoding="utf-8")


def test_structure_json_declared_comparison(real_lut, tmp_path):
    circuit = "two_stage_ota"
    topology = LIBRARY / (circuit + ".topology.json")
    d_s1, c_s1 = open_run()                # [card B C6] 사실 파일 지문용 S1 = 따로 한 실행
    s1 = build_s1(load_topology(str(topology)), _supplies(circuit), donors=d_s1, counters=c_s1)
    good, bad, stale = tmp_path / "g.json", tmp_path / "b.json", tmp_path / "s.json"
    _structure_file(good, s1.key.topology_fp, structure_rule_fp(), "M1 M2", "M6")
    _structure_file(bad, s1.key.topology_fp, structure_rule_fp(), "M1 M6", "M2")
    _structure_file(stale, "0" * 64, structure_rule_fp(), "M1 M2", "M6")
    sup = _supplies(circuit)               # [규칙 M M-c] run_stage_a(**kw) 금지 -> 키워드를 풀어 쓴다
    d1, c1 = open_run()
    ok = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "o1", structure_path=good, supplies_v=sup, donors=d1, counters=c1)
    assert ok.report["declared_comparison"] == "performed" and ok.status == "ok"
    d2, c2 = open_run()
    mismatch = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "o2", structure_path=bad, supplies_v=sup,
                           donors=d2, counters=c2)
    assert mismatch.status == "review_needed" and any("declared_stage_mismatch" in r for r in mismatch.report["review_needed"])
    d3, c3 = open_run()
    old = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "o3", structure_path=stale, supplies_v=sup, donors=d3, counters=c3)
    assert old.status == "review_needed" and any("structure_fact_stale" in r for r in old.report["review_needed"])
    assert old.report["declared_comparison"].startswith("not_performed")
