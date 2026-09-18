import json, sys, collections, os
dc = {json.loads(l)["circuit"]: json.loads(l) for l in open("results3_dc.jsonl", encoding="utf-8")}
out = open("results7_dec59.txt", "a", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.write(s + "\n")
for tag in sys.argv[1:]:
    rows = [json.loads(l) for l in open(f"results2_{tag}.jsonl", encoding="utf-8")]
    br = collections.defaultdict(dict)   # branch -> circuit -> detail
    for r in rows:
        p1, p2 = r["part1"], r["part2"]; c = p1["circuit"]; F = set(p1["forward"])
        cells = p1["cells"]; kind = p1["drive_kind"]
        fwdc = lambda d: d not in p1["cells_offforward"]
        cs_start = [s for s in p1["starts"] if cells[s] in ("CS", "CSCD_review")]
        if cs_start: br["CS stage start [계산]"][c] = (len([s for s in cs_start if fwdc(s)]), [s for s in cs_start if not fwdc(s)])
        if p1["cascode"]: br["cascode CG(전류 구동 source) [계산]"][c] = (len([s for s in p1["cascode"] if fwdc(s)]), [s for s in p1["cascode"] if not fwdc(s)])
        if p1["vcg"]:
            f = [s for s in p1["vcg"] if fwdc(s)]; o = [s for s in p1["vcg"] if not fwdc(s)]
            br["전압 구동 CG stage 시작 [계산]"][c] = (len(f), o)
        if p1["buf_cd"]: br["CD 셀 [계산]"][c] = (len(p1["buf_cd"]), [])
        b1 = [d for d in p2["dec63"] if d["kind"] == "buffer"]; bm = [d for d in p2["dec63"] if d["kind"] != "buffer"]
        if b1: br["버퍼 묶음 단일 합류 DEC-63 [계산]"][c] = (len(b1), [d["u"] for d in b1])
        if bm: br["다출력 버퍼 [기록만]"][c] = (len(bm), [])
        if p1["bundles"]: br["pass 묶음(역병렬 2소자) [계산]"][c] = (len(p1["bundles"]), [])
        if p1["pass3"]: br["pass 3소자+ [기록만]"][c] = (len(p1["pass3"]), [])
        dual = [k for k, v in cells.items() if v == "CSCD_review"]
        if dual: br["CS·CD 이중 출력 [기록만]"][c] = (len(dual), dual)
        if p2["rule9"]["a_forward"] or p2["rule9"]["a"]: br["9(a) [기록만]"][c] = (len(p2["rule9"]["a_forward"]), p2["rule9"]["a"])
        if p2["rule9"]["c"]: br["9(c) [기록만]"][c] = (len(p2["rule9"]["c"]), [x["block"] + "@" + x["out"] for x in p2["rule9"]["c"]])
        mixed = p1["mixed_nodes"]
        mv = [n for n in mixed if kind[n] == "V"]; mj = [n for n in mixed if kind[n] == "REVIEW_J"]; mc = [n for n in mixed if kind[n] == "REVIEW_conflict"]
        if mv: br["혼재 우선→전압 구동 [계산]"][c] = (len(mv), mv)
        if mj: br["혼재 review_needed(J 대기) [기록만]"][c] = (len(mj), mj)
        if mc: br["혼재 충돌 review_needed [기록만]"][c] = (len(mc), mc)
        und = [n for n, k in kind.items() if k.startswith("UNDEF")]
        if und: br["구동 종류 미정의"][c] = (len(und), [f"{n}:{kind[n]}" for n in und])
        tap = [n for n, k in kind.items() if k == "TAP"]
        if tap: br["tap [→9(a)]"][c] = (len(tap), tap)
        if p2["k8"]: br["K8 측면 주입 [계산]"][c] = (len(p2["k8"]), [x["dev"] for x in p2["k8"]])
        if p2["residual_merges"]: br["①로 안 풀린 합류 → DEC-81 (a) 또는 다입력"][c] = (len(p2["residual_merges"]), [m["node"] for m in p2["residual_merges"]])
        cc = collections.Counter()
        for cy in p2["cycles"]:
            for k in cy["klass"].split("|"): cc[k] += 1
        for k, v in cc.items():
            br[f"루프 {k}"][c] = (v, [])
        if p1["rule1_4"]: br["규칙1(4) 바이어스 종속 넷 [계산, J1 ratified]"][c] = (len(p1["rule1_4"]), [x["net"] for x in p1["rule1_4"]])
        ov = p2["block_overlap"]
        if ov: br["규칙6 블록 노드 겹침 review_needed"][c] = (len(ov), [f"{a}/{b}:{','.join(n)}" for a, b, n in ov][:6])
        g = dc[c]["gvgs"]["bfs"]["counts"]
        for k, v in g.items(): br[f"G_vgs {k} [계산]"][c] = (v, [])
        ur = p1["dc_unresolved_groups"]
        if ur: br["DC 역할 못 가름 그룹 review_needed"][c] = (len(ur), [",".join(x["members"]) for x in ur])
    P("########", tag)
    for b in sorted(br):
        d = br[b]
        P(f"  {b}: 발동 {sum(1 for v in d.values() if v[0] > 0)}회로 | " + "; ".join(f"{k}={v[0]}{(' '+str(v[1])) if v[1] else ''}" for k, v in sorted(d.items())))
