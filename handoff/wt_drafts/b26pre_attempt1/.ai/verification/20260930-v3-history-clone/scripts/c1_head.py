"""계약 1 '사본 HEAD = --head' 측정(순서 7에서 병합본 도구로 재사용, 지금은 base 도구로 기준값).
합성 저장소: base -> head(rt_scale 3배 + 인벤토리 test) -> after-head(root HEAD, --head 아님), 그리고 root 작업 트리에
미커밋 변경(rt_engine.py를 4배로)과 추적 안 된 표지 파일. 인벤토리 test는 사본에서
  git log -1 --format=%s == 'head', 표지 파일 없음, git status --porcelain 빈 값, rt_scale(2.0) == 6.0
을 단언한다. 사본이 --head 커밋이면 기준 실행 통과·변이 전부 죽음(exit 0), root 작업 트리·root HEAD 사본이면 기준 실행 실패.
사용: python c1_head.py <mutate_changed.py> <pytest_gate.ini> <출력 json>"""
import json
import os
import shutil
import stat
import subprocess
import sys

TOOL, INI, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
BASEDIR = "C:/g17/probe/c1"
R = BASEDIR + "/root"
TMPD = BASEDIR + "/tooltmp"


def rm(p):
    if os.path.exists(p):
        def onerr(f, path, _):
            os.chmod(path, stat.S_IWRITE)
            f(path)
        shutil.rmtree(p, onerror=onerr)


def g(*a):
    r = subprocess.run(["git", "-C", R, *a], capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8")


def w(rel, text):
    p = os.path.join(R, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


ENG0 = "def rt_gain(gm, ro):\n    return gm * ro\n"
ENG1 = ENG0 + "\n\ndef rt_scale(x):\n    return 3.0 * x\n"
TEST = '''import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rt_engine import rt_scale

ROOT = Path(__file__).resolve().parents[4]


def _git(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    return r.stdout.decode("utf-8")


def test_copy_is_head_commit():
    assert Path(_git("rev-parse", "--show-toplevel").strip()).resolve() == ROOT
    assert _git("log", "-1", "--format=%s").strip() == "head"
    assert not (ROOT / "UNCOMMITTED_MARKER.txt").exists()
    assert _git("status", "--porcelain", "--untracked-files=all").strip() == ""
    assert rt_scale(2.0) == 6.0
'''

rm(BASEDIR)
os.makedirs(R)
os.makedirs(TMPD)
g("init", "-q", "-b", "master")
g("config", "user.email", "a@b")
g("config", "user.name", "a")
g("config", "core.autocrlf", "false")
w("skills/analog-gmid-design/assets/rt_engine.py", ENG0)
g("add", "-A")
g("commit", "-q", "-m", "base")
base = g("rev-parse", "HEAD").strip()
w("skills/analog-gmid-design/assets/rt_engine.py", ENG1)
w("skills/analog-gmid-design/assets/tests/test_copy_head.py", TEST)
g("add", "-A")
g("commit", "-q", "-m", "head")
head = g("rev-parse", "HEAD").strip()
w("AFTER_HEAD.txt", "after head\n")
g("add", "-A")
g("commit", "-q", "-m", "after-head")
root_head = g("rev-parse", "HEAD").strip()
# 미커밋 변경: 엔진을 4배로(작업 트리만), 추적 안 된 표지
w("skills/analog-gmid-design/assets/rt_engine.py", ENG0 + "\n\ndef rt_scale(x):\n    return 4.0 * x\n")
w("UNCOMMITTED_MARKER.txt", "uncommitted\n")


def state():
    return (g("for-each-ref"), g("status", "--porcelain", "--ignored", "--untracked-files=all"),
            g("worktree", "list", "--porcelain"))


before = state()
parent_before = sorted(os.listdir(BASEDIR))
env = dict(os.environ, TMP=TMPD, TEMP=TMPD, TMPDIR=TMPD, PYTHONDONTWRITEBYTECODE="1")
cmd = [sys.executable, TOOL, "--root", R, "--base", base, "--head", head, "--pytest-ini", INI,
       "--out", BASEDIR + "/out.jsonl"]
r = subprocess.run(cmd, capture_output=True, env=env, cwd=R)
recs = []
if os.path.exists(BASEDIR + "/out.jsonl"):
    recs = [json.loads(l) for l in open(BASEDIR + "/out.jsonl", encoding="utf-8")]
res = {"tool": TOOL, "base": base, "head": head, "root_head": root_head, "cmd": " ".join(cmd), "exit": r.returncode,
       "stdout": r.stdout.decode("utf-8", "replace"), "stderr_tail": r.stderr.decode("utf-8", "replace")[-1500:],
       "records": recs, "tmp_left": sorted(os.listdir(TMPD)), "root_unchanged": state() == before,
       "root_parent_new_entries": sorted(set(os.listdir(BASEDIR)) - set(parent_before) - {"out.jsonl"})}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("exit", "stdout", "tmp_left", "root_unchanged", "root_parent_new_entries")},
                 ensure_ascii=False))
print(sorted({x.get("reason") or x["result"] for x in recs}))
