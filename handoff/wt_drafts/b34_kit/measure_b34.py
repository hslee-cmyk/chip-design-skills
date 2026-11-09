"""B34 V3 규모: 현행 도구 규칙(바뀐 def 전체) vs 범위 정책 N2(scope_proto N2w=넓힌 T6, N2b=승인 당시).
도구 함수(mutate_changed.changed_defs·mutants·inventory, reachability.build_graph 등)는 C:/g123/repo(0f23786 판) 읽기 전용 import."""
import ast, json, re, subprocess, sys
CL = "C:/g123/repo"
KIT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3scope_kit"
sys.path.insert(0, CL + "/tools/gates"); sys.path.insert(0, KIT)
import mutate_changed as mc, reachability as rch, scope_proto as SP
OUT = "C:/g123/out/measure_b34.txt"
def git(*a): return subprocess.run(["git", "-C", CL] + list(a), capture_output=True, check=True).stdout
def log(s):
    print(s, flush=True); open(OUT, "a", encoding="utf-8").write(s + "\n")
open(OUT, "w").close()
base = git("rev-parse", "0f23786").decode().strip(); head = git("rev-parse", "sim-b34").decode().strip()
log("base %s head %s" % (base, head))
diff = git("diff", "--name-only", "--no-renames", "--diff-filter=AM", base, head).decode()
targets = [p for p in diff.splitlines() if p.endswith(".py") and rch._is_source(p)]
log("targets %s" % targets)
head_files = rch.read_tree(CL, head, rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(head_files)
tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS) and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
res = {"all": [], "N2w": [], "N2b": [], "defs": {}}
for path in targets:
    hsrc = head_files[path]; bsrc = git("show", "%s:%s" % (base, path)).decode("utf-8")
    bdefs = dict(rch.iter_defs(ast.parse(bsrc))); mod = rch.module_name(path)
    for q, hfn in mc.changed_defs(bsrc, hsrc):
        ms = mc.mutants(hfn, hsrc)
        w = SP.select(bdefs[q], hfn, ms, "N2w"); b = SP.select(bdefs[q], hfn, ms, "N2b")
        inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
        ids = ["%s:%s:%s:%s" % (mod, q, o, p) for o, p, _ in ms]
        res["all"] += ids; res["N2w"] += [i for i, s in zip(ids, w) if s]; res["N2b"] += [i for i, s in zip(ids, b) if s]
        res["defs"][q] = {"all": len(ms), "N2b": sum(b), "N2w": sum(w), "inv": len(inv),
                          "base_hash": mc.def_hash(bdefs[q]) if hasattr(mc, "def_hash") else None}
        log("%-30s all=%3d N2b=%2d N2w=%2d inv=%d" % (q, len(ms), sum(b), sum(w), len(inv)))
log("total all=%d N2b=%d N2w=%d" % (len(res["all"]), len(res["N2b"]), len(res["N2w"])))
log("N2w ids:\n  " + "\n  ".join(res["N2w"]))
prev = json.load(open(KIT + "/out/ids_b34_narrow.json", encoding="utf-8"))["ids"]
for k in ("all", "N2w", "N2b"):
    log("same as kit ids_b34_narrow[%s]: %s" % (k, res[k] == prev[k]))
# spec card 'V3 계획' 표의 N2 10개 id(spec 문자열 그대로)
spec10 = ["_import_analog_grammar:stmt_delete:body[4]", "_import_analog_grammar:except_body_delete:body[4].handlers[0]",
          "_import_analog_grammar:early_return:body[1]", "find_idiom_matches:stmt_delete:body[2]", "find_idiom_matches:early_return:body[1]",
          "find_stack_edges:stmt_delete:body[2]", "find_stack_edges:early_return:body[1]", "audit_theta_root_direction:stmt_delete:body[2]",
          "audit_theta_root_direction:stmt_delete:body[5]", "audit_theta_root_direction:early_return:body[1]"]
log("N2w == spec 10: %s" % (sorted(res["N2w"]) == sorted("stick_diagram:" + s for s in spec10)))
c4 = ["stick_diagram:_import_analog_grammar:const+:body[3].body[0].value.args[0]", "stick_diagram:_import_analog_grammar:const-:body[3].body[0].value.args[0]",
      "stick_diagram:_import_analog_grammar:stmt_delete:body[3]", "stick_diagram:audit_theta_root_direction:stmt_delete:body[3]",
      "stick_diagram:audit_theta_root_direction:stmt_delete:body[3].body[0]", "stick_diagram:audit_theta_root_direction:stmt_delete:body[6].body[5].orelse[0]"]
for i in c4:
    log("contract4/6 id %s: in all=%s in N2w=%s" % (i, i in res["all"], i in res["N2w"]))
# 승인 기록 decision 원소와 겹침
appr = rch._approved_ids(CL, head) if rch._approved_ids.__code__.co_argcount >= 2 else None
if appr is not None:
    log("approved elements %d, overlap with all: %d" % (len(appr), len(set(appr) & set(res["all"]))))
json.dump(res, open("C:/g123/out/ids_b34_0f23786.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
