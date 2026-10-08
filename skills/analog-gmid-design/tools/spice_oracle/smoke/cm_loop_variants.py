"""연속시간 CMFB 변형 5종 -- 출력 포트 CM 주입 T_cm: 엔진(ledger cm_output) 대 ngspice 선형(같은 소신호 값) + PM (metrics CONTRACT 7.11).
합성 소신호 회로(코어: 차동쌍 + PMOS 부하 + 꼬리, CM 제어 = 부하 gate vc). 변형: (1) R 평균 -> 오차 증폭 2단, (2) 소스 팔로어 버퍼 -> R 평균, (3) DDA,
(4) triode MOS 평균, (5) 감지 넷에 기준 R·C. 사용: WORK=<임시 폴더> python cm_loop_variants.py -- 표를 JSON 으로 낸다."""
import sys, os, subprocess, math, json
import numpy
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'spice_oracle'))
from gmid_engine.metrics import ss_metrics as sm
from gmid_engine.metrics.records import MosSmallSignal, Resistor, Capacitor, SmallSignalCircuit
from gmid_engine.metrics.ss_types import SsCircuit, MetricRequest
from gmid_engine.authoring import ViewDecl, ROLE_DIFFERENTIAL_OUTPUT_P, ROLE_DIFFERENTIAL_OUTPUT_N
from oracle_simulate import loop_gain, ac_measures, nyquist_count
EXE = 'C:/ngspice/Spice64/bin/ngspice_con.exe'
WORK = os.environ.get('WORK', os.environ['TEMP'])
GROUND = ('gnd', 'vdd', 'vb', 'vref')
INPUTS = ('in1', 'in2')
OUT = ('om', 'op')


def mos(name, d, g, s, gm, gds=1e-5, cgs=5e-14, cgd=1e-14, cgb=0.0, cdb=1e-14, csb=1e-14, gmb=0.0):
    return dict(name=name, d=d, g=g, s=s, b='gnd', gm=gm, gmb=gmb, gds=gds, cgs=cgs, cgd=cgd, cgb=cgb, cdb=cdb, csb=csb)


def core():
    m = [mos('Mn1', 'op', 'in1', 'tail', 1e-3), mos('Mn2', 'om', 'in2', 'tail', 1e-3),
         mos('M0', 'tail', 'vb', 'gnd', 1e-3, 2e-5),
         mos('Mp1', 'op', 'vc', 'vdd', 2e-5), mos('Mp2', 'om', 'vc', 'vdd', 2e-5)]
    c = [('CL1', 'op', 'gnd', 1e-12), ('CL2', 'om', 'gnd', 1e-12)]
    return m, [], c


def chain(first_in, tag='e'):
    """오차 증폭 사슬: first_in(감지 넷) -> Mea1 -> vc1 -> Mea2 -> vc (반전 2 + 액추에이터 Mp 반전 1 = 음되먹임)."""
    m = [mos('Mea1', 'vc1', first_in, 'gnd', 5e-4), mos('Mdl1', 'vc1', 'vc1', 'vdd', 2e-4),
         mos('Mea2', 'vc', 'vc1', 'gnd', 5e-4), mos('Mdl2', 'vc', 'vc', 'vdd', 2e-4)]
    c = [('Cvc', 'vc', 'gnd', 5e-14), ('Cvc1', 'vc1', 'gnd', 5e-14)]
    return m, [], c


def merge(*parts):
    return [sum((p[i] for p in parts), []) for i in range(3)]


def v1():
    avg = ([], [('R1', 'op', 'vs', 1e5), ('R2', 'vs', 'om', 1e5)], [])
    return merge(core(), avg, chain('vs'))


def v2():
    sf = ([mos('Msf1', 'vdd', 'op', 'bp', 1e-3), mos('Msf2', 'vdd', 'om', 'bm', 1e-3)], [('R1', 'bp', 'vs', 1e5), ('R2', 'vs', 'bm', 1e5)], [])
    return merge(core(), sf, chain('vs'))


