"""기준선 제안: 덤프 head·base 와 fixture 를 대조해 바뀐 칸만 낸다. usage: proposal.py <fixture json 원본> <run3> <쓸 제안 json> [적용 대상 fixture]"""
import json
import pathlib
import sys

fix = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
run3 = pathlib.Path(sys.argv[2])
head = json.loads((run3 / "dump_head.json").read_text(encoding="utf-8"))
base = json.loads((run3 / "dump_base.json").read_text(encoding="utf-8"))
cells = []
for c in head:
    w = fix[c]
    for k, sha in w.get("achievability_sha", {}).items():
        if head[c]["ach_keys"].get(k) != sha:
            cells.append({"circuit": c, "cell": "achievability_sha." + k, "old": sha, "base_dump": base[c]["ach_keys"].get(k), "new": head[c]["ach_keys"].get(k)})
    if "metric_structure_fp" in w.get("kernel", {}) and head[c].get("metric_structure_fp") not in (None, w["kernel"]["metric_structure_fp"]):
        cells.append({"circuit": c, "cell": "kernel.metric_structure_fp", "old": w["kernel"]["metric_structure_fp"], "base_dump": base[c].get("metric_structure_fp"), "new": head[c]["metric_structure_fp"]})
    for k, sha in w.get("stage_b_sha", {}).items():
        if head[c]["report_b_keys"].get(k) != sha:
            cells.append({"circuit": c, "cell": "stage_b_sha." + k, "old": sha, "base_dump": base[c]["report_b_keys"].get(k), "new": head[c]["report_b_keys"].get(k)})
    for k, sha in w.get("stage_a_sha", {}).items():
        if head[c]["report_a_keys"].get(k) != sha:
            cells.append({"circuit": c, "cell": "stage_a_sha." + k, "old": sha, "base_dump": base[c]["report_a_keys"].get(k), "new": head[c]["report_a_keys"].get(k)})
out = {"cause": "값 변화 0. gain 칸 = load_note 칸 추가(folded None, ngcc 값 3행), metric_structure = BlockStruct.members·ViewStruct.ac_ground 칸 추가. 숫자 칸 변경 0 (run3/out/cmp_chain.txt)",
       "applied_by": "test 역할(판정자 아님)", "cells": cells}
pathlib.Path(sys.argv[3]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(cells), [(x["circuit"], x["cell"], x["old"] == x["base_dump"]) for x in cells])
if len(sys.argv) > 4:
    for x in cells:
        node = fix[x["circuit"]]
        path = x["cell"].split(".")
        for p in path[:-1]:
            node = node[p]
        node[path[-1]] = x["new"]
    pathlib.Path(sys.argv[4]).write_text(json.dumps(fix, ensure_ascii=False, indent=1), encoding="utf-8")
