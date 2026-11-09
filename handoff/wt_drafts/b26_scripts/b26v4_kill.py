"""B26-1 v4 -- 대상 변이를 b1(모의 base)의 같은 문장 변이로 옮겨 기존 test 인벤토리로 실행 (review2_b26_1 §3 근사의 재현).

대응: (연산자, 정규화한 문장 글, 순번). 정규화 = rails.nets <-> _RAIL_NETS, rails=rails 제거, 씨앗 dict, SR 두 줄.
  문장 글: 단순문 = unparse 전체, 복합문 자기 필드 변이 = 머리(블록을 pass로 비운 unparse), 문장 삭제 = 전체 unparse + '#del'.
  def 자기 필드(기본값 등) 변이는 경로 그대로, early_return은 early_return끼리.
실행: b1 사본 C:/g83/w<k>(k < NW)에서 도구와 같은 pytest 인자 + -x, --gmid-phase=2 --gmid-strict=, PYTHONHASHSEED=1.
  인벤토리 = b1 그래프의 그 def 인벤토리(test_ts6_probe_relocate 2개 제외 -- 사본에 .git 없음).
출력: C:/g83/out/kill_<mode>.jsonl (변이마다 append), kill_<mode>_baseline.json
사용: python -B b26v4_kill.py <mode> <NW> [extra_test_nodeid ...]
"""
import ast, copy, json, os, re, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_scripts")
import b26v4_classify as C   # noqa: E402
W, V, S, mc, rch = C.W, C.V, C.S, C.mc, C.rch

PY = "C:/Python314/python.exe"
INI = "C:/g83/b1/tools/gates/pytest_gate.ini"
OUT = "C:/g83/out/"


def norm(t):
    t = t.replace("set(_topology_meta_cached(ctx.topology_path)['rails'].nets)",
                  "set(spec.get('rail_nets') or ('vdd', 'VDD', 'gnd', 'GND', 'vss', 'VSS'))")
    t = t.replace("set(rails.nets)", "set(_DEFAULT_RAIL_HI) | set(_DEFAULT_RAIL_LO)")
    t = t.replace("{n: n for n in rails.nets}", "{'vdd': 'vdd', 'gnd': 'gnd'}")
    t = t.replace("rails.nets", "_RAIL_NETS")
    t = t.replace(", rails=rails", "").replace("(rails=rails)", "()")
    return t


def header_text(n):
    c = copy.copy(n)
    for f in V.BLOCK:
        v = getattr(c, f, None)
        if isinstance(v, list) and v:
            setattr(c, f, [ast.Pass()] if f != "handlers" and f != "cases" else [])
    try:
        return ast.unparse(c)
    except Exception:
        return ast.dump(c, include_attributes=False)


def stmt_of(fn, op, mpath):
    """(키 글) -- 변이가 걸린 문장."""
    if op == "early_return":
        return ("ER",)
    np_ = V.node_path(op, mpath)
    if np_ and V.split_path(np_)[0][0] not in V.BLOCK:
        return ("DEFSELF", np_)
    if op in ("stmt_delete", "except_body_delete"):
        node = mc._get(fn, np_)
        return ("DEL" + op, norm(ast.unparse(node)))
    pre = V.stmt_prefixes(np_)
    node_full = mc._get(fn, np_)
    if isinstance(node_full, (ast.stmt, ast.ExceptHandler)):
        sp = np_
    else:
        sp = pre[-1]
    s = mc._get(fn, sp)
    if V.is_compound(s) or isinstance(s, ast.ExceptHandler):
        return ("HDR", norm(header_text(s)))
    return ("S", norm(ast.unparse(s)))


def keyed(fn, src):
    out = {}
    cnt = {}
    for op, p, mfn in mc.mutants(fn, src):
        k = (op,) + stmt_of(fn, op, p)
        if k[1] == "DEFSELF":
            key = k + (p,)
        else:
            i = cnt.get(k, 0)
            cnt[k] = i + 1
            key = k + (i,)
        out[(op, p)] = (key, mfn)
    return out


def build_jobs(mode, which):
    head, _ = C.H.build_head(mode)
    base = S.BASEF
    tgt = json.load(open(OUT + "targets_%s.json" % mode, encoding="utf-8"))
    tgt = [t for t in tgt if t[which]]
    nodes, edges = rch.build_graph(base)
    tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
             and re.search(r"::(Test[^.]*\.)?test[^.]*$", n) and "test_ts6_probe_relocate" not in n]
    cache = {}
    jobs, unmapped = [], []
    for t in tgt:
        path, q = t["file"], t["def_"]
        if t.get("new_def"):
            unmapped.append(dict(id=t["id"], why="new def"))
            continue
        ck = (path, q)
        if ck not in cache:
            bd = dict(rch.iter_defs(ast.parse(base[path])))[q]
            hd = dict(rch.iter_defs(ast.parse(head[path])))[q]
            hk = keyed(hd, head[path])
            bk = keyed(bd, base[path])
            rev = {v[0]: (p, v[1]) for p, v in bk.items()}
            inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
            cache[ck] = (bd, hk, rev, inv)
        bd, hk, rev, inv = cache[ck]
        key = hk[(t["op"], t["path"])][0]
        if key not in rev:
            unmapped.append(dict(id=t["id"], why="no counterpart", key=str(key)[:200]))
            continue
        bpath, bmfn = rev[key]
        jobs.append(dict(id=t["id"], file=path, def_=q, b1_path="%s:%s" % (t["op"], bpath), inv=inv,
                         N2b=t["N2b"], N2w=t["N2w"], N2d=t["N2d"],
                         src=mc._replace_def(base[path], bd, bmfn)))
    return jobs, unmapped


