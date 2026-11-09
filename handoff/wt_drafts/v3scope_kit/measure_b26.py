"""V3 범위 card 착수 키트 -- B26-1 등 대상 변이 수 재측정(scratch C:/g109, 저장소 읽기 전용).

격리 복제본 C:/g109/repo(origin 없음, 빈 hooksPath)에 모의 커밋을 만들고, 도구 `main`과 같은 경로
(`git diff --name-only --no-renames --diff-filter=AM` → `rch._is_source` → `changed_defs` → `mutants` → id)로 변이를 만든 뒤
독립 프로토타입 scope_proto.select(계약 1)로 대상을 고른다. pytest는 돌리지 않는다(대상 수·시간 추정만).

모의 커밋:
  P0  = 인자 REV(gate master, 기본 0f23786)
  B1  = P0 + B34 코드 변경(mk_b1.py가 C:/g109/b1에 쓴 SD)                       -- "B34 좁힌 초안" = P0..B1
  H4  = B1 + B26-1 card v4 head(b26v4_head.build_head("v4"))                     -- "B26-1 v4"     = B1..H4  (정본)
  H2  = B1 + review2 head(build_head("review2"))                                 -- "B26-1 review2" = B1..H2
  O0  = 7535799, HO = O0 + 옛 시뮬레이션 build_b26(옛 SITE_SD)                   -- "B26-1 옛 시뮬" = O0..HO (승인 당시 228 재현)
  P9  = 6bf510b..93b18db(실제 P9 병합)
결과: C:/g109/out/measure_b26.txt(append), measure_b26.json, ids_<label>.json -> 키트 out/로 복사.
"""
import ast, io, json, os, re, subprocess, sys, tarfile, time

G = "C:/g109"
CL = G + "/repo"
KIT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3scope_kit"
sys.path.insert(0, KIT)
sys.path.insert(0, G + "/scripts")
sys.path.insert(0, CL + "/tools/gates")
import mutate_changed as mc     # noqa: E402  (복제본 도구 -- 0f23786 판)
import reachability as rch      # noqa: E402
import scope_proto as SP        # noqa: E402

