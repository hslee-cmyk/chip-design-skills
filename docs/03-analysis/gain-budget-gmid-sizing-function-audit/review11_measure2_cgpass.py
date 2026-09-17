# -*- coding: utf-8 -*-
"""CG/pass discriminator per plan v5.18 N3.2-3 ratified wording, vs. the
distance-comparison reading the plan explicitly rejects.

Plan wording (ratified):
  "CG와 pass를 가르는 판별은 두 채널 단자의 도달 거리 비교가 아니라
   '그 소자를 지나지 않고도 닿는가'로 한다: 그 소자의 채널 엣지를 뺀 그래프에서
    drain이 여기로부터 도달하지 못하면 CG, 두 채널 단자가 서로 독립으로 신호를
    받으면 pass"

Appends results to measure2_results.txt (one line per case).
"""
import io
import json
import os
import itertools
from pathlib import Path

LIB = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library")
OUT = Path(__file__).resolve().parent / "measure2_results.txt"


def emit(*parts):
    line = " | ".join(str(p) for p in parts)
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
        f.flush()


def load(fn):
    d = json.load(io.open(LIB / fn, encoding="utf-8"))
    mos = [m for m in d["netlist"] if isinstance(m, dict)]
    pas = [e for e in (d.get("passive_elements") or []) if isinstance(e, dict)]
    return d, mos, pas


def ac_ground_set(d, mos, pas, extra):
    rails = set(d.get("supply_nets") or [])
    driven = set()
    for m in mos:
        driven |= {m["drain"], m["source"]}
    for e in pas:
        driven |= set(e.get("terminals") or [])
    for s in (d.get("ideal_sources") or []):
        driven |= set(s.get("terminals") or [])
    ports = set(k for k in (d.get("ports") or {}) if not k.startswith("_"))
    gate_only = {m["gate"] for m in mos} - driven - ports
    return rails | gate_only | set(extra)


def excitation(d):
    return [n for n, p in (d.get("ports") or {}).items()
            if isinstance(p, dict) and p.get("direction") == "input"]


def outputs(d):
    return [n for n, p in (d.get("ports") or {}).items()
            if isinstance(p, dict) and p.get("direction") == "output"]


def signal_nets(mos, pas, excite, acg):
    sig = {n for n in excite if n not in acg}
    changed = True
    while changed:
        changed = False
        for m in mos:
            add = set()
            if m["gate"] in sig:
                add |= {m["drain"], m["source"]}
            if m["source"] in sig:
                add.add(m["drain"])
            for n in add:
                if n not in acg and n not in sig:
                    sig.add(n)
                    changed = True
        for e in pas:
            t = e.get("terminals") or []
            if len(t) == 2:
                for a, b in ((t[0], t[1]), (t[1], t[0])):
                    if a in sig and b not in acg and b not in sig:
                        sig.add(b)
                        changed = True
    return sig


def back_reach(mos, pas, sig, outs):
    radj = {}

    def add(u, v):
        radj.setdefault(v, set()).add(u)
    for m in mos:
        if m["gate"] in sig:
            add(m["gate"], m["drain"])
            add(m["gate"], m["source"])
        if m["source"] in sig:
            add(m["source"], m["drain"])
    for e in pas:
        t = e.get("terminals") or []
        if len(t) == 2:
            add(t[0], t[1])
            add(t[1], t[0])
    back = set(n for n in outs if n in sig)
    stack = list(back)
    while stack:
        x = stack.pop()
        for y in sorted(radj.get(x, ())):
            if y not in back:
                back.add(y)
                stack.append(y)
    return back


def classify_ratified(d, mos, pas, excite, acg):
    """plan-ratified discriminator"""
    sig = signal_nets(mos, pas, excite, acg)
    cells = {}
    for m in mos:
        g, s, dr, n = m["gate"], m["source"], m["drain"], m["name"]
        if g in sig:
            if dr in acg:
                cells[n] = "CD"
            elif s in acg:
                cells[n] = "CS"
            else:
                cells[n] = "CS(degen)"
            continue
        # gate outside the signal path -> CG / pass / load / off_path
        if s not in sig and dr not in sig:
            cells[n] = "off_path"
            continue
        if s not in sig:
            cells[n] = "load"          # only drain touches a signal node
            continue
        # s in sig: signal can traverse s->d.  Apply the discriminator.
        rest = [x for x in mos if x["name"] != n]
        sig2 = signal_nets(rest, pas, excite, acg)
        if dr not in sig2:
            cells[n] = "CG"            # signal can only get out through this device
        elif s in sig2 and dr in sig2:
            cells[n] = "pass"          # both channel terminals get signal independently
        else:
            cells[n] = "CG"
    return cells, sig


