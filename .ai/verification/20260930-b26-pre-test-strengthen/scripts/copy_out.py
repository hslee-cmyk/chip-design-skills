"""순서 7 산출물을 판정 기록 폴더(audit worktree .ai/verification/<id>/)로 복사한다(큰 out.jsonl·kit 사본 제외 -- 해시는 kill_summary.json)."""
import os
import shutil

V = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-pre-test-strengthen-audit/.ai/verification/20260930-b26-pre-test-strengthen"
O = "C:/g372/out"
dst = V + "/out/order7"
os.makedirs(dst + "/kill_logs", exist_ok=True)
skip = {"executed_lines.json", "junit_base.xml", "v3_b26v4.out.jsonl", "v3_b26v5.out.jsonl", "plan_names.txt"}
for f in sorted(os.listdir(O)):
    p = os.path.join(O, f)
    if os.path.isfile(p) and f not in skip:
        shutil.copyfile(p, os.path.join(dst, f))
for f in sorted(os.listdir(O + "/kill_logs")):
    shutil.copyfile(O + "/kill_logs/" + f, dst + "/kill_logs/" + f)
for f in sorted(os.listdir("C:/g372/scripts")):
    if f.endswith((".py", ".sh")) and f not in ("extract_gate.py", "cache_cmp.py", "adapt.py") or f == "adapt.py":
        shutil.copyfile("C:/g372/scripts/" + f, V + "/scripts/" + f)
print(len(os.listdir(dst)), len(os.listdir(dst + "/kill_logs")), sorted(os.listdir(V + "/scripts")))
