"""FU spec card '작성 전 실측' 계약 2(함수 몸체 코드 객체 동일) -- 판정기 시제품.

사용: python -B fu_codeobj.py <base 트리> <head 트리> <out.json> [--selfcheck]  |  python -B fu_codeobj.py dump <트리>
  * DR(`design_report.py`)·ACF(`audit_current_forced.py`)를 두 트리에서 읽어 각각 compile하고, 모듈 코드 객체 아래의
    모든 코드 객체를 co_qualname(같은 qualname이 둘 이상이면 등장 순번을 붙임)으로 짝짓는다.
  * 비교 필드: co_code, co_consts(코드 객체 원소는 그 qualname으로 바꿔 비교), co_names, co_varnames, co_freevars,
    co_cellvars, co_argcount, co_posonlyargcount, co_kwonlyargcount, co_flags(__future__.annotations.compiler_flag 비트 제외).
  * 판정: 모듈 코드 객체(<module>)와 주석 평가 함수(qualname이 `__annotate__`로 끝남)를 뺀 짝이 모두 같고, 한쪽에만 있는
    qualname이 `__annotate__`뿐이면 PASS.
  * 그 밖 관찰: 두 트리 각각 하위 프로세스에서 모듈을 import해 최상위 함수 `__annotations__`(값 repr)와 모듈 이름 집합을 비교한다.
  --selfcheck: 판정기가 실제로 거부하는지 -- head DR의 첫 함수 몸체에 문장 하나를 더한 합성 소스로 FAIL이 나는지 본다.
결과는 <out.json>에 쓴다(실행마다 덮어씀 -- 한 번에 끝나는 짧은 실행).
"""
import __future__
import json
import subprocess
import sys
import types

A = "skills/analog-gmid-design/assets/"
FILES = ("design_report.py", "audit_current_forced.py")
FUT = __future__.annotations.compiler_flag
FIELDS = ("co_code", "co_names", "co_varnames", "co_freevars", "co_cellvars",
          "co_argcount", "co_posonlyargcount", "co_kwonlyargcount")


def walk(co, out, seen):
    q = co.co_qualname
    n = seen.get(q, 0)
    seen[q] = n + 1
    key = q if n == 0 else "%s#%d" % (q, n)
    out[key] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out, seen)
    return out


def norm_consts(co):
    return tuple(("<code %s>" % c.co_qualname) if isinstance(c, types.CodeType) else repr(c) for c in co.co_consts)


def diff_fields(a, b):
    d = [f for f in FIELDS if getattr(a, f) != getattr(b, f)]
    if norm_consts(a) != norm_consts(b):
        d.append("co_consts")
    if (a.co_flags & ~FUT) != (b.co_flags & ~FUT):
        d.append("co_flags")
    return d


def compare(bsrc, hsrc, name):
    bm = walk(compile(bsrc, name, "exec"), {}, {})
    hm = walk(compile(hsrc, name, "exec"), {}, {})
    same, differ, ann = [], {}, []
    for k in sorted(set(bm) | set(hm)):
        is_ann = k.split("#")[0].endswith("__annotate__")
        if k not in bm or k not in hm:
            (ann if is_ann else differ.setdefault("__only_one_side__", [])).append(k)
            continue
        if k == "<module>":
            continue
        d = diff_fields(bm[k], hm[k])
        if is_ann:
            if d:
                ann.append(k)
            continue
        if d:
            differ[k] = d
        else:
            same.append(k)
    return {"same_body_code_objects": same, "differ": differ, "annotate_only_diff": ann,
            "pass": not differ}


PROBE = r"""
import json, sys, inspect
sys.path.insert(0, sys.argv[1])
res = {}
for m in ("design_report", "audit_current_forced"):
    mod = __import__(m)
    fn = {n: {k: repr(v) for k, v in o.__annotations__.items()}
          for n, o in vars(mod).items() if inspect.isfunction(o) and o.__module__ == m}
    res[m] = {"names": sorted(vars(mod)), "fn_annotations": fn}
print(json.dumps(res))
"""


def probe(tree):
    r = subprocess.run([sys.executable, "-B", "-c", PROBE, tree + "/" + A], capture_output=True, text=True,
                       encoding="utf-8", cwd=tree)
    if r.returncode:
        return {"error": r.stderr[-2000:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def dump(tree):
    """equivalence 명령용: 한 트리의 DR·ACF 몸체 코드 객체 요약을 stdout에 쓴다(base·병합본 바이트 같아야 함).
    줄 = `<파일>::<qualname[#n]> <sha256(비교 필드 정규화)>`, 모듈 코드 객체·`__annotate__` 제외, 키 정렬."""
    import hashlib
    for f in FILES:
        src = open(tree + "/" + A + f, encoding="utf-8").read()
        m = walk(compile(src, f, "exec"), {}, {})
        for k in sorted(m):
            if k == "<module>" or k.split("#")[0].endswith("__annotate__"):
                continue
            co = m[k]
            payload = repr(([getattr(co, x) for x in FIELDS], norm_consts(co), co.co_flags & ~FUT))
            print("%s::%s %s" % (f, k, hashlib.sha256(payload.encode("utf-8")).hexdigest()))


def main():
    if sys.argv[1] == "dump":
        dump(sys.argv[2])
        return
    base, head, outp = sys.argv[1], sys.argv[2], sys.argv[3]
    res = {"base": base, "head": head, "files": {}}
    for f in FILES:
        bsrc = open(base + "/" + A + f, encoding="utf-8").read()
        hsrc = open(head + "/" + A + f, encoding="utf-8").read()
        res["files"][f] = compare(bsrc, hsrc, f)
        if "--selfcheck" in sys.argv and f == "design_report.py":
            # 합성 거부 입력: head의 첫 최상위 def 몸체 첫 줄 앞에 'pass' 문장 하나 -- 판정기가 FAIL을 내야 한다
            lines = hsrc.split("\n")
            i = next(j for j, l in enumerate(lines) if l.startswith("def "))
            while not lines[i].rstrip().endswith(":"):
                i += 1
            lines.insert(i + 1, "    _fu_selfcheck = 0")
            res["selfcheck_reject"] = compare(bsrc, "\n".join(lines), f)
    pb, ph = probe(base), probe(head)
    obs = {}
    for m in ("design_report", "audit_current_forced"):
        if "error" in pb or "error" in ph:
            obs = {"error": [pb.get("error"), ph.get("error")]}
            break
        nb, nh = set(pb[m]["names"]), set(ph[m]["names"])
        fb, fh = pb[m]["fn_annotations"], ph[m]["fn_annotations"]
        obs[m] = {"names_only_head": sorted(nh - nb), "names_only_base": sorted(nb - nh),
                  "functions": len(fb),
                  "functions_with_annotation_diff": sorted(k for k in fb if fb[k] != fh.get(k)),
                  "functions_with_annotations": sorted(k for k in fb if fb[k])}
    res["import_observation"] = obs
    res["pass"] = all(v["pass"] for v in res["files"].values())
    with open(outp, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"pass": res["pass"],
                      "same": {f: len(v["same_body_code_objects"]) for f, v in res["files"].items()},
                      "annotate_only_diff": {f: v["annotate_only_diff"] for f, v in res["files"].items()},
                      "selfcheck_pass": res.get("selfcheck_reject", {}).get("pass")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
