"""merge gate (05-role-separation design §9, 00-common §8·§9, CC-1·CC-2).

* 계획서 판정 표 읽기 `read_plan_tables`·`plan_phase_tokens`(00-common §9.1·§9.2), `plan_tables_hash`(05 §15.2)
* 승인 기록 머리 파서 `parse_approval_header`(00-common §8.2), diff·staged_diff 해시
* 판정 기록 로더 `load_verification_record`(00-common §8.1 로더 규칙 1~10, 규칙마다 함수 하나)
* `red_failure_hash`와 red 수집 pytest 플러그인(`-p merge_gate`, 00-common §8.1)
* 커밋 판정 공용부(§8.2의 2·4·5 -- EL3 `role_commit_gate.py`와 EL4가 같은 함수를 쓴다)
* `receive --old --new`(EL4, §9.2), `plan-tables-hash <계획서>`(§15.2)

gate는 push된 코드를 실행하지 않는다(§3.2): 여기서 push된 트리는 `git cat-file`로 데이터로만 읽는다.
하위 명령 종료 코드(§17): 0 통과 / 1 거부 / 2 입력 오류.
"""
from __future__ import annotations

import ast
import datetime
import hashlib
import json
import math
import os
import re
import shlex
import sys
import unicodedata
from dataclasses import dataclass
from typing import Mapping

import role_paths as rp  # noqa: E402  (스크립트 실행이면 sys.path[0], 플러그인이면 PYTHONPATH 첫 원소 = 캐시)

GateError = rp.GateError
SCHEMA_PATH = ".ai/verification/_schema.json"
APPROVALS_DIR = ".ai/approvals/"
REQUIREMENTS_PATH = "tools/gates/requirements.txt"
CONFTEST_PATH = "skills/analog-gmid-design/assets/tests/conftest.py"
TESTS_REL = "skills/analog-gmid-design/assets/tests"
PLAN_PATH = rp.PLAN_PATH


# ================================================================ 00-common §9 계획서 판정 표
@dataclass(frozen=True)
class ICPart:
    phase: str
    sub: bool          # 칸의 괄호 안에서만 나오는 Phase


@dataclass(frozen=True)
class PlanTables:
    v_intro: Mapping[str, str]
    ic_parts: Mapping[str, tuple]
    ic_test: Mapping[str, str]
    phase_order: tuple


_TOKEN_RE = re.compile(r"(?<![0-9A-Za-z.\-])(0\.5|[1-5]|6[abc]|7[abc])(?=$|[\s,;:)*~/])")
_PAREN_RE = re.compile(r"\([^()]*\)")


def _split_parens(cell: str):
    outside, inside = cell, []
    while True:
        found = _PAREN_RE.findall(outside)
        if not found:
            break
        inside.extend(f[1:-1] for f in found)
        outside = _PAREN_RE.sub("", outside)
    return outside, inside


def _ordered_tokens(s: str):
    out = []
    for m in _TOKEN_RE.finditer(s):
        if m.group(1) not in out:
            out.append(m.group(1))
    return out


def _cell_tokens_ordered(cell: str):
    outside, inside = _split_parens(cell)
    ins = []
    for part in inside:
        for t in _ordered_tokens(part):
            if t not in ins:
                ins.append(t)
    return _ordered_tokens(outside), ins


def plan_phase_tokens(cell: str):
    """(괄호 밖 토큰 집합, 괄호 안 토큰 집합), 00-common §9.2."""
    o, i = _cell_tokens_ordered(cell)
    return set(o), set(i)


def _col(header, prefix):
    idx = [k for k, h in enumerate(header) if h.strip().startswith(prefix)]
    if len(idx) != 1:
        raise GateError("표 머리에서 %r 열을 정확히 하나 찾지 못함: %r" % (prefix, header))
    return idx[0]


def _first_backtick(cell):
    m = re.search(r"`([^`]+)`", cell)
    if not m:
        raise GateError("강제 test 칸에 백틱 토큰이 없다: %r" % cell[:80])
    return m.group(1)


def read_plan_tables_text(text: str) -> PlanTables:
    h41, r41 = rp.read_section_table(text, "### N4.1 ")
    ci, cp, ct = _col(h41, "ID"), _col(h41, "담당 Phase"), _col(h41, "강제 test")
    ic_parts, ic_test = {}, {}
    for r in r41:
        ic = r[ci].strip()
        if not re.fullmatch(r"IC[0-9]+", ic):
            raise GateError("N4.1 ID 형식 위반: %r" % ic)
        o, i = _cell_tokens_ordered(r[cp])
        parts = tuple([ICPart(p, False) for p in o] + [ICPart(p, True) for p in i if p not in o])
        if not o:
            raise GateError("N4.1 %s 담당 Phase 괄호 밖 토큰이 없다" % ic)
        if ic in ic_parts:
            raise GateError("N4.1 ID 중복: %s" % ic)
        ic_parts[ic] = parts
        ic_test[ic] = _first_backtick(r[ct])
    h42, r42 = rp.read_section_table(text, "### N4.2 ")
    vi, vd = _col(h42, "ID"), _col(h42, "도입")
    v_intro = {}
    for r in r42:
        v = r[vi].strip()
        if not re.fullmatch(r"V[0-9]+", v):
            raise GateError("N4.2 ID 형식 위반: %r" % v)
        o, _ = _cell_tokens_ordered(r[vd])
        if len(o) != 1:
            raise GateError("N4.2 %s 도입 칸 괄호 밖 토큰이 정확히 하나가 아니다: %r" % (v, o))
        v_intro[v] = o[0]
    h61, r61 = rp.read_section_table(text, "### N6.1 ")
    pc = _col(h61, "Phase")
    order, empty = [], 0
    for r in r61:
        o, _ = _cell_tokens_ordered(r[pc])
        if not o:
            empty += 1
            continue
        if len(o) != 1:
            raise GateError("N6.1 Phase 칸 토큰이 정확히 하나가 아니다: %r" % r[pc])
        if o[0] in order:
            raise GateError("N6.1 Phase 중복: %s" % o[0])
        order.append(o[0])
    if empty != 2:
        raise GateError("N6.1 빈 집합 행이 정확히 둘(`0`, `0(문서)`)이 아니다: %d" % empty)
    return PlanTables(v_intro=v_intro, ic_parts=ic_parts, ic_test=ic_test, phase_order=tuple(order))


def read_plan_tables(plan_path: str) -> PlanTables:
    with open(plan_path, "rb") as fh:
        data = fh.read()
    return read_plan_tables_text(data.decode("utf-8"))


def plan_tables_object(text: str) -> dict:
    """§15.2 해시 입력 객체."""
    t = read_plan_tables_text(text)
    wp = rp.read_write_paths(text)
    return {
        "v_intro": dict(t.v_intro),
        "ic_parts": {k: [[p.phase, p.sub] for p in v] for k, v in t.ic_parts.items()},
        "ic_test": dict(t.ic_test),
        "phase_order": list(t.phase_order),
        "write_paths": [[r.actor, r.glob, r.exclude, r.condition] for r in wp],
    }


