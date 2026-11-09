"""B26-1 V3 생존 변이 통합 재측정(B26pre card 시제품 + B26-1 계약 근사의 합집합).

대상 = v4 모의 head의 승인 범위 규칙(N2(b)+넓힌 T6 = N2w) 변이 중 b1(HEAD a796468 + B34)에 대응이 있는 것(b26v4_kill.build_jobs).
worker C:/g103/w<k> = b1 사본 + 시제품 test 3파일(tests/contracts/ 아래):
  CON = test_b26x_approx.py(B26-1 계약 7(e)·4·14·7(a)·7(c) 근사) + test_b26x_metric_approx.py('V3 계획' 4 근사)
  PRE = test_b26pre_card.py(B26pre card 계약 1~8 시제품)
단계:
  baseline          -- 변이 없는 b1 worker에서 CON·PRE 실행(모두 PASS여야 함)
  proto             -- 변이마다 CON, PRE 각각 실행(-x 없음, 실패 test 이름 기록) -> out/proto.jsonl
  existing <ids.json> -- 지정 변이만 기존 인벤토리 실행(-x) -> out/existing.jsonl
결과는 변이마다 append(중간에 죽어도 남는다).
"""
import json, os, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

R = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile/"
sys.path.insert(0, R)
import b26v4_kill as K   # noqa: E402

PY = "C:/Python314/python.exe"
OUT = "C:/g103/out/"
TD = "skills/analog-gmid-design/assets/tests/contracts/"
FILES = {"test_b26x_approx.py": R + "test_b26x_approx.py",
         "test_b26x_metric_approx.py": R + "test_b26x_metric_approx.py",
         "test_b26pre_card.py": R + "proto_test_b26pre_card.py"}
CON = ["test_b26x_approx.py", "test_b26x_metric_approx.py"]
PRE = ["test_b26pre_card.py"]


def workers(nw):
    pool = []
    for k in range(nw):
        w = "C:/g103/w%d" % k
        if not os.path.exists(w):
            shutil.copytree("C:/g103/b1", w)
        for dst, src in FILES.items():
            shutil.copyfile(src, os.path.join(w, *(TD + dst).split("/")))
        pool.append(w)
    return pool


def run_files(w, names, timeout=1500):
    env = dict(os.environ, PYTHONPYCACHEPREFIX=w + "_pyc", PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="1",
               PYTHONIOENCODING="utf-8")
    ini = os.path.join(w, "tools", "gates", "pytest_gate.ini")
    cmd = [PY, "-P", "-m", "pytest", "-c", ini, "--rootdir=" + w, "--confcutdir=" + w, "-q", "-rf", "--color=no",
           "-p", "no:cacheprovider", "--gmid-phase=2", "--gmid-strict="] + [os.path.join(w, *(TD + n).split("/")) for n in names]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=w, capture_output=True, env=env, timeout=timeout)
        txt = r.stdout.decode("utf-8", "replace")
        failed = [l.split(" ", 1)[1].split(" - ")[0].split("::")[-1] for l in txt.splitlines() if l.startswith("FAILED ")]
        return r.returncode, round(time.time() - t0, 1), failed, txt[-800:]
    except subprocess.TimeoutExpired:
        return "timeout", round(time.time() - t0, 1), [], ""


def jobs_all():
    K.OUT = OUT
    jobs, unmapped = K.build_jobs("v4", "N2w")
    json.dump(unmapped, open(OUT + "unmapped_N2w.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return jobs


def mutate_and(pool, lock, j, fn):
    with lock:
        w = pool.pop()
    fp = os.path.join(w, *j["file"].split("/"))
    orig = K.S.BASEF[j["file"]]
    try:
        with open(fp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(j["src"])
        return fn(w)
    finally:
        with open(fp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(orig)
        with lock:
            pool.append(w)


def done_ids(path):
    if not os.path.exists(path):
        return set()
    return {json.loads(l)["id"] for l in open(path, encoding="utf-8")}


def main():
    what, nw = sys.argv[1], int(sys.argv[2])
    pool = workers(nw)
    lock = threading.Lock()
    if what == "baseline":
        with open(OUT + "baseline.txt", "w", encoding="utf-8") as fh:
            for names in (CON, PRE):
                rc, s, failed, tail = run_files(pool[0], names)
                fh.write("%s rc=%s %ss failed=%s\n%s\n" % (names, rc, s, failed, tail))
                print(names, rc, s, failed, flush=True)
        return
    jobs = jobs_all()
    print("jobs", len(jobs), flush=True)
    if what == "proto":
        path = OUT + "proto.jsonl"
        done = done_ids(path)

        def one(j):
            if j["id"] in done:
                return

            def f(w):
                a = run_files(w, CON)
                b = run_files(w, PRE)
                return a, b
            (ca, cs, cf, _), (pa, ps, pf, _) = mutate_and(pool, lock, j, f)
            rec = dict(id=j["id"], b1=j["b1_path"], con=("killed" if ca != 0 else "survived"), con_rc=ca, con_failed=cf, con_s=cs,
                       pre=("killed" if pa != 0 else "survived"), pre_rc=pa, pre_failed=pf, pre_s=ps,
                       N2b=j["N2b"], N2w=j["N2w"], N2d=j["N2d"], inv=len(j["inv"]))
            with lock:
                with open(path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(rec["con"], rec["pre"], rec["id"], flush=True)
        with ThreadPoolExecutor(nw) as ex:
            list(ex.map(one, jobs))
    elif what == "existing":
        ids = set(json.load(open(sys.argv[3], encoding="utf-8")))
        path = OUT + "existing.jsonl"
        done = done_ids(path)
        sel = [j for j in jobs if j["id"] in ids]
        print("existing jobs", len(sel), flush=True)

        def one(j):
            if j["id"] in done:
                return
            if not j["inv"]:
                rec = dict(id=j["id"], result="survived", reason="no inventory", inv=0)
            else:
                rc, s, _t = mutate_and(pool, lock, j, lambda w: K.run_pytest(w, j["inv"], []))
                rec = dict(id=j["id"], result="survived" if rc == 0 else "killed", exit=rc, s=round(s, 1), inv=len(j["inv"]))
            with lock:
                with open(path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(rec["result"], rec["id"], rec.get("s"), flush=True)
        with ThreadPoolExecutor(nw) as ex:
            list(ex.map(one, sel))
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
