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
import os
import pathlib
import re
import sys

_DISP_RE = re.compile(r"^보류\(Phase [0-9]+[a-z]?\)")
_FIRST_NAME_RE = re.compile(r"^`([^`]+)`")
_HEADING_N_RE = re.compile(r"^###\s+(.+?)\s*\((\d+)\)\s*$")
_ASSETS_REL = ("skills", "analog-gmid-design", "assets")
# 2026-10-07 legacy 이동: 옛 엔진 소스·하네스는 legacy/ 로 옮겼다. 이동 전 범위(A/*.py + 하네스)를 그대로 본다.
_LEGACY_REL = ("skills", "analog-gmid-design", "legacy")


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


_DF23_BEHAVIOR = "동작을 정함"
_DF23_NEW = "신규"
_DF23_DF_RE = re.compile(r"^DF-(\d+)")
_DF23_PATH_RE = re.compile(r"^목록:\s*`([^`]*)`")
_DF23_MEASURED_RE = re.compile(r"^measured_at:\s*`([^`]*)`")
_DF23_HDR_81 = ["축", "값", "항목 수"]
_DF23_HDR_82 = ["함수", "파일", "항목 수", "DF", "담당 Phase"]
_DF23_ITEM_KEYS = ("file", "function", "role", "phase", "plan_mapping")


def _df23_expected(inventory):
    """목록 items에서 §8.1·§8.2 기대 값을 계산한다. 입력 오류는 ValueError."""
    if not isinstance(inventory, dict) or "measured_at" not in inventory or "items" not in inventory:
        raise ValueError("목록에 measured_at·items가 없다")
    items = inventory["items"]
    if not isinstance(items, list):
        raise ValueError("목록 items가 목록이 아니다")
    totals = {}
    groups = {}
    base_files = {}
    for idx, it in enumerate(items):
        if not isinstance(it, dict):
            raise ValueError(f"항목 {idx}가 dict가 아니다")
        for k in _DF23_ITEM_KEYS:
            if k not in it:
                raise ValueError(f"항목 {idx}에 {k} 필드가 없다")
        fn, file = it["function"], it["file"]
        if not isinstance(fn, str) or fn == "":
            raise ValueError(f"항목 {idx}의 function이 빈 값이다")
        base = str(file).replace("\\", "/").rsplit("/", 1)[-1]
        base_files.setdefault(base, set()).add(file)
        for axis in ("role", "phase"):
            key = (axis, str(it[axis]))
            totals[key] = totals.get(key, 0) + 1
        if it["role"] == _DF23_BEHAVIOR:
            pm = it["plan_mapping"]
            m = _DF23_DF_RE.match(pm) if isinstance(pm, str) else None
            if not m and not (isinstance(pm, str) and pm.startswith(_DF23_NEW)):
                raise ValueError(f"항목 {idx}의 plan_mapping이 DF 번호도 {_DF23_NEW}도 아니다: {pm!r}")
            g = groups.setdefault(("`" + fn + "`", base), {"n": 0, "df": set(), "new": False, "ph": set()})
            g["n"] += 1
            if m:
                g["df"].add(int(m.group(1)))
            else:
                g["new"] = True
            g["ph"].add(str(it["phase"]))
    for base, files in base_files.items():
        if len(files) > 1:
            raise ValueError(f"서로 다른 file 값이 같은 파일 이름 {base!r}을 가진다")
    exp81 = {k: str(v) for k, v in totals.items()}
    exp82 = {}
    for key, g in groups.items():
        dfs = ["DF-%d" % n for n in sorted(g["df"])]
        if g["new"]:
            dfs.append(_DF23_NEW)
        exp82[key] = (str(g["n"]), ", ".join(dfs), ", ".join(sorted(g["ph"])))
    return exp81, exp82


def _df23_rows_under(sec, sub_prefix, header):
    """절 줄들에서 `### <sub_prefix>` 소절 아래 `header` 머리를 가진 표들의 행. 없으면 None."""
    start = None
    for i, ln in enumerate(sec):
        if ln.startswith("### " + sub_prefix):
            start = i
            break
    if start is None:
        return None
    end = len(sec)
    for j in range(start + 1, len(sec)):
        if sec[j].startswith("### "):
            end = j
            break
    found = False
    rows = []
    for hdr, rws in _tables_in(sec[start + 1:end]):
        if hdr == header:
            found = True
            rows += rws
    return rows if found else None