def plan_tables_hash(text: str) -> str:
    obj = plan_tables_object(text)
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


# ================================================================ 00-common §8.2 승인 기록
APPROVAL_KEYS = ("id", "date", "target_kind", "target", "diff_base", "diff_head", "diff_path", "scope")
TARGET_KINDS = ("diff", "staged_diff", "decision", "plan_tables")


def _real_date8(s):
    try:
        datetime.datetime.strptime(s[:8], "%Y%m%d")
        return True
    except ValueError:
        return False


def parse_approval_header(text_or_bytes, filename: str) -> dict:
    """머리 블록 파싱. 위반이면 GateError. `filename`은 `<id>.md`(경로 가능)."""
    base = os.path.basename(filename.replace("\\", "/"))
    if base.startswith("_") or not base.endswith(".md"):
        raise GateError("승인 기록 파서 대상이 아니다: %s" % base)
    if isinstance(text_or_bytes, bytes):
        if text_or_bytes.startswith(b"\xef\xbb\xbf"):
            raise GateError("승인 기록에 BOM")
        try:
            text = text_or_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise GateError("승인 기록이 UTF-8이 아니다")
    else:
        text = text_or_bytes
        if text.startswith(chr(0xFEFF)):
            raise GateError("승인 기록에 BOM")
    lines = re.split(r"\r?\n", text)
    if not lines or lines[0] != "---":
        raise GateError("승인 기록 머리 블록 시작 `---`가 없다")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise GateError("승인 기록 머리 블록이 닫히지 않았다")
    rec = {"diff_path": []}
    for line in lines[1:end]:
        if line.lstrip().startswith("#"):
            raise GateError("승인 기록 머리에 주석 줄 금지")
        if ": " not in line:
            raise GateError("승인 기록 머리 줄 형식 위반: %r" % line)
        k, v = line.split(": ", 1)
        k, v = k.strip(), v.strip()
        if k not in APPROVAL_KEYS:
            raise GateError("승인 기록 모르는 키: %r" % k)
        if k == "diff_path":
            rec["diff_path"].append(v)
            continue
        if k in rec:
            raise GateError("승인 기록 키 중복: %s" % k)
        rec[k] = v
    for k in ("id", "date", "target_kind", "target", "scope"):
        if k not in rec:
            raise GateError("승인 기록 필수 키 없음: %s" % k)
    if not rp.ID_RE.match(rec["id"]) or not _real_date8(rec["id"]):
        raise GateError("승인 기록 id 형식 위반: %r" % rec["id"])
    if rec["id"] + ".md" != base:
        raise GateError("승인 기록 id %r != 파일 이름 %r" % (rec["id"], base))
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", rec["date"]):
        raise GateError("승인 기록 date 형식 위반")
    try:
        datetime.datetime.strptime(rec["date"], "%Y-%m-%d")
    except ValueError:
        raise GateError("승인 기록 date가 실제 날짜가 아니다")
    if rec["target_kind"] not in TARGET_KINDS:
        raise GateError("승인 기록 target_kind 값 밖: %r" % rec["target_kind"])
    if not rec["scope"]:
        raise GateError("승인 기록 scope가 비었다")
    kind = rec["target_kind"]
    has_diff = ("diff_base" in rec) or ("diff_head" in rec) or bool(rec["diff_path"])
    if kind in ("plan_tables", "decision"):
        if has_diff:
            raise GateError("target_kind %s에는 diff_* 키 금지" % kind)
        if kind == "plan_tables":
            if not rp.HEX64.match(rec["target"]):
                raise GateError("plan_tables target은 64자리 소문자 16진")
        else:
            items = [x.strip() for x in rec["target"].split(",")]
            if not all(items):
                raise GateError("decision target에 빈 원소")
            rec["target_list"] = items
    else:
        if not rp.HEX64.match(rec["target"]):
            raise GateError("%s target은 64자리 소문자 16진" % kind)
        if "diff_base" not in rec or not rp.HEX40.match(rec["diff_base"]):
            raise GateError("%s에는 diff_base(40자리 소문자 16진) 필수" % kind)
        if kind == "diff":
            if "diff_head" not in rec or not rp.HEX40.match(rec["diff_head"]):
                raise GateError("diff에는 diff_head(40자리 소문자 16진) 필수")
        elif "diff_head" in rec:
            raise GateError("staged_diff에는 diff_head 금지")
        if not rec["diff_path"]:
            raise GateError("%s에는 diff_path 1개 이상 필수" % kind)
        for p in rec["diff_path"]:
            _check_norm_path(p)
    return rec


def _check_norm_path(p):
    if (not p or "\t" in p or "\n" in p or "\\" in p or p.endswith("/") or p.startswith("/")
            or p.startswith("./") or p == "." or ".." in p.split("/") or "." in p.split("/")):
        raise GateError("diff_path가 정규화되지 않음: %r" % p)


def diff_hash_from_blobs(entries) -> str:
    """entries: [(path, base_blob, head_blob)] -- 00-common §8.2 blob 기반 식."""
    s = "".join("%s\t%s\t%s\n" % e for e in sorted(entries))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- 트리·index 보기
class TreeView:
    """커밋 트리(rev = 커밋 id) 또는 index(rev = ':')의 파일 읽기. repo_args = ['--git-dir', g] 또는 ['-C', d]."""

    def __init__(self, repo_args, rev):
        self.repo_args = list(repo_args)
        self.rev = rev
        self._blob_cache = {}
        # index는 git client hook이 준 GIT_INDEX_FILE(`commit -a`·`commit <경로>`의 임시 index)로 읽는다
        self.clean = False if rev == ":" else None

    def blob(self, path):
        if path in self._blob_cache:
            return self._blob_cache[path]
        spec = (":" + path) if self.rev == ":" else "%s:%s" % (self.rev, path)
        rc, out = rp.git_try(self.repo_args + ["rev-parse", "--verify", "--quiet", spec], clean=self.clean)
        res = None
        if rc == 0:
            b = out.decode().strip()
            rc2, t = rp.git_try(self.repo_args + ["cat-file", "-t", b], clean=self.clean)
            if rc2 != 0:
                raise GateError("객체 종류를 읽지 못함: %s" % spec)
            res = b if t.decode().strip() == "blob" else ("<%s>" % t.decode().strip())
        if len(self._blob_cache) > 4096:  # 상한(WP-10)
            self._blob_cache.clear()
        self._blob_cache[path] = res
        return res

    def read(self, path):
        b = self.blob(path)
        if b is None or b.startswith("<"):
            return None
        return rp.git(self.repo_args + ["cat-file", "blob", b], clean=self.clean)

    def list(self, prefix=""):
        if self.rev == ":":
            args = self.repo_args + ["ls-files", "-z", "--full-name"]
            if prefix:
                args += ["--", ":(top)" + prefix]
            out = rp.git(args, clean=False)
        else:
            args = self.repo_args + ["ls-tree", "-r", "-z", "--name-only", "--full-tree", self.rev]
            if prefix:
                args += ["--", prefix]
            out = rp.git(args)
        return [p for p in out.decode("utf-8").split("\0") if p]


