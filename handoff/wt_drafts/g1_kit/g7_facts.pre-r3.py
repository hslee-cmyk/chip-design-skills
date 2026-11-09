import importlib.util, json, sys, collections
sys.path.insert(0, 'C:/g143/p/tools/gates')
import reachability as g1
R='C:/g143/b'
out={}
for rid,(b,h) in {"df36":("070cf69","ed98d35"),"dup-w-calc":("b7d1798","a9de49c")}.items():
    bt=g1.read_tree(R,b,g1.SOURCE_GLOBS); ht=g1.read_tree(R,h,g1.SOURCE_GLOBS)
    mv=g1.moved_defs({k:v for k,v in bt.items() if g1._is_source(k)},{k:v for k,v in ht.items() if g1._is_source(k)})
    out[rid]={k:len(mv[k]) for k in ("units","defs","rejected")}
# engine facts at HEAD via SourceIndex
ht=g1.read_tree(R,"HEAD",g1.SOURCE_GLOBS)
AS="skills/analog-gmid-design/assets/"
H=g1.SourceIndex({AS+m+".py":ht[AS+m+".py"] for m in ("sizing_recipe","stick_diagram","topology_library","design_report")})
facts={}
for m in ("sizing_recipe","stick_diagram","topology_library","design_report"):
    md=H.mod(AS+m+".py")
    import ast
    cls=[n for n in md.tree.body if isinstance(n,ast.ClassDef)]
    facts[m]={"star":"*" in md.bindings,"global":sorted(md.global_declared),"futures":sorted(md.futures),
      "multi":sorted(n for n,b in md.bindings.items() if len(b)>1),"qual_dups":sorted(q for q,c in md.qcount.items() if c>1),
      "classes":len(cls),"classes_no_method":sum(1 for c in cls if not any(isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) for x in ast.walk(c))),
      "units":len(md.units),"defs":len(g1.iter_defs(md.tree))}
out["facts"]=facts
print(json.dumps(out,ensure_ascii=False,indent=0))
json.dump(out,open('C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/g1_kit/out/g7_facts_0f23786.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
