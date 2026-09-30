"""V3 진단(auditor): mutate_changed.py와 같은 방식으로 인벤토리를 구하고, 같은 방식(.git 제외 copytree, -x -q)의 기준 실행 출력을 파일로 남긴다.
사용: PYTHONPATH=<캐시> python -P v3_baseline_probe.py <root> <head> <copy 상위 디렉터리> <out.txt>"""
import os, re, shutil, subprocess, sys
import mutate_changed as mc
import reachability as rch
root, head, parent, out = sys.argv[1:5]
root = os.path.abspath(root)
head_files = rch.read_tree(root, head, rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(head_files)
test_nodes = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
              and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
path = "skills/analog-gmid-design/assets/stick_diagram.py"
fo = open(out, "w", encoding="utf-8")
invs = {}
for q in ("_topology_ref_relpath", "save_instance_json"):
    inv = mc.inventory(edges, "%s::%s" % (path, q), test_nodes)
    invs[q] = inv
    fo.write("%s inventory %d\n" % (q, len(inv)))
    for t in inv:
        fo.write("  %s\n" % t)
work = os.path.join(parent, "copy")
if os.path.exists(work):
    shutil.rmtree(work)
shutil.copytree(root, work, ignore=shutil.ignore_patterns(".git"))
cache = os.environ["PYTHONPATH"].split(os.pathsep)[0]
inv = invs["save_instance_json"]
cmd = [sys.executable, "-P", "-m", "pytest", "-c", cache + "/pytest_gate.ini", "--rootdir=" + work, "--confcutdir=" + work,
       "-x", "-q", "-p", "no:cacheprovider", "--gmid-phase=2", "--gmid-strict="] + \
      [os.path.join(work, *mc.test_nodeid(t).split("::")[0].split("/")) + "::" + mc.test_nodeid(t).split("::", 1)[1] for t in inv]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPYCACHEPREFIX=os.path.join(parent, "pyc"))
p = subprocess.run(cmd, cwd=work, capture_output=True, env=env)
fo.write("rc %d\n" % p.returncode)
fo.write(p.stdout.decode("utf-8", "replace")[-6000:])
fo.write(p.stderr.decode("utf-8", "replace")[-2000:])
fo.close()
