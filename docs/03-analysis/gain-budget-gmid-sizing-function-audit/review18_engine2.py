# -*- coding: utf-8 -*-
"""engine v2 patches: ambiguity-aware measurements (two readings side by side)."""
import os, sys, json, itertools, collections
import networkx as nx
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import *   # noqa
import engine as E

# ---------------------------------------------------------------- columns on MULTIgraph
def columns_multi(c):
    G = dc_graph(c, prune_leaf_resistors=True)
    rails = set(c.supply_nets or []) & set(G.nodes())
    Gs = nx.Graph()
    mult = collections.Counter()
    for u, v, k in G.edges(keys=True):
        Gs.add_edge(u, v)
        mult[tuple(sorted((u, v)))] += 1
    total = 0
    per = collections.Counter()
    for a, b in itertools.combinations(sorted(rails), 2):
        if a not in Gs or b not in Gs:
            continue
        n = 0
        for p in nx.all_simple_paths(Gs, a, b):
            prod = 1
            for i in range(len(p) - 1):
                prod *= mult[tuple(sorted((p[i], p[i + 1])))]
            n += prod
        per[(a, b)] = n
        total += n
    return total, per

# ---------------------------------------------------------------- driving types v2
def driving_types2(c, view, S, acg, fwd, cells, pass_mode="none"):
    """pass_mode: 'none'(pass 출력 단자는 구동 진입으로 세지 않음) /
                  'drain'(용어집 문장 그대로 pass 소자의 drain 단자 = 전류 진입) /
                  'propagate'(pass 묶음 반대편 노드의 구동 종류를 물려받음)"""
    dev = {t["name"]: t for t in c.devs}
    cur_in = collections.defaultdict(list)
    volt_in = collections.defaultdict(list)
    res_in = collections.defaultdict(list)
    pass_link = collections.defaultdict(list)
    for n, v in cells.items():
        t = dev[n]
        cl = v["cls"]
        if cl in ("CS", "CG") and t["d"] in S:
            cur_in[t["d"]].append(n)
        if cl == "CD" and t["s"] in S:
            volt_in[t["s"]].append(n)
        if cl == "CS" and t["s"] in S and t["s"] not in acg:
            volt_in[t["s"]].append(n + "(CS source)")
        if cl == "pass":
            if t["d"] in S and t["s"] in S:
                pass_link[t["d"]].append((n, t["s"]))
                pass_link[t["s"]].append((n, t["d"]))
                if pass_mode == "drain":
                    cur_in[t["d"]].append(n + "(pass drain)")
    for p in c.pas:
        if p["kind"] == "resistor" and len(p["t"]) == 2:
            for a, b in ((p["t"][0], p["t"][1]), (p["t"][1], p["t"][0])):
                if a in S and b in S:
                    res_in[a].append((p["name"], b))
    for i in view["excite"]:
        volt_in[i].append("<input port>")

    def exits(k):
        eg = [t["name"] for t in c.devs if t["g"] == k and cells.get(t["name"], {}).get("cls") in ("CS", "CD")]
        ec = [t["name"] for t in c.devs if t["s"] == k and t["d"] in S and cells.get(t["name"], {}).get("cls") in ("CG", "CS")]
        for n, other in pass_link[k]:
            ec.append(n + "(pass)")
        return eg, ec

    def priority(k, val_dep, why):
        eg, ec = exits(k)
        if eg and not ec:
            return {"type": "voltage", "value_dep": val_dep, "why": why + f"; 배출 gate뿐 {eg}"}
        if ec and not eg:
            return {"type": "current", "value_dep": val_dep, "why": why + "; 배출 채널뿐"}
        if eg and ec:
            gf = []
            for x in eg:
                t = dev[x]; cl = cells[x]["cls"]
                o = t["d"] if cl in ("CS", "CG") else (t["s"] if cl == "CD" else None)
                if o and o in fwd:
                    gf.append(x)
            if gf:
                return {"type": "voltage", "value_dep": val_dep, "why": why + f"; gate·채널 동시, gate측 순방향 {gf}"}
            return {"type": "current", "value_dep": val_dep, "why": why + "; gate·채널 동시, gate측 순방향 아님 -> tap(9a)",
                    "tap": eg}
        return {"type": "current", "value_dep": val_dep, "why": why + "; 배출 없음(종단)"}

    out = {}
    for k in sorted(S):
        has_c, has_v, has_r = bool(cur_in[k]), bool(volt_in[k]), bool(res_in[k])
        if has_c and has_v:
            lat = all(E.is_lateral_injection(c, cells, dev[x.split("(")[0]], S, acg, fwd)
                      for x in cur_in[k] if x.split("(")[0] in dev)
            out[k] = {"type": "voltage", "value_dep": has_r,
                      "why": f"혼재 우선(전압 {volt_in[k]} + drain {cur_in[k]})",
                      "flag": None if lat else "review_needed(혼재: drain 쪽 측면 주입 아님)"}
        elif has_c:
            out[k] = priority(k, has_r, f"전류 진입 {cur_in[k]}")
        elif has_v:
            out[k] = {"type": "voltage", "value_dep": has_r, "why": f"{volt_in[k]}"}
        elif has_r:
            out[k] = {"type": "inherit", "value_dep": True, "why": f"저항 진입만 {res_in[k]}"}
        else:
            out[k] = {"type": "undefined", "value_dep": False, "why": "신호 진입 단자 없음"}
    # inheritance then RE-APPLY priority (plan: "상속·혼합으로 전류 진입이 붙은 노드도 최종 구동 종류는 위 우선순위가 가른다")
    for _ in range(len(S) + 2):
        moved = False
        for k, v in out.items():
            if v["type"] == "inherit":
                cand = [out[b]["type"] for (_n, b) in res_in[k] if b in out and out[b]["type"] in ("voltage", "current")]
                if cand:
                    if "current" in cand:
                        nv = priority(k, True, v["why"] + f" -> 상속 current")
                        out[k] = nv
                    else:
                        v["type"] = "voltage"; v["why"] += " -> 상속 voltage"
                    moved = True
        if not moved:
            break
    # pass propagation reading
    if pass_mode == "propagate":
        for _ in range(4):
            for k, v in out.items():
                if v["type"] == "undefined":
                    for n, other in pass_link[k]:
                        if out.get(other, {}).get("type") in ("voltage", "current"):
                            out[k] = {"type": out[other]["type"], "value_dep": v["value_dep"],
                                      "why": f"pass 묶음 {n} 반대편 {other}에서 전파"}
    for k, v in out.items():
        if v["type"] == "inherit":
            v["type"] = "review_needed"; v["why"] += " -> 순환/미정"
    return out, cur_in, volt_in, res_in, pass_link

