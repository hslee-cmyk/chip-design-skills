"""Phase 3 가벼운 이동 도구 -- 배정표대로 정의를 split 파일에서 MOD 파일로 바이트 그대로 옮긴다.

    python -B move.py <MODn | 파일 이름> [--root R] [--report out.json] [--dry-run] [--commit] [--strict-registry]

* 배정: 손으로 정하지 않는다. mp_core.compute_plan(= D0a plan 시제품, design 30 §6.2 규칙 A-0~A-7)이 계획 N3.10
  '대표 대상' 열과 레지스트리 '이관 목적지' 열에서 HEAD 기준으로 계산한다. 인자는 design 30 §6.3 MP_ARGS 그대로,
  문장 단위 키 = 바인딩 이름(D0a 계약 2 문언, MP_STMT_KEY=names).
* 고정(D-19): rail_declaration·RailDeclaration(B26-1 뒤 생김)은 MOD2. plan이 다른 값을 내면 고정값으로 바꾸고 보고에 남긴다.
* 멈춤(아무것도 쓰지 않음): plan의 upward·cycles·unassigned·conflicts·import_time_high가 비지 않음, 이 card MOD의
  import_conflicts가 비지 않음(예: __future__ 혼합 -- FU 전 M2·M9), card 파일이 이미 있음, mod_imports가 아직 없는
  N3.10 파일을 가리킴(순서 어김), 작업 트리의 대상 파일이 HEAD와 다름. reg_mismatch는 보고만(D0b 열 재생성을 버렸다,
  --strict-registry면 멈춤).
* MOD 파일 = plan.mod_imports[card](이름마다 import 한 번, D-30) + 단위 원본 줄(바로 위에 붙은 주석 줄 + 데코레이터 첫 줄 ~
  end_lineno) 바이트 그대로. 순서 = 원본 파일 위상 순서(TL → SD → SR → DR → ACF) 다음 원본 줄. 모듈 docstring 없음(W-3).
  card 번호 >= 8이면 번호 >= 7 N3.10 모듈 import 줄은 파일 끝(D-22 (2)).
* split 파일 = 단위 줄 삭제 + 명시 재수출 한 줄 `from <MOD 줄기> import <바인딩 이름 정렬>`(`_` 접두 포함, import * 없음)을
  앞머리 묶음(docstring 뒤 연속한 import·from·`sys.path.*` 식 문장)의 마지막 import 뒤에(W-2, 경로 설정 뒤면 `# noqa: E402`).
  stick_diagram이 MOD 8·9로 내보내면 파일 끝(D-22 (1)). N3.10·--keep 밖 파일이 단위 0이 되면 완전 shim(SHIM (b)):
  docstring + __future__ + N3.10 모듈 import 줄(앞 card 재수출과 base의 from stick_diagram 줄) + 새 재수출 줄.
* 줄 끝(CRLF/LF)은 파일마다 보존한다. tools/·tests/·그 밖 파일은 건드리지 않는다.
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("MP_STMT_KEY", "names")
import mp_core  # noqa: E402

A = mp_core.A
PLAN_DOC = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
REGISTRY = "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"
SPLIT = ["sizing_recipe.py", "stick_diagram.py", "topology_library.py", "design_report.py", "audit_current_forced.py"]
KEEP = ["audit_current_forced.py"]
ALIASES = {"optimizer": "theta_search.py"}
INIT_ORDER = ["topology_library.py", "stick_diagram.py", "sizing_recipe.py", "design_report.py", "audit_current_forced.py"]
PINS = {"rail_declaration": "topology_authoring.py", "RailDeclaration": "topology_authoring.py"}   # D-19 (가), A-2
BLOCKING = ("upward", "cycles", "unassigned", "conflicts", "import_time_high")


def die(msg, code=2):
    sys.stderr.write("move.py: " + msg + "\n")
    sys.exit(code)


def git(root, *args):
    r = subprocess.run(["git", "-C", root] + list(args), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")


class Src:
    """작업 트리 파일 한 개 -- 줄 목록(줄 끝 없이)과 줄 끝 모양."""

    def __init__(self, root, f):
        self.path = os.path.join(root, A, f)
        raw = open(self.path, "rb").read().decode("utf-8")
        self.nl = "\r\n" if "\r\n" in raw else "\n"
        text = raw.replace("\r\n", "\n")
        self.trailing_nl = text.endswith("\n")
        self.lines = text.split("\n")
        if self.trailing_nl:
            self.lines.pop()
        self.tree = ast.parse(text)
        self.covered = set()
        for n in self.tree.body:
            a = n.decorator_list[0].lineno if getattr(n, "decorator_list", None) else n.lineno
            self.covered |= set(range(a, n.end_lineno + 1))

    def write(self, lines):
        with open(self.path, "wb") as fh:
            fh.write((self.nl.join(lines) + (self.nl if self.trailing_nl else "")).encode("utf-8"))


def span(node, lines, covered=frozenset()):
    """(첫 줄, 끝 줄) 1-기반 -- 바로 위에 빈 줄 없이 붙은 주석 줄을 포함한다(다른 문장 범위 안의 줄은 제외)."""
    a = node.decorator_list[0].lineno if getattr(node, "decorator_list", None) else node.lineno
    while a > 1 and lines[a - 2].lstrip().startswith("#") and (a - 1) not in covered:
        a -= 1
    return a, node.end_lineno


def is_doc(tree, n):
    return (tree.body and n is tree.body[0] and isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
            and isinstance(n.value.value, str))


def is_syspath(n):
    if not isinstance(n, ast.Expr) or not isinstance(n.value, ast.Call):
        return False
    f = n.value.func
    while isinstance(f, ast.Attribute):
        if isinstance(f.value, ast.Attribute) and f.value.attr == "path" and isinstance(f.value.value, ast.Name) \
                and f.value.value.id == "sys":
            return True
        f = f.value
    return False


def head_end(tree):
    """앞머리 묶음(docstring 뒤 연속한 import·from·sys.path.* 식 문장)의 마지막 import 끝 줄, 그 앞에 경로 설정이 있었는지."""
    end, saw_path, path_before_end = 0, False, False
    for n in tree.body:
        if is_doc(tree, n):
            continue
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            end = n.end_lineno
            path_before_end = saw_path
            continue
        if is_syspath(n):
            saw_path = True
            continue
        break
    return end, path_before_end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("card")
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--report")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--strict-registry", action="store_true")
    ns = ap.parse_args()
    root = os.path.abspath(ns.root)

    il, rch, rp = mp_core.load_gates(root)
    modtab = il.mod_table(open(os.path.join(root, PLAN_DOC), encoding="utf-8").read())
    n310 = {s + ".py": k for s, k in modtab.items()}
    byk = {k: f for f, k in n310.items()}
    m = re.fullmatch(r"MOD([0-9]+)", ns.card)
    card = byk.get(int(m.group(1))) if m else (ns.card if ns.card.endswith(".py") else ns.card + ".py")
    if card not in n310:
        die("N3.10에 없는 card: %r" % ns.card)
    kc = n310[card]
    if os.path.exists(os.path.join(root, A, card)):
        die("card 파일이 이미 있다: %s" % card)
    rc, dirty = git(root, "status", "--porcelain", "--untracked-files=no", "--", A)
    if rc != 0 or any(l[3:].endswith(".py") for l in dirty.splitlines()):
        die("작업 트리의 assets .py가 HEAD와 다르다 -- 깨끗한 트리에서 돌린다:\n" + dirty)

    pns = argparse.Namespace(plan=PLAN_DOC, registry=REGISTRY, split=SPLIT, keep=KEEP)
    res, S = mp_core.compute_plan(root, "HEAD", pns, ALIASES, il, rch, rp)
    U = S["U"]
    pin_notes = []
    for uid, a in res["assignment"].items():
        for nm in U[uid]["bound"]:
            if nm in PINS and a["mod"] != PINS[nm]:
                pin_notes.append({"unit": uid, "plan": a["mod"], "pinned": PINS[nm]})
                a["mod"], a["rule"] = PINS[nm], "PIN-D19"
    stop = {k: res[k] for k in BLOCKING if res[k]}
    ic = [c for c in res["import_conflicts"] if c.get("mod") == card]
    if ic:
        stop["import_conflicts(card)"] = ic
    if ns.strict_registry and res["reg_mismatch"]:
        stop["reg_mismatch"] = res["reg_mismatch"]
    summary = {"card": card, "mod": kc, "plan_verdict": res["verdict"],
               "plan_lists": {k: len(res[k]) for k in BLOCKING + ("reg_mismatch", "import_conflicts")},
               "pins": pin_notes}
    if pin_notes and any(p["pinned"] == card or p["plan"] == card for p in pin_notes):
        # 고정값이 이 card의 단위 집합을 바꾸면 mod_imports도 plan과 달라진다 -- 손 배정 대신 멈추고 알린다
        stop["pin_changes_this_card"] = pin_notes
    if stop:
        print(json.dumps(dict(summary, stopped=stop), ensure_ascii=False, indent=1))
        die("plan 멈춤 조건 -- 아무것도 쓰지 않았다", 1)

    units = []
    for uid, a in res["assignment"].items():
        u = U[uid]
        if a["mod"] != card or u["file"] == card:
            continue
        units.append((u["file"], uid, u["node"], sorted(u["bound"]), a["rule"]))
    if not units:
        die("이 card로 가는 단위가 없다")
    srcs = {f: Src(root, f) for f in {x[0] for x in units}}
    for f, uid, node, b, r in units:                     # plan 노드와 작업 트리 파일이 같은 문장인지 확인
        lines = srcs[f].lines
        hit = [n for n in srcs[f].tree.body if n.lineno == node.lineno and ast.dump(n) == ast.dump(node)]
        if len(hit) != 1:
            die("작업 트리 %s의 단위 %s가 plan 노드와 다르다" % (f, uid))
    units.sort(key=lambda u: (INIT_ORDER.index(u[0]) if u[0] in INIT_ORDER else 99, span(u[2], srcs[u[0]].lines, srcs[u[0]].covered)[0]))

    # ---- MOD 파일
    head, tail, missing = [], [], []
    for line in res["mod_imports"].get(card, []):
        mod = line.split()[1].split(".")[0]
        if (mod + ".py") in n310 and mod + ".py" != card and not os.path.exists(os.path.join(root, A, mod + ".py")):
            missing.append(line)
        if kc >= 8 and (mod + ".py") in n310 and n310[mod + ".py"] >= 7 and not line.startswith("from __future__"):
            tail.append(line)
        else:
            head.append(line)
    if missing:
        die("mod_imports가 아직 없는 N3.10 파일을 가리킨다(앞 card 먼저): %s" % missing)
    out = list(head)
    for f, uid, node, b, r in units:
        a, e = span(node, srcs[f].lines, srcs[f].covered)
        if out:
            out += ["", ""]
        out += srcs[f].lines[a - 1:e]
    if tail:
        out += ["", ""] + tail
    nl = srcs[units[0][0]].nl

    # ---- split 파일
    per_file = {}
    for f, uid, node, b, r in units:
        per_file.setdefault(f, []).append((node, b))
    stem = card[:-3]
    new_text, reexports = {}, {}
    for f, lst in per_file.items():
        s = srcs[f]
        L = s.lines
        drop, names, starts = set(), set(), set()
        for node, b in lst:
            a, e = span(node, L, s.covered)
            drop |= set(range(a, e + 1))
            starts.add(a)
            names |= set(b)
        line = "from %s import %s" % (stem, ", ".join(sorted(names)))
        if re.search(r"^from %s import " % re.escape(stem), "\n".join(L), re.M):
            die("%s에 이미 %s 재수출 줄이 있다" % (f, stem))
        gone = {node.lineno for node, b in lst}           # plan 노드와 s.tree 노드는 다른 객체 -- 시작 줄로 맞춘다(위에서 dump 같음 확인)
        remaining = [n for n in s.tree.body if n.lineno not in gone and not is_doc(s.tree, n)
                     and not isinstance(n, (ast.Import, ast.ImportFrom))]
        if f not in n310 and f not in KEEP and not remaining:                       # 완전 shim (SHIM (b))
            keep_l = []
            first = s.tree.body[0] if s.tree.body else None
            if first is not None and is_doc(s.tree, first):
                keep_l += L[:first.end_lineno]
            for n in s.tree.body:
                if isinstance(n, ast.ImportFrom) and (n.module == "__future__" or (n.level == 0 and n.module
                                                                                     and (n.module + ".py") in n310)):
                    keep_l += L[n.lineno - 1:n.end_lineno]
            new_text[f] = keep_l + [line]
            reexports[f] = {"line": line, "where": "complete shim"}
            continue
        at_end = (n310.get(f) == 7 and kc > 7)
        he, after_path = head_end(s.tree)
        if not at_end and he == 0:
            die("%s: 앞머리 import 묶음이 없다" % f)
        rline = line + ("  # noqa: E402" if after_path and not at_end else "")
        newL, blank_run, junction = [], 0, False
        for i, l in enumerate(L, 1):
            if i in drop:
                junction = True
                continue
            if l.strip() == "":
                if junction and blank_run >= 2:
                    continue                              # 삭제 자리에서 빈 줄 3개 이상을 2개로
                blank_run += 1
            else:
                blank_run, junction = 0, False
            newL.append(l)
            if i == he and not at_end:
                newL.append(rline)
        if at_end:
            while newL and newL[-1] == "":
                newL.pop()
            newL += ["", "", rline]
        new_text[f] = newL
        reexports[f] = {"line": rline, "where": "file end (D-22)" if at_end else "after import head line %d" % he}

    report = dict(summary, units=[{"unit": uid, "rule": r, "file": f, "lines": list(span(node, srcs[f].lines, srcs[f].covered)),
                                   "names": b} for f, uid, node, b, r in units],
                  mod_imports_head=head, mod_imports_tail=tail, reexports=reexports,
                  reg_mismatch_card=[x for x in res["reg_mismatch"] if res["assignment"].get(x["unit"], {}).get("mod") == card])
    if not ns.dry_run:
        with open(os.path.join(root, A, card), "wb") as fh:
            fh.write((nl.join(out) + nl).encode("utf-8"))
        for f, lines in new_text.items():
            srcs[f].write(lines)
        if ns.commit:
            files = [A + card] + [A + f for f in new_text]
            rc, o = git(root, "add", "--", *files)
            msg = "move: MOD%d %s -- %d 단위를 %s에서 옮김(바이트 그대로), 명시 재수출" % (
                kc, card, len(units), "·".join(sorted(new_text)))
            rc2, o2 = git(root, "commit", "-q", "-m", msg)
            if rc or rc2:
                die("commit 실패: " + o + o2)
            report["commit"] = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip()
    if ns.report:
        json.dump(report, open(ns.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: report[k] for k in ("card", "plan_verdict", "plan_lists", "pins", "reexports",
                                             "mod_imports_head", "mod_imports_tail")}
                     | {"n_units": len(units), "dry_run": ns.dry_run, "commit": report.get("commit")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
