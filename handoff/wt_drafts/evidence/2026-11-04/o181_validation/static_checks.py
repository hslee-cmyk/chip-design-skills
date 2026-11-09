import subprocess,re,json,sys,collections
A=r"C:/Users/HSLEE/AppData/Local/Temp/la1s_o181_audit/iso"
BASE="0d99a813"
def g(*a): return subprocess.run(["git","-C",A,*a],capture_output=True).stdout
files=g("diff","--name-only",BASE,"HEAD").decode().split("\n")[:-1]
rx=re.compile(rb"\bQ([1-5])\b")
rx2=re.compile(rb"\bq([1-5])(x?)\b")
pure=[];other=[]
for f in files:
    old=g("show",BASE+":"+f); new=g("show","HEAD:"+f)
    conv=rx.sub(rb"Mfx\1",old)
    conv2=rx2.sub(rb"mfx\1\2",conv)
    if conv==new: pure.append(f)
    elif conv2==new: pure.append(f+" (q소문자 포함)")
    else: other.append(f)
print("rename only",len(pure))
for f in pure:
    if 'q소문자' in f: print(" ",f)
print("not rename only",len(other))
for f in other:
    old=rx2.sub(rb"mfx\1\2",rx.sub(rb"Mfx\1",g("show",BASE+":"+f))).decode('utf-8').splitlines()
    new=g("show","HEAD:"+f).decode('utf-8').splitlines()
    import difflib
    d=[l for l in difflib.unified_diff(old,new,lineterm="",n=0) if l[:2] not in("--","++","@@")]
    print(" ",f.split("gmid_engine/")[-1],"-%d +%d"%(sum(l[0]=='-' for l in d),sum(l[0]=='+' for l in d)))
    if "fixtures/" in f:
        for l in d: print("     ",l[:230])
