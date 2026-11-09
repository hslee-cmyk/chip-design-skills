"""B33 개정 측정 3: 복제본(시뮬레이션 head/base)에서 run_all.py를 변형별로 돌리고 단계별 exit를 모은다.
    python -B run_redteam_variants.py <out.jsonl> <clone>:<variant>[,<variant>...] ... -- <run_all 인자...>
TMP/TEMP는 C:/g64/tmp(호출 환경에서 지정). 결과는 케이스·단계마다 out.jsonl에 append."""
import glob
import json
import os
import subprocess
import sys

out = sys.argv[1]
i = sys.argv.index("--")
targets, ra_args = sys.argv[2:i], sys.argv[i + 1:]
for t in targets:
    clone, variants = t.rsplit(":", 1)
    for v in variants.split(","):
        logs_before = set(glob.glob(os.path.join(clone, "tools/gates/redteam/logs/*.jsonl")))
        env = dict(os.environ)
        if v != "-":
            env["RCH_VARIANT"] = v
        else:
            env.pop("RCH_VARIANT", None)
        r = subprocess.run([sys.executable, "-B", os.path.join(clone, "tools/gates/redteam/run_all.py")] + ra_args,
                           cwd=clone, env=env, capture_output=True, timeout=7000)
        new = sorted(set(glob.glob(os.path.join(clone, "tools/gates/redteam/logs/*.jsonl"))) - logs_before)
        with open(out, "a", encoding="utf-8") as f:
            for lg in new:
                for line in open(lg, encoding="utf-8"):
                    o = json.loads(line)
                    if o.get("summary"):
                        f.write(json.dumps({"clone": clone, "variant": v, "summary": o}, ensure_ascii=False) + "\n")
                        continue
                    for s in o.get("steps", []) or [{"step": "-", "verdict": o.get("verdict"), "why": o.get("reason")}]:
                        f.write(json.dumps({"clone": clone, "variant": v, "case": o["case"], "case_verdict": o["verdict"],
                                            "step": s.get("step"), "exit": s.get("exit"), "verdict": s.get("verdict"),
                                            "why": (s.get("why") or "")[:300]}, ensure_ascii=False) + "\n")
        print(clone, v, "rc", r.returncode, r.stdout.decode("utf-8", "replace").strip().splitlines()[-2:])
