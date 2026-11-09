"""엔진 LUT 정본 필드 slice_map[(kind, w_key)].w_m 를 봉인점 소자마다 읽어 out_v2/slice_wm.json 에 쓴다(폭 슬라이스 폭을 숫자 곱으로 만들지 않는다)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import eng_seal  # noqa: E402  (엔진 LUT 를 읽는다)

OUT = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_it2c_spice\out_v2")
res = {}
for name in sys.argv[1:]:
    eng = json.loads((eng_seal.OUTDIR / (name + ".engine.json")).read_text(encoding="utf-8"))
    res[name] = {m: {"kind": op["kind"], "w_key": op["w_key"], "w_m": eng_seal.LUT.slice_map[(op["kind"], op["w_key"])].w_m}
                 for m, op in eng["device_cols"]["dc_op"].items()}
(OUT / "slice_wm.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps({n: sorted({(v["kind"], v["w_key"], v["w_m"]) for v in d.values()}) for n, d in res.items()}))
