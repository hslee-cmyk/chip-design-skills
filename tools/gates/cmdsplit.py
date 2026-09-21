"""EL1 명령 분해기 (05-role-separation design §6.2, review30 P1·P2, review31 N-08, review32 M-11).

`shlex`는 쓰지 않는다(따옴표 밖 줄바꿈을 공백으로 보고 `$'…'`를 못 읽는다). 따옴표와 이스케이프 상태를
추적하며 **따옴표 밖의** `;`·`&&`·`||`·`|`·`|&`·`&`·줄바꿈에서만 단순 명령으로 나눈다. 리다이렉트 안의 `&`
(`>&`, `<&`, `&>`, `&>>`, `N>&M`)는 구분자가 아니다. 명령 치환 `$(…)`·백틱·프로세스 치환 `<(…)`·`>(…)`
(PowerShell `$(…)`·`@(…)`)은 안쪽을 같은 분해기로 재귀 분해한다. heredoc은 구분자 줄까지를 데이터로
건너뛴다(따옴표 없는 구분자의 본문은 명령 치환만 재귀). 분해할 수 없으면(`$'…'`, 닫히지 않은 따옴표·괄호,
구분자를 찾지 못한 heredoc) `Unparseable`(위치 포함).
"""
from __future__ import annotations

from dataclasses import dataclass, field


class Unparseable(Exception):
    def __init__(self, pos, reason):
        super().__init__("명령을 분해하지 못함(위치 %d): %s" % (pos, reason))
        self.pos = pos
        self.reason = reason


SUB = "\x01"   # 단어 안의 치환·확장 자리 표지(해석할 수 없는 부분)


@dataclass
class Word:
    text: str = ""
    quoted: bool = False
    subst: bool = False      # 명령 치환·확장이 들었다(값을 모른다)
    assign_at: int = -1      # 따옴표 밖 `NAME=`의 `=` 위치(대입 단어), 없으면 -1


@dataclass
class Simple:
    words: list = field(default_factory=list)       # Word 목록(대입 제외)
    assigns: list = field(default_factory=list)     # (이름, Word)
    redirects: list = field(default_factory=list)   # (연산자, Word 또는 None)
    shell: str = "bash"

    def argv(self):
        return [w.text for w in self.words]


_REDIR_OPS = ("&>>", "&>", ">>", ">|", ">&", "<<<", "<<-", "<<", "<&", "<>", ">", "<")


def _heredoc_delim_at(s, i):
    """s[i:]가 `<<`·`<<-`로 시작하는 heredoc이면 (구분자, 탭 제거, 연산자 뒤 위치), 아니면 None.
    `<<<`(here-string)는 heredoc이 아니다."""
    if not s.startswith("<<", i) or s.startswith("<<<", i):
        return None
    j = i + 2
    strip = False
    if j < len(s) and s[j] == "-":
        strip = True
        j += 1
    while j < len(s) and s[j] in " \t":
        j += 1
    k = j
    delim = []
    while k < len(s) and s[k] not in " \t\n;&|<>()":
        if s[k] in "'\"":
            q = s[k]
            e = s.find(q, k + 1)
            if e < 0:
                return None
            delim.append(s[k + 1:e])
            k = e + 1
            continue
        if s[k] == "\\" and k + 1 < len(s):
            delim.append(s[k + 1])
            k += 2
            continue
        delim.append(s[k])
        k += 1
    if not delim:
        return None
    return "".join(delim), strip, k


def _skip_heredoc_bodies(s, i, pend):
    """줄바꿈 바로 뒤 위치 i에서 대기 중인 heredoc 본문들을 건너뛴다."""
    for delim, strip in pend:
        while True:
            if i >= len(s):
                raise Unparseable(i, "heredoc 구분자 %r 줄을 찾지 못함" % delim)
            j = s.find("\n", i)
            line = s[i:] if j < 0 else s[i:j]
            i = len(s) if j < 0 else j + 1
            if (line.lstrip("\t") if strip else line) == delim:
                break
    return i