def compute_diff_hash(base_view: TreeView, head_view: TreeView, paths, forbid_same=True) -> str:
    entries = []
    for p in sorted(paths):
        _check_norm_path(p)
        b, h = base_view.blob(p), head_view.blob(p)
        for x in (b, h):
            if x is not None and x.startswith("<"):
                raise GateError("diff_path가 blob이 아니다: %s" % p)
        if b is None and h is None:
            raise GateError("diff_path가 양쪽 모두 없다: %s" % p)
        if forbid_same and b == h:
            raise GateError("diff_path가 바뀌지 않았다: %s" % p)
        entries.append((p, b or "-", h or "-"))
    return diff_hash_from_blobs(entries)


def load_approvals(*views):
    """views의 `.ai/approvals/*.md`(이름이 `_`로 시작하지 않는 것)를 파싱한 목록. 파싱 실패 파일은
    승인으로 세지 않는다(더 엄격한 쪽 -- 통과로 바꾸지 않는다)."""
    out, seen = [], set()
    for v in views:
        if v is None:
            continue
        for p in v.list(APPROVALS_DIR):
            base = os.path.basename(p)
            if base.startswith("_") or not base.endswith(".md") or os.path.dirname(p) + "/" != APPROVALS_DIR:
                continue
            data = v.read(p)
            if data is None:
                continue
            key = (p, rp.blob_id(data))
            if key in seen:
                continue
            seen.add(key)
            try:
                out.append(parse_approval_header(data, p))
            except GateError:
                continue
    return out


# ================================================================ 00-common §8.1 판정 기록 로더
class LoaderReject(GateError):
    def __init__(self, rule, msg):
        super().__init__("로더 규칙 %s: %s" % (rule, msg))
        self.rule = rule


_BOMS = ((b"\x00\x00\xfe\xff", "UTF-32 BE"), (b"\xff\xfe\x00\x00", "UTF-32 LE"),
         (b"\xef\xbb\xbf", "UTF-8"), (b"\xfe\xff", "UTF-16 BE"), (b"\xff\xfe", "UTF-16 LE"))


def rule1_encoding(raw: bytes) -> str:
    for bom, name in _BOMS:
        if raw.startswith(bom):
            raise LoaderReject(1, "파일 머리에 %s BOM" % name)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise LoaderReject(1, "UTF-8 디코드 실패: %s" % e)


def rule2_json(text: str):
    def pairs(ps):
        d = {}
        for k, v in ps:
            if k in d:
                raise LoaderReject(2, "중복 키 %r" % k)
            d[k] = v
        return d

    def const(c):
        raise LoaderReject(2, "리터럴 %s 금지" % c)
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=const)
    except LoaderReject:
        raise
    except (json.JSONDecodeError, RecursionError) as e:
        raise LoaderReject(2, "JSON 파싱 실패: %s" % e)


def _bad_chars(s):
    return [c for c in s if unicodedata.category(c) in ("Cc", "Cs")]


def rule3_values(obj):
    stack = [obj]
    while stack:
        v = stack.pop()
        if isinstance(v, dict):
            for k, x in v.items():
                stack.append(k)
                stack.append(x)
        elif isinstance(v, list):
            stack.extend(v)
        elif isinstance(v, bool) or v is None:
            continue
        elif isinstance(v, (int, float)):
            try:
                f = float(v)
            except OverflowError:
                raise LoaderReject(3, "수 범위 초과")
            if not math.isfinite(f):
                raise LoaderReject(3, "유한하지 않은 수")
        elif isinstance(v, str):
            try:
                v.encode("utf-8")
            except UnicodeEncodeError:
                raise LoaderReject(3, "짝 없는 서로게이트")
            if _bad_chars(v):
                raise LoaderReject(3, "제어 문자(Cc·Cs) 포함: %r" % v[:40])


def rule4_schema(obj, schema):
    try:
        import jsonschema
    except ImportError as e:
        raise LoaderReject(4, "jsonschema import 실패: %s" % e)
    v = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errs = sorted(v.iter_errors(obj), key=lambda e: list(e.absolute_path))
    if errs:
        e = errs[0]
        raise LoaderReject(4, "스키마 위반(%d건) 첫 위반 %s: %s" % (len(errs), "/".join(map(str, e.absolute_path)),
                                                            e.message[:200]))


def rule5_identity(obj, file_id):
    if obj["id"] != file_id:
        raise LoaderReject(5, "파일 이름 id %r != id %r" % (file_id, obj["id"]))
    sc = os.path.basename(obj["spec_card"])
    if sc != obj["id"] + ".spec.md":
        raise LoaderReject(5, "spec_card 파일 이름 id가 id와 다르다: %r" % sc)


def rule6_dates_approvals(obj, read_approval):
    for x in [obj["id"]] + list(obj["approvals"]):
        if not _real_date8(x):
            raise LoaderReject(6, "앞 8자리가 실제 날짜가 아니다: %r" % x)
    for a in obj["approvals"]:
        data = read_approval(a)
        if data is None:
            raise LoaderReject(6, "승인 기록 파일이 없다: .ai/approvals/%s.md" % a)
        try:
            parse_approval_header(data, "%s.md" % a)
        except GateError as e:
            raise LoaderReject(6, "승인 기록 %s 머리 파싱 실패: %s" % (a, e))


def rule7_red_lengths(obj):
    red = obj.get("red")
    if red is not None and len(red["test_ids"]) != len(red["failure_hashes"]):
        raise LoaderReject(7, "red.test_ids와 red.failure_hashes 길이가 다르다")


_TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})(?![\s\S])")


def rule8_time(obj):
    t = obj["auditor_run"]["time"]
    if not _TIME_RE.match(t):
        raise LoaderReject(8, "auditor_run.time 형식 위반: %r" % t)
    try:
        datetime.datetime.fromisoformat(t)
    except ValueError as e:
        raise LoaderReject(8, "auditor_run.time을 읽지 못함: %s" % e)


_FILLERS = {chr(0x3164), chr(0x115F), chr(0x1160), chr(0xFFA0)}   # 한글 채움 문자(로더 규칙 9)


def _visible(s):
    for c in s:
        cat = unicodedata.category(c)
        if cat.startswith("Z") or cat in ("Cc", "Cf") or c in _FILLERS:
            continue
        return True
    return False


def rule9_visible(obj):
    fields = []
    for k, v in obj["checks"].items():
        fields.append(("checks.%s.basis" % k, v["basis"]))
    if obj.get("red"):
        fields += [("red.test_ids", x) for x in obj["red"]["test_ids"]]
    if obj.get("equivalence"):
        fields += [("equivalence.commands", x) for x in obj["equivalence"]["commands"]]
    for r in obj["reproduced_numbers"]:
        fields += [("reproduced_numbers.name", r["name"]), ("reproduced_numbers.command", r["command"])]
    fields.append(("auditor_run.worktree", obj["auditor_run"]["worktree"]))
    fields += [("auditor_run.commands", x) for x in obj["auditor_run"]["commands"]]
    for name, s in fields:
        if not _visible(s):
            raise LoaderReject(9, "보이는 문자가 없다: %s" % name)


