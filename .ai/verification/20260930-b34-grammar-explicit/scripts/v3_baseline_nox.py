"""V3 기준 실행 미리 확인(B28): 도구 main과 같은 방식으로 T 트리 그래프의 4 def 인벤토리를 만들고,
mutate_changed.make_clone(이력 있는 복제본, origin 없음)에서 도구 run_tests와 같은 pytest 명령(-x, gmid 옵션)으로
인벤토리마다 변이 없는 기준 실행을 한다(-x 없이 -- 실패 집합을 모은다. T에서는 새 red test가 실패하는 것이 정상). 도구와 달리 timeout을 두지 않고 걸린 시간을 적는다(도구 기본 600s와 대조).
사용: PYTHONPATH=<캐시> python -P v3_baseline.py <복제본(.git 있음)> <rev> <work> <ini> <out.jsonl>"""
import json, os, re, subprocess, sys, time
import mutate_changed as mc, reachability as rch, merge_gate as mg

root, rev, work, ini, out = sys.argv[1:6]
PHASE, STRICT = "3", set()
SD = "skills/analog-gmid-design/assets/stick_diagram.py"
DEFS = ("_import_analog_grammar", "find_idiom_matches", "find_stack_edges", "audit_theta_root_direction")
hf = rch.read_tree(root, rev, rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(hf)
tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
         and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
mc.make_clone(root, work, rev) if not os.path.isdir(work) else None
pyc = os.path.join(os.path.dirname(work), "pyc_v3base")
os.makedirs(pyc, exist_ok=True)
with open(os.path.join(work, *mc.CONFTEST_REL.split("/")), "rb") as fh:
    gmid_supported = mg.conftest_has_gmid_phase(fh.read())
done = {}
for q in DEFS:
    inv = mc.inventory(edges, "%s::%s" % (SD, q), tests)
    key = tuple(inv)
    if key in done:
        rec = {"def": q, "n": len(inv), "same_as": done[key]}
    else:
        extra = []
        if gmid_supported:
            extra = ["--gmid-phase=%s" % PHASE, "--gmid-strict=%s" % ",".join(sorted(STRICT & mc.inventory_gmid_keys(work, inv, PHASE)))]
        cmd = [sys.executable, "-P", "-m", "pytest", "-c", ini, "--rootdir=" + work, "--confcutdir=" + work,
               "-q", "-rf", "-p", "no:cacheprovider"] + extra + \
              [os.path.join(work, *mc.test_nodeid(t).split("::")[0].split("/")) + "::" + mc.test_nodeid(t).split("::", 1)[1] for t in inv]
        env = dict(os.environ, PYTHONPYCACHEPREFIX=pyc, PYTHONDONTWRITEBYTECODE="1")
        s = time.time()
        r = subprocess.run(cmd, cwd=work, capture_output=True, env=env)
        el = round(time.time() - s, 1)
        _o = r.stdout.decode("utf-8", "replace").strip().splitlines(); tail = _o[-1:]; failed = sorted(l[7:].split(" - ")[0] for l in _o if l.startswith("FAILED "))
        rec = {"def": q, "n": len(inv), "rc": r.returncode, "elapsed_s": el, "over_tool_timeout_600": el > 600,
               "gmid_args": extra, "tail": tail, "n_failed": len(failed), "failed": failed}
        done[key] = q
    with open(out, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False), flush=True)
st = subprocess.run(["git", "-C", work, "status", "--porcelain"], capture_output=True).stdout.decode()
with open(out, "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"work_status_lines": len(st.splitlines()), "head": rev}) + "\n")
