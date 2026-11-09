import numpy as np, sys
sys.argv=[sys.argv[0]]
import measure as M
for kind in "np":
    li=list(range(18)); di=[i for i in range(49) if M.VD[i]>=0.3-1e-12]; vi=list(range(10))
    r=M.evaluate(kind,li,di,vi,None)["A"]
    ne=r["nonempty"]
    print(kind,"configs",ne.size,"nonempty",ne.sum(),"left",r["left"].sum(),"differ",r["differ"].sum())
    pk=r["vg_peak"]
    print(" peak VGS unique:",np.unique(np.round(pk,4))[:12], "frac peak>0:",(pk>0).mean())
    for l in range(18):
        sel=r["left"][l]
        if sel.any():
            print("  L",f"{M.LG[l]*1e6:.3g}","left",int(sel.sum()),"/",sel.size," dvgs_peak max",np.nanmax(r["dvgs_peak"][l]),"dg_peak max",np.nanmax(r["dg_peak"][l]), "rel", np.nanmax(r["dg_peak"][l]/ (r["g_peak"][l]-r["dg_peak"][l])))
