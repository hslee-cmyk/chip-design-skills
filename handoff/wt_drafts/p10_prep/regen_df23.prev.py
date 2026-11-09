"""DF-23 전수 목록 재측정기 (P10 `20260930-p10-df23-inventory` 준비용, 읽기 전용).

사용:
    python -B regen_df23.py --repo <저장소> --commit <커밋> --out <json> [--report <md>]
                            [--prev-measured-at <옛 목록을 잰 커밋>]

* 소스는 `git -C <repo> show <commit>:<path>` blob만 읽는다(작업 트리를 보지 않는다).
* 옛 목록(비교·수동 분류 이월 입력)은 같은 커밋의 blob
  `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json`이다.
  옛 목록에 `measured_at`이 없으면 `--prev-measured-at`이 필요하다(1e2e243 -- acad7c8 커밋 설명/초안 기록).
* 방법(옛 목록 `method` 그대로):
  (1) library/*.topology.json에서 소자·넷·회로 어휘를 실제로 수집 -> scope 파일의 문자열 상수(AST Constant,
      f-string 조각 포함)와 정확히 같으면 항목. 역할은 AST 부모 노드로 판정.
  (2) 회로 이름 '줄기' substring(대소문자 무시)으로 파생 이름 보충 -- 줄기 집합은 옛 목록 `stems` 합집합을
      그대로 쓴다(비교 가능성). 한 줄에 한 항목, (1) 항목이 있는 줄은 건너뛴다. 역할은 tokenize 토큰
      종류(NAME/문자열/f-string/주석) + AST(docstring·Dict·Compare)로 판정.
* 담당 Phase: 계획서 N5.2 DF 표의 Phase 열(헤더 '수정 Phase')과 N6.1 순서표 Phase 열을 파싱해 정한다.
  항목별 손 입력 없음. 규칙은 `PHASE_RULE` 문자열(출력 JSON `phase_rule`에도 기록).
"""
import argparse
import ast
import collections
import io
import json
import re
import subprocess
import sys
import tokenize

INV_PATH = "docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json"
PLAN_PATH = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
A = "skills/analog-gmid-design/assets"
LIB = A + "/library"
HARNESS = "workspaces/run_harness.py"
MIN_LEN = 2  # 한 글자 넷 이름(A/B/X/Y)은 어휘에서 뺀다 -- 옛 목록 n_nets 101과 같은 규칙(재수집 보정으로 확인)
PATH_SUFFIX_RE = re.compile(r"\.(topology|instance)\.(json|md)$")
NA = "해당 없음"
MSG = "메시지뿐"
BEH = "동작을 정함"
NEW_PM = "신규(계획 DF-29~34 목록 밖)"
SUB_RAIL = "레일 넷 이름 리터럴(vdd/gnd/vss)"
SUB_FIX_PREFIX = "픽스처 넷리스트"
SUB_OTHER = "기타 넷/소자 이름 리터럴"
SUB_PATH = "파일 이름 규약 리터럴(.topology.json 등)"
SUB_VOCAB = "어휘 충돌(역할 라벨/spec 키 -- 넷·소자 이름 아님)"
SUB_MSG = "메시지·주석·docstring"

PHASE_RULE = (
    "항목 phase: (a) role=메시지뿐 -> '해당 없음'. (b) plan_mapping이 ^DF-(\\d+)이면 계획 N5.2 DF 표 그 행의 Phase 열을 "
    "깊이 0 쉼표로 나눈 조각마다 앞 토큰(N6.1 Phase 이름)을 뽑고 '2'를 뺀다(Phase 2 몫은 목록 자체). 남은 토큰이 하나면 그것, "
    "여럿이면 조각 괄호 안에 '교체'가 있는 토큰 중 N6.1 순서로 가장 이른 것(없으면 가장 이른 토큰) -- 이름 종속을 실제로 없애는 Phase를 고른다"
    "(DF-29 {7a}, DF-32 {6b(교체), 6c(IC4 PASS로 확인)} -> 6b, DF-34 {4(PDK 상수 복사 제거), 7b(데이터 항목으로 교체·함수 삭제)} -> 7b). "
    "(c) DF 밖(신규): 픽스처 넷리스트 -> '3'(MOD7, 사유 기록), 어휘 충돌 -> '해당 없음'(사유), 회로 이름이 없는 파일 이름 규약 -> '해당 없음'(사유). "
    "레일 넷 이름 리터럴은 plan_mapping을 DF-19로, 그 밖의 넷·소자 이름·회로 이름을 담은 경로는 DF-23으로 옮긴 뒤 (b)."
)


# ---------------------------------------------------------------- git blob
def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 실패: {r.stderr.decode('utf-8', 'replace')}")
    return r.stdout


def blob(repo, commit, path):
    return git(repo, "show", f"{commit}:{path}").decode("utf-8")


def ls(repo, commit, path):
    out = git(repo, "ls-tree", "--name-only", commit, path + "/").decode("utf-8")
    return [x for x in out.splitlines() if x]


# ---------------------------------------------------------------- plan tables
def split_row(line):
    cells, cur, i = [], "", 0
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "|"; i += 2; continue
        if c == "|":
            cells.append(cur.strip()); cur = ""; i += 1; continue
        cur += c; i += 1
    cells.append(cur.strip())
    return cells


