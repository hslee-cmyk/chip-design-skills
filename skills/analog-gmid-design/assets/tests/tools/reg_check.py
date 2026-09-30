"""레지스트리 검사 도구 (20260930-registry-grade-fix, design 20-dead-code-dup §10 E0).

`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` §7('D -- 운영 경로 호출 0')이 사실인지 기계로 본다.

규칙:
* `stale`       -- §7 표 첫 칸의 백틱 이름(메서드는 `Class.method`)이 엔진 정의 이름에 없다.
* `disposition` -- §7 표에 `처리` 열이 없거나, 값이 `^보류\\(Phase [0-9]+[a-z]?\\)`에 맞지 않는다.
* `count`       -- §1 표의 파일별 D 열 값과 §7 해당 소절 표의 행 수가 다르다(소절 제목의 괄호 수도 같아야 한다).

엔진 정의 이름 = `<root>/skills/analog-gmid-design/assets/*.py`(최상위 파일만)의 최상위 def·class와 클래스 메서드 `Class.method`,
`<root>/workspaces/run_harness.py`의 최상위 def·class. 표준 라이브러리만 쓴다.

사용: reg_check.py --registry <레지스트리> --root <저장소 루트>   (exit 0 = 발견 0, 1 = 발견, 2 = 입력 오류)
"""
import argparse
import ast
import json
import pathlib
import re
import sys

_DISP_RE = re.compile(r"^보류\(Phase [0-9]+[a-z]?\)")
_FIRST_NAME_RE = re.compile(r"^`([^`]+)`")
_HEADING_N_RE = re.compile(r"^###\s+(.+?)\s*\((\d+)\)\s*$")
_ASSETS_REL = ("skills", "analog-gmid-design", "assets")


def _split_row(line):
    """마크다운 표 한 줄을 칸 목록으로(`\\|`는 칸 구분이 아니다)."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    parts = re.split(r"(?<!\\)\|", s)
    return [p.strip() for p in parts]


def _is_separator(cells):
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) or c == "" for c in cells) and any(cells)


def _tables_in(lines):
    """줄 목록에서 표를 모은다: [(머리 칸들, [행 칸들...])]. 머리 다음 줄이 구분선인 것만 표다."""
    tables = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].lstrip().startswith("|") and i + 1 < n and lines[i + 1].lstrip().startswith("|"):
            header = _split_row(lines[i])
            if _is_separator(_split_row(lines[i + 1])):
                rows = []
                j = i + 2
                while j < n and lines[j].lstrip().startswith("|"):
                    rows.append(_split_row(lines[j]))
                    j += 1
                tables.append((header, rows))
                i = j
                continue
        i += 1
    return tables


def _section_lines(lines, prefix):
    """`prefix`로 시작하는 `## ` 제목 줄부터 다음 `## ` 전까지. 제목이 없으면 None."""
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith(prefix):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return lines[start + 1:end]


def _subsections(sec_lines):
    """§7 소절: [(제목 파일, 제목 괄호 수 또는 None, 소절 줄들)]."""
    subs = []
    cur = None
    for ln in sec_lines:
        if ln.startswith("### "):
            m = _HEADING_N_RE.match(ln.rstrip())
            if m:
                cur = [m.group(1), int(m.group(2)), []]
            else:
                cur = [ln[4:].strip(), None, []]
            subs.append(cur)
        elif cur is not None:
            cur[2].append(ln)
    return subs


def _finding(rule, section, name, detail):
    return {"rule": rule, "section": section, "name": name, "detail": detail}


def check(registry_text: str, engine_names: set) -> list:
    """레지스트리 §7을 판정해 발견 목록을 돌려준다. §7 제목이 없으면 ValueError."""
    lines = registry_text.splitlines()
    sec7 = _section_lines(lines, "## 7.")
    if sec7 is None:
        raise ValueError("레지스트리에 '## 7.' 절이 없다")
    findings = []

    # §1 집계: 파일 -> D 값
    s1_d = {}
    sec1 = _section_lines(lines, "## 1.")
    if sec1 is not None:
        for header, rows in _tables_in(sec1):
            if "D" in header and header and header[0] == "파일":
                d_idx = header.index("D")
                for r in rows:
                    if len(r) > d_idx and r[0]:
                        s1_d[r[0]] = r[d_idx]
                break

    seen_files = set()
    for fname, heading_n, sub_lines in _subsections(sec7):
        section = "7/" + fname
        seen_files.add(fname)
        tables = _tables_in(sub_lines)
        n_rows = sum(len(rows) for _, rows in tables)

        for header, rows in tables:
            disp_idx = header.index("처리") if "처리" in header else None
            if disp_idx is None:
                findings.append(_finding("disposition", section, "", "표에 `처리` 열이 없다"))
            for r in rows:
                m = _FIRST_NAME_RE.match(r[0]) if r else None
                name = m.group(1) if m else ""
                if name and name not in engine_names:
                    findings.append(_finding("stale", section, name, "엔진 정의 이름에 없다"))
                if disp_idx is not None:
                    val = r[disp_idx] if disp_idx < len(r) else ""
                    if not _DISP_RE.match(val):
                        findings.append(_finding("disposition", section, name or (r[0] if r else ""),
                                                 "`처리` 값이 `보류(Phase <p>)` 형식이 아니다: " + repr(val)))

        if heading_n is not None and heading_n != n_rows:
            findings.append(_finding("count", section, fname, f"소절 제목 괄호 수 {heading_n} != 표 행 수 {n_rows}"))
        if fname not in s1_d:
            findings.append(_finding("count", section, fname, "§1 집계 표에 이 파일 행이 없다"))
        else:
            d_txt = s1_d[fname]
            if not re.fullmatch(r"\d+", d_txt) or int(d_txt) != n_rows:
                findings.append(_finding("count", section, fname, f"§1 D 열 {d_txt!r} != 표 행 수 {n_rows}"))

    for fname, d_txt in s1_d.items():
        if fname not in seen_files and d_txt != "0":
            findings.append(_finding("count", "1", fname, f"§1 D 열 {d_txt!r}인데 §7 소절이 없다"))
    return findings


def _defs_of(path):
    """소스 파일의 최상위 def·class 이름과 클래스 메서드 `Class.method`."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.add(node.name + "." + sub.name)
    return names


def collect_engine_names(root):
    """엔진 정의 이름 집합(모듈 문서 참조)."""
    root = pathlib.Path(root)
    names = set()
    assets = root.joinpath(*_ASSETS_REL)
    for p in sorted(assets.glob("*.py")):
        names |= _defs_of(p)
    harness = root / "workspaces" / "run_harness.py"
    if harness.is_file():
        names |= _defs_of(harness)
    return names


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="함수 재사용 레지스트리 §7 검사")
    ap.add_argument("--registry", required=True)
    ap.add_argument("--root", required=True)
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    reg = pathlib.Path(args.registry)
    root = pathlib.Path(args.root)
    try:
        text = reg.read_text(encoding="utf-8")
        names = collect_engine_names(root)
        findings = check(text, names)
    except (OSError, UnicodeDecodeError, SyntaxError, ValueError) as e:
        print(f"입력 오류: {e}", file=sys.stderr)
        return 2
    for f in findings:
        print(json.dumps(f, ensure_ascii=False))
    if not findings:
        print("reg_check: 발견 0")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
