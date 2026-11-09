"""Phase 3 design v6 -- D0a `order`/`shim` 규칙 개정(3차 검토 B1·B2)의 모의.

읽기 전용 측정 스크립트(초안 측정 -- D0a 구현·test 기대값의 근거가 아니다, 작성자 != 검증자).
입력: 격리 복제본 REPO(gate master 7535799), 출력 JSON OUT, 모의 트리 작업 디렉터리 WORK.

1. 이관표 근사: design §6.2 규칙 A-1~A-5를 실제 계획서 N3.10 표·레지스트리 '이관 목적지' 열·엔진 소스에
   단순화해 적용한다(D0b가 낼 이관표가 아니다 -- B26-1·B34 병합 전이고 규칙 구현도 근사).
2. 모의용 계층 보정: 근사 배정에 남는 위쪽 참조는 sigma(u) = max(sigma(u), max sigma(R(u)))로 올려 없앤다
   (PLAN-LAYER가 0인 배정이라는 M card 착수 조건을 흉내 낸 것. split 파일(SD 제외) 단위가 7이 되면 8).
3. M1~M9를 번호순으로 적용한 트리를 실제 파일로 만든다(본문 바이트 그대로, import 줄만 생성).
4. 각 card 병합본에서 D0a `order`(옛 문언 / 새 문언)와 `shim`(옛 문언 / 새 문언 (a)(b))을 판정하고,
   모듈마다 새 파이썬 프로세스에서 import해 중간 상태 순환 import(F3)를 본다.
결과는 케이스마다 OUT + '.partial.jsonl'에 누적하고 끝에 OUT에 쓴다.
"""
import ast
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import symtable
import builtins

REPO, OUT, WORK = sys.argv[1], sys.argv[2], sys.argv[3]
VARIANT = sys.argv[4] if len(sys.argv) > 4 else "top"
BOTTOM = VARIANT == "bottom"  # 변형: MOD k>7 파일의 SD import만 파일 끝에
BOTTOMALL = VARIANT == "bottomall"  # 변형: MOD k>7 파일의 트리 import 전부를 파일 끝에
BOTTOM7 = VARIANT == "bottom7"  # 변형: MOD k>7 파일에서 번호 7 이상 모듈(SD·MOD8) import만 파일 끝에
PY = sys.executable
A = os.path.join(REPO, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, os.path.join(REPO, "tools", "gates"))
import role_paths as rp  # noqa: E402
import import_layering as il  # noqa: E402

SPLIT = ["sizing_recipe.py", "stick_diagram.py", "topology_library.py", "design_report.py",
         "audit_current_forced.py"]
KEEP = ["audit_current_forced.py"]
ALIASES = {"optimizer": "theta_search"}
PARTIAL = OUT + ".partial.jsonl"
if os.path.exists(PARTIAL):
    os.remove(PARTIAL)


def log(kind, obj):
    with open(PARTIAL, "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": kind, "data": obj}, ensure_ascii=False) + "\n")


plan_text = open(os.path.join(REPO, "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"),
                 encoding="utf-8").read()
MODTAB = il.mod_table(plan_text)                     # stem -> num
NUM2STEM = {v: k for k, v in MODTAB.items()}
hdr, rows = rp.read_section_table(plan_text, "### N3.10 ")
ci_rep = hdr.index("대표 대상")
ci_id = hdr.index("ID")


def stem(f):
    return os.path.splitext(os.path.basename(f))[0]


# ---------------------------------------------------------------- 단위
SRC = {f: open(os.path.join(A, f), encoding="utf-8").read() for f in SPLIT}
TREE_STEMS = {stem(p) for p in os.listdir(A) if p.endswith(".py")} | set(MODTAB)
BUILTINS = set(dir(builtins))


def is_main_block(n):
    return (isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
            and isinstance(n.test.left, ast.Name) and n.test.left.id == "__name__")


