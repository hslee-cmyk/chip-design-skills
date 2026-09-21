"""V5 기준 약화 (05-role-separation design §10 V5 판정식, 계획 N4.2 V5, N0.4 '기준 약화' 8패턴).

    $PY weakening_diff.py --root <격리 복제본 루트> --base <커밋> --head <커밋>

입력: test 분류 파일(`skills/analog-gmid-design/assets/tests/**`, `tests/tools/**` 제외) diff와, TS1 전에는 소스의
`if __name__ == "__main__":` 블록 diff. test 분류의 `.py` 아닌 파일(기준선 `.log` 등)과 `assets/tests/conftest.py`가
바뀌면 무조건 승인 기록 요구(review29 Q-15, review30 J1). 그 밖의 `.py`는 test 함수 단위(이름 목록 없이 구조로):

| 패턴 | 판정식 |
|---|---|
| assert 삭제 | 함수 안 `Assert`·`pytest.raises`·`pytest.approx` 수 감소, 또는 test 함수 삭제 |
| 비교 완화 | `Compare` 연산자 변화, `approx`의 `rel`·`abs` 인자 추가·변경 |
| 허용오차 확대·기대값 리터럴·픽스처 입력 리터럴·격자 확대 | 숫자·문자열 `Constant` 값 변경(픽스처 함수 포함) |
| skip/xfail 추가 | `pytest.mark.skip*`·`xfail` 표식이나 `pytest.skip`·`pytest.xfail` 호출 추가 |
| assert를 조건문·try 아래로 | `Assert`의 조상에 새 `If`·`Try` |

발견이 있으면 발견 경로의 diff 해시(00-common §8.2 blob 식)를 내고, head 트리에 `target_kind: diff`·그 해시의 승인
기록이 없으면 FAIL. auditor는 이 해시를 `checks.V5.basis`에 적는다(§9.2-9가 승인 기록과 대조).
exit 0 PASS / 1 FAIL / 2 실행 오류.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os
import subprocess
import sys

TEST_PREFIX = "skills/analog-gmid-design/assets/tests/"
TEST_TOOLS = "skills/analog-gmid-design/assets/tests/tools/"
CONFTEST = "skills/analog-gmid-design/assets/tests/conftest.py"


def _git(root, args, check=True):
    p = subprocess.run(["git", "-C", root] + args, capture_output=True, env=dict(os.environ, GIT_NO_REPLACE_OBJECTS="1"))
    if check and p.returncode != 0:
        raise RuntimeError("git %s 실패: %s" % (" ".join(args[:3]), p.stderr.decode("utf-8", "replace")[:300]))
    return p


def _blob(root, rev, path):
    p = _git(root, ["rev-parse", "--verify", "--quiet", "%s:%s" % (rev, path)], check=False)
    return p.stdout.decode().strip() if p.returncode == 0 else None


def _src(root, rev, path):
    p = _git(root, ["show", "%s:%s" % (rev, path)], check=False)
    return p.stdout.decode("utf-8", "replace") if p.returncode == 0 else None


def _is_docstring(node, parent):
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) \
        and getattr(parent, "body", [None])[0] is node


def _units(tree):
    """{이름: 노드 목록} -- 함수(qualname)마다, 그리고 모듈 최상위 문장('<module>'), `if __name__` 블록('__main__')."""
    units = {}

    def rec(nodes, prefix):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                units[prefix + n.name] = [n]
            elif isinstance(n, ast.ClassDef):
                rec(n.body, prefix + n.name + ".")
    rec(tree.body, "")
    top, main = [], []
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name) \
                and n.test.left.id == "__name__":
            main.append(n)
        else:
            top.append(n)
    units["<module>"] = top
    if main:
        units["__main__"] = main
    return units


def _walk(nodes):
    """중첩 def 안으로 들어가지 않는 walk(중첩 def는 자기 단위다) -- 단 단위 자신의 데코레이터는 본다."""
    stack = []
    for n in nodes:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stack.extend(n.decorator_list)
            stack.extend(n.args.defaults + [d for d in n.args.kw_defaults if d is not None])
            stack.extend(n.body)
        else:
            stack.append(n)
    out = []
    while stack:
        x = stack.pop()
        out.append(x)
        for c in ast.iter_child_nodes(x):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            stack.append(c)
    return out


def _is_call(n, names):
    if not isinstance(n, ast.Call):
        return False
    f = n.func
    if isinstance(f, ast.Attribute) and f.attr in names:
        return True
    return isinstance(f, ast.Name) and f.id in names


def _dotted(n):
    parts = []
    while isinstance(n, ast.Attribute):
        parts.append(n.attr)
        n = n.value
    if isinstance(n, ast.Name):
        parts.append(n.id)
    return ".".join(reversed(parts))


def features(nodes):
    ns = _walk(nodes)
    f = {}
    f["asserts"] = sum(1 for n in ns if isinstance(n, ast.Assert)) + \
        sum(1 for n in ns if _is_call(n, ("raises", "approx")) and _dotted(n.func).startswith("pytest"))
    f["cmp_ops"] = sorted(type(o).__name__ for n in ns if isinstance(n, ast.Assert)
                          for c in ast.walk(n.test) if isinstance(c, ast.Compare) for o in c.ops)
    f["approx_kw"] = sorted((k.arg, ast.dump(k.value)) for n in ns if _is_call(n, ("approx",)) for k in n.keywords
                            if k.arg in ("rel", "abs"))
    consts = []
    for n in ns:
        if isinstance(n, ast.Constant) and (isinstance(n.value, (int, float, complex, str)) and not isinstance(n.value, bool)):
            consts.append(repr(n.value))
    # docstring 제외
    docs = set()
    for n in nodes:
        for x in [n] + list(ast.walk(n)):
            if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and x.body and _is_docstring(x.body[0], x):
                docs.add(repr(x.body[0].value.value))
    f["consts"] = [c for c in consts if c not in docs]
    skips = 0
    for n in ns:
        d = _dotted(n.func) if isinstance(n, ast.Call) else _dotted(n) if isinstance(n, ast.Attribute) else ""
        if d.startswith("pytest.mark.skip") or d.startswith("pytest.mark.xfail"):
            skips += 1
        if isinstance(n, ast.Call) and d in ("pytest.skip", "pytest.xfail", "pytest.importorskip"):
            skips += 1
    f["skips"] = skips
    guarded = 0
    for top in nodes:
        guarded += _guarded_asserts(top)
    f["guarded"] = guarded
    return f


def _guarded_asserts(root):
    cnt = 0

    def rec(n, g):
        nonlocal cnt
        for c in ast.iter_child_nodes(n):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and c is not root:
                continue
            if isinstance(c, ast.Assert) and g:
                cnt += 1
            rec(c, g or isinstance(c, (ast.If, ast.Try, ast.TryStar)))
    rec(root, False)
    return cnt


def compare_units(path, base_src, head_src):
    """발견 목록 [{path, unit, pattern, detail}]."""
    out = []
    bt = ast.parse(base_src) if base_src is not None else None
    ht = ast.parse(head_src) if head_src is not None else None
    bu = _units(bt) if bt else {}
    hu = _units(ht) if ht else {}
    for name, bn in bu.items():
        leaf = name.split(".")[-1]
        if name not in hu:
            if leaf.startswith("test"):
                out.append({"path": path, "unit": name, "pattern": "assert 삭제", "detail": "test 함수 삭제"})
            continue
        bf, hf = features(bn), features(hu[name])
        if hf["asserts"] < bf["asserts"]:
            out.append({"path": path, "unit": name, "pattern": "assert 삭제",
                        "detail": "%d -> %d" % (bf["asserts"], hf["asserts"])})
        if hf["cmp_ops"] != bf["cmp_ops"] or hf["approx_kw"] != bf["approx_kw"]:
            out.append({"path": path, "unit": name, "pattern": "비교 완화", "detail": "Compare 연산자 또는 approx rel/abs 변화"})
        sm = difflib.SequenceMatcher(a=bf["consts"], b=hf["consts"], autojunk=False)
        changed = [(bf["consts"][i1:i2], hf["consts"][j1:j2]) for tag, i1, i2, j1, j2 in sm.get_opcodes()
                   if tag in ("replace", "delete")]
        if changed:
            out.append({"path": path, "unit": name, "pattern": "리터럴 변경(허용오차·기대값·픽스처 입력·격자)",
                        "detail": "; ".join("%s -> %s" % (a, b) for a, b in changed[:5])})
        if hf["skips"] > bf["skips"]:
            out.append({"path": path, "unit": name, "pattern": "skip/xfail 추가",
                        "detail": "%d -> %d" % (bf["skips"], hf["skips"])})
        if hf["guarded"] > bf["guarded"]:
            out.append({"path": path, "unit": name, "pattern": "assert를 조건문·try 아래로",
                        "detail": "%d -> %d" % (bf["guarded"], hf["guarded"])})
    return out


def diff_hash(root, base, head, paths):
    ents = []
    for p in sorted(paths):
        ents.append("%s\t%s\t%s\n" % (p, _blob(root, base, p) or "-", _blob(root, head, p) or "-"))
    return hashlib.sha256("".join(ents).encode("utf-8")).hexdigest()


def approved_hashes(root, rev):
    out = _git(root, ["ls-tree", "-r", "-z", "--name-only", "--full-tree", rev, "--", ".ai/approvals/"]).stdout.decode("utf-8")
    hs = set()
    for p in out.split("\0"):
        if not p.endswith(".md") or os.path.basename(p).startswith("_"):
            continue
        text = (_src(root, rev, p) or "").replace("\r\n", "\n")
        if "\ntarget_kind: diff\n" in text:
            for line in text.split("\n"):
                if line.startswith("target: "):
                    hs.add(line[len("target: "):].strip())
    return hs


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="weakening_diff.py")
    ap.add_argument("--root", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        root = ns.root
        names = _git(root, ["diff", "--name-only", "--no-renames", ns.base, ns.head]).stdout.decode("utf-8").splitlines()
        findings = []
        for p in names:
            is_test = p.startswith(TEST_PREFIX) and not p.startswith(TEST_TOOLS)
            if is_test and (not p.endswith(".py") or p == CONFTEST):
                findings.append({"path": p, "unit": "(파일)", "pattern": "무조건 승인 필요",
                                 "detail": "test 분류 비-.py 파일 또는 tests/conftest.py 변경"})
                continue
            if is_test:
                findings += compare_units(p, _src(root, ns.base, p), _src(root, ns.head, p))
            elif p.startswith("skills/analog-gmid-design/assets/") and p.count("/") == 3 and p.endswith(".py"):
                # TS1 전: 소스의 `if __name__ == "__main__":` 블록 diff
                b, h = _src(root, ns.base, p), _src(root, ns.head, p)
                fs = compare_units(p, b, h)
                findings += [f for f in fs if f["unit"] == "__main__"]
        paths = sorted({f["path"] for f in findings})
        h = diff_hash(root, ns.base, ns.head, paths) if paths else None
        ok_by_approval = h is not None and h in approved_hashes(root, ns.head)
    except (OSError, RuntimeError, SyntaxError, UnicodeDecodeError) as e:
        print(json.dumps({"tool": "V5", "verdict": "ERROR", "error": "%s: %s" % (type(e).__name__, e)}, ensure_ascii=False))
        return 2
    fail = bool(findings) and not ok_by_approval
    print(json.dumps({"tool": "V5", "verdict": "FAIL" if fail else "PASS", "findings": findings, "diff_paths": paths,
                      "diff_hash": h, "approved": ok_by_approval}, ensure_ascii=False))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
