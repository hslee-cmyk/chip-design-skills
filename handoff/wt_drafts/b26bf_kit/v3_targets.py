"""backfill card V3 대상 수 -- 현재 도구(바뀐 def의 변이 전부)와 범위 정책 N2w(_drafts/v3scope_kit/scope_proto.py).

도구 main과 같은 경로(`git diff --name-only --no-renames --diff-filter=AM` → `rch._is_source` → `changed_defs` → `mutants` → id)로
변이를 만들고, 각 변이에 N2w/N2b 선택 여부와 인벤토리를 붙인다. pytest는 돌리지 않는다.
게이트 코드 = C:/g128/gate0/tools/gates(gate master 0f23786 archive, a796468과 tools/ 차이 0).
사용: python -B v3_targets.py <base> <head> <label>   결과: C:/g128/out/v3_targets_<label>.json"""
import ast, json, os, re, subprocess, sys

G = "C:/g128"
CL = G + "/sim/r"
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3scope_kit")
sys.path.insert(0, G + "/gate0/tools/gates")
import mutate_changed as mc   # noqa: E402
import reachability as rch    # noqa: E402
import scope_proto as SP      # noqa: E402

base, head, label = sys.argv[1:4]


def git(*a):
    return subprocess.run(["git", "-C", CL] + list(a), capture_output=True, check=True).stdout


diff = git("diff", "--name-only", "--no-renames", "--diff-filter=AM", base, head).decode("utf-8")
targets = [p for p in diff.splitlines() if p.endswith(".py") and rch._is_source(p)]
head_files = rch.read_tree(CL, head, rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(head_files)
tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
         and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
out = {"base": base, "head": head, "diff": diff.splitlines(), "targets": targets, "defs": [], "mutants": []}
for path in targets:
    hsrc = head_files[path]
    rc = subprocess.run(["git", "-C", CL, "cat-file", "-e", "%s:%s" % (base, path)], capture_output=True).returncode
    bsrc = git("show", "%s:%s" % (base, path)).decode("utf-8") if rc == 0 else None
    bdefs = dict(rch.iter_defs(ast.parse(bsrc))) if bsrc else {}
    mod = rch.module_name(path)
    for q, hfn in mc.changed_defs(bsrc, hsrc):
        ms = mc.mutants(hfn, hsrc)
        if q in bdefs:
            w = SP.select(bdefs[q], hfn, ms, "N2w")
            b = SP.select(bdefs[q], hfn, ms, "N2b")
        else:
            w = b = [True] * len(ms)
        inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
        out["defs"].append({"path": path, "def": q, "new": q not in bdefs, "all": len(ms), "N2w": sum(w), "N2b": sum(b),
                            "inventory": inv})
        for (o, p, mfn), sw, sb in zip(ms, w, b):
            # 변이 대상 줄(head) -- 경로의 노드 lineno
            node = mc._get(hfn, p) if hasattr(mc, "_get") else None
            line = getattr(node, "lineno", None)
            out["mutants"].append({"id": "%s:%s:%s:%s" % (mod, q, o, p), "line": line, "N2w": sw, "N2b": sb})
os.makedirs(G + "/out", exist_ok=True)
with open(G + "/out/v3_targets_%s.json" % label, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print("targets", targets)
for d in out["defs"]:
    print("%s::%s all=%d N2b=%d N2w=%d inventory=%d" % (d["path"].split("/")[-1], d["def"], d["all"], d["N2b"], d["N2w"], len(d["inventory"])))
print("N2w ids:")
for m in out["mutants"]:
    if m["N2w"]:
        print("  ", m["line"], m["id"])
