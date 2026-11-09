"""M-G3 기준선 집합 조립: measure_rule_l.py 결과(권고 진입점) + 처리 배정(N3.2 표, 표에 없는 것은 NEW 표지).
항목 키 표기 = design §3. 동적 접근은 design 표기가 없어 ("L-1d", "모듈.함수")를 제안한다(card 멈춤 S-3).
출력: baseline_items.jsonl, baseline_keys.json, baseline_summary.txt. 사용: python -B build_baseline.py <gc1 폴더>"""
import collections
import hashlib
import json
import pathlib
import sys

G = pathlib.Path(sys.argv[1])


def rows(name):
    return [json.loads(x) for x in open(G / name, encoding="utf-8")]


O, D, W, R = "출력 전용 선언 대기", "삭제 승인 대기", "배선 대기", "정본 읽기로 교체"
S = "정적 해석 형태로 바꾸기"
FIELD_PLAN = {
    "device.dc_off_current": (D, "EO-1", "N3.2 상위 O-205"), "device.dc_conduction_floor": (D, "EO-1", "N3.2 상위 O-205"),
    "graph.residual_probe": (W, "LA-1", "N3.2"), "graph.dof_numeric": (W, "LA-1", "N3.2"),
    "graph.ly_rows": (W, "LI-1", "N3.2 layout_outputs 미호출"), "graph.ly_dispositions": (O, "LI-1", "N3.2"),
    "device.start.point": (O, "GC-7", "N3.2"), "device.start.row": (O, "GC-7", "N3.2"),
    "graph.area_est_m2": (O, "GC-7", "N3.2"), "graph.area_fraction": (O, "GC-7", "N3.2"), "graph.conflicts": (O, "GC-7", "N3.2"),
    "graph.inactive": (O, "GC-7", "N3.2"), "graph.macro": (O, "GC-7", "N3.2"), "graph.records": (O, "GC-7", "N3.2"), "graph.uncovered": (O, "GC-7", "N3.2"),
    "graph.dc_scc_log": (O, "GC-7", "N3.2"), "graph.dc_tie_breaks": (O, "GC-7", "N3.2"),
    "graph.column_orphans": (W, "GC-7", "N3.2"), "graph.column_pairs": (O, "GC-7", "N3.2"),
    "graph.gvgs_summary": (D, "GC-2", "N3.2"), "graph.rel_kcl_group": (D, "GC-3", "N3.2"),
    "graph.rel_vds_eq_vgs": (D, "GC-7", "N3.2"), "graph.rel_matching_ratio": (D, "GC-7", "N3.2"), "graph.rel_matching_offset": (D, "GC-7", "N3.2"),
    "device.value": (D, "GC-7", "N3.2"), "device.value_key": (D, "GC-7", "N3.2"), "node.dc_branch_node": (D, "GC-7", "N3.2"),
    # 동적 접근 자리로만 읽히는 필드(N3.1-1 '그 기간에는 reader 0')
    "graph.declared": (S, "GC-7", "N3.1-1 structure_tables"),
    "graph.constraint_classes": (S, "GC-7", "NEW F-G30 SearchContext._field"), "graph.junction_source": (S, "GC-7", "NEW F-G30 SearchContext._field"),
    "graph.mismatch_source": (S, "GC-7", "NEW F-G30 SearchContext._field"), "graph.model_error": (S, "GC-7", "NEW F-G30 SearchContext._field"),
    "graph.metric_structure": (S, "GC-7", "NEW F-G30 SearchContext._field"), "graph.noise_input_cells": (S, "GC-7", "NEW F-G30 SearchContext._field"),
    "graph.ly_canon": (S, "GC-7", "NEW canonical_names.decorate.run"), "graph.ly_canon_rows": (S, "GC-7", "NEW canonical_names.decorate.run"),
}
L2_PLAN = {
    "graph.vars": (W, "LA-1", "N3.2 F-G3 문제"), "graph.column_block_map": (W, "LA-1", "N3.2 F-G3 문제"), "graph.bias_columns": (W, "LA-1", "N3.2 F-G3 문제"),
}
OUTPUT_ONLY_INITIAL = ["graph.area_bound", "graph.buffer_window_report", "graph.count_budget", "graph.curve_checks", "graph.dof", "graph.headroom_rows", "graph.verdict", "graph.warnings"]
DYNAMIC_ALLOWED = {"core/graph_snapshot.py", "core/projection.py", "core/graft.py", "sizing/seal_versions.py"}
L1X = {
    "convergence.converge:converge": None, "core.pdk_decl:read_pdk_decl": None,
    "core.writer_table:WriterTable.fields_of": (D, "GC-7", "NEW test만 호출"),
    "layout.floorplan_pack:pack_floorplan_grouped": (D, "GC-7", "NEW test만 호출"),
    "layout.outputs:layout_outputs": (W, "LI-1", "N3.2 ly_rows 소비자"),
    "lut.curve_check:curve_report": (D, "GC-7", "NEW test만 호출"),
    "lut.id_inverse:gm_id_for_target": (D, "GC-7", "NEW test만 호출, WB-1·LA-1 소비 여부는 그 card 착수 때"),
    "metrics.model_error:model_error_pairs": (D, "GC-7", "NEW test만 호출"),
    "search.eval_budget:EvalBudget.remaining": (D, "XRUN-F1 card C", "NEW card C가 EvalBudget을 지움"),
    "search.macro_poles:_signed": (D, "GC-7", "NEW 호출 0, test 0"),
    "search.residual_probe:residual_probe": (W, "LA-1", "N3.2 필드 residual_probe"),
    "sizing.size_and_seal_local:size_and_seal_local": (W, "LA-1", "N3.2 O-36"),
}
L5_SITES = {
    ("diode", "metrics/block_gain_model.py", "block_gain_model_of"): (R, "GC-6", "F-G13"),
    ("diode", "metrics/ls_swing.py", "_constraints"): (R, "GC-6", "F-G13, DE-1이 먼저면 대상 소멸"),
    ("diode", "graph/cells.py", "_signal_cells"): (R, "GC-6", "F-G13"),
    ("diode", "graph/cells.py", "classify_cells"): (R, "GC-6", "F-G13"),
    ("diode", "graph/net_model.py", "net_model"): (R, "GC-6", "F-G13"),
    ("diode", "graph/node_impedance.py", "node_impedance"): (R, "GC-6", "F-G13"),
    ("diode", "graph/cells.py", "_pass_groups"): (R, "GC-6", "NEW m.g != m.d"),
    ("diode", "graph/loops.py", "_graph_edges"): (R, "GC-6", "NEW m.d != m.g"),
    ("diode", "graph/output_direction.py", "output_directions"): (R, "GC-6", "NEW m.g != m.d"),
    ("diode", "search/iv_speed.py", "_providers"): (R, "GC-6", "NEW d.drain == d.gate"),
    ("same_vgs", "metrics/block_gain_model.py", "block_gain_model_of"): (R, "GC-6", "F-G13"),
    ("same_vgs", "sizing/writer_plan.py", "dc_writer_plan"): (R, "GC-2", "F-G13 변수 경유 꼴"),
    ("same_vgs", "graph/gvgs_cycles.py", "s1_gvgs"): (D, "GC-2", "NEW (gate, source) 키, 모듈 삭제 대상"),
    ("op_copy", "convergence/layout_input.py", "layout_input_of"): (R, "LI-1", "N3.1-5 O-27"),
    ("op_copy", "layout/run.py", "_input_columns"): (R, "LI-1", "N3.1-5 ly_point"),
    ("op_copy", "metrics/ls_fields.py", "_cell_current"): (R, "GC-7", "NEW 멈춤 S-4 -- N3.1-5 분류에 없는 자리"),
    ("op_copy", "metrics/ls_fields.py", "_signal_current"): (R, "GC-7", "NEW 멈춤 S-4 -- N3.1-5 분류에 없는 자리"),
}
items, unassigned = [], []
fields = rows("mg3_fields_recommended.jsonl")
for row in fields:
    name = row["kind"] + "." + row["field"]
    if row["class"] == "L-1":
        got = FIELD_PLAN.get(name)
        (items.append((("L-1", name), got)) if got else unassigned.append(("L-1", name, row["reads_unreachable"])))
    elif row["class"] == "L-2" and name not in OUTPUT_ONLY_INITIAL:
        got = L2_PLAN.get(name)
        (items.append((("L-2", name), got)) if got else unassigned.append(("L-2", name, row["reads"])))
