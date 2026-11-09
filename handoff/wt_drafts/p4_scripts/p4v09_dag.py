# Phase 4 design v0.9 dependency graph acyclicity check (hard + soft edges, per-branch scenarios)
# Based on p4v08_dag.py. v0.9 changes (review5_phase4_v08.md):
#  N-S4  v0.8 swallowed three edges inside trailing comments (#6 -> #10, #25 -> #10, #17 -> #18).
#        They are restored as separate statements below (no edge text after a '#' on any add line).
#  N-S1  Approval-time edges. The Phase 4 approval question (UD-0 design approval, UD-6, UD-1, UD-15;
#        2nd question UD-4, UD-5, U-26 (a)) is raised at Phase 4 start = after Phase 3 DoD (P3DoD).
#        So P3DoD -> UD-0/UD-1/UD-6/UD-15, UD-0 -> UD-4/UD-5/U26a (2nd question only after UD-0),
#        UD-0 -> every card this design defines (#1, #45, B26pre have their own approvals -> excluded),
#        U26a -> #21. Principled default (ga): NO pull-forward of #2/#3/#4/#17/#18 before D0b.
#        Former R1/R8/R9 (pull-forward) become controls RC1/RC8/RC9 that must be CYCLIC with these
#        approval edges (they reproduce review5 N-S1). N1 shows the rejected alternative (na) -- separate
#        approval asked before D0b -- would be acyclic (information only, not adopted).
#  New   U-BF (backfill interdig_ok fix card, b26_backfill_question.md option 1): BF between B26pre and #1 (S9).
import collections, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "p4v09_dag.out.txt")

QUOTED = {"#1", "#45"}          # Phase 2 cards quoted by this design (own approvals A2 etc.)


def base_graph():
    E = {}

    def add(n, *preds):
        E.setdefault(n, []).extend(preds)

    for d in ["UD-17a", "UD-17b", "UD-17c", "UD-17d", "UD-17e", "UD-18", "UD-7", "UD-9",
              "A2", "install", "P9", "P10", "P10b", "planpatch",
              "U4", "U5", "D19", "userconn55"]:
        add(d)
    add("UD-17b", "UD-17a")
    # --- confirmed order (hard) ---
    add("P2DoD", "P10b")                                            # reading (b): w/o B34, B26-1
    add("x34", "P9", "P10", "P10b", "P2DoD")                         # exempt-binding
    add("x35", "x34")                                                # scope policy (#48)
    add("#45", "P9", "A2", "install", "planpatch", "x35")            # B34 after 34->35 (confirmed order)
    add("B26pre", "#45")                                             # test-only; U1 = principle default (no node)
    add("#1", "#45", "x34", "x35", "A2", "planpatch", "B26pre", "U4", "U5", "P2DoD")
    add("x33", "#1")                                                 # B33 after B26-1 (confirmed, hard)
    add("G1", "x33", "x34", "x35")
    add("D0a", "G1", "P2DoD")
    add("T0", "#1", "P2DoD", "x33")                                  # D-23; B33 before Phase 3
    add("D0b", "D0a", "#1", "#45", "P2DoD", "D19")
    add("M1", "G1", "T0", "D0b")
    add("P3DoD", "M1", "D0b")                                        # P3DoD = F2 merged (end of D-27 freeze)
    # --- approval-time edges (N-S1) ---
    add("UD-0", "P3DoD")                                             # 1st question at Phase 4 start
    add("UD-1", "P3DoD")
    add("UD-6", "P3DoD")
    add("UD-15", "P3DoD")
    add("UD-4", "UD-0")                                              # 2nd question only after UD-0
    add("UD-5", "UD-0")
    add("U26a", "UD-0")
    # --- Phase 4 cards ---
    add("#2", "P3DoD")
    add("#3", "P3DoD")
    add("#4", "P3DoD")
    add("#5", "P3DoD", "#2")
    add("#6", "#5")
    add("#7", "#6")
    add("#8", "#7")
    add("#9", "#6")
    add("#25", "#6", "#22", "#23")                                   # #23 = normalized_margin
    add("#10", "#6", "#25")                                          # restored (N-S4)
    for n in ["#11", "#14", "#15", "#16", "#20", "#30", "#32", "#33", "#34", "#35", "#36", "#40"]:
        add(n, "#6")
    add("#12", "#3", "#6")
    add("#13", "#6", "#9")
    add("#17", "#1", "#45", "UD-1", "UD-15", "P3DoD")                # default after F2 (only path, N-S1 ga)
    add("#18", "#17")                                                # restored (N-S4)
    add("C1", "UD-7")
    add("#19", "#17", "#18", "#21", "#3", "C1", "UD-9")
    add("#23", "#6")
    add("#21", "#20", "#23", "U26a")
    add("#22", "#21", "#23", "#17")
    add("#51", "#22")
    add("#46", "UD-15")
    add("#49", "#17", "#46", "#19")
    add("#47", "#45", "#1", "#6", "UD-18", "D19")
    add("#52", "#46", "#47")
    add("#24", "#22", "#23", "#13")
    add("#26", "#25")
    add("#27", "#26")
    add("#28", "#27")
    add("#29", "#28")
    add("#31", "#6", "UD-5")
    add("#37", "UD-4")
    add("#38", "#13")
    add("#39", "P10")
    add("#41", "#2")
    add("#42")
    add("#43", "#6", "#10", "#23")
    add("#44", "UD-6", "#43")
    add("#53", "UD-17a", "UD-17b", "UD-17c")                         # data branch (iii) baseline
    add("#54", "UD-17d")                                             # data branch baseline
    add("#55", "UD-17e", "UD-17d", "userconn55", "#22")              # UD-17e (ii) only
    # UD-0 (design approval) precedes every card this design defines
    for n in list(E):
        if n.startswith("#") and n not in QUOTED:
            add(n, "UD-0")
    for n in ["C1"]:
        add(n, "UD-0")
    add("E3", "#21", "#54")                                          # OR pred (#54 or #53) -> #54 kept
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


