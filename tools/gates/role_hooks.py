"""역할 hook 판정 (05-role-separation design §5·§6·§7, §3.3 세션 시작).

얇은 실행기(`hooks/role_*.py`)가 gate master 판 게이트 코드 캐시를 풀고 이 모듈의 `run(event, payload,
cache_dir)`을 부른다. 반환 (exit code, 메시지): 0 통과 / 2 거부(Claude Code는 exit 2로만 막는다).

* EL1 PreToolUse(`role_guard.py`): §6 -- 도구 대상의 쓰기 경로 판정, Bash·PowerShell 명령 판정(§6.2),
  고정 규칙(§6.3), test-author 소스 열람 거부(§6.4). 역할 Bash는 EL2용 메인 worktree 상태를 기록한다.
* EL2 PostToolUse(Bash)(`role_diff_guard_bash.py`)·SubagentStop(`role_diff_guard_stop.py`): §7.
* SessionStart(`role_session_start.py`): §3.3 행 1~6 대조, `status-*.json` 잔여 삭제, 감사 로그 출력.
"""
from __future__ import annotations

import glob as globmod
import json
import os
import re

import cmdsplit
import integrity
import merge_gate as mg
import role_paths as rp

GateError = rp.GateError
ORCH = "오케스트레이터"
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
READ_TOOLS = ("Read", "Grep", "Glob")


class Deny(Exception):
    pass


# ================================================================ 주체(§5)
def actor_of(agent_type):
    """(주체, agent_type). `gmid-`로 시작하는데 세 역할이 아니면 거부."""
    if not agent_type:
        return ORCH
    if agent_type in rp.ROLE_OF_AGENT:
        return agent_type
    if agent_type.startswith("gmid-"):
        raise Deny("알 수 없는 역할 agent_type=%r(gmid- 접두인데 세 역할이 아니다)" % agent_type)
    return ORCH


class HC:
    """hook 한 번의 판정 문맥."""

    def __init__(self, env: rp.Env, actor, payload, cache_dir):
        self.env = env
        self.actor = actor
        self.payload = payload
        self.cache_dir = rp.norm_abs(cache_dir) if cache_dir else None
        self.cwd = rp.norm_abs(payload.get("cwd") or os.getcwd())
        self.in_scope = False
        self.marker = os.path.exists(os.path.join(env.cache_root, rp.INTEGRITY_MARKER))
        self._gate_change = {}

    @property
    def is_role(self):
        return self.actor in rp.ROLE_OF_AGENT

    @property
    def role_short(self):
        return rp.ROLE_OF_AGENT.get(self.actor)

    def gate_change_ok(self, cid):
        if cid not in self._gate_change:
            base = mg.TreeView(self.env.gate_args(), self.env.gate_master) if self.env.source == "gate" \
                else mg.TreeView(["-C", self.env.main_root], "HEAD")
            self._gate_change[cid] = mg.gate_change_ok(base, cid)
        return self._gate_change[cid]

    def scope(self):
        self.in_scope = True
        if self.marker:
            raise Deny("무결성 대조 실패 표지(integrity-failed)가 있어 판정 범위의 모든 호출을 거부한다. "
                       + integrity.RECOVERY)


def branch_of(root):
    rc, out = rp.git_try(["-C", root, "symbolic-ref", "--short", "-q", "HEAD"])
    return out.decode().strip() if rc == 0 else None


def _fmt_deny(hc, target, v: rp.Verdict):
    row = ("%s | %s | %s | %s" % (v.rule.actor, v.rule.glob, v.rule.exclude or "--", v.rule.condition)) if v.rule \
        else "맞는 행 없음"
    globs = rp.globs_of(hc.actor, hc.env.rules)
    return ("[EL1 거부] 주체 %s, 대상 %s\n  판정 행: %s\n  사유: %s\n  이 주체가 쓸 수 있는 glob: %s"
            % (hc.actor, target, row, v.reason, "; ".join(globs) if globs else "(없음)"))


# ================================================================ 쓰기 대상 판정(§6.1-5, §5.1, §6.3)
def judge_write(hc: HC, abs_path: str, how="도구 쓰기"):
    a = rp.norm_abs(abs_path, hc.cwd)
    env = hc.env
    if rp.is_under(a, env.common_dir) or (env.gate_path and rp.is_under(a, env.gate_path)):
        hc.scope()
        raise Deny("[EL1 거부] 저장소 내부(%s) 쓰기: %s (%s)" % ("gate" if env.gate_path and rp.is_under(a, env.gate_path)
                                                           else "git-common-dir", a, how))
    wt = rp.worktree_of(a)
    if wt is None or rp.ncase(wt[1]) != rp.ncase(env.common_dir):
        # DESIGN-GAP: §5 "역할: 모든 쓰기" — 작업 저장소의 어느 worktree에도 속하지 않는 경로($TEMP의 격리 복제본 등)는
        # 쓰기 경로표의 정의역 밖이라 판정하지 않는다(§4.1: 그런 경로는 overlaps_any 거짓).
        return
    root = wt[0]
    rel = rp.rel_to(a, root)
    br = branch_of(root)
    rinfo = rp.role_of_branch(br)
    fixed = rel.casefold()
    if fixed.startswith(".claude/hooks/") or re.fullmatch(r"\.claude/settings[^/]*\.json", fixed) or fixed.startswith(".githooks/"):
        hc.scope()
        raise Deny("[EL1 거부] 고정 규칙(§6.3): %s는 모든 주체의 도구 쓰기 거부(사용자 경로)" % rel)
    if hc.is_role:
        hc.scope()
        if rinfo is None or rinfo[0] != hc.role_short:
            raise Deny("[EL1 거부] 주체 %s가 자기 역할 worktree(role/%s/<id>) 밖에 쓴다: %s (worktree %s, 브랜치 %s)"
                       % (hc.actor, hc.role_short, a, root, br or "detached"))
        cid = rinfo[1]
    else:
        if rinfo is not None:
            hc.scope()
            raise Deny("[EL1 거부] 오케스트레이터는 역할 worktree에 쓰지 못한다(§5.1): %s" % a)
        if not rp.overlaps_any(rel, env.rules):
            return
        hc.scope()
        cid = None
    ctx = rp.WriteContext(rules=env.rules, change_id=cid, bootstrapped=env.bootstrapped,
                          gate_change_ok=hc.gate_change_ok(cid) if cid else False)
    v = rp.allowed(hc.actor, rel, ctx)
    if not v.ok:
        raise Deny(_fmt_deny(hc, "%s (%s)" % (rel, how), v))


