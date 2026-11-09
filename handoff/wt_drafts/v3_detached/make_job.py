"""make_job.py -- 설정 JSON 하나로 분리 실행 래퍼(.cmd)를 만든다(실행하지 않는다).

쓰기: C:/Python314/python.exe make_job.py <config.json>
  -> <job_dir>/run.cmd, <job_dir>/job.resolved.json 을 쓴다. 이미 있으면 거부(새 job_dir를 쓸 것).

설정 키(전부 Windows 절대 경로, '/' 또는 '\\' 모두 허용 -- '/c/...' MSYS 꼴·상대 경로·'.' 거부):
  job_dir      (필수) run.cmd·wrapper 로그를 둘 디렉터리(없으면 만든다)
  argv         (필수) 실행할 명령 리스트. argv[0] = 실행 파일 절대 경로. 글자 그대로 넘긴다
  stdout       (필수) stdout 그대로 받을 파일(예: 판정 JSON)
  stderr       (필수) stderr 받을 파일
  rc           (선택) exit 코드 파일. 기본 <job_dir>/rc
  pid          (선택) 래퍼 PID 파일.  기본 <job_dir>/pid
  delete_first (선택) 실행 전에 지울 파일 리스트(예: --out). 지우지 못하면 실행하지 않고 rc 97
  env          (필수) 환경 변수 dict. TMP·TEMP는 필수. 값은 .cmd에 리터럴로 적힌다
  cwd          (선택) 래퍼의 작업 디렉터리(WMI CurrentDirectory). 기본 job_dir
  helper_python(선택) PID 기록용 python. 기본 argv[0](python이 아니면 반드시 지정)
  mkdirs       (선택) 실행 전에 만들 디렉터리 리스트(TMP 등)

.cmd 안의 모든 값은 ASCII만 허용한다(코드 페이지 문제 방지 -- 비ASCII면 거부).
"""
from __future__ import annotations

import json
import ntpath
import os
import re
import sys

REQUIRED_ENV = ("TMP", "TEMP")
PATH_ENV_KEYS = ("TMP", "TEMP", "TMPDIR", "PYTHONPYCACHEPREFIX", "APPDATA", "LOCALAPPDATA")


def die(msg: str) -> None:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.write("make_job: " + msg + "\n")
    sys.exit(2)


def winpath(p: str, what: str) -> str:
    if not isinstance(p, str) or not p:
        die("%s: 빈 경로" % what)
    if re.match(r"^/[a-zA-Z]/", p):
        die("%s: MSYS 꼴 경로 금지(C:/... 로): %r" % (what, p))
    q = p.replace("/", "\\")
    if not re.match(r"^[A-Za-z]:\\", q):
        die("%s: 절대 경로(드라이브 문자)만: %r" % (what, p))
    q = ntpath.normpath(q)
    parts = q.split("\\")
    if "." in parts or ".." in parts:
        die("%s: '.'·'..' 금지: %r" % (what, p))
    return q


def ascii_only(s: str, what: str) -> None:
    try:
        s.encode("ascii")
    except UnicodeEncodeError:
        die("%s: 비ASCII 글자 -- .cmd 코드 페이지 문제로 거부: %r" % (what, s))


def batch_escape(s: str) -> str:
    # 배치 파일에서 %는 %%로. 지연 확장은 끈다(setlocal DisableDelayedExpansion) -> ! 그대로.
    return s.replace("%", "%%")


def set_line(k: str, v: str) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k):
        die("env 이름 이상: %r" % k)
    if "\n" in v or "\r" in v or '"' in v:
        die("env %s: 줄바꿈·큰따옴표 금지" % k)
    return 'set "%s=%s"' % (k, batch_escape(v))