def v3():
    dda = ([mos('Ma1', 'n1', 'op', 'ta', 5e-4), mos('Ma2', 'n2', 'vref', 'ta', 5e-4), mos('Mb1', 'n1', 'om', 'tb', 5e-4),
            mos('Mb2', 'n2', 'vref', 'tb', 5e-4), mos('Mta', 'ta', 'vb', 'gnd', 1e-3, 2e-5), mos('Mtb', 'tb', 'vb', 'gnd', 1e-3, 2e-5),
            mos('Ml1', 'n1', 'n1', 'vdd', 2e-4), mos('Ml2', 'n2', 'n2', 'vdd', 2e-4),
            mos('Mea2', 'vc', 'n1', 'gnd', 5e-4), mos('Mdl2', 'vc', 'vc', 'vdd', 2e-4)], [], [('Cvc', 'vc', 'gnd', 5e-14), ('Cn1', 'n1', 'gnd', 5e-14)])
    return merge(core(), dda)


def v4():
    tri = ([mos('Mt1', 'op', 'vref', 'vs', 2e-6, 1e-5), mos('Mt2', 'om', 'vref', 'vs', 2e-6, 1e-5)], [], [])
    return merge(core(), tri, chain('vs'))


def v5():
    avg = ([], [('R1', 'op', 'vs', 1e5), ('R2', 'vs', 'om', 1e5), ('Rref', 'vs', 'vref', 1e6)], [('Cs', 'vs', 'gnd', 1e-13)])
    return merge(core(), avg, chain('vs'))


VARIANTS = {'1 R평균->오차증폭': v1, '2 SF버퍼->R평균': v2, '3 DDA': v3, '4 triode평균': v4, '5 감지넷 기준R·C': v5}


def engine_side(m, r, c):
    nets = sorted({n for x in m for n in (x['d'], x['g'], x['s'], x['b'])} | {n for x in r + c for n in x[1:3]} | set(GROUND) | set(INPUTS) | set(OUT))
    ix = {n: i for i, n in enumerate(nets)}
    mm = tuple(MosSmallSignal(ix[x['d']], ix[x['g']], ix[x['s']], ix[x['b']], x['gm'], x['gmb'], x['gds'], x['cgs'], x['cgd'], x['cgb'], x['cdb'], x['csb'], label=x['name']) for x in m)
    rr = tuple(Resistor(ix[a], ix[b], v, label=n) for n, a, b, v in r)
    cc = tuple(Capacitor(ix[a], ix[b], v, label=n) for n, a, b, v in c)
    ss = SsCircuit(tuple(nets), SmallSignalCircuit(mm, rr, cc), tuple(n for n, *_ in r), tuple(n for n, *_ in c), tuple(sorted(GROUND)), tuple(sorted(INPUTS)))
    view = sm._cm_report_view(((OUT[0], ROLE_DIFFERENTIAL_OUTPUT_N), (OUT[1], ROLE_DIFFERENTIAL_OUTPUT_P)))
    ledger = sm._Ledger(ss)
    cuts = ledger.cm_cuts(view)
    plan = sm._plan(MetricRequest('', view), ledger)
    responses, cutmap = ledger.solve()
    analysis, _ = sm._analysis(plan, responses, cutmap)
    reports, warns = sm._cm_report(analysis, view, False)
    factor = sm._analysis(plan, responses, cutmap)[1][0]
    return analysis, dict(reports[0][1]), warns, cuts, ss, factor


