"""c1_head.py 합성 저장소(C:/g17/probe/c1/root)의 인벤토리 test가 사본 형태를 구별하는지:
(a) --head 커밋 격리 복제본(origin 제거) -> 통과 기대, (b) root HEAD(after-head) 복제본 -> 실패 기대,
(c) .git 포함 작업 트리 복사(미커밋 변경 포함) -> 실패 기대."""
import json
import os
import shutil
import stat
import subprocess
import sys

R = "C:/g17/probe/c1/root"
D = "C:/g17/probe/c1disc"
INI = "C:/g17/gate/pytest_gate.ini"
TEST = "skills/analog-gmid-design/assets/tests/test_copy_head.py"
d0 = json.load(open("C:/g17/probe/c1_base.json", encoding="utf-8"))


def rm(p):
    if os.path.exists(p):
        def onerr(f, path, _):
            os.chmod(path, stat.S_IWRITE)
            f(path)
        shutil.rmtree(p, onerror=onerr)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, **kw)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


def pytest(work):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPYCACHEPREFIX=D + "/pyc")
    rc, out = run([sys.executable, "-P", "-m", "pytest", "-c", INI, "--rootdir=" + work, "--confcutdir=" + work, "-q",
                   "-p", "no:cacheprovider", work + "/" + TEST], cwd=work, env=env)
    last = [l for l in out.splitlines() if "passed" in l or "failed" in l or "Error" in l][-3:]
    return {"exit": rc, "tail": last}


rm(D)
os.makedirs(D)
res = {}
a = D + "/a"
run(["git", "clone", "-q", "--no-hardlinks", "--no-local", "--no-checkout", R, a])
run(["git", "-C", a, "remote", "remove", "origin"])
run(["git", "-C", a, "checkout", "-q", "--detach", d0["head"]])
res["a_clone_at_head"] = pytest(a)
b = D + "/b"
run(["git", "clone", "-q", "--no-hardlinks", "--no-local", R, b])
run(["git", "-C", b, "remote", "remove", "origin"])
res["b_clone_at_root_HEAD"] = pytest(b)
c = D + "/c"
shutil.copytree(R, c)
res["c_worktree_copy_with_git"] = pytest(c)
with open(D + ".json", "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