def q(p: str) -> str:
    return '"%s"' % p


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        die("쓰기: make_job.py <config.json>")
    with open(argv[0], encoding="utf-8") as fh:
        cfg = json.load(fh)
    job_dir = winpath(cfg.get("job_dir", ""), "job_dir")
    args = cfg.get("argv")
    if not isinstance(args, list) or not args or not all(isinstance(a, str) and a for a in args):
        die("argv: 비지 않은 문자열 리스트여야 한다")
    args = list(args)
    args[0] = winpath(args[0], "argv[0]")
    stdout = winpath(cfg.get("stdout", ""), "stdout")
    stderr = winpath(cfg.get("stderr", ""), "stderr")
    rc = winpath(cfg.get("rc", job_dir + "\\rc"), "rc")
    pid = winpath(cfg.get("pid", job_dir + "\\pid"), "pid")
    cwd = winpath(cfg.get("cwd", job_dir), "cwd")
    helper = winpath(cfg.get("helper_python", args[0]), "helper_python")
    if not ntpath.basename(helper).lower().startswith("python"):
        die("helper_python이 python 실행 파일이 아니다: %r (설정에 helper_python 지정)" % helper)
    delete_first = [winpath(p, "delete_first") for p in cfg.get("delete_first", [])]
    mkdirs = [winpath(p, "mkdirs") for p in cfg.get("mkdirs", [])]
    env = cfg.get("env")
    if not isinstance(env, dict):
        die("env: dict 필수")
    for k in REQUIRED_ENV:
        if k not in env:
            die("env에 %s 필수(도구의 tempfile.mkdtemp 위치)" % k)
    env = dict(env)
    for k in PATH_ENV_KEYS:
        if k in env:
            env[k] = winpath(env[k], "env " + k)
    for k in ("PATH", "PYTHONPATH"):   # ';' 목록 -- 항목마다 절대 경로('/' 허용 -> '\')
        if k in env:
            env[k] = ";".join(winpath(x, "env %s 항목" % k) for x in env[k].split(";") if x)
    # 결과 파일 경로는 서로 달라야 한다
    outs = [stdout, stderr, rc, pid]
    if len({o.lower() for o in outs}) != len(outs):
        die("stdout·stderr·rc·pid 경로가 겹친다")
    for s, what in [(job_dir, "job_dir"), (stdout, "stdout"), (stderr, "stderr"), (rc, "rc"), (pid, "pid"),
                    (cwd, "cwd"), (helper, "helper_python")] + [(a, "argv") for a in args] + \
                   [(v, "env " + k) for k, v in env.items()] + [(d, "delete_first") for d in delete_first] + \
                   [(d, "mkdirs") for d in mkdirs]:
        ascii_only(s, what)

    os.makedirs(job_dir, exist_ok=True)
    cmd_path = job_dir + "\\run.cmd"
    resolved_path = job_dir + "\\job.resolved.json"
    for p in (cmd_path, resolved_path):
        if os.path.exists(p):
            die("이미 있음 -- 새 job_dir를 쓸 것: %s" % p)

    for x in args:
        if '"' in x or "\n" in x or "\r" in x:
            die("argv 항목에 큰따옴표·줄바꿈 금지: %r" % x)
        if "<" in x or ">" in x:
            die("argv에 '<'·'>' -- 템플릿 자리표시자가 남았거나 리다이렉트 글자: %r" % x)

    def arg_quote(x: str) -> str:
        # 공백·cmd 메타문자가 있으면 큰따옴표로 감싼다(따옴표 안에서는 & | ( ) ^ 가 글자 그대로).
        # 감싼 값이 '\'로 끝나면 MS C 런타임 규칙대로 '\'를 두 배로.
        if x and not re.search(r'[\s&|()^,;=]', x):
            return x
        return '"%s"' % (x + "\\" * (len(x) - len(x.rstrip("\\"))))
    cmdline = batch_escape(" ".join(arg_quote(x) for x in args))
    wlog = job_dir + "\\wrapper.log"
    L = []
    a = L.append
    a("@echo off")
    a("rem generated by make_job.py -- do not edit; change the config JSON and regenerate into a new job_dir")
    a("setlocal DisableDelayedExpansion")
    for k, v in env.items():
        a(set_line(k, v))
    # 1) PID를 먼저 적는다(os.getppid() = 이 cmd.exe). 임시 파일 -> move로 원자적 교체
    a('"%s" -I -c "import os,sys;sys.stdout.write(str(os.getppid()))" > %s 2>nul' % (helper, q(pid + ".tmp")))
    a("move /y %s %s >nul" % (q(pid + ".tmp"), q(pid)))
    a(">%s echo start %%DATE%% %%TIME%%" % q(wlog))
    a(">>%s echo cwd %%CD%%" % q(wlog))
    for k in list(env) + (["PATH"] if "PATH" not in env else []):
        a(">>%s set %s" % (q(wlog), k))
    a(">>%s 2>&1 where git python" % q(wlog))
    # 2) 결과 파일 디렉터리·mkdirs
    dirs = []
    for p in [stdout, stderr, rc, pid] + delete_first:
        d = ntpath.dirname(p)
        if d and d.lower() not in {x.lower() for x in dirs}:
            dirs.append(d)
    for d in mkdirs + dirs:
        a('if not exist "%s\\" mkdir "%s"' % (d, d))
    # 3) 이전 결과·--out 지우기. 남아 있으면 실행하지 않는다
    for p in [stdout, stderr] + delete_first:
        a("if exist %s del /f /q %s" % (q(p), q(p)))
        a("if exist %s goto :delfail" % q(p))
    # 4) 실행: stdout -> stdout 파일 그대로, stderr -> stderr 파일
    a(">>%s echo run %%DATE%% %%TIME%%" % q(wlog))
    a("%s 1>%s 2>%s" % (cmdline, q(stdout), q(stderr)))
    a('set "WRAP_RC=%ERRORLEVEL%"')
    a(">>%s echo end %%DATE%% %%TIME%% rc=%%WRAP_RC%%" % q(wlog))
    a(">%s echo %%WRAP_RC%%" % q(rc + ".tmp"))
    a("move /y %s %s >nul" % (q(rc + ".tmp"), q(rc)))
    a("exit /b %WRAP_RC%")
    a(":delfail")
    a(">>%s echo delete_first failed -- not run" % q(wlog))
    a(">%s echo 97" % q(rc + ".tmp"))
    a("move /y %s %s >nul" % (q(rc + ".tmp"), q(rc)))
    a("exit /b 97")
    with open(cmd_path, "w", encoding="ascii", newline="\r\n") as fh:
        fh.write("\n".join(L) + "\n")
    resolved = {"job_dir": job_dir, "cmd": cmd_path, "argv": args, "stdout": stdout, "stderr": stderr,
                "rc": rc, "pid": pid, "cwd": cwd, "helper_python": helper, "delete_first": delete_first,
                "mkdirs": mkdirs, "env": env, "wrapper_log": wlog, "config_source": os.path.abspath(argv[0])}
    with open(resolved_path, "w", encoding="utf-8") as fh:
        json.dump(resolved, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"cmd": cmd_path, "resolved": resolved_path}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