def stores(node):
    out = set()

    def walk(n, top):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not top:
                out.add(n.name)
            return
        if isinstance(n, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.add(n.id)
        for c in ast.iter_child_nodes(n):
            walk(c, False)
    walk(node, True)
    return out


def sym_globals(tab):
    out = set()
    for s in tab.get_symbols():
        if s.is_global() and (s.is_referenced() or s.is_assigned()):
            out.add(s.get_name())
    for c in tab.get_children():
        out |= sym_globals(c)
    return out


def ann_names(node):
    out = set()
    anns = []
    for n in ast.walk(node):
        if isinstance(n, ast.arg) and n.annotation is not None:
            anns.append(n.annotation)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns is not None:
            anns.append(n.returns)
        if isinstance(n, ast.AnnAssign):
            anns.append(n.annotation)
    for a in anns:
        for m in ast.walk(a):
            if isinstance(m, ast.Name):
                out.add(m.id)
            elif isinstance(m, ast.Constant) and isinstance(m.value, str):
                try:
                    for q in ast.walk(ast.parse(m.value, mode="eval")):
                        if isinstance(q, ast.Name):
                            out.add(q.id)
                except SyntaxError:
                    out.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", m.value))
    return out


def names_in(nodes):
    out = set()
    for x in nodes:
        if x is None:
            continue
        for m in ast.walk(x):
            if isinstance(m, ast.Name):
                out.add(m.id)
    return out


UNITS = []          # dict(file, kind, key, binds, lines(a,b), node)
IMPORTS = {}        # file -> list of (node, module, [(name, asname)]) top-level
FUTURE = {}
for f in SPLIT:
    src = SRC[f]
    tree = ast.parse(src)
    top = symtable.symtable(src, f, "exec")
    child = {}
    for c in top.get_children():
        child.setdefault((c.get_name(), c.get_lineno()), c)
    IMPORTS[f] = []
    FUTURE[f] = set()
    body = tree.body
    for i, n in enumerate(body):
        if i == 0 and isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            continue
        if isinstance(n, ast.ImportFrom):
            if n.module == "__future__":
                FUTURE[f] |= {a.name for a in n.names}
            IMPORTS[f].append(("from", n.module, [(a.name, a.asname or a.name) for a in n.names], n))
            continue
        if isinstance(n, ast.Import):
            IMPORTS[f].append(("import", None, [(a.name, a.asname or a.name.split(".")[0]) for a in n.names], n))
            continue
        if is_main_block(n):
            continue
        a = (n.decorator_list[0].lineno if getattr(n, "decorator_list", None) else n.lineno)
        b = n.end_lineno
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(n, ast.ClassDef) else "def"
            tab = child.get((n.name, n.lineno))
            g = sym_globals(tab) if tab is not None else set()
            g |= ann_names(n)
            extra = list(n.decorator_list)
            if kind == "def":
                extra += list(n.args.defaults) + [d for d in n.args.kw_defaults if d is not None]
            else:
                extra += list(n.bases) + [k.value for k in n.keywords]
            g |= names_in(extra)
            UNITS.append(dict(file=f, kind=kind, key=n.name, binds={n.name}, lines=(a, b), node=n, refs=g))
        else:
            binds = stores(n)
            loads = set()
            local = set()
            for m in ast.walk(n):
                if isinstance(m, ast.Name) and isinstance(m.ctx, ast.Load):
                    loads.add(m.id)
                if isinstance(m, ast.comprehension):
                    local |= {q.id for q in ast.walk(m.target) if isinstance(q, ast.Name)}
                if isinstance(m, ast.Lambda):
                    local |= {x.arg for x in m.args.args + m.args.kwonlyargs}
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    local |= {x.id for x in ast.walk(m) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)}
            key = ",".join(sorted(binds)) if binds else "<stmt:%d>" % n.lineno
            UNITS.append(dict(file=f, kind="stmt", key=key, binds=binds, lines=(a, b), node=n,
                              refs=(loads - local) | ann_names(n)))

UID = {(u["file"], u["key"]): i for i, u in enumerate(UNITS)}
BIND = {}
for i, u in enumerate(UNITS):
    for nm in u["binds"]:
        BIND.setdefault((u["file"], nm), []).append(i)


