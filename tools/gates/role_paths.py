"""쓰기 경로표 파싱과 경로 판정 (05-role-separation design §4, 계획 N3.12.2).

정본은 계획서 N3.12.2 표다. 이 모듈은 그 표를 **직접** 파싱한다(사본 없음). 표 읽기 함수
`read_section_table`는 `merge_gate.read_plan_tables`가 같은 것을 쓴다(§4.1 "같은 함수").

게이트 코드 전체가 쓰는 git 호출 도우미(`git`)와 경로 정규화, 실행 환경(`load_env`)도 여기 둔다 --
모든 겹의 git 호출에 `GIT_NO_REPLACE_OBJECTS=1`(§4.4, review30 R-20).
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field

# ---------------------------------------------------------------- 상수(설계 참조)
# 계획서 경로: 계획서가 쓰기 경로표·판정 표의 정본이다(N3.12.2, 00-common §9).
PLAN_PATH = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
CONFIG_PATH = "tools/gates/gate_config.json"
GATE_CODE_PREFIX = "tools/gates/"
# 게이트 코드 캐시에 풀지 않는 하위 경로: 공격 재생 데이터는 게이트 코드가 아니다(§13.2, 검증 agent 소유).
GATE_CODE_EXCLUDE = ("tools/gates/redteam/",)
CACHE_DIRNAME = "gmid-gate-cache"
INTEGRITY_MARKER = "integrity-failed"

ACTORS = ("gmid-code-author", "gmid-test-author", "gmid-verification-auditor", "오케스트레이터", "사용자")
CONDITIONS = ("없음", "자기 변경 id", "게이트 변경", "부트스트랩", "승인 기록", "status 전이만", "판정 환경", "판정 트리")
# 주체 `사용자` 행에만 쓰는 조건(N3.12.2 조건 값 정의)
USER_ONLY_CONDITIONS = ("판정 환경", "판정 트리")
# EL1은 허용하고 EL3·EL4가 내용으로 판정하는 조건(§4.1)
CONTENT_CONDITIONS = ("승인 기록", "status 전이만")

# §4.2 역할 ↔ 주체 ↔ 트레일러
ROLE_OF_AGENT = {
    "gmid-code-author": "code",
    "gmid-test-author": "test",
    "gmid-verification-auditor": "audit",
}
AGENT_OF_ROLE = {v: k for k, v in ROLE_OF_AGENT.items()}
ACTOR_OF_TRAILER = {"code": "gmid-code-author", "test": "gmid-test-author",
                    "audit": "gmid-verification-auditor", "doc": "오케스트레이터", "user": "사용자"}
ROLE_SHORT = ("code", "test", "audit")

ID_RE = re.compile(r"^[0-9]{8}-[a-z0-9][a-z0-9-]*(?![\s\S])")   # 00-common §8.1 `id`
HEX40 = re.compile(r"^[0-9a-f]{40}(?![\s\S])")
HEX64 = re.compile(r"^[0-9a-f]{64}(?![\s\S])")
ZERO40 = "0" * 40

# §4.3 경로 5분류. 정의의 정본은 계획 N3.12.4 EL3(산문)이라 파싱하지 않고 여기 적는다.
# 파일을 명시한 규칙이 glob 규칙보다 우선한다(같은 절).
CLASS_EXPLICIT = {
    "workspaces/run_harness.py": "source",
    ".ai/verification/_schema.json": "source",
}
CLASS_GLOBS = (
    ("source", ("skills/analog-gmid-design/assets/*.py",), ()),
    ("test", ("skills/analog-gmid-design/assets/tests/**",), ("skills/analog-gmid-design/assets/tests/tools/**",)),
    ("tool", ("skills/analog-gmid-design/assets/tests/tools/**", "tools/**", "hooks/role_*.py", "hooks/role_*.json"), ()),
    ("data", ("skills/analog-gmid-design/assets/library/**",), ()),
    ("doc", ("docs/**", ".ai/**", "agents/gmid-*.md"), ()),
)


class GateError(Exception):
    """게이트가 판정할 수 없는 상태(표 파손, git 실패 등). 호출자는 거부로 끝낸다(fail-closed)."""


# ---------------------------------------------------------------- git
# 저장소를 가리키는 환경 변수: git client hook(GIT_INDEX_FILE 등)과 gate `pre-receive`(GIT_DIR=., 격리 객체
# 디렉터리)가 설정한다. 다른 저장소(작업 저장소 worktree)를 `-C`로 부를 때 남아 있으면 엉뚱한 저장소를 읽는다.
_REPO_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
             "GIT_QUARANTINE_PATH", "GIT_PREFIX", "GIT_COMMON_DIR", "GIT_NAMESPACE")


def git_env(extra=None, clean=True):
    env = dict(os.environ)
    if clean:
        for k in _REPO_ENV:
            env.pop(k, None)
    env["GIT_NO_REPLACE_OBJECTS"] = "1"  # §4.4 R-20
    env.setdefault("LC_ALL", "C")
    if extra:
        env.update(extra)
    return env


def _auto_clean(args, clean):
    # `--git-dir <g>`로 부르는 gate 호출은 격리 객체 환경을 유지해야 push된 객체가 보인다(pre-receive).
    # 그 밖(`-C <worktree>`)은 저장소 환경 변수를 뗀다. index를 읽는 EL3 호출은 clean=False를 명시한다.
    if clean is not None:
        return clean
    return not (args and args[0] == "--git-dir")


def git(args, cwd=None, input=None, check=True, env=None, clean=None):
    """git 호출. 실패하면 GateError(check=True). 표준출력 바이트를 돌려준다."""
    args = list(args)
    p = subprocess.run(["git"] + args, cwd=cwd, input=input, capture_output=True,
                       env=git_env(env, _auto_clean(args, clean)))
    if check and p.returncode != 0:
        raise GateError("git %s 실패(%d): %s" % (" ".join(args[:4]), p.returncode,
                                               p.stderr.decode("utf-8", "replace").strip()[:400]))
    return p.stdout if check else p


def git_text(args, cwd=None, **kw):
    return git(args, cwd=cwd, **kw).decode("utf-8", "replace").strip()


def git_try(args, cwd=None, env=None, clean=None):
    """(returncode, stdout bytes). 존재 확인 등 실패가 정상 분기인 호출용."""
    args = list(args)
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, env=git_env(env, _auto_clean(args, clean)))
    return p.returncode, p.stdout


def blob_id(data: bytes) -> str:
    """`git hash-object --no-filters`와 같은 blob id."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def show_blob(repo_args, rev_path):
    """`git show <rev>:<path>` 바이트, 없으면 None. repo_args는 `["--git-dir", g]` 또는 `["-C", d]`."""
    rc, out = git_try(repo_args + ["cat-file", "blob", rev_path])
    return out if rc == 0 else None