def parse_n61_phases(plan):
    lines = plan.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("### N6.1"))
    phases = []
    hdr = None
    for l in lines[start + 1:]:
        if l.startswith("### "):
            break
        if not l.startswith("|"):
            if hdr is not None and phases:
                break
            continue
        cells = split_row(l)
        if hdr is None:
            hdr = cells
            continue
        if set(cells[0]) <= set("-: "):
            continue
        phases.append(cells[0].replace("*", "").strip())
    return phases


def parse_df_table(plan):
    lines = plan.splitlines()
    table, col = {}, None
    for idx, l in enumerate(lines):
        if not l.startswith("|"):
            continue
        cells = split_row(l)
        if cells and cells[0] == "ID" and any("Phase" in c for c in cells):
            nxt = [split_row(x)[0] for x in lines[idx + 2: idx + 4] if x.startswith("|")]
            if any(n.startswith("DF-") for n in nxt):
                col = next(i for i, c in enumerate(cells) if "Phase" in c)
                header = cells[col]
            continue
        if col is not None and re.match(r"^DF-\d+$", cells[0]):
            table[cells[0]] = {"phase_cell": cells[col], "line": idx + 1}
    if not table:
        raise SystemExit("계획서에서 DF 표를 찾지 못함")
    return table, header


def phase_segments(cell, phase_names):
    segs, depth, cur = [], 0, ""
    for ch in cell:
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth -= 1
        if ch == "," and depth == 0:
            segs.append(cur); cur = ""
        else:
            cur += ch
    segs.append(cur)
    out = []
    names = sorted(phase_names, key=len, reverse=True)
    for s in segs:
        t = s.strip()
        tok = next((n for n in names if t.startswith(n) and (len(t) == len(n) or not t[len(n)].isalnum())), None)
        if tok is not None:
            out.append((tok, t))
    return out


def choose_phase(cell, order):
    segs = [(t, s) for t, s in phase_segments(cell, order) if t != "2"]
    if not segs:
        return None, []
    toks = [t for t, _ in segs]
    if len(segs) == 1:
        return toks[0], toks
    repl = [t for t, s in segs if "교체" in s]
    pool = repl or toks
    return min(pool, key=order.index), toks


# ---------------------------------------------------------------- vocabulary
def build_vocab(repo, commit):
    files = [p for p in ls(repo, commit, LIB) if p.endswith(".topology.json")]
    circuits, mos, passive, nets, rails = [], set(), set(), set(), set()
    per = {}
    dev_in, net_in = collections.defaultdict(set), collections.defaultdict(set)
    for p in sorted(files):
        d = json.loads(blob(repo, commit, p))
        name = p.rsplit("/", 1)[1][: -len(".topology.json")]
        circuits.append(name)
        cd, cn = set(), set()
        for e in d.get("netlist") or []:
            if not isinstance(e, dict) or "name" not in e:
                continue
            (mos if e.get("kind") in ("nmos", "pmos") else passive).add(e["name"])
            cd.add(e["name"])
            for k in ("source", "drain", "gate", "body", "bulk"):
                if isinstance(e.get(k), str):
                    cn.add(e[k])
        for f in ("passive_elements", "ideal_sources"):
            for e in d.get(f) or []:
                if isinstance(e, dict) and "name" in e:
                    passive.add(e["name"]); cd.add(e["name"])
                    for t in e.get("terminals") or []:
                        if isinstance(t, str):
                            cn.add(t)
        for r in d.get("supply_nets") or []:
            if isinstance(r, str):
                rails.add(r); cn.add(r)
        for x in cd:
            dev_in[x].add(name)
        for x in cn:
            net_in[x].add(name)
        nets |= {x for x in cn if len(x) >= MIN_LEN}
        per[name] = {"n_devices": len(cd), "n_nets": len(cn)}  # 회로별 수는 한 글자 넷 포함(옛 목록과 같음)
    # 종류는 netlist kind가 정한다(nmos/pmos = device). 옛 목록은 MP/MN(folded_cascode netlist의 pmos/nmos
    # 다이오드 레퍼런스)을 passive로 적었다 -- 재측정은 선언 kind를 따른다(보고서에 차이로 기록).
    passive -= mos
    return {
        "n_devices": len(mos | passive), "n_nets": len(nets), "n_circuits": len(circuits),
        "circuits": circuits, "per_circuit": per, "mos_devices": sorted(mos),
        "passive_elements": sorted(passive), "net_sample": sorted(nets)[:60],
        "rail_nets_from_supply_nets": sorted(rails),
    }, {"nets": nets, "mos": mos, "passive": passive, "circuits": set(circuits), "rails": rails,
        "dev_in": dev_in, "net_in": net_in}


# ---------------------------------------------------------------- AST helpers
def parents_map(tree):
    par = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            par[c] = n
    return par


def docstring_nodes(tree):
    ds = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for st in n.body:
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
                    ds.add(st.value)
        # 모든 bare 문자열 문장(설명 문자열)도 docstring 취급
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            ds.add(n.value)
    return ds


def func_resolver(tree, nlines):
    owner = ["<module>"] * (nlines + 2)
    for st in tree.body:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            lo = min([st.lineno] + [d.lineno for d in st.decorator_list])
            for ln in range(lo, st.end_lineno + 1):
                owner[ln] = st.name
            if isinstance(st, ast.ClassDef):
                for m in st.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        mlo = min([m.lineno] + [d.lineno for d in m.decorator_list])
                        for ln in range(mlo, m.end_lineno + 1):
                            owner[ln] = f"{st.name}.{m.name}"
    return lambda ln: owner[ln] if 0 < ln < len(owner) else "<module>"


