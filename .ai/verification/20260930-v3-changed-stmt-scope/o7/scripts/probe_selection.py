"""V3 대상 선택 probe -- 도구 `main`을 실제 경로 그대로 돌리되 pytest를 '항상 통과' 가짜로 바꿔(PYTHONPATH 앞에 가짜 `pytest` 패키지)
모든 실행 변이를 빠르게 '생존'으로 만든 뒤, `--out`의 레코드로 도구가 고른 대상 집합을 기대 id 목록과 대조한다(판정 아님 -- 선택 집합만 본다).

  C:/Python314/python.exe -B probe_selection.py --tool <mutate_changed.py> --root <격리 복제본> --base <커밋> --head <커밋>
        --expect <ids_<label>.json> --key <N2w|N2b|all> --work <scratch 폴더> [--label 이름]

* 가짜 pytest: <work>/fakepytest/pytest/__main__.py = sys.exit(0). 도구는 `python -P -m pytest`로 부르고 환경을 그대로 넘기므로 PYTHONPATH가 이긴다.
  기준 실행도 통과(0)라 BaselineFailed가 나지 않는다. 인벤토리가 빈 def의 변이는 원래대로 '생존(인벤토리 없음)'.
* 대상 = `--out`에서 result가 survived·killed·exempt인 id, 대상 밖 = result가 not_targeted인 id(범위 card 병합본). 지금 도구(base)는 not_targeted가 없다.
* 결과: <work>/probe_<label>.json + 표준 출력 요약. exit 0 = 기대와 같음, 1 = 다름, 2 = 실행 오류.
"""
import argparse, json, os, subprocess, sys


def main(argv):
    ap = argparse.ArgumentParser()
    for k in ("--tool", "--root", "--base", "--head", "--expect", "--work"):
        ap.add_argument(k, required=True)
    ap.add_argument("--key", default="N2w")
    ap.add_argument("--label", default="probe")
    ns = ap.parse_args(argv)
    fake = os.path.join(ns.work, "fakepytest", "pytest")
    os.makedirs(fake, exist_ok=True)
    open(os.path.join(fake, "__init__.py"), "w").close()
    with open(os.path.join(fake, "__main__.py"), "w", encoding="utf-8") as fh:
        fh.write("import sys\nsys.exit(0)\n")
    out = os.path.join(ns.work, "probe_%s.jsonl" % ns.label)
    if os.path.exists(out):
        os.remove(out)
    env = dict(os.environ, PYTHONPATH=os.path.join(ns.work, "fakepytest"))
    r = subprocess.run([sys.executable, "-B", ns.tool, "--root", ns.root, "--base", ns.base, "--head", ns.head,
                        "--pytest-ini", os.path.join(ns.work, "none.ini"), "--out", out], capture_output=True, env=env)
    stdout = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode not in (0, 1) or not os.path.exists(out):
        print("실행 오류 exit %d: %s %s" % (r.returncode, stdout[:500], r.stderr.decode("utf-8", "replace")[:500]))
        return 2
    recs = [json.loads(l) for l in open(out, encoding="utf-8") if l.strip()]
    tg = [x["id"] for x in recs if x["result"] in ("survived", "killed", "exempt")]
    nt = [x["id"] for x in recs if x["result"] == "not_targeted"]
    exp = json.load(open(ns.expect, encoding="utf-8"))["ids"]
    want, allids = set(exp[ns.key]), exp["all"]
    summary = json.loads(stdout.splitlines()[-1])
    res = {"label": ns.label, "tool_exit": r.returncode, "records": len(recs), "targeted": len(tg), "not_targeted": len(nt),
           "expect_targeted": len(want), "missing": sorted(want - set(tg)), "extra": sorted(set(tg) - want),
           "not_targeted_ok": sorted(nt) == sorted(i for i in allids if i not in want) if nt else None,
           "stdout_keys": list(summary.keys()), "stdout_mutants": summary.get("mutants"), "stdout_not_targeted": summary.get("not_targeted"),
           "order_ok": [x["id"] for x in recs] == [i for i in allids if (i in want or nt)]}
    with open(os.path.join(ns.work, "probe_%s.json" % ns.label), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 6 else "%d개" % len(v)) for k, v in res.items()}, ensure_ascii=False))
    return 0 if not res["missing"] and not res["extra"] and res["not_targeted_ok"] in (True, None) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