# ---------------------------------------------------------------- 경로
_MSYS_DRIVE = re.compile(r"^/([a-zA-Z])(/|$)")


def norm_abs(p: str, cwd: str | None = None) -> str:
    """`C:\\…`·`C:/…`·`/c/…`를 같은 절대 경로(슬래시 표기)로(§6.2 캐시 경로 비교)."""
    s = p.replace("\\", "/")
    m = _MSYS_DRIVE.match(s)
    if m:
        s = m.group(1).upper() + ":/" + s[m.end():]
    if not re.match(r"^[a-zA-Z]:/", s) and not s.startswith("//"):
        if cwd is None:
            raise GateError("상대 경로의 기준 디렉터리가 없다: %r" % p)
        s = norm_abs(cwd) + "/" + s
    s = os.path.normpath(s).replace("\\", "/")
    if re.match(r"^[a-z]:/", s):
        s = s[0].upper() + s[1:]
    return s


def ncase(p: str) -> str:
    return os.path.normcase(p.replace("/", os.sep)).replace("\\", "/")


def is_under(path: str, root: str) -> bool:
    a, b = ncase(path).rstrip("/"), ncase(root).rstrip("/")
    return a == b or a.startswith(b + "/")


_toplevel_cache: dict = {}


def worktree_of(abs_path: str):
    """(worktree 루트, git-common-dir) 또는 None. 대상의 가장 가까운 존재하는 조상 디렉터리에서
    `git rev-parse --show-toplevel`(§4.1). 조회 결과는 프로세스 안에서 캐시(상한 = 조회한 디렉터리 수)."""
    d = abs_path
    while not os.path.isdir(d):
        nd = os.path.dirname(d)
        if nd == d:
            return None
        d = nd
    key = ncase(d)
    if key in _toplevel_cache:
        return _toplevel_cache[key]
    rc, out = git_try(["-C", d, "rev-parse", "--show-toplevel", "--git-common-dir"])
    res = None
    if rc == 0:
        lines = out.decode("utf-8", "replace").splitlines()
        if len(lines) >= 2 and lines[0].strip():
            top = norm_abs(lines[0].strip())
            common = norm_abs(lines[1].strip(), d)
            res = (top, common)
    if len(_toplevel_cache) > 512:  # 상한(WP-10)
        _toplevel_cache.clear()
    _toplevel_cache[key] = res
    return res


