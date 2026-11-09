"""G7 사실(측정 전용): 판정 기록 2건(df36·dup-w-calc) base->head 옮긴 단위 + 엔진 4파일 사실(star·global·multi·qualname 중복·클래스).

  $PY -B g7_facts.py [--scratch C:/g<n>] [--gates <시제품 tools/gates>] [--repo <base 복제본>] [--rev <rev>] [--out <json>]
  기본값: --scratch C:/g143, --gates <scratch>/p/tools/gates, --repo <scratch>/b, --rev HEAD,
          --out <이 키트>/out/g7_facts_<--repo에서 --rev의 짧은 sha>.json
  경로 인자는 절대 경로만 받는다 -- '.'·빈 값·상대 경로·현재 디렉터리·저장소(chip-design-skills·gmid-gate.git) 안은 거부(exit 1, 메시지 '[거부]').
"""
import argparse, ast, json, os, re, subprocess, sys

KIT = os.path.dirname(os.path.abspath(__file__))
FORBID = [os.path.normcase(os.path.abspath(p)) for p in (
    "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills",
    "C:/Users/HSLEE/Documents/Todoc/fpga/gmid-gate.git")]


def _abs(name, p, must_exist=True):
    if p in (".", "") or not re.match(r"^[A-Za-z]:[/\\]", p):
        sys.exit("[거부] --%s: 드라이브 문자로 시작하는 절대 경로만 받는다('.'·상대 경로 금지): %r" % (name, p))
    a = os.path.normcase(os.path.abspath(p))
    if a == os.path.normcase(os.getcwd()):
        sys.exit("[거부] --%s: 현재 디렉터리를 가리킨다: %r" % (name, p))
    for f in FORBID:
        if a == f or a.startswith(f + os.sep):
            sys.exit("[거부] --%s: 저장소 안을 가리킨다: %r" % (name, p))
    if must_exist and not os.path.exists(p):
        sys.exit("[거부] --%s: 없다: %r" % (name, p))
    return p


ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default="C:/g143")
ap.add_argument("--gates")
ap.add_argument("--repo")
ap.add_argument("--rev", default="HEAD")
ap.add_argument("--out")
a = ap.parse_args()
if not re.match(r"^[Cc]:/g\d+$", a.scratch.rstrip("/")):
    sys.exit("[거부] --scratch는 C:/g<n>: %r" % a.scratch)
S = a.scratch.rstrip("/")
GATES = _abs("gates", a.gates or S + "/p/tools/gates")
R = _abs("repo", a.repo or S + "/b")
short = subprocess.run(["git", "-C", R, "rev-parse", "--short=7", a.rev], capture_output=True, text=True, check=True).stdout.strip()
OUT = _abs("out", a.out or os.path.join(KIT, "out", "g7_facts_%s.json" % short), must_exist=False)

sys.path.insert(0, GATES)
import reachability as g1

out = {"repo": R, "rev": a.rev, "rev_short": short, "gates": GATES}
for rid, (b, h) in {"df36": ("070cf69", "ed98d35"), "dup-w-calc": ("b7d1798", "a9de49c")}.items():
    bt = g1.read_tree(R, b, g1.SOURCE_GLOBS); ht = g1.read_tree(R, h, g1.SOURCE_GLOBS)
    mv = g1.moved_defs({k: v for k, v in bt.items() if g1._is_source(k)}, {k: v for k, v in ht.items() if g1._is_source(k)})
    out[rid] = {k: len(mv[k]) for k in ("units", "defs", "rejected")}
# 엔진 사실(--rev 판, SourceIndex)
ht = g1.read_tree(R, a.rev, g1.SOURCE_GLOBS)
AS = "skills/analog-gmid-design/assets/"
MODS = ("sizing_recipe", "stick_diagram", "topology_library", "design_report")
H = g1.SourceIndex({AS + m + ".py": ht[AS + m + ".py"] for m in MODS})
facts = {}
for m in MODS:
    md = H.mod(AS + m + ".py")
    cls = [n for n in md.tree.body if isinstance(n, ast.ClassDef)]
    facts[m] = {"star": "*" in md.bindings, "global": sorted(md.global_declared), "futures": sorted(md.futures),
                "multi": sorted(n for n, b in md.bindings.items() if len(b) > 1), "qual_dups": sorted(q for q, c in md.qcount.items() if c > 1),
                "classes": len(cls), "classes_no_method": sum(1 for c in cls if not any(isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) for x in ast.walk(c))),
                "units": len(md.units), "defs": len(g1.iter_defs(md.tree))}
out["facts"] = facts
print(json.dumps(out, ensure_ascii=False, indent=0))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print("wrote", OUT)
