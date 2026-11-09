"""measure only (NOT a role artifact): D0b five-test simulation + (d)-1 fact-sample check on one commit.

    python -B sim5.py <clone root> <rev> <plan.json or -> <out.jsonl (append)> <case id> [<ref plan.json>]

T-A..T-E follow draft_p3_d0b.spec.md contract 11 (a) assertion order; reports the FIRST failing assertion per test (or PASS).
Registry/plan read with `git show <rev>:` (contract 11 (e)). Expected sample stems = the spec's (d)-1 table + D-11 (가) row
`_QUERY_CACHE_MAX` -> gmid_lut (A-1). B26-1-only samples (RailDeclaration, rail_declaration) are skipped when absent.
"""
import json
import re
import subprocess
import sys

ROOT, REV, PLAN, OUT, CASE = sys.argv[1:6]
REF = sys.argv[6] if len(sys.argv) > 6 else None
REG = "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"
MOD7 = "stick_diagram.py"
RULES = {"A-0", "A-1", "A-2", "A-3", "A-4", "A-K", "A-5", "A-6", "A-7"}
# (unit key, expected stem, has registry row)
SAMPLES = [
    ("load_topology", "circuit_state_graph", 1), ("validate_theta_declaration_order", "circuit_state_graph", 1),
    ("require_declared_spec_source", "circuit_state_graph", 1), ("optimize_full_circuit_budget", "sizing_layout_convergence", 1),
    ("_optimize_theta_slsqp", "sizing_layout_convergence", 1), ("GmIdLUT", "gmid_lut", 1), ("compute_metric", "circuit_metrics", 1),
    ("apply_theta_feed", "circuit_metrics", 1), ("true_current_mirror_groups", "circuit_state_graph", 1),
    ("find_hub_merge_candidates", "circuit_state_graph", 1), ("run_topology_pipeline_with_finger_fixup", "sizing_layout_convergence", 1),
    ("render_html_report", "instance_report_builder", 1), ("NameCollisionVerdict", "circuit_state_graph", 1),
    ("run_full_circuit_audit", "stick_diagram", 1), ("_invert_gm_id_for_current", "gmid_sizing_engine", 1),
    ("quantize_L", "theta_search", 1), ("_theta_evidence_for_pair", "instance_report_builder", 1), ("_kv_table", "instance_report_builder", 1),
    ("save_html_report", "instance_report_builder", 1), ("_topology_ref_relpath", "instance_report_builder", 0),
    ("check_topology_name_uniqueness", "circuit_state_graph", 0), ("render_report", "audit_current_forced", 1),
    ("solve_diode_stack_current", "gmid_sizing_engine", 1), ("MultiLeafHubParityVerdict", "stick_diagram", 1),
    ("check_multi_leaf_hub_parity", "stick_diagram", 1),
    ("_QUERY_CACHE_MAX", "gmid_lut", 1),  # D-11 (가) -- new row
    ("RailDeclaration", "topology_authoring", 0), ("rail_declaration", "topology_authoring", 0),  # B26-1 only
]
B26_ONLY = {"RailDeclaration", "rail_declaration"}


def show(path):
    r = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (REV, path)], capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