def rel_to(abs_path: str, root: str) -> str:
    a = norm_abs(abs_path)
    r = norm_abs(root).rstrip("/")
    if not is_under(a, r):
        raise GateError("경로가 루트 밖: %s" % a)
    rest = a[len(r):].lstrip("/")
    return rest


# ---------------------------------------------------------------- 표 읽기
def _split_cells(line: str):
    """이스케이프되지 않은 `|`로 나눈다(`\\|`는 셀 안 문자)."""
    s = line.strip()
    if not s.startswith("|"):
        raise GateError("표 줄이 `|`로 시작하지 않는다: %r" % line[:80])
    s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, i = [], [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if c == "|":
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def read_section_table(text: str, heading_prefix: str):
    """절 제목 줄(`heading_prefix`로 시작) 아래 **첫 표**를 (머리 셀, 행 목록)으로. 절·표를 못 찾거나
    행의 셀 수가 머리와 다르면 GateError(표 파손, 00-common §9.2)."""
    lines = text.replace("\r\n", "\n").split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(heading_prefix)]
    if len(idx) != 1:
        raise GateError("절 %r을 정확히 하나 찾지 못함(%d개)" % (heading_prefix.strip(), len(idx)))
    i = idx[0] + 1
    level = len(heading_prefix) - len(heading_prefix.lstrip("#"))
    while i < len(lines) and not lines[i].startswith("|"):
        l = lines[i]
        if l.startswith("#"):
            lvl = len(l) - len(l.lstrip("#"))
            if lvl <= level:
                raise GateError("절 %r 안에 표가 없다" % heading_prefix.strip())
        i += 1
    if i >= len(lines):
        raise GateError("절 %r 아래 표가 없다" % heading_prefix.strip())
    header = _split_cells(lines[i])
    if i + 1 >= len(lines) or not re.match(r"^\|\s*:?-{3,}", lines[i + 1].strip()):
        raise GateError("절 %r 표의 구분 줄이 없다" % heading_prefix.strip())
    sep = _split_cells(lines[i + 1])
    if len(sep) != len(header):
        raise GateError("절 %r 표 구분 줄 셀 수 불일치" % heading_prefix.strip())
    rows = []
    j = i + 2
    while j < len(lines) and lines[j].startswith("|"):
        cells = _split_cells(lines[j])
        if len(cells) != len(header):
            raise GateError("절 %r 표 %d번째 행 셀 수 %d != 머리 %d" % (heading_prefix.strip(), len(rows) + 1,
                                                               len(cells), len(header)))
        rows.append(cells)
        j += 1
    return header, rows


def _strip_code(cell: str) -> str:
    c = cell.strip()
    if c.startswith("`") and c.endswith("`") and len(c) >= 2:
        c = c[1:-1]
    if "`" in c:
        raise GateError("glob 셀에 백틱이 남음: %r" % cell)
    return c


