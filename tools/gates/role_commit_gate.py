"""EL3 커밋 판정 (05-role-separation design §8.2).

    role_commit_gate.py pre-commit            # 역할과 무관한 부분(casefold 충돌, 소스+test 동시 변경)
    role_commit_gate.py commit-msg <파일>      # 트레일러·경로 권한·조건(§8.2-2·4·5), 병합 판정(§8.2-3)

`.githooks/*`(부트스트랩 ④(a)에서 `tools/gates/githooks/`를 사용자가 복사)가 gate master 판 캐시의 이 파일을
부른다. 0 통과 / 1 차단(§17). 판정 불가(예외)도 차단.

DESIGN-GAP: §8.1은 pre-commit이 §8.2-4 경로 검사를 한다고 적었지만, 경로 권한의 주체는 트레일러(커밋 메시지)에서
나오고 메시지는 commit-msg 시점에만 있다. pre-commit은 역할과 무관한 판정만 하고, 경로 권한 전체는 commit-msg가
한다(`git commit`은 두 hook을 모두 돌리고 `merge`는 pre-merge-commit·commit-msg를 돌린다 -- review28 E1·review30 H1).
"""
from __future__ import annotations

import os
import sys

import merge_gate as mg
import role_paths as rp

GateError = rp.GateError


def _root():
    return rp.norm_abs(rp.git_text(["rev-parse", "--show-toplevel"], clean=False))


def _merge_heads(root):
    p = rp.git_text(["-C", root, "rev-parse", "--git-path", "MERGE_HEAD"], clean=False)
    p = rp.norm_abs(p, root)
    if not os.path.isfile(p):
        return []
    with open(p, "r", encoding="utf-8") as fh:
        return [l.strip() for l in fh if l.strip()]


def _staged_changes(root):
    out = rp.git(["-C", root, "diff", "--cached", "--name-status", "-z", "--no-renames", "HEAD"], clean=False)
    toks = [t for t in out.decode("utf-8").split("\0") if t]
    return [(toks[i], toks[i + 1]) for i in range(0, len(toks) - 1, 2)]


def _base_view(env):
    if env.source == "gate":
        return mg.TreeView(env.gate_args(), env.gate_master)
    return mg.TreeView(["-C", env.main_root], "HEAD")


def pre_commit(env, root):
    if _merge_heads(root):
        return []   # §8.1 ③: MERGE_HEAD가 있으면 경로 검사를 하지 않는다(병합 판정은 commit-msg)
    changes = _staged_changes(root)
    fails = []
    added = [p for s, p in changes if s.startswith("A")]
    if added:
        coll = mg.casefold_collisions(added, mg.TreeView(["-C", root], ":").list())
        if coll:
            fails.append("casefold 충돌 경로 추가: %s -- 주체 %s, 판정 행 §4.1 casefold 충돌" % (", ".join(coll), _PRE_ACTOR))
    paths = [p for _, p in changes]
    if any(rp.overlaps_any(p, env.rules) for p in paths):
        fails += mg.source_test_violation(paths, _PRE_ACTOR)
    return fails


# pre-commit 시점에는 커밋 메시지(트레일러)가 없어 주체를 모른다(모듈 머리 DESIGN-GAP)
_PRE_ACTOR = "미정(pre-commit: 트레일러는 commit-msg에서 읽는다)"


def _rev(root, r):
    rc, out = rp.git_try(["-C", root, "rev-parse", "--verify", "--quiet", r + "^{commit}"])
    return out.decode().strip() if rc == 0 else None


def judge_merge(env, root, trailers, heads):
    fails = _judge_merge(env, root, trailers, heads)
    if not fails:
        return fails
    # §8.2-6 차단 메시지: 위반 경로·주체·판정 행
    roles = mg.trailer_values(trailers, "Role")
    actor = rp.ACTOR_OF_TRAILER.get(roles[0], "?") if len(roles) == 1 else "미정(Role 트레일러 %r)" % roles
    staged = [p for _, p in _staged_changes(root)]
    ctx = " -- 주체 %s, 판정 행 §8.2-3, 병합이 들이는 경로: %s" % (actor, ", ".join(staged[:20]) or "(없음)")
    return [f + ctx for f in fails]


