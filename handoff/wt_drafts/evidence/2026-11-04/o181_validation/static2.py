import subprocess,json,sys,tempfile,os,re,collections
from pathlib import Path
A=r"C:/Users/HSLEE/AppData/Local/Temp/la1s_o181_audit/iso"
SK=Path(A)/"skills/analog-gmid-design"
sys.path.insert(0,str(SK)); sys.path.insert(0,str(SK/"gmid_engine/tests/structure"))
from gmid_engine.authoring import load_topology
def g(*a): return subprocess.run(["git","-C",A,*a],capture_output=True).stdout
def rd(p): return json.load(open(p,encoding="utf-8"))
LIB=SK/"assets/library"
print("== erfc fp")
T="skills/analog-gmid-design/assets/library/erfc_ota.topology.json"
print("master==merged topology blob", g("rev-parse","0d99a813:"+T)==g("rev-parse","HEAD:"+T))
print("HEAD fp", load_topology(str(LIB/"erfc_ota.topology.json")).connectivity_fp)
print("spec old", json.loads(g("show","0d99a813:skills/analog-gmid-design/assets/library/erfc_ota.sizing_spec.json"))["meta"]["topology_fp"])
print("spec new", rd(LIB/"erfc_ota.sizing_spec.json")["meta"]["topology_fp"])
h="skills/analog-gmid-design/assets/heldout/erfc_ota.topology.json"
for c in ("81dddba5","6705b911"):
    raw=g("show",c+":"+h)
    d=tempfile.mkdtemp(dir=str(Path(A).parent)); p=os.path.join(d,"erfc_ota.topology.json"); open(p,"wb").write(raw)
    try: print(c,"fp",load_topology(p).connectivity_fp)
    except Exception as e: print(c,"err",type(e).__name__,str(e)[:300])
a=json.loads(g("show","81dddba5:"+h)); b=rd(LIB/"erfc_ota.topology.json")
strip=lambda e:{f:v for f,v in e.items() if not f.startswith("_")}
na={e["name"]:strip(e) for e in a["netlist"]}; nb={e["name"]:strip(e) for e in b["netlist"]}
print("netlist diff vs 81dddba5", {k:{f:(na.get(k,{}).get(f),nb[k].get(f)) for f in set(na.get(k,{}))|set(nb[k]) if na.get(k,{}).get(f)!=nb[k].get(f)} for k in nb if na.get(k)!=nb[k]}, "removed", set(na)-set(nb))
print("other connectivity keys eq", {k:a.get(k)==b.get(k) for k in("passive_elements","ideal_sources","supply_nets","ports","bias_inputs")})
print("== fp all spec=topology")
for p in sorted(LIB.glob("*.sizing_spec.json")):
    n=p.name[:-len(".sizing_spec.json")]
    ok=rd(p)["meta"]["topology_fp"]==load_topology(str(LIB/(n+".topology.json"))).connectivity_fp
    print(n,ok)
print("== new 4 counts (JSON)")
for n in("cnr_ota","erfc_ota","r2r_opamp","rfc_ota"):
    t=rd(LIB/(n+".topology.json")); s=rd(LIB/(n+".sizing_spec.json"))
    ports={k:v for k,v in t.get("ports",{}).items() if not k.startswith("_")}
    print(n,len(t["netlist"]),len(t.get("passive_elements",[])),len(t.get("ideal_sources",[])),len(t["supply_nets"]),
      sum(1 for v in ports.values() if v.get("direction")=="input"),sum(1 for v in ports.values() if v.get("direction")=="output"),
      "bias",sorted(t.get("bias_inputs",[])),"cons",len(s["human"]["constraints"]))
print("== r2r n_ab nets")
t=rd(LIB/"r2r_opamp.topology.json")
for net in("n_abp","n_abn"):
    print(net)
    for e in t["netlist"]:
        ts=[k for k in("drain","gate","source","bulk") if e.get(k)==net]
        if ts: print("  ",e["name"],e["kind"],ts,{k:e.get(k) for k in("drain","gate","source")})
    for e in t.get("passive_elements",[])+t.get("ideal_sources",[]):
        if net in e.get("terminals",[]): print("  ",e["name"],e["kind"],e["terminals"])
for m in("M21","M22","M23","M24"): print(m,[{k:e.get(k) for k in("kind","drain","gate","source")} for e in t["netlist"] if e["name"]==m])
for s in t.get("ideal_sources",[]): print(s["name"],s["kind"],s["terminals"])
sp=rd(LIB/"r2r_opamp.sizing_spec.json")["human"]["element_values"]
print({k:v.get("value_dc_amp") for k,v in sp.items() if isinstance(v,dict) and "value_dc_amp" in v})
print("== supplies old vs new")
for p in sorted(LIB.glob("*.topology.json")):
    if p.name.startswith("_"): continue
    n=p.name[:-len(".topology.json")]
    raw=rd(p); dec=raw.get("_declared_target_spec",{}).get("supplies_v")
    old={k:v for k,v in dec.items() if not k.startswith("_")} if dec else {"vdd":1.8,"gnd":0.0}
    new=rd(LIB/(n+".sizing_spec.json"))["human"]["supplies_v"]["values"]
    print(n,"same" if old==new else ("DIFF",old,new),"declared" if dec else "default-used","rails",raw["supply_nets"])
print("== rule E")
import structure_checks as sc
circ,names=sc.library_names(LIB)
voc=sc.engine_vocabulary()
ER=SK/"gmid_engine"
print("circuits",len(circ),"names",len(names),"vocab",len(voc),"removed",sorted(set(names)&voc))
n,v=sc.check_e(ER,names); print("full names: n",n,"violations",len(v))
print(collections.Counter(x.detail.split(" = ")[0] for x in v))
n2,v2=sc.check_e(ER,sc.without_engine_vocabulary(names)); print("filtered: n",n2,"violations",len(v2))
for x in v[:60]: print("  ",x.path,x.line,x.detail[:90])
print("origins",{k:names[k][:4] for k in sorted(set(names)&voc)})
print("Mfx in library", [k for k in names if k.lower().startswith("mfx")])
