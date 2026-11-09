"""Sequential full-test runner: one pytest process per test file (memory bound). Reusable by every card verdict.

usage:
  python -P run_by_file.py --cwd <clone> --out <output dir> [--tests <relative tests root>]
         [--first <relpath or relpath prefix> ...] [--only-file <text file of relative paths>]
         [--wait-mb 3072] [--abort-mb 1536] [--no-slow]

Behaviour
- Before each file: waits until free memory >= --wait-mb (re-measures every 30 s, indefinitely).
- While a file runs: free memory < --abort-mb kills that process tree, records status "aborted_memory", moves on.
- Appends one JSON line per run to <out>/results.jsonl, written as soon as the file ends.
- On restart: files whose latest record is status "done" are skipped; aborted files are tried again.
- status "done" means pytest exited by itself. Test outcome is in rc/failed_ids. An aborted file has no outcome and
  counts as unmeasured.
- Exit code 0 only when every file is "done".
"""
import argparse
import ctypes
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PY = r"C:\Python314\python.exe"
DEFAULT_TESTS = "skills/analog-gmid-design/gmid_engine/tests"


class _MemoryStatus(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                ("avail", ctypes.c_ulonglong), ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                ("avail_extended", ctypes.c_ulonglong)]


def free_mb():
    status = _MemoryStatus()
    status.length = ctypes.sizeof(_MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx failed")
    return status.avail / 1048576


def read_junit(path):
    """Returns the counts and non-passing test ids. A missing or broken file returns None (never read as a pass)."""
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return None
    suites = [root] if root.tag == "testsuite" else list(root)
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    failed, errored = [], []
    for suite in suites:
        for key in counts:
            counts[key] += int(suite.get(key, 0))
        for case in suite.iter("testcase"):
            test_id = "%s::%s" % (case.get("classname"), case.get("name"))
            if case.find("failure") is not None:
                failed.append(test_id)
            if case.find("error") is not None:
                errored.append(test_id)
    return dict(counts, failed_ids=failed, error_ids=errored)


def discover(cwd, tests_root, first, only_file):
    root = cwd / tests_root
    if not root.is_dir():
        raise SystemExit("tests root not found: %s" % root)
    files = sorted(p.relative_to(cwd).as_posix() for p in root.rglob("test_*.py")
                   if "fixtures" not in p.relative_to(root).parts)
    if only_file:
        wanted = [line.strip() for line in Path(only_file).read_text(encoding="utf-8").splitlines() if line.strip()]
        unknown = sorted(set(wanted) - set(files))
        if unknown:
            raise SystemExit("--only-file lists files that do not exist: %s" % unknown)
        files = [f for f in files if f in set(wanted)]
    head = []
    for prefix in first:
        matched = [f for f in files if f == prefix or f.startswith(prefix.rstrip("/") + "/") and f not in head]
        if not matched:
            raise SystemExit("--first matches no file: %s" % prefix)
        head += [f for f in matched if f not in head]
    return head + [f for f in files if f not in head]


def finished_files(results):
    latest = {}
    if results.exists():
        for line in results.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                latest[record["file"]] = record["status"]
    return {f for f, status in latest.items() if status == "done"}


def run_one(cwd, out, rel, args, env):
    tag = re.sub(r"[^A-Za-z0-9_.-]", "_", rel[len(args.tests):].strip("/"))
    junit, log_path = out / (tag + ".xml"), out / (tag + ".log")
    junit.unlink(missing_ok=True)
    cmd = [PY, "-P", "-m", "pytest", rel, "-q", "-rfE", "--tb=short", "--junitxml=" + str(junit), "-p", "no:cacheprovider"]
    if not args.no_slow:
        cmd.append("--run-slow")
    start, low, aborted = time.time(), float("inf"), False
    with open(log_path, "wb") as log:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        while proc.poll() is None:
            now = free_mb()
            low = min(low, now)
            if now < args.abort_mb:
                aborted = True
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
                break
            time.sleep(2)
        rc = proc.wait()
    record = {"file": rel, "status": "aborted_memory" if aborted else "done", "rc": rc,
              "sec": round(time.time() - start), "min_free_mb": None if low == float("inf") else round(low)}
    if not aborted:
        summary = read_junit(junit)
        if summary is None:
            # pytest ended without a readable report: unknown outcome, so it may not count as passed.
            record["status"] = "no_report"
        else:
            record.update(summary)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--tests", default=DEFAULT_TESTS)
    parser.add_argument("--first", nargs="*", default=[])
    parser.add_argument("--only-file")
    parser.add_argument("--wait-mb", type=float, default=3072)
    parser.add_argument("--abort-mb", type=float, default=1536)
    parser.add_argument("--no-slow", action="store_true")
    args = parser.parse_args()
    args.tests = args.tests.strip("/")
    cwd, out = Path(args.cwd).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONPYCACHEPREFIX=str(out / "pyc"))
    results = out / "results.jsonl"
    files = discover(cwd, args.tests, args.first, args.only_file)
    done = finished_files(results)
    pending = [f for f in files if f not in done]
    print("files %d, already done %d, to run %d" % (len(files), len(files) - len(pending), len(pending)), flush=True)
    for rel in pending:
        while free_mb() < args.wait_mb:
            time.sleep(30)
        record = run_one(cwd, out, rel, args, env)
        with open(results, "a", encoding="utf-8") as sink:
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
    remaining = [f for f in files if f not in finished_files(results)]
    print("not done: %d" % len(remaining), flush=True)
    return 0 if not remaining else 1


if __name__ == "__main__":
    sys.exit(main())
