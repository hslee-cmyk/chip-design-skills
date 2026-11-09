# DEC-95 (3): kvl_branch 밖 비트리 관계(equal_vgs: 같은 kind·gate·source MOS 묶음)의 종속 멤버 선택에서 이름 키
import sys, random, collections, json
import common
from common import *
common.ROLEMODE = sys.argv[1] if len(sys.argv) > 1 else "family"
rng = random.Random(11)
RES = OUT + f"/results_rules3_{common.ROLEMODE}.jsonl"

def an(M):
    G = build_graph(M); wl = wl_refine(G, {v: G.nodes[v]["base"] for v in G})
    orb, _ = orbits(G, wl); pos, _ = canon_positions(G, wl); return G, wl, orb, pos

def groups(M):
    g = collections.defaultdict(list)
    for k, m in M.mos.items(): g[(m["kind"], m["g"], m["s"])].append(k)
    return [sorted(v) for v in g.values() if len(v) > 1]

def select(M, G, wl, pos, grp, usepos=True):
    """독립 유지 멤버: diode 우선 -> (GB5/stage: 측정 불가, 생략) -> wl 최소(궤도 대표 구조색) -> 정준 위치 / 이름."""
    d = [x for x in grp if M.mos[x]["d"] == M.mos[x]["g"]] or grp
    return min(d, key=lambda x: (wl["D:" + x], pos["D:" + x] if usepos else 0, x))

for c in circuits():
    M = load(c); G, wl, orb, pos = an(M); gs = groups(M)
    rec = dict(circuit=c, groups=len(gs), detail=[])
    nm_old = nm_same = nm_multi = 0   # 옛 규칙(이름)이 도달하는 묶음: diode 뒤에도 후보>1
    for g in gs:
        d = [x for x in g if M.mos[x]["d"] == M.mos[x]["g"]] or g
        if len(d) > 1:
            nm_old += 1
            o = len({orb["D:" + x] for x in d})
            # 궤도 대표(구조색 wl) 단계 뒤에도 동점인가
            mw = min(wl["D:" + x] for x in d); rest = [x for x in d if wl["D:" + x] == mw]
            ro = len({orb["D:" + x] for x in rest})
            rec["detail"].append(dict(members=g, after_diode=d, orbits_after_diode=o, tie_after_orbit_rep=len(rest), orbits_in_tie=ro))
            if len(rest) > 1: (nm_same if ro == 1 else nm_multi).__class__
            if len(rest) > 1:
                if ro == 1: nm_same += 1
                else: nm_multi += 1
    rec.update(old_name_reachable=nm_old, tie_after_orbit_rep_same_orbit=nm_same, tie_after_orbit_rep_multi_orbit=nm_multi)
    dep = lambda M_, G_, wl_, pos_, up=True: frozenset("D:" + x for gg in groups(M_) for x in gg if x != select(M_, G_, wl_, pos_, gg, up))
    base = dep(M, G, wl, pos)
    rec["dep_count"] = len(base)
    meta = []
    for _ in range(3):
        pd, pn = random_rename(M, rng); inv = {v: k for k, v in pd.items()}
        M2 = M.rename(pd, pn); G2, wl2, orb2, pos2 = an(M2)
        d2 = dep(M2, G2, wl2, pos2); back = frozenset("D:" + inv[x[2:]] for x in d2)
        meta.append(dict(pos_identical=sorted(pos2[x] for x in d2) == sorted(pos[x] for x in base),
                         same_names=back == base, automorphic=sets_equivalent(G, wl, base, back)))
    rec["meta"] = meta
    # 옛 이름 키(위치 없이 이름 최소)로 재이름 3회
    meta_old = []
    for _ in range(3):
        pd, pn = random_rename(M, rng); inv = {v: k for k, v in pd.items()}
        M2 = M.rename(pd, pn); G2, wl2, orb2, pos2 = an(M2)
        d2 = dep(M2, G2, wl2, pos2, False); back = frozenset("D:" + inv[x[2:]] for x in d2)
        base_old = dep(M, G, wl, pos, False)
        meta_old.append(dict(same_names=back == base_old, automorphic=sets_equivalent(G, wl, base_old, back)))
    rec["meta_name_key_wl_only"] = meta_old
    append(RES, rec); print(c, nm_old, nm_same, nm_multi, flush=True)