def _find_close_paren(s, i, pos0):
    """s[i]는 '(' 바로 뒤. 짝 맞는 ')'의 위치. 따옴표·이스케이프·중첩 괄호·heredoc 본문·주석을 따른다
    (`$(cat <<'EOF' … EOF)` 본문의 짝 없는 따옴표를 따옴표로 읽지 않는다)."""
    depth = 1
    pend = []
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "\n":
            i += 1
            if pend:
                i = _skip_heredoc_bodies(s, i, pend)
                pend = []
            continue
        if c == "<":
            hd = _heredoc_delim_at(s, i)
            if hd is not None:
                pend.append((hd[0], hd[1]))
                i = hd[2]
                continue
        if c == "#" and (i == 0 or s[i - 1] in " \t\n;(|&"):
            j = s.find("\n", i)
            i = len(s) if j < 0 else j
            continue
        if c == "'":
            j = s.find("'", i + 1)
            if j < 0:
                raise Unparseable(i, "닫히지 않은 작은따옴표")
            i = j + 1
            continue
        if c == '"':
            i = _skip_dquote(s, i + 1)
            continue
        if c == "`":
            j = _find_backtick(s, i + 1)
            i = j + 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise Unparseable(pos0, "닫히지 않은 괄호")


def _skip_dquote(s, i):
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            return i + 1
        if c == "$" and i + 1 < len(s) and s[i + 1] == "(":
            i = _find_close_paren(s, i + 2, i) + 1
            continue
        if c == "`":
            i = _find_backtick(s, i + 1) + 1
            continue
        i += 1
    raise Unparseable(i, "닫히지 않은 큰따옴표")


def _find_backtick(s, i):
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == "`":
            return i
        i += 1
    raise Unparseable(i, "닫히지 않은 백틱")


def _find_brace(s, i, pos0):
    depth = 1
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "'":
            j = s.find("'", i + 1)
            if j < 0:
                raise Unparseable(i, "닫히지 않은 작은따옴표")
            i = j + 1
            continue
        if c == '"':
            i = _skip_dquote(s, i + 1)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise Unparseable(pos0, "닫히지 않은 중괄호")


def _unescape_backtick_body(b):
    out, i = [], 0
    while i < len(b):
        if b[i] == "\\" and i + 1 < len(b) and b[i + 1] in "`\\$":
            out.append(b[i + 1])
            i += 2
        else:
            out.append(b[i])
            i += 1
    return "".join(out)


# ================================================================ bash
def parse_bash(s: str):
    """단순 명령 목록(치환 안쪽 포함, 평탄화)."""
    out = []
    _parse_bash(s, out, 0)
    return out


