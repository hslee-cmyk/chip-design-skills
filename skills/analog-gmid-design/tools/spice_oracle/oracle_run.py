# -*- coding: utf-8 -*-
"""oracle_run.py -- SPICE 오라클 한 번에 돌리기: 넷리스트 생성 -> ngspice(.op/.ac) -> 비교표.

진입점(단독 실행):
    python oracle_run.py <oracle_input.json> <out_dir> --bias free [forced] [iso]
                         [--judge judge.json] [--sat-margin-v V] [--ngspice EXE] [--timeout-s S] [--tag TAG]
                         [--topology T] [--require-topology] [--omit N ...] [--short N ...] [--cache-dir D]

  bias 마다 <out_dir>/<circuit>[.<tag>].<bias>.{cir, cir.meta.json, log, ac.txt, sim.json, compare.json, compare.md}
  를 쓰고, 끝에 판정 요약을 출력한다. 반환 코드: 0 = 모든 bias 판정 PASS/INCOMPLETE, 1 = FAIL, 2 = BLOCKED
  또는 입력이 스키마 위반(그때는 아무 산출물도 쓰지 않음). 합격 판정은 free 모드만(README "합격 정의").
  ngspice 경로는 --ngspice, 없으면 입력 process.ngspice_exe.

이 파일은 oracle_netlist / oracle_simulate / oracle_compare 의 공개 함수만 부른다.
[신규] --require-topology = 합격 실행: C15 topology 연결 동일성이 미검증이면 막힘. free 와 forced 를 함께 돌리면
  free 결과에 diagnosis_free(C19, free FAIL 원인 분류)를 붙여 다시 쓴다. --omit/--short = Z1 제거법(C18, 합격 판정 안 함).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle_netlist import BIASES, load_input, resolve_topology_path, validate_input, write_netlists  # noqa: E402
from oracle_simulate import simulate  # noqa: E402
from oracle_noise import noise_measure  # noqa: E402
from oracle_offset_mc import offset_mc_measure  # noqa: E402
from oracle_swing import swing_icmr_measure  # noqa: E402
from oracle_compare import compare, diagnose, merge_judge, to_markdown  # noqa: E402


def _write_compare(out_dir, stem, res):
    with open(os.path.join(out_dir, stem + ".compare.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, stem + ".compare.md"), "w", encoding="utf-8") as f:
        f.write(to_markdown(res))


def run_one(inp, out_dir, bias, judge, exe, timeout_s=None, tag="", topology_path=None, require_topology=False,
            omit=(), short=(), cache_dir=None):
    stem = f"{inp.get('circuit', 'circuit')}{('.' + tag) if tag else ''}.{bias}"
    cir = os.path.join(out_dir, stem + ".cir")
    meta = write_netlists(inp, bias, cir, topology_path, require_topology, omit, short)
    sim = simulate(cir, meta, exe, timeout_s, cache_dir)
    if bias == "free" and not sim.get("skipped"):
        # [신규 U6] 선택 측정(입력 블록이 있을 때만): .noise 대조, 오프셋 Monte-Carlo, 스윙·ICMR .op 스윕 (README "U6")
        for key, fn in (("noise", lambda: noise_measure(inp, cir, meta, exe, timeout_s, cache_dir)),
                        ("offset_mc", lambda: offset_mc_measure(inp, cir, meta, exe, timeout_s, cache_dir)),
                        ("swing_icmr", lambda: swing_icmr_measure(inp, cir, meta, exe, timeout_s, cache_dir,
                                                                  (judge or {}).get("sat_margin_V"),
                                                                  (judge or {}).get("off_current_A")))):
            if inp.get(key):          # 입력에 그 측정 블록이 있을 때만(없으면 sim 에 키를 만들지 않는다)
                sim[key] = fn()
    with open(os.path.join(out_dir, stem + ".sim.json"), "w", encoding="utf-8") as f:
        json.dump(sim, f, ensure_ascii=False, indent=1)
    res = compare(inp, meta, sim, judge)
    res["netlist"] = cir
    res["stem"] = stem
    _write_compare(out_dir, stem, res)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="SPICE 오라클: 넷리스트 -> ngspice -> 비교표")
    ap.add_argument("oracle_input")
    ap.add_argument("out_dir")
    ap.add_argument("--bias", nargs="+", choices=BIASES, required=True)
    ap.add_argument("--judge", default=None)
    ap.add_argument("--sat-margin-v", type=float, default=None)
    ap.add_argument("--ngspice", default=None)
    ap.add_argument("--timeout-s", type=float, default=None)
    ap.add_argument("--tag", default="")
    ap.add_argument("--topology", default=None, help="[신규] C15 대조용 topology JSON(입력 topology.path 보다 우선)")
    ap.add_argument("--require-topology", action="store_true", help="[신규] 합격 실행: topology 미검증이면 막힘")
    ap.add_argument("--omit", nargs="+", default=[], help="[신규] Z1 제거법: 뺄 원소 이름")
    ap.add_argument("--short", nargs="+", default=[], help="[신규] Z1 제거법: 0 V 로 단락할 수동소자 이름")
    ap.add_argument("--cache-dir", default=None, help="[신규] ngspice 실행 캐시 폴더(C21)")
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
    topo = resolve_topology_path(inp, a.oracle_input, a.topology)
    worst = 0
    results = {}
    for bias in a.bias:
        res = run_one(inp, a.out_dir, bias, judge, exe, a.timeout_s, a.tag, topo, a.require_topology,
                      a.omit, a.short, a.cache_dir)
        results[bias] = res
        s = res["summary"]
        ac = s.get("spice_ac") or {}
        print(f"[{bias}] verdict={s['verdict']} ({s['verdict_reason']}) gain_db={ac.get('dc_gain_db')} "
              f"ugf_hz={ac.get('ugf_hz')} pm_deg={ac.get('pm_deg')}({ac.get('pm_definition')}) "
              f"rail_I={s.get('rail_current_A')} topology={s['topology_identity']['status']}")
        if s.get("iso"):
            print(f"  iso(K3): {s['iso']['verdict']} outside={s['iso']['outside_tol']}")
        for w in s.get("warnings") or []:
            print("  WARNING:", w)
        for b in res["blockers"]:
            print("  BLOCKER:", b)
        worst = max(worst, {"PASS": 0, "INCOMPLETE": 0, "FAIL": 1, "BLOCKED": 2}[s["verdict"]])
    if "free" in results:
        fr = results["free"]
        fr["diagnosis_free"] = diagnose(fr, results.get("forced"))
        _write_compare(a.out_dir, fr["stem"], fr)
        print(f"  diagnosis(free): {fr['diagnosis_free']['classification']} -- {fr['diagnosis_free']['reason']}")
    return worst


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