def distances(mos, pas, excite, sig, acg, passive_cost=1):
    edges = []
    for m in mos:
        if m["gate"] in sig:
            edges.append((m["gate"], m["drain"], 1))
            edges.append((m["gate"], m["source"], 0))
        edges.append((m["source"], m["drain"], 0))
    for e in pas:
        t = e.get("terminals") or []
        if len(t) == 2:
            edges += [(t[0], t[1], passive_cost), (t[1], t[0], passive_cost)]
    import collections
    dist = {n: 0 for n in excite if n not in acg}
    dq = collections.deque(sorted(dist))
    adj = {}
    for u, v, w in edges:
        adj.setdefault(u, []).append((v, w))
    while dq:
        u = dq.popleft()
        for v, w in sorted(adj.get(u, [])):
            if v in acg:
                continue
            nd = dist[u] + w
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)
    return dist


def classify_distance(d, mos, pas, excite, acg):
    """the reading the plan explicitly rejects (repo review9 script uses it)"""
    sig = signal_nets(mos, pas, excite, acg)
    dist = distances(mos, pas, excite, sig, acg)
    anti = {}
    for m in mos:
        anti.setdefault(tuple(sorted((m["source"], m["drain"]))), []).append(m)
    cells = {}
    INF = float("inf")
    for m in mos:
        g, s, dr, n = m["gate"], m["source"], m["drain"], m["name"]
        if g in sig:
            cells[n] = "CD" if dr in acg else ("CS" if s in acg else "CS(degen)")
            continue
        if s in sig and dr in sig:
            pair = [x for x in anti[tuple(sorted((s, dr)))] if x["gate"] not in sig]
            if len(pair) == 2 and pair[0]["source"] != pair[1]["source"]:
                cells[n] = "pass"
            elif dist.get(s, INF) <= dist.get(dr, INF):
                cells[n] = "CG"
            else:
                cells[n] = "pass"
        elif s in sig:
            cells[n] = "CG"
        elif dr in sig:
            cells[n] = "load"
        else:
            cells[n] = "off_path"
    return cells, sig


def fwd_filter(mos, pas, cells, sig, outs):
    back = back_reach(mos, pas, sig, outs)
    out = {}
    for m in mos:
        c = cells[m["name"]]
        t = {"CS": m["drain"], "CS(degen)": m["drain"], "CG": m["drain"],
             "CD": m["source"], "pass": m["drain"]}.get(c)
        if t is None:
            continue
        if t in sig and t in back:
            out[m["name"]] = c
    return out


J1 = {"current_reuse_telescopic_ota": {"Vbias2", "Vbias3"}}


def main():
    if OUT.exists():
        OUT.unlink()
    emit("circuit", "reading", "CG_all", "CG_fwd", "pass", "antiparallel_pairs")
    for f in sorted(LIB.glob("*.topology.json")):
        if f.name.startswith("_TEMPLATE"):
            continue
        d, mos, pas = load(f.name)
        name = str(d.get("topology_name"))
        ex = excitation(d)
        outs = outputs(d)
        if not ex:
            emit(name, "SKIP(no input ports)", "", "", "", "")
            continue
        acg = ac_ground_set(d, mos, pas, J1.get(name, set()))
        for label, fn in (("ratified(비지남 도달)", classify_ratified),
                          ("rejected(거리비교)", classify_distance)):
            cells, sig = fn(d, mos, pas, ex, acg)
            fwd = fwd_filter(mos, pas, cells, sig, outs)
            cg_all = sorted(k for k, v in cells.items() if v == "CG")
            cg_fwd = sorted(k for k, v in fwd.items() if v == "CG")
            ps = sorted(k for k, v in cells.items() if v == "pass")
            by = {}
            for m in mos:
                if cells[m["name"]] == "pass":
                    by.setdefault(tuple(sorted((m["source"], m["drain"]))), []).append(m["name"])
            bundles = [v for v in by.values() if len(v) == 2]
            emit(name, label, "%d %s" % (len(cg_all), cg_all),
                 "%d %s" % (len(cg_fwd), cg_fwd), "%d %s" % (len(ps), ps),
                 "%d %s" % (len(bundles), bundles))


if __name__ == "__main__":
    main()
    print("done")