def call_name(c):
    f = c.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return type(f).__name__


def exact_role_reason(node, par, is_path):
    if is_path:
        return "경로 조립(os.path.join/f-string)"
    p = par.get(node)
    if isinstance(p, ast.Dict):
        return "dict key" if node in p.keys else "Dict"
    if isinstance(p, ast.Subscript) and p.slice is node:
        return "딕셔너리 조회 키"
    if isinstance(p, ast.Call):
        if node in p.args:
            if isinstance(p.func, ast.Attribute) and p.func.attr == "get" and p.args and p.args[0] is node:
                return "get() 키"
            return f"호출 인자 {call_name(p)}()"
    if isinstance(p, ast.keyword):
        return f"키워드 인자 {p.arg}="
    if isinstance(p, ast.Compare):
        return "비교(분기 조건)"
    if isinstance(p, ast.IfExp):
        return "IfExp"
    if isinstance(p, (ast.Assign, ast.AnnAssign)):
        return "상수 대입 "
    if isinstance(p, (ast.Tuple, ast.List, ast.Set)):
        pp = par.get(p)
        if isinstance(pp, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in pp.ops):
            return "멤버십 검사(in)"
        if isinstance(pp, ast.Call) and p in pp.args:
            return f"호출 인자 {call_name(pp)}(...)"
        return "컨테이너 원소"
    return type(p).__name__ if p is not None else "?"


# ---------------------------------------------------------------- scanning
def scan_file(path, src, V, stems, fixture_fns):
    tree = ast.parse(src)
    par = parents_map(tree)
    lines = src.splitlines()
    fn_of = func_resolver(tree, len(lines))
    ds = docstring_nodes(tree)
    items = []
    exact_lines = set()
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)):
            continue
        s = n.value
        kind = None
        if s in V["circuits"]:
            kind = "circuit"
        elif PATH_SUFFIX_RE.search(s) or any(s == c + ".topology.json" for c in V["circuits"]):
            kind = "path"
        elif s in V["mos"]:
            kind = "device"
        elif s in V["passive"]:
            kind = "element(passive/source)"
        elif s in V["nets"]:
            kind = "net"
        if kind is None:
            continue
        ln = n.lineno
        declared = {}
        if kind in ("device", "element(passive/source)"):
            declared = {"device_in": sorted(V["dev_in"][s])}
        elif kind == "net":
            declared = {"net_in": sorted(V["net_in"][s])}
        if n in ds:
            role, reason = MSG, "docstring/설명 문자열"
        else:
            role, reason = BEH, exact_role_reason(n, par, kind == "path")
        exact_lines.add(ln)
        items.append({
            "file": path, "line": ln, "literal": s, "kind": kind, "function": fn_of(ln),
            "role": role, "role_reason": reason, "declared_in": declared,
            "source_line": lines[ln - 1].strip(),
            "scan": "exact-match(어휘는 library/*.topology.json에서 수집)", "_col": n.col_offset,
        })
    # ---- stem substring scan
    stem_re = re.compile("|".join(re.escape(s) for s in sorted(stems, key=len, reverse=True)), re.I)
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    str_nodes = [n for n in ast.walk(tree) if isinstance(n, (ast.Constant, ast.JoinedStr))
                 and (not isinstance(n, ast.Constant) or isinstance(n.value, str))]
    defs = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.setdefault(n.lineno, []).append(n.name)
    dict_spans = [(n.lineno, n.end_lineno) for n in ast.walk(tree) if isinstance(n, ast.Dict)]
    cmp_spans = [(n.lineno, n.end_lineno) for n in ast.walk(tree) if isinstance(n, ast.Compare)]

    row_toks = collections.defaultdict(list)
    for i, t in enumerate(toks):
        for rr in range(t.start[0], t.end[0] + 1):
            row_toks[rr].append(i)

    def tok_at(r, c):
        for i in row_toks.get(r, []):
            t = toks[i]
            (sr, sc), (er, ec) = t.start, t.end
            if (sr, sc) <= (r, c) < (er, ec):
                return i, t
        return None, None

    def enclosing_str_node(r, c):
        best = None
        c = len(lines[r - 1][:c].encode("utf-8"))  # AST col_offset는 UTF-8 바이트
        for n in str_nodes:
            if (n.lineno, n.col_offset) <= (r, c) < (n.end_lineno, n.end_col_offset):
                if best is None or (n.lineno, n.col_offset) >= (best.lineno, best.col_offset):
                    best = n
        return best

    def in_span(spans, r):
        return any(a <= r <= b for a, b in spans)

    def str_context(node):
        top = node
        while isinstance(par.get(top), ast.JoinedStr):
            top = par[top]
        if top in ds:
            return MSG, "docstring/설명 문자열"
        p = par.get(top)
        ident = isinstance(top, ast.Constant) and re.fullmatch(r"[\w.\-/*]+", top.value or "") is not None
        if not ident:  # 산문(공백 포함)·f-string은 어디 있든 메시지
            return MSG, "문자열 안(설명/오류 메시지)"
        if isinstance(p, ast.Dict):
            return BEH, "dict 키(레지스트리 항목)"
        if isinstance(p, ast.Compare) or (isinstance(p, (ast.Tuple, ast.List, ast.Set)) and isinstance(par.get(p), ast.Compare)):
            return BEH, "분기 비교/멤버십"
        if isinstance(p, ast.Subscript) and p.slice is top:
            return BEH, "딕셔너리 조회 키"
        return MSG, "문자열 안(설명/오류 메시지)"

    by_line = collections.OrderedDict()
    for r, text in enumerate(lines, 1):
        if r in exact_lines:
            continue
        ms = list(stem_re.finditer(text))
        if not ms:
            continue
        roles = []
        for m in ms:
            c = m.start()
            i, t = tok_at(r, c)
            if t is None:
                # 여러 줄 문자열 안(토큰이 앞 줄에서 시작)
                node = enclosing_str_node(r, c)
                roles.append(str_context(node) if node is not None else (MSG, "문자열 안(설명/오류 메시지)"))
                continue
            tn = tokenize.tok_name[t.type]
            if tn == "COMMENT":
                roles.append((MSG, "주석"))
            elif tn == "NAME":
                nxt = toks[i + 1] if i + 1 < len(toks) else None
                if r in defs and any(stem_re.search(d) for d in defs[r]) and t.string in defs[r]:
                    roles.append((BEH, "함수 정의 이름"))
                elif nxt is not None and nxt.string == "(":
                    roles.append((BEH, "식별자 참조(호출/디스패치 값)"))
                elif in_span(dict_spans, r):
                    roles.append((BEH, "dict 키(레지스트리 항목)"))
                elif in_span(cmp_spans, r):
                    roles.append((BEH, "분기 비교/멤버십"))
                else:
                    roles.append((BEH, "코드 줄(수동 확인 필요)"))
            else:  # STRING / FSTRING_* / TSTRING_*
                node = enclosing_str_node(r, c)
                roles.append(str_context(node) if node is not None else (MSG, "문자열 안(설명/오류 메시지)"))
        beh = [x for x in roles if x[0] == BEH]
        role, reason = (beh[0] if beh else roles[0])
        by_line[r] = {
            "file": path, "line": r, "literal": "(회로 이름 줄기)", "kind": "circuit(파생 이름)",
            "function": fn_of(r), "role": role, "role_reason": reason, "declared_in": {},
            "source_line": text.strip(), "stems": sorted({m.group(0).lower() for m in ms}),
            "scan": "stem-substring(파생 이름 포함)", "_col": ms[0].start(),
        }
    items.extend(by_line.values())
    return items, fn_of