seen_dyn = set()
for row in rows("mg3_dynamic.jsonl"):
    if row["src"] == "getattr_nonconst" or row["file"] in DYNAMIC_ALLOWED:
        continue
    key = ("L-1d", row["file"].replace("/", ".")[:-3] + "." + row["fn"])
    if key not in seen_dyn:
        seen_dyn.add(key)
        items.append((key, (S, "GC-7", "F-G30" if "search_context" in row["file"] or "structure_tables" in row["file"] or "canon_block" in row["file"] else "NEW F-G30 밖")))
for row in rows("mg3_l3.jsonl"):
    card = "GC-2" if row["block"] == "s1_gvgs" else "GC-7"
    why = "F-G15" if row["block"] in ("build_s1v", "coupling_vars") else "NEW F-G15 밖 " + row["status"]
    how = S if row["status"] == "reads_unverifiable" else D   # N3.1-6 어휘 안에서: 안 읽는 READS 열 = 삭제, 못 따라가는 열 = 정적 해석 형태로
    items.append((("L-3", row["block"] + "." + row["column"]), (how, card, why)))
for row in rows("mg3_l4.jsonl"):
    if row["decl_module"] and not row["read"] and not row["registry"]:
        items.append((("L-4", row["module"] + "." + row["cls"] + "." + row["slot"]), (D, "GC-7", "N3.2 하위 칸 -- M-G3c 미룸, GC-7에서 칸별로 출력·지문·삭제 분류")))
