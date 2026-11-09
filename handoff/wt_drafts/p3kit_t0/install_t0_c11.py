"""T0 계약 11(UD-6 W-1) 시제품 설치(측정 전용 -- 역할 산출물 아님, test-author·auditor에게 건네지 않는다(작성자 != 검증자)).

    C:/Python314/python.exe -B install_t0_c11.py <복제본 루트>

spec card 20260930-p3-tests-location-free 계약 11 표대로 unit selftest 3파일의 `from E import (…)` 한 줄에서 7이름을 빼고,
출처 import를 그 줄 바로 앞에 둔다(`# noqa: E402`). DR은 빼기만(13행 `import os`가 이미 있다).
앵커(그 줄이 정확히 하나, 7이름이 그 줄에 있음)가 하나라도 맞지 않으면 exit 1, 아무것도 쓰지 않는다(r2t 2026-10-02 -- 착수 0단계 V4 재측정용 모의 T).
"""
import os
import sys

U = os.path.join(sys.argv[1], "skills", "analog-gmid-design", "assets", "tests", "unit")
PLAN = {
    "test_selftest_topology_library.py": ("topology_library", ["math"], ["import math  # noqa: E402"]),
    "test_selftest_sizing_recipe.py": ("sizing_recipe", ["_dc_replace", "json", "math", "nmcnr_predict_ac_response", "np"],
                                       ["from dataclasses import replace as _dc_replace  # noqa: E402", "import json  # noqa: E402",
                                        "import math  # noqa: E402", "import numpy as np  # noqa: E402",
                                        "from topology_library import nmcnr_predict_ac_response  # noqa: E402"]),
    "test_selftest_design_report.py": ("design_report", ["os"], []),
}
out = {}
for fn, (mod, drop, add) in PLAN.items():
    p = os.path.join(U, fn)
    with open(p, encoding="utf-8", newline="") as fh:
        src = fh.read()
    nl = "\r\n" if "\r\n" in src else "\n"
    lines = src.split(nl)
    idx = [i for i, l in enumerate(lines) if l.startswith("from %s import (" % mod)]
    if len(idx) != 1:
        raise SystemExit("앵커 %s: `from %s import (` 줄 %d개(1개여야 한다)" % (fn, mod, len(idx)))
    i = idx[0]
    line = lines[i]
    if ")" not in line:
        raise SystemExit("앵커 %s: import 줄이 한 줄이 아니다(괄호가 다음 줄로 넘어감) -- 계약 11 표를 다시 잰다" % fn)
    names = [x.strip() for x in line[line.index("(") + 1:line.index(")")].split(",")]
    miss = [d for d in drop if d not in names]
    if miss:
        raise SystemExit("앵커 %s: 7이름 중 %s가 그 줄에 없다 -- 계약 11 표를 다시 잰다(w1_lines.py)" % (fn, miss))
    keep = [x for x in names if x not in drop]
    lines[i] = line[:line.index("(") + 1] + ", ".join(keep) + line[line.index(")"):]
    lines[i:i] = add
    out[p] = nl.join(lines)
for p, t in out.items():
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(t)
print("installed c11", len(out))
