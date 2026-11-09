"""T-5e 입력 실현성 측정: bin toy(tests/lut/conftest.BinToy) 위 `derived("param_row")`와 ParamTables 격자. 구현물 아님.

실행: PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 C:/Python314/python.exe probe_t5e.py
결과: 같은 폴더 probe_t5e.jsonl(줄마다 append)
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
from gmid_engine.metrics import ParamTables  # noqa: E402
from lut.conftest import BinToy, TOY_SPEC, bin_model_text, new_memo  # noqa: E402

OUT = open(HERE / "probe_t5e.jsonl", "w", encoding="utf-8")


def emit(**row):
    line = json.dumps(row, ensure_ascii=False)
    OUT.write(line + "\n")
    OUT.flush()
    print(line[:300])


for n_vgs in (3, 7, 13):
    tmp = tempfile.mkdtemp(prefix="t5e")
    try:
        lut = BinToy(tmp, bin_model_text(), n_vgs=n_vgs).load(TOY_SPEC)
    except Exception as exc:  # noqa: BLE001 -- 측정: 실패 사유를 남긴다
        emit(n_vgs=n_vgs, load_error=repr(exc)[:200])
        continue
    keys = sorted(lut.slice_map)
    sl = lut.slice_map[keys[0]]
    emit(n_vgs=n_vgs, keys=[list(k) for k in keys], anchor_bin=list(sl.l_bins.anchor_bin), grids=[len(g) for g in sl.grids], vds=[float(x) for x in sl.grids[2]][:4], vs=[float(x) for x in sl.grids[3]][:4], w_m=sl.w_m)
    memo = new_memo(lut)
    kind, w_key = keys[0]
    vds, vsb = float(sl.grids[2][0]), float(sl.grids[3][0])
    for L in (1e-6, 1.25e-6, 1.5e-6, 1.75e-6, 2e-6, 2.5e-6, 3e-6, 3.5e-6, 5e-6):
        try:
            row = derived(memo, "param_row", kind, w_key, L, vds, vsb)
            emit(n_vgs=n_vgs, L=L, row=None if row is None else {"vgs": row[0], "x": row[1], "y": row[2]})
        except Exception as exc:  # noqa: BLE001
            emit(n_vgs=n_vgs, L=L, raised=type(exc).__name__, msg=str(exc)[:160])
    tables = ParamTables(memo, {kind: w_key}, sl.grids)
    emit(n_vgs=n_vgs, shape=tables.shape)
