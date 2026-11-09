"""§2 모든 행의 정본(제안) 칸 함수가 넷·소자·회로 이름 리터럴이나 이름 집합 상수를 읽는지 AST로 조사(1차 canon_names.py 확장).
사용: canon_names2.py <root> <out.json>
- 정본 칸(둘째 칸)의 백틱 이름을 엔진(A/*.py 최상위 def·class, Class.method; 'mod.name' 접두는 그 모듈에서, 메서드 이름만 적힌 것은 모든 클래스에서)에서 찾는다
- 직접(본문+기본 인자): (a) 이름 집합 상수 참조 -- 모든 엔진 파일의 모듈 최상위 대입 중 값이 문자열만 가진 set/frozenset/tuple/list/dict 키인 것,
  (b) 넷 이름 모양 문자열 상수(vdd/vss/gnd 계열, vcm/out/in/bias 계열, M<숫자> 소자 이름), (c) 문자열 상수와의 비교에 쓰인 문자열(참고)
- 전이: 본문에서 이름으로 부르는 같은 모듈 최상위 함수를 따라가(깊이 제한 없음, 방문 1회) (a)(b)가 있는 함수를 모은다(참고)
판정은 사람이 한다."""
import ast, json, os, re, sys
root, out = sys.argv[1], sys.argv[2]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
reg = open(os.path.join(root, "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"), encoding="utf-8").read().split("\n")
s = next(i for i, l in enumerate(reg) if l.startswith("## 2."))
e = next(j for j in range(s + 1, len(reg)) if reg[j].startswith("## "))
rows = [l for l in reg[s:e] if l.startswith("|") and not re.match(r"^\|\s*-", l)][1:]
NETPAT = re.compile(r"^(vdd|vss|gnd|avdd|avss|dvdd|vdda|vssa|vcm|vcmfb|vout|voutp|voutn|out|outp|outn|inp|inn|in|vin|vinp|vinn|vip|vim|vbias\w*|vb\d*|bias\w*|tail|iref|M\d+\w*)$", re.I)
mods, defs, consts = {}, {}, {}
for f in sorted(os.listdir(A)):
    if not f.endswith(".py"):
        continue
    t = ast.parse(open(os.path.join(A, f), encoding="utf-8").read())
    mod = f[:-3]
    mods[mod] = t
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            defs[(mod, n.name)] = n
            if isinstance(n, ast.ClassDef):
                for m in n.body:
                    if isinstance(m, ast.FunctionDef):
                        defs[(mod, f"{n.name}.{m.name}")] = m
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            v = n.value
            if isinstance(v, ast.Call) and getattr(v.func, "id", "") in ("frozenset", "set", "tuple") and v.args:
                v = v.args[0]
            elts = getattr(v, "elts", None) or (v.keys if isinstance(v, ast.Dict) else None)
            if elts and all(isinstance(x, ast.Constant) and isinstance(x.value, str) for x in elts):
                consts[(mod, n.targets[0].id)] = (n.lineno, [x.value for x in elts])

def resolve(nm):
    nm = nm.split("(")[0].strip()
    if "." in nm and nm.split(".")[0] in mods:
        m, rest = nm.split(".", 1)
        return [(m, rest)] if (m, rest) in defs else []
    hits = [k for k in defs if k[1] == nm]
    if not hits:
        hits = [k for k in defs if k[1].endswith("." + nm)]
    return hits

def direct(mod, node):
    cref, net, cmp_ = set(), set(), set()
    for x in ast.walk(node):
        if isinstance(x, ast.Name) and (mod, x.id) in consts:
            cref.add(x.id)
        if isinstance(x, ast.Constant) and isinstance(x.value, str) and NETPAT.match(x.value):
            net.add(x.value)
        if isinstance(x, ast.Compare):
            for c in [x.left] + x.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    cmp_.add(c.value)
    return cref, net, cmp_

def callees(mod, node):
    r = set()
    for x in ast.walk(node):
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and (mod, x.func.id) in defs:
            r.add(x.func.id)
    return r

res = []
for r in rows:
    c = [x.strip() for x in r.strip().strip("|").split("|")]
    concept, cell = c[0], c[1]
    for nm in re.findall(r"`([^`]+)`", cell):
        hits = resolve(nm)
        if not hits:
            res.append({"concept": concept, "cell": cell, "name": nm, "found": False})
            continue
        for (mod, qn) in hits:
            node = defs[(mod, qn)]
            cref, net, cmp_ = direct(mod, node)
            seen, stack, trans = {qn}, list(callees(mod, node)), {}
            while stack:
                f = stack.pop()
                if f in seen:
                    continue
                seen.add(f)
                fn = defs[(mod, f)]
                a, b, _ = direct(mod, fn)
                if a or b:
                    trans[f] = {"consts": sorted(a), "netlike": sorted(b), "line": fn.lineno}
                stack += list(callees(mod, fn))
            res.append({"concept": concept, "cell": cell, "name": nm, "found": True, "def": f"{mod}.py:{node.lineno} {qn}",
                        "direct_name_set_consts": {k: consts[(mod, k)] for k in sorted(cref)},
                        "direct_netlike_strings": sorted(net), "compared_strings": sorted(cmp_),
                        "transitive_callees_reading_names": trans, "n_transitive_callees": len(seen) - 1})
json.dump({"n_rows": len(rows), "scan": res}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for x in res:
    if not x["found"]:
        print("NOTFOUND", x["concept"], "|", x["name"])
    else:
        print(x["concept"][:14], "|", x["name"], "|", x["def"], "| direct", list(x["direct_name_set_consts"]), x["direct_netlike_strings"],
              "| trans", {k: v["consts"] + v["netlike"] for k, v in x["transitive_callees_reading_names"].items()})
