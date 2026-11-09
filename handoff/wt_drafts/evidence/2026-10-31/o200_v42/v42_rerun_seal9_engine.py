# O-200 v2 -- 봉인 9 판정 변화(옛 정의 -> P4 / P5)를 master HEAD 엔진의 실제 커널 평가 점 전부에서 잰다.
# 읽기·실행만: 엔진 소스 수정 0, 저장소 쓰기 0 (PYTHONDONTWRITEBYTECODE, 단계 A/B 출력 = TEMP, 탐색 archive = None).
# 방법: library 회로마다 tests/search/u13_real.real_case(단계 A ok·단계 B ok 인 회로만) -> search.find_front(sctx, ()) 를 돌리고,
#       봉인 9 블록 모듈(gmid_engine.sizing.seal_conduction)의 모듈 전역 `_off_current`·`judge` 를 감싸 평가마다 전도 MOS 행을 기록한다.
#       (블록 함수가 모듈 전역을 호출 시점에 찾으므로 감싸기만으로 기록된다 -- 판정 값·반환은 그대로 돌려준다.)
# 기록 행: circuit, eval 번호, device, kind, L, W, vgs, vds, vsb, ID, gm/ID, I_off, epsID(= eps*ID, tol_V None 이면 None), tol_V(역산).
# 판정: 옛 = I_off <= eps*ID (전도) / P4 = ID > I_off (⇔ VGS > 0) / P5 = ID > 0 (기록 대상은 모두 ID > 0 이라 늘 전도).
#       P4 '구별 불가' 띠 = 0 < ln(ID/I_off) <= eps (기록 전용).
# 산출: seal9_rows.jsonl (행마다 append), seal9_circuits.jsonl (회로마다 append), 집계는 agg_seal9.py.
import os, sys, json, time, math, traceback, pathlib
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
HERE = pathlib.Path(__file__).parent
import importlib
R = importlib.import_module("gmid_engine.tests.search.u13_real")
SC = importlib.import_module("gmid_engine.sizing.seal_conduction")
from gmid_engine.search import find_front

STATE = dict(circuit=None, n_eval=0, pending=[])
ROWS = open(HERE / "seal9_rows.jsonl", "a", encoding="utf-8")
CIRC = open(HERE / "seal9_circuits.jsonl", "a", encoding="utf-8")

_orig_off = SC._off_current
_orig_judge = SC.judge


def _off(lut, device, op):
    v = _orig_off(lut, device, op)
    STATE["pending"].append((device, op, v))
    return v


def _judge(kind, rows):
    if kind == SC.SEAL_CONDUCTION:
        STATE["n_eval"] += 1
        ops = {d: (op, off) for d, op, off in STATE["pending"]}
        STATE["pending"] = []
        for r in rows:
            m, off, epsid = r[0], r[1], r[2]
            op, _ = ops.get(m, (None, None))
            rec = dict(circuit=STATE["circuit"], ev=STATE["n_eval"], device=m, I_off=off, epsID=epsid)
            if op is not None:
                ID = float(op.current); gid = float(op.gm_id)
                rec.update({f: getattr(op, f) for f in ("kind", "w_key", "L", "W", "vgs", "vds", "vsb") if hasattr(op, f)})
                rec.update(ID=ID, gm_id=gid,
                           tol_V=(None if epsid is None else epsid / (gid * ID)))
            ROWS.write(json.dumps(rec, default=float) + "\n")
        ROWS.flush()
    return _orig_judge(kind, rows)


SC._off_current = _off
SC.judge = _judge

names = sorted(p.name.replace(".topology.json", "") for p in R.LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
if len(sys.argv) > 1:
    names = sys.argv[1:]
for c in names:
    STATE.update(circuit=c, n_eval=0, pending=[])
    t0 = time.time()
    rec = dict(circuit=c)
    try:
        case = R.real_case(c)
        rec["stage"] = "ab_ok"
        front = find_front(case.sctx, ())
        rec.update(stage="front_done", n_front=len(getattr(front, "front", ()) or ()), n_pending=len(getattr(front, "pending_front", ()) or ()))
    except AssertionError as e:
        rec.update(stage=rec.get("stage", "stage_ab_not_ok"), error=repr(e)[:400])
    except BaseException as e:
        rec.update(error=repr(e)[:400], tb=traceback.format_exc()[-800:])
    rec.update(seal9_evals=STATE["n_eval"], seconds=round(time.time() - t0, 1))
    CIRC.write(json.dumps(rec, default=str) + "\n"); CIRC.flush()
    print(c, rec.get("stage"), rec.get("seal9_evals"), rec.get("error", ""), rec["seconds"], flush=True)
