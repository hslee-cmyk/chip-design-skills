"""git-history-kill 인벤토리 test가 .git 없는 사본(base 도구 방식)에서 실패하고 이력 있는 복제본(origin 제거)에서 통과하는지(격리 C:/g17)."""
import json
import os
import shutil
import subprocess
import sys

SRC = "C:/g17/tmp/gmid-redteam/20260930-195723-direct/31-v3-git-history-tui_wc21/v/git-history-kill"
TEST = "skills/analog-gmid-design/assets/tests/test_rt_scale_history.py::test_rt_scale_with_base_blob"
INI = "C:/g17/gate/pytest_gate.ini"
OUT = "C:/g17/probe/red_cause.json"
res = {}


def pytest(work, tag):
    pyc = "C:/g17/probe/pyc_" + tag
    os.makedirs(pyc, exist_ok=True)
    env = dict(os.environ, PYTHONPYCACHEPREFIX=pyc, PYTHONDONTWRITEBYTECODE="1")
    cmd = [sys.executable, "-P", "-m", "pytest", "-c", INI, "--rootdir=" + work, "--confcutdir=" + work, "-q",
           "-p", "no:cacheprovider", work + "/" + TEST]
    r = subprocess.run(cmd, cwd=work, capture_output=True, env=env)
    out = r.stdout.decode("utf-8", "replace")
    return {"cmd": " ".join(cmd), "exit": r.returncode, "tail": out[-1500:]}


nogit = "C:/g17/probe/nogit_copy"
if os.path.exists(nogit):
    shutil.rmtree(nogit)
shutil.copytree(SRC, nogit, ignore=shutil.ignore_patterns(".git"))
res["copytree_no_git"] = pytest(nogit, "nogit")

clone = "C:/g17/probe/hist_clone"
if os.path.exists(clone):
    subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", clone.replace("/", "\\")])
head = subprocess.run(["git", "-C", SRC, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
c1 = subprocess.run(["git", "clone", "-q", "--no-hardlinks", "--no-local", "-c", "core.longpaths=true", "--no-checkout",
                     SRC, clone], capture_output=True, text=True)
c2 = subprocess.run(["git", "-C", clone, "remote", "remove", "origin"], capture_output=True, text=True)
c3 = subprocess.run(["git", "-C", clone, "checkout", "-q", "--detach", head], capture_output=True, text=True)
res["clone_steps"] = [c1.returncode, c2.returncode, c3.returncode, c1.stderr + c2.stderr + c3.stderr]
res["history_clone"] = pytest(clone, "clone")
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps({k: (v if k == "clone_steps" else {"exit": v["exit"], "tail": v["tail"][-600:]}) for k, v in res.items()},
                 ensure_ascii=False, indent=1))
