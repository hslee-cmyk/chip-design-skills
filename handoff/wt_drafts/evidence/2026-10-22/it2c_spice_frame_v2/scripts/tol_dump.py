"""엔진 LUT 의 tol_VDsat 표(lut.vdsat_tolerance.tol_vdsat_table)를 (kind, w_key, L) 마다 VDS 1 mV 격자에서 읽어 out/tol_tables.json 에 쓴다.
SPICE 점마다의 여유 VDS − VDSAT − tol 을 엔진과 같은 표 값으로 재기 위해서다(상수 발명 없음)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import eng_seal  # noqa: E402  (LUT 를 읽는다)
from gmid_engine.lut.vdsat_tolerance import tol_vdsat_table  # noqa: E402

OUT = eng_seal.OUTDIR
memo = eng_seal.LutMemo(eng_seal.LUT, point=1000, curve=1000, root=64)
keys = set()
for name in sys.argv[1:]:
    eng = json.loads((OUT / (name + ".engine.json")).read_text(encoding="utf-8"))
    for r in eng["rows"]:
        keys.add((r["kind"], r["w_key"], r["L"]))
res = {}
for kind, wk, L in sorted(keys):
    t = tol_vdsat_table(memo, kind, wk)
    vals = []
    for i in range(0, 1801):
        v = i * 1e-3
        try:
            vals.append(t.at(L, v))
        except Exception as exc:  # noqa: BLE001 -- 격자 밖은 None 으로 기록
            vals.append(None)
    res[f"{kind}|{wk}|{L!r}"] = vals
(OUT / "tol_tables.json").write_text(json.dumps(res), encoding="utf-8")
print("tol tables", list(res))
