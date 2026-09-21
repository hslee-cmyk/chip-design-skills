"""10-test-separation design 부록 A의 계수 스크립트(분석 부산물, 판정 도구 아님).

인라인 self-test 블록(`if __name__ == "__main__":`)을 AST로 읽어 섹션 경계, 섹션별 판정 형태,
섹션 사이 이름 의존(사슬), 블록이 읽는 모듈 이름(명시 import 목록 후보)을 센다.

섹션 경계 규칙(design §5.1과 같다):
  * 블록 최상위 문장 중 `print(<문자열>)`의 정적 머리 텍스트가
      - "# " 또는 "=== " 로 시작하면 **대 표지**(연속한 대 표지 print는 하나로 합친다)
      - "  [" 로 시작하고 괄호 안 첫 낱말이 PASS/FAIL/OK/SKIP/불가가 아니면 **소 표지**
  * 섹션 = 표지(대 또는 소)부터 다음 표지 앞까지. 첫 표지 앞 문장은 '머리'(prelude)다.

출력: 같은 디렉터리의 selftest_sections.json(전체)과 selftest_sections.md(표). 실행마다 덮어쓴다.
사용: C:/Python314/python.exe count_selftest_sections.py <저장소 루트>
"""
from __future__ import annotations

import ast
import builtins
import json
import re
import subprocess
import sys
from pathlib import Path

FILES = ["sizing_recipe.py", "stick_diagram.py", "design_report.py", "topology_library.py",
         "audit_current_forced.py", "sky130_lut_sweep.py", "topology_to_markdown.py"]
ASSETS = Path("skills/analog-gmid-design/assets")
TOKEN = re.compile(r"(?<![A-Za-z])(PASS|FAIL)(?![A-Za-z])")
SUB_EXCLUDE = re.compile(r"^  \[\s*(PASS|FAIL|OK|SKIP|불가)")
BUILTINS = set(dir(builtins)) | {"__file__", "__name__"}


def static_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = []
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                out.append(v.value)
            else:
                out.append("{}")
        return "".join(out)
    return None


def all_strings(node: ast.AST) -> list[str]:
    """문자열 `Constant` 노드마다 한 번(f-string은 그 안의 `Constant` 조각만 -- JoinedStr 자체를 다시 세지 않는다, review1 S2-1)."""
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def is_print(stmt: ast.stmt) -> ast.Call | None:
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        f = stmt.value.func
        if isinstance(f, ast.Name) and f.id == "print":
            return stmt.value
    return None


def header_kind(stmt: ast.stmt) -> tuple[str, str] | None:
    call = is_print(stmt)
    if call is None or not call.args:
        return None
    t = static_text(call.args[0])
    if t is None:
        return None
    if t.startswith("# ") or t.startswith("=== "):
        return "major", t
    if t.startswith("  [") and not SUB_EXCLUDE.match(t):
        return "sub", t
    return None


def main_block(tree: ast.Module) -> ast.If | None:
    for n in tree.body:
        if isinstance(n, ast.If):
            s = ast.unparse(n.test).replace("'", '"')
            if s == '__name__ == "__main__"':
                return n
    return None


def verdict_print_count(node: ast.AST) -> int:
    """print(...) 또는 logging.*(...) 인자 안 PASS/FAIL 토큰 개수(TS3 AST 검사와 같은 식)."""
    c = 0
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            base = f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else ""
            if name == "print" or base in ("logging", "logger", "log"):
                for a in list(n.args) + [k.value for k in n.keywords]:
                    for s in all_strings(a):
                        c += len(TOKEN.findall(s))
    return c


def rejection_try_count(node: ast.AST) -> int:
    """try 본문에 `raise AssertionError`가 있고 except 핸들러가 있는 형태(거부 케이스 -> pytest.raises 후보)."""
    c = 0
    for n in ast.walk(node):
        if isinstance(n, ast.Try) and n.handlers:
            for b in n.body:
                for m in ast.walk(b):
                    if isinstance(m, ast.Raise) and m.exc is not None:
                        e = m.exc.func if isinstance(m.exc, ast.Call) else m.exc
                        if isinstance(e, ast.Name) and e.id == "AssertionError":
                            c += 1
                            break
    return c


