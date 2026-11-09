# O-200 v2 Q5 실측 -- tol_VDsat 셀값 분포(엔진 lut `tol_vdsat_table`, 읽기 전용; LUT 는 u13_real.real_env = resolve_lut_location sha 대조).
# S_d 헤드룸 행이 Σ tol_VDsat 만큼 정의역을 자르는 크기의 소자 하나 몫과, 같은 셀의 VDSAT 대비 비를 낸다. 결과 tolvdsat_cells.txt.
import os, sys, json, pathlib, math
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
import importlib
R = importlib.import_module("gmid_engine.tests.search.u13_real")
from gmid_engine.lut import tol_vdsat_table
HERE = pathlib.Path(__file__).parent
env = R.real_env()
out = open(HERE / "tolvdsat_cells.txt", "w", encoding="utf-8")
keys = sorted({k for k in env.lut.slice_map})
for kind in ("nmos", "pmos"):
    wk = sorted(w for (k, w) in keys if k == kind)
    for w in wk:
        tb = tol_vdsat_table(env.memo, kind, w)
        vals = [c.vdsat_v for row in tb.cells for c in row if c.vdsat_v is not None]
        vds = list(tb.vds_grid)
        v03 = [c.vdsat_v for row in tb.cells for k_, c in enumerate(row) if c.vdsat_v is not None and vds[k_] >= 0.3 - 1e-12]
        vals.sort(); v03.sort()
        f = lambda v, p: v[min(len(v) - 1, int(p * (len(v) - 1) + 0.5))] if v else None
        line = dict(kind=kind, w_key=w, n=len(vals), q_all_mV=[round(1e3 * f(vals, p), 3) for p in (0, .1, .5, .9, 1)] if vals else None,
                    q_vds_ge_0p3_mV=[round(1e3 * f(v03, p), 3) for p in (0, .1, .5, .9, 1)] if v03 else None)
        out.write(json.dumps(line) + "\n"); out.flush()
        print(line, flush=True)
