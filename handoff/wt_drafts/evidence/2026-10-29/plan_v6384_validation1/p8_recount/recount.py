"""검증 1 P8 독립 재계수: 작성자 측정 W_s(p8_enum.out.jsonl w_by_slice -- 엔진 LUT 조회 결과)만 읽고 해 열거·선택을 새로 짠다.
규칙 (i): bin b마다 그 bin 슬라이스로 W_b, m = 1..: w_f = 격자(W_b/m) ∈ b(첫 bin은 아래 끝 포함), w_f ≥ W_min -> 해. 선택 = w_f ≤ w_hi 중 w_f 최대.
(ii): bin 안 슬라이스가 둘 이상이면 1/W(∝ IDu)를 w에 대해 bin 안 선형 보간, 격자 w마다 m·w ≈ W(w)인지.
비교 변형: (ii') 같은 보간을 1/w 변수로. 출력 recount.out.json"""
import json, collections, math
SRC="C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6384/p8_finger/p8_enum.out.jsonl"
G=0.005; WMIN=0.42
def gr(x): return round(x/G)*G
res=collections.Counter(); per=collections.defaultdict(collections.Counter); det=[]
for line in open(SRC,encoding="utf-8"):
    r=json.loads(line)
    for p in r.get("points",[]):
        for dev,e in p["devices"].items():
            it=e.get("iter_rule",{}); en=e.get("enum",{})
            if not en or "w_by_slice" not in en: continue
            sl=en["w_by_slice"]; whi=en["w_hi_um"]
            bins=sorted({tuple(v[1]) for v in sl.values()}); first=bins[0]
            def inb(w,b): return (b[0]-1e-9<=w<=b[1]+1e-9) if b==first else (b[0]+1e-9<w<=b[1]+1e-9)
            def solve(var):
                sols=[]
                for b in bins:
                    pts=sorted((v[0],1.0/v[2]) for v in sl.values() if tuple(v[1])==b and v[0]>=WMIN-1e-9)
                    if not pts: continue
                    lo=max(b[0],WMIN) if b==first else b[0]+G
                    for n in range(int(round(lo/G)),int(round(b[1]/G))+1):
                        w=n*G
                        if len(pts)==1: y=pts[0][1]
                        else:
                            (w0,y0),(w1,y1)=pts[0],pts[-1]
                            if var=="w": t=(w-w0)/(w1-w0)
                            elif var=="invw": t=(1/w-1/w0)/(1/w1-1/w0)
                            else:  # nearest slice (old)
                                t=0.0 if abs(w-w0)<=abs(w-w1) else 1.0
                            t=min(max(t,0.0),1.0); y=y0+t*(y1-y0)
                        W=1.0/y
                        m=max(1,round(W/w))
                        for mm in (m-1,m,m+1):
                            if mm>=1 and abs(gr(W/mm)-w)<1e-9 and inb(w,b): sols.append((mm,round(w,4)))
                return sorted(set(sols))
            out={}
            for var in ("nearest","w","invw"):
                s=[x for x in solve(var) if x[1]<=whi+1e-9]
                out[var]=max(s,key=lambda x:(x[1],-x[0])) if s else None
            st=it.get("status")
            for var in out:
                res[(var,st,"fit" if out[var] else "none")]+=1
                per[r["circuit"]][(var,st,"fit" if out[var] else "none")]+=1
            if out["w"]!=out["invw"]: det.append([r["circuit"],p["point"],dev,st,out])
json.dump({"counts":{"|".join(k):v for k,v in sorted(res.items())},"w_vs_invw_diff":det},open("recount.out.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
for k,v in sorted(res.items()): print(k,v)
print("w vs invw 선택 다름:",len(det)); [print(d) for d in det]