def resolve(f, name, depth=0):
    """(f에서 name이 가리키는 단위 id) 또는 None(외부·내장)."""
    if depth > 20:
        return None
    if (f, name) in BIND:
        return BIND[(f, name)][-1]
    for kind, mod, names, _n in IMPORTS.get(f, []):
        if kind == "from" and mod and (mod + ".py") in SPLIT:
            for nm, asn in names:
                if asn == name:
                    return resolve(mod + ".py", nm, depth + 1)
    return None


R = {}
for i, u in enumerate(UNITS):
    tgt = set()
    for nm in u["refs"]:
        j = resolve(u["file"], nm)
        if j is not None and j != i:
            tgt.add(j)
    R[i] = tgt
REFBY = {i: set() for i in R}
for i, ts in R.items():
    for j in ts:
        REFBY[j].add(i)

# ---------------------------------------------------------------- 규칙(근사)
TOK = re.compile(r"`([^`]+)`")
a1 = {}
for r in rows:
    num = int(r[ci_id].strip()[3:])
    for t in TOK.findall(r[ci_rep]):
        t = t.strip()
        if re.fullmatch(r"[A-Za-z_*][A-Za-z0-9_*]*", t):
            pats = [("name", t)]
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.py", t):
            pats = [("file", t)]
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", t):
            pats = [("name", t.split(".")[1])]
        else:
            pats = []
        for kind, p in pats:
            for i, u in enumerate(UNITS):
                hit = (u["file"] == p) if kind == "file" else any(fnmatch.fnmatchcase(b, p) for b in u["binds"])
                if hit:
                    a1.setdefault(i, set()).add(num)

reg_text = open(os.path.join(REPO, "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"),
                encoding="utf-8").read().splitlines()
reg = {}
sec_file = None
prev_cell = None
col = None
for line in reg_text:
    m = re.match(r"^###\s+(\S+\.py)", line)
    if line.startswith("#"):
        sec_file = m.group(1) if m else ("*" if "기타" in line else None)
        col = None
        prev_cell = None
        continue
    if line.startswith("|"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if "이관 목적지" in cells:
            col = cells.index("이관 목적지")
            continue
        if col is None or set(cells[0]) <= set("-: "):
            continue
        nm = TOK.findall(cells[0])
        if not nm:
            continue
        cell = cells[col]
        if cell.strip() == "〃":
            cell = prev_cell or ""
        prev_cell = cell
        mods = set()
        for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", cell):
            if t in MODTAB:
                mods.add(MODTAB[t])
            elif t in ALIASES:
                mods.add(MODTAB[ALIASES[t]])
        for n0 in nm:
            for n1 in n0.split("/"):
                key = n1.split(".")[0].strip().rstrip("()")
                reg.setdefault(key, []).append((sec_file, mods))


def reg_mods(u):
    best = None
    for sf, mods in reg.get(u["key"], []):
        if sf in (u["file"], "*", None):
            if sf == u["file"]:
                return mods
            best = mods if best is None else best
    return best or set()


EXC = {n for n in BUILTINS if isinstance(getattr(builtins, n), type) and issubclass(getattr(builtins, n), BaseException)}


def is_record(i, recs):
    u = UNITS[i]
    if u["kind"] != "class":
        return False
    n = u["node"]
    for d in n.decorator_list:
        dd = d.func if isinstance(d, ast.Call) else d
        nm = dd.id if isinstance(dd, ast.Name) else (dd.attr if isinstance(dd, ast.Attribute) else "")
        if nm == "dataclass":
            return True
    for b in n.bases:
        if isinstance(b, ast.Name) and (b.id in EXC or resolve(u["file"], b.id) in recs):
            return True
    return not any(isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) for x in n.body)


recs = set()
changed = True
while changed:
    changed = False
    for i in range(len(UNITS)):
        if i not in recs and is_record(i, recs):
            recs.add(i)
            changed = True

sigma, rule = {}, {}
for i, u in enumerate(UNITS):
    if i in a1:
        if len(a1[i]) == 1:
            sigma[i], rule[i] = min(a1[i]), "A-1"
        else:
            sigma[i], rule[i] = min(a1[i]), "A-1(conflict)"
