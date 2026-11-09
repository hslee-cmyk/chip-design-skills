"""F1 작성 전 실측 -- 실행 문자열(내장 스크립트) 전수 스캔(측정 전용, 판정 도구가 아니다: auditor는 계약 문언만 보고 독립으로 쓴다).

review_p3_f1_b34t B1: `test_b34_grammar_explicit.py`의 `_B34_FRESH_SCRIPT`(subprocess `-c`로 실행되는 문자열)가 SD 삭제 집합 이름을 읽는데
design §10 `E3_AST`·`E3B_AST file_reads`는 문자열 안을 보지 않는다.

    python -B f12_execstr.py <저장소 루트> <rev> <out.json> [--drop <SD 삭제 집합 json 목록>] [--drop-acf <ACF 삭제 집합 json 목록>]

규칙 = 계약 1 (e) 문언(b1fix3 2026-10-07, review_p3_f1_b1fix2 m1~m4 반영). 문언과 이 파일이 다른 곳이 있으면 문언이 맞고 이 파일이 틀린 것이다
(selftest: out/b1fix/selftest_execstr_b1fix3.py -- review_p3_f1_b1fix2 1.3 적대 입력).
 실행 문자열 = 추적 .py 안 문자열 상수(`ast.Constant` str, docstring 자리 제외) 중 같은 파일 안에서 실행 자리에 닿는 것.
   실행 자리: (s1) 내장 `exec`·`eval`·`compile` 이름 호출의 첫 인자, (s2) 첫 원소가 인터프리터인 리스트·튜플 표시의 옵션 구간 `"-c"` 바로 뒤 원소,
             (s3) `write_text`·`write`의 첫 인자(어느 경로로 닿든 스크립트 모양인 문자열만).
   닿음: 자리 식을 감싼 식(w1 `%` 왼쪽, w2 format·format_map·replace·strip·lstrip·rstrip 수신자, w3 dedent·textwrap.dedent·str 첫 인자)과
         `+`로 풀어 나온 잎이 ① 문자열 상수 ② 이름 -- 그 이름에 대입된 값(파일 안 모든 대입문 `=`·주석 대입·`+=`)을 같은 풀이로 다시 푼다
         (m3: 대입값도 w1~w3·`+`로 푼다. 이미 푸는 중인 이름은 다시 풀지 않는다 -- 순환 가드)
         ③ 둘러싼 **보통 함수**(클래스 본문 바로 아래 def = 메서드가 아닌 def)의 위치 매개변수 -- 그 함수 이름을 부르는 **이름 호출**의
            같은 위치·같은 키워드 인자(고정점; 같은 이름의 보통 함수가 여럿이면 모두의 합. 메서드는 이 표에 들지 않는다 -- m1).
   규칙 밖(기록만, kind): 잎이 ①~③으로 풀리지 않는 것 -- 목록 밖 호출 결과·대입이 없는 이름 등(outside), 메서드 매개변수(method),
         keyword-only(kwonly)·`*`/`**`(vararg)·lambda(lambda) 매개변수, ③ 함수를 `partial`에 넘긴 자리(partial). (s1)·(s2) 자리만 기록한다.
         f-string 잎은 멈춤 표지(stop_fstring). 자리 = (파일, 자리 식에서 풀려 나온 첫 잎의 줄) -- 잎 수는 세지 않는다(m2).
   템플릿: w1·format·format_map을 거쳐서만 닿은 상수. 자리표시자를 `__f12_fmt_<k>__`로 채워 파싱하고, 자리표시자가 import 모듈 자리
         (import 문 모듈 이름·import 호출 첫 인자 상수)에 왔는데 그 경로의 format·`%` 인자가 그 호출 자리의 문자열 상수이면 그 값으로 채워
         다시 파싱해 판정한다(m4). 상수가 아니면 동적 import로 자리만 적는다.
   파싱 실패((s1)·(s2)) = parse_fail(계약상 FAIL·멈춤).
 보조 검출(내용) = 문자열 상수가 파싱되고 import 문이 있는 것, 파싱되지 않지만 줄 머리 import 모양이 있는 것(content_only_unparsed).
각 내장 파일에 design §10 E3_AST 식(SR·TL·DR)과 E3B_AST `file_reads`(SD·ACF 각각 -- 계약 1 (b) 'ACF에도 같은 식')를 적용한다.
"""
import ast
import json
import re
import string
import subprocess
import sys
import textwrap

