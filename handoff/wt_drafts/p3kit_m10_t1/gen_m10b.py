"""measure only (NOT a role artifact): M10 prototype (design 30 §2.3 (i), D-5) on a tree at the M9-merge state.

    python -B gen_m10.py <root> <gates dir> [--variant <name>]

* new A/gmid_design_pipeline.py: import lines (each name from its R-DEF defining module, never a split shim -- ORDER) +
  one def run_gmid_design_pipeline(spec, *, topology_path, search, output_dir) whose body = the harness run() `try` statement
  verbatim (bytes) preceded by the derived locals the moved statements read (no module docstring -- MOVE-TOTAL allows exactly
  two changed/new units).
* workspaces/run_harness.py: run() keeps key check, cfg, topo, report_dir, spec, two setdefault; stem/instance_out/report_out
  and the try statement are replaced by one call. Harness imports: names no longer read anywhere in run_harness are dropped
  from the engine import lines; `from gmid_design_pipeline import run_gmid_design_pipeline` added after them.
Variants (rejection inputs): see VARIANTS at the bottom."""
import ast
import os
import re
import sys

ROOT, GATES = sys.argv[1:3]
VARIANT = sys.argv[sys.argv.index("--variant") + 1] if "--variant" in sys.argv else None
sys.path.insert(0, GATES)
A = os.path.join(ROOT, "skills", "analog-gmid-design", "assets")
H = os.path.join(ROOT, "workspaces", "run_harness.py")
raw = open(H, encoding="utf-8", newline="").read()
assert "\r\n" not in raw
lines = raw.split("\n")
tree = ast.parse(raw)
run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
body = run.body
try_stmt = next(s for s in body if isinstance(s, ast.Try))
pre = body[:body.index(try_stmt)]
# statements to drop from run(): stem / instance_out / report_out assignments
drop = [s for s in pre if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name)
        and s.targets[0].id in ("stem", "instance_out", "report_out")]
assert len(drop) == 3, [ast.unparse(d) for d in drop]


def seg(n):
    return "\n".join(lines[n.lineno - 1:n.end_lineno])


