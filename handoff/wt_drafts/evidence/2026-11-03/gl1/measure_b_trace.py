"""GL-1 design 제안(공유 호출 B 분류 정의)의 실현 가능성 측정용 시제품. 구현물 아님(읽기 전용, 엔진 import 0).

실행: PYTHONIOENCODING=utf-8 C:/Python314/python.exe measure_b_trace.py <engine dir> <label>
결과: 같은 폴더 b_trace_<label>.tsv(callee마다 바로 append), 끝에 합계 stdout.
대조: 감사 classification.tsv의 B 함수가 B/D/not_B 어디로 가는지.
"""
import ast
import collections
import csv
import sys
from pathlib import Path

ENG = Path(sys.argv[1])
LABEL = sys.argv[2]
HERE = Path(__file__).resolve().parent
AUDIT = Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/shared_pure_fn_audit/classification.tsv")
DEPTH = 6


def mods():
    for p in sorted(ENG.rglob("*.py")):
        parts = p.relative_to(ENG).parts
        if parts[0] == "tests" or "__pycache__" in parts:
            continue
        m = "gmid_engine." + "/".join(parts)[:-3].replace("/", ".")
        if m.endswith(".__init__"):
            m = m[:-9]
        yield m, p


trees = {m: (p, ast.parse(p.read_text(encoding="utf-8"))) for m, p in mods()}
defs = {m: {n.name: n for n in t.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))} for m, (p, t) in trees.items()}


def resolve_from(m, node):
    if node.level == 0:
        return node.module
    parts = m.split(".")
    base = parts if trees[m][0].name == "__init__.py" else parts[:-1]
    base = base[: len(base) - (node.level - 1)]
    return ".".join(base + (node.module.split(".") if node.module else []))


def follow(mod, name, d=0):
    if d > 6 or mod not in trees:
        return None
    if name in defs[mod]:
        return (mod, name)
    for n in trees[mod][1].body:
        if isinstance(n, ast.ImportFrom):
            src = resolve_from(mod, n)
            for a in n.names:
                if (a.asname or a.name) == name:
                    r = follow(src, a.name, d + 1)
                    if r:
                        return r
    return None


def bindings(fn):
    """지역 이름 -> 값 식 목록. for·컴프리헨션 대상은 반복 식에 묶는다."""
    b = collections.defaultdict(list)

    def bind(t, v):
        if isinstance(t, ast.Name):
            b[t.id].append(v)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for e in t.elts:
                bind(e, v)
        elif isinstance(t, ast.Starred):
            bind(t.value, v)

    for x in ast.walk(fn):
        if isinstance(x, ast.Assign):
            for t in x.targets:
                bind(t, x.value)
        elif isinstance(x, (ast.AnnAssign, ast.AugAssign)) and x.value is not None:
            bind(x.target, x.value)
        elif isinstance(x, (ast.For, ast.comprehension)):
            bind(x.target, x.iter)
    return b


def params(fn):
    a = fn.args
    return [p.arg for p in a.posonlyargs + a.args + a.kwonlyargs] + ([a.vararg.arg] if a.vararg else []) + ([a.kwarg.arg] if a.kwarg else [])


class Sig:
    def __init__(self):
        self.fields = set()
        self.params = set()
        self.unknown = set()


def text(e, fn, m, sig, d=0, seen=()):
    """인자 식을 graph 필드·매개변수·리터럴 잎으로 치환한 문자열."""
    if d > DEPTH:
        sig.unknown.add("depth")
        return "?"
    if isinstance(e, ast.Constant):
        return repr(e.value)
    if isinstance(e, ast.Call):
        f = e.func
        if isinstance(f, ast.Attribute) and f.attr in ("column", "value") and len(e.args) >= 2:
            a = [x.value if isinstance(x, ast.Constant) else None for x in e.args]
            kf = (a[0], a[-1])
            if all(isinstance(x, str) for x in kf):
                sig.fields.add("%s.%s" % kf)
                return "F[%s.%s]" % kf
            if isinstance(e.args[-1], ast.Name):
                sig.unknown.add("field_name_var")
                return "?"
        fname = ast.unparse(f)
        inner = ",".join(text(x, fn, m, sig, d + 1, seen) for x in list(e.args) + [k.value for k in e.keywords])
        return "%s(%s)" % (fname, inner)
    if isinstance(e, ast.Attribute):
        return text(e.value, fn, m, sig, d + 1, seen) + "." + e.attr
    if isinstance(e, ast.Name):
        if fn is None:
            sig.unknown.add("no_fn")
            return e.id
        b = bindings(fn)
        if e.id in b and e.id not in seen:
            return "|".join(sorted({text(v, fn, m, sig, d + 1, seen + (e.id,)) for v in b[e.id]}))
        if e.id in params(fn):
            return follow_param(e.id, fn, m, sig, d, seen)
        if e.id in defs[m] or e.id in b:
            return e.id
        return "G[%s]" % e.id
    if isinstance(e, (ast.Tuple, ast.List, ast.BinOp, ast.Subscript, ast.UnaryOp, ast.Compare, ast.IfExp, ast.Dict,
                      ast.GeneratorExp, ast.ListComp, ast.DictComp, ast.SetComp, ast.BoolOp, ast.Starred)):
        s = []
        for c in ast.iter_child_nodes(e):
            if isinstance(c, ast.expr):
                s.append(text(c, fn, m, sig, d + 1, seen))
        return type(e).__name__ + "(" + ",".join(s) + ")"
    if isinstance(e, ast.Lambda):
        sig.unknown.add("lambda")
        return "?"
    sig.unknown.add(type(e).__name__)
    return "?"