MODS = {"sizing_recipe", "topology_library", "design_report"}
SD, ACF = "stick_diagram", "audit_current_forced"
DROP_MODS = (SD, ACF)
IMPF = ("import_module", "_import", "__import__")
ATTRF = ("getattr", "hasattr", "setattr", "delattr")
EXECF = ("exec", "eval", "compile")
WRITEF = ("write_text", "write")
G = []


def git(*a):
    r = subprocess.run(G + list(a), capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def fname(e):
    f = e.func
    return f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")


def e3_hits(tree):   # design §10 E3_AST 식 그대로
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] in MODS for a in n.names):
            out.append(("stmt", n.lineno))
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module and n.module.split(".")[0] in MODS:
            out.append(("stmt", n.lineno))
        elif isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
            if fname(n) in IMPF and n.args[0].value.split(".")[0] in MODS:
                out.append(("call", n.lineno))
    return out


def file_reads(tree, mod=SD):   # design §10 E3B_AST file_reads 그대로(모듈 이름 자리만 매개 -- 계약 1 (b) 'ACF에도 같은 식', m1)
    al, fn_sd = set(), set()

    def is_sd(e):
        if isinstance(e, ast.Name):
            return e.id in al
        if isinstance(e, ast.Call):
            f = e.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if nm in IMPF and e.args and isinstance(e.args[0], ast.Constant) and e.args[0].value == mod:
                return True
            return isinstance(f, ast.Name) and f.id in fn_sd
        return False
    ch = True
    while ch:
        ch = False
        for n in ast.walk(tree):
            new = set()
            if isinstance(n, ast.Import):
                new = {a.asname or a.name for a in n.names if a.name == mod}
            elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and n.value is not None and is_sd(n.value):
                tg = n.targets if isinstance(n, ast.Assign) else [n.target]
                new = {t.id for t in tg if isinstance(t, ast.Name)}
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name not in fn_sd and any(
                    isinstance(r, ast.Return) and r.value is not None and is_sd(r.value) for r in ast.walk(n)):
                fn_sd.add(n.name)
                ch = True
            if new - al:
                al |= new
                ch = True
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module == mod:
            out |= {(n.lineno, a.name) for a in n.names}
        elif isinstance(n, ast.Attribute) and is_sd(n.value):
            out.add((n.lineno, n.attr))
        elif isinstance(n, ast.Call) and n.args and is_sd(n.args[0]) and fname(n) in ATTRF:
            a = n.args[1] if len(n.args) > 1 else None
            out.add((n.lineno, a.value if isinstance(a, ast.Constant) and isinstance(a.value, str) else "<동적 이름>"))
    return out


def docstring_ids(tree):
    ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            s = n.body[0]
            if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str):
                ids.add(id(s.value))
    return ids


def _parse_text(t):
    """(파싱된 원문, 트리) -- `ast.parse` 실패 시 `textwrap.dedent` 뒤 한 번 더. 실패면 (t, None)."""
    for c in (t, textwrap.dedent(t)):
        try:
            return c, ast.parse(c)
        except (SyntaxError, ValueError):
            continue
    return t, None


def parse_embedded(s):
    return _parse_text(s)[1]


STRM = ("format", "format_map", "replace", "strip", "lstrip", "rstrip")   # 감싼 자리: 이 메서드의 수신자(문자열)를 따라간다
STRF = ("dedent", "str")                                                  # 감싼 자리: 이 함수(이름·속성 호출)의 첫 위치 인자를 따라간다
PYOPT_ARG = ("-W", "-X")                                                   # 인터프리터 옵션 중 다음 원소를 값으로 먹는 것


