"""병합본 mutate_changed.main을 그대로 부르되 pytest 하위 프로세스의 출력을 C:/g17/o7/spy_log.json에 남긴다(진단)."""
import json
import subprocess
import sys

sys.path.insert(0, "C:/g17/isom/tools/gates")
import mutate_changed as mc  # noqa: E402

real = subprocess.run
log = []


def spy(cmd, *a, **kw):
    r = real(cmd, *a, **kw)
    if "pytest" in cmd:
        log.append({"cmd": cmd, "cwd": kw.get("cwd"), "rc": r.returncode,
                    "env_diff": {k: v for k, v in (kw.get("env") or {}).items() if k.startswith(("PY", "TMP", "TEMP"))},
                    "out": (r.stdout or b"").decode("utf-8", "replace")[-4000:], "err": (r.stderr or b"").decode("utf-8", "replace")[-4000:]})
        with open("C:/g17/o7/spy_log.json", "w", encoding="utf-8") as fh:
            json.dump(log, fh, ensure_ascii=False, indent=1)
    return r


mc.subprocess.run = spy
sys.exit(mc.main(sys.argv[1:]))
