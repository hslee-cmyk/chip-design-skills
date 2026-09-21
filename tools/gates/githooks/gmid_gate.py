"""EL3 git client hook 실행기 (05-role-separation design §8.1).

부트스트랩 ④(a)에서 사용자가 이 디렉터리(`tools/gates/githooks/`)의 파일을 작업 저장소 `.githooks/`로 복사한다
(`.githooks/**`는 사용자 경로). `core.hooksPath` = `.githooks`의 절대 경로라 모든 worktree가 같은 파일을 쓴다.

    gmid_gate.py pre-commit          # ② 무결성 대조(--scope commit) ③ role_commit_gate pre-commit
    gmid_gate.py commit-msg <파일>   # role_commit_gate commit-msg (병합 판정 포함)
    gmid_gate.py pre-merge-commit    # 무결성 대조만(병합 대상은 GITHEAD_<sha>로만 보인다, review30 H1)

게이트 코드는 gate master 판(§4.4 캐시)을 쓴다. 부트스트랩 완료 표지 전(gate 없음)에는 작업 저장소 HEAD 판으로
돌고 경고를 출력한다(§8.1). 0 통과 / 1 차단. 예외도 차단(fail-closed).
"""
import sys


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
    import json
    import types
    rc, out = _git(["-C", cwd, "worktree", "list", "--porcelain"])
    if rc != 0:
        raise RuntimeError("저장소를 찾지 못함: %s" % cwd)
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
    return cache, env.main_root


def _main(argv):
    import os
    sys.dont_write_bytecode = True
    mode = argv[0] if argv else ""
    if mode not in ("pre-commit", "commit-msg", "pre-merge-commit"):
        print("[EL3] 모르는 모드: %r" % mode, file=sys.stderr)
        return 1
    cache, main_root = _load_gate_code(os.getcwd())
    sys.path.insert(0, cache)
    import integrity
    import role_commit_gate
    if mode in ("pre-commit", "pre-merge-commit"):
        results, ok = integrity.check("commit", main_root)
        if not ok:
            import json
            for r in results:
                if not r["ok"]:
                    print(json.dumps(r, ensure_ascii=False), file=sys.stderr)
            print("[EL3 차단] " + integrity.RECOVERY, file=sys.stderr)
            return 1
        if mode == "pre-merge-commit":
            return 0
        return role_commit_gate.main(["pre-commit"])
    return role_commit_gate.main(["commit-msg"] + argv[1:2])


if __name__ == "__main__":
    try:   # 로캘·PYTHONIOENCODING과 무관하게 출력을 UTF-8로(spec card 20260921-gate-output-utf8)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        rc = _main(sys.argv[1:])
    except BaseException as e:   # fail-closed
        try:
            sys.stderr.write("[EL3 차단] 판정 실패(fail-closed): %s: %s\n" % (type(e).__name__, e))
        except BaseException:
            pass
        rc = 1
    sys.exit(1 if rc else 0)
