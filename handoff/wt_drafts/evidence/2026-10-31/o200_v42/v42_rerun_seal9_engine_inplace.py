# O-200 v2 보강 -- 하네스 결함(u13_real.real_case 가 topology·sizing_spec 만 임시 폴더로 복사해 형제 파일 누락,
# stageA_regression/report.md) 을 피해 library 경로 그대로(inplace) 단계 A·B 를 돌리고, 같은 조건(find_front, 예산 40 -- u13 설정)으로
# 봉인 9 판정 변화(옛 정의 -> P4·P5)를 잰다. 대상 기본 = current_reuse_telescopic_ota, nmcnr_amplifier, two_stage_ota_sf.
# 읽기·실행만: 엔진 소스 수정 0, 저장소 쓰기 0 (단계 A/B 출력 = TEMP, 탐색 archive = None, PYTHONDONTWRITEBYTECODE).
# 단계 A/B 뒤 컨텍스트 생성은 u13_real 의 _recipe·_contexts(같은 설정·같은 경로)를 그대로 쓴다 -- 다른 점은 단계 A 입력 경로뿐.
# 산출: seal9_rows_inplace.jsonl, seal9_circuits_inplace.jsonl (행·회로마다 Python append). 행 형식은 run_seal9_engine.py 와 같다.
import os, sys, json, time, traceback, pathlib, tempfile
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
HERE = pathlib.Path(__file__).parent
import importlib
R = importlib.import_module("gmid_engine.tests.search.u13_real")
SC = importlib.import_module("gmid_engine.sizing.seal_conduction")
from gmid_engine.search import find_front, SearchSettings, open_run
from gmid_engine.pipeline import run_stage_a, run_stage_b

STATE = dict(circuit=None, n_eval=0, pending=[])
ROWS = open(HERE / "seal9_rows_inplace.jsonl", "a", encoding="utf-8")
CIRC = open(HERE / "seal9_circuits_inplace.jsonl", "a", encoding="utf-8")
_orig_off = SC._off_current
_orig_judge = SC.judge


def _off(lut, device, op):
    v = _orig_off(lut, device, op)
    STATE["pending"].append((device, op, v))
    return v


def _judge(kind, rows):
    if kind == SC.SEAL_CONDUCTION:
        STATE["n_eval"] += 1
        ops = {d: op for d, op, _ in STATE["pending"]}
        STATE["pending"] = []
        for r in rows:
            m, off, epsid = r[0], r[1], r[2]
            op = ops.get(m)
            rec = dict(circuit=STATE["circuit"], ev=STATE["n_eval"], device=m, I_off=off, epsID=epsid)
            if op is not None:
                ID = float(op.current); gid = float(op.gm_id)
                rec.update({f: getattr(op, f) for f in ("kind", "w_key", "L", "W", "vgs", "vds", "vsb") if hasattr(op, f)})
                rec.update(ID=ID, gm_id=gid, tol_V=(None if epsid is None else epsid / (gid * ID)))
            ROWS.write(json.dumps(rec, default=float) + "\n")
        ROWS.flush()
    return _orig_judge(kind, rows)


SC._off_current = _off
SC.judge = _judge

names = sys.argv[1:] or ["current_reuse_telescopic_ota", "nmcnr_amplifier", "two_stage_ota_sf"]
env = R.real_env()
for c in names:
    STATE.update(circuit=c, n_eval=0, pending=[])
    t0 = time.time()
    rec = dict(circuit=c, mode="inplace")
    try:
        out = pathlib.Path(tempfile.mkdtemp(prefix="o200inp_", dir=os.environ.get("TEMP") or None))
        donors, counters = open_run()
        a = run_stage_a(R.LIBRARY / (c + ".topology.json"), R.LIBRARY / (c + ".sizing_spec.json"), env.lut, output_dir=out,
                        donors=donors, counters=counters)
        rec["stageA"] = a.status
        settings = SearchSettings(600.0, R.EVAL_BUDGET, R.RBOX, (("front_budget_s", "u13 test fixture"),), R.CBOX)
        if a.status == "ok":
            b = run_stage_b(a, env.memo, env.pdk, output_dir=out, settings=settings)
            rec["stageB"] = b.status
            if b.status == "ok":
                topo = json.loads((R.LIBRARY / (c + ".topology.json")).read_text(encoding="utf-8"))
                recipe = R._recipe(a, b, topo, settings)
                case = R._contexts(recipe, dict(donors=a.donors, counters=a.counters))
                front = find_front(case.sctx, ())
                rec.update(stage="front_done", n_front=len(getattr(front, "front", ()) or ()),
                           n_pending=len(getattr(front, "pending_front", ()) or ()))
    except BaseException as e:
        rec.update(error=repr(e)[:400], tb=traceback.format_exc()[-800:])
    rec.update(seal9_evals=STATE["n_eval"], seconds=round(time.time() - t0, 1))
    CIRC.write(json.dumps(rec, default=str) + "\n"); CIRC.flush()
    print(c, rec.get("stageA"), rec.get("stageB"), rec.get("stage"), rec.get("seal9_evals"), rec.get("error", ""), rec["seconds"], flush=True)
