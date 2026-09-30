"""V3 대체 측정(auditor 작성, DF-36 2차 시도 순서 3 준비 -- 순서 7에서 쓴다).

왜 대체인가: base 판 mutate_changed.py는 저장소를 .git 없이 임시 디렉터리로 복사해 돌린다. 인벤토리에 든 기존 test
(contracts/test_ts6_probe_relocate.py -- git으로 base blob을 읽는다)가 .git 없는 복사본에서 실패해 '기준 실행 실패'로
모든 변이가 생존 처리된다(도구 환경 한계, 1차 v3_mut.json). 이 스크립트는 **같은 도구 함수**(mutate_changed.changed_defs·
mutants·_replace_def·inventory·inventory_gmid_keys·test_nodeid, reachability.read_tree·build_graph·_is_source·module_name·
_approved_ids, merge_gate.conftest_has_gmid_phase)와 **같은 pytest 명령 모양**(-x -q -p no:cacheprovider + gmid 옵션)을
**.git이 있는 격리 복제본**에서 돌린다. 도구와 다른 점은 작업 위치(복사본 대신 복제본 안에서 변이 파일을 바꾸고 원래
바이트로 되돌림) 하나다.

1차 결함 보정: 면제 승인을 적용한다. 도구와 같이 **head 트리**의 승인 기록(`.ai/approvals/*.md`, target_kind: decision)
`target` 목록(rch._approved_ids(root, head))에 든 변이 id는 실행하지 않고 exempt로 센다(도구 main의 `if mid in approved`).

사용(PYTHONPATH 맨 앞 = base 판 게이트 캐시, -P):
  PYTHONPATH=<캐시> python -P mut_def.py <복제본> <base> <head> <모드> <out.jsonl> [--gmid-phase=<P>] [--gmid-strict=<집합>]
모드:
  list        변이 목록만(실행 없음): 번호·id·exempt 여부·인벤토리 수. 끝에 같은 def의 승인 id 중 어떤 변이와도 안 맞은 것 목록.
  baseline    인벤토리마다 변이 없는 기준 실행(도구의 baseline_ok). 결과를 out에 append.
  <a>:<b>     변이 번호 a 이상 b 미만 실행(exempt는 실행하지 않고 기록). baseline 기록이 out에 있어야 한다.
  summary     out의 기록을 모아 도구와 같은 판정(생존 있으면 FAIL)을 한 줄 JSON으로. exempt는 현재 head 승인으로 다시 판정한다
              (그래서 면제 적용 없이 만든 1차 기록에도 쓸 수 있다). 빠진 번호가 있으면 INCOMPLETE.
결과는 변이마다 out에 append(중간에 죽어도 남는다). 끝에 복제본 git status를 출력한다(빈 문자열이어야 한다).
"""
import hashlib
import json
import os
import re
import subprocess
import sys

import merge_gate as mg
import mutate_changed as mc
import reachability as rch

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

args = [a for a in sys.argv[1:] if not a.startswith("--gmid-")]
opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--gmid-"))
root, base, head, mode, out = args[:5]
root = os.path.abspath(root)
cache = os.environ["PYTHONPATH"].split(os.pathsep)[0]
phase = opts.get("gmid-phase")
strict_v1 = mc._strict_keys(opts.get("gmid-strict", ""))

