"""무결성 대조 (05-role-separation design §3.3).

'드러나게 한다' 행위(N3.12.0)를 감지한다. 대조 실패는 `<git-common-dir>/gmid-gate-cache/integrity-failed`
표지를 남겨 모든 게이트가 거부하는 상태로 만든다(fail-closed). `--scope session`이 전부 일치할 때만 표지를
지운다(복구 확인의 유일한 경로).

    $PY integrity.py check [--scope session|push|commit|gate] [--workspace <메인 worktree>] [--gate <gate 경로>]

행마다 한 줄 JSON `{"row", "ok", "expected", "actual"}`. 전부 일치 0 / 불일치 1 / 입력 오류 2(§17).
행 번호: 1 gate hook 바이트 / 2 작업 저장소 git 설정 / 3a accept-log 사슬 / 3b 구간 재판정 /
4 gate hooks 디렉터리·core.hooksPath / 5 설치된 Claude Code hook / 6 부트스트랩 완료 표지.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import role_paths as rp

GateError = rp.GateError
SCOPE_ROWS = {
    "session": ("1", "2", "3a", "3b", "4", "5", "6"),
    "push": ("1", "2", "3a", "4", "5", "6"),
    "commit": ("1", "2", "4", "6"),
    "gate": ("1", "2", "3a", "4", "6"),
}
GATE_FILES = {"hooks/pre-receive": "tools/gates/gate/pre-receive",
              "gate-runner.py": "tools/gates/gate/gate-runner.py"}
ACCEPT_LOG = "gmid-accept-log"
ROLE_HOOK_EVENTS = ("PreToolUse", "PostToolUse", "SubagentStop", "SessionStart")


class Ctx:
    """대조 입력: 작업 저장소(메인 worktree)·gate·gate master 판 설정."""

    def __init__(self, workspace, gate):
        self.workspace = rp.norm_abs(workspace)
        self.common = rp.norm_abs(rp.git_text(["-C", self.workspace, "rev-parse", "--git-common-dir"]), self.workspace)
        head_cfg = rp.parse_config(self._must(rp.show_blob(["-C", self.workspace], "HEAD:" + rp.CONFIG_PATH), "HEAD 설정"))
        self.gate = rp.norm_abs(gate) if gate else rp.norm_abs(head_cfg["gate_path"])
        self.gate_exists = os.path.isdir(self.gate)
        self.gate_master = None
        if self.gate_exists:
            rc, out = rp.git_try(["--git-dir", self.gate, "rev-parse", "--verify", "--quiet", "refs/heads/master^{commit}"])
            if rc == 0:
                self.gate_master = out.decode().strip()
        if self.gate_master:
            self.cfg = rp.parse_config(self._must(rp.show_blob(["--git-dir", self.gate], "%s:%s" % (self.gate_master, rp.CONFIG_PATH)),
                                                  "gate master 설정"))
        else:
            self.cfg = head_cfg
        self.bootstrapped = self.cfg.get("bootstrapped") is True or head_cfg.get("bootstrapped") is True

    @staticmethod
    def _must(v, what):
        if v is None:
            raise GateError("%s을 읽지 못함" % what)
        return v

    def gate_blob(self, path):
        if not self.gate_master:
            return None
        rc, out = rp.git_try(["--git-dir", self.gate, "rev-parse", "--verify", "--quiet", "%s:%s" % (self.gate_master, path)])
        return out.decode().strip() if rc == 0 else None

    def hash_file(self, file_path, attr_path):
        """eol 필터를 적용한 blob id(`git hash-object --path`, §3.3 행 1·5)."""
        return rp.git_text(["-C", self.workspace, "hash-object", "--path", attr_path, file_path])


def _row(row, ok, expected, actual):
    return {"row": row, "ok": bool(ok), "expected": expected, "actual": actual}


# ---------------------------------------------------------------- 행 1
def row1(c: Ctx):
    out = []
    for installed, src in GATE_FILES.items():
        f = os.path.join(c.gate, *installed.split("/"))
        exp = c.gate_blob(src)
        if not c.gate_exists or not os.path.isfile(f):
            ok = not c.bootstrapped
            out.append(_row("1", ok, exp or "(부트스트랩 전: 설치 전 허용)", "없음: %s" % f))
            continue
        if exp is None:
            out.append(_row("1", False, "gate master의 %s" % src, "gate master에 원본 없음"))
            continue
        act = c.hash_file(f, src)
        out.append(_row("1", act == exp, "%s %s" % (src, exp), "%s %s" % (installed, act)))
    return out


# ---------------------------------------------------------------- 행 2
def _config_entries(wt, pattern):
    rc, out = rp.git_try(["-C", wt, "config", "--show-origin", "--get-regexp", pattern])
    if rc not in (0, 1):
        raise GateError("git config 읽기 실패(%s, %s)" % (wt, pattern))
    ents = []
    for line in out.decode("utf-8", "replace").splitlines():
        if "\t" not in line:
            continue
        origin, kv = line.split("\t", 1)
        k, _, v = kv.partition(" ")
        ents.append((origin, k, v))
    return ents


def _origin_is(origin, path, wt):
    """`--show-origin`의 출처가 path 파일인가. 상대 출처는 `-C <wt>` 기준이다."""
    if not origin.startswith("file:"):
        return False
    return rp.ncase(rp.norm_abs(origin[len("file:"):], wt)) == rp.ncase(path)


def row2(c: Ctx):
    local_cfg = c.common.rstrip("/") + "/config"
    hooks_path = c.workspace.rstrip("/") + "/.githooks"
    gate_url = c.gate
    targets = [c.workspace] + [p for p, b in rp.list_worktrees(c.workspace) if rp.role_of_branch(b)]
    out = []
    for wt in targets:
        bad, seen_url, seen_hooks = [], None, None
        ents = []
        for pat in (r"^remote\.gate\.", r"^url\.", r"^core\.hookspath$"):
            ents += _config_entries(wt, pat)
        urls = [v for o, k, v in ents if k == "remote.gate.url"]
        for o, k, v in ents:
            if k == "remote.gate.url":
                if not _origin_is(o, local_cfg, wt) or rp.ncase(rp.norm_abs(v, wt)) != rp.ncase(gate_url):
                    bad.append("%s %s=%s" % (o, k, v))
                seen_url = v
            elif k == "remote.gate.fetch":
                if not _origin_is(o, local_cfg, wt):
                    bad.append("%s %s=%s" % (o, k, v))
            elif k.startswith("remote.gate."):
                bad.append("%s %s=%s" % (o, k, v))
            elif k == "core.hookspath":
                if not _origin_is(o, local_cfg, wt) or rp.ncase(rp.norm_abs(v, wt)) != rp.ncase(hooks_path):
                    bad.append("%s %s=%s" % (o, k, v))
                seen_hooks = v
            elif k.startswith("url.") and (k.endswith(".insteadof") or k.endswith(".pushinsteadof")):
                # gate URL을 바꾸는 것만(값이 remote.gate.url의 접두) -- review31 N-13
                for u in urls + [gate_url]:
                    if u.replace("\\", "/").lower().startswith(v.replace("\\", "/").lower()) and v:
                        bad.append("%s %s=%s" % (o, k, v))
                        break
        if seen_hooks is None:
            # DESIGN-GAP: §3.3 행 2는 허용 값만 적었고 core.hooksPath가 없는 경우를 정하지 않았다. 없으면 EL3가 돌지
            # 않으므로(§8.1) 불일치로 본다.
            bad.append("core.hooksPath 없음")
        if seen_url is None and c.bootstrapped:
            bad.append("remote.gate.url 없음(부트스트랩 뒤)")
        out.append(_row("2", not bad, "remote.gate.url=%s, core.hooksPath=%s (출처 %s)" % (gate_url, hooks_path, local_cfg),
                        "%s: %s" % (wt, "; ".join(bad) if bad else "일치")))
    return out


# ---------------------------------------------------------------- 행 3
def _read_log(c: Ctx):
    p = os.path.join(c.gate, ACCEPT_LOG)
    if not os.path.isfile(p):
        return None
    with open(p, "rb") as fh:
        text = fh.read().decode("utf-8", "replace")
    lines = []
    for l in text.splitlines():
        if not l.strip():
            continue
        parts = l.split()
        if len(parts) < 3 or not rp.HEX40.match(parts[0]) or not rp.HEX40.match(parts[1]):
            lines.append(None)
        else:
            lines.append((parts[0], parts[1]))
    return lines


def row3a(c: Ctx):
    if not c.gate_exists:
        return [_row("3a", not c.bootstrapped, "gate master 사슬", "gate 없음")]
    lines = _read_log(c)
    if lines is None or not lines:
        # 부트스트랩 ④(b) 뒤 로그가 없거나 비면 실패(review30 I6c). gate master가 없으면 아직 ④(b) 전이다.
        ok = (not c.bootstrapped) and c.gate_master is None
        return [_row("3a", ok, "accept-log 첫 줄 = baseline", "로그 없음 또는 빈 로그")]
    bad = []
    if any(l is None for l in lines):
        bad.append("형식이 깨진 줄")
    else:
        first = lines[0]
        if first[0] != first[1]:
            bad.append("첫 줄 old != new")
        base = c.cfg.get("baseline_commit")
        if isinstance(base, str) and base and first[0] != base:
            bad.append("첫 줄 %s != baseline_commit %s" % (first[0][:12], base[:12]))
        for a, b in zip(lines, lines[1:]):
            if b[0] != a[1]:
                bad.append("사슬 끊김 %s -> %s" % (a[1][:12], b[0][:12]))
        if lines[-1][1] != c.gate_master:
            bad.append("마지막 new %s != gate master %s" % (lines[-1][1][:12], str(c.gate_master)[:12]))
    return [_row("3a", not bad, "사슬 baseline..gate master", "; ".join(bad) or "일치 (%d줄)" % len(lines))]


def row3b(c: Ctx):
    """구간 재판정: 줄마다 그 old 판 게이트 코드의 merge_gate.py receive를 데이터만으로. 생략 캐시 없음(review31 N-06)."""
    lines = _read_log(c) if c.gate_exists else None
    if not lines:
        return [_row("3b", not c.bootstrapped or c.gate_master is None, "구간 재판정", "로그 없음")]
    if any(l is None for l in lines):
        return [_row("3b", False, "구간 재판정", "형식이 깨진 줄")]
    out = []
    py = sys.executable
    for old, new in lines:
        if old == new:
            continue
        tmp = tempfile.mkdtemp(prefix="gmid-rejudge-")
        try:
            mapping = rp.tree_blobs(["--git-dir", c.gate], old, rp.GATE_CODE_PREFIX, rp.GATE_CODE_EXCLUDE)
            rp.extract_blobs(["--git-dir", c.gate], mapping, tmp)
            p = subprocess.run([py, os.path.join(tmp, "merge_gate.py"), "receive", "--old", old, "--new", new,
                                "--git-dir", c.gate], capture_output=True, env=rp.git_env(clean=True),
                               cwd=tmp)
            ok = p.returncode == 0
            out.append(_row("3b", ok, "%s..%s 통과" % (old[:12], new[:12]),
                            "exit %d %s" % (p.returncode, p.stderr.decode("utf-8", "replace").strip()[:300])))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if not out:
        out.append(_row("3b", True, "구간 재판정", "재판정할 구간 없음"))
    return out


# ---------------------------------------------------------------- 행 4
def row4(c: Ctx):
    if not c.gate_exists:
        return [_row("4", not c.bootstrapped, "gate hooks 디렉터리", "gate 없음")]
    hd = os.path.join(c.gate, "hooks")
    others = sorted(f for f in (os.listdir(hd) if os.path.isdir(hd) else []) if f != "pre-receive")
    rc, out = rp.git_try(["--git-dir", c.gate, "config", "--show-origin", "--get", "core.hooksPath"], clean=True)
    hp = out.decode("utf-8", "replace").strip() if rc == 0 else ""
    bad = []
    if others:
        bad.append("다른 파일: %s" % ", ".join(others))
    if rc == 0:
        bad.append("gate core.hooksPath 있음: %s" % hp)
    elif rc != 1:
        bad.append("gate core.hooksPath 읽기 실패")
    return [_row("4", not bad, "hooks/에 pre-receive만, core.hooksPath 없음", "; ".join(bad) or "일치")]


# ---------------------------------------------------------------- 행 5
def row5(c: Ctx):
    out = []
    if not c.gate_master:
        return [_row("5", not c.bootstrapped, "설치된 역할 hook", "gate master 없음(부트스트랩 전)")]
    src = rp.tree_blobs(["--git-dir", c.gate], c.gate_master, "hooks/")
    py_src = {k: v for k, v in src.items() if re.fullmatch(r"role_[A-Za-z0-9_]+\.py", k)}
    js_src = {k: v for k, v in src.items() if re.fullmatch(r"role_[A-Za-z0-9_]+\.json", k)}
    inst_dir = os.path.join(c.workspace, ".claude", "hooks")
    installed = sorted(f for f in (os.listdir(inst_dir) if os.path.isdir(inst_dir) else [])
                       if re.fullmatch(r"role_[A-Za-z0-9_]+\.py", f))
    if not installed and not c.bootstrapped:
        return [_row("5", True, "설치된 역할 hook", "설치 전(부트스트랩 전)")]
    for name, oid in sorted(py_src.items()):
        f = os.path.join(inst_dir, name)
        if not os.path.isfile(f):
            out.append(_row("5", False, "hooks/%s %s" % (name, oid), "설치 안 됨"))
            continue
        act = c.hash_file(f, "hooks/" + name)
        out.append(_row("5", act == oid, "hooks/%s %s" % (name, oid), ".claude/hooks/%s %s" % (name, act)))
    extra = sorted(set(installed) - set(py_src))
    if extra:
        out.append(_row("5", False, "gate master의 role_*.py만", "남는 설치 파일: %s" % ", ".join(extra)))
    sp = os.path.join(c.workspace, ".claude", "settings.json")
    try:
        with open(sp, "rb") as fh:
            settings = json.loads(fh.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return out + [_row("5", False, ".claude/settings.json", "읽지 못함: %s" % e)]
    hooks = settings.get("hooks") if isinstance(settings, dict) else None
    events_seen = set()
    for name, oid in sorted(js_src.items()):
        meta = json.loads(rp.git(["--git-dir", c.gate, "cat-file", "blob", oid]).decode("utf-8"))
        stem = name[:-5]
        ev, mt = meta.get("event"), meta.get("matcher")
        events_seen.add(ev)
        found = []
        for e, blocks in (hooks or {}).items():
            for b in blocks or []:
                for h in (b.get("hooks") or []):
                    if stem in (h.get("command") or ""):
                        found.append((e, b.get("matcher")))
        ok = found == [(ev, mt)]
        out.append(_row("5", ok, "%s: %s/%s" % (stem, ev, mt), "%s: %r" % (stem, found)))
    if set(ROLE_HOOK_EVENTS) - events_seen:
        out.append(_row("5", False, "역할 hook 네 이벤트 %s" % (ROLE_HOOK_EVENTS,), "gate master의 hooks/role_*.json 이벤트 %r" % sorted(map(str, events_seen))))
    return out


# ---------------------------------------------------------------- 행 6
def row6(c: Ctx):
    if not c.bootstrapped:
        return [_row("6", True, "부트스트랩 완료 표지", "표지 없음(부트스트랩 전)")]
    missing = []
    if not c.gate_exists or not c.gate_master:
        missing.append("gate 저장소 또는 master")
    for installed in GATE_FILES:
        if not os.path.isfile(os.path.join(c.gate, *installed.split("/"))):
            missing.append("gate " + installed)
    if not os.path.isdir(os.path.join(c.workspace, ".claude", "hooks")):
        missing.append(".claude/hooks")
    return [_row("6", not missing, "표지 뒤 gate·hook 존재", "없음: " + ", ".join(missing) if missing else "있음")]


ROWS = {"1": row1, "2": row2, "3a": row3a, "3b": row3b, "4": row4, "5": row5, "6": row6}


def marker_path(common_dir):
    return os.path.join(common_dir, rp.CACHE_DIRNAME, rp.INTEGRITY_MARKER)


def check(scope: str, workspace: str, gate: str | None = None):
    """(결과 행 목록, 전부 일치 여부). 불일치면 표지를 쓰고, session 전부 일치면 표지를 지운다."""
    c = Ctx(workspace, gate)
    results = []
    for r in SCOPE_ROWS[scope]:
        try:
            results += ROWS[r](c)
        except GateError as e:
            results.append(_row(r, False, "대조", "대조 실패(판정 불가): %s" % e))
    ok = all(x["ok"] for x in results)
    mp = marker_path(c.common)
    if not ok:
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        with open(mp, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"scope": scope, "failed": [x for x in results if not x["ok"]]}, ensure_ascii=False) + "\n")
    elif scope == "session" and os.path.exists(mp):
        os.remove(mp)
    return results, ok


RECOVERY = ("무결성 대조 실패: 위 행의 expected와 actual이 다르다. 모든 게이트가 거부하는 상태다(integrity-failed 표지). "
            "복구: 사용자가 세션 밖에서 원인을 확인·복구한 뒤(gate 사본 재복사·설정 원복·hook 재설치, §13.4) "
            "`$PY tools/gates/integrity.py check --scope session`으로 전부 일치를 확인한다(그때만 표지가 지워진다).")


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="integrity.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ck = sub.add_parser("check")
    ck.add_argument("--scope", choices=sorted(SCOPE_ROWS), default="session")
    ck.add_argument("--workspace", default=None)
    ck.add_argument("--gate", default=None)
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        ws = ns.workspace
        if ws is None:
            if ns.scope == "gate":
                raise GateError("--scope gate에는 --workspace가 필요하다")
            ws, _ = rp.main_worktree_of(os.getcwd())
        results, ok = check(ns.scope, ws, ns.gate)
    except (GateError, OSError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(json.dumps({"row": "input", "ok": False, "expected": "", "actual": "%s: %s" % (type(e).__name__, e)},
                         ensure_ascii=False))
        return 2
    for r in results:
        print(json.dumps(r, ensure_ascii=False))
    if not ok:
        print(RECOVERY, file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