def _interp_names(tree):
    """인터프리터를 가리키는 이름(파일 안 어느 스코프든 -- 닫힌 쪽): `sys.executable`·`python*` 상수·그런 이름을 대입받은 이름(고정점),
    `from sys import executable [as x]`."""
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "sys":
            names |= {a.asname or a.name for a in n.names if a.name == "executable"}
    grew = True
    while grew:
        grew = False
        for n in ast.walk(tree):
            if isinstance(n, (ast.Assign, ast.AnnAssign)) and getattr(n, "value", None) is not None and _is_interp(n.value, names):
                for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                    if isinstance(t, ast.Name) and t.id not in names:
                        names.add(t.id)
                        grew = True
    return names


def _is_interp(e, names):
    if isinstance(e, ast.Attribute) and e.attr == "executable" and isinstance(e.value, ast.Name) and e.value.id == "sys":
        return True
    if isinstance(e, ast.Name):
        return e.id in names
    if isinstance(e, ast.Constant) and isinstance(e.value, str):
        return e.value.replace("\\", "/").rsplit("/", 1)[-1].lower().startswith("python")
    if isinstance(e, ast.BoolOp):   # `sys.executable or "python"`
        return any(_is_interp(v, names) for v in e.values)
    return False


def _py_c_arg(elts, names):
    """(s2) 리스트·튜플 표시: 첫 원소가 인터프리터면 인터프리터 옵션 구간의 `"-c"` 바로 뒤 원소. 옵션 구간은 상수 `"-m"`이나
    `-`로 시작하지 않는 상수(스크립트 경로·`-` 표준 입력)에서 끝난다(그 뒤 `-c`는 모듈·스크립트의 인자 -- `pytest -c` 등).
    상수가 아닌 원소·`*펼침`은 구간을 끝내지 않는다(닫힌 쪽). `-W`·`-X`는 다음 원소를 값으로 먹는다."""
    if not elts or not _is_interp(elts[0], names):
        return None
    i = 1
    while i < len(elts):
        e = elts[i]
        if isinstance(e, ast.Constant) and isinstance(e.value, str):
            if e.value == "-c":
                return elts[i + 1] if i + 1 < len(elts) else None
            if e.value == "-m" or not e.value.startswith("-") or e.value == "-":
                return None
            if e.value in PYOPT_ARG:
                i += 1
        i += 1
    return None


def _leaves(e, tm=None, fnode=None):
    """(잎 식, tmpl, 채움 노드) -- ④ `+` 양쪽, w1 `%` 왼쪽(tmpl percent, 채움 노드 = 그 BinOp),
    w2 STRM 메서드 수신자(format·format_map이면 tmpl format, 채움 노드 = 그 호출), w3 STRF 첫 인자. 바깥 템플릿이 먼저 정해지면 유지한다."""
    if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Add):
        return _leaves(e.left, tm, fnode) + _leaves(e.right, tm, fnode)
    if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Mod):
        return _leaves(e.left, tm or "percent", fnode if tm else e)
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr in STRM:
        if not tm and e.func.attr in ("format", "format_map"):
            return _leaves(e.func.value, "format", e)
        return _leaves(e.func.value, tm, fnode)
    if isinstance(e, ast.Call) and fname(e) in STRF and e.args:
        return _leaves(e.args[0], tm, fnode)
    return [(e, tm, fnode)]


def _parent_map(tree):
    par = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            par[id(c)] = n
    return par


def _param_kind(nm_node, par):
    """이름 잎이 둘러싼 함수(안쪽부터)의 매개변수면 (종류, 함수 노드, 위치, 키워드 이름), 아니면 None.
    종류: pos(보통 함수의 위치 매개변수 -- ③), method(클래스 본문 바로 아래 def의 매개변수), kwonly, vararg(`*`/`**`), lambda."""
    nm, n = nm_node.id, nm_node
    while id(n) in par:
        n = par[id(n)]
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        a = n.args
        pos = [x.arg for x in a.posonlyargs + a.args]
        kwo = [x.arg for x in a.kwonlyargs]
        var = [x.arg for x in (a.vararg, a.kwarg) if x is not None]
        if nm not in pos and nm not in kwo and nm not in var:
            continue
        if isinstance(n, ast.Lambda):
            return ("lambda", n, None, None)
        if isinstance(par.get(id(n)), ast.ClassDef):
            return ("method", n, None, None)
        if nm in pos:
            i = pos.index(nm)
            return ("pos", n, i, nm if i >= len(a.posonlyargs) else None)
        return ("kwonly" if nm in kwo else "vararg", n, None, None)
    return None


