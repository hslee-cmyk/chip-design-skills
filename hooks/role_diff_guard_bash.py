#!/usr/bin/env python
"""EL2 PostToolUse(Bash) 실행기 (05-role-separation design §7). 판정은 gate master 판 `tools/gates/role_hooks.py`.

얇은 실행기: gate master(부트스트랩 전이면 메인 worktree HEAD)의 `role_paths.py`로 게이트 코드 캐시
`<git-common-dir>/gmid-gate-cache/<커밋 id>/`를 검증·풀고(§4.4), 그 캐시의 `role_hooks.run()`을 부른다.
실행기 전체를 `try: … except BaseException: → exit 2`(§6.1-1: Claude Code는 exit 2로만 막는다).
네 실행기(role_guard / role_diff_guard_bash / role_diff_guard_stop / role_session_start)는 EVENT만 다르다.
"""
import sys

EVENT = "PostToolUse"


def _git(args):
    import os
    import subprocess
    env = dict(os.environ)
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
              "GIT_QUARANTINE_PATH", "GIT_PREFIX", "GIT_COMMON_DIR", "GIT_NAMESPACE"):
        env.pop(k, None)
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    p = subprocess.run(["git"] + args, capture_output=True, env=env)
    return p.returncode, p.stdout


def _load_gate_code(cwd):
    """gate master 판 role_paths.py를 모듈로 올려 캐시를 검증·풀고 (캐시 경로, 판정 환경)을 돌려준다."""
    import json
    import types
    rc, out = _git(["-C", cwd, "worktree", "list", "--porcelain"])
    if rc != 0:
        raise RuntimeError("저장소 밖에서 hook이 불렸다: %s" % cwd)
    main = next(l[len("worktree "):] for l in out.decode("utf-8").splitlines() if l.startswith("worktree "))
    rc, cfg = _git(["-C", main, "cat-file", "blob", "HEAD:tools/gates/gate_config.json"])
    if rc != 0:
        raise RuntimeError("메인 HEAD에 tools/gates/gate_config.json이 없다")
    gate = json.loads(cfg.decode("utf-8"))["gate_path"]
    rc, m = _git(["--git-dir", gate, "rev-parse", "--verify", "--quiet", "refs/heads/master^{commit}"])
    if rc == 0:
        rc, src = _git(["--git-dir", gate, "cat-file", "blob", "%s:tools/gates/role_paths.py" % m.decode().strip()])
    else:
        rc, src = _git(["-C", main, "cat-file", "blob", "HEAD:tools/gates/role_paths.py"])
    if rc != 0:
        raise RuntimeError("게이트 코드 role_paths.py를 읽지 못함")
    boot = types.ModuleType("role_paths")
    boot.__file__ = "<gate role_paths>"
    sys.modules["role_paths"] = boot
    exec(compile(src.decode("utf-8"), "<gate role_paths>", "exec"), boot.__dict__)
    env = boot.load_env(cwd)
    cache = boot.ensure_cache(env)
    del sys.modules["role_paths"]
    return cache, env


def _main():
    import json
    import os
    sys.dont_write_bytecode = True   # 캐시에 .pyc를 만들지 않는다(role_paths.dir_matches)
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    agent = payload.get("agent_type") or ""
    tool = payload.get("tool_name") or ""
    if EVENT == "PreToolUse" and tool in ("Read", "Grep", "Glob") and agent != "gmid-test-author":
        return 0   # §6.1-4: Read·Grep·Glob은 §6.4(test-author)에만
    if EVENT in ("PostToolUse", "SubagentStop") and not agent.startswith("gmid-"):
        return 0   # §7: EL2는 gmid-* 역할에만
    cwd = payload.get("cwd") or os.getcwd()
    cache, env = _load_gate_code(cwd)
    sys.path.insert(0, cache)
    import role_hooks
    code, msg = role_hooks.run(EVENT, payload, cache, env)   # 판정 환경을 다시 읽지 않는다(WP-10: git 호출 7회 절약)
    if msg:
        (sys.stderr if code else sys.stdout).write(msg + "\n")
    return code


if __name__ == "__main__":
    try:   # 로캘·PYTHONIOENCODING과 무관하게 출력을 UTF-8로(spec card 20260921-gate-output-utf8). 판정 전이라 캐시 밖에서, 자기 안에서 한다(§4.4)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        rc = _main()
    except BaseException as e:   # fail-closed: 게이트 코드 import 실패·git 실패·무결성 실패 모두 거부
        try:
            sys.stderr.write("[역할 게이트 %s 거부] 판정 실패(fail-closed): %s: %s\n" % (EVENT, type(e).__name__, e))
        except BaseException:
            pass
        rc = 2
    sys.exit(2 if rc else 0)
