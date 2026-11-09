"""V3 기준 실행 시간(auditor, P9 순서 3): base 판 mutate_changed.run_tests와 같은 명령 모양
([py, -P, -m, pytest, -c ini, --rootdir=work, --confcutdir=work, -x, -q, -p no:cacheprovider, --gmid-phase=2, --gmid-strict=, <인벤토리 test>])을
mutate_changed.make_clone으로 만든 이력 포함 복제본(--head)에서 인벤토리 하나에 대해 돌려 벽시계 시간과 exit를 잰다.
사용: python -P v3_baseline.py <root> <head> <ini> <inv.json> <키> <out.json>"""
import json, os, shutil, subprocess, sys, tempfile, time
import mutate_changed as mc
root, head, ini, invf, key, out = sys.argv[1:7]
inv = json.load(open(invf, encoding="utf-8"))[key]["tests"]
tmp = tempfile.mkdtemp(prefix="gmid-v3b-", dir="C:/g47")
work = os.path.join(tmp, "copy")
mc.make_clone(os.path.abspath(root), work, head)
pyc = os.path.join(tmp, "pycache"); os.makedirs(pyc)
env = dict(os.environ, PYTHONPYCACHEPREFIX=pyc, PYTHONDONTWRITEBYTECODE="1")
cmd = [sys.executable, "-P", "-m", "pytest", "-c", ini, "--rootdir=" + work, "--confcutdir=" + work, "-x", "-q", "-p", "no:cacheprovider",
       "--gmid-phase=2", "--gmid-strict="] + [os.path.join(work, *mc.test_nodeid(t).split("::")[0].split("/")) + "::" + mc.test_nodeid(t).split("::", 1)[1] for t in inv]
s = time.time()
p = subprocess.run(cmd, cwd=work, capture_output=True, env=env)
el = time.time() - s
tail = p.stdout.decode("utf-8", "replace").strip().splitlines()[-1:]
res = {"head": head, "key": key, "n_inventory": len(inv), "exit": p.returncode, "elapsed_s": round(el, 2), "summary": tail}
print(json.dumps(res, ensure_ascii=False))
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
mc._rmtree_force(tmp)