def exec_strings_ex(tree):
    """실행 문자열(계약 1 (e) 문언 -- 실행 자리 s1~s3, 닿음 ①~③, 감싼 식 w1~w3·`+`).
    돌려줌: (hit, meta, unresolved)
      hit[id(상수)] = 사람이 읽는 경로 문자열(첫 경로)
      meta[id(상수)] = {"base": {s1|s2|s3}, "tmpl": {None|"format"|"percent"}, "fills": {(tmpl, 채움 값 튜플)}} -- 모든 경로의 합
      unresolved = [(자리 줄, 자리 종류, 식 모양, kind)] -- kind: outside·method·kwonly·vararg·lambda·partial(규칙 밖 기록), stop_fstring(멈춤)."""
    par = _parent_map(tree)
    assigns = {}   # 이름 -> [대입값 식] (② -- 파일 안 모든 대입문, 스코프 무관)
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    assigns.setdefault(t.id, []).append(n.value)
        elif isinstance(n, ast.AnnAssign) and n.value is not None and isinstance(n.target, ast.Name):
            assigns.setdefault(n.target.id, []).append(n.value)
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            # `X += v` = `X = X + v`: v를 같은 풀이로. 다른 연산(`%=` 등)은 규칙 밖 잎(그 문 자체)
            assigns.setdefault(n.target.id, []).append(n.value if isinstance(n.op, ast.Add) else n)
    inames = _interp_names(tree)
    rcache = {}

    def resolve(e, tm, fnode):
        """자리 식 -> [(kind, 잎, tmpl, 채움 노드, 매개변수 종류, 자리 줄)] (자리 식 단위 캐시 -- sink_params와 무관)."""
        key = (id(e), tm, id(fnode))
        if key in rcache:
            return rcache[key]
        out = []

        def go(x, tm_, fn_, seen, top):
            for lf, t2, f2 in _leaves(x, tm_, fn_):
                ln = top if top is not None else getattr(lf, "lineno", getattr(e, "lineno", 0))
                if isinstance(lf, ast.Constant) and isinstance(lf.value, str):
                    out.append(("const", lf, t2, f2, None, ln))
                elif isinstance(lf, ast.JoinedStr):
                    out.append(("fstring", lf, t2, f2, None, ln))
                elif isinstance(lf, ast.Name):
                    pk = _param_kind(lf, par)
                    if pk:
                        out.append(("param", lf, t2, f2, pk, ln))
                    vals = assigns.get(lf.id, [])
                    if lf.id not in seen:
                        for v in vals:
                            go(v, t2, f2, seen | {lf.id}, ln)
                    if pk is None and not vals:
                        out.append(("outside", lf, t2, f2, None, ln))
                else:
                    out.append(("outside", lf, t2, f2, None, ln))
        go(e, tm, fnode, frozenset(), None)
        rcache[key] = out
        return out

    sink_params = {}   # 보통 함수 이름 -> {(위치, 키워드 이름, base, tmpl, 채움 노드)}
    partial_sites = []

    def sinks():
        out = []   # (식, base, tmpl, 채움 노드, 경로 이름)
        del partial_sites[:]
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                fn = fname(n)
                if n.args and isinstance(n.func, ast.Name) and fn in EXECF:   # 내장 exec/eval/compile만(`re.compile` 등 속성 호출은 아니다)
                    out.append((n.args[0], "s1", None, None, "exec"))
                elif n.args and fn in WRITEF:
                    out.append((n.args[0], "s3", None, None, "write"))
                if isinstance(n.func, ast.Name) and n.func.id in sink_params:   # ③ 이름 호출만(메서드·속성 호출은 아니다)
                    for pos, kw, base, tm, fnode in sink_params[n.func.id]:
                        args = []
                        if pos is not None:
                            star = [a for a in n.args[:pos + 1] if isinstance(a, ast.Starred)]
                            if star:
                                args.append(star[0])   # 위치를 알 수 없음 -> 규칙 밖 잎
                            elif pos < len(n.args):
                                args.append(n.args[pos])
                        args += [k.value for k in n.keywords if kw is not None and k.arg == kw]
                        for a in args:
                            out.append((a, base, tm, fnode, "param:" + n.func.id))
                if fn == "partial" and n.args and isinstance(n.args[0], ast.Name) and n.args[0].id in sink_params:
                    partial_sites.append(n)
            if isinstance(n, (ast.List, ast.Tuple)):
                a = _py_c_arg(n.elts, inames)
                if a is not None:
                    out.append((a, "s2", None, None, "-c"))
        return out
    grew = True
    while grew:   # ③ 고정점 -- 자리 종류(base)·템플릿 여부·채움 노드를 함께 넘긴다
        grew = False
        for e, base, tm, fnode, _r in sinks():
            for kind, lf, t2, f2, pk, _ln in resolve(e, tm, fnode):
                if kind == "param" and pk[0] == "pos":
                    ent = sink_params.setdefault(pk[1].name, set())
                    k = (pk[2], pk[3], base, t2, f2)
                    if k not in ent:
                        ent.add(k)
                        grew = True
    hit, meta, unresolved = {}, {}, []
    for e, base, tm, fnode, route in sinks():
        for kind, lf, t2, f2, pk, ln in resolve(e, tm, fnode):
            if kind == "const":
                fill = _fill_values(lf.value, t2, f2)
                # (s3) 파일 쓰기 자리는 어느 경로로 닿든 스크립트 모양인 문자열만 -- 출력·기록 문자열 제외
                if base == "s3" and not script_shaped(lf.value, t2, fill):
                    continue
                hit.setdefault(id(lf), route + (" tmpl:" + t2 if t2 else ""))
                m = meta.setdefault(id(lf), {"base": set(), "tmpl": set(), "fills": set(), "fpos": {}})
                m["base"].add(base)
                m["tmpl"].add(t2)
                m["fills"].add((t2, fill))
                # b1fix4(review_p3_f1_b1fix3 minor 3): 판 순서 = 채움 경로의 채움 자리(format·format_map 호출·`%` 식)의 소스 위치(줄, 열)
                if f2 is not None:
                    pos = (f2.lineno, f2.col_offset)
                    m["fpos"][(t2, fill)] = min(m["fpos"].get((t2, fill), pos), pos)
            elif base == "s3":
                continue
            elif kind == "fstring":
                unresolved.append((ln, route, "JoinedStr", "stop_fstring"))
            elif kind == "param":
                if pk[0] != "pos":
                    unresolved.append((ln, route, "Name:" + lf.id, pk[0]))
            else:
                unresolved.append((ln, route, type(lf).__name__ + (":" + lf.id if isinstance(lf, ast.Name) else ""), "outside"))
    for n in partial_sites:
        unresolved.append((n.lineno, "partial", "partial:" + n.args[0].id, "partial"))
    return hit, meta, sorted(set(unresolved))


