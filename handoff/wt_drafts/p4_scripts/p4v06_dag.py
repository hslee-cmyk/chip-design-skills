# Phase 4 design v0.6 dependency graph acyclicity check (hard + soft edges, per-branch scenarios)
# Based on p4v05_dag.py. v0.6 changes: #55 split from #54 (UD-17e bulk), #53 gated by UD-17a+b+c,
# UD-17c branch edges, B26-1 v4 conditions U3/U4/U5, Phase 2 DoD node (Phase 3 v6 D-23 / §9.1),
# D-19 node, B33 working-order edge, b34_commit_plan.md §1 order scenario.
# Results are appended to p4_scripts/out/p4v06_dag.out.txt (one line per scenario).
import collections, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "p4v06_dag.out.txt")


def base_graph():
    E = {}

    def add(n, *preds):
        E.setdefault(n, []).extend(preds)

    for d in ["UD-1", "UD-4", "UD-5", "UD-6", "UD-7", "UD-9", "UD-15", "UD-17a", "UD-17b", "UD-17c",
              "UD-17d", "UD-17e", "UD-18", "A2", "install", "P9", "P10", "P10b", "planpatch",
              "U3", "U4", "U5", "D19", "userconn55"]:
        add(d)
    add("UD-17b", "UD-17a")
    add("x34", "P9", "P10", "P10b"); add("x35", "x34")          # exempt-binding -> scope policy (#48)
    add("#45", "P9", "A2", "install", "planpatch")
    add("#1", "#45", "x34", "x35", "A2", "planpatch", "U3", "U4", "U5")   # v0.6: B26-1 v4 U3/U4/U5
    add("P2DoD", "P10b", "#45", "#1")                              # Phase 3 v6 §9.1 reading (a)
    add("x33"); add("G1", "x33", "x34", "x35")
    add("D0a", "G1", "P2DoD"); add("T0", "#1", "P2DoD")            # D-23
    add("D0b", "D0a", "#1", "#45", "P2DoD", "D19")
    add("#2"); add("#3"); add("#4")
    add("M1", "G1", "T0", "D0b")
    add("P3DoD", "M1", "D0b", "#2", "#3", "#4")
    add("#5", "P3DoD", "#2"); add("#6", "#5"); add("#7", "#6"); add("#8", "#7"); add("#9", "#6")
    add("#25", "#6", "#22"); add("#10", "#6", "#25")
    for n in ["#11", "#14", "#15", "#16", "#20", "#30", "#32", "#33", "#34", "#35", "#36", "#40"]:
        add(n, "#6")
    add("#12", "#3", "#6"); add("#13", "#6", "#9")
    add("#17", "#1", "#45", "UD-1", "UD-15"); add("#18", "#17")
    add("C1", "UD-7"); add("#19", "#17", "#18", "#21", "#3", "C1", "UD-9")
    add("#23", "#6"); add("#21", "#20", "#23")
    add("#22", "#21", "#23", "#17"); add("#51", "#22")
    add("#46", "UD-15"); add("#49", "#17", "#46", "#19")
    add("#47", "#45", "#1", "#6", "UD-18", "D19"); add("#52", "#46", "#47")
    add("#24", "#22", "#23", "#13")
    add("#26", "#25"); add("#27", "#26"); add("#28", "#27"); add("#29", "#28")
    add("#31", "#6", "UD-5"); add("#37", "UD-4"); add("#38", "#13"); add("#39", "P10")
    add("#41", "#2"); add("#42")
    add("#43", "#6", "#10", "#23"); add("#44", "UD-6", "#43")
    add("#53", "UD-17a", "UD-17b", "UD-17c")                      # v0.6: 17a + 17c jointly gate
    add("#54", "UD-17d")                                            # v0.6: bulk split off
    add("#55", "UD-17e", "UD-17d", "userconn55", "#22")             # v0.6: UD-17e (ii) only
    add("E3", "#21", "#54"); add("E8", "#54", "#55", "#27")
    add("DoD", *[n for n in list(E) if n.startswith("#")], "E3", "E8")
    return E


def topo(edges):
    indeg = collections.Counter(); succ = collections.defaultdict(list); nodes = set(edges)
    for n, ps in edges.items():
        for p in ps:
            nodes.add(p); succ[p].append(n); indeg[n] += 1
    q = [n for n in nodes if indeg[n] == 0]; out = []
    while q:
        n = q.pop(); out.append(n)
        for s in succ[n]:
            indeg[s] -= 1
            if indeg[s] == 0:
                q.append(s)
    left = sorted(n for n in nodes if n not in out)
    return len(out) == len(nodes), len(nodes), left


def with_edges(E, extra=(), drop=()):
    G = {k: list(v) for k, v in E.items()}
    for a, b in drop:          # remove edge a -> b
        if b in G and a in G[b]:
            G[b].remove(a)
    for a, b in extra:         # add edge a -> b
        G.setdefault(b, []).append(a)
    return G


SOFT = [("#54", "#23"), ("#54", "#21"), ("#53", "#23"), ("#44", "#51"), ("#1", "x33")]

E = base_graph()
scen = []
scen.append(("S0 hard only", E))
scen.append(("S1 hard+soft (17c (i)/(iii), 17e (ii))", with_edges(E, SOFT)))
# 17c (ii): engine column-KVL rule -> #23 -> #53, soft #53 -> #23 removed
scen.append(("S2 17c(ii): #23->#53, no soft #53->#23",
             with_edges(E, [e for e in SOFT if e != ("#53", "#23")] + [("#23", "#53")])))
# 17e (i): no #55 card; E8 <- #54 + #27 only
E_e1 = {k: [p for p in v if p != "#55"] for k, v in E.items() if k != "#55"}
scen.append(("S3 17e(i): #55 absent", with_edges(E_e1, SOFT)))
# negative control: v0.5-style single #54 carrying bulk (needs #22) while keeping soft #54 -> #23
scen.append(("S4 ctrl v0.5 single #54 incl. bulk (#22->#54) + soft #54->#23",
             with_edges(E_e1, SOFT + [("#22", "#54")])))
# working order of b34_commit_plan.md §1 taken literally together with P2DoD <- #45,#1
scen.append(("S5 ctrl b34_commit_plan order P2DoD->x34 with P2DoD<-#1",
             with_edges(E, SOFT + [("P2DoD", "x34")])))
# reading (b): Phase 2 DoD excludes B34/B26-1
E_b = with_edges(E, drop=[("#45", "P2DoD"), ("#1", "P2DoD")])
scen.append(("S6 reading (b): P2DoD w/o B34,B26-1, then P2DoD->x34", with_edges(E_b, SOFT + [("P2DoD", "x34")])))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "a", encoding="utf-8") as f:
    for name, G in scen:
        ok, n, left = topo(G)
        line = f"{name}: acyclic={ok} nodes={n} unsorted={left[:12]}"
        print(line)
        f.write(line + "\n")
