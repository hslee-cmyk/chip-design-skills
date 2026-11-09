"""예측 probe(판정 증거 아님): 1차 병합본 코드(f38abf6)에 1차 생존 변이를 넣고 T2의 새 test 2건이 죽이는지. 파일은 끝에 원래 바이트로 되돌린다."""
import os, re, subprocess, sys
import mutate_changed as mc, reachability as rch
root, base, head, t2test, cache = sys.argv[1:6]
path = "skills/analog-gmid-design/assets/stick_diagram.py"; tpath = "skills/analog-gmid-design/assets/tests/contracts/test_df36_instance_relpath.py"
hf = rch.read_tree(root, head, rch.GRAPH_PREFIXES); src = hf[path]
bs = rch._git(root, ["show", "%s:%s" % (base, path)]).decode("utf-8")
target = "stick_diagram:_topology_ref_relpath:except_body_delete:body[3].handlers[0]"
fp, tp = os.path.join(root, *path.split("/")), os.path.join(root, *tpath.split("/"))
ob, ot = open(fp, "rb").read(), open(tp, "rb").read()
res = {}
try:
    open(tp, "wb").write(open(t2test, "rb").read())
    for label in ("unmutated", "mutated"):
        if label == "mutated":
            for q, fn in mc.changed_defs(bs, src):
                for op, np_, mfn in mc.mutants(fn, src):
                    if "stick_diagram:%s:%s:%s" % (q, op, np_) == target:
                        open(fp, "w", encoding="utf-8", newline="\n").write(mc._replace_def(src, fn, mfn))
        cmd = [sys.executable, "-P", "-m", "pytest", "-c", cache + "/pytest_gate.ini", "--rootdir=" + root, "--confcutdir=" + root, "-q",
               "-p", "no:cacheprovider", "--gmid-phase=2", "--gmid-strict=", "--color=no", tp + "::test_other_drive_topology_rejected"]
        p = subprocess.run(cmd, cwd=root, capture_output=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        res[label] = (p.returncode, [l for l in p.stdout.decode("utf-8", "replace").splitlines() if l.strip()][-3:])
finally:
    open(fp, "wb").write(ob); open(tp, "wb").write(ot)
for k, v in res.items(): print(k, v)
print("status_after", repr(subprocess.run(["git", "-C", root, "status", "--porcelain"], capture_output=True).stdout.decode()))
