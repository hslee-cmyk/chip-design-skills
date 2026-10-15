import json


def read_front_entries(run_dir):
    p = run_dir / "runs.jsonl"
    if not p.is_file():
        return ()
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        for e in rec["front"] + rec["pending_front"]:
            out.append(dict(e, run_id=rec["run_id"], code_fp=rec["code_fp"]))
    return tuple(out)