def _parse_bash(s, out, depth):
    if depth > 20:
        raise Unparseable(0, "치환 중첩이 너무 깊다")
    cur = Simple(shell="bash")
    word = None
    pending_redir = None       # 대상을 기다리는 리다이렉트 연산자
    heredocs = []              # (구분자, 따옴표 여부, 탭 제거)
    paren = 0
    i, n = 0, len(s)

    def nested(text):
        _parse_bash(text, out, depth + 1)

    def end_word():
        nonlocal word, pending_redir
        if word is None:
            return
        w = word
        word = None
        if pending_redir is not None:
            op = pending_redir
            pending_redir = None
            if op in ("<<", "<<-"):
                heredocs.append((w.text, w.quoted, op == "<<-"))
                cur.redirects.append((op, w))
                return
            if op in (">&", "<&") and (w.text.isdigit() or w.text == "-"):
                cur.redirects.append((op, None))
                return
            cur.redirects.append((op, w))
            return
        if not cur.words and w.assign_at >= 0:
            name, val = w.text[:w.assign_at], w.text[w.assign_at + 1:]
            cur.assigns.append((name, Word(val, w.quoted, w.subst)))
            return
        cur.words.append(w)

    def end_cmd():
        nonlocal cur
        end_word()
        if pending_redir is not None:
            raise Unparseable(i, "리다이렉트 대상이 없다")
        if cur.words or cur.assigns or cur.redirects:
            out.append(cur)
        cur = Simple(shell="bash")

    def w():
        nonlocal word
        if word is None:
            word = Word()
        return word

    while i < n:
        c = s[i]
        if c in " \t":
            end_word()
            i += 1
            continue
        if c == "\n":
            end_cmd()
            i += 1
            if heredocs:
                i = _consume_heredocs(s, i, heredocs, nested)
                heredocs = []
            continue
        if c == "\\":
            if i + 1 < n and s[i + 1] == "\n":   # 줄 이음
                i += 2
                continue
            if i + 1 >= n:
                i += 1
                continue
            w().text += s[i + 1]
            word.quoted = True
            i += 2
            continue
        if c == "'":
            j = s.find("'", i + 1)
            if j < 0:
                raise Unparseable(i, "닫히지 않은 작은따옴표")
            w().text += s[i + 1:j]
            word.quoted = True
            i = j + 1
            continue
        if c == '"':
            i = _dquote_into(s, i + 1, w(), nested)
            word.quoted = True
            continue
        if c == "$":
            nx = s[i + 1] if i + 1 < n else ""
            if nx == "'":
                raise Unparseable(i, "`$'…'` 인용은 분해하지 않는다")
            if nx == '"':
                i = _dquote_into(s, i + 2, w(), nested)
                word.quoted = True
                continue
            if s.startswith("$((", i):
                j = _find_close_paren(s, i + 2, i)
                w().text += SUB
                word.subst = True
                nested_arith = s[i + 3:j]
                _scan_substs(nested_arith, nested)
                i = j + 1
                if i < n and s[i] == ")":
                    i += 1
                continue
            if nx == "(":
                j = _find_close_paren(s, i + 2, i)
                nested(s[i + 2:j])
                w().text += SUB
                word.subst = True
                i = j + 1
                continue
            if nx == "{":
                j = _find_brace(s, i + 2, i)
                _scan_substs(s[i + 2:j], nested)
                w().text += "${" + s[i + 2:j] + "}"
                word.subst = True
                i = j + 1
                continue
            w().text += "$"
            if nx and (nx.isalnum() or nx in "_?@*#!-$"):
                word.subst = True
            i += 1
            continue
        if c == "`":
            j = _find_backtick(s, i + 1)
            nested(_unescape_backtick_body(s[i + 1:j]))
            w().text += SUB
            word.subst = True
            i = j + 1
            continue
        if c in "<>" and i + 1 < n and s[i + 1] == "(" and (word is None):
            j = _find_close_paren(s, i + 2, i)
            nested(s[i + 2:j])
            w().text += SUB
            word.subst = True
            i = j + 1
            continue
        if c == "#" and word is None:
            j = s.find("\n", i)
            i = n if j < 0 else j
            continue
        # 리다이렉트: 단어 시작이거나 단어가 숫자뿐(파일 기술자)일 때
        if c in "<>" or (c == "&" and i + 1 < n and s[i + 1] == ">"):
            if word is None or (word.text.isdigit() and not word.quoted):
                op = next(o for o in _REDIR_OPS if s.startswith(o, i))
                word = None   # 파일 기술자 번호는 연산자의 일부
                if pending_redir is not None:
                    raise Unparseable(i, "리다이렉트 대상이 없다")
                pending_redir = op
                i += len(op)
                continue
        if c == "&":
            end_word()
            if s.startswith("&&", i):
                end_cmd()
                i += 2
                continue
            end_cmd()
            i += 1
            continue
        if c == "|":
            end_cmd()
            if s.startswith("||", i) or s.startswith("|&", i):
                i += 2
            else:
                i += 1
            continue
        if c == ";":
            end_cmd()
            i += 2 if s.startswith(";;", i) else 1
            continue
        if c == "(" and word is None:
            end_cmd()
            paren += 1
            i += 1
            continue
        if c == ")" and word is None or (c == ")" and paren > 0):
            end_cmd()
            paren -= 1
            if paren < 0:
                raise Unparseable(i, "짝 없는 닫는 괄호")
            i += 1
            continue
        x = w()
        if c == "=" and x.assign_at < 0 and not x.quoted and not x.subst and _is_assign(x.text):
            x.assign_at = len(x.text)
        x.text += c
        i += 1
    end_cmd()
    if heredocs:
        raise Unparseable(n, "heredoc 구분자 줄을 찾지 못함")
    if paren != 0:
        raise Unparseable(n, "닫히지 않은 괄호")
    return out