_b0, _b1 = try_stmt.body[0].lineno, try_stmt.body[-1].end_lineno
assert all(l.startswith("        ") or not l.strip() for l in lines[_b0 - 1:_b1])
try_src = chr(10).join(l[4:] if l.strip() else l for l in lines[_b0 - 1:_b1])   # try BODY only, dedented to def level
# names read by the try statement that are harness globals
gl = {n.id for b in try_stmt.body for n in ast.walk(b) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
harness_globals = {x.id for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign)) for x in ast.walk(n)
                   if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)} | \
    {a.asname or a.name for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
harness_globals |= {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
local_run = {t.id for s in pre for t in ast.walk(s) if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store)}
reads = sorted(gl & (harness_globals | local_run))
# engine names the try reads (imported in harness)
eng_imports = {}
for n in tree.body:
    if isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
        for a in n.names:
            eng_imports[a.asname or a.name] = (n.module, a.name)
std_mods = {a.asname or a.name: a.name for n in tree.body if isinstance(n, ast.Import) for a in n.names}

# R-DEF defining module per engine name (top-level def/class/assign in A/*.py)
binders = {}
for f in sorted(os.listdir(A)):
    if not f.endswith(".py"):
        continue
    t = ast.parse(open(os.path.join(A, f), encoding="utf-8").read())
    for n in t.body:
        nm = []
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            nm = [n.name]
        elif isinstance(n, ast.Assign):
            nm = [x.id for tg in n.targets for x in ast.walk(tg) if isinstance(x, ast.Name)]
        for x in nm:
            binders.setdefault(x, set()).add(f[:-3])
need_eng = sorted(x for x in reads if x in eng_imports)
need_std = sorted(x for x in reads if x in std_mods)
need_const = sorted(x for x in reads if x not in eng_imports and x not in std_mods and x not in local_run)
from_lines = {}
for x in need_eng:
    orig = eng_imports[x][1]
    b = binders.get(orig, set())
    assert len(b) == 1, (x, b)
    from_lines.setdefault(next(iter(b)), []).append(orig)
if VARIANT == "import_via_shim":
    # rejection input: import optimize_full_circuit_budget from the split shim instead of its MOD
    for m, ns in list(from_lines.items()):
        if "optimize_full_circuit_budget" in ns:
            ns.remove("optimize_full_circuit_budget")
            if not ns:
                del from_lines[m]
    from_lines.setdefault("sizing_recipe", []).append("optimize_full_circuit_budget")
imp_lines = ["import %s" % m for m in sorted(set(std_mods[x] for x in need_std) | {"os"})]
imp_lines += ["from %s import %s" % (m, ", ".join(sorted(ns))) for m, ns in sorted(from_lines.items())]
if VARIANT == "imports_workspaces":
    imp_lines.append("import run_harness  # noqa")

# locals the moved try reads that were run() locals / harness constants
prelude = [
    "    stem = os.path.basename(topology_path).removesuffix(\".topology.json\")",
    "    instance_out = os.path.join(output_dir, f\"{stem}.instance.json\")",
    "    report_out = os.path.join(output_dir, f\"{stem}.report.html\")",
    "    topo = topology_path",
    "    cfg = {\"grid_points_per_theta\": search[\"grid_points_per_theta\"]}",
]
# constants: FLOORPLAN_* come from the spec's floorplan_target (single source -- run() set them there by setdefault)
const_map = {"FLOORPLAN_MAX_ASPECT_RATIO": "spec[\"floorplan_target\"][\"max_aspect_ratio\"]",
             "FLOORPLAN_MIN_PACKING_DENSITY": "spec[\"floorplan_target\"][\"min_packing_density\"]"}
for c in need_const:
    assert c in const_map or c in ("spec", "cfg", "topo", "instance_out", "report_out"), c
for c in need_const:
    if c in const_map:
        val = const_map[c]
        if VARIANT == "const_literal" and c == "FLOORPLAN_MAX_ASPECT_RATIO":
            val = "1.5"
        prelude.append("    %s = %s" % (c, val))
moved = try_src
# cfg.get(...) for search settings -> search[...]
moved = moved.replace('grid_points_per_theta=cfg["grid_points_per_theta"]', 'grid_points_per_theta=search["grid_points_per_theta"]')
moved = moved.replace('search_method=cfg.get("search_method", "grid")', 'search_method=search["search_method"]')
moved = moved.replace('slsqp_kwargs=cfg.get("slsqp_kwargs")', 'slsqp_kwargs=search["slsqp_kwargs"]')
assert "cfg" not in moved, "cfg still read"
prelude = [p for p in prelude if not p.startswith("    cfg =")]
if VARIANT == "print_dropped":
    moved = moved.replace('print("audit_ok:", result["audit_ok"])', 'pass', 1)
sig = "def run_gmid_design_pipeline(spec, *, topology_path, search, output_dir):"
new_src = "\n".join(imp_lines) + "\n\n\n" + sig + "\n" + "\n".join(prelude) + "\n" + moved + "\n"
ast.parse(new_src)
open(os.path.join(A, "gmid_design_pipeline.py"), "w", encoding="utf-8", newline="\n").write(new_src)

# harness edit
if VARIANT == "no_wire":
    print({'variant': VARIANT}); sys.exit(0)
call = ['        run_gmid_design_pipeline(spec, topology_path=topo, output_dir=report_dir,',
        '                                 search={"grid_points_per_theta": cfg["grid_points_per_theta"],',
        '                                         "search_method": cfg.get("search_method", "grid"),',
        '                                         "slsqp_kwargs": cfg.get("slsqp_kwargs")})']
if VARIANT == "search_default_dropped":
    call[2] = '                                         "search_method": cfg.get("search_method"),'
keep = set(range(1, len(lines) + 1))
for d in drop:
    for i in range(d.lineno, d.end_lineno + 1):
        keep.discard(i)
for i in range(_b0, _b1 + 1):
    keep.discard(i)
out = []
for i, l in enumerate(lines, 1):
    if i == _b0:
        out.extend(call)
    if i in keep:
        out.append(l)
hsrc = "\n".join(out)
# drop now-unused engine import names
t2 = ast.parse(hsrc)
used = {n.id for n in ast.walk(t2) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
if VARIANT == "keep_dead_imports":
    used |= set(eng_imports)
hl = hsrc.split("\n")
for n in sorted([n for n in t2.body if isinstance(n, ast.ImportFrom) and n.module in {m for m, _ in eng_imports.values()}],
                key=lambda n: -n.lineno):
    names = [a for a in n.names if (a.asname or a.name) in used]
    if len(names) == len(n.names):
        continue
    new = [] if not names else ["from %s import %s" % (n.module, ", ".join(a.name if not a.asname else "%s as %s" % (a.name, a.asname) for a in names))]
    hl[n.lineno - 1:n.end_lineno] = new
hsrc = "\n".join(hl)
t3 = ast.parse(hsrc)
last_imp = max(n.end_lineno for n in t3.body if isinstance(n, ast.ImportFrom) and n.module in {m for m, _ in eng_imports.values()})
hl = hsrc.split("\n")
hl.insert(last_imp, "from gmid_design_pipeline import run_gmid_design_pipeline")
hsrc = "\n".join(hl)
ast.parse(hsrc)
open(H, "w", encoding="utf-8", newline="\n").write(hsrc)
print({"reads": reads, "need_eng": need_eng, "need_std": need_std, "need_const": need_const, "imports": imp_lines,
       "dropped_run_stmts": [ast.unparse(d) for d in drop], "variant": VARIANT})
