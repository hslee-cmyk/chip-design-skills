"""통합 계획의 두 시나리오를 같은 방식으로 잰다(승인 범위 규칙 N2w, v4 head, 시제품 합집합).

공통 전제(통합안): b26pre test-only card(v2 시제품 17 test) + backfill 결함 card(U-BF 선택지 1 -- SR 11800·11879 삭제)가 B26-1 앞에 병합.
  baseF = b1(HEAD + B34) + backfill 수정(b26v4c C4, SR만)
  시나리오 A(등가는 면제): head = baseF 위 B26-1 v4
  시나리오 B(등가 정리):   head = baseF 위 B26-1 v4 + 정리 C1·C2·C3(b26v4c)
  변이 실행 base(대응·소스): A = baseF, B = baseF + C1·C2·C3(rails 없이)
UNION 시제품(worker의 tests/contracts/):
  CON  = test_b26x_approx.py + test_b26x_metric_approx.py   (B26-1 계약 근사)
  PRE  = test_b26pre_card.py  <- b26pre_v2_scripts/proto_v2_test_b26pre.py (b26pre v2 시제품 17)
  TRACE= test_b26pre_trace.py <- proto_test_b26pre_trace.py (이번 보강 제안 2)
  BF   = test_b26bf.py        <- b26pre_v2_scripts/proto_bf_test.py (backfill card red-green 2, baseF에서 green)
사용: python -B plan_measure.py <A|B> classify
      python -B plan_measure.py <A|B> baseline
      python -B plan_measure.py <A|B> proto <NW>          -> C:/g103/out/plan_<S>_proto.jsonl (그룹별 판정)
      python -B plan_measure.py <A|B> existing <NW>       -> UNION 생존만 기존 인벤토리 -> plan_<S>_existing.jsonl
"""
import json, os, shutil, sys, threading
from concurrent.futures import ThreadPoolExecutor

R = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile/"
V2 = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26pre_v2_scripts/"
sys.path.insert(0, R)
import b26v4c as VC            # noqa: E402
import reconcile_run as RR     # noqa: E402
H, C, K = VC.H, VC.C, RR.K
S = H.S
OUT = "C:/g103/out/"
TD = RR.TD
FILES = {"test_b26x_approx.py": R + "test_b26x_approx.py",
         "test_b26x_metric_approx.py": R + "test_b26x_metric_approx.py",
         "test_b26pre_card.py": V2 + "proto_v2_test_b26pre.py",
         "test_b26pre_trace.py": R + "proto_test_b26pre_trace.py",
         "test_b26bf.py": V2 + "proto_bf_test.py"}
GROUPS = {"con": ["test_b26x_approx.py", "test_b26x_metric_approx.py"], "pre": ["test_b26pre_card.py"],
          "trace": ["test_b26pre_trace.py"], "bf": ["test_b26bf.py"]}

B1 = dict(S.BASEF)
_orig_build = VC._orig_build


def with_only(only, fn):
    old = VC.ONLY
    VC.ONLY = only
    try:
        return fn()
    finally:
        VC.ONLY = old


baseF = with_only({"C4"}, lambda: VC.cleanup(dict(B1), rr=""))


def set_base(d):
    S.BASEF = d
    K.S.BASEF = d


def head_for(sc):
    set_base(baseF)
    h, o = _orig_build("v4")
    if sc == "B":
        h = with_only({"C1", "C2", "C3"}, lambda: VC.cleanup(h))
    return h, o


def run_base_for(sc):
    if sc == "A":
        return baseF
    return with_only({"C1", "C2", "C3"}, lambda: VC.cleanup(dict(baseF), rr=""))


def prep(sc):
    mode = "plan" + sc
    hh = head_for(sc)
    H.build_head = lambda m: hh
    set_base(baseF)
    return mode


def pool_for(sc, nw):
    rb = run_base_for(sc)
    pool = []
    for k in range(nw):
        w = "C:/g103/p%s%d" % (sc.lower(), k)
        if not os.path.exists(w):
            shutil.copytree("C:/g103/b1", w)
        for rel in (S.SD, S.SR):
            with open(os.path.join(w, *rel.split("/")), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(rb[rel])
        for dst, src in FILES.items():
            shutil.copyfile(src, os.path.join(w, *(TD + dst).split("/")))
        pool.append(w)
    return pool


def jobs_for(sc, mode):
    K.OUT = OUT
    set_base(run_base_for(sc))     # 대응·변이 소스 = 실행 base
    jobs, unmapped = K.build_jobs(mode, "N2w")
    json.dump(unmapped, open(OUT + "plan_%s_unmapped.json" % sc, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return jobs, unmapped


def run_jobs(sc, jobs, pool, path, fn):
    lock = threading.Lock()
    done = RR.done_ids(path)
    rb = run_base_for(sc)

    def one(j):
        if j["id"] in done:
            return
        with lock:
            w = pool.pop()
        fp = os.path.join(w, *j["file"].split("/"))
        try:
            with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(j["src"])
            rec = fn(w, j)
        finally:
            with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(rb[j["file"]])
            with lock:
                pool.append(w)
        rec.update(id=j["id"], b1=j["b1_path"], inv=len(j["inv"]), N2b=j["N2b"])
        with lock:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(j["id"], {k: v for k, v in rec.items() if k in GROUPS or k == "result"}, flush=True)
    with ThreadPoolExecutor(len(pool)) as ex:
        list(ex.map(one, jobs))


def main():
    sc, what = sys.argv[1], sys.argv[2]
    mode = prep(sc)
    if what == "classify":
        C.main(mode)
        return
    if what == "baseline":
        pool = pool_for(sc, 1)
        with open(OUT + "plan_%s_baseline.txt" % sc, "w", encoding="utf-8") as fh:
            for g, names in GROUPS.items():
                rc, s, failed, tail = RR.run_files(pool[0], names)
                fh.write("%s rc=%s %ss failed=%s\n%s\n" % (g, rc, s, failed, tail[-400:]))
                print(g, rc, s, failed, flush=True)
        return
    nw = int(sys.argv[3])
    jobs, unmapped = jobs_for(sc, mode)
    print("jobs", len(jobs), "unmapped", len(unmapped), flush=True)
    if what == "proto":
        def fn(w, j):
            rec = {}
            for g, names in GROUPS.items():
                rc, s, failed, _ = RR.run_files(w, names)
                rec[g] = "killed" if rc != 0 else "survived"
                rec[g + "_failed"] = failed
            return rec
        run_jobs(sc, jobs, pool_for(sc, nw), OUT + "plan_%s_proto.jsonl" % sc, fn)
    elif what == "existing":
        pr = [json.loads(l) for l in open(OUT + "plan_%s_proto.jsonl" % sc, encoding="utf-8")]
        ids = {r["id"] for r in pr if all(r[g] == "survived" for g in GROUPS)}
        if len(sys.argv) > 4 and sys.argv[4] == "all":
            ids = {r["id"] for r in pr}
        sel = [j for j in jobs if j["id"] in ids]
        print("existing jobs", len(sel), flush=True)

        def fe(w, j):
            if not j["inv"]:
                return dict(result="survived", reason="no inventory")
            rc, s, _t = K.run_pytest(w, j["inv"], [])
            return dict(result="killed" if rc != 0 else "survived", rc=rc, s=round(s, 1))
        run_jobs(sc, sel, pool_for(sc, min(nw, max(1, len(sel)))), OUT + "plan_%s_existing.jsonl" % sc, fe)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