for (concept, path, fn), got in L5_SITES.items():
    items.append((("L-5", concept, path, fn), got))
for row in rows("mg9_zero_callers_fn.jsonl"):
    sid = row["fn"]
    got = L1X.get(sid, "?")
    if got == "?":
        unassigned.append(("L-1x", sid, ""))
    elif got is not None:
        items.append((("L-1x", sid.replace(":", ".")), got))
for row in rows("mg9_zero_callers_cls.jsonl"):
    items.append((("L-1x", row["cls"].replace(":", ".")), (D, "GC-7", "NEW 클래스, test만 호출(M-G9 후보)")))
items.sort(key=lambda it: it[0])
with open(G / "baseline_items.jsonl", "w", encoding="utf-8") as fh:
    for key, (how, card, why) in items:
        fh.write(json.dumps({"key": key, "how": how, "card": card, "why": why}, ensure_ascii=False) + "\n")
keys = [list(k) for k, _ in items]
text = json.dumps(keys, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
(G / "baseline_keys.json").write_text(text, encoding="utf-8")
by_rule = collections.Counter(k[0] for k, _ in items)
by_card = collections.Counter(v[1] for _k, v in items)
new = collections.Counter(k[0] for k, v in items if v[2].startswith("NEW"))
lines = ["base master 7620f5ee", "items=%d" % len(items), "by_rule=%s" % dict(sorted(by_rule.items())), "by_card=%s" % dict(sorted(by_card.items())),
         "NEW(계획 표 밖)=%s" % dict(sorted(new.items())), "unassigned=%s" % unassigned, "sha256(keys)=%s" % hashlib.sha256(text.encode("utf-8")).hexdigest()]
(G / "baseline_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
