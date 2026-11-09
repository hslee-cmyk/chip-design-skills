import hashlib,json,os,subprocess,sys,glob
import numpy as np
W=r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/docs-op23"
out=open(os.path.join(os.path.dirname(__file__),"m1.jsonl"),"w",encoding="utf-8")
def w(**k):
    out.write(json.dumps(k,ensure_ascii=False)+"\n"); out.flush()
def lf(b): return hashlib.sha256(b.replace(b"\r\n",b"\n")).hexdigest()
def raw(b): return hashlib.sha256(b).hexdigest()
A=W+"/skills/analog-gmid-design/assets/"
for p in ["sky130_pdk_decl.json","lut_v2_location.json","sky130_lut_rule_decl.json","lut_v2_bin_rule.json"]:
    b=open(A+p,"rb").read(); w(m="decl_sha",file=p,lf=lf(b),raw=raw(b),crlf=b.count(b"\r\n"))
pd=json.load(open(A+"sky130_pdk_decl.json",encoding="utf-8"))
for k,v in pd["sources"].items():
    fp=os.path.join(pd["pdk_root"],v["path"])
    if os.path.exists(fp):
        b=open(fp,"rb").read(); w(m="engine_source",key=k,exists=True,rec=v["sha256"][:12],lf=lf(b)[:12],raw=raw(b)[:12],rec_is=("lf" if v["sha256"]==lf(b) else "raw" if v["sha256"]==raw(b) else "none"),path=v["path"])
    else: w(m="engine_source",key=k,exists=False,path=v["path"])
loc=json.load(open(A+"lut_v2_location.json",encoding="utf-8"))
root=os.environ.get(loc["root"]["env"]) or loc["root"]["default"]; pdk=os.environ.get(loc["pdk_root"]["env"]) or loc["pdk_root"]["default"]
w(m="loc",root=root,pdk_root=loc["pdk_root"],keys=list(loc.keys()),files=list(loc["files"].keys()))
lod=pdk+"/models/parameters/lod.spice"; b=open(lod,"rb").read(); w(m="lod",lf=lf(b),raw=raw(b))
gens={}; shapes={}
files=[]
for r,ds,fs in os.walk(root):
    if "verification" in r: continue
    for f in fs:
        if f.endswith(".npz"): files.append(os.path.join(r,f))
for fp in sorted(files):
    z=np.load(fp,allow_pickle=False)
    if "meta_json" not in z.files:
        w(m="meta_absent",f=os.path.relpath(fp,root)); continue
    mt=json.loads(str(z["meta_json"]))
    g=mt.get("generator_sha256"); rec=mt.get("model_files_sha256") or {}
    shape="flat" if rec and all(isinstance(x,str) for x in rec.values()) else "nested" if rec else "empty"
    gens.setdefault(g,[]).append(os.path.relpath(fp,root)); shapes[shape]=shapes.get(shape,0)+1
    if shape=="nested":
        w(m="nested",f=os.path.relpath(fp,root),gen=g,keys=sorted(rec),corner=str(z["corner"]) if "corner" in z.files else None)
    else:
        w(m="flat",f=os.path.relpath(fp,root),gen=g,keys=sorted(rec))
w(m="gens",by={str(k):len(v) for k,v in gens.items()},shapes=shapes,ex={str(k):v[:2] for k,v in gens.items()})
g=lambda *a: subprocess.run(["git","-C",W,*a],capture_output=True).stdout
paths=set()
for line in g("log","--all","--name-only","--format=","--","*lut_sweep*").decode("utf-8","replace").splitlines():
    if line.strip(): paths.add(line.strip())
w(m="gen_paths",paths=sorted(paths))
found={}; tot=0
targets=set(x for x in gens if x)
seen=set()
for p in sorted(paths):
    revs=g("log","--all","--format=%H","--",p).decode().split()
    for rv in revs:
        b=g("show",f"{rv}:{p}")
        if not b: continue
        tot+=1
        for tag,val in (("lf",lf(b)),("crlf",raw(b.replace(b"\r\n",b"\n").replace(b"\n",b"\r\n"))),("blob",raw(b))):
            if val in targets: found.setdefault(val,[]).append((rv[:10],p,tag))
w(m="gen_hunt",versions=tot,found={k:v[:4] for k,v in found.items()},missing=sorted(targets-set(found)))
for extra in (os.path.dirname(root),root):
    for fp in glob.glob(extra+"/**/*lut_sweep*.py",recursive=True):
        b=open(fp,"rb").read(); w(m="disk_gen",f=fp,lf=lf(b),raw=raw(b),hit=lf(b) in targets or raw(b) in targets)
