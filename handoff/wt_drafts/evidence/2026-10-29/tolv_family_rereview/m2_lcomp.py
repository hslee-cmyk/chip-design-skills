"""측정 2: tol_V 셀값이 L 방향(bin 중점 외부 값) 성분에서 오는지 확인 + 봉인점 tol_I/I(노드) 비.
m1_tables.py 의 LUT 적재를 재사용(import). 결과 m2_lcomp.txt."""
import json
import sys
from pathlib import Path

sys.argv = [sys.argv[0]]
HERE = Path(__file__).parent
OUT = HERE / "m2_lcomp.txt"
OUT.write_text("", encoding="utf-8")


def w(s):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(s + "\n")


import importlib.util  # noqa: E402

spec_ = importlib.util.spec_from_file_location("m1", HERE / "m1_tables.py")
# m1 은 import 때 표를 다시 쓰므로 LUT 적재 부분만 쓰기 위해 실행 후 객체를 가져온다
m1 = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(m1)
from gmid_engine.lut import tol_v_table  # noqa: E402

for kind in ("nmos", "pmos"):
    t = tol_v_table(m1.memo, kind, m1.wk[kind])
    w("[%s] l_bins=%r" % (kind, t.l_bins))
    w("[%s] l_loo(anchor)=%r" % (kind, t.l_loo))
    w("[%s] l_loo_bins=%r" % (kind, t.l_loo_bins))
    w("[%s] l_bin_checks=%r" % (kind, t.l_bin_checks))

# 봉인점 tol_I / 노드 전류 (it2c v2 봉인점, 읽기만)
EV = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\evidence\2026-10-22\it2c_spice_frame_v2\engine")
for c in ("two_stage_ota", "folded_cascode", "ngcc_3stage_ff"):
    d = json.loads((EV / (c + ".engine.json")).read_text(encoding="utf-8"))
    dc = d["device_cols"]
    w("== %s  device: ID_uA gm/ID tolV_mV eps=tolV*gm/ID(%%) tolV*gm_uA (tolV*gm)/ID(%%)" % c)
    for m, op in sorted(dc["dc_op"].items()):
        tv = dc["dc_tol_v"][m]
        gm = dc["dc_gm"][m]
        I = op["current"]
        w("  %-4s %8.3f %5.1f %6.2f %6.1f %8.3f %6.1f" % (m, I * 1e6, op["gm_id"], tv * 1e3, 100 * tv * op["gm_id"],
                                                    tv * gm * 1e6, 100 * tv * gm / I if I else float("nan")))
