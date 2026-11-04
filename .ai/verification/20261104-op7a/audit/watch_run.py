"""자기 자식 프로세스 트리를 돌리며 메모리를 잰다. 여유가 2 GB 아래면 자기 트리만 끝내고 'MEM_STOP'을 남긴다.
usage: watch_run.py <log> <argv...>"""
import psutil, subprocess, sys, time, os, json
log = sys.argv[1]
argv = sys.argv[2:]
env = dict(os.environ); env["OPENBLAS_NUM_THREADS"] = "1"
out = open(log + ".out", "wb")
p = subprocess.Popen(argv, stdout=out, stderr=subprocess.STDOUT, env=env)
pp = psutil.Process(p.pid)
peak = 0; floor = 1e15; t0 = time.time(); stopped = False
while p.poll() is None:
    try:
        procs = [pp] + pp.children(recursive=True)
        rss = sum(x.memory_info().rss for x in procs if x.is_running())
    except psutil.Error:
        rss = 0
    peak = max(peak, rss)
    avail = psutil.virtual_memory().available
    floor = min(floor, avail)
    if avail < 2 * 2**30:
        stopped = True
        for x in reversed(procs):
            try: x.kill()
            except psutil.Error: pass
        break
    time.sleep(0.2)
rc = p.wait()
json.dump({"rc": rc, "peak_gb": peak / 2**30, "floor_avail_gb": floor / 2**30, "seconds": time.time() - t0, "mem_stop": stopped},
          open(log + ".json", "w"), indent=1)
print(open(log + ".json").read())
