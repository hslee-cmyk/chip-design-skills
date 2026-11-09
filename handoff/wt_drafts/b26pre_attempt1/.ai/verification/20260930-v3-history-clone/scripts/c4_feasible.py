"""계약 4 측정 설계의 실현성: 합성 저장소에서 --base/--head 밖 ref의 loose object만 깨뜨리면
diff·read_tree(= 도구 앞단)는 되고 git clone --no-hardlinks --no-local은 실패하는가(격리 C:/g17)."""
import json
import os
import shutil
import stat
import subprocess

R = "C:/g17/probe/c4repo"
OUT = "C:/g17/probe/c4_feasible.json"


def g(*a, cwd=R, check=True):
    r = subprocess.run(["git", "-C", cwd, *a], capture_output=True)
    if check and r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r


def rm(p):
    if os.path.exists(p):
        def onerr(f, path, _):
            os.chmod(path, stat.S_IWRITE)
            f(path)
        shutil.rmtree(p, onerror=onerr)


rm(R)
os.makedirs(R)
g("init", "-q", "-b", "master")
g("config", "user.email", "a@b")
g("config", "user.name", "a")
g("config", "core.autocrlf", "false")
eng = os.path.join(R, "skills/analog-gmid-design/assets")
os.makedirs(eng)
open(os.path.join(eng, "rt_engine.py"), "w", newline="\n").write("def rt_gain(gm, ro):\n    return gm * ro\n")
g("add", "-A")
g("commit", "-q", "-m", "base")
base = g("rev-parse", "HEAD").stdout.decode().strip()
open(os.path.join(eng, "rt_engine.py"), "a", newline="\n").write("\n\ndef rt_scale(x):\n    return 3.0 * x\n")
g("add", "-A")
g("commit", "-q", "-m", "head")
head = g("rev-parse", "HEAD").stdout.decode().strip()
# base/head 밖 ref: side 브랜치에만 있는 blob
g("checkout", "-q", "-b", "side")
open(os.path.join(R, "side_only.txt"), "w", newline="\n").write("side only blob c4\n")
g("add", "-A")
g("commit", "-q", "-m", "side")
blob = g("rev-parse", "HEAD:side_only.txt").stdout.decode().strip()
g("checkout", "-q", "master")
obj = os.path.join(R, ".git", "objects", blob[:2], blob[2:])
os.chmod(obj, stat.S_IWRITE)
with open(obj, "wb") as fh:
    fh.write(b"corrupt")
res = {"base": base, "head": head, "corrupted_blob": blob}
res["diff_ok"] = g("diff", "--name-only", base, head, check=False).returncode
res["show_head_ok"] = g("show", head + ":skills/analog-gmid-design/assets/rt_engine.py", check=False).returncode
dst = "C:/g17/probe/c4clone"
rm(dst)
c = subprocess.run(["git", "clone", "-q", "--no-hardlinks", "--no-local", "-c", "core.longpaths=true", R, dst],
                   capture_output=True)
res["clone_exit"] = c.returncode
res["clone_stderr"] = c.stderr.decode("utf-8", "replace")[-600:]
res["clone_dir_left"] = os.path.exists(dst)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
