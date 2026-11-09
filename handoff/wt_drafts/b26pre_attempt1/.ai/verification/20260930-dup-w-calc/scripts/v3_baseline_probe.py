"""V3 도구가 '변이 없는 기준 실행 실패'라고 한 원인 추적(auditor). mutate_changed.py와 같은 인벤토리·같은 명령으로
<work>(복제본의 .git 없는 사본)에서 기준 실행을 재현하고 출력 끝을 보인다.
사용: PYTHONPATH=<캐시> python -P v3_baseline_probe.py <root> <base> <head> <work> <pytest_ini> <out.txt> [<def qualname>...]"""
import os, subprocess, sys
import mutate_changed as mc
rch = mc.rch
root, base, head, work, ini, out = sys.argv[1:7]
want = sys.argv[7:]
head_files = rch.read_tree(root, head, rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(head_files)
test_nodes = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
              and mc.re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
path = "skills/analog-gmid-design/assets/sizing_recipe.py"
base_src = rch._git(root, ["show", "%s:%s" % (base, path)]).decode("utf-8")
fo = open(out, "w", encoding="utf-8")
seen = set()
for q, fn in mc.changed_defs(base_src, head_files[path]):
    inv = mc.inventory(edges, "%s::%s" % (path, q), test_nodes)
    fo.write("DEF %s inventory %d\n" % (q, len(inv)))
    if want and q not in want:
        continue
    if tuple(inv) in seen or not inv:
        continue
    seen.add(tuple(inv))
    cmd = [sys.executable, "-P", "-m", "pytest", "-c", ini, "--rootdir=" + work, "--confcutdir=" + work, "-x", "-q",
           "-p", "no:cacheprovider", "--gmid-phase=2", "--gmid-strict="] + \
          [os.path.join(work, *mc.test_nodeid(t).split("::")[0].split("/")) + "::" + mc.test_nodeid(t).split("::", 1)[1] for t in inv]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    r = subprocess.run(cmd, cwd=work, capture_output=True, env=env)
    fo.write("  inv: %s\n" % inv[:50])
    fo.write("  rc %s\n" % r.returncode)
    fo.write("  stdout tail:\n" + r.stdout.decode("utf-8", "replace")[-4000:] + "\n")
    fo.write("  stderr tail:\n" + r.stderr.decode("utf-8", "replace")[-2000:] + "\n")
    fo.flush()
fo.close()
print("done")
