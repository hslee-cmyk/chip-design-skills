"""head·master 덤프 칸별 비교 -> run3/out/cmp_chain.txt"""
import json
import pathlib

base = pathlib.Path(__file__).parent
a = json.loads((base / "dump_base.json").read_text(encoding="utf-8"))
b = json.loads((base / "dump_head.json").read_text(encoding="utf-8"))
out = []


def walk(path, x, y):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            if k not in x:
                out.append(("added", path + "/" + k, y[k]))
            elif k not in y:
                out.append(("removed", path + "/" + k, x[k]))
            else:
                walk(path + "/" + k, x[k], y[k])
    elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        for i, (p, q) in enumerate(zip(x, y)):
            walk(path + "/" + str(i), p, q)
    elif x != y:
        out.append(("changed", path, (x, y)))


for circuit in a:
    walk(circuit, a[circuit], b[circuit])
lines = [str(o)[:400] for o in out]
(base / "out" / "cmp_chain.txt").write_text("\n".join(lines), encoding="utf-8")
print(len(lines))
for l in lines:
    if "added" in l[:8] and "load_note" in l and "None" in l[-8:]:
        continue
    print(l)
