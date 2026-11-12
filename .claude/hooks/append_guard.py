#!/usr/bin/env python
"""Bash·PowerShell PreToolUse 게이트 -- 셸 추가 쓰기(`>>`, `tee -a`, heredoc 파일 쓰기, Add-Content, Out-File -Append)를
임시 폴더 밖 파일에 하면 exit 2로 거부한다(원칙 29, `.claude/rules/operations.md`: 프로젝트 파일 수정은 Edit/Write 또는 Python 바이너리 치환·append만).
대상 경로를 정할 수 없으면(변수 등) 거부한다(fail-closed). 허용 대상: 임시 폴더, /dev/null, NUL, $null, fd(&1·&2).
환경 변수: APPEND_GUARD_ALLOW(추가 허용 루트, os.pathsep 구분).
"""
import json
import os
import re
import sys

TEMP_VARS = ("TEMP", "TMP", "TMPDIR")
NULL_TARGETS = {"/dev/null", "nul", "$null", "/dev/stdout", "/dev/stderr"}

HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)[A-Za-z_][A-Za-z0-9_]*\1")
APPEND_RE = re.compile(r"(?<![<>])(?:\d|&)?>>\s*(\"[^\"]*\"|'[^']*'|[^\s;|&)]+)")
WRITE_RE = re.compile(r"(?<![<>&\d-])(?:\d|&)?>(?![>&=])\s*(\"[^\"]*\"|'[^']*'|[^\s;|&)]+)")
TEE_RE = re.compile(r"\btee\b((?:\s+-[A-Za-z-]+)*)((?:\s+(?:\"[^\"]*\"|'[^']*'|[^\s;|&)-][^\s;|&)]*))*)")
PS_APPEND_RE = re.compile(r"\b(?:Add-Content|ac)\b|\bOut-File\b[^;|]*-Append\b", re.I)
PS_PATH_RE = re.compile(r"-(?:Path|FilePath|LiteralPath)\s+(\"[^\"]*\"|'[^']*'|[^\s;|]+)", re.I)