diff = rch._git(root, ["diff", "--name-only", "--no-renames", "--diff-filter=AM", base, head]).decode("utf-8")
targets = [p for p in diff.splitlines() if p.endswith(".py") and rch._is_source(p)]
head_files = rch.read_tree(root, head, rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(head_files)
test_nodes = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
              and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
approved = rch._approved_ids(root, head)

try:
    with open(os.path.join(root, *mc.CONFTEST_REL.split("/")), "rb") as fh:
        conftest_bytes = fh.read()
except OSError:
    conftest_bytes = None
gmid_supported = phase is not None and mg.conftest_has_gmid_phase(conftest_bytes)

allm = []   # (path, q, fn, inv, mid, mfn)
for path in targets:
    head_src = head_files[path]
    rc = subprocess.run(["git", "-C", root, "cat-file", "-e", "%s:%s" % (base, path)], capture_output=True,
                        env=dict(os.environ, GIT_NO_REPLACE_OBJECTS="1")).returncode
    base_src = rch._git(root, ["show", "%s:%s" % (base, path)]).decode("utf-8") if rc == 0 else None
    modname = rch.module_name(path)
    for q, fn in mc.changed_defs(base_src, head_src):
        inv = mc.inventory(edges, "%s::%s" % (path, q), test_nodes)
        for opname, npath, mfn in mc.mutants(fn, head_src):
            allm.append((path, q, fn, inv, "%s:%s:%s:%s" % (modname, q, opname, npath), mfn))


def inv_key(inv):
    return hashlib.sha256("\n".join(inv).encode("utf-8")).hexdigest()[:16]


def gmid_extra_args(inv):
    if not gmid_supported:
        return []
    keys = sorted(strict_v1 & mc.inventory_gmid_keys(root, inv, phase))
    return ["--gmid-phase=%s" % phase, "--gmid-strict=%s" % ",".join(keys)]


def run_tests(inv):
    env = dict(os.environ, PYTHONPYCACHEPREFIX=os.path.join(os.path.dirname(os.path.abspath(out)), "pyc_mutdef"),
               PYTHONDONTWRITEBYTECODE="1")
    cmd = [sys.executable, "-P", "-m", "pytest", "-c", cache + "/pytest_gate.ini", "--rootdir=" + root,
           "--confcutdir=" + root, "-x", "-q", "-p", "no:cacheprovider"] + gmid_extra_args(inv) + \
          [os.path.join(root, *mc.test_nodeid(t).split("::")[0].split("/")) + "::" + mc.test_nodeid(t).split("::", 1)[1]
           for t in inv]
    try:
        p = subprocess.run(cmd, cwd=root, capture_output=True, env=env, timeout=600)
    except subprocess.TimeoutExpired:
        return "timeout", []
    text = re.sub(r"\x1b\[[0-9;]*m", "", p.stdout.decode("utf-8", "replace"))
    tail = [l for l in text.splitlines() if l.strip()][-2:]
    return p.returncode, tail


def emit(fo, rec):
    fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
    fo.flush()
    print(json.dumps(rec, ensure_ascii=False))


def read_out():
    if not os.path.exists(out):
        return []
    with open(out, "r", encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


if mode == "summary":
    by_id = {r["id"]: r for r in read_out() if "id" in r}
    killed, exempt, survivors, missing = 0, [], [], []
    for path, q, fn, inv, mid, mfn in allm:
        if mid in approved:
            exempt.append(mid)
            continue
        r = by_id.get(mid)
        if r is None:
            missing.append(mid)
        elif r["result"] == "killed":
            killed += 1
        else:
            survivors.append(mid)
    verdict = "INCOMPLETE" if missing else ("FAIL" if survivors else "PASS")
    print(json.dumps({"tool": "V3(대체: .git 있는 격리 복제본)", "verdict": verdict, "targets": targets,
                      "mutants": len(allm), "killed": killed, "exempt": len(exempt), "survivors": survivors,
                      "missing": missing, "exempt_ids": exempt}, ensure_ascii=False))
    sys.exit(0)

fo = open(out, "a", encoding="utf-8")
if mode == "list":
    matched = set()
    for i, (path, q, fn, inv, mid, mfn) in enumerate(allm):
        ex = mid in approved
        if ex:
            matched.add(mid)
        emit(fo, {"list": i, "id": mid, "exempt": ex, "n_inventory": len(inv), "inv": inv_key(inv)})
    defs = {(rch.module_name(p), q) for p, q, *_ in allm}
    unmatched = sorted(a for a in approved if tuple(a.split(":")[:2]) in defs and a not in matched)
    emit(fo, {"n_mutants": len(allm), "n_exempt": len(matched), "targets": targets,
              "approved_ids_same_def_unmatched": unmatched, "gmid_supported": gmid_supported})
elif mode == "baseline":
    seen = set()
    for path, q, fn, inv, mid, mfn in allm:
        k = inv_key(inv)
        if not inv or k in seen:
            continue
        seen.add(k)
        rc, tail = run_tests(inv)
        emit(fo, {"baseline": k, "def": q, "n_inventory": len(inv), "rc": rc, "tail": tail})
else:
    start, end = (int(x) for x in mode.split(":"))
    base_ok = {r["baseline"]: r["rc"] == 0 for r in read_out() if "baseline" in r}
    orig = {}
    for i in range(start, min(end, len(allm))):
        path, q, fn, inv, mid, mfn = allm[i]
        if mid in approved:
            emit(fo, {"i": i, "id": mid, "result": "exempt"})
            continue
        if not inv:
            emit(fo, {"i": i, "id": mid, "result": "survived", "reason": "인벤토리 없음(도달하는 test 없음)"})
            continue
        k = inv_key(inv)
        if k not in base_ok:
            sys.exit("baseline 기록 없음(먼저 baseline 모드): %s" % q)
        if not base_ok[k]:
            emit(fo, {"i": i, "id": mid, "result": "survived", "reason": "변이 없는 기준 실행에서 인벤토리 test가 통과하지 않음"})
            continue
        fpath = os.path.join(root, *path.split("/"))
        if path not in orig:
            b = open(fpath, "rb").read()
            assert b.replace(b"\r\n", b"\n") == head_files[path].encode("utf-8").replace(b"\r\n", b"\n"), \
                "작업 파일 != head blob: " + path
            orig[path] = b
        try:
            with open(fpath, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(mc._replace_def(head_files[path], fn, mfn))
            rc, tail = run_tests(inv)
        finally:
            with open(fpath, "wb") as fh:
                fh.write(orig[path])
        emit(fo, {"i": i, "id": mid, "rc": rc, "result": "killed" if rc != 0 else "survived", "tail": tail})
fo.close()
st = subprocess.run(["git", "-C", root, "status", "--porcelain"], capture_output=True).stdout.decode()
print("status_after", repr(st))