def drop_node(E, node):
    return {k: [p for p in v if p != node] for k, v in E.items() if k != node}


SOFT = [("#54", "#23"), ("#54", "#21"), ("#53", "#23"), ("#44", "#51")]


def minus(lst, *rm):
    return [e for e in lst if e not in rm]


E = base_graph()
# self-checks for N-S4: the restored edges must be present
assert "#25" in E["#10"] and "#6" in E["#10"], "edge #6/#25 -> #10 missing"
assert "#17" in E["#18"], "edge #17 -> #18 missing"
assert "UD-0" in E["#2"] and "P3DoD" in E["UD-0"], "approval-time edges missing"

E_e1 = drop_node(E, "#55")                                           # UD-17e (i): no #55
PULL_234 = [("#2", "D0b"), ("#3", "D0b"), ("#4", "D0b")]
PULL_1718 = [("#17", "D0b"), ("#18", "D0b")]
DROP_234 = [("P3DoD", "#2"), ("P3DoD", "#3"), ("P3DoD", "#4")]
DROP_17 = [("P3DoD", "#17")]
scen = []
scen.append(("S0 hard only (confirmed order, approval-time edges, D-27 single path after F2)", E))
scen.append(("S1 hard+soft (17c (iii), 17d data, 17e (ii))", with_edges(E, SOFT)))
scen.append(("S2a 17c(i) separate path made by #53 first: #6->#53, soft #53->#23 kept, #53->#22 (reuse)",
             with_edges(E, SOFT + [("#6", "#53"), ("#53", "#22")])))
scen.append(("S2b 17c(i) same schema as supplies_v: #6->#53, #21->#53, no soft #53->#23",
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
scen.append(("S9 U-BF option 1: backfill fix card BF after B26pre, before #1 (U-BF answered)",
             with_edges(E, SOFT + [("U-BF", "BF"), ("B26pre", "BF"), ("BF", "#1")])))
# information only: rejected alternative (na) -- separate approvals asked before D0b
N1 = drop_node(E, "UD-0")
N1 = with_edges(N1, SOFT + PULL_234 + PULL_1718 + [("UD-0pre", "#2"), ("UD-0pre", "#3"), ("UD-0pre", "#4")],
                drop=DROP_234 + DROP_17 + [("P3DoD", "UD-1"), ("P3DoD", "UD-15")])
scen.append(("N1 info (na, not adopted): pull-forward with SEPARATE approvals before D0b (UD-0pre, UD-1, UD-15 roots)",
             N1))
# negative controls (expected cyclic)
scen.append(("RC1 ctrl N-S1: #2,#3,#4 pulled before D0b while UD-0 asked after P3DoD",
             with_edges(E, SOFT + PULL_234, drop=DROP_234)))
scen.append(("RC8 ctrl N-S1: #17,#18 pulled before D0b while UD-1/UD-15 asked after P3DoD",
             with_edges(E, SOFT + PULL_1718, drop=DROP_17)))
scen.append(("RC9 ctrl N-S1: RC1 + RC8",
             with_edges(E, SOFT + PULL_234 + PULL_1718, drop=DROP_234 + DROP_17)))
scen.append(("C1 ctrl confirmed order + v0.6 reading (a) P2DoD<-#45,#1",
             with_edges(E, SOFT + [("#45", "P2DoD"), ("#1", "P2DoD")])))
scen.append(("C2 ctrl Phase 3 bundle read literally as order T0,D0a,D0b -> G1 (with v6 G1 -> D0a)",
             with_edges(E, SOFT + [("T0", "G1"), ("D0a", "G1"), ("D0b", "G1")])))
scen.append(("C3 ctrl 17d engine #23->#54 with soft #54->#23 kept",
             with_edges(E, SOFT + [("#23", "#54")])))
scen.append(("C4 ctrl v0.5 single #54 incl. bulk (#22->#54) + soft #54->#23",
             with_edges(E_e1, SOFT + [("#22", "#54")])))
scen.append(("C5 ctrl 17c(i) same schema (#21->#53) + soft #53->#23 kept",
             with_edges(E, SOFT + [("#6", "#53"), ("#21", "#53")])))
scen.append(("C6 ctrl 17c(i) reuse #22 path (#22->#53) + soft #53->#23 kept",
             with_edges(E, SOFT + [("#6", "#53"), ("#22", "#53")])))
scen.append(("C7 ctrl S2a + #22 also made first (#22->#53 and #53->#22)",
             with_edges(E, SOFT + [("#6", "#53"), ("#53", "#22"), ("#22", "#53")])))

EXPECT_CYCLIC = ("RC", "C")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bad = 0
with open(OUT, "a", encoding="utf-8") as f:
    for name, G in scen:
        ok, n, left = topo(G)
        expect_ok = not name.startswith(EXPECT_CYCLIC)
        verdict = "as-expected" if ok == expect_ok else "UNEXPECTED"
        bad += ok != expect_ok
        line = f"{name}: acyclic={ok} nodes={n} [{verdict}] unsorted={left[:12]}"
        print(line)
        f.write(line + "\n")
    tail = f"SUMMARY scenarios={len(scen)} unexpected={bad}"
    print(tail)
    f.write(tail + "\n")