# ================================================================ §6.4 test-author 소스 열람 거부
def judge_read(hc: HC, tool, ti):
    if hc.actor != "gmid-test-author":
        return
    hc.scope()
    if tool == "Read":
        targets = [(ti.get("file_path") or "", False)]
    elif tool == "Grep":
        targets = [(ti.get("path") or "", True)]
    else:
        base = ti.get("path") or ""
        pat = (ti.get("pattern") or "").replace("\\", "/")
        pre = re.split(r"[*?\[{]", pat, 1)[0]
        pre = pre.rsplit("/", 1)[0] if "/" in pre else ""
        targets = [(base, True)]
        if pre:
            targets.append((os.path.join(base or hc.cwd, pre) if not re.match(r"^[a-zA-Z]:|^/", pre) else pre, True))
    for t, maybe_dir in targets:
        a = rp.norm_abs(t or hc.cwd, hc.cwd)
        wt = rp.worktree_of(a)
        if wt is None or rp.ncase(wt[1]) != rp.ncase(hc.env.common_dir):
            continue
        rel = rp.rel_to(a, wt[0])
        if (not t) and tool != "Read":
            rel = ""     # path 없음 = 대상 worktree 루트 전체
        if rp.classify(rel) == "source":
            raise Deny("[EL1 거부] test-author의 소스 열람(DEC-38): %s %s" % (tool, rel))
        if (maybe_dir and (os.path.isdir(a) or rel == "")) and rp.dir_contains_source(rel):
            raise Deny("[EL1 거부] test-author의 소스 포함 디렉터리 열람(DEC-38): %s %s" % (tool, rel or "(worktree 루트)"))


# ================================================================ §6.2 명령 판정
PY_RE = re.compile(r"^(python(\d+(\.\d+)*)?|py)(\.exe)?$", re.I)
WRAPPERS = ("command", "builtin", "exec", "nohup", "time", "nice", "env", "sudo")
READ_SUBS = {"status", "diff", "log", "show", "rev-parse", "ls-files", "ls-tree", "cat-file", "blame", "grep",
             "describe", "show-ref", "for-each-ref", "merge-base", "rev-list", "name-rev", "shortlog", "check-ignore",
             "check-attr", "whatchanged", "var", "help", "version", "count-objects", "verify-commit", "diff-tree",
             "diff-index", "diff-files", "interpret-trailers", "cherry", "range-diff", "annotate", "show-branch",
             "ls-remote", "check-ref-format", "get-tar-commit-id", "fsck", "bugreport"}
REF_MOVE = ("update-ref", "commit-tree", "write-tree", "replace", "filter-branch", "rebase", "am", "cherry-pick",
            "revert", "stash", "reset", "update-index", "filter-repo")
CONFIG_READ_FLAGS = {"--get", "--get-all", "--get-regexp", "--get-urlmatch", "--list", "-l", "--get-color",
                     "--get-colorbool"}
CONFIG_WRITE_FLAGS = {"--unset", "--unset-all", "--add", "--replace-all", "--rename-section", "--remove-section",
                      "-e", "--edit"}
CONFIG_VALUE_OPTS = {"--file", "-f", "--blob", "--type", "--default", "--comment", "--value"}
WRITE_REDIR = (">", ">>", ">|", "&>", "&>>", "<>", "*>", "*>>", "2>", "2>>", "1>", "1>>", "3>", "4>", "5>", "6>",
               "3>>", "4>>", "5>>", "6>>", ">&")


def _brace_expand(t):
    m = re.search(r"\{([^{}]*,[^{}]*)\}", t)
    if not m:
        return [t]
    out = []
    for part in m.group(1).split(","):
        out += _brace_expand(t[:m.start()] + part + t[m.end():])
    return out


_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)|\$env:([A-Za-z_][A-Za-z0-9_]*)", re.I)


def expand(word: cmdsplit.Word, vars_):
    """단어 값(변수 확장 뒤) 또는 None(해석 불가: 명령 치환·모르는 변수)."""
    t = word.text
    if cmdsplit.SUB in t:
        return None
    if word.subst:
        def rep(m):
            name = m.group(1) or m.group(2) or m.group(3)
            if name in vars_:
                return vars_[name]
            v = os.environ.get(name)
            if v is None:
                raise KeyError(name)
            return v
        try:
            t = _VAR_RE.sub(rep, t)
        except KeyError:
            return None
        if "$" in t:
            return None
    if t.startswith("~") and not word.quoted and (len(t) == 1 or t[1] in "/\\"):
        t = os.path.expanduser("~") + t[1:]
    return t


class CmdState:
    def __init__(self, hc):
        self.hc = hc
        self.vars = {}
        self.cwd = hc.cwd
        self.cd_seen = False


def _looks_path(s):
    return bool(s) and "\n" not in s and "://" not in s and not s.startswith("-")


def _in_cache(hc, a):
    root = hc.env.cache_root
    if not rp.is_under(a, root):
        return False
    rest = rp.ncase(a)[len(rp.ncase(root)) + 1:]
    return bool(re.match(r"^[0-9a-f]{40}(/|$)", rest))


def _points_inside(hc, st, s):
    """문자열이 git-common-dir·gate 안을 가리키면 그 절대 경로, 아니면 None."""
    if not _looks_path(s):
        return None
    try:
        cands = [rp.norm_abs(s, st.cwd)]
        if st.cwd != hc.cwd:
            cands.append(rp.norm_abs(s, hc.cwd))
    except GateError:
        return None
    for a in cands:
        if rp.is_under(a, hc.env.common_dir) or (hc.env.gate_path and rp.is_under(a, hc.env.gate_path)):
            return a
    return None


def _check_pointing(hc, st, sc, argv, exempt):
    """'저장소 내부' 규칙: 인자·`--opt=값`·대입 값·리다이렉트가 git-common-dir·gate를 가리키면 거부.
    exempt: 캐시 읽기·실행으로 허용하는 단어 위치 집합(인덱스)과 대입 이름."""
    for idx, s in enumerate(argv):
        if s is None:
            continue
        vals = [s]
        if s.startswith("-") and "=" in s:
            vals = [s.split("=", 1)[1]]
        elif re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", s):
            vals = [s.split("=", 1)[1]]
        for v in vals:
            a = _points_inside(hc, st, v)
            if a is None:
                continue
            if idx in exempt and _in_cache(hc, a):
                continue
            hc.scope()
            raise Deny("[EL1 거부] 저장소 내부를 가리키는 인자: %r (%s)" % (s, a))
    for name, w in sc.assigns:
        val = expand(w, st.vars)
        if val is None:
            continue
        elems = val.split(";") if name.upper() == "PYTHONPATH" else [val]
        for k, e in enumerate(elems):
            a = _points_inside(hc, st, e)
            if a is None:
                continue
            if name.upper() == "PYTHONPATH" and k == 0 and _in_cache(hc, a):
                continue
            hc.scope()
            raise Deny("[EL1 거부] 저장소 내부를 가리키는 대입: %s=%r" % (name, val))


