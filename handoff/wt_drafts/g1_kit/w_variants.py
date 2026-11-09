import sys, ast, os
sys.path.insert(0,'C:/g143/p/tools/gates')
import reachability as g1
AS="skills/analog-gmid-design/assets/"
base={k:v for k,v in g1.read_tree('C:/g143/b','HEAD',g1.SOURCE_GLOBS).items() if g1._is_source(k)}
hf=dict(base)
for m in ("sizing_recipe","stick_diagram","topology_library","design_report"):
    p=AS+m+".py"; src=base[p]; tree=ast.parse(src); tops=set()
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)): tops.add(n.name)
        elif isinstance(n,(ast.Assign,ast.AnnAssign)):
            for t in (n.targets if isinstance(n,ast.Assign) else [n.target]): tops|={x.id for x in ast.walk(t) if isinstance(x,ast.Name)}
    hf[AS+m+"_mv.py"]=src; hf[p]="from %s_mv import (%s)  # noqa\n"%(m,", ".join(sorted(x for x in tops if not x.startswith("__"))))
for v in sys.argv[1:]:
    os.environ["G1_VARIANT"]=v
    mv=g1.moved_defs(base,hf); print(v, len(mv["units"]), len(mv["defs"]), len(mv["rejected"]))
