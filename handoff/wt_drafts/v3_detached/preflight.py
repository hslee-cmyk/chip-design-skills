"""preflight.py -- 분리 실행 전 점검(읽기 전용. 시스템 설정은 바꾸지 않는다 -- 보고만).

쓰기: C:/Python314/python.exe preflight.py <JOB_DIR> [--report <json 파일>]
점검:
  1. 전원: 현재 체계 STANDBYIDLE·HIBERNATEIDLE(AC/DC 초), 덮개 닫기 동작(AC/DC), 지금 AC 전원인지(GetSystemPowerStatus).
     AC 절전 시간이 0이 아니거나 배터리로 돌고 있으면 WARN(절전 중에도 subprocess timeout 시계가 흐르면 거짓 killed 위험).
  2. 동시 pytest/python 프로세스(부하 -> 생존 변이가 --timeout을 넘어 거짓 killed 위험): 목록·수. pytest 있으면 WARN.
  3. job 설정: TMP·TEMP가 절대 경로이고 '.' 아님, argv[0]·helper_python 존재, 래퍼 env PATH로 git·python이 찾아지는지,
     TMP 드라이브 여유 공간, rc·pid·launch.json이 아직 없는지(새 job인지).
exit 0 = WARN/FAIL 없음, 1 = WARN만, 2 = FAIL(띄우지 말 것).
"""
from __future__ import annotations

import ctypes
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUBS = [("SUB_SLEEP", "STANDBYIDLE"), ("SUB_SLEEP", "HIBERNATEIDLE"), ("SUB_BUTTONS", "LIDACTION")]
LID = {0: "do nothing", 1: "sleep", 2: "hibernate", 3: "shut down"}


def powercfg(sub: str, setting: str):
    p = subprocess.run(["powercfg", "/query", "SCHEME_CURRENT", sub, setting], capture_output=True)
    txt = p.stdout.decode("cp949", errors="replace")
    vals = re.findall(r":\s*0x([0-9a-fA-F]{8})\s*$", txt, re.M)
    # 마지막 두 값 = 현재 AC, 현재 DC (앞의 값은 최소·최대·증분)
    if len(vals) < 2:
        return None
    return {"ac": int(vals[-2], 16), "dc": int(vals[-1], 16)}


class SPS(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte),
                ("BatteryLifePercent", ctypes.c_byte), ("SystemStatusFlag", ctypes.c_byte),
                ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("job_dir")
    ap.add_argument("--report", default=None)
    ns = ap.parse_args(argv)
    warn, fail, rep = [], [], {}

    # 1. 전원
    scheme = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True).stdout.decode("cp949", "replace")
    m = re.search(r"([0-9a-f]{8}-[0-9a-f-]{27})", scheme)
    rep["power_scheme"] = m.group(1) if m else scheme.strip()
    for sub, st in SUBS:
        rep[st] = powercfg(sub, st)
    s = SPS()
    ok = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s))
    ac = {0: "battery", 1: "AC", 255: "unknown"}.get(s.ACLineStatus & 0xFF, str(s.ACLineStatus)) if ok else "unknown"
    rep["power_source"] = ac
    sb = rep.get("STANDBYIDLE")
    if sb is None:
        warn.append("STANDBYIDLE 읽기 실패")
    else:
        if sb["ac"] != 0:
            warn.append("AC 절전 대기 %d초 -- 실행 동안 절전되면 거짓 killed 위험(사용자에게 설정 확인 요청)" % sb["ac"])
        if ac != "AC":
            warn.append("지금 전원 = %s, DC 절전 대기 %d초 -- 전원 연결 필요" % (ac, sb["dc"]))
    hb = rep.get("HIBERNATEIDLE")
    if hb and hb["ac"] != 0:
        warn.append("AC 최대 절전 대기 %d초" % hb["ac"])
    lid = rep.get("LIDACTION")
    if lid:
        rep["LIDACTION_text"] = {"ac": LID.get(lid["ac"], lid["ac"]), "dc": LID.get(lid["dc"], lid["dc"])}
        if lid["ac"] != 0:
            warn.append("덮개 닫기(AC) = %s -- 실행 동안 덮개를 닫지 말 것" % rep["LIDACTION_text"]["ac"])

    # 2. 동시 python/pytest
    p = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        os.path.join(HERE, "procs.ps1")], capture_output=True)
    try:
        procs = json.loads(p.stdout.decode("utf-8", "replace") or "[]")
        if isinstance(procs, dict):
            procs = [procs]
    except ValueError:
        procs = []
        warn.append("프로세스 목록 읽기 실패: %r" % p.stderr[:200])
    me = os.getpid()
    procs = [x for x in procs if x.get("pid") != me]
    pyt = [x for x in procs if "pytest" in (x.get("cmd") or "")]
    rep["python_procs"] = len(procs)
    rep["pytest_procs"] = [{"pid": x["pid"], "cmd": (x.get("cmd") or "")[:200]} for x in pyt]
    if pyt:
        warn.append("동시 pytest 프로세스 %d개 -- 부하로 생존 변이가 --timeout을 넘으면 거짓 killed" % len(pyt))

    # 3. job 설정
    with open(os.path.join(ns.job_dir, "job.resolved.json"), encoding="utf-8") as fh:
        job = json.load(fh)
    env = job["env"]
    for k in ("TMP", "TEMP"):
        v = env.get(k, "")
        if not re.match(r"^[A-Za-z]:\\", v) or v.strip(" .\\") in ("", "."):
            fail.append("env %s 이상: %r" % (k, v))
    for k in ("argv0", "helper_python"):
        path = job["argv"][0] if k == "argv0" else job["helper_python"]
        if not os.path.isfile(path):
            fail.append("%s 없음: %s" % (k, path))
    path_env = env.get("PATH")
    if path_env is None:
        warn.append("env에 PATH 없음 -- WMI 프로세스는 사용자 기본 PATH를 받는다(wrapper.log 'where git' 확인)")
    else:
        for exe in ("git", "python"):
            w = shutil.which(exe, path=path_env)
            rep["which_" + exe] = w
            if not w:
                fail.append("래퍼 PATH로 %s를 찾지 못함" % exe)
    tdrive = os.path.splitdrive(env.get("TMP", "C:\\"))[0] + "\\"
    free = shutil.disk_usage(tdrive).free
    rep["tmp_drive_free_gb"] = round(free / 2**30, 1)
    if free < 5 * 2**30:
        warn.append("TMP 드라이브 여유 %.1f GB" % (free / 2**30))
    for k in ("rc", "pid"):
        if os.path.exists(job[k]):
            fail.append("%s 이미 있음(새 job_dir 필요): %s" % (k, job[k]))
    if os.path.exists(os.path.join(ns.job_dir, "launch.json")):
        fail.append("launch.json 이미 있음")
    for d in job.get("delete_first", []):
        rep.setdefault("delete_first_exists", {})[d] = os.path.exists(d)

    rep["warn"], rep["fail"] = warn, fail
    line = json.dumps(rep, ensure_ascii=False)
    if ns.report:
        with open(ns.report, "w", encoding="utf-8") as fh:
            fh.write(line + "\n")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(line)
    return 2 if fail else (1 if warn else 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