def linear_ng(m, r, c, tag, outs=None, passives_moved=True):
    outs = list(outs or OUT)
    w = 1 / len(outs)
    moved_r = set()
    moved_c = set()
    L = ['* variant ' + tag]
    nn = lambda n: '0' if n == 'gnd' else n
    for x in m:
        d, g, s, b = nn(x['d']), nn(x['g']), nn(x['s']), nn(x['b'])
        ends = [t for t in ('d', 's') if x[t] in outs]
        if len(ends) == 1:                      # 구동자(channel 단자)를 x 로
            if ends[0] == 'd':
                d = 'lbx_' + d
            else:
                s = 'lbx_' + s
        L += [f"Gm_{x['name']} {d} {s} {g} {s} {x['gm']}", f"Gb_{x['name']} {d} {s} {b} {s} {x['gmb'] or 1e-30}", f"Gd_{x['name']} {d} {s} {d} {s} {x['gds']}"]
        for nm, p, q, val in (('gs', g, s, x['cgs']), ('gd', g, d, x['cgd']), ('gb', g, b, x['cgb']), ('db', d, b, x['cdb']), ('sb', s, b, x['csb'])):
            if val:
                L.append(f'C{nm}_{x["name"]} {p} {q} {val}')
    for kind, items, moved in (('R', r, moved_r), ('C', c, moved_c)):
        for n, a, b, v in items:
            A, B = nn(a), nn(b)
            if n in moved:
                A = 'lbx_' + A if a in outs else A
                B = 'lbx_' + B if b in outs else B
            L.append(f'{kind}{n} {A} {B} {v}')
    L.append('Vvdd vdd 0 0')
    L += [f'Vvb vb 0 0', f'Vvref vref 0 0'] + [f'Vin_{n} {n} 0 0' for n in INPUTS]
    for n in outs:
        L += [f'Vlb_{n} {n} lbx_{n} DC 0 AC {w}', f'Ilb_{n} 0 {n} DC 0 AC 0']
    pre = os.path.join(WORK, 'var_' + tag)
    ac = 'ac dec 40 1 1e11'
    L += ['.control', 'set noaskquit', 'set wr_singlescale', ac, f'wrdata {pre}.v.txt ' + ' '.join(f'v(lbx_{n}) v({n})' for n in outs)]
    L += [x for n in outs for x in (f'alter @vlb_{n.lower()}[acmag] = 0', f'alter @ilb_{n.lower()}[acmag] = {w}')]
    L += [ac, f'wrdata {pre}.i.txt ' + ' '.join(f'i(vlb_{n.lower()})' for n in outs) + ''.join(f' v({n})' for n in outs), 'quit', '.endc', '.end']
    open(pre + '.cir', 'w').write('\n'.join(L) + '\n')
    subprocess.run([EXE, '-b', pre + '.cir'], capture_output=True)
    f, re_, im = loop_gain(pre + '.v.txt', pre + '.i.txt', [w] * len(outs))
    return numpy.array(f), numpy.array(re_) + 1j * numpy.array(im)


def main():
    from gmid_engine.metrics._helpers_product import product_at
    rows = []
    for name, build in VARIANTS.items():
        m, r, c = build()
        analysis, rep, warns, cuts, ss, factor = engine_side(m, r, c)
        f, T = linear_ng(m, r, c, name.split()[0])
        T_eng = numpy.array([product_at((factor,), 2 * math.pi * float(x))[0] for x in f])
        sel = numpy.abs(T) > 1e-3        # 잡음 바닥(ngspice wrdata 유효숫자) 아래 표본은 뺀다
        ddb = numpy.max(numpy.abs(20 * numpy.log10(numpy.abs(T_eng[sel]) / numpy.abs(T[sel])))) if sel.any() else float('nan')
        ddeg = numpy.max(numpy.abs(numpy.degrees(numpy.angle(T_eng[sel] / T[sel])))) if sel.any() else float('nan')
        mng = ac_measures(f, T.real, T.imag)
        rows.append(dict(variant=name, cuts=len(cuts), dc_db=rep['dc_db'], ugf_hz=rep['ugf_hz'], pm_deg=rep['pm_deg'], undefined=rep['undefined'],
                         warn=[w[0] for w in warns], ng_dc_db=mng['dc_gain_db'], ng_ugf=mng['ugf_hz'], ng_pm=mng['pm_deg'],
                         max_db=float(ddb), max_deg=float(ddeg),
                         poles_rhp=[complex(p) for p in factor.poles if p.real > 0][:3]))
        print(json.dumps(rows[-1], default=str, ensure_ascii=False))
    json.dump(rows, open(os.path.join(WORK, 'variants.json'), 'w', encoding='utf-8'), default=str, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
