"""V3 사전 목록(auditor): base 판 mutate_changed.changed_defs·mutants로 base->M의 변이 대상 def와 변이 id를 나열(실행 없음)."""
import subprocess, sys
import mutate_changed as mc, reachability as rch
root, base, head = sys.argv[1:4]
P = "skills/analog-gmid-design/assets/stick_diagram.py"
bs = subprocess.run(["git", "-C", root, "show", "%s:%s" % (base, P)], capture_output=True, check=True).stdout.decode("utf-8")
hs = subprocess.run(["git", "-C", root, "show", "%s:%s" % (head, P)], capture_output=True, check=True).stdout.decode("utf-8")
tot = 0
for q, fn in mc.changed_defs(bs, hs):
    ms = list(mc.mutants(fn, hs))
    tot += len(ms)
    print(q, len(ms))
    for op, path, _ in ms:
        print("   ", op, path)
print("total", tot)
