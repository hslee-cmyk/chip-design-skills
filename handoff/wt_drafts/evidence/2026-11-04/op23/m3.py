"""git 객체 전부와 worktree·디스크에서 생성기 판 찾기(OP-3 착수 조건)."""
import hashlib,json,os,subprocess,glob
W=r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/docs-op23"
T="8df35d2ea405a0f53a836f7ce6cccc26e0db82ad2f82838588991afdcfb319df"
out=open(os.path.join(os.path.dirname(__file__),"m3.jsonl"),"w",encoding="utf-8")
def w(**k):
    out.write(json.dumps(k,ensure_ascii=False)+"\n"); out.flush()
def sh(b): return hashlib.sha256(b).hexdigest()
p=subprocess.run(["git","-C",W,"cat-file","--batch-check","--batch-all-objects"],capture_output=True,text=True)
blobs=[l.split() for l in p.stdout.splitlines()]
blobs=[(a,int(c)) for a,b,c in blobs if b=="blob"]
w(m="objects",blobs=len(blobs))
cand=[a for a,c in blobs if 15000<c<120000]
w(m="cand",n=len(cand))
proc=subprocess.Popen(["git","-C",W,"cat-file","--batch"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
hit=[];gen=0
for a in cand:
    proc.stdin.write((a+"\n").encode());proc.stdin.flush()
    hdr=proc.stdout.readline().split()
    size=int(hdr[2]);b=proc.stdout.read(size);proc.stdout.read(1)
    if b"model_includes" not in b and b"DUT_LINE" not in b: continue
    gen+=1
    n=b.replace(b"\r\n",b"\n")
    for tag,v in (("blob",sh(b)),("lf",sh(n)),("crlf",sh(n.replace(b"\n",b"\r\n")))):
        if v==T: hit.append((a,tag))
proc.stdin.close()
w(m="blob_scan",generator_like=gen,hit=hit)
roots=[r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/*/skills/analog-gmid-design/assets/sky130_lut_sweep.py",
       r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/sky130_lut_sweep.py",
       r"C:/Users/HSLEE/Documents/Todoc/fpga/**/*lut_sweep*.py"]
seen=set();n=0;hits=[]
for r in roots:
    for f in glob.glob(r,recursive=True):
        f=os.path.normpath(f)
        if f in seen: continue
        seen.add(f);n+=1
        b=open(f,"rb").read();m=b.replace(b"\r\n",b"\n")
        if T in (sh(b),sh(m),sh(m.replace(b"\n",b"\r\n"))): hits.append(f)
w(m="disk_scan",files=n,hits=hits)
