# -*- coding: utf-8 -*-
"""규칙 DEC-70(이름 정렬 전류 기저)·DEC-97 (2)(열 정렬 키) 측정. 케이스마다 results.jsonl 에 append."""
import sys, random, time, json
import common
from common import *
from kcl import *

rolemode = sys.argv[1] if len(sys.argv) > 1 else "family"
common.ROLEMODE = rolemode
only = sys.argv[2:] or circuits()
RES = OUT + f"/results_rules1_{rolemode}.jsonl"
rng = random.Random(20261030)


def analyse(M):
    G = build_graph(M)
    wl = wl_refine(G, {v: G.nodes[v]["base"] for v in G})
    orb, groups = orbits(G, wl)
    pos, leaves = canon_positions(G, wl)
    osize = {v: len(next(g for g in groups if v in g)) for v in G}
    return G, wl, orb, groups, pos, leaves, osize


def keyfun_97(G, wl, pos, osize, name_in=True):
    # (비자명 궤도가 뒤, dc_colour=(wl, 정준 위치) 순위, 이름)
    return lambda c: (1 if osize[c] > 1 else 0, wl[c], pos[c], c if name_in else "")


def free_in_pos(free, pos):
    return tuple(sorted(pos[c] for c in free))


def run(c):
    t0 = time.time()
    M = load(c)
    G, wl, orb, groups, pos, leaves, osize = analyse(M)
    vec = vectors(M)
    cols = sorted(vec)
    ncol = len(cols)
    rec = dict(circuit=c, rolemode=rolemode, n_dev=len(devices(G)), n_cols=ncol, canon_leaves=leaves)
    # ---- 기준: DEC-70 literal (이름 정렬)
    fr70, pv70 = free_set(vec, sorted(cols))
    rec["nullity"] = len(fr70)
    rec["v70_free"] = sorted(x[2:] for x in fr70)
    # 이름 순열 표본: 같은 규칙('이름 정렬')을 다른 이름 전단사 아래에서 적용했을 때의 결과 분포
    outs = {}
    NS = 60
    for i in range(NS):
        pd, pn = random_rename(M, rng)
        inv = {v: k for k, v in pd.items()}
        order = sorted(pd[x[2:]] for x in cols)           # 새 이름의 정렬
        v2 = {"D:" + pd[k[2:]]: val for k, val in vec.items()}
        # 열 이름만 바꾸고 행(넷)은 그대로여도 rank 구조는 같다 -> 열 순서만 중요
        f, _ = free_set({("D:" + pd[k[2:]]): val for k, val in vec.items()}, ["D:" + x for x in order])
        back = frozenset("D:" + inv[x[2:]] for x in f)
        outs[back] = outs.get(back, 0) + 1
    rec["v70_name_perm_samples"] = NS
    rec["v70_distinct_free_sets"] = len(outs)
    # 자기동형 동치류 수
    reps = []
    for s in outs:
        for r in reps:
            if sets_equivalent(G, wl, r, s): break
        else:
            reps.append(s)
    rec["v70_equiv_classes"] = len(reps)
    rec["v70_literal_vs_orbit_basis_same_class"] = None
    # ---- DEC-97 (2): 구조 키 (비자명, wl) 만으로의 동점 = 이름이 도달하는 곳
    skey = {x: (1 if osize[x] > 1 else 0, wl[x]) for x in cols}
    tc = {}
    for x in cols: tc.setdefault(skey[x], []).append(x)
    ties = [m for m in tc.values() if len(m) > 1]
    rec["v97_tie_classes"] = len(ties)
    rec["v97_tie_cols"] = sum(len(m) for m in ties)
    same_orb = [m for m in ties if len({orb[x] for x in m}) == 1]
    rec["v97_ties_single_orbit"] = len(same_orb)
    rec["v97_ties_multi_orbit_WLfail"] = len(ties) - len(same_orb)
    rec["v97_tie_detail"] = [dict(members=[x[2:] for x in m], orbits=len({orb[x] for x in m})) for m in ties]
    # 전체 키(dc_colour 포함) 아래 이름 도달 수: (wl,pos) 유일하므로 0
    dup = len(cols) - len({(wl[x], pos[x]) for x in cols})
    rec["v97_full_key_name_reached"] = dup
    base_order = sorted(cols, key=keyfun_97(G, wl, pos, osize))
    f97, _ = free_set(vec, base_order)
    rec["v97_free"] = sorted(x[2:] for x in f97)
    rec["v97_free_pos"] = list(free_in_pos(f97, pos))
    rec["v97_equiv_v70"] = sets_equivalent(G, wl, fr70, f97)
    # 동점 클래스별: 같은 클래스 안 독립 순열(나머지 고정)에서 결과가 달라지는가, 달라지면 동치인가
    percls = []
    for m in ties:
        outs2 = {}
        for _ in range(40):
            mm = list(m); rng.shuffle(mm)
            order = []
            placed = False
            sk = lambda x: skey[x]
            # 기본 순서에서 이 클래스의 자리만 mm 순으로 치환
            idx = [i for i, x in enumerate(base_order) if x in set(m)]
            order = list(base_order)
            # 클래스 멤버가 비연속이면 자리만 바꿔 넣는다(자리 집합은 같고 키는 동일)
            for i, x in zip(idx, mm): order[i] = x
            f, _ = free_set(vec, order)
            outs2[frozenset(f)] = 1
        reps2 = []
        for s in outs2:
            for r in reps2:
                if sets_equivalent(G, wl, r, s): break
            else:
                reps2.append(s)
        percls.append(dict(members=[x[2:] for x in m], distinct=len(outs2), equiv_classes=len(reps2),
                           same_orbit=len({orb[x] for x in m}) == 1))
    rec["v97_percls"] = percls
    rec["v97_decisive_classes"] = sum(1 for p in percls if p["distinct"] > 1)
    rec["v97_decisive_harmless"] = sum(1 for p in percls if p["distinct"] > 1 and p["equiv_classes"] == 1)
    rec["v97_decisive_inequiv"] = sum(1 for p in percls if p["equiv_classes"] > 1)
    # ---- metamorphic: 이름 전단사 3회, 전 과정을 새로 계산
    mm = []
    for k in range(3):
        pd, pn = random_rename(M, rng)
        inv = {v: kk for kk, v in pd.items()}
        M2 = M.rename(pd, pn)
        G2, wl2, orb2, groups2, pos2, leaves2, osize2 = analyse(M2)
        vec2 = vectors(M2)
        cols2 = sorted(vec2)
        # DEC-97 (2)
        o2 = sorted(cols2, key=keyfun_97(G2, wl2, pos2, osize2))
        f2, _ = free_set(vec2, o2)
        pos_same = free_in_pos(f2, pos2) == free_in_pos(f97, pos)
        back = frozenset("D:" + inv[x[2:]] for x in f2)
        eq = sets_equivalent(G, wl, f97, back)
        ident = back == f97
        # DEC-70 literal
        fl, _ = free_set(vec2, sorted(cols2))
        backl = frozenset("D:" + inv[x[2:]] for x in fl)
        mm.append(dict(
            struct_invariants_same=(sorted(wl2.values()) == sorted(wl.values())) and
                                   sorted(len(g) for g in groups2) == sorted(len(g) for g in groups),
            v97_free_pos_bit_identical=pos_same, v97_free_same_names=ident, v97_free_automorphic=eq,
            v70_free_same_names=(backl == fr70), v70_free_automorphic=sets_equivalent(G, wl, fr70, backl),
        ))
    rec["metamorphic"] = mm
    # 정준 위치 키(이름 대체) 하의 DEC-70 : 열을 dc_colour 만으로 정렬
    posorder = sorted(cols, key=lambda x: (wl[x], pos[x]))
    fp, _ = free_set(vec, posorder)
    rec["v70_with_canon_key_equiv_v97"] = sets_equivalent(G, wl, fp, f97)
    rec["v70_with_canon_key_equal_v97"] = (fp == f97)
    rec["secs"] = round(time.time() - t0, 1)
    return rec


for c in only:
    try:
        r = run(c)
    except Exception as e:
        import traceback
        r = dict(circuit=c, rolemode=rolemode, error=traceback.format_exc())
    append(RES, r)
    print(c, "done", r.get("secs"), r.get("error", "")[:200] if r.get("error") else "", flush=True)