def rule10_phase(obj, spec_phase, plan: PlanTables):
    order = list(plan.phase_order)
    if spec_phase not in order:
        raise LoaderReject(10, "spec card Phase %r가 phase_order에 없다" % spec_phase)
    for v, c in obj["checks"].items():
        if c["verdict"] == "N/A":
            intro = plan.v_intro.get(v)
            if intro is None or intro not in order:
                raise LoaderReject(10, "%s 도입 Phase를 계획서에서 찾지 못함" % v)
            if not order.index(spec_phase) < order.index(intro):
                raise LoaderReject(10, "%s N/A인데 Phase %s가 도입 %s보다 앞이 아니다" % (v, spec_phase, intro))
            m = re.match(r"도입 (\S+?): ", c["basis"])
            if not m or m.group(1) != intro:
                raise LoaderReject(10, "%s N/A basis가 `도입 %s: <사유>` 형식이 아니다" % (v, intro))
    v4 = obj["checks"]["V4"]
    if v4["verdict"] == "PASS":
        if not any(l.startswith("oracle 대조: ") for l in re.split(r"\r?\n", v4["basis"])):
            raise LoaderReject(10, "V4 PASS basis에 `oracle 대조: ` 줄이 없다")


def load_verification_record(raw: bytes, *, file_id: str, schema: dict, read_approval, spec_phase: str,
                             plan: PlanTables) -> dict:
    """00-common §8.1 로더 규칙 1~10. 위반이면 LoaderReject(메시지에 규칙 번호)."""
    text = rule1_encoding(raw)
    obj = rule2_json(text)
    rule3_values(obj)
    rule4_schema(obj, schema)
    rule5_identity(obj, file_id)
    rule6_dates_approvals(obj, read_approval)
    rule7_red_lengths(obj)
    rule8_time(obj)
    rule9_visible(obj)
    rule10_phase(obj, spec_phase, plan)
    return obj


# ================================================================ red 해시와 수집 플러그인
def red_failure_hash(test_id: str, exc_type) -> str:
    name = exc_type if isinstance(exc_type, str) else "%s.%s" % (exc_type.__module__, exc_type.__qualname__)
    return hashlib.sha256(("%s\n%s" % (test_id, name)).encode("utf-8")).hexdigest()


def read_new_symbols(interface_text: str):
    """interface card '신규 시그니처' 절의 (모듈, 심볼) 쌍 표(`| 모듈 | 심볼 | 시그니처 |`)."""
    text = interface_text.replace("\r\n", "\n")
    # 절 제목 `## 신규 시그니처` 아래 첫 표
    header, rows = rp.read_section_table(text, "## 신규 시그니처")
    mi, si = _col(header, "모듈"), _col(header, "심볼")
    out = set()
    for r in rows:
        m, s = r[mi].strip().strip("`"), r[si].strip().strip("`")
        if m and s:
            out.add((m, s))
    return out


_ALWAYS_RED = ("builtins.AssertionError", "builtins.Failed")
_NEW_SYMBOL_TYPES = ("builtins.ImportError", "builtins.ModuleNotFoundError", "builtins.AttributeError")


def _type_name(t):
    return "%s.%s" % (t.__module__, t.__qualname__)


def new_symbol_pair(exc):
    """05 §15 신규 심볼 판정의 세 형태. 해당 없으면 None."""
    if isinstance(exc, ModuleNotFoundError):
        return (exc.name, "*") if exc.name else None
    if isinstance(exc, ImportError):
        nf = getattr(exc, "name_from", None)
        return (exc.name, nf) if exc.name and nf else None
    if isinstance(exc, AttributeError):
        obj = getattr(exc, "obj", None)
        name = getattr(exc, "name", None)
        if obj is None or name is None:
            return None
        import types
        if isinstance(obj, types.ModuleType):
            return (obj.__name__, name)
        if isinstance(obj, type):
            return ("%s.%s" % (obj.__module__, obj.__qualname__), name)
        return None   # 인스턴스 속성은 신규 심볼 아님
    return None


class _RedCapture:
    def __init__(self):
        self.path = os.environ.get("GMID_RED_CAPTURE")
        # DESIGN-GAP: 00-common §8.1 — 플러그인이 interface card를 어디서 받는지 정하지 않았다. 환경 변수
        # GMID_INTERFACE_CARD로 받는다. 없으면 신규 심볼 목록이 비어 ImportError류는 red로 인정하지 않는다(엄격 쪽).
        card = os.environ.get("GMID_INTERFACE_CARD")
        self.new_symbols = set()
        if card:
            with open(card, "rb") as fh:
                self.new_symbols = read_new_symbols(fh.read().decode("utf-8"))

    def record(self, test_id, exc_type, exc_value):
        tn = _type_name(exc_type)
        if tn not in _ALWAYS_RED:
            if tn not in _NEW_SYMBOL_TYPES:
                return
            pair = new_symbol_pair(exc_value)
            if pair is None or pair not in self.new_symbols:
                return
        if not self.path:
            return
        with open(self.path, "a", encoding="utf-8") as fh:   # 케이스마다 append(WP-11)
            fh.write(json.dumps({"test_id": test_id, "exc_type": tn,
                                 "failure_hash": red_failure_hash(test_id, tn)}, ensure_ascii=False) + "\n")


_capture = None


def _cap():
    global _capture
    if _capture is None:
        _capture = _RedCapture()
    return _capture


def pytest_runtest_makereport(item, call):
    if call.when in ("setup", "call") and call.excinfo is not None:
        _cap().record(item.nodeid, call.excinfo.type, call.excinfo.value)
    return None


def pytest_exception_interact(node, call, report):
    import _pytest.reports
    if isinstance(report, _pytest.reports.CollectReport) and call.excinfo is not None:
        v = call.excinfo.value
        cause = getattr(v, "__cause__", None)
        if cause is not None:
            _cap().record(node.nodeid, type(cause), cause)
        else:
            _cap().record(node.nodeid, call.excinfo.type, v)


# ================================================================ 커밋 판정 공용부(§8.2의 2·4·5)
ROLE_VALUES = ("code", "test", "audit", "doc", "user")


def parse_trailers(message: str, repo_args):
    out = rp.git(repo_args + ["interpret-trailers", "--parse"], input=message.encode("utf-8"))
    res = []
    for line in out.decode("utf-8", "replace").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            res.append((k.strip(), v.strip()))
    return res


def trailer_values(trailers, key):
    return [v for k, v in trailers if k.casefold() == key.casefold()]


