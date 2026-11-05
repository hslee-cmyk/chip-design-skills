"""IT-2c 재측정 행만 fixture 에 반영(u17_1b stage_a_sha.tables), g8 기준선 stale 8행 제거. 각 회로 tables 차이가 default_port 칸뿐임을 먼저 단언. 인자: 대상 저장소 루트, 결과 루트(res)."""
import json
import sys
from pathlib import Path

ROOT, RES = Path(sys.argv[1]), Path(sys.argv[2])
fx = ROOT / "skills/analog-gmid-design/gmid_engine/tests/integration/fixtures/u17_1b_s0_baseline.json"
raw = fx.read_bytes()
doc = json.loads(raw.decode("utf-8"))


def strip(node):
    if isinstance(node, dict):
        return {k: strip(v) for k, v in node.items() if k != "default_port"}
    if isinstance(node, list):
        return [strip(x) for x in node]
    return node


def count(node):
    if isinstance(node, dict):
        return sum(count(v) for v in node.values()) + ("default_port" in node)
    if isinstance(node, list):
        return sum(count(x) for x in node)
    return 0


note = ("[IT-2c 2026-11-04, 원인 칸 ViewS1v.default_port(O-118 6번, 계획 N6.6), 위임 A-39] 판정자(audit)가 병합본 37a2cf5c(격리 복제본, OPENBLAS_NUM_THREADS=1, 사슬 두 번 비트 동일 확인)에서 잰 값으로 "
        "11회로의 stage_a_sha.tables 만 바꿨다. 회로마다 base 4d39eaf5 tables 와 대조해 차이가 views[].default_port 칸 추가뿐임을 단언했다(칸을 지우면 비트 동일). 값 변화표는 O-225 보류 표지, 판정 기록 "
        ".ai/verification/20261104-it2c-icm-config.json. cnr_ota·erfc_ota 는 O-228 고정 유지(기준선 없음).")
doc2 = {}
for k, v in doc.items():
    doc2[k] = v
    if k == "_source_it1":
        doc2["_source_it2c"] = note
table = []
for p in sorted((RES / "rm_head").glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["diff"] == ["stage_a.tables"], (p, d["diff"])
    assert d["bit_same_a"] and d["bit_same_b"] and d["s0_fp_same"] in (True, None), p
    assert d["status"] == doc[d["circuit"]]["status"]
    head = json.loads(Path(str(p) + ".tables").read_text(encoding="utf-8"))
    base = json.loads(Path(str(RES / "rm_base" / p.name) + ".tables").read_text(encoding="utf-8"))
    assert strip(head["a"]) == base["a"], ("tables 차이가 default_port 밖", d["circuit"])
    assert strip(head["b"]) == base["b"], d["circuit"]
    n = count(head["a"])
    assert n == len(head["a"]["views"]), (d["circuit"], n)
    old = doc[d["circuit"]]["stage_a_sha"]["tables"]
    new = d["new"]["stage_a_sha"]["tables"]
    assert old != new
    doc2[d["circuit"]] = d["new"]
    table.append({"circuit": d["circuit"], "row": "stage_a_sha.tables", "old": old, "new": new, "cause": "views[].default_port 칸 추가(O-118 6번) -- 칸을 지운 head tables == base tables(비트)", "default_port_cells": n, "status": d["status"]})
fx.write_bytes((json.dumps(doc2, ensure_ascii=False, indent=1) + ("\n" if raw.endswith(b"\n") else "")).encode("utf-8"))

gb = ROOT / "skills/analog-gmid-design/gmid_engine/tests/structure/g8_baseline.json"
rawg = gb.read_bytes()
g = json.loads(rawg.decode("utf-8"))
before = len(g["rows"])
STALE = {"_Circuit.L", "_Circuit.bulk", "_Circuit.coord", "_Circuit.device_colour", "_Circuit.kinds", "_Circuit.pins", "_Circuit.rail_v", "_Circuit.writers"}
g["rows"] = [r for r in g["rows"] if not (r["path"] == "sizing/block_columns.py" and r["kind"] == "g8_attr_container" and r["detail"] in STALE)]
assert len(g["rows"]) == before - 8, (before, len(g["rows"]))
gb.write_bytes((json.dumps(g, ensure_ascii=False, indent=2, sort_keys=True) + ("\n" if rawg.endswith(b"\n") else "")).encode("utf-8"))
(RES / "cause_table.json").write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(table), "rows; g8", before, "->", len(g["rows"]))
