"""redteam 단계 실행기. setup.sh·run.sh가 부른다.

환경(run_all.py가 준다): WORK(케이스 임시 루트), CASE_DIR, RT_REPO(시험 대상 저장소 루트), RT_MODE.
단계 기록은 $WORK/steps.jsonl에 한 줄씩 append한다(중간에 죽어도 앞 단계가 남는다).
종료 코드: 0 정상(판정 결과와 무관), 97 게이트 코드 없음(setup에서), 1 하네스 오류.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import time
import types
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import iface  # noqa: E402
import sb  # noqa: E402
from sb import Missing, State, git, gout, posix, win, write  # noqa: E402

WORK = Path(os.environ.get("WORK") or ".").resolve()
CASE_DIR = Path(os.environ.get("CASE_DIR") or ".").resolve()
EXIT_MISSING = 97
TRUNC = 6000


# ----------------------------------------------------------------------------------------------------------
def st() -> State:
    return State(WORK)


def subst_str(s: str, S: State) -> str:
    """`@{KEY}` -> 상태 변수(슬래시 표기), `@{KEY:win}` -> 역슬래시 표기, `@win(...)` -> 괄호 안 전체를 역슬래시 표기로."""
    def rep(m):
        key, _, form = m.group(1).partition(":")
        if key not in S.vars:
            raise RuntimeError(f"치환 변수 없음: {key}")
        v = str(S.vars[key])
        return win(v) if form == "win" else v
    s = re.sub(r"@\{([^}]+)\}", rep, s)
    return re.sub(r"@win\(([^)]*)\)", lambda m: m.group(1).replace("/", "\\"), s)


def subst(obj, S: State):
    if isinstance(obj, str):
        return subst_str(obj, S)
    if isinstance(obj, list):
        return [subst(x, S) for x in obj]
    if isinstance(obj, dict):
        return {k: subst(v, S) for k, v in obj.items()}
    return obj


def record(name: str, *, kind: str, layer: str, status: str, exit_code=None, stdout="", stderr="", cmd=None,
           note="", missing=None, expect=None, observed=None, extra=None):
    line = {"step": name, "kind": kind, "layer": layer, "status": status, "exit": exit_code,
            "stdout": (stdout or "")[-TRUNC:], "stderr": (stderr or "")[-TRUNC:], "cmd": cmd, "note": note,
            "missing": missing or [], "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if expect is not None:
        line["expect"] = expect
    if observed is not None:
        line["observed"] = observed
    if extra:
        line.update(extra)
    with (WORK / "steps.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def dec(b: bytes) -> str:
    return b.decode("utf-8", "replace") if isinstance(b, (bytes, bytearray)) else (b or "")


def run_gate(name, kind, layer, cmd, cwd, *, env=None, stdin=None, expect=None, note="", extra=None):
    try:
        r = sb.run_py(cmd, cwd, env=env, stdin=stdin)
    except subprocess.TimeoutExpired as e:
        record(name, kind=kind, layer=layer, status="ran", exit_code="timeout", cmd=_cmdstr(cmd), note=f"timeout {e}",
               expect=expect)
        return None
    record(name, kind=kind, layer=layer, status="ran", exit_code=r.returncode, stdout=dec(r.stdout),
           stderr=dec(r.stderr), cmd=_cmdstr(cmd), note=note, expect=expect, extra=extra)
    return r


def _cmdstr(cmd):
    return " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)


def need(name, kind, layer, *keys, expect=None) -> bool:
    try:
        sb.require(*keys)
        return True
    except Missing as e:
        record(name, kind=kind, layer=layer, status="missing", missing=e.paths, note="게이트 코드 없음", expect=expect)
        return False


# ----------------------------------------------------------------------------------------------------------
# 준비 동작(판정 아님). 실패는 하네스 오류(1) 또는 게이트 코드 없음(97)
# ----------------------------------------------------------------------------------------------------------
def a_sandbox(ns):
    S = st()
    extra = {}
    for e in ns.extra_spec or []:
        cid, et, phase = e.split("|")
        extra[cid] = (et, phase)
    sb.make_sandbox(S, extra_specs=extra)


def a_flow(ns):
    S = st()
    kw = dict(also_test=ns.also_test, extra_role_test=ns.extra_role_test, code_role=ns.code_role,
              code_change_id=ns.code_change_id, test_role=ns.test_role)
    if ns.code_extra_file:
        kw["code_extra_files"] = {subst_str(k, S): v for k, v in (x.split("=", 1) for x in ns.code_extra_file)}
    cid, et = sb.flow_full(S, ns.key, cid=ns.cid, evidence_type=ns.et, base=subst_str(ns.base, S),
                           audit=not ns.no_audit, **kw)
    S["LAST_CID"] = cid


def a_flow_step(ns):
    S = st()
    cid = ns.cid
    if ns.stage == "start":
        sb.flow_start(S, cid, subst_str(ns.base, S))
    elif ns.stage == "test":
        sb.flow_test(S, cid, role=ns.role or "test", change_id=ns.change_id)
    elif ns.stage == "code":
        sb.flow_code(S, cid, role=ns.role or "code", change_id=ns.change_id, equivalence=ns.equivalence)
    elif ns.stage == "worktrees":
        sb.ensure_audit_code(S, cid)
    elif ns.stage == "audit-wt":
        git(S["WORK"], "worktree", "add", "-q", posix(sb.wt(S, cid, "audit")), "-b", f"role/audit/{cid}",
            f"role/test/{cid}")
    elif ns.stage == "merge":
        sb.flow_merge(S, cid, no_commit=ns.no_commit)
    elif ns.stage == "audit":
        sb.flow_audit(S, cid, ns.et)


def a_git(ns):
    S = st()
    cwd = subst_str(ns.cwd, S)
    args = [subst_str(a, S) for a in ns.args]
    r = git(cwd, *args, check=not ns.allow_fail)
    if ns.save:
        S[ns.save] = dec(r.stdout).strip()


def a_write(ns):
    S = st()
    path = subst_str(ns.path, S)
    if ns.jtext is not None:
        content = subst_str(json.loads(ns.jtext), S)
    elif ns.from_repo is not None:
        content = sb.repo_read("show", ns.from_repo).decode("utf-8")
    else:
        content = subst_str(ns.text or "", S)
    if ns.append and Path(path).exists():
        content = Path(path).read_text(encoding="utf-8") + content
    write(path, content)


def a_set(ns):
    S = st()
    S[ns.key] = subst_str(ns.value, S)


def a_replace(ns):
    S = st()
    path = Path(subst_str(ns.path, S))
    sb._assert_temp(path)
    text = path.read_text(encoding="utf-8")
    old, new = subst_str(json.loads(ns.old), S), subst_str(json.loads(ns.new), S)
    if text.count(old) != 1:
        raise RuntimeError(f"replace 대상이 정확히 하나가 아니다({text.count(old)}): {old[:80]!r}")
    path.write_bytes(text.replace(old, new).encode("utf-8"))


def a_advance(ns):
    S = st()
    sb.advance_gate_master(S, subst_str(ns.rev, S))


def a_mkcommit(ns):
    """hook을 거치지 않는 커밋(commit-tree): parent 트리(또는 --tree-from 트리)에 파일을 더하거나 지운다."""
    S = st()
    work = S["WORK"]
    parents = [gout(work, "rev-parse", subst_str(p, S)) for p in ns.parent]
    idx = Path(S["SB"]) / f"idx-{time.time_ns()}"
    env = {"GIT_INDEX_FILE": str(idx)}
    git(work, "read-tree", subst_str(ns.tree_from, S) if ns.tree_from else parents[0], env=env)
    for spec in ns.file or []:
        p, _, jt = spec.partition("=")
        p = subst_str(p, S)
        if jt == "@delete":
            git(work, "update-index", "--force-remove", p, env=env)
            continue
        h = git(work, "hash-object", "-w", "--stdin", input_bytes=subst_str(json.loads(jt), S).encode("utf-8")
                ).stdout.decode().strip()
        git(work, "update-index", "--add", "--cacheinfo", f"100644,{h},{p}", env=env)
    tree = git(work, "write-tree", env=env).stdout.decode().strip()
    idx.unlink(missing_ok=True)
    args = ["commit-tree", tree]
    for p in parents:
        args += ["-p", p]
    c = git(work, *args, input_bytes=subst_str(json.loads(ns.msg), S).encode("utf-8")).stdout.decode().strip()
    S[ns.save] = c


def a_plan_approval(ns):
    """판정 표 승인 기록(target_kind: plan_tables) -- target은 §15.2 CLI로 계산(대조군 16 (iv))."""
    S = st()
    sb.require("EL4")
    plan = subst_str(ns.plan, S)
    r = sb.run_py(iface.plan_tables_hash_command(iface.PY, str(Path(S["WORK"]) / iface.GATE_FILES["EL4"]), plan),
                  Path(plan).parent)
    h = dec(r.stdout).strip().splitlines()[-1].strip() if r.returncode == 0 and r.stdout.strip() else ""
    if len(h) != 64:
        raise RuntimeError(f"plan-tables-hash 실패: {dec(r.stdout)[:300]} {dec(r.stderr)[:300]}")
    write(subst_str(ns.out, S), sb.approval_text([("id", ns.id), ("date", "2026-09-21"), ("target_kind", "plan_tables"),
                                                  ("target", h), ("scope", "redteam 판정 표 개정 승인")]), binary=True)


def a_trailerless(ns):
    """트레일러 없는 커밋 하나(`git add -f`)를 gate master에서 가지를 내 만들고 EL3·EL4로 판정한다.
    단계 이름: <step>::EL3, <step>::EL4 (공격 10b·17)."""
    S = st()
    n = S.get("TL", 0) + 1
    S["TL"] = n
    d = Path(S["SB"]) / f"tl{n}"
    base = gout(S["WORK"], "rev-parse", "gate/master")
    git(S["WORK"], "worktree", "add", "-q", posix(d), "-b", f"rt/tl{n}", base)
    path = subst_str(ns.path, S)
    content = subst_str(json.loads(ns.jtext), S).encode("utf-8") if ns.jtext is not None else b"x\n"
    if ns.index_only:
        h = git(d, "hash-object", "-w", "--stdin", input_bytes=content).stdout.decode().strip()
        git(d, "update-index", "--add", "--cacheinfo", f"100644,{h},{path}")
    else:
        write(d / path, content, binary=True)
        git(d, "add", "-f", "--", path)
    msg = subst_str(ns.msg, S).replace("\\n", "\n") if ns.msg else f"trailerless {ns.step}"
    a_el3(argparse.Namespace(step=f"{ns.step}::EL3", kind=ns.kind, layer="EL3", cwd=posix(d), msg=msg))
    mf = WORK / f"tlmsg-{n}.txt"
    mf.write_text(msg + "\n", encoding="utf-8")
    git(d, "commit", "-q", "-F", str(mf))
    new = gout(d, "rev-parse", "HEAD")
    a_el4(argparse.Namespace(step=f"{ns.step}::EL4", kind=ns.kind, layer="EL4", old=base, new=new))


def a_sh(ns):
    """Bash 도구 호출의 실제 효과를 sandbox에서 낸다(EL2 재생). 판정 단계가 아니다."""
    S = st()
    cwd = subst_str(ns.cwd, S)
    sb._assert_temp(cwd)
    cmd = subst_str((CASE_DIR / ns.command_file).read_text(encoding="utf-8") if ns.command_file else ns.command, S)
    bash = os.environ.get("RT_BASH") or "bash"
    r = subprocess.run([bash, "-c", cmd], cwd=cwd, capture_output=True, env=sb.clean_env())
    if r.returncode != 0 and not ns.allow_fail:
        raise RuntimeError(f"sh 실패 {r.returncode}: {dec(r.stderr)[:500]}")


# ----------------------------------------------------------------------------------------------------------
# 판정 단계
# ----------------------------------------------------------------------------------------------------------
def a_hook(ns):
    S = st()
    key = iface.HOOK_FOR_EVENT[ns.event]
    if not need(ns.step, ns.kind, ns.layer, key):
        return
    raw = (CASE_DIR / ns.input_file).read_text(encoding="utf-8") if ns.input_file else ns.input
    tool_input = subst(json.loads(raw), S) if raw else None
    resp = subst(json.loads(ns.response), S) if ns.response else None
    agent = None if ns.agent in (None, "none") else ("" if ns.agent == "empty" else ns.agent)
    payload = iface.hook_payload(ns.event, win(S["WORK"]), tool=ns.tool, tool_input=tool_input, agent_type=agent,
                                 tool_use_id=ns.tool_use_id, tool_response=resp)
    script = Path(S["WORK"]) / iface.GATE_FILES[key]
    run_gate(ns.step, ns.kind, ns.layer, [iface.PY, str(script)], S["WORK"],
             env={"CLAUDE_PROJECT_DIR": win(S["WORK"])},
             stdin=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
             extra={"hook_input": payload})


def a_el3(ns):
    S = st()
    if not need(ns.step, ns.kind, ns.layer, "EL3"):
        return
    cwd = subst_str(ns.cwd, S)
    msg = subst_str(ns.msg, S).replace("\\n", "\n")
    mf = WORK / ("msg-" + re.sub(r"[^A-Za-z0-9_.-]", "_", ns.step) + ".txt")
    mf.write_text(msg if msg.endswith("\n") else msg + "\n", encoding="utf-8")
    script = str(Path(S["WORK"]) / iface.GATE_FILES["EL3"])
    outs, errs, code, blocked_by = [], [], 0, None
    for hook, cmd in iface.el3_commands(iface.PY, script, str(mf)):
        r = sb.run_py(cmd, cwd)
        outs.append(f"[{hook}] " + dec(r.stdout))
        errs.append(f"[{hook}] " + dec(r.stderr))
        if r.returncode != 0:
            code, blocked_by = r.returncode, hook
            break
    record(ns.step, kind=ns.kind, layer=ns.layer, status="ran", exit_code=code, stdout="\n".join(outs),
           stderr="\n".join(errs), cmd=f"role_commit_gate.py pre-commit; commit-msg <msg> (cwd={cwd})",
           note=f"blocked_by={blocked_by}", extra={"message": msg})


def a_el4(ns):
    S = st()
    if not need(ns.step, ns.kind, ns.layer, "EL4"):
        return
    old = gout(S["WORK"], "rev-parse", subst_str(ns.old, S))
    new = gout(S["WORK"], "rev-parse", subst_str(ns.new, S))
    sb.push_side(S, new)
    script = str(Path(S["WORK"]) / iface.GATE_FILES["EL4"])
    run_gate(ns.step, ns.kind, ns.layer, iface.el4_command(iface.PY, script, old, new), S["GATE"],
             env={"GIT_DIR": win(S["GATE"])}, note=f"old={old} new={new}")


def a_tamper_cache(ns):
    """공격 10c: 게이트 코드 캐시(§4.4 `<git-common-dir>/gmid-gate-cache/<gate master id>/`)의 .py 앞에
    `import os; os._exit(0)`을 넣는다. 캐시 대조 없이 실행되면 거부 케이스가 exit 0이 된다."""
    S = st()
    cache = Path(S["CACHE"])
    files = sorted(cache.rglob("*.py")) if cache.is_dir() else []
    if not files:
        record(ns.step, kind="precondition", layer="EL1", status="ran", exit_code=1,
               note=f"캐시 디렉터리 또는 .py가 없다: {posix(cache)} (§4.4는 모든 겹이 이 캐시를 쓴다고 적는다)")
        return
    for f in files:
        f.write_bytes(b"import os; os._exit(0)\n" + f.read_bytes())
    record(ns.step, kind="precondition", layer="EL1", status="ran", exit_code=0,
           note=f"훼손한 파일 {len(files)}개: " + ", ".join(p.name for p in files[:20]))


# ----------------------------------------------------------------------------------------------------------
# 공격 15: 판정 기록·승인 기록
# ----------------------------------------------------------------------------------------------------------
def _approval_from_case(S: State, spec: dict, *, head_blobs=None, base_rev=None) -> bytes:
    if "text" in spec:
        data = subst_str(spec["text"], S).encode("utf-8")
    else:
        header = []
        for k, v in spec["header"]:
            if v == "@auto_target":
                v = sb.diff_hash(S["WORK"], base_rev, head_blobs or {}, spec["paths_for_hash"])
            elif v == "@base":
                v = base_rev
            header.append((k, subst_str(v, S) if isinstance(v, str) else v))
        data = sb.approval_text(header, eol=spec.get("eol", "\n"))
    if spec.get("eol") == "\r\n" and "text" in spec:
        data = data.replace(b"\n", b"\r\n")
    return bytes.fromhex(spec.get("prefix_hex", "")) + data


def a_records(ns):
    S = st()
    cases = sorted(Path(ns.cases).glob("*.json"))
    if not cases:
        raise RuntimeError("케이스 없음")
    shared: dict[str, tuple[str, str]] = {}
    n = 0
    for cf in cases:
        c = json.loads(cf.read_text(encoding="utf-8"))
        name = cf.stem
        exp = {"exit": 0 if c["expect"] == "accept" else 1, "message_contains": c.get("message_contains", []),
               "basis": c.get("basis", ""), "contested": c.get("contested", False)}
        layers = c.get("layers", ["EL4"])
        try:
            if c.get("type", "record") == "commit":
                _commit_case(S, name, c, exp, layers)
                continue
            if not need(name, "attack" if c["expect"] == "reject" else "control", "EL4", "EL4", expect=exp):
                continue
            key = c.get("flow", "rg")
            et = sb.FLOW_IDS[key][1] if key in sb.FLOW_IDS else c["evidence_type"]
            if c.get("fresh") or c.get("old_files") or c.get("id"):
                n += 1
                cid = c.get("id") or f"20260921-rt-f{n}"
                et = c.get("evidence_type", et)
                # old: 오케스트레이터 문서 커밋(spec card와 old_files)을 gate master로 -- 준비 단계
                work = S["WORK"]
                files = {f"{sb.SPEC_DIR}/{cid}.spec.md": sb.spec_card(cid, c.get("spec_phase", "1"), c.get("spec_evidence_type", et))}
                for p, spec in (c.get("old_files") or {}).items():
                    files[p] = _approval_from_case(S, spec) if isinstance(spec, dict) else spec.encode("utf-8")
                for p, data in files.items():
                    write(Path(work) / p, data if isinstance(data, bytes) else data.encode("utf-8"), binary=True)
                git(work, "add", "-A")
                sb.commit(work, f"old for {name}", "doc")
                sb.advance_gate_master(S, "HEAD")
                sb.flow_full(S, key, cid=cid, evidence_type=et, audit=False)
            else:
                if key not in shared:
                    cid0 = sb.FLOW_IDS[key][0]
                    if f"{cid0}.OLD" not in S.vars:
                        # 공유 흐름의 old는 B0(gate master가 다른 케이스 준비로 움직여도 --old로 고정)
                        sb.flow_full(S, key, base=S["B0"], audit=False)
                    shared[key] = (cid0, et)
                cid = shared[key][0]
            parent = S[f"{cid}.M"] if et != "test-only" else S[f"{cid}.T"]
            rec = sb.valid_record(S, cid, et)
            subf = lambda v: subst(_flowvars(v, S, cid), S)  # noqa: E731
            data = sb.render_record(S, rec, c.get("ops", []), subf)
            new = sb.audit_commit_plumbing(S, cid, parent, data, rec_name=c.get("record_name"))
            S["CUR_NEW"] = new
            old = S[f"{cid}.OLD"]
            sb.push_side(S, new)
            script = str(Path(S["WORK"]) / iface.GATE_FILES["EL4"])
            run_gate(name, "attack" if c["expect"] == "reject" else "control", "EL4",
                     iface.el4_command(iface.PY, script, old, new), S["GATE"], env={"GIT_DIR": win(S["GATE"])},
                     expect=exp, note=f"{c.get('rule', '')} | old={old} new={new}",
                     extra={"record_head": data[:400].decode("utf-8", "replace")})
        except Missing as e:
            record(name, kind="attack", layer="EL4", status="missing", missing=e.paths, expect=exp)
        except Exception as e:  # 하네스 오류는 그 케이스만 ERROR로 남기고 계속
            record(name, kind="attack", layer="EL4", status="error", note=f"{type(e).__name__}: {e}", expect=exp)


def _flowvars(v, S: State, cid: str):
    if isinstance(v, str):
        for k in ("OLD", "T", "K", "M"):
            v = v.replace("@{F." + k + "}", str(S.get(f"{cid}.{k}", "")))
        return v.replace("@{F.ID}", cid)
    if isinstance(v, list):
        return [_flowvars(x, S, cid) for x in v]
    if isinstance(v, dict):
        return {k: _flowvars(x, S, cid) for k, x in v.items()}
    return v


def _commit_case(S: State, name: str, c: dict, exp: dict, layers: list[str]):
    """커밋형 케이스(staged_diff 승인 기록 등): gate master에서 가지를 내 파일과 승인 기록을 staged하고
    EL3(role_commit_gate)와 EL4(merge_gate receive)를 판정한다."""
    work = Path(S["WORK"])
    n = S.get("CN", 0) + 1
    S["CN"] = n
    d = Path(S["SB"]) / f"c{n}"
    base = gout(work, "rev-parse", "gate/master")
    git(work, "worktree", "add", "-q", posix(d), "-b", f"rt15/c{n}", base)
    head_blobs = {}
    for p, content in c["files"].items():
        data = subst_str(content, S).encode("utf-8")
        write(d / p, data, binary=True)
        head_blobs[p] = sb.blob_of(d, data)
    if c.get("approval"):
        ap = c["approval"]
        write(d / f".ai/approvals/{ap['id']}.md", _approval_from_case(S, ap, head_blobs=head_blobs, base_rev=base),
              binary=True)
    git(d, "add", "-A")
    kind = "attack" if c["expect"] == "reject" else "control"
    msg = f"{name}\n\n" + "".join(f"{t}\n" for t in c.get("trailers", []))
    if "EL3" in layers:
        if need(name + "::EL3", kind, "EL3", "EL3", expect=exp):
            ns = argparse.Namespace(step=name + "::EL3", kind=kind, layer="EL3", cwd=posix(d), msg=msg)
            a_el3(ns)
            _patch_last_expect(exp)
    git(d, "commit", "-q", "-m", msg)
    new = gout(d, "rev-parse", "HEAD")
    if "EL4" in layers and need(name + "::EL4", kind, "EL4", "EL4", expect=exp):
        sb.push_side(S, new)
        script = str(work / iface.GATE_FILES["EL4"])
        run_gate(name + "::EL4", kind, "EL4", iface.el4_command(iface.PY, script, base, new), S["GATE"],
                 env={"GIT_DIR": win(S["GATE"])}, expect=exp, note=f"old={base} new={new}")


def _patch_last_expect(exp):
    f = WORK / "steps.jsonl"
    lines = f.read_text(encoding="utf-8").splitlines()
    last = json.loads(lines[-1])
    last["expect"] = exp
    lines[-1] = json.dumps(last, ensure_ascii=False)
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------------------------------------
# V 도구 케이스(공격 6~9·17 V5, v3_survivor, v7_unwired, 과거 사례)
# ----------------------------------------------------------------------------------------------------------
def _file_content(spec, S) -> bytes | None:
    if spec is None:
        return None
    if isinstance(spec, str):
        return subst_str(spec, S).encode("utf-8")
    if "git" in spec:
        data = sb.repo_read("show", spec["git"]).decode("utf-8")
    elif "section" in spec:
        data = section_to_test(spec["section"])
    elif "text" in spec:
        data = spec["text"]
    else:
        raise RuntimeError(f"파일 명세 모름: {spec}")
    for old, new in spec.get("replace", []):
        if old not in data:
            raise RuntimeError(f"replace 대상 없음: {old[:80]!r}")
        data = data.replace(old, new)
    return data.encode("utf-8")


def section_to_test(sec: dict) -> str:
    """§13.3 변환 규칙: 표지 줄 다음 줄부터 `print()`만 있는 줄 앞까지의 self-test 섹션 하나를 test 함수 하나로
    (본문·리터럴·print 그대로, 들여쓰기만 한 단계로)."""
    src = sb.repo_read("show", sec["git"]).decode("utf-8")
    lines = src.splitlines()
    start = next(i for i, ln in enumerate(lines) if sec["marker"] in ln) + 1
    end = next(i for i in range(start, len(lines)) if lines[i].strip() == "print()")
    body = lines[start:end]
    indent = min(len(ln) - len(ln.lstrip()) for ln in body if ln.strip())
    return f"def {sec['def']}():\n" + "\n".join(("    " + ln[indent:]) if ln.strip() else "" for ln in body) + "\n"


def build_vrepo(S: State, name: str, case: dict) -> tuple[Path, str, str, str | None]:
    root = WORK / "v" / name
    if root.exists():
        shutil.rmtree(root)
    sb.init_repo(root)
    card_rel = None
    base_files = case.get("base", {})
    for p, spec in base_files.items():
        data = _file_content(spec, S)
        if data is not None:
            write(root / p, data, binary=True)
    if case.get("subjects"):
        cid = case.get("cid", "20260921-rt-v")
        spec_rel = f"{sb.SPEC_DIR}/{cid}.spec.md"
        write(root / spec_rel, sb.spec_card(cid, contracts=case["subjects"]))
        write(root / ".gitkeep-rt", "")
    git(root, "add", "-A")
    sb.commit(root, "base", "user")
    base = gout(root, "rev-parse", "HEAD")
    if case.get("subjects"):
        sb.require("CARD")
        r = sb.run_py(iface.card_command(iface.PY, str(sb.gate_path("CARD")), spec_rel), root)
        card_rel = f"{sb.SPEC_DIR}/{cid}.interface.md"
        if r.returncode != 0 or not (root / card_rel).is_file():
            raise RuntimeError(f"interface_card.py 실패 exit {r.returncode}: {dec(r.stderr)[:600]}")
        git(root, "add", "-A")
        sb.commit(root, "interface card", "doc")
        base = gout(root, "rev-parse", "HEAD")
    for p, spec in case.get("head", {}).items():
        data = _file_content(spec, S)
        if data is None:
            git(root, "rm", "-q", p)
        else:
            write(root / p, data, binary=True)
    git(root, "add", "-A")
    sb.commit(root, "head", "user", allow_empty=True)
    head = gout(root, "rev-parse", "HEAD")
    for ap in case.get("approve_after_head", []):   # V5 승인 기록(대조군): head 뒤 문서 커밋
        paths = ap["paths"]
        blobs = {p: gout(root, "rev-parse", f"{head}:{p}") for p in paths}
        target = sb.diff_hash(root, base, blobs, paths)
        hdr = [("id", ap["id"]), ("date", "2026-09-21"), ("target_kind", "diff"), ("target", target),
               ("diff_base", base), ("diff_head", head)] + [("diff_path", p) for p in sorted(paths)] + \
              [("scope", "redteam V5 대조군")]
        write(root / f".ai/approvals/{ap['id']}.md", sb.approval_text(hdr), binary=True)
        git(root, "add", "-A")
        sb.commit(root, "approval", "doc")
        head = gout(root, "rev-parse", "HEAD")
    return root, base, head, card_rel


def a_vcase(ns):
    S = st()
    spec = json.loads((CASE_DIR / ns.file).read_text(encoding="utf-8"))
    for case in spec["cases"]:
        name = case["step"]
        tool = case["tool"]
        keys = [tool] + (["CARD"] if case.get("subjects") else [])
        exp = case.get("expect")
        if not need(name, case.get("kind", "attack"), tool, *keys, expect=exp):
            continue
        try:
            root, base, head, card = build_vrepo(S, name, case)
        except Missing as e:
            record(name, kind=case.get("kind", "attack"), layer=tool, status="missing", missing=e.paths, expect=exp)
            continue
        cmd = iface.vtool_command(iface.PY, str(sb.gate_path(tool)), posix(root), base, head, card)
        r = sb.run_py(cmd, root)
        obj = iface.first_json_line(dec(r.stdout))
        observed = None
        if case.get("observe") == "v4_first":
            stm = iface.v4_statements(obj)
            observed = stm[0][1] if stm else None
        record(name, kind=case.get("kind", "attack"), layer=tool, status="ran", exit_code=r.returncode,
               stdout=dec(r.stdout), stderr=dec(r.stderr), cmd=_cmdstr(cmd), expect=exp, observed=observed,
               note=case.get("note", ""))


# ----------------------------------------------------------------------------------------------------------
# 공격 23: V4 (2) 판정 경계 -- v4_rule_probe의 67 케이스 + 누적 회귀 코퍼스 94 + 실제 엔진 전수
# ----------------------------------------------------------------------------------------------------------
PROBE_DIR = "docs/03-analysis/gain-budget-gmid-sizing-function-audit/v4_rule_probe"


def load_probe_cases():
    """probe 파일을 복사하지 않고 고정 커밋의 blob을 읽어, probe의 judge를 기록기로 바꿔 main()을 돌린다.
    기록한 (module, test, subjects)를 v4.out.txt의 같은 순서 줄(이름·기대·known_limit)과 짝짓는다."""
    d = WORK / "v4probe"
    d.mkdir(parents=True, exist_ok=True)
    src = sb.repo_read("show", f"{sb.PINNED_PROBE_COMMIT}:{PROBE_DIR}/v4.py").decode("utf-8")
    corpus = sb.repo_read("show", f"{sb.PINNED_PROBE_COMMIT}:{PROBE_DIR}/regression_cases.json")
    (d / "regression_cases.json").write_bytes(corpus)
    mod = types.ModuleType("v4probe")
    mod.__file__ = str(d / "v4.py")
    exec(compile(src, str(d / "v4.py"), "exec"), mod.__dict__)
    calls = []

    def recorder(m, t, s, inline_test=True, inline_subject=True):
        calls.append((m, t, sorted(s)))
        return [(0, "RECORDED")]
    mod.judge = recorder
    cwd = os.getcwd()
    try:
        os.chdir(sb.HISTORY)  # e329283_inputs()가 `git show e329283:...`(읽기)를 현재 디렉터리에서 부른다
        with open(os.devnull, "w", encoding="utf-8") as dn:
            old_stdout = sys.stdout
            sys.stdout = dn
            try:
                mod.main()
            finally:
                sys.stdout = old_stdout
    finally:
        os.chdir(cwd)
    out_lines = (d / "v4.out.txt").read_text(encoding="utf-8").splitlines()
    case_lines = []
    for ln in out_lines:
        if ln.startswith("케이스 "):
            break
        case_lines.append(ln)
    cases = []
    for i, ln in enumerate(case_lines):
        m, t, s = calls[i]
        name = ln[len("MISMATCH "):] if ln.startswith("MISMATCH ") else ln
        name = name.split(": [", 1)[0]
        mexp = re.search(r"\| 기대 (.+?)(?: \| known_limit (.+))?$", ln)
        expect_word = mexp.group(1).split()[-1]
        cases.append({"name": name, "module": m, "test": t, "subjects": s, "expect": expect_word,
                      "known_limit": mexp.group(2)})
    reg = json.loads(corpus.decode("utf-8"))
    return cases, reg


def _v4_repo(name, module, test, subjects, modname="rtmod"):
    case = {"step": name, "tool": "V4", "cid": "20260921-rt-v4",
            "subjects": [f"{modname}.{s}" for s in subjects],
            "base": {f"skills/analog-gmid-design/assets/{modname}.py": {"text": module}},
            "head": {"skills/analog-gmid-design/assets/tests/test_case.py": {"text": test}}}
    return case


def a_v4probe(ns):
    S = st()
    if not need("23-inventory", "precondition", "V4", "V4", "CARD"):
        record("23-all", kind="attack", layer="V4", status="missing", missing=[iface.GATE_FILES["V4"]])
        return
    cases, reg = load_probe_cases()
    from collections import Counter
    cnt = Counter(("known_limit:" + c["expect"]) if c["known_limit"] else c["expect"] for c in cases)
    want = {"FAIL": 34, "PASS": 11, "known_limit:PASS": 7, "known_limit:UNJUDGED": 1, "UNJUDGED": 12, "NO-SUBJECT": 2}
    record("23-inventory", kind="precondition", layer="V4", status="ran", exit_code=0 if dict(cnt) == want and len(cases) == 67 and len(reg) == 94 else 1,
           note=f"probe 케이스 {len(cases)}개 {dict(cnt)} / 회귀 코퍼스 {len(reg)}개 (§13.2 23 기대: 67 = {want}, 94)")
    for i, c in enumerate(cases, 1):
        name = f"23-probe-{i:02d}"
        exp = {"observed_equals": c["expect"], "exit": [0, 1], "basis": "§10 V4 실측 표·§13.2 23 (probe 기대 열)"}
        _run_v4_case(S, name, c["module"], c["test"], c["subjects"], exp, mode="first",
                     note=c["name"] + (f" | known_limit {c['known_limit']}" if c["known_limit"] else ""))
    for i, c in enumerate(reg, 1):
        name = f"23-corpus-{i:03d}"
        exp = {"observed_equals": [list(x) for x in c["output"]], "exit": [0, 1],
               "basis": "§10 누적 회귀 코퍼스(출력 변화 0) · §13.2 23"}
        _run_v4_case(S, name, c["module"], c["test"], c["subjects"], exp, mode="all", note=f"{c['source']} {c['name']}")
    # 실제 엔진 최상위 함수 전수: 검출기 예외 0(= exit 2 없음)
    for mod in sorted((sb.REPO / "skills/analog-gmid-design/assets").glob("*.py")):
        src = mod.read_text(encoding="utf-8")
        tests, subjects = [], []
        for f in ast.parse(src).body:
            if isinstance(f, ast.FunctionDef):
                a = f.args
                names = [p.arg for p in a.posonlyargs + a.args]
                tests.append(f"def test_x_{len(tests)}():\n    assert {f.name}({', '.join(names)}) == pytest.approx(expected)\n")
                subjects.append(f.name)
        if not tests:
            continue
        name = f"23-sweep-{mod.stem}"
        exp = {"exit": [0, 1], "basis": "§13.2 23: 실제 엔진 최상위 함수 전수에서 검출기 예외 0(exit 2 = 도구 오류)"}
        _run_v4_case(S, name, src, "import pytest\n\n\n" + "\n\n".join(tests), subjects, exp, mode=None,
                     modname=mod.stem, note=f"{len(subjects)} functions")


def _run_v4_case(S, name, module, test, subjects, exp, *, mode, note="", modname="rtmod"):
    try:
        root, base, head, card = build_vrepo(S, name, _v4_repo(name, module, test, subjects, modname))
    except Exception as e:
        record(name, kind="attack", layer="V4", status="error", note=f"{type(e).__name__}: {e}", expect=exp)
        return
    cmd = iface.vtool_command(iface.PY, str(sb.gate_path("V4")), posix(root), base, head, card)
    r = sb.run_py(cmd, root)
    obj = iface.first_json_line(dec(r.stdout))
    stm = iface.v4_statements(obj)
    observed = None
    if mode == "first":
        observed = stm[0][1] if stm else None
    elif mode == "all":
        observed = [list(x) for x in stm] if stm else None
    record(name, kind="attack", layer="V4", status="ran", exit_code=r.returncode, stdout=dec(r.stdout)[-1500:],
           stderr=dec(r.stderr)[-1500:], cmd=_cmdstr(cmd), expect=exp, observed=observed, note=note)
    shutil.rmtree(root, ignore_errors=True)


# ----------------------------------------------------------------------------------------------------------
# 공격 17 보조: pytest 후보 대조, 격리 실행 로그
# ----------------------------------------------------------------------------------------------------------
def plan_judging_env_names() -> set[str]:
    """계획 N3.12.2 표에서 조건 `판정 환경` 행의 경로 glob 마지막 조각(파일 이름). 검증 agent가 따로 읽는다."""
    text = (sb.REPO / sb.PLAN_REL).read_text(encoding="utf-8")
    sec = text.split("#### N3.12.2 ", 1)[1].split("#### N3.12.3 ", 1)[0]
    names = set()
    for ln in sec.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[3] == "판정 환경":
            names.add(cells[1].strip("`").split("/")[-1].casefold())
    return names


def a_pytest_candidates(ns):
    exp = {"exit": 0, "basis": "§13.2 17 후보 대조: 고정 pytest 판의 locate_config config_names ⊆ 판정 환경 파일 이름; §9.2-10"}
    if not need(ns.step, "attack", "data", "REQUIREMENTS", expect=exp):
        return
    req = (sb.REPO / iface.GATE_FILES["REQUIREMENTS"]).read_text(encoding="utf-8")
    m = re.search(r"(?im)^\s*pytest\s*==\s*([^\s#]+)", req)
    import importlib.metadata as md
    import importlib.util
    running = md.version("pytest")
    spec = importlib.util.find_spec("_pytest.config.findpaths")
    tree = ast.parse(Path(spec.origin).read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "locate_config")
    lst = None
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "config_names" for t in n.targets):
            lst = [e.value for e in n.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    names = plan_judging_env_names()
    miss = [x for x in (lst or []) if x.casefold() not in names]
    ok = m is not None and m.group(1) == running and lst and not miss
    record(ns.step, kind="attack", layer="data", status="ran", exit_code=0 if ok else 1, expect=exp,
           note=f"requirements pytest=={m.group(1) if m else None}, 실행 판 {running}, config_names={lst}, "
                f"판정 환경 이름에 없는 것={miss}")


RED_TEST = "def test_rt_red():\n    assert 1 + 1 == 3\n"


def a_isolated_run(ns):
    """§12-7·00-common §8.1 격리 실행 명령이 복제본 밖·복제본 루트에 심은 파일을 읽지 않는지 로그로 보인다
    (공격 17의 review33·review34 '로그로' 항목)."""
    S = st()
    exp_attack = {"exit": 1, "message_not_contains": ["PLANTED", "Traceback (most recent call last)"],
                  "basis": "§12-7: -P·-c pytest_gate.ini·--rootdir·--confcutdir·PYTHONPYCACHEPREFIX로 가둔 실행은 실패 test를 실패로 낸다"}
    if not need(ns.step, "attack", "pytest", "PYTEST_INI", "EL4", expect=exp_attack):
        return
    base = WORK / "iso"
    parent = base / "parent"
    clone = parent / "clone-iso"
    cache = base / "cache"
    shutil.rmtree(base, ignore_errors=True)
    # 캐시 판 게이트 코드
    shutil.copytree(sb.REPO / "tools/gates", cache, ignore=shutil.ignore_patterns("redteam", "__pycache__", "*.pyc"))
    # 복제본 부모에 심은 설정(review34 M3-02)
    write(parent / "pytest.ini", "[pytest]\naddopts = -k nothing_matches_PLANTED\n")
    write(parent / "conftest.py", "import sys\nprint('PLANTED parent conftest')\nsys.exit(0)\n")
    # 복제본: 실패하는 test, 루트에 심은 merge_gate.py·pytest.py(review33 M2-01)
    write(clone / "skills/analog-gmid-design/assets/tests/test_red.py", RED_TEST)
    write(clone / "skills/analog-gmid-design/assets/rt_mod.py", "def v():\n    return 3\n")
    write(clone / "skills/analog-gmid-design/assets/tests/test_mod.py",
          "import sys, pathlib\nsys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))\n"
          "from rt_mod import v\n\n\ndef test_mod():\n    assert v() == 3\n")
    write(clone / "merge_gate.py", "print('PLANTED merge_gate')\nimport os\nos._exit(0)\n")
    write(clone / "pytest.py", "print('PLANTED pytest')\nimport os\nos._exit(0)\n")
    # 커밋된 .pyc(review34 M3-01 (3)): 검사 없이 쓰이는 unchecked-hash pyc가 rt_mod를 3 -> 4로 바꾼다
    import py_compile
    evil = base / "evil_rt_mod.py"
    write(evil, "def v():\n    print('PLANTED pyc')\n    return 4\n")
    tag = sys.implementation.cache_tag
    pyc = clone / f"skills/analog-gmid-design/assets/__pycache__/rt_mod.{tag}.pyc"
    pyc.parent.mkdir(parents=True, exist_ok=True)
    py_compile.compile(str(evil), cfile=str(pyc), invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
    empty = base / "pyc-empty"
    empty.mkdir()
    cap = base / "red_capture.json"
    tests = posix(clone / "skills/analog-gmid-design/assets/tests")
    ini = posix(cache / "pytest_gate.ini")
    common = ["-m", "pytest", "-c", ini, f"--rootdir={posix(clone)}", f"--confcutdir={posix(clone)}"]
    env_ok = {"PYTHONPATH": str(cache), "PYTHONPYCACHEPREFIX": str(empty), "GMID_RED_CAPTURE": str(cap)}
    env_ok.pop("PYTHONDONTWRITEBYTECODE", None)
    # (1) 설계 명령: $PY -P + 캐시 PYTHONPATH + -c/--rootdir/--confcutdir + PYTHONPYCACHEPREFIX + -p merge_gate
    cmd = [iface.PY, "-P"] + common + ["-p", "merge_gate", "--continue-on-collection-errors", tests]
    r = subprocess.run(cmd, cwd=str(clone), capture_output=True, env=_env_keep_pyc(env_ok))
    record(ns.step, kind="attack", layer="pytest", status="ran", exit_code=r.returncode, stdout=dec(r.stdout),
           stderr=dec(r.stderr), cmd=_cmdstr(cmd), expect=exp_attack,
           note="red 수집 파일: " + (cap.read_text(encoding="utf-8")[:400] if cap.exists() else "없음"))
    # (2) 기록: -P 없이(복제본 루트의 merge_gate.py·pytest.py가 앞선다)
    cmd2 = [iface.PY] + common + ["-p", "merge_gate", tests]
    r2 = subprocess.run(cmd2, cwd=str(clone), capture_output=True, env=_env_keep_pyc(env_ok))
    record(ns.step + "-record-no-P", kind="record", layer="pytest", status="ran", exit_code=r2.returncode,
           stdout=dec(r2.stdout), stderr=dec(r2.stderr), cmd=_cmdstr(cmd2), note="기록(-P 없음): PLANTED가 보이면 -P가 필요한 이유")
    # (3) 기록: PYTHONPYCACHEPREFIX 없이(커밋된 pyc가 쓰인다) + -c/--confcutdir 없이(부모 설정이 읽힌다)
    env3 = dict(env_ok)
    env3.pop("PYTHONPYCACHEPREFIX")
    cmd3 = [iface.PY, "-P", "-m", "pytest", tests]
    r3 = subprocess.run(cmd3, cwd=str(clone), capture_output=True, env=_env_keep_pyc(env3, drop_prefix=True))
    record(ns.step + "-record-unconfined", kind="record", layer="pytest", status="ran", exit_code=r3.returncode,
           stdout=dec(r3.stdout), stderr=dec(r3.stderr), cmd=_cmdstr(cmd3),
           note="기록(가두지 않은 실행): 부모 pytest.ini·conftest와 커밋된 pyc의 영향이 보이면 격리 옵션이 필요한 이유")


def _env_keep_pyc(extra, drop_prefix=False):
    env = sb.clean_env(extra)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    if drop_prefix:
        env.pop("PYTHONPYCACHEPREFIX", None)
    return env


def a_not_implemented(ns):
    record(ns.step, kind="attack", layer=ns.layer, status="not-implemented",
           note="installed 모드 재생은 부트스트랩 ④ 설치 상태(실제 도구 호출·실제 git hook)가 필요하다 -- 이 단계에서는 선언만 한다")


# ----------------------------------------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(prog="rt.py")
    sp = p.add_subparsers(dest="action", required=True)

    s = sp.add_parser("sandbox")
    s.add_argument("--extra-spec", action="append", help="cid|evidence_type|phase")
    s.set_defaults(fn=a_sandbox)

    s = sp.add_parser("flow")
    s.add_argument("key")
    s.add_argument("--cid")
    s.add_argument("--et")
    s.add_argument("--base", default="gate/master")
    s.add_argument("--no-audit", action="store_true")
    s.add_argument("--also-test", action="store_true")
    s.add_argument("--extra-role-test", action="store_true")
    s.add_argument("--code-role", default="code")
    s.add_argument("--test-role", default="test")
    s.add_argument("--code-change-id")
    s.add_argument("--code-extra-file", action="append")
    s.set_defaults(fn=a_flow)

    s = sp.add_parser("flow-step")
    s.add_argument("stage", choices=["start", "test", "code", "worktrees", "audit-wt", "merge", "audit"])
    s.add_argument("cid")
    s.add_argument("--base", default="gate/master")
    s.add_argument("--role")
    s.add_argument("--change-id")
    s.add_argument("--et", default="red-green")
    s.add_argument("--no-commit", action="store_true")
    s.add_argument("--equivalence", action="store_true")
    s.set_defaults(fn=a_flow_step)

    s = sp.add_parser("git")
    s.add_argument("cwd")
    s.add_argument("--save")
    s.add_argument("--allow-fail", action="store_true")
    s.add_argument("args", nargs=argparse.REMAINDER)
    s.set_defaults(fn=a_git)

    s = sp.add_parser("write")
    s.add_argument("path")
    s.add_argument("--text")
    s.add_argument("--jtext")
    s.add_argument("--from-repo")
    s.add_argument("--append", action="store_true")
    s.set_defaults(fn=a_write)

    s = sp.add_parser("set")
    s.add_argument("key")
    s.add_argument("value")
    s.set_defaults(fn=a_set)

    s = sp.add_parser("sh")
    s.add_argument("cwd")
    s.add_argument("command", nargs="?")
    s.add_argument("--command-file")
    s.add_argument("--allow-fail", action="store_true")
    s.set_defaults(fn=a_sh)

    s = sp.add_parser("replace")
    s.add_argument("path")
    s.add_argument("--old", required=True, help="JSON 문자열")
    s.add_argument("--new", required=True, help="JSON 문자열")
    s.set_defaults(fn=a_replace)

    s = sp.add_parser("advance")
    s.add_argument("rev")
    s.set_defaults(fn=a_advance)

    s = sp.add_parser("mkcommit")
    s.add_argument("--parent", action="append", required=True)
    s.add_argument("--tree-from")
    s.add_argument("--file", action="append", help="경로=JSON문자열 또는 경로=@delete")
    s.add_argument("--msg", required=True, help="JSON 문자열")
    s.add_argument("--save", required=True)
    s.set_defaults(fn=a_mkcommit)

    s = sp.add_parser("plan-approval")
    s.add_argument("--plan", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--id", required=True)
    s.set_defaults(fn=a_plan_approval)

    s = sp.add_parser("trailerless")
    s.add_argument("step")
    s.add_argument("--path", required=True)
    s.add_argument("--jtext")
    s.add_argument("--msg")
    s.add_argument("--index-only", action="store_true")
    s.add_argument("--kind", default="attack", choices=["attack", "control", "record"])
    s.set_defaults(fn=a_trailerless)

    for nm, fn in (("hook", a_hook), ("el3", a_el3), ("el4", a_el4)):
        s = sp.add_parser(nm)
        s.add_argument("step")
        s.add_argument("--kind", default="attack", choices=["attack", "control", "record"])
        s.add_argument("--layer", default={"hook": "EL1", "el3": "EL3", "el4": "EL4"}[nm])
        if nm == "hook":
            s.add_argument("--event", default="PreToolUse")
            s.add_argument("--agent")
            s.add_argument("--tool")
            s.add_argument("--input")
            s.add_argument("--input-file", help="CASE_DIR 기준 JSON 파일")
            s.add_argument("--response")
            s.add_argument("--tool-use-id", default="toolu_redteam")
        if nm == "el3":
            s.add_argument("--cwd", required=True)
            s.add_argument("--msg", required=True)
        if nm == "el4":
            s.add_argument("--old", required=True)
            s.add_argument("--new", required=True)
        s.set_defaults(fn=fn)

    s = sp.add_parser("tamper-cache")
    s.add_argument("step")
    s.set_defaults(fn=a_tamper_cache)

    s = sp.add_parser("records")
    s.add_argument("cases")
    s.set_defaults(fn=a_records)

    s = sp.add_parser("vcase")
    s.add_argument("file")
    s.set_defaults(fn=a_vcase)

    s = sp.add_parser("v4probe")
    s.set_defaults(fn=a_v4probe)

    s = sp.add_parser("pytest-candidates")
    s.add_argument("step")
    s.set_defaults(fn=a_pytest_candidates)

    s = sp.add_parser("isolated-run")
    s.add_argument("step")
    s.set_defaults(fn=a_isolated_run)

    s = sp.add_parser("not-implemented")
    s.add_argument("step")
    s.add_argument("--layer", default="installed")
    s.set_defaults(fn=a_not_implemented)

    ns = p.parse_args(argv)
    if getattr(ns, "args", None) and ns.args and ns.args[0] == "--":
        ns.args = ns.args[1:]
    try:
        ns.fn(ns)
    except Missing as e:
        print(f"GATE-CODE-MISSING: {e.paths}", file=sys.stderr)
        return EXIT_MISSING
    return 0


if __name__ == "__main__":
    sys.exit(main())