def check_df23(registry_text: str, inventory: dict, inventory_rel: str) -> list:
    """레지스트리 §8(DF-23 기록)을 목록 items에서 계산한 값과 대조해 발견 목록을 돌려준다. 입력 오류는 ValueError."""
    exp81, exp82 = _df23_expected(inventory)
    lines = registry_text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("## 8.") and "DF-23" in ln:
            start = i
            break
    if start is None:
        return [_finding("df23-section", "8", "title", "`## 8.` DF-23 제목 줄이 없다")]
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    sec = lines[start + 1:end]
    findings = []

    path_val = measured_val = None
    for ln in sec:
        m = _DF23_PATH_RE.match(ln)
        if m and path_val is None:
            path_val = m.group(1)
        m = _DF23_MEASURED_RE.match(ln)
        if m and measured_val is None:
            measured_val = m.group(1)
    if path_val is None:
        findings.append(_finding("df23-section", "8", "목록", "`목록:` 줄이 없다"))
    elif path_val != inventory_rel:
        findings.append(_finding("df23-path", "8", path_val, f"목록 경로 != {inventory_rel!r}"))
    if measured_val is None:
        findings.append(_finding("df23-section", "8", "measured_at", "`measured_at:` 줄이 없다"))
    elif measured_val != inventory["measured_at"]:
        findings.append(_finding("df23-measured-at", "8", measured_val, f"measured_at != {inventory['measured_at']!r}"))

    rows81 = _df23_rows_under(sec, "8.1", _DF23_HDR_81)
    if rows81 is None:
        findings.append(_finding("df23-section", "8", "8.1", "§8.1 소절 또는 표 머리가 없다"))
    else:
        seen = set()
        for r in rows81:
            r = r + [""] * (3 - len(r))
            key = (r[0], r[1])
            name = f"{r[0]}:{r[1]}"
            if key in seen:
                findings.append(_finding("df23-total", "8.1", name, "같은 (축, 값) 행이 두 번 있다"))
            elif key not in exp81:
                findings.append(_finding("df23-total", "8.1", name, "목록에 없는 행이다"))
            elif r[2] != exp81[key]:
                findings.append(_finding("df23-total", "8.1", name, f"항목 수 {r[2]!r} != {exp81[key]!r}"))
            seen.add(key)
        for key in exp81:
            if key not in seen:
                findings.append(_finding("df23-total", "8.1", f"{key[0]}:{key[1]}", "행이 빠졌다"))

    rows82 = _df23_rows_under(sec, "8.2", _DF23_HDR_82)
    if rows82 is None:
        findings.append(_finding("df23-section", "8", "8.2", "§8.2 소절 또는 표 머리가 없다"))
    else:
        seen = set()
        for r in rows82:
            r = r + [""] * (5 - len(r))
            key = (r[0], r[1])
            name = f"{r[1]}::{r[0].strip('`')}"
            if key in seen:
                findings.append(_finding("df23-function", "8.2", name, "같은 (함수, 파일) 행이 두 번 있다"))
            elif key not in exp82:
                findings.append(_finding("df23-function", "8.2", name, "목록에 없는 행이다"))
            elif tuple(r[2:5]) != exp82[key]:
                findings.append(_finding("df23-function", "8.2", name,
                                         f"(항목 수, DF, 담당 Phase) {tuple(r[2:5])!r} != {exp82[key]!r}"))
            seen.add(key)
        for key in exp82:
            if key not in seen:
                findings.append(_finding("df23-function", "8.2", f"{key[1]}::{key[0].strip('`')}", "행이 빠졌다"))
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
    for rel in (_ASSETS_REL, _LEGACY_REL):
        for p in sorted(root.joinpath(*rel).glob("*.py")):
            names |= _defs_of(p)
    for harness in (root / "workspaces" / "run_harness.py", root.joinpath(*_LEGACY_REL) / "workspaces" / "run_harness.py"):
        if harness.is_file():
            names |= _defs_of(harness)
    return names


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="함수 재사용 레지스트리 §7 검사")
    ap.add_argument("--registry", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--df23-inventory", default=None)
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
        if args.df23_inventory is not None:
            inv_real = os.path.realpath(args.df23_inventory)
            root_real = os.path.realpath(str(root))
            if os.path.commonpath([os.path.normcase(root_real), os.path.normcase(inv_real)]) != os.path.normcase(root_real):
                raise ValueError("목록이 저장소 루트 밖이다")
            inv_rel = "/".join(pathlib.PurePath(os.path.relpath(inv_real, root_real)).parts)
            with open(inv_real, encoding="utf-8") as fh:
                inventory = json.load(fh)
            if not isinstance(inventory, dict):
                raise ValueError("목록 최상위가 dict가 아니다")
            findings = findings + check_df23(text, inventory, inv_rel)
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
