"""통합 재측정 2단계 -- (A) v4 잔존 변이에 trace 보강 시제품, (B) 정리 변형 v4c 전체.

(A) python -B reconcile_run2.py trace_v4 <NW> <ids.json>
    v4 변이(b1 대응)에 TRACE(proto_test_b26pre_trace.py)만 실행 -> out/trace_v4.jsonl
(B) python -B reconcile_run2.py v4c_proto <NW>
    v4c(= v4 head + b26v4c 정리) N2w 대상을 b1c(= b1 + 같은 정리, rails 없이)의 같은 문장 변이로 옮겨
    UNION(CON + PRE + TRACE) 실행 -> out/v4c_proto.jsonl
    python -B reconcile_run2.py v4c_existing <NW> <ids.json>  -> 지정 변이를 b1c 기존 인벤토리로 -> out/v4c_existing.jsonl
worker: (A) C:/g103/t<k>(b1), (B) C:/g103/c<k>(b1c).
"""
import json, os, shutil, sys, threading
from concurrent.futures import ThreadPoolExecutor

R = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile/"
sys.path.insert(0, R)
import b26v4c as VC           # noqa: E402  (H.build_head에 v4c 추가)
import reconcile_run as RR    # noqa: E402
K = RR.K
S = K.S
OUT = RR.OUT
RR.FILES["test_b26pre_trace.py"] = R + "proto_test_b26pre_trace.py"
TRACE = ["test_b26pre_trace.py"]
UNION = RR.CON + RR.PRE + TRACE


def b1c_sources():
    return VC.cleanup(dict(S.BASEF), rr="")


def pool_for(prefix, nw, files_override=None):
    pool = []
    for k in range(nw):
        w = "C:/g103/%s%d" % (prefix, k)
        if not os.path.exists(w):
            shutil.copytree("C:/g103/b1", w)
        if files_override:
            for rel, txt in files_override.items():
                with open(os.path.join(w, *rel.split("/")), "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(txt)
        for dst, src in RR.FILES.items():
            shutil.copyfile(src, os.path.join(w, *(RR.TD + dst).split("/")))
        pool.append(w)
    return pool


def run_jobs(jobs, pool, path, fn):
    lock = threading.Lock()
    done = RR.done_ids(path)

    def one(j):
        if j["id"] in done:
            return
        with lock:
            w = pool.pop()
        fp = os.path.join(w, *j["file"].split("/"))
        orig = S.BASEF[j["file"]]
        try:
            with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(j["src"])
            rec = fn(w, j)
        finally:
            with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(orig)
            with lock:
                pool.append(w)
        rec.update(id=j["id"], b1=j["b1_path"], inv=len(j["inv"]))
        with lock:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(rec.get("result"), j["id"], flush=True)
    with ThreadPoolExecutor(len(pool)) as ex:
        list(ex.map(one, jobs))


def files_run(names):
    def fn(w, j):
        rc, s, failed, _ = RR.run_files(w, names)
        return dict(result="killed" if rc != 0 else "survived", rc=rc, s=s, failed=failed)
    return fn


def existing_run(w, j):
    if not j["inv"]:
        return dict(result="survived", reason="no inventory")
    rc, s, _t = K.run_pytest(w, j["inv"], [])
    return dict(result="killed" if rc != 0 else "survived", rc=rc, s=round(s, 1))


def main():
    what, nw = sys.argv[1], int(sys.argv[2])
    K.OUT = OUT
    if what == "trace_v4":
        ids = set(json.load(open(sys.argv[3], encoding="utf-8")))
        jobs, _ = K.build_jobs("v4", "N2w")
        jobs = [j for j in jobs if j["id"] in ids]
        pool = pool_for("t", min(nw, len(jobs)))
        run_jobs(jobs, pool, OUT + "trace_v4.jsonl", files_run(TRACE))
    else:
        b1c = b1c_sources()
        _head = VC.build_head("v4c")       # head는 b1에서 만든다(정리 포함) -- base 교체 전에 고정
        VC.H.build_head = lambda mode: _head
        S.BASEF = b1c                     # 대응·변이 소스·되돌림 기준 = b1c
        K.S.BASEF = b1c
        jobs, unmapped = K.build_jobs("v4c", "N2w")
        json.dump(unmapped, open(OUT + "unmapped_v4c_N2w.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        ov = {S.SD: b1c[S.SD], S.SR: b1c[S.SR]}
        if what == "v4c_baseline":
            pool = pool_for("c", 1, ov)
            rc, s, failed, tail = RR.run_files(pool[0], UNION)
            print("baseline b1c UNION", rc, s, failed, tail[-300:])
            return
        if what == "v4c_proto":
            print("jobs", len(jobs), "unmapped", len(unmapped), flush=True)
            pool = pool_for("c", nw, ov)
            run_jobs(jobs, pool, OUT + "v4c_proto.jsonl", files_run(UNION))
        elif what == "v4c_existing":
            ids = set(json.load(open(sys.argv[3], encoding="utf-8")))
            jobs = [j for j in jobs if j["id"] in ids]
            pool = pool_for("c", min(nw, len(jobs)), ov)
            run_jobs(jobs, pool, OUT + "v4c_existing.jsonl", existing_run)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
