"""B-T17 [XRUN-F1 card B C6·C1·C9] 두 실행(두 `open_run()` 쌍)은 아무것도 나누지 않는다.

한 test 안에서 같은 library 회로를 `run_stage_a` 로 두 번 돌린다 -- 호출마다 바로 앞에서 자기 `open_run()`(규칙 M M-c 꼴: 튜플 풀기,
그 이름은 그 호출 하나에만).
oracle (비교)·(식):
- interface card C6 '두 실행은 아무것도 나누지 않는다: 두 번째 실행의 S0 수준 블록 행도 computes 1, 첫 실행 계수 불변'.
- S0 수준 블록 = 단계 A 결과의 S0 수준 스냅샷(`StageAResult.s1.snapshot`, 설계 40 §2.4.7 '단계 결과는 S0 수준 스냅샷 참조만')에 필드를 쓴 writer
  전부 -- test 가 스냅샷 필드의 writer 를 직접 모은다(피검 계수를 읽지 않는 목록).
- C1 행 항등식 calls = reuses + grafts + replays + computes, 같은 입력 재계산 0.
- 첫 실행 계수 불변 = 두 번째 실행 전에 뜬 `counters.snapshot()`(C1: 그 뒤 기록에 따라 바뀌지 않는 불변 값)과 두 번째 실행 뒤 다시 뜬 snapshot 이 같고,
  첫 실행 색인 `entry_count()` 도 같다. 두 실행의 두 객체는 서로 다른 객체(`is not`).
실 LUT 데이터가 없으면 FAIL(skip 아님).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gmid_engine.lut import LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a
from gmid_engine.search import open_run

SKILL = Path(__file__).resolve().parents[3]
LIBRARY = SKILL / "assets" / "library"
CIRCUIT = "common_gate_amplifier"          # 단계 A ok 회로(tests/integration/test_s0_layer_9circuits.py 기준선 status [ok, ok]) -- 입력 선택
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
COUNT_FIELDS = ("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input")


@pytest.fixture(scope="module")
def real_lut():
    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX)
    return load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path)


def _supplies():
    raw = json.loads((LIBRARY / (CIRCUIT + ".topology.json")).read_text(encoding="utf-8"))
    declared = raw.get("_declared_target_spec", {}).get("supplies_v")
    return {k: v for k, v in declared.items() if not k.startswith("_")} if declared else {"vdd": 1.8, "gnd": 0.0}


def _writers(snapshot):
    """S0 수준 스냅샷의 필드 writer 가운데 계산 블록(스냅샷 `block_versions` 에 있는 것 -- test_s0_layer_9circuits 와 같은 '계산 블록' 판정)
    전부. test 가 스냅샷을 직접 읽는다."""
    out = set()
    for kind in snapshot.kinds():
        for key in snapshot.keys(kind):
            rec = snapshot.record(kind, key)
            out.update(rec.get(name).writer for name in rec.field_names())
    return sorted(w for w in out if w in snapshot.block_versions)


def _rows(counters):
    """{block: {칸: 값}} -- (block, "*") 행(card B: part 는 늘 "*")."""
    out = {}
    for r in counters.snapshot().blocks:
        assert r.part == "*", (r.block, r.part)
        out[r.block] = {f: getattr(r, f) for f in COUNT_FIELDS}
    return out


def test_second_run_recomputes_s0_blocks_and_first_run_counters_unchanged(real_lut, tmp_path):
    topology = LIBRARY / (CIRCUIT + ".topology.json")
    d1, c1 = open_run()
    first = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "a", supplies_v=_supplies(), donors=d1, counters=c1)
    assert (first.exit_code, first.status) == (0, "ok"), first.report["stop_reasons"] + first.report["review_needed"]   # 전제
    before = first.counters.snapshot()
    entries_before = first.donors.entry_count()
    writers = _writers(first.s1.snapshot)
    assert writers, "전제: S0 수준 스냅샷에 필드가 있다"

    d2, c2 = open_run()
    second = run_stage_a(topology, None, real_lut, output_dir=tmp_path / "b", supplies_v=_supplies(), donors=d2, counters=c2)
    assert (second.exit_code, second.status) == (0, "ok")

    assert second.donors is not first.donors and second.counters is not first.counters
    # 첫 실행 계수 불변(C6): 두 번째 실행 뒤에 뜬 snapshot = 두 번째 실행 전에 뜬 snapshot, 색인 항목 수도 그대로
    assert first.counters.snapshot() == before
    assert first.donors.entry_count() == entries_before

    rows_first, rows_second = _rows(first.counters), _rows(second.counters)
    assert _writers(second.s1.snapshot) == writers
    bad = []
    for name, rows in (("first", rows_first), ("second", rows_second)):
        for w in writers:
            r = rows.get(w)
            if r is None or r["computes"] != 1 or r["recomputes_same_input"] != 0:
                bad.append((name, w, r))
        for blk, r in rows.items():
            if r["calls"] != r["reuses"] + r["grafts"] + r["replays"] + r["computes"] or r["recomputes_same_input"] != 0:
                bad.append((name, blk, r))
    assert not bad, "S0 수준 블록 행 (실행, 블록, 행): %r" % bad
    # 두 실행은 같은 입력 -> 같은 계수 행(앞 실행이 남긴 것으로 건너뛰지 않는다)
    assert rows_second == rows_first