# ---------------------------------------------------------------- 쓰기 경로표
@dataclass(frozen=True)
class PathRule:
    actor: str
    glob: str
    exclude: str | None
    condition: str


def read_write_paths(plan_text: str) -> tuple:
    header, rows = read_section_table(plan_text, "#### N3.12.2 ")
    if [h.strip() for h in header] != ["주체", "경로 glob", "제외 glob", "조건"]:
        raise GateError("N3.12.2 표 머리가 다르다: %r" % header)
    out = []
    for r in rows:
        actor, glob, excl, cond = (c.strip() for c in r)
        if actor not in ACTORS:
            raise GateError("N3.12.2 주체 값 집합 밖: %r" % actor)
        if cond not in CONDITIONS:
            raise GateError("N3.12.2 조건 값 집합 밖: %r" % cond)
        if cond in USER_ONLY_CONDITIONS and actor != "사용자":
            raise GateError("조건 %r은 주체 `사용자` 행에만 쓴다: %r" % (cond, actor))
        g = _strip_code(glob)
        if not g:
            raise GateError("빈 경로 glob")
        e = None if excl.strip() in ("--", "") else _strip_code(excl)
        out.append(PathRule(actor, g, e, cond))
    if not out:
        raise GateError("N3.12.2 표가 비었다")
    return tuple(out)


def _seg_match(pat_seg: str, seg: str, change_id):
    if "<id>" in pat_seg:
        if change_id is None:
            return False
        pat_seg = pat_seg.replace("<id>", change_id.casefold())
    return fnmatch.fnmatchcase(seg, pat_seg)


def _match_segs(ps, xs, change_id):
    # ps: 패턴 조각, xs: 경로 조각. `**`는 0개 이상 조각.
    if not ps:
        return not xs
    if ps[0] == "**":
        for k in range(len(xs) + 1):
            if _match_segs(ps[1:], xs[k:], change_id):
                return True
        return False
    if not xs:
        return False
    return _seg_match(ps[0], xs[0], change_id) and _match_segs(ps[1:], xs[1:], change_id)


def match_glob(pattern: str, rel_path: str, change_id: str | None) -> bool:
    """§4.1: `/`로 조각을 나누고 `**`는 0개 이상 조각, 나머지는 `fnmatchcase`. `<id>`는 조각 안 부분 문자열
    토큰으로 `change_id`로 치환(없으면 맞지 않음). 패턴과 경로 모두 casefold 뒤 대조(review33 M2-02)."""
    p = pattern.casefold().split("/")
    x = rel_path.replace("\\", "/").casefold().split("/")
    return _match_segs(p, x, change_id)


def _match_any_id(pattern, rel_path):
    # overlaps용: `<id>`를 한 조각 안의 임의 문자열로 본다.
    return match_glob(pattern.replace("<id>", "*"), rel_path, None)


def overlaps_any(rel_path: str, rules) -> bool:
    """경로가 표의 어떤 행(주체 무관)의 경로 glob에 맞으면 참(계획 N3.12.2 hook 판정 범위).
    worktree 밖 경로는 호출자가 걸러 낸다(§4.1: 어느 worktree에도 속하지 않는 경로는 거짓)."""
    return any(_match_any_id(r.glob, rel_path) for r in rules)


@dataclass(frozen=True)
class WriteContext:
    rules: tuple
    change_id: str | None = None
    bootstrapped: bool = False
    gate_change_ok: bool = False   # 그 변경의 spec card가 게이트 변경이고 승인 기록이 있다


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str
    rule: PathRule | None = None
    pending: str | None = None    # EL3·EL4가 내용으로 판정할 조건(승인 기록 / status 전이만)


def _row_matches(r: PathRule, rel, change_id):
    return match_glob(r.glob, rel, change_id) and not (r.exclude and match_glob(r.exclude, rel, change_id))


def globs_of(actor, rules):
    return [r.glob + (" (제외 %s)" % r.exclude if r.exclude else "") + " [%s]" % r.condition
            for r in rules if r.actor == actor]