def _python_exempt(hc, argv, pythonpath_first_cache):
    """캐시를 읽기·실행하는 두 형태(§6.2 review31 N-07)와 V1의 `-c <캐시>/pytest_gate.ini`.
    반환: 허용할 단어 인덱스 집합. `-m`·`-c`(코드) 실행에 캐시 PYTHONPATH면 `-P` 필수."""
    ex = set()
    i = 1
    opts = []
    while i < len(argv):
        a = argv[i]
        if a in ("-m", "-c"):
            opts.append(a)
            break
        if a in ("-W", "-X", "--check-hash-based-pycs"):
            i += 2
            continue
        if a is not None and a.startswith("-") and a != "-":
            opts.append(a)
            i += 1
            continue
        # 스크립트 인자 -- 해석 못 하는 값(모르는 변수 등, D-10)은 예외로 끝내지 않는다: 예외 없이 못 받은 값으로 판정(비예외)
        if a is not None and a.lower().endswith(".py"):
            ex.add(i)
        break
    has_P = any(o == "-P" or (o.startswith("-") and not o.startswith("--") and "P" in o[1:]) for o in opts)
    runs_mc = "-m" in opts or "-c" in opts
    if pythonpath_first_cache and runs_mc and not has_P:
        raise Deny("[EL1 거부] 캐시 판 게이트 코드를 PYTHONPATH로 쓰는 `-m`·`-c` 실행에는 `-P`가 필요하다(§0, review33 M2-01)")
    if "-m" in opts and i + 1 < len(argv) and argv[i + 1] == "pytest":
        # DESIGN-GAP: §6.2는 캐시 예외를 두 형태로만 적었지만 §12-7 V1 명령의 `-c <캐시>/pytest_gate.ini`가 정상 흐름이다.
        # 그 값(파일 이름 pytest_gate.ini)만 읽기로 허용한다(정상 흐름 오거부 방지).
        for j in range(i + 2, len(argv) - 1):
            if argv[j] == "-c" and argv[j + 1] and os.path.basename(argv[j + 1].replace("\\", "/")) == "pytest_gate.ini":
                ex.add(j + 1)
    return ex


def _unwrap(argv):
    while argv:
        h = os.path.basename((argv[0] or "").replace("\\", "/")).lower()
        if h in WRAPPERS:
            argv = argv[1:]
            if h == "env":
                while argv and argv[0] is not None and (argv[0].startswith("-") or re.match(r"^[A-Za-z_]\w*=", argv[0])):
                    argv = argv[1:]
            elif h in ("nice", "sudo"):
                while argv and argv[0] is not None and argv[0].startswith("-"):
                    argv = argv[1:]
            continue
        if h == "&":   # PowerShell 호출 연산자
            argv = argv[1:]
            continue
        break
    return argv


def judge_command_string(hc: HC, text: str, shell: str, st: CmdState | None = None, depth=0):
    if depth > 5:
        raise Deny("[EL1 거부] 셸 중첩이 너무 깊다")
    try:
        cmds = cmdsplit.parse_bash(text) if shell == "bash" else cmdsplit.parse_powershell(text)
    except cmdsplit.Unparseable as e:
        hc.scope()
        raise Deny("[EL1 거부] %s" % e)
    st = st or CmdState(hc)
    for sc in cmds:
        judge_simple(hc, st, sc, depth)


def _env_assign_names(sc, argv):
    names = [n for n, _ in sc.assigns]
    for a in argv:
        if a and re.match(r"^[A-Za-z_]\w*=", a):
            names.append(a.split("=", 1)[0])
        if a and re.match(r"^\$env:([A-Za-z_]\w*)$", a, re.I):
            names.append(re.match(r"^\$env:([A-Za-z_]\w*)$", a, re.I).group(1))
    return names


def judge_simple(hc: HC, st: CmdState, sc: cmdsplit.Simple, depth):
    raw_argv = []
    for w in sc.words:
        v = expand(w, st.vars)
        if v is not None and not w.quoted and "{" in v and "," in v:
            raw_argv += _brace_expand(v)
        else:
            raw_argv.append(v)
    # 검사 끄기: GIT_CONFIG_* 환경 변수(대입·export·$env:)
    for name in _env_assign_names(sc, [a for a in raw_argv if a]):
        if name.upper().startswith("GIT_CONFIG"):
            hc.scope()
            raise Deny("[EL1 거부] 검사 끄기: 환경 변수 %s" % name)
    if "--no-verify" in [a for a in raw_argv if a]:
        hc.scope()
        raise Deny("[EL1 거부] 검사 끄기: --no-verify")
    # PowerShell 대입 `$env:NAME = 값`
    # 이름은 확장 전 원문으로 본다: 확장하면 `$env:PYTHONPATH`가 현재 값(또는 None)이 되어 대입으로 인식되지 않았다
    # (공격 10c allow-ps-pythonpath-cache 오거부, §6.2 review32 M-09).
    if sc.shell == "powershell" and len(sc.words) >= 3 and sc.words[1].text == "=" \
            and re.fullmatch(r"\$env:[A-Za-z_][A-Za-z0-9_]*", sc.words[0].text, re.I):
        name = sc.words[0].text[5:]
        val = expand(sc.words[2], st.vars)
        if name.upper().startswith("GIT_CONFIG"):
            hc.scope()
            raise Deny("[EL1 거부] 검사 끄기: 환경 변수 %s" % name)
        fake = cmdsplit.Simple(assigns=[(name, cmdsplit.Word(val or cmdsplit.SUB))], shell="powershell")
        _check_pointing(hc, st, fake, [], set())
        if val is not None:
            st.vars[name] = val
        return
    argv = _unwrap(raw_argv)
    pp_first_cache = False
    for n, w in sc.assigns:
        if n.upper() == "PYTHONPATH":
            v = expand(w, st.vars)
            if v is not None:
                a0 = rp.norm_abs(v.split(";")[0], st.cwd) if _looks_path(v.split(";")[0]) else None
                pp_first_cache = bool(a0) and _in_cache(hc, a0)
    if not argv and not sc.redirects:
        for n, w in sc.assigns:
            v = expand(w, st.vars)
            if v is not None:
                st.vars[n] = v
    # 명령 이름
    cmd = os.path.basename((argv[0] or "").replace("\\", "/")).lower() if argv and argv[0] else ""
    exempt = set()
    offset = len(raw_argv) - len(argv)
    if cmd and PY_RE.match(cmd):
        exempt = {offset + i for i in _python_exempt(hc, argv, pp_first_cache)}
    _check_pointing(hc, st, sc, raw_argv, exempt)
    # 리다이렉트
    for op, tw in sc.redirects:
        if tw is None or op in ("<<", "<<-", "<<<"):
            continue
        t = expand(tw, st.vars)
        if op in WRITE_REDIR:
            if t is not None and t.replace("\\", "/") in ("/dev/null", "nul", "$null", "NUL"):
                continue
            _write_target(hc, st, t, "리다이렉트 %s" % op)
        elif t is not None:
            a = _points_inside(hc, st, t)
            if a is not None:
                hc.scope()
                raise Deny("[EL1 거부] 저장소 내부를 가리키는 리다이렉트: %s" % a)
    if not argv or argv[0] is None:
        if argv and argv[0] is None:
            hc.scope()
            raise Deny("[EL1 거부] 명령 이름을 해석하지 못함(명령 치환·모르는 변수)")
        return
    if cmd in ("cd", "pushd", "popd", "set-location", "sl", "push-location"):
        st.cd_seen = True
        if len(argv) >= 2 and argv[1] is not None and not argv[1].startswith("-"):
            st.cwd = rp.norm_abs(argv[1], st.cwd)
        return
    if cmd in ("git", "git.exe"):
        judge_git(hc, st, argv)
        return
    if cmd in ("bash", "sh", "zsh", "bash.exe", "sh.exe") and "-c" in argv:
        k = argv.index("-c")
        if k + 1 < len(argv):
            if argv[k + 1] is None:
                hc.scope()
                raise Deny("[EL1 거부] `%s -c`의 명령을 해석하지 못함" % cmd)
            judge_command_string(hc, argv[k + 1], "bash", None, depth + 1)
        return
    if cmd == "eval":
        if any(a is None for a in argv[1:]):
            hc.scope()
            raise Deny("[EL1 거부] eval 인자를 해석하지 못함")
        judge_command_string(hc, " ".join(argv[1:]), "bash", st, depth + 1)
        return
    if cmd in ("powershell", "pwsh", "powershell.exe", "pwsh.exe"):
        for k, a in enumerate(argv):
            if a and a.lower() in ("-command", "-c") and k + 1 < len(argv):
                if hc.is_role:
                    hc.scope()
                    raise Deny("[EL1 거부] 역할은 PowerShell을 쓰지 않는다")
                if argv[k + 1] is None:
                    hc.scope()
                    raise Deny("[EL1 거부] PowerShell 명령을 해석하지 못함")
                judge_command_string(hc, " ".join(x or "" for x in argv[k + 1:]), "powershell", None, depth + 1)
            elif a and a.lower() in ("-encodedcommand", "-enc", "-e", "-ec"):
                hc.scope()
                raise Deny("[EL1 거부] 인코딩된 PowerShell 명령은 판정하지 않는다")
        return
    judge_file_writers(hc, st, sc.shell, cmd, argv)


