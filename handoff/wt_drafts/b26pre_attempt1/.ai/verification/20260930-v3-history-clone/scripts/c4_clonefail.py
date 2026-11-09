"""계약 4·5 측정(순서 7에서 병합본 도구로 재사용, 지금은 base 도구로 기준값).
합성 저장소: base·head 모두에 같은 비-.py 파일 docs/blob.txt(GRAPH_PREFIXES 밖, base..head diff에 없음)를 두고
그 loose object를 깨뜨린다 -> 도구 앞단(diff --name-only, ls-tree/show head:assets .py, approvals ls-tree)은 되고
그 blob을 담아야 하는 git clone(어떤 형태든 --head 트리를 받으면)은 실패한다.
기대(계약 4): exit 2, stdout JSON 한 줄 verdict ERROR, stderr에 Traceback 없음. 계약 5: 도구 TMP에 남은 항목 0.
사용: python c4_clonefail.py <mutate_changed.py> <pytest_gate.ini> <출력 json>"""
import json
import os
import shutil
import stat
import subprocess
import sys

TOOL, INI, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
BASEDIR = "C:/g17/probe/c4"
R = BASEDIR + "/root"
TMPD = BASEDIR + "/tooltmp"


def rm(p):
    if os.path.exists(p):
        def onerr(f, path, _):
            os.chmod(path, stat.S_IWRITE)
            f(path)
        shutil.rmtree(p, onerror=onerr)


def g(*a, check=True):
    r = subprocess.run(["git", "-C", R, *a], capture_output=True)
    if check and r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r


def w(rel, text):
    p = os.path.join(R, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


ENG0 = "def rt_gain(gm, ro):\n    return gm * ro\n"
ENG1 = ENG0 + "\n\ndef rt_scale(x):\n    return 3.0 * x\n"
TEST = ("import sys\nfrom pathlib import Path\n\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
        "from rt_engine import rt_scale\n\n\ndef test_rt_scale():\n    assert rt_scale(2.0) == 6.0\n")

rm(BASEDIR)
os.makedirs(R)
os.makedirs(TMPD)
g("init", "-q", "-b", "master")
g("config", "user.email", "a@b")
g("config", "user.name", "a")
g("config", "core.autocrlf", "false")
w("skills/analog-gmid-design/assets/rt_engine.py", ENG0)
w("docs/blob.txt", "c4 blob outside graph prefixes\n")
g("add", "-A")
g("commit", "-q", "-m", "base")
base = g("rev-parse", "HEAD").stdout.decode().strip()
w("skills/analog-gmid-design/assets/rt_engine.py", ENG1)
w("skills/analog-gmid-design/assets/tests/test_rt_scale.py", TEST)
g("add", "-A")
g("commit", "-q", "-m", "head")
head = g("rev-parse", "HEAD").stdout.decode().strip()
blob = g("rev-parse", "HEAD:docs/blob.txt").stdout.decode().strip()
obj = os.path.join(R, ".git", "objects", blob[:2], blob[2:])
os.chmod(obj, stat.S_IWRITE)
with open(obj, "wb") as fh:
    fh.write(b"corrupt")
pre = {"diff": g("diff", "--name-only", base, head, check=False).returncode,
       "show_engine": g("show", head + ":skills/analog-gmid-design/assets/rt_engine.py", check=False).returncode,
       "fsck_detects": g("fsck", "--full", check=False).returncode}
parent_before = sorted(os.listdir(BASEDIR))
env = dict(os.environ, TMP=TMPD, TEMP=TMPD, TMPDIR=TMPD, PYTHONDONTWRITEBYTECODE="1")
cmd = [sys.executable, TOOL, "--root", R, "--base", base, "--head", head, "--pytest-ini", INI]
r = subprocess.run(cmd, capture_output=True, env=env, cwd=R)
stdout = r.stdout.decode("utf-8", "replace")
stderr = r.stderr.decode("utf-8", "replace")
lines = [l for l in stdout.splitlines() if l.strip()]
res = {"tool": TOOL, "base": base, "head": head, "corrupted_blob": blob, "pre": pre, "cmd": " ".join(cmd),
       "exit": r.returncode, "stdout": stdout, "stdout_nonempty_lines": len(lines),
       "stderr_tail": stderr[-1500:], "traceback_in_stderr": "Traceback" in stderr,
       "tmp_left": sorted(os.listdir(TMPD)),
       "root_parent_new_entries": sorted(set(os.listdir(BASEDIR)) - set(parent_before))}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("pre", "exit", "stdout", "stdout_nonempty_lines", "traceback_in_stderr",
                                      "tmp_left", "root_parent_new_entries")}, ensure_ascii=False))