for _ in range(50):
    before = dict(sigma)
    for i, u in enumerate(UNITS):
        if rule.get(i, "").startswith("A-1"):
            continue
        if i in recs:
            ref = [sigma[j] for j in REFBY[i] if j in sigma and j not in recs or (j in sigma and j != i)]
            if ref:
                sigma[i], rule[i] = min(ref), "A-2"
                continue
        mods = reg_mods(u)
        if len(mods) >= 2:
            up = [sigma[j] for j in R[i] if j in sigma]
            sigma[i], rule[i] = max([min(mods)] + up), "A-3"
            continue
        if len(mods) == 1:
            sigma[i], rule[i] = min(mods), "A-4"
            continue
        ref = [sigma[j] for j in REFBY[i] if j in sigma]
        if ref:
            sigma[i], rule[i] = min(ref), "A-5"
    if sigma == before:
        break

unassigned = [UNITS[i]["file"] + "::" + UNITS[i]["key"] for i in range(len(UNITS)) if i not in sigma]
upward = [(i, j) for i in sigma for j in R[i] if j in sigma and sigma[i] < sigma[j]]
rule_counts = {}
for i in sigma:
    rule_counts[rule[i]] = rule_counts.get(rule[i], 0) + 1


def U(i):
    return UNITS[i]["file"] + "::" + UNITS[i]["key"]


INTEREST = ["load_topology", "validate_theta_declaration_order", "_build_shared_current_joint_plan",
            "_shared_current_groups_from_compensation", "optimize_full_circuit_budget", "_audit_result_json",
            "save_instance_json", "run_full_circuit_audit_from_topology", "Transistor", "audit_topology",
            "render_report", "run_topology_pipeline_with_finger_fixup", "resolve_stack_layout"]
interest = {}
for i, u in enumerate(UNITS):
    if u["key"] in INTEREST:
        interest[U(i)] = {"sigma": sigma.get(i), "rule": rule.get(i),
                          "refs_mod": sorted({(sigma.get(j), U(j)) for j in R[i] if sigma.get(j) and sigma.get(j) > 1},
                                             key=lambda x: -x[0])[:6]}
vtdo = [i for i, u in enumerate(UNITS) if u["key"] == "validate_theta_declaration_order"]
vtdo_refs = {U(j): sigma.get(j) for i in vtdo for j in R[i]}
log("plan", {"units": len(UNITS), "rule_counts": rule_counts, "unassigned_n": len(unassigned),
             "upward_n": len(upward), "interest": interest, "vtdo_refs": vtdo_refs})

# ---------------------------------------------------------------- 모의 보정(계층 0)
sig2 = {}
for i in range(len(UNITS)):
    sig2[i] = sigma.get(i, 1)
raised = 0
REPAIR = sys.argv[5] if len(sys.argv) > 5 else "raise"
if REPAIR == "pull":
    # 위쪽 참조 u -> v: v가 계획 명시(A-1)가 아니면 v를 u 번호로 끌어내린다(소비자 따라 -- A-5 쪽 해석).
    # 단 SD 밖 단위를 7로 끌어내리지 않는다(옮길 card가 없다) -- 그때는 u를 올린다.
    for _ in range(500):
        ch = False
        for i in range(len(UNITS)):
            for j in R[i]:
                if sig2[i] < sig2[j]:
                    if rule.get(j) != "A-1" and not (sig2[i] == 7 and UNITS[j]["file"] != "stick_diagram.py"):
                        sig2[j] = sig2[i]
                    else:
                        sig2[i] = 8 if (sig2[j] == 7 and UNITS[i]["file"] != "stick_diagram.py") else sig2[j]
                    ch = True
        if not ch:
            break
for _ in range(200):
    ch = False
    for i in range(len(UNITS)):
        m = max([sig2[i]] + [sig2[j] for j in R[i]])
        if m == 7 and UNITS[i]["file"] != "stick_diagram.py":
            m = 8
        if UNITS[i]["file"] in KEEP and i not in sigma:
            continue
        if m != sig2[i]:
            sig2[i] = m
            ch = True
    if not ch:
        break
