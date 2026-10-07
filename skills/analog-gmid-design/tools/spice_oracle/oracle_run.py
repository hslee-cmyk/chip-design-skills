# -*- coding: utf-8 -*-
"""oracle_run.py -- SPICE 오라클 한 번에 돌리기: 넷리스트 생성 -> ngspice(.op/.ac) -> 비교표.

진입점(단독 실행):
    python oracle_run.py <oracle_input.json> <out_dir> --bias free [forced]
                         [--judge judge.json] [--sat-margin-v V] [--ngspice EXE] [--timeout-s S] [--tag TAG]

  bias 마다 <out_dir>/<circuit>[.<tag>].<bias>.{cir, cir.meta.json, log, ac.txt, sim.json, compare.json, compare.md}
  를 쓰고, 끝에 판정 요약을 출력한다. 반환 코드: 0 = 모든 bias 판정 PASS/INCOMPLETE, 1 = FAIL, 2 = BLOCKED
  또는 입력이 스키마 위반(그때는 아무 산출물도 쓰지 않음). 합격 판정은 free 모드만(README "합격 정의").
  ngspice 경로는 --ngspice, 없으면 입력 process.ngspice_exe.

이 파일은 oracle_netlist / oracle_simulate / oracle_compare 의 공개 함수만 부른다.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle_netlist import load_input, validate_input, write_netlists  # noqa: E402
from oracle_simulate import simulate  # noqa: E402
from oracle_compare import compare, merge_judge, to_markdown  # noqa: E402


def run_one(inp, out_dir, bias, judge, exe, timeout_s=None, tag=""):
    stem = f"{inp.get('circuit', 'circuit')}{('.' + tag) if tag else ''}.{bias}"
    cir = os.path.join(out_dir, stem + ".cir")
    meta = write_netlists(inp, bias, cir)
    sim = simulate(cir, meta, exe, timeout_s)
    with open(os.path.join(out_dir, stem + ".sim.json"), "w", encoding="utf-8") as f:
        json.dump(sim, f, ensure_ascii=False, indent=1)
    res = compare(inp, meta, sim, judge)
    res["netlist"] = cir
    with open(os.path.join(out_dir, stem + ".compare.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, stem + ".compare.md"), "w", encoding="utf-8") as f:
        f.write(to_markdown(res))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="SPICE 오라클: 넷리스트 -> ngspice -> 비교표")
    ap.add_argument("oracle_input")
    ap.add_argument("out_dir")
    ap.add_argument("--bias", nargs="+", choices=("free", "forced"), required=True)
    ap.add_argument("--judge", default=None)
    ap.add_argument("--sat-margin-v", type=float, default=None)
    ap.add_argument("--ngspice", default=None)
    ap.add_argument("--timeout-s", type=float, default=None)
    ap.add_argument("--tag", default="")
    a = ap.parse_args(argv)
    inp = load_input(a.oracle_input)
    errs = validate_input(inp)
    if errs:
        print("입력이 oracle_input.schema.json 위반 -- 거부(넷리스트·비교표를 쓰지 않음):")
        for e in errs:
            print("  ", e)
        return 2
    exe = a.ngspice or inp["process"].get("ngspice_exe")
    if not exe:
        print("ngspice 실행 파일 경로 없음(--ngspice 또는 process.ngspice_exe)")
        return 2
    fj = None
    if a.judge:
        with open(a.judge, encoding="utf-8") as f:
            fj = json.load(f)
    judge = merge_judge(inp.get("judge"), fj, a.sat_margin_v)
    os.makedirs(a.out_dir, exist_ok=True)
    worst = 0
    for bias in a.bias:
        res = run_one(inp, a.out_dir, bias, judge, exe, a.timeout_s, a.tag)
        s = res["summary"]
        ac = s.get("spice_ac") or {}
        print(f"[{bias}] verdict={s['verdict']} ({s['verdict_reason']}) gain_db={ac.get('dc_gain_db')} "
              f"ugf_hz={ac.get('ugf_hz')} pm_deg={ac.get('pm_deg')}({ac.get('pm_definition')}) "
              f"rail_I={s.get('rail_current_A')}")
        for w in s.get("warnings") or []:
            print("  WARNING:", w)
        for b in res["blockers"]:
            print("  BLOCKER:", b)
        worst = max(worst, {"PASS": 0, "INCOMPLETE": 0, "FAIL": 1, "BLOCKED": 2}[s["verdict"]])
    return worst


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