def judge_trailers(trailers, merge=False):
    """(role, change_id, 실패 목록). §8.2-2."""
    fails = []
    roles = trailer_values(trailers, "Role")
    cids = trailer_values(trailers, "Change-Id")
    role = roles[0] if len(roles) == 1 else None
    if len(roles) != 1 or role not in ROLE_VALUES:
        fails.append("트레일러 `Role: code|test|audit|doc|user`가 정확히 하나가 아니다(%r)" % roles)
        return None, None, fails
    cid = None
    if role in ("code", "test", "audit") or merge:
        if len(cids) != 1 or not rp.ID_RE.match(cids[0]):
            fails.append("트레일러 `Change-Id: <id>`가 정확히 하나가 아니거나 형식 위반(%r)" % cids)
        else:
            cid = cids[0]
    elif len(cids) == 1 and rp.ID_RE.match(cids[0]):
        cid = cids[0]
    return role, cid, fails


def casefold_collisions(added_paths, all_paths):
    """casefold하면 트리의 다른 경로와 같아지는 추가 경로(§4.1 EL3·EL4)."""
    by = {}
    for p in all_paths:
        by.setdefault(p.casefold(), set()).add(p)
    bad = []
    for p in added_paths:
        if len(by.get(p.casefold(), set()) | {p}) > 1:
            bad.append(p)
    return bad


def gate_change_ok(base_view: TreeView, change_id):
    """조건 `게이트 변경`: base의 spec card가 `gate_change: yes`이고 `approval:` 기록이 모두 있고 파싱된다."""
    if not change_id:
        return False
    data = base_view.read(rp.spec_card_path(change_id))
    if data is None:
        return False
    try:
        card = rp.parse_spec_card(data.decode("utf-8"), change_id)
    except (GateError, UnicodeDecodeError):
        return False
    if card["gate_change"] != "yes" or not card["approval"]:
        return False
    for a in card["approval"]:
        d = base_view.read(APPROVALS_DIR + a + ".md")
        if d is None:
            return False
        try:
            parse_approval_header(d, a + ".md")
        except GateError:
            return False
    return True


