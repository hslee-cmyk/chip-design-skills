"""계약 3 측정(순서 7에서 병합본 도구로 재사용, 지금은 base 도구로 기준값).
합성 저장소 head에서 바뀐 def 셋:
  rt_scale  -- 인벤토리 test가 항상 실패(rt_scale(2.0) == 7.0)        -> 기준 실행 실패 인벤토리
  rt_orphan -- 도달하는 test 없음                                      -> 인벤토리 없음(생존 유지 기대)
  rt_twice  -- 인벤토리 test가 0 입력만 봄(rt_twice(0.0) == 0.0)        -> 기준 통과, 상수 변이 생존
기대(계약 3): verdict ERROR, exit 2, 실패 인벤토리 test id 출력, rt_scale 변이는 survivors/--out survived에 없음,
rt_orphan 변이는 survived 그대로(사유 '인벤토리 없음'), rt_twice 생존 변이도 survived.
사용: python c3_mixed.py <mutate_changed.py> <pytest_gate.ini> <출력 json>"""
import json
import os
import shutil
import stat
import subprocess
import sys

TOOL, INI, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
BASEDIR = "C:/g17/probe/c3"
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
ENG1 = ENG0 + ("\n\ndef rt_scale(x):\n    return 3.0 * x\n"
               "\n\ndef rt_orphan(x):\n    return x + 1\n"
               "\n\ndef rt_twice(x):\n    return 2.0 * x\n")
HDR = "import sys\nfrom pathlib import Path\n\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
T_SEVEN = HDR + "from rt_engine import rt_scale\n\n\ndef test_rt_scale_seven():\n    assert rt_scale(2.0) == 7.0\n"
T_TWICE = HDR + "from rt_engine import rt_twice\n\n\ndef test_rt_twice_zero():\n    assert rt_twice(0.0) == 0.0\n"

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
w("skills/analog-gmid-design/assets/tests/test_rt_seven.py", T_SEVEN)
w("skills/analog-gmid-design/assets/tests/test_rt_twice.py", T_TWICE)
g("add", "-A")
g("commit", "-q", "-m", "head")
head = g("rev-parse", "HEAD").strip()
env = dict(os.environ, TMP=TMPD, TEMP=TMPD, TMPDIR=TMPD, PYTHONDONTWRITEBYTECODE="1")
cmd = [sys.executable, TOOL, "--root", R, "--base", base, "--head", head, "--pytest-ini", INI,
       "--out", BASEDIR + "/out.jsonl"]
r = subprocess.run(cmd, capture_output=True, env=env, cwd=R)
recs = []
if os.path.exists(BASEDIR + "/out.jsonl"):
    recs = [json.loads(l) for l in open(BASEDIR + "/out.jsonl", encoding="utf-8")]
stdout = r.stdout.decode("utf-8", "replace")
first = None
for line in stdout.splitlines():
    try:
        first = json.loads(line)
        break
    except ValueError:
        continue
by_fn = {}
for x in recs:
    fn = x["id"].split(":")[1]
    by_fn.setdefault(fn, []).append(x["result"])
surv = (first or {}).get("survivors", (first or {}).get("survived"))
res = {"tool": TOOL, "base": base, "head": head, "cmd": " ".join(cmd), "exit": r.returncode, "stdout": stdout,
       "stderr_tail": r.stderr.decode("utf-8", "replace")[-1500:], "records": recs, "results_by_fn": by_fn,
       "stdout_keys": sorted(first) if first else None,
       "survivor_fns": sorted({s.split(":")[1] for s in surv}) if isinstance(surv, list) else None,
       "failing_test_id_in_stdout": "test_rt_seven.py::test_rt_scale_seven" in stdout,
       "tmp_left": sorted(os.listdir(TMPD))}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("exit", "stdout_keys", "survivor_fns", "results_by_fn",
                                      "failing_test_id_in_stdout", "tmp_left")}, ensure_ascii=False))
print(stdout)
