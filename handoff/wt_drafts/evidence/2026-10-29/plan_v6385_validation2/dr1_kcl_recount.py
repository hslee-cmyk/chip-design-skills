"""DR-1 일반형(검증 2) 13회로 재계수: 엔진 dc_current_basis와 같은 정의로 KCL 항등 0 전류 MOS(dead) 집합을 구한다.
- 엣지 = MOS 채널(d-s), 저항, 이상 전류원(값 선언 = fixed 열로 가정). 커패시터 제외.
- 잎 저항 가지치기 = 레일·포트 아닌 넷 중 DC 엣지가 저항 하나뿐(dc_conduction.py 2).
- KCL 행 = 레일이 아닌 넷 전부(포트 포함, current_basis.py와 같음). Fraction RREF.
- dead MOS의 채널 엣지로 연결 성분을 만들고, 성분마다 고정 쪽 후보(레일 또는 live DC 원소가 닿는 넷) 수,
  포트 여부, bulk 조건을 적는다. 연결만 사용(주석·태그 미사용)."""
import json, pathlib, collections
from fractions import Fraction

A = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets")
OUT = pathlib.Path(__file__).with_name("dr1_kcl_recount.txt")
files = [f for f in sorted((A / "library").glob("*.topology.json")) + sorted((A / "heldout").glob("*.topology.json"))
         if not f.name.startswith("_")]


def rref(rows, n):
    piv = []
    r = 0
    for c in range(n):
        p = next((i for i in range(r, len(rows)) if rows[i][c] != 0), None)
        if p is None:
            continue
        rows[r], rows[p] = rows[p], rows[r]
        lead = rows[r][c]
        rows[r] = [x / lead for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c] != 0:
                f = rows[i][c]
                rows[i] = [a - f * b for a, b in zip(rows[i], rows[r])]
        piv.append(c)
        r += 1
    return rows, piv


L = []
total = 0
for f in files:
    t = json.loads(f.read_text(encoding="utf-8"))
    rails = set(t.get("supply_nets", []))
    ports = {k for k in t.get("ports", {}) if not k.startswith("_")}
    edges, cls, bulk = {}, {}, {}
    for m in t["netlist"]:
        edges[m["name"]] = (m["drain"], m["source"])
        cls[m["name"]] = "mos"
        bulk[m["name"]] = m.get("bulk")
    for p in t.get("passive_elements", []):
        if p["kind"] == "resistor":
            edges[p["name"]] = tuple(p["terminals"])
            cls[p["name"]] = "res"
    for s in t.get("ideal_sources", []):
        edges[s["name"]] = tuple(s["terminals"])
        cls[s["name"]] = "src"
    keep = rails | ports
    pruned = set()
    while True:
        at = collections.defaultdict(set)
        for n, (a, b) in edges.items():
            if n in pruned:
                continue
            at[a].add(n)
            at[b].add(n)
        leaf = [net for net in sorted(at) if net not in keep and len(at[net]) == 1
                and cls[next(iter(at[net]))] == "res"]
        if not leaf:
            break
        for net in leaf:
            pruned |= at[net]
    el = [n for n in edges if n not in pruned]
    fixed = [n for n in el if cls[n] == "src"]
    unk = sorted(n for n in el if n not in fixed)
    cols = unk + fixed
    col = {n: i for i, n in enumerate(cols)}
    nets = sorted({x for n in el for x in edges[n]} - rails)
    rows = []
    for net in nets:
        row = [Fraction(0)] * len(cols)
        for n in el:
            a, b = edges[n]
            if a == net:
                row[col[n]] += 1
            if b == net:
                row[col[n]] -= 1
        rows.append(row)
    rows, piv = rref(rows, len(unk))
    free = {unk[c] for c in range(len(unk)) if c not in piv}
    terms = {n: True for n in free}
    terms.update({n: True for n in fixed})
    for i, c in enumerate(piv):
        terms[unk[c]] = any(rows[i][j] != 0 for j in range(len(cols)) if j != c)
    dead = sorted(n for n in el if cls[n] == "mos" and not terms[n])
    total += len(dead)
    L.append(f"== {f.parent.name}/{f.name} rails={sorted(rails)} pruned={sorted(pruned)}")
    L.append(f"   dead MOS (KCL 항등 0) = {dead}")
    if dead:
        live_at = collections.defaultdict(list)
        for n in el:
            if n in dead:
                continue
            for x in edges[n]:
                live_at[x].append(n)
        par = {}

        def fd(x):
            par.setdefault(x, x)
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            return x

        for d in dead:
            a, b = edges[d]
            par[fd(a)] = fd(b)
        comp = collections.defaultdict(set)
        for d in dead:
            for x in edges[d]:
                comp[fd(x)].add(x)
        for k, ns in comp.items():
            anchors = sorted(x for x in ns if x in rails or live_at.get(x))
            empty = sorted(ns - set(anchors))
            devs = sorted(d for d in dead if fd(edges[d][0]) == k)
            L.append(f"   성분 nets={sorted(ns)} 고정쪽후보={anchors}(수 {len(anchors)}) 빈쪽={empty} "
                     f"포트∩빈쪽={sorted(set(empty) & ports)} 사슬길이={len(devs)}")
            for d in devs:
                a, b = edges[d]
                fs = a if a in anchors else (b if b in anchors else None)
                L.append(f"     {d}: d={a} s={b} bulk={bulk[d]} 고정쪽={fs} bulk==고정쪽={bulk[d] == fs}")
L.append(f"\n13회로 dead MOS 합계 = {total}")
OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