for i in range(len(UNITS)):
    if sig2[i] != sigma.get(i):
        raised += 1
# keep 파일에서 규칙이 MOD를 주지 않은 단위는 그 파일에 남는다(도구)
STAY = {i for i in range(len(UNITS)) if UNITS[i]["file"] in KEEP and i not in sigma}
STAY |= {i for i in range(len(UNITS)) if UNITS[i]["file"] == "stick_diagram.py" and sig2[i] == 7}
up2 = [(U(i), U(j)) for i in sig2 for j in R[i] if i not in STAY and j not in STAY and sig2[i] < sig2[j]]
sd_out_hi = sorted(U(i) for i in range(len(UNITS)) if UNITS[i]["file"] == "stick_diagram.py" and sig2[i] > 7)
nonsd_7 = sorted(U(i) for i in range(len(UNITS)) if UNITS[i]["file"] != "stick_diagram.py" and sigma.get(i) == 7)
by_mod = {}
for i in range(len(UNITS)):
    if i in STAY:
        continue
    by_mod.setdefault(sig2[i], []).append(i)
log("sim_assign", {"changed_from_rules": raised, "upward_after": len(up2), "upward_sample": up2[:5],
                   "per_mod": {k: len(v) for k, v in sorted(by_mod.items())},
                   "sd_units_to_mod8_9": sd_out_hi, "nonsd_rules_to_mod7": nonsd_7})

# ---------------------------------------------------------------- 트리 생성
LINES = {f: SRC[f].splitlines(keepends=True) for f in SPLIT}
CARDS = [k for k in sorted(by_mod) if k != 7]
GEN_ORDER = ["topology_library.py", "stick_diagram.py", "sizing_recipe.py", "design_report.py",
             "audit_current_forced.py"]


def ext_import_lines(f):
    out = []
    for kind, mod, names, n in IMPORTS[f]:
        if kind == "from" and mod and (mod in TREE_STEMS):
            continue
        if kind == "from" and mod == "__future__":
            continue
        out.append("".join(LINES[f][n.lineno - 1:n.end_lineno]))
    return out