# ---------------------------------------------------------------- carry-forward & mapping
def key_of(x):
    return (x["file"], x["literal"], x["source_line"].strip())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report")
    ap.add_argument("--prev-measured-at")
    ap.add_argument("--preamble", help="보고서 앞에 붙일 사람이 쓴 md")
    ap.add_argument("--calibrate", action="store_true",
                    help="옛 목록을 잰 커밋에서 같은 스캐너를 돌려 옛 목록과의 일치도를 보고")
    a = ap.parse_args(argv)
    repo = a.repo
    sha = git(repo, "rev-parse", a.commit + "^{commit}").decode().strip()
    old = json.loads(blob(repo, sha, INV_PATH))
    prev = old.get("measured_at") or a.prev_measured_at
    if not prev:
        raise SystemExit("옛 목록에 measured_at이 없어 --prev-measured-at 필요")
    prev = git(repo, "rev-parse", prev + "^{commit}").decode().strip()
    plan = blob(repo, sha, PLAN_PATH)
    order = parse_n61_phases(plan)
    if "2" not in order:
        raise SystemExit(f"N6.1 Phase 열에 '2'가 없다: {order}")
    closed = order[order.index("2") + 1:] + [NA]
    dft, df_header = parse_df_table(plan)

    stems = sorted({s for x in old["items"] for s in x.get("stems", [])})
    old_fixture_ctx = {}
    for x in old["items"]:
        if x["context"] != "운영":
            old_fixture_ctx.setdefault(x["file"], {})
    # 옛 항목의 함수 이름은 옛 커밋 blob에서 같은 규칙으로 다시 구한다(옛 목록의 '' 90개 보정)
    old_fn = {}
    for f in sorted({x["file"] for x in old["items"]}):
        try:
            osrc = blob(repo, prev, f)
        except SystemExit:
            continue
        otree = ast.parse(osrc)
        old_fn[f] = func_resolver(otree, len(osrc.splitlines()))
    for x in old["items"]:
        x["_fn"] = old_fn[x["file"]](x["line"]) if x["file"] in old_fn else x["function"]
    fixture_fns = {(x["file"], x["_fn"]): x["context"] for x in old["items"] if x["context"] != "운영"}
    fn_pm = collections.defaultdict(collections.Counter)
    for x in old["items"]:
        if x["role"] == BEH:
            fn_pm[(x["file"], x["_fn"])][(x["plan_mapping"], x.get("new_subcategory", ""))] += 1

    vocab_out, V = build_vocab(repo, sha)
    scope = sorted(p for p in ls(repo, sha, A) if p.endswith(".py") and p.count("/") == A.count("/") + 1) + [HARNESS]
    items = []
    for p in scope:
        its, _ = scan_file(p, blob(repo, sha, p), V, stems, fixture_fns)
        items.extend(its)
    items.sort(key=lambda x: (x["file"], x["line"], x["_col"], x["literal"]))

    # carry-forward (수동 분류: plan_mapping, new_subcategory, context, 어휘 충돌 kind)
    pool = collections.defaultdict(list)
    for x in old["items"]:
        pool[key_of(x)].append(x)
    for k in pool:
        pool[k].sort(key=lambda x: x["line"])
    used = set()
    for x in items:
        cands = [o for o in pool.get(key_of(x), []) if id(o) not in used and o["role"] == x["role"]] or \
                [o for o in pool.get(key_of(x), []) if id(o) not in used]
        o = cands[0] if cands else None
        if o is not None:
            used.add(id(o))
            x["_old"] = o
            x["plan_mapping"] = o["plan_mapping"]
            x["new_subcategory"] = o.get("new_subcategory", "")
            x["context"] = o["context"]
            if o["kind"].startswith("어휘 충돌"):
                x["kind"] = o["kind"]
            x["mapping_source"] = "이월(옛 목록 같은 파일·리터럴·줄 내용)"
            if o["role"] != x["role"]:
                x["mapping_source"] += f"; 역할 재판정 {o['role']}->{x['role']}"
                if x["role"] == MSG:
                    x["new_subcategory"] = SUB_MSG if not x["plan_mapping"].startswith("DF-") else ""
            continue
        ctx = fixture_fns.get((x["file"], x["function"]), "운영")
        x["context"] = ctx
        inh = fn_pm.get((x["file"], x["function"]))
        if x["role"] == BEH and inh and len(inh) == 1:
            (pm, sub), = inh.keys()
            x["plan_mapping"], x["new_subcategory"] = pm, sub
            x["mapping_source"] = "함수 상속(옛 목록 같은 함수의 동작 항목이 한 가지 분류)"
        elif x["role"] == MSG:
            x["plan_mapping"], x["new_subcategory"] = NEW_PM, SUB_MSG
            x["mapping_source"] = "규칙(메시지뿐)"
        else:
            x["plan_mapping"] = NEW_PM
            if ctx != "운영":
                x["new_subcategory"] = next((o.get("new_subcategory") for o in old["items"]
                                             if (o["file"], o["_fn"]) == (x["file"], x["function"])
                                             and o.get("new_subcategory", "").startswith(SUB_FIX_PREFIX)), SUB_FIX_PREFIX)
            elif x["kind"] == "net" and x["literal"] in V["rails"]:
                x["new_subcategory"] = SUB_RAIL
            elif x["kind"] == "path":
                x["new_subcategory"] = SUB_PATH
            else:
                x["new_subcategory"] = SUB_OTHER
            x["mapping_source"] = "규칙(새 항목 -- 검토 대상)"

    # P10 담당 Phase 배정 (계획 표에서)
    for x in items:
        pm, sub = x["plan_mapping"], x.get("new_subcategory", "")
        x.pop("phase_reason", None)
        if x["role"] == MSG:
            if pm.startswith("DF-"):
                x["related_plan_mapping"] = pm
                x["plan_mapping"] = f"메시지뿐(관련 {pm})"
            x["phase"] = NA
            x["phase_reason"] = "메시지뿐(주석·docstring·메시지 문자열) -- 동작을 정하지 않는다"
            continue
        if not pm.startswith("DF-"):
            if sub == SUB_RAIL:
                x["related_plan_mapping"] = pm
                x["plan_mapping"] = pm = "DF-19"
            elif sub.startswith(SUB_FIX_PREFIX) or x["context"] != "운영":
                x["phase"] = "3"
                x["phase_reason"] = ("픽스처 넷리스트(운영 호출부 0) -- MOD7: stick_diagram은 레이아웃만 남고 픽스처는 "
                                     "Phase 3 모듈 분할에서 운영 모듈 밖으로 나간다. 계획 DF 표에 행이 없다(레지스트리 행 없음)")
                continue
            elif sub.startswith("어휘 충돌") or x["kind"].startswith("어휘 충돌"):
                x["phase"] = NA
                x["phase_reason"] = "어휘 충돌 -- 역할 라벨/spec 키가 우연히 넷·소자 이름과 같은 문자열일 뿐 넷·소자 이름 종속이 아니다"
                continue
            elif sub == SUB_PATH and not any(c in x["literal"] for c in V["circuits"]):
                x["phase"] = NA
                x["phase_reason"] = "특정 회로를 가리키지 않는 파일 이름 규약(접미사·glob) -- 회로 이름 종속이 아니다"
                continue
            else:
                x["related_plan_mapping"] = pm
                x["plan_mapping"] = pm = "DF-23"
        dfid = re.match(r"^DF-\d+", pm).group(0)
        if dfid not in dft:
            raise SystemExit(f"{x['file']}:{x['line']} plan_mapping {pm}: 계획 DF 표에 없음")
        ph, toks = choose_phase(dft[dfid]["phase_cell"], order)
        if ph is None:
            raise SystemExit(f"{dfid} Phase 열에서 2 뒤 Phase를 못 찾음: {dft[dfid]['phase_cell']}")
        x["phase"] = ph
        if len(toks) > 1:
            x["phase_reason"] = f"{dfid} Phase 열 토큰 {toks} 중 '교체' 조각 규칙으로 {ph}"
        if x.get("related_plan_mapping"):
            x["phase_reason"] = (x.get("phase_reason", "") + f"; 원래 분류 '{x['related_plan_mapping']}' "
                                 f"-> {dfid}({'레일 이름 집합 하드코딩, DF-19 위치 열' if dfid == 'DF-19' else 'DF-23 일반 규칙 교체'})").lstrip("; ")

    for x in items:
        x.pop("_col", None)
        x.pop("_old", None)
        if x["phase"] not in closed:
            raise SystemExit(f"phase {x['phase']} 닫힌 집합 밖")
    cnt = lambda f: dict(collections.Counter(f(x) for x in items).most_common())
    beh = [x for x in items if x["role"] == BEH]
    out = {
        "measured_at": sha,
        "scope": f"{A}/*.py ({len(scope) - 1}개) + {HARNESS}",
        "scope_files": scope,
        "method": old["method"],
        "method_params": {
            "stems(옛 목록 stems 합집합)": stems,
            "path_rule": "문자열 상수가 " + PATH_SUFFIX_RE.pattern + " 에 맞거나 '<회로>.topology.json'",
            "kind_precedence": "circuit > path > device(mos) > element(passive/source) > net",
            "vocab_min_len": "넷·소자 이름 길이 2 이상(한 글자 넷 A/B/X/Y 제외 -- 옛 목록 어휘 수와 같음)",
            "stem_string_rule": "줄기 스캔에서 문자열은 식별자·경로 모양([\\w.\\-/*]+)이고 Dict·Compare·Subscript 안일 때만 동작, 그 밖(산문·f-string)은 메시지",
            "function": "그 줄을 감싼 최상위 def·class 이름(메서드면 Class.method), 모듈 수준이면 <module>",
            "stem_line_rule": "한 줄 한 항목, exact 항목이 있는 줄 제외, 토큰 종류로 역할(NAME=동작, 주석/docstring/메시지 문자열=메시지뿐, Dict·Compare·Subscript 안 문자열=동작)",
            "carry_forward": "plan_mapping·new_subcategory·context·어휘 충돌 kind는 옛 목록에서 (file, literal, 줄 내용) 일치로 이월, 없으면 같은 함수 상속, 없으면 규칙",
            "prev_inventory_measured_at": prev,
        },
        "phase_rule": PHASE_RULE,
        "phase_source": {"plan": PLAN_PATH, "df_table_phase_header": df_header,
                         "df_rows": {k: v["phase_cell"] for k, v in sorted(dft.items()) if k in
                                     {re.match(r"^DF-\d+", x["plan_mapping"]).group(0) for x in items if x["plan_mapping"].startswith("DF-")}},
                         "n61_order": order, "closed_set": closed},
        "vocabulary": vocab_out,
        "totals": {
            "n_items": len(items),
            "by_role": cnt(lambda x: x["role"]),
            "by_phase": cnt(lambda x: x["phase"]),
            "by_plan_mapping": cnt(lambda x: x["plan_mapping"]),
            "by_kind": cnt(lambda x: x["kind"]),
            "by_context": cnt(lambda x: x["context"]),
            "by_file_role": cnt(lambda x: f"{x['file']} | {x['role']}"),
            "new_subcategories": cnt(lambda x: x.get("new_subcategory", "")),
            "behavior_items_by_file": dict(collections.Counter(x["file"] for x in beh).most_common()),
            "behavior_by_phase": dict(collections.Counter(x["phase"] for x in beh).most_common()),
            "by_mapping_source": cnt(lambda x: x["mapping_source"].split("(")[0]),
        },
        "items": items,
    }
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    # ------------------------------------------------ diff vs old inventory
    if a.report:
        rep = diff_report(repo, sha, prev, old, out, stems, V)
        if a.preamble:
            rep = open(a.preamble, encoding="utf-8").read().rstrip() + "\n\n---\n\n(아래는 regen_df23.py 자동 출력)\n\n" + rep
        if a.calibrate:
            rep += calibrate(repo, prev, old, V, stems, fixture_fns)
        with open(a.report, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(rep)
    print(json.dumps(out["totals"], ensure_ascii=False)[:2000])


def diff_report(repo, sha, prev, old, new, stems, V):
    L = []
    oi, ni = old["items"], new["items"]
    L.append(f"# DF-23 목록 재측정 보고 (regen_df23.py)\n")
    L.append(f"* 재측정 커밋 `measured_at` = `{sha}`, 옛 목록 측정 커밋 = `{prev}` "
             f"(`git rev-list --count`: {git(repo, 'rev-list', '--count', f'{prev}..{sha}').decode().strip()}커밋 차이).")
    L.append(f"* 항목 수: 옛 {len(oi)} -> 새 {len(ni)}.\n")

    def table(title, f_old, f_new):
        co, cn = collections.Counter(map(f_old, oi)), collections.Counter(map(f_new, ni))
        L.append(f"### {title}\n\n| 값 | 옛 | 새 | 차 |\n|---|---:|---:|---:|")
        for k in sorted(set(co) | set(cn), key=lambda k: (-(cn[k] + co[k]), str(k))):
            L.append(f"| {k} | {co[k]} | {cn[k]} | {cn[k] - co[k]:+d} |")
        L.append("")

    table("role별", lambda x: x["role"], lambda x: x["role"])
    table("plan_mapping별(새 목록의 P10 재분류 전 값 = related_plan_mapping 우선)",
          lambda x: x["plan_mapping"], lambda x: x.get("related_plan_mapping", x["plan_mapping"]))
    table("plan_mapping별(새 목록 최종값)", lambda x: x["plan_mapping"], lambda x: x["plan_mapping"])
    table("동작 항목 plan_mapping별(재분류 전 값)", lambda x: x["plan_mapping"] if x["role"] == BEH else None,
          lambda x: x.get("related_plan_mapping", x["plan_mapping"]) if x["role"] == BEH else None)
    table("kind별", lambda x: x["kind"], lambda x: x["kind"])
    L.append("### phase별(새 목록만 -- 옛 목록엔 phase 없음)\n\n| phase | 전체 | 동작을 정함 |\n|---|---:|---:|")
    cp = collections.Counter(x["phase"] for x in ni)
    cb = collections.Counter(x["phase"] for x in ni if x["role"] == BEH)
    for k in new["phase_source"]["closed_set"]:
        if cp[k]:
            L.append(f"| {k} | {cp[k]} | {cb[k]} |")
    L.append("")

    # appeared / disappeared / moved
    po = collections.defaultdict(list)
    for x in oi:
        po[key_of(x)].append(x)
    pn = collections.defaultdict(list)
    for x in ni:
        pn[key_of(x)].append(x)
    same = moved = 0
    appeared, gone, moved_l = [], [], []
    for k in set(po) | set(pn):
        a_, b_ = sorted(po.get(k, []), key=lambda x: x["line"]), sorted(pn.get(k, []), key=lambda x: x["line"])
        for o, n in zip(a_, b_):
            if o["line"] == n["line"]:
                same += 1
            else:
                moved += 1; moved_l.append((o, n))
        gone += a_[len(b_):]
        appeared += b_[len(a_):]
    L.append("### 항목 대응(키 = 파일·리터럴·줄 내용, 같은 키는 줄 순서로 짝)\n")
    L.append(f"| 구분 | 전체 | 동작을 정함 |\n|---|---:|---:|")
    L.append(f"| 줄까지 같음 | {same} | {sum(1 for k in pn for o, n in zip(sorted(po.get(k, []), key=lambda x: x['line']), sorted(pn[k], key=lambda x: x['line'])) if o['line'] == n['line'] and n['role'] == BEH)} |")
    L.append(f"| 옮겨감(내용 같고 줄 다름) | {moved} | {sum(1 for o, n in moved_l if n['role'] == BEH)} |")
    L.append(f"| 사라짐(옛에만) | {len(gone)} | {sum(1 for x in gone if x['role'] == BEH)} |")
    L.append(f"| 나타남(새에만) | {len(appeared)} | {sum(1 for x in appeared if x['role'] == BEH)} |\n")
    rc = collections.Counter((o["role"], n["role"]) for o, n in moved_l)
    L.append(f"옮겨간 항목의 역할 변화(옛->새): {dict(rc)}\n")

    def fn_counter(xs, key):
        return collections.Counter((x["file"].rsplit('/', 1)[1], x[key] or "''") for x in xs).most_common()

    L.append("#### 사라진 동작 항목(옛 목록 기준, 파일·옛 함수별 -- 함수 '' 는 옛 커밋 blob에서 다시 구한 이름)\n")
    for (f, fn), c in fn_counter([x for x in gone if x["role"] == BEH], "_fn"):
        L.append(f"* {f} `{fn}`: {c}")
    L.append("\n#### 사라진 메시지 항목(파일·옛 함수별 상위 15)\n")
    for (f, fn), c in fn_counter([x for x in gone if x["role"] == MSG], "_fn")[:15]:
        L.append(f"* {f} `{fn}`: {c}")
    L.append("\n#### 나타난 동작 항목(전부)\n")
    L.append("| 파일:줄 | 함수 | 리터럴 | role_reason | plan_mapping | phase | 분류 출처 | 줄 |\n|---|---|---|---|---|---|---|---|")
    for x in sorted([x for x in appeared if x["role"] == BEH], key=lambda x: (x["file"], x["line"])):
        L.append(f"| {x['file'].rsplit('/', 1)[1]}:{x['line']} | `{x['function']}` | `{x['literal']}` | {x['role_reason']} | "
                 f"{x['plan_mapping']} | {x['phase']} | {x['mapping_source'].split('(')[0]} | `{x['source_line'][:90].replace('|', '/')}` |")
    L.append("\n#### 나타난 메시지 항목(파일·함수별)\n")
    for (f, fn), c in fn_counter([x for x in appeared if x["role"] == MSG], "function"):
        L.append(f"* {f} `{fn}`: {c}")
    L.append("\n#### 규칙으로 분류된(이월·상속 아님) 동작 항목 -- 오케스트레이터 검토 대상\n")
    rs = [x for x in ni if x["role"] == BEH and x["mapping_source"].startswith("규칙")]
    L.append(f"{len(rs)}개" + ("" if not rs else ": " + ", ".join(
        f"{x['file'].rsplit('/', 1)[1]}:{x['line']} `{x['literal']}`->{x['plan_mapping']}/{x['phase']}" for x in rs)))
    L.append("\n#### 역할 재판정(이월 대응은 됐지만 새 규칙의 role이 옛 role과 다름)\n")
    rr = [x for x in ni if "역할 재판정" in x["mapping_source"]]
    L.append(f"{len(rr)}개")
    for x in rr:
        L.append(f"* {x['file'].rsplit('/', 1)[1]}:{x['line']} {x['mapping_source'].split('; ')[1]} ({x['role_reason']}) `{x['source_line'][:90]}`")
    L.append("")
    return "\n".join(L) + "\n"


def calibrate(repo, prev, old, V_now, stems, fixture_fns):
    """옛 측정 커밋에서 같은 스캐너를 돌려 옛 목록과 비교 -- 생성기의 비교 가능성 근거."""
    vocab_out, V = build_vocab(repo, prev)
    ov = old["vocabulary"]
    L = ["## 보정(calibration): 옛 측정 커밋 `%s`에서 같은 스캐너 대 옛 목록\n" % prev]
    L.append(f"* 어휘: 옛 n_devices {ov['n_devices']}/n_nets {ov['n_nets']}/n_circuits {ov['n_circuits']} 대 "
             f"재수집 {vocab_out['n_devices']}/{vocab_out['n_nets']}/{vocab_out['n_circuits']}; "
             f"mos 집합 같음={set(ov['mos_devices']) == set(vocab_out['mos_devices'])}, "
             f"passive 집합 같음={set(ov['passive_elements']) == set(vocab_out['passive_elements'])}, "
             f"per_circuit 같음={ov['per_circuit'] == vocab_out['per_circuit']}, circuits 같음={ov['circuits'] == vocab_out['circuits']}")
    scope = sorted(p for p in ls(repo, prev, A) if p.endswith(".py") and p.count("/") == A.count("/") + 1) + [HARNESS]
    items = []
    for p in scope:
        its, _ = scan_file(p, blob(repo, prev, p), V, stems, fixture_fns)
        items.extend(its)
    ex_new = collections.Counter((x["file"], x["line"], x["literal"]) for x in items if x["scan"].startswith("exact"))
    ex_old = collections.Counter((x["file"], x["line"], x["literal"]) for x in old["items"] if x["scan"].startswith("exact"))
    L.append(f"* exact 항목: 옛 {sum(ex_old.values())}, 재스캔 {sum(ex_new.values())}, 공통 {sum((ex_old & ex_new).values())}, "
             f"옛에만 {sum((ex_old - ex_new).values())}, 재스캔에만 {sum((ex_new - ex_old).values())}")
    for k, c in list((ex_old - ex_new).items())[:20]:
        L.append(f"  * 옛에만 {k[0].rsplit('/', 1)[1]}:{k[1]} `{k[2]}` x{c}")
    for k, c in list((ex_new - ex_old).items())[:20]:
        L.append(f"  * 재스캔에만 {k[0].rsplit('/', 1)[1]}:{k[1]} `{k[2]}` x{c}")
    rn = collections.Counter((x["file"], x["line"], x["literal"], x["role_reason"]) for x in items if x["scan"].startswith("exact"))
    ro = collections.Counter((x["file"], x["line"], x["literal"], x["role_reason"]) for x in old["items"] if x["scan"].startswith("exact"))
    L.append(f"* exact 항목 role_reason 일치 {sum((rn & ro).values())}/{sum(ro.values())}")
    for k, c in list((ro - rn).items())[:10]:
        L.append(f"  * 옛 role_reason 불일치 {k[0].rsplit('/', 1)[1]}:{k[1]} `{k[2]}` 옛='{k[3]}'")
    fo = {(x["file"], x["line"], x["literal"]): x["function"] for x in old["items"] if x["scan"].startswith("exact")}
    fn_ = {(x["file"], x["line"], x["literal"]): x["function"] for x in items if x["scan"].startswith("exact")}
    agree = sum(1 for k in fo if k in fn_ and fn_[k] == fo[k])
    L.append(f"* exact 항목 function 일치 {agree}/{len(fo)}" + "".join(
        f"\n  * {k[0].rsplit('/', 1)[1]}:{k[1]} 옛 `{fo[k]}` 새 `{fn_.get(k)}`" for k in fo if k in fn_ and fn_[k] != fo[k]))
    so = {(x["file"], x["line"]): x for x in old["items"] if x["scan"].startswith("stem")}
    sn = {(x["file"], x["line"]): x for x in items if x["scan"].startswith("stem")}
    both = set(so) & set(sn)
    L.append(f"* stem 줄: 옛 {len(so)}, 재스캔 {len(sn)}, 공통 {len(both)}, 옛에만 {len(set(so) - set(sn))}, 재스캔에만 {len(set(sn) - set(so))}")
    for k in sorted(set(so) - set(sn))[:15]:
        L.append(f"  * 옛에만 {k[0].rsplit('/', 1)[1]}:{k[1]} `{so[k]['source_line'][:80]}`")
    for k in sorted(set(sn) - set(so))[:15]:
        L.append(f"  * 재스캔에만 {k[0].rsplit('/', 1)[1]}:{k[1]} `{sn[k]['source_line'][:80]}`")
    rag = collections.Counter((so[k]["role"], sn[k]["role"]) for k in both)
    L.append(f"* stem 공통 줄 role(옛, 재스캔) 분포: {dict(rag)}")
    dis = [k for k in sorted(both) if so[k]["role"] != sn[k]["role"]]
    for k in dis[:40]:
        L.append(f"  * {k[0].rsplit('/', 1)[1]}:{k[1]} 옛 {so[k]['role']}/{so[k]['role_reason']} -> 재스캔 {sn[k]['role']}/{sn[k]['role_reason']} `{so[k]['source_line'][:80]}`")
    if len(dis) > 40:
        L.append(f"  * ... 외 {len(dis) - 40}")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
