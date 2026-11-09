import numpy as np, json, sys
from scipy.interpolate import RegularGridInterpolator as RGI
LUTD='C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/'
F={'nmos':'sky130_fd_pr__nfet_01v8__tt__W1p0000um_dc.npz','pmos':'sky130_fd_pr__pfet_01v8__tt__W1p0000um_dc.npz'}
Z={k:np.load(LUTD+f) for k,f in F.items()}
def q(kind,L,vgs,vds,vsb,col,log=False):
    z=Z[kind]; li=int(np.argmin(abs(z['L']-L)))
    a=z[col][li]; a=np.log(np.maximum(abs(a),1e-30)) if log else a
    v=float(RGI((z['VGS'],z['VDS'],z['VS']),a)([[vgs,vds,vsb]])[0])
    return float(np.exp(v)) if log else v
for name in sys.argv[1:]:
    d=json.load(open('out/%s.devtb.json'%name))
    for m,r in d['devices'].items():
        e=r['engine']; kind='nmos' if 'nfet' in [p for p in d['plan'] if p['device']==m][0]['cell'] else 'pmos'
        idl=q(kind,e['L'],e['vgs'],e['vds'],e['vsb'],'ID',True); exp_eng=e['id']*1e-6/e['W']
        sl=abs(r['spice_dev']['slice']['id'])/1.0
        print(name,m,kind,'npzID %.4e engID@1um %.4e npz/eng %.3f spiceslice/npz %.3f npzVDSAT %.4f engVDSAT %.4f'%(idl,exp_eng,idl/exp_eng,sl/idl,q(kind,e['L'],e['vgs'],e['vds'],e['vsb'],'VDSAT'),e['vdsat'] or -1))
