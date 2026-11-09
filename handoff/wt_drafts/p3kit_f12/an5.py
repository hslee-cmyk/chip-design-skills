import ast,subprocess,re,json,sys
R='C:/g202/r'; REV=sys.argv[1]
G=['git','-c','core.quotepath=off','-C',R]
fl=subprocess.run(G+['ls-tree','-r','--name-only','-z',REV],capture_output=True).stdout.decode().split('\0')
E=re.compile(r'^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)')
pat=re.compile(r'(sizing_recipe|topology_library|design_report)(\.py)?$|^(sizing_recipe|topology_library|design_report)\.py')
out={}
for p in fl:
    if not p.endswith('.py') or E.search(p): continue
    src=subprocess.run(G+['show',REV+':'+p],capture_output=True).stdout
    if not re.search(rb'sizing_recipe|topology_library|design_report',src): continue
    try: t=ast.parse(src)
    except SyntaxError: continue
    doc=set()
    for n in ast.walk(t):
        if isinstance(n,(ast.Module,ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef)) and n.body and isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Constant): doc.add(id(n.body[0].value))
    calls=set()
    for n in ast.walk(t):
        if isinstance(n,ast.Call) and n.args and isinstance(n.args[0],ast.Constant):
            f=n.func; nm=f.id if isinstance(f,ast.Name) else getattr(f,'attr','')
            if nm in ('import_module','_import','__import__'): calls.add(id(n.args[0]))
    hits=[]
    for n in ast.walk(t):
        if isinstance(n,ast.Constant) and isinstance(n.value,str) and id(n) not in doc and id(n) not in calls:
            v=n.value.strip()
            if re.fullmatch(r'(sizing_recipe|topology_library|design_report)(\.py)?',v):
                hits.append((n.lineno,v))
    if hits: out[p]=hits
for p,h in out.items(): print(p.split('assets/')[-1], h)
print(len(out))
