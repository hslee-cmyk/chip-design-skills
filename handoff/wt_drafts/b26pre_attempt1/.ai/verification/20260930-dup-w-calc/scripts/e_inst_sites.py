"""E-INST가 W 식 사이트 줄을 몇 번 지나는지 센다(auditor, 순서 3 참고값 -- 시간 측정과 별도 실행).
sys.monitoring LINE 이벤트: sizing_recipe.py의 대상 줄만 세고 나머지 위치는 DISABLE.
사용: python -P e_inst_sites.py <w_sites_base.json> <out.json> <e_inst.py> <e_inst 인자...>"""
import json, runpy, sys
sites_f, out = sys.argv[1], sys.argv[2]
sites = json.load(open(sites_f, encoding="utf-8"))["sites"]
lines = {s["line"]: s["function"] for s in sites}
counts = {ln: 0 for ln in lines}
M = sys.monitoring
TOOL = M.PROFILER_ID
M.use_tool_id(TOOL, "wsites")
DIS = M.DISABLE


def on_line(code, ln):
    if code.co_filename.endswith("sizing_recipe.py") and ln in counts:
        counts[ln] += 1
        return None
    return DIS


M.register_callback(TOOL, M.events.LINE, on_line)
M.set_events(TOOL, M.events.LINE)
sys.argv = sys.argv[3:]
rc = 0
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit as e:
    rc = e.code
finally:
    M.set_events(TOOL, 0)
    json.dump({"rc": rc, "counts": {f"{ln} {lines[ln]}": c for ln, c in sorted(counts.items())}},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
