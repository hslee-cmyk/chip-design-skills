"""검증 1 P8: 격자 해 없음이 물리적 실현 불능인지 -- bin 안 연속 W(w)(보간 변수 w 또는 1/w)에서 m·w = W(w)의 연속해(중간값 정리, 부호 변화)가
있는지 본다. 격자 판정(|격자(W/m) − w| < 격자/2)과 비교. 출력 continuum.out.json"""
import json, collections
SRC="C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6384/p8_finger/p8_enum.out.jsonl"
WMIN=0.42; out=[]; cnt=collections.Counter()
for line in open(SRC,encoding="utf-8"):
    r=json.loads(line)
    for p in r.get("points",[]):
        for dev,e in p["devices"].items():
            en=e.get("enum",{}); it=e.get("iter_rule",{})
            if "w_by_slice" not in en: continue
            st=it.get("status")
            if st=="converged": continue
            sl=en["w_by_slice"]; whi=en["w_hi_um"]; bins=sorted({tuple(v[1]) for v in sl.values()})
            rec={"circuit":r["circuit"],"point":p["point"],"dev":dev,"status":st}
            for var in ("w","invw"):
                sols=[]
                for b in bins:
                    pts=sorted((v[0],1/v[2]) for v in sl.values() if tuple(v[1])==b and v[0]>=WMIN-1e-9)
                    if not pts: continue
                    lo=max(b[0],WMIN); hi=min(b[1],whi)
                    if lo>=hi: continue
                    def W(w):
                        if len(pts)==1: return 1/pts[0][1]
                        (w0,y0),(w1,y1)=pts[0],pts[-1]
                        t=(w-w0)/(w1-w0) if var=="w" else (1/w-1/w0)/(1/w1-1/w0)
                        return 1/(y0+min(max(t,0),1)*(y1-y0))
                    for m in range(1,400):
                        f_lo=W(lo)/m-lo; f_hi=W(hi)/m-hi
                        if f_lo*f_hi<=0:
                            # bisection
                            a,bb=lo,hi
                            for _ in range(60):
                                c=(a+bb)/2
                                if (W(a)/m-a)*(W(c)/m-c)<=0: bb=c
                                else: a=c
                            sols.append((m,round((a+bb)/2,5),list(b)))
                        if W(lo)/m < lo*0.5: break
                rec[var]=sols[:4]; rec[var+"_n"]=len(sols)
                cnt[(var,st,"cont_fit" if sols else "cont_none")]+=1
            out.append(rec)
json.dump({"counts":{"|".join(k):v for k,v in sorted(cnt.items())},"rows":out},open("continuum.out.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
for k,v in sorted(cnt.items()): print(k,v)
for o in out: print(o["circuit"],o["point"],o["dev"],o["status"],"w:",o["w"][:2],"invw:",o["invw"][:2])
