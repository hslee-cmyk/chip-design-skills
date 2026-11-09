# 검증 42: current_reuse 봉인 9 평가 0회의 원인 판별. library 경로 그대로(inplace) 단계 A·B, find_front(예산 40).
# sizing.seal 모듈 전역의 봉인 단계 블록을 감싸 호출 수·예외 수를 센다(판정·반환은 그대로). 엔진 소스 수정 0.
import os, sys, json, time, traceback, pathlib, tempfile, collections
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
HERE = pathlib.Path(__file__).parent
import importlib
R = importlib.import_module("gmid_engine.tests.search.u13_real")
SEAL = importlib.import_module("gmid_engine.sizing.seal")
SC = importlib.import_module("gmid_engine.sizing.seal_conduction")
from gmid_engine.search import find_front, SearchSettings, open_run
from gmid_engine.pipeline import run_stage_a, run_stage_b
CNT = collections.Counter(); EXC = collections.Counter()
def wrap(name):
    f = getattr(SEAL, name)
    def g(*a, **k):
        CNT[name] += 1
        try: return f(*a, **k)
        except BaseException as e:
            EXC[(name, type(e).__name__)] += 1; raise
    setattr(SEAL, name, g)
FF = importlib.import_module("gmid_engine.search.find_front")
KR = importlib.import_module("gmid_engine.sizing.kernel_run")
INFO = {}
_l0 = FF.layer0_start
def l0(sctx):
    r = _l0(sctx); INFO["layer0"] = dict(start=r.start is not None, stop=r.stop, start_status=r.start_status, kernel_calls=r.kernel_calls, hard_ok=r.hard_ok); return r
FF.layer0_start = l0
_sp = FF.start_points
def sp(*a):
    r = _sp(*a); INFO["n_starts"] = len(r[0]); INFO["start_log"] = repr(r[1])[:500]; return r
FF.start_points = sp
_sd = KR.seal_dc
def sd(*a, **k):
    CNT["seal_dc"] += 1; return _sd(*a, **k)
KR.seal_dc = sd
_j = SC.judge
def judge(kind, rows):
    CNT["seal9_judge"] += 1; CNT["seal9_judge_rows"] += len(rows); return _j(kind, rows)
SC.judge = judge
out_f = open(HERE / "v42_probe_seal_steps.txt", "a", encoding="utf-8")
env = R.real_env()
for c in (sys.argv[1:] or ["current_reuse_telescopic_ota"]):
    CNT.clear(); EXC.clear(); INFO.clear(); t0 = time.time(); rec = dict(circuit=c)
    try:
        out = pathlib.Path(tempfile.mkdtemp(prefix="v42p_", dir=os.environ.get("TEMP") or None))
        donors, counters = open_run()
        a = run_stage_a(R.LIBRARY / (c + ".topology.json"), R.LIBRARY / (c + ".sizing_spec.json"), env.lut, output_dir=out,
                        donors=donors, counters=counters)
        rec["A"] = a.status
        settings = SearchSettings(600.0, R.EVAL_BUDGET, R.RBOX, (("front_budget_s", "u13 test fixture"),), R.CBOX)
        if a.status == "ok":
            b = run_stage_b(a, env.memo, env.pdk, output_dir=out, settings=settings); rec["B"] = b.status
            if b.status == "ok":
                topo = json.loads((R.LIBRARY / (c + ".topology.json")).read_text(encoding="utf-8"))
                case = R._contexts(R._recipe(a, b, topo, settings), dict(donors=a.donors, counters=a.counters))
                front = find_front(case.sctx, ())
                rec["front"] = len(getattr(front, "front", ()) or ())
                for attr in ("stats", "evaluations", "n_evaluated", "failures", "archive", "status", "reason"):
                    if hasattr(front, attr):
                        v = getattr(front, attr); rec["front." + attr] = repr(v)[:600]
    except BaseException as e:
        rec["error"] = repr(e)[:400]; rec["tb"] = traceback.format_exc()[-600:]
    rec.update(info=dict(INFO), calls=dict(CNT), exc={f"{k[0]}:{k[1]}": v for k, v in EXC.items()}, s=round(time.time() - t0, 1))
    s = json.dumps(rec, ensure_ascii=False, default=str); print(s); out_f.write(s + "\n"); out_f.flush()