# ---------------------------------------------------------------- 쓰기 대상 명령
PS_WRITE = {
    "set-content": "content", "sc": "content", "add-content": "content", "ac": "content",
    "out-file": "content", "new-item": "new", "ni": "new", "md": "new", "mkdir": "new",
    "remove-item": "remove", "ri": "remove", "rm": "remove", "rmdir": "remove", "del": "remove", "erase": "remove",
    "rd": "remove", "copy-item": "copy", "cp": "copy", "copy": "copy", "cpi": "copy",
    "move-item": "move", "mv": "move", "move": "move", "mi": "move",
}
PS_SWITCHES = ("force", "recurse", "append", "nonewline", "whatif", "confirm", "passthru", "noclobber", "container",
               "asbytestream")


def _write_target(hc, st, t, how):
    if t is None:
        hc.scope()
        raise Deny("[EL1 거부] 쓰기 대상을 해석하지 못함(%s): 명령 치환·모르는 변수" % how)
    t = t.replace("\\", "/") if not t.startswith("\\\\") else t
    if st.cd_seen and not re.match(r"^[a-zA-Z]:/|^/", t):
        hc.scope()
        raise Deny("[EL1 거부] `cd` 뒤의 상대 경로 쓰기 대상은 해석하지 않는다(§5.1): %s" % t)
    targets = [t]
    if any(ch in t for ch in "*?["):
        targets += [p.replace("\\", "/") for p in globmod.glob(rp.norm_abs(t, st.cwd))]
    for x in targets:
        judge_write(hc, rp.norm_abs(x, st.cwd), how)


def _nonopt(args, value_opts=()):
    out, i, ddash = [], 0, False
    while i < len(args):
        a = args[i]
        if not ddash and a == "--":
            ddash = True
            i += 1
            continue
        if not ddash and a is not None and a.startswith("-") and a != "-":
            if a in value_opts:
                i += 2
                continue
            i += 1
            continue
        out.append(a)
        i += 1
    return out


def judge_file_writers(hc, st, shell, cmd, argv):
    args = argv[1:]
    if shell == "powershell" and cmd in PS_WRITE:
        _judge_ps_writer(hc, st, PS_WRITE[cmd], args, cmd)
        return
    if cmd == "tee":
        for t in _nonopt(args):
            _write_target(hc, st, t, "tee")
    elif cmd == "sed":
        if any(a and (a == "-i" or a.startswith("-i") or a.startswith("--in-place")) for a in args):
            has_script_opt = any(a in ("-e", "-f", "--expression", "--file") or (a or "").startswith("--expression=")
                                 for a in args)
            files = _nonopt(args, value_opts=("-e", "-f", "--expression", "--file"))
            if not has_script_opt and files:
                files = files[1:]
            for t in files:
                _write_target(hc, st, t, "sed -i")
    elif cmd in ("rm", "touch", "mkdir"):
        for t in _nonopt(args, value_opts=("-m", "--mode")):
            _write_target(hc, st, t, cmd)
    elif cmd in ("cp", "mv"):
        tdir = None
        rest = []
        i = 0
        while i < len(args):
            a = args[i]
            if a in ("-t", "--target-directory"):
                tdir = args[i + 1] if i + 1 < len(args) else None
                i += 2
                continue
            if a and a.startswith("--target-directory="):
                tdir = a.split("=", 1)[1]
                i += 1
                continue
            rest.append(a)
            i += 1
        ops = _nonopt(rest, value_opts=("-S", "--suffix"))
        if tdir is None and len(ops) >= 2:
            srcs, dest = ops[:-1], ops[-1]
        else:
            srcs, dest = ops, tdir
        if cmd == "mv":
            for s in srcs:
                _write_target(hc, st, s, "mv 원본")
        if dest is None:
            if srcs:
                _write_target(hc, st, None, cmd)
            return
        dest_abs = rp.norm_abs(dest, st.cwd) if dest is not None else None
        into_dir = tdir is not None or len(srcs) > 1 or dest.endswith(("/", "\\")) or (dest_abs and os.path.isdir(dest_abs))
        _write_target(hc, st, dest, cmd + " 대상")
        if into_dir:
            for s in srcs:
                if s is None:
                    _write_target(hc, st, None, cmd)
                _write_target(hc, st, dest.rstrip("/\\") + "/" + os.path.basename(s.replace("\\", "/").rstrip("/")),
                              cmd + " 대상")


def _judge_ps_writer(hc, st, kind, args, cmd):
    named, pos = {}, []
    i = 0
    while i < len(args):
        a = args[i]
        if a is not None and a.startswith("-") and len(a) > 1 and not re.match(r"^-\d", a):
            name = a[1:].split(":", 1)[0].lower()
            if ":" in a:
                i += 1
                continue
            if any(sw.startswith(name) for sw in PS_SWITCHES) and not any(p.startswith(name) for p in ("path", "literalpath", "filepath", "destination", "name", "value", "itemtype", "encoding", "include", "exclude", "filter")):
                i += 1
                continue
            val = args[i + 1] if i + 1 < len(args) else None
            named.setdefault(name, []).append(val)
            i += 2
            continue
        pos.append(a)
        i += 1

    def get(names):
        vals = []
        for k, v in named.items():
            if any(n.startswith(k) for n in names):
                vals += v
        return vals
    paths = get(("path", "literalpath", "filepath", "pspath", "lp"))
    dests = get(("destination",))
    if not paths and pos:
        paths = [pos[0]]
    if kind in ("copy", "move") and not dests and len(pos) >= 2:
        dests = [pos[1]]
    split = []
    for p in paths + dests:
        split += (p.split(",") if p is not None else [None])
    if kind == "new":
        names = get(("name",))
        if names and paths:
            split = [(p or "") + "/" + (nm or "") if (p is not None and nm is not None) else None for p in paths for nm in names]
    if kind in ("copy", "move"):
        targets = dests[:] if dests else [None]
        if kind == "move":
            targets += paths
        for t in targets:
            for x in (t.split(",") if t is not None else [None]):
                _write_target(hc, st, x, cmd)
        return
    for t in split or [None]:
        _write_target(hc, st, t, cmd)


