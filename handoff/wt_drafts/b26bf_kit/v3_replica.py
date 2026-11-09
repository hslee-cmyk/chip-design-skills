"""backfill card V3 -- 도구(mutate_changed.py main)와 같은 변이·같은 pytest 명령을 여러 작업 사본에서 병렬로 돌리는 보조 실행기.

도구 실행(run_v3_tool.sh)이 직렬이라 97 변이에 ~2.5시간 걸린다. 이 실행기는 도구 결과(--out jsonl)에 아직 없는 변이를
**뒤에서부터** 처리해 겹침을 줄이고, 끝나면 두 결과를 id로 합친다(도구 결과가 있으면 도구 것을 쓴다).
변이 생성·def 치환·인벤토리·pytest 인자는 게이트 코드(C:/g128/gate0/tools/gates, gate master 0f23786 archive)의 함수를 그대로 부른다.
사용: python -B v3_replica.py <base> <head> <label> <workers>   결과: C:/g128/out/v3rep_<label>.jsonl, v3merged_<label>.json"""
import json, os, re, shutil, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor

G = "C:/g128"
CL = G + "/sim/r"
GATES = G + "/gate0/tools/gates"
sys.path.insert(0, GATES)
import mutate_changed as mc   # noqa: E402
import reachability as rch    # noqa: E402

base, head, label, nw = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
TOOL = G + "/out/v3tool_%s.jsonl" % label
REP = G + "/out/v3rep_%s.jsonl" % label
PY = "C:/Python314/python.exe"


def git(*a):
    return subprocess.run(["git", "-C", CL] + list(a), capture_output=True, check=True).stdout


def done_ids(p):
    if not os.path.exists(p):
        return {}
    out = {}
    for l in open(p, encoding="utf-8"):
        l = l.strip()
        if l:
            r = json.loads(l)
            out[r["id"]] = r
    return out


diff = git("diff", "--name-only", "--no-renames", "--diff-filter=AM", base, head).decode("utf-8")
targets = [p for p in diff.splitlines() if p.endswith(".py") and rch._is_source(p)]
head_files = rch.read_tree(CL, head, rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(head_files)
tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
         and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
jobs = []
for path in targets:
    hsrc = head_files[path]
    bsrc = git("show", "%s:%s" % (base, path)).decode("utf-8")
    mod = rch.module_name(path)
    for q, fn in mc.changed_defs(bsrc, hsrc):
        inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
        for op, npath, mfn in mc.mutants(fn, hsrc):
            jobs.append({"id": "%s:%s:%s:%s" % (mod, q, op, npath), "path": path, "src": mc._replace_def(hsrc, fn, mfn),
                         "head_src": hsrc, "inv": inv})
order = list(reversed(jobs))
pool = []
for k in range(nw):
    w = G + "/rep/w%d" % k
    if not os.path.exists(w):
        os.makedirs(os.path.dirname(w), exist_ok=True)
        mc.make_clone(CL, w, head)
    pool.append(w)
lock = threading.Lock()


def run_tests(work, inv):
    env = dict(os.environ, PYTHONPYCACHEPREFIX=work + "_pyc", PYTHONDONTWRITEBYTECODE="1")
    cmd = [PY, "-P", "-m", "pytest", "-c", GATES + "/pytest_gate.ini", "--rootdir=" + work, "--confcutdir=" + work, "-x", "-q",
           "-p", "no:cacheprovider", "--gmid-phase=2", "--gmid-strict="] + \
          [os.path.join(work, *mc.test_nodeid(t).split("::")[0].split("/")) + "::" + mc.test_nodeid(t).split("::", 1)[1] for t in inv]
    try:
        return subprocess.run(cmd, cwd=work, capture_output=True, env=env, timeout=600).returncode
    except subprocess.TimeoutExpired:
        return "timeout"


def one(j):
    if j["id"] in done_ids(TOOL) or j["id"] in done_ids(REP):
        return
    with lock:
        w = pool.pop()
    fp = os.path.join(w, *j["path"].split("/"))
    try:
        with open(fp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(j["src"])
        code = run_tests(w, j["inv"])
    finally:
        with open(fp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(j["head_src"])
        with lock:
            pool.append(w)
    rec = {"id": j["id"], "result": "survived" if code == 0 else "killed", "exit": code, "runner": "replica"}
    with lock:
        with open(REP, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(rec["result"], rec["id"], flush=True)


if __name__ == "__main__":
    # 기준 실행(도구와 같은 WP-02 확인) -- 작업 사본 하나에서
    bc = run_tests(pool[0], jobs[0]["inv"])
    assert bc == 0, "baseline failed %s" % bc
    with ThreadPoolExecutor(nw) as ex:
        list(ex.map(one, order))
    tool, rep = done_ids(TOOL), done_ids(REP)
    merged = []
    for j in jobs:
        r = tool.get(j["id"]) or rep.get(j["id"])
        merged.append({"id": j["id"], "result": r["result"] if r else "missing", "by": "tool" if j["id"] in tool else ("replica" if r else None)})
    both = [i for i in tool if i in rep]
    agree = all(tool[i]["result"] == rep[i]["result"] for i in both)
    res = {"jobs": len(jobs), "by_tool": sum(m["by"] == "tool" for m in merged), "by_replica": sum(m["by"] == "replica" for m in merged),
           "overlap": len(both), "overlap_agree": agree,
           "survived": [m["id"] for m in merged if m["result"] == "survived"], "missing": [m["id"] for m in merged if m["result"] == "missing"],
           "merged": merged}
    with open(G + "/out/v3merged_%s.json" % label, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "merged"}, ensure_ascii=False))
