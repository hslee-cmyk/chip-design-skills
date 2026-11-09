"""B33 최종 card 재측정: 7535799 이후 새로 생긴 V7 판정 기록 쌍(20260930-p9-kcl-edges)의 base 도구 vs 시제품(fixed).
결과는 C:/g80/m4_one.jsonl 에 append."""
import importlib.util
import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout

ROOT = "C:/g80/clone"
OUT = "C:/g80/m4_one.jsonl"
PROTO = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b33_scripts/reachability_b33.py"
pairs = [tuple(a.split(":")) for a in sys.argv[1:]]


def load(path, name, variant=None):
    if variant:
        os.environ["RCH_VARIANT"] = variant
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


tools = {"base": load(os.path.join(ROOT, "tools/gates/reachability.py"), "rb"), "fixed": load(PROTO, "rf", "fixed")}
for b, h in pairs:
    cfg = "C:/g80/tmp/cfg_%s.json" % h[:10]
    with open(cfg, "wb") as f:
        f.write(subprocess.run(["git", "-C", ROOT, "show", h + ":tools/gates/gate_config.json"], capture_output=True, check=True).stdout)
    row = {"base_commit": b, "head_commit": h}
    for k, m in tools.items():
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = m.main(["--root", ROOT, "--base", b, "--head", h, "--config", cfg])
        j = json.loads(buf.getvalue().strip().splitlines()[0])
        row[k] = {"exit": rc, "verdict": j.get("verdict"), "new_defs": j.get("new_defs"), "unreached": j.get("unreached"),
                  "uwa": j.get("unreached_without_approval")}
    row["same"] = all(row["fixed"][x] == row["base"][x] for x in ("verdict", "unreached", "uwa"))
    with open(OUT, "a", encoding="utf-8") as o:
        o.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False))
