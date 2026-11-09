"""B33 개정 측정 4: 과거 판정 기록 V7 쌍 무동작(base 도구 = 복제본 HEAD 도구, new = 시제품 fixed/draft).
    python -B m4_records.py <root(복제본, 이력 포함)> <out.jsonl> <base 도구 reachability.py>
--config는 head 트리의 tools/gates/gate_config.json(없으면 복제본 HEAD 것). 쌍마다 out.jsonl에 append."""
import glob
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT, OUT = sys.argv[1], sys.argv[2]
PAT = re.compile(r"reachability\.py\b.*?--base\s+([0-9a-f]{6,40})\s+--head\s+([0-9a-f]{6,40})")


def load(path, name, variant=None):
    if variant:
        os.environ["RCH_VARIANT"] = variant
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


BASETOOL = load(sys.argv[3], "rb")   # base 도구 = 원 HEAD reachability.py(복제본 base의 것)
tools = {"base": BASETOOL, "fixed": load(os.path.join(HERE, "reachability_b33.py"), "rf", "fixed"),
         "draft": load(os.path.join(HERE, "reachability_b33.py"), "rd", "draft")}


_TREE, _APPR = {}, {}
_orig_read_tree, _orig_appr = BASETOOL.read_tree, BASETOOL._approved_ids


def cached_read_tree(root, rev, prefixes):
    """같은 (rev, prefixes)는 한 번만 git show(세 도구가 공유 -- 결과 동일, 재계산만 없앤다)."""
    k = (rev, tuple(prefixes))
    if k not in _TREE:
        _TREE[k] = _orig_read_tree(root, rev, prefixes)
        if len(_TREE) > 8:
            _TREE.pop(next(iter(_TREE)))
    return dict(_TREE[k])


def cached_appr(root, rev):
    if rev not in _APPR:
        _APPR[rev] = _orig_appr(root, rev)
    return set(_APPR[rev])


for _m in tools.values():
    _m.read_tree = cached_read_tree
    _m._approved_ids = cached_appr
DONE = set()
if os.path.exists(OUT):
    for _l in open(OUT, encoding="utf-8"):
        _o = json.loads(_l)
        if _o.get("what") == "pair" and "error" not in _o:
            DONE.add((_o["base_commit"], _o["head_commit"]))


def git(*a):
    return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True)


def full(h):
    r = git("rev-parse", "--verify", h + "^{commit}")
    return r.stdout.decode().strip() if r.returncode == 0 else None


recs = sorted(glob.glob(os.path.join(ROOT, ".ai/verification/2026*.json")))
pairs = []
for f in recs:
    txt = open(f, encoding="utf-8").read()
    for b, h in PAT.findall(txt):
        pairs.append((os.path.basename(f)[:-5], b, h))
distinct = {}
for rid, b, h in pairs:
    fb, fh = full(b), full(h)
    distinct.setdefault((fb, fh), []).append((rid, b, h))
with open(OUT, "a", encoding="utf-8") as o:
    o.write(json.dumps({"what": "scan", "records_with_pairs": len({p[0] for p in pairs}), "pairs_regex": len(pairs),
                        "distinct_pairs": len(distinct)}, ensure_ascii=False) + "\n")
for (fb, fh), srcs in distinct.items():
    if (fb, fh) in DONE:
        continue
    row = {"what": "pair", "records": sorted({s[0] for s in srcs}), "base_commit": fb, "head_commit": fh, "n_regex": len(srcs)}
    if not fb or not fh:
        row["error"] = "커밋 없음"
    else:
        cfg_ok = git("cat-file", "-e", fh + ":tools/gates/gate_config.json").returncode == 0
        row["config_from_head"] = cfg_ok
        cfgpath = None
        if cfg_ok:
            cfgpath = os.path.join(os.environ.get("TMP", "."), "cfg_%s.json" % fh[:10])
            with open(cfgpath, "wb") as fh_:
                fh_.write(git("show", fh + ":tools/gates/gate_config.json").stdout)
        for k, m in tools.items():
            buf = io.StringIO()
            args = ["--root", ROOT, "--base", fb, "--head", fh] + (["--config", cfgpath] if cfgpath else
                                                                   ["--config", os.path.join(ROOT, "tools/gates/gate_config.json")])
            with redirect_stdout(buf):
                rc = m.main(args)
            j = json.loads(buf.getvalue().strip().splitlines()[0])
            row[k] = {"exit": rc, "verdict": j.get("verdict"), "new_defs": j.get("new_defs"), "unreached": j.get("unreached"),
                      "uwa": j.get("unreached_without_approval")}
        row["same_fixed"] = all(row[k]["verdict"] == row["base"]["verdict"] and row[k]["uwa"] == row["base"]["uwa"]
                                and row[k]["unreached"] == row["base"]["unreached"] for k in ("fixed", "draft"))
    with open(OUT, "a", encoding="utf-8") as o:
        o.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(row.get("records"), row.get("same_fixed"), row.get("base", {}).get("verdict"), len(row.get("base", {}).get("new_defs") or []))
