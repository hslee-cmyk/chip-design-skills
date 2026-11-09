"""base mutate_changed.py를 redteam 31 sandbox(보존본)에 --out으로 다시 돌려 변이별 사유를 얻는다(격리 C:/g17)."""
import json
import os
import subprocess
import sys

V = "C:/g17/tmp/gmid-redteam/20260930-195723-direct/31-v3-git-history-tui_wc21/v"
STEPS = [
    ("git-history-kill", "93882c5e3331bcb811cccf35a6f69a4dfbaae301", "18282e150b640d0cc2e8307013f604aaf9fda589"),
    ("baseline-fail-error", "e0d05d3e4c1d96eebe55aa5de3c677eec6aa27b3", "e6525b5f30da52cb563c14e9b990553525278b06"),
    ("survivor-fail-clean", "51fc28b02f1274e4f005b8e570573074aa64d615", "a6db4ad6aa1ff5c2111acf7862a69066620736aa"),
]
OUT = "C:/g17/probe/red_reason.json"
res = {}
for name, b, h in STEPS:
    tmp = "C:/g17/probe/tmp_" + name
    os.makedirs(tmp, exist_ok=True)
    out = "C:/g17/probe/%s.out.jsonl" % name
    if os.path.exists(out):
        os.remove(out)
    env = dict(os.environ, TEMP=tmp, TMP=tmp, TMPDIR=tmp, PYTHONDONTWRITEBYTECODE="1")
    root = V + "/" + name
    cmd = [sys.executable, "C:/g17/gate/mutate_changed.py", "--root", root, "--base", b, "--head", h,
           "--pytest-ini", "C:/g17/gate/pytest_gate.ini", "--out", out]
    r = subprocess.run(cmd, capture_output=True, env=env)
    recs = [json.loads(l) for l in open(out, encoding="utf-8")] if os.path.exists(out) else []
    log = subprocess.run(["git", "-C", root, "log", "--format=%H %s"], capture_output=True, text=True).stdout
    rem = subprocess.run(["git", "-C", root, "remote"], capture_output=True, text=True).stdout
    res[name] = {"cmd": " ".join(cmd), "exit": r.returncode, "stdout": r.stdout.decode("utf-8", "replace"),
                 "stderr": r.stderr.decode("utf-8", "replace")[-800:], "records": recs, "root_log": log,
                 "root_remote": rem, "tmp_left": sorted(os.listdir(tmp))}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
