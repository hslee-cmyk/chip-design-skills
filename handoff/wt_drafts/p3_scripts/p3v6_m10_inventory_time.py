"""Phase 3 design v6 -- M10 V3 비용 추정 입력(3차 검토 S3). 읽기 전용, 격리 복제본에서 실행.

    C:/Python314/python.exe -B p3v6_m10_inventory_time.py <복제본> <출력 json>

1. `workspaces/run_harness.py::run`의 V3 인벤토리(HEAD 그래프, mutate_changed.inventory 그대로)를 전부 뽑는다.
2. 그 test id 전체를 V3와 같은 방식(`-x` 없이 전부, `-q -p no:cacheprovider`)으로 한 번 실행해 벽시계 초를 잰다
   -- 변이가 E-INST test에서 죽지 않을 때 한 변이가 치르는 상한.
결과는 출력 json에 쓴다(케이스 하나).
"""
import json
import os
import re
import subprocess
import sys
import time

ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, "tools", "gates"))
import reachability as rch  # noqa: E402
import mutate_changed as mc  # noqa: E402

graph = rch.read_tree(ROOT, "HEAD", rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(graph)
test_nodes = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
              and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
inv = sorted(mc.inventory(edges, "workspaces/run_harness.py::run", test_nodes))
ids = [n.replace("::", "::", 1) for n in inv]
by_file = {}
for n in inv:
    by_file.setdefault(n.split("::")[0], 0)
    by_file[n.split("::")[0]] += 1
env = dict(os.environ)
import site  # noqa: E402
env["PYTHONPATH"] = os.pathsep.join([os.path.join(ROOT, "tools", "gates"), site.getusersitepackages()])
ini = os.path.join(ROOT, "tools", "gates", "pytest_gate.ini")
cmd = [sys.executable, "-B", "-P", "-m", "pytest", "-c", ini, "--rootdir=" + ROOT, "--confcutdir=" + ROOT,
       "-q", "-p", "no:cacheprovider", "--gmid-phase=2"] + [os.path.join(ROOT, i) for i in ids]
t0 = time.time()
p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
el = time.time() - t0
res = {"inventory_count": len(inv), "by_file": by_file, "pytest_exit": p.returncode,
       "wall_s": round(el, 1), "tail": p.stdout.strip().splitlines()[-3:]}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
