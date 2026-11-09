# Phase 4 design v0.5 dependency graph acyclicity check (hard + soft edges)
import sys
E = {}  # node -> list of predecessors
def add(n, *preds): E.setdefault(n, []).extend(preds)
for d in ["UD-1","UD-4","UD-5","UD-6","UD-7","UD-9","UD-15","UD-17a","UD-17b","UD-17c","UD-17d","UD-17e","UD-18","A2","install","P9","P10","P10b","planpatch"]: add(d)
add("UD-17b","UD-17a")
add("x34",'P9','P10','P10b'); add("x35","x34")        # exempt-binding -> scope policy (#48)
add("#45","P9","A2","install","planpatch")
add("#1","#45","x34","x35","A2","planpatch")
add("x33"); add("G1","x33","x34","x35"); add("D0a","G1"); add("D0b","D0a","#1","#45")
add("#2"); add("#3"); add("#4")
add("P3DoD","D0b","#2","#3","#4")
add("#5","P3DoD","#2"); add("#6","#5"); add("#7","#6"); add("#8","#7"); add("#9","#6")
add("#25","#6","#22"); add("#10","#6","#25")
for n in ["#11","#14","#15","#16","#20","#30","#32","#33","#34","#35","#36","#40"]: add(n,"#6")
add("#12","#3","#6"); add("#13","#6","#9")
add("#17","#1","#45","UD-1","UD-15"); add("#18","#17")
add("C1","UD-7"); add("#19","#17","#18","#21","#3","C1","UD-9")
add("#23","#6"); add("#21","#20","#23")
add("#22","#21","#23","#17"); add("#51","#22")
add("#46","UD-15"); add("#49","#17","#46","#19")
add("#47","#45","#1","#6","UD-18"); add("#52","#46","#47")
add("#24","#22","#23","#13")
add("#26","#25"); add("#27","#26"); add("#28","#27"); add("#29","#28")
add("#31","#6","UD-5"); add("#37","UD-4"); add("#38","#13"); add("#39","P10")
add("#41","#2"); add("#42")
add("#43","#6","#10","#23"); add("#44","UD-6","#43")
add("#53","UD-17a","UD-17b","UD-17c")
add("#54","UD-17d","UD-17e")
# conditional/soft edges (recommended merge order) -- must also stay acyclic
SOFT = [("#54","#23"),("#54","#21"),("#53","#23"),("#44","#51")]
add("DoD", *[n for n in list(E) if n.startswith("#")])
def topo(edges):
    import collections
    indeg = collections.Counter(); succ = collections.defaultdict(list); nodes=set(edges)
    for n,ps in edges.items():
        for p in ps:
            nodes.add(p); succ[p].append(n); indeg[n]+=1
    q=[n for n in nodes if indeg[n]==0]; out=[]
    while q:
        n=q.pop(); out.append(n)
        for s in succ[n]:
            indeg[s]-=1
            if indeg[s]==0: q.append(s)
    return len(out)==len(nodes), len(nodes), [n for n in nodes if n not in out]
print("hard:", topo(E))
E2={k:list(v) for k,v in E.items()}
for a,b in SOFT: E2.setdefault(b,[]).append(a)
print("hard+soft:", topo(E2))
