# Phase 4 design v0.8 dependency graph acyclicity check (hard + soft edges, per-branch scenarios)
# Based on p4v07_dag.py. v0.8 changes (review4_phase4_v07.md):
#  S4  Phase 3 v7 D-27 engine-card freeze (D0b..F2): #2/#3/#4 and B26-2/B26-3 (#17/#18) default = after F2
#      (P3DoD -> #2,#3,#4,#17); pulling earlier is allowed only before D0b (scenarios R1, R8).
#  S3  #53 UD-17c (i) single read path for fixed node potentials: same schema as supplies_v (#21 -> #53) or
#      reuse #22's fixing path (#22 -> #53) => no soft #53 -> #23; separate path created by #53 first =>
#      soft kept and #22 reuses it (#53 -> #22). Controls R3/R4 (soft kept with #21/#22 -> #53) must be cyclic.
#  S2  normalized_margin (CC-9) moved into #23; #43/#25 records call it (tol None -> null): #23 -> #25 explicit.
import collections, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "p4v08_dag.out.txt")


def base_graph():
    E = {}

    def add(n, *preds):
        E.setdefault(n, []).extend(preds)

    for d in ["UD-1", "UD-4", "UD-5", "UD-6", "UD-7", "UD-9", "UD-15", "UD-17a", "UD-17b", "UD-17c",
              "UD-17d", "UD-17e", "UD-18", "A2", "install", "P9", "P10", "P10b", "planpatch",
              "B26pre-U1", "B26pre-U2", "U4", "U5", "D19", "userconn55"]:
        add(d)
    add("UD-17b", "UD-17a")
    # --- B1: confirmed order (hard) ---
    add("P2DoD", "P10b")                                            # reading (b): w/o B34, B26-1
    add("x34", "P9", "P10", "P10b", "P2DoD")                         # exempt-binding
    add("x35", "x34")                                                # scope policy (#48)
    add("#45", "P9", "A2", "install", "planpatch", "x35")            # B34 after 34->35 (confirmed order)
    add("B26pre", "#45", "B26pre-U1")                                # test-only strengthen card
    add("#1", "#45", "x34", "x35", "A2", "planpatch", "B26pre", "B26pre-U2", "U4", "U5", "P2DoD")
    add("x33", "#1")                                                 # B33 after B26-1 (confirmed, hard)
    add("G1", "x33", "x34", "x35")
    add("D0a", "G1", "P2DoD"); add("T0", "#1", "P2DoD", "x33")      # D-23; B33 before Phase 3
    add("D0b", "D0a", "#1", "#45", "P2DoD", "D19")
    add("M1", "G1", "T0", "D0b")
    add("P3DoD", "M1", "D0b")                                       # P3DoD = F2 merged (end of D-27 freeze)
    add("#2", "P3DoD"); add("#3", "P3DoD"); add("#4", "P3DoD")       # v0.8 S4: default after F2 (D-27)
    add("#5", "P3DoD", "#2"); add("#6", "#5"); add("#7", "#6"); add("#8", "#7"); add("#9", "#6")
    add("#25", "#6", "#22", "#23")                              # v0.8 S2: normalized_margin from #23; add("#10", "#6", "#25")
    for n in ["#11", "#14", "#15", "#16", "#20", "#30", "#32", "#33", "#34", "#35", "#36", "#40"]:
        add(n, "#6")
    add("#12", "#3", "#6"); add("#13", "#6", "#9")
    add("#17", "#1", "#45", "UD-1", "UD-15", "P3DoD")  # v0.8 S4: default after F2; add("#18", "#17")
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
    add("#53", "UD-17a", "UD-17b", "UD-17c")                        # data branch (iii) baseline
    add("#54", "UD-17d")                                            # data branch baseline
    add("#55", "UD-17e", "UD-17d", "userconn55", "#22")             # UD-17e (ii) only
    add("E3", "#21", "#54")                                         # OR pred (#54 or #53) -> #54 kept (m7)
    add("E8", "#54", "#55", "#27")
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


SOFT = [("#54", "#23"), ("#54", "#21"), ("#53", "#23"), ("#44", "#51")]   # #1 -> x33 is hard in v0.7


def minus(lst, *rm):
    return [e for e in lst if e not in rm]


E = base_graph()
E_e1 = {k: [p for p in v if p != "#55"] for k, v in E.items() if k != "#55"}   # UD-17e (i): no #55
scen = []
scen.append(("S0 hard only (confirmed order, D-27 defaults)", E))
scen.append(("S1 hard+soft (17c (iii), 17d data, 17e (ii))", with_edges(E, SOFT)))
scen.append(("S2a 17c(i) separate path made by #53 first: #6->#53, soft #53->#23 kept, #53->#22 (reuse)",
             with_edges(E, SOFT + [("#6", "#53"), ("#53", "#22")])))