# ---------------------------------------------------------------- git
def _git_globals(argv):
    i, Cs, cfgs, gitdir = 1, [], [], None
    while i < len(argv):
        a = argv[i]
        if a == "-C":
            Cs.append(argv[i + 1] if i + 1 < len(argv) else None)
            i += 2
        elif a == "-c":
            cfgs.append(argv[i + 1] if i + 1 < len(argv) else None)
            i += 2
        elif a is not None and a.startswith("--git-dir="):
            gitdir = a.split("=", 1)[1]
            i += 1
        elif a == "--git-dir":
            gitdir = argv[i + 1] if i + 1 < len(argv) else None
            i += 2
        elif a is not None and a.startswith("--config-env="):
            cfgs.append(a.split("=", 1)[1])
            i += 1
        elif a == "--config-env":
            cfgs.append(argv[i + 1] if i + 1 < len(argv) else None)
            i += 2
        elif a in ("--work-tree", "--namespace", "--exec-path", "--super-prefix"):
            i += 2
        elif a is not None and a.startswith("-"):
            i += 1
        else:
            break
    sub = argv[i] if i < len(argv) else None
    return Cs, cfgs, gitdir, sub, argv[i + 1:]


def _deny(hc, msg):
    hc.scope()
    raise Deny("[EL1 거부] " + msg)


def judge_git(hc: HC, st: CmdState, argv):
    Cs, cfgs, gitdir, sub, args = _git_globals(argv)
    for c in cfgs:
        if c is None:
            _deny(hc, "git -c 값을 해석하지 못함")
        k = c.split("=", 1)[0].strip().lower()
        if k.startswith("alias.") or k == "core.hookspath":
            _deny(hc, "검사 끄기: git -c %s" % k)
    if sub is None:
        return
    base = st.cwd
    unknown = False
    for c in Cs:
        if c is None:
            unknown = True
            break
        base = rp.norm_abs(c, base)
    if st.cd_seen and not Cs:
        unknown = True
    if sub in ("clone", "init", "version", "help"):
        return
    wt = None if unknown else rp.worktree_of(base)
    if gitdir is not None:
        is_ws = True   # --git-dir이 작업 저장소·gate를 가리키면 '저장소 내부' 규칙이 이미 거부했다
    elif unknown:
        is_ws = True
    else:
        is_ws = wt is not None and rp.ncase(wt[1]) == rp.ncase(hc.env.common_dir)
    if not is_ws:
        # DESIGN-GAP: §6.2 규칙 표는 대상 저장소를 정하지 않았다. 작업 저장소(git-common-dir이 같은 저장소) 밖의 git 명령
        # (§12-7 격리 복제본의 `git -C <TEMP>/<id>-iso remote remove origin`, 다른 프로젝트 저장소)은 git 규칙을 적용하지
        # 않는다(경로·저장소 내부 규칙은 적용). gate·작업 저장소 내부를 가리키면 '저장소 내부' 규칙이 이미 거부했다.
        return
    subl0 = sub.lower()
    if not (subl0 in READ_SUBS or (subl0 == "config" and not args) or (subl0 == "branch" and _branch_is_read(args))):
        hc.scope()   # 읽기 명령은 무결성 표지가 있어도 막지 않는다(판정 범위 = 쓰기)
    root = wt[0] if wt else None
    br = branch_of(root) if root else None
    rinfo = rp.role_of_branch(br)
    is_main = root is not None and rp.ncase(root) == rp.ncase(hc.env.main_root)
    subl = sub.lower()
    # 검사 끄기
    if subl == "commit":
        for a in args:
            if a and re.match(r"^-[A-Za-z]+$", a):
                for ch in a[1:]:
                    if ch == "n":
                        _deny(hc, "검사 끄기: git commit -n")
                    if ch in "mFcCt":
                        break
    # git 설정 쓰기
    if subl == "config":
        _judge_config(hc, args)
        return
    if subl == "remote" and args and args[0] in ("add", "set-url", "rename", "remove", "rm"):
        _deny(hc, "git 설정 쓰기: git remote %s" % args[0])
    if subl == "push":
        _judge_push(hc, root, rinfo, is_main, args)
        return
    if subl in REF_MOVE:
        _deny(hc, "참조 이동·hook 없는 커밋 생성: git %s" % sub)
    if subl == "symbolic-ref":
        pos = [a for a in args if a and not a.startswith("-")]
        if len(pos) >= 2 or any(a in ("-d", "--delete") for a in args):
            _deny(hc, "참조 이동: git symbolic-ref(쓰기)")
    if subl == "hash-object" and any(a == "-w" or (a and re.match(r"^-[a-z]*w", a)) for a in args):
        _deny(hc, "hook 없는 객체 쓰기: git hash-object -w")
    if subl == "branch":
        _judge_branch(hc, args)
    if subl in ("checkout", "switch"):
        if any(a in ("-B", "-C", "--force-create") for a in args):
            _deny(hc, "참조 이동: git %s -B/-C" % sub)
    if subl in ("merge", "pull"):
        # DESIGN-GAP: §6.2 '병합' 행은 `git merge`만 적었다. `git pull`은 병합(또는 rebase)을 만들므로 같은 규칙으로 판정한다.
        _judge_merge(hc, root, rinfo, is_main, args, subl)
        return
    if subl == "worktree":
        _judge_worktree(hc, args)
        return
    if subl in ("checkout", "restore"):
        _judge_test_revert(hc, st, root, subl, args)
    read_only = subl in READ_SUBS or (subl == "branch" and _branch_is_read(args)) \
        or (subl == "remote" and (not args or args[0] in ("-v", "show", "get-url"))) \
        or (subl == "tag" and (not args or args[0] in ("-l", "--list"))) \
        or (subl == "reflog" and (not args or args[0] in ("show",))) \
        or (subl == "fetch" and not hc.is_role)
    if hc.is_role and not read_only:
        if not Cs:
            _deny(hc, "역할의 쓰기 git 명령은 `git -C <자기 worktree>`로만(§5.1): git %s" % sub)
        if rinfo is None or rinfo[0] != hc.role_short:
            _deny(hc, "역할 %s가 자기 worktree(role/%s/<id>) 밖에서 git %s" % (hc.actor, hc.role_short, sub))
        if subl == "commit":
            _judge_role_commit(hc, rinfo, args)
    if not hc.is_role and rinfo is not None and not read_only:
        if subl == "commit":
            _deny(hc, "오케스트레이터는 역할 worktree에서 커밋하지 못한다(§12-6 병합만)")
        _deny(hc, "오케스트레이터는 역할 worktree에서 쓰기 git 명령을 쓰지 못한다(§5.1): git %s" % sub)


