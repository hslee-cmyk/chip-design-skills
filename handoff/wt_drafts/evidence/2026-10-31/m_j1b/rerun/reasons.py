import sys, json, pathlib
sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import probe_engine as P
for c in ("cnr_ota","erfc_ota","r2r_opamp","ngcc_3stage_ff","rfc_ota"):
    a, b, s = P.run(c)
    rp = json.loads(pathlib.Path(a.report_paths[0]).read_text(encoding="utf-8"))
    def find(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("status","reasons","reason","stop_reason","verdict","errors","review","findings","violations","issues") : print("  ", path+"/"+k, json.dumps(v, ensure_ascii=False)[:500])
                find(v, path+"/"+k)
        elif isinstance(o, list):
            for i, v in enumerate(o[:5]): find(v, path+f"[{i}]")
    print("==", c, a.status, "keys", list(rp.keys())[:15])
    print("  STOP", json.dumps(rp.get("stop_reasons"), ensure_ascii=False)[:700]); print("  REVIEW", json.dumps(rp.get("review_needed"), ensure_ascii=False)[:500])