scen.append(("S2b 17c(i) same schema as supplies_v: #6->#53, #21->#53, no soft #53->#23 (R5)",
             with_edges(E, minus(SOFT, ("#53", "#23")) + [("#6", "#53"), ("#21", "#53")])))
scen.append(("S2c 17c(i) reuse #22 fixing path: #6->#53, #22->#53, no soft #53->#23",
             with_edges(E, minus(SOFT, ("#53", "#23")) + [("#6", "#53"), ("#22", "#53")])))
scen.append(("S3 17c(ii): #6->#53, #23->#53, no soft #53->#23",
             with_edges(E, minus(SOFT, ("#53", "#23")) + [("#6", "#53"), ("#23", "#53")])))
scen.append(("S4 17e(i): #55 absent", with_edges(E_e1, SOFT)))
scen.append(("S5 17d engine: #23->#54, no soft #54->#23/#54->#21",
             with_edges(E, minus(SOFT, ("#54", "#23"), ("#54", "#21")) + [("#23", "#54")])))
scen.append(("S6 recommended UD-17e->#22 (answer before #22)",
             with_edges(E, SOFT + [("UD-17e", "#22")])))
scen.append(("S7 17e(ii) decided after #22: #55 owns engine part (#22->#55, #6->#55)",
             with_edges(E, SOFT + [("#6", "#55")])))
scen.append(("S8 all engine branches together (S2c+S5+S6)",
             with_edges(E, minus(SOFT, ("#53", "#23"), ("#54", "#23"), ("#54", "#21"))
                        + [("#6", "#53"), ("#22", "#53"), ("#23", "#54"), ("UD-17e", "#22")])))
scen.append(("R1 D-27: #2,#3,#4 pulled before D0b (#2..#4 -> D0b, P3DoD->#2..#4 dropped)",
             with_edges(E, SOFT + [("#2", "D0b"), ("#3", "D0b"), ("#4", "D0b")],
                        drop=[("P3DoD", "#2"), ("P3DoD", "#3"), ("P3DoD", "#4")])))
scen.append(("R8 D-27: #17,#18 pulled before D0b (#17,#18 -> D0b, P3DoD->#17 dropped)",
             with_edges(E, SOFT + [("#17", "D0b"), ("#18", "D0b")], drop=[("P3DoD", "#17")])))
scen.append(("R9 D-27 both pulled early (R1+R8)",
             with_edges(E, SOFT + [("#2", "D0b"), ("#3", "D0b"), ("#4", "D0b"), ("#17", "D0b"), ("#18", "D0b")],
                        drop=[("P3DoD", "#2"), ("P3DoD", "#3"), ("P3DoD", "#4"), ("P3DoD", "#17")])))
# negative controls (expected cyclic)
scen.append(("C1 ctrl confirmed order + v0.6 reading (a) P2DoD<-#45,#1",
             with_edges(E, SOFT + [("#45", "P2DoD"), ("#1", "P2DoD")])))
scen.append(("C2 ctrl Phase 3 bundle read literally as order T0,D0a,D0b -> G1 (with v6 G1 -> D0a)",
             with_edges(E, SOFT + [("T0", "G1"), ("D0a", "G1"), ("D0b", "G1")])))
scen.append(("C3 ctrl 17d engine #23->#54 with soft #54->#23 kept",
             with_edges(E, SOFT + [("#23", "#54")])))
scen.append(("C4 ctrl v0.5 single #54 incl. bulk (#22->#54) + soft #54->#23",
             with_edges(E_e1, SOFT + [("#22", "#54")])))
scen.append(("C5 ctrl R3: 17c(i) same schema (#21->#53) + soft #53->#23 kept",
             with_edges(E, SOFT + [("#6", "#53"), ("#21", "#53")])))
scen.append(("C6 ctrl R4: 17c(i) reuse #22 path (#22->#53) + soft #53->#23 kept",
             with_edges(E, SOFT + [("#6", "#53"), ("#22", "#53")])))
scen.append(("C7 ctrl S2a + #22 also made first (#22->#53 and #53->#22)",
             with_edges(E, SOFT + [("#6", "#53"), ("#53", "#22"), ("#22", "#53")])))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "a", encoding="utf-8") as f:
    for name, G in scen:
        ok, n, left = topo(G)
        line = f"{name}: acyclic={ok} nodes={n} unsorted={left[:12]}"
        print(line)
        f.write(line + "\n")