# ---------------------------------------------------------------- blocks
def build_blocks(c, view, S, acg, fwd, cells, drv, dcr):
    """규칙 5·6: starter 셀에서 출력노드까지 따라가 이득 블록을 만든다."""
    dev = {t["name"]: t for t in c.devs}
    starters = []
    notes = []
    for n, v in cells.items():
        t = dev[n]
        if not v.get("fwd"):
            continue
        cl = v["cls"]
        if cl == "CS":
            dt = drv.get(t["g"], {}).get("type")
            if dcr.get(n) == "bias_current_source":
                notes.append((n, "규칙5 예외: DC 역할 바이어스 전류원"))
            elif dt == "voltage":
                starters.append((n, "CS", t["g"], t["d"]))
            elif dt == "current":
                notes.append((n, f"9(a) 후보: gate {t['g']} 전류 구동"))
            else:
                notes.append((n, f"미정: gate {t['g']} 구동종류 {dt}"))
        elif cl == "CG":
            dt = drv.get(t["s"], {}).get("type")
            if dt == "voltage":
                starters.append((n, "CG(전압구동)", t["s"], t["d"]))
            elif dt != "current":
                notes.append((n, f"미정: CG source {t['s']} 구동종류 {dt}"))
    blocks = []
    for (n, kind, innet, outstart) in starters:
        node = outstart
        members = [n]
        seen = {node}
        while True:
            if node in view["sense"]:
                break
            nxt = None
            for u in c.devs:
                cl = cells.get(u["name"], {}).get("cls")
                if cl == "CG" and u["s"] == node and drv.get(node, {}).get("type") == "current":
                    nxt = (u["name"], u["d"])
                    break
                if cl == "pass" and node in (u["d"], u["s"]):
                    other = u["s"] if u["d"] == node else u["d"]
                    if other not in seen:
                        nxt = (u["name"], other)
                        break
            if not nxt:
                break
            members.append(nxt[0]); node = nxt[1]
            if node in seen:
                break
            seen.add(node)
        blocks.append({"start": n, "kind": kind, "in": innet, "out": node, "members": members})
    return blocks, starters, notes

def rule9c_blockbased(c, view, S, acg, fwd, cells, blocks):
    diode_nets = {t["d"] for t in c.devs if t["g"] == t["d"]}
    hits = []
    for b in blocks:
        if not b["kind"].startswith("CS"):
            continue
        k = b["out"]
        if k not in fwd:
            continue
        low = E.impedance_low(c, k, acg, cells)
        if not low:
            continue
        if k in diode_nets:
            readers = [u for u in c.devs if u["g"] == k and u["g"] != u["d"]]
            mo = []
            for u in readers:
                cl = cells.get(u["name"], {}).get("cls")
                o = u["d"] if cl in ("CS", "CG") else (u["s"] if cl == "CD" else u["d"])
                if o in fwd:
                    mo.append(u["name"])
            if mo:
                continue
        hits.append({"block_start": b["start"], "out": k, "why": low})
    return hits

# ---------------------------------------------------------------- DEC-63 buffer bundles
def buffer_bundles(c, view, S, acg, fwd, cells, drv, blocks):
    dev = {t["name"]: t for t in c.devs}
    us = set(view["excite"]) | {b["out"] for b in blocks}
    out = []
    for u in sorted(us):
        R, frontier = set(), [u]
        used = []
        while frontier:
            x = frontier.pop()
            for t in c.devs:
                if cells.get(t["name"], {}).get("cls") == "CD" and t["g"] == x:
                    if t["s"] not in R:
                        R.add(t["s"]); frontier.append(t["s"]); used.append(t["name"])
        if not R:
            continue
        cd_inputs = {t["g"] for t in c.devs if cells.get(t["name"], {}).get("cls") == "CD"}
        term = sorted(n for n in R if n not in cd_inputs)
        out.append({"u": u, "R": sorted(R), "cells": sorted(set(used)),
                    "merge": term, "status": "계산 규칙 있음" if len(term) == 1 else "기록만(다출력 버퍼)"})
    return out
