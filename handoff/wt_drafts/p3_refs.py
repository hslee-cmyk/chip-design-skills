import ast, sys
sys.stdout.reconfigure(encoding="utf-8")
A = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets"
mods = ["sizing_recipe", "stick_diagram", "topology_library"]
trees = {m: ast.parse(open(A + "\\" + m + ".py", "rb").read().decode("utf-8")) for m in mods}
top = {m: {n.name: n for n in t.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))} for m, t in trees.items()}


def refs(m, name):
    node = top[m][name]
    names = {x.id for x in ast.walk(node) if isinstance(x, ast.Name)}
    out = {}
    for mm in mods:
        if mm != m and mm not in ("stick_diagram", "topology_library") and m != "sizing_recipe":
            pass
        hit = sorted(n for n in names if n in top[mm] and n != name)
        if hit:
            out[mm] = hit
    return out


for m, n in [("sizing_recipe", "optimize_full_circuit_budget"), ("sizing_recipe", "_build_theta_evaluator"),
             ("stick_diagram", "load_topology"), ("sizing_recipe", "validate_theta_declaration_order"),
             ("sizing_recipe", "compute_metric"), ("stick_diagram", "propose_device_roles_gap_fill")]:
    r = refs(m, n)
    print(m, n, {k: (len(v), v[:30]) for k, v in r.items()})
    print("  lines", top[m][n].lineno, top[m][n].end_lineno)