def split_cells(line):
    s = line.strip()[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    out, cur, i = [], "", 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "\\|"; i += 2; continue
        if s[i] == "|":
            out.append(cur.strip()); cur = ""
        else:
            cur += s[i]
        i += 1
    out.append(cur.strip())
    return out


def tables(text):
    lines = text.splitlines()
    res, i = [], 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*:?-{3,}", lines[i + 1]):
            hdr = split_cells(lines[i])
            if "함수" in hdr and "이관 목적지" in hdr:
                rows, j = [], i + 2
                while j < len(lines) and lines[j].startswith("|"):
                    rows.append((j + 1, split_cells(lines[j]))); j += 1
                res.append((hdr, rows)); i = j; continue
        i += 1
    return res


def first_tok(cell):
    t = re.findall(r"`([^`]*)`", cell)
    return t[0] if t else ""


reg = show(REG)
plan = None
if PLAN != "-":
    try:
        with open(PLAN, encoding="utf-8") as fh:
            first = fh.readline()
        plan = json.loads(first)
        if plan.get("tool") != "move_plan":
            plan = None
    except Exception:
        plan = None
tabs = tables(reg)
res = {"case": CASE, "rev": REV}


def target_rows():
    by_key = {}
    for u, v in plan["assignment"].items():
        by_key.setdefault(u.split("::", 1)[1], []).append(v)
    out = []
    for hdr, rows in tabs:
        cf, cd = hdr.index("함수"), hdr.index("이관 목적지")
        cr = hdr.index("근거 규칙") if "근거 규칙" in hdr else None
        for ln, c in rows:
            tok = first_tok(c[cf] if cf < len(c) else "")
            if tok.lstrip().startswith("└") or tok.startswith(" "):
                continue
            key = tok.strip().split(".")[0]
            if key in by_key:
                out.append((ln, key, c[cd] if cd < len(c) else "", c[cr] if cr is not None and cr < len(c) else None, by_key[key]))
    return out


def TA():
    if plan is None:
        return "first-line JSON"
    for k in ("conflicts", "upward", "cycles", "unassigned", "import_time_high", "import_conflicts"):
        if plan[k]:
            return "%s %d" % (k, len(plan[k]))
    out7 = [u for u, v in plan["assignment"].items() if v["mod"] == MOD7 and not u.startswith(MOD7 + "::")]
    if out7:
        return "MOD7 outside %d %s" % (len(out7), out7)
    if plan["reg_mismatch"]:
        return "reg_mismatch %d" % len(plan["reg_mismatch"])
    if plan["verdict"] != "PASS":
        return "verdict"
    return "PASS"


def TB():
    if plan is None:
        return "first-line JSON"
    if not tabs:
        return "tables 0"
    tr = target_rows()
    if not tr:
        return "target rows 0"
    if any(len({v["mod"] for v in vs}) > 1 for _, _, _, _, vs in tr):
        return "same-key mod split"
    bad = [(ln, k, cell) for ln, k, cell, _, vs in tr if cell != vs[0]["mod"][:-3]]
    return "cell!=stem %d %s" % (len(bad), bad[:3]) if bad else "PASS"


def TC():
    for hdr, _ in tabs:
        cd = hdr.index("이관 목적지")
        if cd + 1 >= len(hdr) or hdr[cd + 1] != "근거 규칙":
            return "header"
    if plan is None:
        return "first-line JSON (after header)"
    bad = [(ln, k, r) for ln, k, _, r, _ in target_rows() if r not in RULES]
    return "rule set %d %s" % (len(bad), bad[:3]) if bad else "PASS"


def TD():
    n = reg.count("보류(Phase 3)")
    return "hold3 %d" % n if n else "PASS"


def TE():
    if plan is None:
        return "first-line JSON"
    tr = {k: (ln, cell) for ln, k, cell, _, _ in target_rows()}
    stems = {}
    for u, v in plan["assignment"].items():
        stems.setdefault(u.split("::", 1)[1], set()).add(v["mod"][:-3])
    bad = []
    for name, exp, row in SAMPLES:
        if name in B26_ONLY and name not in stems:
            continue
        if row and (name not in tr or tr[name][1] != exp):
            bad.append((name, "cell", tr.get(name, (None, None))[1]))
        if stems.get(name) != {exp}:
            bad.append((name, "plan", sorted(stems.get(name, []))))
    return "samples %d %s" % (len(bad), bad[:4]) if bad else "PASS"


if plan is not None:
    res["plan"] = {"exit_verdict": plan["verdict"], "lens": {k: len(plan[k]) for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch", "import_time_high", "import_conflicts")},
                   "assigned": len(plan["assignment"]), "mod7_outside": sorted(u for u, v in plan["assignment"].items() if v["mod"] == MOD7 and not u.startswith(MOD7 + "::")),
                   "upward": plan["upward"], "conflicts": plan["conflicts"], "unassigned": plan["unassigned"], "import_time_high": [x.get("unit") for x in plan["import_time_high"]],
                   "import_conflicts": [(x["mod"], x["name"]) for x in plan["import_conflicts"]], "reg_mismatch": [m["unit"] for m in plan["reg_mismatch"]][:5]}
    res["target_rows"] = len(target_rows())
    if REF:
        e = json.load(open(REF, encoding="utf-8"))["assignment"]
        k1 = {u.split("::", 1)[1]: v["mod"] for u, v in plan["assignment"].items()}
        k2 = {u.split("::", 1)[1]: v["mod"] for u, v in e.items()}
        res["map_diff"] = sorted([("%s %s->%s" % (k, k2.get(k), k1.get(k))) for k in set(k1) | set(k2) if k1.get(k) != k2.get(k)])
res["tests"] = {"T-A": TA(), "T-B": TB(), "T-C": TC(), "T-D": TD(), "T-E": TE()}
res["tables"] = len(tabs)
res["hold3"], res["hold4"] = reg.count("보류(Phase 3)"), reg.count("보류(Phase 4)")
with open(OUT, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(res, ensure_ascii=False) + "\n")
print(json.dumps({"case": CASE, "tests": res["tests"], "plan": res.get("plan", {}).get("lens"), "map_diff": res.get("map_diff")}, ensure_ascii=False))
