"""p8 교차(auditor): 같은 모의 커밋에서 순서 3 auditor 분류기(disc35.py classify -- 계약 1 auditor 구현)로 고른 대상 id 집합과
병합본 도구 `--out`(probe_selection 실행 기록)의 대상 id 집합을 대조한다. 변이 생성은 도구 경로 그대로(diff -> _is_source -> changed_defs -> mutants).
사용: python -B p8_disc_cross.py <병합본 tools/gates> <disc35.py> <root> <base> <head> <probe jsonl> <출력 json>"""
import ast
import json
import subprocess
import sys

TG, DISC, ROOT, BASE, HEAD, PJ, OUTP = sys.argv[1:8]
sys.path.insert(0, TG)
import mutate_changed as mc   # noqa: E402
import reachability as rch    # noqa: E402

src = open(DISC, encoding="utf-8").read().split("# ---------------------------------------------------------------- 합성 저장소")[0]
src = src.replace("vjson, gate, work, outp = sys.argv[1:5]", "")
DC = {}
exec(compile(src, DISC, "exec"), DC)


def git(*a):
    return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, check=True).stdout.decode("utf-8")


diff = git("diff", "--name-only", "--no-renames", "--diff-filter=AM", BASE, HEAD)
targets = [p for p in diff.splitlines() if p.endswith(".py") and rch._is_source(p)]
mine = []
alln = 0
for path in targets:
    hsrc = git("show", "%s:%s" % (HEAD, path))
    rc = subprocess.run(["git", "-C", ROOT, "cat-file", "-e", "%s:%s" % (BASE, path)], capture_output=True).returncode
    bsrc = git("show", "%s:%s" % (BASE, path)) if rc == 0 else None
    bdefs = dict(rch.iter_defs(ast.parse(bsrc))) if bsrc else {}
    mod = rch.module_name(path)
    for q, hfn in mc.changed_defs(bsrc, hsrc):
        ms = mc.mutants(hfn, hsrc)
        alln += len(ms)
        mids = [("%s:%s:%s:%s" % (mod, q, op, p), op, p) for op, p, _ in ms]
        if q in bdefs:
            sel = DC["classify"](bdefs[q], hfn, mids)
        else:
            sel = {m for m, _, _ in mids}
        mine += [m for m, _, _ in mids if m in sel]
recs = [json.loads(l) for l in open(PJ, encoding="utf-8") if l.strip()]
tool = [r["id"] for r in recs if r["result"] != "not_targeted"]
res = {"base": BASE, "head": HEAD, "all": alln, "auditor_targeted": len(mine), "tool_targeted": len(tool),
       "missing_in_tool": sorted(set(mine) - set(tool)), "extra_in_tool": sorted(set(tool) - set(mine)),
       "same": set(mine) == set(tool)}
json.dump(res, open(OUTP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in res.items()}, ensure_ascii=False))
