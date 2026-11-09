import json, collections, sys
sys.dont_write_bytecode = True
recs = [json.loads(l) for l in open('devices_j1b.jsonl', encoding='utf-8')]
IDS = ["1e-07", "1e-06", "1e-05", "0.0001", "0.001"]
VTS = ["D1@t0p1mV", "D1@t1mV", "D1@tLOO", "D2P@t0p1mV", "D2P@t1mV", "D2P@tLOO", "D2"]
def tolof(vt):
    return vt.split("@")[1] if "@" in vt else None
def leak_tables(point="att", bud="none", rule="ga", tols_for_d2=True):
    print(f"\n== 누설 영역 출발 (point={point}, bud={bud}, rule={rule}) 다수(>=50% 설정) n/N  [any>=1 설정]  S|F")
    for vt in VTS:
        tols = [tolof(vt)] if "@" in vt else ["t0p1mV", "t1mV", "tLOO"]
        for tol in tols:
            row = []
            for idc in IDS:
                k = f"{vt}|{rule}|ID{idc}|{bud}"
                cnt = collections.Counter()
                for r in recs:
                    if bud != 'none' and r['budget_m2'] is None: continue
                    c = r['combos'].get(k)
                    if c is None: continue
                    ne = c['sd_nonempty']
                    lk = c['leak_' + point][tol]
                    denom = c['att']['n'] if point == 'att' else c['ts']['n']
                    cnt[(r['cls'], 'N')] += 1
                    if ne == 0: cnt[(r['cls'], 'empty')] += 1; continue
                    if denom and lk >= 0.5 * denom: cnt[(r['cls'], 'maj')] += 1
                    if lk > 0: cnt[(r['cls'], 'any')] += 1
                row.append(f"{cnt[('S','maj')]}/{cnt[('S','N')]}|{cnt[('F','maj')]}/{cnt[('F','N')]} (any {cnt[('S','any')]},{cnt[('F','any')]}; empty {cnt[('S','empty')]},{cnt[('F','empty')]})")
            print(f"{vt:12s} tol={tol:7s}", " ; ".join(row))
if __name__ == '__main__':
    leak_tables('att', 'none', 'ga')