def analyze(path: Path) -> dict:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    blk = main_block(tree)
    res = {"file": path.name, "lines_total": len(src.splitlines())}
    if blk is None:
        res["main_block"] = None
        return res
    body = blk.body
    res["main_block"] = {"start": blk.lineno, "end": blk.end_lineno,
                         "lines": blk.end_lineno - blk.lineno + 1,
                         "uses_sys_argv": "sys.argv" in ast.unparse(blk)}
    module_defs = set()
    for n in tree.body:
        if n is blk:
            continue
        for m in ast.walk(n) if isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)) else [n]:
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                module_defs.add(m.name)
            elif isinstance(m, ast.Name) and isinstance(m.ctx, ast.Store):
                module_defs.add(m.id)
            elif isinstance(m, ast.alias):
                module_defs.add((m.asname or m.name).split(".")[0])
    # 섹션 나누기
    sections, cur = [], {"kind": "prelude", "title": "(머리)", "stmts": []}
    prev_major = False
    for st in body:
        hk = header_kind(st)
        if hk and hk[0] == "major" and prev_major and cur["kind"] == "major" and \
                all(header_kind(s) for s in cur["stmts"]):
            cur["stmts"].append(st)
            continue
        if hk:
            if cur["stmts"]:
                sections.append(cur)
            cur = {"kind": hk[0], "title": hk[1].strip()[:70], "stmts": [st]}
            prev_major = hk[0] == "major"
        else:
            cur["stmts"].append(st)
            prev_major = False
    if cur["stmts"]:
        sections.append(cur)
    # 이름 저장 위치(블록 안, 줄 기준)
    stores: dict[str, list[int]] = {}
    for n in ast.walk(blk):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            stores.setdefault(n.id, []).append(n.lineno)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            stores.setdefault(n.name, []).append(n.lineno)
        elif isinstance(n, ast.alias):
            stores.setdefault((n.asname or n.name).split(".")[0], []).append(n.lineno)
        elif isinstance(n, ast.arg):
            stores.setdefault(n.arg, []).append(n.lineno)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            stores.setdefault(n.name, []).append(n.lineno)
    sec_of_line = []
    for i, s in enumerate(sections):
        s["start"] = s["stmts"][0].lineno
        s["end"] = s["stmts"][-1].end_lineno
        sec_of_line.append((s["start"], s["end"], i))

    def sec_idx(line: int) -> int | None:
        for a, b, i in sec_of_line:
            if a <= line <= b:
                return i
        return None

    module_used = set()
    for i, s in enumerate(sections):
        deps, asserts, raises_ae = set(), 0, 0
        for st in s["stmts"]:
            for n in ast.walk(st):
                if isinstance(n, ast.Assert):
                    asserts += 1
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                    ls = [l for l in stores.get(n.id, []) if l < n.lineno]
                    if ls:
                        j = sec_idx(max(ls))
                        if j is not None and j < i:
                            deps.add((n.id, j))
                    elif n.id not in stores and n.id not in BUILTINS:
                        module_used.add(n.id)
                    elif n.id in stores and not ls and n.id not in BUILTINS:
                        # 뒤에서 정의된 이름(중첩 함수 안 참조 등): 모듈 이름일 수 있다
                        if n.id in module_defs:
                            module_used.add(n.id)
        s["asserts"] = asserts
        s["reject_try"] = rejection_try_count(ast.Module(body=s["stmts"], type_ignores=[]))
        s["verdict_prints"] = verdict_print_count(ast.Module(body=s["stmts"], type_ignores=[]))
        s["deps"] = sorted({f"{nm}<-S{j}" for nm, j in deps})
        s["dep_sections"] = sorted({j for _, j in deps})
        s["reads_lut"] = any(nm == "lut" for nm, _ in deps)
        s["uses_drl_case"] = "_drl_case" in ast.unparse(ast.Module(body=s["stmts"], type_ignores=[]))
        s["uses_file"] = "__file__" in ast.unparse(ast.Module(body=s["stmts"], type_ignores=[]))
        mod = ast.Module(body=s["stmts"], type_ignores=[])
        s["raise_assertion"] = sum(1 for n in ast.walk(mod) if isinstance(n, ast.Raise) and n.exc is not None
                                   and isinstance(n.exc.func if isinstance(n.exc, ast.Call) else n.exc, ast.Name)
                                   and (n.exc.func if isinstance(n.exc, ast.Call) else n.exc).id == "AssertionError")
        only_static_prints = all(
            is_print(st) is not None and all(static_text(a) is not None and "{}" not in (static_text(a) or "")
                                              for a in is_print(st).args)
            for st in s["stmts"])
        if s["kind"] == "prelude":
            s["category"] = "P"
        elif only_static_prints:
            s["category"] = "D"
        elif s["asserts"] > 0 or s["raise_assertion"] > 0:
            s["category"] = "A"
        elif s["verdict_prints"] > 0:
            s["category"] = "B"
        else:
            s["category"] = "C"
        s["judged"] = s["category"] in ("A", "B")
        del s["stmts"]
    for i, s in enumerate(sections):
        s["provides_to"] = sorted({j for j, t in enumerate(sections) if i in t["dep_sections"]})
    res["sections"] = sections
    res["module_names_read"] = sorted(module_used & module_defs)
    res["unresolved_names_read"] = sorted(module_used - module_defs)
    return res


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()
    out = {"commit": head, "files": [analyze(root / ASSETS / f) for f in FILES]}
    here = Path(__file__).resolve().parent
    (here / "selftest_sections.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                 encoding="utf-8")
    md = [f"# self-test 섹션 계수 (commit {head})", ""]
    for f in out["files"]:
        mb = f.get("main_block")
        if not mb:
            md.append(f"## {f['file']} -- main 블록 없음\n")
            continue
        secs = f["sections"]
        md.append(f"## {f['file']} -- 블록 {mb['start']}~{mb['end']} ({mb['lines']}줄), sys.argv 사용 {mb['uses_sys_argv']}")
        md.append("")
        cat = {k: sum(1 for s in secs if s["category"] == k) for k in "PDABC"}
        md.append(f"섹션 {len(secs)}(머리 P 포함) / 범주 P {cat['P']} · D(표지만) {cat['D']} · A(assert·raise 판정) {cat['A']} · "
                  f"B(print 판정만) {cat['B']} · C(판정 없음) {cat['C']} / C 중 뒤 섹션이 의존 {sum(1 for s in secs if s['category']=='C' and s['provides_to'])} / "
                  f"assert {sum(s['asserts'] for s in secs)} / raise AssertionError {sum(s['raise_assertion'] for s in secs)} / "
                  f"거부 try {sum(s['reject_try'] for s in secs)} / print PASS·FAIL 토큰 {sum(s['verdict_prints'] for s in secs)} / "
                  f"앞 섹션 의존 섹션 {sum(1 for s in secs if s['dep_sections'])} / `lut` 읽는 섹션 {sum(s['reads_lut'] for s in secs)}")
        md.append(f"모듈 이름 읽음 {len(f['module_names_read'])}개, 미해결 이름 {f['unresolved_names_read']}")
        md.append("")
        md.append("| S | 종류 | 범주 | 줄 | 표지 | assert | raise AE | 거부 try | PASS/FAIL print | 앞 섹션 의존 | 뒤 섹션이 의존 |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for i, s in enumerate(secs):
            t = s["title"].replace("|", "\\|")
            md.append(f"| S{i} | {s['kind']} | {s['category']} | {s['start']}-{s['end']} | {t} | {s['asserts']} | {s['raise_assertion']} | {s['reject_try']} | "
                      f"{s['verdict_prints']} | {', '.join('S'+str(j) for j in s['dep_sections'])} | {len(s['provides_to'])} |")
        md.append("")
    (here / "selftest_sections.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"written: {here / 'selftest_sections.json'}, {here / 'selftest_sections.md'}")


if __name__ == "__main__":
    main()