def exec_strings(tree):
    """실행 문자열 상수 노드 id -> 경로."""
    return exec_strings_ex(tree)[0]


_PCT = re.compile(r"%(?:\(([^)]*)\))?[-#0 +]*(?:\*|\d+)?(?:\.(?:\*|\d+))?[hlL]?([diouxXeEfFgGcrsa%])")
_SLOT = re.compile(r"__f12_fmt_(\d+)__")


def fill_template(s, tm, override=None):
    """템플릿 자리표시자를 나오는 순서대로 식별자 `__f12_fmt_<k>__`로 채운다(format: 치환 필드, percent: %-지정자; `{{`·`%%`는 글자 하나로).
    override[k]가 있으면 그 자리는 그 값으로 채운다(m4). 채울 수 없으면(형식 오류) None."""
    if tm is None:
        return s
    out, k = [], 0
    ov = override or {}
    try:
        if tm == "format":
            for lit, field, _spec, _conv in string.Formatter().parse(s):
                out.append(lit)
                if field is not None:
                    out.append(ov.get(k, "__f12_fmt_%d__" % k))
                    k += 1
            return "".join(out)
        pos = 0
        for m in _PCT.finditer(s):
            out.append(s[pos:m.start()])
            if m.group(2) == "%":
                out.append("%")
            else:
                out.append(ov.get(k, "__f12_fmt_%d__" % k))
                k += 1
            pos = m.end()
        out.append(s[pos:])
        return "".join(out)
    except ValueError:
        return None


