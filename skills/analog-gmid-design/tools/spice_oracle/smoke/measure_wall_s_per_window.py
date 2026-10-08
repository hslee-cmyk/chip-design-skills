# -*- coding: utf-8 -*-
"""measure_wall_s_per_window.py -- oracle_config.json stability_transient 의 근거 측정 (조기 종결 계약 1(c), 기록 -- test 아님).

사용:
    python measure_wall_s_per_window.py <out.json> --ngspice EXE --repeat N NAME=<path/to/xxx.stab.cir> [NAME=<...stab2.cir> ...]

오라클이 쓴 폐루프 과도 넷리스트(`.stab.cir`)를 ngspice -b 로 N 번 다시 돌려(캐시 없음) 실행 시간과 끝낸 창 수(로그의 `STABWIN j` 줄 수)를 잰다.
  창당 비용 c = 실행 시간 / 끝낸 창 수 (조기 종결이면 그 창 수).
  케이스별 중앙값 c_med, 최댓값 c_max, 부하 변동비 max/median.
유도(설정 값):
  c_worst         = 케이스들의 c_med 중 최댓값(창당 실측 최대치)
  safety_factor   = 케이스들의 (같은 케이스 반복 실행의 max / median) 중 최댓값, 1 미만이면 1  -- 측정된 부하 변동폭을 그대로 덮는 값
  wall_s_per_window = safety_factor × c_worst
결과 JSON 에 케이스별 반복 측정치를 모두 남긴다(oracle_config.json 의 measured_* 근거).
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time


def run_case(exe, cir, repeat):
    d = os.path.dirname(os.path.abspath(cir))
    runs = []
    for _ in range(repeat):
        t0 = time.monotonic()
        p = subprocess.run([exe, "-b", os.path.basename(cir)], cwd=d, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        dt = time.monotonic() - t0
        n = len(re.findall(r"^STABWIN\s+\d+\s", p.stdout, re.M))
        runs.append({"wall_s": dt, "windows": n, "c_s_per_window": (dt / n) if n else None})
    cs = [r["c_s_per_window"] for r in runs if r["c_s_per_window"]]
    out = {"cir": cir, "runs": runs}
    if cs:
        med = statistics.median(cs)
        out.update(c_med=med, c_max=max(cs), max_over_median=max(cs) / med)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_json")
    ap.add_argument("--ngspice", required=True)
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("cases", nargs="+", help="NAME=<.stab.cir 경로>")
    a = ap.parse_args(argv)
    res = {"repeat": a.repeat, "cases": {}}
    for c in a.cases:
        name, path = c.split("=", 1)
        res["cases"][name] = run_case(a.ngspice, path, a.repeat)
        with open(a.out_json, "w", encoding="utf-8") as f:       # 케이스마다 저장(중간에 죽어도 건진다)
            json.dump(res, f, ensure_ascii=False, indent=1)
    ok = [v for v in res["cases"].values() if "c_med" in v]
    if ok:
        res["c_worst_s_per_window"] = max(v["c_med"] for v in ok)
        res["safety_factor"] = max(1.0, max(v["max_over_median"] for v in ok))
        res["wall_s_per_window"] = res["c_worst_s_per_window"] * res["safety_factor"]
    with open(a.out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: res.get(k) for k in ("c_worst_s_per_window", "safety_factor", "wall_s_per_window")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
