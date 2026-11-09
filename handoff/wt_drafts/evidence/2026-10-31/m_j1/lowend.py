import sys, numpy as np
sys.argv=[sys.argv[0]]
import measure as M
for k in "np":
    T=M.TAB[k]; di=[i for i in range(49) if M.VD[i]>=0.3-1e-12]
    g=T["g"][...,0][:,di,:]; lnid=T["lnid"][...,0][:,di,:]
    idv=np.exp(lnid)
    print(k,"VGS=0 point: gm/ID min/max",np.nanmin(g),np.nanmax(g),"ID(W_ref 5um) min/max",np.nanmin(idv),np.nanmax(idv), "IDu=ID*L/W_ref range", np.nanmin(idv*M.LG[:,None,None]/5e-6), np.nanmax(idv*M.LG[:,None,None]/5e-6))