def _str_const(e):
    return e.value if isinstance(e, ast.Constant) and isinstance(e.value, str) else None


def _fill_values(s, tm, node):
    """템플릿 경로의 자리표시자마다 그 호출 자리의 인자가 문자열 상수면 그 값, 아니면 None(튜플, 자리표시자 순서). 템플릿 아니면 ()."""
    if tm is None or node is None:
        return ()
    vals = []
    try:
        if tm == "format":
            if not isinstance(node, ast.Call):
                return ()
            if node.func.attr == "format_map":
                d = node.args[0] if node.args else None
                kw = {_str_const(k): v for k, v in zip(d.keys, d.values) if k is not None and _str_const(k)} if isinstance(d, ast.Dict) else {}
                pa, star = [], True
            else:
                kw = {k.arg: k.value for k in node.keywords if k.arg}
                pa, star = node.args, any(k.arg is None for k in node.keywords)
            auto = 0
            for _lit, field, spec, conv in string.Formatter().parse(s):
                if field is None:
                    continue
                v = None
                key = field
                if field == "":
                    key, auto = auto, auto + 1
                elif field.isdigit():
                    key = int(field)
                if not spec and conv in (None, "s"):
                    if isinstance(key, int):
                        if key < len(pa) and not any(isinstance(a, ast.Starred) for a in pa[:key + 1]):
                            v = _str_const(pa[key])
                    elif key.isidentifier() and key in kw:
                        v = _str_const(kw[key])
                    elif key.isidentifier() and not star:
                        v = None
                vals.append(v)
            return tuple(vals)
        right = node.right if isinstance(node, ast.BinOp) else None
        j = 0
        for m in _PCT.finditer(s):
            if m.group(2) == "%":
                continue
            v = None
            if m.group(2) == "s":
                if m.group(1) is not None:
                    if isinstance(right, ast.Dict):
                        for k, x in zip(right.keys, right.values):
                            if k is not None and _str_const(k) == m.group(1):
                                v = _str_const(x)
                elif isinstance(right, ast.Tuple):
                    if j < len(right.elts) and not any(isinstance(a, ast.Starred) for a in right.elts[:j + 1]):
                        v = _str_const(right.elts[j])
                elif j == 0:
                    v = _str_const(right)
            if m.group(1) is None:
                j += 1
            vals.append(v)
        return tuple(vals)
    except (ValueError, AttributeError):
        return ()


def _import_slots(tree):
    """[(줄, 자리 글자)] -- 자리표시자가 import 모듈 자리(import 문 모듈 이름, import 호출 첫 인자 상수)에 온 곳."""
    out = []
    for x in ast.walk(tree):
        if isinstance(x, ast.Import):
            out += [(x.lineno, a.name) for a in x.names if "__f12_fmt_" in a.name]
        elif isinstance(x, ast.ImportFrom) and x.module and "__f12_fmt_" in x.module:
            out.append((x.lineno, x.module))
        elif isinstance(x, ast.Call) and fname(x) in IMPF and x.args and _str_const(x.args[0]) and "__f12_fmt_" in x.args[0].value:
            out.append((x.lineno, x.args[0].value))
    return out


def dynamic_import_slots(tree):
    """채운 뒤에도 자리표시자가 남은 import 모듈 자리(동적 모듈 -- 판정 기록에 자리만 적는다)."""
    return _import_slots(tree)


