import re, json, sys
sys.path.insert(0,"C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-op7a-audit/.ai/verification/20261104-op7a/scripts")
import bin_rule_lib as B
def bins_of(path):
    out=[];cur=None
    for ln in open(path,encoding="utf-8",errors="replace"):
        m=re.match(r"\s*\.model\s+(\S+)\s+\w+",ln,re.I)
        if m:
            cur={"model":m.group(1)};out.append(cur);continue
        if cur is not None and len(cur)<5:
            for k,v in re.findall(r"\b(lmin|lmax|wmin|wmax)\s*=\s*([0-9.eE+-]+)",ln):
                cur.setdefault(k,float(v))
    return out
if __name__=="__main__":
    g=5e-9
    for d in ("nfet_01v8","pfet_01v8"):
        b=bins_of(f"C:/pdk/sky130_fd_pr/cells/{d}/sky130_fd_pr__{d}__tt.pm3.spice")
        print(d,len(b),all(len(x)==5 for x in b))
        ws=sorted({(x["wmin"],x["wmax"]) for x in b}); print(" W",ws)
        ls=sorted({(x["lmin"],x["lmax"]) for x in b}); print(" L",ls)
        for x in b:
            for k in ("lmin","lmax","wmin","wmax"):
                r=x[k]/g
                if abs(r-round(r))>1e-6: print("offgrid",x)
        try:
            print(" wbp",len(B.w_boundary_points(b,g)), B.w_boundary_points(b,g)[:5])
        except B.BinRuleStop as e: print(" STOP",e.reason,e.detail, [x for x in b if x["model"] in e.detail])