def run_pytest(work, inv, extra):
    env = dict(os.environ, PYTHONPYCACHEPREFIX=work + "_pyc", PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="1")
    cmd = [PY, "-P", "-m", "pytest", "-c", INI, "--rootdir=" + work, "--confcutdir=" + work, "-x", "-q",
           "-p", "no:cacheprovider", "--gmid-phase=2", "--gmid-strict="] + \
          [os.path.join(work, *mc.test_nodeid(t).split("::")[0].split("/")) + "::" + mc.test_nodeid(t).split("::", 1)[1]
           for t in inv] + list(extra)
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=work, capture_output=True, env=env, timeout=1500)
        return r.returncode, time.time() - t0, r.stdout.decode("utf-8", "replace")[-600:]
    except subprocess.TimeoutExpired:
        return "timeout", time.time() - t0, ""


CFIRST = False
CREL = "skills/analog-gmid-design/assets/tests/contracts/test_b26x_approx.py"
CSRC = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_scripts/test_b26x_approx.py"


def main(mode, nw, which, extra):
    jobs, unmapped = build_jobs(mode, which)
    tag = "%s_%s%s" % (mode, which, "_x" if extra else "")
    if CFIRST:
        for k in range(nw):
            w = "C:/g83/w%d" % k
            if os.path.exists(w):
                shutil.copyfile(CSRC, os.path.join(w, *CREL.split("/")))
    res_path = OUT + "kill_%s.jsonl" % tag
    done = set()
    if os.path.exists(res_path):
        for l in open(res_path, encoding="utf-8"):
            done.add(json.loads(l)["id"])
    json.dump(unmapped, open(OUT + "unmapped_%s.json" % tag, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("jobs", len(jobs), "unmapped", len(unmapped), "done", len(done), flush=True)
    jobs.sort(key=lambda j: (not j["N2w"],))   # 확정 규칙(N2w) 대상 먼저
    for k in range(nw):
        w = "C:/g83/w%d" % k
        if not os.path.exists(w):
            shutil.copytree("C:/g83/b1", w)
        if CFIRST:
            shutil.copyfile(CSRC, os.path.join(w, *CREL.split("/")))
    pool = ["C:/g83/w%d" % k for k in range(nw)]
    lock = threading.Lock()
    # 기준 실행(인벤토리별 1회)
    bl_path = OUT + "kill_%s_baseline.json" % tag
    base_ok = json.load(open(bl_path)) if os.path.exists(bl_path) else {}
    invs = sorted({tuple(j["inv"]) for j in jobs if j["inv"]} - {tuple(json.loads(k)) for k in base_ok})

    def bl(inv):
        with lock:
            w = pool.pop()
        try:
            rc, dt, tail = run_pytest(w, inv, extra)
        finally:
            with lock:
                pool.append(w)
        with lock:
            base_ok[json.dumps(list(inv))] = dict(rc=rc, s=round(dt, 1), tail=tail)
            json.dump(base_ok, open(bl_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print("baseline", len(inv), rc, round(dt), flush=True)
    with ThreadPoolExecutor(nw) as ex:
        list(ex.map(bl, invs))
    bad = [k for k, v in base_ok.items() if v["rc"] != 0]
    if bad:
        print("BASELINE FAILED", [base_ok[k]["tail"][-300:] for k in bad])
        return

    def one(j):
        if j["id"] in done:
            return
        if not j["inv"]:
            rec = dict(id=j["id"], result="survived", reason="no inventory")
        else:
            with lock:
                w = pool.pop()
            fp = os.path.join(w, *j["file"].split("/"))
            orig = S.BASEF[j["file"]]   # 되돌림은 b1 원본으로(중단 뒤 재시작해도 사본이 변이된 채 남지 않게)
            try:
                with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(j["src"])
                via = "inventory"
                rc = 0
                if CFIRST:
                    rc, dt, tail = run_pytest(w, [], [os.path.join(w, *CREL.split("/"))])
                    via = "contract"
                if rc == 0:
                    rc, dt2, tail = run_pytest(w, j["inv"], extra)
                    dt = (dt if CFIRST else 0) + dt2
                    via = "inventory"
            finally:
                with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(orig)
                with lock:
                    pool.append(w)
            rec = dict(id=j["id"], result="survived" if rc == 0 else "killed", exit=rc, s=round(dt, 1),
                       by=None if rc == 0 else via)
        rec.update(b1=j["b1_path"], N2b=j["N2b"], N2w=j["N2w"], N2d=j["N2d"], inv=len(j["inv"]))
        with lock:
            with open(res_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(rec["result"], rec["id"], rec.get("s"), flush=True)
    with ThreadPoolExecutor(nw) as ex:
        list(ex.map(one, jobs))
    print("DONE", flush=True)


if __name__ == "__main__":
    mode, nw, which = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    rest = sys.argv[4:]
    if rest[:1] == ["--contracts-first"]:
        CFIRST = True
        rest = rest[1:]
    main(mode, nw, which, rest)
