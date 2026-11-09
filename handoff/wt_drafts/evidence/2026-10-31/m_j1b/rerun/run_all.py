import sys, json, pathlib, traceback
sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import probe_engine as P
names = sorted(p.name.replace(".topology.json", "") for p in P.R.LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
out = HERE / "engine_calls.jsonl"
if out.exists(): out.unlink()
for c in names:
    rec = dict(circuit=c)
    try:
        a, b, s = P.run(c)
        rec.update(stageA=a.status, stageB=b.status, calls=P.CALLS[:], searchctx=s is not None)
    except BaseException as e:
        rec.update(error=repr(e)[:500], tb=traceback.format_exc()[-600:], calls=P.CALLS[:])
    with open(out, "a", encoding="utf-8") as fh: fh.write(json.dumps(rec, default=str) + "\n")
    print(c, rec.get("stageA"), rec.get("stageB"), rec.get("error"), len(rec["calls"]), flush=True)
