"""§11.2 1d·§11.1 규칙을 커밋된 입력에 적용(읽기만): OP-1b R1~R10, OP-1 입력 전부."""
import json,os,glob,sys,collections
W=r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/docs-op23"
out=open(os.path.join(os.path.dirname(__file__),"m2.jsonl"),"w",encoding="utf-8")
def w(**k):
    out.write(json.dumps(k,ensure_ascii=False)+"\n"); out.flush()
def gate_only(inp):
    touch=collections.defaultdict(set)
    for d in inp.get("devices") or []:
        touch[d["gate"]].add("g")
        for t in ("drain","source","bulk"):
            touch[d[t]].add(t)
    for s in (inp.get("sources") or [])+(inp.get("passives") or []):
        for t in s["terminals"]:
            touch[t].add(s["kind"])
    rails={r["net"] for r in inp.get("rails") or []}
    ports=set(v for v in (inp.get("ports") or {}).values() if isinstance(v,str))
    return {n for n,k in touch.items() if k=={"g"} and n not in rails and n not in ports}
def declared(inp): return {b["net"] for b in inp.get("bias_voltages") or []}
B=W+"/.ai/verification/20261104-op1b/baseline/"
for i in range(1,11):
    inp=json.load(open(B+f"files/R{i}/t.input.json",encoding="utf-8"))
    conv=json.load(open(B+f"R{i}.converted.json",encoding="utf-8"))
    new=conv.get("new") or conv
    w(m="R",id=f"R{i}",gate_only=sorted(gate_only(inp)),bias=sorted(declared(inp)),mismatch=sorted(gate_only(inp)^declared(inp)),
      ref=[r for r in inp["rails"] if r.get("reference")],keys=sorted(inp),proc=sorted(inp["process"]),tb=sorted(inp["testbench"]),conv_keys=sorted(new),
      conv_process=sorted((new.get("process") or {})),simulator=new.get("simulator"),devices=len(inp.get("devices") or []),
      dev_keys=sorted({k for d in inp.get("devices") or [] for k in d}))
R=W+"/.ai/verification/20261016-op1-baseline/baseline/files/"
files=glob.glob(R+"**/*.json",recursive=True)
tot=0;c=collections.Counter();ex=collections.defaultdict(list)
for f in files:
    try: inp=json.load(open(f,encoding="utf-8"))
    except Exception: continue
    if not isinstance(inp,dict) or inp.get("schema")!="spice_oracle_input/1" and "process" not in inp: continue
    if "devices" not in inp or "rails" not in inp: continue
    tot+=1
    try:
        go=gate_only(inp);dc=declared(inp)
    except Exception as e:
        c["unreadable"]+=1; continue
    if go!=dc:
        c["mismatch"]+=1; ex["mismatch"].append((os.path.relpath(f,R),sorted(go^dc)))
        if go-dc: c["undeclared_gate_only"]+=1
        if dc-go: c["declared_not_gate_only"]+=1
    else: c["match"]+=1
    if go: c["has_gate_only"]+=1
w(m="op1",inputs=tot,counts=dict(c),ex={k:v[:12] for k,v in ex.items()})
# sim.json 절대 경로 칸
def walk(o,p=""):
    if isinstance(o,dict):
        for k,v in o.items(): yield from walk(v,p+"/"+k)
    elif isinstance(o,list):
        for i,v in enumerate(o): yield from walk(v,p+"/"+str(i))
    elif isinstance(o,str):
        if ":/" in o or ":\\" in o or o.startswith("/"): yield p,o[:120]
paths=collections.Counter()
for i in range(1,11):
    for f in glob.glob(B+f"files/R{i}/o/*.json"):
        d=json.load(open(f,encoding="utf-8"))
        for p,v in walk(d):
            paths[(os.path.basename(f).split(".",1)[1],p)]+=1
w(m="abs_paths",items=[{"kind":k[0],"ptr":k[1],"n":n} for k,n in sorted(paths.items())])
ex=json.load(open(B+"files/R1/o/tfb_cs_rfeedback.free.sim.json",encoding="utf-8"))
w(m="sample_ac_file",v=ex.get("ac_file"),log=ex.get("log"))