def _is_assign(name):
    return bool(name) and (name[0].isalpha() or name[0] == "_") and all(ch.isalnum() or ch == "_" for ch in name)


def _dquote_into(s, i, word, nested):
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            nx = s[i + 1]
            if nx == "\n":
                i += 2
                continue
            if nx in '$`"\\':
                word.text += nx
                i += 2
                continue
            word.text += "\\"
            i += 1
            continue
        if c == '"':
            return i + 1
        if c == "$" and i + 1 < n and s[i + 1] == "(":
            if s.startswith("$((", i):
                j = _find_close_paren(s, i + 2, i)
                _scan_substs(s[i + 3:j], nested)
                word.text += SUB
                word.subst = True
                i = j + 1
                if i < n and s[i] == ")":
                    i += 1
                continue
            j = _find_close_paren(s, i + 2, i)
            nested(s[i + 2:j])
            word.text += SUB
            word.subst = True
            i = j + 1
            continue
        if c == "$" and i + 1 < n and s[i + 1] == "{":
            j = _find_brace(s, i + 2, i)
            _scan_substs(s[i + 2:j], nested)
            word.text += "${" + s[i + 2:j] + "}"
            word.subst = True
            i = j + 1
            continue
        if c == "$" and i + 1 < n and (s[i + 1].isalnum() or s[i + 1] in "_?@*#!-$"):
            word.subst = True
        if c == "`":
            j = _find_backtick(s, i + 1)
            nested(_unescape_backtick_body(s[i + 1:j]))
            word.text += SUB
            word.subst = True
            i = j + 1
            continue
        word.text += c
        i += 1
    raise Unparseable(i, "닫히지 않은 큰따옴표")


