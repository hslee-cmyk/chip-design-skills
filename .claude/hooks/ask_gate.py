#!/usr/bin/env python
"""AskUserQuestion PreToolUse 게이트. 점검 파일(wt/_drafts/ask_gates/*.md)이 없거나 불완전하면 exit 2로 거부.
환경 변수: ASK_GATE_DIR(점검 폴더), ASK_GATE_REPO(적용 범위 루트), ASK_GATE_BASE(상대 경로 기준).
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ask_gate_rules  # noqa: E402

DEF_DIR = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/ask_gates"
DEF_REPO = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
DEF_BASE = "C:/Users/HSLEE/Documents/Todoc/fpga"
# POSIX 절대경로(/usrdata/..., /users/...)도 근거 경로로 인식한다 -- Linux(cloud0)에서만(2026-11-11 사용자 결정 A).
# Windows는 판정 불변: MSYS식 /c/... 표기를 새로 경로로 세지 않는다. 앞 글자가 단어·/·\·.·:·~ 이면 경로 아님(URL·1/2·and/or 제외).
_POSIX_ABS = r"|(?<![\w/\\.:~])/(?=[\w.~-])" if os.sep == "/" else ""
PATH_RE = re.compile(r"(?:(?<![\w/\\])wt/_drafts/|[A-Za-z]:[\\/]" + _POSIX_ABS + r")[^\s|`'\"()<>,;]+")


def norm(p):
    return os.path.normcase(os.path.realpath(p))


def read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    return raw, raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def frontmatter(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text
    fm = {}
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return fm, "\n".join(lines[i + 1:])
        if ":" in lines[i]:
            k, v = lines[i].split(":", 1)
            fm[k.strip()] = v.strip()
    return None, text


def check_path_tokens(cell, base, errs, tag):
    for m in PATH_RE.finditer(cell):
        tok = m.group(0)
        tok = re.sub(r"§.*$", "", tok)
        tok = re.sub(r":\d+(?:-\d+)?$", "", tok)
        tok = tok.rstrip(".。:*")
        if not os.path.splitext(tok)[1]:
            continue
        full = tok if re.match(r"[A-Za-z]:", tok) else os.path.join(base, tok)
        if not os.path.exists(full):
            errs.append("%s: 근거 칸의 경로가 존재하지 않음: %s (실제 파일 경로로 고칠 것)" % (tag, tok))


def check_table(sec, header, base, errs, R):
    rows = {}
    for ln in sec.split("\n"):
        s = ln.strip()
        if not s.startswith("|"):
            continue
        s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        cells = [c.strip() for c in s.split("|")]
        for n, _name in R["rows"]:
            if cells and cells[0].startswith(n):
                rows[n] = cells
    for n, _name in R["rows"]:
        tag = "[%s %s]" % (header, n)
        if n not in rows:
            errs.append("%s 행이 없음 (원칙 26 의 %s 행 모두 필요)" % (tag, "".join(x[0] for x in R["rows"])))
            continue
        cells = rows[n]
        if len(cells) < 3:
            errs.append("%s 칸이 3개 미만 (| # | 항목 | 내용 | 근거 칸 |)" % tag)
            continue
        for c in cells:
            if c == "" or set(c) <= set("?？"):
                errs.append("%s 빈 칸 또는 '?'만 있는 칸이 있음" % tag)
                break
        for c in cells:
            hit = [b for b in R["forbidden"] if b in c]
            if hit:
                errs.append("%s '%s' 포함 칸이 있음 (실제로 확인하고 근거를 적을 것)" % (tag, hit[0]))
                break
        last = cells[-1]
        pre = next((x for x in R["prefixes"] if last.startswith(x)), None)
        if pre is None:
            errs.append("%s 근거 칸이 %s 중 하나로 시작하지 않음 (원칙 26)" % (tag, " / ".join("'%s'" % x for x in R["prefixes"])))
        elif pre.endswith("("):
            inner = last[len(pre):]
            inner = inner[:inner.rfind(")")] if ")" in inner else inner
            if not inner.strip():
                errs.append("%s '%s' 괄호 안 근거가 비어 있음" % (tag, pre))
        if n in R.get("measured_only", {}):
            need = R["prefixes"][0]
            if not last.startswith(need):
                errs.append("%s 이 행은 '%s' 근거만 허용 -- %s" % (tag, need, R["measured_only"][n]))
            elif not any(os.path.splitext(re.sub(r":\d+(?:-\d+)?$", "", m.group(0).rstrip(".。:*")))[1]
                         for m in PATH_RE.finditer(last)):
                errs.append("%s 이 행 근거 칸에 점검 기록 파일 경로가 없음 -- %s" % (tag, R["measured_only"][n]))
        check_path_tokens(last, base, errs, tag)


def evaluate(q_headers, gate_dir, base, R):
    errs = []
    cands = []
    if os.path.isdir(gate_dir):
        for fn in os.listdir(gate_dir):
            if not fn.lower().endswith(".md") or fn.upper() == "TEMPLATE.MD":
                continue
            p = os.path.join(gate_dir, fn)
            try:
                _, t = read_text(p)
                fm, _b = frontmatter(t)
            except Exception:
                continue
            if not fm:
                continue
            hs = set(h.strip() for h in fm.get("headers", "").split(",") if h.strip())
            if hs == q_headers:
                cands.append((os.path.getmtime(p), p))
    if not cands:
        return ["header 집합 %s 와 정확히 같은 headers 를 가진 점검 파일이 %s 에 없음. TEMPLATE.md 로 점검 파일을 먼저 작성할 것."
                % (sorted(q_headers), gate_dir)], None, None
    cands.sort()
    gate = cands[-1][1]
    raw, text = read_text(gate)
    fm, body = frontmatter(text)
    kind = fm.get("kind", "")
    if kind == "clarify":
        if not fm.get("reason", "").strip():
            errs.append("kind=clarify 인데 reason 이 비어 있음")
        return errs, gate, kind
    if kind not in ("recommend", "approval"):
        return ["frontmatter kind 가 recommend|approval|clarify 중 하나가 아님: %r" % kind], gate, kind
    for s in R["sections"]:
        if not re.search(r"^## " + re.escape(s) + r"\s*$", body, re.M):
            errs.append("본문에 '## %s' 절이 없음" % s)
    for h in sorted(q_headers):
        m = re.search(r"^## " + re.escape(R["table_label"]) + r":\s*" + re.escape(h) + r"\s*$", body, re.M)
        if not m:
            errs.append("'## %s: %s' 절이 없음" % (R["table_label"], h))
            continue
        rest = body[m.end():]
        nx = re.search(r"^## ", rest, re.M)
        check_table(rest[:nx.start()] if nx else rest, h, base, errs, R)
    cd = fm.get("candidate_doc", "")
    if not cd or not os.path.isfile(cd):
        errs.append("candidate_doc 가 없거나 파일이 존재하지 않음: %r" % cd)
    else:
        with open(cd, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        if sha.lower() != fm.get("candidate_sha256", "").lower():
            errs.append("candidate_sha256 불일치 (현재 %s). 후보 문서가 바뀌었으면 점검을 다시 하고 sha 를 갱신할 것." % sha)
    vp = fm.get("validation", "")
    if not vp or not os.path.isfile(vp):
        errs.append("validation 파일이 없음: %r" % vp)
    else:
        _, vt = read_text(vp)
        vl = [l.strip() for l in vt.split("\n") if l.strip()]
        verdicts = [i for i, l in enumerate(vl) if l.startswith("verdict:")]
        shas = [i for i, l in enumerate(vl) if l.startswith("gate_sha256:")]
        if not verdicts or vl[verdicts[-1]] != "verdict: Major 0":
            errs.append("validation 의 마지막 verdict 줄이 'verdict: Major 0' 이 아님")
        want = "gate_sha256: " + hashlib.sha256(raw).hexdigest()
        if not shas or vl[shas[-1]] != want:
            errs.append("validation 의 gate_sha256 이 현재 점검 파일과 다름 (검증 뒤 수정됐거나 검증 안 됨). 기대 줄: %s" % want)
        elif not verdicts or shas[-1] != verdicts[-1] + 1:
            errs.append("validation 의 마지막 gate_sha256 줄 바로 앞 줄이 그 판정의 verdict 줄이 아님 (옛 판정을 새 sha 에 잇댈 수 없음)")
    return errs, gate, kind


def main():
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        if data.get("tool_name") != "AskUserQuestion":
            return 0
        cwd = data.get("cwd") or os.getcwd()
        repo = norm(os.environ.get("ASK_GATE_REPO", DEF_REPO))
        c = norm(cwd)
        if not (c == repo or c.startswith(repo + os.sep)):
            return 0
        qs = (data.get("tool_input") or {}).get("questions") or []
        q_headers = set(str(q.get("header", "")).strip() for q in qs)
        gate_dir = os.environ.get("ASK_GATE_DIR", DEF_DIR)
        base = os.environ.get("ASK_GATE_BASE", DEF_BASE)
        R = ask_gate_rules.load_rules()
        errs, gate, kind = evaluate(q_headers, gate_dir, base, R)
        if kind == "clarify" and gate:
            for q in qs:
                for o in q.get("options", []) or []:
                    if "(Recommended)" in str(o.get("label", "")):
                        errs.append("kind=clarify 인데 option label 에 '(Recommended)' 가 있음 (권고가 있으면 recommend 점검이 필요)")
        if errs:
            sys.stderr.write("AskUserQuestion 거부 -- 점검 미충족:\n")
            for e in errs:
                sys.stderr.write(" - %s\n" % e)
            sys.stderr.write("점검 파일: %s\n(양식: %s/TEMPLATE.md)\n" % (gate or gate_dir, gate_dir))
            return 2
        return 0
    except ask_gate_rules.RuleError as e:
        sys.stderr.write("ask_gate 거부(fail-closed) -- 원칙 26 형식을 읽지 못함: %s\n" % (e,))
        return 2
    except BaseException as e:  # fail-closed
        sys.stderr.write("ask_gate 예외로 거부(fail-closed): %r\n" % (e,))
        return 2


if __name__ == "__main__":
    sys.exit(main())
