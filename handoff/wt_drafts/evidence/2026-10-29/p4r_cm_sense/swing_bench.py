"""범위 끝(Vod = +-1.2 V) 상태에서 R의 역할: 개루프 DC 차동 sweep(파일럿 swing bench 와 같은 구동) ->
Vod(Vid), 국소 이득 dVod/dVid, 할선 이득 Vod/Vid, R 가지 DC 전류 (Vop-Vom)/(R1+R2), 출력단 M15/M16/M25/M26 전류.
정적 오차 추정 eps_end ~ 1/(beta*A_sec(Vod_end)), beta = T0/A0 (lg bench 값, results.jsonl)."""
import os, re, subprocess, json, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RUN = os.path.join(HERE, 'runs')
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
base = open(os.path.join(HERE, 'base_pilot_r1_lg.cir'), encoding='utf-8').read().split('.control')[0]
OUT = os.path.join(HERE, 'swing_results.jsonl')
VOD_END = 1.2   # spec swing_out_v 2.4 (차동 p-p) -> +-1.2 V


def build(R):
    lines = []
    for l in base.split('\n'):
        low = l.lower()
        if low.startswith('r1 ') or low.startswith('r2 ') or low.startswith('vtp ') or low.startswith('vtm '):
            continue
        lines.append(l)
    lines += [f'r1 Vom Voc {R:.6e}', f'r2 Voc Vop {R:.6e}',
              'vdpc vdp_ctl 0 dc 0', 'edp Vip_g Vip vdp_ctl 0 0.5', 'edm Vim_g Vim vdp_ctl 0 -0.5']
    tag = f'swing_R{R:.0e}'.replace('+', '')
    f = os.path.join(RUN, tag + '_dc.txt').replace('\\', '/')
    ctl = ['.control', 'op', 'dc vdpc -8m 8m 0.02m',
           f'wrdata {f} v(Vop)-v(Vom) (v(Vop)-v(Vom))/{2*R:.6e} @m.xm15.msky130_fd_pr__pfet_01v8[id] @m.xm16.msky130_fd_pr__nfet_01v8[id] '
           '@m.xm25.msky130_fd_pr__pfet_01v8[id] @m.xm26.msky130_fd_pr__nfet_01v8[id] '
           '@m.xm15.msky130_fd_pr__pfet_01v8[vds] @m.xm15.msky130_fd_pr__pfet_01v8[vdsat] @m.xm16.msky130_fd_pr__nfet_01v8[vds] @m.xm16.msky130_fd_pr__nfet_01v8[vdsat]',
           'quit', '.endc', '.end']
    p = os.path.join(RUN, tag + '.cir')
    open(p, 'w', encoding='utf-8').write('\n'.join(lines + ctl) + '\n')
    return p, f


def main(Rs, beta):
    for R in Rs:
        p, f = build(R)
        r = subprocess.run([NG, '-b', p], capture_output=True, text=True, cwd=RUN)
        open(p.replace('.cir', '.log'), 'w', encoding='utf-8').write(r.stdout + r.stderr)
        d = np.loadtxt(f)
        vid = d[:, 0]; vod = d[:, 1]; ir = d[:, 3]
        id15, id16, id25, id26 = d[:, 5], d[:, 7], d[:, 9], d[:, 11]
        rec = dict(R=R)
        i0 = int(np.argmin(np.abs(vid)))
        for sgn, name in ((1, 'pos'), (-1, 'neg')):
            target = sgn * VOD_END
            if (sgn > 0 and vod.max() < target) or (sgn < 0 and vod.min() > target):
                rec[name] = dict(reached=False, vod_extreme=float(vod.max() if sgn > 0 else vod.min()))
                continue
            k = int(np.argmin(np.abs(vod - target)))
            a_loc = float(np.gradient(vod, vid)[k])
            a_sec = float((vod[k] - vod[i0]) / (vid[k] - vid[i0]))
            rec[name] = dict(reached=True, vid_mv=float(vid[k] * 1e3), vod=float(vod[k]), A_loc_db=20 * np.log10(abs(a_loc)),
                             A_sec_db=20 * np.log10(abs(a_sec)), eps_end_pct=100 / (1 + beta * abs(a_sec)),
                             I_R_uA=float(ir[k] * 1e6), I15_uA=float(-id15[k] * 1e6) if id15[k] < 0 else float(id15[k] * 1e6),
                             I16_uA=float(id16[k] * 1e6), I25_uA=float(abs(id25[k]) * 1e6), I26_uA=float(id26[k] * 1e6))
        rec['A0_db'] = 20 * np.log10(abs(np.gradient(vod, vid)[i0]))
        open(OUT, 'a', encoding='utf-8').write(json.dumps(rec) + '\n')
        print(json.dumps(rec))


if __name__ == '__main__':
    main([float(x) for x in sys.argv[1].split(',')], float(sys.argv[2]))
