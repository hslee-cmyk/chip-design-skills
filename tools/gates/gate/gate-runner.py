"""gmid gate 실행기 (05-role-separation design §9.1). 원본: 작업 저장소 tools/gates/gate/gate-runner.py.
부트스트랩 ④(b)에서 사용자가 <gate_path>/gate-runner.py로 복사한다.

1. 무결성 대조(§3.3의 gate 항목) -- `old` 판 게이트 코드의 `integrity.py check --scope gate`
2. stdin `<old> <new> <ref>` 줄마다: `refs/heads/master`만, 삭제·생성·non-ff 거부
3. `old` 판 게이트 코드를 `git ls-tree` + `git cat-file`로 임시 디렉터리에 풀고(`git archive`는 export-ignore를
   따르므로 쓰지 않는다, review29 A1) `merge_gate.py receive --old --new` 실행. push된 트리는 데이터로만 읽는다.
4. 통과하면 `gmid-accept-log`에 `<old> <new> <시각>` 한 줄을 쓰고 exit 0.

실행 전체를 try/except → exit 1(fail-closed). 모든 git 호출에 GIT_NO_REPLACE_OBJECTS=1.
"""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ZERO = "0" * 40
PREFIX = "tools/gates/"
EXCLUDE = ("tools/gates/redteam/",)


def git(gate, args, check=True):
    env = dict(os.environ)
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    p = subprocess.run(["git", "--git-dir", gate] + args, capture_output=True, env=env)
    if check and p.returncode != 0:
        raise RuntimeError("git %s 실패: %s" % (" ".join(args[:3]), p.stderr.decode("utf-8", "replace").strip()[:300]))
    return p


def extract(gate, commit, dest):
    out = git(gate, ["ls-tree", "-r", "-z", "--full-tree", commit, "--", PREFIX]).stdout.decode("utf-8")
    n = 0
    for ent in out.split("\0"):
        if not ent:
            continue
        meta, path = ent.split("\t", 1)
        mode, typ, oid = meta.split()
        if typ != "blob" or any(path.startswith(e) for e in EXCLUDE):
            continue
        if mode == "120000":
            raise RuntimeError("게이트 코드에 심볼릭 링크: %s" % path)
        data = git(gate, ["cat-file", "blob", oid]).stdout
        if hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() != oid:
            raise RuntimeError("blob 내용이 id와 다르다: %s" % path)
        p = os.path.join(dest, *path[len(PREFIX):].split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(data)
        n += 1
    if n == 0:
        raise RuntimeError("old 판 게이트 코드가 없다")


def run():
    gate = os.path.abspath(os.environ.get("GIT_DIR") or ".")
    lines = [l.split() for l in sys.stdin.read().splitlines() if l.strip()]
    if not lines:
        return 0
    for parts in lines:
        if len(parts) != 3:
            print("[gate 거부] 입력 줄 형식 위반: %r" % parts, file=sys.stderr)
            return 1
        old, new, ref = parts
        if ref != "refs/heads/master":
            print("[gate 거부] refs/heads/master만 받는다: %s" % ref, file=sys.stderr)
            return 1
        if new == ZERO:
            print("[gate 거부] master 삭제", file=sys.stderr)
            return 1
        if old == ZERO:
            print("[gate 거부] 최초 push는 pre-receive 설치 전에 한다(§9.1 기준 커밋)", file=sys.stderr)
            return 1
        if git(gate, ["merge-base", "--is-ancestor", old, new], check=False).returncode != 0:
            print("[gate 거부] non-fast-forward", file=sys.stderr)
            return 1
    accepted = []
    for old, new, ref in lines:
        tmp = tempfile.mkdtemp(prefix="gmid-gate-")
        try:
            extract(gate, old, tmp)
            cfg = json.loads(git(gate, ["cat-file", "blob", "%s:tools/gates/gate_config.json" % old]).stdout.decode("utf-8"))
            ws = cfg.get("workspace_path")
            if not isinstance(ws, str) or not ws:
                print("[gate 거부] old gate_config.json에 workspace_path가 없다", file=sys.stderr)
                return 1
            py = sys.executable
            env = dict(os.environ)
            env["GIT_NO_REPLACE_OBJECTS"] = "1"
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            ic = subprocess.run([py, os.path.join(tmp, "integrity.py"), "check", "--scope", "gate",
                                 "--workspace", ws, "--gate", gate], capture_output=True, env=env, cwd=tmp)
            if ic.returncode != 0:
                sys.stderr.write(ic.stdout.decode("utf-8", "replace"))
                sys.stderr.write(ic.stderr.decode("utf-8", "replace"))
                print("[gate 거부] 무결성 대조 실패(exit %d)" % ic.returncode, file=sys.stderr)
                return 1
            mg = subprocess.run([py, os.path.join(tmp, "merge_gate.py"), "receive", "--old", old, "--new", new,
                                 "--git-dir", gate], capture_output=True, env=env, cwd=tmp)
            sys.stderr.write(mg.stderr.decode("utf-8", "replace"))
            if mg.returncode != 0:
                print("[gate 거부] merge_gate receive exit %d" % mg.returncode, file=sys.stderr)
                return 1
            accepted.append((old, new))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    with open(os.path.join(gate, "gmid-accept-log"), "a", encoding="utf-8") as fh:
        for old, new in accepted:
            fh.write("%s %s %s\n" % (old, new, datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
    return 0


def main():
    try:
        return run()
    except BaseException as e:   # fail-closed(§9.1): 어떤 예외도 거부
        print("[gate 거부] 실행기 예외: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    # 로캘·PYTHONIOENCODING과 무관하게 출력을 UTF-8로(spec card 20260921-gate-output-utf8).
    # Python 3.14는 항상 reconfigure를 제공한다(V6, spec card 20260921-gate-flow-liveness 계약 6).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