def _judge_config(hc, args):
    if args and args[0] in ("get", "list"):
        return
    if args and args[0] in ("set", "unset", "rename-section", "remove-section", "edit"):
        _deny(hc, "git 설정 쓰기: git config %s" % args[0])
    if any(a in CONFIG_WRITE_FLAGS for a in args):
        _deny(hc, "git 설정 쓰기: git config")
    if any(a in CONFIG_READ_FLAGS for a in args):
        return
    pos, i = [], 0
    while i < len(args):
        a = args[i]
        if a in CONFIG_VALUE_OPTS:
            i += 2
            continue
        if a is not None and a.startswith("-"):
            i += 1
            continue
        pos.append(a)
        i += 1
    if len(pos) == 1:
        return   # `git config <키>` = 읽기
    _deny(hc, "git 설정 쓰기: git config %s" % " ".join(x or "?" for x in args))


def _role_branches(hc):
    out = rp.git_text(["-C", hc.env.main_root, "for-each-ref", "--format=%(refname:short)", "refs/heads/role/"])
    return [x for x in out.splitlines() if x.strip()]


def _judge_push(hc, root, rinfo, is_main, args):
    if hc.is_role:
        _deny(hc, "역할은 push하지 못한다")
    if any(a is None or a.startswith("+") or ":+" in a or a.startswith("--force") or a in ("-f", "--mirror", "--all", "--delete", "-d", "--prune")
           for a in args):
        _deny(hc, "강제·삭제 push 거부")
    if is_main and args == ["gate", "master:master"]:
        rb = _role_branches(hc)
        if rb:
            _deny(hc, "진행 중인 변경이 있어(역할 브랜치 %s) 문서 커밋 push를 거부한다(review29 Q-08)" % ", ".join(rb))
    elif rinfo is not None and rinfo[0] == "audit" and args == ["gate", "role/audit/%s:master" % rinfo[1]]:
        pass
    else:
        _deny(hc, "허용된 push 형태가 아니다: `git push gate master:master`(메인) 또는 "
                  "`git -C <audit worktree> push gate role/audit/<id>:master`")
    results, ok = integrity.check("push", hc.env.main_root)
    if not ok:
        bad = [r for r in results if not r["ok"]]
        _deny(hc, "push 직전 무결성 대조 실패:\n  " + "\n  ".join(json.dumps(b, ensure_ascii=False) for b in bad)
              + "\n" + integrity.RECOVERY)


def _branch_is_read(args):
    return not args or all(a is not None and (a in ("-a", "-r", "-v", "-vv", "--list", "-l", "--show-current", "--all",
                                                  "--merged", "--no-merged", "--contains", "--format")
                                              or a.startswith("--format=") or a.startswith("--sort=")) for a in args)


def _judge_branch(hc, args):
    flags = [a for a in args if a and a.startswith("-")]
    pos = [a for a in args if a and not a.startswith("-")]
    force = any(f in ("-f", "--force", "-M", "-C") or f in ("-D",) or (f.startswith("-") and not f.startswith("--") and any(ch in f[1:] for ch in "fMDC")) for f in flags)
    if any(f in ("-D",) or (f.startswith("-") and not f.startswith("--") and "D" in f[1:]) for f in flags) \
            or (("-d" in flags or "--delete" in flags) and ("-f" in flags or "--force" in flags)):
        if hc.is_role:
            _deny(hc, "참조 이동: git branch -D")
        if len(flags) != 1 or not pos:
            _deny(hc, "git branch -D는 정리 형태(`git branch -D role/{test,code,audit}/<id>`)만")
        for b in pos:
            ri = rp.role_of_branch(b)
            if ri is None:
                _deny(hc, "git branch -D는 역할 브랜치 정리에만: %s" % b)
            if ri[0] == "code":
                _dispute_guard(hc, ri[1], branch=b)
        return
    if force:
        _deny(hc, "참조 이동: git branch %s" % " ".join(flags))