def allowed(actor: str, rel_path: str, ctx: WriteContext) -> Verdict:
    """§4.1 allowed. `판정 환경` 행 우선, 그 주체 행 중 (glob 일치 ∧ 제외 불일치 ∧ 조건 참)이 있으면 허용.
    `판정 트리` 기본 거부는 '다른 조건의 행에 맞지 않는 트리 안 경로'에 사용자 행만 맞는다는 것으로 성립한다."""
    if actor not in ACTORS:
        return Verdict(False, "알 수 없는 주체 %r" % actor)
    rules = ctx.rules
    env_rows = [r for r in rules if r.condition == "판정 환경" and _row_matches(r, rel_path, ctx.change_id)]
    if env_rows and actor != "사용자":
        return Verdict(False, "`판정 환경` 행 우선: 사용자만 쓴다", env_rows[0])
    matched_false = None
    for r in rules:
        if r.actor != actor or not _row_matches(r, rel_path, ctx.change_id):
            continue
        c = r.condition
        if c in ("없음", "자기 변경 id", "판정 환경", "판정 트리"):
            return Verdict(True, "허용", r)
        if c == "게이트 변경":
            if ctx.gate_change_ok:
                return Verdict(True, "허용(게이트 변경 spec card + 승인 기록)", r)
            matched_false = matched_false or (r, "조건 `게이트 변경` 거짓(게이트 변경 spec card·승인 기록 없음)")
            continue
        if c == "부트스트랩":
            if not ctx.bootstrapped:
                return Verdict(True, "허용(부트스트랩 완료 표지 전)", r)
            matched_false = matched_false or (r, "조건 `부트스트랩` 거짓(부트스트랩 완료 표지 있음)")
            continue
        if c in CONTENT_CONDITIONS:
            return Verdict(True, "허용(내용 조건 %s는 EL3·EL4가 판정)" % c, r, pending=c)
        matched_false = matched_false or (r, "조건 %r 거짓" % c)
    if matched_false:
        return Verdict(False, matched_false[1], matched_false[0])
    in_tree = [r for r in rules if r.condition == "판정 트리" and _row_matches(r, rel_path, ctx.change_id)]
    if in_tree:
        return Verdict(False, "맞는 행 없음(`판정 트리` 기본 거부: 사용자만 쓴다)", in_tree[0])
    return Verdict(False, "맞는 행 없음")


def classify(rel_path: str):
    """§4.3 경로 5분류(source/test/tool/data/doc) 또는 None."""
    rp = rel_path.replace("\\", "/")
    for k, v in CLASS_EXPLICIT.items():
        if rp.casefold() == k.casefold():
            return v
    for name, globs, excls in CLASS_GLOBS:
        if any(match_glob(g, rp, None) for g in globs) and not any(match_glob(e, rp, None) for e in excls):
            return name
    return None


def source_dirs():
    """소스 분류가 들어 있는 디렉터리(루트 상대, test-author 열람 거부 §6.4의 '포함' 판정)."""
    out = set()
    for k, v in CLASS_EXPLICIT.items():
        if v == "source":
            out.add(os.path.dirname(k))
    for name, globs, _ in CLASS_GLOBS:
        if name == "source":
            for g in globs:
                out.add(os.path.dirname(g))
    return sorted(out)


def dir_contains_source(rel_dir: str) -> bool:
    d = rel_dir.replace("\\", "/").strip("/").casefold()
    for s in source_dirs():
        sc = s.casefold()
        if d == "" or sc == d or sc.startswith(d + "/"):
            return True
    return False


# ---------------------------------------------------------------- 실행 환경
@dataclass
class Env:
    main_root: str
    common_dir: str
    gate_path: str | None
    gate_exists: bool
    gate_master: str | None
    config: dict
    bootstrapped: bool
    plan_text: str
    rules: tuple
    source: str                       # "gate" | "workspace"
    warnings: list = field(default_factory=list)

    @property
    def cache_root(self):
        return self.common_dir.rstrip("/") + "/" + CACHE_DIRNAME

    @property
    def wt_dir(self):
        # §12 W = 작업 저장소의 형제 wt 디렉터리
        return norm_abs(os.path.dirname(self.main_root.rstrip("/")) + "/wt")

    def gate_args(self):
        return ["--git-dir", self.gate_path]

    def read_base(self, path):
        """판정에 쓰는 판(gate master, 부트스트랩 전이면 메인 HEAD)의 파일 바이트 또는 None."""
        if self.source == "gate":
            return show_blob(self.gate_args(), "%s:%s" % (self.gate_master, path))
        return show_blob(["-C", self.main_root], "HEAD:%s" % path)