def gen_state(k_done, outdir):
    """M card k_done까지 적용한 트리(A/*.py 중 split 파일 + MOD 파일 + 나머지 원본 파일 사본)."""
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir)
    for p in os.listdir(A):
        if p.endswith(".py") and p not in SPLIT:
            shutil.copy2(os.path.join(A, p), outdir)
    moved = {i for i in range(len(UNITS)) if i not in STAY and sig2[i] in k_done}

    def loc(i):
        return (NUM2STEM[sig2[i]] + ".py") if i in moved else UNITS[i]["file"]
    files = {}
    # MOD 파일
    for k in k_done:
        # 원본 파일 사이 순서 = 원래 import 초기화 순서(TL·SD가 SR보다 먼저 실행됐다), 같은 원본 안은 원래 순서
        us = sorted(by_mod[k], key=lambda i: (GEN_ORDER.index(UNITS[i]["file"]), UNITS[i]["lines"][0]))
        fut = set()
        ext = []
        need = {}
        for i in us:
            f = UNITS[i]["file"]
            fut |= FUTURE[f]
            for line in ext_import_lines(f):
                if line not in ext:
                    ext.append(line)
            for j in R[i]:
                if sig2.get(j) == k and j in moved:
                    continue
                for nm in UNITS[j]["binds"]:
                    pass
            # 단위가 실제로 읽는 이름만 import(출처 파일은 지금 위치)
            for nm in UNITS[i]["refs"]:
                j = resolve(f, nm)
                if j is None or (j in moved and sig2[j] == k):
                    continue
                need.setdefault(stem(loc(j)), set()).add(nm)
        body = ['"""MOD%d %s (모의)."""\n' % (k, NUM2STEM[k])]
        if fut:
            body.append("from __future__ import %s\n" % ", ".join(sorted(fut)))
        body += ext
        tail = []
        for s in sorted(need):
            line = "from %s import %s\n" % (s, ", ".join(sorted(need[s])))
            # 변형 BOTTOM: SD(MOD7)가 이 MOD(k > 7)를 임시 재수출하면 SD <-> MOD k 순환 -- 이 파일의 SD import를 끝에
            (tail if (k > 7 and (BOTTOMALL or (BOTTOM and s == "stick_diagram")
                                  or (BOTTOM7 and MODTAB.get(s, 0) >= 7))) else body).append(line)
        for i in us:
            a, b = UNITS[i]["lines"]
            body.append("\n\n" + "".join(LINES[UNITS[i]["file"]][a - 1:b]))
        if tail:
            body.append("\n\n" + "".join(tail))
        files[NUM2STEM[k] + ".py"] = "".join(body)
    # split 파일
    complete = {}
    for f in SPLIT:
        mine = [i for i in range(len(UNITS)) if UNITS[i]["file"] == f]
        gone = [i for i in mine if i in moved]
        left = [i for i in mine if i not in moved]
        drop = set()
        for i in gone:
            a, b = UNITS[i]["lines"]
            drop |= set(range(a, b + 1))
        lines = [l for n, l in enumerate(LINES[f], 1) if n not in drop]
        rex = {}
        for i in gone:
            rex.setdefault(NUM2STEM[sig2[i]], set()).update(UNITS[i]["binds"])
        # split 파일 재수출은 import 머리 뒤(남은 모듈 수준 문장이 읽기 전에 묶인다). SD(MOD7)의 MOD 8·9 재수출만 파일 끝
        is_sd = stem(f) in MODTAB
        lo = "".join("from %s import %s\n" % (s, ", ".join(sorted(v))) for s, v in sorted(rex.items())
                     if not (is_sd and MODTAB[s] > 7))
        hi = "".join("from %s import %s\n" % (s, ", ".join(sorted(v))) for s, v in sorted(rex.items())
                     if is_sd and MODTAB[s] > 7)
        nonmod = f not in KEEP and stem(f) not in MODTAB
        if not left and nonmod:
            # 완전 shim: docstring + (선택) __future__ + 재수출만
            t = ast.parse(SRC[f])
            doc = ""
            if t.body and isinstance(t.body[0], ast.Expr) and isinstance(getattr(t.body[0], "value", None), ast.Constant):
                doc = "".join(LINES[f][:t.body[0].end_lineno])
            fut = ("from __future__ import %s\n" % ", ".join(sorted(FUTURE[f]))) if FUTURE[f] else ""
            files[f] = doc + fut + lo + hi
            complete[f] = True
            continue
        # 재수출 위치: import 머리 바로 뒤(작은 번호), 파일 끝(큰 번호 -- 순환 완화)
        last_imp = 0
        for kind, mod, names, n in IMPORTS[f]:
            if n.lineno < 200:
                last_imp = max(last_imp, n.end_lineno)
        kept_before = sum(1 for n in range(1, last_imp + 1) if n not in drop)
        lines = lines[:kept_before] + ([lo] if lo else []) + lines[kept_before:] + (["\n" + hi] if hi else [])
        files[f] = "".join(lines)
        complete[f] = False
    for name, text in files.items():
        with open(os.path.join(outdir, name), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    return files, complete


def top_imports(text):
    out = []
    for n in ast.walk(ast.parse(text)):
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            out.append(n.module.split(".")[0])
        elif isinstance(n, ast.Import):
            out += [a.name.split(".")[0] for a in n.names]
    return out


def order_findings(card_k, text, rule):
    found = []
    for m in top_imports(text):
        if m not in TREE_STEMS:
            continue
        f = m + ".py"
        if rule == "old":
            if f in SPLIT or (m in MODTAB and MODTAB[m] >= card_k):
                found.append(f)
        else:
            if m in MODTAB:
                if MODTAB[m] >= card_k:
                    found.append(f)
            elif f in SPLIT:
                found.append(f)
    return sorted(set(found))


def top_dumps(text):
    t = ast.parse(text)
    return [(ast.dump(n), n) for n in t.body]


def shim_findings(f, base_text, head_text, complete):
    old, new_a, new_b = [], [], []
    if head_text is None:
        return old, new_a, new_b
    body = ast.parse(head_text).body
    nonmod = f not in KEEP and stem(f) not in MODTAB
    for i, n in enumerate(body):
        if i == 0 and isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant):
            continue
        ok = isinstance(n, ast.ImportFrom) and n.module in MODTAB
        if nonmod and not ok:
            old.append(ast.dump(n)[:60])
    base = {}
    for d, n in top_dumps(base_text):
        base[d] = base.get(d, 0) + 1
    for d, n in top_dumps(head_text):
        if base.get(d, 0) > 0:
            base[d] -= 1
            continue
        if not (isinstance(n, ast.ImportFrom) and n.module in MODTAB):
            new_a.append(d[:60])
    if nonmod and complete:
        for i, n in enumerate(body):
            if i == 0 and isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant):
                continue
            if isinstance(n, ast.ImportFrom) and (n.module in MODTAB or n.module == "__future__"):
                continue
            new_b.append(ast.dump(n)[:60])
    return old, new_a, new_b


