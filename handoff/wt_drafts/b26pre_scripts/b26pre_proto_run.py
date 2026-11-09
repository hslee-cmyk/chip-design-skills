"""b26pre -- 시제품 test(C:/g87/proto/test_b26pre_proto.py)가 E6·E7 생존 변이를 죽이는지 잰다.

1) 기준: 시제품 test를 b1(HEAD + B34)과 base(HEAD) 사본에서 실행 -> 둘 다 PASS여야 한다.
2) 변이: b26pre_kill이 남긴 kill_v4_N2d.jsonl의 survived 변이마다, b26v4_kill.build_jobs의 같은 b1 변이 소스를
   worker(C:/g87/p<k>, b1 사본 + 시제품)에 써서 시제품 test만 실행한다.
출력: C:/g87/out/proto/proto_kill.jsonl (변이마다 append), proto_baseline.txt
사용: python -B b26pre_proto_run.py <NW> [baseline|mutants|all]
"""
import json, os, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26pre_scripts")
import b26v4_kill as K   # noqa: E402

PY = "C:/Python314/python.exe"
PROTO = os.environ.get("B26PRE_PROTO", "C:/g87/proto/test_b26pre_proto.py")
REL = "skills/analog-gmid-design/assets/tests/contracts/" + os.path.basename(PROTO)
OUT = os.environ.get("B26PRE_OUT", "C:/g87/out/proto/")
E67 = "C:/g87/out/e67/"


def place(root):
    dst = os.path.join(root, *REL.split("/"))
    shutil.copyfile(PROTO, dst)


def run(root, timeout=1500):
    env = dict(os.environ, PYTHONPYCACHEPREFIX=root + "_pyc", PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="1",
               PYTHONIOENCODING="utf-8")
    ini = os.path.join(root, "tools", "gates", "pytest_gate.ini")
    cmd = [PY, "-P", "-m", "pytest", "-c", ini, "--rootdir=" + root, "--confcutdir=" + root, "-q", "-rA", "--color=no",
           "-p", "no:cacheprovider", "--gmid-phase=2", "--gmid-strict=", os.path.join(root, *REL.split("/"))]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=root, capture_output=True, env=env, timeout=timeout)
        return r.returncode, time.time() - t0, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return "timeout", time.time() - t0, ""


def baseline():
    with open(OUT + "proto_baseline.txt", "w", encoding="utf-8") as fh:
        for root in ("C:/g87/b1", "C:/g87/base"):
            place(root)
            rc, dt, txt = run(root)
            fh.write("== %s rc=%s %.0fs\n%s\n" % (root, rc, dt, txt[-6000:]))
            print(root, rc, round(dt), flush=True)


def mutants(nw):
    surv = [json.loads(l) for l in open(E67 + "kill_v4_N2d.jsonl", encoding="utf-8")]
    surv_ids = {r["id"] for r in surv if r["result"] == "survived"}
    K.OUT = E67
    jobs, _ = K.build_jobs("v4", "N2d")
    jobs = [j for j in jobs if j["id"] in surv_ids]
    print("survivor jobs", len(jobs), "of", len(surv_ids), flush=True)
    res_path = OUT + "proto_kill.jsonl"
    done = set()
    if os.path.exists(res_path):
        done = {json.loads(l)["id"] for l in open(res_path, encoding="utf-8")}
    pool = []
    for k in range(nw):
        w = "C:/g87/p%d" % k
        if not os.path.exists(w):
            shutil.copytree("C:/g87/b1", w)
        place(w)
        pool.append(w)
    lock = threading.Lock()

    def one(j):
        if j["id"] in done:
            return
        with lock:
            w = pool.pop()
        fp = os.path.join(w, *j["file"].split("/"))
        orig = open(fp, encoding="utf-8").read()
        try:
            with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(j["src"])
            rc, dt, txt = run(w)
        finally:
            with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(orig)
            with lock:
                pool.append(w)
        failed = [l.split(" ", 1)[1].split(" - ")[0] for l in txt.splitlines() if l.startswith("FAILED ")]
        rec = dict(id=j["id"], b1=j["b1_path"], result="survived" if rc == 0 else "killed", exit=rc, s=round(dt, 1),
                   failed=failed, N2b=j["N2b"], N2w=j["N2w"], N2d=j["N2d"])
        with lock:
            with open(res_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(rec["result"], rec["id"], rec["s"], failed, flush=True)
    with ThreadPoolExecutor(nw) as ex:
        list(ex.map(one, jobs))
    print("DONE", flush=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    nw, what = int(sys.argv[1]), sys.argv[2]
    if what in ("baseline", "all"):
        baseline()
    if what in ("mutants", "all"):
        mutants(nw)
