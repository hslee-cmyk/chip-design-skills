import subprocess,re,sys
A=r"C:/Users/HSLEE/AppData/Local/Temp/la1s_o181_audit/iso"
d=subprocess.run(["git","-C",A,"diff","-U0","0d99a813","HEAD","--","*.py"],capture_output=True,encoding="utf-8").stdout
f=None
pat=re.compile(r"assert|raises|xfail|skip|def test_|deselect|pytest\.|fail\(")
minus=[];plus=[]
for l in d.splitlines():
    if l.startswith("+++ "): f=l[6:].split("/")[-1]
    elif l.startswith("--- "): pass
    elif l.startswith("-") and pat.search(l): minus.append((f,l[1:].strip()))
    elif l.startswith("+") and pat.search(l): plus.append((f,l[1:].strip()))
# normalise device names Q1..5 -> Mfx
norm=lambda s:re.sub(r"\bQ([1-5])\b",r"Mfx\1",s)
ps=[(f,norm(s)) for f,s in plus]; ms=[(f,norm(s)) for f,s in minus]
print("removed",len(minus),"added",len(plus))
print("== removed w/o identical after name norm")
for x in ms:
    if x not in ps: print(x[0],"|",x[1][:200])
print("== added w/o identical")
for x in ps:
    if x not in ms: print(x[0],"|",x[1][:200])