def parse_config(data: bytes) -> dict:
    try:
        cfg = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise GateError("gate_config.json을 읽지 못함: %s" % e)
    if not isinstance(cfg, dict):
        raise GateError("gate_config.json이 객체가 아니다")
    return cfg


def main_worktree_of(start_dir: str):
    """(메인 worktree 루트, git-common-dir). `git worktree list --porcelain`의 첫 항목이 메인이다."""
    wt = worktree_of(norm_abs(start_dir))
    if wt is None:
        raise GateError("저장소 밖: %s" % start_dir)
    top, common = wt
    out = git_text(["-C", top, "worktree", "list", "--porcelain"])
    first = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            first = norm_abs(line[len("worktree "):].strip())
            break
    if first is None:
        raise GateError("worktree 목록이 비었다")
    return first, common


def list_worktrees(main_root):
    """[(경로, 브랜치 짧은 이름 또는 None)]."""
    out = git_text(["-C", main_root, "worktree", "list", "--porcelain"])
    res, cur = [], None
    for line in out.splitlines() + [""]:
        if line.startswith("worktree "):
            cur = [norm_abs(line[len("worktree "):].strip()), None]
        elif line.startswith("branch ") and cur is not None:
            b = line[len("branch "):].strip()
            cur[1] = b[len("refs/heads/"):] if b.startswith("refs/heads/") else b
        elif line == "" and cur is not None:
            res.append(tuple(cur))
            cur = None
    return res


ROLE_BRANCH_RE = re.compile(r"^role/(code|test|audit)/([0-9]{8}-[a-z0-9][a-z0-9-]*)$")


def role_of_branch(branch):
    """(짧은 역할, id) 또는 None."""
    if not branch:
        return None
    m = ROLE_BRANCH_RE.match(branch)
    return (m.group(1), m.group(2)) if m else None


def load_env(start_dir: str) -> Env:
    """모든 겹이 읽는 판(§4.4): gate가 있으면 gate `master`, 없으면(부트스트랩 전) 메인 HEAD."""
    main_root, common = main_worktree_of(start_dir)
    head_cfg_bytes = show_blob(["-C", main_root], "HEAD:%s" % CONFIG_PATH)
    if head_cfg_bytes is None:
        raise GateError("메인 HEAD에 %s이 없다" % CONFIG_PATH)
    head_cfg = parse_config(head_cfg_bytes)
    gate_path = head_cfg.get("gate_path")
    if not isinstance(gate_path, str) or not gate_path:
        raise GateError("gate_config.json에 gate_path가 없다")
    gate_path = norm_abs(gate_path)
    gate_exists = os.path.isdir(gate_path)
    warnings = []
    gate_master = None
    if gate_exists:
        rc, out = git_try(["--git-dir", gate_path, "rev-parse", "--verify", "--quiet", "refs/heads/master^{commit}"])
        if rc == 0:
            gate_master = out.decode().strip()
    if gate_master:
        cfg_b = show_blob(["--git-dir", gate_path], "%s:%s" % (gate_master, CONFIG_PATH))
        if cfg_b is None:
            raise GateError("gate master에 %s이 없다" % CONFIG_PATH)
        cfg = parse_config(cfg_b)
        plan = show_blob(["--git-dir", gate_path], "%s:%s" % (gate_master, PLAN_PATH))
        source = "gate"
    else:
        # DESIGN-GAP: §8.1은 '표지 전에는 작업 저장소 판 게이트 코드로 돌고 경고'를 EL3에 대해서만 적었다. gate가 없을 때
        # EL1·EL2·세션 시작도 같은 규칙(메인 worktree HEAD 판, 경고)으로 돈다. 표지가 있는데 gate가 없으면 실패(§3.3 행 6).
        cfg = head_cfg
        if cfg.get("bootstrapped") is True:
            # §3.3 행 6: 표지 뒤에는 gate가 없는 것도 실패
            raise GateError("부트스트랩 완료 표지가 있는데 gate 저장소(%s) 또는 그 master가 없다" % gate_path)
        plan = show_blob(["-C", main_root], "HEAD:%s" % PLAN_PATH)
        source = "workspace"
        warnings.append("부트스트랩 완료 전: gate 저장소가 없어 작업 저장소 HEAD 판 계획서·게이트 코드로 판정한다")
    if plan is None:
        raise GateError("계획서 %s를 읽지 못함" % PLAN_PATH)
    plan_text = plan.decode("utf-8")
    rules = read_write_paths(plan_text)
    return Env(main_root=main_root, common_dir=common, gate_path=gate_path, gate_exists=gate_exists,
               gate_master=gate_master, config=cfg, bootstrapped=cfg.get("bootstrapped") is True,
               plan_text=plan_text, rules=rules, source=source, warnings=warnings)


