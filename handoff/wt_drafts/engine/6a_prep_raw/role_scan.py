import ast, re, sys, io, collections, os
A = r"C:\Users\HSLEE\Documents\Todoc\fpga\gmid-light\skills\analog-gmid-design\assets"
KEYS = ["headroom_role","gm_id_role","L_role","sizing_roles","device_roles","fold_group","vertical_stack_id",
        "same_as_device","gm_id_match_vgs_of","budget_reference_device","shared_gm_id_groups","netlist_sections_structured",
        "gain_stages_sum","stage_devices","matching_pairs","current_forced","\"stages\"","netclass","net_class"]
out = io.open(sys.argv[1], "w", encoding="utf-8")
for fn in ["sizing_recipe.py","stick_diagram.py","design_report.py","topology_library.py","topology_to_markdown.py","audit_current_forced.py"]:
    p = os.path.join(A, fn)
    src = io.open(p, encoding="utf-8").read()
    lines = src.splitlines()
    tree = ast.parse(src)
    spans = []
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            spans.append((node.lineno, node.end_lineno, node.name))
    def enclosing(l):
        best=None
        for a,b,n in spans:
            if a<=l<=b and (best is None or a>best[0]): best=(a,b,n)
        return best
    # string-literal / code occurrences (exclude pure comment lines and docstrings roughly: we keep all but tag)
    doc_lines=set()
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.ClassDef,ast.Module,ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0],ast.Expr) and isinstance(getattr(node.body[0],'value',None),ast.Constant) and isinstance(node.body[0].value.value,str):
                d=node.body[0]; doc_lines.update(range(d.lineno,d.end_lineno+1))
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for i,l in enumerate(lines,1):
        s=l.strip()
        if s.startswith("#") or i in doc_lines: continue
        for k in KEYS:
            if k in l:
                e=enclosing(i)
                per[k][e[2] if e else "<module>"].append(i)
    out.write(f"\n## {fn}\n")
    for k in KEYS:
        if not per[k]: continue
        tot=sum(len(v) for v in per[k].values())
        out.write(f"\n### {k}  (code lines {tot}, functions {len(per[k])})\n")
        for f,ls in sorted(per[k].items(), key=lambda x:x[1][0]):
            out.write(f"- {f}: {','.join(map(str,ls))}\n")
out.close()