def allowed_roots():
    roots = []
    for v in TEMP_VARS:
        if os.environ.get(v):
            roots.append(os.environ[v])
    roots.append(os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp"))
    extra = os.environ.get("APPEND_GUARD_ALLOW", "")
    roots += [r for r in extra.split(os.pathsep) if r]
    return [os.path.normcase(os.path.abspath(r)) for r in roots]


def unquote(t):
    t = t.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        t = t[1:-1]
    return t


def expand_temp_vars(t):
    for v in TEMP_VARS:
        val = os.environ.get(v)
        if not val:
            continue
        for pat in ("${%s}" % v, "$%s" % v, "$env:%s" % v, "%%%s%%" % v):
            if t.lower().startswith(pat.lower()):
                t = val + t[len(pat):]
    return t


def resolve(tok, cwd):
    """대상 토큰 -> (허용 여부, 정규 경로 또는 사유)."""
    t = unquote(tok)
    if t.startswith("&") or t.lower() in NULL_TARGETS:
        return True, t
    t = expand_temp_vars(t)
    if t.startswith("/tmp/") or t == "/tmp":
        return True, t
    if re.search(r"[$`%]|\$\(", t):
        return False, "대상 경로에 풀리지 않는 변수/치환이 있음: %s" % tok
    m = re.match(r"^/([A-Za-z])(/.*)?$", t)
    if m:
        t = m.group(1) + ":" + (m.group(2) or "/")
    if t.startswith("~"):
        t = os.path.expanduser(t)
    if not os.path.isabs(t):
        t = os.path.join(cwd, t)
    p = os.path.normcase(os.path.abspath(t))
    for r in allowed_roots():
        if p == r or p.startswith(r.rstrip("\\/") + os.sep):
            return True, p
    return False, p


def tee_targets(args):
    out = []
    for m in re.finditer(r"\"[^\"]*\"|'[^']*'|[^\s;|&)]+", args):
        tok = m.group(0)
        if not tok.startswith("-"):
            out.append(tok)
    return out


def strip_heredoc_bodies(cmd):
    """heredoc 본문(표지 다음 줄 ~ 닫는 표지 줄)을 지운다 -- 본문 글자(`>` 등)는 셸 연산자가 아니다."""
    lines = cmd.split("\n")
    out, pending = [], []
    for ln in lines:
        if pending:
            if ln.strip() == pending[0]:
                pending.pop(0)
            continue
        out.append(ln)
        pending = [m.group(2) for m in re.finditer(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", ln)]
    return "\n".join(out)


def mask_quotes(cmd):
    """따옴표 구간을 자리표로 바꾼다 -- 따옴표 안 `>>`는 연산자가 아니다. 자리표가 대상 토큰이면 원문으로 되돌린다."""
    spans, out, i = {}, [], 0
    while i < len(cmd):
        c = cmd[i]
        if c in "\"'":
            j = cmd.find(c, i + 1)
            if j < 0:
                j = len(cmd) - 1
            key = "\x00%d\x00" % len(spans)
            spans[key] = cmd[i:j + 1]
            out.append(key)
            i = j + 1
            continue
        out.append(c)
        i += 1
    return "".join(out), spans


def check(cmd, cwd):
    errs = []
    has_heredoc = bool(HEREDOC_RE.search(cmd))
    cmd, spans = mask_quotes(strip_heredoc_bodies(cmd))

    def judge(tok, what):
        for k, v in spans.items():
            tok = tok.replace(k, v)
        ok, info = resolve(tok, cwd)
        if not ok:
            errs.append("%s -> %s" % (what, info))

    for m in APPEND_RE.finditer(cmd):
        judge(m.group(1), "`>>` 추가 쓰기")
    for m in TEE_RE.finditer(cmd):
        flags, args = m.group(1), m.group(2)
        if re.search(r"(?:^|\s)-(?:a\b|[A-Za-z]*a[A-Za-z]*\b|-append\b)", flags):
            for tok in tee_targets(args):
                judge(tok, "`tee -a` 추가 쓰기")
    if has_heredoc:
        for m in WRITE_RE.finditer(cmd):
            judge(m.group(1), "heredoc + `>` 파일 쓰기")
        for m in TEE_RE.finditer(cmd):
            for tok in tee_targets(m.group(2)):
                judge(tok, "heredoc + `tee` 파일 쓰기")
    if PS_APPEND_RE.search(cmd):
        paths = [m.group(1) for m in PS_PATH_RE.finditer(cmd)]
        if not paths:
            pm = re.search(r"\b(?:Add-Content|ac)\s+(\"[^\"]*\"|'[^']*'|[^\s;|-][^\s;|]*)", cmd, re.I)
            if pm:
                paths = [pm.group(1)]
        if not paths:
            errs.append("PowerShell 추가 쓰기 -> 대상 경로를 정할 수 없음")
        for tok in paths:
            judge(tok, "PowerShell 추가 쓰기")
    return errs


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001 -- 재설정 불가 스트림은 그대로 쓴다
            pass
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        if data.get("tool_name") not in ("Bash", "PowerShell"):
            return 0
        cmd = (data.get("tool_input") or {}).get("command") or ""
        cwd = data.get("cwd") or os.getcwd()
        errs = check(cmd, cwd)
    except Exception as e:  # noqa: BLE001 -- fail-closed: 판정 실패는 거부
        sys.stderr.write("append_guard: 판정 실패로 거부 (%s: %s)\n" % (type(e).__name__, e))
        return 2
    if errs:
        sys.stderr.write(
            "append_guard: 셸 추가 쓰기 거부 (원칙 29 .claude/rules/operations.md -- heredoc·`>>` append 금지).\n"
            + "".join("  - %s\n" % e for e in errs)
            + "대신: 새 파일·전체 교체는 Write, 부분 수정은 Edit, 추가는 Python 바이너리 append"
              "(open(p,'ab'), 쓰기 전 기존 바이트 접두 확인). 임시 파일은 임시 폴더에 쓰면 허용.\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
