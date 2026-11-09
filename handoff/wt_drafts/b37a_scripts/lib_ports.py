"""B37a: library topology ports / passive / ideal source facts (read-only on C:/g68/base)."""
import json, glob, os, sys
L = sys.argv[1] if len(sys.argv) > 1 else "C:/g68/base/skills/analog-gmid-design/library"
OUT = "C:/g68/out/lib_ports.txt"
with open(OUT, "w", encoding="utf-8") as fh:
    for p in sorted(glob.glob(os.path.join(L, "*.topology.json"))):
        d = json.load(open(p, encoding="utf-8"))
        name = os.path.basename(p)
        ports = d.get("ports")
        pe = d.get("passive_elements") or []
        isrc = d.get("ideal_sources") or []
        keys_pe = sorted({k for e in pe if isinstance(e, dict) for k in e})
        keys_is = sorted({k for e in isrc if isinstance(e, dict) for k in e})
        fh.write("== %s\n supply_nets=%r linked=%r\n" % (name, d.get("supply_nets"), d.get("linked_topology_files")))
        fh.write(" ports=%s\n" % json.dumps(ports, ensure_ascii=False))
        fh.write(" passive keys=%s ideal keys=%s\n" % (keys_pe, keys_is))
        if isinstance(ports, dict):
            nets = set()
            for t in d.get("netlist") or []:
                if isinstance(t, dict):
                    nets |= {t.get("source"), t.get("drain"), t.get("gate")}
            for e in pe + isrc:
                if isinstance(e, dict):
                    for k in ("terminals", "nodes", "nets"):
                        v = e.get(k)
                        if isinstance(v, list):
                            nets |= set(v)
                        elif isinstance(v, dict):
                            nets |= set(v.values())
            for k in ports:
                if k.startswith("_"):
                    continue
                fh.write("   port %-10s in_netlist_terminals=%s in_supply=%s\n" % (k, k in nets, k in (d.get("supply_nets") or [])))
print(open(OUT, encoding="utf-8").read())