REV = sys.argv[1] if len(sys.argv) > 1 else "0f23786"
TXT = G + "/out/measure_b26.txt"
LOW_S = 5.0


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(TXT, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def git(*a):
    r = subprocess.run(["git", "-C", CL] + list(a), capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def commit_files(parent, files, msg, branch):
    git("checkout", "--quiet", "-B", branch, parent)
    for rel, txt in files.items():
        p = os.path.join(CL, *rel.split("/"))
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt)
        git("add", "--", rel)
    git("commit", "--quiet", "-m", msg)
    return git("rev-parse", "HEAD").decode().strip()


def measure(label, base, head):
    t0 = time.time()
    diff = git("diff", "--name-only", "--no-renames", "--diff-filter=AM", base, head).decode("utf-8")
    targets = [p for p in diff.splitlines() if p.endswith(".py") and rch._is_source(p)]
    head_files = rch.read_tree(CL, head, rch.GRAPH_PREFIXES)
    nodes, edges = rch.build_graph(head_files)
    tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
             and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
    dur = DUR
    res = {"label": label, "base": base, "head": head, "targets": targets, "defs": [], "ids": {"N2w": [], "N2b": [], "all": []}}
    tot = {"all": 0, "N2b": 0, "N2w": 0, "high_N2b": 0.0, "high_N2w": 0.0, "inv0_N2w": 0, "nodur_tests": set()}
    for path in targets:
        hsrc = head_files[path]
        rc = subprocess.run(["git", "-C", CL, "cat-file", "-e", "%s:%s" % (base, path)], capture_output=True).returncode
        bsrc = git("show", "%s:%s" % (base, path)).decode("utf-8") if rc == 0 else None
        bdefs = dict(rch.iter_defs(ast.parse(bsrc))) if bsrc else {}
        mod = rch.module_name(path)
        for q, hfn in mc.changed_defs(bsrc, hsrc):
            ms = mc.mutants(hfn, hsrc)
            if q in bdefs:
                w = SP.select(bdefs[q], hfn, ms, "N2w")
                b = SP.select(bdefs[q], hfn, ms, "N2b")
            else:
                w = b = [True] * len(ms)
            inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
            invs = sum(dur.get(x, 0.0) for x in inv)
            tot["nodur_tests"].update(x for x in inv if x not in dur)
            nw, nb = sum(w), sum(b)
            tot["all"] += len(ms); tot["N2w"] += nw; tot["N2b"] += nb
            tot["high_N2w"] += nw * invs; tot["high_N2b"] += nb * invs
            if not inv:
                tot["inv0_N2w"] += nw
            ids = ["%s:%s:%s:%s" % (mod, q, o, p) for o, p, _ in ms]
            res["ids"]["all"] += ids
            res["ids"]["N2w"] += [i for i, s in zip(ids, w) if s]
            res["ids"]["N2b"] += [i for i, s in zip(ids, b) if s]
            res["defs"].append({"def": path.split("/")[-1] + "::" + q, "new": q not in bdefs, "all": len(ms),
                                "N2b": nb, "N2w": nw, "inv": len(inv), "inv_s": round(invs, 1)})
    log("== %s  base %s head %s  (%.0f s)" % (label, base[:10], head[:10], time.time() - t0))
    log("   changed defs %d (new %d) | all %d | N2b(승인 당시) %d | N2w(이 card) %d" % (
        len(res["defs"]), sum(d["new"] for d in res["defs"]), tot["all"], tot["N2b"], tot["N2w"]))
    for k in ("N2b", "N2w"):
        log("   %s: 하한 %.1f 분, 상한 %.2f h" % (k, tot[k] * LOW_S / 60, tot["high_" + k] / 3600))
    log("   인벤토리 0 대상(N2w) %d, junit 시간 없는 인벤토리 test %d개(상한에 0초로 셈)" % (tot["inv0_N2w"], len(tot["nodur_tests"])))
    for d in sorted(res["defs"], key=lambda d: (-d["N2w"], d["def"])):
        log("   %-70s all=%4d N2b=%3d N2w=%3d inv=%d%s" % (d["def"], d["all"], d["N2b"], d["N2w"], d["inv"], " (새 def)" if d["new"] else ""))
    res["tot"] = {k: (sorted(v) if isinstance(v, set) else v) for k, v in tot.items()}
    with open(G + "/out/ids_%s.json" % label, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=0)
    return res


if __name__ == "__main__":
    open(TXT, "w").close()
    import b26v4_head as H               # sim_head(BASE = C:/g109/b1)를 import
    S = H.S
    DUR = S.durations()                  # junit_base.xml(7535799 사본 전체 test 1회) 재사용
    P0 = git("rev-parse", REV).decode().strip()
    B1 = commit_files(P0, {S.SD: S.BASEF[S.SD]}, "sim: B34 code (b1)", "sim-b1")
    head4, _ = H.build_head("v4")
    H4 = commit_files(B1, {p: t for p, t in head4.items() if t != S.BASEF.get(p)}, "sim: B26-1 v4 head", "sim-h4")
    head2, _ = H.build_head("review2")
    H2 = commit_files(B1, {p: t for p, t in head2.items() if t != S.BASEF.get(p)}, "sim: B26-1 review2 head", "sim-h2")
    # 옛 시뮬레이션(승인 당시 수치 228/294의 head): base 7535799, sim_head 사본을 b0으로
    b0 = G + "/b0"
    if not os.path.exists(b0):
        os.makedirs(b0)
        tarfile.open(fileobj=io.BytesIO(git("archive", "7535799"))).extractall(b0, filter="data")
    src0 = open(G + "/scripts/sim_head.py", encoding="utf-8").read().replace('BASE = "C:/g109/b1"', 'BASE = "C:/g109/b0"') \
        .replace("v3_measure.txt", "v3_measure0.txt")
    import types
    S0 = types.ModuleType("sim_head0")
    S0.__file__ = G + "/scripts/sim_head0.py"
    exec(compile(src0, S0.__file__, "exec"), S0.__dict__)
    headO, _ = S0.build_b26(S0.BASEF)
    O0 = git("rev-parse", "7535799").decode().strip()
    HO = commit_files(O0, {p: t for p, t in headO.items() if t != S0.BASEF.get(p)}, "sim: B26-1 old sim head", "sim-ho")
    git("checkout", "--quiet", "sim")
    out = {}
    for label, b, h in (("b26_v4", B1, H4), ("b26_review2", B1, H2), ("b26_oldsim", O0, HO),
                        ("p9_real", "6bf510b", "93b18db"), ("b34_narrow", P0, B1)):
        r = measure(label, git("rev-parse", b).decode().strip(), git("rev-parse", h).decode().strip())
        out[label] = {"base": r["base"], "head": r["head"], **{k: r["tot"][k] for k in ("all", "N2b", "N2w")}}
    with open(G + "/out/measure_b26.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    log("done", json.dumps(out, ensure_ascii=False))
