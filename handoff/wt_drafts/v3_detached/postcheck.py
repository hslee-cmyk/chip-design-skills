"""postcheck.py -- 분리 실행이 끝난 뒤 결과 파일 점검(판정 아님 -- 판정은 도구 JSON 그 자체와 carry check).

쓰기: C:/Python314/python.exe postcheck.py <JOB_DIR> [--out <--out jsonl>] [--report <json 파일>]
  - rc 파일: 있음, 정수
  - stdout 파일(판정 JSON): 정확히 한 줄, JSON 객체, 'verdict' 키
  - --out 이 주어지면(V3): 레코드 수·결과별 수, id 중복, '"exit": "timeout"' killed 레코드 id 목록(따로 재현할 것),
    판정 JSON과의 대조(mutants = not_targeted 밖 레코드 수, not_targeted, killed, survivors 집합)
exit 0 = 모든 점검 OK, 1 = 점검 실패(목록은 'problems'), 2 = 사용법.
결과 JSON은 stdout 한 줄 + --report 파일(주면).
"""
from __future__ import annotations

import collections
import json
import os
import sys


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("job_dir")
    ap.add_argument("--out", default=None)
    ap.add_argument("--report", default=None)
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    with open(os.path.join(ns.job_dir, "job.resolved.json"), encoding="utf-8") as fh:
        job = json.load(fh)
    problems, rep = [], {"job_dir": ns.job_dir}

    # rc
    rc = None
    if not os.path.isfile(job["rc"]):
        problems.append("rc 파일 없음: %s" % job["rc"])
    else:
        raw = open(job["rc"], encoding="ascii", errors="replace").read().strip()
        try:
            rc = int(raw)
        except ValueError:
            problems.append("rc 파일이 정수가 아님: %r" % raw)
    rep["rc"] = rc
    if rc == 97:
        problems.append("rc 97 = 래퍼가 delete_first를 지우지 못해 실행하지 않음(wrapper.log)")

    # 판정 JSON
    verdict = None
    if not os.path.isfile(job["stdout"]):
        problems.append("stdout 파일 없음: %s" % job["stdout"])
    else:
        data = open(job["stdout"], "rb").read()
        rep["stdout_bytes"] = len(data)
        text = data.decode("utf-8", errors="strict")
        lines = text.splitlines()
        rep["stdout_lines"] = len(lines)
        if len(lines) != 1:
            problems.append("stdout가 한 줄이 아님(%d줄)" % len(lines))
        if lines:
            try:
                verdict = json.loads(lines[0])
            except ValueError as e:
                problems.append("stdout 첫 줄 JSON 아님: %s" % e)
        if verdict is not None:
            if not isinstance(verdict, dict) or "verdict" not in verdict:
                problems.append("판정 JSON에 'verdict' 키 없음")
                verdict = verdict if isinstance(verdict, dict) else None
            else:
                rep["verdict"] = verdict["verdict"]
                for k in ("tool", "mutants", "killed", "not_targeted", "survivors", "survivor_bindings",
                          "exempt_ignored", "error"):
                    if k in verdict:
                        rep[k] = verdict[k]
    if os.path.isfile(job["stderr"]):
        rep["stderr_bytes"] = os.path.getsize(job["stderr"])

    # --out (V3 변이 레코드)
    if ns.out:
        if not os.path.isfile(ns.out):
            problems.append("--out 파일 없음: %s" % ns.out)
        else:
            recs, bad = [], 0
            with open(ns.out, encoding="utf-8") as fh:
                for i, ln in enumerate(fh, 1):
                    if not ln.strip():
                        continue
                    try:
                        recs.append(json.loads(ln))
                    except ValueError:
                        bad += 1
            if bad:
                problems.append("--out에 JSON 아닌 줄 %d개" % bad)
            ids = [r.get("id") for r in recs]
            dup = sorted(k for k, n in collections.Counter(ids).items() if n > 1)
            by = collections.Counter(r.get("result") for r in recs)
            timeouts = [r.get("id") for r in recs if r.get("result") == "killed" and r.get("exit") == "timeout"]
            rep["out_records"] = len(recs)
            rep["out_by_result"] = dict(by)
            rep["out_duplicate_ids"] = dup
            rep["timeout_killed_ids"] = timeouts
            rep["timeout_killed_n"] = len(timeouts)
            if dup:
                problems.append("--out id 중복 %d개(이어 붙인 흔적?)" % len(dup))
            if verdict and verdict.get("tool") == "V3" and verdict.get("verdict") in ("PASS", "FAIL"):
                run = [r for r in recs if r.get("result") != "not_targeted"]
                if verdict.get("mutants") != len(run):
                    problems.append("mutants %s != --out 실행 레코드 %d" % (verdict.get("mutants"), len(run)))
                if verdict.get("not_targeted") != by.get("not_targeted", 0):
                    problems.append("not_targeted %s != --out %d" % (verdict.get("not_targeted"), by.get("not_targeted", 0)))
                if verdict.get("killed") != by.get("killed", 0):
                    problems.append("killed %s != --out %d" % (verdict.get("killed"), by.get("killed", 0)))
                surv_out = sorted(r.get("id") for r in recs if r.get("result") == "survived")
                if sorted(verdict.get("survivors", [])) != surv_out:
                    problems.append("survivors 집합이 --out survived 레코드와 다름")
                tbd = verdict.get("targets_by_def") or {}
                st = sum(v.get("targeted", 0) for v in tbd.values())
                sn = sum(v.get("not_targeted", 0) for v in tbd.values())
                rep["targets_by_def_sum"] = {"targeted": st, "not_targeted": sn}
                if (st, sn) != (verdict.get("mutants"), verdict.get("not_targeted")):
                    problems.append("targets_by_def 합 (%d,%d) != (mutants, not_targeted)" % (st, sn))
    rep["problems"] = problems
    rep["ok"] = not problems
    line = json.dumps(rep, ensure_ascii=False)
    if ns.report:
        with open(ns.report, "w", encoding="utf-8") as fh:
            fh.write(line + "\n")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(line)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
