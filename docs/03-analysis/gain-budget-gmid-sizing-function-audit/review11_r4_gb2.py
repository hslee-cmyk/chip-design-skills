# -*- coding: utf-8 -*-
"""Block construction (rule 5/6) + rule 9(c) on the BLOCK output node + GB2 stop table."""
import sys, os, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r4_rules as R
from r4_rules import C, CIRCUITS, EXISTING4, default_views, signal_nets
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
OUT=os.environ.get("R4OUT","r4_gb2.txt")
def emit(s=""):
    with io.open(OUT,"a",encoding="utf-8") as f: f.write(s+"\n")
    print(s)
if os.path.exists(OUT): os.remove(OUT)

SIZING4 = EXISTING4

def low_z(c, n, ag, S, fold_mirror):
    """impedance class '낮음' (rule 6): a gm-order conductance terminal sits on n."""
    src_acg = [x["name"] for x in c.devs if x["source"]==n and x["gate"] in ag]
    diode   = [x["name"] for x in c.devs if x["drain"]==n and x["gate"]==n]
    if fold_mirror:
        diode = []          # reading R4: a diode mirror input node continues the same stage
    return (src_acg + diode), bool(src_acg or diode)

def blocks(c, excit, ag, S, cells, dt, fold_mirror):
    out=[]
    for x in c.devs:
        k=cells.get(x["name"],"")
        is_cs = k.startswith("CS")
        is_vcg = (k=="CG" and dt.get(x["source"],{}).get("t","").startswith("voltage"))
        if not (is_cs or is_vcg): continue
        node = x["drain"]; chain=[x["name"]]; guard=0
        while guard<20:
            guard+=1
            nxt=[y for y in c.devs if y["source"]==node and cells.get(y["name"])=="CG"
                 and dt.get(node,{}).get("t","").startswith("current")]
            if not nxt: break
            node = nxt[0]["drain"]; chain.append(nxt[0]["name"])
        ev,lo = low_z(c,node,ag,S,fold_mirror)
        out.append(dict(start=x["name"], kind="CS" if is_cs else "vCG",
                        outnode=node, chain=chain, lowz=lo, lowz_ev=ev))
    return out

emit("### 블록(규칙 5·6) 구성과 규칙 9 (c) -- 블록 출력노드 기준")
summary={}
for n in CIRCUITS:
    c=C(n); vs=default_views(c)
    if not vs: continue
    _,excit=vs[0]; ag,_=R.acground_fixpoint(c,excit)
    S,cells,bundles,notes=R.classify_cells(c,excit,ag)
    fwd,_=R.forward_nets(c,excit,ag,S)
    dt=R.driving_types(c,excit,ag,S,cells)
    row={}
    for lbl,fold in (("R5-literal",False),("R4-mirror-folded",True)):
        bl=blocks(c,excit,ag,S,cells,dt,fold)
        bad=[b for b in bl if b["kind"]=="CS" and b["lowz"]]
        row[lbl]=(len(bl),[b["start"]+"->"+b["outnode"] for b in bad])
    ro=R.record_only_branches(c,excit,ag,S,cells,dt,bundles,notes)
    taps=[x for x in S if dt[x]["t"]=="TAP->rule9(a)"]
    nine_a=sorted(ro.get("9a_CS_on_tap",[]))
    dual=sorted(ro.get("cell_CS_CD_dual",[]))
    undet=[x for x in S if dt[x]["t"]=="undetermined"]
    emit("")
    emit("%s" % n)
    for lbl in ("R5-literal","R4-mirror-folded"):
        emit("   blocks=%d  9(c) 발동=%d %s   [%s]"%(row[lbl][0],len(row[lbl][1]),row[lbl][1],lbl))
    emit("   9(a) 발동(TAP gate CS)=%d %s  TAP노드=%s"%(len(nine_a),nine_a,taps))
    emit("   CS/CD 이중출력 review_needed=%d %s"%(len(dual),dual))
    emit("   구동 종류 미정의 신호넷=%s"%undet)
    summary[n]=dict(a=len(nine_a),c5=len(row["R5-literal"][1]),c4=len(row["R4-mirror-folded"][1]),
                    dual=len(dual),undet=len(undet))

emit("")
emit("### GB2 정지 요약 (기록만 분기 하나라도 있으면 DEC-59 탐색 전 정지)")
emit("%-30s %5s %5s %5s %5s %6s | %s"%("circuit","9(a)","9c-R5","9c-R4","dual","undef","정지?(R5 / R4)"))
for n in CIRCUITS:
    if n not in summary: continue
    s=summary[n]
    stopR5 = s["a"]+s["c5"]+s["dual"]>0
    stopR4 = s["a"]+s["c4"]+s["dual"]>0
    emit("%-30s %5d %5d %5d %5d %6d | %s / %s"%(n,s["a"],s["c5"],s["c4"],s["dual"],s["undet"],
        "STOP" if stopR5 else "pass","STOP" if stopR4 else "pass"))
emit("")
emit("사이징 스펙 4회로 GB2 무정지 통과 수: R5-literal=%d / R4-mirror=%d"%(
    sum(1 for n in SIZING4 if summary.get(n) and summary[n]["a"]+summary[n]["c5"]+summary[n]["dual"]==0),
    sum(1 for n in SIZING4 if summary.get(n) and summary[n]["a"]+summary[n]["c4"]+summary[n]["dual"]==0)))
