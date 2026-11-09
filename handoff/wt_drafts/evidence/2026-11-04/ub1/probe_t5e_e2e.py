"""T-5e (iii) 입력 실현성: 앵커 셋 한 bin toy에서 CS 한 소자 gain = x/y 가 어디서 최대이고 구간 안 값이 끝값 이하인지 본다. 구현물 아님.

실행: PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 C:/Python314/python.exe probe_t5e_e2e.py
결과: 같은 폴더 probe_t5e.jsonl에 append
"""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-ub1-nl1-test/skills/analog-gmid-design")
sys.path.insert(0, str(SKILL))
sys.path.insert(0, str(SKILL / "gmid_engine" / "tests"))

from gmid_engine.lut import derived  # noqa: E402
from lut.conftest import BinToy, TOY_SPEC, bin_model_text, new_memo  # noqa: E402

OUT = open(HERE / "probe_t5e.jsonl", "a", encoding="utf-8")
lut = BinToy(tempfile.mkdtemp(prefix="t5e2"), bin_model_text(), L=(1e-6, 1.5e-6, 2e-6)).load(TOY_SPEC)
sl = lut.slice_map[("nmos", 100)]
memo = new_memo(lut)
rows = {}
for L in (1e-6, 1.25e-6, 1.5e-6, 1.625e-6, 1.75e-6, 1.875e-6, 2e-6):
    r = derived(memo, "param_row", "nmos", 100, L, float(sl.grids[2][0]), float(sl.grids[3][0]))
    rows[L] = None if r is None else [a / b for a, b in zip(r[1], r[2])]
line = json.dumps({"case": "e2e_three_anchor_one_bin", "anchor_bin": list(sl.l_bins.anchor_bin), "grids": [list(map(float, g)) for g in sl.grids], "gain_by_L": rows})
OUT.write(line + "\n")
OUT.close()
print(line[:900])