def fill_parse(s, tm, fill=()):
    """한 경로의 내장 파일 (원문, 트리|None): 템플릿 아니면 원문 그대로. 템플릿이면 자리표시자를 식별자로 채워 파싱하고,
    import 모듈 자리의 자리표시자 중 그 경로 인자가 문자열 상수인 것은 그 값으로 채워 다시 파싱한다(m4)."""
    if tm is None:
        return _parse_text(s)
    t = fill_template(s, tm)
    if t is None:
        return s, None
    text, tree = _parse_text(t)
    if tree is None:
        return text, None
    ks = {int(k) for _l, nm in _import_slots(tree) for k in _SLOT.findall(nm)}
    sub = {k: fill[k] for k in ks if k < len(fill) and fill[k] is not None}
    if not sub:
        return text, tree
    return _parse_text(fill_template(s, tm, sub))


def exec_texts(s, m):
    """실행 문자열의 내장 파일 목록 [(원문, 트리|None)]: 템플릿이 아닌 경로가 있으면 원문 하나, 템플릿으로만 닿으면 경로(채움)마다(같은 원문은 하나).
    b1fix4(review_p3_f1_b1fix3 minor 3 -- 계약 1 (e)·3 (사) `.v<j>`): 판 순서 = 채움 경로의 채움 자리 소스 위치(줄, 열) 순서,
    같은 원문이 여러 경로에서 나오면 첫 자리의 판 하나(옛 판은 repr 순서 -- 소스 순서와 무관했다)."""
    if m is None or None in m["tmpl"]:
        return [_parse_text(s)]
    out, seen = [], set()
    fpos = m.get("fpos", {})
    for tm, fill in sorted((x for x in m["fills"] if x[0]), key=lambda x: (fpos.get(x, (0, 0)), repr(x))):
        text, tree = fill_parse(s, tm, fill)
        if text not in seen:
            seen.add(text)
            out.append((text, tree))
    return out


def script_shaped(s, tm=None, fill=()):
    t = fill_parse(s, tm, fill)[1]
    return t is not None and any(isinstance(x, (ast.Import, ast.ImportFrom)) for x in ast.walk(t))


IMPORT_LINE = re.compile(r"^\s*(?:import\s+[A-Za-z_{]|from\s+[A-Za-z_.{]+\s+import\b)", re.M)


def scan_tree(tree, drop=None):
    """파일 하나의 전수 결과(main과 selftest가 같이 쓴다). drop = {모듈: 삭제 집합 이름}."""
    drop = drop or {}
    res = {"exec": [], "content_only": [], "parse_fail": [], "unresolved_sink": [], "stop_fstring": [], "content_only_unparsed": []}
    docs = docstring_ids(tree)
    hit, meta, unres = exec_strings_ex(tree)
    for ln, route, shape, kind in unres:
        res["stop_fstring" if kind == "stop_fstring" else "unresolved_sink"].append({"line": ln, "sink": route, "expr": shape, "kind": kind})
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)) or id(n) in docs:
            continue
        is_exec = id(n) in hit
        if is_exec:
            variants = exec_texts(n.value, meta[id(n)])
        elif "import" in n.value:
            variants = [_parse_text(n.value)]
        else:
            variants = []
        subs = [t for _x, t in variants if t is not None]
        has_imp = any(isinstance(x, (ast.Import, ast.ImportFrom)) for t in subs for x in ast.walk(t))
        if not is_exec and not has_imp:
            if not subs and "import" in n.value and IMPORT_LINE.search(n.value):
                res["content_only_unparsed"].append({"line": n.lineno, "len": len(n.value),
                                                     "engine": sorted(m for m in MODS | set(DROP_MODS) if m in n.value)})
            continue
        ok = bool(variants) and all(t is not None for _x, t in variants)
        ent = {"line": n.lineno, "len": len(n.value), "sink": hit.get(id(n)), "parses": ok}
        if is_exec:
            ent["base"] = sorted(meta[id(n)]["base"])
            ent["tmpl"] = sorted(t for t in meta[id(n)]["tmpl"] if t)
            if len(variants) > 1:
                ent["variants"] = len(variants)
            if not ok:
                res["parse_fail"].append({"line": n.lineno, "sink": ent["sink"]})
        if subs:
            e3, reads, imps, dyn = set(), {m: set() for m in DROP_MODS}, set(), set()
            for t in subs:
                e3 |= set(e3_hits(t))
                for m in DROP_MODS:
                    reads[m] |= file_reads(t, m)
                imps |= {(a.name if isinstance(x, ast.Import) else (x.module or ".")) for x in ast.walk(t)
                         if isinstance(x, (ast.Import, ast.ImportFrom)) for a in (x.names if isinstance(x, ast.Import) else [x])}
                dyn |= set(dynamic_import_slots(t))
            ent["e3"] = sorted(e3)
            ent["sd_reads"] = len(reads[SD])
            ent["acf_reads"] = len(reads[ACF])
            ent["sd_drop_reads"] = sorted({nm for _l, nm in reads[SD] if nm in drop.get(SD, ())})
            ent["acf_drop_reads"] = sorted({nm for _l, nm in reads[ACF] if nm in drop.get(ACF, ())})
            ent["imports"] = sorted(imps)
            if dyn:
                ent["dynamic_import"] = sorted(dyn)
        (res["exec"] if is_exec else res["content_only"]).append(ent)
    return res


