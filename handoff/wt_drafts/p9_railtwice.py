"""Read-only: per loadable library circuit, count source/drain uses of each net in stick_diagram._RAIL_NETS
and whether any rail net is used exactly twice (the only case where the rail exclusion changes KCL edges)."""
import collections, glob, os, sys
R = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
A = os.path.join(R, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, A)
import stick_diagram as sd  # noqa: E402
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "p9_railtwice.out.txt")
lines = [f"_RAIL_NETS={sorted(sd._RAIL_NETS)}"]
for p in sorted(glob.glob(os.path.join(A, "library", "*.topology.json"))):
    name = os.path.basename(p)
    try:
        trs, meta = sd.load_topology(p)
    except Exception as e:  # report only
        lines.append(f"{name}: LOAD FAIL {type(e).__name__}")
        continue
    uses = collections.defaultdict(list)
    for t in trs:
        uses[t.source].append(t.name)
        uses[t.drain].append(t.name)
    rail = {n: len(u) for n, u in uses.items() if n in sd._RAIL_NETS}
    twice = [n for n, c in rail.items() if c == 2 and len(set(uses[n])) == 2]
    lines.append(f"{name}: rail_uses={rail} rail_used_exactly_twice_distinct={twice}")
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("\n".join(lines))