def _scan_substs(text, nested):
    """데이터(heredoc 본문, `${…}` 안) 안의 명령 치환만 찾아 재귀 판정."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "$" and i + 1 < n and text[i + 1] == "(":
            j = _find_close_paren(text, i + 2, i)
            if not text.startswith("$((", i):
                nested(text[i + 2:j])
            i = j + 1
            continue
        if c == "`":
            j = _find_backtick(text, i + 1)
            nested(_unescape_backtick_body(text[i + 1:j]))
            i = j + 1
            continue
        i += 1


def _consume_heredocs(s, i, heredocs, nested):
    for delim, quoted, strip_tabs in heredocs:
        body = []
        while True:
            if i >= len(s):
                raise Unparseable(i, "heredoc 구분자 %r 줄을 찾지 못함" % delim)
            j = s.find("\n", i)
            line = s[i:] if j < 0 else s[i:j]
            i = len(s) if j < 0 else j + 1
            cmp = line.lstrip("\t") if strip_tabs else line
            if cmp == delim:
                break
            body.append(line)
        if not quoted:
            _scan_substs("\n".join(body), nested)
    return i


# ================================================================ PowerShell
def parse_powershell(s: str):
    out = []
    _parse_ps(s, out, 0)
    return out


_PS_REDIR = ("*>>", "*>", "2>>", "2>&1", "1>>", "1>&2", "3>>", "4>>", "5>>", "6>>", "2>", "1>", "3>", "4>", "5>", "6>",
             ">>", ">")


def _parse_ps(s, out, depth):
    if depth > 20:
        raise Unparseable(0, "치환 중첩이 너무 깊다")
    cur = Simple(shell="powershell")
    word = None
    pending = None
    i, n = 0, len(s)

    def nested(text):
        _parse_ps(text, out, depth + 1)

    def w():
        nonlocal word
        if word is None:
            word = Word()
        return word

    def end_word():
        nonlocal word, pending
        if word is None:
            return
        x = word
        word = None
        if pending is not None:
            cur.redirects.append((pending, x))
            pending = None
            return
        cur.words.append(x)

    def end_cmd():
        nonlocal cur
        end_word()
        if pending is not None:
            raise Unparseable(i, "리다이렉트 대상이 없다")
        if cur.words or cur.redirects:
            out.append(cur)
        cur = Simple(shell="powershell")

    while i < n:
        c = s[i]
        if c in " \t\r":
            end_word()
            i += 1
            continue
        if c == "\n" or c == ";":
            end_cmd()
            i += 1
            continue
        if c == "`":
            if i + 1 < n and s[i + 1] == "\n":
                i += 2
                continue
            if i + 1 < n:
                w().text += s[i + 1]
                word.quoted = True
            i += 2
            continue
        if s.startswith("@'", i) and (i + 2 < n and s[i + 2] in "\r\n"):
            j = s.find("\n'@", i)
            if j < 0:
                raise Unparseable(i, "닫히지 않은 here-string")
            w().text += s[i + 2:j].lstrip("\r\n")
            word.quoted = True
            i = j + 3
            continue
        if s.startswith('@"', i) and (i + 2 < n and s[i + 2] in "\r\n"):
            j = s.find('\n"@', i)
            if j < 0:
                raise Unparseable(i, "닫히지 않은 here-string")
            body = s[i + 2:j]
            _ps_scan_subexpr(body, nested)
            w().text += body.lstrip("\r\n")
            word.quoted = True
            word.subst = word.subst or "$" in body
            i = j + 3
            continue
        if c == "'":
            j = i + 1
            buf = []
            while True:
                k = s.find("'", j)
                if k < 0:
                    raise Unparseable(i, "닫히지 않은 작은따옴표")
                buf.append(s[j:k])
                if k + 1 < n and s[k + 1] == "'":
                    buf.append("'")
                    j = k + 2
                    continue
                j = k + 1
                break
            w().text += "".join(buf)
            word.quoted = True
            i = j
            continue
        if c == '"':
            i = _ps_dquote(s, i + 1, w(), nested)
            word.quoted = True
            continue
        if (c == "$" or c == "@") and i + 1 < n and s[i + 1] == "(":
            j = _find_close_paren(s, i + 2, i)
            nested(s[i + 2:j])
            w().text += SUB
            word.subst = True
            i = j + 1
            continue
        if c == "$":
            w().text += "$"
            word.subst = True
            i += 1
            continue
        if c == "#" and word is None:
            j = s.find("\n", i)
            i = n if j < 0 else j
            continue
        if s.startswith("<#", i):
            j = s.find("#>", i)
            if j < 0:
                raise Unparseable(i, "닫히지 않은 블록 주석")
            i = j + 2
            continue
        if word is None and c in "*123456>":
            op = next((o for o in _PS_REDIR if s.startswith(o, i)), None)
            if op is not None:
                if op in ("2>&1", "1>&2"):
                    cur.redirects.append((op, None))
                else:
                    pending = op
                i += len(op)
                continue
        if c == "|":
            end_cmd()
            i += 2 if s.startswith("||", i) else 1
            continue
        if s.startswith("&&", i):
            end_cmd()
            i += 2
            continue
        if c in "({":
            end_word()
            j = _find_close_paren(s, i + 1, i) if c == "(" else _find_brace(s, i + 1, i)
            nested(s[i + 1:j])
            i = j + 1
            continue
        if c in ")}":
            raise Unparseable(i, "짝 없는 닫는 괄호")
        w().text += c
        i += 1
    end_cmd()
    return out


def _ps_dquote(s, i, word, nested):
    n = len(s)
    while i < n:
        c = s[i]
        if c == "`" and i + 1 < n:
            word.text += s[i + 1]
            i += 2
            continue
        if c == '"':
            if i + 1 < n and s[i + 1] == '"':
                word.text += '"'
                i += 2
                continue
            return i + 1
        if c == "$" and i + 1 < n and s[i + 1] == "(":
            j = _find_close_paren(s, i + 2, i)
            nested(s[i + 2:j])
            word.text += SUB
            word.subst = True
            i = j + 1
            continue
        if c == "$":
            word.subst = True
        word.text += c
        i += 1
    raise Unparseable(i, "닫히지 않은 큰따옴표")


def _ps_scan_subexpr(text, nested):
    i = 0
    while i < len(text):
        if text[i] == "$" and i + 1 < len(text) and text[i + 1] == "(":
            j = _find_close_paren(text, i + 2, i)
            nested(text[i + 2:j])
            i = j + 1
            continue
        i += 1