def _load_list(p):
    return set(json.load(open(p, encoding="utf-8")))


def main():
    global G
    ROOT, REV, OUT = sys.argv[1:4]
    drop = {}
    if "--drop" in sys.argv:
        drop[SD] = _load_list(sys.argv[sys.argv.index("--drop") + 1])
    if "--drop-acf" in sys.argv:
        drop[ACF] = _load_list(sys.argv[sys.argv.index("--drop-acf") + 1])
    G = ["git", "-c", "core.quotepath=off", "-C", ROOT]
    res = {"rev": REV, "files_scanned": 0, "drop_sizes": {m: len(v) for m, v in drop.items()}, "exec": [], "content_only": [],
           "parse_error": [], "parse_fail": [], "unresolved_sink": [], "stop_fstring": [], "content_only_unparsed": []}
    paths = [p for p in git("ls-tree", "-r", "--name-only", "-z", REV).decode("utf-8").split("\0") if p.endswith(".py")]
    for p in paths:
        src = git("show", REV + ":" + p)
        try:
            tree = ast.parse(src)
        except SyntaxError:
            res["parse_error"].append(p)
            continue
        res["files_scanned"] += 1
        r = scan_tree(tree, drop)
        for k, v in r.items():
            res[k] += [dict(path=p, **x) for x in v]
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    d9 = lambda x: not x["path"].startswith(".ai/verification/")   # noqa: E731 -- D-9 밖
    sites = {(x["path"], x["line"]) for x in res["unresolved_sink"]}
    print(json.dumps({"files": res["files_scanned"], "exec": len(res["exec"]), "exec_d9_out": len([x for x in res["exec"] if d9(x)]),
                      "exec_base": {b: len([x for x in res["exec"] if b in x["base"]]) for b in ("s1", "s2", "s3")},
                      "content_only": len(res["content_only"]), "parse_fail": len(res["parse_fail"]),
                      "stop_fstring": len(res["stop_fstring"]),
                      "outside_sites": len(sites), "outside_sites_d9_out": len({s for s in sites if not s[0].startswith(".ai/verification/")}),
                      "outside_files_d9_out": len({s[0] for s in sites if not s[0].startswith(".ai/verification/")}),
                      "outside_kinds": {k: len([x for x in res["unresolved_sink"] if x["kind"] == k]) for k in
                                        sorted({x["kind"] for x in res["unresolved_sink"]})},
                      "content_only_unparsed": len(res["content_only_unparsed"]),
                      "exec_with_e3_or_drop": [(x["path"], x["line"], len(x.get("e3", [])), len(x.get("sd_drop_reads", [])),
                                                len(x.get("acf_drop_reads", []))) for x in res["exec"]
                                               if x.get("e3") or x.get("sd_drop_reads") or x.get("acf_drop_reads")],
                      "content_only_engine": [(x["path"], x["line"], x.get("imports")) for x in res["content_only"]
                                              if set(x.get("imports", [])) & (MODS | set(DROP_MODS))]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