def status_only_change(before: bytes | None, after: bytes | None):
    """`status 전이만`: `status`를 뺀 나머지가 앞 판과 같다.
    DESIGN-GAP: 05 §8.2-5 — `status`의 위치를 정하지 않았다. 최상위 키 `status`로 읽는다. 앞 판이 없으면 거짓."""
    if before is None or after is None:
        return False
    try:
        a, b = json.loads(before.decode("utf-8")), json.loads(after.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    a.pop("status", None)
    b.pop("status", None)
    return a == b


def _plan_hash_or_none(data):
    if data is None:
        return None
    try:
        return plan_tables_hash(data.decode("utf-8"))
    except (GateError, UnicodeDecodeError):
        return None


def judge_commit_change(*, parent_view: TreeView, child_view: TreeView, changes, trailers, base_view: TreeView,
                        rules, bootstrapped: bool, layer: str, check_paths=True):
    """병합 아닌 커밋 하나의 §8.2 판정(1·2·4·5). changes: [(status, path)]. 실패 목록을 돌려준다.
    EL3: parent=HEAD, child=index. EL4: parent=첫 부모, child=그 커밋."""
    fails = []
    paths = [p for _, p in changes]
    added = [p for s, p in changes if s.startswith("A")]
    if added:
        coll = casefold_collisions(added, child_view.list())
        if coll:
            fails.append("casefold 충돌 경로 추가: %s" % ", ".join(coll))
    scoped = [p for p in paths if rp.overlaps_any(p, rules)]
    if not scoped:
        return fails   # 역할 밖 경로만: 트레일러 불필요(§8.2-1, review31 N-01)
    role, cid, tf = judge_trailers(trailers)
    if tf:
        return fails + tf
    classes = {rp.classify(p) for p in paths}
    if "source" in classes and "test" in classes:
        fails.append("소스와 test를 한 커밋에서 바꿈")
    actor = rp.ACTOR_OF_TRAILER[role]
    ctx = rp.WriteContext(rules=rules, change_id=cid, bootstrapped=bootstrapped,
                          gate_change_ok=gate_change_ok(base_view, cid))
    # DESIGN-GAP: §8.2-4 "staged 경로마다" — 역할 트레일러는 모든 경로, doc·user는 표와 겹치는 경로만 판정한다
    # (EL1 §5 판정 범위와 같게. 오케스트레이터가 표 밖 경로(다른 skill)를 함께 커밋하는 정상 흐름의 오거부 방지).
    judged = paths if role in ("code", "test", "audit") else scoped
    pending = {}
    if check_paths:
        for p in judged:
            v = rp.allowed(actor, p, ctx)
            if not v.ok:
                fails.append("경로 권한 거부: 주체 %s, %s -- %s%s" % (
                    actor, p, v.reason, (" (행 %s %s [%s])" % (v.rule.actor, v.rule.glob, v.rule.condition)) if v.rule else ""))
            elif v.pending:
                pending.setdefault(v.pending, []).append(p)
    non_approval = sorted(p for p in paths if not p.startswith(APPROVALS_DIR))
    approvals = None

    def staged_diff_ok():
        nonlocal approvals
        if approvals is None:
            approvals = load_approvals(child_view, parent_view)
        try:
            h = compute_diff_hash(parent_view, child_view, non_approval)
        except GateError as e:
            return None, str(e)
        return any(a["target_kind"] == "staged_diff" and a["target"] == h for a in approvals), h

    if "승인 기록" in pending or role == "user":
        ok, h = staged_diff_ok()
        if not ok:
            fails.append("`target_kind: staged_diff` 승인 기록 필요(target = %s)%s" % (
                h, " -- topology 변경" if "승인 기록" in pending else " -- `Role: user` 커밋"))
    for p in pending.get("status 전이만", []):
        if not status_only_change(parent_view.read(p), child_view.read(p)):
            fails.append("`status 전이만` 위반: %s" % p)
    if PLAN_PATH in paths:
        after = child_view.read(PLAN_PATH)
        h_after = _plan_hash_or_none(after)
        if h_after is None:
            fails.append("바뀐 계획서의 판정 표를 읽지 못함(표 파손)")
        else:
            h_before = _plan_hash_or_none(parent_view.read(PLAN_PATH))
            if h_before != h_after:
                if approvals is None:
                    approvals = load_approvals(child_view, parent_view)
                if not any(a["target_kind"] == "plan_tables" and a["target"] == h_after for a in approvals):
                    fails.append("판정 표 변경: `target_kind: plan_tables` 승인 기록 필요(target = %s)" % h_after)
    return fails


# ================================================================ EL4 receive (§9.2)
class Repo:
    def __init__(self, git_dir):
        self.args = ["--git-dir", git_dir]
        self._info = {}

    def text(self, args):
        return rp.git_text(self.args + args)

    def info(self, c):
        if c not in self._info:
            out = rp.git(self.args + ["show", "-s", "--format=%P%x00%T%x00%B", c]).decode("utf-8", "replace")
            parents, tree, msg = out.split("\0", 2)
            self._info[c] = {"parents": parents.split(), "tree": tree, "msg": msg,
                             "trailers": parse_trailers(msg, self.args)}
        return self._info[c]

    def is_ancestor(self, a, b):
        rc, _ = rp.git_try(self.args + ["merge-base", "--is-ancestor", a, b])
        return rc == 0

    def changes(self, a, b):
        out = rp.git(self.args + ["diff-tree", "-r", "-z", "--no-renames", "--name-status", a, b]).decode("utf-8")
        toks = [t for t in out.split("\0") if t]
        return [(toks[i], toks[i + 1]) for i in range(0, len(toks) - 1, 2)]


def _role(repo, c):
    r = trailer_values(repo.info(c)["trailers"], "Role")
    return r[0] if len(r) == 1 else None


def _cid(repo, c):
    r = trailer_values(repo.info(c)["trailers"], "Change-Id")
    return r[0] if len(r) == 1 else None


def _first_parent_chain(repo, start, stop, allowed_set):
    """start에서 첫 부모를 따라 stop(제외)까지. 병합이 끼거나 집합 밖으로 나가면 None."""
    chain, x = [], start
    while x != stop:
        if x not in allowed_set:
            return None
        ps = repo.info(x)["parents"]
        if len(ps) != 1:
            return None
        chain.append(x)
        x = ps[0]
    return chain


def v1_command_check(cmd: str, *, python_path: str, old: str, strict_needed, phase):
    """§9.2-7 V1 명령 형태(형식 검사). 실패 목록."""
    fails = []
    try:
        toks = shlex.split(cmd)
    except ValueError as e:
        return ["V1 명령을 나누지 못함: %s" % e]
    i = 0
    while i < len(toks) and re.match(r"^(PYTHONPATH|PYTHONPYCACHEPREFIX)=", toks[i]):
        i += 1
    rest = toks[i:]

    def nz(p):
        return rp.ncase(p.replace("\\", "/"))
    if len(rest) < 4:
        return ["V1 명령이 너무 짧다"]
    if not (rest[0] == "$PY" or nz(rest[0]) == nz(python_path)):
        fails.append("V1 첫 토큰이 `$PY`·python_path가 아니다: %r" % rest[0])
    if rest[1:4] != ["-P", "-m", "pytest"]:
        fails.append("V1이 `-P -m pytest`로 이어지지 않는다: %r" % rest[1:4])
    args = rest[4:]
    c_vals, rootdir, confcut, paths, phase_tok, strict_tok = [], [], [], [], [], []
    # DESIGN-GAP: §9.2-7 — 필수 토큰 외 허용 옵션을 정하지 않았다. N4.2 V1이 금지한 `-k`·`--deselect`·`-x`와
    # 선택 옵션(`-m` 표식 선택 등)을 막기 위해 허용 목록으로 판정한다.
    j = 0
    while j < len(args):
        t = args[j]
        if t == "-c":
            if j + 1 >= len(args):
                fails.append("V1 `-c` 값 없음")
                break
            c_vals.append(args[j + 1])
            j += 2
            continue
        if t == "-p":
            if j + 1 >= len(args):
                fails.append("V1 `-p` 값 없음")
                break
            if args[j + 1] not in ("merge_gate", "no:cacheprovider"):
                fails.append("V1 `-p %s` 허용 밖" % args[j + 1])
            j += 2
            continue
        if t.startswith("--rootdir="):
            rootdir.append(t.split("=", 1)[1])
        elif t.startswith("--confcutdir="):
            confcut.append(t.split("=", 1)[1])
        elif t.startswith("--gmid-phase="):
            phase_tok.append(t.split("=", 1)[1])
        elif t.startswith("--gmid-strict="):
            strict_tok.append(t.split("=", 1)[1])
        elif t in ("--continue-on-collection-errors", "-q", "-v", "-ra", "-rA", "--gmid-dod") or t.startswith("--tb="):
            pass
        elif t.startswith("-"):
            fails.append("V1 허용 밖 옵션: %r" % t)
        else:
            paths.append(t)
        j += 1
    if len(c_vals) != 1:
        fails.append("V1 `-c <값>`이 정확히 하나가 아니다")
    else:
        cv = c_vals[0].replace("\\", "/")
        if os.path.basename(cv) != "pytest_gate.ini":
            fails.append("V1 `-c` 파일 이름이 pytest_gate.ini가 아니다")
        d = os.path.dirname(cv).rstrip("/")
        if not rp.ncase(d).endswith(rp.ncase("%s/%s" % (rp.CACHE_DIRNAME, old))):
            fails.append("V1 `-c` 디렉터리가 gmid-gate-cache/<old>/가 아니다")
    if len(rootdir) != 1 or len(confcut) != 1 or (rootdir and confcut and nz(rootdir[0]) != nz(confcut[0])):
        fails.append("V1 `--rootdir=`·`--confcutdir=`가 한 토큰씩 정확히 하나이고 같아야 한다")
    elif len(paths) != 1 or nz(paths[0]).rstrip("/") != nz(rootdir[0]).rstrip("/") + "/" + TESTS_REL:
        fails.append("V1 test 경로 인자가 정확히 하나 `<복제본 루트>/%s`가 아니다: %r" % (TESTS_REL, paths))
    elif not re.match(r"^[a-zA-Z]:/|^/", rootdir[0].replace("\\", "/")):
        fails.append("V1 복제본 루트가 절대 경로가 아니다")
    if strict_needed is not None:
        want = ",".join(sorted(strict_needed))
        if phase_tok != [phase]:
            fails.append("V1 `--gmid-phase=%s`가 없다(%r)" % (phase, phase_tok))
        if strict_tok != [want]:
            fails.append("V1 `--gmid-strict=%s`와 다르다(%r)" % (want, strict_tok))
    return fails


def conftest_has_gmid_phase(data):
    """CC-3 병합 전 판정식(§9.2-7): conftest AST에 `addoption("--gmid-phase", …)` 호출."""
    if data is None:
        return False
    try:
        tree = ast.parse(data.decode("utf-8"))
    except (SyntaxError, UnicodeDecodeError, ValueError):
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "addoption" \
                and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "--gmid-phase":
            return True
    return False


def strict_set(old_view: TreeView, card: dict):
    """00-common §9.3: 같은 Phase의 병합된 spec card `activated_ic_case` ∪ 이번 card 필드(이름 바꿈 적용)."""
    keys, renames = set(), []
    for p in old_view.list(".ai/verification/"):
        if not p.endswith(".json") or os.path.dirname(p) != ".ai/verification" or os.path.basename(p).startswith("_"):
            continue
        rid = os.path.basename(p)[:-5]
        cd = old_view.read(rp.spec_card_path(rid))
        if cd is None:
            continue
        c = rp.parse_spec_card(cd.decode("utf-8"), rid)
        if c["phase"] == card["phase"]:
            keys |= set(c["activated_ic_case"])
            renames += c["activated_ic_case_rename"]
    keys |= set(card["activated_ic_case"])
    renames += card["activated_ic_case_rename"]
    for r in renames:
        m = re.match(r"^(\S+)\s*->\s*(\S+)$", r)
        if not m:
            raise GateError("activated_ic_case_rename 형식 위반: %r" % r)
        if m.group(1) in keys:
            keys.discard(m.group(1))
            keys.add(m.group(2))
    return keys


def receive(git_dir: str, old: str, new: str) -> list:
    """§9.2 판정. 실패 목록(비면 통과). 실패는 모두 모아 돌려준다(첫 두 단계 실패는 즉시)."""
    repo = Repo(git_dir)
    old_view = TreeView(repo.args, old)
    fails = []
    plan_b = old_view.read(PLAN_PATH)
    if plan_b is None:
        return ["old 계획서가 없다"]
    try:
        plan_text = plan_b.decode("utf-8")
        tables = read_plan_tables_text(plan_text)
        rules = rp.read_write_paths(plan_text)
        h_old = plan_tables_hash(plan_text)
    except (GateError, UnicodeDecodeError) as e:
        return ["old 계획서 판정 표를 파싱하지 못해 판정하지 않고 거부: %s" % e]
    cfg_b = old_view.read(rp.CONFIG_PATH)
    if cfg_b is None:
        return ["old에 %s이 없다" % rp.CONFIG_PATH]
    cfg = rp.parse_config(cfg_b)
    bootstrapped = cfg.get("bootstrapped") is True
    # 2 상태 기반 판정 표 검사
    old_apps = load_approvals(old_view)
    if not any(a["target_kind"] == "plan_tables" and a["target"] == h_old for a in old_apps):
        fails.append("old 계획서 판정 표 해시 %s의 `plan_tables` 승인 기록이 old 트리에 없다" % h_old)
    # 3 커밋 전수
    rl = ["rev-list", "--reverse", "%s..%s" % (old, new)]
    baseline = cfg.get("baseline_commit")
    if isinstance(baseline, str) and rp.HEX40.match(baseline):
        rl.append("^" + baseline)
    commits = [c for c in repo.text(rl).split() if c]
    cset = set(commits)
    role_commits = [c for c in commits if _role(repo, c) in ("code", "test", "audit")]
    merges = [c for c in commits if len(repo.info(c)["parents"]) > 1]
    for c in commits:
        inf = repo.info(c)
        if len(inf["parents"]) > 1:
            continue
        if not inf["parents"]:
            fails.append("%s: 부모 없는 커밋" % c[:12])
            continue
        p = inf["parents"][0]
        f = judge_commit_change(parent_view=TreeView(repo.args, p), child_view=TreeView(repo.args, c),
                                changes=repo.changes(p, c), trailers=inf["trailers"], base_view=old_view,
                                rules=rules, bootstrapped=bootstrapped, layer="EL4")
        fails += ["%s: %s" % (c[:12], x) for x in f]

    def out_of_role_merge(m):
        ps = repo.info(m)["parents"]
        if len(ps) != 2:
            return "부모가 정확히 둘이 아니다(%d)" % len(ps)
        if not repo.is_ancestor(old, ps[0]):
            return "첫 부모가 old와 같거나 그 후손이 아니다"
        diff = [p for _, p in repo.changes(ps[0], m) if rp.overlaps_any(p, rules)]
        if diff:
            return "역할 경로에서 트리가 첫 부모와 다르다: %s" % ", ".join(diff[:5])
        return None

    if not role_commits:
        for m in merges:
            why = out_of_role_merge(m)
            if why:
                fails.append("%s: 역할 밖 병합이 아닌 병합 거부 -- %s" % (m[:12], why))
        return fails
    # 4 변경 한 건 구조
    ids = {_cid(repo, c) for c in role_commits}
    if len(ids) != 1 or None in ids:
        return fails + ["역할 커밋의 Change-Id가 정확히 하나가 아니다: %r" % sorted(map(str, ids))]
    cid = ids.pop()
    card_b = old_view.read(rp.spec_card_path(cid))
    if card_b is None:
        return fails + ["old 트리에 spec card %s가 없다" % rp.spec_card_path(cid)]
    try:
        card = rp.parse_spec_card(card_b.decode("utf-8"), cid)
    except (GateError, UnicodeDecodeError) as e:
        return fails + ["spec card 파싱 실패: %s" % e]
    ev = card["evidence_type"]
    ni = repo.info(new)
    if len(ni["parents"]) != 1 or _role(repo, new) != "audit" or _cid(repo, new) != cid:
        return fails + ["new가 부모 하나인 `Role: audit`·`Change-Id: %s` 커밋이 아니다" % cid]
    T = K = None
    if ev in ("red-green", "equivalence"):
        M = ni["parents"][0]
        mi = repo.info(M) if M in cset else None
        if mi is None or len(mi["parents"]) != 2:
            return fails + ["new의 부모가 이번 push의 병합 커밋 M(부모 둘)이 아니다"]
        if merges != [M]:
            return fails + ["병합 커밋이 M 하나가 아니다(역할 커밋이 있는 push에는 역할 밖 병합이 끼지 못한다)"]
        M1, M2 = mi["parents"]
        if _role(repo, M) != "doc" or _cid(repo, M) != cid:
            fails.append("M 트레일러가 `Role: doc`·`Change-Id: %s`가 아니다" % cid)
        if mi["tree"] != repo.info(M2)["tree"]:
            fails.append("M 트리가 M^2(code 끝) 트리와 다르다")
        chain = _first_parent_chain(repo, M1, old, cset)
        if chain is None:
            return fails + ["old..M^1이 첫 부모 사슬이 아니다"]
        if ev == "red-green" and not chain:
            fails.append("red-green인데 `Role: test` 커밋이 없다")
        for c in chain:
            if _role(repo, c) != "test" or _cid(repo, c) != cid:
                fails.append("%s: test 사슬 커밋이 `Role: test`·`Change-Id: %s`가 아니다" % (c[:12], cid))
        if not repo.is_ancestor(M1, M2):
            fails.append("M^2가 M^1의 후손이 아니다")
        code = [c for c in repo.text(["rev-list", "%s..%s" % (M1, M2)]).split() if c]
        if not code:
            fails.append("code 커밋이 없다")
        for c in code:
            if len(repo.info(c)["parents"]) != 1 or _role(repo, c) != "code" or _cid(repo, c) != cid:
                fails.append("%s: code 쪽 커밋이 병합 아닌 `Role: code`·`Change-Id: %s`가 아니다" % (c[:12], cid))
        if set(commits) != set(chain) | set(code) | {M, new}:
            extra = set(commits) - (set(chain) | set(code) | {M, new})
            fails.append("커밋 집합이 모양과 다르다(끼어든 커밋 %s)" % ", ".join(sorted(x[:12] for x in extra)))
        T, K = M1, M2
    else:
        if merges:
            fails.append("test-only에 병합이 있다")
        chain = _first_parent_chain(repo, ni["parents"][0], old, cset)
        if chain is None or not chain:
            return fails + ["old..new^이 `Role: test` 1개 이상의 첫 부모 사슬이 아니다"]
        for c in chain:
            if _role(repo, c) != "test" or _cid(repo, c) != cid:
                fails.append("%s: `Role: test`·`Change-Id: %s`가 아니다" % (c[:12], cid))
        if set(commits) != set(chain) | {new}:
            fails.append("커밋 집합이 test-only 모양과 다르다")
        T, K = ni["parents"][0], None
    # 5 판정 기록
    new_view = TreeView(repo.args, new)
    rec_b = new_view.read(".ai/verification/%s.json" % cid)
    schema_b = old_view.read(SCHEMA_PATH)
    if rec_b is None:
        return fails + ["판정 기록 .ai/verification/%s.json이 없다" % cid]
    if schema_b is None:
        return fails + ["old 트리에 %s가 없다" % SCHEMA_PATH]
    try:
        rec = load_verification_record(
            rec_b, file_id=cid, schema=json.loads(schema_b.decode("utf-8")),
            read_approval=lambda a: new_view.read(APPROVALS_DIR + a + ".md"),
            spec_phase=card["phase"], plan=tables)
    except GateError as e:
        return fails + [str(e)]
    if rec["test_commit"] != T:
        fails.append("판정 기록 test_commit %s != T %s" % (rec["test_commit"][:12], T[:12]))
    if rec["code_commit"] != K:
        fails.append("판정 기록 code_commit %r != K %r" % (rec["code_commit"], K))
    if rec["evidence_type"] != ev:
        fails.append("판정 기록 evidence_type %s != spec card %s" % (rec["evidence_type"], ev))
    if not repo.is_ancestor(rec["base_commit"], old):
        fails.append("판정 기록 base_commit이 old이거나 그 조상이 아니다")
    # 7 V1 명령 형태 + 엄격 집합
    v1 = [c for c in rec["auditor_run"]["commands"] if c.startswith("V1: ")]
    if len(v1) != 1:
        fails.append("auditor_run.commands의 `V1: ` 원소가 정확히 하나가 아니다(%d)" % len(v1))
    else:
        strict = None
        if conftest_has_gmid_phase(old_view.read(CONFTEST_PATH)):
            strict = strict_set(old_view, card)
        fails += v1_command_check(v1[0][len("V1: "):], python_path=str(cfg.get("python_path", "")), old=old,
                                  strict_needed=strict, phase=card["phase"])
    # 8 auditor 판정
    for v, c in rec["checks"].items():
        if c["verdict"] == "FAIL":
            fails.append("checks.%s = FAIL" % v)
    # 9 V5 승인
    v5_hashes = re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", rec["checks"]["V5"]["basis"])
    if v5_hashes:
        apps = load_approvals(new_view)
        for h in v5_hashes:
            if not any(a["target_kind"] == "diff" and a["target"] == h for a in apps):
                fails.append("V5 diff 해시 %s의 승인 기록이 없다" % h)
    # 10 의존성
    fails += dependency_check(old_view.read(REQUIREMENTS_PATH))
    return fails


def dependency_check(req_bytes):
    import importlib.metadata as md
    if req_bytes is None:
        return ["%s가 없다" % REQUIREMENTS_PATH]
    pins = {}
    for line in req_bytes.decode("utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.fullmatch(r"([A-Za-z0-9_.\-]+)==([A-Za-z0-9_.\-+]+)", line)
        if not m:
            return ["requirements.txt 줄 형식 위반: %r" % line]
        pins[m.group(1).lower()] = m.group(2)
    fails = []
    for name in ("jsonschema", "pytest"):
        if name not in pins:
            fails.append("requirements.txt에 %s 고정 판이 없다" % name)
            continue
        try:
            have = md.version(name)
        except md.PackageNotFoundError:
            fails.append("%s가 설치돼 있지 않다" % name)
            continue
        if have != pins[name]:
            fails.append("%s 판 %s != 고정 판 %s" % (name, have, pins[name]))
    return fails


# ================================================================ CLI
def _main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="merge_gate.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("receive")
    r.add_argument("--old", required=True)
    r.add_argument("--new", required=True)
    r.add_argument("--git-dir", default=None)
    h = sub.add_parser("plan-tables-hash")
    h.add_argument("plan")
    c = sub.add_parser("check-record", help="판정 기록 하나를 로더 규칙 1~10으로(직접 재생용)")
    c.add_argument("--git-dir", required=True)
    c.add_argument("--rev", required=True, help="기록·승인 기록을 읽을 커밋")
    c.add_argument("--base", required=True, help="스키마·계획서·spec card를 읽을 커밋(base)")
    c.add_argument("--id", required=True)
    a = sub.add_parser("parse-approval")
    a.add_argument("file")
    a2 = sub.add_parser("diff-hash", help="00-common §8.2 diff 해시(base·head 커밋 또는 ':'=index)")
    a2.add_argument("--repo", required=True)
    a2.add_argument("--base", required=True)
    a2.add_argument("--head", required=True)
    a2.add_argument("paths", nargs="+")
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        if ns.cmd == "plan-tables-hash":
            with open(ns.plan, "rb") as fh:
                print(plan_tables_hash(fh.read().decode("utf-8")))
            return 0
        if ns.cmd == "parse-approval":
            with open(ns.file, "rb") as fh:
                rec = parse_approval_header(fh.read(), ns.file)
            print(json.dumps(rec, ensure_ascii=False))
            return 0
        if ns.cmd == "diff-hash":
            args = ["-C", ns.repo]
            print(compute_diff_hash(TreeView(args, ns.base), TreeView(args, ns.head), ns.paths))
            return 0
        if ns.cmd == "check-record":
            args = ["--git-dir", ns.git_dir]
            base, rev = TreeView(args, ns.base), TreeView(args, ns.rev)
            need = {"spec card": base.read(rp.spec_card_path(ns.id)), "판정 기록": rev.read(".ai/verification/%s.json" % ns.id),
                    "스키마": base.read(SCHEMA_PATH), "계획서": base.read(PLAN_PATH)}
            missing = [k for k, v in need.items() if v is None]
            if missing:
                print("없음: %s" % ", ".join(missing), file=sys.stderr)
                return 1
            card = rp.parse_spec_card(need["spec card"].decode("utf-8"), ns.id)
            load_verification_record(need["판정 기록"], file_id=ns.id, schema=json.loads(need["스키마"].decode("utf-8")),
                                     read_approval=lambda x: rev.read(APPROVALS_DIR + x + ".md"),
                                     spec_phase=card["phase"],
                                     plan=read_plan_tables_text(need["계획서"].decode("utf-8")))
            print("PASS")
            return 0
        # receive
        gd = ns.git_dir or os.environ.get("GIT_DIR") or "."
        fails = receive(os.path.abspath(gd), ns.old, ns.new)
        for f in fails:
            print("[EL4 거부] " + f, file=sys.stderr)
        return 1 if fails else 0
    except (GateError, OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print("[merge_gate] 거부(판정 불가): %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 1 if ns.cmd == "receive" else 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
