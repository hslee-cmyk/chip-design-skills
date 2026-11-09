import subprocess, sys, difflib
W="C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384"
a,b,path=sys.argv[1],sys.argv[2],sys.argv[3]
def show(rev):
    return subprocess.run(["git","-C",W,"show",f"{rev}:{path}"],capture_output=True).stdout.decode("utf-8").split("\n")
A=show(a);B=show(b)
sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
out=[]
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=="equal": continue
    out.append(f"=== {tag} old {i1+1}-{i2} new {j1+1}-{j2}")
    if tag=="replace" and i2-i1==j2-j1:
        for k in range(i2-i1):
            x,y=A[i1+k],B[j1+k]
            s=difflib.SequenceMatcher(None,x,y,autojunk=False)
            out.append(f"--- line new {j1+k+1}")
            for t,p1,p2,q1,q2 in s.get_opcodes():
                if t=="equal":
                    seg=x[p1:p2]
                    out.append(("[="+seg+"=]") if len(seg)<120 else "[="+seg[:50]+" ... "+seg[-50:]+"=]")
                else:
                    if p2>p1: out.append("[-"+x[p1:p2]+"-]")
                    if q2>q1: out.append("{+"+y[q1:q2]+"+}")
    else:
        for k in range(i1,i2): out.append("- "+A[k])
        for k in range(j1,j2): out.append(f"+ [{k+1}] "+B[k])
print("\n".join(out))
