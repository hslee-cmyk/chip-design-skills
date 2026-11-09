"""decision 승인 기록·면제 원소 집계(V3 면제 묶기 card 20260930-v3-exempt-binding '작성 전 실측' 1 셋째 항목).

착수 0단계에서 다시 돌린다 -- card의 집계 수치는 고정값이 아니라 이 출력이다.
저장소는 git ls-tree/show로만 읽는다(쓰기 없음, import로 저장소 파일을 열지 않음 -- reachability.py는 <rev> 판을
git show로 읽어 메모리에서 실행한다).

사용(Git Bash):
  C:/Python314/python.exe -B <이 파일> --repo <저장소> --rev "$(git -C <저장소> rev-parse gate/master)" --out <scratch>/census.txt

출력 항목:
  decision 기록 수와 이름, 기록별 원소 수
  _approved_ids(<rev>) 원소 수(도구가 실제로 읽는 집합 -- 자체 집계와 같아야 한다, 다르면 exit 1)
  V3 모양 원소 수, 기록별로 나눔
  V3 모양 원소마다: 모듈 basename에 맞는 <rev> 트리 .py 경로, 그중 V3 대상 영역(reachability._is_source) 여부,
                    @ 접미사(묶기 해시) 유무, 그 경로의 qualname def가 있으면 묶기 해시 앞 16자
"""
import argparse
import ast
import hashlib
import os
import re
import subprocess
import sys
import types

OPS = ("cmp_flip", "arith", "const+", "const-", "stmt_delete", "early_return", "except_body_delete")
V3_RE = re.compile(r"^[^:@\s]+:[^:@\s]+:(%s):\S+$" % "|".join(re.escape(o) for o in OPS))


def git(repo, *a):
    return subprocess.run(["git", "-C", repo] + list(a), capture_output=True, check=True).stdout


def bind_hash(fn):
    return hashlib.sha256(ast.dump(fn, annotate_fields=True, include_attributes=False, indent=None,
                                   show_empty=False).encode("utf-8")).hexdigest()


def load_rch(repo, rev):
    src = git(repo, "show", "%s:tools/gates/reachability.py" % rev).decode("utf-8")
    mod = types.ModuleType("reachability_at_rev")
    mod.__file__ = "<git %s:tools/gates/reachability.py>" % rev
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--rev", required=True)
    ap.add_argument("--out", required=True)
    ns = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    repo, rev = os.path.abspath(ns.repo), ns.rev
    lines = []

    def log(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        lines.append(s)

    full = git(repo, "rev-parse", rev).decode().strip()
    log("rev", full)
    names = [n for n in git(repo, "ls-tree", "-r", "--name-only", "--full-tree", full, "--", ".ai/approvals/")
             .decode("utf-8").splitlines() if n.endswith(".md") and not os.path.basename(n).startswith("_")]
    per = {}
    for n in names:
        t = git(repo, "show", "%s:%s" % (full, n)).decode("utf-8", "replace").replace("\r\n", "\n")
        if not t.startswith("---\n") or "\ntarget_kind: decision\n" not in t:
            continue
        els = set()
        for line in t.split("\n"):
            if line.startswith("target: "):
                els |= {x.strip() for x in line[len("target: "):].split(",")}
        per[os.path.basename(n)[:-3]] = els
    allels = set().union(*per.values()) if per else set()
    log("decision 기록", len(per))
    for k in sorted(per):
        nv3 = sum(1 for e in per[k] if V3_RE.match(e.split("@", 1)[0]))
        log("  %-45s 원소 %3d  V3 모양 %3d" % (k, len(per[k]), nv3))
    rch = load_rch(repo, full)
    tool = rch._approved_ids(repo, full)
    log("원소(자체 합집합)", len(allels), " _approved_ids(<rev>)", len(tool), " 같음", tool == allels)
    v3 = sorted(e for e in allels if V3_RE.match(e.split("@", 1)[0]))
    log("V3 모양 원소", len(v3), " 그중 @ 접미사 있음", sum(1 for e in v3 if "@" in e))
    tree = [p for p in git(repo, "ls-tree", "-r", "--name-only", "--full-tree", full).decode("utf-8").splitlines()
            if p.endswith(".py")]
    by_mod = {}
    for p in tree:
        by_mod.setdefault(rch.module_name(p), []).append(p)
    defs_cache = {}
    in_dom = out_dom = 0
    for e in v3:
        eid = e.split("@", 1)[0]
        mod, qual = eid.split(":")[0], eid.split(":")[1]
        paths = by_mod.get(mod, [])
        dom = [p for p in paths if rch._is_source(p)]
        if dom:
            in_dom += 1
        else:
            out_dom += 1
        info = []
        for p in paths:
            if p not in defs_cache:
                try:
                    defs_cache[p] = rch.iter_defs(ast.parse(git(repo, "show", "%s:%s" % (full, p)).decode("utf-8")))
                except SyntaxError:
                    defs_cache[p] = []
            hits = [fn for q, fn in defs_cache[p] if q == qual]
            h = ",".join(bind_hash(fn)[:16] for fn in hits) if hits else "no-def"
            info.append("%s[%s|bind %s]" % (p, "V3대상" if rch._is_source(p) else "V3대상밖", h))
        log("  %s  -> %s" % (e, "; ".join(info) if info else "모듈 경로 없음"))
    log("V3 모양 원소 중 V3 대상 영역(_is_source) 모듈", in_dom, " 대상 밖", out_dom)
    with open(ns.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0 if tool == allels else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