# ---------------------------------------------------------------- 게이트 코드 풀기와 캐시(§3.2·§4.4)
def tree_blobs(repo_args, commit, prefix, exclude=()):
    """`git ls-tree -r -z <commit> <prefix>`의 blob 항목 {prefix 뒤 상대 경로: blob id}. `git archive`는
    `.gitattributes`의 export-ignore를 따르므로 쓰지 않는다(review29 A1)."""
    out = git(repo_args + ["ls-tree", "-r", "-z", "--full-tree", commit, "--", prefix])
    res = {}
    for ent in out.decode("utf-8").split("\0"):
        if not ent:
            continue
        meta, path = ent.split("\t", 1)
        mode, typ, oid = meta.split()
        if typ != "blob" or any(path.startswith(e) for e in exclude):
            continue
        if mode == "120000":
            raise GateError("게이트 코드에 심볼릭 링크: %s" % path)
        res[path[len(prefix):]] = oid
    return res


def extract_blobs(repo_args, mapping, dest):
    for rel, oid in mapping.items():
        data = git(repo_args + ["cat-file", "blob", oid])
        if blob_id(data) != oid:
            raise GateError("blob 내용이 id와 다르다: %s" % rel)
        p = os.path.join(dest, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(data)


def dir_matches(dest, mapping):
    # 캐시 파일은 `git cat-file blob` 원시 바이트로 쓰므로 blob id는 필터 없는 해시(`git hash-object --no-filters`와 같다,
    # §4.4의 `git hash-object` 대조)로 계산한다 -- 파일마다 git을 띄우지 않는다(WP-10).
    """디렉터리의 파일 집합과 blob id가 mapping과 같은가(캐시 훼손 감지, review29 Q-11).
    `__pycache__`도 대조에 넣는다(남는 파일 = 불일치) -- .pyc는 소스 mtime·크기만으로 유효성을 판단하므로 심은
    .pyc가 소스 대신 실행될 수 있다. 게이트 실행기는 `sys.dont_write_bytecode = True`로 캐시에 .pyc를 만들지 않는다."""
    seen = {}
    for root, dirs, files in os.walk(dest):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, dest).replace("\\", "/")
            with open(full, "rb") as fh:
                seen[rel] = blob_id(fh.read())
    return seen == mapping


_HEX40_DIR = re.compile(r"^[0-9a-f]{40}$")