import site  # noqa: E402
_ENV = dict(os.environ)
_ENV["PYTHONPATH"] = os.pathsep.join([site.getusersitepackages()] + [p for p in sys.path if p.endswith("site-packages")])


def import_check(d, mods):
    """모듈마다 새 프로세스에서 **그 모듈을 처음으로** import(중간 상태 순환 import 확인, design §4 F3)."""
    res = {}
    for m in mods:
        p = subprocess.run([PY, "-B", "-c", "import %s" % m], cwd=d, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600, env=_ENV)
        res[m] = "ok" if p.returncode == 0 else (p.stderr.strip().splitlines() or ["?"])[-1][:200]
    return res


results = []
prev_files = {f: SRC[f] for f in SPLIT}
done = []
for k in CARDS:
    done.append(k)
    d = os.path.join(WORK, "state_M%d" % k)
    files, complete = gen_state(list(done), d)
    head_mod = files[NUM2STEM[k] + ".py"]
    tree_imps = sorted({m for m in top_imports(head_mod) if m in TREE_STEMS})
    rec = {"card": "M%d" % k, "mod_file": NUM2STEM[k] + ".py", "moved_units": len(by_mod[k]),
           "tree_imports": tree_imps,
           "order_old": order_findings(k, head_mod, "old"), "order_new": order_findings(k, head_mod, "new"),
           "shim": {}, "complete_shims": sorted(f for f, c in complete.items() if c)}
    for f in SPLIT:
        o, a, b = shim_findings(f, prev_files.get(f, ""), files.get(f), complete.get(f, False))
        rec["shim"][f] = {"old_n": len(o), "new_a": a[:3], "new_a_n": len(a), "new_b": b[:3], "new_b_n": len(b)}
    mods = [stem(f) for f in SPLIT] + [NUM2STEM[j] for j in done]
    rec["import_each_first"] = import_check(d, mods)
    results.append(rec)
    log("card", rec)
    prev_files = {f: files.get(f) for f in SPLIT}
    prev_files.update({n: t for n, t in files.items()})

summary = {"cards": [r["card"] for r in results],
           "order_old_fail": [r["card"] for r in results if r["order_old"]],
           "order_new_fail": [r["card"] for r in results if r["order_new"]],
           "shim_old_fail": [r["card"] for r in results if any(v["old_n"] for v in r["shim"].values())],
           "shim_new_fail": [r["card"] for r in results if any(v["new_a_n"] or v["new_b_n"] for v in r["shim"].values())],
           "import_fail": {r["card"]: {m: e for m, e in r["import_each_first"].items() if e != "ok"} for r in results}}
log("summary", summary)
out = {"plan": None, "results": results, "summary": summary}
with open(PARTIAL, encoding="utf-8") as fh:
    out["log"] = [json.loads(l) for l in fh]
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False))