def _judge_merge(env, root, trailers, heads):
    fails = []
    br = rp.git_try(["-C", root, "symbolic-ref", "--short", "-q", "HEAD"])
    branch = br[1].decode().strip() if br[0] == 0 else None
    ri = rp.role_of_branch(branch)
    head = _rev(root, "HEAD")
    if ri is not None and ri[0] == "audit":
        cid = ri[1]
        role, tcid, tf = mg.judge_trailers(trailers, merge=True)
        fails += tf
        if role != "doc" or tcid != cid:
            fails.append("(가) 변경 한 건의 병합 트레일러는 `Role: doc`·`Change-Id: %s`" % cid)
        if head != _rev(root, "refs/heads/role/test/%s" % cid):
            fails.append("(나) HEAD가 role/test/%s 끝이 아니다" % cid)
        if len(heads) != 1 or heads[0] != _rev(root, "refs/heads/role/code/%s" % cid):
            fails.append("(나) MERGE_HEAD가 role/code/%s 끝 하나가 아니다" % cid)
        elif rp.git_try(["-C", root, "diff", "--cached", "--quiet", heads[0]], clean=False)[0] != 0:
            fails.append("(다) staged 트리가 MERGE_HEAD(code 끝) 트리와 다르다(병합이 다른 내용을 들인다)")
        return fails
    # (라) 역할 밖 병합
    if len(heads) != 1:
        fails.append("(라) 부모가 정확히 둘이 아닌 병합(부모 %d)" % (len(heads) + 1))
    gm = _rev(root, "refs/remotes/gate/master")
    if gm is None:
        # DESIGN-GAP: §8.2-3 (라)는 gate/master가 없는 상태(부트스트랩 ④(b) 전)를 정하지 않았다. 판정할 수 없으므로 차단한다.
        fails.append("(라) gate/master가 없어 첫 부모 조건을 판정하지 못함")
    elif rp.git_try(["-C", root, "merge-base", "--is-ancestor", gm, "HEAD"])[0] != 0:
        fails.append("(라) HEAD가 gate/master와 같거나 그 후손이 아니다(review32 M-01)")
    diff = [p for _, p in _staged_changes(root) if rp.overlaps_any(p, env.rules)]
    if diff:
        fails.append("(라) 역할 경로에서 staged 트리가 HEAD와 다르다: %s" % ", ".join(diff[:8]))
    return fails


def commit_msg(env, root, msg_file):
    with open(msg_file, "rb") as fh:
        message = fh.read().decode("utf-8", "replace")
    trailers = mg.parse_trailers(message, ["-C", root])
    heads = _merge_heads(root)
    if heads:
        return judge_merge(env, root, trailers, heads)
    return mg.judge_commit_change(parent_view=mg.TreeView(["-C", root], "HEAD"),
                                  child_view=mg.TreeView(["-C", root], ":"),
                                  changes=_staged_changes(root), trailers=trailers, base_view=_base_view(env),
                                  rules=env.rules, bootstrapped=env.bootstrapped, layer="EL3")


def main(argv):
    if not argv or argv[0] not in ("pre-commit", "commit-msg"):
        print("사용법: role_commit_gate.py pre-commit | commit-msg <파일>", file=sys.stderr)
        return 1
    try:
        root = _root()
        env = rp.load_env(root)
        for w in env.warnings:
            print("[EL3 경고] " + w, file=sys.stderr)
        if argv[0] == "pre-commit":
            fails = pre_commit(env, root)
        else:
            if len(argv) != 2:
                print("commit-msg <파일>", file=sys.stderr)
                return 1
            fails = commit_msg(env, root, argv[1])
    except (GateError, OSError, UnicodeDecodeError) as e:
        print("[EL3 차단] 판정 불가: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 1
    for f in fails:
        print("[EL3 차단] " + f, file=sys.stderr)
    return 1 if fails else 0


if __name__ == "__main__":
    try:   # 로캘·PYTHONIOENCODING과 무관하게 출력을 UTF-8로(spec card 20260921-gate-output-utf8)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