def ensure_cache(env: "Env") -> str:
    """게이트 코드 캐시 `<git-common-dir>/gmid-gate-cache/<커밋 id>/`를 검증하고 없거나 다르면 다시 푼다.
    쓰기는 임시 이름 + 원자적 이름 바꾸기, 상한은 커밋 id 하나(WP-10)."""
    import shutil
    import tempfile
    if env.source == "gate":
        repo_args, commit = env.gate_args(), env.gate_master
    else:
        repo_args, commit = ["-C", env.main_root], git_text(["-C", env.main_root, "rev-parse", "HEAD"])
    mapping = tree_blobs(repo_args, commit, GATE_CODE_PREFIX, GATE_CODE_EXCLUDE)
    if not mapping:
        raise GateError("게이트 코드가 비었다(%s)" % commit)
    root = env.cache_root
    os.makedirs(root, exist_ok=True)
    dest = os.path.join(root, commit)
    if os.path.isdir(dest) and not dir_matches(dest, mapping):
        shutil.rmtree(dest)
    if not os.path.isdir(dest):
        tmp = tempfile.mkdtemp(prefix=".tmp-", dir=root)
        extract_blobs(repo_args, mapping, tmp)
        try:
            os.replace(tmp, dest)
        except OSError:
            shutil.rmtree(tmp, ignore_errors=True)
            if not (os.path.isdir(dest) and dir_matches(dest, mapping)):
                raise
    for name in os.listdir(root):   # 상한: 커밋 id 하나
        if name != commit and (_HEX40_DIR.match(name) or name.startswith(".tmp-")):
            shutil.rmtree(os.path.join(root, name), ignore_errors=True)
    if not dir_matches(dest, mapping):
        raise GateError("게이트 코드 캐시 대조 실패: %s" % dest)
    return dest.replace("\\", "/")


# ---------------------------------------------------------------- spec card 머리(게이트 변경 조건 등)
SPEC_KEYS_SINGLE = ("id", "phase", "evidence_type", "gate_change")
SPEC_KEYS_MULTI = ("activated_ic_case", "activated_ic_case_rename", "noop_activation_id", "approval")


def parse_spec_card(text: str, expect_id: str | None = None) -> dict:
    """spec card 머리 블록(§11.2): `key: value`, 모르는 키 거부. 본문 절은 `sections`에."""
    t = text.replace("\r\n", "\n")
    if not t.startswith("---\n"):
        raise GateError("spec card 머리 블록이 없다")
    end = t.find("\n---\n", 4)
    if end < 0:
        raise GateError("spec card 머리 블록이 닫히지 않았다")
    head = t[4:end].split("\n")
    body = t[end + 5:]
    card = {k: [] for k in SPEC_KEYS_MULTI}
    for line in head:
        if not line.strip():
            raise GateError("spec card 머리에 빈 줄")
        if ": " not in line:
            raise GateError("spec card 머리 줄 형식 위반: %r" % line)
        k, v = line.split(": ", 1)
        k, v = k.strip(), v.strip()
        if k in SPEC_KEYS_SINGLE:
            if k in card:
                raise GateError("spec card 키 중복: %s" % k)
            card[k] = v
        elif k in SPEC_KEYS_MULTI:
            card[k].append(v)
        else:
            raise GateError("spec card 모르는 키: %s" % k)
    for k in SPEC_KEYS_SINGLE:
        if k not in card:
            raise GateError("spec card 필수 키 없음: %s" % k)
    if not ID_RE.match(card["id"]):
        raise GateError("spec card id 형식 위반: %r" % card["id"])
    if expect_id is not None and card["id"] != expect_id:
        raise GateError("spec card id %r != 파일 이름 id %r" % (card["id"], expect_id))
    if card["evidence_type"] not in ("red-green", "equivalence", "test-only"):
        raise GateError("spec card evidence_type 값 밖: %r" % card["evidence_type"])
    if card["gate_change"] not in ("yes", "no"):
        raise GateError("spec card gate_change 값 밖: %r" % card["gate_change"])
    for a in card["approval"]:
        if not ID_RE.match(a):
            raise GateError("spec card approval id 형식 위반: %r" % a)
    sections = {}
    cur = None
    for line in body.split("\n"):
        if line.startswith("## "):
            cur = line[3:].strip()
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(line)
    card["sections"] = {k: "\n".join(v).strip("\n") for k, v in sections.items()}
    return card


def spec_card_path(change_id):
    return "docs/02-design/specs/%s.spec.md" % change_id
