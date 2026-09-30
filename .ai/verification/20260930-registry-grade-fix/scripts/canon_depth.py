"""계약 5(2차 오케스트레이터 기준): §2 각 행 정본 칸 함수가 직접 또는 한 단계 하위 함수에서 넷·소자·회로 이름 리터럴이나 이름 집합 상수를 읽는지.
사용: canon_depth.py <엔진 루트> <레지스트리 경로> <out.json>
- 하위 = 본문에서 이름으로 부르는 같은 모듈 최상위 함수, 그리고 self.<메서드>(같은 클래스). 두 단계 하위는 관찰로 따로 적는다.
- 오탐 제외(오케스트레이터 기준): 연산자·metric 이름 레지스트리(_CONSTRAINT_OPS·_METRICS_REGISTRY·_METRIC_UNITS 등 값이 함수·단위인 dict), spec 스칼라 키
  (spec[...]/spec.get(...)의 첨자 문자열), 소자 종류('nmos'·'pmos'·'nfet'·'pfet').
- 이름 집합 상수 = 모듈 최상위 대입 중 값이 문자열만 가진 set/frozenset/tuple/list(dict는 키가 넷 이름 모양일 때만).
- 넷 이름 모양 문자열 = vdd/vss/gnd 계열, vcm/out/in/bias 계열, M<숫자> 소자 이름."""
import ast, json, os, re, sys
root, regp, out = sys.argv[1:4]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
reg = open(regp, encoding="utf-8").read().split("\n")
s = next(i for i, l in enumerate(reg) if l.startswith("## 2."))
e = next(j for j in range(s + 1, len(reg)) if reg[j].startswith("## "))
rows = [l for l in reg[s:e] if l.startswith("|") and not re.match(r"^\|\s*-", l)][1:]
NETPAT = re.compile(r"^(vdd|vss|gnd|avdd|avss|dvdd|vdda|vssa|vcm|vcmfb|vout|voutp|voutn|out|outp|outn|inp|inn|in|vin|vinp|vinn|vip|vim|vbias\w*|vb\d*|bias\w*|tail|iref|M\d+\w*)$", re.I)
KIND = {"nmos", "pmos", "nfet", "pfet"}
mods, defs, consts = {}, {}, {}
for f in sorted(os.listdir(A)):
    if not f.endswith(".py"):
        continue
    t = ast.parse(open(os.path.join(A, f), encoding="utf-8").read())
    mod = f[:-3]; mods[mod] = t
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
            if isinstance(v, ast.Dict):
                ks = v.keys
                if ks and all(isinstance(x, ast.Constant) and isinstance(x.value, str) and NETPAT.match(x.value) for x in ks):
                    consts[(mod, n.targets[0].id)] = (n.lineno, [x.value for x in ks])
            elif isinstance(v, (ast.Set, ast.Tuple, ast.List)) and v.elts and all(isinstance(x, ast.Constant) and isinstance(x.value, str) for x in v.elts):
                vals = [x.value for x in v.elts]
                if not set(v.lower() for v in vals) <= KIND:
                    consts[(mod, n.targets[0].id)] = (n.lineno, vals)

def resolve(nm):
    nm = nm.split("(")[0].strip()
    if "." in nm and nm.split(".")[0] in mods:
        m, rest = nm.split(".", 1)
        return [(m, rest)] if (m, rest) in defs else []
    hits = [k for k in defs if k[1] == nm]
    return hits or [k for k in defs if k[1].endswith("." + nm)]

def spec_key_consts(node):
    """spec[...] / spec.get(...) 첨자·인자로 쓰인 문자열 상수 노드 id 집합(오탐 제외)."""
    ids = set()
    for x in ast.walk(node):
        if isinstance(x, ast.Subscript) and isinstance(x.value, ast.Name) and x.value.id == "spec" and isinstance(x.slice, ast.Constant):
            ids.add(id(x.slice))
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == "get" and isinstance(x.func.value, ast.Name) and x.func.value.id == "spec" and x.args and isinstance(x.args[0], ast.Constant):
            ids.add(id(x.args[0]))
    return ids

def reads(mod, node):
    skip = spec_key_consts(node)
    found = []
    for x in ast.walk(node):
        if isinstance(x, ast.Name) and (mod, x.id) in consts:
            found.append((x.lineno, "const", x.id))
        if isinstance(x, ast.Constant) and isinstance(x.value, str) and id(x) not in skip and NETPAT.match(x.value) and x.value.lower() not in KIND:
            found.append((x.lineno, "literal", x.value))
    return sorted(set(found))

def callees(mod, qn, node):
    cls = qn.split(".")[0] if "." in qn else None
    r = set()
    for x in ast.walk(node):
        if isinstance(x, ast.Call):
            if isinstance(x.func, ast.Name) and (mod, x.func.id) in defs:
                r.add(x.func.id)
            if cls and isinstance(x.func, ast.Attribute) and isinstance(x.func.value, ast.Name) and x.func.value.id == "self" and (mod, f"{cls}.{x.func.attr}") in defs:
                r.add(f"{cls}.{x.func.attr}")
    r.discard(qn)
    return r

res = []
for r in rows:
    c = [x.strip() for x in r.strip().strip("|").split("|")]
    concept, cell = c[0], c[1]
    entry = {"concept": concept, "cell": cell, "funcs": []}
    for nm in re.findall(r"`([^`]+)`", cell):
        hits = resolve(nm)
        for (mod, qn) in hits:
            node = defs[(mod, qn)]
            d0 = reads(mod, node)
            d1, d2 = {}, {}
            for c1 in sorted(callees(mod, qn, node)):
                n1 = defs[(mod, c1)]
                r1 = reads(mod, n1)
                if r1:
                    d1[c1] = r1
                for c2 in sorted(callees(mod, c1, n1)):
                    if c2 == qn:
                        continue
                    r2 = reads(mod, defs[(mod, c2)])
                    if r2:
                        d2[f"{c1}->{c2}"] = r2
            entry["funcs"].append({"name": nm, "def": f"{mod}.py:{node.lineno} {qn}", "direct": d0, "depth1": d1, "depth2_obs": d2})
    entry["reads_names_depth_le_1"] = any(f["direct"] or f["depth1"] for f in entry["funcs"])
    entry["cell_marked_candidate"] = cell.startswith("정본 후보(") or cell.startswith("(정본 없음")
    res.append(entry)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for x in res:
    fs = [(f["name"], [t[2] for t in f["direct"]], {k: [t[2] for t in v] for k, v in f["depth1"].items()}, list(f["depth2_obs"])) for f in x["funcs"]]
    print(x["concept"][:16], "| reads<=1:", x["reads_names_depth_le_1"], "| marked:", x["cell_marked_candidate"], "|", fs)
