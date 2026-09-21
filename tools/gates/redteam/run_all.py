"""공격 재생 실행기 (05-role-separation §13.2·§13.3·§19).

    $PY tools/gates/redteam/run_all.py --phase 0.5 --mode direct      # 공격 시나리오
    $PY tools/gates/redteam/run_all.py --cases 0.5 --mode direct      # 과거 사례 5건
    $PY tools/gates/redteam/run_all.py --mode installed               # 설치 모드(이 단계에서는 선언만)

케이스마다 %TEMP% 아래 새 디렉터리에서 setup.sh -> run.sh를 돌리고, 단계 기록($WORK/steps.jsonl)을 expect.json과
대조해 결과를 logs/<시각>-<mode>.jsonl에 케이스마다 append한다(WP-11).

판정 값(케이스·단계):
  PASS             기대와 같다
  FAIL             게이트 코드가 돌았고 기대와 다르다
  MISSING          게이트 코드(작성본 파일)가 없어 돌리지 못했다 -- PASS가 아니다
  NOT-IMPLEMENTED  installed 모드 재생이 아직 없다(선언만)
  ERROR            재생 하네스 자체의 오류
  SKIPPED          modes·phase가 이 실행과 맞지 않는다(사유 기록)
  RECORD           판정하지 않고 동작을 로그로 남기는 단계
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EXIT_MISSING, EXIT_NOT_IMPL = 97, 98
DEFAULT_NOT_CONTAINS = ["Traceback (most recent call last)"]
ORDER = ["ERROR", "FAIL", "MISSING", "NOT-IMPLEMENTED", "PASS"]


def find_bash() -> str:
    env = os.environ.get("RT_BASH")
    if env:
        return env
    for c in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe",
              r"C:\msys64\usr\bin\bash.exe"):
        if Path(c).is_file():
            return c
    w = shutil.which("bash")
    if w and "system32" not in w.lower():
        return w
    raise SystemExit("bash를 찾지 못했다(RT_BASH로 지정)")


def discover(select_cases: str | None):
    dirs = []
    if select_cases is None:
        dirs += sorted(p for p in (HERE / "attacks").iterdir() if (p / "expect.json").is_file())
        dirs += [HERE / n for n in ("v3_survivor", "v7_unwired") if (HERE / n / "expect.json").is_file()]
    else:
        dirs += sorted(p for p in (HERE / "cases").iterdir() if (p / "expect.json").is_file())
    return dirs


def exit_ok(spec, code) -> bool:
    if spec is None or spec == "any":
        return True
    if spec == "nonzero":
        return isinstance(code, int) and code != 0
    if isinstance(spec, list):
        return code in spec
    return code == spec


def eval_step(rec: dict, exp: dict | None) -> tuple[str, str]:
    st = rec.get("status")
    if st == "missing":
        return "MISSING", "게이트 코드 없음: " + ", ".join(rec.get("missing", []))
    if st == "error":
        return "ERROR", rec.get("note", "")
    if st == "not-implemented":
        return "NOT-IMPLEMENTED", rec.get("note", "")
    kind = (exp or {}).get("kind") or rec.get("kind")
    if kind == "record":
        return "RECORD", f"exit {rec.get('exit')}"
    if kind == "precondition" and exp is None:
        exp = {"exit": 0}
    if exp is None:
        return "ERROR", "이 단계의 기대가 expect.json에 없다"
    why = []
    if not exit_ok(exp.get("exit"), rec.get("exit")):
        why.append(f"exit {rec.get('exit')} != 기대 {exp.get('exit')}")
    text = (rec.get("stdout") or "") + "\n" + (rec.get("stderr") or "")
    norm = text.replace("\\", "/")
    for s in exp.get("message_contains", []):
        if s not in text and s.replace("\\", "/") not in norm:
            why.append(f"메시지에 {s!r} 없음")
    for s in exp.get("message_not_contains", DEFAULT_NOT_CONTAINS):
        if s in text:
            why.append(f"메시지에 {s!r} 있음")
    if "observed_equals" in exp and rec.get("observed") != exp["observed_equals"]:
        why.append(f"관찰 {rec.get('observed')!r} != 기대 {exp['observed_equals']!r}")
    if why and kind == "precondition":
        return "FAIL", "전제 불충족: " + "; ".join(why) + " | " + rec.get("note", "")
    return ("FAIL", "; ".join(why)) if why else ("PASS", "")


def worst(verdicts):
    vs = [v for v in verdicts if v in ORDER]
    if not vs:
        return "RECORD"
    return min(vs, key=ORDER.index)


def run_case(case_dir: Path, mode: str, repo: Path, runroot: Path, bash: str, keep: bool) -> dict:
    exp = json.loads((case_dir / "expect.json").read_text(encoding="utf-8"))
    name = case_dir.name
    res = {"case": name, "mode": mode, "phase": exp.get("phase", "0.5"), "basis": exp.get("basis", ""),
           "expected": {k: exp.get(k) for k in ("layer", "exit", "message_contains", "modes")}}
    if exp.get("phase", "0.5") != res["phase"] or mode not in exp.get("modes", []):
        res.update(verdict="SKIPPED", reason=exp.get("skip_reason") or f"modes {exp.get('modes')}에 {mode} 없음")
        return res
    if mode == "installed":
        # 설치 모드(부트스트랩 ⑤: 실제 도구 호출·실제 git hook)는 아직 선언만 한다 -- direct 단계를 대신 돌리지 않는다
        res.update(verdict="NOT-IMPLEMENTED", reason="installed 재생 미구현(부트스트랩 ④ 설치 상태 필요) -- 기대는 expect.json에 선언됨")
        return res
    work = Path(tempfile.mkdtemp(prefix=f"{name[:24]}-", dir=runroot))
    env = dict(os.environ)
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(k, None)
    env.update({"PY": sys.executable.replace("\\", "/"), "RT": str(HERE / "lib" / "rt.py").replace("\\", "/"),
                "WORK": str(work), "CASE_DIR": str(case_dir), "RT_REPO": str(repo), "RT_MODE": mode,
                "RT_BASH": bash, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
    t0 = time.time()
    phases = []
    status = "ok"
    for script in ("setup.sh", "run.sh"):
        f = case_dir / script
        if not f.is_file():
            continue
        # core.autocrlf 체크아웃의 CRLF를 bash가 읽지 못하므로 LF로 바꿔 stdin으로 넘긴다(.gitattributes는 판정 환경 파일이라 두지 않는다)
        script_bytes = f.read_bytes().replace(b"\r\n", b"\n")
        r = subprocess.run([bash, "-s"], input=script_bytes, cwd=str(work), env=env, capture_output=True, timeout=3600)
        phases.append({"script": script, "exit": r.returncode,
                       "stderr": r.stderr.decode("utf-8", "replace")[-3000:],
                       "stdout": r.stdout.decode("utf-8", "replace")[-1500:]})
        if r.returncode == EXIT_MISSING:
            status = "missing"
            break
        if r.returncode == EXIT_NOT_IMPL:
            status = "not-implemented"
            break
        if r.returncode != 0:
            status = f"error in {script}"
            break
    steps = []
    sf = work / "steps.jsonl"
    if sf.exists():
        steps = [json.loads(x) for x in sf.read_text(encoding="utf-8").splitlines() if x.strip()]
    exp_steps = exp.get("steps") or {}
    if not exp_steps and not exp.get("steps_from_records"):
        exp_steps = {"attack": {"layer": exp.get("layer"), "exit": exp.get("exit"),
                                "message_contains": exp.get("message_contains", [])}}
    by_name = {}
    for s in steps:
        by_name[s["step"]] = s     # 같은 이름이면 마지막
    out_steps, verdicts, contested = [], [], []
    for sname, rec in by_name.items():
        e = rec.get("expect") if "expect" in rec else exp_steps.get(sname)
        v, why = eval_step(rec, e)
        item = {"step": sname, "kind": (e or {}).get("kind") or rec.get("kind"), "layer": rec.get("layer"),
                "verdict": v, "why": why, "exit": rec.get("exit"), "expect": e, "observed": rec.get("observed"),
                "note": rec.get("note", ""), "cmd": rec.get("cmd"),
                "stderr_tail": (rec.get("stderr") or "")[-800:], "stdout_tail": (rec.get("stdout") or "")[-400:]}
        out_steps.append(item)
        if (e or {}).get("contested"):
            contested.append(item)
        else:
            verdicts.append(v)
    for sname in exp_steps:
        if sname not in by_name:
            v = {"missing": "MISSING", "not-implemented": "NOT-IMPLEMENTED"}.get(status, "ERROR")
            if v == "ERROR" and any(s["status"] == "missing" for s in by_name.values()):
                v = "MISSING"     # 같은 동작의 앞 단계가 게이트 코드 없음으로 멈췄다
            out_steps.append({"step": sname, "verdict": v, "why": f"단계가 실행되지 않음({status})",
                              "expect": exp_steps[sname]})
            verdicts.append(v)
    if status == "missing" and not verdicts:
        verdicts.append("MISSING")
    if status == "not-implemented" and not verdicts:
        verdicts.append("NOT-IMPLEMENTED")
    if status.startswith("error"):
        verdicts.append("ERROR")
    res.update(verdict=worst(verdicts), status=status, seconds=round(time.time() - t0, 1), steps=out_steps,
               contested=[{"step": c["step"], "verdict": c["verdict"], "why": c["why"]} for c in contested],
               scripts=phases, work=str(work) if keep else None)
    if not keep:
        shutil.rmtree(work, ignore_errors=True)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["direct", "installed"], default="direct",
                    help="§19: 공격 재생은 direct와 installed 둘 다, 사례(--cases)는 direct")
    ap.add_argument("--phase", default="0.5", help="공격 시나리오의 실행 Phase(기본 0.5, 12·13·14는 6a)")
    ap.add_argument("--cases", help="과거 사례 재생(§13.3) Phase, 예 0.5")
    ap.add_argument("--only", action="append", help="케이스 디렉터리 이름에 이 문자열이 든 것만")
    ap.add_argument("--repo", help="시험 대상 저장소 루트(기본: 이 redteam이 든 저장소)")
    ap.add_argument("--keep", action="store_true", help="임시 디렉터리를 지우지 않는다")
    ns = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    repo =Path(ns.repo).resolve() if ns.repo else HERE.parents[2]
    bash = find_bash()
    dirs = discover(ns.cases)
    if ns.only:
        dirs = [d for d in dirs if any(o in d.name for o in ns.only)]
    stamp = time.strftime("%Y%m%d-%H%M%S")
    logdir = HERE / "logs"
    logdir.mkdir(exist_ok=True)
    log = logdir / f"{stamp}-{ns.mode}{'-cases' if ns.cases else ''}.jsonl"
    runroot = Path(tempfile.gettempdir()) / "gmid-redteam" / f"{stamp}-{ns.mode}"
    runroot.mkdir(parents=True, exist_ok=True)
    want_phase = ns.cases or ns.phase
    counts, step_counts = {}, {}
    print(f"repo={repo}\nlog={log}\n")
    for d in dirs:
        exp = json.loads((d / "expect.json").read_text(encoding="utf-8"))
        if exp.get("phase", "0.5") != want_phase:
            res = {"case": d.name, "mode": ns.mode, "verdict": "SKIPPED",
                   "reason": exp.get("skip_reason") or f"실행 Phase {exp.get('phase')} != {want_phase}"}
        else:
            try:
                res = run_case(d, ns.mode, repo, runroot, bash, ns.keep)
            except Exception as e:  # 하네스 오류: 그 케이스만 ERROR
                res = {"case": d.name, "mode": ns.mode, "verdict": "ERROR", "reason": f"{type(e).__name__}: {e}"}
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
        counts[res["verdict"]] = counts.get(res["verdict"], 0) + 1
        for s in res.get("steps", []):
            step_counts[s["verdict"]] = step_counts.get(s["verdict"], 0) + 1
        extra = res.get("reason") or ""
        if res.get("contested"):
            extra += f" contested={[(c['step'], c['verdict']) for c in res['contested']]}"
        print(f"{res['verdict']:<16} {d.name:<44} {extra}")
        if res["verdict"] in ("FAIL", "ERROR"):
            for s in res.get("steps", []):
                if s["verdict"] in ("FAIL", "ERROR"):
                    print(f"    - {s['verdict']} {s['step']}: {s['why']}")
            for sc in res.get("scripts", []):
                if sc["exit"] not in (0, EXIT_MISSING, EXIT_NOT_IMPL):
                    print(f"    - {sc['script']} exit {sc['exit']}: {sc['stderr'][-600:]}")
    summary = {"summary": True, "mode": ns.mode, "phase": want_phase, "cases": counts, "steps": step_counts,
               "repo": str(repo), "time": stamp}
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print("\n케이스:", json.dumps(counts, ensure_ascii=False))
    print("단계:", json.dumps(step_counts, ensure_ascii=False))
    if not ns.keep:
        shutil.rmtree(runroot, ignore_errors=True)
    bad = counts.get("FAIL", 0) + counts.get("ERROR", 0) + counts.get("MISSING", 0)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