def follow_param(name, fn, m, sig, d, seen):
    """같은 모듈 호출자가 정확히 하나의 인자 식을 넘기면 따라간다. 없으면 매개변수 잎."""
    idx = params(fn).index(name)
    outs = set()
    for caller in ast.walk(trees[m][1]):
        if isinstance(caller, ast.FunctionDef):
            for c in ast.walk(caller):
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == fn.name and idx < len(c.args):
                    outs.add(text(c.args[idx], caller, m, sig, d + 2, ()))
    if outs:
        return "|".join(sorted(outs))
    sig.params.add(name)
    return "P[%s]" % name


sites = collections.defaultdict(list)
for m, (p, t) in trees.items():
    nm, al = {}, {}
    for n in ast.walk(t):
        if isinstance(n, ast.ImportFrom):
            src = resolve_from(m, n)
            for a in n.names:
                local = a.asname or a.name
                if src + "." + a.name in trees:
                    al[local] = src + "." + a.name
                else:
                    r = follow(src, a.name)
                    if r:
                        nm[local] = r

    def visit(node, fn):
        for c in ast.iter_child_nodes(node):
            f2 = c if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)) and fn is None else fn
            if isinstance(c, ast.ClassDef):
                f2 = fn
            if isinstance(c, ast.Call):
                tgt = None
                if isinstance(c.func, ast.Name) and c.func.id in nm:
                    tgt = nm[c.func.id]
                elif isinstance(c.func, ast.Attribute) and isinstance(c.func.value, ast.Name) and c.func.value.id in al:
                    tgt = follow(al[c.func.value.id], c.func.attr)
                if tgt and tgt[0] != m and isinstance(defs[tgt[0]].get(tgt[1]), ast.FunctionDef):
                    sig = Sig()
                    s = ",".join(text(x, f2, m, sig) for x in list(c.args) + [k.value for k in c.keywords])
                    sites[tgt].append((m, c.lineno, s, sig))
            visit(c, f2)

    visit(t, None)


def classify(ss):
    res = {"B": [], "not_B": [], "D": []}
    for i in range(len(ss)):
        for j in range(i + 1, len(ss)):
            a, b = ss[i], ss[j]
            if a[0] == b[0]:
                continue
            if a[3].unknown or b[3].unknown:
                res["D"].append((a, b))
            elif a[2] == b[2]:
                res["B" if a[3].fields else "D"].append((a, b))
            elif a[3].fields and b[3].fields and not a[3].params and not b[3].params:
                res["not_B"].append((a, b))
            else:
                res["D"].append((a, b))
    return res


audit_b = set()
with open(AUDIT, encoding="utf-8") as fh:
    for row in csv.reader(fh, delimiter="\t"):
        if len(row) >= 3 and "B" == row[2].strip():
            audit_b.add(row[1].strip())
        elif len(row) >= 3 and row[0].strip() == "B":
            audit_b.add(row[2].strip())

total = collections.Counter()
hit = {}
with open(HERE / ("b_trace_%s.tsv" % LABEL), "w", encoding="utf-8") as out:
    out.write("callee\tn_sites\tB_pairs\tnotB_pairs\tD_pairs\n")
    for (cm, fn), ss in sorted(sites.items()):
        if len({s[0] for s in ss}) < 2:
            continue
        r = classify(ss)
        cls = "B" if r["B"] else ("D" if r["D"] else "not_B")
        total[cls] += 1
        hit[fn] = cls
        out.write("%s.%s\t%d\t%d\t%d\t%d\t%s\n" % (cm, fn, len(ss), len(r["B"]), len(r["not_B"]), len(r["D"]), cls))
        out.flush()
print("shared callee classes", dict(total), "audit_B names", len(audit_b))
print("audit B ->", collections.Counter(hit.get(x, "absent") for x in audit_b))
print("audit B detail", sorted((x, hit.get(x, "absent")) for x in audit_b))
print("tool B not in audit_B", sorted(k for k, v in hit.items() if v == "B" and k not in audit_b)[:40])
