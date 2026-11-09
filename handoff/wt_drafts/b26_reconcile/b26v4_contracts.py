"""B26-1 v4 -- 기존 인벤토리에서 산 변이(kill_v4_N2d.jsonl)를 추가 계약 근사(test_b26x_approx.py)로 다시 실행.
같은 b1 대응·같은 pytest 인자. 출력: C:/g103/out/contracts_v4.jsonl (변이마다 append)
사용: python -B b26v4_contracts.py <NW>
"""
import json, os, shutil, sys, threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile")
import b26v4_kill as K   # noqa: E402

TEST_SRC = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile/test_b26x_approx.py"
REL = "skills/analog-gmid-design/assets/tests/contracts/test_b26x_approx.py"


def main(nw):
    surv = {}
    for l in open(K.OUT + "kill_v4_N2d.jsonl", encoding="utf-8"):
        r = json.loads(l)
        if r["result"] == "survived":
            surv[r["id"]] = r
    jobs, _ = K.build_jobs("v4", "N2d")
    jobs = [j for j in jobs if j["id"] in surv]
    out = K.OUT + "contracts_v4.jsonl"
    done = set()
    if os.path.exists(out):
        done = {json.loads(l)["id"] for l in open(out, encoding="utf-8")}
    pool = []
    for k in range(nw):
        w = "C:/g103/w%d" % k
        shutil.copyfile(TEST_SRC, os.path.join(w, *REL.split("/")))
        pool.append(w)
    lock = threading.Lock()
    node = REL

    # 기준: 변이 없는 b1에서 통과해야 한다
    rc, dt, tail = K.run_pytest(pool[0], [], [os.path.join(pool[0], *REL.split("/"))])
    print("baseline", rc, round(dt, 1), tail[-200:], flush=True)
    if rc != 0:
        return

    def one(j):
        if j["id"] in done:
            return
        with lock:
            w = pool.pop()
        fp = os.path.join(w, *j["file"].split("/"))
        try:
            with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(j["src"])
            rc, dt, tail = K.run_pytest(w, [], [os.path.join(w, *node.split("/"))])
        finally:
            with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(K.S.BASEF[j["file"]])
            with lock:
                pool.append(w)
        failed = [l.split(" ")[1] for l in tail.splitlines() if l.startswith("FAILED ")]
        rec = dict(id=j["id"], result="survived" if rc == 0 else "killed", exit=rc, s=round(dt, 1), failed=failed,
                   b1=j["b1_path"], N2b=j["N2b"], N2w=j["N2w"], N2d=j["N2d"])
        with lock:
            with open(out, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(rec["result"], rec["id"], failed, flush=True)
    with ThreadPoolExecutor(nw) as ex:
        list(ex.map(one, jobs))
    print("DONE", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]))