def _dispute_guard(hc, cid, branch=None, wt_path=None):
    """§6.2 정리 전 dispute 보존: code worktree(또는 브랜치)의 dispute blob id가 메인 HEAD spec card의
    `## dispute 기록` 절에 없으면 거부(review30 R-16)."""
    rel = "docs/02-design/disputes/%s.md" % cid
    blobs = []
    wts = [p for p, b in rp.list_worktrees(hc.env.main_root) if b == "role/code/%s" % cid]
    if wt_path:
        wts.append(wt_path)
    for w in wts:
        f = os.path.join(w, *rel.split("/"))
        if os.path.isfile(f):
            blobs.append(rp.git_text(["-C", w, "hash-object", f]))
    rc, out = rp.git_try(["-C", hc.env.main_root, "rev-parse", "--verify", "--quiet", "refs/heads/role/code/%s:%s" % (cid, rel)])
    if rc == 0:
        blobs.append(out.decode().strip())
    if not blobs:
        return
    card = rp.show_blob(["-C", hc.env.main_root], "HEAD:" + rp.spec_card_path(cid))
    sec = ""
    if card is not None:
        text = card.decode("utf-8", "replace").replace("\r\n", "\n")
        m = re.search(r"^## dispute 기록[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        sec = m.group(1) if m else ""
    missing = [b for b in blobs if b not in sec]
    if missing:
        _deny(hc, "dispute(%s, blob %s)가 메인 HEAD spec card의 `## dispute 기록`에 없어 code worktree 정리를 거부한다(§12 재시도)"
              % (rel, ", ".join(missing)))


def _judge_merge(hc, root, rinfo, is_main, args, subl):
    if hc.is_role:
        _deny(hc, "역할은 병합하지 못한다")
    if subl == "merge" and rinfo is not None and rinfo[0] == "audit":
        cid = rinfo[1]
        if len(args) == 6 and args[0] == "--no-ff" and args[1] == "role/code/%s" % cid and args[2] == "-m" \
                and args[3] and args[4] == "-m" and args[5] == "Role: doc\nChange-Id: %s" % cid:
            return
        # D-3: 오케스트레이터의 §12 재시도 정리 -- 남은 병합 상태를 되돌린다(audit worktree만, 다른 병합 형태는 여전히 거부).
        if args == ["--abort"]:
            return
    if subl == "merge" and is_main and args == ["--ff-only", "gate/master"]:
        return
    _deny(hc, "허용된 병합 형태가 아니다: §12-6 `git -C <audit worktree> merge --no-ff role/code/<id> -m \"merge <id>\" "
              "-m \"Role: doc⏎Change-Id: <id>\"` 또는 메인 worktree의 `git merge --ff-only gate/master`")


def _judge_worktree(hc, args):
    if hc.is_role:
        _deny(hc, "역할은 git worktree를 쓰지 못한다")
    if args and args[0] == "list":
        return   # DESIGN-GAP: §6.2는 add·remove만 적었다. list는 읽기라 허용(정상 흐름 오거부 방지)
    W = hc.env.wt_dir

    def same(p, q):
        return p is not None and rp.ncase(rp.norm_abs(p, hc.cwd)) == rp.ncase(q)
    if args and args[0] == "add":
        # D-6: `-q`/`--quiet`만 걸러내면 §12-1 형태와 같은 판정.
        add_rest = [a for a in args[1:] if a not in ("-q", "--quiet")]
        if len(add_rest) == 4 and add_rest[1] == "-b":
            m = rp.role_of_branch(add_rest[2])
            if m:
                short, cid = m
                want_base = "gate/master" if short == "test" else "role/test/%s" % cid
                if same(add_rest[0], "%s/%s-%s" % (W, cid, short)) and add_rest[3] == want_base:
                    return
    if args and args[0] == "remove":
        # D-3: `--force`/`-f`가 앞이든 뒤든(순서 무관) 걸러내면 같은 경로 판정. §12 세 경로(<id>-{test,code,audit})만.
        rm_rest = [a for a in args[1:] if a not in ("--force", "-f")]
        if len(rm_rest) == 1:
            p = rp.norm_abs(rm_rest[0], hc.cwd) if rm_rest[0] else None
            m = re.match(r"^([0-9]{8}-[a-z0-9][a-z0-9-]*)-(test|code|audit)$", os.path.basename(p or ""))
            if m and same(rm_rest[0], "%s/%s-%s" % (W, m.group(1), m.group(2))):
                if m.group(2) == "code":
                    _dispute_guard(hc, m.group(1), wt_path=p)
                return
    _deny(hc, "git worktree는 §12의 add·remove 형태만: %s" % " ".join(x or "?" for x in args))


def _judge_test_revert(hc, st, root, subl, args):
    if root is None:
        return
    if subl == "checkout" and "--" in args:
        paths = args[args.index("--") + 1:]
    else:
        paths = [a for a in args if a and not a.startswith("-")]
    for p in paths:
        if p is None:
            continue
        a = rp.norm_abs(p, root if not st.cd_seen else st.cwd)
        if rp.is_under(a, root) and rp.classify(rp.rel_to(a, root)) == "test":
            _deny(hc, "test 되돌리기: git %s %s" % (subl, p))
        if rp.is_under(a, root) and rp.rel_to(a, root).casefold() in ("skills/analog-gmid-design/assets/tests",):
            _deny(hc, "test 되돌리기: git %s %s" % (subl, p))


def _judge_role_commit(hc, rinfo, args):
    role, cid = rinfo[0], rinfo[1]
    trailers, i = [], 0
    while i < len(args):
        a = args[i]
        if a == "--trailer":
            trailers.append(args[i + 1] if i + 1 < len(args) else None)
            i += 2
            continue
        if a in ("-m", "--message"):
            if i + 1 >= len(args) or not args[i + 1]:
                _deny(hc, "커밋 메시지 값 없음")
            i += 2
            continue
        if a in ("-a", "--all", "-q", "--quiet"):
            i += 1
            continue
        # DESIGN-GAP: §6.2 "-F·에디터 메시지·다른 값은 거부" — 허용 옵션 목록(-m·--trailer·-a·-q)으로 판정한다
        _deny(hc, "역할 커밋 형태 위반: 허용 옵션은 -m·--trailer·-a·-q뿐(%r)" % a)
    if "-m" not in args and "--message" not in args:
        _deny(hc, "역할 커밋은 -m 메시지로(에디터 메시지 거부)")
    want = ["Role: %s" % role, "Change-Id: %s" % cid]
    if trailers != want:
        _deny(hc, "역할 커밋 트레일러는 정확히 `--trailer \"Role: %s\" --trailer \"Change-Id: %s\"`(%r)" % (role, cid, trailers))


# ================================================================ EL2 (§7)
IGNORED_SEGMENTS = ("__pycache__", ".pytest_cache")


def _status_entries(root):
    out = rp.git(["-C", root, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"])
    toks = out.decode("utf-8", "replace").split("\0")
    ents = []
    for t in toks:
        if len(t) < 4:
            continue
        ents.append((t[:2], t[3:]))
    return ents


def _ignored(path):
    return any(seg in IGNORED_SEGMENTS for seg in path.split("/"))


def main_snapshot(env):
    snap = {}
    for xy, p in _status_entries(env.main_root):
        if _ignored(p) or not rp.overlaps_any(p, env.rules):
            continue
        f = os.path.join(env.main_root, *p.split("/"))
        blob = None
        if os.path.isfile(f):
            with open(f, "rb") as fh:
                blob = rp.blob_id(fh.read())
        snap[p] = [xy, blob]
    return snap


def _status_file(env, tool_use_id):
    if not tool_use_id or not re.fullmatch(r"[A-Za-z0-9_\-]+", tool_use_id):
        raise GateError("tool_use_id 형식이 판정할 수 없다: %r" % tool_use_id)
    return os.path.join(env.cache_root, "status-%s.json" % tool_use_id)


def role_worktree_violations(env, actor):
    fails = []
    short = rp.ROLE_OF_AGENT[actor]
    for path, br in rp.list_worktrees(env.main_root):
        ri = rp.role_of_branch(br)
        if ri is None:
            continue
        dirty = [(xy, p) for xy, p in _status_entries(path) if not _ignored(p)]
        if not dirty:
            continue
        if ri[0] != short:
            # D-7: 다른 역할 worktree의 미커밋 경로는, 그 worktree 주인 역할에게 허용된 경로(쓰기 경로표,
            # 그 worktree의 변경 id)이면 호출 역할의 위반으로 세지 않는다. 주인에게도 허용되지 않으면 위반이다.
            owner_agent = rp.AGENT_OF_ROLE.get(ri[0])
            owner_ctx = rp.WriteContext(rules=env.rules, change_id=ri[1], bootstrapped=env.bootstrapped,
                                  gate_change_ok=mg.gate_change_ok(
                                      mg.TreeView(env.gate_args(), env.gate_master) if env.source == "gate"
                                      else mg.TreeView(["-C", env.main_root], "HEAD"), ri[1]))
            owner_denied = []
            for xy, p in dirty:
                v = rp.allowed(owner_agent, p, owner_ctx) if owner_agent else None
                if v is None or not v.ok:
                    owner_denied.append((xy, p))
            if owner_denied:
                fails.append("%s: 다른 역할(%s)의 worktree에 미커밋 변경 %s" % (path, ri[0], ", ".join(p for _, p in owner_denied[:5])))
            continue
        ctx = rp.WriteContext(rules=env.rules, change_id=ri[1], bootstrapped=env.bootstrapped,
                              gate_change_ok=mg.gate_change_ok(
                                  mg.TreeView(env.gate_args(), env.gate_master) if env.source == "gate"
                                  else mg.TreeView(["-C", env.main_root], "HEAD"), ri[1]))
        for xy, p in dirty:
            v = rp.allowed(actor, p, ctx)
            if not v.ok:
                fails.append("%s: %s %s -- %s" % (path, xy, p, v.reason))
    return fails


def subagent_commit_violations(env, actor):
    short = rp.ROLE_OF_AGENT[actor]
    fails = []
    for path, br in rp.list_worktrees(env.main_root):
        ri = rp.role_of_branch(br)
        if ri is None or ri[0] != short:
            continue
        cid = ri[1]
        args = ["-C", path]

        def ok_ref(r):
            return rp.git_try(args + ["rev-parse", "--verify", "--quiet", r + "^{commit}"])[0] == 0
        if short == "test":
            if not ok_ref("refs/remotes/gate/master"):
                fails.append("gate/master가 없어 test 범위를 정하지 못함")
                continue
            rng = "refs/remotes/gate/master..HEAD"
        else:
            tref = "refs/heads/role/test/%s" % cid
            if not ok_ref(tref):
                fails.append("%s가 없어 범위를 정하지 못함" % tref)
                continue
            rng = "%s..HEAD" % tref
            if short == "audit":
                m = rp.git_text(args + ["rev-list", "--merges", "-n", "1", "HEAD"])
                if m and rp.git_try(args + ["merge-base", "--is-ancestor", tref, m])[0] == 0:
                    rng = "%s..HEAD" % m
        commits = [c for c in rp.git_text(args + ["rev-list", rng]).split() if c]
        if short == "audit" and len(commits) > 1:
            fails.append("%s: audit 범위 커밋이 최대 1개여야 한다(%d)" % (path, len(commits)))
        for c in commits:
            out = rp.git(args + ["show", "-s", "--format=%P%x00%B", c]).decode("utf-8", "replace")
            parents, msg = out.split("\0", 1)
            if len(parents.split()) != 1:
                fails.append("%s: 병합 커밋 %s" % (path, c[:12]))
                continue
            tr = mg.parse_trailers(msg, args)
            if mg.trailer_values(tr, "Role") != [short] or mg.trailer_values(tr, "Change-Id") != [cid]:
                fails.append("%s: 커밋 %s 트레일러가 `Role: %s`·`Change-Id: %s`가 아니다(%r)" % (path, c[:12], short, cid, tr))
    return fails


# ================================================================ 진입점
def run(event: str, payload: dict, cache_dir: str, env=None):
    """(exit code, 메시지). env: 실행기가 이미 읽은 판정 환경(없으면 여기서 읽는다)."""
    try:
        actor = actor_of(payload.get("agent_type"))
    except Deny as e:
        return 2, str(e)
    tool = payload.get("tool_name") or ""
    ti = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    if event == "SessionStart":
        return session_start(cwd)
    if event in ("PostToolUse", "SubagentStop") and actor not in rp.ROLE_OF_AGENT:
        return 0, ""   # EL2는 gmid-* 역할에만(§7)
    if event == "PreToolUse" and tool in READ_TOOLS and actor != "gmid-test-author":
        return 0, ""   # Read·Grep·Glob은 §6.4(test-author)에만
    if env is None:
        env = rp.load_env(cwd)
    hc = HC(env, actor, payload, cache_dir)
    warn = ("[역할 게이트 경고] " + " / ".join(env.warnings) + "\n") if env.warnings else ""
    try:
        if event == "PreToolUse":
            if hc.is_role and hc.marker:
                hc.scope()
            if tool in WRITE_TOOLS:
                t = ti.get("file_path") or ti.get("notebook_path")
                if not t:
                    hc.scope()
                    raise Deny("[EL1 거부] 쓰기 도구 대상 경로가 없다")
                judge_write(hc, t, tool)
            elif tool in READ_TOOLS:
                judge_read(hc, tool, ti)
            elif tool in ("Bash", "PowerShell"):
                if hc.is_role and tool == "PowerShell":
                    hc.scope()
                    raise Deny("[EL1 거부] 역할은 PowerShell을 쓰지 않는다(agent 정의 tools에 없음)")
                judge_command_string(hc, ti.get("command") or "", "bash" if tool == "Bash" else "powershell")
                if hc.is_role and tool == "Bash":
                    f = _status_file(env, payload.get("tool_use_id"))
                    os.makedirs(os.path.dirname(f), exist_ok=True)
                    with open(f, "w", encoding="utf-8") as fh:
                        json.dump(main_snapshot(env), fh, ensure_ascii=False)
            return 0, warn
        if event == "PostToolUse":
            if not hc.is_role:
                return 0, ""
            f = _status_file(env, payload.get("tool_use_id"))
            fails = []
            if not os.path.exists(f):
                fails.append("PreToolUse 상태 기록 %s가 없어 메인 worktree 변경을 대조하지 못함" % os.path.basename(f))
                before = None
            else:
                with open(f, "r", encoding="utf-8") as fh:
                    before = json.load(fh)
                os.remove(f)
            if before is not None:
                after = main_snapshot(env)
                for p in sorted(set(before) | set(after)):
                    if before.get(p) != after.get(p):
                        fails.append("메인 worktree 변경: %s %r -> %r" % (p, before.get(p), after.get(p)))
            fails += role_worktree_violations(env, actor)
            if fails:
                return 2, "[EL2 거부] 주체 %s\n  " % actor + "\n  ".join(fails)
            return 0, ""
        if event == "SubagentStop":
            if not hc.is_role:
                return 0, ""
            fails = role_worktree_violations(env, actor) + subagent_commit_violations(env, actor)
            if fails:
                return 2, "[EL2 거부] SubagentStop 주체 %s\n  " % actor + "\n  ".join(fails)
            return 0, ""
        return 2, "알 수 없는 hook 이벤트 %r" % event
    except Deny as e:
        return 2, warn + str(e)


def session_start(cwd):
    main_root, common = rp.main_worktree_of(cwd)
    cache_root = os.path.join(common, rp.CACHE_DIRNAME)
    removed = 0
    if os.path.isdir(cache_root):
        for f in os.listdir(cache_root):
            if re.fullmatch(r"status-.*\.json", f):
                os.remove(os.path.join(cache_root, f))
                removed += 1
    results, ok = integrity.check("session", main_root)
    lines = ["[역할 게이트] 세션 시작 무결성 대조: %s (status 잔여 %d개 삭제)" % ("전부 일치" if ok else "불일치", removed)]
    lines += [json.dumps(r, ensure_ascii=False) for r in results if not r["ok"]]
    ctx = integrity.Ctx(main_root, None)
    n = ctx.cfg.get("audit_tail_lines")
    logp = os.path.join(ctx.gate, integrity.ACCEPT_LOG)
    if isinstance(n, int) and n > 0 and os.path.isfile(logp):
        with open(logp, "rb") as fh:
            tail = fh.read().decode("utf-8", "replace").splitlines()[-n:]
        lines.append("[감사 로그 gmid-accept-log 마지막 %d줄]" % n)
        lines += tail
    if not ok:
        lines.append(integrity.RECOVERY)
        return 2, "\n".join(lines)
    return 0, "\n".join(lines)
